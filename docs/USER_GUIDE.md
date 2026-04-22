# PRISM User Guide

## Overview

PRISM organizes top-level files into categorized folders based on file extension. It also supports dry-run previews, JSON logging, undo, persistent config profiles, and debug tracing for internal actions.

## Basic Commands

Organize files
`python prism-core.py organize`

Preview without moving files
`python prism-core.py organize --dry-run`

Run organize with debug output
`python prism-core.py --debug-mode organize`

Undo the most recent run
`python prism-core.py undo`

Run undo with debug output
`python prism-core.py --debug-mode undo`

List previous run logs
`python prism-core.py list-logs`

## Config Profiles

Profiles are stored in:
`~/.prism_config/`

The default profile is:
`default.json`

Select a profile globally with:
`-c PROFILE_NAME`
`--config PROFILE_NAME`

Example:
`python prism-core.py -c photography organize`

This uses:
`~/.prism_config/photography.json`

## Profile Commands

Create the default profile
`python prism-core.py config --create`

Create a named profile
`python prism-core.py -c photography config --create`

List available profiles
`python prism-core.py config --list`

Show the selected profile path
`python prism-core.py -c photography config --path`

Show an organized config summary
`python prism-core.py -c photography config --status`

Show the raw config JSON
`python prism-core.py -c photography config --show`

Reset the selected profile to defaults
`python prism-core.py -c photography config --reset`

Delete the selected profile
`python prism-core.py -c photography config --delete`

## Saving Runtime Settings into a Profile

Example:
`python prism-core.py -c photography config --save --dry-run --exclude-str "Draft"`

Another example:
`python prism-core.py -c dev config --save --debug-mode`

This saves the current runtime settings into the selected profile.

What each part means:

* `python prism-core.py`
  runs PRISM

* `-c photography`
  selects the profile named `photography`
  PRISM will use: `~/.prism_config/photography.json`

* `config`
  enters config-management mode

* `--save`
  saves the current runtime settings into the selected profile

* `--dry-run`
  sets `dry_run = true` before saving

* `--exclude-str "Draft"`
  sets `exclude_str = "Draft"` before saving

* `--debug-mode`
  sets `debug_mode = true` before saving

What this does:

1. PRISM loads the selected profile
2. the CLI flags temporarily override its values
3. `config --save` writes that final runtime state back into the profile

So after running this command, the selected profile can save settings like:

* `dry_run: true`
* `exclude_str: "Draft"`
* `debug_mode: true`

This is useful when you want to build or update a profile from the command line instead of editing JSON by hand.

## Runtime Setting Order

PRISM resolves settings in this order:

1. built-in defaults
2. selected config profile
3. CLI flag overrides

This applies to settings like `dry_run`, `exclude_str`, `sort_hidden`, and `debug_mode`.

CLI flags temporarily override saved settings unless you save them back into the selected profile with `config --save`.

## Example Workflows

Default everyday use
`python prism-core.py config --create`
`python prism-core.py organize`

Photo-specific profile
`python prism-core.py -c photography config --create`
`python prism-core.py -c photography config --save --dry-run --exclude-str "Draft"`
`python prism-core.py -c photography organize`

Debug a run
`python prism-core.py --debug-mode organize`
`python prism-core.py --debug-mode undo`

Inspect a profile before use
`python prism-core.py -c photography config --status`
`python prism-core.py -c photography config --show`

## Notes

* Use `--dry-run` before large organize runs.
* Use `--debug-mode` when you want extra internal tracing for classification, path resolution, and undo behavior.
* Use `list-logs` to review previous runs.
* Use `undo` to revert a previous organize run.
* Use named profiles to separate different workflows safely.
