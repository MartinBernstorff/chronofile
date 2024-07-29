from typing import TYPE_CHECKING, Sequence

from rescuetime2gcal.event import ChronofileEvent

if TYPE_CHECKING:
    import datetime


def _update_end_time(event: ChronofileEvent, end_time: "datetime.datetime") -> ChronofileEvent:
    return ChronofileEvent(
        title=event.title, start=event.start, end=end_time, source_event=event.source_event
    )


def merge_within_window(
    events: Sequence["ChronofileEvent"], merge_gap: "datetime.timedelta"
) -> Sequence["ChronofileEvent"]:
    """Combine events in the same timeline if their end time is within merge_gap of the next event."""
    if len(events) < 2:
        return events

    processed_events: list[ChronofileEvent] = []
    sorted_events = sorted(events, key=lambda e: e.start)

    cur_event = sorted_events[0]
    cur_end_time = cur_event.end
    for candidate in sorted_events[1:]:
        overlapping = cur_end_time + merge_gap >= candidate.start
        if overlapping:
            cur_end_time = candidate.end

        # Cases where events should be appended
        if not overlapping:
            processed_events.append(_update_end_time(cur_event, cur_end_time))
            cur_event = candidate
            cur_end_time = candidate.end

        if candidate == sorted_events[-1]:
            if overlapping:
                processed_events.append(_update_end_time(cur_event, cur_end_time))
            else:
                processed_events.append(candidate)

    return processed_events
