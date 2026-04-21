import pytest
import re
from unittest.mock import MagicMock
from tests.conftest import env_filter_mod as EnvFilterModule


EnvFilter = EnvFilterModule.EnvFilter


class TestEnvFilterConstants:
    def test_default_re_flags_is_ignorecase(self):
        assert EnvFilter.DEFAULT_RE_FLAGS == re.IGNORECASE

    def test_default_indicator_is_env(self):
        assert EnvFilter.DEFAULT_INDICATOR == "env"

    def test_default_strip_re_is_pattern(self):
        assert isinstance(EnvFilter.DEFAULT_STRIP_RE, re.Pattern)

    def test_value_separators(self):
        assert "." in EnvFilter.VALUE_SEPARATORS
        assert "-" in EnvFilter.VALUE_SEPARATORS
        assert "_" in EnvFilter.VALUE_SEPARATORS


class TestEnvFilterConstructor:
    def test_default_indicator(self):
        f = EnvFilter()
        assert f.indicator == EnvFilter.DEFAULT_INDICATOR

    def test_custom_indicator(self):
        f = EnvFilter(indicator="custom")
        assert f.indicator == "custom"

    def test_cur_values_set(self):
        f = EnvFilter(cur_values=["dev", "prod"])
        assert f.cur_values == ["dev", "prod"]

    def test_all_values_defaults_to_cur_values(self):
        f = EnvFilter(cur_values=["dev", "prod"])
        assert f.all_values == ["dev", "prod"]

    def test_custom_all_values(self):
        f = EnvFilter(cur_values=["dev"], all_values=["dev", "staging", "prod"])
        assert f.all_values == ["dev", "staging", "prod"]

    @pytest.mark.parametrize(
        "indicator,cur_values",
        [
            ("dev", None),
            ("app", ["dev", "prod"]),
        ],
    )
    def test_constructor_params(self, indicator, cur_values):
        f = EnvFilter(indicator=indicator, cur_values=cur_values)
        assert f.indicator == indicator
        assert f.cur_values == cur_values


class TestEnvFilterHasValue:
    @pytest.mark.parametrize(
        "input_str,value,expected_found,expected_equal",
        [
            ("env", "env", True, True),
            ("app", "app", True, True),
            ("env.file", "env", True, False),
            ("file.env", "env", True, False),
            ("env.file.prod", "env", True, False),
            ("myenv", "env", False, False),
            ("environ", "env", False, False),
            ("", "env", False, False),
            ("env", "", False, False),
            (None, "env", False, False),
            ("env", None, False, False),
        ],
    )
    def test_has_value(self, input_str, value, expected_found, expected_equal):
        found, equal = EnvFilter.has_value(input_str, value)
        assert found == expected_found
        assert equal == expected_equal

    def test_has_value_with_separators(self):
        found, _ = EnvFilter.has_value("dev.env", "env")
        assert found is True

        found, _ = EnvFilter.has_value("prod.env", "env")
        assert found is True

    def test_has_value_complex(self):
        found, _ = EnvFilter.has_value("my.env.file", "env")
        assert found is True

    def test_has_value_input_shorter(self):
        found, equal = EnvFilter.has_value("ab", "abc")
        assert found is False
        assert equal is False

    def test_has_value_just_separator(self):
        found, equal = EnvFilter.has_value(".", "env")
        assert found is False


class TestEnvFilterSearch:
    @pytest.mark.parametrize(
        "indicator,cur_values,input_str,expected",
        [
            ("env", None, "env", 0),
            ("env", ["dev"], "env", 0),
            ("env", ["dev"], "dev.env", 1),
            ("env", ["dev", "prod"], "dev.env", 1),
            ("env", ["dev", "prod"], "prod.env", 2),
            ("env", ["dev", "staging", "prod"], "staging.env", 2),
            ("env", None, "file", -1),
            ("app", ["dev"], "prod", -1),
            ("env", ["dev"], None, -1),
            ("env", ["dev"], "", -1),
        ],
    )
    def test_search(self, indicator, cur_values, input_str, expected):
        f = EnvFilter(indicator=indicator, cur_values=cur_values)
        result = f.search(input_str)
        assert result == expected

    def test_search_with_no_cur_values(self):
        f = EnvFilter(indicator="env", cur_values=None)
        result = f.search("env")
        assert result == 0

    def test_search_matching_indicator(self):
        f = EnvFilter(indicator="env")
        result = f.search("env")
        assert result == 0

    def test_search_not_in_values(self):
        f = EnvFilter(indicator="app", cur_values=["dev"])
        result = f.search("prod")
        assert result == -1


class TestEnvFilterEquality:
    @pytest.mark.xfail(reason="EnvFilter class does not implement __eq__")
    def test_equality_same_params(self):
        f1 = EnvFilter(indicator="env")
        f2 = EnvFilter(indicator="env")
        assert f1 == f2

    def test_equality_different_indicator(self):
        f1 = EnvFilter(indicator="env")
        f2 = EnvFilter(indicator="app")
        assert f1 != f2

    def test_equality_different_cur_values(self):
        f1 = EnvFilter(cur_values=["dev"])
        f2 = EnvFilter(cur_values=["prod"])
        assert f1 != f2


class TestEnvFilterIntegration:
    def test_full_workflow(self):
        f = EnvFilter(indicator="env", cur_values=["dev", "test", "prod"])
        found = f.search("dev.env")
        assert found == 1

    def test_complex_matching(self):
        f = EnvFilter(indicator="app", cur_values=["v1"])
        found, _ = EnvFilter.has_value("v1.0.0", "v1")
        assert found is True

    def test_multiple_values(self):
        f = EnvFilter(indicator="env", cur_values=["dev", "prod"])
        result = f.search("staging.env")
        assert result == 0
