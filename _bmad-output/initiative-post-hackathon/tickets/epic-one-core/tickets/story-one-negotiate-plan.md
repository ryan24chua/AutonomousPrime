---
title: 'One negotiate()'
type: 'refactor'
ticket: '1'
created: '2026-11-11'
status: 'done'
baseline_revision: 'd810429'
route: 'full'
risk: 'medium'
review: 'quick'
review_loop_iteration: 0
built_by: 'subagent (worktree)'
deferred:
  - 'find_flight then negotiate loads the day twice (about 3 s each, uncached); story 2 caching removes the cost.'
  - 'make_cache.py still loads .env as well as .env.local; one place for settings belongs to story 7 (infra).'
  - '"middleman" survives in comments (agents/ground/demo.py, agents/schema.py, agents/pilot/agent.py) and in the Pilot prompt; story 11 sweep (G7). The prompt changes only with a live check.'
---

## Intent

**Problem:** There were two copies of "run one negotiation": `middleman.py` (the console's bridge, live whenever ANTHROPIC_API_KEY was set) and `mediator/run.py` (CLI).

**Approach:** One `service.negotiate(flight: FlightKey, seed=7, live=False) -> RunResult` and one CLI, `python -m autonomousprime run`. `live` is an explicit bool: a key in the environment never turns it on (design-register P7). With `live=True` and no key, `LiveUnavailable` is raised before any work. The console shows an error, and the CLI exits 2.

## Code Map

- `src/autonomousprime/service.py`:
  - `FlightKey` (with `from_spec`), `find_flight` (the old CLI default pick), `LiveUnavailable`;
  - `RunResult` (adds `negotiation_id`, `votes`, `fallback`, `mediator_outcome`, `mediator_plan`); its `to_dict()` gives the seven keys the console and `results/*.json` read;
  - `negotiate`.
- `src/autonomousprime/cli.py` (argparse subcommands; `eval` arrives in story 9) and `src/autonomousprime/__main__.py`.
- Deleted: `middleman.py`, `src/autonomousprime/mediator/run.py`. The ruff ignore for `middleman.py` is removed.
- `make_cache.py`: `cache_one(row_id, live)`, with a `--live` flag; it runs dry by default.
- `app_prime.py`: `run_live` passes `live=True`; it handles `LiveUnavailable`.
- `tests/golden/capture.py`: patches `service.load_day`; the console capture goes through `service.negotiate(...).to_dict()`. The snapshot is unchanged.
- `tests/unit/test_service.py`: four tests (live without a key raises before building; the CLI exits 2; `live` defaults to False; `FlightKey.from_spec`).
- Docs: AGENTS.md, README.md, docs/usage.md, docs/architecture.md.

## Review Triage Log

- 2026-11-11, orchestrator review. The diff stays inside the code map.
- The extra `mediator_plan` field is accepted: the CLI's `Plan:` line prints the mediator's pick, and on no-consensus that differs from `final_plan`.
- The three items under `deferred` are not blocking.

## Verification

- Subagent: the old `mediator.run` and the new `run` were compared for DFW MQ3086 and ORD OO6213 (no consensus). Stdout differs only in timestamped paths. The decision records differ only in the run_id and log-path lines.
- Orchestrator, on the subagent branch:
  - `uv sync --locked`, then `pytest`: 80 passed, 1 deselected. `ruff check`, `ruff format --check` and `uv lock --check` are clean. The snapshot is unchanged.
  - `python -m autonomousprime run` reaches consensus on C2 (21:09, B20). `run --live` with no key exits 2 with the message.
