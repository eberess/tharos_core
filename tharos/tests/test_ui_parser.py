"""Tests du parser IHM WinDev (v0.4)."""

from pathlib import Path

from tharos.parsers.ui_parser import UIControlType, UIParser

SAMPLES = Path(__file__).parent / "samples"


def _parse_sample() -> "object":
    return UIParser().parse_file(SAMPLES / "fen_facturation.wdw")


def test_title_extraction():
    window = _parse_sample()
    assert window.title == "Facturation client"


def test_controls_by_prefix():
    window = _parse_sample()
    by_name = {c.name: c for c in window.controls}

    assert by_name["SAI_NumClient"].control_type == UIControlType.INPUT
    assert by_name["BTN_Enregistrer"].control_type == UIControlType.BUTTON
    assert by_name["TABLE_Lignes"].control_type == UIControlType.TABLE
    assert by_name["LIB_TitreEnTete"].control_type == UIControlType.LABEL
    assert by_name["INT_AcomptePaye"].control_type == UIControlType.CHECKBOX
    assert by_name["COMBO_ModePaiement"].control_type == UIControlType.SELECT


def test_captions_applied():
    window = _parse_sample()
    by_name = {c.name: c for c in window.controls}
    assert by_name["BTN_Enregistrer"].label == "Enregistrer la facture"
    assert by_name["TABLE_Lignes"].label == "Lignes de commande"


def test_table_columns_ordered():
    window = _parse_sample()
    table = next(c for c in window.controls if c.name == "TABLE_Lignes")
    assert table.columns == ["Référence", "Désignation", "Quantité", "Prix unitaire"]


def test_events_detected_and_bound_to_controls():
    window = _parse_sample()
    events = {(e.control_name, e.event_name) for e in window.events}

    assert ("BTN_Enregistrer", "clic") in events
    assert ("BTN_Annuler", "clic") in events
    assert ("SAI_NumClient", "init") in events

    clic = next(e for e in window.events if e.control_name == "BTN_Enregistrer")
    assert clic.procedure_name == "BTN_Enregistrer_Clic"
    assert any("HAjoute" in ln for ln in clic.body_lines)


def test_parse_content_matches_parse_file():
    content = (SAMPLES / "fen_facturation.wdw").read_text(encoding="utf-8")
    from_content = UIParser().parse_content(content, filename="fen_facturation.wdw")
    from_file = _parse_sample()
    assert from_content.title == from_file.title
    assert [c.name for c in from_content.controls] == [c.name for c in from_file.controls]
