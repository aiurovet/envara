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
import re
from typing import Final

from dotenv_file_flags import DotEnvFileFlags
from env import Env
from env_expand_flags import EnvExpandFlags
from env_platform_stack_flags import EnvPlatformStackFlags

###############################################################################
# Implementation
###############################################################################


class DotEnv:

    # Default set of string expansion flags
    DEFAULT_EXPAND_FLAGS: Final[EnvExpandFlags] = (
        EnvExpandFlags.UNESCAPE
        | EnvExpandFlags.REMOVE_LINE_COMMENT
        | EnvExpandFlags.REMOVE_QUOTES
        | EnvExpandFlags.SKIP_SINGLE_QUOTED
    )

    # Default dit-env file type without leading extension separator
    DEFAULT_EXT: Final[str] = "env"

    # Regex to split a string into key and value
    RE_KEY_VALUE: Final[re.Pattern] = re.compile(r"\s*=\s*")

    # Internal list of files that were loaded already
    _loaded: list[str] = []

    ###########################################################################

    @staticmethod
    def load_from_file(
        path: Path,
        file_flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT,
        expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
        default_dir: str | None = None,
    ) -> str:
        """
        Load environment variables from a .env-compliant file

        :param path: a file to load from
        :type path: Path
        """

        default_dir_path = Path(default_dir) if default_dir else None
        content = DotEnv.read_text(path, file_flags, default_dir_path)
        DotEnv.load_from_str(content, expand_flags=expand_flags)

        return content

    ###########################################################################

    @staticmethod
    def load_from_str(
        data: str | None,
        args: list[str] | None = None,
        expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
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
                environ[key] = Env.expand(val, args, expand_flags)
            elif key and key in environ:
                del environ[key]

        return data

    ###########################################################################

    @staticmethod
    def read_text(
        path: Path | None,
        file_flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT,
        default_dir: Path | None = None,
        alt_ext: str | None = None,
    ) -> str:
        """
        Load environment variables from .env-compliant files taken either from
        the directory of the custom file (path) or from default_dir if passed,
        or from the current directory. The files to load are defined as the
        maximum platform stack, as well as the custom one.

        :param path: a path to a custom file to load from after the default
                     files were loaded (unless the latter was turned off)
        :type path: Path
        :param file_flags: Describes what and how to load
        :type file_flags: DotEnvFileFlags
        :param default_dir: Default directory for the default files
        :type default_dir: str
        :param alt_ext: Alternative extension for the default files
        :type alt_ext: str
        """

        # Initialise suffix for the list of files

        ext_sep = os.extsep
        suffix = alt_ext or DotEnv.DEFAULT_EXT

        if suffix[0] != ext_sep:
            suffix = ext_sep + suffix

        # Ensure we have Path objects

        if path and not isinstance(path, Path):
            path = Path(path)

        if default_dir and not isinstance(default_dir, Path):
            default_dir = Path(default_dir)

        # Initialise

        content = ""
        dir = None
        is_dir = False

        # If required, discard information about the files already loaded

        if file_flags & DotEnvFileFlags.RESET:
            DotEnv._loaded = []

        # Set is_dir indicating the custom file is a directory, resolve path
        # in several cases and append the custom path if it is not directory

        if path:
            is_dir = path.is_dir()
            if not path.is_absolute() and default_dir:
                path = default_dir / path
        else:
            path = default_dir or Path.cwd()
            is_dir = True

        # Make custom path absolute to ensure it won't change, then add to
        # the list of files to load

        path = path.absolute()

        # Get directory that should contain all default files to read

        if default_dir:
            dir = default_dir
        elif is_dir:
            dir = path
        else:
            dir = path.parent

        # Get platform hierarchy as a list of dot-env files if needed

        if file_flags & DotEnvFileFlags.SKIP_DEFAULT_FILES:
            item_names = []
        else:
            if (file_flags & DotEnvFileFlags.VISIBLE_FILES):
                prefix = ""
            else:
                prefix = ext_sep

            item_names = Env.get_platform_stack(
                EnvPlatformStackFlags.ADD_MAX,
                prefix,
                suffix,
            )

        # Add custom path if passed

        if not is_dir:
            item_names.append(str(path))

        for item_name in item_names:
            # Get path object and string to load the respective file

            item_path = dir / item_name
            item_path_str = str(item_path)

            # If the file of that path wasn't loaded yet, and the file
            # exists, load it

            if (item_path_str not in DotEnv._loaded) and item_path.exists():
                content += f"{item_path.read_text()}\n"
                DotEnv._loaded.append(item_path_str)

        # Return full content

        return content


###############################################################################
