"""Tests unitaires pour le module de transpilation FacturationClient."""

import pytest
from decimal import Decimal
from typing import Any, Dict, List

from tharos.transpiled.facturation_client import (
    CodeTVA,
    FacturationClient,
    LigneFacture,
    StatutFacture,
    calculer_tva,
)


class FakeDb:
    """Simulation de session de base de données pour les tests."""

    def __init__(self, rows: List[Dict[str, Any]] | None = None) -> None:
        self._rows = rows or []
        self.executed: List[tuple[str, List[Any]]] = []

    def execute(self, sql: str, params: List[Any]) -> None:
        """Enregistre la requête exécutée."""
        self.executed.append((sql, params))

    def fetch_first(self) -> Dict[str, Any] | None:
        """Retourne la première ligne ou None si vide."""
        if self._rows:
            return self._rows[0]
        return None


def test_calculer_tva():
    """Test de la fonction calculer_tva avec différentes valeurs."""
    
    # Test TX20
    result = calculer_tva(Decimal("100"), CodeTVA.TX20.value)
    assert result == Decimal("20.00")
    
    # Test TX10  
    result = calculer_tva(Decimal("100"), CodeTVA.TX10.value)
    assert result == Decimal("10.00")
    
    # Test default (inconnu)
    result = calculer_tva(Decimal("100"), "INCONNU")
    assert result == Decimal("0.00")
    
    # Test avec montant non entier
    result = calculer_tva(Decimal("50.50"), CodeTVA.TX20.value)
    assert result == Decimal("10.10")


def test_valider_facture_ok():
    """Test de validation de facture avec succès."""
    db = FakeDb([{"STATUT": "NONVALIDEE"}])
    
    client = FacturationClient(db)
    result = client.valider_facture(123)
    
    assert result is True
    assert len(db.executed) == 2  # SELECT + UPDATE
    
    # Vérifie l'UPDATE
    update_sql, update_params = db.executed[1]
    assert "UPDATE FACTURE SET STATUT" in update_sql
    assert update_params[0] == StatutFacture.VALIDEE.value
    assert update_params[2] == 123


def test_valider_facture_invalide():
    """Test de validation avec numéro de facture invalide."""
    db = FakeDb()
    
    client = FacturationClient(db)
    result = client.valider_facture(-1)
    
    assert result is False
    assert len(db.executed) == 0  # Aucune requête exécutée


def test_valider_facture_introuvable():
    """Test de validation avec facture introuvable."""
    db = FakeDb()  # Pas de lignes
    
    client = FacturationClient(db)
    result = client.valider_facture(123)
    
    assert result is False
    assert len(db.executed) == 1  # SELECT uniquement


def test_valider_facture_deja_validee():
    """Test de validation avec facture déjà validée."""
    db = FakeDb([{"STATUT": StatutFacture.VALIDEE.value}])
    
    client = FacturationClient(db)
    result = client.valider_facture(123)
    
    assert result is False
    assert len(db.executed) == 1  # SELECT uniquement


def test_ajouter_ligne_facture():
    """Test d'ajout d'une ligne de facture."""
    db = FakeDb()
    
    client = FacturationClient(db)
    client.ajouter_ligne_facture(123, "Produit A", Decimal("50"), 2)
    
    assert len(db.executed) == 1  # INSERT uniquement
    
    insert_sql, insert_params = db.executed[0]
    assert "INSERT INTO LIGNE_FACTURE" in insert_sql
    assert insert_params[0] == 123  # num_facture
    assert insert_params[1] == "Produit A"  # designation
    assert insert_params[2] == Decimal("50")  # prix_unitaire
    assert insert_params[3] == 2  # quantite
    assert insert_params[4] == Decimal("100")  # montant_ht (50 * 2)
    assert insert_params[5] == Decimal("20.00")  # montant_tva (100 * 0.20)


def test_supprimer_ligne_facture_ok():
    """Test de suppression d'une ligne avec succès."""
    db = FakeDb()
    
    client = FacturationClient(db)
    result = client.supprimer_ligne_facture(456)
    
    assert result is True
    assert len(db.executed) == 1  # DELETE
    
    delete_sql, delete_params = db.executed[0]
    assert "DELETE FROM LIGNE_FACTURE" in delete_sql
    assert delete_params[0] == 456


def test_supprimer_ligne_facture_invalide():
    """Test de suppression avec ID invalide."""
    db = FakeDb()
    
    client = FacturationClient(db)
    result = client.supprimer_ligne_facture(-1)
    
    assert result is False
    assert len(db.executed) == 0


def test_calculer_total_facture_avec_lignes():
    """Test de calcul du total avec lignes existantes."""
    db = FakeDb([{"TOTAL_HT": "200.00", "TOTAL_TVA": "40.00"}])
    
    client = FacturationClient(db)
    result = client.calculer_total_facture(123)
    
    assert result == Decimal("240.00")
    assert len(db.executed) == 2  # SELECT + UPDATE
    
    # Vérifie l'UPDATE
    update_sql, update_params = db.executed[1]
    assert "UPDATE FACTURE SET TOTAL_HT" in update_sql
    assert update_params[0] == Decimal("200.00")  # total_ht_local
    assert update_params[1] == Decimal("40.00")   # tva_totale  
    assert update_params[2] == Decimal("240.00")  # total_ttc_local
    assert update_params[3] == 123


def test_calculer_total_facture_sans_lignes():
    """Test de calcul du total avec aucune ligne."""
    db = FakeDb()  # Aucune ligne
    
    client = FacturationClient(db)
    result = client.calculer_total_facture(123)
    
    assert result == Decimal("0.00")
    assert len(db.executed) == 2  # SELECT + UPDATE
    
    # Vérifie l'UPDATE
    update_sql, update_params = db.executed[1]
    assert "UPDATE FACTURE SET TOTAL_HT" in update_sql
    assert update_params[0] == Decimal("0.00")  # total_ht_local
    assert update_params[1] == Decimal("0.00")  # tva_totale  
    assert update_params[2] == Decimal("0.00")  # total_ttc_local