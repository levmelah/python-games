import random
import sys
import math

import pygame


WIDTH, HEIGHT = 960, 540
FPS = 60

GROUND_Y = HEIGHT - 110
PLAYER_SIZE = 44
GRAVITY = 0.8
JUMP_FORCE = -15

START_SPEED = 6
MAX_SPEED = 15
SPEED_UP_EVERY = 300

BG_COLOR = (18, 22, 34)
GROUND_COLOR = (40, 48, 72)
PLAYER_COLOR = (85, 255, 178)
OBSTACLE_COLOR = (255, 90, 130)
TEXT_COLOR = (235, 242, 255)
ACCENT_COLOR = (110, 170, 255)
SKY_TOP = (14, 18, 34)
SKY_BOTTOM = (30, 40, 70)


class Player:
    def __init__(self):
        self.x = 170
        self.y = GROUND_Y - PLAYER_SIZE
        self.size = PLAYER_SIZE
        self.vel_y = 0
        self.on_ground = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False

    def update(self):
        self.vel_y += GRAVITY
        self.y += self.vel_y

        floor_y = GROUND_Y - self.size
        if self.y >= floor_y:
            self.y = floor_y
            self.vel_y = 0
            self.on_ground = True

    def draw(self, surface):
        tilt = -self.vel_y * 2.4
        tilt = max(-35, min(35, tilt))

        square = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        square.fill(PLAYER_COLOR)
        pygame.draw.rect(square, (0, 0, 0, 40), (0, 0, self.size, self.size), 3)

        rotated = pygame.transform.rotate(square, tilt)
        draw_rect = rotated.get_rect(center=self.rect.center)
        surface.blit(rotated, draw_rect)


class Obstacle:
    def __init__(self, x, speed, kind):
        self.kind = kind
        self.x = x
        self.speed = speed

        if self.kind == "spike":
            self.width = random.randint(30, 46)
            self.height = random.randint(42, 92)
            self.y = GROUND_Y - self.height
        elif self.kind == "block":
            self.width = random.randint(38, 64)
            self.height = random.randint(34, 76)
            self.y = GROUND_Y - self.height
        elif self.kind == "double_spike":
            self.width = random.randint(56, 76)
            self.height = random.randint(38, 62)
            self.y = GROUND_Y - self.height
        elif self.kind == "floating_block":
            self.width = random.randint(50, 74)
            self.height = random.randint(22, 34)
            self.y = GROUND_Y - random.randint(130, 210)
        else:
            self.width = random.randint(32, 46)
            self.height = random.randint(40, 86)
            self.y = GROUND_Y - self.height

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, speed):
        self.speed = speed
        self.x -= self.speed

    def draw(self, surface):
        if self.kind == "spike":
            points = [
                (self.x, self.y + self.height),
                (self.x + self.width / 2, self.y),
                (self.x + self.width, self.y + self.height),
            ]
            pygame.draw.polygon(surface, OBSTACLE_COLOR, points)
            pygame.draw.polygon(surface, (255, 220, 230), points, 2)
        elif self.kind == "double_spike":
            left = [
                (self.x, self.y + self.height),
                (self.x + self.width * 0.25, self.y),
                (self.x + self.width * 0.5, self.y + self.height),
            ]
            right = [
                (self.x + self.width * 0.5, self.y + self.height),
                (self.x + self.width * 0.75, self.y),
                (self.x + self.width, self.y + self.height),
            ]
            pygame.draw.polygon(surface, OBSTACLE_COLOR, left)
            pygame.draw.polygon(surface, OBSTACLE_COLOR, right)
            pygame.draw.polygon(surface, (255, 220, 230), left, 2)
            pygame.draw.polygon(surface, (255, 220, 230), right, 2)
        elif self.kind == "floating_block":
            rect = self.rect
            pygame.draw.rect(surface, (255, 130, 160), rect, border_radius=5)
            pygame.draw.rect(surface, (255, 225, 235), rect, 2, border_radius=5)
            chain_x = rect.centerx
            pygame.draw.line(surface, (195, 205, 240), (chain_x, 0), (chain_x, rect.top), 2)
            for y in range(8, rect.top, 16):
                pygame.draw.circle(surface, (220, 228, 255), (chain_x, y), 2)
        else:
            rect = self.rect
            pygame.draw.rect(surface, OBSTACLE_COLOR, rect, border_radius=4)
            pygame.draw.rect(surface, (255, 220, 230), rect, 2, border_radius=4)


def draw_background(surface, tick, speed, state):
    # Vertical gradient sky.
    for y in range(GROUND_Y):
        t = y / max(1, GROUND_Y)
        color = (
            int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t),
            int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t),
            int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t),
        )
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))

    # Twinkling stars.
    for i in range(30):
        sx = int((i * 117 + tick * 7) % (WIDTH + 120)) - 60
        sy = 30 + (i * 37) % (GROUND_Y - 80)
        alpha = 120 + int(80 * (0.5 + 0.5 * math.sin(tick * 0.03 + i)))
        star = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(star, (210, 226, 255, alpha), (2, 2), 2)
        surface.blit(star, (sx, sy))

    # Parallax mountains: far layer.
    far_offset = (tick * 0.12) % 300
    for i in range(-2, 7):
        base_x = i * 300 - far_offset
        points = [
            (base_x, GROUND_Y),
            (base_x + 140, GROUND_Y - 140),
            (base_x + 300, GROUND_Y),
        ]
        pygame.draw.polygon(surface, (34, 44, 78), points)

    # Parallax mountains: near layer.
    near_offset = (tick * 0.32) % 220
    for i in range(-2, 8):
        base_x = i * 220 - near_offset
        points = [
            (base_x, GROUND_Y),
            (base_x + 90, GROUND_Y - 95),
            (base_x + 220, GROUND_Y),
        ]
        pygame.draw.polygon(surface, (44, 58, 96), points)

    pygame.draw.rect(surface, GROUND_COLOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

    pulse = 0.5 + 0.5 * math.sin(tick * 0.08)
    glow = int(70 + pulse * 50)

    # Ground tiles with horizontal movement.
    tile_shift = int((tick * max(2.5, speed * 0.9)) % 40)
    for x in range(-40, WIDTH + 40, 40):
        xx = x - tile_shift
        pygame.draw.line(surface, (58, 72, 106), (xx, GROUND_Y), (xx + 20, GROUND_Y + 24), 2)
        pygame.draw.line(surface, (48, 60, 92), (xx + 20, GROUND_Y + 24), (xx + 40, GROUND_Y), 2)

    pygame.draw.line(surface, (90, 120, glow), (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

    # Speed lines appear while actively running.
    if state == "running":
        for i in range(12):
            sy = 30 + i * 26
            line_len = 22 + (i % 4) * 7
            sx = int((WIDTH - (tick * (4 + speed * 0.5) + i * 90) % (WIDTH + 120)))
            pygame.draw.line(surface, (120, 150, 210), (sx, sy), (sx + line_len, sy), 2)


def reset_game():
    return {
        "player": Player(),
        "obstacles": [],
        "frames": 0,
        "score": 0,
        "best": 0,
        "speed": START_SPEED,
        "spawn_timer": 0,
        "spawn_gap": random.randint(70, 115),
        "state": "menu",
    }


def spawn_obstacle_if_needed(data):
    data["spawn_timer"] += 1
    if data["spawn_timer"] >= data["spawn_gap"]:
        data["spawn_timer"] = 0
        data["spawn_gap"] = random.randint(65, 115)
        score = data["score"]
        weights = [("spike", 55), ("block", 30)]

        if score > 120:
            weights.append(("double_spike", 20))
        if score > 220:
            weights.append(("floating_block", 18))

        kinds = [kind for kind, _ in weights]
        chances = [weight for _, weight in weights]
        kind = random.choices(kinds, weights=chances, k=1)[0]
        data["obstacles"].append(Obstacle(WIDTH + 20, data["speed"], kind))


def update_gameplay(data):
    data["frames"] += 1
    data["score"] = data["frames"] // 3

    data["speed"] = min(MAX_SPEED, START_SPEED + data["score"] / SPEED_UP_EVERY)

    data["player"].update()
    spawn_obstacle_if_needed(data)

    for obstacle in data["obstacles"]:
        obstacle.update(data["speed"])

    data["obstacles"] = [obs for obs in data["obstacles"] if obs.x + obs.width > -10]

    player_rect = data["player"].rect.inflate(-10, -6)
    for obstacle in data["obstacles"]:
        if player_rect.colliderect(obstacle.rect):
            data["best"] = max(data["best"], data["score"])
            data["state"] = "game_over"
            break


def draw_ui(surface, font, small_font, data):
    score_text = font.render(f"Score: {data['score']}", True, TEXT_COLOR)
    best_text = small_font.render(f"Best: {max(data['best'], data['score'])}", True, ACCENT_COLOR)
    speed_text = small_font.render(f"Speed: {data['speed']:.1f}", True, ACCENT_COLOR)

    surface.blit(score_text, (20, 18))
    surface.blit(best_text, (22, 54))
    surface.blit(speed_text, (22, 80))


def draw_center_text(surface, title_font, body_font, line1, line2):
    title = title_font.render(line1, True, TEXT_COLOR)
    body = body_font.render(line2, True, ACCENT_COLOR)

    surface.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
    surface.blit(body, body.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 22)))


def main():
    pygame.init()
    pygame.display.set_caption("Geometry Dash - Mini")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", 50, bold=True)
    font = pygame.font.SysFont("arial", 34, bold=True)
    small_font = pygame.font.SysFont("arial", 24, bold=True)

    data = reset_game()
    running = True
    tick = 0

    while running:
        dt = clock.tick(FPS)
        tick += dt * 0.05

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if data["state"] == "menu" and event.key in (pygame.K_SPACE, pygame.K_UP):
                    data["state"] = "running"
                elif data["state"] == "running" and event.key in (pygame.K_SPACE, pygame.K_UP):
                    data["player"].jump()
                elif data["state"] == "game_over" and event.key == pygame.K_r:
                    best_score = data["best"]
                    data = reset_game()
                    data["best"] = best_score
                    data["state"] = "running"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if data["state"] == "menu":
                    data["state"] = "running"
                elif data["state"] == "running":
                    data["player"].jump()

        if data["state"] == "running":
            update_gameplay(data)

        draw_background(screen, tick, data["speed"], data["state"])

        for obstacle in data["obstacles"]:
            obstacle.draw(screen)
        data["player"].draw(screen)

        draw_ui(screen, font, small_font, data)

        if data["state"] == "menu":
            draw_center_text(
                screen,
                title_font,
                small_font,
                "GEOMETRY DASH",
                "Press SPACE or click to start",
            )
        elif data["state"] == "game_over":
            draw_center_text(
                screen,
                title_font,
                small_font,
                "GAME OVER",
                "Press R to restart",
            )

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
