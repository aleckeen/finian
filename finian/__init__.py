#!/usr/bin/env python3

from finian.client import Client
from finian.connection import Connection
from finian.globals import current_conn
from finian.server import Server
from finian.tcpsocket import Result

current_conn: Connection
