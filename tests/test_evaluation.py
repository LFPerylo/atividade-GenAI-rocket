from cinerocket.domain.models import QueryResult
from cinerocket.evaluation.compare import compare_results
from cinerocket.evaluation.dataset import EvalCase, load_cases

EXPECTED = QueryResult(sql="", columns=["titulo", "receita"], rows=[["Barbie", 7000.0], ["Duna", 2000.0]])


def case(**overrides: object) -> EvalCase:
    return EvalCase.model_validate(
        {"id": "c", "category": "c", "question": "q", "reference_sql": "SELECT 1", "value_columns": [1]}
        | overrides
    )


def test_matches_by_content_regardless_of_column_names_and_order() -> None:
    actual = QueryResult(
        sql="", columns=["receita_total_brl", "filme"], rows=[[7000.004, "barbie"], [2000, "Duna"], [10, "X"]]
    )

    comparison = compare_results(case(), EXPECTED, actual)

    assert comparison.passed is True
    assert comparison.score == 1.0


def test_fails_when_values_diverge() -> None:
    actual = QueryResult(sql="", columns=["titulo", "receita"], rows=[["Barbie", 1.0], ["Duna", 2.0]])

    assert compare_results(case(), EXPECTED, actual).passed is False


def test_dataset_is_valid() -> None:
    assert len(load_cases()) == 14
