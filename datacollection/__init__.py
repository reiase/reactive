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

# pylint: disable=redefined-builtin

VERSION = "0.1.0"

from .datacollection import DataCollection, DataFrame
from .execution.factory import ops
from .execution.registry import register
from .hparam import HyperParameter as Document
from .hparam import HyperParameter as State
from .hparam import dynamic_dispatch, param_scope
from .types import Entity

from_glob = DataCollection.from_glob
from_pandas = DataFrame.from_pandas
read_audio = DataCollection.read_audio
read_camera = DataCollection.read_camera
read_csv = DataFrame.read_csv
read_json = DataFrame.read_json
read_video = DataCollection.read_video
read_zip = DataCollection.read_zip


def _range(*args, **kwargs):  # pragma: no cover
    """
    Return a DataCollection of a range of values.
    Examples:

    1. create a simple data collection;

    >>> import datacollection as dc
    >>> dc.range(5).to_list() #doctest: +SKIP
    [0, 1, 2, 3, 4]

    2. create a data collection of schema'd range.

    >>> dc.range['nums'](5).select['nums']().as_raw() #doctest: +SKIP
    [0, 1, 2, 3, 4]
    """

    index = param_scope()._index
    if index is None:
        return DataCollection.range(*args, **kwargs)
    return DataFrame.range(*args, **kwargs).map(lambda x: Entity(**{index: x}))


range = dynamic_dispatch(_range)


def _api():
    """
    Create an API input, for building RestFul API or application API.

    Examples:

    >>> from fastapi import FastAPI
    >>> from fastapi.testclient import TestClient
    >>> app = FastAPI()

    >>> import datacollection as dc
    >>> with dc.api() as api:
    ...     app1 = (
    ...         api.map(lambda x: x+' -> 1')
    ...            .map(lambda x: x+' => 1')
    ...            .serve('/app1', app)
    ...     )

    >>> with dc.api['x']() as api:
    ...     app2 = (
    ...         api.runas_op['x', 'x_plus_1'](func=lambda x: x+' -> 2')
    ...            .runas_op['x_plus_1', 'y'](func=lambda x: x+' => 2')
    ...            .select['y']()
    ...            .serve('/app2', app)
    ...     )

    >>> with dc.api() as api:
    ...     app2 = (
    ...         api.parse_json()
    ...            .runas_op['x', 'x_plus_1'](func=lambda x: x+' -> 3')
    ...            .runas_op['x_plus_1', 'y'](func=lambda x: x+' => 3')
    ...            .select['y']()
    ...            .serve('/app3', app)
    ...     )

    >>> client = TestClient(app)
    >>> client.post('/app1', '1').text
    '"1 -> 1 => 1"'
    >>> client.post('/app2', '2').text
    '{"y":"2 -> 2 => 2"}'
    >>> client.post('/app3', '{"x": "3"}').text
    '{"y":"3 -> 3 => 3"}'
    """
    return DataFrame.api(index=param_scope()._index)


api = dynamic_dispatch(_api)


def _dc(iterable):
    """
    Return a DataCollection.

    Examples:

    1. create a simple data collection;

    >>> import datacollection as dc
    >>> dc.dc([0, 1, 2]).to_list()
    [0, 1, 2]

    2. create a data collection of structural data.

    >>> dc.dc['column']([0, 1, 2]).to_list()
    [<Entity dict_keys(['column'])>, <Entity dict_keys(['column'])>, <Entity dict_keys(['column'])>]

    >>> dc.dc['string', 'int']([['a', 1], ['b', 2], ['c', 3]]).to_list()
    [<Entity dict_keys(['string', 'int'])>, <Entity dict_keys(['string', 'int'])>, <Entity dict_keys(['string', 'int'])>]
    """

    index = param_scope()._index
    if index is None:
        return DataCollection(iterable)
    if isinstance(index, (list, tuple)):
        return DataFrame(iterable).map(lambda x: Entity(**dict(zip(index, x))))
    return DataFrame(iterable).map(lambda x: Entity(**{index: x}))


dc = dynamic_dispatch(_dc)


# Place all functions that are meant to be called by towhee.func() here aftering importing them.
__all__ = [
    "ops",
    "register",
    "param_scope",
    "Document",
    "DataCollection",
    "DataFrame",
    "Entity",
    "State",
    "range",
    "from_pandas",
    "read_audio",
    "read_camera",
    "read_csv",
    "read_json",
    "read_video",
    "read_zip",
    "dc",
    "api",
]
