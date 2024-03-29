from enum import Flag, auto

from hyperparameter import param_scope

from reactive.types.storages import ChunkedTable, WritableTable


# pylint: disable=import-outside-toplevel
# pylint: disable=bare-except
class ColumnMixin:
    """
    Mixins to support column-based storage.
    """

    class ModeFlag(Flag):
        ROWBASEDFLAG = auto()
        COLBASEDFLAG = auto()
        CHUNKBASEDFLAG = auto()

    def __init__(self) -> None:
        super().__init__()
        parent = param_scope.data_collection.parent | None
        if parent is not None and hasattr(parent, "_chunksize"):
            self._chunksize = parent._chunksize

    def set_chunksize(self, chunksize):
        """
        Set chunk size for arrow

        Examples:

        >>> import reactive as rv
        >>> d1 = rv.of['a'](range(20))
        >>> d1 = d1.set_chunksize(10)
        >>> d2 = d1.runas_op['a', 'b'](func=lambda x: x+1)
        >>> d1.get_chunksize(), d2.get_chunksize()
        (10, 10)
        >>> for chunk in d2._iterable.chunks(): print(chunk)
        pyarrow.Table
        a: int64
        b: int64
        ----
        a: [[0,1,2,3,4,5,6,7,8,9]]
        b: [[1,2,3,4,5,6,7,8,9,10]]
        pyarrow.Table
        a: int64
        b: int64
        ----
        a: [[10,11,12,13,14,15,16,17,18,19]]
        b: [[11,12,13,14,15,16,17,18,19,20]]

        >>> dc_3 = rv.of['a'](range(20)).stream()
        >>> dc_3 = dc_3.set_chunksize(10)
        >>> dc_4 = dc_3.runas_op['a', 'b'](func=lambda x: x+1)
        >>> for chunk in dc_4._iterable.chunks(): print(chunk)
        pyarrow.Table
        a: int64
        b: int64
        ----
        a: [[0,1,2,3,4,5,6,7,8,9]]
        b: [[1,2,3,4,5,6,7,8,9,10]]
        pyarrow.Table
        a: int64
        b: int64
        ----
        a: [[10,11,12,13,14,15,16,17,18,19]]
        b: [[11,12,13,14,15,16,17,18,19,20]]
        """

        self._chunksize = chunksize
        chunked_table = ChunkedTable(chunksize=chunksize, stream=self.is_stream)
        chunked_table.feed(self._iterable)
        return self._factory(
            chunked_table, parent_stream=False, mode=self.ModeFlag.CHUNKBASEDFLAG
        )

    def get_chunksize(self):
        return self._chunksize

    def _create_col_table(self):
        """
        Create a column-based table.

        Examples:
            >>> from reactive import Entity, DataFrame
            >>> e = [Entity(a=a, b=b) for a,b in zip(['abc', 'def', 'ghi'], [1,2,3])]
            >>> df = DataFrame(e)
            >>> table = df._create_col_table()
            >>> table
            pyarrow.Table
            a: string
            b: int64
            ----
            a: [["abc","def","ghi"]]
            b: [[1,2,3]]

            >>> df.stream()._create_col_table()
            pyarrow.Table
            a: string
            b: int64
            ----
            a: [["abc","def","ghi"]]
            b: [[1,2,3]]
        """
        import pyarrow as pa

        from reactive.types.tensor_array import TensorArray

        header = None
        cols = None

        # cols = [[getattr(entity, col) for entity in self._iterable] for col in header]
        def inner(entity):
            nonlocal cols, header
            header = [*entity.__dict__] if not header else header
            cols = [[] for _ in header] if not cols else cols
            for col, name in zip(cols, header):
                col.append(getattr(entity, name))

        for entity in self._iterable:
            inner(entity)

        arrays = []
        for col in cols:
            try:
                arrays.append(pa.array(col))
            # pylint: disable=bare-except
            except:
                arrays.append(TensorArray.from_numpy(col))

        return pa.Table.from_arrays(arrays, names=header)

    @classmethod
    def from_arrow_table(cls, **kws):
        import pyarrow as pa

        arrays = []
        names = []
        for k, v in kws.items():
            arrays.append(v)
            names.append(k)
        return pa.Table.from_arrays(arrays, names=names)

    def to_column(self):
        """
        Convert the iterables to column-based table.

        Examples:
            >>> from reactive import Entity, DataFrame
            >>> e = [Entity(a=a, b=b) for a,b in zip(['abc', 'def', 'ghi'], [1,2,3])]
            >>> df = DataFrame(e)
            >>> df
            [<Entity dict_keys(['a', 'b'])>, <Entity dict_keys(['a', 'b'])>, <Entity dict_keys(['a', 'b'])>]
            >>> df.to_column()
            pyarrow.Table
            a: string
            b: int64
            ----
            a: [["abc","def","ghi"]]
            b: [[1,2,3]]
        """

        # pylint: disable=protected-access
        df = self.to_df()
        res = df._create_col_table()
        df._iterable = WritableTable(res)
        df._mode = self.ModeFlag.COLBASEDFLAG
        return df

    def cmap(self, unary_op):
        """
        chunked map

        Examples:

        >>> import reactive as rv
        >>> dc = rv.of['a'](range(10))
        >>> dc = dc.to_column()
        >>> dc = dc.runas_op['a', 'b'](func=lambda x: x+1)

        # >>> dc.show(limit=5, tablefmt='plain')
        #   a    b
        #   0    1
        #   1    2
        #   2    3
        #   3    4
        #   4    5

        >>> dc._iterable
        pyarrow.Table
        a: int64
        b: int64
        ----
        a: [[0,1,2,3,4,5,6,7,8,9]]
        b: [[1,2,3,4,5,6,7,8,9,10]]

        >>> len(dc._iterable)
        10
        """
        # pylint: disable=protected-access
        if self.get_executor() is None:
            if isinstance(self._iterable, ChunkedTable):
                if not self.is_stream:
                    tables = [
                        WritableTable(self.__table_apply__(chunk, unary_op))
                        for chunk in self._iterable.chunks()
                    ]
                else:
                    tables = (
                        WritableTable(self.__table_apply__(chunk, unary_op))
                        for chunk in self._iterable.chunks()
                    )
                return self._factory(ChunkedTable(chunks=tables))
            return self._factory(self.__table_apply__(self._iterable, unary_op))
        else:
            return self.pmap(unary_op)

    def __table_apply__(self, table, unary_op):
        # pylint: disable=protected-access
        return table.write_many(unary_op._index[1], self.__col_apply__(table, unary_op))

    def __col_apply__(self, cols, unary_op):
        # pylint: disable=protected-access
        import numpy as np
        import pyarrow as pa

        from reactive.types.tensor_array import TensorArray

        args = []
        # Multi inputs.
        if isinstance(unary_op._index[0], tuple):
            for name in unary_op._index[0]:
                try:
                    data = cols[name].combine_chunks()
                except:
                    data = cols[name].chunk(0)

                buffer = data.buffers()[-1]
                dtype = data.type
                if isinstance(data, TensorArray):
                    dtype = dtype.storage_type.value_type
                elif hasattr(data.type, "value_type"):
                    while hasattr(dtype, "value_type"):
                        dtype = dtype.value_type
                dtype = dtype.to_pandas_dtype()
                shape = (
                    [-1, *data.type.shape]
                    if isinstance(data, TensorArray)
                    else [len(data), -1]
                    if isinstance(data, pa.lib.ListArray)
                    else [len(data)]
                )
                args.append(np.frombuffer(buffer=buffer, dtype=dtype).reshape(shape))
                # args.append(data.to_numpy(zero_copy_only=False).reshape(shape))

        # Single input.
        else:
            try:
                data = cols[unary_op._index[0]].combine_chunks()
            except:
                data = cols[unary_op._index[0]].chunk(0)

            buffer = data.buffers()[-1]
            dtype = data.type
            if isinstance(data, TensorArray):
                dtype = dtype.storage_type.value_type
            elif hasattr(data.type, "value_type"):
                while hasattr(dtype, "value_type"):
                    dtype = dtype.value_type
            dtype = dtype.to_pandas_dtype()
            shape = (
                [-1, *data.type.shape]
                if isinstance(data, TensorArray)
                else [len(data), -1]
                if isinstance(data, pa.lib.ListArray)
                else [len(data)]
            )
            args.append(np.frombuffer(buffer=buffer, dtype=dtype).reshape(shape))
            # args.append(data.to_numpy(zero_copy_only=False).reshape(shape))

        return unary_op.__vcall__(*args)
