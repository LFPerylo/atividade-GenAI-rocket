import logging
from collections.abc import Sequence

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
ROUTER_PREFIX = "openrouter/"
FALLBACK_ROUTER = "openrouter/free"


def fetch_tool_capable_models(timeout_seconds: float = 5.0) -> frozenset[str] | None:
    try:
        response = httpx.get(OPENROUTER_MODELS_URL, timeout=timeout_seconds)
        response.raise_for_status()
        models = response.json()["data"]
    except (httpx.HTTPError, KeyError, ValueError):
        logger.warning("Catálogo do OpenRouter indisponível; usando a lista configurada sem verificação.")
        return None
    return frozenset(model["id"] for model in models if "tools" in model.get("supported_parameters", ()))


def select_available(configured: Sequence[str], catalog: frozenset[str] | None) -> list[str]:
    if catalog is None:
        return list(configured)
    available = [name for name in configured if name in catalog or name.startswith(ROUTER_PREFIX)]
    missing = [name for name in configured if name not in available]
    if missing:
        logger.warning("Modelos fora do catálogo ou sem tool calling, ignorados: %s", ", ".join(missing))
    return available or [FALLBACK_ROUTER]
