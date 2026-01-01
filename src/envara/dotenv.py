###############################################################################
# svg2many (C) Alexander Iurovetski 2025
#
# A class to read series of key=value lines from a text file and set those
# as environment variables.
#
# Differs from the standard dotenv.load_dotenv by the ability to expand
# existing environment variables in the new values before these are added.
#
# This class also allows to avoid unnecessary dependency: easy to implement.
###############################################################################

from argparse import Namespace
import os
from pathlib import Path
import platform
import re

###############################################################################
# Implementation
###############################################################################

#
# Discover simple env var patterns
#
# (\$([A-Z][A-Z_0-9]*))|(\${([^{}]*)})
#
class DotEnv:
    DEF_FILE_TYPE: str = ".env"
    ESCAPING: str = "unicode_escape"

    COMMENTS_RE: re.Pattern = re.compile(
        r'(^.*".*"|^.*x.*x|^[^"x]*)(\s*[^#]*)#.*'.replace("x", "'"), flags=re.MULTILINE
    )
    KEY_VALUE_RE: re.Pattern = re.compile(r"\s*=\s*")

    _loaded: list[str] = []

    ###########################################################################

    @staticmethod
    def load_from_file(opts: Namespace, path: Path):
        """
        Load environment variables from a .env-compliant file

        :param path: a file to load from
        :type path: Path
        """

        DotEnv.load_from_str(DotEnv.read_text(opts, path))

    ###########################################################################

    @staticmethod
    def load_from_str(data: str):
        """
        Load environment variables from a string

        :param data: a string to load from
        :type data: str
        """

        # Split data into lines and loop through every line

        for line in data.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            # Remove comments

            m = DotEnv.COMMENTS_RE.match(line)
            line = (m.group(1) + m.group(2)) if (m) else line

            # Split key and value, then trim the key

            parts = DotEnv.KEY_VALUE_RE.split(line)
            key = parts[0].strip()

            # If the key is empty, silently continue

            if not key or (len(parts) < 2):
                continue

            # Trim the value and get its length

            value = parts[1].strip()
            length = len(value)
            can_expand = True  # allow expansion by default

            # If the value is double-quoted, unquote it
            # If the value is single-quoted, unquote it and disallow expansion

            if length >= 2:
                if (value[0] == '"') and (value[length - 1] == '"'):
                    value = value[1 : length - 1]
                elif (value[0] == "'") and (value[length - 1] == "'"):
                    value = value[1 : length - 1]
                    can_expand = False

            # Expand escaped characters and environment variables if allowed

            if can_expand:
                value = os.path.expandvars(value.encode().decode(DotEnv.ESCAPING))

            # Add new environment variable or override the existing one

            os.environ[key] = value

    ###########################################################################

    @staticmethod
    def read_text(opts: Namespace, path: Path) -> str:
        """
        Load environment variables from .env-compliant files: in the directory
        of the user-defined file or in the current one otherwise, it will first
        load .env, then any.env, then <platform>.env, then the fallback ones,
        then the one passed (if not None)

        :param path: a path to a custom file to load from
        :type path: Path
        """

        # Get the default directory (should be validated already)

        content = ""

        is_dir = True if ((not path) or path.is_dir()) else False
        dir = (
            Path(opts.config).parent
            if (path is None)
            else (path if (is_dir) else path.parent)
        )

        plat_name = platform.system().lower()

        # Try loading the file for the following platforms in the specified order if the
        # right side is empty, or represents a part of the current platform name

        x = DotEnv.DEF_FILE_TYPE

        for plat_pairs in [
            "",
            "any:",
            "unix:aix",
            "bsd",
            "unix:bsd",
            "unix:linux",
            "bsd:darwin",
            "bsd:macos",
            "macos:darwin",
            "darwin:macos",
            "windows",
        ]:
            # Break text into the base platform name, and the current platform's substring

            parts = plat_pairs.split(":")
            count = len(parts)

            plat_base = parts[0]
            plat_like = parts[1 if (count > 1) else 0]

            # If the platform pattern is not empty, and the current one doesn't match

            if plat_like and (plat_like not in plat_name) or (count > 2):
                continue

            # Load the environment from the current base platform and add it to the list
            # of the loaded ones

            _path = dir / f"{plat_base}{x}"
            _path_str = str(_path)

            if (_path_str not in DotEnv._loaded) and _path.exists():
                content += f"{_path.read_text()}\n"
                DotEnv._loaded.append(_path_str)

            # Check whether the current platform matches the templates and load the
            # respective file if so

            if (not plat_base) or (not plat_like) or (plat_like == plat_base):
                continue

            _path = dir / f"{plat_like}{x}"
            _path_str = str(_path)

            if (_path_str not in DotEnv._loaded) and _path.exists():
                content += f"{_path.read_text()}\n"
                DotEnv._loaded.append(_path_str)

        # Finally, load the one passed by the user if not covered yet

        _path_str = str(path) if (path) else ""

        if (
            (not is_dir)
            and _path_str
            and (_path_str not in DotEnv._loaded)
            and path.exists()
        ):
            content += f"{path.read_text()}\n"
            DotEnv._loaded.append(_path_str)

        return content


###############################################################################
