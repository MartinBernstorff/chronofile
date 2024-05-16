import datetime
import logging
import os

import devtools
from iterpy.arr import Arr

from rescuetime_to_gcal import gcal, rescuetime
from rescuetime_to_gcal._preprocessing import apply_metadata, merge_within_window
from rescuetime_to_gcal.config import config as cfg


def main(
    rescuetime_api_key: str,
    gcal_email: str,
    gcal_client_id: str,
    gcal_client_secret: str,
    gcal_refresh_token: str,
):
    rescuetime_data = rescuetime.load(
        api_key=rescuetime_api_key,
        anchor_date=datetime.datetime.now(),
        lookback_window=cfg.sync_window,
        timezone=cfg.rescuetime_timezone,
    )

    logging.debug(f"Rescuetime, got {devtools.debug.format(rescuetime_data)}")

    events = (
        Arr(rescuetime_data)
        .filter(
            lambda e: not any(
                [title.lower() in e.title for title in cfg.exclude_titles]
            )
        )
        .filter(lambda e: e.duration > cfg.min_duration)
        .map(
            lambda e: apply_metadata(
                event=e,
                metadata=cfg.metadata_enrichment,
                category2emoji=cfg.category2emoji,
            )
        )
        .groupby(lambda e: e.title)
        .map(lambda g: merge_within_window(g[1], merge_gap=cfg.merge_gap))
        .flatten()
        .to_list()
    )

    logging.debug("Syncing events to calendar")
    gcal.sync(
        source_events=events,
        email=gcal_email,
        client_id=gcal_client_id,
        client_secret=gcal_client_secret,
        refresh_token=gcal_refresh_token,
    )

    return events


if __name__ == "__main__":
    main(
        os.environ["RESCUETIME_API_KEY"],
        os.environ["GCAL_EMAIL"],
        os.environ["GCAL_CLIENT_ID"],
        os.environ["GCAL_CLIENT_SECRET"],
        os.environ["GCAL_REFRESH_TOKEN"],
    )
