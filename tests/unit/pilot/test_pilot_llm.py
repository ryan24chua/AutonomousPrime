"""Pilot live path with a fake client: success, correction loop, refusal / truncation / API errors -> reject."""

import asyncio
from types import SimpleNamespace

import anthropic
import httpx2

from autonomousprime.core.contracts import AgentMessage
from tests.unit.pilot.test_pilot import INP, PilotAgent, plan


def counter(reason="fuel"):
    return AgentMessage(
        **{"from": "pilot"},
        round=2,
        action="counter",
        plan=plan("17:55", gd=25),
        need="ATC confirm slot",
        offer="ground delay",
        reason=reason,
    )


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


def ask(*script):
    fake = Fake(*script)
    msg = asyncio.run(PilotAgent(client=fake).respond(INP, "P1", plan("17:55", hold=25), {"valid": True}, [], 2))
    return msg, fake


def test_success():
    msg, fake = ask(resp(counter()))
    assert msg.action == "counter" and len(fake.calls) == 1
    assert fake.calls[0]["max_tokens"] == 4000 and fake.calls[0]["output_config"] == {"effort": "medium"}


def test_prompt_is_read_at_call_time(tmp_path, monkeypatch):
    from autonomousprime.agents.pilot import agent as mod

    p = tmp_path / "pilot.md"
    monkeypatch.setattr(mod, "PROMPT_PATH", p)
    fake = Fake(resp(counter()), resp(counter()))
    agent = PilotAgent(client=fake)
    agent._prompt = p
    p.write_text("PROMPT V1")
    asyncio.run(agent.respond(INP, "P1", plan("17:55", hold=25), {"valid": True}, [], 2))
    p.write_text("PROMPT V2")
    asyncio.run(agent.respond(INP, "P1", plan("17:55", hold=25), {"valid": True}, [], 2))
    assert [c["system"][0]["text"] for c in fake.calls] == ["PROMPT V1", "PROMPT V2"]


def test_malformed_then_valid_recovers_on_attempt_two():
    msg, fake = ask(resp(counter("word " * 60)), resp(counter()))
    assert msg.action == "counter" and len(fake.calls) == 2
    assert "Fix these problems" in fake.calls[1]["messages"][-1]["content"]


def test_refusal_then_valid_recovers():
    msg, fake = ask(resp(None, "refusal"), resp(counter()))
    assert msg.action == "counter" and "stop_reason=refusal" in fake.calls[1]["messages"][-1]["content"]


def test_refusal_twice_is_reject():
    msg, fake = ask(resp(None, "refusal"), resp(None, "refusal"))
    assert msg.action == "reject" and msg.reason.endswith("treated as reject.") and len(fake.calls) == 2


def test_max_tokens_twice_is_reject():
    msg, fake = ask(resp(counter(), "max_tokens"), resp(counter(), "max_tokens"))
    assert msg.action == "reject" and len(fake.calls) == 2


def test_api_error_other_than_transient_is_reject_at_once():
    r = httpx2.Response(400, request=httpx2.Request("POST", "https://api.anthropic.com"))
    msg, fake = ask(anthropic.BadRequestError("bad", response=r, body=None))
    assert msg.action == "reject" and len(fake.calls) == 1


def test_connection_error_uses_the_next_attempt():
    err = anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com"))
    msg, fake = ask(err, err, resp(counter()))  # the gateway's retry uses one call; attempt 2 succeeds
    assert msg.action == "counter" and len(fake.calls) == 3
