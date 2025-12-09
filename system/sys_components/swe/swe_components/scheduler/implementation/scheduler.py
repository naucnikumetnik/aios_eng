from system.sys_components.swe.swe_interfaces.if_scheduler import scheduler_port, scheduler_config, execution_plan
from system.sys_components.swe.swe_interfaces.if_architecture_description import architecture_description
from system.sys_components.swe.swe_interfaces.if_resolve import resolve_port
from system.sys_components.swe.swe_components.resolver.implementation.resolve import resolve
from system.sys_components.swe.swe_components.execution_engine.implementation.execution_engine import order_task
from system.sys_components.swe.swe_interfaces.if_task_lifecycle_events import TaskStatusEvent, TaskStatus, TaskLifecycleEventsPort

class scheduler (scheduler_port):
    def __init__(self, config: scheduler_config, events_port: TaskLifecycleEventsPort, resources):
        self.base_resources = resources
        self.config = config
        self.events_port = events_port
        self._events_port.subscribe(self._on_task_status_changed)

    def create_execution_plan (self, architecture_description : Path, resolver: resolve_port) -> execution_plan:
        execution_plan = {}
        with open(architecture_description, 'r') as f:
            for id in f.read()[structural_view[components]]: 
                execution_plan[id] = {"status": "todo", priority: "normal"}
                execution_plan[id]["batch"] = input_set_batch_1

        execution_plan = {
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
        }
        resolver.resolve_inputs()
        print(execution_plan)

    def _monitor_and_adjust(self, execution_plan: execution_plan, event):
        ''' detect task status change.
        if complete, move to next,  if failed, retry or escalate
        review execution plan
        calculate next priority
        dipatch request
        on event see what happened and adjust'''
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

    async def _order_task(self, unit):
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
        
    def calculate_batches(self, task, inputs, base_resources):
        # calculation_logic
        batches = {batch1:{input_set: {chunk: 1, previous_batch: ""}, status: "todo", priority: "normal", artifact_operation: "stitch"}}
        return batches
    
    def _report_status():
        pass

    def _run():
        if self.config.restore_v_create == "create":
            resolver = resolve()
            execution_plan = self.create_execution_plan(self.config.architecture_v_unit_path, resolver)
        elif self.config.restore_v_create == "restore":
            execution_plan = self.restore_execution_plan()
        self.order_task(execution_plan)

        if self.config.architecture_v_unit == "unit":
            pass
        elif self.config.architecture_v_unit == "architecture":
            pass

def main():
    resolver = resolve()
    scheduler.create_execution_plan("path/to/architecture_description", resolver)

if __name__ == "__main__":
    main()