# prism-core

A safe folder cleanup tool that sorts files, previews changes, and lets you undo mistakes.

[Changelog](./CHANGELOG.md) - [User Guide](./docs/USER_GUIDE.md) - [Extension Guide](./docs/EXTENSIONS.md) - [Architecture Map](./docs/ARCHITECTURE_MAP.md) - [Discord Server](https://discord.gg/6G5PPS23fD)

PRISM helps clean messy folders by sorting files into categories like Images, Documents, Videos, and Archives. It can preview changes before moving anything, save logs of what happened, undo previous organize runs, use persistent config profiles, and run experimental extensions for custom sorting behavior.

> `v1.3.0-devt4c` is a development build. The extension system, config editing commands, and per-extension settings are experimental and may change before the stable v1.3.x release.

## Features

- sorts top-level files into category folders
- previews changes with dry-run mode
- avoids overwriting duplicate filenames
- saves JSON run logs
- can undo previous organize runs
- supports persistent config profiles
- supports direct config editing with `config --set` and `config --unset`
- includes debug output for inspection
- supports experimental extension-based sorting
- supports per-extension enable/disable controls
- supports per-extension option storage

## Install

```bash
git clone https://github.com/lemlnn/prism-core.git
cd prism-core
python -m pip install .
```

After installation:

```bash
prism --version
```

For editable local development:

```bash
python -m pip install -e .
```

## Quick Start

Create the default config profile:

```bash
prism config --create
```

Preview a cleanup:

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

Undo and remove empty category folders:

```bash
prism undo --delete-empty-folders
```

List saved organize logs:

```bash
prism list-logs
```

Inspect the most recent organize log:

```bash
prism inspect
```

Inspect a specific organize log:

```bash
prism inspect --log-file organize_log_YYYYMMDD_HHMMSS.json
```

Run with debug output:

```bash
prism --debug-mode organize
```

## Config Profiles

Profiles are stored in:

```text
~/.prism_config/
```

The default profile is:

```text
default.json
```

Create a named profile:

```bash
prism -c photography config --create
```

Use a named profile:

```bash
prism -c photography organize --dry-run
```

Show a readable config summary:

```bash
prism -c photography config --status
```

Show raw JSON:

```bash
prism -c photography config --show
```

Save current runtime settings into a profile:

```bash
prism -c photography config --save --dry-run --exclude-str "Draft"
```

## Direct Config Editing

`v1.3.0-devt4c` adds direct config editing commands.

Set one or more config values:

```bash
prism config --set sort_hidden=true enable_extensions=true
```

Set values inside a named profile:

```bash
prism -c photography config --set dry_run=true exclude_str=Draft
```

Unset values and fall back to defaults:

```bash
prism config --unset sort_hidden exclude_str
```

Common editable config keys include:

- `debug_mode`
- `dry_run`
- `sort_hidden`
- `delete_empty_folders`
- `exclude_str`
- `enable_extensions`
- `extensions_dir_path`
- `disabled_extensions`
- `extension_options`

## Experimental Extensions

Extensions are disabled by default.

Enable extensions for one run:

```bash
prism --enable-extensions organize --dry-run
```

Create the default extensions directory:

```bash
prism extension --create
```

Show extension status:

```bash
prism extension --status
```

List discovered extensions and whether they are enabled or disabled:

```bash
prism --enable-extensions extension --list
```

Use a custom extension folder:

```bash
prism --enable-extensions --extensions-dir ./extensions organize --dry-run
```

Inspect loaded extensions from a custom folder:

```bash
prism --enable-extensions --extensions-dir ./extensions extension --status
```

Current hooks:

- `file_should_process`
- `file_target_resolve`

Extensions can suggest behavior, but PRISM core still owns file movement, path validation, duplicate-safe naming, logs, undo, and core safety checks.

## Per-Extension Controls

`v1.3.0-devt4c` adds per-extension enable/disable controls.

Disable an extension in the current config profile:

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

Unset a per-extension option:

```bash
prism extension --unset-option metadata-image-sorter-v1.2 prefer_filesystem_created
```

Per-extension options are stored in the selected config profile under `extension_options`. Extensions can read those values through `PRISM_EXTENSION_OPTIONS` or an optional `configure_extension(options)` function.

## Development Build Notes

The current split package structure is organized under `src/prism/`:

```text
src/prism/
  __init__.py
  __main__.py
  defaults.py
  extensions.py
  filesystem.py
  logs.py
  config_store.py
  config_edit.py
  commands.py
  cli.py
  main.py
```

The main design boundary is still the same: extensions suggest behavior, while PRISM core owns safe execution.

## Tested Platforms

- Windows 10/11 (restricted, unrestricted)
- Fedora KDE 42/43
- EndeavorOS

## Credits

Special thanks to my early contributors and testers.

Development Team:

- Lemuel ([@lemlnn](https://github.com/lemlnn)) - Lead Developer
- Devin ([@DevinEats314](https://github.com/DevinEats314)) - Co-Developer & Outreach

Alpha Testers:

- Bella - beta macOS compatibility attempt
- Gavin ([@dojozycknar10-player](https://github.com/dojozycknar10-player)) - Windows 11 restricted environment compatibility
- Maxwell ([@b135-crypto](https://github.com/b135-crypto)) - planned Zorin OS and macOS compatibility

Early Contributors:

- Enoch ([@Wavefire5201](https://github.com/Wavefire5201))
- Gavin ([@dojozycknar10-player](https://github.com/dojozycknar10-player))
- Devin ([@DevinEats314](https://github.com/DevinEats314))

## License

Apache License 2.0. See the LICENSE file for details.
