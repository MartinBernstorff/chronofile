import datetime
from typing import TYPE_CHECKING, Sequence

from rescuetime2gcal.test_event import FakeDestinationEvent

if TYPE_CHECKING:
    from rescuetime2gcal.event import DestinationEvent

import os

from rescuetime2gcal.commands.sync_logic import main
from rescuetime2gcal.config import Config
from rescuetime2gcal.sources import gcal
from rescuetime2gcal.sources.source_event import BareEvent, SourceEvent

from .sync_logic import _pipeline


class FakeBareEvent(BareEvent):
    title: str = "fake title"
    start: datetime.datetime = datetime.datetime(
        2010, 1, 1, 0, 0, 0, 1, tzinfo=datetime.timezone.utc
    )
    duration: datetime.timedelta = datetime.timedelta(seconds=1)


def mock_input_client(input_events: Sequence[SourceEvent]) -> Sequence["SourceEvent"]:
    return input_events


def test_e2e():
    start_window = datetime.datetime(2010, 1, 1, 0, 0, 0, 1, tzinfo=datetime.timezone.utc)
    duration = datetime.timedelta(hours=1)
    end_window = start_window + 5 * duration

    def input_client() -> Sequence[SourceEvent]:
        return [
            FakeBareEvent(start=start_window, duration=duration),
            FakeBareEvent(start=start_window + duration * 2, duration=duration),
        ]

    destination_client = gcal.GcalClient(
        calendar_id=os.environ["GCAL_EMAIL"],
        client_id=os.environ["GCAL_CLIENT_ID"],
        client_secret=os.environ["GCAL_CLIENT_SECRET"],
        refresh_token=os.environ["GCAL_REFRESH_TOKEN"],
    )

    # Clear calendar in interval
    events = destination_client.get_events(start=start_window, end=end_window)
    for event in events:
        destination_client.delete_event(event)

    # First sync, to create new event
    cfg = Config.from_toml("config.toml")
    main(
        input_clients=[input_client], destination_client=destination_client, dry_run=False, cfg=cfg
    )

    # Check that event exists
    events = destination_client.get_events(start=start_window, end=end_window)
    assert len(events) == 2

    # Run again, should not create a duplicate
    main(
        input_clients=[input_client], destination_client=destination_client, dry_run=False, cfg=cfg
    )
    events = destination_client.get_events(start=start_window, end=end_window)
    assert len(events) == 2


def test_pipeline_should_remove_duplicates():
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
    assert changes == [sync.DeleteEvent(event=FakeDestinationEvent(id="1"))]
