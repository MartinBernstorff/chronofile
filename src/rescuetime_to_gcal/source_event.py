import datetime  # noqa: TCH003
from enum import Enum
from typing import TYPE_CHECKING

import pydantic

from rescuetime_to_gcal.generic_event import Event


class BareEvent(pydantic.BaseModel):
    start: "datetime.datetime"
    duration: "datetime.timedelta"


class AFKState(Enum):
    AFK = "afk"
    NOT_AFK = "not-afk"


class AFKEvent(BareEvent):
    state: AFKState


class URLEvent(BareEvent):
    url: str
    url_title: str


class WindowTitleEvent(BareEvent):
    app: str
    window_title: str


SourceEvent = BareEvent | URLEvent | WindowTitleEvent | AFKEvent
