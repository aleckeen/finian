#!/usr/bin/env python3

from .local import LocalProxy
from .local import LocalStack

_app_ctx_err_msg = """\
Working outside of application context.
This typically means that you attempted to use functionality that needed
to interface with the current application object in some way. To solve
this, set up an application context with conn.conn_context().\
"""


def _find_conn():
    top = _conn_ctx_stack.top
    if top is None:
        raise RuntimeError(_app_ctx_err_msg)
    return top.conn


_conn_ctx_stack = LocalStack()
current_conn = LocalProxy(_find_conn)
