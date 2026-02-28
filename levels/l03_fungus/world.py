# levels/l03_fungus/world.py
# Pure engine logic. No curses imports.
# Phase 1: germinate — spore senses substrate (4 steps).
# Phase 2: network — mycelium spreads through substrate, converting it to soil.

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field

# ── World dimensions ───────────────────────────────────────────
WORLD_W = 48
WORLD_H = 15

# ── Tile types ─────────────────────────────────────────────────
ROCK     = 0
ORGANIC  = 1
MYCELIUM = 2
SOIL     = 3

# ── Organic placement ──────────────────────────────────────────
BASE_DENSITY  = 0.10
CARRY_BONUS   = 0.18   # max additional density from strong cyano legacy

# ── Growth ─────────────────────────────────────────────────────
AGE_TO_SOIL     = 50    # ticks before MYCELIUM → SOIL
BRANCH_CHANCE   = 0.005 # per tick per MYCELIUM/SOIL tile: chance to sprout a tip
TIP_MOVE_CHANCE = 0.20  # per tick per tip: chance to advance one cell
MAX_TIPS        = 30    # cap on autonomous tips

# ── Win ────────────────────────────────────────────────────────
WIN_SOIL_FRAC = 0.30   # fraction of tiles that must be soil

# ── Germination ────────────────────────────────────────────────
GERM_STEPS = 4


@dataclass
class LevelState:
    phase: str = "germinate"

    grid: list = field(default_factory=list)   # WORLD_H × WORLD_W int
    age:  list = field(default_factory=list)   # WORLD_H × WORLD_W int (ticks as MYCELIUM)

    py: int = 0
    px: int = 0

    tips: list = field(default_factory=list)   # [[y, x], ...]

    germ_step: int = GERM_STEPS

    soil_count:     int  = 0
    tick:           int  = 0
    won:            bool = False

    soil_msgs_shown: set = field(default_factory=set)

    origin_x: float = 0.5
    origin_y: float = 0.5


# ── Generation ─────────────────────────────────────────────────
def generate_state(carry) -> LevelState:
    origin_x = getattr(carry, "origin_x", 0.5)
    origin_y = getattr(carry, "origin_y", 0.5)

    cyano    = carry.substrate.get("cyano", {})
    coverage = cyano.get("coverage", 0.0)
    density  = BASE_DENSITY + coverage * CARRY_BONUS

    grid = [[ROCK] * WORLD_W for _ in range(WORLD_H)]
    age  = [[0]    * WORLD_W for _ in range(WORLD_H)]

    _place_organics(grid, origin_x, origin_y, density)

    px = int(origin_x * (WORLD_W - 1))
    py = int(origin_y * (WORLD_H - 1))
    px = max(1, min(WORLD_W - 2, px))
    py = max(1, min(WORLD_H - 2, py))

    grid[py][px] = MYCELIUM

    return LevelState(
        grid=grid,
        age=age,
        py=py,
        px=px,
        tips=[[py, px]],
        germ_step=GERM_STEPS,
        origin_x=origin_x,
        origin_y=origin_y,
    )


def _place_organics(grid, origin_x: float, origin_y: float, density: float) -> None:
    ox    = int(origin_x * (WORLD_W - 1))
    oy    = int(origin_y * (WORLD_H - 1))
    sigma = WORLD_W * 0.30
    for y in range(WORLD_H):
        for x in range(WORLD_W):
            dist = math.sqrt((x - ox) ** 2 + (y - oy) ** 2)
            p    = density * math.exp(-0.5 * (dist / sigma) ** 2)
            if random.random() < p:
                grid[y][x] = ORGANIC


# ── Germinate phase ────────────────────────────────────────────
def germinate_step(ls: LevelState) -> str:
    from . import text as txt
    if ls.germ_step <= 0:
        return ""
    ls.germ_step -= 1
    if ls.germ_step == 0:
        return txt.GERM_ARRIVE
    idx = GERM_STEPS - ls.germ_step - 1
    return txt.GERM_TEXT[idx % len(txt.GERM_TEXT)]


# ── Network phase ──────────────────────────────────────────────
def network_tick(ls: LevelState) -> None:
    ls.tick += 1

    # Age MYCELIUM tiles → convert to SOIL
    for y in range(WORLD_H):
        for x in range(WORLD_W):
            if ls.grid[y][x] == MYCELIUM:
                ls.age[y][x] += 1
                if ls.age[y][x] >= AGE_TO_SOIL:
                    ls.grid[y][x] = SOIL

    # Advance existing tips
    surviving = []
    for ty, tx in ls.tips:
        if random.random() < TIP_MOVE_CHANCE:
            nbrs = _open_neighbors(ls.grid, ty, tx)
            if nbrs:
                ny, nx = random.choice(nbrs)
                ls.grid[ny][nx] = MYCELIUM
                surviving.append([ny, nx])
            # stuck tips retire (fall off the list)
        else:
            surviving.append([ty, tx])

    # Sprout new tips from existing network tiles
    new_tips = []
    for y in range(WORLD_H):
        for x in range(WORLD_W):
            if ls.grid[y][x] in (MYCELIUM, SOIL) and random.random() < BRANCH_CHANCE:
                nbrs = _open_neighbors(ls.grid, y, x)
                if nbrs:
                    ny, nx = random.choice(nbrs)
                    ls.grid[ny][nx] = MYCELIUM
                    new_tips.append([ny, nx])

    ls.tips = surviving + new_tips
    if len(ls.tips) > MAX_TIPS:
        ls.tips = random.sample(ls.tips, MAX_TIPS)

    # Soil count
    ls.soil_count = sum(1 for row in ls.grid for cell in row if cell == SOIL)

    if ls.soil_count >= WIN_SOIL_FRAC * WORLD_W * WORLD_H:
        ls.won = True


def player_move(ls: LevelState, dy: int, dx: int) -> None:
    ny = max(0, min(WORLD_H - 1, ls.py + dy))
    nx = max(0, min(WORLD_W - 1, ls.px + dx))
    ls.py, ls.px = ny, nx
    tile = ls.grid[ny][nx]
    if tile == ROCK:
        ls.grid[ny][nx] = MYCELIUM
    elif tile == ORGANIC:
        ls.grid[ny][nx] = SOIL   # player processing is immediate


def _open_neighbors(grid, y: int, x: int) -> list:
    result = []
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < WORLD_H and 0 <= nx < WORLD_W:
            if grid[ny][nx] in (ROCK, ORGANIC):
                result.append((ny, nx))
    return result


def get_soil_fraction(ls: LevelState) -> float:
    return ls.soil_count / (WORLD_W * WORLD_H)


# ── Carry serialization ────────────────────────────────────────
def serialize_for_carry(ls: LevelState) -> dict:
    return {
        "soil_fraction": round(get_soil_fraction(ls), 3),
        "origin_x":      round(ls.px / (WORLD_W - 1), 3),
        "origin_y":      round(ls.py / (WORLD_H - 1), 3),
    }
