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
import platform
import re
from typing import Final

from dotenv_file_flags import DotEnvFileFlags
from env import Env
from env_expand_flags import EnvExpandFlags

###############################################################################
# Implementation
###############################################################################


class DotEnv:

    # Default set of string expansion flags
    DEFAULT_EXPAND_FLAGS: Final = \
        EnvExpandFlags.DECODE_ESCAPED | \
        EnvExpandFlags.REMOVE_LINE_COMMENT | \
        EnvExpandFlags.REMOVE_QUOTES | \
        EnvExpandFlags.SKIP_SINGLE_QUOTED

    # Default dit-env file type without leading extension separator
    DEFAULT_FILE_TYPE: Final = 'env'

    # Regex to split a string into key and value
    KEY_VALUE_RE: Final = re.compile(r'\s*=\s*')

    # Internal list of files that were loaded already
    _loaded: list[str] = []

    # Internal dictionary: regex => list-of-system-names
    _plat_map: dict[str, list[str]] = {
        '': ['', 'any'],
        '^aix': ['posix', 'aix'],
        'android': ['posix', 'linux', 'android'],
        '^atheos': ['posix', 'atheos'],
        'beos|haiku': ['posix', 'beos', 'haiku'],
        'bsd': ['posix', 'bsd'],
        'audioos|bridgeos|ios|ipados|macos|tvos|visionos|watchos': [
            'posix',
            'bsd',
            'darwin',
        ],
        '^(java|linux|cygwin|msys)': ['posix', 'linux'],
        '^riscos': ['riscos'],  # os.sep == ':'
        'solaris': ['posix', 'solaris'],
        'vms': ['vms'],
        '^win': ['windows'],
        '.*': ['*'],  # the actual system name, lowercased
    }

    ###########################################################################

    @staticmethod
    def load_from_file(
        path: Path,
        file_flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT,
        expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
        default_dir: str = None
    ) -> str:
        """
        Load environment variables from a .env-compliant file

        :param path: a file to load from
        :type path: Path
        """

        content = DotEnv.read_text(path, file_flags, default_dir)
        DotEnv.load_from_str(content, expand_flags)

    ###########################################################################

    @staticmethod
    def load_from_str(
        data: str,
        args: list[str] = None,
        expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS
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

        for line in data.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
            # Break into key and value and skip if can't

            key, val = DotEnv.KEY_VALUE_RE.split(line, maxsplit=1)

            # Expand the value and add to the dict of enviroment variables

            if val:
                environ[key] = Env.expand(val, args, expand_flags)
            elif key and key in environ:
                del environ[key]

    ###########################################################################

    @staticmethod
    def read_text(
        path: Path,
        file_flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT,
        default_dir: Path = None
    ) -> str:
        """
        Load environment variables from .env-compliant files: in the directory
        of the user-defined file or in the current one otherwise, it will first
        load .env, then any.env, then <platform>.env, then the fallback ones,
        then the one passed (if not None)

        :param path: a path to a custom file to load from
        :type path: Path
        """

        # Initialise
        # If required, discard information about the files already loaded

        content = ''

        if file_flags & DotEnvFileFlags.RESET:
            DotEnv._loaded = []

        # Set is_dir indicating the custom file is a directory,
        # and resolve an empty path

        if not path:
            path = Path.cwd()
            is_dir = True
        else:
            is_dir = path.is_dir()

        if (not (file_flags & DotEnvFileFlags.SKIP_DEFAULT_FILES)):
            # Get directory that should contain all files to read

            if (default_dir):
                dir = default_dir
            elif (is_dir):
                dir = path
            else:
                dir = path.parent

            # Get platform name to build the hierarchy of files to read

            plat_name = platform.system().lower()
            prefix = '' if (file_flags & DotEnvFileFlags.VISIBLE_FILES) else os.extsep

            # Try loading the file for the following platforms in the specified order if the
            # right side is empty, or represents a part of the current platform name

            x = DotEnv.DEFAULT_FILE_TYPE

            for key, plat_names in DotEnv._plat_map.items():
                # Break text into the base platform name, and the current platform's substring

                if key and (not re.search(key, plat_name, re.IGNORECASE | re.UNICODE)):
                    continue

                for item_plat_name in plat_names:
                    # If the platform name is a placeholder, take the running one

                    if item_plat_name == '*':
                        item_plat_name = plat_name

                    # Get path object and string to load the respective file

                    item_name = f'{item_plat_name}.{x}' if item_plat_name else x
                    item_path = dir / f'{prefix}{item_name}'
                    item_path_str = str(item_path)

                    # If the file of that path wasn't loaded yet, and the file
                    # exists, load it

                    if (item_path_str not in DotEnv._loaded) and item_path.exists():

                        content += f'{item_path.read_text()}\n'
                        DotEnv._loaded.append(item_path_str)

        # Finally, load the one passed by the user if it is an existing
        # file that was not loaded yet

        if (not is_dir) and path and path.exists():
            item_path_str = str(path)

            if item_path_str not in DotEnv._loaded:
                content += f'{path.read_text()}\n'
                DotEnv._loaded.append(item_path_str)

        # Return full content

        return content


###############################################################################
