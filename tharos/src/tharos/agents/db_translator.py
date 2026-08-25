"""Traducteur de requêtes HFSQL vers SQLAlchemy 2.0."""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TranslationResult:
    """Résultat de la traduction d'une requête."""
    original_query: str
    translated_code: str
    query_type: str  # 'insert', 'update', 'select', 'delete', etc.
    table_name: Optional[str] = None


class HFSQLToSQLAlchemyTranslator:
    """Traducteur de requêtes HFSQL vers SQLAlchemy 2.0."""
    
    def __init__(self):
        self.query_translations: Dict[str, str] = {}
        
    def translate_file_queries(self, file_content: str, file_name: str) -> Dict[str, TranslationResult]:
        """
        Traduit toutes les requêtes HFSQL dans un fichier.
        
        Args:
            file_content (str): Contenu du fichier WinDev
            file_name (str): Nom du fichier
            
        Returns:
            Dict[str, TranslationResult]: Dictionnaire des traductions
        """
        translations = {}
        
        # Rechercher les requêtes HFSQL
        queries = self._extract_hfsql_queries(file_content)
        
        for query in queries:
            result = self.translate_query(query)
            if result:
                translations[query] = result
                
        return translations
    
    def _extract_hfsql_queries(self, content: str) -> List[str]:
        """Extrait toutes les requêtes HFSQL du contenu."""
        queries = []
        
        # Rechercher les appels des fonctions HFSQL
        patterns = [
            r'HAjoute\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)',
            r'HModifie\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', 
            r'HLitPremier\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'HLitRecherchePremier\s*\(\s*["\']([^"\']+)["\']\s*,.*?\)',
            r'HExécuteRequêteSQL\s*\(\s*["\']([^"\']+)["\']\s*(?:,.*?)*\)'
        ]
        
        # Extraire toutes les requêtes
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                # Pour chaque pattern, on récupère l'expression complète
                for match in re.finditer(pattern, content):
                    queries.append(match.group(0))
        
        # Rechercher aussi les requêtes SELECT dans les HExécuteRequêteSQL
        select_matches = re.findall(
            r'HExécuteRequêteSQL\s*\(\s*["\']\s*(SELECT[^"\']*)\s*["\']', 
            content, 
            re.IGNORECASE | re.MULTILINE
        )
        
        for match in select_matches:
            if "SELECT" in match.upper():
                queries.append(f"HExécuteRequêteSQL(\"{match}\")")
            
        return list(set(queries))  # Supprimer les doublons
    
    def translate_query(self, query: str) -> Optional[TranslationResult]:
        """
        Traduit une requête HFSQL individuelle.
        
        Args:
            query (str): Requête HFSQL
            
        Returns:
            Optional[TranslationResult]: Résultat de la traduction
        """
        if not query.strip():
            return None
            
        # Déterminer le type de requête
        query_type = self._determine_query_type(query)
        
        # Traduire selon le type
        translated = self._translate_query_by_type(query, query_type)
        
        if translated:
            return TranslationResult(
                original_query=query,
                translated_code=translated,
                query_type=query_type,
                table_name=self._extract_table_name(query)
            )
        
        return None

    def _determine_query_type(self, query: str) -> str:
        """Détermine le type de requête."""
        if "HAjoute" in query:
            return "insert"
        elif "HModifie" in query:
            return "update" 
        elif "HLitPremier" in query:
            return "select"
        elif "HLitRecherchePremier" in query:
            return "select"
        elif "HExécuteRequêteSQL" in query and "SELECT" in query.upper():
            return "select"
        elif "HExécuteRequêteSQL" in query and ("INSERT" in query.upper() or 
                                                "UPDATE" in query.upper() or 
                                                "DELETE" in query.upper()):
            return "execute"
        else:
            return "unknown"

    def _translate_query_by_type(self, query: str, query_type: str) -> str:
        """Traduit une requête selon son type."""
        if query_type == "insert":
            return self._translate_insert(query)
        elif query_type == "update":
            return self._translate_update(query)
        elif query_type == "select":
            return self._translate_select(query)
        elif query_type == "execute":
            return self._translate_execute_query(query)
        else:
            return f"# Translation not implemented for: {query}"

    def _translate_insert(self, query: str) -> str:
        """Traduit une requête HAjoute."""
        table_match = re.search(r'HAjoute\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', query)
        if table_match:
            table_name = table_match.group(1)
            return f"session.add({table_name}())"
        return "# Insert translation failed"

    def _translate_update(self, query: str) -> str:
        """Traduit une requête HModifie."""  
        return "session.commit()"

    def _translate_select(self, query: str) -> str:
        """Traduit une requête de sélection."""
        if "HExécuteRequêteSQL" in query and ("SELECT" in query.upper()):
            # Extraire la requête SQL
            sql_match = re.search(r'HExécuteRequêteSQL\s*\(\s*["\']([^"\']+)["\']', query, re.IGNORECASE)
            if sql_match:
                sql_query = sql_match.group(1)
                return f"session.execute(text('{sql_query}'))"
        elif "HLitPremier" in query:
            # Traduire HLitPremier
            sql_match = re.search(r'HLitPremier\s*\(\s*(["\'][^"\']*["\'])', query, re.IGNORECASE)
            if sql_match:
                sql_query = sql_match.group(1)
                return f"session.execute(text({sql_query})).fetchone()"
        elif "HLitRecherchePremier" in query:
            # Traduire HLitRecherchePremier
            sql_match = re.search(r'HLitRecherchePremier\s*\(\s*([^,]+),[^)]+\)', query)
            if sql_match:
                table_name = sql_match.group(1)
                return f"# HLitRecherchePremier translation for {table_name}"
        return "# Select translation failed"

    def _translate_execute_query(self, query: str) -> str:
        """Traduit une requête executée."""
        sql_match = re.search(r'HExécuteRequêteSQL\s*\(\s*["\']([^"\']+)["\']', query, re.IGNORECASE)
        if sql_match:
            sql_text = sql_match.group(1)
            # Générer le code SQLAlchemy pour execution
            return f"session.execute(text('{sql_text}'))"
        return "# Execute translation failed"

    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extrait le nom de la table d'une requête."""
        if "HAjoute" in query:
            table_match = re.search(r'HAjoute\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', query)
            return table_match.group(1) if table_match else None
        elif "HModifie" in query:
            table_match = re.search(r'HModifie\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', query)
            return table_match.group(1) if table_match else None
        return None


# Fonction utilitaire pour traduire un exemple
def translate_example():
    """Fonction d'exemple pour démontrer la traduction."""
    translator = HFSQLToSQLAlchemyTranslator()
    
    # Test d'une requête de type HLitRecherchePremier
    example_query = "HLitRecherchePremier(Client, NumClient, 105)"
    result = translator.translate_query(example_query)
    
    print("Exemple de traduction:")
    if result:
        print(f"Original: {result.original_query}")
        print(f"Traduit:  {result.translated_code}")
        print(f"Type:     {result.query_type}")
    
    return result


if __name__ == "__main__":
    # Exemple d'utilisation
    translate_example()