"""Takes a pandas dataframe and converts it to the relevant type for gcal"""
from typing import List

import pandas as pd
from gcsa.event import Event


def df_to_gcsa_events(df: pd.DataFrame) -> List[Event]:
    """Takes a pandas dataframe and converts it to the relevant type for gcal"""
    # Iterate over the rows of the dataframe
    events = []

    for _, row in df.iterrows():
        events.append(
            Event(
                summary=row["title"],
                start=pd.Timestamp(row["start_time"], tz="Europe/Copenhagen"),
                end=pd.Timestamp(row["end_time"], tz="Europe/Copenhagen"),
                timezone="Europe/Copenhagen",
                description=(row["category"]),
            )
        )

    return events
