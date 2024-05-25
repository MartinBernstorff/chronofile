import datetime
import os

import pytz

from rescuetime_to_gcal import rescuetime
from rescuetime_to_gcal.generic_event import GenericEvent


def test_get_data():
    result = rescuetime.load(
        api_key=os.environ["RESCUETIME_API_KEY"],
        anchor_date=datetime.datetime.now(),
        lookback_window=datetime.timedelta(days=2),
        timezone=pytz.timezone("Europe/Copenhagen"),
    )
    assert isinstance(result[0], GenericEvent)
