from system.sys_components.swe.swe_interfaces.implementation.if_local_llm import llm_answer, local_llm_port
from system.sys_components.swe.swe_interfaces.implementation.if_agent_configurator import llm_config

class local_llm_engine(local_llm_port):
    def trigger_local_llm (self, prompt: str, settings: llm_config) -> llm_answer:
        return llm_answer(0.0, 0.0, "This is a dummy response from local_llm_engine.")
    pass

if __name__ == "__main__":
    config = llm_config(
        model_path="path/to/model",
        n_ctx=2048,
        n_gpu_layers=0,
        n_batch=8,
        n_threads=4,
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
        max_tokens=512
    )
    prompt = "Test prompt"
    local_llm_engine()