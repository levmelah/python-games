import math
import random
import sys

import pygame

pygame.init()

W, H = 1000, 620
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Morph Balls Style")
clock = pygame.time.Clock()

# Colors
SKY_TOP = (120, 200, 255)
SKY_BOT = (240, 250, 255)
GROUND = (84, 62, 46)
GRASS = (70, 170, 80)
WHITE = (245, 248, 255)
BLACK = (20, 20, 24)
HUD_BG = (12, 20, 36, 180)

BALL_DEFAULT = (255, 135, 70)
BALL_BALLOON = (255, 95, 170)
BALL_SOFT = (90, 220, 255)
BALL_HEAVY = (110, 95, 255)

GLASS = (180, 235, 255)
WALL = (120, 120, 130)
SPIKE = (180, 70, 70)

font_big = pygame.font.SysFont("Arial", 44, bold=True)
font_med = pygame.font.SysFont("Arial", 24, bold=True)
font_sm = pygame.font.SysFont("Arial", 18)


class Obstacle:
    def __init__(self, x, kind, y, w, h):
        self.x = x
        self.kind = kind  # glass, wall, spikes
        self.y = y
        self.w = w
        self.h = h
        self.broken = False

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))


class MorphBallGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.state = "menu"  # menu, play, win, lose
        self.pause = False

        self.ground_y = H - 84
        self.world_end = 5200

        self.player_x = 160
        self.player_y = self.ground_y - 24
        self.vx = 0.0
        self.vy = 0.0
        self.r = 24

        self.mode = 1  # 1 balloon, 2 soft, 3 heavy
        self.on_ground = True

        self.scroll_x = 0
        self.score = 0
        self.energy = 100
        self.time_left = 90.0

        self.particles = []
        self.obstacles = []
        self.platforms = []
        self._build_world()

    def _build_world(self):
        # Floating platforms
        for x in range(650, 5100, 500):
            py = random.choice([self.ground_y - 120, self.ground_y - 170, self.ground_y - 220])
            self.platforms.append(pygame.Rect(x, py, random.randint(140, 220), 18))

        # Obstacle patterns
        x = 520
        while x < self.world_end - 200:
            pick = random.choice(["glass", "wall", "spikes", "glass", "wall"])
            if pick == "glass":
                h = random.randint(44, 74)
                self.obstacles.append(Obstacle(x, "glass", self.ground_y - h, 20, h))
                x += random.randint(170, 290)
            elif pick == "wall":
                h = random.randint(70, 150)
                self.obstacles.append(Obstacle(x, "wall", self.ground_y - h, 36, h))
                x += random.randint(210, 330)
            else:
                self.obstacles.append(Obstacle(x, "spikes", self.ground_y - 24, 60, 24))
                x += random.randint(180, 300)

    def spawn_break_fx(self, x, y, color):
        for _ in range(18):
            self.particles.append([
                x,
                y,
                random.uniform(-4.2, 4.2),
                random.uniform(-6.2, -0.7),
                random.randint(18, 36),
                color,
            ])

    def set_mode(self, m):
        self.mode = m

    def _mode_params(self):
        if self.mode == 1:  # balloon
            return {
                "color": BALL_BALLOON,
                "max_speed": 4.9,
                "jump": -8.0,
                "gravity": 0.22,
                "air_drag": 0.985,
                "label": "BALLOON",
            }
        if self.mode == 2:  # soft
            return {
                "color": BALL_SOFT,
                "max_speed": 6.3,
                "jump": -10.0,
                "gravity": 0.48,
                "air_drag": 0.993,
                "label": "SOFT",
            }
        # heavy
        return {
            "color": BALL_HEAVY,
            "max_speed": 7.2,
            "jump": -7.1,
            "gravity": 0.70,
            "air_drag": 0.997,
            "label": "HEAVY",
        }

    def collide_platforms(self, prev_y):
        player_rect = pygame.Rect(int(self.player_x - self.r), int(self.player_y - self.r), self.r * 2, self.r * 2)

        # Ground
        self.on_ground = False
        if self.player_y + self.r >= self.ground_y:
            self.player_y = self.ground_y - self.r
            self.vy = 0
            self.on_ground = True

        # Platforms
        for p in self.platforms:
            if player_rect.colliderect(p):
                if prev_y + self.r <= p.top + 5 and self.vy >= 0:
                    self.player_y = p.top - self.r
                    self.vy = 0
                    self.on_ground = True

    def handle_obstacles(self):
        player_rect = pygame.Rect(int(self.player_x - self.r), int(self.player_y - self.r), self.r * 2, self.r * 2)

        for obs in self.obstacles:
            if obs.broken:
                continue
            r = obs.rect
            if not player_rect.colliderect(r):
                continue

            if obs.kind == "glass":
                if self.mode == 2:  # soft can pass and break
                    obs.broken = True
                    self.score += 25
                    self.spawn_break_fx(r.centerx, r.centery, GLASS)
                else:
                    self.player_x -= 22
                    self.vx *= -0.35
                    self.energy -= 10
            elif obs.kind == "wall":
                if self.mode == 3 and abs(self.vx) > 2.4:  # heavy breaks walls
                    obs.broken = True
                    self.score += 40
                    self.spawn_break_fx(r.centerx, r.centery, WALL)
                    self.vx *= 0.65
                else:
                    self.player_x -= 26
                    self.vx *= -0.25
                    self.energy -= 14
            else:  # spikes
                if self.mode == 1:  # balloon can glide above easier but still hurts on touch
                    self.energy -= 14
                else:
                    self.energy -= 22
                self.player_x -= 30
                self.vx *= -0.15
                self.spawn_break_fx(player_rect.centerx, player_rect.centery, SPIKE)

            if self.energy <= 0:
                self.state = "lose"
                return

    def update_particles(self):
        keep = []
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.24
            p[4] -= 1
            if p[4] > 0:
                keep.append(p)
        self.particles = keep

    def update(self, dt, keys):
        if self.state != "play" or self.pause:
            return

        params = self._mode_params()
        accel = 0.35 if self.mode != 3 else 0.42

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx -= accel
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx += accel

        self.vx *= 0.95
        self.vx = max(-params["max_speed"], min(params["max_speed"], self.vx))

        # Balloon mode can float with UP/W held
        if self.mode == 1 and (keys[pygame.K_UP] or keys[pygame.K_w]):
            self.vy -= 0.38

        # Jump
        if self.on_ground and (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]):
            self.vy = params["jump"]
            self.on_ground = False

        prev_y = self.player_y
        self.vy += params["gravity"]
        self.vy *= params["air_drag"]
        self.player_x += self.vx
        self.player_y += self.vy

        self.player_x = max(20, min(self.world_end - 20, self.player_x))

        self.collide_platforms(prev_y)
        self.handle_obstacles()
        self.update_particles()

        # Progress and timer
        self.time_left -= dt
        self.score += int(max(0, self.vx) * 0.7)
        self.scroll_x = max(0, min(self.player_x - 210, self.world_end - W))

        if self.time_left <= 0:
            self.state = "lose"
        if self.player_x >= self.world_end - 70:
            self.score += int(self.energy * 6)
            self.state = "win"

    def draw_bg(self):
        for y in range(H):
            t = y / H
            col = (
                int(SKY_TOP[0] * (1 - t) + SKY_BOT[0] * t),
                int(SKY_TOP[1] * (1 - t) + SKY_BOT[1] * t),
                int(SKY_TOP[2] * (1 - t) + SKY_BOT[2] * t),
            )
            pygame.draw.line(screen, col, (0, y), (W, y))

        # hills
        for i in range(5):
            hx = int((i * 340 - self.scroll_x * (0.18 + i * 0.03)) % (W + 520)) - 260
            hy = self.ground_y - 40 - (i % 2) * 38
            pygame.draw.ellipse(screen, (130, 200, 130), (hx, hy, 520, 150))

        # ground
        pygame.draw.rect(screen, GROUND, (0, self.ground_y, W, H - self.ground_y))
        pygame.draw.rect(screen, GRASS, (0, self.ground_y - 12, W, 14))

    def draw_world(self):
        self.draw_bg()

        # Finish gate
        fx = self.world_end - self.scroll_x
        if -90 < fx < W + 90:
            pygame.draw.rect(screen, (250, 225, 70), (int(fx), self.ground_y - 170, 14, 170))
            pygame.draw.rect(screen, (250, 225, 70), (int(fx + 54), self.ground_y - 170, 14, 170))
            pygame.draw.rect(screen, (240, 245, 255), (int(fx), self.ground_y - 170, 68, 16))
            label = font_sm.render("FINISH", True, BLACK)
            screen.blit(label, (int(fx + 6), self.ground_y - 166))

        for p in self.platforms:
            rx = p.x - self.scroll_x
            if rx + p.w < 0 or rx > W:
                continue
            pygame.draw.rect(screen, (126, 93, 62), (rx, p.y, p.w, p.h), border_radius=6)
            pygame.draw.rect(screen, (80, 170, 90), (rx, p.y - 4, p.w, 6), border_radius=4)

        for obs in self.obstacles:
            if obs.broken:
                continue
            rx = obs.x - self.scroll_x
            if rx + obs.w < 0 or rx > W:
                continue

            if obs.kind == "glass":
                pygame.draw.rect(screen, GLASS, (rx, obs.y, obs.w, obs.h), border_radius=4)
                pygame.draw.rect(screen, WHITE, (rx + 4, obs.y + 8, max(3, obs.w - 8), 6), border_radius=3)
            elif obs.kind == "wall":
                pygame.draw.rect(screen, WALL, (rx, obs.y, obs.w, obs.h), border_radius=4)
                for by in range(int(obs.y) + 8, int(obs.y + obs.h), 12):
                    pygame.draw.line(screen, (90, 90, 96), (rx, by), (rx + obs.w, by), 2)
            else:
                base_x = rx
                for i in range(5):
                    x0 = base_x + i * 12
                    pygame.draw.polygon(screen, SPIKE, [(x0, obs.y + obs.h), (x0 + 6, obs.y), (x0 + 12, obs.y + obs.h)])

        # Ball
        params = self._mode_params()
        sx = int(self.player_x - self.scroll_x)
        sy = int(self.player_y)

        pygame.draw.circle(screen, (0, 0, 0, 90), (sx + 3, self.ground_y + 10), max(8, self.r - 6))
        pygame.draw.circle(screen, params["color"], (sx, sy), self.r)
        pygame.draw.circle(screen, WHITE, (sx - 8, sy - 9), 7)
        pygame.draw.circle(screen, BLACK, (sx - 8, sy - 9), 2)

        if self.mode == 1:
            pygame.draw.ellipse(screen, (255, 180, 220), (sx - 10, sy - self.r - 18, 20, 12), 2)
            pygame.draw.line(screen, (255, 190, 230), (sx, sy - self.r - 6), (sx, sy - self.r - 18), 2)
        elif self.mode == 2:
            pygame.draw.arc(screen, (220, 250, 255), (sx - 13, sy - 13, 26, 26), 0.2, 2.9, 2)
        else:
            pygame.draw.circle(screen, (80, 60, 180), (sx + 9, sy + 8), 6)

        for p in self.particles:
            pygame.draw.circle(screen, p[5], (int(p[0] - self.scroll_x), int(p[1])), 3)

    def draw_hud(self):
        panel = pygame.Surface((W, 70), pygame.SRCALPHA)
        panel.fill(HUD_BG)
        screen.blit(panel, (0, 0))

        params = self._mode_params()
        mode_text = font_med.render(f"MODE: {params['label']}   (1/2/3)", True, WHITE)
        score_text = font_sm.render(f"Score: {self.score}", True, WHITE)
        timer_text = font_sm.render(f"Time: {max(0, int(self.time_left))}", True, WHITE)
        energy_text = font_sm.render(f"Energy", True, WHITE)

        screen.blit(mode_text, (16, 10))
        screen.blit(score_text, (18, 42))
        screen.blit(timer_text, (190, 42))
        screen.blit(energy_text, (300, 42))

        bar_x, bar_y, bw, bh = 360, 45, 220, 14
        pygame.draw.rect(screen, (70, 70, 80), (bar_x, bar_y, bw, bh), border_radius=8)
        fill = int(bw * max(0, self.energy) / 100)
        fill_col = (80, 220, 110) if self.energy > 45 else (255, 185, 70) if self.energy > 20 else (240, 90, 80)
        pygame.draw.rect(screen, fill_col, (bar_x, bar_y, fill, bh), border_radius=8)
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bw, bh), 2, border_radius=8)

        prog = min(1.0, self.player_x / self.world_end)
        px, py, pw, ph = 620, 45, 350, 14
        pygame.draw.rect(screen, (70, 70, 90), (px, py, pw, ph), border_radius=8)
        pygame.draw.rect(screen, (255, 225, 90), (px, py, int(pw * prog), ph), border_radius=8)
        pygame.draw.rect(screen, WHITE, (px, py, pw, ph), 2, border_radius=8)

    def draw_menu(self):
        self.draw_bg()
        title = font_big.render("MORPH BALLS STYLE", True, WHITE)
        hint1 = font_med.render("Move: A/D or Arrows", True, WHITE)
        hint2 = font_med.render("Modes: 1 Balloon  2 Soft  3 Heavy", True, WHITE)
        hint3 = font_med.render("Space/Up/W = Jump (Balloon: hold to float)", True, WHITE)
        btn = pygame.Rect(W // 2 - 120, H // 2 + 70, 240, 62)

        screen.blit(title, title.get_rect(center=(W // 2, H // 2 - 110)))
        screen.blit(hint1, hint1.get_rect(center=(W // 2, H // 2 - 20)))
        screen.blit(hint2, hint2.get_rect(center=(W // 2, H // 2 + 20)))
        screen.blit(hint3, hint3.get_rect(center=(W // 2, H // 2 + 58)))

        pygame.draw.rect(screen, (255, 210, 80), btn, border_radius=14)
        pygame.draw.rect(screen, WHITE, btn, 3, border_radius=14)
        txt = font_med.render("PLAY", True, BLACK)
        screen.blit(txt, txt.get_rect(center=btn.center))
        return btn

    def draw_end(self, won):
        self.draw_bg()
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        title = "YOU WIN" if won else "GAME OVER"
        sub = f"Score: {self.score}"
        t1 = font_big.render(title, True, (255, 230, 120) if won else (255, 140, 130))
        t2 = font_med.render(sub, True, WHITE)
        screen.blit(t1, t1.get_rect(center=(W // 2, H // 2 - 20)))
        screen.blit(t2, t2.get_rect(center=(W // 2, H // 2 + 30)))

        btn = pygame.Rect(W // 2 - 120, H // 2 + 90, 240, 62)
        pygame.draw.rect(screen, (255, 210, 80), btn, border_radius=14)
        pygame.draw.rect(screen, WHITE, btn, 3, border_radius=14)
        txt = font_med.render("RESTART", True, BLACK)
        screen.blit(txt, txt.get_rect(center=btn.center))
        return btn


def main():
    game = MorphBallGame()

    while True:
        dt = clock.tick(60) / 1000.0
        click = False
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    game.set_mode(1)
                elif event.key == pygame.K_2:
                    game.set_mode(2)
                elif event.key == pygame.K_3:
                    game.set_mode(3)
                elif event.key == pygame.K_p:
                    game.pause = not game.pause
                elif event.key == pygame.K_ESCAPE:
                    if game.state == "play":
                        game.state = "menu"

        keys = pygame.key.get_pressed()

        if game.state == "menu":
            btn = game.draw_menu()
            if click and btn.collidepoint(mouse_pos):
                game.state = "play"

        elif game.state == "play":
            game.update(dt, keys)
            game.draw_world()
            game.draw_hud()

        elif game.state == "win":
            btn = game.draw_end(True)
            if click and btn.collidepoint(mouse_pos):
                game.reset()
                game.state = "play"

        elif game.state == "lose":
            btn = game.draw_end(False)
            if click and btn.collidepoint(mouse_pos):
                game.reset()
                game.state = "play"

        if game.pause and game.state == "play":
            pause_t = font_big.render("PAUSED", True, WHITE)
            screen.blit(pause_t, pause_t.get_rect(center=(W // 2, H // 2)))

        pygame.display.flip()


main()
