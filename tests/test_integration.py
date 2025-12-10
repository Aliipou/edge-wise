"""
Integration tests for end-to-end workflows.
"""

import pytest
from fastapi.testclient import TestClient

from smallworld.api.app import app, user_scores, simulation_history
from smallworld.core.graph_builder import GraphBuilder
from smallworld.core.metrics import MetricsCalculator
from smallworld.core.shortcut_optimizer import ShortcutOptimizer, PolicyConstraints
from smallworld.io.json_loader import JsonLoader
from smallworld.io.schemas import ServiceTopology


@pytest.fixture
def client():
    """Create test client."""
    user_scores.clear()
    simulation_history.clear()
    return TestClient(app)


@pytest.fixture
def sample_topology():
    """Create a sample topology for testing."""
    return {
        "services": [
            {"name": "api-gateway", "replicas": 3, "tags": ["gateway"], "criticality": "critical"},
            {"name": "auth-service", "replicas": 2, "tags": ["auth"], "criticality": "high"},
            {"name": "user-service", "replicas": 2, "tags": ["user"], "criticality": "medium"},
            {"name": "order-service", "replicas": 2, "tags": ["order"], "criticality": "high"},
            {"name": "payment-service", "replicas": 2, "tags": ["payment"], "criticality": "critical"},
            {"name": "notification-service", "replicas": 1, "tags": ["notification"], "criticality": "low"},
        ],
        "edges": [
            {"from": "api-gateway", "to": "auth-service", "call_rate": 500, "p50": 10, "p95": 50, "error_rate": 0.001},
            {"from": "api-gateway", "to": "user-service", "call_rate": 300, "p50": 15, "p95": 70, "error_rate": 0.002},
            {"from": "api-gateway", "to": "order-service", "call_rate": 200, "p50": 20, "p95": 100, "error_rate": 0.003},
            {"from": "auth-service", "to": "user-service", "call_rate": 150, "p50": 5, "p95": 25, "error_rate": 0.001},
            {"from": "order-service", "to": "payment-service", "call_rate": 180, "p50": 30, "p95": 150, "error_rate": 0.005},
            {"from": "order-service", "to": "notification-service", "call_rate": 150, "p50": 8, "p95": 40, "error_rate": 0.001},
            {"from": "payment-service", "to": "notification-service", "call_rate": 100, "p50": 5, "p95": 20, "error_rate": 0.001},
        ],
    }


class TestEndToEndAnalysis:
    """Test end-to-end analysis workflow."""

    def test_full_analysis_pipeline(self, sample_topology):
        """Test complete analysis pipeline: load -> build -> metrics -> optimize."""
        # 1. Load topology
        topology = JsonLoader.load_from_dict(sample_topology)
        assert isinstance(topology, ServiceTopology)
        assert len(topology.services) == 6
        assert len(topology.edges) == 7

        # 2. Build graph
        builder = GraphBuilder()
        graph = builder.build_from_topology(topology)
        assert graph.number_of_nodes() == 6
        assert graph.number_of_edges() == 7

        # 3. Calculate metrics
        calculator = MetricsCalculator(graph)
        graph_metrics, node_metrics = calculator.calculate_all()

        assert graph_metrics.node_count == 6
        assert graph_metrics.edge_count == 7
        assert graph_metrics.average_path_length > 0
        assert len(node_metrics) == 6

        # 4. Find shortcuts
        optimizer = ShortcutOptimizer(graph)
        shortcuts = optimizer.find_shortcuts(k=3)

        assert len(shortcuts) <= 3
        for shortcut in shortcuts:
            assert shortcut.source in [s.name for s in topology.services]
            assert shortcut.target in [s.name for s in topology.services]

    def test_api_analyze_returns_complete_response(self, client, sample_topology):
        """Test API analyze endpoint returns complete response."""
        response = client.post(
            "/analyze",
            json={
                "services": sample_topology["services"],
                "edges": sample_topology["edges"],
                "options": {"goal": "balanced", "k": 5},
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check metrics
        assert "metrics" in data
        assert data["metrics"]["node_count"] == 6
        assert data["metrics"]["edge_count"] == 7

        # Check node metrics
        assert "node_metrics" in data
        assert len(data["node_metrics"]) == 6

        # Check shortcuts
        assert "shortcuts" in data
        assert isinstance(data["shortcuts"], list)

        # Check graph summary
        assert "graph_summary" in data
        assert data["graph_summary"]["total_services"] == 6
        assert "recommendations" in data["graph_summary"]

        # Check metadata
        assert "analysis_metadata" in data
        assert "processing_time_ms" in data["analysis_metadata"]


class TestEndToEndGamification:
    """Test end-to-end gamification workflow."""

    def test_full_gamification_flow(self, client, sample_topology):
        """Test complete gamification flow: analyze -> simulate -> leaderboard."""
        user_id = "test_user_123"

        # 1. Run analysis
        response = client.post(
            "/analyze",
            json={
                "services": sample_topology["services"],
                "edges": sample_topology["edges"],
                "options": {"goal": "balanced", "k": 3},
            },
        )
        assert response.status_code == 200
        analysis = response.json()
        original_path_length = analysis["metrics"]["average_path_length"]

        # 2. Simulate improvement (15% improvement)
        optimized_path_length = original_path_length * 0.85

        response = client.post(
            f"/simulations?user_id={user_id}&original_path_length={original_path_length}"
            f"&optimized_path_length={optimized_path_length}&shortcuts_applied=2"
        )
        assert response.status_code == 200
        simulation = response.json()
        assert simulation["improvement_percent"] > 0
        assert simulation["points_earned"] > 0

        # 3. Check user score
        response = client.get(f"/users/{user_id}/score")
        assert response.status_code == 200
        user_score = response.json()
        assert user_score["score"] > 0
        assert user_score["optimizations"] == 1
        assert "first_optimization" in user_score["achievements"]

        # 4. Check leaderboard
        response = client.get("/leaderboard")
        assert response.status_code == 200
        leaderboard = response.json()
        assert len(leaderboard) >= 1
        assert any(entry["user_id"] == user_id for entry in leaderboard)

    def test_achievement_unlocking(self, client, sample_topology):
        """Test that achievements unlock correctly."""
        user_id = "achievement_tester"

        # Record first optimization
        response = client.post(
            f"/simulations?user_id={user_id}&original_path_length=3.0"
            f"&optimized_path_length=2.5&shortcuts_applied=1"
        )
        assert response.status_code == 200

        # Check first_optimization achievement
        response = client.get(f"/users/{user_id}/score")
        assert "first_optimization" in response.json()["achievements"]

        # Record a 60% improvement for perfect_score achievement
        response = client.post(
            f"/simulations?user_id={user_id}&original_path_length=5.0"
            f"&optimized_path_length=2.0&shortcuts_applied=3"
        )
        assert response.status_code == 200

        # Check perfect_score achievement
        response = client.get(f"/users/{user_id}/score")
        assert "perfect_score" in response.json()["achievements"]


class TestEndToEndExport:
    """Test end-to-end export workflow."""

    def test_export_after_simulations(self, client):
        """Test exporting data after running simulations."""
        # Run several simulations
        for i in range(5):
            client.post(
                f"/simulations?user_id=export_user&original_path_length={3.0 + i * 0.1}"
                f"&optimized_path_length={2.5 + i * 0.05}&shortcuts_applied={i + 1}"
            )

        # Export as JSON
        response = client.get("/export/json?user_id=export_user")
        assert response.status_code == 200
        data = response.json()
        assert data["total_simulations"] == 5

        # Export as CSV
        response = client.get("/export/csv?user_id=export_user")
        assert response.status_code == 200
        csv_data = response.json()["csv"]
        lines = csv_data.strip().split("\n")
        assert len(lines) == 6  # Header + 5 data rows


class TestPolicyConstraints:
    """Test policy constraints integration."""

    def test_forbidden_pairs_respected(self, sample_topology):
        """Test that forbidden pairs are not suggested as shortcuts."""
        builder = GraphBuilder()
        topology = JsonLoader.load_from_dict(sample_topology)
        graph = builder.build_from_topology(topology)

        optimizer = ShortcutOptimizer(graph)

        # Forbid connection from api-gateway to notification-service
        policy = PolicyConstraints(
            forbidden_pairs=[("api-gateway", "notification-service")],
        )

        shortcuts = optimizer.find_shortcuts(k=5, policy=policy)

        # Verify forbidden pair is not in shortcuts
        for shortcut in shortcuts:
            assert not (
                shortcut.source == "api-gateway" and shortcut.target == "notification-service"
            )

    def test_max_edges_per_service_policy_filtering(self, sample_topology):
        """Test that max_edges_per_service policy filters some candidates."""
        builder = GraphBuilder()
        topology = JsonLoader.load_from_dict(sample_topology)
        graph = builder.build_from_topology(topology)

        optimizer = ShortcutOptimizer(graph)

        # Compare with and without policy
        no_policy_shortcuts = optimizer.find_shortcuts(k=10, policy=None)

        policy = PolicyConstraints(max_new_edges_per_service=1)
        with_policy_shortcuts = optimizer.find_shortcuts(k=10, policy=policy)

        # Policy should result in same or fewer shortcuts
        assert len(with_policy_shortcuts) <= len(no_policy_shortcuts)


class TestOptimizationGoals:
    """Test different optimization goals."""

    def test_latency_goal(self, client, sample_topology):
        """Test latency optimization goal."""
        response = client.post(
            "/analyze",
            json={
                "services": sample_topology["services"],
                "edges": sample_topology["edges"],
                "options": {"goal": "latency", "k": 3},
            },
        )
        assert response.status_code == 200
        assert response.json()["analysis_metadata"]["optimization_goal"] == "latency"

    def test_paths_goal(self, client, sample_topology):
        """Test paths optimization goal."""
        response = client.post(
            "/analyze",
            json={
                "services": sample_topology["services"],
                "edges": sample_topology["edges"],
                "options": {"goal": "paths", "k": 3},
            },
        )
        assert response.status_code == 200
        assert response.json()["analysis_metadata"]["optimization_goal"] == "paths"

    def test_load_goal(self, client, sample_topology):
        """Test load optimization goal."""
        response = client.post(
            "/analyze",
            json={
                "services": sample_topology["services"],
                "edges": sample_topology["edges"],
                "options": {"goal": "load", "k": 3},
            },
        )
        assert response.status_code == 200
        assert response.json()["analysis_metadata"]["optimization_goal"] == "load"

    def test_balanced_goal(self, client, sample_topology):
        """Test balanced optimization goal."""
        response = client.post(
            "/analyze",
            json={
                "services": sample_topology["services"],
                "edges": sample_topology["edges"],
                "options": {"goal": "balanced", "k": 3},
            },
        )
        assert response.status_code == 200
        assert response.json()["analysis_metadata"]["optimization_goal"] == "balanced"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_node_topology(self, client):
        """Test analysis with single node topology."""
        response = client.post(
            "/analyze",
            json={
                "services": [{"name": "lonely-service", "replicas": 1, "tags": [], "criticality": "low"}],
                "edges": [],
                "options": {"goal": "balanced", "k": 3},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["node_count"] == 1
        assert data["metrics"]["edge_count"] == 0

    def test_disconnected_graph(self, client):
        """Test analysis with disconnected graph."""
        response = client.post(
            "/analyze",
            json={
                "services": [
                    {"name": "service-a", "replicas": 1, "tags": [], "criticality": "low"},
                    {"name": "service-b", "replicas": 1, "tags": [], "criticality": "low"},
                    {"name": "service-c", "replicas": 1, "tags": [], "criticality": "low"},
                ],
                "edges": [
                    {"from": "service-a", "to": "service-b", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0},
                ],
                "options": {"goal": "balanced", "k": 3},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["node_count"] == 3
        assert data["metrics"]["weakly_connected_components"] == 2

    def test_large_topology(self, client):
        """Test analysis with larger topology."""
        services = [
            {"name": f"service-{i}", "replicas": 1, "tags": [], "criticality": "medium"}
            for i in range(20)
        ]
        edges = [
            {"from": f"service-{i}", "to": f"service-{(i + 1) % 20}", "call_rate": 100, "p50": 10, "p95": 50, "error_rate": 0}
            for i in range(20)
        ]

        response = client.post(
            "/analyze",
            json={
                "services": services,
                "edges": edges,
                "options": {"goal": "balanced", "k": 5},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["node_count"] == 20
        assert data["metrics"]["edge_count"] == 20
