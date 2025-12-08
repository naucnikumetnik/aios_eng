from prompt_compiler.design.interfaces.if_prompt import prompt_compilation_port
from prompt_compiler.implementation import prompt_compiler

class envoke_llm (prompt_compilation_port):
    pass

def main():
    task = "Example Task"
    project_path = "/path/to/project"
    compiler = prompt_compiler()
    envoke_llm ()
if __name__ == "__main__":
    envoke_llm()
    print("LLM Envoke executed")
    