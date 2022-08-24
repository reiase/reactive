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

from datacollection.functional import (api, dc, dummy_input, from_df, glob,
                                       glob_zip, range, read_audio,
                                       read_camera, read_csv, read_json,
                                       read_video, read_zip)

from .datacollection import DataCollection, DataFrame
from .execution.registry import register
from .hparam import HyperParameter as Document
from .hparam import param_scope
from .types import Entity

# Place all functions that are meant to be called by towhee.func() here aftering importing them.
__all__ = [
    "register",
    "param_scope",
    "Document",
    "DataCollection",
    "DataFrame",
    "Entity",
    "range",
    "glob",
    "glob_zip",
    "from_df",
    "read_audio",
    "read_camera",
    "read_csv",
    "read_json",
    "read_video",
    "read_zip",
    "dc",
    "api",
    "dummy_input",
]

__import__("pkg_resources").declare_namespace(__name__)
