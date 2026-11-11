# Constraints audit: what the hackathon imposed, and what still binds

> **Superseded on 2026-11-11 by [design-register.md](design-register.md),** which re-rules every row below (mapping at its end) and adds the choices this audit missed. Kept as history.

Every constraint the build followed, where it came from, and whether it still matters now that the contest is over.
**Retire** = drop it. **Relax** = keep the intent, change the rule. **Keep** = still a product invariant (carried into the architecture spine as an `AD`).

Sources: `docs/hackathon/challenge-2-brief.md` (brief, rubric), `CLAUDE.md` as it was on 2026-11-02, now `docs/hackathon/mvp-spec.md` (§ numbers refer to its second half), `docs/hackathon/challenge-2-framing.md`, `docs/adr/`.

## Retire

| # | Constraint | Source | Why it no longer matters | What replaces it |
|---|---|---|---|---|
| X1 | Resolve "in under 3 turns"; exactly 3 rounds; ≤ 9 agent calls per scenario | Brief; CLAUDE.md §2, §5; ADR-0003 | A judging criterion, not an operational limit. A fixed 3 also forces the shortcut in X6. The real need is *bounded, deterministic* termination (kept as K3). | A `NegotiationPolicy` (round cap, wall-clock deadline, LLM-call budget, monotonic concession) with the cap as configuration. New ADR supersedes ADR-0003. |
| X2 | 6-hour timeline, 15:00 feature freeze, 15:45 submit, 3-minute pitch | CLAUDE.md §1, §17 | Event logistics. | Normal epic and story planning. |
| X3 | Rubric weights as the optimisation target (realism 20%, soundness 25% …, time discipline 5%) | Brief; CLAUDE.md §3 | No judges. The *practices* behind them stay (honest evaluation, traceability); the scoring does not. | Product success measures in the initiative's Done when. |
| X4 | "One owner per folder, don't edit another person's folder"; lanes A–D | CLAUDE.md "Roles", §16 | Root cause of the duplication: `mediator/adapters.py` exists to avoid editing lanes; four world builders, three cost tables, five checkers, two schemas. | One package, shared modules, code review instead of folder ownership. |
| X5 | "Optimise for a working demo, not production quality"; "skip test-first TDD"; "simplest end-to-end first (terminal), then UI" | CLAUDE.md top half, §18 | The project is now the starting point for further work. | Tests in every story, CI, lint, a golden-master safety net. |
| X6 | Rounds 1–2 use code rankings; Claude only votes in round 3 | ADR-0003 "Negative"; architecture §8 | A time-box shortcut. It means the "negotiation" is mostly code, and the ATC dry-run vote rule disagrees with the pick rule (10/32 no consensus). | Claude acts in every round, still choosing only among code-computed options (K1). |
| X7 | Singapore-task template: "real multi-step Singapore task", Singpass/CAPTCHA rule, SG API keys | CLAUDE.md top half; `.env.example` | Template text from before the Airbus problem was picked; contradicts the actual product. | Delete; `.env.example` keeps `ANTHROPIC_API_KEY` only. |
| X8 | "Stack TBD", "Roles TBD", "Stack & layout — TODO" | CLAUDE.md top half, §15 | Settled by what was built: Python, Streamlit, `anthropic` SDK. | State the stack and layout. |
| X9 | Demo-first data handling: 5 hand-picked demo rows, "Replay saved run" default, cached JSON in `results/` | CLAUDE.md "Rules"; `demo_rows.py`, `make_cache.py` | A stage-safety device. Useful as fixtures, wrong as the primary path. | Replays become test fixtures; live runs are the default when a key is present. |
| X10 | Only the organiser's pre-filtered subset (358,774 delayed rows), hence synthetic filler traffic | Brief "Provided data"; framing change log | The full BTS 2015 file (5.8 M rows, on-time flights included) is public. Real background traffic removes the biggest synthetic input. | Open question: data size and storage (not in git). |
| X11 | Model pinned to Sonnet for agents and crafter; "Haiku only if latency forces it" | CLAUDE.md §14 | Cost/latency trade-off was set for a demo. | Per-role model in config; evaluation reports cost per run. |
| X12 | Evaluation fixed at N = 32, one world seed | Framing §7; RESULTS.md caveats | Sized to fit a 30-second hackathon run. | ≥ 200 rows, ≥ 3 seeds, sensitivity sweep. |

## Relax

| # | Constraint | Source | Keep the intent | Change |
|---|---|---|---|---|
| L1 | Only two events: weather (`WEATHER_DELAY > 15`) and late aircraft (`LATE_AIRCRAFT_DELAY > 20`) | Brief; CLAUDE.md §4 | Events stay grounded in a real data row. | Event model becomes an interface; runway closure / equipment / crew are candidates once data or a labelled synthetic source exists. |
| L2 | Only three decisions (arrival slot, gate, continue/divert) | CLAUDE.md §4 | Agents choose from code-generated options. | Add options as the world model supports them (e.g. delay the next leg, swap gate earlier). |
| L3 | Focal flight is pre-departure only (`airborne=False`) | CLAUDE.md §4 "Flight state" | The `airborne` flag already exists. | Airborne scenarios in scope: holding limited by fuel on board, diversion when exceeded. |
| L4 | No diversion or cancellation options "because the data has none" | Framing change log item 3; ADR-0002 gap | Cancellation stays a human-only recommendation (K6). | Diversion becomes a real option for the mediator and fallback (needed for L3). |
| L5 | One Pilot agent (focal flight); background flights are passive | CLAUDE.md §4 "Agents" | Background flights still cannot be harmed silently: their knock-on is costed. | Multi-flight negotiation is a candidate extension (open question). |
| L6 | Organiser workbook is the only source of limits (gates, turnaround, fuel, crew, runway ops), flagged "SYNTHETIC planning limits" | Brief data; `ground_agent/assumptions.py` | Every limit carries provenance. | Workbook stays the default config; real sources can override per airport. |
| L7 | Message word limits (need/offer ≤ 20 words, reason ≤ 30) | CLAUDE.md §7 | Short, auditable reasons. | Keep short, but make the limit a schema setting, not a validator failure that forces a re-ask. |
| L8 | "Ask before adding dependencies or external services" | CLAUDE.md §18 | Keep the dependency set small. | Pre-agree a dev toolchain (ruff, pytest config, maybe a columnar reader) in the opening epic. |

## Keep (product invariants)

| # | Constraint | Source | Becomes |
|---|---|---|---|
| K1 | Code computes every number and checks every rule; the LLM proposes, chooses among code options and explains (LLM-Modulo) | Brief "avoid"; CLAUDE.md §18; framing §2 | AD-1 |
| K2 | The three roles are never merged into one prompt; each agent sees only its own facts | Brief "avoid"; CLAUDE.md §7 | AD-2 |
| K3 | No unbounded loops: termination, pick rule and fallback are code; any non-consensus ends in the deterministic non-AI fallback | Brief; ADR-0003 (intent, not the number 3) | AD-6 |
| K4 | Safety is a filter, never a price; final check before anything leaves the mediator | Brief "avoid"; ADR-0002 | AD-3 |
| K5 | No hindsight: agents never see outcome columns | CLAUDE.md §6 | AD-8 |
| K6 | A human decides; cancellation is only ever a recommendation | Brief; rubric "trust"; CLAUDE.md §4 | AD-9 (and the decision is now logged) |
| K7 | Append-only, traceable consensus log for every step | Brief; CLAUDE.md §11 | AD-9 |
| K8 | Synthetic inputs are seeded, labelled and reproducible | CLAUDE.md §6; framing §6 | AD-4 |
| K9 | Never commit keys; real keys in `.env.local` | CLAUDE.md "Rules" | Consistency convention |
| K10 | No agent frameworks; the SDK plus our own loop | CLAUDE.md §15; framing §9 | AD-7 |
