# PRISM User Guide

## Overview

PRISM is a Python CLI folder cleanup tool.

It can:

- sort top-level files into category folders
- preview changes before moving files
- save JSON run logs
- undo previous organize runs
- use persistent config profiles
- edit config profiles from the CLI
- show debug output
- run experimental extensions
- enable/disable individual extensions
- store per-extension options

PRISM works from the current working directory unless the saved config says otherwise.

## Runtime Model

PRISM resolves settings in this order:

1. built-in defaults
2. selected config profile
3. CLI flags

CLI flags temporarily override profile values.

Use `config --save` when you want the current runtime settings written back into the selected profile.

Use `config --set` or `config --unset` when you want to directly edit saved profile values.

## Basic Commands

Check the installed version:

```bash
prism --version
```

Create the default config profile:

```bash
prism config --create
```

Preview organization without moving files:

```bash
prism organize --dry-run
```

Organize the current folder:

```bash
prism organize
```

Undo the most recent organize run:

```bash
prism undo
```

Undo a specific log:

```bash
prism undo --log-file organize_log_YYYYMMDD_HHMMSS.json
```

List saved organize logs:

```bash
prism list-logs
```

Run with debug output:

```bash
prism --debug-mode organize
```

If you are running the split source package directly, use:

```bash
python -m prism
```

## Organize

The organize command sorts top-level files into category folders.

Example:

```bash
prism organize
```

Preview first:

```bash
prism organize --dry-run
```

Include hidden files:

```bash
prism organize --sort-hidden
```

Skip files containing specific text:

```bash
prism organize --exclude-str "Draft"
```

Example result:

```text
report.pdf -> Documents/report.pdf
photo.jpg -> Images/photo.jpg
archive.zip -> Archives/archive.zip
```

If a target filename already exists, PRISM generates a safe duplicate name such as:

```text
report (1).pdf
```

## Undo

Undo restores files from a saved JSON run log.

Undo the most recent run:

```bash
prism undo
```

Undo a specific run:

```bash
prism undo --log-file organize_log_YYYYMMDD_HHMMSS.json
```

Preview an undo:

```bash
prism undo --dry-run
```

Undo and delete empty category folders afterward:

```bash
prism undo --delete-empty-folders
```

If an undo cannot fully complete, PRISM keeps or updates the remaining log entries instead of pretending everything was restored.

## Logs

PRISM saves organize logs inside:

```text
.prism_logs/
```

Logs are JSON files named like:

```text
organize_log_YYYYMMDD_HHMMSS.json
```

Each entry stores:

```json
{
  "original": "original/path/file.txt",
  "moved_to": "new/path/file.txt"
}
```

These logs make undo possible.

## Config Profiles

Profiles are stored in:

```text
~/.prism_config/
```

The default profile is:

```text
default.json
```

Select a named profile:

```bash
prism -c photography organize
```

This uses:

```text
~/.prism_config/photography.json
```

Create a profile:

```bash
prism -c photography config --create
```

List profiles:

```bash
prism config --list
```

Show the selected profile path:

```bash
prism -c photography config --path
```

Show a readable summary:

```bash
prism -c photography config --status
```

Show raw JSON:

```bash
prism -c photography config --show
```

Reset a profile:

```bash
prism -c photography config --reset
```

Delete a profile:

```bash
prism -c photography config --delete
```

## Saving Runtime Settings

Save current runtime settings into a profile:

```bash
prism -c photography config --save --dry-run --exclude-str "Draft"
```

Another example:

```bash
prism -c dev config --save --debug-mode
```

This process works like this:

1. PRISM loads built-in defaults.
2. PRISM loads the selected profile.
3. CLI flags override those values.
4. `config --save` writes the final runtime state into the profile.

Common saved settings include:

- `dry_run`
- `exclude_str`
- `sort_hidden`
- `debug_mode`
- `delete_empty_folders`
- `enable_extensions`
- `extensions_dir_path`
- `disabled_extensions`
- `extension_options`

## Editing Config Values

`v1.3.0-devt4c` adds direct config editing.

Set one value:

```bash
prism config --set sort_hidden=true
```

Set multiple values:

```bash
prism -c photography config --set enable_extensions=true extensions_dir_path=./extensions
```

Unset a value back to default:

```bash
prism config --unset sort_hidden
```

Unset multiple values:

```bash
prism config --unset exclude_str dry_run
```

Examples:

```bash
prism config --set dry_run=true
prism config --set exclude_str=Draft
prism config --set folder_path=./Downloads
prism config --set enable_extensions=true
```

Supported editable keys include:

- `debug_mode`
- `script_name`
- `log_dir_name`
- `folder_path`
- `config_dir_path`
- `enable_extensions`
- `extensions_dir_path`
- `dry_run`
- `sort_hidden`
- `delete_empty_folders`
- `exclude_str`
- `default_file_types`
- `disabled_extensions`
- `extension_options`

## Experimental Extensions

`v1.3.0-devt4c` continues the experimental extension framework.

Extensions are disabled by default.

Create the default extension directory:

```bash
prism extension --create
```

Default extension directory:

```text
~/.prism_extensions
```

Show extension status:

```bash
prism extension --status
```

Enable extensions for one run:

```bash
prism --enable-extensions organize --dry-run
```

Use a custom extension directory:

```bash
prism --enable-extensions --extensions-dir ./extensions organize --dry-run
```

Create a custom extension directory:

```bash
prism --extensions-dir ./extensions extension --create
```

Inspect loaded extensions from a custom directory:

```bash
prism --enable-extensions --extensions-dir ./extensions extension --status
```

List discovered extensions:

```bash
prism --enable-extensions extension --list
```

Save extension settings into a profile:

```bash
prism -c dev config --save --enable-extensions --extensions-dir ./extensions
```

Then run with that profile:

```bash
prism -c dev organize --dry-run
```

Current hooks:

- `file_should_process`
- `file_target_resolve`

See the Extension Guide for hook details and examples.

## Per-Extension Controls

Disable an extension in the current config:

```bash
prism extension --disable pdf-classifier-APs-v1.0
```

Enable it again:

```bash
prism extension --enable pdf-classifier-APs-v1.0
```

Set a per-extension option:

```bash
prism extension --set-option metadata-image-sorter-v1.2 prefer_filesystem_created=true
```

Remove a per-extension option:

```bash
prism extension --unset-option metadata-image-sorter-v1.2 prefer_filesystem_created
```

Use a named profile:

```bash
prism -c photography extension --disable pdf-classifier-APs-v1.0
prism -c photography extension --set-option metadata-image-sorter-v1.2 folder_format=year/month
```

Stored config example:

```json
{
  "disabled_extensions": [
    "pdf-classifier-APs-v1.0"
  ],
  "extension_options": {
    "metadata-image-sorter-v1.2": {
      "prefer_filesystem_created": true
    }
  }
}
```

PRISM stores extension options and passes them to loaded extensions. An extension must read `PRISM_EXTENSION_OPTIONS` or implement `configure_extension(options)` before those options affect behavior.

## Debugging

Enable debug output:

```bash
prism --debug-mode organize
```

Disable debug output explicitly:

```bash
prism --no-debug-mode organize
```

Debug output can show:

- file classification
- skip decisions
- target path resolution
- selected undo log
- missing moved files
- restore target paths
- extension loading order
- disabled extension skips
- extension options in status output
- extension skip or target suggestions

## Example Workflows

### Everyday Cleanup

```bash
prism config --create
prism organize --dry-run
prism organize
```

### Photo Folder Profile

```bash
prism -c photography config --create
prism -c photography config --save --dry-run --exclude-str "Draft"
prism -c photography config --set enable_extensions=true extensions_dir_path=./extensions
prism -c photography organize
```

### Extension Test Run

```bash
prism --debug-mode --enable-extensions --extensions-dir ./extensions organize --dry-run
```

### Disable a Specific Extension

```bash
prism extension --disable pdf-classifier-APs-v1.0
prism --enable-extensions extension --list
prism --enable-extensions organize --dry-run
```

### Safe Undo

```bash
prism list-logs
prism undo --dry-run
prism undo --delete-empty-folders
```

## Notes

- Use `--dry-run` before large organize runs.
- Use `undo` soon after organizing if you want an easy rollback.
- Use named profiles to separate workflows.
- Use debug mode when behavior looks unexpected.
- Treat the extension API as experimental until the stable v1.3.x release.
