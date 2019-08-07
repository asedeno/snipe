# Stubs for h11.tests.test_against_stdlib_http (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

import SocketServer as socketserver
from SimpleHTTPServer import SimpleHTTPRequestHandler
from typing import Any

def socket_server(handler: Any) -> None: ...

test_file_path: Any
test_file_data: Any

class SingleMindedRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: Any): ...

def test_h11_as_client() -> None: ...

class H11RequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None: ...

def test_h11_as_server() -> None: ...
