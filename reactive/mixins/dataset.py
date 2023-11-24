# Copyright 2021 Zilliz. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from pathlib import Path

from reactive.types.entity import Entity


def _url_valid(uri) -> bool:
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if re.match(regex, uri) is not None:
        return True
    return False


class DatasetMixin:
    """
    Mixin for dealing with dataset
    """

    @classmethod
    def from_pandas(cls, dataframe, stream=False):
        """Create DataFrame from pandas

        Examples:
            >>> import pandas as pd
            >>> import reactive
            >>> df = pd.DataFrame({"a": range(5), "b": range(5)})
            >>> reactive.from_pandas(df).df
               a  b
            0  0  0
            1  1  1
            2  2  2
            3  3  3
            4  4  4
        """
        if stream:
            return cls(dataframe.iterrows()).map(lambda x: Entity(**x[1].to_dict()))
        return cls(dataframe)

    def to_pandas(self):
        """Create Pandas DataFrame

        Examples:
            >>> import reactive
            >>> reactive.new([{"a":1}, {"a":2}]).to_df().as_entity().to_pandas()
               a
            0  1
            1  2
        """
        import pandas as pd

        return pd.DataFrame.from_records(data=self.as_dict().to_list())

    # pylint: disable=import-outside-toplevel
    @classmethod
    def from_glob(cls, *args):  # pragma: no cover
        """
        generate a file list with `pattern`
        """
        from glob import glob

        files = []
        for path in args:
            files.extend(glob(path))
        if len(files) == 0:
            raise FileNotFoundError(f"There is no files with {args}.")
        return cls(files)

    @classmethod
    def read_zip(cls, url, pattern, mode="r"):  # pragma: no cover
        """load files from url/path.

        Args:
            zip_src (`Union[str, path]`):
                The path leads to the image.
            pattern (`str`):
                The filename pattern to extract.
            mode (str):
                file open mode.

        Returns:
            (File): The file handler for file in the zip file.
        """
        from glob import fnmatch
        from io import BytesIO
        from urllib.request import urlopen
        from zipfile import ZipFile

        def inner():
            if _url_valid(str(url)):
                with urlopen(url) as zip_file:
                    zip_path = BytesIO(zip_file.read())
            else:
                zip_path = str(Path(url).resolve())
            with ZipFile(zip_path, "r") as zfile:
                file_list = zfile.namelist()
                path_list = fnmatch.filter(file_list, pattern)
                for path in path_list:
                    with zfile.open(path, mode=mode) as f:
                        yield f.read()

        return cls(inner())

    @classmethod
    def read_json(cls, *args, stream=False, **kwargs):
        """Read JSON file

        Examples:
            >>> import pandas as pd
            >>> import io
            >>> df = pd.DataFrame({"a": range(5), "b": range(5)})
            >>> buff = io.StringIO()
            >>> df.to_json(buff, orient="records", lines=True)
            >>> _ = buff.seek(0)

            >>> import reactive
            >>> reactive.read_json(buff)
               a  b
            0  0  0
            1  1  1
            2  2  2
            3  3  3
            4  4  4

            >>> _ = buff.seek(0)
            >>> reactive.read_json(buff, stream=True).as_str().to_list()[0]
            "{'a': 0, 'b': 0}"
        """
        kwargs["lines"] = True
        if stream:
            kwargs["chunksize"] = 1024
        import pandas as pd

        reader = pd.read_json(*args, **kwargs)
        if hasattr(reader, "get_chunk") or hasattr(reader, "chunksize"):

            def inner():
                for chunk in reader:
                    for row in chunk.iterrows():
                        yield Entity(**row[1].to_dict())

            return cls(inner())
        return cls.from_pandas(reader, stream=stream)

    @classmethod
    def read_csv(cls, *args, stream=False, **kwargs):
        """Read CSV file

        Examples:
            >>> import pandas as pd
            >>> import io
            >>> df = pd.DataFrame({"a": range(5), "b": range(5)})
            >>> buff = io.StringIO()
            >>> df.to_csv(buff, index=False)
            >>> _ = buff.seek(0)

            >>> import reactive
            >>> reactive.read_csv(buff)
               a  b
            0  0  0
            1  1  1
            2  2  2
            3  3  3
            4  4  4

            >>> _ = buff.seek(0)
            >>> reactive.read_csv(buff, stream=True).as_str().to_list()[0]
            "{'a': 0, 'b': 0}"
        """
        if stream:
            kwargs["iterator"] = True
            kwargs["chunksize"] = 1024
        import pandas as pd

        reader = pd.read_csv(*args, **kwargs)
        if hasattr(reader, "get_chunk"):

            def inner():
                for chunk in reader:
                    for row in chunk.iterrows():
                        yield Entity(**row[1].to_dict())

            return cls(inner())
        return cls.from_pandas(reader, stream=stream)

    def to_csv(self, *args, **kwargs):
        """Save dc as a csv file.

        Examples:
            >>> import pandas as pd
            >>> import io
            >>> buff = io.StringIO()

            >>> import reactive
            >>> dc = reactive.new([{"a":1}, {"a":2}]).to_df().as_entity()
            >>> dc.to_csv(buff)
            >>> _ = buff.seek(0)
            >>> print(buff.read())
            ,a
            0,1
            1,2
            <BLANKLINE>
        """
        self.to_pandas().to_csv(*args, **kwargs)

    # pylint: disable=dangerous-default-value
    def split_train_test(self, size: list = [0.9, 0.1], **kws):
        """
        Split DataCollection to train and test data.

        Args:
            size (`list`):
                The size of the train and test.

        Examples:

        >>> import reactive
        >>> dc = reactive.range(10)
        >>> train, test = dc.split_train_test(shuffle=False)
        >>> train.to_list()
        [0, 1, 2, 3, 4, 5, 6, 7, 8]
        >>> test.to_list()
        [9]
        """
        from sklearn.model_selection import train_test_split

        train_size = size[0]
        test_size = size[1]
        train, test = train_test_split(
            self._iterable, train_size=train_size, test_size=test_size, **kws
        )
        return self._factory(train), self._factory(test)
