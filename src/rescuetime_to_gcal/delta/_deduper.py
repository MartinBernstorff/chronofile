from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from rescuetime_to_gcal.generic_event import Event


def _event_hasher(event: "Event") -> str:
    return f"{event.title.lower().strip()}: {event.start} to {event.end}"


def deduper(
    source_events: Sequence["Event"], destination_events: Sequence["Event"]
) -> Sequence["Event"]:
    origin_hashes = {_event_hasher(e) for e in destination_events}
    return [e for e in source_events if _event_hasher(e) not in origin_hashes]
