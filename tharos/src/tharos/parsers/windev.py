"""Parser AST pour les fichiers WinDev / WLanguage."""

import re
from pathlib import Path

from tharos.parsers.base import (
    ASTCondition,
    ASTHFSQLQuery,
    ASTModel,
    ASTParameter,
    ASTProcedure,
    ASTVariable,
    BaseParser,
    HFSQLQueryType,
    VariableType,
)

# ── Mapping des types WLanguage → types normalisés ──────────────────────────

WTYPE_MAP: dict[str, VariableType] = {
    "chaîne": VariableType.CHAINE,
    "chaine": VariableType.CHAINE,
    "entier": VariableType.ENTIER,
    "réel": VariableType.REEL,
    "reel": VariableType.REEL,
    "monétaire": VariableType.MONETAIRE,
    "monetaire": VariableType.MONETAIRE,
    "date": VariableType.DATE,
    "booléen": VariableType.BOOLEEN,
    "booleen": VariableType.BOOLEEN,
}


def _resolve_wtype(raw: str) -> VariableType:
    normalized = raw.strip().lower().replace("une ", "").replace("un ", "")
    return WTYPE_MAP.get(normalized, VariableType.COMPLEXE)


# ── Patterns regex ───────────────────────────────────────────────────────────

# Déclaration de variable globale : sNomClient est une chaîne
RE_GLOBAL_VAR = re.compile(
    r"^(?P<name>\w+)\s+est\s+(?:une?|un)\s+(?P<wtype>[a-zA-ZÀ-ÿéèêëàâäùûüôöîïç]+)",
    re.MULTILINE,
)

# Déclaration de variable locale : nTVA est un monétaire
RE_LOCAL_VAR = re.compile(
    r"^(?P<name>\w+)\s+est\s+(?:une?|un)\s+(?P<wtype>[a-zA-ZÀ-ÿéèêëàâäùûüôöîïç]+)",
    re.MULTILINE,
)

# En-tête procédure : PROCEDURE Nom(arg1 type, arg2 type) LOCAL
RE_PROCEDURE_HEADER = re.compile(
    r"^PROCEDURE\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*(?:LOCAL)?",
    re.MULTILINE,
)

# RENVOYER (valeur de retour)
RE_RETURN = re.compile(r"RENVOYER\s+(?P<value>.+)", re.MULTILINE)

# HFSQL : HExécuteRequêteSQL("...")
RE_HFSQL_QUERY = re.compile(
    r'HExécuteRequêteSQL\s*\(\s*"(?P<sql>[^"]+)"',
    re.MULTILINE,
)

# HFSQL : HLitPremier(REQ_xxx)
RE_HFSQL_READ = re.compile(
    r"HLitPremier\s*\(\s*(?P<cursor>\w+)\s*\)",
    re.MULTILINE,
)

# HFSQL : HAjoute(NOM_TABLE)
RE_HFSQL_INSERT = re.compile(
    r"HAjoute\s*\(\s*(?P<table>\w+)\s*\)",
    re.MULTILINE,
)

# Bloc conditionnel : SI ... ALORS / SINON SI ... ALORS / SINON
RE_CONDITION = re.compile(
    r"^(?P<type>SI|SINON\s+SI|SINON)\s+(?P<expr>.+?)\s*(?:ALORS)?$",
    re.MULTILINE,
)

RE_BLOCK_END = re.compile(r"^\s*FIN\s*$", re.MULTILINE)


def _parse_wtypes_from_params(params_str: str) -> list[ASTParameter]:
    """Parse les paramètres d'une procédure WLanguage."""
    if not params_str.strip():
        return []

    params: list[ASTParameter] = []
    for param in params_str.split(","):
        param = param.strip()
        # Format : nMontantHT est un monétaire
        match = re.match(r"(\w+)\s+est\s+(?:une?|un)\s+(.+)", param)
        if match:
            params.append(
                ASTParameter(name=match.group(1), wtype=_resolve_wtype(match.group(2)))
            )
    return params


def _classify_hfsql(sql: str) -> tuple[HFSQLQueryType, str]:
    """Classifie une requête HFSQL et extrait la table cible."""
    upper = sql.strip().upper()

    if upper.startswith("SELECT"):
        table_match = re.search(r"FROM\s+(\w+)", upper)
        table = table_match.group(1) if table_match else "UNKNOWN"
        return HFSQLQueryType.SELECT, table
    elif upper.startswith("INSERT"):
        table_match = re.search(r"INTO\s+(\w+)", upper)
        table = table_match.group(1) if table_match else "UNKNOWN"
        return HFSQLQueryType.INSERT, table
    elif upper.startswith("UPDATE"):
        table_match = re.search(r"UPDATE\s+(\w+)", upper)
        table = table_match.group(1) if table_match else "UNKNOWN"
        return HFSQLQueryType.UPDATE, table
    elif upper.startswith("DELETE"):
        table_match = re.search(r"FROM\s+(\w+)", upper)
        table = table_match.group(1) if table_match else "UNKNOWN"
        return HFSQLQueryType.DELETE, table

    return HFSQLQueryType.SELECT, "UNKNOWN"


class WinDevParser(BaseParser):
    """Parser déterministe pour les fichiers WinDev (.wdw, .wdg, .wda)."""

    def parse_file(self, filepath: Path) -> ASTModel:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")

        # Extraire les variables globales (avant toute procédure)
        global_vars = self._extract_global_variables(content, lines)

        # Extraire les procédures
        procedures = self.extract_functions(content)

        # Extraire les requêtes HFSQL (depuis le contenu complet)
        queries = self.extract_queries(content)

        # Extraire les conditions
        conditions = self._extract_conditions(content, lines)

        return ASTModel(
            filename=filepath.name,
            global_variables=global_vars,
            procedures=procedures,
            hfsql_queries=queries,
            conditions=conditions,
            total_lines=len(lines),
        )

    def _extract_global_variables(
        self, content: str, lines: list[str]
    ) -> list[ASTVariable]:
        """Extrait les variables déclarées avant la première procédure."""
        first_proc_line = None
        for i, line in enumerate(lines):
            if re.match(r"^\s*PROCEDURE\s+", line, re.IGNORECASE):
                first_proc_line = i
                break

        header = content if first_proc_line is None else "\n".join(lines[:first_proc_line])
        variables: list[ASTVariable] = []

        for match in RE_GLOBAL_VAR.finditer(header):
            name = match.group("name")
            wtype = _resolve_wtype(match.group("wtype"))
            line_num = header[: match.start()].count("\n") + 1
            variables.append(ASTVariable(name=name, wtype=wtype, is_global=True, line=line_num))

        return variables

    def extract_variables(self, content: str) -> list[ASTVariable]:
        """Extrait toutes les déclarations de variables (globales + locales)."""
        variables: list[ASTVariable] = []
        seen_names: set[str] = set()

        for match in RE_GLOBAL_VAR.finditer(content):
            name = match.group("name")
            if name in seen_names:
                continue
            seen_names.add(name)
            wtype = _resolve_wtype(match.group("wtype"))
            line_num = content[: match.start()].count("\n") + 1
            variables.append(ASTVariable(name=name, wtype=wtype, line=line_num))

        return variables

    def extract_functions(self, content: str) -> list[ASTProcedure]:
        """Extrait les procédures WLanguage avec leur corps."""
        lines = content.split("\n")
        procedures: list[ASTProcedure] = []
        proc_starts: list[int] = []

        # Indexer les positions de toutes les procédures
        for i, line in enumerate(lines):
            if RE_PROCEDURE_HEADER.match(line):
                proc_starts.append(i)

        for idx, start_i in enumerate(proc_starts):
            match = RE_PROCEDURE_HEADER.match(lines[start_i])
            if not match:
                continue

            proc_name = match.group("name")
            params = _parse_wtypes_from_params(match.group("params"))
            start_line = start_i + 1

            # La procédure s'étend jusqu'à la prochaine PROCEDURE ou EOF
            if idx + 1 < len(proc_starts):
                end_i = proc_starts[idx + 1]
            else:
                end_i = len(lines)

            local_vars: list[ASTVariable] = []
            body_lines: list[str] = []
            return_values: list[str] = []

            for i in range(start_i + 1, end_i):
                stripped = lines[i].strip()

                # Variables locales
                var_match = RE_LOCAL_VAR.match(stripped)
                if var_match:
                    local_vars.append(
                        ASTVariable(
                            name=var_match.group("name"),
                            wtype=_resolve_wtype(var_match.group("wtype")),
                            is_global=False,
                            line=i + 1,
                        )
                    )

                # RENVOYER
                ret_match = RE_RETURN.search(stripped)
                if ret_match:
                    return_values.append(ret_match.group("value").strip())

                body_lines.append(lines[i])

            procedures.append(
                ASTProcedure(
                    name=proc_name,
                    parameters=params,
                    local_variables=local_vars,
                    body_lines=body_lines,
                    return_value=return_values[-1] if return_values else None,
                    start_line=start_line,
                    end_line=end_i,
                )
            )

        return procedures

    def extract_queries(self, content: str) -> list[ASTHFSQLQuery]:
        """Extrait les requêtes HFSQL (HExécuteRequêteSQL)."""
        queries: list[ASTHFSQLQuery] = []
        seen_sql: set[str] = set()

        for match in RE_HFSQL_QUERY.finditer(content):
            sql = match.group("sql").strip()
            if sql in seen_sql:
                continue
            seen_sql.add(sql)

            qtype, table = _classify_hfsql(sql)
            line_num = content[: match.start()].count("\n") + 1

            queries.append(
                ASTHFSQLQuery(
                    query_type=qtype,
                    target_table=table,
                    raw_sql=sql,
                    line=line_num,
                )
            )

        return queries

    def _extract_conditions(self, content: str, lines: list[str]) -> list[ASTCondition]:
        """Extrait les blocs conditionnels SI/SINON SI/SINON."""
        conditions: list[ASTCondition] = []

        for match in RE_CONDITION.finditer(content):
            cond_type = match.group("type").strip()
            expr = match.group("expr").strip() if match.group("expr") else ""
            line_num = content[: match.start()].count("\n") + 1
            conditions.append(
                ASTCondition(condition_type=cond_type, expression=expr, line=line_num)
            )

        return conditions
