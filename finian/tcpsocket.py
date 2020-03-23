#!/usr/bin/env python3

import socket
import struct
from typing import Optional, Union, Dict, Any

import rsa

DataType = Union[Dict[str, Any], bytes]


class Result:
    # is encrypted, is json, protocol, data
    def __init__(self, encrypted: bool, is_json: bool,
                 protocol: int, data: DataType):
        self.encrypted: bool = encrypted
        self.json: bool = is_json
        self.protocol: int = protocol
        self.data: DataType = data


class TCPSocket:
    def __init__(self, sock: socket.socket = None):
        if sock is None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.socket = sock
        self._recp_pubkey: Optional[rsa.key.PublicKey] = None
        self._privkey: Optional[rsa.key.PrivateKey] = None

    def setserveropt(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    @property
    def recp_pubkey(self):
        if self._recp_pubkey is None:
            return None
        return self._recp_pubkey.save_pkcs1()

    @recp_pubkey.setter
    def recp_pubkey(self, value):
        if isinstance(value, bytes):
            self._recp_pubkey = rsa.key.PublicKey.load_pkcs1(value)
        else:
            self._recp_pubkey = value

    @property
    def privkey(self):
        if self._privkey is None:
            return None
        return self._privkey.save_pkcs1()

    @privkey.setter
    def privkey(self, value):
        if isinstance(value, bytes):
            self._privkey = rsa.key.PrivateKey.load_pkcs1(value)
        else:
            self._privkey = value

    @property
    def bind(self):
        return self.socket.bind

    @property
    def listen(self):
        return self.socket.listen

    @property
    def connect(self):
        return self.socket.connect

    def accept(self):
        conn, _ = self.socket.accept()
        return TCPSocket(conn)

    def send(self, data: Optional[bytes], is_json: bool = True,
             protocol: int = 0):
        if data is None:
            data = "".encode()
        if self._recp_pubkey is not None:
            data = rsa.encrypt(data, self._recp_pubkey)
        # data size, is encrypted, is json, protocol
        header = struct.pack(
            "I??H", len(data), self._recp_pubkey is not None,
            is_json, protocol
        )
        self.socket.sendall(header + data)

    def recv(self) -> Optional[Result]:
        # data size, is encrypted, is json, protocol
        head = self.socket.recv(8)
        if head == b'':
            return Result(False, False, 0, head)
        header = struct.unpack("I??H", head)
        if header is None:
            return None
        data = self.socket.recv(header[0])
        if data is None:
            return None
        encrypted = False
        if header[1]:
            if self._privkey is not None:
                data = rsa.decrypt(data, self._privkey)
            else:
                encrypted = True
        if len(data) == 0:
            data = None
        # is encrypted, is json, protocol, data
        return Result(encrypted, header[2], header[3], data)

    def disconnect(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
