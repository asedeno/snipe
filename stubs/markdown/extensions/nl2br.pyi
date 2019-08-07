# Stubs for markdown.extensions.nl2br (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from . import Extension
from ..inlinepatterns import SubstituteTagPattern
from typing import Any

BR_RE: str

class Nl2BrExtension(Extension):
    def extendMarkdown(self, md: Any, md_globals: Any) -> None: ...

def makeExtension(*args: Any, **kwargs: Any): ...
