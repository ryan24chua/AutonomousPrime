"""Opt-in live Pilot eval (real Claude calls, about $0.30). Run: pytest -m live (needs ANTHROPIC_API_KEY)."""

import asyncio
import os

import pytest

from tests.live import pilot_eval


@pytest.mark.live
@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
def test_pilot_live_eval_writes_output(tmp_path, monkeypatch):
    out = tmp_path / "pilot_live_eval.json"
    monkeypatch.setattr(pilot_eval, "OUT", out)
    asyncio.run(pilot_eval.main())
    assert out.exists()
    assert out.stat().st_size > 0
