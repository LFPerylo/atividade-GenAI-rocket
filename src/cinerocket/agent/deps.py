from dataclasses import dataclass, field
from datetime import date

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
    executed: dict[str, QueryResult] = field(default_factory=dict)

    def execute(self, sql: str) -> QueryResult:
        key = normalize_sql(sql)
        if key not in self.executed:
            self.executed[key] = self.executor.execute(sql)
        return self.executed[key]
