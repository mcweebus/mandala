# wipe.py
# The mandala wipe — reusable dissolution ceremony between levels.
#
# Usage:
#   from wipe import play_mandala_wipe
#   play_mandala_wipe(stdscr)
#
# Three phases:
#   1. Build  — mandala materialises ring by ring, center outward (~4s)
#   2. Hold   — stillness (~3s)
#   3. Wipe   — dust blown in the wind: outer cells go first,
#               in irregular gusts with pauses between them
#
# Pattern: 8-fold rotational symmetry. Each cell is mapped by its
# elliptical radius (fills the terminal) and aspect-corrected angle.
# Spokes + concentric rings + petals at intersections.
# Brightness gradient: bold center → normal → dim outer edge.

import curses
import math
import random
import time

import screen as scr

# ── Tuning ────────────────────────────────────────────────────
SYMMETRY      = 8
BUILD_STEPS   = 80       # reveal batches during build
BUILD_DELAY   = 0.05     # seconds per build step  →  ~4 s total
HOLD_DURATION = 3.0      # seconds to hold the completed mandala

# Wind wipe — each gust: dim-flash → erase all at once → pause.
# "Fits and starts": variable gust sizes and uneven pauses.
GUST_MIN_FRAC = 0.06     # smallest gust: 6% of remaining cells
GUST_MAX_FRAC = 0.28     # largest gust: 28% of remaining cells
FADE_DURATION = 0.07     # seconds cells dim before vanishing
PAUSE_MIN     = 0.12     # shortest breath between gusts
PAUSE_MAX     = 0.52     # longest breath between gusts (~20-28 gusts total ~8-10s)

# Title flash — "mandala" appears centred after the hold, before the wipe.
TITLE           = "mandala"
TITLE_FLASHES   = 3      # on-off cycles
TITLE_ON        = 0.25   # seconds each bold flash lasts
TITLE_OFF       = 0.15   # dark gap between flashes

# Aspect correction for angle calculation — terminal chars are ~2× taller than wide.
ASPECT = 0.5

# ── Fill character palettes ────────────────────────────────────
# Structural chars (@, *, +, o) define the geometry; these fill the space between.
# Picked deterministically by position so the texture is stable, not random noise.
_FILL_INNER  = "X8HBS"    # dense, visually heavy — centre region
_FILL_MID    = "xvsun"    # medium weight — mid rings
_FILL_OUTER  = "zrije"    # lighter — outer fringe

def _pick(chars: str, row: int, col: int) -> str:
    return chars[(row * 7 + col * 13) % len(chars)]


# ── Geometry ──────────────────────────────────────────────────

def _cell_params(row: int, col: int, cy: int, cx: int,
                 rx: float, ry: float) -> tuple[float, float, bool]:
    """Return (r_norm, theta_sym, in_bounds).

    r_norm    — elliptical radius, 0=center, 1=edge of screen-filling ellipse
    theta_sym — folded angle, 0=on spoke, 1=between spokes (aspect-corrected)
    in_bounds — False if outside the ellipse
    """
    dx = col - cx
    dy = row - cy

    # Elliptical normalisation — fills the terminal regardless of dimensions.
    r_ellipse = math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2) if rx and ry else 0.0
    if r_ellipse > 1.0:
        return 0.0, 0.0, False

    # Aspect-corrected angle keeps spokes visually even across the ellipse.
    theta     = math.atan2(dy, dx * ASPECT) % (2 * math.pi)
    theta_sym = _fold(theta)

    return r_ellipse, theta_sym, True


def _fold(theta: float) -> float:
    """Fold theta into one symmetry sector, mirrored.
    Returns [0, 1]: 0 = on a spoke, 1 = midway between spokes."""
    sector = (2 * math.pi) / SYMMETRY
    t = theta % sector
    if t > sector / 2:
        t = sector - t
    return t / (sector / 2)


# ── Character / brightness mapping ────────────────────────────

def _cell(r_norm: float, theta_sym: float,
          row: int = 0, col: int = 0) -> tuple[str, bool, bool]:
    """Map (r_norm, theta_sym, row, col) → (char, bold, dim)."""
    on_spoke   = theta_sym < 0.13
    near_spoke = theta_sym < 0.26

    ring_phase = (r_norm * 6.0) % 1.0
    on_ring    = ring_phase < 0.20
    near_ring  = ring_phase < 0.38

    # Center seed
    if r_norm < 0.04:
        return "@", True, False

    # Petal — spoke × ring intersection
    if on_spoke and on_ring:
        return "*", r_norm < 0.60, r_norm >= 0.60

    # Spoke lines
    if on_spoke:
        if r_norm < 0.33:
            return "+", True, False
        elif r_norm < 0.66:
            return "+", False, False
        else:
            return _pick(_FILL_OUTER, row, col), False, True

    # Concentric ring arcs
    if on_ring:
        if r_norm < 0.28:
            return "o", True, False
        elif r_norm < 0.58:
            return "o", False, False
        else:
            return _pick(_FILL_OUTER, row, col), False, True

    # Secondary detail at near-spoke × near-ring
    if near_spoke and near_ring:
        return _pick(_FILL_MID, row, col), False, r_norm >= 0.45

    # Fill
    if r_norm < 0.28:
        return _pick(_FILL_INNER, row, col), False, False
    elif r_norm < 0.60:
        return _pick(_FILL_MID, row, col), False, True
    else:
        return _pick(_FILL_OUTER, row, col), False, True   # outer fringe


# ── Grid construction ─────────────────────────────────────────

def _build_grid(h: int, w: int) -> tuple[dict, float, float]:
    """Return (grid, rx, ry).
    grid: {(row, col): (char, bold, dim)}
    rx, ry: ellipse semi-axes in screen units
    """
    cy = h // 2
    cx = w // 2
    rx = w // 2 - 2
    ry = h // 2 - 1

    grid = {}
    for row in range(h):
        for col in range(w):
            r_norm, theta_sym, ok = _cell_params(row, col, cy, cx, rx, ry)
            if not ok:
                continue
            ch, bold, dim = _cell(r_norm, theta_sym, row, col)
            if ch.strip():
                grid[(row, col)] = (ch, bold, dim)
    return grid, rx, ry


# ── Build phase ───────────────────────────────────────────────

def _phase_build(stdscr, grid: dict,
                 cy: int, cx: int, rx: float, ry: float) -> None:
    """Reveal center-outward in BUILD_STEPS batches."""
    cells = sorted(
        grid.items(),
        key=lambda item: math.sqrt(
            ((item[0][1] - cx) / rx) ** 2 +
            ((item[0][0] - cy) / ry) ** 2
        )
    )
    batch = max(1, len(cells) // BUILD_STEPS)

    stdscr.erase()
    for i, ((row, col), (ch, bold, dim)) in enumerate(cells):
        scr.addch(stdscr, row, col, ch, bold=bold, dim=dim)
        if i % batch == 0:
            stdscr.refresh()
            time.sleep(BUILD_DELAY)
    stdscr.refresh()


# ── Title flash ───────────────────────────────────────────────

def _phase_title(stdscr, cy: int, cx: int) -> None:
    """Flash TITLE centred on the mandala, then leave it dim as wipe begins."""
    col = cx - len(TITLE) // 2
    for _ in range(TITLE_FLASHES):
        scr.addstr(stdscr, cy, col, TITLE, bold=True)
        stdscr.refresh()
        time.sleep(TITLE_ON)
        scr.addstr(stdscr, cy, col, TITLE, dim=True)
        stdscr.refresh()
        time.sleep(TITLE_OFF)


# ── Wipe phase ────────────────────────────────────────────────

def _phase_wipe(stdscr, grid: dict,
                cy: int, cx: int, rx: float, ry: float) -> None:
    """Dissolve like dust in wind — outer cells first, in irregular gusts."""

    # Score each cell: outer cells are less anchored and go first.
    # Randomness makes the order organic rather than ring-perfect.
    scored = []
    for (row, col), cell_data in grid.items():
        r_ellipse = math.sqrt(
            ((col - cx) / rx) ** 2 + ((row - cy) / ry) ** 2
        )
        wind_score = r_ellipse * 0.55 + random.random() * 0.45
        scored.append((wind_score, (row, col), cell_data))

    # Sort descending — highest score (outer / random-first) erases first.
    scored.sort(key=lambda x: x[0], reverse=True)
    cells = [(pos, data) for _, pos, data in scored]

    n      = len(cells)
    erased = 0

    while erased < n:
        remaining  = n - erased
        gust_frac  = random.uniform(GUST_MIN_FRAC, GUST_MAX_FRAC)
        gust_size  = max(2, min(remaining, int(remaining * gust_frac)))
        gust       = cells[erased : erased + gust_size]

        # Pre-fade: dim the entire gust briefly before it disappears.
        for (row, col), (ch, bold, _dim) in gust:
            scr.addch(stdscr, row, col, ch, bold=False, dim=True)
        stdscr.refresh()
        time.sleep(FADE_DURATION)

        # Erase — all gust cells vanish at once (poof).
        for (row, col), _ in gust:
            scr.addch(stdscr, row, col, " ")

        stdscr.refresh()
        erased += gust_size

        # Irregular pause — some gusts come right after, others wait.
        time.sleep(random.uniform(PAUSE_MIN, PAUSE_MAX))

    stdscr.erase()
    stdscr.refresh()
    time.sleep(0.4)


# ── Public entry point ────────────────────────────────────────

def play_mandala_wipe(stdscr) -> None:
    """Full mandala formation and dissolution. Blocks until complete."""
    h, w = stdscr.getmaxyx()
    cy   = h // 2
    cx   = w // 2

    grid, rx, ry = _build_grid(h, w)
    if not grid:
        return

    _phase_build(stdscr, grid, cy, cx, rx, ry)
    time.sleep(HOLD_DURATION)
    _phase_title(stdscr, cy, cx)
    _phase_wipe(stdscr, grid, cy, cx, rx, ry)
