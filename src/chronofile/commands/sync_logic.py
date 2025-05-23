import datetime
import logging
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Callable, Mapping, Optional, Sequence

import coloredlogs
from iterpy.arr import Arr

import chronofile.diff as diff
from chronofile.event import DestinationEvent, SourceEvent, WindowTitleEvent, hydrate_event
from chronofile.sources import activitywatch
from chronofile.timeline import merge_within_window

if TYPE_CHECKING:
    from chronofile.config import RecordCategory, RecordMetadata

coloredlogs.install(  # type: ignore
    level="INFO",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

log = logging.getLogger(__name__)


def try_activitywatch(
    activitywatch_base_url: str | None,
) -> Optional[Callable[[], Sequence[SourceEvent]]]:
    if activitywatch_base_url:
        if not activitywatch_base_url.endswith("/"):
            activitywatch_base_url += "/"
        return partial(
            activitywatch.load_all_events,
            date=datetime.datetime.now(),
            base_url=activitywatch_base_url,
        )
    return None


@dataclass(frozen=True)
class DeduplicatedGroup:
    keeper: "DestinationEvent"
    duplicates: Sequence["DestinationEvent"]

    @staticmethod
    def _from_event_group(event_group: Sequence["DestinationEvent"]) -> "DeduplicatedGroup":
        if len(event_group) > 1:
            return DeduplicatedGroup(keeper=event_group[0], duplicates=event_group[1:])
        return DeduplicatedGroup(keeper=event_group[0], duplicates=[])


def pipeline(  # noqa: D417
    source_events: Sequence["SourceEvent"],
    destination_events: Sequence["DestinationEvent"],
    min_duration: "datetime.timedelta",
    category2emoji: Mapping["RecordCategory", str],
    exclude_titles: Sequence[str],
    merge_gap: "datetime.timedelta",
    metadata_enrichment: Sequence["RecordMetadata"],
    exclude_apps: Sequence[str],
) -> Sequence[diff.EventChange]:
    """Event processing without I/O. Separating this from I/O makes debugging and testing easier.

    Args:
        source_events: Source events to process
        destination_events: Destination events to process
        ... [See the Config object for the rest of the arguments]
    """

    # Preprocess the source events
    sufficient_length_events = Arr(source_events).filter(lambda e: e.duration > min_duration)

    without_excluded_apps = sufficient_length_events.filter(
        lambda e: not any(excluded_app.lower() in e.app.lower() for excluded_app in exclude_apps)
        if isinstance(e, WindowTitleEvent)
        else True
    )

    parsed_events = without_excluded_apps.map(
        lambda e: hydrate_event(
            event=e, metadata=metadata_enrichment, category2emoji=category2emoji
        )
    )

    filtered_by_title = parsed_events.filter(
        lambda e: not any(
            excluded_title.lower() in e.title.lower() for excluded_title in exclude_titles
        )
    )

    merged_within_gap = (
        filtered_by_title.groupby(lambda e: e.title)
        .map(lambda g: merge_within_window(g[1], merge_gap=merge_gap))
        .flatten()
        .to_list()
    )

    # Deduplicate destination events
    deduplicated_destination_events = (
        Arr(destination_events)
        .groupby(lambda e: e.identity)
        .map(lambda g: DeduplicatedGroup._from_event_group(g[1]))
    )
    destination_keepers = deduplicated_destination_events.map(lambda g: g.keeper).to_list()
    destination_duplicates = (
        deduplicated_destination_events.map(lambda g: list(g.duplicates)).flatten().to_list()
    )

    # Calculate the delta
    changeset = diff.diff(merged_within_gap, destination_keepers)

    return [*changeset, *[diff.DeleteEvent(event=e) for e in destination_duplicates]]
