import datetime
import os
from typing import Sequence

from rescuetime2gcal.__main__ import main
from rescuetime2gcal.clients import gcal
from rescuetime2gcal.source_event import BareEvent, SourceEvent


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
    main(input_clients=[input_client], destination_client=destination_client, dry_run=False)

    # Check that event exists
    events = destination_client.get_events(start=start_window, end=end_window)
    assert len(events) == 2

    # Run again, should not create a duplicate
    main(input_clients=[input_client], destination_client=destination_client, dry_run=False)
    events = destination_client.get_events(start=start_window, end=end_window)
    assert len(events) == 2
