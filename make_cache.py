"""Run negotiate() on every demo row and save results/<row_id>.json so the demo works offline.

Usage: uv run python make_cache.py [--live] [row_id ...]
Dry run (no LLM) unless --live is given; --live uses Claude and overwrites the console's replay files.
Calls service.negotiate(...).to_dict() (see app_prime.py for the keys it reads).
"""

import argparse
import json

from dotenv import load_dotenv

from autonomousprime import paths
from autonomousprime.service import FlightKey, negotiate
from demo_rows import DEMO_ROWS, SEED, row_date

RESULTS = paths.RESULTS


# Runs negotiate() for one demo row and writes results/<row_id>.json.
# Args: row_id - key of DEMO_ROWS; live - use Claude for the votes (else a dry run).
# Returns: the result dict.
def cache_one(row_id, live: bool):
    spec = DEMO_ROWS[row_id]
    month, day = row_date(spec)
    result = negotiate(FlightKey.from_spec({**spec, "month": month, "day": day}), SEED, live=live).to_dict()
    result["row_id"] = row_id
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{row_id}.json").write_text(json.dumps(result, indent=2, default=str))
    return result


# Caches every requested demo row, continuing past per-row failures.
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("row_ids", nargs="*")
    ap.add_argument("--live", action="store_true", help="use Claude for the votes (default: dry run)")
    a = ap.parse_args()
    load_dotenv(paths.REPO / ".env.local")
    load_dotenv(paths.REPO / ".env")
    for row_id in a.row_ids or DEMO_ROWS:
        try:
            r = cache_one(row_id, live=a.live)
            print(f"ok   {row_id}: {r.get('outcome')} in {r.get('rounds')} round(s)")
        except Exception as e:  # keep going so one bad row doesn't block the rest
            print(f"FAIL {row_id}: {e!r}")


if __name__ == "__main__":
    main()
