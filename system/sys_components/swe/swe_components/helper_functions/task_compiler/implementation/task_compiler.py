class task_compiler (request_task_port):
    def compile_task (self, task_order: task_order) -> task:
        # Convert task_order to task
        input_files = [Path(f) for f in task_order.input_requirements.values()]
        output_files = [Path(f) for f in task_order.output_requirements.values()]
        compiled_task = task(
            name=task_order.task_name,
            description=task_order.task_description,
            input_files=input_files,
            output_files=output_files,
            parameters=task_order.parameters
        ) 
        return compiled_task

def main():
    pass
if __name__ == "__main__":