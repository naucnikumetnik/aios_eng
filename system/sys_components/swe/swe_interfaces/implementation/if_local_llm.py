from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence, Mapping, Any
from enum import Enum
from system.sys_components.swe.swe_interfaces.implementation.if_agent_configurator import llm_config

# Error model for Local LLMs
class LlmErrorCategory(str, Enum):
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    INTERNAL = "internal"
    TRANSPORT = "transport"


class LlmErrorSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(frozen=True)
class LlmErrorInfo:
    code: str
    description: str
    category: LlmErrorCategory
    severity: LlmErrorSeverity
    recoverable: bool


class LocalLlmError(RuntimeError):
    """
    Error raised by LocalLlmPort implementations.

    code/category/severity/recoverable map 1:1 to interface_spec.error_model.
    """

    def __init__(
        self,
        info: LlmErrorInfo,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(info.description)
        self.info = info
        self.details = dict(details or {})


# you can optionally generate a registry from the YAML error_model
KNOWN_LLM_ERRORS: dict[str, LlmErrorInfo] = {
    # filled from interface_spec:
    # "MODEL_NOT_FOUND": LlmErrorInfo(...),
    # "TIMEOUT": LlmErrorInfo(...),
    # ...
}

# Success model for Local LLMs

@dataclass(frozen=True)
class llm_answer:
    execution_time: float
    generation_speed: float # tokens per second
    response_text: str

class local_llm_port (Protocol):
    def trigger_local_llm (self, prompt: str, settings: llm_config) -> llm_answer:
        ...