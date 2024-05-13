import logging
from typing import Annotated

import coloredlogs
import typer

from rescuetime_to_gcal.gcal.auth import print_refresh_token
from rescuetime_to_gcal.main import main

log = coloredlogs.install(  # type: ignore
    level="INFO",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

app = typer.Typer()


RESCUETIME_API_KEY = "B6300jX6LJHN6RU0uhZCQfOJEMrn2RfLIY0bkT_z"
GCAL_EMAIL = "martinbernstorff@gmail.com"
GCAL_CLIENT_ID = (
    "952562068458-eaok38c6ojn9cmm2s08v8l6hocok5a21.apps.googleusercontent.com"
)
GCAL_CLIENT_SECRET = "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"
GCAL_REFRESH_TOKEN = "1//0chpk9cJszftQCgYIARAAGAwSNwF-L9Ir47o_-OiYSl_0mfBcTuhOmAt6YvFoOB3WU4VaByZi05HDne_AHke6DRLgCAzSL20qHgo"


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

    events = main(
        rescuetime_api_key,
        gcal_email,
        gcal_client_id,
        gcal_client_secret,
        gcal_refresh_token,
    )

    logging.info(f"Sync complete, synced {events.count()} events")


if __name__ == "__main__":
    app()
