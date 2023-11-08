from typing import Any


class Document(dict):
    """Data type for json document

    Examples
    --------
        >>> doc = Document(**{"a": 1, "b.c":2})
        >>> doc
        {'a': 1, 'b': {'c': 2}}

        >>> getattr(doc, "b.c")
        2

        >>> doc = Document()
        >>> setattr(doc, "a", 1)
        >>> setattr(doc, "b.c", 2)
        >>> doc
        {'a': 1, 'b': {'c': 2}}

        >>> getattr(doc, "a")
        1
        >>> getattr(doc, "b")
        {'c': 2}
        >>> getattr(doc, "b.c")
        2
    """

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattr__(self, name):
        if "." in name:
            head, tail = name.split(".", 1)
            return getattr(self[head], tail)
        if name in self:
            return self[name]
        return None

    def __setattr__(self, name: str, value: Any) -> None:
        if "." in name:
            head, tail = name.split(".", 1)
            if not head in self:
                self[head] = Document()
            setattr(self[head], tail, value)
            return self
        if isinstance(value, dict):
            self[name] = Document(**value)
        else:
            self[name] = value
        return self
