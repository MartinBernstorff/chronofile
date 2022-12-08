from df_to_gcal import CalendarManager
from log import log
from rescuetime_to_df import (
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
        data=data, strs_to_match=["youtube", "reddit", "macrumors.com"]
    )
    events_of_interest = compute_end_time(data=events_of_interest)

    calendar = CalendarManager()

    calendar.sync_df_to_calendar(
        df=events_of_interest,
        title_col_name="title",
        start_time_col_name="start_time",
        end_time_col_name="end_time",
    )
