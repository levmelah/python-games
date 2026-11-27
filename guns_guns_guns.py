import os
import math
import random
from collections import deque

import pygame

WIDTH, HEIGHT = 900, 600
FPS = 60
PLAYER_SPEED = 6
BULLET_SPEED = 16
ENEMY_BASE_SPEED = 2.0
MAX_ENEMIES = 12
SPAWN_CHANCE = 0.009
POWERUP_CHANCE = 0.0035
RAPID_FIRE_DURATION = 320
SHIELD_DURATION = 280
LEVEL_SCORE_STEP = 170
# HERE = התיקייה של הקובץ הזה, כדי שהשיא והתמונות יימצאו מכל מקום שמריצים ממנו
HERE = os.path.dirname(os.path.abspath(__file__))
HIGH_SCORE_FILE = os.path.join(HERE, "guns_guns_guns_highscore.txt")
PLAYER_IMAGE_PATH = os.path.join(HERE, "img", "8b7ccfd8-65c4-43db-82e4-70e6af4e50e2 (1).png")
BOSS_IMAGE_PATH = os.path.join(HERE, "img", "download.jpeg")
BOSS_BOTTOM_TRIM_RATIO = 0.17
BACKGROUND_IMAGE_PATH = os.path.join(HERE, "img", "717MFqAl7fL._AC_UF894,1000_QL80_.jpg")
METEOR_BACKGROUND_IMAGE_PATH = os.path.join(HERE, "img", "images (7).jpeg")
METEOR_IMAGE_PATH = os.path.join(HERE, "img", "download (7).jpeg")
BACKGROUND_SCROLL_SPEED = 1.6
METEOR_MODE_LEVEL = 5
ENEMY_IMAGE_PATHS = {
    "normal": os.path.join(HERE, "img", "images (5).jpeg"),
    "fast": os.path.join(HERE, "img", "images (4).jpeg"),
    "shooter": os.path.join(HERE, "img", "images (3).jpeg"),
    "tank": os.path.join(HERE, "img", "images (6).jpeg"),
}

pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

font = pygame.font.SysFont("Arial", 26, bold=True)
small_font = pygame.font.SysFont("Arial", 20)
large_font = pygame.font.SysFont("Arial", 52, bold=True)
menu_font = pygame.font.SysFont("Arial", 38, bold=True)

COLOR_BG = (8, 10, 30)
COLOR_TEXT = (255, 255, 255)
NEBULA_COLORS = [(35, 42, 80), (70, 40, 120), (120, 50, 180)]


def remove_edge_background(surface, tolerance=22):
    width, height = surface.get_size()
    if width == 0 or height == 0:
        return surface

    # Sample border colors (including both checkerboard shades) as background keys.
    sample_points = {
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
    }
    step_x = max(1, width // 8)
    step_y = max(1, height // 8)
    for x in range(0, width, step_x):
        sample_points.add((x, 0))
        sample_points.add((x, height - 1))
    for y in range(0, height, step_y):
        sample_points.add((0, y))
        sample_points.add((width - 1, y))

    bg_colors = []
    for x, y in sample_points:
        r, g, b, a = surface.get_at((x, y))
        if a > 0:
            bg_colors.append((r, g, b))

    if not bg_colors:
        return surface

    def is_background(pixel):
        pr, pg, pb, pa = pixel
        if pa == 0:
            return False
        for br, bg, bb in bg_colors:
            if abs(pr - br) <= tolerance and abs(pg - bg) <= tolerance and abs(pb - bb) <= tolerance:
                return True
        return False

    visited = [[False for _ in range(height)] for _ in range(width)]
    queue = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        if visited[x][y]:
            continue
        visited[x][y] = True

        if not is_background(surface.get_at((x, y))):
            continue

        r, g, b, _ = surface.get_at((x, y))
        surface.set_at((x, y), (r, g, b, 0))

        queue.append((x + 1, y))
        queue.append((x - 1, y))
        queue.append((x, y + 1))
        queue.append((x, y - 1))

    return surface

class Player:
    def __init__(self):
        self.width = 120
        self.height = 120
        self.x = WIDTH // 2
        self.y = HEIGHT - 80
        self.speed = PLAYER_SPEED
        self.color = (50, 200, 255)
        self.cooldown = 0
        self.lives = 5
        self.rapid_fire = 0
        self.shield = 0
        self.sprite = None
        try:
            loaded = pygame.image.load(PLAYER_IMAGE_PATH)
            loaded = pygame.transform.scale(loaded, (self.width, self.height)).convert_alpha()
            for px in range(loaded.get_width()):
                for py in range(loaded.get_height()):
                    r, g, b, a = loaded.get_at((px, py))
                    if r > 235 and g > 235 and b > 235:
                        loaded.set_at((px, py), (r, g, b, 0))
            self.sprite = loaded
        except (pygame.error, FileNotFoundError):
            self.sprite = None

    def move(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        self.x = max(self.width // 2, min(WIDTH - self.width // 2, self.x))

    def shoot(self):
        if self.cooldown == 0:
            self.cooldown = 8 if self.rapid_fire > 0 else 16
            return Bullet(self.x, self.y - self.height // 2)
        return None

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.rapid_fire > 0:
            self.rapid_fire -= 1
        if self.shield > 0:
            self.shield -= 1

    def draw(self, surface):
        if self.sprite is not None:
            surface.blit(self.sprite, (self.x - self.width // 2, self.y - self.height // 2))
        else:
            points = [
                (self.x, self.y - self.height // 2),
                (self.x - self.width // 2, self.y + self.height // 3),
                (self.x + self.width // 2, self.y + self.height // 3),
            ]
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, COLOR_TEXT, points, 3)
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y - 8)), 6)
            wing_left = [(self.x - 16, self.y + 8), (self.x - 28, self.y + 20), (self.x - 8, self.y + 20)]
            wing_right = [(self.x + 16, self.y + 8), (self.x + 28, self.y + 20), (self.x + 8, self.y + 20)]
            pygame.draw.polygon(surface, (70, 180, 255), wing_left)
            pygame.draw.polygon(surface, (70, 180, 255), wing_right)
            pygame.draw.polygon(surface, COLOR_TEXT, wing_left, 2)
            pygame.draw.polygon(surface, COLOR_TEXT, wing_right, 2)
        if self.shield > 0:
            shield_radius = self.width + 8
            shield_surf = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (120, 210, 255, 90), (shield_radius, shield_radius), shield_radius, 8)
            surface.blit(shield_surf, (self.x - shield_radius, self.y - shield_radius))

    def rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

class Bullet:
    def __init__(self, x, y, dy=-BULLET_SPEED, color=(255, 220, 90)):
        self.x = x
        self.y = y
        self.dy = dy
        self.radius = 6
        self.color = color

    def update(self):
        self.y += self.dy

    def draw(self, surface):
        for offset in range(4, 0, -1):
            pygame.draw.circle(surface, (*self.color, max(40, 60 - offset * 8)), (int(self.x), int(self.y + offset * 1)), self.radius + offset)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, COLOR_TEXT, (int(self.x), int(self.y)), self.radius, 1)
        glow_color = (255, 255, 190)
        pygame.draw.circle(surface, glow_color, (int(self.x), int(self.y - 4)), 2)

    def off_screen(self):
        return self.y < -10 or self.y > HEIGHT + 10

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

class Explosion:
    def __init__(self, x, y, color=(255, 180, 90), max_radius=28):
        self.x = x
        self.y = y
        self.color = color
        self.max_radius = max_radius
        self.radius = 4
        self.alpha = 200

    def update(self):
        self.radius += 1.8
        self.alpha -= 14

    def draw(self, surface):
        if self.alpha <= 0:
            return
        surf = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, max(self.alpha, 0)), (self.radius + 2, self.radius + 2), int(self.radius))
        surface.blit(surf, (self.x - self.radius - 2, self.y - self.radius - 2))

    def finished(self):
        return self.alpha <= 0 or self.radius >= self.max_radius

class Particle:
    def __init__(self, x, y, dx, dy, radius, color, life=30):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = radius
        self.color = color
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        self.radius = max(0, self.radius - 0.08)

    def draw(self, surface):
        if self.life <= 0 or self.radius <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        surf = pygame.Surface((int(self.radius * 2 + 4), int(self.radius * 2 + 4)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (int(self.radius + 2), int(self.radius + 2)), int(self.radius))
        surface.blit(surf, (self.x - self.radius - 2, self.y - self.radius - 2))

    def finished(self):
        return self.life <= 0 or self.radius <= 0

class Enemy:
    BASE_SPRITES = {}
    SCALED_SPRITES = {}

    @classmethod
    def _ensure_base_sprites(cls):
        if cls.BASE_SPRITES:
            return
        for enemy_type, path in ENEMY_IMAGE_PATHS.items():
            try:
                image = pygame.image.load(path).convert_alpha()
                image = remove_edge_background(image, tolerance=26)
                cls.BASE_SPRITES[enemy_type] = image
            except (pygame.error, FileNotFoundError):
                cls.BASE_SPRITES[enemy_type] = None

    @classmethod
    def _get_sprite(cls, enemy_type, width, height):
        cls._ensure_base_sprites()
        key = (enemy_type, width, height)
        if key in cls.SCALED_SPRITES:
            return cls.SCALED_SPRITES[key]

        base = cls.BASE_SPRITES.get(enemy_type)
        if base is None:
            cls.SCALED_SPRITES[key] = None
            return None

        sprite = pygame.transform.smoothscale(base, (width, height)).convert_alpha()
        sprite = pygame.transform.rotate(sprite, 180)
        cls.SCALED_SPRITES[key] = sprite
        return sprite

    def __init__(self, difficulty=1):
        self.type = random.choices(["normal", "fast", "tank", "shooter"], weights=[50, 25, 15, 10], k=1)[0]
        self.difficulty = difficulty

        if self.type == "normal":
            self.width = random.randint(72, 92)
            self.height = random.randint(72, 92)
            self.color = (220, 80, 80)
            self.speed = ENEMY_BASE_SPEED + random.random() * 1.3 + difficulty * 0.1
            self.points = 10
            self.health = 1
            self.shoot_timer = random.randint(130, 210)
        elif self.type == "fast":
            self.width = random.randint(64, 80)
            self.height = random.randint(64, 80)
            self.color = (255, 170, 70)
            self.speed = ENEMY_BASE_SPEED + random.random() * 2.0 + difficulty * 0.2
            self.points = 15
            self.health = 1
            self.wave_offset = random.uniform(0, math.pi * 2)
            self.shoot_timer = random.randint(150, 240)
        elif self.type == "shooter":
            self.width = random.randint(74, 92)
            self.height = random.randint(74, 92)
            self.color = (170, 110, 255)
            self.speed = ENEMY_BASE_SPEED + random.random() * 1.1 + difficulty * 0.09
            self.points = 18
            self.health = 1
            self.shoot_timer = random.randint(90, 150)
        else:
            self.width = random.randint(92, 120)
            self.height = random.randint(92, 120)
            self.color = (120, 180, 240)
            self.speed = ENEMY_BASE_SPEED + random.random() * 0.8 + difficulty * 0.08
            self.points = 30
            self.health = 2

        self.x = random.randint(self.width // 2, WIDTH - self.width // 2)
        self.y = random.randint(-260, -70)
        self.sprite = self._get_sprite(self.type, self.width, self.height)

    def update(self):
        if self.type == "fast":
            self.x += math.sin(pygame.time.get_ticks() * 0.005 + self.wave_offset) * 2
        self.y += self.speed
        self.x = max(self.width // 2, min(WIDTH - self.width // 2, self.x))
        if hasattr(self, "shoot_timer"):
            self.shoot_timer -= 1

    def draw(self, surface):
        center = (int(self.x), int(self.y))
        if self.sprite is not None:
            surface.blit(self.sprite, (self.x - self.width // 2, self.y - self.height // 2))
            if self.type == "tank":
                health_text = small_font.render(str(self.health), True, COLOR_TEXT)
                surface.blit(health_text, (center[0] - health_text.get_width() // 2, center[1] - health_text.get_height() // 2))
            return

        if self.type == "normal":
            pygame.draw.circle(surface, self.color, center, self.width // 2)
            pygame.draw.circle(surface, COLOR_TEXT, center, self.width // 2, 2)
            pygame.draw.circle(surface, (255, 220, 190), (center[0], center[1] - 4), 5)
            pygame.draw.arc(surface, (255, 180, 180), (self.x - self.width // 2, self.y - self.height // 2, self.width, self.height), 0.2, 1.4, 2)
        elif self.type == "fast":
            pygame.draw.ellipse(surface, self.color, (self.x - self.width // 2, self.y - self.height // 2, self.width, self.height))
            pygame.draw.ellipse(surface, COLOR_TEXT, (self.x - self.width // 2, self.y - self.height // 2, self.width, self.height), 2)
            pygame.draw.circle(surface, (255, 255, 255), (center[0], center[1]), 5)
            pygame.draw.line(surface, (255, 200, 150), (self.x - self.width // 2, self.y), (self.x + self.width // 2, self.y), 2)
        elif self.type == "shooter":
            points = [
                (self.x, self.y - self.height // 2),
                (self.x - self.width // 3, self.y - self.height // 4),
                (self.x - self.width // 4, self.y + self.height // 2),
                (self.x + self.width // 4, self.y + self.height // 2),
                (self.x + self.width // 3, self.y - self.height // 4),
            ]
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, COLOR_TEXT, points, 2)
            pygame.draw.circle(surface, (255, 190, 255), (center[0], center[1] - 6), 5)
            pygame.draw.circle(surface, (200, 200, 255), (center[0], center[1] + 8), 6, 2)
        else:
            pygame.draw.circle(surface, self.color, center, self.width // 2)
            pygame.draw.circle(surface, COLOR_TEXT, center, self.width // 2, 2)
            pygame.draw.circle(surface, (180, 210, 255), center, self.width // 2 - 8, 3)
            health_text = small_font.render(str(self.health), True, COLOR_TEXT)
            surface.blit(health_text, (center[0] - health_text.get_width() // 2, center[1] - health_text.get_height() // 2))

    def off_screen(self):
        return self.y > HEIGHT + 90

    def rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

    def can_shoot(self):
        return self.type in ("normal", "fast", "shooter") and self.y > 20 and self.shoot_timer <= 0

    def reset_shoot_timer(self):
        if self.type == "normal":
            self.shoot_timer = random.randint(120, 200)
        elif self.type == "fast":
            self.shoot_timer = random.randint(140, 230)
        elif self.type == "shooter":
            self.shoot_timer = random.randint(90, 150)


class Meteor:
    BASE_SPRITE = None
    SCALED_SPRITES = {}

    @classmethod
    def _ensure_base_sprite(cls):
        if cls.BASE_SPRITE is not None:
            return
        try:
            image = pygame.image.load(METEOR_IMAGE_PATH).convert_alpha()
            image = remove_edge_background(image, tolerance=28)
            cls.BASE_SPRITE = image
        except (pygame.error, FileNotFoundError):
            cls.BASE_SPRITE = None

    @classmethod
    def _get_sprite(cls, width, height):
        cls._ensure_base_sprite()
        key = (width, height)
        if key in cls.SCALED_SPRITES:
            return cls.SCALED_SPRITES[key]

        if cls.BASE_SPRITE is None:
            cls.SCALED_SPRITES[key] = None
            return None

        sprite = pygame.transform.smoothscale(cls.BASE_SPRITE, (width, height)).convert_alpha()
        cls.SCALED_SPRITES[key] = sprite
        return sprite

    def __init__(self, difficulty=1):
        self.type = "meteor"
        self.is_meteor = True
        self.width = random.randint(62, 94)
        self.height = random.randint(62, 94)
        self.x = random.randint(self.width // 2, WIDTH - self.width // 2)
        self.y = random.randint(-280, -80)
        self.speed = ENEMY_BASE_SPEED + random.random() * 2.5 + difficulty * 0.12
        self.drift = random.uniform(-1.6, 1.6)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-2.4, 2.4)
        self.points = 0
        self.health = 9999
        self.color = (170, 170, 170)
        self.sprite = self._get_sprite(self.width, self.height)

    def update(self):
        self.y += self.speed
        self.x += self.drift
        self.rotation += self.rotation_speed
        if self.x <= self.width // 2 or self.x >= WIDTH - self.width // 2:
            self.drift *= -1
        self.x = max(self.width // 2, min(WIDTH - self.width // 2, self.x))

    def draw(self, surface):
        if self.sprite is not None:
            rotated = pygame.transform.rotate(self.sprite, self.rotation)
            rect = rotated.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated, rect.topleft)
        else:
            pygame.draw.circle(surface, (140, 140, 140), (int(self.x), int(self.y)), self.width // 2)
            pygame.draw.circle(surface, COLOR_TEXT, (int(self.x), int(self.y)), self.width // 2, 2)

    def off_screen(self):
        return self.y > HEIGHT + 120

    def rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

    def can_shoot(self):
        return False

    def reset_shoot_timer(self):
        return

class Boss:
    def __init__(self, level):
        self.width = 360
        self.height = 260
        self.x = WIDTH // 2
        self.y = -120
        self.speed = 1.4 + level * 0.08
        self.health = 12 + level * 4
        self.max_health = self.health
        self.color = (220, 140, 40)
        self.entered = False
        self.fire_timer = 60
        self.direction = 1
        self.points = 180 + level * 20
        self.sprite = None
        try:
            loaded = pygame.image.load(BOSS_IMAGE_PATH)
            loaded = pygame.transform.scale(loaded, (self.width, self.height)).convert_alpha()
            loaded = remove_edge_background(loaded, tolerance=24)
            trim_pixels = int(self.height * BOSS_BOTTOM_TRIM_RATIO)
            if 0 < trim_pixels < loaded.get_height():
                visible_height = loaded.get_height() - trim_pixels
                loaded = loaded.subsurface((0, 0, loaded.get_width(), visible_height)).copy()
                self.height = visible_height
            self.sprite = loaded
        except (pygame.error, FileNotFoundError):
            self.sprite = None

    def update(self):
        if not self.entered:
            self.y += self.speed
            if self.y >= 100:
                self.entered = True
        else:
            self.x += self.speed * self.direction
            if self.x <= self.width // 2 or self.x >= WIDTH - self.width // 2:
                self.direction *= -1
            self.fire_timer -= 1

    def draw(self, surface):
        if self.sprite is not None:
            surface.blit(self.sprite, (self.x - self.width // 2, self.y - self.height // 2))
        else:
            body_rect = pygame.Rect(0, 0, self.width, self.height)
            body_rect.center = (int(self.x), int(self.y))
            pygame.draw.ellipse(surface, self.color, body_rect)
            pygame.draw.ellipse(surface, COLOR_TEXT, body_rect, 4)

            wing_left = [(self.x - self.width // 2, self.y), (self.x - self.width // 2 - 24, self.y + 22), (self.x - self.width // 2 + 10, self.y + 26)]
            wing_right = [(self.x + self.width // 2, self.y), (self.x + self.width // 2 + 24, self.y + 22), (self.x + self.width // 2 - 10, self.y + 26)]
            pygame.draw.polygon(surface, (210, 140, 60), wing_left)
            pygame.draw.polygon(surface, (210, 140, 60), wing_right)
            pygame.draw.polygon(surface, COLOR_TEXT, wing_left, 2)
            pygame.draw.polygon(surface, COLOR_TEXT, wing_right, 2)

            core = pygame.Rect(0, 0, self.width // 2, self.height // 3)
            core.center = (int(self.x), int(self.y + 4))
            pygame.draw.ellipse(surface, (255, 230, 140), core)
            pygame.draw.ellipse(surface, COLOR_TEXT, core, 2)
        self.draw_health_bar(surface)

    def draw_health_bar(self, surface):
        bar_width = self.width
        bar_height = 10
        ratio = self.health / self.max_health
        background = pygame.Rect(self.x - bar_width // 2, self.y - self.height // 2 - 18, bar_width, bar_height)
        fill = pygame.Rect(background.x, background.y, int(bar_width * ratio), bar_height)
        pygame.draw.rect(surface, (80, 80, 80), background)
        pygame.draw.rect(surface, (220, 60, 60), fill)
        pygame.draw.rect(surface, COLOR_TEXT, background, 2)

    def rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

    def can_shoot(self):
        return self.entered and self.fire_timer <= 0

    def reset_fire_timer(self):
        self.fire_timer = 50

class PowerUp:
    COLORS = {
        "health": (140, 255, 140),
        "rapid": (255, 180, 80),
        "shield": (120, 220, 255),
        "bomb": (255, 120, 120),
    }

    LABELS = {
        "health": "+1",
        "rapid": "R",
        "shield": "S",
        "bomb": "B",
    }

    def __init__(self):
        self.type = random.choice(list(self.COLORS.keys()))
        self.x = random.randint(30, WIDTH - 30)
        self.y = random.randint(-120, -40)
        self.radius = 13
        self.speed = 2.2
        self.color = self.COLORS[self.type]

    def update(self):
        self.y += self.speed

    def draw(self, surface):
        glow = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, 80), (self.radius * 2, self.radius * 2), self.radius * 2)
        surface.blit(glow, (self.x - self.radius * 2, self.y - self.radius * 2))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, COLOR_TEXT, (int(self.x), int(self.y)), self.radius, 2)
        label = small_font.render(self.LABELS[self.type], True, COLOR_TEXT)
        surface.blit(label, (self.x - label.get_width() // 2, self.y - label.get_height() // 2))
        mini = self.radius // 2
        pygame.draw.circle(surface, COLOR_TEXT, (int(self.x), int(self.y - mini)), 1)
        pygame.draw.circle(surface, COLOR_TEXT, (int(self.x), int(self.y + mini)), 1)

    def off_screen(self):
        return self.y > HEIGHT + 20

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Guns Guns Guns")
        self.clock = pygame.time.Clock()
        self.background_image = None
        self.meteor_background_image = None
        self.background_offset = 0.0
        try:
            self.background_image = pygame.image.load(BACKGROUND_IMAGE_PATH).convert()
            self.background_image = pygame.transform.scale(self.background_image, (WIDTH, HEIGHT))
        except (pygame.error, FileNotFoundError):
            self.background_image = None
        try:
            self.meteor_background_image = pygame.image.load(METEOR_BACKGROUND_IMAGE_PATH).convert()
            self.meteor_background_image = pygame.transform.scale(self.meteor_background_image, (WIDTH, HEIGHT))
        except (pygame.error, FileNotFoundError):
            self.meteor_background_image = None
        self.player = Player()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = [Enemy() for _ in range(6)]
        self.powerups = []
        self.explosions = []
        self.particles = []
        self.score = 0
        self.level = 1
        self.combo = 1
        self.combo_timer = 0
        self.state = "menu"
        self.game_over = False
        self.boss = None
        self.next_boss_level = 200
        self.high_score = self.load_high_score()
        self.stars = [(random.randrange(0, WIDTH), random.randrange(0, HEIGHT), random.randint(1, 3)) for _ in range(90)]
        self.message_timer = 0
        self.message = ""

    def load_high_score(self):
        if not os.path.exists(HIGH_SCORE_FILE):
            return 0
        try:
            with open(HIGH_SCORE_FILE, "r") as fp:
                return int(fp.read().strip() or 0)
        except (ValueError, OSError):
            return 0

    def save_high_score(self):
        try:
            with open(HIGH_SCORE_FILE, "w") as fp:
                fp.write(str(self.high_score))
        except OSError:
            pass

    def spawn_enemy(self):
        if len(self.enemies) < MAX_ENEMIES and self.boss is None:
            if self.is_meteor_mode():
                self.enemies.append(Meteor(difficulty=self.level))
            else:
                self.enemies.append(Enemy(difficulty=self.level))

    def spawn_powerup(self):
        self.powerups.append(PowerUp())

    def spawn_boss(self):
        self.boss = Boss(self.level)
        self.message_timer = 180
        self.message = "Boss Incoming!"

    def spawn_particles(self, x, y, color, amount=14, speed=3.5):
        for _ in range(amount):
            angle = random.uniform(0, math.pi * 2)
            velocity = random.uniform(1.2, speed)
            self.particles.append(Particle(
                x,
                y,
                math.cos(angle) * velocity,
                math.sin(angle) * velocity,
                random.uniform(2.2, 4.2),
                color,
                life=random.randint(18, 32),
            ))

    def draw_background(self):
        active_background = self.meteor_background_image if self.is_meteor_mode() else self.background_image
        if active_background is not None:
            self.background_offset = (self.background_offset + BACKGROUND_SCROLL_SPEED) % HEIGHT
            y = int(self.background_offset)
            self.screen.blit(active_background, (0, y - HEIGHT))
            self.screen.blit(active_background, (0, y))
            return

        for y in range(HEIGHT):
            fade = y / HEIGHT
            color = (
                int(COLOR_BG[0] + (NEBULA_COLORS[0][0] - COLOR_BG[0]) * fade),
                int(COLOR_BG[1] + (NEBULA_COLORS[0][1] - COLOR_BG[1]) * fade),
                int(COLOR_BG[2] + (NEBULA_COLORS[0][2] - COLOR_BG[2]) * fade),
            )
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))

        for radius, offset in [(140, 0.15), (100, 0.3), (80, 0.5)]:
            neb_x = int(WIDTH * (0.5 + math.sin(pygame.time.get_ticks() * offset) * 0.15))
            neb_y = int(HEIGHT * (0.35 + math.cos(pygame.time.get_ticks() * offset) * 0.1))
            neb_color = NEBULA_COLORS[int(offset * 10) % len(NEBULA_COLORS)]
            neb_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(neb_surface, (*neb_color, 40), (radius, radius), radius)
            self.screen.blit(neb_surface, (neb_x - radius, neb_y - radius))

        for index, (x, y, speed) in enumerate(self.stars):
            new_y = y + speed
            if new_y > HEIGHT:
                new_y = 0
                x = random.randrange(0, WIDTH)
            self.stars[index] = (x, new_y, speed)
            star_color = (220, 220, 255) if speed > 1 else (180, 180, 220)
            pygame.draw.circle(self.screen, star_color, (x, int(new_y)), speed)

    def draw_ui(self):
        score_text = font.render(f"Score: {self.score}", True, COLOR_TEXT)
        high_score_text = small_font.render(f"High Score: {self.high_score}", True, COLOR_TEXT)
        lives_text = font.render(f"Lives: {self.player.lives}", True, COLOR_TEXT)
        level_text = font.render(f"Level: {self.level}", True, COLOR_TEXT)
        status = []
        if self.player.rapid_fire > 0:
            status.append("Rapid")
        if self.player.shield > 0:
            status.append("Shield")
        status_text = font.render(" | ".join(status), True, COLOR_TEXT) if status else None

        self.screen.blit(score_text, (20, 18))
        self.screen.blit(high_score_text, (20, 48))
        self.screen.blit(lives_text, (20, 78))
        self.screen.blit(level_text, (WIDTH - level_text.get_width() - 20, 18))
        if status_text:
            self.screen.blit(status_text, (WIDTH - status_text.get_width() - 20, 50))
        if self.boss:
            boss_text = font.render("BOSS INCOMING!", True, (255, 80, 80))
            self.screen.blit(boss_text, (WIDTH // 2 - boss_text.get_width() // 2, 20))

    def draw_menu(self):
        title = large_font.render("Guns Guns Guns", True, (120, 220, 255))
        prompt = font.render("Press SPACE to start", True, COLOR_TEXT)
        controls = ["Move: A/D or Left/Right", "Shoot: Space", "Pause: P", "Restart: R after game over"]
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))
        self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 200))
        for i, text in enumerate(controls):
            line = small_font.render(text, True, COLOR_TEXT)
            self.screen.blit(line, (WIDTH // 2 - line.get_width() // 2, 280 + i * 32))
        footer = small_font.render("Collect power-ups: H = Health, R = Rapid Fire, S = Shield, B = Bomb", True, COLOR_TEXT)
        self.screen.blit(footer, (WIDTH // 2 - footer.get_width() // 2, HEIGHT - 80))

    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        pause_text = large_font.render("Paused", True, COLOR_TEXT)
        hint_text = font.render("Press P to resume", True, COLOR_TEXT)
        self.screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 60))
        self.screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT // 2 + 10))

    def reset(self):
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
        self.player = Player()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = [Enemy() for _ in range(6)]
        self.powerups = []
        self.score = 0
        self.level = 1
        self.state = "menu"
        self.game_over = False
        self.boss = None
        self.next_boss_level = 200
        self.particles = []
        self.message_timer = 0
        self.message = ""

    def show_message(self, text):
        self.message = text
        self.message_timer = 180

    def is_meteor_mode(self):
        return self.level >= METEOR_MODE_LEVEL

    def update_level(self):
        old_level = self.level
        self.level = max(1, self.score // LEVEL_SCORE_STEP + 1)
        if old_level < METEOR_MODE_LEVEL <= self.level:
            self.enemies.clear()
            self.enemy_bullets.clear()
            self.boss = None
            self.show_message("Meteor field! Dodge them!")

    def handle_boss(self):
        if self.boss:
            self.boss.update()
            if self.boss.can_shoot():
                self.enemy_bullets.append(Bullet(self.boss.x, self.boss.y + self.boss.height // 2 + 10, dy=8, color=(255, 120, 120)))
                self.boss.reset_fire_timer()
            if self.boss.rect().colliderect(self.player.rect()):
                if self.player.shield > 0:
                    self.player.shield = 0
                else:
                    self.player.lives -= 1
                self.boss.health -= 1
            for bullet in self.bullets[:]:
                if self.boss.rect().colliderect(bullet.rect()):
                    self.boss.health -= 1
                    self.bullets.remove(bullet)
            if self.boss.health <= 0:
                self.score += self.boss.points
                self.explosions.append(Explosion(self.boss.x, self.boss.y, color=(255, 120, 80), max_radius=70))
                self.spawn_particles(self.boss.x, self.boss.y, (255, 180, 80), amount=22, speed=6.2)
                self.boss = None
                self.next_boss_level += 200
                self.show_message("Boss defeated! Level up!")

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.draw_background()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.score > self.high_score:
                        self.high_score = self.score
                        self.save_high_score()
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if self.state == "menu" and event.key == pygame.K_SPACE:
                        self.state = "playing"
                        self.show_message("Good luck!")
                    elif self.state == "playing" and event.key == pygame.K_p:
                        self.state = "paused"
                    elif self.state == "paused" and event.key == pygame.K_p:
                        self.state = "playing"
                    elif self.game_over and event.key == pygame.K_r:
                        self.reset()

            keys = pygame.key.get_pressed()
            if self.state == "playing" and not self.game_over:
                self.player.move(keys)
                self.player.update()
                if keys[pygame.K_SPACE]:
                    bullet = self.player.shoot()
                    if bullet:
                        self.bullets.append(bullet)

                for bullet in self.bullets[:]:
                    bullet.update()
                    if bullet.off_screen():
                        self.bullets.remove(bullet)

                if random.random() < SPAWN_CHANCE:
                    self.spawn_enemy()
                if random.random() < POWERUP_CHANCE:
                    self.spawn_powerup()

                for enemy in self.enemies[:]:
                    enemy.update()
                    if enemy.off_screen():
                        self.enemies.remove(enemy)
                        continue
                    if not getattr(enemy, "is_meteor", False) and enemy.can_shoot():
                        self.enemy_bullets.append(Bullet(enemy.x, enemy.y + enemy.height // 2 + 10, dy=7, color=(255, 140, 140)))
                        enemy.reset_shoot_timer()
                    if getattr(enemy, "is_meteor", False):
                        if enemy.rect().colliderect(self.player.rect()):
                            if self.player.shield > 0:
                                self.player.shield = 0
                            else:
                                self.player.lives -= 1
                            self.enemies.remove(enemy)
                        if self.player.lives <= 0:
                            self.game_over = True
                            self.state = "game_over"
                            break
                        continue
                    for bullet in self.bullets[:]:
                        if enemy.rect().colliderect(bullet.rect()):
                            self.bullets.remove(bullet)
                            enemy.health -= 1
                            if enemy.health <= 0:
                                self.combo += 1
                                self.combo_timer = 120
                                self.score += enemy.points * self.combo
                                self.explosions.append(Explosion(enemy.x, enemy.y, color=(255, 180, 90), max_radius=34))
                                self.enemies.remove(enemy)
                            break
                    if enemy in self.enemies and enemy.rect().colliderect(self.player.rect()):
                        if self.player.shield > 0:
                            self.player.shield = 0
                        else:
                            self.player.lives -= 1
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                    if self.player.lives <= 0:
                        self.game_over = True
                        self.state = "game_over"
                        break

                for bullet in self.enemy_bullets[:]:
                    bullet.update()
                    if bullet.off_screen():
                        self.enemy_bullets.remove(bullet)
                        continue
                    if bullet.rect().colliderect(self.player.rect()):
                        if self.player.shield > 0:
                            self.player.shield = 0
                        else:
                            self.player.lives -= 1
                        self.enemy_bullets.remove(bullet)
                        if self.player.lives <= 0:
                            self.game_over = True
                            self.state = "game_over"
                            break

                for powerup in self.powerups[:]:
                    powerup.update()
                    if powerup.off_screen():
                        self.powerups.remove(powerup)
                        continue
                    if powerup.rect().colliderect(self.player.rect()):
                        if powerup.type == "health":
                            self.player.lives = min(self.player.lives + 1, 7)
                        elif powerup.type == "rapid":
                            self.player.rapid_fire = RAPID_FIRE_DURATION
                        elif powerup.type == "shield":
                            self.player.shield = SHIELD_DURATION
                        elif powerup.type == "bomb":
                            removed = len(self.enemies)
                            for enemy in self.enemies:
                                self.explosions.append(Explosion(enemy.x, enemy.y, color=(255, 120, 80), max_radius=40))
                                self.spawn_particles(enemy.x, enemy.y, enemy.color, amount=10, speed=4.0)
                            self.enemies.clear()
                            self.score += removed * 12
                            self.show_message("Bomb exploded: cleared the field!")
                        self.powerups.remove(powerup)

                if self.combo_timer > 0:
                    self.combo_timer -= 1
                    if self.combo_timer == 0:
                        self.combo = 1

                self.update_level()
                if not self.is_meteor_mode() and self.boss is None and self.score >= self.next_boss_level:
                    self.spawn_boss()
                if self.boss and not self.is_meteor_mode():
                    self.handle_boss()

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "paused":
                self.draw_ui()
                self.player.draw(self.screen)
                for bullet in self.bullets:
                    bullet.draw(self.screen)
                for enemy in self.enemies:
                    enemy.draw(self.screen)
                for powerup in self.powerups:
                    powerup.draw(self.screen)
                for bullet in self.enemy_bullets:
                    bullet.draw(self.screen)
                if self.boss:
                    self.boss.draw(self.screen)
                self.draw_pause()
                pygame.display.flip()
                continue
            else:
                for bullet in self.bullets:
                    bullet.draw(self.screen)
                for enemy in self.enemies:
                    enemy.draw(self.screen)
                for powerup in self.powerups:
                    powerup.draw(self.screen)
                for bullet in self.enemy_bullets:
                    bullet.draw(self.screen)
                if self.boss:
                    self.boss.draw(self.screen)
                self.player.draw(self.screen)
                self.draw_ui()

                for particle in self.particles:
                    particle.draw(self.screen)

            if self.game_over:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 190))
                self.screen.blit(overlay, (0, 0))
                title = large_font.render("Game Over", True, COLOR_TEXT)
                prompt = font.render("Press R to restart", True, COLOR_TEXT)
                final = small_font.render(f"Score: {self.score}  High Score: {self.high_score}", True, COLOR_TEXT)
                self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 70))
                self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2))
                self.screen.blit(final, (WIDTH // 2 - final.get_width() // 2, HEIGHT // 2 + 40))
                if self.score > self.high_score:
                    best_text = font.render("New high score!", True, (255, 220, 100))
                    self.screen.blit(best_text, (WIDTH // 2 - best_text.get_width() // 2, HEIGHT // 2 + 80))
                    self.high_score = self.score
                    self.save_high_score()

            for explosion in self.explosions[:]:
                explosion.update()
                if explosion.finished():
                    self.explosions.remove(explosion)
                else:
                    explosion.draw(self.screen)

            for particle in self.particles[:]:
                particle.update()
                if particle.finished():
                    self.particles.remove(particle)
                else:
                    particle.draw(self.screen)

            if self.combo > 1:
                combo_text = small_font.render(f"Combo x{self.combo}", True, (255, 220, 120))
                self.screen.blit(combo_text, (WIDTH - combo_text.get_width() - 20, 90))

            if self.message_timer > 0:
                message = font.render(self.message, True, (255, 220, 120))
                self.screen.blit(message, (WIDTH // 2 - message.get_width() // 2, HEIGHT - 50))
                self.message_timer -= 1

            pygame.display.flip()

if __name__ == "__main__":
    Game().run()
