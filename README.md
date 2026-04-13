# prism-core

A specialized file utility
by Lemuel L.

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
* CLI:
  * command-based CLI interface via `argparse` with 3 commands and their respective flags
    * `organize` (`--dry-run`, `--sort-hidden`, `--exclude-str`)
    * `undo` (`--dry-run`, `--log-file`, `--exclude-str`)
    * `list-logs`
* Error handling:
  * basic filesystem error handling during organize and undo tasks

**Planned Features:**

* TUI support using `textual`
* flatten mode for moving files to prepare for the organize command
* `.exe` and `.pkg` packages
* possible extension system using a hooks/events model

**Currently Tested Platforms:**

* Windows 10/11
* Fedora KDE 42/43
    
**Credits:**

* Development Team:
  * Lemuel ([@lemlnn](https://github.com)) - Lead Developer
* Alpha Testers:
  * Gavin ([@dojozycknar10-player](https://github.com)) - Windows 11 Compat
  * Maxwell ([@b135-crypto](https://github.com)) - Planned Zorin OS & macOS Compat
* Contributors:
  * Enoch ([@Wavefire5201](https://github.com))
  * Gavin ([@dojozycknar10-player](https://github.com))
