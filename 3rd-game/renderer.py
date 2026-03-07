"""
renderer.py - 終端機畫面渲染

特色：
- 自動置中遊戲區域
- 雙線方框邊框
- 星空背景
- 彩色 UI 與危機警告
"""

import curses
import unicodedata
from typing import List
from constants import *
from entities import Player, Platform

# ─── 顏色對索引 ───
C_DEFAULT      = 1
C_PLAYER       = 2
C_PLAT_NORMAL  = 3
C_PLAT_DAMAGE  = 4
C_PLAT_HEAL    = 5
C_PLAT_CRUMBLE = 6
C_PLAT_SPRING  = 7
C_PLAT_MOVING  = 8
C_UI           = 9
C_INVINCIBLE   = 10
C_BORDER       = 11
C_STAR         = 12
C_HP_FULL      = 13
C_TITLE        = 14
C_DANGER       = 15
C_LABEL        = 16


def init_colors():
    """初始化 curses 顏色"""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(C_DEFAULT,      curses.COLOR_WHITE,   -1)
    curses.init_pair(C_PLAYER,       curses.COLOR_CYAN,    -1)
    curses.init_pair(C_PLAT_NORMAL,  curses.COLOR_WHITE,   -1)
    curses.init_pair(C_PLAT_DAMAGE,  curses.COLOR_RED,     -1)
    curses.init_pair(C_PLAT_HEAL,    curses.COLOR_GREEN,   -1)
    curses.init_pair(C_PLAT_CRUMBLE, curses.COLOR_YELLOW,  -1)
    curses.init_pair(C_PLAT_SPRING,  curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_PLAT_MOVING,  curses.COLOR_BLUE,    -1)
    curses.init_pair(C_UI,           curses.COLOR_YELLOW,  -1)
    curses.init_pair(C_INVINCIBLE,   curses.COLOR_BLACK,   curses.COLOR_CYAN)
    curses.init_pair(C_BORDER,       curses.COLOR_CYAN,    -1)
    curses.init_pair(C_STAR,         curses.COLOR_WHITE,   -1)
    curses.init_pair(C_HP_FULL,      curses.COLOR_RED,     -1)
    curses.init_pair(C_TITLE,        curses.COLOR_CYAN,    -1)
    curses.init_pair(C_DANGER,       curses.COLOR_RED,     -1)
    curses.init_pair(C_LABEL,        curses.COLOR_YELLOW,  -1)


# ─── 座標工具 ───

def _display_width(s: str) -> int:
    """計算字串的顯示寬度（CJK 全形字元為 2）"""
    total = 0
    for ch in s:
        ea = unicodedata.east_asian_width(ch)
        total += 2 if ea in ('W', 'F') else 1
    return total


def _get_offsets(win):
    """
    計算使遊戲區域置中的終端機偏移量。

    版面配置（高度）：
      off_y + 0 : 標題列
      off_y + 1 : ╔═══╗  上邊框
      off_y + 2 ~ off_y+1+SCREEN_HEIGHT : 遊戲區域
      off_y+2+SCREEN_HEIGHT : ╠═══╣  分隔線
      off_y+3+SCREEN_HEIGHT : 狀態列
      off_y+4+SCREEN_HEIGHT : ╚═══╝  下邊框
    總高 = SCREEN_HEIGHT + 5
    """
    h, w = win.getmaxyx()
    total_h = SCREEN_HEIGHT + 5
    total_w = SCREEN_WIDTH + 2
    off_y = max(0, (h - total_h) // 2)
    off_x = max(0, (w - total_w) // 2)
    return off_y, off_x


def _gr(off_y: int, row: int) -> int:
    """遊戲列 → 終端機列"""
    return off_y + 2 + row


def _gc(off_x: int, col: int) -> int:
    """遊戲欄 → 終端機欄"""
    return off_x + 1 + col


# ─── 安全繪製 ───

def _puts(win, row: int, col: int, text: str, attr: int):
    """安全的 addstr，忽略超出畫面的錯誤"""
    try:
        win.addstr(row, col, text, attr)
    except curses.error:
        pass


# ─── 邊框 ───

def _draw_frame(win, off_y: int, off_x: int):
    """繪製遊戲區域外框（雙線方框 + 標題 + 分隔線）"""
    h, w = win.getmaxyx()
    ba = curses.color_pair(C_BORDER) | curses.A_BOLD
    ta = curses.color_pair(C_TITLE)  | curses.A_BOLD

    # 標題列（外框上方）
    title_ascii = "* STAIR DESCENT  |  TERMINAL EDITION *"
    tcol = off_x + max(0, (SCREEN_WIDTH + 2 - len(title_ascii)) // 2)
    _puts(win, off_y, tcol, title_ascii, ta)

    # 上邊框
    _puts(win, off_y + 1, off_x,
          CHAR_BORDER_TL + CHAR_BORDER_H * SCREEN_WIDTH + CHAR_BORDER_TR, ba)

    # 左右側線（遊戲區域）
    for r in range(SCREEN_HEIGHT):
        _puts(win, _gr(off_y, r), off_x, CHAR_BORDER_V, ba)
        _puts(win, _gr(off_y, r), off_x + SCREEN_WIDTH + 1, CHAR_BORDER_V, ba)

    # 分隔線
    _puts(win, off_y + 2 + SCREEN_HEIGHT, off_x,
          CHAR_BORDER_ML + CHAR_BORDER_H * SCREEN_WIDTH + CHAR_BORDER_MR, ba)

    # 左右側線（狀態列）
    _puts(win, off_y + 3 + SCREEN_HEIGHT, off_x, CHAR_BORDER_V, ba)
    _puts(win, off_y + 3 + SCREEN_HEIGHT, off_x + SCREEN_WIDTH + 1, CHAR_BORDER_V, ba)

    # 下邊框
    _puts(win, off_y + 4 + SCREEN_HEIGHT, off_x,
          CHAR_BORDER_BL + CHAR_BORDER_H * SCREEN_WIDTH + CHAR_BORDER_BR, ba)


# ─── 背景星空 ───

_STAR_POS = None

def _build_star_positions():
    """預先計算稀疏星點座標（固定種子，每行平均 1~2 顆）"""
    global _STAR_POS
    stars = []
    for r in range(SCREEN_HEIGHT):
        for c in range(1, SCREEN_WIDTH - 1):
            # LCG 風格 hash，密度約 1/40
            h = (r * 2654435761 ^ c * 1013904223) & 0xFFFFFF
            if h % 40 == 0:
                ch = "." if h % 3 else "*"
                stars.append((r, c, ch))
    _STAR_POS = stars


def _draw_bg(win, off_y: int, off_x: int, frame: int):
    """繪製帶視差感的星空背景"""
    global _STAR_POS
    if _STAR_POS is None:
        _build_star_positions()

    sa = curses.color_pair(C_STAR) | curses.A_DIM
    shift = frame // 20  # 緩慢上移星點，製造視差感

    for (r, c, ch) in _STAR_POS:
        draw_r = (r - shift) % SCREEN_HEIGHT
        term_r = _gr(off_y, draw_r)
        term_c = _gc(off_x, c)
        _puts(win, term_r, term_c, ch, sa)


# ─── 平台 ───

def _platform_attr(platform_type: str) -> int:
    mapping = {
        PLATFORM_NORMAL:  curses.color_pair(C_PLAT_NORMAL)  | curses.A_BOLD,
        PLATFORM_DAMAGE:  curses.color_pair(C_PLAT_DAMAGE)  | curses.A_BOLD,
        PLATFORM_HEAL:    curses.color_pair(C_PLAT_HEAL)    | curses.A_BOLD,
        PLATFORM_CRUMBLE: curses.color_pair(C_PLAT_CRUMBLE) | curses.A_BOLD,
        PLATFORM_SPRING:  curses.color_pair(C_PLAT_SPRING)  | curses.A_BOLD,
        PLATFORM_MOVING:  curses.color_pair(C_PLAT_MOVING)  | curses.A_BOLD,
    }
    return mapping.get(platform_type, curses.color_pair(C_PLAT_NORMAL))


# 平台兩端裝飾字元
_PLAT_CAP = {
    PLATFORM_NORMAL:  ("[", "]"),
    PLATFORM_DAMAGE:  ("<", ">"),
    PLATFORM_HEAL:    ("(", ")"),
    PLATFORM_CRUMBLE: ("{", "}"),
    PLATFORM_SPRING:  ("/", "\\"),
    PLATFORM_MOVING:  ("<", ">"),
}


def _draw_platforms(win, off_y: int, off_x: int, platforms: List[Platform]):
    for plat in platforms:
        if not plat.active:
            continue
        py = int(plat.y)
        if not (0 <= py < SCREEN_HEIGHT):
            continue
        attr = _platform_attr(plat.platform_type)
        ch   = plat.char()
        cap_l, cap_r = _PLAT_CAP.get(plat.platform_type, ("[", "]"))
        px = int(plat.x)

        for i in range(plat.width):
            col = px + i
            if not (1 <= col < SCREEN_WIDTH - 1):
                continue
            if i == 0:
                draw_ch = cap_l
            elif i == plat.width - 1:
                draw_ch = cap_r
            else:
                draw_ch = ch
            _puts(win, _gr(off_y, py), _gc(off_x, col), draw_ch, attr)


# ─── 玩家 ───

def _draw_player(win, off_y: int, off_x: int, player: Player, frame: int):
    px, py = int(player.x), int(player.y)
    if not (0 <= py < SCREEN_HEIGHT and 1 <= px < SCREEN_WIDTH - 1):
        return

    if player.invincible_frames > 0:
        # 無敵閃爍：交替顯示反白
        attr = (curses.color_pair(C_INVINCIBLE) | curses.A_BOLD
                if (frame // 2) % 2 == 0
                else curses.color_pair(C_PLAYER) | curses.A_BOLD)
    else:
        attr = curses.color_pair(C_PLAYER) | curses.A_BOLD

    # 玩家角色下方畫「影子」線，增加立體感
    if py + 1 < SCREEN_HEIGHT:
        shadow_attr = curses.color_pair(C_STAR) | curses.A_DIM
        _puts(win, _gr(off_y, py + 1), _gc(off_x, px), "v", shadow_attr)

    _puts(win, _gr(off_y, py), _gc(off_x, px), CHAR_PLAYER, attr)


# ─── 危機警告 ───

def _draw_danger(win, off_y: int, off_x: int, player: Player, frame: int):
    """玩家靠近頂部時顯示危機閃爍警告"""
    if player.y >= SCREEN_HEIGHT * 0.25:
        return
    # 根據接近程度決定閃爍頻率
    blink_rate = 2 if player.y < SCREEN_HEIGHT * 0.1 else 4
    if (frame // blink_rate) % 2 == 0:
        msg = "!! DANGER -- MOVE DOWN !!"
        col = _gc(off_x, max(1, (SCREEN_WIDTH - len(msg)) // 2))
        _puts(win, _gr(off_y, 0), col, msg,
              curses.color_pair(C_DANGER) | curses.A_BOLD | curses.A_REVERSE)


# ─── 狀態列 ───

def _draw_status(win, off_y: int, off_x: int, player: Player,
                 score: int, level: int, platform_speed: float):
    """在邊框內的狀態列繪製 HP / 分數 / 等級"""
    status_row = off_y + 3 + SCREEN_HEIGHT

    # HP 心形符號
    hp_full  = curses.color_pair(C_HP_FULL) | curses.A_BOLD
    hp_empty = curses.color_pair(C_DEFAULT) | curses.A_DIM
    col = off_x + 2
    _puts(win, status_row, col, "HP:", curses.color_pair(C_LABEL))
    col += 3
    for i in range(PLAYER_HP_MAX):
        ch   = "v" if i < player.hp else "."
        attr = hp_full if i < player.hp else hp_empty
        _puts(win, status_row, col + i, ch, attr)

    # 分數
    col += PLAYER_HP_MAX + 2
    score_str = f"SCORE:{score:06d}"
    _puts(win, status_row, col, score_str, curses.color_pair(C_UI) | curses.A_BOLD)

    # 等級
    col += len(score_str) + 2
    _puts(win, status_row, col, f"LV:{level}",
          curses.color_pair(C_TITLE) | curses.A_BOLD)

    # 速度指示（讓玩家感知難度）
    col += 7
    speed_pct = int(platform_speed / 0.018 * 100)
    _puts(win, status_row, col, f"SPD:{speed_pct}%",
          curses.color_pair(C_PLAT_MOVING))


# ─── 圖例（遊戲右側，若空間夠）───

_LEGEND = [
    (PLATFORM_NORMAL,  "= Normal"),
    (PLATFORM_DAMAGE,  "# Damage"),
    (PLATFORM_HEAL,    "+ Heal"),
    (PLATFORM_CRUMBLE, "~ Crumble"),
    (PLATFORM_SPRING,  "^ Spring"),
    (PLATFORM_MOVING,  "- Moving"),
]


def _draw_legend(win, off_y: int, off_x: int):
    h, w = win.getmaxyx()
    legend_col = off_x + SCREEN_WIDTH + 3
    if legend_col + 12 >= w:
        return
    _puts(win, off_y + 2, legend_col, "PLATFORMS", curses.color_pair(C_LABEL))
    _puts(win, off_y + 3, legend_col, "---------", curses.color_pair(C_STAR) | curses.A_DIM)
    for i, (pt, label) in enumerate(_LEGEND):
        _puts(win, off_y + 4 + i, legend_col, label, _platform_attr(pt))


# ─── 主遊戲渲染 ───

def render_game(win, player: Player, platforms: List[Platform],
                score: int, level: int, frame: int,
                platform_speed: float = PLATFORM_SPEED_INITIAL):
    """遊戲主畫面渲染"""
    win.erase()
    off_y, off_x = _get_offsets(win)

    _draw_frame(win, off_y, off_x)
    _draw_bg(win, off_y, off_x, frame)
    _draw_platforms(win, off_y, off_x, platforms)
    _draw_player(win, off_y, off_x, player, frame)
    _draw_danger(win, off_y, off_x, player, frame)
    _draw_status(win, off_y, off_x, player, score, level, platform_speed)
    _draw_legend(win, off_y, off_x)

    win.refresh()


# ─── 選單畫面 ───

_MENU_ART = [
    r" _____ _        _          ____                            _  ",
    r"/ ____| |      (_)        |  _ \                          | | ",
    r"| (___ | |_ __ _ _ _ __   | | | | ___  ___ ___ ___ _ __  | |_",
    r" \___ \| __/ _` | | '__| | | | |/ _ \/ __/ __/ _ \ '_ \ | __|",
    r" ____) | || (_| | | |    | |_| |  __/\__ \__ \  __/ | | | |_ ",
    r"|_____/ \__\__,_|_|_|    |____/ \___||___/___/\___|_| |_| \__|",
]

_CONTROLS = [
    ("  [a / d]", "  Move Left / Right"),
    ("  [arrow]", "  Also works"),
    ("  [p]    ", "  Pause / Resume"),
    ("  [q]    ", "  Quit"),
]

_PLAT_LEGEND_MENU = [
    ("=", PLATFORM_NORMAL,  " Normal  "),
    ("#", PLATFORM_DAMAGE,  " Damage  "),
    ("+", PLATFORM_HEAL,    " Heal    "),
    ("~", PLATFORM_CRUMBLE, " Crumble "),
    ("^", PLATFORM_SPRING,  " Spring  "),
    ("-", PLATFORM_MOVING,  " Moving  "),
]


def render_menu(win, scores: list):
    win.erase()
    h, w = win.getmaxyx()
    ba = curses.color_pair(C_BORDER) | curses.A_BOLD
    ta = curses.color_pair(C_TITLE)  | curses.A_BOLD
    la = curses.color_pair(C_LABEL)  | curses.A_BOLD
    da = curses.color_pair(C_DEFAULT)

    # ASCII art 標題（左側對齊並置中）
    art_w = max(len(l) for l in _MENU_ART)
    art_col = max(0, (w - art_w) // 2)
    art_row = max(1, (h - 22) // 2)
    for i, line in enumerate(_MENU_ART):
        _puts(win, art_row + i, art_col, line, ta)

    # 中文副標題
    subtitle = "  小朋友下樓梯   TERMINAL EDITION  "
    sub_dw = _display_width(subtitle)
    sub_col = max(0, (w - sub_dw) // 2)
    _puts(win, art_row + len(_MENU_ART), sub_col, subtitle, la)

    # 分隔線
    sep_row = art_row + len(_MENU_ART) + 1
    sep = CHAR_BORDER_H * min(art_w, w - 2)
    _puts(win, sep_row, art_col, sep, ba)

    # 操作說明
    ctrl_row = sep_row + 1
    for i, (key, desc) in enumerate(_CONTROLS):
        _puts(win, ctrl_row + i, art_col + 2, key,
              curses.color_pair(C_UI) | curses.A_BOLD)
        _puts(win, ctrl_row + i, art_col + 2 + len(key), desc, da)

    # 平台圖例（橫排）
    plat_row = ctrl_row + len(_CONTROLS) + 1
    _puts(win, plat_row, art_col + 2, "Platforms: ", la)
    pc = art_col + 13
    for ch, pt, label in _PLAT_LEGEND_MENU:
        attr = _platform_attr(pt)
        _puts(win, plat_row, pc, ch + label, attr)
        pc += 1 + len(label)

    # 排行榜
    lb_row = plat_row + 2
    if scores:
        _puts(win, lb_row, art_col + 2, "TOP 5 SCORES", la)
        medals = ["#1", "#2", "#3", "#4", "#5"]
        for rank, s in enumerate(scores[:5], 0):
            _puts(win, lb_row + 1 + rank, art_col + 4,
                  f"{medals[rank]}  {s:06d}",
                  curses.color_pair(C_UI) if rank == 0 else da)

    # 按 Enter 開始（底部閃爍）
    enter_row = min(h - 2, lb_row + (len(scores) + 3 if scores else 2))
    _puts(win, enter_row, art_col + 2,
          ">>  Press ENTER to Start  <<",
          curses.color_pair(C_PLAYER) | curses.A_BOLD)

    win.refresh()


# ─── 暫停畫面 ───

def render_pause(win):
    h, w = win.getmaxyx()
    lines = [
        "╔═══════════════════╗",
        "║      PAUSED       ║",
        "║  [p] to continue  ║",
        "╚═══════════════════╝",
    ]
    sr = h // 2 - len(lines) // 2
    lw = max(len(l) for l in lines)
    sc = max(0, (w - lw) // 2)
    attr = curses.color_pair(C_BORDER) | curses.A_BOLD
    for i, line in enumerate(lines):
        _puts(win, sr + i, sc, line, attr)
    win.refresh()


# ─── Game Over 畫面 ───

_GAMEOVER_ART = [
    r" _____   ___  __  __ _____    _____   _____ ______ _____  ",
    r"|  __ \ / _ \|  \/  | ____|  / _ \ \ / / __|  ____|  __ \ ",
    r"| |  \// /_\ \ \  / | |__   | | | \ V /| |__| |__  | |__) |",
    r"| | __ |  _  | |\/| |  __|  | | | |> < |  __|  __| |  _  / ",
    r"| |_\ \| | | | |  | | |___  | |_| / . \| |__| |____| | \ \ ",
    r" \____/\_| |_/_|  |_|_____|  \___/_/ \_\____|______|_|  \_\\",
]


def render_gameover(win, score: int, scores: list):
    win.erase()
    h, w = win.getmaxyx()
    ra = curses.color_pair(C_PLAT_DAMAGE) | curses.A_BOLD
    ua = curses.color_pair(C_UI)
    da = curses.color_pair(C_DEFAULT)
    ba = curses.color_pair(C_BORDER) | curses.A_BOLD

    art_w = max(len(l) for l in _GAMEOVER_ART)
    art_col = max(0, (w - art_w) // 2)
    art_row = max(1, (h - 20) // 2)
    for i, line in enumerate(_GAMEOVER_ART):
        _puts(win, art_row + i, art_col, line, ra)

    sep_row = art_row + len(_GAMEOVER_ART) + 1
    _puts(win, sep_row, art_col,
          CHAR_BORDER_H * min(art_w, w - art_col - 1), ba)

    score_row = sep_row + 1
    score_str = f"FINAL SCORE:  {score:06d}"
    _puts(win, score_row, art_col + 4, score_str, ua | curses.A_BOLD)

    # 排名提示
    rank_pos = None
    sorted_scores = sorted(scores, reverse=True)
    if score in sorted_scores:
        rank_pos = sorted_scores.index(score) + 1

    if rank_pos:
        _puts(win, score_row + 1, art_col + 4,
              f">> Ranked #{rank_pos} in Leaderboard! <<",
              curses.color_pair(C_PLAYER) | curses.A_BOLD)

    # 排行榜
    lb_row = score_row + 3
    _puts(win, lb_row, art_col + 4, "TOP 5 LEADERBOARD:", ua)
    medals = ["#1", "#2", "#3", "#4", "#5"]
    for i, s in enumerate(sorted_scores[:5]):
        attr = curses.color_pair(C_UI) | curses.A_BOLD if i == 0 else da
        marker = " <--" if s == score and rank_pos == i + 1 else ""
        _puts(win, lb_row + 1 + i, art_col + 6,
              f"{medals[i]}  {s:06d}{marker}", attr)

    # 操作提示
    hint_row = lb_row + 8
    _puts(win, hint_row, art_col + 4,
          "[r] Restart    [q] Quit",
          curses.color_pair(C_TITLE) | curses.A_BOLD)

    win.refresh()

