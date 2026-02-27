#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for EnvFile
###############################################################################


from pathlib import Path
from envara.env_file import EnvFile
from envara.env_file_flags import EnvFileFlags

from envara.env_filter import EnvFilter

from env_expand_flags import EnvExpandFlags


def test_read_text_basic(mocker):
    # Arrange
    EnvFile._loaded = []
    m1 = mocker.MagicMock(spec=Path)
    m1.read_text.return_value = "A"
    m1.__str__.return_value = "/tmp/one"

    m2 = mocker.MagicMock(spec=Path)
    m2.read_text.return_value = "B"
    m2.__str__.return_value = "/tmp/two"

    # Act
    result = EnvFile.read_text([m1, m2], flags=0)

    # Assert
    assert result == "A\nB"
    assert "/tmp/one" in EnvFile._loaded
    assert "/tmp/two" in EnvFile._loaded


def test_read_text_skips_already_loaded(mocker):
    # Arrange - mark first file as already loaded
    EnvFile._loaded = ["/tmp/one"]
    m1 = mocker.MagicMock(spec=Path)
    m1.read_text.return_value = "A"
    m1.__str__.return_value = "/tmp/one"

    m2 = mocker.MagicMock(spec=Path)
    m2.read_text.return_value = "B"
    m2.__str__.return_value = "/tmp/two"

    # Act
    result = EnvFile.read_text([m1, m2], flags=0)

    # Assert - only second file's content is returned, both paths present in _loaded
    assert result == "B"
    assert "/tmp/one" in EnvFile._loaded
    assert "/tmp/two" in EnvFile._loaded


def test_read_text_ignores_exceptions(mocker):
    # Arrange
    EnvFile._loaded = []
    m1 = mocker.MagicMock(spec=Path)
    m1.read_text.return_value = "A"
    m1.__str__.return_value = "/tmp/one"

    m2 = mocker.MagicMock(spec=Path)
    m2.read_text.side_effect = Exception("boom")
    m2.__str__.return_value = "/tmp/two"

    # Act
    result = EnvFile.read_text([m1, m2], flags=0)

    # Assert - exception from second file is ignored, but its path is still recorded
    assert result == "A"
    assert "/tmp/one" in EnvFile._loaded
    assert "/tmp/two" in EnvFile._loaded


def test_read_text_reset_flag(mocker):
    # Arrange - _loaded contains a previous entry but RESET should clear it
    EnvFile._loaded = ["/tmp/one"]
    m1 = mocker.MagicMock(spec=Path)
    m1.read_text.return_value = "A"
    m1.__str__.return_value = "/tmp/one"

    # Act
    result = EnvFile.read_text([m1], flags=EnvFileFlags.RESET_ACCUMULATED)

    # Assert - content read and _loaded contains the file again
    assert result == "A"
    assert "/tmp/one" in EnvFile._loaded


def test_load_with_empty_args_and_empty_file_list(mocker):
    # Arrange - no files found
    mocker.patch("envara.env_file.EnvFile.get_files", return_value=[])
    m_read_text = mocker.patch("envara.env_file.EnvFile.read_text", return_value="")
    m_load_from_str = mocker.patch("envara.env_file.EnvFile.load_from_str")
    m_dir = mocker.MagicMock(spec=Path)

    # Act
    EnvFile.load(m_dir)

    # Assert
    m_read_text.assert_called_once()
    m_load_from_str.assert_called_once_with(
        "", args=None, expand_flags=EnvFile.DEFAULT_EXPAND_FLAGS
    )


def test_load_with_nonempty_args_and_empty_file_list(mocker):
    # Arrange - no files found
    content = "V1=$1\nV2=$2"
    args = ["a1", "a2"]
    mocker.patch("envara.env_file.EnvFile.get_files", return_value=[])
    m_read_text = mocker.patch(
        "envara.env_file.EnvFile.read_text", return_value=content
    )
    m_load_from_str = mocker.patch("envara.env_file.EnvFile.load_from_str")
    m_dir = mocker.MagicMock(spec=Path)

    # Act
    EnvFile.load(m_dir, args=args)

    # Assert
    m_read_text.assert_called_once()
    m_load_from_str.assert_called_once_with(
        content, args=args, expand_flags=EnvFile.DEFAULT_EXPAND_FLAGS
    )


def test_load_reads_files_and_passes_flags(mocker):
    # Arrange - simulate get_files returning two files and read_text returning content
    fake_files = [mocker.MagicMock(spec=Path), mocker.MagicMock(spec=Path)]
    mocker.patch("envara.env_file.EnvFile.get_files", return_value=fake_files)
    m_read_text = mocker.patch("envara.env_file.EnvFile.read_text", return_value="K=V")
    m_load_from_str = mocker.patch("envara.env_file.EnvFile.load_from_str")
    m_dir = mocker.MagicMock(spec=Path)
    flags = EnvFileFlags.ADD_PLATFORMS

    # Act
    result = EnvFile.load(m_dir, file_flags=flags)

    # Assert
    m_read_text.assert_called_once()
    m_load_from_str.assert_called_once_with(
        "K=V", args=None, expand_flags=EnvFile.DEFAULT_EXPAND_FLAGS
    )


def test_load_from_str_uses_env_expand(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    m_expand = mocker.patch("envara.env.Env.expand", return_value="EXPANDED")
    data = "KEY=VALUE"

    # Act
    EnvFile.load_from_str(data)

    # Assert
    m_expand.assert_called_once_with("VALUE", args=None, flags=EnvFile.DEFAULT_EXPAND_FLAGS)
    assert m_environ["KEY"] == "EXPANDED"


def test_load_from_str_passes_args_and_flags(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    m_expand = mocker.patch("envara.env.Env.expand", return_value="X")
    data = "K=$1"
    args = ["a1"]
    flags = EnvFile.DEFAULT_EXPAND_FLAGS

    # Act
    EnvFile.load_from_str(data, args=args, expand_flags=flags)

    # Assert
    m_expand.assert_called_once_with("$1", args=args, flags=flags)
    assert m_environ["K"] == "X"


def test_get_files_basic_filtering(tmp_path):
    # Arrange - create a few fake files in a temporary directory
    for name in ["dev.env", "prod.env", "other.txt"]:
        (tmp_path / name).write_text("")

    # a simple filter object that matches 'dev' or 'prod' and only 'prod' as current
    filt = EnvFilter(all_values="dev|prod", cur_values=r"prod")

    # Act
    result = EnvFile.get_files(tmp_path, "env", 0, filt)

    # Assert - operate on names for clarity
    names = [p.name for p in result]
    assert "prod.env" in names
    assert "other.txt" not in names
    assert "dev.env" not in names


def test_get_files_adds_platform_filter(tmp_path, mocker):
    # Arrange - stub platform filter so only names containing "plat" stay
    fake_cur_platforms = ["plat1", "plat2", "plat3"]
    m_platform = mocker.patch(
        "envara.env.Env.get_cur_platforms", return_value=fake_cur_platforms
    )

    fake_all_platforms = ["plat1", "plat2", "plat3", "plat4", "plat5", "plat6"]
    m_platform = mocker.patch(
        "envara.env.Env.get_all_platforms", return_value=fake_all_platforms
    )

    # create files in temp directory
    for name in ["file.plat2.env", "file.plat4.env", "file.other.env"]:
        (tmp_path / name).write_text("")

    # Act
    result = EnvFile.get_files(tmp_path)

    # Assert - platform filter applied automatically
    assert m_platform.called
    names = [p.name for p in result]
    assert "file.plat2.env" in names
    assert "file.other.env" in names
    assert "file.plat4.env" not in names
