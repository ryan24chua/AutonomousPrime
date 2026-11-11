---
title: 'One cached data loader with hindsight removed'
type: 'refactor'
ticket: '2'
created: '2026-11-11'
status: 'done'
baseline_revision: 'a1292f4'
route: 'full'
risk: 'low'
review: 'quick'
review_loop_iteration: 0
built_by: 'subagent (worktree)'
deferred:
  - 'Ground _read_rows hard-codes year 2015 (the old reader ignored YEAR): story 3, one year filter.'
  - 'AIR_SYSTEM_DELAY, SECURITY_DELAY and AIRLINE_DELAY stay in loader rows (delay causes, not outcomes). Only ATC strips_hindsight removes them; Ground and Pilot whitelist columns. Story 3 role views settle one policy.'
  - 'agents/atc/config.py and fallback/config.py keep their own forbidden-column lists; story 3 or 11 points them at infra.data.OUTCOME_COLUMNS.'
---

## Intent

**Problem:** Six places re-read the 37 MB `flights.csv`, each with its own csv loop (about 3 s each), and outcome columns travelled in the rows the world builders received.

**Approach:** `infra/data.py` is the only loader (decision 2026-11-10):
- stdlib `csv`, with a per-day pickle cache in `.cache/flights/<sha256[:16]>-py313/`, built atomically;
- exact strings, file order;
- outcome columns removed from every row it hands out; `outcomes()` is the only way to read them, and only `evaluation/` calls it.

The data directory is a setting, `AUTONOMOUSPRIME_DATA_DIR` (W6).

## Code Map

- New:
  - `src/autonomousprime/infra/data.py`: `day`, `day_at`, `flight`, `tail`, `days`, `outcomes`, `OUTCOME_COLUMNS`.
  - `tests/unit/test_data.py`: 8 tests, including the AST boundary test (only evaluation reads outcomes).
- `paths.py`: the `AUTONOMOUSPRIME_DATA_DIR` override and `CACHE`. `.env.example`: the variable.
- Readers replaced:
  - `world_stub.load_day` (a thin wrapper);
  - Ground `_read_rows(path, month, day)`;
  - Pilot `load_schedule(year, month, day)`, narrowed to the focal date because every caller needs only that date;
  - `evaluate.load_rows` (same shape), plus the historical delay via `data.outcomes`;
  - `app_prime.load_row`;
  - the Pilot unit test and the live eval helper.
- `tests/golden/capture.py`: the speed monkeypatches are dropped; only the `ev.OUT` redirect stays.
- `AGENTS.md`: the loader entry and the pitfall text.

## Review Triage Log

- 2026-11-11, orchestrator review. The diff stays inside the code map. Every row function hands out stripped copies; the full rows stay internal to the memo. The three items under `deferred` are not blocking.

## Verification

- Subagent: pytest gives 88 passed, 1 deselected; a cold run takes 20 s against 36.5 s before. Dry run: 3.2 s cold (includes the cache build) and 1.3 s warm.
- Orchestrator, on the subagent branch after `rm -rf .cache`:
  - pytest: 88 passed, 1 deselected, 21 s; the snapshot is unchanged;
  - `ruff check`, `ruff format --check` and `uv lock --check` are clean;
  - the warm `python -m autonomousprime run` takes 1.7 s wall time.
