# levels/l03_fungus/view.py
# Curses rendering for the fungus level. Terminal, richer than l01/l02.
# Phase 1 (germinate): dark substrate, player at origin, text.
# Phase 2 (network): box-drawing network chars for mycelium; soil meter HUD.

import curses
import screen as scr
from . import world as w

# ── Color pairs ────────────────────────────────────────────────
CP_WHITE  = 1   # mycelium network
CP_GREEN  = 2   # soil
CP_YELLOW = 3   # organic matter
CP_CYAN   = 4   # HUD meter


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_WHITE,  curses.COLOR_WHITE,  -1)
    curses.init_pair(CP_GREEN,  curses.COLOR_GREEN,  -1)
    curses.init_pair(CP_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_CYAN,   curses.COLOR_CYAN,   -1)


# ── Color helpers ──────────────────────────────────────────────
def _cattr(pair: int, bold: bool = False, dim: bool = False) -> int:
    attr = curses.color_pair(pair)
    if bold:
        attr |= curses.A_BOLD
    if dim:
        attr |= curses.A_DIM
    return attr


def _cch(win, y: int, x: int, ch: str,
         pair: int, bold: bool = False, dim: bool = False) -> None:
    try:
        win.addstr(y, x, ch, _cattr(pair, bold, dim))
    except curses.error:
        pass


def _cstr(win, y: int, x: int, text: str,
          pair: int, bold: bool = False, dim: bool = False) -> None:
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


# ── Network character map ──────────────────────────────────────
# key: (N, S, E, W) neighbor connectivity as bools
_NET_CHARS = {
    (False, False, False, False): "\u00b7",  # ·  isolated
    (False, False, False, True):  "\u2574",  # ╴  W
    (False, False, True,  False): "\u2576",  # ╶  E
    (False, False, True,  True):  "\u2500",  # ─  EW
    (False, True,  False, False): "\u2577",  # ╷  S
    (False, True,  False, True):  "\u2510",  # ┐  SW
    (False, True,  True,  False): "\u250c",  # ┌  SE
    (False, True,  True,  True):  "\u252c",  # ┬  SEW
    (True,  False, False, False): "\u2575",  # ╵  N
    (True,  False, False, True):  "\u2518",  # ┘  NW
    (True,  False, True,  False): "\u2514",  # └  NE
    (True,  False, True,  True):  "\u2534",  # ┴  NEW
    (True,  True,  False, False): "\u2502",  # │  NS
    (True,  True,  False, True):  "\u2524",  # ┤  NSW
    (True,  True,  True,  False): "\u251c",  # ├  NSE
    (True,  True,  True,  True):  "\u253c",  # ┼  NSEW
}


def _is_net(grid, y: int, x: int) -> bool:
    if 0 <= y < w.WORLD_H and 0 <= x < w.WORLD_W:
        return grid[y][x] in (w.MYCELIUM, w.SOIL)
    return False


def _net_char(grid, y: int, x: int) -> str:
    key = (
        _is_net(grid, y - 1, x),  # N
        _is_net(grid, y + 1, x),  # S
        _is_net(grid, y, x + 1),  # E
        _is_net(grid, y, x - 1),  # W
    )
    return _NET_CHARS.get(key, "\u00b7")


# ── Arena offset ───────────────────────────────────────────────
_ARENA_TOP = 2


# ── Germinate view ─────────────────────────────────────────────
def draw_germinate(stdscr, ls: w.LevelState, msg: str = "") -> None:
    stdscr.erase()
    h, sw = stdscr.getmaxyx()
    arena_left = max(0, (sw - w.WORLD_W) // 2)

    for ry in range(w.WORLD_H):
        for rx in range(w.WORLD_W):
            sr = _ARENA_TOP + ry
            sc = arena_left + rx
            if sr >= h - 2 or sc >= sw:
                continue
            tile = ls.grid[ry][rx]
            if tile == w.ORGANIC:
                _cch(stdscr, sr, sc, "o", CP_YELLOW, dim=True)
            elif (ry * 17 + rx * 11) % 19 == 0:
                scr.addch(stdscr, sr, sc, ".", dim=True)

    # Player (spore)
    sr = _ARENA_TOP + ls.py
    sc = arena_left + ls.px
    if 0 <= sr < h - 2 and 0 <= sc < sw:
        scr.addch(stdscr, sr, sc, "@", bold=True)

    if msg:
        _draw_centered(stdscr, h // 2, msg, dim=True)

    scr.addstr(stdscr, h - 2, 2, "w / \u2191 to extend", dim=True)
    stdscr.refresh()


# ── Network view ───────────────────────────────────────────────
def draw_network(stdscr, ls: w.LevelState, msg: str = "") -> None:
    stdscr.erase()
    h, sw = stdscr.getmaxyx()
    arena_left = max(0, (sw - w.WORLD_W) // 2)

    # HUD — soil progress meter
    progress = min(1.0, w.get_soil_fraction(ls) / w.WIN_SOIL_FRAC)
    bar_w    = 20
    filled   = int(progress * bar_w)
    bar      = "\u2588" * filled + "\u2591" * (bar_w - filled)
    hud_str  = f"soil [{bar}] {int(progress * 100)}%"
    _cstr(stdscr, 0, 2, hud_str, CP_GREEN)

    # Arena
    for ry in range(w.WORLD_H):
        for rx in range(w.WORLD_W):
            sr = _ARENA_TOP + ry
            sc = arena_left + rx
            if sr >= h - 2 or sc >= sw:
                continue

            is_player = (ry == ls.py and rx == ls.px)
            tile      = ls.grid[ry][rx]

            if is_player:
                scr.addch(stdscr, sr, sc, "@", bold=True)
            elif tile == w.SOIL:
                ch = _net_char(ls.grid, ry, rx)
                _cch(stdscr, sr, sc, ch, CP_GREEN, dim=True)
            elif tile == w.MYCELIUM:
                ch = _net_char(ls.grid, ry, rx)
                _cch(stdscr, sr, sc, ch, CP_WHITE)
            elif tile == w.ORGANIC:
                _cch(stdscr, sr, sc, "o", CP_YELLOW, dim=True)
            elif (ry * 17 + rx * 11) % 19 == 0:
                scr.addch(stdscr, sr, sc, ".", dim=True)

    if msg:
        scr.addstr(stdscr, h - 2, 2, msg, dim=True)

    scr.addstr(stdscr, h - 1, 2, "wasd / arrows to move", dim=True)
    stdscr.refresh()


# ── Win / dissolve ─────────────────────────────────────────────
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
