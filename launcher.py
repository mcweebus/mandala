# launcher.py
# Master entry point. Manages level progression and seamless transitions.
# Each level exposes run(carry) -> carry. The launcher sequences them.

from state import CarryState, load_carry, save_carry

LEVELS = [
    ("01_archaea",  "levels.l01_archaea"),
    ("02_cyano",    "levels.l02_cyano"),
    ("03_fungus",   "levels.l03_fungus"),
    ("04_lichens",  "levels.l04_lichens"),
    ("05_symbiotes","levels.l05_symbiotes"),
    ("06_beetles",  "levels.l06_beetles"),
    ("07_worms",    "levels.l07_worms"),
]


def main() -> None:
    carry = load_carry()

    for key, module_path in LEVELS[carry.level_index:]:
        import importlib
        level = importlib.import_module(module_path)
        carry = level.run(carry)
        carry.level_index += 1
        save_carry(carry)

    # All levels complete — the ending
    _ending()


def _ending() -> None:
    # The mandala of mandalas is complete.
    # Something walks onto the ground and doesn't know what made it possible.
    pass


if __name__ == "__main__":
    main()
