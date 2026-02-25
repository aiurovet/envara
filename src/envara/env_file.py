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

from env_file_flags import EnvFileFlags
from env_filter import EnvFilter
from env import Env
from env_expand_flags import EnvExpandFlags
from env_platform_flags import EnvPlatformFlags

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
        flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS,
        *filters: list[EnvFilter] | EnvFilter,
    ) -> list[Path]:
        """
        Get list of eligible files. Adds a list of platform names if
        `with_platforms = True` (default)

        :param dir: directory to look in
        :type dir: Path | None

        :param indicator: necessary part of every relevant filename
        :type indicator: str

        :param flags: add platform names to filters
        :type flags: EnvFileFlags, default: EnvFileFlags.ADD_PLATFORMS

        :param filters: one or more EnvFilter objects showing what is the
            current value, and what are the possibilities; should be matched
            against: `EnvFile.get_files(EnvFilter(cur_values='prod*',
            all_values=['dev', 'test', 'prod', 'production']), EnvFilter(
            cur_values='jp', all=['en', 'fr', 'de']))`
        :type filters: unlimited arguments of type EnvFilter

        :rtype: list[Path]
        """

        # Adjust arguments

        dir = dir or pathlib.Path()

        # Define extended filters as a growable list and append
        # the ones passed as separate arguments

        filters_ex: list[EnvFilter] = []

        for x in filters:
            if isinstance(x, list):
                filters_ex.extend(x)
            else:
                filters_ex.append(x)

        # Add the platform filter if required

        if flags & EnvFileFlags.ADD_PLATFORMS:
            filters_ex.append(
                EnvFilter(
                    indicator,
                    cur_values=Env.get_cur_platforms(flags=EnvPlatformFlags.NONE),
                    all_values=Env.get_all_platforms(flags=EnvPlatformFlags.NONE),
                )
            )

        # Fallback: append a minimal set of filters

        if len(filters_ex) <= 0:
            filters_ex.append(EnvFilter())

        # Grab all files and filter those to the result list

        result: list[Path] = []

        for file in dir.iterdir():
            name: str = file.name

            for x in filters_ex:
                if x.is_match(name):
                    result.append(dir / name)
                    break

        # Finish

        return result

    ###########################################################################

    @staticmethod
    def load(
        dir: Path | None = None,
        file_flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS,
        expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
        *filters: list[str] | str | None,
    ) -> str:
        """
        Load environment variables from a .env-compliant file(s)

        :param dir: default directory to locate platform-specific files
        :type dir: Path | str | None
        :param file_flags: Describes what and how to load
        :type file_flags: EnvFileFileFlags
        :param file_flags: Describes how to expand env vars and app args
        :type expand_flags: EnvExpandFlags
        """

        files: list[Path] = EnvFile.get_files(dir, file_flags, filters)
        content: str = EnvFile.read_text(files, file_flags, dir)

        EnvFile.load_from_str(content, expand_flags=expand_flags)

        return content

    ###########################################################################

    @staticmethod
    def load_from_str(
        data: str | None,
        args: list[str] | None = None,
        expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
    ):
        """
        Load environment variables from a string

        :param data: a string to parse, then load env variables from
        :type data: str
        :param args: a list of arguments (e.g. application args) to expand
                     placeholders like $1, ${2}, ...
        :type args: list[str]
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
                expanded, _ = Env.expand(val, args, expand_flags)
                environ[key] = expanded
            elif key and key in environ:
                del environ[key]

    ###########################################################################

    @staticmethod
    def read_text(
        files: list[Path], flags: EnvFileFlags = EnvFileFlags.ADD_PLATFORMS
    ) -> str:
        """
        Load the content of all files as text and return. May
        discard previously loaded content if the special flag
        is set

        :param files: list of Paths to read text from
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
