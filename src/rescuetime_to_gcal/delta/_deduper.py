from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from rescuetime_to_gcal.preprocessing import DestinationEvent, ParsedEvent


def _event_hasher(event: "DestinationEvent | ParsedEvent") -> str:
    return f"{event.title.lower().strip()}: {event.start} to {event.end}"


def deduper(
    parsed_events: Sequence["ParsedEvent"], destination_events: Sequence["DestinationEvent"]
) -> Sequence["ParsedEvent"]:
    origin_hashes = {_event_hasher(e) for e in destination_events}
    return [e for e in parsed_events if _event_hasher(e) not in origin_hashes]
