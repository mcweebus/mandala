# levels/l02_cyano/view.py
# Curses rendering for the cyanobacteria level. First level with color.
# Phase 1 (ascend): vertical cross-section; light zone grows from top.
# Phase 2 (bloom): mat spread across lit grid; O2 meter and coverage counter.

import curses
import screen as scr
from . import world as w

# ── Color pairs ───────────────────────────────────────────────
CP_GREEN  = 1   # colony mat, player
CP_YELLOW = 2   # sunlit water
CP_WHITE  = 3   # O2 bubbles
CP_CYAN   = 4   # O2 meter bar
CP_BLUE   = 5   # dark water background


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_GREEN,  curses.COLOR_GREEN,  -1)
    curses.init_pair(CP_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_WHITE,  curses.COLOR_WHITE,  -1)
    curses.init_pair(CP_CYAN,   curses.COLOR_CYAN,   -1)
    curses.init_pair(CP_BLUE,   curses.COLOR_BLUE,   -1)


# ── Color helpers ─────────────────────────────────────────────
def _cattr(pair: int, bold: bool = False, dim: bool = False) -> int:
    attr = curses.color_pair(pair)
    if bold:
        attr |= curses.A_BOLD
    if dim:
        attr |= curses.A_DIM
    return attr


def _cch(win, y: int, x: int, ch: str, pair: int,
         bold: bool = False, dim: bool = False) -> None:
    try:
        win.addstr(y, x, ch, _cattr(pair, bold, dim))
    except curses.error:
        pass


def _cstr(win, y: int, x: int, text: str, pair: int,
          bold: bool = False, dim: bool = False) -> None:
    try:
        win.addstr(y, x, text, _cattr(pair, bold, dim))
    except curses.error:
        pass


def _draw_centered(stdscr, row: int, text: str,
                   bold: bool = False, dim: bool = False,
                   pair: int = 0) -> None:
    _, sw = stdscr.getmaxyx()
    cx = max(0, (sw - len(text)) // 2)
    if pair:
        _cstr(stdscr, row, cx, text, pair, bold=bold, dim=dim)
    else:
        scr.addstr(stdscr, row, cx, text, bold=bold, dim=dim)


# ── Ascend view ───────────────────────────────────────────────
_ARENA_TOP_ASCEND = 1   # row 0 = HUD

def draw_ascend(stdscr, ls: w.LevelState, msg: str = "") -> None:
    stdscr.erase()
    h, sw = stdscr.getmaxyx()

    arena_h    = h - 3   # top row for HUD, bottom two rows for hints
    arena_top  = _ARENA_TOP_ASCEND
    player_col = sw // 2

    # Light zone grows down from surface; player is at its lower edge.
    # depth=MAX_DEPTH → light_rows=0, player at bottom.
    # depth=0         → light_rows=arena_h-1, player at top.
    light_rows = int((w.MAX_DEPTH - ls.depth) / w.MAX_DEPTH * (arena_h - 1))
    player_row = arena_h - 1 - light_rows   # player rises as light grows

    # Fill arena
    for row in range(arena_h):
        screen_row = arena_top + row
        if screen_row >= h - 2:
            break
        for col in range(sw):
            if row < light_rows:
                # Lit water — denser/brighter near the boundary (lower half)
                if not _is_sparse(row, col):
                    continue
                is_lower_half = row >= light_rows // 2
                ch = "~" if is_lower_half else "\xb7"  # · = U+00B7
                _cch(stdscr, screen_row, col, ch,
                     CP_YELLOW, bold=is_lower_half)
            elif row == player_row:
                pass   # player drawn separately below
            else:
                # Dark water — sparse blue dots
                if _is_sparse(row, col):
                    _cch(stdscr, screen_row, col, ".", CP_BLUE, dim=True)

    # Player
    screen_player_row = arena_top + player_row
    if 0 <= screen_player_row < h - 2:
        _cch(stdscr, screen_player_row, player_col, "@", CP_GREEN, bold=True)

    # HUD — depth counter
    depth_str = f"depth: {ls.depth}"
    scr.addstr(stdscr, 0, 2, depth_str, bold=True)

    if msg:
        _draw_centered(stdscr, h // 2, msg, dim=True)

    scr.addstr(stdscr, h - 2, 2, "w / \u2191 to rise", dim=True)
    stdscr.refresh()


def _is_sparse(row: int, col: int) -> bool:
    return (row * 17 + col * 11) % 13 == 0


# ── Bloom view ────────────────────────────────────────────────
_ARENA_TOP_BLOOM = 2   # rows 0–1 for HUD

def draw_bloom(stdscr, ls: w.LevelState, msg: str = "") -> None:
    stdscr.erase()
    h, sw = stdscr.getmaxyx()

    arena_top  = _ARENA_TOP_BLOOM
    arena_left = max(0, (sw - w.BLOOM_W) // 2)

    # HUD row 0 — O2 meter
    o2_pct  = min(1.0, ls.total_o2 / w.WIN_O2)
    bar_w   = 20
    filled  = int(o2_pct * bar_w)
    bar     = "\u2588" * filled + "\u2591" * (bar_w - filled)
    o2_str  = f"o2 [{bar}] {int(o2_pct * 100)}%"
    _cstr(stdscr, 0, 2, o2_str, CP_CYAN)

    # HUD row 1 — coverage counter (right-aligned)
    cov_pct = int(w.get_coverage(ls) * 100)
    mat_str = f"mat: {cov_pct}%"
    _cstr(stdscr, 1, max(0, sw - len(mat_str) - 2), mat_str, CP_GREEN)

    # Arena — background layer then colony/player
    for ry in range(w.BLOOM_H):
        for rx in range(w.BLOOM_W):
            sr = arena_top + ry
            sc = arena_left + rx
            if sr >= h - 2 or sc >= sw:
                continue

            is_player = (ry == ls.py and rx == ls.px)
            is_colony = ls.colony[ry][rx]
            light_val = ls.light[rx]

            if is_player:
                _cch(stdscr, sr, sc, "@", CP_GREEN, bold=True)
            elif is_colony:
                ch = _colony_char(light_val)
                _cch(stdscr, sr, sc, ch, CP_GREEN)
            elif light_val > 0.3:
                _cch(stdscr, sr, sc, "\xb7", CP_YELLOW, dim=True)
            # else: dark, leave empty

    # Bubbles — drawn last so they float above colony tiles
    for bx, by in ls.bubbles:
        sr = arena_top + by
        sc = arena_left + bx
        if 0 <= sr < h - 2 and 0 <= sc < sw:
            _cch(stdscr, sr, sc, "*", CP_WHITE, bold=True)

    if msg:
        scr.addstr(stdscr, h - 2, 2, msg, dim=True)

    scr.addstr(stdscr, h - 1, 2, "wasd / arrows to move", dim=True)
    stdscr.refresh()


def _colony_char(light_val: float) -> str:
    if light_val > 0.7:
        return "#"
    if light_val > 0.4:
        return "+"
    return "%"


# ── Win / dissolve ────────────────────────────────────────────
def draw_win(stdscr, msg: str) -> None:
    stdscr.erase()
    h, _ = stdscr.getmaxyx()
    _draw_centered(stdscr, h // 2, msg, bold=True, pair=CP_GREEN)
    stdscr.refresh()


def draw_dissolve_line(stdscr, line: str) -> None:
    stdscr.erase()
    h, _ = stdscr.getmaxyx()
    _draw_centered(stdscr, h // 2, line, dim=True)
    stdscr.refresh()
