import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from cinerocket.application.service import AnalyticsService
from cinerocket.database.executor import QueryExecutor
from cinerocket.domain.errors import CineRocketError
from cinerocket.evaluation.compare import compare_results
from cinerocket.evaluation.dataset import EvalCase

logger = logging.getLogger(__name__)


class CaseResult(BaseModel):
    case_id: str
    category: str
    question: str
    passed: bool
    score: float
    detail: str
    agent_sql: str | None = None
    cached: bool = False
    model_requests: int = 0
    error: str | None = None


class EvaluationReport(BaseModel):
    started_at: datetime
    finished_at: datetime | None = None
    results: list[CaseResult] = Field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return sum(result.passed for result in self.results) / len(self.results) if self.results else 0.0

    @property
    def model_requests(self) -> int:
        return sum(result.model_requests for result in self.results)

    def save(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"report-{self.started_at:%Y%m%d-%H%M%S}.json"
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return path


class EvaluationRunner:
    def __init__(self, service: AnalyticsService, executor: QueryExecutor) -> None:
        self._service = service
        self._executor = executor

    async def run(
        self,
        cases: list[EvalCase],
        delay_seconds: float = 0,
        on_result: Callable[[CaseResult], None] | None = None,
    ) -> EvaluationReport:
        report = EvaluationReport(started_at=datetime.now(UTC))
        for position, case in enumerate(cases):
            result = await self._evaluate(case)
            report.results.append(result)
            if on_result is not None:
                on_result(result)
            if delay_seconds and position < len(cases) - 1 and not result.cached:
                await asyncio.sleep(delay_seconds)
        report.finished_at = datetime.now(UTC)
        return report

    async def _evaluate(self, case: EvalCase) -> CaseResult:
        base = {"case_id": case.id, "category": case.category, "question": case.question}
        expected = await asyncio.to_thread(self._executor.execute, case.reference_sql)
        try:
            response = await self._service.ask(case.question)
        except CineRocketError as error:
            logger.warning("Falha no caso %s: %s", case.id, error)
            return CaseResult(**base, passed=False, score=0.0, detail="Erro do agente", error=str(error))
        comparison = compare_results(case, expected, response.result)
        return CaseResult(
            **base,
            passed=comparison.passed,
            score=comparison.score,
            detail=comparison.detail,
            agent_sql=response.sql,
            cached=response.cached,
            model_requests=response.usage.requests,
        )
