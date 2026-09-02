"""Tests over the real shipped data -- these guard the map join."""

from __future__ import annotations

import pandas as pd
import pytest

from schemesetu.config import CANONICAL_CATEGORIES, REQUIRED_COLUMNS
from schemesetu.data import (
    DataValidationError,
    geojson_state_names,
    load_schemes,
    load_states_geojson,
)


@pytest.fixture(scope="module")
def schemes() -> pd.DataFrame:
    return load_schemes()


@pytest.fixture(scope="module")
def geojson() -> dict:
    return load_states_geojson()


def test_required_columns_present(schemes):
    assert set(REQUIRED_COLUMNS).issubset(schemes.columns)


def test_every_state_in_the_csv_exists_on_the_map(schemes, geojson):
    """A mismatch here shows up in the UI as a silently empty state, not an error."""
    assert set(schemes["State"]) <= geojson_state_names(geojson)


def test_categories_are_canonical_after_load(schemes):
    """'EWC' in the source must be normalised to 'EWS' on load."""
    assert set(schemes["Category"]) <= set(CANONICAL_CATEGORIES)
    assert "EWC" not in set(schemes["Category"])


def test_geojson_ids_are_unique(geojson):
    ids = [feature["id"] for feature in geojson["features"]]
    assert len(ids) == len(set(ids))


def test_amounts_are_positive(schemes):
    assert (schemes["Benefit"] > 0).all()
    assert (schemes["Max Annual Income"] > 0).all()


def test_missing_column_raises(tmp_path):
    path = tmp_path / "broken.csv"
    path.write_text("Scheme Name,State\nAlpha,GOA\n")
    with pytest.raises(DataValidationError, match="missing columns"):
        load_schemes(path)


def test_non_numeric_benefit_raises(tmp_path):
    path = tmp_path / "broken.csv"
    path.write_text(
        "Scheme Name,State,Category,Gender,Max Annual Income,Benefit\n"
        "Alpha,GOA,OBC,Male,200000,not-a-number\n"
    )
    with pytest.raises(DataValidationError, match="non-numeric"):
        load_schemes(path)
