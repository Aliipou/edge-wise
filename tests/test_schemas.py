"""
Tests for Pydantic schemas.

Achieves 100% coverage for schemas.py
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from smallworld.io.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    CriticalityLevel,
    EdgeData,
    ErrorResponse,
    GraphMetricsResponse,
    GraphSummary,
    HealthResponse,
    NodeMetricsResponse,
    OptimizationOptions,
    PolicyConfig,
    ServiceData,
    ServiceTopology,
    ShortcutSuggestion,
)


class TestCriticalityLevel:
    """Tests for CriticalityLevel enum."""

    def test_enum_values(self) -> None:
        """Test enum values."""
        assert CriticalityLevel.LOW.value == "low"
        assert CriticalityLevel.MEDIUM.value == "medium"
        assert CriticalityLevel.HIGH.value == "high"
        assert CriticalityLevel.CRITICAL.value == "critical"


class TestServiceData:
    """Tests for ServiceData schema."""

    def test_minimal_service(self) -> None:
        """Test creating service with minimal data."""
        service = ServiceData(name="test-service")

        assert service.name == "test-service"
        assert service.replicas == 1
        assert service.tags == []
        assert service.criticality == CriticalityLevel.MEDIUM

    def test_full_service(self) -> None:
        """Test creating service with all fields."""
        service = ServiceData(
            name="auth-service",
            replicas=3,
            tags=["critical", "auth"],
            criticality=CriticalityLevel.CRITICAL,
            zone="us-east-1",
        )

        assert service.name == "auth-service"
        assert service.replicas == 3
        assert "critical" in service.tags
        assert service.zone == "us-east-1"

    def test_name_validation_empty(self) -> None:
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError):
            ServiceData(name="")

    def test_name_validation_whitespace(self) -> None:
        """Test that whitespace-only name is rejected."""
        with pytest.raises(ValidationError):
            ServiceData(name="   ")

    def test_name_validation_special_chars(self) -> None:
        """Test that special characters are rejected."""
        with pytest.raises(ValidationError):
            ServiceData(name="service@invalid")

    def test_name_validation_allowed_chars(self) -> None:
        """Test that allowed characters work."""
        service = ServiceData(name="my-service_v1.0")
        assert service.name == "my-service_v1.0"

    def test_name_trimmed(self) -> None:
        """Test that name is trimmed."""
        service = ServiceData(name="  trimmed  ")
        assert service.name == "trimmed"

    def test_replicas_zero(self) -> None:
        """Test that zero replicas is allowed."""
        service = ServiceData(name="test", replicas=0)
        assert service.replicas == 0

    def test_replicas_negative(self) -> None:
        """Test that negative replicas is rejected."""
        with pytest.raises(ValidationError):
            ServiceData(name="test", replicas=-1)


class TestEdgeData:
    """Tests for EdgeData schema."""

    def test_minimal_edge(self) -> None:
        """Test creating edge with minimal data."""
        edge = EdgeData(source="a", target="b")

        assert edge.source == "a"
        assert edge.target == "b"
        assert edge.call_rate == 0.0
        assert edge.error_rate == 0.0

    def test_full_edge(self) -> None:
        """Test creating edge with all fields."""
        edge = EdgeData(
            source="gateway",
            target="auth",
            call_rate=100.5,
            p50_latency=10.0,
            p95_latency=50.0,
            error_rate=0.01,
            cost=0.001,
        )

        assert edge.source == "gateway"
        assert edge.call_rate == 100.5
        assert edge.p50_latency == 10.0

    def test_edge_alias_from_to(self) -> None:
        """Test edge with 'from'/'to' aliases."""
        data = {"from": "a", "to": "b", "call_rate": 10.0}
        edge = EdgeData.model_validate(data)

        assert edge.source == "a"
        assert edge.target == "b"

    def test_edge_alias_p50_p95(self) -> None:
        """Test edge with p50/p95 aliases."""
        data = {"from": "a", "to": "b", "p50": 10.0, "p95": 50.0}
        edge = EdgeData.model_validate(data)

        assert edge.p50_latency == 10.0
        assert edge.p95_latency == 50.0

    def test_empty_source(self) -> None:
        """Test that empty source is rejected."""
        with pytest.raises(ValidationError):
            EdgeData(source="", target="b")

    def test_empty_target(self) -> None:
        """Test that empty target is rejected."""
        with pytest.raises(ValidationError):
            EdgeData(source="a", target="")

    def test_negative_call_rate(self) -> None:
        """Test that negative call rate is rejected."""
        with pytest.raises(ValidationError):
            EdgeData(source="a", target="b", call_rate=-1.0)

    def test_error_rate_bounds(self) -> None:
        """Test error rate must be 0-1."""
        # Valid
        edge = EdgeData(source="a", target="b", error_rate=0.5)
        assert edge.error_rate == 0.5

        # Invalid > 1
        with pytest.raises(ValidationError):
            EdgeData(source="a", target="b", error_rate=1.5)


class TestServiceTopology:
    """Tests for ServiceTopology schema."""

    def test_empty_topology(self) -> None:
        """Test creating empty topology."""
        topology = ServiceTopology()

        assert topology.services == []
        assert topology.edges == []

    def test_full_topology(self) -> None:
        """Test creating full topology."""
        topology = ServiceTopology(
            services=[
                ServiceData(name="a"),
                ServiceData(name="b"),
            ],
            edges=[
                EdgeData(source="a", target="b", call_rate=10.0),
            ],
        )

        assert len(topology.services) == 2
        assert len(topology.edges) == 1

    def test_self_loop_rejected(self) -> None:
        """Test that self-loops are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ServiceTopology(
                services=[ServiceData(name="a")],
                edges=[EdgeData(source="a", target="a")],
            )

        assert "Self-loop" in str(exc_info.value)


class TestOptimizationOptions:
    """Tests for OptimizationOptions schema."""

    def test_default_options(self) -> None:
        """Test default optimization options."""
        options = OptimizationOptions()

        assert options.goal == "balanced"
        assert options.k == 5
        assert options.alpha == 1.0
        assert options.beta == 1.0
        assert options.gamma == 0.1

    def test_custom_options(self) -> None:
        """Test custom optimization options."""
        options = OptimizationOptions(
            goal="latency",
            k=10,
            alpha=2.0,
        )

        assert options.goal == "latency"
        assert options.k == 10
        assert options.alpha == 2.0

    def test_invalid_goal(self) -> None:
        """Test that invalid goal is rejected."""
        with pytest.raises(ValidationError):
            OptimizationOptions(goal="invalid")

    def test_goal_case_insensitive(self) -> None:
        """Test that goal validation is case insensitive."""
        options = OptimizationOptions(goal="LATENCY")
        assert options.goal == "latency"

    def test_k_bounds(self) -> None:
        """Test k value bounds."""
        # Min
        options = OptimizationOptions(k=1)
        assert options.k == 1

        # Max
        options = OptimizationOptions(k=100)
        assert options.k == 100

        # Below min
        with pytest.raises(ValidationError):
            OptimizationOptions(k=0)

        # Above max
        with pytest.raises(ValidationError):
            OptimizationOptions(k=101)


class TestPolicyConfig:
    """Tests for PolicyConfig schema."""

    def test_default_policy(self) -> None:
        """Test default policy configuration."""
        policy = PolicyConfig()

        assert policy.forbidden_pairs == []
        assert policy.allowed_zones == {}
        assert policy.max_new_edges_per_service == 3
        assert policy.require_same_zone is False

    def test_custom_policy(self) -> None:
        """Test custom policy configuration."""
        policy = PolicyConfig(
            forbidden_pairs=[["a", "b"]],
            allowed_zones={"us-east": ["us-west"]},
            max_new_edges_per_service=5,
            require_same_zone=True,
            min_path_length_to_shortcut=3,
        )

        assert ["a", "b"] in policy.forbidden_pairs
        assert policy.require_same_zone is True


class TestAnalyzeRequest:
    """Tests for AnalyzeRequest schema."""

    def test_minimal_request(self) -> None:
        """Test minimal analyze request."""
        request = AnalyzeRequest(
            services=[ServiceData(name="a")],
            edges=[],
        )

        assert len(request.services) == 1
        assert request.options.goal == "balanced"

    def test_full_request(self) -> None:
        """Test full analyze request."""
        request = AnalyzeRequest(
            services=[
                ServiceData(name="a"),
                ServiceData(name="b"),
            ],
            edges=[
                EdgeData(source="a", target="b"),
            ],
            options=OptimizationOptions(goal="latency", k=10),
            policy=PolicyConfig(require_same_zone=True),
        )

        assert request.options.goal == "latency"
        assert request.policy is not None
        assert request.policy.require_same_zone is True


class TestNodeMetricsResponse:
    """Tests for NodeMetricsResponse schema."""

    def test_node_metrics_response(self) -> None:
        """Test node metrics response creation."""
        response = NodeMetricsResponse(
            name="test",
            in_degree=2,
            out_degree=3,
            total_degree=5,
            betweenness_centrality=0.5,
            closeness_centrality=0.6,
            clustering_coefficient=0.3,
            pagerank=0.1,
            incoming_load=100.0,
            outgoing_load=50.0,
            is_hub=True,
            is_bottleneck=False,
            vulnerability_score=0.45,
        )

        assert response.name == "test"
        assert response.is_hub is True


class TestGraphMetricsResponse:
    """Tests for GraphMetricsResponse schema."""

    def test_graph_metrics_response(self) -> None:
        """Test graph metrics response creation."""
        response = GraphMetricsResponse(
            node_count=10,
            edge_count=20,
            density=0.22,
            average_path_length=2.5,
            weighted_average_path_length=25.0,
            diameter=5,
            average_clustering=0.33,
            is_connected=True,
            strongly_connected_components=1,
            weakly_connected_components=1,
            max_betweenness=0.45,
            total_load=500.0,
            hub_count=2,
            bottleneck_count=1,
            small_world_coefficient=1.5,
        )

        assert response.node_count == 10
        assert response.is_connected is True


class TestShortcutSuggestion:
    """Tests for ShortcutSuggestion schema."""

    def test_shortcut_suggestion(self) -> None:
        """Test shortcut suggestion creation."""
        suggestion = ShortcutSuggestion(
            source="a",
            target="b",
            improvement=0.5,
            delta_path_length=-0.3,
            delta_max_betweenness=-0.1,
            risk_score=0.2,
            confidence=0.8,
            score=2.5,
            rationale="Test",
            estimated_latency=10.0,
        )

        assert suggestion.source == "a"
        assert suggestion.target == "b"

    def test_shortcut_suggestion_alias(self) -> None:
        """Test shortcut suggestion with aliases."""
        data = {
            "from": "a",
            "to": "b",
            "improvement": 0.5,
            "delta_path_length": -0.3,
            "delta_max_betweenness": -0.1,
            "risk_score": 0.2,
            "confidence": 0.8,
            "score": 2.5,
            "rationale": "Test",
            "estimated_latency": 10.0,
        }
        suggestion = ShortcutSuggestion.model_validate(data)

        assert suggestion.source == "a"


class TestGraphSummary:
    """Tests for GraphSummary schema."""

    def test_graph_summary(self) -> None:
        """Test graph summary creation."""
        summary = GraphSummary(
            total_services=10,
            total_dependencies=20,
            hub_services=["gateway"],
            bottleneck_services=["auth"],
            most_connected_service="gateway",
            highest_load_service="auth",
            is_small_world=True,
            recommendations=["Add shortcut"],
        )

        assert summary.total_services == 10
        assert "gateway" in summary.hub_services


class TestAnalyzeResponse:
    """Tests for AnalyzeResponse schema."""

    def test_analyze_response(self) -> None:
        """Test analyze response creation."""
        response = AnalyzeResponse(
            metrics=GraphMetricsResponse(
                node_count=3,
                edge_count=2,
                density=0.33,
                average_path_length=1.5,
                weighted_average_path_length=15.0,
                diameter=2,
                average_clustering=0.0,
                is_connected=True,
                strongly_connected_components=1,
                weakly_connected_components=1,
                max_betweenness=0.5,
                total_load=100.0,
                hub_count=1,
                bottleneck_count=1,
                small_world_coefficient=1.0,
            ),
            node_metrics=[],
            shortcuts=[],
            graph_summary=GraphSummary(
                total_services=3,
                total_dependencies=2,
                hub_services=[],
                bottleneck_services=[],
                most_connected_service=None,
                highest_load_service=None,
                is_small_world=True,
                recommendations=[],
            ),
            analysis_metadata={"time": 0.1},
        )

        assert response.metrics.node_count == 3


class TestHealthResponse:
    """Tests for HealthResponse schema."""

    def test_health_response(self) -> None:
        """Test health response creation."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            details={"uptime": 100},
        )

        assert response.status == "healthy"


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_error_response(self) -> None:
        """Test error response creation."""
        response = ErrorResponse(
            error="Something went wrong",
            detail="More details",
            code="ERR_001",
        )

        assert response.error == "Something went wrong"

    def test_error_response_minimal(self) -> None:
        """Test minimal error response."""
        response = ErrorResponse(error="Error")

        assert response.error == "Error"
        assert response.detail is None
        assert response.code is None
