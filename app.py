"""SchemeSetu -- Streamlit entrypoint.

Deliberately thin: it reads widget state, calls into `schemesetu`, and renders.
All eligibility logic lives in `schemesetu.eligibility` so it can be tested
without spinning up a Streamlit session.
"""

from __future__ import annotations

import streamlit as st

from schemesetu import cache, eligibility
from schemesetu.config import (
    APP_NAME,
    APP_TAGLINE,
    CANONICAL_CATEGORIES,
    GENDER_CHOICES,
    INCOME_DEFAULT,
    INCOME_MAX,
    INCOME_MIN,
    INCOME_STEP,
)
from schemesetu.data import geojson_state_names
from schemesetu.viz import build_choropleth, build_state_ranking

st.set_page_config(
    page_title=f"{APP_NAME} · Scheme Eligibility Explorer",
    page_icon="🪷",
    layout="wide",
)


def sidebar_controls(schemes) -> eligibility.Applicant:
    """Collect applicant details. Returns immediately -- no submit gate.

    The original build hid every result behind a form submit, so the first
    thing a visitor saw was an empty page. Filters now apply live and the map
    is populated on load.
    """
    with st.sidebar:
        st.header("Your details")

        income = st.slider(
            "Annual household income (₹)",
            min_value=INCOME_MIN,
            max_value=INCOME_MAX,
            value=INCOME_DEFAULT,
            step=INCOME_STEP,
            help="Schemes are shown when their income ceiling is at or above this.",
        )
        gender = st.radio("Gender", GENDER_CHOICES, horizontal=True)

        available = [c for c in CANONICAL_CATEGORIES if c in set(schemes["Category"])]
        categories = st.multiselect(
            "Category", available, help="Leave empty to include every category."
        )

        states = st.multiselect(
            "State / UT",
            sorted(schemes["State"].unique()),
            help="Leave empty to see the whole country.",
        )

        st.divider()
        st.caption(
            "Demonstration data. Verify eligibility on the official state "
            "portal before applying."
        )

    return eligibility.Applicant(
        annual_income=income,
        gender=gender,
        categories=tuple(categories),
        states=tuple(states),
    )


def render_metrics(metrics: dict[str, int]) -> None:
    schemes_col, states_col, total_col, best_col = st.columns(4)
    schemes_col.metric("Schemes matched", f"{metrics['schemes']:,}")
    states_col.metric("States covered", f"{metrics['states']:,}")
    total_col.metric("Combined benefit", f"₹{metrics['total_benefit']:,}")
    best_col.metric("Largest single benefit", f"₹{metrics['best_benefit']:,}")


def main() -> None:
    schemes = cache.load_schemes()
    geojson = cache.load_states_geojson()

    st.title(f"🪷 {APP_NAME}")
    st.caption(APP_TAGLINE)

    applicant = sidebar_controls(schemes)
    eligible = eligibility.filter_schemes(schemes, applicant)
    metrics = eligibility.headline_metrics(eligible)

    render_metrics(metrics)
    st.divider()

    if eligible.empty:
        st.warning(
            "No schemes match these details. Try lowering the income figure -- "
            "a scheme applies when its ceiling is at or above your income."
        )
        return

    summary = eligibility.summarise_by_state(eligible)
    map_frame = eligibility.align_to_map(summary, geojson_state_names(geojson))

    map_tab, table_tab, ranking_tab = st.tabs(
        ["Map", "Matched schemes", "State ranking"]
    )

    with map_tab:
        st.plotly_chart(
            build_choropleth(map_frame, geojson),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.caption("Hover a state to see the individual schemes behind its total.")

    with table_tab:
        st.dataframe(
            eligible[["Scheme Name", "State", "Category", "Gender", "Benefit"]]
            .sort_values("Benefit", ascending=False)
            .reset_index(drop=True),
            width="stretch",
            hide_index=True,
            # Scheme names are long and the code columns are short, so the
            # default even split wastes space on Category/Gender.
            column_config={
                "Scheme Name": st.column_config.TextColumn("Scheme", width="large"),
                "State": st.column_config.TextColumn("State", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Gender": st.column_config.TextColumn("Gender", width="small"),
                "Benefit": st.column_config.NumberColumn(
                    "Benefit", format="₹%d", width="small"
                ),
            },
        )
        st.download_button(
            "Download as CSV",
            eligible.to_csv(index=False).encode("utf-8"),
            file_name="schemesetu-matches.csv",
            mime="text/csv",
        )

    with ranking_tab:
        st.plotly_chart(
            build_state_ranking(summary),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.caption("Top 15 states by combined benefit for these details.")


if __name__ == "__main__":
    main()
