import datetime
import logging
from typing import Sequence

import devtools
import pydantic
import pytz
import pytz.tzfile
import requests

from rescuetime_to_gcal.event import Event


class RescuetimeEvent(pydantic.BaseModel):
    title: str
    start: datetime.datetime
    duration: datetime.timedelta

    def to_generic_event(self, timezone: pytz.tzinfo.BaseTzInfo) -> Event:
        return Event(
            title=self.title,
            start=timezone.localize(self.start),
            end=timezone.localize(self.start + self.duration),
        )


def load(
    api_key: str,
    anchor_date: datetime.datetime,
    lookback_window: datetime.timedelta,
    timezone: pytz.tzinfo.BaseTzInfo,
) -> Sequence[Event]:
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
    response = requests.get(
        "https://www.rescuetime.com/anapi/data", params=params
    ).json()

    events = [
        RescuetimeEvent(
            title=row[3],
            start=row[0],
            duration=datetime.timedelta(seconds=row[1]),
        )
        for row in response["rows"]
    ]
    logging.debug(f"Rescuetime {devtools.debug.format(events)}")

    return [e.to_generic_event(timezone) for e in events]
