import pytest
from tests.conftest import env_chars_data_mod


def _make_envcharsdata(**kwargs):
    kwargs.setdefault("normal_quote", "")
    return env_chars_data_mod.EnvCharsData(**kwargs)


class TestEnvCharsDataConstructor:
    @pytest.mark.parametrize(
        "field,value",
        [
            ("expand", "$"),
            ("windup", ">"),
            ("escape", "\\"),
            ("cutter", "#"),
            ("hard_quote", "'"),
            ("normal_quote", '"'),
        ],
    )
    def test_constructor_all_fields(self, field, value):
        info = _make_envcharsdata(**{field: value})
        assert getattr(info, field) == value

    def test_constructor_defaults(self):
        info = _make_envcharsdata()

        assert info.expand == ""
        assert info.windup == ""
        assert info.escape == ""
        assert info.cutter == ""
        assert info.hard_quote == ""
        assert info.normal_quote == ""
        assert info.all_quotes == ""
        assert info.all_quotes_len == 0
        assert info.hard_quote_len == 0
        assert info.normal_quote_len == 0

    @pytest.mark.parametrize(
        "field,value,expected_len",
        [
            ("expand", "$", 1),
            ("windup", ">", 1),
            ("escape", "\\", 1),
            ("cutter", "#", 1),
            ("hard_quote", "'", 1),
            ("normal_quote", '"', 1),
        ],
    )
    def test_constructor_lengths_set(self, field, value, expected_len):
        info = _make_envcharsdata(**{field: value})
        assert getattr(info, f"{field}_len") == expected_len

    @pytest.mark.parametrize(
        "field",
        ["expand", "windup", "escape", "cutter", "hard_quote", "normal_quote"],
    )
    def test_constructor_lengths_zero_for_empty(self, field):
        info = _make_envcharsdata()
        assert getattr(info, f"{field}_len") == 0


class TestEnvCharsDataEquality:
    @pytest.mark.parametrize(
        "field,val1,val2",
        [
            ("expand", "$", "%"),
            ("windup", "", ">"),
            ("escape", "\\", "^"),
            ("cutter", "#", "::"),
            ("hard_quote", "'", ""),
            ("normal_quote", '"', ""),
        ],
    )
    def test_eq_different_single_field(self, field, val1, val2):
        info1 = _make_envcharsdata(**{field: val1})
        info2 = _make_envcharsdata(**{field: val2})
        assert info1 != info2

    def test_eq_equal_objects(self):
        info1 = _make_envcharsdata(
            expand="$",
            windup="",
            escape="\\",
            cutter="#",
            hard_quote="'",
            normal_quote='"',
        )
        info2 = _make_envcharsdata(
            expand="$",
            windup="",
            escape="\\",
            cutter="#",
            hard_quote="'",
            normal_quote='"',
        )
        assert info1 == info2

    def test_eq_with_none(self):
        pass

    def test_eq_with_different_type(self):
        pass

    def test_eq_all_attributes_differ(self):
        info1 = _make_envcharsdata(
            expand="$",
            windup="",
            escape="\\",
            cutter="#",
            hard_quote="'",
            normal_quote='"',
        )
        info2 = _make_envcharsdata(
            expand="%",
            windup=">",
            escape="^",
            cutter="::",
            hard_quote="",
            normal_quote="",
        )
        assert info1 != info2


class TestEnvCharsDataCopyWith:
    @pytest.mark.parametrize(
        "field,val1,val2",
        [
            ("expand", "$", "%"),
            ("windup", "", ">"),
            ("escape", "\\", "^"),
            ("cutter", "#", "::"),
            ("hard_quote", "'", ""),
            ("normal_quote", '"', ""),
        ],
    )
    def test_copy_with_single_field_changed(self, field, val1, val2):
        src = _make_envcharsdata(**{field: val1})
        result = src.copy_with(**{field: val2})
        assert getattr(result, field) == val2

    def test_copy_with_no_changes(self):
        src = _make_envcharsdata(
            expand="$",
            windup=">",
            escape="\\",
            cutter="#",
            hard_quote="'",
            normal_quote='"',
        )

        result = src.copy_with()

        assert result.expand == "$"
        assert result.windup == ">"
        assert result.escape == "\\"
        assert result.cutter == "#"
        assert result.hard_quote == "'"
        assert result.normal_quote == '"'

    def test_copy_with_multiple_changes(self):
        src = _make_envcharsdata(
            expand="$",
            windup="",
            escape="\\",
            cutter="#",
            hard_quote="'",
            normal_quote='"',
        )

        result = src.copy_with(expand="%", windup=">", escape="^")

        assert result.expand == "%"
        assert result.windup == ">"
        assert result.escape == "^"
        assert result.cutter == "#"
        assert result.hard_quote == "'"
        assert result.normal_quote == '"'

    def test_copy_with_returns_new_object(self):
        src = _make_envcharsdata(expand="$")

        result = src.copy_with()

        assert result is not src

    def test_copy_with_none_value_overrides(self):
        src = _make_envcharsdata(expand="$")

        result = src.copy_with(expand=None)

        assert result.expand == "$"


class TestEnvCharsDataAttributes:
    @pytest.mark.parametrize(
        "hard_quote,normal_quote,expected_all_quotes,expected_len",
        [
            ("'", '"', "'\"", 2),
            ("", "", "", 0),
            ("'", "", "'", 1),
            ("", '"', '"', 1),
        ],
    )
    def test_all_quotes_combinations(
        self, hard_quote, normal_quote, expected_all_quotes, expected_len
    ):
        info = _make_envcharsdata(hard_quote=hard_quote, normal_quote=normal_quote)
        assert info.all_quotes == expected_all_quotes
        assert info.all_quotes_len == expected_len
