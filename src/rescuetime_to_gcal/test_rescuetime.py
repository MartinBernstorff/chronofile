import os

from rescuetime_to_gcal.event import Event
from rescuetime_to_gcal.rescuetime import RescuetimeClient


def test_get_data():
    result = RescuetimeClient(api_key=os.environ["RESCUETIME_API_KEY"])._get_data(
        perspective="interval",
        resolution_time="minute",
        restrict_begin=None,
        restrict_end=None,
    )
    assert isinstance(result[0], Event)
