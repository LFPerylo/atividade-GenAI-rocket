import math
import unicodedata
from collections import defaultdict, deque
from collections.abc import Sequence

from pydantic import BaseModel

from cinerocket.domain.models import CellValue, QueryResult
from cinerocket.evaluation.dataset import EvalCase

Key = tuple[str, ...]


class Comparison(BaseModel):
    passed: bool
    score: float
    detail: str


def normalize(value: CellValue) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return f"{value:.2f}"
    return unicodedata.normalize("NFKC", str(value)).strip().casefold()


def as_number(value: CellValue) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return None


def column(
    result: QueryResult, index: int, rows: Sequence[Sequence[CellValue]] | None = None
) -> list[CellValue]:
    return [row[index] for row in (rows if rows is not None else result.rows)]


def best_key_column(expected: list[CellValue], actual: QueryResult, used: set[int]) -> int | None:
    targets = {normalize(value) for value in expected}
    scores = {
        index: len(targets & {normalize(value) for value in column(actual, index)})
        for index in range(len(actual.columns))
        if index not in used
    }
    best = max(scores, key=lambda index: scores[index], default=None)
    return best if best is not None and scores[best] > 0 else None


def values_match(expected: CellValue, actual: CellValue, tolerance: float) -> bool:
    left, right = as_number(expected), as_number(actual)
    if left is None or right is None:
        return normalize(expected) == normalize(actual)
    return math.isclose(left, right, rel_tol=tolerance, abs_tol=0.01)


def compare_results(case: EvalCase, expected: QueryResult, actual: QueryResult | None) -> Comparison:
    if actual is None or not actual.rows:
        return Comparison(passed=False, score=0.0, detail="O agente não retornou linhas.")
    if not expected.rows:
        return Comparison(passed=False, score=0.0, detail="A consulta de referência não retornou linhas.")

    mapping: dict[int, int] = {}
    for key in case.key_columns:
        match = best_key_column(column(expected, key), actual, set(mapping.values()))
        if match is None:
            return Comparison(
                passed=False,
                score=0.0,
                detail=f"Coluna '{expected.columns[key]}' não encontrada na resposta.",
            )
        mapping[key] = match

    window = actual.rows[: len(expected.rows)] if case.ordered else actual.rows
    actual_rows: defaultdict[Key, deque[Sequence[CellValue]]] = defaultdict(deque)
    for row in window:
        actual_rows[tuple(normalize(row[mapping[index]]) for index in case.key_columns)].append(row)
    matched: list[tuple[Sequence[CellValue], Sequence[CellValue]]] = []
    for row in expected.rows:
        candidates = actual_rows.get(tuple(normalize(row[index]) for index in case.key_columns))
        if candidates:
            matched.append((row, candidates.popleft()))
    overlap = len(matched) / len(expected.rows)
    value_score = _value_score(case, matched, len(actual.columns), set(mapping.values()))
    score = round(overlap * value_score, 4)
    passed = overlap >= case.min_overlap and value_score >= case.min_overlap
    detail = f"{len(matched)}/{len(expected.rows)} chaves encontradas"
    if case.value_columns:
        detail += f", valores conferem em {value_score:.0%}"
    return Comparison(passed=passed, score=score, detail=detail)


def _value_score(
    case: EvalCase,
    matched: list[tuple[Sequence[CellValue], Sequence[CellValue]]],
    actual_width: int,
    used: set[int],
) -> float:
    if not case.value_columns:
        return 1.0
    if not matched:
        return 0.0
    scores = []
    for value_index in case.value_columns:
        candidates = [index for index in range(actual_width) if index not in used]
        hits = [
            sum(
                values_match(expected[value_index], actual[candidate], case.value_tolerance)
                for expected, actual in matched
            )
            for candidate in candidates
        ]
        scores.append(max(hits, default=0) / len(matched))
    return sum(scores) / len(scores)
