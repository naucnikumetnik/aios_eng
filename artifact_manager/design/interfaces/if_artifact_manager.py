from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


class save_as_type_port (Protocol):
    def save_as_type (self, file_path: Path, file_type: str, data: str) -> bool:
        pass

class modify_artifact_port (Protocol):
    def modify_artifact (self, file_path: Path, edit_type: str, data) -> bool:
        pass