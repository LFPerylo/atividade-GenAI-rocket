from typing import Any

import httpx
from pydantic import TypeAdapter

from cinerocket.domain.models import ChatResponse

TRANSCRIPT = TypeAdapter(list[ChatResponse])


class ApiError(Exception):
    pass


class CineRocketClient:
    def __init__(self, base_url: str, timeout_seconds: float = 180) -> None:
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout_seconds)

    def ask(self, question: str, session_id: str | None) -> ChatResponse:
        payload = {"question": question, "session_id": session_id}
        return ChatResponse.model_validate(self._request("POST", "/api/v1/chat", json=payload))

    def transcript(self, session_id: str) -> list[ChatResponse]:
        return TRANSCRIPT.validate_python(self._request("GET", f"/api/v1/sessions/{session_id}"))

    def reset(self, session_id: str) -> None:
        self._request("DELETE", f"/api/v1/sessions/{session_id}")

    def health(self) -> dict[str, Any]:
        return dict(self._request("GET", "/health"))

    def quota(self) -> dict[str, Any]:
        return dict(self._request("GET", "/api/v1/quota"))

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.TimeoutException as error:
            raise ApiError(
                "A análise demorou mais que o esperado. Tente uma pergunta mais específica."
            ) from error
        except httpx.HTTPError as error:
            message = f"Não foi possível conectar à API em {self._http.base_url}. Ela está no ar?"
            raise ApiError(message) from error
        if response.status_code == httpx.codes.NO_CONTENT:
            return None
        if response.is_error:
            raise ApiError(self._error_message(response))
        return response.json()

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return f"Erro {response.status_code} na API."
        detail = body.get("detail")
        if isinstance(detail, list):
            return "; ".join(str(item.get("msg", item)) for item in detail)
        return str(detail or f"Erro {response.status_code} na API.")
