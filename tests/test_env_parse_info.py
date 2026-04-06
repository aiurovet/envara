import pytest
from envara.env_parse_info import EnvParseInfo, EnvQuoteType


def test_constants_values():
    # POSIX constants
    assert EnvParseInfo.POSIX_CUTTER_CHAR == "#"
    assert EnvParseInfo.POSIX_EXPAND_CHAR == "$"
    assert EnvParseInfo.POSIX_ESCAPE_CHAR == "\\"
    # RISCOS constants
    assert EnvParseInfo.RISCOS_CUTTER_CHAR == "|"
    assert EnvParseInfo.RISCOS_EXPAND_CHAR == "<"
    assert EnvParseInfo.RISCOS_WINDUP_CHAR == ">"
    assert EnvParseInfo.RISCOS_ESCAPE_CHAR == "\\"
    # VMS constants
    assert EnvParseInfo.VMS_CUTTER_CHAR == "!"
    assert EnvParseInfo.VMS_EXPAND_CHAR == "'"
    assert EnvParseInfo.VMS_ESCAPE_CHAR == "^"
    # Windows constants
    assert EnvParseInfo.WINDOWS_CUTTER_CHAR == ""
    assert EnvParseInfo.WINDOWS_EXPAND_CHAR == "%"
    assert EnvParseInfo.WINDOWS_ESCAPE_CHAR == "^"


def test_initialization_and_defaults():
    info = EnvParseInfo(
        input="input_str",
        result="result_str",
        expand_char="E",
        escape_char="X",
        cutter_char="C",
        quote_type=EnvQuoteType.DOUBLE,
    )
    assert info.input == "input_str"
    assert info.result == "result_str"
    assert info.expand_char == "E"
    assert info.escape_char == "X"
    assert info.cutter_char == "C"
    assert info.quote_type == EnvQuoteType.DOUBLE

    # Omitted optional parameters should be None
    default_info = EnvParseInfo()
    assert default_info.input is None
    assert default_info.result is None
    assert default_info.expand_char is None
    assert default_info.escape_char is None
    assert default_info.cutter_char is None
    assert default_info.quote_type == EnvQuoteType.NONE


def test_copy_to_method():
    src = EnvParseInfo(
        input="src_input",
        result="src_result",
        expand_char="S",
        escape_char="Y",
        cutter_char="Z",
        quote_type=EnvQuoteType.SINGLE,
    )
    dest = EnvParseInfo()
    returned = src.copy_to(dest)
    # Ensure the returned object is the destination
    assert returned is dest
    # Verify all attributes were copied
    assert dest.input == "src_input"
    assert dest.result == "src_result"
    assert dest.expand_char == "S"
    assert dest.escape_char == "Y"
    assert dest.cutter_char == "Z"
    assert dest.quote_type == EnvQuoteType.SINGLE


def test_copy_to_with_none():
    src = EnvParseInfo(input="src_input")
    result = src.copy_to(None)
    assert result is None


def test_copy_to_preserves_windup_char():
    src = EnvParseInfo(
        input="src_input",
        windup_char="W",
    )
    dest = EnvParseInfo()
    src.copy_to(dest)
    assert dest.windup_char == "W"


def test_initialization_with_explicit_windup_char():
    info = EnvParseInfo(
        input="input_str",
        windup_char=">",
    )
    assert info.windup_char == ">"


def test_initialization_without_windup_char_uses_default(mocker):
    mock_riscos = mocker.patch("envara.Env.IS_RISCOS", False)
    mock_posix = mocker.patch("envara.Env.IS_POSIX", True)
    info = EnvParseInfo(input="input_str")
    assert info.windup_char == EnvParseInfo.POSIX_EXPAND_CHAR


def test_get_default_expand_char_posix(mocker):
    mocker.patch("envara.Env.IS_POSIX", True)
    assert EnvParseInfo.get_default_expand_char() == EnvParseInfo.POSIX_EXPAND_CHAR


def test_get_default_expand_char_windows(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", True)
    assert EnvParseInfo.get_default_expand_char() == EnvParseInfo.WINDOWS_EXPAND_CHAR


def test_get_default_expand_char_vms(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", True)
    assert EnvParseInfo.get_default_expand_char() == EnvParseInfo.VMS_EXPAND_CHAR


def test_get_default_expand_char_riscos(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", False)
    mocker.patch("envara.Env.IS_RISCOS", True)
    assert EnvParseInfo.get_default_expand_char() == EnvParseInfo.RISCOS_EXPAND_CHAR


def test_get_default_escape_char_posix(mocker):
    mocker.patch("envara.Env.IS_POSIX", True)
    assert EnvParseInfo.get_default_escape_char() == EnvParseInfo.POSIX_ESCAPE_CHAR


def test_get_default_escape_char_windows(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", True)
    assert EnvParseInfo.get_default_escape_char() == EnvParseInfo.WINDOWS_ESCAPE_CHAR


def test_get_default_escape_char_vms(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", True)
    assert EnvParseInfo.get_default_escape_char() == EnvParseInfo.VMS_ESCAPE_CHAR


def test_get_default_escape_char_riscos(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", False)
    mocker.patch("envara.Env.IS_RISCOS", True)
    assert EnvParseInfo.get_default_escape_char() == EnvParseInfo.RISCOS_ESCAPE_CHAR


def test_get_default_cutter_char_posix(mocker):
    mocker.patch("envara.Env.IS_POSIX", True)
    assert EnvParseInfo.get_default_cutter_char() == EnvParseInfo.POSIX_CUTTER_CHAR


def test_get_default_cutter_char_windows(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", True)
    assert EnvParseInfo.get_default_cutter_char() == EnvParseInfo.WINDOWS_CUTTER_CHAR


def test_get_default_cutter_char_vms(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", True)
    assert EnvParseInfo.get_default_cutter_char() == EnvParseInfo.VMS_CUTTER_CHAR


def test_get_default_cutter_char_riscos(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", False)
    mocker.patch("envara.Env.IS_RISCOS", True)
    assert EnvParseInfo.get_default_cutter_char() == EnvParseInfo.RISCOS_CUTTER_CHAR


def test_get_default_windup_char_riscos(mocker):
    mocker.patch("envara.Env.IS_RISCOS", True)
    assert EnvParseInfo.get_default_windup_char() == EnvParseInfo.RISCOS_WINDUP_CHAR


def test_get_default_windup_char_non_riscos_uses_expand_char(mocker):
    mocker.patch("envara.Env.IS_RISCOS", False)
    mocker.patch("envara.Env.IS_POSIX", True)
    assert EnvParseInfo.get_default_windup_char() == EnvParseInfo.POSIX_EXPAND_CHAR
