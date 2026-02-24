# levels/l01_archaea/world.py
# Pure engine logic. No curses imports.
# Phase 1: navigation via relative heading across a 2D grid.
# Phase 2: catch — compounds rise from vent, player intercepts.

from __future__ import annotations
import random
from dataclasses import dataclass, field
from . import text as txt

# ── Navigation grid ───────────────────────────────────────────
NAV_W = 22
NAV_H = 16

HEADINGS = ["N", "E", "S", "W"]   # clockwise order
HEADING_DELTA = {
    "N": (0, -1),
    "E": (1,  0),
    "S": (0,  1),
    "W": (-1, 0),
}

# ── Catch arena ───────────────────────────────────────────────
CATCH_COLS    = 44
CATCH_ROWS    = 20
SPAWN_INTERVAL = 10    # ticks between new compound spawns
RISE_SPEED    = 1      # rows per tick (toward player)
COMPOUNDS     = ["S", "F", "H", "C"]

# ── Win condition ─────────────────────────────────────────────
WIN_DEAD = 18


# ── State ─────────────────────────────────────────────────────
@dataclass
class CompoundSprite:
    x: int
    y: int
    kind: str


@dataclass
class LevelState:
    # Navigation
    nx:      int  = NAV_W // 2
    ny:      int  = 0
    heading: str  = "S"
    vent_x:  int  = 0
    vent_y:  int  = 0

    # Phase
    phase:   str  = "nav"   # "nav" | "catch"
    first:   bool = True    # True until first bacterium completes nav

    # Catch
    target:     str  = "S"
    sprites:    list = field(default_factory=list)
    catch_px:   int  = CATCH_COLS // 2
    catch_ticks: int = 0

    # Progress
    dead_count: int  = 0
    won:        bool = False


# ── Generation ────────────────────────────────────────────────
def generate_state() -> LevelState:
    # Vent anywhere in the lower two-thirds, full width
    vent_x = random.randint(2, NAV_W - 3)
    vent_y = random.randint(NAV_H // 3, NAV_H - 1)

    # Player starts at center with a random heading — no guaranteed "forward" answer
    heading = random.choice(HEADINGS)

    return LevelState(
        nx=NAV_W // 2,
        ny=NAV_H // 2,
        heading=heading,
        vent_x=vent_x,
        vent_y=vent_y,
        target=random.choice(COMPOUNDS),
    )


# ── Navigation helpers ────────────────────────────────────────
def nav_proximity(ls: LevelState) -> float:
    """0.0 = far from vent, 1.0 = at vent."""
    dist = abs(ls.nx - ls.vent_x) + abs(ls.ny - ls.vent_y)
    return max(0.0, 1.0 - dist / (NAV_W + NAV_H))


def nav_arrived(ls: LevelState) -> bool:
    return ls.nx == ls.vent_x and ls.ny == ls.vent_y


def _turn_left(h: str) -> str:
    return HEADINGS[(HEADINGS.index(h) - 1) % 4]


def _turn_right(h: str) -> str:
    return HEADINGS[(HEADINGS.index(h) + 1) % 4]


def _forward_pos(nx: int, ny: int, heading: str) -> tuple[int, int]:
    dx, dy = HEADING_DELTA[heading]
    return (
        max(0, min(NAV_W - 1, nx + dx)),
        max(0, min(NAV_H - 1, ny + dy)),
    )


def nav_warmer_direction(ls: LevelState) -> str:
    """Return 'left', 'forward', or 'right' — whichever leads closest to vent."""
    def dist_from(nx: int, ny: int) -> int:
        return abs(nx - ls.vent_x) + abs(ny - ls.vent_y)

    fx, fy = _forward_pos(ls.nx, ls.ny, ls.heading)
    lx, ly = _forward_pos(ls.nx, ls.ny, _turn_left(ls.heading))
    rx, ry = _forward_pos(ls.nx, ls.ny, _turn_right(ls.heading))

    options = {
        "forward": dist_from(fx, fy),
        "left":    dist_from(lx, ly),
        "right":   dist_from(rx, ry),
    }
    return min(options, key=options.get)


def nav_move(ls: LevelState, action: str) -> str:
    """Mutate ls. Return flavor text or ''."""
    if action == "left":
        ls.heading = _turn_left(ls.heading)
        return ""
    if action == "right":
        ls.heading = _turn_right(ls.heading)
        return ""
    if action == "forward":
        ls.nx, ls.ny = _forward_pos(ls.nx, ls.ny, ls.heading)
        if nav_arrived(ls):
            return txt.ARRIVE_VENT
        prox = nav_proximity(ls)
        if prox > 0.65:
            return random.choice(txt.ATMOSPHERE_CLOSE)
        if prox > 0.35:
            return random.choice(txt.ATMOSPHERE_MED)
        return random.choice(txt.ATMOSPHERE_FAR)
    return ""


# ── Catch phase ───────────────────────────────────────────────
def catch_tick(ls: LevelState) -> None:
    ls.catch_ticks += 1

    # Spawn a new compound — biased 40% toward target
    if ls.catch_ticks % SPAWN_INTERVAL == 0:
        kind = ls.target if random.random() < 0.4 else random.choice(COMPOUNDS)
        ls.sprites.append(CompoundSprite(
            x=random.randint(0, CATCH_COLS - 1),
            y=CATCH_ROWS - 1,
            kind=kind,
        ))

    # Rise all sprites
    for s in ls.sprites:
        s.y -= RISE_SPEED
    ls.sprites = [s for s in ls.sprites if s.y >= 0]


def catch_check_collision(ls: LevelState) -> str | None:
    """Check if any sprite has reached player row (y == 0). Returns 'caught', 'wrong', or None."""
    result = None
    remaining = []
    for s in ls.sprites:
        if s.y == 0 and abs(s.x - ls.catch_px) <= 1:
            if result is None:
                result = "caught" if s.kind == ls.target else "wrong"
            # sprite consumed regardless
        else:
            remaining.append(s)
    ls.sprites = remaining
    return result


def catch_move(ls: LevelState, dx: int) -> None:
    ls.catch_px = max(0, min(CATCH_COLS - 1, ls.catch_px + dx))


def next_bacterium(ls: LevelState) -> None:
    """Called after a bacterium has sunk. Prepare the next one."""
    ls.dead_count += 1
    ls.first = False
    ls.sprites = []
    ls.catch_ticks = 0
    ls.target = random.choice(COMPOUNDS)
    ls.catch_px = CATCH_COLS // 2
    if ls.dead_count >= WIN_DEAD:
        ls.won = True
    else:
        ls.phase = "catch"   # subsequent bacteria start at vent


# ── Carry serialization ───────────────────────────────────────
def serialize_for_carry(ls: LevelState) -> dict:
    return {
        "dead_count": ls.dead_count,
        "coverage":   round(ls.dead_count / WIN_DEAD, 3),
        "origin_x":   round(ls.vent_x / (NAV_W - 1), 3),
        "origin_y":   round(ls.vent_y / (NAV_H - 1), 3),
    }
