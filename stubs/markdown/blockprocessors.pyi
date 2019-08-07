# Stubs for markdown.blockprocessors (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from .blockparser import BlockParser
from typing import Any

logger: Any

def build_block_parser(md_instance: Any, **kwargs: Any): ...

class BlockProcessor:
    parser: Any = ...
    tab_length: Any = ...
    def __init__(self, parser: Any) -> None: ...
    def lastChild(self, parent: Any): ...
    def detab(self, text: Any): ...
    def looseDetab(self, text: Any, level: int = ...): ...
    def test(self, parent: Any, block: Any) -> None: ...
    def run(self, parent: Any, blocks: Any) -> None: ...

class ListIndentProcessor(BlockProcessor):
    ITEM_TYPES: Any = ...
    LIST_TYPES: Any = ...
    INDENT_RE: Any = ...
    def __init__(self, *args: Any) -> None: ...
    def test(self, parent: Any, block: Any): ...
    def run(self, parent: Any, blocks: Any) -> None: ...
    def create_item(self, parent: Any, block: Any) -> None: ...
    def get_level(self, parent: Any, block: Any): ...

class CodeBlockProcessor(BlockProcessor):
    def test(self, parent: Any, block: Any): ...
    def run(self, parent: Any, blocks: Any) -> None: ...

class BlockQuoteProcessor(BlockProcessor):
    RE: Any = ...
    def test(self, parent: Any, block: Any): ...
    def run(self, parent: Any, blocks: Any) -> None: ...
    def clean(self, line: Any): ...

class OListProcessor(BlockProcessor):
    TAG: str = ...
    STARTSWITH: str = ...
    SIBLING_TAGS: Any = ...
    RE: Any = ...
    CHILD_RE: Any = ...
    INDENT_RE: Any = ...
    def __init__(self, parser: Any) -> None: ...
    def test(self, parent: Any, block: Any): ...
    def run(self, parent: Any, blocks: Any) -> None: ...
    def get_items(self, block: Any): ...

class UListProcessor(OListProcessor):
    TAG: str = ...
    RE: Any = ...
    def __init__(self, parser: Any) -> None: ...

class HashHeaderProcessor(BlockProcessor):
    RE: Any = ...
    def test(self, parent: Any, block: Any): ...
    def run(self, parent: Any, blocks: Any) -> None: ...

class SetextHeaderProcessor(BlockProcessor):
    RE: Any = ...
    def test(self, parent: Any, block: Any): ...
    def run(self, parent: Any, blocks: Any) -> None: ...

class HRProcessor(BlockProcessor):
    RE: str = ...
    SEARCH_RE: Any = ...
    match: Any = ...
    def test(self, parent: Any, block: Any): ...
    def run(self, parent: Any, blocks: Any) -> None: ...

class EmptyBlockProcessor(BlockProcessor):
    def test(self, parent: Any, block: Any): ...
    def run(self, parent: Any, blocks: Any) -> None: ...

class ParagraphProcessor(BlockProcessor):
    def test(self, parent: Any, block: Any): ...
    def run(self, parent: Any, blocks: Any) -> None: ...
