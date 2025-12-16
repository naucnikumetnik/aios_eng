# core/artifact_engine/implementation/artifact_engine.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from system.sys_components.swe.swe_interfaces.implementation.if_artifact_manager import (
    artifact_engine_port,
    artifact_ref,
    cm_anchor_ref,
    artifact_blob,
    artifact_format,
)
from system.sys_components.swe.swe_interfaces.implementation.if_document_codec import (
    document_codec_port,
    artifact_blob as codec_blob,
)
from sos_interfaces.if_target_repo_access import target_repo_access_port
from sos_interfaces.if_system_configuration import target_repo_profile_port


def infer_format_from_relpath(relpath: str) -> artifact_format:
    ext = Path(relpath).suffix.lower().lstrip(".")
    if ext in ("yaml", "yml", "json", "md", "txt"):
        return ext  # type: ignore
    return "unknown"


@dataclass
class artifact_engine(artifact_engine_port):
    repo_access: target_repo_access_port
    repo_profile: target_repo_profile_port
    codec: document_codec_port

    # ------------------------------ public API --------------------------------

    def load_by_cm_anchor(self, anchor: cm_anchor_ref) -> Optional[artifact_blob]:
        profile = self.repo_profile.get_profile()
        cat_obj = self._load_cm_catalogue(profile)
        if cat_obj is None:
            return None

        entry = self._find_entry_by_cm_id(cat_obj, profile, anchor.cm_anchor_id)
        if entry is None:
            return None

        rel, fmt, kind, out_id = self._entry_to_resolution(profile, entry, default_id=anchor.cm_anchor_id)
        if rel is None:
            return None

        if not self.repo_access.path_exists(Path(rel)):
            return None

        raw = self.repo_access.read_text(Path(rel))
        # prefer caller expected_kind if provided (sanity)
        kind = anchor.expected_kind or kind
        return artifact_blob(ref=artifact_ref(kind=kind, id=out_id), raw=raw, fmt=fmt, repo_relpath=rel)

    def load_by_ref(self, ref: artifact_ref) -> Optional[artifact_blob]:
        """
        CM-first: resolve (kind,id) using cm_catalogue if possible.
        Fallback glob is kept only as a dev escape hatch.
        """
        profile = self.repo_profile.get_profile()
        cat_obj = self._load_cm_catalogue(profile)

        if cat_obj is not None:
            entry = self._find_entry_by_ref(cat_obj, profile, ref)
            if entry is not None:
                rel, fmt, kind, out_id = self._entry_to_resolution(profile, entry, default_id=ref.id, default_kind=ref.kind)
                if rel is None:
                    return None
                if not self.repo_access.path_exists(Path(rel)):
                    return None
                raw = self.repo_access.read_text(Path(rel))
                return artifact_blob(ref=artifact_ref(kind=kind, id=out_id), raw=raw, fmt=fmt, repo_relpath=rel)

        # fallback: search by filename (avoid relying on this long-term)
        return self._fallback_glob_load(ref)

    def save_to_cm_anchor(self, anchor: cm_anchor_ref, raw: str, fmt: artifact_format) -> None:
        profile = self.repo_profile.get_profile()
        cat_obj = self._load_cm_catalogue(profile)
        if cat_obj is None:
            raise FileNotFoundError("CM catalogue not found / unreadable.")

        entry = self._find_entry_by_cm_id(cat_obj, profile, anchor.cm_anchor_id)
        if entry is None:
            raise KeyError(f"CM anchor not found: {anchor.cm_anchor_id}")

        rel = entry.get(profile.cm_catalogue.location_field)
        if not isinstance(rel, str) or not rel:
            raise KeyError(f"CM entry missing location for: {anchor.cm_anchor_id}")

        # we *write*, we don't mutate catalogue here
        self.repo_access.write_text(Path(rel), raw, create_parents=True, overwrite=True)

    # ------------------------------ internals ---------------------------------

    def _load_cm_catalogue(self, profile) -> Optional[dict]:
        cat_path = Path(profile.cm_catalogue.catalogue_relpath)
        if not self.repo_access.path_exists(cat_path):
            return None

        cat_raw = self.repo_access.read_text(cat_path)
        cat_fmt = infer_format_from_relpath(str(cat_path))

        cat_obj = self.codec.decode(codec_blob(
            kind="cm_catalogue",
            id="cm_catalogue",
            raw=cat_raw,
            fmt=cat_fmt,
            repo_relpath=str(cat_path),
        ))
        return cat_obj if isinstance(cat_obj, dict) else None

    def _entries(self, cat_obj: dict, profile) -> Optional[list]:
        entries = cat_obj.get(profile.cm_catalogue.entries_list_key)
        return entries if isinstance(entries, list) else None

    def _find_entry_by_cm_id(self, cat_obj: dict, profile, cm_id: str) -> Optional[dict]:
        entries = self._entries(cat_obj, profile)
        if entries is None:
            return None
        cm_field = profile.cm_catalogue.cm_id_field

        for e in entries:
            if isinstance(e, dict) and e.get(cm_field) == cm_id:
                return e
        return None

    def _find_entry_by_ref(self, cat_obj: dict, profile, ref: artifact_ref) -> Optional[dict]:
        """
        Resolve by (artifact_kind, artifact_id) if fields exist in profile.
        If profile doesn't define these fields, you can't do ref->cm reliably.
        """
        entries = self._entries(cat_obj, profile)
        if entries is None:
            return None

        kf = profile.cm_catalogue.artifact_kind_field
        idf = profile.cm_catalogue.artifact_id_field
        if not kf or not idf:
            return None

        for e in entries:
            if not isinstance(e, dict):
                continue
            if e.get(kf) == ref.kind and e.get(idf) == ref.id:
                return e
        return None

    def _entry_to_resolution(
        self,
        profile,
        entry: dict,
        default_id: str,
        default_kind: str = "cm_anchor",
    ) -> tuple[Optional[str], artifact_format, str, str]:
        rel = entry.get(profile.cm_catalogue.location_field)
        rel = rel if isinstance(rel, str) else None

        # format: prefer entry.format_field if present, else infer by extension
        fmt: artifact_format = infer_format_from_relpath(rel or "")
        ff = profile.cm_catalogue.format_field
        if ff:
            v = entry.get(ff)
            if isinstance(v, str) and v.lower() in ("yaml", "yml", "json", "md", "txt"):
                fmt = v.lower()  # type: ignore

        # kind/id: optional, but helpful
        kind = default_kind
        out_id = default_id

        kf = profile.cm_catalogue.artifact_kind_field
        if kf:
            kv = entry.get(kf)
            if isinstance(kv, str) and kv:
                kind = kv

        idf = profile.cm_catalogue.artifact_id_field
        if idf:
            iv = entry.get(idf)
            if isinstance(iv, str) and iv:
                out_id = iv

        return rel, fmt, kind, out_id

    def _fallback_glob_load(self, ref: artifact_ref) -> Optional[artifact_blob]:
        candidates = []
        for ext in (".yaml", ".yml", ".json", ".md", ".txt"):
            candidates.extend(self.repo_access.glob(f"**/{ref.id}{ext}"))

        if not candidates:
            return None

        rel = str(candidates[0])
        raw = self.repo_access.read_text(Path(rel))
        fmt = infer_format_from_relpath(rel)
        return artifact_blob(ref=ref, raw=raw, fmt=fmt, repo_relpath=rel)
