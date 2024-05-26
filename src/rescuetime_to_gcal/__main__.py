import datetime
import logging
from typing import TYPE_CHECKING, Sequence

import devtools
from iterpy.arr import Arr

from rescuetime_to_gcal import delta
from rescuetime_to_gcal.clients import gcal
from rescuetime_to_gcal.config import config as cfg
from rescuetime_to_gcal.preprocessing import DestinationEvent, apply_metadata, merge_within_window

if TYPE_CHECKING:
    from rescuetime_to_gcal.clients.event_source import EventSource
    from rescuetime_to_gcal.clients.gcal.client import DestinationClient
    from rescuetime_to_gcal.event import SourceEvent

log = logging.getLogger(__name__)


def main(
    input_clients: Sequence["EventSource"], destination_client: "DestinationClient", dry_run: bool
) -> None:
    input_events = Arr(input_clients).map(lambda f: f()).flatten().to_list()
    destination_events = destination_client.get_events(
        start=min([event.start for event in input_events]), end=datetime.datetime.now()
    )

    changes = pipeline(source_events=input_events, presentation_events=destination_events)

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
    source_events: Sequence["SourceEvent"], presentation_events: Sequence["DestinationEvent"]
) -> Sequence[delta.EventChange]:
    sufficient_length_events = Arr(source_events).filter(lambda e: e.duration > cfg.min_duration)

    events_with_metadata = sufficient_length_events.map(
        lambda e: apply_metadata(
            event=e, metadata=cfg.metadata_enrichment, category2emoji=cfg.category2emoji
        )
    )

    filtered_by_title = events_with_metadata.filter(
        lambda e: not any(
            excluded_title.lower() in e.title.lower() for excluded_title in cfg.exclude_titles
        )
    )

    merged_source_events = (
        filtered_by_title.groupby(lambda e: e.title)
        .map(lambda g: merge_within_window(g[1], merge_gap=cfg.merge_gap))
        .flatten()
        .to_list()
    )

    changeset = delta.changeset(merged_source_events, presentation_events)

    return changeset
