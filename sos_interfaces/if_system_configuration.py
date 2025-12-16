# if_target_repo_profile.py
# SoS-level interface: Target Repository Profile (policy/contract), not read/write access.
# Consumers: typically ArtifactEngine

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Protocol, Sequence, Literal, Tuple


@dataclass (frozen=True)
class system_config:
    restore_v_create: str
    checkpoint: Path
    execute_v_implement: str
    architecture_v_unit: str
    architecture_v_unit_path: Path
    review_required: bool
    tests_required: bool
    resources: resources_data
    orga: Path
    project_path: Path

RepoKind = Literal["filesystem", "git_worktree", "git_bare", "object_store", "other"]
Severity = Literal["info", "warning", "error"]
PathKind = Literal["file", "dir", "glob"]


@dataclass(frozen=True)
class repo_path_rule:
    """
    Declarative rule describing required repo paths/structure.
    Example: kind="dir", path="project/configuration_management"
    Example: kind="glob", path="**/*.yaml"
    """
    id: str
    kind: PathKind
    path: str                      # relative to repo_root
    description: str = ""
    required: bool = True


@dataclass(frozen=True)
class artifact_location_rule:
    """
    Where a given artifact kind is expected to live, and how it is named.
    You can keep this minimal and evolve later.
    """
    artifact_kind: str             # e.g. "unit_detailed_design", "interface_spec"
    base_dir: str                  # e.g. "project/design/udd"
    file_extensions: Tuple[str, ...] = (".yaml", ".yml", ".json")
    naming_pattern: str = ""       # optional regex-ish string (not enforced here)


@dataclass(frozen=True)
class cm_catalogue_profile:
    # where the catalogue lives
    catalogue_relpath: str         # e.g. "project/configuration_management/cm_catalogue.yaml"

    # how entries are represented
    entries_list_key: str          # e.g. "entries"

    # required for CM-anchor resolution
    cm_id_field: str               # e.g. "cm_id"
    location_field: str            # e.g. "location" (repo-relative)
    format_field: Optional[str] = "format"          # optional
    artifact_kind_field: Optional[str] = "artifact_kind"  # optional
    artifact_id_field: Optional[str] = "artifact_id"      # optional



@dataclass(frozen=True)
class target_repo_profile:
    profile_id: str
    profile_version: str
    repo_kind: RepoKind
    cm_catalogue: cm_catalogue_profile



@dataclass(frozen=True)
class validation_issue:
    severity: Severity
    rule_id: str
    message: str
    path: Optional[str] = None     # relative path involved (if any)


@dataclass(frozen=True)
class target_repo_validation_result:
    repo_root: Path
    profile_id: str
    ok: bool
    issues: Tuple[validation_issue, ...] = ()


@dataclass(frozen=True)
class cm_anchor_resolution:
    """
    Result of resolving a cm_anchor_id/cm_id to a concrete file/directory location in the repo.
    """
    cm_anchor_id: str
    resolved_relpath: str          # relative to repo_root
    exists: bool = False
    notes: str = ""

@dataclass(frozen=True)
class resources_data:
    gpu_count: int
    gpu_name: str | None                  # "RTX 5080"
    gpu_vram_gb: float              # 16.0
    gpu_compute_capability: str | None    # "8.9" or similar, if CUDA
    gpu_supports_fp16: bool
    gpu_supports_bf16: bool
    gpu_supports_cuda: bool

    cpu_model: str                  # "i9-14900KF"
    cpu_physical_cores: int | None
    cpu_logical_cores: int | None          # threads
    cpu_base_clock_ghz: float | None     # optional but nice
    cpu_has_avx2: bool | None
    cpu_has_avx512: bool | None

    ram_total_gb: float
    ram_available_gb: float         # at runtime, optional in static config

    storage_type: str               # "nvme", "ssd", "hdd"
    storage_read_mb_s: float | None       # rough benchmark, optional
    storage_free_gb: float


class target_repo_profile_port(Protocol):
    """
    Port for obtaining and applying a TargetRepoProfile.
    Typical provider: RepoProfileProvider (config loader).
    Typical consumer: ArtifactEngine / RepoAdapter.
    """

    def get_profile(self) -> target_repo_profile: 
        """
        Return the active target repo profile (policy contract).
        """
        ...

    def validate_repo_against_profile(self, repo_root: Path, profile: target_repo_profile) -> target_repo_validation_result:
        """
        Check whether repo_root satisfies profile.required_paths and basic conventions.
        (No file reading is required here, unless you choose to validate cm_catalogue presence.)
        """
        ...

    def resolve_cm_anchor(self, repo_root: Path, profile: target_repo_profile, cm_anchor_id: str) -> cm_anchor_resolution:
        """
        Resolve a CM anchor (cm_id / cm_anchor_id) to a repo-relative path,
        according to profile.cm_catalogue rules.
        """
        ...
    