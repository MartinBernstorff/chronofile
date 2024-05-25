import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

import pytest

from rescuetime_to_gcal import delta
from rescuetime_to_gcal.delta import EventChange, NewEvent, UpdateEvent
from rescuetime_to_gcal.test_preprocessing import FakeEvent

if TYPE_CHECKING:
    from rescuetime_to_gcal.generic_event import Event


@dataclass(frozen=True)
class ChangesetExample:
    intention: str
    source_events: Sequence["Event"]
    destination_events: Sequence["Event"]
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
        ChangesetExample(
            "New event in source results in new event",
            source_events=[FakeEvent()],
            destination_events=[],
            result=[NewEvent(FakeEvent())],
        ),
    ],
    ids=lambda e: e.intention,
)
def test_changeset(example: ChangesetExample):
    assert example.result == delta.changeset(example.source_events, example.destination_events)
