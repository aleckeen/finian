#!/usr/bin/env python3

import sys

from .globals import _conn_ctx_stack

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

    def pop(self, exc=_sentinel):
        try:
            self._refcnt -= 1
            if self._refcnt <= 0:
                if exc is _sentinel:
                    exc = sys.exc_info()[1]
                self.conn.do_teardown_conn_context(exc)
        finally:
            rv = _conn_ctx_stack.pop()
        assert(
                rv is self
        ), "Popped wrong conn context.  (%r instead of %r)" % (rv, self)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        self.pop(exc_val)
