"""Anthropic client wrapper with cost cap + JSON extraction.

Pricing (as of 2025-11): claude-sonnet-4-6 = $3/M input, $15/M output.
We read it from PRICE_PER_MTOK so it's easy to update.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

from db import connect, record_cost, total_spent_usd

load_dotenv(Path(__file__).parent / ".env", override=True)

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
COST_CAP_USD = float(os.getenv("COST_CAP_USD", "50.00"))

# USD per million tokens. Update if pricing changes.
PRICE_PER_MTOK = {
    "claude-sonnet-4-6":   {"input": 3.00,  "output": 15.00},
    "claude-opus-4-7":     {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5":    {"input": 1.00,  "output": 5.00},
}


class CostCapExceeded(RuntimeError):
    pass


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int
    usd: float


def _price(model: str) -> dict:
    base = re.sub(r"-\d{8}$", "", model)
    if base in PRICE_PER_MTOK:
        return PRICE_PER_MTOK[base]
    raise KeyError(f"No pricing entry for model {model}; add it to PRICE_PER_MTOK")


def cost_of(model: str, input_tokens: int, output_tokens: int) -> float:
    p = _price(model)
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000


def assert_under_cap() -> float:
    with connect() as conn:
        spent = total_spent_usd(conn)
    if spent >= COST_CAP_USD:
        raise CostCapExceeded(f"Spent ${spent:.4f} of ${COST_CAP_USD:.2f} cap")
    return spent


def call(*, system: str, user: str, operation: str, ref: str = "",
         max_tokens: int = 4096, temperature: float = 0.2) -> tuple[str, Usage]:
    """Single non-streaming call. Records cost. Raises if cap exceeded."""
    spent = assert_under_cap()
    client = Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    usage = Usage(
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
        usd=cost_of(MODEL, resp.usage.input_tokens, resp.usage.output_tokens),
    )
    with connect() as conn:
        record_cost(conn, provider="anthropic", model=MODEL, operation=operation,
                    input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                    usd=usage.usd, ref=ref)
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    if spent + usage.usd >= COST_CAP_USD:
        # Allow this call to complete since it's already paid for, but block subsequent.
        print(f"[cost] WARNING: cap reached after this call (${spent + usage.usd:.4f})")
    return text, usage


def extract_json(text: str) -> dict:
    """Pull the first JSON object out of a Claude response."""
    # Prefer fenced ```json blocks
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    # Else first balanced { ... }
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object in response")
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("Unbalanced JSON in response")
