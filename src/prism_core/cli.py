import argparse
import importlib.util
import json
import os
import shutil
import sys
import textwrap
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

#region information
# naming convention:
# - constants: UPPER_SNAKE_CASE
# - variables/functions: snake_case
# - classes: PascalCase

# contributors as of now:
# - lemlnn/Lemuel
# - DevinDaboi314159/Devin

# extension info:
# - extension hook count: 2

# priority system:
# - 100 = strongest/specific workflow extension
# - 90  = safety/skip filters
# - 80  = metadata/photo/date sorter
# - 50  = school/project/finance keyword sorters
# - 10  = expanded file type packs
# - 0   = default

#endregion

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
    script_version: str = "1.3.0p-devt3a"
    log_dir_name: str = ".prism_logs"
    folder_path: Path = field(default_factory=Path.cwd)
    config_dir_path: Path = Path.home() / ".prism_config"
    enable_extensions: bool = False
    extensions_dir_path: Path = Path.home() / ".prism_extensions"
    dry_run: bool = False
    sort_hidden: bool = False
    delete_empty_folders: bool = False
    exclude_str: str | None = None
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
    default_file_types: dict[str, list[str]]

default_config = DefaultConfig()

#endregion

#region extension-models

@dataclass(frozen=True)
class FileTargetContext: #information given to file_target_resolve()
    source_path: Path
    file_name: str
    extension: str
    original_category: str
    working_folder: Path
@dataclass(frozen=True)
class TargetSuggestion: #information validated from file_target_resolve()
    category: str
    reason: str
    extension_name: str

@dataclass(frozen=True)
class FileShouldProcessContext: #information given to file_should_process()
    source_path: Path
    file_name: str
    extension: str
    is_hidden: bool
    working_folder: Path
    dry_run: bool
@dataclass(frozen=True)
class ProcessSuggestion: #information validated to file_should_process()
    process: bool
    reason: str
    extension_name: str
#endregion

#region extension-safety

def normalize_category(category: str) -> str: #normalizes the file paths across OSes
    return category.strip().replace("\\", "/")

def is_safe_relative_category(category: str) -> bool: #returns the file category/relative path instead of absolute
    category = normalize_category(category)

    if not category:
        return False
    if ":" in category: #blocks Windows style drive paths
        return False

    category_path = Path(category)

    if category_path.is_absolute():
        return False
    if any(part in {"..", "", "."} for part in category_path.parts): # blocks path traversal and weird empty/current parts
        return False

    return True

#endregion

#region extension-loader

class ExtensionLoader: #loads extensions from the specified folder
    
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def load(self) -> list:
        if not self.config.enable_extensions:
            return []

        extension_dir = self.config.extensions_dir_path

        if not extension_dir.exists():
            try:
                extension_dir.mkdir(parents=True, exist_ok=True)
                if self.config.debug_mode:
                    print(f"[debug] Created extension directory: {extension_dir}")
            except OSError as error:
                print(f"[warn] Could not create extension directory {extension_dir}: {error}")
                return []

        loaded_extensions = []

        for path in sorted(extension_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            try:
                module = self._load_module(path)
                loaded_extensions.append(module)
            except Exception as error:
                print(f"[warn] Failed to load extension {path.name}: {error}")

        loaded_extensions.sort(
            key=lambda module: (
                int(getattr(module, "EXTENSION_PRIORITY", 0)),
                str(getattr(module, "EXTENSION_NAME", module.__name__)),
            ),
            reverse=True,
        )

        if self.config.debug_mode and loaded_extensions:
            print("[debug] Extension hook order:")
            for module in loaded_extensions:
                ext_name = getattr(module, "EXTENSION_NAME", module.__name__)
                ext_priority = int(getattr(module, "EXTENSION_PRIORITY", 0))
                print(f"[debug]   {ext_name} (priority {ext_priority})")
        
        return loaded_extensions

    @staticmethod
    def _load_module(path: Path):
        module_name = f"prism_extension_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)

        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load extension spec: {path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

#endregion

#region extension-manager

class ExtensionManager: #calls hooks from the modules

    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.extensions = ExtensionLoader(config).load()

    @staticmethod
    def get_extension_name(module) -> str:
        return str(getattr(module, "EXTENSION_NAME", module.__name__))

    def call_hook(self, module, hook_name: str, context):
        hook = getattr(module, hook_name, None)

        if hook is None:
            return None
        try:
            return hook(context)
        except Exception as error:
            ext_name = self.get_extension_name(module)
            print(f"[warn] Extension hook failed in {ext_name}.{hook_name}: {error}")
            return None


#endregion

#region extension-hooks

FILE_TARGET_RESOLVE_HOOK = "file_target_resolve"
FILE_SHOULD_PROCESS_HOOK = "file_should_process"

def parse_target_suggestion(module, result) -> TargetSuggestion | None: # parses and validates raw output returned by file_target_resolve()
    ext_name = ExtensionManager.get_extension_name(module)

    if not isinstance(result, dict):
        print(f"[warn] Extension {ext_name} returned invalid target suggestion.")
        return None

    category = result.get("category")
    reason = result.get("reason", "extension suggestion")

    if not isinstance(category, str):
        print(f"[warn] Extension {ext_name} returned category that is not a string.")
        return None

    category = normalize_category(category)

    if not is_safe_relative_category(category):
        print(f"[warn] Extension {ext_name} returned unsafe category: {category}")
        return None
    return TargetSuggestion(
        category=category,
        reason=str(reason),
        extension_name=ext_name,
    )

def resolve_target_category(manager: ExtensionManager, context: FileTargetContext) -> TargetSuggestion | None: #specific hook system for file_target_resolve()
    for module in manager.extensions:
        result = manager.call_hook(module, FILE_TARGET_RESOLVE_HOOK, context)

        if result is None:
            continue

        suggestion = parse_target_suggestion(module, result)

        if suggestion is not None:
            return suggestion

    return None

def parse_process_suggestion(module, result) -> ProcessSuggestion | None: #parses and validates raw output returned by file_should_process()
    ext_name = ExtensionManager.get_extension_name(module)

    if not isinstance(result, dict):
        print(f"[warn] Extension {ext_name} returned invalid process suggestion.")
        return None

    process = result.get("process")
    reason = result.get("reason", "extension suggestion")

    if not isinstance(process, bool):
        print(f"[warn] Extension {ext_name} returned process that is not a bool.")
        return None

    return ProcessSuggestion(
        process=process,
        reason=str(reason),
        extension_name=ext_name,
    )

def should_process_file(manager: ExtensionManager, context: FileShouldProcessContext) -> ProcessSuggestion | None: #specific hook system for file_should_process()
    for module in manager.extensions:
        result = manager.call_hook(module, FILE_SHOULD_PROCESS_HOOK, context)

        if result is None:
            continue

        suggestion = parse_process_suggestion(module, result)

        if suggestion is not None:
            return suggestion

    return None


#endregion

#region prism-command-api

class PrismApp: #organized class of non file action functions

    def __init__(self, runtime_config: RuntimeConfig, config_path: Path):
        self.config = runtime_config
        self.config_path = config_path

    def handle_config_command(self, args: argparse.Namespace) -> None: #organizes config creation and logic
        if args.create:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            if self.config_path.exists():
                print(f"[info] Config already exists: {self.config_path}")
            else:
                write_default_config(self.config_path)
                print(f"[success] Wrote default config: {self.config_path}")
        elif args.save:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            write_config(self.config_path, self.config)
            print(f"[success] Saved runtime config to: {self.config_path}")
        elif args.list:
            list_configs(default_config.config_dir_path)
        elif args.path:
            print(f"[info] Config path: {self.config_path}")
            if self.config_path.exists():
                print("[info] Config file exists.")
            else:
                print("[info] Config file does not exist yet.")
        elif args.reset:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            write_default_config(self.config_path)
            print(f"[success] Reset config: {self.config_path}")
        elif args.delete:
            delete_config(self.config_path)
        elif args.status:
            show_config_status(self.config, self.config_path)
        elif args.show:
            print(json.dumps(serialize_config(self.config), indent=4))
        else: #suggested commands if user does not provide config parameters
            print("No config action provided.\n")
            print("Examples:")
            print(f"  {self.config.script_name} -c my_config config --create")
            print(f"  {self.config.script_name} config --list")
            print(f"  {self.config.script_name} config --save")
            print(f"  {self.config.script_name} config --status")
            print(f"  {self.config.script_name} config --show")
            print(f"  {self.config.script_name} config --reset")
            print(f"  {self.config.script_name} config --delete")
            print(f"  {self.config.script_name} config --help")
            pause_before_exit()

    def handle_extension_command(self, args: argparse.Namespace) -> None:
        if args.create:
            if self.config.extensions_dir_path.exists():
                print(f"[info] Extensions directory already exists: {self.config.extensions_dir_path}")
            else:
                try:
                    self.config.extensions_dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"[success] Created extensions directory: {self.config.extensions_dir_path}")
                except OSError as error:
                    print(f"[error] Could not create extensions directory {self.config.extensions_dir_path}: {error}")
        elif args.status:
            manager = ExtensionManager(self.config)

            print("PRISM Extension Status")
            print("----------------------")
            print(f"Extensions enabled : {self.config.enable_extensions}")
            print(f"Extensions folder  : {self.config.extensions_dir_path}")
            print(f"Loaded extensions  : {len(manager.extensions)}")

            if not self.config.enable_extensions:
                print("\n[info] Extensions are disabled.")
                print("[info] Use --enable-extensions to enable them for one run.")
                return
            if not manager.extensions:
                print("\n[info] No extensions loaded.")
                return

            print("\nLoaded extension details:")

            for module in manager.extensions:
                ext_name = ExtensionManager.get_extension_name(module)
                ext_priority = int(getattr(module, "EXTENSION_PRIORITY", 0))
                hooks = []

                if hasattr(module, FILE_SHOULD_PROCESS_HOOK):
                    hooks.append(FILE_SHOULD_PROCESS_HOOK)
                if hasattr(module, FILE_TARGET_RESOLVE_HOOK):
                    hooks.append(FILE_TARGET_RESOLVE_HOOK)

                hook_text = ", ".join(hooks) if hooks else "none"

                print(f"- {ext_name}")
                print(f"  Priority: {ext_priority}")
                print(f"  Hooks   : {hook_text}")
        else:
            print("No extension action provided.\n")
            print("Examples:")
            print(f"  {self.config.script_name} extension --create")
            print(f"  {self.config.script_name} extension --status")
            print(f"  {self.config.script_name} --enable-extensions extension --status")
            print(f"  {self.config.script_name} --enable-extensions --extensions-dir ./extensions extension --status")

#endregion

#region filesystem-entry-api

class FileEntryService: #responsible for reading directories and collecting top-level file entries

    @staticmethod
    def iterate_entries(path: Path): #more RAM efficient listdir()
        try:
            with os.scandir(path) as stream:
                yield from stream
        except PermissionError:
            print(f"[error] Access denied to {path}")
        except FileNotFoundError:
            print(f"[error] Folder {path} does not exist")
        except OSError as error_message:
            print(f"[error] System reported {error_message}")

    @staticmethod
    def get_entry_type(entry) -> str: #figures out if a entry is a folder or a file or something else
        try:
            if entry.is_dir(follow_symlinks=False):
                return "dir"
            if entry.is_file(follow_symlinks=False):
                return "file"
            return "unknown"
        except OSError as error_message:
            print(f"[error] System reported {error_message}")
            return "error"

    def collect_top_level_files(self, folder: Path, script_name: str) -> list[Path]:
        files = []
        current_file = Path(__file__).resolve()

        for entry in self.iterate_entries(folder):
            if self.get_entry_type(entry) != "file":
                continue

            entry_path = Path(entry.path).resolve()

            if entry_path == current_file:
                continue
            files.append(Path(entry.path))
            
        return files

#endregion

#region filesystem-classification-api

class FileClassificationService: #responsible for extension/category classification and skip decisions

    def __init__(self, config: RuntimeConfig):
        self.config = config

    @staticmethod 
    def is_hidden(path: Path) -> bool: #helper function to determine if a entry is hidden
        return path.name.startswith(".")

    @staticmethod
    def get_extension(path: Path) -> str: #helper function to determine what extension ending it has (ex: txt, pdf)
        return path.suffix.lower()

    @staticmethod
    def get_target_folder(extension: str, file_types: dict[str, list[str]]) -> str: #function to classify the file location based on the dict, first pass before extension suggestions
        for folder_name, extensions in file_types.items():
            if extension in extensions:
                return folder_name
        return "Others"

    def classify_file(self, path: Path) -> str: #function to unify the helper functions
        extension = self.get_extension(path)
        return self.get_target_folder(extension, self.config.default_file_types)

    def skip_file(self, path: Path) -> str | None: #function to determine if a file should be skipped, first pass before extension suggestions
        if self.config.exclude_str is not None and self.config.exclude_str in path.name:
            return "matches exclude string"
        if not self.config.sort_hidden and self.is_hidden(path):
            return "is hidden file"
        return None

    def skip_undo_move(self, original_path: Path, moved_path: Path) -> str | None: #function to determine if a file should be skipped (undo variant), fist pass before extension suggestions
        if self.config.exclude_str is not None and (
            self.config.exclude_str in original_path.name or self.config.exclude_str in moved_path.name
        ):
            return "matches exclude string"
        return None

#endregion

#region filesystem-process-api

class FileProcessResolver:  #responsible for extension-based process/skip decisions

    def __init__( #loads the config variables and services
        self,
        config: RuntimeConfig,
        classifier: FileClassificationService,
        extensions: ExtensionManager,
    ):
        self.config = config
        self.classifier = classifier
        self.extensions = extensions

    def build_file_should_process_context(self, path: Path, folder: Path) -> FileShouldProcessContext: #compiles the details of each file sorted for extensions to suggest paths
        return FileShouldProcessContext(
            source_path=path,
            file_name=path.name,
            extension=self.classifier.get_extension(path),
            is_hidden=self.classifier.is_hidden(path),
            working_folder=folder,
            dry_run=self.config.dry_run,
        )

    def extension_skip_reason(self, path: Path, folder: Path) -> str | None: #extension skip decision logic
        context = self.build_file_should_process_context(path, folder)
        suggestion = should_process_file(self.extensions, context)

        if suggestion is None:
            return None
        if suggestion.process:
            return None
        if self.config.debug_mode:
            print(
                f"[debug] Extension {suggestion.extension_name} "
                f"skipped {path.name} "
                f"({suggestion.reason})"
            )

        return f"extension {suggestion.extension_name}: {suggestion.reason}"

#endregion

#region filesystem-path-api

class FilePathService: #responsible for file path helpers and move functions

    def __init__(self, config: RuntimeConfig):
        self.config = config

    @staticmethod
    def get_unique_path(target_path: Path) -> Path: #duplicate file name handling
        if not target_path.exists():
            return target_path

        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent
        counter = 1

        while True:
            new_path = parent / f"{stem} ({counter}){suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    @staticmethod
    def path_exists(path: Path) -> bool: #helper function to determine if a path is occupied or not
        return path.exists()

    @staticmethod
    def move_file(source: Path, destination: Path) -> None: #function to do the moving of entries
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

    def abs_to_relative_path(self, path: Path, root: Path) -> str: #function to change absolute paths to relative paths for runs without debug mode
        debug_mode = self.config.debug_mode
        if debug_mode:
            return str(path)
        try:
            return str(path.relative_to(root))
        except ValueError:
            return str(path)

    def delete_empty_folders(self, folder: Path) -> int: #function to delete empty folders safely if the flag is turned on
        deleted_count = 0
        protected_names = {self.config.log_dir_name}

        for child in folder.iterdir():
            if not child.is_dir():
                continue
            if child.name in protected_names:
                continue
            try:
                next(child.iterdir())
            except StopIteration:
                try:
                    child.rmdir()
                    deleted_count += 1
                    if self.config.debug_mode:
                        print(f"[debug] Deleted empty folder: {child}")
                except OSError as error:
                    print(f"[warn] Could not delete empty folder {child}: {error}")
            except OSError as error:
                print(f"[warn] Could not inspect folder {child}: {error}")

        return deleted_count

#endregion

#region filesystem-target-api

class FileTargetResolver: #responsible for final file movement decision after extension suggestion

    def __init__( #loads the config variables and services
        self,
        config: RuntimeConfig,
        classifier: FileClassificationService,
        path_service: FilePathService,
        extensions: ExtensionManager,
    ):
        self.config = config
        self.classifier = classifier
        self.path_service = path_service
        self.extensions = extensions

    def build_file_target_context(self, path: Path, folder: Path, original_category: str) -> FileTargetContext: #builds the data packet sent to the extensions for classification
        return FileTargetContext(
            source_path=path,
            file_name=path.name,
            extension=self.classifier.get_extension(path),
            original_category=original_category,
            working_folder=folder,
        )

    def build_target_path(self, path: Path, folder: Path) -> Path: #extension returns the suggested folder path based on the data packet sent out
        original_category = self.classifier.classify_file(path) #original core classification
        folder_name = original_category
        context = self.build_file_target_context(path, folder, original_category)
        suggestion = resolve_target_category(self.extensions, context)

        if suggestion is not None:
            folder_name = suggestion.category
            if self.config.debug_mode:
                print(
                    f"[debug] Extension {suggestion.extension_name} "
                    f"suggested {folder_name} for {path.name} "
                    f"({suggestion.reason})"
                )

        target_path = folder / Path(folder_name) / path.name

        if target_path.exists():
            return self.path_service.get_unique_path(target_path)

        return target_path

#endregion

#region filesystem-service-api

class FileSystemService:  #responsible for functions used by the organize/undo commands

    def __init__(self, config: RuntimeConfig): #loads the config variables and services
        self.config = config
        self.extensions = ExtensionManager(config)
        self.entries = FileEntryService()
        self.classifier = FileClassificationService(config)
        self.paths = FilePathService(config)
        self.process = FileProcessResolver(config, self.classifier, self.extensions)
        self.targets = FileTargetResolver(config, self.classifier, self.paths, self.extensions)

    #grouped functions from the other filesystem and extension classes
    def collect_top_level_files(self, folder: Path) -> list[Path]: 
        return self.entries.collect_top_level_files(folder, self.config.script_name)

    def classify_file(self, path: Path) -> str:
        return self.classifier.classify_file(path)

    def skip_file(self, path: Path) -> str | None:
        return self.classifier.skip_file(path)

    def skip_undo_move(self, original_path: Path, moved_path: Path) -> str | None:
        return self.classifier.skip_undo_move(original_path, moved_path)

    def build_target_path(self, path: Path, folder: Path) -> Path:
        return self.targets.build_target_path(path, folder)
    
    def abs_to_relative_path(self, path: Path, root: Path) -> str:
        return self.paths.abs_to_relative_path(path, root)

    def delete_empty_folders(self, folder: Path) -> int:
        return self.paths.delete_empty_folders(folder)

    def get_unique_path(self, target_path: Path) -> Path:
        return self.paths.get_unique_path(target_path)

    def path_exists(self, path: Path) -> bool:
        return self.paths.path_exists(path)

    def move_file(self, source: Path, destination: Path) -> None:
        self.paths.move_file(source, destination)

    def extension_skip_reason(self, path: Path, folder: Path) -> str | None:
        return self.process.extension_skip_reason(path, folder)

#endregion

#region main-functions

def organize_files(folder: Path, runtime_config: RuntimeConfig) -> None: #core organize function
    fs = FileSystemService(runtime_config)
    files = fs.collect_top_level_files(folder)

    files_moved = 0
    files_skipped = 0
    errors = 0
    move_log = []

    for path in files:
        skip_reason = fs.skip_file(path)
        if skip_reason is not None:
            files_skipped += 1
            if runtime_config.dry_run:
                print(f"[dry-run] Skip: {path.name} ({skip_reason})")
            elif runtime_config.debug_mode:
                print(f"[debug] Skip: {path.name} ({skip_reason})")
            continue

        extension_skip_reason = fs.extension_skip_reason(path, folder)
        if extension_skip_reason is not None:
            files_skipped += 1
            if runtime_config.dry_run:
                print(f"[dry-run] Skip: {path.name} ({extension_skip_reason})")
            elif runtime_config.debug_mode:
                print(f"[debug] Skip: {path.name} ({extension_skip_reason})")
            continue

        target_path = fs.build_target_path(path, folder)
        display_path = fs.abs_to_relative_path(target_path, folder)

        if runtime_config.debug_mode:
            core_category = fs.classify_file(path)
            print(f"[debug] Core classified: {path.name} -> {core_category}")
            print(f"[debug] Final target path: {target_path}")
        if runtime_config.dry_run:
            print(f"[dry-run] Move: {path.name} -> {display_path}")
            files_moved += 1
            continue
        try:
            fs.move_file(path, target_path)
            print(f"[success] Moved: {path.name} -> {display_path}")
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

def undo_recent_organize(folder: Path, runtime_config: RuntimeConfig, log_file: str | None = None) -> None: #core undo function
    fs = FileSystemService(runtime_config)

    if log_file:
        log_path = folder / runtime_config.log_dir_name / log_file
        if not log_path.exists():
            print(f"[error] Log file not found: {log_path}")
            return
        if runtime_config.debug_mode:
            print(f"[debug] Using user-provided log file: {log_path}")
    else:
        log_path = get_latest_log(folder, runtime_config.log_dir_name)
        if log_path is None:
            print("[info] No log files found. Nothing to undo.")
            return
        if runtime_config.debug_mode:
            print(f"[debug] Using latest log file: {log_path}")

    move_log = load_log(log_path)
    if not move_log:
        print("[info] Log file is empty or unreadable. Nothing to undo.")
        return

    entries_undone = 0
    entries_skipped = 0
    errors = 0
    remaining_log = []

    for entry in reversed(move_log):
        original = Path(entry["original"])
        moved_to = Path(entry["moved_to"])
        skip_reason = fs.skip_undo_move(original, moved_to)

        if skip_reason is not None:
            remaining_log.insert(0, entry)
            entries_skipped += 1
            if runtime_config.dry_run:
                print(f"[dry-run] Skip: {original} ({skip_reason})")
            elif runtime_config.debug_mode:
                print(f"[debug] Skip: {original} ({skip_reason})")
            continue
        if not fs.path_exists(moved_to):
            if runtime_config.debug_mode:
                print(f"[debug] Missing moved file: {moved_to}")
            remaining_log.insert(0, entry)
            entries_skipped += 1
            errors += 1
            continue

        restore_target = fs.get_unique_path(original)
        display_path_moved = fs.abs_to_relative_path(moved_to, folder)
        display_path_restore = fs.abs_to_relative_path(restore_target, folder)

        if runtime_config.debug_mode:
            print(f"[debug] Restore target resolved: {original} -> {restore_target}")
        try:
            if runtime_config.dry_run:
                print(f"[dry-run] Undo: {display_path_moved} -> {display_path_restore}")
            else:
                fs.move_file(moved_to, restore_target)
                print(f"[success] Undo: {display_path_moved} -> {display_path_restore}")

            entries_undone += 1

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

    empty_folders_deleted = 0

    if runtime_config.delete_empty_folders and not runtime_config.dry_run:
        empty_folders_deleted = fs.delete_empty_folders(folder)
        if empty_folders_deleted:
            print(f"\n[cleanup] Deleted empty folders: {empty_folders_deleted}")

    print("\nUndo complete!")
    print(f"Total undone: {entries_undone}")
    print(f"Total skipped: {entries_skipped}")
    print(f"Total errors: {errors}")
    if runtime_config.delete_empty_folders:
        print(f"Empty folders deleted: {empty_folders_deleted}")

def pause_before_exit() -> None: #helper function to keep the window open after execution is finished/no command provided dialogue
    if sys.stdin is not None and sys.stdin.isatty():
        input("\nPress Enter to exit...")

#endregion

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

def load_log(log_path: Path) -> list[dict]: #function to read the log for the undo command
    try:
        with log_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as error:
        print(f"[warn] Could not read log file: {error}")
        return []

def get_latest_log(root: Path, log_dir_name: str) -> Path | None: #function to obtain the most recent log for the undo command
    log_dir = root / log_dir_name
    if not log_dir.exists():
        return None

    logs = sorted(log_dir.glob("organize_log_*.json"))
    return logs[-1] if logs else None

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
        exclude_str=(
            exclude_str_arg
            if exclude_str_arg is not None
            else loaded_config.get("exclude_str", default_config.exclude_str)
        ),
        delete_empty_folders=(
            delete_empty_folders_arg
            if delete_empty_folders_arg is not None
            else loaded_config.get("delete_empty_folders", default_config.delete_empty_folders)
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
    lines.append(f"  File categories     : {len(runtime_config.default_file_types)}")

    return lines


def show_config_status(runtime_config: RuntimeConfig, config_path: Path) -> None:
    for line in build_config_status(runtime_config, config_path):
        print(line)

#endregion

#region args-functions

def parse_args() -> argparse.Namespace: #function to load all arguments for the script
    usage_info = "%(prog)s [options] {organize,undo,list-logs,config} ..."

    example_usage = textwrap.dedent("""
        Commands:
          organize    Sort files into categorized folders
          undo        Revert the last organization run
          list-logs   Show history of previous runs
          config      Manage settings and custom profiles

        Examples:
          %(prog)s organize --dry-run
          %(prog)s --enable_extensions organize --dry-run
          %(prog)s --enable_extensions --extensions-dir ./extensions organize --dry-run
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
    global_group.add_argument(
        "--debug-mode",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable additional debug dialogues for actions"
    )
    global_group.add_argument(
        "--enable-extensions",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable extension framework"
    )
    global_group.add_argument(
        "--extensions-dir",
        metavar="PATH",
        dest="extensions_dir_path",
        type=str,
        default=None,
        help="Specify the extensions directory"
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
        default=None,
        help="Skip files containing this specific text"
    )

    organize_parser = subparsers.add_parser(
        "organize",
        parents=[shared_flags],
        help="Sort files into folders"
    )
    organize_parser.add_argument(
        "--sort-hidden",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include or exclude hidden files (starting with '.')"
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
    undo_parser.add_argument(
        "--delete-empty-folders",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Delete empty category folders after undo completes"
    )

    extension_parser = subparsers.add_parser(
        "extension",
        help="Manage and view extensions"
    )
    
    extension_actions = extension_parser.add_mutually_exclusive_group()
    extension_actions.add_argument("--status", action="store_true", help="Show current extension summary")
    extension_actions.add_argument("--create", action="store_true", help="Create the extensions directory")

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
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Set whether hidden files are included"
    )
    config_parser.add_argument(
        "--delete-empty-folders",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Set whether undo deletes empty category folders after restoring files"
    )

    config_actions = config_parser.add_mutually_exclusive_group()
    config_actions.add_argument("--create", action="store_true", help="Initialize a new config file")
    config_actions.add_argument("--save", action="store_true", help="Save current settings to profile")
    config_actions.add_argument("--list", action="store_true", help="List all saved profiles")
    config_actions.add_argument("--status", action="store_true", help="Show current profile summary")
    config_actions.add_argument("--show", action="store_true", help="Print raw JSON configuration")
    config_actions.add_argument("--path", action="store_true", help="Show location of config file")
    config_actions.add_argument("--reset", action="store_true", help="Restore profile to defaults")
    config_actions.add_argument("--delete", action="store_true", help="Remove the current config profile")

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {default_config.script_version}"
    )

    return parser.parse_args()

#endregion

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

if __name__ == "__main__":
    main()

#endregion
