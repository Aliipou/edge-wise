"""
Tests for the CLI module.

Achieves 100% coverage for cli.py
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from smallworld.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_topology_file(sample_topology_dict: dict) -> Path:
    """Create a temporary topology file."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as f:
        json.dump(sample_topology_dict, f)
        temp_path = Path(f.name)

    yield temp_path

    if temp_path.exists():
        temp_path.unlink()


class TestVersion:
    """Tests for version option."""

    def test_version(self, runner: CliRunner) -> None:
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "Small-World Services" in result.output

    def test_version_short(self, runner: CliRunner) -> None:
        """Test -v flag."""
        result = runner.invoke(app, ["-v"])

        assert result.exit_code == 0
        assert "Small-World Services" in result.output


class TestAnalyzeCommand:
    """Tests for analyze command."""

    def test_analyze_basic(
        self, runner: CliRunner, sample_topology_file: Path
    ) -> None:
        """Test basic analyze command."""
        result = runner.invoke(app, ["analyze", str(sample_topology_file)])

        assert result.exit_code == 0
        assert "Graph Metrics" in result.output

    def test_analyze_with_output_file(
        self, runner: CliRunner, sample_topology_file: Path, tmp_path: Path
    ) -> None:
        """Test analyze with output file."""
        output_file = tmp_path / "output.json"

        result = runner.invoke(
            app,
            ["analyze", str(sample_topology_file), "--output", str(output_file)],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify output content
        with open(output_file, encoding="utf-8") as f:
            data = json.load(f)

        assert "metrics" in data
        assert "shortcuts" in data

    def test_analyze_with_goal(
        self, runner: CliRunner, sample_topology_file: Path
    ) -> None:
        """Test analyze with custom goal."""
        result = runner.invoke(
            app,
            ["analyze", str(sample_topology_file), "--goal", "latency"],
        )

        assert result.exit_code == 0

    def test_analyze_with_shortcuts_count(
        self, runner: CliRunner, sample_topology_file: Path
    ) -> None:
        """Test analyze with custom shortcuts count."""
        result = runner.invoke(
            app,
            ["analyze", str(sample_topology_file), "--shortcuts", "10"],
        )

        assert result.exit_code == 0

    def test_analyze_verbose(
        self, runner: CliRunner, sample_topology_file: Path
    ) -> None:
        """Test analyze with verbose output."""
        result = runner.invoke(
            app,
            ["analyze", str(sample_topology_file), "--verbose"],
        )

        assert result.exit_code == 0
        # Verbose should show more details
        assert "Loaded" in result.output or "Top Nodes" in result.output

    def test_analyze_nonexistent_file(self, runner: CliRunner) -> None:
        """Test analyze with nonexistent file."""
        result = runner.invoke(app, ["analyze", "/nonexistent/file.json"])

        assert result.exit_code != 0

    def test_analyze_invalid_json(
        self, runner: CliRunner, invalid_json_file: Path
    ) -> None:
        """Test analyze with invalid JSON file."""
        result = runner.invoke(app, ["analyze", str(invalid_json_file)])

        assert result.exit_code == 1
        assert "Error" in result.output


class TestMetricsCommand:
    """Tests for metrics command."""

    def test_metrics_basic(
        self, runner: CliRunner, sample_topology_file: Path
    ) -> None:
        """Test basic metrics command."""
        result = runner.invoke(app, ["metrics", str(sample_topology_file)])

        assert result.exit_code == 0
        assert "Graph Metrics" in result.output

    def test_metrics_single_node(
        self, runner: CliRunner, sample_topology_file: Path
    ) -> None:
        """Test metrics for single node."""
        result = runner.invoke(
            app,
            ["metrics", str(sample_topology_file), "--node", "gateway"],
        )

        assert result.exit_code == 0
        assert "gateway" in result.output

    def test_metrics_nonexistent_node(
        self, runner: CliRunner, sample_topology_file: Path
    ) -> None:
        """Test metrics for nonexistent node."""
        result = runner.invoke(
            app,
            ["metrics", str(sample_topology_file), "--node", "nonexistent"],
        )

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_metrics_invalid_file(
        self, runner: CliRunner, invalid_json_file: Path
    ) -> None:
        """Test metrics with invalid file."""
        result = runner.invoke(app, ["metrics", str(invalid_json_file)])

        assert result.exit_code == 1


class TestValidateCommand:
    """Tests for validate command."""

    def test_validate_valid_file(
        self, runner: CliRunner, sample_topology_file: Path
    ) -> None:
        """Test validating valid file."""
        result = runner.invoke(app, ["validate", str(sample_topology_file)])

        assert result.exit_code == 0
        assert "Valid topology file" in result.output
        assert "Services:" in result.output
        assert "Edges:" in result.output

    def test_validate_invalid_file(
        self, runner: CliRunner, invalid_json_file: Path
    ) -> None:
        """Test validating invalid file."""
        result = runner.invoke(app, ["validate", str(invalid_json_file)])

        assert result.exit_code == 1
        assert "Invalid" in result.output

    def test_validate_missing_services(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test validating file with edges referencing missing services."""
        data = {
            "services": [{"name": "a"}],
            "edges": [{"from": "a", "to": "b"}],  # 'b' not in services
        }

        file_path = tmp_path / "missing.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        result = runner.invoke(app, ["validate", str(file_path)])

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "undefined services" in result.output


class TestServeCommand:
    """Tests for serve command."""

    def test_serve_help(self, runner: CliRunner) -> None:
        """Test serve command help."""
        result = runner.invoke(app, ["serve", "--help"])

        assert result.exit_code == 0
        assert "host" in result.output
        assert "port" in result.output

    @patch("uvicorn.run")
    def test_serve_default(
        self, mock_uvicorn: any, runner: CliRunner
    ) -> None:
        """Test serve with default options."""
        result = runner.invoke(app, ["serve"])

        assert result.exit_code == 0
        mock_uvicorn.assert_called_once()

        # Check call arguments
        call_kwargs = mock_uvicorn.call_args[1]
        assert call_kwargs["host"] == "0.0.0.0"
        assert call_kwargs["port"] == 8000
        assert call_kwargs["reload"] is False

    @patch("uvicorn.run")
    def test_serve_custom_port(
        self, mock_uvicorn: any, runner: CliRunner
    ) -> None:
        """Test serve with custom port."""
        result = runner.invoke(app, ["serve", "--port", "8080"])

        assert result.exit_code == 0
        call_kwargs = mock_uvicorn.call_args[1]
        assert call_kwargs["port"] == 8080

    @patch("uvicorn.run")
    def test_serve_custom_host(
        self, mock_uvicorn: any, runner: CliRunner
    ) -> None:
        """Test serve with custom host."""
        result = runner.invoke(app, ["serve", "--host", "127.0.0.1"])

        assert result.exit_code == 0
        call_kwargs = mock_uvicorn.call_args[1]
        assert call_kwargs["host"] == "127.0.0.1"

    @patch("uvicorn.run")
    def test_serve_with_reload(
        self, mock_uvicorn: any, runner: CliRunner
    ) -> None:
        """Test serve with reload enabled."""
        result = runner.invoke(app, ["serve", "--reload"])

        assert result.exit_code == 0
        call_kwargs = mock_uvicorn.call_args[1]
        assert call_kwargs["reload"] is True


class TestMainCallback:
    """Tests for main callback."""

    def test_help(self, runner: CliRunner) -> None:
        """Test help output."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Microservice topology analyzer" in result.output
        assert "analyze" in result.output
        assert "metrics" in result.output
        assert "serve" in result.output
        assert "validate" in result.output
