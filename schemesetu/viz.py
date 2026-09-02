"""Plotly figure construction for the state choropleth."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Sequential, perceptually uniform and colour-blind safe. Viridis reads
# "low = dark purple" which fights the intuition that dark = more money, so we
# use a light-to-dark green ramp where darker genuinely means a larger benefit.
COLOR_SCALE = "Greens"


def build_choropleth(frame: pd.DataFrame, geojson: dict) -> go.Figure:
    """Draw total benefit per state.

    `frame` must already cover every state on the map (see
    `eligibility.align_to_map`) so that zero-benefit states are drawn rather
    than left as holes.
    """
    figure = px.choropleth(
        frame,
        geojson=geojson,
        locations="State",
        featureidkey="id",
        color="Total Benefit",
        color_continuous_scale=COLOR_SCALE,
        projection="mercator",
        custom_data=["State", "Scheme Count", "Total Benefit", "Scheme Details"],
    )

    figure.update_traces(
        marker_line_color="rgba(255,255,255,0.55)",
        marker_line_width=0.5,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "%{customdata[1]} scheme(s) · ₹%{customdata[2]:,.0f} total"
            "<br><br>%{customdata[3]}<extra></extra>"
        ),
    )

    figure.update_geos(fitbounds="locations", visible=False)
    figure.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=620,
        dragmode=False,
        coloraxis_colorbar={"title": "Total<br>benefit (₹)", "thickness": 14},
        paper_bgcolor="rgba(0,0,0,0)",
        geo={"bgcolor": "rgba(0,0,0,0)"},
    )
    return figure


def build_state_ranking(summary: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Horizontal bar chart of the highest-benefit states.

    Deliberately not `st.bar_chart`: that re-sorts the axis alphabetically, so
    a "ranking" comes out in name order, and vertical bars force the state
    labels to rotate into illegibility.
    """
    ranked = summary.sort_values("Total Benefit", ascending=False).head(top_n)

    figure = px.bar(
        # Plotly draws the first category at the bottom, so reverse to put the
        # largest bar on top.
        ranked.iloc[::-1],
        x="Total Benefit",
        y="State",
        orientation="h",
        color="Total Benefit",
        color_continuous_scale=COLOR_SCALE,
        text="Total Benefit",
        custom_data=["Scheme Count"],
    )

    figure.update_traces(
        texttemplate="₹%{x:,.0f}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>₹%{x:,.0f} across "
            "%{customdata[0]} scheme(s)<extra></extra>"
        ),
    )
    figure.update_layout(
        height=max(320, 28 * len(ranked)),
        margin={"r": 80, "t": 10, "l": 10, "b": 10},
        coloraxis_showscale=False,
        xaxis={"title": None, "showticklabels": False, "showgrid": False},
        yaxis={"title": None},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure
