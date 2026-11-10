# Delegation plan: Epic 1 (safety net and hygiene) built by Sonnet subagents, orchestrated by me

## Context

The BMAD planning work (branch `docs/post-hackathon-refactor-plan`, commit `b957a2d`) produced a refactor roadmap in `_bmad-output/initiative-post-hackathon/`. Epic 1 (`tickets/epic-safety-net-and-hygiene/`) has 6 stories. You asked to delegate the build to Sonnet subagents with me (Opus) orchestrating.

Decisions taken (2026-11-03):
- **Engine:** I write a self-contained brief per story in BMAD's plan-template shape. Subagents implement from it. No BMAD scripts run (`bmad-build-auto` needs `bmad setup` and nested subagents).
- **Scope:** Epic 1 only, then pause for your review before Epic 2.
- **Tooling:** dev-only ruff (format + lint, autofix) and GitHub Actions running ruff + pytest on push and PR.
- **Cleanup:** archive `pitch.pptx`, the hackathon PDF, `atc-agent/agent-spec/` and `atc-agent/docs/` under `docs/hackathon/`. Keep `.claude/skills/` as is. BMAD skills stay local.

## Roles

| Who | Does |
|---|---|
| **Me (orchestrator, Opus)** | Builds 1.1 (the golden master every later review depends on) and 1.6 (CLAUDE.md/AGENTS.md; `bmad-project-context` needs your approval of writes). Writes each story brief. Reviews every diff, runs all checks, merges, pushes, updates ticket status. |
| **Sonnet subagents** (`Agent`, `subagent_type: general-purpose`, `model: sonnet`, `isolation: worktree`) | Build 1.2, 1.3, 1.4, 1.5. One subagent per story, in its own git worktree. Commit there; never push, never touch other branches. |

## Branching and tracking

- Integration branch **`refactor/safety-net-and-hygiene`**, cut from `docs/post-hackathon-refactor-plan` so the ticket tree travels with the code. One commit per story (`story 1.N: <title>`), pushed after each merge. No PR unless you ask; I'll offer one at the pause.
- Each story gets a plan file beside its ticket, per BMAD convention: `_bmad-output/initiative-post-hackathon/tickets/epic-safety-net-and-hygiene/tickets/story-<slug>-plan.md`. It carries `status` (ready-for-dev → in-progress → in-review → done | blocked), `baseline_revision`, the brief, and review notes.
- Answers already given are recorded: dated `Decision:` lines in the epic's Notes and the initiative memlog. The `unknown` keys come off entries 1.2 and 1.5.
- Ticket corrections during the run: 1.4's verify line and the epic's Done-when say `python -m autonomousprime run`, but that CLI only arrives in 2.1. Change both to `python -m autonomousprime.mediator.run`. Story 1.6 also takes over 1.5's leftover doc updates if any.

## Order (from the tickets' `after` graph)

```
1.1 (me) → 1.2 (sonnet) → ┬ 1.3 (sonnet) ┐ → 1.5 (sonnet) → 1.6 (me) → PAUSE
                          └ 1.4 (sonnet) ┘
```
1.3 and 1.4 run in parallel, in separate worktrees, launched in one message. I merge 1.3 first, then rebase 1.4 onto it.

## Story briefs (what each subagent gets)

Every brief has this fixed shape (BMAD `plan-template.md`, kept under ~1,300 tokens):
- **Intent:** problem and approach in 1–2 sentences each.
- **Always / Never:** allowed paths, invariants, forbidden changes.
- **Code map:** exact files and functions to touch.
- **Verify:** commands that must pass before committing, plus report format (branch, SHA, commands run with output tail, anything deferred).

Every brief also includes these standing rules:
- Set up the worktree with `uv venv .venv && uv pip install -r requirements.txt` (after 1.4: `uv pip install -e ".[dev]"`).
- Run `pytest` including `tests/golden` before committing.
- No golden-master changes. No new runtime dependencies. No edits outside the code map.
- Do not run `evaluation.evaluate` `main()`: it rewrites `docs/RESULTS.md`.

Per-story specifics:

**1.1 Golden master (me).**
- `tests/golden/test_golden.py`, `tests/golden/snapshot.json`, and an update script (`python -m tests.golden.update`).
- Reuse `evaluation.evaluate.load_rows` / `sample` / `demo_row` and `mediator.adapters.build_scenario`, `mediator.core.run_negotiation` (dry `LaneAgent`s), `fallback.scenario.solve_scenario`. Load the CSV once.
- Rows: the 32-row sample, the DFW MQ3086 demo row, and the 5 `demo_rows.DEMO_ROWS`.
- Snapshot per row: outcome, picked plan id and plan, votes, candidate/valid counts, shortlist ids, products and costs, fallback outcome/plan/cost. Timestamps, run ids and paths stripped.
- Verify: passes twice in a row (determinism); editing `ground_agent/cost_config.GROUND_DELAY_PER_MIN` makes it fail with a readable diff (then reverted).

**1.2 Test tree, pytest config, ruff, CI (sonnet).**
- Move tests to `tests/unit/<area>/` (from `mediator/test_core.py`, `fallback/tests/`, `ground_agent/tests/`, `tests/test_pilot.py`).
- `tests/live_pilot_eval.py` becomes `tests/live/` with a skip when there's no `ANTHROPIC_API_KEY`.
- `pyproject.toml` gets only `[tool.pytest.ini_options]` and `[tool.ruff]` for now (the package metadata comes in 1.4). `requirements-dev.txt` adds ruff.
- Add `.github/workflows/ci.yml`: Python 3.13, uv install, `ruff check`, `ruff format --check`, `pytest`.
- Formatting churn goes in a separate commit within the story.

**1.3 Console smoke test (sonnet).**
- `tests/unit/ui/test_console.py` with `streamlit.testing.v1.AppTest` on `app_prime.py`, replay mode.
- For each demo row: select it, click "Find a recovery plan", and assert that the recommendation and the Approve/Reject buttons render.
- No edits to `app_prime.py` beyond stable widget keys, if needed.

**1.4 One installable package (sonnet, highest blast radius).**
- `git mv` into `src/autonomousprime/`: `mediator/`, `fallback/`, `evaluation/`, `atc-agent/atc_agent` → `agents/atc`, `agents/` (pilot) → `agents/pilot`, `ground_agent/` → `agents/ground`. Prompts move with their modules.
- Rewrite imports and delete the `sys.path.insert` calls (`mediator/adapters.py:21`, `fallback/world.py:14-16`).
- Replace every `Path(__file__).parents[n]` / `REPO` constant with one `autonomousprime/paths.py`:
  - `atc_agent/config.py` (`REPO = parents[2]`)
  - `atc_agent/agent.py` (`ROOT` for logs and cache)
  - `agents/constraints.py`, `agents/pilot_inputs.py`, `ground_agent/inputs.py`, `fallback/world.py`, `mediator/adapters.py`
- `middleman.py`, `demo_rows.py`, `make_cache.py` and `app_prime.py` stay at the root with updated imports.
- Only import/path edits allowed. Review uses `git diff -M` and confirms that every non-rename hunk is an import or path line.

**1.5 Delete unused code, archive hackathon material (sonnet).**
- Delete `app.py`, `fallback/world.py`, `rules.py`, `solver.py`, `__main__.py` and their tests. Move `TIE_BREAK` into `fallback/scenario.py`. Fix `fallback/__init__.py`.
- Keep `mediator/eval_batch.py`: the console reads its output. It goes in 2.9.
- Delete `ui/ui_implementation_plan_mock_data.md` and the lane-local `atc-agent/requirements.txt` and `.gitignore`.
- `git mv` the pitch, the PDF, `atc-agent/agent-spec/` and `atc-agent/docs/` to `docs/hackathon/`.
- Update every doc reference to moved or deleted paths and commands: README, `docs/usage.md`, `docs/architecture.md` component table.

**1.6 Repo instructions (me, with you).**
- Rewrite `CLAUDE.md`: stack, layout, commands, invariants K1–K10 from `constraints-audit.md`, branch naming by purpose (no `claude/` prefix). Remove the hackathon timeline, lanes and the Singapore template.
- Trim `.env.example` to `ANTHROPIC_API_KEY`.
- Run `bmad-project-context` to propose an `AGENTS.md` block, which you approve at the pause.

## Review gate (me, after every story, before merge)

1. Read the full diff. Reject edits outside the brief's code map or Never list.
2. In a clean venv on the merged result, run the full `pytest` (unit + golden; smoke test once 1.3 lands), plus `ruff check` and `ruff format --check` once 1.2 lands.
3. Golden master must be byte-identical. **Any change means the story is rejected:** nothing in Epic 1 may move a number.
4. Story-specific check: the `Verify:` line in its `tickets.toml` entry.
5. **Fail:** send the findings back to the same subagent (`SendMessage`), at most 2 rounds. After that, I fix it myself or mark the story `blocked` in its plan file and stop.
6. **Pass:** squash or merge into `refactor/safety-net-and-hygiene`, push, and set the plan file to `status: done`. Deferred findings go to the plan's `deferred:` list for Epic 2's sweep (2.11).

## Stop conditions

- A story is blocked after 2 review rounds.
- A golden-master change I can't attribute to a test artifact.
- CI red on the pushed branch, and the cause isn't in the current story.
- Anything needing a decision outside Epic 1's scope.

## Verification (end of Epic 1, before the pause)

- **CI:** GitHub Actions is green on `refactor/safety-net-and-hygiene` (checked via the GitHub MCP `actions_list` / `actions_get`), with ruff, unit tests, golden master and the console smoke test all passing.
- **Fresh clone in a new venv:** `uv pip install -e ".[dev]" && pytest` passes. `python -m autonomousprime.mediator.run` produces the same decision record as on `main`.
- **Console:** `streamlit run app_prime.py` replays all five demo rows.
- **No leftovers:** `grep -rn "sys.path.insert" src/` is empty, and `grep -n "TBD\|Singapore\|Singpass\|15:00" CLAUDE.md` is empty.
- **Hand-off:** a short summary for you covering commits per story, review rounds, deferred findings and the CI link. I'll also offer to open the PR.
