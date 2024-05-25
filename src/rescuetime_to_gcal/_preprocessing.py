from typing import TYPE_CHECKING, Mapping, Sequence

from rescuetime_to_gcal.generic_event import Event

if TYPE_CHECKING:
    import datetime

    from rescuetime_to_gcal.config import RecordCategory, RecordMetadata


def apply_metadata(
    event: Event,
    metadata: Sequence["RecordMetadata"],
    category2emoji: Mapping["RecordCategory", str],
) -> Event:
    for meta in metadata:
        if any(title.lower() in event.title.lower() for title in meta.title_matcher):
            event.category = meta.category
            if meta.prettified_title is not None:
                event.title = meta.prettified_title
            event.title = f"{category2emoji[meta.category]} {event.title}"

    return event


def filter_by_title(data: Sequence[Event], strs_to_match: Sequence[str]) -> Sequence[Event]:
    return [
        event for event in data if not any(title.lower() in event.title for title in strs_to_match)
    ]


def _new_event(event: Event, end_time: "datetime.datetime") -> Event:
    return Event(title=event.title, start=event.start, end=end_time)


def merge_within_window(
    events: Sequence[Event], merge_gap: "datetime.timedelta"
) -> Sequence[Event]:
    """Combine rows if end time is within merge_gap of the next event within groups by the group_by function."""
    if len(events) < 2:
        return events

    processed_events: list[Event] = []
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
