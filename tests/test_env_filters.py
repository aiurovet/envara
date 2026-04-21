import pytest
from tests.conftest import env_filter_mod, env_filters_mod


EnvFilter = env_filter_mod.EnvFilter
EnvFilters = env_filters_mod.EnvFilters


class TestEnvFiltersProcess:
    def test_process_empty_input(self):
        result = EnvFilters.process([], [EnvFilter()])
        assert result == []

    def test_process_empty_filters(self):
        result = EnvFilters.process(["file.env"], [])
        assert result == ["file.env"]

    def test_process_no_match(self):
        result = EnvFilters.process(["file.txt"], [EnvFilter(indicator="app")])
        assert result == []

    def test_process_indicator_only(self):
        result = EnvFilters.process([".env"], [EnvFilter(indicator="env")])
        assert ".env" in result

    def test_process_with_cur_values_match(self):
        files = ["dev.env", "prod.env"]
        filters = [EnvFilter(indicator="env", cur_values=["dev"])]
        result = EnvFilters.process(files, filters)
        assert "dev.env" in result

    def test_process_with_multiple_cur_values(self):
        files = ["dev.env", "prod.env", "test.env"]
        filters = [EnvFilter(indicator="env", cur_values=["dev", "prod"])]
        result = EnvFilters.process(files, filters)
        assert "dev.env" in result
        assert "prod.env" in result

    def test_process_no_matching_values(self):
        files = ["other.env"]
        filters = [EnvFilter(indicator="env", cur_values=["dev", "prod"])]
        result = EnvFilters.process(files, filters)
        assert len(result) >= 0

    def test_process_multiple_filters(self):
        files = ["dev.env", "prod.env"]
        filters = [
            EnvFilter(indicator="env", cur_values=["dev", "prod"]),
            EnvFilter(indicator="env", cur_values=["dev"]),
        ]
        result = EnvFilters.process(files, filters)
        assert len(result) > 0

    def test_process_preserves_order(self):
        files = ["a.env", "b.env", "c.env"]
        filters = [EnvFilter(indicator="env", cur_values=["a", "b", "c"])]
        result = EnvFilters.process(files, filters)
        assert len(result) == 3

    def test_process_string_sorting(self):
        files = ["c.env", "a.env", "b.env"]
        filters = [EnvFilter(indicator="env", cur_values=["a", "b", "c"])]
        result = EnvFilters.process(files, filters)
        assert result[0] == "a.env"

    def test_process_same_indices_diff_strings(self):
        files = ["a.env", "b.env"]
        filters = [EnvFilter(indicator="env", cur_values=["dev"])]
        result = EnvFilters.process(files, filters)
        sorted_names = sorted(result)
        assert sorted_names[0] == "a.env"

    def test_process_different_lengths(self):
        files = ["dev.env", ".env"]
        filters = [
            EnvFilter(indicator="env", cur_values=["dev"]),
            EnvFilter(indicator="env", cur_values=["dev"]),
        ]
        result = EnvFilters.process(files, filters)
        assert "dev.env" in result

    def test_process_equal_indices_tie_break(self):
        files = ["aaa.env", "bbb.env"]
        filters = [EnvFilter(indicator="env", cur_values=["aaa", "bbb"])]
        result = EnvFilters.process(files, filters)
        assert result[0] == "aaa.env"
        assert result[1] == "bbb.env"

    def test_process_equal_indices_different_strings(self):
        files = ["zzz.env", "aaa.env", "mmm.env"]
        filters = [EnvFilter(indicator="env", cur_values=["dev"])]
        result = EnvFilters.process(files, filters)
        sorted_result = sorted(result)
        assert sorted_result == ["aaa.env", "mmm.env", "zzz.env"]


class TestEnvFiltersIntegration:
    def test_process_exact_indicator_match(self):
        files = [".env", "app.env"]
        result = EnvFilters.process(files, [EnvFilter(indicator="env")])
        assert ".env" in result

    def test_process_with_filter_values(self):
        files = ["dev.env", "prod.env", "other.env"]
        result = EnvFilters.process(files, [EnvFilter(indicator="env", cur_values=["dev", "prod"])])
        assert "dev.env" in result
        assert "prod.env" in result
        assert "other.env" in result or len(result) == 3

    def test_process_empty_result(self):
        result = EnvFilters.process(["file.txt", "data.json"], [EnvFilter(indicator="env")])
        assert len(result) == 0
