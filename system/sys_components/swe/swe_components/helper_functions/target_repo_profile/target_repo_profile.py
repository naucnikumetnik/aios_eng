# sos_interfaces/implementation/repo_profile_provider.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

from sos_interfaces.if_system_configuration import (
    target_repo_profile_port,
    target_repo_profile,
    cm_catalogue_profile,
)


@dataclass
class repo_profile_provider(target_repo_profile_port):
    repo_root: Path
    profile_relpath: str = ".aios/target_repo_profile.yaml"

    def get_profile(self) -> target_repo_profile:
        profile_path = self.repo_root / self.profile_relpath
        if not profile_path.exists():
            raise FileNotFoundError(f"Target repo profile not found: {profile_path}")

        raw = profile_path.read_text(encoding="utf-8")

        # parse yaml/json based on extension (bootstrap only)
        if profile_path.suffix.lower() == ".json":
            obj = json.loads(raw)
        else:
            if yaml is None:
                raise RuntimeError("PyYAML not installed; cannot read YAML repo profile.")
            obj = yaml.safe_load(raw)

        if not isinstance(obj, dict):
            raise ValueError("Invalid target repo profile format (expected object)")

        cm = obj.get("cm_catalogue") or {}
        return target_repo_profile(
            profile_id=str(obj.get("profile_id", "")),
            profile_version=str(obj.get("profile_version", "")),
            repo_kind=str(obj.get("repo_kind", "filesystem")),
            cm_catalogue=cm_catalogue_profile(
                catalogue_relpath=str(cm.get("catalogue_relpath", "")),
                entries_list_key=str(cm.get("entries_list_key", "entries")),
                cm_id_field=str(cm.get("cm_id_field", "cm_id")),
                location_field=str(cm.get("location_field", "location")),
                format_field=cm.get("format_field", "format"),
                artifact_kind_field=cm.get("artifact_kind_field", "artifact_kind"),
                artifact_id_field=cm.get("artifact_id_field", "artifact_id"),
            ),
        )
