import pandas as pd
import plotly.graph_objects as go

from cinerocket.domain.models import ChartSpec, QueryResult

SERIES_COLOR = "#008573"
SURFACE = "#FFFFFF"
INK = "#16191D"
INK_MUTED = "#5E646C"
GRID = "#ECEEEA"
FONT_FAMILY = "Archivo, system-ui, sans-serif"
MAX_POINTS = 25
ROW_HEIGHT = 28


def build_figure(spec: ChartSpec, result: QueryResult) -> go.Figure | None:
    frame = pd.DataFrame(result.rows, columns=result.columns)
    if spec.x not in frame or spec.y not in frame:
        return None
    frame[spec.y] = pd.to_numeric(frame[spec.y], errors="coerce")
    frame = frame.dropna(subset=[spec.y]).head(MAX_POINTS)
    if frame.empty:
        return None
    horizontal = spec.kind == "horizontal_bar"
    figure = go.Figure(_trace(spec, frame))
    figure.update_layout(
        title={"text": spec.title, "x": 0, "xanchor": "left", "font": {"size": 15, "color": INK}},
        font={"family": FONT_FAMILY, "size": 12, "color": INK_MUTED},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 8, "r": 16, "t": 48, "b": 8},
        height=max(320, ROW_HEIGHT * len(frame) + 96) if horizontal else 380,
        hoverlabel={"bgcolor": SURFACE, "bordercolor": GRID, "font": {"family": FONT_FAMILY, "color": INK}},
        bargap=0.35,
        showlegend=False,
        separators=",.",
    )
    value_axis = {"showgrid": True, "gridcolor": GRID, "zeroline": False, "title": None, "tickformat": "~s"}
    category_axis = {"showgrid": False, "zeroline": False, "linecolor": GRID, "title": None}
    if spec.kind in {"line", "scatter"}:
        category_axis = {**category_axis, "showgrid": spec.kind == "scatter", "gridcolor": GRID}
    figure.update_xaxes(value_axis if horizontal else category_axis)
    figure.update_yaxes(category_axis if horizontal else value_axis)
    return figure


def _hover_template(spec: ChartSpec, horizontal: bool) -> str:
    label, value = ("y", "x") if horizontal else ("x", "y")
    return f"<b>%{{{label}}}</b><br>{spec.y}: %{{{value}:,.2f}}<extra></extra>"


def _trace(spec: ChartSpec, frame: pd.DataFrame) -> go.Bar | go.Scatter:
    horizontal = spec.kind == "horizontal_bar"
    hover = _hover_template(spec, horizontal)
    marker_ring = {"color": SURFACE, "width": 2}
    if horizontal:
        ordered = frame.iloc[::-1]
        return go.Bar(
            x=ordered[spec.y],
            y=ordered[spec.x].astype(str),
            orientation="h",
            marker={"color": SERIES_COLOR, "cornerradius": 4},
            hovertemplate=hover,
        )
    if spec.kind == "line":
        return go.Scatter(
            x=frame[spec.x],
            y=frame[spec.y],
            mode="lines+markers",
            line={"color": SERIES_COLOR, "width": 2},
            marker={"size": 8, "color": SERIES_COLOR, "line": marker_ring},
            hovertemplate=hover,
        )
    if spec.kind == "scatter":
        return go.Scatter(
            x=frame[spec.x],
            y=frame[spec.y],
            mode="markers",
            marker={"size": 9, "color": SERIES_COLOR, "line": marker_ring},
            hovertemplate=hover,
        )
    return go.Bar(
        x=frame[spec.x].astype(str),
        y=frame[spec.y],
        marker={"color": SERIES_COLOR, "cornerradius": 4},
        hovertemplate=hover,
    )
