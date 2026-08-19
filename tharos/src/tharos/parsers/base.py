"""Classe abstraite pour les parsers AST."""

from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field


class VariableType(str, Enum):
    CHAINE = "chaine"
    ENTIER = "entier"
    REEL = "reel"
    MONETAIRE = "monetaire"
    DATE = "date"
    BOOLEEN = "booleen"
    COMPLEXE = "complexe"


class HFSQLQueryType(str, Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class ASTVariable(BaseModel):
    name: str
    wtype: VariableType
    is_global: bool = True
    line: int = 0


class ASTParameter(BaseModel):
    name: str
    wtype: VariableType


class ASTHFSQLQuery(BaseModel):
    query_type: HFSQLQueryType
    target_table: str
    raw_sql: str
    line: int = 0


class ASTCondition(BaseModel):
    condition_type: str  # SI, SINON SI, SINON
    expression: str
    line: int = 0


class ASTProcedure(BaseModel):
    name: str
    parameters: list[ASTParameter] = Field(default_factory=list)
    local_variables: list[ASTVariable] = Field(default_factory=list)
    body_lines: list[str] = Field(default_factory=list)
    return_value: str | None = None
    start_line: int = 0
    end_line: int = 0


class ASTModel(BaseModel):
    filename: str
    global_variables: list[ASTVariable] = Field(default_factory=list)
    procedures: list[ASTProcedure] = Field(default_factory=list)
    hfsql_queries: list[ASTHFSQLQuery] = Field(default_factory=list)
    conditions: list[ASTCondition] = Field(default_factory=list)
    total_lines: int = 0


class BaseParser(ABC):
    """Interface standard pour les parsers AST."""

    @abstractmethod
    def parse_file(self, filepath: Path) -> ASTModel:
        """Parse un fichier source et retourne un AST structuré."""

    @abstractmethod
    def extract_functions(self, content: str) -> list[ASTProcedure]:
        """Extrait les procédures/fonctions du contenu source."""

    @abstractmethod
    def extract_queries(self, content: str) -> list[ASTHFSQLQuery]:
        """Extrait les requêtes HFSQL du contenu source."""

    @abstractmethod
    def extract_variables(self, content: str) -> list[ASTVariable]:
        """Extrait les déclarations de variables du contenu source."""
