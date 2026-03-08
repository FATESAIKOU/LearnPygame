"""
renderer.py - 終端機畫面渲染

特色：
- 自動置中遊戲區域
- 雙線方框邊框（動態色彩）
- 多層視差星空背景
- 粒子特效系統
- 螢幕震動 & 閃光
- 連擊指示器
- 動態 HP 條
"""

import curses
import math
import unicodedata
from typing import List
from constants import *
from entities import Player, Platform, Particle

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
C_COMBO        = 17
C_FLASH_DMG    = 18
C_FLASH_HEAL   = 19
C_BORDER_ALT   = 20
C_TRAIL        = 21
C_SCORE_POP    = 22


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
    curses.init_pair(C_COMBO,        curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_FLASH_DMG,    curses.COLOR_WHITE,   curses.COLOR_RED)
    curses.init_pair(C_FLASH_HEAL,   curses.COLOR_WHITE,   curses.COLOR_GREEN)
    curses.init_pair(C_BORDER_ALT,   curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_TRAIL,        curses.COLOR_BLUE,    -1)
    curses.init_pair(C_SCORE_POP,    curses.COLOR_YELLOW,  -1)


# ─── 座標工具 ───

def _display_width(s: str) -> int:
    total = 0
    for ch in s:
        ea = unicodedata.east_asian_width(ch)
        total += 2 if ea in ('W', 'F') else 1
    return total


def _get_offsets(win, shake_x: int = 0, shake_y: int = 0):
    """計算使遊戲區域置中的偏移量，加上震動偏移"""
    h, w = win.getmaxyx()
    total_h = SCREEN_HEIGHT + 5
    total_w = SCREEN_WIDTH + 2
    off_y = max(0, (h - total_h) // 2) + shake_y
    off_x = max(0, (w - total_w) // 2) + shake_x
    return off_y, off_x


def _gr(off_y: int, row: int) -> int:
    return off_y + 2 + row


def _gc(off_x: int, col: int) -> int:
    return off_x + 1 + col


# ─── 安全繪製 ───

def _puts(win, row: int, col: int, text: str, attr: int):
    try:
        h, w = win.getmaxyx()
        if row < 0 or row >= h or col < 0:
            return
        # 截斷避免超出右邊界
        max_len = w - col - 1
        if max_len <= 0:
            return
        if len(text) > max_len:
            text = text[:max_len]
        win.addstr(row, col, text, attr)
    except curses.error:
        pass


# ─── 顏色循環工具 ───

_RAINBOW_COLORS = [C_PLAT_DAMAGE, C_UI, C_PLAT_HEAL, C_PLAYER, C_PLAT_SPRING, C_PLAT_MOVING]


def _rainbow_attr(frame: int, offset: int = 0) -> int:
    """根據幀數和偏移量返回彩虹色屬性"""
    idx = ((frame // 3) + offset) % len(_RAINBOW_COLORS)
    return curses.color_pair(_RAINBOW_COLORS[idx]) | curses.A_BOLD


# ─── 邊框 ───

def _draw_frame(win, off_y: int, off_x: int, frame: int = 0, level: int = 1):
    """繪製遊戲區域外框（動態色彩邊框）"""
    h, w = win.getmaxyx()

    # 根據等級切換邊框風格
    if level <= 3:
        ba = curses.color_pair(C_BORDER) | curses.A_BOLD
    elif level <= 6:
        alt = C_BORDER if (frame // 8) % 2 == 0 else C_BORDER_ALT
        ba = curses.color_pair(alt) | curses.A_BOLD
    else:
        ba = _rainbow_attr(frame)

    # 標題列（帶動態效果）
    title_ascii = "* STAIR DESCENT  |  TERMINAL EDITION *"
    tcol = off_x + max(0, (SCREEN_WIDTH + 2 - len(title_ascii)) // 2)
    if level >= 5:
        for i, ch in enumerate(title_ascii):
            _puts(win, off_y, tcol + i, ch, _rainbow_attr(frame, i))
    else:
        ta = curses.color_pair(C_TITLE) | curses.A_BOLD
        _puts(win, off_y, tcol, title_ascii, ta)

    # 上邊框
    _puts(win, off_y + 1, off_x,
          CHAR_BORDER_TL + CHAR_BORDER_H * SCREEN_WIDTH + CHAR_BORDER_TR, ba)

    # 左右側線（遊戲區域）— 高等級時動態閃爍
    for r in range(SCREEN_HEIGHT):
        if level >= 8:
            side_attr = _rainbow_attr(frame, r)
        else:
            side_attr = ba
        _puts(win, _gr(off_y, r), off_x, CHAR_BORDER_V, side_attr)
        _puts(win, _gr(off_y, r), off_x + SCREEN_WIDTH + 1, CHAR_BORDER_V, side_attr)

    # 分隔線
    _puts(win, off_y + 2 + SCREEN_HEIGHT, off_x,
          CHAR_BORDER_ML + CHAR_BORDER_H * SCREEN_WIDTH + CHAR_BORDER_MR, ba)

    # 狀態列左右框
    _puts(win, off_y + 3 + SCREEN_HEIGHT, off_x, CHAR_BORDER_V, ba)
    _puts(win, off_y + 3 + SCREEN_HEIGHT, off_x + SCREEN_WIDTH + 1, CHAR_BORDER_V, ba)

    # 下邊框
    _puts(win, off_y + 4 + SCREEN_HEIGHT, off_x,
          CHAR_BORDER_BL + CHAR_BORDER_H * SCREEN_WIDTH + CHAR_BORDER_BR, ba)


# ─── 多層視差星空 ───

_STAR_LAYERS = None


def _build_star_layers():
    """建立三層星空（遠/中/近），密度和亮度不同"""
    global _STAR_LAYERS
    layers = [[], [], []]
    configs = [
        (60, [".", ".", ","]),     # 遠景：稀疏暗星
        (35, [".", "*", ","]),     # 中景：中等密度
        (25, ["*", "+", "o"]),    # 近景：明亮大星
    ]
    for layer_idx, (density, chars) in enumerate(configs):
        for r in range(SCREEN_HEIGHT):
            for c in range(1, SCREEN_WIDTH - 1):
                h = ((r + layer_idx * 137) * 2654435761 ^ (c + layer_idx * 97) * 1013904223) & 0xFFFFFF
                if h % density == 0:
                    ch = chars[h % len(chars)]
                    layers[layer_idx].append((r, c, ch))
    _STAR_LAYERS = layers


def _draw_bg(win, off_y: int, off_x: int, frame: int):
    """繪製多層視差星空"""
    global _STAR_LAYERS
    if _STAR_LAYERS is None:
        _build_star_layers()

    speeds = [30, 15, 8]  # 越近移動越快（除數越小 → 移動越快）
    brightnesses = [curses.A_DIM, 0, curses.A_BOLD]

    for layer_idx, stars in enumerate(_STAR_LAYERS):
        shift = frame // speeds[layer_idx]
        attr = curses.color_pair(C_STAR) | brightnesses[layer_idx]
        for (r, c, ch) in stars:
            draw_r = (r - shift) % SCREEN_HEIGHT
            _puts(win, _gr(off_y, draw_r), _gc(off_x, c), ch, attr)


# ─── 粒子渲染 ───

_PARTICLE_COLOR_MAP = {
    3: C_PLAT_NORMAL,   # landing dust
    4: C_PLAT_DAMAGE,   # damage sparks
    5: C_PLAT_HEAL,     # heal sparkles
    6: C_PLAT_CRUMBLE,  # crumble debris
    7: C_PLAT_SPRING,   # spring burst
    2: C_PLAYER,        # trail
}


def _draw_particles(win, off_y: int, off_x: int, particles: List[Particle]):
    for p in particles:
        if not p.alive:
            continue
        px, py = int(p.x), int(p.y)
        if not (0 <= py < SCREEN_HEIGHT and 1 <= px < SCREEN_WIDTH - 1):
            continue

        color = _PARTICLE_COLOR_MAP.get(p.color_id, C_DEFAULT)
        # 粒子隨年齡變暗
        if p.age_ratio > 0.7:
            brightness = curses.A_DIM
        elif p.age_ratio > 0.4:
            brightness = 0
        else:
            brightness = curses.A_BOLD

        attr = curses.color_pair(color) | brightness
        _puts(win, _gr(off_y, py), _gc(off_x, px), p.char, attr)


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


_PLAT_CAP = {
    PLATFORM_NORMAL:  ("[", "]"),
    PLATFORM_DAMAGE:  ("<", ">"),
    PLATFORM_HEAL:    ("(", ")"),
    PLATFORM_CRUMBLE: ("{", "}"),
    PLATFORM_SPRING:  ("/", "\\"),
    PLATFORM_MOVING:  ("<", ">"),
}


def _draw_platforms(win, off_y: int, off_x: int, platforms: List[Platform], frame: int):
    for plat in platforms:
        if not plat.active:
            continue
        py = int(plat.y)
        if not (0 <= py < SCREEN_HEIGHT):
            continue

        attr = _platform_attr(plat.platform_type)
        ch = plat.char()
        cap_l, cap_r = _PLAT_CAP.get(plat.platform_type, ("[", "]"))
        px = int(plat.x)

        # 崩壞平台閃爍效果
        if plat.crumble_timer >= 0:
            if (frame // 2) % 2 == 0:
                attr = curses.color_pair(C_PLAT_CRUMBLE) | curses.A_DIM
            else:
                continue  # 隱藏幀

        # 移動平台動態 glow
        if plat.moving and (frame // 4) % 2 == 0:
            attr |= curses.A_REVERSE

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

        # 傷害平台呼吸光暈（上下各一行微弱提示）
        if plat.platform_type == PLATFORM_DAMAGE:
            glow_attr = curses.color_pair(C_PLAT_DAMAGE) | curses.A_DIM
            pulse = abs(math.sin(frame * 0.15)) > 0.5
            if pulse:
                center = px + plat.width // 2
                for dc in [-1, 0, 1]:
                    gc = center + dc
                    if 1 <= gc < SCREEN_WIDTH - 1:
                        if py - 1 >= 0:
                            _puts(win, _gr(off_y, py - 1), _gc(off_x, gc), ".", glow_attr)

        # 補血平台柔光
        if plat.platform_type == PLATFORM_HEAL:
            glow_attr = curses.color_pair(C_PLAT_HEAL) | curses.A_DIM
            pulse = abs(math.sin(frame * 0.12)) > 0.5
            if pulse:
                center = px + plat.width // 2
                for dc in [-1, 0, 1]:
                    gc = center + dc
                    if 1 <= gc < SCREEN_WIDTH - 1:
                        if py - 1 >= 0:
                            _puts(win, _gr(off_y, py - 1), _gc(off_x, gc), "+", glow_attr)

        # 彈簧平台脈動
        if plat.platform_type == PLATFORM_SPRING:
            if (frame // 6) % 3 == 0:
                center = px + plat.width // 2
                if 1 <= center < SCREEN_WIDTH - 1 and py - 1 >= 0:
                    _puts(win, _gr(off_y, py - 1), _gc(off_x, center), "^",
                          curses.color_pair(C_PLAT_SPRING) | curses.A_BOLD)


# ─── 玩家 ───

# 玩家動畫幀（面朝方向）
_PLAYER_FRAMES = {
    -1: ["<", "d"],   # 面左
     0: ["@", "A"],   # 正面
     1: [">", "b"],   # 面右
}

_PLAYER_FALL_CHARS = ["V", "Y", "T"]  # 下落時的字元


def _draw_player(win, off_y: int, off_x: int, player: Player, frame: int):
    px, py = int(player.x), int(player.y)
    if not (0 <= py < SCREEN_HEIGHT and 1 <= px < SCREEN_WIDTH - 1):
        return

    # 選擇角色字元
    if player.vy > 1.5:
        ch = _PLAYER_FALL_CHARS[(frame // 3) % len(_PLAYER_FALL_CHARS)]
    else:
        frames = _PLAYER_FRAMES.get(player.facing, _PLAYER_FRAMES[0])
        ch = frames[(frame // 6) % len(frames)]

    if player.invincible_frames > 0:
        if (frame // 2) % 2 == 0:
            attr = curses.color_pair(C_INVINCIBLE) | curses.A_BOLD
        else:
            attr = curses.color_pair(C_PLAYER) | curses.A_BOLD
    else:
        attr = curses.color_pair(C_PLAYER) | curses.A_BOLD

    # 玩家下方影子
    if py + 1 < SCREEN_HEIGHT:
        shadow_attr = curses.color_pair(C_STAR) | curses.A_DIM
        _puts(win, _gr(off_y, py + 1), _gc(off_x, px), ".", shadow_attr)

    # 頭頂裝飾（高連擊時發光）
    if player.combo >= 5 and py - 1 >= 0:
        crown_ch = "*" if (frame // 4) % 2 == 0 else "^"
        crown_attr = _rainbow_attr(frame)
        _puts(win, _gr(off_y, py - 1), _gc(off_x, px), crown_ch, crown_attr)

    _puts(win, _gr(off_y, py), _gc(off_x, px), ch, attr)


# ─── 連擊指示器 ───

def _draw_combo(win, off_y: int, off_x: int, player: Player, frame: int):
    if player.combo < 2:
        return
    py = max(0, int(player.y) - 2)
    px = int(player.x)

    combo_text = f"x{player.combo}"
    if player.combo >= 10:
        combo_text += "!"
    if player.combo >= 20:
        combo_text = f"x{player.combo}!!"

    # 動態大小 / 閃爍
    if player.combo >= 10:
        attr = _rainbow_attr(frame, 0)
    elif player.combo >= 5:
        attr = curses.color_pair(C_COMBO) | curses.A_BOLD
    else:
        attr = curses.color_pair(C_UI) | curses.A_BOLD

    if 0 <= py < SCREEN_HEIGHT:
        col = max(1, min(SCREEN_WIDTH - len(combo_text) - 1, px - len(combo_text) // 2))
        _puts(win, _gr(off_y, py), _gc(off_x, col), combo_text, attr)


# ─── 危機警告 ───

def _draw_danger(win, off_y: int, off_x: int, player: Player, frame: int):
    if player.y >= SCREEN_HEIGHT * 0.25:
        return
    blink_rate = 2 if player.y < SCREEN_HEIGHT * 0.1 else 4
    if (frame // blink_rate) % 2 == 0:
        msg = "!! DANGER -- MOVE DOWN !!"
        col = _gc(off_x, max(1, (SCREEN_WIDTH - len(msg)) // 2))
        _puts(win, _gr(off_y, 0), col, msg,
              curses.color_pair(C_DANGER) | curses.A_BOLD | curses.A_REVERSE)

    # 側邊警告線
    if player.y < SCREEN_HEIGHT * 0.15:
        danger_attr = curses.color_pair(C_DANGER) | curses.A_BOLD
        for r in range(min(3, SCREEN_HEIGHT)):
            if (frame + r) % 3 == 0:
                _puts(win, _gr(off_y, r), _gc(off_x, 1), "!", danger_attr)
                _puts(win, _gr(off_y, r), _gc(off_x, SCREEN_WIDTH - 2), "!", danger_attr)


# ─── 速度線（高速時的側邊裝飾）───

def _draw_speed_lines(win, off_y: int, off_x: int, platform_speed: float, frame: int):
    """高速時在兩側繪製速度線"""
    if platform_speed < 0.03:
        return
    intensity = min(1.0, (platform_speed - 0.03) / 0.03)
    line_count = int(intensity * 6) + 1
    attr = curses.color_pair(C_STAR) | curses.A_DIM

    for i in range(line_count):
        r = (frame * 2 + i * 4) % SCREEN_HEIGHT
        if r < SCREEN_HEIGHT:
            _puts(win, _gr(off_y, r), _gc(off_x, 2), "|", attr)
            _puts(win, _gr(off_y, r), _gc(off_x, SCREEN_WIDTH - 3), "|", attr)


# ─── 螢幕閃光覆蓋 ───

def _draw_flash(win, off_y: int, off_x: int, flash_type: str, flash_frames: int):
    """在遊戲區域上覆蓋閃光效果"""
    if flash_frames <= 0:
        return
    if flash_type == "damage":
        attr = curses.color_pair(C_FLASH_DMG)
    elif flash_type == "heal":
        attr = curses.color_pair(C_FLASH_HEAL)
    else:
        return

    # 只在前幾幀覆蓋邊緣
    if flash_frames >= SCREEN_FLASH_FRAMES - 1:
        # 全亮閃光 — 邊框閃
        for r in range(SCREEN_HEIGHT):
            _puts(win, _gr(off_y, r), _gc(off_x, 1), " ", attr)
            _puts(win, _gr(off_y, r), _gc(off_x, SCREEN_WIDTH - 2), " ", attr)


# ─── 狀態列 ───

def _draw_status(win, off_y: int, off_x: int, player: Player,
                 score: int, level: int, platform_speed: float, frame: int):
    status_row = off_y + 3 + SCREEN_HEIGHT

    # HP：動態心形（低血量時閃爍）
    hp_full  = curses.color_pair(C_HP_FULL) | curses.A_BOLD
    hp_empty = curses.color_pair(C_DEFAULT) | curses.A_DIM
    hp_crit  = curses.color_pair(C_DANGER)  | curses.A_BOLD | curses.A_REVERSE

    col = off_x + 2
    _puts(win, status_row, col, "HP:", curses.color_pair(C_LABEL))
    col += 3

    for i in range(PLAYER_HP_MAX):
        if i < player.hp:
            # 低血量心跳效果
            if player.hp <= 2 and (frame // 3) % 2 == 0:
                ch, attr = "<3", hp_crit
            else:
                ch, attr = "<3", hp_full
        else:
            ch, attr = "..", hp_empty
        _puts(win, status_row, col, ch, attr)
        col += 2

    col += 1

    # 分數（大數字時帶顏色）
    score_str = f"SCORE:{score:07d}"
    score_attr = curses.color_pair(C_UI) | curses.A_BOLD
    if score >= 50000:
        score_attr = _rainbow_attr(frame)
    _puts(win, status_row, col, score_str, score_attr)

    # 等級
    col += len(score_str) + 1
    level_str = f"LV:{level}"
    if level >= 5:
        level_attr = curses.color_pair(C_COMBO) | curses.A_BOLD
    else:
        level_attr = curses.color_pair(C_TITLE) | curses.A_BOLD
    _puts(win, status_row, col, level_str, level_attr)

    # 速度條
    col += len(level_str) + 1
    speed_pct = min(100, int(platform_speed / PLATFORM_SPEED_MAX * 100))
    bar_len = 8
    filled = int(speed_pct / 100 * bar_len)
    bar = ">" * filled + "-" * (bar_len - filled)
    speed_color = C_PLAT_HEAL if speed_pct < 50 else (C_UI if speed_pct < 80 else C_DANGER)
    _puts(win, status_row, col, f"[{bar}]", curses.color_pair(speed_color))


# ─── 圖例 ───

_LEGEND = [
    (PLATFORM_NORMAL,  "= Normal"),
    (PLATFORM_DAMAGE,  "# Damage"),
    (PLATFORM_HEAL,    "+ Heal"),
    (PLATFORM_CRUMBLE, "~ Crumble"),
    (PLATFORM_SPRING,  "^ Spring"),
    (PLATFORM_MOVING,  "- Moving"),
]


def _draw_legend(win, off_y: int, off_x: int, frame: int):
    h, w = win.getmaxyx()
    legend_col = off_x + SCREEN_WIDTH + 4
    if legend_col + 14 >= w:
        return

    _puts(win, off_y + 2, legend_col, "PLATFORMS", curses.color_pair(C_LABEL) | curses.A_BOLD)
    _puts(win, off_y + 3, legend_col, "---------", curses.color_pair(C_STAR) | curses.A_DIM)
    for i, (pt, label) in enumerate(_LEGEND):
        attr = _platform_attr(pt)
        _puts(win, off_y + 4 + i, legend_col, label, attr)

    # 操作提示
    ctrl_row = off_y + 4 + len(_LEGEND) + 1
    _puts(win, ctrl_row, legend_col, "CONTROLS", curses.color_pair(C_LABEL) | curses.A_BOLD)
    _puts(win, ctrl_row + 1, legend_col, "---------", curses.color_pair(C_STAR) | curses.A_DIM)
    ctrls = [
        ("[a/d]  Move",),
        ("[p]    Pause",),
        ("[q]    Quit",),
    ]
    for i, (line,) in enumerate(ctrls):
        _puts(win, ctrl_row + 2 + i, legend_col, line, curses.color_pair(C_DEFAULT))


# ─── 主遊戲渲染 ───

def render_game(win, player: Player, platforms: List[Platform],
                score: int, level: int, frame: int,
                platform_speed: float = PLATFORM_SPEED_INITIAL,
                particles=None,
                shake_x: int = 0, shake_y: int = 0,
                flash_type: str = "", flash_frames: int = 0):
    """遊戲主畫面渲染"""
    win.erase()
    off_y, off_x = _get_offsets(win, shake_x, shake_y)

    _draw_frame(win, off_y, off_x, frame, level)
    _draw_bg(win, off_y, off_x, frame)
    _draw_speed_lines(win, off_y, off_x, platform_speed, frame)
    _draw_platforms(win, off_y, off_x, platforms, frame)

    if particles:
        _draw_particles(win, off_y, off_x, particles)

    _draw_player(win, off_y, off_x, player, frame)
    _draw_combo(win, off_y, off_x, player, frame)
    _draw_danger(win, off_y, off_x, player, frame)
    _draw_flash(win, off_y, off_x, flash_type, flash_frames)
    _draw_status(win, off_y, off_x, player, score, level, platform_speed, frame)
    _draw_legend(win, off_y, off_x, frame)

    win.refresh()


# ─── 選單畫面 ───

_MENU_ART = [
    r"  _____ _        _       ",
    r" / ____| |      (_)      ",
    r"| (___ | |_ __ _ _ _ __  ",
    r" \___ \| __/ _` | | '__| ",
    r" ____) | || (_| | | |    ",
    r"|_____/ \__\__,_|_|_|    ",
    r"",
    r"  ____                            _   ",
    r" |  _ \  ___  ___  ___ ___ _ __ | |_  ",
    r" | | | |/ _ \/ __|/ __/ _ \ '_ \| __| ",
    r" | |_| |  __/\__ \ (_|  __/ | | | |_  ",
    r" |____/ \___||___/\___\___|_| |_|\__| ",
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

_menu_frame = 0


def render_menu(win, scores: list):
    global _menu_frame
    _menu_frame += 1
    win.erase()
    h, w = win.getmaxyx()
    la = curses.color_pair(C_LABEL)  | curses.A_BOLD
    da = curses.color_pair(C_DEFAULT)
    ba = curses.color_pair(C_BORDER) | curses.A_BOLD

    # 星空背景（全畫面）
    _draw_menu_bg(win, h, w, _menu_frame)

    # ASCII art 標題（彩虹動態）
    art_w = max(len(l) for l in _MENU_ART)
    art_col = max(0, (w - art_w) // 2)
    art_row = max(1, (h - 28) // 2)
    for i, line in enumerate(_MENU_ART):
        for j, ch in enumerate(line):
            if ch != ' ':
                _puts(win, art_row + i, art_col + j, ch, _rainbow_attr(_menu_frame, i + j))
            else:
                _puts(win, art_row + i, art_col + j, ch, da)

    # 中文副標題
    subtitle = "  小朋友下樓梯   TERMINAL EDITION  "
    sub_dw = _display_width(subtitle)
    sub_col = max(0, (w - sub_dw) // 2)
    _puts(win, art_row + len(_MENU_ART) + 1, sub_col, subtitle, la)

    # 分隔線
    sep_row = art_row + len(_MENU_ART) + 2
    sep = CHAR_BORDER_H * min(art_w, w - 2)
    _puts(win, sep_row, art_col, sep, ba)

    # 操作說明
    ctrl_row = sep_row + 1
    for i, (key, desc) in enumerate(_CONTROLS):
        _puts(win, ctrl_row + i, art_col + 2, key,
              curses.color_pair(C_UI) | curses.A_BOLD)
        _puts(win, ctrl_row + i, art_col + 2 + len(key), desc, da)

    # 平台圖例
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
            medal_attr = _rainbow_attr(_menu_frame, rank) if rank == 0 else da
            _puts(win, lb_row + 1 + rank, art_col + 4,
                  f"{medals[rank]}  {s:07d}", medal_attr)

    # 動態 Enter 提示
    enter_row = min(h - 2, lb_row + (len(scores) + 3 if scores else 2))
    enter_text = ">>  Press ENTER to Start  <<"
    if (_menu_frame // 8) % 2 == 0:
        enter_attr = curses.color_pair(C_PLAYER) | curses.A_BOLD
    else:
        enter_attr = curses.color_pair(C_PLAT_SPRING) | curses.A_BOLD
    _puts(win, enter_row, art_col + 2, enter_text, enter_attr)

    win.refresh()


def _draw_menu_bg(win, h: int, w: int, frame: int):
    """選單畫面的動態星空"""
    attr_dim = curses.color_pair(C_STAR) | curses.A_DIM
    attr_normal = curses.color_pair(C_STAR)
    shift = frame // 12
    for r in range(h):
        for c in range(w):
            hv = ((r + shift) * 2654435761 ^ c * 1013904223) & 0xFFFFFF
            if hv % 80 == 0:
                ch = "." if hv % 3 else "*"
                attr = attr_dim if hv % 5 else attr_normal
                _puts(win, r, c, ch, attr)


# ─── 暫停畫面 ───

_pause_frame = 0


def render_pause(win):
    global _pause_frame
    _pause_frame += 1
    h, w = win.getmaxyx()
    lines = [
        "╔═══════════════════════╗",
        "║                       ║",
        "║      ◆  PAUSED  ◆     ║",
        "║                       ║",
        "║   [p] to continue     ║",
        "║   [q] to quit         ║",
        "║                       ║",
        "╚═══════════════════════╝",
    ]
    sr = h // 2 - len(lines) // 2
    lw = max(len(l) for l in lines)
    sc = max(0, (w - lw) // 2)
    for i, line in enumerate(lines):
        attr = _rainbow_attr(_pause_frame, i)
        _puts(win, sr + i, sc, line, attr)
    win.refresh()


# ─── Game Over 畫面 ───

_GAMEOVER_ART = [
    r"  ____    _    __  __ _____  ",
    r" / ___|  / \  |  \/  | ____| ",
    r"| |  _  / _ \ | |\/| |  _|   ",
    r"| |_| |/ ___ \| |  | | |___  ",
    r" \____/_/   \_\_|  |_|_____| ",
    r"",
    r"  _____     _______ ____  ",
    r" / _ \ \   / / ____|  _ \ ",
    r"| | | \ \ / /|  _| | |_) |",
    r"| |_| |\ V / | |___|  _ < ",
    r" \___/  \_/  |_____|_| \_\\",
]

_gameover_frame = 0


def render_gameover(win, score: int, scores: list):
    global _gameover_frame
    _gameover_frame += 1
    win.erase()
    h, w = win.getmaxyx()
    ra = curses.color_pair(C_PLAT_DAMAGE) | curses.A_BOLD
    ua = curses.color_pair(C_UI)
    da = curses.color_pair(C_DEFAULT)
    ba = curses.color_pair(C_BORDER) | curses.A_BOLD

    # 暗星空背景
    _draw_menu_bg(win, h, w, _gameover_frame)

    art_w = max(len(l) for l in _GAMEOVER_ART)
    art_col = max(0, (w - art_w) // 2)
    art_row = max(1, (h - 24) // 2)

    # 動態紅色閃爍標題
    for i, line in enumerate(_GAMEOVER_ART):
        for j, ch in enumerate(line):
            if ch != ' ':
                if (_gameover_frame // 4 + i + j) % 3 == 0:
                    attr = curses.color_pair(C_DANGER) | curses.A_BOLD
                else:
                    attr = curses.color_pair(C_PLAT_DAMAGE) | curses.A_BOLD
                _puts(win, art_row + i, art_col + j, ch, attr)

    sep_row = art_row + len(_GAMEOVER_ART) + 1
    _puts(win, sep_row, art_col,
          CHAR_BORDER_H * min(art_w, w - art_col - 1), ba)

    score_row = sep_row + 1
    score_str = f"FINAL SCORE:  {score:07d}"
    # 高分彩虹效果
    if score >= 30000:
        for i, ch in enumerate(score_str):
            _puts(win, score_row, art_col + 4 + i, ch, _rainbow_attr(_gameover_frame, i))
    else:
        _puts(win, score_row, art_col + 4, score_str, ua | curses.A_BOLD)

    # 排名
    rank_pos = None
    sorted_scores = sorted(scores, reverse=True)
    if score in sorted_scores:
        rank_pos = sorted_scores.index(score) + 1

    if rank_pos:
        rank_text = f">> Ranked #{rank_pos} in Leaderboard! <<"
        rank_attr = _rainbow_attr(_gameover_frame) if rank_pos <= 3 else (curses.color_pair(C_PLAYER) | curses.A_BOLD)
        _puts(win, score_row + 1, art_col + 4, rank_text, rank_attr)

    # 排行榜
    lb_row = score_row + 3
    _puts(win, lb_row, art_col + 4, "TOP 5 LEADERBOARD:", ua)
    medals = ["#1", "#2", "#3", "#4", "#5"]
    for i, s in enumerate(sorted_scores[:5]):
        if i == 0:
            attr = _rainbow_attr(_gameover_frame, i)
        else:
            attr = da
        marker = " <--" if s == score and rank_pos == i + 1 else ""
        _puts(win, lb_row + 1 + i, art_col + 6,
              f"{medals[i]}  {s:07d}{marker}", attr)

    # 操作提示
    hint_row = lb_row + 8
    hint_text = "[r] Restart    [q] Quit"
    if (_gameover_frame // 10) % 2 == 0:
        hint_attr = curses.color_pair(C_TITLE) | curses.A_BOLD
    else:
        hint_attr = curses.color_pair(C_PLAYER) | curses.A_BOLD
    _puts(win, hint_row, art_col + 4, hint_text, hint_attr)

    win.refresh()

