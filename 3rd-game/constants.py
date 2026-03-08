"""
constants.py - Game constants and configuration for NS-SHAFT terminal game.
"""

# Screen dimensions (play area)
SCREEN_WIDTH = 60
SCREEN_HEIGHT = 28

# Play area borders
BORDER_CHAR_H = '═'
BORDER_CHAR_V = '║'
CORNER_TL = '╔'
CORNER_TR = '╗'
CORNER_BL = '╚'
CORNER_BR = '╝'

# Player settings
PLAYER_CHAR = '☺'
PLAYER_START_HP = 5
PLAYER_MAX_HP = 8
PLAYER_MOVE_SPEED = 2
GRAVITY = 1
MAX_FALL_SPEED = 3
PLAYER_WIDTH = 1

# Platform settings
PLATFORM_MIN_WIDTH = 6
PLATFORM_MAX_WIDTH = 14
PLATFORM_GAP_MIN = 4
PLATFORM_GAP_MAX = 7

# Platform types
PLATFORM_NORMAL = 'normal'
PLATFORM_DAMAGE = 'damage'
PLATFORM_HEAL = 'heal'
PLATFORM_MOVING = 'moving'
PLATFORM_CRUMBLE = 'crumble'
PLATFORM_SPRING = 'spring'

# Platform characters
PLATFORM_CHARS = {
    PLATFORM_NORMAL:  '═',
    PLATFORM_DAMAGE:  '▓',
    PLATFORM_HEAL:    '♥',
    PLATFORM_MOVING:  '~',
    PLATFORM_CRUMBLE: '░',
    PLATFORM_SPRING:  '▲',
}

# Platform spawn weights (higher = more common)
PLATFORM_WEIGHTS_INITIAL = {
    PLATFORM_NORMAL:  50,
    PLATFORM_DAMAGE:  10,
    PLATFORM_HEAL:    8,
    PLATFORM_MOVING:  10,
    PLATFORM_CRUMBLE: 12,
    PLATFORM_SPRING:  10,
}

# Platform effects
DAMAGE_AMOUNT = 1
HEAL_AMOUNT = 1
SPRING_BOOST = -5
MOVING_SPEED = 1

# Scroll settings
SCROLL_INTERVAL_INITIAL = 4.0  # seconds between scroll ticks
SCROLL_INTERVAL_MIN = 1.5
SCROLL_SPEED_INCREASE = 0.05  # decrease interval per difficulty tick

# Difficulty
DIFFICULTY_INTERVAL = 15.0  # seconds between difficulty increases
DIFFICULTY_DAMAGE_WEIGHT_INCREASE = 3
DIFFICULTY_NORMAL_WEIGHT_DECREASE = 2

# Timing
TARGET_FPS = 15
FRAME_TIME = 1.0 / TARGET_FPS

# Scoring
SCORE_PER_SCROLL = 10
SCORE_PER_PLATFORM = 5
SCORE_PER_SECOND = 1

# Crumble timing
CRUMBLE_TICKS = 8  # frames before crumble platform disappears

# Colors (curses color pair indices)
COLOR_DEFAULT = 0
COLOR_PLAYER = 1
COLOR_NORMAL_PLATFORM = 2
COLOR_DAMAGE_PLATFORM = 3
COLOR_HEAL_PLATFORM = 4
COLOR_MOVING_PLATFORM = 5
COLOR_CRUMBLE_PLATFORM = 6
COLOR_SPRING_PLATFORM = 7
COLOR_BORDER = 8
COLOR_TITLE = 9
COLOR_SCORE = 10
COLOR_HP_GOOD = 11
COLOR_HP_LOW = 12
COLOR_PARTICLE = 13

# UI
TITLE_ART = [
    "╔═══════════════════════════════════════╗",
    "║     ★ 小朋友下樓梯 ★  NS-SHAFT      ║",
    "║          Terminal Edition              ║",
    "╚═══════════════════════════════════════╝",
]

GAME_OVER_ART = [
    "╔═══════════════════════════════════════╗",
    "║          ☠  GAME OVER  ☠             ║",
    "╚═══════════════════════════════════════╝",
]
