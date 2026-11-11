"""The one flights.csv loader: cache, row order, outcome columns, and the hindsight boundary."""

import ast
import csv
from pathlib import Path

import pytest

from autonomousprime import paths
from autonomousprime.infra import data

HEADER = (
    "YEAR,MONTH,DAY,AIRLINE,FLIGHT_NUMBER,TAIL_NUMBER,ORIGIN_AIRPORT,DESTINATION_AIRPORT,"
    "DEPARTURE_TIME,ARRIVAL_DELAY,CANCELLED,CANCELLATION_REASON,WEATHER_DELAY"
)
ROWS = [
    "2015,1,2,AA,10,N1,DFW,ORD,0612,15,0,,20",
    "2015,1,1,UA,20,N2,ORD,DEN,0700,-3,0,,0",
    "2015,1,2,AA,11,N1,ORD,MIA,0900,40,0,,0",
    "2015,2,3,DL,30,N3,ATL,DFW,1000,7,0,,0",
    "2015,1,2,WN,40,N4,DEN,DFW,1100,9,0,,0",
]


@pytest.fixture
def csv_path(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CACHE", tmp_path / "cache")
    data._memo.clear()
    p = tmp_path / "flights.csv"
    p.write_text("\n".join([HEADER, *ROWS]) + "\n")
    return p


def test_day_is_file_order_exact_strings_no_outcomes(csv_path):
    rows = data.day(2015, 1, 2, path=csv_path)
    assert [(r["AIRLINE"], r["FLIGHT_NUMBER"]) for r in rows] == [("AA", "10"), ("AA", "11"), ("WN", "40")]
    assert rows[0]["WEATHER_DELAY"] == "20" and rows[0]["MONTH"] == "1"
    assert not set(rows[0]) & set(data.OUTCOME_COLUMNS)
    assert data.day(2015, 9, 9, path=csv_path) == []


def test_day_hands_out_fresh_dicts(csv_path):
    data.day(2015, 1, 2, path=csv_path)[0]["AIRLINE"] = "XX"
    assert data.day(2015, 1, 2, path=csv_path)[0]["AIRLINE"] == "AA"


def test_day_at_flight_tail_days(csv_path):
    assert [r["FLIGHT_NUMBER"] for r in data.day_at(2015, 1, 2, "ORD", path=csv_path)] == ["10", "11"]
    assert [r["FLIGHT_NUMBER"] for r in data.day_at(2015, 1, 2, "DFW", path=csv_path)] == ["10", "40"]
    assert data.flight(2015, 1, 2, "AA", "11", "ORD", path=csv_path)["TAIL_NUMBER"] == "N1"
    assert data.flight(2015, 1, 2, "AA", "99", "ORD", path=csv_path) is None
    assert [r["FLIGHT_NUMBER"] for r in data.tail(2015, 1, 2, "N1", path=csv_path)] == ["10", "11"]
    by_date = data.days(path=csv_path)
    assert list(by_date) == [(2015, 1, 2), (2015, 1, 1), (2015, 2, 3)]  # keys in file order
    assert [len(v) for v in by_date.values()] == [3, 1, 1]
    assert all(not set(r) & set(data.OUTCOME_COLUMNS) for v in by_date.values() for r in v)


def test_outcomes_only_outcome_columns(csv_path):
    o = data.outcomes(2015, 1, 2, "AA", "10", "DFW", path=csv_path)
    assert set(o) == {"DEPARTURE_TIME", "ARRIVAL_DELAY", "CANCELLED", "CANCELLATION_REASON"}  # those in the file
    assert o["ARRIVAL_DELAY"] == "15" and o["DEPARTURE_TIME"] == "0612" and o["CANCELLATION_REASON"] == ""
    assert "WEATHER_DELAY" not in o and "AIRLINE" not in o
    with pytest.raises(LookupError):
        data.outcomes(2015, 1, 2, "AA", "99", "DFW", path=csv_path)


def test_second_call_is_served_from_the_pickle(csv_path, monkeypatch):
    first = data.day(2015, 1, 2, path=csv_path)
    data._memo.clear()

    def boom(*a, **k):
        raise AssertionError("csv was parsed again")

    monkeypatch.setattr(csv, "DictReader", boom)
    assert data.day(2015, 1, 2, path=csv_path) == first
    assert len(data.days(path=csv_path)) == 3


def test_changed_csv_gets_a_new_cache_directory(csv_path):
    data.day(2015, 1, 2, path=csv_path)
    before = {p.name for p in (paths.CACHE / "flights").iterdir()}
    csv_path.write_text("\n".join([HEADER, *ROWS, "2015,1,2,AA,12,N5,DFW,ORD,1,1,0,,0"]) + "\n")
    assert len(data.day(2015, 1, 2, path=csv_path)) == 4
    after = {p.name for p in (paths.CACHE / "flights").iterdir()}
    assert len(after) == 2 and before < after
    assert not [n for n in after if ".tmp-" in n]


def test_real_file_day_matches_direct_csv_read():
    with open(paths.FLIGHTS, newline="") as f:
        want = [
            {k: v for k, v in r.items() if k not in data.OUTCOME_COLUMNS}
            for r in csv.DictReader(f)
            if (r["YEAR"], r["MONTH"], r["DAY"]) == ("2015", "4", "24")
        ]
    assert want and data.day(2015, 4, 24) == want


def _uses_outcomes(tree: ast.AST) -> bool:
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and (n.module or "").endswith("infra.data"):
            if any(a.name == "outcomes" for a in n.names):
                return True
        if isinstance(n, ast.Attribute) and n.attr == "outcomes":
            v = n.value
            if (isinstance(v, ast.Name) and v.id == "data") or (isinstance(v, ast.Attribute) and v.attr == "data"):
                return True
    return False


def test_only_evaluation_reads_outcomes():
    src = Path(paths.REPO) / "src" / "autonomousprime"
    offenders = [
        str(p.relative_to(src))
        for p in src.rglob("*.py")
        if "evaluation" not in p.relative_to(src).parts
        and p.relative_to(src).as_posix() != "infra/data.py"
        and _uses_outcomes(ast.parse(p.read_text()))
    ]
    assert not offenders, f"hindsight: only evaluation/ may call data.outcomes(): {offenders}"
    assert _uses_outcomes(ast.parse("from autonomousprime.infra import data\ndata.outcomes()"))  # the check bites
