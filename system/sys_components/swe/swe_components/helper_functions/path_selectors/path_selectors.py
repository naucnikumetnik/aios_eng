# core/utils/path_selectors.py
from __future__ import annotations

from typing import Any


def normalize_internal_path(p: str) -> str:
    # Treat your "[i]" as wildcard
    return p.replace("[i]", "[*]")


def get_by_internal_path(obj: Any, path: str) -> Any:
    """
    Minimal JSONPath-like selector:
      - dot notation: a.b.c
      - list wildcard: a.b[*].id
    If wildcard yields list, next tokens map across that list.
    """
    path = normalize_internal_path(path)
    if not path:
        return obj

    tokens = path.split(".")
    cur = obj

    for t in tokens:
        if cur is None:
            return None

        # wildcard token
        if t.endswith("[*]"):
            key = t[:-3]
            if not isinstance(cur, dict):
                return None
            cur = cur.get(key)
            if not isinstance(cur, list):
                return None
            continue

        # map over list
        if isinstance(cur, list):
            nxt = []
            for item in cur:
                if isinstance(item, dict):
                    nxt.append(item.get(t))
                else:
                    nxt.append(None)
            cur = nxt
            continue

        # dict step
        if isinstance(cur, dict):
            cur = cur.get(t)
            continue

        return None

    return cur


def set_by_dotted_path(root: dict, dotted_path: str, value: Any) -> None:
    """
    Set into dict using dot notation. Supports segments ending with [] by ensuring a list exists
    and writing into first element dict.
    Example:
      set_by_dotted_path(body, "task_metadata.assignees.responsible[].name", "Jane")
    """
    parts = dotted_path.split(".")
    cur: Any = root
    for i, seg in enumerate(parts):
        last = i == len(parts) - 1
        is_list = seg.endswith("[]")
        key = seg[:-2] if is_list else seg

        if is_list:
            if key not in cur or not isinstance(cur[key], list):
                cur[key] = []
            if last:
                cur[key] = value if isinstance(value, list) else [value]
                return
            if len(cur[key]) == 0 or not isinstance(cur[key][0], dict):
                cur[key].append({})
            cur = cur[key][0]
            continue

        if last:
            cur[key] = value
            return

        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]
