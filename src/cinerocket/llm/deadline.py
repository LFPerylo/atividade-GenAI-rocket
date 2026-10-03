import anyio
from pydantic_ai.exceptions import ModelAPIError
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import Model, ModelRequestParameters
from pydantic_ai.models.wrapper import WrapperModel
from pydantic_ai.settings import ModelSettings


class DeadlineModel(WrapperModel):
    def __init__(self, wrapped: Model, seconds: float) -> None:
        super().__init__(wrapped)
        self._seconds = seconds

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        try:
            with anyio.fail_after(self._seconds):
                return await super().request(messages, model_settings, model_request_parameters)
        except TimeoutError as error:
            raise ModelAPIError(self.model_name, f"sem resposta completa em {self._seconds:.0f} s") from error
