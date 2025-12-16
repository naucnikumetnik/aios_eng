from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

@dataclass (frozen = True)
class available_resources:
    gpu: float
    ram: float
    cpu: float
    rom: float

class fetch_resources_port (Protocol):
    def fetch_available_resources (self, resource_name: str, destination: Path) -> available_resources | None:
        ...