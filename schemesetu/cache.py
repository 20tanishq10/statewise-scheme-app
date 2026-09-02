"""Streamlit-cached wrappers around the pure loaders in `schemesetu.data`.

Kept separate so `data.py` and `eligibility.py` import cleanly under pytest and
in scripts, with no Streamlit runtime required.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from . import data


@st.cache_data(show_spinner=False)
def load_schemes() -> pd.DataFrame:
    return data.load_schemes()


@st.cache_data(show_spinner=False)
def load_states_geojson() -> dict:
    return data.load_states_geojson()
