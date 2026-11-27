import pygame
import random
import math

# === התחלת pygame ===
pygame.init()

# === קבועים ===
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 40
COLS = WIDTH // TILE_SIZE
ROWS = HEIGHT // TILE_SIZE
FPS = 60

# צבעים
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 50, 255)
GREEN = (50, 200, 50)
GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)
DARK_GRAY = (100, 100, 100)

# === מסך ===
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hide and Paint - Python Edition")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 48)

# === מחלקות ===
class Player:
    def __init__(self, x, y, color, name):
        self.x = x
        self.y = y
        self.color = color
        self.name = name
        self.speed = 3
        self.radius = TILE_SIZE // 2 - 4
        self.painted_tiles = set()

    def move(self, dx, dy):
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed
        new_x = max(self.radius, min(WIDTH - self.radius, new_x))
        new_y = max(self.radius, min(HEIGHT - self.radius, new_y))
        
        for other in players:
            if other != self:
                dist = math.hypot(new_x - other.x, new_y - other.y)
                if dist < self.radius + other.radius:
                    return

        self.x = new_x
        self.y = new_y
        
        tile_x = int(self.x // TILE_SIZE)
        tile_y = int(self.y // TILE_SIZE)
        if 0 <= tile_x < COLS and 0 <= tile_y < ROWS:
            self.painted_tiles.add((tile_x, tile_y))
            painted_map[tile_y][tile_x] = self

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 2)
        name_text = font.render(self.name, True, BLACK)
        surface.blit(name_text, (self.x - name_text.get_width() // 2, self.y - self.radius - 25))

    def get_score(self):
        return len(self.painted_tiles)


class Bot:
    def __init__(self, x, y, color, name, difficulty="medium"):
        self.x = x
        self.y = y
        self.color = color
        self.name = name
        self.speed = 2.5
        self.radius = TILE_SIZE // 2 - 4
        self.painted_tiles = set()
        self.difficulty = difficulty
        self.target_x = x
        self.target_y = y
        self.change_target_timer = 0

    def update(self):
        self.change_target_timer += 1
        if self.change_target_timer > random.randint(30, 90):
            unpainted = []
            for r in range(ROWS):
                for c in range(COLS):
                    if painted_map[r][c] is None:
                        dist = math.hypot(c * TILE_SIZE + TILE_SIZE // 2 - self.x,
                                          r * TILE_SIZE + TILE_SIZE // 2 - self.y)
                        unpainted.append((dist, c, r))
            if unpainted:
                unpainted.sort()
                if self.difficulty == "easy":
                    target = random.choice(unpainted[:10])
                elif self.difficulty == "medium":
                    target = unpainted[min(3, len(unpainted) - 1)]
                else:
                    target = unpainted[0]
                self.target_x = target[1] * TILE_SIZE + TILE_SIZE // 2
                self.target_y = target[2] * TILE_SIZE + TILE_SIZE // 2
            self.change_target_timer = 0

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 2:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        
        tile_x = int(self.x // TILE_SIZE)
        tile_y = int(self.y // TILE_SIZE)
        if 0 <= tile_x < COLS and 0 <= tile_y < ROWS:
            self.painted_tiles.add((tile_x, tile_y))
            painted_map[tile_y][tile_x] = self

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 2)
        name_text = font.render(self.name, True, BLACK)
        surface.blit(name_text, (self.x - name_text.get_width() // 2, self.y - self.radius - 25))

    def get_score(self):
        return len(self.painted_tiles)


# === אתחול ===
def reset_game():
    global painted_map, players, bots, game_time, game_over, winner
    painted_map = [[None for _ in range(COLS)] for _ in range(ROWS)]
    players = [Player(100, 100, RED, "Player 1")]
    bots = [
        Bot(700, 500, BLUE, "Bot 1", "medium"),
        Bot(100, 500, GREEN, "Bot 2", "easy"),
    ]
    game_time = 0
    game_over = False
    winner = None


def draw_grid():
    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if painted_map[r][c] is not None:
                color = painted_map[r][c].color
                light_color = (min(255, color[0] + 100), min(255, color[1] + 100), min(255, color[2] + 100))
                pygame.draw.rect(screen, light_color, rect)
            pygame.draw.rect(screen, DARK_GRAY, rect, 1)


def draw_ui():
    y_offset = 10
    for p in players + bots:
        score_text = font.render(f"{p.name}: {p.get_score()}", True, p.color)
        screen.blit(score_text, (10, y_offset))
        y_offset += 30
    minutes = game_time // 60000
    seconds = (game_time // 1000) % 60
    timer_text = font.render(f"Time: {minutes}:{seconds:02d}", True, BLACK)
    screen.blit(timer_text, (WIDTH - timer_text.get_width() - 10, 10))
    inst_text = font.render("Arrow keys | R to restart", True, DARK_GRAY)
    screen.blit(inst_text, (WIDTH // 2 - inst_text.get_width() // 2, HEIGHT - 30))


def show_winner():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    wc = winner.color if winner else WHITE
    wn = winner.name if winner else "Tie!"
    win_text = big_font.render(f"{wn} Wins!", True, wc)
    screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2 - 60))
    y_offset = HEIGHT // 2 + 10
    for e in sorted(players + bots, key=lambda x: x.get_score(), reverse=True):
        sl = font.render(f"{e.name}: {e.get_score()}", True, e.color)
        screen.blit(sl, (WIDTH // 2 - sl.get_width() // 2, y_offset))
        y_offset += 30


# === לולאה ראשית ===
reset_game()
running = True
while running:
    dt = clock.tick(FPS)
    game_time += dt
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            reset_game()

    if not game_over:
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]: dx -= 1
        if keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_UP]: dy -= 1
        if keys[pygame.K_DOWN]: dy += 1
        if dx or dy:
            players[0].move(dx, dy)
        for bot in bots:
            bot.update()
        painted = sum(1 for r in range(ROWS) for c in range(COLS) if painted_map[r][c] is not None)
        if painted >= COLS * ROWS * 0.8 or game_time > 180000:
            game_over = True
            all_e = sorted(players + bots, key=lambda e: e.get_score(), reverse=True)
            winner = all_e[0] if all_e[0].get_score() > all_e[1].get_score() else None

    screen.fill(WHITE)
    draw_grid()
    for bot in bots:
        bot.draw(screen)
    for player in players:
        player.draw(screen)
    draw_ui()
    if game_over:
        show_winner()
    pygame.display.flip()

pygame.quit()