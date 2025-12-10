"""
Tests for the ShortcutOptimizer module.

Achieves 100% coverage for shortcut_optimizer.py
"""

from __future__ import annotations

import pytest
import networkx as nx

from smallworld.core.graph_builder import GraphBuilder
from smallworld.core.shortcut_optimizer import (
    OptimizationGoal,
    PolicyConstraints,
    ShortcutCandidate,
    ShortcutOptimizer,
)
from smallworld.io.schemas import EdgeData, ServiceData, ServiceTopology


class TestOptimizationGoal:
    """Tests for OptimizationGoal enum."""

    def test_enum_values(self) -> None:
        """Test enum values."""
        assert OptimizationGoal.LATENCY.value == "latency"
        assert OptimizationGoal.PATHS.value == "paths"
        assert OptimizationGoal.LOAD.value == "load"
        assert OptimizationGoal.BALANCED.value == "balanced"


class TestShortcutCandidate:
    """Tests for ShortcutCandidate dataclass."""

    def test_to_dict(self) -> None:
        """Test ShortcutCandidate to_dict conversion."""
        candidate = ShortcutCandidate(
            source="a",
            target="b",
            delta_objective=-0.5,
            delta_path_length=-0.3,
            delta_max_betweenness=-0.1,
            delta_weighted_path_length=-5.0,
            risk_score=0.2,
            confidence=0.8,
            score=2.5,
            rationale="Test rationale",
            estimated_latency=10.0,
        )

        result = candidate.to_dict()

        assert result["from"] == "a"
        assert result["to"] == "b"
        assert result["improvement"] == 0.5  # Negated delta
        assert result["rationale"] == "Test rationale"


class TestPolicyConstraints:
    """Tests for PolicyConstraints dataclass."""

    def test_default_values(self) -> None:
        """Test default policy values."""
        policy = PolicyConstraints()

        assert policy.forbidden_pairs == []
        assert policy.allowed_zones == {}
        assert policy.max_new_edges_per_service == 3
        assert policy.require_same_zone is False
        assert policy.min_path_length_to_shortcut == 2

    def test_from_dict(self) -> None:
        """Test creating policy from dictionary."""
        data = {
            "forbidden_pairs": [["a", "b"], ["c", "d"]],
            "allowed_zones": {"us-east": ["us-west"]},
            "max_new_edges_per_service": 5,
            "require_same_zone": True,
            "min_path_length_to_shortcut": 3,
        }

        policy = PolicyConstraints.from_dict(data)

        assert ("a", "b") in policy.forbidden_pairs
        assert policy.max_new_edges_per_service == 5
        assert policy.require_same_zone is True

    def test_from_dict_empty(self) -> None:
        """Test creating policy from empty dictionary."""
        policy = PolicyConstraints.from_dict({})

        assert policy.forbidden_pairs == []
        assert policy.max_new_edges_per_service == 3


class TestShortcutOptimizer:
    """Tests for ShortcutOptimizer class."""

    def test_init(self) -> None:
        """Test optimizer initialization."""
        optimizer = ShortcutOptimizer()

        assert isinstance(optimizer.graph, nx.DiGraph)
        assert optimizer.goal == OptimizationGoal.BALANCED
        assert optimizer.alpha == 1.0
        assert optimizer.beta == 1.0

    def test_set_graph(self, complex_graph: nx.DiGraph) -> None:
        """Test setting graph."""
        optimizer = ShortcutOptimizer()
        optimizer.set_graph(complex_graph)

        assert optimizer.graph is complex_graph

    def test_set_goal_string(self) -> None:
        """Test setting goal from string."""
        optimizer = ShortcutOptimizer()
        optimizer.set_goal("latency")

        assert optimizer.goal == OptimizationGoal.LATENCY
        assert optimizer.alpha == 2.0  # Latency goal increases alpha

    def test_set_goal_enum(self) -> None:
        """Test setting goal from enum."""
        optimizer = ShortcutOptimizer()
        optimizer.set_goal(OptimizationGoal.LOAD)

        assert optimizer.goal == OptimizationGoal.LOAD
        assert optimizer.beta == 2.0  # Load goal increases beta

    def test_set_goal_paths(self) -> None:
        """Test setting paths goal."""
        optimizer = ShortcutOptimizer()
        optimizer.set_goal("paths")

        assert optimizer.goal == OptimizationGoal.PATHS
        assert optimizer.alpha == 2.0
        assert optimizer.gamma == 0.0

    def test_set_goal_balanced(self) -> None:
        """Test setting balanced goal."""
        optimizer = ShortcutOptimizer()
        optimizer.set_goal("balanced")

        assert optimizer.goal == OptimizationGoal.BALANCED
        assert optimizer.alpha == 1.0
        assert optimizer.beta == 1.0

    def test_find_shortcuts_chain(self, chain_graph: nx.DiGraph) -> None:
        """Test finding shortcuts for chain topology."""
        optimizer = ShortcutOptimizer(graph=chain_graph)
        shortcuts = optimizer.find_shortcuts(k=3)

        # Chain topology should benefit from shortcuts
        assert len(shortcuts) <= 3
        # Each shortcut should have positive score
        for s in shortcuts:
            assert s.score > 0

    def test_find_shortcuts_with_policy(self, chain_graph: nx.DiGraph) -> None:
        """Test finding shortcuts with policy constraints."""
        optimizer = ShortcutOptimizer(graph=chain_graph)
        policy = PolicyConstraints(
            forbidden_pairs=[("service_0", "service_5")],
        )

        shortcuts = optimizer.find_shortcuts(k=5, policy=policy)

        # Forbidden pair should not appear
        for s in shortcuts:
            assert not (s.source == "service_0" and s.target == "service_5")

    def test_find_shortcuts_empty_graph(self) -> None:
        """Test finding shortcuts for empty graph."""
        optimizer = ShortcutOptimizer()
        shortcuts = optimizer.find_shortcuts(k=3)

        assert shortcuts == []

    def test_find_shortcuts_single_node(self) -> None:
        """Test finding shortcuts for single node graph."""
        builder = GraphBuilder()
        topology = ServiceTopology(
            services=[ServiceData(name="single")],
            edges=[],
        )
        graph = builder.build_from_topology(topology)

        optimizer = ShortcutOptimizer(graph=graph)
        shortcuts = optimizer.find_shortcuts(k=3)

        assert shortcuts == []

    def test_find_shortcuts_fully_connected(self) -> None:
        """Test finding shortcuts for fully connected graph."""
        # Create fully connected 3-node graph
        builder = GraphBuilder()
        topology = ServiceTopology(
            services=[
                ServiceData(name="a"),
                ServiceData(name="b"),
                ServiceData(name="c"),
            ],
            edges=[
                EdgeData(source="a", target="b", call_rate=10.0),
                EdgeData(source="a", target="c", call_rate=10.0),
                EdgeData(source="b", target="a", call_rate=10.0),
                EdgeData(source="b", target="c", call_rate=10.0),
                EdgeData(source="c", target="a", call_rate=10.0),
                EdgeData(source="c", target="b", call_rate=10.0),
            ],
        )
        graph = builder.build_from_topology(topology)

        optimizer = ShortcutOptimizer(graph=graph)
        shortcuts = optimizer.find_shortcuts(k=3)

        # Fully connected graph has no room for shortcuts
        assert shortcuts == []

    def test_zone_constraint(self) -> None:
        """Test zone-based constraint."""
        builder = GraphBuilder()
        topology = ServiceTopology(
            services=[
                ServiceData(name="a", zone="us-east"),
                ServiceData(name="b", zone="us-east"),
                ServiceData(name="c", zone="us-west"),
                ServiceData(name="d", zone="us-west"),
            ],
            edges=[
                EdgeData(source="a", target="b", call_rate=10.0),
                EdgeData(source="b", target="c", call_rate=10.0),
                EdgeData(source="c", target="d", call_rate=10.0),
            ],
        )
        graph = builder.build_from_topology(topology)

        optimizer = ShortcutOptimizer(graph=graph)
        policy = PolicyConstraints(require_same_zone=True)
        shortcuts = optimizer.find_shortcuts(k=5, policy=policy)

        # All shortcuts should be within same zone
        for s in shortcuts:
            source_zone = graph.nodes[s.source].get("zone")
            target_zone = graph.nodes[s.target].get("zone")
            # If both have zones, they should match
            if source_zone and target_zone:
                assert source_zone == target_zone

    def test_allowed_zones_constraint(self) -> None:
        """Test allowed zones constraint."""
        builder = GraphBuilder()
        topology = ServiceTopology(
            services=[
                ServiceData(name="a", zone="zone1"),
                ServiceData(name="b", zone="zone2"),
                ServiceData(name="c", zone="zone3"),
            ],
            edges=[
                EdgeData(source="a", target="b", call_rate=10.0),
                EdgeData(source="b", target="c", call_rate=10.0),
            ],
        )
        graph = builder.build_from_topology(topology)

        optimizer = ShortcutOptimizer(graph=graph)
        policy = PolicyConstraints(
            allowed_zones={"zone1": ["zone2"]},  # zone1 can only connect to zone2
        )
        shortcuts = optimizer.find_shortcuts(k=5, policy=policy)

        # Shortcuts from zone1 should only go to zone2
        for s in shortcuts:
            source_zone = graph.nodes[s.source].get("zone")
            if source_zone == "zone1":
                target_zone = graph.nodes[s.target].get("zone")
                assert target_zone in ["zone2", None]

    def test_max_edges_per_service(self, chain_graph: nx.DiGraph) -> None:
        """Test max edges per service constraint limits candidates."""
        optimizer = ShortcutOptimizer(graph=chain_graph)

        # With very restrictive limit, fewer candidates generated
        policy_strict = PolicyConstraints(max_new_edges_per_service=1)
        shortcuts_strict = optimizer.find_shortcuts(k=10, policy=policy_strict)

        # With more generous limit, more candidates possible
        policy_generous = PolicyConstraints(max_new_edges_per_service=10)
        shortcuts_generous = optimizer.find_shortcuts(k=10, policy=policy_generous)

        # Strict policy should produce fewer or equal shortcuts
        assert len(shortcuts_strict) <= len(shortcuts_generous)

    def test_min_path_length_constraint(self) -> None:
        """Test minimum path length constraint."""
        builder = GraphBuilder()
        topology = ServiceTopology(
            services=[
                ServiceData(name="a"),
                ServiceData(name="b"),
                ServiceData(name="c"),
            ],
            edges=[
                EdgeData(source="a", target="b", call_rate=10.0),
                EdgeData(source="b", target="c", call_rate=10.0),
            ],
        )
        graph = builder.build_from_topology(topology)

        optimizer = ShortcutOptimizer(graph=graph)
        policy = PolicyConstraints(min_path_length_to_shortcut=3)  # Require path >= 3

        shortcuts = optimizer.find_shortcuts(k=5, policy=policy)

        # a -> c has path length 2, should be excluded with min 3
        for s in shortcuts:
            if s.source == "a" and s.target == "c":
                pytest.fail("Shortcut a->c should be excluded (path length 2 < 3)")

    def test_simulate_shortcuts(self, chain_graph: nx.DiGraph) -> None:
        """Test simulating multiple shortcuts."""
        optimizer = ShortcutOptimizer(graph=chain_graph)
        shortcuts = optimizer.find_shortcuts(k=2)

        if shortcuts:
            graph_metrics, node_metrics = optimizer.simulate_shortcuts(shortcuts)

            assert graph_metrics.node_count == 6
            # Simulated graph should have more edges
            assert graph_metrics.edge_count >= 5 + len(shortcuts)

    def test_simulate_shortcuts_empty(self, chain_graph: nx.DiGraph) -> None:
        """Test simulating empty shortcuts list."""
        optimizer = ShortcutOptimizer(graph=chain_graph)
        graph_metrics, node_metrics = optimizer.simulate_shortcuts([])

        assert graph_metrics.node_count == 6
        assert graph_metrics.edge_count == 5

    def test_get_removal_candidates(self, complex_graph: nx.DiGraph) -> None:
        """Test getting edge removal candidates."""
        optimizer = ShortcutOptimizer(graph=complex_graph)
        removals = optimizer.get_removal_candidates(k=3)

        # Should return list of removal suggestions
        assert isinstance(removals, list)
        for r in removals:
            assert "source" in r
            assert "target" in r
            assert "impact" in r

    def test_get_removal_candidates_empty_graph(self) -> None:
        """Test removal candidates for empty graph."""
        optimizer = ShortcutOptimizer()
        removals = optimizer.get_removal_candidates(k=3)

        assert removals == []

    def test_get_removal_candidates_single_edge(self) -> None:
        """Test removal candidates for graph with single edge."""
        builder = GraphBuilder()
        topology = ServiceTopology(
            services=[ServiceData(name="a"), ServiceData(name="b")],
            edges=[EdgeData(source="a", target="b", call_rate=10.0)],
        )
        graph = builder.build_from_topology(topology)

        optimizer = ShortcutOptimizer(graph=graph)
        removals = optimizer.get_removal_candidates(k=3)

        # Single edge graph can't have edges removed without disconnection
        assert removals == []

    def test_shortcut_rationale_generation(self, chain_graph: nx.DiGraph) -> None:
        """Test that shortcuts have meaningful rationales."""
        optimizer = ShortcutOptimizer(graph=chain_graph)
        shortcuts = optimizer.find_shortcuts(k=3)

        for s in shortcuts:
            assert len(s.rationale) > 0
            assert "Shortcut" in s.rationale

    def test_estimated_latency(self, chain_graph: nx.DiGraph) -> None:
        """Test that estimated latency is calculated."""
        optimizer = ShortcutOptimizer(graph=chain_graph)
        shortcuts = optimizer.find_shortcuts(k=3)

        for s in shortcuts:
            assert s.estimated_latency > 0

    def test_confidence_score(self, chain_graph: nx.DiGraph) -> None:
        """Test confidence score calculation."""
        optimizer = ShortcutOptimizer(graph=chain_graph)
        shortcuts = optimizer.find_shortcuts(k=3)

        for s in shortcuts:
            assert 0 <= s.confidence <= 1

    def test_risk_score(self, chain_graph: nx.DiGraph) -> None:
        """Test risk score calculation."""
        optimizer = ShortcutOptimizer(graph=chain_graph)
        shortcuts = optimizer.find_shortcuts(k=3)

        for s in shortcuts:
            assert 0 <= s.risk_score <= 1

    def test_no_improvement_candidate_filtered(self) -> None:
        """Test that candidates with no improvement are filtered."""
        # Create graph where shortcuts don't help
        builder = GraphBuilder()
        topology = ServiceTopology(
            services=[
                ServiceData(name="a"),
                ServiceData(name="b"),
            ],
            edges=[
                EdgeData(source="a", target="b", call_rate=10.0),
            ],
        )
        graph = builder.build_from_topology(topology)

        optimizer = ShortcutOptimizer(graph=graph)
        shortcuts = optimizer.find_shortcuts(k=5)

        # No beneficial shortcuts possible in 2-node graph
        assert len(shortcuts) == 0

    def test_disconnected_graph_shortcuts(
        self, disconnected_topology: ServiceTopology
    ) -> None:
        """Test shortcuts for disconnected graph."""
        builder = GraphBuilder()
        graph = builder.build_from_topology(disconnected_topology)

        optimizer = ShortcutOptimizer(graph=graph)
        shortcuts = optimizer.find_shortcuts(k=5)

        # May find shortcuts to connect components
        assert isinstance(shortcuts, list)


class TestShortcutOptimizerEdgeCases:
    """Edge case tests for ShortcutOptimizer."""

    def test_graph_with_no_latency_data(self) -> None:
        """Test graph where edges have no latency."""
        builder = GraphBuilder()
        topology = ServiceTopology(
            services=[
                ServiceData(name="a"),
                ServiceData(name="b"),
                ServiceData(name="c"),
            ],
            edges=[
                EdgeData(source="a", target="b"),
                EdgeData(source="b", target="c"),
            ],
        )
        graph = builder.build_from_topology(topology)

        optimizer = ShortcutOptimizer(graph=graph)
        shortcuts = optimizer.find_shortcuts(k=3)

        # Should still work with default weights
        assert isinstance(shortcuts, list)

    def test_very_large_k(self, chain_graph: nx.DiGraph) -> None:
        """Test requesting more shortcuts than possible."""
        optimizer = ShortcutOptimizer(graph=chain_graph)
        shortcuts = optimizer.find_shortcuts(k=100)

        # Should return all beneficial shortcuts, not crash
        assert len(shortcuts) <= 100
