"""Every repo path in one place. Assumes a source checkout (`pip install -e .`): the data lives in the repo."""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# The data directory is a setting: AUTONOMOUSPRIME_DATA_DIR (process environment) or the checkout's data/raw.
DATA = (
    Path(os.environ["AUTONOMOUSPRIME_DATA_DIR"])
    if os.environ.get("AUTONOMOUSPRIME_DATA_DIR")
    else REPO / "data" / "raw"
)
FLIGHTS = DATA / "dot2015" / "flights.csv"
AIRPORTS = DATA / "dot2015" / "airports.csv"
WORKBOOK = DATA / "challenge2" / "challenge-2-operational-constraints.xlsx"

RESULTS = REPO / "results"
LOGS = REPO / "logs"
CACHE = REPO / ".cache"
DOCS = REPO / "docs"
