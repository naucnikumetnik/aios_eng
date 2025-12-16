from dataclasses import dataclass
from typing import Protocol, Optional
from pathlib import Path
from system.sys_components.swe.swe_interfaces.implementation.if_resources import resources_data


# plan events
@dataclass (frozen=True)
class plan_runtime_report:
    execution_plan_id: str
    plan: dict [str, str]
    completion_percent: int
    duration: int
    estimated_remaining_time:int 
    todo: int
    done: int
    failed: int
    models: dict [str, str]

@dataclass (frozen=True)
class plan_aborted_report:
    total_execution_time: int
    paths_to_artifacts: list

@dataclass (frozen=True)
class plan_failed_report:
    total_execution_time: int
    paths_to_artifacts: dict [str, str]

@dataclass (frozen=True)
class plan_complete_report:
    total_execution_time: int
    paths_to_artifacts: dict [str, str]

# task events
@dataclass (frozen=True)
class task_starting_report:
    task_id: str
    storage_tool: str
    file_location: Path

@dataclass (frozen=True)
class task_runtime_report:
    current_task: str
    progress: int
    batch: int
    batches_remaining: int
    execution_time: int

@dataclass (frozen=True)
class task_failed_report:
    total_execution_time: int
    execution_speed: str
    answer: str
    artifact_location: Path

@dataclass (frozen=True)
class task_aborted_report:
    total_execution_time: int
    execution_speed: str
    answer: str
    artifact_location: Path

@dataclass (frozen=True)
class complete_task_report:
    total_execution_time: int
    execution_speed: str
    answer: str
    artifact_location: Path

# batch events
@dataclass (frozen=True)
class batch_starting_report:
    execution_time: int
    prompt: str

@dataclass (frozen=True)
class batch_runtime_report:
    execution_time: int
    prompt: str

@dataclass (frozen=True)
class batch_complete_report:
    execution_time: int
    prompt: str

@dataclass (frozen=True)
class batch_failed_report:
    execution_time: int
    prompt: str

@dataclass (frozen=True)
class batch_aborted_report:
    execution_time: int
    prompt: str

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
    orga: Path
    project_path: Path

class report_to_user_port (Protocol):
    def report_plan_progress (self) -> plan_status:
        ...
    def report_task_progress (self) -> task_status:
        ...
    def provide_help (self) -> help:
        ... 