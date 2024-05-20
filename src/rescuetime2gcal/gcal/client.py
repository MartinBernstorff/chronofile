import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Sequence

import devtools
import pytz
from gcsa.event import Event as GCSAEvent
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.credentials import Credentials
from iterpy.arr import Arr

import rescuetime2gcal.delta as delta
from rescuetime2gcal.event import Event
from rescuetime2gcal.gcal._consts import required_scopes


def _to_gcsa_event(event: Event) -> GCSAEvent:
    return GCSAEvent(
        summary=event.title,
        start=event.start,  # type: ignore
        end=event.end,  # type: ignore
        timezone=event.timezone,
        event_id=event.destination_event_id,  # type: ignore
    )


def _to_generic_event(event: GCSAEvent) -> Event:
    return Event(
        title=event.summary,
        start=event.start,  # type: ignore
        end=event.end,  # type: ignore
        timezone=event.timezone,
        destination_event_id=event.event_id,
    )


def _dt_to_utc(dt: datetime) -> datetime:
    return dt.astimezone(pytz.UTC).replace(tzinfo=pytz.UTC)


def _timezone_to_utc(event: GCSAEvent) -> GCSAEvent:
    if not isinstance(event.start, datetime) or not isinstance(event.end, datetime):
        raise ValueError("Event must have timestamps, not dates")

    event.start = _dt_to_utc(event.start)
    event.end = _dt_to_utc(event.end)

    event.timezone = "UTC"

    return event


class DestinationClient(Protocol):
    """Interface for a client that can add, get, update, and delete events. All responsese must be in UTC."""

    def add_event(self, event: Event) -> Event:
        ...

    def get_events(self, start: datetime, end: datetime) -> Sequence[Event]:
        ...

    def update_event(self, event: Event) -> Event:
        ...

    def delete_event(self, event: Event) -> Event:
        ...


@dataclass
class GcalClient(DestinationClient):
    calendar_id: str
    client_id: str
    client_secret: str
    refresh_token: str

    def __post_init__(self):
        self._client = GoogleCalendar(
            default_calendar=self.calendar_id,
            credentials=Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                scopes=required_scopes,
                client_id=self.client_id,
                client_secret=self.client_secret,
            ),
        )

    def add_event(self, event: Event) -> Event:
        val = self._client.add_event(_to_gcsa_event(event))  # type: ignore
        return _to_generic_event(_timezone_to_utc(val))

    def get_events(self, start: datetime, end: datetime) -> Sequence[Event]:
        events = (
            Arr(self._client.get_events(start, end, order_by="updated", single_events=True))  # type: ignore
            .map(_timezone_to_utc)
            .map(_to_generic_event)
            .to_list()
        )
        logging.debug(f"Destination events: {devtools.debug.format(events)}")
        return events

    def update_event(self, event: Event) -> Event:
        response = self._client.update_event(_to_gcsa_event(event))  # type: ignore
        return _to_generic_event(_timezone_to_utc(response))

    def delete_event(self, event: Event) -> Event:
        self._client.delete_event(_to_gcsa_event(event))  # type: ignore
        return event


def sync(source_events: Sequence[Event], client: DestinationClient, dry_run: bool) -> None:
    destination_events = Arr(
        client.get_events(min([event.start for event in source_events]), datetime.today())
    ).to_list()

    changes = delta.changeset(source_events, destination_events)
    logging.info(f"Changes to be made: {devtools.debug.format(changes)}")

    if dry_run:
        logging.info("Dry run, not syncing")
        return

    for change in changes:
        match change:
            case delta.NewEvent():
                client.add_event(change.event)
            case delta.UpdateEvent():
                client.update_event(change.event)
