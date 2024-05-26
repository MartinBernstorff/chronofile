import datetime
import os

import pytest
from rescuetime_to_gcal.clients import activitywatch


@pytest.fixture(autouse=True)
def _skip_if_no_base_url():  # type: ignore
    if os.environ.get("ACTIVITYWATCH_BASE_URL") is None:
        pytest.skip("No ACTIVITYWATCH_BASE_URL set")


def test_load_window_titles():
    events = activitywatch.load_window_titles(
        bucket_id="aw-watcher-window_d45830", date=datetime.datetime.now()
    )
    assert len(events) > 0


def test_load_url_events():
    events = activitywatch.load_url_events(
        bucket_id="aw-watcher-web-chrome", date=datetime.datetime.now()
    )
    assert len(events) > 0


def test_load_all():
    events = activitywatch.load_all_events(date=datetime.datetime.now())
    assert len(events) > 0
