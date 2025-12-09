from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

class logger_port (Protocol):
    def log_message (self, message: str, level: str) -> None:
        pass

    def save_log_to_file (self, file_path: Path) -> None:
        pass