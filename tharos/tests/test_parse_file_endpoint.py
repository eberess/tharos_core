"""Test pour le nouveau endpoint /parse-file qui analyse les fichiers WinDev complets."""

import pytest
from pathlib import Path

from tharos.parsers.windev import WinDevParser


class TestParseFileEndpoint:
    """Tests du nouveau endpoint d'analyse de fichier."""
    
    def test_parser_extraction(self):
        """Test que le parser extrait correctement les structures complexes."""
        # Utiliser un contenu plus réaliste avec plusieurs procédures
        sample_content = """
// Exemple complexe
sNomClient est une chaîne
nTotalHT est un monétaire

PROCEDURE CalculerTVA(nMontantHT est un monétaire, sCodeTVA est une chaîne) LOCAL
    nTVA est un monétaire
    SI sCodeTVA = "TX20" ALORS
        nTVA = nMontantHT * 0.20
    FIN
    RENVOYER nTVA
END

PROCEDURE ValiderFacture(nNumFacture est un entier) LOCAL
    HExécuteRequêteSQL("SELECT * FROM FACTURE WHERE NUM_FACTURE = " + nNumFacture)
    RENVOYER VRAI
END
        """
        
        parser = WinDevParser()
        deps = parser.get_dependencies(sample_content)
        
        # Le parser détecte les appels de procédures (les fonctions HFSQL
        # natives sont volontairement exclues des dépendances internes).
        assert "CalculerTVA" in deps
        assert "ValiderFacture" in deps
        
        # Parser le fichier complet
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.wdw', delete=False) as f:
            f.write(sample_content)
            temp_path = f.name
            
        try:
            ast = parser.parse_file(Path(temp_path))
            
            assert len(ast.procedures) == 2
            assert len(ast.global_variables) == 2
            
            # Vérifier les procédures extraites
            proc_names = [p.name for p in ast.procedures]
            assert "CalculerTVA" in proc_names
            assert "ValiderFacture" in proc_names
            
        finally:
            os.unlink(temp_path)


def test_parse_file_http_roundtrip():
    """Le endpoint /parse-file accepte un corps JSON {filename, content}."""
    from fastapi.testclient import TestClient
    from tharos.api.main import app

    client = TestClient(app)
    res = client.post(
        "/api/v1/parse-file",
        json={
            "filename": "facture.wdw",
            "content": (
                "sNomClient est une chaîne\n"
                "PROCEDURE CalculerTVA(nMontantHT est un monétaire) LOCAL\n"
                "    RENVOYER nMontantHT * 0.20\n"
            ),
        },
    )

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["filename"] == "facture.wdw"
    assert [p["name"] for p in data["procedures"]] == ["CalculerTVA"]
    assert [v["name"] for v in data["global_variables"]] == ["sNomClient"]