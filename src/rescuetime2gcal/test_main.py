from typing import TYPE_CHECKING, Sequence

from rescuetime2gcal import delta
from rescuetime2gcal.__main__ import pipeline
from rescuetime2gcal.test_preprocessing import FakeDestinationEvent

if TYPE_CHECKING:
    from rescuetime2gcal.preprocessing import DestinationEvent


def test_pipeline_should_remove_duplicates():
    def destination_client() -> Sequence["DestinationEvent"]:
        return [FakeDestinationEvent(id="0"), FakeDestinationEvent(id="1")]

    changes = pipeline(source_events=[], destination_events=destination_client())
    assert changes == [delta.DeleteEvent(event=FakeDestinationEvent(id="1"))]
