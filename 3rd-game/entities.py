"""
entities.py - Game entities: Player, Platform, Particle.
"""

import random
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PLAYER_START_HP, PLAYER_MAX_HP, PLAYER_MOVE_SPEED,
    GRAVITY, MAX_FALL_SPEED, PLAYER_WIDTH,
    PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH,
    PLATFORM_NORMAL, PLATFORM_DAMAGE, PLATFORM_HEAL,
    PLATFORM_MOVING, PLATFORM_CRUMBLE, PLATFORM_SPRING,
    PLATFORM_WEIGHTS_INITIAL,
    DAMAGE_AMOUNT, HEAL_AMOUNT, SPRING_BOOST, MOVING_SPEED,
    CRUMBLE_TICKS,
)


class Particle:
    """Visual particle effect."""

    def __init__(self, x, y, char, life, dx=0, dy=-1, color_pair=0):
        self.x = x
        self.y = y
        self.char = char
        self.life = life
        self.max_life = life
        self.dx = dx
        self.dy = dy
        self.color_pair = color_pair
        self.tick = 0

    def update(self):
        self.tick += 1
        if self.tick % 2 == 0:
            self.x += self.dx
            self.y += self.dy
        self.life -= 1
        return self.life > 0


class Player:
    """Player character entity."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vy = 0
        self.hp = PLAYER_START_HP
        self.max_hp = PLAYER_MAX_HP
        self.score = 0
        self.on_platform = None
        self.invincible_frames = 0
        self.facing_right = True

    def move_left(self):
        self.x = max(0, self.x - PLAYER_MOVE_SPEED)
        self.facing_right = False

    def move_right(self):
        self.x = min(SCREEN_WIDTH - PLAYER_WIDTH, self.x + PLAYER_MOVE_SPEED)
        self.facing_right = True

    def apply_gravity(self):
        if self.on_platform is None:
            self.vy = min(self.vy + GRAVITY, MAX_FALL_SPEED)
        self.y += self.vy

    def take_damage(self, amount=DAMAGE_AMOUNT):
        if self.invincible_frames <= 0:
            self.hp -= amount
            self.invincible_frames = 10

    def heal(self, amount=HEAL_AMOUNT):
        self.hp = min(self.hp + amount, self.max_hp)

    def is_dead(self):
        return self.hp <= 0

    def is_out_of_bounds(self):
        return self.y < -1 or self.y >= SCREEN_HEIGHT + 1

    def update(self):
        if self.invincible_frames > 0:
            self.invincible_frames -= 1

    def get_display_char(self):
        if self.invincible_frames > 0 and self.invincible_frames % 2 == 0:
            return ' '
        if self.facing_right:
            return '☺'
        return '☺'


class Platform:
    """Platform (stair) entity."""

    def __init__(self, x, y, width, platform_type=PLATFORM_NORMAL):
        self.x = x
        self.y = y
        self.width = width
        self.platform_type = platform_type
        self.active = True
        self.crumble_timer = CRUMBLE_TICKS if platform_type == PLATFORM_CRUMBLE else -1
        self.stepped_on = False
        self.moving_dir = random.choice([-1, 1]) if platform_type == PLATFORM_MOVING else 0
        self.spring_used = False

    def update(self):
        if self.platform_type == PLATFORM_MOVING and self.active:
            self.x += self.moving_dir * MOVING_SPEED
            if self.x <= 0:
                self.moving_dir = 1
            elif self.x + self.width >= SCREEN_WIDTH:
                self.moving_dir = -1

        if self.platform_type == PLATFORM_CRUMBLE and self.stepped_on:
            self.crumble_timer -= 1
            if self.crumble_timer <= 0:
                self.active = False

    def on_player_land(self, player):
        """Handle player landing on this platform. Returns list of particles."""
        particles = []
        self.stepped_on = True

        if self.platform_type == PLATFORM_DAMAGE:
            player.take_damage(DAMAGE_AMOUNT)
            for i in range(3):
                particles.append(Particle(
                    player.x + random.randint(-1, 1),
                    player.y - 1,
                    random.choice(['✦', '!', '×']),
                    life=6,
                    dx=random.choice([-1, 0, 1]),
                    dy=-1,
                    color_pair=3
                ))

        elif self.platform_type == PLATFORM_HEAL:
            player.heal(HEAL_AMOUNT)
            for i in range(3):
                particles.append(Particle(
                    player.x + random.randint(-1, 1),
                    player.y - 1,
                    random.choice(['♥', '✦', '+',]),
                    life=8,
                    dx=random.choice([-1, 0, 1]),
                    dy=-1,
                    color_pair=4
                ))

        elif self.platform_type == PLATFORM_SPRING:
            if not self.spring_used:
                player.vy = SPRING_BOOST
                player.on_platform = None
                self.spring_used = True
                for i in range(5):
                    particles.append(Particle(
                        player.x + random.randint(-2, 2),
                        player.y + 1,
                        random.choice(['↑', '⇑', '★']),
                        life=10,
                        dx=random.choice([-1, 0, 1]),
                        dy=-1,
                        color_pair=7
                    ))

        elif self.platform_type == PLATFORM_NORMAL:
            particles.append(Particle(
                player.x, player.y + 1,
                '·', life=3, color_pair=2
            ))

        return particles

    def contains_x(self, px):
        return self.x <= px <= self.x + self.width - 1


def generate_platform(y, difficulty_level=0):
    """Generate a random platform at given y position."""
    weights = dict(PLATFORM_WEIGHTS_INITIAL)
    weights[PLATFORM_DAMAGE] = weights[PLATFORM_DAMAGE] + difficulty_level * 2
    weights[PLATFORM_CRUMBLE] = weights[PLATFORM_CRUMBLE] + difficulty_level
    weights[PLATFORM_NORMAL] = max(10, weights[PLATFORM_NORMAL] - difficulty_level * 2)

    types = list(weights.keys())
    w = list(weights.values())
    platform_type = random.choices(types, weights=w, k=1)[0]

    width = random.randint(PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH)
    if platform_type == PLATFORM_SPRING:
        width = max(PLATFORM_MIN_WIDTH, width - 2)
    elif platform_type == PLATFORM_HEAL:
        width = max(PLATFORM_MIN_WIDTH, width - 1)

    x = random.randint(0, SCREEN_WIDTH - width)

    return Platform(x, y, width, platform_type)
