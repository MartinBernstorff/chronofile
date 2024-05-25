import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

import pydantic
import pytz


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


@dataclass(frozen=True)
class RecordMetadata:
    title_matcher: Sequence[
        str
    ]  # If a title has a substring matching any of these strings, it will have the metadata applied
    prettified_title: str | None
    category: RecordCategory


class Config(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    rescuetime_timezone: pytz.tzinfo.BaseTzInfo
    # Timezone of the rescuetime user. Is not provided by the API, so must be provided manually.

    sync_window: datetime.timedelta
    # How far back from the current date to look for events

    exclude_titles: Sequence[str]
    # Exclude events who contain these titles. Case insensitive.

    merge_gap: datetime.timedelta
    # If events have the same title and the first event's end time is within this gap, combine the events

    min_duration: datetime.timedelta
    # Exclude events shorter than this

    metadata_enrichment: Sequence[RecordMetadata]
    # Enrich events with metadata, e.g. emoji selection

    category2emoji: Mapping[RecordCategory, str]
    # Map categories to emoji


config = Config(
    rescuetime_timezone=pytz.timezone("Europe/Copenhagen"),
    sync_window=datetime.timedelta(days=0.5),
    exclude_titles=[
        "newtab",
        "raycast",
        "chrome",
        "system settings",
        "localhost",
        "finder",
        "google",
        "safari",
    ],
    merge_gap=datetime.timedelta(minutes=15),
    min_duration=datetime.timedelta(seconds=5),
    category2emoji={
        RecordCategory.BROWSING: "🔥",
        RecordCategory.COMMUNICATING: "️☎️",
        RecordCategory.GAMING: "🎮",
        RecordCategory.PROGRAMMING: "🤖",
        RecordCategory.PLANNING: "🗺️",
        RecordCategory.SOUND: "🎵",
        RecordCategory.READING: "📗",
        RecordCategory.REFERENCE: "📚",
        RecordCategory.WRITING: "✍️",
    },
    metadata_enrichment=[
        RecordMetadata(
            title_matcher=["workflowy"], prettified_title=None, category=RecordCategory.PLANNING
        ),
        RecordMetadata(
            title_matcher=["tldraw"], prettified_title="TLDraw", category=RecordCategory.PLANNING
        ),
        RecordMetadata(
            title_matcher=["2718"], prettified_title="Marimo", category=RecordCategory.PROGRAMMING
        ),
        RecordMetadata(
            title_matcher=["skim"], prettified_title="Skim", category=RecordCategory.READING
        ),
        RecordMetadata(
            title_matcher=["dr.dk"], prettified_title="DR", category=RecordCategory.BROWSING
        ),
        RecordMetadata(
            title_matcher=["citrix"], prettified_title="Citrix", category=RecordCategory.PROGRAMMING
        ),
        RecordMetadata(
            title_matcher=["facebook"],
            prettified_title="Facebook",
            category=RecordCategory.BROWSING,
        ),
        RecordMetadata(
            title_matcher=["github"], prettified_title=None, category=RecordCategory.PROGRAMMING
        ),
        RecordMetadata(
            title_matcher=["hey"], prettified_title="Hey", category=RecordCategory.BROWSING
        ),
        RecordMetadata(
            title_matcher=["linkedin"],
            prettified_title="LinkedIn",
            category=RecordCategory.BROWSING,
        ),
        RecordMetadata(
            title_matcher=["Notes"], prettified_title="Notes", category=RecordCategory.PLANNING
        ),
        RecordMetadata(
            title_matcher=["mail"], prettified_title="Mail", category=RecordCategory.COMMUNICATING
        ),
        RecordMetadata(
            title_matcher=["macrumors"],
            prettified_title="Browsing",
            category=RecordCategory.BROWSING,
        ),
        RecordMetadata(
            title_matcher=["reddit"], prettified_title="Reddit", category=RecordCategory.BROWSING
        ),
        RecordMetadata(
            title_matcher=["slack"], prettified_title="Slack", category=RecordCategory.COMMUNICATING
        ),
        RecordMetadata(
            title_matcher=["star realms"],
            prettified_title="Star Realms",
            category=RecordCategory.GAMING,
        ),
        RecordMetadata(
            title_matcher=["stackoverflow"],
            prettified_title="Stack Overflow",
            category=RecordCategory.PROGRAMMING,
        ),
        RecordMetadata(
            title_matcher=["twitter"], prettified_title="Browsing", category=RecordCategory.BROWSING
        ),
        RecordMetadata(
            title_matcher=["wandb.ai"],
            prettified_title="Programming",
            category=RecordCategory.PROGRAMMING,
        ),
        RecordMetadata(
            title_matcher=["spotify"], prettified_title="Spotify", category=RecordCategory.SOUND
        ),
        RecordMetadata(
            title_matcher=["omnivore"], prettified_title="Omnivore", category=RecordCategory.READING
        ),
        RecordMetadata(
            title_matcher=["twitter"], prettified_title="Twitter", category=RecordCategory.BROWSING
        ),
        RecordMetadata(
            title_matcher=["Word"], prettified_title="Word", category=RecordCategory.WRITING
        ),
        RecordMetadata(
            title_matcher=["Calendar"],
            prettified_title="Calendar",
            category=RecordCategory.PLANNING,
        ),
        RecordMetadata(
            title_matcher=["Obsidian"], prettified_title="Obsidian", category=RecordCategory.WRITING
        ),
        RecordMetadata(
            title_matcher=["Docs"], prettified_title=None, category=RecordCategory.PROGRAMMING
        ),
        RecordMetadata(
            title_matcher=["Alacritty"],
            prettified_title="Alacritty",
            category=RecordCategory.PROGRAMMING,
        ),
        RecordMetadata(
            title_matcher=["Orbstack"],
            prettified_title="Orbstack",
            category=RecordCategory.PROGRAMMING,
        ),
    ],
)
