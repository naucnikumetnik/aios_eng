#local
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
#interfaces



@dataclass(frozen=True)
class execution_plan:
    status: str # e.g., "pending", "in_progress", "completed"

class scheduler_port (Protocol):
    def create_execution_plan (self, architecture_description: Path) -> execution_plan:
        ...
    def order_task (self, unit: Path) -> None:
        ...