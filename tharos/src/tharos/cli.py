"""Point d'entree CLI de Tharos Core."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from tharos.agents.translator import CodeTranslatorAgent, translate_with_retry
from tharos.graph.builder import DependencyGraphBuilder
from tharos.parsers.windev import WinDevParser

app = typer.Typer(name="tharos", help="Tharos Core — Moteur de Migration WinDev")
parse_app = typer.Typer(help="Outils de parsing de fichiers legacy")
graph_app = typer.Typer(help="Analyse des dependances")
translate_app = typer.Typer(help="Traduction de code legacy vers Python")
pipeline_app = typer.Typer(help="Pipeline complet de migration")
app.add_typer(parse_app, name="parse")
app.add_typer(graph_app, name="graph")
app.add_typer(translate_app, name="translate")
app.add_typer(pipeline_app, name="pipeline")

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


@translate_app.command("windev")
def translate_windev(
    filepath: Annotated[
        Path,
        typer.Argument(
            help="Chemin vers le fichier WinDev (.wdw, .wdg, .wda)",
            exists=True,
            dir_okay=False,
        ),
    ],
    proc_name: Annotated[
        str,
        typer.Option("--proc", "-p", help="Nom de la procedure a traduire"),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Sauvegarder le code genere dans un fichier"),
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Sortie brute en JSON")
    ] = False,
) -> None:
    """Traduit une procedure WinDev vers Python via LLM."""
    parser = WinDevParser()
    ast = parser.parse_file(filepath)

    proc = next((p for p in ast.procedures if p.name == proc_name), None)
    if proc is None:
        console.print(f"[bold red]Procedure '{proc_name}' non trouvee.[/]")
        available = [p.name for p in ast.procedures]
        console.print(f"[dim]Procedures disponibles : {', '.join(available)}[/]")
        raise typer.Exit(1)

    agent = CodeTranslatorAgent()
    result = agent.translate_procedure_with_graph(proc, ast)

    if json_output:
        console.print_json(
            json.dumps(
                {
                    "source_proc": result.source_proc,
                    "is_valid": result.is_valid,
                    "provider": result.provider,
                    "model": result.model,
                    "generated_code": result.generated_code,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    status = "[bold green]VALIDE[/]" if result.is_valid else "[bold red]INVALIDE[/]"
    console.print(
        Panel(
            f"[bold cyan]Procedure :[/] {result.source_proc}\n"
            f"[bold cyan]Fournisseur :[/] {result.provider}\n"
            f"[bold cyan]Modele :[/] {result.model}\n"
            f"[bold cyan]Syntaxe :[/] {status}",
            title="Tharos Translate — Resultat",
            border_style="bright_magenta",
        )
    )

    console.print(
        Panel(
            result.generated_code,
            title="Code Genere",
            border_style="bright_cyan",
            padding=(1, 2),
        )
    )

    if output:
        output.write_text(result.generated_code, encoding="utf-8")
        console.print(f"\n[bold green]Code sauvegarde dans :[/] {output}")


@pipeline_app.command("windev")
def pipeline_windev(
    filepath: Annotated[
        Path,
        typer.Argument(
            help="Chemin vers le fichier WinDev (.wdw, .wdg, .wda)",
            exists=True,
            dir_okay=False,
        ),
    ],
    proc_name: Annotated[
        str,
        typer.Option("--proc", "-p", help="Nom de la procedure a migrer"),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Sauvegarder le code final"),
    ] = None,
    max_attempts: Annotated[
        int, typer.Option("--attempts", "-n", help="Nombre max de tentatives")
    ] = 3,
) -> None:
    """Pipeline complet : AST -> Graphe -> Agent -> Sandbox -> Auto-correction."""
    parser = WinDevParser()
    ast = parser.parse_file(filepath)

    proc = next((p for p in ast.procedures if p.name == proc_name), None)
    if proc is None:
        console.print(f"[bold red]Procedure '{proc_name}' non trouvee.[/]")
        available = [p.name for p in ast.procedures]
        console.print(f"[dim]Procedures disponibles : {', '.join(available)}[/]")
        raise typer.Exit(1)

    builder = DependencyGraphBuilder(ast)
    graph = builder.build()

    console.print(
        Panel(
            f"[bold cyan]Fichier :[/] {ast.filename}\n"
            f"[bold cyan]Procedure :[/] {proc_name}\n"
            f"[bold cyan]Noeuds graphe :[/] {graph.number_of_nodes()}\n"
            f"[bold cyan]Aretes graphe :[/] {graph.number_of_edges()}\n"
            f"[bold cyan]Max tentatives :[/] {max_attempts}",
            title="Tharos Pipeline — Lancement",
            border_style="bright_yellow",
        )
    )

    with console.status("[bold bright_yellow]Execution du pipeline...[/]"):
        result = translate_with_retry(proc, ast, max_attempts=max_attempts)

    for record in result.history:
        icon = "[bold green]PASS[/]" if record.passed else "[bold red]FAIL[/]"
        console.print(
            f"  Tentative {record.attempt}/{max_attempts} : {icon} "
            f"(exit {record.exit_code})"
        )
        if not record.passed and record.logs:
            preview = record.logs.strip().splitlines()[-3:]
            for line in preview:
                console.print(f"    [dim]{line}[/]")

    if result.success:
        console.print(
            Panel(
                f"[bold green]SUCCES[/] en {result.attempts} tentative(s)\n"
                f"[bold cyan]Code final genere avec succes.[/]",
                title="Tharos Pipeline — Resultat",
                border_style="bright_green",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold red]ECHEC[/] apres {result.attempts} tentative(s)\n"
                f"[dim]Dernier traceback :[/]\n{result.history[-1].logs[-500:]}",
                title="Tharos Pipeline — Resultat",
                border_style="bright_red",
            )
        )

    console.print(
        Panel(
            result.final_code,
            title="Code Final",
            border_style="bright_cyan",
            padding=(1, 2),
        )
    )

    if output:
        output.write_text(result.final_code, encoding="utf-8")
        console.print(f"\n[bold green]Code sauvegarde dans :[/] {output}")


if __name__ == "__main__":
    app()
