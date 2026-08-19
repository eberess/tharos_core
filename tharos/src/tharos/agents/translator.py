"""Agent traducteur — génération du code cible via LLM."""

import json
import os
import re
from dataclasses import dataclass

import requests

from tharos.graph.builder import DependencyGraphBuilder
from tharos.parsers.base import ASTModel, ASTProcedure

# ── Prompt système Clean Architecture ────────────────────────────────────────

SYSTEM_PROMPT = """\
Tu es un expert en migration de code legacy WinDev/WLanguage vers Python moderne.

## Règles strictes
1. Génère du Python 3.12+ avec type hints complets.
2. Utilise Pydantic v2 pour tous les modèles de données.
3. Structure le code en Clean Architecture :
   - Un fichier par fonction/endpoint.
   - Modèles Pydantic séparés.
   - Fonctions pures quand possible.
4. Remplace HFSQL par SQLAlchemy 2.0 (async si possible).
5. Les procédures WLanguage deviennent des fonctions Python.
6. Les variables globales deviennent des paramètres explicites ou des models Pydantic.
7. Les conditions SI/SINON deviennent if/elif/else.
8. Les RENVOYER deviennent return.
9. Aucun commentaire sauf si demandé.
10. Code valide syntaxiquement (pas de pseudo-code).
"""

# ── Mapping des types WLanguage → Python ─────────────────────────────────────

WTYPE_TO_PYTHON: dict[str, str] = {
    "chaine": "str",
    "entier": "int",
    "reel": "float",
    "monetaire": "float",
    "date": "date",
    "booleen": "bool",
    "complexe": "Any",
}


def _wtype_to_python(wtype: str) -> str:
    return WTYPE_TO_PYTHON.get(wtype.lower(), "Any")


# ── Client LLM configurable ──────────────────────────────────────────────────


@dataclass
class LLMConfig:
    provider: str  # "ollama", "vllm", "openai", "anthropic"
    model: str
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.2
    max_tokens: int = 4096


def _load_config() -> LLMConfig:
    """Charge la configuration LLM depuis les variables d'environnement."""
    provider = os.getenv("THAROS_LLM_PROVIDER", "ollama")
    model = os.getenv("THAROS_LLM_MODEL", "qwen2.5-coder:7b")
    base_url = os.getenv("THAROS_LLM_BASE_URL")
    api_key = os.getenv("THAROS_LLM_API_KEY")
    temperature = float(os.getenv("THAROS_LLM_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("THAROS_LLM_MAX_TOKENS", "4096"))

    if base_url is None:
        if provider in ("ollama", "vllm"):
            base_url = "http://localhost:11434" if provider == "ollama" else "http://localhost:8000"
        elif provider == "openai":
            base_url = "https://api.openai.com/v1"
        elif provider == "anthropic":
            base_url = "https://api.anthropic.com"

    return LLMConfig(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _call_ollama(config: LLMConfig, prompt: str, system: str) -> str:
    resp = requests.post(
        f"{config.base_url}/api/chat",
        json={
            "model": config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            },
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _call_vllm(config: LLMConfig, prompt: str, system: str) -> str:
    resp = requests.post(
        f"{config.base_url}/v1/chat/completions",
        json={
            "model": config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_openai(config: LLMConfig, prompt: str, system: str) -> str:
    resp = requests.post(
        f"{config.base_url}/chat/completions",
        headers={"Authorization": f"Bearer {config.api_key}"},
        json={
            "model": config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_anthropic(config: LLMConfig, prompt: str, system: str) -> str:
    resp = requests.post(
        f"{config.base_url}/v1/messages",
        headers={
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": config.model,
            "max_tokens": config.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config.temperature,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def _call_llm(config: LLMConfig, prompt: str, system: str) -> str:
    dispatch = {
        "ollama": _call_ollama,
        "vllm": _call_vllm,
        "openai": _call_openai,
        "anthropic": _call_anthropic,
    }
    fn = dispatch.get(config.provider)
    if fn is None:
        raise ValueError(f"Fournisseur LLM inconnu : {config.provider}")
    return fn(config, prompt, system)


# ── Extraction de code depuis la réponse LLM ─────────────────────────────────

_CODE_BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def _extract_python_code(response: str) -> str:
    """Extrait le code Python depuis une réponse markdown avec blocs de code."""
    match = _CODE_BLOCK.search(response)
    if match:
        return match.group(1).strip()
    return response.strip()


def _validate_python_code(code: str) -> bool:
    """Vérifie que le code est syntaxiquement valide."""
    try:
        compile(code, "<translated>", "exec")
        return True
    except SyntaxError:
        return False


# ── Prompt de traduction ─────────────────────────────────────────────────────


def _build_procedure_prompt(proc: ASTProcedure, context: str = "") -> str:
    """Construit le prompt de traduction pour une procédure."""
    params = ", ".join(
        f"{p.name}: {_wtype_to_python(p.wtype.value)}" for p in proc.parameters
    )
    ret_type = "None"
    if proc.return_value:
        ret_type = "Any"

    body = "\n".join(proc.body_lines)

    return (
        f"Traduis cette procédure WLanguage en Python FastAPI.\n\n"
        f"## Procédure : {proc.name}\n"
        f"Paramètres : ({params})\n"
        f"Retour : {ret_type}\n"
        f"Variables locales : "
        + ", ".join(
            f"{v.name} ({v.wtype.value})" for v in proc.local_variables
        )
        + "\n\n"
        f"```wlanguage\nPROCEDURE {proc.name}({params})\n{body}\n```\n\n"
        + (f"## Contexte\n{context}\n\n" if context else "")
        + "Génère une fonction Python valide avec type hints et docstring."
    )


def _build_subgraph_prompt(
    proc: ASTProcedure,
    builder: DependencyGraphBuilder,
) -> str:
    """Construit le prompt avec le sous-graphe de dépendances."""
    context_lines: list[str] = []

    # Procédures appelées
    for _, target, data in builder.graph.out_edges(proc.name, data=True):
        if data.get("kind") == "calls":
            called_proc = next(
                (p for p in builder.ast.procedures if p.name == target), None
            )
            if called_proc:
                context_lines.append(
                    f"Procédure appelée {target}("
                    + ", ".join(
                        f"{p.name}: {p.wtype.value}" for p in called_proc.parameters
                    )
                    + f") → {_wtype_to_python(called_proc.return_value or 'void')}"
                )

    # Tables utilisées
    for _, target, data in builder.graph.out_edges(proc.name, data=True):
        if data.get("kind") == "accesses":
            table = target.replace("TABLE:", "")
            context_lines.append(f"Table HFSQL : {table} (opération {data.get('operation', '')})")

    # Variables globales utilisées
    for _, target, data in builder.graph.out_edges(proc.name, data=True):
        if data.get("kind") == "uses":
            var_name = target.replace("VAR:", "")
            var_info = next(
                (v for v in builder.ast.global_variables if v.name == var_name), None
            )
            if var_info:
                context_lines.append(f"Variable globale : {var_name} ({var_info.wtype.value})")

    context = "\n".join(context_lines) if context_lines else ""
    return _build_procedure_prompt(proc, context)


# ── Classe publique ──────────────────────────────────────────────────────────


@dataclass
class TranslationResult:
    source_proc: str
    generated_code: str
    is_valid: bool
    provider: str
    model: str


class CodeTranslatorAgent:
    """Agent de traduction WLanguage → Python via LLM configurable."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or _load_config()

    def translate_procedure(
        self, proc: ASTProcedure, context: str = ""
    ) -> TranslationResult:
        """Traduit une procédure WLanguage."""
        prompt = _build_procedure_prompt(proc, context)
        raw_response = _call_llm(self.config, prompt, SYSTEM_PROMPT)
        code = _extract_python_code(raw_response)
        valid = _validate_python_code(code)

        return TranslationResult(
            source_proc=proc.name,
            generated_code=code,
            is_valid=valid,
            provider=self.config.provider,
            model=self.config.model,
        )

    def translate_procedure_with_graph(
        self,
        proc: ASTProcedure,
        ast: ASTModel,
    ) -> TranslationResult:
        """Traduit une procédure en utilisant le sous-graphe de dépendances."""
        builder = DependencyGraphBuilder(ast)
        builder.build()

        prompt = _build_subgraph_prompt(proc, builder)
        raw_response = _call_llm(self.config, prompt, SYSTEM_PROMPT)
        code = _extract_python_code(raw_response)
        valid = _validate_python_code(code)

        return TranslationResult(
            source_proc=proc.name,
            generated_code=code,
            is_valid=valid,
            provider=self.config.provider,
            model=self.config.model,
        )
