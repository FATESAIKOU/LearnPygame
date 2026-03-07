"""
main.py - 程式入口

執行方式：
    python main.py

需求：Python 3.7+，使用標準函式庫 curses（Linux / macOS）。
Windows 使用者請安裝 windows-curses：pip install windows-curses
"""

import curses
import locale
import sys

from renderer import init_colors
from game import Game
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

# 啟用終端機 UTF-8 支援（方框字元、特殊符號）
locale.setlocale(locale.LC_ALL, "")


def main(stdscr):
    h, w = stdscr.getmaxyx()
    # 含邊框與標題的最小尺寸：(SCREEN_WIDTH+2) × (SCREEN_HEIGHT+5)
    required_h = SCREEN_HEIGHT + 5
    required_w = SCREEN_WIDTH + 2
    if h < required_h or w < required_w:
        stdscr.addstr(
            0, 0,
            f"Terminal too small! Need at least {required_w}x{required_h}, "
            f"currently {w}x{h}. Please resize and restart."
        )
        stdscr.getch()
        return

    curses.curs_set(0)   # 隱藏游標
    init_colors()

    game = Game(stdscr)
    try:
        game.run()
    except SystemExit:
        pass


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    sys.exit(0)
