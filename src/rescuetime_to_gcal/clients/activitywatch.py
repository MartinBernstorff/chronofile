import datetime  # noqa: TCH003
import logging
from functools import partial
from typing import Any, Callable, Literal, Mapping, Sequence

import devtools
import pydantic
import requests
from rescuetime_to_gcal.event import BareEvent, SourceEvent, URLEvent, WindowTitleEvent

log = logging.getLogger(__name__)


class AwBucket(pydantic.BaseModel):
    id: str
    created: "datetime.datetime"
    type: Literal["currentwindow", "web.tab.current"]
    client: str
    hostname: str
    last_updated: "datetime.datetime"


def _load_bucket_contents(
    bucket_id: str, date: "datetime.datetime", base_url: str = "http://localhost:5600/api/"
) -> Sequence[Mapping[str, Any]]:
    params = {"bucket_id": bucket_id, "start": date.strftime("%Y-%m-%d")}
    response = requests.get(f"{base_url}/0/buckets/{bucket_id}/events", params=params).json()
    return response


def load_window_titles(
    bucket_id: str, date: "datetime.datetime", base_url: str = "http://localhost:5600/api/"
) -> Sequence[WindowTitleEvent]:
    response = _load_bucket_contents(bucket_id, date, base_url)
    events = [
        WindowTitleEvent(
            app=e["data"]["app"],
            window_title=e["data"]["title"],
            start=e["timestamp"],
            duration=e["duration"],
        )
        for e in response
    ]
    return events


def load_url_events(
    bucket_id: str, date: "datetime.datetime", base_url: str = "http://localhost:5600/api/"
) -> Sequence[URLEvent]:
    response = _load_bucket_contents(bucket_id, date, base_url)
    events = [
        URLEvent(
            url=e["data"]["url"],
            url_title=e["data"]["title"],
            start=e["timestamp"],
            duration=e["duration"],
        )
        for e in response
    ]
    return events


def _initialise_bucket_loader(
    bucket: AwBucket, date: "datetime.datetime"
) -> Callable[[], Sequence[SourceEvent]]:
    match bucket.type:
        case "currentwindow":
            return partial(load_window_titles, bucket.id, date)
        case "web.tab.current":
            return partial(load_url_events, bucket.id, date)


def load_all_events(
    date: "datetime.datetime", base_url: str = "http://localhost:5600/api/"
) -> Sequence[SourceEvent]:
    bucket_data = requests.get(f"{base_url}/0/buckets").json()

    supported_buckets: Sequence[Mapping[str, Any]] = []
    for b in bucket_data.values():
        if b["type"] not in ["currentwindow", "web.tab.current"]:
            log.warning(f"Unknown bucket type {b['type']}")
            continue
        supported_buckets.append(b)

    buckets = [AwBucket(**b) for b in supported_buckets]
    loaders = [_initialise_bucket_loader(bucket=b, date=date) for b in buckets]
    events = [event for loader in loaders for event in loader()]
    log.info(f"Activitywatch {devtools.debug.format(events)}")

    return events
