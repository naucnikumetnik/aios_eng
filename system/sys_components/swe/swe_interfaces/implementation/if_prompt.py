from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from system.sys_components.swe.swe_interfaces.implementation.if_task import task_spec

@dataclass
class prompt:
    content: str

class prompt_compilation_port (Protocol):
    def compile_prompt (self, task = task_spec, project_path = Path) -> prompt:
        ...