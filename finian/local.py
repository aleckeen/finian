#!/usr/bin/env python3

import copy

from _thread import get_ident


def release_local(local):
    local.__release_local__()


class Local:
    __slots__ = ("__storage__", "__ident_func__")

    def __init__(self):
        object.__setattr__(self, "__storage__", {})
        object.__setattr__(self, "__ident_func__", get_ident)

    def __iter__(self):
        return iter(self.__storage__.items())

    def __call__(self, proxy):
        return LocalProxy(self, proxy)

    def __release_local__(self):
        self.__storage__.pop(self.__ident_func__(), None)

    def __getattr__(self, name):
        try:
            return self.__storage__[self.__ident_func__()][name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        ident = self.__ident_func__()
        storage = self.__storage__
        try:
            storage[ident][name] = value
        except KeyError:
            storage[ident] = {name: value}

    def __delattr__(self, name):
        try:
            del self.__storage__[self.__ident_func__()][name]
        except KeyError:
            raise AttributeError(name)


class LocalStack:
    def __init__(self):
        self._local = Local()

    def __release_local__(self):
        self._local.__release_local__()

    @property
    def __ident_func__(self):
        return self._local.__ident_func__

    @__ident_func__.setter
    def __ident_func__(self, value):
        object.__setattr__(self._local, "__ident_func__", value)

    def __call__(self):
        def _lookup():
            rv = self.top
            if rv is None:
                raise RuntimeError("object unbound")
            return rv

        return LocalProxy(_lookup)

    def push(self, obj):
        """Pushes a new item to the stack"""
        rv = getattr(self._local, "stack", None)
        if rv is None:
            # noinspection PyDunderSlots,PyUnresolvedReferences
            self._local.stack = rv = []
        rv.append(obj)
        return rv

    def pop(self):
        """Removes the topmost item from the stack, will return the
        old value or `None` if the stack was already empty.
        """
        stack = getattr(self._local, "stack", None)
        if stack is None:
            return None
        elif len(stack) == 1:
            release_local(self._local)
            return stack[-1]
        else:
            return stack.pop()

    @property
    def top(self):
        """The topmost item on the stack.  If the stack is empty,
        `None` is returned.
        """
        try:
            return self._local.stack[-1]
        except (AttributeError, IndexError):
            return None


# noinspection PyArgumentList
class LocalProxy:
    def __init__(self, local, name=None):
        object.__setattr__(self, "_LocalProxy__local", local)
        object.__setattr__(self, "__name__", name)
        if callable(local) and not hasattr(local, "__release_local__"):
            object.__setattr__(self, "__wrapped__", local)

    def get_current_object(self):
        if not hasattr(self.__local, "__release_local__"):
            return self.__local()
        try:
            return getattr(self.__local, self.__name__)
        except AttributeError:
            raise RuntimeError(f"no object bound to {self.__name__}")

    @property
    def __dict__(self):
        try:
            return self.get_current_object().__dict__
        except RuntimeError:
            raise AttributeError("__dict__")

    def __repr__(self):
        try:
            obj = self.get_current_object()
        except RuntimeError:
            return f"<{type(self).__name__} unbound>"
        return repr(obj)

    def __bool__(self):
        try:
            return bool(self.get_current_object())
        except RuntimeError:
            return False

    def __dir__(self):
        try:
            return dir(self.get_current_object())
        except RuntimeError:
            return []

    def __getattr__(self, name):
        if name == "__members__":
            return dir(self.get_current_object())
        if name == "get_current_object":
            return self.get_current_object()
        return getattr(self.get_current_object(), name)

    def __setitem__(self, key, value):
        self.get_current_object()[key] = value

    def __delitem__(self, key):
        del self.get_current_object()[key]

    __setattr__ = lambda x, n, v: setattr(x.get_current_object(), n, v)
    __delattr__ = lambda x, n: delattr(x.get_current_object(), n)
    __str__ = lambda x: str(x.get_current_object())
    __lt__ = lambda x, o: x.get_current_object() < o
    __le__ = lambda x, o: x.get_current_object() <= o
    __eq__ = lambda x, o: x.get_current_object() == o
    __ne__ = lambda x, o: x.get_current_object() != o
    __gt__ = lambda x, o: x.get_current_object() > o
    __ge__ = lambda x, o: x.get_current_object() >= o
    __cmp__ = lambda x, o: cmp(x.get_current_object(), o)  # noqa
    __hash__ = lambda x: hash(x.get_current_object())
    __call__ = lambda x, *a, **kw: x.get_current_object()(*a, **kw)
    __len__ = lambda x: len(x.get_current_object())
    __getitem__ = lambda x, i: x.get_current_object()[i]
    __iter__ = lambda x: iter(x.get_current_object())
    __contains__ = lambda x, i: i in x.get_current_object()
    __add__ = lambda x, o: x.get_current_object() + o
    __sub__ = lambda x, o: x.get_current_object() - o
    __mul__ = lambda x, o: x.get_current_object() * o
    __floordiv__ = lambda x, o: x.get_current_object() // o
    __mod__ = lambda x, o: x.get_current_object() % o
    __divmod__ = lambda x, o: x.get_current_object().__divmod__(o)
    __pow__ = lambda x, o: x.get_current_object() ** o
    __lshift__ = lambda x, o: x.get_current_object() << o
    __rshift__ = lambda x, o: x.get_current_object() >> o
    __and__ = lambda x, o: x.get_current_object() & o
    __xor__ = lambda x, o: x.get_current_object() ^ o
    __or__ = lambda x, o: x.get_current_object() | o
    __div__ = lambda x, o: x.get_current_object().__div__(o)
    __truediv__ = lambda x, o: x.get_current_object().__truediv__(o)
    __neg__ = lambda x: -(x.get_current_object())
    __pos__ = lambda x: +(x.get_current_object())
    __abs__ = lambda x: abs(x.get_current_object())
    __invert__ = lambda x: ~(x.get_current_object())
    __complex__ = lambda x: complex(x.get_current_object())
    __int__ = lambda x: int(x.get_current_object())
    __long__ = lambda x: long(x.get_current_object())  # noqa
    __float__ = lambda x: float(x.get_current_object())
    __oct__ = lambda x: oct(x.get_current_object())
    __hex__ = lambda x: hex(x.get_current_object())
    __index__ = lambda x: x.get_current_object().__index__()
    __coerce__ = lambda x, o: x.get_current_object().__coerce__(x, o)
    __enter__ = lambda x: x.get_current_object().__enter__()
    __exit__ = lambda x, *a, **kw: x.get_current_object().__exit__(*a, **kw)
    __radd__ = lambda x, o: o + x.get_current_object()
    __rsub__ = lambda x, o: o - x.get_current_object()
    __rmul__ = lambda x, o: o * x.get_current_object()
    __rdiv__ = lambda x, o: o / x.get_current_object()
    __rtruediv__ = __rdiv__
    __rfloordiv__ = lambda x, o: o // x.get_current_object()
    __rmod__ = lambda x, o: o % x.get_current_object()
    __rdivmod__ = lambda x, o: x.get_current_object().__rdivmod__(o)
    __copy__ = lambda x: copy.copy(x.get_current_object())
    __deepcopy__ = lambda x, memo: copy.deepcopy(x.get_current_object(), memo)
