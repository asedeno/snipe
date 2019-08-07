# Stubs for wsproto.handshake (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from .connection import Connection, ConnectionState, ConnectionType
from .events import AcceptConnection, RejectConnection, RejectData, Request
from .utilities import LocalProtocolError, RemoteProtocolError, generate_accept_token, generate_nonce, normed_header_dict, split_comma_header
from typing import Any, Optional

WEBSOCKET_VERSION: bytes

class H11Handshake:
    client: Any = ...
    def __init__(self, connection_type: ConnectionType) -> None: ...
    @property
    def state(self): ...
    @property
    def connection(self): ...
    def initiate_upgrade_connection(self, headers: List[Tuple[bytes, bytes]], path: str) -> None: ...
    def send(self, event: Any): ...
    def receive_data(self, data: bytes) -> None: ...
    def events(self) -> None: ...

def server_extensions_handshake(requested: List[str], supported: List[Extension]) -> Optional[bytes]: ...
def client_extensions_handshake(accepted: List[str], supported: List[Extension]) -> List[Extension]: ...
