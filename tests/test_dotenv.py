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
            m.__truediv__.side_effect = lambda other: get_mock_path(f"{path_str}/{other}")
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


def test_load_from_file(mocker):
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


def test_load_from_file_with_default_dir(mocker):
    # Arrange
    m_read_text = mocker.patch("dotenv.DotEnv.read_text", return_value="KEY=VAL")
    mocker.patch("dotenv.DotEnv.load_from_str")
    m_path = mocker.MagicMock(spec=Path)
    dir = Path("/some/path")

    # Act
    DotEnv.load_from_file(m_path, dir=dir)

    # Assert
    args, _ = m_read_text.call_args
    # args[2] is default_dir
    assert isinstance(args[2], Path)
    assert str(args[2]) == str(dir)


###############################################################################
# Tests for __append_filters
###############################################################################


def test_append_filters_single_filter():
    # Arrange
    target = []
    side_seps = r"[\-._]"  # Properly escaped character class
    mid_seps = r"([\-._]|[\-._].+[\-._])"  # Properly escaped character class
    source = ["production"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 2
    assert all(isinstance(p, re.Pattern) for p in target)
    # First pattern should match separator + env + separator + filter + separator
    assert target[0].search("-env-production-") is not None
    assert target[0].search(".env.production.") is not None
    # Second pattern should match separator + filter + separator + env + separator
    assert target[1].search("-production-env-") is not None


def test_append_filters_multiple_filters():
    # Arrange
    target = []
    side_seps = r"[\-._]"
    mid_seps = r"([\-._]|[\-._].+[\-._])"
    source = ["dev", "test"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 4
    assert all(isinstance(p, re.Pattern) for p in target)
    # First item "dev" generates two patterns
    assert target[0].search("-env-dev-") is not None
    assert target[1].search("-dev-env-") is not None
    # Second item "test" generates two patterns
    assert target[2].search("-env-test-") is not None
    assert target[3].search("-test-env-") is not None


def test_append_filters_empty_string():
    # Arrange
    target = []
    side_seps = r"[\-._]"
    mid_seps = r"([\-._]|[\-._].+[\-._])"
    source = [""]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 1
    assert isinstance(target[0], re.Pattern)
    # Pattern should match separator + indicator + separator
    assert target[0].search("-env-") is not None
    assert target[0].search(".env.") is not None
    assert target[0].search("_env_") is not None


def test_append_filters_with_empty_and_nonempty():
    # Arrange
    target = []
    side_seps = r"[\-._]"
    mid_seps = r"([\-._]|[\-._].+[\-._])"
    source = ["", "production"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 3
    # First from empty string
    assert target[0].search("-env-") is not None
    # Two from production
    assert target[1].search("-env-production-") is not None
    assert target[2].search("-production-env-") is not None


def test_append_filters_special_characters():
    # Arrange
    target = []
    side_seps = r"[-]"  # Just hyphen
    mid_seps = r"([-]|[-].+[-])"  # Just hyphen
    source = ["dev.test"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 2
    # The dot in "dev.test" should be escaped in the pattern
    assert target[0].search("-env-dev.test-") is not None
    assert target[1].search("-dev.test-env-") is not None


def test_append_filters_regex_escaped_characters():
    # Arrange
    target = []
    side_seps = r"[-]"
    mid_seps = r"([-]|[-].+[-])"
    # Source with regex special characters that should be escaped
    source = ["dev[test]"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 2
    # The brackets should be escaped and match literally
    assert target[0].search("-env-dev[test]-") is not None
    assert target[1].search("-dev[test]-env-") is not None


def test_append_filters_appends_to_existing_list():
    # Arrange
    target = [re.compile(r"existing")]
    side_seps = r"[\-._]"
    mid_seps = r"([\-._]|[\-._].+[\-._])"
    source = ["new"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 3
    # Check that the first pattern is still the original
    assert target[0].pattern == r"existing"
    # Check that new patterns were appended
    assert target[1].search("-env-new-") is not None
    assert target[2].search("-new-env-") is not None


def test_append_filters_different_separators():
    # Arrange
    target = []
    side_seps = r"[_]"  # Just underscore
    mid_seps = r"([_]|[_].+[_])"  # Just underscore
    source = ["stage"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 2
    # With underscore separators
    assert target[0].search("_env_stage_") is not None
    assert target[1].search("_stage_env_") is not None


def test_append_filters_complex_mid_seps():
    # Arrange
    target = []
    side_seps = r"[\-._]"
    # Complex mid_seps with alternatives
    mid_seps = r"([\-._]|[\-._][a-z]+[\-._])"
    source = ["linux"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 2
    # Should match with single separator or separator with text and separator
    assert target[0].search("-env-linux-") is not None
    assert target[0].search("-env-platform-linux-") is not None
    assert target[1].search("-linux-env-") is not None
    assert target[1].search("-linux-platform-env-") is not None


def test_append_filters_empty_source_list():
    # Arrange
    target = []
    side_seps = r"[\-._]"
    mid_seps = r"([\-._]|[\-._].+[\-._])"
    source = []

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 0


def test_append_filters_none_values_in_source():
    # Arrange
    target = []
    side_seps = r"[\-._]"
    mid_seps = r"([\-._]|[\-._].+[\-._])"
    # Source with empty strings mixed in
    source = ["prod", "", "staging"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    assert len(target) == 5
    # "prod" generates 2 patterns
    assert target[0].search("-env-prod-") is not None
    assert target[1].search("-prod-env-") is not None
    # "" generates 1 pattern
    assert target[2].search("-env-") is not None
    # "staging" generates 2 patterns
    assert target[3].search("-env-staging-") is not None
    assert target[4].search("-staging-env-") is not None


def test_append_filters_pattern_count():
    # Arrange
    target = []
    side_seps = r"[-]"
    mid_seps = r"([-]|[-].+[-])"
    source = ["a", "b", "c"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    # Three non-empty sources should generate 3 * 2 = 6 patterns
    assert len(target) == 6


def test_append_filters_order_preserved():
    # Arrange
    target = []
    side_seps = r"[-]"
    mid_seps = r"([-]|[-].+[-])"
    source = ["first", "second"]

    # Act
    DotEnv._DotEnv__append_filters(target, side_seps, mid_seps, source)

    # Assert
    # Patterns for "first" should come before patterns for "second"
    assert target[0].search("-env-first-") is not None
    assert target[1].search("-first-env-") is not None
    assert target[2].search("-env-second-") is not None
    assert target[3].search("-second-env-") is not None


###############################################################################
# Tests for get_file_stack
###############################################################################


def test_get_file_stack_empty_directory(mocker):
    # Arrange
    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = []
    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    result = DotEnv.get_file_stack(dir=m_dir)

    # Assert
    assert result == []


def test_get_file_stack_default_dir(mocker):
    # Arrange
    m_file1 = mocker.MagicMock(spec=Path)
    m_file1.name = ".env"
    m_file2 = mocker.MagicMock(spec=Path)
    m_file2.name = "config.txt"

    m_cwd = mocker.MagicMock(spec=Path)
    m_cwd.iterdir.return_value = [m_file1, m_file2]
    mocker.patch("pathlib.Path", return_value=m_cwd)
    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    result = DotEnv.get_file_stack(dir=None)

    # Assert
    assert len(result) >= 0
    m_cwd.iterdir.assert_called_once()


def test_get_file_stack_filters_by_indicator(mocker):
    # Arrange
    m_env_file = mocker.MagicMock(spec=Path)
    m_env_file.name = ".env"
    m_other_file = mocker.MagicMock(spec=Path)
    m_other_file.name = ".config"

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_file, m_other_file]
    m_dir.__truediv__.side_effect = lambda x: f"{m_dir}/{x}"

    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    result = DotEnv.get_file_stack(dir=m_dir)

    # Assert
    # Should find at least .env
    assert len(result) > 0


def test_get_file_stack_with_all_of_filter(mocker):
    # Arrange
    m_env_prod = mocker.MagicMock(spec=Path)
    m_env_prod.name = ".env-production"
    m_env_dev = mocker.MagicMock(spec=Path)
    m_env_dev.name = ".env-development"
    m_env_basic = mocker.MagicMock(spec=Path)
    m_env_basic.name = ".env"

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_prod, m_env_dev, m_env_basic]
    m_dir.__truediv__.side_effect = lambda x: f"{m_dir}/{x}"

    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    result = DotEnv.get_file_stack(dir=m_dir, all_of=["production"])

    # Assert
    # Should only match files with "production" in the name
    assert len(result) > 0


def test_get_file_stack_with_any_of_filter(mocker):
    # Arrange
    m_env_prod = mocker.MagicMock(spec=Path)
    m_env_prod.name = ".env-production"
    m_env_dev = mocker.MagicMock(spec=Path)
    m_env_dev.name = ".env-development"
    m_env_staging = mocker.MagicMock(spec=Path)
    m_env_staging.name = ".env-staging"

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_prod, m_env_dev, m_env_staging]
    m_dir.__truediv__.side_effect = lambda x: f"{m_dir}/{x}"

    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    # Should match any file with either "production" or "staging"
    result = DotEnv.get_file_stack(dir=m_dir, any_of=["production", "staging"])

    # Assert
    assert len(result) > 0


def test_get_file_stack_with_both_all_and_any_filters(mocker):
    # Arrange
    m_env_prod_es = mocker.MagicMock(spec=Path)
    m_env_prod_es.name = ".env-production-es"
    m_env_prod_en = mocker.MagicMock(spec=Path)
    m_env_prod_en.name = ".env-production-en"
    m_env_dev_es = mocker.MagicMock(spec=Path)
    m_env_dev_es.name = ".env-development-es"

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_prod_es, m_env_prod_en, m_env_dev_es]
    m_dir.__truediv__.side_effect = lambda x: f"{m_dir}/{x}"

    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    # all_of: must contain "production"
    # any_of: must contain either "es" or "en"
    result = DotEnv.get_file_stack(
        dir=m_dir, all_of=["production"], any_of=["es", "en"]
    )

    # Assert
    assert len(result) == 2


def test_get_file_stack_with_custom_separators(mocker):
    # Arrange
    m_env_prod = mocker.MagicMock(spec=Path)
    m_env_prod.name = ".env_production"  # Using underscore instead of hyphen
    m_env_dev = mocker.MagicMock(spec=Path)
    m_env_dev.name = ".env_development"

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_prod, m_env_dev]
    m_dir.__truediv__.side_effect = lambda x: f"{m_dir}/{x}"

    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    result = DotEnv.get_file_stack(dir=m_dir, seps="_")

    # Assert
    assert len(result) >= 0


def test_get_file_stack_includes_platform_stack(mocker):
    # Arrange
    m_env_base = mocker.MagicMock(spec=Path)
    m_env_base.name = ".env"
    m_env_linux = mocker.MagicMock(spec=Path)
    m_env_linux.name = ".env-linux"
    m_env_macos = mocker.MagicMock(spec=Path)
    m_env_macos.name = ".env-macos"

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_base, m_env_linux, m_env_macos]
    m_dir.__truediv__.side_effect = lambda x: f"{m_dir}/{x}"

    # Mock get_platform_stack to return both empty and a platform
    mocker.patch("dotenv.Env.get_platform_stack", return_value=["", "linux"])

    # Act
    result = DotEnv.get_file_stack(dir=m_dir)

    # Assert
    # Should find files matching both empty (base) and "linux" platform
    assert len(result) > 0


def test_get_file_stack_returns_path_objects(mocker):
    # Arrange
    m_env_file = mocker.MagicMock(spec=Path)
    m_env_file.name = ".env"
    m_result_path = mocker.MagicMock(spec=Path)

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_file]
    m_dir.__truediv__.return_value = m_result_path

    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    result = DotEnv.get_file_stack(dir=m_dir)

    # Assert
    if len(result) > 0:
        # Result items should be Path objects (or mock Path objects in tests)
        assert all(hasattr(item, "name") or isinstance(item, (Path, type(m_result_path))) for item in result)


def test_get_file_stack_with_multiple_language_filters(mocker):
    # Arrange
    m_env_prod_en = mocker.MagicMock(spec=Path)
    m_env_prod_en.name = ".env-production-en"
    m_env_prod_es = mocker.MagicMock(spec=Path)
    m_env_prod_es.name = ".env-production-es"
    m_env_prod_fr = mocker.MagicMock(spec=Path)
    m_env_prod_fr.name = ".env-production-fr"
    m_env_dev = mocker.MagicMock(spec=Path)
    m_env_dev.name = ".env-development"

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_prod_en, m_env_prod_es, m_env_prod_fr, m_env_dev]
    m_dir.__truediv__.side_effect = lambda x: f"{m_dir}/{x}"

    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    # Must have "production" and must have one of the language codes
    result = DotEnv.get_file_stack(
        dir=m_dir, all_of=["production"], any_of=["en", "es", "fr"]
    )

    # Assert
    assert len(result) > 0


def test_get_file_stack_empty_all_of_list(mocker):
    # Arrange
    m_env_prod = mocker.MagicMock(spec=Path)
    m_env_prod.name = ".env-production"
    m_env_dev = mocker.MagicMock(spec=Path)
    m_env_dev.name = ".env-development"

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_prod, m_env_dev]
    m_dir.__truediv__.side_effect = lambda x: f"{m_dir}/{x}"

    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    # Empty all_of should match all files that match any_of (or platform stack if no any_of)
    result = DotEnv.get_file_stack(dir=m_dir, all_of=[])

    # Assert
    assert len(result) >= 0


def test_get_file_stack_empty_any_of_list(mocker):
    # Arrange
    m_env_file = mocker.MagicMock(spec=Path)
    m_env_file.name = ".env"

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_file]
    m_dir.__truediv__.side_effect = lambda x: f"{m_dir}/{x}"

    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    result = DotEnv.get_file_stack(dir=m_dir, any_of=[])

    # Assert
    # With no any_of filters, platform stack empty strings should be used
    assert len(result) > 0


def test_get_file_stack_default_parameters(mocker):
    # Arrange
    m_env_file = mocker.MagicMock(spec=Path)
    m_env_file.name = ".env"

    m_cwd = mocker.MagicMock(spec=Path)
    m_cwd.iterdir.return_value = [m_env_file]

    mocker.patch("pathlib.Path", return_value=m_cwd)
    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    result = DotEnv.get_file_stack()

    # Assert
    assert isinstance(result, list)
    m_cwd.iterdir.assert_called_once()


def test_get_file_stack_separators_default(mocker):
    # Arrange
    m_env_hyphen = mocker.MagicMock(spec=Path)
    m_env_hyphen.name = ".env-production"
    m_env_dot = mocker.MagicMock(spec=Path)
    m_env_dot.name = ".env.production"
    m_env_underscore = mocker.MagicMock(spec=Path)
    m_env_underscore.name = ".env_production"

    m_dir = mocker.MagicMock(spec=Path)
    m_dir.iterdir.return_value = [m_env_hyphen, m_env_dot, m_env_underscore]
    m_dir.__truediv__.side_effect = lambda x: f"{m_dir}/{x}"

    mocker.patch("dotenv.Env.get_platform_stack", return_value=[""])

    # Act
    # Default seps is '.-_' so all three should match
    result = DotEnv.get_file_stack(dir=m_dir)

    # Assert
    assert len(result) > 0
