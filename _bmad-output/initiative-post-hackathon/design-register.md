# Design-choice register: what still binds after the hackathon

Every design or architecture choice that limits where the project can go, whether or not a document called it a hackathon constraint. It supersedes `constraints-audit.md` (2026-11-02), whose rows are mapped at the end.

Built on 2026-11-11 from three read-only sweeps of the repository at `ec69cda`: agents and mediator, data/world/evaluation, and UI/tooling/docs. About 290 raw findings, grouped into 45 rows. ★ marks a finding no planning document recorded before.

**Rulings.**
- **Retire:** delete the rule or behaviour.
- **Demote:** it stays the current design but stops being an invariant; changing it takes an ADR.
- **Relax:** keep the intent, change the rule.
- **Keep:** unchanged.
- **Planned:** an epic already covers it.
- **Open:** the user's vision decides; the row stays as it is until then.

The user approved the plan on 2026-11-11, so every row's recommendation is applied except the Open ones. "Lands in" names the document, epic or story that now carries the row.

Path shorthand: `PLAN/` = `_bmad-output/initiative-post-hackathon/`; "spine" = `PLAN/architecture-target/architecture-target.md`; `epic-N.story` = a story id in that epic's `tickets/tickets.toml`.

## G. Rules from the brief that were labelled permanent

| ID | Choice (where) | Origin | Blocks | Ruling | Lands in |
|---|---|---|---|---|---|
| G1 ★ | Exactly ATC, Pilot and Ground. The names are written into types (`agents/schema.AgentName`, `mediator/core.AGENTS`), `nash_pick`, the log convention (spine "Roles") and the UI copy. | Brief: "avoid combining the 3 roles" | Adding a role (dispatch, crew scheduling, traffic management), dropping one, a single-planner baseline | **Demote.** Roles become a registry; "one role per prompt, own facts only" is the default. | AGENTS.md defaults; ADR-0004; spine AD-2 and Roles convention; epic-one-core story 8 |
| G2 ★ | A negotiation without consensus may end only in the deterministic fallback, "never in another agent turn" (AGENTS.md, audit K3). | Brief deliverable | A re-vote on the runner-up, escalating to the human mid-negotiation, re-planning on new information | **Relax.** Keep "bounded, terminates in code, a fallback always exists"; drop "the only exit". | AGENTS.md invariant; ADR-0004; spine AD-6; epic-negotiation |
| G3 ★ | LLM output may hold only option ids, votes and closed-enum flags; any number in it is ignored; plans come only from code menus (spine AD-1, initiative R5). Epic-negotiation's numeric concession already contradicts it. | Brief and rubric | Concessions that carry a bound; LLM-proposed plan edits that code then validates | **Relax** to LLM-Modulo: the LLM may propose; code validates the proposal and recomputes every number. | AGENTS.md invariant; ADR-0004; spine AD-1; initiative R5 |
| G4 | No agent framework, Anthropic SDK only, only `infra/llm.py` imports `anthropic` (AGENTS.md Policy, audit K10, spine AD-7). | Old CLAUDE.md §15, written for a sponsored hackathon | Agent SDK, MCP tools, other model providers | **Demote** "never a framework"; **Keep** one LLM gateway. | AGENTS.md defaults; ADR-0004; spine AD-7 |
| G5 ★ | Approve/Reject happens "in the console" (AGENTS.md). | Rubric "trust" | Approval through an API or a notification | **Keep** "a human decides; cancellation is only a recommendation"; **Retire** "in the console". | AGENTS.md invariant |
| G6 | Schema or rule-id changes go in their own commit "and tell the team" (AGENTS.md); rule-id meanings are frozen (spine AD-5, initiative). | Four-lane coordination | Nothing serious; team process from the hackathon | **Retire** "tell the team"; **Keep** a versioned contract and "a new meaning gets a new id". | AGENTS.md Policy |
| G7 ★ | Hackathon documents still read as current:<br>• `docs/challenge-2-brief.md` calls itself "source of truth … read before building".<br>• `challenge-2-framing.md` and `agent-alignment.md` ("PROPOSED … object by 15:00") sit in `docs/` and are linked as current.<br>• About 20 code comments cite `mvp-spec §n`.<br>• The planning docs cite "CLAUDE.md §n", which is now only `@AGENTS.md`. | Archive left half-done | Readers and agents keep loading the contest as rules | **Retire.** Move the three docs to `docs/hackathon/`; re-point citations in living docs. | This commit; code comments in epic-one-core story 11 |
| G8 ★ | The AGENTS.md block is managed by bmad: "edits inside this block are replaced on refresh". | Tooling | The user's own edits there are lost on a refresh | **Open.** Recommended: remove the markers so the file is the user's. Until decided, edit it only through bmad-project-context or with care. | Initiative open question |

## P. Planning choices that froze hackathon behaviour

| ID | Choice (where) | Blocks | Ruling | Lands in |
|---|---|---|---|---|
| P1 ★ | The golden master is byte-identical (spine AD-11, AGENTS.md). The 1.09 MB snapshot pins plans, costs, every mediator log line, reason text, decision-record prose and the known bugs. A $1 weight change once gave a 5,116-line diff. | Any fix during the refactor; diffs too large to review | **Relax.** The snapshot pins plans, costs, outcomes, rule ids and round counts. A behaviour change lands as its own commit that regenerates it and states which numbers moved. | Spine AD-11; epic-one-core story 12 (narrows the snapshot first) |
| P2 ★ | Epic-one-core is bug-compatible: the new `WorldState` keeps each lane's disagreeing values; ATC's vote tolerance is preserved; the loader keeps raw csv strings. | The new core starts with the old inconsistencies | **Relax** with P1: one value per derived field in story 3, each unification its own commit. ATC's rule is still fixed in epic-negotiation. Raw strings stay (decision 2026-11-10). | epic-one-core constraints and story 3 |
| P3 ★ | Epic-negotiation's Done-when says "golden master unchanged" while the same epic changes vote/pick alignment and the fallback order. | The epic cannot be finished as written | **Retire** the contradiction; `max_rounds = 3` stays the default. | epic-negotiation Done-when |
| P4 ★ | "Out" lists:<br>• Inherited from framing §1: live feeds, real gate layouts, FAA Part 117, RECAT/CWT, aircraft registry (initiative: "still out").<br>• "Out: replacing Streamlit, agent framework, database beyond JSONL" (initiative; the spine only said "Deferred").<br>• Epic-airborne: several alternates, en-route weather, real fuel.<br>• Epic-evaluation: live feeds, monitoring. | Realism work, with no recorded reason | **Relax.** Each becomes "Not yet", with the trigger that brings it in. | Initiative Boundaries; spine Deferred; epic files |
| P5 | Assumptions: Streamlit stays the UI, Python 3.13, src layout (initiative). | Another front end | **Keep** Python 3.13 and src layout; **Demote** Streamlit to the current UI. | Initiative Notes |
| P6 | Epic order (negotiation, then realism, then scale) waits on "which extension first". | Planning past epic-one-core | **Open**, after the S rows. | Initiative open question |
| P7 ★ | Audit X9 made "live runs are the default when a key is present" the target, which is the footgun AGENTS.md warns about (cost, overwritten replays). | Safe local runs | **Retire.** A run is live only when the caller asks (`--live`, a UI toggle); nothing infers it from a key. | epic-one-core story 1 |

## S. Product scope

| ID | Choice (where) | Blocks | Ruling |
|---|---|---|---|
| S1 | The persona is an airline OCC duty manager at a US hub (AGENTS.md, initiative, framing §1). | Other users: traffic management, ramp control, crew scheduling | **Open** |
| S2 | The data is the organiser's pre-filtered subset:<br>• 358,774 delayed rows; no on-time, cancelled or diverted flights; no October.<br>• Background traffic is therefore synthetic, scaled from DFW on 24 Apr for every airport.<br>• Year 2015 is hard-coded (`middleman.py`, `app_prime.py`, `mediator/eval_batch.py`).<br>• `airports.csv` has no timezone.<br>• `flights.csv` is in git, and any new data folder is gitignored by default. | Real background traffic, other years, non-US airports | **Open** (with the storage question) |
| S3 | All limits come from the organiser workbook: four size-class profiles labelled "SYNTHETIC … not real airport data"; every Large hub identical (150 gates, 90 ops/h); rules parsed by label prefix. | Real per-airport limits | **Relax:** the workbook is the default config; per-airport overrides carry provenance. Lands in: initiative Notes; spine AD-10. |
| S4 | One focal flight. Background flights are passive (first come, first served). Only the destination airport is modelled. `Plan` has no flight id; the run id and `negotiate(flight_key)` assume one flight; multi-flight is "Out for now". | Network or bank recovery, tail rotations, several Pilot agents | **Open** |
| S5 ★ | Two event types, thresholds 15 and 20 written in 6+ places. The event size is the realised `WEATHER_DELAY`/`LATE_AIRCRAFT_DELAY`, which is a perfect forecast, an accepted hole in "no hindsight". `INTERESTS` raises KeyError on any new type. Pilot classifies events differently from ATC and Ground (6,373 rows). | New event types; forecast or uncertainty scenarios | **Relax:** the event becomes an interface with one classifier (epic-plans-time-and-events). **Open:** whether the size stays labelled hindsight or becomes a forecast. |

## N. Negotiation shape in code

| ID | Choice (where) | Blocks | Ruling | Lands in |
|---|---|---|---|---|
| N1 | Three straight-line phases, no loop. Claude only votes in round 3; propose and score are pure code even live; `others_reasons` is ignored (`mediator/core.py`, `mediator/adapters.py`). | Real negotiation | **Planned** | epic-negotiation |
| N2 ★ | Two incompatible protocols. The agent folders implement propose/accept/counter/reject over rounds; the mediator runs 10 plans → shortlist → score → vote. Each `AgentMessage` is reduced to an accept bool, discarding need, offer, flags, the ICAP brief and any counter. | All agent-side negotiation code is dead | **Relax.** The epic's protocol ADR keeps one protocol and deletes the other. | epic-negotiation |
| N3 | Unanimity required. The Nash product multiplies rank positions (not utilities) by a cost score, with a 0.05 floor and fixed tie-breaks; cost is an unweighted fourth factor; gains are measured from 0. ADR-0001 and the review say "keep". | Majority or weighted rules, utility-based bargaining | **Demote** ADR-0001 to the current default. | ADR-0001 status; epic-negotiation |
| N4 ★ | ATC's menu is the universe of plans: 5-min grid, 90-min horizon (too short for a 185-min event), each option pure ground delay or pure holding. ATC's own check is a stub that is always valid. Off-menu fails C-CAP-1, so diversion is unreachable and cancellation is never a plan. | Mixed plans, long events, diversion, cancellation as an option | **Relax.** A core plan generator combines the levers; diversion becomes a plan type. | epic-plans-time-and-events; epic-airborne |
| N5 ★ | A plan has six fixed fields everywhere (`agents/schema.Plan`, `mediator/core.PLAN_FIELDS`, ATC `PLAN_KEYS`), no flight id, and an `"HH:MM"` arrival with no date (regex-enforced). | New levers, multi-flight plans, arrivals after midnight | **Relax.** A versioned plan contract with a flight id and absolute time. | epic-plans-time-and-events |
| N6 ★ | Fixed levers per role: ATC may not set gate or divert; Ground has only the gate, with turnaround fixed at the minimum so C-TURN-1 can never fail; only the Pilot diverts; code picks the gate for ATC and Pilot plans. | Richer trade-offs, real turnaround decisions | **Relax.** Each role's levers are declared in config. | epic-plans-time-and-events |
| N7 | Message rules enforced three ways: word limits (shared check +5 words, ATC none), ATC's "no number not in the prompt", Ground's I1–I7 citations. A breach uses the only retry; `for attempt in (1, 2)` is written three times. | Reliable live runs | **Planned.** Limits and retry count become settings. | epic-one-core story 4 |
| N8 | The report, `middleman.py` and the UI parse exact log step names and the strings "3 rounds" and "three teams". | A protocol or role change silently breaks the UI | **Planned.** They read a versioned outcome object. | epic-one-core stories 1, 10 |
| N9 | The fallback takes the cheapest valid plan; it ignores flags and votes, has no divert or extra-fuel variants, returns a hard-coded `"VALID"`; 5 of its 7 triggers never fire; it depends on mediator internals. | A safety-ranked fallback | **Planned** | epic-negotiation; epic-airborne |

## W. World and data model

| ID | Choice (where) | Blocks | Ruling | Lands in |
|---|---|---|---|---|
| W1 | Three world builders disagree on event type, disrupted arrival, year filter, "2400" and seeding; two are stubs "until team B's build_world lands" and are what production runs. | Consistency | **Planned**, unified per P2 | epic-one-core story 3 |
| W2 ★ | Time is minutes after local midnight, with no date or timezone, and the spine made that the convention. The four HHMM helpers disagree on "2400". 15,140 overnight rows and 25,513 arrivals pushed past midnight land on the wrong day. ATC sorts `"HH:MM"` strings. | Overnight flights, crew duty, several airports, tail rotations | **Relax.** Core uses absolute local time (date, minutes, airport timezone). | Spine Time convention; epic-plans-time-and-events |
| W3 ★ | The synthetic Ground world:<br>• Gates are `'ABCDEFGH'[i//30]` and spares are drawn outside terminal A, so it crashes at every airport with 30 gates or fewer: 294 of 322, all Small hubs and Non-hubs. That is the unstated reason the evaluation samples only Large and Medium hubs.<br>• The scheduled gate is always "A12" and always busy, so the status quo has a gate conflict built in.<br>• The RNG is not keyed per flight, so all 32 evaluated plans use A12 or B20. | Most airports; credible gate results | **Relax.** Fixed in the one world: gates for any airport size, RNG keyed per flight, scheduled gate from the world. | epic-one-core story 3 |
| W4 | The ATC world:<br>• One airport, focal hour −1 to +2.<br>• DFW-derived filler ratios everywhere.<br>• A flat 30% weather cut only in hours with ≥ 5 weather-delayed arrivals.<br>• Arrival share 50%.<br>• Every aircraft wake class "Large", so the wake table never binds. | Realistic capacity | **Planned** in part (weather bug). Parameters move to config. | epic-known-gaps-closed; epic-plans-time-and-events |
| W5 | Aircraft and passengers:<br>• Narrowbody/widebody by distance only, no seat counts (a 50-seat jet shows 191 missed connections).<br>• Two independent connection models; only Ground's is priced.<br>• Crew report built from delayed legs across time zones.<br>• Alternate = nearest airport > 100 nm; blank coordinates crash it. | Credible passenger and crew results | **Planned** in part | epic-known-gaps-closed |
| W6 ★ | Five full-CSV readers with different keys; only ATC filters by year. The focal flight is re-found by (airline, flight, origin, month, day). An airport missing from the workbook raises KeyError. Data is found only in a source checkout (`paths.REPO`). | A second data year; installed use | **Relax.** The loader keys by full date and flight; a data-directory setting. | epic-one-core story 2 |

## C. Cost and evaluation

| ID | Choice (where) | Blocks | Ruling | Lands in |
|---|---|---|---|---|
| C1 | Plan cost = ATC option cost + Ground cost; the Pilot side (delay-caused missed connections, extra fuel, diversion) is unpriced. The evaluation uses another weight table. Weights sit in 3+ files plus a literal `* 5.0`. ATC's cost is a "stub until team B". | Honest cost | **Planned** | epic-one-core story 6; epic-known-gaps-closed |
| C2 ★ | Evaluation:<br>• N = 32 with one seed.<br>• Large and Medium hubs only, because of W3.<br>• Baselines are scored with the same `plan_cost` the system optimises, which is circular.<br>• Live mode re-runs a biased subset.<br>• `llm_calls = 3` and `rounds_max: 3` are hard-coded. | Trustworthy results | **Planned**, plus an independent scorer | epic-evaluation-at-scale |
| C3 ★ | `evaluation/report.py`:<br>• Types this run's findings as prose ("18.3 min at DFW", "A12", "~50-seat MQ jet").<br>• Cites stale paths and a "CLAUDE.md §n" requirements table.<br>• Overwrites the committed `docs/RESULTS.md`.<br>A second harness (`mediator/eval_batch.py`, live by default, DFW only) feeds the UI. | RESULTS.md stays wrong after every fix | **Relax.** The generator writes numbers; findings live in a hand-written section. | epic-one-core story 9 |

## U, L, K. Console, LLM layer, packaging

| ID | Choice (where) | Blocks | Ruling | Lands in |
|---|---|---|---|---|
| U1 | The console:<br>• Streamlit script logic at module top level.<br>• Five hand-picked rows ordered for the pitch.<br>• "Replay saved run" on by default (the smoke test asserts it); turning it off overwrites the committed replays.<br>• Live whenever a key is set.<br>• Approve/Reject only in session state, yet the UI says "Logged at …" and "released to ATC, the pilot and the ground crew".<br>• Hackathon branding, `time.sleep` animation, a wrong rule-id map, replay files with two teammates' laptop paths. | An honest UI; any use beyond the demo | **Retire** the demo-first defaults, branding, the "released" text and the laptop paths; the rest is **Planned**. | epic-one-core stories 1, 10; epic-known-gaps-closed (decision logged) |
| L1 | The model id is written three times; `max_tokens` 700 vs 4000; three client styles. ATC's disk cache replays old answers on live re-runs. Call logs are inconsistent; cost and latency are not captured. | Cost/latency evaluation; per-role models | **Planned.** "Ask before changing the model tier" stays (user rule). | epic-one-core story 7 |
| K1 ★ | Packaging:<br>• Streamlit is a hard dependency of the core (no `[ui]` extra).<br>• No lockfile while dependencies are floor-only and the golden master is strict, so CI is not reproducible.<br>• `requires-python >= 3.13` has no code reason.<br>• `logs/` is gitignored, so the audit trail never leaves the machine, while generated `results/` is tracked.<br>• A ruff ignore names the deleted `app.py`. | Library use; reproducible CI; a shareable audit trail | **Relax.** `[ui]` extra and the ruff fix in epic-one-core. **Open:** a lockfile (`uv.lock`, a new tool file) and where run logs are kept. | epic-one-core stories 10, 11; initiative open questions |

## Mapping from constraints-audit.md

| Audit row | Now |
|---|---|
| X1, X6 | N1, P3 (Planned) |
| X2, X3, X4, X5, X7, X8 | Done in epic-safety-net-and-hygiene |
| X9 | P7 (its replacement text is retired), U1 |
| X10 | S2 (Open) |
| X11 | L1 |
| X12 | C2 |
| L1 | S5 |
| L2 | N4, N6 |
| L3, L4 | N4, N9; epic-airborne |
| L5 | S4 (Open) |
| L6 | S3 |
| L7 | N7 |
| L8 | Done (dev toolchain decision 2026-11-03); "ask before a dependency" stays policy |
| K1 | G3: kept, wording relaxed |
| K2 | G1: demoted to a default |
| K3 | G2: relaxed |
| K4 | Kept (ADR-0002) |
| K5 | Kept; S5 records the event-size hole |
| K6 | G5: kept, "in the console" retired |
| K7, K8, K9 | Kept |
| K10 | G4: demoted, LLM gateway kept |
