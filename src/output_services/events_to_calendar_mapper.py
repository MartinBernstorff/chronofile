from datetime import datetime, timedelta
from typing import Dict, List, Set

from gcsa.calendar import Calendar
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from wasabi import Printer

log = Printer(timestamp=True)


class EventsToCalendarMapper:
    def __init__(
        self,
        gcal_account: GoogleCalendar,
        min_date: datetime,
        mapping_buffer: timedelta = timedelta(days=2),
    ):
        self.gcal_account = gcal_account
        self.min_date_to_sync = min_date - mapping_buffer
        self.events = list(
            self.gcal_account.get_events(
                self.min_date_to_sync, datetime.now(), order_by="updated"
            )
        )

    def _find_calendars_in_events(self) -> List[str]:
        # Keep only those who have no spaces in description
        return list(
            {
                event.description
                for event in self.events
                if event.description is not None and "Data: " in event.description
            }
        )

    def _find_calendars_in_g_account(self) -> List[Calendar]:
        return list(self.gcal_account.get_calendar_list())

    def _create_missing_calendars(self) -> Dict[str, List[Event]]:
        calendars_in_g_account = self._find_calendars_in_g_account()
        calendars_in_g_account_names = [c.summary for c in calendars_in_g_account]
        calendars_in_events = self._find_calendars_in_events()

        missing_calendar_names = [
            c for c in calendars_in_events if c not in calendars_in_g_account_names
        ]

        missing_calendar_objects = [
            Calendar(summary=c, timezone=self.gcal_account.get_settings().timezone)
            for c in missing_calendar_names
        ]

        for calendar in missing_calendar_objects:
            self.gcal_account.add_calendar(calendar)

    def move_events_to_correct_calendar(self) -> Dict[str, List[Event]]:
        self._create_missing_calendars()

        events_to_move = [
            e
            for e in self.events
            if e.description is not None and "Data: " in e.description
        ]

        calendar_summary_to_id = {
            c.summary: c.id for c in self._find_calendars_in_g_account()
        }

        for event in events_to_move:
            log.info(f"Moving event {event.summary} to calendar {event.description}")
            self.gcal_account.move_event(
                event, destination_calendar_id=calendar_summary_to_id[event.description]
            )
