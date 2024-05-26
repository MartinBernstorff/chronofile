import copy
import logging

from abc import ABC
from dataclasses import dataclass
from typing import Sequence

import devtools

from rescuetime_to_gcal.delta._deduper import deduper
from rescuetime_to_gcal.generic_event import GenericEvent

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewEvent:
    event: GenericEvent


@dataclass(frozen=True)
class UpdateEvent:
    event: GenericEvent


EventChange = NewEvent | UpdateEvent


def changeset(
    true_events: Sequence[GenericEvent], mirror_events: Sequence[GenericEvent]
) -> Sequence[EventChange]:
    """Identify which changes are needed on the mirror for it to match truth."""
    timezones = set(e.timezone for e in [*true_events, *mirror_events])
    if len(timezones) != 1:
        raise ValueError(f"All events must be in the same timezone. Found {timezones}")

    deduped_events = deduper(mirror_events=mirror_events, true_events=true_events)

    changeset: list[EventChange] = []
    for new_event in deduped_events:
        ancestor = [
            event
            for event in mirror_events
            if event.title == new_event.title and event.start == new_event.start
        ]

        if len(ancestor) > 1:
            log.warning(
                f"Found multiple events with the same title and start time: {ancestor}. Updating both events."
            )

        sorted_ancestors = sorted(ancestor, key=lambda e: e.start)
        event_is_update = len(ancestor) != 0
        if event_is_update:
            existing_event = sorted_ancestors[-1]
            updated_existing_event = copy.deepcopy(existing_event)
            updated_existing_event.end = new_event.end
            changeset.append(UpdateEvent(event=updated_existing_event))
        else:
            changeset.append(NewEvent(event=new_event))

    sorted_changeset = sorted(changeset, key=lambda c: c.event.start)
    logging.info(f"Changeset: {devtools.debug.format(sorted_changeset)}")

    return changeset
