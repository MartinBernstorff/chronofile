from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from rescuetime_to_gcal.generic_event import GenericEvent


def _event_hasher(event: "GenericEvent") -> str:
    return f"{event.title.lower().strip()}: {event.start} to {event.end}"


def deduper(
    source_events: Sequence["GenericEvent"], destination_events: Sequence["GenericEvent"]
) -> Sequence["GenericEvent"]:
    origin_hashes = {_event_hasher(e) for e in destination_events}
    return [e for e in source_events if _event_hasher(e) not in origin_hashes]
