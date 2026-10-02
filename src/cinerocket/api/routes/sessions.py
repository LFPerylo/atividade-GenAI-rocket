from typing import Annotated

from fastapi import APIRouter, Path, Response, status

from cinerocket.api.dependencies import ServiceDep
from cinerocket.api.schemas import SESSION_ID_PATTERN
from cinerocket.domain.models import ChatResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])

SessionId = Annotated[str, Path(pattern=SESSION_ID_PATTERN)]


@router.get("/{session_id}")
def get_session(session_id: SessionId, service: ServiceDep) -> list[ChatResponse]:
    return service.transcript(session_id)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: SessionId, service: ServiceDep) -> Response:
    service.reset(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
