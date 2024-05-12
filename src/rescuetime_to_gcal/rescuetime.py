import datetime
from typing import Callable, Dict, Literal, Sequence, Union

import pandas as pd
import pydantic
import requests
from iterpy.arr import Arr

from rescuetime_to_gcal.config import RecordCategory, RecordMetadata
from rescuetime_to_gcal.config import config as cfg


class Event(pydantic.BaseModel):
    title: str
    start: datetime.datetime
    duration: datetime.timedelta

    @property
    def end(self) -> datetime.datetime:
        return self.start + self.duration


class Rescuetime:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://www.rescuetime.com/anapi/data"
        self.title_col_name: str = "title"
        self.start_col_name: str = "start_time"
        self.end_col_name: str = "end_time"
        self.category_col_name: str = "category"
        self.duration_col_name: str = "duration_seconds"
        self.category2emoji: dict[RecordCategory, str] = cfg.category2emoji

    @staticmethod
    def _get_data(
        api_key: str,
        url: str,
        perspective: Literal["interval"] = "interval",
        resolution_time: Literal["minute"] = "minute",
        restrict_begin: Union[str, None] = None,
        restrict_end: Union[str, None] = None,
    ) -> Sequence[Event]:
        params = {
            "key": api_key,
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
        response = requests.get(url, params=params).json()
        events = [
            Event(
                title=row[3],
                start=row[0],
                duration=datetime.timedelta(seconds=row[1]),
            )
            for row in response["rows"]
        ]
        return events

    @staticmethod
    def _filter_by_title(
        data: Sequence[Event],
        strs_to_match: Sequence[str],
    ) -> Sequence[Event]:
        return [
            event
            for event in data
            if not any([title.lower() in event.title for title in strs_to_match])
        ]

    @staticmethod
    def _merge_events_within_window(
        events: Sequence[Event],
        group_by: Callable[[Event], str],
        merge_gap: datetime.timedelta,
    ) -> Sequence[Event]:
        # TODO: Rewrite to use RescuetimeEvents. Add tests.
        """Combine rows with overlapping end and start times.

        First group by group_by_col. Then, if a row's end time is the same or later than the next row's start time, combine the two rows.
        """
        groups = Arr(events).groupby(group_by)

        for _, group_events in groups:
            sorted_events = sorted(group_events, key=lambda e: e.start)
            for i, e in enumerate(sorted_events):
                if i == 0:
                    continue
                if e.start <= sorted_events[i - 1].end + merge_gap:
                    sorted_events[i - 1].duration += e.duration
                    # TODO Assumes that events do not overlap, otherwise we cannot add together the durations.
                    # An alternative is to add an end date to the events, and then update the end date.
                    sorted_events.pop(i)
                    i -= 1

        return groups.map(lambda g: g[1]).flatten().to_list()

    def _set_time_dtypes(self, data: pd.DataFrame) -> pd.DataFrame:
        # TODO: Rewrite to use RescuetimeEvents

        # Convert the start_time column to a datetime column
        data[self.start_col_name] = pd.to_datetime(data[self.start_col_name])

        # Convert the duration_seconds column to a timedelta column
        data[self.duration_col_name] = pd.to_timedelta(
            data[self.duration_col_name], unit="seconds"
        )

        return data

    def _map_title_to_category(
        self, data: pd.DataFrame, title_pattern_to_cateogory: Dict[str, str]
    ) -> pd.DataFrame:
        """Map titles to categories.

        Assign the category of the first matching title pattern to each row.
        Title matches are case insensitive. A match is found if the title contains the pattern.
        """
        # TODO: Rewrite to use RescuetimeEvents
        for k in title_pattern_to_cateogory:
            regex_pattern = k.lower()

            matching_values = data[
                data[self.title_col_name].str.contains(regex_pattern)
            ][self.title_col_name].unique()

            # Create a new column where you
            # map the category to the matching values
            data.loc[
                data[self.title_col_name].isin(matching_values),
                self.category_col_name,
            ] = title_pattern_to_cateogory[k]

        return data

    def _apply_metadata(
        self, row: pd.Series, metadata: Sequence[RecordMetadata]
    ) -> pd.Series:
        # TODO: Rewrite to use RescuetimeEvents
        for record in metadata:
            if any(
                [
                    title.lower() in row[self.title_col_name].lower()
                    for title in record.title_matcher
                ]
            ):
                row[self.category_col_name] = record.category.value
                if record.prettified_title is not None:
                    row[self.title_col_name] = record.prettified_title
                row[self.title_col_name] = (
                    f"{self._category2emoji(record.category)} {row[self.title_col_name]} "
                )

        return row

    def _category2emoji(self, category: RecordCategory) -> str:
        return self.category2emoji[category]

    def pull(
        self,
        anchor_date: pd.Timestamp,
        lookbehind_distance: pd.Timedelta,
        titles_to_keep: Sequence[str] | None,
        titles_to_exclude: Sequence[str] | None,
        perspective: Literal["interval"] = "interval",
        resolution_time: Literal["minute"] = "minute",
        min_duration: str = "0 seconds",
        allowed_gap_for_combining: pd.Timedelta = pd.Timedelta("5 minutes"),
        metadata: Sequence[RecordMetadata] | None = None,
    ):
        # TODO: Rewrite to use RescuetimeEvents
        data = self._get_data(
            resolution_time=resolution_time,
            perspective=perspective,
            restrict_begin=(anchor_date - lookbehind_distance).strftime("%Y-%m-%d"),
            restrict_end=anchor_date.strftime("%Y-%m-%d"),
        )

        if titles_to_exclude:
            data = self._filter_by_title(
                data=data, strs_to_match=titles_to_exclude, mode="exclude"
            )

        if titles_to_keep:
            data = self._filter_by_title(
                data=data, strs_to_match=titles_to_keep, mode="include"
            )

        data = self._compute_end_time(data=data)

        if min_duration:
            data = data[data[self.duration_col_name] > pd.Timedelta(min_duration)]

        data = self._merge_events_within_window(
            df=data,
            group_by="title",
            merge_gap=allowed_gap_for_combining - pd.Timedelta(min_duration),
        )

        data = data.sort_values(by="start_time")

        if metadata:
            data = data.apply(
                lambda row: self._apply_metadata(row=row, metadata=metadata), axis=1
            )

        return data[
            [
                self.title_col_name,
                self.start_col_name,
                self.end_col_name,
                self.duration_col_name,
            ]
        ].reset_index(drop=True)
