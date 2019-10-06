# Stubs for markdown.extensions (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from ..util import parseBoolValue
from typing import Any

class Extension:
    config: Any = ...
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def getConfig(self, key: Any, default: str = ...): ...
    def getConfigs(self): ...
    def getConfigInfo(self): ...
    def setConfig(self, key: Any, value: Any) -> None: ...
    def setConfigs(self, items: Any) -> None: ...
    def extendMarkdown(self, md: Any, md_globals: Any) -> None: ...