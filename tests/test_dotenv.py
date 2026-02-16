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


def test_read_text_reset_flag(mocker):
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
        file_flags=DotEnvFileFlags.RESET,
    )

    # Assert
    assert "/already/loaded" not in DotEnv._loaded


def test_read_text_with_platform_stack(mocker):
    # Arrange
    DotEnv._loaded = []
    m_get_stack = mocker.patch(
        "dotenv.Env.get_platform_stack", return_value=[".env", f".{Env.PLATFORM_THIS}.env"]
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
            m.__truediv__.side_effect = lambda other: get_mock_path(f"{path_str}/{other}")
            mock_paths[path_str] = m
        return mock_paths[path_str]

    m_cwd = get_mock_path("/cwd")
    mocker.patch.object(Path, "cwd", return_value=m_cwd)

    get_mock_path("/cwd/.env").exists.return_value = True
    get_mock_path(f"/cwd/.{Env.PLATFORM_THIS}.env").exists.return_value = True

    # Act
    content = DotEnv.read_text(None)

    # Assert
    assert "CONTENT_OF_/cwd/.env" in content
    assert f"CONTENT_OF_/cwd/.{Env.PLATFORM_THIS}.env" in content
    m_get_stack.assert_called_once()


def test_read_text_alt_ext(mocker):
    # Arrange
    DotEnv._loaded = []
    m_get_stack = mocker.patch("dotenv.Env.get_platform_stack", return_value=[".myenv"])
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


def test_read_text_persistence_and_reset(mocker):
    # Arrange
    DotEnv._loaded = []
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


def test_load(mocker):
    # Arrange
    m_read_text = mocker.patch("dotenv.DotEnv.read_text", return_value="KEY=VAL")
    m_load_from_str = mocker.patch("dotenv.DotEnv.load_from_str")
    m_path = mocker.MagicMock(spec=Path)

    # Act
    result = DotEnv.load(m_path)

    # Assert
    m_read_text.assert_called_once()
    # Ensure expand_flags is passed correctly as keyword
    m_load_from_str.assert_called_once_with(
        "KEY=VAL", expand_flags=DotEnv.DEFAULT_EXPAND_FLAGS
    )
    assert result == "KEY=VAL"


def test_load_with_default_dir(mocker):
    # Arrange
    m_read_text = mocker.patch("dotenv.DotEnv.read_text", return_value="KEY=VAL")
    mocker.patch("dotenv.DotEnv.load_from_str")
    m_path = mocker.MagicMock(spec=Path)
    dir = Path("/some/path")

    # Act
    DotEnv.load(m_path, dir=dir)

    # Assert
    args, _ = m_read_text.call_args
    # args[2] is default_dir
    assert isinstance(args[2], Path)
    assert str(args[2]) == str(dir)


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
