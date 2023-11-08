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

from typing import Any, Callable

from hyperparameter import param_scope

from .audio_frame import AudioFrame
from .document import Document
from .entity import Entity, EntityView
from .option import Empty, Option, Some
from .video_frame import VideoFrame


class DynamicDispatch:
    """
    Dynamic call dispatch

    Examples:

    >>> @dynamic_dispatch
    ... def debug_print(*args, **kws):
    ...     hp = param_scope()
    ...     name = hp._name | None
    ...     index = hp._index | None
    ...     return (name, index, args, kws)

    >>> debug_print()
    (None, None, (), {})
    >>> debug_print.a()
    ('a', None, (), {})
    >>> debug_print.a.b.c()
    ('a.b.c', None, (), {})
    >>> debug_print[1]()
    (None, 1, (), {})
    >>> debug_print[1,2]()
    (None, (1, 2), (), {})
    >>> debug_print(1,2, a=1,b=2)
    (None, None, (1, 2), {'a': 1, 'b': 2})

    >>> debug_print.a.b.c[1,2](1, 2, a=1, b=2)
    ('a.b.c', (1, 2), (1, 2), {'a': 1, 'b': 2})
    """

    def __init__(self, func: Callable, name=None, index=None):
        self._func = func
        self._name = name
        self._index = index

    def __call__(self, *args, **kws) -> Any:
        with param_scope(_index=self._index, _name=self._name):
            return self._func(*args, **kws)

    def __getattr__(self, name: str) -> Any:
        if self._name is not None:
            name = "{}.{}".format(self._name, name)
        return dynamic_dispatch(self._func, name, self._index)

    def __getitem__(self, index):
        return dynamic_dispatch(self._func, self._name, index)


def dynamic_dispatch(func, name=None, index=None):
    """Wraps function with a class to allow __getitem__ and __getattr__ on a function."""
    new_class = type(
        func.__name__,
        (
            DynamicDispatch,
            object,
        ),
        dict(__doc__=func.__doc__),
    )
    return new_class(func, name, index)


__all__ = [
    "AudioFrame",
    "VideoFrame",
    "Empty",
    "Some",
    "Option",
    "Entity",
    "EntityView",
    "dynamic_dispatch",
]
