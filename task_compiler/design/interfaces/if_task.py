from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

@dataclass(fixed = True)
class task_order:
    task_name: str
    task_description: str
    input_requirements: dict[str, str]
    output_requirements: dict[str, str]
    parameters: dict[str, str]

@dataclass
class task:
    name: str
    description: str
    input_files: Sequence[Path]
    output_files: Sequence[Path]
    parameters: dict[str, str]

class request_task_port (Protocol):
    def compile_task (self, task_order: task_order) -> task:
        pass