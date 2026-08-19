"""Modèles Pydantic pour les requêtes/réponses API."""

from enum import Enum

from pydantic import BaseModel, Field


# ── Detect ───────────────────────────────────────────────────────────────────


class DetectRequest(BaseModel):
    filename: str = Field(..., description="Nom du fichier source")
    content: str = Field(default="", description="Contenu du fichier (optionnel)")


class DetectedLanguage(str, Enum):
    WINDEV = "windev"
    UNKNOWN = "unknown"


class DetectResponse(BaseModel):
    filename: str
    detected_language: DetectedLanguage
    confidence: float = Field(ge=0.0, le=1.0)
    matched_patterns: list[str] = Field(default_factory=list)


# ── Transpile ────────────────────────────────────────────────────────────────


class TranspileRequest(BaseModel):
    filename: str = Field(..., description="Nom du fichier WinDev")
    content: str = Field(..., description="Contenu du fichier WinDev")
    procedure: str = Field(..., description="Nom de la procédure à transpiler")
    max_attempts: int = Field(default=3, ge=1, le=10)


class TranspileResponse(BaseModel):
    success: bool
    procedure: str
    generated_code: str
    test_code: str
    attempts: int
    history: list["AttemptInfo"] = Field(default_factory=list)
    error: str | None = None


class AttemptInfo(BaseModel):
    attempt: int
    passed: bool
    exit_code: int
    logs: str = ""
