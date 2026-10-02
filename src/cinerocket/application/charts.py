from cinerocket.domain.models import ChartSpec, QueryResult

MAX_CHART_ROWS = 25
TEMPORAL_HINTS = ("ano", "year", "mes", "data", "date")


def is_numeric_column(result: QueryResult, index: int) -> bool:
    values = [row[index] for row in result.rows if row[index] is not None]
    return bool(values) and all(isinstance(value, int | float) for value in values)


def infer_chart(result: QueryResult) -> ChartSpec | None:
    if len(result.columns) != 2 or not 2 <= result.row_count <= MAX_CHART_ROWS:
        return None
    label, value = result.columns
    if not is_numeric_column(result, 1):
        return None
    if any(hint in label.lower() for hint in TEMPORAL_HINTS) and is_numeric_column(result, 0):
        return ChartSpec(kind="line", x=label, y=value, title=f"{value} por {label}")
    return ChartSpec(kind="horizontal_bar", x=label, y=value, title=f"{value} por {label}")
