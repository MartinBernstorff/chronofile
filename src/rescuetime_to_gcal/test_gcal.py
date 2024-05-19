import datetime
import os
import time

import pytest
import pytz

from rescuetime_to_gcal.event import Event
from rescuetime_to_gcal.gcal.client import DestinationClient, GcalClient


def _clean_test_interval(
    client: DestinationClient, start: datetime.datetime, end: datetime.datetime
):
    for event in client.get_events(start, end):
        client.delete_event(event)


@pytest.mark.parametrize(
    ("client", "system_timezone"),
    [
        (
            GcalClient(
                calendar_id=os.environ["TEST_CALENDAR_ID"],
                client_id=os.environ["GCAL_CLIENT_ID"],
                client_secret=os.environ["GCAL_CLIENT_SECRET"],
                refresh_token=os.environ["GCAL_REFRESH_TOKEN"],
            ),
            "Europe/Copenhagen",
        ),
        (
            GcalClient(
                calendar_id=os.environ["TEST_CALENDAR_ID"],
                client_id=os.environ["GCAL_CLIENT_ID"],
                client_secret=os.environ["GCAL_CLIENT_SECRET"],
                refresh_token=os.environ["GCAL_REFRESH_TOKEN"],
            ),
            "America/New_York",
        ),
    ],
)
def test_client_sync(
    client: DestinationClient,
    system_timezone: pytz.BaseTzInfo,
):
    # Update the system timezone
    os.environ["TZ"] = system_timezone  # type: ignore
    time.tzset()

    base_event = Event(
        title="🔥 Test",
        start=datetime.datetime(2023, 1, 1, 0, 0),
        end=datetime.datetime(2023, 1, 1, 0, 0),
    )

    _clean_test_interval(
        client, base_event.start, base_event.end + datetime.timedelta(days=1)
    )

    # Create an event
    add_response = client.add_event(base_event)
    # Get the event back
    loaded_event = client.get_events(
        base_event.start, base_event.end + datetime.timedelta(days=1)
    )[0]

    # Check identity is unchanged
    assert add_response.identity == loaded_event.identity

    # Update the event
    loaded_event.end = datetime.datetime(2023, 1, 1, 0, 1, tzinfo=pytz.UTC)
    payload = loaded_event
    response = client.update_event(loaded_event)
    assert response.identity == payload.identity

    # Delete the event
    delete_response = client.delete_event(payload)
    assert delete_response.identity == payload.identity
    assert (
        len(
            client.get_events(
                base_event.start, base_event.end + datetime.timedelta(days=1)
            )
        )
        == 0
    )


# TD Setup gcal tests
