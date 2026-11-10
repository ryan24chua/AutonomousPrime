"""Golden master: capture every dry-run output the published results and the console depend on.

What is captured (no LLM calls, no files written in the repo):
  * evaluation  - `autonomousprime.evaluation.evaluate.evaluate_one` on the demo row + the 32-row stratified sample: every
                  method's plan, cost and metrics, the ablations, and the mediator's step-by-step log.
  * console     - `middleman.negotiate` (live=False) on the five console demo rows: outcome, plan, UI log,
                  decision record.

Volatile values (timestamps, run ids, file paths, latency) are stripped so the snapshot is deterministic.
While capturing, two pure CSV readers are swapped for cached copies that return the same rows in the same
order, only to keep the test fast; they are restored afterwards and the readers themselves are untouched.
"""

from __future__ import annotations

import asyncio
import json
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

SNAPSHOT = Path(__file__).with_name("snapshot.json")
VOLATILE_KEYS = {"ts", "latency_s", "log_path", "run_id"}


def _strip(obj):
    """Drop volatile keys, recursively."""
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in VOLATILE_KEYS}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


@contextmanager
def _patched(by_day: dict, out_dir: Path):
    """For the duration of a capture: serve the per-day and Ground CSV reads from memory (identical rows,
    identical order) and send the evaluation's per-row logs to `out_dir`. Everything is restored after."""
    import middleman
    from autonomousprime.evaluation import evaluate as ev
    from autonomousprime.agents.ground import inputs as ground_inputs

    def load_day(year: int, month: int, day: int) -> list[dict]:
        return [r for r in by_day.get((str(month), str(day)), []) if r["YEAR"] == str(year)]

    original_read_rows = ground_inputs._read_rows
    cache: dict = {}

    def read_rows(path):
        if path not in cache:
            cache[path] = list(original_read_rows(path))
        return iter(cache[path])

    saved = [
        (middleman, "load_day", middleman.load_day),
        (ground_inputs, "_read_rows", original_read_rows),
        (ev, "OUT", ev.OUT),
    ]
    middleman.load_day, ground_inputs._read_rows, ev.OUT = load_day, read_rows, out_dir
    try:
        yield
    finally:
        for module, name, value in saved:
            setattr(module, name, value)


def _evaluation(by_day: dict, out_dir: Path) -> list[dict]:
    from autonomousprime.evaluation import evaluate as ev

    picks = [("demo", ev.demo_row(by_day))] + ev.sample(by_day)
    rows = []
    for stratum, row in picks:
        rec = asyncio.run(ev.evaluate_one(stratum, row, by_day[(row["MONTH"], row["DAY"])]))
        log = out_dir / "logs" / f"{rec['id']}-{rec['mode']}.jsonl"
        rec["mediator_log"] = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
        rows.append(_strip(rec))
    return rows


def _console() -> dict[str, dict]:
    import middleman
    from demo_rows import DEMO_ROWS, SEED, row_date

    out = {}
    for row_id, spec in DEMO_ROWS.items():
        month, day = row_date(spec)
        res = middleman.negotiate({**spec, "month": month, "day": day}, SEED, live=False)
        log_path, run_id = res["log_path"], res["world"]["run_id"]
        doc = res["document"].replace(log_path, "<log_path>").replace(run_id, "<run_id>")
        res["document"] = re.sub(r"`[^`]*\.jsonl`", "`<log_path>`", doc)
        Path(log_path).unlink(missing_ok=True)  # middleman writes one log per run under logs/
        out[row_id] = _strip(res)
    return out


def capture() -> dict:
    from autonomousprime.evaluation.evaluate import load_rows

    by_day = load_rows()
    with tempfile.TemporaryDirectory() as tmp, _patched(by_day, Path(tmp)):
        data = {"evaluation": _evaluation(by_day, Path(tmp)), "console": _console()}
    # Round-trip through JSON so the captured value compares equal to the stored one.
    return json.loads(json.dumps(data, default=str))
