# screen.py
# Shared curses utilities. Monochrome-first — no color pairs for level 1.
# Later levels can call curses.start_color() and extend as needed.

import curses


def init_screen(stdscr) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.nodelay(True)


def get_key(stdscr) -> str:
    try:
        key = stdscr.get_wch()
    except curses.error:
        return ""
    if isinstance(key, int):
        mapping = {
            curses.KEY_UP:        "UP",
            curses.KEY_DOWN:      "DOWN",
            curses.KEY_LEFT:      "LEFT",
            curses.KEY_RIGHT:     "RIGHT",
            curses.KEY_BACKSPACE: "BACKSPACE",
            27:                   "ESC",
        }
        return mapping.get(key, "")
    return str(key)


def addstr(win, y: int, x: int, text: str,
           bold: bool = False, dim: bool = False) -> None:
    try:
        win.addstr(y, x, text, _attr(bold, dim))
    except curses.error:
        pass


def addch(win, y: int, x: int, ch: str,
          bold: bool = False, dim: bool = False) -> None:
    try:
        win.addch(y, x, ch, _attr(bold, dim))
    except curses.error:
        pass


def _attr(bold: bool, dim: bool) -> int:
    if bold:
        return curses.A_BOLD
    if dim:
        return curses.A_DIM
    return curses.A_NORMAL
