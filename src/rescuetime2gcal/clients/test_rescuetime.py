import datetime
import os

import pytz
from rescuetime2gcal.clients import rescuetime
from rescuetime2gcal.source_event import BareEvent


def test_get_data():
    rescuetime.load(
        api_key=os.environ["RESCUETIME_API_KEY"],
        anchor_date=datetime.datetime.now(),
        lookback_window=datetime.timedelta(days=2),
        timezone=pytz.timezone("Europe/Copenhagen"),
    )
