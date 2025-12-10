from system.sys_components.swe.swe_interfaces.if_prompt import prompt_compilation_port
from prompt_compiler.implementation import prompt_compiler

class envoke_llm (prompt_compilation_port):
    if local_v_cloud == "local":
        answer = local_llm(prompt)
    else:
        answer = cloud_llm(prompt)
    log = llm_logger(answer, task, project_path)
    artifact_engine.store_artifact(log, project_path, task_id)
    execution_plan.update_task_status(task_id, "completed")

class task_ordered (task_order):
    def __init__ (self, events_port: TaskLifecycleEventsPort):
        self._events_port = events_port
    def run_task(self, task_instance_id: str) -> None:
        self._emit_status(task_instance_id, TaskStatus.RUNNING)

        try:
            # do the actual work
            ...
            self._emit_status(task_instance_id, TaskStatus.COMPLETED)
        except Exception as ex:
            self._emit_status(task_instance_id, TaskStatus.FAILED, reason=str(ex))
            raise

    def _emit_status(self, task_instance_id: str, new_status: TaskStatus, reason: str | None = None) -> None:
        event = TaskStatusEvent(
            event_id=str(uuid.uuid4()),
            task_instance_id=task_instance_id,
            old_status=TaskStatus.CREATED,     # you’d actually load current status from storage
            new_status=new_status,
            occurred_at=datetime.utcnow(),
            reason=reason,
        )
        self._events_port.publish(event)
    # check if logs available
    if logs_available:
        # use logs to enhance task order
        enhanced_task_order = enhance_task_order_with_logs(task_order, logs)
    else:
        enhanced_task_order = task_order
    # Compile task and prompt
    task = task_compiler(task_order = {
            task_id: str,
            unit_id: str,
            operation: str,
            input_set: dict,
            batch: str,
            priority: str
        }) # task
    prompt = prompt_compiler(task_order = {
        task_id: str,
        unit_id: str,
        operation: str,
        input_set: dict,
        batch: str,
        priority: str
    }) # task 

    envoke_llm (task: task, project_path: str, compiler: prompt_compiler) -> None:

def main():
    task = "Example Task"
    project_path = "/path/to/project"
    compiler = prompt_compiler()
    envoke_llm ()
if __name__ == "__main__":
    main()
    