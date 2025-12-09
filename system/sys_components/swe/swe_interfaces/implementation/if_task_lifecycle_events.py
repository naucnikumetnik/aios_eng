from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Protocol, Callable


class TaskStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TaskStatusEvent:
    event_id: str               # could map to dynamic_view.events[*].id + UUID
    task_instance_id: str
    old_status: TaskStatus
    new_status: TaskStatus
    occurred_at: datetime
    reason: str | None = None

class TaskLifecycleEventsPort(Protocol):
    def publish(self, event: TaskStatusEvent) -> None:
        """Used by TaskExecutor / ArtifactEngine to emit events."""
        ...

    def subscribe(self, handler: Callable[[TaskStatusEvent], None]) -> None:
        """Used by Scheduler to listen for status changes."""
        ...
    def unsubscribe(self, handler: Callable[[TaskStatusEvent], None]) -> None:
        """Used by Scheduler to stop listening for status changes."""
        ...