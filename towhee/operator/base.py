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

from abc import abstractmethod
from abc import ABC
from enum import Enum
from enum import Flag, auto

# NotShareable:
#    Stateful & reusable operator.

# NotRusable:
#    Stateful & not reusable operator.

# Shareable:
#    Stateless operator

SharedType = Enum("SharedType", ("NotShareable", "NotReusable", "Shareable"))


class OperatorFlag(Flag):
    EMPTYFLAG = auto()
    STATELESS = auto()
    REUSEABLE = auto()


class Operator(ABC):
    """
    Operator base class, implements __init__ and __call__,

    Examples:
        class AddOperator(Operator):
            def __init__(self, factor: int):
                self._factor = factor

            def __call__(self, num) -> NamedTuple("Outputs", [("sum", int)]):
                Outputs = NamedTuple("Outputs", [("sum", int)])
                return Outputs(self._factor + num)
    """

    @abstractmethod
    def __init__(self):
        """
        Init operator, before a graph starts, the framework will call Operator __init__ function.

        Args:

        Raises:
            An exception during __init__ can terminate the graph run.
        """
        self._key = ""

    @abstractmethod
    def __call__(self):
        """
        The framework calls __call__ function repeatedly for every input data.

        Args:

        Returns:

        Raises:
            An exception during __init__ can terminate the graph run.
        """
        raise NotImplementedError

    @property
    def key(self):
        return self._key

    @property
    def shared_type(self):
        return SharedType.NotShareable

    @key.setter
    def key(self, value):
        self._key = value

    @property
    def flag(self):
        return OperatorFlag.STATELESS | OperatorFlag.REUSEABLE
