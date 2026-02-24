# levels/l01_archaea/view.py
# Curses rendering for the archaebacteria level.
# Phase 1 (nav): three vertical panels, warm direction slightly brighter.
# Phase 2 (catch): ASCII invaders — compounds rise from vent, player at top.
# Monochrome only.

import screen as scr
from . import world as w
from . import text as txt

_FILL_CHAR = "."


# ── Navigation view ───────────────────────────────────────────
def draw_nav(stdscr, ls: w.LevelState, msg: str = "") -> None:
    stdscr.erase()
    h, sw = stdscr.getmaxyx()

    panel_w = sw // 3
    warmer  = w.nav_warmer_direction(ls)
    prox    = w.nav_proximity(ls)

    panels = [
        ("left",    0,           panel_w),
        ("forward", panel_w,     panel_w * 2),
        ("right",   panel_w * 2, sw),
    ]

    for direction, x0, x1 in panels:
        _fill_panel(stdscr, h, x0, x1, direction == warmer, prox)

    # Faint vertical dividers
    for row in range(h):
        scr.addch(stdscr, row, panel_w - 1,     "|", dim=True)
        scr.addch(stdscr, row, panel_w * 2 - 1, "|", dim=True)

    # Key hints — barely visible at bottom of each panel
    hint_row = h - 2
    scr.addch(stdscr, hint_row, panel_w // 2,                    "a", dim=True)
    scr.addch(stdscr, hint_row, panel_w + panel_w // 2,          "w", dim=True)
    scr.addch(stdscr, hint_row, panel_w * 2 + (sw - panel_w * 2) // 2, "d", dim=True)

    # Atmospheric text centered, overlaid dim
    if msg:
        _draw_centered(stdscr, h // 2, msg, dim=True)

    stdscr.refresh()


def _fill_panel(stdscr, h: int, x0: int, x1: int,
                is_warm: bool, prox: float) -> None:
    """Fill a nav panel with sparse dots. Warm panel is brighter."""
    for row in range(1, h - 2):
        for col in range(x0 + 1, x1 - 1):
            if (row * 17 + col * 11) % 13 == 0:
                if is_warm:
                    bold = prox > 0.60
                    dim  = prox < 0.20
                    scr.addch(stdscr, row, col, _FILL_CHAR, bold=bold, dim=dim)
                else:
                    scr.addch(stdscr, row, col, _FILL_CHAR, dim=True)


# ── Catch view ────────────────────────────────────────────────
_ARENA_TOP = 2

def draw_catch(stdscr, ls: w.LevelState, msg: str = "") -> None:
    stdscr.erase()
    h, sw = stdscr.getmaxyx()

    arena_left = max(0, (sw - w.CATCH_COLS) // 2)
    arena_h    = min(w.CATCH_ROWS, h - 5)

    # HUD
    settled_str = f"settled: {ls.dead_count}/{w.WIN_DEAD}"
    needs_str   = f"needs: {txt.COMPOUND_NAMES.get(ls.target, ls.target)}"
    scr.addstr(stdscr, 0, 2, settled_str)
    scr.addstr(stdscr, 0, sw - len(needs_str) - 2, needs_str, bold=True)

    # Player at top of arena
    scr.addch(stdscr, _ARENA_TOP, arena_left + ls.catch_px, "@", bold=True)

    # Rising compounds
    for s in ls.sprites:
        if 0 <= s.y < arena_h:
            ch = txt.COMPOUND_DISPLAY.get(s.kind, "?")
            is_target = (s.kind == ls.target)
            scr.addch(stdscr, _ARENA_TOP + s.y, arena_left + s.x,
                      ch, bold=is_target, dim=not is_target)

    # Vent at bottom
    vent_row = _ARENA_TOP + arena_h - 1
    scr.addch(stdscr, vent_row, arena_left + w.CATCH_COLS // 2, "^", dim=True)

    if msg:
        scr.addstr(stdscr, h - 2, 2, msg, dim=True)
    scr.addstr(stdscr, h - 1, 2, "a d to move", dim=True)
    stdscr.refresh()


# ── Sink animation ────────────────────────────────────────────
def draw_sink(stdscr, ls: w.LevelState, msg: str) -> None:
    stdscr.erase()
    h, _ = stdscr.getmaxyx()
    _draw_centered(stdscr, h // 2,     msg,                                  dim=True)
    _draw_centered(stdscr, h // 2 + 2, f"{ls.dead_count + 1} of {w.WIN_DEAD}", dim=True)
    stdscr.refresh()


# ── Win / dissolve ────────────────────────────────────────────
def draw_win(stdscr, msg: str) -> None:
    stdscr.erase()
    h, _ = stdscr.getmaxyx()
    _draw_centered(stdscr, h // 2, msg)
    stdscr.refresh()


def draw_dissolve_line(stdscr, line: str) -> None:
    stdscr.erase()
    h, _ = stdscr.getmaxyx()
    _draw_centered(stdscr, h // 2, line, dim=True)
    stdscr.refresh()


# ── Utility ───────────────────────────────────────────────────
def _draw_centered(stdscr, row: int, text: str,
                   bold: bool = False, dim: bool = False) -> None:
    _, sw = stdscr.getmaxyx()
    cx = max(0, (sw - len(text)) // 2)
    scr.addstr(stdscr, row, cx, text, bold=bold, dim=dim)
