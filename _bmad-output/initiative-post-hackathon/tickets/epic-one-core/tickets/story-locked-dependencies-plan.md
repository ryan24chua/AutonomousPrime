---
title: 'Locked dependencies'
type: 'chore'
ticket: '13'
created: '2026-11-11'
status: 'done'
baseline_revision: 'f025c8c'
route: 'full'
risk: 'low'
review: 'quick'
review_loop_iteration: 0
built_by: 'subagent (worktree)'
deferred: []
---

## Intent

**Problem:** CI resolved floor-only pins (`anthropic>=2.3`, `streamlit>=1.40`, …) on every run, so an upstream release could break CI with no code change (design-register K1).

**Approach:** `uv.lock` holds exact versions. CI installs with `uv sync --locked --extra dev` and runs the checks through `uv run`. AGENTS.md says how to upgrade on purpose. `pip install -e ".[dev]"` keeps working.

**Never:** change a pin in `pyproject.toml` or add a dependency; touch `src/`, the tests or the snapshot.

## Code Map

- `uv.lock`: new, 57 packages. anthropic 2.8.0, streamlit 1.67.0, pydantic 2.14.2, pytest 9.2.0, ruff 0.17.4.
- `.github/workflows/ci.yml`: `astral-sh/setup-uv@v6`, `uv sync --locked --extra dev`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`.
- `AGENTS.md` "Running and verifying": install from the lock; upgrade with `uv lock --upgrade` in its own commit.
- `README.md`, `docs/usage.md`: one line naming the uv route.

## Review Triage Log

- 2026-11-11, orchestrator review. The diff stays inside the code map. No findings.

## Verification

- Subagent: `uv lock --check` exits 0. `uv sync --locked --extra dev` after `rm -rf .venv`: 76 passed, 1 deselected; ruff clean. `uv pip install -e ".[dev]"` into a scratch venv imports `autonomousprime`.
- Orchestrator, in a fresh clone in the scratchpad: `uv sync --locked --extra dev`, `uv lock --check`, then `pytest`: 76 passed, 1 deselected. `ruff check` and `ruff format --check` are clean.
- CI on the pushed branch: see the run for this commit.
