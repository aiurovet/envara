import pytest
import types
from pathlib import Path
from enum import IntFlag

project_dir = Path(__file__).parent.parent
src_dir = project_dir / "src"

env_expand_flags_mod = types.ModuleType("envara.env_expand_flags")
env_expand_flags_file = src_dir / "envara" / "env_expand_flags.py"
with open(env_expand_flags_file) as f:
    code = compile(f.read(), "env_expand_flags.py", "exec")
    exec(code, env_expand_flags_mod.__dict__)

EnvExpandFlags = env_expand_flags_mod.EnvExpandFlags


class TestEnvExpandFlagsValues:
    @pytest.mark.parametrize(
        "flag,expected_value",
        [
            ("NONE", 0),
            ("ALLOW_SHELL", 1 << 0),
            ("ALLOW_SUBPROC", 1 << 1),
            ("SKIP_HARD_QUOTED", 1 << 2),
            ("STRIP_COMMENT", 1 << 3),
            ("STRIP_SPACES", 1 << 4),
            ("UNESCAPE", 1 << 5),
            ("UNQUOTE", 1 << 6),
        ],
    )
    def test_flag_values(self, flag, expected_value):
        assert getattr(EnvExpandFlags, flag).value == expected_value

    def test_default_value(self):
        assert EnvExpandFlags.DEFAULT.value == (
            EnvExpandFlags.ALLOW_SHELL
            | EnvExpandFlags.SKIP_HARD_QUOTED
            | EnvExpandFlags.STRIP_SPACES
            | EnvExpandFlags.UNESCAPE
            | EnvExpandFlags.UNQUOTE
        )


class TestEnvExpandFlagsIsIntFlag:
    def test_is_intflag(self):
        assert issubclass(EnvExpandFlags, IntFlag)


class TestEnvExpandFlagsNone:
    def test_none_is_zero(self):
        assert EnvExpandFlags.NONE == 0
        assert EnvExpandFlags.NONE.value == 0

    def test_none_combines_with_or(self):
        result = EnvExpandFlags.NONE | EnvExpandFlags.ALLOW_SHELL
        assert result == EnvExpandFlags.ALLOW_SHELL

    def test_none_combines_with_and(self):
        result = EnvExpandFlags.ALLOW_SHELL & EnvExpandFlags.NONE
        assert result == EnvExpandFlags.NONE


class TestEnvExpandFlagsCombine:
    @pytest.mark.parametrize(
        "flag1,flag2",
        [
            ("ALLOW_SHELL", "ALLOW_SUBPROC"),
            ("ALLOW_SHELL", "STRIP_COMMENT"),
            ("UNQUOTE", "SKIP_HARD_QUOTED"),
            ("UNESCAPE", "STRIP_SPACES"),
        ],
    )
    def test_or_combines_flags(self, flag1, flag2):
        f1 = getattr(EnvExpandFlags, flag1)
        f2 = getattr(EnvExpandFlags, flag2)
        combined = f1 | f2
        assert combined & f1 == f1
        assert combined & f2 == f2

    @pytest.mark.parametrize(
        "flag",
        [
            "ALLOW_SHELL",
            "SKIP_HARD_QUOTED",
            "STRIP_SPACES",
            "UNESCAPE",
            "UNQUOTE",
        ],
    )
    def test_flag_in_default(self, flag):
        assert getattr(EnvExpandFlags, flag) & EnvExpandFlags.DEFAULT == getattr(
            EnvExpandFlags, flag
        )


class TestEnvExpandFlagsDefault:
    def test_default_contains_expected_flags(self):
        expected = {
            EnvExpandFlags.ALLOW_SHELL,
            EnvExpandFlags.SKIP_HARD_QUOTED,
            EnvExpandFlags.STRIP_SPACES,
            EnvExpandFlags.UNESCAPE,
            EnvExpandFlags.UNQUOTE,
        }
        for flag in expected:
            assert flag & EnvExpandFlags.DEFAULT == flag

    def test_default_excludes_shell_related_flags(self):
        assert not (EnvExpandFlags.DEFAULT & EnvExpandFlags.ALLOW_SUBPROC)
        assert not (EnvExpandFlags.DEFAULT & EnvExpandFlags.STRIP_COMMENT)
        assert not (EnvExpandFlags.DEFAULT & EnvExpandFlags.SKIP_ENV_VARS)

    def test_default_is_not_none(self):
        assert EnvExpandFlags.DEFAULT != EnvExpandFlags.NONE
        assert EnvExpandFlags.DEFAULT != 0


class TestEnvExpandFlagsBitwiseOperations:
    @pytest.mark.parametrize(
        "op,flag1,flag2,expected",
        [
            ("or", "ALLOW_SHELL", "UNQUOTE", 1 << 0 | 1 << 5),
            ("and", "ALLOW_SHELL", "ALLOW_SUBPROC", 0),
            ("xor", "ALLOW_SHELL", "ALLOW_SHELL", 0),
            ("xor", "ALLOW_SHELL", "UNQUOTE", 1 << 0 | 1 << 5),
        ],
    )
    def test_bitwise_operations(self, op, flag1, flag2, expected):
        f1 = getattr(EnvExpandFlags, flag1) if isinstance(flag1, str) else flag1
        f2 = getattr(EnvExpandFlags, flag2) if isinstance(flag2, str) else flag2
        result = getattr(f1, f"__{op}__")(f2)
        assert (result.value if hasattr(result, "value") else result) == expected


class TestEnvExpandFlagsIdentity:
    def test_combined_flags_are_singleton(self):
        result1 = EnvExpandFlags.ALLOW_SHELL | EnvExpandFlags.UNQUOTE
        result2 = EnvExpandFlags.ALLOW_SHELL | EnvExpandFlags.UNQUOTE
        assert result1 == result2
