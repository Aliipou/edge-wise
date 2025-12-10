"""
Tests for the GraphBuilder module.

Achieves 100% coverage for graph_builder.py
"""

from __future__ import annotations

import pytest
import networkx as nx

from smallworld.core.graph_builder import GraphBuilder
from smallworld.io.schemas import EdgeData, ServiceData, ServiceTopology


class TestGraphBuilder:
    """Tests for GraphBuilder class."""

    def test_init_creates_empty_graph(self) -> None:
        """Test that initialization creates an empty graph."""
        builder = GraphBuilder()
        assert isinstance(builder.graph, nx.DiGraph)
        assert builder.get_node_count() == 0
        assert builder.get_edge_count() == 0

    def test_build_from_topology(self, simple_topology: ServiceTopology) -> None:
        """Test building graph from ServiceTopology."""
        builder = GraphBuilder()
        graph = builder.build_from_topology(simple_topology)

        assert builder.get_node_count() == 3
        assert builder.get_edge_count() == 2
        assert builder.has_node("gateway")
        assert builder.has_node("auth")
        assert builder.has_node("users")
        assert builder.has_edge("gateway", "auth")
        assert builder.has_edge("auth", "users")

    def test_build_from_dict(self, sample_topology_dict: dict) -> None:
        """Test building graph from dictionary."""
        builder = GraphBuilder()
        graph = builder.build_from_dict(sample_topology_dict)

        assert builder.get_node_count() == 3
        assert builder.get_edge_count() == 2

    def test_node_metadata_preserved(self, simple_topology: ServiceTopology) -> None:
        """Test that node metadata is preserved."""
        builder = GraphBuilder()
        graph = builder.build_from_topology(simple_topology)

        # Check node attributes
        assert graph.nodes["gateway"]["replicas"] == 2
        assert "frontend" in graph.nodes["gateway"]["tags"]
        assert graph.nodes["auth"]["replicas"] == 3

    def test_edge_metadata_preserved(self, simple_topology: ServiceTopology) -> None:
        """Test that edge metadata is preserved."""
        builder = GraphBuilder()
        graph = builder.build_from_topology(simple_topology)

        edge_data = graph.edges["gateway", "auth"]
        assert edge_data["call_rate"] == 100.0
        assert edge_data["p50_latency"] == 10.0
        assert edge_data["weight"] == 10.0  # weight defaults to p50_latency

    def test_auto_create_nodes_for_edges(self) -> None:
        """Test that nodes are auto-created when referenced in edges."""
        topology = ServiceTopology(
            services=[],  # No explicit services
            edges=[
                EdgeData(source="a", target="b", call_rate=10.0),
            ],
        )

        builder = GraphBuilder()
        graph = builder.build_from_topology(topology)

        assert builder.has_node("a")
        assert builder.has_node("b")
        assert builder.has_edge("a", "b")

    def test_get_undirected_view(self, simple_topology: ServiceTopology) -> None:
        """Test getting undirected view of graph."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)
        undirected = builder.get_undirected_view()

        assert isinstance(undirected, nx.Graph)
        assert not isinstance(undirected, nx.DiGraph)
        assert undirected.number_of_nodes() == 3

    def test_get_neighbors(self, simple_topology: ServiceTopology) -> None:
        """Test getting successors of a node."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        neighbors = builder.get_neighbors("gateway")
        assert "auth" in neighbors
        assert len(neighbors) == 1

    def test_get_neighbors_nonexistent_node(self, simple_topology: ServiceTopology) -> None:
        """Test getting neighbors of nonexistent node."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        neighbors = builder.get_neighbors("nonexistent")
        assert neighbors == []

    def test_get_predecessors(self, simple_topology: ServiceTopology) -> None:
        """Test getting predecessors of a node."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        predecessors = builder.get_predecessors("auth")
        assert "gateway" in predecessors

    def test_get_predecessors_nonexistent_node(self, simple_topology: ServiceTopology) -> None:
        """Test getting predecessors of nonexistent node."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        predecessors = builder.get_predecessors("nonexistent")
        assert predecessors == []

    def test_add_shortcut_edge(self, simple_topology: ServiceTopology) -> None:
        """Test adding a shortcut edge."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        result = builder.add_shortcut_edge(
            "gateway", "users",
            call_rate=50.0,
            p50_latency=8.0,
        )

        assert result is True
        assert builder.has_edge("gateway", "users")
        assert builder.graph.edges["gateway", "users"]["is_shortcut"] is True

    def test_add_shortcut_edge_already_exists(self, simple_topology: ServiceTopology) -> None:
        """Test adding a shortcut edge that already exists."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        result = builder.add_shortcut_edge("gateway", "auth")
        assert result is False  # Edge already exists

    def test_remove_edge(self, simple_topology: ServiceTopology) -> None:
        """Test removing an edge."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        assert builder.has_edge("gateway", "auth")
        result = builder.remove_edge("gateway", "auth")

        assert result is True
        assert not builder.has_edge("gateway", "auth")

    def test_remove_edge_nonexistent(self, simple_topology: ServiceTopology) -> None:
        """Test removing an edge that doesn't exist."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        result = builder.remove_edge("gateway", "users")
        assert result is False

    def test_copy(self, simple_topology: ServiceTopology) -> None:
        """Test copying the graph builder."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        copy = builder.copy()

        # Verify copy is independent
        assert copy.get_node_count() == builder.get_node_count()
        copy.remove_edge("gateway", "auth")
        assert builder.has_edge("gateway", "auth")  # Original unchanged

    def test_to_dict(self, simple_topology: ServiceTopology) -> None:
        """Test exporting graph to dictionary."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        result = builder.to_dict()

        assert "services" in result
        assert "edges" in result
        assert len(result["services"]) == 3
        assert len(result["edges"]) == 2

    def test_to_dict_preserves_data(self, simple_topology: ServiceTopology) -> None:
        """Test that to_dict preserves node and edge data."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        result = builder.to_dict()

        # Find gateway in services
        gateway = next(s for s in result["services"] if s["name"] == "gateway")
        assert gateway["replicas"] == 2

        # Find gateway->auth edge
        edge = next(
            e for e in result["edges"]
            if e["source"] == "gateway" and e["target"] == "auth"
        )
        assert edge["call_rate"] == 100.0

    def test_edge_weight_zero_latency(self) -> None:
        """Test edge weight when latency is zero."""
        topology = ServiceTopology(
            services=[
                ServiceData(name="a"),
                ServiceData(name="b"),
            ],
            edges=[
                EdgeData(source="a", target="b", call_rate=10.0, p50_latency=0.0),
            ],
        )

        builder = GraphBuilder()
        graph = builder.build_from_topology(topology)

        # Weight should default to 1.0 when p50_latency is 0
        assert graph.edges["a", "b"]["weight"] == 1.0

    def test_has_node_true(self, simple_topology: ServiceTopology) -> None:
        """Test has_node returns True for existing node."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)
        assert builder.has_node("gateway") is True

    def test_has_node_false(self, simple_topology: ServiceTopology) -> None:
        """Test has_node returns False for non-existing node."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)
        assert builder.has_node("nonexistent") is False

    def test_has_edge_true(self, simple_topology: ServiceTopology) -> None:
        """Test has_edge returns True for existing edge."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)
        assert builder.has_edge("gateway", "auth") is True

    def test_has_edge_false(self, simple_topology: ServiceTopology) -> None:
        """Test has_edge returns False for non-existing edge."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)
        assert builder.has_edge("gateway", "users") is False

    def test_empty_topology(self) -> None:
        """Test handling empty topology."""
        topology = ServiceTopology(services=[], edges=[])
        builder = GraphBuilder()
        graph = builder.build_from_topology(topology)

        assert builder.get_node_count() == 0
        assert builder.get_edge_count() == 0

    def test_service_with_zone(self) -> None:
        """Test service with zone attribute."""
        topology = ServiceTopology(
            services=[
                ServiceData(name="svc1", zone="us-east-1"),
                ServiceData(name="svc2", zone="us-west-2"),
            ],
            edges=[
                EdgeData(source="svc1", target="svc2", call_rate=10.0),
            ],
        )

        builder = GraphBuilder()
        graph = builder.build_from_topology(topology)

        assert graph.nodes["svc1"]["zone"] == "us-east-1"
        assert graph.nodes["svc2"]["zone"] == "us-west-2"

    def test_add_shortcut_with_defaults(self, simple_topology: ServiceTopology) -> None:
        """Test adding shortcut with default values."""
        builder = GraphBuilder()
        builder.build_from_topology(simple_topology)

        builder.add_shortcut_edge("gateway", "users")
        edge = builder.graph.edges["gateway", "users"]

        assert edge["call_rate"] == 0.0
        assert edge["p50_latency"] == 1.0
        assert edge["p95_latency"] == 5.0
        assert edge["error_rate"] == 0.0
        assert edge["cost"] == 0.0
