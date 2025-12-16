from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from system.sys_components.swe.swe_interfaces.implementation.if_resources import resources_data
from system.sys_components.swe.swe_interfaces.implementation.if_task import task_spec

@dataclass
class llm_config:
    model_path: str
    n_ctx: int         # you can bump this towards 32768 if RAM/VRAM allows
    n_gpu_layers: int     # "all layers" *if* GPU offload is actually available
    n_batch: int
    n_threads: int

    temperature: float 
    top_p: float
    repeat_penalty: float 
    max_tokens: int

@dataclass(frozen=True)
class llm_interview_results:
    responses: dict[str, str]
    confidence_scores: dict[str, float]

@dataclass(frozen=True)
class leaderboard:
    llm_rankings: dict[str, float]

@dataclass(frozen=True)
class model_card:
    model_name: str
    model_version: str
    architecture: str
    tokenizer: str
    training_data: str
    intended_use: str
    limitations: str
    ethical_considerations: str
    contact_information: str
    license: str
    additional_info: dict[str, str]

class agent_configurator_port (Protocol):
    def interview_llm (self, task : task_spec, model : Path) -> llm_interview_results:
        ...

    def rank_llm_options (self, task : task_spec, resources : resources_data) -> leaderboard:
        ...

    def create_model_card (self, model_path: Path) -> model_card:
        ...

    def select_optimal_llm (self, available_llms, task : task_spec, resources : resources_data) -> Path:
        ...

    def configure_llm (self, model: str, task: dict[str, str]) -> llm_config:
        ...