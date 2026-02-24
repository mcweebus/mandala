# levels/l01_archaea/main.py
# Level 1 — Archaebacteria.
# Terminal/curses. Monochrome. No light — only chemistry.
# The player is a single archaebacterium moving through primordial substrate.

from state import CarryState


def run(carry: CarryState) -> CarryState:
    # TODO: implement archaebacteria level
    # - Generate substrate map (mineral seams, temperature zones, chemical gradients)
    # - Player moves through medium, consumes chemicals, leaves biofilm trail
    # - Colony spreads from trail; competes with other microbial mats
    # - Win: conditioned substrate covers sufficient area, system self-sustains
    # - On win: record conditioned tile data into carry.substrate["archaea"]
    #           append dissolution note to carry.dissolved
    #           return carry
    raise NotImplementedError("level 1 not yet implemented")
