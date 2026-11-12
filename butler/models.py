from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Schedule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=300)
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def valid(self):
        if not self.title.strip():
            raise ValueError("A title is required")
        if self.start.utcoffset() is None or self.end.utcoffset() is None:
            raise ValueError("Explicit timezone offsets are required")
        if self.end <= self.start:
            raise ValueError("End must follow start")
        self.start = self.start.astimezone(timezone.utc)
        self.end = self.end.astimezone(timezone.utc)
        return self

class Request(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    key: str = Field(min_length=1, max_length=100)

class Decision(BaseModel):
    approve: bool
