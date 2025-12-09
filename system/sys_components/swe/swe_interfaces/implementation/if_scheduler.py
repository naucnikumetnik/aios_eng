from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

@dataclass(frozen=True)
class task_status:
    task_id: str
    status: str

@dataclass(frozen=True)
class execution_plan:
    task: str # unit id
    status: str # e.g., "pending", "in_progress", "completed"

dataclass (frozen=True)
class scheduler_config:
    restore_v_create: str
    execute_v_implement: str
    architecture_v_unit: str
    architecture_v_unit_path: Path
    review_required: bool
    tests_required: bool
    resources: Sequence[str]

class scheduler_port (Protocol):
    def create_execution_plan (self, architecture_description : Path) -> execution_plan:
        pass