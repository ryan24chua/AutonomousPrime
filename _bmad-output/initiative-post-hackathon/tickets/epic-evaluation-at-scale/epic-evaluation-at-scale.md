---
type: epic
title: "Results are measured on 200+ disruptions with live cost and latency"
parent: initiative-post-hackathon
covers: [R9]
after: [epic-negotiation-beyond-three-rounds]
refined: false
risk: medium
---

# Results are measured on 200+ disruptions with live cost and latency

## Description

Retire the 32-row, one-seed evaluation sized for a hackathon (constraints-audit X12). Run ≥ 200 stratified rows over ≥ 3 world seeds, across every hub size (the Ground world works at every airport after epic-one-core story 3), in dry and live modes on the same sample (not a re-run of the no-consensus subset), with LLM cost, latency and tokens taken from the call log, bootstrap CIs, a cost-weight sensitivity sweep, and a failure section that names at least one case where the agents do worse than the fallback or fail to agree, with its cause. Live runs use the response cache so re-runs are free. Every method is also scored by a reference the system does not optimise, such as the realised 2015 delay read only by evaluation (AD-8), because scoring the baselines with the same `plan_cost` the mediator minimises makes the comparison circular (design-register C2). Optionally, add the LLM-written explanation the original design called the document crafter (mvp-spec §12): prose only, from the log only, numbers filled by code. If the data-storage question allows, replace synthetic filler traffic with real on-time flights from the full BTS 2015 file.

## Outcome

Anyone can judge from RESULTS.md whether negotiation beats the solver and status quo, at what LLM cost, and where it fails.

## Done when

- RESULTS.md headline is computed on ≥ 200 rows × ≥ 3 seeds, with CIs, live and dry.
- Per-run LLM cost and latency (mean, P90) are reported.
- At least one failure is shown with its cause and the run log linked.
- A second run with a warm cache makes zero API calls and reproduces the numbers.
- The headline table shows each method under both the system cost and the independent reference.

## Boundaries

- Not yet: live operational feeds (trigger: a feed and a user who needs it), production monitoring (trigger: a deployment).
- Touch point: full BTS data — waits on the initiative's data-storage open question.

## References

- parent — `_bmad-output/initiative-post-hackathon/initiative-post-hackathon.md`, R9
- constraints — `_bmad-output/initiative-post-hackathon/constraints-audit.md`, X10, X12
- register — `_bmad-output/initiative-post-hackathon/design-register.md`, C2, W3
- framing — `docs/hackathon/challenge-2-framing.md` §7 (metrics, baselines, ablations)
- architecture — AD-7, AD-8
