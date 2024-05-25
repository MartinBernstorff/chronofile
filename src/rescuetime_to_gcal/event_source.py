from typing import TYPE_CHECKING, Protocol, Sequence

if TYPE_CHECKING:
    from rescuetime_to_gcal.generic_event import Event


class EventSource(Protocol):
    def __call__(self) -> Sequence["Event"]:
        ...
