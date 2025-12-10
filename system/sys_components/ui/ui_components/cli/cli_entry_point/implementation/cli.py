# local lib
import argparse
# interfaces
from sos_interfaces.if_user_port import fetch_user_data_port
from system.sys_components.swe.swe_interfaces.implementation.if_scheduler import system_config

class cli (fetch_user_data_port):
    def __init__(self):
        self.parser = argparse.ArgumentParser(description=('Welcome to AIOS' + " v0.1"))
        self.parser.add_argument('restore_v_create', help='Do you want a fresh execution or to restore previous session?')
        self.parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
        self.parser.add_argument('--count', type=int, default=1, help='Number of times to perform an action.')
        self.read_user_data()
        
    def read_user_data(self) -> system_config | None:
        args = self.parser.parse_args()
        return system_config (
            restore_v_create= args.restore_v_create,
            checkpoint= Path,
            execute_v_implement= str,
            architecture_v_unit= str,
            architecture_v_unit_path= Path,
            review_required= bool,
            tests_required= bool,
            resources= resources_data,
            log_path= Path,
            project_path= Path
        )
    
def main():
    cli()

if __name__ == "__main__":
    main()