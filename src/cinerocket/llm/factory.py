from dataclasses import dataclass

from openai import AsyncOpenAI
from pydantic_ai.exceptions import ModelAPIError
from pydantic_ai.models import Model
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider

from cinerocket.config import Settings
from cinerocket.domain.errors import ConfigurationError
from cinerocket.llm.deadline import DeadlineModel

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
APP_TITLE = "CineRocket Analytics"


@dataclass(frozen=True)
class ModelChain:
    model: Model
    names: tuple[str, ...]

    @property
    def fingerprint(self) -> str:
        return ",".join(self.names)


def build_model_chain(settings: Settings) -> ModelChain:
    models: list[Model] = []
    if settings.openrouter_api_key is not None:
        client = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=settings.openrouter_api_key.get_secret_value(),
            max_retries=0,
            default_headers={"X-Title": APP_TITLE},
        )
        provider = OpenRouterProvider(openai_client=client)
        models.extend(OpenRouterModel(name, provider=provider) for name in settings.openrouter_models)
    if settings.google_api_key is not None:
        google = GoogleProvider(api_key=settings.google_api_key.get_secret_value())
        models.extend(GoogleModel(name, provider=google) for name in settings.gemini_models)
    if not models:
        raise ConfigurationError("Configure OPENROUTER_API_KEY e/ou GOOGLE_API_KEY no arquivo .env.")
    names = tuple(model.model_name for model in models)
    bounded = [DeadlineModel(model, settings.llm_timeout_seconds) for model in models]
    if len(bounded) == 1:
        return ModelChain(model=bounded[0], names=names)
    return ModelChain(model=FallbackModel(*bounded, fallback_on=(ModelAPIError,)), names=names)
