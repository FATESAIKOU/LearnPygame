"""
renderer.py - 終端機畫面渲染
使用 curses 進行雙緩衝風格繪製，減少閃爍。
"""

import curses
from typing import List
from constants import *
from entities import Player, Platform


# curses 顏色對 (pair index)
COLOR_DEFAULT = 1
COLOR_PLAYER = 2
COLOR_PLATFORM_NORMAL = 3
COLOR_PLATFORM_DAMAGE = 4
COLOR_PLATFORM_HEAL = 5
COLOR_PLATFORM_CRUMBLE = 6
COLOR_PLATFORM_SPRING = 7
COLOR_PLATFORM_MOVING = 8
COLOR_UI = 9
COLOR_INVINCIBLE = 10


def init_colors():
    """初始化 curses 顏色"""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_DEFAULT, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_PLAYER, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_PLATFORM_NORMAL, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_PLATFORM_DAMAGE, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_PLATFORM_HEAL, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_PLATFORM_CRUMBLE, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_PLATFORM_SPRING, curses.COLOR_MAGENTA, -1)
    curses.init_pair(COLOR_PLATFORM_MOVING, curses.COLOR_BLUE, -1)
    curses.init_pair(COLOR_UI, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_INVINCIBLE, curses.COLOR_BLACK, curses.COLOR_CYAN)


def _platform_color(platform_type: str) -> int:
    mapping = {
        PLATFORM_NORMAL: COLOR_PLATFORM_NORMAL,
        PLATFORM_DAMAGE: COLOR_PLATFORM_DAMAGE,
        PLATFORM_HEAL: COLOR_PLATFORM_HEAL,
        PLATFORM_CRUMBLE: COLOR_PLATFORM_CRUMBLE,
        PLATFORM_SPRING: COLOR_PLATFORM_SPRING,
        PLATFORM_MOVING: COLOR_PLATFORM_MOVING,
    }
    return curses.color_pair(mapping.get(platform_type, COLOR_PLATFORM_NORMAL))


def render_game(win, player: Player, platforms: List[Platform], score: int,
                level: int, frame: int):
    """繪製遊戲畫面主函式"""
    win.erase()

    h, w = win.getmaxyx()

    # --- 邊界牆壁 ---
    for row in range(h - 1):
        _safe_addch(win, row, 0, CHAR_WALL, curses.color_pair(COLOR_DEFAULT))
        _safe_addch(win, row, SCREEN_WIDTH - 1, CHAR_WALL, curses.color_pair(COLOR_DEFAULT))

    # --- 平台 ---
    for plat in platforms:
        py = int(plat.y)
        if 0 <= py < SCREEN_HEIGHT:
            color = _platform_color(plat.platform_type)
            ch = plat.char()
            for col in range(int(plat.x), int(plat.x) + plat.width):
                if 1 <= col < SCREEN_WIDTH - 1:
                    _safe_addch(win, py, col, ch, color)

    # --- 玩家 ---
    px = int(player.x)
    py = int(player.y)
    if 0 <= py < SCREEN_HEIGHT and 1 <= px < SCREEN_WIDTH - 1:
        if player.invincible_frames > 0 and (frame % 4 < 2):
            player_attr = curses.color_pair(COLOR_INVINCIBLE) | curses.A_BOLD
        else:
            player_attr = curses.color_pair(COLOR_PLAYER) | curses.A_BOLD
        _safe_addch(win, py, px, CHAR_PLAYER, player_attr)

    # --- UI 欄位（最底列）---
    ui_row = SCREEN_HEIGHT
    hp_bar = "♥" * player.hp + "♡" * (PLAYER_HP_MAX - player.hp)
    ui_text = f" HP:{hp_bar}  Score:{score:06d}  Lv:{level} "
    _safe_addstr(win, ui_row, 0, ui_text[:w - 1], curses.color_pair(COLOR_UI))

    win.refresh()


def render_menu(win, scores: list):
    """繪製開始畫面"""
    win.erase()
    h, w = win.getmaxyx()
    title_lines = [
        r" ____  _        _                ____                      _   ",
        r"/ ___|| |_ __ _(_)_ __          |  _ \  ___  ___  ___ ___ | |_ ",
        r"\___ \| __/ _` | | '__|  _____  | | | |/ _ \/ __|/ __/ _ \| __|",
        r" ___) | || (_| | | |    |_____| | |_| |  __/\__ \ (_|  __/| |_ ",
        r"|____/ \__\__,_|_|_|            |____/ \___||___/\___\___| \__|",
        "",
        "  小朋友下樓梯  (Terminal Edition)",
        "",
        "  [a/d 或 ←/→]  左右移動",
        "  [p]           暫停",
        "  [q]           離開",
        "",
        "  按 Enter 開始",
    ]
    start_row = max(0, h // 2 - len(title_lines) // 2)
    for i, line in enumerate(title_lines):
        row = start_row + i
        if row < h - 1:
            col = max(0, (w - len(line)) // 2)
            _safe_addstr(win, row, col, line[:w - 1], curses.color_pair(COLOR_UI))

    # 排行榜
    if scores:
        lb_row = start_row + len(title_lines) + 1
        _safe_addstr(win, lb_row, 2, "  排行榜 TOP5:", curses.color_pair(COLOR_PLATFORM_NORMAL))
        for rank, s in enumerate(scores[:5], 1):
            lb_row += 1
            if lb_row < h - 1:
                _safe_addstr(win, lb_row, 2, f"  #{rank}  {s:06d}", curses.color_pair(COLOR_DEFAULT))

    win.refresh()


def render_pause(win):
    """繪製暫停畫面（疊加在遊戲畫面上）"""
    h, w = win.getmaxyx()
    msg = "  PAUSED  按 [p] 繼續  "
    row = SCREEN_HEIGHT // 2
    col = max(0, (w - len(msg)) // 2)
    _safe_addstr(win, row, col, msg, curses.color_pair(COLOR_UI) | curses.A_REVERSE)
    win.refresh()


def render_gameover(win, score: int, scores: list):
    """繪製 Game Over 畫面"""
    win.erase()
    h, w = win.getmaxyx()
    lines = [
        "  GAME OVER  ",
        "",
        f"  最終分數: {score:06d}",
        "",
        "  排行榜 TOP5:",
    ]
    for rank, s in enumerate(scores[:5], 1):
        lines.append(f"    #{rank}  {s:06d}")
    lines += ["", "  [r] 重新開始   [q] 離開"]

    start_row = max(0, h // 2 - len(lines) // 2)
    for i, line in enumerate(lines):
        row = start_row + i
        if row < h - 1:
            col = max(0, (w - len(line)) // 2)
            attr = curses.color_pair(COLOR_PLATFORM_DAMAGE) | curses.A_BOLD if "GAME OVER" in line else curses.color_pair(COLOR_UI)
            _safe_addstr(win, row, col, line[:w - 1], attr)
    win.refresh()


# ---------- 安全寫入工具 ----------

def _safe_addch(win, row: int, col: int, ch: str, attr: int):
    try:
        win.addch(row, col, ch, attr)
    except curses.error:
        pass


def _safe_addstr(win, row: int, col: int, text: str, attr: int):
    try:
        win.addstr(row, col, text, attr)
    except curses.error:
        pass
