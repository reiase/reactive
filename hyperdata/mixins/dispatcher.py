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

from types import FrameType

from hyperparameter import param_scope

from ..execution.factory import create_op, ops


def getattr_nested(mod, path):
    # pylint: disable=bare-except

    obj = mod
    for par in path.split("."):
        try:
            obj = getattr(obj, par)
        except:
            return None
    return obj


class DispatcherMixin:
    """
    Mixin for call dispatcher for data collection

    >>> from hyperdata import register
    >>> from hyperdata import ops
    >>> from hyperdata import DataCollection

    1. resolve operator from registry

    >>> @register(name='add_1')
    ... def add_1(x):
    ...     return x+1

    >>> dc = DataCollection.range(5).stream()
    >>> dc.add_1['a','b','c']() #doctest: +ELLIPSIS
    <map object at ...>

    2. resolve operator from local scope

    >>> def add_2(x):
    ...     return x+2
    >>> dc = DataCollection.range(5).stream()
    >>> dc.range(5).add_2()
    [2, 3, 4, 5, 6]

    3. resolve operator from module
    >>> import math
    >>> dc.range(5).math.sin()
    [0.0, 0.8414709848078965, 0.9092974268256817, 0.1411200080598672, -0.7568024953079282]
    """

    def resolve(self, stack: FrameType = None, *arg, **kws):
        locals_ = stack.f_locals if isinstance(stack, FrameType) else {}
        globals_ = stack.f_globals if isinstance(stack, FrameType) else {}
        with param_scope() as ps:
            name = ps._name | None
            index = ps._index | None
            if self._jit is not None:
                op = self.jit_resolve(name, index, *arg, **kws)
                if op is not None:
                    return op
            if name and "." in name:
                mod_name, attr_name = name.split(".", 1)
            else:
                mod_name, attr_name = name, None
            mod = globals_.get(mod_name, None)
            mod = locals_.get(mod_name, mod)

            if mod is ops:
                return getattr(ops, attr_name)[index](*arg, **kws)
            if mod is not None:
                op = getattr_nested(mod, attr_name) if attr_name is not None else mod
            else:
                op = None
            if op is not None and callable(op):
                if isinstance(op, type):
                    instance = op(*arg, **kws)
                else:
                    instance = op
                return create_op(instance, name, index, arg, kws)
            return getattr(ops, name)[index](*arg, **kws)
