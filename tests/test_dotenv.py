#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for DotEnv
###############################################################################

from pathlib import Path
from dotenv import DotEnv
from dotenv_file_flags import DotEnvFileFlags
from env_expand_flags import EnvExpandFlags

###############################################################################


def test_load_from_str_basic(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    data = "KEY1 =   VALUE1\nKEY2\t=\t\tVALUE2"

    # Act
    result = DotEnv.load_from_str(data)

    # Assert
    assert m_environ["KEY1"] == "VALUE1"
    assert m_environ["KEY2"] == "VALUE2"
    assert result == data


def test_load_from_str_skip_empty_lines(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    data = "KEY1 = VALUE1\n\n  \nKEY2=VALUE2"

    # Act
    DotEnv.load_from_str(data)

    # Assert
    assert m_environ["KEY1"] == "VALUE1"
    assert m_environ["KEY2"] == "VALUE2"
    assert len(m_environ) == 2


def test_load_from_str_deletion(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {"KEY1": "OLD_VALUE", "KEY2": "STAY"})
    data = "KEY1="

    # Act
    DotEnv.load_from_str(data)

    # Assert
    assert "KEY1" not in m_environ
    assert m_environ["KEY2"] == "STAY"


def test_load_from_str_with_args(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    data = "KEY1=$1\nKEY2=${2}"
    args = ["arg1", "arg2"]

    # Act
    DotEnv.load_from_str(data, args=args)

    # Assert
    assert m_environ["KEY1"] == "arg1"
    assert m_environ["KEY2"] == "arg2"


def test_load_from_str_sequential_expansion(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    data = "KEY1=VALUE1\nKEY2=$KEY1"

    # Act
    DotEnv.load_from_str(data)

    # Assert
    assert m_environ["KEY1"] == "VALUE1"
    assert m_environ["KEY2"] == "VALUE1"


def test_load_from_str_comments(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    data = "KEY1=VALUE1 # basic comment\nKEY2='VAL#UE2' # quoted comment\n# Full line comment\nKEY3=VALUE3"

    # Act
    DotEnv.load_from_str(data)

    # Assert
    assert m_environ["KEY1"] == "VALUE1"
    assert m_environ["KEY2"] == "VAL#UE2"
    assert m_environ["KEY3"] == "VALUE3"


class TestReadText:
    """Test suite for DotEnv.read_text method"""

    def setup_method(self):
        DotEnv._loaded = []

    def test_read_text_skip_defaults(self, mocker):
        # Arrange
        m_path = mocker.MagicMock(spec=Path)
        m_path.is_dir.return_value = False
        m_path.exists.return_value = True
        m_path.read_text.return_value = "KEY=VAL"
        m_path.is_absolute.return_value = True
        m_path.absolute.return_value = m_path
        m_path.__str__.return_value = "/path/to/file.env"
        m_path.parent.__truediv__.return_value = m_path

        # Act
        content = DotEnv.read_text(
            m_path, file_flags=DotEnvFileFlags.SKIP_DEFAULT_FILES
        )

        # Assert
        assert content == "KEY=VAL\n"
        assert "/path/to/file.env" in DotEnv._loaded

    def test_read_text_reset_flag(self, mocker):
        # Arrange
        DotEnv._loaded = ["/already/loaded"]
        m_path = mocker.MagicMock(spec=Path)
        m_path.is_dir.return_value = False
        m_path.exists.return_value = False
        m_path.is_absolute.return_value = True
        m_path.absolute.return_value = m_path

        # Act
        DotEnv.read_text(
            m_path,
            file_flags=DotEnvFileFlags.RESET | DotEnvFileFlags.SKIP_DEFAULT_FILES,
        )

        # Assert
        assert "/already/loaded" not in DotEnv._loaded

    def test_read_text_with_platform_stack(self, mocker):
        # Arrange
        m_get_stack = mocker.patch(
            "dotenv.Env.get_platform_stack", return_value=[".env", ".linux.env"]
        )

        mock_paths = {}

        def get_mock_path(path_str):
            if path_str not in mock_paths:
                m = mocker.MagicMock(spec=Path)
                m.exists.return_value = False
                m.read_text.return_value = f"CONTENT_OF_{path_str}"
                m.__str__.return_value = path_str
                m.is_absolute.return_value = True
                m.absolute.return_value = m
                m.__truediv__.side_effect = lambda other: get_mock_path(
                    f"{path_str}/{other}"
                )
                mock_paths[path_str] = m
            return mock_paths[path_str]

        m_cwd = get_mock_path("/cwd")
        mocker.patch.object(Path, "cwd", return_value=m_cwd)

        get_mock_path("/cwd/.env").exists.return_value = True
        get_mock_path("/cwd/.linux.env").exists.return_value = True

        # Act
        content = DotEnv.read_text(None)

        # Assert
        assert "CONTENT_OF_/cwd/.env" in content
        assert "CONTENT_OF_/cwd/.linux.env" in content
        m_get_stack.assert_called_once()

    def test_read_text_alt_ext(self, mocker):
        # Arrange
        m_get_stack = mocker.patch(
            "dotenv.Env.get_platform_stack", return_value=[".myenv"]
        )
        m_cwd = mocker.MagicMock(spec=Path)
        m_cwd.is_absolute.return_value = True
        m_cwd.absolute.return_value = m_cwd
        mocker.patch.object(Path, "cwd", return_value=m_cwd)

        m_file = mocker.MagicMock(spec=Path)
        m_cwd.__truediv__.return_value = m_file
        m_file.exists.return_value = True
        m_file.read_text.return_value = "ALT_CONTENT"
        m_file.__str__.return_value = "/cwd/.myenv"

        # Act
        content = DotEnv.read_text(None, alt_ext="myenv")

        # Assert
        assert "ALT_CONTENT" in content
        m_get_stack.assert_called_once_with(mocker.ANY, ".", ".myenv")

    def test_read_text_visible_files_flag(self, mocker):
        # Arrange
        m_get_stack = mocker.patch(
            "dotenv.Env.get_platform_stack", return_value=["env"]
        )
        m_cwd = mocker.MagicMock(spec=Path)
        m_cwd.is_absolute.return_value = True
        m_cwd.absolute.return_value = m_cwd
        mocker.patch.object(Path, "cwd", return_value=m_cwd)

        m_file = mocker.MagicMock(spec=Path)
        m_cwd.__truediv__.return_value = m_file
        m_file.exists.return_value = True
        m_file.read_text.return_value = "VISIBLE_CONTENT"
        m_file.__str__.return_value = "/cwd/env"

        # Act
        DotEnv.read_text(None, file_flags=DotEnvFileFlags.VISIBLE_FILES)

        # Assert
        # When VISIBLE_FILES is set, prefix passed to get_platform_stack should be ""
        m_get_stack.assert_called_once_with(mocker.ANY, "", mocker.ANY)

    def test_read_text_persistence_and_reset(self, mocker):
        # Arrange
        mocker.patch("dotenv.Env.get_platform_stack", return_value=[".env"])
        m_cwd = mocker.MagicMock(spec=Path)
        m_cwd.is_absolute.return_value = True
        m_cwd.absolute.return_value = m_cwd
        mocker.patch.object(Path, "cwd", return_value=m_cwd)

        m_file = mocker.MagicMock(spec=Path)
        m_cwd.__truediv__.return_value = m_file
        m_file.exists.return_value = True
        m_file.read_text.return_value = "A=B"
        m_file.__str__.return_value = "/cwd/.env"

        # Act 1: First load
        content1 = DotEnv.read_text(None)
        assert "A=B" in content1
        assert "/cwd/.env" in DotEnv._loaded

        # Act 2: Second load without reset - should not load again
        content2 = DotEnv.read_text(None)
        assert content2 == ""

        # Act 3: Third load with reset - should load again
        content3 = DotEnv.read_text(None, file_flags=DotEnvFileFlags.RESET)
        assert "A=B" in content3


class TestLoadFromFile:
    """Test suite for DotEnv.load_from_file method"""

    def test_load_from_file(self, mocker):
        # Arrange
        m_read_text = mocker.patch("dotenv.DotEnv.read_text", return_value="KEY=VAL")
        m_load_from_str = mocker.patch("dotenv.DotEnv.load_from_str")
        m_path = mocker.MagicMock(spec=Path)

        # Act
        result = DotEnv.load_from_file(m_path)

        # Assert
        m_read_text.assert_called_once()
        # Ensure expand_flags is passed correctly as keyword
        m_load_from_str.assert_called_once_with(
            "KEY=VAL", expand_flags=DotEnv.DEFAULT_EXPAND_FLAGS
        )
        assert result == "KEY=VAL"

    def test_load_from_file_with_default_dir(self, mocker):
        # Arrange
        m_read_text = mocker.patch("dotenv.DotEnv.read_text", return_value="KEY=VAL")
        mocker.patch("dotenv.DotEnv.load_from_str")
        m_path = mocker.MagicMock(spec=Path)
        dir = Path("/some/path")

        # Act
        DotEnv.load_from_file(m_path, default_dir=dir)

        # Assert
        args, _ = m_read_text.call_args
        # args[2] is default_dir
        assert isinstance(args[2], Path)
        assert str(args[2]) == str(dir)
