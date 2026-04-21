import pytest
import types
from pathlib import Path
from enum import IntFlag

project_dir = Path(__file__).parent.parent
src_dir = project_dir / "src"

env_platform_flags_mod = types.ModuleType("envara.env_platform_flags")
env_platform_flags_file = src_dir / "envara" / "env_platform_flags.py"
with open(env_platform_flags_file) as f:
    code = compile(f.read(), "env_platform_flags.py", "exec")
    exec(code, env_platform_flags_mod.__dict__)

EnvPlatformFlags = env_platform_flags_mod.EnvPlatformFlags


class TestEnvPlatformFlagsValues:
    @pytest.mark.parametrize(
        "member,expected_value",
        [
            ("NONE", 0),
            ("ADD_EMPTY", 1 << 0),
        ],
    )
    def test_flag_values(self, member, expected_value):
        assert getattr(EnvPlatformFlags, member).value == expected_value


class TestEnvPlatformFlagsIsIntFlag:
    def test_is_intflag(self):
        assert issubclass(EnvPlatformFlags, IntFlag)


class TestEnvPlatformFlagsNone:
    def test_none_is_zero(self):
        assert EnvPlatformFlags.NONE == 0
        assert EnvPlatformFlags.NONE.value == 0

    def test_none_combines_with_or(self):
        result = EnvPlatformFlags.NONE | EnvPlatformFlags.ADD_EMPTY
        assert result == EnvPlatformFlags.ADD_EMPTY

    def test_none_combines_with_and(self):
        result = EnvPlatformFlags.ADD_EMPTY & EnvPlatformFlags.NONE
        assert result == EnvPlatformFlags.NONE


class TestEnvPlatformFlagsCombine:
    def test_or_with_self(self):
        combined = EnvPlatformFlags.ADD_EMPTY | EnvPlatformFlags.ADD_EMPTY
        assert combined == EnvPlatformFlags.ADD_EMPTY

    def test_and_with_self(self):
        combined = EnvPlatformFlags.ADD_EMPTY & EnvPlatformFlags.ADD_EMPTY
        assert combined == EnvPlatformFlags.ADD_EMPTY

    def test_xor_with_self(self):
        combined = EnvPlatformFlags.ADD_EMPTY ^ EnvPlatformFlags.ADD_EMPTY
        assert combined == EnvPlatformFlags.NONE


class TestEnvPlatformFlagsBitwiseOperations:
    @pytest.mark.parametrize(
        "op,flag1,flag2,expected",
        [
            ("or", "ADD_EMPTY", "ADD_EMPTY", 1 << 0),
            ("and", "ADD_EMPTY", "ADD_EMPTY", 1 << 0),
            ("xor", "ADD_EMPTY", "ADD_EMPTY", 0),
        ],
    )
    def test_bitwise_operations(self, op, flag1, flag2, expected):
        f1 = getattr(EnvPlatformFlags, flag1)
        f2 = getattr(EnvPlatformFlags, flag2)
        result = getattr(f1, f"__{op}__")(f2)
        assert (result.value if hasattr(result, "value") else result) == expected


class TestEnvPlatformFlagsIdentity:
    @pytest.mark.parametrize(
        "member",
        ["NONE", "ADD_EMPTY"],
    )
    def test_enum_members_are_singleton(self, member):
        m1 = getattr(EnvPlatformFlags, member)
        m2 = getattr(EnvPlatformFlags, member)
        assert m1 is m2

    def test_none_not_equal_to_add_empty(self):
        assert EnvPlatformFlags.NONE != EnvPlatformFlags.ADD_EMPTY
