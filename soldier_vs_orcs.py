"""
Soldier vs Orcs
================
A small top-down action/survival game built with pygame, using the
"Tiny RPG Character Asset Pack" Soldier sprite sheets.

Setup:
    pip install pygame
    Keep this script in the same folder as the "assets" directory
    (Soldier_Idle.png, Soldier_Walk.png, Soldier_Attack01/02/03.png,
     Soldier_Hurt.png, Soldier_Death.png, Arrow01_100x100_.png)

Controls:
    WASD / Arrow keys : move
    Space             : melee attack (3-hit combo)
    F                 : shoot an arrow
    Esc               : quit

Note on the Orc:
    Only the source Orc.aseprite file was available (not an exported
    PNG sprite sheet), so orcs are drawn as simple placeholder shapes.
    Export Orc.aseprite as a horizontal PNG strip (100x100 per frame,
    same convention as the Soldier sheets) and drop it in assets/ as
    "Orc_Walk.png" to have it picked up automatically - see
    load_orc_sheet() below for the exact filename it looks for.
"""

import math
import os
import random
import sys

import pygame

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 960, 600
FRAME_SIZE = 100
PLAYER_SCALE = 2.0                 # soldier drawn at 200x200
DRAW_SIZE = int(FRAME_SIZE * PLAYER_SCALE)
FPS = 60

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

ANIM_FILES = {
    "idle":    ("Soldier_Idle.png", 6),
    "walk":    ("Soldier_Walk.png", 8),
    "attack1": ("Soldier_Attack01.png", 6),
    "attack2": ("Soldier_Attack02.png", 6),
    "attack3": ("Soldier_Attack03.png", 9),
    "hurt":    ("Soldier_Hurt.png", 4),
    "death":   ("Soldier_Death.png", 4),
}
ARROW_FILE = "Arrow01_100x100_.png"

ANIM_SPEED = {   # frames of game-time per sprite-frame (lower = faster)
    "idle": 10, "walk": 7, "attack1": 5, "attack2": 5,
    "attack3": 5, "hurt": 8, "death": 10,
}

COLOR_PARCHMENT = (232, 220, 192)
COLOR_GOLD = (201, 162, 75)
COLOR_BLOOD = (138, 31, 31)
COLOR_BG = (47, 36, 24)
COLOR_NIGHT = (20, 16, 12)


# ---------------------------------------------------------------------------
# Asset loading
# ---------------------------------------------------------------------------
def load_strip(path, frame_count):
    """Load a horizontal sprite strip and slice it into frame surfaces."""
    sheet = pygame.image.load(path).convert_alpha()
    frames = []
    for i in range(frame_count):
        rect = pygame.Rect(i * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE)
        frame = sheet.subsurface(rect).copy()
        frames.append(frame)
    return frames


def load_all_animations():
    animations = {}
    for name, (filename, count) in ANIM_FILES.items():
        path = os.path.join(ASSET_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Missing sprite sheet: {path}\n"
                f"Make sure the 'assets' folder sits next to this script."
            )
        animations[name] = load_strip(path, count)
    return animations


def load_arrow():
    path = os.path.join(ASSET_DIR, ARROW_FILE)
    img = pygame.image.load(path).convert_alpha()
    return img


def load_orc_sheet():
    """Optional: if the user exports Orc.aseprite as Orc_Walk.png
    (100x100 frames, horizontal strip), use it instead of the
    placeholder shape."""
    path = os.path.join(ASSET_DIR, "Orc_Walk.png")
    if os.path.exists(path):
        sheet = pygame.image.load(path).convert_alpha()
        frame_count = sheet.get_width() // FRAME_SIZE
        return load_strip(path, frame_count)
    return None


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 3.2
        self.facing = 1  # 1 right, -1 left
        self.state = "idle"
        self.frame = 0
        self.frame_timer = 0
        self.hp = 100
        self.max_hp = 100
        self.attack_combo = 0
        self.attack_cooldown = 0
        self.hurt_cooldown = 0
        self.alive = True
        self.attack_hit_done = False

    def set_state(self, state):
        if self.state == state:
            return
        self.state = state
        self.frame = 0
        self.frame_timer = 0
        self.attack_hit_done = False

    def rect(self):
        return pygame.Rect(self.x - 40, self.y - 60, 80, 100)

    def update(self, keys, game):
        if not self.alive:
            return

        if self.hurt_cooldown > 0:
            self.hurt_cooldown -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        attacking = self.state.startswith("attack")
        hurting = self.state == "hurt"

        if not attacking and not hurting:
            mx = my = 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                my -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                my += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                mx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                mx += 1

            length = math.hypot(mx, my) or 1
            vx = (mx / length) * self.speed
            vy = (my / length) * self.speed

            if mx != 0:
                self.facing = 1 if mx > 0 else -1

            self.x = max(60, min(WIDTH - 60, self.x + vx))
            self.y = max(80, min(HEIGHT - 40, self.y + vy))

            self.set_state("walk" if (mx != 0 or my != 0) else "idle")

            if keys[pygame.K_SPACE] and self.attack_cooldown <= 0:
                self.attack_combo = (self.attack_combo % 3) + 1
                self.set_state(f"attack{self.attack_combo}")
                self.attack_cooldown = 20
            elif keys[pygame.K_f] and self.attack_cooldown <= 0:
                game.shoot_arrow(self)
                self.attack_cooldown = 18

    def update_animation(self, game):
        speed = ANIM_SPEED.get(self.state, 8)
        total_frames = len(game.animations[self.state])

        self.frame_timer += 1
        if self.frame_timer >= speed:
            self.frame_timer = 0
            self.frame += 1

            if self.state.startswith("attack") and \
               self.frame == int(total_frames * 0.55) and not self.attack_hit_done:
                game.melee_hit(self)
                self.attack_hit_done = True

            if self.frame >= total_frames:
                if self.state.startswith("attack") or self.state == "hurt":
                    self.set_state("idle")
                elif self.state == "death":
                    self.frame = total_frames - 1  # hold last frame
                else:
                    self.frame = 0

    def take_damage(self, dmg):
        if self.hurt_cooldown > 0 or not self.alive:
            return
        self.hp -= dmg
        self.hurt_cooldown = 30
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.set_state("death")
        else:
            self.set_state("hurt")

    def draw(self, surf, animations):
        frames = animations[self.state]
        f = min(self.frame, len(frames) - 1)
        img = frames[f]

        # shadow
        shadow = pygame.Surface((52, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surf.blit(shadow, (self.x - 26, self.y + 32))

        scaled = pygame.transform.scale(img, (DRAW_SIZE, DRAW_SIZE))
        if self.facing < 0:
            scaled = pygame.transform.flip(scaled, True, False)

        if self.hurt_cooldown > 0 and self.state == "hurt":
            scaled = scaled.copy()
            alpha = 180 + int(75 * math.sin(pygame.time.get_ticks() / 40))
            scaled.set_alpha(max(0, min(255, alpha)))

        rect = scaled.get_rect(center=(self.x, self.y - 10))
        surf.blit(scaled, rect)


# ---------------------------------------------------------------------------
# Orc (placeholder shape, or real sprite if Orc_Walk.png is provided)
# ---------------------------------------------------------------------------
class Orc:
    def __init__(self, x, y, wave):
        self.x = x
        self.y = y
        self.hp = 20 + wave * 4
        self.max_hp = self.hp
        self.speed = 1.1 + random.random() * 0.6 + wave * 0.05
        self.hit_timer = 0
        self.facing = 1
        self.bob_phase = random.random() * math.pi * 2
        self.atk_cooldown = 0
        self.dead = False
        self.frame = 0
        self.frame_timer = 0

    def update(self, player):
        if self.dead:
            return
        self.bob_phase += 0.15
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy) or 1
        self.facing = 1 if dx > 0 else -1

        if dist > 46:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
            self.frame_timer += 1
            if self.frame_timer >= 8:
                self.frame_timer = 0
                self.frame += 1
        elif self.atk_cooldown <= 0 and player.alive:
            player.take_damage(6 + random.randint(0, 3))
            self.atk_cooldown = 45

        if self.atk_cooldown > 0:
            self.atk_cooldown -= 1
        if self.hit_timer > 0:
            self.hit_timer -= 1

    def take_damage(self, dmg):
        self.hp -= dmg
        self.hit_timer = 8
        if self.hp <= 0:
            self.dead = True

    def draw(self, surf, orc_frames):
        bob = math.sin(self.bob_phase) * 2
        cx, cy = int(self.x), int(self.y + bob)

        # shadow
        shadow = pygame.Surface((44, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        surf.blit(shadow, (cx - 22, cy + 14))

        if orc_frames:
            f = self.frame % len(orc_frames)
            img = pygame.transform.scale(orc_frames[f], (DRAW_SIZE, DRAW_SIZE))
            if self.facing < 0:
                img = pygame.transform.flip(img, True, False)
            if self.hit_timer > 0:
                img = img.copy()
                white = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                white.fill((255, 255, 255, 120))
                img.blit(white, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            rect = img.get_rect(center=(cx, cy - 10))
            surf.blit(img, rect)
        else:
            body_color = (255, 255, 255) if self.hit_timer > 0 else (61, 90, 61)
            head_color = (255, 255, 255) if self.hit_timer > 0 else (79, 122, 79)
            flip = -1 if self.facing < 0 else 1

            body_pts = [(-16, 20), (-20, -10), (0, -26), (20, -10), (16, 20)]
            body_pts = [(cx + p[0] * flip, cy + p[1]) for p in body_pts]
            pygame.draw.polygon(surf, body_color, body_pts)
            pygame.draw.polygon(surf, (28, 43, 28), body_pts, 2)

            pygame.draw.ellipse(surf, head_color, (cx - 11, cy - 40, 22, 20))
            pygame.draw.ellipse(surf, (28, 43, 28), (cx - 11, cy - 40, 22, 20), 2)

            eye_x = cx + 5 * flip
            pygame.draw.circle(surf, (255, 59, 59), (eye_x, cy - 31), 2)

        # HP bar
        bar_w = 30
        pygame.draw.rect(surf, (32, 0, 0), (cx - bar_w // 2, cy - 46, bar_w, 4))
        pygame.draw.rect(
            surf, (201, 75, 75),
            (cx - bar_w // 2, cy - 46, int(bar_w * max(0, self.hp / self.max_hp)), 4)
        )


# ---------------------------------------------------------------------------
# Arrow
# ---------------------------------------------------------------------------
class Arrow:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.dir = direction
        self.vx = 9 * direction
        self.hit = False

    def update(self):
        self.x += self.vx

    def offscreen(self):
        return self.x < -50 or self.x > WIDTH + 50

    def draw(self, surf, arrow_img):
        img = pygame.transform.scale(arrow_img, (50, 50))
        if self.dir < 0:
            img = pygame.transform.flip(img, True, False)
        rect = img.get_rect(center=(self.x, self.y))
        surf.blit(img, rect)


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self, screen, animations, arrow_img, orc_frames, font, big_font):
        self.screen = screen
        self.animations = animations
        self.arrow_img = arrow_img
        self.orc_frames = orc_frames
        self.font = font
        self.big_font = big_font

        self.state = "start"  # start, playing, gameover
        self.reset()

    def reset(self):
        self.player = Player(WIDTH / 2, HEIGHT / 2)
        self.orcs = []
        self.arrows = []
        self.score = 0
        self.wave = 1
        self.wave_orcs_remaining = 0
        self.wave_spawn_timer = 0
        self.wave_active = False
        self.wave_msg = ""
        self.wave_msg_timer = 0

    def start_wave(self):
        self.wave_orcs_remaining = 3 + self.wave * 2
        self.wave_spawn_timer = 0
        self.wave_active = True
        self.wave_msg = f"גל {self.wave}"
        self.wave_msg_timer = 90

    def spawn_orc(self):
        edge = random.randint(0, 3)
        if edge == 0:
            x, y = -40, random.uniform(0, HEIGHT)
        elif edge == 1:
            x, y = WIDTH + 40, random.uniform(0, HEIGHT)
        elif edge == 2:
            x, y = random.uniform(0, WIDTH), -40
        else:
            x, y = random.uniform(0, WIDTH), HEIGHT + 40
        self.orcs.append(Orc(x, y, self.wave))

    def shoot_arrow(self, player):
        self.arrows.append(Arrow(player.x + player.facing * 30, player.y - 6, player.facing))

    def melee_hit(self, player):
        rng = 70
        for o in self.orcs:
            if o.dead:
                continue
            dx = o.x - player.x
            dy = o.y - player.y
            if abs(dy) < 50 and (
                (player.facing > 0 and 0 < dx < rng) or
                (player.facing < 0 and -rng < dx < 0)
            ):
                o.take_damage(12 + random.randint(0, 5))
                if o.dead:
                    self.score += 10

    def update(self, keys):
        if self.state != "playing":
            return

        self.player.update(keys, self)
        self.player.update_animation(self)

        for a in self.arrows:
            a.update()
            for o in self.orcs:
                if o.dead or a.hit:
                    continue
                if abs(a.x - o.x) < 30 and abs(a.y - o.y) < 34:
                    o.take_damage(15)
                    a.hit = True
                    if o.dead:
                        self.score += 10
        self.arrows = [a for a in self.arrows if not a.hit and not a.offscreen()]

        for o in self.orcs:
            o.update(self.player)
        before = len(self.orcs)
        self.orcs = [o for o in self.orcs if not o.dead]
        removed = before - len(self.orcs)
        if removed > 0:
            self.wave_orcs_remaining -= removed

        if not self.wave_active:
            self.wave_spawn_timer += 1
            if self.wave_spawn_timer > 60:
                self.wave += 1
                self.start_wave()
        else:
            self.wave_spawn_timer += 1
            if (self.wave_spawn_timer > 55 and len(self.orcs) < 6 and
                    self.wave_orcs_remaining > len(self.orcs)):
                self.spawn_orc()
                self.wave_spawn_timer = 0
            if self.wave_orcs_remaining <= 0 and len(self.orcs) == 0:
                self.wave_active = False
                self.wave_spawn_timer = 0

        if self.wave_msg_timer > 0:
            self.wave_msg_timer -= 1

        death_frames = len(self.animations["death"])
        if (not self.player.alive and self.player.frame >= death_frames - 1
                and self.state == "playing"):
            self.state = "gameover"

    def draw(self):
        self.draw_background()

        for o in self.orcs:
            o.draw(self.screen, self.orc_frames)
        for a in self.arrows:
            a.draw(self.screen, self.arrow_img)
        self.player.draw(self.screen, self.animations)

        self.draw_hud()

        if self.wave_msg_timer > 0:
            self.draw_center_text(self.wave_msg, self.big_font, COLOR_GOLD, y=110)

        if self.state == "start":
            self.draw_overlay_start()
        elif self.state == "gameover":
            self.draw_overlay_gameover()

    def draw_background(self):
        self.screen.fill(COLOR_BG)
        grid_color = (0, 0, 0)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(0, WIDTH, 48):
            pygame.draw.line(overlay, (*grid_color, 35), (i, 0), (i, HEIGHT))
        for j in range(0, HEIGHT, 48):
            pygame.draw.line(overlay, (*grid_color, 35), (0, j), (WIDTH, j))
        self.screen.blit(overlay, (0, 0))
        shade = pygame.Surface((WIDTH, 30), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 60))
        self.screen.blit(shade, (0, HEIGHT - 30))

    def draw_hud(self):
        bar_x, bar_y, bar_w, bar_h = 16, 14, 220, 22
        pygame.draw.rect(self.screen, (58, 20, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        hp_ratio = max(0, self.player.hp / self.player.max_hp)
        pygame.draw.rect(
            self.screen, COLOR_BLOOD,
            (bar_x, bar_y, int(bar_w * hp_ratio), bar_h), border_radius=3
        )
        pygame.draw.rect(self.screen, COLOR_GOLD, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=3)

        score_txt = self.font.render(f"ניקוד: {self.score}", True, COLOR_PARCHMENT)
        wave_txt = self.font.render(f"גל: {self.wave}", True, COLOR_PARCHMENT)
        self.screen.blit(score_txt, (WIDTH - 260, 16))
        self.screen.blit(wave_txt, (WIDTH - 120, 16))

        hint = self.font.render(
            "WASD/חיצים = תנועה | רווח = חרב | F = חץ", True, (184, 168, 136)
        )
        self.screen.blit(hint, (16, HEIGHT - 28))

    def draw_center_text(self, text, font, color, y=None):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WIDTH // 2, y if y else HEIGHT // 2))
        self.screen.blit(surf, rect)

    def draw_overlay_start(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        self.draw_center_text("חייל מול אורקים", self.big_font, COLOR_GOLD, y=HEIGHT // 2 - 60)
        self.draw_center_text(
            "לחץ על רווח כדי להתחיל את הקרב", self.font, COLOR_PARCHMENT, y=HEIGHT // 2
        )

    def draw_overlay_gameover(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        self.draw_center_text("נפלת בקרב", self.big_font, COLOR_GOLD, y=HEIGHT // 2 - 60)
        self.draw_center_text(
            f"ניקוד סופי: {self.score} | הגעת לגל {self.wave}",
            self.font, COLOR_PARCHMENT, y=HEIGHT // 2 - 10
        )
        self.draw_center_text(
            "לחץ על רווח כדי לנסות שוב", self.font, COLOR_PARCHMENT, y=HEIGHT // 2 + 30
        )

    def handle_start_key(self):
        if self.state == "start":
            self.state = "playing"
            self.start_wave()
        elif self.state == "gameover":
            self.reset()
            self.state = "playing"
            self.start_wave()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f"[info] Looking for sprites in: {ASSET_DIR}")
    if not os.path.isdir(ASSET_DIR):
        print(f"[error] The 'assets' folder was not found at: {ASSET_DIR}")
        print("        Make sure the 'assets' folder sits in the SAME folder as this .py file.")
        input("Press Enter to exit...")
        sys.exit(1)
    else:
        found = os.listdir(ASSET_DIR)
        print(f"[info] Files found in assets/: {found}")

    pygame.init()
    pygame.display.set_caption("Soldier vs Orcs")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    try:
        animations = load_all_animations()
        arrow_img = load_arrow()
    except Exception as e:
        print(f"[error] Failed to load sprites: {e}")
        pygame.quit()
        input("Press Enter to exit...")
        sys.exit(1)

    orc_frames = load_orc_sheet()  # None unless user supplies Orc_Walk.png

    font = pygame.font.SysFont("arial", 20)
    big_font = pygame.font.SysFont("arial", 46, bold=True)

    game = Game(screen, animations, arrow_img, orc_frames, font, big_font)

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE and game.state != "playing":
                        game.handle_start_key()

            keys = pygame.key.get_pressed()
            game.update(keys)
            game.draw()

            pygame.display.flip()
            clock.tick(FPS)
    except Exception as e:
        pygame.quit()
        print(f"[error] Crashed during gameplay: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
