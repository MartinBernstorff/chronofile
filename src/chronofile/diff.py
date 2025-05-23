import copy
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

import devtools

from chronofile.event import event_identity

if TYPE_CHECKING:
    from chronofile.event import ChronofileEvent, DestinationEvent

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewEvent:
    event: "ChronofileEvent"


@dataclass(frozen=True)
class UpdateEvent:
    event: "DestinationEvent"


@dataclass(frozen=True)
class DeleteEvent:
    event: "DestinationEvent"


EventChange = NewEvent | UpdateEvent | DeleteEvent


def _deduper(
    parsed_events: Sequence["ChronofileEvent"], destination_events: Sequence["ChronofileEvent"]
) -> Sequence["ChronofileEvent"]:
    origin_hashes = {event_identity(e) for e in destination_events}
    return [e for e in parsed_events if event_identity(e) not in origin_hashes]


def _ancestry_identity(event: "ChronofileEvent | ChronofileEvent") -> str:
    string_format = "%d/%m/%Y, %H:%M:%S"
    return f"{event.title} {event.start.strftime(string_format)}"


def diff(
    parsed_events: Sequence["ChronofileEvent"], destination_events: Sequence["DestinationEvent"]
) -> Sequence[EventChange]:
    """Identify which changes are needed on the mirror for it to match truth."""
    if len(destination_events) == 0:
        return [NewEvent(event=e) for e in parsed_events]

    timezones = {e.timezone for e in [*parsed_events, *destination_events]}
    if len(timezones) != 1:
        raise ValueError(f"All events must be in the same timezone. Found {timezones}")

    deduped_events = _deduper(destination_events=destination_events, parsed_events=parsed_events)

    changeset: list[EventChange] = []
    for new_event in deduped_events:
        ancestor = [
            event
            for event in destination_events
            if _ancestry_identity(event) == _ancestry_identity(new_event)
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
