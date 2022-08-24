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

# pylint: disable=unused-import
# pylint: disable=dangerous-default-value

import os
import threading
from typing import Any, Dict, List, Tuple

from towhee.engine.operator_loader import OperatorLoader
from towhee.hparam.hyperparameter import dynamic_dispatch, param_scope

from .execution.base_execution import BaseExecution
from .execution.pandas_execution import PandasExecution
from .execution.stateful_execution import StatefulExecution
from .execution.vectorized_execution import VectorizedExecution


def op(
    operator_src: str,
    tag: str = "main",
    arg: List[Any] = [],
    kwargs: Dict[str, Any] = {},
):
    """
    Entry method which takes either operator tasks or paths to python files or class in notebook.
    An `Operator` object is created with the init args(kwargs).
    Args:
        operator_src (`str`):
            operator name or python file location or class in notebook.
        tag (`str`):
            Which tag to use for operators on hub, defaults to `main`.
    Returns
        (`typing.Any`)
            The `Operator` output.
    """
    if isinstance(operator_src, type):
        class_op = type("operator", (operator_src,), kwargs)
        return class_op.__new__(class_op, **kwargs)

    loader = OperatorLoader()
    if os.path.isfile(operator_src):
        return loader.load_operator_from_path(operator_src, arg, kwargs)
    else:
        return loader.load_operator(operator_src, arg, kwargs, tag)


class _OperatorLazyWrapper(BaseExecution, PandasExecution, StatefulExecution, VectorizedExecution):  #  #  #  #
    """
    operator wrapper for lazy initialization. Inherits from different execution strategies.
    """

    def __init__(
        self,
        real_name: str,
        index: Tuple[str],
        load: bool = True,
        arg: List[Any] = [],
        kws: Dict[str, Any] = {},
    ) -> None:
        self._name = real_name
        self._index = index
        self._arg = arg
        self._kws = kws
        self._lock = threading.Lock()
        self._op = None
        if load:
            self.__check_init__()
            if self._op is None:
                raise Exception(f"failed to load operator {real_name}")

    def __check_init__(self):
        with self._lock:
            if self._op is None:
                #  Called with param scope in order to pass index in to op.
                with param_scope(index=self._index):
                    self._op = op(self._name, "main", arg=self._arg, kwargs=self._kws)
                    if hasattr(self._op, "__vcall__"):
                        self.__has_vcall__ = True
        return self._op

    def get_op(self):
        self.__check_init__()
        return self._op

    @property
    def op_config(self):
        self.__check_init__()
        return self._op_config

    @property
    def function(self):
        return self._name

    @property
    def init_args(self):
        return self._kws

    @staticmethod
    def callback(real_name: str, index: Tuple[str], *arg, **kws):
        return _OperatorLazyWrapper(real_name, index, arg=arg, kws=kws)


@dynamic_dispatch
def ops(*arg, **kws):
    """
    Entry point for creating operator instances, for example:

    >>> op_instance = ops.my_namespace.my_repo_name(init_arg1=xxx, init_arg2=xxx)
    """

    # pylint: disable=protected-access
    with param_scope() as hp:
        real_name = hp._name
        index = hp._index
    return _OperatorLazyWrapper.callback(real_name, index, *arg, **kws)


def create_op(
    func,
    name: str = "tmp",
    index: Tuple[str] = None,
    arg: List[Any] = [],
    kws: Dict[str, Any] = {},
) -> None:
    # pylint: disable=protected-access
    operator = _OperatorLazyWrapper(name, index, load=False, arg=arg, kws=kws)
    operator._op = func
    return operator
