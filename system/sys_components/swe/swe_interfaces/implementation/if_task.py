from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Sequence, Callable, List, Optional
from enum import Enum
from datetime import datetime

#events
class task_status(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class task_status_event:
    event_id: str               # could map to dynamic_view.events[*].id + UUID
    task_instance_id: str
    old_status: task_status
    new_status: task_status
    occurred_at: datetime
    reason: str | None = None

@dataclass
class task_order:
    unit_path: Path
    batch_num: int
    input_set: str
    execute_v_implement: str

# ---------------------------------------------------------------------------
# Information item metadata
# ---------------------------------------------------------------------------

@dataclass
class identity:
    id: str
    name: str
    classification: Optional[str] = None


@dataclass
class person_ref:
    name: str
    role: Optional[str] = None


@dataclass
class authorship:
    author: Optional[person_ref] = None
    approver: Optional[person_ref] = None


@dataclass
class change_record:
    version: str
    date: Optional[datetime] = None
    author: Optional[str] = None
    note: Optional[str] = None


@dataclass
class access_control:
    level: Optional[str] = None
    group: Optional[str] = None


@dataclass
class information_item_metadata:
    """
    Only stuff about this task as an information item.
    """
    metadata_template_version: Optional[str] = None
    identity: Optional[identity] = None
    work_item_status: Optional[str] = None
    authorship: Optional[authorship] = None
    change_history: List[change_record] = field(default_factory=list)
    access_control: Optional[access_control] = None


# ---------------------------------------------------------------------------
# Task metadata
# ---------------------------------------------------------------------------

@dataclass
class assignee:
    """
    RACI-like assignee; type = "human" | "agent" | ...
    """
    id: str
    type: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None


@dataclass
class assignee_set:
    responsible: List[assignee] = field(default_factory=list)
    accountable: List[assignee] = field(default_factory=list)
    consulted: List[assignee] = field(default_factory=list)
    informed: List[assignee] = field(default_factory=list)


@dataclass
class requirement_ref:
    id: str


@dataclass
class component_ref:
    id: str


@dataclass
class task_dependency:
    id: str
    type: Optional[str] = None


@dataclass
class traceability:
    domain_requirements: List[requirement_ref] = field(default_factory=list)
    domain_component: List[component_ref] = field(default_factory=list)
    task_dependencies: List[task_dependency] = field(default_factory=list)


@dataclass
class schedule:
    planned_start: Optional[datetime] = None
    planned_finish: Optional[datetime] = None


@dataclass
class task_metadata:
    task_id: str
    unit_type: Optional[str] = None
    task_name: Optional[str] = None
    task_template_version: Optional[str] = None
    task_level: Optional[str] = None
    conformance: Optional[str] = None  # org/project policy IDs; refine later
    integrity_level: Optional[str] = None
    assignees: assignee_set = field(default_factory=assignee_set)
    priority: Optional[int] = None
    traceability: traceability = field(default_factory=traceability)
    schedule: schedule = field(default_factory=schedule)
    lifecycle: Optional[str] = None
    iteration: Optional[int] = None


# ---------------------------------------------------------------------------
# Guideline, controls, enablers
# ---------------------------------------------------------------------------

@dataclass
class enabler:
    enabler_cm_anchor_id: str
    name: Optional[str] = None
    type: Optional[str] = None
    purpose: Optional[str] = None


@dataclass
class thinking_checklist_bundle:
    id: str
    storage_cm_anchor_id: Optional[str] = None


@dataclass
class method_control_bundle:
    id: str
    storage_cm_anchor_id: Optional[str] = None
    enablers: List[enabler] = field(default_factory=list)


@dataclass
class guideline:
    description: Optional[str] = None
    steps: Optional[str] = None  # algorithm / pseudo-code / narrative
    thinking_checklist_bundle: Optional[thinking_checklist_bundle] = None
    method_control_bundles: List[method_control_bundle] = field(default_factory=list)
    enablers: List[enabler] = field(default_factory=list)  # general task enablers


# ---------------------------------------------------------------------------
# Inputs / outputs
# ---------------------------------------------------------------------------

@dataclass
class input_primary:
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    storage_cm_anchor_id: Optional[str] = None


@dataclass
class hysteresis_record:
    failure_record_id: str
    failure_type: Optional[str] = None
    corrective_action_ref: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class inputs:
    primary: List[input_primary] = field(default_factory=list)
    hysteresis: List[hysteresis_record] = field(default_factory=list)


@dataclass
class control_bundle:
    id: str
    storage_cm_anchor_id: Optional[str] = None
    enablers: List[enabler] = field(default_factory=list)


@dataclass
class output_formatting:
    format_type: Optional[str] = None
    control_bundles: List[control_bundle] = field(default_factory=list)


@dataclass
class output_styling:
    control_bundles: List[control_bundle] = field(default_factory=list)


@dataclass
class template_ref:
    storage_cm_anchor_id: str
    enablers: List[enabler] = field(default_factory=list)


@dataclass
class example_ref:
    storage_cm_anchor_id: str


@dataclass
class output_definition:
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    storage_cm_anchor_id: Optional[str] = None
    formatting: Optional[output_formatting] = None
    styling: Optional[output_styling] = None
    template: Optional[template_ref] = None
    example: Optional[example_ref] = None
    bad_example: Optional[example_ref] = None


# ---------------------------------------------------------------------------
# Acceptance criteria
# ---------------------------------------------------------------------------

@dataclass
class acceptance_criterion:
    id: str
    outcome: Optional[str] = None
    measure: Optional[str] = None
    evidence: Optional[str] = None
    reference: Optional[str] = None


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

@dataclass
class review_stack_item:
    type: Optional[str] = None
    tool: Optional[str] = None
    mode: Optional[str] = None


@dataclass
class review_roles:
    reviewers: List[str] = field(default_factory=list)
    approvers: List[str] = field(default_factory=list)


@dataclass
class disposition_policy:
    severity_classes: List[str] = field(default_factory=list)
    waiver_approval_roles: List[str] = field(default_factory=list)


@dataclass
class review_control_pack:
    id: str


@dataclass
class review:
    objective: Optional[str] = None
    scope_artifacts: List[str] = field(default_factory=list)
    review_stack: List[review_stack_item] = field(default_factory=list)
    independence_level: Optional[str] = None
    roles: review_roles = field(default_factory=review_roles)
    coverage: Optional[str] = None
    evidence_to_capture: Optional[str] = None
    disposition_policy: Optional[disposition_policy] = None
    exit_criteria: Optional[str] = None
    control_packs: List[review_control_pack] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Task run logs & notes
# ---------------------------------------------------------------------------

@dataclass
class task_run_log:
    log_id: str
    description: Optional[str] = None
    storage_cm_anchor_id: Optional[str] = None


@dataclass
class note:
    note_id: str
    note_owner: Optional[str] = None
    text: Optional[str] = None
    links: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Root "Task" / "TaskSpec" object
# ---------------------------------------------------------------------------

@dataclass
class task_spec:
    information_item_metadata: information_item_metadata
    task_metadata: task_metadata
    guideline: Optional[guideline] = None
    inputs: inputs = field(default_factory=inputs)
    outputs: List[output_definition] = field(default_factory=list)
    acceptance_criteria: List[acceptance_criterion] = field(default_factory=list)
    review: Optional[review] = None
    task_run_logs: List[task_run_log] = field(default_factory=list)
    notes: List[note] = field(default_factory=list)


class request_task_port (Protocol):
    def compile_task (self, task_order: task_order) -> task_spec:
        ...

class task_lifecycle_port(Protocol):
    def publish(self, event: task_status_event) -> None:
        """Used by TaskExecutor / ArtifactEngine to emit events."""
        ...
    def subscribe(self, handler: Callable[[task_status_event], None]) -> None:
        """Used by Scheduler to listen for status changes."""
        ...
    def unsubscribe(self, handler: Callable[[task_status_event], None]) -> None:
        """Used by Scheduler to stop listening for status changes."""
        ...