#local libs
from pathlib import Path
#interfaces
from system.sys_components.swe.swe_interfaces.implementation.if_task import request_task_port, task_spec, task_order
from system.sys_components.swe.swe_interfaces.implementation.if_artifact_manager import artifact_store_port

class task_compiler (request_task_port, artifact_store_port):
    def __init__ (self, unit: Path, orga: Path):
        self.artifact_manager = artifact_store_port
    def compile_task (self, task_order: task_order) -> task_spec:
        mapping_req = self._load_mapping_requirements(order)  # REQ-AIOS-TaskMapping-UnitExec-v1
        design_ctx = self._load_design_context(order)

        task = task_spec.empty()

        for rule in mapping_req.mapping_rules:
            self._apply_rule(rule, design_ctx, task)

        self._validate_task(task)
        return task_spec

def main():
    ...
if __name__ == "__main__":
    main()