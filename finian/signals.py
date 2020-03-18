#!/usr/bin/env python3

class Namespace:
    def signal(self, name, doc=None):
        return _FakeSignal(name, doc)


class _FakeSignal:
    def __init__(self, name, doc=None):
        self.name = name
        self.__doc__ = doc

    def send(self, *args, **kwargs):
        pass

    def _fail(self, *args, **kwargs):
        raise RuntimeError("Signaling support is unavailable.")

    connect = connect_via = connected_to = temporarily_connected_to = _fail
    disconnect = _fail
    has_receivers_for = receivers_for = _fail
    del _fail


_signals = Namespace()

conncontext_pushed = _signals.signal("appcontext-pushed")
conncontext_popped = _signals.signal("appcontext-popped")
conncontext_tearing_down = _signals.signal("appcontext-tearing-down")
