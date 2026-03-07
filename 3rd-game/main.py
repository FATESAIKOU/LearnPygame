"""
main.py - 程式入口

執行方式：
    python main.py

需求：Python 3.7+，使用標準函式庫 curses（Linux / macOS）。
Windows 使用者請安裝 windows-curses：pip install windows-curses
"""

import curses
import sys

from renderer import init_colors
from game import Game
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


def main(stdscr):
    # 取得終端機尺寸
    h, w = stdscr.getmaxyx()
    required_h = SCREEN_HEIGHT + 2
    required_w = SCREEN_WIDTH + 2
    if h < required_h or w < required_w:
        stdscr.addstr(
            0, 0,
            f"終端機太小！需要至少 {required_w}x{required_h}，"
            f"目前 {w}x{h}。請放大視窗後重新執行。"
        )
        stdscr.getch()
        return

    # 初始化
    curses.curs_set(0)       # 隱藏游標
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
