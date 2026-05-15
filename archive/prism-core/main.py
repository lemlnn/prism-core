from .cli import parse_args
from .commands import PrismApp, organize_files, pause_before_exit, undo_recent_organize
from .config_store import build_runtime_config, load_config
from .defaults import default_config
from .logs import inspect_logs, list_logs

#region main

def main() -> None: #function as the main runtime pathway and calling processes/API components
    args = parse_args()

    config_name = args.config_name
    if not config_name.endswith(".json"):
        config_name += ".json"

    config_path = default_config.config_dir_path / config_name
    loaded_config = load_config(config_path)
    runtime_config = build_runtime_config(args, loaded_config)

    app = PrismApp(runtime_config, config_path)

    if args.command == "list-logs":
        list_logs(runtime_config.folder_path, runtime_config.log_dir_name)
    elif args.command == "inspect":
        inspect_logs(runtime_config.folder_path, runtime_config.log_dir_name, args.log_file)
    elif args.command == "undo":
        print(f"Working in {runtime_config.folder_path}")
        undo_recent_organize(runtime_config.folder_path, runtime_config, args.log_file)
    elif args.command == "organize":
        print(f"Working in {runtime_config.folder_path}")
        organize_files(runtime_config.folder_path, runtime_config)
    elif args.command == "extension":
        app.handle_extension_command(args)
    elif args.command == "config":
        app.handle_config_command(args)
    else:
        print("No command provided.\n")
        print("Examples:")
        print(f"  {runtime_config.script_name} -c my_config organize")
        print(f"  {runtime_config.script_name} config")
        print(f"  {runtime_config.script_name} organize --dry-run")
        print(f"  {runtime_config.script_name} organize")
        print(f"  {runtime_config.script_name} undo")
        print(f"  {runtime_config.script_name} --help")
        pause_before_exit()

#endregion
