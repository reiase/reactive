import asyncio
import concurrent.futures
import threading
import time
from queue import Queue
from warnings import warn

try:
    import torch
except:  # pylint: disable=bare-except
    pass

from hyperparameter import param_scope

from reactive.types.option import Empty, Option, _Reason
from reactive.types.storages import ChunkedTable, WritableTable

stream = threading.local()


def initializer():
    # pylint: disable=bare-except
    try:
        if torch.cuda.is_available():
            stream.stream = torch.cuda.Stream()
    except:
        pass


class ParallelMixin:
    """
    Mixin for parallel execution.

    Examples:

    >>> import reactive as rv
    >>> def add_1(x):
    ...     return x+1
    >>> result = rv.range(1000).set_parallel(2).map(add_1).to_list()
    >>> len(result)
    1000

    >>> dc = rv.of['a'](range(1000)).set_parallel(5)
    >>> dc = dc.runas_op['a', 'b'](lambda x: x+1).to_list()
    >>> len(dc)
    1000

    >>> dc = rv.of['a'](range(1000)).set_parallel(5).set_chunksize(2)
    >>> dc = dc.runas_op['a', 'b'](lambda x: x+1)
    >>> for chunk in dc._iterable.chunks()[:2]: print(chunk)
    pyarrow.Table
    a: int64
    b: int64
    ----
    a: [[0,1]]
    b: [[1,2]]
    pyarrow.Table
    a: int64
    b: int64
    ----
    a: [[2,3]]
    b: [[3,4]]

    >>> result = rv.range(1000).pmap(add_1, 10).pmap(add_1, 10).to_list()
    >>> result[990:]
    [992, 993, 994, 995, 996, 997, 998, 999, 1000, 1001]
    """

    def __init__(self) -> None:
        super().__init__()
        with param_scope() as ps:
            parent = ps.data_collection.parent | None
        if parent is not None and hasattr(parent, "_executor"):
            self._backend = parent._backend
            self._executor = parent._executor
            self._num_worker = parent._num_worker

    def get_executor(self):
        if hasattr(self, "_executor"):
            return self._executor
        return None

    def get_backend(self):
        if hasattr(self, "_backend") and isinstance(self._backend, str):
            return self._backend
        return None

    def get_num_worker(self):
        if hasattr(self, "_num_worker"):
            return self._num_worker
        return None

    def set_parallel(self, num_worker=2, backend="thread"):
        """
        Set parallel execution for following calls.

        Examples:

        >>> import reactive as rv
        >>> import threading
        >>> stage_1_thread_set = set()
        >>> stage_2_thread_set = set()
        >>> result = (
        ...     rv.range(1000).stream().set_parallel(4)
        ...     .map(lambda x: stage_1_thread_set.add(threading.current_thread().ident))
        ...     .map(lambda x: stage_2_thread_set.add(threading.current_thread().ident)).to_list()
        ... )

        >>> len(stage_2_thread_set)>1
        True
        """
        self._backend = backend
        self._num_worker = num_worker

        if self._backend == "thread" and self._num_worker is not None:
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=num_worker, initializer=initializer
            )
        else:  # clear executor
            self._executor = None
        return self

    def split(self, count):
        """
        Split a dataframe into multiple dataframes.

        Args:
            count (int): how many resulting DCs;

        Returns:
            [DataCollection, ...]: copies of DC;

        Examples:

        1. Split:

        >>> import reactive as rv
        >>> d = rv.of([0, 1, 2, 3, 4]).stream()
        >>> a, b, c = d.split(3)
        >>> a.zip(b, c).to_list()
        [(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3), (4, 4, 4)]
        """
        # Figure out better optimization
        if self.is_stream:
            queues = [Queue(count) for _ in range(count)]
        else:
            queues = [Queue() for _ in range(count)]
        loop = asyncio.new_event_loop()

        def inner(queue):
            while True:
                x = queue.get()
                if isinstance(x, EOS):
                    break
                else:
                    yield x

        async def worker():
            cached_values = {x: [] for x in range(count)}

            for x in self:
                # TODO: Use some kind of event instead of wait
                sleepy = 0.01
                while all(y.full() for y in queues):
                    time.sleep(sleepy)

                for i, queue in enumerate(queues):
                    if len(cached_values[i]) > 0:
                        while not queue.full() and len(cached_values[i]) > 0:
                            queue.put(cached_values[i].pop(0))
                    if len(cached_values[i]) == 0 and not queue.full():
                        queue.put(x)
                    else:
                        cached_values[i].append(x)

            for i, queue in enumerate(queues):
                poison = EOS()
                cached_values[i].append(poison)

            while len(cached_values) > 0:
                for x in list(cached_values.keys()):
                    if len(cached_values[x]) == 0:
                        del cached_values[x]
                    else:
                        while not queues[x].full() and len(cached_values[x]) > 0:
                            queues[x].put(cached_values[x].pop(0))

        def worker_wrapper():
            loop.run_until_complete(worker())
            loop.close()

        t = threading.Thread(target=worker_wrapper, daemon=True)
        t.start()
        retval = [inner(queue) for queue in queues]
        return [self._factory(x) for x in retval]

    def _map_task(self, x, unary_op):
        def inner():
            try:
                if isinstance(x, Option):
                    res = x.map(unary_op)
                elif isinstance(x, WritableTable):
                    res = WritableTable(self.__table_apply__(x, unary_op))
                else:
                    res = unary_op(x)
                return res
            except Exception as e:  # pylint: disable=broad-except
                warn(
                    f"{e}, please check {x} with op {unary_op}. Continue..."
                )  # pylint: disable=logging-fstring-interpolation
                return Empty(_Reason(x, e))

        def map_wrapper():
            if hasattr(stream, "stream"):
                torch.cuda.synchronize()
                with torch.cuda.stream(stream.stream):
                    res = inner()
                torch.cuda.synchronize()
                return res
            else:
                return inner()

        return map_wrapper

    def pmap(self, unary_op, num_worker=None, backend=None):
        """
        Apply `unary_op` with parallel execution.
        Currently supports two backends, `ray` and `thread`.

        Args:
            unary_op (func): the op to be mapped;
            num_worker (int): how many threads to reserve for this op;
            backend (str): whether to use `ray` or `thread`

        Examples:

        >>> import reactive as rv
        >>> import threading
        >>> stage_1_thread_set = {threading.current_thread().ident}
        >>> stage_2_thread_set = {threading.current_thread().ident}
        >>> result = (
        ...     rv.range(1000).stream()
        ...     .pmap(lambda x: stage_1_thread_set.add(threading.current_thread().ident), 5)
        ...     .pmap(lambda x: stage_2_thread_set.add(threading.current_thread().ident), 4).to_list()
        ... )
        >>> len(stage_1_thread_set) > 1
        True
        >>> len(stage_2_thread_set) > 1
        True
        """
        backend = self.get_backend()
        if backend == "ray":
            return self._ray_pmap(unary_op, num_worker)
        return self._thread_pmap(unary_op, num_worker)

    def _thread_pmap(self, unary_op, num_worker=None):
        if num_worker is None and self.get_num_worker() is None:
            num_worker = 2
        if num_worker is not None:
            executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=num_worker, initializer=initializer
            )
        elif self.get_executor() is not None:
            executor = self._executor
            num_worker = self._num_worker

        queue = Queue(num_worker)
        loop = asyncio.new_event_loop()

        def inner():
            while True:
                x = queue.get()
                queue.task_done()
                if isinstance(x, EOS):
                    break
                else:
                    yield x

        async def worker():
            buff = []
            iterable = (
                self._iterable.chunks()
                if isinstance(self._iterable, ChunkedTable)
                else self
            )
            for x in iterable:
                if len(buff) == num_worker:
                    queue.put(await buff.pop(0))
                buff.append(loop.run_in_executor(executor, self._map_task(x, unary_op)))
            while len(buff) > 0:
                queue.put(await buff.pop(0))
            queue.put(EOS())

        def worker_wrapper():
            loop.run_until_complete(worker())
            loop.close()

        t = threading.Thread(target=worker_wrapper, daemon=True)
        t.start()

        res = inner()

        if isinstance(self._iterable, ChunkedTable):
            if not self.is_stream:
                res = list(res)
            res = ChunkedTable(chunks=res)

        return self._factory(res)

    def mmap(self, ops: list, num_worker=None, backend=None):
        """
        Apply multiple unary_op to data collection.
        Currently supports two backends, `ray` and `thread`.

        Args:
            unary_op (func): the op to be mapped;
            num_worker (int): how many threads to reserve for this op;
            backend (str): whether to use `ray` or `thread`

        # TODO: the test is broken with pytest
        # Examples:

        # 1. Using mmap:

        # >>> from towhee import DataCollection
        # >>> dc1 = DataCollection([0,1,2,'3',4]).stream()
        # >>> a1, b1 = dc1.mmap([lambda x: x+1, lambda x: x*2])
        # >>> c1 = a1.map(lambda x: x+1)
        # >>> c1.zip(b1).to_list()
        # [(2, 0), (3, 2), (4, 4), (Empty(), '33'), (6, 8)]

        # 2. Using map instead of mmap:

        # >>> from towhee import DataCollection
        # >>> dc2 = DataCollection.range(5).stream()
        # >>> a2, b2, c2 = dc2.map(lambda x: x+1, lambda x: x*2, lambda x: int(x/2))
        # >>> d2 = a2.map(lambda x: x+1)
        # >>> d2.zip(b2, c2).to_list()
        # [(2, 0, 0), (3, 2, 0), (4, 4, 1), (5, 6, 1), (6, 8, 2)]

        # 3. DAG execution:

        # >>> dc3 = DataCollection.range(5).stream()
        # >>> a3, b3, c3 = dc3.map(lambda x: x+1, lambda x: x*2, lambda x: int(x/2))
        # >>> d3 = a3.map(lambda x: x+1)
        # >>> d3.zip(b3, c3).map(lambda x: x[0]+x[1]+x[2]).to_list()
        # [2, 5, 9, 12, 16]
        """
        if len(ops) == 1:
            return self._pmap(unary_op=ops[0], num_worker=num_worker, backend=backend)

        next_vals = []
        next_vals = self.split(len(ops))

        ret = []
        for i, x in enumerate(ops):
            ret.append(next_vals[i].pmap(x, num_worker=num_worker, backend=backend))
        return ret


class EOS:
    """
    Internal object used to signify end of processing queue.
    """

    pass
