import random
from typing import Iterable

from hyperparameter import param_scope

from ..types import dynamic_dispatch
from ..types.entity import Entity


class DataProcessingMixin:
    """
    Mixin for processing data.
    """

    def zip(self, *others) -> "DataCollection":
        """
        Combine two data collections.

        Args:
            *others (DataCollection): other data collections;

        Returns:
            DataCollection: data collection with zipped values;

        Examples:

        >>> import reactive as rv
        >>> dc1 = rv.of([1,2,3,4])
        >>> dc2 = rv.of([1,2,3,4]).map(lambda x: x+1)
        >>> dc3 = dc1.zip(dc2)
        >>> list(dc3)
        [(1, 2), (2, 3), (3, 4), (4, 5)]
        """

        return self._factory(zip(self, *others))

    def head(self, n: int = 5):
        """
        Get the first n lines of a DataCollection.

        Args:
            n (`int`):
                The number of lines to print. Default value is 5.

        Examples:

        >>> import reactive as rv
        >>> rv.range(10).head(3).to_list()
        [0, 1, 2]
        """

        def inner():
            for i, x in enumerate(self._iterable):
                if i >= n:
                    break
                yield x

        return self._factory(inner())

    def sample(self, ratio=1.0) -> "DataCollection":
        """
        Sample the data collection.

        Args:
            ratio (float): sample ratio;

        Returns:
            DataCollection: sampled data collection;

        Examples:

        >>> import reactive as rv
        >>> dc = rv.of(range(10000))
        >>> result = dc.sample(0.1)
        >>> ratio = len(result.to_list()) / 10000.
        >>> 0.09 < ratio < 0.11
        True
        """
        return self._factory(filter(lambda _: random.random() < ratio, self))

    def batch(self, size, drop_tail=False):
        """
        Create small batches from data collections.

        Args:
            size (`int`):
                Window size;
            drop_tail (`bool`):
                Drop tailing windows that not full, defaults to False;


        Returns:
            DataCollection of batched windows or batch raw data

        Examples:

        >>> import reactive as rv
        >>> dc = rv.of(range(10))
        >>> [list(batch) for batch in dc.batch(2)]
        [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]

        >>> dc = rv.of(range(10))
        >>> dc.batch(3)
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

        >>> dc = rv.of(range(10))
        >>> dc.batch(3, drop_tail=True)
        [[0, 1, 2], [3, 4, 5], [6, 7, 8]]

        >>> from reactive import Entity
        >>> dc = rv.of([Entity(a=a, b=b) for a,b in zip(['abc', 'vdfvcd', 'cdsc'], [1,2,3])])
        >>> dc.batch(2)
        [[<Entity dict_keys(['a', 'b'])>, <Entity dict_keys(['a', 'b'])>], [<Entity dict_keys(['a', 'b'])>]]
        """

        def inner():
            buff = []
            count = 0
            for ele in self._iterable:
                buff.append(ele)
                count += 1

                if count == size:
                    yield buff
                    buff = []
                    count = 0

            if not drop_tail and count > 0:
                yield buff

        return self._factory(inner())

    def rolling(self, size: int, step: int = 1, drop_head=True, drop_tail=True):
        """
        Create rolling windows from data collections.

        Args:
            size (`int`):
                Wndow size.
            drop_head (`bool`):
                Drop headding windows that not full.
            drop_tail (`bool`):
                Drop tailing windows that not full.

        Returns:
            DataCollection: data collection of rolling windows;

        Examples:

        >>> import reactive as rv
        >>> dc = rv.range(5)
        >>> [list(batch) for batch in dc.rolling(3)]
        [[0, 1, 2], [1, 2, 3], [2, 3, 4]]

        >>> dc = rv.range(5)
        >>> [list(batch) for batch in dc.rolling(3, drop_head=False)]
        [[0], [0, 1], [0, 1, 2], [1, 2, 3], [2, 3, 4]]

        >>> dc = rv.range(5)
        >>> [list(batch) for batch in dc.rolling(3, drop_tail=False)]
        [[0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4], [4]]

        >>> rv.range(5).rolling(2, 2, drop_head=False, drop_tail=False)
        [[0], [0, 1], [2, 3], [4]]

        >>> rv.range(5).rolling(2, 4, drop_head=False, drop_tail=False)
        [[0], [0, 1], [4]]
        """

        def inner():
            buff = []
            gap = 0
            head_flag = True
            for ele in self._iterable:
                if gap:
                    gap -= 1
                    continue

                buff.append(ele)

                if not drop_head and head_flag or len(buff) == size:
                    yield buff.copy()

                if len(buff) == size:
                    head_flag = False
                    buff = buff[step:]
                    gap = step - size if step > size else 0

            while not drop_tail and buff:
                yield buff
                buff = buff[step:]

        return self._factory(inner())

    @property
    def flatten(self) -> "DataCollection":
        """
        Flatten nested data collections.

        Args:
            index (`str`):
                The index of the column to flatten.

        Returns:
            DataCollection: flattened data collection;

        Examples:

        >>> import reactive as rv
        >>> dc = rv.range(10)
        >>> nested_dc = dc.batch(2)
        >>> nested_dc.flatten().to_list()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        >>> g = (i for i in range(3))
        >>> e = Entity(a=1, b=2, c=g)
        >>> dc = rv.of([e]).flatten['c']()
        >>> [str(i) for i in dc]
        ["{'a': 1, 'b': 2, 'c': 0}", "{'a': 1, 'b': 2, 'c': 1}", "{'a': 1, 'b': 2, 'c': 2}"]
        """

        @dynamic_dispatch
        def flattener():
            def inner():
                for ele in self._iterable:
                    # pylint: disable=protected-access
                    index = param_scope._index | None
                    # With schema
                    if isinstance(ele, Entity):
                        if not index:
                            raise IndexError("Please specify the column to flatten.")
                        else:
                            new_ele = ele.__dict__.copy()
                            for nested_ele in getattr(ele, index):
                                new_ele[index] = nested_ele
                                yield Entity(**new_ele)
                    # Without schema
                    elif isinstance(ele, Iterable):
                        for nested_ele in iter(ele):
                            yield nested_ele
                    else:
                        yield ele

            return self._factory(inner())

        return flattener

    def shuffle(self) -> "DataCollection":
        """
        Shuffle an unstreamed data collection in place.

        Returns:
            DataCollection: shuffled data collection;

        Examples:

        1. Shuffle:

        >>> import reactive as rv
        >>> dc = rv.range(5)
        >>> a = dc.shuffle()
        >>> tuple(a) == tuple(range(5))
        False

        2. streamed data collection is not supported:

        >>> dc = rv.of([0, 1, 2, 3, 4]).stream()
        >>> _ = dc.shuffle()
        Traceback (most recent call last):
        TypeError: shuffle is not supported for streamed data collection.
        """
        if self.is_stream:
            raise TypeError("shuffle is not supported for streamed data collection.")
        iterable = random.sample(self._iterable, len(self._iterable))
        return self._factory(iterable)
