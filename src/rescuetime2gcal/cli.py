import importlib
import importlib.metadata
import logging
import time
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Annotated, Optional, Sequence

import coloredlogs
import rich
import rich.pretty
import typer

from rescuetime2gcal.__main__ import main
from rescuetime2gcal.clients import activitywatch, gcal, rescuetime
from rescuetime2gcal.clients.gcal.auth import print_refresh_token
from rescuetime2gcal.config import Config

if TYPE_CHECKING:
    from rescuetime2gcal.clients.event_source import EventSource

coloredlogs.install(  # type: ignore
    level="INFO",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

log = logging.getLogger(__name__)

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
    config_path: Annotated[str, typer.Argument(envvar="CONFIG_PATH")] = "config.toml",
    dry_run: bool = False,
    watch: bool = False,
):
    cfg = Config.from_toml(config_path)

    logging.info(
        f"Running Rescuetime-to-gcal version {importlib.metadata.version('rescuetime2gcal')}"
    )
    logging.info(rich.pretty.pprint(cfg))
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

    main(
        event_sources,
        destination_client=gcal.GcalClient(
            calendar_id=gcal_email,
            client_id=gcal_client_id,
            client_secret=gcal_client_secret,
            refresh_token=gcal_refresh_token,
        ),
        dry_run=dry_run,
        cfg=cfg,
    )

    if watch:
        sleep_minutes = 5
        log.info(f"Watch is {watch}, sleeping for {sleep_minutes} minutes")
        time.sleep(sleep_minutes * 60)
        cli(
            rescuetime_api_key=rescuetime_api_key,
            activitywatch_base_url=activitywatch_base_url,
            gcal_email=gcal_email,
            gcal_client_id=gcal_client_id,
            gcal_client_secret=gcal_client_secret,
            gcal_refresh_token=gcal_refresh_token,
            dry_run=dry_run,
            watch=watch,
        )


if __name__ == "__main__":
    from typer.testing import CliRunner

    # TD: Remove before publish
    CliRunner().invoke(app, ["sync", "--dry-run"])

    app()
