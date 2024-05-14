import importlib
import importlib.metadata
import logging
from typing import Annotated

import coloredlogs
import devtools
import typer

from rescuetime_to_gcal.config import config as cfg
from rescuetime_to_gcal.gcal.auth import print_refresh_token
from rescuetime_to_gcal.main import main

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
    print_refresh_token(client_id=gcal_client_id, client_secret=gcal_client_secret)


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
    logging.info(
        f"Running Rescuetime-to-gcal version {importlib.metadata.version('rescuetime-to-gcal')}"
    )
    logging.info(devtools.debug.format(cfg))
    logging.info("Starting sync")

    events = main(
        rescuetime_api_key,
        gcal_email,
        gcal_client_id,
        gcal_client_secret,
        gcal_refresh_token,
    )

    logging.info(f"Sync complete, synced {len(events)} events")


if __name__ == "__main__":
    app()
