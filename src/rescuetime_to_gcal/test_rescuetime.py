import datetime
import os

from rescuetime_to_gcal.rescuetime import Event, Rescuetime


def test_get_data():
    result = Rescuetime(api_key=os.environ["RESCUETIME_API_KEY"])._get_data(
        api_key=os.environ["RESCUETIME_API_KEY"],
        url="https://www.rescuetime.com/anapi/data",
        perspective="interval",
        resolution_time="minute",
        restrict_begin=None,
        restrict_end=None,
    )
    assert isinstance(result[0], Event)


def test_filter_by_title():
    events = [
        Event(
            title="tes",
            start=datetime.datetime(2023, 1, 1, 0, 0),
            duration=datetime.timedelta(seconds=10),
        ),
        Event(
            title="test2",
            start=datetime.datetime(2023, 1, 1, 0, 0),
            duration=datetime.timedelta(seconds=10),
        ),
        Event(
            title="test3",
            start=datetime.datetime(2023, 1, 1, 0, 0),
            duration=datetime.timedelta(seconds=10),
        ),
    ]
    filtered_events = Rescuetime._filter_by_title(data=events, strs_to_match=["test"])
    assert len(filtered_events) == 1
    assert filtered_events[0].title == "tes"


def test_merge_events_within_window():
    events = [
        Event(
            title="tes",
            start=datetime.datetime(2023, 1, 1, 0, 0),
            duration=datetime.timedelta(seconds=10),
        ),
        Event(
            title="test2",
            start=datetime.datetime(2023, 1, 1, 0, 0),
            duration=datetime.timedelta(seconds=10),
        ),
        Event(
            title="test3",
            start=datetime.datetime(2023, 1, 1, 0, 0),
            duration=datetime.timedelta(seconds=10),
        ),
    ]

    combined = Rescuetime._merge_events_within_window()
    # * Finish test here.
    # Missing is:
    # - Shuffle events
    # - Check that within merge gap is merged for the same title
    # - No merging outside merge gap
    # - No merging between event titles
    # - If events are overlapping, end date is the highest end date, not the durations
