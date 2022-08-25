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

from ..execution.factory import create_op, ops
from ..hparam import param_scope


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

    >>> from datacollection import register
    >>> from datacollection import ops
    >>> from datacollection import DataCollection
    >>> @register(name='add_1')
    ... def add_1(x):
    ...     return x+1

    >>> dc = DataCollection.range(5).stream()
    >>> dc.add_1['a','b','c']() #doctest: +ELLIPSIS
    <map object at ...>
    """

    def resolve(self, stack: FrameType = None, *arg, **kws):
        locals_ = stack.f_locals if isinstance(stack, FrameType) else {}
        globals_ = stack.f_globals if isinstance(stack, FrameType) else {}
        with param_scope() as ps:
            if self._jit is not None:
                op = self.jit_resolve(ps._name, ps._index, *arg, **kws)
                if op is not None:
                    return op
            if "." in ps._name:
                mod_name, attr_name = ps._name.split(".", 1)
            else:
                mod_name, attr_name = ps._name, None
            mod = globals_.get(mod_name, None)
            mod = locals_.get(mod_name, mod)

            if mod is ops:
                return getattr(ops, attr_name)[ps._index](*arg, **kws)
            if mod is not None:
                op = getattr_nested(mod, attr_name) if attr_name is not None else mod
            else:
                op = None
            if op is not None and callable(op):
                if isinstance(op, type):
                    instance = op(*arg, **kws)
                else:
                    instance = op
                return create_op(instance, ps._name, ps._index, arg, kws)
            return getattr(ops, ps._name)[ps._index](*arg, **kws)