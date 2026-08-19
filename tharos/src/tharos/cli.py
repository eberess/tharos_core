"""Point d'entree CLI de Tharos Core."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from tharos.graph.builder import DependencyGraphBuilder
from tharos.parsers.windev import WinDevParser

app = typer.Typer(name="tharos", help="Tharos Core — Moteur de Migration WinDev")
parse_app = typer.Typer(help="Outils de parsing de fichiers legacy")
graph_app = typer.Typer(help="Analyse des dependances")
app.add_typer(parse_app, name="parse")
app.add_typer(graph_app, name="graph")

console = Console()


@parse_app.command("windev")
def parse_windev(
    filepath: Annotated[
        Path,
        typer.Argument(
            help="Chemin vers le fichier WinDev (.wdw, .wdg, .wda)",
            exists=True,
            dir_okay=False,
        ),
    ],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Sortie brute en JSON")
    ] = False,
) -> None:
    """Parse un fichier WinDev et affiche l'AST structure."""
    parser = WinDevParser()
    ast = parser.parse_file(filepath)

    if json_output:
        console.print_json(ast.model_dump_json(indent=2))
        return

    # En-tete
    console.print(
        Panel(
            f"[bold cyan]Fichier :[/] {ast.filename}\n"
            f"[bold cyan]Lignes  :[/] {ast.total_lines}\n"
            f"[bold cyan]Procedures :[/] {len(ast.procedures)}\n"
            f"[bold cyan]Requetes HFSQL :[/] {len(ast.hfsql_queries)}\n"
            f"[bold cyan]Conditions :[/] {len(ast.conditions)}",
            title="Tharos Parser — Resultat",
            border_style="bright_blue",
        )
    )

    # Variables globales
    if ast.global_variables:
        table = Table(title="Variables Globales", show_lines=False)
        table.add_column("Nom", style="green", no_wrap=True)
        table.add_column("Type WLanguage", style="yellow")
        table.add_column("Ligne", justify="right", style="dim")

        for var in ast.global_variables:
            table.add_row(var.name, var.wtype.value, str(var.line))
        console.print(table)

    # Procedures
    for proc in ast.procedures:
        params_str = ", ".join(
            f"{p.name} ({p.wtype.value})" for p in proc.parameters
        )
        ret_str = proc.return_value or "—"

        table = Table(
            title=f"Procedure : {proc.name}({params_str})",
            show_lines=True,
        )
        table.add_column("Detail", style="white")

        table.add_row(f"[bold]Retour :[/] {ret_str}")
        table.add_row(
            f"[bold]Variables locales :[/] "
            + ", ".join(f"{v.name} ({v.wtype.value})" for v in proc.local_variables)
            or "—"
        )

        body_preview = "\n".join(proc.body_lines[:10])
        if len(proc.body_lines) > 10:
            body_preview += f"\n... (+{len(proc.body_lines) - 10} lignes)"
        table.add_row(f"[bold]Corps :[/]\n{body_preview}")

        console.print(table)

    # Requetes HFSQL
    if ast.hfsql_queries:
        table = Table(title="Requetes HFSQL", show_lines=False)
        table.add_column("Type", style="bold magenta", no_wrap=True)
        table.add_column("Table", style="cyan")
        table.add_column("SQL", style="dim")
        table.add_column("Ligne", justify="right", style="dim")

        for q in ast.hfsql_queries:
            table.add_row(q.query_type.value, q.target_table, q.raw_sql, str(q.line))
        console.print(table)

    # Conditions
    if ast.conditions:
        table = Table(title="Conditions", show_lines=False)
        table.add_column("Type", style="bold red", no_wrap=True)
        table.add_column("Expression", style="white")
        table.add_column("Ligne", justify="right", style="dim")

        for c in ast.conditions:
            table.add_row(c.condition_type, c.expression, str(c.line))
        console.print(table)


@graph_app.command("windev")
def graph_windev(
    filepath: Annotated[
        Path,
        typer.Argument(
            help="Chemin vers le fichier WinDev (.wdw, .wdg, .wda)",
            exists=True,
            dir_okay=False,
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Sauvegarder le graphe en JSON"),
    ] = None,
) -> None:
    """Genere le graphe de dependances et l'affiche dans le terminal."""
    parser = WinDevParser()
    ast = parser.parse_file(filepath)

    builder = DependencyGraphBuilder(ast)
    graph = builder.build()

    # En-tete
    n_edges = graph.number_of_edges()
    n_nodes = graph.number_of_nodes()
    console.print(
        Panel(
            f"[bold cyan]Fichier :[/] {ast.filename}\n"
            f"[bold cyan]Noeuds  :[/] {n_nodes}\n"
            f"[bold cyan]Aretes  :[/] {n_edges}",
            title="Tharos Graph — Dependances",
            border_style="bright_green",
        )
    )

    # Affichage en arbre par procedure
    for proc in ast.procedures:
        tree = Tree(f"[bold green]{proc.name}[/]", guide_style="bright_green")

        # Appels vers d'autres procedures
        calls = [
            (t, d.get("kind", ""))
            for _, t, d in graph.out_edges(proc.name, data=True)
            if d.get("kind") == "calls"
        ]
        if calls:
            calls_branch = tree.add("[bold magenta]Appelle[/]")
            for target, _ in calls:
                calls_branch.add(f"[white]{target}[/]")

        # Tables accesseees
        tables = [
            (t, d.get("operation", ""))
            for _, t, d in graph.out_edges(proc.name, data=True)
            if d.get("kind") == "accesses"
        ]
        if tables:
            tables_branch = tree.add("[bold cyan]Accede aux tables[/]")
            for target, op in tables:
                table_name = target.replace("TABLE:", "")
                tables_branch.add(f"[white]{table_name}[/] [dim]({op})[/]")

        # Variables utilisees
        vars_used = [
            (t, d.get("kind", ""))
            for _, t, d in graph.out_edges(proc.name, data=True)
            if d.get("kind") == "uses"
        ]
        if vars_used:
            vars_branch = tree.add("[bold yellow]Utilise les variables[/]")
            for target, _ in vars_used:
                var_name = target.replace("VAR:", "")
                vars_branch.add(f"[white]{var_name}[/]")

        console.print(tree)

    # Sauvegarde optionnelle
    if output:
        builder.save_json(output)
        console.print(f"\n[bold green]Graphe sauvegarde dans :[/] {output}")


if __name__ == "__main__":
    app()
