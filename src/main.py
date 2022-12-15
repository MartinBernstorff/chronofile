import pandas as pd

from input_services.rescuetime import Rescuetime
from output_services.events_to_calendar_mapper import EventsToCalendarMapper
from output_services.gcal.converter import df_to_gcsa_events
from output_services.gcal.syncer import CalendarSyncer
from utils.log import log

API_KEY = "B6300jX6LJHN6RU0uhZCQfOJEMrn2RfLIY0bkT_z"

if __name__ == "__main__":
    log.info("Starting script")

    rescuetime = Rescuetime(api_key=API_KEY)
    rescuetime_df = rescuetime.pull(
        perspective="interval",
        resolution_time="minute",
        anchor_date=pd.Timestamp.today(),
        lookbehind_distance=pd.Timedelta(days=2),
        titles_to_keep={
            "calendar": "Planning",
            "citrix": "Programming",
            "dr.dk": "Browsing",
            "facebook": "Browsing",
            "github": "Programming",
            "hey": "Browsing",
            "linkedin": "Browsing",
            "logseq": "Planning",
            "mail": "Communicating",
            "macrumors": "Browsing",
            "reddit": "Browsing",
            "slack": "Communicating",
            "star realms": "Gaming",
            "stackoverflow": "Programming",
            "twitter": "Browsing",
            "Visual": "Programming",
            "wandb.ai": "Programming",
            "word": "Writing",
            "youtube": "Browsing",
        },
        min_duration="5 seconds",
    )

    events = df_to_gcsa_events(rescuetime_df)

    mapper = EventsToCalendarMapper(events=events)
    mapper._map_events_to_calendars()

    calendar = CalendarSyncer().sync_events_to_calendar(events)
