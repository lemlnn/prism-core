#made by lemlnn
EXTENSION_NAME = "expanded_file_types-v1.2"
EXTENSION_PRIORITY = 10

EXTENSION_CATEGORIES = {
    # Image / design
    ".tif": "Images",
    ".ai": "Design",
    ".svg": "Design",
    ".psd": "Design",

    # Documents
    ".rtf": "Documents",
    ".docm": "Documents",
    ".dot": "Documents",
    ".dotm": "Documents",
    ".dotx": "Documents",
    ".wbk": "Documents",
    ".asd": "Documents",
    ".svd": "Documents",
    ".wll": "Documents",

    # Spreadsheets
    ".xls": "Spreadsheets",
    ".xlsx": "Spreadsheets",
    ".xltx": "Spreadsheets",
    ".xltm": "Spreadsheets",
    ".xlsb": "Spreadsheets",
    ".xlsm": "Spreadsheets",
    ".xlam": "Spreadsheets",
    ".xlb": "Spreadsheets",
    ".xla": "Spreadsheets",
    ".xlt": "Spreadsheets",
    ".xar": "Spreadsheets",
    ".xlm": "Spreadsheets",
    ".xl": "Spreadsheets",
    ".xlw": "Spreadsheets",
    ".xll": "Spreadsheets",
    ".xlc": "Spreadsheets",
    ".ods": "Spreadsheets",

    # Presentations
    ".pptm": "Presentations",
    ".pps": "Presentations",
    ".ppsx": "Presentations",
    ".ppsm": "Presentations",
    ".sldx": "Presentations",
    ".sldm": "Presentations",
    ".pot": "Presentations",
    ".potx": "Presentations",
    ".potm": "Presentations",
    ".ppam": "Presentations",
    ".ppa": "Presentations",
    ".pa": "Presentations",

    # Office / database
    ".pub": "Office",
    ".accdb": "Office",

    # Video
    ".mpg": "Videos",
    ".mp2": "Videos",
    ".mpe": "Videos",
    ".mpv": "Videos",
    ".m4p": "Videos",
    ".m4v": "Videos",
    ".wmv": "Videos",
    ".qt": "Videos",
    ".flv": "Videos",
    ".swf": "Videos",
    ".avchd": "Videos",
    ".vob": "Videos",
    ".rm": "Videos",
    ".3gp": "Videos",
    ".3g2": "Videos",

    # Audio
    ".gsm": "Audio",
    ".dct": "Audio",
    ".au": "Audio",
    ".aiff": "Audio",
    ".vox": "Audio",
    ".wma": "Audio",
    ".aac": "Audio",
    ".atrac": "Audio",
    ".ra": "Audio",
    ".oma": "Audio",
    ".omg": "Audio",
    ".atp": "Audio",
    ".waptt": "Audio",
    ".i3pack": "Audio",
    ".3ga": "Audio",
    ".opus": "Audio",
    ".cda": "Audio",
    ".wpl": "Audio",
    ".rec": "Audio",
    ".vdjsample": "Audio",
    ".mus": "Audio",
    ".aax": "Audio",
    ".amr": "Audio",
    ".ds2": "Audio",
    ".sng": "Audio",
    ".dss": "Audio",
    ".nvf": "Audio",
    ".midi": "Audio",
    ".pcm": "Audio",
    ".mscz": "Audio",
    ".ses": "Audio",
    ".dvf": "Audio",
    ".gp5": "Audio",
    ".gp4": "Audio",
    ".bnk": "Audio",
    ".aup": "Audio",
    ".acd": "Audio",
    ".sf2": "Audio",
    ".thd": "Audio",
    ".sty": "Audio",
    ".mxl": "Audio",
    ".band": "Audio",
    ".cdfs": "Audio",
    ".ram": "Audio",
    ".aa": "Audio",
    ".eac3": "Audio",
    ".mogg": "Audio",
    ".seq": "Audio",
    ".uax": "Audio",
    ".mid": "Audio",
    ".kar": "Audio",
    ".dlp": "Audio",
    ".vce": "Audio",
    ".spx": "Audio",
    ".m4r": "Audio",
    ".wax": "Audio",

    # Code
    ".c": "Code",
    ".cpp": "Code",
    ".h": "Code",
    ".r": "Code",
    ".html": "Code",
    ".xhtml": "Code",
    ".css": "Code",
    ".class": "Code",
    ".php": "Code",
    ".swift": "Code",
    ".vb": "Code",

    # Applications
    ".apk": "Applications",
    ".appimage": "Applications",
    ".exe": "Applications",

    # Fonts
    ".fnt": "Fonts",
    ".fon": "Fonts",
    ".otf": "Fonts",
    ".ttf": "Fonts",
    ".woff": "Fonts",
    ".woff2": "Fonts",
    ".ofm": "Fonts",
    ".bmap": "Fonts",
    ".frf": "Fonts",
    ".afs": "Fonts",
}

EXTENSION_CATEGORIES = {
    ext.lower(): category
    for ext, category in EXTENSION_CATEGORIES.items()
}

CATEGORY_ALIASES = {}
CATEGORY_PREFIX = ""


def configure_extension(options):
    global CATEGORY_ALIASES
    global CATEGORY_PREFIX

    options = options or {}

    CATEGORY_PREFIX = str(options.get("category_prefix", "")).strip().strip("/")

    CATEGORY_ALIASES = {
        "Images": str(options.get("images_folder", "Images")),
        "Design": str(options.get("design_folder", "Design")),
        "Documents": str(options.get("documents_folder", "Documents")),
        "Spreadsheets": str(options.get("spreadsheets_folder", "Spreadsheets")),
        "Presentations": str(options.get("presentations_folder", "Presentations")),
        "Office": str(options.get("office_folder", "Office")),
        "Videos": str(options.get("videos_folder", "Videos")),
        "Audio": str(options.get("audio_folder", "Audio")),
        "Code": str(options.get("code_folder", "Code")),
        "Applications": str(options.get("applications_folder", "Applications")),
        "Fonts": str(options.get("fonts_folder", "Fonts")),
    }


def resolve_category_alias(category):
    category = CATEGORY_ALIASES.get(category, category)

    if CATEGORY_PREFIX:
        return f"{CATEGORY_PREFIX}/{category}"

    return category


def file_target_resolve(context):
    category = EXTENSION_CATEGORIES.get(context.extension.lower())

    if category is None:
        return None

    category = resolve_category_alias(category)

    return {
        "category": category,
        "reason": f"expanded file type match: {context.extension}",
    }
