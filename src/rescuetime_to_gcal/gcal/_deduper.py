from typing import Sequence

from gcsa.event import Event as GCSAEvent


def _event_hasher(event: GCSAEvent) -> str:
    return f"{event.summary.lower().strip()}: {event.start} to {event.end}"


def _deduper(
    source_events: Sequence[GCSAEvent],
    destination_events: Sequence[GCSAEvent],
) -> Sequence[GCSAEvent]:
    origin_hashes = {_event_hasher(e) for e in destination_events}
    return [e for e in source_events if _event_hasher(e) not in origin_hashes]
