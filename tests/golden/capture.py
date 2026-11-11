"""Golden master: pin the dry-run outcomes the published results and the console depend on.

What is captured (no LLM calls, no files written in the repo):
  * evaluation  - `autonomousprime.evaluation.evaluate.evaluate_one` on the demo row + the 32-row stratified sample: every
                  method's plan, cost and metrics, the ablations, and the mediator's step-by-step log.
  * console     - `middleman.negotiate` (live=False) on the five console demo rows: outcome, plan, round count and
                  the per-agent log.

Only outcomes are pinned (ADR-0004): plans, plan ids, costs, metrics, scores, vote booleans, check results with
their rule ids, and round counts. Prose is dropped, so editing a reason, a decision-record sentence or a
violation message does not fail the test; changing a number, a plan, a rule id or an outcome does.
Volatile values (timestamps, run ids, file paths, latency) are stripped so the snapshot is deterministic.
While capturing, two pure CSV readers are swapped for cached copies that return the same rows in the same
order, only to keep the test fast; they are restored afterwards and the readers themselves are untouched.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

SNAPSHOT = Path(__file__).with_name("snapshot.json")
VOLATILE_KEYS = {"ts", "latency_s", "log_path", "run_id"}
# Free text: agents' reasons, the mediator's explanations, rule descriptions, the decision record, display labels.
PROSE_KEYS = {
    "reason",
    "why",
    "neg_why",
    "r1_reasons",
    "r2_reasons",
    "need",
    "offer",
    "consensus_rule",
    "pick_rule",
    "document",
}
VIOLATION_KEYS = {"violations", "pick_violations"}  # lists of "RULE-ID: message"; only the id is pinned
WORLD_LABELS = {"data", "mode", "synthetic_inputs"}  # console header text


def rule_id(violation: str) -> str:
    return violation.split(":", 1)[0].strip()


def project(obj):
    """Keep outcomes, drop prose, recursively (see the module docstring)."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in VOLATILE_KEYS or k in PROSE_KEYS:
                continue
            if k in VIOLATION_KEYS and isinstance(v, list):
                out[k] = [rule_id(x) for x in v]
            elif k == "world" and isinstance(v, dict):
                out[k] = project({wk: wv for wk, wv in v.items() if wk not in WORLD_LABELS})
            elif k == "scores" and isinstance(v, dict):
                # round-2 log: {plan_id: [score, reason]} -> {plan_id: score}; the pick ranking is already numbers
                out[k] = {sk: sv[0] if isinstance(sv, list) else project(sv) for sk, sv in v.items()}
            else:
                out[k] = project(v)
        return out
    if isinstance(obj, list):
        return [project(v) for v in obj]
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
        rows.append(project(rec))
    return rows


def _console() -> dict[str, dict]:
    import middleman
    from demo_rows import DEMO_ROWS, SEED, row_date

    out = {}
    for row_id, spec in DEMO_ROWS.items():
        month, day = row_date(spec)
        res = middleman.negotiate({**spec, "month": month, "day": day}, SEED, live=False)
        Path(res["log_path"]).unlink(missing_ok=True)  # middleman writes one log per run under logs/
        out[row_id] = project(res)
    return out


def capture() -> dict:
    from autonomousprime.evaluation.evaluate import load_rows

    by_day = load_rows()
    with tempfile.TemporaryDirectory() as tmp, _patched(by_day, Path(tmp)):
        data = {"evaluation": _evaluation(by_day, Path(tmp)), "console": _console()}
    # Round-trip through JSON so the captured value compares equal to the stored one.
    return json.loads(json.dumps(data, default=str))
