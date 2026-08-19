"""Construction du graphe de dependances fonctionnel."""

import json
import re
from pathlib import Path

import networkx as nx

from tharos.parsers.base import ASTModel, ASTProcedure

# Pattern pour detecter les appels de procédures dans le corps
RE_CALL = re.compile(r"(?<!//)\b(?P<proc>\w+)\s*\(")


class DependencyGraphBuilder:
    """Construit un graphe orienté de dépendances à partir d'un AST."""

    def __init__(self, ast: ASTModel) -> None:
        self.ast = ast
        self.graph = nx.DiGraph()
        self._proc_names = {p.name for p in ast.procedures}

    def build(self) -> nx.DiGraph:
        """Construit le graphe complet de dépendances."""
        self._add_procedure_nodes()
        self._add_table_nodes()
        self._add_global_var_nodes()
        self._add_procedure_call_edges()
        self._add_procedure_table_edges()
        self._add_procedure_var_edges()
        return self.graph

    def _add_procedure_nodes(self) -> None:
        for proc in self.ast.procedures:
            params = ", ".join(f"{p.name}:{p.wtype.value}" for p in proc.parameters)
            self.graph.add_node(
                proc.name,
                kind="procedure",
                params=params,
                return_type=proc.return_value or "",
                start_line=proc.start_line,
                end_line=proc.end_line,
            )

    def _add_table_nodes(self) -> None:
        tables = {q.target_table for q in self.ast.hfsql_queries}
        for table in tables:
            self.graph.add_node(
                f"TABLE:{table}",
                kind="table",
                label=table,
            )

    def _add_global_var_nodes(self) -> None:
        for var in self.ast.global_variables:
            self.graph.add_node(
                f"VAR:{var.name}",
                kind="variable",
                wtype=var.wtype.value,
                line=var.line,
            )

    def _add_procedure_call_edges(self) -> None:
        """Détecte les appels entre procédures dans le corps de chaque procédure."""
        for proc in self.ast.procedures:
            body = "\n".join(proc.body_lines)
            calls_found: set[str] = set()

            for match in RE_CALL.finditer(body):
                called_name = match.group("proc")
                if called_name in self._proc_names and called_name != proc.name:
                    if called_name not in calls_found:
                        calls_found.add(called_name)
                        self.graph.add_edge(proc.name, called_name, kind="calls")

    def _add_procedure_table_edges(self) -> None:
        """Relie les procédures aux tables HFSQL qu'elles manipulent."""
        for proc in self.ast.procedures:
            start = proc.start_line - 1
            end = proc.end_line - 1
            tables_used: set[str] = set()

            for query in self.ast.hfsql_queries:
                # Position approximative de la requête dans le fichier
                # On approxime: si la ligne de la requête est entre start et end
                if start <= query.line <= end:
                    if query.target_table not in tables_used:
                        tables_used.add(query.target_table)
                        self.graph.add_edge(
                            proc.name,
                            f"TABLE:{query.target_table}",
                            kind="accesses",
                            operation=query.query_type.value,
                        )

    def _add_procedure_var_edges(self) -> None:
        """Relie les procédures aux variables globales qu'elles utilisent."""
        for proc in self.ast.procedures:
            body = "\n".join(proc.body_lines)
            used_vars: set[str] = set()

            for var in self.ast.global_variables:
                # Cherche le nom de la variable comme mot complet dans le corps
                if re.search(rf"\b{re.escape(var.name)}\b", body):
                    if var.name not in used_vars:
                        used_vars.add(var.name)
                        self.graph.add_edge(proc.name, f"VAR:{var.name}", kind="uses")

    # ── Export ────────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Exporte le graphe sous forme de dictionnaire d'adjacence."""
        adjacency: dict[str, list[dict[str, str]]] = {}
        for node in self.graph.nodes:
            neighbors = []
            for _, target, data in self.graph.out_edges(node, data=True):
                neighbors.append({"target": target, "kind": data.get("kind", "")})
            adjacency[node] = neighbors
        return adjacency

    def to_json_dict(self) -> dict:
        """Exporte le graphe en JSON structuré (noeuds + arêtes)."""
        nodes = []
        for node, attrs in self.graph.nodes(data=True):
            nodes.append({"id": node, **attrs})

        edges = []
        for source, target, attrs in self.graph.edges(data=True):
            edges.append({"source": source, "target": target, **attrs})

        return {"nodes": nodes, "edges": edges}

    def save_json(self, filepath: Path) -> None:
        """Sauvegarde le graphe en JSON."""
        data = self.to_json_dict()
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def save_adjacency(self, filepath: Path) -> None:
        """Sauvegarde le dictionnaire d'adjacence en JSON."""
        data = self.to_dict()
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
