from typing import Protocol, Any
from core import TaskDetail


class SyncService(Protocol):
    enabled: bool
    config: Any

    def sync_task(self, task: TaskDetail) -> bool:
        ...

    def pull_task_fields(self, task: TaskDetail) -> None:
        ...

    def clone(self) -> "SyncService":
        ...
