# levels/l01_archaea/world.py
# Pure engine logic. No curses imports.
# Grid, state, generation, tick, movement.

from __future__ import annotations
import random
from dataclasses import dataclass, field
from . import text as txt

MAP_W = 44
MAP_H = 16

# ── Tile types ────────────────────────────────────────────────
ROCK        = "R"
SULFUR      = "S"
IRON        = "I"
METHANE     = "M"
HOT         = "H"
ACID        = "A"
BIOFILM     = "B"
CONDITIONED = "C"
COMPETITOR  = "W"

# Display: (char, bold, dim)
TILE_DISPLAY = {
    ROCK:        (".", False, True),
    SULFUR:      ("s", True,  False),
    IRON:        ("i", True,  False),
    METHANE:     ("m", True,  False),
    HOT:         ("^", True,  False),
    ACID:        ("~", False, False),
    BIOFILM:     (",", False, True),
    CONDITIONED: ("+", False, False),
    COMPETITOR:  ("w", False, True),
}

CONSUMABLE  = {SULFUR, IRON, METHANE}
HAZARD      = {HOT, ACID}
IMPASSABLE  = {COMPETITOR}
SEEDABLE    = {ROCK, SULFUR, IRON, METHANE}

BIOFILM_MATURE    = 55     # ticks for biofilm to become conditioned
SPREAD_INTERVAL   = 8      # ticks between competitor spread
ERODE_INTERVAL    = 22     # ticks between competitor biofilm erosion
DRAIN_INTERVAL    = 5      # ticks between passive energy drain
PASSIVE_INTERVAL  = 12     # ticks between passive biomass from conditioned
COMPETITOR_CAP    = int(MAP_W * MAP_H * 0.22)  # max competitor tiles

WIN_COVERAGE  = 0.30   # fraction of map that must be conditioned
WIN_BIOMASS   = 80     # minimum biomass to win


# ── State ─────────────────────────────────────────────────────
@dataclass
class LevelState:
    grid:   list = field(default_factory=list)  # grid[y][x] = tile type
    age:    list = field(default_factory=list)  # age[y][x] = int (biofilm age)
    px:     int  = 0
    py:     int  = 0
    energy: int  = 100
    biomass: int = 0
    ticks:  int  = 0
    won:    bool = False


# ── Map generation ────────────────────────────────────────────
def generate_map() -> LevelState:
    grid = [[ROCK] * MAP_W for _ in range(MAP_H)]
    age  = [[0]    * MAP_W for _ in range(MAP_H)]

    # Sulfur seams — upper two-thirds, 3 veins
    for _ in range(3):
        sx = random.randint(0, MAP_W - 1)
        sy = random.randint(0, int(MAP_H * 0.65))
        _vein(grid, SULFUR, sx, sy, length=random.randint(10, 18))

    # Iron seams — middle zone, 2 veins
    for _ in range(2):
        sx = random.randint(0, MAP_W - 1)
        sy = random.randint(MAP_H // 4, int(MAP_H * 0.75))
        _vein(grid, IRON, sx, sy, length=random.randint(7, 13))

    # Methane pockets — lower half, rare, 1-2 clusters
    for _ in range(random.randint(1, 2)):
        sx = random.randint(2, MAP_W - 3)
        sy = random.randint(MAP_H // 2, MAP_H - 2)
        _cluster(grid, METHANE, sx, sy, radius=random.randint(1, 2),
                 avoid={HOT})

    # Hot zones — 2 thermal clusters, weighted toward bottom
    for _ in range(2):
        sx = random.randint(4, MAP_W - 5)
        sy = random.randint(MAP_H // 2, MAP_H - 2)
        _cluster(grid, HOT, sx, sy, radius=random.randint(2, 3),
                 avoid={COMPETITOR})

    # Acid zones — 1-2 small patches, anywhere
    for _ in range(random.randint(1, 2)):
        sx = random.randint(1, MAP_W - 2)
        sy = random.randint(1, MAP_H - 2)
        _cluster(grid, ACID, sx, sy, radius=random.randint(1, 2),
                 avoid={HOT, COMPETITOR})

    # Competitors — seeded at left and right edges
    cy_a = random.randint(2, MAP_H - 3)
    cy_b = random.randint(2, MAP_H - 3)
    _cluster(grid, COMPETITOR, 1,         cy_a, radius=1, avoid=HAZARD)
    _cluster(grid, COMPETITOR, MAP_W - 2, cy_b, radius=1, avoid=HAZARD)

    # Player start — center, shift if hazard or competitor
    px, py = MAP_W // 2, MAP_H // 2
    attempts = 0
    while grid[py][px] in HAZARD | IMPASSABLE and attempts < MAP_W:
        px = (px + 1) % MAP_W
        attempts += 1

    # Seed starting tile as biofilm
    grid[py][px] = BIOFILM
    age[py][px] = 0

    ls = LevelState(grid=grid, age=age, px=px, py=py)
    return ls


def _vein(grid, tile_type: str, x: int, y: int, length: int) -> None:
    dx = random.choice([-1, 1])
    for _ in range(length):
        x = max(0, min(MAP_W - 1, x))
        y = max(0, min(MAP_H - 1, y))
        if grid[y][x] not in (HOT, COMPETITOR):
            grid[y][x] = tile_type
        # Drift: mostly horizontal with occasional vertical shift
        if random.random() < 0.25:
            y += random.choice([-1, 0, 1])
        else:
            x += dx
            if random.random() < 0.08:
                dx = -dx


def _cluster(grid, tile_type: str, cx: int, cy: int,
             radius: int, avoid: set | None = None) -> None:
    avoid = avoid or set()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < MAP_W and 0 <= ny < MAP_H):
                continue
            dist = abs(dx) + abs(dy)
            if dist > radius:
                continue
            prob = 1.0 - (dist / (radius + 1)) * 0.6
            if random.random() < prob and grid[ny][nx] not in avoid:
                grid[ny][nx] = tile_type


# ── Movement ──────────────────────────────────────────────────
def move_player(ls: LevelState, dx: int, dy: int) -> str:
    nx = ls.px + dx
    ny = ls.py + dy

    if not (0 <= nx < MAP_W and 0 <= ny < MAP_H):
        return ""

    tile = ls.grid[ny][nx]

    if tile in IMPASSABLE:
        return random.choice(
            ["the other colony holds this.",
             "something else has claimed this ground."]
        )

    ls.px, ls.py = nx, ny
    msg = ""

    if tile == SULFUR:
        ls.energy = min(100, ls.energy + 15)
        ls.biomass += 8
        ls.grid[ny][nx] = BIOFILM
        ls.age[ny][nx] = 0
        msg = random.choice(txt.CONSUME_SULFUR)
    elif tile == IRON:
        ls.energy = min(100, ls.energy + 25)
        ls.biomass += 15
        ls.grid[ny][nx] = BIOFILM
        ls.age[ny][nx] = 0
        msg = random.choice(txt.CONSUME_IRON)
    elif tile == METHANE:
        ls.energy = min(100, ls.energy + 40)
        ls.biomass += 30
        ls.grid[ny][nx] = BIOFILM
        ls.age[ny][nx] = 0
        msg = random.choice(txt.CONSUME_METHANE)
    elif tile in SEEDABLE:
        ls.grid[ny][nx] = BIOFILM
        ls.age[ny][nx] = 0
    elif tile in HAZARD:
        msg = random.choice(txt.ENTER_HOT if tile == HOT else txt.ENTER_ACID)
    # BIOFILM and CONDITIONED: player moves on them with no change

    return msg


# ── World tick ────────────────────────────────────────────────
def world_tick(ls: LevelState) -> str | None:
    ls.ticks += 1
    msg = None

    # Passive energy drain
    if ls.ticks % DRAIN_INTERVAL == 0:
        drain = 1
        tile = ls.grid[ls.py][ls.px]
        if tile == HOT:
            drain += 2
        elif tile == ACID:
            drain += 1
        ls.energy = max(0, ls.energy - drain)

    # Biofilm aging → conditioned
    for y in range(MAP_H):
        for x in range(MAP_W):
            if ls.grid[y][x] == BIOFILM:
                ls.age[y][x] += 1
                if ls.age[y][x] >= BIOFILM_MATURE:
                    ls.grid[y][x] = CONDITIONED
                    ls.age[y][x] = 0

    # Passive biomass from conditioned tiles
    if ls.ticks % PASSIVE_INTERVAL == 0:
        cond = count_conditioned(ls)
        if cond > 0:
            ls.biomass += max(1, cond // 18)

    # Competitor spread
    if ls.ticks % SPREAD_INTERVAL == 0:
        _competitor_spread(ls)

    # Competitor erosion of biofilm
    if ls.ticks % ERODE_INTERVAL == 0:
        _competitor_erode(ls)

    # Ambient message
    if ls.ticks % 48 == 0 and ls.ticks > 0:
        msg = random.choice(txt.AMBIENT)

    # Win check
    check_win(ls)

    return msg


def _competitor_spread(ls: LevelState) -> None:
    comp_total = sum(
        1 for y in range(MAP_H) for x in range(MAP_W)
        if ls.grid[y][x] == COMPETITOR
    )
    if comp_total >= COMPETITOR_CAP:
        return

    candidates = []
    for y in range(MAP_H):
        for x in range(MAP_W):
            if ls.grid[y][x] == COMPETITOR:
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                        t = ls.grid[ny][nx]
                        if t == ROCK:
                            candidates.append((nx, ny))

    random.shuffle(candidates)
    for nx, ny in candidates[:2]:
        ls.grid[ny][nx] = COMPETITOR


def _competitor_erode(ls: LevelState) -> None:
    candidates = []
    for y in range(MAP_H):
        for x in range(MAP_W):
            if ls.grid[y][x] == COMPETITOR:
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                        if ls.grid[ny][nx] == BIOFILM:
                            candidates.append((nx, ny))

    if candidates:
        nx, ny = random.choice(candidates)
        ls.grid[ny][nx] = ROCK
        ls.age[ny][nx] = 0


# ── Win / utility ─────────────────────────────────────────────
def check_win(ls: LevelState) -> None:
    if ls.won:
        return
    cond = count_conditioned(ls)
    if cond >= MAP_W * MAP_H * WIN_COVERAGE and ls.biomass >= WIN_BIOMASS:
        ls.won = True


def count_conditioned(ls: LevelState) -> int:
    return sum(
        1 for y in range(MAP_H) for x in range(MAP_W)
        if ls.grid[y][x] == CONDITIONED
    )


def conditioned_positions(ls: LevelState) -> list[tuple[int, int]]:
    positions = [
        (x, y) for y in range(MAP_H) for x in range(MAP_W)
        if ls.grid[y][x] == CONDITIONED
    ]
    random.shuffle(positions)
    return positions[:150]


def serialize_for_carry(ls: LevelState) -> dict:
    cond = count_conditioned(ls)
    return {
        "conditioned_count": cond,
        "coverage": round(cond / (MAP_W * MAP_H), 3),
        "origin_x": round(ls.px / (MAP_W - 1), 3),
        "origin_y": round(ls.py / (MAP_H - 1), 3),
    }
