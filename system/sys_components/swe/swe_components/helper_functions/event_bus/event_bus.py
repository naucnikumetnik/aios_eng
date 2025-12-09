# simple_event_bus.py

from collections.abc import Callable
from typing import List

from .if_task_lifecycle_events import TaskLifecycleEventsPort, TaskStatusEvent


class InProcessTaskLifecycleBus(TaskLifecycleEventsPort):
    def __init__(self) -> None:
        self._subscribers: List[Callable[[TaskStatusEvent], None]] = []

    def publish(self, event: TaskStatusEvent) -> None:
        for handler in list(self._subscribers):
            handler(event)

    def subscribe(self, handler: Callable[[TaskStatusEvent], None]) -> None:
        self._subscribers.append(handler)
    def unsubscribe(self, handler: Callable[[TaskStatusEvent], None]) -> None:
        self._subscribers.remove(handler)