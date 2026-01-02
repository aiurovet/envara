#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for DotEnv
###############################################################################

import os
from unittest.mock import Mock
from pathlib import Path
from dotenv import DotEnv, DotEnvFileFlags
from env import Env

###############################################################################


class TestDotEnv:
    """Test suite for DotEnv class"""

    def test_load_from_str(self, mocker: Mock):
        # Arrange
        data = "KEY1=VAL1\nKEY2=VAL2\nKEY3="
        mocker.patch.dict(os.environ, {"KEY3": "OLD_VAL"}, clear=True)
        mock_expand = mocker.patch.object(Env, "expand", side_effect=lambda v, a, f: v)

        # Act
        DotEnv.load_from_str(data, DotEnv.DEFAULT_EXPAND_FLAGS)

        # Assert
        assert os.environ["KEY1"] == "VAL1"
        assert os.environ["KEY2"] == "VAL2"
        assert "KEY3" not in os.environ
        assert mock_expand.call_count == 2

    def test_load_from_str_complex_line_endings(self, mocker: Mock):
        # Arrange
        data = "K1=V1\rK2=V2\r\nK3=V3"
        mocker.patch.dict(os.environ, {}, clear=True)
        mocker.patch.object(Env, "expand", side_effect=lambda v, a, f: v)

        # Act
        DotEnv.load_from_str(data)

        # Assert
        assert os.environ["K1"] == "V1"
        assert os.environ["K2"] == "V2"
        assert os.environ["K3"] == "V3"

    def test_read_text_reset(self, mocker: Mock):
        # Arrange
        DotEnv._loaded = ["some_file"]
        mocker.patch("platform.system", return_value="Linux")
        mocker.patch.object(Path, "exists", return_value=False)
        mocker.patch.object(Path, "cwd", return_value=Path("/tmp"))

        # Act
        DotEnv.read_text(None, DotEnvFileFlags.RESET)

        # Assert
        assert DotEnv._loaded == []

    def test_read_text_hierarchy(self, mocker: Mock):
        # Arrange
        mocker.patch("platform.system", return_value="Linux")
        mocker.patch.object(Path, "cwd", return_value=Path("/app"))

        # Mock Path.exists to return True for specific files
        def mock_exists(self):
            return str(self) in ["/app/.env", "/app/.linux.env", "/app/custom.env"]

        mocker.patch.object(Path, "exists", autospec=True, side_effect=mock_exists)

        # Mock Path.read_text
        def mock_read_text(self):
            return f"content_of_{self.name}"

        mocker.patch.object(
            Path, "read_text", autospec=True, side_effect=mock_read_text
        )

        DotEnv._loaded = []

        # Act
        content = DotEnv.read_text(Path("/app/custom.env"), DotEnvFileFlags.DEFAULT)

        # Assert
        # Linux plat_map: ["posix", "linux"]
        # Expected files in order:
        # .any.env (not exists)
        # .posix.env (not exists)
        # .linux.env (exists)
        # .env (exists - actually it is listed first in loop usually but let's check order)
        # custom.env (exists)

        # In DotEnv._plat_map:
        # "": ["", "any"] -> .env, .any.env
        # "^(java|linux|cygwin|msys)": ["posix", "linux"] -> .posix.env, .linux.env

        assert "content_of_.env" in content
        assert "content_of_.linux.env" in content
        assert "content_of_custom.env" in content
        assert "/app/.env" in DotEnv._loaded
        assert "/app/.linux.env" in DotEnv._loaded
        assert "/app/custom.env" in DotEnv._loaded

    def test_load_from_file(self, mocker: Mock):
        # Arrange
        path = Path("test.env")
        mock_read = mocker.patch.object(DotEnv, "read_text", return_value="K=V")
        mock_load_str = mocker.patch.object(DotEnv, "load_from_str")

        # Act
        DotEnv.load_from_file(path)

        # Assert
        mock_read.assert_called_once_with(path, DotEnvFileFlags.DEFAULT, None)
        mock_load_str.assert_called_once_with("K=V", DotEnv.DEFAULT_EXPAND_FLAGS)


###############################################################################
