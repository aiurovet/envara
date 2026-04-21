import pytest
import types
from pathlib import Path
from enum import IntFlag

project_dir = Path(__file__).parent.parent
src_dir = project_dir / "src"

env_file_flags_mod = types.ModuleType("envara.env_file_flags")
env_file_flags_file = src_dir / "envara" / "env_file_flags.py"
with open(env_file_flags_file) as f:
    code = compile(f.read(), "env_file_flags.py", "exec")
    exec(code, env_file_flags_mod.__dict__)

EnvFileFlags = env_file_flags_mod.EnvFileFlags


class TestEnvFileFlagsValues:
    @pytest.mark.parametrize(
        "flag,expected_value",
        [
            ("NONE", 0),
            ("ADD_PLATFORMS_BEFORE", 1 << 0),
            ("ADD_PLATFORMS_AFTER", 1 << 1),
            ("RESET_ACCUMULATED", 1 << 2),
        ],
    )
    def test_flag_values(self, flag, expected_value):
        assert getattr(EnvFileFlags, flag).value == expected_value


class TestEnvFileFlagsIsIntFlag:
    def test_is_intflag(self):
        assert issubclass(EnvFileFlags, IntFlag)


class TestEnvFileFlagsNone:
    def test_none_is_zero(self):
        assert EnvFileFlags.NONE == 0
        assert EnvFileFlags.NONE.value == 0

    def test_none_combines_with_or(self):
        result = EnvFileFlags.NONE | EnvFileFlags.ADD_PLATFORMS_BEFORE
        assert result == EnvFileFlags.ADD_PLATFORMS_BEFORE

    def test_none_combines_with_and(self):
        result = EnvFileFlags.ADD_PLATFORMS_BEFORE & EnvFileFlags.NONE
        assert result == EnvFileFlags.NONE


class TestEnvFileFlagsCombine:
    @pytest.mark.parametrize(
        "flag1,flag2",
        [
            ("ADD_PLATFORMS_BEFORE", "ADD_PLATFORMS_AFTER"),
            ("ADD_PLATFORMS_BEFORE", "RESET_ACCUMULATED"),
            ("ADD_PLATFORMS_AFTER", "RESET_ACCUMULATED"),
        ],
    )
    def test_or_combines_flags(self, flag1, flag2):
        f1 = getattr(EnvFileFlags, flag1)
        f2 = getattr(EnvFileFlags, flag2)
        combined = f1 | f2
        assert combined & f1 == f1
        assert combined & f2 == f2


class TestEnvFileFlagsMutuallyExclusive:
    def test_platform_flags_are_exclusive(self):
        assert not (EnvFileFlags.ADD_PLATFORMS_BEFORE & EnvFileFlags.ADD_PLATFORMS_AFTER)

    def test_platform_flags_can_combine(self):
        combined = EnvFileFlags.ADD_PLATFORMS_BEFORE | EnvFileFlags.ADD_PLATFORMS_AFTER
        assert combined == (1 << 0 | 1 << 1)


class TestEnvFileFlagsBitwiseOperations:
    @pytest.mark.parametrize(
        "op,flag1,flag2,expected",
        [
            ("or", "ADD_PLATFORMS_BEFORE", "RESET_ACCUMULATED", 1 << 0 | 1 << 2),
            ("and", "ADD_PLATFORMS_BEFORE", "ADD_PLATFORMS_AFTER", 0),
            ("xor", "ADD_PLATFORMS_BEFORE", "ADD_PLATFORMS_BEFORE", 0),
            ("xor", "ADD_PLATFORMS_BEFORE", "RESET_ACCUMULATED", 1 << 0 | 1 << 2),
        ],
    )
    def test_bitwise_operations(self, op, flag1, flag2, expected):
        f1 = getattr(EnvFileFlags, flag1)
        f2 = getattr(EnvFileFlags, flag2)
        result = getattr(f1, f"__{op}__")(f2)
        assert (result.value if hasattr(result, "value") else result) == expected


class TestEnvFileFlagsIdentity:
    def test_combined_flags_are_singleton(self):
        result1 = EnvFileFlags.ADD_PLATFORMS_BEFORE | EnvFileFlags.RESET_ACCUMULATED
        result2 = EnvFileFlags.ADD_PLATFORMS_BEFORE | EnvFileFlags.RESET_ACCUMULATED
        assert result1 == result2

    def test_none_not_equal_to_flags(self):
        assert EnvFileFlags.NONE != EnvFileFlags.ADD_PLATFORMS_BEFORE
        assert EnvFileFlags.NONE != EnvFileFlags.ADD_PLATFORMS_AFTER
        assert EnvFileFlags.NONE != EnvFileFlags.RESET_ACCUMULATED
