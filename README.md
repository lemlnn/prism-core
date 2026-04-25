# prism-core

[View the Changelog](./CHANGELOG.md) -
[Read the User Guide](./docs/USER_GUIDE.md) -
[Read the Architecture Map](./docs/ARCHITECTURE_MAP.md)

A safety-focused file utility  
by Lemuel L.

PRISM is a Python CLI file organizer designed for repeatable cleanup workflows. It focuses on safe organization through dry-run previews, undo support, JSON run logs, persistent config profiles, and installable command-line usage.

## What PRISM Does

PRISM organizes files into category folders based on file extension while giving you tools to inspect, configure, and reverse what happened.

Current core capabilities include:

- category-based file sorting
- duplicate-safe renaming
- dry-run preview
- JSON run logs
- undo from the most recent run or a specific log
- empty-folder cleanup after undo
- persistent config profiles
- debug tracing for internal behavior
- local editable installation with the `prism` command

## Why It Exists

PRISM is meant to make repetitive file cleanup safer and more controllable than a one-shot sorter script.

Instead of only moving files, it also supports:

- preview before action
- saved run history
- reversible organize flows
- profile-based behavior
- inspectable runtime state
- safer cleanup after undo

## Install

PRISM currently supports local editable installation from the repository.

```bash
git clone https://github.com/lemlnn/prism-core.git
cd prism-core
python -m pip install -e .
```

After installation, the `prism` command should be available:

```bash
prism --version
```

## Quick Start

Check the current version:

```bash
prism --version
```

Create the default config profile:

```bash
prism config --create
```

Preview organization without moving anything:

```bash
prism organize --dry-run
```

Organize files in the current folder:

```bash
prism organize
```

Undo the most recent run:

```bash
prism undo
```

Undo and remove empty category folders left behind by the organize run:

```bash
prism undo --delete-empty-folders
```

Run with debug output:

```bash
prism --debug-mode organize
```

For detailed usage, profile workflows, and command examples, see the [User Guide](./docs/USER_GUIDE.md).

## Current System Areas

### Organize / Undo

- organize top-level files into category folders
- avoid overwriting by generating unique filenames
- record move history in `.prism_logs`
- undo previous runs using saved log data
- optionally delete empty category folders after undo

### Config Profiles

- persistent profiles stored in `~/.prism_config/*.json`
- global profile selection with `-c` / `--config`
- runtime config saving with `config --save`
- config inspection with `config --status` and `config --show`
- config reset and deletion support

### Debugging / Inspection

- global `--debug-mode` / `--no-debug-mode`
- internal tracing for classification, target resolution, undo behavior, and cleanup behavior

### Installability

- package structure under `src/prism_core/`
- local editable install support (work in progress)
- console command entry point through `prism`
- current-working-directory based runtime behavior

## Current Architectural Direction

PRISM is now in its final pre-extension preparation stage.

The current codebase separates:

- app-level command handling
- runtime/config state
- filesystem and classification behavior
- top-level organize / undo flows
- package entry behavior

That separation exists to make future extension-system work more sustainable.

For a higher-level view of how the system is currently structured, see the [Architecture Map](./docs/ARCHITECTURE_MAP.md).

## Current Development Focus

Current release direction:

- v1.2.5p: installability, packaging groundwork, cleanup behavior, and final pre-extension preparation
- v1.3.x: extension-system foundation

The next major architectural goal is to build a safe extension framework where extensions can suggest behavior while the PRISM core continues to own file safety, path validation, moves, logs, and undo behavior.

## Planned / Future Areas

- extension system
- rule-based sorting
- flatten mode
- TUI support using `textual`
- GUI/rendering pipeline
- `.exe` and `.pkg` packaging
- advanced media/file workflow extensions
- possible future cloud-related support

## Currently Tested Platforms

- Windows 10/11
- Fedora KDE 42/43

## Credits

Special thanks to my alpha testers and early contributors.

### Development Team

- Lemuel ([@lemlnn](https://github.com/lemlnn)) - Lead Developer
- Devin ([@DevinEats314](https://github.com/DevinEats314)) - Co-Developer & Outreach

### Alpha Testers

- Bella - beta macOS compatibility attempt
- Gavin ([@dojozycknar10-player](https://github.com/dojozycknar10-player)) - Windows 11 compatibility
- Maxwell ([@b135-crypto](https://github.com/b135-crypto)) - planned Zorin OS and macOS compatibility

### Early Contributors

- Enoch ([@Wavefire5201](https://github.com/Wavefire5201))
- Gavin ([@dojozycknar10-player](https://github.com/dojozycknar10-player))
- Devin ([@DevinEats314](https://github.com/DevinEats314))

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
