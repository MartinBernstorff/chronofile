from typing import List, Union

import pandas as pd
import requests

# Replace with your own RescueTime API key
API_KEY = "B6300jX6LJHN6RU0uhZCQfOJEMrn2RfLIY0bkT_z"

# Set the URL for the API endpoint
URL = "https://www.rescuetime.com/anapi/data"


def get_from_rescuetime(
    perspective: str,
    resolution_time: str,
    restrict_begin: Union[str, None] = None,
    restrict_end: Union[str, None] = None,
) -> pd.DataFrame:
    """
    Makes an API request to the RescueTime API and returns the response as a pandas DataFrame.
    """
    # Set the parameters for the API request
    params = {
        "key": API_KEY,
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
    response = requests.get(URL, params=params).json()

    # Add column labels to the data
    column_labels = response["row_headers"]
    data = [dict(zip(column_labels, row)) for row in response["rows"]]

    # Convert the API response to a pandas DataFrame
    return pd.DataFrame(data)


def get_events_containing_str(
    data: pd.DataFrame, strs_to_match: List[str]
) -> pd.DataFrame:
    """
    Gets all rows in a data frame that have a title containing "youtube".

    Args:
        data (pd.DataFrame): The data frame to filter.

    Returns:
        pd.DataFrame: A data frame containing only rows with titles containing "youtube".
    """
    # Rename columns
    data = data.rename(
        columns={
            "Activity": "title",
            "Date": "start_time",
            "Time Spent (seconds)": "duration_seconds",
        }
    )

    # Get a list of unique titles that contain any element in the distracting_title list
    distracting_titles = data[
        data["title"].str.contains("|".join([s for s in strs_to_match]))
    ]["title"].unique()

    # Get all rows with "Activity" in the "distracting_titles" list
    data = data[data["title"].isin(distracting_titles)]

    return data


def compute_end_time(data: pd.DataFrame) -> pd.DataFrame:
    """
    Adds duration and end_time columns to a data frame.

    Args:
        data (pd.DataFrame): The data frame to modify.

    Returns:
        pd.DataFrame: The modified data frame.
    """
    # Convert the duration_seconds column to a timedelta column
    data["duration"] = pd.to_timedelta(data["duration_seconds"], unit="s")

    # Convert the start_time column to a datetime column
    data["start_time"] = pd.to_datetime(data["start_time"])

    # Create the end_time column
    data["end_time"] = data["start_time"] + data["duration"]

    return data


def combine_overlapping_rows(
    df: pd.DataFrame,
    start_col_name: str,
    end_col_name: str,
    group_by_col: str,
    duration_col_name: str,
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
                    row[end_col_name]
                    >= group_df.iloc[index + 1][start_col_name] - allowed_gap
                ):
                    group_df.at[index + 1, start_col_name] = group_df.iloc[index][
                        start_col_name
                    ]

                    group_df.at[index + 1, duration_col_name] = (
                        group_df.iloc[index][duration_col_name]
                        + group_df.iloc[index + 1][duration_col_name]
                    )

                    # Set the drop column to True for the row that will be dropped
                    group_df.at[index, "drop"] = True

            if "drop" in group_df.columns:
                group_df = group_df[group_df["drop"] != True]

            if n_before_combining == len(group_df):
                break

        df_elements += [group_df.apply(lambda x: x).reset_index(drop=True)]

    df = pd.concat(df_elements)
    df["duration_seconds"] = df["duration"].dt.total_seconds()

    return df
