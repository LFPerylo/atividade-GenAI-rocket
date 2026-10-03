from cinerocket.application.charts import chart_for, infer_chart
from cinerocket.domain.models import ChartSpec, QueryResult


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


def test_swaps_axes_when_model_inverts_them() -> None:
    result = QueryResult(sql="", columns=["genero", "lucro"], rows=[["Drama", 10.5], ["Horror", 4.0]])
    inverted = ChartSpec(kind="horizontal_bar", x="lucro", y="genero", title="Lucro")

    chart = chart_for(inverted, result)

    assert chart is not None
    assert (chart.x, chart.y) == ("genero", "lucro")


def test_inferred_chart_title_uses_readable_labels() -> None:
    result = QueryResult(sql="", columns=["titulo", "receita_brl"], rows=[["Duna", 2.0], ["Barbie", 7.0]])

    chart = infer_chart(result)

    assert chart is not None and chart.title == "Receita (R$) por título"
