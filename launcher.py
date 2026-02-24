# launcher.py
# Master entry point. Manages level progression and seamless transitions.
# Each level exposes run(carry) -> carry. The launcher sequences them.

import sys
import os
import importlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import CarryState, load_carry, save_carry

LEVELS = [
    ("01_archaea",   "levels.l01_archaea"),
    ("02_cyano",     "levels.l02_cyano"),
    ("03_fungus",    "levels.l03_fungus"),
    ("04_lichens",   "levels.l04_lichens"),
    ("05_symbiotes", "levels.l05_symbiotes"),
    ("06_beetles",   "levels.l06_beetles"),
    ("07_worms",     "levels.l07_worms"),
]


def main() -> None:
    carry = load_carry()

    for key, module_path in LEVELS[carry.level_index:]:
        try:
            level = importlib.import_module(module_path)
        except (ImportError, ModuleNotFoundError):
            # Next level not yet built — loop back to the beginning
            carry.level_index = 0
            save_carry(carry)
            main()
            return

        carry = level.run(carry)
        carry.level_index += 1
        save_carry(carry)

    _ending()


def _ending() -> None:
    # All levels complete — the ending.
    # Something walks onto the ground and doesn't know what made it possible.
    pass


if __name__ == "__main__":
    import sys as _sys
    if not os.isatty(_sys.stdin.fileno()):
        script = os.path.abspath(__file__)
        terminals = [
            ["xfce4-terminal", "--hold", "-e", f"python3 {script}"],
            ["gnome-terminal", "--", "python3", script],
            ["xterm", "-hold", "-e", f"python3 {script}"],
            ["konsole", "--hold", "-e", f"python3 {script}"],
            ["alacritty", "-e", "python3", script],
            ["kitty", "python3", script],
        ]
        import subprocess
        for cmd in terminals:
            try:
                subprocess.Popen(cmd)
                break
            except FileNotFoundError:
                continue
        _sys.exit(0)

    main()
