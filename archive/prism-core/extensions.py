import importlib.util
from dataclasses import dataclass
from pathlib import Path

from .defaults import RuntimeConfig

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


def normalize_extension_lookup_name(name: str) -> str: #normalizes extension names for config matching
    return str(name).strip().lower()


def is_extension_name_disabled(config: RuntimeConfig, *names: str) -> bool: #checks disabled_extensions against file stem/module names
    disabled_names = {
        normalize_extension_lookup_name(item)
        for item in getattr(config, "disabled_extensions", [])
    }

    return any(
        normalize_extension_lookup_name(name) in disabled_names
        for name in names
        if name
    )


def get_extension_options(config: RuntimeConfig, extension_name: str, module_name: str = "") -> dict: #gets per-extension options by EXTENSION_NAME or module name
    options_map = getattr(config, "extension_options", {})

    if not isinstance(options_map, dict):
        return {}

    for lookup_name in (extension_name, module_name):
        if not lookup_name:
            continue
        for stored_name, options in options_map.items():
            if normalize_extension_lookup_name(stored_name) == normalize_extension_lookup_name(lookup_name):
                return dict(options) if isinstance(options, dict) else {}

    return {}


def apply_extension_options(module, options: dict) -> None: #exposes per-extension options to loaded extension modules
    setattr(module, "PRISM_EXTENSION_OPTIONS", options)

    configure_hook = getattr(module, "configure_extension", None)

    if configure_hook is None:
        return

    if not callable(configure_hook):
        return

    configure_hook(options)

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

            if is_extension_name_disabled(self.config, path.stem, path.name):
                if self.config.debug_mode:
                    print(f"[debug] Skipped disabled extension file: {path.name}")
                continue

            try:
                module = self._load_module(path)
                ext_name = str(getattr(module, "EXTENSION_NAME", module.__name__))

                if is_extension_name_disabled(self.config, ext_name, module.__name__, path.stem, path.name):
                    if self.config.debug_mode:
                        print(f"[debug] Skipped disabled extension: {ext_name}")
                    continue

                options = get_extension_options(self.config, ext_name, module.__name__)
                apply_extension_options(module, options)
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
