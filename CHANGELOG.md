# Changelog

## PRISM [v1.3.0-devt2a] (4/30/26)

First experimental extension-system development build.

Added:

- extension loading
- extension priority ordering
- `--extensions-enabled`
- `--extensions-dir`
- `file_should_process` hook
- `file_target_resolve` hook
- extension context and suggestion models
- safe relative category validation
- extension debug output

Changed:

- added extension settings to runtime config
- split filesystem behavior into smaller service classes
- updated organize flow to support extension suggestions
- updated config status output to show extension settings

Notes:

- development build
- extension API is not stable yet
- PRISM core still owns validation, file movement, logs, and undo

## PRISM [v1.2.5p] (4/24/26)

Installability and final pre-extension preparation release.

Added:

- `pyproject.toml`
- package structure under `src/prism_core/`
- `prism` console command
- editable local install support
- `--delete-empty-folders` for undo cleanup

Changed:

- default runtime now works from the current working directory
- usage moved toward `prism ...` instead of direct script execution
- undo cleanup can remove empty category folders

## PRISM [v1.2.4p] (4/22/26)

Internal architecture cleanup release.

Added:

- debug mode
- `--debug-mode` / `--no-debug-mode`
- `PrismApp`
- `FileSystemService`
- debug tracing for organize and undo behavior

Changed:

- moved config command handling into `PrismApp`
- moved file behavior into a service layer
- cleaned up organize and undo control flow

## PRISM [v1.2.3p] (4/17/26)

Config profile workflow release.

Added:

- `-c` / `--config`
- `config --save`
- `config --list`
- `config --delete`
- shared runtime settings for config saving

Changed:

- config loading now supports named profiles
- config help and examples now reflect profile usage

## PRISM [v1.2.2p] (4/15/26)

Config inspection and reset release.

Added:

- `config --status`
- `config --show`
- `config --reset`
- `--version`

Changed:

- improved config command guidance
- separated config summary from raw JSON output

## PRISM [v1.2.1p] (4/15/26)

Small usability release after the first config-system update.

Added:

- pause-before-exit behavior when launched directly without a command
- `config --create`
- `config --path`

Changed:

- improved no-command output
- improved config command output when no action is provided

## PRISM [v1.2.0p] (4/14/26)

First real config-system release.

Added:

- persistent config support through `~/.prism_config/default.json`
- runtime config loading
- CLI override behavior

Changed:

- organize, undo, and logging now use runtime config
- file-type routing and log directory behavior became config-aware

## PRISM [v1.1.1p] (4/13/26)

Refinement release.

Added:

- `--exclude-str` for organize and undo

Changed:

- command functions now receive parsed args
- move output now shows fuller target paths

## PRISM [v1.1.0p] (4/11/26)

First major usability and safety expansion.

Added:

- command-based CLI
- `organize`
- `undo`
- `list-logs`
- JSON run logs
- targeted undo with `--log-file`
- `--sort-hidden`

Changed:

- organize now tracks moved, skipped, and errored files

## PRISM [v1.0.0p] (4/10/26)

Initial structured organizer release.

Added:

- top-level file collection
- category-based sorting
- duplicate-safe renaming
- dry-run preview
