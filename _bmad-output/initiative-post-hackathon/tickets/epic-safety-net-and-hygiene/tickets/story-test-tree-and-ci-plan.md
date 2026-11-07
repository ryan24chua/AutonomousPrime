---
title: 'One test tree, pytest config and CI'
type: 'chore'
ticket: '2'
created: '2026-11-07'
status: 'in-progress'
baseline_revision: 'a4d354b'
route: 'full'
route_source: 'pinned'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Tests are spread over four folders, nothing configures pytest or a linter, and no CI runs them. A behaviour change can merge unnoticed.

**Approach:** Move every test into `tests/unit/<area>/`. Turn the live Pilot eval script into an opt-in `live` test. Add pytest and ruff config and a GitHub Actions workflow that runs ruff and pytest on every push and pull request.

## Boundaries & Constraints

**Always:**
- Move files with `git mv`.
- Test logic is unchanged: only import lines and file locations change.
- `pytest` collects the same 75 tests as before (74 unit + 1 golden) and they all pass.
- Keep import order exactly as it is: `fallback.world` and `mediator.adapters` insert `atc-agent/` into `sys.path`, and later imports depend on that.
- Commit in three steps: (1) moves + config + CI + live test, (2) `ruff check --fix` changes, (3) `ruff format` changes.

**Never:**
- Change product logic.
- Change `tests/golden/snapshot.json`.
- Add the isort rule (`I`): it would reorder the `sys.path`-dependent imports.
- Use `--unsafe-fixes`.
- Edit `requirements.txt`, `.claude/`, `_bmad-output/` or `_bmad/`.
- Add runtime dependencies.
- Push.

</frozen-after-approval>

## Code Map

- `mediator/test_core.py` → `tests/unit/mediator/test_core.py`
- `fallback/tests/test_fallback.py` → `tests/unit/fallback/test_fallback.py`. Story 5 deletes it, but move it now.
- `ground_agent/tests/{helpers,test_agent,test_checker,test_icap,test_options}.py` → `tests/unit/ground/`. Rewrite `from ground_agent.tests.helpers` as `from tests.unit.ground.helpers`.
- `tests/test_pilot.py` → `tests/unit/pilot/test_pilot.py`
- Add `__init__.py` to `tests/unit/` and to each area folder. Remove the emptied `fallback/tests/` and `ground_agent/tests/`, including their `__init__.py`.
- `tests/live_pilot_eval.py` → `tests/live/pilot_eval.py`. Keep it runnable with `python -m tests.live.pilot_eval` and update its docstring command.
- New `tests/live/test_pilot_live.py`:
  - Marked `@pytest.mark.live`, and skipped when `ANTHROPIC_API_KEY` is unset.
  - Runs `pilot_eval.main()` with `pilot_eval.OUT` monkeypatched to `tmp_path`, so a test run never rewrites `results/`.
  - Asserts the output file was written and is non-empty.
- New `pyproject.toml`, containing only:
  - `[tool.pytest.ini_options]`:
    - `testpaths = ["tests"]`
    - a `live` marker with a one-line description
    - `addopts = "-m 'not live'"`, so a developer with a key loaded does not spend money by accident (`pytest -m live` opts in)
  - `[tool.ruff]`:
    - `line-length = 120`, `target-version = "py313"`
    - `extend-exclude = [".claude", "_bmad", "_bmad-output"]`
  - `[tool.ruff.lint]`: `select = ["E4", "E7", "E9", "F"]` (ruff's defaults, written out).
  - Package metadata waits for story 4.
- New `requirements-dev.txt`: `-r requirements.txt` plus `ruff==<exact version uv resolves>`.
- New `.github/workflows/ci.yml`:
  - Name `CI`, on `push` and `pull_request`, `permissions: contents: read`, one `ubuntu-latest` job.
  - Steps:
    1. `actions/checkout@v4`
    2. `actions/setup-python@v5` with Python 3.13
    3. `python -m pip install uv`
    4. `uv pip install --system -r requirements-dev.txt`
    5. `ruff check .`
    6. `ruff format --check .`
    7. `pytest`
- `docs/adr/0001-nash-product-pick.md:40`: update the `mediator/test_core.py` path. This is the only doc line that names a moved test.

## Tasks & Acceptance

**Execution:**
1. Moves, imports, `__init__.py` files, the live test, pyproject, requirements-dev and the workflow. Then run `pytest`: 75 passed, 1 deselected. Commit.
2. Run `ruff check --fix .`. Read every removed import in the diff. Restore any whose module has a side effect, such as `sys.path` setup, with `# noqa: F401`.
   - For what is left: hand-fix only trivially behaviour-neutral findings. Otherwise add `per-file-ignores` in pyproject with a short reason, and list them in the report.
   - `ruff check .` must be clean. Run `pytest`. Commit.
3. Run `ruff format .`, then `pytest`. Commit.

**Acceptance Criteria:**
- Given a fresh venv with `requirements-dev.txt`, when `pytest` runs, then 75 pass and the live test is deselected.
- When `ruff check .` and `ruff format --check .` run, then both exit 0.
- When `git diff a4d354b -- tests/golden/snapshot.json` runs, then the output is empty.

## Implementation Notes

## Review Triage Log

## Verification

**Commands** (run with `env -u ANTHROPIC_API_KEY`):
- `pytest -q` -- expected: `75 passed, 1 deselected`
- `pytest -q -m live` -- expected: 1 skipped (no key)
- `ruff check . && ruff format --check .` -- expected: exit 0
- `git status --short` -- expected: clean after the last commit; no new files in `results/` or `logs/`
