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

from typing import Any, Callable, Dict, List

from datacollection.hparam import param_scope

from .registry import resolve


class OperatorLoader:
    """Wrapper class used to load operators from either local cache or a remote
    location.

    Args:
        cache_path: (`str`)
            Local cache path to use. If not specified, it will default to
            `$HOME/.towhee/operators`.
    """

    def __init__(self, cache_path: str = None):
        pass

    def load_operator(
        self, function: str, arg: List[Any], kws: Dict[str, Any], tag: str
    ) -> Callable:  # pylint: disable=unused-argument
        op = resolve(function)
        return self.instance_operator(op, arg, kws) if op is not None else None

    def instance_operator(self, op, arg: List[Any], kws: Dict[str, Any]) -> Callable:
        with param_scope() as hp:
            return op(*arg, **kws) if kws is not None else op()
