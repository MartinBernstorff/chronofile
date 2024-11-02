import datetime
import os

import pytest
import pytz

from rescuetime2gcal.sources import rescuetime


def test_get_data():
    if os.environ.get("RESCUETIME_API_KEY") is None:
        pytest.skip("No RESCUETIME_API_KEY set")

    rescuetime.load(
        api_key=os.environ["RESCUETIME_API_KEY"],
        anchor_date=datetime.datetime.now(),
        lookback_window=datetime.timedelta(days=2),
        timezone=pytz.timezone("Europe/Copenhagen"),
    )
