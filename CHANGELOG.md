# Changelog  
  
## PRISM [v1.2.4p] (4/22/26)

PRISM v1.2.4p is a pre-extension architecture release focused on internal structure, control flow cleanup, and better separation of responsibilities. It introduces a dedicated app layer for config command handling, a filesystem service layer for file operations and classification logic, and a new debug mode for tracing internal behavior. This release does not add major end-user features, but it significantly improves maintainability and prepares PRISM for future extension-system work.

Added

* debug_mode support in config and runtime state
* global --debug-mode / --no-debug-mode flag
* PrismApp class for app-level command handling
* FileSystemService class for filesystem operations, classification, skip logic, and path handling
* debug output for classification, target path resolution, undo log selection, missing moved files, and restore-target resolution

Changed

* moved config command handling out of main() and into PrismApp
* reorganized file operations into a dedicated service layer instead of leaving them spread across top-level functions
* centralized classify / skip / move / undo helper behavior into cleaner internal routing
* cleaned up organize and undo flow structure to be easier to reason about and extend later
* improved internal separation between app control flow, config logic, filesystem behavior, and CLI parsing

## PRISM [v1.2.3p] (4/17/26)

PRISM v1.2.3p expands the config system into a full profile workflow. It adds named profile selection, runtime config saving, profile listing, profile deletion, and improved CLI guidance.

Added

* global `-c` / `--config` option for selecting configuration profiles
* `config --save` for saving current runtime settings into the selected profile
* `config --list` for listing available configuration profiles
* `config --delete` for removing the selected configuration profile
* shared runtime-setting support in `config` for saving values like `--dry-run`, `--exclude-str`, and `--sort-hidden`

Changed

* config loading now resolves against the selected profile instead of only `default.json`
* config command help and examples now reflect profile-based usage more clearly
* documentation flow now better matches the profile-based config system
* config profiles now support a more complete lifecycle from creation to deletion

## PRISM [v1.2.2p] (4/15/26)

PRISM v1.2.2p expands the config command into a more complete navigation and inspection layer. It adds direct ways to create, locate, inspect, summarize, and reset the active config, while also improving overall CLI usability.

Added

* `config --status` for a organized config summary
* `config --show` for raw JSON display of the currently loaded config
* `config --reset` for resetting the default config file to defaults
* top-level `--version` flag

Changed

* expanded config command guidance with clearer example usage
* improved config UX by separating organized status from raw JSON display
* continued CLI polish for the config workflow

## PRISM [v1.2.1p] (4/15/26)

PRISM v1.2.1p is a small follow-up usability release after the v1.2.0p config-system update. It focuses on making the CLI less awkward to use when launched directly and adds a more navigable entry point for basic config actions.

Added

- pause-before-exit behavior when launched directly without a command, to avoid appearing to immediately close or crash
- `config --create` support for creating the default config file
- `config --path` support for showing the config file path and whether the file exists

Changed

- improved no-command output by showing clearer example commands
- improved config command output when no config action is provided

  
## PRISM [1.2.0p] (4/14/26)
  
PRISM v1.2.0p was the first real config-system release, so far the biggest architectural update, and so far the hardest to implement as of now. It introduced DefaultConfig and RuntimeConfig, added support for loading persistent config from `~/.prism_config/default.json`, added a config command to initialize the default config file, and changed organize, undo, and logging behavior to run through a runtime config layer instead of only hardcoded defaults and CLI flags. It also updated file-type routing and log directory handling so they could be driven by runtime config, which moved PRISM from being a CLI-only tool into a config-aware system.

Added
- persistent config support via `~/.prism_config/default.json`
- runtime config loading with CLI override behavior

Changed
- refactored organize, undo, and logging paths to use runtime config
- reworked internal value flow to support future extensibility
  
## PRISM [v1.1.1p] (4/13/26)  

PRISM v1.1.1p was a refinement and flexibility release on top of v1.1.0p. It added `--exclude-str` support for skipping matching entries during both organize and undo, changed organize and undo to take the parsed args object directly, and improved output so moves displayed the full target path rather than only the root folder plus filename. The overall command structure stayed the same, but the behavior became cleaner and more configurable.
  
Added
- `--exclude-str` support for skipping matching entries during organize and undo
  
Changed  
- passed the parsed `args` object into top-level command functions from `main()`  
- improved move output so destination paths show the full target path
  
## PRISM [v1.1.0p] (4/11/26)  

PRISM v1.1.0p was the first major usability and safety expansion. It introduced a real CLI with `organize`, `undo`, and `list-logs`, added JSON move logs in `.prism_logs,` added undo support for the most recent run or a specific log file, added `--sort-hidden`, and started tracking moved, skipped, and errored files during organize runs. This is the version where PRISM became a real command tool instead of just a sorter script.  
  
Added  
- JSON run logs in `.prism_logs`  
- undo support for recent organize runs  
- added CLI with `organize`, `undo`, and `list-logs` commands
- `--log-file` support for targeted undo
- `--sort-hidden` support

Changed  
- expanded v1.0.0p organize mode to track moved, skipped, and errored files
  
## PRISM [v1.0.0p] (4/10/26)  

PRISM v1.0.0p was the initial structured organizer release. It could collect top-level files, sort them by extension into category folders, avoid overwriting duplicates by generating numbered filenames, and preview actions with a basic dry-run mode. At this stage, it was still a relatively simple organizer script with no command-based CLI, no hidden-file handling, no logging, and no undo support yet.  
  
Added  
- top-level file collection and category-based sorting  
- duplicate-safe renaming for filename collisions  
- dry-run preview support  
- the core PRISM organize flow  
