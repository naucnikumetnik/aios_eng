# core/task_compiler/implementation/task_compiler.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List

from system.sys_components.swe.swe_interfaces.implementation.if_artifact_manager import artifact_engine_port, artifact_ref
from system.sys_components.swe.swe_interfaces.implementation.if_document_codec import document_codec_port, artifact_blob as codec_blob
from system.sys_components.swe.swe_interfaces.implementation.if_validator import validator_port
from system.sys_components.swe.swe_components.helper_functions.path_selectors.path_selectors import get_by_internal_path, set_by_dotted_path


def apply_mode(mode: str, extracted: Any) -> Any:
    if mode == "copy":
        return extracted
    if mode == "copy_list":
        if extracted is None:
            return []
        return extracted if isinstance(extracted, list) else [extracted]
    if mode == "copy_list_unique":
        if extracted is None:
            return []
        if not isinstance(extracted, list):
            return [extracted]
        out, seen = [], set()
        for x in extracted:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out
    raise ValueError(f"Unsupported mapping mode: {mode}")


@dataclass
class task_compiler:
    artifact_engine: artifact_engine_port
    codec: document_codec_port
    validator: validator_port

    mapping_bundle_ref: artifact_ref
    project_ref: Optional[artifact_ref] = None

    def compile_task(self, task_order: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        errors: List[str] = []

        mb = self._load_structured(self.mapping_bundle_ref) 
        fields_spec = (mb or {}).get("fields", {}) or {}

        unit_id = task_order.get("unit_id")
        if not unit_id:
            return ({}, ["task_order.unit_id missing"])

        unit = self._load_structured(artifact_ref(kind="unit_detailed_design", id=str(unit_id)))
        project = self._load_structured(self.project_ref) if self.project_ref else None

        # context available to mappings
        ctx: Dict[str, Any] = {
            "task_order": task_order,
            "unit_detailed_design": unit,
        }
        if project is not None:
            ctx["project"] = project

        task: Dict[str, Any] = {
            "metadata": {"schema_version": (mb or {}).get("metadata", {}).get("schema_version", "0v1")},
            "body": {},
        }

        for field_path, spec in fields_spec.items():
            mapping = (spec or {}).get("mapping") or {}
            sources = mapping.get("sources") or []
            mode = mapping.get("mode") or "copy"

            if not sources:
                continue

            # your current mapping style maps each leaf field with exactly one source
            src = sources[0]
            kind = src.get("artifact_kind")
            internal_path = src.get("internal_artifact_path") or ""

            if not kind:
                continue

            if kind not in ctx:
                errors.append(f"{field_path}: missing context for artifact_kind='{kind}'")
                continue

            extracted = get_by_internal_path(ctx[kind], internal_path)
            value = apply_mode(mode, extracted)

            # if you map list ids into "...[].id" fields, convert ["A","B"] -> [{"id":"A"},{"id":"B"}]
            if field_path.endswith("[].id") and isinstance(value, list):
                value = [{"id": v} for v in value]

            set_by_dotted_path(task["body"], field_path, value)

        # validation as a shared service
        vr = self.validator.validate_fields(fields_spec, task["body"])
        if not vr.ok:
            errors.extend([f"{i.field}: {i.message} ({i.rule_id})" for i in vr.issues])

        return task, errors

    def _load_structured(self, ref: Optional[artifact_ref]) -> Dict[str, Any]:
        if ref is None:
            return {}
        blob = self.artifact_engine.load_by_ref(ref)
        if blob is None:
            return {}
        obj = self.codec.decode(codec_blob(kind=ref.kind, id=ref.id, raw=blob.raw, fmt=blob.fmt, repo_relpath=blob.repo_relpath))
        return obj if isinstance(obj, dict) else {}
