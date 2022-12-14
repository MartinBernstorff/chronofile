import pandas as pd

from df_to_gcal import CalendarManager
from rescuetime_puller import RescuetimePuller
from utils.log import log

API_KEY = "B6300jX6LJHN6RU0uhZCQfOJEMrn2RfLIY0bkT_z"

if __name__ == "__main__":
    log.info("Starting script")

    # One week ago as YYYY-MM-DD
    one_week_ago_timestamp = pd.Timestamp.today() - pd.Timedelta(days=7)
    one_week_ago_str = one_week_ago_timestamp.strftime("%Y-%m-%d")

    # Get today as YYYY-MM-DD
    today = pd.Timestamp.today().strftime("%Y-%m-%d")

    rt_puller = RescuetimePuller(api_key=API_KEY)
    rescuetime_df = rt_puller.pull(
        perspective="interval",
        resolution_time="minute",
        restrict_begin=one_week_ago_str,
        restrict_end=today,
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
