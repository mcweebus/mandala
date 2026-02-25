# welcome.py
# Title screen. Shown once at first launch.
#
# Sequence:
#   1. "mandala" types itself out, bold, centred in the upper third.
#   2. Two flavor lines appear dim below, one at a time.
#   3. A faint prompt settles near the bottom.
#   4. Any key → mandala wipe dissolves the screen into level 1.
#
# Tone: lowercase, no exclamation points. the writing is the world noticing itself.

import curses
import time

import screen as scr
from wipe import play_mandala_wipe

_TITLE = "mandala"

_LINES = []

_CHAR_DELAY   = 0.08   # seconds per character — title typewriter
_FILL_DELAY   = 0.03   # seconds per character — body typewriter
_LINE_PAUSE   = 0.7    # pause after each body line finishes
_SETTLE_PAUSE = 1.4    # silence before the prompt appears
_PROMPT       = "[ any key ]"


def play() -> None:
    """Show the title screen and dissolve with the mandala wipe."""
    curses.wrapper(_wrapped)


def _wrapped(stdscr) -> None:
    scr.init_screen(stdscr)
    h, w = stdscr.getmaxyx()
    stdscr.erase()

    title_row  = max(2, h // 3)
    body_row   = title_row + 3
    prompt_row = h - 3

    # Title — bold, centred, typed character by character
    title_col = max(0, (w - len(_TITLE)) // 2)
    for i, ch in enumerate(_TITLE):
        scr.addch(stdscr, title_row, title_col + i, ch, bold=True)
        stdscr.refresh()
        time.sleep(_CHAR_DELAY)

    time.sleep(_LINE_PAUSE)

    # Flavor lines — dim, centred, typed one line at a time
    row = body_row
    for line in _LINES:
        if line:
            cx = max(0, (w - len(line)) // 2)
            for j, ch in enumerate(line):
                scr.addch(stdscr, row, cx + j, ch, dim=True)
                stdscr.refresh()
                time.sleep(_FILL_DELAY)
            time.sleep(_LINE_PAUSE)
        row += 1

    time.sleep(_SETTLE_PAUSE)

    # Prompt — very dim, centred
    prompt_col = max(0, (w - len(_PROMPT)) // 2)
    scr.addstr(stdscr, prompt_row, prompt_col, _PROMPT, dim=True)
    stdscr.refresh()

    # Wait for any key (switch to blocking just for this)
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)

    # Dissolve into level 1
    play_mandala_wipe(stdscr)
