# PRISM Extensions

## Status

The PRISM extension system is experimental as of `v1.3.0-devt4c`.

Extensions are disabled by default. The API may change or be added to before the stable v1.3.x release.

## Core Idea

Extensions suggest behavior, while core still retains these functionalities:

- file movement
- path validation
- duplicate-safe naming
- logs
- undo
- safety checks

This allows extensions to influence sorting without bypassing PRISM’s safety model.

## Enable Extensions

Extensions are disabled by default.

Enable extensions for one run:

```bash
prism --enable-extensions organize --dry-run
```

Create the default extensions directory:

```bash
prism extension --create
```

Use a custom extension directory:

```bash
prism --enable-extensions --extensions-dir ./extensions organize --dry-run
```

Save extension settings into a profile:

```bash
prism -c dev config --save --enable-extensions --extensions-dir ./extensions
```

Run later with that profile:

```bash
prism -c dev organize --dry-run
```

Default extension directory:

```text
~/.prism_extensions
```

## Extension Management Commands

Show loaded extension status:

```bash
prism --enable-extensions extension --status
```

List discovered extensions and show enabled/disabled state:

```bash
prism --enable-extensions extension --list
```

Disable one extension in the current config profile:

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

Named profiles work with extension commands too:

```bash
prism -c photography extension --disable pdf-classifier-APs-v1.0
prism -c photography extension --set-option metadata-image-sorter-v1.2 folder_format=year/month
```

## Config Fields

`v1.3.0-devt4c` adds these extension-related config fields:

```json
{
  "enable_extensions": true,
  "extensions_dir_path": "/path/to/extensions",
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

`disabled_extensions` can match an extension by declared `EXTENSION_NAME`, module name, file stem, or file name.

`extension_options` stores option dictionaries by extension name. PRISM stores and passes these options, but each extension decides whether to use them.

## Extension Loading

PRISM loads `.py` files from the selected extension directory.

Example:

```text
~/.prism_extensions/
├── photo_sorter.py
├── temp_file_skipper.py
└── _disabled_example.py
```

Files starting with `_` are ignored.

Disabled extensions are skipped before or after import, depending on whether PRISM can match the file/module name before loading.

If an extension fails to load, PRISM prints a warning and continues.

## Extension Metadata

Extensions may define:

```python
EXTENSION_NAME = "MyExtension"
EXTENSION_PRIORITY = 50
```

`EXTENSION_NAME` is used in debug output, warnings, disable/enable config matching, and option lookup.

`EXTENSION_PRIORITY` controls hook order. Higher priority runs first.

Suggested priority ranges:

- `100` = strongest/specific workflow extensions
- `90` = safety/skip filters
- `80` = metadata/photo/date sorters
- `50` = school/project/finance keyword sorters
- `10` = expanded file type packs
- `0` = default

## Per-Extension Options

When PRISM loads an extension, it attaches configured options to the module as:

```python
PRISM_EXTENSION_OPTIONS
```

Example extension usage:

```python
EXTENSION_NAME = "ExampleOptionExtension"
EXTENSION_PRIORITY = 50


def file_target_resolve(context):
    options = globals().get("PRISM_EXTENSION_OPTIONS", {})
    target_folder = options.get("target_folder", "Documents/Examples")

    if context.extension == ".example":
        return {
            "category": target_folder,
            "reason": "example extension option"
        }

    return None
```

Extensions may also define an optional configuration hook:

```python
EXTENSION_NAME = "ExampleConfiguredExtension"
EXTENSION_PRIORITY = 50

OPTIONS = {}


def configure_extension(options):
    global OPTIONS
    OPTIONS = dict(options)
```

PRISM calls `configure_extension(options)` after loading the module and before hook execution.

## Current Hooks

`v1.3.0-devt4c` supports two hooks:

- `file_should_process`
- `file_target_resolve`

Return `None` when your extension has no suggestion.

## `file_should_process`

Use this hook when an extension wants to suggest whether a file should be processed.

Example:

```python
EXTENSION_NAME = "TempFileSkipper"
EXTENSION_PRIORITY = 90


def file_should_process(context):
    if context.file_name.endswith(".tmp"):
        return {
            "process": False,
            "reason": "temporary file"
        }

    return None
```

Context fields:

```text
source_path
file_name
extension
is_hidden
working_folder
dry_run
```

Return format:

```python
{
    "process": False,
    "reason": "why this file should be skipped"
}
```

Rules:

- `process` must be a boolean.
- `reason` should be a short string.
- `None` means the extension has no opinion.
- The first valid suggestion wins based on priority order.

If `process` is `False`, PRISM skips the file.

If `process` is `True`, PRISM continues processing.

## `file_target_resolve`

Use this hook when an extension wants to suggest a different target category.

Example:

```python
EXTENSION_NAME = "MarkdownSorter"
EXTENSION_PRIORITY = 50


def file_target_resolve(context):
    if context.extension == ".md":
        return {
            "category": "Documents/Markdown",
            "reason": "markdown file"
        }

    return None
```

Context fields:

```text
source_path
file_name
extension
original_category
working_folder
```

Return format:

```python
{
    "category": "Documents/Markdown",
    "reason": "why this category was selected"
}
```

Rules:

- `category` must be a string.
- `category` must be a safe relative path.
- `reason` should be a short string.
- `None` means the extension has no opinion.
- The first valid suggestion wins based on priority order.

## Category Safety

Extension-provided categories must be safe relative paths.

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

Unsafe suggestions are ignored, which prevents extensions from routing files outside the working folder or using dangerous paths.

## Hook Order

Extensions are sorted by:

1. `EXTENSION_PRIORITY`
2. `EXTENSION_NAME`

Higher priority extensions run first, and this extension priority system allows certain extensions to take over overlapping roles.

Example:

```python
EXTENSION_PRIORITY = 90
```

runs before:

```python
EXTENSION_PRIORITY = 50
```

## Debugging Extensions

Use debug mode:

```bash
prism --debug-mode --enable-extensions organize --dry-run
```

Debug output can show:

- extension load order
- extension priority
- disabled extension skips
- applied option visibility in status output
- extension skip suggestions
- extension target suggestions
- invalid suggestion warnings
- hook failures

## Minimal Extension Template

```python
EXTENSION_NAME = "ExampleExtension"
EXTENSION_PRIORITY = 50


def configure_extension(options):
    # Optional. Only needed if this extension supports user options.
    pass


def file_should_process(context):
    return None


def file_target_resolve(context):
    return None
```

## Example: Sort Markdown Files

```python
EXTENSION_NAME = "MarkdownSorter"
EXTENSION_PRIORITY = 50


def file_target_resolve(context):
    if context.extension == ".md":
        return {
            "category": "Documents/Markdown",
            "reason": "markdown file"
        }

    return None
```

## Example: Skip Temporary Files

```python
EXTENSION_NAME = "TempFileSkipper"
EXTENSION_PRIORITY = 90


def file_should_process(context):
    if context.file_name.endswith(".tmp"):
        return {
            "process": False,
            "reason": "temporary file"
        }

    return None
```

## Development Notes

This extension system is not stable yet. For now, extensions should stay simple, local, and suggestion-based.

Expected future work:

- more hooks
- better examples
- possible extension manifests
- stronger option schemas
- better extension conflict reporting
- TUI display of extension options
