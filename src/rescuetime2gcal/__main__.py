import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

import devtools
from iterpy.arr import Arr

from rescuetime2gcal import delta
from rescuetime2gcal.config import config as cfg
from rescuetime2gcal.preprocessing import DestinationEvent, merge_within_window, parse_events

if TYPE_CHECKING:
    from rescuetime2gcal.clients.event_source import EventSource
    from rescuetime2gcal.clients.gcal.client import DestinationClient
    from rescuetime2gcal.source_event import SourceEvent

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeduplicatedGroup:
    keeper: DestinationEvent
    duplicates: Sequence[DestinationEvent]

    @staticmethod
    def _from_event_group(event_group: Sequence[DestinationEvent]) -> "DeduplicatedGroup":
        if len(event_group) > 1:
            return DeduplicatedGroup(keeper=event_group[0], duplicates=event_group[1:])
        return DeduplicatedGroup(keeper=event_group[0], duplicates=[])


def main(
    input_clients: Sequence["EventSource"], destination_client: "DestinationClient", dry_run: bool
) -> None:
    input_events = Arr(input_clients).map(lambda f: f()).flatten().to_list()

    first_start = min([event.start for event in input_events])
    last_start = max([event.start for event in input_events])

    destination_events = destination_client.get_events(
        start=first_start, end=last_start + max([event.duration for event in input_events])
    )

    changes = _pipeline(source_events=input_events, destination_events=destination_events)

    logging.info(f"Changes to be made {devtools.debug.format(changes)}")

    if not dry_run:
        log.info("Dry-run is false, syncing changes")
        for change in changes:
            match change:
                case delta.NewEvent():
                    destination_client.add_event(change.event)
                case delta.UpdateEvent():
                    destination_client.update_event(change.event)
                case delta.DeleteEvent():
                    destination_client.delete_event(change.event)
    else:
        log.info("Dry-run enabled, skipping sync")


def _pipeline(
    source_events: Sequence["SourceEvent"], destination_events: Sequence["DestinationEvent"]
) -> Sequence[delta.EventChange]:
    """Event processing without I/O. Separating this from I/O makes debugging and testing easier."""

    # Preprocess the source events
    sufficient_length_events = Arr(source_events).filter(lambda e: e.duration > cfg.min_duration)

    parsed_events = sufficient_length_events.map(
        lambda e: parse_events(
            event=e, metadata=cfg.metadata_enrichment, category2emoji=cfg.category2emoji
        )
    )

    filtered_by_title = parsed_events.filter(
        lambda e: not any(
            excluded_title.lower() in e.title.lower() for excluded_title in cfg.exclude_titles
        )
    )

    merged_within_gap = (
        filtered_by_title.groupby(lambda e: e.title)
        .map(lambda g: merge_within_window(g[1], merge_gap=cfg.merge_gap))
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
    changeset = delta.changeset(merged_within_gap, destination_keepers)

    return [*changeset, *[delta.DeleteEvent(event=e) for e in destination_duplicates]]
