from typing import Protocol
from pathlib import Path
# interfaces
from system.sys_components.swe.swe_interfaces.implementation.if_prompt import prompt

class execution_engine_port (Protocol):
    def trigger_llm (self, hosting: str, llm_component: Path, model_path: str | None, API: str | None, prompt: prompt, settings: dict):
        '''
        Docstring for envoke_llm
        
        :param self: Description
        :param hosting: Description
        :type hosting: str
        :param llm_component: Description
        :type llm_component: Path
        :param model_path: Description
        :type model_path: str | None
        :param API: Description
        :type API: str | None
        :param prompt: Description
        :type prompt: prompt
        '''
        ...