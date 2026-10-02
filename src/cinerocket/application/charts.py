from cinerocket.domain.models import ChartSpec, QueryResult

MAX_CHART_ROWS = 25
TEMPORAL_TOKENS = frozenset({"ano", "year", "mes", "month", "data", "date", "dia", "day"})


def is_numeric_column(result: QueryResult, index: int) -> bool:
    values = [row[index] for row in result.rows if row[index] is not None]
    return bool(values) and all(isinstance(value, int | float) for value in values)


def infer_chart(result: QueryResult) -> ChartSpec | None:
    if len(result.columns) != 2 or not 2 <= result.row_count <= MAX_CHART_ROWS:
        return None
    label, value = result.columns
    if not is_numeric_column(result, 1):
        return None
    if TEMPORAL_TOKENS & set(label.lower().split("_")) and is_numeric_column(result, 0):
        return ChartSpec(kind="line", x=label, y=value, title=f"{value} por {label}")
    return ChartSpec(kind="horizontal_bar", x=label, y=value, title=f"{value} por {label}")


def align_chart(spec: ChartSpec | None, result: QueryResult) -> ChartSpec | None:
    if spec is None or not {spec.x, spec.y} <= set(result.columns):
        return None
    x_index, y_index = result.columns.index(spec.x), result.columns.index(spec.y)
    if is_numeric_column(result, y_index):
        return spec
    if is_numeric_column(result, x_index):
        return spec.model_copy(update={"x": spec.y, "y": spec.x})
    return None


def chart_for(spec: ChartSpec | None, result: QueryResult) -> ChartSpec | None:
    return align_chart(spec, result) or infer_chart(result)
