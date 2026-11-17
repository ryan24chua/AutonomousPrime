"""ATC live path with a fake client: typed output, validator, correction loop, reject on give-up; dry run unchanged."""

import asyncio
import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from autonomousprime.agents.atc.agent import ATCAgent, ATCOutput
from autonomousprime.core.world import build_world
from autonomousprime.infra import data


@pytest.fixture(scope="module")
def world():
    rows = data.day(2015, 4, 24)
    row = next(r for r in rows if r["DESTINATION_AIRPORT"] == "DFW" and float(r["WEATHER_DELAY"] or 0) > 15)
    return build_world(rows, row, seed=7).atc


def resp(parsed, stop="end_turn"):
    return SimpleNamespace(parsed_output=parsed, stop_reason=stop, _request_id="r", usage=SimpleNamespace())


class Fake:
    def __init__(self, *script):
        self.script, self.calls, self.messages = list(script), [], self

    async def parse(self, **kw):
        self.calls.append(kw)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def valid_round1(world):
    agent = ATCAgent(world, client=Fake())
    return ATCOutput.model_validate(json.loads(agent._stand_in(1, None)))


def run(agent):
    return asyncio.run(agent.propose())


def test_output_model_mirrors_the_dict_contract(world):
    body = valid_round1(world).model_dump(by_alias=True)
    assert list(body) == ["from", "round", "action", "plan_id", "plan", "need", "offer", "reason", "flags"]
    assert set(body["plan"]) == {"arrival_slot", "ground_delay_min", "holding_min", "extra_fuel_min", "gate", "divert"}
    assert ATCOutput.model_json_schema()["properties"]["flags"]["items"]["enum"] == ["MINIMUM_FUEL", "EMERGENCY_FUEL"]


def test_success(world):
    fake = Fake(resp(valid_round1(world)))
    out = run(ATCAgent(world, client=fake))
    assert out["status"] == "OK" and out["action"] == "propose" and out["validator_errors"] == []
    assert out["message_id"].endswith("-r1-atc") and out["from"] == "atc"
    assert fake.calls[0]["max_tokens"] == 700 and "output_config" not in fake.calls[0]
    assert fake.calls[0]["output_format"] is ATCOutput


def test_validator_failure_then_valid_recovers_on_attempt_two(world):
    good = valid_round1(world)
    bad = good.model_copy(update={"action": "accept"})  # round 1 must propose
    fake = Fake(resp(bad), resp(good))
    out = run(ATCAgent(world, client=fake))
    assert out["status"] == "OK" and len(fake.calls) == 2
    assert "REJECTED BY THE VALIDATOR" in fake.calls[1]["messages"][-1]["content"]


def test_invalid_twice_is_reject_with_error_status(world):
    bad = valid_round1(world).model_copy(update={"action": "accept"})
    out = run(ATCAgent(world, client=Fake(resp(bad), resp(bad))))
    assert out["action"] == "reject" and out["status"] == "ERROR" and out["validator_errors"]


def test_refusal_then_valid_recovers(world):
    fake = Fake(resp(None, "refusal"), resp(valid_round1(world)))
    assert run(ATCAgent(world, client=fake))["status"] == "OK" and len(fake.calls) == 2


@pytest.mark.parametrize("stop", ["refusal", "max_tokens"])
def test_refusal_or_truncation_twice_is_reject(world, stop):
    out = run(ATCAgent(world, client=Fake(resp(None, stop), resp(valid_round1(world), stop))))
    assert out["action"] == "reject" and out["status"] == "ERROR" and out["validator_errors"] == [stop]


def test_api_error_is_reject_after_the_gateway_retry(world):
    err = anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com"))
    fake = Fake(err, err)
    out = run(ATCAgent(world, client=fake))
    assert out["action"] == "reject" and out["status"] == "ERROR" and len(fake.calls) == 2


def test_dry_run_needs_no_client_and_is_deterministic(world):
    a, b = (asyncio.run(ATCAgent(world, dry_run=True).propose()) for _ in range(2))
    assert a == b and a["status"] == "OK" and a["action"] == "propose"
