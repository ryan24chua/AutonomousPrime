---
type: epic
title: "Every 2015 flight is available, not only the delayed ones"
parent: initiative-post-hackathon
covers: [R13]
after: [epic-one-core, epic-plans-time-and-events]
refined: false
risk: medium
---

# Every 2015 flight is available, not only the delayed ones

## Description

The organisers' file holds only flights that already meet the brief's delay filter: 358,774 rows, with no on-time, cancelled or diverted flights. At DFW on 24 Apr 2015 it has 203 of about 933 arrivals; the rest of the airport is synthetic filler, scaled from that one day to every airport. Tail rotations are mostly missing: only 144,746 linked delayed-leg pairs. Recovering several flights at once and predicting cascades both need what is missing (design-register S2).

This epic:
- **Fetch:** a script downloads the full 2015 DOT on-time data (about 5.8 M flights, the same 31 columns), verifies its checksum, and stores it in a gitignored data folder. The organisers' subset stays as the golden-master input until a commit moves it.
- **Load:** the loader from epic-one-core reads it through its per-day cache. Whether 5.8 M rows still fit the standard-library loader is measured first; duckdb is the fallback and needs approval as a dependency (decision 2026-11-10).
- **Use:** real flights replace synthetic background traffic, each labelled `real`.
- **Timezones:** airport timezones come from a labelled source, for absolute time (epic-plans-time-and-events).

## Outcome

Background traffic, tail rotations and connections come from what flew, not from synthetic filler.

## Done when

- A fresh clone gets the data with one command, and the checksum is verified.
- A world for DFW on 24 Apr 2015 contains all of that day's real arrivals, and no synthetic filler where real flights exist.
- A dry run stays under the 2 s target with a warm cache, or the epic records the measured time and the loader decision.

## Boundaries

- Approval needed at the start (AGENTS.md: ask before an external service): the download source. Candidates are the BTS on-time reporting download, which uses different column names and needs a converter, and a mirror with the same columns as today's file.
- Not yet: other years and non-US data.

## References

- register — `_bmad-output/initiative-post-hackathon/design-register.md`, S2, W6
- framing — `docs/hackathon/challenge-2-framing.md`, change log (what the subset lacks)
- epic-one-core — story 2 (loader), decision 2026-11-10 (duckdb revisit trigger)
