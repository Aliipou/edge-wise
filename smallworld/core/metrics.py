"""
Metrics Calculator Module

Computes network metrics for service dependency graphs:
- Degree centrality
- Betweenness centrality
- Closeness centrality
- Clustering coefficient
- Average path length
- Load distribution
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx
import numpy as np


@dataclass
class NodeMetrics:
    """Metrics for a single node (service)."""

    name: str
    in_degree: int = 0
    out_degree: int = 0
    total_degree: int = 0
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    clustering_coefficient: float = 0.0
    pagerank: float = 0.0
    incoming_load: float = 0.0
    outgoing_load: float = 0.0
    is_hub: bool = False
    is_bottleneck: bool = False
    vulnerability_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "total_degree": self.total_degree,
            "betweenness_centrality": round(self.betweenness_centrality, 6),
            "closeness_centrality": round(self.closeness_centrality, 6),
            "clustering_coefficient": round(self.clustering_coefficient, 6),
            "pagerank": round(self.pagerank, 6),
            "incoming_load": round(self.incoming_load, 2),
            "outgoing_load": round(self.outgoing_load, 2),
            "is_hub": self.is_hub,
            "is_bottleneck": self.is_bottleneck,
            "vulnerability_score": round(self.vulnerability_score, 4),
        }


@dataclass
class GraphMetrics:
    """Global metrics for the entire graph."""

    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    average_path_length: float = 0.0
    weighted_average_path_length: float = 0.0
    diameter: int = 0
    average_clustering: float = 0.0
    is_connected: bool = False
    strongly_connected_components: int = 0
    weakly_connected_components: int = 0
    max_betweenness: float = 0.0
    total_load: float = 0.0
    hub_count: int = 0
    bottleneck_count: int = 0
    small_world_coefficient: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "density": round(self.density, 6),
            "average_path_length": round(self.average_path_length, 4),
            "weighted_average_path_length": round(self.weighted_average_path_length, 4),
            "diameter": self.diameter,
            "average_clustering": round(self.average_clustering, 6),
            "is_connected": self.is_connected,
            "strongly_connected_components": self.strongly_connected_components,
            "weakly_connected_components": self.weakly_connected_components,
            "max_betweenness": round(self.max_betweenness, 6),
            "total_load": round(self.total_load, 2),
            "hub_count": self.hub_count,
            "bottleneck_count": self.bottleneck_count,
            "small_world_coefficient": round(self.small_world_coefficient, 4),
        }


@dataclass
class MetricsCalculator:
    """
    Calculates network metrics for service dependency graphs.

    Uses NetworkX for graph algorithms and computes both per-node
    and global metrics relevant to microservice topology analysis.
    """

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    hub_threshold: float = 0.7  # Top 30% by degree are hubs
    bottleneck_threshold: float = 0.8  # Top 20% by betweenness are bottlenecks

    def set_graph(self, graph: nx.DiGraph) -> None:
        """Set the graph to analyze."""
        self.graph = graph

    def calculate_all(self) -> tuple[GraphMetrics, dict[str, NodeMetrics]]:
        """
        Calculate all metrics for the graph.

        Returns:
            Tuple of (global_metrics, node_metrics_dict).
        """
        if self.graph.number_of_nodes() == 0:
            return GraphMetrics(), {}

        # Calculate node-level metrics
        node_metrics = self._calculate_node_metrics()

        # Calculate global metrics
        graph_metrics = self._calculate_graph_metrics(node_metrics)

        # Identify hubs and bottlenecks
        self._identify_hubs_and_bottlenecks(node_metrics, graph_metrics)

        return graph_metrics, node_metrics

    def _calculate_node_metrics(self) -> dict[str, NodeMetrics]:
        """Calculate metrics for each node."""
        metrics: dict[str, NodeMetrics] = {}

        # Degree centrality
        in_degrees = dict(self.graph.in_degree())
        out_degrees = dict(self.graph.out_degree())

        # Betweenness centrality (normalized)
        try:
            betweenness = nx.betweenness_centrality(self.graph, normalized=True)
        except Exception:
            betweenness = {n: 0.0 for n in self.graph.nodes()}

        # Closeness centrality
        try:
            closeness = nx.closeness_centrality(self.graph)
        except Exception:
            closeness = {n: 0.0 for n in self.graph.nodes()}

        # Clustering coefficient (on undirected version)
        undirected = self.graph.to_undirected()
        try:
            clustering = nx.clustering(undirected)
        except Exception:
            clustering = {n: 0.0 for n in self.graph.nodes()}

        # PageRank
        try:
            pagerank = nx.pagerank(self.graph, alpha=0.85)
        except Exception:
            pagerank = {n: 1.0 / self.graph.number_of_nodes() for n in self.graph.nodes()}

        # Load calculation
        incoming_load = self._calculate_incoming_load()
        outgoing_load = self._calculate_outgoing_load()

        for node in self.graph.nodes():
            metrics[node] = NodeMetrics(
                name=node,
                in_degree=in_degrees.get(node, 0),
                out_degree=out_degrees.get(node, 0),
                total_degree=in_degrees.get(node, 0) + out_degrees.get(node, 0),
                betweenness_centrality=betweenness.get(node, 0.0),
                closeness_centrality=closeness.get(node, 0.0),
                clustering_coefficient=clustering.get(node, 0.0),
                pagerank=pagerank.get(node, 0.0),
                incoming_load=incoming_load.get(node, 0.0),
                outgoing_load=outgoing_load.get(node, 0.0),
            )

        return metrics

    def _calculate_incoming_load(self) -> dict[str, float]:
        """Calculate incoming call rate load for each node."""
        load: dict[str, float] = {n: 0.0 for n in self.graph.nodes()}
        for _, target, data in self.graph.edges(data=True):
            call_rate = data.get("call_rate", 0.0)
            load[target] += call_rate
        return load

    def _calculate_outgoing_load(self) -> dict[str, float]:
        """Calculate outgoing call rate load for each node."""
        load: dict[str, float] = {n: 0.0 for n in self.graph.nodes()}
        for source, _, data in self.graph.edges(data=True):
            call_rate = data.get("call_rate", 0.0)
            load[source] += call_rate
        return load

    def _calculate_graph_metrics(
        self, node_metrics: dict[str, NodeMetrics]
    ) -> GraphMetrics:
        """Calculate global graph metrics."""
        n = self.graph.number_of_nodes()
        m = self.graph.number_of_edges()

        if n == 0:
            return GraphMetrics()

        # Density
        max_edges = n * (n - 1)  # Directed graph
        density = m / max_edges if max_edges > 0 else 0.0

        # Path lengths
        avg_path_length = self._calculate_average_path_length()
        weighted_avg_path_length = self._calculate_weighted_average_path_length()

        # Diameter
        diameter = self._calculate_diameter()

        # Average clustering
        undirected = self.graph.to_undirected()
        try:
            avg_clustering = nx.average_clustering(undirected)
        except Exception:
            avg_clustering = 0.0

        # Connected components
        weakly_connected = nx.number_weakly_connected_components(self.graph)
        strongly_connected = nx.number_strongly_connected_components(self.graph)
        is_connected = weakly_connected == 1

        # Max betweenness
        max_betweenness = max(
            (nm.betweenness_centrality for nm in node_metrics.values()),
            default=0.0
        )

        # Total load
        total_load = sum(nm.incoming_load for nm in node_metrics.values())

        # Small-world coefficient (clustering / path_length ratio)
        # Compare to random graph of same size
        small_world_coef = self._calculate_small_world_coefficient(
            avg_clustering, avg_path_length, n, m
        )

        return GraphMetrics(
            node_count=n,
            edge_count=m,
            density=density,
            average_path_length=avg_path_length,
            weighted_average_path_length=weighted_avg_path_length,
            diameter=diameter,
            average_clustering=avg_clustering,
            is_connected=is_connected,
            strongly_connected_components=strongly_connected,
            weakly_connected_components=weakly_connected,
            max_betweenness=max_betweenness,
            total_load=total_load,
            small_world_coefficient=small_world_coef,
        )

    def _calculate_average_path_length(self) -> float:
        """Calculate average shortest path length (unweighted)."""
        try:
            if nx.is_weakly_connected(self.graph):
                # Use largest strongly connected component
                largest_scc = max(
                    nx.strongly_connected_components(self.graph),
                    key=len
                )
                if len(largest_scc) > 1:
                    subgraph = self.graph.subgraph(largest_scc)
                    return nx.average_shortest_path_length(subgraph)

            # Calculate for all reachable pairs
            total_length = 0.0
            count = 0
            for source in self.graph.nodes():
                lengths = nx.single_source_shortest_path_length(self.graph, source)
                for target, length in lengths.items():
                    if source != target:
                        total_length += length
                        count += 1

            return total_length / count if count > 0 else 0.0
        except Exception:
            return 0.0

    def _calculate_weighted_average_path_length(self) -> float:
        """Calculate average shortest path length using latency weights."""
        try:
            total_length = 0.0
            count = 0

            for source in self.graph.nodes():
                try:
                    lengths = nx.single_source_dijkstra_path_length(
                        self.graph, source, weight="weight"
                    )
                    for target, length in lengths.items():
                        if source != target:
                            total_length += length
                            count += 1
                except nx.NetworkXNoPath:
                    continue

            return total_length / count if count > 0 else 0.0
        except Exception:
            return 0.0

    def _calculate_diameter(self) -> int:
        """Calculate graph diameter (longest shortest path)."""
        try:
            if nx.is_strongly_connected(self.graph):
                return nx.diameter(self.graph)

            # Find diameter of largest SCC
            largest_scc = max(
                nx.strongly_connected_components(self.graph),
                key=len
            )
            if len(largest_scc) > 1:
                subgraph = self.graph.subgraph(largest_scc)
                return nx.diameter(subgraph)

            return 0
        except Exception:
            return 0

    def _calculate_small_world_coefficient(
        self,
        clustering: float,
        path_length: float,
        n: int,
        m: int,
    ) -> float:
        """
        Calculate small-world coefficient.

        Compares clustering and path length to equivalent random graph.
        Values > 1 indicate small-world properties.
        """
        if path_length == 0 or n < 3:
            return 0.0

        # Expected values for Erdos-Renyi random graph
        p = m / (n * (n - 1)) if n > 1 else 0

        # Random clustering coefficient ≈ p
        random_clustering = p

        # Random path length ≈ ln(n) / ln(k) where k = average degree
        avg_degree = 2 * m / n if n > 0 else 0
        if avg_degree > 1:
            random_path_length = np.log(n) / np.log(avg_degree)
        else:
            random_path_length = n / 2  # Fallback

        if random_clustering == 0 or random_path_length == 0:
            return 0.0

        # Small-world coefficient = (C/C_random) / (L/L_random)
        gamma = clustering / random_clustering if random_clustering > 0 else 0
        # Note: lambda_ratio cannot be 0 here because:
        # 1. path_length > 0 is guaranteed by check on line 352
        # 2. random_path_length > 0 is guaranteed by check above
        lambda_ratio = path_length / random_path_length

        return gamma / lambda_ratio

    def _identify_hubs_and_bottlenecks(
        self,
        node_metrics: dict[str, NodeMetrics],
        graph_metrics: GraphMetrics,
    ) -> None:
        """Identify hub nodes and bottleneck nodes."""
        if not node_metrics:
            return

        # Get degree and betweenness distributions
        degrees = [nm.total_degree for nm in node_metrics.values()]
        betweenness_values = [nm.betweenness_centrality for nm in node_metrics.values()]

        # Calculate thresholds
        hub_degree_threshold = np.percentile(degrees, self.hub_threshold * 100)
        bottleneck_threshold = np.percentile(
            betweenness_values, self.bottleneck_threshold * 100
        )

        hub_count = 0
        bottleneck_count = 0

        for nm in node_metrics.values():
            # Hub: high degree connectivity
            if nm.total_degree >= hub_degree_threshold:
                nm.is_hub = True
                hub_count += 1

            # Bottleneck: high betweenness (many paths go through)
            if nm.betweenness_centrality >= bottleneck_threshold:
                nm.is_bottleneck = True
                bottleneck_count += 1

            # Vulnerability: combination of being critical and high load
            nm.vulnerability_score = self._calculate_vulnerability(nm)

        graph_metrics.hub_count = hub_count
        graph_metrics.bottleneck_count = bottleneck_count

    def _calculate_vulnerability(self, nm: NodeMetrics) -> float:
        """
        Calculate vulnerability score for a node.

        High vulnerability means removing this node would significantly
        impact the network.
        """
        # Normalize factors
        betweenness_factor = nm.betweenness_centrality
        load_factor = nm.incoming_load + nm.outgoing_load

        # Normalize load to 0-1 range (rough heuristic)
        max_load = 10000  # Assumed max load for normalization
        normalized_load = min(load_factor / max_load, 1.0)

        # Weighted combination
        return 0.6 * betweenness_factor + 0.4 * normalized_load

    def get_objective_value(
        self,
        alpha: float = 1.0,
        beta: float = 1.0,
        gamma: float = 0.0,
    ) -> float:
        """
        Calculate the optimization objective value.

        OBJ(G) = α * avg_path_length + β * max_betweenness + γ * total_cost

        Lower is better.
        """
        graph_metrics, node_metrics = self.calculate_all()

        # Get total cost from edges
        total_cost = sum(
            data.get("cost", 0.0)
            for _, _, data in self.graph.edges(data=True)
        )

        return (
            alpha * graph_metrics.average_path_length +
            beta * graph_metrics.max_betweenness +
            gamma * total_cost
        )
