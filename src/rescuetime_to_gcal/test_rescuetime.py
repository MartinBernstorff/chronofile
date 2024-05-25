import datetime
import os

import pytz

from rescuetime_to_gcal.generic_event import GenericEvent
from rescuetime_to_gcal.source_event import BareEvent
from rescuetime_to_gcal.sources import rescuetime


def test_get_data():
    result = rescuetime.load(
        api_key=os.environ["RESCUETIME_API_KEY"],
        anchor_date=datetime.datetime.now(),
        lookback_window=datetime.timedelta(days=2),
        timezone=pytz.timezone("Europe/Copenhagen"),
    )
    assert isinstance(result[0], BareEvent)
