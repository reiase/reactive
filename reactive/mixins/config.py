from typing import Union

from hyperparameter import param_scope


class ConfigMixin:
    """Mixin to manage configurations such as `parallel`, `chunksize` and `jit`.

    Examples:
        >>> import reactive as rv
        >>> dc0 = rv.of['a'](range(20))
        >>> dc0 = dc0.set_chunksize(10)
        >>> dc0 = dc0.set_parallel(2)
        >>> dc0 = dc0.set_jit('numba')
        >>> dc0.get_config()
        {'parallel': 2, 'chunksize': 10, 'jit': 'numba'}

        >>> dc1 = rv.of([1,2,3]).config(jit='numba')
        >>> dc2 = rv.of['a'](range(40)).config(parallel=2, chunksize=20)
        >>> dc1.get_config()
        {'parallel': None, 'chunksize': None, 'jit': 'numba'}
        >>> dc2.get_config()
        {'parallel': 2, 'chunksize': 20, 'jit': None}

        >>> dc0 = rv.of['a'](range(20))
        >>> dc0 = dc0.set_chunksize(10)
        >>> dc0 = dc0.set_parallel(2)
        >>> dc0 = dc0.set_jit('numba')
    """

    def __init__(self) -> None:
        super().__init__()
        with param_scope() as ps:
            parent = ps.data_collection.parent(None)
        if parent is None or not hasattr(parent, "_num_worker"):
            self._num_worker = None
        if parent is None or not hasattr(parent, "_chunksize"):
            self._chunksize = None
        if parent is None or not hasattr(parent, "_jit"):
            self._jit = None

    def config(
        self,
        parallel: int = None,
        chunksize: int = None,
        jit: Union[str, dict] = None,
    ):
        """
        Set the parameters in DC.

        Args:
            parallel (`int`):
               Set the number of parallel execution for following calls.
            chunksize (`int`):
               Set the chunk size for arrow.
            jit (`Union[str, dict]`):
               It can set to "numba", this mode will speed up the Operator's function, but it may also need to return to python mode due to JIT
               failure, which will take longer, so please set it carefully.
        """
        dc = self
        if jit is not None:
            dc = dc.set_jit(compiler=jit)
        if parallel is not None:
            dc = dc.set_parallel(num_worker=parallel)
        if chunksize is not None:
            dc = dc.set_chunksize(chunksize=chunksize)
        return dc

    def get_config(self):
        """
        Return the config in DC, such as `parallel`, `chunksize` and `jit`.
        """
        config = {}

        if hasattr(self, "_num_worker"):
            config["parallel"] = self._num_worker
        if hasattr(self, "_chunksize"):
            config["chunksize"] = self._chunksize
        if hasattr(self, "_jit"):
            config["jit"] = self._jit
        return config
