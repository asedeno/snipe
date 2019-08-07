# Stubs for parsedatetime.context (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any

class pdtContextStack:
    def __init__(self) -> None: ...
    def push(self, ctx: Any) -> None: ...
    def pop(self): ...
    def last(self): ...
    def isEmpty(self): ...

class pdtContext:
    ACU_YEAR: Any = ...
    ACU_MONTH: Any = ...
    ACU_WEEK: Any = ...
    ACU_DAY: Any = ...
    ACU_HALFDAY: Any = ...
    ACU_HOUR: Any = ...
    ACU_MIN: Any = ...
    ACU_SEC: Any = ...
    ACU_NOW: Any = ...
    ACU_DATE: Any = ...
    ACU_TIME: Any = ...
    accuracy: Any = ...
    def __init__(self, accuracy: int = ...) -> None: ...
    def updateAccuracy(self, *accuracy: Any) -> None: ...
    def update(self, context: Any) -> None: ...
    @property
    def hasDate(self): ...
    @property
    def hasTime(self): ...
    @property
    def dateTimeFlag(self): ...
    @property
    def hasDateOrTime(self): ...
    def __eq__(self, ctx: Any): ...
