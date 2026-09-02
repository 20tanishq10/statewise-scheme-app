"""Tests for the eligibility rules -- the part that decides entitlements."""

from __future__ import annotations

import pandas as pd
import pytest

from schemesetu.eligibility import (
    Applicant,
    align_to_map,
    filter_schemes,
    headline_metrics,
    summarise_by_state,
)


@pytest.fixture
def schemes() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("Alpha", "GOA", "OBC", "Male", 200_000, 10_000),
            ("Beta", "GOA", "SC", "Any", 400_000, 20_000),
            ("Gamma", "KERALA", "OBC", "Female", 150_000, 5_000),
            ("Delta", "KERALA", "GENERAL", "Any", 500_000, 30_000),
        ],
        columns=[
            "Scheme Name",
            "State",
            "Category",
            "Gender",
            "Max Annual Income",
            "Benefit",
        ],
    )


def test_income_ceiling_is_inclusive(schemes):
    """A scheme capped at exactly the applicant's income still applies."""
    result = filter_schemes(schemes, Applicant(annual_income=200_000))
    assert "Alpha" in set(result["Scheme Name"])


def test_income_above_ceiling_excludes(schemes):
    result = filter_schemes(schemes, Applicant(annual_income=200_001))
    assert "Alpha" not in set(result["Scheme Name"])


def test_gender_any_matches_everyone(schemes):
    result = filter_schemes(schemes, Applicant(annual_income=0, gender="Other"))
    # Only the two 'Any' schemes; Male- and Female-restricted ones drop out.
    assert set(result["Scheme Name"]) == {"Beta", "Delta"}


def test_gender_specific_also_includes_any(schemes):
    result = filter_schemes(schemes, Applicant(annual_income=0, gender="Female"))
    assert set(result["Scheme Name"]) == {"Beta", "Gamma", "Delta"}


def test_empty_filters_mean_no_restriction(schemes):
    """Empty category/state tuples must not be read as 'match nothing'."""
    result = filter_schemes(schemes, Applicant(annual_income=0))
    assert len(result) == len(schemes)


def test_category_and_state_filters_combine(schemes):
    result = filter_schemes(
        schemes,
        Applicant(annual_income=0, categories=("OBC",), states=("KERALA",)),
    )
    assert set(result["Scheme Name"]) == {"Gamma"}


def test_summarise_totals_and_counts(schemes):
    summary = summarise_by_state(filter_schemes(schemes, Applicant(annual_income=0)))
    goa = summary.set_index("State").loc["GOA"]
    assert goa["Total Benefit"] == 30_000
    assert goa["Scheme Count"] == 2
    assert "Alpha: ₹10,000" in goa["Scheme Details"]


def test_summarise_handles_empty_input():
    empty = pd.DataFrame(
        columns=["Scheme Name", "State", "Category", "Gender", "Max Annual Income", "Benefit"]
    )
    summary = summarise_by_state(empty)
    assert summary.empty
    assert list(summary.columns) == [
        "State",
        "Total Benefit",
        "Scheme Count",
        "Scheme Details",
    ]


def test_align_to_map_zero_fills_missing_states(schemes):
    summary = summarise_by_state(
        filter_schemes(schemes, Applicant(annual_income=0, states=("GOA",)))
    )
    frame = align_to_map(summary, {"GOA", "KERALA", "PUNJAB"})
    assert len(frame) == 3
    punjab = frame.set_index("State").loc["PUNJAB"]
    assert punjab["Total Benefit"] == 0
    assert punjab["Scheme Details"] == "No schemes available"


def test_headline_metrics(schemes):
    metrics = headline_metrics(filter_schemes(schemes, Applicant(annual_income=0)))
    assert metrics == {
        "schemes": 4,
        "states": 2,
        "total_benefit": 65_000,
        "best_benefit": 30_000,
    }


def test_headline_metrics_on_empty_frame(schemes):
    metrics = headline_metrics(filter_schemes(schemes, Applicant(annual_income=10**9)))
    assert metrics == {"schemes": 0, "states": 0, "total_benefit": 0, "best_benefit": 0}
