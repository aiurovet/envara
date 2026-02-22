#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for DotEnv
###############################################################################


from pathlib import Path
from dotenv import DotEnv
from dotenv_file_flags import DotEnvFileFlags
import re

# simple stand-in filter class for exercising DotEnv.get_files logic
class SimpleFilter:
    def __init__(self, all_pattern: str, cur_pattern: str):
        self.all_regex = re.compile(all_pattern)
        self.cur_regex = re.compile(cur_pattern)


def test_read_text_basic(mocker):
    # Arrange
    DotEnv._loaded = []
    m1 = mocker.MagicMock(spec=Path)
    m1.read_text.return_value = "A"
    m1.__str__.return_value = "/tmp/one"

    m2 = mocker.MagicMock(spec=Path)
    m2.read_text.return_value = "B"
    m2.__str__.return_value = "/tmp/two"

    # Act
    result = DotEnv.read_text([m1, m2], flags=0)

    # Assert
    assert result == "A\nB"
    assert "/tmp/one" in DotEnv._loaded
    assert "/tmp/two" in DotEnv._loaded


def test_read_text_skips_already_loaded(mocker):
    # Arrange - mark first file as already loaded
    DotEnv._loaded = ["/tmp/one"]
    m1 = mocker.MagicMock(spec=Path)
    m1.read_text.return_value = "A"
    m1.__str__.return_value = "/tmp/one"

    m2 = mocker.MagicMock(spec=Path)
    m2.read_text.return_value = "B"
    m2.__str__.return_value = "/tmp/two"

    # Act
    result = DotEnv.read_text([m1, m2], flags=0)

    # Assert - only second file's content is returned, both paths present in _loaded
    assert result == "B"
    assert "/tmp/one" in DotEnv._loaded
    assert "/tmp/two" in DotEnv._loaded


def test_read_text_ignores_exceptions(mocker):
    # Arrange
    DotEnv._loaded = []
    m1 = mocker.MagicMock(spec=Path)
    m1.read_text.return_value = "A"
    m1.__str__.return_value = "/tmp/one"

    m2 = mocker.MagicMock(spec=Path)
    m2.read_text.side_effect = Exception("boom")
    m2.__str__.return_value = "/tmp/two"

    # Act
    result = DotEnv.read_text([m1, m2], flags=0)

    # Assert - exception from second file is ignored, but its path is still recorded
    assert result == "A"
    assert "/tmp/one" in DotEnv._loaded
    assert "/tmp/two" in DotEnv._loaded


def test_read_text_reset_flag(mocker):
    # Arrange - _loaded contains a previous entry but RESET should clear it
    DotEnv._loaded = ["/tmp/one"]
    m1 = mocker.MagicMock(spec=Path)
    m1.read_text.return_value = "A"
    m1.__str__.return_value = "/tmp/one"

    # Act
    result = DotEnv.read_text([m1], flags=DotEnvFileFlags.RESET)

    # Assert - content read and _loaded contains the file again
    assert result == "A"
    assert "/tmp/one" in DotEnv._loaded


def test_load_with_empty_stack(mocker):
    # Arrange - no files found
    mocker.patch("dotenv.DotEnv.get_files", return_value=[])
    m_read_text = mocker.patch("dotenv.DotEnv.read_text", return_value="")
    m_load_from_str = mocker.patch("dotenv.DotEnv.load_from_str")
    m_dir = mocker.MagicMock(spec=Path)

    # Act
    result = DotEnv.load(m_dir)

    # Assert
    m_read_text.assert_called_once()
    m_load_from_str.assert_called_once_with("", exp_flags=DotEnv.DEFAULT_EXPAND_FLAGS)
    assert result == ""


def test_load_reads_files_and_passes_flags(mocker):
    # Arrange - simulate get_files returning two files and read_text returning content
    fake_files = [mocker.MagicMock(spec=Path), mocker.MagicMock(spec=Path)]
    mocker.patch("dotenv.DotEnv.get_files", return_value=fake_files)
    m_read_text = mocker.patch("dotenv.DotEnv.read_text", return_value="K=V")
    m_load_from_str = mocker.patch("dotenv.DotEnv.load_from_str")
    m_dir = mocker.MagicMock(spec=Path)
    flags = DotEnvFileFlags.DEFAULT

    # Act
    result = DotEnv.load(m_dir, file_flags=flags)

    # Assert
    m_read_text.assert_called_once()
    m_load_from_str.assert_called_once_with("K=V", exp_flags=DotEnv.DEFAULT_EXPAND_FLAGS)


def test_load_from_str_uses_env_expand(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    m_expand = mocker.patch("dotenv.Env.expand", return_value=("EXPANDED", None))
    data = "KEY=VALUE"

    # Act
    DotEnv.load_from_str(data)

    # Assert
    m_expand.assert_called_once_with("VALUE", None, DotEnv.DEFAULT_EXPAND_FLAGS)
    assert m_environ["KEY"] == "EXPANDED"


def test_load_from_str_passes_args_and_flags(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    m_expand = mocker.patch("dotenv.Env.expand", return_value=("X", None))
    data = "K=$1"
    args = ["a1"]
    flags = DotEnv.DEFAULT_EXPAND_FLAGS

    # Act
    DotEnv.load_from_str(data, args=args, exp_flags=flags)

    # Assert
    m_expand.assert_called_once_with("$1", args, flags)
    assert m_environ["K"] == "X"


def test_get_files_basic_filtering(tmp_path):
    # Arrange - create a few fake files in a temporary directory
    for name in ['dev.env', 'prod.env', 'other.txt']:
        (tmp_path / name).write_text('')

    # a simple filter object that matches 'dev' or 'prod' and only 'prod' as current
    filt = SimpleFilter(all_pattern=r"dev|prod", cur_pattern=r"prod")

    # Act
    result = DotEnv.get_files(tmp_path, 0, filt)

    # Assert - operate on names for clarity
    names = [p.name for p in result]
    assert 'prod.env' in names
    assert 'other.txt' in names
    assert 'dev.env' not in names


def test_get_files_adds_platform_filter(tmp_path, mocker):
    # Arrange - stub platform filter so only names containing "plat" stay
    fake_platform = SimpleFilter(all_pattern=r"plat", cur_pattern=r"plat")
    m_platform = mocker.patch('dotenv.Env.get_platform_stack', return_value=fake_platform)

    # create files in temp directory
    for name in ['file.plat.env', 'file.other.env']:
        (tmp_path / name).write_text('')

    # Act
    result = DotEnv.get_files(tmp_path)

    # Assert - platform filter applied automatically
    assert m_platform.called
    names = [p.name for p in result]
    assert 'file.plat.env' in names
    assert 'file.other.env' not in names
