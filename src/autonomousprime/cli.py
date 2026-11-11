"""Command line: `python -m autonomousprime run [--date 2015-04-24] [--dest DFW] [--flight MQ3086] [--seed 7] [--live]`.

Runs one negotiation (dry by default, no LLM; --live uses the lanes' Claude agents) and writes the decision record.
"""

import argparse
import json
import sys
from pathlib import Path

from autonomousprime.mediator.report import write_report
from autonomousprime.service import LiveUnavailable, find_flight, negotiate


def _run(a: argparse.Namespace) -> int:
    try:
        r = negotiate(find_flight(a.date, a.dest, a.flight), seed=a.seed, live=a.live)
    except LiveUnavailable as e:
        print(e, file=sys.stderr)
        return 2
    report = write_report(Path(r.log_path))
    print(f"Negotiation {r.negotiation_id}: {r.mediator_outcome}")
    print("Plan:", json.dumps(r.mediator_plan))
    print("Votes:", json.dumps(r.votes, indent=1))
    if r.fallback:
        fb = r.fallback
        print(f"Fallback ({fb['fallback']['trigger']}): {fb['outcome']}", json.dumps(fb["plan"]))
    print("Log:", r.log_path)
    print("Decision record:", report)
    return 0


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="autonomousprime")
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one negotiation")
    run.add_argument("--date", default="2015-04-24")
    run.add_argument("--dest", default="DFW")
    run.add_argument("--flight", help="e.g. MQ3086; default = biggest weather delay in the busiest weather hour")
    run.add_argument("--seed", type=int, default=7)
    run.add_argument(
        "--live", action="store_true", help="round-3 votes by Claude (needs ANTHROPIC_API_KEY in .env.local)"
    )
    run.set_defaults(func=_run)
    args = p.parse_args(argv)
    sys.exit(args.func(args))
