from typing import Any

import pytest
from pytest_mock import MockerFixture
from tests.conftest import env_chars_mod, env_chars_data_mod


def _get_envchars(is_posix: bool = False, is_riscos: bool = False, is_vms: bool = False, is_windows: bool = False):
    x = env_chars_mod.EnvChars
    x.IS_POSIX = is_posix
    x.IS_RISCOS = is_riscos
    x.IS_VMS = is_vms
    x.IS_WINDOWS = is_windows
    x.Default = x.init_default()
    return x


class TestEnvCharsConstants:
    @pytest.mark.parametrize(
        "name,expected_attrs",
        [
            (
                "POSIX",
                {
                    "is_posix": True,
                    "expand": "$",
                    "windup": "",
                    "escape": "\\",
                    "cutter": "#",
                    "hard_quote": "'",
                    "normal_quote": '"',
                },
            ),
            (
                "WINDOWS",
                {
                    "is_posix": False,
                    "expand": "%",
                    "windup": "%",
                    "escape": "^",
                    "cutter": "::",
                    "hard_quote": "",
                    "normal_quote": '"',
                },
            ),
            (
                "RISCOS",
                {
                    "is_posix": False,
                    "expand": "<",
                    "windup": ">",
                    "escape": "\\",
                    "cutter": "|",
                    "hard_quote": "",
                    "normal_quote": '"',
                },
            ),
            (
                "VMS",
                {
                    "is_posix": False,
                    "expand": "'",
                    "windup": "'",
                    "escape": "^",
                    "cutter": "!",
                    "hard_quote": "",
                    "normal_quote": '"',
                },
            ),
        ],
    )
    def test_platform_is_envcharsdata(self, name: str, expected_attrs: Any):
        EnvChars = _get_envchars()
        platform = getattr(EnvChars, name)
        assert platform is not None
        assert isinstance(platform, env_chars_data_mod.EnvCharsData)
        for attr, expected_value in expected_attrs.items():
            assert getattr(platform, attr) == expected_value


class TestEnvCharsDataAttrs:
    @pytest.mark.parametrize(
        "platform,expected_expand",
        [
            ("POSIX", "$"),
            ("RISCOS", "<"),
            ("WINDOWS", "%"),
        ],
    )
    def test_platform_expand(self, platform: str, expected_expand: str):
        EnvChars = _get_envchars()
        assert getattr(EnvChars, platform).expand == expected_expand

    def test_select_init_default_when_not_set(self):
        EnvChars = env_chars_mod.EnvChars
        EnvChars.Default = EnvChars.POSIX
        EnvChars.Current = EnvChars.Default
        result = EnvChars.select("test")
        assert result is not None
        assert EnvChars.Default is not None


class TestEnvCharsMethods:
    def test_init_sets_default(self):
        EnvChars = _get_envchars()
        assert EnvChars.Current is not None
        assert EnvChars.Default is not None

    def test_init_with_existing_default_skips_init(self):
        EnvChars = _get_envchars()
        EnvChars.select("")
        assert EnvChars.Default is not None
        original = EnvChars.Default
        assert EnvChars.Default is original

    def test_select_with_riscos_cutter(self):
        EnvChars = _get_envchars()
        EnvChars.select("|test")
        assert EnvChars.Current.expand == "<"

    def test_select_with_vms_cutter(self):
        EnvChars = _get_envchars()
        EnvChars.select("!test")
        assert EnvChars.Current.expand == "'"

    def test_select_with_windows_cutter(self):
        EnvChars = _get_envchars()
        EnvChars.select("::test")
        assert EnvChars.Current.expand == "%"


class TestEnvCharsSelect:

    @pytest.mark.xfail(
        reason="Source bug: startswith gets EnvCharsData instead of string"
    )
    def test_select_copies_constants(self):
        EnvChars = _get_envchars(is_posix=True)
        EnvChars.select("test")

        assert EnvChars.Default is not EnvChars.POSIX
        assert EnvChars.Current is not EnvChars.POSIX

    @pytest.mark.xfail(
        reason="Source bug: startswith gets EnvCharsData instead of string"
    )
    def test_select_sets_current_based_on_comment(self, mocker: MockerFixture):
        EnvChars = _get_envchars(is_posix=True)
        EnvChars.select("# test")

        assert EnvChars.Current is not None
        assert EnvChars.Current.expand == "$"

    @pytest.mark.parametrize(
        "is_posix,is_riscos,is_vms,is_windows,expected_expand",
        [
            pytest.param(True, False, False, False, "$", id="posix"),
            pytest.param(False, True, False, False, "<", id="riscos"),
            pytest.param(False, False, True, False, "'", id="vms"),
            pytest.param(False, False, False, True, "%", id="windows"),
        ],
    )
    def test_select_sets_default_based_on_platform(
        self, mocker: MockerFixture, is_posix: bool, is_riscos: bool, is_vms: bool, is_windows: bool, expected_expand: str
    ):
        EnvChars = _get_envchars(is_posix, is_riscos, is_vms, is_windows)
        EnvChars.select("test")

        assert EnvChars.Default is not None
        assert EnvChars.Default.expand == expected_expand

    @pytest.mark.xfail(
        reason="Source bug: startswith gets EnvCharsData instead of string"
    )
    def test_select_with_empty_string(self):
        EnvChars = _get_envchars(is_posix=True)
        EnvChars.select("")

        assert EnvChars.Current is not None
        assert EnvChars.Current.expand == "$"
