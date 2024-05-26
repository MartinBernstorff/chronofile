import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

import pytest

from rescuetime_to_gcal import delta
from rescuetime_to_gcal.delta import EventChange, NewEvent, UpdateEvent
from rescuetime_to_gcal.test_preprocessing import FakeEvent

if TYPE_CHECKING:
    from rescuetime_to_gcal.preprocessing import ParsedEvent


@dataclass(frozen=True)
class ChangesetExample:
    intention: str
    true_events: Sequence["ParsedEvent"]
    mirror_events: Sequence["ParsedEvent"]
    then: Sequence[EventChange]


@pytest.mark.parametrize(
    ("e"),
    [
        ChangesetExample(
            "Matching events result in no diff",
            true_events=[FakeEvent()],
            mirror_events=[FakeEvent()],
            then=[],
        ),
        ChangesetExample(
            "Same start time but different end time result in update",
            true_events=[
                FakeEvent(
                    start=datetime.datetime(2023, 1, 1, 0, 0),
                    end=datetime.datetime(2023, 1, 1, 0, 1),
                )
            ],
            mirror_events=[
                FakeEvent(
                    start=datetime.datetime(2023, 1, 1, 0, 0),
                    end=datetime.datetime(2023, 1, 1, 0, 0),
                )
            ],
            then=[
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
            true_events=[FakeEvent()],
            mirror_events=[],
            then=[NewEvent(FakeEvent())],
        ),
        ChangesetExample(
            "Multiple existing events that match, updates final event by end time",
            true_events=[FakeEvent(end=datetime.datetime(2024, 1, 1, 0, 0))],
            mirror_events=[
                FakeEvent(id=0),
                FakeEvent(id=1, end=datetime.datetime(2021, 1, 1, 0, 1)),
            ],
            then=[UpdateEvent(FakeEvent(end=datetime.datetime(2024, 1, 1, 0, 0), id=1))],
        ),
    ],
    ids=lambda e: e.intention,
)  # TD Update ptp snippet to write a function with the right arguments, as well as dynamically generate the example name
def test_changeset(e: ChangesetExample):
    assert e.then == delta.changeset(e.true_events, e.mirror_events)
