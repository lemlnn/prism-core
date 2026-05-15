import json
from datetime import datetime
from pathlib import Path

#region logging-functions

def check_log_dir(folder: Path, log_dir_name: str) -> Path: #function to check if a log directory exists or not
    log_dir = folder / log_dir_name
    log_dir.mkdir(exist_ok=True)
    return log_dir

def create_log_path(folder: Path, log_dir_name: str) -> Path: #function to create a log name based on the current system time
    log_dir = check_log_dir(folder, log_dir_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir / f"organize_log_{timestamp}.json"

def save_log(log_path: Path, moves: list[dict]) -> None: #function to attempt saving the log by dumping contents into JSON
    try:
        with log_path.open("w", encoding="utf-8") as f:
            json.dump(moves, f, indent=2)
    except Exception as error:
        print(f"[error] Could not save log file: {error}")

def load_log(log_path: Path) -> list[dict]: #function to read the log
    try:
        with log_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as error:
        print(f"[warn] Could not read log file: {error}")
        return []

def get_latest_log(root: Path, log_dir_name: str) -> Path | None: #function to obtain the most recent log
    log_dir = root / log_dir_name
    if not log_dir.exists():
        return None

    logs = sorted(log_dir.glob("organize_log_*.json"))
    return logs[-1] if logs else None

def get_specified_log(root: Path, log_dir_name: str, log_file: str) -> Path | None: #function to obtain the specified log
    log_name = Path(log_file).name

    if not log_name.endswith(".json"):
        log_name += ".json"

    log_path = root / log_dir_name / log_name

    if not log_path.is_file():
        return None

    return log_path

def list_logs(folder_path: Path, log_dir_name: str) -> None: #function to identify any log files in a folder
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

def inspect_logs(folder_path: Path, log_dir_name: str, log_file: str | None = None) -> None: #gets a basic summary of the log
    
    if log_file:
        log_path = get_specified_log(folder_path, log_dir_name, log_file)
    else:
        log_path = get_latest_log(folder_path, log_dir_name)

    if log_path is None:
        print("[info] No logs found.")
        return

    move_log = load_log(log_path)
    if not move_log:
        print("[info] Log file is empty or unreadable.")
        return
    log_path_clean = log_path.relative_to(folder_path)

    print("PRISM Log Summary")
    print("-----------------")
    print(f"  Log file    : {log_path_clean}")
    print(f"  Total moved : {len(move_log)}") 

#endregion
