"""
entities.py - 玩家、平台、粒子特效的資料結構定義
"""

import random
import math
from constants import *


class Particle:
    """單一粒子"""
    def __init__(self, x: float, y: float, vx: float, vy: float,
                 char: str, color_id: int, lifetime: int, gravity: float = 0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.char = char
        self.color_id = color_id
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    @property
    def age_ratio(self) -> float:
        """0.0 = just born, 1.0 = about to die"""
        return 1.0 - (self.lifetime / max(1, self.max_lifetime))


class ParticleSystem:
    """管理所有粒子"""
    def __init__(self):
        self.particles: list = []

    def update(self, scroll_step: float = 0.0):
        for p in self.particles:
            p.update()
            p.y -= scroll_step
        self.particles = [p for p in self.particles if p.alive and
                          -2 < p.y < SCREEN_HEIGHT + 2 and
                          -2 < p.x < SCREEN_WIDTH + 2]
        # 限制粒子上限
        if len(self.particles) > PARTICLE_MAX:
            self.particles = self.particles[-PARTICLE_MAX:]

    def spawn_landing_dust(self, x: float, y: float):
        """著陸時的揚塵效果"""
        chars = [".", "*", ",", "'"]
        for _ in range(PARTICLE_LAND_COUNT):
            vx = random.uniform(-1.5, 1.5)
            vy = random.uniform(-0.8, -0.1)
            ch = random.choice(chars)
            self.particles.append(Particle(
                x + random.uniform(-1, 1), y, vx, vy, ch,
                color_id=3, lifetime=random.randint(6, 12), gravity=0.05
            ))

    def spawn_damage_sparks(self, x: float, y: float):
        """受傷時的火花爆炸"""
        chars = ["*", "#", "!", "X", "+"]
        for _ in range(PARTICLE_DMG_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.5, 2.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            ch = random.choice(chars)
            self.particles.append(Particle(
                x, y, vx, vy, ch,
                color_id=4, lifetime=random.randint(8, 16), gravity=0.03
            ))

    def spawn_heal_sparkles(self, x: float, y: float):
        """補血時的上升光點"""
        chars = ["+", "*", "o", "."]
        for _ in range(PARTICLE_HEAL_COUNT):
            vx = random.uniform(-0.8, 0.8)
            vy = random.uniform(-1.5, -0.3)
            ch = random.choice(chars)
            self.particles.append(Particle(
                x + random.uniform(-2, 2), y, vx, vy, ch,
                color_id=5, lifetime=random.randint(10, 20), gravity=-0.02
            ))

    def spawn_spring_burst(self, x: float, y: float):
        """彈簧平台的彈射特效"""
        chars = ["|", "!", "^", "*"]
        for _ in range(PARTICLE_SPRING_COUNT):
            vx = random.uniform(-0.5, 0.5)
            vy = random.uniform(0.3, 1.5)
            ch = random.choice(chars)
            self.particles.append(Particle(
                x + random.uniform(-1, 1), y, vx, vy, ch,
                color_id=7, lifetime=random.randint(6, 14), gravity=0.04
            ))

    def spawn_crumble_debris(self, x: float, y: float, width: int):
        """崩壞平台的碎片掉落"""
        chars = ["~", ".", ",", "`", "'"]
        for _ in range(PARTICLE_CRUMBLE_COUNT):
            px = x + random.uniform(0, width)
            vx = random.uniform(-0.5, 0.5)
            vy = random.uniform(0.2, 1.0)
            ch = random.choice(chars)
            self.particles.append(Particle(
                px, y, vx, vy, ch,
                color_id=6, lifetime=random.randint(10, 18), gravity=0.06
            ))

    def spawn_trail(self, x: float, y: float, color_id: int = 2):
        """玩家移動尾跡"""
        chars = [".", ",", "'"]
        ch = random.choice(chars)
        self.particles.append(Particle(
            x + random.uniform(-0.3, 0.3),
            y + random.uniform(-0.3, 0.3),
            random.uniform(-0.1, 0.1),
            random.uniform(-0.2, 0.1),
            ch, color_id=color_id,
            lifetime=random.randint(4, 8)
        ))

    def spawn_score_popup(self, x: float, y: float, text: str, color_id: int):
        """分數彈出文字（每個字元一個粒子）"""
        for i, ch in enumerate(text):
            self.particles.append(Particle(
                x + i, y, 0, -0.15, ch,
                color_id=color_id, lifetime=18, gravity=-0.005
            ))


class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vy = 0.0
        self.hp = PLAYER_HP_MAX
        self.score = 0
        self.on_platform = False
        self.alive = True
        self.invincible_frames = 0
        self.facing = 0       # -1 左, 0 中, 1 右
        self.combo = 0        # 連擊計數
        self.combo_timer = 0  # 連擊超時計時器

    def apply_gravity(self):
        if not self.on_platform:
            self.vy = min(self.vy + GRAVITY, MAX_FALL_SPEED)

    def move(self, dx: int):
        self.x = max(1, min(SCREEN_WIDTH - 2, self.x + dx))
        self.facing = 1 if dx > 0 else -1

    def take_damage(self, amount: int = 1):
        if self.invincible_frames <= 0:
            self.hp -= amount
            self.invincible_frames = TARGET_FPS
            if self.hp <= 0:
                self.hp = 0
                self.alive = False

    def heal(self, amount: int = 1):
        self.hp = min(PLAYER_HP_MAX, self.hp + amount)

    def land_combo(self):
        """著陸時累加連擊"""
        self.combo += 1
        self.combo_timer = COMBO_TIMEOUT_FRAMES

    def update(self):
        if self.invincible_frames > 0:
            self.invincible_frames -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0


class Platform:
    def __init__(self, x: int, y: float, width: int, platform_type: str = PLATFORM_NORMAL):
        self.x = x
        self.y = y
        self.width = width
        self.platform_type = platform_type
        self.active = True
        self.moving = (platform_type == PLATFORM_MOVING)
        self.move_speed = random.choice([-1, 1]) * 0.5 if self.moving else 0.0
        self.move_dir = 1
        # 崩壞動畫計時（踩到後先閃爍再消失）
        self.crumble_timer = -1

    def char(self) -> str:
        mapping = {
            PLATFORM_NORMAL: CHAR_PLATFORM_NORMAL,
            PLATFORM_DAMAGE: CHAR_PLATFORM_DAMAGE,
            PLATFORM_HEAL: CHAR_PLATFORM_HEAL,
            PLATFORM_CRUMBLE: CHAR_PLATFORM_CRUMBLE,
            PLATFORM_SPRING: CHAR_PLATFORM_SPRING,
            PLATFORM_MOVING: CHAR_PLATFORM_MOVING,
        }
        return mapping.get(self.platform_type, CHAR_PLATFORM_NORMAL)

    def start_crumble(self):
        """開始崩壞倒計時"""
        if self.crumble_timer < 0:
            self.crumble_timer = 8  # 8 幀後消失

    def update(self):
        if self.moving:
            self.x += self.move_speed * self.move_dir
            if self.x < 1:
                self.x = 1
                self.move_dir *= -1
            if self.x + self.width > SCREEN_WIDTH - 1:
                self.x = SCREEN_WIDTH - 1 - self.width
                self.move_dir *= -1
        if self.crumble_timer >= 0:
            self.crumble_timer -= 1
            if self.crumble_timer <= 0:
                self.active = False

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
