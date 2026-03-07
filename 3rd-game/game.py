"""
game.py - 主遊戲迴圈與狀態管理

狀態機：
  MENU → PLAYING → PAUSED → PLAYING
                 → GAMEOVER → MENU / 退出
"""

import time
import json
import os
import random
from typing import List

from constants import *
from entities import Player, Platform, make_platform
from renderer import (
    init_colors, render_game, render_menu,
    render_pause, render_gameover,
)
from input_handler import InputHandler


class GameState:
    """所有遊戲執行期資料"""

    def __init__(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.platforms: List[Platform] = []
        self.scroll_offset = 0.0     # 世界向上捲動的累計量（浮點）
        self.platform_speed = PLATFORM_SPEED_INITIAL
        self.score = 0
        self.level = 1
        self.frame = 0

        # 下一個平台的 y 座標（世界座標，往下為大）
        self._next_platform_y = SCREEN_HEIGHT - 1
        self._init_platforms()

    def _init_platforms(self):
        """初始生成幾個平台讓玩家有地方站"""
        # 底部保底平台（讓玩家一開始有地方站）
        start_plat = Platform(
            x=SCREEN_WIDTH // 2 - 5,
            y=SCREEN_HEIGHT // 2 + 2,
            width=10,
            platform_type=PLATFORM_NORMAL,
        )
        self.platforms.append(start_plat)
        # 玩家站在起始平台上
        self.player.y = start_plat.y - 1
        self.player.on_platform = True

        # 往下預填平台
        y = SCREEN_HEIGHT - 1
        while y < SCREEN_HEIGHT + 20:
            self.platforms.append(make_platform(y))
            y += PLATFORM_SPAWN_INTERVAL
        self._next_platform_y = y


class Game:
    def __init__(self, win):
        self.win = win
        self.input = InputHandler(win)
        self.state = STATE_MENU
        self.gs: GameState = None
        self.scores = _load_scores()

    # ──────────────────────────────
    # 主迴圈
    # ──────────────────────────────
    def run(self):
        frame_duration = 1.0 / TARGET_FPS
        while True:
            t0 = time.monotonic()
            keys = self.input.get_input()

            if self.state == STATE_MENU:
                self._handle_menu(keys)
            elif self.state == STATE_PLAYING:
                self._handle_playing(keys)
            elif self.state == STATE_PAUSED:
                self._handle_paused(keys)
            elif self.state == STATE_GAMEOVER:
                self._handle_gameover(keys)

            # 固定幀率休眠
            elapsed = time.monotonic() - t0
            sleep_time = frame_duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    # ──────────────────────────────
    # 狀態處理
    # ──────────────────────────────
    def _handle_menu(self, keys):
        render_menu(self.win, self.scores)
        if 'enter' in keys:
            self._start_game()
        if 'q' in keys:
            raise SystemExit

    def _handle_playing(self, keys):
        gs = self.gs

        # 暫停 / 離開
        if 'p' in keys:
            self.state = STATE_PAUSED
            return
        if 'q' in keys:
            raise SystemExit

        # 輸入移動
        if 'left' in keys:
            gs.player.move(-PLAYER_MOVE_SPEED)
        if 'right' in keys:
            gs.player.move(PLAYER_MOVE_SPEED)

        # 更新物理
        self._update_physics()

        # 難度提升
        if gs.frame > 0 and gs.frame % DIFFICULTY_INTERVAL == 0:
            gs.platform_speed = min(gs.platform_speed + PLATFORM_SPEED_INCREMENT, 2.0)
            gs.level += 1

        # 分數（每幀 +1）
        gs.score += gs.level
        gs.frame += 1

        # 渲染
        render_game(self.win, gs.player, gs.platforms, gs.score, gs.level,
                    gs.frame, gs.platform_speed)

        # 死亡判定：掉出底部 或 被捲出頂部 或 HP 歸零
        if not gs.player.alive or gs.player.y > SCREEN_HEIGHT or gs.player.y < -1:
            self._end_game()

    def _handle_paused(self, keys):
        render_pause(self.win)
        if 'p' in keys:
            self.state = STATE_PLAYING
        if 'q' in keys:
            raise SystemExit

    def _handle_gameover(self, keys):
        render_gameover(self.win, self.gs.score, self.scores)
        if 'r' in keys:
            self._start_game()
        if 'q' in keys:
            raise SystemExit

    # ──────────────────────────────
    # 物理更新
    # ──────────────────────────────
    def _update_physics(self):
        gs = self.gs
        player = gs.player

        # 重力
        player.on_platform = False
        player.apply_gravity()

        # 預測下一幀位置
        new_y = player.y + player.vy

        # 碰撞偵測：掃描玩家移動路徑
        landed_platform = None
        for plat in gs.platforms:
            if not plat.active:
                continue
            # 玩家在平台水平範圍內
            if plat.left() <= player.x <= plat.right():
                # 玩家從平台上方穿過 → 著陸
                if player.y <= plat.top() < new_y + 0.5:
                    landed_platform = plat
                    new_y = plat.top() - 1   # 停在平台頂部的上一格
                    player.vy = 0.0
                    player.on_platform = True
                    break

        # 更新玩家 y
        player.y = new_y
        player.update()

        # 處理著陸平台效果
        if landed_platform is not None:
            self._apply_platform_effect(landed_platform)

        # 捲動世界（平台向上移動）
        gs.scroll_offset += gs.platform_speed
        step = gs.platform_speed
        for plat in gs.platforms:
            plat.y -= step
            plat.update()
        player.y -= step

        # 生成新平台（從畫面底部下方補）
        gs._next_platform_y -= step
        while gs._next_platform_y < SCREEN_HEIGHT + PLATFORM_SPAWN_INTERVAL:
            gs.platforms.append(make_platform(gs._next_platform_y + SCREEN_HEIGHT))
            gs._next_platform_y += PLATFORM_SPAWN_INTERVAL

        # 移除超出畫面頂部的平台
        gs.platforms = [p for p in gs.platforms if p.y > -2]

    def _apply_platform_effect(self, plat: Platform):
        player = self.gs.player
        if plat.platform_type == PLATFORM_DAMAGE:
            player.take_damage(1)
        elif plat.platform_type == PLATFORM_HEAL:
            player.heal(1)
        elif plat.platform_type == PLATFORM_SPRING:
            player.vy = -MAX_FALL_SPEED * 1.5   # 彈射
            player.on_platform = False
        elif plat.platform_type == PLATFORM_CRUMBLE:
            plat.active = False  # 崩壞平台消失

    # ──────────────────────────────
    # 遊戲開始 / 結束
    # ──────────────────────────────
    def _start_game(self):
        self.gs = GameState()
        self.state = STATE_PLAYING

    def _end_game(self):
        score = self.gs.score
        self.scores.append(score)
        self.scores.sort(reverse=True)
        self.scores = self.scores[:LEADERBOARD_MAX]
        _save_scores(self.scores)
        self.state = STATE_GAMEOVER


# ──────────────────────────────
# 排行榜 I/O
# ──────────────────────────────

def _load_scores() -> list:
    path = os.path.join(os.path.dirname(__file__), LEADERBOARD_FILE)
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("scores", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_scores(scores: list):
    path = os.path.join(os.path.dirname(__file__), LEADERBOARD_FILE)
    with open(path, "w") as f:
        json.dump({"scores": scores}, f)
