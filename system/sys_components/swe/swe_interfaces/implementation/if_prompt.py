from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from task_compiler.design.interfaces.if_task import task

@dataclass
class prompt:
    content: str

class prompt_compilation_port (Protocol):
    def compile_prompt (self, task = task, project_path = Path) -> prompt:
        pass