"""
Graph Builder Module

Constructs directed weighted graphs from service dependency data.
Supports JSON input with service metadata and edge weights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from smallworld.io.schemas import EdgeData, ServiceData, ServiceTopology


@dataclass
class GraphBuilder:
    """
    Builds NetworkX graphs from service topology definitions.

    The graph is a directed weighted graph G = (V, E, w) where:
    - V: services (nodes) with metadata
    - E: service-to-service calls (edges)
    - w: edge weights (call_rate, latency, etc.)
    """

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    def build_from_topology(self, topology: ServiceTopology) -> nx.DiGraph:
        """
        Build a directed graph from a ServiceTopology object.

        Args:
            topology: The service topology containing services and edges.

        Returns:
            A NetworkX DiGraph with all service nodes and dependency edges.
        """
        self.graph = nx.DiGraph()

        # Add nodes with metadata
        for service in topology.services:
            self._add_service_node(service)

        # Add edges with weights
        for edge in topology.edges:
            self._add_dependency_edge(edge)

        return self.graph

    def build_from_dict(self, data: dict[str, Any]) -> nx.DiGraph:
        """
        Build graph from a raw dictionary.

        Args:
            data: Dictionary with 'services' and 'edges' keys.

        Returns:
            A NetworkX DiGraph.
        """
        topology = ServiceTopology.model_validate(data)
        return self.build_from_topology(topology)

    def _add_service_node(self, service: ServiceData) -> None:
        """Add a service as a node with its metadata."""
        self.graph.add_node(
            service.name,
            replicas=service.replicas,
            tags=service.tags,
            criticality=service.criticality,
            zone=service.zone,
        )

    def _add_dependency_edge(self, edge: EdgeData) -> None:
        """Add a dependency edge with call metrics."""
        # Ensure nodes exist (auto-create if needed)
        if edge.source not in self.graph:
            self.graph.add_node(edge.source)
        if edge.target not in self.graph:
            self.graph.add_node(edge.target)

        self.graph.add_edge(
            edge.source,
            edge.target,
            call_rate=edge.call_rate,
            p50_latency=edge.p50_latency,
            p95_latency=edge.p95_latency,
            error_rate=edge.error_rate,
            cost=edge.cost,
            # Compute unified weight for pathfinding (latency-based by default)
            weight=edge.p50_latency if edge.p50_latency > 0 else 1.0,
        )

    def get_undirected_view(self) -> nx.Graph:
        """
        Get an undirected view of the graph for certain metrics.

        Some metrics (like clustering coefficient) are typically computed
        on undirected graphs.

        Returns:
            Undirected copy of the graph.
        """
        return self.graph.to_undirected()

    def get_node_count(self) -> int:
        """Return the number of nodes (services) in the graph."""
        return self.graph.number_of_nodes()

    def get_edge_count(self) -> int:
        """Return the number of edges (dependencies) in the graph."""
        return self.graph.number_of_edges()

    def has_node(self, name: str) -> bool:
        """Check if a service exists in the graph."""
        return name in self.graph

    def has_edge(self, source: str, target: str) -> bool:
        """Check if a dependency exists between two services."""
        return self.graph.has_edge(source, target)

    def get_neighbors(self, node: str) -> list[str]:
        """Get all services that this service calls (outgoing edges)."""
        if node not in self.graph:
            return []
        return list(self.graph.successors(node))

    def get_predecessors(self, node: str) -> list[str]:
        """Get all services that call this service (incoming edges)."""
        if node not in self.graph:
            return []
        return list(self.graph.predecessors(node))

    def add_shortcut_edge(
        self,
        source: str,
        target: str,
        call_rate: float = 0.0,
        p50_latency: float = 1.0,
        p95_latency: float = 5.0,
        error_rate: float = 0.0,
        cost: float = 0.0,
    ) -> bool:
        """
        Add a new shortcut edge to the graph.

        Args:
            source: Source service name.
            target: Target service name.
            call_rate: Expected call rate.
            p50_latency: Expected median latency.
            p95_latency: Expected 95th percentile latency.
            error_rate: Expected error rate.
            cost: Associated cost.

        Returns:
            True if edge was added, False if it already exists.
        """
        if self.has_edge(source, target):
            return False

        self.graph.add_edge(
            source,
            target,
            call_rate=call_rate,
            p50_latency=p50_latency,
            p95_latency=p95_latency,
            error_rate=error_rate,
            cost=cost,
            weight=p50_latency if p50_latency > 0 else 1.0,
            is_shortcut=True,
        )
        return True

    def remove_edge(self, source: str, target: str) -> bool:
        """
        Remove an edge from the graph.

        Args:
            source: Source service name.
            target: Target service name.

        Returns:
            True if edge was removed, False if it didn't exist.
        """
        if not self.has_edge(source, target):
            return False
        self.graph.remove_edge(source, target)
        return True

    def copy(self) -> "GraphBuilder":
        """Create a deep copy of this graph builder."""
        new_builder = GraphBuilder()
        new_builder.graph = self.graph.copy()
        return new_builder

    def to_dict(self) -> dict[str, Any]:
        """
        Export the graph to a dictionary format.

        Returns:
            Dictionary with nodes and edges.
        """
        nodes = []
        for node, attrs in self.graph.nodes(data=True):
            nodes.append({
                "name": node,
                **{k: v for k, v in attrs.items() if v is not None}
            })

        edges = []
        for source, target, attrs in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                **{k: v for k, v in attrs.items() if k != "weight"}
            })

        return {"services": nodes, "edges": edges}
