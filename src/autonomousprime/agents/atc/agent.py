"""ATC agent: one Claude call per round, schema-validated, one re-ask, then reject (docs/hackathon/mvp-spec.md §5)."""

import json
import time
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from autonomousprime import paths
from autonomousprime.agents.base import Checked, RoleAgent
from autonomousprime.core.contracts import LIMITS
from autonomousprime.core.world import World
from autonomousprime.infra.llm import ROLE_SETTINGS, LLMResult

from . import config
from .facts import build_atc_facts
from .menu import Option, build_menu, cheapest_valid, earliest_valid
from .prompt import user_message
from .validate import validate

ENVELOPE_KEYS = frozenset(
    {"schema_version", "negotiation_id", "message_id", "state_revision", "ruleset_id", "status", "validator_errors"}
)
LOG_DIR = paths.LOGS / "atc"


class ATCPlan(BaseModel):
    arrival_slot: str
    ground_delay_min: int
    holding_min: int
    extra_fuel_min: int
    gate: None = None  # ATC never sets gate or divert (validate.py enforces it)
    divert: bool = False


class ATCOutput(BaseModel):
    """What the ATC model returns: the dict contract of agent contract v0.2 minus the code-filled envelope."""

    model_config = ConfigDict(populate_by_name=True)

    from_: Literal["atc"] = Field(alias="from")
    round: int
    action: Literal["propose", "accept", "counter", "reject"]
    plan_id: Optional[str] = None
    plan: Optional[ATCPlan] = None
    need: str
    offer: str
    reason: str
    flags: list[Literal["MINIMUM_FUEL", "EMERGENCY_FUEL"]] = Field(default_factory=list)  # == config.FLAGS


def parse_json(text: str) -> dict | None:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _system() -> str:
    from . import prompt  # read at call time

    return prompt.SYSTEM


class ATCAgent(RoleAgent):
    """`client`: an LLMGateway, a raw async client (tests), or None for the live gateway; unused in a dry run."""

    def __init__(self, world: World, dry_run: bool = False, negotiation_id: str | None = None, client=None):
        self.world = world
        f = world.focal
        self.negotiation_id = (
            negotiation_id or f"{world.dest}-{world.date.replace('-', '')}-{f['AIRLINE']}{f['FLIGHT_NUMBER']}"
        )
        self.menu: list[Option] = build_menu(world)
        self.flags: set[str] = set()
        self.dry_run = dry_run
        if dry_run:
            self.role, self._prompt, self.gateway = "atc", _system, None
        else:
            super().__init__("atc", _system, client)
        self._last_meta: dict = {}
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.log_path = LOG_DIR / f"atc-calls-{time.strftime('%Y%m%d')}.jsonl"

    # --- public API for the middle man ---
    async def propose(self) -> dict:
        return await self._turn(1)

    async def respond(self, round_no: int, table: dict, check: dict, others: list[dict]) -> dict:
        for m in others:
            self.flags |= {f for f in m.get("flags", []) if f in config.FLAGS}
        return await self._turn(round_no, table, check, others)

    # --- internals ---
    def _envelope(self, round_no: int) -> dict:
        """Code-filled envelope fields; never taken from the LLM."""
        return {
            "schema_version": config.SCHEMA_VERSION,
            "negotiation_id": self.negotiation_id,
            "message_id": f"{self.negotiation_id}-r{round_no}-atc",
            "state_revision": 0,
            "ruleset_id": config.RULESET_ID,
        }

    async def _turn(
        self, round_no: int, table: dict | None = None, check: dict | None = None, others: list[dict] | None = None
    ) -> dict:
        facts = build_atc_facts(self.world, self.menu, self.flags)
        user = user_message(round_no, facts, table, check, others)
        if self.dry_run:  # no LLM, nothing awaited: the same loop as before the gateway
            return self._turn_dry(round_no, user, facts, table, check, others)
        messages = [{"role": "user", "content": user}]

        def check_reply(out: ATCOutput) -> Checked:
            body = out.model_dump(by_alias=True)
            errors = validate(body, round_no, self.menu, user, self.flags, table)
            if not errors:
                return Checked(body)
            return Checked(
                errors=errors,
                followup=[
                    {"role": "assistant", "content": out.model_dump_json(by_alias=True)},
                    {"role": "user", "content": user_message(round_no, facts, table, check, others, errors)},
                ],
            )

        def on_failure(res: LLMResult) -> list[dict] | None:
            if res.kind in ("transient_error", "api_error"):
                return None  # the gateway already retried; the duty manager sees a reject
            why = f"invalid reply: {res.error}" if res.kind == "invalid" else "no JSON object"
            return [{"role": "user", "content": user_message(round_no, facts, table, check, others, [why])}]

        def on_attempt(attempt: int, res: LLMResult, errors: list[str]) -> None:
            self._last_meta = {"latency_s": res.latency_s, "usage": res.usage}
            text = res.parsed.model_dump_json(by_alias=True) if res.parsed is not None else ""
            self._log(round_no, attempt, text, errors)

        turn = await self.run_turn(messages, ATCOutput, check_reply, on_failure=on_failure, on_attempt=on_attempt)
        if turn.ok:
            return {**self._envelope(round_no), **turn.value, "status": "OK", "validator_errors": []}
        return self._reject(round_no, turn.errors)

    def _turn_dry(self, round_no, user, facts, table, check, others) -> dict:
        messages = [{"role": "user", "content": user}]
        errors: list[str] = []
        for attempt in range(1, LIMITS.max_attempts + 1):
            text = self._stand_in(round_no, table)
            body = parse_json(text)
            if body is not None:
                body = {k: v for k, v in body.items() if k not in ENVELOPE_KEYS}
            errors = (
                validate(body, round_no, self.menu, user, self.flags, table) if body is not None else ["no JSON object"]
            )
            self._log(round_no, attempt, text, errors)
            if not errors:
                return {**self._envelope(round_no), **body, "status": "OK", "validator_errors": []}
            messages += [
                {"role": "assistant", "content": text},
                {"role": "user", "content": user_message(round_no, facts, table, check, others, errors)},
            ]
        return self._reject(round_no, errors)

    def _reject(self, round_no: int, errors: list[str]) -> dict:
        return {
            **self._envelope(round_no),
            "from": "atc",
            "round": round_no,
            "action": "reject",
            "plan_id": None,
            "plan": None,
            "need": "",
            "offer": "",
            "reason": "Invalid output after one re-ask; treated as reject.",
            "flags": [],
            "status": "ERROR",
            "validator_errors": errors,
        }

    def _stand_in(self, round_no: int, table: dict | None) -> str:
        """Dry run: deterministic reply with no LLM, to exercise the pipeline. Never used in the demo path."""
        if "EMERGENCY_FUEL" in self.flags:
            opt = earliest_valid(self.menu)
        elif "MINIMUM_FUEL" in self.flags:
            opt = min((o for o in self.menu if o.valid and o.holding_min == 0), key=lambda o: o.arrival_slot)
        else:
            opt = cheapest_valid(self.menu)
        body = {"from": "atc", "round": round_no, "need": "Thin margin: no spare arrival slot this hour.", "flags": []}
        if round_no == 1:
            body |= {"action": "propose", "plan_id": opt.option_id, "plan": opt.plan()}
        else:
            tp = table["plan"]
            t_opt = next(
                (
                    o
                    for o in self.menu
                    if (o.arrival_slot, o.ground_delay_min, o.holding_min)
                    == (tp["arrival_slot"], tp["ground_delay_min"], tp["holding_min"])
                ),
                opt,
            )
            wants_counter = opt.option_id != t_opt.option_id and (
                "EMERGENCY_FUEL" in self.flags
                or opt.total_system_delay_min <= t_opt.total_system_delay_min - config.CAP10_TOLERANCE_MIN
            )
            if wants_counter and round_no == 2:
                body |= {"action": "counter", "plan_id": opt.option_id, "plan": opt.plan()}
            elif wants_counter:
                body |= {"action": "reject", "plan_id": None, "plan": None}
            else:
                opt = t_opt
                body |= {"action": "accept", "plan_id": table["plan_id"], "plan": dict(tp)}
        if body["action"] == "reject":
            body |= {
                "offer": "",
                "reason": f"Own option {opt.option_id} has lower total_system_delay_min "
                f"({opt.total_system_delay_min}) than the table; no counter in round {round_no}.",
            }
        else:
            body |= {
                "offer": f"Slot {opt.arrival_slot} via ground delay.",
                "reason": f"Arrival cap reached; knock-on {opt.knock_on_min} min.",
            }
        return json.dumps(body)

    def _log(self, round_no: int, attempt: int, text: str, errors: list[str]) -> None:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "agent": "atc",
            "round": round_no,
            "attempt": attempt,
            "negotiation_id": self.negotiation_id,
            "message_id": f"{self.negotiation_id}-r{round_no}-atc",
            "dry_run": self.dry_run,
            "model": ROLE_SETTINGS["atc"].model,
            "raw": text,
            "validator_errors": errors,
            **getattr(self, "_last_meta", {}),
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
