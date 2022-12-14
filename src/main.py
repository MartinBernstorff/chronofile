import pandas as pd

from df_to_gcal import CalendarManager
from src.input_services.rescuetime import Rescuetime
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
        titles_to_keep=[
            "calendar",
            "citrix",
            "dr.dk",
            "facebook",
            "github",
            "hey",
            "linkedin",
            "logseq",
            "mail",
            "macrumors",
            "reddit",
            "slack",
            "star realms",
            "stackoverflow",
            "twitter",
            "Visual",
            "wandb.ai",
            "word",
            "youtube",
        ],
        min_duration="5 seconds",
    )

    calendar = CalendarManager(color_code=True)

    calendar.sync_df_to_calendar(
        df=rescuetime_df,
        title_col_name="title",
        start_time_col_name="start_time",
        end_time_col_name="end_time",
    )
