#!/usr/bin/env python3

import threading
from typing import Callable

from .connection import Connection

NewConnectionCallbackType = Callable[[Connection], None]


class Server(Connection):
    def __init__(self, host: str, port: int):
        super().__init__()
        self.host: str = host
        self.port: int = port
        self.socket.setserveropt()
        self.socket.bind((self.host, self.port))
        self._new_connection_callback: NewConnectionCallbackType = lambda c: None

    def _setup_connection(self, connection: Connection):
        connection.pubkey = self.pubkey
        connection.privkey = self.privkey
        connection._recv_callbacks = self._recv_callbacks
        connection._recv_no_protocol_callback = self._recv_no_protocol_callback
        self._new_connection_callback(connection)
        connection.listen()

    def new_connection(self, callback: NewConnectionCallbackType):
        self._new_connection_callback = callback

    def listen(self):
        self.socket.listen()
        while True:
            connection = self.socket.accept()
            connection = Connection(connection)
            thread = threading.Thread(target=self._setup_connection, args=(connection,))
            thread.daemon = True
            thread.run()
