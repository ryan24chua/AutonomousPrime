---
type: epic
title: "A plan's knock-on through the rest of the day is predicted and costed"
parent: initiative-post-hackathon
covers: [R12]
after: [epic-full-2015-data, epic-plans-time-and-events]
refined: false
risk: high
---

# A plan's knock-on through the rest of the day is predicted and costed

## Description

Today "knock-on" means the first-come-first-served delay a plan pushes onto other arrivals in the same hour or two. Nothing follows the aircraft, the crew or the passengers past the focal flight.

This epic propagates a plan's delays through the rest of the day:
- **Aircraft:** along the aircraft's later legs, with turnaround minimums at each airport.
- **Crew:** through the crew's duty, against duty limits.
- **Passengers:** through connections, against minimum connection times.

The inputs are only the delays known at decision time (design-register S5). The prediction is code, not an LLM. Each plan's cost includes its predicted cascade, and the duty manager sees it. Evaluation, and only evaluation, compares the prediction with what happened in 2015 (AD-8).

## Outcome

The duty manager sees what a plan does to the rest of the day before approving it, and agents argue over real consequences.

## Done when

- A late-aircraft row shows its predicted delay on each later leg of the same tail, and the plan's cost includes it.
- Evaluation reports predicted against actual 2015 downstream delay, with an error measure.
- No agent or core module reads an outcome column; the existing import-boundary test covers the cascade module.

## Boundaries

- Belongs to epic-several-flights-at-once: recovering the affected flights together.
- Not yet: network-wide re-optimisation, such as re-routing aircraft or crew swaps.

## References

- register — `_bmad-output/initiative-post-hackathon/design-register.md`, S4, S5, W2
- review — `_bmad-output/initiative-post-hackathon/review-current-state.md`, F3 (missed connections unpriced)
