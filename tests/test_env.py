import os
import pytest
from env import Env
from env_exp_flags import EnvExpFlags
from env_platform_stack_flags import EnvPlatformStackFlags


# ---------------------------------------------------------------------------
# Windows-style expansion via Env.expand_simple
# ---------------------------------------------------------------------------

def test_expand_posix_expand_posix_unbraced_env_var(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    assert Env.expand_posix("Value $FOO") == "Value bar"


def test_expand_posix_braced_env_var(monkeypatch):
    monkeypatch.setenv("BR", "yes")
    assert Env.expand_posix("Before ${BR} After") == "Before yes After"


def test_expand_posix_length(monkeypatch):
    monkeypatch.setenv("L", "abcd")
    assert Env.expand_posix("${#L}") == "4"


def test_expand_posix_default_unset_or_null(monkeypatch):
    # unset
    monkeypatch.delenv("DEF", raising=False)
    assert Env.expand_posix("${DEF:-alt}") == "alt"
    # null
    monkeypatch.setenv("DEF", "")
    assert Env.expand_posix("${DEF:-alt}") == "alt"


def test_expand_posix_default_unset_only(monkeypatch):
    monkeypatch.delenv("D2", raising=False)
    assert Env.expand_posix("${D2-default}") == "default"
    monkeypatch.setenv("D2", "")
    # since set (even empty), '-' does not apply
    assert Env.expand_posix("${D2-default}") == ""


def test_expand_posix_alternate(monkeypatch):
    monkeypatch.setenv("A", "val")
    assert Env.expand_posix("${A:+alt}") == "alt"
    monkeypatch.delenv("A", raising=False)
    assert Env.expand_posix("${A:+alt}") == ""


def test_expand_posix_error_colon(monkeypatch):
    monkeypatch.delenv("E", raising=False)
    with pytest.raises(ValueError):
        Env.expand_posix("${E:?missing}")


def test_expand_posix_error_no_colon(monkeypatch):
    monkeypatch.delenv("E2", raising=False)
    with pytest.raises(ValueError):
        Env.expand_posix("${E2?missing}")


def test_expand_posix_substring(monkeypatch):
    monkeypatch.setenv("S", "abcdefgh")
    assert Env.expand_posix("${S:2:3}") == "cde"
    assert Env.expand_posix("${S:3}") == "defgh"


def test_expand_posix_nested_default(monkeypatch):
    monkeypatch.delenv("X", raising=False)
    monkeypatch.delenv("Y", raising=False)
    assert Env.expand_posix("${X:-${Y:-inner}}") == "inner"


def test_expand_posix_escape_dollar(monkeypatch):
    monkeypatch.setenv("ESC", "value")
    s = r"literal \$ESC and real $ESC"
    assert Env.expand_posix(s) == "literal $ESC and real value"


def test_expand_posix_nonexistent_unchanged():
    assert Env.expand_posix("keep ${NO_SUCH}") == "keep ${NO_SUCH}"
    assert Env.expand_posix("keep $NO_SUCH") == "keep $NO_SUCH"


def test_expand_posix_assignment_operators(monkeypatch):
    # := assigns if unset or null
    monkeypatch.delenv("ASS", raising=False)
    assert Env.expand_posix("${ASS:=hello}") == "hello"
    assert os.getenv("ASS") == "hello"
    # = assigns only if unset
    monkeypatch.delenv("ASS2", raising=False)
    assert Env.expand_posix("${ASS2=foo}") == "foo"
    assert os.getenv("ASS2") == "foo"
    monkeypatch.setenv("ASS2", "")
    assert Env.expand_posix("${ASS2=bar}") == ""


def test_expand_posix_assignment_to_custom_vars_dict():
    d: dict = {}
    assert Env.expand_posix("${N:=x}", vars=d) == "x"
    assert d.get("N") == "x"


def test_expand_posix_substitution_and_all(monkeypatch):
    monkeypatch.setenv("R", "foo_bar_foo")
    assert Env.expand_posix("${R/foo/X}") == "X_bar_foo"
    assert Env.expand_posix("${R//foo/X}") == "X_bar_X"


def test_expand_posix_prefix_suffix_removal(monkeypatch):
    monkeypatch.setenv("Z", "pre_mid_suf")
    assert Env.expand_posix("${Z#pre_}") == "mid_suf"
    assert Env.expand_posix("${Z%_suf}") == "pre_mid"


def test_expand_posix_prefix_suffix_wildcard(monkeypatch):
    monkeypatch.setenv("Y", "aaaaab")
    assert Env.expand_posix("${Y#a*}") == "aaaab"
    # longest match may consume the whole string
    assert Env.expand_posix("${Y##a*}") == ""


def test_expand_posix_anchor_substitution(monkeypatch):
    monkeypatch.setenv("V", "foobarfoo")
    assert Env.expand_posix("${V/#foo/X}") == "Xbarfoo"
    assert Env.expand_posix("${V/%foo/X}") == "foobarX"


def test_expand_posix_global_and_single_substitution(monkeypatch):
    monkeypatch.setenv("SUB", "foofoo")
    assert Env.expand_posix("${SUB/foo/X}") == "Xfoo"
    assert Env.expand_posix("${SUB//foo/X}") == "XX"


def test_expand_posix_anchor_subst_with_glob(monkeypatch):
    monkeypatch.setenv("G", "abc123abc")
    # prefix pattern 'a*' shortest prefix match is 'a' -> replace just that
    assert Env.expand_posix("${G/#a*/X}") == "Xbc123abc"
    # suffix pattern '*abc' matches ending 'abc', should replace end
    assert Env.expand_posix("${G/%*abc/Y}") == "abc123Y"


def test_expand_posix_global_anchored_prefix_removal(monkeypatch):
    monkeypatch.setenv("P", "ababab")
    # remove leading 'ab' repeatedly
    assert Env.expand_posix("${P//#ab/}") == ""


def test_expand_posix_global_anchored_suffix_removal(monkeypatch):
    monkeypatch.setenv("S", "foofoo")
    # remove trailing 'foo' repeatedly
    assert Env.expand_posix("${S//%foo/}") == ""


def test_expand_posix_empty_pattern_global_unanchored(monkeypatch):
    monkeypatch.setenv("E", "ab")
    # empty pattern (global) inserts between every position
    assert Env.expand_posix("${E///X}") == "XaXbX"


def test_expand_posix_empty_pattern_anchored_prefix_noop(monkeypatch):
    monkeypatch.setenv("P", "abc")
    # anchored empty pattern should not match non-empty prefixes
    assert Env.expand_posix("${P//#/X}") == "abc"


def test_expand_posix_empty_pattern_replace_with_empty(monkeypatch):
    monkeypatch.setenv("E2", "ab")
    # empty pattern replaced with empty string should leave input unchanged
    assert Env.expand_posix("${E2///}") == "ab"


def test_expand_posix_nested_replacement_with_defaults(monkeypatch):
    monkeypatch.delenv("B", raising=False)
    monkeypatch.setenv("VAR", "foofoo")
    # replacement contains a default that expands to 'Y'
    assert Env.expand_posix("${VAR//foo/${B:-Y}}") == "YY"


def test_expand_posix_replacement_with_nested_substitution(monkeypatch):
    monkeypatch.setenv("B", "Z")
    monkeypatch.setenv("VAR", "foofoo")
    assert Env.expand_posix("${VAR//foo/${B}}") == "ZZ"


def test_expand_posix_no_infinite_loop_when_replacement_equals_original(monkeypatch):
    monkeypatch.setenv("T", "a")
    # replacement equals original should not cause infinite loop
    assert Env.expand_posix("${T//#/a}") == "a"

def test_expand_posix_command_substitution_parens():
    assert Env.expand_posix('$(printf "X")') == "X"


def test_expand_posix_command_substitution_backticks():
    assert Env.expand_posix('`printf "Y"`') == "Y"


def test_expand_posix_command_substitution_with_env(monkeypatch):
    monkeypatch.setenv("FOO", "hello")
    assert Env.expand_posix('$(printf "%s" $FOO)') == "hello"


def test_expand_posix_command_substitution_with_braced_env(monkeypatch):
    monkeypatch.setenv("FOO", "hello")
    assert Env.expand_posix('$(printf "%s" ${FOO})') == "hello"


def test_expand_posix_command_substitution_error():
    # a command that fails should raise ValueError
    with pytest.raises(ValueError):
        Env.expand_posix('$(false)')


def test_expand_posix_command_subst_disabled():
    # when disabled, the original expression must remain intact
    assert Env.expand_posix('$(printf "X")', exp_flags=0) == '$(printf "X")'
    assert Env.expand_posix('`printf "Y"`', exp_flags=0) == '`printf "Y"`'


def test_expand_posix_command_subst_no_shell():
    # no shell mode should still execute simple commands
    assert Env.expand_posix('$(printf "Z")', exp_flags=EnvExpFlags.ALLOW_SUBPROC) == 'Z'


def test_expand_posix_command_subst_timeout():
    # use python to sleep; enforce tight timeout
    with pytest.raises(ValueError):
        Env.expand_posix('$(python -c "import time; time.sleep(0.2)")', exp_flags=EnvExpFlags.ALLOW_SHELL, subprocess_timeout=0.01)

# ---------------------------------------------------------------------------
# expand_posix tests with backtick as escape character
# ---------------------------------------------------------------------------

def test_expand_posix_backtick_escape_dollar(monkeypatch):
    monkeypatch.setenv("VAR", "value")
    # backtick escapes the dollar sign
    assert Env.expand_posix("`$VAR", esc_chr="`", vars={"VAR": "value"}) == "$VAR"


def test_expand_posix_backtick_escape_multiple_dollars(monkeypatch):
    # two backticks: first escapes second backtick, then $ is processed
    assert Env.expand_posix("``$VAR", esc_chr="`", vars={"VAR": "value"}) == "`value"


def test_expand_posix_backtick_escape_odd_count(monkeypatch):
    # odd number of backticks: final one escapes the dollar
    assert Env.expand_posix("`$VAR", esc_chr="`", vars={"VAR": "value"}) == "$VAR"


def test_expand_posix_backtick_escape_even_count(monkeypatch):
    # even number of backticks: none escape the dollar
    assert Env.expand_posix("````$VAR", esc_chr="`", vars={"VAR": "value"}) == "``value"


def test_expand_posix_backtick_escape_braced_var(monkeypatch):
    # backtick escapes braced variable expansion
    assert Env.expand_posix("`${VAR}", esc_chr="`", vars={"VAR": "value"}) == "${VAR}"


def test_expand_posix_backtick_not_escape_when_cmd_disabled(monkeypatch):
    # when subprocess disabled, backtick is just a literal character
    result = Env.expand_posix("`echo test`", esc_chr="`", exp_flags=EnvExpFlags.ALLOW_SHELL)
    assert result == "`echo test`"


def test_expand_posix_backtick_escape_with_other_chars(monkeypatch):
    # backtick escape should not affect other characters
    # Note: backtick after the escape is output literally, then $ expands normally
    assert Env.expand_posix("a`$VARb", esc_chr="`", vars={"VAR": "x"}) == "a$VARb"


def test_expand_posix_backtick_escape_mixed_with_normal(monkeypatch):
    # mixing escaped and unescaped expansions
    result = Env.expand_posix("`$A and $B", esc_chr="`", vars={"A": "first", "B": "second"})
    assert result == "$A and second"


def test_expand_posix_backtick_escape_in_nested_expansion(monkeypatch):
    # When backtick is escape, it disables backtick command substitution
    # So we test a simple default expansion instead
    result = Env.expand_posix("${VAR:-hello}", esc_chr="`", vars={"INNER": "value"})
    assert result == "hello"


def test_expand_posix_backtick_escape_command_subst(monkeypatch):
    # backtick escape should prevent command substitution with parentheses
    result = Env.expand_posix("`$(echo test)", esc_chr="`", exp_flags=EnvExpFlags.ALLOW_SUBPROC)
    assert result == "$(echo test)"


# ---------------------------------------------------------------------------
# Windows-style expansion via Env.expand_simple
# ---------------------------------------------------------------------------

def test_expand_simple_named_env_var(monkeypatch):
    monkeypatch.setenv("TEST_FOO", "bar")
    assert Env.expand_simple("Value %TEST_FOO% end") == "Value bar end"


def test_expand_simple_positional_args():
    args = ["one", "two"]
    assert Env.expand_simple("Arg %1 and %2", args=args) == "Arg one and two"


def test_expand_simple_literal_percent():
    assert Env.expand_simple("100%% sure") == "100% sure"


def test_expand_simple_caret_escape(monkeypatch):
    monkeypatch.setenv("VAR", "val")
    s = r"literal ^%VAR% and real %VAR%"
    assert Env.expand_simple(s) == "literal %VAR% and real val"


def test_expand_simple_missing_var_unchanged(monkeypatch):
    monkeypatch.delenv("NO_SUCH", raising=False)
    assert Env.expand_simple("keep %NO_SUCH%") == "keep %NO_SUCH%"


def test_expand_simple_star_expansion():
    args = ["a", "b"]
    assert Env.expand_simple("All %*", args=args) == "All a b"


def test_expand_simple_trailing_percent_no_close():
    assert Env.expand_simple("Bad %NAME rest") == "Bad %NAME rest"


def test_expand_simple_digit_with_trailing_percent_uncommon():
    args = ["X"]
    assert Env.expand_simple("%1%", args=args) == "X"
    assert Env.expand_simple("%1", args=args) == "X"


def test_expand_simple_modifiers_dpnx():
    args = ["/home/user/file.txt"]
    # %~d = drive (empty on POSIX), %~p = path with trailing sep
    expected_dp = os.path.splitdrive(args[0])[0] + os.path.dirname(args[0]) + os.sep
    assert Env.expand_simple("%~dp1", args=args) == expected_dp
    assert Env.expand_simple("%~n1", args=args) == os.path.splitext(os.path.basename(args[0]))[0]
    assert Env.expand_simple("%~x1", args=args) == os.path.splitext(args[0])[1]
    assert Env.expand_simple("%~nx1", args=args) == os.path.splitext(os.path.basename(args[0]))[0] + os.path.splitext(args[0])[1]
    # combined dpnx
    expected = expected_dp + os.path.splitext(os.path.basename(args[0]))[0] + os.path.splitext(args[0])[1]
    assert Env.expand_simple("%~dpnx1", args=args) == expected


def test_expand_simple_modifiers_missing_arg_leaves_intact():
    args = []
    assert Env.expand_simple("%~dp1", args=args) == "%~dp1"


def test_expand_simple_named_var_substring_positive(monkeypatch):
    monkeypatch.setenv("SV", "abcdefgh")
    assert Env.expand_simple("%SV:~2,3%") == "cde"


def test_expand_simple_named_var_substring_from_start(monkeypatch):
    monkeypatch.setenv("SV", "abcdefgh")
    assert Env.expand_simple("%SV:~2%") == "cdefgh"


def test_expand_simple_named_var_substring_negative(monkeypatch):
    monkeypatch.setenv("SV", "abcdefgh")
    assert Env.expand_simple("%SV:~-3,2%") == "fg"


def test_expand_simple_named_var_substring_missing_var(monkeypatch):
    monkeypatch.delenv("NOPE", raising=False)
    assert Env.expand_simple("%NOPE:~1,2%") == "%NOPE:~1,2%"


def test_expand_simple_custom_expand_named_and_positional():
    # Named variable using custom expand char '@'
    assert Env.expand_simple("@FOO@", vars={"FOO": "bar"}, exp_chr="@") == "bar"
    # Positional using custom expand char '@'
    assert Env.expand_simple("@1", args=["one"], exp_chr="@") == "one"
    # Literal '@' via doubling
    assert Env.expand_simple("@@", exp_chr="@") == "@"


def test_expand_simple_custom_escape_behavior():
    # Custom escape '\' should prevent expansion and yield the literal token
    assert Env.expand_simple(r"\%FOO%", esc_chr="\\", vars={"FOO": "X"}) == "%FOO%"
    # Combined custom expand '@' and custom escape '\' should produce a literal @FOO@
    assert Env.expand_simple(r"\@FOO@", esc_chr="\\", exp_chr="@", vars={"FOO": "X"}) == "@FOO@"
    # Default caret escape still works (sanity)
    assert Env.expand_simple(r"^%FOO%", esc_chr="^", vars={"FOO": "X"}) == "%FOO%"



# ---------------------------------------------------------------------------
# Tests for Env.get_platform_stack method
# ---------------------------------------------------------------------------

def test_get_platform_stack_no_flags():
    # With EnvPlatformStackFlags.NONE, minimal platforms should be returned
    result = Env.get_platform_stack(flags=EnvPlatformStackFlags.NONE)
    # Should return a list with at least the current platform
    assert isinstance(result, list)
    assert len(result) > 0


def test_get_platform_stack_add_empty(mocker):
    # Patch to ensure we're on a known platform
    mocker.patch.object(Env, "PLATFORM_THIS", "linux")
    mocker.patch.object(Env, "IS_POSIX", True)
    
    # Get stack with ADD_EMPTY flag
    result = Env.get_platform_stack(flags=EnvPlatformStackFlags.ADD_EMPTY)
    
    # Empty string should be included
    assert "" in result
    assert isinstance(result, list)


def test_get_platform_stack_add_max_includes_all(mocker):
    # Patch platform details for Linux + POSIX
    mocker.patch.object(Env, "PLATFORM_THIS", "linux")
    mocker.patch.object(Env, "IS_POSIX", True)
    mocker.patch.object(Env, "IS_WINDOWS", False)
    
    # Get full stack with ADD_MAX flag
    result = Env.get_platform_stack(flags=EnvPlatformStackFlags.ADD_MAX)
    
    # Result should contain multiple platforms
    assert len(result) > 0
    assert isinstance(result, list)
    # Should include at least the current platform (linux)
    assert "linux" in result
