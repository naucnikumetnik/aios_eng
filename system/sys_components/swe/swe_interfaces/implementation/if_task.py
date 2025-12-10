from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

@dataclass
class task_order:
    task_name: str
    task_description: str
    input_requirements: str
    output_requirements: str
    parameters: str
    execute_v_implement: str

@dataclass
class task:
    name: str
    description: str
    input_files: Sequence[Path]
    output_files: Sequence[Path]
    parameters: dict[str, str]

class request_task_port (Protocol):
    def compile_task (self, task_order: task_order) -> task:
        ...