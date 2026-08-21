"""Transpilation de FacturationClient.wdw (WinDev/WLanguage) vers Python 3.12 typé.

Ce module respecte les règles de transpilation Tharos :
- les montants 'monétaire' sont traduits par ``decimal.Decimal`` (jamais ``float``) ;
- les codes métiers fixes utilisent des ``enum.Enum`` ;
- aucune ternaire imbriquée ; structures ``if/elif/else`` explicites ;
- logique métier strictement conservée (isofonctionnalité).
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Protocol, Sequence

logger = logging.getLogger(__name__)


class CodeTVA(str, Enum):
    """Codes TVA gérés par la fenêtre de facturation."""

    TX20 = "TX20"
    TX10 = "TX10"


class StatutFacture(str, Enum):
    """Statuts possibles d'une facture."""

    VALIDEE = "VALIDEE"


@dataclass
class LigneFacture:
    """Ligne d'une facture (structure WLanguage ``ligne facture``)."""

    num_facture: int
    designation: str
    prix_unitaire: Decimal
    quantite: int
    montant_ht: Decimal
    montant_tva: Decimal


@dataclass
class Facture:
    """Etat courant de la facture (variables globales de la fenêtre)."""

    nom_client: str = ""
    total_ht: Decimal = Decimal("0")
    total_ttc: Decimal = Decimal("0")
    date_facture: dt.date | None = None
    facture_validee: bool = False
    lignes: list[LigneFacture] = field(default_factory=list)


def calculer_tva(montant_ht: Decimal, code_tva: str) -> Decimal:
    """Calcule le montant de TVA à partir d'un montant HT et d'un code TVA.

    :param montant_ht: Montant hors taxe (monétaire).
    :param code_tva: Code TVA parmi ``CodeTVA``.
    :return: Montant de la TVA (monétaire).
    """
    if code_tva == CodeTVA.TX20.value:
        taux_tva = Decimal("0.20")
    elif code_tva == CodeTVA.TX10.value:
        taux_tva = Decimal("0.10")
    else:
        taux_tva = Decimal("0.00")

    return montant_ht * taux_tva


class DbSession(Protocol):
    """Port d'accès aux données (HFSQL -> PostgreSQL)."""

    def execute(self, sql: str, params: Sequence[Any]) -> None: ...
    def fetch_first(self) -> dict[str, Any] | None: ...


def afficher_erreur(message: str) -> None:
    """Affiche un message d'erreur dans les logs."""
    logger.error("ERREUR: %s", message)


def afficher_info(message: str) -> None:
    """Affiche un message d'information dans les logs."""
    logger.info("INFO: %s", message)


class FacturationClient:
    """Classe représentant la fenêtre de facturation."""

    def __init__(self, db: DbSession) -> None:
        self.db = db
        self.etat = Facture()

    def valider_facture(self, num_facture: int) -> bool:
        """Valide une facture après vérification de son existence."""
        if num_facture <= 0:
            afficher_erreur("Numéro de facture invalide")
            return False

        self.db.execute(
            "SELECT * FROM FACTURE WHERE NUM_FACTURE = %s",
            [num_facture],
        )
        ligne = self.db.fetch_first()
        if ligne is None:
            afficher_erreur("Facture introuvable")
            return False

        statut = ligne["STATUT"]
        if statut == StatutFacture.VALIDEE.value:
            afficher_info("Facture déjà validée")
            return False

        self.db.execute(
            "UPDATE FACTURE SET STATUT = %s, DATE_VALIDATION = %s WHERE NUM_FACTURE = %s",
            [StatutFacture.VALIDEE.value, dt.date.today(), num_facture],
        )
        return True

    def ajouter_ligne_facture(
        self,
        num_facture: int,
        designation: str,
        prix_unitaire: Decimal,
        quantite: int,
    ) -> None:
        """Ajoute une ligne à la facture après calcul de la TVA."""
        montant_ligne = prix_unitaire * Decimal(quantite)
        montant_tva = calculer_tva(montant_ligne, CodeTVA.TX20.value)

        self.db.execute(
            "INSERT INTO LIGNE_FACTURE "
            "(NUM_FACTURE, DESIGNATION, PRIX_UNITAIRE, QUANTITE, MONTANT_HT, MONTANT_TVA) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [
                num_facture, designation, prix_unitaire,
                quantite, montant_ligne, montant_tva,
            ],
        )

        afficher_info("Ligne ajoutée avec succès")

    def supprimer_ligne_facture(self, id_ligne: int) -> bool:
        """Supprime une ligne de facture."""
        if id_ligne <= 0:
            afficher_erreur("ID ligne invalide")
            return False

        self.db.execute(
            "DELETE FROM LIGNE_FACTURE WHERE ID_LIGNE = %s",
            [id_ligne],
        )
        return True

    def calculer_total_facture(self, num_facture: int) -> Decimal:
        """Calcule le total HT/TVA/TTC pour une facture."""
        self.db.execute(
            "SELECT SUM(MONTANT_HT) AS TOTAL_HT, SUM(MONTANT_TVA) AS TOTAL_TVA "
            "FROM LIGNE_FACTURE WHERE NUM_FACTURE = %s",
            [num_facture],
        )
        ligne = self.db.fetch_first()
        if ligne is None:
            total_ht_local = Decimal("0")
            tva_totale = Decimal("0")
        else:
            total_ht_local = Decimal(str(ligne["TOTAL_HT"]))
            tva_totale = Decimal(str(ligne["TOTAL_TVA"]))

        total_ttc_local = total_ht_local + tva_totale

        self.db.execute(
            "UPDATE FACTURE SET TOTAL_HT = %s, TOTAL_TVA = %s, TOTAL_TTC = %s "
            "WHERE NUM_FACTURE = %s",
            [total_ht_local, tva_totale, total_ttc_local, num_facture],
        )
        return total_ttc_local