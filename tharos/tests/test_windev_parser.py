"""Tests unitaires pour le parser WinDev."""

from pathlib import Path

import pytest

from tharos.parsers.base import (
    ASTModel,
    HFSQLQueryType,
    VariableType,
)
from tharos.parsers.windev import WinDevParser

SAMPLE_PATH = Path(__file__).parent / "samples" / "sample_windev.wdw"


@pytest.fixture
def ast() -> ASTModel:
    parser = WinDevParser()
    return parser.parse_file(SAMPLE_PATH)


class TestGlobalVariables:
    def test_count(self, ast: ASTModel) -> None:
        assert len(ast.global_variables) == 6

    def test_names(self, ast: ASTModel) -> None:
        names = [v.name for v in ast.global_variables]
        assert names == [
            "sNomClient",
            "nTotalHT",
            "nTotalTTC",
            "dDateFacture",
            "bFactureValidee",
            "tabLignesFacture",
        ]

    def test_types(self, ast: ASTModel) -> None:
        types = [v.wtype for v in ast.global_variables]
        assert types == [
            VariableType.CHAINE,
            VariableType.MONETAIRE,
            VariableType.MONETAIRE,
            VariableType.DATE,
            VariableType.BOOLEEN,
            VariableType.COMPLEXE,
        ]

    def test_all_global(self, ast: ASTModel) -> None:
        assert all(v.is_global for v in ast.global_variables)


class TestProcedures:
    def test_count(self, ast: ASTModel) -> None:
        assert len(ast.procedures) == 5

    def test_names(self, ast: ASTModel) -> None:
        names = [p.name for p in ast.procedures]
        assert names == [
            "CalculerTVA",
            "ValiderFacture",
            "AjouterLigneFacture",
            "SupprimerLigneFacture",
            "CalculerTotalFacture",
        ]

    def test_calculer_tva_params(self, ast: ASTModel) -> None:
        proc = ast.procedures[0]
        assert proc.name == "CalculerTVA"
        assert len(proc.parameters) == 2
        assert proc.parameters[0].name == "nMontantHT"
        assert proc.parameters[0].wtype == VariableType.MONETAIRE
        assert proc.parameters[1].name == "sCodeTVA"
        assert proc.parameters[1].wtype == VariableType.CHAINE

    def test_calculer_tva_return(self, ast: ASTModel) -> None:
        proc = ast.procedures[0]
        assert proc.return_value == "nTVA"

    def test_calculer_tva_local_vars(self, ast: ASTModel) -> None:
        proc = ast.procedures[0]
        local_names = [v.name for v in proc.local_variables]
        assert "nTVA" in local_names
        assert "nTauxTVA" in local_names

    def test_valider_facture_params(self, ast: ASTModel) -> None:
        proc = ast.procedures[1]
        assert proc.name == "ValiderFacture"
        assert len(proc.parameters) == 1
        assert proc.parameters[0].name == "nNumFacture"
        assert proc.parameters[0].wtype == VariableType.ENTIER

    def test_ajouter_ligne_params(self, ast: ASTModel) -> None:
        proc = ast.procedures[2]
        assert proc.name == "AjouterLigneFacture"
        assert len(proc.parameters) == 4
        param_names = [p.name for p in proc.parameters]
        assert param_names == ["nNumFacture", "sDesignation", "nPrixUnitaire", "nQuantite"]

    def test_supprimer_ligne_return(self, ast: ASTModel) -> None:
        proc = ast.procedures[3]
        assert proc.name == "SupprimerLigneFacture"
        assert proc.return_value == "VRAI"

    def test_calculer_total_return(self, ast: ASTModel) -> None:
        proc = ast.procedures[4]
        assert proc.name == "CalculerTotalFacture"
        assert proc.return_value == "nTotalTTCLocal"


class TestHFSQLQueries:
    def test_count(self, ast: ASTModel) -> None:
        assert len(ast.hfsql_queries) == 6

    def test_select_facture(self, ast: ASTModel) -> None:
        selects = [q for q in ast.hfsql_queries if q.query_type == HFSQLQueryType.SELECT]
        assert len(selects) == 2
        tables = [q.target_table for q in selects]
        assert "FACTURE" in tables
        assert "LIGNE_FACTURE" in tables

    def test_insert_ligne(self, ast: ASTModel) -> None:
        inserts = [q for q in ast.hfsql_queries if q.query_type == HFSQLQueryType.INSERT]
        assert len(inserts) == 1
        assert inserts[0].target_table == "LIGNE_FACTURE"

    def test_update_facture(self, ast: ASTModel) -> None:
        updates = [q for q in ast.hfsql_queries if q.query_type == HFSQLQueryType.UPDATE]
        assert len(updates) == 2
        tables = [q.target_table for q in updates]
        assert all(t == "FACTURE" for t in tables)

    def test_delete_ligne(self, ast: ASTModel) -> None:
        deletes = [q for q in ast.hfsql_queries if q.query_type == HFSQLQueryType.DELETE]
        assert len(deletes) == 1
        assert deletes[0].target_table == "LIGNE_FACTURE"

    def test_tables_affected(self, ast: ASTModel) -> None:
        tables = {q.target_table for q in ast.hfsql_queries}
        assert tables == {"FACTURE", "LIGNE_FACTURE"}


class TestASTModel:
    def test_filename(self, ast: ASTModel) -> None:
        assert ast.filename == "sample_windev.wdw"

    def test_total_lines(self, ast: ASTModel) -> None:
        assert ast.total_lines == 115
