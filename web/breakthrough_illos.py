"""Editorial spot illustrations for breakthrough cards.

Design intent: a *cover image* in the spirit of NYT Magazine / Kinfolk —
asymmetric composition, layered depth, refined line weights, subtle
gradients in the brand palette. Not chart-y; not clipart; not flat.

One illustration per category. The renderer reads `category` and `stage`
from the card so subtle elements (sample density, focal accent colour)
can shift with the story. All paths are hand-drawn; no external deps.

Palette:
  cream  #faf4dd   gold #c9a961  green #1f3a2e
  ink    #1f1f1f   rose #9b1c1c
"""
from __future__ import annotations

import math

# ─── Palette ──────────────────────────────────────────────────────
CREAM       = "#faf4dd"
CREAM_DEEP  = "#f3ead0"
INK         = "#1f1f1f"
INK_SOFT    = "#5a5a5a"
INK_FAINT   = "#a8a39a"
GREEN       = "#1f3a2e"
GREEN_SOFT  = "#3b8e5a"
GREEN_MIST  = "#cfded3"
GOLD        = "#c9a961"
GOLD_LIGHT  = "#e6d4a3"
GOLD_DEEP   = "#9e8045"
ROSE        = "#9b1c1c"
ROSE_SOFT   = "#f3b3ad"


# ─── Shared scaffolding ───────────────────────────────────────────

def _open(w: int, h: int) -> list[str]:
    """Open an SVG with cream-on-cream radial wash background + shared defs."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="100%" height="100%" preserveAspectRatio="xMidYMid slice" '
        f'role="img" aria-hidden="true">',
        '<defs>',
        # Background wash — warmer in the centre, cooler at edges
        f'<radialGradient id="bgwash" cx="55%" cy="40%" r="80%">'
        f'<stop offset="0%" stop-color="{CREAM}"/>'
        f'<stop offset="100%" stop-color="{CREAM_DEEP}"/>'
        f'</radialGradient>',
        # Gold gradient
        f'<linearGradient id="goldgrad" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%"  stop-color="{GOLD_LIGHT}"/>'
        f'<stop offset="100%" stop-color="{GOLD_DEEP}"/>'
        f'</linearGradient>',
        # Green organic fill
        f'<radialGradient id="greengrad" cx="35%" cy="35%" r="80%">'
        f'<stop offset="0%"  stop-color="{GREEN_MIST}"/>'
        f'<stop offset="100%" stop-color="{GREEN}" stop-opacity="0.55"/>'
        f'</radialGradient>',
        # Rose organic fill
        f'<radialGradient id="rosegrad" cx="35%" cy="35%" r="80%">'
        f'<stop offset="0%"  stop-color="{ROSE_SOFT}"/>'
        f'<stop offset="100%" stop-color="{ROSE}" stop-opacity="0.45"/>'
        f'</radialGradient>',
        # Soft drop shadow
        f'<filter id="soft" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feGaussianBlur in="SourceAlpha" stdDeviation="3"/>'
        f'<feOffset dx="0" dy="2"/>'
        f'<feComponentTransfer><feFuncA type="linear" slope="0.18"/></feComponentTransfer>'
        f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>'
        f'</filter>',
        '</defs>',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="url(#bgwash)"/>',
    ]


def _texture(parts: list[str], w: int, h: int) -> None:
    """Soft editorial stipple — adds paper-grain feeling without being noisy."""
    seeds = [
        (0.06, 0.18), (0.94, 0.22), (0.04, 0.78), (0.96, 0.82),
        (0.12, 0.45), (0.88, 0.55), (0.21, 0.10), (0.81, 0.90),
        (0.50, 0.06), (0.50, 0.94), (0.32, 0.86), (0.70, 0.16),
    ]
    for fx, fy in seeds:
        parts.append(
            f'<circle cx="{fx * w:.1f}" cy="{fy * h:.1f}" r="1.2" '
            f'fill="{GOLD_DEEP}" opacity="0.30"/>'
        )


def _baseline(parts: list[str], w: int, h: int) -> None:
    """A single hairline ground rule that visually anchors the composition."""
    parts.append(
        f'<line x1="{w * 0.04:.1f}" y1="{h * 0.92:.1f}" '
        f'x2="{w * 0.96:.1f}" y2="{h * 0.92:.1f}" '
        f'stroke="{GOLD_DEEP}" stroke-width="0.6" opacity="0.55"/>'
    )


# ═══════════════════════════════════════════════════════════════════
# ONCOLOGY — DNA helix targeting a cell, with floating molecular orbs
# ═══════════════════════════════════════════════════════════════════

def oncology(w: int = 720, h: int = 260, stage: str = "phase3") -> str:
    parts = _open(w, h)
    _texture(parts, w, h)

    # Soft organic blob behind helix — creates depth
    parts.append(
        f'<ellipse cx="{w * 0.25:.1f}" cy="{h * 0.55:.1f}" '
        f'rx="{w * 0.20:.1f}" ry="{h * 0.42:.1f}" '
        f'fill="url(#greengrad)" opacity="0.55"/>'
    )

    # ─── DNA double helix on the left, oriented vertically ────────
    hx = w * 0.25
    h_top = h * 0.10
    h_bot = h * 0.86
    amplitude = w * 0.08
    n = 80
    pts_a, pts_b = [], []
    for i in range(n + 1):
        t = i / n
        y = h_top + t * (h_bot - h_top)
        phase = t * math.pi * 2.6
        pts_a.append((hx + math.sin(phase) * amplitude, y))
        pts_b.append((hx + math.sin(phase + math.pi) * amplitude, y))

    # Rear strand (gold, soft) — drawn first so it sits behind
    da = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts_b)
    parts.append(
        f'<path d="{da}" fill="none" stroke="{GOLD}" stroke-width="3" '
        f'stroke-linecap="round" opacity="0.85"/>'
    )

    # Rungs — denser for phase3+
    rungs = 11 if stage in ("phase3", "approved", "guideline") else 8
    for i in range(rungs):
        t = (i + 0.5) / rungs
        idx = int(t * n)
        ax, ay = pts_a[idx]; bx, by = pts_b[idx]
        # Visible only when strands aren't crossing
        if abs(ax - bx) > amplitude * 0.4:
            colour = ROSE if i == rungs // 2 else INK_SOFT
            parts.append(
                f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
                f'stroke="{colour}" stroke-width="1.4" stroke-linecap="round" opacity="0.85"/>'
            )

    # Front strand (deep green, bold)
    db = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts_a)
    parts.append(
        f'<path d="{db}" fill="none" stroke="{GREEN}" stroke-width="3.6" '
        f'stroke-linecap="round"/>'
    )

    # Subtle highlight along front strand
    parts.append(
        f'<path d="{db}" fill="none" stroke="{GREEN_MIST}" stroke-width="1.2" '
        f'stroke-linecap="round" opacity="0.6"/>'
    )

    # ─── Cell + target on the right ───────────────────────────────
    tcx, tcy = w * 0.65, h * 0.50
    r = h * 0.34

    # Halo (very soft glow behind the cell)
    parts.append(
        f'<circle cx="{tcx:.1f}" cy="{tcy:.1f}" r="{r * 1.45:.1f}" '
        f'fill="url(#goldgrad)" opacity="0.18"/>'
    )

    # Cell body with green fill gradient
    parts.append(
        f'<circle cx="{tcx:.1f}" cy="{tcy:.1f}" r="{r:.1f}" '
        f'fill="url(#greengrad)" opacity="0.85" filter="url(#soft)"/>'
    )
    parts.append(
        f'<circle cx="{tcx:.1f}" cy="{tcy:.1f}" r="{r:.1f}" '
        f'fill="none" stroke="{INK}" stroke-width="1.8"/>'
    )

    # Mitochondria-like organelles (3, asymmetric)
    for ang_d, dist_f, size_f in [(35, 0.55, 0.18), (220, 0.50, 0.22), (160, 0.30, 0.14)]:
        ang = math.radians(ang_d)
        ox = tcx + math.cos(ang) * r * dist_f
        oy = tcy + math.sin(ang) * r * dist_f
        sz = r * size_f
        parts.append(
            f'<ellipse cx="{ox:.1f}" cy="{oy:.1f}" rx="{sz * 1.6:.1f}" ry="{sz * 0.7:.1f}" '
            f'fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="1" '
            f'transform="rotate({ang_d * 0.7:.0f} {ox:.1f} {oy:.1f})"/>'
        )

    # Nucleus (off-centre)
    ncx = tcx - r * 0.10
    ncy = tcy - r * 0.10
    parts.append(
        f'<circle cx="{ncx:.1f}" cy="{ncy:.1f}" r="{r * 0.32:.1f}" '
        f'fill="{GREEN}" opacity="0.55"/>'
    )
    parts.append(
        f'<circle cx="{ncx:.1f}" cy="{ncy:.1f}" r="{r * 0.32:.1f}" '
        f'fill="none" stroke="{GREEN}" stroke-width="1.5"/>'
    )
    # Nucleus chromatin hint
    parts.append(
        f'<circle cx="{ncx - r * 0.08:.1f}" cy="{ncy - r * 0.06:.1f}" r="{r * 0.05:.1f}" '
        f'fill="{INK}" opacity="0.4"/>'
    )
    parts.append(
        f'<circle cx="{ncx + r * 0.10:.1f}" cy="{ncy + r * 0.08:.1f}" r="{r * 0.04:.1f}" '
        f'fill="{INK}" opacity="0.35"/>'
    )

    # ─── Floating molecular orbs (top-right) ──────────────────────
    for cx, cy, rad, col in [
        (w * 0.82, h * 0.18, 6, GOLD),
        (w * 0.90, h * 0.30, 4, GREEN),
        (w * 0.88, h * 0.18, 3, ROSE),
    ]:
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad}" fill="{col}" opacity="0.85"/>'
        )
    # Bond hints
    parts.append(
        f'<line x1="{w * 0.82:.1f}" y1="{h * 0.18:.1f}" x2="{w * 0.88:.1f}" y2="{h * 0.18:.1f}" '
        f'stroke="{GOLD_DEEP}" stroke-width="1.2"/>'
    )
    parts.append(
        f'<line x1="{w * 0.82:.1f}" y1="{h * 0.18:.1f}" x2="{w * 0.90:.1f}" y2="{h * 0.30:.1f}" '
        f'stroke="{GOLD_DEEP}" stroke-width="1.2"/>'
    )

    _baseline(parts, w, h)
    parts.append('</svg>')
    return "".join(parts)


# ═══════════════════════════════════════════════════════════════════
# CARDIO — anatomical heart with halo + ECG trace + pulse rings
# ═══════════════════════════════════════════════════════════════════

def cardio(w: int = 720, h: int = 260, stage: str = "phase3") -> str:
    parts = _open(w, h)
    _texture(parts, w, h)

    # Pulse rings (3 concentric, gold) behind the heart
    cx, cy = w * 0.32, h * 0.50
    for ring_r, op in [(h * 0.55, 0.10), (h * 0.45, 0.16), (h * 0.35, 0.22)]:
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{ring_r:.1f}" '
            f'fill="none" stroke="{GOLD}" stroke-width="0.9" opacity="{op}"/>'
        )

    # Anatomical heart silhouette — refined
    sz = h * 0.38
    d = (
        f"M {cx:.1f} {cy + sz * 0.62:.1f} "
        f"C {cx - sz * 1.10:.1f} {cy + sz * 0.10:.1f}, "
        f"{cx - sz * 1.00:.1f} {cy - sz * 0.85:.1f}, "
        f"{cx - sz * 0.18:.1f} {cy - sz * 0.58:.1f} "
        f"C {cx - sz * 0.05:.1f} {cy - sz * 0.40:.1f}, "
        f"{cx + sz * 0.05:.1f} {cy - sz * 0.40:.1f}, "
        f"{cx + sz * 0.18:.1f} {cy - sz * 0.58:.1f} "
        f"C {cx + sz * 1.00:.1f} {cy - sz * 0.85:.1f}, "
        f"{cx + sz * 1.10:.1f} {cy + sz * 0.10:.1f}, "
        f"{cx:.1f} {cy + sz * 0.62:.1f} Z"
    )
    # Soft shadow underneath
    parts.append(f'<path d="{d}" fill="url(#rosegrad)" filter="url(#soft)"/>')
    # Outline
    parts.append(f'<path d="{d}" fill="none" stroke="{ROSE}" stroke-width="2.2" stroke-linejoin="round"/>')

    # Coronary arteries — three flowing curves over the heart
    arteries = [
        (cx - sz * 0.45, cy - sz * 0.20, cx - sz * 0.15, cy + sz * 0.30, cx + sz * 0.10, cy + sz * 0.50),
        (cx + sz * 0.50, cy - sz * 0.20, cx + sz * 0.20, cy + sz * 0.10, cx - sz * 0.05, cy + sz * 0.40),
        (cx, cy - sz * 0.35, cx, cy, cx + sz * 0.05, cy + sz * 0.45),
    ]
    for ax, ay, mx, my, ex, ey in arteries:
        parts.append(
            f'<path d="M {ax:.1f} {ay:.1f} Q {mx:.1f} {my:.1f} {ex:.1f} {ey:.1f}" '
            f'fill="none" stroke="{GREEN}" stroke-width="1.8" stroke-linecap="round" opacity="0.92"/>'
        )

    # Small highlight on top of heart
    parts.append(
        f'<ellipse cx="{cx - sz * 0.42:.1f}" cy="{cy - sz * 0.55:.1f}" '
        f'rx="{sz * 0.20:.1f}" ry="{sz * 0.08:.1f}" '
        f'fill="#fff" opacity="0.35"/>'
    )

    # ─── ECG trace running into the heart ─────────────────────────
    base_y = cy + sz * 0.05
    ecg_x0 = cx + sz * 1.25
    # P → PR → QRS → ST → T → flat
    pattern = [
        (24, 0), (10, -5), (10, 5), (8, 0),       # P
        (12, 0),                                  # PR
        (3, -12), (3, 34), (3, -22), (3, 0),     # QRS
        (10, 0),                                  # ST
        (12, -8), (12, 8), (8, 0),                # T
        (28, 0),
    ]
    pts = [(ecg_x0, base_y)]
    x = ecg_x0
    for dx, dy in pattern + pattern:
        x += dx; pts.append((x, base_y + dy))
        if dy != 0:
            x += 0; pts.append((x, base_y))
    d_ecg = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)

    # Soft glow under trace
    parts.append(f'<path d="{d_ecg}" fill="none" stroke="{GREEN_MIST}" stroke-width="6" opacity="0.55"/>')
    # Main trace
    parts.append(
        f'<path d="{d_ecg}" fill="none" stroke="{GREEN}" stroke-width="2.4" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
    )
    # Gold dotted baseline
    parts.append(
        f'<line x1="{ecg_x0:.1f}" y1="{base_y:.1f}" x2="{w - 16:.1f}" y2="{base_y:.1f}" '
        f'stroke="{GOLD}" stroke-width="0.8" stroke-dasharray="2 5"/>'
    )

    # A single gold marker dot at the QRS peak — focal accent
    qrs_x = ecg_x0 + 24 + 10 + 10 + 8 + 12 + 3
    parts.append(f'<circle cx="{qrs_x:.1f}" cy="{base_y - 12:.1f}" r="3" fill="{GOLD}"/>')

    _baseline(parts, w, h)
    parts.append('</svg>')
    return "".join(parts)


# ═══════════════════════════════════════════════════════════════════
# METABOLIC — liver silhouette + glucose molecule with downward arrow
# ═══════════════════════════════════════════════════════════════════

def metabolic(w: int = 720, h: int = 260, stage: str = "phase3") -> str:
    parts = _open(w, h)
    _texture(parts, w, h)

    # Liver — anatomically inspired (right lobe larger, gallbladder hint)
    lcx, lcy = w * 0.30, h * 0.52
    sz = h * 0.36

    # Soft halo
    parts.append(
        f'<ellipse cx="{lcx:.1f}" cy="{lcy:.1f}" '
        f'rx="{sz * 1.7:.1f}" ry="{sz * 1.15:.1f}" '
        f'fill="url(#goldgrad)" opacity="0.16"/>'
    )

    d_liver = (
        f"M {lcx - sz * 1.45:.1f} {lcy - sz * 0.20:.1f} "
        f"C {lcx - sz * 1.55:.1f} {lcy - sz * 0.90:.1f}, "
        f"{lcx - sz * 0.40:.1f} {lcy - sz * 1.20:.1f}, "
        f"{lcx + sz * 0.40:.1f} {lcy - sz * 1.00:.1f} "
        f"C {lcx + sz * 1.30:.1f} {lcy - sz * 0.80:.1f}, "
        f"{lcx + sz * 1.55:.1f} {lcy + sz * 0.35:.1f}, "
        f"{lcx + sz * 0.95:.1f} {lcy + sz * 0.75:.1f} "
        f"C {lcx + sz * 0.10:.1f} {lcy + sz * 1.05:.1f}, "
        f"{lcx - sz * 0.90:.1f} {lcy + sz * 0.95:.1f}, "
        f"{lcx - sz * 1.35:.1f} {lcy + sz * 0.35:.1f} "
        f"C {lcx - sz * 1.55:.1f} {lcy + sz * 0.05:.1f}, "
        f"{lcx - sz * 1.50:.1f} {lcy - sz * 0.05:.1f}, "
        f"{lcx - sz * 1.45:.1f} {lcy - sz * 0.20:.1f} Z"
    )
    parts.append(f'<path d="{d_liver}" fill="url(#goldgrad)" opacity="0.70" filter="url(#soft)"/>')
    parts.append(f'<path d="{d_liver}" fill="none" stroke="{GREEN}" stroke-width="2.2" stroke-linejoin="round"/>')

    # Lobe division
    parts.append(
        f'<path d="M {lcx - sz * 0.05:.1f} {lcy - sz * 1.05:.1f} '
        f'Q {lcx - sz * 0.35:.1f} {lcy + sz * 0.05:.1f} '
        f'{lcx + sz * 0.30:.1f} {lcy + sz * 0.85:.1f}" '
        f'fill="none" stroke="{GREEN}" stroke-width="1.5" opacity="0.85"/>'
    )

    # Surface highlight (subtle)
    parts.append(
        f'<path d="M {lcx - sz * 0.85:.1f} {lcy - sz * 0.60:.1f} '
        f'Q {lcx - sz * 0.50:.1f} {lcy - sz * 0.95:.1f} '
        f'{lcx + sz * 0.10:.1f} {lcy - sz * 0.85:.1f}" '
        f'fill="none" stroke="#fff" stroke-width="2" opacity="0.45" stroke-linecap="round"/>'
    )

    # Gallbladder hint
    parts.append(
        f'<ellipse cx="{lcx + sz * 0.55:.1f}" cy="{lcy + sz * 0.40:.1f}" '
        f'rx="{sz * 0.12:.1f}" ry="{sz * 0.20:.1f}" '
        f'fill="{GREEN_SOFT}" opacity="0.55" stroke="{GREEN}" stroke-width="1.2"/>'
    )

    # ─── Glucose hexagon on the right ────────────────────────────
    rcx, rcy = w * 0.72, h * 0.40
    R = h * 0.22
    hex_pts = [
        (rcx + R * math.cos(math.pi / 3 * i - math.pi / 6),
         rcy + R * math.sin(math.pi / 3 * i - math.pi / 6))
        for i in range(6)
    ]

    # Soft inner fill
    pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in hex_pts)
    parts.append(f'<polygon points="{pts_str}" fill="url(#greengrad)" opacity="0.25"/>')

    # Ring outline
    parts.append('<g stroke="' + INK + '" stroke-width="2" fill="none" stroke-linejoin="round">')
    for i in range(6):
        x1, y1 = hex_pts[i]; x2, y2 = hex_pts[(i + 1) % 6]
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    parts.append('</g>')

    # Vertex carbons (dots)
    for x, y in hex_pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{INK}"/>')

    # OH substituents — at three alternate vertices, longer bond
    for i, (x, y) in enumerate(hex_pts):
        ang = math.atan2(y - rcy, x - rcx)
        if i % 2 == 0:
            ox = x + math.cos(ang) * 16
            oy = y + math.sin(ang) * 16
            parts.append(
                f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" '
                f'stroke="{GOLD_DEEP}" stroke-width="1.5"/>'
            )
            parts.append(
                f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="5" '
                f'fill="{GOLD_LIGHT}" stroke="{GOLD_DEEP}" stroke-width="1.2"/>'
            )

    # ─── Sweeping arrow from molecule down to liver baseline ─────
    ax0, ay0 = w * 0.55, h * 0.30
    ax1, ay1 = w * 0.50, h * 0.78
    mid_x = w * 0.46
    mid_y = h * 0.65
    parts.append(
        f'<path d="M {ax0:.1f} {ay0:.1f} Q {mid_x:.1f} {mid_y:.1f} {ax1:.1f} {ay1:.1f}" '
        f'fill="none" stroke="{GREEN}" stroke-width="2.5" stroke-linecap="round" '
        f'marker-end="url(#arrow_met)"/>'
    )
    parts.append(
        f'<defs><marker id="arrow_met" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{GREEN}"/></marker></defs>'
    )

    _baseline(parts, w, h)
    parts.append('</svg>')
    return "".join(parts)


# ═══════════════════════════════════════════════════════════════════
# NEURO — brain side-profile with sulci + neuron network with synapses
# ═══════════════════════════════════════════════════════════════════

def neuro(w: int = 720, h: int = 260, stage: str = "phase3") -> str:
    parts = _open(w, h)
    _texture(parts, w, h)

    # Brain silhouette — refined side profile
    cx, cy = w * 0.30, h * 0.50
    sz = h * 0.38

    # Halo
    parts.append(
        f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" '
        f'rx="{sz * 1.7:.1f}" ry="{sz * 1.4:.1f}" '
        f'fill="url(#goldgrad)" opacity="0.14"/>'
    )

    d_brain = (
        f"M {cx - sz * 1.25:.1f} {cy + sz * 0.30:.1f} "
        f"C {cx - sz * 1.50:.1f} {cy - sz * 0.30:.1f}, "
        f"{cx - sz * 1.20:.1f} {cy - sz * 1.05:.1f}, "
        f"{cx - sz * 0.35:.1f} {cy - sz * 1.20:.1f} "
        # bump for frontal lobe
        f"C {cx - sz * 0.05:.1f} {cy - sz * 1.30:.1f}, "
        f"{cx + sz * 0.20:.1f} {cy - sz * 1.30:.1f}, "
        f"{cx + sz * 0.50:.1f} {cy - sz * 1.15:.1f} "
        f"C {cx + sz * 1.20:.1f} {cy - sz * 0.95:.1f}, "
        f"{cx + sz * 1.40:.1f} {cy - sz * 0.15:.1f}, "
        f"{cx + sz * 1.10:.1f} {cy + sz * 0.55:.1f} "
        # brain stem hint
        f"C {cx + sz * 0.80:.1f} {cy + sz * 0.90:.1f}, "
        f"{cx + sz * 0.30:.1f} {cy + sz * 0.95:.1f}, "
        f"{cx - sz * 0.30:.1f} {cy + sz * 0.90:.1f} "
        f"C {cx - sz * 0.95:.1f} {cy + sz * 0.85:.1f}, "
        f"{cx - sz * 1.30:.1f} {cy + sz * 0.65:.1f}, "
        f"{cx - sz * 1.25:.1f} {cy + sz * 0.30:.1f} Z"
    )
    parts.append(f'<path d="{d_brain}" fill="url(#goldgrad)" opacity="0.55" filter="url(#soft)"/>')
    parts.append(f'<path d="{d_brain}" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>')

    # Sulci — meandering interior folds
    sulci = [
        # (y_offset, amplitude)
        (-sz * 0.65, 0.10), (-sz * 0.30, 0.14), (-sz * 0.00, 0.12),
        ( sz * 0.30, 0.10), ( sz * 0.60, 0.08),
    ]
    for off_y, amp in sulci:
        x0 = cx - sz * 1.10
        n = 24
        pts = []
        for i in range(n + 1):
            t = i / n
            xx = x0 + t * sz * 2.30
            yy = cy + off_y + math.sin(t * math.pi * 3.2) * sz * amp
            pts.append((xx, yy))
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        parts.append(
            f'<path d="{d}" fill="none" stroke="{GREEN}" stroke-width="1.4" '
            f'stroke-linecap="round" opacity="0.55"/>'
        )

    # ─── Neuron network on the right ─────────────────────────────
    nodes = [
        (w * 0.58, h * 0.30),
        (w * 0.72, h * 0.22),
        (w * 0.88, h * 0.35),
        (w * 0.62, h * 0.62),
        (w * 0.80, h * 0.70),
        (w * 0.92, h * 0.55),
    ]

    # Connecting axons — curvy, gold
    pairs = [(0, 1), (1, 2), (1, 3), (3, 4), (4, 5), (2, 5), (0, 3)]
    for a, b in pairs:
        x1, y1 = nodes[a]; x2, y2 = nodes[b]
        mx = (x1 + x2) / 2 + (x2 - x1) * 0.1
        my = (y1 + y2) / 2 - 14
        parts.append(
            f'<path d="M {x1:.1f} {y1:.1f} Q {mx:.1f} {my:.1f} {x2:.1f} {y2:.1f}" '
            f'fill="none" stroke="{GOLD}" stroke-width="1.6" '
            f'stroke-linecap="round" opacity="0.85"/>'
        )

    # Synapse pulse — a gold dot midway through one connection (focal)
    sx0, sy0 = nodes[1]; sx1, sy1 = nodes[3]
    parts.append(
        f'<circle cx="{(sx0 + sx1) / 2:.1f}" cy="{(sy0 + sy1) / 2 - 8:.1f}" r="3.5" '
        f'fill="{ROSE}"/>'
    )

    # Neuron cell bodies with dendrites
    import random
    rng = random.Random(stage)
    for i, (x, y) in enumerate(nodes):
        # Soma
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" '
            f'fill="{GREEN}" stroke="{INK}" stroke-width="1.2"/>'
        )
        # Dendrites
        n_dend = 4 if i == 1 else 3
        for _ in range(n_dend):
            ang = rng.uniform(0, math.tau)
            ex = x + math.cos(ang) * 16
            ey = y + math.sin(ang) * 16
            parts.append(
                f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                f'stroke="{INK_SOFT}" stroke-width="1.2" stroke-linecap="round" opacity="0.85"/>'
            )
            # End knob
            parts.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="1.6" fill="{INK_SOFT}"/>')

    _baseline(parts, w, h)
    parts.append('</svg>')
    return "".join(parts)


# ═══════════════════════════════════════════════════════════════════
# LONGEVITY — hourglass with sand + rising sun + small sapling
# ═══════════════════════════════════════════════════════════════════

def longevity(w: int = 720, h: int = 260, stage: str = "phase3") -> str:
    parts = _open(w, h)
    _texture(parts, w, h)

    # ─── Hourglass on the left ───────────────────────────────────
    hx = w * 0.27
    hy = h * 0.50
    hw = h * 0.50
    hh = h * 0.62

    # Halo
    parts.append(
        f'<ellipse cx="{hx:.1f}" cy="{hy:.1f}" rx="{hw * 1.4:.1f}" ry="{hh * 1.15:.1f}" '
        f'fill="url(#goldgrad)" opacity="0.16"/>'
    )

    # Caps (top and bottom)
    parts.append(
        f'<rect x="{hx - hw / 2 - 4:.1f}" y="{hy - hh - 5:.1f}" width="{hw + 8}" height="6" rx="2" '
        f'fill="{GOLD_DEEP}"/>'
    )
    parts.append(
        f'<rect x="{hx - hw / 2 - 4:.1f}" y="{hy + hh - 1:.1f}" width="{hw + 8}" height="6" rx="2" '
        f'fill="{GOLD_DEEP}"/>'
    )

    # Top bulb (gold) — represents time remaining; shrink for late-stage trial
    fill_top = 0.85 if stage in ("phase1", "phase2") else 0.55
    parts.append(
        f'<path d="M {hx - hw / 2:.1f} {hy - hh:.1f} '
        f'L {hx + hw / 2:.1f} {hy - hh:.1f} '
        f'L {hx + 6:.1f} {hy - 2:.1f} '
        f'L {hx - 6:.1f} {hy - 2:.1f} Z" '
        f'fill="none" stroke="{INK}" stroke-width="2"/>'
    )
    # Sand in top bulb (clipped triangle)
    parts.append(
        f'<path d="M {hx - hw / 2 + 4:.1f} {hy - hh * (1 - (1 - fill_top)):.1f} '
        f'L {hx + hw / 2 - 4:.1f} {hy - hh * (1 - (1 - fill_top)):.1f} '
        f'L {hx + 6:.1f} {hy - 4:.1f} '
        f'L {hx - 6:.1f} {hy - 4:.1f} Z" '
        f'fill="url(#goldgrad)" opacity="0.95"/>'
    )

    # Bottom bulb (filling with sand)
    parts.append(
        f'<path d="M {hx - 6:.1f} {hy + 2:.1f} '
        f'L {hx + 6:.1f} {hy + 2:.1f} '
        f'L {hx + hw / 2:.1f} {hy + hh:.1f} '
        f'L {hx - hw / 2:.1f} {hy + hh:.1f} Z" '
        f'fill="none" stroke="{INK}" stroke-width="2"/>'
    )
    # Sand pile in bottom — small hill
    pile_h = hh * 0.30
    parts.append(
        f'<path d="M {hx - hw * 0.42:.1f} {hy + hh:.1f} '
        f'Q {hx:.1f} {hy + hh - pile_h:.1f} '
        f'{hx + hw * 0.42:.1f} {hy + hh:.1f} Z" '
        f'fill="url(#goldgrad)" stroke="{GOLD_DEEP}" stroke-width="1.2" stroke-linejoin="round"/>'
    )

    # Falling sand stream — single thin line + 3 grains
    parts.append(
        f'<line x1="{hx:.1f}" y1="{hy:.1f}" x2="{hx:.1f}" y2="{hy + hh * 0.65:.1f}" '
        f'stroke="{GOLD}" stroke-width="1.2" opacity="0.85"/>'
    )
    for gy in (hy + hh * 0.10, hy + hh * 0.30, hy + hh * 0.50):
        parts.append(f'<circle cx="{hx:.1f}" cy="{gy:.1f}" r="1.6" fill="{GOLD_DEEP}"/>')

    # Glass highlight (white sliver)
    parts.append(
        f'<line x1="{hx - hw / 2 + 6:.1f}" y1="{hy - hh + 8:.1f}" '
        f'x2="{hx - hw / 2 + 6:.1f}" y2="{hy - 6:.1f}" '
        f'stroke="#fff" stroke-width="1.2" opacity="0.7"/>'
    )
    parts.append(
        f'<line x1="{hx - hw / 2 + 6:.1f}" y1="{hy + 6:.1f}" '
        f'x2="{hx - hw / 2 + 6:.1f}" y2="{hy + hh - 8:.1f}" '
        f'stroke="#fff" stroke-width="1.2" opacity="0.7"/>'
    )

    # ─── Sun rising over horizon on the right ────────────────────
    sx, sy = w * 0.72, h * 0.72
    R = h * 0.40

    # Half-arc of horizon
    arc_pts = []
    for i in range(28):
        a = math.pi + (math.pi * i / 27)
        arc_pts.append((sx + R * math.cos(a), sy + R * math.sin(a)))
    d_arc = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in arc_pts)
    parts.append(f'<path d="{d_arc}" fill="none" stroke="{INK_SOFT}" stroke-width="1.2" opacity="0.55"/>')

    # Sun core
    sun_y = sy - R * 0.42
    parts.append(
        f'<circle cx="{sx:.1f}" cy="{sun_y:.1f}" r="14" '
        f'fill="url(#goldgrad)" stroke="{GOLD_DEEP}" stroke-width="1.5" filter="url(#soft)"/>'
    )
    # Inner highlight
    parts.append(f'<circle cx="{sx - 4:.1f}" cy="{sun_y - 4:.1f}" r="3" fill="#fff" opacity="0.55"/>')

    # Rays — 8 short rays, alternating long/short
    for k, ang_d in enumerate(range(0, 360, 30)):
        ang = math.radians(ang_d)
        long = 28 if k % 2 == 0 else 20
        rx0 = sx + math.cos(ang) * 18
        ry0 = sun_y + math.sin(ang) * 18
        rx1 = sx + math.cos(ang) * long
        ry1 = sun_y + math.sin(ang) * long
        parts.append(
            f'<line x1="{rx0:.1f}" y1="{ry0:.1f}" x2="{rx1:.1f}" y2="{ry1:.1f}" '
            f'stroke="{GOLD_DEEP}" stroke-width="1.6" stroke-linecap="round"/>'
        )

    # Horizon line
    parts.append(
        f'<line x1="{sx - R - 8:.1f}" y1="{sy:.1f}" x2="{sx + R + 8:.1f}" y2="{sy:.1f}" '
        f'stroke="{INK}" stroke-width="1.5"/>'
    )

    # Tiny sapling on the horizon, just left of the sun
    spx = sx - R * 0.55
    spy = sy
    parts.append(f'<line x1="{spx:.1f}" y1="{spy:.1f}" x2="{spx:.1f}" y2="{spy - 18:.1f}" stroke="{GREEN}" stroke-width="1.6" stroke-linecap="round"/>')
    parts.append(f'<path d="M {spx:.1f} {spy - 10:.1f} Q {spx - 6:.1f} {spy - 16:.1f} {spx - 10:.1f} {spy - 10:.1f}" fill="none" stroke="{GREEN}" stroke-width="1.6" stroke-linecap="round"/>')
    parts.append(f'<path d="M {spx:.1f} {spy - 14:.1f} Q {spx + 6:.1f} {spy - 20:.1f} {spx + 10:.1f} {spy - 14:.1f}" fill="none" stroke="{GREEN}" stroke-width="1.6" stroke-linecap="round"/>')

    _baseline(parts, w, h)
    parts.append('</svg>')
    return "".join(parts)


# ═══════════════════════════════════════════════════════════════════
# OTHER / generic — open journal + magnifying glass + ink spot
# ═══════════════════════════════════════════════════════════════════

def other(w: int = 720, h: int = 260, stage: str = "phase3") -> str:
    parts = _open(w, h)
    _texture(parts, w, h)

    # Open book
    bx, by = w * 0.32, h * 0.55
    bw, bh = h * 1.30, h * 0.60

    # Page shadow
    parts.append(
        f'<ellipse cx="{bx:.1f}" cy="{by + bh / 2 + 8:.1f}" '
        f'rx="{bw / 2:.1f}" ry="6" fill="{INK}" opacity="0.10"/>'
    )

    # Left and right pages
    parts.append(
        f'<path d="M {bx - bw / 2:.1f} {by + bh / 2:.1f} '
        f'L {bx - bw / 2 - 6:.1f} {by - bh / 2 + 4:.1f} '
        f'L {bx - 2:.1f} {by - bh / 2 + 10:.1f} '
        f'L {bx - 2:.1f} {by + bh / 2:.1f} Z" '
        f'fill="#fffaf0" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>'
    )
    parts.append(
        f'<path d="M {bx + bw / 2:.1f} {by + bh / 2:.1f} '
        f'L {bx + bw / 2 + 6:.1f} {by - bh / 2 + 4:.1f} '
        f'L {bx + 2:.1f} {by - bh / 2 + 10:.1f} '
        f'L {bx + 2:.1f} {by + bh / 2:.1f} Z" '
        f'fill="#fffaf0" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>'
    )

    # Spine fold
    parts.append(
        f'<line x1="{bx:.1f}" y1="{by - bh / 2 + 10:.1f}" x2="{bx:.1f}" y2="{by + bh / 2:.1f}" '
        f'stroke="{INK_FAINT}" stroke-width="1"/>'
    )

    # Page text lines (alternating lengths for editorial feel)
    line_lens = [0.42, 0.38, 0.46, 0.34, 0.40, 0.30]
    line_lens_r = [0.38, 0.46, 0.42, 0.40, 0.36, 0.32]
    for i, frac in enumerate(line_lens):
        ly = by - bh * 0.30 + i * 11
        parts.append(
            f'<line x1="{bx - bw / 2 + 16:.1f}" y1="{ly:.1f}" '
            f'x2="{bx - bw / 2 + 16 + bw * frac:.1f}" y2="{ly:.1f}" '
            f'stroke="{INK_SOFT}" stroke-width="1.4" stroke-linecap="round"/>'
        )
    for i, frac in enumerate(line_lens_r):
        ly = by - bh * 0.30 + i * 11
        parts.append(
            f'<line x1="{bx + 12:.1f}" y1="{ly:.1f}" '
            f'x2="{bx + 12 + bw * frac:.1f}" y2="{ly:.1f}" '
            f'stroke="{INK_SOFT}" stroke-width="1.4" stroke-linecap="round"/>'
        )

    # A small green title underline on the left page
    parts.append(
        f'<line x1="{bx - bw / 2 + 16:.1f}" y1="{by - bh * 0.32:.1f}" '
        f'x2="{bx - bw / 2 + 16 + bw * 0.18:.1f}" y2="{by - bh * 0.32:.1f}" '
        f'stroke="{GREEN}" stroke-width="2.5" stroke-linecap="round"/>'
    )

    # Magnifying glass over right page
    mcx, mcy = w * 0.74, h * 0.40
    mr = h * 0.22
    # Halo
    parts.append(
        f'<circle cx="{mcx:.1f}" cy="{mcy:.1f}" r="{mr * 1.5:.1f}" '
        f'fill="url(#goldgrad)" opacity="0.16"/>'
    )
    # Lens fill
    parts.append(
        f'<circle cx="{mcx:.1f}" cy="{mcy:.1f}" r="{mr:.1f}" '
        f'fill="{GOLD_LIGHT}" opacity="0.20"/>'
    )
    # Lens outline (thick)
    parts.append(
        f'<circle cx="{mcx:.1f}" cy="{mcy:.1f}" r="{mr:.1f}" '
        f'fill="none" stroke="{GREEN}" stroke-width="3.5"/>'
    )
    # Inner lens highlight
    parts.append(
        f'<ellipse cx="{mcx - mr * 0.35:.1f}" cy="{mcy - mr * 0.35:.1f}" '
        f'rx="{mr * 0.18:.1f}" ry="{mr * 0.10:.1f}" '
        f'fill="#fff" opacity="0.6"/>'
    )
    # Handle
    parts.append(
        f'<line x1="{mcx + mr * 0.72:.1f}" y1="{mcy + mr * 0.72:.1f}" '
        f'x2="{mcx + mr * 1.55:.1f}" y2="{mcy + mr * 1.55:.1f}" '
        f'stroke="{GREEN}" stroke-width="6" stroke-linecap="round"/>'
    )
    parts.append(
        f'<line x1="{mcx + mr * 0.72:.1f}" y1="{mcy + mr * 0.72:.1f}" '
        f'x2="{mcx + mr * 1.55:.1f}" y2="{mcy + mr * 1.55:.1f}" '
        f'stroke="{GOLD_DEEP}" stroke-width="1.8"/>'
    )

    # Ink dot — focal accent (top right, small)
    parts.append(
        f'<circle cx="{w * 0.92:.1f}" cy="{h * 0.18:.1f}" r="4" fill="{ROSE}"/>'
    )

    _baseline(parts, w, h)
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


def illo_svg(item: dict, w: int = 720, h: int = 260) -> str:
    cat = item.get("category", "other")
    stage = item.get("stage", "phase3")
    fn = _RENDERERS.get(cat, other)
    try:
        return fn(w=w, h=h, stage=stage)
    except Exception:
        return other(w=w, h=h, stage=stage)
