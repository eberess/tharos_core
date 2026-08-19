"""Routes API — detect et transpile."""

import re
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException

from tharos.api.schemas import (
    DetectRequest,
    DetectResponse,
    DetectedLanguage,
    TranspileRequest,
    TranspileResponse,
    AttemptInfo,
)

router = APIRouter()

# ── Patterns de détection WLanguage ──────────────────────────────────────────

_WLANGUAGE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("PROCEDURE", re.compile(r"^\s*PROCEDURE\s+", re.MULTILINE)),
    ("RENVOYER", re.compile(r"\bRENVOYER\b", re.MULTILINE)),
    ("POUR TOUT", re.compile(r"\bPOUR\s+TOUT\b", re.MULTILINE)),
    ("HExécuteRequêteSQL", re.compile(r"\bHExécuteRequêteSQL\b", re.MULTILINE)),
    ("HLitPremier", re.compile(r"\bHLitPremier\b", re.MULTILINE)),
    ("SI ... ALORS", re.compile(r"\bSI\b.*\bALORS\b", re.MULTILINE)),
    ("SINON", re.compile(r"\bSINON\b", re.MULTILINE)),
    ("est un/une", re.compile(r"\w+\s+est\s+(?:une?|un)\s+\w+", re.MULTILINE)),
    ("HFenDeHorsRequête", re.compile(r"\bHFenDeHorsRequête\b", re.MULTILINE)),
]

_WINDEV_EXTENSIONS = {".wdw", ".wdg", ".wda", ".wwd"}


def _detect_language(filename: str, content: str) -> tuple[DetectedLanguage, float, list[str]]:
    """Détecte le langage source par extension et regex."""
    ext = Path(filename).suffix.lower()
    matched: list[str] = []

    if ext in _WINDEV_EXTENSIONS:
        for label, pattern in _WLANGUAGE_PATTERNS:
            if pattern.search(content):
                matched.append(label)
        confidence = min(0.5 + 0.05 * len(matched), 1.0) if matched else 0.5
        return DetectedLanguage.WINDEV, confidence, matched

    for label, pattern in _WLANGUAGE_PATTERNS:
        if pattern.search(content):
            matched.append(label)

    if len(matched) >= 2:
        confidence = min(0.3 + 0.08 * len(matched), 1.0)
        return DetectedLanguage.WINDEV, confidence, matched

    return DetectedLanguage.UNKNOWN, 0.0, matched


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/detect", response_model=DetectResponse)
async def detect_language(req: DetectRequest) -> DetectResponse:
    language, confidence, patterns = _detect_language(req.filename, req.content)
    return DetectResponse(
        filename=req.filename,
        detected_language=language,
        confidence=confidence,
        matched_patterns=patterns,
    )


@router.post("/transpile", response_model=TranspileResponse)
async def transpile_code(req: TranspileRequest) -> TranspileResponse:
    from tharos.agents.translator import translate_with_retry
    from tharos.parsers.windev import WinDevParser

    tmp_dir = Path(tempfile.mkdtemp(prefix="tharos_api_"))
    tmp_file = tmp_dir / req.filename

    try:
        tmp_file.write_text(req.content, encoding="utf-8")

        parser = WinDevParser()
        ast = parser.parse_file(tmp_file)

        proc = next((p for p in ast.procedures if p.name == req.procedure), None)
        if proc is None:
            available = [p.name for p in ast.procedures]
            raise HTTPException(
                status_code=404,
                detail=f"Procédure '{req.procedure}' introuvable. Disponibles : {', '.join(available)}",
            )

        result = translate_with_retry(proc, ast, max_attempts=req.max_attempts)

        return TranspileResponse(
            success=result.success,
            procedure=req.procedure,
            generated_code=result.final_code,
            test_code=result.test_code,
            attempts=result.attempts,
            history=[
                AttemptInfo(
                    attempt=h.attempt,
                    passed=h.passed,
                    exit_code=h.exit_code,
                    logs=h.logs,
                )
                for h in result.history
            ],
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
