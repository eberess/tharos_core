"""Agent correcteur — analyse des erreurs et correction en boucle."""

from dataclasses import dataclass

from tharos.agents.translator import (
    LLMConfig,
    _call_llm,
    _extract_python_code,
    _load_config,
    _validate_python_code,
)

CORRECTOR_SYSTEM_PROMPT = """\
Tu es un expert en debug et refactoring Python. Tu reçois du code généré automatiquement \
qui contient des erreurs lors de l'exécution de tests pytest.

## Règles strictes
1. Corrige UNIQUEMENT la partie défaillante. Ne change PAS la signature de la fonction.
2. Conserve le type hints, la docstring et la structure existante.
3. Analyse le traceback pour identifier la cause racine (AssertionError, TypeError, NameError...).
4. Retourne le code complet corrigé (pas un diff).
5. Code valide syntaxiquement (pas de pseudo-code).
6. N'ajoute aucun commentaire.
"""


@dataclass
class CorrectionResult:
    source_proc: str
    generated_code: str
    is_valid: bool
    attempt: int
    provider: str
    model: str


def _build_correction_prompt(
    original_code: str,
    traceback: str,
    context: str = "",
) -> str:
    parts = [
        "Le code suivant génère des erreurs lors de pytest. "
        "Corrige les erreurs tout en conservant la signature de la fonction.\n\n",
        "## Code actuel\n",
        f"```python\n{original_code}\n```\n\n",
        "## Traceback pytest\n",
        f"```\n{traceback}\n```\n\n",
    ]
    if context:
        parts.append(f"## Contexte dépendances\n{context}\n\n")
    parts.append("Retourne le code Python corrigé complet.")
    return "".join(parts)


class CodeCorrectorAgent:
    """Agent de correction automatique via LLM."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or _load_config()

    def correct(
        self,
        original_code: str,
        traceback: str,
        context: str = "",
        attempt: int = 1,
        source_proc: str = "",
    ) -> CorrectionResult:
        prompt = _build_correction_prompt(original_code, traceback, context)
        raw_response = _call_llm(self.config, prompt, CORRECTOR_SYSTEM_PROMPT)
        code = _extract_python_code(raw_response)
        valid = _validate_python_code(code)

        return CorrectionResult(
            source_proc=source_proc,
            generated_code=code,
            is_valid=valid,
            attempt=attempt,
            provider=self.config.provider,
            model=self.config.model,
        )
