# prism-core

A safe folder cleanup tool that sorts files, previews changes, and lets you undo mistakes.

[Changelog](./CHANGELOG.md) -
[User Guide](./docs/USER_GUIDE.md) -
[Extension Guide](./docs/EXTENSIONS.md) -
[Architecture Map](./docs/ARCHITECTURE_MAP.md)

PRISM helps clean messy folders by sorting files into categories like Images, Documents, Videos, and Archives. It can preview changes before moving anything, save logs of what happened, undo previous organize runs, and support experimental extensions for custom sorting behavior.

> `v1.3.0-devt2a` is a development build. The extension system is experimental and may change before the stable v1.3.x release.

## Features

- sorts files into category folders
- previews changes with dry-run mode
- avoids overwriting duplicate filenames
- saves JSON run logs
- can undo previous organize runs
- supports config profiles
- includes debug output for inspection
- supports experimental extension-based sorting

## Install

```bash
git clone https://github.com/lemlnn/prism-core.git
cd prism-core
python -m pip install .
```

After installation:

```bash
prism --version
```

## Quick Start

Create the default config profile:

```bash
prism config --create
```

Preview a cleanup:

```bash
prism organize --dry-run
```

Organize the current folder:

```bash
prism organize
```

Undo the most recent organize run:

```bash
prism undo
```

Undo and remove empty category folders:

```bash
prism undo --delete-empty-folders
```

Run with debug output:

```bash
prism --debug-mode organize
```

## Experimental Extensions

Extensions are disabled by default.

Enable extensions for one run:

```bash
prism --enable-extensions organize --dry-run
```

Create the default extensions directory:

```bash
prism extension --create
```

Show extension status:

```bash
prism extension --status
```

Use a custom extension folder:

```bash
prism --enable-extensions --extensions-dir ./extensions organize --dry-run
```

Inspect loaded extensions from a custom folder:

```bash
prism --enable-extensions --extensions-dir ./extensions extension --status
```

Current hooks:

- `file_should_process`
- `file_target_resolve`

Extensions can suggest behavior, but the core system still operates main functionality

## Tested Platforms

- Windows 10/11 (restricted, unrestricted)
- Fedora KDE 42/43

## Credits
Special thanks to my early contributors and testers

Development Team:

- Lemuel ([@lemlnn](https://github.com/lemlnn)) - Lead Developer
- Devin ([@DevinEats314](https://github.com/DevinEats314)) - Co-Developer & Outreach

Alpha Testers:

- Bella - beta macOS compatibility attempt
- Gavin ([@dojozycknar10-player](https://github.com/dojozycknar10-player)) - Windows 11 restricted environment compatibility
- Maxwell ([@b135-crypto](https://github.com/b135-crypto)) - planned Zorin OS and macOS compatibility

Early Contributors:

- Enoch ([@Wavefire5201](https://github.com/Wavefire5201))
- Gavin ([@dojozycknar10-player](https://github.com/dojozycknar10-player))
- Devin ([@DevinEats314](https://github.com/DevinEats314))

## License

Apache License 2.0. See the LICENSE file for details.
