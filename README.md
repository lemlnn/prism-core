# prism-core

[View the Changelog](./CHANGELOG.md)
[Read the User Guide](./docs/USER_GUIDE.md)

A specialized file utility
by Lemuel L.

PRISM is a file organizer that automatically cleans up messy files while giving you safe ways to preview, undo, inspect, and customize behavior through persistent config profiles.

## Current Features

### Core

* extension-based file sorting
* duplicate-safe renaming
* optional hidden-file sorting

### Safety

* dry-run preview for `organize` and `undo`
* JSON run logs saved in `.prism_logs`
* undo for the most recent run or a specific log
* automatic cleanup and update of undo logs

### Config Profiles

* persistent config profile support via `~/.prism_config/*.json`
* runtime config loading with CLI override behavior
* default config initialization through `config --create`
* named profile selection through `-c` / `--config`
* runtime config saving through `config --save`
* available profile listing through `config --list`
* config path lookup through `config --path`
* organized config summary through `config --status`
* raw config display through `config --show`
* config reset through `config --reset`
* config deletion through `config --delete`
* debug mode persistence through config profiles  

### CLI

* command-based CLI interface via `argparse`

  * `organize` (`--dry-run`, `--sort-hidden`, `--exclude-str`)
  * `undo` (`--dry-run`, `--log-file`, `--exclude-str`)
  * `list-logs`
  * `config` (`--create`, `--save`, `--list`, `--path`, `--status`, `--show`, `--reset`, `--delete`)
* global profile selection through `-c` / `--config`
* global debug control through `--debug-mode` / `--no-debug-mode`
* top-level version reporting through `--version`

### Error Handling

* basic filesystem error handling during organize and undo tasks

## Quick Start

* check the current version
  `python prism-core.py --version`

* initialize the default profile
  `python prism-core.py config --create`

* organize files
  `python prism-core.py organize`

* preview without moving
  `python prism-core.py organize --dry-run`

* create and use a named profile
  `python prism-core.py -c photography config --create`
  `python prism-core.py -c photography organize`

* undo the most recent run
  `python prism-core.py undo`
  
* run with debug output
  `python prism-core.py --debug-mode organize`  
  
For full usage details, config profile workflows, and examples, see [docs/USER_GUIDE.md](./docs/USER_GUIDE.md).

## Planned/Future Features

* TUI support using `textual`
* flatten mode for moving files to prepare for the organize command
* `.exe` and `.pkg` packages
* possible extension system using a hooks/events model

## Currently Tested Platforms

* Windows 10/11
* Fedora KDE 42/43

## Credits

Special thanks to my alpha testers and early contributors.

### Development Team

* Lemuel ([@lemlnn](https://github.com)) - Lead Developer

### Alpha Testers

* Bella - beta macOS compatibility attempt
* Gavin ([@dojozycknar10-player](https://github.com)) - Windows 11 compatibility
* Maxwell ([@b135-crypto](https://github.com)) - planned Zorin OS and macOS compatibility

### Early Contributors

* Enoch ([@Wavefire5201](https://github.com))
* Gavin ([@dojozycknar10-player](https://github.com))

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
