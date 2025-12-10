"""
Pytest configuration and shared fixtures.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Generator

import networkx as nx
import pytest

from smallworld.core.graph_builder import GraphBuilder
from smallworld.io.schemas import EdgeData, ServiceData, ServiceTopology


@pytest.fixture
def simple_topology() -> ServiceTopology:
    """Create a simple 3-node topology for testing."""
    return ServiceTopology(
        services=[
            ServiceData(name="gateway", replicas=2, tags=["frontend"]),
            ServiceData(name="auth", replicas=3, tags=["critical"]),
            ServiceData(name="users", replicas=2, tags=["backend"]),
        ],
        edges=[
            EdgeData(source="gateway", target="auth", call_rate=100.0, p50_latency=10.0),
            EdgeData(source="auth", target="users", call_rate=80.0, p50_latency=15.0),
        ],
    )


@pytest.fixture
def complex_topology() -> ServiceTopology:
    """Create a more complex topology with multiple paths."""
    return ServiceTopology(
        services=[
            ServiceData(name="gateway", replicas=2),
            ServiceData(name="auth", replicas=3),
            ServiceData(name="users", replicas=2),
            ServiceData(name="orders", replicas=2),
            ServiceData(name="payments", replicas=3),
            ServiceData(name="inventory", replicas=2),
            ServiceData(name="notifications", replicas=1),
        ],
        edges=[
            EdgeData(source="gateway", target="auth", call_rate=100.0, p50_latency=10.0),
            EdgeData(source="gateway", target="orders", call_rate=50.0, p50_latency=12.0),
            EdgeData(source="auth", target="users", call_rate=80.0, p50_latency=15.0),
            EdgeData(source="orders", target="payments", call_rate=40.0, p50_latency=20.0),
            EdgeData(source="orders", target="inventory", call_rate=45.0, p50_latency=8.0),
            EdgeData(source="payments", target="notifications", call_rate=35.0, p50_latency=5.0),
            EdgeData(source="inventory", target="notifications", call_rate=10.0, p50_latency=5.0),
        ],
    )


@pytest.fixture
def chain_topology() -> ServiceTopology:
    """Create a linear chain topology (worst case for path length)."""
    services = [ServiceData(name=f"service_{i}") for i in range(6)]
    edges = [
        EdgeData(source=f"service_{i}", target=f"service_{i+1}", call_rate=10.0, p50_latency=10.0)
        for i in range(5)
    ]
    return ServiceTopology(services=services, edges=edges)


@pytest.fixture
def star_topology() -> ServiceTopology:
    """Create a star topology (hub and spoke)."""
    services = [ServiceData(name="hub")] + [
        ServiceData(name=f"spoke_{i}") for i in range(5)
    ]
    edges = [
        EdgeData(source="hub", target=f"spoke_{i}", call_rate=20.0, p50_latency=5.0)
        for i in range(5)
    ]
    return ServiceTopology(services=services, edges=edges)


@pytest.fixture
def disconnected_topology() -> ServiceTopology:
    """Create a topology with disconnected components."""
    return ServiceTopology(
        services=[
            ServiceData(name="a1"),
            ServiceData(name="a2"),
            ServiceData(name="b1"),
            ServiceData(name="b2"),
        ],
        edges=[
            EdgeData(source="a1", target="a2", call_rate=10.0, p50_latency=5.0),
            EdgeData(source="b1", target="b2", call_rate=10.0, p50_latency=5.0),
        ],
    )


@pytest.fixture
def simple_graph(simple_topology: ServiceTopology) -> nx.DiGraph:
    """Create a simple graph from the simple topology."""
    builder = GraphBuilder()
    return builder.build_from_topology(simple_topology)


@pytest.fixture
def complex_graph(complex_topology: ServiceTopology) -> nx.DiGraph:
    """Create a complex graph from the complex topology."""
    builder = GraphBuilder()
    return builder.build_from_topology(complex_topology)


@pytest.fixture
def chain_graph(chain_topology: ServiceTopology) -> nx.DiGraph:
    """Create a chain graph from the chain topology."""
    builder = GraphBuilder()
    return builder.build_from_topology(chain_topology)


@pytest.fixture
def sample_topology_dict() -> dict[str, Any]:
    """Return a sample topology as a dictionary."""
    return {
        "services": [
            {"name": "gateway", "replicas": 2, "tags": ["frontend"]},
            {"name": "auth", "replicas": 3, "tags": ["critical"]},
            {"name": "users", "replicas": 2, "tags": ["backend"]},
        ],
        "edges": [
            {"from": "gateway", "to": "auth", "call_rate": 100.0, "p50": 10.0, "p95": 50.0},
            {"from": "auth", "to": "users", "call_rate": 80.0, "p50": 15.0, "p95": 75.0},
        ],
    }


@pytest.fixture
def sample_json_file(sample_topology_dict: dict[str, Any]) -> Generator[Path, None, None]:
    """Create a temporary JSON file with sample topology."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as f:
        json.dump(sample_topology_dict, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def invalid_json_file() -> Generator[Path, None, None]:
    """Create a temporary file with invalid JSON."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write("{ invalid json }")
        temp_path = Path(f.name)

    yield temp_path

    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def analyze_request_dict() -> dict[str, Any]:
    """Return a sample analyze request as a dictionary."""
    return {
        "services": [
            {"name": "gateway", "replicas": 2},
            {"name": "auth", "replicas": 3},
            {"name": "users", "replicas": 2},
            {"name": "orders", "replicas": 2},
        ],
        "edges": [
            {"from": "gateway", "to": "auth", "call_rate": 100.0, "p50": 10.0},
            {"from": "gateway", "to": "orders", "call_rate": 50.0, "p50": 12.0},
            {"from": "auth", "to": "users", "call_rate": 80.0, "p50": 15.0},
            {"from": "orders", "to": "users", "call_rate": 40.0, "p50": 8.0},
        ],
        "options": {
            "goal": "balanced",
            "k": 3,
        },
    }
