"""Ollama embeddings — free, local, no spend.

Default model: nomic-embed-text (768 dims, fast on CPU). If not pulled:

    ollama pull nomic-embed-text

Used by `dedupe.py` and the daily ingest's near-duplicate fold step.
"""
from __future__ import annotations

import os
import struct
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

OLLAMA_URL  = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


class EmbeddingsUnavailable(RuntimeError):
    pass


def embed(text: str) -> list[float]:
    """Embed one string. Returns float vector. Uses /api/embed (current
    Ollama endpoint) — the legacy /api/embeddings returned identical
    vectors for short inputs."""
    if not text or not text.strip():
        return []
    try:
        with httpx.Client(timeout=60.0) as c:
            r = c.post(f"{OLLAMA_URL}/api/embed",
                       json={"model": EMBED_MODEL, "input": text})
            r.raise_for_status()
        data = r.json()
        embs = data.get("embeddings") or []
        return embs[0] if embs else []
    except Exception as e:
        raise EmbeddingsUnavailable(
            f"Ollama embeddings failed at {OLLAMA_URL}: {e}. "
            f"Try: ollama pull {EMBED_MODEL}"
        ) from e


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Sequential batch (Ollama doesn't support true batching for /embeddings)."""
    return [embed(t) for t in texts]


# ---------- packing helpers (we store as compact bytes in SQLite) ----------

def pack(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def unpack(blob: bytes) -> list[float]:
    if not blob:
        return []
    return list(struct.unpack(f"{len(blob)//4}f", blob))


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na  += x * x
        nb  += y * y
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na ** 0.5 * nb ** 0.5)


if __name__ == "__main__":
    v = embed("magnesium and sleep quality")
    print(f"dims: {len(v)}, first 5: {v[:5]}")
