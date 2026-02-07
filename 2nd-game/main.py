"""
無限捲軸平台跳躍遊戲 (Infinite Scrolling Platformer)
=============================================
- 方向鍵左右移動
- 空白鍵跳躍（僅限站在平台上時）
- 掉出畫面底部 → Game Over，按任意鍵重新開始
"""

import pygame
import random
import sys

# --------------- 常數設定 ---------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 顏色 — 天空之城風格
SKY_TOP = (70, 130, 200)        # 天空頂部（深藍）
SKY_BOTTOM = (200, 225, 255)    # 天空底部（淺白藍）
CLOUD_WHITE = (240, 245, 255)   # 雲朵
CLOUD_SHADOW = (210, 220, 235)  # 雲朵陰影
WHITE = (255, 255, 255)
DARK_GRAY = (40, 40, 40)

# 石橋平台顏色
STONE_TOP = (160, 155, 145)     # 石面
STONE_MID = (130, 125, 115)     # 石磚
STONE_DARK = (95, 90, 80)       # 石磚深色
STONE_LINE = (110, 105, 95)     # 磚縫
MOSS_GREEN = (80, 120, 60)      # 青苔點綴

# 勇者顏色
HERO_SKIN = (240, 200, 160)     # 膚色
HERO_HAIR = (100, 60, 30)       # 棕髮
HERO_TUNIC = (30, 100, 180)     # 藍色戰衣
HERO_BELT = (150, 110, 50)      # 腰帶
HERO_BOOTS = (90, 55, 30)       # 靴子
HERO_CAPE = (180, 40, 40)       # 紅色披風
HERO_SWORD = (200, 210, 220)    # 劍（銀色）
HERO_SWORD_HILT = (160, 130, 50)  # 劍柄（金色）

# 玩家設定
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 48
PLAYER_SPEED = 5
JUMP_FORCE = -14
GRAVITY = 0.7

# 平台設定（石橋風格，較厚）
PLATFORM_HEIGHT = 32
PLATFORM_MIN_WIDTH = 100
PLATFORM_MAX_WIDTH = 220
PLATFORM_GAP_MIN = 60       # 平台之間的最小水平間隙
PLATFORM_GAP_MAX = 140      # 平台之間的最大水平間隙
PLATFORM_Y_VARIATION = 60   # 平台高度隨機上下偏移量

# 攝影機捲軸觸發線（玩家超過此 x 座標就開始捲動世界）
SCROLL_THRESHOLD = SCREEN_WIDTH // 3


# --------------- 平台類別（石橋風格） ---------------
class Platform:
    """灰色石橋平台，帶有磚縫和青苔點綴。"""

    def __init__(self, x: float, y: float, width: float):
        self.rect = pygame.Rect(x, y, width, PLATFORM_HEIGHT)
        # 預先計算磚縫位置，讓每個平台的花紋獨特且穩定
        self.brick_offsets = []
        bx = 0
        while bx < width:
            bw = random.randint(18, 32)
            self.brick_offsets.append((bx, bw))
            bx += bw + 2  # 2px 磚縫
        # 隨機青苔位置
        self.moss_spots = [
            (random.randint(4, max(5, int(width) - 8)), random.randint(0, 3))
            for _ in range(max(1, int(width) // 40))
        ]

    def draw(self, surface: pygame.Surface):
        r = self.rect
        # 石橋主體
        pygame.draw.rect(surface, STONE_MID, r)
        # 頂面高光
        pygame.draw.rect(surface, STONE_TOP, (r.x, r.y, r.w, 6))
        # 底面陰影
        pygame.draw.rect(surface, STONE_DARK, (r.x, r.bottom - 5, r.w, 5))
        # 磚縫紋理
        for bx, bw in self.brick_offsets:
            px = r.x + bx
            # 水平磚縫
            pygame.draw.line(surface, STONE_LINE, (px, r.y + 10), (px + bw, r.y + 10), 1)
            pygame.draw.line(surface, STONE_LINE, (px, r.y + 20), (px + bw, r.y + 20), 1)
            # 垂直磚縫
            pygame.draw.line(surface, STONE_LINE, (px + bw + 1, r.y + 6), (px + bw + 1, r.bottom - 5), 1)
        # 青苔點綴
        for mx, my in self.moss_spots:
            pygame.draw.circle(surface, MOSS_GREEN, (r.x + mx, r.y + my + 2), 3)
        # 左右邊緣柱（橋頭）
        pillar_w = 6
        pygame.draw.rect(surface, STONE_DARK, (r.x, r.y - 4, pillar_w, r.h + 4))
        pygame.draw.rect(surface, STONE_DARK, (r.right - pillar_w, r.y - 4, pillar_w, r.h + 4))
        pygame.draw.rect(surface, STONE_TOP, (r.x, r.y - 4, pillar_w, 3))
        pygame.draw.rect(surface, STONE_TOP, (r.right - pillar_w, r.y - 4, pillar_w, 3))


# --------------- 玩家類別（勇者） ---------------
class Player:
    """勇者角色，具備移動、跳躍與重力。使用幾何圖形繪製。"""

    def __init__(self, x: float, y: float):
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.vel_y: float = 0.0        # 垂直速度
        self.on_ground: bool = False    # 是否站在平台上
        self.facing_right: bool = True  # 面朝方向

    def handle_input(self, keys):
        """根據鍵盤輸入更新水平移動與跳躍。"""
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED
            self.facing_right = True
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False

    def apply_gravity(self):
        """套用重力讓玩家往下掉。"""
        self.vel_y += GRAVITY
        self.rect.y += int(self.vel_y)

    def check_platform_collision(self, platforms: list[Platform]):
        """檢查玩家是否落在某個平台上。"""
        self.on_ground = False
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                # 只在「從上方落下」時才站上去
                if self.vel_y >= 0 and self.rect.bottom <= plat.rect.top + self.vel_y + 10:
                    self.rect.bottom = plat.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    break

    def is_dead(self) -> bool:
        """掉出螢幕底部 → 死亡。"""
        return self.rect.top > SCREEN_HEIGHT

    def draw(self, surface: pygame.Surface):
        """用幾何圖形繪製勇者角色。"""
        r = self.rect
        cx = r.centerx  # 角色中心 x
        flip = 1 if self.facing_right else -1

        # --- 披風（在身體後面，紅色） ---
        cape_x = cx - 6 * flip
        cape_points = [
            (cape_x, r.y + 14),
            (cape_x - 8 * flip, r.y + 38),
            (cape_x - 2 * flip, r.y + 42),
            (cape_x + 4 * flip, r.y + 36),
        ]
        pygame.draw.polygon(surface, HERO_CAPE, cape_points)

        # --- 靴子 ---
        boot_w, boot_h = 8, 6
        pygame.draw.rect(surface, HERO_BOOTS, (cx - 9, r.bottom - boot_h, boot_w, boot_h))
        pygame.draw.rect(surface, HERO_BOOTS, (cx + 1, r.bottom - boot_h, boot_w, boot_h))

        # --- 腿（膚色） ---
        pygame.draw.rect(surface, HERO_SKIN, (cx - 7, r.y + 34, 5, 8))
        pygame.draw.rect(surface, HERO_SKIN, (cx + 2, r.y + 34, 5, 8))

        # --- 身體 / 戰衣（藍色） ---
        pygame.draw.rect(surface, HERO_TUNIC, (cx - 9, r.y + 14, 18, 21))
        # 腰帶
        pygame.draw.rect(surface, HERO_BELT, (cx - 9, r.y + 28, 18, 4))
        # 腰帶扣（小亮點）
        pygame.draw.rect(surface, (220, 190, 80), (cx - 2, r.y + 29, 4, 2))

        # --- 手臂（膚色） ---
        pygame.draw.rect(surface, HERO_SKIN, (cx - 12, r.y + 16, 4, 14))
        pygame.draw.rect(surface, HERO_SKIN, (cx + 8, r.y + 16, 4, 14))

        # --- 頭部 ---
        head_y = r.y + 2
        # 頭髮（棕色，稍大）
        pygame.draw.rect(surface, HERO_HAIR, (cx - 7, head_y, 14, 6))
        pygame.draw.rect(surface, HERO_HAIR, (cx - 8, head_y + 2, 16, 4))
        # 臉（膚色）
        pygame.draw.rect(surface, HERO_SKIN, (cx - 6, head_y + 4, 12, 10))
        # 眼睛
        eye_x = cx + 3 * flip
        pygame.draw.rect(surface, (30, 30, 30), (eye_x, head_y + 7, 2, 2))

        # --- 劍（持劍手那邊） ---
        sword_x = cx + 11 * flip
        # 劍身
        pygame.draw.rect(surface, HERO_SWORD, (sword_x, r.y + 10, 2, 18))
        # 劍尖
        pygame.draw.polygon(surface, HERO_SWORD, [
            (sword_x, r.y + 10), (sword_x + 1, r.y + 6), (sword_x + 2, r.y + 10)
        ])
        # 劍柄 / 護手
        pygame.draw.rect(surface, HERO_SWORD_HILT, (sword_x - 2, r.y + 28, 6, 3))


# --------------- 生成新平台 ---------------
def generate_platform(last_platform: Platform) -> Platform:
    """在上一個平台的右側隨機生成一個新平台。"""
    gap = random.randint(PLATFORM_GAP_MIN, PLATFORM_GAP_MAX)
    width = random.randint(PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH)
    x = last_platform.rect.right + gap

    # 新平台的 y 座標在上一個平台附近隨機偏移，但限制在合理範圍內
    y = last_platform.rect.y + random.randint(-PLATFORM_Y_VARIATION, PLATFORM_Y_VARIATION)
    y = max(200, min(y, SCREEN_HEIGHT - 80))  # 限制高度範圍

    return Platform(x, y, width)


# --------------- 遊戲主函式 ---------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("⚔️ 天空之城 — 勇者冒險")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    # 背景裝飾（只生成一次，每次重置不需要重建）
    # 雲朵: (base_x, y, width)
    clouds = [(random.randint(0, SCREEN_WIDTH + 300),
               random.randint(30, 200),
               random.randint(80, 160)) for _ in range(8)]
    # 遠景浮島: (base_x, y, width)
    floating_islands = [(random.randint(0, SCREEN_WIDTH + 600),
                         random.randint(60, 180),
                         random.randint(50, 90)) for _ in range(4)]

    def reset_game():
        """初始化 / 重置所有遊戲狀態。"""
        # 建立初始平台（一條長長的起始石橋）
        start_platform = Platform(0, SCREEN_HEIGHT - 60, 400)
        platforms = [start_platform]

        # 預先生成數個平台填滿畫面
        while platforms[-1].rect.right < SCREEN_WIDTH + 400:
            platforms.append(generate_platform(platforms[-1]))

        player = Player(100, start_platform.rect.top - PLAYER_HEIGHT)
        return player, platforms, 0  # 回傳 (玩家, 平台列表, 距離分數)

    player, platforms, score = reset_game()
    game_over = False

    # ======== 遊戲主迴圈 ========
    while True:
        # ---- 1. 事件處理 ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Game Over 狀態下按任意鍵重新開始
            if event.type == pygame.KEYDOWN and game_over:
                player, platforms, score = reset_game()
                game_over = False

        if not game_over:
            # ---- 2. 更新狀態 ----
            keys = pygame.key.get_pressed()
            player.handle_input(keys)
            player.apply_gravity()
            player.check_platform_collision(platforms)

            # -- 攝影機捲軸 --
            # 當玩家超過畫面左 1/3 處時，世界向左移動
            if player.rect.x > SCROLL_THRESHOLD:
                shift = player.rect.x - SCROLL_THRESHOLD
                player.rect.x = SCROLL_THRESHOLD
                score += shift  # 累計距離分數

                for plat in platforms:
                    plat.rect.x -= shift

            # -- 生成新平台 --
            # 當最右邊的平台快要進入畫面時，繼續生成新的
            while platforms[-1].rect.right < SCREEN_WIDTH + 300:
                platforms.append(generate_platform(platforms[-1]))

            # -- 移除離開畫面的舊平台 --
            platforms = [p for p in platforms if p.rect.right > -50]

            # -- 限制玩家不超出畫面左邊界 --
            if player.rect.left < 0:
                player.rect.left = 0

            # -- 死亡判定 --
            if player.is_dead():
                game_over = True

        # ---- 3. 繪製畫面 ----

        # -- 天空漸層背景（天空之城風格） --
        for y_line in range(SCREEN_HEIGHT):
            ratio = y_line / SCREEN_HEIGHT
            r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * ratio)
            g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * ratio)
            b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y_line), (SCREEN_WIDTH, y_line))

        # -- 飄浮的雲朵（視差捲動） --
        cloud_scroll = int(score * 0.15)  # 雲比前景慢，營造遠景感
        for i, (cx_base, cy, cw) in enumerate(clouds):
            cx = (cx_base - cloud_scroll) % (SCREEN_WIDTH + 300) - 150
            # 雲朵由多個橢圓疊成
            pygame.draw.ellipse(surface=screen, color=CLOUD_SHADOW,
                                rect=(cx - 2, cy + 6, cw, cw // 3))
            pygame.draw.ellipse(surface=screen, color=CLOUD_WHITE,
                                rect=(cx, cy, cw, cw // 3))
            pygame.draw.ellipse(surface=screen, color=CLOUD_WHITE,
                                rect=(cx + cw // 4, cy - cw // 8, cw // 2, cw // 3))

        # -- 遠景浮島剪影 --
        island_scroll = int(score * 0.05)
        for ix_base, iy, iw in floating_islands:
            ix = (ix_base - island_scroll) % (SCREEN_WIDTH + 600) - 200
            # 島嶼底部（倒三角碎石）
            pygame.draw.polygon(screen, (140, 150, 160), [
                (ix, iy + 10), (ix + iw, iy + 10),
                (ix + iw // 2 + 10, iy + 40),
                (ix + iw // 2 - 10, iy + 45),
            ])
            # 島嶼頂面
            pygame.draw.ellipse(screen, (150, 160, 140), (ix - 5, iy, iw + 10, 22))
            # 島上小城堡剪影
            castle_x = ix + iw // 2 - 8
            pygame.draw.rect(screen, (120, 125, 135), (castle_x, iy - 14, 16, 16))
            pygame.draw.polygon(screen, (120, 125, 135), [
                (castle_x - 2, iy - 14), (castle_x + 8, iy - 22), (castle_x + 18, iy - 14)
            ])

        # 繪製所有平台
        for plat in platforms:
            plat.draw(screen)

        # 繪製玩家
        player.draw(screen)

        # 繪製分數 (距離) — 帶陰影文字
        score_str = f"Distance: {int(score)}"
        shadow_text = font.render(score_str, True, (0, 0, 0))
        score_text = font.render(score_str, True, WHITE)
        screen.blit(shadow_text, (17, 17))
        screen.blit(score_text, (15, 15))

        # Game Over 畫面
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))

            go_font = pygame.font.SysFont(None, 72)
            go_text = go_font.render("GAME OVER", True, WHITE)
            go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            screen.blit(go_text, go_rect)

            hint_text = font.render(f"Score: {int(score)}  -  Press any key to restart", True, WHITE)
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            screen.blit(hint_text, hint_rect)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
