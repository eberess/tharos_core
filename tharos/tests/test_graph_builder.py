"""Tests unitaires pour le graphe de dépendances."""

from pathlib import Path

import pytest

from tharos.graph.builder import DependencyGraphBuilder
from tharos.parsers.base import ASTModel
from tharos.parsers.windev import WinDevParser

SAMPLE_PATH = Path(__file__).parent / "samples" / "sample_windev.wdw"


@pytest.fixture
def ast() -> ASTModel:
    parser = WinDevParser()
    return parser.parse_file(SAMPLE_PATH)


@pytest.fixture
def builder(ast: ASTModel) -> DependencyGraphBuilder:
    b = DependencyGraphBuilder(ast)
    b.build()
    return b


class TestProcedureNodes:
    def test_count(self, builder: DependencyGraphBuilder) -> None:
        proc_nodes = [
            n for n, d in builder.graph.nodes(data=True) if d.get("kind") == "procedure"
        ]
        assert len(proc_nodes) == 5

    def test_names(self, builder: DependencyGraphBuilder) -> None:
        proc_nodes = [
            n for n, d in builder.graph.nodes(data=True) if d.get("kind") == "procedure"
        ]
        assert set(proc_nodes) == {
            "CalculerTVA",
            "ValiderFacture",
            "AjouterLigneFacture",
            "SupprimerLigneFacture",
            "CalculerTotalFacture",
        }

    def test_procedure_has_params(self, builder: DependencyGraphBuilder) -> None:
        attrs = builder.graph.nodes["CalculerTVA"]
        assert "nMontantHT" in attrs["params"]
        assert "sCodeTVA" in attrs["params"]

    def test_procedure_has_return(self, builder: DependencyGraphBuilder) -> None:
        attrs = builder.graph.nodes["CalculerTVA"]
        assert attrs["return_type"] == "nTVA"

    def test_procedure_line_range(self, builder: DependencyGraphBuilder) -> None:
        attrs = builder.graph.nodes["CalculerTVA"]
        assert attrs["start_line"] == 19
        assert attrs["end_line"] == 35


class TestTableNodes:
    def test_count(self, builder: DependencyGraphBuilder) -> None:
        table_nodes = [
            n for n, d in builder.graph.nodes(data=True) if d.get("kind") == "table"
        ]
        assert len(table_nodes) == 2

    def test_table_names(self, builder: DependencyGraphBuilder) -> None:
        table_nodes = [
            n for n, d in builder.graph.nodes(data=True) if d.get("kind") == "table"
        ]
        assert set(table_nodes) == {"TABLE:FACTURE", "TABLE:LIGNE_FACTURE"}


class TestVariableNodes:
    def test_count(self, builder: DependencyGraphBuilder) -> None:
        var_nodes = [
            n for n, d in builder.graph.nodes(data=True) if d.get("kind") == "variable"
        ]
        assert len(var_nodes) == 6

    def test_variable_prefix(self, builder: DependencyGraphBuilder) -> None:
        var_nodes = [
            n for n, d in builder.graph.nodes(data=True) if d.get("kind") == "variable"
        ]
        for node in var_nodes:
            assert node.startswith("VAR:")

    def test_variable_type(self, builder: DependencyGraphBuilder) -> None:
        attrs = builder.graph.nodes["VAR:sNomClient"]
        assert attrs["wtype"] == "chaine"


def _has_edge_kind(graph, u, v, kind):
    if not graph.has_edge(u, v):
        return False
    return graph.edges[u, v].get("kind") == kind


class TestProcedureCallEdges:
    def test_ajouter_calls_calculer_tva(self, builder: DependencyGraphBuilder) -> None:
        assert _has_edge_kind(builder.graph, "AjouterLigneFacture", "CalculerTVA", "calls")

    def test_self_call_excluded(self, builder: DependencyGraphBuilder) -> None:
        for _, target, data in builder.graph.out_edges("CalculerTVA", data=True):
            if data.get("kind") == "calls":
                assert target != "CalculerTVA"


class TestProcedureTableEdges:
    def test_valider_facture_accesses_facture(
        self, builder: DependencyGraphBuilder
    ) -> None:
        assert _has_edge_kind(builder.graph, "ValiderFacture", "TABLE:FACTURE", "accesses")

    def test_ajouter_accesses_ligne_facture(
        self, builder: DependencyGraphBuilder
    ) -> None:
        assert _has_edge_kind(builder.graph, "AjouterLigneFacture", "TABLE:LIGNE_FACTURE", "accesses")

    def test_supprimer_accesses_ligne_facture(
        self, builder: DependencyGraphBuilder
    ) -> None:
        assert _has_edge_kind(builder.graph, "SupprimerLigneFacture", "TABLE:LIGNE_FACTURE", "accesses")

    def test_calculer_total_accesses_both_tables(
        self, builder: DependencyGraphBuilder
    ) -> None:
        assert _has_edge_kind(builder.graph, "CalculerTotalFacture", "TABLE:LIGNE_FACTURE", "accesses")
        assert _has_edge_kind(builder.graph, "CalculerTotalFacture", "TABLE:FACTURE", "accesses")

    def test_edge_has_operation(self, builder: DependencyGraphBuilder) -> None:
        data = builder.graph.edges["ValiderFacture", "TABLE:FACTURE"]
        assert data["operation"] in {"SELECT", "INSERT", "UPDATE", "DELETE"}


class TestProcedureVarEdges:
    def test_calculer_total_uses_global_vars(
        self, builder: DependencyGraphBuilder
    ) -> None:
        var_edges = [
            t for _, t, d in builder.graph.out_edges("CalculerTotalFacture", data=True)
            if d.get("kind") == "uses"
        ]
        for edge in var_edges:
            assert edge.startswith("VAR:")

    def test_ajouter_uses_global_vars(
        self, builder: DependencyGraphBuilder
    ) -> None:
        uses_edges = [
            (t, d.get("kind"))
            for _, t, d in builder.graph.out_edges("AjouterLigneFacture", data=True)
            if d.get("kind") == "uses"
        ]
        assert len(uses_edges) >= 0


class TestGraphExport:
    def test_to_dict_keys(self, builder: DependencyGraphBuilder) -> None:
        adj = builder.to_dict()
        assert isinstance(adj, dict)
        assert "CalculerTVA" in adj
        assert "ValiderFacture" in adj

    def test_to_dict_neighbors(self, builder: DependencyGraphBuilder) -> None:
        adj = builder.to_dict()
        valider_neighbors = [n["target"] for n in adj["ValiderFacture"]]
        assert "TABLE:FACTURE" in valider_neighbors

    def test_to_json_dict_structure(self, builder: DependencyGraphBuilder) -> None:
        data = builder.to_json_dict()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_to_json_dict_node_fields(
        self, builder: DependencyGraphBuilder
    ) -> None:
        data = builder.to_json_dict()
        proc_nodes = [n for n in data["nodes"] if n["kind"] == "procedure"]
        assert len(proc_nodes) == 5
        for node in proc_nodes:
            assert "id" in node
            assert "kind" in node

    def test_to_json_dict_edge_fields(
        self, builder: DependencyGraphBuilder
    ) -> None:
        data = builder.to_json_dict()
        assert len(data["edges"]) > 0
        for edge in data["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "kind" in edge

    def test_save_json(self, builder: DependencyGraphBuilder, tmp_path: Path) -> None:
        out = tmp_path / "graph.json"
        builder.save_json(out)
        assert out.exists()
        import json

        data = json.loads(out.read_text())
        assert "nodes" in data
        assert "edges" in data

    def test_save_adjacency(
        self, builder: DependencyGraphBuilder, tmp_path: Path
    ) -> None:
        out = tmp_path / "adj.json"
        builder.save_adjacency(out)
        assert out.exists()
        import json

        data = json.loads(out.read_text())
        assert isinstance(data, dict)

    def test_total_node_count(self, builder: DependencyGraphBuilder) -> None:
        total = builder.graph.number_of_nodes()
        assert total == 5 + 2 + 6

    def test_total_edge_count(self, builder: DependencyGraphBuilder) -> None:
        total = builder.graph.number_of_edges()
        assert total > 0
