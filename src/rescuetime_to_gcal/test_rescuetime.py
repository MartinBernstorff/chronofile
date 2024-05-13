import datetime
import os

from rescuetime_to_gcal import rescuetime
from rescuetime_to_gcal.event import Event


def test_get_data():
    result = rescuetime.load(
        api_key=os.environ["RESCUETIME_API_KEY"],
        anchor_date=datetime.datetime.now(),
        lookback_window=datetime.timedelta(days=2),
    )
    assert isinstance(result[0], Event)
