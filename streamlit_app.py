"""The dashboard's screens. Run it with:  streamlit run streamlit_app.py

This page is the template's starting point. It proves the connection works
and shows one example chart on vinyl_vault. Replace it with the screens your
spec describes; keep every query in dashboard/metrics.py.

Rule for a public app on a shared login: no box where a viewer can type SQL.
Filters (dropdowns, sliders, dates) pass values to the queries as parameters.
"""

import plotly.express as px
import streamlit as st

from dashboard import db, metrics

st.set_page_config(page_title="Dashboard", layout="wide")


# Cached for ten minutes: every viewer shares one answer instead of each
# sending the same query to the server.
@st.cache_data(ttl=600)
def load_about():
    return metrics.about(db.get_engine())


@st.cache_data(ttl=600)
def load_revenue_by_genre():
    return metrics.revenue_by_genre(db.get_engine())


st.title("Dashboard Starter")

about = load_about()
st.success(f"Connected to **{about.loc[0, 'display_name']}**: {about.loc[0, 'description']}")

if db.get_engine().url.database == "vinyl_vault":
    revenue = load_revenue_by_genre()
    top = revenue.iloc[0]
    st.subheader(f"{top['genre']} earns the most: ${float(top['revenue']):,.2f}")
    chart = px.bar(
        revenue.head(10),
        x="revenue",
        y="genre",
        orientation="h",
        labels={"revenue": "Revenue ($)", "genre": ""},
    )
    chart.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(chart, width="stretch")
else:
    st.info("Your database is connected. Build the screens your spec describes here.")
