from typing import Protocol
from .models import Schedule

class CalendarConnector(Protocol):
    def conflicts(self, connection, schedule: Schedule) -> bool: ...
    def create(self, connection, task_id: str, schedule: Schedule) -> None: ...

class MockCalendar:
    def conflicts(self, connection, schedule):
        return connection.execute("SELECT 1 FROM calendar WHERE start < ? AND end > ?",
            (schedule.end.isoformat(), schedule.start.isoformat())).fetchone() is not None

    def create(self, connection, task_id, schedule):
        connection.execute("INSERT INTO calendar VALUES (?,?,?,?)",
            (task_id, schedule.title, schedule.start.isoformat(), schedule.end.isoformat()))

class EmailConnector(Protocol):
    def drafts(self) -> list[dict]: ...

class MockEmail:
    def drafts(self):
        return []
