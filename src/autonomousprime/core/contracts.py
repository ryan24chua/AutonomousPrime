"""The message contract: one definition of the agent message, the mediator's result types and the limits.

Agent message (docs/hackathon/mvp-spec.md section 7, docs/architecture.md section 5): every agent's output
must validate against AgentMessage. Ranges (minutes >= 0, HH:MM format, word limits) are enforced in Python
by `validate_ranges`, because structured outputs do not support min/max constraints in the schema.
Mediator results (ScoredPlan, Vote, CheckResult) are frozen dataclasses. Message limits live in
`MessageLimits`, validated at construction; the module-level `LIMITS` is the one instance in use.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class MessageLimits:
    """Word limits and retry count for an agent message (design-register N7). Positive ints; tolerance >= 0."""

    need_words: int = 20
    offer_words: int = 20
    reason_words: int = 30
    word_tolerance: int = 5  # extra words `validate_ranges` allows; the UI trims. ATC's validator allows none.
    max_attempts: int = 2  # calls per turn for a malformed reply: ask, then re-ask once

    def __post_init__(self) -> None:
        for name in ("need_words", "offer_words", "reason_words", "max_attempts"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
                raise ValueError(f"{name} must be a positive int, got {v!r}")
        t = self.word_tolerance
        if isinstance(t, bool) or not isinstance(t, int) or t < 0:
            raise ValueError(f"word_tolerance must be an int >= 0, got {t!r}")

    def word_limits(self) -> dict[str, int]:
        return {"need": self.need_words, "offer": self.offer_words, "reason": self.reason_words}


LIMITS = MessageLimits()

# Version of every consensus-log line (docs/architecture.md section 5). Bump on any change to a line's shape.
LOG_SCHEMA_VERSION = "consensus-log/1.1"

AgentName = Literal["atc", "pilot", "ground"]
Action = Literal["propose", "accept", "counter", "reject"]
Flag = Literal[
    "MINIMUM_FUEL", "DUTY_LIMIT", "DIVERT_RECOMMENDED", "CANCEL_RECOMMENDED", "CREW_OVERTIME", "CONNECTION_RISK"
]  # last two: Ground agent (soft cost, code-derived)


class Plan(BaseModel):
    arrival_slot: str = Field(description="Arrival time at the destination, local HH:MM")
    ground_delay_min: int = Field(description="Minutes the take-off is delayed at the origin")
    holding_min: int = Field(description="Minutes of airborne holding before landing")
    extra_fuel_min: int = Field(description="Extra holding fuel loaded before departure, in minutes")
    gate: Optional[str] = Field(description="Arrival gate id, e.g. C14; null if not this agent's lever (ATC)")
    divert: bool = Field(description="True only if the flight diverts to its alternate airport")


class FailedConstraint(BaseModel):
    rule: Literal["fuel", "crew_duty", "gate", "slot", "none"]
    evidence: list[str] = Field(description="Fact keys with values, e.g. 'plans.P2.assessment.fuel_margin_min=-7.1'")


class Alternative(BaseModel):
    plan_ref: str = Field(description="Candidate id, e.g. P2 or P1-ground-delay")
    summary: str
    status: Literal["candidate", "confirmed"] = Field(description="candidate until the owning agent confirms it")


class ICAPBrief(BaseModel):
    """Optional decision brief (Interests, Constraints, Alternatives, Priorities). Additive: agents and the
    middleman may ignore it; the consensus log and decision document show it."""

    interest: str = Field(description="The outcome being protected and why (interest, not position)")
    red_lines: list[str] = Field(
        default_factory=list, description="Hard limits this agent will never trade, stated up front"
    )
    failed_constraint: Optional[FailedConstraint] = None
    alternatives: list[Alternative] = Field(default_factory=list, description="Ranked, best first")
    concessions: list[str] = Field(default_factory=list, description="What this agent can give up")
    deadline: Optional[str] = None
    requested_next_action: str


class AgentMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: AgentName = Field(alias="from")
    round: int
    action: Action
    plan_id: Optional[str] = Field(default=None, description="Id of the table plan when accepting, e.g. P3")
    plan: Optional[Plan] = Field(default=None, description="Required for propose and counter")
    need: str = Field(description="What this agent needs, <= 20 words")
    offer: str = Field(description="What this agent can give, <= 20 words")
    reason: str = Field(description="<= 30 words, cites a fact key, constraint or objective")
    flags: list[Flag] = Field(default_factory=list)
    icap: Optional[ICAPBrief] = Field(default=None, description="Optional ICAP decision brief")


_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def validate_ranges(msg: AgentMessage) -> list[str]:
    """Return a list of problems the JSON schema cannot express. Empty list = OK."""
    problems = []
    if msg.action in ("propose", "counter") and msg.plan is None:
        problems.append(f"action '{msg.action}' requires a plan")
    if msg.action == "accept" and not msg.plan_id:
        problems.append("action 'accept' requires plan_id")
    if msg.plan is not None:
        p = msg.plan
        if not _HHMM.match(p.arrival_slot):
            problems.append(f"arrival_slot '{p.arrival_slot}' is not HH:MM")
        for name in ("ground_delay_min", "holding_min", "extra_fuel_min"):
            if getattr(p, name) < 0:
                problems.append(f"{name} must be >= 0")
    for name, limit in LIMITS.word_limits().items():
        if len(getattr(msg, name).split()) > limit + LIMITS.word_tolerance:  # small tolerance; trimmed by the UI
            problems.append(f"{name} longer than {limit} words")
    return problems


@dataclass(frozen=True)
class ScoredPlan:
    """One plan as an agent sends it: the full plan, the agent's 0-1 score, and why."""

    plan: dict
    score: float
    reason: str


@dataclass(frozen=True)
class Vote:
    accept: bool
    reason: str
    flags: tuple[str, ...] = ()  # the agent's flags when it votes; empty in a dry run


@dataclass(frozen=True)
class CheckResult:
    valid: bool
    violations: list[str]  # each starts with a rule id, e.g. "C-FUEL-1: ..."
