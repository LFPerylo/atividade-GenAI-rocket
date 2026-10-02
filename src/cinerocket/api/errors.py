import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from cinerocket.api.schemas import ErrorResponse
from cinerocket.domain.errors import (
    AgentFailureError,
    CineRocketError,
    ConfigurationError,
    DatabaseNotFoundError,
    InvalidQuestionError,
    LLMUnavailableError,
    QueryExecutionError,
    SemanticIndexUnavailableError,
    SessionNotFoundError,
    UnsafeQueryError,
)

logger = logging.getLogger(__name__)

STATUS_BY_ERROR: dict[type[CineRocketError], int] = {
    InvalidQuestionError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    UnsafeQueryError: status.HTTP_400_BAD_REQUEST,
    QueryExecutionError: status.HTTP_400_BAD_REQUEST,
    SessionNotFoundError: status.HTTP_404_NOT_FOUND,
    AgentFailureError: status.HTTP_502_BAD_GATEWAY,
    LLMUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
    ConfigurationError: status.HTTP_503_SERVICE_UNAVAILABLE,
    DatabaseNotFoundError: status.HTTP_503_SERVICE_UNAVAILABLE,
    SemanticIndexUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def status_for(error: CineRocketError) -> int:
    for error_type in type(error).__mro__:
        if error_type in STATUS_BY_ERROR:
            return STATUS_BY_ERROR[error_type]
    return status.HTTP_500_INTERNAL_SERVER_ERROR


async def handle_domain_error(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, CineRocketError)
    code = status_for(error)
    if code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.warning("%s: %s", type(error).__name__, error)
    body = ErrorResponse(error=type(error).__name__, detail=str(error))
    return JSONResponse(status_code=code, content=body.model_dump())


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(CineRocketError, handle_domain_error)
