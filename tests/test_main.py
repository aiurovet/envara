import pytest
import runpy


def test_main_output(capsys):
    """Test that the main module prints the help message and exits with 0."""
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("envara", run_name="__main__")

    # Check exit code
    assert excinfo.value.code == 0

    # Check output
    captured = capsys.readouterr()
    assert "envara (c) Alexander Iurovetski 2026" in captured.out
    assert "class Env:" in captured.out
    assert "class EnvFile:" in captured.out
    assert "See README.md for more details" in captured.out
    assert "Here is an incomplete list of dot-env files" in captured.out


def test_main_import_does_nothing(capsys):
    """Importing the module should not execute the main block or print anything."""
    # import the package's __main__ module the normal way
    import importlib

    mod = importlib.import_module("envara.__main__")
    # the module should load without side effects
    assert mod.__name__ == "envara.__main__"

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
