#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for DotEnv
###############################################################################

from pathlib import Path
import re
from dotenv import DotEnv
from dotenv_file_flags import DotEnvFileFlags
from env import Env

###############################################################################

def test_append_filter_with_none():
    target: list[re.Pattern] = []
    result = DotEnv._DotEnv__append_filter(target, None)
    assert result is None
    assert len(target) == 1
    pattern = target[0].pattern
    assert '(env)' in pattern
    # basic matches for the default indicator
    assert target[0].search('.env')
    assert target[0].search('-env')
    assert target[0].search('_env')
    assert target[0].search('env')
    assert target[0].search('env-')
    assert target[0].search('env_')
    assert target[0].search('.env.')
    assert target[0].search('-env-')
    assert target[0].search('_env_')
    assert target[0].search('env')
    assert target[0].search('env-')
    assert target[0].search('.env_')
    assert target[0].search('_env-')


def test_append_filter_with_string():
    target: list[re.Pattern] = []
    DotEnv._DotEnv__append_filter(target, 'prod')
    assert len(target) == 1
    pat = target[0]
    # current implementation composes a pattern including the indicator
    assert '(prod)' in pat.pattern
    assert '(env)' in pat.pattern
    assert r'[\.\-_]' in pat.pattern
    # should not match when there's no separator between parts
    assert not pat.search('prodenv')
    assert pat.search('prod.env')
    assert pat.search('env_prod')
    assert pat.search('_env_prod_')
    assert pat.search('-env-prod-')
    assert pat.search('.env.prod')


def test_append_filter_with_list():
    target: list[re.Pattern] = []
    DotEnv._DotEnv__append_filter(target, ['posix', 'bsd', 'macos'])
    assert len(target) == 1
    pat = target[0]
    # pattern contains the listed alternatives and the indicator
    assert '(posix|bsd|macos)' in pat.pattern
    assert '(env)' in pat.pattern
    assert '[\.\-_]' in pat.pattern
    assert not pat.search('envposix')
    assert pat.search('env-posix')
    assert pat.search('posix-env')
    assert pat.search('_posix_env_')
    assert pat.search('.env.posix')
    assert pat.search('.env.posix.env')
    assert pat.search('-posix.env.posix')


def test_get_file_stack_with_platforms_no_filters(mocker):
    # Arrange - mock a directory with files
    files = [
        ".env",
        f".{Env.PLATFORM_THIS}.env",
        "prod.env",
        "env-prod",
        "README.md",
    ]
    mock_files = []
    for name in files:
        m = mocker.MagicMock(spec=Path)
        m.name = name
        mock_files.append(m)

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = mock_files
    m_dir.__truediv__.side_effect = lambda other: Path(other)

    # Act
    result = DotEnv.get_file_stack(dir=m_dir, flags=DotEnvFileFlags.ADD_PLATFORMS)

    # Assert - current implementation matches only the simple default name
    names = {p.name for p in result}
    assert ".env" in names
    assert f".{Env.PLATFORM_THIS}.env" in names
    assert "prod.env" not in names
    assert "env-prod" not in names
    assert "README.md" not in names


def test_get_file_stack_without_platforms_no_filters(mocker):
    # Arrange - mock a directory with files
    files = [
        ".env",
        f".{Env.PLATFORM_THIS}.env",
        "prod.env",
        "env-prod",
        "README.md",
    ]
    mock_files = []
    for name in files:
        m = mocker.MagicMock(spec=Path)
        m.name = name
        mock_files.append(m)

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = mock_files
    m_dir.__truediv__.side_effect = lambda other: Path(other)

    # Act
    result = DotEnv.get_file_stack(dir=m_dir, flags=0)

    # Assert - current implementation matches only the simple default name
    names = {p.name for p in result}
    assert ".env" in names
    assert f".{Env.PLATFORM_THIS}.env" not in names
    assert "prod.env" not in names
    assert "env-prod" not in names
    assert "README.md" not in names


def test_get_file_stack_with_filter(mocker):
    # Arrange
    names_to_create = ["prod.env", "env-prod", "dev.env", "other.txt"]
    mock_files = []
    for name in names_to_create:
        m = mocker.MagicMock(spec=Path)
        m.name = name
        mock_files.append(m)

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = mock_files
    m_dir.__truediv__.side_effect = lambda other: Path(other)

    # Act - filter for 'prod'
    result = DotEnv.get_file_stack(m_dir, 0, "prod")

    # Assert - current implementation requires matching all patterns, so
    # combining default and filter produces no matches in this layout
    res_names = {p.name for p in result}
    assert res_names == set()


def test_get_file_stack_with_filter(mocker):
    # Arrange
    names_to_create = ["prod.env", "env-prod", "dev.env", "other.txt"]
    mock_files = []
    for name in names_to_create:
        m = mocker.MagicMock(spec=Path)
        m.name = name
        mock_files.append(m)

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = mock_files
    m_dir.__truediv__.side_effect = lambda other: Path(other)

    # Act - filter for 'prod'
    result = DotEnv.get_file_stack(m_dir, 0, "prod")

    # Assert - current implementation requires matching all patterns, so
    # combining default and filter produces no matches in this layout
    res_names = {p.name for p in result}
    assert set(res_names) == set(["prod.env", "env-prod"])


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
    mocker.patch("dotenv.DotEnv.get_file_stack", return_value=[])
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
    # Arrange - simulate get_file_stack returning two files and read_text returning content
    fake_files = [mocker.MagicMock(spec=Path), mocker.MagicMock(spec=Path)]
    mocker.patch("dotenv.DotEnv.get_file_stack", return_value=fake_files)
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
