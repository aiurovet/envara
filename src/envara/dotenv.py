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
    def get_file_stack(
        dir: Path | None = None,
        flags: DotEnvFileFlags = DotEnvFileFlags.ADD_PLATFORMS,
        *all_of: list[str] | str | None,
    ) -> list[Path]:
        """
        Get list of eligible files. Adds a list of platform names if
        `with_platforms = True` (default)

        :param dir: directory to look in
        :type dir: Path | None
        :param with_platforms: add platform names to filters
        :type with_platforms: bool, default: True
        :param all_of: filters (lists of strings or strings) the filename
            should be matched against: `DotEnv.get_file_stack('prod*',
            'es', ['linux','windows','darwin','bsd','*os'])`
        :type all_of: unlimited arguments of type list[str] or str
        :rtype: list[Path]
        """

        # Adjust arguments

        dir = dir or pathlib.Path()

        # Add a regex for the default filename

        regexi: list[re.Pattern] = []

        # Add regexi for the passed filters

        for f in all_of:
            DotEnv.__append_filter(regexi, f)

        # Add regexi for the platforms if required

        if flags & DotEnvFileFlags.ADD_PLATFORMS:
            DotEnv.__append_filter(
                regexi,
                ",".join(Env.get_platform_stack(EnvPlatformStackFlags.NONE))
            )

        # Ensure the defualt filter is added

        if len(regexi) <= 0:
            DotEnv.__append_filter(regexi, None)

        # Grab all files and filter those to the result list

        result: list[Path] = []

        for file in dir.iterdir():
            name: str = file.name

            if all(r.search(name) for r in regexi):
                result.append(dir / name)

        # Finish

        return result

    ###########################################################################

    @staticmethod
    def load(
        dir: Path | None = None,
        file_flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT,
        exp_flags: EnvExpFlags = DEFAULT_EXPAND_FLAGS,
        *all_of: list[str] | str | None,
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

        files: list[Path] = DotEnv.get_file_stack(dir, file_flags, all_of)
        content: str = DotEnv.read_text(files, file_flags, dir)

        DotEnv.load_from_str(content, exp_flags=exp_flags)

        return content

    ###########################################################################

    @staticmethod
    def load_from_str(
        data: str | None,
        args: list[str] | None = None,
        exp_flags: EnvExpFlags = DEFAULT_EXPAND_FLAGS,
    ) -> str:
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

        return data

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

    ###########################################################################

    @staticmethod
    def __append_filter(
        target: list[re.Pattern],
        source: list[str] | str | None
    ):
        """
        Attach delimiters to source items, create patterns and append
        those to the target list
      
        :param target: destination list of regexi
        :type target: list[re.Pattern]
        :param source: comma-separated source filters with optional wildcards:
                       "linux,*os" or "en,es,fr" or "dev,*test*,prod*"
        :type source: str
        """

        # Making variable name shorter for better clarity

        i: str = f"({DotEnv.INDICATOR})"

        # Define a pattern for all allowed separators as well as default
        # filename pattern

        s: str = r"[\.\-_]"
        p: str = f"^{s}?{i}{s}?$"

        # If source filters are not present, add the default regex and finish

        if not source:
            target.append(re.compile(p))
            return

        # Define the derived pattern for all allowed separators between the
        # indicator and source or vice versa: a single separator pattern or
        # two separator patterns with something else inbetween

        m = f"({s}|{s}.+{s})"

        # Convert source to a regular expression pattern string replacing the
        # list item separator and wildcards with the regular expression
        # equivalents

        x: str = ",".join(source) if isinstance(source, list) else source

        x = "(" + re.escape(x.replace(r"\\", r"\u0001"))\
            .replace(",", "|")\
            .replace(r"\?", ".")\
            .replace(r"\*", ".*")\
            .replace(r"\u0001", r"\\") + ")"

        # Compose the final pattern, compile that into a regular expression
        # and append to the target list

        p = f"{p}|(^|{s}){i}{m}{x}({s}|$)|(^|{s}){x}{m}{i}({s}|$)"
        target.append(re.compile(p))

        return


###############################################################################
