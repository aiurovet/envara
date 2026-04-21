import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envara.env import Env, EnvChars, EnvExpandFlags, EnvPlatformFlags, EnvQuoteType


class TestEnvUnquote:
    """Tests for Env.unquote() - Called during expand"""
    
    @pytest.mark.parametrize("input_str,flags,chars,expected,expected_qt", [
        ("hello", EnvExpandFlags.NONE, EnvChars.POSIX.copy_with(), "hello", EnvQuoteType.NONE),
        ("", EnvExpandFlags.NONE, EnvChars.POSIX.copy_with(), "", EnvQuoteType.NONE),
        ("'hello'", EnvExpandFlags.NONE, EnvChars.POSIX.copy_with(), "hello", EnvQuoteType.HARD),
        ("$VAR", EnvExpandFlags.NONE, EnvChars.POSIX.copy_with(), "$VAR", EnvQuoteType.NONE),
        ("${VAR}", EnvExpandFlags.NONE, EnvChars.POSIX.copy_with(), "${VAR}", EnvQuoteType.NONE),
        ("%VAR%", EnvExpandFlags.NONE, EnvChars.WINDOWS.copy_with(), "%VAR%", EnvQuoteType.NONE),
        ("hello world", EnvExpandFlags.NONE, EnvChars.POSIX.copy_with(), "hello world", EnvQuoteType.NONE),
        ("hello#comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), "hello", EnvQuoteType.NONE),
        ("hello # comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), "hello ", EnvQuoteType.NONE),
        ("\\\"he#llo\\\" # comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), "\\\"he", EnvQuoteType.NONE),
        ('\\"he\\#llo\\" # comment', EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), '\\"he\\#llo\\" ', EnvQuoteType.NONE),
        ("he'#'llo # comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), "he'", EnvQuoteType.NONE),
        ("hello::comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.WINDOWS.copy_with(), "hello", EnvQuoteType.NONE),
        ("hello :: comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.WINDOWS.copy_with(), "hello ", EnvQuoteType.NONE),
        ("he\"::\"llo # comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), "he\"::\"llo ", EnvQuoteType.NONE),
        ("he'::'llo # comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), "he'", EnvQuoteType.NONE),
        ("hello|comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.RISCOS.copy_with(), "hello", EnvQuoteType.NONE),
        ("hello | comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.RISCOS.copy_with(), "hello ", EnvQuoteType.NONE),
        ("he\"|\"llo # comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), "he\"|\"llo ", EnvQuoteType.NONE),
        ("he'|'llo # comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), "he'|'llo ", EnvQuoteType.NONE),
        ("hello!comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.VMS.copy_with(), "hello", EnvQuoteType.NONE),
        ("hello ! comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.VMS.copy_with(), "hello ", EnvQuoteType.NONE),
        ("he\"!\"llo # comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), "he\"!\"llo ", EnvQuoteType.NONE),
        ("he'!'llo # comment", EnvExpandFlags.REMOVE_LINE_COMMENT, EnvChars.POSIX.copy_with(), "he'!'llo ", EnvQuoteType.NONE),
        ("\the'!'llo\n # comment", EnvExpandFlags.REMOVE_LINE_COMMENT | EnvExpandFlags.STRIP_SPACES, EnvChars.POSIX.copy_with(), "he'!'llo", EnvQuoteType.NONE),
    ])
    def test_unquote(self, input_str, flags, chars, expected, expected_qt):
        """Parametrized test ensuring maximum coverage"""
        result, qt = Env.unquote(input_str, flags=flags, chars=chars)
        assert result == expected
        assert qt == expected_qt


class TestEnvExpand:
    """Tests for Env.expand() method"""
    
    def test_expand_sets_flags_to_default_when_none(self):
        """Sets flags to default when passed as None"""
        with patch.object(Env, 'unquote', return_value=("test", EnvQuoteType.NONE)):
            with patch.object(Env, 'expand_posix', return_value="result"):
                result = Env.expand("test", flags=None, chars=EnvChars.POSIX.copy_with())
    
    def test_expand_calls_unquote_when_needed(self):
        """Calls unquote when needed"""
        with patch.object(Env, 'unquote', return_value=("test", EnvQuoteType.NONE)) as mock_unquote:
            with patch.object(Env, 'expand_posix', return_value="test"):
                Env.expand("test", chars=EnvChars.POSIX.copy_with())
                mock_unquote.assert_called()
    
    def test_expand_empty_dict_for_vars_when_skip_env_vars(self):
        """Calls expand_posix or expand_simple with empty dict for vars when SKIP_ENV_VARS is set"""
        with patch.object(Env, 'unquote', return_value=("$VAR", EnvQuoteType.NONE)):
            with patch.object(Env, 'expand_posix', return_value="$VAR") as mock_expand:
                Env.expand("$VAR", 
                          flags=EnvExpandFlags.SKIP_ENV_VARS, 
                          chars=EnvChars.POSIX.copy_with())
                mock_expand.assert_called()
    
    def test_expand_returns_path_if_input_is_path(self):
        """Returns Path if input is Path, otherwise returns str"""
        with patch.object(Env, 'unquote', return_value=("test", EnvQuoteType.NONE)):
            with patch.object(Env, 'expand_posix', return_value="test"):
                result = Env.expand(Path("/some/path"), chars=EnvChars.POSIX.copy_with())
                assert isinstance(result, Path)
    
    def test_expand_returns_str_by_default(self):
        """Returns str by default"""
        with patch.object(Env, 'unquote', return_value=("test", EnvQuoteType.NONE)):
            with patch.object(Env, 'expand_posix', return_value="test"):
                result = Env.expand("test", chars=EnvChars.POSIX.copy_with())
                assert isinstance(result, str)
    
    def test_expand_skips_hard_quoted(self):
        """Skips expansion when string is hard-quoted with SKIP_HARD_QUOTED"""
        hard_chars = EnvChars.POSIX.copy_with(hard_quote="'")
        with patch.object(Env, 'unquote', return_value=("'test'", EnvQuoteType.HARD)):
            result = Env.expand("'test'", 
                              flags=EnvExpandFlags.SKIP_HARD_QUOTED, 
                              chars=hard_chars)
            assert result == "'test'"
    
    def test_expand_routes_to_expand_posix_when_dollar(self):
        """Routes to expand_posix when expand_char is "$" (POSIX)"""
        with patch.object(Env, 'unquote', return_value=("$VAR", EnvQuoteType.NONE)):
            with patch.object(Env, 'expand_posix', return_value="value") as mock_expand_posix:
                Env.expand("$VAR", chars=EnvChars.POSIX.copy_with())
                mock_expand_posix.assert_called()
    
    def test_expand_routes_to_expand_simple_when_percent(self):
        """Routes to expand_simple when expand_char is "%" (Windows)"""
        with patch.object(Env, 'unquote', return_value=("%VAR%", EnvQuoteType.NONE)):
            with patch.object(Env, 'expand_simple', return_value="value") as mock_expand_simple:
                Env.expand("%VAR%", chars=EnvChars.WINDOWS.copy_with())
                mock_expand_simple.assert_called()
    
    def test_expand_routes_to_expand_simple_when_riscos(self):
        """Routes to expand_simple when expand_char is "<" (RISCOS)"""
        with patch.object(Env, 'unquote', return_value=("<VAR>", EnvQuoteType.NONE)):
            with patch.object(Env, 'expand_simple', return_value="value") as mock_expand_simple:
                Env.expand("<VAR>", chars=EnvChars.RISCOS.copy_with())
                mock_expand_simple.assert_called()
    
    def test_expand_routes_to_expand_simple_when_vms(self):
        """Routes to expand_simple when expand_char is "'" (VMS)"""
        with patch.object(Env, 'unquote', return_value=("'VAR'", EnvQuoteType.NONE)):
            with patch.object(Env, 'expand_simple', return_value="value") as mock_expand_simple:
                Env.expand("'VAR'", chars=EnvChars.VMS.copy_with())
                mock_expand_simple.assert_called()
    
    def test_expand_calls_unescape_when_needed(self):
        """Calls unescape when needed"""
        with patch.object(Env, 'unquote', return_value=("test", EnvQuoteType.NONE)):
            with patch.object(Env, 'expand_posix', return_value="test"):
                with patch.object(Env, 'unescape', return_value="test") as mock_unescape:
                    Env.expand("test", 
                              flags=EnvExpandFlags.UNESCAPE, 
                              chars=EnvChars.POSIX.copy_with())
                    mock_unescape.assert_called()
    
    def test_expand_checks_quote_type_hard(self):
        """Checks returned quote_type depending on surrounding quotes"""
        with patch.object(Env, 'unquote', return_value=("test", EnvQuoteType.HARD)):
            with patch.object(Env, 'expand_posix', return_value="expanded") as mock_expand:
                result = Env.expand("'test'", chars=EnvChars.POSIX.copy_with())
                assert result == "test"
    
    def test_expand_checks_quote_type_normal(self):
        """Checks returned quote_type for normal (double) quotes"""
        with patch.object(Env, 'unquote', return_value=("test", EnvQuoteType.NORMAL)):
            with patch.object(Env, 'expand_posix', return_value="expanded"):
                result = Env.expand('"test"', chars=EnvChars.POSIX.copy_with())
                assert result == "expanded"
    
    def test_expand_checks_quote_type_none(self):
        """Checks returned quote_type when NONE"""
        with patch.object(Env, 'unquote', return_value=("test", EnvQuoteType.NONE)):
            with patch.object(Env, 'expand_posix', return_value="expanded"):
                result = Env.expand("test", chars=EnvChars.POSIX.copy_with())
                assert result == "expanded"


class TestEnvExpandPosix:
    """Tests for Env.expand_posix() method"""
    
    @pytest.mark.parametrize("input_str,vars,args,expected", [
        ("$VAR", {"VAR": "value"}, None, "value"),
        ("${VAR}", {"VAR": "value"}, None, "value"),
        ("$1", None, ["one", "two"], "one"),
        ("${1}", None, ["one", "two"], "one"),
        ("$UNKNOWN", None, None, "$UNKNOWN"),
        ("hello world", None, None, "hello world"),
        ("$VAR$VAR2", {"VAR": "a", "VAR2": "b"}, None, "ab"),
        ("${VAR:-default}", {"VAR": ""}, None, "default"),
        ("${VAR-default}", {}, None, "default"),
        ("${VAR:=value}", {}, None, "value"),
        ("${VAR:+alternative}", {"VAR": "value"}, None, "alternative"),
        ("${VAR:+alternative}", {"VAR": ""}, None, ""),
        ("${VAR:0:3}", {"VAR": "hello"}, None, "hel"),
        ("${#VAR}", {"VAR": "hello"}, None, "5"),
    ])
    def test_expand_posix(self, input_str, vars, args, expected):
        """Parametrized test ensuring maximum coverage for POSIX expansion"""
        with patch.dict(os.environ, vars or {}, clear=vars is not None):
            result = Env.expand_posix(input_str, vars=vars, args=args)
            assert result == expected
    
    def test_expand_posix_returns_path_if_input_is_path(self):
        """Returns Path if input is Path, otherwise returns str"""
        result = Env.expand_posix(Path("$VAR"), vars={"VAR": "value"})
        assert isinstance(result, Path)


class TestEnvExpandSimple:
    """Tests for Env.expand_simple() method"""
    
    @pytest.mark.parametrize("input_str,vars,args,expected", [
        ("%VAR%", {"VAR": "value"}, None, "value"),
        ("%1", None, ["one", "two"], "one"),
        ("%*", None, ["arg1", "arg2"], "arg1 arg2"),
        ("%UNKNOWN%", None, None, "%UNKNOWN%"),
        ("plain text", None, None, "plain text"),
        ("%%", None, None, "%"),
        ("%VAR", None, None, "%VAR"),
        ("%VAR:~0,3%", {"VAR": "hello"}, None, "hel"),
        ("%VAR:~-3%", {"VAR": "hello"}, None, "llo"),
    ])
    def test_expand_simple(self, input_str, vars, args, expected):
        """Parametrized test ensuring maximum coverage for Windows expansion"""
        chars = EnvChars.WINDOWS.copy_with()
        result = Env.expand_simple(input_str, vars=vars or {}, args=args, chars=chars)
        assert result == expected
    
    def test_expand_simple_returns_path_if_input_is_path(self):
        """Returns Path if input is Path, otherwise returns str"""
        result = Env.expand_simple(Path("%VAR%"), vars={"VAR": "value"}, chars=EnvChars.WINDOWS.copy_with())
        assert isinstance(result, Path)


class TestEnvUnescape:
    """Tests for Env.unescape() method"""
    
    @pytest.mark.parametrize("input_str,strip_blanks,chars,expected", [
        ("hello", False, EnvChars.POSIX.copy_with(), "hello"),
        ("line1\\nline2", False, EnvChars.POSIX.copy_with(), "line1\nline2"),
        ("test\\t", False, EnvChars.POSIX.copy_with(), "test\t"),
        ("", False, EnvChars.POSIX.copy_with(), ""),
        ("line1\\r\\nline2", False, EnvChars.POSIX.copy_with(), "line1\r\nline2"),
        ("hello", False, EnvChars.WINDOWS.copy_with(), "hello"),
        ("hello", False, EnvChars.RISCOS.copy_with(), "hello"),
        ("line1\\nline2", False, EnvChars.RISCOS.copy_with(), "line1\nline2"),
        ("hello", False, EnvChars.VMS.copy_with(), "hello"),
    ])
    def test_unescape(self, input_str, strip_blanks, chars, expected):
        """Parametrized test ensuring maximum coverage"""
        result = Env.unescape(input_str, strip_blanks=strip_blanks, chars=chars)
        assert result == expected