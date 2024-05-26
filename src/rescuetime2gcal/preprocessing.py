import datetime  # noqa: TCH003
from typing import TYPE_CHECKING, Mapping, Optional, Sequence

import pydantic

from rescuetime2gcal.config import RecordCategory
from rescuetime2gcal.source_event import (
    BareEvent,
    BaseEvent,
    SourceEvent,
    URLEvent,
    WindowTitleEvent,
    event_identity,
)

if TYPE_CHECKING:
    from rescuetime2gcal.config import RecordCategory, RecordMetadata


class ParsedEvent(pydantic.BaseModel):
    """Represents an event across the stack, when the information has been parsed for presentation."""

    title: str
    start: "datetime.datetime"
    end: "datetime.datetime"
    category: Optional["RecordCategory"] = None
    timezone: str = "UTC"

    @pydantic.field_validator("title")
    def validate_title(cls, value: str) -> str:
        if len(value) < 1:
            raise ValueError("Title must be at least one character long")
        return value

    @property
    def identity(self) -> str:
        return event_identity(self)

    @property
    def duration(self) -> "datetime.timedelta":
        return self.end - self.start

    def __repr__(self) -> str:
        return f"Event(title={self.title}, {self.start} to {self.end}, {self.timezone})"


class DestinationEvent(ParsedEvent):
    id: str


def _parse_event(event: "SourceEvent") -> ParsedEvent:
    match event:
        case URLEvent():
            title = event.url_title if len(event.url_title) != 0 else event.url
            if title == "":
                title = "No title"
            return ParsedEvent(title=title, start=event.start, end=event.start + event.duration)
        case WindowTitleEvent():
            title = event.window_title if len(event.window_title) != 0 else event.app
            return ParsedEvent(title=title, start=event.start, end=event.start + event.duration)
        case BareEvent():
            return ParsedEvent(
                title=event.title, start=event.start, end=event.start + event.duration
            )
        case BaseEvent():
            raise ValueError(f"Event type {type(event)} not supported")


def filter_by_title(
    data: Sequence[ParsedEvent], strs_to_match: Sequence[str]
) -> Sequence[ParsedEvent]:
    return [
        event for event in data if not any(title.lower() in event.title for title in strs_to_match)
    ]


def _new_event(event: ParsedEvent, end_time: "datetime.datetime") -> ParsedEvent:
    return ParsedEvent(title=event.title, start=event.start, end=end_time)


def merge_within_window(
    events: Sequence[ParsedEvent], merge_gap: "datetime.timedelta"
) -> Sequence[ParsedEvent]:
    """Combine rows if end time is within merge_gap of the next event within groups by the group_by function."""
    if len(events) < 2:
        return events

    processed_events: list[ParsedEvent] = []
    sorted_events = sorted(events, key=lambda e: e.start)

    cur_event = sorted_events[0]
    cur_end_time = cur_event.end
    for candidate in sorted_events[1:]:
        overlapping = cur_end_time + merge_gap >= candidate.start
        if overlapping:
            cur_end_time = candidate.end

        # Cases where events should be appended
        if not overlapping:
            processed_events.append(_new_event(cur_event, cur_end_time))
            cur_event = candidate
            cur_end_time = candidate.end

        if candidate == sorted_events[-1]:
            if overlapping:
                processed_events.append(_new_event(cur_event, cur_end_time))
            else:
                processed_events.append(candidate)

    return processed_events


def parse_events(
    event: "SourceEvent",
    metadata: Sequence["RecordMetadata"],
    category2emoji: Mapping["RecordCategory", str],
) -> ParsedEvent:
    generic_event = _parse_event(event)

    # Apply category and emoji
    for meta in metadata:
        if any(title.lower() in generic_event.title.lower() for title in meta.title_matcher):
            generic_event.category = meta.category
            if meta.prettified_title is not None:
                generic_event.title = meta.prettified_title
            generic_event.title = f"{category2emoji[meta.category]} {generic_event.title}"

    return generic_event
