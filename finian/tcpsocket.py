#!/usr/bin/env python3

import socket
import struct
from typing import Optional, Union, Dict, Any

# import rsa
# from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

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
        self._recp_pubkey: Optional[rsa.RSAPublicKey] = None
        self._privkey: Optional[rsa.RSAPrivateKey] = None

    def setserveropt(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    @property
    def recp_pubkey(self):
        if self._recp_pubkey is None:
            return None
        return self._recp_pubkey.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @recp_pubkey.setter
    def recp_pubkey(self, value):
        if isinstance(value, bytes):
            self._recp_pubkey = serialization.load_pem_public_key(
                value,
                backend=default_backend()
            )
        else:
            self._recp_pubkey = value

    @property
    def privkey(self):
        if self._privkey is None:
            return None
        return self._privkey.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    @privkey.setter
    def privkey(self, value):
        if isinstance(value, bytes):
            self._privkey = serialization.load_pem_private_key(
                value,
                password=None,
                backend=default_backend()
            )
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
            data = self._recp_pubkey.encrypt(
                data,
                padding=padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            # key = Fernet.generate_key()
            # f = Fernet(key)
            # token = f.encrypt(data)
            # key_token = rsa.encrypt(key, self._recp_pubkey)
            # data = struct.pack("H", len(key_token)) + key_token + token
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
                data = self._privkey.decrypt(
                    data,
                    padding=padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                # key_token_size = struct.unpack("H", data[0:2])[0]
                # key_token = data[2:2+key_token_size]
                # key = rsa.decrypt(key_token, self._privkey)
                # f = Fernet(key)
                # data = f.decrypt(data[2+key_token_size:])
            else:
                encrypted = True
        if len(data) == 0:
            data = None
        # is encrypted, is json, protocol, data
        return Result(encrypted, header[2], header[3], data)

    def disconnect(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
