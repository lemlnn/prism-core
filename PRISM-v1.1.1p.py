import argparse
import json
import os
import plistlib
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

#region information
# - constants: UPPER_SNAKE_CASE
# - variables/functions: snake_case
# - classes: PascalCase
#endregion

#region constants
SCRIPT_VERSION = "1.1.1p"
LOG_DIR_NAME = ".prism_logs"
SCRIPT_NAME = Path(__file__).name
FOLDER_PATH = Path(__file__).resolve().parent

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
CATEGORY_FOLDERS = set(DEFAULT_FILE_TYPES.keys()) | {"Others"}
#endregion

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
        if entry.name == SCRIPT_NAME:
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


def get_target_folder(extension: str) -> str:
    for folder_name, extensions in DEFAULT_FILE_TYPES.items():
        if extension in extensions:
            return folder_name
    return "Others"


def get_extension(path: Path) -> str:
    return path.suffix.lower()


def build_target_path(path: Path, folder: Path) -> Path:
    extension = get_extension(path)
    folder_name = get_target_folder(extension)
    target_path = folder / folder_name / path.name

    if target_path.exists():
        return get_unique_path(target_path)
    return target_path


def organize_files(folder: Path, args) -> None:
    files = collect_top_level_files(folder)

    files_moved = 0
    files_skipped = 0
    errors = 0
    move_log = []

    for path in files:
        target_path = build_target_path(path, folder)

        if args.exclude_str is not None and args.exclude_str in path.name:
            continue
        if args.dry_run:
            if is_hidden(path) == True and args.sort_hidden == False:
                print(f"[dry-run] {path.name} is hidden, skipping")
                files_skipped += 1
                continue
            print(f"[dry-run] {path.name} -> {target_path}")
            files_moved += 1
        else:
            try:
                if is_hidden(path) == True and args.sort_hidden == False:
                    files_skipped += 1
                    continue
                target_path.parent.mkdir(exist_ok=True)
                shutil.move(str(path), str(target_path))
                print(f"[success] Moved: {path.name} -> {target_path}")
                files_moved += 1
                move_log.append({ #logs the moves as the file runs
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
        
    if not args.dry_run and move_log:
        log_path = create_log_path(folder)
        save_log(log_path, move_log)
        print(f"\n[log] Saved run log: {log_path}")

    print("\nDone!")
    print(f"Total moved: {files_moved}")
    print(f"Total skipped: {files_skipped}")
    print(f"Total errors: {errors}")

def undo_recent_organize(folder: Path, args) -> None:

    if args.log_file:
        log_path = folder / LOG_DIR_NAME / args.log_file
        if not log_path.exists():
            print(f"[error] Log file not found: {log_path}")
            return
    else:
        log_path = get_latest_log(folder)
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

        if args.exclude_str is not None and (
            args.exclude_str in original.name or args.exclude_str in moved_to.name
        ):
            continue
        if not moved_to.exists():
            print(f"[skip] Missing moved file: {moved_to}")
            remaining_log.insert(0, entry)
            continue

        restore_target = get_unique_path(original)

        try:
            if args.dry_run:
                print(f"[dry-run] Undo: {moved_to} -> {restore_target}")
            else:
                # Recreate original parent folders if needed, then move back.
                restore_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(moved_to), str(restore_target))
                print(f"[success] Undo: {moved_to.name} -> {restore_target}")

            undone += 1

        except Exception as error:
            print(f"[error] Could not undo {moved_to}: {error}")
            errors += 1
            remaining_log.insert(0, entry)

    if not args.dry_run:
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

def check_log_dir(folder: Path) -> Path:
    log_dir = folder / LOG_DIR_NAME
    log_dir.mkdir(exist_ok=True)
    return log_dir

def create_log_path(folder: Path) -> Path:
    log_dir = check_log_dir(folder)
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
    except Exception as e:
        print(f"[warn] Could not read log file: {e}")
        return []

def get_latest_log(root: Path) -> Path | None:
    log_dir = root / LOG_DIR_NAME
    if not log_dir.exists():
        return None

    logs = sorted(log_dir.glob("organize_log_*.json"))
    return logs[-1] if logs else None

def list_logs(folder_path: Path) -> None:

    log_dir = folder_path / LOG_DIR_NAME
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

#endregion

#region args-functions

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description="Organize files in the current folder.")
    subparsers = parser.add_subparsers(dest="sub", required=False)
    shared_flags = argparse.ArgumentParser(add_help=False)

    #shared flags
    shared_flags.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Preview actions without moving files."
    )
    shared_flags.add_argument(
        "--exclude-str",
        type=str,
        help="Excludes a entry that contains the specified string"
    )

    #commands
    organize_parser = subparsers.add_parser(
        "organize", 
        parents=[shared_flags], 
        help="Runs the organizer script"
    )
    undo_parser = subparsers.add_parser(
        "undo",
        parents=[shared_flags], 
        help="Reverses the most recent organize run"
    )
    list_logs_parser = subparsers.add_parser(
        "list-logs", 
        help="List available run logs"
    )

    #specific flags
    organize_parser.add_argument(
        "--sort-hidden",
        action="store_true",
        help="Sorts hidden files."
    )
    undo_parser.add_argument(
        "--log-file",
        type=str,
        help="Specific log file inside .prism_logs/ to undo."
    )
    return parser.parse_args()

#endregion

def main() -> None:

    args = parse_args()

    if args.sub == "list-logs":
        list_logs(FOLDER_PATH)
        return
    elif args.sub == "undo":
        print(f"Working in {FOLDER_PATH}")
        undo_recent_organize(FOLDER_PATH, args)
    elif args.sub == "organize":
        print(f"Working in {FOLDER_PATH}")
        organize_files(FOLDER_PATH, args)
    else:
        print(f"No command provided. Try '{SCRIPT_NAME}.py organize' or use --help")


if __name__ == "__main__":
    main()
