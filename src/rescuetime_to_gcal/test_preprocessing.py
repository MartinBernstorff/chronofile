import copy
import datetime
import random
from dataclasses import dataclass

import pytest
from iterpy.arr import Arr

from rescuetime_to_gcal.generic_event import GenericEvent
from rescuetime_to_gcal.preprocessing import filter_by_title, merge_within_window, parse_url_event
from rescuetime_to_gcal.source_event import URLEvent


class FakeEvent(GenericEvent):
    title: str = "fake title"
    start: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0)
    end: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0)


def test_filter_by_title():
    events = [FakeEvent(title="tes"), FakeEvent(title="test2"), FakeEvent(title="test3")]
    filtered_events = filter_by_title(data=events, strs_to_match=["test"])
    assert len(filtered_events) == 1
    assert filtered_events[0].title == "tes"


@dataclass
class MergeTestCase:
    name: str
    input: list[GenericEvent]
    expected: list[GenericEvent]


@pytest.mark.parametrize(
    ("testcase"),
    [
        (MergeTestCase(name="No events", input=[], expected=[])),
        (
            MergeTestCase(
                name="Single event",
                input=[FakeEvent(title="test")],
                expected=[FakeEvent(title="test")],
            )
        ),
        (
            MergeTestCase(
                name="Dependent overlap",
                input=[
                    FakeEvent(  # Event 1 start
                        start=datetime.datetime(2023, 1, 1, 0, 0),
                        end=datetime.datetime(2023, 1, 2, 0, 0),
                    ),
                    FakeEvent(  # Merge with previous event
                        start=datetime.datetime(2023, 1, 2, 0, 0),
                        end=datetime.datetime(2023, 1, 3, 0, 0),
                    ),
                    FakeEvent(  # Merge with previous event
                        start=datetime.datetime(2023, 1, 3, 0, 0, 0),
                        end=datetime.datetime(2023, 1, 4, 0, 0, 0),
                    ),
                ],
                expected=[
                    FakeEvent(
                        start=datetime.datetime(2023, 1, 1, 0, 0),
                        end=datetime.datetime(2023, 1, 4, 0, 0, 0),
                    )
                ],
            )
        ),
        (
            MergeTestCase(
                name="No overlap",
                input=[
                    FakeEvent(  # Event 1 start
                        start=datetime.datetime(2023, 1, 1, 0, 0),
                        end=datetime.datetime(2023, 1, 1, 0, 0),
                    ),
                    FakeEvent(  # Merge with previous event
                        start=datetime.datetime(2024, 2, 1, 0, 0),
                        end=datetime.datetime(2025, 1, 1, 0, 0),
                    ),
                ],
                expected=[
                    FakeEvent(
                        start=datetime.datetime(2023, 1, 1, 0, 0),
                        end=datetime.datetime(2023, 1, 1, 0, 0),
                    ),
                    FakeEvent(
                        start=datetime.datetime(2024, 2, 1, 0, 0),
                        end=datetime.datetime(2025, 1, 1, 0, 0),
                    ),
                ],
            )
        ),
    ],
)
def test_merge_events_within_window(testcase: MergeTestCase):
    for i in range(10):
        random.seed(i)
        shuffled_events = copy.deepcopy(testcase.input)
        random.shuffle(shuffled_events)
        # Shuffle events to ensure the test is order-independent

        combined = (
            Arr(shuffled_events)
            .groupby(lambda e: e.title)
            .map(lambda g: merge_within_window(g[1], merge_gap=datetime.timedelta(days=1)))
            .flatten()
        ).to_list()

        output = sorted(combined, key=lambda e: e.start)
        assert "\n".join(str(e) for e in output) == "\n".join(str(e) for e in testcase.expected)
