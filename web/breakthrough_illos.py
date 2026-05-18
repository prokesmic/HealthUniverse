"""Editorial line-art illustrations for breakthrough cards.

One illustration per (category, stage) combination, rendered in the
brand palette: cream background, gold strokes for primary line work,
deep-green accents for emphasis, soft ink for shadows.

Design intent: feel like a New Yorker or Kinfolk spot illustration —
elegant, restrained, not chart-y. The card-level graphic is now a
"cover image"; the detail page keeps the actual study chart.

Each generator returns an SVG string sized to a 16:6 banner ratio
(suits a compact card height). All paths are hand-tuned by hand for
the brand — no clipart, no AI.
"""
from __future__ import annotations

# ─── Palette (mirrors style.css) ──────────────────────────────────
CREAM  = "#faf4dd"
INK    = "#1f1f1f"
INK_SOFT = "#5a5a5a"
GREEN  = "#1f3a2e"
GREEN_SOFT = "#3b8e5a"
GOLD   = "#c9a961"
GOLD_SOFT = "#e6d4a3"
ROSE   = "#9b1c1c"
ROSE_SOFT = "#f3b3ad"


def _open(w: int, h: int, bg: str = CREAM) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="100%" height="100%" preserveAspectRatio="xMidYMid meet" '
        f'role="img" aria-hidden="true">',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="{bg}"/>',
    ]


def _decor_dots(parts: list[str], w: int, h: int, color: str = GOLD) -> None:
    """Tiny scattered editorial dots — adds texture without noise."""
    for cx, cy, r in [
        (w * 0.08, h * 0.18, 1.5), (w * 0.92, h * 0.22, 1.5),
        (w * 0.05, h * 0.78, 1.2), (w * 0.96, h * 0.82, 1.2),
        (w * 0.12, h * 0.45, 1.0), (w * 0.88, h * 0.55, 1.0),
    ]:
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{color}" opacity="0.55"/>')


# ─── Oncology ─────────────────────────────────────────────────────

def oncology(w: int = 480, h: int = 180, stage: str = "phase3") -> str:
    """DNA double helix + targeting marker. Phase 1 = sparser, Phase 3 = full."""
    cx_l = w * 0.18
    cy = h * 0.5
    parts = _open(w, h)
    _decor_dots(parts, w, h)

    # DNA double helix (left side)
    helix_w = w * 0.28; helix_h = h * 0.72
    sx = cx_l - helix_w / 2; sy = cy - helix_h / 2
    rungs = 7 if stage in ("phase3", "approved", "guideline") else 5
    parts.append(f'<g stroke="{GREEN}" stroke-width="2" fill="none" stroke-linecap="round">')
    # Two sinusoidal strands
    n = 40
    pts_a = []
    pts_b = []
    import math
    for i in range(n + 1):
        t = i / n
        y = sy + t * helix_h
        ox = math.sin(t * math.pi * 3) * (helix_w * 0.42)
        pts_a.append((sx + helix_w / 2 + ox, y))
        pts_b.append((sx + helix_w / 2 - ox, y))
    da = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts_a)
    db = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts_b)
    parts.append(f'<path d="{da}"/>')
    parts.append(f'<path d="{db}" stroke="{GOLD}"/>')
    # Rungs
    for i in range(rungs):
        t = (i + 0.5) / rungs
        idx = int(t * n)
        ax, ay = pts_a[idx]; bx, by = pts_b[idx]
        parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{INK_SOFT}" stroke-width="1.2"/>')
    parts.append('</g>')

    # Cell with target on the right
    tcx, tcy, r = w * 0.68, h * 0.5, h * 0.32
    parts.append(f'<circle cx="{tcx:.1f}" cy="{tcy:.1f}" r="{r:.1f}" fill="none" stroke="{INK}" stroke-width="2"/>')
    # Nucleus
    parts.append(f'<circle cx="{tcx:.1f}" cy="{tcy:.1f}" r="{r * 0.36:.1f}" fill="{GREEN}" opacity="0.18"/>')
    parts.append(f'<circle cx="{tcx:.1f}" cy="{tcy:.1f}" r="{r * 0.36:.1f}" fill="none" stroke="{GREEN}" stroke-width="1.5"/>')
    # Targeting crosshair
    cx2 = tcx + r * 1.05
    cy2 = tcy
    parts.append(f'<circle cx="{cx2:.1f}" cy="{cy2:.1f}" r="{r * 0.5:.1f}" fill="none" stroke="{GOLD}" stroke-width="2" stroke-dasharray="4 4"/>')
    parts.append(f'<line x1="{cx2 - r * 0.7:.1f}" y1="{cy2:.1f}" x2="{cx2 + r * 0.7:.1f}" y2="{cy2:.1f}" stroke="{GOLD}" stroke-width="1.2"/>')
    parts.append(f'<line x1="{cx2:.1f}" y1="{cy2 - r * 0.7:.1f}" x2="{cx2:.1f}" y2="{cy2 + r * 0.7:.1f}" stroke="{GOLD}" stroke-width="1.2"/>')
    # Arrow from crosshair to cell
    parts.append(f'<path d="M {cx2 - r * 0.5:.1f} {cy2:.1f} L {tcx + r * 0.6:.1f} {cy2:.1f}" stroke="{ROSE}" stroke-width="1.8" marker-end="url(#arr_onc)"/>')
    parts.append(f'<defs><marker id="arr_onc" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="{ROSE}"/></marker></defs>')

    parts.append('</svg>')
    return "".join(parts)


# ─── Cardiovascular ───────────────────────────────────────────────

def cardio(w: int = 480, h: int = 180, stage: str = "phase3") -> str:
    parts = _open(w, h)
    _decor_dots(parts, w, h)
    cx, cy = w * 0.32, h * 0.5
    # Heart silhouette (anatomical-ish, single closed path)
    sz = h * 0.42
    d = (
        f"M {cx:.1f} {cy + sz * 0.55:.1f} "
        f"C {cx - sz * 1.05:.1f} {cy + sz * 0.05:.1f}, "
        f"{cx - sz * 0.95:.1f} {cy - sz * 0.85:.1f}, "
        f"{cx - sz * 0.10:.1f} {cy - sz * 0.55:.1f} "
        f"C {cx:.1f} {cy - sz * 0.30:.1f}, "
        f"{cx:.1f} {cy - sz * 0.30:.1f}, "
        f"{cx + sz * 0.10:.1f} {cy - sz * 0.55:.1f} "
        f"C {cx + sz * 0.95:.1f} {cy - sz * 0.85:.1f}, "
        f"{cx + sz * 1.05:.1f} {cy + sz * 0.05:.1f}, "
        f"{cx:.1f} {cy + sz * 0.55:.1f} Z"
    )
    parts.append(f'<path d="{d}" fill="{ROSE_SOFT}" opacity="0.45" stroke="{ROSE}" stroke-width="2" stroke-linejoin="round"/>')
    # Inner vessels (3 curves)
    for off in (-sz * 0.35, 0, sz * 0.35):
        parts.append(
            f'<path d="M {cx + off - sz * 0.12:.1f} {cy - sz * 0.18:.1f} '
            f'Q {cx + off:.1f} {cy + sz * 0.05:.1f} {cx + off + sz * 0.12:.1f} {cy + sz * 0.30:.1f}" '
            f'fill="none" stroke="{GREEN}" stroke-width="1.4" stroke-linecap="round"/>'
        )
    # ECG trace running across right half
    base_y = cy
    ecg_x0 = cx + sz * 1.4
    pts = []
    x = ecg_x0
    # Pattern: flat → small bump (P) → flat → spike (QRS) → flat → bump (T) — repeated 2x
    pattern = [(18, 0), (8, -4), (8, 4), (8, 0), (3, -10), (3, 26), (3, -16), (3, 0), (18, 0), (8, -6), (8, 6), (8, 0)]
    for dx, dy in pattern + pattern:
        pts.append((x, base_y)); x += dx
        pts.append((x, base_y + dy))
    d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)
    parts.append(f'<path d="{d}" fill="none" stroke="{GREEN}" stroke-width="2" stroke-linejoin="round"/>')
    # Baseline guideline behind ECG
    parts.append(f'<line x1="{ecg_x0:.1f}" y1="{base_y:.1f}" x2="{w - 12:.1f}" y2="{base_y:.1f}" stroke="{GOLD}" stroke-width="0.8" stroke-dasharray="2 4"/>')
    parts.append('</svg>')
    return "".join(parts)


# ─── Metabolic ────────────────────────────────────────────────────

def metabolic(w: int = 480, h: int = 180, stage: str = "phase3") -> str:
    parts = _open(w, h)
    _decor_dots(parts, w, h)
    # Liver silhouette on the left
    lcx, lcy = w * 0.30, h * 0.55
    sz = h * 0.38
    d_liver = (
        f"M {lcx - sz * 1.3:.1f} {lcy - sz * 0.1:.1f} "
        f"C {lcx - sz * 1.4:.1f} {lcy - sz * 0.9:.1f}, "
        f"{lcx - sz * 0.2:.1f} {lcy - sz * 1.1:.1f}, "
        f"{lcx + sz * 0.6:.1f} {lcy - sz * 0.9:.1f} "
        f"C {lcx + sz * 1.3:.1f} {lcy - sz * 0.7:.1f}, "
        f"{lcx + sz * 1.4:.1f} {lcy + sz * 0.5:.1f}, "
        f"{lcx + sz * 0.5:.1f} {lcy + sz * 0.75:.1f} "
        f"C {lcx - sz * 0.5:.1f} {lcy + sz * 0.95:.1f}, "
        f"{lcx - sz * 1.4:.1f} {lcy + sz * 0.45:.1f}, "
        f"{lcx - sz * 1.3:.1f} {lcy - sz * 0.1:.1f} Z"
    )
    parts.append(f'<path d="{d_liver}" fill="{GOLD_SOFT}" opacity="0.55" stroke="{GREEN}" stroke-width="2" stroke-linejoin="round"/>')
    # Lobe division line
    parts.append(f'<path d="M {lcx - sz * 0.05:.1f} {lcy - sz * 0.95:.1f} Q {lcx - sz * 0.4:.1f} {lcy + sz * 0.2:.1f} {lcx + sz * 0.2:.1f} {lcy + sz * 0.8:.1f}" fill="none" stroke="{GREEN}" stroke-width="1.4"/>')
    # Glucose molecule on the right (hexagon ring + carbons)
    rcx, rcy = w * 0.72, h * 0.42
    R = h * 0.20
    import math
    hex_pts = [(rcx + R * math.cos(math.pi/3 * i - math.pi/6), rcy + R * math.sin(math.pi/3 * i - math.pi/6)) for i in range(6)]
    parts.append('<g stroke="' + INK + '" stroke-width="1.6" fill="none">')
    for i in range(6):
        x1, y1 = hex_pts[i]; x2, y2 = hex_pts[(i + 1) % 6]
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    parts.append('</g>')
    # OH groups at three vertices (small line + label dot)
    for i, (x, y) in enumerate(hex_pts):
        if i % 2 == 0:
            ang = math.atan2(y - rcy, x - rcx)
            ox = x + math.cos(ang) * 10
            oy = y + math.sin(ang) * 10
            parts.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" stroke="{GOLD}" stroke-width="1.4"/>')
            parts.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="2.4" fill="{GOLD}"/>')
    # Down-arrow between liver and molecule — sema-style "lower"
    ax = w * 0.50; ay0 = h * 0.35; ay1 = h * 0.72
    parts.append(f'<line x1="{ax:.1f}" y1="{ay0:.1f}" x2="{ax:.1f}" y2="{ay1:.1f}" stroke="{GREEN}" stroke-width="2.2"/>')
    parts.append(f'<path d="M {ax - 7:.1f} {ay1 - 7:.1f} L {ax:.1f} {ay1:.1f} L {ax + 7:.1f} {ay1 - 7:.1f}" fill="none" stroke="{GREEN}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
    parts.append('</svg>')
    return "".join(parts)


# ─── Neuro & mental health ────────────────────────────────────────

def neuro(w: int = 480, h: int = 180, stage: str = "phase3") -> str:
    parts = _open(w, h)
    _decor_dots(parts, w, h)
    # Brain silhouette (side profile, simplified)
    cx, cy = w * 0.32, h * 0.5
    sz = h * 0.38
    d_brain = (
        f"M {cx - sz * 1.2:.1f} {cy + sz * 0.2:.1f} "
        f"C {cx - sz * 1.4:.1f} {cy - sz * 0.5:.1f}, "
        f"{cx - sz * 0.8:.1f} {cy - sz * 1.15:.1f}, "
        f"{cx + sz * 0.1:.1f} {cy - sz * 1.05:.1f} "
        f"C {cx + sz * 1.0:.1f} {cy - sz * 0.95:.1f}, "
        f"{cx + sz * 1.3:.1f} {cy - sz * 0.2:.1f}, "
        f"{cx + sz * 1.05:.1f} {cy + sz * 0.45:.1f} "
        f"C {cx + sz * 0.95:.1f} {cy + sz * 0.85:.1f}, "
        f"{cx + sz * 0.3:.1f} {cy + sz * 1.0:.1f}, "
        f"{cx - sz * 0.4:.1f} {cy + sz * 0.85:.1f} "
        f"C {cx - sz * 1.1:.1f} {cy + sz * 0.7:.1f}, "
        f"{cx - sz * 1.2:.1f} {cy + sz * 0.5:.1f}, "
        f"{cx - sz * 1.2:.1f} {cy + sz * 0.2:.1f} Z"
    )
    parts.append(f'<path d="{d_brain}" fill="{GOLD_SOFT}" opacity="0.40" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>')
    # Gyri (3 curvy lines)
    for off_y in (-sz * 0.45, -sz * 0.15, sz * 0.20):
        parts.append(
            f'<path d="M {cx - sz * 0.9:.1f} {cy + off_y:.1f} '
            f'Q {cx - sz * 0.3:.1f} {cy + off_y - sz * 0.15:.1f} '
            f'{cx + sz * 0.2:.1f} {cy + off_y:.1f} '
            f'T {cx + sz * 0.9:.1f} {cy + off_y - sz * 0.05:.1f}" '
            f'fill="none" stroke="{INK_SOFT}" stroke-width="1.4"/>'
        )
    # Neuron network on the right — 5 cells with dendrites
    base_x = w * 0.66; base_y = h * 0.5
    import math, random
    rng = random.Random(stage)
    nodes = [(base_x + (i % 3) * 60, base_y - 35 + (i // 3) * 55) for i in range(5)]
    parts.append(f'<g stroke="{GREEN}" stroke-width="1.3" fill="{GREEN}">')
    for x, y in nodes:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" />')
        # Random dendrites
        for _ in range(3):
            ang = rng.uniform(0, math.tau)
            ex = x + math.cos(ang) * 22
            ey = y + math.sin(ang) * 22
            parts.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" fill="none"/>')
    parts.append('</g>')
    # Connecting axons
    parts.append(f'<g stroke="{GOLD}" stroke-width="1.5" fill="none" stroke-linecap="round">')
    pairs = [(0, 1), (1, 2), (1, 4), (3, 4), (0, 3)]
    for a, b in pairs:
        x1, y1 = nodes[a]; x2, y2 = nodes[b]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 12
        parts.append(f'<path d="M {x1:.1f} {y1:.1f} Q {mx:.1f} {my:.1f} {x2:.1f} {y2:.1f}"/>')
    parts.append('</g>')
    parts.append('</svg>')
    return "".join(parts)


# ─── Longevity ────────────────────────────────────────────────────

def longevity(w: int = 480, h: int = 180, stage: str = "phase3") -> str:
    parts = _open(w, h)
    _decor_dots(parts, w, h)
    # Hourglass on left
    hx = w * 0.28; hy = h * 0.5; hw = h * 0.45; hh = h * 0.55
    # Outer frame
    parts.append(f'<path d="M {hx - hw / 2:.1f} {hy - hh:.1f} L {hx + hw / 2:.1f} {hy - hh:.1f}" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>')
    parts.append(f'<path d="M {hx - hw / 2:.1f} {hy + hh:.1f} L {hx + hw / 2:.1f} {hy + hh:.1f}" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>')
    # Bulbs (two triangles meeting at center)
    parts.append(f'<path d="M {hx - hw / 2:.1f} {hy - hh:.1f} L {hx:.1f} {hy:.1f} L {hx + hw / 2:.1f} {hy - hh:.1f}" fill="{GOLD_SOFT}" stroke="{GOLD}" stroke-width="2" stroke-linejoin="round"/>')
    parts.append(f'<path d="M {hx - hw / 2:.1f} {hy + hh:.1f} L {hx:.1f} {hy:.1f} L {hx + hw / 2:.1f} {hy + hh:.1f} Z" fill="{GREEN}" opacity="0.18" stroke="{GREEN}" stroke-width="2" stroke-linejoin="round"/>')
    # Falling sand grains
    for gy in (hy - hh * 0.10, hy + hh * 0.05, hy + hh * 0.25):
        parts.append(f'<circle cx="{hx:.1f}" cy="{gy:.1f}" r="1.5" fill="{GOLD}"/>')
    # Sun arc on the right (rising over a path)
    sx, sy = w * 0.70, h * 0.78
    R = h * 0.42
    import math
    # Half-circle
    arc_pts = []
    for i in range(20):
        a = math.pi + (math.pi * i / 19)
        arc_pts.append((sx + R * math.cos(a), sy + R * math.sin(a)))
    d_arc = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in arc_pts)
    parts.append(f'<path d="{d_arc}" fill="none" stroke="{GOLD}" stroke-width="2"/>')
    # Sun
    parts.append(f'<circle cx="{sx:.1f}" cy="{sy - R * 0.55:.1f}" r="9" fill="{GOLD}" stroke="{GREEN}" stroke-width="1.5"/>')
    # Rays
    for ang_d in range(0, 360, 45):
        ang = math.radians(ang_d)
        rx0 = sx + math.cos(ang) * 13; ry0 = sy - R * 0.55 + math.sin(ang) * 13
        rx1 = sx + math.cos(ang) * 20; ry1 = sy - R * 0.55 + math.sin(ang) * 20
        parts.append(f'<line x1="{rx0:.1f}" y1="{ry0:.1f}" x2="{rx1:.1f}" y2="{ry1:.1f}" stroke="{GOLD}" stroke-width="1.6" stroke-linecap="round"/>')
    # Horizon
    parts.append(f'<line x1="{sx - R - 6:.1f}" y1="{sy:.1f}" x2="{sx + R + 6:.1f}" y2="{sy:.1f}" stroke="{INK}" stroke-width="1.4"/>')
    parts.append('</svg>')
    return "".join(parts)


# ─── Other / recall ───────────────────────────────────────────────

def other(w: int = 480, h: int = 180, stage: str = "phase3") -> str:
    """Generic "study" — open journal + magnifying glass."""
    parts = _open(w, h)
    _decor_dots(parts, w, h)
    # Book/journal — two facing pages
    bx, by = w * 0.30, h * 0.5
    bw, bh = h * 0.95, h * 0.55
    # Left page
    parts.append(f'<path d="M {bx - bw / 2:.1f} {by + bh / 2:.1f} L {bx - bw / 2:.1f} {by - bh / 2:.1f} L {bx:.1f} {by - bh / 2 + 8:.1f} L {bx:.1f} {by + bh / 2:.1f} Z" fill="#fff" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>')
    parts.append(f'<path d="M {bx + bw / 2:.1f} {by + bh / 2:.1f} L {bx + bw / 2:.1f} {by - bh / 2:.1f} L {bx:.1f} {by - bh / 2 + 8:.1f} L {bx:.1f} {by + bh / 2:.1f} Z" fill="#fff" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>')
    # Lines of text
    for off in range(5):
        ly = by - bh * 0.3 + off * 12
        wl = bw * 0.35 - (off % 2) * 8
        parts.append(f'<line x1="{bx - bw / 2 + 12:.1f}" y1="{ly:.1f}" x2="{bx - bw / 2 + 12 + wl:.1f}" y2="{ly:.1f}" stroke="{INK_SOFT}" stroke-width="1.5" stroke-linecap="round"/>')
        parts.append(f'<line x1="{bx + 12:.1f}" y1="{ly:.1f}" x2="{bx + 12 + wl:.1f}" y2="{ly:.1f}" stroke="{INK_SOFT}" stroke-width="1.5" stroke-linecap="round"/>')
    # Magnifying glass over the right page
    mcx, mcy = w * 0.74, h * 0.42
    parts.append(f'<circle cx="{mcx:.1f}" cy="{mcy:.1f}" r="{h * 0.20:.1f}" fill="{CREAM}" stroke="{GREEN}" stroke-width="2.5"/>')
    parts.append(f'<circle cx="{mcx:.1f}" cy="{mcy:.1f}" r="{h * 0.20:.1f}" fill="{GOLD}" opacity="0.10"/>')
    parts.append(f'<line x1="{mcx + h * 0.14:.1f}" y1="{mcy + h * 0.14:.1f}" x2="{mcx + h * 0.32:.1f}" y2="{mcy + h * 0.32:.1f}" stroke="{GREEN}" stroke-width="3.5" stroke-linecap="round"/>')
    parts.append('</svg>')
    return "".join(parts)


# ─── Dispatch ─────────────────────────────────────────────────────

_RENDERERS = {
    "oncology":  oncology,
    "cardio":    cardio,
    "metabolic": metabolic,
    "neuro":     neuro,
    "longevity": longevity,
    "other":     other,
}


def illo_svg(item: dict, w: int = 480, h: int = 180) -> str:
    cat = item.get("category", "other")
    stage = item.get("stage", "phase3")
    fn = _RENDERERS.get(cat, other)
    try:
        return fn(w=w, h=h, stage=stage)
    except Exception:
        return other(w=w, h=h, stage=stage)
