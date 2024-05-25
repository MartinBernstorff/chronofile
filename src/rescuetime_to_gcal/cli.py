import importlib
import importlib.metadata
import logging
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Annotated, Optional, Sequence

import coloredlogs
import devtools
import typer

from rescuetime_to_gcal import activitywatch, rescuetime
from rescuetime_to_gcal.__main__ import main
from rescuetime_to_gcal.config import config as cfg
from rescuetime_to_gcal.gcal.auth import print_refresh_token

if TYPE_CHECKING:
    from rescuetime_to_gcal.event_source import EventSource

log = coloredlogs.install(  # type: ignore
    level="INFO",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

app = typer.Typer()


@app.command(name="auth")
def auth(
    gcal_client_id: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_ID")],
    gcal_client_secret: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_SECRET")],
):
    logging.info("Getting refresh token")
    print_refresh_token(client_id=gcal_client_id, client_secret=gcal_client_secret)


@app.command(name="sync")
def cli(
    rescuetime_api_key: Annotated[Optional[str], typer.Argument(envvar="RESCUETIME_API_KEY")],
    activitywatch_base_url: Annotated[
        Optional[str], typer.Argument(envvar="ACTIVITYWATCH_BASE_URL")
    ],
    gcal_email: Annotated[str, typer.Argument(envvar="GCAL_EMAIL")],
    gcal_client_id: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_ID")],
    gcal_client_secret: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_SECRET")],
    gcal_refresh_token: Annotated[str, typer.Argument(envvar="GCAL_REFRESH_TOKEN")],
    dry_run: bool = False,
):
    logging.info(
        f"Running Rescuetime-to-gcal version {importlib.metadata.version('rescuetime-to-gcal')}"
    )
    logging.info(devtools.debug.format(cfg))
    logging.info("Starting sync")

    event_sources: Sequence[EventSource] = []

    if rescuetime_api_key:
        event_sources.append(
            partial(
                rescuetime.load,
                api_key=rescuetime_api_key,
                anchor_date=datetime.now(),
                lookback_window=cfg.sync_window,
                timezone=cfg.rescuetime_timezone,
            )
        )

    if activitywatch_base_url:
        event_sources.append(
            partial(
                activitywatch.load_all_events, date=datetime.now(), base_url=activitywatch_base_url
            )
        )

    if len(event_sources) == 0:
        raise ValueError(
            "No event sources provided. Specify either rescuetime_api_key or activitywatch_base_url"
        )

    events = main(
        event_sources,
        gcal_email,
        gcal_client_id,
        gcal_client_secret,
        gcal_refresh_token,
        dry_run=dry_run,
    )

    if not dry_run:
        logging.info(f"Sync complete, synced {len(events)} events")
    else:
        logging.info("Dry run, not syncing")


if __name__ == "__main__":
    from typer.testing import CliRunner

    CliRunner().invoke(app, ["sync", "--dry-run"])

    app()
