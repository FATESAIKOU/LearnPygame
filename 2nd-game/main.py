"""
無限捲軸平台跳躍遊戲 (Infinite Scrolling Platformer)
=============================================
- 方向鍵左右移動
- 空白鍵跳躍（僅限站在平台上時）
- 按住 Shift 衝刺（消耗體力，空中放開維持慣性至落地）
- Z 鍵揮刀發射劍氣
- 消滅敵人得分，被碰到扣血
- 掉出畫面底部或血量歸零 → Game Over
"""

import pygame
import random
import sys
import math

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
SPRINT_SPEED = 9           # 衝刺時的速度
JUMP_FORCE = -14
GRAVITY = 0.7

# 體力系統
STAMINA_MAX = 100.0
STAMINA_DRAIN = 1.2        # 衝刺時每幀消耗
STAMINA_REGEN = 0.4        # 非衝刺時每幀恢復
STAMINA_MIN_TO_SPRINT = 10 # 體力低於此值無法啟動衝刺

# 體力條 UI 顏色
STAMINA_BAR_BG = (40, 40, 40, 180)
STAMINA_BAR_GREEN = (50, 200, 80)
STAMINA_BAR_YELLOW = (220, 200, 40)
STAMINA_BAR_RED = (200, 50, 50)
STAMINA_BAR_BORDER = (200, 200, 200)

# 血量系統
HP_MAX = 5
HP_BAR_HEART = (220, 30, 50)      # 愛心紅
HP_BAR_EMPTY = (80, 80, 80)       # 空心灰
INVINCIBLE_FRAMES = 90            # 受傷後無敵幀數 (1.5秒)

# 劍氣設定
SLASH_WIDTH = 28
SLASH_HEIGHT = 10
SLASH_SPEED = 12
SLASH_LIFETIME = 40              # 劍氣存活幀數
SLASH_COOLDOWN = 18              # 攻擊冷卻幀數
SLASH_COLOR = (180, 220, 255)    # 淡藍白劍氣
SLASH_GLOW = (100, 180, 255, 100)

# 敵人設定
ENEMY_WIDTH = 28
ENEMY_HEIGHT = 32
ENEMY_SPEED = 2
ENEMY_COLOR = (120, 40, 160)     # 紫色魔物
ENEMY_EYE = (255, 60, 60)        # 紅眼
ENEMY_SPAWN_INTERVAL = 120       # 每隔幾幀嘗試生成敵人
ENEMY_KILL_SCORE = 50            # 殺敵加分

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
    """勇者角色，具備移動、衝刺、跳躍、體力與奔跑動畫。"""

    def __init__(self, x: float, y: float):
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.vel_y: float = 0.0        # 垂直速度
        self.on_ground: bool = False    # 是否站在平台上
        self.facing_right: bool = True  # 面朝方向

        # 衝刺 & 體力
        self.sprinting: bool = False
        self.stamina: float = STAMINA_MAX
        self.air_momentum: bool = False  # 空中慣性狀態

        # 攻擊
        self.attack_cooldown: int = 0   # 攻擊冷卻倒數
        self.slash_anim: int = 0        # 掮刀動畫計時器

        # 血量
        self.hp: int = HP_MAX
        self.invincible: int = 0        # 無敵幀倒數

        # 奔跑動畫計時器
        self.anim_timer: float = 0.0
        self.is_moving: bool = False

    def handle_input(self, keys, slash_list: list):
        """根據鍵盤輸入更新移動、衝刺、跳躍與攻擊。"""
        self.is_moving = False

        # 判斷是否衝刺（按住 Shift 且體力足夠）
        want_sprint = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

        if self.on_ground:
            # 地面上：正常衝刺判定，並重置空中慣性
            self.sprinting = want_sprint and self.stamina > STAMINA_MIN_TO_SPRINT
            self.air_momentum = False
        else:
            # 空中：如果剛才在衝刺中起跳，標記慣性
            if self.sprinting and not want_sprint:
                self.air_momentum = True
                self.sprinting = False
            elif self.sprinting:
                # 空中繼續按 Shift — 繼續衝刺（消耗體力）
                self.sprinting = self.stamina > 0

        # 決定實際速度
        if self.sprinting or self.air_momentum:
            speed = SPRINT_SPEED
        else:
            speed = PLAYER_SPEED

        if keys[pygame.K_LEFT]:
            self.rect.x -= speed
            self.facing_right = False
            self.is_moving = True
        if keys[pygame.K_RIGHT]:
            self.rect.x += speed
            self.facing_right = True
            self.is_moving = True
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False

        # 攻擊（Z 鍵）
        if keys[pygame.K_z] and self.attack_cooldown <= 0:
            self.attack_cooldown = SLASH_COOLDOWN
            self.slash_anim = 10  # 掮刀動畫持續 10 幀
            # 生成劍氣
            sx = self.rect.right + 4 if self.facing_right else self.rect.left - SLASH_WIDTH - 4
            sy = self.rect.centery
            slash_list.append(SlashProjectile(sx, sy, self.facing_right))

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.slash_anim > 0:
            self.slash_anim -= 1

    def take_damage(self):
        """受到傷害（有無敵保護）。"""
        if self.invincible > 0:
            return
        self.hp -= 1
        self.invincible = INVINCIBLE_FRAMES

    def update_invincible(self):
        if self.invincible > 0:
            self.invincible -= 1

    def update_stamina(self):
        """更新體力：衝刺時消耗，否則緩慢恢復。"""
        if (self.sprinting or self.air_momentum) and self.is_moving:
            self.stamina = max(0, self.stamina - STAMINA_DRAIN)
            if self.stamina <= 0:
                self.sprinting = False
                # 空中慣性不因體力耗盡而停止，但不再消耗
        else:
            self.stamina = min(STAMINA_MAX, self.stamina + STAMINA_REGEN)

    def update_animation(self):
        """更新奔跑動畫計時器。"""
        if self.is_moving and self.on_ground:
            # 衝刺時動畫更快
            speed_mult = 1.8 if self.sprinting else 1.0
            self.anim_timer += speed_mult
        elif self.on_ground:
            # 站立時緩慢歸零（呈現微微呼吸感）
            self.anim_timer *= 0.8

    def apply_gravity(self):
        """套用重力讓玩家往下掉。"""
        self.vel_y += GRAVITY
        self.rect.y += int(self.vel_y)

    def check_platform_collision(self, platforms: list[Platform]):
        """檢查玩家是否落在某個平台上。"""
        self.on_ground = False
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel_y >= 0 and self.rect.bottom <= plat.rect.top + self.vel_y + 10:
                    self.rect.bottom = plat.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.air_momentum = False  # 落地時取消空中慣性
                    break

    def is_dead(self) -> bool:
        """掉出螢幕底部或血量歸零 → 死亡。"""
        return self.rect.top > SCREEN_HEIGHT or self.hp <= 0

    def draw(self, surface: pygame.Surface):
        """用幾何圖形繪製勇者角色（含奔跑動畫）。"""
        # 受傷無敵時閃爍
        if self.invincible > 0 and (self.invincible // 4) % 2 == 1:
            return  # 閃爍幀不繪製

        r = self.rect
        cx = r.centerx
        flip = 1 if self.facing_right else -1

        # === 奔跑動畫偏移量 ===
        # 用 sin 波計算腿部與手臂的擺動幅度
        if self.is_moving and self.on_ground:
            swing = math.sin(self.anim_timer * 0.4)   # -1 ~ 1 的擺動
        elif not self.on_ground:
            swing = 0.3  # 跳躍中腿微張
        else:
            swing = 0  # 站立

        leg_spread = int(swing * 6)    # 腿前後擺動幅度
        arm_swing = int(swing * 5)     # 手臂前後擺動幅度
        body_bob = int(abs(swing) * 2) # 身體上下微彈

        # 衝刺特效：身體前傾
        lean = 3 * flip if (self.sprinting and self.is_moving) else 0

        # --- 衝刺殘影特效 ---
        if self.sprinting and self.is_moving:
            ghost_surf = pygame.Surface((PLAYER_WIDTH + 30, PLAYER_HEIGHT + 10), pygame.SRCALPHA)
            ghost_cx = PLAYER_WIDTH // 2 + 15
            ghost_y = 5
            # 半透明殘影身體
            pygame.draw.rect(ghost_surf, (*HERO_CAPE, 60),
                             (ghost_cx - 9, ghost_y + 14, 18, 21))
            pygame.draw.rect(ghost_surf, (*HERO_TUNIC, 40),
                             (ghost_cx - 7, ghost_y + 16, 14, 18))
            surface.blit(ghost_surf, (r.x - 15 - 8 * flip, r.y - 5))

        by = r.y - body_bob  # 身體 y（含上下彈跳）

        # --- 披風（紅色，衝刺時飄得更遠） ---
        cape_x = cx - 6 * flip + lean
        cape_length = 42 if (self.sprinting and self.is_moving) else 36
        cape_wave = int(math.sin(self.anim_timer * 0.5) * 3)  # 披風飄動
        cape_points = [
            (cape_x, by + 14),
            (cape_x - (10 + cape_wave) * flip, by + cape_length),
            (cape_x - (4 + cape_wave) * flip, by + cape_length + 4),
            (cape_x + 4 * flip, by + 34),
        ]
        pygame.draw.polygon(surface, HERO_CAPE, cape_points)

        # --- 腿（帶奔跑擺動動畫） ---
        # 後腿
        back_leg_x = cx - 4 - leg_spread + lean
        pygame.draw.rect(surface, HERO_SKIN, (back_leg_x, by + 34, 5, 8))
        pygame.draw.rect(surface, HERO_BOOTS, (back_leg_x - 1, by + 42, 7, 6))
        # 前腿
        front_leg_x = cx + 0 + leg_spread + lean
        pygame.draw.rect(surface, HERO_SKIN, (front_leg_x, by + 34, 5, 8))
        pygame.draw.rect(surface, HERO_BOOTS, (front_leg_x - 1, by + 42, 7, 6))

        # --- 身體 / 戰衣（藍色） ---
        pygame.draw.rect(surface, HERO_TUNIC, (cx - 9 + lean, by + 14, 18, 21))
        # 腰帶
        pygame.draw.rect(surface, HERO_BELT, (cx - 9 + lean, by + 28, 18, 4))
        # 腰帶扣
        pygame.draw.rect(surface, (220, 190, 80), (cx - 2 + lean, by + 29, 4, 2))

        # --- 手臂（帶擺動動畫） ---
        # 後手臂
        back_arm_y = by + 16 - arm_swing
        pygame.draw.rect(surface, HERO_SKIN, (cx - 12 + lean, back_arm_y, 4, 14))
        # 前手臂
        front_arm_y = by + 16 + arm_swing
        pygame.draw.rect(surface, HERO_SKIN, (cx + 8 + lean, front_arm_y, 4, 14))

        # --- 頭部 ---
        head_y = by + 2
        # 頭髮
        pygame.draw.rect(surface, HERO_HAIR, (cx - 7 + lean, head_y, 14, 6))
        pygame.draw.rect(surface, HERO_HAIR, (cx - 8 + lean, head_y + 2, 16, 4))
        # 臉
        pygame.draw.rect(surface, HERO_SKIN, (cx - 6 + lean, head_y + 4, 12, 10))
        # 眼睛
        eye_x = cx + 3 * flip + lean
        pygame.draw.rect(surface, (30, 30, 30), (eye_x, head_y + 7, 2, 2))

        # --- 劍 ---
        sword_x = cx + 11 * flip + lean
        sword_bob = -arm_swing if self.facing_right else arm_swing
        sy = by + 10 + sword_bob
        pygame.draw.rect(surface, HERO_SWORD, (sword_x, sy, 2, 18))
        pygame.draw.polygon(surface, HERO_SWORD, [
            (sword_x, sy), (sword_x + 1, sy - 4), (sword_x + 2, sy)
        ])
        pygame.draw.rect(surface, HERO_SWORD_HILT, (sword_x - 2, sy + 18, 6, 3))

        # --- 衝刺 / 空中慣性時腳下揚塵粒子 ---
        if (self.sprinting or self.air_momentum) and self.is_moving and self.on_ground:
            for _ in range(3):
                dx = random.randint(-12, -2) * flip
                dy = random.randint(-4, 2)
                size = random.randint(2, 4)
                alpha = random.randint(60, 120)
                dust = pygame.Surface((size, size), pygame.SRCALPHA)
                dust.fill((180, 170, 150, alpha))
                surface.blit(dust, (cx + dx - size // 2, r.bottom + dy - size))

        # --- 掮刀動畫（弧形斬擊特效） ---
        if self.slash_anim > 0:
            arc_progress = 1.0 - (self.slash_anim / 10.0)
            arc_alpha = max(30, int(200 * (self.slash_anim / 10.0)))
            arc_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
            start_angle = -0.5 if flip == 1 else 2.1
            end_angle = start_angle + 2.0 * arc_progress
            pygame.draw.arc(arc_surf, (*SLASH_COLOR, arc_alpha),
                            (0, 0, 48, 48), start_angle, end_angle, 3)
            arc_x = cx + 10 * flip - 25
            arc_y = by + 5
            surface.blit(arc_surf, (arc_x, arc_y))

    def draw_hp(self, surface: pygame.Surface):
        """用愛心圖示顯示血量。"""
        start_x, start_y = 15, 68
        heart_size = 16
        spacing = 22
        for i in range(HP_MAX):
            x = start_x + i * spacing
            color = HP_BAR_HEART if i < self.hp else HP_BAR_EMPTY
            # 簡易愛心：兩個圓 + 三角形
            radius = heart_size // 4
            pygame.draw.circle(surface, color, (x + radius, start_y + radius), radius)
            pygame.draw.circle(surface, color, (x + heart_size - radius, start_y + radius), radius)
            pygame.draw.polygon(surface, color, [
                (x, start_y + radius),
                (x + heart_size, start_y + radius),
                (x + heart_size // 2, start_y + heart_size)
            ])

    def draw_stamina_bar(self, surface: pygame.Surface):
        """在畫面左上角繪製體力條。"""
        bar_x, bar_y = 15, 48
        bar_w, bar_h = 160, 12

        # 背景
        bg = pygame.Surface((bar_w + 4, bar_h + 4), pygame.SRCALPHA)
        bg.fill(STAMINA_BAR_BG)
        surface.blit(bg, (bar_x - 2, bar_y - 2))

        # 體力比例
        ratio = self.stamina / STAMINA_MAX
        fill_w = int(bar_w * ratio)

        # 根據體力量變色
        if ratio > 0.5:
            color = STAMINA_BAR_GREEN
        elif ratio > 0.25:
            color = STAMINA_BAR_YELLOW
        else:
            color = STAMINA_BAR_RED

        # 填充
        if fill_w > 0:
            pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, bar_h))

        # 邊框
        pygame.draw.rect(surface, STAMINA_BAR_BORDER, (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), 1)

        # 標籤
        small_font = pygame.font.SysFont(None, 20)
        label = small_font.render("STAMINA", True, WHITE)
        surface.blit(label, (bar_x + bar_w + 8, bar_y - 1))


# --------------- 劍氣投射物 ---------------
class SlashProjectile:
    """勇者掮出的劍氣波，水平飛行並傷害敵人。"""

    def __init__(self, x: float, y: float, facing_right: bool):
        self.direction = 1 if facing_right else -1
        self.rect = pygame.Rect(x, y - SLASH_HEIGHT // 2, SLASH_WIDTH, SLASH_HEIGHT)
        self.life = SLASH_LIFETIME
        self.anim_timer = 0

    def update(self):
        self.rect.x += SLASH_SPEED * self.direction
        self.life -= 1
        self.anim_timer += 1

    def is_alive(self) -> bool:
        return self.life > 0 and -50 < self.rect.x < SCREEN_WIDTH + 50

    def draw(self, surface: pygame.Surface):
        # 劍氣主體 — 發光淡藍弧形
        alpha = max(40, int(255 * (self.life / SLASH_LIFETIME)))
        wave = math.sin(self.anim_timer * 0.6) * 2

        # 外光暈
        glow = pygame.Surface((SLASH_WIDTH + 12, SLASH_HEIGHT + 12), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (100, 180, 255, alpha // 3),
                            (0, 0, SLASH_WIDTH + 12, SLASH_HEIGHT + 12))
        surface.blit(glow, (self.rect.x - 6, self.rect.y - 6 + wave))

        # 劍氣本體
        slash_surf = pygame.Surface((SLASH_WIDTH, SLASH_HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(slash_surf, (*SLASH_COLOR, alpha),
                            (0, int(wave), SLASH_WIDTH, SLASH_HEIGHT))
        # 中心亮線
        pygame.draw.line(slash_surf, (255, 255, 255, alpha),
                         (4, SLASH_HEIGHT // 2 + int(wave)),
                         (SLASH_WIDTH - 4, SLASH_HEIGHT // 2 + int(wave)), 2)
        surface.blit(slash_surf, self.rect.topleft)


# --------------- 敵人類別 ---------------
class Enemy:
    """紫色魔物敵人，在平台上左右巡邏。"""

    def __init__(self, platform: Platform):
        # 隨機放在平台上
        x = random.randint(int(platform.rect.x + 10),
                           max(int(platform.rect.x + 11), int(platform.rect.right - ENEMY_WIDTH - 10)))
        y = platform.rect.top - ENEMY_HEIGHT
        self.rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.platform = platform
        self.speed = ENEMY_SPEED * random.choice([-1, 1])
        self.alive = True
        self.anim_timer = random.randint(0, 100)
        # 死亡動畫
        self.dying = False
        self.death_timer = 0

    def update(self):
        if self.dying:
            self.death_timer += 1
            return

        self.anim_timer += 1
        # 在平台上左右巡邏
        self.rect.x += self.speed
        # 碰到平台邊緣就轉向
        if self.rect.left <= self.platform.rect.left + 5:
            self.speed = abs(self.speed)
        elif self.rect.right >= self.platform.rect.right - 5:
            self.speed = -abs(self.speed)

    def kill(self):
        """開始死亡動畫。"""
        self.dying = True
        self.death_timer = 0

    def is_finished(self) -> bool:
        """死亡動畫播完。"""
        return self.dying and self.death_timer > 15

    def draw(self, surface: pygame.Surface):
        r = self.rect

        if self.dying:
            # 死亡動畫：閃爍 + 縮小
            if self.death_timer % 4 < 2:
                return  # 閃爍
            shrink = self.death_timer * 2
            dr = pygame.Rect(r.x + shrink // 2, r.y + shrink // 2,
                             max(2, r.w - shrink), max(2, r.h - shrink))
            pygame.draw.rect(surface, (255, 200, 100), dr)
            return

        bob = int(math.sin(self.anim_timer * 0.08) * 3)  # 上下浮動

        # 身體（紫色）
        body_rect = pygame.Rect(r.x + 2, r.y + 8 + bob, r.w - 4, r.h - 8)
        pygame.draw.rect(surface, ENEMY_COLOR, body_rect)
        # 明亮邊緣
        pygame.draw.rect(surface, (160, 80, 200), (r.x + 2, r.y + 8 + bob, r.w - 4, 4))

        # 紅色眼睛（兩隻）
        eye_y = r.y + 14 + bob
        pygame.draw.rect(surface, ENEMY_EYE, (r.x + 6, eye_y, 4, 4))
        pygame.draw.rect(surface, ENEMY_EYE, (r.x + r.w - 10, eye_y, 4, 4))
        # 瞳孔
        pygame.draw.rect(surface, (255, 255, 200), (r.x + 7, eye_y + 1, 2, 2))
        pygame.draw.rect(surface, (255, 255, 200), (r.x + r.w - 9, eye_y + 1, 2, 2))

        # 小角（魔物特徵）
        pygame.draw.polygon(surface, (100, 30, 140), [
            (r.x + 5, r.y + 8 + bob), (r.x + 8, r.y + bob), (r.x + 11, r.y + 8 + bob)
        ])
        pygame.draw.polygon(surface, (100, 30, 140), [
            (r.x + r.w - 11, r.y + 8 + bob), (r.x + r.w - 8, r.y + bob),
            (r.x + r.w - 5, r.y + 8 + bob)
        ])


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
        slashes: list[SlashProjectile] = []
        enemies: list[Enemy] = []
        return player, platforms, 0, slashes, enemies

    player, platforms, score, slashes, enemies = reset_game()
    game_over = False
    enemy_spawn_timer = 0

    # ======== 遊戲主迴圈 ========
    while True:
        # ---- 1. 事件處理 ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Game Over 狀態下按任意鍵重新開始
            if event.type == pygame.KEYDOWN and game_over:
                player, platforms, score, slashes, enemies = reset_game()
                enemy_spawn_timer = 0
                game_over = False

        if not game_over:
            # ---- 2. 更新狀態 ----
            keys = pygame.key.get_pressed()
            player.handle_input(keys, slashes)
            player.update_stamina()
            player.update_animation()
            player.update_invincible()
            player.apply_gravity()
            player.check_platform_collision(platforms)

            # -- 更新劍氣 --
            for s in slashes:
                s.update()
            slashes = [s for s in slashes if s.is_alive()]

            # -- 更新敵人 --
            for e in enemies:
                e.update()
            enemies = [e for e in enemies if not e.is_finished()]

            # -- 劍氣 vs 敵人 碰撞 --
            for s in slashes[:]:
                for e in enemies:
                    if not e.dying and s.rect.colliderect(e.rect):
                        e.kill()
                        score += ENEMY_KILL_SCORE
                        s.life = 0  # 劍氣命中後消失
                        break

            # -- 敵人 vs 玩家 碰撞 --
            for e in enemies:
                if not e.dying and player.rect.colliderect(e.rect):
                    player.take_damage()

            # -- 攝影機捲軸 --
            if player.rect.x > SCROLL_THRESHOLD:
                shift = player.rect.x - SCROLL_THRESHOLD
                player.rect.x = SCROLL_THRESHOLD
                score += shift

                for plat in platforms:
                    plat.rect.x -= shift
                for s in slashes:
                    s.rect.x -= shift
                for e in enemies:
                    e.rect.x -= shift
                    e.platform.rect.x -= 0  # platform 已經在上面調過了

            # -- 生成新平台 --
            while platforms[-1].rect.right < SCREEN_WIDTH + 300:
                platforms.append(generate_platform(platforms[-1]))

            # -- 生成敵人 --
            enemy_spawn_timer += 1
            if enemy_spawn_timer >= ENEMY_SPAWN_INTERVAL:
                enemy_spawn_timer = 0
                # 在畫面內的平台上隨機放敵人（避開起始平台和過小的）
                valid = [p for p in platforms
                         if p.rect.right > SCREEN_WIDTH * 0.5
                         and p.rect.w >= ENEMY_WIDTH + 20]
                if valid:
                    plat = random.choice(valid)
                    # 檢查該平台上是否已有敵人
                    has_enemy = any(e.platform is plat and not e.dying for e in enemies)
                    if not has_enemy:
                        enemies.append(Enemy(plat))

            # -- 移除離開畫面的舊平台和敵人 --
            platforms = [p for p in platforms if p.rect.right > -50]
            enemies = [e for e in enemies
                       if not e.is_finished() and e.rect.right > -50]

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

        # 繪製敵人
        for e in enemies:
            e.draw(screen)

        # 繪製劍氣
        for s in slashes:
            s.draw(screen)

        # 繪製玩家
        player.draw(screen)

        # 繪製分數 (距離) — 帶陰影文字
        score_str = f"Distance: {int(score)}"
        shadow_text = font.render(score_str, True, (0, 0, 0))
        score_text = font.render(score_str, True, WHITE)
        screen.blit(shadow_text, (17, 17))
        screen.blit(score_text, (15, 15))

        # 繪製體力條 & 血量
        player.draw_stamina_bar(screen)
        player.draw_hp(screen)

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
