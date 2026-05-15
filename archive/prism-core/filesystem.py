import os
import shutil
from pathlib import Path

from .defaults import RuntimeConfig
from .extensions import (
    ExtensionManager,
    FileShouldProcessContext,
    FileTargetContext,
    resolve_target_category,
    should_process_file,
)

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
