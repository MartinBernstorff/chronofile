import logging
from datetime import date, datetime
from typing import Sequence

import pytz
from gcsa.event import Event as GCSAEvent
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.credentials import Credentials
from iterpy.arr import Arr

from rescuetime_to_gcal.constants import required_scopes
from rescuetime_to_gcal.event import Event
from rescuetime_to_gcal.gcal._deduper import _deduper


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

    destination_events = Arr(
        destination.get_events(
            min([event.start for event in source_events]),
            datetime.today(),
            order_by="updated",
            single_events=True,
        )
    ).map(_timezone_to_utc)

    deduped_events = _deduper(
        destination_events=destination_events.to_list(),
        source_events=[
            GCSAEvent(
                summary=e.title,
                start=e.start,
                end=e.end,
                timezone=e.timezone,
            )
            for e in source_events
        ],
    )

    for update_event in deduped_events:
        existing_event = [
            event
            for event in destination_events
            if event.summary == update_event.summary
            and event.start == update_event.start
        ]

        event_exists = len(existing_event) != 0
        if event_exists:
            matched_event = existing_event[0]
            matched_event.end = update_event.end
            destination.update_event(matched_event)
            logging.info(
                f"Updated event in calendar, {matched_event.start} - {matched_event.summary}"
            )
        else:
            destination.add_event(update_event)
            logging.info(
                f"Created event  {update_event.start} - {update_event.summary}"
            )
