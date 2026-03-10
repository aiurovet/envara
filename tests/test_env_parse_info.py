import pytest
from envara.env_parse_info import EnvParseInfo, EnvQuoteType


def test_constants_values():
    # POSIX constants
    assert EnvParseInfo.POSIX_CUTTER_CHAR == "#"
    assert EnvParseInfo.POSIX_EXPAND_CHAR == "$"
    assert EnvParseInfo.POSIX_ESCAPE_CHAR == "\\"
    # PowerShell constants
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
