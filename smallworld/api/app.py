"""
FastAPI Application Module

Provides REST API endpoints for graph analysis and optimization.
Includes WebSocket support for real-time updates and gamification features.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from smallworld import __version__
from smallworld.core.graph_builder import GraphBuilder
from smallworld.core.metrics import MetricsCalculator
from smallworld.core.shortcut_optimizer import PolicyConstraints, ShortcutOptimizer
from smallworld.io.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ErrorResponse,
    GraphMetricsResponse,
    GraphSummary,
    HealthResponse,
    NodeMetricsResponse,
    ShortcutSuggestion,
)


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


# Gamification models
class UserScore(BaseModel):
    user_id: str
    username: str
    score: int = 0
    optimizations: int = 0
    streak: int = 0
    achievements: list[str] = []
    last_active: str = ""


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: str
    score: int
    optimizations: int
    streak: int


class Achievement(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    rarity: str
    points: int


class SimulationResult(BaseModel):
    id: str
    user_id: str
    original_path_length: float
    optimized_path_length: float
    improvement_percent: float
    shortcuts_applied: int
    timestamp: str
    points_earned: int


# In-memory stores (in production, use a database)
user_scores: dict[str, UserScore] = {}
simulation_history: list[SimulationResult] = []
achievements_definitions: list[Achievement] = [
    Achievement(
        id="first_optimization",
        name="First Steps",
        description="Complete your first topology optimization",
        icon="target",
        rarity="common",
        points=10,
    ),
    Achievement(
        id="streak_7",
        name="On Fire",
        description="Maintain a 7-day optimization streak",
        icon="flame",
        rarity="rare",
        points=50,
    ),
    Achievement(
        id="top_10",
        name="Rising Star",
        description="Reach the top 10 on the leaderboard",
        icon="star",
        rarity="epic",
        points=100,
    ),
    Achievement(
        id="hundred_optimizations",
        name="Century Club",
        description="Complete 100 topology optimizations",
        icon="award",
        rarity="legendary",
        points=500,
    ),
    Achievement(
        id="perfect_score",
        name="Perfectionist",
        description="Achieve 50%+ improvement in a single optimization",
        icon="gem",
        rarity="legendary",
        points=200,
    ),
]

# Global connection manager
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup
    app.state.start_time = time.time()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Small-World Services API",
        description=(
            "Microservice topology analyzer using Small-World Network theory. "
            "Analyzes service dependency graphs, computes network metrics, "
            "and suggests optimal shortcut edges for topology optimization."
        ),
        version=__version__,
        lifespan=lifespan,
        responses={
            400: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
        },
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register all API routes."""

    @app.get("/", response_model=dict[str, str])
    async def root() -> dict[str, str]:
        """Root endpoint with basic info."""
        return {
            "name": "Small-World Services API",
            "version": __version__,
            "docs": "/docs",
        }

    @app.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        uptime = time.time() - app.state.start_time if hasattr(app.state, "start_time") else 0
        return HealthResponse(
            status="healthy",
            version=__version__,
            details={"uptime_seconds": round(uptime, 2)},
        )

    @app.post(
        "/analyze",
        response_model=AnalyzeResponse,
        summary="Analyze service topology",
        description="Analyzes the service dependency graph and suggests optimal shortcuts.",
    )
    async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
        """
        Analyze service topology and generate optimization suggestions.

        - Builds graph from service definitions
        - Calculates network metrics
        - Identifies hubs and bottlenecks
        - Suggests shortcut edges to optimize topology
        """
        try:
            start_time = time.time()

            # Build graph
            builder = GraphBuilder()
            topology_dict = {
                "services": [s.model_dump() for s in request.services],
                "edges": [e.model_dump(by_alias=True) for e in request.edges],
            }
            graph = builder.build_from_dict(topology_dict)

            # Calculate metrics
            metrics_calc = MetricsCalculator(graph=graph)
            graph_metrics, node_metrics = metrics_calc.calculate_all()

            # Run optimizer
            optimizer = ShortcutOptimizer(graph=graph)
            optimizer.set_goal(request.options.goal)
            optimizer.alpha = request.options.alpha
            optimizer.beta = request.options.beta
            optimizer.gamma = request.options.gamma

            # Parse policy if provided
            policy = None
            if request.policy:
                policy = PolicyConstraints(
                    forbidden_pairs=[
                        tuple(p) for p in request.policy.forbidden_pairs
                    ],
                    allowed_zones=request.policy.allowed_zones,
                    max_new_edges_per_service=request.policy.max_new_edges_per_service,
                    require_same_zone=request.policy.require_same_zone,
                    min_path_length_to_shortcut=request.policy.min_path_length_to_shortcut,
                )

            shortcuts = optimizer.find_shortcuts(k=request.options.k, policy=policy)

            # Build response
            node_metrics_list = [
                NodeMetricsResponse(**nm.to_dict())
                for nm in node_metrics.values()
            ]

            shortcuts_list = [
                ShortcutSuggestion(
                    **{
                        "from": s.source,
                        "to": s.target,
                        "improvement": round(-s.delta_objective, 4),
                        "delta_path_length": round(s.delta_path_length, 4),
                        "delta_max_betweenness": round(s.delta_max_betweenness, 4),
                        "risk_score": round(s.risk_score, 4),
                        "confidence": round(s.confidence, 4),
                        "score": round(s.score, 4),
                        "rationale": s.rationale,
                        "estimated_latency": round(s.estimated_latency, 2),
                    }
                )
                for s in shortcuts
            ]

            # Build summary
            hub_services = [nm.name for nm in node_metrics.values() if nm.is_hub]
            bottleneck_services = [nm.name for nm in node_metrics.values() if nm.is_bottleneck]

            # Find most connected and highest load
            most_connected = max(
                node_metrics.values(),
                key=lambda nm: nm.total_degree,
                default=None
            )
            highest_load = max(
                node_metrics.values(),
                key=lambda nm: nm.incoming_load + nm.outgoing_load,
                default=None
            )

            recommendations = generate_recommendations(
                graph_metrics, node_metrics, shortcuts
            )

            graph_summary = GraphSummary(
                total_services=graph_metrics.node_count,
                total_dependencies=graph_metrics.edge_count,
                hub_services=hub_services,
                bottleneck_services=bottleneck_services,
                most_connected_service=most_connected.name if most_connected else None,
                highest_load_service=highest_load.name if highest_load else None,
                is_small_world=graph_metrics.small_world_coefficient > 1.0,
                recommendations=recommendations,
            )

            processing_time = time.time() - start_time

            return AnalyzeResponse(
                metrics=GraphMetricsResponse(**graph_metrics.to_dict()),
                node_metrics=node_metrics_list,
                shortcuts=shortcuts_list,
                graph_summary=graph_summary,
                analysis_metadata={
                    "processing_time_ms": round(processing_time * 1000, 2),
                    "optimization_goal": request.options.goal,
                },
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis failed: {str(e)}",
            )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Any, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "code": f"HTTP_{exc.status_code}",
            },
        )

    # WebSocket endpoint for real-time updates
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time updates."""
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Echo back with acknowledgment
                await websocket.send_json({"type": "ack", "data": data})
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    # Gamification endpoints
    @app.get("/leaderboard", response_model=list[LeaderboardEntry])
    async def get_leaderboard(limit: int = 10) -> list[LeaderboardEntry]:
        """Get the top users on the leaderboard."""
        sorted_users = sorted(
            user_scores.values(),
            key=lambda x: x.score,
            reverse=True,
        )[:limit]
        return [
            LeaderboardEntry(
                rank=i + 1,
                user_id=user.user_id,
                username=user.username,
                score=user.score,
                optimizations=user.optimizations,
                streak=user.streak,
            )
            for i, user in enumerate(sorted_users)
        ]

    @app.get("/users/{user_id}/score", response_model=UserScore)
    async def get_user_score(user_id: str) -> UserScore:
        """Get a user's score and achievements."""
        if user_id not in user_scores:
            # Create new user
            user_scores[user_id] = UserScore(
                user_id=user_id,
                username=f"user_{user_id[:8]}",
                last_active=datetime.now(timezone.utc).isoformat(),
            )
        return user_scores[user_id]

    @app.post("/users/{user_id}/score", response_model=UserScore)
    async def update_user_score(
        user_id: str,
        points: int,
        optimization_completed: bool = False,
    ) -> UserScore:
        """Update a user's score."""
        if user_id not in user_scores:
            user_scores[user_id] = UserScore(
                user_id=user_id,
                username=f"user_{user_id[:8]}",
                last_active=datetime.now(timezone.utc).isoformat(),
            )

        user = user_scores[user_id]
        user.score += points
        if optimization_completed:
            user.optimizations += 1

        user.last_active = datetime.now(timezone.utc).isoformat()

        # Check for achievements
        new_achievements: list[str] = []
        if user.optimizations == 1 and "first_optimization" not in user.achievements:
            user.achievements.append("first_optimization")
            new_achievements.append("first_optimization")
            user.score += 10

        if user.optimizations >= 100 and "hundred_optimizations" not in user.achievements:
            user.achievements.append("hundred_optimizations")
            new_achievements.append("hundred_optimizations")
            user.score += 500

        # Broadcast update if there are new achievements
        if new_achievements:
            await manager.broadcast({
                "type": "achievement_unlocked",
                "user_id": user_id,
                "achievements": new_achievements,
            })

        return user

    @app.get("/achievements", response_model=list[Achievement])
    async def get_achievements() -> list[Achievement]:
        """Get all available achievements."""
        return achievements_definitions

    @app.post("/simulations", response_model=SimulationResult)
    async def record_simulation(
        user_id: str,
        original_path_length: float,
        optimized_path_length: float,
        shortcuts_applied: int,
    ) -> SimulationResult:
        """Record a simulation result and award points."""
        improvement = (
            (original_path_length - optimized_path_length) / original_path_length * 100
            if original_path_length > 0
            else 0
        )

        # Calculate points (10 points per 1% improvement)
        points = int(improvement * 10)

        result = SimulationResult(
            id=str(uuid.uuid4()),
            user_id=user_id,
            original_path_length=round(original_path_length, 4),
            optimized_path_length=round(optimized_path_length, 4),
            improvement_percent=round(improvement, 2),
            shortcuts_applied=shortcuts_applied,
            timestamp=datetime.now(timezone.utc).isoformat(),
            points_earned=points,
        )

        simulation_history.append(result)

        # Update user score
        await update_user_score(user_id, points, optimization_completed=True)

        # Check for perfect score achievement
        if improvement >= 50:
            if user_id in user_scores:
                user = user_scores[user_id]
                if "perfect_score" not in user.achievements:
                    user.achievements.append("perfect_score")
                    user.score += 200
                    await manager.broadcast({
                        "type": "achievement_unlocked",
                        "user_id": user_id,
                        "achievements": ["perfect_score"],
                    })

        # Broadcast simulation result
        await manager.broadcast({
            "type": "simulation_completed",
            "result": result.model_dump(),
        })

        return result

    @app.get("/simulations", response_model=list[SimulationResult])
    async def get_simulation_history(
        user_id: str | None = None,
        limit: int = 50,
    ) -> list[SimulationResult]:
        """Get simulation history, optionally filtered by user."""
        results = simulation_history
        if user_id:
            results = [r for r in results if r.user_id == user_id]
        return sorted(results, key=lambda x: x.timestamp, reverse=True)[:limit]

    # Export endpoint
    @app.get("/export/{format}")
    async def export_analysis(
        format: str,
        user_id: str | None = None,
    ) -> JSONResponse:
        """Export analysis data in various formats."""
        if format not in ["json", "csv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported format. Use 'json' or 'csv'.",
            )

        results = simulation_history
        if user_id:
            results = [r for r in results if r.user_id == user_id]

        if format == "json":
            return JSONResponse(
                content={
                    "export_date": datetime.now(timezone.utc).isoformat(),
                    "total_simulations": len(results),
                    "simulations": [r.model_dump() for r in results],
                }
            )
        else:
            # CSV format
            csv_lines = [
                "id,user_id,original_path_length,optimized_path_length,improvement_percent,shortcuts_applied,timestamp,points_earned"
            ]
            for r in results:
                csv_lines.append(
                    f"{r.id},{r.user_id},{r.original_path_length},{r.optimized_path_length},{r.improvement_percent},{r.shortcuts_applied},{r.timestamp},{r.points_earned}"
                )
            return JSONResponse(
                content={"csv": "\n".join(csv_lines)},
                media_type="text/csv",
            )


def generate_recommendations(
    graph_metrics: Any,
    node_metrics: dict[str, Any],
    shortcuts: list[Any],
) -> list[str]:
    """Generate human-readable recommendations."""
    recommendations = []

    # Small-world analysis
    if graph_metrics.small_world_coefficient < 0.5:
        recommendations.append(
            "Graph has poor small-world properties. Consider adding shortcuts to reduce path lengths."
        )
    elif graph_metrics.small_world_coefficient > 1.5:
        recommendations.append(
            "Graph shows strong small-world properties. Topology is well-optimized."
        )

    # Connectivity
    if not graph_metrics.is_connected:
        recommendations.append(
            f"Warning: Graph has {graph_metrics.weakly_connected_components} disconnected components."
        )

    # High betweenness
    if graph_metrics.max_betweenness > 0.5:
        bottlenecks = [nm.name for nm in node_metrics.values() if nm.is_bottleneck]
        if bottlenecks:
            recommendations.append(
                f"High betweenness centrality detected. Services at risk of overload: {', '.join(bottlenecks[:3])}"
            )

    # Path length
    if graph_metrics.average_path_length > 4:
        recommendations.append(
            "High average path length detected. Multi-hop calls may cause latency issues."
        )

    # Shortcut suggestions
    if shortcuts:
        recommendations.append(
            f"Found {len(shortcuts)} beneficial shortcut(s) that could improve topology."
        )
    else:
        recommendations.append(
            "No beneficial shortcuts identified. Current topology may be near-optimal."
        )

    return recommendations


# Create default app instance
app = create_app()
