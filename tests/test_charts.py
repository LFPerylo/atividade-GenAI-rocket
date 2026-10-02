from cinerocket.application.charts import infer_chart
from cinerocket.domain.models import QueryResult


def test_infers_bar_for_category_metric_pairs() -> None:
    result = QueryResult(sql="", columns=["genero", "filmes"], rows=[["Drama", 10], ["Horror", 4]])

    chart = infer_chart(result)

    assert chart is not None
    assert (chart.kind, chart.x, chart.y) == ("horizontal_bar", "genero", "filmes")


def test_infers_line_for_yearly_series_and_skips_wide_results() -> None:
    yearly = QueryResult(sql="", columns=["ano_lancamento", "nota"], rows=[[2020, 6.1], [2021, 6.3]])
    wide = QueryResult(sql="", columns=["a", "b", "c"], rows=[["x", 1, 2], ["y", 3, 4]])

    assert infer_chart(yearly) is not None and infer_chart(yearly).kind == "line"
    assert infer_chart(wide) is None
