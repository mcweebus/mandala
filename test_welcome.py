# test_welcome.py — run the welcome screen in isolation
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from welcome import play

if __name__ == "__main__":
    if not os.isatty(sys.stdin.fileno()):
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
        sys.exit(0)

    play()
