"""Loading and validation of the scheme table and state geometries.

Everything here is pure I/O plus normalisation; the Streamlit caching wrappers
live in `schemesetu.cache` so these functions stay importable from tests and
scripts without a Streamlit runtime.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import (
    CATEGORY_CORRECTIONS,
    REQUIRED_COLUMNS,
    SCHEMES_CSV,
    STATES_GEOJSON,
)


class DataValidationError(RuntimeError):
    """Raised when the scheme table is missing columns or structurally wrong."""


def load_schemes(path: Path | None = None) -> pd.DataFrame:
    """Read the scheme table, validate its shape and normalise its vocabulary."""
    df = pd.read_csv(path or SCHEMES_CSV)

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise DataValidationError(f"schemes.csv is missing columns: {missing}")

    # Trailing whitespace in state names silently breaks the join against the
    # GeoJSON, and the failure looks like "state has no schemes" rather than an
    # error, so we normalise before anything downstream sees the data.
    for column in ("Scheme Name", "State", "Category", "Gender"):
        df[column] = df[column].astype(str).str.strip()

    df["State"] = df["State"].str.upper()
    df["Category"] = df["Category"].str.upper().replace(CATEGORY_CORRECTIONS)

    for column in ("Max Annual Income", "Benefit"):
        df[column] = pd.to_numeric(df[column], errors="coerce")

    invalid = df["Max Annual Income"].isna() | df["Benefit"].isna()
    if invalid.any():
        raise DataValidationError(
            f"{int(invalid.sum())} row(s) have non-numeric income or benefit"
        )

    return df.reset_index(drop=True)


def load_states_geojson(path: Path | None = None) -> dict:
    """Read the pre-built state boundaries produced by scripts/build_geodata.py."""
    target = path or STATES_GEOJSON
    if not target.exists():
        raise FileNotFoundError(
            f"{target} not found -- run `python scripts/build_geodata.py` first"
        )
    return json.loads(target.read_text())


def geojson_state_names(geojson: dict) -> set[str]:
    """The set of state names the map can actually draw."""
    return {feature["id"] for feature in geojson["features"]}
