from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence
from interfaces.if_architecture_description import architecture_description

@dataclass(frozen=True)
class execution_plan:
    task: str # unit id
    status: str # e.g., "pending", "in_progress", "completed"

class execution_plan_port (Protocol):
    def create_execution_plan (self, architecture_description = architecture_description) -> execution_plan:
        pass