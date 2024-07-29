import logging
from typing import Annotated

import typer
from rescuetime2gcal.commands.sync import app
from rescuetime2gcal.sources.gcal.auth import print_refresh_token


@app.command()
def gcal_auth(
    gcal_client_id: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_ID")],
    gcal_client_secret: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_SECRET")],
):
    logging.info("Getting refresh token")
    print_refresh_token(client_id=gcal_client_id, client_secret=gcal_client_secret)
