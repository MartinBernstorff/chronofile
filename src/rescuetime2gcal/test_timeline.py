import copy
import datetime
import random

import pytest
import pytz
from iterpy.arr import Arr

from rescuetime2gcal.test_event import FakeParsedEvent, MergeTestCase
from rescuetime2gcal.timeline import merge_within_window


@pytest.mark.parametrize(
    ("testcase"),
    [
        (MergeTestCase(name="No events", input=[], expected=[])),
        (
            MergeTestCase(
                name="Single event",
                input=[FakeParsedEvent(title="test")],
                expected=[FakeParsedEvent(title="test")],
            )
        ),
        (
            MergeTestCase(
                name="Dependent overlap",
                input=[
                    FakeParsedEvent(  # Event 1 start
                        start=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
                        end=datetime.datetime(2023, 1, 2, 0, 0, tzinfo=pytz.UTC),
                    ),
                    FakeParsedEvent(  # Merge with previous event
                        start=datetime.datetime(2023, 1, 2, 0, 0, tzinfo=pytz.UTC),
                        end=datetime.datetime(2023, 1, 3, 0, 0, tzinfo=pytz.UTC),
                    ),
                    FakeParsedEvent(  # Merge with previous event
                        start=datetime.datetime(2023, 1, 3, 0, 0, 0, tzinfo=pytz.UTC),
                        end=datetime.datetime(2023, 1, 4, 0, 0, 0, tzinfo=pytz.UTC),
                    ),
                ],
                expected=[
                    FakeParsedEvent(
                        start=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
                        end=datetime.datetime(2023, 1, 4, 0, 0, 0, tzinfo=pytz.UTC),
                    )
                ],
            )
        ),
        (
            MergeTestCase(
                name="No overlap",
                input=[
                    FakeParsedEvent(  # Event 1 start
                        start=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
                        end=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
                    ),
                    FakeParsedEvent(  # Merge with previous event
                        start=datetime.datetime(2024, 2, 1, 0, 0, tzinfo=pytz.UTC),
                        end=datetime.datetime(2025, 1, 1, 0, 0, tzinfo=pytz.UTC),
                    ),
                ],
                expected=[
                    FakeParsedEvent(
                        start=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
                        end=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
                    ),
                    FakeParsedEvent(
                        start=datetime.datetime(2024, 2, 1, 0, 0, tzinfo=pytz.UTC),
                        end=datetime.datetime(2025, 1, 1, 0, 0, tzinfo=pytz.UTC),
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
