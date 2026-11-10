"""Every repo path in one place. Assumes a source checkout (`pip install -e .`): the data lives in the repo."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

DATA = REPO / "data" / "raw"
FLIGHTS = DATA / "dot2015" / "flights.csv"
AIRPORTS = DATA / "dot2015" / "airports.csv"
WORKBOOK = DATA / "challenge2" / "challenge-2-operational-constraints.xlsx"

RESULTS = REPO / "results"
LOGS = REPO / "logs"
DOCS = REPO / "docs"
