# levels/l02_cyano/world.py
# Pure engine logic. No curses imports.
# Phase 1: ascend — player rises 10 steps from deep water to the surface.
# Phase 2: bloom — cyanobacteria mat spreads across a lit grid, producing O2.

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field

# ── Ascend constants ───────────────────────────────────────────
MAX_DEPTH = 10

# ── Bloom constants ───────────────────────────────────────────
BLOOM_W        = 40
BLOOM_H        = 14
SPREAD_CHANCE  = 0.02
O2_RATE        = 0.04
WIN_O2         = 200.0
BUBBLE_CHANCE  = 0.04


# ── State ─────────────────────────────────────────────────────
@dataclass
class LevelState:
    # Phase
    phase: str = "ascend"

    # Ascend
    depth: int = MAX_DEPTH

    # Bloom — player position
    px: int   = 0
    py: int   = 0

    # Bloom — world
    origin_x: float = 0.5
    light:    list  = field(default_factory=list)   # BLOOM_W floats 0.0–1.0
    colony:   list  = field(default_factory=list)   # BLOOM_H x BLOOM_W bools
    bubbles:  list  = field(default_factory=list)   # list of [x, y]

    # Bloom — progress
    total_o2:            float = 0.0
    coverage_msgs_shown: set   = field(default_factory=set)  # {5, 20, 50}
    won:                 bool  = False


# ── Generation ────────────────────────────────────────────────
def _make_light(origin_x: float) -> list:
    sigma = 0.35
    return [
        math.exp(-0.5 * ((col / (BLOOM_W - 1) - origin_x) / sigma) ** 2)
        for col in range(BLOOM_W)
    ]


def generate_state(carry) -> LevelState:
    origin_x = carry.origin_x
    px = int(origin_x * (BLOOM_W - 1))
    px = max(1, min(BLOOM_W - 2, px))
    py = 2

    light  = _make_light(origin_x)
    colony = [[False] * BLOOM_W for _ in range(BLOOM_H)]

    # Seed 3×3 patch centered on starting position
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            cy = max(0, min(BLOOM_H - 1, py + dy))
            cx = max(0, min(BLOOM_W - 1, px + dx))
            colony[cy][cx] = True

    return LevelState(
        depth=MAX_DEPTH,
        px=px,
        py=py,
        origin_x=origin_x,
        light=light,
        colony=colony,
    )


# ── Ascend phase ──────────────────────────────────────────────
def ascend_step(ls: LevelState) -> str:
    """Decrease depth by 1, return flavor text."""
    from . import text as txt
    if ls.depth <= 0:
        return ""
    ls.depth -= 1
    if ls.depth == 0:
        return txt.ASCEND_ARRIVE
    elif ls.depth <= 2:
        return random.choice(txt.ASCEND_NEAR)
    elif ls.depth <= 5:
        return random.choice(txt.ASCEND_MID)
    else:
        return random.choice(txt.ASCEND_DEEP)


# ── Bloom phase ───────────────────────────────────────────────
def bloom_tick(ls: LevelState) -> None:
    # Spread: each colonized cell has SPREAD_CHANCE of claiming a random empty neighbor
    new_colonies = []
    for ry in range(BLOOM_H):
        for rx in range(BLOOM_W):
            if ls.colony[ry][rx] and random.random() < SPREAD_CHANCE:
                neighbors = []
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = ry + dy, rx + dx
                    if 0 <= ny < BLOOM_H and 0 <= nx < BLOOM_W and not ls.colony[ny][nx]:
                        neighbors.append((ny, nx))
                if neighbors:
                    new_colonies.append(random.choice(neighbors))
    for ny, nx in new_colonies:
        ls.colony[ny][nx] = True

    # O2 production
    for ry in range(BLOOM_H):
        for rx in range(BLOOM_W):
            if ls.colony[ry][rx]:
                ls.total_o2 += ls.light[rx] * O2_RATE

    # Advance existing bubbles (rise = y decreases)
    new_bubbles = [[x, y - 1] for x, y in ls.bubbles if y - 1 >= 0]

    # Emit new bubbles from colonized cells
    for ry in range(BLOOM_H):
        for rx in range(BLOOM_W):
            if ls.colony[ry][rx] and random.random() < BUBBLE_CHANCE:
                new_bubbles.append([rx, ry - 1])

    ls.bubbles = new_bubbles

    # Win check
    if ls.total_o2 >= WIN_O2:
        ls.won = True


def bloom_move(ls: LevelState, dy: int, dx: int) -> None:
    ny = max(0, min(BLOOM_H - 1, ls.py + dy))
    nx = max(0, min(BLOOM_W - 1, ls.px + dx))
    ls.py, ls.px = ny, nx
    ls.colony[ny][nx] = True


def get_coverage(ls: LevelState) -> float:
    total = BLOOM_W * BLOOM_H
    colonized = sum(1 for row in ls.colony for cell in row if cell)
    return colonized / total


# ── Carry serialization ───────────────────────────────────────
def serialize_for_carry(ls: LevelState) -> dict:
    return {
        "coverage":  round(get_coverage(ls), 3),
        "total_o2":  round(ls.total_o2, 1),
        "origin_x":  ls.origin_x,
        "origin_y":  round(ls.py / (BLOOM_H - 1), 3),
    }
