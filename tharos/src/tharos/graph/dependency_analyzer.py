"""Analyseur de dépendances entre fichiers WinDev."""

import re
from pathlib import Path
from typing import List, Set, Dict, Tuple
from collections import defaultdict


class DependencyAnalyzer:
    """Analyse les dépendances entre fichiers WinDev."""
    
    def __init__(self):
        self.file_dependencies: Dict[str, Set[str]] = defaultdict(set)
    
    def analyze_file_dependencies(self, file_path: Path) -> List[Dict]:
        """
        Analyse les dépendances d'un fichier WinDev en cherchant les appels de procédures.
        
        Args:
            file_path (Path): Chemin du fichier à analyser
            
        Returns:
            List[Dict]: Liste des dépendances trouvées
        """
        dependencies = []
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Rechercher les appels de procédures
            # Pattern pour trouver des appels de procédures : PROCEDURE Nom() 
            procedure_calls = re.findall(
                r'\b([A-Z][a-zA-Z0-9_]*)\s*\(', content, re.MULTILINE
            )
            
            for call in procedure_calls:
                # Ignore les mots-clés internes et les fonctions système
                if not self._is_internal_function(call):
                    dependencies.append({
                        "type": "procedure_call",
                        "name": call,
                        "file": str(file_path)
                    })
            
            return dependencies
            
        except Exception as e:
            print(f"Erreur lors de l'analyse des dépendances : {e}")
            return []
    
    def _is_internal_function(self, name: str) -> bool:
        """Détermine si une fonction est interne au système."""
        internal_functions = {
            "HAjoute", "HModifie", "HLitPremier", "HLitRecherchePremier",
            "HExécuteRequêteSQL", "SELECT", "INSERT", "UPDATE", "DELETE"
        }
        return name in internal_functions
    
    def analyze_project_dependencies(self, project_files: List[Path]) -> Dict:
        """
        Analyse l'ensemble des dépendances du projet.
        
        Args:
            project_files (List[Path]): Liste des fichiers du projet
            
        Returns:
            Dict: Dictionnaire des dépendances pour chaque fichier
        """
        all_dependencies = {}
        for file_path in project_files:
            dependencies = self.analyze_file_dependencies(file_path)
            all_dependencies[str(file_path)] = dependencies
        
        return all_dependencies


# Fonction utilitaire pour l'analyse de dépendance
def find_cross_file_calls(content: str) -> List[str]:
    """
    Trouve les appels de procédures entre fichiers.
    
    Args:
        content (str): Contenu d'un fichier
        
    Returns:
        List[str]: Liste des noms de procédures appelées
    """
    # Recherche les appels potentiels de fonctions ou procédures
    pattern = r'\b([A-Z][a-zA-Z0-9_]*)\s*\([^)]*\)'
    matches = re.findall(pattern, content)
    
    # Filtrer les appels internes du système
    internal_calls = {"HAjoute", "HModifie", "HLitPremier", 
                      "HLitRecherchePremier", "HExécuteRequêteSQL"}
    
    return [match for match in matches if match not in internal_calls]