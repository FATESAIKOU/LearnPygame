"""
entities.py - 玩家與平台的資料結構定義
"""

import random
from constants import *


class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vy = 0.0       # 垂直速度（正 = 向下）
        self.hp = PLAYER_HP_MAX
        self.score = 0
        self.on_platform = False
        self.alive = True
        # 無敵幀（踩到傷害平台後短暫無敵）
        self.invincible_frames = 0

    def apply_gravity(self):
        if not self.on_platform:
            self.vy = min(self.vy + GRAVITY, MAX_FALL_SPEED)

    def move(self, dx: int):
        self.x = max(1, min(SCREEN_WIDTH - 2, self.x + dx))

    def take_damage(self, amount: int = 1):
        if self.invincible_frames <= 0:
            self.hp -= amount
            self.invincible_frames = TARGET_FPS  # 1 秒無敵
            if self.hp <= 0:
                self.hp = 0
                self.alive = False

    def heal(self, amount: int = 1):
        self.hp = min(PLAYER_HP_MAX, self.hp + amount)

    def update(self):
        if self.invincible_frames > 0:
            self.invincible_frames -= 1


class Platform:
    def __init__(self, x: int, y: float, width: int, platform_type: str = PLATFORM_NORMAL):
        self.x = x
        self.y = y
        self.width = width
        self.platform_type = platform_type
        self.active = True  # 崩壞平台踩後設 False

        # 移動平台
        self.moving = (platform_type == PLATFORM_MOVING)
        self.move_speed = random.choice([-1, 1]) * 0.5 if self.moving else 0.0
        self.move_dir = 1

    def char(self) -> str:
        """回傳平台對應的字元"""
        mapping = {
            PLATFORM_NORMAL: CHAR_PLATFORM_NORMAL,
            PLATFORM_DAMAGE: CHAR_PLATFORM_DAMAGE,
            PLATFORM_HEAL: CHAR_PLATFORM_HEAL,
            PLATFORM_CRUMBLE: CHAR_PLATFORM_CRUMBLE,
            PLATFORM_SPRING: CHAR_PLATFORM_SPRING,
            PLATFORM_MOVING: CHAR_PLATFORM_MOVING,
        }
        return mapping.get(self.platform_type, CHAR_PLATFORM_NORMAL)

    def update(self):
        """移動平台水平移動"""
        if self.moving:
            self.x += self.move_speed * self.move_dir
            # 碰牆反彈
            if self.x < 1:
                self.x = 1
                self.move_dir *= -1
            if self.x + self.width > SCREEN_WIDTH - 1:
                self.x = SCREEN_WIDTH - 1 - self.width
                self.move_dir *= -1

    def left(self) -> float:
        return self.x

    def right(self) -> float:
        return self.x + self.width - 1

    def top(self) -> float:
        return self.y


def make_platform(y: float, platform_type: str = None) -> Platform:
    """隨機生成一個平台"""
    if platform_type is None:
        r = random.random()
        if r < PLATFORM_MOVING_CHANCE:
            platform_type = PLATFORM_MOVING
        elif r < PLATFORM_MOVING_CHANCE + PLATFORM_CRUMBLE_CHANCE:
            platform_type = PLATFORM_CRUMBLE
        elif r < PLATFORM_MOVING_CHANCE + PLATFORM_CRUMBLE_CHANCE + PLATFORM_SPRING_CHANCE:
            platform_type = PLATFORM_SPRING
        elif r < PLATFORM_MOVING_CHANCE + PLATFORM_CRUMBLE_CHANCE + PLATFORM_SPRING_CHANCE + PLATFORM_DAMAGE_CHANCE:
            platform_type = PLATFORM_DAMAGE
        elif r < PLATFORM_MOVING_CHANCE + PLATFORM_CRUMBLE_CHANCE + PLATFORM_SPRING_CHANCE + PLATFORM_DAMAGE_CHANCE + PLATFORM_HEAL_CHANCE:
            platform_type = PLATFORM_HEAL
        else:
            platform_type = PLATFORM_NORMAL

    width = random.randint(PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH)
    x = random.randint(1, SCREEN_WIDTH - 1 - width)
    return Platform(x, y, width, platform_type)
