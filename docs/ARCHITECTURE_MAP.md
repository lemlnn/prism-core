# PRISM Architecture Map

## Overview

PRISM is currently a layered Python CLI tool with four main concerns:

- command parsing
- runtime/config state
- app-level command routing
- filesystem and organize/undo behavior

As of v1.2.4p, the codebase is in a pre-extension architecture stage.

## Current Runtime Objects

### `DefaultConfig`

`DefaultConfig` defines the built-in baseline state for the application, including:

- script metadata
- log directory name
- working folder
- config directory
- behavior defaults such as `dry_run`, `sort_hidden`, and `exclude_str`
- default file-type routing

This is the immutable baseline.

### `RuntimeConfig`

`RuntimeConfig` is the active runtime state used by the rest of the system.

It is built from:

1. built-in defaults
2. loaded config profile values
3. CLI overrides

This object is the main configuration payload that moves through the rest of PRISM.

## Main Layers

### 1. CLI / Entry Layer

The CLI layer is responsible for:

- defining top-level commands
- defining global options
- defining shared command flags
- parsing user input

Main entry points:
- `parse_args()`
- `main()`

This layer should answer:
“What did the user ask PRISM to do?”

### 2. Config / Runtime Layer

The config layer is responsible for:

- loading saved profile data
- serializing config values
- building runtime config
- saving and resetting profiles
- showing config status

Main functions:
- `load_config()`
- `build_runtime_config()`
- `write_config()`
- `write_default_config()`
- `serialize_config()`
- `show_config_status()`

This layer should answer:
“What runtime state should PRISM operate with?”

### 3. App Layer

The app layer currently exists as `PrismApp`.

Its main responsibility is config command handling.

Main class:
- `PrismApp`

Main method:
- `handle_config_command()`

This layer should answer:
“How should high-level application commands be handled?”

### 4. Filesystem / Behavior Layer

The filesystem layer currently exists as `FileSystemService`.

It is responsible for:

- iterating directory entries
- classifying files
- deciding skip behavior
- resolving target paths
- handling duplicate-safe naming
- moving files

Main class:
- `FileSystemService`

This layer should answer:
“How should file-level behavior work?”

### 5. Top-Level Operation Layer

These functions coordinate organize and undo flows using `RuntimeConfig` and `FileSystemService`.

Main functions:
- `organize_files()`
- `undo_recent_organize()`

This layer should answer:
“How do the main user-visible flows execute from start to finish?”

### 6. Logging Layer

The logging layer is responsible for:

- creating log paths
- saving run logs
- loading run logs
- finding the latest log
- listing available logs

Main functions:
- `create_log_path()`
- `save_log()`
- `load_log()`
- `get_latest_log()`
- `list_logs()`

This layer should answer:
“How does PRISM persist and inspect organize history?”

## Flow of Control

### Organize Flow

1. `main()` parses args
2. PRISM resolves the active config profile
3. `build_runtime_config()` creates `RuntimeConfig`
4. `organize_files()` starts the organize flow
5. `FileSystemService` collects files and classifies behavior
6. files are skipped, previewed, or moved
7. if not in dry-run mode, a JSON run log is saved
8. summary output is printed

### Undo Flow

1. `main()` parses args
2. PRISM resolves the active config profile
3. `build_runtime_config()` creates `RuntimeConfig`
4. `undo_recent_organize()` selects a log
5. move entries are processed in reverse
6. files are restored, skipped, or left unresolved
7. the log is updated or removed
8. summary output is printed

### Config Flow

1. `main()` parses args
2. config profile path is resolved
3. `build_runtime_config()` creates active runtime state
4. `PrismApp.handle_config_command()` routes the requested config action
5. config is created, saved, listed, shown, reset, or deleted

## Current Architectural Boundaries

PRISM currently has these meaningful boundaries:

- CLI parsing should not own file behavior
- config loading should not own organize/undo flow
- app-level command handling should not directly implement filesystem behavior
- filesystem behavior should not own CLI parsing
- organize/undo flows should coordinate, not absorb every low-level helper

These boundaries are the main reason v1.2.4p matters.

## Current Focus Areas

The next major architecture milestone is the extension system.

That future work will likely need to touch:

- registration model
- extension lifecycle
- public vs private core surfaces
- config interaction
- possible extension-defined settings
- future TUI/GUI configuration needs

That means the most sensitive current areas are:

- app/control routing
- runtime config representation
- filesystem behavior boundaries
- how much of classification / skip / move behavior should stay core-owned

## Future Extension Boundary Questions

These are the major future questions PRISM is currently approaching:

- how extensions should register themselves
- whether they should be command-based, hook-based, event-based, or mixed
- how much access they should have to core internals
- how extension-defined settings should be represented and validated
- how a future TUI/GUI could reflect plugin-defined configuration requirements
- what the first minimal extension surface should be
