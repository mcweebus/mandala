# state.py
# Cross-level carryforward state. What persists between mandalas.
# Nothing mechanical — only position and substrate quality.

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict

SAVE_PATH = os.path.expanduser("~/.mandala/carry.json")


@dataclass
class CarryState:
    level_index: int = 0               # which level we're on (0-6)

    # Spatial carryforward — the same patch of earth across all levels.
    # Origin tile coordinates persist. Each level interprets them at its own scale.
    origin_x: float = 0.5             # normalized 0.0–1.0 within the area
    origin_y: float = 0.5

    # Substrate quality map — what the archaebacteria leave for the cyanobacteria,
    # what the cyanobacteria leave for the fungus, etc.
    # Keyed by level name; each entry is level-specific data.
    substrate: dict = field(default_factory=dict)

    # Dissolution records — a trace that each mandala happened.
    # Not used mechanically. The world noticing itself.
    dissolved: list[str] = field(default_factory=list)


def load_carry() -> CarryState:
    if os.path.exists(SAVE_PATH):
        with open(SAVE_PATH) as f:
            data = json.load(f)
        cs = CarryState()
        for k, v in data.items():
            if hasattr(cs, k):
                setattr(cs, k, v)
        return cs
    return CarryState()


def save_carry(cs: CarryState) -> None:
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    with open(SAVE_PATH, "w") as f:
        json.dump(asdict(cs), f, indent=2)
