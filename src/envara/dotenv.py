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
        with_platforms: bool = True,
        all_of: list[str] | None = None,
    ) -> list[Path]:
        """
        Get list of eligible files. Adds a list of platform names if
        with_platforms = True (default)

        :param dir: directory to look in
        :type dir: Path | None
        :param with_platforms: add platform names to filters
        :type with_platforms: bool, default: True
        :param all_of: list of filters with every to be matched in
            the filename; like runtime environment, language code, OS;
            wildcards are allowed:
            [',dev,\*test\*,prod\*', 'en,es,fr', 'linux,windows,darwin,bsd,*os']
        :type all_of: list[str] | None
        :rtype: list[Path]
        """

        # Adjust arguments

        dir = dir or pathlib.Path()

        # Add a regex for the default filename

        regexi: list[re.Pattern] = [
            DotEnv.__append_filter(regexi, "")
        ]

        # Add regexi for the passed filters

        if all_of:
            for f in all_of:
                if f:
                    DotEnv.__append_filter(regexi, f)

        # Add regexi for the platforms if required

        if (with_platforms):
            DotEnv.__append_filter(
                regexi,
                ",".join(Env.get_platform_stack(EnvPlatformStackFlags.NONE))
            )

        # Grab all files and filter those to the result list

        has_regexi: bool = len(regexi) > 0
        result: list[Path] = []

        for file in dir.iterdir():
            name: str = file.name

            if (not has_regexi) or all(r.search(name) for r in regexi):
                result.append(dir / name)

        # Finish

        return result

    ###########################################################################

    @staticmethod
    def load(
        path: Path | str | None = None,
        dir: Path | str | None = None,
        file_flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT,
        expand_flags: EnvExpandFlags = DEFAULT_EXPAND_FLAGS,
    ) -> str:
        """
        Load environment variables from a .env-compliant file

        :param path: a file to load from (optional)
        :type path: Path
        :param dir: default directory to locate platform-specific files
        :type dir: Path | str | None
        """

        content = DotEnv.read_text(path, file_flags, dir)
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
                expanded, _ = Env.expand(val, args, expand_flags)
                environ[key] = expanded
            elif key and key in environ:
                del environ[key]

        return data

    ###########################################################################

    @staticmethod
    def read_text(
        path: Path | str | None = None,
        file_flags: DotEnvFileFlags = DotEnvFileFlags.DEFAULT,
        default_dir: Path | str | None = None,
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
        :type default_dir: str | Path | None
        :param alt_ext: Alternative extension for the default files
        :type alt_ext: str
        """

        # Initialise suffix for the list of files

        ext_sep = os.extsep
        suffix = alt_ext or DotEnv.INDICATOR

        if suffix[0] != ext_sep:
            suffix = ext_sep + suffix

        # Resolve base directory where default/platform files are located

        if default_dir:
            base_dir = Path(default_dir) if not isinstance(default_dir, Path) else default_dir
        elif path and isinstance(path, Path) and path.is_absolute() and not path.is_dir():
            # if path is a file, use its parent as the base dir
            base_dir = path.absolute().parent
        else:
            base_dir = Path.cwd()

        # Initialise

        content = ""

        # If required, discard information about the files already loaded

        if file_flags & DotEnvFileFlags.RESET:
            DotEnv._loaded = []

        # Ask Env for the platform filenames (with prefix and suffix applied)
        platform_filenames = Env.get_platform_stack(
            EnvPlatformStackFlags.ADD_EMPTY, ".", suffix
        )

        # Load files for each platform filename
        for platform_filename in platform_filenames:
            file = base_dir / platform_filename
            file_str = str(file)

            # If the file of that path wasn't loaded yet, and the file
            # exists, load it

            if file_str not in DotEnv._loaded:
                try:
                    if file.exists():
                        content += f"{file.read_text()}\n"
                        DotEnv._loaded.append(file_str)
                except Exception:
                    # Be tolerant of mock Path objects in tests
                    try:
                        content += f"{file.read_text()}\n"
                        DotEnv._loaded.append(file_str)
                    except Exception:
                        # ignore unreadable files
                        pass

        # If a custom path was passed and it is a file, load it last
        if path and (not isinstance(path, Path) or not path.is_dir()):
            custom_path = path if isinstance(path, Path) else Path(path)
            custom_str = str(custom_path)
            if custom_str not in DotEnv._loaded:
                try:
                    if custom_path.exists():
                        content += f"{custom_path.read_text()}\n"
                        DotEnv._loaded.append(custom_str)
                except Exception:
                    try:
                        content += f"{custom_path.read_text()}\n"
                        DotEnv._loaded.append(custom_str)
                    except Exception:
                        pass

        # Return full content

        return content

    ###########################################################################

    @staticmethod
    def __append_filter(
        target: list[re.Pattern],
        source: str
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

        i: str = DotEnv.INDICATOR

        # If source filters are not present, add the default regex and finish

        if not source:
            target.append(re.compile(f"^\.{i}$"))
            return

        # Convert source to a regular expression pattern string replacing the
        # list item separator and wildcards into the regular expression
        # equivalents

        s: str = re.escape(source.replace(r"\\", r"\u0001"))\
            .replace(",", "|")\
            .replace(r"\?", ".")\
            .replace(r"\*", ".*")\
            .replace(r"\u0001", r"\\")

        # Compose the final pattern, compile that into a regular expression
        # and append to the target list

        target.append(re.compile(
            f"^\.{i}$|\.{i}(\.|\..+\.)({s})(\.|$)|\.({s})(\.|\..+\.){i}(\.|$)"
        ))

        return


###############################################################################
