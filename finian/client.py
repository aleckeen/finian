#!/usr/bin/env python3

from .connection import Connection


class Client(Connection):
    def __init__(self, host: str, port: int):
        super().__init__()
        self.host: str = host
        self.port: int = port

    def connect(self) -> bool:
        try:
            self.socket.connect((self.host, self.port))
            return True
        except ConnectionError:
            return False
