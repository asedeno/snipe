# Stubs for markdown.util (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any, Optional

string_type = str
text_type = str
int2str = chr
BLOCK_LEVEL_ELEMENTS: Any
STX: str
ETX: str
INLINE_PLACEHOLDER_PREFIX: Any
INLINE_PLACEHOLDER: Any
INLINE_PLACEHOLDER_RE: Any
AMP_SUBSTITUTE: Any
HTML_PLACEHOLDER: Any
HTML_PLACEHOLDER_RE: Any
TAG_PLACEHOLDER: Any
RTL_BIDI_RANGES: Any

def isBlockLevel(tag: Any): ...
def parseBoolValue(value: Any, fail_on_errors: bool = ..., preserve_none: bool = ...): ...

class AtomicString(text_type): ...

class Processor:
    markdown: Any = ...
    def __init__(self, markdown_instance: Optional[Any] = ...) -> None: ...

class HtmlStash:
    html_counter: int = ...
    rawHtmlBlocks: Any = ...
    tag_counter: int = ...
    tag_data: Any = ...
    def __init__(self) -> None: ...
    def store(self, html: Any, safe: bool = ...): ...
    def reset(self) -> None: ...
    def get_placeholder(self, key: Any): ...
    def store_tag(self, tag: Any, attrs: Any, left_index: Any, right_index: Any): ...
