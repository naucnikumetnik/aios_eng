from dataclasses import dataclass

@dataclass(frozen=True)
class task_status:
    task_id: str
    status: str
