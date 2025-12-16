# core/artifact_engine/design/interfaces/if_artifact_engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Literal

artifact_format = Literal["yaml", "yml", "json", "md", "txt", "unknown"]


@dataclass(frozen=True)
class artifact_ref:
    kind: str
    id: str


@dataclass(frozen=True)
class cm_anchor_ref:
    cm_anchor_id: str
    expected_kind: Optional[str] = None


@dataclass(frozen=True)
class artifact_blob:
    ref: artifact_ref
    raw: str
    fmt: artifact_format
    repo_relpath: Optional[str] = None


class artifact_engine_port(Protocol):
    def load_by_ref(self, ref: artifact_ref) -> Optional[artifact_blob]: ...
    def load_by_cm_anchor(self, anchor: cm_anchor_ref) -> Optional[artifact_blob]: ...
    def save_to_cm_anchor(self, anchor: cm_anchor_ref, raw: str, fmt: artifact_format) -> None: ...
