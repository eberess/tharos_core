"""Point d'entree CLI de Tharos Core."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tharos.parsers.windev import WinDevParser

app = typer.Typer(name="tharos", help="Tharos Core — Moteur de Migration WinDev")
parse_app = typer.Typer(help="Outils de parsing de fichiers legacy")
app.add_typer(parse_app, name="parse")

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


if __name__ == "__main__":
    app()
