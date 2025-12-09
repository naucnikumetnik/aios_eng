from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

'''
arch/unit
path
exec/implement
review flag
test flag
resources
'''
dataclass (frozen=True)
class scheduler_config:
    architecture_unit: str
    design_path: Path
    execution_implementation: str
    review_required: bool
    test_required: bool
    resources: Sequence[str]