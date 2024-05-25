from typing import TYPE_CHECKING, Mapping, Sequence

from rescuetime_to_gcal.generic_event import GenericEvent
from rescuetime_to_gcal.source_event import BareEvent, BaseEvent, URLEvent, WindowTitleEvent

if TYPE_CHECKING:
    import datetime

    from rescuetime_to_gcal.config import RecordCategory, RecordMetadata
    from rescuetime_to_gcal.source_event import SourceEvent


def apply_metadata(
    event: "SourceEvent",
    metadata: Sequence["RecordMetadata"],
    category2emoji: Mapping["RecordCategory", str],
) -> GenericEvent:
    generic_event = _parse_event(event)

    # Apply category and emoji
    for meta in metadata:
        if any(title.lower() in generic_event.title.lower() for title in meta.title_matcher):
            generic_event.category = meta.category
            if meta.prettified_title is not None:
                generic_event.title = meta.prettified_title
            generic_event.title = f"{category2emoji[meta.category]} {generic_event.title}"

    return generic_event


def _parse_event(event: "SourceEvent") -> GenericEvent:
    match event:
        case URLEvent():
            return parse_url_event(event)
        case WindowTitleEvent():
            return parse_window_title_event(event)
        case BareEvent():
            return GenericEvent(
                title=event.title, start=event.start, end=event.start + event.duration
            )
        case BaseEvent():
            raise ValueError(f"Event type {type(event)} not supported")


def parse_window_title_event(event: WindowTitleEvent) -> GenericEvent:
    return GenericEvent(
        title=event.window_title, start=event.start, end=event.start + event.duration
    )


def parse_url_event(event: URLEvent) -> GenericEvent:
    return GenericEvent(
        title=f"Github · {event.url_title}", start=event.start, end=event.start + event.duration
    )


def filter_by_title(
    data: Sequence[GenericEvent], strs_to_match: Sequence[str]
) -> Sequence[GenericEvent]:
    return [
        event for event in data if not any(title.lower() in event.title for title in strs_to_match)
    ]


def _new_event(event: GenericEvent, end_time: "datetime.datetime") -> GenericEvent:
    return GenericEvent(title=event.title, start=event.start, end=end_time)


def merge_within_window(
    events: Sequence[GenericEvent], merge_gap: "datetime.timedelta"
) -> Sequence[GenericEvent]:
    """Combine rows if end time is within merge_gap of the next event within groups by the group_by function."""
    if len(events) < 2:
        return events

    processed_events: list[GenericEvent] = []
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
