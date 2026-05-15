# Contributing to PRISM

Thanks for helping with PRISM. The project is still moving quickly, especially around the extension system, config behavior, and future TUI work.

## Good First Areas

Good first contributions usually stay close to documentation, examples, or safe category coverage:

- documentation fixes
- README wording
- user guide examples
- extension guide examples
- example extensions
- file type category suggestions
- small bug reports
- testing on Windows/Linux/macOS
- verifying CLI help output against the docs

## Medium Areas

These are useful, but they need more care because they touch real behavior:

- config status wording
- extension status/list output
- additional extension examples
- new default file categories
- safer error messages
- test folders for dry-run/undo behavior
- small refactors that do not change behavior

## Harder Areas

These should usually be discussed before work starts:

- extension hook design
- config/runtime behavior
- per-extension option behavior
- organize/undo safety
- packaging changes
- planner/TUI pipeline design
- anything that changes how moved files are logged or restored

## Please Ask Before Changing

Please ask before changing:

- file movement logic
- undo/log behavior
- extension API contracts
- extension context models
- extension return formats
- config format
- `disabled_extensions`
- `extension_options`
- path validation rules
- duplicate-safe naming rules

These areas are part of PRISM’s safety boundary. Breaking them can make organize/undo less reliable.

## Extension Contributions

Extensions should stay suggestion-based. PRISM core owns validation, file movement, duplicate-safe naming, logs, and undo.

A normal extension can suggest:

- whether a file should be processed through `file_should_process`
- where a file should go through `file_target_resolve`

Extensions should not directly move files, delete files, write organize logs, or bypass path validation.

## Extension Options

As of `v1.3.0-devt4c`, PRISM can store per-extension options in config.

Options are passed to loaded extensions through:

```python
PRISM_EXTENSION_OPTIONS
```

Extensions may also define:

```python
def configure_extension(options):
    ...
```

Existing extensions do not need to use options, but option-aware extensions should document the keys they support.

## Style Notes

PRISM currently uses:

- `UPPER_SNAKE_CASE` for constants
- `snake_case` for variables and functions
- `PascalCase` for classes
- small service classes for grouped behavior
- explicit config/runtime objects instead of hidden global behavior

Keep changes readable. PRISM is still beginner-friendly enough that contributors should be able to follow the code without digging through too much magic.

## Testing Suggestions

Before opening a PR or merging a change, try:

```bash
prism --version
prism config --status
prism organize --dry-run
prism extension --status
```

For extension changes, also try:

```bash
prism --enable-extensions extension --list
prism --enable-extensions organize --dry-run
```

For undo/log changes, test with disposable files only.
