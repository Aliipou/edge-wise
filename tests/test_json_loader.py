"""
Tests for the JsonLoader module.

Achieves 100% coverage for json_loader.py
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from smallworld.io.json_loader import JsonLoader, JsonLoaderError
from smallworld.io.schemas import ServiceData, ServiceTopology


class TestJsonLoader:
    """Tests for JsonLoader class."""

    def test_load_from_file_success(self, sample_json_file: Path) -> None:
        """Test loading valid JSON file."""
        topology = JsonLoader.load_from_file(sample_json_file)

        assert len(topology.services) == 3
        assert len(topology.edges) == 2

    def test_load_from_file_not_found(self, tmp_path: Path) -> None:
        """Test loading non-existent file."""
        nonexistent_path = tmp_path / "does_not_exist" / "file.json"
        with pytest.raises(JsonLoaderError) as exc_info:
            JsonLoader.load_from_file(nonexistent_path)

        assert "File not found" in str(exc_info.value)

    def test_load_from_file_not_a_file(self, tmp_path: Path) -> None:
        """Test loading a directory instead of file."""
        with pytest.raises(JsonLoaderError) as exc_info:
            JsonLoader.load_from_file(tmp_path)

        assert "Not a file" in str(exc_info.value)

    def test_load_from_file_invalid_json(self, invalid_json_file: Path) -> None:
        """Test loading invalid JSON file."""
        with pytest.raises(JsonLoaderError) as exc_info:
            JsonLoader.load_from_file(invalid_json_file)

        assert "Invalid JSON" in str(exc_info.value)

    def test_load_from_string_success(self) -> None:
        """Test loading valid JSON string."""
        json_string = json.dumps({
            "services": [{"name": "test"}],
            "edges": [],
        })

        topology = JsonLoader.load_from_string(json_string)

        assert len(topology.services) == 1
        assert topology.services[0].name == "test"

    def test_load_from_string_invalid(self) -> None:
        """Test loading invalid JSON string."""
        with pytest.raises(JsonLoaderError) as exc_info:
            JsonLoader.load_from_string("{ invalid json }")

        assert "Invalid JSON" in str(exc_info.value)

    def test_load_from_dict_success(self, sample_topology_dict: dict) -> None:
        """Test loading from dictionary."""
        topology = JsonLoader.load_from_dict(sample_topology_dict)

        assert len(topology.services) == 3
        assert len(topology.edges) == 2

    def test_load_from_dict_validation_error(self) -> None:
        """Test loading dictionary with validation error."""
        invalid_dict = {
            "services": [{"name": ""}],  # Empty name not allowed
            "edges": [],
        }

        with pytest.raises(JsonLoaderError) as exc_info:
            JsonLoader.load_from_dict(invalid_dict)

        assert "Validation error" in str(exc_info.value)

    def test_load_request_from_file_success(
        self, sample_json_file: Path, sample_topology_dict: dict
    ) -> None:
        """Test loading analyze request from file."""
        # Create a request file
        request_data = {
            **sample_topology_dict,
            "options": {"goal": "latency", "k": 3},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(request_data, f)
            temp_path = Path(f.name)

        try:
            request = JsonLoader.load_request_from_file(temp_path)

            assert len(request.services) == 3
            assert request.options.goal == "latency"
        finally:
            temp_path.unlink()

    def test_load_request_from_file_not_found(self) -> None:
        """Test loading request from non-existent file."""
        with pytest.raises(JsonLoaderError) as exc_info:
            JsonLoader.load_request_from_file("/nonexistent.json")

        assert "File not found" in str(exc_info.value)

    def test_load_request_from_file_invalid_json(
        self, invalid_json_file: Path
    ) -> None:
        """Test loading request from invalid JSON file."""
        with pytest.raises(JsonLoaderError) as exc_info:
            JsonLoader.load_request_from_file(invalid_json_file)

        assert "Invalid JSON" in str(exc_info.value)

    def test_load_request_from_string_success(self) -> None:
        """Test loading request from JSON string."""
        json_string = json.dumps({
            "services": [{"name": "test"}],
            "edges": [],
            "options": {"goal": "balanced"},
        })

        request = JsonLoader.load_request_from_string(json_string)

        assert len(request.services) == 1
        assert request.options.goal == "balanced"

    def test_load_request_from_string_invalid(self) -> None:
        """Test loading request from invalid string."""
        with pytest.raises(JsonLoaderError) as exc_info:
            JsonLoader.load_request_from_string("not json")

        assert "Invalid JSON" in str(exc_info.value)

    def test_load_request_from_dict_success(
        self, analyze_request_dict: dict
    ) -> None:
        """Test loading request from dictionary."""
        request = JsonLoader.load_request_from_dict(analyze_request_dict)

        assert len(request.services) == 4
        assert request.options.k == 3

    def test_load_request_from_dict_validation_error(self) -> None:
        """Test loading request with validation error."""
        invalid_dict = {
            "services": [{"name": "test"}],
            "edges": [],
            "options": {"goal": "invalid_goal"},  # Invalid goal
        }

        with pytest.raises(JsonLoaderError) as exc_info:
            JsonLoader.load_request_from_dict(invalid_dict)

        assert "Validation error" in str(exc_info.value)

    def test_save_to_file(self, tmp_path: Path) -> None:
        """Test saving topology to file."""
        topology = ServiceTopology(
            services=[ServiceData(name="test-service")],
            edges=[],
        )

        output_file = tmp_path / "output.json"
        JsonLoader.save_to_file(topology, output_file)

        assert output_file.exists()

        # Verify content
        with open(output_file, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["services"]) == 1
        assert data["services"][0]["name"] == "test-service"

    def test_save_to_file_creates_directories(self, tmp_path: Path) -> None:
        """Test that save_to_file creates parent directories."""
        topology = ServiceTopology(services=[], edges=[])

        output_file = tmp_path / "nested" / "deep" / "output.json"
        JsonLoader.save_to_file(topology, output_file)

        assert output_file.exists()

    def test_save_to_file_custom_indent(self, tmp_path: Path) -> None:
        """Test saving with custom indentation."""
        topology = ServiceTopology(
            services=[ServiceData(name="test")],
            edges=[],
        )

        output_file = tmp_path / "output.json"
        JsonLoader.save_to_file(topology, output_file, indent=4)

        with open(output_file, encoding="utf-8") as f:
            content = f.read()

        # Check that it's indented with 4 spaces
        assert "    " in content

    def test_to_json_string(self) -> None:
        """Test converting topology to JSON string."""
        topology = ServiceTopology(
            services=[ServiceData(name="test")],
            edges=[],
        )

        json_string = JsonLoader.to_json_string(topology)

        assert isinstance(json_string, str)
        data = json.loads(json_string)
        assert data["services"][0]["name"] == "test"

    def test_to_json_string_compact(self) -> None:
        """Test converting to compact JSON string."""
        topology = ServiceTopology(
            services=[ServiceData(name="test")],
            edges=[],
        )

        json_string = JsonLoader.to_json_string(topology, indent=None)

        # Compact JSON should have no newlines in the middle
        assert "\n" not in json_string.strip()

    def test_to_json_string_custom_indent(self) -> None:
        """Test converting with custom indent."""
        topology = ServiceTopology(
            services=[ServiceData(name="test")],
            edges=[],
        )

        json_string = JsonLoader.to_json_string(topology, indent=4)

        assert "    " in json_string  # 4-space indent

    def test_roundtrip_file(self, tmp_path: Path) -> None:
        """Test saving and loading back preserves data."""
        original = ServiceTopology(
            services=[
                ServiceData(name="gateway", replicas=2, tags=["frontend"]),
                ServiceData(name="auth", replicas=3),
            ],
            edges=[],
        )

        output_file = tmp_path / "roundtrip.json"
        JsonLoader.save_to_file(original, output_file)
        loaded = JsonLoader.load_from_file(output_file)

        assert len(loaded.services) == len(original.services)
        assert loaded.services[0].name == "gateway"
        assert loaded.services[0].replicas == 2

    def test_roundtrip_string(self) -> None:
        """Test converting to string and back preserves data."""
        original = ServiceTopology(
            services=[ServiceData(name="test", replicas=5)],
            edges=[],
        )

        json_string = JsonLoader.to_json_string(original)
        loaded = JsonLoader.load_from_string(json_string)

        assert loaded.services[0].name == "test"
        assert loaded.services[0].replicas == 5

    def test_load_with_aliases(self, tmp_path: Path) -> None:
        """Test loading file with edge aliases (from/to, p50/p95)."""
        data = {
            "services": [{"name": "a"}, {"name": "b"}],
            "edges": [
                {
                    "from": "a",
                    "to": "b",
                    "call_rate": 10.0,
                    "p50": 5.0,
                    "p95": 25.0,
                }
            ],
        }

        file_path = tmp_path / "aliases.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        topology = JsonLoader.load_from_file(file_path)

        assert topology.edges[0].source == "a"
        assert topology.edges[0].target == "b"
        assert topology.edges[0].p50_latency == 5.0
        assert topology.edges[0].p95_latency == 25.0


class TestJsonLoaderError:
    """Tests for JsonLoaderError exception."""

    def test_exception_message(self) -> None:
        """Test exception message."""
        error = JsonLoaderError("Test error message")
        assert str(error) == "Test error message"

    def test_exception_inheritance(self) -> None:
        """Test that JsonLoaderError inherits from Exception."""
        error = JsonLoaderError("Test")
        assert isinstance(error, Exception)
