# stdlib
from pathlib import Path
import json

# interfaces
from sos_interfaces.if_user_port import fetch_user_data_port, system_config
from system.sys_components.swe.swe_interfaces.implementation.if_resources import (
    resources_data,
)


class cli(fetch_user_data_port):
    def configure_system(self) -> system_config:
        """
        Interactively collect all data needed to build a system_config.
        """

        print("Welcome to AIOS v0.1\n")

        # 1) restore vs create
        restore_v_create = self._ask_choice(
            "Do you want a fresh execution or to restore previous session?",
            {"1": "restore", "2": "create"},
        )

        # === CREATE BRANCH ===================================================
        if restore_v_create == "create":
            # workflow vs task
            architecture_v_unit = self._ask_choice(
                "Would you like to execute a workflow or one task?",
                {"1": "workflow", "2": "task"},
            )

            # path to unit or architecture
            if architecture_v_unit == "task":
                architecture_v_unit_path_str = input(
                    "Please provide path to the desired unit detailed design: "
                )
            else:  # workflow
                architecture_v_unit_path_str = input(
                    "Please provide path to the desired architecture description: "
                )
            architecture_v_unit_path = Path(architecture_v_unit_path_str)

            # execute vs implement
            execute_v_implement = self._ask_choice(
                "Would you like to execute or implement?",
                {"1": "execute", "2": "implement"},
            )

            # review / tests (bools)
            review_required = self._yes_no(
                "Would you like output to be reviewed? (longer execution time)"
            )
            tests_required = self._yes_no(
                "Would you like output to be tested? (longer execution time)"
            )

            # HW resources
            resources_cfg = self._load_resources_cfg()

            # logging / artifacts paths
            log_path_str = input("Please provide path for runtime logs: ")
            project_path_str = input("Please provide path for generated artifacts: ")
            log_path = Path(log_path_str)
            project_path = Path(project_path_str)

            # in create mode we usually have no checkpoint yet
            checkpoint = None

        # === RESTORE BRANCH ==================================================
        else:  # restore
            checkpoint_str = input(
                "Please provide path to execution checkpoint you would like to restore: "
            )
            checkpoint = Path(checkpoint_str)

            # For restore, these may be irrelevant / handled by checkpoint.
            # Set them to None / defaults – adjust to match your system_config type.
            execute_v_implement = None
            architecture_v_unit = None
            architecture_v_unit_path = None
            review_required = False
            tests_required = False
            resources_cfg = None
            log_path = None
            project_path = None

        # === BUILD CONFIG ====================================================
        return system_config(
            restore_v_create=restore_v_create,
            checkpoint=checkpoint,
            execute_v_implement=execute_v_implement,
            architecture_v_unit=architecture_v_unit,
            architecture_v_unit_path=architecture_v_unit_path,
            review_required=review_required,
            tests_required=tests_required,
            resources=resources_cfg,
            log_path=log_path,
            project_path=project_path,
        )

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #

    def _ask_choice(self, question: str, options: dict[str, str]) -> str:
        """
        Ask user to choose from numbered options.
        options = {"1": "restore", "2": "create"} etc.
        Returns the *value* ("restore"/"create"/...) not the key.
        """
        print()
        print(question)
        for key, value in options.items():
            print(f"{key}) {value}")

        valid_keys = set(options.keys())
        prompt = f"Enter your choice ({'/'.join(sorted(valid_keys))}): "

        while True:
            choice = input(prompt).strip()
            if choice in valid_keys:
                return options[choice]
            print("Invalid choice. Please try again.")

    def _yes_no(self, question: str) -> bool:
        """
        Yes/no wrapper around _ask_choice.
        Returns True for yes, False for no.
        """
        answer = self._ask_choice(question, {"1": "yes", "2": "no"})
        return answer == "yes"

    def _load_resources_cfg(self) -> resources_data:
        """
        Load HW resources config from a file and map it into resources_data.

        Assumes JSON with keys matching resources_data field names, e.g.:

        {
          "gpu_count": 1,
          "gpu_name": "RTX 5080",
          "gpu_vram_gb": 16.0,
          ...
        }
        """
        path_str = input("Please provide path to HW resources cfg file (JSON): ")
        path = Path(path_str)

        if not path.is_file():
            raise FileNotFoundError(f"Resources config file not found: {path}")

        with path.open() as f:
            data = json.load(f)

        # This assumes your JSON keys == resources_data field names.
        # If not, map them manually here.
        return resources_data(**data)


def main() -> None:
    ui = cli()
    cfg = ui.configure_system()

    # Hand off to scheduler / runtime here
    # scheduler = Scheduler(...)
    # scheduler.run(cfg)


if __name__ == "__main__":
    main()
