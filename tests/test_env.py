#!/usr/bin/env pytest

###############################################################################
# envara (C) Alexander Iurovetski 2026
#
# Tests for Env
###############################################################################

import os
import re
from typing import Final
import pytest

from env import Env, EnvExpandFlags, EnvQuoteType
from env_expand_info import EnvExpandInfo
from env_expand_info_type import EnvExpandInfoType
from env_platform_stack_flags import EnvPlatformStackFlags
from env_unquote_info import EnvUnquoteInfo

###############################################################################

msdos: Final[EnvExpandInfo] = Env._Env__msdos_info
posix: Final[EnvExpandInfo] = Env._Env__posix_info
powsh: Final[EnvExpandInfo] = Env._Env__powsh_info
vms: Final[EnvExpandInfo] = Env._Env__vms_info

###############################################################################


class TestExpand:
    """Test suite for Env.expand method"""

    @pytest.mark.parametrize(
        "platform, input, env, args, flags, expected",
        [
            ("", "", {}, [], EnvExpandFlags.NONE, ""),
            ("", "a$1b", {}, ["x"], EnvExpandFlags.NONE, "axb"),
            ("", "a${1}b", None, ["x"], EnvExpandFlags.NONE, "axb"),
            ("", "a$a${b}", {"a": "efg1"}, [], EnvExpandFlags.NONE, "aefg1${b}"),
            ("", "a#$a${b}", {"a": "efg1"}, [], EnvExpandFlags.REMOVE_LINE_COMMENT, "a"),
            (
                "posix",
                "'a $2 $a \\${b}'",
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.UNESCAPE
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a $2 $a \\${b}",
            ),
            (
                "posix",
                '"a $2 ~ $a \\${b}"',
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.UNESCAPE
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a A2 ~ efg1 ${b}",
            ),
            (
                "windows",
                "a %2 $a #${b}",
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.UNESCAPE
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a A2 efg1",
            ),
            (
                "windows",
                '"a $20 ~ $a \\${b}"',
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.UNESCAPE
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a $20 ~ efg1 ${b}",
            ),
            (
                "posix",
                '"a $1 ~ $xyz \\${b}"',
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.UNESCAPE
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a A1 ~ $xyz ${b}",
            ),
            (
                "posix",
                "'a $2 $a #${b}'",
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.UNESCAPE
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                "a $2 $a #${b}",
            ),
            (
                "posix",
                "~/abc",
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.UNESCAPE
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                os.path.expanduser(f"~{os.sep}abc"),
            ),
            (
                "posix",
                f"~{os.sep}$a{os.sep}${{b}}",
                {"a": "efg1", "b": "xx"},
                ["A1", "A2"],
                EnvExpandFlags.REMOVE_LINE_COMMENT
                | EnvExpandFlags.UNESCAPE
                | EnvExpandFlags.REMOVE_QUOTES
                | EnvExpandFlags.SKIP_SINGLE_QUOTED,
                os.path.expanduser("~") + f"{os.sep}efg1{os.sep}xx",
            ),
        ],
    )
    def test_expand(self, platform, input, env, args, flags, expected):
        # Arrange
        keys_to_clear = list((env or {}).keys())
        for k, v in (env or {}).items():
            os.environ[k] = v

        if (platform == "posix"):
            Env.IS_POSIX = True
            Env.IS_WINDOWS = False
        elif (platform == "windows"):
            Env.IS_POSIX = False
            Env.IS_WINDOWS = True
        else:
            Env.IS_POSIX = False
            Env.IS_WINDOWS = False

        # Call the method
        result = Env.expand(input, args, flags)

        # Verify result matches expected
        assert result == expected

        # Cleanup
        for k in keys_to_clear:
            os.environ.pop(k, None)


###############################################################################


class TestExpandArgs:
    """Test suite for Env.expand_args method"""

    @pytest.mark.parametrize(
        "input, args, expected",
        [
            (None, [], ""),
            ("", [], ""),
            ("a b c", [], "a b c"),
            ("a$1 b ${2}9", [], "a$1 b ${2}9"),
            ("a$1 b ${2}9", ["A1"], "aA1 b ${2}9"),
            ("a$1 b ${2}9", ["A1", "A2"], "aA1 b A29"),
            ("a$1 b $29", ["A1", "A2"], "aA1 b $29"),
        ],
    )
    def test_expand_args(self, input, args, expected):

        # Call the method
        result = Env.expand_args(input, args)

        # Verify result matches expected
        assert result == expected


###############################################################################


class TestGetPlatformStack:
    """Test suite for Env.expandargs method"""

    @pytest.mark.parametrize(
        "type, platform, flags, prefix, suffix, expected",
        [
            ("P", "linux3", EnvPlatformStackFlags.NONE, None, None, "posix, linux"),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_EMPTY,
                None,
                None,
                ", posix, linux",
            ),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_ANY,
                None,
                None,
                "any, posix, linux",
            ),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_ANY | EnvPlatformStackFlags.ADD_EMPTY,
                None,
                None,
                ", any, posix, linux",
            ),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_CURRENT,
                None,
                None,
                "posix, linux, linux3",
            ),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, linux, linux3",
            ),
            (
                "P",
                "linux3",
                EnvPlatformStackFlags.ADD_MAX,
                ".",
                ".env",
                ".env, .any.env, .posix.env, .linux.env, .linux3.env",
            ),
            (
                "P",
                "darwin",
                EnvPlatformStackFlags.ADD_MAX,
                ".",
                ".env",
                ".env, .any.env, .posix.env, .bsd.env, .darwin.env, .macos.env",
            ),
            (
                "P",
                "macos",
                EnvPlatformStackFlags.ADD_MAX,
                ".",
                ".env",
                ".env, .any.env, .posix.env, .bsd.env, .darwin.env, .macos.env",
            ),
            (
                "P",
                "ios",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, bsd, ios",
            ),
            (
                "P",
                "aix5",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, aix, aix5",
            ),
            (
                "P",
                "cygwin",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, cygwin",
            ),
            (
                "P",
                "msys",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, msys",
            ),
            (
                "P",
                "java",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, posix, java",
            ),
            (
                "W",
                "java",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, windows, java",
            ),
            ("", "vms", EnvPlatformStackFlags.ADD_MAX, None, None, ", any, vms"),
            (
                "W",
                "windows",
                EnvPlatformStackFlags.ADD_MAX,
                None,
                None,
                ", any, windows",
            ),
        ],
    )
    def test_get_platform_stack(
        self, type, platform, flags, prefix, suffix, expected
    ):
        Env.IS_POSIX = True if (type == "P") else False
        Env.IS_WINDOWS = True if (type == "W") else False
        Env.IS_VMS = True if (type == "V") else False
        Env.PLATFORM_THIS = platform
        Env._Env__platform_map[".+"] = [platform]

        # Call the method
        result: list[str] = Env.get_platform_stack(flags, prefix, suffix)

        # Verify result matches expected
        assert ", ".join(result) == expected


###############################################################################

class TestParseEscapes:
    """Test suite for Env.__parse_escapes method"""

    @pytest.mark.parametrize(
        "regex, group_count, min_escape_count, input, exp_escapes, exp_no_action",
        [
            (posix.RE_VAR, 4, 0, "", "", ""),
            (posix.RE_VAR, 4, 0, "abc", "", "abc"),
            (posix.RE_VAR, 4, 0, f"\\$Key", "", "$Key"),
            (posix.RE_VAR, 4, 0, f"\\\\\\$Key", "\\", f"\\$Key"),
            (posix.RE_VAR, 4, 0, "`$Key", "", ""),
            (posix.RE_VAR, 4, 0, "```$Key", "", ""),
            (posix.RE_ESC, 4, 1, "", "", ""),
            (posix.RE_ESC, 4, 1, "abc", "", "abc"),
            (posix.RE_ESC, 4, 1, "\\x12", "", ""),
            (posix.RE_ESC, 4, 1, f"\\\\x12", "\\", f"\\x12"),

            (powsh.RE_VAR, 4, 0, "", "", ""),
            (powsh.RE_VAR, 4, 0, "abc", "", "abc"),
            (powsh.RE_VAR, 4, 0, "`$Key", "", "$Key"),
            (powsh.RE_VAR, 4, 0, "```$Key", "`", "`$Key"),
            (powsh.RE_VAR, 4, 0, "^$Key", "", ""),
            (powsh.RE_VAR, 4, 0, "^^^$Key", "", ""),
            (powsh.RE_ESC, 4, 1, "", "", ""),
            (powsh.RE_ESC, 4, 1, "abc", "", "abc"),
            (powsh.RE_ESC, 4, 1, "`x12", "", ""),
            (powsh.RE_ESC, 4, 1, "``x12", "`", "`x12"),

            (msdos.RE_VAR, 4, 0, "", "", ""),
            (msdos.RE_VAR, 4, 0, "abc", "", "abc"),
            (msdos.RE_VAR, 4, 0, "^%Key%", "", "%Key%"),
            (msdos.RE_VAR, 4, 0, "^^^%Key%", "^", "^%Key%"),
            (msdos.RE_VAR, 4, 0, "`%Key%", "", ""),
            (msdos.RE_VAR, 4, 0, "```%Key%", "", ""),
            (msdos.RE_ESC, 4, 1, "", "", ""),
            (msdos.RE_ESC, 4, 1, "abc", "", "abc"),
            (msdos.RE_ESC, 4, 1, "^x12", "", ""),
            (msdos.RE_ESC, 4, 1, "^^x12", "^", "^x12"),

            (vms.RE_VAR, 4, 0, "", "", ""),
            (vms.RE_VAR, 4, 0, "abc", "", "abc"),
            (vms.RE_VAR, 4, 0, "^'Key'", "", "'Key'"),
            (vms.RE_VAR, 4, 0, "^^^'Key'", "^", "^'Key'"),
            (vms.RE_VAR, 4, 0, "$'Key'", "", ""),
            (vms.RE_VAR, 4, 0, "$$$'Key'", "", ""),
            (vms.RE_ESC, 4, 1, "", "", ""),
            (vms.RE_ESC, 4, 1, "abc", "", "abc"),
            (vms.RE_ESC, 4, 1, "^x12", "", ""),
            (vms.RE_ESC, 4, 1, "^^x12", "^", "^x12"),
        ],
    )
    def test_parse_escapes(
        self, regex, min_escape_count, group_count, input, exp_escapes,
        exp_no_action
    ):
        # Arrange
        match = regex.search(input)

        # Call the method
        groups, escapes, no_action = \
            Env._Env__parse_escapes(input, match, min_escape_count)
        group_count = len(groups) if (groups) else 0

        # Verify result matches expected
        assert group_count == group_count
        assert escapes == exp_escapes
        assert no_action == exp_no_action


###############################################################################


class TestQuote:
    """Test suite for Env.quote method"""

    @pytest.mark.parametrize(
        "input, type, expected",
        [
            (None, EnvQuoteType.NONE, ""),
            (None, EnvQuoteType.SINGLE, "''"),
            (None, EnvQuoteType.DOUBLE, '""'),
            ("", EnvQuoteType.NONE, ""),
            ("", EnvQuoteType.SINGLE, "''"),
            ("", EnvQuoteType.DOUBLE, '""'),
            (" a \"b'  c   ", EnvQuoteType.NONE, " a \"b'  c   "),
            (" a \"b'  c   ", EnvQuoteType.SINGLE, "' a \"b\\'  c   '"),
            (" a \\\"b\\'  c   ", EnvQuoteType.SINGLE, "' a \\\\\"b\\\\\\'  c   '"),
            (" a \\\"b\\'  c   ", EnvQuoteType.DOUBLE, '" a \\\\\\"b\\\\\'  c   "'),
        ],
    )
    def test_quote(self, input, type, expected):
        # Call the method
        result = Env.quote(input, type)

        # Verify result matches expected
        assert result == expected


###############################################################################


class TestUnescape:
    """Test suite for Env.decode_escaped method"""

    @pytest.mark.parametrize(
        "input, escape, expected",
        [
            (None, None, ""),
            ("", "", ""),
            ("A b c", None, "A b c"),
            ("A\\tb\\tc", "", "A\tb\tc"),
            ("A\\ \\N\\+\\u0042b\\a\\x41c\\x42", "\\", "A N+Bb\aAcB"),

            (None, None, ""),
            ("", "", ""),
            ("A b c", "`", "A b c"),
            ("A`tb`tc", "`", "A\tb\tc"),
            ("A` `N`+`u0042b`a`x41c`x42", "`", "A N+Bb\aAcB"),

            (None, None, ""),
            ("", "", ""),
            ("A b c", "^", "A b c"),
            ("A^tb^tc", "^", "A\tb\tc"),
            ("A^ ^N^+^u0042b^a^x41c^x42", "^", "A N+Bb\aAcB"),
        ],
    )
    def test_unescape(self, input, escape, expected):
        # Call the method
        result = Env.unescape(input, escape)

        # Verify result matches expected
        assert result == expected

    @pytest.mark.parametrize(
        "input, escape, exp_beg_pos, exp_bad",
        [
            ("A\\", "\\", 1, "\\"),
            ("\\xG", "\\", 0, "\\x"),
            ("\\x0", "\\", 0, "\\x0"),
            ("\\x0g", "\\", 0, "\\x0"),
            ("\\u012g", "\\", 0, "\\u012"),
            ("abc \\xG", "\\", 4, "\\x"),
            ("abc \\x0", "\\", 4, "\\x0"),
            ("abc \\x0g", "\\", 4, "\\x0"),
            ("abc \\u012g", "\\", 4, "\\u012"),

            ("A^", "^", 1, "^"),
            ("^xG", "^", 0, "^x"),
            ("^x0", "^", 0, "^x0"),
            ("^x0g", "^", 0, "^x0"),
            ("^u012g", "^", 0, "^u012"),
            ("abc ^xG", "^", 4, "^x"),
            ("abc ^x0", "^", 4, "^x0"),
            ("abc ^x0g", "^", 4, "^x0"),
            ("abc ^u012g", "^", 4, "^u012"),
        ],
    )
    def test_unescape_bad(self, input, escape, exp_beg_pos, exp_bad):
        # Call the method
        with pytest.raises(ValueError) as ex:
            Env.unescape(input, escape)

        # Verify result matches expected
        assert f"[{exp_beg_pos}]: \"{exp_bad}\" in \"{input}\"" in str(ex.value)


###############################################################################


class TestUnquote:
    """Test suite for Env.unquote method"""

    @pytest.mark.parametrize(
        "input, unescape, escapes, strip_spaces, hard_quotes, stoppers, exp_result, exp_quote_type, exp_escape, exp_expand",
        [
            (' Abc # def', False, "\\", False, None, "#", ' Abc ', EnvQuoteType.NONE, "", ""),
            (' Abc # def', True, "\\", False, None, "#", ' Abc ', EnvQuoteType.NONE, "", ""),
            (' Abc \\x41\\t\\n', False, "\\", False, None, None, ' Abc \\x41\\t\\n', EnvQuoteType.NONE, "\\", ""),
            (' Abc \\u0041\\t\\n', True, "\\", True, None, None, 'Abc A', EnvQuoteType.NONE, "\\", ""),
            ('" Abc \\u0041\\t\\n"', True, "\\", False, None, None, ' Abc A\t\n', EnvQuoteType.DOUBLE, "\\", ""),
            ('" Abc \\u0041\\t\\n"', True, "\\", True, None, None, ' Abc A\t\n', EnvQuoteType.DOUBLE, "\\", ""),
        ],
    )
    def test_unquote(
        self, input, unescape, escapes, strip_spaces, hard_quotes, stoppers,
        exp_result, exp_quote_type, exp_escape, exp_expand
    ):
        # Call the method
        result, info = Env.unquote(
            input,
            unescape=unescape,
            escapes=escapes,
            strip_spaces=strip_spaces,
            hard_quotes=hard_quotes,
            stoppers=stoppers
        )

        # Verify result matches expected
        assert info.input == (input or "")
        assert info.result == (result or "")
        assert info.result == (exp_result or "")
        assert info.quote_type == (exp_quote_type)
        assert info.escape == (exp_escape or "")
        assert info.expand == (exp_expand or "")


###############################################################################


class TestUnquoteOnly:
    """Test suite for Env.unquote_only method"""

    @pytest.mark.parametrize(
        "input, escapes, strip_spaces, hard_quotes, stoppers, exp_result, exp_quote_type, exp_escape, exp_expand",
        [
            (None, None, False, None, None, "", EnvQuoteType.NONE, "", ""),
            (None, None, True, None, None, "", EnvQuoteType.NONE, "", ""),
            ("", None, False, None, None, "", EnvQuoteType.NONE, "", ""),
            ("", None, True, None, None, "", EnvQuoteType.NONE, "", ""),
            (" \t ", None, False, None, None, " \t ", EnvQuoteType.NONE, "", ""),
            (" \t ", None, True, None, None, "", EnvQuoteType.NONE, "", ""),
            (' \n " \t " \n ', None, False, None, None, ' \n " \t " \n ', EnvQuoteType.NONE, "", ""),
            (' \n " \t " \n ', None, True, None, None, ' \t ', EnvQuoteType.DOUBLE, "", ""),
            ('"\t\\""', "\\", False, None, None, '\t\\"', EnvQuoteType.DOUBLE, "\\", ""),
            (' A\"', "\\", False, None, None, ' A\"', EnvQuoteType.NONE, "", ""),
            (' A\"', "\\", True, None, None, 'A\"', EnvQuoteType.NONE, "", ""),
            (' A\"', "\\", True, True, None, 'A\"', EnvQuoteType.NONE, "", ""),
            ('"\\""', "\\", True, None, None, '\\"', EnvQuoteType.DOUBLE, "\\", ""),
            ('"\\\\""', "\\", True, None, None, '\\\\', EnvQuoteType.DOUBLE, "\\", ""),
            ('"\\\\\\""', "\\", True, None, None, '\\\\\\"', EnvQuoteType.DOUBLE, "\\", ""),
            ("'\\\\\\\"'", "\\", True,None, None, '\\\\\\\"', EnvQuoteType.SINGLE, "", ""),
            ('"\\\\\\\\""', "\\", True, '"', None, '\\\\\\\\', EnvQuoteType.DOUBLE, "", ""),
            (' Abc # def', "\\", False, None, "#", ' Abc ', EnvQuoteType.NONE, "", ""),
            (' Abc # def', "\\", True, None, "#", 'Abc', EnvQuoteType.NONE, "", ""),
            (' "Ab;c" # def', "\\", False, None, "#;", ' "Ab', EnvQuoteType.NONE, "", ""),
            (' "Ab;c" # def', "\\", True, None, "#;", 'Ab;c', EnvQuoteType.DOUBLE, "", ""),
            (' "Ab#c" ; def', "\\", False, None, "#;", ' "Ab', EnvQuoteType.NONE, "", ""),
            (' "Ab#c" ; def', "\\", True, None, "#;", 'Ab#c', EnvQuoteType.DOUBLE, "", ""),
            (' Ab\\#c # def', "\\", True, None, "#;", 'Ab\\#c', EnvQuoteType.NONE, "\\", ""),
            (' $Abc %def% ', "\\", False, None, "#", ' $Abc %def% ', EnvQuoteType.NONE, "", "$"),
            ('"`""', "`", False, None, None, '`"', EnvQuoteType.DOUBLE, "`", ""),
            ('"`""', "`", True, None, None, '`"', EnvQuoteType.DOUBLE, "`", ""),
            ('"``""', "`", True, None, None, '``', EnvQuoteType.DOUBLE, "`", ""),
            ('"```""', "`", True, None, None, '```"', EnvQuoteType.DOUBLE, "`", ""),
            ("'```\"'", "`", True, None, None, '```"', EnvQuoteType.SINGLE, "", ""),
            ('"````""', "`", True, '"', None, '````', EnvQuoteType.DOUBLE, "", ""),
        ],
    )
    def test_unquote_only(
        self, input, escapes, strip_spaces, hard_quotes, stoppers,
        exp_result, exp_quote_type, exp_escape, exp_expand
    ):
        # Call the method
        actual = Env.unquote_only(
            input,
            escapes=escapes,
            strip_spaces=strip_spaces,
            hard_quotes=hard_quotes,
            stoppers=stoppers
        )

        # Verify result matches expected
        assert actual.input == (input or "")
        assert actual.result == (exp_result or "")
        assert actual.quote_type == (exp_quote_type)
        assert actual.escape == (exp_escape or "")
        assert actual.expand == (exp_expand or "")

    @pytest.mark.parametrize(
        "input, escapes, strip_spaces, hard_quotes, stoppers, expected",
        [
            (' "', "\\", True, None, None, 'Unterminated'),
            (' \t"\\', "\\", True, None, None, 'dangling'),
            (' \t \\"\\\\\\', "\\", True, None, None, 'dangling'),
            ('" \t \\"\\\\#\\"', "\\", True, None, "#", 'Unterminated'),
            ('" \t \\"\\\\#\\', "\\", True, None, "#", 'dangling'),

            (' "', "`", True, None, None, 'Unterminated'),
            (' \t"`', "`", True, None, None, 'dangling'),
            (' \t `"```', "`", True, None, None, 'dangling'),
            ('" \t `"``#`"', "`", True, None, "#", 'Unterminated'),
            ('" \t `"``#`', "`", True, None, "#", 'dangling'),
        ],
    )
    def test_unquote_only_bad(
        self, input, escapes, strip_spaces, hard_quotes, stoppers, expected
    ):
        # Call the method
        with pytest.raises(ValueError) as ex:
            Env.unquote_only(
                input,
                escapes=escapes,
                strip_spaces=strip_spaces,
                hard_quotes=hard_quotes,
                stoppers=stoppers
            )

        # Verify result matches expected
        assert expected in str(ex.value)


###############################################################################
