# if_target_repo_access.py
# SoS-level interface: Target Repository Access (how to read/write/list in the target repo)
# Typical consumer: ArtifactEngine 

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Optional, Sequence


# --- Keep compatible with your style -------------------------------------------------

@dataclass(frozen=True)
class artifact_ref:
    kind: str        # "udd|arch_desc|interface|task|trace|..."
    id: str          # e.g. "UDD-AIOS-SCHED-01"


@dataclass(frozen=True)
class artifact_content:
    ref: artifact_ref
    raw_content: Optional[str]     # text content (yaml/json/md). None if missing/unreadable.


# --- Repo access port ----------------------------------------------------------------
# Notes:
# - file_path parameters are expected to be repo-relative Paths (preferred).
#   Implementations MAY accept absolute paths if they are under repo_root, but that is optional.
# - load/save resolve artifact_ref -> repo path using the active TargetRepoProfile rules
#   (e.g., artifact_locations + naming rules, or cm_catalogue), but that logic is inside the provider.

class target_repo_access_port(Protocol):
    # --- Identity / context ----------------------------------------------------------

    def get_repo_root(self) -> Path:
        """Return the configured root directory of the target repo (worktree root)."""
        ...

    # --- Artifact-level operations (compatible with your artifact_store_port) --------

    def resolve_artifact_path(self, ref: artifact_ref) -> Path:
        """
        Resolve an artifact_ref to a repo-relative path (preferred) or absolute path.
        Resolution policy is defined by IF-TargetRepoProfile (artifact_locations / cm_catalogue).
        """
        ...

    def exists(self, ref: artifact_ref) -> bool:
        """True if the resolved artifact path exists."""
        ...

    def load(self, ref: artifact_ref) -> artifact_content:
        """
        Load text content of the artifact identified by (kind,id).
        If not found, return artifact_content(ref, raw_content=None).
        """
        ...

    def save(self, artifact: artifact_content) -> None:
        """
        Save text content for artifact.ref at its canonical location.
        Implementations should create parent directories as needed.
        """
        ...

    # --- Path-level operations (plumbing used by adapters/engines) -------------------

    def path_exists(self, file_path: Path) -> bool:
        """True if file_path exists (repo-relative preferred)."""
        ...

    def read_text(self, file_path: Path, encoding: str = "utf-8") -> str:
        """Read a text file at file_path."""
        ...

    def write_text(
        self,
        file_path: Path,
        content: str,
        encoding: str = "utf-8",
        create_parents: bool = True,
        overwrite: bool = True,
    ) -> None:
        """Write a text file at file_path."""
        ...

            
        """List direct children of dir_path (repo-relative preferred)."""
        ...

    def glob(self, pattern: str) -> Sequence[Path]:
        """
        Glob paths under repo_root using pattern (e.g. '**/*.yaml').
        Return repo-relative paths when possible.
        """
        ...

    def delete_path(self, file_path: Path, missing_ok: bool = True) -> None:
        """Delete a file (or empty dir if you allow); missing_ok avoids raising."""
        ...

    def move_path(self, src: Path, dst: Path, overwrite: bool = False) -> None:
        """Move/rename a path within the repo."""
        ...

    # --- Patch/edit operation (kept compatible with your current usage) --------------

    def modify_artifact(self, file_path: Path, edit_type: str, data) -> bool:
        """
        Apply a structured edit to an artifact at file_path.
        Return True if something changed, False if no-op.

        Examples (you define these semantics):
          - edit_type='set_json_path', data={'path': 'a.b[0].c', 'value': 123}
          - edit_type='yaml_merge', data={'overlay': {...}}
          - edit_type='append_text', data={'text': '...'}
        """
        ...
