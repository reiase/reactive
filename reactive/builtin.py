from typing import Callable

from .execution.registry import register


@register
class runas_op:
    """
    Convert a user-defined function as an operator and execute.
    Args:
        func (`Callable`):
            The user-defined function.
    Examples:
    >>> from reactive import DataCollection
    >>> from reactive import Entity
    >>> entities = [Entity(a=i, b=i) for i in range(5)]
    >>> dc = DataCollection(entities)
    >>> res = dc.runas_op['a', 'b'](func=lambda x: x - 1).to_list()
    >>> res[0].a == res[0].b + 1
    True
    """

    def __init__(self, func: Callable):
        self._func = func

    def __call__(self, *args, **kws):
        return self._func(*args, **kws)
