import datetime
import logging
from typing import TYPE_CHECKING, Sequence

import devtools
import pytz
import requests
from rescuetime_to_gcal.event import BareEvent

if TYPE_CHECKING:
    import pytz.tzfile


def load(
    api_key: str,
    anchor_date: datetime.datetime,
    lookback_window: datetime.timedelta,
    timezone: "pytz.tzinfo.BaseTzInfo",
) -> Sequence["BareEvent"]:
    params = {
        "key": api_key,
        "perspective": "interval",
        "resolution_time": "minute",
        "format": "json",
    }

    # Set the date range for the API request, if provided
    params["restrict_begin"] = (anchor_date - lookback_window).strftime("%Y-%m-%d")
    params["restrict_end"] = anchor_date.strftime("%Y-%m-%d")

    # Make the API request
    response = requests.get("https://www.rescuetime.com/anapi/data", params=params).json()

    timezone_naive_events = [
        BareEvent(title=row[3], start=row[0], duration=datetime.timedelta(seconds=row[1]))
        for row in response["rows"]
    ]

    timezone_aware_events = [
        BareEvent(title=e.title, start=timezone.localize(e.start), duration=e.duration)
        for e in timezone_naive_events
    ]
    logging.debug(f"Rescuetime {devtools.debug.format(timezone_aware_events)}")

    return timezone_aware_events
