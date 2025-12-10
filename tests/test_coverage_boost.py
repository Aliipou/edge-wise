"""
Additional tests to boost code coverage.
"""

import pytest
from fastapi.testclient import TestClient

from smallworld.api.app import app, manager, user_scores, simulation_history
from smallworld.core.graph_builder import GraphBuilder
from smallworld.core.metrics import MetricsCalculator
from smallworld.core.shortcut_optimizer import ShortcutOptimizer


@pytest.fixture
def client():
    """Create test client."""
    user_scores.clear()
    simulation_history.clear()
    return TestClient(app)


class TestMetricsCoverage:
    """Additional metrics tests for coverage."""

    def test_metrics_with_weighted_edges(self):
        """Test metrics with weighted edges for coverage."""
        builder = GraphBuilder()
        graph = builder.build_from_dict({
            "services": [
                {"name": "a", "replicas": 1, "criticality": "high"},
                {"name": "b", "replicas": 1, "criticality": "low"},
                {"name": "c", "replicas": 1, "criticality": "medium"},
            ],
            "edges": [
                {"from": "a", "to": "b", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0.01, "cost": 5.0},
                {"from": "b", "to": "c", "call_rate": 50, "p50": 20, "p95": 100, "error_rate": 0.02, "cost": 3.0},
            ],
        })

        calc = MetricsCalculator(graph)
        graph_metrics, node_metrics = calc.calculate_all()

        # Check weighted path length is calculated
        assert graph_metrics.weighted_average_path_length >= 0

    def test_metrics_circular_graph(self):
        """Test metrics with circular graph."""
        builder = GraphBuilder()
        graph = builder.build_from_dict({
            "services": [
                {"name": "a", "replicas": 1, "criticality": "medium"},
                {"name": "b", "replicas": 1, "criticality": "medium"},
                {"name": "c", "replicas": 1, "criticality": "medium"},
            ],
            "edges": [
                {"from": "a", "to": "b", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                {"from": "b", "to": "c", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                {"from": "c", "to": "a", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
            ],
        })

        calc = MetricsCalculator(graph)
        graph_metrics, node_metrics = calc.calculate_all()

        # Should complete without error
        assert graph_metrics.is_connected


class TestOptimizerCoverage:
    """Additional optimizer tests for coverage."""

    def test_optimizer_with_high_betweenness_nodes(self):
        """Test optimizer focusing on high betweenness nodes."""
        builder = GraphBuilder()
        # Create a star topology where center has high betweenness
        graph = builder.build_from_dict({
            "services": [
                {"name": "center", "replicas": 1, "criticality": "critical"},
                {"name": "leaf1", "replicas": 1, "criticality": "low"},
                {"name": "leaf2", "replicas": 1, "criticality": "low"},
                {"name": "leaf3", "replicas": 1, "criticality": "low"},
                {"name": "leaf4", "replicas": 1, "criticality": "low"},
            ],
            "edges": [
                {"from": "center", "to": "leaf1", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                {"from": "center", "to": "leaf2", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                {"from": "center", "to": "leaf3", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                {"from": "center", "to": "leaf4", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                {"from": "leaf1", "to": "center", "call_rate": 50, "p50": 5, "p95": 25, "error_rate": 0},
            ],
        })

        optimizer = ShortcutOptimizer(graph)
        optimizer.set_goal("load")
        shortcuts = optimizer.find_shortcuts(k=3)

        # Should find shortcuts or not, but should not crash
        assert isinstance(shortcuts, list)


class TestAPICoverage:
    """Additional API tests for coverage."""

    def test_analyze_with_custom_alpha_beta_gamma(self, client):
        """Test analyze with custom optimization weights."""
        response = client.post(
            "/analyze",
            json={
                "services": [
                    {"name": "a", "replicas": 1, "tags": [], "criticality": "medium"},
                    {"name": "b", "replicas": 1, "tags": [], "criticality": "medium"},
                ],
                "edges": [
                    {"from": "a", "to": "b", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                ],
                "options": {
                    "goal": "balanced",
                    "k": 3,
                    "alpha": 0.5,
                    "beta": 0.3,
                    "gamma": 0.2,
                },
            },
        )
        assert response.status_code == 200

    def test_analyze_with_zone_policy(self, client):
        """Test analyze with zone-based policy."""
        response = client.post(
            "/analyze",
            json={
                "services": [
                    {"name": "a", "replicas": 1, "tags": [], "criticality": "medium", "zone": "us-east-1"},
                    {"name": "b", "replicas": 1, "tags": [], "criticality": "medium", "zone": "us-east-1"},
                    {"name": "c", "replicas": 1, "tags": [], "criticality": "medium", "zone": "us-west-2"},
                ],
                "edges": [
                    {"from": "a", "to": "b", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                    {"from": "b", "to": "c", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                ],
                "options": {"goal": "balanced", "k": 3},
                "policy": {
                    "require_same_zone": True,
                    "allowed_zones": {"us-east-1": ["us-east-1", "us-west-2"]},
                },
            },
        )
        assert response.status_code == 200

    def test_analyze_with_min_path_length_policy(self, client):
        """Test analyze with min path length policy."""
        response = client.post(
            "/analyze",
            json={
                "services": [
                    {"name": "a", "replicas": 1, "tags": [], "criticality": "medium"},
                    {"name": "b", "replicas": 1, "tags": [], "criticality": "medium"},
                    {"name": "c", "replicas": 1, "tags": [], "criticality": "medium"},
                    {"name": "d", "replicas": 1, "tags": [], "criticality": "medium"},
                ],
                "edges": [
                    {"from": "a", "to": "b", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                    {"from": "b", "to": "c", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                    {"from": "c", "to": "d", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                ],
                "options": {"goal": "balanced", "k": 3},
                "policy": {
                    "min_path_length_to_shortcut": 3,
                },
            },
        )
        assert response.status_code == 200


class TestWebSocketCoverage:
    """Additional WebSocket tests for coverage."""

    def test_websocket_json_message(self, client):
        """Test WebSocket with JSON message."""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text('{"type": "ping"}')
            data = websocket.receive_json()
            assert data["type"] == "ack"


class TestSimulationBroadcast:
    """Test that simulations trigger broadcasts."""

    def test_simulation_triggers_points(self, client):
        """Test that simulation awards points correctly."""
        user_id = "broadcast_test_user"

        # Record a simulation
        response = client.post(
            f"/simulations?user_id={user_id}&original_path_length=3.0"
            f"&optimized_path_length=2.0&shortcuts_applied=2"
        )
        assert response.status_code == 200
        result = response.json()

        # Check points were earned (33% improvement = 33 * 10 = 330 points approx)
        assert result["points_earned"] > 0

        # Check user score updated
        user = client.get(f"/users/{user_id}/score")
        assert user.json()["score"] > 0


class TestGraphBuilderCoverage:
    """Additional graph builder tests."""

    def test_builder_with_all_edge_attributes(self):
        """Test building graph with all edge attributes."""
        builder = GraphBuilder()
        graph = builder.build_from_dict({
            "services": [
                {"name": "a", "replicas": 2, "tags": ["api"], "criticality": "high", "zone": "us-east"},
                {"name": "b", "replicas": 1, "tags": ["db"], "criticality": "critical", "zone": "us-east"},
            ],
            "edges": [
                {
                    "from": "a",
                    "to": "b",
                    "call_rate": 1000,
                    "p50": 5,
                    "p95": 25,
                    "error_rate": 0.001,
                    "cost": 0.5,
                },
            ],
        })

        # Check edge has key attributes
        edge_data = graph.get_edge_data("a", "b")
        assert edge_data["call_rate"] == 1000
        assert edge_data["error_rate"] == 0.001
        assert edge_data["weight"] > 0


class TestJsonLoaderCoverage:
    """Additional JSON loader tests."""

    def test_loader_with_request_options(self):
        """Test loading analyze request with all options."""
        from smallworld.io.json_loader import JsonLoader

        data = {
            "services": [
                {"name": "a", "replicas": 1, "criticality": "medium"},
            ],
            "edges": [],
            "options": {
                "goal": "latency",
                "k": 10,
                "alpha": 0.4,
                "beta": 0.3,
                "gamma": 0.3,
            },
            "policy": {
                "forbidden_pairs": [["a", "b"]],
                "max_new_edges_per_service": 2,
                "require_same_zone": True,
                "min_path_length_to_shortcut": 2,
                "allowed_zones": {"us-east-1": ["us-east-1", "us-west-2"]},
            },
        }

        request = JsonLoader.load_request_from_dict(data)
        assert request.options.goal == "latency"
        assert request.options.k == 10
        assert request.policy is not None
        assert request.policy.require_same_zone is True
