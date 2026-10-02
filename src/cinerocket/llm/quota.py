import httpx
from pydantic import BaseModel

from cinerocket.llm.factory import OPENROUTER_BASE_URL


class DailyRequests(BaseModel):
    used: int | None = None
    limit: int | None = None
    remaining: int | None = None


class KeyData(BaseModel):
    label: str | None = None
    usage: float | None = None
    limit: float | None = None
    is_free_tier: bool | None = None
    free_model_daily_requests: DailyRequests | None = None


class KeyInfo(BaseModel):
    data: KeyData


async def fetch_openrouter_quota(api_key: str, client: httpx.AsyncClient | None = None) -> KeyData:
    if client is None:
        async with httpx.AsyncClient(timeout=10) as owned:
            return await _request_key_info(api_key, owned)
    return await _request_key_info(api_key, client)


async def _request_key_info(api_key: str, client: httpx.AsyncClient) -> KeyData:
    response = await client.get(f"{OPENROUTER_BASE_URL}/key", headers={"Authorization": f"Bearer {api_key}"})
    response.raise_for_status()
    return KeyInfo.model_validate(response.json()).data
