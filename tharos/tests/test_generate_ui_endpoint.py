"""Test d'intégration de l'endpoint POST /api/v1/generate-ui (v0.4)."""

from pathlib import Path

from fastapi.testclient import TestClient

from tharos.api.main import app

SAMPLES = Path(__file__).parent / "samples"

client = TestClient(app)


def test_generate_ui_endpoint_roundtrip():
    content = (SAMPLES / "fen_facturation.wdw").read_text(encoding="utf-8")

    res = client.post(
        "/api/v1/generate-ui",
        json={"filename": "fen_facturation.wdw", "content": content},
    )

    assert res.status_code == 200, res.text
    data = res.json()

    assert data["success"] is True
    assert data["component_name"] == "FenFacturation"
    assert "useState" in data["tsx_code"]
    assert "<Button" in data["tsx_code"]

    structure = data["ui_structure"]
    names = [c["name"] for c in structure["controls"]]
    for expected in (
        "SAI_NumClient",
        "BTN_Enregistrer",
        "TABLE_Lignes",
        "LIB_TitreEnTete",
    ):
        assert expected in names

    assert any(e["event_name"] == "clic" for e in structure["events"])


def test_generate_ui_endpoint_unknown_content_still_succeeds():
    """Contenu vide → composant minimal, pas de crash 500."""
    res = client.post(
        "/api/v1/generate-ui",
        json={"filename": "vide.wdw", "content": "// rien"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "export default function" in data["tsx_code"]
