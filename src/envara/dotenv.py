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

from dotenv_file_flags import DotEnvFileFlags
from dotenv_filter import DotEnvFilter
from env import Env
from env_exp_flags import EnvExpFlags
from env_platform_stack_flags import EnvPlatformStackFlags

###############################################################################
# Implementation
###############################################################################


class DotEnv:

    # Default set of string expansion flags
    DEFAULT_EXPAND_FLAGS: Final[EnvExpFlags] = (
        EnvExpFlags.UNESCAPE
        | EnvExpFlags.REMOVE_LINE_COMMENT
        | EnvExpFlags.REMOVE_QUOTES
        | EnvExpFlags.SKIP_SINGLE_QUOTED
    )

    # Default dot-env file type without leading extension separator
    INDICATOR: Final[str] = "env"

    # Regex to split a string into key and value
    RE_KEY_VALUE: Final[re.Pattern] = re.compile(r"\s*=\s*")

    # Internal list of files that were loaded already
    _loaded: list[str] = []

    ###########################################################################

    @staticmethod
    def get_files(
        dir: Path | None = None,
        flags: DotEnvFileFlags = DotEnvFileFlags.ADD_PLATFORMS,
        *filters: list[DotEnvFilter] | DotEnvFilter,
    ) -> list[Path]:
        """
        Get list of eligible files. Adds a list of platform names if
        `with_platforms = True` (default)

        :param dir: directory to look in
        :type dir: Path | None
        :param flags: add platform names to filters
        :type flags: DotEnvFileFlags, default: DotEnvFileFlags.ADD_PLATFORMS
        :param filters: one or more DotEnvFilter objects showing what is the
            current value, and what are the possibilities; should be matched
            against: `DotEnv.get_files(DotEnvFilter(cur='prod*', all=['dev',
            'test', 'prod', 'production']), DotEnvFilter(cur='jp', all=['en',
            'fr', 'de']))`
        :type filters: unlimited arguments of type DotEnvFilter
        :rtype: list[Path]
        """

        # Adjust arguments

        dir = dir or pathlib.Path()

        # Define extended filters as a growable list and append
        # the ones passed as separate arguments

        filters_ex: list[DotEnvFilter] = []

        for x in filters:
            if isinstance(x, list):
                filters_ex.extend(x)
            else:
                filters_ex.append(x)

        # Add the platform filter if required

        if flags & DotEnvFileFlags.ADD_PLATFORMS:
            for x in Env.get_platform_stack(EnvPlatformStackFlags.NONE):
                filters_ex.append(DotEnvFilter(x))

        # Ensure the default filter is added if no other filter exists

        filters_ex.append(DotEnvFilter())

        # Grab all files and filter those to the result list

        result: list[Path] = []

        for file in dir.iterdir():
            name: str = file.name

            # If none of the expected values match or one of the current
            # ones, then the filename is valid: '.env.jp' should match
            # any runtime environment: 'dev', 'test' and 'prod' as well as
            # '.env.jp', but neither of: '.env.de', '.env.en', '.env.fr'

            # `f.all` and `f.cur` store the original values; regex patterns
            # were compiled to `all_regex` and `cur_regex` in the filter
            # constructor.  The previous implementation accidentally used
            # the raw lists/strings which caused attribute errors.  Use the
            # regex attributes here.
            if all(f.is_match(name) for f in filters):
                result.append(dir / name)

        # Finish

        return result

    ###########################################################################

    @staticmethod
    def load(
        dir: Path | None = None,
        file_flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT,
        exp_flags: EnvExpFlags = DEFAULT_EXPAND_FLAGS,
        *filters: list[str] | str | None,
    ) -> str:
        """
        Load environment variables from a .env-compliant file(s)

        :param dir: default directory to locate platform-specific files
        :type dir: Path | str | None
        :param file_flags: Describes what and how to load
        :type file_flags: DotEnvFileFlags
        :param file_flags: Describes how to expand env vars and app args
        :type exp_flags: EnvExpandFlags
        """

        files: list[Path] = DotEnv.get_files(dir, file_flags, filters)
        content: str = DotEnv.read_text(files, file_flags, dir)

        DotEnv.load_from_str(content, exp_flags=exp_flags)

        return content

    ###########################################################################

    @staticmethod
    def load_from_str(
        data: str | None,
        args: list[str] | None = None,
        exp_flags: EnvExpFlags = DEFAULT_EXPAND_FLAGS,
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

            parts = DotEnv.RE_KEY_VALUE.split(line, maxsplit=1)
            if len(parts) < 2:
                continue

            key, val = parts

            # Expand the value and add to the dict of enviroment variables

            if val:
                expanded, _ = Env.expand(val, args, exp_flags)
                environ[key] = expanded
            elif key and key in environ:
                del environ[key]

    ###########################################################################

    @staticmethod
    def read_text(
        files: list[Path],
        flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT
    ) -> str:
        """
        Load the content of all files as text and return. May
        discard previously loaded content if the special flag
        is set

        :param files: list of Paths to read text from
        :type files: list[Path]
        :param flags: Describes what and how to load
        :type flags: DotEnvFileFlags
        """

        # Initialise the content

        result: list[str] = []

        # If required, discard information about the files already loaded

        if flags & DotEnvFileFlags.RESET:
            DotEnv._loaded = []

        # Accumulate the content

        for file in files:
            file_str = str(file)

            # If the file of that path was loaded aready, skip it

            if file_str in DotEnv._loaded:
                continue

            # Avoid multiple loads of the same file 

            DotEnv._loaded.append(file_str)

            # Read the file content ignoring any issue

            try:
                result.append(file.read_text())
            except Exception:
                pass

        # Return the content

        return "\n".join(result)


###############################################################################
