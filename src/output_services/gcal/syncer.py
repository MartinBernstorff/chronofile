from datetime import datetime
from typing import List

from gcsa.calendar import Calendar
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from wasabi import Printer

from output_services.events_to_calendar_mapper import EventsToCalendarMapper
from utils.log import log

log = Printer(timestamp=True)


class CalendarSyncer:
    def __init__(self, group_col_name: str = "category"):
        self.calendar = GoogleCalendar(
            "martinbernstorff@gmail.com",
            credentials_path="credentials/credentials.json",
        )

        self.timezone = self.calendar.get_settings().timezone
        self.group_col_name = group_col_name
        self.min_date_in_events = None

    def _deduplicate_events(
        self, events: List[Event], calendar: Calendar, events_in_calendar: List[Event]
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
                    and event.description == calendar_event.description
                    for calendar_event in events_in_calendar
                ]
            )
        ]

        return events_to_sync

    def _update_event_if_exists(
        self, event_to_sync: Event, events_in_calendar: List[Event], calendar: Calendar
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
        event_matches[0].description = event_to_sync.description

        calendar.update_event(matched_event)
        log.good(
            f"Updated event in calendar, {matched_event.start} - {matched_event.summary}"
        )
        return True

    def _sync_event(
        self, event_to_sync: Event, events_in_calendar: List[Event], calendar: Calendar
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

    def sync_events_to_calendar(
        self, events: List[Event]
    ) -> None:  # Add calendar arguments here
        calendar = self.calendar

        self.min_date_in_events = min([event.start for event in events])

        events_in_calendar = list(
            calendar.get_events(
                self.min_date_in_events,
                datetime.today(),
                order_by="updated",
                single_events=True,
            )
        )
        # Deduplicate events
        dedup_events_to_sync = self._deduplicate_events(
            events=events, calendar=calendar, events_in_calendar=events_in_calendar
        )

        # Update events if already exists with identical start time
        for event in dedup_events_to_sync:
            self._sync_event(
                event_to_sync=event,
                events_in_calendar=events_in_calendar,
                calendar=calendar,
            )

        if self.group_col_name:
            EventsToCalendarMapper(
                gcal_account=self.calendar, min_date=self.min_date_in_events
            ).move_events_to_correct_calendar()
