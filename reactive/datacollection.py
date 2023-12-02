import inspect
import reprlib
from typing import Callable, Iterable, Iterator

from hyperparameter import param_scope

from .builtin import runas_op  # noqa: F401
from .mixins import ColumnMixin, DataFrameMixin, DCMixins
from .types import EntityView, Option, Some, dynamic_dispatch


class DataCollection(Iterable, DCMixins):
    """A generalization container datatype for `list` and `iterator`.

    `DataCollection` also supports chaining invocations, exception safety
    and parallel execution. Can be thought of as a `list` if created from `list`,
    and as a `iterator` if create from `iterator`. The primary data structure for
    reactive programming.

    Examples:
        - Create `DataCollection` from list or iterator:
        >>> import reactive as rv
        >>> rv.of([1, 2, 3, 4])
        [1, 2, 3, 4]
        >>> rv.of(iter([0, 1, 2, 3, 4])) #doctest: +ELLIPSIS
        <list_iterator object at ...>

        - Chaining method calls:
        >>> (
        ...     rv.of([1, 2, 3, 4])
        ...       .map(lambda x: x+1)
        ...       .map(lambda x: x*2)
        ... ).to_list()
        [4, 6, 8, 10]

        - Any function invocations:
        >>> def add1(x): return x+1
        >>> def mul2(x): return x*2
        >>> (
        ...     rv.of([1, 2, 3, 4])
        ...       .add1()
        ...       .mul2()
        ... )
        [4, 6, 8, 10]
    """

    def __init__(self, iterable: Iterable) -> None:
        super().__init__()
        self._iterable = iterable

    def __iter__(self) -> iter:
        if hasattr(self._iterable, "iterrows"):
            return (x[1] for x in self._iterable.iterrows())
        return iter(self._iterable)

    def __getattr__(self, name) -> "DataCollection":
        if name.startswith("_"):
            return super().__getattribute__(name)

        stacks = inspect.stack()[1][0]

        @dynamic_dispatch
        def wrapper(*arg, **kws):
            op = self.resolve(stacks, *arg, **kws)
            return self.map(op)

        return getattr(wrapper, name)

    def __getitem__(self, index) -> any:
        """Index based access of element in DataCollection.

        Access the element at the given index, similar to accessing `list[at_index]`.
        Does not work with streamed DataCollections.

        Args:
            index (int): The index location of the element being accessed.

        Raises:
            TypeError: If function called on streamed DataCollection

        Returns:
            any: The object at index.

        Examples:
            1. Usage with non-streamed:
            >>> dc = DataCollection([0, 1, 2, 3, 4])
            >>> dc[2]
            2

            2. Usage with streamed:
            >>> dc.stream()[1] # doctest: +NORMALIZE_WHITESPACE
            Traceback (most recent call last):
            TypeError: indexing is only supported for DataCollection created from list
                or pandas DataFrame.
        """
        if not hasattr(self._iterable, "__getitem__"):
            raise TypeError(
                "indexing is only supported for "
                "DataCollection created from list or pandas DataFrame."
            )
        if isinstance(index, int):
            return self._iterable[index]
        return DataCollection(self._iterable[index])

    def __setitem__(self, index, value):
        """Index based setting of element in DataCollection.

        Assign the value of the element at the given index, similar to
        `list[at_index]=val`. Does not work with streamed DataCollections.

        Args:
            index (int): The index location of the element being set.
            value (any): The value to be set.

        Raises:
            TypeError: If function called on streamed DataCollection

        Examples:
            1. Usage with non-streamed:
            >>> dc = DataCollection([0, 1, 2, 3, 4])
            >>> dc[2] = 3
            >>> dc.to_list()
            [0, 1, 3, 3, 4]

            2. Usage with streamed:
            >>> dc.stream()[1] # doctest: +NORMALIZE_WHITESPACE
            Traceback (most recent call last):
            TypeError: indexing is only supported for DataCollection created from list
                or pandas DataFrame.
        """
        if not hasattr(self._iterable, "__setitem__"):
            raise TypeError(
                "indexing is only supported for "
                "DataCollection created from list or pandas DataFrame."
            )
        self._iterable[index] = value

    def __add__(self, other) -> "DataCollection":
        """Concat two DataCollections.

        Args:
            other (DataCollection): The DataCollection being appended to the calling
                DataFrame.

        Returns:
            DataCollection: A new DataCollection of the concated DataCollections.

        Examples:
            >>> dc0 = DataCollection(range(5))
            >>> dc1 = DataCollection(range(5))
            >>> dc2 = DataCollection(range(5))
            >>> (dc0 + dc1 + dc2)
            [0, 1, 2, 3, 4, 0, ...]
        """

        def inner():
            for x in self:
                yield x
            for x in other:
                yield x

        return self._factory(inner())

    def __repr__(self) -> str:
        """String representation of the DataCollection

        Returns:
            str: String representation of the DataCollection.

        Examples:
            1. Usage with non-streamed::
            >>> DataCollection([1, 2, 3]).unstream()
            [1, 2, 3]

            2. Usage with streamed::
            >>> DataCollection([1, 2, 3]).stream() #doctest: +ELLIPSIS
            <list_iterator object at...>
        """
        if isinstance(self._iterable, list):
            return reprlib.repr(self._iterable)
        if hasattr(self._iterable, "__repr__"):
            return repr(self._iterable)
        return super().__repr__()

    # Generation Related Function
    def _factory(self, iterable, parent_stream=True) -> "DataCollection":
        """Factory method for Creating new DataCollections.

        This factory method has been wrapped into a `param_scope()` which contains the
        parent DataCollection's information.

        Args:
            iterable (Iterable): The data being encapsulated by the DataCollection
            parent_stream (bool, optional): Whether to use the same format of parent
                DataCollection (streamed or unstreamed). Defaults to True.

        Returns:
            DataCollection: The newly created DataCollection.
        """
        if parent_stream is True:
            if self.is_stream:
                if not isinstance(iterable, Iterator):
                    iterable = iter(iterable)
            else:
                if isinstance(iterable, Iterator):
                    iterable = list(iterable)

        with param_scope() as ps:
            ps.data_collection.parent = self
            return DataCollection(iterable)

    def map(self, *arg) -> "DataCollection":
        """Apply a function across all values in a DataCollection.

        Can apply multiple functions to the DataCollection. If multiple functions
        supplied, the same amount of new DataCollections will be returend.

        Args:
            *arg (Callable): One or multiple functions to apply to the DataCollection.

        Returns:
            DataCollection: New DataCollection containing computation results.

        Examples:
            1. Single Function::
            >>> DataCollection([1,2,3,4]).map(lambda x: x+1).map(lambda x: x*2)
            [4, 6, 8, 10]

            2. Multiple Functions::
            >>> a, b = DataCollection([1,2,3,4]).map(lambda x: x+1, lambda x: x*2)
            >>> (a.to_list(), b.to_list())
            ([2, 3, 4, 5], [2, 4, 6, 8])
        """
        # mmap
        if len(arg) > 1:
            return self.mmap(list(arg))
        fn = arg[0]

        # smap map for stateful operator
        if hasattr(fn, "is_stateful") and fn.is_stateful:
            return self.smap(fn)

        # pmap
        if self.get_executor() is not None:
            return self.pmap(fn)

        if hasattr(self._iterable, "map"):
            return self._factory(self._iterable.map(fn))

        if hasattr(self._iterable, "apply") and hasattr(fn, "__dataframe_apply__"):
            return self._factory(fn.__dataframe_apply__(self._iterable))

        # map
        def inner(x):
            if isinstance(x, Option):
                return x.map(fn)
            else:
                return fn(x)

        result = map(inner, self._iterable)
        return self._factory(result)

    def filter(self, fn: Callable, drop_empty=False) -> "DataCollection":
        """Filter the DataCollection data based on function.

        Filters the DataCollection based on the function provided. If data is stored
        as an Option (see reactive.Option), drop empty will decide whether
        to remove the element or set it to empty.

        Args:
            unary_op (Callable): Function that dictates filtering.
            drop_empty (bool, optional): Whether to drop empty fields. Defaults to False.

        Returns:
            DataCollection: Resulting DataCollection after filter.
        """

        def inner(x):
            if isinstance(x, Option):
                if isinstance(x, Some):
                    return fn(x.get())
                return not drop_empty
            return fn(x)

        if hasattr(self._iterable, "filter"):
            return self._factory(self._iterable.filter(fn))

        if hasattr(self._iterable, "apply") and hasattr(fn, "__dataframe_filter__"):
            return DataCollection(fn.__dataframe_apply__(self._iterable))

        return self._factory(filter(inner, self._iterable))

    def run(self, fn: Callable = None):
        """Iterate through the DataCollections data.

        Stream-based DataCollections will not run if the data is not a datasink. This
        function is a datasink that consumes the data without any operations.

        Args:
            fn (Callable): callback function for each element;

        Examples:
            >>> DataCollection([1, 2, 3, 4]).run()
            >>> DataCollection([1, 2, 3, 4]).run(print)
            1
            2
            3
            4
        """
        if fn is None:
            for _ in self._iterable:
                pass
        else:
            for x in self._iterable:
                fn(x)

    def subscribe(self, fn: Callable = None):
        return self.run(fn)

    def to_list(self) -> list:
        """Convert DataCollection to list.

        Returns:
            list: List of values stored in DataCollection.

        Examples:
            >>> DataCollection(range(5)).to_list()
            [0, 1, 2, 3, 4]
        """
        return (
            self._iterable if isinstance(self._iterable, list) else list(self._iterable)
        )

    def to_df(self) -> "DataFrame":
        """Turn a DataCollection into a DataFrame.

        Returns:
            DataFrame: Resulting converted DataFrame.

        Examples:
            >>> from reactive import DataCollection, Entity
            >>> e = [Entity(a=a, b=b) for a,b in zip(['abc', 'def', 'ghi'], [1,2,3])]
            >>> d = DataCollection(e)
            >>> type(d)
            <class 'reactive.datacollection.DataCollection'>

            >>> type(d.to_df())
            <class 'reactive.datacollection.DataFrame'>
        """
        return DataFrame(self._iterable)


class DataFrame(DataCollection, DataFrameMixin, ColumnMixin):
    """Entity based DataCollection.

    Examples:
        >>> from reactive import Entity
        >>> DataFrame([Entity(id=a) for a in [1,2,3]])
        [<Entity dict_keys(['id'])>, <Entity dict_keys(['id'])>, <Entity dict_keys(['id'])>]
    """

    def __init__(self, iterable: Iterable = None, parent=None, **kws) -> None:
        """Initializes a new DataFrame instance.

        Args:
            iterable (Iterable, optional): The data to be encapsualted by the DataFrame.
                Defaults to None.
        """
        if iterable is not None:
            super().__init__(iterable)
            self._mode = self.ModeFlag.ROWBASEDFLAG
        else:
            super().__init__(DataFrame.from_arrow_talbe(**kws))
            self._mode = self.ModeFlag.COLBASEDFLAG

    def _factory(self, iterable, parent_stream=True, mode=None) -> "DataFrame":
        """Factory method for Creating new DataFrames.

        This factory method has been wrapped into a `param_scope()` which contains the
        parent DataFrames's information.

        Args:
            iterable (Iterable): The data being encapsulated by the DataFrame
            parent_stream (bool, optional): Whether to use the same format of parent
                DataFrame (streamed or unstreamed). Defaults to True.
            mode (ModeFlag): The storage mode of the Dataframe.

        Returns:
            DataFrame: The newly created DataFrame.
        """

        # pylint: disable=protected-access
        if parent_stream is True:
            if self.is_stream:
                if not isinstance(iterable, Iterator):
                    iterable = iter(iterable)
            else:
                if isinstance(iterable, Iterator):
                    iterable = list(iterable)

        with param_scope() as ps:
            ps.data_collection.parent = self
            df = DataFrame(iterable)
            df._mode = self._mode if mode is None else mode
            return df

    def to_dc(self) -> "DataCollection":
        """Turn a DataFrame into a DataCollection.

        Returns:
            DataCollection: Resulting DataCollection from DataFrame

        Examples:
            >>> from reactive import DataFrame, Entity
            >>> e = [Entity(a=a, b=b) for a,b in zip(['abc', 'def', 'ghi'], [1,2,3])]
            >>> df = DataFrame(e)
            >>> type(df)
            <class 'reactive.datacollection.DataFrame'>

            >>> type(df.to_dc())
            <class 'reactive.datacollection.DataCollection'>
        """
        return DataCollection(self._iterable)

    @property
    def mode(self):
        """Storage mode of the DataFrame.

        Return the storage mode of the DataFrame.

        Returns:
            ModeFlag: The storage format of the Dataframe.

        Examples:
            >>> from reactive import Entity, DataFrame
            >>> e = [Entity(a=a, b=b) for a,b in zip(range(5), range(5))]
            >>> df = DataFrame(e)
            >>> df.mode
            <ModeFlag.ROWBASEDFLAG: 1>

            >>> df = df.to_column()
            >>> df.mode
            <ModeFlag.COLBASEDFLAG: 2>
        """
        return self._mode

    def __iter__(self) -> iter:
        """Generate an iterator of the DataFrame.

        Returns:
            iterator: The iterator for the DataFrame.

        Examples:
            1. Row Based::
            >>> from reactive import Entity, DataFrame
            >>> e = [Entity(a=a, b=b) for a,b in zip(range(3), range(3))]
            >>> df = DataFrame(e)
            >>> df.to_list()[0]
            <Entity dict_keys(['a', 'b'])>

            2. Column Based::
            >>> df = df.to_column()
            >>> df.to_list()[0]
            <EntityView dict_keys(['a', 'b'])>

            2. Chunk Bassed::
            >>> df = DataFrame(e)
            >>> df = df.set_chunksize(2)
            >>> df.to_list()[0]
            <EntityView dict_keys(['a', 'b'])>
        """
        if hasattr(self._iterable, "iterrows"):
            return (x[1] for x in self._iterable.iterrows())
        if self._mode == self.ModeFlag.ROWBASEDFLAG:
            return iter(self._iterable)
        if self._mode == self.ModeFlag.COLBASEDFLAG:
            return (EntityView(i, self._iterable) for i in range(len((self._iterable))))
        if self._mode == self.ModeFlag.CHUNKBASEDFLAG:
            return (ev for wtable in self._iterable.chunks() for ev in wtable)

    def map(self, *arg) -> "DataFrame":
        """Apply a function across all values in a DataFrame.

        Args:
            *arg (Callable): One function to apply to the DataFrame.

        Returns:
            DataFrame: New DataFrame containing computation results.
        """
        if hasattr(arg[0], "__check_init__"):
            arg[0].__check_init__()
        if (
            self._mode == self.ModeFlag.COLBASEDFLAG
            or self._mode == self.ModeFlag.CHUNKBASEDFLAG
        ):
            return self.cmap(arg[0])
        else:
            return super().map(*arg)
