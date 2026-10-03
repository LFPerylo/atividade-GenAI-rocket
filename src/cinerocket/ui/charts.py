import pandas as pd
import plotly.graph_objects as go

from cinerocket.application.labels import humanize, scaled_title, value_scale
from cinerocket.domain.models import ChartSpec, QueryResult

SERIES_COLOR = "#008573"
SURFACE = "#FFFFFF"
INK = "#16191D"
INK_MUTED = "#5E646C"
GRID = "#ECEEEA"
FONT_FAMILY = "Archivo, system-ui, sans-serif"
MAX_POINTS = 25
ROW_HEIGHT = 28
AXIS_TITLE_FONT = {"size": 12, "color": INK_MUTED}


def build_figure(spec: ChartSpec, result: QueryResult) -> go.Figure | None:
    frame = pd.DataFrame(result.rows, columns=result.columns)
    if spec.x not in frame or spec.y not in frame:
        return None
    frame[spec.y] = pd.to_numeric(frame[spec.y], errors="coerce")
    frame = frame.dropna(subset=[spec.y]).head(MAX_POINTS)
    if frame.empty:
        return None
    horizontal = spec.kind == "horizontal_bar"
    factor, unit = value_scale(frame[spec.y])
    category_label, value_label = humanize(spec.x), humanize(spec.y)
    figure = go.Figure(_trace(spec, frame, factor, category_label, value_label))
    figure.update_layout(
        title={"text": spec.title, "x": 0, "xanchor": "left", "font": {"size": 15, "color": INK}},
        font={"family": FONT_FAMILY, "size": 12, "color": INK_MUTED},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 8, "r": 16, "t": 48, "b": 8},
        height=max(340, ROW_HEIGHT * len(frame) + 120) if horizontal else 400,
        hoverlabel={"bgcolor": SURFACE, "bordercolor": GRID, "font": {"family": FONT_FAMILY, "color": INK}},
        bargap=0.35,
        showlegend=False,
        separators=",.",
    )
    value_axis = {
        "showgrid": True,
        "gridcolor": GRID,
        "zeroline": False,
        "tickformat": ",.1~f",
        "title": {"text": scaled_title(value_label, unit), "font": AXIS_TITLE_FONT, "standoff": 12},
        "automargin": True,
    }
    category_axis = {
        "showgrid": spec.kind == "scatter",
        "gridcolor": GRID,
        "zeroline": False,
        "linecolor": GRID,
        "title": {"text": category_label, "font": AXIS_TITLE_FONT, "standoff": 16},
        "automargin": True,
    }
    if pd.api.types.is_numeric_dtype(frame[spec.x]):
        category_axis["tickformat"] = "d" if spec.kind == "line" else ",.1~f"
    figure.update_xaxes(value_axis if horizontal else category_axis)
    figure.update_yaxes(category_axis if horizontal else value_axis)
    return figure


def _hover_template(category_label: str, value_label: str, horizontal: bool) -> str:
    category = "%{y}" if horizontal else "%{x}"
    return f"<b>{category}</b><br>{value_label}: %{{customdata:,.2f}}<extra>{category_label}</extra>"


def _trace(
    spec: ChartSpec, frame: pd.DataFrame, factor: float, category_label: str, value_label: str
) -> go.Bar | go.Scatter:
    horizontal = spec.kind == "horizontal_bar"
    ordered = frame.iloc[::-1] if horizontal else frame
    values = ordered[spec.y]
    common = {
        "customdata": values,
        "hovertemplate": _hover_template(category_label, value_label, horizontal),
    }
    marker_ring = {"color": SURFACE, "width": 2}
    if horizontal:
        return go.Bar(
            x=values / factor,
            y=ordered[spec.x].astype(str),
            orientation="h",
            marker={"color": SERIES_COLOR, "cornerradius": 4},
            **common,
        )
    if spec.kind == "line":
        return go.Scatter(
            x=ordered[spec.x],
            y=values / factor,
            mode="lines+markers",
            line={"color": SERIES_COLOR, "width": 2},
            marker={"size": 8, "color": SERIES_COLOR, "line": marker_ring},
            **common,
        )
    if spec.kind == "scatter":
        return go.Scatter(
            x=ordered[spec.x],
            y=values / factor,
            mode="markers",
            marker={"size": 9, "color": SERIES_COLOR, "line": marker_ring},
            **common,
        )
    return go.Bar(
        x=ordered[spec.x].astype(str),
        y=values / factor,
        marker={"color": SERIES_COLOR, "cornerradius": 4},
        **common,
    )
