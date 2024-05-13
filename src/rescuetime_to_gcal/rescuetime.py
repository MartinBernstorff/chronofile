import datetime
from dataclasses import dataclass
from typing import Literal, Sequence, Union

import pydantic
import requests

from rescuetime_to_gcal.event import Event


class RescuetimeEvent(pydantic.BaseModel):
    title: str
    start: datetime.datetime
    duration: datetime.timedelta

    def to_generic_event(self) -> Event:
        return Event(
            title=self.title,
            start=self.start,
            end=self.start + self.duration,
        )


@dataclass(frozen=True)
class RescuetimeClient:
    api_key: str
    url: str = "https://www.rescuetime.com/anapi/data"

    def _get_data(
        self,
        perspective: Literal["interval"] = "interval",
        resolution_time: Literal["minute"] = "minute",
        restrict_begin: Union[str, None] = None,
        restrict_end: Union[str, None] = None,
    ) -> Sequence[Event]:
        params = {
            "key": self.api_key,
            "perspective": perspective,
            "resolution_time": resolution_time,
            "format": "json",
        }

        # Set the date range for the API request, if provided
        if restrict_begin is not None:
            params["restrict_begin"] = restrict_begin
        if restrict_end is not None:
            params["restrict_end"] = restrict_end

        # Make the API request
        response = requests.get(self.url, params=params).json()
        events = [
            RescuetimeEvent(
                title=row[3],
                start=row[0],
                duration=datetime.timedelta(seconds=row[1]),
            )
            for row in response["rows"]
        ]
        return [e.to_generic_event() for e in events]

    def pull(
        self,
        anchor_date: datetime.datetime,
        lookback_window: datetime.timedelta,
        perspective: Literal["interval"] = "interval",
        resolution_time: Literal["minute"] = "minute",
    ) -> Sequence[Event]:
        return self._get_data(
            resolution_time=resolution_time,
            perspective=perspective,
            restrict_begin=(anchor_date - lookback_window).strftime("%Y-%m-%d"),
            restrict_end=anchor_date.strftime("%Y-%m-%d"),
        )
