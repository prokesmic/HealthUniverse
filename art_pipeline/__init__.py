"""Health Universe portable art pipeline.

Cross-machine workflow:
  1. prepare  — build prompt jobs in this repo (heuristic OR merge external Gemma JSON)
  2. export   — bundle prompts as portable JSON files
  3. (offline) — render on a separate machine with Gemma + Draw Things
  4. import   — scan returned renders, write to web/static/art/, update manifest
  5. review   — optional QA pass marking entries approved / needs_review / regenerate

The site is offline-only at request time. Cached images are preferred when
present; the procedural SVG layer in web/illustrations.py is the always-safe
fallback. No image generation happens in request handlers.
"""

from .manifest import load_manifest, save_manifest, manifest_key
from .prompts import build_heuristic_prompt, merge_external_prompts
from .jobs    import write_prompt_job, scan_pending_jobs, scan_done_renders
from .review  import load_reviews, apply_reviews

__all__ = [
    "load_manifest", "save_manifest", "manifest_key",
    "build_heuristic_prompt", "merge_external_prompts",
    "write_prompt_job", "scan_pending_jobs", "scan_done_renders",
    "load_reviews", "apply_reviews",
]
