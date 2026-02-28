# levels/l03_fungus/main.py
# Level 3 — Fungus.
# Two phases: germinate (spore senses substrate, 4 steps) then network (mycelium grows).
# Network topology rendered with box-drawing chars. Still underground.

import curses
import random
import time

import screen as scr
from state import CarryState
from . import world, view
from . import text as txt

TICK_INTERVAL      = 0.15    # seconds between network ticks
FRAME_INTERVAL     = 0.033   # ~30 fps
MSG_DURATION       = 8.0     # seconds a message stays visible
GERM_STEP_INTERVAL = 1.5     # minimum seconds between germinate steps


def run(carry: CarryState) -> CarryState:
    return curses.wrapper(_run_wrapped, carry)


def _run_wrapped(stdscr, carry: CarryState) -> CarryState:
    scr.init_screen(stdscr)
    view.init_colors()
    ls = world.generate_state(carry)
    return _play(stdscr, ls, carry)


def _play(stdscr, ls: world.LevelState, carry: CarryState) -> CarryState:
    msg        = ""
    msg_at     = 0.0
    last_tick  = time.monotonic()
    last_frame = time.monotonic()
    last_germ  = 0.0

    while True:
        now = time.monotonic()

        # ── Network tick ──────────────────────────────────────
        if ls.phase == "network" and now - last_tick >= TICK_INTERVAL:
            world.network_tick(ls)

            if ls.won:
                return _dissolve(stdscr, ls, carry)

            # Soil progress threshold messages
            progress_pct = int(world.get_soil_fraction(ls) / world.WIN_SOIL_FRAC * 100)
            for threshold, pool in [
                (25, txt.SOIL_25),
                (50, txt.SOIL_50),
                (75, txt.SOIL_75),
            ]:
                if progress_pct >= threshold and threshold not in ls.soil_msgs_shown:
                    ls.soil_msgs_shown.add(threshold)
                    msg, msg_at = random.choice(pool), now
                    break

            last_tick = now

        # ── Render ────────────────────────────────────────────
        if now - last_frame >= FRAME_INTERVAL:
            display_msg = msg if (now - msg_at <= MSG_DURATION) else ""
            if ls.phase == "germinate":
                view.draw_germinate(stdscr, ls, display_msg)
            else:
                view.draw_network(stdscr, ls, display_msg)
            last_frame = now

        # ── Input ─────────────────────────────────────────────
        key = scr.get_key(stdscr)

        if ls.phase == "germinate":
            if key in ("w", "UP") and now - last_germ >= GERM_STEP_INTERVAL:
                flavor = world.germinate_step(ls)
                msg, msg_at = flavor, now
                last_germ = now
                if ls.germ_step == 0:
                    ls.phase = "network"

        elif ls.phase == "network":
            if key in ("w", "UP"):
                world.player_move(ls, -1, 0)
            elif key in ("s", "DOWN"):
                world.player_move(ls, 1, 0)
            elif key in ("a", "LEFT"):
                world.player_move(ls, 0, -1)
            elif key in ("d", "RIGHT"):
                world.player_move(ls, 0, 1)

        curses.napms(10)


def _dissolve(stdscr, ls: world.LevelState, carry: CarryState) -> CarryState:
    # Win beat
    view.draw_win(stdscr, txt.WIN_MESSAGE)
    curses.napms(4500)

    # Dissolution — one line at a time
    for line in txt.DISSOLVE_LINES:
        view.draw_dissolve_line(stdscr, line)
        curses.napms(1500)

    # Final stillness
    stdscr.erase()
    h, sw = stdscr.getmaxyx()
    cx = max(0, (sw - len(txt.DISSOLVED)) // 2)
    scr.addstr(stdscr, h // 2, cx, txt.DISSOLVED, dim=True)
    stdscr.refresh()
    curses.napms(5000)

    # Carry out
    data = world.serialize_for_carry(ls)
    carry.substrate["fungus"] = data
    carry.origin_x = data["origin_x"]
    carry.origin_y = data["origin_y"]
    carry.dissolved.append("fungus \u2014 it unmade the boundary between rock and soil")
    return carry
