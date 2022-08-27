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

import types
from typing import Any, Dict

from pulse.hparam import param_scope


REGISTRY: Dict[str, Any] = {}


def resolve(name: str) -> Any:
    """
    Resolve operator by name
    """
    return REGISTRY.get(name, None)


def register(name: str = None):
    """
    Register a class, function, or callable as a towhee operator.

    Examples:

        1. register a function as operator
        >>> from pulse import register
        >>> @register
        ... def foo(x, y):
        ...     return x+y

        2. register a class as operator
        >>> @register
        ... class foo_cls:
        ...     def __init__(self, x):
        ...         self.x = x
        ...     def __call__(self, y):
        ...         return self.x + y

        By default, function/class name is used as operator name,
        which is used by the operator factory `towhee.ops` to invoke the operator.
        >>> from pulse import ops
        >>> op = ops.foo()
        >>> op(1, 2)
        3

        >>> op = ops.foo_cls(x=2)
        >>> op(3)
        5

        3. register operator with an alternative name:
        >>> @register(name='my_foo')
        ... def foo(x, y):
        ...     return x+y
        >>> ops.my_foo()(1,2)
        3

    Args:
        name (str, optional): operator name, will use the class/function name if None.
    """
    if callable(name):
        # the decorator is called directly without any arguments,
        # relaunch the register
        cls = name
        return register()(cls)

    def wrapper(cls):
        nonlocal name
        name = cls.__name__ if name is None else name

        if isinstance(cls, types.FunctionType):
            REGISTRY[name + "_func"] = cls

        # wrap a callable to a class
        if not isinstance(cls, type) and callable(cls):
            func = cls
            cls = type(
                cls.__name__,
                (object,),
                {
                    "__call__": lambda _, *arg, **kws: func(*arg, **kws),
                    "__doc__": func.__doc__,
                },
            )
        REGISTRY[name] = cls
        return cls

    return wrapper
