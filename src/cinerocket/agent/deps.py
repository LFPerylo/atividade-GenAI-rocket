from dataclasses import dataclass, field
from datetime import date

from cinerocket.agent.examples import SqlExample
from cinerocket.database.catalog import SchemaCatalog
from cinerocket.database.executor import QueryExecutor
from cinerocket.domain.models import QueryResult
from cinerocket.semantic.search import SemanticSearch


def normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().rstrip(";").split())


@dataclass
class AgentDeps:
    catalog: SchemaCatalog
    executor: QueryExecutor
    semantic: SemanticSearch | None
    today: date
    preview_rows: int
    semantic_limit: int
    examples: list[SqlExample] = field(default_factory=list)
    executed: dict[str, QueryResult] = field(default_factory=dict)

    def was_executed(self, sql: str) -> bool:
        return normalize_sql(sql) in self.executed

    def execute(self, sql: str) -> QueryResult:
        key = normalize_sql(sql)
        if key not in self.executed:
            self.executed[key] = self.executor.execute(sql)
        return self.executed[key]
