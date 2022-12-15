from typing import Dict, List, Set

from gcsa.calendar import Calendar
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from wasabi import Printer

log = Printer(timestamp=True)


class EventsToCalendarMapper:
    def __init__(self, events: List[Event]):
        self.calendar = GoogleCalendar(
            "martinbernstorff@gmail.com",
            credentials_path="credentials/credentials.json",
        )

        self.events = events

    def _find_calendars_in_events(self) -> Set[str]:
        return list({event.description for event in self.events})

    def _find_calendars_in_g_account(self) -> Set[Calendar]:
        return self.calendar.get_calendar_list()

    def _map_events_to_calendars(self) -> Dict[str, List[Event]]:
        calendars_in_g_account = self._find_calendars_in_g_account()
        calendars_in_events = self._find_calendars_in_events()

        missing_calendars = calendars_in_events - calendars_in_g_account
