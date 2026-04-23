# prism-core

[View the Changelog](./CHANGELOG.md) -
[Read the User Guide](./docs/USER_GUIDE.md) -
[Read the Architecture Map](./docs/ARCHITECTURE_MAP.md)

A safety-focused file utility
by Lemuel L.

PRISM is a Python CLI file organizer designed for repeatable cleanup workflows by focusing on safe organization through preview, undo, JSON run logs, and persistent config profiles.

## What PRISM Does

PRISM organizes top-level files into category folders based on file extension while giving you tools to inspect and reverse what happened.

Current core capabilities include:

- category-based file sorting
- duplicate-safe renaming
- dry-run preview
- JSON run logs
- undo from the most recent run or a specific log
- persistent config profiles
- debug tracing for internal behavior

## Why It Exists

PRISM is meant to make repetitive file cleanup safer and more controllable than a one-shot sorter script.

Instead of only moving files, it also supports:

- preview before action
- saved run history
- reversible organize flows
- profile-based behavior
- inspectable runtime state

## Quick Start

Check the current version:
`python prism-core.py --version`

Create the default config profile:
`python prism-core.py config --create`

Organize files:
`python prism-core.py organize`

Preview without moving anything:
`python prism-core.py organize --dry-run`

Undo the most recent run:
`python prism-core.py undo`

Run with debug output:
`python prism-core.py --debug-mode organize`

For detailed usage, profile workflows, and command examples, see the [User Guide](./docs/USER_GUIDE.md).

## Current System Areas

### Organize / Undo

- organize top-level files into category folders
- avoid overwriting by generating unique filenames
- record move history in `.prism_logs`
- undo previous runs using saved log data

### Config Profiles

- persistent profiles stored in `~/.prism_config/*.json`
- global profile selection with `-c` / `--config`
- runtime config saving with `config --save`
- config inspection with `config --status` and `config --show`
- config reset and deletion support

### Debugging / Inspection

- global `--debug-mode` / `--no-debug-mode`
- internal tracing for classification, target resolution, and undo behavior

## Current Architectural Direction

PRISM is now in a pre-extension architecture stage.

The current codebase separates:

- app-level command handling
- runtime/config state
- filesystem and classification behavior
- top-level organize / undo flows

That separation exists to make future extension-system work more sustainable for future updates.

For a higher-level view of how the system is currently structured, see the [Architecture Map](./docs/ARCHITECTURE_MAP.md).

## Planned / Future Areas

- extension system
- flatten mode
- TUI support using `textual`
- `.exe` and `.pkg` packaging
- possible future cloud-related support

## Currently Tested Platforms

- Windows 10/11
- Fedora KDE 42/43

## Credits

Special thanks to my alpha testers and early contributors.

### Development Team

- Lemuel ([@lemlnn](https://github.com)) - Lead Developer

### Alpha Testers

- Bella - beta macOS compatibility attempt
- Gavin ([@dojozycknar10-player](https://github.com)) - Windows 11 compatibility
- Maxwell ([@b135-crypto](https://github.com)) - planned Zorin OS and macOS compatibility

### Early Contributors

- Enoch ([@Wavefire5201](https://github.com))
- Gavin ([@dojozycknar10-player](https://github.com))

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
