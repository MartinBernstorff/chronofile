import datetime  # noqa: TCH003
from typing import Optional

import pydantic

from rescuetime2gcal.config import RecordCategory  # noqa: TCH001


class Event(pydantic.BaseModel):
    title: str
    start: datetime.datetime
    end: datetime.datetime
    category: Optional[RecordCategory] = None
    timezone: str = "UTC"
    destination_event_id: Optional[str] = None

    @property
    def identity(self) -> str:
        return f"{self.title} {self.start} to {self.end}"

    @property
    def duration(self) -> "datetime.timedelta":
        return self.end - self.start

    def __repr__(self) -> str:
        return f"Event(title={self.title}, {self.start} to {self.end}, {self.timezone})"
