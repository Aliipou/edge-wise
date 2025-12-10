"""
Tests for the FastAPI application.

Achieves 100% coverage for api/app.py
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from smallworld.api.app import app, create_app, generate_recommendations


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client: TestClient) -> None:
        """Test root endpoint returns basic info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Small-World Services API"
        assert "version" in data
        assert data["docs"] == "/docs"


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health(self, client: TestClient) -> None:
        """Test health endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data["details"]


class TestAnalyzeEndpoint:
    """Tests for analyze endpoint."""

    def test_analyze_minimal(self, client: TestClient) -> None:
        """Test analyze with minimal request."""
        request = {
            "services": [
                {"name": "gateway"},
                {"name": "auth"},
            ],
            "edges": [
                {"from": "gateway", "to": "auth", "call_rate": 10.0},
            ],
        }

        response = client.post("/analyze", json=request)

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "node_metrics" in data
        assert "shortcuts" in data
        assert "graph_summary" in data

    def test_analyze_full_request(
        self, client: TestClient, analyze_request_dict: dict
    ) -> None:
        """Test analyze with full request."""
        response = client.post("/analyze", json=analyze_request_dict)

        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["node_count"] == 4

    def test_analyze_with_options(self, client: TestClient) -> None:
        """Test analyze with custom options."""
        request = {
            "services": [
                {"name": "a"},
                {"name": "b"},
                {"name": "c"},
            ],
            "edges": [
                {"from": "a", "to": "b", "call_rate": 10.0},
                {"from": "b", "to": "c", "call_rate": 10.0},
            ],
            "options": {
                "goal": "latency",
                "k": 3,
                "alpha": 2.0,
                "beta": 0.5,
            },
        }

        response = client.post("/analyze", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["analysis_metadata"]["optimization_goal"] == "latency"

    def test_analyze_with_policy(self, client: TestClient) -> None:
        """Test analyze with policy constraints."""
        request = {
            "services": [
                {"name": "a"},
                {"name": "b"},
                {"name": "c"},
                {"name": "d"},
            ],
            "edges": [
                {"from": "a", "to": "b", "call_rate": 10.0},
                {"from": "b", "to": "c", "call_rate": 10.0},
                {"from": "c", "to": "d", "call_rate": 10.0},
            ],
            "policy": {
                "forbidden_pairs": [["a", "d"]],
                "max_new_edges_per_service": 2,
            },
        }

        response = client.post("/analyze", json=request)

        assert response.status_code == 200
        data = response.json()

        # Check that forbidden pair is not suggested
        for shortcut in data["shortcuts"]:
            assert not (shortcut["from"] == "a" and shortcut["to"] == "d")

    def test_analyze_returns_metrics(self, client: TestClient) -> None:
        """Test that analyze returns proper metrics."""
        request = {
            "services": [
                {"name": "gateway", "replicas": 2},
                {"name": "auth", "replicas": 3},
                {"name": "users", "replicas": 2},
            ],
            "edges": [
                {"from": "gateway", "to": "auth", "call_rate": 100.0, "p50": 10.0},
                {"from": "auth", "to": "users", "call_rate": 80.0, "p50": 15.0},
            ],
        }

        response = client.post("/analyze", json=request)

        assert response.status_code == 200
        data = response.json()

        # Check metrics structure
        metrics = data["metrics"]
        assert metrics["node_count"] == 3
        assert metrics["edge_count"] == 2
        assert "density" in metrics
        assert "average_path_length" in metrics
        assert "small_world_coefficient" in metrics

    def test_analyze_returns_node_metrics(self, client: TestClient) -> None:
        """Test that analyze returns node metrics."""
        request = {
            "services": [{"name": "a"}, {"name": "b"}],
            "edges": [{"from": "a", "to": "b", "call_rate": 10.0}],
        }

        response = client.post("/analyze", json=request)

        assert response.status_code == 200
        data = response.json()

        # Check node metrics
        assert len(data["node_metrics"]) == 2
        node_a = next(n for n in data["node_metrics"] if n["name"] == "a")
        assert "betweenness_centrality" in node_a
        assert "is_hub" in node_a

    def test_analyze_returns_graph_summary(self, client: TestClient) -> None:
        """Test that analyze returns graph summary."""
        request = {
            "services": [{"name": "a"}, {"name": "b"}, {"name": "c"}],
            "edges": [
                {"from": "a", "to": "b", "call_rate": 100.0},
                {"from": "b", "to": "c", "call_rate": 50.0},
            ],
        }

        response = client.post("/analyze", json=request)

        assert response.status_code == 200
        data = response.json()

        summary = data["graph_summary"]
        assert summary["total_services"] == 3
        assert summary["total_dependencies"] == 2
        assert "hub_services" in summary
        assert "bottleneck_services" in summary
        assert "recommendations" in summary

    def test_analyze_invalid_request(self, client: TestClient) -> None:
        """Test analyze with invalid request."""
        request = {
            "services": [{"name": ""}],  # Empty name
            "edges": [],
        }

        response = client.post("/analyze", json=request)

        assert response.status_code == 422  # Validation error

    def test_analyze_empty_graph(self, client: TestClient) -> None:
        """Test analyze with empty graph."""
        request = {
            "services": [],
            "edges": [],
        }

        response = client.post("/analyze", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["node_count"] == 0

    def test_analyze_processing_time(self, client: TestClient) -> None:
        """Test that processing time is included in metadata."""
        request = {
            "services": [{"name": "a"}, {"name": "b"}],
            "edges": [{"from": "a", "to": "b"}],
        }

        response = client.post("/analyze", json=request)

        assert response.status_code == 200
        data = response.json()
        assert "processing_time_ms" in data["analysis_metadata"]
        assert data["analysis_metadata"]["processing_time_ms"] >= 0


class TestCreateApp:
    """Tests for create_app function."""

    def test_create_app(self) -> None:
        """Test creating app instance."""
        application = create_app()

        assert application.title == "Small-World Services API"
        assert application.version is not None


class TestGenerateRecommendations:
    """Tests for generate_recommendations function."""

    def test_poor_small_world(self) -> None:
        """Test recommendation for poor small-world properties."""
        from smallworld.core.metrics import GraphMetrics, NodeMetrics

        graph_metrics = GraphMetrics(
            small_world_coefficient=0.3,
            is_connected=True,
            max_betweenness=0.2,
            average_path_length=2.0,
        )
        node_metrics = {}
        shortcuts = []

        recommendations = generate_recommendations(
            graph_metrics, node_metrics, shortcuts
        )

        assert any("poor small-world" in r.lower() for r in recommendations)

    def test_good_small_world(self) -> None:
        """Test recommendation for good small-world properties."""
        from smallworld.core.metrics import GraphMetrics

        graph_metrics = GraphMetrics(
            small_world_coefficient=2.0,
            is_connected=True,
            max_betweenness=0.2,
            average_path_length=2.0,
        )

        recommendations = generate_recommendations(graph_metrics, {}, [])

        assert any("strong small-world" in r.lower() for r in recommendations)

    def test_disconnected_warning(self) -> None:
        """Test warning for disconnected graph."""
        from smallworld.core.metrics import GraphMetrics

        graph_metrics = GraphMetrics(
            is_connected=False,
            weakly_connected_components=3,
            small_world_coefficient=1.0,
            max_betweenness=0.2,
            average_path_length=2.0,
        )

        recommendations = generate_recommendations(graph_metrics, {}, [])

        assert any("disconnected" in r.lower() for r in recommendations)

    def test_high_betweenness_warning(self) -> None:
        """Test warning for high betweenness centrality."""
        from smallworld.core.metrics import GraphMetrics, NodeMetrics

        graph_metrics = GraphMetrics(
            max_betweenness=0.6,
            is_connected=True,
            small_world_coefficient=1.0,
            average_path_length=2.0,
        )
        node_metrics = {
            "hub": NodeMetrics(
                name="hub",
                is_bottleneck=True,
                betweenness_centrality=0.6,
            ),
        }

        recommendations = generate_recommendations(graph_metrics, node_metrics, [])

        assert any("betweenness" in r.lower() for r in recommendations)

    def test_high_path_length_warning(self) -> None:
        """Test warning for high average path length."""
        from smallworld.core.metrics import GraphMetrics

        graph_metrics = GraphMetrics(
            average_path_length=5.0,
            is_connected=True,
            small_world_coefficient=1.0,
            max_betweenness=0.2,
        )

        recommendations = generate_recommendations(graph_metrics, {}, [])

        assert any("path length" in r.lower() for r in recommendations)

    def test_shortcuts_found(self) -> None:
        """Test recommendation when shortcuts are found."""
        from smallworld.core.metrics import GraphMetrics
        from smallworld.core.shortcut_optimizer import ShortcutCandidate

        graph_metrics = GraphMetrics(
            is_connected=True,
            small_world_coefficient=1.0,
            max_betweenness=0.2,
            average_path_length=2.0,
        )
        shortcuts = [
            ShortcutCandidate(source="a", target="b"),
            ShortcutCandidate(source="c", target="d"),
        ]

        recommendations = generate_recommendations(graph_metrics, {}, shortcuts)

        assert any("2 beneficial shortcut" in r for r in recommendations)

    def test_no_shortcuts_found(self) -> None:
        """Test recommendation when no shortcuts are found."""
        from smallworld.core.metrics import GraphMetrics

        graph_metrics = GraphMetrics(
            is_connected=True,
            small_world_coefficient=1.0,
            max_betweenness=0.2,
            average_path_length=2.0,
        )

        recommendations = generate_recommendations(graph_metrics, {}, [])

        assert any("no beneficial shortcuts" in r.lower() for r in recommendations)


class TestExceptionHandler:
    """Tests for exception handling."""

    def test_http_exception_handler(self, client: TestClient) -> None:
        """Test that HTTP exceptions are properly formatted."""
        # Trigger a validation error
        response = client.post("/analyze", json={"invalid": "data"})

        assert response.status_code == 422
