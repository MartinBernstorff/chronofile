import datetime
from typing import TYPE_CHECKING, Sequence

from rescuetime2gcal.diff import DeleteEvent
from rescuetime2gcal.test_event import FakeDestinationEvent

if TYPE_CHECKING:
    from rescuetime2gcal.event import DestinationEvent


from rescuetime2gcal.sources.source_event import BareEvent, SourceEvent

from .sync import _pipeline  # type: ignore


class FakeBareEvent(BareEvent):
    title: str = "fake title"
    start: datetime.datetime = datetime.datetime(
        2010, 1, 1, 0, 0, 0, 1, tzinfo=datetime.timezone.utc
    )
    duration: datetime.timedelta = datetime.timedelta(seconds=1)


def mock_input_client(input_events: Sequence[SourceEvent]) -> Sequence["SourceEvent"]:
    return input_events


def test_should_remove_duplicates():
    def destination_client() -> Sequence["DestinationEvent"]:
        return [FakeDestinationEvent(id="0"), FakeDestinationEvent(id="1")]

    changes = _pipeline(
        source_events=[],
        destination_events=destination_client(),
        exclude_titles=[],
        metadata_enrichment=[],
        category2emoji={},
        min_duration=datetime.timedelta(days=1),
        merge_gap=datetime.timedelta(days=1),
        exclude_apps=[],
    )
    assert changes == [DeleteEvent(event=FakeDestinationEvent(id="1"))]
