import datetime
import importlib
import importlib.metadata
import logging
import time
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Annotated, Callable, Mapping, Optional, Sequence

import coloredlogs
import devtools
import rescuetime2gcal.diff as diff
import rich
import rich.pretty
import typer  # noqa: TCH002
from iterpy.arr import Arr
from rescuetime2gcal.commands.cli import app
from rescuetime2gcal.config import Config, RecordCategory, RecordMetadata
from rescuetime2gcal.event import DestinationEvent, hydrate_event
from rescuetime2gcal.sources import activitywatch, gcal, rescuetime
from rescuetime2gcal.sources.source import EventSource
from rescuetime2gcal.sources.source_event import SourceEvent, WindowTitleEvent
from rescuetime2gcal.timeline import merge_within_window

if TYPE_CHECKING:
    from rescuetime2gcal.sources.source import EventSource

coloredlogs.install(  # type: ignore
    level="INFO",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

log = logging.getLogger(__name__)


def _try_activitywatch(
    activitywatch_base_url: str | None,
) -> Optional[Callable[[], Sequence[SourceEvent]]]:
    if activitywatch_base_url:
        return partial(
            activitywatch.load_all_events,
            date=datetime.datetime.now(),
            base_url=activitywatch_base_url,
        )
    return None


def _try_rescuetime(
    rescuetime_api_key: str | None, cfg: "Config"
) -> Optional[Callable[[], Sequence[SourceEvent]]]:
    if rescuetime_api_key:
        return partial(
            rescuetime.load,
            api_key=rescuetime_api_key,
            anchor_date=datetime.datetime.now(),
            lookback_window=cfg.sync_window,
            timezone=cfg.rescuetime_timezone,
        )
    return None


@dataclass(frozen=True)
class DeduplicatedGroup:
    keeper: "DestinationEvent"
    duplicates: Sequence["DestinationEvent"]

    @staticmethod
    def _from_event_group(event_group: Sequence["DestinationEvent"]) -> "DeduplicatedGroup":
        if len(event_group) > 1:
            return DeduplicatedGroup(keeper=event_group[0], duplicates=event_group[1:])
        return DeduplicatedGroup(keeper=event_group[0], duplicates=[])


def _pipeline(  # noqa: D417
    source_events: Sequence["SourceEvent"],
    destination_events: Sequence["DestinationEvent"],
    min_duration: "datetime.timedelta",
    category2emoji: Mapping["RecordCategory", str],
    exclude_titles: Sequence[str],
    merge_gap: "datetime.timedelta",
    metadata_enrichment: Sequence["RecordMetadata"],
    exclude_apps: Sequence[str],
) -> Sequence[diff.EventChange]:
    """Event processing without I/O. Separating this from I/O makes debugging and testing easier.

    Args:
        source_events: Source events to process
        destination_events: Destination events to process
        ... [See the Config object for the rest of the arguments]
    """

    # Preprocess the source events
    sufficient_length_events = Arr(source_events).filter(lambda e: e.duration > min_duration)

    without_excluded_apps = sufficient_length_events.filter(
        lambda e: not any(excluded_app.lower() in e.app.lower() for excluded_app in exclude_apps)
        if isinstance(e, WindowTitleEvent)
        else True
    )

    parsed_events = without_excluded_apps.map(
        lambda e: hydrate_event(
            event=e, metadata=metadata_enrichment, category2emoji=category2emoji
        )
    )

    filtered_by_title = parsed_events.filter(
        lambda e: not any(
            excluded_title.lower() in e.title.lower() for excluded_title in exclude_titles
        )
    )

    merged_within_gap = (
        filtered_by_title.groupby(lambda e: e.title)
        .map(lambda g: merge_within_window(g[1], merge_gap=merge_gap))
        .flatten()
        .to_list()
    )

    # Deduplicate destination events
    deduplicated_destination_events = (
        Arr(destination_events)
        .groupby(lambda e: e.identity)
        .map(lambda g: DeduplicatedGroup._from_event_group(g[1]))
    )
    destination_keepers = deduplicated_destination_events.map(lambda g: g.keeper).to_list()
    destination_duplicates = (
        deduplicated_destination_events.map(lambda g: list(g.duplicates)).flatten().to_list()
    )

    # Calculate the delta
    changeset = diff.diff(merged_within_gap, destination_keepers)

    return [*changeset, *[diff.DeleteEvent(event=e) for e in destination_duplicates]]


@app.command()
def sync(
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
    watch: Annotated[bool, typer.Option(envvar="WATCH")] = False,
):
    cfg = Config.from_toml(config_path)

    logging.info(f"Running rescuetime2gcal version {importlib.metadata.version('rescuetime2gcal')}")
    logging.info(rich.pretty.pprint(cfg))
    logging.info("Starting sync")

    event_sources: Sequence[EventSource] = [
        s
        for s in [
            _try_rescuetime(rescuetime_api_key, cfg),
            _try_activitywatch(activitywatch_base_url),
        ]
        if s is not None
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

    changes = _pipeline(
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
