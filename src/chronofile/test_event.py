import datetime
from dataclasses import dataclass

import pytest
import pytz

from chronofile.event import ChronofileEvent, DestinationEvent, SourceEvent, URLEvent, _parse_event


class FakeParsedEvent(ChronofileEvent):
    title: str = "fake title"
    start: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    end: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    source_event: SourceEvent | None = None

    def __post_init__(self):
        self.start = self.start.astimezone(pytz.UTC)
        self.end = self.end.astimezone(pytz.UTC)


class FakeDestinationEvent(DestinationEvent):
    title: str = "fake title"
    start: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    end: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    id: str = "0"
    source_event: "SourceEvent | None" = None


@dataclass
class MergeTestCase:
    name: str
    input: list[ChronofileEvent]
    expected: list[ChronofileEvent]


class FakeURLEvent(URLEvent):
    url: str = "https://github.com/MartinBernstorff/chronofile/pull/39"
    url_title: str
    start: datetime.datetime = datetime.datetime(2023, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    duration: datetime.timedelta = datetime.timedelta(seconds=0)


@dataclass(frozen=True)
class PEx:
    given: "SourceEvent"
    then: ChronofileEvent


@pytest.mark.parametrize(
    ("ex"),
    [
        PEx(
            FakeURLEvent(
                url="https://github.com/MartinBernstorff/chronofile/pull/39",
                url_title="github_with_subdomain.com",
            ),
            FakeParsedEvent(title="GitHub: MartinBernstorff/chronofile"),
        ),
        PEx(
            FakeURLEvent(url="https://github.com/", url_title="GitHub without subdomain"),
            FakeParsedEvent(title="GitHub without subdomain"),
        ),
    ],
    ids=lambda e: e.given.url,
)
def test_parse_event_titles(ex: PEx):
    assert ex.then.title == _parse_event(ex.given).title
