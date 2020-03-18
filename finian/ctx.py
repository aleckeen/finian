#!/usr/bin/env python3

import sys
from .globals import _conn_ctx_stack
from .signals import conncontext_pushed
from .signals import conncontext_popped

_sentinel = object()


class ConnContext:
    def __init__(self, conn):
        self.conn = conn
        self._refcnt = 0

    def push(self):
        self._refcnt += 1
        if hasattr(sys, "exc_clear"):
            sys.exc_clear()
        _conn_ctx_stack.push(self)
        conncontext_pushed.send(self.conn)

    def pop(self, exc=_sentinel):
        try:
            self._refcnt -= 1
            if self._refcnt <= 0:
                if exc is _sentinel:
                    exc = sys.exc_info()[1]
                self.conn.do_teardown_conncontext(exc)
        finally:
            rv = _conn_ctx_stack.pop()
        assert rv is self, "Popped wrong conn context.  (%r insted of %r)" % (rv, self)
        conncontext_popped.send(self.conn)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        self.pop(exc_val)
