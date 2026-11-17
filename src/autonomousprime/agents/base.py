"""Shared agent template: gateway, role name, prompt loaded at call time, and the one correction loop.

A role agent builds its messages and facts, then calls `run_turn`: call the gateway, validate the reply with the
role's `check`, and on failure append a correction and ask again, up to `LIMITS.max_attempts` calls in all. When the
attempts run out (or the role says to stop early) it returns a `TurnResult` with `ok=False`; the role maps that to
its own give-up message (today every role turns it into a `reject`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from pydantic import BaseModel

from autonomousprime.core.contracts import LIMITS
from autonomousprime.infra.llm import LLMGateway, LLMResult, as_gateway


@dataclass
class Checked:
    """A role's verdict on a parsed reply. No `errors` = accepted: `value` is the turn's result. Otherwise
    `followup` are the messages appended before asking again (typically the reply and a correction)."""

    value: Any = None
    errors: list[str] = field(default_factory=list)
    followup: list[dict] = field(default_factory=list)


@dataclass
class TurnResult:
    ok: bool
    value: Any = None
    attempts: int = 0
    last: LLMResult | None = None  # the final gateway result: kind, stop_reason, usage, latency
    errors: list[str] = field(default_factory=list)  # the last attempt's validation errors


UNUSABLE_KINDS = ("refusal", "max_tokens", "no_output", "invalid")


class RoleAgent:
    """Base for ATC, Pilot and Ground. `prompt` is a file path (read on every call, so editing the prompt needs no
    restart) or a zero-argument callable returning the text."""

    def __init__(self, role: str, prompt: Path | Callable[[], str], client: Any = None):
        self.role = role
        self._prompt = prompt
        self.gateway: LLMGateway = as_gateway(client)

    def load_prompt(self) -> str:
        return self._prompt.read_text(encoding="utf-8") if isinstance(self._prompt, Path) else self._prompt()

    def on_failure(self, res: LLMResult) -> list[dict] | None:
        """What to do when the gateway gave no usable reply: messages to append before re-asking, `[]` to re-ask
        unchanged, or None to give up now. Default: ask again after a refusal, truncation, empty or invalid reply;
        stop on an API error. Roles override this to keep their own behaviour."""
        if res.kind in UNUSABLE_KINDS:
            return [
                {
                    "role": "user",
                    "content": f"Your last reply could not be used (stop_reason={res.stop_reason}). "
                    "Reply again with one valid message.",
                }
            ]
        return None

    async def run_turn(
        self,
        messages: list[dict],
        output_format: type[BaseModel],
        check: Callable[[BaseModel], Checked],
        *,
        system_extra: Sequence[str] = (),
        on_failure: Callable[[LLMResult], list[dict] | None] | None = None,
        on_attempt: Callable[[int, LLMResult, list[str]], None] | None = None,
    ) -> TurnResult:
        """The correction loop. `messages` is extended in place. `on_attempt(attempt, result, errors)` is called
        after every gateway call (errors empty when the reply was accepted)."""
        handler = on_failure or self.on_failure
        system = [self.load_prompt(), *system_extra]
        errors: list[str] = []
        res: LLMResult | None = None
        for attempt in range(1, LIMITS.max_attempts + 1):
            res = await self.gateway.parse(self.role, system, messages, output_format)
            if res.ok:
                checked = check(res.parsed)
                errors, follow = checked.errors, checked.followup
            else:
                errors, follow = [res.kind], handler(res)
            if on_attempt:
                on_attempt(attempt, res, errors)
            if res.ok and not errors:
                return TurnResult(True, checked.value, attempt, res)
            if follow is None:  # the role gives up now
                return TurnResult(False, None, attempt, res, errors)
            messages += follow
        return TurnResult(False, None, LIMITS.max_attempts, res, errors)
