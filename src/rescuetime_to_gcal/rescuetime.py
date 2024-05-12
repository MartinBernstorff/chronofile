import datetime
from typing import Dict, Literal, Sequence, Union

import pandas as pd
import pydantic
import requests

from rescuetime_to_gcal.config import RecordCategory, RecordMetadata
from rescuetime_to_gcal.config import config as cfg


class RescuetimeEvent(pydantic.BaseModel):
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
    ) -> Sequence[RescuetimeEvent]:
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
            RescuetimeEvent(
                title=row[3],
                start=row[0],
                duration=datetime.timedelta(seconds=row[1]),
            )
            for row in response["rows"]
        ]
        return events

    def _filter_by_title(
        self,
        data: pd.DataFrame,
        strs_to_match: Sequence[str],
        mode: Literal["include", "exclude"],
    ) -> pd.DataFrame:
        """
        Gets all rows in a data frame that have a title containing "youtube".

        Args:
            data (pd.DataFrame): The data frame to filter.

        Returns:
            pd.DataFrame: A data frame containing only rows with titles containing "youtube".
        """
        # TODO: Rewrite to use RescuetimeEvents
        data[self.title_col_name] = data[self.title_col_name].str.lower()

        # Convert the list of strings to match to a regex pattern
        regex_pattern = r"|".join([s.lower() for s in strs_to_match])

        # Get the relevant titles
        distracting_titles = data[
            data[self.title_col_name].str.contains(regex_pattern)
        ][self.title_col_name].unique()

        matching = data[self.title_col_name].isin(distracting_titles)
        match mode:
            case "include":
                data = data[matching]
            case "exclude":
                data = data[~matching]

        # Get all rows with "Activity" in the "distracting_titles" list

        return data

    def _compute_end_time(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Adds duration and end_time columns to a data frame.

        Args:
            data (pd.DataFrame): The data frame to modify.

        Returns:
            pd.DataFrame: The modified data frame.
        """
        # TODO: Rewrite to use RescuetimeEvents
        # Create the end_time column
        data[self.end_col_name] = (
            data[self.start_col_name] + data[self.duration_col_name]
        )

        return data

    def _combine_overlapping_rows(
        self,
        df: pd.DataFrame,
        group_by_col: str,
        allowed_gap: pd.Timedelta,
    ) -> pd.DataFrame:
        # TODO: Rewrite to use RescuetimeEvents. Add tests.
        """Combine rows with overlapping end and start times.

        First group by group_by_col. Then, if a row's end time is the same or later than the next row's start time, combine the two rows.

        Args:
            df (pd.DataFrame): The data frame to modify.
            start_col_name (str): The name of the column containing the start time.
            end_col_name (str): The name of the column containing the end time.
            group_by_col (str): The name of the column to group by.
            duration_col_name (str): The name of the column containing the duration.
            allowed_gap (pd.Timedelta): The maximum allowed gap between the end of a row and the start of the next row.

        Returns:
            pd.DataFrame: The modified data frame.
        """
        grouped_df = df.groupby(group_by_col)
        df_elements = []

        for _, group_df in grouped_df:
            # Keep iterating until no more rows can be combined
            while True:
                if len(group_df) == 1:
                    break

                n_before_combining = len(group_df)

                group_df = group_df.reset_index(drop=True)

                for index, row in group_df.iterrows():
                    if index == len(group_df) - 1:
                        break

                    if (
                        row[self.end_col_name]
                        >= group_df.iloc[index + 1][self.start_col_name] - allowed_gap  # type: ignore
                    ):
                        group_df.at[index + 1, self.start_col_name] = group_df.iloc[  # type: ignore
                            index
                        ][self.start_col_name]

                        group_df.at[index + 1, self.duration_col_name] = (  # type: ignore
                            group_df.iloc[index][self.duration_col_name]  # type: ignore
                            + group_df.iloc[index + 1][self.duration_col_name]  # type: ignore
                        )

                        # Set the drop column to True for the row that will be dropped
                        group_df.at[index, "drop"] = True

                if "drop" in group_df.columns:
                    group_df = group_df[group_df["drop"] != True]  # noqa: E712

                if n_before_combining == len(group_df):
                    break

            df_elements += [group_df.apply(lambda x: x).reset_index(drop=True)]

        df = pd.concat(df_elements)

        return df

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

        data = self._combine_overlapping_rows(
            df=data,
            group_by_col="title",
            allowed_gap=allowed_gap_for_combining - pd.Timedelta(min_duration),
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
