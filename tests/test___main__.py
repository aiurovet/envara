from typing import Any

import pytest
from pytest import CaptureFixture

import envara.__main__ as envara_main_module


def get_main_output() -> Any:
    return envara_main_module.main


class TestEnvaraMain:
    def test_main_prints_class_list(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert "class Env:" in captured.out
        assert "class EnvFile:" in captured.out

    def test_main_prints_copyright_year(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert "2026" in captured.out

    def test_main_prints_env_methods(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert ".expand(...)" in captured.out
        assert ".expand_path(...)" in captured.out
        assert ".get_all_platforms(...)" in captured.out
        assert ".get_cur_platforms(...)" in captured.out
        assert ".quote(...)" in captured.out
        assert ".split(...)" in captured.out
        assert ".unescape(...)" in captured.out
        assert ".unquote(...)" in captured.out

    def test_main_prints_envara_header(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert "envara" in captured.out.lower()
        assert "Alexander Iurovetski" in captured.out

    def test_main_prints_envfile_methods(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert ".load(...)" in captured.out
        assert ".load_from_str(...)" in captured.out
        assert ".read_text(...)" in captured.out

    def test_main_prints_platform_info(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert ".env" in captured.out

    def test_main_returns_zero(self):
        main = get_main_output()
        assert main is not None
        result = main()
        assert result == 0


class TestEnvaraMainContent:
    def test_prints_examples_section(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert "filter" in captured.out.lower() or "example" in captured.out.lower()

    def test_prints_file_patterns(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert ".env" in captured.out

    def test_prints_library_description(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert "environment" in captured.out.lower()
        assert "variable" in captured.out.lower()


class TestEnvaraMainEdgeCases:
    def test_main_does_not_raise_exception(self):
        main = get_main_output()
        try:
            main()
        except Exception as e:
            pytest.fail(f"main() raised an exception: {e}")

    def test_main_output_is_multiline(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert "\n" in captured.out
        assert len(captured.out.split("\n")) > 10


class TestEnvaraMainIntegration:
    def test_main_callable_twice(self, capsys: CaptureFixture[str]):
        main = get_main_output()
        result1 = main()
        result2 = main()
        assert result1 == 0
        assert result2 == 0
        assert result1 == result2

    @pytest.mark.parametrize(
        "expected_count",
        [100, 200, 500],
    )
    def test_main_output_length(self, expected_count: int, capsys: CaptureFixture[str]):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert len(captured.out) > expected_count


class TestEnvaraMainOutput:
    @pytest.mark.parametrize(
        "expected_string",
        [
            "envara",
            "Alexander Iurovetski",
            "class Env:",
            "class EnvFile:",
            ".expand(...)",
            ".env",
        ],
    )
    def test_main_contains_expected_output(
        self, expected_string: str, capsys: CaptureFixture[str]
    ):
        main = get_main_output()
        main()
        captured = capsys.readouterr()
        assert expected_string in captured.out
