from fastapi import APIRouter

from cinerocket.api.dependencies import ServiceDep
from cinerocket.api.schemas import ChatRequest
from cinerocket.domain.models import ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(request: ChatRequest, service: ServiceDep) -> ChatResponse:
    return await service.ask(request.question, request.session_id)
