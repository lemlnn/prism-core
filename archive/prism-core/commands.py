import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from .config_store import (
    delete_config,
    list_configs,
    serialize_config,
    show_config_status,
    write_config,
    write_default_config,
)
from .config_edit import (
    apply_config_sets,
    apply_config_unsets,
    build_config_data,
    disable_extension,
    enable_extension,
    set_extension_option,
    unset_extension_option,
    write_config_data,
)
from .defaults import RuntimeConfig, default_config
from .extensions import (
    ExtensionManager,
    FILE_SHOULD_PROCESS_HOOK,
    FILE_TARGET_RESOLVE_HOOK,
    is_extension_name_disabled,
)
from .filesystem import FileSystemService
from .logs import create_log_path, get_latest_log, load_log, save_log

#region prism-command-api

class PrismApp: #organized class of non file action functions

    def __init__(self, runtime_config: RuntimeConfig, config_path: Path):
        self.config = runtime_config
        self.config_path = config_path

    def build_editable_config_data(self) -> dict: #starts edits from the active runtime config
        return build_config_data(self.config)

    def save_config_data(self, config_data: dict) -> None: #writes edited config data to the selected profile
        write_config_data(self.config_path, config_data)

    def build_extension_scan_manager(self) -> ExtensionManager: #loads extensions for status/listing without applying disabled filters
        scan_config = replace(
            self.config,
            enable_extensions=True,
            disabled_extensions=[],
        )
        return ExtensionManager(scan_config)

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
        elif args.set_values is not None:
            config_data = self.build_editable_config_data()
            try:
                changed_keys = apply_config_sets(config_data, args.set_values)
            except ValueError as error:
                print(f"[error] {error}")
                return
            self.save_config_data(config_data)
            print(f"[success] Updated config: {self.config_path}")
            for key in changed_keys:
                print(f"  set {key}")
        elif args.unset_keys is not None:
            config_data = self.build_editable_config_data()
            try:
                changed_keys = apply_config_unsets(config_data, args.unset_keys)
            except ValueError as error:
                print(f"[error] {error}")
                return
            self.save_config_data(config_data)
            print(f"[success] Reset config values in: {self.config_path}")
            for key in changed_keys:
                print(f"  reset {key}")
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
        elif args.list:
            self.list_extensions()
        elif args.enable:
            config_data = self.build_editable_config_data()
            try:
                changed = enable_extension(config_data, args.enable)
            except ValueError as error:
                print(f"[error] {error}")
                return
            self.save_config_data(config_data)
            if changed:
                print(f"[success] Enabled extension in config: {args.enable}")
            else:
                print(f"[info] Extension was not disabled: {args.enable}")
            if not config_data.get("enable_extensions", False):
                print("[info] Global extensions are still disabled. Use config --set enable_extensions=true or --enable-extensions for one run.")
        elif args.disable:
            config_data = self.build_editable_config_data()
            try:
                changed = disable_extension(config_data, args.disable)
            except ValueError as error:
                print(f"[error] {error}")
                return
            self.save_config_data(config_data)
            if changed:
                print(f"[success] Disabled extension in config: {args.disable}")
            else:
                print(f"[info] Extension was already disabled: {args.disable}")
        elif args.set_option:
            extension_name, assignment = args.set_option
            config_data = self.build_editable_config_data()
            try:
                option_key, option_value = set_extension_option(config_data, extension_name, assignment)
            except ValueError as error:
                print(f"[error] {error}")
                return
            self.save_config_data(config_data)
            print(f"[success] Set option for {extension_name}: {option_key}={option_value}")
        elif args.unset_option:
            extension_name, option_key = args.unset_option
            config_data = self.build_editable_config_data()
            try:
                changed = unset_extension_option(config_data, extension_name, option_key)
            except ValueError as error:
                print(f"[error] {error}")
                return
            self.save_config_data(config_data)
            if changed:
                print(f"[success] Removed option from {extension_name}: {option_key}")
            else:
                print(f"[info] Option was not set for {extension_name}: {option_key}")
        elif args.status:
            self.show_extension_status()
        else:
            print("No extension action provided.\n")
            print("Examples:")
            print(f"  {self.config.script_name} extension --create")
            print(f"  {self.config.script_name} extension --status")
            print(f"  {self.config.script_name} extension --list")
            print(f"  {self.config.script_name} extension --disable pdf-classifier-APs-v1.0")
            print(f"  {self.config.script_name} extension --enable pdf-classifier-APs-v1.0")
            print(f"  {self.config.script_name} extension --set-option metadata-image-sorter-v1.2 prefer_created=true")
            print(f"  {self.config.script_name} extension --unset-option metadata-image-sorter-v1.2 prefer_created")
            print(f"  {self.config.script_name} --enable-extensions extension --status")
            print(f"  {self.config.script_name} --enable-extensions --extensions-dir ./extensions extension --status")

    def show_extension_status(self) -> None: #shows loaded extension details using current config filters
        manager = ExtensionManager(self.config)

        print("PRISM Extension Status")
        print("----------------------")
        print(f"Extensions enabled : {self.config.enable_extensions}")
        print(f"Extensions folder  : {self.config.extensions_dir_path}")
        print(f"Disabled filters   : {len(self.config.disabled_extensions)}")
        print(f"Loaded extensions  : {len(manager.extensions)}")

        if self.config.disabled_extensions:
            print("\nDisabled extensions:")
            for extension_name in self.config.disabled_extensions:
                print(f"- {extension_name}")

        if not self.config.enable_extensions:
            print("\n[info] Extensions are disabled.")
            print("[info] Use --enable-extensions to enable them for one run.")
            return
        if not manager.extensions:
            print("\n[info] No extensions loaded.")
            return

        print("\nLoaded extension details:")
        self.print_extension_modules(manager.extensions)

    def list_extensions(self) -> None: #lists discovered extensions and marks disabled state
        manager = self.build_extension_scan_manager()

        print("PRISM Extension List")
        print("--------------------")
        print(f"Extensions folder: {self.config.extensions_dir_path}")

        if not manager.extensions:
            print("[info] No extensions discovered.")
            return

        for module in manager.extensions:
            ext_name = ExtensionManager.get_extension_name(module)
            ext_priority = int(getattr(module, "EXTENSION_PRIORITY", 0))
            status = "disabled" if is_extension_name_disabled(self.config, ext_name, module.__name__) else "enabled"
            options = getattr(self.config, "extension_options", {}).get(ext_name, {})

            print(f"- {ext_name}")
            print(f"  Status  : {status}")
            print(f"  Priority: {ext_priority}")
            if options:
                print(f"  Options : {json.dumps(options, sort_keys=True)}")

    @staticmethod
    def print_extension_modules(modules: list) -> None: #prints extension modules with hook details
        for module in modules:
            ext_name = ExtensionManager.get_extension_name(module)
            ext_priority = int(getattr(module, "EXTENSION_PRIORITY", 0))
            hooks = []

            if hasattr(module, FILE_SHOULD_PROCESS_HOOK):
                hooks.append(FILE_SHOULD_PROCESS_HOOK)
            if hasattr(module, FILE_TARGET_RESOLVE_HOOK):
                hooks.append(FILE_TARGET_RESOLVE_HOOK)

            hook_text = ", ".join(hooks) if hooks else "none"
            options = getattr(module, "PRISM_EXTENSION_OPTIONS", {})

            print(f"- {ext_name}")
            print(f"  Priority: {ext_priority}")
            print(f"  Hooks   : {hook_text}")
            if options:
                print(f"  Options : {json.dumps(options, sort_keys=True)}")

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
