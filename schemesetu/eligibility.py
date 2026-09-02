"""The eligibility rules and per-state aggregation.

These are the functions that decide what a citizen is entitled to, so they are
kept pure -- DataFrame in, DataFrame out, no Streamlit, no I/O -- and are the
part of the codebase covered by tests.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import GENDER_ANY


@dataclass(frozen=True)
class Applicant:
    """The citizen we are testing schemes against.

    `categories` and `states` are empty when the user has applied no filter,
    which we read as "no restriction" rather than "match nothing".
    """

    annual_income: int
    gender: str | None = None
    categories: tuple[str, ...] = ()
    states: tuple[str, ...] = ()


def filter_schemes(schemes: pd.DataFrame, applicant: Applicant) -> pd.DataFrame:
    """Return the schemes `applicant` qualifies for.

    A scheme matches when the applicant's income is at or below the scheme's
    income ceiling, and the scheme's category and gender restrictions (if any)
    admit the applicant.
    """
    eligible = schemes["Max Annual Income"] >= applicant.annual_income

    if applicant.gender:
        eligible &= schemes["Gender"].isin([applicant.gender, GENDER_ANY])

    if applicant.categories:
        eligible &= schemes["Category"].isin(applicant.categories)

    if applicant.states:
        eligible &= schemes["State"].isin(applicant.states)

    return schemes[eligible].reset_index(drop=True)


def summarise_by_state(eligible: pd.DataFrame) -> pd.DataFrame:
    """Collapse eligible schemes to one row per state, for the choropleth.

    Produces the total benefit, the scheme count, and an HTML-broken list of
    scheme names used as the map's hover text.
    """
    columns = ["State", "Total Benefit", "Scheme Count", "Scheme Details"]
    if eligible.empty:
        return pd.DataFrame(columns=columns)

    grouped = eligible.groupby("State", as_index=False).agg(
        **{
            "Total Benefit": ("Benefit", "sum"),
            "Scheme Count": ("Scheme Name", "size"),
        }
    )

    # Built from the same groupby rather than a second .apply() so the row
    # order is guaranteed to line up on merge.
    details = (
        eligible.assign(
            _line=lambda d: d["Scheme Name"] + ": " + d["Benefit"].map("₹{:,.0f}".format)
        )
        .groupby("State", as_index=False)["_line"]
        .agg("<br>".join)
        .rename(columns={"_line": "Scheme Details"})
    )

    return grouped.merge(details, on="State", how="left")[columns]


def align_to_map(summary: pd.DataFrame, state_names: set[str]) -> pd.DataFrame:
    """Expand `summary` to every state on the map, zero-filling the rest.

    Without this a state with no eligible schemes is simply absent from the
    trace and renders as a hole in the map, which reads as missing data rather
    than as a real "nothing here" answer.
    """
    frame = pd.DataFrame({"State": sorted(state_names)}).merge(
        summary, on="State", how="left"
    )
    frame["Total Benefit"] = frame["Total Benefit"].fillna(0).astype(int)
    frame["Scheme Count"] = frame["Scheme Count"].fillna(0).astype(int)
    frame["Scheme Details"] = frame["Scheme Details"].fillna("No schemes available")
    return frame


def headline_metrics(eligible: pd.DataFrame) -> dict[str, int]:
    """The numbers shown above the map."""
    return {
        "schemes": len(eligible),
        "states": int(eligible["State"].nunique()) if not eligible.empty else 0,
        "total_benefit": int(eligible["Benefit"].sum()) if not eligible.empty else 0,
        "best_benefit": int(eligible["Benefit"].max()) if not eligible.empty else 0,
    }
