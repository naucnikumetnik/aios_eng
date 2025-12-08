from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

@dataclass(frozen=True)
class available_resources:
    gpu_memory_gb: float
    cpu_cores: int
    ram_gb: float

class fetch_resources_port (Protocol):
    def fetch_available_resources (self, resource_name: str, destination: Path) -> available_resources:
        pass