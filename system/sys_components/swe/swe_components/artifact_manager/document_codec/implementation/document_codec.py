# core/document_codec/implementation/document_codec.py
from __future__ import annotations

import json
from typing import Any

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

from system.sys_components.swe.swe_interfaces.implementation.if_document_codec import (
    document_codec_port,
    artifact_blob,
    ArtifactFormat,
)


class document_codec(document_codec_port):
    def decode(self, blob: artifact_blob) -> Any:
        raw = blob.raw

        if blob.fmt in ("json",) or raw.lstrip().startswith("{") or raw.lstrip().startswith("["):
            return json.loads(raw)

        if blob.fmt in ("yaml", "yml", "unknown"):
            if yaml is None:
                raise RuntimeError("PyYAML not installed; cannot decode YAML.")
            return yaml.safe_load(raw)

        # md/txt: return as-is
        return raw

    def encode(self, obj: Any, fmt: ArtifactFormat) -> str:
        if fmt == "json":
            return json.dumps(obj, indent=2, ensure_ascii=False)

        if fmt in ("yaml", "yml"):
            if yaml is None:
                raise RuntimeError("PyYAML not installed; cannot encode YAML.")
            return yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)

        # md/txt/unknown
        return str(obj)
