import logging
from typing import Annotated

import coloredlogs
import pandas as pd
import typer

from rescuetime_to_gcal.config import config as cfg
from rescuetime_to_gcal.gcal.auth import get_refresh_token
from rescuetime_to_gcal.gcal.client import GcalSyncer
from rescuetime_to_gcal.gcal.converter import df_to_gcsa_events
from rescuetime_to_gcal.rescuetime import Rescuetime

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
    get_refresh_token(gcal_client_id, gcal_client_secret)


@app.command(name="sync")
def cli(
    rescuetime_api_key: Annotated[str, typer.Argument(envvar="RESCUETIME_API_KEY")],
    gcal_email: Annotated[str, typer.Argument(envvar="GCAL_EMAIL")],
    gcal_project_id: Annotated[
        str,
        typer.Argument(envvar="GCAL_PROJECT_ID"),
    ],
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
    logging.info("Starting script")
    rescuetime_data = Rescuetime(api_key=rescuetime_api_key).pull(
        anchor_date=pd.Timestamp.today(),
        lookbehind_distance=cfg.sync_window,
        titles_to_exclude=cfg.exclude_titles,
        titles_to_keep=None,
        min_duration=cfg.min_duration,
        allowed_gap_for_combining=cfg.merge_gap,
        metadata=cfg.metadata_enrichment,
    )
    events = df_to_gcsa_events(rescuetime_data)

    logging.info("Syncing events to calendar")
    GcalSyncer(
        email=gcal_email,
        client_id=gcal_client_id,
        project_id=gcal_project_id,
        client_secret=gcal_client_secret,
        refresh_token=gcal_refresh_token,
    ).sync_events_to_calendar(events)

    logging.info(f"Sync complete, synced {len(events)} events")


if __name__ == "__main__":
    app()
