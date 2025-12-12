from pathlib import Path
#interfaces
from system.sys_components.swe.swe_interfaces.implementation.if_artifact_manager import artifact_store_port, artifact_ref, artifact_content
from sos_interfaces.if_target_repo import target_repo_port

class local_manager (artifact_store_port, target_repo_port):
    def __init__ (self):
        with open (".aios/config/repo_config.json") as repo_config:
            self.target_cm_catalogue = repo_config["cm_catalogue"] 
    def load(self, ref: artifact_ref) -> artifact_content: ...
def main ():
    ...
if __name__ == "__main__":
    ...