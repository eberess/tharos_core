"""Construit le graphe de dépendance entre fichiers WinDev."""

import networkx as nx
from collections import deque
from pathlib import Path
from typing import List, Set, Dict, Optional

from tharos.graph.dependency_analyzer import DependencyAnalyzer


class GraphBuilder:
    """Construit et manipule un graphe de dépendances entre fichiers."""
    
    def __init__(self):
        self.graph = nx.DiGraph()  # Graphe orienté
        self.dependencies: Dict[str, Set[str]] = {}
        
    def build_dependency_graph(self, file_paths: List[str]) -> nx.DiGraph:
        """
        Construit un graphe de dépendances à partir d'une liste de fichiers.
        
        Args:
            file_paths (List[str]): Liste des chemins des fichiers
            
        Returns:
            nx.DiGraph: Le graphe des dépendances
        """
        # Initialiser le graphe avec les nœuds
        for file_path in file_paths:
            self.graph.add_node(file_path)
            
        # Analyser les dépendances entre fichiers
        analyzer = DependencyAnalyzer()
        
        for file_path in file_paths:
            try:
                file_node = Path(file_path)
                if not file_node.exists():
                    continue
                    
                dependencies = analyzer.analyze_file_dependencies(file_node)
                
                # Ajouter des arcs au graphe pour chaque dépendance
                for dep in dependencies:
                    dep_name = dep["name"]
                    # Rechercher si cette dépendance est dans notre projet
                    for other_file in file_paths:
                        if other_file != file_path and self._contains_procedure(other_file, dep_name):
                            self.graph.add_edge(file_path, other_file)
                            
            except Exception as e:
                print(f"Erreur lors de la construction du graphe pour {file_path}: {e}")
                
        self.dependencies = analyzer.analyze_project_dependencies([Path(p) for p in file_paths])
        return self.graph
    
    def _contains_procedure(self, file_path: str, proc_name: str) -> bool:
        """
        Vérifie si un fichier contient une déclaration de procédure.
        
        Args:
            file_path (str): Chemin du fichier
            proc_name (str): Nom de la procédure
            
        Returns:
            bool: True si la procédure est déclarée dans le fichier
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Rechercher une déclaration de procédure du type "PROCEDURE NomProc()"
                pattern = rf'PROCEDURE\s+{proc_name}\s*\('
                return bool(re.search(pattern, content, re.IGNORECASE))
        except Exception:
            return False
    
    def get_transpilation_order(self, file_paths: List[str]) -> List[str]:
        """
        Retourne l'ordre de transpilation topologique.
        
        Args:
            file_paths (List[str]): Liste des fichiers
            
        Returns:
            List[str]: Ordre de transpilation
        """
        self.build_dependency_graph(file_paths)
        
        try:
            # Calculer l'ordre topologique
            topo_order = list(nx.topological_sort(self.graph))
            return topo_order
        except nx.NetworkXError:
            # Si le graphe a des cycles, effectuer un tri différent
            return file_paths
    
    def get_dependencies(self, file_path: str) -> List[str]:
        """
        Retourne les dépendances directes d'un fichier.
        
        Args:
            file_path (str): Fichier pour lequel récupérer les dépendances
            
        Returns:
            List[str]: Liste des dépendances
        """
        if file_path in self.dependencies:
            return list(self.dependencies[file_path])
        return []
    
    def has_cycle(self) -> bool:
        """
        Vérifie si le graphe contient des cycles.
        
        Returns:
            bool: True si un cycle est détecté
        """
        try:
            list(nx.simple_cycles(self.graph))
            return True
        except:
            return False
    
    def print_graph_info(self):
        """Affiche les informations du graphe."""
        print(f"Graphe de dépendances avec {self.graph.number_of_nodes()} nœuds")
        print(f"{self.graph.number_of_edges()} arcs")
        
        if self.has_cycle():
            print("⚠️  Cycle détecté dans le graphe")


def create_sample_dependency_graph(file_paths: List[str]) -> nx.DiGraph:
    """
    Fonction utilitaire pour créer un graphe de dépendance simple.
    
    Args:
        file_paths (List[str]): Liste des chemins des fichiers
        
    Returns:
        nx.DiGraph: Graphe des dépendances
    """
    builder = GraphBuilder()
    return builder.build_dependency_graph(file_paths)