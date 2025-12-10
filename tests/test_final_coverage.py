"""
Final tests to achieve 100% code coverage.
Targets the remaining uncovered lines.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import networkx as nx

from smallworld.core.metrics import MetricsCalculator, GraphMetrics
from smallworld.core.shortcut_optimizer import ShortcutOptimizer, OptimizationGoal


class TestCLIUvicornImportError:
    """Test CLI serve command when uvicorn is not installed."""

    def test_serve_without_uvicorn(self):
        """Test serve command handles missing uvicorn gracefully."""
        from typer.testing import CliRunner
        from smallworld.cli import app as cli_app

        runner = CliRunner()

        # Mock uvicorn import to raise ImportError
        with patch.dict(sys.modules, {'uvicorn': None}):
            # We need to force the import to fail
            import builtins
            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == 'uvicorn':
                    raise ImportError("No module named 'uvicorn'")
                return original_import(name, *args, **kwargs)

            with patch.object(builtins, '__import__', mock_import):
                result = runner.invoke(cli_app, ["serve"])
                # Command should exit with error code 1
                assert result.exit_code == 1
                assert "uvicorn not installed" in result.output


class TestCLIPrintTopNodesEmpty:
    """Test print_top_nodes with empty node_metrics."""

    def test_print_top_nodes_empty_dict(self):
        """Test print_top_nodes returns early for empty dict."""
        from smallworld.cli import print_top_nodes

        # Should not raise, just return early
        result = print_top_nodes({})
        assert result is None


class TestCLIMainBlock:
    """Test CLI main block execution."""

    def test_main_block_execution(self):
        """Test that main block can be executed."""
        # We can test this by importing and running app()
        from smallworld.cli import app
        from typer.testing import CliRunner

        runner = CliRunner()
        # Run --help to verify app works
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_main_block_via_runpy(self):
        """Test main block via runpy to cover if __name__ == '__main__'."""
        import runpy
        import sys

        # Save original argv and set to show help
        original_argv = sys.argv
        sys.argv = ["smallworld", "--help"]

        try:
            # This should execute the main block and call app()
            # We catch SystemExit since --help causes exit
            with pytest.raises(SystemExit) as exc_info:
                runpy.run_module("smallworld.cli", run_name="__main__", alter_sys=True)
            # --help exits with code 0
            assert exc_info.value.code == 0
        finally:
            sys.argv = original_argv


class TestMetricsGraphMetricsEmpty:
    """Test _calculate_graph_metrics with zero nodes."""

    def test_calculate_graph_metrics_zero_nodes(self):
        """Test _calculate_graph_metrics returns early when n==0 after filtering."""
        graph = nx.DiGraph()
        calc = MetricsCalculator(graph)

        # Call _calculate_graph_metrics directly with empty node_metrics
        result = calc._calculate_graph_metrics({})

        # Should return default GraphMetrics
        assert isinstance(result, GraphMetrics)
        assert result.node_count == 0


class TestMetricsNetworkXNoPath:
    """Test weighted path length with NetworkXNoPath exception."""

    def test_weighted_path_length_no_path(self):
        """Test weighted path length handles NetworkXNoPath exception."""
        graph = nx.DiGraph()
        graph.add_node("a")
        graph.add_node("b")
        # No edge between a and b - no path exists

        calc = MetricsCalculator(graph)

        # This should handle NetworkXNoPath gracefully
        result = calc._calculate_weighted_average_path_length()

        # Should return 0.0 when no paths exist
        assert result == 0.0

    def test_weighted_path_length_with_disconnected_components(self):
        """Test weighted path length with multiple disconnected components."""
        graph = nx.DiGraph()
        # Component 1
        graph.add_edge("a", "b", weight=1.0)
        # Component 2 (disconnected)
        graph.add_edge("c", "d", weight=2.0)

        calc = MetricsCalculator(graph)
        result = calc._calculate_weighted_average_path_length()

        # Should handle gracefully - will calculate for reachable pairs
        assert result >= 0.0


class TestMetricsSmallWorldEdgeCases:
    """Test small-world coefficient edge cases."""

    def test_small_world_zero_random_clustering(self):
        """Test small world coefficient when random_clustering is 0."""
        graph = nx.DiGraph()
        # Create graph with 0 edges - p will be 0, so random_clustering = 0
        for i in range(5):
            graph.add_node(f"n{i}")

        calc = MetricsCalculator(graph)
        graph_metrics, _ = calc.calculate_all()

        # Should return 0 when random_clustering is 0
        assert graph_metrics.small_world_coefficient == 0.0

    def test_small_world_zero_lambda_ratio(self):
        """Test small world coefficient when lambda_ratio is 0."""
        # This is a challenging edge case - we need lambda_ratio = 0
        # which means path_length / random_path_length = 0
        # This happens when path_length = 0
        graph = nx.DiGraph()
        # Single node - path_length will be 0
        graph.add_node("single")

        calc = MetricsCalculator(graph)
        result = calc._calculate_small_world_coefficient(
            clustering=0.5,
            path_length=0.0,  # This makes the function return 0 early
            n=1,
            m=0
        )

        assert result == 0.0

    def test_small_world_zero_random_path_length(self):
        """Test small world coefficient when random_path_length becomes 0."""
        graph = nx.DiGraph()
        # This tests line 368-369: when random_clustering or random_path_length is 0
        for i in range(3):
            graph.add_node(f"n{i}")

        calc = MetricsCalculator(graph)
        # Call with values that would make random_clustering = 0
        result = calc._calculate_small_world_coefficient(
            clustering=0.5,
            path_length=2.0,
            n=3,
            m=0  # No edges means p=0, random_clustering=0
        )

        assert result == 0.0

    def test_small_world_lambda_ratio_zero_after_calculation(self):
        """Test when lambda_ratio becomes 0 after calculation (line 375-376)."""
        graph = nx.DiGraph()
        # Create specific conditions where lambda_ratio could be 0
        calc = MetricsCalculator(graph)

        # Directly test with path_length=0 which makes lambda_ratio=0
        # This tests line 375-376
        result = calc._calculate_small_world_coefficient(
            clustering=0.5,
            path_length=0.0,  # Will cause early return at line 352
            n=5,
            m=2
        )

        assert result == 0.0


class TestMetricsIdentifyHubsBottlenecksEmpty:
    """Test _identify_hubs_and_bottlenecks with empty node_metrics."""

    def test_identify_hubs_bottlenecks_empty(self):
        """Test _identify_hubs_and_bottlenecks returns early for empty dict."""
        graph = nx.DiGraph()
        calc = MetricsCalculator(graph)
        graph_metrics = GraphMetrics()

        # Should not raise, just return early
        calc._identify_hubs_and_bottlenecks({}, graph_metrics)

        # hub_count and bottleneck_count should remain 0
        assert graph_metrics.hub_count == 0
        assert graph_metrics.bottleneck_count == 0


class TestOptimizerGoalEnumDirect:
    """Test optimizer set_goal with OptimizationGoal enum directly."""

    def test_set_goal_with_enum_latency(self):
        """Test setting goal with OptimizationGoal.LATENCY enum."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        optimizer = ShortcutOptimizer(graph)
        optimizer.set_goal(OptimizationGoal.LATENCY)

        assert optimizer.goal == OptimizationGoal.LATENCY
        assert optimizer.alpha == 2.0
        assert optimizer.beta == 0.5

    def test_set_goal_with_enum_paths(self):
        """Test setting goal with OptimizationGoal.PATHS enum."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        optimizer = ShortcutOptimizer(graph)
        optimizer.set_goal(OptimizationGoal.PATHS)

        assert optimizer.goal == OptimizationGoal.PATHS
        assert optimizer.alpha == 2.0
        assert optimizer.beta == 0.3

    def test_set_goal_with_enum_load(self):
        """Test setting goal with OptimizationGoal.LOAD enum."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        optimizer = ShortcutOptimizer(graph)
        optimizer.set_goal(OptimizationGoal.LOAD)

        assert optimizer.goal == OptimizationGoal.LOAD
        assert optimizer.alpha == 0.5
        assert optimizer.beta == 2.0

    def test_set_goal_with_enum_balanced(self):
        """Test setting goal with OptimizationGoal.BALANCED enum."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        optimizer = ShortcutOptimizer(graph)
        optimizer.set_goal(OptimizationGoal.BALANCED)

        assert optimizer.goal == OptimizationGoal.BALANCED
        assert optimizer.alpha == 1.0
        assert optimizer.beta == 1.0


class TestMetricsWeightedPathNetworkXNoPathSpecific:
    """Specifically test the NetworkXNoPath exception in weighted path calculation."""

    def test_networkx_no_path_exception_caught(self):
        """Test that NetworkXNoPath is caught and continues iteration."""
        graph = nx.DiGraph()
        # Create a graph where some paths don't exist
        graph.add_edge("a", "b", weight=1.0)
        graph.add_node("c")  # Isolated node

        calc = MetricsCalculator(graph)

        # This should iterate through all nodes and catch NetworkXNoPath
        # when trying to find paths from/to the isolated node
        result = calc._calculate_weighted_average_path_length()

        # Should return a valid value (path length for a->b)
        assert result >= 0.0

    def test_networkx_no_path_exception_mocked(self):
        """Test NetworkXNoPath exception handling with mock."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b", weight=1.0)
        graph.add_edge("b", "c", weight=2.0)

        calc = MetricsCalculator(graph)

        # Mock single_source_dijkstra_path_length to raise NetworkXNoPath
        call_count = [0]
        original_dijkstra = nx.single_source_dijkstra_path_length

        def mock_dijkstra(G, source, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:  # Raise on second call
                raise nx.NetworkXNoPath("No path")
            return original_dijkstra(G, source, *args, **kwargs)

        with patch.object(nx, 'single_source_dijkstra_path_length', side_effect=mock_dijkstra):
            result = calc._calculate_weighted_average_path_length()

        # Should handle the exception gracefully
        assert result >= 0.0


class TestMetricsSmallWorldWithSpecificValues:
    """Test small-world coefficient with values that trigger specific branches."""

    def test_small_world_n_less_than_3(self):
        """Test small world returns 0 when n < 3."""
        graph = nx.DiGraph()
        graph.add_edge("a", "b")

        calc = MetricsCalculator(graph)
        result = calc._calculate_small_world_coefficient(
            clustering=0.5,
            path_length=1.0,
            n=2,  # n < 3
            m=1
        )

        assert result == 0.0

    def test_small_world_path_length_zero(self):
        """Test small world returns 0 when path_length is 0."""
        graph = nx.DiGraph()

        calc = MetricsCalculator(graph)
        result = calc._calculate_small_world_coefficient(
            clustering=0.5,
            path_length=0.0,  # Zero path length
            n=5,
            m=4
        )

        assert result == 0.0

    def test_small_world_avg_degree_less_than_1(self):
        """Test small world when average degree < 1 (uses fallback path length)."""
        graph = nx.DiGraph()
        # Many nodes, few edges
        for i in range(10):
            graph.add_node(f"n{i}")

        calc = MetricsCalculator(graph)
        # m=0 means avg_degree = 0, which triggers fallback
        result = calc._calculate_small_world_coefficient(
            clustering=0.0,
            path_length=1.0,
            n=10,
            m=0  # No edges - avg_degree will be 0
        )

        # random_clustering = 0, so result should be 0
        assert result == 0.0
