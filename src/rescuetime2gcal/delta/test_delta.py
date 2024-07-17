import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

import pytest
import pytz

from rescuetime2gcal import delta
from rescuetime2gcal.delta import EventChange, NewEvent, UpdateEvent
from rescuetime2gcal.test_preprocessing import FakeDestinationEvent, FakeParsedEvent

if TYPE_CHECKING:
    from rescuetime2gcal.preprocessing import DestinationEvent, ParsedEvent


@dataclass(frozen=True)
class ChangesetExample:
    intention: str
    parsed_events: Sequence["ParsedEvent"]
    destination_events: Sequence["DestinationEvent"]
    then: Sequence[EventChange]


@pytest.mark.parametrize(
    ("e"),
    [
        ChangesetExample(
            "Matching events result in no diff",
            parsed_events=[FakeParsedEvent()],
            destination_events=[FakeDestinationEvent()],
            then=[],
        ),
        ChangesetExample(
            "Same start time but different end time result in update",
            parsed_events=[
                FakeParsedEvent(
                    start=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
                    end=datetime.datetime(2023, 1, 1, 0, 1, tzinfo=pytz.UTC),
                )
            ],
            destination_events=[
                FakeDestinationEvent(
                    start=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
                    end=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
                )
            ],
            then=[
                UpdateEvent(
                    FakeDestinationEvent(
                        start=datetime.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.UTC),
                        end=datetime.datetime(2023, 1, 1, 0, 1, tzinfo=pytz.UTC),
                    )
                )
            ],
        ),
        ChangesetExample(
            "New event in source results in new event",
            parsed_events=[FakeParsedEvent()],
            destination_events=[],
            then=[NewEvent(FakeParsedEvent())],
        ),
        ChangesetExample(
            "Multiple existing events that match, updates final event by end time",
            parsed_events=[
                FakeParsedEvent(end=datetime.datetime(2024, 1, 1, 0, 0, tzinfo=pytz.UTC))
            ],
            destination_events=[
                FakeDestinationEvent(id="0"),
                FakeDestinationEvent(
                    id="1", end=datetime.datetime(2021, 1, 1, 0, 1, tzinfo=pytz.UTC)
                ),
            ],
            then=[
                UpdateEvent(
                    FakeDestinationEvent(
                        end=datetime.datetime(2024, 1, 1, 0, 0, tzinfo=pytz.UTC), id="1"
                    )
                )
            ],
        ),
    ],
    ids=lambda e: e.intention,
)
def test_changeset(e: ChangesetExample):
    assert e.then == delta.changeset(e.parsed_events, e.destination_events)


if __name__ == "__main__":
    pass
