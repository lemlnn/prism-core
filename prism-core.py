import argparse
import json
import os
import plistlib
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime

#region information
# - constants: UPPER_SNAKE_CASE
# - variables/functions: snake_case
# - classes: PascalCase
#endregion

#region default-configs

DEFAULT_FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".tiff", ".bmp", ".eps", ".raw", ".heic", ".arw", ".webp"],
    "Documents": [".pdf", ".doc", ".docx", ".xlsx", ".pptx", ".ppt", ".csv"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".mpeg", ".webm"],
    "Audio": [".mp3", ".wav", ".ogg", ".flac", ".m4a"],
    "Archives": [".zip", ".rar", ".tar", ".gz", ".7z"],
    "Scripts": [".py", ".js", ".sh", ".bat", ".cmd", ".ps1", ".pyw"],
    "Applications": [".exe", ".dmg", ".app", ".msi", ".iso"],
    "Texts": [".txt", ".md", ".json", ".yaml", ".yml", ".xml"],
}

@dataclass(frozen=True)
class DefaultConfig:
    script_name: str = Path(__file__).name
    script_version: str = "1.2.3p"
    log_dir_name: str = ".prism_logs"
    folder_path: Path = Path(__file__).resolve().parent
    config_dir_path: Path = Path.home() / ".prism_config"
    dry_run: bool = False
    sort_hidden: bool = False
    exclude_str: str | None = None
    default_file_types: dict[str, list[str]] = field(
        default_factory=lambda: {k: v[:] for k, v in DEFAULT_FILE_TYPES.items()}
    )

@dataclass
class RuntimeConfig:
    script_name: str
    script_version: str
    log_dir_name: str
    folder_path: Path
    config_dir_path: Path
    dry_run: bool
    sort_hidden: bool
    exclude_str: str | None
    default_file_types: dict[str, list[str]]

default_config = DefaultConfig()

#region folder-indexing-functions

def is_hidden(path: Path) -> bool:
    return path.name.startswith(".")


def iterate_entries(path: Path):
    try:
        with os.scandir(path) as stream:
            yield from stream
    except PermissionError:
        print(f"[error] Access denied to {path}")
    except FileNotFoundError:
        print(f"[error] Folder {path} does not exist")
    except OSError as error_message:
        print(f"[error] System reported {error_message}")


def get_entry_type(entry) -> str:
    try:
        if entry.is_dir(follow_symlinks=False):
            return "dir"
        elif entry.is_file(follow_symlinks=False):
            return "file"
        else:
            return "unknown"
    except OSError as error_message:
        print(f"[error] System reported {error_message}")
        return "error"


def collect_top_level_files(folder: Path) -> list[Path]:
    files = []
    for entry in iterate_entries(folder):
        if get_entry_type(entry) != "file":
            continue
        if entry.name == default_config.script_name:
            continue
        path = Path(entry.path)
        files.append(path)
    return files
#endregion

#region main-functions
def get_unique_path(target_path: Path) -> Path:
    if not target_path.exists():
        return target_path

    stem = target_path.stem
    extension = target_path.suffix
    containing_folder = target_path.parent
    counter = 1

    while True:
        new_path = containing_folder / f"{stem} ({counter}){extension}"
        if not new_path.exists():
            return new_path
        counter += 1


def get_target_folder(extension: str, file_types: dict[str, list[str]]) -> str:
    for folder_name, extensions in file_types.items():
        if extension in extensions:
            return folder_name
    return "Others"


def get_extension(path: Path) -> str:
    return path.suffix.lower()


def build_target_path(
    path: Path,
    folder: Path,
    file_types: dict[str, list[str]]
) -> Path:
    extension = get_extension(path)
    folder_name = get_target_folder(extension, file_types)
    target_path = folder / folder_name / path.name

    if target_path.exists():
        return get_unique_path(target_path)
    return target_path



def organize_files(folder: Path, runtime_config: RuntimeConfig) -> None:
    files = collect_top_level_files(folder)

    files_moved = 0
    files_skipped = 0
    errors = 0
    move_log = []

    for path in files:
        target_path = build_target_path(path, folder, runtime_config.default_file_types)

        if runtime_config.exclude_str is not None and runtime_config.exclude_str in path.name:
            continue
        if runtime_config.dry_run:
            if is_hidden(path) and not runtime_config.sort_hidden:
                print(f"[dry-run] {path.name} is hidden, skipping")
                files_skipped += 1
                continue
            print(f"[dry-run] {path.name} -> {target_path}")
            files_moved += 1
        else:
            try:
                if is_hidden(path) and not runtime_config.sort_hidden:
                    files_skipped += 1
                    continue
                target_path.parent.mkdir(exist_ok=True)
                shutil.move(str(path), str(target_path))
                print(f"[success] Moved: {path.name} -> {target_path}")
                files_moved += 1
                move_log.append({
                    "original": str(path),
                    "moved_to": str(target_path)
                })
            except PermissionError:
                print(f"[error] Access denied to {path}")
                errors += 1
            except FileNotFoundError:
                print(f"[error] File {path} does not exist")
                errors += 1
            except OSError as error_message:
                print(f"[error] System reported {error_message}")
                errors += 1

    if not runtime_config.dry_run and move_log:
        log_path = create_log_path(folder, runtime_config.log_dir_name)
        save_log(log_path, move_log)
        print(f"\n[log] Saved run log: {log_path}")

    print("\nDone!")
    print(f"Total moved: {files_moved}")
    print(f"Total skipped: {files_skipped}")
    print(f"Total errors: {errors}")

def undo_recent_organize(folder: Path, args, runtime_config: RuntimeConfig) -> None:

    if args.log_file:
        log_path = folder / runtime_config.log_dir_name / args.log_file
        if not log_path.exists():
            print(f"[error] Log file not found: {log_path}")
            return
    else:
        log_path = get_latest_log(folder, runtime_config.log_dir_name)
        if log_path is None:
            print("[info] No log files found. Nothing to undo.")
            return

    move_log = load_log(log_path)
    if not move_log:
        print("[info] Log file is empty or unreadable. Nothing to undo.")
        return

    undone = 0
    errors = 0
    remaining_log = []

    for entry in reversed(move_log):
        original = Path(entry["original"])
        moved_to = Path(entry["moved_to"])

        if runtime_config.exclude_str is not None and (
            runtime_config.exclude_str in original.name or runtime_config.exclude_str in moved_to.name
        ):
            continue
        if not moved_to.exists():
            print(f"[skip] Missing moved file: {moved_to}")
            remaining_log.insert(0, entry)
            continue

        restore_target = get_unique_path(original)

        try:
            if runtime_config.dry_run:
                print(f"[dry-run] Undo: {moved_to} -> {restore_target}")
            else:
                restore_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(moved_to), str(restore_target))
                print(f"[success] Undo: {moved_to.name} -> {restore_target}")

            undone += 1

        except Exception as error:
            print(f"[error] Could not undo {moved_to}: {error}")
            errors += 1
            remaining_log.insert(0, entry)

    if not runtime_config.dry_run:
        if remaining_log:
            save_log(log_path, remaining_log)
            print(f"\n[log] Updated incomplete undo log: {log_path}")
        else:
            try:
                log_path.unlink()
                print(f"\n[log] Removed completed log: {log_path}")
            except Exception as error:
                print(f"[warn] Could not remove log file: {error}")

    print("\nUndo complete!")
    print(f"Total undone: {undone}")
    print(f"Total errors: {errors}")

#endregion

#region logging-functions

def check_log_dir(folder: Path, log_dir_name: str) -> Path:
    log_dir = folder / log_dir_name
    log_dir.mkdir(exist_ok=True)
    return log_dir

def create_log_path(folder: Path, log_dir_name: str) -> Path:
    log_dir = check_log_dir(folder, log_dir_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir / f"organize_log_{timestamp}.json"

def save_log(log_path: Path, moves: list[dict]) -> None:
    try:
        with log_path.open("w", encoding="utf-8") as f:
            json.dump(moves, f, indent=2)
    except Exception as error:
        print(f"[error] Could not save log file: {error}")

def load_log(log_path: Path) -> list[dict]:
    try:
        with log_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as error:
        print(f"[warn] Could not read log file: {error}")
        return []

def get_latest_log(root: Path, log_dir_name: str) -> Path | None:
    log_dir = root / log_dir_name
    if not log_dir.exists():
        return None

    logs = sorted(log_dir.glob("organize_log_*.json"))
    return logs[-1] if logs else None

def list_logs(folder_path: Path, log_dir_name: str) -> None:
    log_dir = folder_path / log_dir_name
    if not log_dir.exists():
        print("[info] No log directory found.")
        return

    logs = sorted(log_dir.glob("organize_log_*.json"))
    if not logs:
        print("[info] No logs found.")
        return

    print("Available logs:")
    for log in logs:
        print(f" - {log.name}")

def list_configs(config_dir: Path) -> None:
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

#region config-functions

def check_config_path(target_path: Path) -> Path:
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

def get_config_file_path(config_dir: Path, name: str) -> Path:
    config_dir.mkdir(parents=True, exist_ok=True)
    target_path = config_dir / f"{name}.json"
    return check_config_path(target_path)

def serialize_default_config() -> dict:
    data = asdict(default_config)
    for key, value in data.items():
        if isinstance(value, Path):
            data[key] = str(value)
    return data

def write_default_config(config_path: Path) -> None:
    with config_path.open("w", encoding="utf-8") as json_output:
        json.dump(serialize_default_config(), json_output, indent=4)

def write_config(config_path: Path, runtime_config: RuntimeConfig) -> None:
    with config_path.open("w", encoding="utf-8") as json_output:
        json.dump(serialize_config(runtime_config), json_output, indent=4)

def load_config(config_path: Path) -> dict:
    try:
        with config_path.open("r", encoding="utf-8") as json_input:
            data = json.load(json_input)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as error:
        print(f"[warn] Could not read config file: {error}")
        return {}
    
def serialize_config(runtime_config: RuntimeConfig) -> dict:
    data = asdict(runtime_config)
    for key, value in data.items():
        if isinstance(value, Path):
            data[key] = str(value)
    return data

def build_runtime_config(args, loaded_config: dict | None = None) -> RuntimeConfig:
    loaded_config = loaded_config or {}

    dry_run_arg = getattr(args, "dry_run", None)
    sort_hidden_arg = getattr(args, "sort_hidden", None)
    exclude_str_arg = getattr(args, "exclude_str", None)

    return RuntimeConfig(
        script_name=loaded_config.get("script_name", default_config.script_name),
        script_version=loaded_config.get("script_version", default_config.script_version),
        log_dir_name=loaded_config.get("log_dir_name", default_config.log_dir_name),
        folder_path=Path(loaded_config.get("folder_path", default_config.folder_path)),
        config_dir_path=Path(loaded_config.get("config_dir_path", default_config.config_dir_path)),
        dry_run=dry_run_arg if dry_run_arg is not None else loaded_config.get("dry_run", default_config.dry_run),
        sort_hidden=sort_hidden_arg if sort_hidden_arg is not None else loaded_config.get("sort_hidden", default_config.sort_hidden),
        exclude_str=exclude_str_arg if exclude_str_arg is not None else loaded_config.get("exclude_str", default_config.exclude_str),
        default_file_types=loaded_config.get(
            "default_file_types",
            {k: v[:] for k, v in default_config.default_file_types.items()}
        ),
    )

def build_config_status(runtime_config: RuntimeConfig, config_path: Path) -> list[str]:
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
    lines.append(f"  Script version : {runtime_config.script_version}")
    lines.append(f"  Working folder : {runtime_config.folder_path}")
    lines.append(f"  Log directory  : {runtime_config.log_dir_name}")
    lines.append(f"  Dry run        : {runtime_config.dry_run}")
    lines.append(f"  Sort hidden    : {runtime_config.sort_hidden}")
    lines.append(f"  Exclude string : {runtime_config.exclude_str if runtime_config.exclude_str is not None else 'None'}")
    lines.append(f"  File categories: {len(runtime_config.default_file_types)}")

    return lines

def show_config_status(runtime_config: RuntimeConfig, config_path: Path) -> None:
    for line in build_config_status(runtime_config, config_path):
        print(line)

#endregion

#region args-functions

def parse_args() -> argparse.Namespace:
    usage_info = "%(prog)s [options] {organize,undo,list-logs,config} ..."
    
    example_usage = textwrap.dedent("""
        Commands:
          organize    Sort files into categorized folders
          undo        Revert the last organization run
          list-logs   Show history of previous runs
          config      Manage settings and custom profiles

        Examples:
          %(prog)s organize --dry-run
          %(prog)s -c my_profile config --save --dry-run --exclude-str "Draft"
          %(prog)s -c photography organize
          %(prog)s config --list
          %(prog)s undo
    """)

    parser = argparse.ArgumentParser(
        description="PRISM: A smart file organizer that categorizes files by type.",
        usage=usage_info,
        epilog=example_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    global_group = parser.add_argument_group("Global Options")
    global_group.add_argument(
        "-c", "--config",
        metavar="NAME",
        dest="config_name",
        default="default",
        help="Use a specific configuration profile (default: 'default')"
    )
    
    subparsers = parser.add_subparsers(dest="command", title="Available Commands", metavar="")
    shared_flags = argparse.ArgumentParser(add_help=False)

    shared_flags.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="Preview changes without moving any files"
    )
    shared_flags.add_argument(
        "--exclude-str",
        metavar="TEXT",
        type=str,
        help="Skip files containing this specific text"
    )

    organize_parser = subparsers.add_parser(
        "organize",
        parents=[shared_flags],
        help="Sort files into folders"
    )
    organize_parser.add_argument(
        "--sort-hidden",
        action="store_true",
        default=None,
        help="Include hidden files (starting with '.')"
    )

    undo_parser = subparsers.add_parser(
        "undo",
        parents=[shared_flags],
        help="Reverse a previous run"
    )
    undo_parser.add_argument(
        "--log-file",
        metavar="FILENAME",
        type=str,
        help="Specify a specific log to undo"
    )

    subparsers.add_parser(
        "list-logs",
        help="View organization history"
    )

    config_parser = subparsers.add_parser(
        "config",
        parents=[shared_flags],
        help="Manage configuration profiles"
    )
    config_parser.add_argument(
        "--sort-hidden",
        action="store_true",
        default=None,
        help="Include hidden files (starting with '.')"
    )
    config_actions = config_parser.add_mutually_exclusive_group()
    config_actions.add_argument("--create", action="store_true", help="Initialize a new config file")
    config_actions.add_argument("--save", action="store_true", help="Save current settings to profile")
    config_actions.add_argument("--list", action="store_true", help="List all saved profiles")
    config_actions.add_argument("--status", action="store_true", help="Show current profile summary")
    config_actions.add_argument("--show", action="store_true", help="Print raw JSON configuration")
    config_actions.add_argument("--path", action="store_true", help="Show location of config file")
    config_actions.add_argument("--reset", action="store_true", help="Restore profile to defaults")

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {default_config.script_version}"
    )

    return parser.parse_args()

#endregion
#region utility-functions

def pause_before_exit() -> None:
    if sys.stdin is not None and sys.stdin.isatty():
        input("\nPress Enter to exit...")

#region main

def main() -> None:
    args = parse_args()
    
    config_name = args.config_name
    if not config_name.endswith(".json"):
        config_name += ".json"
    
    config_path = default_config.config_dir_path / config_name

    loaded_config = load_config(config_path)
    runtime_config = build_runtime_config(args, loaded_config)

    if args.command == "list-logs":
        list_logs(runtime_config.folder_path, runtime_config.log_dir_name)
        return
    elif args.command == "undo":
        print(f"Working in {runtime_config.folder_path}")
        undo_recent_organize(runtime_config.folder_path, args, runtime_config)
    elif args.command == "organize":
        print(f"Working in {runtime_config.folder_path}")
        organize_files(runtime_config.folder_path, runtime_config)
    elif args.command == "config":
        if args.create:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            if config_path.exists():
                print(f"[info] Config already exists: {config_path}")
            else:
                write_default_config(config_path)
                print(f"[success] Wrote default config: {config_path}")
        elif args.save:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            write_config(config_path, runtime_config)
            print(f"[success] Saved runtime config to: {config_path}")
        elif args.list:
            list_configs(default_config.config_dir_path)
        elif args.path:
            print(f"[info] Config path: {config_path}")
            if config_path.exists():
                print("[info] Config file exists.")
            else:
                print("[info] Config file does not exist yet.")
        elif args.reset:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            write_default_config(config_path)
            print(f"[success] Reset config: {config_path}")
        elif args.status:
            show_config_status(runtime_config, config_path)
        elif args.show:
            print(json.dumps(serialize_config(runtime_config), indent=4))
        else:
            print("No config action provided.\n")
            print("Examples:")
            print(f"  {runtime_config.script_name} -c my_config config --create")
            print(f"  {runtime_config.script_name} config --list")
            print(f"  {runtime_config.script_name} config --save")
            print(f"  {runtime_config.script_name} config --status")
            print(f"  {runtime_config.script_name} config --show")
            print(f"  {runtime_config.script_name} config --reset")
            print(f"  {runtime_config.script_name} config --help")
            pause_before_exit()
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


if __name__ == "__main__":
    main()
