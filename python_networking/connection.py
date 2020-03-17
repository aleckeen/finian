#!/usr/bin/env python3

import rsa
import json
import threading

from typing import Dict, Any, Callable, Union, Tuple

from .tcpsocket import TCPSocket, Result

DataType = Union[Dict[str, Any], bytes]
RecvCallbackType = Callable[["Connection", Result], None]
ConnectionBrokeCallbackType = Callable[["Connection"], None]

# Protocol 1
def protocol_request_pubkey(connection: "Connection", result: Result):
    connection.send(connection.pubkey, 2)

#Protocol 2
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
        self._connection_broke_callback: ConnectionBrokeCallbackType = lambda c: None
        self._pubkey: rsa.key.PublicKey = None
        self.protocol(1, False)(protocol_request_pubkey)
        self.protocol(2, False)(protocol_recv_pubkey)


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
            self._recp_pubkey = value


    @property
    def privkey(self):
        return self.socket.privkey


    @privkey.setter
    def privkey(self, value):
        self.socket.privkey = value


    @property
    def recp_pubkey(self):
        return self.socket.recp_pubkey


    @property
    def recp_pubkey(self, value):
        self.socket.recp_pubkey = value


    def disconnect(self):
        self.socket.disconnect()


    def protocol(self, protocol: int, threaded: bool = True):
        def setter(callback: RecvCallbackType):
            def threaded_callback(*args):
                thread = threading.Thread(target=callback, args=args)
                thread.daemon = True
                thread.run()
            self._recv_callbacks[protocol] = threaded_callback if threaded else callback
        return setter

   
    def connection_broke(self, callback: ConnectionBrokeCallbackType):
        self._connection_broke_callback = callback


    def recv(self) -> Result:
        result = self.socket.recv()
        if result is None:
            return None
        if not result.encrypted and result.json:
            result.data = json.loads(result.data.decode())
        return result


    def send(self, data: DataType, protocol: int = 0):
        json = False
        if isinstance(data, dict):
            data = json.dumps(data).encode()
            json = True
        self.socket.send(data, json, protocol)


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
