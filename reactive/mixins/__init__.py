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

from .audio import AudioMixin
from .column import ColumnMixin
from .compile import CompileMixin
from .computer_vision import ComputerVisionMixin
from .config import ConfigMixin
from .data_processing import DataProcessingMixin
from .dataframe import DataFrameMixin
from .dataset import DatasetMixin
from .dispatcher import DispatcherMixin
from .list import ListMixin
from .metric import MetricMixin
from .parallel import ParallelMixin
from .ray import RayMixin
from .safe import SafeMixin
from .serve import ServeMixin
from .state import StateMixin
from .stream import StreamMixin


class DCMixins(
    AudioMixin,
    CompileMixin,
    ComputerVisionMixin,
    ConfigMixin,
    DataProcessingMixin,
    DatasetMixin,
    DispatcherMixin,
    ListMixin,
    MetricMixin,
    ParallelMixin,
    RayMixin,
    SafeMixin,
    ServeMixin,
    StateMixin,
    StreamMixin,
):
    def __init__(self) -> None:  # pylint: disable=useless-super-delegation
        super().__init__()
