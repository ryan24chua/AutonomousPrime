---
type: epic
title: "Plans, time and events are not tied to one day, six fields or two causes"
parent: initiative-post-hackathon
covers: [R2, R7]
after: [epic-one-core]
refined: false
risk: high
---

# Plans, time and events are not tied to one day, six fields or two causes

## Description

The code assumes one local day, one plan shape, one source of plans and two event types. The design-choice register (2026-11-11) relaxes each of these four assumptions:

- **Time (W2).** Core time becomes absolute local time: the service date, minutes after local midnight and the airport's timezone, with `"HH:MM"` used only for display. Arrivals pushed past midnight and overnight flights (15,140 rows) then land on the right day, and a crew duty clock across airports becomes possible.
- **Plan contract (N5).** The plan becomes a versioned contract with a flight id and absolute times, so a new lever or a second flight does not break the six fixed fields.
- **Plan generator (N4, N6).** A core plan generator builds plans from each role's declared levers, for example ATC slots and holding, Ground gates and turnaround, and Pilot extra fuel and diversion. Today ATC's arrival menu is the universe of plans. With the generator, mixed ground delay and holding, longer horizons and diversion become plan types, and C-TURN-1 can fail when it should.
- **Events and ATC world (S5, W4).** One classifier and an event interface replace the two hard-coded causes and their scattered thresholds. The ATC world's capacity, weather and wake parameters move to config, each with a provenance label.

This epic is not refined yet. It runs third, after epic-one-core and epic-known-gaps-closed (decision 2026-11-11, register P6). Epics full-2015-data, cascading-effects and several-flights-at-once build on its absolute time and plan contract.

## Outcome

The world and plan model can carry overnight arrivals, new levers, new event types and, later, more than one flight, without another contract break.

## Done when

- A late-aircraft row whose earliest arrival falls after midnight produces plans dated the next day, and its background traffic comes from that day.
- A plan with both ground delay and holding can be generated, checked and costed.
- Adding an event type means one classifier entry and its config, not edits in several modules.
- The golden master is updated once per behaviour change, each commit stating which numbers moved.

## Boundaries

- Belongs to epic-airborne-and-diversion: airborne scenarios and diversion as a chosen plan, which build on this epic's plan types.
- Belongs to epic-several-flights-at-once: negotiating several flights. The flight id in the plan contract is what makes that possible.
- Open: whether an event's size stays the realised delay-cause minutes (a labelled hindsight hole) or becomes a forecast (register S5).

## References

- register — `_bmad-output/initiative-post-hackathon/design-register.md`, W2, N4, N5, N6, S5, W4
- architecture — AD-1, AD-4, AD-5; spine Time convention
- results — `docs/RESULTS.md` §5.4 (horizon too short for a 185-min event)
