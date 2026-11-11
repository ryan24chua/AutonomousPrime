# Delegation plan: Epic 2 (one core) built by Sonnet subagents, orchestrated by me

**Status:** approved 2026-11-11.

## Context

Epic 2 (`_bmad-output/initiative-post-hackathon/tickets/epic-one-core/`) collapses the hackathon's three parallel implementations into one core:
- one loader, one world, one contracts module;
- one rule registry, one cost module, one LLM client;
- one `negotiate()`, one evaluation, one console.

It has 13 stories in `tickets/tickets.toml`. Stories 12 and 13 were added on 2026-11-11 and run first. The 2026-11-11 decisions (ADR-0004, design register) change how Epic 1's delegation pattern applies here:
- **The golden master gets narrower.** Story 12 first reduces it to plans, costs, outcomes, rule ids and round counts.
- **Number moves are allowed in their own commits.** Pure-move commits must leave the snapshot byte-identical. Story 3's world unifications and gate-world fixes may move numbers, but only as separate commits that state which numbers moved and why.
- **The register rows are part of the stories.** Stories 1, 2, 4, 8, 9, 10 and 11 carry rows P7, W6, N7, G1, C3, U1/K1 and G7.

**On approval:** I commit this plan as `tickets/epic-one-core/delegation-plan.md` on `refactor/one-core` and start story 12. The run continues in auto mode, stopping only on a stop condition or a check-in listed below. A pause comes at the end of the epic.

## Roles

| Who | Does |
|---|---|
| **Me (orchestrator)** | Build story 12 (the gate every review depends on) and story 3 (one world: highest risk, and the only story whose commits deliberately move golden numbers). Write each brief, review every diff, run all checks, merge, push, update ticket status. |
| **Sonnet subagents** (`Agent`, `general-purpose`, `model: sonnet`, `isolation: worktree`) | Build stories 13, 1, 2, 4, 5, 6, 7, 8, 9, 10 and 11. One subagent per story, each in its own worktree. They commit there and never push. |

## Branching and tracking

- **Integration branch:** `refactor/one-core`, which already holds the planning docs. Each story lands as one commit `story 2.N: <title>`. Story 3 lands as a short series: one pure-move commit, then one commit per unification. Every merge is pushed. No PR unless you ask.
- **Per-story plan file:** `tickets/epic-one-core/tickets/story-<slug>-plan.md`. It holds the status (ready-for-dev → in-progress → in-review → done | blocked), `baseline_revision`, the brief, review notes and a `deferred:` list for story 11.
- **Ticket corrections, made in the first commit:**
  - Story 3 creates `core/timeutil.py` with a single rule for "2400". Story 4 moves the remaining helper callers onto it (the ground timeutil and the console).
  - Story 9 republishes `docs/RESULTS.md` instead of reproducing it. Story 3 moves numbers, so the republish diff must match story 3's stated moves.
  - `epic-plans-time-and-events.md` still calls S5 "Open"; it is now decided.

## Order (from the `after` graph)

```
12 (me) → 13 → 1 → 2 → 3 (me) → 4 → ┬ 5 → 6 ┐ → 8 → 9 → 10 → 11 → PAUSE
                                     └ 7 ────┘
```

Story 7 runs in parallel with stories 5 and 6, in its own worktree, launched as soon as story 4 merges. I merge 5 and 6 first, then rebase 7 onto them.

## Story briefs

Each brief follows Epic 1's fixed shape (Intent, Always / Never, Code map, Verify) and stays under about 1,300 tokens.

**Standing rules in every brief**
- **Setup:** `uv venv .venv && uv pip install -e ".[dev]"`; after story 13, `uv sync --locked --extra dev`.
- **Checks before committing:** run `env -u ANTHROPIC_API_KEY pytest` (golden master, unit tests, smoke test), plus `ruff check` and `ruff format --check`.
- **Golden master:** byte-identical unless the brief names the numbers it may move.
- **Dependencies:** no new ones. stdlib `tomllib` and `csv` only.
- **Commands not to run:** `evaluation.evaluate` main/run (it rewrites `docs/RESULTS.md`; story 9 excepted), `make_cache.py`, live tests.
- **Scope:** no edits outside the code map. Repo paths go through `autonomousprime/paths.py`.
- **Rule-ID policy (AGENTS.md):** a schema or rule-ID change goes in its own commit, with a version bump and `docs/architecture.md` §5–6 updated.

**Per-story specifics**

**12 Golden master pins outcomes, not prose (me).**
- In `tests/golden/capture.py`, add projection functions:
  - Evaluation rows keep metrics per method (`m`), ablations, `attr`, counts, outcome and event.
  - The mediator log keeps proposals, shortlist and picked plan ids and plans, costs, scores, products, vote booleans, and violation rule ids (the text before `:`).
  - Console rows keep outcome, `final_plan` and `rounds`.
  - Dropped: `reason`, `why`, `neg_why`, `r1_reasons`, `r2_reasons`, UI-log text and the decision-record `document`.
- Regenerate the snapshot once.
- Update AGENTS.md "Running and verifying" and the golden test docstring.
- **Verify:**
  - A scratch script shows every pinned value is equal in the old and new snapshots.
  - Editing a reason string passes; editing `GROUND_DELAY_PER_MIN` fails with a readable diff (then reverted).

**13 Locked dependencies.**
- `uv lock` writes `uv.lock`.
- `ci.yml` installs with `uv sync --locked --extra dev`, then `uv run ruff …` and `uv run pytest`.
- AGENTS.md "Running and verifying" adds the lockfile and `uv lock --upgrade`. `pip install -e ".[dev]"` keeps working.
- **Verify:** CI is green on the pushed branch, and a fresh clone with `uv sync --locked` passes pytest.

**1 One `negotiate()`.**
- Add `src/autonomousprime/service.py`: `negotiate(flight_key, seed, live=False) -> RunResult`.
  - RunResult holds outcome, plan, rounds actually used, log path, decision record, and the data the UI shows.
  - This absorbs `middleman.negotiate` and `_entry`, and `mediator/run.main`.
- Add `src/autonomousprime/cli.py` (`python -m autonomousprime run`) and a package `__main__.py`.
- Delete `middleman.py` and `mediator/run.py`. Re-point `app_prime.py`, `make_cache.py`, `tests/golden/capture.py` and the AGENTS.md commands to the service.
- **P7:** `live` is an explicit bool. Nothing reads `ANTHROPIC_API_KEY` to decide it. The console's live toggle passes `live=True`, and shows an error with no key instead of silently running dry.
- **Verify:**
  - `python -m autonomousprime run` matches the old `mediator.run` decision record.
  - Smoke test passes; golden master byte-identical.

**2 One cached data loader** (decision 2026-11-10).
- Add `src/autonomousprime/infra/data.py`:
  - stdlib `csv` reader with a per-day pickle cache in gitignored `.cache/`, keyed by file hash and Python version;
  - values stay exact strings;
  - indexed by full date with airport, by flight key and by tail;
  - outcome columns only via `data.outcomes()`.
- **W6:** the data directory is a setting, `AUTONOMOUSPRIME_DATA_DIR`, defaulting to the checkout's `data/`, and added to `.env.example`.
- Replace these readers:
  - `agents/atc/world_stub.load_day`
  - `agents/pilot/inputs.load_schedule`
  - `agents/ground/inputs._read_rows`
  - `evaluation/evaluate.load_rows`
  - `app_prime.load_row`
  - `tests/unit/pilot/test_pilot.py:226`
  - `tests/live/pilot_eval.py:37`
- Drop the golden capture's monkeypatches that only existed for speed.
- **Verify:**
  - A timed dry run takes under 2 s with a warm cache.
  - A test fails if anything outside `evaluation/` imports `data.outcomes`.
  - Golden master byte-identical.

**3 One world with per-role views (me).**
- **Commit A (pure move):** add `core/world.py` with a frozen `WorldState` built once per `negotiate()`, plus `core/timeutil.py`. It holds atc/pilot/ground/fallback views and provenance labels on every synthetic field. The three builders are deleted. Golden master byte-identical.
- **Commits B…** (one per unification, each regenerating the snapshot and stating the numbers that moved):
  1. one disrupted arrival and Ground "now" (fixes RESULTS §5.4, DFW-20150303-MQ3275);
  2. one event classifier;
  3. one year filter;
  4. one "2400" rule;
  5. seeding per flight;
  6. W3, gates for any airport size (today's world crashes at 294 of 322 airports);
  7. W3, scheduled gate taken from the world.
- **Verify:**
  - Ticket verify line.
  - `build_world` succeeds on a Small-hub row and a Non-hub row.
  - A test shows each view excludes the other roles' private fields.

**4 One contracts module.**
- `core/contracts.py` replaces `agents/schema.py`, `agents/atc/schema.py`, and mediator `ScoredPlan`/`Vote`/`CheckResult`.
- `Vote` gains flags. The log line gets a versioned schema; this is its own commit, updating architecture §5.
- Remaining HHMM helpers move onto `core/timeutil.py`.
- **N7:** word limits and the retry count become settings, validated in one place.
- **Verify:** schema round-trip tests; golden master byte-identical.

**5 Rule registry.**
- Add `core/rules/`, with one registration per rule id: `check_slot`, `assess_plan` fuel/crew, `check_ground` gate/turn/crew.
- `adapters.check_plan` becomes `registry.check`. Delete ATC's fuel stub and the adapter's filter of it.
- Keep every id and its order (golden master byte-identical).
- The id collisions (the adapter's "C-GATE-1: no gate in plan", and the invented "C-CREW-2") are fixed in one last commit that follows the rule-ID policy and moves only rule ids in the snapshot.
- **Verify:** a test that every id is registered once and emitted only from `core/rules`.

**6 One cost module.**
- `core/cost.py` plus `config/cost.toml` (weights with source labels, read with `tomllib`).
- Delete the duplicates:
  - `agents/atc/config.py` cost stub
  - `agents/ground/cost_config.py`
  - `fallback/config.py` cost block
  - the evaluation's literal `5.0`
- Remove AGENTS.md's "change all three together" line.
- **Verify:**
  - Golden master byte-identical.
  - A test fails on a weight literal outside `config/` and the tests.

**7 One LLM client and agent template (hitl).**
- Add `infra/llm.py`. It provides:
  - async `messages.parse`;
  - a cached system prompt;
  - retry once, then a typed failure;
  - a response cache keyed by (model, system, messages, schema);
  - one JSONL call log with usage and latency;
  - the per-role model and `max_tokens` from settings (every role on `claude-sonnet-5-5`, with today's limits kept).
- Add `agents/base.py`.
- Move ATC (sync client, `find("{")` parsing, its own `.env` reader and cache), Pilot and Ground onto it. Prompts load at call time. Only `infra/llm.py` imports `anthropic`.
- The subagent reads the `claude-api` skill reference first.
- **Verify:**
  - Fake-client tests per role (success, malformed-then-valid, refusal, `max_tokens`).
  - A dry run imports no SDK.
  - Golden master byte-identical.
- **Check-in:** the live demo-row test costs money, and this environment has no key. I'll ask you then to either run `pytest -m live` yourself, or give this session a key through the credential form (never in chat).

**8 Mediator, fallback and agents on the core.**
- Dissolve `mediator/adapters.py`:
  - proposers and scoring keys move to `agents/<role>/policy.py`;
  - `LaneAgent` moves to `agents/base.py`;
  - `fallback/scenario.py` becomes `core/fallback.py`;
  - `mediator/core.py` becomes `core/mediator.py`.
- **G1:** a role registry that the mediator, `nash_pick`, contracts and report iterate.
- **Verify:**
  - Golden master byte-identical.
  - A test that `core` imports nothing from agents, infra or the app layer.

**9 One evaluation harness and summary.**
- Merge `mediator/eval_batch.py` into `evaluation/`: live and dry modes, one summary file, `python -m autonomousprime eval`.
- **C3:** `evaluation/report.py` writes numbers and tables only. The findings narrative moves to a hand-written section.
- The console reads the one summary.
- Generated results stop being committed, except dated snapshots.
- Republish `docs/RESULTS.md` once.
- **Verify:**
  - Every RESULTS.md number that differs from today's is explained by story 3's stated moves.
  - The console shows the same consensus rate as RESULTS.md.

**10 The console inside the package.**
- Move `app_prime.py` to `autonomousprime/ui/app.py`, split into render helpers, importing only `service` and the summary.
- Streamlit moves to a `[ui]` extra (K1).
- **U1:** the default is a dry run; replay is optional and never overwritten; live only via the toggle.
- Remove:
  - the hackathon branding and `time.sleep` staging;
  - the "released to ATC…" and "Logged at" text;
  - the teammates' laptop paths in `results/*.json`.
- **N8:** round, stage and team labels come from RunResult and the role registry.
- Update README and `docs/usage.md`.
- **Verify:** smoke test against the new path; the five demo rows match the snapshot.

**11 Refactor sweep.**
- Work through the deferred lists collected in story plans.
- **G7:** code comments citing mvp-spec §n, "team B", lane, MVP or stub either point at a current doc or are deleted.
- Remove the stale ruff ignore for `app.py`.
- Update the `docs/architecture.md` component table and diagram to the new tree.
- **Verify:** the table lists only modules that exist; full CI green.

## Review gate (me, after every story, before merge)

1. Read the full diff. Reject anything outside the code map or on the Never list.
2. In a clean venv on the merged result, run the full pytest, ruff and format checks.
3. Golden master: byte-identical for every pure-move commit.
   - Each allowed move (story 3 B…, story 5's id commit, story 9's republish) must match its stated cause. Otherwise the story is rejected.
4. Run the story's `verify` line from `tickets.toml`.
5. On failure, findings go back to the same subagent, at most 2 rounds. After that I fix it or mark the story `blocked` and stop.
6. On pass, merge to `refactor/one-core`, push, and set the plan file to `done`. Deferred findings go to story 11.

## Stop conditions and check-ins

- **Stop:**
  - a story blocked after 2 rounds;
  - a golden-master change with no stated cause;
  - CI red on the pushed branch for a cause outside the current story;
  - any decision outside Epic 2's scope (for example, a dependency).
- **Check-in:** story 7's live test (money and a key).
- **Pause:** end of epic.

## Verification (end of Epic 2, before the pause)

- **CI:** green on `refactor/one-core`, installing from `uv.lock`.
- **Timing:** a timed dry run of the default row takes under 2 s.
- **Structure:**
  - The duplication map in `review-current-state.md` has one implementation per row.
  - `grep -rn "import anthropic" src/` shows only `infra/llm.py`.
  - The core import-boundary test passes.
- **Entry points:** `python -m autonomousprime run` and `eval --dry` work; `streamlit run src/autonomousprime/ui/app.py` runs all five demo rows.
- **Hand-off:**
  - commits per story;
  - every golden-number move and its cause;
  - review rounds;
  - deferred items;
  - the CI link;
  - an offer to open a PR to `main`.
