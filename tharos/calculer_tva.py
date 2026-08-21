"""Transpilation de la procédure ``CalculerTVA`` (WinDev/WLanguage).

Implémentation canonique respectant les normes Tharos :
- Utilisation de ``decimal.Decimal`` au lieu de ``float``
- Typage explicite avec ``typing`` 
- Structures ``if/elif/else`` claires
- Convention snake_case idiomatique
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any


class CodeTVA(str, Enum):
    """Codes TVA gérés par la fenêtre de facturation."""

    TX20 = "TX20"
    TX10 = "TX10"


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