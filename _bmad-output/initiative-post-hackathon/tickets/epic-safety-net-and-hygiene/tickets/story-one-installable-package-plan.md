---
title: 'One installable package'
type: 'refactor'
ticket: '4'
created: '2026-11-07'
status: 'in-progress'
baseline_revision: 'acfa4c6'
route: 'full'
route_source: 'pinned'
risk: 'medium'
review: 'thorough'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Six top-level folders import each other through two `sys.path.insert` hacks and nine `Path(__file__).parents[n]` constants. Nothing installs, and the hyphenated `atc-agent/` cannot be imported as a package.

**Approach:**
- Move the code with `git mv` into one `src/autonomousprime/` package, installable with `pip install -e .`.
- Rewrite imports and delete the `sys.path` hacks.
- Resolve every repo path through one `autonomousprime/paths.py`.

This story moves files and rewrites import and path lines only. It changes no logic.

## Boundaries & Constraints

**Always:**
- Use `git mv`, so that `git diff -M` shows renames.
- Every non-rename hunk is an import line, a path constant, a usage docstring or comment naming a moved module, a `.gitignore` line, or packaging config.
- Imports of package code are absolute (`autonomousprime.…`), except where a relative import still resolves after the move.
- The golden master (`tests/golden/snapshot.json`) passes byte-identical.

**Never:**
- Change logic, names of functions, classes or constants, or defaults.
- Merge duplicated code. That is epic-one-core's job.
- Delete `app.py`, `fallback/world.py|rules.py|solver.py|__main__.py`, or anything else story 5 deletes. Move them with their packages and fix their imports so they still import.
- Rename or reorganise `tests/unit/<area>/` folders.
- Add runtime dependencies.
- Run `evaluation.evaluate` main/run, or make any LLM call.
- Push.

</frozen-after-approval>

## Code Map

Moves (old → new; everything under `src/autonomousprime/`):

| Old | New |
|---|---|
| `mediator/` | `mediator/` |
| `fallback/` | `fallback/` |
| `evaluation/` | `evaluation/` |
| `atc-agent/atc_agent/` | `agents/atc/` |
| `ground_agent/` (with `prompts/`) | `agents/ground/` |
| `agents/__init__.py`, `agents/schema.py`, `agents/constraints.py` | `agents/` (shared by all three roles until epic-one-core) |
| `agents/pilot.py` | `agents/pilot/agent.py` |
| `agents/pilot_inputs.py` | `agents/pilot/inputs.py` |
| `agents/prompts/` | `agents/pilot/prompts/` |

Moving `pilot.py` and `pilot_inputs.py` to `agent.py` and `inputs.py` mirrors the ground and ATC packages. Add an empty `agents/pilot/__init__.py`.

`atc-agent/` keeps only what story 5 archives or deletes: `agent-spec/`, `docs/`, `requirements.txt` and `.gitignore`.

New files:
- `src/autonomousprime/__init__.py`: a docstring only.
- `src/autonomousprime/paths.py`:
  - `REPO = Path(__file__).resolve().parents[2]`, with a docstring noting it assumes a source checkout (the data lives in the repo).
  - `DATA = REPO/"data"/"raw"`, `FLIGHTS = DATA/"dot2015"/"flights.csv"`, `AIRPORTS = DATA/"dot2015"/"airports.csv"`, `WORKBOOK = DATA/"challenge2"/"challenge-2-operational-constraints.xlsx"`.
  - `RESULTS = REPO/"results"`, `LOGS = REPO/"logs"`, `DOCS = REPO/"docs"`.
- `pyproject.toml`: add to the existing file and keep its pytest and ruff sections.
  - `[build-system]`: setuptools.
  - `[project]`:
    - `name = "autonomousprime"`, `version = "0.1.0"`, `requires-python = ">=3.13"`.
    - `dependencies`: today's `requirements.txt` minus pytest, with the same pins.
    - `[project.optional-dependencies] dev`: pytest and ruff, pinned as today.
  - `[tool.setuptools.packages.find] where = ["src"]`.
  - Package data so `prompts/*.md` ships.
- `requirements.txt` becomes `-e .` and `requirements-dev.txt` becomes `-e .[dev]`, each with a one-line comment, so old commands keep working.
- `.gitignore`: add `*.egg-info/` and `.cache/`.

Path constants to replace with `autonomousprime.paths` names (keep each module's existing constant name as an alias so its importers still work):
- `mediator/adapters.py:19-21`: `REPO`. Delete the `sys.path` insert.
- `fallback/world.py:13-16`: `REPO`. Delete the `sys.path` loop.
- `agents/constraints.py:16-17`: `REPO`, `WORKBOOK`.
- `pilot_inputs.py:18-19`: `FLIGHTS`, `AIRPORTS`.
- `ground_agent/inputs.py:19`: `FLIGHTS_CSV`.
- `atc_agent/config.py:11-13`: `REPO`, `WORKBOOK`, `FLIGHTS_CSV`.
- `atc_agent/agent.py:17-19`: `LOG_DIR = paths.LOGS/"atc"`, `CACHE_DIR = paths.REPO/".cache"/"atc"`.
- `evaluation/evaluate.py:49-50`, `evaluation/report.py:9`, `mediator/eval_batch.py:20`.
- Root scripts `app_prime.py:21-23`, `app.py:21-23`, `make_cache.py:14,32-33`.

`Path(__file__).parent / "prompts"` in the pilot and ground agents stays: it is package-relative.

Other edits:
- Imports everywhere: package modules, root scripts (`middleman.py`, `demo_rows.py`, `make_cache.py`, `app_prime.py`, `app.py`), `tests/unit/**` and `tests/golden/capture.py`. In `capture.py`, that includes the patch target `autonomousprime.agents.ground.inputs`.
- Remove `# noqa: E402` comments and ruff `per-file-ignores` that existed only because of the `sys.path` hacks.
- Update the usage docstrings that name moved modules (for example `python -m autonomousprime.mediator.run`) and the "Generated by" command string in `evaluation/report.py`.
- `.github/workflows/ci.yml`: install with `uv pip install --system -e ".[dev]"`.
- `pyproject.toml` `[tool.ruff.lint.per-file-ignores]`: re-point the keys at the moved files (for example `src/autonomousprime/evaluation/evaluate.py`), so `ruff check` stays clean; `requirements-dev.txt`'s ruff pin moves into the `dev` extra.
- `tests/live/pilot_eval.py` imports (it is not collected by default; check it with `python -c "import ast,sys; ast.parse(open('tests/live/pilot_eval.py').read())"` and a grep, never by running it).

## Tasks & Acceptance

**Execution:**
1. Before any move, record the baseline: `python -m mediator.run > before.txt`. Save the decision-record `.md` it names. Delete the logs it wrote.
2. Make the moves and the import, path and config edits. Commit with the message `story 1.4: …`.
3. Start a fresh venv: `uv venv .venv2 && uv pip install --python .venv2/bin/python -e ".[dev]"`. Run all the Verification checks from it.

**Acceptance Criteria:**
- Given a fresh venv with `-e ".[dev]"`, when `pytest` runs, then it shows the same pass count as the baseline and the golden master passes.
- When `python -m autonomousprime.mediator.run` runs, then its stdout and decision record match the baseline once the run id, timestamps and log paths are normalised.
- When `grep -rn "sys.path" src tests *.py` runs, then it prints nothing.
- When `grep -rn "parents\[" src` runs, then it prints only `paths.py`.

## Implementation Notes

## Review Triage Log

## Verification

**Commands** (run with `env -u ANTHROPIC_API_KEY`, from `.venv2`):
- `pytest -q` -- expected: same pass count as on the baseline, 0 failed
- `ruff check . && ruff format --check .` -- expected: exit 0
- `python -m autonomousprime.mediator.run` -- expected: matches `before.txt` after normalising (then delete the logs it wrote)
- `python -c "import middleman, demo_rows, make_cache"` -- expected: no error
- `git diff -M --stat acfa4c6` -- expected: renames dominate; list every non-rename file in the report
- `git status --short` -- expected: clean; `results/` and `docs/RESULTS.md` unchanged
