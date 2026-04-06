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
        "", args=None, expand_flags=EnvExpandFlags.DEFAULT
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
        content, args=args, expand_flags=EnvExpandFlags.DEFAULT
    )


def test_load_reads_files_and_passes_flags(mocker):
    # Arrange - simulate get_files returning two files and read_text returning content
    fake_files = [mocker.MagicMock(spec=Path), mocker.MagicMock(spec=Path)]
    mocker.patch("envara.env_file.EnvFile.get_files", return_value=fake_files)
    m_read_text = mocker.patch("envara.env_file.EnvFile.read_text", return_value="K=V")
    m_load_from_str = mocker.patch("envara.env_file.EnvFile.load_from_str")
    m_dir = mocker.MagicMock(spec=Path)
    flags = EnvFileFlags.ADD_PLATFORMS_BEFORE

    # Act
    result = EnvFile.load(m_dir, file_flags=flags)

    # Assert
    m_read_text.assert_called_once()
    m_load_from_str.assert_called_once_with(
        "K=V", args=None, expand_flags=EnvExpandFlags.DEFAULT
    )


def test_load_from_str_uses_env_expand(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    m_expand = mocker.patch("envara.env.Env.expand", return_value="EXPANDED")
    data = "KEY=VALUE"

    # Act
    EnvFile.load_from_str(data)

    # Assert
    m_expand.assert_called_once_with("VALUE", args=None, flags=EnvExpandFlags.DEFAULT)
    assert m_environ["KEY"] == "EXPANDED"


def test_load_from_str_passes_args_and_flags(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    m_expand = mocker.patch("envara.env.Env.expand", return_value="X")
    data = "K=$1"
    args = ["a1"]
    flags = EnvExpandFlags.DEFAULT

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
    filter = EnvFilter(cur_values=["prod"], all_values=["dev", "prod"])

    # Act
    result = EnvFile.get_files(tmp_path, "env", 0, filter)

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


def test_get_files_adds_platforms_after(tmp_path, mocker):
    # Arrange
    fake_cur_platforms = ["test"]
    mocker.patch("envara.env.Env.get_cur_platforms", return_value=fake_cur_platforms)
    mocker.patch("envara.env.Env.get_all_platforms", return_value=["test"])

    for name in ["a.env", "a.test.env"]:
        (tmp_path / name).write_text("")

    # Act
    result = EnvFile.get_files(tmp_path, flags=EnvFileFlags.ADD_PLATFORMS_AFTER)

    # Assert
    names = [p.name for p in result]
    assert "a.test.env" in names


def test_get_files_multiple_filters_as_list(tmp_path, mocker):
    # Arrange
    mocker.patch("envara.env.Env.get_cur_platforms", return_value=[])
    mocker.patch("envara.env.Env.get_all_platforms", return_value=[])

    for name in ["dev.env", "prod.env", "test.env"]:
        (tmp_path / name).write_text("")

    filter1 = EnvFilter(cur_values=["dev"], all_values=["dev", "prod"])
    filter2 = EnvFilter(cur_values=["test"], all_values=["test"])

    # Act - filters are positional variadic arguments after dir, indicator, flags
    result = EnvFile.get_files(tmp_path, None, 0, filter1, filter2)

    # Assert
    names = [p.name for p in result]
    assert "dev.env" in names
    assert "test.env" in names


def test_get_files_empty_directory(tmp_path, mocker):
    # Arrange
    mocker.patch("envara.env.Env.get_cur_platforms", return_value=[])
    mocker.patch("envara.env.Env.get_all_platforms", return_value=[])

    # Act
    result = EnvFile.get_files(tmp_path)

    # Assert
    assert result == []


def test_get_files_custom_indicator(tmp_path, mocker):
    # Arrange - use explicit filter with proper indicator to test custom indicator
    mocker.patch("envara.env.Env.get_cur_platforms", return_value=[])
    mocker.patch("envara.env.Env.get_all_platforms", return_value=[])

    for name in ["app.config", "app.settings", "other.txt"]:
        (tmp_path / name).write_text("")

    # Create filter with cur_values that match files containing "app"
    filter = EnvFilter(indicator="app", cur_values=["app"], all_values=["app"])

    # Act - flags=0 to skip platform filters, filter as variadic argument
    result = EnvFile.get_files(tmp_path, "app", 0, filter)

    # Assert
    names = [p.name for p in result]
    assert "app.config" in names
    assert "app.settings" in names
    assert "other.txt" not in names


def test_load_custom_indicator(mocker):
    # Arrange
    m_get_files = mocker.patch(
        "envara.env_file.EnvFile.get_files", return_value=[]
    )
    mocker.patch("envara.env_file.EnvFile.read_text", return_value="")
    mocker.patch("envara.env_file.EnvFile.load_from_str")

    # Act
    EnvFile.load(indicator="custom")

    # Assert
    m_get_files.assert_called_once()
    args = m_get_files.call_args
    assert args[0][1] == "custom"


def test_load_with_multiple_filters(mocker):
    # Arrange
    m_get_files = mocker.patch(
        "envara.env_file.EnvFile.get_files", return_value=[]
    )
    mocker.patch("envara.env_file.EnvFile.read_text", return_value="")
    mocker.patch("envara.env_file.EnvFile.load_from_str")

    filter1 = EnvFilter(cur_values=["dev"], all_values=["dev", "prod"])

    # Act - filters are positional arguments
    EnvFile.load(filter1)

    # Assert
    m_get_files.assert_called_once()
    args = m_get_files.call_args[0]
    assert len(args) >= 3  # dir, indicator, flags, filters...


def test_load_adds_platforms_after(mocker):
    # Arrange
    mocker.patch("envara.env_file.EnvFile.get_files", return_value=[])
    mocker.patch("envara.env_file.EnvFile.read_text", return_value="")
    mocker.patch("envara.env_file.EnvFile.load_from_str")

    # Act
    EnvFile.load(file_flags=EnvFileFlags.ADD_PLATFORMS_AFTER)

    # Assert
    m_get_files = mocker.patch(
        "envara.env_file.EnvFile.get_files", return_value=[]
    )
    EnvFile.load(file_flags=EnvFileFlags.ADD_PLATFORMS_AFTER)
    args = m_get_files.call_args
    assert args[0][2] == EnvFileFlags.ADD_PLATFORMS_AFTER


def test_load_from_str_none_data(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})

    # Act - None data should be handled gracefully
    EnvFile.load_from_str(None)

    # Assert
    assert len(m_environ) == 0


def test_load_from_str_empty_data(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})

    # Act
    EnvFile.load_from_str("")

    # Assert
    assert len(m_environ) == 0


def test_load_from_str_multiline_data(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    mocker.patch("envara.env.Env.expand", side_effect=lambda x, **k: x)

    data = "KEY1=val1\nKEY2=val2\nKEY3=val3"

    # Act
    EnvFile.load_from_str(data)

    # Assert
    assert m_environ["KEY1"] == "val1"
    assert m_environ["KEY2"] == "val2"
    assert m_environ["KEY3"] == "val3"


def test_load_from_str_removes_key_with_empty_value(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {"KEY": "old_value"})
    mocker.patch("envara.env.Env.expand", return_value="")

    # Act
    EnvFile.load_from_str("KEY=")

    # Assert
    assert "KEY" not in m_environ


def test_load_from_str_preserves_key_with_empty_value_when_not_in_environ(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})

    # Act
    EnvFile.load_from_str("KEY=")

    # Assert
    assert "KEY" not in m_environ


def test_load_from_str_crlf_handling(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    mocker.patch("envara.env.Env.expand", side_effect=lambda x, **k: x)

    data = "KEY1=val1\r\nKEY2=val2\rKEY3=val3"

    # Act
    EnvFile.load_from_str(data)

    # Assert
    assert m_environ["KEY1"] == "val1"
    assert m_environ["KEY2"] == "val2"
    assert m_environ["KEY3"] == "val3"


def test_load_from_str_skips_lines_without_equals(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    mocker.patch("envara.env.Env.expand", side_effect=lambda x, **k: x)

    data = "KEY=VALUE\njust a comment\nANOTHER=value"

    # Act
    EnvFile.load_from_str(data)

    # Assert
    assert "KEY" in m_environ
    assert "just a comment" not in m_environ
    assert "ANOTHER" in m_environ


def test_load_from_str_expands_value(mocker):
    # Arrange
    m_environ = mocker.patch("os.environ", {})
    mocker.patch("envara.env.Env.expand", return_value="EXPANDED")

    # Act
    EnvFile.load_from_str("KEY=original")

    # Assert
    assert m_environ["KEY"] == "EXPANDED"


def test_read_text_empty_list():
    # Arrange
    EnvFile._loaded = []

    # Act
    result = EnvFile.read_text([], flags=0)

    # Assert
    assert result == ""


def test_re_key_value_split():
    # Test the regex pattern for splitting key=value pairs
    result = EnvFile.RE_KEY_VALUE.split("KEY=VALUE", maxsplit=1)
    assert result == ["KEY", "VALUE"]

    result = EnvFile.RE_KEY_VALUE.split("  KEY  =  VALUE  ", maxsplit=1)
    assert result == ["  KEY", "VALUE  "]

    result = EnvFile.RE_KEY_VALUE.split("KEY=", maxsplit=1)
    assert result == ["KEY", ""]

    result = EnvFile.RE_KEY_VALUE.split("=VALUE", maxsplit=1)
    assert result == ["", "VALUE"]

    result = EnvFile.RE_KEY_VALUE.split("A=B=C", maxsplit=1)
    assert result == ["A", "B=C"]


def test_get_files_with_filters_as_list_in_variadic(tmp_path, mocker):
    # Arrange - test passing a list of filters as a single variadic argument
    # This exercises the filters_ex.extend(filter) code path at line 98
    mocker.patch("envara.env.Env.get_cur_platforms", return_value=[])
    mocker.patch("envara.env.Env.get_all_platforms", return_value=[])

    for name in ["dev.env", "prod.env", "test.env"]:
        (tmp_path / name).write_text("")

    filter_list = [
        EnvFilter(cur_values=["dev"], all_values=["dev", "prod", "test"]),
    ]

    # Act - pass list as a variadic argument (triggers filters_ex.extend(filter))
    # indicator=None means indicator check passes
    result = EnvFile.get_files(tmp_path, None, 0, filter_list)

    # Assert - file should be matched since cur_values includes "dev" and file is "dev.env"
    names = [p.name for p in result]
    assert "dev.env" in names


def test_get_files_no_platform_flags_no_filters_adds_default(tmp_path, mocker):
    # Arrange - verify default filter is added when no filters provided (line 117)
    # flags=0 means no platform filters are added
    mocker.patch("envara.env.Env.get_cur_platforms", return_value=[])
    mocker.patch("envara.env.Env.get_all_platforms", return_value=[])

    for name in ["file.env"]:
        (tmp_path / name).write_text("")

    # Act - no filters, no platform filters (flags=0)
    # The default EnvFilter() with indicator=None excludes everything (search returns -1)
    result = EnvFile.get_files(tmp_path, None, 0)

    # Assert - result is empty because default filter with indicator=None excludes all
    assert result == []
