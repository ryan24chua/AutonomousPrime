"""The one flights.csv loader: stdlib csv, a per-day pickle cache, outcome columns removed.

First use parses the file once and writes one pickle per date under
`paths.CACHE / "flights" / <sha256(file)[:16]>-py<major><minor>/`; later calls read one small pickle.
A different file or Python version gets its own directory. Values stay the exact csv strings.

Rows handed out never contain OUTCOME_COLUMNS (product invariant "no hindsight"). `outcomes()` is the only
way to read them and only `evaluation/` may call it (tests/unit/test_data.py enforces this).
The delay-cause columns (WEATHER_DELAY, LATE_AIRCRAFT_DELAY, ...) are the given disruption, not outcomes.
Every function returns fresh dicts, so callers may mutate what they get.
"""

from __future__ import annotations

import csv
import hashlib
import os
import pickle
import shutil
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

from autonomousprime import paths

OUTCOME_COLUMNS = (
    "DEPARTURE_TIME",
    "ARRIVAL_TIME",
    "ARRIVAL_DELAY",
    "DEPARTURE_DELAY",
    "WHEELS_ON",
    "WHEELS_OFF",
    "ELAPSED_TIME",
    "AIR_TIME",
    "TAXI_IN",
    "TAXI_OUT",
    "DIVERTED",
    "CANCELLED",
    "CANCELLATION_REASON",
)
_OUTCOME_SET = frozenset(OUTCOME_COLUMNS)
_INDEX = "_days.pkl"
_MEMO_MAX = 64

Date = tuple[int, int, int]
_hashes: dict[tuple, str] = {}
_memo: dict[tuple, list[dict]] = {}


def _file_hash(path: Path) -> str:
    st = path.stat()
    key = (str(path), st.st_size, st.st_mtime_ns)
    if key not in _hashes:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        _hashes[key] = h.hexdigest()[:16]
    return _hashes[key]


def _build(path: Path, target: Path) -> None:
    by_date: dict[Date, list[dict]] = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            by_date.setdefault((int(r["YEAR"]), int(r["MONTH"]), int(r["DAY"])), []).append(r)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=target.name + ".tmp-", dir=target.parent))
    try:
        for (y, m, d), rows in by_date.items():
            with open(tmp / f"{y:04d}-{m:02d}-{d:02d}.pkl", "wb") as f:
                pickle.dump(rows, f, pickle.HIGHEST_PROTOCOL)
        with open(tmp / _INDEX, "wb") as f:
            pickle.dump(list(by_date), f)
        try:
            os.replace(tmp, target)
        except OSError:
            if not (target / _INDEX).exists():  # not a lost race with another builder
                raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _cache_dir(path: Path) -> Path:
    target = paths.CACHE / "flights" / f"{_file_hash(path)}-py{sys.version_info.major}{sys.version_info.minor}"
    if not (target / _INDEX).exists():
        _build(path, target)
    return target


def _load(year: int, month: int, day: int, path: Path | None) -> list[dict]:
    """Full rows (outcomes included, shared with the memo): internal, never hand these out."""
    target = _cache_dir(Path(path) if path else paths.FLIGHTS)
    key = (str(target), year, month, day)
    if key not in _memo:
        if len(_memo) >= _MEMO_MAX:
            _memo.clear()
        pkl = target / f"{year:04d}-{month:02d}-{day:02d}.pkl"
        if pkl.exists():
            with open(pkl, "rb") as f:
                _memo[key] = pickle.load(f)
        else:
            _memo[key] = []
    return _memo[key]


def _strip(r: dict) -> dict:
    return {k: v for k, v in r.items() if k not in _OUTCOME_SET}


def day(year: int, month: int, day: int, path: Path | None = None) -> list[dict]:
    """Every row of the date in file order, outcome columns removed."""
    return [_strip(r) for r in _load(year, month, day, path)]


def day_at(year: int, month: int, day: int, airport: str, path: Path | None = None) -> list[dict]:
    """Rows of the date that leave from or arrive at `airport`, file order."""
    return [
        _strip(r)
        for r in _load(year, month, day, path)
        if r["ORIGIN_AIRPORT"] == airport or r["DESTINATION_AIRPORT"] == airport
    ]


def _find(year, month, day, airline, flight_number, origin, path) -> dict | None:
    return next(
        (
            r
            for r in _load(year, month, day, path)
            if r["AIRLINE"] == airline and r["FLIGHT_NUMBER"] == flight_number and r["ORIGIN_AIRPORT"] == origin
        ),
        None,
    )


def flight(
    year: int, month: int, day: int, airline: str, flight_number: str, origin: str, path: Path | None = None
) -> dict | None:
    """The row of one flight on one date, outcome columns removed; None if absent."""
    r = _find(year, month, day, airline, flight_number, origin, path)
    return _strip(r) if r is not None else None


def tail(year: int, month: int, day: int, tail_number: str, path: Path | None = None) -> list[dict]:
    """Rows of one aircraft on the date, file order."""
    return [_strip(r) for r in _load(year, month, day, path) if r["TAIL_NUMBER"] == tail_number]


def days(path: Path | None = None) -> dict[Date, list[dict]]:
    """The whole file by date, outcome columns removed; keys and rows in file order."""
    target = _cache_dir(Path(path) if path else paths.FLIGHTS)
    with open(target / _INDEX, "rb") as f:
        keys = pickle.load(f)
    out = {}
    for y, m, d in keys:
        with open(target / f"{y:04d}-{m:02d}-{d:02d}.pkl", "rb") as f:
            out[(y, m, d)] = [_strip(r) for r in pickle.load(f)]
    return out


def outcomes(
    year: int, month: int, day: int, airline: str, flight_number: str, origin: str, path: Path | None = None
) -> dict:
    """Only the OUTCOME_COLUMNS of one row (the historical reference). Only `evaluation/` may call this."""
    r = _find(year, month, day, airline, flight_number, origin, path)
    if r is None:
        raise LookupError(f"no flight {airline}{flight_number} from {origin} on {year}-{month}-{day}")
    return {k: r[k] for k in OUTCOME_COLUMNS if k in r}


@lru_cache(maxsize=1)
def airports() -> dict[str, dict]:
    """airports.csv by IATA code (real coordinates; no outcome data)."""
    with open(paths.AIRPORTS, newline="") as f:
        return {r["IATA_CODE"]: r for r in csv.DictReader(f)}
