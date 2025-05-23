import importlib.metadata
import logging
import time
from typing import TYPE_CHECKING, Annotated, Optional, Sequence

import devtools
import rich.pretty
import typer
from iterpy.arr import Arr

import chronofile.diff as diff
from chronofile.commands.sync_logic import log, pipeline, try_activitywatch
from chronofile.config import Config
from chronofile.destinations import gcal
from chronofile.destinations.gcal.auth import print_refresh_token

if TYPE_CHECKING:
    from chronofile.sources.source import EventSource

app = typer.Typer()


@app.command()
def sync(
    activitywatch_base_url: Annotated[
        Optional[str], typer.Argument(envvar="ACTIVITYWATCH_BASE_URL")
    ],
    gcal_email: Annotated[str, typer.Argument(envvar="GCAL_EMAIL")],
    gcal_client_id: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_ID")],
    gcal_client_secret: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_SECRET")],
    gcal_refresh_token: Annotated[str, typer.Argument(envvar="GCAL_REFRESH_TOKEN")],
    config_path: Annotated[str, typer.Argument(envvar="CONFIG_PATH")] = "config.toml",
    rescuetime_api_key: Annotated[
        Optional[str], typer.Argument(envvar="RESCUETIME_API_KEY")
    ] = None,
    dry_run: bool = False,
    watch: Annotated[bool, typer.Option(envvar="WATCH")] = False,
):
    cfg = Config.from_toml(config_path)

    logging.info(f"Running chronofile version {importlib.metadata.version('chronofile')}")
    logging.info(rich.pretty.pprint(cfg))
    logging.info("Starting sync")

    event_sources: Sequence[EventSource] = [
        s for s in [try_activitywatch(activitywatch_base_url)] if s is not None
    ]

    if len(event_sources) == 0:
        raise ValueError(
            "No event sources provided. Specify either rescuetime_api_key or activitywatch_base_url"
        )

    input_events = Arr(event_sources).map(lambda f: f()).flatten().to_list()

    destination_client = gcal.GcalClient(
        calendar_id=gcal_email,
        client_id=gcal_client_id,
        client_secret=gcal_client_secret,
        refresh_token=gcal_refresh_token,
    )

    changes = pipeline(
        source_events=input_events,
        destination_events=destination_client.get_events(
            start=min([event.start for event in input_events]),
            end=max([event.start for event in input_events])
            + max([event.duration for event in input_events]),
        ),
        min_duration=cfg.min_duration,
        category2emoji=cfg.category2emoji,
        exclude_titles=cfg.exclude_titles,
        merge_gap=cfg.merge_gap,
        metadata_enrichment=cfg.metadata_enrichment,
        exclude_apps=cfg.exclude_apps,
    )

    logging.info(f"Changes to be made {devtools.debug.format(changes)}")

    if not dry_run:
        log.info("Dry-run is false, syncing changes")
        for change in changes:
            match change:
                case diff.NewEvent():
                    destination_client.add_event(change.event)
                case diff.UpdateEvent():
                    destination_client.update_event(change.event)
                case diff.DeleteEvent():
                    destination_client.delete_event(change.event)
    else:
        log.info("Dry-run enabled, skipping sync")

    if watch:
        sleep_minutes = 5
        log.info(f"Watch is {watch}, sleeping for {sleep_minutes} minutes")
        time.sleep(sleep_minutes * 60)
        sync(
            rescuetime_api_key=rescuetime_api_key,
            activitywatch_base_url=activitywatch_base_url,
            gcal_email=gcal_email,
            gcal_client_id=gcal_client_id,
            gcal_client_secret=gcal_client_secret,
            gcal_refresh_token=gcal_refresh_token,
            dry_run=dry_run,
            watch=watch,
        )


@app.command()
def gcal_auth(
    gcal_client_id: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_ID")],
    gcal_client_secret: Annotated[str, typer.Argument(envvar="GCAL_CLIENT_SECRET")],
):
    logging.info("Getting refresh token")
    print_refresh_token(client_id=gcal_client_id, client_secret=gcal_client_secret)
