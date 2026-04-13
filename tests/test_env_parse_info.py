import pytest
from env_chars import EnvChars, EnvQuoteType


def test_constants_values():
    # POSIX constants
    assert EnvChars.POSIX_CUTTER == "#"
    assert EnvChars.POSIX_EXPAND == "$"
    assert EnvChars.POSIX_ESCAPE == "\\"
    # RISCOS constants
    assert EnvChars.RISCOS_CUTTER == "|"
    assert EnvChars.RISCOS_EXPAND == "<"
    assert EnvChars.RISCOS_WINDUP == ">"
    assert EnvChars.RISCOS_ESCAPE == "\\"
    # VMS constants
    assert EnvChars.VMS_CUTTER == "!"
    assert EnvChars.VMS_EXPAND == "'"
    assert EnvChars.VMS_ESCAPE == "^"
    # Windows constants
    assert EnvChars.WINDOWS_CUTTER == ""
    assert EnvChars.WINDOWS_EXPAND == "%"
    assert EnvChars.WINDOWS_ESCAPE == "^"


def test_initialization_and_defaults():
    info = EnvChars(
        input="input_str",
        result="result_str",
        expand="E",
        escape="X",
        cutter="C",
        quote_type=EnvQuoteType.DEFAULT,
    )
    assert info.input == "input_str"
    assert info.result == "result_str"
    assert info.expand == "E"
    assert info.escape == "X"
    assert info.cutter == "C"
    assert info.quote_type == EnvQuoteType.DEFAULT

    # Omitted optional parameters should be None
    default_info = EnvChars()
    assert default_info.input is None
    assert default_info.result is None
    assert default_info.expand_char is None
    assert default_info.escape_char is None
    assert default_info.cutter_char is None
    assert default_info.quote_type == EnvQuoteType.NONE


def test_copy_to_method():
    src = EnvChars(
        input="src_input",
        result="src_result",
        expand="S",
        escape="Y",
        cutter="Z",
        quote_type=EnvQuoteType.HARD,
    )
    dest = EnvChars()
    returned = src.copy_to(dest)
    # Ensure the returned object is the destination
    assert returned is dest
    # Verify all attributes were copied
    assert dest.input == "src_input"
    assert dest.result == "src_result"
    assert dest.expand == "S"
    assert dest.escape == "Y"
    assert dest.cutter == "Z"
    assert dest.quote_type == EnvQuoteType.HARD


def test_copy_to_with_none():
    src = EnvChars(input="src_input")
    result = src.copy_to(None)
    assert result is None


def test_copy_to_preserves_windup_char():
    src = EnvChars(
        input="src_input",
        windup="W",
    )
    dest = EnvChars()
    src.copy_to(dest)
    assert dest.windup == "W"


def test_initialization_with_explicit_windup_char():
    info = EnvChars(
        input="input_str",
        windup=">",
    )
    assert info.windup == ">"


def test_initialization_without_windup_char_uses_default(mocker):
    mock_riscos = mocker.patch("envara.Env.IS_RISCOS", False)
    mock_posix = mocker.patch("envara.Env.IS_POSIX", True)
    info = EnvChars(input="input_str")
    assert info.windup == EnvChars.POSIX_EXPAND


def test_get_default_expand_char_posix(mocker):
    mocker.patch("envara.Env.IS_POSIX", True)
    assert EnvChars.get_default_expand_char() == EnvChars.POSIX_EXPAND


def test_get_default_expand_char_windows(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", True)
    assert EnvChars.get_default_expand_char() == EnvChars.WINDOWS_EXPAND


def test_get_default_expand_char_vms(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", True)
    assert EnvChars.get_default_expand_char() == EnvChars.VMS_EXPAND


def test_get_default_expand_char_riscos(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", False)
    mocker.patch("envara.Env.IS_RISCOS", True)
    assert EnvChars.get_default_expand_char() == EnvChars.RISCOS_EXPAND


def test_get_default_escape_char_posix(mocker):
    mocker.patch("envara.Env.IS_POSIX", True)
    assert EnvChars.get_default_escape_char() == EnvChars.POSIX_ESCAPE


def test_get_default_escape_char_windows(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", True)
    assert EnvChars.get_default_escape_char() == EnvChars.WINDOWS_ESCAPE


def test_get_default_escape_char_vms(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", True)
    assert EnvChars.get_default_escape_char() == EnvChars.VMS_ESCAPE


def test_get_default_escape_char_riscos(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", False)
    mocker.patch("envara.Env.IS_RISCOS", True)
    assert EnvChars.get_default_escape_char() == EnvChars.RISCOS_ESCAPE


def test_get_default_cutter_char_posix(mocker):
    mocker.patch("envara.Env.IS_POSIX", True)
    assert EnvChars.get_default_cutter_char() == EnvChars.POSIX_CUTTER


def test_get_default_cutter_char_windows(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", True)
    assert EnvChars.get_default_cutter_char() == EnvChars.WINDOWS_CUTTER


def test_get_default_cutter_char_vms(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", True)
    assert EnvChars.get_default_cutter_char() == EnvChars.VMS_CUTTER


def test_get_default_cutter_char_riscos(mocker):
    mocker.patch("envara.Env.IS_POSIX", False)
    mocker.patch("envara.Env.IS_WINDOWS", False)
    mocker.patch("envara.Env.IS_VMS", False)
    mocker.patch("envara.Env.IS_RISCOS", True)
    assert EnvChars.get_default_cutter_char() == EnvChars.RISCOS_CUTTER


def test_get_default_windup_char_riscos(mocker):
    mocker.patch("envara.Env.IS_RISCOS", True)
    assert EnvChars.get_default_windup_char() == EnvChars.RISCOS_WINDUP


def test_get_default_windup_char_non_riscos_uses_expand_char(mocker):
    mocker.patch("envara.Env.IS_RISCOS", False)
    mocker.patch("envara.Env.IS_POSIX", True)
    assert EnvChars.get_default_windup_char() == EnvChars.POSIX_EXPAND
