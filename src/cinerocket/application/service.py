import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import anyio
from pydantic_ai import UsageLimits
from pydantic_ai.exceptions import (
    FallbackExceptionGroup,
    ModelAPIError,
    ModelHTTPError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

from cinerocket.agent.builder import AnalystAgent
from cinerocket.agent.deps import AgentDeps
from cinerocket.agent.history import keep_recent_turns
from cinerocket.application.charts import chart_for
from cinerocket.application.keys import cache_key
from cinerocket.application.ports import ResponseCache, SessionStore
from cinerocket.domain.errors import AgentFailureError, LLMUnavailableError, SessionNotFoundError
from cinerocket.domain.models import AgentAnswer, ChatResponse, QueryResult, UsageStats
from cinerocket.guardrails.input import QuestionGuard

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ServicePolicy:
    request_limit: int
    history_max_turns: int


class AnalyticsService:
    def __init__(
        self,
        agent: AnalystAgent,
        deps_factory: Callable[[], AgentDeps],
        sessions: SessionStore,
        cache: ResponseCache,
        question_guard: QuestionGuard,
        policy: ServicePolicy,
        cache_scope: Callable[[], tuple[str, ...]],
    ) -> None:
        self._agent = agent
        self._deps_factory = deps_factory
        self._sessions = sessions
        self._cache = cache
        self._question_guard = question_guard
        self._policy = policy
        self._cache_scope = cache_scope

    async def ask(self, question: str, session_id: str | None = None) -> ChatResponse:
        cleaned = self._question_guard.clean(question)
        session_id = session_id or uuid.uuid4().hex
        history = self._sessions.load_messages(session_id)
        key = cache_key(cleaned, *self._cache_scope())
        if not history and (cached := self._cache.get(key)) is not None:
            logger.info("Resposta servida do cache para a sessão %s", session_id)
            response = cached.model_copy(
                update={
                    "session_id": session_id,
                    "question": cleaned,
                    "cached": True,
                    "usage": UsageStats(),
                    "created_at": datetime.now(UTC),
                }
            )
            self._remember(session_id, self._replay(cleaned, response), response)
            return response

        deps = self._deps_factory()
        answer, messages, usage, model_name = await self._run_agent(cleaned, deps, history)
        result = await self._final_result(answer, deps)
        response = ChatResponse(
            session_id=session_id,
            question=cleaned,
            answer=answer.answer,
            sql=result.sql if result else None,
            result=result,
            chart=chart_for(answer.chart, result) if result else None,
            assumptions=answer.assumptions,
            out_of_scope=answer.out_of_scope,
            model=model_name,
            usage=usage,
            created_at=datetime.now(UTC),
        )
        self._remember(session_id, messages, response)
        if not history and not answer.out_of_scope:
            self._cache.set(key, response)
        return response

    def clear_cache(self) -> int:
        return self._cache.clear()

    def transcript(self, session_id: str) -> list[ChatResponse]:
        turns = self._sessions.transcript(session_id)
        if not turns:
            raise SessionNotFoundError(f"Sessão '{session_id}' não encontrada.")
        return turns

    def reset(self, session_id: str) -> None:
        if not self._sessions.delete(session_id):
            raise SessionNotFoundError(f"Sessão '{session_id}' não encontrada.")

    async def _run_agent(
        self, question: str, deps: AgentDeps, history: list[ModelMessage]
    ) -> tuple[AgentAnswer, list[ModelMessage], UsageStats, str | None]:
        try:
            run = await self._agent.run(
                question,
                deps=deps,
                message_history=history or None,
                usage_limits=UsageLimits(request_limit=self._policy.request_limit),
            )
        except UsageLimitExceeded as error:
            raise AgentFailureError(
                "O agente atingiu o limite de etapas sem chegar a uma resposta. Reformule a pergunta "
                "com mais detalhes."
            ) from error
        except (FallbackExceptionGroup, ModelAPIError) as error:
            raise LLMUnavailableError(describe_provider_failure(error)) from error
        except UnexpectedModelBehavior as error:
            raise AgentFailureError(f"O modelo respondeu de forma inesperada: {error.message}") from error
        usage = UsageStats(
            requests=run.usage.requests,
            input_tokens=run.usage.input_tokens,
            output_tokens=run.usage.output_tokens,
        )
        return run.output, run.all_messages(), usage, run.response.model_name

    @staticmethod
    async def _final_result(answer: AgentAnswer, deps: AgentDeps) -> QueryResult | None:
        if answer.out_of_scope or not answer.sql:
            return None
        sql = answer.sql
        return await anyio.to_thread.run_sync(lambda: deps.execute(sql))

    def _remember(self, session_id: str, messages: list[ModelMessage], response: ChatResponse) -> None:
        trimmed = keep_recent_turns(messages, self._policy.history_max_turns)
        self._sessions.save_turn(session_id, trimmed, response)

    @staticmethod
    def _replay(question: str, response: ChatResponse) -> list[ModelMessage]:
        content = (
            response.answer if not response.sql else f"{response.answer}\n\nSQL utilizado:\n{response.sql}"
        )
        return [
            ModelRequest(parts=[UserPromptPart(content=question)]),
            ModelResponse(parts=[TextPart(content=content)], model_name=response.model),
        ]


def describe_provider_failure(error: Exception) -> str:
    failures = list(error.exceptions) if isinstance(error, FallbackExceptionGroup) else [error]
    statuses = {failure.status_code for failure in failures if isinstance(failure, ModelHTTPError)}
    if statuses == {429}:
        return (
            "Todos os modelos estão com limite de requisições atingido (429). Aguarde alguns minutos ou "
            "verifique a cota diária do OpenRouter."
        )
    if statuses & {401, 403}:
        return "Credenciais de LLM inválidas. Verifique OPENROUTER_API_KEY e GOOGLE_API_KEY no .env."
    detail = "; ".join(str(failure) for failure in failures)[:500]
    return f"Nenhum modelo de linguagem disponível no momento. Detalhes: {detail}"
