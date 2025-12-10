"""
Tests to cover remaining uncovered lines for 100% coverage.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import networkx as nx

from smallworld.core.metrics import MetricsCalculator
from smallworld.core.shortcut_optimizer import ShortcutOptimizer, OptimizationGoal
from smallworld.io.json_loader import JsonLoader, JsonLoaderError
from smallworld.io.schemas import ServiceTopology


class TestMetricsExceptionBranches:
    """Test exception branches in metrics calculation."""

    def test_betweenness_with_exception_raising_graph(self):
        """Test betweenness when nx.betweenness_centrality raises."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        calc = MetricsCalculator(graph)

        with patch.object(nx, 'betweenness_centrality', side_effect=Exception("Test error")):
            graph_metrics, node_metrics = calc.calculate_all()

            # Should use default values
            assert node_metrics["a"].betweenness_centrality == 0.0

    def test_closeness_with_exception_raising_graph(self):
        """Test closeness when nx.closeness_centrality raises."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        calc = MetricsCalculator(graph)

        with patch.object(nx, 'closeness_centrality', side_effect=Exception("Test error")):
            graph_metrics, node_metrics = calc.calculate_all()

            assert node_metrics["a"].closeness_centrality == 0.0

    def test_clustering_with_exception(self):
        """Test clustering when nx.clustering raises."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        calc = MetricsCalculator(graph)

        with patch.object(nx, 'clustering', side_effect=Exception("Test error")):
            graph_metrics, node_metrics = calc.calculate_all()

            assert node_metrics["a"].clustering_coefficient == 0.0

    def test_pagerank_with_exception(self):
        """Test pagerank when nx.pagerank raises."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        calc = MetricsCalculator(graph)

        with patch.object(nx, 'pagerank', side_effect=Exception("Test error")):
            graph_metrics, node_metrics = calc.calculate_all()

            # Should have fallback value
            assert node_metrics["a"].pagerank >= 0

    def test_average_clustering_with_exception(self):
        """Test average clustering when nx.average_clustering raises."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        calc = MetricsCalculator(graph)

        with patch.object(nx, 'average_clustering', side_effect=Exception("Test error")):
            graph_metrics, node_metrics = calc.calculate_all()

            assert graph_metrics.average_clustering == 0.0

    def test_path_length_exception(self):
        """Test path length when calculation raises."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        calc = MetricsCalculator(graph)

        with patch.object(nx, 'single_source_shortest_path_length', side_effect=Exception("Test")):
            graph_metrics, _ = calc.calculate_all()

            assert graph_metrics.average_path_length == 0.0

    def test_weighted_path_length_exception(self):
        """Test weighted path length when calculation raises."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b", weight=1.0)

        calc = MetricsCalculator(graph)

        with patch.object(nx, 'single_source_dijkstra_path_length', side_effect=Exception("Test")):
            graph_metrics, _ = calc.calculate_all()

            assert graph_metrics.weighted_average_path_length == 0.0

    def test_diameter_exception(self):
        """Test diameter when calculation raises exception."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")
        graph.add_edge("b", "a")

        calc = MetricsCalculator(graph)

        with patch.object(nx, 'diameter', side_effect=Exception("Test")):
            with patch.object(nx, 'is_strongly_connected', return_value=True):
                graph_metrics, _ = calc.calculate_all()

                assert graph_metrics.diameter == 0

    def test_small_world_edge_cases(self):
        """Test small world coefficient edge cases."""
        graph = nx.DiGraph()
        # Just 2 nodes - below n<3 threshold
        graph.add_edge("a", "b")

        calc = MetricsCalculator(graph)
        graph_metrics, _ = calc.calculate_all()

        # Should return 0 for small graphs
        assert graph_metrics.small_world_coefficient >= 0

    def test_small_world_with_zero_lambda(self):
        """Test small world coefficient when lambda_ratio is 0."""
        graph = nx.DiGraph()
        for i in range(5):
            graph.add_node(f"n{i}")

        calc = MetricsCalculator(graph)
        graph_metrics, _ = calc.calculate_all()

        # Should handle zero lambda ratio
        assert graph_metrics.small_world_coefficient >= 0


class TestOptimizerGoalEnum:
    """Test optimizer with OptimizationGoal enum."""

    def test_set_goal_with_enum_directly(self):
        """Test setting goal with OptimizationGoal enum."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        optimizer = ShortcutOptimizer(graph)
        optimizer.set_goal(OptimizationGoal.LATENCY)

        assert optimizer.goal == OptimizationGoal.LATENCY
        assert optimizer.alpha == 2.0  # Latency weights


class TestJsonLoaderIOErrors:
    """Test JSON loader IO error handling."""

    def test_load_from_file_io_error(self):
        """Test IOError when reading file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.json"
            filepath.write_text('{"services": [], "edges": []}')

            # Mock open to raise IOError
            with patch('builtins.open', side_effect=IOError("Cannot read")):
                with pytest.raises(JsonLoaderError) as exc_info:
                    JsonLoader.load_from_file(filepath)

                assert "Cannot read file" in str(exc_info.value)

    def test_save_to_file_io_error(self):
        """Test IOError when writing file."""
        topology = ServiceTopology(services=[], edges=[])

        with patch('builtins.open', side_effect=IOError("Cannot write")):
            with pytest.raises(JsonLoaderError) as exc_info:
                JsonLoader.save_to_file(topology, Path("test.json"))

            assert "Cannot write file" in str(exc_info.value)


class TestCLIExceptionHandling:
    """Test CLI exception handling paths."""

    def test_analyze_with_json_loader_error(self):
        """Test analyze command with JsonLoaderError."""
        from typer.testing import CliRunner
        from smallworld.cli import app as cli_app

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "invalid.json"
            filepath.write_text("not valid json {{{")

            result = runner.invoke(cli_app, ["analyze", str(filepath)])
            assert result.exit_code == 1
            assert "Error" in result.output

    def test_analyze_with_general_exception(self):
        """Test analyze command handles general exceptions."""
        from typer.testing import CliRunner
        from smallworld.cli import app as cli_app

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.json"
            filepath.write_text('{"services": [{"name": "a", "replicas": 1, "criticality": "medium"}], "edges": []}')

            with patch('smallworld.cli.GraphBuilder.build_from_topology', side_effect=RuntimeError("Test error")):
                result = runner.invoke(cli_app, ["analyze", str(filepath)])
                assert result.exit_code == 1


class TestAPIValueError:
    """Test API ValueError handling."""

    def test_analyze_with_value_error(self):
        """Test analyze endpoint with ValueError."""
        from fastapi.testclient import TestClient
        from smallworld.api.app import app

        client = TestClient(app)

        with patch('smallworld.api.app.GraphBuilder') as mock_builder:
            mock_builder.return_value.build_from_dict.side_effect = ValueError("Invalid value")

            response = client.post(
                "/analyze",
                json={
                    "services": [{"name": "a", "replicas": 1, "tags": [], "criticality": "medium"}],
                    "edges": [],
                    "options": {"goal": "balanced", "k": 3},
                },
            )
            assert response.status_code == 400
            assert "Invalid value" in response.json()["error"]
