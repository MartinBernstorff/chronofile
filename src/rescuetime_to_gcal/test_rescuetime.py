import os

from rescuetime_to_gcal.rescuetime import Rescuetime


def test_get_data():
    result = Rescuetime(api_key=os.environ["RESCUETIME_API_KEY"])._get_data()
    assert isinstance(result, list)
