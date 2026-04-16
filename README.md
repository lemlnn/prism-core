# prism-core

[View the Changelog](./CHANGELOG.md)

A specialized file utility
by Lemuel L.

PRISM is a tool that automatically cleans up and organizes messy files while giving you safe ways to preview, undo, inspect, and customize its behavior through persistent config.

**Current Features:**

* Core:

  * extension-based file sorting
  * duplicate-safe renaming
  * optional hidden-file sorting

* Safety:

  * supports dry-run preview for organize and undo
  * saves organize runs as JSON logs in `.prism_logs`
  * undo for the most recent run or a specific log
  * automatic cleanup/update of undo logs

* Config:

  * persistent config support via `~/.prism_config/default.json`
  * runtime config loading with CLI override behavior
  * default config initialization through `config --create`
  * config path lookup through `config --path`
  * organized config summary through `config --status`
  * raw config display through `config --show`
  * config reset through `config --reset`

* CLI:

  * command-based CLI interface via `argparse` with 4 commands and their respective flags

    * `organize` (`--dry-run`, `--sort-hidden`, `--exclude-str`)
    * `undo` (`--dry-run`, `--log-file`, `--exclude-str`)
    * `list-logs`
    * `config` (`--create`, `--path`, `--status`, `--show`, `--reset`)
  * top-level version reporting through `--version`

* Error handling:

  * basic filesystem error handling during organize and undo tasks

**Quick Start:**

* check the current version:
  * `python prism-core.py --version`
* initialize default config:
  * `python prism-core.py config --create`
* show config path:
  * `python prism-core.py config --path`
* show config status:
  * `python prism-core.py config --status`
* show raw config JSON:
  * `python prism-core.py config --show`
* organize files:
  * `python prism-core.py organize`
* preview without moving:
  * `python prism-core.py organize --dry-run`
* undo the most recent run:
  * `python prism-core.py undo`

**Planned Features:**

* TUI support using `textual`
* flatten mode for moving files to prepare for the organize command
* `.exe` and `.pkg` packages
* possible extension system using a hooks/events model

**Currently Tested Platforms:**

* Windows 10/11
* Fedora KDE 42/43

**Credits:**
Special thanks to my Alpha testers and early contributors!

* Development Team:

  * Lemuel ([@lemlnn](https://github.com)) - Lead Developer

* Alpha Testers:

  * Bella - beta macOS compatibility attempt
  * Gavin ([@dojozycknar10-player](https://github.com)) - Windows 11 compatibility
  * Maxwell ([@b135-crypto](https://github.com)) - planned Zorin OS and macOS compatibility

* Early Contributors:

  * Enoch ([@Wavefire5201](https://github.com))
  * Gavin ([@dojozycknar10-player](https://github.com))

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
