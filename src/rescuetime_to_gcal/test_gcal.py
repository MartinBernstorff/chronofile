import datetime
import os

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
    ("client"),
    [
        GcalClient(
            calendar_id=os.environ["TEST_CALENDAR_ID"],
            client_id=os.environ["GCAL_CLIENT_ID"],
            client_secret=os.environ["GCAL_CLIENT_SECRET"],
            refresh_token=os.environ["GCAL_REFRESH_TOKEN"],
        )
    ],
)
def test_client_sync(client: DestinationClient):
    base_event = Event(
        title="test",
        start=datetime.datetime(2023, 1, 1, 0, 0),
        end=datetime.datetime(2023, 1, 1, 0, 0),
    )

    _clean_test_interval(
        client, base_event.start, base_event.end + datetime.timedelta(days=1)
    )

    # Create an event
    add_response = client.add_event(
        Event(
            title="test",
            start=datetime.datetime(2023, 1, 1, 0, 0),
            end=datetime.datetime(2023, 1, 1, 0, 0),
        )
    )
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


# TD Add tests for round-trip sync
# * Identity is preserved when creating, loading, and deleting the same event
# * Across emoji
# * Across system timezones
# import datetime
# import pytz

# # Get the current datetime in the default system timezone
# default_now: datetime.datetime = datetime.datetime.now()
# print("Default timezone:", default_now.strftime("%Y-%m-%d %H:%M:%S"))

# # Set the desired timezone
# new_timezone: str = "US/Eastern"  # Replace with your desired timezone
# tz: pytz.BaseTzInfo = pytz.timezone(new_timezone)

# # Update the system timezone
# datetime.datetime.now(tz)

# # Get the current datetime in the new timezone
# new_now: datetime.datetime = datetime.datetime.now()
# print("New timezone:", new_now.strftime("%Y-%m-%d %H:%M:%S"))

# TD Setup gcal tests
# * Add the test calendar env variable to the secrets
# * Add a run tests workflow
