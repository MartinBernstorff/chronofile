import copy
import datetime
import random
from dataclasses import dataclass

import pytest
import pytz
from iterpy.arr import Arr

from rescuetime2gcal.preprocessing import (
    DestinationEvent,
    ParsedEvent,
    filter_by_title,
    merge_within_window,
)


class FakeParsedEvent(ParsedEvent):
    title: str = "fake title"
    start: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    end: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)

    def __post_init__(self):
        self.start = self.start.astimezone(pytz.UTC)
        self.end = self.end.astimezone(pytz.UTC)


class FakeDestinationEvent(DestinationEvent):
    title: str = "fake title"
    start: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    end: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    id: str = "0"


def test_filter_by_title():
    events = [
        FakeParsedEvent(title="tes"),
        FakeParsedEvent(title="test2"),
        FakeParsedEvent(title="test3"),
    ]
    filtered_events = filter_by_title(data=events, strs_to_match=["test"])
    assert len(filtered_events) == 1
    assert filtered_events[0].title == "tes"


@dataclass
class MergeTestCase:
    name: str
    input: list[ParsedEvent]
    expected: list[ParsedEvent]


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
