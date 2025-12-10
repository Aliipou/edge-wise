"""
Pydantic schemas for input/output data validation.

Defines the data contracts for:
- Service definitions
- Edge (dependency) definitions
- API requests and responses
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CriticalityLevel(str, Enum):
    """Service criticality levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceData(BaseModel):
    """
    Schema for a service node.

    Represents a microservice with its metadata.
    """

    name: str = Field(..., min_length=1, max_length=256, description="Unique service name")
    replicas: int = Field(default=1, ge=0, description="Number of service replicas")
    tags: list[str] = Field(default_factory=list, description="Service tags/labels")
    criticality: CriticalityLevel = Field(
        default=CriticalityLevel.MEDIUM,
        description="Service criticality level"
    )
    zone: str | None = Field(default=None, description="Deployment zone/region")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate service name format."""
        v = v.strip()
        if not v:
            raise ValueError("Service name cannot be empty")
        # Allow alphanumeric, hyphens, underscores
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
        if not all(c in allowed for c in v):
            raise ValueError(
                "Service name can only contain alphanumeric characters, hyphens, underscores, and dots"
            )
        return v


class EdgeData(BaseModel):
    """
    Schema for a dependency edge.

    Represents a call relationship between two services.
    """

    source: str = Field(..., alias="from", min_length=1, description="Source service name")
    target: str = Field(..., alias="to", min_length=1, description="Target service name")
    call_rate: float = Field(default=0.0, ge=0, description="Calls per second")
    p50_latency: float = Field(default=0.0, ge=0, alias="p50", description="Median latency (ms)")
    p95_latency: float = Field(default=0.0, ge=0, alias="p95", description="95th percentile latency (ms)")
    error_rate: float = Field(default=0.0, ge=0, le=1, description="Error rate (0-1)")
    cost: float = Field(default=0.0, ge=0, description="Cost per call")

    model_config = {"populate_by_name": True}

    @field_validator("source", "target")
    @classmethod
    def validate_service_names(cls, v: str) -> str:
        """Validate service name format in edge definition."""
        v = v.strip()
        if not v:
            raise ValueError("Service name cannot be empty")
        return v


class ServiceTopology(BaseModel):
    """
    Schema for complete service topology.

    Contains all services and their dependencies.
    """

    services: list[ServiceData] = Field(
        default_factory=list,
        description="List of services"
    )
    edges: list[EdgeData] = Field(
        default_factory=list,
        description="List of service dependencies"
    )

    @field_validator("edges")
    @classmethod
    def validate_no_self_loops(cls, edges: list[EdgeData]) -> list[EdgeData]:
        """Ensure no self-referencing edges."""
        for edge in edges:
            if edge.source == edge.target:
                raise ValueError(f"Self-loop detected: {edge.source} -> {edge.target}")
        return edges


class OptimizationOptions(BaseModel):
    """Options for the optimization analysis."""

    goal: str = Field(
        default="balanced",
        description="Optimization goal: latency, paths, load, or balanced"
    )
    k: int = Field(default=5, ge=1, le=100, description="Number of shortcuts to suggest")
    alpha: float = Field(default=1.0, ge=0, description="Weight for path length")
    beta: float = Field(default=1.0, ge=0, description="Weight for max betweenness")
    gamma: float = Field(default=0.1, ge=0, description="Weight for cost")

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, v: str) -> str:
        """Validate optimization goal."""
        valid_goals = {"latency", "paths", "load", "balanced"}
        v = v.lower()
        if v not in valid_goals:
            raise ValueError(f"Goal must be one of: {valid_goals}")
        return v


class PolicyConfig(BaseModel):
    """Policy constraints for optimization."""

    forbidden_pairs: list[list[str]] = Field(
        default_factory=list,
        description="Pairs of services that cannot have direct edges"
    )
    allowed_zones: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Zone connectivity rules"
    )
    max_new_edges_per_service: int = Field(
        default=3,
        ge=1,
        description="Maximum new edges per service"
    )
    require_same_zone: bool = Field(
        default=False,
        description="Require shortcuts within same zone"
    )
    min_path_length_to_shortcut: int = Field(
        default=2,
        ge=2,
        description="Minimum path length to consider for shortcut"
    )


class AnalyzeRequest(BaseModel):
    """
    Request schema for the /analyze endpoint.
    """

    services: list[ServiceData] = Field(..., description="List of services")
    edges: list[EdgeData] = Field(..., description="List of service dependencies")
    options: OptimizationOptions = Field(
        default_factory=OptimizationOptions,
        description="Optimization options"
    )
    policy: PolicyConfig | None = Field(
        default=None,
        description="Policy constraints"
    )


class NodeMetricsResponse(BaseModel):
    """Metrics for a single node."""

    name: str
    in_degree: int
    out_degree: int
    total_degree: int
    betweenness_centrality: float
    closeness_centrality: float
    clustering_coefficient: float
    pagerank: float
    incoming_load: float
    outgoing_load: float
    is_hub: bool
    is_bottleneck: bool
    vulnerability_score: float


class GraphMetricsResponse(BaseModel):
    """Global graph metrics."""

    node_count: int
    edge_count: int
    density: float
    average_path_length: float
    weighted_average_path_length: float
    diameter: int
    average_clustering: float
    is_connected: bool
    strongly_connected_components: int
    weakly_connected_components: int
    max_betweenness: float
    total_load: float
    hub_count: int
    bottleneck_count: int
    small_world_coefficient: float


class ShortcutSuggestion(BaseModel):
    """A suggested shortcut edge."""

    source: str = Field(..., alias="from")
    target: str = Field(..., alias="to")
    improvement: float
    delta_path_length: float
    delta_max_betweenness: float
    risk_score: float
    confidence: float
    score: float
    rationale: str
    estimated_latency: float

    model_config = {"populate_by_name": True}


class GraphSummary(BaseModel):
    """Summary of graph characteristics."""

    total_services: int
    total_dependencies: int
    hub_services: list[str]
    bottleneck_services: list[str]
    most_connected_service: str | None
    highest_load_service: str | None
    is_small_world: bool
    recommendations: list[str]


class AnalyzeResponse(BaseModel):
    """
    Response schema for the /analyze endpoint.
    """

    metrics: GraphMetricsResponse
    node_metrics: list[NodeMetricsResponse]
    shortcuts: list[ShortcutSuggestion]
    graph_summary: GraphSummary
    analysis_metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    detail: str | None = None
    code: str | None = None
