import datetime
import logging
import os
from typing import TYPE_CHECKING, Sequence

from iterpy.arr import Arr

from rescuetime_to_gcal import gcal, rescuetime
from rescuetime_to_gcal._preprocessing import apply_metadata, merge_within_window
from rescuetime_to_gcal.config import config as cfg

if TYPE_CHECKING:
    from rescuetime_to_gcal.generic_event import Event
    from rescuetime_to_gcal.event_source import EventSource


def main(
    input_sources: Sequence["EventSource"],
    gcal_email: str,
    gcal_client_id: str,
    gcal_client_secret: str,
    gcal_refresh_token: str,
    dry_run: bool,
) -> Sequence["Event"]:
    input_data = Arr(input_sources).map(lambda f: f()).flatten()

    events = (
        input_data.filter(
            lambda e: not any(title.lower() in e.title for title in cfg.exclude_titles)
        )
        .filter(lambda e: e.duration > cfg.min_duration)
        .map(
            lambda e: apply_metadata(
                event=e, metadata=cfg.metadata_enrichment, category2emoji=cfg.category2emoji
            )
        )
        .groupby(lambda e: e.title)
        .map(lambda g: merge_within_window(g[1], merge_gap=cfg.merge_gap))
        .flatten()
        .to_list()
    )

    logging.debug("Syncing events to calendar")
    gcal.sync(
        client=gcal.GcalClient(
            calendar_id=gcal_email,
            client_id=gcal_client_id,
            client_secret=gcal_client_secret,
            refresh_token=gcal_refresh_token,
        ),
        source_events=events,
        dry_run=dry_run,
    )

    return events


if __name__ == "__main__":
    import coloredlogs

    coloredlogs.install(  # type: ignore
        level="INFO",
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    main(
        os.environ["RESCUETIME_API_KEY"],
        os.environ["GCAL_EMAIL"],
        os.environ["GCAL_CLIENT_ID"],
        os.environ["GCAL_CLIENT_SECRET"],
        os.environ["GCAL_REFRESH_TOKEN"],
        dry_run=False,
    )
