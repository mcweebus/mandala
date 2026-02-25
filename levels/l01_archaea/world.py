# levels/l01_archaea/world.py
# Pure engine logic. No curses imports.
# Phase 1: navigation via relative heading across a 2D grid.
# Phase 2: catch — compounds rise from vent, player collects all four types.
#           When complete the bacterium lights up and floats to the bottom.

from __future__ import annotations
import random
from dataclasses import dataclass, field
from . import text as txt

# ── Navigation grid ───────────────────────────────────────────
NAV_W = 22
NAV_H = 16

HEADINGS = ["N", "E", "S", "W"]
HEADING_DELTA = {
    "N": (0, -1),
    "E": (1,  0),
    "S": (0,  1),
    "W": (-1, 0),
}

# ── Catch arena ───────────────────────────────────────────────
CATCH_COLS     = 44
CATCH_ROWS     = 20
SPAWN_INTERVAL = 10
RISE_SPEED     = 1
COMPOUNDS      = ["S", "F", "H", "C"]

# ── Body definition ───────────────────────────────────────────
# Segments extending LEFT of @ and RIGHT of @.
# Each entry: (compound_key, display_char)
BODY_LEFT  = [("F", "f"), ("S", "s"), ("H", "h")]   # drawn nearest→farthest from @
BODY_RIGHT = [("H", "h"), ("S", "s"), ("C", "c")]   # drawn nearest→farthest from @

# How far the body extends in each direction from the @ column.
BODY_HALF_L = len(BODY_LEFT)   # 3
BODY_HALF_R = len(BODY_RIGHT)  # 3

# Clamp catch_px so the full body stays inside the arena.
BODY_PX_MIN = BODY_HALF_L
BODY_PX_MAX = CATCH_COLS - 1 - BODY_HALF_R

# ── Float animation ───────────────────────────────────────────
FLOAT_SPEED     = 1.0   # rows per tick
FLOAT_MAX_DRIFT = 0.3   # max horizontal drift per tick (adds subtle organic feel)

# ── Win condition ─────────────────────────────────────────────
WIN_DEAD = 8


# ── State ─────────────────────────────────────────────────────
@dataclass
class CompoundSprite:
    x: int
    y: int
    kind: str


@dataclass
class SettledBody:
    x: int   # column of @ when the body settled


@dataclass
class LevelState:
    # Navigation
    nx:      int  = NAV_W // 2
    ny:      int  = 0
    heading: str  = "S"
    vent_x:  int  = 0
    vent_y:  int  = 0

    # Phase
    phase:   str  = "nav"
    first:   bool = True

    # Catch — living bacterium
    collected:    set  = field(default_factory=set)   # compound keys absorbed so far
    sprites:      list = field(default_factory=list)
    catch_px:     int  = CATCH_COLS // 2
    catch_ticks:  int  = 0

    # Float (death animation)
    floating:     bool  = False
    float_y:      float = 0.0
    float_x:      float = 0.0
    float_drift:  float = 0.0

    # Settled bodies
    settled:      list = field(default_factory=list)

    # Progress
    dead_count:   int  = 0
    won:          bool = False


# ── Generation ────────────────────────────────────────────────
def generate_state() -> LevelState:
    vent_x  = random.randint(2, NAV_W - 3)
    vent_y  = random.randint(NAV_H // 3, NAV_H - 1)
    heading = random.choice(HEADINGS)
    return LevelState(
        nx=NAV_W // 2,
        ny=NAV_H // 2,
        heading=heading,
        vent_x=vent_x,
        vent_y=vent_y,
        catch_px=max(BODY_PX_MIN, min(BODY_PX_MAX, CATCH_COLS // 2)),
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

    if ls.floating:
        # Advance float animation — body drifts downward with slight horizontal wander.
        ls.float_y += FLOAT_SPEED
        ls.float_x += ls.float_drift
        ls.float_x  = max(BODY_PX_MIN, min(BODY_PX_MAX, ls.float_x))
        if ls.float_y >= CATCH_ROWS - 1:
            ls.settled.append(SettledBody(x=int(ls.float_x)))
            ls.floating = False
            _advance_bacterium(ls)
        return

    # Spawn — bias 55% toward compounds not yet collected.
    if ls.catch_ticks % SPAWN_INTERVAL == 0:
        needed = [c for c in COMPOUNDS if c not in ls.collected]
        if needed and random.random() < 0.55:
            kind = random.choice(needed)
        else:
            kind = random.choice(COMPOUNDS)
        ls.sprites.append(CompoundSprite(
            x=random.randint(0, CATCH_COLS - 1),
            y=CATCH_ROWS - 1,
            kind=kind,
        ))

    # Rise all sprites one row toward player.
    for s in ls.sprites:
        s.y -= RISE_SPEED
    ls.sprites = [s for s in ls.sprites if s.y >= 0]


def catch_check_collision(ls: LevelState) -> str | None:
    """Check if any sprite reached the player row and is uncollected.
    Returns 'collected', 'all_collected', or None."""
    result   = None
    remaining = []
    for s in ls.sprites:
        if s.y == 0 and abs(s.x - ls.catch_px) <= 1:
            if s.kind not in ls.collected:
                ls.collected.add(s.kind)
                result = "collected"
            # sprite consumed regardless
        else:
            remaining.append(s)
    ls.sprites = remaining

    # All four types absorbed — trigger float death.
    if set(COMPOUNDS) <= ls.collected:
        ls.floating    = True
        ls.float_y     = 0.0
        ls.float_x     = float(ls.catch_px)
        ls.float_drift = random.uniform(-FLOAT_MAX_DRIFT, FLOAT_MAX_DRIFT)
        ls.sprites     = []
        return "all_collected"

    return result


def catch_move(ls: LevelState, dx: int) -> None:
    ls.catch_px = max(BODY_PX_MIN, min(BODY_PX_MAX, ls.catch_px + dx))


def _advance_bacterium(ls: LevelState) -> None:
    """Called after a settled body lands. Reset for the next bacterium."""
    ls.dead_count += 1
    ls.first       = False
    ls.sprites     = []
    ls.catch_ticks = 0
    ls.collected   = set()
    ls.catch_px    = max(BODY_PX_MIN, min(BODY_PX_MAX, CATCH_COLS // 2))
    ls.floating    = False
    ls.float_y     = 0.0
    ls.float_x     = 0.0
    if ls.dead_count >= WIN_DEAD:
        ls.won = True


def next_bacterium(ls: LevelState) -> None:
    """Legacy alias — kept so dissolve path still compiles."""
    _advance_bacterium(ls)


# ── Carry serialization ───────────────────────────────────────
def serialize_for_carry(ls: LevelState) -> dict:
    return {
        "dead_count": ls.dead_count,
        "coverage":   round(ls.dead_count / WIN_DEAD, 3),
        "origin_x":   round(ls.vent_x / (NAV_W - 1), 3),
        "origin_y":   round(ls.vent_y / (NAV_H - 1), 3),
    }
