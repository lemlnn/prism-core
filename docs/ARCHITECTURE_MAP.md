# PRISM Architecture Map

## Overview

PRISM is a layered Python CLI tool with these main concerns:

- command parsing
- runtime/config state
- app-level command routing
- filesystem behavior
- extension loading and hook dispatch
- organize/undo coordination
- logging

As of `v1.3.0-devt3a`, PRISM has entered the first experimental extension-system stage.

## Runtime Objects

### `DefaultConfig`

`DefaultConfig` defines the built-in baseline state.

It includes:

- script metadata
- version
- log directory name
- working folder
- config directory
- extension settings
- behavior defaults
- default file-type routing

This is the immutable baseline.

### `RuntimeConfig`

`RuntimeConfig` is the active state used during a run.

It is built from:

1. built-in defaults
2. selected config profile
3. CLI overrides

Most major services receive `RuntimeConfig` instead of reading global settings directly.

## Main Layers

## 1. CLI / Entry Layer

Responsible for:

- defining commands
- defining global options
- defining shared flags
- parsing user input
- routing into the main command flow

Main entry points:

- `parse_args()`
- `main()`

This layer answers:

> What did the user ask PRISM to do?

## 2. Config / Runtime Layer

Responsible for:

- loading profile JSON
- building runtime config
- serializing config
- saving profiles
- resetting profiles
- showing config status

Main functions:

- `load_config()`
- `build_runtime_config()`
- `write_config()`
- `write_default_config()`
- `serialize_config()`
- `show_config_status()`

This layer answers:

> What runtime state should PRISM use?

## 3. App Layer

The app layer currently exists as `PrismApp`.

Responsible for:

- high-level config command handling
- config action routing
- keeping config command logic out of `main()`

Main class:

- `PrismApp`

Main method:

- `handle_config_command()`

This layer answers:

> How should high-level application commands be handled?

## 4. Extension Layer

The extension layer is experimental.

Responsible for:

- loading local `.py` extension files
- skipping files that start with `_`
- ordering extensions by priority
- calling supported hooks safely
- validating extension suggestions before core uses them

Main classes:

- `ExtensionLoader`
- `ExtensionManager`

Current hooks:

- `file_should_process`
- `file_target_resolve`

Main models:

- `FileShouldProcessContext`
- `ProcessSuggestion`
- `FileTargetContext`
- `TargetSuggestion`

This layer answers:

> What optional behavior have extensions suggested, and is it safe enough for core to use?

## 5. Filesystem / Behavior Layer

Responsible for:

- reading directory entries
- collecting top-level files
- classifying files
- deciding skip behavior
- resolving target paths
- generating duplicate-safe names
- moving files
- deleting empty folders after undo

Main classes:

- `FileEntryService`
- `FileClassificationService`
- `FileProcessResolver`
- `FilePathService`
- `FileTargetResolver`
- `FileSystemService`

This layer answers:

> How should file-level behavior work?

## 6. Top-Level Operation Layer

Responsible for coordinating user-visible flows.

Main functions:

- `organize_files()`
- `undo_recent_organize()`

This layer does not own every low-level detail. It coordinates config, filesystem behavior, extension suggestions, logging, and output.

This layer answers:

> How do organize and undo execute from start to finish?

## 7. Logging Layer

Responsible for:

- creating log directories
- creating log paths
- saving run logs
- loading run logs
- finding the latest log
- listing logs

Main functions:

- `check_log_dir()`
- `create_log_path()`
- `save_log()`
- `load_log()`
- `get_latest_log()`
- `list_logs()`

This layer answers:

> How does PRISM persist and inspect organize history?

## Organize Flow

1. `main()` parses args.
2. PRISM resolves the config profile path.
3. `load_config()` loads saved profile data.
4. `build_runtime_config()` creates active runtime state.
5. `organize_files()` starts the organize flow.
6. `FileSystemService` collects top-level files.
7. Core skip rules run.
8. Extension skip suggestions may run.
9. Core classification determines the original category.
10. Extension target suggestions may override the category after validation.
11. PRISM previews or moves files.
12. If files were moved, a JSON run log is saved.
13. Summary output is printed.

## Undo Flow

1. `main()` parses args.
2. PRISM resolves runtime config.
3. `undo_recent_organize()` selects a log.
4. Log entries are processed in reverse order.
5. Core skip rules run.
6. PRISM resolves safe restore targets.
7. Files are previewed or restored.
8. The log is updated or removed.
9. Empty folders may be deleted if enabled.
10. Summary output is printed.

## Config Flow

1. `main()` parses args.
2. PRISM resolves the selected profile path.
3. `load_config()` loads profile data if it exists.
4. `build_runtime_config()` applies CLI overrides.
5. `PrismApp.handle_config_command()` routes the config action.
6. The profile is created, saved, listed, shown, reset, or deleted.

## Extension Flow

1. `main()` parses args.
2. PRISM resolves the selected config profile.
3. `load_config()` loads profile data if it exists.
4. `build_runtime_config()` applies CLI overrides.
5. `PrismApp.handle_extension_command()` routes the extension action.
6. `extension --create` creates the configured extension directory.
7. `extension --status` shows extension settings and loaded extension details.
8. If extensions are enabled, `ExtensionManager` loads extension modules for inspection.

## Current Boundaries

PRISM currently follows these boundaries:

- CLI parsing should not own file behavior.
- Config loading should not own organize/undo flow.
- App command handling should not directly implement filesystem behavior.
- Filesystem behavior should not own CLI parsing.
- Extensions should suggest behavior, not directly control core safety.
- Organize/undo should coordinate instead of absorbing every helper.
- Core should own path validation, moves, logs, and undo.

## Extension Safety Boundary

Extensions may suggest:

- whether a file should be processed
- what category a file should route to

Extensions should not own:

- actual file movement
- absolute target paths
- path traversal
- undo log integrity
- duplicate-safe naming
- core validation

Extension target categories must be safe relative paths.

Allowed:

```text
Documents/Markdown
Images/Sony
School/AP_Bio
```

Blocked:

```text
../OutsideFolder
/home/user/Desktop
C:/Users/name/Desktop
.
empty string
```

## Current Focus Areas

The current milestone is stabilizing the experimental extension system.

Current extension surface:

- local extension discovery
- extension priority ordering
- hook dispatch
- process/skip suggestions
- target-folder suggestions
- safe category validation

Sensitive areas:

- keeping core-owned safety boundaries clear
- deciding which hooks become stable public API
- preventing extensions from bypassing path safety
- deciding how extension settings should be represented
- keeping logs reliable when extensions influence routing
- preparing the extension model for future TUI/GUI use

## Remaining Extension Questions

Before the extension API becomes stable, this update still needs to resolve these questions:

- how many hooks belong in the first stable API
- whether extensions should only suggest behavior or also add commands
- how extension-defined settings should be stored
- whether extension metadata should use a manifest file
- how extension conflicts should be reported
- how a TUI/GUI should display extension options
- how much of the context model should become public API
