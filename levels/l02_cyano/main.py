# levels/l02_cyano/main.py
# Level 2 — Cyanobacteria.
# Two phases: ascend (rise 10 steps to the surface) then bloom (spread mat, build O2).
# First level to use color. Light enters the world.

import curses
import random
import time

import screen as scr
from state import CarryState
from . import world, view
from . import text as txt

TICK_INTERVAL  = 0.15    # seconds between bloom ticks
FRAME_INTERVAL = 0.033   # ~30 fps
MSG_DURATION   = 4.0     # seconds a message stays visible


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

    while True:
        now = time.monotonic()

        # ── Bloom tick ────────────────────────────────────────
        if ls.phase == "bloom" and now - last_tick >= TICK_INTERVAL:
            world.bloom_tick(ls)

            if ls.won:
                return _dissolve(stdscr, ls, carry)

            # Coverage threshold messages (trigger once each)
            cov_pct = int(world.get_coverage(ls) * 100)
            for threshold, pool in [
                (5,  txt.BLOOM_5),
                (20, txt.BLOOM_20),
                (50, txt.BLOOM_50),
            ]:
                if cov_pct >= threshold and threshold not in ls.coverage_msgs_shown:
                    ls.coverage_msgs_shown.add(threshold)
                    msg, msg_at = random.choice(pool), now
                    break

            last_tick = now

        # ── Render ────────────────────────────────────────────
        if now - last_frame >= FRAME_INTERVAL:
            display_msg = msg if (now - msg_at <= MSG_DURATION) else ""
            if ls.phase == "ascend":
                view.draw_ascend(stdscr, ls, display_msg)
            else:
                view.draw_bloom(stdscr, ls, display_msg)
            last_frame = now

        # ── Input ─────────────────────────────────────────────
        key = scr.get_key(stdscr)

        if ls.phase == "ascend":
            if key in ("w", "UP"):
                flavor = world.ascend_step(ls)
                msg, msg_at = flavor, now
                if ls.depth == 0:
                    ls.phase = "bloom"

        elif ls.phase == "bloom":
            if key in ("w", "UP"):
                world.bloom_move(ls, -1, 0)
            elif key in ("s", "DOWN"):
                world.bloom_move(ls, 1, 0)
            elif key in ("a", "LEFT"):
                world.bloom_move(ls, 0, -1)
            elif key in ("d", "RIGHT"):
                world.bloom_move(ls, 0, 1)

        curses.napms(10)


def _dissolve(stdscr, ls: world.LevelState, carry: CarryState) -> CarryState:
    # Win beat — green, 3 seconds
    view.draw_win(stdscr, txt.WIN_MESSAGE)
    curses.napms(3000)

    # Dissolution — one line at a time
    for line in txt.DISSOLVE_LINES:
        view.draw_dissolve_line(stdscr, line)
        curses.napms(700)

    # Final stillness
    stdscr.erase()
    h, sw = stdscr.getmaxyx()
    cx = max(0, (sw - len(txt.DISSOLVED)) // 2)
    scr.addstr(stdscr, h // 2, cx, txt.DISSOLVED, dim=True)
    stdscr.refresh()
    curses.napms(3000)

    # Carry out
    data = world.serialize_for_carry(ls)
    carry.substrate["cyano"] = data
    carry.origin_x = data["origin_x"]
    carry.origin_y = data["origin_y"]
    carry.dissolved.append("cyano \u2014 the light changed everything")
    return carry
