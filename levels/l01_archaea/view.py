# levels/l01_archaea/view.py
# Curses rendering for the archaebacteria level.
# Monochrome only — bold, dim, normal. No color.

import screen as scr
from .world import (MAP_W, MAP_H, TILE_DISPLAY, CONDITIONED,
                    LevelState, count_conditioned, WIN_COVERAGE, WIN_BIOMASS)

MAP_LEFT = 2
MAP_TOP  = 2
MSG_ROW  = MAP_TOP + MAP_H + 1
HINT_ROW = MSG_ROW + 1


def draw(stdscr, ls: LevelState, msg: str = "") -> None:
    stdscr.erase()
    _draw_hud(stdscr, ls)
    _draw_map(stdscr, ls)
    if msg:
        scr.addstr(stdscr, MSG_ROW, MAP_LEFT, msg, dim=True)
    scr.addstr(stdscr, HINT_ROW, MAP_LEFT, "arrows: move", dim=True)
    stdscr.refresh()


def _draw_hud(stdscr, ls: LevelState) -> None:
    cond  = count_conditioned(ls)
    total = MAP_W * MAP_H
    pct   = int(100 * cond / total)

    # Coverage progress toward win
    cov_target  = int(WIN_COVERAGE * 100)
    bio_target  = WIN_BIOMASS

    e_bold = ls.energy > 60
    e_dim  = ls.energy < 25

    scr.addstr(stdscr, 0, MAP_LEFT,
               f"energy:{ls.energy:<4}", bold=e_bold, dim=e_dim)
    scr.addstr(stdscr, 0, MAP_LEFT + 14,
               f"biomass:{ls.biomass:<5}", bold=ls.biomass >= bio_target)
    scr.addstr(stdscr, 0, MAP_LEFT + 28,
               f"conditioned:{pct}%/{cov_target}%",
               bold=(pct >= cov_target))


def _draw_map(stdscr, ls: LevelState) -> None:
    for y in range(MAP_H):
        for x in range(MAP_W):
            sx = MAP_LEFT + x
            sy = MAP_TOP  + y
            if x == ls.px and y == ls.py:
                scr.addch(stdscr, sy, sx, "@", bold=True)
            else:
                tile = ls.grid[y][x]
                ch, bold, dim = TILE_DISPLAY.get(tile, (".", False, True))
                scr.addch(stdscr, sy, sx, ch, bold=bold, dim=dim)


def draw_death(stdscr, msg: str) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    cx = max(0, (width - len(msg)) // 2)
    scr.addstr(stdscr, height // 2, cx, msg, dim=True)
    stdscr.refresh()


def draw_win(stdscr, ls: LevelState, msg: str) -> None:
    draw(stdscr, ls)
    height, width = stdscr.getmaxyx()
    cx = max(MAP_LEFT, (width - len(msg)) // 2)
    scr.addstr(stdscr, MAP_TOP + MAP_H // 2, cx, msg, bold=True)
    stdscr.refresh()


def draw_dissolve(stdscr, ls: LevelState, step_msg: str = "") -> None:
    stdscr.erase()
    _draw_map(stdscr, ls)
    if step_msg:
        scr.addstr(stdscr, MSG_ROW, MAP_LEFT, step_msg, dim=True)
    stdscr.refresh()
