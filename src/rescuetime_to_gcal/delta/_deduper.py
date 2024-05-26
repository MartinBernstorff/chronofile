from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from rescuetime_to_gcal.preprocessing import ParsedEvent


def _event_hasher(event: "ParsedEvent") -> str:
    return f"{event.title.lower().strip()}: {event.start} to {event.end}"


def deduper(
    true_events: Sequence["ParsedEvent"], mirror_events: Sequence["ParsedEvent"]
) -> Sequence["ParsedEvent"]:
    origin_hashes = {_event_hasher(e) for e in mirror_events}
    return [e for e in true_events if _event_hasher(e) not in origin_hashes]
