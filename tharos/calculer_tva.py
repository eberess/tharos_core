from typing import Any

class TaxRateModel:
    TX20 = 0.20
    TX10 = 0.10
    DEFAULT = 0.00

async def calculer_tva(n_montant_ht: float, s_code_tva: str) -> Any:
    """
    Calcule la TVA en fonction du montant HT et du code TVA.

    :param n_montant_ht: Montant hors taxe
    :param s_code_tva: Code de la TVA
    :return: Montant de la TVA
    """
    n_tva = 0.0

    if s_code_tva == "TX20":
        n_tva = TaxRateModel.TX20
    elif s_code_tva == "TX10":
        n_tva = TaxRateModel.TX10
    else:
        n_tva = TaxRateModel.DEFAULT

    return n_montant_ht * n_tva