from abc import ABC
from dataclasses import dataclass
from typing import Sequence

from rescuetime_to_gcal.delta._deduper import deduper
from rescuetime_to_gcal.event import Event


class EventChange(ABC):
    event: Event


@dataclass(frozen=True)
class NewEvent(EventChange):
    event: Event


@dataclass(frozen=True)
class UpdateEvent(EventChange):
    event: Event


def changeset(
    source_events: Sequence[Event],
    destination_events: Sequence[Event],
) -> Sequence[EventChange]:
    deduped_events = deduper(
        destination_events=destination_events,
        source_events=source_events,
    )

    changeset: list[EventChange] = []

    for new_event in deduped_events:
        existing_events = [
            event
            for event in destination_events
            if event.title == new_event.title and event.start == new_event.start
        ]

        event_is_update = len(existing_events) != 0
        if event_is_update:
            existing_event = existing_events[0]
            existing_event.end = new_event.end
            changeset.append(UpdateEvent(event=existing_event))
        else:
            changeset.append(NewEvent(event=new_event))

    return changeset
