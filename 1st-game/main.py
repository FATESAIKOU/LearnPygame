"""
Star Catcher — A simple Pygame learning project.

Move the blue paddle left/right to catch falling yellow stars.
Every caught star adds 1 point. Missed stars simply disappear.
"""

import random
import sys

import pygame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors (R, G, B)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (30, 144, 255)
YELLOW = (255, 215, 0)

# Player settings
PLAYER_WIDTH = 80
PLAYER_HEIGHT = 20
PLAYER_SPEED = 6

# Star settings
STAR_RADIUS = 8
STAR_SPEED = 4
STAR_SPAWN_INTERVAL = 1000  # milliseconds between spawns


# ---------------------------------------------------------------------------
# Helper classes
# ---------------------------------------------------------------------------
class Player:
    """A simple paddle that moves left and right along the bottom."""

    def __init__(self):
        self.rect = pygame.Rect(
            (SCREEN_WIDTH - PLAYER_WIDTH) // 2,  # center horizontally
            SCREEN_HEIGHT - PLAYER_HEIGHT - 10,   # near the bottom
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
        )

    def move(self, dx: int) -> None:
        """Move horizontally by *dx* pixels, clamped to screen bounds."""
        self.rect.x += dx
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, BLUE, self.rect)


class Star:
    """A small circle that falls from a random x-position at the top."""

    def __init__(self):
        self.x = random.randint(STAR_RADIUS, SCREEN_WIDTH - STAR_RADIUS)
        self.y = -STAR_RADIUS  # start just above the visible area
        self.radius = STAR_RADIUS

    def update(self) -> None:
        """Move the star downward each frame."""
        self.y += STAR_SPEED

    def is_off_screen(self) -> bool:
        return self.y - self.radius > SCREEN_HEIGHT

    def get_rect(self) -> pygame.Rect:
        """Return a bounding-box rect for simple collision detection."""
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2,
        )

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, YELLOW, (self.x, self.y), self.radius)


# ---------------------------------------------------------------------------
# Main game function
# ---------------------------------------------------------------------------
def main() -> None:
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Star Catcher")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)  # default system font, size 36

    player = Player()
    stars: list[Star] = []
    score = 0

    # Custom event fired every STAR_SPAWN_INTERVAL ms to create a new star
    SPAWN_STAR_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_STAR_EVENT, STAR_SPAWN_INTERVAL)

    running = True
    while running:
        # ---- Event handling ------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == SPAWN_STAR_EVENT:
                stars.append(Star())

        # ---- Input ---------------------------------------------------------
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player.move(-PLAYER_SPEED)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player.move(PLAYER_SPEED)

        # ---- Update --------------------------------------------------------
        for star in stars:
            star.update()

        # Check collisions — iterate in reverse so we can safely remove items
        for i in range(len(stars) - 1, -1, -1):
            if player.rect.colliderect(stars[i].get_rect()):
                score += 1
                stars.pop(i)
            elif stars[i].is_off_screen():
                stars.pop(i)

        # ---- Draw ----------------------------------------------------------
        screen.fill(BLACK)
        player.draw(screen)
        for star in stars:
            star.draw(screen)

        # Score text
        score_surface = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_surface, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
