#local
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
#interfaces
from system.sys_components.swe.swe_interfaces.implementation.if_resources import resources_data


@dataclass(frozen=True)
class execution_plan:
    status: str # e.g., "pending", "in_progress", "completed"

@dataclass (frozen=True)
class system_config:
    restore_v_create: str
    checkpoint: Path
    execute_v_implement: str
    architecture_v_unit: str
    architecture_v_unit_path: Path
    review_required: bool
    tests_required: bool
    resources: resources_data
    log_path: Path
    project_path: Path

class scheduler_port (Protocol):
    def create_execution_plan (self, architecture_description: Path) -> execution_plan:
        ...
    def order_task (self, unit: Path) -> None:
        ...