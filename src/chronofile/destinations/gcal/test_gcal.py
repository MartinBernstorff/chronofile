import datetime
import os
import time
from typing import TYPE_CHECKING

import pytest
import pytz

from chronofile.destinations.gcal.client import DestinationClient, GcalClient
from chronofile.test_event import FakeParsedEvent

if TYPE_CHECKING:
    from chronofile.event import ChronofileEvent


@pytest.fixture(autouse=True)
def _skip_if_no_gcal_credentials():  # type: ignore
    if any(
        os.environ.get(key) is None
        for key in [
            "GCAL_CLIENT_ID",
            "GCAL_CLIENT_SECRET",
            "GCAL_REFRESH_TOKEN",
            "TEST_CALENDAR_ID",
        ]
    ):
        pytest.skip("No Google Calendar credentials found")


def _clean_test_interval(
    client: "DestinationClient", start: datetime.datetime, end: datetime.datetime
):
    for event in client.get_events(start, end):
        client.delete_event(event)


@pytest.mark.parametrize(("system_timezone"), ["Europe/Copenhagen", "America/New_York"])
@pytest.mark.parametrize(
    ("base_event"),
    [
        FakeParsedEvent(
            title="🔥 Test",
            start=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
            end=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
        )
    ],
)
def test_client_sync(system_timezone: pytz.BaseTzInfo, base_event: "ChronofileEvent"):
    client = GcalClient(
        calendar_id=os.environ["TEST_CALENDAR_ID"],
        client_id=os.environ["GCAL_CLIENT_ID"],
        client_secret=os.environ["GCAL_CLIENT_SECRET"],
        refresh_token=os.environ["GCAL_REFRESH_TOKEN"],
    )

    # Update the system timezone
    os.environ["TZ"] = system_timezone  # type: ignore
    time.tzset()

    _clean_test_interval(client, base_event.start, base_event.end + datetime.timedelta(days=1))

    # Create an event
    add_response = client.add_event(base_event)
    # Get the event back
    loaded_event = client.get_events(base_event.start, base_event.end + datetime.timedelta(days=1))[
        0
    ]

    # Check identity is unchanged
    assert add_response.identity == loaded_event.identity

    # Update the event
    loaded_event.end = datetime.datetime(2023, 1, 1, 0, 1, tzinfo=pytz.UTC)
    payload = loaded_event
    response = client.update_event(loaded_event)
    assert response.identity == payload.identity

    # Delete the event
    client.delete_event(payload)
    assert (
        len(client.get_events(base_event.start, base_event.end + datetime.timedelta(days=1))) == 0
    )
