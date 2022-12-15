from datetime import datetime
from typing import List, Tuple

from gcsa.calendar import Calendar
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from wasabi import Printer

from output_services.gcal.calendar_handler import CalendarHandler
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
        self.calendar_handler = CalendarHandler(
            gcal_account=self.calendar,
        )

        self.all_calendars = self.calendar_handler._find_calendars_in_g_account()

    def _deduplicate_events(
        self,
        candidate_events: List[Event],
        events_in_calendar: List[Event],
        attributes: Tuple[str],
    ) -> List[Event]:

        # Filter out events that are in the calendar, based on the start, end and summary attributes
        events_to_sync = [
            event
            for event in candidate_events
            if not any(
                [
                    all(
                        getattr(event, attribute) == getattr(calendar_event, attribute)
                        for attribute in attributes
                    )
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
        matched_event.end = event_to_sync.end
        # matched_event.description = event_to_sync.description

        self.calendar.update_event(matched_event)
        self.calendar_handler.move_event_to_correct_calendar(matched_event)

        log.good(
            f"Updated event in calendar, {matched_event.start} - {matched_event.summary}"
        )

        return True

    def _sync_event(
        self, event_to_sync: Event, events_in_gcal: List[Event], calendar: Calendar
    ):
        event_updated = self._update_event_if_exists(
            event_to_sync=event_to_sync,
            events_in_calendar=events_in_gcal,
            calendar=calendar,
        )

        if not event_updated:
            # Add event to calendar
            new_event = self.calendar.add_event(event_to_sync)
            log.good(
                f"Added event to calendar, {new_event.start} - {new_event.summary}"
            )

            self.calendar_handler.move_event_to_correct_calendar(new_event)

    def sync_events_to_calendar(
        self, events_to_sync: List[Event]
    ) -> None:  # Add calendar arguments here
        self.min_date_in_events = min([event.start for event in events_to_sync])
        self.calendar_handler.create_missing_calendars(events=events_to_sync)

        calendars_in_events = self.calendar_handler.get_calendars_in_events(
            events=events_to_sync
        )

        all_events = [
            self.calendar.get_events(
                self.min_date_in_events,
                datetime.now(),
                order_by="updated",
                single_events=True,
                calendar_id=calendar.id,
            )
            for calendar in self.all_calendars
        ]

        # Combine list of lists into one list
        all_events = [item for sublist in all_events for item in sublist]

        for calendar in calendars_in_events:
            events_for_calendar = [
                e for e in events_to_sync if calendar.summary in e.description
            ]

            events_in_calendar = list(
                self.calendar.get_events(
                    self.min_date_in_events,
                    datetime.now(),
                    order_by="updated",
                    single_events=True,
                    calendar_id=calendar.id,
                )
            )

            # Deduplicate events
            dedup_events_to_sync = self._deduplicate_events(
                candidate_events=events_for_calendar,
                events_in_calendar=events_in_calendar,
                attributes=("start", "end", "summary", "description"),
            )

            # Update events if already exists with identical start time
            for event in dedup_events_to_sync:
                self._sync_event(
                    event_to_sync=event,
                    events_in_gcal=all_events,
                    calendar=calendar,
                )
