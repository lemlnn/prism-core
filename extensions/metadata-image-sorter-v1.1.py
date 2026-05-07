#made by lemlnn
EXTENSION_NAME = "metadata-image-sorter-v1.1"
EXTENSION_PRIORITY = 80

import json
import os
import shutil
import subprocess
from datetime import datetime
from functools import lru_cache
from pathlib import Path

try:
    from PIL import Image, ExifTags, UnidentifiedImageError
except Exception:
    Image = None
    ExifTags = None
    UnidentifiedImageError = OSError

PHOTO_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".heic"
}

RAW_EXTENSIONS = {
    ".arw", ".raw", ".dng", ".cr2", ".cr3", ".nef", ".raf", ".rw2"
}

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"
}

EXIF_DATE_KEYS = (
    "DateTimeOriginal",
    "DateTimeDigitized",
    "DateTime",
)

PNG_DATE_KEYS = (
    "Creation Time",
    "date:create",
    "date:modify",
    "creation_time",
    "created",
    "modified",
    "timestamp",
)

EXIFTOOL_DATE_KEYS = (
    "DateTimeOriginal",
    "SubSecDateTimeOriginal",
    "CreateDate",
    "SubSecCreateDate",
    "MediaCreateDate",
    "TrackCreateDate",
    "CreationDate",
)

EXIFTOOL_FALLBACK_DATE_HINTS = (
    "datetimeoriginal",
    "createdate",
    "creationdate",
    "mediacreatedate",
    "trackcreatedate",
    "contentcreatedate",
    "datecreated",
    "profiledatetime",
)

KNOWN_DATE_FORMATS = (
    "%Y:%m:%d %H:%M:%S",
    "%Y:%m:%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%a %b %d %H:%M:%S %Y",
)

DATE_KEYWORDS = (
    "date",
    "time",
    "created",
    "modified",
)

EXIFTOOL_TIMEOUT_SECONDS = 10
EXIFTOOL_PATH = shutil.which("exiftool")

def file_target_resolve(context):
    ext = context.extension.lower()

    if ext not in PHOTO_EXTENSIONS and ext not in RAW_EXTENSIONS and ext not in VIDEO_EXTENSIONS:
        return None

    best_date, source = get_best_media_datetime(context.source_path)

    year = best_date.strftime("%Y")
    month = best_date.strftime("%m")

    if ext in VIDEO_EXTENSIONS:
        category = f"Videos/{year}/{month}"
    elif ext in RAW_EXTENSIONS:
        category = f"Images/RAW/{year}/{month}"
    else:
        category = f"Images/{year}/{month}"
    return {
        "category": category,
        "reason": f"media date from {source}: {year}-{month}",
    }

def get_best_media_datetime(path):
    ext = path.suffix.lower()

    if ext in RAW_EXTENSIONS:
        exiftool_dt = get_exiftool_datetime(path)
        if exiftool_dt is not None:
            return exiftool_dt, "metadata-exiftool"

    if ext in PHOTO_EXTENSIONS:
        pillow_dt = get_pillow_metadata_datetime(path)
        if pillow_dt is not None:
            return pillow_dt, "metadata-pillow"

    if ext not in RAW_EXTENSIONS:
        exiftool_dt = get_exiftool_datetime(path)
        if exiftool_dt is not None:
            return exiftool_dt, "metadata-exiftool"

    created_dt = get_created_datetime(path)
    if created_dt is not None:
        return created_dt, "created"

    modified_dt = get_modified_datetime(path)
    if modified_dt is not None:
        return modified_dt, "modified"

    return datetime.now(), "current-time"

@lru_cache(maxsize=4096)
def parse_date_text_cached(text):
    if text.endswith(" UTC"):
        text = text[:-4] + "+00:00"
    for date_format in KNOWN_DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None

def parse_date_text(value):
    if value is None:
        return None
    if isinstance(value, bytes):
        decoded_value = None

        for encoding in ("utf-8", "latin-1"):
            try:
                decoded_value = value.decode(encoding, errors="ignore")
                break
            except Exception:
                continue

        value = decoded_value if decoded_value is not None else ""

    text = str(value).strip().replace("\x00", "")

    if not text:
        return None

    return parse_date_text_cached(text)

def get_pillow_metadata_datetime(path):
    if Image is None:
        return None
    try:
        with Image.open(path) as image:
            exif_map = {}
            try:
                raw_exif = image.getexif()

                if raw_exif and ExifTags is not None:
                    exif_map = {
                        ExifTags.TAGS.get(tag_id, tag_id): value
                        for tag_id, value in raw_exif.items()
                    }
            except Exception:
                exif_map = {}
            for key in EXIF_DATE_KEYS:
                parsed = parse_date_text(exif_map.get(key))

                if parsed is not None:
                    return parsed
            info = getattr(image, "info", {}) or {}
            for key in PNG_DATE_KEYS:
                parsed = parse_date_text(info.get(key))

                if parsed is not None:
                    return parsed
            for key, value in info.items():
                lowered = str(key).lower()

                if any(token in lowered for token in DATE_KEYWORDS):
                    parsed = parse_date_text(value)

                    if parsed is not None:
                        return parsed

    except (UnidentifiedImageError, OSError, ValueError):
        return None

    return None

def get_exiftool_datetime(path):
    if EXIFTOOL_PATH is None:
        return None

    command = [
        EXIFTOOL_PATH,
        "-j",
        "-m",
        "-q",
        "-api",
        "QuickTimeUTC=1",
    ]

    for key in EXIFTOOL_DATE_KEYS:
        command.append(f"-{key}")

    command.append(str(path))

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=EXIFTOOL_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return None
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, list) or not payload:
        return None

    item = payload[0]

    if not isinstance(item, dict):
        return None

    return parse_exiftool_item_datetime(item)

def parse_exiftool_item_datetime(item):
    for key in EXIFTOOL_DATE_KEYS:
        parsed = parse_date_text(item.get(key))

        if parsed is not None:
            return parsed
    for key, value in item.items():
        if key == "SourceFile":
            continue

        lowered = str(key).lower()

        if any(hint in lowered for hint in EXIFTOOL_FALLBACK_DATE_HINTS):
            parsed = parse_date_text(value)

            if parsed is not None:
                return parsed

    return None

def get_created_datetime(path):
    try:
        stat_result = path.stat()
    except OSError:
        return None

    if hasattr(stat_result, "st_birthtime"):
        try:
            return datetime.fromtimestamp(stat_result.st_birthtime)
        except (OSError, OverflowError, ValueError):
            return None
    if os.name == "nt":
        try:
            return datetime.fromtimestamp(stat_result.st_ctime)
        except (OSError, OverflowError, ValueError):
            return None

    return None

def get_modified_datetime(path):
    try:
        stat_result = path.stat()
    except OSError:
        return None
    try:
        return datetime.fromtimestamp(stat_result.st_mtime)
    except (OSError, OverflowError, ValueError):
        return None