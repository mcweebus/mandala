# levels/l01_archaea/view.py
# Curses rendering for the archaebacteria level.
# Phase 1 (nav): black screen, three dim options, one warm.
# Phase 2 (catch): ASCII invaders — compounds rise from vent, player at top.
# Monochrome only.

import screen as scr
from . import world as w
from . import text as txt


# ── Navigation view ───────────────────────────────────────────
def draw_nav(stdscr, ls: w.LevelState, msg: str = "") -> None:
    stdscr.erase()
    h, _ = stdscr.getmaxyx()

    if msg:
        _draw_centered(stdscr, h // 2, msg, dim=True)

    warmer = w.nav_warmer_direction(ls)
    _draw_nav_options(stdscr, h, warmer)
    stdscr.refresh()


def _draw_nav_options(stdscr, h: int, warmer: str) -> None:
    _, sw = stdscr.getmaxyx()
    labels = [
        ("left",    "< left"),
        ("forward", "^ forward"),
        ("right",   "> right"),
    ]
    gap = 4
    total_w = sum(len(lbl) for _, lbl in labels) + gap * (len(labels) - 1)
    x = max(0, (sw - total_w) // 2)
    row = h - 3

    for key, lbl in labels:
        is_warm = (key == warmer)
        scr.addstr(stdscr, row, x, lbl, bold=is_warm, dim=not is_warm)
        x += len(lbl) + gap


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
    scr.addstr(stdscr, h - 1, 2, "< > to move", dim=True)
    stdscr.refresh()


# ── Sink animation ────────────────────────────────────────────
def draw_sink(stdscr, ls: w.LevelState, msg: str) -> None:
    stdscr.erase()
    h, _ = stdscr.getmaxyx()
    _draw_centered(stdscr, h // 2, msg, dim=True)
    count_str = f"{ls.dead_count + 1} of {w.WIN_DEAD}"
    _draw_centered(stdscr, h // 2 + 2, count_str, dim=True)
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
