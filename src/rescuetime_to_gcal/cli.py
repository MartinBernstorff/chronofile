import logging
from typing import Annotated

import coloredlogs
import pandas as pd
import typer
from iterpy.arr import Arr

from rescuetime_to_gcal import gcal
from rescuetime_to_gcal.config import config as cfg
from rescuetime_to_gcal.gcal.auth import print_refresh_token
from rescuetime_to_gcal.processing_steps import apply_metadata, merge_within_window
from rescuetime_to_gcal.rescuetime import RescuetimeClient

log = coloredlogs.install(  # type: ignore
    level="INFO",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

app = typer.Typer()


@app.command(name="auth")
def auth(
    gcal_client_id: Annotated[
        str,
        typer.Argument(envvar="GCAL_CLIENT_ID"),
    ],
    gcal_client_secret: Annotated[
        str,
        typer.Argument(envvar="GCAL_CLIENT_SECRET"),
    ],
):
    logging.info("Getting refresh token")
    print_refresh_token(gcal_client_id, gcal_client_secret)


@app.command(name="sync")
def cli(
    rescuetime_api_key: Annotated[str, typer.Argument(envvar="RESCUETIME_API_KEY")],
    gcal_email: Annotated[str, typer.Argument(envvar="GCAL_EMAIL")],
    gcal_client_id: Annotated[
        str,
        typer.Argument(envvar="GCAL_CLIENT_ID"),
    ],
    gcal_client_secret: Annotated[
        str,
        typer.Argument(envvar="GCAL_CLIENT_SECRET"),
    ],
    gcal_refresh_token: Annotated[
        str,
        typer.Argument(envvar="GCAL_REFRESH_TOKEN"),
    ],
):
    logging.info("Starting sync")
    rescuetime_data = RescuetimeClient(api_key=rescuetime_api_key).pull(
        anchor_date=pd.Timestamp.today(),
        lookback_window=cfg.sync_window,
    )

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
    )

    merged_events = merge_within_window(
        rescuetime_data, lambda e: e.title, cfg.merge_gap
    )

    logging.info("Syncing events to calendar")
    gcal.sync(
        events=merged_events,
        email=gcal_email,
        client_id=gcal_client_id,
        client_secret=gcal_client_secret,
        refresh_token=gcal_refresh_token,
    )

    logging.info(f"Sync complete, synced {events.count()} events")


if __name__ == "__main__":
    app()
