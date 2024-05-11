import time
from dataclasses import dataclass
from datetime import datetime
from typing import List

import pandas as pd
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.credentials import Credentials
from pydantic import BaseModel
from rescuetime_to_gcal.base_config import required_scopes
from rescuetime_to_gcal.utils.log import log


class MinimalEvent(BaseModel):
    title: str
    start: datetime
    end: datetime
    timezone: str = "Europe/Copenhagen"

    def __init__(self, **data) -> None:
        super().__init__(**data)

        # Convert all datetime.datetime objects to Timestamps without tzoffset
        if self.start.tzinfo is not None:
            self.start = pd.Timestamp(self.start).tz_convert(self.timezone)
        else:
            self.start = pd.Timestamp(self.start).tz_localize(self.timezone)

        if self.end.tzinfo is not None:
            self.end = pd.Timestamp(self.end).tz_convert(self.timezone)
        else:
            self.end = pd.Timestamp(self.end).tz_localize(self.timezone)

    def to_gcsa_event(self) -> Event:
        return Event(
            title=self.title, start=self.start, end=self.end, summary=self.title
        )


@dataclass
class GcalSyncer:
    email: str
    client_id: str
    project_id: str
    client_secret: str
    refresh_token: str

    def __post_init__(self):
        self.calendar: GoogleCalendar = GoogleCalendar(
            self.email,
            credentials=Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                scopes=required_scopes,
                client_id=self.client_id,
                client_secret=self.client_secret,
            ),
        )

    def _deduplicate_events(
        self,
        events: List[Event],
        events_in_calendar: List[Event],
    ) -> List[Event]:
        # Filter out events that are in the calendar, based on the start, end and summary attributes
        events_to_sync = [
            event
            for event in events
            if not any(
                [
                    event.start == calendar_event.start
                    and event.end == calendar_event.end
                    and event.summary == calendar_event.summary
                    for calendar_event in events_in_calendar
                ]
            )
        ]

        return events_to_sync

    def _update_event_if_exists(
        self,
        event_to_sync: Event,
        events_in_calendar: List[Event],
        calendar: GoogleCalendar,
    ) -> bool:
        # Check if event exists in calendar based on summary and start time
        event_matches = [
            event
            for event in events_in_calendar
            if event.summary == event_to_sync.summary
            and event.start == event_to_sync.start
        ]

        if len(event_matches) == 0:
            return False

        matched_event = event_matches[0]
        event_matches[0].end = event_to_sync.end
        calendar.update_event(matched_event)
        log.good(
            f"Updated event in calendar, {matched_event.start} - {matched_event.summary}"
        )
        return True

    def _sync_event(
        self,
        event_to_sync: Event,
        events_in_calendar: List[Event],
        calendar: GoogleCalendar,
    ):
        event_updated = self._update_event_if_exists(
            event_to_sync=event_to_sync,
            events_in_calendar=events_in_calendar,
            calendar=calendar,
        )

        if not event_updated:
            # Add event to calendar
            calendar.add_event(event_to_sync)
            log.good(
                f"Added event to calendar, {event_to_sync.start} - {event_to_sync.summary}"
            )
            time.sleep(5)

    def sync_events_to_calendar(
        self, events: List[Event], do_not_sync: bool = False
    ) -> None:  # Add calendar arguments here
        if do_not_sync:
            return None

        min_date_in_events = min([event.start for event in events])

        events_in_calendar = list(
            self.calendar.get_events(
                min_date_in_events,
                datetime.today(),
                order_by="updated",
                single_events=True,
            )
        )
        # Deduplicate events
        dedup_events_to_sync = self._deduplicate_events(
            events=events, events_in_calendar=events_in_calendar
        )

        # Update events if already exists with identical start time
        for event in dedup_events_to_sync:
            self._sync_event(
                event_to_sync=event,
                events_in_calendar=events_in_calendar,
                calendar=self.calendar,
            )
