#!/usr/bin/env python3

import json
import sys
import threading
from typing import Any, Callable, Dict, Optional
from io import BytesIO

import rsa

from .ctx import ConnContext
from .tcpsocket import Result, TCPSocket, DataType

_sentinel = object()

RecvCallbackType = Callable[["Connection", Result], None]
ConnectionBrokeCallbackType = Callable[["Connection"], None]


# Protocol 1
def protocol_request_pubkey(connection: "Connection", _):
    connection.send(connection.pubkey, 2)


# Protocol 2
def protocol_recv_pubkey(connection: "Connection", result: Result):
    connection.recp_pubkey = result.data


class Connection:
    def __init__(self, socket: TCPSocket = None):
        if socket is None:
            socket = TCPSocket()
        self.socket: TCPSocket = socket
        self.session: Dict[str, Any] = {}
        self._recv_callbacks: Dict[int, RecvCallbackType] = {}
        self._recv_no_protocol_callback: RecvCallbackType = lambda c, r: None
        self._connection_broke_callback: ConnectionBrokeCallbackType = \
            lambda c: None
        self._pubkey: Optional[rsa.key.PublicKey] = None
        self.protocol(1, False)(protocol_request_pubkey)
        self.protocol(2, False)(protocol_recv_pubkey)
        self.teardown_conn_context_funcs = []

    def teardown_conn_context(self, f):
        self.teardown_conn_context_funcs.append(f)
        return f

    def conn_context(self):
        return ConnContext(self)

    def do_teardown_conn_context(self, exc=_sentinel):
        if exc is _sentinel:
            exc = sys.exc_info()[1]
        for func in reversed(self.teardown_conn_context_funcs):
            func(exc)

    @property
    def pubkey(self):
        if self._pubkey is None:
            return None
        return self._pubkey.save_pkcs1()

    @pubkey.setter
    def pubkey(self, value):
        if isinstance(value, bytes):
            self._pubkey = rsa.key.PublicKey.load_pkcs1(value)
        else:
            self._pubkey = value

    @property
    def privkey(self):
        return self.socket.privkey

    @privkey.setter
    def privkey(self, value):
        self.socket.privkey = value

    @property
    def recp_pubkey(self):
        return self.socket.recp_pubkey

    @recp_pubkey.setter
    def recp_pubkey(self, value):
        self.socket.recp_pubkey = value

    def disconnect(self):
        self.socket.disconnect()

    def protocol(self, protocol: int, threaded: bool = True):
        def decorator(callback: RecvCallbackType):
            def threaded_callback(*args):
                thread = threading.Thread(target=callback, args=args)
                thread.daemon = True
                thread.start()

            self._recv_callbacks[protocol] = \
                threaded_callback if threaded else callback

        return decorator

    def connection_broke(self, callback: ConnectionBrokeCallbackType):
        self._connection_broke_callback = callback

    def recv(self) -> Optional[Result]:
        result = self.socket.recv()
        if result is None:
            return None
        if not result.encrypted and result.json:
            result.data = json.loads(result.data.decode())
        return result

    def send(self, data: DataType, protocol: int = 0):
        is_json = False
        if isinstance(data, dict):
            data = json.dumps(data).encode()
            is_json = True
        self.socket.send(data, is_json, protocol)

    def listen(self):
        while True:
            result = self.recv()
            if result is None:
                self._connection_broke_callback(self)
                break
            if result.protocol in self._recv_callbacks:
                callback = self._recv_callbacks[result.protocol]
            else:
                callback = self._recv_no_protocol_callback
            callback(self, result)

    def request_recv_pubkey(self):
        self.socket.send(None, False, 1)
