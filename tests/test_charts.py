"""The house style holds: the chart helpers draw what design.md promises.

These run without the database. They guard the rules every view relies on,
so a change to dashboard/charts.py that breaks one shows up here first.
"""

import pandas as pd
from streamlit.testing.v1 import AppTest

from dashboard import charts

GENRES = pd.DataFrame(
    {"genre": ["Jazz", "Rock", "Latin", "Metal"], "revenue": [80.0, 830.0, 380.0, 260.0]}
)


def test_numbers_are_written_the_house_way():
    assert charts.fmt(1234.4, "money") == "$1,234"
    assert charts.fmt(5.65, "money") == "$5.65"  # small amounts keep their cents
    assert charts.fmt(1234, "count") == "1,234"
    assert charts.fmt(0.1234, "percent") == "12.3%"


def test_ranked_bar_puts_the_largest_on_top_in_the_accent():
    fig = charts.ranked_bar(GENRES, "genre", "revenue")
    bar = fig.data[0]
    assert fig.layout.yaxis.categoryorder == "total ascending"  # largest drawn on top
    assert list(bar.y) == ["Rock", "Latin", "Metal", "Jazz"]
    assert list(bar.marker.color) == [charts.ACCENT] + [charts.NEUTRAL] * 3


def test_ranked_bar_can_highlight_another_item():
    fig = charts.ranked_bar(GENRES, "genre", "revenue", highlight="Jazz")
    colors = dict(zip(fig.data[0].y, fig.data[0].marker.color))
    assert colors["Jazz"] == charts.ACCENT
    assert colors["Rock"] == charts.NEUTRAL


def test_ranked_bar_keeps_only_the_top_items():
    fig = charts.ranked_bar(GENRES, "genre", "revenue", top=2)
    assert list(fig.data[0].y) == ["Rock", "Latin"]


def test_trend_line_labels_the_latest_value():
    months = pd.DataFrame(
        {"month": pd.to_datetime(["2026-02-01", "2026-01-01"]), "orders": [120, 100]}
    )
    fig = charts.trend_line(months, "month", "orders", kind="count")
    assert fig.layout.annotations[0].text == "120"


def test_kpi_row_shows_each_tile_with_its_comparison():
    def page():
        from dashboard import charts

        charts.kpi_row(
            [
                {"label": "Revenue", "value": 2328.6, "kind": "money", "delta": 12.9, "versus": "vs last year"},
                {"label": "Customers", "value": 59, "kind": "count"},
            ]
        )

    app = AppTest.from_function(page).run()
    assert [m.value for m in app.metric] == ["$2,329", "59"]
    assert app.metric[0].delta == "+$13 vs last year"
