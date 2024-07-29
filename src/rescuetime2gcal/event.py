import datetime
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping, Optional, Sequence

import pydantic
import pytz

from rescuetime2gcal.config import RecordCategory
from rescuetime2gcal.sources.source_event import (
    BareEvent,
    BaseSourceEvent,
    SourceEvent,
    URLEvent,
    WindowTitleEvent,
)

if TYPE_CHECKING:
    from rescuetime2gcal.config import RecordCategory, RecordMetadata


def event_identity(event: "DestinationEvent | ChronofileEvent") -> str:
    string_format = "%d/%m/%Y, %H:%M:%S"
    return f"{event.title} {event.start.strftime(string_format)} to {event.end.strftime(string_format)}"


class ChronofileEvent(pydantic.BaseModel):
    """Represents an event across the stack, when the information has been parsed for presentation."""

    title: str
    start: "datetime.datetime"
    end: "datetime.datetime"
    category: Optional["RecordCategory"] = None
    source_event: SourceEvent | None

    @pydantic.field_validator("title")
    def validate_title(cls, value: str) -> str:
        if len(value) < 1:
            raise ValueError("Title must be at least one character long")
        return value

    @pydantic.field_validator("start")
    def validate_start(cls, value: "datetime.datetime") -> "datetime.datetime":
        if not _is_utc(value):
            raise ValueError("Timezone must be UTC")
        return value

    @pydantic.field_validator("end")
    def validate_end(cls, value: "datetime.datetime") -> "datetime.datetime":
        if not _is_utc(value):
            raise ValueError("Timezone must be UTC")
        return value

    @property
    def timezone(self) -> str:
        return "UTC"

    @property
    def identity(self) -> str:
        return event_identity(self)

    @property
    def duration(self) -> "datetime.timedelta":
        return self.end - self.start

    def __repr__(self) -> str:
        return f"Event(title={self.title}, {self.start} to {self.end}, {self.timezone})"


class DestinationEvent(ChronofileEvent):
    """A ChronofileEvent with an ID matching a destination event. Enables updating the duration of the event."""

    id: str


def _parse_event(event: "SourceEvent") -> ChronofileEvent:
    match event:
        case URLEvent():
            return _parse_url_event(event)
        case WindowTitleEvent():
            title = event.window_title if len(event.window_title) != 0 else event.app
            return ChronofileEvent(
                title=title, start=event.start, end=event.start + event.duration, source_event=event
            )
        case BareEvent():
            return ChronofileEvent(
                title=event.title,
                start=event.start,
                end=event.start + event.duration,
                source_event=event,
            )
        case BaseSourceEvent():
            raise ValueError(f"Event type {type(event)} not supported")


def _is_utc(value: "datetime.datetime") -> bool:
    return value.tzinfo in (pytz.UTC, datetime.timezone.utc)


@dataclass(frozen=True)
class URLParseRule:
    apply_to: str
    extract_regex: str
    format_result: str


def _parse_url_event(event: "URLEvent") -> ChronofileEvent:
    parsers = [
        URLParseRule(
            apply_to=".*github.com.*",
            extract_regex=r".*github.com\/([^\/]*)\/([^\/]*)",
            format_result="GitHub: {0}/{1}",
        )
    ]

    for p in parsers:
        if re.match(p.apply_to, event.url):
            try:
                extraction = re.match(p.extract_regex, event.url)

                if not extraction:
                    continue

                title = p.format_result.format(*extraction.groups())
            except Exception:
                continue

            return ChronofileEvent(
                title=title, start=event.start, end=event.start + event.duration, source_event=event
            )

    title = event.url_title if len(event.url_title) != 0 else event.url

    if title == "":
        title = "No title"

    return ChronofileEvent(
        title=title, start=event.start, end=event.start + event.duration, source_event=event
    )


def _event_matches_metadata(generic_event: ChronofileEvent, meta: "RecordMetadata") -> bool:
    return any(title.lower() in generic_event.title.lower() for title in meta.title_matcher)


def _add_category(generic_event: ChronofileEvent, meta: "RecordMetadata"):
    generic_event.category = meta.category


def _override_title(generic_event: ChronofileEvent, meta: "RecordMetadata"):
    if meta.override_title is not None:
        generic_event.title = meta.override_title


def _add_emoji(
    category2emoji: Mapping["RecordCategory", str],
    generic_event: ChronofileEvent,
    meta: "RecordMetadata",
):
    if category2emoji[meta.category] not in generic_event.title:
        generic_event.title = f"{category2emoji[meta.category]} {generic_event.title}"


def hydrate_event(
    event: "SourceEvent",
    metadata: Sequence["RecordMetadata"],
    category2emoji: Mapping["RecordCategory", str],
) -> ChronofileEvent:
    generic_event = _parse_event(event)

    # Apply category and emoji
    for meta in metadata:
        if _event_matches_metadata(generic_event, meta):
            _add_category(generic_event, meta)
            _override_title(generic_event, meta)
            _add_emoji(category2emoji, generic_event, meta)

    return generic_event
