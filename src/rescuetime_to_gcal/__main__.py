import datetime
import logging
import os
from typing import TYPE_CHECKING, Sequence

from iterpy.arr import Arr

from rescuetime_to_gcal import gcal, rescuetime
from rescuetime_to_gcal._preprocessing import apply_metadata, merge_within_window
from rescuetime_to_gcal.config import config as cfg

if TYPE_CHECKING:
    from rescuetime_to_gcal.event import Event


def main(
    rescuetime_api_key: str,
    gcal_email: str,
    gcal_client_id: str,
    gcal_client_secret: str,
    gcal_refresh_token: str,
    dry_run: bool,
) -> Sequence["Event"]:
    rescuetime_data = rescuetime.load(
        api_key=rescuetime_api_key,
        anchor_date=datetime.datetime.now(),
        lookback_window=cfg.sync_window,
        timezone=cfg.rescuetime_timezone,
    )

    events = (
        Arr(rescuetime_data)
        .filter(lambda e: not any(title.lower() in e.title for title in cfg.exclude_titles))
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
    if not dry_run:
        gcal.sync(
            source_events=events,
            email=gcal_email,
            client_id=gcal_client_id,
            client_secret=gcal_client_secret,
            refresh_token=gcal_refresh_token,
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
