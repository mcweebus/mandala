# levels/l01_archaea/main.py
# Level 1 — Archaebacteria.
# Two phases: navigate to vent (text adventure), catch compounds (ASCII invaders).
# Each bacterium must absorb all four compound types before it completes.
# On completion the body lights up and floats to the bottom as sediment.
# WIN_DEAD bacteria must settle to finish the level.

import curses
import time

import screen as scr
from state import CarryState
from . import world, view
from . import text as txt

TICK_INTERVAL  = 0.12    # seconds between catch-phase ticks
FRAME_INTERVAL = 0.033   # ~30 fps
MSG_DURATION   = 8.0     # seconds a message stays visible


def run(carry: CarryState) -> CarryState:
    return curses.wrapper(_run_wrapped, carry)


def _run_wrapped(stdscr, carry: CarryState) -> CarryState:
    scr.init_screen(stdscr)
    ls = world.generate_state()
    return _play(stdscr, ls, carry)


def _play(stdscr, ls: world.LevelState, carry: CarryState) -> CarryState:
    msg        = ""
    msg_at     = 0.0
    last_tick  = time.monotonic()
    last_frame = time.monotonic()

    while True:
        now = time.monotonic()

        # ── Catch-phase tick ──────────────────────────────────
        if ls.phase == "catch" and now - last_tick >= TICK_INTERVAL:
            world.catch_tick(ls)

            if ls.won:
                return _dissolve(stdscr, ls, carry)

            # Collision only when the living bacterium is present (not floating)
            if not ls.floating:
                result = world.catch_check_collision(ls)
                if result == "collected":
                    msg, msg_at = txt.CATCH_SUCCESS, now
                elif result == "all_collected":
                    msg, msg_at = txt.ALL_COLLECTED_MSG, now

            last_tick = now

        # ── Render ────────────────────────────────────────────
        if now - last_frame >= FRAME_INTERVAL:
            display_msg = msg if (now - msg_at <= MSG_DURATION) else ""
            if ls.phase == "nav":
                view.draw_nav(stdscr, ls, display_msg)
            else:
                view.draw_catch(stdscr, ls, display_msg)
            last_frame = now

        # ── Input ─────────────────────────────────────────────
        key = scr.get_key(stdscr)

        if ls.phase == "nav":
            if key in ("a", "LEFT"):
                m = world.nav_move(ls, "left")
            elif key in ("d", "RIGHT"):
                m = world.nav_move(ls, "right")
            elif key in ("w", "UP"):
                m = world.nav_move(ls, "forward")
            else:
                m = ""
            if m:
                msg, msg_at = m, now
            if world.nav_arrived(ls):
                ls.phase = "catch"

        elif ls.phase == "catch" and not ls.floating:
            # Disable movement during float — the death animation plays uninterrupted.
            if key in ("a", "LEFT"):
                world.catch_move(ls, -2)
            elif key in ("d", "RIGHT"):
                world.catch_move(ls, 2)

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

    # Carry
    data = world.serialize_for_carry(ls)
    carry.substrate["archaea"] = data
    carry.origin_x = data["origin_x"]
    carry.origin_y = data["origin_y"]
    carry.dissolved.append("archaea — the sediment remembers")
    return carry
