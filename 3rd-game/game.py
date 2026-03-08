"""
game.py - Main game loop, physics, collision, platform generation.
"""

import time
import random
from entities import Player, Platform, Particle, generate_platform
from input_handler import InputHandler
from renderer import Renderer
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    GRAVITY, MAX_FALL_SPEED,
    PLATFORM_NORMAL, PLATFORM_SPRING,
    SCROLL_INTERVAL_INITIAL, SCROLL_INTERVAL_MIN, SCROLL_SPEED_INCREASE,
    DIFFICULTY_INTERVAL,
    TARGET_FPS, FRAME_TIME,
    SCORE_PER_SCROLL, SCORE_PER_SECOND,
    PLATFORM_GAP_MIN, PLATFORM_GAP_MAX,
)


class Game:
    """Main game controller."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.renderer = Renderer(stdscr)
        self.input_handler = InputHandler(stdscr)
        self.high_score = 0
        self.running = True

    def run(self):
        """Main application loop: title -> game -> game over -> repeat."""
        while self.running:
            action = self._show_title()
            if action == 'quit':
                break
            result = self._play_game()
            if result == 'quit':
                break
            action = self._show_game_over()
            if action == 'quit':
                break

    def _show_title(self):
        """Display title screen, wait for input."""
        self.input_handler.flush()
        self.renderer.draw_title_screen(self.high_score)

        while True:
            action = self.input_handler.wait_for_key()
            if action == InputHandler.ACTION_QUIT:
                return 'quit'
            if action == InputHandler.ACTION_CONFIRM:
                return 'start'

    def _show_game_over(self):
        """Display game over screen."""
        self.input_handler.flush()
        is_new_high = self.player.score > self.high_score
        if is_new_high:
            self.high_score = self.player.score
        else:
            self.high_score = max(self.high_score, self.player.score)

        self.renderer.draw_game_over(
            self.player, self.elapsed_time, self.high_score, is_new_high
        )

        while True:
            action = self.input_handler.wait_for_key()
            if action == InputHandler.ACTION_QUIT:
                return 'quit'
            if action == InputHandler.ACTION_CONFIRM:
                return 'restart'

    def _play_game(self):
        """Run the main gameplay loop."""
        self._init_game_state()

        while True:
            frame_start = time.time()

            # Input
            action = self.input_handler.get_action()
            if action == InputHandler.ACTION_QUIT:
                return 'quit'
            elif action == InputHandler.ACTION_PAUSE:
                result = self._pause()
                if result == 'quit':
                    return 'quit'
                self.last_scroll_time = time.time()
                self.last_difficulty_time = time.time()
                continue
            elif action == InputHandler.ACTION_LEFT:
                self.player.move_left()
            elif action == InputHandler.ACTION_RIGHT:
                self.player.move_right()

            # Update
            self._update()

            # Check game over
            if self.player.is_dead() or self.player.is_out_of_bounds():
                return 'game_over'

            # Render
            self._render()

            # Frame rate control
            elapsed = time.time() - frame_start
            sleep_time = FRAME_TIME - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

            self.frame_count += 1

    def _init_game_state(self):
        """Initialize/reset all game state."""
        self.player = Player(SCREEN_WIDTH // 2, 4)
        self.platforms = []
        self.particles = []
        self.frame_count = 0
        self.elapsed_time = 0
        self.start_time = time.time()
        self.last_scroll_time = time.time()
        self.last_difficulty_time = time.time()
        self.scroll_interval = SCROLL_INTERVAL_INITIAL
        self.difficulty_level = 0
        self.score_timer = 0

        # Generate initial platforms
        self._generate_initial_platforms()

        # Place player on the first platform
        if self.platforms:
            first = self.platforms[0]
            self.player.x = first.x + first.width // 2
            self.player.y = first.y - 1
            self.player.on_platform = first

    def _generate_initial_platforms(self):
        """Generate starting set of platforms."""
        y = 6
        while y < SCREEN_HEIGHT - 2:
            plat = generate_platform(y, 0)
            # First few platforms should be normal
            if y < 12:
                plat.platform_type = PLATFORM_NORMAL
            self.platforms.append(plat)
            y += random.randint(PLATFORM_GAP_MIN, PLATFORM_GAP_MAX)

    def _update(self):
        """Update game state: physics, scrolling, collisions, scoring."""
        now = time.time()
        self.elapsed_time = now - self.start_time

        # Difficulty scaling
        if now - self.last_difficulty_time >= DIFFICULTY_INTERVAL:
            self.difficulty_level += 1
            self.scroll_interval = max(
                SCROLL_INTERVAL_MIN,
                self.scroll_interval - SCROLL_SPEED_INCREASE
            )
            self.last_difficulty_time = now

        # Scroll platforms upward
        if now - self.last_scroll_time >= self.scroll_interval:
            self._scroll_up()
            self.last_scroll_time = now

        # Player physics
        old_y = self.player.y
        self.player.on_platform = None
        self.player.apply_gravity()
        self.player.update()

        # Collision detection
        self._check_collisions(old_y)

        # Update platforms
        for plat in self.platforms:
            plat.update()
            # If player is on a moving platform, move with it
            if self.player.on_platform == plat and plat.moving_dir != 0:
                from constants import MOVING_SPEED
                self.player.x += plat.moving_dir * MOVING_SPEED
                self.player.x = max(0, min(SCREEN_WIDTH - 1, self.player.x))

        # Remove inactive platforms
        self.platforms = [p for p in self.platforms if p.active and p.y >= -1]

        # Update particles
        self.particles = [p for p in self.particles if p.update()]

        # Scoring
        self.score_timer += 1
        if self.score_timer >= TARGET_FPS:
            self.player.score += SCORE_PER_SECOND
            self.score_timer = 0

        # Ceiling damage
        if self.player.y <= 1:
            self.player.take_damage(1)
            for _ in range(2):
                self.particles.append(Particle(
                    int(self.player.x) + random.randint(-1, 1),
                    int(self.player.y),
                    random.choice(['✦', '!', '×']),
                    life=5, dx=random.choice([-1, 0, 1]), dy=1,
                    color_pair=3
                ))

    def _scroll_up(self):
        """Move all platforms up by 1, generate new ones at bottom."""
        for plat in self.platforms:
            plat.y -= 1

        # Player also moves up if on a platform
        if self.player.on_platform:
            self.player.y -= 1

        self.player.score += SCORE_PER_SCROLL

        # Generate new platform at bottom if needed
        bottom_platforms = [p for p in self.platforms if p.y >= SCREEN_HEIGHT - 8]
        if not bottom_platforms:
            new_y = SCREEN_HEIGHT - 2
            new_plat = generate_platform(new_y, self.difficulty_level)
            self.platforms.append(new_plat)

        # Also ensure good distribution
        max_y = max((p.y for p in self.platforms), default=0)
        if max_y < SCREEN_HEIGHT - 4:
            new_y = max_y + random.randint(PLATFORM_GAP_MIN, PLATFORM_GAP_MAX)
            if new_y < SCREEN_HEIGHT:
                new_plat = generate_platform(new_y, self.difficulty_level)
                self.platforms.append(new_plat)

    def _check_collisions(self, old_y):
        """Check if player landed on any platform."""
        player = self.player

        # Only check landing when falling
        if player.vy <= 0:
            return

        for plat in self.platforms:
            if not plat.active:
                continue
            if not (0 <= plat.y < SCREEN_HEIGHT):
                continue

            # Check horizontal overlap
            if not plat.contains_x(int(player.x)):
                continue

            # Check vertical: player was above platform, now at or below it
            player_feet = int(player.y)
            old_feet = int(old_y)

            if old_feet <= plat.y and player_feet >= plat.y:
                # Land on platform
                player.y = plat.y - 1
                player.vy = 0
                player.on_platform = plat

                # Platform effects
                new_particles = plat.on_player_land(player)
                self.particles.extend(new_particles)

                # Spring platforms override on_platform
                if plat.platform_type == PLATFORM_SPRING and not plat.spring_used:
                    pass  # spring_used is set in on_player_land

                break

    def _pause(self):
        """Handle pause state."""
        self.renderer.draw_pause_screen()
        self.input_handler.flush()
        while True:
            action = self.input_handler.wait_for_key()
            if action == InputHandler.ACTION_QUIT:
                return 'quit'
            if action in (InputHandler.ACTION_PAUSE, InputHandler.ACTION_CONFIRM):
                self.input_handler.flush()
                return 'resume'

    def _render(self):
        """Render the current game frame."""
        self.renderer.clear()
        self.renderer.draw_border()
        self.renderer.draw_ceiling_spikes(self.frame_count)
        self.renderer.draw_platforms(self.platforms)
        self.renderer.draw_particles(self.particles)
        self.renderer.draw_player(self.player)
        self.renderer.draw_hud(self.player, self.elapsed_time, self.difficulty_level)
        self.renderer.refresh()
