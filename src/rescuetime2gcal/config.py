import datetime
import pathlib
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

import pydantic
import pytz
import toml


class RecordCategory(Enum):
    BROWSING = "Browsing"
    COMMUNICATING = "Communicating"
    GAMING = "Gaming"
    PROGRAMMING = "Programming"
    PLANNING = "Planning"
    READING = "Reading"
    REFERENCE = "Reference"
    SOUND = "Sound"
    WRITING = "Writing"

    def __repr__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RecordMetadata:
    title_matcher: Sequence[
        str
    ]  # If a title has a substring matching any of these strings, it will have the metadata applied
    category: RecordCategory
    prettified_title: str | None = None

    def __repr__(self) -> str:
        return f"{self.category}: {self.title_matcher} -> {self.prettified_title}"


class Config(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    rescuetime_timezone: pytz.tzinfo.BaseTzInfo
    # Timezone of the rescuetime user. Is not provided by the API, so must be provided manually.

    sync_window: datetime.timedelta
    # How far back from the current date to look for events

    exclude_titles: Sequence[str]
    # Exclude events who contain these titles. Case insensitive.

    exclude_apps: Sequence[str]
    # Exclude events from these apps

    merge_gap: datetime.timedelta
    # If events have the same title and the first event's end time is within this gap, combine the events

    min_duration: datetime.timedelta
    # Exclude events shorter than this

    metadata_enrichment: Sequence[RecordMetadata]
    # Enrich events with metadata, e.g. emoji selection

    category2emoji: Mapping[RecordCategory, str]
    # Map categories to emoji

    @staticmethod
    def from_toml(path: str) -> "Config":
        values = toml.load(pathlib.Path(path))

        return Config(
            rescuetime_timezone=pytz.timezone(values.get("rescuetime_timezone", "")),
            sync_window=datetime.timedelta(seconds=values.get("sync_window", 60 * 60 * 5)),
            exclude_titles=values.get("exclude_titles", ""),
            merge_gap=datetime.timedelta(seconds=values.get("merge_gap", 60 * 10)),
            min_duration=datetime.timedelta(seconds=values.get("min_duration", 60 * 5)),
            category2emoji={
                RecordCategory(k): v for k, v in values.get("category2emoji", "").items()
            },
            exclude_apps=values.get("exclude_apps", []),
            metadata_enrichment=values.get("metadata_enrichment", ""),
        )
