import datetime
from abc import ABC
from enum import Enum
from typing import TYPE_CHECKING

import pydantic

from rescuetime_to_gcal.generic_event import GenericEvent


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
