import json
from dataclasses import asdict
from pathlib import Path

from .defaults import RuntimeConfig, default_config

#region config-functions

def check_config_path(target_path: Path) -> Path:  #function to check if the config path is taken, along with a new name picker if occupied
    if not target_path.exists():
        return target_path

    extension = target_path.suffix

    while True:
        input_target_name = input("[input] Config file name taken, try another? ").strip()

        if not input_target_name:
            print("[error] Config name cannot be empty.")
            continue
        if input_target_name.endswith(extension):
            input_target_name = input_target_name.removesuffix(extension)

        input_target_path = target_path.parent / f"{input_target_name}{extension}"

        if not input_target_path.exists():
            return input_target_path

def get_config_file_path(config_dir: Path, name: str) -> Path: #function to return a valid config file name
    config_dir.mkdir(parents=True, exist_ok=True)
    target_path = config_dir / f"{name}.json"
    return check_config_path(target_path)

def serialize_default_config() -> dict: #function to ensure all Path objects are converted into str
    data = asdict(default_config)
    for key, value in data.items():
        if isinstance(value, Path):
            data[key] = str(value)
    return data

def write_default_config(config_path: Path) -> None: #function to do the actual content writing to the config with default settings
    with config_path.open("w", encoding="utf-8") as json_output:
        json.dump(serialize_default_config(), json_output, indent=4)

def write_config(config_path: Path, runtime_config: RuntimeConfig) -> None: #function to do the actual content writing to the config with default settings
    with config_path.open("w", encoding="utf-8") as json_output:
        json.dump(serialize_config(runtime_config), json_output, indent=4)

def delete_config(config_path: Path) -> None: #function to delete the specified config
    if not config_path.exists():
        print(f"[error] Config file does not exist: {config_path}")
        return

    confirm = input(f"[input] Are you sure you want to delete '{config_path.stem}'? (y/n): ").lower()
    if confirm == "y":
        try:
            config_path.unlink()
            print(f"[success] Deleted config: {config_path}")
        except Exception as error:
            print(f"[error] Could not delete config: {error}")
    else:
        print("[info] Deletion cancelled.")

def load_config(config_path: Path) -> dict: #function to read the config file
    try:
        with config_path.open("r", encoding="utf-8") as json_input:
            data = json.load(json_input)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as error:
        print(f"[warn] Could not read config file: {error}")
        return {}

def serialize_config(runtime_config: RuntimeConfig) -> dict: #function to ensure all Path objects are converted into str
    data = asdict(runtime_config)
    for key, value in data.items():
        if isinstance(value, Path):
            data[key] = str(value)
    return data


def normalize_string_list(value, default: list[str]) -> list[str]: #normalizes list-like config fields into a string list
    if isinstance(value, list):
        return [str(item) for item in value]
    return default[:]


def normalize_extension_options(value) -> dict[str, dict[str, object]]: #normalizes per-extension option config
    if not isinstance(value, dict):
        return {}

    normalized = {}

    for extension_name, options in value.items():
        if isinstance(options, dict):
            normalized[str(extension_name)] = dict(options)

    return normalized

def build_runtime_config(args, loaded_config: dict | None = None) -> RuntimeConfig: #function to take the loaded config and apply it to runtime
    loaded_config = loaded_config or {}

    debug_mode_arg = getattr(args, "debug_mode", None)
    dry_run_arg = getattr(args, "dry_run", None)
    sort_hidden_arg = getattr(args, "sort_hidden", None)
    exclude_str_arg = getattr(args, "exclude_str", None)
    delete_empty_folders_arg = getattr(args, "delete_empty_folders", None)
    enable_extensions_arg = getattr(args, "enable_extensions", None)
    extensions_dir_path_arg = getattr(args, "extensions_dir_path", None)

    return RuntimeConfig(
        debug_mode=(
            debug_mode_arg
            if debug_mode_arg is not None
            else loaded_config.get("debug_mode", default_config.debug_mode)
        ),
        script_name=loaded_config.get("script_name", default_config.script_name),
        script_version=loaded_config.get("script_version", default_config.script_version),
        log_dir_name=loaded_config.get("log_dir_name", default_config.log_dir_name),
        folder_path=Path(loaded_config.get("folder_path", default_config.folder_path)),
        config_dir_path=Path(loaded_config.get("config_dir_path", default_config.config_dir_path)),
        enable_extensions=(
            enable_extensions_arg
            if enable_extensions_arg is not None
            else loaded_config.get("enable_extensions", default_config.enable_extensions)
        ),
        extensions_dir_path=Path(
            extensions_dir_path_arg
            if extensions_dir_path_arg is not None
            else loaded_config.get("extensions_dir_path", default_config.extensions_dir_path)
        ),
        dry_run=(
            dry_run_arg
            if dry_run_arg is not None
            else loaded_config.get("dry_run", default_config.dry_run)
        ),
        sort_hidden=(
            sort_hidden_arg
            if sort_hidden_arg is not None
            else loaded_config.get("sort_hidden", default_config.sort_hidden)
        ),
        delete_empty_folders=(
            delete_empty_folders_arg
            if delete_empty_folders_arg is not None
            else loaded_config.get("delete_empty_folders", default_config.delete_empty_folders)
        ),
        exclude_str=(
            exclude_str_arg
            if exclude_str_arg is not None
            else loaded_config.get("exclude_str", default_config.exclude_str)
        ),
        disabled_extensions=normalize_string_list(
            loaded_config.get("disabled_extensions", default_config.disabled_extensions),
            default_config.disabled_extensions,
        ),
        extension_options=normalize_extension_options(
            loaded_config.get("extension_options", default_config.extension_options)
        ),
        default_file_types=loaded_config.get(
            "default_file_types",
            {k: v[:] for k, v in default_config.default_file_types.items()}
        ),
    )

def build_config_status(runtime_config: RuntimeConfig, config_path: Path) -> list[str]: #function to render the current settings when using config --status
    lines = []

    lines.append("PRISM Config Status")
    lines.append("-------------------")
    lines.append(f"Config path: {config_path}")

    if config_path.exists():
        lines.append("Config file: exists")
    else:
        lines.append("Config file: missing")

    lines.append("")
    lines.append("Current runtime settings:")
    lines.append(f"  Script version      : {runtime_config.script_version}")
    lines.append(f"  Working folder      : {runtime_config.folder_path}")
    lines.append(f"  Log directory       : {runtime_config.log_dir_name}")
    lines.append(f"  Extensions enabled  : {runtime_config.enable_extensions}")
    lines.append(f"  Extensions folder   : {runtime_config.extensions_dir_path}")
    lines.append(f"  Dry run             : {runtime_config.dry_run}")
    lines.append(f"  Sort hidden         : {runtime_config.sort_hidden}")
    lines.append(f"  Delete empty folders: {runtime_config.delete_empty_folders}")
    lines.append(f"  Exclude string      : {runtime_config.exclude_str if runtime_config.exclude_str is not None else 'None'}")
    lines.append(f"  Disabled extensions : {len(runtime_config.disabled_extensions)}")
    if runtime_config.disabled_extensions:
        for extension_name in runtime_config.disabled_extensions:
            lines.append(f"    - {extension_name}")
    lines.append(f"  Extension options   : {len(runtime_config.extension_options)}")
    lines.append(f"  File categories     : {len(runtime_config.default_file_types)}")

    return lines


def show_config_status(runtime_config: RuntimeConfig, config_path: Path) -> None:
    for line in build_config_status(runtime_config, config_path):
        print(line)

def list_configs(config_dir: Path) -> None: #function to list the config files in a folder
    if not config_dir.exists():
        print("[info] No config directory found.")
        return

    configs = sorted(config_dir.glob("*.json"))
    if not configs:
        print("[info] No configurations found.")
        return

    print("Available configurations:")
    for cfg in configs:
        print(f" - {cfg.stem}")

#endregion
