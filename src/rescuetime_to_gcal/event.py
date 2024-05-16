import datetime
from typing import Optional

import pydantic

from rescuetime_to_gcal.config import RecordCategory


class Event(pydantic.BaseModel):
    title: str
    start: datetime.datetime
    end: datetime.datetime
    category: Optional[RecordCategory] = None
    timezone: str = "UTC"

    @property
    def duration(self) -> datetime.timedelta:
        return self.end - self.start

    def __repr__(self):
        return f"Event(title={self.title}, {self.start} to {self.end}, {self.timezone})"
