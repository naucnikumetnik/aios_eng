# local lib
from pathlib import Path

# interfaces
from system.sys_components.swe.swe_interfaces.implementation.if_scheduler import scheduler_port, system_config, execution_plan
from system.sys_components.swe.swe_interfaces.implementation.if_architecture_description import architecture_description
from system.sys_components.swe.swe_interfaces.implementation.if_resolve import resolve_port
from system.sys_components.swe.swe_interfaces.implementation.if_task_lifecycle_events import TaskStatusEvent, TaskStatus, TaskLifecycleEventsPort
from system.sys_components.swe.swe_interfaces.implementation.if_agent_configurator import llm_config
from system.sys_components.swe.swe_interfaces.implementation.if_resources import resources_data
from system.sys_components.swe.swe_interfaces.implementation.if_task import task_order

# functions
from system.sys_components.swe.swe_components.helper_functions.resolver.implementation.resolve import resolve 
from system.sys_components.swe.swe_components.execution_engine.implementation.execution_engine import order_task
from system.sys_components.swe.swe_components.helper_functions.event_bus.event_bus import InProcessTaskLifecycleBus

class scheduler (scheduler_port):

    def __init__(self, config: system_config, events_port: TaskLifecycleEventsPort):
        self.config = config
        self.base_resources = config.resources
        self.events_port = events_port
        self.events_port.subscribe(self._monitor)
        self._run()

    def create_execution_plan (self, architecture_description : Path) -> execution_plan:
        execution_plan = {}
        with open(architecture_description, 'r') as f:
            for id in f.read()[structural_view[components]]: 
                execution_plan[id] = {"status": "todo", priority: "normal"}
                execution_plan[id]["batch"] = input_set_batch_1
        execution_plan = execution_plan()
        '''{
            scenario1: {
                unit1: {
                    operation: config.execute_v_implement,
                    input_set_core: {
                        input_name: path }, 
                    batches: { 
                        batch1:{input_set: {chunk: 1, previous_batch: ""}, status: "todo", priority: "normal", artifact_operation: "stitch"}, 
                        batch2:{input_set: {chunk: 2, previous_batch: "batch1"}, status: "todo", priority: "normal", artifact_operation: "stitch"}}, 
                    review:{ 
                        batches: {
                            batch1: {input_set: "batch1", status: "todo", priority: "high", artifact_operation: "review"}}, 
                            batch2: {}}, 
                    test: {
                        batches:{
                            batch1:{input_set: "batch1", status: "todo", priority: "high", artifact_operation: "test"}}}},
                unit2: {
                    operation: config.execute_v_implement,
                    input_set_core: {
                        input_name: path }, 
                    batches: { 
                        batch1:{input_set: {chunk: 1, previous_batch: ""}, status: "todo", priority: "normal", artifact_operation: "stitch"}, 
                        batch2:{input_set: {chunk: 2, previous_batch: "batch1"}, status: "todo", priority: "normal", artifact_operation: "stitch"}}, 
                    review:{
                        batches: {
                            batch1: {input_set: "batch1", status: "todo", priority: "high", artifact_operation: "review"}}, 
                            batch2: {}}, 
                    test: {
                        batches:{
                            batch1:{input_set: "batch1", status: "todo", priority: "high", artifact_operation: "test"}}}}
                            },
            scenario2: {
                unit5: {
                    operation: config.execute_v_implement,
                    input_set_core: {
                        input_name: path }, 
                    batches: { 
                        batch1:{input_set: {chunk: 1, previous_batch: ""}, status: "todo", priority: "normal", artifact_operation: "stitch"}, 
                        batch2:{input_set: {chunk: 2, previous_batch: "batch1"}, status: "todo", priority: "normal", artifact_operation: "stitch"}}, 
                    review:{ 
                        batches: {
                            batch1: {input_set: "batch1", status: "todo", priority: "high", artifact_operation: "review"}}, 
                            batch2: {}}, 
                    test: {
                        batches:{
                            batch1:{input_set: "batch1", status: "todo", priority: "high", artifact_operation: "test"}}}},
                unit6: {
                    operation: config.execute_v_implement,
                    input_set_core: {
                        input_name: path }, 
                    batches: { 
                        batch1:{input_set: {chunk: 1, previous_batch: ""}, status: "todo", priority: "normal", artifact_operation: "stitch"}, 
                        batch2:{input_set: {chunk: 2, previous_batch: "batch1"}, status: "todo", priority: "normal", artifact_operation: "stitch"}}, 
                    review:{
                        batches: {
                            batch1: {input_set: "batch1", status: "todo", priority: "high", artifact_operation: "review"}}, 
                            batch2: {}}, 
                    test: {
                        batches:{
                            batch1:{input_set: "batch1", status: "todo", priority: "high", artifact_operation: "test"}}}}
                            }
        } '''
        resolver.resolve_inputs()
        print(execution_plan)
        return execution_plan
    
    def assign_resources (self):
        ...
    
    def estimate_effort (self):
        ...
    
    def _adjust (self):
        ...
    
    def _baseline (self):
        ...
    
    def execute_plan (self, execution_plan: execution_plan):
        for unit in execution_plan[units]:
            if unit[status] == "todo":
                self.order_task(Path("asd"))

    def order_task (self, unit: Path) -> None:
        asd = task_order (
            task_name= "asd",
            task_description= "asd",
            input_requirements= "asd",
            output_requirements= "asd",
            parameters= "asd",
            execute_v_implement = self.config.execute_v_implement
        )
    
    def build_task (self):
        ...

    def _calculate_concurrency (self):
        ...

    def _monitor(self, event):
        ''' detect task status change.
        if complete, move to next,  if failed, retry or escalate
        review execution plan
        calculate next priority
        dipatch request
        on event see what happened and adjust'''
        # overview execution plan
        '''
        load execution plan
        '''
        if event.new_status == TaskStatus.COMPLETED:
            self._handle_task_completed(event.task_instance_id)
        elif event.new_status == TaskStatus.FAILED:
            self._handle_task_failed(event.task_instance_id)

    def _handle_task_completed(self, task_instance_id: str) -> None:
        # look up plan, dependencies, unlock next tasks, etc.
        ...

    def _handle_task_failed(self, task_instance_id: str) -> None:
        # retry / mark blocked / request human input, etc.
        ...

        # compile task order
        task_order = {}
        if task.ongoing == True:
            resources = resource_manager.available_resources()
        else:
            resources = self.base_resources
        llm_settings = agent_configurator.get_llm_settings(task, resources)
        task_order = {
            unit1: {
                "operator_activity": "implement",
                "artifact_activity": "create",
                "input_set": {"input_name": "path/to/input"},
                "model": "gpt-4",
                settings: llm_settings,
            }
            }
        for unit_id, details in execution_plan.items():
            task_order[unit_id] = {
                "operation": details["operation"],
                "input_set": details["input_set_core"],
                "batches": details["batches"],
                "review": details["review"],
                "test": details["test"]
            }
        # send to execution engine
        execution_engine = order_task(task_order)
        
    def _calculate_batches(self, task, inputs, base_resources):
        # calculation_logic
        batches = {batch1:{input_set: {chunk: 1, previous_batch: ""}, status: "todo", priority: "normal", artifact_operation: "stitch"}}
        return batches
    
    def _report_status(self):
        pass

    def _run(self):
        if self.config.restore_v_create == "create":
            if self.config.architecture_v_unit == "unit":
                self.order_task(Path ("asd"))
            elif self.config.architecture_v_unit == "architecture":
                self.create_execution_plan(architecture_description=Path("asd"))
        elif self.config.restore_v_create == "restore":
            with open(self.config.checkpoint) as checkpoint:
                plan = execution_plan (checkpoint[plan])
                self.execute_plan (plan)
 
def main():
    event_bus = InProcessTaskLifecycleBus()
    resources = resources_data (
        gpu_count = 12,
        gpu_name= "asd",
        gpu_vram_gb= 12,
        gpu_compute_capability= "asd",
        gpu_supports_fp16= True,
        gpu_supports_bf16= True,
        gpu_supports_cuda= True,
        cpu_model= "asd",
        cpu_physical_cores= 12,
        cpu_logical_cores= 12,
        cpu_base_clock_ghz= 12,
        cpu_has_avx2= True,
        cpu_has_avx512= True,
        ram_total_gb= 12,
        ram_available_gb= 12,
        storage_type= "asd",
        storage_read_mb_s= 12,
        storage_free_gb= 12
    )
    config = system_config (
        restore_v_create = "create",
        checkpoint = Path ("asd"),
        execute_v_implement = "execute",
        architecture_v_unit = "unit",
        architecture_v_unit_path = Path ('asd/asd.asd'),
        review_required = False,
        tests_required = False,
        resources = resources
    )
    scheduler (config = config, events_port = event_bus)

if __name__ == "__main__":
    main()