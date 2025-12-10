"""
Command Line Interface for Small-World Services.

Provides commands for analyzing service topologies from the command line.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from smallworld import __version__
from smallworld.core.graph_builder import GraphBuilder
from smallworld.core.metrics import MetricsCalculator
from smallworld.core.shortcut_optimizer import PolicyConstraints, ShortcutOptimizer
from smallworld.io.json_loader import JsonLoader, JsonLoaderError

app = typer.Typer(
    name="smallworld",
    help="Microservice topology analyzer using Small-World Network theory.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"Small-World Services v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit."
    ),
) -> None:
    """Small-World Services - Microservice Topology Optimizer."""
    pass


@app.command()
def analyze(
    input_file: Path = typer.Argument(
        ...,
        help="JSON file containing service topology.",
        exists=True,
        readable=True,
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output file for results (JSON). Prints to stdout if not specified.",
    ),
    goal: str = typer.Option(
        "balanced",
        "--goal", "-g",
        help="Optimization goal: latency, paths, load, or balanced.",
    ),
    shortcuts: int = typer.Option(
        5,
        "--shortcuts", "-k",
        help="Number of shortcut suggestions to generate.",
        min=1,
        max=100,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed output.",
    ),
) -> None:
    """
    Analyze a service topology and suggest optimizations.

    Reads service definitions and dependencies from a JSON file,
    calculates network metrics, and suggests shortcut edges to
    optimize the topology.
    """
    try:
        # Load topology
        with console.status("[bold green]Loading topology..."):
            topology = JsonLoader.load_from_file(input_file)

        if verbose:
            console.print(f"[green]Loaded {len(topology.services)} services, {len(topology.edges)} edges[/green]")

        # Build graph
        with console.status("[bold green]Building graph..."):
            builder = GraphBuilder()
            graph = builder.build_from_topology(topology)

        # Calculate metrics
        with console.status("[bold green]Calculating metrics..."):
            calc = MetricsCalculator(graph=graph)
            graph_metrics, node_metrics = calc.calculate_all()

        # Find shortcuts
        with console.status("[bold green]Finding shortcuts..."):
            optimizer = ShortcutOptimizer(graph=graph)
            optimizer.set_goal(goal)
            shortcut_list = optimizer.find_shortcuts(k=shortcuts)

        # Build result
        result = build_result(graph_metrics, node_metrics, shortcut_list, goal)

        # Output
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            console.print(f"[green]Results written to {output_file}[/green]")
        else:
            # Pretty print to console
            print_results(graph_metrics, node_metrics, shortcut_list, verbose)

    except JsonLoaderError as e:
        console.print(f"[red]Error loading file: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def metrics(
    input_file: Path = typer.Argument(
        ...,
        help="JSON file containing service topology.",
        exists=True,
        readable=True,
    ),
    node: Optional[str] = typer.Option(
        None,
        "--node", "-n",
        help="Show metrics for a specific node only.",
    ),
) -> None:
    """
    Calculate and display metrics for a service topology.

    Shows network metrics including centrality measures, clustering,
    and load distribution.
    """
    try:
        topology = JsonLoader.load_from_file(input_file)
        builder = GraphBuilder()
        graph = builder.build_from_topology(topology)

        calc = MetricsCalculator(graph=graph)
        graph_metrics, node_metrics = calc.calculate_all()

        if node:
            if node not in node_metrics:
                console.print(f"[red]Node '{node}' not found[/red]")
                raise typer.Exit(code=1)
            print_node_metrics(node_metrics[node])
        else:
            print_graph_metrics(graph_metrics)
            print_top_nodes(node_metrics)

    except JsonLoaderError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def serve(
    host: str = typer.Option(
        "0.0.0.0",
        "--host", "-h",
        help="Host to bind to.",
    ),
    port: int = typer.Option(
        8000,
        "--port", "-p",
        help="Port to bind to.",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Enable auto-reload for development.",
    ),
) -> None:
    """
    Start the REST API server.

    Runs a FastAPI server that provides endpoints for topology analysis.
    """
    try:
        import uvicorn
        console.print(f"[green]Starting server at http://{host}:{port}[/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        uvicorn.run(
            "smallworld.api.app:app",
            host=host,
            port=port,
            reload=reload,
        )
    except ImportError:
        console.print("[red]uvicorn not installed. Install with: pip install uvicorn[/red]")
        raise typer.Exit(code=1)


@app.command()
def validate(
    input_file: Path = typer.Argument(
        ...,
        help="JSON file to validate.",
        exists=True,
        readable=True,
    ),
) -> None:
    """
    Validate a topology JSON file.

    Checks if the file is valid JSON and conforms to the expected schema.
    """
    try:
        topology = JsonLoader.load_from_file(input_file)
        console.print("[green]Valid topology file![/green]")
        console.print(f"  Services: {len(topology.services)}")
        console.print(f"  Edges: {len(topology.edges)}")

        # Check for issues
        service_names = {s.name for s in topology.services}
        edge_services = set()
        for e in topology.edges:
            edge_services.add(e.source)
            edge_services.add(e.target)

        missing = edge_services - service_names
        if missing:
            console.print(f"[yellow]Warning: Edges reference undefined services: {missing}[/yellow]")

    except JsonLoaderError as e:
        console.print(f"[red]Invalid: {e}[/red]")
        raise typer.Exit(code=1)


def build_result(
    graph_metrics: any,
    node_metrics: dict,
    shortcuts: list,
    goal: str,
) -> dict:
    """Build result dictionary for JSON output."""
    return {
        "metrics": graph_metrics.to_dict(),
        "node_metrics": {
            name: nm.to_dict() for name, nm in node_metrics.items()
        },
        "shortcuts": [s.to_dict() for s in shortcuts],
        "options": {"goal": goal},
    }


def print_results(
    graph_metrics: any,
    node_metrics: dict,
    shortcuts: list,
    verbose: bool,
) -> None:
    """Print analysis results to console."""
    # Graph summary panel
    summary = Table.grid(padding=(0, 2))
    summary.add_row("Nodes:", str(graph_metrics.node_count))
    summary.add_row("Edges:", str(graph_metrics.edge_count))
    summary.add_row("Density:", f"{graph_metrics.density:.4f}")
    summary.add_row("Avg Path Length:", f"{graph_metrics.average_path_length:.2f}")
    summary.add_row("Clustering:", f"{graph_metrics.average_clustering:.4f}")
    summary.add_row("Small-World Coef:", f"{graph_metrics.small_world_coefficient:.2f}")
    summary.add_row("Connected:", "Yes" if graph_metrics.is_connected else "No")

    console.print(Panel(summary, title="Graph Metrics", border_style="blue"))

    # Shortcuts table
    if shortcuts:
        table = Table(title="Suggested Shortcuts")
        table.add_column("From", style="cyan")
        table.add_column("To", style="cyan")
        table.add_column("Improvement", justify="right", style="green")
        table.add_column("Confidence", justify="right")
        table.add_column("Risk", justify="right", style="yellow")

        for s in shortcuts:
            table.add_row(
                s.source,
                s.target,
                f"{-s.delta_objective:.4f}",
                f"{s.confidence:.2f}",
                f"{s.risk_score:.2f}",
            )

        console.print(table)
    else:
        console.print("[yellow]No beneficial shortcuts found.[/yellow]")

    if verbose:
        print_top_nodes(node_metrics)


def print_graph_metrics(metrics: any) -> None:
    """Print graph-level metrics."""
    table = Table(title="Graph Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    for key, value in metrics.to_dict().items():
        if isinstance(value, float):
            table.add_row(key, f"{value:.4f}")
        else:
            table.add_row(key, str(value))

    console.print(table)


def print_node_metrics(nm: any) -> None:
    """Print metrics for a single node."""
    table = Table(title=f"Node Metrics: {nm.name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    for key, value in nm.to_dict().items():
        if key == "name":
            continue
        if isinstance(value, float):
            table.add_row(key, f"{value:.4f}")
        else:
            table.add_row(key, str(value))

    console.print(table)


def print_top_nodes(node_metrics: dict) -> None:
    """Print top nodes by various metrics."""
    if not node_metrics:
        return

    # Top by betweenness
    by_betweenness = sorted(
        node_metrics.values(),
        key=lambda x: x.betweenness_centrality,
        reverse=True,
    )[:5]

    table = Table(title="Top Nodes by Betweenness Centrality")
    table.add_column("Node", style="cyan")
    table.add_column("Betweenness", justify="right")
    table.add_column("Hub", justify="center")
    table.add_column("Bottleneck", justify="center")

    for nm in by_betweenness:
        table.add_row(
            nm.name,
            f"{nm.betweenness_centrality:.4f}",
            "[green]Yes[/green]" if nm.is_hub else "No",
            "[yellow]Yes[/yellow]" if nm.is_bottleneck else "No",
        )

    console.print(table)


if __name__ == "__main__":
    app()
