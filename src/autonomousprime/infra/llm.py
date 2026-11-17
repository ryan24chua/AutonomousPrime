"""The one LLM gateway: the only module that imports the Anthropic SDK (design-register G4: our own loop, no framework).

Every role calls `LLMGateway.parse`. It sends one structured-output request (`messages.parse`) with the system prompt
cached, retries once on a transient API error, answers repeated identical requests from a disk cache, and appends one
line per API attempt to a JSONL call log (usage, latency, cache hit, stop reason; never message text or the key).

A failure is a typed `LLMResult.kind`, not an exception, so each agent's correction loop (agents/base.py) decides what
to do. Refusal, truncation, a missing or schema-invalid reply and API failures are all kinds; only programming errors
raise. The SDK is imported lazily, so a dry run (which never builds a client) imports no SDK.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Sequence

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from autonomousprime import paths

MODEL = "claude-sonnet-5-5"  # docs/hackathon/mvp-spec.md section 14: agents on Sonnet tier


@dataclass(frozen=True)
class RoleSettings:
    model: str
    max_tokens: int
    effort: str | None = None  # output_config effort; None = not sent


# One table for every role's model, token cap and effort. Ask before changing the model tier.
ROLE_SETTINGS: dict[str, RoleSettings] = {
    "atc": RoleSettings(MODEL, 700),
    "pilot": RoleSettings(MODEL, 4000, "medium"),
    "ground": RoleSettings(MODEL, 4000, "medium"),
}

Kind = Literal["ok", "refusal", "max_tokens", "no_output", "invalid", "transient_error", "api_error"]


class LiveUnavailable(RuntimeError):
    """Live mode was asked for but no API key is configured."""


@dataclass
class LLMResult:
    """Outcome of one gateway call. `parsed` is set only when kind == "ok"."""

    kind: Kind
    parsed: BaseModel | None = None
    stop_reason: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    latency_s: float = 0.0
    cache_hit: bool = False
    error: str | None = None  # short text for a failure (schema message, exception class)
    request_id: str | None = None
    attempts: int = 1  # API attempts made (0 on a cache hit)

    @property
    def ok(self) -> bool:
        return self.kind == "ok"


def make_client():
    """The one place a client is built: load `.env.local`, then an async Anthropic client.

    Raises LiveUnavailable when no key is configured."""
    load_dotenv(paths.REPO / ".env.local")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise LiveUnavailable("Live mode needs ANTHROPIC_API_KEY in .env.local")
    import anthropic

    return anthropic.AsyncAnthropic()


def _classify(exc: Exception) -> Literal["transient_error", "api_error"] | None:
    """Transient (connection, rate limit, 5xx), other API error, or None for anything that is not an SDK error."""
    import anthropic

    if isinstance(exc, (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.InternalServerError)):
        return "transient_error"
    if isinstance(exc, anthropic.APIStatusError):
        return "transient_error" if exc.status_code >= 500 else "api_error"
    return None


def _usage(resp: Any) -> dict[str, int]:
    u = getattr(resp, "usage", None)
    names = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
    return {n: int(getattr(u, n, 0) or 0) for n in names}


class LLMGateway:
    """Async gateway. `client` is anything with an async `messages.parse` (the SDK client, or a fake in tests); None
    builds the real one on first use. `cache`: answer identical requests from `cache_dir`. `log_path`: JSONL call log
    (None = no file). Every attempt is also kept in `self.calls`."""

    def __init__(
        self,
        client: Any = None,
        *,
        cache: bool = True,
        cache_dir: Path | None = None,
        log_path: Path | None | Literal["default"] = "default",
        retry_delay_s: float = 1.0,
    ):
        self._client = client
        self.cache = cache
        self.cache_dir = cache_dir if cache_dir is not None else paths.CACHE / "llm"
        self.log_path = paths.LOGS / "llm_calls.jsonl" if log_path == "default" else log_path
        self.retry_delay_s = retry_delay_s
        self.calls: list[dict] = []

    # -- public
    async def parse(
        self,
        role: str,
        system: str | Sequence[str],
        messages: list[dict],
        output_format: type[BaseModel],
    ) -> LLMResult:
        """One structured call for `role`. `system` is one text or several; the last block carries the cache
        breakpoint, so the whole prefix is cached."""
        cfg = ROLE_SETTINGS[role]
        texts = [system] if isinstance(system, str) else list(system)
        key = self._key(cfg, texts, messages, output_format)
        if self.cache and (hit := self._read(key, output_format)) is not None:
            res = LLMResult("ok", parsed=hit, stop_reason="cache", cache_hit=True, attempts=0)
            self._log(role, cfg.model, res)
            return res
        blocks: list[dict] = [{"type": "text", "text": t} for t in texts]
        blocks[-1]["cache_control"] = {"type": "ephemeral"}
        kwargs: dict[str, Any] = dict(
            model=cfg.model, max_tokens=cfg.max_tokens, system=blocks, messages=messages, output_format=output_format
        )
        if cfg.effort:
            kwargs["output_config"] = {"effort": cfg.effort}
        client = self._get_client()
        res = LLMResult("api_error")
        for attempt in (1, 2):  # one retry on a transient error
            t0 = time.perf_counter()
            res = await self._once(client, kwargs)
            res.latency_s, res.attempts = round(time.perf_counter() - t0, 3), attempt
            self._log(role, cfg.model, res)
            if res.kind != "transient_error" or attempt == 2:
                break
            await asyncio.sleep(self.retry_delay_s)
        if self.cache and res.ok:  # never cache a failure
            self._write(key, res.parsed)
        return res

    # -- internals
    def _get_client(self):
        if self._client is None:
            self._client = make_client()
        return self._client

    async def _once(self, client, kwargs: dict) -> LLMResult:
        try:
            resp = await client.messages.parse(**kwargs)
        except ValidationError as e:  # the reply did not match the output schema
            return LLMResult("invalid", error=e.errors()[0]["msg"] if e.errors() else "schema")
        except Exception as e:
            kind = _classify(e)
            if kind is None:
                raise
            return LLMResult(kind, error=type(e).__name__)
        stop = getattr(resp, "stop_reason", None)
        common = dict(stop_reason=stop, usage=_usage(resp), request_id=getattr(resp, "_request_id", None))
        parsed = getattr(resp, "parsed_output", None)
        if stop in ("refusal", "max_tokens"):
            return LLMResult(stop, **common)
        if parsed is None:
            return LLMResult("no_output", **common)
        return LLMResult("ok", parsed=parsed, **common)

    @staticmethod
    def _key(cfg: RoleSettings, texts: list[str], messages: list[dict], output_format: type[BaseModel]) -> str:
        payload = [cfg.model, cfg.max_tokens, cfg.effort, texts, messages, output_format.model_json_schema()]
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()

    def _read(self, key: str, output_format: type[BaseModel]) -> BaseModel | None:
        f = self.cache_dir / f"{key}.json"
        try:
            return output_format.model_validate_json(f.read_text(encoding="utf-8"))
        except (OSError, ValidationError):
            return None

    def _write(self, key: str, parsed: BaseModel | None) -> None:
        if parsed is None:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.cache_dir / f"{key}.json.tmp"
        tmp.write_text(parsed.model_dump_json(by_alias=True), encoding="utf-8")
        tmp.replace(self.cache_dir / f"{key}.json")

    def _log(self, role: str, model: str, res: LLMResult) -> None:
        u = res.usage
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "role": role,
            "model": model,
            "kind": res.kind,
            "stop_reason": res.stop_reason,
            "input_tokens": u.get("input_tokens", 0),
            "output_tokens": u.get("output_tokens", 0),
            "cache_creation_input_tokens": u.get("cache_creation_input_tokens", 0),
            "cache_read_input_tokens": u.get("cache_read_input_tokens", 0),
            "latency_s": res.latency_s,
            "cache_hit": res.cache_hit,
            "attempt": res.attempts,
            "error": res.error,
            "request_id": res.request_id,
        }
        self.calls.append(entry)
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")


def make_gateway(**kw) -> LLMGateway:
    """A live gateway on a real client (cache and call log on). Raises LiveUnavailable without a key."""
    return LLMGateway(make_client(), **kw)


def as_gateway(client: Any = None) -> LLMGateway:
    """What an agent was given -> a gateway. A gateway is used as is; None builds the live one; any other object is a
    raw client (the test seam): wrapped without cache or log file, so tests stay isolated."""
    if isinstance(client, LLMGateway):
        return client
    if client is None:
        return make_gateway()
    return LLMGateway(client, cache=False, log_path=None, retry_delay_s=0.0)
