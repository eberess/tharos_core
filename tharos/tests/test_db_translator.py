"""Tests pour le traducteur HFSQL vers SQLAlchemy."""

import pytest
from tharos.agents.db_translator import HFSQLToSQLAlchemyTranslator
from tharos.parsers.windev import WinDevParser


def test_hfsql_to_sqlalchemy_translation():
    """Test la traduction des requêtes HFSQL vers SQLAlchemy."""
    
    # Créer un traducteur
    translator = HFSQLToSQLAlchemyTranslator()
    
    # Contenu avec diverses requêtes HFSQL
    content = """
PROCEDURE TestProcedure()
    // Ajout d'un enregistrement
    HAjoute(Commandes)
    
    // Modification d'un enregistrement
    HModifie(Commandes)
    
    // Lecture en premier
    Resultat = HLitPremier("SELECT * FROM Commandes WHERE ID = ?")
    
    // Recherche premier
    Client = HLitRecherchePremier("SELECT ClientID FROM LignesCommande WHERE ArticleID = ?", "A001")
    
    // Exécution de requête SQL
    HExécuteRequêteSQL("SELECT SUM(Montant) FROM Commandes WHERE ClientID = ?", "C001")
END
"""
    
    # Analyser le contenu
    parser = WinDevParser()
    ast = parser.parse_content(content, "test.wdw")
    assert len(ast.procedures) >= 1

    # Traduire les requêtes
    translations = translator.translate_file_queries(content, "test.wdw")
    
    # Vérifier qu'on a bien traduit toutes les requêtes HFSQL
    assert len(translations) > 0
    
    # Examiner quelques traductions spécifiques
    for original_query, result in translations.items():
        assert result.translated_code is not None
        assert result.original_query == original_query
    

def test_specific_translations():
    """Teste des traductions spécifiques."""
    
    translator = HFSQLToSQLAlchemyTranslator()
    
    # Test HAjoute
    content_add = """
PROCEDURE TestAdd()
    HAjoute(Produits)
END
"""
    
    # Test HModifie 
    content_modify = """
PROCEDURE TestModify()
    HModifie(Produits)
END
"""
    
    # Vérifier que les types de requêtes sont bien traduits
    translations_add = translator.translate_file_queries(content_add, "test_add.wdw")
    translations_modify = translator.translate_file_queries(content_modify, "test_modify.wdw")
    
    assert len(translations_add) == 1
    assert len(translations_modify) == 1


def test_select_query_translation():
    """Teste la traduction de requêtes SELECT."""
    
    translator = HFSQLToSQLAlchemyTranslator()
    
    content = """
PROCEDURE TestSelect()
    Resultat = HExécuteRequêteSQL("SELECT * FROM Articles WHERE Prix > ?", 100)
END
"""
    
    translations = translator.translate_file_queries(content, "test_select.wdw")
    assert len(translations) >= 1
    
    # Vérifier que des requêtes SELECT sont bien traitées
    for original_query, result in translations.items():
        if "SELECT" in original_query.upper():
            # La traduction devrait contenir une requête SQLAlchemy
            assert "session.execute" in result.translated_code or "select(" in result.translated_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])