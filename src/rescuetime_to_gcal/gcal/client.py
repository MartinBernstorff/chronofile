import logging
from datetime import date, datetime
from typing import Sequence

import devtools
import pytz
from gcsa.event import Event as GCSAEvent
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.credentials import Credentials
from iterpy.arr import Arr

import rescuetime_to_gcal.delta as delta
from rescuetime_to_gcal.event import Event
from rescuetime_to_gcal.gcal._consts import required_scopes


def _to_gcsa_event(event: Event) -> GCSAEvent:
    if event.gcal_event_id is None:
        raise ValueError("Event must have a gcal_event_id")

    return GCSAEvent(
        summary=event.title,
        start=event.start,  # type: ignore
        end=event.end,  # type: ignore
        timezone=event.timezone,
        event_id=event.gcal_event_id,
    )


def _to_generic_event(event: GCSAEvent) -> Event:
    return Event(
        title=event.summary,
        start=event.start,  # type: ignore
        end=event.end,  # type: ignore
        timezone=event.timezone,
        gcal_event_id=event.event_id,
    )


def _timezone_to_utc(event: GCSAEvent) -> GCSAEvent:
    if isinstance(event.start, date) or isinstance(event.end, date):
        return event

    event.start = event.start.astimezone(pytz.UTC)
    event.end = event.end.astimezone(pytz.UTC)
    event.timezone = "UTC"

    return event


def sync(
    source_events: Sequence[Event],
    email: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> None:
    destination = GoogleCalendar(
        email,
        credentials=Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=required_scopes,
            client_id=client_id,
            client_secret=client_secret,
        ),
    )

    destination_events = (
        Arr(
            destination.get_events(
                min([event.start for event in source_events]),
                datetime.today(),
                order_by="updated",
                single_events=True,
            )
        )
        .map(_timezone_to_utc)
        .map(_to_generic_event)
        .to_list()
    )
    logging.debug(f"Destination events: {devtools.debug.format(destination_events)}")

    changes = delta.changeset(
        source_events,
        destination_events,
    )

    for change in changes:
        match change:
            case delta.NewEvent():
                destination.add_event(_to_gcsa_event(change.event))
            case delta.UpdateEvent():
                destination.update_event(_to_gcsa_event(change.event))
