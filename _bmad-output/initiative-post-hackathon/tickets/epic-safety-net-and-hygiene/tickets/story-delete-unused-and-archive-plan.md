---
title: 'Delete unused code and archive hackathon material'
type: 'chore'
ticket: '5'
created: '2026-11-07'
status: 'in-progress'
baseline_revision: 'd332462'
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

**Problem:**
- The repo carries code the product never runs: a second UI (`app.py`) and a standalone fallback solver with its own world, rules and CLI.
- It also carries lane-local leftovers and hackathon material (pitch, PDFs, greenfield specs) that contradict the code.
- The docs still name folders that story 4 moved.

**Approach:**
- Delete the unused code.
- `git mv` the hackathon material under `docs/hackathon/`.
- Update every doc and docstring reference to a moved or deleted path or command.

User decisions (2026-11-03): archive, don't delete, the pitch, the PDFs, `atc-agent/agent-spec/` and `atc-agent/docs/`; keep `.claude/skills/`.

## Boundaries & Constraints

**Always:**
- Use `git mv` for archives.
- After deleting, `grep` proves that nothing imports a deleted module.
- The golden master and the console smoke test pass unchanged.

**Never:**
- Delete `src/autonomousprime/mediator/eval_batch.py`: the console reads its output (`results/eval_summary.json`). It goes in epic-one-core.
- Delete `src/autonomousprime/fallback/config.py`: `evaluation/evaluate.py` reads its cost weights.
- Touch `.claude/`, `_bmad-output/`, `results/`, `docs/RESULTS.md` (generated) or `CLAUDE.md` (story 6 rewrites it).
- Change any logic.
- Push.

</frozen-after-approval>

## Code Map

**Delete** (`git rm`):
- `app.py`
- `src/autonomousprime/fallback/world.py`, `rules.py`, `solver.py`, `__main__.py`
- `tests/unit/fallback/` (5 tests of the standalone solver, plus `__init__.py`)
- `ui/ui_implementation_plan_mock_data.md`; `ui/` is then empty
- `atc-agent/requirements.txt`, `atc-agent/.gitignore`

**Move:** `TIE_BREAK` (`solver.py:14`) goes into `src/autonomousprime/fallback/scenario.py` as the same list, replacing `from .solver import TIE_BREAK`.

**Fix:**
- `src/autonomousprime/fallback/__init__.py`: it re-exports `solve`, `build_world` and `FallbackWorld` from deleted modules. Make it docstring-only, describing the fallback as `scenario.solve_scenario` plus `config`.
- `scenario.py`: change the docstring line "fallback/world.py stays the standalone evaluation baseline" and the comment "same dict shape as fallback.solver.solve" so they describe what remains.

**Archive** (`git mv` into `docs/hackathon/`):
- `pitch.pptx`
- `Autonomous SG 2026_Airbus Track.pdf`
- `Autonomous SG 2026_NUS Hackers.pdf`
- `atc-agent/agent-spec/` → `docs/hackathon/atc-agent-spec/`
- `atc-agent/docs/` → `docs/hackathon/atc-agent-docs/`
- Add `docs/hackathon/README.md`, 3–6 lines: what this folder is (hackathon-era material kept for the record, not current design) and one line per item.

**Reference updates.** Only the lines that name a moved or deleted path or a changed command. Use package paths such as `src/autonomousprime/mediator/` and `python -m autonomousprime.mediator.run`.
- `README.md:38-45`: use the install command `pip install -e ".[dev]"` and update the run commands.
- `README.md:80-86`: update the layout table to the `src/autonomousprime/` folders. Drop `app.py`, and add `tests/` and `docs/hackathon/` rows.
- `docs/usage.md:8,12,63-66`: update the install line and commands, and delete the `app.py` sentence.
- `docs/architecture.md:42-55` (mermaid labels), `:82-88` (component table), `:225`, `:256`: update the paths, and drop `app.py`.
- `docs/adr/0002-…md:13,54` and `docs/adr/0003-…md:11`: update the code paths only.
- `docs/challenge-2-brief.md:3`: update the PDF path to `docs/hackathon/`.
- `src/autonomousprime/agents/atc/config.py:4`: update the spec path.
- Docstrings that name `app.py`: `app_prime.py:1`, `demo_rows.py:1`, `middleman.py:1`, `make_cache.py:4`. Say `app_prime.py` (the console).

## Tasks & Acceptance

**Execution:**
1. Make the deletions, the TIE_BREAK move and the `__init__` fix. Run `pytest`: expect 75 passed (80 − 5 standalone fallback tests).
2. Make the archives and the reference updates. Commit as `story 1.5: …`.

**Acceptance Criteria:**
- Given the deletions, when `grep -rnE "fallback\.(world|rules|solver)|fallback import (solve|build_world)|\bapp\.py\b" src tests *.py README.md docs --include=*.py --include=*.md` runs over everything except `docs/hackathon/` and `docs/RESULTS.md`, then nothing is printed.
- When `pytest` runs, then 75 pass, the golden master is unchanged and the 5 console tests pass.
- When `ls` runs at the repo root, then it shows no `app.py`, `ui/`, `pitch.pptx` or `*.pdf`, and `atc-agent/` holds no tracked files.

## Implementation Notes

## Review Triage Log

## Verification

**Commands** (run with `env -u ANTHROPIC_API_KEY`):
- `pytest -q` -- expected: `75 passed, 1 deselected`
- `ruff check . && ruff format --check .` -- expected: exit 0
- `git ls-files atc-agent ui app.py '*.pdf' pitch.pptx` -- expected: empty
- The acceptance grep above -- expected: empty
- `git status --short` -- expected: clean after commit
