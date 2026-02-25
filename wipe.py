# wipe.py
# The mandala wipe — reusable dissolution ceremony between levels.
#
# Usage:
#   from wipe import play_mandala_wipe
#   play_mandala_wipe(stdscr)
#
# Three phases:
#   1. Build  — mandala materialises ring by ring from center outward
#   2. Hold   — a moment of stillness
#   3. Wipe   — a clockwise sweep arm erases the mandala
#
# The pattern uses 8-fold rotational symmetry. Every cell within the
# mandala circle is assigned a character and brightness based on its
# (r_norm, theta_sym) polar position. Spokes radiate from the center;
# concentric rings cross them; petals form at intersections.
#
# Brightness gradient: bold center → normal midfield → dim outer edge.

import curses
import math
import time

import screen as scr

# ── Tuning ────────────────────────────────────────────────────
SYMMETRY        = 8       # n-fold rotational symmetry
BUILD_STEPS     = 48      # number of reveal batches during build
BUILD_DELAY     = 0.03    # seconds per build step
HOLD_DURATION   = 1.8     # seconds to hold the completed mandala
WIPE_STEPS      = 90      # frames for the clockwise sweep
WIPE_DELAY      = 0.011   # seconds per wipe frame

# Aspect correction: terminal cells are roughly 2× taller than wide.
# Multiplying x-offset by this makes the mandala appear circular.
ASPECT = 0.5


# ── Geometry ──────────────────────────────────────────────────

def _polar(row: int, col: int, cy: int, cx: int) -> tuple[float, float]:
    """Return aspect-corrected (r, theta) with theta in [0, 2π)."""
    dx    = (col - cx) * ASPECT
    dy    = row - cy
    r     = math.sqrt(dx * dx + dy * dy)
    theta = math.atan2(dy, dx) % (2 * math.pi)
    return r, theta


def _fold(theta: float) -> float:
    """Fold theta into a single symmetry sector, mirrored.
    Returns value in [0, 1]: 0 = on a spoke, 1 = midway between spokes."""
    sector = (2 * math.pi) / SYMMETRY
    t      = theta % sector
    if t > sector / 2:
        t = sector - t
    return t / (sector / 2)


# ── Character / brightness mapping ────────────────────────────

def _cell(r_norm: float, theta_sym: float) -> tuple[str, bool, bool]:
    """Map (r_norm ∈ [0,1], theta_sym ∈ [0,1]) → (char, bold, dim).

    r_norm   : 0 = center, 1 = outer edge of circle
    theta_sym: 0 = on a spoke, 1 = between spokes
    """
    on_spoke      = theta_sym < 0.14
    near_spoke    = theta_sym < 0.28

    # Ring phase: fractional position within a repeating radial band.
    ring_phase    = (r_norm * 5.5) % 1.0
    on_ring       = ring_phase < 0.18
    near_ring     = ring_phase < 0.34

    # ── Center seed ──────────────────────────────────────────
    if r_norm < 0.05:
        return "@", True, False

    # ── Petal: spoke × ring intersection ─────────────────────
    if on_spoke and on_ring:
        if r_norm < 0.55:
            return "*", True, False
        else:
            return "*", False, False

    # ── Spoke lines ──────────────────────────────────────────
    if on_spoke:
        if r_norm < 0.35:
            return "+", True, False
        elif r_norm < 0.65:
            return "+", False, False
        else:
            return ".", False, True

    # ── Concentric ring arcs ─────────────────────────────────
    if on_ring:
        if r_norm < 0.30:
            return "o", True, False
        elif r_norm < 0.60:
            return "o", False, False
        else:
            return ".", False, True

    # ── Near-spoke / near-ring secondary detail ───────────────
    if near_spoke and near_ring:
        dim = r_norm >= 0.5
        return ".", False, dim

    # ── Fill: everything else inside the circle ───────────────
    if r_norm < 0.30:
        return ".", False, False
    elif r_norm < 0.62:
        return ".", False, True
    else:
        return " ", False, True    # sparse outer fringe


# ── Grid construction ─────────────────────────────────────────

def _build_grid(h: int, w: int) -> dict:
    """Return {(row, col): (char, bold, dim)} for the full mandala."""
    cy    = h // 2
    cx    = w // 2
    max_r = min(h // 2 - 1, (w // 2 - 1) * ASPECT)

    grid = {}
    for row in range(h):
        for col in range(w):
            r, theta = _polar(row, col, cy, cx)
            if r > max_r:
                continue
            r_norm    = r / max_r
            theta_sym = _fold(theta)
            ch, bold, dim = _cell(r_norm, theta_sym)
            if ch.strip():    # exclude pure-space cells
                grid[(row, col)] = (ch, bold, dim)
    return grid


# ── Animation phases ──────────────────────────────────────────

def _phase_build(stdscr, grid: dict, cy: int, cx: int) -> None:
    """Reveal the mandala from center outward in BUILD_STEPS batches."""
    cells = sorted(
        grid.items(),
        key=lambda item: _polar(item[0][0], item[0][1], cy, cx)[0]
    )
    batch_size = max(1, len(cells) // BUILD_STEPS)

    stdscr.erase()
    for i, ((row, col), (ch, bold, dim)) in enumerate(cells):
        scr.addch(stdscr, row, col, ch, bold=bold, dim=dim)
        if i % batch_size == 0:
            stdscr.refresh()
            time.sleep(BUILD_DELAY)

    stdscr.refresh()


def _phase_wipe(stdscr, grid: dict, cy: int, cx: int) -> None:
    """Erase the mandala with a clockwise sweep arm from 12 o'clock."""

    def _cw_angle(item):
        (row, col), _ = item
        dx = (col - cx) * ASPECT
        dy = row - cy
        # Rotate so 12 o'clock = 0, sweeping clockwise
        return (math.atan2(dy, dx) + math.pi / 2) % (2 * math.pi)

    cells   = sorted(grid.items(), key=_cw_angle)
    n       = len(cells)
    batch   = max(1, n // WIPE_STEPS)

    for i in range(0, n, batch):
        for (row, col), _ in cells[i : i + batch]:
            try:
                stdscr.addch(row, col, " ")
            except curses.error:
                pass
        stdscr.refresh()
        time.sleep(WIPE_DELAY)

    stdscr.erase()
    stdscr.refresh()
    time.sleep(0.25)


# ── Public entry point ────────────────────────────────────────

def play_mandala_wipe(stdscr) -> None:
    """Full mandala formation and dissolution. Blocks until complete.
    Call from within a curses.wrapper context."""
    h, w = stdscr.getmaxyx()
    cy   = h // 2
    cx   = w // 2

    grid = _build_grid(h, w)
    if not grid:
        return

    _phase_build(stdscr, grid, cy, cx)
    time.sleep(HOLD_DURATION)
    _phase_wipe(stdscr, grid, cy, cx)
