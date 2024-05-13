import datetime
from typing import Callable, Mapping, Sequence

from iterpy.arr import Arr

from rescuetime_to_gcal.config import RecordCategory, RecordMetadata
from rescuetime_to_gcal.event import Event


def apply_metadata(
    event: Event,
    metadata: Sequence[RecordMetadata],
    category2emoji: Mapping[RecordCategory, str],
) -> Event:
    for record in metadata:
        if any(
            [title.lower() in event.title.lower() for title in record.title_matcher]
        ):
            event.category = record.category
            if record.prettified_title is not None:
                event.title = record.prettified_title
            event.title = f"{category2emoji[record.category]} {event.title}"

    return event


def filter_by_title(
    data: Sequence[Event],
    strs_to_match: Sequence[str],
) -> Sequence[Event]:
    return [
        event
        for event in data
        if not any([title.lower() in event.title for title in strs_to_match])
    ]


def merge_within_window(
    events: Sequence[Event],
    group_by: Callable[[Event], str],
    merge_gap: datetime.timedelta,
) -> Sequence[Event]:
    """Combine rows if end time is within merge_gap of the next event within groups by the group_by function."""
    groups = Arr(events).groupby(group_by)

    processed_events = []
    for _, group_events in groups:
        sorted_events = sorted(group_events, key=lambda e: e.start)

        i = 1  # Skip the first event
        while i < len(sorted_events) - 1:
            cur = sorted_events[i]
            prev = sorted_events[i - 1]

            overlapping = cur.start <= prev.end + merge_gap
            if overlapping and prev.end < cur.end:
                prev.end = cur.end
                sorted_events.pop(i)
            else:
                i += 1

        processed_events.append(sorted_events)

    return Arr(processed_events).flatten().to_list()
