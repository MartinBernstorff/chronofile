import pandas as pd

from df_to_gcal import CalendarManager
from log import log
from rescuetime_to_df import (
    combine_overlapping_rows,
    compute_end_time,
    get_events_containing_str,
    get_from_rescuetime,
)

if __name__ == "__main__":
    log.info("Starting script")

    data = get_from_rescuetime(
        perspective="interval",
        resolution_time="minute",
        restrict_begin="2022-12-08",
        restrict_end="2022-12-08",
    )

    events_of_interest = get_events_containing_str(
        data=data,
        strs_to_match=[
            "Star realms",
            "youtube",
            "reddit",
            "macrumors",
            "hey",
            "twitter",
            "Visual",
        ],
    )
    events_of_interest = compute_end_time(data=events_of_interest)[
        ["start_time", "end_time", "title", "duration"]
    ]

    events_of_interest = combine_overlapping_rows(
        df=events_of_interest,
        start_col_name="start_time",
        end_col_name="end_time",
        duration_col_name="duration",
        group_by_col="title",
        allowed_gap=pd.Timedelta("5 minutes"),
    )

    calendar = CalendarManager()

    calendar.sync_df_to_calendar(
        df=events_of_interest,
        title_col_name="title",
        start_time_col_name="start_time",
        end_time_col_name="end_time",
    )
