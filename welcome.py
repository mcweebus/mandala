# welcome.py
# Welcome screen for mandala.
#
# Sequence:
#   1. "mandala" types itself bold at centre.
#   2. A full a-z mandala fills in around it — title stays in place.
#   3. The completed mandala holds. A prompt fades in.
#   4. Any key triggers the gust wipe.
#      One cell per unique letter of "mandala" {m, a, n, d, l} is spared,
#      chosen at random from anywhere in the mandala body.
#   5. Five letters remain scattered on a dark screen — seeds.
#   6. They linger, then the screen clears and level 1 begins.
#
# Monochrome only. No curses color pairs.

import curses
import math
import random
import string
import time

import screen as scr

# ── Constants ─────────────────────────────────────────────────
_TITLE       = "mandala"
_SEEDS       = set(_TITLE)            # unique: {m, a, n, d, l}
_ALPHA       = string.ascii_lowercase
_ASPECT      = 0.5
_SYMMETRY    = 8

_TITLE_DELAY  = 0.08   # s/char — title typewriter
_FLASH_SETTLE = 0.5    # pause after typing before flash
_FLASH_OFF    = 0.35   # dim duration of flash
_FLASH_ON     = 0.45   # bold duration of flash
_FLASH_PAUSE  = 0.4    # settle after flash before fill begins
_BUILD_STEPS = 80      # reveal batches
_BUILD_DELAY = 0.05    # s/batch  →  ~4 s total
_HOLD        = 3.0     # hold before prompt appears

_GUST_MIN    = 0.06
_GUST_MAX    = 0.28
_FADE_DUR    = 0.07
_PAUSE_MIN   = 0.12
_PAUSE_MAX   = 0.52

_SEED_LINGER = 2.5     # s seeds remain after wipe
_PROMPT      = "[ any key ]"


# ── Public entry ──────────────────────────────────────────────

def play() -> None:
    curses.wrapper(_run)


def _run(stdscr) -> None:
    scr.init_screen(stdscr)
    h, w = stdscr.getmaxyx()

    cy = h // 2
    cx = w // 2
    rx = w // 2 - 2
    ry = h // 2 - 1

    stdscr.erase()

    # 1. Type title — bold, centred, character by character
    title_col  = cx - len(_TITLE) // 2
    title_cells = {}
    for i, ch in enumerate(_TITLE):
        pos = (cy, title_col + i)
        title_cells[pos] = (ch, True, False)
        scr.addch(stdscr, cy, title_col + i, ch, bold=True)
        stdscr.refresh()
        time.sleep(_TITLE_DELAY)

    # 2. Gentle flash — title alone on empty screen
    time.sleep(_FLASH_SETTLE)
    scr.addstr(stdscr, cy, title_col, _TITLE, dim=True)
    stdscr.refresh()
    time.sleep(_FLASH_OFF)
    scr.addstr(stdscr, cy, title_col, _TITLE, bold=True)
    stdscr.refresh()
    time.sleep(_FLASH_PAUSE)

    # 3. Build fill around the title (no erase — title stays)
    fill = _build_fill(h, w, cy, cx, rx, ry, set(title_cells))
    _phase_build(stdscr, fill, cy, cx, rx, ry)

    # 4. Hold, then prompt
    time.sleep(_HOLD)
    prompt_row = h - 3
    prompt_col = max(0, (w - len(_PROMPT)) // 2)
    scr.addstr(stdscr, prompt_row, prompt_col, _PROMPT, dim=True)
    stdscr.refresh()

    # Wait for any key
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)

    # Erase prompt before wipe
    scr.addstr(stdscr, prompt_row, prompt_col, " " * len(_PROMPT))
    stdscr.refresh()
    time.sleep(0.3)

    # 5. Wipe — spare one cell per seed letter
    all_cells = {**fill, **title_cells}
    survivors = _pick_survivors(all_cells)
    _phase_wipe(stdscr, all_cells, survivors, cy, cx, rx, ry)

    # 6. Seeds linger, then screen clears
    time.sleep(_SEED_LINGER)
    stdscr.erase()
    stdscr.refresh()
    time.sleep(0.4)


# ── Geometry ──────────────────────────────────────────────────

def _r_theta(row, col, cy, cx, rx, ry):
    """Return (r_norm, theta_sym, ok)."""
    dx = col - cx
    dy = row - cy
    r  = math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2) if (rx and ry) else 0.0
    if r > 1.0:
        return 0.0, 0.0, False
    theta  = math.atan2(dy, dx * _ASPECT) % (2 * math.pi)
    sector = (2 * math.pi) / _SYMMETRY
    t      = theta % sector
    if t > sector / 2:
        t = sector - t
    return r, t / (sector / 2), True


def _letter(row, col):
    """Deterministic a-z letter for a grid cell."""
    return _ALPHA[(row * 7 + col * 13) % 26]


def _char(r, theta_sym, row, col):
    """Map geometry → (char, bold, dim). All fill is a-z; @ and * anchor the structure."""
    ch         = _letter(row, col)
    on_spoke   = theta_sym < 0.13
    near_spoke = theta_sym < 0.26
    ring_phase = (r * 6.0) % 1.0
    on_ring    = ring_phase < 0.20
    near_ring  = ring_phase < 0.38

    # Centre seed
    if r < 0.04:
        return "@", True, False

    # Petal — spoke × ring intersection
    if on_spoke and on_ring:
        return "*", r < 0.60, r >= 0.60

    # Spoke / ring arcs — a-z letter, brightness by radius
    if on_spoke or on_ring:
        if r < 0.28:   return ch, True,  False
        elif r < 0.58: return ch, False, False
        else:          return ch, False, True

    # Secondary detail
    if near_spoke and near_ring:
        return ch, False, r >= 0.45

    # Fill
    if r < 0.28:   return ch, False, False
    elif r < 0.60: return ch, False, True
    else:          return ch, False, True


# ── Grid ──────────────────────────────────────────────────────

def _build_fill(h, w, cy, cx, rx, ry, protected):
    """Build fill grid, skipping protected (title) positions."""
    grid = {}
    for row in range(h):
        for col in range(w):
            if (row, col) in protected:
                continue
            r, theta_sym, ok = _r_theta(row, col, cy, cx, rx, ry)
            if not ok:
                continue
            ch, bold, dim = _char(r, theta_sym, row, col)
            grid[(row, col)] = (ch, bold, dim)
    return grid


# ── Build phase ───────────────────────────────────────────────

def _phase_build(stdscr, grid, cy, cx, rx, ry):
    """Reveal fill centre-outward without erasing (title stays drawn)."""
    cells = sorted(
        grid.items(),
        key=lambda item: math.sqrt(
            ((item[0][1] - cx) / rx) ** 2 +
            ((item[0][0] - cy) / ry) ** 2
        )
    )
    batch = max(1, len(cells) // _BUILD_STEPS)
    for i, ((row, col), (ch, bold, dim)) in enumerate(cells):
        scr.addch(stdscr, row, col, ch, bold=bold, dim=dim)
        if i % batch == 0:
            stdscr.refresh()
            time.sleep(_BUILD_DELAY)
    stdscr.refresh()


# ── Survivor selection ────────────────────────────────────────

def _pick_survivors(all_cells):
    """One randomly chosen cell per unique letter of _TITLE."""
    by_letter = {}
    for pos, (ch, bold, dim) in all_cells.items():
        if ch in _SEEDS:
            by_letter.setdefault(ch, []).append(pos)
    survivors = set()
    for letter in _SEEDS:
        candidates = by_letter.get(letter, [])
        if candidates:
            survivors.add(random.choice(candidates))
    return survivors


# ── Wipe phase ────────────────────────────────────────────────

def _phase_wipe(stdscr, all_cells, survivors, cy, cx, rx, ry):
    """Gust wipe sparing survivors. Survivors rendered dim after."""
    scored = []
    for pos, cell_data in all_cells.items():
        if pos in survivors:
            continue
        row, col = pos
        r = math.sqrt(((col - cx) / rx) ** 2 + ((row - cy) / ry) ** 2)
        scored.append((r * 0.55 + random.random() * 0.45, pos, cell_data))
    scored.sort(key=lambda x: x[0], reverse=True)
    cells = [(pos, data) for _, pos, data in scored]

    n, erased = len(cells), 0
    while erased < n:
        remaining = n - erased
        size = max(2, min(remaining,
                          int(remaining * random.uniform(_GUST_MIN, _GUST_MAX))))
        gust = cells[erased : erased + size]

        for (row, col), (ch, bold, dim) in gust:
            scr.addch(stdscr, row, col, ch, bold=False, dim=True)
        stdscr.refresh()
        time.sleep(_FADE_DUR)

        for (row, col), cell_data in gust:
            scr.addch(stdscr, row, col, " ")
        stdscr.refresh()
        erased += size
        time.sleep(random.uniform(_PAUSE_MIN, _PAUSE_MAX))

    # Draw survivors dim — the seeds
    for pos in survivors:
        ch, bold, dim = all_cells[pos]
        scr.addch(stdscr, pos[0], pos[1], ch, dim=True)
    stdscr.refresh()
