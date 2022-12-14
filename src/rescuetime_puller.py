from typing import List, Literal, Union

import pandas as pd
import requests


class RescuetimePuller:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://www.rescuetime.com/anapi/data"
        self.title_col_name: str = "title"
        self.start_col_name: str = "start_time"
        self.end_col_name: str = "end_time"
        self.duration_col_name: str = "duration_seconds"

    def _get_data(
        self,
        perspective: Literal["interval"] = "interval",
        resolution_time: Literal["minute"] = "minute",
        restrict_begin: Union[str, None] = None,
        restrict_end: Union[str, None] = None,
    ) -> pd.DataFrame:
        """
        Makes an API request to the RescueTime API and returns the response as a pandas DataFrame.
        """
        # Set the parameters for the API request
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

        # Add column labels to the data
        column_labels = response["row_headers"]
        data = [dict(zip(column_labels, row)) for row in response["rows"]]

        output_df = pd.DataFrame(data)

        # Convert the API response to a pandas DataFrame
        output_df = output_df.rename(
            columns={
                "Activity": self.title_col_name,
                "Date": self.start_col_name,
                "Time Spent (seconds)": self.duration_col_name,
            }
        )

        output_df = self._set_time_dtypes(output_df)

        return output_df

    def _filter_by_title(
        self, data: pd.DataFrame, strs_to_match: List[str]
    ) -> pd.DataFrame:
        """
        Gets all rows in a data frame that have a title containing "youtube".

        Args:
            data (pd.DataFrame): The data frame to filter.

        Returns:
            pd.DataFrame: A data frame containing only rows with titles containing "youtube".
        """
        # Get a list of unique titles that contain any element in the distracting_title list
        # Convert the title column to lowercase
        data[self.title_col_name] = data[self.title_col_name].str.lower()

        # Convert the list of strings to match to a regex pattern
        regex_pattern = r"|".join([s.lower() for s in strs_to_match])

        # Get the relevant titles
        distracting_titles = data[
            data[self.title_col_name].str.contains(regex_pattern)
        ][self.title_col_name].unique()

        # Get all rows with "Activity" in the "distracting_titles" list
        data = data[data[self.title_col_name].isin(distracting_titles)]

        return data

    def _compute_end_time(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Adds duration and end_time columns to a data frame.

        Args:
            data (pd.DataFrame): The data frame to modify.

        Returns:
            pd.DataFrame: The modified data frame.
        """
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
                        >= group_df.iloc[index + 1][self.start_col_name] - allowed_gap
                    ):
                        group_df.at[index + 1, self.start_col_name] = group_df.iloc[
                            index
                        ][self.start_col_name]

                        group_df.at[index + 1, self.duration_col_name] = (
                            group_df.iloc[index][self.duration_col_name]
                            + group_df.iloc[index + 1][self.duration_col_name]
                        )

                        # Set the drop column to True for the row that will be dropped
                        group_df.at[index, "drop"] = True

                if "drop" in group_df.columns:
                    group_df = group_df[group_df["drop"] != True]

                if n_before_combining == len(group_df):
                    break

            df_elements += [group_df.apply(lambda x: x).reset_index(drop=True)]

        df = pd.concat(df_elements)

        return df

    def _set_time_dtypes(self, data: pd.DataFrame) -> pd.DataFrame:
        # Convert the start_time column to a datetime column
        data[self.start_col_name] = pd.to_datetime(data[self.start_col_name])

        # Convert the duration_seconds column to a timedelta column
        data[self.duration_col_name] = pd.to_timedelta(
            data[self.duration_col_name], unit="seconds"
        )

        return data

    def pull(
        self,
        anchor_date: pd.Timestamp,
        lookbehind_distance: pd.Timedelta,
        perspective: Literal["interval"] = "interval",
        resolution_time: Literal["minute"] = "minute",
        titles_to_keep=List[str],
        min_duration: str = "0 seconds",
    ):
        data = self._get_data(
            resolution_time=resolution_time,
            perspective=perspective,
            restrict_begin=(anchor_date - lookbehind_distance).strftime("%Y-%m-%d"),
            restrict_end=anchor_date.strftime("%Y-%m-%d"),
        )

        if titles_to_keep:
            data = self._filter_by_title(data=data, strs_to_match=titles_to_keep)

        data = self._compute_end_time(data=data)

        data = self._combine_overlapping_rows(
            df=data,
            group_by_col="title",
            allowed_gap=pd.Timedelta("5 minutes") - pd.Timedelta(min_duration),
        )

        if min_duration:
            data = data[data[self.duration_col_name] > pd.Timedelta(min_duration)]

        data = data.sort_values(by="start_time")

        return data[
            [
                self.title_col_name,
                self.start_col_name,
                self.end_col_name,
                self.duration_col_name,
            ]
        ].reset_index(drop=True)
