"""Handles the calendar creation and event moving"""
from datetime import datetime, timedelta
from typing import List

from gcsa.calendar import Calendar
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from wasabi import Printer

log = Printer(timestamp=True)


class CalendarHandler:
    def __init__(
        self,
        gcal_account: GoogleCalendar,
        mapping_buffer: timedelta = timedelta(days=2),
    ):
        self.gcal_account = gcal_account

    def get_calendar_names_in_events(self, events: List[Event]) -> List[str]:
        # Keep only those who have no spaces in description
        return list(
            {
                event.description
                for event in events
                if event.description is not None and "Data: " in event.description
            }
        )

    def _find_calendars_in_g_account(self) -> List[Calendar]:
        return list(self.gcal_account.get_calendar_list())

    def create_missing_calendars(self, events: List[Event]):
        calendars_in_g_account = self._find_calendars_in_g_account()
        calendars_in_g_account_names = [c.summary for c in calendars_in_g_account]
        calendars_in_events = self.get_calendar_names_in_events(events=events)

        missing_calendar_names = [
            c for c in calendars_in_events if c not in calendars_in_g_account_names
        ]

        missing_calendar_objects = [
            Calendar(summary=c, timezone=self.gcal_account.get_settings().timezone)
            for c in missing_calendar_names
        ]

        for calendar in missing_calendar_objects:
            log.info(f"Creating calendar {calendar.summary} because it was missing")
            self.gcal_account.add_calendar(calendar)

    def get_calendars_in_events(self, events: List[Event]) -> List[Calendar]:
        calendar_names = self.get_calendar_names_in_events(events=events)
        return [
            c
            for c in self._find_calendars_in_g_account()
            if c.summary in calendar_names
        ]

    def move_event_to_correct_calendar(self, event: Event):
        if event.description is not None and "Data: " in event.description:
            calendar_summary_to_id = {
                c.summary: c.id for c in self._find_calendars_in_g_account()
            }

            log.info(f"Moving event {event.summary} to calendar {event.description}")

            self.gcal_account.move_event(
                event, destination_calendar_id=calendar_summary_to_id[event.description]
            )

            log.info(f"Moved {event.summary} to calendar {event.description}")
