import pandas as pd

from df_to_gcal import CalendarManager
from rescuetime_puller import RescuetimePuller
from utils.log import log

API_KEY = "B6300jX6LJHN6RU0uhZCQfOJEMrn2RfLIY0bkT_z"

if __name__ == "__main__":
    log.info("Starting script")

    # Get today as YYYY-MM-DD
    today = pd.Timestamp.today().strftime("%Y-%m-%d")

    rt_puller = RescuetimePuller(api_key=API_KEY)
    rescuetime_df = rt_puller.pull(
        perspective="interval",
        resolution_time="minute",
        restrict_begin=today,
        restrict_end=today,
        titles_to_keep=[
            "dr.dk",
            "facebook",
            "hey",
            "linkedin",
            "macrumors",
            "reddit",
            "star realms",
            "twitter",
            "Visual",
            "youtube",
            "citrix",
            "github",
            "wandb.ai",
            "logseq",
            "mail",
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
