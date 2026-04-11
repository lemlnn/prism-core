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

#region information
# - constants: UPPER_SNAKE_CASE
# - variables/functions: snake_case
# - classes: PascalCase
#endregion

#region constants
SCRIPT_VERSION = "1.5.2"

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

SORT_LOG_DIRECTORY = ".sort-logs"
FLAT_LOG_DIRECTORY = ".flat-logs"
#endregion

#region folder-indexing-functions
folder_path = Path(__file__).resolve().parent
current_script_name = Path(__file__).name


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
        if entry.name == current_script_name:
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


def organize_files(folder: Path, dry_run: bool) -> None:
    files = collect_top_level_files(folder)

    for path in files:
        target_path = build_target_path(path, folder)

        if dry_run:
            print(f"[dry-run] {path.name} -> {folder}/{target_path.name}")
        else:
            target_path.parent.mkdir(exist_ok=True)
            shutil.move(str(path), str(target_path))
            print(f"[success] Moved: {path.name} -> {folder}/{target_path.name}")
#endregion


if __name__ == "__main__":
    organize_files(folder_path, True)
