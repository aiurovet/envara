###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# A class to read series of key=value lines from a text file, remove line
# comments, expand environment values and arguments, expand escaped characters
# and set or update those as environment variables
#
# It also allows hierarchical OS-specific stacking of such files, as for
# instance, locations and filenames of executables like Google Chrome are
# quite specific to Linux, macOS and Windows. As a result, it is possible
# confine OS-specific things to such files making the application portable
#
###############################################################################

import os
from pathlib import Path
import pathlib
import re
from typing import Final

from envara.env_file_flags import EnvFileFlags
from envara.env_filter import EnvFilter
from envara.env import Env
from envara.env_expand_flags import EnvExpandFlags
from envara.env_filters import EnvFilters
from envara.env_platform_flags import EnvPlatformFlags

###############################################################################
# Implementation
###############################################################################


class EnvFile:

    DEFAULT_EXPAND_FLAGS: Final[EnvExpandFlags] = (
        EnvExpandFlags.UNESCAPE
        | EnvExpandFlags.REMOVE_LINE_COMMENT
        | EnvExpandFlags.REMOVE_QUOTES
        | EnvExpandFlags.SKIP_SINGLE_QUOTED
    )
    """Default set of string expansion flags"""

    RE_KEY_VALUE: Final[re.Pattern] = re.compile(r"\s*=\s*")
    """Regex to split a string into key and value"""

    _loaded: list[str] = []
    """Internal list of files that were loaded already"""

    ###########################################################################

    @staticmethod
    def get_files(
        dir: Path | None = None,
        indicator: str | None = None,
        flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS_BEFORE,
        *filters: list[EnvFilter] | EnvFilter,
    ) -> list[Path]:
        """
        Get list of eligible files. Adds a list of platform names if
        `with_platforms = True` (default)

        :param dir: Directory to look in
        :type dir: Path | None

        :param indicator: Necessary part of every relevant filename
        :type indicator: str

        :param flags: Add platform names to filters
        :type flags: EnvFileFlags, default: EnvFileFlags.ADD_PLATFORMS

        :param filters: One or more EnvFilter objects showing what is the
            current value(s), and all possibilities; should be matched
            against: `EnvFile.get_files(EnvFilter(cur_values='prod*',
            all_values=['dev', 'test', 'prod', 'production']), EnvFilter(
            cur_values=['jp', 'en'], all='en,fr,de,jp'))`
        :type filters: unlimited arguments of type EnvFilter

        :return: List of matching paths in the given directory
        :rtype: list[Path]
        """

        # Adjust arguments

        dir = dir or pathlib.Path()

        # Define extended filters as a growable list that is initially empty

        filters_ex: list[EnvFilter] = []
        plat_flags = EnvPlatformFlags.NONE

        # Add the platforms filter before the other ones (if required)

        if flags & EnvFileFlags.ADD_PLATFORMS_BEFORE:
            filters_ex.append(
                EnvFilter(
                    indicator,
                    cur_values=Env.get_cur_platforms(plat_flags),
                    all_values=Env.get_all_platforms(plat_flags),
                )
            )

        # Append the filters passed as separate arguments

        for filter in filters:
            if isinstance(filter, list):
                filters_ex.extend(filter)
            elif filter:
                filters_ex.append(filter)

        # Add the platforms filter after the other ones (if required)

        if flags & EnvFileFlags.ADD_PLATFORMS_AFTER:
            filters_ex.append(
                EnvFilter(
                    indicator,
                    cur_values=Env.get_cur_platforms(plat_flags),
                    all_values=Env.get_all_platforms(plat_flags),
                )
            )

        # Fallback: append a minimal set of filters if no other filter
        # already added

        if len(filters_ex) <= 0:
            filters_ex.append(EnvFilter())

        # Grab filenames of all files in the given directory

        file_names: list[str] = [
            entry.name for entry in dir.iterdir() if entry.is_file()
        ]

        # Filter and sort filenames

        file_names = EnvFilters.process(file_names, filters_ex)

        # Return paths to the files filtered and sorted above

        return [dir / file_name for file_name in file_names]

    ###########################################################################

    @staticmethod
    def load(
        dir: Path | None = None,
        indicator: str = EnvFilter.DEFAULT_INDICATOR,
        file_flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS_BEFORE,
        args: list[str] | None = None,
        expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
        *filters: list[EnvFilter] | EnvFilter,
    ):
        """
        Add key-expanded-value pairs from .env-compliant file(s) to os.environ

        :param dir: Default directory to locate platform-specific files
        :type dir: Path | None

        :param indicator: Necessary part of every relevant filename,
            default: EnvFilter.DEFAULT_INDICATOR
        :type indicator: str

        :param file_flags: Describes what and how to load
        :type file_flags: EnvFileFlags

        :param args: List of arguments (e.g. application args) to expand
            placeholders like $1, ${2}, ...
        :type args: list[str]

        :param expand_flags: Describes how to expand env vars and app args
        :type expand_flags: EnvExpandFlags

        :param filters: One or more EnvFilter objects showing what is the
            current value(s), and all possibilities; should be matched
            against: `EnvFile.get_files(EnvFilter(cur_values='prod*',
            all_values=['dev', 'test', 'prod', 'production']), EnvFilter(
            cur_values=['jp', 'en'], all='en,fr,de,jp'))`
        :type filters: unlimited arguments of type EnvFilter

        """

        files: list[Path] = EnvFile.get_files(dir, indicator, file_flags, filters)
        content: str = EnvFile.read_text(files, file_flags)

        EnvFile.load_from_str(content, args=args, expand_flags=expand_flags)

    ###########################################################################

    @staticmethod
    def load_from_str(
        data: str | None,
        args: list[str] | None = None,
        expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
    ):
        """
        Add key-expanded-value pairs from a string buffer to os.environ

        :param data: String to parse, then load env variables from
        :type data: str

        :param args: List of arguments (e.g. application args) to expand
            placeholders like $1, ${2}, ...
        :type args: list[str]

        :param expand_flags: Describes how to expand env vars and app args
        :type expand_flags: EnvExpandFlags
        """

        # Split data into lines and loop through every line

        environ = os.environ

        for line in data.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            # Break into key and value and skip if can't

            parts = EnvFile.RE_KEY_VALUE.split(line, maxsplit=1)

            if len(parts) < 2:
                continue

            key, val = parts

            # Expand the value and add to the dict of enviroment variables

            if val:
                environ[key] = Env.expand(val, args=args, flags=expand_flags)
            elif key and key in environ:
                del environ[key]

    ###########################################################################

    @staticmethod
    def read_text(
        files: list[Path], flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS_BEFORE
    ) -> str:
        """
        Load the content of all files as text and return. May
        discard previously loaded content if the special flag
        is set

        :param files: List of Paths to read text from
        :type files: list[Path]

        :param flags: Describes what and how to load
        :type flags: EnvFileFlags
        """

        # Initialise the content

        result: list[str] = []

        # If required, discard information about the files already loaded

        if flags & EnvFileFlags.RESET_ACCUMULATED:
            EnvFile._loaded = []

        # Accumulate the content

        for file in files:
            file_str = str(file)

            # If the file of that path was loaded aready, skip it

            if file_str in EnvFile._loaded:
                continue

            # Avoid multiple loads of the same file

            EnvFile._loaded.append(file_str)

            # Read the file content ignoring any issue

            try:
                result.append(file.read_text())
            except Exception:
                pass

        # Return the content

        return "\n".join(result)


###############################################################################
