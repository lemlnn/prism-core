# PRISM User Guide

## Overview

PRISM is a Python CLI folder cleanup tool.

It can:

- sort top-level files into category folders
- preview changes before moving files
- save JSON run logs
- undo previous organize runs
- use persistent config profiles
- show debug output
- run experimental extensions

PRISM works from the current working directory unless the saved config says otherwise.

## Runtime Model

PRISM resolves settings in this order:

1. built-in defaults
2. selected config profile
3. CLI flags

CLI flags temporarily override profile values.

Use `config --save` when you want the current runtime settings written back into the selected profile.

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

If you are running the development script directly, replace `prism` with:

```bash
python PRISM-v1.3.0-devt3a.py
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

## Experimental Extensions

`v1.3.0-devt3a` continues the experimental extension framework.

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
prism -c photography organize
```

### Extension Test Run

```bash
prism --debug-mode --extensions-enabled --extensions-dir ./extensions organize --dry-run
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
