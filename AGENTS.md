## AutonomousPrime

Decision support for an airline operations-control duty manager at a US hub. ATC, Pilot and Ground Claude agents negotiate a recovery plan for a real DOT 2015 disruption. Code checks and prices every plan, a deterministic solver is the fallback, and the human approves or rejects. Python 3.13 package `autonomousprime` (src layout), Anthropic SDK, Streamlit console. Design lives in `docs/architecture.md` and `docs/adr/`; the refactor roadmap and tickets live in `_bmad-output/initiative-post-hackathon/`.

## Policy

- Never commit keys. Real keys go in `.env.local` (gitignored); add new variable names to `.env.example`.
- Name branches by purpose (`refactor/…`, `fix/…`, `docs/…`), never with a `claude/` prefix.
- Commit small, `git pull --rebase` before pushing, keep `main` deployable.
- Ask before adding a dependency or an external service.
- Change the message schema or a rule ID (`C-WAKE-1`, `C-FUEL-1`, …) in its own commit, with a version bump, and update `docs/architecture.md` §5–6 in that commit. A rule whose meaning changes gets a new ID.

## Product invariants

- Code computes every number, checks every rule and decides termination and the pick. An agent's LLM proposes, chooses and explains; code validates anything it proposes and recomputes every number in it. Never put arithmetic, scheduling or legality checks in a prompt; write code.
- Every negotiation is bounded and terminates in code, and a deterministic fallback (`fallback/scenario.py`) always exists for a negotiation that ends without consensus.
- Safety is a filter, not a price: drop a plan that breaks a hard rule before costing it, and re-check the picked plan before it leaves the mediator.
- No hindsight: agents never see `DEPARTURE_TIME`, `ARRIVAL_TIME`, `ARRIVAL_DELAY`, `DEPARTURE_DELAY`, `WHEELS_ON/OFF`, `ELAPSED_TIME`, `AIR_TIME`, `TAXI_IN/OUT`. Only evaluation reads them, as a historical reference.
- A human decides: the duty manager approves or rejects every outcome, and cancellation is only ever a recommendation.
- Log every step to the append-only JSONL consensus log. Seed and label every synthetic input (`real`, `derived`, `workbook`, `synthetic`).

## Current design defaults (change by ADR)

These came from the hackathon brief and are the design today, not rules. Changing one takes an ADR; see `docs/adr/0004-post-hackathon-design-baseline.md`.

- Three roles, ATC, Pilot and Ground, each with its own prompt and its own call and seeing only its own facts. No call plays several roles. Each role acts as its organisation's delegate: ATC for the airport's traffic management, Pilot for the airline's flight operations, Ground for the airport and ground handler.
- Agents choose among code-built options; today every plan comes from ATC's arrival menu.
- A negotiation without consensus goes to the fallback, today after three rounds. Target (epic-negotiation): the fallback is still computed, and the duty manager chooses between the two best checked plans with each organisation's objection.
- All LLM access goes through one gateway on the Anthropic SDK with our own loop; no agent framework today.
- Scope today: an airline OCC duty manager at a US hub, one delayed arrival, the organisers' DOT 2015 file, a Streamlit console. `_bmad-output/initiative-post-hackathon/design-register.md` lists every choice like these, with its ruling.
- Direction (decided 2026-11-11): several flights recovered at once, cascading effects predicted in code, the full 2015 DOT data; agents negotiate under an authority model with typed proposals. Build order in `_bmad-output/initiative-post-hackathon/tickets/tickets.toml`.

## Where things are

- Roles: `src/autonomousprime/agents/{atc,pilot,ground}/`, with each prompt beside its agent. The shared message schema and workbook limits are in `agents/schema.py` and `agents/constraints.py`.
- Negotiation:
  - `mediator/core.py`: rounds, Nash pick, log.
  - `mediator/adapters.py`: `check_plan`, `plan_cost`, `LaneAgent`.
  - `mediator/report.py`: decision record.
- Console: `app_prime.py` → `middleman.py` → mediator. The replay files are `results/<row_id>.json`.
- Resolve repo paths through `autonomousprime/paths.py`, never `Path(__file__).parents[n]`.
- `docs/hackathon/` is archived hackathon material (brief, framing, specs); `mvp-spec.md` there is the old `CLAUDE.md` that code comments cite. Read it for provenance, never as current rules: this block and `docs/architecture.md` win.
- Cost weights are duplicated in `agents/ground/cost_config.py`, `agents/atc/config.py` and `fallback/config.py` until epic-one-core merges them. Change all three together.

## Running and verifying

- Install editable: `pip install -e ".[dev]"`. `paths.py` reads `data/` from the source checkout, so a regular install cannot find it.
- `pytest` (about 40 s) runs the unit tests, the golden master and the console smoke test. Live tests are deselected; opt in with `pytest -m live`, which makes real API calls and costs money.
- Leave `tests/golden/snapshot.json` unchanged in a refactor. A commit meant to change behaviour regenerates it with `python -m tests.golden.update` and says in its message which numbers moved and why.
- `python -m autonomousprime.mediator.run` runs one negotiation without the LLM (`--live` uses Claude) and writes its log and decision record to `logs/`.
- Run `python -m autonomousprime.evaluation.evaluate` only to republish results: it rewrites `docs/RESULTS.md` and `results/evaluation/`.
- Verify a change by running it (tests, golden master, console) before calling it done; test-first TDD is not required.

## Conventions that differ from defaults

- Agent calls use `claude-sonnet-5-5` with `max_tokens` set and the system prompt cached. Ask before changing the model tier.

## Known pitfalls

- `middleman.negotiate(row)` and `make_cache.py` go live whenever `ANTHROPIC_API_KEY` is set. In code and tests, pass `live=False` or unset the key. `make_cache.py` also overwrites the console's replay files.
- Each uncached world build re-reads the 37 MB `flights.csv` (about 3 s). In tests, load the rows once and reuse them (see `tests/golden/capture.py`).
