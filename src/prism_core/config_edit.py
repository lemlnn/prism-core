import json
from pathlib import Path
from typing import Any

from .config_store import serialize_config, serialize_default_config
from .defaults import RuntimeConfig

#region config-edit-models

CONFIG_EDITABLE_KEYS = {
    "debug_mode",
    "script_name",
    "log_dir_name",
    "folder_path",
    "config_dir_path",
    "enable_extensions",
    "extensions_dir_path",
    "dry_run",
    "sort_hidden",
    "delete_empty_folders",
    "exclude_str",
    "default_file_types",
    "disabled_extensions",
    "extension_options",
}

BOOLEAN_KEYS = {
    "debug_mode",
    "enable_extensions",
    "dry_run",
    "sort_hidden",
    "delete_empty_folders",
}

PATH_KEYS = {
    "folder_path",
    "config_dir_path",
    "extensions_dir_path",
}

LIST_STRING_KEYS = {
    "disabled_extensions",
}

DICT_KEYS = {
    "default_file_types",
    "extension_options",
}

#endregion

#region value-parsing

def parse_config_assignment(text: str) -> tuple[str, Any]: #parses KEY=VALUE config edit syntax
    if "=" not in text:
        raise ValueError("Config assignments must use KEY=VALUE syntax.")

    key, value_text = text.split("=", 1)
    key = key.strip()

    if not key:
        raise ValueError("Config key cannot be empty.")

    if key not in CONFIG_EDITABLE_KEYS:
        raise ValueError(f"Unsupported config key: {key}")

    return key, coerce_config_value(key, value_text.strip())


def parse_extension_option_assignment(text: str) -> tuple[str, Any]: #parses KEY=VALUE extension option syntax
    if "=" not in text:
        raise ValueError("Extension option assignments must use KEY=VALUE syntax.")

    key, value_text = text.split("=", 1)
    key = key.strip()

    if not key:
        raise ValueError("Extension option key cannot be empty.")

    return key, parse_scalar_or_json(value_text.strip())


def coerce_config_value(key: str, value_text: str) -> Any: #coerces a config value based on the known config field
    if key in BOOLEAN_KEYS:
        return parse_bool(value_text)

    if key in PATH_KEYS:
        return str(Path(value_text).expanduser())

    if key == "exclude_str":
        if value_text.lower() in {"none", "null"}:
            return None
        return value_text

    if key in LIST_STRING_KEYS:
        value = parse_scalar_or_json(value_text)
        if isinstance(value, str):
            value = [item.strip() for item in value.split(",") if item.strip()]
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"{key} must be a string list or a comma-separated string.")
        return value

    if key in DICT_KEYS:
        value = parse_scalar_or_json(value_text)
        if not isinstance(value, dict):
            raise ValueError(f"{key} must be a JSON object/dict.")
        return value

    return parse_scalar_or_json(value_text)


def parse_bool(value_text: str) -> bool: #parses common boolean spellings
    lowered = value_text.strip().lower()

    if lowered in {"true", "1", "yes", "y", "on", "enable", "enabled"}:
        return True
    if lowered in {"false", "0", "no", "n", "off", "disable", "disabled"}:
        return False

    raise ValueError(f"Expected a boolean value, got: {value_text}")


def parse_scalar_or_json(value_text: str) -> Any: #parses JSON when possible, otherwise returns a string
    if value_text == "":
        return ""

    lowered = value_text.lower()
    if lowered in {"none", "null"}:
        return None
    if lowered in {"true", "false"}:
        return lowered == "true"

    try:
        return json.loads(value_text)
    except json.JSONDecodeError:
        return value_text

#endregion

#region config-data-editing

def build_config_data(runtime_config: RuntimeConfig) -> dict[str, Any]: #starts edits from the resolved runtime config
    return serialize_config(runtime_config)


def apply_config_sets(config_data: dict[str, Any], assignments: list[str]) -> list[str]: #applies config KEY=VALUE edits
    changed = []

    for assignment in assignments:
        key, value = parse_config_assignment(assignment)
        config_data[key] = value
        changed.append(key)

    return changed


def apply_config_unsets(config_data: dict[str, Any], keys: list[str]) -> list[str]: #resets config keys back to default values
    defaults = serialize_default_config()
    changed = []

    for key in keys:
        key = key.strip()
        if not key:
            raise ValueError("Config key cannot be empty.")
        if key not in CONFIG_EDITABLE_KEYS:
            raise ValueError(f"Unsupported config key: {key}")

        if key in defaults:
            config_data[key] = defaults[key]
        else:
            config_data.pop(key, None)
        changed.append(key)

    return changed


def ensure_extension_collections(config_data: dict[str, Any]) -> None: #ensures extension-related config fields are valid containers
    disabled = config_data.get("disabled_extensions")
    options = config_data.get("extension_options")

    if not isinstance(disabled, list):
        config_data["disabled_extensions"] = []
    if not isinstance(options, dict):
        config_data["extension_options"] = {}


def disable_extension(config_data: dict[str, Any], extension_name: str) -> bool: #adds an extension to the disabled list
    ensure_extension_collections(config_data)
    disabled_extensions = config_data["disabled_extensions"]
    normalized = extension_name.strip()

    if not normalized:
        raise ValueError("Extension name cannot be empty.")

    if normalized not in disabled_extensions:
        disabled_extensions.append(normalized)
        disabled_extensions.sort(key=str.lower)
        return True

    return False


def enable_extension(config_data: dict[str, Any], extension_name: str) -> bool: #removes an extension from the disabled list
    ensure_extension_collections(config_data)
    disabled_extensions = config_data["disabled_extensions"]
    normalized = extension_name.strip()

    if not normalized:
        raise ValueError("Extension name cannot be empty.")

    before = len(disabled_extensions)
    config_data["disabled_extensions"] = [
        item for item in disabled_extensions
        if item.lower() != normalized.lower()
    ]

    return len(config_data["disabled_extensions"]) != before


def set_extension_option(config_data: dict[str, Any], extension_name: str, assignment: str) -> tuple[str, Any]: #sets one per-extension option
    ensure_extension_collections(config_data)
    normalized = extension_name.strip()

    if not normalized:
        raise ValueError("Extension name cannot be empty.")

    key, value = parse_extension_option_assignment(assignment)
    extension_options = config_data["extension_options"].setdefault(normalized, {})

    if not isinstance(extension_options, dict):
        extension_options = {}
        config_data["extension_options"][normalized] = extension_options

    extension_options[key] = value
    return key, value


def unset_extension_option(config_data: dict[str, Any], extension_name: str, option_key: str) -> bool: #removes one per-extension option
    ensure_extension_collections(config_data)
    normalized = extension_name.strip()
    option_key = option_key.strip()

    if not normalized:
        raise ValueError("Extension name cannot be empty.")
    if not option_key:
        raise ValueError("Extension option key cannot be empty.")

    extension_options = config_data["extension_options"].get(normalized)

    if not isinstance(extension_options, dict):
        return False

    removed = option_key in extension_options
    extension_options.pop(option_key, None)

    if not extension_options:
        config_data["extension_options"].pop(normalized, None)

    return removed


def write_config_data(config_path: Path, config_data: dict[str, Any]) -> None: #writes edited raw config data to disk
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as json_output:
        json.dump(config_data, json_output, indent=4)

#endregion
