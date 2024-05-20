import importlib
import importlib.metadata
import logging
from typing import Annotated

import coloredlogs
import devtools
import typer

from rescuetime2gcal.__main__ import main
from rescuetime2gcal.config import config as cfg
from rescuetime2gcal.gcal.auth import print_refresh_token

log = coloredlogs.install(  # type: ignore
    level="INFO",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

app = typer.Typer()


@app.command()
def auth(
    gcal_client_id: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_ID")],
    gcal_client_secret: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_SECRET")],
):
    logging.info("Getting refresh token")
    print_refresh_token(client_id=gcal_client_id, client_secret=gcal_client_secret)


@app.command()
def sync(
    rescuetime_api_key: Annotated[str, typer.Argument(envvar="RESCUETIME_API_KEY")],
    gcal_email: Annotated[str, typer.Argument(envvar="GCAL_EMAIL")],
    gcal_client_id: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_ID")],
    gcal_client_secret: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_SECRET")],
    gcal_refresh_token: Annotated[str, typer.Argument(envvar="GCAL_REFRESH_TOKEN")],
    dry_run: bool = False,
):
    logging.info(f"Running Rescuetime2gcal version {importlib.metadata.version('rescuetime2gcal')}")
    logging.info(devtools.debug.format(cfg))
    logging.info("Starting sync")

    events = main(
        rescuetime_api_key,
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
    app()
