import datetime
from abc import ABC

import pydantic


class BaseEvent(pydantic.BaseModel, ABC):
    start: "datetime.datetime"
    duration: "datetime.timedelta"

    def __post_init__(self):
        if self.start.tzinfo != datetime.timezone.utc:
            raise ValueError("Start time must be in UTC to ensure correct timezone conversion")


class BareEvent(BaseEvent):
    title: str


class URLEvent(BaseEvent):
    url: str
    url_title: str


class WindowTitleEvent(BaseEvent):
    app: str
    window_title: str


SourceEvent = BaseEvent | URLEvent | WindowTitleEvent | BareEvent
"""A source event, i.e. right after ingest."""
