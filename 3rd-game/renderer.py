"""
renderer.py - Terminal rendering engine using curses.
Handles all drawing: borders, play area, HUD, menus, particles.
"""

import curses
import math
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BORDER_CHAR_H, BORDER_CHAR_V,
    CORNER_TL, CORNER_TR, CORNER_BL, CORNER_BR,
    PLATFORM_CHARS,
    PLATFORM_NORMAL, PLATFORM_DAMAGE, PLATFORM_HEAL,
    PLATFORM_MOVING, PLATFORM_CRUMBLE, PLATFORM_SPRING,
    COLOR_DEFAULT, COLOR_PLAYER, COLOR_NORMAL_PLATFORM,
    COLOR_DAMAGE_PLATFORM, COLOR_HEAL_PLATFORM,
    COLOR_MOVING_PLATFORM, COLOR_CRUMBLE_PLATFORM,
    COLOR_SPRING_PLATFORM, COLOR_BORDER, COLOR_TITLE,
    COLOR_SCORE, COLOR_HP_GOOD, COLOR_HP_LOW, COLOR_PARTICLE,
    TITLE_ART, GAME_OVER_ART,
    PLAYER_MAX_HP,
)


PLATFORM_COLOR_MAP = {
    PLATFORM_NORMAL:  COLOR_NORMAL_PLATFORM,
    PLATFORM_DAMAGE:  COLOR_DAMAGE_PLATFORM,
    PLATFORM_HEAL:    COLOR_HEAL_PLATFORM,
    PLATFORM_MOVING:  COLOR_MOVING_PLATFORM,
    PLATFORM_CRUMBLE: COLOR_CRUMBLE_PLATFORM,
    PLATFORM_SPRING:  COLOR_SPRING_PLATFORM,
}


def init_colors():
    """Initialize curses color pairs."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_PLAYER, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_NORMAL_PLATFORM, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_DAMAGE_PLATFORM, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_HEAL_PLATFORM, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_MOVING_PLATFORM, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_CRUMBLE_PLATFORM, curses.COLOR_MAGENTA, -1)
    curses.init_pair(COLOR_SPRING_PLATFORM, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_BORDER, curses.COLOR_BLUE, -1)
    curses.init_pair(COLOR_TITLE, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_SCORE, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_HP_GOOD, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_HP_LOW, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_PARTICLE, curses.COLOR_WHITE, -1)


class Renderer:
    """Handles all terminal rendering via curses."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.stdscr.clear()
        curses.curs_set(0)
        init_colors()
        self.term_h, self.term_w = stdscr.getmaxyx()
        self._update_offsets()

    def _update_offsets(self):
        """Calculate offsets to center the play area."""
        self.term_h, self.term_w = self.stdscr.getmaxyx()
        # +2 for borders on each side
        total_w = SCREEN_WIDTH + 2
        total_h = SCREEN_HEIGHT + 4  # borders + HUD rows
        self.offset_x = max(0, (self.term_w - total_w) // 2)
        self.offset_y = max(0, (self.term_h - total_h) // 2)

    def _safe_addstr(self, y, x, text, attr=0):
        """Safely write text, handling edge-of-screen issues."""
        try:
            if 0 <= y < self.term_h and 0 <= x < self.term_w:
                max_len = self.term_w - x - 1
                if max_len > 0:
                    self.stdscr.addstr(y, x, text[:max_len], attr)
        except curses.error:
            pass

    def _safe_addch(self, y, x, ch, attr=0):
        """Safely write a character."""
        try:
            if 0 <= y < self.term_h - 1 and 0 <= x < self.term_w - 1:
                self.stdscr.addch(y, x, ch, attr)
        except curses.error:
            pass

    def clear(self):
        self.stdscr.erase()
        self._update_offsets()

    def draw_border(self):
        """Draw the play area border with fancy box-drawing characters."""
        ox, oy = self.offset_x, self.offset_y
        w = SCREEN_WIDTH + 2
        h = SCREEN_HEIGHT + 2

        border_attr = curses.color_pair(COLOR_BORDER) | curses.A_BOLD

        # Top border
        top = CORNER_TL + BORDER_CHAR_H * SCREEN_WIDTH + CORNER_TR
        self._safe_addstr(oy, ox, top, border_attr)

        # Side borders
        for row in range(1, h - 1):
            self._safe_addstr(oy + row, ox, BORDER_CHAR_V, border_attr)
            self._safe_addstr(oy + row, ox + w - 1, BORDER_CHAR_V, border_attr)

        # Bottom border
        bottom = CORNER_BL + BORDER_CHAR_H * SCREEN_WIDTH + CORNER_BR
        self._safe_addstr(oy + h - 1, ox, bottom, border_attr)

    def draw_hud(self, player, elapsed_time, difficulty_level):
        """Draw the HUD below the play area."""
        ox = self.offset_x
        oy = self.offset_y + SCREEN_HEIGHT + 2

        # HP bar with hearts
        hp_color = COLOR_HP_GOOD if player.hp > 2 else COLOR_HP_LOW
        hp_bar = '♥' * player.hp + '♡' * (player.max_hp - player.hp)
        hp_str = f" HP: {hp_bar} "
        self._safe_addstr(oy, ox, hp_str,
                          curses.color_pair(hp_color) | curses.A_BOLD)

        # Score
        score_str = f" ★ Score: {player.score:>6} "
        self._safe_addstr(oy, ox + 25, score_str,
                          curses.color_pair(COLOR_SCORE) | curses.A_BOLD)

        # Time & difficulty
        time_str = f" ⏱ {int(elapsed_time)}s  Lv.{difficulty_level + 1} "
        self._safe_addstr(oy, ox + 46, time_str,
                          curses.color_pair(COLOR_TITLE))

        # Controls hint
        ctrl_str = " [A/←]Left  [D/→]Right  [P]Pause  [Q]Quit "
        self._safe_addstr(oy + 1, ox, ctrl_str,
                          curses.color_pair(COLOR_DEFAULT) | curses.A_DIM)

    def draw_player(self, player):
        """Draw the player character in the play area."""
        px = self.offset_x + 1 + int(player.x)
        py = self.offset_y + 1 + int(player.y)
        ch = player.get_display_char()
        attr = curses.color_pair(COLOR_PLAYER) | curses.A_BOLD
        self._safe_addstr(py, px, ch, attr)

    def draw_platform(self, platform):
        """Draw a single platform."""
        if not platform.active:
            return

        color = PLATFORM_COLOR_MAP.get(platform.platform_type, COLOR_NORMAL_PLATFORM)
        ch = PLATFORM_CHARS.get(platform.platform_type, '=')
        attr = curses.color_pair(color)

        if platform.platform_type == PLATFORM_DAMAGE:
            attr |= curses.A_BOLD
        elif platform.platform_type == PLATFORM_SPRING:
            attr |= curses.A_BOLD
        elif platform.platform_type == PLATFORM_CRUMBLE and platform.stepped_on:
            attr |= curses.A_DIM

        base_x = self.offset_x + 1 + int(platform.x)
        base_y = self.offset_y + 1 + int(platform.y)

        for i in range(platform.width):
            self._safe_addch(base_y, base_x + i, ord(ch), attr)

    def draw_platforms(self, platforms):
        """Draw all platforms."""
        for platform in platforms:
            if 0 <= platform.y < SCREEN_HEIGHT:
                self.draw_platform(platform)

    def draw_particles(self, particles):
        """Draw particle effects."""
        for p in particles:
            px = self.offset_x + 1 + int(p.x)
            py = self.offset_y + 1 + int(p.y)
            brightness = p.life / p.max_life
            attr = curses.color_pair(p.color_pair)
            if brightness > 0.5:
                attr |= curses.A_BOLD
            else:
                attr |= curses.A_DIM
            self._safe_addstr(py, px, p.char, attr)

    def draw_ceiling_spikes(self, frame_count):
        """Draw animated danger zone at top of screen."""
        ox = self.offset_x + 1
        oy = self.offset_y + 1
        attr = curses.color_pair(COLOR_DAMAGE_PLATFORM) | curses.A_BOLD

        spike_chars = ['▼', '▽']
        for i in range(SCREEN_WIDTH):
            ch = spike_chars[(i + frame_count // 4) % 2]
            self._safe_addstr(oy, ox + i, ch, attr)

    def draw_title_screen(self, high_score=0):
        """Draw the start/title screen centered."""
        self.clear()
        cx = self.term_w // 2
        cy = self.term_h // 2 - 8

        # Decorative top
        deco = "✦ ═══════════════════════════════════════ ✦"
        self._safe_addstr(cy, cx - len(deco) // 2, deco,
                          curses.color_pair(COLOR_BORDER) | curses.A_BOLD)

        # Title art
        for i, line in enumerate(TITLE_ART):
            self._safe_addstr(cy + 2 + i, cx - len(line) // 2, line,
                              curses.color_pair(COLOR_TITLE) | curses.A_BOLD)

        # Player preview
        preview_y = cy + 8
        preview = [
            "          ☺    ← You!",
            "       ═══════════",
            "   ▓▓▓▓▓▓▓▓    ← Danger!",
            "           ♥♥♥♥♥♥♥  ← Heal!",
            "     ~~~~~~        ← Moving!",
            "       ░░░░░░░    ← Crumble!",
            "         ▲▲▲▲▲   ← Spring!",
        ]
        for i, line in enumerate(preview):
            attr = curses.color_pair(COLOR_DEFAULT)
            if 'Danger' in line:
                attr = curses.color_pair(COLOR_DAMAGE_PLATFORM)
            elif 'Heal' in line:
                attr = curses.color_pair(COLOR_HEAL_PLATFORM)
            elif 'Moving' in line:
                attr = curses.color_pair(COLOR_MOVING_PLATFORM)
            elif 'Crumble' in line:
                attr = curses.color_pair(COLOR_CRUMBLE_PLATFORM)
            elif 'Spring' in line:
                attr = curses.color_pair(COLOR_SPRING_PLATFORM)
            elif 'You' in line:
                attr = curses.color_pair(COLOR_PLAYER) | curses.A_BOLD
            self._safe_addstr(preview_y + i, cx - 20, line, attr)

        # High score
        if high_score > 0:
            hs = f"🏆 High Score: {high_score}"
            self._safe_addstr(preview_y + 9, cx - len(hs) // 2, hs,
                              curses.color_pair(COLOR_SCORE) | curses.A_BOLD)

        # Instructions
        inst_y = preview_y + 11
        instructions = [
            "╔═════════════════════════════════╗",
            "║   [A/←] Move Left               ║",
            "║   [D/→] Move Right              ║",
            "║   [P]   Pause                   ║",
            "║   [Q]   Quit                    ║",
            "╚═════════════════════════════════╝",
        ]
        for i, line in enumerate(instructions):
            self._safe_addstr(inst_y + i, cx - len(line) // 2, line,
                              curses.color_pair(COLOR_BORDER))

        # Start prompt (blinking effect handled by caller)
        prompt = ">>> Press ENTER or SPACE to Start <<<"
        self._safe_addstr(inst_y + 7, cx - len(prompt) // 2, prompt,
                          curses.color_pair(COLOR_TITLE) | curses.A_BOLD | curses.A_BLINK)

        self.stdscr.refresh()

    def draw_pause_screen(self):
        """Draw pause overlay."""
        cx = self.term_w // 2
        cy = self.term_h // 2

        box = [
            "╔══════════════════════════╗",
            "║      ⏸  PAUSED  ⏸       ║",
            "║                          ║",
            "║  Press P to Resume       ║",
            "║  Press Q to Quit         ║",
            "╚══════════════════════════╝",
        ]
        for i, line in enumerate(box):
            self._safe_addstr(cy - 3 + i, cx - len(line) // 2, line,
                              curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
        self.stdscr.refresh()

    def draw_game_over(self, player, elapsed_time, high_score, is_new_high):
        """Draw game over screen."""
        self.clear()
        cx = self.term_w // 2
        cy = self.term_h // 2 - 6

        # Game over art
        for i, line in enumerate(GAME_OVER_ART):
            self._safe_addstr(cy + i, cx - len(line) // 2, line,
                              curses.color_pair(COLOR_DAMAGE_PLATFORM) | curses.A_BOLD)

        # Stats
        stats_y = cy + 5
        stats = [
            f"  ★ Final Score:  {player.score}",
            f"  ⏱ Survived:     {int(elapsed_time)} seconds",
        ]
        for i, s in enumerate(stats):
            self._safe_addstr(stats_y + i, cx - 18, s,
                              curses.color_pair(COLOR_SCORE) | curses.A_BOLD)

        if is_new_high:
            nh = "🎉 ★ NEW HIGH SCORE! ★ 🎉"
            self._safe_addstr(stats_y + 3, cx - len(nh) // 2, nh,
                              curses.color_pair(COLOR_TITLE) | curses.A_BOLD | curses.A_BLINK)
        else:
            hs = f"  🏆 High Score:  {high_score}"
            self._safe_addstr(stats_y + 3, cx - 18, hs,
                              curses.color_pair(COLOR_SCORE))

        # Options
        opt_y = stats_y + 6
        options = [
            "╔═════════════════════════════╗",
            "║  Press ENTER to Play Again  ║",
            "║  Press Q to Quit            ║",
            "╚═════════════════════════════╝",
        ]
        for i, line in enumerate(options):
            self._safe_addstr(opt_y + i, cx - len(line) // 2, line,
                              curses.color_pair(COLOR_BORDER) | curses.A_BOLD)

        self.stdscr.refresh()

    def refresh(self):
        self.stdscr.refresh()
