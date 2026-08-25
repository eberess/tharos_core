"""Tests du générateur React/TSX (v0.4)."""

import re
from pathlib import Path

from tharos.agents.react_generator import ReactComponentGenerator
from tharos.parsers.ui_parser import UIParser

SAMPLES = Path(__file__).parent / "samples"


def _generate():
    window = UIParser().parse_file(SAMPLES / "fen_facturation.wdw")
    return ReactComponentGenerator().generate(window)


def test_generation_success_and_naming():
    result = _generate()
    assert result.success, result.error
    assert result.component_name == "FenFacturation"


def test_tsx_contains_state_and_types():
    result = _generate()
    tsx = result.tsx_code
    assert '"use client";' in tsx
    assert "export interface FenFacturationForm {" in tsx
    # SAI_MontantHT est un monétaire → number
    assert re.search(r"saiMontantHT:\s*number;", tsx)
    # INT_AcomptePaye est un booléen → boolean
    assert re.search(r"intAcomptePaye:\s*boolean;", tsx)
    assert "useState<FenFacturationForm>" in tsx


def test_buttons_wired_with_handlers():
    result = _generate()
    tsx = result.tsx_code
    assert "async function handleBtnEnregistrerClic()" in tsx
    assert 'type="submit"' in tsx  # premier bouton clic → submit du form
    assert "<Button" in tsx


def test_shadcn_table_markup():
    result = _generate()
    tsx = result.tsx_code
    assert '<TableHead>Référence</TableHead>' in tsx
    assert "<TableBody>" in tsx
    assert "Aucune ligne" in tsx


def test_hfsql_calls_mapped_to_fastapi():
    result = _generate()
    tsx = result.tsx_code
    # HAjoute(Factures) → POST /api/factures avec formData
    assert 'fetch("/api/factures", { method: "POST"' in tsx
    assert "JSON.stringify(formData)" in tsx
    # HLitRecherchePremier non traduisible déterministement → TODO explicite
    assert any("TODO" in w for w in result.warnings) or "TODO WLanguage" in tsx


def test_ferme_maps_to_onclose_prop():
    result = _generate()
    tsx = result.tsx_code
    assert "onClose?: () => void;" in tsx
    assert "onClose?.();" in tsx


def test_component_name_override_and_sanitization():
    content = (SAMPLES / "fen_facturation.wdw").read_text(encoding="utf-8")
    window = UIParser().parse_content(content, filename="fen_facturation.wdw")
    res = ReactComponentGenerator().generate(window, component_name="ma fenetre-test")
    assert res.component_name == "MaFenetreTest"
