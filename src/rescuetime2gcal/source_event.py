import datetime
from abc import ABC
from typing import TYPE_CHECKING

import pydantic

if TYPE_CHECKING:
    from rescuetime2gcal.preprocessing import DestinationEvent, ParsedEvent


class BaseEvent(pydantic.BaseModel, ABC):
    start: "datetime.datetime"
    duration: "datetime.timedelta"

    def __post_init__(self):
        if self.start.tzinfo != datetime.timezone.utc:
            raise ValueError(
                "Start time must be in UTC to ensure correct timezone conversion"
            )


class BareEvent(BaseEvent):
    title: str

    @pydantic.field_validator("title")
    def validate_title(cls, value: str) -> str:
        if len(value) < 1:
            raise ValueError("Title must contain content")
        return value


class URLEvent(BaseEvent):
    url: str
    url_title: str


class WindowTitleEvent(BaseEvent):
    app: str
    window_title: str


SourceEvent = BaseEvent | URLEvent | WindowTitleEvent | BareEvent
"""A source event, i.e. right after ingest."""


def event_identity(event: "DestinationEvent | ParsedEvent") -> str:
    string_format = "%d/%m/%Y, %H:%M:%S"
    return f"{event.title} {event.start.strftime(string_format)} to {event.end.strftime(string_format)}"
