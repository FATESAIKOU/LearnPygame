#!/usr/bin/env python3
"""
main.py - Entry point for NS-SHAFT Terminal Game (小朋友下樓梯).

Run with: python3 main.py

Requires: Python 3.6+ with curses support (Linux/macOS).
For Windows, install windows-curses: pip install windows-curses
"""

import curses
import sys
import locale
from game import Game


def main(stdscr):
    """Curses wrapper main function."""
    # Setup locale for unicode support
    locale.setlocale(locale.LC_ALL, '')

    # Configure curses
    curses.curs_set(0)
    stdscr.timeout(0)

    # Check terminal size
    h, w = stdscr.getmaxyx()
    min_h, min_w = 35, 66
    if h < min_h or w < min_w:
        stdscr.clear()
        msg = f"Terminal too small! Need at least {min_w}x{min_h}, got {w}x{h}"
        try:
            stdscr.addstr(0, 0, msg)
            stdscr.addstr(1, 0, "Please resize your terminal and try again.")
            stdscr.addstr(2, 0, "Press any key to exit...")
            stdscr.refresh()
            stdscr.nodelay(False)
            stdscr.getch()
        except curses.error:
            pass
        return

    game = Game(stdscr)
    game.run()


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n✦ Thanks for playing NS-SHAFT Terminal! ✦")
        print("  小朋友下樓梯 — Terminal Edition")
