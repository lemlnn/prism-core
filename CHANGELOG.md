# Changelog

## PRISM [v1.3.0-devt4c] (5/15/26)

Config editing and per-extension control development build.

Added:

- `config_edit.py` for controlled profile editing helpers
- `config --set KEY=VALUE [KEY=VALUE ...]`
- `config --unset KEY [KEY ...]`
- `disabled_extensions` config field
- `extension_options` config field
- `extension --list` to show discovered extensions and enabled/disabled state
- `extension --enable NAME` to remove an extension from the disabled list
- `extension --disable NAME` to add an extension to the disabled list
- `extension --set-option NAME KEY=VALUE` for per-extension option storage
- `extension --unset-option NAME KEY` for removing per-extension options
- `PRISM_EXTENSION_OPTIONS` injection into loaded extension modules
- optional `configure_extension(options)` hook for extension setup

Changed:

- extension loader now skips extensions listed in `disabled_extensions`
- extension loader now applies per-extension options after loading a module
- extension status output now includes disabled filters
- extension list output now shows status, priority, and configured options
- config status output now includes disabled extension and extension option counts
- config serialization now preserves `disabled_extensions` and `extension_options`
- built-in CLI help now includes config editing and per-extension control examples

Notes:

- development build
- extension options are stored by PRISM, but individual extensions must read `PRISM_EXTENSION_OPTIONS` or implement `configure_extension(options)` to use them
- extension API is still experimental

## PRISM [v1.3.0-devt4b] (5/11/26)

Package split development build.

Added:

- split package layout under `src/prism/`
- `defaults.py` for default config and runtime config models
- `extensions.py` for extension models, safety, loading, and hook dispatch
- `filesystem.py` for file collection, classification, path resolution, and movement services
- `logs.py` for organize logs, log inspection, and log loading helpers
- `config_store.py` for config load/save/serialize/status behavior
- `commands.py` for high-level organize, undo, config, and extension commands
- `cli.py` for argparse command definitions
- `main.py` and `__main__.py` for package entry flow
- `README_SPLIT.md` for split-build notes

Changed:

- moved the former single-file architecture into smaller modules
- kept organize, undo, config, logs, and extension behavior in the same general pipeline
- prepared the project structure for future TUI and planner work

Notes:

- development build
- intended as a structure/refactor checkpoint before additional v1.3.0 features

## PRISM [v1.3.0-devt3a] (5/6/26)

Extension usability and CLI output polish release.

Added:

- `extension` command for extension management and inspection
- `extension --status` to show extension runtime status
- `extension --create` to create the configured extensions directory
- loaded extension count in extension status output
- loaded extension detail output with name, priority, and supported hooks

Changed:

- normal organize and undo output now uses cleaner relative paths
- debug output still keeps full technical paths
- extension examples now use `--enable-extensions`
- extension docs now include extension directory creation and status commands

Notes:

- development build
- extension API is still experimental

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
