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
from entities import Player, Platform, ParticleSystem, make_platform
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
        self.particles = ParticleSystem()
        self.scroll_offset = 0.0
        self.platform_speed = PLATFORM_SPEED_INITIAL
        self.score = 0
        self.level = 1
        self.frame = 0

        # 螢幕特效
        self.shake_frames = 0
        self.shake_x = 0
        self.shake_y = 0
        self.flash_type = ""
        self.flash_frames = 0

        self._next_platform_y = SCREEN_HEIGHT - 1
        self._init_platforms()

    def _init_platforms(self):
        start_plat = Platform(
            x=SCREEN_WIDTH // 2 - 5,
            y=SCREEN_HEIGHT // 2 + 2,
            width=10,
            platform_type=PLATFORM_NORMAL,
        )
        self.platforms.append(start_plat)
        self.player.y = start_plat.y - 1
        self.player.on_platform = True

        y = SCREEN_HEIGHT - 1
        while y < SCREEN_HEIGHT + 20:
            self.platforms.append(make_platform(y))
            y += PLATFORM_SPAWN_INTERVAL
        self._next_platform_y = y

    def trigger_shake(self, intensity: int = 1):
        self.shake_frames = SCREEN_SHAKE_FRAMES
        self.shake_x = random.choice([-intensity, intensity])
        self.shake_y = random.choice([-intensity, 0, intensity])

    def trigger_flash(self, flash_type: str):
        self.flash_type = flash_type
        self.flash_frames = SCREEN_FLASH_FRAMES

    def update_effects(self):
        if self.shake_frames > 0:
            self.shake_frames -= 1
            self.shake_x = random.choice([-1, 0, 1]) if self.shake_frames > 0 else 0
            self.shake_y = random.choice([-1, 0, 1]) if self.shake_frames > 0 else 0
        if self.flash_frames > 0:
            self.flash_frames -= 1


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

        if 'p' in keys:
            self.state = STATE_PAUSED
            return
        if 'q' in keys:
            raise SystemExit

        # 輸入移動（帶尾跡）
        if 'left' in keys:
            gs.player.move(-PLAYER_MOVE_SPEED)
            gs.particles.spawn_trail(gs.player.x + 1, gs.player.y)
        if 'right' in keys:
            gs.player.move(PLAYER_MOVE_SPEED)
            gs.particles.spawn_trail(gs.player.x - 1, gs.player.y)

        # 下落時的微弱尾跡
        if gs.player.vy > 1.0 and gs.frame % 2 == 0:
            gs.particles.spawn_trail(gs.player.x, gs.player.y - 0.5, color_id=2)

        self._update_physics()

        # 難度提升
        if gs.frame > 0 and gs.frame % DIFFICULTY_INTERVAL == 0:
            gs.platform_speed = min(gs.platform_speed + PLATFORM_SPEED_INCREMENT,
                                    PLATFORM_SPEED_MAX)
            gs.level += 1

        # 分數（連擊加成）
        combo_bonus = max(1, gs.player.combo // 3)
        gs.score += gs.level * combo_bonus
        gs.frame += 1

        # 更新特效
        gs.update_effects()
        gs.particles.update(gs.platform_speed)

        # 渲染
        render_game(self.win, gs.player, gs.platforms, gs.score, gs.level,
                    gs.frame, gs.platform_speed,
                    particles=gs.particles.particles,
                    shake_x=gs.shake_x, shake_y=gs.shake_y,
                    flash_type=gs.flash_type, flash_frames=gs.flash_frames)

        # 死亡判定
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

        player.on_platform = False
        player.apply_gravity()

        new_y = player.y + player.vy

        landed_platform = None
        for plat in gs.platforms:
            if not plat.active:
                continue
            if plat.left() <= player.x <= plat.right():
                if player.y <= plat.top() < new_y + 0.5:
                    landed_platform = plat
                    new_y = plat.top() - 1
                    player.vy = 0.0
                    player.on_platform = True
                    break

        player.y = new_y
        player.update()

        # 著陸效果
        if landed_platform is not None:
            player.land_combo()
            gs.particles.spawn_landing_dust(player.x, player.y + 1)
            self._apply_platform_effect(landed_platform)

            # 連擊分數彈出
            if player.combo >= 3 and player.combo % 3 == 0:
                bonus = player.combo * 10
                gs.score += bonus
                gs.particles.spawn_score_popup(
                    player.x - 2, player.y - 2,
                    f"+{bonus}", color_id=9
                )

        # 捲動
        gs.scroll_offset += gs.platform_speed
        step = gs.platform_speed
        for plat in gs.platforms:
            plat.y -= step
            plat.update()
        player.y -= step

        # 生成新平台
        gs._next_platform_y -= step
        while gs._next_platform_y < SCREEN_HEIGHT + PLATFORM_SPAWN_INTERVAL:
            gs.platforms.append(make_platform(gs._next_platform_y + SCREEN_HEIGHT))
            gs._next_platform_y += PLATFORM_SPAWN_INTERVAL

        # 清理超出畫面的平台
        gs.platforms = [p for p in gs.platforms if p.y > -2]

    def _apply_platform_effect(self, plat: Platform):
        gs = self.gs
        player = gs.player

        if plat.platform_type == PLATFORM_DAMAGE:
            player.take_damage(1)
            gs.particles.spawn_damage_sparks(player.x, player.y)
            gs.trigger_shake(2)
            gs.trigger_flash("damage")

        elif plat.platform_type == PLATFORM_HEAL:
            player.heal(1)
            gs.particles.spawn_heal_sparkles(player.x, player.y)
            gs.trigger_flash("heal")

        elif plat.platform_type == PLATFORM_SPRING:
            player.vy = -MAX_FALL_SPEED * 1.5
            player.on_platform = False
            gs.particles.spawn_spring_burst(player.x, player.y + 1)
            gs.trigger_shake(1)

        elif plat.platform_type == PLATFORM_CRUMBLE:
            plat.start_crumble()
            gs.particles.spawn_crumble_debris(plat.x, plat.y, plat.width)

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
