from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

class convert_file_port (Protocol):
    def convert_file (self, input_file: Path, output_format: str) -> Path:
        pass