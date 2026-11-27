import pygame
import math
import random
import sys

pygame.init()

WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🌸 גן של בנבן 🌸")
clock = pygame.time.Clock()

# ── Colors ──────────────────────────────────────────────────────────────────
WHITE   = (255, 255, 255)
BLACK   = (0, 0, 0)
GRAY    = (180, 180, 180)
DARK    = (30, 30, 40)
RED     = (220, 60, 60)
GREEN   = (80, 200, 80)
BLUE    = (60, 120, 220)
YELLOW  = (240, 220, 60)
ORANGE  = (230, 130, 40)
PINK    = (240, 100, 180)
PURPLE  = (160, 80, 220)
CYAN    = (60, 210, 210)
LIGHT_BLUE = (130, 190, 255)
WALL_COLOR  = (70, 50, 90)
FLOOR_COLOR = (210, 195, 230)
DOOR_COLOR  = (160, 110, 60)
KEY_COLOR   = (255, 215, 0)
BG_COLOR    = (20, 15, 30)

# ── Fonts ────────────────────────────────────────────────────────────────────
try:
    font_big   = pygame.font.SysFont("arial", 42, bold=True)
    font_med   = pygame.font.SysFont("arial", 26, bold=True)
    font_small = pygame.font.SysFont("arial", 18)
    font_heb   = pygame.font.SysFont("arial", 22, bold=True)
except:
    font_big   = pygame.font.Font(None, 48)
    font_med   = pygame.font.Font(None, 32)
    font_small = pygame.font.Font(None, 22)
    font_heb   = pygame.font.Font(None, 28)

# ── Map Layout ───────────────────────────────────────────────────────────────
# 0=floor  1=wall  2=door(locked)  3=door(open)  4=key  5=note  6=exit
TILE = 40
COLS = WIDTH  // TILE
ROWS = HEIGHT // TILE

MAP = [
    "111111111111111111111111",
    "1...........1.........11",
    "1...........1.........11",
    "1...........2.........11",
    "1...........1.........11",
    "1...1111....1....1111.11",
    "1...1K.1....1....1..1.11",
    "1...1.......1....1..1..11",
    "1...1111....1....11111 1",
    "1..........111.........1",
    "1...N......111......N..1",
    "1..........111.........1",
    "1111111....111....1111111",
    "1.....1..........1.....1",
    "1.....2..........2.....1",
    "1.....1..........1.....1",
    "111111111111111111111111",
]

# Trim / pad map to screen
while len(MAP) < ROWS:
    MAP.append("1" * COLS)
MAP = [row.ljust(COLS, "1")[:COLS] for row in MAP]

def tile_rect(col, row):
    return pygame.Rect(col * TILE, row * TILE, TILE, TILE)

def is_wall(col, row, game_map):
    if col < 0 or row < 0 or col >= COLS or row >= len(game_map):
        return True
    return game_map[row][col] == "1"

def is_blocked(col, row, game_map):
    if col < 0 or row < 0 or col >= COLS or row >= len(game_map):
        return True
    return game_map[row][col] in ("1", "2")

# ── Draw helpers ─────────────────────────────────────────────────────────────
def draw_banban(surf, x, y, size=28, anim=0):
    """Draw Banban – blue bird mascot."""
    # body
    pygame.draw.ellipse(surf, (60, 130, 230), (x - size//2, y - size//2, size, size))
    # beak
    beak = [(x + size//2, y), (x + size//2 + 8, y - 4), (x + size//2 + 8, y + 4)]
    pygame.draw.polygon(surf, YELLOW, beak)
    # eyes
    eye_y = y - size//6
    pygame.draw.circle(surf, WHITE, (x - 5, eye_y), 5)
    pygame.draw.circle(surf, WHITE, (x + 5, eye_y), 5)
    pygame.draw.circle(surf, BLACK, (x - 4, eye_y), 2)
    pygame.draw.circle(surf, BLACK, (x + 6, eye_y), 2)
    # wings
    wing_off = int(math.sin(anim * 0.15) * 4)
    pygame.draw.ellipse(surf, (40, 100, 200),
                        (x - size - 4, y - size//4 + wing_off, size//2, size//3))
    pygame.draw.ellipse(surf, (40, 100, 200),
                        (x + size//2 + 2, y - size//4 - wing_off, size//2, size//3))

def draw_opila(surf, x, y, size=34, anim=0):
    """Draw Opila Bird – big yellow menacing bird."""
    # body
    pygame.draw.ellipse(surf, (230, 200, 50), (x - size//2, y - size//2, size, size))
    # head tuft
    pygame.draw.circle(surf, (230, 200, 50), (x, y - size//2 - 6), 10)
    # beak (large)
    beak = [(x - 6, y - 4), (x + 6, y - 4), (x, y + 8)]
    pygame.draw.polygon(surf, ORANGE, beak)
    # scary eyes
    eye_y = y - size//4
    pygame.draw.circle(surf, RED,   (x - 7, eye_y), 7)
    pygame.draw.circle(surf, RED,   (x + 7, eye_y), 7)
    pygame.draw.circle(surf, BLACK, (x - 7, eye_y), 3)
    pygame.draw.circle(surf, BLACK, (x + 7, eye_y), 3)
    # legs wobble
    leg_off = int(math.sin(anim * 0.2) * 3)
    pygame.draw.line(surf, ORANGE, (x - 6, y + size//2),
                     (x - 6 + leg_off, y + size//2 + 10), 3)
    pygame.draw.line(surf, ORANGE, (x + 6, y + size//2),
                     (x + 6 - leg_off, y + size//2 + 10), 3)

def draw_banbaleena(surf, x, y, size=26, anim=0):
    """Draw Banbaleena – pink dancing mascot."""
    # dress / body
    pygame.draw.ellipse(surf, PINK, (x - size//2, y - size//3, size, size))
    # head
    pygame.draw.circle(surf, (255, 170, 200), (x, y - size//2), size//2)
    # bow
    bow = [(x - 10, y - size), (x, y - size + 6), (x + 10, y - size)]
    pygame.draw.polygon(surf, RED, bow)
    # eyes
    eye_y = y - size//2 - 2
    pygame.draw.circle(surf, BLACK, (x - 5, eye_y), 3)
    pygame.draw.circle(surf, BLACK, (x + 5, eye_y), 3)
    # smile
    pygame.draw.arc(surf, BLACK, (x - 6, eye_y + 6, 12, 8), math.pi, 2 * math.pi, 2)
    # arms sway
    arm_off = int(math.sin(anim * 0.12) * 6)
    pygame.draw.line(surf, PINK, (x - size//2, y - size//4),
                     (x - size//2 - 8, y - size//4 + arm_off), 3)
    pygame.draw.line(surf, PINK, (x + size//2, y - size//4),
                     (x + size//2 + 8, y - size//4 - arm_off), 3)

def draw_player(surf, x, y, direction=0, anim=0):
    """Draw the player character."""
    # body
    pygame.draw.ellipse(surf, (200, 160, 120), (x - 10, y - 8, 20, 16))
    # head
    pygame.draw.circle(surf, (230, 190, 140), (x, y - 14), 10)
    # eyes
    ex = x + int(math.cos(direction) * 4)
    ey = y - 14 + int(math.sin(direction) * 4)
    pygame.draw.circle(surf, BLACK, (ex, ey), 2)
    # flashlight beam
    angle = direction
    beam_len = 90
    bx = x + int(math.cos(angle) * beam_len)
    by = y + int(math.sin(angle) * beam_len)
    beam_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(beam_surf, (255, 255, 200, 45), [
        (x, y),
        (x + int(math.cos(angle - 0.4) * beam_len), y + int(math.sin(angle - 0.4) * beam_len)),
        (x + int(math.cos(angle + 0.4) * beam_len), y + int(math.sin(angle + 0.4) * beam_len)),
    ])
    surf.blit(beam_surf, (0, 0))
    # legs
    leg_off = int(math.sin(anim * 0.2) * 4)
    pygame.draw.line(surf, (140, 100, 80), (x - 4, y + 8), (x - 4, y + 16 + leg_off), 3)
    pygame.draw.line(surf, (140, 100, 80), (x + 4, y + 8), (x + 4, y + 16 - leg_off), 3)

def draw_drone(surf, x, y, anim=0):
    hover = int(math.sin(anim * 0.1) * 3)
    pygame.draw.rect(surf, CYAN, (x - 10, y - 5 + hover, 20, 10), border_radius=4)
    pygame.draw.line(surf, GRAY, (x - 10, y + hover), (x - 18, y - 6 + hover), 2)
    pygame.draw.line(surf, GRAY, (x + 10, y + hover), (x + 18, y - 6 + hover), 2)
    pygame.draw.circle(surf, CYAN, (x - 18, y - 8 + hover), 4)
    pygame.draw.circle(surf, CYAN, (x + 18, y - 8 + hover), 4)
    # light
    pygame.draw.circle(surf, YELLOW, (x, y + 5 + hover), 3)

def draw_key(surf, x, y, anim=0):
    bob = int(math.sin(anim * 0.08) * 3)
    pygame.draw.circle(surf, KEY_COLOR, (x, y + bob), 8, 3)
    pygame.draw.rect(surf, KEY_COLOR, (x + 6, y + bob - 2, 12, 4))
    pygame.draw.rect(surf, KEY_COLOR, (x + 14, y + bob - 5, 3, 4))
    pygame.draw.rect(surf, KEY_COLOR, (x + 18, y + bob - 5, 3, 4))

def draw_note(surf, x, y):
    pygame.draw.rect(surf, (255, 240, 180), (x - 8, y - 10, 16, 20), border_radius=2)
    for i in range(3):
        pygame.draw.line(surf, GRAY, (x - 5, y - 5 + i * 5), (x + 5, y - 5 + i * 5), 1)

def draw_exit(surf, x, y, anim=0):
    glow = abs(int(math.sin(anim * 0.05) * 30))
    pygame.draw.rect(surf, (0, 200 + glow, 0), (x - 15, y - 20, 30, 40), border_radius=4)
    txt = font_small.render("EXIT", True, WHITE)
    surf.blit(txt, (x - txt.get_width() // 2, y - txt.get_height() // 2))

# ── Game classes ──────────────────────────────────────────────────────────────
class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.speed = 3.0
        self.direction = 0.0
        self.anim = 0
        self.health = 3
        self.has_key = False
        self.notes_found = 0
        self.invincible = 0   # frames of invincibility after hit

    def move(self, dx, dy, game_map):
        if dx != 0 or dy != 0:
            self.direction = math.atan2(dy, dx)
            self.anim += 1
        nx, ny = self.x + dx * self.speed, self.y + dy * self.speed
        col_nx = int(nx // TILE)
        row_ny = int(ny // TILE)
        col_x  = int(self.x // TILE)
        row_y  = int(self.y // TILE)
        if not is_blocked(col_nx, row_y, game_map):
            self.x = nx
        if not is_blocked(col_x, row_ny, game_map):
            self.y = ny

    def rect(self):
        return pygame.Rect(int(self.x) - 10, int(self.y) - 14, 20, 28)

    def draw(self, surf):
        draw_player(surf, int(self.x), int(self.y), self.direction, self.anim)
        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            pygame.draw.circle(surf, RED, (int(self.x), int(self.y)), 18, 2)

    def hit(self):
        if self.invincible == 0:
            self.health -= 1
            self.invincible = 90
            return True
        return False

    def update(self):
        if self.invincible > 0:
            self.invincible -= 1


class Monster:
    def __init__(self, x, y, kind="banban", speed=1.2):
        self.x = float(x)
        self.y = float(y)
        self.kind = kind
        self.speed = speed
        self.anim = random.randint(0, 100)
        self.state = "patrol"     # patrol / chase / stunned
        self.patrol_dir = random.uniform(0, 2 * math.pi)
        self.patrol_timer = random.randint(40, 120)
        self.stun_timer = 0
        self.sight = 160 if kind == "opila" else 120

    def rect(self):
        return pygame.Rect(int(self.x) - 16, int(self.y) - 16, 32, 32)

    def draw(self, surf):
        ix, iy = int(self.x), int(self.y)
        if self.kind == "banban":
            draw_banban(surf, ix, iy, anim=self.anim)
        elif self.kind == "opila":
            draw_opila(surf, ix, iy, anim=self.anim)
        elif self.kind == "banbaleena":
            draw_banbaleena(surf, ix, iy, anim=self.anim)
        # stun stars
        if self.stun_timer > 0:
            for i in range(3):
                ang = self.anim * 0.1 + i * 2.1
                sx = ix + int(math.cos(ang) * 22)
                sy = iy - 20 + int(math.sin(ang) * 8)
                pygame.draw.circle(surf, YELLOW, (sx, sy), 4)

    def update(self, player, game_map):
        self.anim += 1
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return

        dist = math.hypot(self.x - player.x, self.y - player.y)

        if dist < self.sight:
            self.state = "chase"
        elif self.state == "chase" and dist > self.sight * 1.5:
            self.state = "patrol"

        if self.state == "chase":
            angle = math.atan2(player.y - self.y, player.x - self.x)
            dx = math.cos(angle)
            dy = math.sin(angle)
        else:
            self.patrol_timer -= 1
            if self.patrol_timer <= 0:
                self.patrol_dir = random.uniform(0, 2 * math.pi)
                self.patrol_timer = random.randint(40, 120)
            dx = math.cos(self.patrol_dir)
            dy = math.sin(self.patrol_dir)

        nx = self.x + dx * self.speed
        ny = self.y + dy * self.speed
        col_nx = int(nx // TILE)
        row_y  = int(self.y // TILE)
        col_x  = int(self.x // TILE)
        row_ny = int(ny // TILE)

        if not is_blocked(col_nx, row_y, game_map):
            self.x = nx
        else:
            self.patrol_dir = random.uniform(0, 2 * math.pi)
        if not is_blocked(col_x, row_ny, game_map):
            self.y = ny
        else:
            self.patrol_dir = random.uniform(0, 2 * math.pi)

    def stun(self):
        self.stun_timer = 120
        self.state = "patrol"


class Drone:
    def __init__(self, player):
        self.x = float(player.x)
        self.y = float(player.y)
        self.active = False
        self.anim = 0

    def update(self, keys, game_map):
        if not self.active:
            return
        self.anim += 1
        speed = 4.0
        dx = dy = 0
        if keys[pygame.K_i]: dy = -1
        if keys[pygame.K_k]: dy =  1
        if keys[pygame.K_j]: dx = -1
        if keys[pygame.K_l]: dx =  1
        if dx != 0 and dy != 0:
            dx *= 0.707; dy *= 0.707
        nx = self.x + dx * speed
        ny = self.y + dy * speed
        col_nx = int(nx // TILE)
        row_y  = int(self.y // TILE)
        col_x  = int(self.x // TILE)
        row_ny = int(ny // TILE)
        if not is_wall(col_nx, row_y, game_map):
            self.x = nx
        if not is_wall(col_x, row_ny, game_map):
            self.y = ny

    def draw(self, surf):
        if self.active:
            draw_drone(surf, int(self.x), int(self.y), self.anim)


# ── Game state ────────────────────────────────────────────────────────────────
def build_game():
    game_map = [list(row) for row in MAP]

    player = Player(2 * TILE + TILE // 2, 2 * TILE + TILE // 2)

    # Parse special tiles
    keys_pos = []
    notes_pos = []
    exit_pos = None
    for r, row in enumerate(game_map):
        for c, ch in enumerate(row):
            cx = c * TILE + TILE // 2
            cy = r * TILE + TILE // 2
            if ch == "K":
                keys_pos.append([cx, cy, True])   # True = visible
                game_map[r][c] = "."
            elif ch == "N":
                notes_pos.append([cx, cy, True])
                game_map[r][c] = "."
            elif ch == "6":
                exit_pos = (cx, cy)
                game_map[r][c] = "."
            elif ch == " ":
                game_map[r][c] = "."   # open area

    # If no exit parsed, place one
    if exit_pos is None:
        exit_pos = (20 * TILE + TILE // 2, 14 * TILE + TILE // 2)

    monsters = [
        Monster(8 * TILE + TILE // 2,  5 * TILE + TILE // 2, "banban",    1.3),
        Monster(18 * TILE + TILE // 2, 3 * TILE + TILE // 2, "opila",     1.0),
        Monster(11 * TILE + TILE // 2, 13 * TILE + TILE // 2, "banbaleena", 1.5),
    ]

    drone = Drone(player)
    return game_map, player, keys_pos, notes_pos, exit_pos, monsters, drone


NOTE_TEXTS = [
    "יומן: ילדי אבד בגן.\nחייב למצוא אותו...",
    "אזהרה: אל תיגע בפסלים!\nהם חיים בלילה.",
]

def main():
    game_map, player, keys_pos, notes_pos, exit_pos, monsters, drone = build_game()

    state = "play"      # play / win / lose / note
    anim_tick = 0
    show_note_text = ""
    note_timer = 0
    score = 0

    # Generate random extra keys if map had none
    if not keys_pos:
        keys_pos.append([5 * TILE + TILE // 2, 7 * TILE + TILE // 2, True])

    # ── Camera offset (player centred) ────────────────────────────────────────
    cam_x = cam_y = 0

    def get_cam():
        cx = int(player.x) - WIDTH // 2
        cy = int(player.y) - HEIGHT // 2
        return cx, cy

    def world_to_screen(wx, wy, cx, cy):
        return wx - cx, wy - cy

    running = True
    while running:
        dt = clock.tick(60)
        anim_tick += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if state == "note":
                    state = "play"
                    note_timer = 0
                if state in ("win", "lose") and event.key == pygame.K_r:
                    game_map, player, keys_pos, notes_pos, exit_pos, monsters, drone = build_game()
                    state = "play"
                    score = 0
                if state == "play":
                    if event.key == pygame.K_TAB:
                        drone.active = not drone.active
                        if drone.active:
                            drone.x, drone.y = player.x, player.y

        # ── Update ────────────────────────────────────────────────────────────
        if state == "play":
            keys = pygame.key.get_pressed()

            # Player movement
            dx = dy = 0
            if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx =  1
            if keys[pygame.K_UP]    or keys[pygame.K_w]: dy = -1
            if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy =  1
            if dx and dy:
                dx *= 0.707; dy *= 0.707
            player.move(dx, dy, game_map)
            player.update()

            # Drone
            drone.update(keys, game_map)

            # Monsters
            for m in monsters:
                m.update(player, game_map)
                if m.stun_timer == 0 and m.rect().colliderect(player.rect()):
                    if player.hit():
                        if player.health <= 0:
                            state = "lose"

            # Pick up key
            for k in keys_pos:
                if k[2]:
                    dx2 = k[0] - player.x
                    dy2 = k[1] - player.y
                    if math.hypot(dx2, dy2) < 20:
                        k[2] = False
                        player.has_key = True
                        score += 50

            # Unlock door
            pr = int(player.y // TILE)
            pc = int(player.x // TILE)
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = pr + dr, pc + dc
                if 0 <= nr < len(game_map) and 0 <= nc < len(game_map[0]):
                    if game_map[nr][nc] == "2" and player.has_key:
                        game_map[nr][nc] = "3"
                        player.has_key = False
                        score += 100

            # Read notes
            for n in notes_pos:
                if n[2]:
                    if math.hypot(n[0] - player.x, n[1] - player.y) < 22:
                        n[2] = False
                        player.notes_found += 1
                        idx = (player.notes_found - 1) % len(NOTE_TEXTS)
                        show_note_text = NOTE_TEXTS[idx]
                        state = "note"
                        score += 30

            # Reach exit
            ex, ey = exit_pos
            if math.hypot(player.x - ex, player.y - ey) < 28:
                state = "win"
                score += 500

            # Drone stun monsters
            if drone.active:
                for m in monsters:
                    if math.hypot(m.x - drone.x, m.y - drone.y) < 35:
                        m.stun()

        # ── Draw ──────────────────────────────────────────────────────────────
        cam_x, cam_y = get_cam()

        screen.fill(BG_COLOR)

        # Tiles
        for r, row in enumerate(game_map):
            for c, ch in enumerate(row):
                rx, ry = c * TILE - cam_x, r * TILE - cam_y
                rect = pygame.Rect(rx, ry, TILE, TILE)
                if ch == "1":
                    pygame.draw.rect(screen, WALL_COLOR, rect)
                    pygame.draw.rect(screen, (90, 60, 110), rect, 1)
                elif ch in (".", "3"):
                    pygame.draw.rect(screen, FLOOR_COLOR, rect)
                    pygame.draw.rect(screen, (190, 175, 210), rect, 1)
                    if ch == "3":   # open door
                        pygame.draw.rect(screen, (120, 200, 120), rect.inflate(-8, -8), 3)
                elif ch == "2":   # locked door
                    pygame.draw.rect(screen, FLOOR_COLOR, rect)
                    pygame.draw.rect(screen, DOOR_COLOR, rect.inflate(-4, -4), 4)
                    lock = font_small.render("🔒", True, DARK)
                    screen.blit(lock, (rx + 8, ry + 8))

        # Exit
        ex_sx, ex_sy = world_to_screen(*exit_pos, cam_x, cam_y)
        draw_exit(screen, ex_sx, ex_sy, anim_tick)

        # Keys
        for k in keys_pos:
            if k[2]:
                kx, ky = world_to_screen(k[0], k[1], cam_x, cam_y)
                draw_key(screen, kx, ky, anim_tick)

        # Notes
        for n in notes_pos:
            if n[2]:
                nx2, ny2 = world_to_screen(n[0], n[1], cam_x, cam_y)
                draw_note(screen, nx2, ny2)

        # Monsters
        for m in monsters:
            mx, my = world_to_screen(m.x, m.y, cam_x, cam_y)
            # save & translate
            orig_x, orig_y = m.x, m.y
            m.x, m.y = mx, my
            m.draw(screen)
            m.x, m.y = orig_x, orig_y

        # Player
        px_s, py_s = world_to_screen(player.x, player.y, cam_x, cam_y)
        orig_x, orig_y = player.x, player.y
        player.x, player.y = px_s, py_s
        player.draw(screen)
        player.x, player.y = orig_x, orig_y

        # Drone
        if drone.active:
            dx_s, dy_s = world_to_screen(drone.x, drone.y, cam_x, cam_y)
            orig_dx, orig_dy = drone.x, drone.y
            drone.x, drone.y = dx_s, dy_s
            drone.draw(screen)
            drone.x, drone.y = orig_dx, orig_dy

        # ── HUD ───────────────────────────────────────────────────────────────
        # Health
        for i in range(3):
            col = RED if i < player.health else DARK
            pygame.draw.circle(screen, col, (20 + i * 30, 25), 10)
            pygame.draw.circle(screen, WHITE, (20 + i * 30, 25), 10, 2)

        # Key indicator
        if player.has_key:
            draw_key(screen, 115, 22, anim_tick)
            kt = font_small.render("מפתח!", True, KEY_COLOR)
            screen.blit(kt, (130, 14))

        # Notes
        nt = font_small.render(f"📝 {player.notes_found}", True, YELLOW)
        screen.blit(nt, (12, 48))

        # Score
        st = font_small.render(f"ניקוד: {score}", True, WHITE)
        screen.blit(st, (WIDTH - st.get_width() - 10, 8))

        # Controls hint
        hint = font_small.render("W/A/S/D=זוז  TAB=רחפן  IJKL=הזז רחפן  ESC=יציאה", True, GRAY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 22))

        # Drone mode notice
        if drone.active:
            dt_txt = font_small.render("[ מצב רחפן פעיל ]", True, CYAN)
            screen.blit(dt_txt, (WIDTH // 2 - dt_txt.get_width() // 2, HEIGHT - 44))

        # ── Note overlay ──────────────────────────────────────────────────────
        if state == "note":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            card = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 100, 400, 200)
            pygame.draw.rect(screen, (255, 240, 180), card, border_radius=12)
            pygame.draw.rect(screen, DARK, card, 3, border_radius=12)
            for i, line in enumerate(show_note_text.split("\n")):
                lt = font_heb.render(line, True, DARK)
                screen.blit(lt, (card.centerx - lt.get_width()//2, card.y + 30 + i * 32))
            cont = font_small.render("לחץ כל מקש להמשך", True, DARK)
            screen.blit(cont, (card.centerx - cont.get_width()//2, card.bottom - 30))

        # ── Win screen ────────────────────────────────────────────────────────
        if state == "win":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            w1 = font_big.render("🎉 ניצחת! 🎉", True, GREEN)
            w2 = font_med.render(f"מצאת את ילדך! ניקוד: {score}", True, YELLOW)
            w3 = font_small.render("R = שחק שוב  |  ESC = יציאה", True, GRAY)
            screen.blit(w1, (WIDTH//2 - w1.get_width()//2, HEIGHT//2 - 70))
            screen.blit(w2, (WIDTH//2 - w2.get_width()//2, HEIGHT//2))
            screen.blit(w3, (WIDTH//2 - w3.get_width()//2, HEIGHT//2 + 60))

        # ── Lose screen ───────────────────────────────────────────────────────
        if state == "lose":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((60, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            l1 = font_big.render("💀 נתפסת! 💀", True, RED)
            l2 = font_med.render("הבנבן אכל אותך...", True, ORANGE)
            l3 = font_small.render("R = שחק שוב  |  ESC = יציאה", True, GRAY)
            screen.blit(l1, (WIDTH//2 - l1.get_width()//2, HEIGHT//2 - 70))
            screen.blit(l2, (WIDTH//2 - l2.get_width()//2, HEIGHT//2))
            screen.blit(l3, (WIDTH//2 - l3.get_width()//2, HEIGHT//2 + 60))

        # ── Title bar splash (first 3 sec) ────────────────────────────────────
        if anim_tick < 180:
            alpha = max(0, 255 - int(anim_tick * 1.5))
            splash = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
            splash.fill((20, 10, 30, alpha))
            screen.blit(splash, (0, 0))
            title = font_big.render("🌸 גן של בנבן 🌸", True,
                                    (255, 200, 230, alpha))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 18))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
