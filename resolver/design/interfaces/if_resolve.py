from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

@dataclass(frozen=True)
class ResolvedTask:
    task_id: str
    description: str
    priority: int
@dataclass(frozen=True)
class ResolvedPrompt:
    prompt_text: str
    variables: dict[str, str]
@dataclass(frozen=True)
class ResolvedSource:
    source_type: str
    location: str

class if_resolve:
    def resolve_task(): 
        pass
    def resolve_prompt():
        pass
    def resolve_sources():
        pass
    
