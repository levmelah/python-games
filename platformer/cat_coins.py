import pygame
import sys
import math

pygame.init()

WIDTH, HEIGHT = 1000, 700
FPS = 60
GRAVITY = 0.5

WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
BLUE   = (50,  120, 220)
GREEN  = (34,  177,  76)
RED    = (220,  50,  50)
YELLOW = (255, 220,   0)
GRAY   = (150, 150, 150)
SKY    = (135, 206, 235)
CAT_FUR = (224, 186, 142)
CAT_STRIPE = (186, 145, 102)
CAT_BELLY = (244, 224, 196)
CAT_INNER_EAR = (250, 190, 198)
CAT_EYE = (120, 195, 95)
CAT_BLUSH = (255, 170, 178)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Platform Game")
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("Arial", 24, bold=True)
big_font = pygame.font.SysFont("Arial", 48, bold=True)
TOTAL_LEVELS = 3

# ── Platforms ────────────────────────────────────────────────────────────────
platforms = [
    pygame.Rect(0,   670, 1000, 30),   # ground
    pygame.Rect(50,  600, 180, 20),
    pygame.Rect(280, 550, 170, 20),
    pygame.Rect(520, 590, 190, 20),
    pygame.Rect(760, 520, 190, 20),
    pygame.Rect(560, 450, 170, 20),
    pygame.Rect(300, 400, 150, 20),
    pygame.Rect(90,  460, 140, 20),
    pygame.Rect(360, 310, 200, 20),
    pygame.Rect(650, 260, 200, 20),
    pygame.Rect(140, 240, 140, 20),
    pygame.Rect(860, 600, 110, 20),
    pygame.Rect(700, 430, 120, 20),
    pygame.Rect(470, 360, 110, 20),
    pygame.Rect(230, 520, 110, 20),
    pygame.Rect(40,  320, 90, 20),
    pygame.Rect(820, 330, 120, 20),
]

# ── Coins ─────────────────────────────────────────────────────────────────────
coin_positions = [
    (110, 570), (330, 520), (580, 560),
    (820, 490), (620, 420), (340, 370),
    (120, 430), (430, 280), (730, 230), (170, 210),
]
coins = [pygame.Rect(x, y, 16, 16) for x, y in coin_positions]

# ── Enemies ───────────────────────────────────────────────────────────────────
class Enemy:
    def __init__(self, x, y, left, right, speed=2):
        self.rect  = pygame.Rect(x, y, 36, 36)
        self.left  = left
        self.right = right
        self.speed = speed
        self.dir   = 1

    def update(self):
        self.rect.x += self.speed * self.dir
        if self.rect.right >= self.right or self.rect.left <= self.left:
            self.dir *= -1

    def draw(self, surface):
        tick = pygame.time.get_ticks()
        bob = int(math.sin((tick + self.rect.x * 8) * 0.01) * 2)
        r = self.rect.move(0, bob)

        # shadow
        shadow = pygame.Rect(r.x + 5, r.bottom - 5, r.w - 10, 8)
        pygame.draw.ellipse(surface, (20, 40, 30), shadow)

        # body
        pygame.draw.ellipse(surface, (129, 213, 139), r)
        pygame.draw.ellipse(surface, (71, 145, 88), r, 2)

        # belly
        belly = pygame.Rect(r.x + 8, r.y + 15, r.w - 16, r.h - 14)
        pygame.draw.ellipse(surface, (179, 235, 168), belly)

        # tiny horns
        left_horn = [(r.x + 8, r.y + 8), (r.x + 13, r.y + 1), (r.x + 16, r.y + 9)]
        right_horn = [(r.right - 16, r.y + 9), (r.right - 13, r.y + 1), (r.right - 8, r.y + 8)]
        pygame.draw.polygon(surface, (255, 230, 170), left_horn)
        pygame.draw.polygon(surface, (255, 230, 170), right_horn)

        # eyes + blink
        blink = (tick // 240) % 16 == 0
        eye_y = r.y + 14
        if blink:
            pygame.draw.line(surface, (35, 56, 42), (r.x + 11, eye_y), (r.x + 16, eye_y), 2)
            pygame.draw.line(surface, (35, 56, 42), (r.right - 16, eye_y), (r.right - 11, eye_y), 2)
        else:
            pygame.draw.ellipse(surface, WHITE, (r.x + 10, eye_y - 2, 7, 8))
            pygame.draw.ellipse(surface, WHITE, (r.right - 17, eye_y - 2, 7, 8))
            pygame.draw.circle(surface, (28, 43, 31), (r.x + 13 + self.dir, eye_y + 2), 2)
            pygame.draw.circle(surface, (28, 43, 31), (r.right - 14 + self.dir, eye_y + 2), 2)
            pygame.draw.circle(surface, WHITE, (r.x + 12, eye_y + 1), 1)
            pygame.draw.circle(surface, WHITE, (r.right - 15, eye_y + 1), 1)

        # blush + smile
        pygame.draw.circle(surface, (246, 178, 188), (r.x + 10, r.y + 23), 3)
        pygame.draw.circle(surface, (246, 178, 188), (r.right - 10, r.y + 23), 3)
        pygame.draw.arc(surface, (35, 56, 42), (r.centerx - 5, r.y + 20, 10, 8), 0.2, 2.9, 2)

enemies = [
    Enemy(70, 564, 50, 230, 2),
    Enemy(535, 554, 520, 710, 2),
    Enemy(665, 224, 650, 850, 3),
]
BASE_ENEMY_SPEEDS = [1.4, 1.4, 2.0]

# ── Portals ──────────────────────────────────────────────────────────────────
PORTAL_W, PORTAL_H = 28, 44
portal_a = pygame.Rect(140, 670 - PORTAL_H, PORTAL_W, PORTAL_H)  # ground portal
portal_b = pygame.Rect(190, 240 - PORTAL_H, PORTAL_W, PORTAL_H)  # high platform portal

# ── Player ────────────────────────────────────────────────────────────────────
class Player:
    W, H = 44, 58

    def __init__(self):
        self.reset()

    def reset(self):
        self.rect    = pygame.Rect(50, 600, self.W, self.H)
        self.vx      = 0
        self.vy      = 0
        self.on_ground = False
        self.lives   = 10
        self.score   = 0
        self.inv_timer = 0   # invincibility frames after hit
        self.portal_cooldown = 0

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vx = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.vx = -5
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.vx =  5
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vy = -13
            self.on_ground = False

    def update(self, platforms_list):
        self.vy += GRAVITY
        self.rect.x += self.vx

        # horizontal collision
        for p in platforms_list:
            if self.rect.colliderect(p):
                if self.vx > 0: self.rect.right = p.left
                elif self.vx < 0: self.rect.left = p.right

        self.rect.y += self.vy
        self.on_ground = False

        for p in platforms_list:
            if self.rect.colliderect(p):
                if self.vy > 0:
                    self.rect.bottom = p.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = p.bottom
                    self.vy = 0

        # screen boundaries
        if self.rect.left < 0:  self.rect.left = 0
        if self.rect.right > WIDTH: self.rect.right = WIDTH

        if self.inv_timer > 0:
            self.inv_timer -= 1
        if self.portal_cooldown > 0:
            self.portal_cooldown -= 1

    def draw(self, surface):
        # flicker when invincible
        if self.inv_timer > 0 and (self.inv_timer // 4) % 2 == 0:
            return
        # Round kitten body + belly patch
        pygame.draw.ellipse(surface, CAT_FUR, self.rect)
        pygame.draw.ellipse(surface, CAT_BELLY, (self.rect.x + 8, self.rect.y + 14, 20, 18))
        pygame.draw.arc(surface, CAT_STRIPE, (self.rect.x + 10, self.rect.y + 18, 16, 10), 0.2, 2.9, 2)

        # Tail with soft curl
        tail_x = self.rect.right - 2 if self.vx >= 0 else self.rect.left - 16
        tail_dir = 1 if self.vx >= 0 else -1
        tail_points = [
            (tail_x, self.rect.y + 16),
            (tail_x + 13 * tail_dir, self.rect.y + 10),
            (tail_x + 18 * tail_dir, self.rect.y + 18),
            (tail_x + 10 * tail_dir, self.rect.y + 24),
            (tail_x + 2 * tail_dir, self.rect.y + 21),
        ]
        pygame.draw.polygon(surface, CAT_FUR, tail_points)

        # Head
        head = pygame.Rect(self.rect.x + 4, self.rect.y - 22, self.W - 8, 24)
        pygame.draw.ellipse(surface, CAT_FUR, head)

        # Ears
        left_ear = [(head.x + 2, head.y + 6), (head.x + 9, head.y - 7), (head.x + 15, head.y + 6)]
        right_ear = [(head.right - 15, head.y + 6), (head.right - 9, head.y - 7), (head.right - 2, head.y + 6)]
        pygame.draw.polygon(surface, CAT_FUR, left_ear)
        pygame.draw.polygon(surface, CAT_FUR, right_ear)
        pygame.draw.polygon(surface, CAT_INNER_EAR, [(head.x + 6, head.y + 5), (head.x + 9, head.y), (head.x + 12, head.y + 5)])
        pygame.draw.polygon(surface, CAT_INNER_EAR, [(head.right - 12, head.y + 5), (head.right - 9, head.y), (head.right - 6, head.y + 5)])

        # Big eyes + highlights
        left_eye = pygame.Rect(head.x + 5, head.y + 9, 8, 7)
        right_eye = pygame.Rect(head.right - 13, head.y + 9, 8, 7)
        pygame.draw.ellipse(surface, CAT_EYE, left_eye)
        pygame.draw.ellipse(surface, CAT_EYE, right_eye)
        pygame.draw.circle(surface, BLACK, left_eye.center, 2)
        pygame.draw.circle(surface, BLACK, right_eye.center, 2)
        pygame.draw.circle(surface, WHITE, (left_eye.x + 2, left_eye.y + 2), 1)
        pygame.draw.circle(surface, WHITE, (right_eye.x + 2, right_eye.y + 2), 1)

        # Blush cheeks
        pygame.draw.circle(surface, CAT_BLUSH, (head.x + 6, head.y + 17), 3)
        pygame.draw.circle(surface, CAT_BLUSH, (head.right - 6, head.y + 17), 3)

        # Nose, mouth, whiskers
        pygame.draw.polygon(surface, (255, 150, 160), [(head.centerx, head.y + 15), (head.centerx - 3, head.y + 18), (head.centerx + 3, head.y + 18)])
        pygame.draw.arc(surface, BLACK, (head.centerx - 5, head.y + 17, 5, 4), 0.2, 2.8, 1)
        pygame.draw.arc(surface, BLACK, (head.centerx, head.y + 17, 5, 4), 0.3, 3.0, 1)
        pygame.draw.line(surface, BLACK, (head.centerx - 5, head.y + 17), (head.centerx - 14, head.y + 16), 1)
        pygame.draw.line(surface, BLACK, (head.centerx + 5, head.y + 17), (head.centerx + 14, head.y + 16), 1)

        # Small paws
        paw_y = self.rect.bottom - 5
        pygame.draw.ellipse(surface, CAT_BELLY, (self.rect.x + 6, paw_y - 3, 9, 6))
        pygame.draw.ellipse(surface, CAT_BELLY, (self.rect.right - 15, paw_y - 3, 9, 6))

player = Player()

def draw_background():
    # Sunset sky gradient
    for y in range(HEIGHT):
        t = y / HEIGHT
        if t < 0.45:
            k = t / 0.45
            r = int(255 - 25 * k)
            g = int(120 - 55 * k)
            b = int(70 + 80 * k)
        else:
            k = (t - 0.45) / 0.55
            r = int(230 - 140 * k)
            g = int(95 + 60 * k)
            b = int(150 + 70 * k)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    # Sun glow
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 190, 115, 120), (WIDTH // 2 - 40, 130), 140)
    pygame.draw.circle(glow, (255, 125, 170, 90), (WIDTH // 2, 145), 190)
    screen.blit(glow, (0, 0))

    # Distant mountains
    pygame.draw.polygon(screen, (80, 72, 125), [(0, 320), (120, 230), (300, 320), (430, 210), (610, 320), (830, 190), (WIDTH, 280), (WIDTH, 420), (0, 420)])
    pygame.draw.polygon(screen, (55, 60, 100), [(0, 390), (180, 300), (350, 390), (530, 290), (700, 390), (890, 280), (WIDTH, 340), (WIDTH, 500), (0, 500)])

    # Water body
    water_top = 380
    for y in range(water_top, HEIGHT):
        k = (y - water_top) / (HEIGHT - water_top)
        r = int(60 - 30 * k)
        g = int(130 - 40 * k)
        b = int(170 - 30 * k)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    # Reflection path
    refl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(refl, (255, 190, 140, 95), (WIDTH // 2 - 140, 395, 280, 260))
    pygame.draw.ellipse(refl, (255, 130, 190, 70), (WIDTH // 2 - 180, 420, 360, 240))
    screen.blit(refl, (0, 0))

    # Shores and foreground rocks
    pygame.draw.polygon(screen, (42, 55, 64), [(0, HEIGHT), (0, 500), (140, 450), (250, 470), (320, 550), (400, HEIGHT)])
    pygame.draw.polygon(screen, (40, 52, 60), [(WIDTH, HEIGHT), (WIDTH, 500), (860, 450), (770, 480), (700, 550), (620, HEIGHT)])

    # Trees silhouettes and flowers for detail
    pygame.draw.rect(screen, (45, 30, 30), (90, 340, 18, 170))
    pygame.draw.circle(screen, (108, 40, 58), (100, 335), 52)
    pygame.draw.circle(screen, (124, 52, 70), (140, 323), 40)
    pygame.draw.circle(screen, (108, 40, 58), (62, 320), 35)
    pygame.draw.circle(screen, (195, 70, 140), (WIDTH - 85, 610), 8)
    pygame.draw.circle(screen, (155, 65, 210), (WIDTH - 62, 618), 6)
    pygame.draw.circle(screen, (220, 90, 160), (WIDTH - 105, 626), 7)

def draw_platforms():
    for p in platforms:
        # Stone platform base
        pygame.draw.rect(screen, (90, 97, 82), p, border_radius=6)
        pygame.draw.rect(screen, (58, 64, 54), p, 2, border_radius=6)
        # Moss strip on top
        moss = pygame.Rect(p.x, p.y, p.w, max(5, p.h // 3))
        pygame.draw.rect(screen, (74, 136, 66), moss, border_radius=5)

def draw_coins(coin_list):
    for c in coin_list:
        pygame.draw.ellipse(screen, YELLOW, c)
        pygame.draw.ellipse(screen, (200, 160, 0), c, 2)

def draw_portals():
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.006)
    for portal, core_color in [
        (portal_a, (125, 235, 255)),
        (portal_b, (255, 170, 210)),
    ]:
        cx, cy = portal.centerx, portal.centery
        radius = 36

        # Outer glow
        glow = pygame.Surface((150, 150), pygame.SRCALPHA)
        glow_color = (*core_color, int(65 + 35 * pulse))
        pygame.draw.circle(glow, glow_color, (75, 75), radius + 20)
        screen.blit(glow, (cx - 75, cy - 75))

        # Stone ring
        pygame.draw.circle(screen, (98, 87, 74), (cx, cy), radius + 11)
        pygame.draw.circle(screen, (60, 52, 44), (cx, cy), radius + 11, 4)

        # Portal core
        pygame.draw.circle(screen, (34, 62, 82), (cx, cy), radius - 1)
        pygame.draw.circle(screen, core_color, (cx, cy), radius - 1, 3)

        # Inner magical gradient circles
        pygame.draw.circle(screen, (90, 150, 170), (cx, cy + 4), radius - 10)
        pygame.draw.circle(screen, (255, 180, 120), (cx, cy + 11), radius - 18)

        # Tiny floating islands silhouette inside portal
        pygame.draw.ellipse(screen, (42, 52, 54), (cx - 12, cy - 5, 24, 8))
        pygame.draw.ellipse(screen, (42, 52, 54), (cx + 13, cy - 15, 18, 6))

        # Rune dots around ring
        for i in range(8):
            a = i * (math.pi / 4) + pygame.time.get_ticks() * 0.001
            rx = int(cx + (radius + 7) * math.cos(a))
            ry = int(cy + (radius + 7) * math.sin(a))
            pygame.draw.circle(screen, (180, 220, 235), (rx, ry), 2)

def draw_hud(level):
    score_surf = font.render(f"Score: {player.score}", True, BLACK)
    lives_surf = font.render(f"Lives: {player.lives}", True, BLACK)
    level_surf = font.render(f"Level: {level}/{TOTAL_LEVELS}", True, BLACK)
    screen.blit(score_surf, (10, 10))
    screen.blit(lives_surf, (10, 38))
    screen.blit(level_surf, (10, 66))

def show_level_screen(level, completed=False):
    while True:
        draw_background()
        draw_platforms()
        draw_portals()

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        screen.blit(overlay, (0, 0))

        if completed:
            title_text = f"LEVEL {level} COMPLETE!"
            hint_text = "Press ENTER for next level"
            title_color = (255, 235, 150)
        else:
            title_text = f"LEVEL {level}"
            hint_text = "Press ENTER to start"
            title_color = (210, 240, 255)

        title = big_font.render(title_text, True, title_color)
        hint = font.render(hint_text, True, WHITE)

        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 70))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 10))

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

def show_start_screen():
    while True:
        draw_background()
        draw_platforms()
        draw_portals()

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        title = big_font.render("MAGIC CAT ADVENTURE", True, (255, 240, 170))
        hint = font.render("Press ENTER to Start", True, WHITE)
        controls = font.render("Move: LEFT/RIGHT or A/D | Jump: SPACE/UP/W | ESC: Quit", True, (220, 220, 220))

        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 90))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 - 20))
        screen.blit(controls, (WIDTH // 2 - controls.get_width() // 2, HEIGHT // 2 + 20))

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

def show_message(title, sub=""):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))
    t = big_font.render(title, True, YELLOW)
    screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 60))
    if sub:
        s = font.render(sub, True, WHITE)
        screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2 + 10))
    pygame.display.flip()
    wait_for_key()

def show_end_screen(title, score):
    while True:
        draw_background()
        draw_platforms()
        draw_portals()

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        screen.blit(overlay, (0, 0))

        title_surf = big_font.render(title, True, YELLOW)
        score_surf = font.render(f"Score: {score}", True, WHITE)
        restart_surf = font.render("Press R to Restart", True, (180, 255, 180))
        quit_surf = font.render("Press Q or ESC to Quit", True, (255, 180, 180))

        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 80))
        screen.blit(score_surf, (WIDTH // 2 - score_surf.get_width() // 2, HEIGHT // 2 - 20))
        screen.blit(restart_surf, (WIDTH // 2 - restart_surf.get_width() // 2, HEIGHT // 2 + 20))
        screen.blit(quit_surf, (WIDTH // 2 - quit_surf.get_width() // 2, HEIGHT // 2 + 55))

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    return False

def set_level_difficulty(level):
    speed_bonus = 0.2 * (level - 1)
    for enemy, base_speed in zip(enemies, BASE_ENEMY_SPEEDS):
        enemy.speed = base_speed + speed_bonus

def prepare_level_start(level):
    set_level_difficulty(level)
    player.rect.topleft = (50, 600)
    player.vx = 0
    player.vy = 0
    player.on_ground = False
    player.inv_timer = 0
    player.portal_cooldown = 0

def wait_for_key():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                return

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    global coins

    show_start_screen()

    current_level = 1
    game_coins = list(coins)
    prepare_level_start(current_level)
    show_level_screen(current_level, completed=False)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        player.handle_input()
        player.update(platforms)

        for enemy in enemies:
            enemy.update()

        # portal teleport
        if player.portal_cooldown == 0:
            if player.rect.colliderect(portal_a):
                player.rect.midbottom = (portal_b.centerx, portal_b.top)
                player.vy = 0
                player.portal_cooldown = 24
            elif player.rect.colliderect(portal_b):
                player.rect.midbottom = (portal_a.centerx, portal_a.top)
                player.vy = 0
                player.portal_cooldown = 24

        # collect coins
        for c in game_coins[:]:
            if player.rect.colliderect(c):
                game_coins.remove(c)
                player.score += 10

        # enemy collision
        if player.inv_timer == 0:
            for enemy in enemies:
                if player.rect.colliderect(enemy.rect):
                    player.lives -= 1
                    player.inv_timer = 90
                    if player.lives <= 0:
                        if show_end_screen("GAME OVER", player.score):
                            player.reset()
                            current_level = 1
                            game_coins = list(coins)
                            prepare_level_start(current_level)
                            show_level_screen(current_level, completed=False)
                        else:
                            pygame.quit(); sys.exit()
                    else:
                        player.rect.topleft = (50, 600)
                        player.vx = player.vy = 0
                    break

        # fall off screen
        if player.rect.top > HEIGHT:
            player.lives -= 1
            player.inv_timer = 60
            if player.lives <= 0:
                if show_end_screen("GAME OVER", player.score):
                    player.reset()
                    current_level = 1
                    game_coins = list(coins)
                    prepare_level_start(current_level)
                    show_level_screen(current_level, completed=False)
                else:
                    pygame.quit(); sys.exit()
            else:
                player.rect.topleft = (50, 600)
                player.vx = player.vy = 0

        # win
        if len(game_coins) == 0:
            if current_level < TOTAL_LEVELS:
                show_level_screen(current_level, completed=True)
                current_level += 1
                game_coins = list(coins)
                prepare_level_start(current_level)
                show_level_screen(current_level, completed=False)
            else:
                if show_end_screen("YOU WIN!", player.score):
                    player.reset()
                    current_level = 1
                    game_coins = list(coins)
                    prepare_level_start(current_level)
                    show_level_screen(current_level, completed=False)
                else:
                    pygame.quit(); sys.exit()

        # ── Draw ──────────────────────────────────────────────────────────────
        draw_background()
        draw_platforms()
        draw_portals()
        draw_coins(game_coins)
        for enemy in enemies:
            enemy.draw(screen)
        player.draw(screen)
        draw_hud(current_level)

        pygame.display.flip()

main()
