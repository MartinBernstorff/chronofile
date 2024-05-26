from typing import TYPE_CHECKING, Protocol, Sequence

if TYPE_CHECKING:
    from rescuetime2gcal.source_event import SourceEvent


class EventSource(Protocol):
    def __call__(self) -> Sequence["SourceEvent"]:
        ...
