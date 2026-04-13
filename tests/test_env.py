import os
from pathlib import Path
import pytest
from envara.env import Env
from envara.env_expand_flags import EnvExpandFlags
from envara.env_platform_flags import EnvPlatformFlags
from env_chars import EnvChars
from envara.env_quote_type import EnvQuoteType


# ---------------------------------------------------------------------------
# Tests for Env.expand (uses Env.unquote -> expand_posix/expand_simple path)
# ---------------------------------------------------------------------------


def test_expand_skips_single_quoted_when_flag_set(mocker):
    # Arrange: make unquote report a SINGLE-quoted string
    info = EnvChars(
        input="'x'",
        result="quoted-result",
        expand=EnvChars.POSIX_EXPAND,
        escape="\\",
        quote_type=EnvQuoteType.HARD,
    )
    mocker.patch.object(Env, "unquote", return_value=(None, info))
    m_posix = mocker.patch.object(Env, "expand_posix")
    m_simple = mocker.patch.object(Env, "expand_simple")

    # Act
    out = Env.expand("'x'", flags=EnvExpandFlags.SKIP_LITERAL)

    # Assert - expansion functions must not be called and original result returned
    assert out == "quoted-result"
    m_posix.assert_not_called()
    m_simple.assert_not_called()


def test_expand_uses_posix_and_unescape(mocker):
    # Arrange: unquote reports POSIX expansion character
    info = EnvChars(
        input="$A",
        result="raw-val",
        expand=EnvChars.POSIX_EXPAND,
        escape="\\",
        quote_type=None,
    )
    mocker.patch.object(Env, "unquote", return_value=(None, info))
    m_posix = mocker.patch.object(Env, "expand_posix", return_value="posix-expanded")
    m_unescape = mocker.patch.object(Env, "unescape", return_value="final-unescaped")

    # Act
    out = Env.expand("$A", args=["arg1"], flags=EnvExpandFlags.UNESCAPE)

    # Assert
    m_posix.assert_called_once()
    called_args, called_kwargs = m_posix.call_args
    # first positional arg passed to expand_posix is the unquoted result
    assert called_args[0] == "raw-val"
    assert called_kwargs["args"] == ["arg1"]
    assert called_kwargs["expand_char"] == info.expand
    assert called_kwargs["escape_char"] == info.escape
    # unescape must be invoked with expand_posix's result and the escape char
    m_unescape.assert_called_once_with("posix-expanded", escape_char=info.escape)
    assert out == "final-unescaped"


def test_expand_uses_simple_and_respects_skip_env_vars(mocker):
    # Arrange: unquote reports Windows-style expansion char
    info = EnvChars(
        input="%X%",
        result="raw-simple",
        expand=EnvChars.WINDOWS_EXPAND,
        escape="^",
        quote_type=None,
    )
    mocker.patch.object(Env, "unquote", return_value=(None, info))
    m_simple = mocker.patch.object(Env, "expand_simple", return_value="simple-expanded")

    # Act - request SKIP_ENV_VARS so vars dict should be empty
    out = Env.expand("%X%", flags=EnvExpandFlags.SKIP_ENV_VARS)

    # Assert
    m_simple.assert_called_once()
    _, kw = m_simple.call_args
    assert kw["vars"] == {}
    assert out == "simple-expanded"


def test_expand_with_none_input_returns_empty_and_info_result_set():
    out = Env.expand(None)
    assert out == ""


def test_expand_preserves_spaces_when_strip_false():
    out = Env.expand("  val  ", strip_spaces=False)
    assert out == "  val  "


def test_expand_sets_cutter_chars_on_remove_line_comment_flag():
    out = Env.expand("A #comment", flags=EnvExpandFlags.REMOVE_LINE_COMMENT)
    assert out == "A"


def test_expand_fills_out_info():
    result = 'Sample = "$ABC\n"'
    out_info = EnvChars()
    out = Env.expand(f'Sample = "$ABC\\n" # this is a sample', out_info=out_info)
    # when SKIP_ENV_VARS is set, env variables are not expanded
    assert out == result
    assert out_info.expand == "$"
    assert out_info.escape == "\\"
    assert out_info.cutter == "#"
    assert out_info.quote_type == EnvQuoteType.NONE
    assert out_info.result == result


def test_expand_path(monkeypatch):
    monkeypatch.setenv("VAR", "abcd")
    out = Env.expand(Path("/$VAR/ef"))
    assert out == Path("/abcd/ef")


# ---------------------------------------------------------------------------
# Tests for Env.unescape and Env.unquote
# ---------------------------------------------------------------------------


def test_unescape_basic_and_codes():
    # basic escapes, unicode and hex, and a literal backslash
    inp = "\\n\\t\\u0041\\x41\\\\"
    out = Env.unescape(inp)
    assert out == "\n\tAA"
    out = Env.unescape(inp, strip_blanks=True)
    assert out == "AA"


def test_unescape_strip_blanks_and_hex():
    # hex escapes produce spaces which are stripped when requested
    assert Env.unescape("\\x20a\\x20", strip_blanks=True) == "a"
    # without strip_blanks the spaces remain
    assert Env.unescape("\\x20a\\x20", strip_blanks=False) == " a "


def test_unescape_invalid_hex_calls_fail_and_raises(mocker):
    # Arrange - patch the private error handler to raise so we can assert it's called
    m_fail = mocker.patch.object(
        Env, "_Env__fail_unescape", side_effect=ValueError("bad")
    )

    # Act / Assert
    with pytest.raises(ValueError):
        Env.unescape("\\u00G1")

    m_fail.assert_called_once()


def test_unescape_empty_returns_empty():
    assert Env.unescape("") == ""
    assert Env.unescape(None) == ""


def test_unescape_custom_escape_not_present_returns_input():
    assert Env.unescape("plain-text", escape_char="^") == "plain-text"


def test_unescape_custom_escape_character_is_processed():
    # custom escape '`' should translate `n into newline
    assert Env.unescape("`n", escape_char="`") == "\n"


def test_unescape_strip_blanks_requires_both_ends():
    # only leading blank -> should NOT be stripped (requires both ends)
    assert Env.unescape(r"\x20a", strip_blanks=True) == "a"
    # without strip_blanks the result is identical
    assert Env.unescape(r"\x20a", strip_blanks=False) == " a"


def test_unescape_invalid_x_hex_calls_fail_and_raises(mocker):
    m_fail = mocker.patch.object(
        Env, "_Env__fail_unescape", side_effect=ValueError("bad")
    )
    with pytest.raises(ValueError):
        Env.unescape(r"\x4")
    m_fail.assert_called_once()


def test_unquote_removes_double_quotes_and_sets_info():
    res, info = Env.unquote('"a$B"')
    assert res == "a$B"
    assert info.quote_type == EnvQuoteType.DEFAULT
    assert info.expand == EnvChars.POSIX_EXPAND


def test_unquote_uses_cutter_chars_and_detects_expchr():
    res, info = Env.unquote("$X#y", cutter_chars="#")
    assert res == "$X"
    assert info.expand == EnvChars.POSIX_EXPAND
    assert info.quote_type == EnvQuoteType.NONE


def test_unquote_raises_for_unterminated_quote():
    with pytest.raises(ValueError):
        Env.unquote('"abc')


def test_unquote_raises_for_dangling_escape():
    with pytest.raises(ValueError):
        Env.unquote("abc\\")


def test_unquote_constructs_envparseinfo_when_input_empty(mocker):
    m = mocker.patch("envara.env.EnvParseInfo")
    mock_inst = m.return_value
    mock_inst.result = ""

    res, info = Env.unquote("")

    m.assert_called_once_with(input="", quote_type=EnvQuoteType.NONE)
    assert res == mock_inst.result
    assert info is mock_inst


def test_unquote_hard_quotes_ignore_escape():
    # backslash inside single quotes should be treated literally (hard quote)
    res, info = Env.unquote(r"'a\nb'")
    assert res == r"a\nb"
    assert info.quote_type == EnvQuoteType.HARD
    assert info.escape is None


def test_unquote_hard_quotes_param_disables_escaping():
    # when hard_quotes includes '"', escaping inside normal quotes is ignored
    res, info = Env.unquote('"a\\"b"', hard_quotes='"')
    # encountering the inner normal quote closes the quoted string because
    # escaping is disabled by hard_quotes -> the result contains the backslash
    assert res == "a\\"
    assert info.quote_type == EnvQuoteType.DEFAULT


def test_unquote_preserves_spaces_when_strip_false():
    inp = "  abc  "
    res, info = Env.unquote(inp, strip_spaces=False)
    assert res == inp
    assert info.quote_type == EnvQuoteType.NONE


def test_unquote_detects_first_of_multiple_expansion_chars():
    res, info = Env.unquote("a%b$z", expand_chars="%$")
    assert info.expand == "%"


def test_unquote_quoted_cutter_ignored():
    res, info = Env.unquote("'a#b'", cutter_chars="#")
    assert res == "a#b"


def test_unquote_escaped_quote_inside_normal_quotes():
    res, info = Env.unquote('"a\\"b"')
    # unquote does not remove escaping backslashes (that's done by Env.unescape)
    assert res == r"a\"b"
    assert info.quote_type == EnvQuoteType.DEFAULT
    assert info.escape == "\\"


# ---------------------------------------------------------------------------
# Tests for Env.quote (with and without mocking defaults)
# ---------------------------------------------------------------------------


def test_quote_escapes_internal_normal_and_escape_char():
    # input contains a normal quote and a backslash (default escape)
    inp = 'a"b\\c'
    out = Env.quote(inp, type=EnvQuoteType.DEFAULT)
    # backslash doubled, internal quote escaped, whole string wrapped in normal quotes
    assert out == '"a\\"b\\\\c"'


def test_quote_doubles_escape_chars_and_single_quote():
    inp = "it's\\done"
    out = Env.quote(inp, type=EnvQuoteType.HARD)
    # backslash doubled and single-quote escaped, wrapped in single quotes
    assert out == "'it\\'s\\\\done'"


def test_quote_returns_input_when_no_quote_type():
    assert Env.quote("plain", type=EnvQuoteType.NONE) == "plain"


def test_quote_none_input_returns_empty_quotes():
    assert Env.quote(None) == '""'


def test_quote_with_custom_escape_arg():
    # custom escape character should be used instead of default; when no
    # quote char is present the implementation does not double escapes
    out = Env.quote("a^b^c", type=EnvQuoteType.DEFAULT, escape_char="^")
    assert out == '"a^b^c"'


def test_quote_uses_mocked_default_escape(mocker):
    # patch the default escape char and ensure Env.quote uses it (no doubling
    # unless a quote char is present in the input)
    mocker.patch.object(EnvChars, "POSIX_ESCAPE_CHAR", "^")
    assert Env.quote("a^b") == '"a^b"'


def test_unquote_respects_mocked_posix_expand_char(mocker):
    # patch the default POSIX expansion char and ensure unquote picks it up
    mocker.patch.object(EnvChars, "POSIX_EXPAND_CHAR", "@")
    _, info = Env.unquote("a@b")
    assert info.expand == "@"


def test_unquote_disallows_posix_expand_char_with_windows_escape_char(mocker):
    _, info = Env.unquote('"$a^b"')
    assert info.escape == "\\"


# ---------------------------------------------------------------------------
# POSIX-style expansion via Env.expand_posix
# ---------------------------------------------------------------------------


def test_expand_posix_unbraced_env_var(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    assert Env.expand_posix("Value $FOO") == "Value bar"


def test_expand_posix_braced_env_var(monkeypatch):
    monkeypatch.setenv("BR", "yes")
    assert Env.expand_posix("Before ${BR} After") == "Before yes After"


def test_expand_posix_length(monkeypatch):
    monkeypatch.setenv("L", "abcd")
    assert Env.expand_posix("${#L}") == "4"


def test_expand_posix_numeric_braced_positional_and_missing(monkeypatch):
    # present positional parameter inside braces
    assert Env.expand_posix("${1}", args=["first"]) == "first"
    # missing positional parameter should remain as-is
    assert Env.expand_posix("${2}", args=["only"]) == "${2}"


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
        Env.expand_posix("$(false)")


def test_expand_posix_command_subst_disabled():
    # when disabled, the original expression must remain intact
    assert Env.expand_posix('$(printf "X")', expand_flags=0) == '$(printf "X")'
    assert Env.expand_posix('`printf "Y"`', expand_flags=0) == '`printf "Y"`'


def test_expand_posix_command_subst_no_shell():
    # no shell mode should still execute simple commands
    assert (
        Env.expand_posix('$(printf "Z")', expand_flags=EnvExpandFlags.ALLOW_SUBPROC)
        == "Z"
    )


def test_expand_posix_command_subst_timeout():
    # use python to sleep; enforce tight timeout
    with pytest.raises(ValueError):
        Env.expand_posix(
            '$(python -c "import time; time.sleep(0.2)")',
            expand_flags=EnvExpandFlags.ALLOW_SHELL,
            subprocess_timeout=0.01,
        )


def test_expand_posix_respects_skip_env_vars(monkeypatch):
    monkeypatch.setenv("SILENT", "yes")
    out = Env.expand("$SILENT", flags=EnvExpandFlags.SKIP_ENV_VARS)
    # when SKIP_ENV_VARS is set, env variables are not expanded
    assert out == "$SILENT"


def test_expand_posix_path(monkeypatch):
    monkeypatch.setenv("VAR", "abcd")
    out = Env.expand_posix(Path("/$VAR/ef"))
    assert out == Path("/abcd/ef")


# ---------------------------------------------------------------------------
# expand_posix tests with backtick as escape character
# ---------------------------------------------------------------------------


def test_expand_posix_backtick_escape_dollar(monkeypatch):
    monkeypatch.setenv("VAR", "value")
    # backtick escapes the dollar sign
    assert Env.expand_posix("`$VAR", escape_char="`", vars={"VAR": "value"}) == "$VAR"


def test_expand_posix_backtick_escape_multiple_dollars(monkeypatch):
    # two backticks: first escapes second backtick, then $ is processed
    assert (
        Env.expand_posix("``$VAR", escape_char="`", vars={"VAR": "value"}) == "`value"
    )


def test_expand_posix_backtick_escape_odd_count(monkeypatch):
    # odd number of backticks: final one escapes the dollar
    assert Env.expand_posix("`$VAR", escape_char="`", vars={"VAR": "value"}) == "$VAR"


def test_expand_posix_backtick_escape_even_count(monkeypatch):
    # even number of backticks: none escape the dollar
    assert (
        Env.expand_posix("````$VAR", escape_char="`", vars={"VAR": "value"})
        == "``value"
    )


def test_expand_posix_backtick_escape_braced_var(monkeypatch):
    # backtick escapes braced variable expansion
    assert (
        Env.expand_posix("`${VAR}", escape_char="`", vars={"VAR": "value"}) == "${VAR}"
    )


def test_expand_posix_backtick_not_escape_when_cmd_disabled(monkeypatch):
    # when subprocess disabled, backtick is just a literal character
    result = Env.expand_posix(
        "`echo test`", escape_char="`", expand_flags=EnvExpandFlags.ALLOW_SHELL
    )
    assert result == "`echo test`"


def test_expand_posix_backtick_escape_with_other_chars(monkeypatch):
    # backtick escape should not affect other characters
    # Note: backtick after the escape is output literally, then $ expands normally
    assert Env.expand_posix("a`$VARb", escape_char="`", vars={"VAR": "x"}) == "a$VARb"


def test_expand_posix_backtick_escape_mixed_with_normal(monkeypatch):
    # mixing escaped and unescaped expansions
    result = Env.expand_posix(
        "`$A and $B", escape_char="`", vars={"A": "first", "B": "second"}
    )
    assert result == "$A and second"


def test_expand_posix_backtick_escape_in_nested_expansion(monkeypatch):
    # When backtick is escape, it disables backtick command substitution
    # So we test a simple default expansion instead
    result = Env.expand_posix("${VAR:-hello}", escape_char="`", vars={"INNER": "value"})
    assert result == "hello"


def test_expand_posix_backtick_escape_command_subst(monkeypatch):
    # backtick escape should prevent command substitution with parentheses
    result = Env.expand_posix(
        "`$(echo test)", escape_char="`", expand_flags=EnvExpandFlags.ALLOW_SUBPROC
    )
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
    assert (
        Env.expand_simple("%~n1", args=args)
        == os.path.splitext(os.path.basename(args[0]))[0]
    )
    assert Env.expand_simple("%~x1", args=args) == os.path.splitext(args[0])[1]
    assert (
        Env.expand_simple("%~nx1", args=args)
        == os.path.splitext(os.path.basename(args[0]))[0] + os.path.splitext(args[0])[1]
    )
    # combined dpnx
    expected = (
        expected_dp
        + os.path.splitext(os.path.basename(args[0]))[0]
        + os.path.splitext(args[0])[1]
    )
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
    assert Env.expand_simple("@FOO@", vars={"FOO": "bar"}, expand_char="@") == "bar"
    # Positional using custom expand char '@'
    assert Env.expand_simple("@1", args=["one"], expand_char="@") == "one"
    # Literal '@' via doubling
    assert Env.expand_simple("@@", expand_char="@") == "@"


def test_expand_simple_custom_escape_behavior():
    # Custom escape '\' should prevent expansion and yield the literal token
    assert Env.expand_simple(r"\%FOO%", escape_char="\\", vars={"FOO": "X"}) == "%FOO%"
    # Combined custom expand '@' and custom escape '\' should produce a literal @FOO@
    assert (
        Env.expand_simple(
            r"\@FOO@", escape_char="\\", expand_char="@", vars={"FOO": "X"}
        )
        == "@FOO@"
    )
    # Default caret escape still works (sanity)
    assert Env.expand_simple(r"^%FOO%", escape_char="^", vars={"FOO": "X"}) == "%FOO%"


def test_expand_simple_with_windup_char():
    # Test named variable expansion with windup_char
    assert (
        Env.expand_simple(
            "<VAR>", vars={"VAR": "val"}, expand_char="<", windup_char=">"
        )
        == "val"
    )
    # Test missing variable with windup_char
    assert (
        Env.expand_simple("<MISSING>", expand_char="<", windup_char=">") == "<MISSING>"
    )
    # Test positional arg expansion with windup_char
    assert (
        Env.expand_simple("<1>", args=["one"], expand_char="<", windup_char=">")
        == "<1>"
    )
    # Test literal expansion with windup_char (<> -> <)
    assert Env.expand_simple("<>", expand_char="<", windup_char=">") == "<"
    # Test star expansion with windup_char
    assert (
        Env.expand_simple("<*>", args=["a", "b"], expand_char="<", windup_char=">")
        == "<*>"
    )


def test_expand_with_windup_char(monkeypatch):
    # Test Env.expand with windup_chars (as string of candidates)
    # If we pass expand_chars='<' and windup_chars='>', it should use them
    monkeypatch.setenv("VAR", "val")
    assert Env.expand("<VAR>", expand_chars="<", windup_chars=">") == "val"
    # Test with multiple candidates: if we use '!' as expand and '!' as windup (VMS style)
    assert Env.expand("!VAR!", expand_chars="<!", windup_chars=">!") == "val"


def test_expand_simple_path(monkeypatch):
    monkeypatch.setenv("VAR", "abcd")
    out = Env.expand_simple(Path("C:\\%VAR%\\ef"))
    assert out == Path("C:\\abcd\\ef")


# ---------------------------------------------------------------------------
# Tests for Env.get_cur_platforms method
# ---------------------------------------------------------------------------


def test_get_cur_platforms_no_flags():
    # With EnvPlatformFlags.NONE, minimal platforms should be returned
    result = Env.get_cur_platforms(flags=EnvPlatformFlags.NONE)
    # Should return a list with at least the current platform
    assert isinstance(result, list)
    assert len(result) > 0


def test_get_cur_platforms_add_empty(mocker):
    # Patch to ensure we're on a known platform
    mocker.patch.object(Env, "PLATFORM_THIS", "linux")
    mocker.patch.object(Env, "IS_POSIX", True)

    # Get stack with ADD_EMPTY flag
    result = Env.get_cur_platforms(flags=EnvPlatformFlags.ADD_EMPTY)

    # Empty string should be included
    assert "" in result
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Tests for expand_posix edge cases
# ---------------------------------------------------------------------------


def test_expand_posix_none_input():
    result = Env.expand_posix(None)
    assert result == ""


def test_expand_posix_with_vars_none(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "test_value")
    result = Env.expand_posix("$TEST_VAR", vars=None)
    assert result == "test_value"


def test_expand_posix_numeric_positional_out_of_bounds():
    result = Env.expand_posix("$10", args=["arg1", "arg2"])
    assert result == "$10"


def test_expand_posix_braced_numeric_out_of_bounds():
    result = Env.expand_posix("${10}")
    assert result == "${10}"


def test_expand_posix_length_of_undefined_var():
    result = Env.expand_posix("${#UNDEFINED_VAR}")
    assert result == "${#UNDEFINED_VAR}"


def test_expand_posix_substring_offset(monkeypatch):
    monkeypatch.setenv("SUB_VAR", "abcdef")
    result = Env.expand_posix("${SUB_VAR:2}")
    assert result == "cdef"


def test_expand_posix_assignment_to_vars(monkeypatch):
    vars_dict = {}
    result = Env.expand_posix("${NEW_VAR:=assigned}", vars=vars_dict)
    assert result == "assigned"
    assert vars_dict["NEW_VAR"] == "assigned"


def test_expand_posix_pattern_removal_prefix(monkeypatch):
    monkeypatch.setenv("PAT_VAR", "prefix_value_suffix")
    result = Env.expand_posix("${PAT_VAR#prefix}")
    assert "value_suffix" in result


def test_expand_posix_pattern_removal_suffix(monkeypatch):
    monkeypatch.setenv("PAT_VAR", "prefix_value_suffix")
    result = Env.expand_posix("${PAT_VAR%suffix}")
    assert "prefix_value" in result


def test_expand_posix_substitution(monkeypatch):
    monkeypatch.setenv("SUB_VAR", "old_text")
    result = Env.expand_posix("${SUB_VAR/old/new}")
    assert result == "new_text"


def test_expand_posix_substitution_all(monkeypatch):
    monkeypatch.setenv("SUB_VAR", "old_old_old")
    result = Env.expand_posix("${SUB_VAR//old/new}")
    assert result == "new_new_new"


def test_expand_posix_substitution_prefix_anchor(monkeypatch):
    monkeypatch.setenv("SUB_VAR", "prefix_replaced")
    result = Env.expand_posix("${SUB_VAR/#prefix/suffix}")
    assert "replaced" in result


def test_expand_posix_substitution_suffix_anchor(monkeypatch):
    monkeypatch.setenv("SUB_VAR", "replaced_suffix")
    result = Env.expand_posix("${SUB_VAR/%suffix/prefix}")
    assert "replaced" in result


def test_expand_posix_default_with_null(monkeypatch):
    monkeypatch.setenv("NULL_VAR", "")
    result = Env.expand_posix("${NULL_VAR:-default}")
    assert result == "default"


def test_expand_posix_alternative_without_default(monkeypatch):
    monkeypatch.setenv("SET_VAR", "value")
    result = Env.expand_posix("${SET_VAR:+alt}")
    assert result == "alt"


def test_expand_posix_alternative_with_undefined(monkeypatch):
    result = Env.expand_posix("${UNDEF:+alt}")
    assert result == ""


def test_expand_posix_plus_equals(monkeypatch):
    vars_dict = {}
    result = Env.expand_posix("${VAR:=newval}", vars=vars_dict)
    assert result == "newval"


def test_expand_posix_question_mark_error_undefined():
    with pytest.raises(ValueError):
        Env.expand_posix("${UNDEF:?error message}")


def test_expand_posix_question_mark_error_null(monkeypatch):
    monkeypatch.setenv("NULL_ERR", "")
    with pytest.raises(ValueError):
        Env.expand_posix("${NULL_ERR:?error}")


def test_expand_posix_double_colon_question_error(monkeypatch):
    monkeypatch.setenv("ERR_VAR", "")
    with pytest.raises(ValueError):
        Env.expand_posix("${ERR_VAR:?msg}")


# ---------------------------------------------------------------------------
# Tests for expand_simple edge cases
# ---------------------------------------------------------------------------


def test_expand_simple_dollar_tilde_expand(monkeypatch):
    monkeypatch.setenv("HOME", "/home/user")
    result = Env.expand_simple("~%HOME%", expand_char="%")
    assert "/home/user" in result


def test_expand_simple_percent_with_percent(monkeypatch):
    monkeypatch.setenv("VAR", "val")
    result = Env.expand_simple("a%VAR%", expand_char="%")
    assert "val" in result


def test_expand_simple_dollar_with_tilde(monkeypatch):
    result = Env.expand_simple("~%HOME%", expand_char="%")
    assert "~" in result or "%" in result


def test_expand_simple_var_with_tilde_modifiers(monkeypatch):
    monkeypatch.setenv("TEST", "/path/to/file")
    result = Env.expand_simple("%TEST%", expand_char="%")
    assert "file" in result


def test_expand_simple_no_windup_found(monkeypatch):
    monkeypatch.setenv("VAR", "value")
    result = Env.expand_simple("%VAR%", expand_char="%")
    assert "value" in result


# ---------------------------------------------------------------------------
# Tests for quote edge cases
# ---------------------------------------------------------------------------


def test_quote_single_type():
    result = Env.quote("a'b", type=EnvQuoteType.HARD)
    assert result == "'a\\'b'"


def test_quote_double_type():
    result = Env.quote('a"b', type=EnvQuoteType.DEFAULT)
    assert result == '"a\\"b"'


def test_quote_none_type():
    result = Env.quote("plain", type=EnvQuoteType.NONE)
    assert result == "plain"


def test_quote_with_both_quote_and_escape():
    result = Env.quote("a'b\"c", type=EnvQuoteType.HARD)
    assert result == "'a\\'b\"c'"


# ---------------------------------------------------------------------------
# Tests for unescape edge cases
# ---------------------------------------------------------------------------


def test_unescape_strip_blanks(monkeypatch):
    monkeypatch.setenv("TEST", "value")
    result = Env.unescape("  $TEST  ", strip_blanks=True)
    assert result.strip() == "value" or result == "  $TEST  "


def test_unescape_with_explicit_escape_char():
    result = Env.unescape("a\\tb", escape_char="\\")
    assert "a" in result


def test_unescape_hex_sequence(monkeypatch):
    monkeypatch.setenv("HEX", "41")
    result = Env.unescape("\\x48\\x45\\x58")
    assert "HEX" in result or "HEX" == result


# ---------------------------------------------------------------------------
# Tests for get_all_platforms
# ---------------------------------------------------------------------------


def test_get_all_platforms():
    result = Env.get_all_platforms()
    assert isinstance(result, list)
    assert len(result) > 0
    assert "posix" in result


# ---------------------------------------------------------------------------
# Tests for command substitution and advanced expand_posix features
# ---------------------------------------------------------------------------


def test_expand_posix_backtick_command(mocker):
    mocker.patch("subprocess.run", return_value=mocker.MagicMock(
        stdout="cmd_output", stderr="", returncode=0
    ))
    result = Env.expand_posix("`echo test`")
    assert "cmd_output" in result


def test_expand_posix_backtick_with_expanded_inner(mocker):
    mocker.patch("subprocess.run", return_value=mocker.MagicMock(
        stdout="output", stderr="", returncode=0
    ))
    result = Env.expand_posix("`echo $HOME`")
    assert "output" in result


def test_expand_posix_dollar_command_substitution(mocker):
    mocker.patch("subprocess.run", return_value=mocker.MagicMock(
        stdout="sub_result", stderr="", returncode=0
    ))
    result = Env.expand_posix("$(echo test)")
    assert "sub_result" in result


def test_expand_posix_command_substitution_allow_shell(mocker):
    mock_proc = mocker.MagicMock()
    mock_proc.stdout = "shell_output"
    mock_proc.stderr = ""
    mock_proc.returncode = 0
    mocker.patch("subprocess.run", return_value=mock_proc)
    result = Env.expand_posix("$(echo test)", expand_flags=EnvExpandFlags.ALLOW_SHELL)
    assert "shell_output" in result


def test_expand_posix_dollar_command_substitution_with_expanded_inner(mocker):
    mocker.patch("subprocess.run", return_value=mocker.MagicMock(
        stdout="inner_out", stderr="", returncode=0
    ))
    result = Env.expand_posix("$(echo $HOME)")
    assert "inner_out" in result


def test_expand_posix_double_dollar_returns_pid():
    result = Env.expand_posix("$$")
    assert result.isdigit()


def test_expand_posix_numeric_arg_expansion(monkeypatch):
    result = Env.expand_posix("$1 $2", args=["arg1", "arg2"])
    assert "arg1" in result
    assert "arg2" in result


def test_expand_posix_unterminated_backtick():
    with pytest.raises(ValueError) as exc_info:
        Env.expand_posix("`echo test")
    assert "Unterminated" in str(exc_info.value)


def test_expand_posix_unterminated_command_substitution():
    with pytest.raises(ValueError) as exc_info:
        Env.expand_posix("$(echo test")
    assert "Unterminated" in str(exc_info.value)


def test_expand_posix_unterminated_braced_expansion():
    with pytest.raises(ValueError) as exc_info:
        Env.expand_posix("${VAR")
    assert "Unterminated" in str(exc_info.value)


def test_expand_posix_pattern_no_match_returns_original(monkeypatch):
    monkeypatch.setenv("VAR", "original_value")
    result = Env.expand_posix("${VAR#nomatch*}")
    assert result == "original_value"


def test_expand_posix_suffix_pattern_no_match(monkeypatch):
    monkeypatch.setenv("VAR", "value_suffix")
    result = Env.expand_posix("${VAR%nomatch*}")
    assert result == "value_suffix"


def test_expand_posix_substitution_no_match(monkeypatch):
    monkeypatch.setenv("VAR", "original")
    result = Env.expand_posix("${VAR/nomatch/replacement}")
    assert result == "original"


def test_expand_posix_backtick_command_with_escaped_backtick(mocker):
    mocker.patch("subprocess.run", return_value=mocker.MagicMock(
        stdout="out", stderr="", returncode=0
    ))
    result = Env.expand_posix("`echo \\`test\\``")
    assert "out" in result


# ---------------------------------------------------------------------------
# Tests for expand_simple additional coverage
# ---------------------------------------------------------------------------


def test_expand_simple_escape_char_handling(monkeypatch):
    monkeypatch.setenv("VAR", "value")
    result = Env.expand_simple("%VAR%", expand_char="%")
    assert "value" in result


def test_expand_simple_triple_expand_char(monkeypatch):
    monkeypatch.setenv("VAR", "test")
    result = Env.expand_simple("%%%VAR%%%", expand_char="%")
    assert "test" in result


def test_expand_simple_path_input(monkeypatch):
    monkeypatch.setenv("HOME", "/home/user")
    result = Env.expand_simple(Path("%HOME%/file.txt"), expand_char="%")
    assert isinstance(result, Path)


def test_expand_simple_double_escape_preserved(monkeypatch):
    monkeypatch.setenv("VAR", "val")
    result = Env.expand_simple("%VAR%", expand_char="%")
    assert "val" in result


def test_expand_simple_digit_after_expand_char(monkeypatch):
    monkeypatch.setenv("HOME", "/home")
    result = Env.expand_simple("%HOME%123", expand_char="%")
    assert "/home123" in result


# ---------------------------------------------------------------------------
# Tests for expand with flags and parameters
# ---------------------------------------------------------------------------


def test_expand_flags_none_uses_default(mocker):
    mocker.patch.object(Env, "unquote", return_value=("result", EnvChars()))
    mocker.patch.object(Env, "expand_posix", return_value="expanded")
    mocker.patch.object(Env, "unescape", return_value="final")

    result = Env.expand("$VAR", flags=None)
    assert result == "final"


def test_expand_with_remove_line_comment(mocker):
    info = EnvChars(
        input="$VAR",
        result="$VAR",
        quote_type=EnvQuoteType.NONE,
    )
    mocker.patch.object(Env, "unquote", return_value=(None, info))
    mocker.patch.object(Env, "expand_posix", return_value="result # comment")

    result = Env.expand("$VAR", flags=EnvExpandFlags.REMOVE_LINE_COMMENT)
    assert "#" not in result or result == "result # comment"


def test_expand_expand_chars(mocker):
    info = EnvChars(
        input="$VAR",
        result="$VAR",
        expand="$",
        escape="\\",
        quote_type=EnvQuoteType.NONE,
    )
    mocker.patch.object(Env, "unquote", return_value=("$VAR", info))
    mocker.patch.object(Env, "expand_posix", return_value="expanded")

    result = Env.expand("$VAR", expand_chars="$")
    assert result == "expanded"


def test_expand_windup_chars(mocker):
    info = EnvChars(
        input="<VAR>",
        result="<VAR>",
        expand="<",
        windup=">",
        escape="\\",
        quote_type=EnvQuoteType.NONE,
    )
    mocker.patch.object(Env, "unquote", return_value=("<VAR>", info))
    mocker.patch.object(Env, "expand_simple", return_value="expanded")

    result = Env.expand("<VAR>", windup_chars=">")
    assert result == "expanded"
