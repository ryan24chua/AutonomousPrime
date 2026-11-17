"""The LLM gateway with a fake client: parse, response cache, retry, typed failures, call log; and the SDK boundary."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from pydantic import BaseModel, ValidationError

from autonomousprime import paths
from autonomousprime.infra.llm import ROLE_SETTINGS, LiveUnavailable, LLMGateway, make_client


class Out(BaseModel):
    answer: str


def reply(parsed=Out(answer="yes"), stop="end_turn"):
    usage = SimpleNamespace(input_tokens=11, output_tokens=7, cache_creation_input_tokens=3, cache_read_input_tokens=5)
    return SimpleNamespace(parsed_output=parsed, stop_reason=stop, usage=usage, _request_id="req_1")


class FakeClient:
    def __init__(self, *script):
        self.script, self.calls = list(script), []
        self.messages = self

    async def parse(self, **kw):
        self.calls.append(kw)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def gateway(client, tmp_path, **kw):
    kw.setdefault("retry_delay_s", 0.0)
    return LLMGateway(client, cache_dir=tmp_path / "cache", log_path=tmp_path / "calls.jsonl", **kw)


def call(gw, text="hello", role="pilot"):
    return asyncio.run(gw.parse(role, "SYSTEM PROMPT", [{"role": "user", "content": text}], Out))


def conn_error():
    return anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com"))


def status_error(code):
    resp = httpx2.Response(code, request=httpx2.Request("POST", "https://api.anthropic.com"))
    cls = anthropic.InternalServerError if code >= 500 else anthropic.BadRequestError
    return cls("boom", response=resp, body=None)


def test_success_returns_parsed_model_with_cached_system_and_role_settings(tmp_path):
    client = FakeClient(reply())
    res = call(gateway(client, tmp_path), role="pilot")
    assert res.ok and res.parsed == Out(answer="yes") and not res.cache_hit
    kw = client.calls[0]
    assert kw["system"] == [{"type": "text", "text": "SYSTEM PROMPT", "cache_control": {"type": "ephemeral"}}]
    assert kw["model"] == "claude-sonnet-5-5" and kw["max_tokens"] == 4000
    assert kw["output_format"] is Out and kw["output_config"] == {"effort": "medium"}


def test_role_settings_table():
    assert {r: (s.model, s.max_tokens, s.effort) for r, s in ROLE_SETTINGS.items()} == {
        "atc": ("claude-sonnet-5-5", 700, None),
        "pilot": ("claude-sonnet-5-5", 4000, "medium"),
        "ground": ("claude-sonnet-5-5", 4000, "medium"),
    }


def test_atc_sends_no_effort(tmp_path):
    client = FakeClient(reply())
    call(gateway(client, tmp_path), role="atc")
    assert client.calls[0]["max_tokens"] == 700 and "output_config" not in client.calls[0]


def test_several_system_texts_put_the_breakpoint_on_the_last(tmp_path):
    client = FakeClient(reply())
    asyncio.run(gateway(client, tmp_path).parse("ground", ["ROLE", "FACTS"], [{"role": "user", "content": "x"}], Out))
    assert [("cache_control" in b) for b in client.calls[0]["system"]] == [False, True]


def test_identical_second_call_is_a_cache_hit_without_a_second_api_call(tmp_path):
    client = FakeClient(reply(), reply())
    gw = gateway(client, tmp_path)
    first, second = call(gw), call(gw)
    assert len(client.calls) == 1
    assert second.cache_hit and second.parsed == first.parsed
    assert not call(gw, text="different").cache_hit and len(client.calls) == 2  # a different request misses


def test_cache_survives_a_new_gateway_and_can_be_turned_off(tmp_path):
    call(gateway(FakeClient(reply()), tmp_path))
    assert call(gateway(FakeClient(), tmp_path)).cache_hit
    client = FakeClient(reply(), reply())
    off = gateway(client, tmp_path, cache=False)
    call(off), call(off)
    assert len(client.calls) == 2


def test_failures_are_not_cached(tmp_path):
    client = FakeClient(reply(None, stop="refusal"), reply())
    gw = gateway(client, tmp_path)
    assert call(gw).kind == "refusal"
    assert call(gw).ok and len(client.calls) == 2
    assert not list((tmp_path / "cache").glob("*.tmp"))


def test_one_retry_on_a_transient_error_then_success(tmp_path):
    client = FakeClient(conn_error(), reply())
    res = call(gateway(client, tmp_path))
    assert res.ok and res.attempts == 2 and len(client.calls) == 2


@pytest.mark.parametrize("make_err", [conn_error, lambda: status_error(500)])
def test_transient_error_twice_is_a_typed_failure(tmp_path, make_err):
    client = FakeClient(make_err(), make_err())
    res = call(gateway(client, tmp_path))
    assert res.kind == "transient_error" and not res.ok and res.parsed is None and len(client.calls) == 2


def test_other_api_errors_are_typed_and_not_retried(tmp_path):
    client = FakeClient(status_error(400))
    res = call(gateway(client, tmp_path))
    assert res.kind == "api_error" and len(client.calls) == 1


def test_refusal_max_tokens_and_missing_output_are_typed(tmp_path):
    client = FakeClient(reply(None, "refusal"), reply(Out(answer="cut"), "max_tokens"), reply(None, "end_turn"))
    gw = gateway(client, tmp_path)
    kinds = [call(gw, text=str(i)).kind for i in range(3)]
    assert kinds == ["refusal", "max_tokens", "no_output"]


def test_schema_invalid_reply_is_typed_invalid(tmp_path):
    try:
        Out.model_validate({})
    except ValidationError as e:
        err = e
    res = call(gateway(FakeClient(err), tmp_path))
    assert res.kind == "invalid" and res.error


def test_programming_errors_are_not_swallowed(tmp_path):
    with pytest.raises(KeyError):
        call(gateway(FakeClient(KeyError("bug")), tmp_path))


def test_call_log_has_usage_and_latency_and_no_message_text(tmp_path):
    gw = gateway(FakeClient(reply()), tmp_path)
    call(gw, text="SECRET-BODY-TEXT")
    call(gw, text="SECRET-BODY-TEXT")
    raw = (tmp_path / "calls.jsonl").read_text()
    miss, hit = [json.loads(x) for x in raw.splitlines()]
    assert miss["role"] == "pilot" and miss["model"] == "claude-sonnet-5-5" and miss["kind"] == "ok"
    assert (miss["input_tokens"], miss["output_tokens"]) == (11, 7)
    assert (miss["cache_creation_input_tokens"], miss["cache_read_input_tokens"]) == (3, 5)
    assert miss["latency_s"] >= 0 and miss["cache_hit"] is False and miss["stop_reason"] == "end_turn"
    assert hit["cache_hit"] is True
    assert "SECRET-BODY-TEXT" not in raw and "SYSTEM PROMPT" not in raw and "yes" not in raw


def test_default_paths_come_from_paths_module():
    gw = LLMGateway(FakeClient())
    assert gw.cache_dir == paths.CACHE / "llm" and gw.log_path == paths.LOGS / "llm_calls.jsonl"


def test_make_client_without_key_raises_live_unavailable(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("autonomousprime.infra.llm.load_dotenv", lambda *a, **k: None)
    with pytest.raises(LiveUnavailable, match="ANTHROPIC_API_KEY"):
        make_client()


def test_service_live_unavailable_is_the_infra_class():
    from autonomousprime.service import LiveUnavailable as FromService

    assert FromService is LiveUnavailable


def test_dry_run_imports_no_sdk(tmp_path):
    code = (
        "import sys, pathlib\n"
        "from autonomousprime import service\n"
        "r = service.negotiate(service.FlightKey(2015, 4, 24, 'AA', '36', 'SAN'), live=False)\n"
        "pathlib.Path(r.log_path).unlink(missing_ok=True)\n"
        "assert 'anthropic' not in sys.modules, 'dry run imported the SDK'\n"
        "print('ok', r.outcome)\n"
    )
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert out.returncode == 0, out.stderr[-800:]
    assert out.stdout.startswith("ok")


def test_only_the_gateway_imports_the_sdk():
    src = Path(paths.REPO) / "src"
    hits = {
        p.relative_to(src).as_posix()
        for p in src.rglob("*.py")
        if any(line.lstrip().startswith(("import anthropic", "from anthropic")) for line in p.read_text().splitlines())
    }
    assert hits == {"autonomousprime/infra/llm.py"}
