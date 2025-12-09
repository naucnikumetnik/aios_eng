from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

dataclass (frozen=True)
class architecture_description:
    name: str
    components: Sequence[str]