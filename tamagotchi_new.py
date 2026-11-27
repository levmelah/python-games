import math
import random
import sys

import pygame


WIDTH = 900
HEIGHT = 620
FPS = 60

# 🎨 Цветовые палитры / Color Palettes
PALETTES = {
    "pastel": {  # Мягкие пастельные цвета
        "BG_TOP": (255, 227, 248),
        "BG_BOTTOM": (219, 245, 255),
        "PANEL": (255, 255, 255),
        "PANEL_BORDER": (210, 170, 240),
        "TEXT": (63, 45, 91),
        "WHITE": (245, 248, 255),
        "GOOD": (104, 209, 140),
        "WARN": (243, 201, 104),
        "BAD": (236, 110, 122),
        "ACCENT1": (255, 180, 220),
        "ACCENT2": (180, 220, 255),
    },
    "dark": {  # Тёмная тема
        "BG_TOP": (20, 15, 35),
        "BG_BOTTOM": (10, 5, 20),
        "PANEL": (40, 35, 50),
        "PANEL_BORDER": (100, 80, 150),
        "TEXT": (220, 210, 240),
        "WHITE": (255, 255, 255),
        "GOOD": (80, 255, 120),
        "WARN": (255, 200, 50),
        "BAD": (255, 80, 100),
        "ACCENT1": (200, 100, 255),
        "ACCENT2": (100, 200, 255),
    },
    "neon": {  # Неоновая тема
        "BG_TOP": (10, 10, 30),
        "BG_BOTTOM": (5, 5, 15),
        "PANEL": (20, 20, 40),
        "PANEL_BORDER": (0, 255, 255),
        "TEXT": (0, 255, 255),
        "WHITE": (255, 0, 255),
        "GOOD": (0, 255, 100),
        "WARN": (255, 255, 0),
        "BAD": (255, 50, 100),
        "ACCENT1": (255, 0, 255),
        "ACCENT2": (0, 255, 255),
    },
    "forest": {  # Лесная тема
        "BG_TOP": (144, 196, 125),
        "BG_BOTTOM": (100, 160, 100),
        "PANEL": (210, 240, 200),
        "PANEL_BORDER": (76, 140, 100),
        "TEXT": (40, 80, 50),
        "WHITE": (255, 255, 255),
        "GOOD": (60, 180, 80),
        "WARN": (200, 150, 50),
        "BAD": (180, 60, 60),
        "ACCENT1": (100, 200, 120),
        "ACCENT2": (150, 200, 180),
    },
    "sunset": {  # Закат
        "BG_TOP": (255, 180, 100),
        "BG_BOTTOM": (200, 100, 80),
        "PANEL": (255, 220, 180),
        "PANEL_BORDER": (230, 140, 80),
        "TEXT": (100, 60, 40),
        "WHITE": (255, 255, 255),
        "GOOD": (100, 200, 120),
        "WARN": (255, 150, 50),
        "BAD": (200, 80, 80),
        "ACCENT1": (255, 140, 100),
        "ACCENT2": (255, 200, 150),
    },
}

# Текущая выбранная палитра / Current palette
CURRENT_THEME = "pastel"
COLORS = PALETTES[CURRENT_THEME]

# Для совместимости / Backward compatibility
BG_TOP = COLORS["BG_TOP"]
BG_BOTTOM = COLORS["BG_BOTTOM"]
PANEL = COLORS["PANEL"]
PANEL_BORDER = COLORS["PANEL_BORDER"]
TEXT = COLORS["TEXT"]
WHITE = COLORS["WHITE"]
GOOD = COLORS["GOOD"]
WARN = COLORS["WARN"]
BAD = COLORS["BAD"]


class Button:
    def __init__(self, x, y, w, h, label, action, color):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.action = action
        self.color = color

    def draw(self, surf, font, hovered=False):
        if hovered:
            color = tuple(min(255, c + 24) for c in self.color)
            y_off = -2
        else:
            color = self.color
            y_off = 0
        draw_rect = self.rect.move(0, y_off)
        pygame.draw.rect(surf, color, draw_rect, border_radius=12)
        pygame.draw.rect(surf, (255, 255, 255), self.rect, 2, border_radius=12)
        txt = font.render(self.label, True, (255, 255, 255))
        surf.blit(txt, (draw_rect.centerx - txt.get_width() // 2, draw_rect.centery - txt.get_height() // 2))


class TamagotchiGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tamagotchi New")
        self.clock = pygame.time.Clock()
        
        self.current_theme = "pastel"
        self.update_theme(self.current_theme)

        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        self.small = pygame.font.SysFont("Arial", 18)
        self.big = pygame.font.SysFont("Arial", 44, bold=True)

        self.buttons = []
        self.reset_game()
    
    def update_theme(self, theme_name):
        """Обновляет цветовую тему / Updates color theme"""
        global COLORS, BG_TOP, BG_BOTTOM, PANEL, PANEL_BORDER, TEXT, WHITE, GOOD, WARN, BAD
        self.current_theme = theme_name
        if theme_name in PALETTES:
            COLORS = PALETTES[theme_name]
            BG_TOP = COLORS["BG_TOP"]
            BG_BOTTOM = COLORS["BG_BOTTOM"]
            PANEL = COLORS["PANEL"]
            PANEL_BORDER = COLORS["PANEL_BORDER"]
            TEXT = COLORS["TEXT"]
            WHITE = COLORS["WHITE"]
            GOOD = COLORS["GOOD"]
            WARN = COLORS["WARN"]
            BAD = COLORS["BAD"]

    def reset_game(self):
        self.state = "play"
        self.name = random.choice(["Mochi", "Bibi", "Neko", "Pixel", "Lumi"])
        self.mood_text = "Hi! Take care of me"
        self.pet_color = random.choice([(120, 180, 255), (255, 180, 120), (180, 255, 200), (220, 180, 255)])
        self.time = 0.0
        self.coins = 0
        self.age_days = 0
        self.level = 1
        self.xp = 0
        self.combo = 0
        self.combo_timer = 0
        self.particles = []
        self.theme_list = list(PALETTES.keys())
        self.theme_index = self.theme_list.index(self.current_theme)

        self.hunger = 75.0
        self.energy = 70.0
        self.happiness = 72.0
        self.hygiene = 78.0
        self.health = 85.0

        self.feed_cooldown = 0
        self.sleep_timer = 0
        self.event_timer = 360
        self.face_mode = "neutral"
        self.face_timer = 0
        self.quest = self.make_quest()

        self.buttons = [
            Button(70, 500, 145, 56, "Feed (F)", "feed", (102, 200, 126)),
            Button(235, 500, 145, 56, "Play (P)", "play", (255, 160, 96)),
            Button(400, 500, 145, 56, "Clean (C)", "clean", (88, 175, 245)),
            Button(565, 500, 145, 56, "Sleep (S)", "sleep", (130, 120, 230)),
            Button(730, 500, 110, 56, "Medicine", "med", (232, 96, 124)),
        ]

    def make_quest(self):
        quests = [
            {"action": "feed", "goal": 3, "reward": 5, "label": "Feed your pet"},
            {"action": "play", "goal": 3, "reward": 6, "label": "Play together"},
            {"action": "clean", "goal": 2, "reward": 5, "label": "Keep things clean"},
            {"action": "sleep", "goal": 1, "reward": 7, "label": "Give a good nap"},
            {"action": "med", "goal": 1, "reward": 9, "label": "Use medicine"},
        ]
        picked = random.choice(quests).copy()
        picked["progress"] = 0
        return picked

    def add_need(self, key, delta):
        value = getattr(self, key)
        setattr(self, key, max(0.0, min(100.0, value + delta)))

    def set_face(self, mode, duration=FPS):
        self.face_mode = mode
        self.face_timer = duration

    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= 100:
            self.xp -= 100
            self.level += 1
            self.coins += 4
            self.mood_text = f"Level up! You are now level {self.level}"
            self.set_face("excited", FPS)

    def spawn_particles(self, x, y, color, count=12):
        for _ in range(count):
            self.particles.append(
                {
                    "x": x + random.uniform(-20, 20),
                    "y": y + random.uniform(-12, 12),
                    "vx": random.uniform(-1.8, 1.8),
                    "vy": random.uniform(-2.4, -0.2),
                    "life": random.uniform(22, 42),
                    "size": random.randint(2, 4),
                    "color": color,
                }
            )

    def on_success_action(self, action):
        self.combo = min(8, self.combo + 1)
        self.combo_timer = FPS * 4
        self.gain_xp(8 + self.combo)

        if action == self.quest["action"]:
            self.quest["progress"] += 1
            if self.quest["progress"] >= self.quest["goal"]:
                self.coins += self.quest["reward"]
                self.mood_text = f"Quest complete! +{self.quest['reward']} coins"
                self.set_face("excited", FPS)
                self.quest = self.make_quest()

        bonus = max(0, self.combo - 1) // 2
        if bonus > 0:
            self.coins += bonus

        self.spawn_particles(WIDTH // 2, 250, (255, 255, 255), 10 + self.combo)

    def apply_action(self, action):
        if self.state != "play":
            return

        if action == "feed":
            if self.feed_cooldown > 0:
                self.mood_text = "Still full... wait a bit"
                self.set_face("annoyed", FPS // 2)
                return
            self.add_need("hunger", +20)
            self.add_need("happiness", +4)
            self.add_need("hygiene", -3)
            self.feed_cooldown = FPS * 2
            self.mood_text = "Yummy!"
            self.set_face("happy", FPS)
            self.on_success_action(action)
            return

        if action == "play":
            self.add_need("happiness", +16)
            self.add_need("energy", -8)
            self.add_need("hunger", -4)
            self.coins += 2
            self.mood_text = "That was fun!"
            self.set_face("excited", FPS)
            self.on_success_action(action)
            return

        if action == "clean":
            self.add_need("hygiene", +20)
            self.add_need("happiness", +3)
            self.mood_text = "Sparkly clean"
            self.set_face("happy", FPS)
            self.on_success_action(action)
            return

        if action == "sleep":
            if self.sleep_timer > 0:
                self.mood_text = "Already sleeping"
                self.set_face("sleepy", FPS // 2)
                return
            self.sleep_timer = FPS * 6
            self.mood_text = "Zzz..."
            self.set_face("sleepy", FPS * 2)
            self.on_success_action(action)
            return

        if action == "med":
            if self.coins < 5:
                self.mood_text = "Need 5 coins"
                self.set_face("sad", FPS // 2)
                return
            self.coins -= 5
            self.add_need("health", +25)
            self.add_need("happiness", -2)
            self.mood_text = "Feeling better"
            self.set_face("relief", FPS)
            self.on_success_action(action)

    def update(self):
        if self.state != "play":
            return

        self.time += 1 / FPS

        if self.feed_cooldown > 0:
            self.feed_cooldown -= 1

        if self.face_timer > 0:
            self.face_timer -= 1

        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0

        alive = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.05
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
        self.particles = alive

        if self.sleep_timer > 0:
            self.sleep_timer -= 1
            self.add_need("energy", +0.42)
            self.add_need("hunger", -0.07)
            if self.sleep_timer <= 0:
                self.mood_text = "Good morning"
                self.set_face("happy", FPS)
        else:
            self.add_need("hunger", -0.05)
            self.add_need("energy", -0.03)
            self.add_need("hygiene", -0.04)
            self.add_need("happiness", -0.02)

        self.event_timer -= 1
        if self.event_timer <= 0:
            self.event_timer = random.randint(260, 520)
            event = random.choice(["mess", "gift", "cold", "party"])
            if event == "mess":
                self.add_need("hygiene", -14)
                self.mood_text = "Oops... made a mess"
                self.set_face("sad", FPS)
            elif event == "gift":
                self.coins += 3
                self.add_need("happiness", +10)
                self.mood_text = "Found a shiny coin"
                self.set_face("excited", FPS)
            elif event == "cold":
                self.add_need("health", -10)
                self.mood_text = "Achoo!"
                self.set_face("sick", FPS)
            else:
                self.add_need("happiness", +12)
                self.add_need("energy", -6)
                self.mood_text = "Dance party"
                self.set_face("excited", FPS)

        bad_count = 0
        for need in [self.hunger, self.energy, self.happiness, self.hygiene]:
            if need < 25:
                bad_count += 1

        if bad_count >= 2:
            self.add_need("health", -0.18)
        else:
            self.add_need("health", +0.05)

        self.health = max(0.0, min(100.0, self.health))
        self.age_days = int(self.time // 25)

        if self.face_timer <= 0:
            if self.sleep_timer > 0:
                self.face_mode = "sleepy"
            elif self.health < 30:
                self.face_mode = "sick"
            elif self.energy < 25:
                self.face_mode = "sleepy"
            elif self.happiness > 70:
                self.face_mode = "happy"
            elif self.happiness < 30:
                self.face_mode = "sad"
            else:
                self.face_mode = "neutral"

        if self.health <= 0:
            self.state = "over"
            self.mood_text = "Oh no..."

    def draw_bar(self, x, y, label, value):
        w = 320
        h = 24
        pygame.draw.rect(self.screen, (245, 238, 255), (x, y, w, h), border_radius=10)
        color = GOOD if value >= 60 else WARN if value >= 30 else BAD
        fill_w = int((w - 4) * (value / 100.0))
        pygame.draw.rect(self.screen, color, (x + 2, y + 2, fill_w, h - 4), border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, (x, y, w, h), 2, border_radius=10)
        txt = self.small.render(f"{label}: {int(value)}", True, TEXT)
        self.screen.blit(txt, (x + 10, y + 2))

    def draw_pet(self):
        cx = WIDTH // 2
        cy = 250 + int(math.sin(self.time * 2.5) * 6)

        aura = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        aura_alpha = 45 + int(20 * math.sin(self.time * 3.0)) + self.combo * 6
        pygame.draw.circle(aura, (255, 255, 255, max(20, min(120, aura_alpha))), (cx, cy), 120 + self.level * 2)
        self.screen.blit(aura, (0, 0))

        body_w = 220
        body_h = 160
        pygame.draw.ellipse(self.screen, self.pet_color, (cx - body_w // 2, cy - body_h // 2, body_w, body_h))
        pygame.draw.ellipse(self.screen, (255, 255, 255), (cx - body_w // 2, cy - body_h // 2, body_w, body_h), 3)

        # Ears
        pygame.draw.polygon(self.screen, self.pet_color, [(cx - 70, cy - 46), (cx - 45, cy - 105), (cx - 18, cy - 40)])
        pygame.draw.polygon(self.screen, self.pet_color, [(cx + 70, cy - 46), (cx + 45, cy - 105), (cx + 18, cy - 40)])
        pygame.draw.polygon(self.screen, (255, 214, 230), [(cx - 56, cy - 50), (cx - 43, cy - 84), (cx - 28, cy - 45)])
        pygame.draw.polygon(self.screen, (255, 214, 230), [(cx + 56, cy - 50), (cx + 43, cy - 84), (cx + 28, cy - 45)])

        # Eyes and face expressions
        blink = int(self.time * 2.7) % 25 == 0 and self.face_mode not in ("sleepy", "sick")
        if self.face_mode == "sleepy":
            pygame.draw.line(self.screen, TEXT, (cx - 40, cy - 10), (cx - 16, cy - 10), 3)
            pygame.draw.line(self.screen, TEXT, (cx + 16, cy - 10), (cx + 40, cy - 10), 3)
        elif self.face_mode == "sick":
            pygame.draw.line(self.screen, TEXT, (cx - 38, cy - 16), (cx - 18, cy - 4), 3)
            pygame.draw.line(self.screen, TEXT, (cx - 38, cy - 4), (cx - 18, cy - 16), 3)
            pygame.draw.line(self.screen, TEXT, (cx + 18, cy - 16), (cx + 38, cy - 4), 3)
            pygame.draw.line(self.screen, TEXT, (cx + 18, cy - 4), (cx + 38, cy - 16), 3)
        elif blink:
            pygame.draw.line(self.screen, TEXT, (cx - 40, cy - 10), (cx - 16, cy - 10), 3)
            pygame.draw.line(self.screen, TEXT, (cx + 16, cy - 10), (cx + 40, cy - 10), 3)
        elif self.face_mode == "excited":
            pygame.draw.circle(self.screen, TEXT, (cx - 28, cy - 10), 12)
            pygame.draw.circle(self.screen, TEXT, (cx + 28, cy - 10), 12)
            pygame.draw.circle(self.screen, WHITE, (cx - 30, cy - 14), 4)
            pygame.draw.circle(self.screen, WHITE, (cx + 26, cy - 14), 4)
        else:
            pygame.draw.circle(self.screen, TEXT, (cx - 28, cy - 10), 10)
            pygame.draw.circle(self.screen, TEXT, (cx + 28, cy - 10), 10)
            pygame.draw.circle(self.screen, WHITE, (cx - 31, cy - 14), 3)
            pygame.draw.circle(self.screen, WHITE, (cx + 25, cy - 14), 3)

        # Mouth mood
        if self.face_mode in ("happy", "excited", "relief"):
            pygame.draw.arc(self.screen, TEXT, (cx - 22, cy + 8, 44, 26), 0.2, 2.95, 3)
        elif self.face_mode in ("sad", "sick", "annoyed"):
            pygame.draw.arc(self.screen, TEXT, (cx - 22, cy + 22, 44, 24), 3.3, 6.1, 3)
        elif self.face_mode == "sleepy":
            pygame.draw.line(self.screen, TEXT, (cx - 10, cy + 24), (cx + 10, cy + 24), 3)
        else:
            pygame.draw.line(self.screen, TEXT, (cx - 14, cy + 24), (cx + 14, cy + 24), 3)

        if self.sleep_timer > 0:
            z1 = self.small.render("Z", True, TEXT)
            z2 = self.font.render("Z", True, TEXT)
            self.screen.blit(z1, (cx + 74, cy - 88))
            self.screen.blit(z2, (cx + 102, cy - 120))

        if self.level >= 4:
            crown = [(cx - 24, cy - 97), (cx - 12, cy - 122), (cx, cy - 97), (cx + 12, cy - 122), (cx + 24, cy - 97)]
            pygame.draw.polygon(self.screen, (255, 220, 85), crown)
            pygame.draw.polygon(self.screen, (255, 245, 180), crown, 2)

    def draw(self):
        # gradient bg
        for y in range(HEIGHT):
            t = y / max(1, HEIGHT - 1)
            wave = 0.06 * math.sin(self.time * 0.6 + t * 5.0)
            tt = max(0.0, min(1.0, t + wave))
            col = (
                int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * tt),
                int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * tt),
                int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * tt),
            )
            pygame.draw.line(self.screen, col, (0, y), (WIDTH, y))

        for i in range(18):
            ox = (i * 53 + int(self.time * 24)) % (WIDTH + 80) - 40
            oy = 90 + int(50 * math.sin(self.time * 0.7 + i * 0.6))
            pygame.draw.circle(self.screen, (255, 255, 255), (ox, oy), 2)

        pygame.draw.rect(self.screen, PANEL, (24, 24, WIDTH - 48, HEIGHT - 48), border_radius=24)
        pygame.draw.rect(self.screen, PANEL_BORDER, (24, 24, WIDTH - 48, HEIGHT - 48), 3, border_radius=24)

        title = self.big.render(f"{self.name} the Tamagotchi", True, TEXT)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 42))

        info = self.small.render(f"Age: {self.age_days} days    Coins: {self.coins}    Theme: {self.current_theme.upper()}", True, TEXT)
        self.screen.blit(info, (WIDTH // 2 - info.get_width() // 2, 96))

        lvl = self.small.render(f"Level {self.level}   Combo x{self.combo}", True, TEXT)
        self.screen.blit(lvl, (WIDTH // 2 - lvl.get_width() // 2, 118))

        self.draw_pet()

        self.draw_bar(60, 350, "Hunger", self.hunger)
        self.draw_bar(60, 382, "Energy", self.energy)
        self.draw_bar(60, 414, "Happiness", self.happiness)
        self.draw_bar(520, 350, "Hygiene", self.hygiene)
        self.draw_bar(520, 382, "Health", self.health)

        xp_w = 320
        xp_h = 20
        pygame.draw.rect(self.screen, (240, 233, 252), (520, 414, xp_w, xp_h), border_radius=10)
        fill_w = int((xp_w - 4) * (self.xp / 100.0))
        pygame.draw.rect(self.screen, (156, 122, 255), (522, 416, fill_w, xp_h - 4), border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, (520, 414, xp_w, xp_h), 2, border_radius=10)
        xp_txt = self.small.render(f"XP: {int(self.xp)}/100", True, TEXT)
        self.screen.blit(xp_txt, (530, 414))

        mood = self.font.render(self.mood_text, True, TEXT)
        self.screen.blit(mood, (WIDTH // 2 - mood.get_width() // 2, 452))

        quest = self.small.render(
            f"Quest: {self.quest['label']} ({self.quest['progress']}/{self.quest['goal']})  Reward: {self.quest['reward']} coins",
            True,
            TEXT,
        )
        self.screen.blit(quest, (WIDTH // 2 - quest.get_width() // 2, 478))

        for p in self.particles:
            alpha = int(min(255, p["life"] * 6))
            part = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(part, (*p["color"], alpha), (5, 5), p["size"])
            self.screen.blit(part, (int(p["x"]), int(p["y"])))

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.draw(self.screen, self.small, btn.rect.collidepoint(mouse_pos))

        if self.state == "over":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((20, 6, 40, 165))
            self.screen.blit(overlay, (0, 0))
            t1 = self.big.render("Game Over", True, WHITE)
            t2 = self.small.render("Press R to restart", True, WHITE)
            self.screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 40))
            self.screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 + 20))

    def handle_click(self, pos):
        if self.state != "play":
            return
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                self.apply_action(btn.action)
                break

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit(0)
                    if event.key == pygame.K_r:
                        self.reset_game()
                    if event.key == pygame.K_f:
                        self.apply_action("feed")
                    if event.key == pygame.K_p:
                        self.apply_action("play")
                    if event.key == pygame.K_c:
                        self.apply_action("clean")
                    if event.key == pygame.K_s:
                        self.apply_action("sleep")
                    if event.key == pygame.K_m:
                        self.apply_action("med")
                    # 🎨 Переключение тем / Theme switching
                    if event.key == pygame.K_t:
                        self.theme_index = (self.theme_index + 1) % len(self.theme_list)
                        next_theme = self.theme_list[self.theme_index]
                        self.update_theme(next_theme)
                        self.mood_text = f"Theme: {next_theme.upper()}"
                        self.set_face("excited", FPS // 2)
                    # 1-5 для прямого выбора темы / Direct theme selection
                    if event.key == pygame.K_1 and len(self.theme_list) > 0:
                        self.theme_index = 0
                        self.update_theme(self.theme_list[0])
                        self.mood_text = f"Theme: {self.theme_list[0].upper()}"
                    if event.key == pygame.K_2 and len(self.theme_list) > 1:
                        self.theme_index = 1
                        self.update_theme(self.theme_list[1])
                        self.mood_text = f"Theme: {self.theme_list[1].upper()}"
                    if event.key == pygame.K_3 and len(self.theme_list) > 2:
                        self.theme_index = 2
                        self.update_theme(self.theme_list[2])
                        self.mood_text = f"Theme: {self.theme_list[2].upper()}"
                    if event.key == pygame.K_4 and len(self.theme_list) > 3:
                        self.theme_index = 3
                        self.update_theme(self.theme_list[3])
                        self.mood_text = f"Theme: {self.theme_list[3].upper()}"
                    if event.key == pygame.K_5 and len(self.theme_list) > 4:
                        self.theme_index = 4
                        self.update_theme(self.theme_list[4])
                        self.mood_text = f"Theme: {self.theme_list[4].upper()}"

            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    TamagotchiGame().run()