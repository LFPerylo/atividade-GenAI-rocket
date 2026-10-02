from pydantic import BaseModel, Field

SESSION_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000, examples=["Top 10 filmes com maior receita em R$"])
    session_id: str | None = Field(default=None, pattern=SESSION_ID_PATTERN)


class HealthResponse(BaseModel):
    status: str
    database: bool
    semantic_index: bool
    models: list[str]


class ErrorResponse(BaseModel):
    error: str
    detail: str
