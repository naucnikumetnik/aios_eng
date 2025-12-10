# Coding Standard (Design → Code Mapping)

This document defines how design artifacts (arch_desc, structural, dynamic, deployment, UDD, interface_spec) map into Python code for AIOS meta-components.

The goal: **every important design ID has an obvious place in code, and every important piece of code points back to design.**

---

## 1. Design IDs & Trace Tags

### 1.1 ID forms (design-side)

Design artifacts use IDs like:

- Architecture: `AD-*`
- Structural view: `SV-*`
- Dynamic view: `DV-*`
- Deployment view: `DEP-*`
- Component: `CMP-*`
- UDD: `UDD-*`
- Interface: `IF-*`
- Payload: `PL-*`
- Operation: `OP-*`
- Requirement: `REQ-*`
- Concern: `C-*`
- Constraint: `CONST-*`
- Condition: `COND-*`
- Action: `ACT-*`
- Event: `EV-*`
- Scenario: `SCN-*`
- Decision record: `DR-*`
- Verification hint: `VH-*`

### 1.2 Code trace tags (docstring-level)

In Python, these IDs appear in docstrings as **structured tags**:

```python
"""
[UDD:UDD-AIOS-SCHED-01]
[COMPONENT:CMP-Scheduler]
[IF:IF-SCHED-Control.OP-create_execution_plan]
[REQ:REQ-SCHED-PLAN-001]
[SCN:SCN-SCHED-PlanHappyPath]
"""

Rules:

    Format: [KIND:ID] (no extra syntax).

    Multiple tags allowed per docstring.

    These tags are the primary anchor for trace scripts (grep / AST tools).

1.3 Code trace decorator (function-level)

For machine-readable trace, we use a standard decorator.

File: aios/common/tracing.py

from typing import Callable, Any

def impl_of(*design_ids: str):
    """Attach design IDs (reqs, ops, scenarios, etc.) to a function or method."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        setattr(fn, "__design_ids__", design_ids)
        return fn
    return decorator

Usage:

from aios.common.tracing import impl_of

class Scheduler:
    @impl_of("IF:IF-SCHED-Control.OP-create_execution_plan",
             "REQ:REQ-SCHED-PLAN-001",
             "SCN:SCN-SCHED-PlanHappyPath")
    def create_execution_plan(self, ...) -> ExecutionPlan:
        ...

    Decorator is recommended for key methods.

    Docstring tags are the human-facing mirror.

2. Repository Layout (Meta Layer)

Recommended layout for Python meta-components:

aios/
  common/
    __init__.py
    tracing.py              # impl_of decorator, common helpers

  meta/
    __init__.py             # system-level tags

    interfaces/
      __init__.py
      if_scheduler_control.py
      if_task_dispatch.py
      if_task_lifecycle_events.py
      # more IF-* as needed

    scheduler/
      __init__.py
      scheduler_core.py     # CMP-Scheduler implementation
      scheduler_app.py      # CLI / entrypoint adapter (boundary)

    task_compiler/
      __init__.py
      task_compiler_core.py # CMP-TaskCompiler implementation

    artifact_engine/
      __init__.py
      artifact_engine_core.py  # CMP-ArtifactEngine implementation

tests/
  meta/
    test_scn_sched_plan_happy_path.py
    # etc

    One component → one core module (*_core.py) under aios/meta/<component>/.

    One interface_spec → one interface module under aios/meta/interfaces/.

3. Architecture Description → Packages / Modules

Artifact: architecture_description

    card.id, system_of_interest → top-level package docstring.

File: aios/meta/__init__.py

"""
AIOS Meta System

[ARCH_DESC:AD-FDB-ARCHDESC-ENGINE]
[SYSTEM:aios.meta]
"""

    design_rationale, concerns, constraints, decision_log:

        Stay in design docs.

        Only referenced in code when they explain non-obvious behavior, e.g.:

        """
        [CONCERN:C-AD-CONSISTENCY]
        [DR:DR-AIOS-SCHED-PRIORITY-01]
        """

No direct additional code structure is mandated by arch_desc.
4. Structural View → Components, Ports, Connectors

Artifact: structural_view
4.1 Components → modules + classes

Each components[*] entry:

    id: CMP-Scheduler

        Module: aios/meta/scheduler/scheduler_core.py

        Class: Scheduler

Module docstring:

"""
Scheduler component.

[COMPONENT:CMP-Scheduler]
[STRUCT_VIEW:SV-AIOS-meta-struct]
"""

Same pattern for:

    CMP-TaskCompiler → aios/meta/task_compiler/task_compiler_core.py → class TaskCompiler

    CMP-ArtifactEngine → aios/meta/artifact_engine/artifact_engine_core.py → class ArtifactEngine

4.2 Ports → interface_spec + Protocols

Each structural port:

    interface_ref: "IF-SCHED-Control" → interface_spec → Python module:

    File: aios/meta/interfaces/if_scheduler_control.py

    """
    Scheduler Control Interface

    [IF:IF-SCHED-Control]
    [SYSTEM:aios.meta]
    [STRUCT_VIEW:SV-AIOS-meta-struct]
    """

    from dataclasses import dataclass
    from typing import Protocol

    @dataclass(frozen=True)
    class SchedulerRunConfig:
        """
        [PAYLOAD:PL-SchedulerRunConfig]
        """
        scope_flag: bool
        review_flag: bool
        test_flag: bool
        execution_flag: bool
        log_flag: bool


    @dataclass(frozen=True)
    class ExecutionPlan:
        """
        [PAYLOAD:PL-ExecutionPlan]
        """
        id: str
        # fields TBD


    class SchedulerPort(Protocol):
        def create_execution_plan(self, config: SchedulerRunConfig) -> ExecutionPlan:
            """
            [IF:IF-SCHED-Control.OP-create_execution_plan]
            kind: command
            """
            ...

Mapping rule:

    data_semantics.payloads[*] → @dataclass definitions.

    operations[*] → Protocol methods.

4.3 Connectors → composition/wiring

Artifact: connectors[*] (structural view)

    Implement wiring in composition modules, not in core units.

File: aios/meta/composition.py (or similar)

"""
Composition / wiring for meta components.

[STRUCT_VIEW:SV-AIOS-meta-struct]
[CONNECTOR:CONN-SCHED-to-TC]
"""

from aios.meta.scheduler.scheduler_core import Scheduler, SchedulerConfig
from aios.meta.task_compiler.task_compiler_core import TaskCompiler
from aios.meta.interfaces.if_scheduler_control import SchedulerRunConfig

def build_scheduler(config: SchedulerConfig) -> Scheduler:
    task_compiler = TaskCompiler(...)
    scheduler = Scheduler(
        config=config,
        task_dispatch_port=task_compiler,   # TaskCompiler implements the port
        events_port=...,
    )
    return scheduler

5. Dynamic View → Events, States, Scenarios

Artifact: dynamic_view
5.1 Events → event types + event bus port

Dynamic view events[*] map to:

    dataclasses

    event bus Protocols

File: aios/meta/interfaces/if_task_lifecycle_events.py

"""
Task lifecycle events interface.

[IF:IF-TaskLifecycleEvents]
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol, Callable


class TaskStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TaskStatusEvent:
    """
    [EVENT:EV-task_status_change]
    """
    event_id: str
    task_instance_id: str
    old_status: TaskStatus
    new_status: TaskStatus
    occurred_at: datetime
    reason: str | None = None


class TaskLifecycleEventsPort(Protocol):
    def publish(self, event: TaskStatusEvent) -> None:
        ...
    def subscribe(self, handler: Callable[[TaskStatusEvent], None]) -> None:
        ...

Producers (e.g. TaskExecutor or ArtifactEngine) call publish.
Consumers (e.g. Scheduler) call subscribe.
5.2 Conditions → predicates

Dynamic view conditions[*] → predicate helpers.

Example:

def is_task_completed(event: TaskStatusEvent) -> bool:
    """
    [COND:COND-status_completed]
    """
    return event.new_status == TaskStatus.COMPLETED

5.3 Actions → side-effect functions/methods

Dynamic view actions[*] → functions that produce effects.

Example:

def schedule_next_task(plan: ExecutionPlan, completed_task_id: str) -> None:
    """
    [ACTION:ACT-schedule_next_task]
    """
    ...

5.4 State dynamics → enums + transition logic

Dynamic view state_dynamics → state enums and transition logic.

Example (TaskInstance state):

from enum import Enum

class TaskInstanceState(str, Enum):
    """
    [STATE_SUBJECT:SUBJ-TaskInstance]
    """
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

Transitions are implemented in the component that owns the lifecycle (e.g. TaskExecutor or Scheduler).
5.5 Scenarios → tests

Dynamic view scenarios[*] map to scenario tests.

File: tests/meta/test_scn_sched_plan_happy_path.py

def test_scn_sched_plan_happy_path():
    """
    [SCN:SCN-SCHED-PlanHappyPath]
    [DYNAMIC_VIEW:DV-AIOS-SCHED-task_lifecycle]
    """
    # step 1: build scheduler + task executor
    # step 2: create plan
    # step 3: simulate task completion event
    # step 4: assert scheduler dispatches next task
    ...

6. UDD → Unit Implementation

Artifact: unit_detailed_design

Main mapping target: *_core.py module.
6.1 Card & basic tags

Top of aios/meta/scheduler/scheduler_core.py:

"""
Scheduler unit.

[UDD:UDD-AIOS-SCHED-01]
[COMPONENT:CMP-Scheduler]
[STRUCT_VIEW:SV-AIOS-meta-struct]
"""

6.2 Config parameters → config dataclass

UDD config_parameters map to a config dataclass:

from dataclasses import dataclass

@dataclass(frozen=True)
class SchedulerConfig:
    """
    [UDD:UDD-AIOS-SCHED-01]
    """
    scope_flag: bool
    review_flag: bool
    test_flag: bool
    execution_flag: bool
    log_flag: bool

Boundary adapter (e.g. CLI) is responsible for constructing this.

File: aios/meta/scheduler/scheduler_app.py:

import argparse
from aios.meta.scheduler.scheduler_core import Scheduler, SchedulerConfig

def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", action="store_true")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--log", action="store_true", default=True)
    return parser

def main(argv=None) -> None:
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    config = SchedulerConfig(
        scope_flag=args.scope,
        review_flag=args.review,
        test_flag=args.test,
        execution_flag=args.execute,
        log_flag=args.log,
    )

    scheduler = Scheduler(config=config, task_dispatch_port=..., events_port=...)
    plan = scheduler.create_execution_plan()
    scheduler.monitor_and_adjust(plan)

if __name__ == "__main__":
    main()

6.3 External ports → method bindings

UDD ports.external[*] should have binding entries pointing to the actual Python methods.

Example from UDD:

ports:
  external:
    - port_ref: "PORT-SCHED-control"
      direction: "provider"
      interface_ref: "IF-SCHED-Control"
      binding:
        - source_artifact_ref: "aios/meta/scheduler/scheduler_core.py"
          binding_kind: "method"
          element_name: "Scheduler.create_execution_plan"

Code:

from aios.meta.interfaces.if_scheduler_control import (
    SchedulerPort,
    SchedulerRunConfig,
    ExecutionPlan,
)
from aios.common.tracing import impl_of

class Scheduler(SchedulerPort):
    def __init__(self, config: SchedulerConfig, task_dispatch_port, events_port):
        self.config = config
        self._task_dispatch_port = task_dispatch_port
        self._events_port = events_port

    @impl_of("IF:IF-SCHED-Control.OP-create_execution_plan",
             "REQ:REQ-SCHED-PLAN-001",
             "SCN:SCN-SCHED-PlanHappyPath")
    def create_execution_plan(self) -> ExecutionPlan:
        ...

6.4 Local data & local functions

    unit_internals.local_data → attributes or helper dataclasses.

    unit_internals.local_functions → private methods.

Example:

from dataclasses import dataclass
from datetime import datetime

@dataclass
class PlanCacheEntry:
    """
    [LOCAL_DATA:LD-SCHED-plan_cache_entry]
    """
    plan_id: str
    last_updated: datetime


class Scheduler(SchedulerPort):
    def __init__(...):
        self._plan_cache: dict[str, PlanCacheEntry] = {}

    def _select_ready_tasks(self, plan: ExecutionPlan):
        """
        [LOCAL_FUNC:LF-SCHED-select_ready_tasks]
        Logic:
          - filter tasks whose dependencies are completed
          - sort by priority
        """
        ...

6.5 Error handling, resource budgets, verification hints

    safety_and_reliability.error_handling → exception types + error paths.

    resource_budget → timeouts/limits where applicable.

    verification_hints → tests tagged with [VH:...].

Example:

class SchedulerError(Exception):
    """
    [ERR:ERR-SCHED-01]
    """
    pass

# tests/meta/test_scheduler_unit_basic.py

def test_scheduler_creates_plan_under_basic_conditions():
    """
    [VH:VH-SCHED-UNIT-001]
    [REQ:REQ-SCHED-PLAN-001]
    """
    ...

7. Interface Spec → Contracts (Protocols + dataclasses)

Artifact: interface_spec

One interface_spec → one module in aios/meta/interfaces/.

Mapping rules:

    card.id → [IF:...] tag in module docstring.

    data_semantics.payloads[*] → @dataclass definitions.

    operations[*] → Protocol methods.

    error_model → exception classes or error enums.

    observability.logs.required_fields → logging schema for calls using that interface.

Protocols MUST:

    Only declare signatures and return types.

    Use ... or pass as body (no logic).

    Use type annotations, not default values for contract semantics.

Example summary:

class TaskDispatchPort(Protocol):
    def dispatch_task(self, order: TaskOrder) -> None:
        """
        [IF:IF-AIOS-TaskDispatch.OP-dispatch_task]
        kind: command
        """
        ...

8. Tests & Scenarios

    Every important SCN-* scenario → at least one test.

    Every important REQ-* → at least one unit or integration test.

    Every VH-* from UDD → at least one test.

Tag tests via docstrings:

def test_task_dispatches_on_completed_event():
    """
    [SCN:SCN-SCHED-DispatchOnComplete]
    [REQ:REQ-SCHED-DISPATCH-001]
    [VH:VH-SCHED-UNIT-002]
    """
    ...

9. Checklist: Adding a New Component (Example: TaskCompiler)

When adding a new component (CMP-TaskCompiler):

    Structural view

        Add components[*] entry with id: CMP-TaskCompiler.

        Add ports with interface_ref to relevant IF-* specs.

    Interface spec(s)

        Define/update interface_spec YAML for its ports.

        Implement corresponding interface module(s) in aios/meta/interfaces/.

    UDD

        Create UDD: UDD-AIOS-TASKCOMP-01.

        Fill card, traceability, ports, config_parameters, unit_internals.

    Implementation

        Create aios/meta/task_compiler/task_compiler_core.py.

        Implement class TaskCompiler:

            Implements relevant Protocols.

            Uses config dataclass if needed.

            Tags with [UDD:...], [COMPONENT:...], [REQ:...], etc.

            Uses @impl_of(...) for key methods.

    Composition

        Update aios/meta/composition.py to wire TaskCompiler into the graph (e.g. as TaskDispatchPort consumer for Scheduler).

    Dynamic behavior & tests

        If TaskCompiler emits/consumes events → update dynamic view & event interfaces.

        Add scenario tests under tests/meta/ referencing SCN-* IDs.

Stick to this mapping and design/code stay aligned without guesswork.
Deviations should be deliberate and documented; everything else follows this standard.