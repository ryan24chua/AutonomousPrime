"""One service function to run a negotiation: the console, the cache script and the CLI all call this.

`negotiate(flight, seed, live)` runs one full negotiation and returns a `RunResult`. `RunResult.to_dict()` is the dict
the console and `results/*.json` read: outcome ("consensus" | "halt_least_cost" | "recommend_cancel"), rounds,
final_plan, log[], document, world, log_path. Every value comes from the mediator's own JSONL log.
A run is live only when the caller passes live=True; an API key in the environment never turns it on (P7).
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv

from autonomousprime import paths
from autonomousprime.agents.atc.world_stub import load_day, pick_focal
from autonomousprime.mediator.adapters import LaneAgent, build_scenario, check_plan, plan_cost
from autonomousprime.mediator.core import AGENTS, Log, run_negotiation
from autonomousprime.mediator.report import render


@dataclass(frozen=True)
class FlightKey:
    """Identifies one flights.csv row."""

    year: int
    month: int
    day: int
    airline: str
    flight_number: str
    origin: str

    @classmethod
    def from_spec(cls, spec: dict) -> "FlightKey":
        """Build from a demo-row dict ({"airline", "flight_number", "origin", "month", "day"}; year defaults to 2015)."""
        return cls(
            int(spec.get("year", 2015)),
            int(spec["month"]),
            int(spec["day"]),
            spec["airline"],
            spec["flight_number"],
            spec["origin"],
        )


class LiveUnavailable(RuntimeError):
    """Live mode was asked for but no API key is configured."""


@dataclass
class RunResult:
    outcome: str
    rounds: int
    final_plan: dict | None
    log: list[dict]
    document: str
    world: dict
    log_path: str
    negotiation_id: str
    votes: dict
    fallback: dict | None
    mediator_outcome: str
    mediator_plan: dict | None

    def to_dict(self) -> dict:
        """The seven keys the console, results/*.json and the golden master read."""
        return {
            "outcome": self.outcome,
            "rounds": self.rounds,
            "final_plan": self.final_plan,
            "log": self.log,
            "document": self.document,
            "world": self.world,
            "log_path": self.log_path,
        }


def find_flight(date: str, dest: str, flight: str | None = None) -> FlightKey:
    """Pick the focal flight on `date` (YYYY-MM-DD) into `dest`; default = biggest weather delay in the busiest weather hour."""
    y, m, d = map(int, date.split("-"))
    row = pick_focal(load_day(y, m, d), dest, flight)
    return FlightKey(
        int(row["YEAR"]),
        int(row["MONTH"]),
        int(row["DAY"]),
        row["AIRLINE"],
        row["FLIGHT_NUMBER"],
        row["ORIGIN_AIRPORT"],
    )


def _find_row(key: FlightKey) -> tuple[list[dict], dict]:
    rows = load_day(key.year, key.month, key.day)
    for r in rows:
        if (r["AIRLINE"], r["FLIGHT_NUMBER"], r["ORIGIN_AIRPORT"]) == (key.airline, key.flight_number, key.origin):
            return rows, r
    raise LookupError(f"row not found: {key}")


def _entry(rnd: int, agent: str, action: str, plan: dict | None, plan_id: str | None, reason: str, s, flags=()):
    chk = check_plan(s, plan) if plan else None
    return {
        "round": rnd,
        "agent": agent,
        "table_plan_id": plan_id,
        "message": {
            "action": action,
            "plan_id": plan_id,
            "plan": plan,
            "need": "",
            "offer": "",
            "reason": reason,
            "flags": list(flags),
        },
        "checker": None
        if chk is None
        else {"valid": chk.valid, "violations": chk.violations, "cost": plan_cost(s, plan)},
    }


def negotiate(flight: FlightKey, seed: int = 7, live: bool = False) -> RunResult:
    """Run one negotiation. live=True -> real Claude votes (needs ANTHROPIC_API_KEY in .env.local); else a dry run."""
    if live:
        load_dotenv(paths.REPO / ".env.local")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise LiveUnavailable("Live mode needs ANTHROPIC_API_KEY in .env.local")
    rows, focal = _find_row(flight)
    s = build_scenario(rows, focal, seed=seed)
    client = None
    if live:
        import anthropic

        client = anthropic.AsyncAnthropic()
    agents = {n: LaneAgent(n, s, live=live, client=client) for n in AGENTS}
    run_id = time.strftime("%Y%m%d-%H%M%S")
    log = Log(paths.REPO / "logs" / f"mediator-{s.negotiation_id}-{run_id}.jsonl", s.negotiation_id)
    f = s.focal_row
    context = {
        "run_id": run_id,
        "mode": "live (round-3 votes by Claude agents)" if live else "dry run (no LLM)",
        "flight": f"{f['AIRLINE']}{f['FLIGHT_NUMBER']} {f['ORIGIN_AIRPORT']}->{f['DESTINATION_AIRPORT']}",
        "date": s.atc_world.date,
        "scheduled_arrival": f["SCHEDULED_ARRIVAL"],
        "event": s.atc_world.event,
        "seed": seed,
        "data": "DOT 2015 flights.csv row + organiser workbook limits",
        "synthetic_inputs": "gate occupancy, filler arrivals, connecting pax, crew report (labelled in each lane)",
    }
    out = asyncio.run(run_negotiation(agents, lambda pl: check_plan(s, pl), lambda pl: plan_cost(s, pl), log, context))
    fb = None
    if out.outcome != "consensus":
        from autonomousprime.fallback.scenario import solve_scenario

        fb = solve_scenario(s, "no_valid_r1" if out.outcome == "no_valid_plan" else "no_consensus_r3")
        log.write(
            3,
            "fallback",
            trigger=fb["fallback"]["trigger"],
            outcome=fb["outcome"],
            plan=fb["plan"],
            cost_usd=fb["cost_usd"],
            total_system_delay_min=fb["total_system_delay_min"],
            detail=fb["fallback"],
        )

    # Rebuild the UI log from the mediator's own log lines.
    lines = [json.loads(x) for x in log.path.read_text().splitlines() if x.strip()]
    ui_log = []
    for line in lines:
        if line["step"] == "proposals" and line["plans"]:
            top = line["plans"][0]
            ui_log.append(
                _entry(
                    1,
                    line["agent"],
                    "propose",
                    top["plan"],
                    None,
                    f"{len(line['plans'])} plans sent; favourite: {top['reason']}",
                    s,
                )
            )
        elif line["step"] == "scores":
            pick = next((x for x in lines if x["step"] == "pick"), None)
            if pick:
                sc, why = line["scores"][pick["plan_id"]]
                ui_log.append(
                    _entry(
                        2,
                        line["agent"],
                        "score",
                        pick["plan"],
                        pick["plan_id"],
                        f"scored {sc} for {pick['plan_id']}: {why}",
                        s,
                    )
                )
        elif line["step"] == "votes":
            plan = next(x for x in lines if x["step"] == "pick")["plan"]
            for agent, v in line["votes"].items():
                ui_log.append(
                    _entry(3, agent, "accept" if v["accept"] else "reject", plan, line["plan_id"], v["reason"], s)
                )
    final = out.plan if out.outcome == "consensus" else (fb or {}).get("plan")
    return RunResult(
        outcome="consensus" if out.outcome == "consensus" else (fb or {}).get("outcome", out.outcome),
        rounds=3 if out.outcome != "no_valid_plan" else 1,
        final_plan=final,
        log=ui_log,
        document=render(log.path),
        world=context,
        log_path=str(log.path),
        negotiation_id=s.negotiation_id,
        votes=out.votes,
        fallback=fb,
        mediator_outcome=out.outcome,
        mediator_plan=out.plan,
    )
