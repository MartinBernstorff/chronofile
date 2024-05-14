import datetime
from typing import Sequence

import pydantic
import pytz
import requests

from rescuetime_to_gcal.event import Event


class RescuetimeEvent(pydantic.BaseModel):
    title: str
    start: datetime.datetime
    duration: datetime.timedelta

    def to_generic_event(self) -> Event:
        return Event(
            title=self.title,
            start=self.start.astimezone(pytz.UTC),
            end=(self.start + self.duration).astimezone(pytz.UTC),
        )


def load(
    api_key: str,
    anchor_date: datetime.datetime,
    lookback_window: datetime.timedelta,
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
    # TODO: Change the timezone to UTC
    return [e.to_generic_event() for e in events]
