# core/document_codec/design/interfaces/if_document_codec.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Literal


ArtifactFormat = Literal["yaml", "yml", "json", "md", "txt", "unknown"]


@dataclass(frozen=True)
class artifact_blob:
    kind: str
    id: str
    raw: str
    fmt: ArtifactFormat
    repo_relpath: str | None = None


class document_codec_port(Protocol):
    def decode(self, blob: artifact_blob) -> Any: ...
    def encode(self, obj: Any, fmt: ArtifactFormat) -> str: ...
