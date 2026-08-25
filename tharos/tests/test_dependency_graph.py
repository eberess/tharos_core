"""Tests pour le moteur de dépendances."""

import pytest
from pathlib import Path
from tharos.graph.dependency_analyzer import DependencyAnalyzer
from tharos.graph.graph_builder import GraphBuilder


def test_dependency_analysis():
    """Teste l'analyse des dépendances."""
    
    # Créer un contenu de test avec dépendances
    content = """
PROCEDURE Proc1()
    // Appel d'une autre procédure
    Proc2()
END

PROCEDURE Proc2()
    // Une autre procédure
    Resultat = 0
END

PROCEDURE Proc3()
    // Appel à une procédure dans un fichier différent (non implémenté ici)
    Proc1()
END
"""
    
    # Créer temporairement un fichier de test
    test_file = Path("/tmp/test_dep.wdw")
    test_file.write_text(content, encoding="utf-8")
    
    try:
        # Analyser les dépendances
        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_file_dependencies(test_file)
        
        # Vérifier que les dépendances sont détectées
        assert len(dependencies) >= 1

        # Vérifier qu'on a au moins un appel vers Proc2
        proc2_calls = [dep for dep in dependencies if dep["name"] == "Proc2"]
        assert len(proc2_calls) >= 1
        
    finally:
        # Nettoyer
        test_file.unlink(missing_ok=True)


def test_graph_building():
    """Teste la construction du graphe de dépendance."""
    
    # Créer plusieurs fichiers de test
    file1 = Path("/tmp/file1.wdw")
    file2 = Path("/tmp/file2.wdw")
    
    content1 = """
PROCEDURE ProcA()
    ProcB()
END
"""
    
    content2 = """
PROCEDURE ProcB()
    // Une autre procédure
    Resultat = 0
END
"""
    
    file1.write_text(content1, encoding="utf-8")  
    file2.write_text(content2, encoding="utf-8")
    
    try:
        # Construire le graphe
        graph_builder = GraphBuilder()
        files = [str(file1), str(file2)]
        graph = graph_builder.build_dependency_graph(files)
        
        # Vérifier que le graphe contient les nœuds
        assert len(graph.nodes()) == 2
        
        # Vérifier la structure de dépendance
        transpilation_order = graph_builder.get_transpilation_order(files)
        assert len(transpilation_order) == 2
        
    finally:
        # Nettoyer
        file1.unlink(missing_ok=True)
        file2.unlink(missing_ok=True)


def test_transpilation_order():
    """Teste l'ordre de transpilation."""
    
    # Créer fichier avec dépendances circulaires
    file1 = Path("/tmp/order1.wdw")
    file2 = Path("/tmp/order2.wdw")
    
    content1 = """
PROCEDURE ProcA()
    ProcB()
END
"""
    
    content2 = """
PROCEDURE ProcB()
    ProcA()
END
"""
    
    file1.write_text(content1, encoding="utf-8")  
    file2.write_text(content2, encoding="utf-8")
    
    try:
        analyzer = DependencyAnalyzer()
        files = [str(file1), str(file2)]
        
        # Ce cas devrait fonctionner sans erreur
        graph_builder = GraphBuilder()
        order = graph_builder.get_transpilation_order(files)
        assert len(order) == 2
        
    finally:
        # Nettoyer
        file1.unlink(missing_ok=True)
        file2.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])