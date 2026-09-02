"""Paths, constants and domain vocabulary for SchemeSetu."""

from __future__ import annotations

from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parent.parent
SCHEMES_CSV: Final = ROOT / "data" / "schemes.csv"
STATES_GEOJSON: Final = ROOT / "data" / "india_states.geojson"

APP_NAME: Final = "SchemeSetu"
APP_TAGLINE: Final = "Bridging citizens to state welfare entitlements"

# 'Any' means the scheme places no gender restriction, so it matches every
# applicant. It is a value in the data, not a choice we offer the user.
GENDER_ANY: Final = "Any"
GENDER_CHOICES: Final = ("Female", "Male", "Other")

# The source data contains 'EWC', which is not a category the Government of
# India recognises -- the five reservation categories are SC, ST, OBC, EWS and
# General. It is a data-entry slip for 'EWS' (13 rows). We normalise on load
# rather than editing the CSV, so the raw source stays byte-identical to what
# was collected and the correction stays visible and testable.
CATEGORY_CORRECTIONS: Final = {"EWC": "EWS"}

CANONICAL_CATEGORIES: Final = ("GENERAL", "OBC", "SC", "ST", "EWS")

INCOME_MIN: Final = 0
INCOME_MAX: Final = 600_000
INCOME_STEP: Final = 10_000
INCOME_DEFAULT: Final = 250_000

REQUIRED_COLUMNS: Final = (
    "Scheme Name",
    "State",
    "Category",
    "Gender",
    "Max Annual Income",
    "Benefit",
)
