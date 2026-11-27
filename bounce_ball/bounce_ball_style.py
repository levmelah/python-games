import random
import sys
import math

import pygame


WIDTH = 960
HEIGHT = 540
FPS = 60

SKY_TOP = (96, 188, 255)
SKY_BOTTOM = (220, 242, 255)
GROUND = (64, 124, 76)
GROUND_DARK = (44, 90, 56)
WHITE = (245, 248, 255)
DANGER = (235, 78, 92)
COIN = (255, 210, 80)


class BounceBallGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Bounce Ball Style")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 26, bold=True)
        self.small = pygame.font.SysFont("Arial", 20)
        self.big = pygame.font.SysFont("Arial", 52, bold=True)
        self.reset_game()

    def reset_game(self):
        self.state = "ready"
        self.score = 0
        self.best = getattr(self, "best", 0)
        self.distance = 0.0
        self.time = 0.0

        self.ground_y = HEIGHT - 88
        self.ball_x = 180.0
        self.ball_y = self.ground_y - 22
        self.ball_r = 22
        self.ball_vy = 0.0
        self.gravity = 0.72
        self.bounce_power = -13.2
        self.air_boost_power = -10.6
        self.air_boost_ready = True
        self.fly_mode = False

        self.world_speed = 5.6
        self.speed_gain = 0.0008

        self.obstacles = []
        self.coins = []
        self.particles = []
        self.clouds = []

        for _ in range(8):
            self.clouds.append([
                random.randint(0, WIDTH),
                random.randint(40, 220),
                random.randint(70, 150),
                random.uniform(0.4, 1.0),
            ])

        self.spawn_timer = 0
        self.coin_timer = 0
        self.air_spawn_timer = 0

    def start(self):
        if self.state != "play":
            self.reset_game()
            self.state = "play"

    def add_particles(self, x, y, color, amount):
        for _ in range(amount):
            self.particles.append(
                {
                    "x": x,
                    "y": y,
                    "vx": random.uniform(-3.0, 3.0),
                    "vy": random.uniform(-4.0, -0.5),
                    "life": random.randint(14, 30),
                    "color": color,
                }
            )

    def spawn_obstacle(self):
        x = WIDTH + random.randint(40, 220)
        kind = random.choice(["spike", "spike", "spike", "box"])
        if kind == "spike":
            w = random.randint(28, 42)
            h = random.randint(28, 52)
            self.obstacles.append({"kind": "spike", "x": x, "w": w, "h": h})
        else:
            w = random.randint(28, 42)
            h = random.randint(36, 70)
            self.obstacles.append({"kind": "box", "x": x, "w": w, "h": h})

    def spawn_air_spike(self):
        x = WIDTH + random.randint(100, 260)
        w = random.randint(26, 40)
        h = random.randint(26, 44)
        if random.random() < 0.5:
            y = random.randint(160, self.ground_y - 130)
            self.obstacles.append({"kind": "air_spike", "x": x, "y": y, "w": w, "h": h})
        else:
            y = random.randint(96, 170)
            self.obstacles.append({"kind": "ceiling_spike", "x": x, "y": y, "w": w, "h": h})

    def spawn_coin(self):
        x = WIDTH + random.randint(80, 220)
        y = self.ground_y - random.randint(90, 170)
        self.coins.append({"x": x, "y": y, "r": 12, "phase": random.random() * 6.28})

    def collide_rect(self, cx, cy, radius, rx, ry, rw, rh):
        closest_x = max(rx, min(cx, rx + rw))
        closest_y = max(ry, min(cy, ry + rh))
        dx = cx - closest_x
        dy = cy - closest_y
        return dx * dx + dy * dy <= radius * radius

    def update(self):
        if self.state != "play":
            return

        self.time += 1 / FPS
        self.world_speed = min(11.5, self.world_speed + self.speed_gain)
        self.distance += self.world_speed * 0.12
        self.score = int(self.distance)

        if self.fly_mode:
            self.ball_vy += self.gravity * 0.32
            self.ball_vy -= 0.45
            self.ball_vy = max(-8.2, self.ball_vy)
        else:
            self.ball_vy += self.gravity
        self.ball_y += self.ball_vy

        # Keep the player visible below HUD while flying.
        top_limit = self.ball_r + 86
        if self.ball_y < top_limit:
            self.ball_y = top_limit
            if self.ball_vy < 0:
                self.ball_vy = 0

        floor = self.ground_y - self.ball_r
        if self.ball_y >= floor:
            self.ball_y = floor
            if self.ball_vy > 1.4:
                self.add_particles(self.ball_x, self.ground_y, (230, 245, 255), 6)
            self.ball_vy = 0
            self.air_boost_ready = True

        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.spawn_obstacle()
            self.spawn_timer = random.randint(38, 76)

        self.coin_timer -= 1
        if self.coin_timer <= 0:
            if random.random() < 0.7:
                self.spawn_coin()
            self.coin_timer = random.randint(45, 90)

        self.air_spawn_timer -= 1
        if self.air_spawn_timer <= 0:
            if self.fly_mode or random.random() < 0.35:
                self.spawn_air_spike()
            self.air_spawn_timer = random.randint(48, 96)

        for cloud in self.clouds:
            cloud[0] -= cloud[3]
            if cloud[0] < -cloud[2] - 30:
                cloud[0] = WIDTH + random.randint(0, 140)
                cloud[1] = random.randint(40, 220)

        for obs in self.obstacles[:]:
            obs["x"] -= self.world_speed
            if obs["x"] + obs["w"] < -20:
                self.obstacles.remove(obs)
                continue

            if obs["kind"] == "box":
                if self.collide_rect(
                    self.ball_x,
                    self.ball_y,
                    self.ball_r,
                    obs["x"],
                    self.ground_y - obs["h"],
                    obs["w"],
                    obs["h"],
                ):
                    self.best = max(self.best, self.score)
                    self.state = "over"
                    self.add_particles(self.ball_x, self.ball_y, DANGER, 22)
                    return
            elif obs["kind"] == "air_spike":
                if self.collide_rect(
                    self.ball_x,
                    self.ball_y,
                    self.ball_r,
                    obs["x"],
                    obs["y"] - obs["h"],
                    obs["w"],
                    obs["h"],
                ):
                    self.best = max(self.best, self.score)
                    self.state = "over"
                    self.add_particles(self.ball_x, self.ball_y, DANGER, 22)
                    return
            elif obs["kind"] == "ceiling_spike":
                if self.collide_rect(
                    self.ball_x,
                    self.ball_y,
                    self.ball_r,
                    obs["x"],
                    obs["y"],
                    obs["w"],
                    obs["h"],
                ):
                    self.best = max(self.best, self.score)
                    self.state = "over"
                    self.add_particles(self.ball_x, self.ball_y, DANGER, 22)
                    return
            else:
                tip_x = obs["x"] + obs["w"] * 0.5
                tip_y = self.ground_y - obs["h"]
                if abs(self.ball_x - tip_x) < self.ball_r + obs["w"] * 0.5 and self.ball_y + self.ball_r > tip_y:
                    self.best = max(self.best, self.score)
                    self.state = "over"
                    self.add_particles(self.ball_x, self.ball_y, DANGER, 22)
                    return

        for coin in self.coins[:]:
            coin["x"] -= self.world_speed
            coin["phase"] += 0.16
            if coin["x"] < -30:
                self.coins.remove(coin)
                continue

            dx = self.ball_x - coin["x"]
            dy = self.ball_y - coin["y"]
            if dx * dx + dy * dy <= (self.ball_r + coin["r"]) ** 2:
                self.score += 8
                self.distance += 8
                self.coins.remove(coin)
                self.add_particles(coin["x"], coin["y"], COIN, 12)

        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.15
            p["vx"] *= 0.98
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

    def draw_background(self):
        for y in range(HEIGHT):
            t = y / max(1, HEIGHT - 1)
            color = (
                int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t),
                int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t),
                int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t),
            )
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))

        for x, y, w, _ in self.clouds:
            pygame.draw.ellipse(self.screen, (245, 252, 255), (x, y, w, w * 0.36))

        pygame.draw.rect(self.screen, GROUND, (0, self.ground_y, WIDTH, HEIGHT - self.ground_y))
        pygame.draw.rect(self.screen, GROUND_DARK, (0, self.ground_y, WIDTH, 8))

    def draw_obstacles(self):
        for obs in self.obstacles:
            if obs["kind"] == "box":
                rect = pygame.Rect(obs["x"], self.ground_y - obs["h"], obs["w"], obs["h"])
                pygame.draw.rect(self.screen, (96, 76, 64), rect, border_radius=5)
                pygame.draw.rect(self.screen, (135, 108, 88), rect, width=3, border_radius=5)
            elif obs["kind"] == "air_spike":
                p1 = (obs["x"], obs["y"])
                p2 = (obs["x"] + obs["w"], obs["y"])
                p3 = (obs["x"] + obs["w"] * 0.5, obs["y"] - obs["h"])
                pygame.draw.polygon(self.screen, (190, 56, 70), [p1, p2, p3])
                pygame.draw.polygon(self.screen, (255, 180, 190), [p1, p2, p3], 2)
            elif obs["kind"] == "ceiling_spike":
                p1 = (obs["x"], obs["y"])
                p2 = (obs["x"] + obs["w"], obs["y"])
                p3 = (obs["x"] + obs["w"] * 0.5, obs["y"] + obs["h"])
                pygame.draw.polygon(self.screen, (170, 46, 66), [p1, p2, p3])
                pygame.draw.polygon(self.screen, (255, 168, 182), [p1, p2, p3], 2)
            else:
                p1 = (obs["x"], self.ground_y)
                p2 = (obs["x"] + obs["w"], self.ground_y)
                p3 = (obs["x"] + obs["w"] * 0.5, self.ground_y - obs["h"])
                pygame.draw.polygon(self.screen, DANGER, [p1, p2, p3])
                pygame.draw.polygon(self.screen, (255, 190, 195), [p1, p2, p3], 2)

    def draw_coins(self):
        for coin in self.coins:
            pulse = 1.0 + 0.15 * math.sin(coin["phase"])
            r = coin["r"] * pulse
            pygame.draw.circle(self.screen, COIN, (int(coin["x"]), int(coin["y"])), int(r))
            pygame.draw.circle(self.screen, (255, 238, 164), (int(coin["x"]), int(coin["y"])), int(r), 2)

    def draw_ball(self):
        px, py = int(self.ball_x), int(self.ball_y)

        # Wings (always visible, flap faster in fly mode)
        flap_speed = 0.46 if self.fly_mode else 0.24
        flap = math.sin(self.time * (14 if self.fly_mode else 8)) * flap_speed
        wing_w = self.ball_r + 14
        wing_h = 12 + abs(flap) * 12
        left_wing = pygame.Rect(px - wing_w - 8, py - wing_h // 2, wing_w, int(wing_h))
        right_wing = pygame.Rect(px + 8, py - wing_h // 2, wing_w, int(wing_h))
        wing_color = (236, 246, 255) if self.fly_mode else (220, 234, 250)
        pygame.draw.ellipse(self.screen, wing_color, left_wing)
        pygame.draw.ellipse(self.screen, wing_color, right_wing)
        pygame.draw.ellipse(self.screen, (170, 196, 230), left_wing, 2)
        pygame.draw.ellipse(self.screen, (170, 196, 230), right_wing, 2)

        pygame.draw.circle(self.screen, (70, 130, 250), (px, py), self.ball_r)
        pygame.draw.circle(self.screen, (220, 240, 255), (px - 8, py - 8), self.ball_r // 3)
        pygame.draw.circle(self.screen, (30, 78, 172), (px, py), self.ball_r, 3)

    def draw_particles(self):
        for p in self.particles:
            pygame.draw.circle(self.screen, p["color"], (int(p["x"]), int(p["y"])), 3)

    def draw_hud(self):
        panel = pygame.Rect(14, 14, 340, 70)
        pygame.draw.rect(self.screen, (12, 26, 60), panel, border_radius=10)
        pygame.draw.rect(self.screen, (80, 130, 230), panel, 2, border_radius=10)
        self.screen.blit(self.font.render(f"Score: {self.score}", True, WHITE), (28, 26))
        self.screen.blit(self.small.render(f"Best: {self.best}", True, (188, 218, 255)), (28, 54))

        if self.state == "ready":
            t1 = self.big.render("Bounce Ball Style", True, WHITE)
            t2 = self.small.render("Space / Up / Left Click = Bounce", True, (232, 240, 255))
            t2b = self.small.render("Press 0 = Fly Mode (with air spikes)", True, (232, 240, 255))
            t3 = self.small.render("Press Space to Start", True, (232, 240, 255))
            self.screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 96))
            self.screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 - 26))
            self.screen.blit(t2b, (WIDTH // 2 - t2b.get_width() // 2, HEIGHT // 2 + 2))
            self.screen.blit(t3, (WIDTH // 2 - t3.get_width() // 2, HEIGHT // 2 + 30))

        if self.state == "over":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.screen.blit(overlay, (0, 0))
            t1 = self.big.render("Game Over", True, WHITE)
            t2 = self.small.render(f"Score: {self.score}    Best: {self.best}", True, (230, 240, 255))
            t3 = self.small.render("Press Space to Restart", True, (230, 240, 255))
            self.screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 86))
            self.screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 - 14))
            self.screen.blit(t3, (WIDTH // 2 - t3.get_width() // 2, HEIGHT // 2 + 16))

    def bounce(self):
        if self.state == "ready":
            self.start()
            return
        if self.state == "over":
            self.start()
            return

        floor = self.ground_y - self.ball_r
        on_ground = self.ball_y >= floor - 1
        if on_ground:
            self.ball_vy = self.bounce_power
            self.air_boost_ready = True
            self.add_particles(self.ball_x, self.ground_y, (200, 232, 255), 8)
        elif self.air_boost_ready:
            self.ball_vy = self.air_boost_power
            self.air_boost_ready = False
            self.add_particles(self.ball_x, self.ball_y, (180, 220, 255), 8)

    def draw(self):
        self.draw_background()
        self.draw_obstacles()
        self.draw_coins()
        self.draw_ball()
        self.draw_particles()
        self.draw_hud()

        mode_text = "Mode: FLY" if self.fly_mode else "Mode: GROUND"
        mode_color = (255, 247, 180) if self.fly_mode else (225, 240, 255)
        self.screen.blit(self.small.render(mode_text, True, mode_color), (WIDTH - 180, 26))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit(0)
                    if event.key in (pygame.K_0, pygame.K_KP0):
                        self.fly_mode = not self.fly_mode
                        if self.fly_mode:
                            self.ball_vy = min(self.ball_vy, -4.0)
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        self.bounce()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.bounce()

            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    BounceBallGame().run()