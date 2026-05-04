"""1200x630 OpenGraph share-card PNG renderer for an edge.

Uses Pillow with bundled fonts only (no network) so it works on Vercel's
read-only runtime. Cards are not cached on disk on Vercel — each request
re-renders. They're cheap (<60ms)."""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG     = (247, 241, 227)     # cream
INK    = (42, 37, 32)
SOFT   = (90, 84, 76)
GOLD   = (201, 169, 97)
PRIM   = (31, 58, 46)

TIER_BG = {
    "A": (230, 239, 225), "B": (247, 238, 207),
    "C": (247, 217, 199), "D": (244, 206, 206), "X": (235, 226, 242),
}
TIER_FG = {"A": (59, 142, 90), "B": (138, 108, 24), "C": (166, 74, 40),
           "D": (138, 41, 41), "X": (74, 62, 90)}
TIER_LABEL = {"A": "STRONG EVIDENCE", "B": "MODERATE EVIDENCE",
              "C": "EMERGING EVIDENCE", "D": "LIMITED EVIDENCE",
              "X": "CONTESTED"}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    # Use system fonts available on macOS / Vercel Linux runtime
    candidates = [
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold
            else "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


def render_edge_png(edge: dict) -> bytes:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Card frame
    d.rounded_rectangle((48, 48, W-48, H-48), radius=24,
                        fill=(255, 253, 246), outline=(231, 222, 203), width=2)

    # Tier pill
    tier = edge.get("tier", "C")
    pill_text = TIER_LABEL.get(tier, "")
    pill_font = _font(20, bold=True)
    pad = 16
    pw = int(d.textlength(pill_text, font=pill_font)) + pad * 2
    d.rounded_rectangle((84, 92, 84 + pw, 132), radius=10, fill=TIER_BG.get(tier, (240,240,240)))
    d.text((84 + pad, 100), pill_text, font=pill_font, fill=TIER_FG.get(tier, INK))

    # Title (factor and outcome)
    title = f"{edge.get('f_name','')} and {edge.get('o_name','')}"
    title_font = _font(72, bold=True)
    lines = _wrap(d, title, title_font, max_w=W - 200)[:2]
    y = 168
    for ln in lines:
        d.text((84, y), ln, font=title_font, fill=INK)
        y += 84

    # Summary
    summary = (edge.get("summary") or "").strip()
    body_font = _font(28)
    body_lines = _wrap(d, summary, body_font, max_w=W - 200)[:5]
    y = max(y + 12, 360)
    for ln in body_lines:
        d.text((84, y), ln, font=body_font, fill=SOFT)
        y += 38

    # Footer
    foot_font = _font(22, bold=True)
    d.text((84, H - 110), "HEALTH UNIVERSE", font=foot_font, fill=GOLD)
    d.text((84, H - 80), "health-universe.vercel.app", font=_font(20), fill=SOFT)

    # Direction badge bottom-right
    direction = (edge.get("direction") or "").replace("_", "-")
    if direction:
        df = _font(22, bold=True)
        dw = int(d.textlength(direction.upper(), font=df)) + 28
        d.rounded_rectangle((W-84-dw, H-110, W-84, H-70), radius=10,
                            fill=PRIM)
        d.text((W-84-dw+14, H-103), direction.upper(), font=df, fill=BG)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
