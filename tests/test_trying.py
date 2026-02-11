import os
import pytest
from trying import Trying


def test_unbraced_env_var(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    assert Trying.expand_posix("Value $FOO") == "Value bar"


def test_braced_env_var(monkeypatch):
    monkeypatch.setenv("BR", "yes")
    assert Trying.expand_posix("Before ${BR} After") == "Before yes After"


def test_length(monkeypatch):
    monkeypatch.setenv("L", "abcd")
    assert Trying.expand_posix("${#L}") == "4"


def test_default_unset_or_null(monkeypatch):
    # unset
    monkeypatch.delenv("DEF", raising=False)
    assert Trying.expand_posix("${DEF:-alt}") == "alt"
    # null
    monkeypatch.setenv("DEF", "")
    assert Trying.expand_posix("${DEF:-alt}") == "alt"


def test_default_unset_only(monkeypatch):
    monkeypatch.delenv("D2", raising=False)
    assert Trying.expand_posix("${D2-default}") == "default"
    monkeypatch.setenv("D2", "")
    # since set (even empty), '-' does not apply
    assert Trying.expand_posix("${D2-default}") == ""


def test_alternate(monkeypatch):
    monkeypatch.setenv("A", "val")
    assert Trying.expand_posix("${A:+alt}") == "alt"
    monkeypatch.delenv("A", raising=False)
    assert Trying.expand_posix("${A:+alt}") == ""


def test_error_colon(monkeypatch):
    monkeypatch.delenv("E", raising=False)
    with pytest.raises(ValueError):
        Trying.expand_posix("${E:?missing}")


def test_error_no_colon(monkeypatch):
    monkeypatch.delenv("E2", raising=False)
    with pytest.raises(ValueError):
        Trying.expand_posix("${E2?missing}")


def test_substring(monkeypatch):
    monkeypatch.setenv("S", "abcdefgh")
    assert Trying.expand_posix("${S:2:3}") == "cde"
    assert Trying.expand_posix("${S:3}") == "defgh"


def test_nested_default(monkeypatch):
    monkeypatch.delenv("X", raising=False)
    monkeypatch.delenv("Y", raising=False)
    assert Trying.expand_posix("${X:-${Y:-inner}}") == "inner"


def test_escape_dollar(monkeypatch):
    monkeypatch.setenv("ESC", "value")
    s = r"literal \$ESC and real $ESC"
    assert Trying.expand_posix(s) == "literal $ESC and real value"


def test_nonexistent_unchanged():
    assert Trying.expand_posix("keep ${NO_SUCH}") == "keep ${NO_SUCH}"
    assert Trying.expand_posix("keep $NO_SUCH") == "keep $NO_SUCH"


def test_assignment_operators(monkeypatch):
    # := assigns if unset or null
    monkeypatch.delenv("ASS", raising=False)
    assert Trying.expand_posix("${ASS:=hello}") == "hello"
    assert os.getenv("ASS") == "hello"
    # = assigns only if unset
    monkeypatch.delenv("ASS2", raising=False)
    assert Trying.expand_posix("${ASS2=foo}") == "foo"
    assert os.getenv("ASS2") == "foo"
    monkeypatch.setenv("ASS2", "")
    assert Trying.expand_posix("${ASS2=bar}") == ""


def test_assignment_to_custom_vars_dict():
    d: dict = {}
    assert Trying.expand_posix("${N:=x}", vars=d) == "x"
    assert d.get("N") == "x"


def test_substitution_and_all(monkeypatch):
    monkeypatch.setenv("R", "foo_bar_foo")
    assert Trying.expand_posix("${R/foo/X}") == "X_bar_foo"
    assert Trying.expand_posix("${R//foo/X}") == "X_bar_X"


def test_prefix_suffix_removal(monkeypatch):
    monkeypatch.setenv("Z", "pre_mid_suf")
    assert Trying.expand_posix("${Z#pre_}") == "mid_suf"
    assert Trying.expand_posix("${Z%_suf}") == "pre_mid"


def test_prefix_suffix_wildcard(monkeypatch):
    monkeypatch.setenv("Y", "aaaaab")
    assert Trying.expand_posix("${Y#a*}") == "aaaab"
    # longest match may consume the whole string
    assert Trying.expand_posix("${Y##a*}") == ""


def test_anchor_substitution(monkeypatch):
    monkeypatch.setenv("V", "foobarfoo")
    assert Trying.expand_posix("${V/#foo/X}") == "Xbarfoo"
    assert Trying.expand_posix("${V/%foo/X}") == "foobarX"


def test_global_and_single_substitution(monkeypatch):
    monkeypatch.setenv("SUB", "foofoo")
    assert Trying.expand_posix("${SUB/foo/X}") == "Xfoo"
    assert Trying.expand_posix("${SUB//foo/X}") == "XX"


def test_anchor_subst_with_glob(monkeypatch):
    monkeypatch.setenv("G", "abc123abc")
    # prefix pattern 'a*' shortest prefix match is 'a' -> replace just that
    assert Trying.expand_posix("${G/#a*/X}") == "Xbc123abc"
    # suffix pattern '*abc' matches ending 'abc', should replace end
    assert Trying.expand_posix("${G/%*abc/Y}") == "abc123Y"


def test_global_anchored_prefix_removal(monkeypatch):
    monkeypatch.setenv("P", "ababab")
    # remove leading 'ab' repeatedly
    assert Trying.expand_posix("${P//#ab/}") == ""


def test_global_anchored_suffix_removal(monkeypatch):
    monkeypatch.setenv("S", "foofoo")
    # remove trailing 'foo' repeatedly
    assert Trying.expand_posix("${S//%foo/}") == ""


def test_empty_pattern_global_unanchored(monkeypatch):
    monkeypatch.setenv("E", "ab")
    # empty pattern (global) inserts between every position
    assert Trying.expand_posix("${E///X}") == "XaXbX"


def test_empty_pattern_anchored_prefix_noop(monkeypatch):
    monkeypatch.setenv("P", "abc")
    # anchored empty pattern should not match non-empty prefixes
    assert Trying.expand_posix("${P//#/X}") == "abc"


def test_empty_pattern_replace_with_empty(monkeypatch):
    monkeypatch.setenv("E2", "ab")
    # empty pattern replaced with empty string should leave input unchanged
    assert Trying.expand_posix("${E2///}") == "ab"


def test_nested_replacement_with_defaults(monkeypatch):
    monkeypatch.delenv("B", raising=False)
    monkeypatch.setenv("VAR", "foofoo")
    # replacement contains a default that expands to 'Y'
    assert Trying.expand_posix("${VAR//foo/${B:-Y}}") == "YY"


def test_replacement_with_nested_substitution(monkeypatch):
    monkeypatch.setenv("B", "Z")
    monkeypatch.setenv("VAR", "foofoo")
    assert Trying.expand_posix("${VAR//foo/${B}}") == "ZZ"


def test_no_infinite_loop_when_replacement_equals_original(monkeypatch):
    monkeypatch.setenv("T", "a")
    # replacement equals original should not cause infinite loop
    assert Trying.expand_posix("${T//#/a}") == "a"

def test_command_substitution_parens():
    assert Trying.expand_posix('$(printf "X")') == "X"


def test_command_substitution_backticks():
    assert Trying.expand_posix('`printf "Y"`') == "Y"


def test_command_substitution_with_env(monkeypatch):
    monkeypatch.setenv("FOO", "hello")
    assert Trying.expand_posix('$(printf "%s" $FOO)') == "hello"


def test_command_substitution_with_braced_env(monkeypatch):
    monkeypatch.setenv("FOO", "hello")
    assert Trying.expand_posix('$(printf "%s" ${FOO})') == "hello"


def test_command_substitution_error():
    # a command that fails should raise ValueError
    with pytest.raises(ValueError):
        Trying.expand_posix('$(false)')


def test_command_subst_disabled():
    # when disabled, the original expression must remain intact
    assert Trying.expand_posix('$(printf "X")', allow_subprocess=False) == '$(printf "X")'
    assert Trying.expand_posix('`printf "Y"`', allow_subprocess=False) == '`printf "Y"`'


def test_command_subst_no_shell():
    # no shell mode should still execute simple commands
    assert Trying.expand_posix('$(printf "Z")', allow_shell=False) == 'Z'


def test_command_subst_timeout():
    # use python to sleep; enforce tight timeout
    with pytest.raises(ValueError):
        Trying.expand_posix('$(python -c "import time; time.sleep(0.2)")', subprocess_timeout=0.01)


# ---------------------------------------------------------------------------
# Windows-style expansion via Trying.expand_symmetric
# ---------------------------------------------------------------------------

def test_trying_expand_named_env_var(monkeypatch):
    monkeypatch.setenv("TEST_FOO", "bar")
    assert Trying.expand_simple("Value %TEST_FOO% end") == "Value bar end"


def test_trying_positional_args():
    args = ["one", "two"]
    assert Trying.expand_simple("Arg %1 and %2", args=args) == "Arg one and two"


def test_trying_literal_percent():
    assert Trying.expand_simple("100%% sure") == "100% sure"


def test_trying_caret_escape(monkeypatch):
    monkeypatch.setenv("VAR", "val")
    s = r"literal ^%VAR% and real %VAR%"
    assert Trying.expand_simple(s) == "literal %VAR% and real val"


def test_trying_missing_var_unchanged(monkeypatch):
    monkeypatch.delenv("NO_SUCH", raising=False)
    assert Trying.expand_simple("keep %NO_SUCH%") == "keep %NO_SUCH%"


def test_trying_star_expansion():
    args = ["a", "b"]
    assert Trying.expand_simple("All %*", args=args) == "All a b"


def test_trying_trailing_percent_no_close():
    assert Trying.expand_simple("Bad %NAME rest") == "Bad %NAME rest"


def test_trying_digit_with_trailing_percent_uncommon():
    args = ["X"]
    assert Trying.expand_simple("%1%", args=args) == "X"
    assert Trying.expand_simple("%1", args=args) == "X"


def test_trying_modifiers_dpnx():
    args = ["/home/user/file.txt"]
    # %~d = drive (empty on POSIX), %~p = path with trailing sep
    expected_dp = os.path.splitdrive(args[0])[0] + os.path.dirname(args[0]) + os.sep
    assert Trying.expand_simple("%~dp1", args=args) == expected_dp
    assert Trying.expand_simple("%~n1", args=args) == os.path.splitext(os.path.basename(args[0]))[0]
    assert Trying.expand_simple("%~x1", args=args) == os.path.splitext(args[0])[1]
    assert Trying.expand_simple("%~nx1", args=args) == os.path.splitext(os.path.basename(args[0]))[0] + os.path.splitext(args[0])[1]
    # combined dpnx
    expected = expected_dp + os.path.splitext(os.path.basename(args[0]))[0] + os.path.splitext(args[0])[1]
    assert Trying.expand_simple("%~dpnx1", args=args) == expected


def test_trying_modifiers_missing_arg_leaves_intact():
    args = []
    assert Trying.expand_simple("%~dp1", args=args) == "%~dp1"


def test_trying_named_var_substring_positive(monkeypatch):
    monkeypatch.setenv("SV", "abcdefgh")
    assert Trying.expand_simple("%SV:~2,3%") == "cde"


def test_trying_named_var_substring_from_start(monkeypatch):
    monkeypatch.setenv("SV", "abcdefgh")
    assert Trying.expand_simple("%SV:~2%") == "cdefgh"


def test_trying_named_var_substring_negative(monkeypatch):
    monkeypatch.setenv("SV", "abcdefgh")
    assert Trying.expand_simple("%SV:~-3,2%") == "fg"


def test_trying_named_var_substring_missing_var(monkeypatch):
    monkeypatch.delenv("NOPE", raising=False)
    assert Trying.expand_simple("%NOPE:~1,2%") == "%NOPE:~1,2%"


def test_expand_symmetric_custom_expand_named_and_positional():
    # Named variable using custom expand char '@'
    assert Trying.expand_simple("@FOO@", vars={"FOO": "bar"}, exp_chr="@") == "bar"
    # Positional using custom expand char '@'
    assert Trying.expand_simple("@1", args=["one"], exp_chr="@") == "one"
    # Literal '@' via doubling
    assert Trying.expand_simple("@@", exp_chr="@") == "@"


def test_expand_symmetric_custom_escape_behavior():
    # Custom escape '\' should prevent expansion and yield the literal token
    assert Trying.expand_simple(r"\%FOO%", esc_chr="\\", vars={"FOO": "X"}) == "%FOO%"
    # Combined custom expand '@' and custom escape '\' should produce a literal @FOO@
    assert Trying.expand_simple(r"\@FOO@", esc_chr="\\", exp_chr="@", vars={"FOO": "X"}) == "@FOO@"
    # Default caret escape still works (sanity)
    assert Trying.expand_simple(r"^%FOO%", esc_chr="^", vars={"FOO": "X"}) == "%FOO%"


# ---------------------------------------------------------------------------
# expand_posix tests with backtick as escape character
# ---------------------------------------------------------------------------

def test_expand_posix_backtick_escape_dollar(monkeypatch):
    monkeypatch.setenv("VAR", "value")
    # backtick escapes the dollar sign
    assert Trying.expand_posix("`$VAR", esc_chr="`", vars={"VAR": "value"}) == "$VAR"


def test_expand_posix_backtick_escape_multiple_dollars(monkeypatch):
    # two backticks: first escapes second backtick, then $ is processed
    assert Trying.expand_posix("``$VAR", esc_chr="`", vars={"VAR": "value"}) == "`value"


def test_expand_posix_backtick_escape_odd_count(monkeypatch):
    # odd number of backticks: final one escapes the dollar
    assert Trying.expand_posix("`$VAR", esc_chr="`", vars={"VAR": "value"}) == "$VAR"


def test_expand_posix_backtick_escape_even_count(monkeypatch):
    # even number of backticks: none escape the dollar
    assert Trying.expand_posix("````$VAR", esc_chr="`", vars={"VAR": "value"}) == "``value"


def test_expand_posix_backtick_escape_braced_var(monkeypatch):
    # backtick escapes braced variable expansion
    assert Trying.expand_posix("`${VAR}", esc_chr="`", vars={"VAR": "value"}) == "${VAR}"


def test_expand_posix_backtick_not_escape_when_cmd_disabled(monkeypatch):
    # when subprocess disabled, backtick is just a literal character
    result = Trying.expand_posix("`echo test`", esc_chr="`", allow_subprocess=False)
    assert result == "`echo test`"


def test_expand_posix_backtick_escape_with_other_chars(monkeypatch):
    # backtick escape should not affect other characters
    # Note: backtick after the escape is output literally, then $ expands normally
    assert Trying.expand_posix("a`$VARb", esc_chr="`", vars={"VAR": "x"}) == "a$VARb"


def test_expand_posix_backtick_escape_mixed_with_normal(monkeypatch):
    # mixing escaped and unescaped expansions
    result = Trying.expand_posix("`$A and $B", esc_chr="`", vars={"A": "first", "B": "second"})
    assert result == "$A and second"


def test_expand_posix_backtick_escape_in_nested_expansion(monkeypatch):
    # When backtick is escape, it disables backtick command substitution
    # So we test a simple default expansion instead
    result = Trying.expand_posix("${VAR:-hello}", esc_chr="`", vars={"INNER": "value"})
    assert result == "hello"


def test_expand_posix_backtick_escape_command_subst(monkeypatch):
    # backtick escape should prevent command substitution with parentheses
    result = Trying.expand_posix("`$(echo test)", esc_chr="`", allow_subprocess=True)
    assert result == "$(echo test)"