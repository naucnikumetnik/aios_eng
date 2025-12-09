"""
0v1 PromptCompiler for FDB / AIOS

- Input:  prompt_mapping artifact (as dict) + ArtifactStore
- Output: prompt_request artifact (as dict)

Deliberately dumb and explicit. No magic.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


# --------------------------------------------------------------------
# Artifact store abstraction
# --------------------------------------------------------------------

class ArtifactStore:
    """
    Abstract source of artifacts.

    In 0v1 we only need: given (ref, kind) -> return loaded artifact (dict).
    You can later back this with FDB index, DB, Git, whatever.
    """

    def get_artifact(self, ref: str, kind: str) -> Dict[str, Any]:
        raise NotImplementedError


class FileSystemArtifactStore(ArtifactStore):
    """
    Very simple filesystem-backed store:
    - ref is treated as a relative path under root.
    - If no extension is provided, '.yaml' is assumed.
    """

    def __init__(self, root: Path | str):
        self.root = Path(root)

    def get_artifact(self, ref: str, kind: str) -> Dict[str, Any]:
        # naive: ref is either "foo.yaml" or "foo.yml" or "foo"
        candidate = Path(ref)
        if not candidate.suffix:
            # assume .yaml
            candidate = candidate.with_suffix(".yaml")

        path = self.root / candidate
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # you *could* assert artifact_kind here if you like:
        # expected_kind = kind
        # if data.get("artifact_kind") != expected_kind:
        #     raise ValueError(f"Artifact {ref} kind={data.get('artifact_kind')} != expected {expected_kind}")
        return data


# --------------------------------------------------------------------
# Small helpers for dotted paths like "task_context.acceptance_criteria[0]"
# --------------------------------------------------------------------

_SEG_RE = re.compile(r"([^\[\]]+)(?:\[(\d+)\])?$")


def _ensure_list_len(lst: list, idx: int) -> None:
    while len(lst) <= idx:
        lst.append(None)


def get_by_path(root: Dict[str, Any], path: str) -> Any:
    """
    Read value from nested dict/list by dotted path with optional [index].
    Returns None if missing.
    """
    current: Any = root
    if not path:
        return current

    for segment in path.split("."):
        m = _SEG_RE.fullmatch(segment)
        if not m:
            raise ValueError(f"Invalid path segment: {segment!r}")

        key, idx = m.group(1), m.group(2)

        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None

        if idx is not None:
            if not isinstance(current, list):
                return None
            i = int(idx)
            if i >= len(current):
                return None
            current = current[i]

        if current is None:
            return None

    return current


def set_by_path(root: Dict[str, Any], path: str, value: Any, *, concat: bool = False) -> None:
    """
    Write value into nested dict/list by dotted path with optional [index].

    If concat=True and existing value is a string, new value is appended with
    two newlines. This is used for accumulating prompt text from multiple
    bindings targeting the same field.
    """
    current: Any = root
    segments = path.split(".")

    for i, segment in enumerate(segments):
        m = _SEG_RE.fullmatch(segment)
        if not m:
            raise ValueError(f"Invalid path segment: {segment!r}")

        key, idx = m.group(1), m.group(2)
        is_last = (i == len(segments) - 1)

        if idx is None:
            # dict access
            if not isinstance(current, dict):
                raise TypeError(f"Cannot index non-dict with key {key!r}")

            if is_last:
                if concat and key in current and isinstance(current[key], str):
                    current[key] = (current[key] + "\n\n" + str(value)) if value else current[key]
                else:
                    current[key] = value
                return
            else:
                if key not in current or current[key] is None:
                    current[key] = {}
                current = current[key]

        else:
            # list access
            if not isinstance(current, dict):
                raise TypeError(f"Cannot index non-dict with list key {key!r}")

            if key not in current or current[key] is None:
                current[key] = []
            lst = current[key]
            if not isinstance(lst, list):
                raise TypeError(f"Expected list at {key!r}, got {type(lst)}")

            idx_int = int(idx)
            _ensure_list_len(lst, idx_int)

            if is_last:
                existing = lst[idx_int]
                if concat and isinstance(existing, str):
                    lst[idx_int] = (existing + "\n\n" + str(value)) if value else existing
                else:
                    lst[idx_int] = value
                return
            else:
                if lst[idx_int] is None:
                    lst[idx_int] = {}
                current = lst[idx_int]


# --------------------------------------------------------------------
# Compiler
# --------------------------------------------------------------------

def load_prompt_mapping(path: Path | str) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _render_artifact_snippet(
    artifact: Any,
    artifact_path: str,
    render_mode: str,
    prefix: str = "",
    suffix: str = "",
) -> str:
    """
    0v1 snippet renderer:
    - render_mode == 'yaml_block' : YAML-dump the snippet
    - render_mode == 'inline'     : str(snippet)
    - render_mode == 'summary'    : same as yaml_block for now (can be upgraded later)
    """
    if artifact_path:
        snippet = get_by_path(artifact, artifact_path)
    else:
        snippet = artifact

    if render_mode == "yaml_block":
        yaml_text = yaml.safe_dump(snippet, sort_keys=False)
        body = yaml_text
    elif render_mode == "inline":
        body = str(snippet)
    elif render_mode == "summary":
        # TODO: smarter summarisation later
        yaml_text = yaml.safe_dump(snippet, sort_keys=False)
        body = yaml_text
    else:
        raise ValueError(f"Unsupported render_mode: {render_mode!r}")

    pieces = []
    if prefix:
        pieces.append(prefix.rstrip() + "\n")
    pieces.append(body.rstrip() + "\n")
    if suffix:
        pieces.append(suffix.strip() + "\n")

    return "".join(pieces).rstrip()  # final strip of trailing newlines


def compile_prompt_request(
    mapping: Dict[str, Any],
    store: ArtifactStore,
    *,
    input_overrides: Optional[Dict[str, Any]] = None,
    card_id_suffix: str = "",
) -> Dict[str, Any]:
    """
    Main entry point.

    - mapping: dict from prompt_mapping YAML
    - store:  ArtifactStore used to resolve inputs[*]
    - input_overrides: optional dict {input_id: artifact_dict} to bypass store for some inputs
    - card_id_suffix: optional suffix to make prompt_request.card.id unique per invocation
    """

    input_overrides = input_overrides or {}

    # 1) Resolve inputs
    resolved_inputs: Dict[str, Any] = {}
    for inp in mapping.get("inputs", []):
        input_id = inp["input_id"]
        kind = inp.get("kind", "")
        ref = inp.get("ref", "")
        required = bool(inp.get("required", True))

        if input_id in input_overrides:
            resolved_inputs[input_id] = copy.deepcopy(input_overrides[input_id])
            continue

        if not ref:
            if required:
                raise ValueError(f"Input {input_id!r} is required but has no 'ref' and no override.")
            else:
                resolved_inputs[input_id] = None
                continue

        artifact = store.get_artifact(ref=ref, kind=kind)
        resolved_inputs[input_id] = artifact

    # 2) Build base prompt_request skeleton
    card = mapping.get("card", {})
    prompt_request: Dict[str, Any] = {
        "artifact_kind": "prompt_request",
        "schema_version": "0.1",
        "card": {
            "id": (card.get("id") or mapping.get("card", {}).get("id") or "PR.UNNAMED")
                  + (card_id_suffix or ""),
            "name": card.get("name", "Prompt request from prompt_mapping"),
            "domain": card.get("domain", mapping.get("domain", "meta")),
            "scope": card.get("scope", mapping.get("scope", "")),
            "target_unit_id": mapping.get("target_unit_id", ""),
            "target_artifact_kind": mapping.get("target_artifact_kind", ""),
            "target_operation": mapping.get("target_operation", ""),
        },
        "system_context": {
            "description": "",
            "links": [],
            "assumptions": [],
        },
        "project_context": {
            "name": "",
            "domain": "",
            "id": "",
            "notes": "",
        },
        "task_context": {
            "name": "",
            "goal": "",
            "kind": "",
            "acceptance_criteria": [],
            "constraints": [],
            "notes": "",
        },
        "input_artifacts": [],  # optional; you can fill from resolved_inputs later if useful
        "prompt_template": {
            "system_prompt": "",
            "user_prompt": "",
            "assistant_instructions": "",
            "few_shot": [],
        },
        "llm_profile_ref": mapping.get("references", {}).get("default_llm_profile_ref", ""),
        "llm_overrides": mapping.get("llm_overrides", {}),
        "output_constraints": mapping.get("output_overrides", {}),
        "rendered_prompt": {
            "system_prompt": "",
            "user_prompt": "",
        },
        "tooling_metadata": mapping.get("tooling_metadata", {}),
        "traceability": mapping.get("traceability", {}),
    }

    # 3) Apply field_bindings
    for fb in mapping.get("field_bindings", []):
        target_field = fb["target_field"]
        source_type = fb["source_type"]

        if source_type == "literal":
            value = fb.get("literal_value", "")

        elif source_type == "artifact_snippet":
            input_id = fb["input_id"]
            artifact = resolved_inputs.get(input_id)
            if artifact is None:
                raise ValueError(f"artifact_snippet binding requires input {input_id!r}, but it was not resolved.")

            artifact_path = fb.get("artifact_path", "")
            render_mode = fb.get("render_mode", "yaml_block")
            prefix = fb.get("prefix", "")
            suffix = fb.get("suffix", "")

            value = _render_artifact_snippet(
                artifact=artifact,
                artifact_path=artifact_path,
                render_mode=render_mode,
                prefix=prefix,
                suffix=suffix,
            )

        else:
            raise ValueError(f"Unsupported source_type: {source_type!r}")

        # Concatenate if the same field is targeted multiple times
        set_by_path(prompt_request, target_field, value, concat=True)

    # 4) Copy final rendered prompts (0v1 = same as template text)
    prompt_request["rendered_prompt"]["system_prompt"] = prompt_request["prompt_template"]["system_prompt"]
    prompt_request["rendered_prompt"]["user_prompt"] = prompt_request["prompt_template"]["user_prompt"]

    return prompt_request
