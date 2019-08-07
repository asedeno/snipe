# Stubs for markdown.extensions.fenced_code (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from . import Extension
from ..preprocessors import Preprocessor
from .codehilite import CodeHilite, CodeHiliteExtension, parse_hl_lines
from typing import Any

class FencedCodeExtension(Extension):
    def extendMarkdown(self, md: Any, md_globals: Any) -> None: ...

class FencedBlockPreprocessor(Preprocessor):
    FENCED_BLOCK_RE: Any = ...
    CODE_WRAP: str = ...
    LANG_TAG: str = ...
    checked_for_codehilite: bool = ...
    codehilite_conf: Any = ...
    def __init__(self, md: Any) -> None: ...
    def run(self, lines: Any): ...

def makeExtension(*args: Any, **kwargs: Any): ...
