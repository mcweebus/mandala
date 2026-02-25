# levels/l01_archaea/view.py
# Curses rendering for the archaebacteria level.
# Phase 1 (nav): three vertical panels, warm direction slightly brighter.
# Phase 2 (catch): archaea body moves at top; compounds rise from vent.
#   Body segments dim = not yet collected, bright = absorbed.
#   On completion the body floats to the bottom and settles as dim sediment.
# Monochrome only.

import screen as scr
from . import world as w
from . import text as txt

_FILL_CHAR = "."


# ── Navigation view ───────────────────────────────────────────
def draw_nav(stdscr, ls: w.LevelState, msg: str = "") -> None:
    stdscr.erase()
    h, sw = stdscr.getmaxyx()

    panel_w = sw // 3
    warmer  = w.nav_warmer_direction(ls)
    prox    = w.nav_proximity(ls)

    panels = [
        ("left",    0,           panel_w),
        ("forward", panel_w,     panel_w * 2),
        ("right",   panel_w * 2, sw),
    ]

    for direction, x0, x1 in panels:
        _fill_panel(stdscr, h, x0, x1, direction == warmer, prox)

    # Faint vertical dividers
    for row in range(h):
        scr.addch(stdscr, row, panel_w - 1,     "|", dim=True)
        scr.addch(stdscr, row, panel_w * 2 - 1, "|", dim=True)

    # Key hints — barely visible at bottom of each panel
    hint_row = h - 2
    scr.addch(stdscr, hint_row, panel_w // 2,                         "a", dim=True)
    scr.addch(stdscr, hint_row, panel_w + panel_w // 2,               "w", dim=True)
    scr.addch(stdscr, hint_row, panel_w * 2 + (sw - panel_w * 2) // 2, "d", dim=True)

    if msg:
        _draw_centered(stdscr, h // 2, msg, dim=True)

    stdscr.refresh()


def _fill_panel(stdscr, h: int, x0: int, x1: int,
                is_warm: bool, prox: float) -> None:
    for row in range(1, h - 2):
        for col in range(x0 + 1, x1 - 1):
            if (row * 17 + col * 11) % 13 == 0:
                if is_warm:
                    bold = prox > 0.60
                    dim  = prox < 0.20
                    scr.addch(stdscr, row, col, _FILL_CHAR, bold=bold, dim=dim)
                else:
                    scr.addch(stdscr, row, col, _FILL_CHAR, dim=True)


# ── Catch view ────────────────────────────────────────────────
_ARENA_TOP = 2

def draw_catch(stdscr, ls: w.LevelState, msg: str = "") -> None:
    stdscr.erase()
    h, sw = stdscr.getmaxyx()

    arena_left = max(0, (sw - w.CATCH_COLS) // 2)
    arena_h    = min(w.CATCH_ROWS, h - 5)

    # HUD — settled count left, remaining compounds right
    settled_str = f"settled: {ls.dead_count}/{w.WIN_DEAD}"
    needed      = [c for c in w.COMPOUNDS if c not in ls.collected]
    needs_str   = "needs: " + " ".join(
        txt.COMPOUND_DISPLAY.get(c, c) for c in needed
    ) if needed else "complete"
    scr.addstr(stdscr, 0, 2, settled_str)
    scr.addstr(stdscr, 0, sw - len(needs_str) - 2, needs_str, bold=bool(needed))

    # Settled bodies — accumulate at the bottom row as dim sediment
    bottom_row = _ARENA_TOP + arena_h - 1
    for body in ls.settled:
        _draw_archaea_body(stdscr, bottom_row, arena_left + body.x,
                           set(w.COMPOUNDS), dim=True)

    # Vent marker (may be overlaid by sediment, which is intentional)
    scr.addch(stdscr, bottom_row, arena_left + w.CATCH_COLS // 2, "^", dim=True)

    # Active or floating archaea body
    if ls.floating:
        float_row = _ARENA_TOP + min(int(ls.float_y), arena_h - 1)
        float_col = arena_left + int(ls.float_x)
        # Fully lit but not bold — dimming as it falls
        _draw_archaea_body(stdscr, float_row, float_col, set(w.COMPOUNDS))
    else:
        _draw_archaea_body(stdscr, _ARENA_TOP, arena_left + ls.catch_px, ls.collected)

    # Rising compounds — bright if still needed, dim if already have it
    for s in ls.sprites:
        if 0 < s.y < arena_h:
            ch        = txt.COMPOUND_DISPLAY.get(s.kind, "?")
            is_needed = s.kind not in ls.collected
            scr.addch(stdscr, _ARENA_TOP + s.y, arena_left + s.x,
                      ch, bold=is_needed, dim=not is_needed)

    if msg:
        scr.addstr(stdscr, h - 2, 2, msg, dim=True)
    scr.addstr(stdscr, h - 1, 2, "a d to move", dim=True)
    stdscr.refresh()


def _draw_archaea_body(stdscr, row: int, col: int,
                       collected: set,
                       bold: bool = False, dim: bool = False) -> None:
    """Draw the archaea body centered on col (the @ nucleus).

    BODY_LEFT extends left from col, BODY_RIGHT extends right.
    Each segment: bright/bold if its compound is in collected, dim if not.
    The dim/bold overrides apply when the body is settled (dim=True)
    or when a full-brightness override is wanted (bold=True).
    """
    h, sw = stdscr.getmaxyx()

    def _put(r: int, c: int, ch: str, seg_bold: bool, seg_dim: bool) -> None:
        if 0 <= r < h and 0 <= c < sw:
            scr.addch(stdscr, r, c, ch, bold=seg_bold, dim=seg_dim)

    def _seg_attr(compound: str) -> tuple[bool, bool]:
        if dim:
            return False, True
        if bold:
            return True, False
        collected_flag = compound in collected
        return collected_flag, not collected_flag

    # Left arm — drawn from nearest to farthest
    for i, (compound, ch) in enumerate(w.BODY_LEFT):
        seg_bold, seg_dim = _seg_attr(compound)
        _put(row, col - 1 - i, ch, seg_bold, seg_dim)

    # Nucleus
    nuc_bold = bold or (not dim and bool(collected))
    _put(row, col, "@", nuc_bold, dim)

    # Right arm
    for i, (compound, ch) in enumerate(w.BODY_RIGHT):
        seg_bold, seg_dim = _seg_attr(compound)
        _put(row, col + 1 + i, ch, seg_bold, seg_dim)


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
