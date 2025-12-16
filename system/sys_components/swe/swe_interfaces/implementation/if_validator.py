# core/validator/design/interfaces/if_validator.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class validation_issue:
    field: str
    rule_id: str
    message: str


@dataclass(frozen=True)
class validation_result:
    ok: bool
    issues: list[validation_issue]


class validator_port(Protocol):
    def validate_fields(self, fields_spec: dict, produced_body: dict) -> validation_result: ...
