import datetime
import os

from rescuetime_to_gcal import activitywatch
from rescuetime_to_gcal.activitywatch import load_afk_events, load_window_titles


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


def test_load_afk_events():
    events = load_afk_events(bucket_id="aw-watcher-afk_d45830", date=datetime.datetime.now())
    assert len(events) > 0


def test_load_all():
    events = activitywatch.load_all_events(date=datetime.datetime.now())
    assert len(events) > 0
