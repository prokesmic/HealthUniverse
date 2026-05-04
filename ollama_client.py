"""Local LLM wrapper around Ollama. Free, runs at 127.0.0.1:11434.

Used for everything that's not seed/adjudication:
- abstract relevance triage
- claim extraction from abstracts
- card-copy summarization
- dedup checks (semantic similarity via embeddings later)
"""
from __future__ import annotations

import json
import os
import re
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:26b")


class OllamaUnavailable(RuntimeError):
    pass


def _client() -> httpx.Client:
    return httpx.Client(base_url=OLLAMA_URL, timeout=120.0)


def health() -> bool:
    try:
        with _client() as c:
            return c.get("/api/tags").status_code == 200
    except Exception:
        return False


def call(*, system: str, user: str, model: str | None = None,
         temperature: float = 0.2, num_predict: int = 1500,
         json_mode: bool = False, retries: int = 2) -> str:
    """Single non-streaming generation. Returns text."""
    if not health():
        raise OllamaUnavailable(
            f"Ollama not reachable at {OLLAMA_URL}. "
            "Start it with `ollama serve` or run `brew services start ollama`."
        )
    body = {
        "model": model or OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        body["format"] = "json"

    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with _client() as c:
                r = c.post("/api/chat", json=body)
                r.raise_for_status()
                return r.json()["message"]["content"]
        except (httpx.HTTPError, KeyError) as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise OllamaUnavailable(f"Ollama call failed after retries: {last}")


def call_json(*, system: str, user: str, **kwargs) -> dict | list:
    """Like call() but parses a JSON response. Adds the JSON-mode hint."""
    text = call(system=system, user=user, json_mode=True, **kwargs)
    # gemma sometimes wraps in fences anyway
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    return json.loads(text)


if __name__ == "__main__":
    print("Ollama health:", health())
    if health():
        out = call(system="You return single short answers.",
                   user="Say PONG and nothing else.")
        print("model says:", out.strip())
