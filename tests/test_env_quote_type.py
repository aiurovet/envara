import pytest
import types
from pathlib import Path
from enum import IntEnum

project_dir = Path(__file__).parent.parent
src_dir = project_dir / "src"

env_quote_type_mod = types.ModuleType("envara.env_quote_type")
env_quote_type_file = src_dir / "envara" / "env_quote_type.py"
with open(env_quote_type_file) as f:
    code = compile(f.read(), "env_quote_type.py", "exec")
    exec(code, env_quote_type_mod.__dict__)

EnvQuoteType = env_quote_type_mod.EnvQuoteType


class TestEnvQuoteTypeValues:
    @pytest.mark.parametrize(
        "member,expected_value",
        [
            ("NONE", 0),
            ("HARD", 1),
            ("NORMAL", 2),
            ("DEFAULT", 2),
        ],
    )
    def test_enum_values(self, member, expected_value):
        assert getattr(EnvQuoteType, member).value == expected_value

    def test_default_equals_normal(self):
        assert EnvQuoteType.DEFAULT == EnvQuoteType.NORMAL


class TestEnvQuoteTypeIsIntEnum:
    def test_is_intenum(self):
        assert issubclass(EnvQuoteType, IntEnum)


class TestEnvQuoteTypeNone:
    def test_none_is_zero(self):
        assert EnvQuoteType.NONE == 0
        assert EnvQuoteType.NONE.value == 0

    def test_none_not_hard(self):
        assert EnvQuoteType.NONE != EnvQuoteType.HARD

    def test_none_not_normal(self):
        assert EnvQuoteType.NONE != EnvQuoteType.NORMAL


class TestEnvQuoteTypeRelationships:
    @pytest.mark.parametrize(
        "member1,member2,expected",
        [
            ("NONE", "NONE", True),
            ("HARD", "HARD", True),
            ("NORMAL", "NORMAL", True),
            ("NONE", "HARD", False),
            ("NONE", "NORMAL", False),
            ("HARD", "NORMAL", False),
            ("DEFAULT", "NORMAL", True),
            ("DEFAULT", "HARD", False),
        ],
    )
    def test_enum_equality(self, member1, member2, expected):
        m1 = getattr(EnvQuoteType, member1)
        m2 = getattr(EnvQuoteType, member2)
        assert (m1 == m2) == expected

    @pytest.mark.parametrize(
        "member,int_value",
        [
            ("NONE", 0),
            ("HARD", 1),
            ("NORMAL", 2),
            ("DEFAULT", 2),
        ],
    )
    def test_enum_equals_int(self, member, int_value):
        assert getattr(EnvQuoteType, member) == int_value


class TestEnvQuoteTypeIdentity:
    @pytest.mark.parametrize(
        "member",
        ["NONE", "HARD", "NORMAL", "DEFAULT"],
    )
    def test_enum_members_are_singleton(self, member):
        m1 = getattr(EnvQuoteType, member)
        m2 = getattr(EnvQuoteType, member)
        assert m1 is m2


class TestEnvQuoteTypeOrdering:
    @pytest.mark.parametrize(
        "member1,member2,expected",
        [
            ("NONE", "HARD", True),
            ("NONE", "NORMAL", True),
            ("HARD", "NORMAL", True),
            ("NORMAL", "HARD", False),
        ],
    )
    def test_enum_less_than(self, member1, member2, expected):
        m1 = getattr(EnvQuoteType, member1)
        m2 = getattr(EnvQuoteType, member2)
        assert (m1 < m2) == expected
