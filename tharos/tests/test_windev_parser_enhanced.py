"""Tests unitaires pour le parser WinDev amélioré avec fichiers multi-procédures."""

from pathlib import Path

import pytest

from tharos.parsers.base import (
    ASTModel,
    HFSQLQueryType,
    VariableType,
)
from tharos.parsers.windev import WinDevParser

# Test with a more complex sample that has more procedures and better structure
COMPLEX_SAMPLE = """// ============================================================
// Fichier : ComplexeWinDev.wdw
// Fenêtre WinDev - Exemple complet multi-procédures
// ============================================================

// --- Déclarations globales ---
sNomClient est une chaîne
nTotalHT est un monétaire
nTotalTTC est un monétaire
dDateFacture est une date
bFactureValidee est un booléen
tabLignesFacture est un tableau de structures de la ligne facture

// --- Autres variables globales ---
sCodeErreur est une chaîne
nCodeRetour est un entier
bVerificationOK est un booléen

// --- Procédure 1 : CalculerTVA ---
// Calcule la TVA à partir du montant HT
PROCEDURE CalculerTVA(nMontantHT est un monétaire, sCodeTVA est une chaîne) LOCAL
    nTVA est un monétaire
    nTauxTVA est un réel

    SI sCodeTVA = "TX20" ALORS
        nTauxTVA = 0.20
    SINON SI sCodeTVA = "TX10" ALORS
        nTauxTVA = 0.10
    SINON
        nTauxTVA = 0.00
    FIN

    nTVA = nMontantHT * nTauxTVA
    RENVOYER nTVA

// --- Procédure 2 : ValiderFacture ---
// Vérifie et valide la facture en base
PROCEDURE ValiderFacture(nNumFacture est un entier) LOCAL
    sStatut est une chaîne

    SI nNumFacture <= 0 ALORS
        Erreur("Numéro de facture invalide")
        RENVOYER FAUX
    FIN

    // Requête HFSQL : lecture de la facture
    HExécuteRequêteSQL("SELECT * FROM FACTURE WHERE NUM_FACTURE = " + nNumFacture)
    HLitPremier(REQ_FACTURE)

    SI HFenDeHorsRequête(REQ_FACTURE) ALORS
        Erreur("Facture introuvable")
        RENVOYER FAUX
    FIN

    sStatut = FACTURE.STATUT

    SI sStatut = "VALIDEE" ALORS
        Info("Facture déjà validée")
        RENVOYER FAUX
    FIN

    // Mise à jour du statut
    HExécuteRequêteSQL("UPDATE FACTURE SET STATUT = 'VALIDEE', DATE_VALIDATION = SYSTEME.DATEJOUR() WHERE NUM_FACTURE = " + nNumFacture)

    RENVOYER VRAI

// --- Procédure 3 : AjouterLigneFacture ---
// Ajoute une ligne à la facture en cours
PROCEDURE AjouterLigneFacture(nNumFacture est un entier, sDesignation est une chaîne, nPrixUnitaire est un monétaire, nQuantite est un entier) LOCAL
    nMontantLigne est un monétaire
    nTVA est un monétaire

    nMontantLigne = nPrixUnitaire * nQuantite
    nTVA = CalculerTVA(nMontantLigne, "TX20")

    // Insertion HFSQL
    HExécuteRequêteSQL("INSERT INTO LIGNE_FACTURE (NUM_FACTURE, DESIGNATION, PRIX_UNITAIRE, QUANTITE, MONTANT_HT, MONTANT_TVA) VALUES (" +
        nNumFacture + ", '" + sDesignation + "', " + nPrixUnitaire + ", " + nQuantite + ", " + nMontantLigne + ", " + nTVA + ")")

    Info("Ligne ajoutée avec succès")

// --- Procédure 4 : SupprimerLigneFacture ---
// Supprime une ligne de facture par son ID
PROCEDURE SupprimerLigneFacture(nIDLigne est un entier) LOCAL
    SI nIDLigne <= 0 ALORS
        Erreur("ID ligne invalide")
        RENVOYER FAUX
    FIN

    HExécuteRequêteSQL("DELETE FROM LIGNE_FACTURE WHERE ID_LIGNE = " + nIDLigne)
    RENVOYER VRAI

// --- Procédure 5 : CalculerTotalFacture ---
// Recalcul le total HT et TTC de la facture
PROCEDURE CalculerTotalFacture(nNumFacture est un entier) LOCAL
    nTotalHTLocal est un monétaire
    nTotalTTCLocal est un monétaire
    nTVATotale est un monétaire

    HExécuteRequêteSQL("SELECT SUM(MONTANT_HT) AS TOTAL_HT, SUM(MONTANT_TVA) AS TOTAL_TVA FROM LIGNE_FACTURE WHERE NUM_FACTURE = " + nNumFacture)
    HLitPremier(REQ_FACTURE)

    SI HFenDeHorsRequête(REQ_FACTURE) ALORS
        nTotalHTLocal = 0
        nTVATotale = 0
    SINON
        nTotalHTLocal = REQ_FACTURE.TOTAL_HT
        nTVATotale = REQ_FACTURE.TOTAL_TVA
    FIN

    nTotalTTCLocal = nTotalHTLocal + nTVATotale

    // Mise à jour de la facture
    HExécuteRequêteSQL("UPDATE FACTURE SET TOTAL_HT = " + nTotalHTLocal + ", TOTAL_TVA = " + nTVATotale + ", TOTAL_TTC = " + nTotalTTCLocal + " WHERE NUM_FACTURE = " + nNumFacture)

    RENVOYER nTotalTTCLocal

// --- Procédure 6 : GererErreur ---
// Gère les erreurs dans le système
PROCEDURE GererErreur(sMessage est une chaîne) LOCAL
    sCodeErreur = sMessage
    nCodeRetour = -1
    bVerificationOK = FAUX
    
    HExécuteRequêteSQL("INSERT INTO LOG_ERREURS (MESSAGE, DATE_ERREUR) VALUES ('" + sMessage + "', SYSTEME.DATEJOUR())")
    
    RENVOYER VRAI

// --- Procédure 7 : CreerNouveauClient ---
// Crée un nouveau client
PROCEDURE CreerNouveauClient(sNom est une chaîne, sEmail est une chaîne) LOCAL
    nIdClient est un entier
    
    HExécuteRequêteSQL("INSERT INTO CLIENTS (NOM_CLIENT, EMAIL_CLIENT) VALUES ('" + sNom + "', '" + sEmail + "')")
    
    HExécuteRequêteSQL("SELECT ID_CLIENT FROM CLIENTS WHERE NOM_CLIENT = '" + sNom + "' AND EMAIL_CLIENT = '" + sEmail + "'")
    HLitPremier(REQ_CLIENT)
    
    nIdClient = REQ_CLIENT.ID_CLIENT
    
    RENVOYER nIdClient

// --- Procédure 8 : MettreAJourClient ---
// Met à jour les informations d'un client
PROCEDURE MettreAJourClient(nIdClient est un entier, sNom est une chaîne) LOCAL
    SI nIdClient <= 0 ALORS
        RENVOYER FAUX
    FIN
    
    HExécuteRequêteSQL("UPDATE CLIENTS SET NOM_CLIENT = '" + sNom + "' WHERE ID_CLIENT = " + nIdClient)
    
    RENVOYER VRAI
"""

def test_complex_parser():
    """Test complet du parser avec fichier multi-procédures."""
    parser = WinDevParser()
    
    # Test en mémoire avec le contenu
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.wdw', delete=False) as f:
        f.write(COMPLEX_SAMPLE)
        temp_path = f.name
    
    try:
        ast = parser.parse_file(Path(temp_path))
        
        # Vérification du nombre de procédures
        assert len(ast.procedures) == 8
        
        # Vérification des noms des procédures
        procedure_names = [p.name for p in ast.procedures]
        expected_names = [
            "CalculerTVA",
            "ValiderFacture", 
            "AjouterLigneFacture",
            "SupprimerLigneFacture",
            "CalculerTotalFacture",
            "GererErreur",
            "CreerNouveauClient",
            "MettreAJourClient"
        ]
        assert procedure_names == expected_names
        
        # Vérification des variables globales
        assert len(ast.global_variables) == 7
        
        # Vérification des types de variables globales
        global_types = [v.wtype for v in ast.global_variables]
        expected_types = [
            VariableType.CHAINE,     # sNomClient
            VariableType.MONETAIRE,  # nTotalHT
            VariableType.MONETAIRE,  # nTotalTTC
            VariableType.DATE,       # dDateFacture
            VariableType.BOOLEEN,    # bFactureValidee
            VariableType.CHAINE,     # sCodeErreur
            VariableType.ENTIER      # nCodeRetour
        ]
        assert global_types == expected_types
        
        # Vérification du contenu du premier procédure (CalculerTVA)
        calc_tva = ast.procedures[0] 
        assert calc_tva.name == "CalculerTVA"
        assert len(calc_tva.parameters) == 2
        assert calc_tva.parameters[0].name == "nMontantHT"
        assert calc_tva.parameters[0].wtype == VariableType.MONETAIRE
        assert calc_tva.parameters[1].name == "sCodeTVA"
        assert calc_tva.parameters[1].wtype == VariableType.CHAINE
        
        # Vérification des variables locales dans CalculerTVA
        local_vars = [v.name for v in calc_tva.local_variables]
        assert "nTVA" in local_vars
        assert "nTauxTVA" in local_vars
        
        # Vérification des requêtes HFSQL
        assert len(ast.hfsql_queries) >= 10  # Plusieurs requêtes dans le fichier complexe
        
        # Vérification des dépendances extraites
        dependencies = parser.get_dependencies(COMPLEX_SAMPLE)
        expected_deps = ["CalculerTVA", "HExécuteRequêteSQL", "HLitPremier", 
                        "HFenDeHorsRequête", "Erreur", "Info"]
        # Vérifier que certaines dépendances importantes sont présentes
        assert "CalculerTVA" in dependencies
        
    finally:
        import os
        os.unlink(temp_path)