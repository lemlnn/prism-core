import argparse
import textwrap

from .defaults import default_config

#region args-functions

def parse_args() -> argparse.Namespace: #function to load all arguments for the script
    usage_info = "%(prog)s [options] {organize,undo,list-logs,inspect,extension,config} ..."

    example_usage = textwrap.dedent("""
        Commands:
          organize    Sort files into categorized folders
          undo        Revert the last organization run
          list-logs   Show history of previous runs
          inspect     View a summary of the last organize run
          config      Manage settings and custom profiles

        Examples:
          %(prog)s organize --dry-run
          %(prog)s --enable-extensions organize --dry-run
          %(prog)s --enable-extensions --extensions-dir ./extensions organize --dry-run
          %(prog)s -c my_profile config --save --dry-run --exclude-str "Draft"
          %(prog)s -c photography organize
          %(prog)s config --list
          %(prog)s config --set sort_hidden=true
          %(prog)s extension --disable pdf-classifier-APs-v1.0
          %(prog)s extension --set-option metadata-image-sorter-v1.2 prefer_created=true
          %(prog)s undo
    """)

    parser = argparse.ArgumentParser(
        description="PRISM: A smart file organizer that categorizes files by type.",
        usage=usage_info,
        epilog=example_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    global_group = parser.add_argument_group("Global Options")
    global_group.add_argument(
        "-c", "--config",
        metavar="NAME",
        dest="config_name",
        default="default",
        help="Use a specific configuration profile (default: 'default')"
    )
    global_group.add_argument(
        "--debug-mode",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable additional debug dialogues for actions"
    )
    global_group.add_argument(
        "--enable-extensions",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable extension framework"
    )
    global_group.add_argument(
        "--extensions-dir",
        metavar="PATH",
        dest="extensions_dir_path",
        type=str,
        default=None,
        help="Specify the extensions directory"
    )

    subparsers = parser.add_subparsers(dest="command", title="Available Commands", metavar="")
    shared_flags = argparse.ArgumentParser(add_help=False)

    shared_flags.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="Preview changes without moving any files"
    )
    shared_flags.add_argument(
        "--exclude-str",
        metavar="TEXT",
        type=str,
        default=None,
        help="Skip files containing this specific text"
    )

    organize_parser = subparsers.add_parser(
        "organize",
        parents=[shared_flags],
        help="Sort files into folders"
    )
    organize_parser.add_argument(
        "--sort-hidden",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include or exclude hidden files (starting with '.')"
    )

    undo_parser = subparsers.add_parser(
        "undo",
        parents=[shared_flags],
        help="Reverse a previous run"
    )
    undo_parser.add_argument(
        "--log-file",
        metavar="FILENAME",
        type=str,
        help="Specify a specific log to undo"
    )
    undo_parser.add_argument(
        "--delete-empty-folders",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Delete empty category folders after undo completes"
    )

    extension_parser = subparsers.add_parser(
        "extension",
        help="Manage and view extensions"
    )
    
    extension_actions = extension_parser.add_mutually_exclusive_group()
    extension_actions.add_argument("--status", action="store_true", help="Show current extension summary")
    extension_actions.add_argument("--list", action="store_true", help="List discovered extensions and enabled/disabled state")
    extension_actions.add_argument("--create", action="store_true", help="Create the extensions directory")
    extension_actions.add_argument("--enable", metavar="NAME", help="Enable an extension in the current config")
    extension_actions.add_argument("--disable", metavar="NAME", help="Disable an extension in the current config")
    extension_actions.add_argument("--set-option", nargs=2, metavar=("NAME", "KEY=VALUE"), help="Set a per-extension option in the current config")
    extension_actions.add_argument("--unset-option", nargs=2, metavar=("NAME", "KEY"), help="Remove a per-extension option from the current config")

    subparsers.add_parser(
        "list-logs",
        help="View organization history"
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="View a summary of an organize run"
    )

    inspect_parser.add_argument(
        "--log-file",
        metavar="FILENAME",
        type=str,
        default=None,
        help="Inspect a specific log file"
    )
    
    config_parser = subparsers.add_parser(
        "config",
        parents=[shared_flags],
        help="Manage configuration profiles"
    )
    config_parser.add_argument(
        "--sort-hidden",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Set whether hidden files are included"
    )
    config_parser.add_argument(
        "--delete-empty-folders",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Set whether undo deletes empty category folders after restoring files"
    )

    config_actions = config_parser.add_mutually_exclusive_group()
    config_actions.add_argument("--create", action="store_true", help="Initialize a new config file")
    config_actions.add_argument("--save", action="store_true", help="Save current settings to profile")
    config_actions.add_argument("--list", action="store_true", help="List all saved profiles")
    config_actions.add_argument("--status", action="store_true", help="Show current profile summary")
    config_actions.add_argument("--show", action="store_true", help="Print raw JSON configuration")
    config_actions.add_argument("--path", action="store_true", help="Show location of config file")
    config_actions.add_argument("--reset", action="store_true", help="Restore profile to defaults")
    config_actions.add_argument("--delete", action="store_true", help="Remove the current config profile")
    config_actions.add_argument("--set", dest="set_values", metavar="KEY=VALUE", nargs="+", help="Edit one or more config values and save them to the current profile")
    config_actions.add_argument("--unset", dest="unset_keys", metavar="KEY", nargs="+", help="Reset one or more config values back to default in the current profile")

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {default_config.script_version}"
    )

    return parser.parse_args()

#endregion
