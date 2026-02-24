# levels/l01_archaea/main.py
# Level 1 — Archaebacteria.
# Game loop, curses lifecycle, dissolution ceremony.

import curses
import time
import random

import screen as scr
from state import CarryState
from . import world, view
from . import text as txt

TICK_INTERVAL = 0.15   # seconds between world ticks
FRAME_INTERVAL = 0.033  # ~30fps


def run(carry: CarryState) -> CarryState:
    return curses.wrapper(_run_wrapped, carry)


def _run_wrapped(stdscr, carry: CarryState) -> CarryState:
    scr.init_screen(stdscr)
    while True:
        result = _play(stdscr, carry)
        if result is not None:
            return result
        # death — brief message, regenerate
        view.draw_death(stdscr, txt.DEATH_MSG)
        curses.napms(1800)


def _play(stdscr, carry: CarryState):
    ls  = world.generate_map()
    msg = txt.ENTER
    last_tick  = time.monotonic()
    last_frame = time.monotonic()

    while True:
        now = time.monotonic()

        # ── World tick ──────────────────────────────────────
        if now - last_tick >= TICK_INTERVAL:
            tick_msg = world.world_tick(ls)
            if tick_msg and not msg:
                msg = tick_msg
            last_tick = now

            if ls.energy <= 0:
                return None   # signal death

            if ls.won:
                return _dissolve(stdscr, ls, carry)

        # ── Render ──────────────────────────────────────────
        if now - last_frame >= FRAME_INTERVAL:
            view.draw(stdscr, ls, msg)
            msg = ""
            last_frame = now

        # ── Input ───────────────────────────────────────────
        key = scr.get_key(stdscr)
        if key == "UP":    m = world.move_player(ls, 0, -1)
        elif key == "DOWN":  m = world.move_player(ls, 0,  1)
        elif key == "LEFT":  m = world.move_player(ls, -1, 0)
        elif key == "RIGHT": m = world.move_player(ls,  1, 0)
        else:                m = ""
        if m:
            msg = m

        curses.napms(10)


def _dissolve(stdscr, ls: world.LevelState, carry: CarryState) -> CarryState:
    # Win screen
    view.draw_win(stdscr, ls, txt.WIN_MESSAGE)
    curses.napms(2500)

    # Dissolution ceremony — tiles convert back to rock one by one
    positions = world.conditioned_positions(ls)
    dissolve_lines = txt.DISSOLVE_LINES

    for i, (x, y) in enumerate(positions):
        ls.grid[y][x] = world.ROCK
        step_msg = dissolve_lines[i % len(dissolve_lines)]
        view.draw_dissolve(stdscr, ls, step_msg)
        curses.napms(70)

    # Final stillness
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    cx = max(0, (width - len(txt.DISSOLVED)) // 2)
    scr.addstr(stdscr, height // 2, cx, txt.DISSOLVED, dim=True)
    stdscr.refresh()
    curses.napms(3000)

    # Record to carry
    data = world.serialize_for_carry(ls)
    carry.substrate["archaea"] = data
    carry.origin_x = data["origin_x"]
    carry.origin_y = data["origin_y"]
    carry.dissolved.append("archaea — the substrate holds what was made here")

    return carry
