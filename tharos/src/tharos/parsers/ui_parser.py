"""Parser IHM pour les fenêtres WinDev (.wdw) → structure React cible.

Extraction déterministe (regex, sans LLM) des composants visuels :
    SAI_xxx  → champ de saisie      → Input React
    BTN_xxx  → bouton               → Button + onClick
    TABLE_xxx→ grille / table       → Table shadcn/ui
    LIB_xxx  → libellé              → Label / Typography
    INT_xxx  → interrupteur         → Checkbox
    SEL_/COMBO_/CBO_ → sélecteur    → Select

Événements détectés : procédures suffixées (_Clic, _Init, _Sortie…).
"""

import re
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from tharos.parsers.windev import WinDevParser, _resolve_wtype
from tharos.parsers.base import VariableType


class UIControlType(str, Enum):
    INPUT = "input"
    BUTTON = "button"
    TABLE = "table"
    LABEL = "label"
    CHECKBOX = "checkbox"
    SELECT = "select"


# Préfixes WinDev → type de contrôle React
PREFIX_TO_TYPE: dict[str, UIControlType] = {
    "SAI": UIControlType.INPUT,
    "BTN": UIControlType.BUTTON,
    "TABLE": UIControlType.TABLE,
    "LIB": UIControlType.LABEL,
    "LIBELLE": UIControlType.LABEL,
    "INT": UIControlType.CHECKBOX,
    "SEL": UIControlType.SELECT,
    "COMBO": UIControlType.SELECT,
    "CBO": UIControlType.SELECT,
}

_PREFIX_ALT = "|".join(PREFIX_TO_TYPE)

RE_CONTROL_DECL = re.compile(
    rf"^(?P<name>(?:{_PREFIX_ALT})_[A-Za-z0-9_]+)"
    r"(?:\s+est\s+(?:une?|un)?\s*(?P<wtype>[A-Za-zÀ-ÿ]+))?",
)

RE_CONTROL_ASSIGN = re.compile(
    rf"^(?P<name>(?:{_PREFIX_ALT})_[A-Za-z0-9_]+)\s*=\s*(?P<value>.+?)\s*$"
)

RE_CAPTION = re.compile(
    r"^(?P<name>[A-Za-z0-9_]+)\.\.(?:Libellé|libelle|Libelle|Caption|caption)"
    r'\s*=\s*"(?P<caption>[^"]*)"'
)

RE_COLUMN = re.compile(
    r"^(?P<table>TABLE_[A-Za-z0-9_]+)\.\.Colonne\[(?P<idx>\d+)\]"
    r'\s*=\s*"(?P<label>[^"]*)"'
)

RE_TITLE = re.compile(
    r'^\s*[A-Za-z0-9_]+\.\.(?:Titre|titre)\s*=\s*"(?P<title>[^"]*)"'
)

RE_EVENT_PROC = re.compile(
    r"^PROCEDURE\s+(?P<control>[A-Za-z0-9_]+?)_"
    r"(?P<event>clic|init|sortie|entr[ée]e|s[ée]lection|selection|fininitialisation"
    r"|d[ée]butinitialisation)\b",
    re.IGNORECASE,
)


class ASTUIControl(BaseModel):
    name: str
    control_type: UIControlType
    label: str | None = None
    wtype: VariableType | None = None
    default_value: str | None = None
    columns: list[str] = Field(default_factory=list)
    line: int = 0


class ASTUIEvent(BaseModel):
    event_name: str            # clic, init, sortie…
    control_name: str          # contrôle ciblé (BTN_Valider…)
    procedure_name: str        # nom complet de la PROCEDURE
    body_lines: list[str] = Field(default_factory=list)


class ASTWindow(BaseModel):
    filename: str
    title: str | None = None
    controls: list[ASTUIControl] = Field(default_factory=list)
    events: list[ASTUIEvent] = Field(default_factory=list)
    total_lines: int = 0

    def control(self, name: str) -> ASTUIControl | None:
        return next((c for c in self.controls if c.name == name), None)


def _infer_type(value: str) -> VariableType | None:
    v = value.strip()
    if not v:
        return None
    if (v.startswith('"') and v.endswith('"')) or (
        v.startswith("'") and v.endswith("'")
    ):
        return VariableType.CHAINE
    low = v.lower()
    if low in {"vrai", "faux", "true", "false"}:
        return VariableType.BOOLEEN
    if re.fullmatch(r"-?\d+", v):
        return VariableType.ENTIER
    if re.fullmatch(r"-?\d+[.,]\d+", v):
        return VariableType.REEL
    return None


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in {'"', "'"}:
        return v[1:-1]
    return v


class UIParser:
    """Parse une fenêtre WLanguage et retourne un ASTWindow structuré."""

    def __init__(self) -> None:
        self._proc_parser = WinDevParser()

    # ── API publique ──────────────────────────────────────────────────────

    def parse_file(self, filepath: Path) -> ASTWindow:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        return self.parse_content(content, filename=filepath.name)

    def parse_content(self, content: str, filename: str = "fenetre.wdw") -> ASTWindow:
        lines = content.split("\n")

        title = self._extract_title(lines)
        controls = self._extract_controls(lines)
        self._apply_captions(lines, controls)
        self._apply_columns(lines, controls)
        events = self._extract_events(content)

        return ASTWindow(
            filename=filename,
            title=title,
            controls=controls,
            events=events,
            total_lines=len(lines),
        )

    # ── Sous-extractions ──────────────────────────────────────────────────

    @staticmethod
    def _extract_title(lines: list[str]) -> str | None:
        for line in lines:
            m = RE_TITLE.match(line)
            if m:
                return m.group("title")
        return None

    @staticmethod
    def _prefix_of(name: str) -> str:
        return name.split("_", 1)[0].upper()

    def _extract_controls(self, lines: list[str]) -> list[ASTUIControl]:
        controls: dict[str, ASTUIControl] = {}

        for i, raw in enumerate(lines):
            line = raw.strip()
            if not line or line.startswith("//"):
                continue

            decl = RE_CONTROL_DECL.match(line)
            name = decl.group("name") if decl else None
            if name is None:
                assign = RE_CONTROL_ASSIGN.match(line)
                if assign:
                    name = assign.group("name")
                    value = assign.group("value")
                    ctrl = controls.get(name)
                    if ctrl is None:
                        ctrl = ASTUIControl(
                            name=name,
                            control_type=PREFIX_TO_TYPE[self._prefix_of(name)],
                            default_value=_strip_quotes(value),
                            wtype=_infer_type(value),
                            line=i + 1,
                        )
                        controls[name] = ctrl
                    elif ctrl.default_value is None:
                        ctrl.default_value = _strip_quotes(value)
                        if ctrl.wtype is None:
                            ctrl.wtype = _infer_type(value)
                continue

            prefix = self._prefix_of(name)
            ctype = PREFIX_TO_TYPE[prefix]
            wtype_raw = decl.group("wtype")

            existing = controls.get(name)
            if existing is not None:
                if wtype_raw and existing.wtype is None:
                    existing.wtype = _resolve_wtype(wtype_raw)
                continue

            ctrl = ASTUIControl(
                name=name,
                control_type=ctype,
                wtype=_resolve_wtype(wtype_raw) if wtype_raw else None,
                line=i + 1,
            )
            # Libellé implicite depuis le nom : BTN_Valider → "Valider"
            suffix = name.split("_", 1)[1]
            ctrl.label = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", suffix).strip()
            controls[name] = ctrl

        return sorted(controls.values(), key=lambda c: (c.line, c.name))

    @staticmethod
    def _apply_captions(lines: list[str], controls: list[ASTUIControl]) -> None:
        by_name = {c.name: c for c in controls}
        for raw in lines:
            m = RE_CAPTION.match(raw.strip())
            if m and m.group("name") in by_name:
                by_name[m.group("name")].label = m.group("caption").strip()

    @staticmethod
    def _apply_columns(lines: list[str], controls: list[ASTUIControl]) -> None:
        by_name = {c.name: c for c in controls}
        collected: dict[str, dict[int, str]] = {}
        for raw in lines:
            m = RE_COLUMN.match(raw.strip())
            if m and m.group("table") in by_name:
                collected.setdefault(m.group("table"), {})[int(m.group("idx"))] = m.group(
                    "label"
                ).strip()
        for table, cols in collected.items():
            by_name[table].columns = [cols[k] for k in sorted(cols)]

    def _extract_events(self, content: str) -> list[ASTUIEvent]:
        events: list[ASTUIEvent] = []
        for proc in self._proc_parser.extract_functions(content):
            m = RE_EVENT_PROC.match(f"PROCEDURE {proc.name}")
            if not m:
                continue
            events.append(
                ASTUIEvent(
                    event_name=m.group("event").lower(),
                    control_name=m.group("control"),
                    procedure_name=proc.name,
                    body_lines=list(proc.body_lines),
                )
            )
        return events
