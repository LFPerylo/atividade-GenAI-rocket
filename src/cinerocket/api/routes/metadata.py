import httpx
from fastapi import APIRouter, HTTPException, status

from cinerocket.api.dependencies import ContainerDep
from cinerocket.domain.errors import ConfigurationError
from cinerocket.domain.models import TableInfo
from cinerocket.llm.quota import KeyData, fetch_openrouter_quota

router = APIRouter(tags=["metadata"])


@router.get("/schema")
def schema(container: ContainerDep) -> list[TableInfo]:
    return list(container.catalog.tables.values())


@router.get("/quota")
async def quota(container: ContainerDep) -> KeyData:
    api_key = container.settings.openrouter_api_key
    if api_key is None:
        raise ConfigurationError("OPENROUTER_API_KEY não configurada.")
    try:
        return await fetch_openrouter_quota(api_key.get_secret_value())
    except httpx.HTTPError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"Falha ao consultar o OpenRouter: {error}"
        ) from error
