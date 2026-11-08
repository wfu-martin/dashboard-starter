"""Every headline, number tile, and chart on the dashboard, in one house style.

design.md states the style rules in words; this module is where they live in
code. Views call these helpers instead of drawing charts directly, so a view
built by any teammate, in any session, looks like the rest of the dashboard.
To change the look, change the rule in design.md and the matching line here
(and the theme in .streamlit/config.toml), never one view at a time.

Number kinds: "money" ($1,234, or $5.65 under $10), "count" (1,234),
"percent" (12.3%, from a fraction such as 0.123).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# The accent marks what the headline is about; everything else is neutral.
# Red is kept for a loss or a miss. The accent matches primaryColor in
# .streamlit/config.toml.
ACCENT = "#1F5FA8"
NEUTRAL = "#B4BAC1"
NEGATIVE = "#B23B3B"
TEXT = "#1F2933"

# d3 formats for chart labels, Python formats for headline numbers. Money
# under $10 keeps its cents: a $5.65 average order must not read as $6.
_D3 = {"money": "$,.0f", "count": ",.0f", "percent": ".1%", "cents": "$,.2f"}
_PY = {"money": "${:,.0f}", "count": "{:,.0f}", "percent": "{:.1%}", "cents": "${:,.2f}"}


def _kind(kind: str, largest: float) -> str:
    return "cents" if kind == "money" and abs(largest) < 10 else kind


def fmt(value, kind: str) -> str:
    """One number written the house way, for headlines and captions."""
    return _PY[_kind(kind, float(value))].format(float(value))


def headline(takeaway: str, note: str = "") -> None:
    """A section's headline: the takeaway as a sentence, then what it measures.

    takeaway: the answer, with its number ("Rock earns 35% of revenue").
    note: the metric, its period, and its filters, from the spec.
    """
    st.subheader(takeaway)
    if note:
        st.caption(note)


def kpi_row(tiles: list[dict]) -> None:
    """A row of headline numbers, each against a comparison.

    Each tile is {"label", "value", "kind"} plus, optionally, "delta" (the
    change against the comparison, same kind, written to the same precision
    as the value) and "versus" (what it is compared with, such as "vs last
    year").
    """
    for column, tile in zip(st.columns(len(tiles)), tiles):
        delta = None
        if tile.get("delta") is not None:
            sign = "+" if float(tile["delta"]) >= 0 else "-"
            precision = _kind(tile["kind"], float(tile["value"]))
            delta = sign + _PY[precision].format(abs(float(tile["delta"])))
            if tile.get("versus"):
                delta += f" {tile['versus']}"
        column.metric(tile["label"], fmt(tile["value"], tile["kind"]), delta)


def ranked_bar(
    df: pd.DataFrame,
    label: str,
    value: str,
    kind: str = "money",
    highlight: str | None = None,
    top: int = 10,
) -> go.Figure:
    """Items ranked by size: horizontal bars, largest at the top.

    The highlighted item (the largest, unless named) gets the accent color;
    the rest stay neutral. Each bar carries its value, so the chart needs no
    axis numbers or gridlines.
    """
    data = df.nlargest(top, value)
    focus = highlight if highlight is not None else data.iloc[0][label]
    colors = [ACCENT if item == focus else NEUTRAL for item in data[label]]
    d3 = _D3[_kind(kind, data[value].abs().max())]
    fig = px.bar(data, x=value, y=label, orientation="h")
    fig.update_traces(
        marker_color=colors,
        texttemplate=f"%{{x:{d3}}}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=f"%{{y}}: %{{x:{d3}}}<extra></extra>",
    )
    fig.update_yaxes(categoryorder="total ascending", title=None)
    fig.update_xaxes(visible=False, rangemode="tozero")
    return _house(fig, height=max(240, 34 * len(data) + 60))


def trend_line(df: pd.DataFrame, date: str, value: str, kind: str = "money") -> go.Figure:
    """Change over time: one line in the accent color, the latest value labeled."""
    data = df.sort_values(date)
    d3 = _D3[_kind(kind, data[value].abs().max())]
    fig = px.line(data, x=date, y=value)
    fig.update_traces(
        line={"color": ACCENT, "width": 3},
        hovertemplate=f"%{{x}}: %{{y:{d3}}}<extra></extra>",
    )
    last = data.iloc[-1]
    fig.add_annotation(
        x=last[date], y=last[value], text=fmt(last[value], kind),
        showarrow=False, xanchor="left", xshift=8, font={"color": ACCENT, "size": 14},
    )
    fig.update_xaxes(title=None, showgrid=False)
    fig.update_yaxes(title=None, tickformat=d3, gridcolor="#ECEEF1")
    return _house(fig, height=320)


def show(fig: go.Figure) -> None:
    """Put a chart on the page, full width, without the toolbar."""
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def nothing_to_show(what: str = "these filters") -> None:
    """The note shown when a filter leaves no rows."""
    st.info(f"No data for {what}. Widen the filters to see results.")


def _house(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height,
        margin={"l": 0, "r": 60, "t": 10, "b": 0},
        plot_bgcolor="white",
        paper_bgcolor="white",
        font={"color": TEXT, "size": 14},
        showlegend=False,
    )
    return fig
