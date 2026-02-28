# levels/l01_archaea/text.py
# All flavor text for the archaebacteria level.
# Lowercase. No exclamation points. The organism is never named.

# ── Navigation ────────────────────────────────────────────────
ATMOSPHERE_FAR = [
    "the water is very cold.",
    "absolute dark.",
]

ATMOSPHERE_MED = [
    "a faint thermal trace.",
    "a gradient. something distant.",
]

ATMOSPHERE_CLOSE = [
    "sulfur. hydrogen. something is active.",
    "a thermal column rises near here.",
    "the rock is warm to the touch.",
]

ARRIVE_VENT = "the vent. it is here."

# ── Catch phase ───────────────────────────────────────────────
CATCH_SUCCESS     = "absorbed."
ALL_COLLECTED_MSG = "the chemistry is complete. it sinks."
CATCH_MISS        = ""

COMPOUND_NAMES = {
    "S":  "sulfur",
    "F":  "iron",
    "H":  "hydrogen",
    "C":  "co2",
}

COMPOUND_DISPLAY = {
    "S": "s",
    "F": "f",
    "H": "h",
    "C": "c",
}

# ── Sink / sediment ───────────────────────────────────────────
SINK_LINES = [
    "the cell descends.",
    "it settles.",
    "the floor receives it.",
    "another layer.",
    "the sediment deepens.",
]

# ── Win ───────────────────────────────────────────────────────
WIN_MESSAGE = "the floor is thick enough. something has been made here."

DISSOLVE_LINES = [
    "the sediment holds its shape.",
    "what was alive is now the ground.",
    "marine soil. it will persist.",
    "the chemistry is changed. permanently.",
]

DISSOLVED = "the ocean floor remembers. it does not know that it does."

# ── Death (unused in this design — no fail state) ─────────────
DEATH_MSG = "the chemistry fails."
