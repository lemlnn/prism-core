# Changelog

**PRISM v1.1.1p (4/13/26)**  
  
Added
- `--exclude-str` support for skipping matching entries during organize and undo
  
Changed  
- passed the parsed `args` object into top-level command functions from `main()`  
- improved move output so destination paths show the full target path
  
**PRISM v1.1.0p (4/11/26)**  
  
Added  
- JSON run logs in `.prism_logs`  
- undo support for recent organize runs  
- added CLI with `organize`, `undo`, and `list-logs` commands
- expanded v1.0.0p organize mode to track moved, skipped, and errored files
- `--log-file` support for targeted undo
- `--sort-hidden` support
  
**PRISM v1.0.0p (4/10/26)**  
  
Added  
- top-level file collection and category-based sorting  
- duplicate-safe renaming for filename collisions  
- dry-run preview support  
- the core PRISM organize flow  
