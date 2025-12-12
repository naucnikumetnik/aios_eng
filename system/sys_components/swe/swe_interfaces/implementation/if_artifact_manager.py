from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

@dataclass(frozen=True)
class artifact_ref:
    kind: str        # "udd|arch_desc|interface|task|trace|..."
    id: str          # e.g. "UDD-AIOS-SCHED-01"

@dataclass(frozen=True)
class artifact_content:
    ref: artifact_ref
    raw_content: str

class artifact_store_port(Protocol):
    def load(self, ref: artifact_ref) -> artifact_content: ...
    def save(self, artifact: artifact_content) -> None: ...
    def modify_artifact (self, file_path: Path, edit_type: str, data) -> bool: ...