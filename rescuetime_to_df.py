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
    distracting_titles = data[data["title"].str.contains("|".join(strs_to_match))][
        "title"
    ].unique()

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


def combine_events_with_same_title(data: pd.DataFrame) -> pd.DataFrame:
    """
    Combines any rows in a data frame where the distance between start_time and end_time is less than 1 minute.

    Args:
        data (pd.DataFrame): The data frame to modify.

    Returns:
        pd.DataFrame: The modified data frame.
    """
    # Combine any rows where the distance between start_time and end_time is less than 1 minute
    data = (
        data.groupby(["title", pd.Grouper(key="start_time", freq="1min")])
        .agg(
            {
                "duration": "sum",
                "duration_seconds": "sum",
                "end_time": "max",
            }
        )
        .reset_index()
    )

    # Drop duration columns
    data = data.drop(columns=["duration", "duration_seconds"])

    return data
