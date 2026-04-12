# prism-core
A specialized file utility
by Lemuel Lin

**Current Features:**
  * Core:
    * extension-based file sorting
    * duplicate-safe renaming
    * optional hidden-file sorting
  * Safety:
    * Supports dry-run preview for organize and undo
    * Saves organize runs as JSON logs in .prism_logs
    * Undo for the most recent run or a specific log
    * Automatic cleanup/update of undo logs
  * CLI:
    * Command-based CLI interface via argparse with 3 commands and their respective flags
      * organize (`--dry-run`, `--sort-hidden`)
      * undo (`--dry-run`, `--log-file`)
      * list-logs
  * Error handling:
      * basic filesystem error handling during organize and undo tasks

**Planned Features:**  
  * TUI support using textual
  * flatten mode for moving files to prepare for the organize command
  * .exe and .pkg packages  

**Credits:**  
  * Special testers  
    * Windows 11 tester: Gavin ([@dojozycknar10-player](https://github.com))
