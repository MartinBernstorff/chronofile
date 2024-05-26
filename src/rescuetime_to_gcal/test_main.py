from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class Ex:
    given: str
    # Required setup

    then: str
    # What the expected result is


@pytest.mark.parametrize(
    ("example"),
    [
        Ex(should="1"),  # Example one
        Ex(should="2"),  # Example two
    ],
)
def test_sync_with_destination_id(e: Ex):
    """To update events at the destination, we need to pass along the event ID on the destination. Otherwise, how would we know which event to update?"""
    ...
