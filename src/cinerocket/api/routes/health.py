from fastapi import APIRouter

from cinerocket.api.dependencies import ContainerDep
from cinerocket.api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health")
def health(container: ContainerDep) -> HealthResponse:
    database = container.database.exists()
    return HealthResponse(
        status="ok" if database else "degraded",
        database=database,
        semantic_index=container.semantic.is_available(),
        models=list(container.model_chain.names),
    )
