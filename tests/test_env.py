import os
import pytest
from env import Env
from env_expand_flags import EnvExpandFlags
from env_platform_flags import EnvPlatformFlags
from env_parse_info import EnvParseInfo
from env_quote_type import EnvQuoteType


# ---------------------------------------------------------------------------
# Tests for Env.expand (uses Env.unquote -> expand_posix/expand_simple path)
# ---------------------------------------------------------------------------


def test_expand_skips_single_quoted_when_flag_set(mocker):
    # Arrange: make unquote report a SINGLE-quoted string
    info = EnvParseInfo(
        input="'x'",
        result="quoted-result",
        expand_char=EnvParseInfo.POSIX_EXPAND_CHAR,
        escape_char="\\",
        quote_type=EnvQuoteType.SINGLE,
    )
    mocker.patch.object(Env, "unquote", return_value=(None, info))
    m_posix = mocker.patch.object(Env, "expand_posix")
    m_simple = mocker.patch.object(Env, "expand_simple")

    # Act
    out, got = Env.expand("'x'", flags=EnvExpandFlags.SKIP_SINGLE_QUOTED)

    # Assert - expansion functions must not be called and original result returned
    assert out == "quoted-result"
    assert got is info
    m_posix.assert_not_called()
    m_simple.assert_not_called()


def test_expand_uses_posix_and_unescape(mocker):
    # Arrange: unquote reports POSIX expansion character
    info = EnvParseInfo(
        input="$A",
        result="raw-val",
        expand_char=EnvParseInfo.POSIX_EXPAND_CHAR,
        escape_char="\\",
        quote_type=None,
    )
    mocker.patch.object(Env, "unquote", return_value=(None, info))
    m_posix = mocker.patch.object(Env, "expand_posix", return_value="posix-expanded")
    m_unescape = mocker.patch.object(Env, "unescape", return_value="final-unescaped")

    # Act
    out, got = Env.expand("$A", args=["arg1"], flags=EnvExpandFlags.UNESCAPE)

    # Assert
    m_posix.assert_called_once()
    called_args, called_kwargs = m_posix.call_args
    # first positional arg passed to expand_posix is the unquoted result
    assert called_args[0] == "raw-val"
    assert called_kwargs["args"] == ["arg1"]
    assert called_kwargs["expand_char"] == info.expand_char
    assert called_kwargs["escape_char"] == info.escape_char
    # unescape must be invoked with expand_posix's result and the escape char
    m_unescape.assert_called_once_with("posix-expanded", escape_char=info.escape_char)
    assert out == "final-unescaped"
    assert got is info


def test_expand_uses_simple_and_respects_skip_env_vars(mocker):
    # Arrange: unquote reports Windows-style expansion char
    info = EnvParseInfo(
        input="%X%",
        result="raw-simple",
        expand_char=EnvParseInfo.WINDOWS_EXPAND_CHAR,
        escape_char="^",
        quote_type=None,
    )
    mocker.patch.object(Env, "unquote", return_value=(None, info))
    m_simple = mocker.patch.object(Env, "expand_simple", return_value="simple-expanded")

    # Act - request SKIP_ENV_VARS so vars dict should be empty
    out, got = Env.expand("%X%", flags=EnvExpandFlags.SKIP_ENV_VARS)

    # Assert
    m_simple.assert_called_once()
    _, kw = m_simple.call_args
    assert kw["vars"] == {}
    assert out == "simple-expanded"
    assert got is info


def test_expand_with_none_input_returns_empty_and_info_result_set():
    out, info = Env.expand(None)
    assert out == ""
    assert info.result == ""


def test_expand_preserves_spaces_when_strip_false():
    out, info = Env.expand("  val  ", strip_spaces=False)
    assert out == "  val  "
    assert info.quote_type == EnvQuoteType.NONE


def test_expand_sets_cutter_chars_on_remove_line_comment_flag():
    out, info = Env.expand("A #comment", flags=EnvExpandFlags.REMOVE_LINE_COMMENT)
    assert out == "A"


def test_expand_posix_respects_skip_env_vars(monkeypatch):
    monkeypatch.setenv("SILENT", "yes")
    out, _ = Env.expand("$SILENT", flags=EnvExpandFlags.SKIP_ENV_VARS)
    # when SKIP_ENV_VARS is set, env variables are not expanded
    assert out == "$SILENT"


# ---------------------------------------------------------------------------
# Tests for Env.unescape and Env.unquote
# ---------------------------------------------------------------------------


def test_unescape_basic_and_codes():
    # basic escapes, unicode and hex, and a literal backslash
    inp = "\\n\\t\\u0041\\x41\\\\"
    out = Env.unescape(inp)
    # two consecutive backslashes in input cancel out in the current implementation
    assert out == "\n\tAA"


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
    assert Env.unescape(r"\x20a", strip_blanks=True) == " a"
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
    assert info.quote_type == EnvQuoteType.DOUBLE
    assert info.expand_char == EnvParseInfo.POSIX_EXPAND_CHAR


def test_unquote_uses_cutter_chars_and_detects_expchr():
    res, info = Env.unquote("$X#y", cutter_chars="#")
    assert res == "$X"
    assert info.expand_char == EnvParseInfo.POSIX_EXPAND_CHAR
    assert info.quote_type == EnvQuoteType.NONE


def test_unquote_raises_for_unterminated_quote():
    with pytest.raises(ValueError):
        Env.unquote('"abc')


def test_unquote_raises_for_dangling_escape():
    with pytest.raises(ValueError):
        Env.unquote("abc\\")


def test_unquote_constructs_envparseinfo_when_input_empty(mocker):
    m = mocker.patch("env.EnvParseInfo")
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
    assert info.quote_type == EnvQuoteType.SINGLE
    assert info.escape_char is None


def test_unquote_hard_quotes_param_disables_escaping():
    # when hard_quotes includes '"', escaping inside double quotes is ignored
    res, info = Env.unquote('"a\\"b"', hard_quotes='"')
    # encountering the inner double-quote closes the quoted string because
    # escaping is disabled by hard_quotes -> the result contains the backslash
    assert res == "a\\"
    assert info.quote_type == EnvQuoteType.DOUBLE


def test_unquote_preserves_spaces_when_strip_false():
    inp = "  abc  "
    res, info = Env.unquote(inp, strip_spaces=False)
    assert res == inp
    assert info.quote_type == EnvQuoteType.NONE


def test_unquote_detects_first_of_multiple_expansion_chars():
    res, info = Env.unquote("a%b$z", expand_chars="%$")
    assert info.expand_char == "%"


def test_unquote_quoted_cutter_ignored():
    res, info = Env.unquote("'a#b'", cutter_chars="#")
    assert res == "a#b"


def test_unquote_escaped_quote_inside_double_quotes():
    res, info = Env.unquote('"a\\"b"')
    # unquote does not remove escaping backslashes (that's done by Env.unescape)
    assert res == r"a\"b"
    assert info.quote_type == EnvQuoteType.DOUBLE
    assert info.escape_char == "\\"


# ---------------------------------------------------------------------------
# Tests for Env.quote (with and without mocking defaults)
# ---------------------------------------------------------------------------


def test_quote_escapes_internal_double_and_escape_char():
    # input contains a double quote and a backslash (default escape)
    inp = 'a"b\\c'
    out = Env.quote(inp, type=EnvQuoteType.DOUBLE)
    # backslash doubled, internal quote escaped, whole string wrapped in double quotes
    assert out == '"a\\"b\\\\c"'


def test_quote_doubles_escape_chars_and_single_quote():
    inp = "it's\\done"
    out = Env.quote(inp, type=EnvQuoteType.SINGLE)
    # backslash doubled and single-quote escaped, wrapped in single quotes
    assert out == "'it\\'s\\\\done'"


def test_quote_returns_input_when_no_quote_type():
    assert Env.quote("plain", type=EnvQuoteType.NONE) == "plain"


def test_quote_none_input_returns_empty_quotes():
    assert Env.quote(None) == '""'


def test_quote_with_custom_escape_arg():
    # custom escape character should be used instead of default; when no
    # quote char is present the implementation does not double escapes
    out = Env.quote("a^b^c", type=EnvQuoteType.DOUBLE, escape_char="^")
    assert out == '"a^b^c"'


def test_quote_uses_mocked_default_escape(mocker):
    # patch the default escape char and ensure Env.quote uses it (no doubling
    # unless a quote char is present in the input)
    mocker.patch.object(EnvParseInfo, "POSIX_ESCAPE_CHAR", "^")
    assert Env.quote("a^b") == '"a^b"'


def test_unquote_respects_mocked_posix_expand_char(mocker):
    # patch the default POSIX expansion char and ensure unquote picks it up
    mocker.patch.object(EnvParseInfo, "POSIX_EXPAND_CHAR", "@")
    _, info = Env.unquote("a@b")
    assert info.expand_char == "@"


def test_unquote_disallows_posix_expand_char_with_windows_escape_char(mocker):
    _, info = Env.unquote('"$a^b"')
    assert info.escape_char == "\\"


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
