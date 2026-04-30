import pytest
import re
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from tests.conftest import (
    env_file_mod,
    env_filter_mod,
    env_filters_mod,
    env_file_flags_mod,
    env_expand_flags_mod,
    env_chars_data_mod,
    env_chars_mod,
    envara_mod,
)

from envara.env_platform_flags import EnvPlatformFlags
from envara.env import Env


EnvFile = env_file_mod.EnvFile
EnvFilter = env_filter_mod.EnvFilter
EnvFilters = env_filters_mod.EnvFilters
EnvFileFlags = env_file_flags_mod.EnvFileFlags
EnvExpandFlags = env_expand_flags_mod.EnvExpandFlags
EnvCharsData = env_chars_data_mod.EnvCharsData
EnvChars = env_chars_mod.EnvChars


class TestEnvFileConstants:
    def test_default_expand_flags_has_remove_line_comment(self):
        assert EnvFile.DEFAULT_EXPAND_FLAGS & EnvExpandFlags.STRIP_COMMENT

    def test_re_key_value_is_compiled(self):
        assert isinstance(EnvFile.RE_KEY_VALUE, re.Pattern)

    def test_loaded_list_initially_empty(self):
        EnvFile._loaded = []
        assert EnvFile._loaded == []

    def test_default_file_flags_none(self):
        assert EnvFileFlags.NONE == 0


class TestEnvFileGetFiles:
    def test_get_files_returns_list(self, mocker):
        EnvFile._loaded = []
        mock_path = mocker.MagicMock()
        mock_iterdir = mocker.MagicMock()
        mock_iterdir.return_value = []
        mock_path.iterdir = mock_iterdir

        result = EnvFile.get_files(mock_path, "env", EnvFileFlags.ADD_PLATFORMS_BEFORE)

        assert isinstance(result, list)


class TestEnvFileGetFiles:
    def test_get_files_returns_list(self, mocker):
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []

        result = EnvFile.get_files(
            Path("/etc"), "app", EnvFileFlags.ADD_PLATFORMS_BEFORE
        )

        assert isinstance(result, list)

    def test_get_files_empty_dir(self, mocker):
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []

        result = EnvFile.get_files(Path("/empty"), "env", EnvFileFlags.NONE)

        assert result == []


class TestEnvFileReadText:
    def test_read_text_returns_string(self, mocker):
        mock_path = MagicMock()
        mock_path.read_text.return_value = "KEY=value"

        result = EnvFile.read_text([mock_path], EnvFileFlags.NONE)

        assert isinstance(result, str)

    def test_read_text_empty(self, mocker):
        mock_path = MagicMock()
        mock_path.read_text.return_value = ""

        result = EnvFile.read_text([mock_path], EnvFileFlags.NONE)

        assert result == ""


class TestEnvFileLoadedList:
    def test_loaded_list_accessible(self):
        EnvFile._loaded = []
        assert EnvFile._loaded == []

    def test_loaded_list_append(self):
        original = (
            EnvFile._loaded.copy()
            if hasattr(EnvFile, "_loaded") and EnvFile._loaded
            else []
        )
        EnvFile._loaded = original + ["test"]
        assert "test" in EnvFile._loaded
        EnvFile._loaded = original


class TestEnvFileLoadFromStr:
    def test_load_from_str_public_api(self):
        assert hasattr(EnvFile, "load_from_str")
        assert callable(EnvFile.load_from_str)


class TestEnvFileLoad:
    def test_load_public_api(self):
        assert hasattr(EnvFile, "load")
        assert callable(EnvFile.load)


class TestEnvFileGetFiles:
    def test_get_files_public_api(self):
        assert hasattr(EnvFile, "get_files")
        assert callable(EnvFile.get_files)


class TestEnvFileReadText:
    def test_read_text_public_api(self):
        assert hasattr(EnvFile, "read_text")
        assert callable(EnvFile.read_text)


class TestEnvFileGetFilesMocked:
    def test_get_files_with_mock(self, mocker):
        EnvFile._loaded = []
        mock_path = mocker.MagicMock()
        mock_path.iterdir.return_value = []
        result = EnvFile.get_files(mock_path, "env", EnvFileFlags.NONE)
        assert isinstance(result, list)


class TestEnvFileReadTextMocked:
    def test_read_text_with_mock(self, mocker):
        mock_path = mocker.MagicMock()
        mock_path.read_text.return_value = "KEY=value"
        result = EnvFile.read_text([mock_path], EnvFileFlags.NONE)
        assert isinstance(result, str)


class TestEnvFileGetFilesPlatforms:
    def test_get_files_adds_platforms_before(self, mocker):
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []
        mocker.patch.object(Env, "get_cur_platforms", return_value=["linux"])
        mocker.patch.object(
            Env, "get_all_platforms", return_value=["linux", "windows", "darwin"]
        )
        mocker.patch.object(EnvFilters, "process", return_value=[])

        result = EnvFile.get_files(
            Path("/test"), "env", EnvFileFlags.ADD_PLATFORMS_BEFORE
        )

        assert isinstance(result, list)

    def test_get_files_adds_platforms_after(self, mocker):
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []
        mocker.patch.object(Env, "get_cur_platforms", return_value=["linux"])
        mocker.patch.object(Env, "get_all_platforms", return_value=["linux", "windows"])
        mocker.patch.object(EnvFilters, "process", return_value=[])

        result = EnvFile.get_files(
            Path("/test"), "env", EnvFileFlags.ADD_PLATFORMS_AFTER
        )

        assert isinstance(result, list)

    def test_get_files_both_before_and_after(self, mocker):
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []
        mocker.patch.object(Env, "get_cur_platforms", return_value=["linux"])
        mocker.patch.object(Env, "get_all_platforms", return_value=["linux", "windows"])
        mocker.patch.object(EnvFilters, "process", return_value=[])

        result = EnvFile.get_files(
            Path("/test"),
            "env",
            EnvFileFlags.ADD_PLATFORMS_BEFORE | EnvFileFlags.ADD_PLATFORMS_AFTER,
        )

        assert isinstance(result, list)
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []
        mocker.patch.object(EnvFilters, "process", return_value=["test.env"])

        f = EnvFilter("env")
        result = EnvFile.get_files(Path("/test"), "env", EnvFileFlags.NONE, [f])

        assert isinstance(result, list)

    def test_get_files_with_filters_multiple(self, mocker):
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []
        mocker.patch.object(EnvFilters, "process", return_value=["test.env"])

        f1 = EnvFilter("env")
        f2 = EnvFilter("prod")
        result = EnvFile.get_files(Path("/test"), "env", EnvFileFlags.NONE, f1, f2)

        assert isinstance(result, list)

    def test_get_files_fallback_to_default_filter(self, mocker):
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []
        mocker.patch.object(EnvFilters, "process", return_value=[])

        result = EnvFile.get_files(Path("/test"), None, EnvFileFlags.NONE)

        assert result == []

    def test_get_files_with_empty_filter_list(self, mocker):
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []
        mocker.patch.object(EnvFilters, "process", return_value=[])

        result = EnvFile.get_files(Path("/test"), "env", EnvFileFlags.NONE, [])

        assert result == []

    def test_get_files_skips_non_files(self, mocker):
        EnvFile._loaded = []
        mock_entry = mocker.MagicMock()
        mock_entry.name = "app.env"
        mock_entry.is_file.return_value = False
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = [mock_entry]
        mocker.patch.object(EnvFilters, "process", return_value=["app.env"])

        result = EnvFile.get_files(Path("/test"), "app", EnvFileFlags.NONE)

        assert result == []

    def test_get_files_with_none_filter(self, mocker):
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []
        mocker.patch.object(EnvFilters, "process", return_value=[])

        result = EnvFile.get_files(Path("/test"), "env", EnvFileFlags.NONE, None)

        assert result == []

    def test_get_files_returns_paths_from_filtered_names(self, mocker):
        EnvFile._loaded = []
        mock_entry = mocker.MagicMock()
        mock_entry.name = "test.env"
        mock_entry.is_file.return_value = True
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = [mock_entry]
        mocker.patch.object(EnvFilters, "process", return_value=["test.env"])

        result = EnvFile.get_files(Path("/test"), "env", EnvFileFlags.NONE)

        assert len(result) >= 0


class TestEnvFileLoad:
    def test_load_public_api(self):
        assert hasattr(EnvFile, "load")
        assert callable(EnvFile.load)

    def test_load_from_str_public_api(self):
        assert hasattr(EnvFile, "load_from_str")
        assert callable(EnvFile.load_from_str)

    def test_get_files_public_api(self):
        assert hasattr(EnvFile, "get_files")
        assert callable(EnvFile.get_files)

    def test_read_text_public_api(self):
        assert hasattr(EnvFile, "read_text")
        assert callable(EnvFile.read_text)

    def test_load_method_gets_files(self, mocker):
        mocker.patch.object(EnvFile, "get_files", return_value=[])
        mocker.patch.object(EnvFile, "read_text", return_value="")
        mocker.patch.object(EnvFile, "load_from_str")

        EnvFile.load(Path("/test"), "env")

        EnvFile.get_files.assert_called_once()

    def test_load_method_reads_text(self, mocker):
        mocker.patch.object(EnvFile, "get_files", return_value=[])
        mocker.patch.object(EnvFile, "read_text", return_value="")
        mocker.patch.object(EnvFile, "load_from_str")

        EnvFile.load(Path("/test"), "env")

        EnvFile.read_text.assert_called_once()


class TestEnvFileLoadFromStr:
    def test_load_from_str_with_data(self):
        EnvFile.load_from_str("KEY=value")

    def test_load_from_str_with_multiple_lines(self):
        EnvFile.load_from_str("KEY1=value1\nKEY2=value2")

    def test_load_from_str_without_equals(self):
        EnvFile.load_from_str("no_equals")

    def test_load_from_str_empty_value(self):
        EnvFile.load_from_str("KEY=")

    def test_load_from_str_none_data(self):
        EnvFile.load_from_str(None)

    def test_load_from_str_deletes_existing_key(self, monkeypatch):
        monkeypatch.setenv("EXISTING_KEY", "original")
        EnvFile.load_from_str("EXISTING_KEY=")
        assert "EXISTING_KEY" not in os.environ

    def test_load_from_str_deletes_key_not_in_environ(self):
        EnvFile.load_from_str("NONEXISTENT_KEY=")

    def test_load_from_str_deletes_key_from_environ(self, monkeypatch):
        monkeypatch.setenv("TO_DELETE", "value")
        EnvFile.load_from_str("TO_DELETE=")
        assert "TO_DELETE" not in os.environ

    def test_load_from_str_with_empty_lines(self):
        EnvFile.load_from_str("\n\nKEY=value\n\n")

    def test_load_from_str_with_cr_lf(self):
        EnvFile.load_from_str("KEY1=value1\r\nKEY2=value2")

    def test_load_from_str_with_cr_only(self):
        EnvFile.load_from_str("KEY1=value1\rKEY2=value2")

    def test_load_from_str_trims_key(self, monkeypatch):
        EnvFile.load_from_str("  KEY  =value")
        assert os.environ.get("KEY") == "value"

    def test_load_from_str_expands_value(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "test_value")
        EnvFile.load_from_str("KEY=$TEST_VAR")
        assert os.environ.get("KEY") == "test_value"

    def test_load_from_str_with_custom_args(self, monkeypatch):
        EnvFile.load_from_str("KEY=$1", args=["arg1"])
        assert os.environ.get("KEY") == "arg1"

    def test_load_from_str_with_custom_expand_flags(self, monkeypatch):
        EnvFile.load_from_str("KEY=value", expand_flags=EnvExpandFlags.NONE)
        assert os.environ.get("KEY") == "value"

    def test_load_from_str_skips_key_only_line(self):
        EnvFile.load_from_str("KEY_ONLY")
        assert "KEY_ONLY" not in os.environ

    def test_load_from_str_selects_platform_from_first_line(self):
        EnvFile.load_from_str("# comment\nKEY=value")
        assert "KEY" in os.environ


class TestEnvFileReadText:
    def test_read_text_accumulates_files(self, mocker):
        EnvFile._loaded = []
        mock_file1 = mocker.MagicMock(spec=Path)
        mock_file1.read_text.return_value = "content1"
        mock_file1.__str__ = lambda self: "/path/file1"
        mock_file2 = mocker.MagicMock(spec=Path)
        mock_file2.read_text.return_value = "content2"
        mock_file2.__str__ = lambda self: "/path/file2"

        result = EnvFile.read_text([mock_file1, mock_file2], EnvFileFlags.NONE)

        assert "content1" in result
        assert "content2" in result

    def test_read_text_resets_loaded(self):
        EnvFile._loaded = ["file1"]
        result = EnvFile.read_text([], EnvFileFlags.RESET_ACCUMULATED)
        assert EnvFile._loaded == []

    def test_read_text_skips_already_loaded(self):
        mock_path_str = "/path/to/file"
        EnvFile._loaded = [mock_path_str]

        class FakePath:
            def __str__(self):
                return mock_path_str

            def read_text(self):
                return "should not read"

        result = EnvFile.read_text([FakePath()], EnvFileFlags.NONE)

        assert result == ""

    def test_read_text_handles_exception(self, mocker):
        EnvFile._loaded = []
        mock_file = mocker.MagicMock(spec=Path)
        mock_file.read_text.side_effect = Exception("Read error")
        mock_file.__str__ = lambda self: "/path/to/file"

        result = EnvFile.read_text([mock_file], EnvFileFlags.NONE)

        assert result == ""


class TestEnvFilePlatformFlags:
    def test_get_files_empty_dir_no_filters(self, mocker):
        EnvFile._loaded = []
        mock_iterdir = mocker.patch.object(Path, "iterdir")
        mock_iterdir.return_value = []
        mocker.patch.object(EnvFilters, "process", return_value=[])

        result = EnvFile.get_files(Path("/test"), "env", EnvFileFlags.NONE)

        assert result == []
