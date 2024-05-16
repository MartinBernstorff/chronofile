import datetime
from dataclasses import dataclass
from typing import Sequence

import pytest

from rescuetime_to_gcal import delta
from rescuetime_to_gcal.delta.main import EventChange, UpdateEvent
from rescuetime_to_gcal.event import Event
from rescuetime_to_gcal.test_preprocessing_steps import FakeEvent


@dataclass(frozen=True)
class ChangesetExample:
    intention: str
    source_events: Sequence[Event]
    destination_events: Sequence[Event]
    result: Sequence[EventChange]


@pytest.mark.parametrize(
    ("example"),
    [
        ChangesetExample(
            "Matching events result in no diff",
            source_events=[FakeEvent()],
            destination_events=[FakeEvent()],
            result=[],
        ),
        ChangesetExample(
            "Same start time but different end time result in update",
            source_events=[
                FakeEvent(
                    start=datetime.datetime(2023, 1, 1, 0, 0),
                    end=datetime.datetime(2023, 1, 1, 0, 1),
                )
            ],
            destination_events=[
                FakeEvent(
                    start=datetime.datetime(2023, 1, 1, 0, 0),
                    end=datetime.datetime(2023, 1, 1, 0, 0),
                )
            ],
            result=[
                UpdateEvent(
                    FakeEvent(
                        start=datetime.datetime(2023, 1, 1, 0, 0),
                        end=datetime.datetime(2023, 1, 1, 0, 1),
                    )
                )
            ],
        ),
    ],
    ids=lambda e: e.intention,
)
def test_changeset(
    example: ChangesetExample,
):
    assert example.result == delta.changeset(
        example.source_events,
        example.destination_events,
    )
