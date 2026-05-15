from dataclasses import dataclass, field
from pathlib import Path

#region default-configs

DEFAULT_FILE_TYPES = { #basic file categories
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
class DefaultConfig: #hardcoded default settings

    debug_mode: bool = False
    script_name: str = "prism"
    script_version: str = "1.3.0p-devt4c"
    log_dir_name: str = ".prism_logs"
    folder_path: Path = field(default_factory=Path.cwd)
    config_dir_path: Path = Path.home() / ".prism_config"
    enable_extensions: bool = False
    extensions_dir_path: Path = Path.home() / ".prism_extensions"
    dry_run: bool = False
    sort_hidden: bool = False
    delete_empty_folders: bool = False
    exclude_str: str | None = None
    disabled_extensions: list[str] = field(default_factory=list)
    extension_options: dict[str, dict[str, object]] = field(default_factory=dict)
    default_file_types: dict[str, list[str]] = field(
        default_factory=lambda: {k: v[:] for k, v in DEFAULT_FILE_TYPES.items()}
    )

@dataclass
class RuntimeConfig: #user requested settings

    debug_mode: bool
    script_name: str
    script_version: str
    log_dir_name: str
    folder_path: Path
    config_dir_path: Path
    enable_extensions: bool
    extensions_dir_path: Path
    dry_run: bool
    sort_hidden: bool
    delete_empty_folders: bool
    exclude_str: str | None
    disabled_extensions: list[str]
    extension_options: dict[str, dict[str, object]]
    default_file_types: dict[str, list[str]]

default_config = DefaultConfig()

#endregion
