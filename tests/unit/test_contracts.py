"""core/contracts.py: round-trips, limits validation, and validate_ranges reading LIMITS."""

from dataclasses import asdict

import pytest

from autonomousprime.core.contracts import (
    LIMITS,
    AgentMessage,
    Alternative,
    CheckResult,
    FailedConstraint,
    ICAPBrief,
    MessageLimits,
    Plan,
    ScoredPlan,
    Vote,
    validate_ranges,
)

PLAN = Plan(arrival_slot="14:30", ground_delay_min=10, holding_min=5, extra_fuel_min=0, gate="C14", divert=False)


def _msg(**kw) -> AgentMessage:
    base = dict(
        **{"from": "pilot"}, round=1, action="propose", plan=PLAN, need="a b", offer="c d", reason="cites fact x"
    )
    base.update(kw)
    return AgentMessage(**base)


def _roundtrip(model):
    return type(model).model_validate(model.model_dump(by_alias=True))


def test_plan_roundtrip():
    assert _roundtrip(PLAN) == PLAN


def test_icap_roundtrip():
    brief = ICAPBrief(
        interest="protect the crew duty limit",
        red_lines=["no divert"],
        failed_constraint=FailedConstraint(rule="fuel", evidence=["plans.P2.assessment.fuel_margin_min=-7.1"]),
        alternatives=[Alternative(plan_ref="P2", summary="slower", status="candidate")],
        concessions=["gate"],
        deadline="14:00",
        requested_next_action="accept P2",
    )
    assert _roundtrip(brief) == brief


@pytest.mark.parametrize("with_plan", [True, False])
@pytest.mark.parametrize("with_icap", [True, False])
def test_agent_message_roundtrip(with_plan, with_icap):
    icap = ICAPBrief(interest="x", requested_next_action="y") if with_icap else None
    msg = _msg(
        plan=PLAN if with_plan else None, icap=icap, action="propose" if with_plan else "reject", flags=["DUTY_LIMIT"]
    )
    dumped = msg.model_dump(by_alias=True)
    assert dumped["from"] == "pilot"
    assert _roundtrip(msg) == msg


def test_dataclass_roundtrips():
    for obj in (
        ScoredPlan({"arrival_slot": "14:30"}, 0.8, "why"),
        Vote(True, "ok"),
        CheckResult(False, ["C-FUEL-1: short"]),
    ):
        assert type(obj)(**asdict(obj)) == obj


@pytest.mark.parametrize("field", ["need_words", "offer_words", "reason_words", "max_attempts"])
@pytest.mark.parametrize("bad", [0, -1, 1.5, True])
def test_limits_reject_non_positive(field, bad):
    with pytest.raises(ValueError):
        MessageLimits(**{field: bad})


def test_limits_reject_negative_tolerance():
    with pytest.raises(ValueError):
        MessageLimits(word_tolerance=-1)
    assert MessageLimits(word_tolerance=0).word_tolerance == 0


def test_limits_today_values():
    assert LIMITS.word_limits() == {"need": 20, "offer": 20, "reason": 30}
    assert (LIMITS.word_tolerance, LIMITS.max_attempts) == (5, 2)


def test_validate_ranges_flags_long_reason_from_limits():
    assert validate_ranges(_msg(reason=" ".join(["w"] * 35))) == []  # within limit + tolerance
    assert validate_ranges(_msg(reason=" ".join(["w"] * 36))) == ["reason longer than 30 words"]


def test_validate_ranges_follows_limits(monkeypatch):
    import autonomousprime.core.contracts as contracts

    tight = MessageLimits(reason_words=3, word_tolerance=0)
    monkeypatch.setattr(contracts, "LIMITS", tight)  # restored after the test; the global is not mutated
    assert validate_ranges(_msg(reason="one two three four")) == ["reason longer than 3 words"]
    assert contracts.LIMITS is tight
    monkeypatch.undo()
    assert LIMITS.reason_words == 30
    assert validate_ranges(_msg(reason="one two three four")) == []
