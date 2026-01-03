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
    assert "Envara (c) Alexander Iurovetski 2026" in captured.out
    assert "class Env:" in captured.out
    assert "class DotEnv:" in captured.out
    assert "See README.md for more details" in captured.out
    assert "Dot-env files" in captured.out
