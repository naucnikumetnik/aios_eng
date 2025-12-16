#interfaces
from pathlib import Path
from system.sys_components.swe.swe_interfaces.implementation.if_agent_configurator import agent_configurator_port, leaderboard, llm_config, llm_interview_results, model_card
from system.sys_components.swe.swe_interfaces.implementation.if_resources import resources_data
from system.sys_components.swe.swe_interfaces.implementation.if_task import task_spec

class agent_configurator (agent_configurator_port):
    def rank_llm_options(self, task: task_spec, resources: resources_data) -> leaderboard:
        ...
    def choose_optimal_llm (self, task: task_spec):
        ...
    def configure_llm (self, model: str, task: dict[str, str]) -> llm_config:
        ...
    def create_model_card(self, model_path: Path) -> model_card:
        ...
    def interview_llm(self, task: task_spec, model: Path) -> llm_interview_results:
        ...
    
    
def main():
    ...

if __name__ == "__main__":
    main()