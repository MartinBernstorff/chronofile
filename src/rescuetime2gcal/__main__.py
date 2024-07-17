import datetime
import logging
from typing import TYPE_CHECKING, Sequence

import devtools
from iterpy.arr import Arr

from rescuetime2gcal import delta
from rescuetime2gcal.config import config as cfg
from rescuetime2gcal.preprocessing import (
    DestinationEvent,
    merge_within_window,
    parse_events,
)

if TYPE_CHECKING:
    from rescuetime2gcal.clients.event_source import EventSource
    from rescuetime2gcal.clients.gcal.client import DestinationClient
    from rescuetime2gcal.source_event import SourceEvent

log = logging.getLogger(__name__)


def main(
    input_clients: Sequence["EventSource"],
    destination_client: "DestinationClient",
    dry_run: bool,
) -> None:
    input_events = Arr(input_clients).map(lambda f: f()).flatten().to_list()

    destination_events = destination_client.get_events(
        start=min([event.start for event in input_events]),
        end=datetime.datetime.now(tz=input_events[0].start.tzinfo),
    )

    changes = pipeline(source_events=input_events, destination_events=destination_events)

    logging.info(f"Changes to be made {devtools.debug.format(changes)}")

    if not dry_run:
        log.info("Dry-run is false, syncing changes")
        for change in changes:
            match change:
                case delta.NewEvent():
                    destination_client.add_event(change.event)
                case delta.UpdateEvent():
                    destination_client.update_event(change.event)
    else:
        log.info("Dry-run enabled, skipping sync")


def pipeline(
    source_events: Sequence["SourceEvent"],
    destination_events: Sequence["DestinationEvent"],
) -> Sequence[delta.EventChange]:
    sufficient_length_events = Arr(source_events).filter(
        lambda e: e.duration > cfg.min_duration
    )

    parsed_events = sufficient_length_events.map(
        lambda e: parse_events(
            event=e, metadata=cfg.metadata_enrichment, category2emoji=cfg.category2emoji
        )
    )

    filtered_by_title = parsed_events.filter(
        lambda e: not any(
            excluded_title.lower() in e.title.lower()
            for excluded_title in cfg.exclude_titles
        )
    )

    merged_within_gap = (
        filtered_by_title.groupby(lambda e: e.title)
        .map(lambda g: merge_within_window(g[1], merge_gap=cfg.merge_gap))
        .flatten()
        .to_list()
    )

    changeset = delta.changeset(merged_within_gap, destination_events)

    return changeset
