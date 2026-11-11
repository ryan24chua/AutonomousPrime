---
type: epic
title: "The bugs RESULTS.md lists are fixed with measured numbers, and the human decision is logged"
parent: initiative-post-hackathon
covers: [R6, R8]
after: [epic-one-core]
refined: false
risk: medium
---

# The bugs RESULTS.md lists are fixed with measured numbers, and the human decision is logged

## Description

Now that each concern lives once, fix the known defects one per story, each updating the golden master and RESULTS.md with the number that moved: missed connections priced in the system cost (RESULTS §5.1), extra fuel sized from the Pilot's holdable fuel so "depart on time and hold" becomes possible (§5.2), weather cutting capacity in the focal hour at every hub (§5.3), connection counts capped by aircraft seats (§5.6), and the synthetic scheduled-gate conflict made a labelled scenario parameter (§5.7). Approve/Reject is appended to the run's consensus log.

## Outcome

The published numbers come from a model without the known distortions, and the audit trail ends in the duty manager's decision.

## Done when

- Each fix is one commit with its golden-master diff and a RESULTS.md before/after line.
- At least one evaluated row picks a "depart on time and hold" plan, or RESULTS.md explains why none should.
- Approving a plan in the console adds a `human_decision` line (timestamp, plan id, choice) to that run's log.

## Boundaries

- Belongs to epic-negotiation-beyond-three-rounds: the ATC vote/pick mismatch (§5.5).
- Belongs to epic-airborne-and-diversion: diversion as an option.
- Belongs to epic-one-core story 3 (decision 2026-11-11): one shared disrupted arrival across roles (§5.4), so the DFW-20150303-MQ3275 false "no valid plan" is fixed there.

## References

- parent — `_bmad-output/initiative-post-hackathon/initiative-post-hackathon.md`, R6, R8
- results — `docs/RESULTS.md` §5 items 1–4, 6, 7
- review — `_bmad-output/initiative-post-hackathon/review-current-state.md`, F1, F2, F3, F9, F11, F12
- architecture — AD-4, AD-5, AD-9, AD-10, AD-11
