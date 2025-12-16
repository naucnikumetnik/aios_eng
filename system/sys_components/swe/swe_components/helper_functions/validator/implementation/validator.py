# core/validator/implementation/validator_engine.py
from __future__ import annotations

import re
from typing import Any

from system.sys_components.swe.swe_components.helper_functions.path_selectors.path_selectors import get_by_internal_path
from system.sys_components.swe.swe_interfaces.implementation.if_validator import (
    validator_port,
    validation_issue,
    validation_result,
)


class validator_engine(validator_port):
    def validate_fields(self, fields_spec: dict, produced_body: dict) -> validation_result:
        issues: list[validation_issue] = []

        for field_path, spec in (fields_spec or {}).items():
            # values are in produced_body; your spec keys are like "task_metadata.task_id"
            value = get_by_internal_path(produced_body, field_path)

            for v in (spec or {}).get("validators", []) or []:
                rule_id = v.get("id", "VAL-UNKNOWN")
                rule = v.get("rule", "")

                if rule == "not_empty":
                    if value is None or (isinstance(value, str) and value.strip() == "") or (isinstance(value, list) and len(value) == 0):
                        issues.append(validation_issue(field_path, rule_id, "not_empty failed"))

                elif rule == "matches":
                    pattern = ((v.get("params") or {}).get("pattern")) or ""
                    if isinstance(value, str) and pattern and re.match(pattern, value) is None:
                        issues.append(validation_issue(field_path, rule_id, f"matches failed: {pattern}"))

                elif rule == "in_enum":
                    enum = (spec or {}).get("enum") or []
                    if enum and value not in enum:
                        issues.append(validation_issue(field_path, rule_id, f"in_enum failed: {value}"))

                elif rule == "min_length":
                    n = int(((v.get("params") or {}).get("n")) or 0)
                    if not isinstance(value, list) or len(value) < n:
                        issues.append(validation_issue(field_path, rule_id, f"min_length failed: n={n}"))

                else:
                    # ignore unknown rules for now (tighten later if you want)
                    pass

        return validation_result(ok=(len(issues) == 0), issues=issues)
