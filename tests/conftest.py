from pathlib import Path
import sys
import os
from unittest.mock import patch
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import envara
import envara.env_chars as env_chars_mod
import envara.env_chars_data as env_chars_data_mod
import envara.env_filter as env_filter_mod  # type: ignore
import envara.env_filters as env_filters_mod  # type: ignore
import envara.env_file as env_file_mod  # type: ignore
import envara.env_file_flags as env_file_flags_mod  # type: ignore
import envara.env_expand_flags as env_expand_flags_mod  # type: ignore

envara.Env = type("Env", (), {})()  # type: ignore
envara.EnvChars = env_chars_mod.EnvChars  # type: ignore
envara.EnvCharsData = env_chars_data_mod.EnvCharsData  # type: ignore
envara_mod = envara

os.chdir(str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def mock_platform():
    with patch("os.sep", "/"):
        with patch("envara.env.Env.IS_POSIX", True):
            with patch("envara.env.Env.IS_WINDOWS", False):
                env_chars_mod.EnvChars.Current = (
                    env_chars_mod.EnvChars.POSIX.copy_with()
                )
                yield
                env_chars_mod.EnvChars.Current = (
                    env_chars_mod.EnvChars.Default.copy_with()
                )


@pytest.fixture
def mock_windows_paths():
    """Mock os.path functions for Windows path slicing tests"""
    with patch("os.path.splitdrive", return_value=("C:", "\\path\\file.txt")):
        with patch("os.path.dirname", return_value="\\path"):
            with patch("os.path.basename", return_value="file.txt"):
                with patch("os.path.splitext", return_value=("file", ".txt")):
                    with patch("os.path.abspath", return_value="C:\\path\\file.txt"):
                        yield
