import datetime
import os

import pytz
from rescuetime_to_gcal.clients import rescuetime
from rescuetime_to_gcal.event import BareEvent


def test_get_data():
    result = rescuetime.load(
        api_key=os.environ["RESCUETIME_API_KEY"],
        anchor_date=datetime.datetime.now(),
        lookback_window=datetime.timedelta(days=2),
        timezone=pytz.timezone("Europe/Copenhagen"),
    )
    assert isinstance(result[0], BareEvent)
