"""
Shortcut Optimizer Module

Identifies and ranks optimal shortcut edges to add to the service graph
to reduce average path length, decrease bottleneck load, and improve
overall network efficiency.

Uses small-world network theory principles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import networkx as nx
import numpy as np

from smallworld.core.metrics import MetricsCalculator


class OptimizationGoal(str, Enum):
    """Optimization objective types."""

    LATENCY = "latency"  # Minimize weighted path length (latency)
    PATHS = "paths"  # Minimize unweighted average path length
    LOAD = "load"  # Minimize max betweenness (load distribution)
    BALANCED = "balanced"  # Balance all objectives


@dataclass
class ShortcutCandidate:
    """A candidate shortcut edge with analysis results."""

    source: str
    target: str
    delta_objective: float = 0.0
    delta_path_length: float = 0.0
    delta_max_betweenness: float = 0.0
    delta_weighted_path_length: float = 0.0
    risk_score: float = 0.0
    confidence: float = 0.0
    score: float = 0.0
    rationale: str = ""
    estimated_latency: float = 1.0
    estimated_call_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "from": self.source,
            "to": self.target,
            "improvement": round(-self.delta_objective, 4),
            "delta_path_length": round(self.delta_path_length, 4),
            "delta_max_betweenness": round(self.delta_max_betweenness, 4),
            "risk_score": round(self.risk_score, 4),
            "confidence": round(self.confidence, 4),
            "score": round(self.score, 4),
            "rationale": self.rationale,
            "estimated_latency": round(self.estimated_latency, 2),
        }


@dataclass
class PolicyConstraints:
    """Policy constraints for shortcut generation."""

    forbidden_pairs: list[tuple[str, str]] = field(default_factory=list)
    allowed_zones: dict[str, list[str]] = field(default_factory=dict)
    max_new_edges_per_service: int = 3
    require_same_zone: bool = False
    min_path_length_to_shortcut: int = 2

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyConstraints":
        """Create from dictionary."""
        return cls(
            forbidden_pairs=[
                tuple(p) for p in data.get("forbidden_pairs", [])
            ],
            allowed_zones=data.get("allowed_zones", {}),
            max_new_edges_per_service=data.get("max_new_edges_per_service", 3),
            require_same_zone=data.get("require_same_zone", False),
            min_path_length_to_shortcut=data.get("min_path_length_to_shortcut", 2),
        )


@dataclass
class ShortcutOptimizer:
    """
    Optimizer for finding beneficial shortcut edges.

    Uses simulation-based approach to evaluate the impact of each
    potential shortcut on the optimization objective.
    """

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    goal: OptimizationGoal = OptimizationGoal.BALANCED
    alpha: float = 1.0  # Weight for path length
    beta: float = 1.0  # Weight for max betweenness
    gamma: float = 0.1  # Weight for cost
    epsilon: float = 0.01  # Small value to avoid division by zero

    def set_graph(self, graph: nx.DiGraph) -> None:
        """Set the graph to optimize."""
        self.graph = graph

    def set_goal(self, goal: str | OptimizationGoal) -> None:
        """Set the optimization goal."""
        if isinstance(goal, OptimizationGoal):
            self.goal = goal
        else:
            self.goal = OptimizationGoal(goal.lower())

        # Adjust weights based on goal
        if self.goal == OptimizationGoal.LATENCY:
            self.alpha = 2.0
            self.beta = 0.5
            self.gamma = 0.1
        elif self.goal == OptimizationGoal.PATHS:
            self.alpha = 2.0
            self.beta = 0.3
            self.gamma = 0.0
        elif self.goal == OptimizationGoal.LOAD:
            self.alpha = 0.5
            self.beta = 2.0
            self.gamma = 0.1
        else:  # BALANCED
            self.alpha = 1.0
            self.beta = 1.0
            self.gamma = 0.1

    def find_shortcuts(
        self,
        k: int = 5,
        policy: PolicyConstraints | None = None,
    ) -> list[ShortcutCandidate]:
        """
        Find the top k beneficial shortcuts.

        Args:
            k: Number of shortcuts to suggest.
            policy: Optional policy constraints.

        Returns:
            List of top k shortcut candidates ranked by score.
        """
        if self.graph.number_of_nodes() < 2:
            return []

        policy = policy or PolicyConstraints()

        # Generate candidate pairs
        candidates = self._generate_candidates(policy)

        # Evaluate each candidate
        evaluated = []
        for source, target in candidates:
            candidate = self._evaluate_candidate(source, target, policy)
            if candidate and candidate.score > 0:
                evaluated.append(candidate)

        # Sort by score (higher is better) and return top k
        evaluated.sort(key=lambda c: c.score, reverse=True)
        return evaluated[:k]

    def _generate_candidates(
        self, policy: PolicyConstraints
    ) -> list[tuple[str, str]]:
        """Generate candidate shortcut pairs based on policy."""
        candidates = []
        nodes = list(self.graph.nodes())

        # Track edges per node for max_new_edges constraint
        edge_counts: dict[str, int] = {n: 0 for n in nodes}

        for source in nodes:
            if edge_counts[source] >= policy.max_new_edges_per_service:
                continue

            for target in nodes:
                if source == target:
                    continue

                # Skip if edge already exists
                if self.graph.has_edge(source, target):
                    continue

                # Check forbidden pairs
                if (source, target) in policy.forbidden_pairs:
                    continue
                if (target, source) in policy.forbidden_pairs:
                    continue

                # Check zone constraints
                if policy.require_same_zone:
                    source_zone = self.graph.nodes[source].get("zone", "")
                    target_zone = self.graph.nodes[target].get("zone", "")
                    if source_zone and target_zone and source_zone != target_zone:
                        continue

                # Check allowed zones
                if policy.allowed_zones:
                    source_zone = self.graph.nodes[source].get("zone", "")
                    if source_zone in policy.allowed_zones:
                        target_zone = self.graph.nodes[target].get("zone", "")
                        if target_zone not in policy.allowed_zones[source_zone]:
                            continue

                # Check minimum path length requirement
                try:
                    path_length = nx.shortest_path_length(
                        self.graph, source, target
                    )
                    if path_length < policy.min_path_length_to_shortcut:
                        continue
                except nx.NetworkXNoPath:
                    # No path exists - this could be a valuable shortcut
                    pass

                candidates.append((source, target))

        return candidates

    def _evaluate_candidate(
        self,
        source: str,
        target: str,
        policy: PolicyConstraints,
    ) -> ShortcutCandidate | None:
        """Evaluate a single shortcut candidate."""
        # Create baseline metrics calculator
        baseline_calc = MetricsCalculator(graph=self.graph)
        baseline_metrics, baseline_node_metrics = baseline_calc.calculate_all()
        baseline_obj = self._calculate_objective(baseline_metrics)

        # Create modified graph with shortcut
        modified_graph = self.graph.copy()

        # Estimate latency for the new edge
        estimated_latency = self._estimate_shortcut_latency(source, target)

        modified_graph.add_edge(
            source,
            target,
            weight=estimated_latency,
            call_rate=0.0,
            p50_latency=estimated_latency,
            p95_latency=estimated_latency * 2,
            error_rate=0.0,
            cost=0.0,
            is_shortcut=True,
        )

        # Calculate metrics for modified graph
        modified_calc = MetricsCalculator(graph=modified_graph)
        modified_metrics, modified_node_metrics = modified_calc.calculate_all()
        modified_obj = self._calculate_objective(modified_metrics)

        # Calculate deltas
        delta_obj = modified_obj - baseline_obj
        delta_path = (
            modified_metrics.average_path_length -
            baseline_metrics.average_path_length
        )
        delta_betweenness = (
            modified_metrics.max_betweenness -
            baseline_metrics.max_betweenness
        )
        delta_weighted = (
            modified_metrics.weighted_average_path_length -
            baseline_metrics.weighted_average_path_length
        )

        # Calculate risk score
        risk_score = self._calculate_risk_score(
            source, target, modified_node_metrics
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            delta_obj, baseline_metrics, modified_metrics
        )

        # Calculate final score (improvement per unit risk)
        if delta_obj >= 0:
            # No improvement or worse
            return None

        improvement = -delta_obj  # Make positive
        score = improvement / (risk_score + self.epsilon)

        # Generate rationale
        rationale = self._generate_rationale(
            source, target, delta_path, delta_betweenness, delta_weighted
        )

        return ShortcutCandidate(
            source=source,
            target=target,
            delta_objective=delta_obj,
            delta_path_length=delta_path,
            delta_max_betweenness=delta_betweenness,
            delta_weighted_path_length=delta_weighted,
            risk_score=risk_score,
            confidence=confidence,
            score=score,
            rationale=rationale,
            estimated_latency=estimated_latency,
        )

    def _calculate_objective(self, metrics: Any) -> float:
        """Calculate optimization objective from metrics."""
        return (
            self.alpha * metrics.average_path_length +
            self.beta * metrics.max_betweenness +
            self.gamma * 0  # Cost term (would need edge data)
        )

    def _estimate_shortcut_latency(self, source: str, target: str) -> float:
        """
        Estimate latency for a direct shortcut edge.

        Uses heuristics based on existing edge latencies and path structure.
        """
        # Get average latency from existing edges
        latencies = [
            data.get("p50_latency", 1.0)
            for _, _, data in self.graph.edges(data=True)
            if data.get("p50_latency", 0) > 0
        ]

        if not latencies:
            return 1.0

        avg_latency = np.mean(latencies)

        # Estimate based on typical direct connection
        # Direct connections are usually faster than multi-hop
        return avg_latency * 0.8

    def _calculate_risk_score(
        self,
        source: str,
        target: str,
        node_metrics: dict[str, Any],
    ) -> float:
        """
        Calculate risk score for adding a shortcut.

        Higher risk for:
        - Creating new single points of failure
        - Connecting to already overloaded nodes
        - Violating architectural boundaries
        """
        risk = 0.0

        # Risk if target becomes more critical
        target_metrics = node_metrics.get(target)
        if target_metrics:
            # High betweenness after shortcut is risky
            risk += target_metrics.betweenness_centrality * 0.5

            # High load concentration is risky
            if target_metrics.is_bottleneck:
                risk += 0.3

        # Risk if source becomes a hub
        source_metrics = node_metrics.get(source)
        if source_metrics:
            if source_metrics.is_hub:
                risk += 0.2

        # Base risk for any new edge
        risk += 0.1

        return min(risk, 1.0)  # Cap at 1.0

    def _calculate_confidence(
        self,
        delta_obj: float,
        baseline: Any,
        modified: Any,
    ) -> float:
        """
        Calculate confidence in the improvement prediction.

        Higher confidence for:
        - Larger improvements
        - Well-connected graphs
        - Significant path length reduction
        """
        if delta_obj >= 0:
            return 0.0

        improvement = -delta_obj

        # Base confidence from improvement magnitude
        confidence = min(improvement * 2, 0.5)

        # Boost if graph is well-connected
        if baseline.is_connected:
            confidence += 0.2

        # Boost if path length significantly reduced
        path_reduction = baseline.average_path_length - modified.average_path_length
        if path_reduction > 0.1:
            confidence += 0.2

        # Penalize if betweenness increased significantly
        betweenness_increase = modified.max_betweenness - baseline.max_betweenness
        if betweenness_increase > 0.1:
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    def _generate_rationale(
        self,
        source: str,
        target: str,
        delta_path: float,
        delta_betweenness: float,
        delta_weighted: float,
    ) -> str:
        """Generate human-readable rationale for the shortcut."""
        reasons = []

        if delta_path < -0.05:
            reasons.append(
                f"Reduces average path length by {-delta_path:.2f}"
            )

        if delta_betweenness < -0.01:
            reasons.append(
                f"Reduces max betweenness by {-delta_betweenness:.3f}"
            )

        if delta_weighted < -1.0:
            reasons.append(
                f"Reduces weighted path length by {-delta_weighted:.1f}ms"
            )

        if not reasons:
            reasons.append("Minor optimization benefit")

        return f"Shortcut {source} -> {target}: " + "; ".join(reasons)

    def simulate_shortcuts(
        self,
        shortcuts: list[ShortcutCandidate],
    ) -> tuple[Any, dict[str, Any]]:
        """
        Simulate applying multiple shortcuts and return resulting metrics.

        Args:
            shortcuts: List of shortcuts to apply.

        Returns:
            Tuple of (graph_metrics, node_metrics) after applying shortcuts.
        """
        # Create copy of graph
        simulated = self.graph.copy()

        # Apply all shortcuts
        for shortcut in shortcuts:
            simulated.add_edge(
                shortcut.source,
                shortcut.target,
                weight=shortcut.estimated_latency,
                p50_latency=shortcut.estimated_latency,
                p95_latency=shortcut.estimated_latency * 2,
                call_rate=shortcut.estimated_call_rate,
                error_rate=0.0,
                cost=0.0,
                is_shortcut=True,
            )

        # Calculate metrics
        calc = MetricsCalculator(graph=simulated)
        return calc.calculate_all()

    def get_removal_candidates(
        self,
        k: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Find edges that could be removed to simplify topology.

        Identifies redundant edges that don't significantly impact
        graph connectivity or metrics.

        Args:
            k: Number of removal candidates to return.

        Returns:
            List of edge removal suggestions.
        """
        if self.graph.number_of_edges() < 2:
            return []

        baseline_calc = MetricsCalculator(graph=self.graph)
        baseline_metrics, _ = baseline_calc.calculate_all()
        baseline_obj = self._calculate_objective(baseline_metrics)

        removal_candidates = []

        for source, target, data in self.graph.edges(data=True):
            # Create graph without this edge
            test_graph = self.graph.copy()
            test_graph.remove_edge(source, target)

            # Check if graph remains connected
            if not nx.is_weakly_connected(test_graph):
                continue  # Cannot remove - would disconnect graph

            # Calculate new metrics
            test_calc = MetricsCalculator(graph=test_graph)
            test_metrics, _ = test_calc.calculate_all()
            test_obj = self._calculate_objective(test_metrics)

            # Calculate impact
            delta = test_obj - baseline_obj

            # Only suggest removal if minimal impact
            if delta < 0.1:  # Less than 10% increase in objective
                removal_candidates.append({
                    "source": source,
                    "target": target,
                    "impact": delta,
                    "call_rate": data.get("call_rate", 0),
                    "rationale": f"Edge has minimal impact on topology (delta: {delta:.3f})",
                })

        # Sort by impact (lowest first)
        removal_candidates.sort(key=lambda x: x["impact"])
        return removal_candidates[:k]
