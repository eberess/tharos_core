"""Agent générateur : fenêtre WinDev (ASTWindow) → composant React/TSX.

Sortie déterministe (template, sans LLM) :
  - TypeScript typé (interface FormData dérivée des champs SAI_/INT_/SEL_)
  - Tailwind CSS + composants shadcn/ui (Button, Input, Label, Table)
  - État React via useState (option react-hook-form prévue en v0.5)
  - Handlers d'événements traduits depuis les PROCEDURE *_Clic/_Init…
  - Connexion automatique aux endpoints FastAPI générés côté backend
    (HAjoute/HModifie → POST/PUT /api/{table}, HExécuteRequêteSQL → POST /api/query)
"""

import re

from pydantic import BaseModel, Field

from tharos.parsers.base import VariableType
from tharos.parsers.ui_parser import ASTUIControl, ASTWindow, UIControlType


class UIGenerationResult(BaseModel):
    success: bool
    component_name: str
    tsx_code: str = ""
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


_TS_TYPE_MAP: dict[VariableType, str] = {
    VariableType.CHAINE: "string",
    VariableType.DATE: "string",
    VariableType.ENTIER: "number",
    VariableType.REEL: "number",
    VariableType.MONETAIRE: "number",
    VariableType.BOOLEEN: "boolean",
    VariableType.COMPLEXE: "string",
}

_RE_HAJOUTE = re.compile(r"\bHAjoute\s*\(\s*(\w+)\s*\)")
_RE_HMODIFIE = re.compile(r"\bHModifie\s*\(\s*(\w+)\s*\)")
_RE_HSUPPRIME = re.compile(r"\bHSupprime\s*\(\s*(\w+)\s*\)")
_RE_HSQL = re.compile(r'HExécuteRequêteSQL\s*\(\s*"([^"]+)"')
_RE_INFO = re.compile(r'\b(?:Info|Message)\s*\(\s*"?([^")]+)"?\s*\)')
_RE_ERREUR = re.compile(r'\bErreur\s*\(\s*"?([^")]+)"?\s*\)')


def _pascal(text: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", text.strip())
    joined = "".join(p.capitalize() for p in parts if p)
    if not joined:
        return "GeneratedWindow"
    if joined[0].isdigit():
        joined = "Win" + joined
    return joined


def _camel(text: str) -> str:
    p = _pascal(text)
    return p[0].lower() + p[1:] if p else p


def _field_key(control_name: str) -> str:
    """SAI_NumClient → saiNumClient ; SAI_MontantHT → saiMontantHT (casse préservée)."""
    parts = [p for p in control_name.split("_") if p]
    head = parts[0].lower()
    tail = "".join(p[0].upper() + p[1:] for p in parts[1:])
    return head + tail


def _handler_name(procedure_name: str) -> str:
    """BTN_Valider_Clic → handleBtnValiderClic"""
    return "handle" + _pascal(procedure_name)


class ReactComponentGenerator:
    """Transforme un ASTWindow en code TSX valide et typé."""

    def generate(
        self, window: ASTWindow, component_name: str | None = None
    ) -> UIGenerationResult:
        warnings: list[str] = []
        try:
            name = self._resolve_component_name(window, component_name)

            state_fields = [
                c
                for c in window.controls
                if c.control_type
                in (UIControlType.INPUT, UIControlType.CHECKBOX, UIControlType.SELECT)
            ]
            buttons = [c for c in window.controls if c.control_type == UIControlType.BUTTON]
            tables = [c for c in window.controls if c.control_type == UIControlType.TABLE]
            labels = [c for c in window.controls if c.control_type == UIControlType.LABEL]

            uses_close = any("ferme" in ev.procedure_name.lower() for ev in window.events)
            for ev in window.events:
                if any(re.search(r"\bFerme\s*\(", ln) for ln in ev.body_lines):
                    uses_close = True

            lines: list[str] = []
            self._emit_header(lines, window, name)
            self._emit_imports(lines, has_input=bool(state_fields), has_button=bool(buttons), has_table=bool(tables))
            self._emit_form_data_interface(lines, name, state_fields, warnings)
            self._emit_handlers(lines, window, name, uses_close, warnings)
            self._emit_component(
                lines,
                name,
                window=window,
                state_fields=state_fields,
                buttons=buttons,
                tables=tables,
                labels=labels,
                uses_close=uses_close,
                warnings=warnings,
            )

            tsx = "\n".join(lines).rstrip() + "\n"
            return UIGenerationResult(
                success=True,
                component_name=name,
                tsx_code=tsx,
                warnings=warnings,
            )
        except Exception as exc:  # pragma: no cover - garde-fou
            fallback = component_name or _pascal(window.filename.rsplit(".", 1)[0])
            return UIGenerationResult(
                success=False,
                component_name=fallback,
                warnings=warnings,
                error=str(exc),
            )

    # ── Nom du composant ──────────────────────────────────────────────────

    @staticmethod
    def _resolve_component_name(window: ASTWindow, override: str | None) -> str:
        raw = override or window.filename.rsplit(".", 1)[0]
        return _pascal(raw)

    # ── Émission du fichier TSX ───────────────────────────────────────────

    @staticmethod
    def _emit_header(lines: list[str], window: ASTWindow, name: str) -> None:
        lines.append('"use client";')
        lines.append("/**")
        lines.append(f" * Composant généré par Tharos Core v0.4 — IHM transpilée.")
        lines.append(f" * Source   : {window.filename}")
        title = window.title or "Fenêtre WinDev"
        lines.append(f" * Titre    : {title}")
        lines.append(" * Style    : Tailwind CSS + shadcn/ui (@/components/ui/*)")
        lines.append(" */")

    @staticmethod
    def _emit_imports(
        lines: list[str], *, has_input: bool, has_button: bool, has_table: bool
    ) -> None:
        lines.append("")
        lines.append('import { useState } from "react";')
        if has_input:
            lines.append('import { Input } from "@/components/ui/input";')
        if has_button:
            lines.append('import { Button } from "@/components/ui/button";')
        if has_input:
            lines.append('import { Label } from "@/components/ui/label";')
        if has_table:
            lines.append(
                'import {\n'
                "  Table,\n"
                "  TableBody,\n"
                "  TableCell,\n"
                "  TableHead,\n"
                "  TableHeader,\n"
                "  TableRow,\n"
                '} from "@/components/ui/table";'
            )

    @staticmethod
    def _emit_form_data_interface(
        lines: list[str],
        name: str,
        fields: list[ASTUIControl],
        warnings: list[str],
    ) -> None:
        if not fields:
            return
        lines.append("")
        lines.append(f"export interface {name}Form {{")
        for ctrl in fields:
            key = _field_key(ctrl.name)
            ts_type = (
                _TS_TYPE_MAP.get(ctrl.wtype, "string")
                if ctrl.wtype is not None
                else "string"
            )
            if ctrl.wtype is None:
                warnings.append(
                    f"{ctrl.name} : type WLanguage non résolu → string par défaut"
                )
            lines.append(f"  {key}: {ts_type};")
        lines.append("}")

    def _emit_handlers(
        self,
        lines: list[str],
        window: ASTWindow,
        name: str,
        uses_close: bool,
        warnings: list[str],
    ) -> None:
        if not window.events:
            return
        lines.append("")
        if uses_close:
            lines.append(f"export interface {name}Props {{")
            lines.append("  onClose?: () => void;")
            lines.append("}")
            lines.append("")
        for ev in window.events:
            handler = _handler_name(ev.procedure_name)
            lines.append(f"async function {handler}(): Promise<void> {{")
            body = self._translate_body(ev.body_lines, uses_close, warnings)
            if not body:
                body = ["// Aucune logique détectée dans la procédure d'origine."]
            lines.extend(body)
            lines.append("}")

    @staticmethod
    def _api_fetch(method: str, table: str, data_expr: str) -> str:
        endpoint = "/api/" + _camel(table)
        return (
            f'await fetch("{endpoint}", {{ method: "{method}", headers: '
            f'{{ "Content-Type": "application/json" }}, body: JSON.stringify({data_expr}) }});'
        )

    def _translate_body(
        self, body_lines: list[str], uses_close: bool, warnings: list[str]
    ) -> list[str]:
        out: list[str] = []
        untranslated = 0
        indent = "  "

        for raw in body_lines:
            line = re.sub(r"//.*$", "", raw).strip()
            if not line:
                continue

            m = _RE_HAJOUTE.search(line)
            if m:
                out.append(indent + self._api_fetch("POST", m.group(1), "formData"))
                continue
            m = _RE_HMODIFIE.search(line)
            if m:
                out.append(indent + self._api_fetch("PUT", m.group(1), "formData"))
                continue
            m = _RE_HSUPPRIME.search(line)
            if m:
                endpoint = "/api/" + _camel(m.group(1))
                out.append(indent + f'await fetch("{endpoint}", {{ method: "DELETE" }});')
                continue
            m = _RE_HSQL.search(line)
            if m:
                sql = m.group(1).replace('"', '\\"')
                out.append(
                    indent
                    + 'await fetch("/api/query", { method: "POST", headers: '
                    + '{ "Content-Type": "application/json" }, body: JSON.stringify({ sql: "'
                    + sql
                    + '" }) });'
                )
                continue
            m = _RE_INFO.match(line) or _RE_ERREUR.search(line)
            if m and (_RE_INFO.match(line)):
                msg = m.group(1).replace('"', "")
                out.append(indent + f'window.alert("{msg}");')
                continue
            if _RE_ERREUR.search(line):
                mm = _RE_ERREUR.search(line)
                msg = (mm.group(1) if mm else "Erreur").replace('"', "")
                out.append(indent + f'window.alert("Erreur: {msg}");')
                continue
            if re.match(r"^Ferme\s*\(", line) or line == "Ferme()":
                if uses_close:
                    out.append(indent + "onClose?.();")
                else:
                    out.append(indent + "// Ferme() : fenêtre fermée côté conteneur")
                continue
            if re.match(r"^\w+\s+est\s+(une?|un)\s+", line):
                out.append(indent + f"// [état React] {line}")
                continue
            if re.match(r"^(EcranVersFichier|FichierVersEcran)\s*\(", line):
                out.append(indent + "// synchronisation écran↔fichier portée par l'état React")
                continue
            if re.match(r"^(SI|SINON|FIN|POUR)\b", line):
                out.append(indent + f"// TODO contrôle de flux WLanguage : {line}")
                untranslated += 1
                continue
            if re.match(r"^RENVOYER\b", line):
                value = line[len("RENVOYER"):].strip()
                out.append(indent + f"return {value};")
                continue

            out.append(indent + f"// TODO WLanguage : {line}")
            untranslated += 1

        if untranslated:
            warnings.append(
                f"{untranslated} instruction(s) WLanguage non transposables "
                "déterministement (marquées TODO)."
            )
        return out

    def _emit_component(
        self,
        lines: list[str],
        name: str,
        *,
        window: ASTWindow,
        state_fields: list[ASTUIControl],
        buttons: list[ASTUIControl],
        tables: list[ASTUIControl],
        labels: list[ASTUIControl],
        uses_close: bool,
        warnings: list[str],
    ) -> None:
        lines.append("")
        props_sig = f"props: {name}Props" if uses_close else ""
        lines.append(f"export default function {name}({props_sig}) {{")
        if uses_close:
            lines.append("  const { onClose } = props;")

        if state_fields:
            lines.append(f"  const initial{name}Form: {name}Form = {{")
            for ctrl in state_fields:
                key = _field_key(ctrl.name)
                default = self._default_literal(ctrl)
                lines.append(f"    {key}: {default},")
            lines.append("  };")
            lines.append(f"  const [formData, setFormData] = useState<{name}Form>(initial{name}Form);")
            lines.append("")
            lines.append("  function update<K extends keyof " + name + "Form>(")
            lines.append("    key: K,")
            lines.append("    value: " + name + "Form[K],")
            lines.append("  ) {")
            lines.append("    setFormData((prev) => ({ ...prev, [key]: value }));")
            lines.append("  }")
            lines.append("")

        if tables:
            lines.append("  // TODO brancher sur GET /api/<table> (backend v0.3)")
            lines.append("  const tableRows: Array<Record<string, string | number>> = [];")
            lines.append("")

        submit_ev = next((e for e in window.events if e.event_name == "clic"), None)

        title = window.title or name
        lines.append("  return (")
        lines.append('    <div className="mx-auto flex max-w-xl flex-col gap-6 rounded-xl border bg-white p-8 shadow-sm">')
        lines.append('      <h2 className="text-lg font-semibold tracking-tight text-zinc-900">')
        lines.append(f"        {title}")
        lines.append("      </h2>")

        open_form = bool(submit_ev) and bool(buttons)
        if open_form:
            handler = _handler_name(submit_ev.procedure_name)
            lines.append(
                f'      <form onSubmit={{(e) => {{ e.preventDefault(); void {handler}(); }}}} '
                'className="flex flex-col gap-4">'
            )

        inner_indent = "        " if open_form else "      "

        for lbl in labels:
            text = lbl.label or lbl.default_value or lbl.name
            lines.append(f'{inner_indent}<p className="text-sm text-zinc-600">{text}</p>')

        for ctrl in state_fields:
            self._emit_field(lines, inner_indent, ctrl, name)

        for tbl in tables:
            self._emit_table(lines, inner_indent, tbl)

        if buttons:
            lines.append(f'{inner_indent}<div className="flex items-center justify-end gap-3 pt-2">')
            for btn in buttons:
                ev = next(
                    (e for e in window.events if e.control_name == btn.name and e.event_name == "clic"),
                    None,
                )
                label = btn.label or btn.default_value or btn.name.split("_", 1)[1]
                is_submit = bool(ev) and ev is submit_ev
                handler = _handler_name(ev.procedure_name) if ev else None
                variant = "" if is_submit else ' variant="outline"'
                click = (
                    f"onClick={{() => void {handler}()}}"
                    if handler and not is_submit
                    else ""
                )
                type_attr = 'type="submit"' if is_submit else 'type="button"'
                attrs = " ".join(a for a in (type_attr, variant, click) if a)
                lines.append(f'{inner_indent}  <Button {attrs}>{label}</Button>')
            lines.append(f"{inner_indent}</div>")

        if open_form:
            lines.append("      </form>")
        lines.append("    </div>")
        lines.append("  );")
        lines.append("}")

    @staticmethod
    def _default_literal(ctrl: ASTUIControl) -> str:
        wtype = ctrl.wtype
        dv = ctrl.default_value
        if wtype is VariableType.BOOLEEN:
            if dv and dv.lower() in {"vrai", "true"}:
                return "true"
            return "false"
        if wtype in (VariableType.ENTIER, VariableType.REEL, VariableType.MONETAIRE):
            if dv is not None:
                num = re.sub(r"[^0-9.,-]", "", dv).replace(",", ".")
                if num:
                    return num
            return "0"
        if dv is not None:
            escaped = str(dv).replace('"', '\\"')
            return f'"{escaped}"'
        return '""'

    def _emit_field(self, lines: list[str], indent: str, ctrl: ASTUIControl, name: str) -> None:
        key = _field_key(ctrl.name)
        label = ctrl.label or ctrl.name.split("_", 1)[1]

        if ctrl.control_type == UIControlType.INPUT:
            input_type = (
                "number"
                if ctrl.wtype in (VariableType.ENTIER, VariableType.REEL, VariableType.MONETAIRE)
                else "text"
            )
            lines.append(f"{indent}<div className=\"flex flex-col gap-1.5\">")
            lines.append(f'{indent}  <Label htmlFor="{key}">{label}</Label>')
            lines.append(
                f'{indent}  <Input id="{key}" type="{input_type}" '
                f"value={{formData.{key}}} onChange={{(e) => update(\"{key}\", "
                "e.target.value)}} />"
            )
            lines.append(f"{indent}</div>")
        elif ctrl.control_type == UIControlType.CHECKBOX:
            lines.append(f"{indent}<div className=\"flex items-center gap-2\">")
            lines.append(
                f'{indent}  <input id="{key}" type="checkbox" className="h-4 w-4 accent-indigo-600" '
                f"checked={{formData.{key}}} onChange={{(e) => update(\"{key}\", e.target.checked)}} />"
            )
            lines.append(f'{indent}  <Label htmlFor="{key}">{label}</Label>')
            lines.append(f"{indent}</div>")
        elif ctrl.control_type == UIControlType.SELECT:
            lines.append(f"{indent}<div className=\"flex flex-col gap-1.5\">")
            lines.append(f'{indent}  <Label htmlFor="{key}">{label}</Label>')
            lines.append(f'{indent}  <select id="{key}" className="h-9 rounded-md border border-zinc-300 bg-white px-3 text-sm"')
            lines.append(f'{indent}          value={{formData.{key}}} onChange={{(e) => update("{key}", e.target.value)}}>')
            lines.append(f'{indent}    <option value="">{label}…</option>')
            lines.append(f"{indent}  </select>")
            lines.append(f"{indent}</div>")

    @staticmethod
    def _emit_table(lines: list[str], indent: str, tbl: ASTUIControl) -> None:
        cols = tbl.columns or ["Colonne 1", "Colonne 2"]
        label = tbl.label or tbl.name.split("_", 1)[1]
        lines.append(f"{indent}<div className=\"flex flex-col gap-2\">")
        lines.append(f'{indent}  <p className="text-sm font-medium text-zinc-700">{label}</p>')
        lines.append(f"{indent}  <Table>")
        lines.append(f"{indent}    <TableHeader>")
        lines.append(f"{indent}      <TableRow>")
        for col in cols:
            lines.append(f"{indent}        <TableHead>{col}</TableHead>")
        lines.append(f"{indent}      </TableRow>")
        lines.append(f"{indent}    </TableHeader>")
        lines.append(f"{indent}    <TableBody>")
        lines.append(f"{indent}      {{tableRows.length === 0 ? (")
        lines.append(
            f"{indent}        <TableRow><TableCell colSpan={{{len(cols)}}} className=\"h-16 text-center text-zinc-500\">Aucune ligne</TableCell></TableRow>"
        )
        lines.append(f"{indent}      ) : null}}")
        lines.append(f"{indent}    </TableBody>")
        lines.append(f"{indent}  </Table>")
        lines.append(f"{indent}</div>")
