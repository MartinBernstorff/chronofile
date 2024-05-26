import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Generic, Protocol, Sequence

import devtools
import pytz
import rescuetime2gcal.delta as delta
from gcsa.event import Event as GCSAEvent
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.credentials import Credentials
from iterpy.arr import Arr
from pydantic import ValidationError
from rescuetime2gcal.clients.gcal._consts import required_scopes
from rescuetime2gcal.preprocessing import DestinationEvent, ParsedEvent

if TYPE_CHECKING:
    from rescuetime2gcal.source_event import SourceEvent


def _parsed_to_gcsa_event(event: ParsedEvent) -> GCSAEvent:
    return GCSAEvent(summary=event.title, start=event.start, end=event.end, timezone=event.timezone)


def _destination_to_gcsa_event(event: "DestinationEvent") -> GCSAEvent:
    return GCSAEvent(
        summary=event.title,
        start=event.start,
        end=event.end,
        timezone=event.timezone,
        event_id=event.id,
    )


def _to_destination_event(event: GCSAEvent) -> DestinationEvent:
    # Unpack here, to avoid overzealous type ignore
    start: datetime = event.start  # type: ignore
    end: datetime = event.end  # type: ignore
    return DestinationEvent(
        title=event.summary, start=start, end=end, timezone=event.timezone, id=event.event_id
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

    def add_event(self, event: ParsedEvent) -> DestinationEvent:
        ...

    def get_events(self, start: datetime, end: datetime) -> Sequence[DestinationEvent]:
        ...

    def update_event(self, event: DestinationEvent) -> DestinationEvent:
        ...

    def delete_event(self, event: DestinationEvent) -> None:
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

    def add_event(self, event: ParsedEvent) -> DestinationEvent:
        val = self._client.add_event(  # type: ignore
            _parsed_to_gcsa_event(event)
        )
        return _to_destination_event(_timezone_to_utc(val))

    def get_events(self, start: datetime, end: datetime) -> Sequence[DestinationEvent]:
        events = (
            Arr(
                self._client.get_events(  # type: ignore
                    start, end, order_by="updated", single_events=True
                )
            )
            .map(_timezone_to_utc)
            .map(_to_destination_event)
            .to_list()
        )
        logging.debug(f"Destination events: {devtools.debug.format(events)}")
        return events

    def update_event(self, event: DestinationEvent) -> DestinationEvent:
        response = self._client.update_event(  # type: ignore
            _destination_to_gcsa_event(event)
        )
        return _to_destination_event(_timezone_to_utc(response))

    def delete_event(self, event: DestinationEvent) -> None:
        self._client.delete_event(  # type: ignore
            _destination_to_gcsa_event(event)
        )
