"""
D3 ןבנב לש ןג - Raycasting first-person horror game
W/A/S/D = העונת    ←→ = בוביס    רבכע = בוביס    ESC = האיצי    R = בוש קחש
"""

import pygame, math, sys, random, os
pygame.init()

# -- Window & engine constants -------------------------------------------------
W, H     = 960, 560
HALF_H   = H // 2
screen   = pygame.display.set_mode((W, H))
pygame.display.set_caption("🌸 D3 ןבנב לש ןג 🌸")
clock    = pygame.time.Clock()

FOV       = math.pi / 3          # 60 deg
HALF_FOV  = FOV / 2
PROJ_DIST = (W / 2) / math.tan(HALF_FOV)   # projection plane distance
TILE      = 64
MAZE_SCALE = 2
MOVE_SPD  = 130    # world-units / sec
ROT_SPD   = 1.8    # rad / sec
SHOOT_COOLDOWN = 0.36
SHOOT_RANGE    = TILE * 5.6
SHOOT_ARC      = 0.09
STUN_TIME      = 0.75
RADIO_PULSE_TIME = 1.25
RADIO_COOLDOWN   = 9.0
GIANT_HP         = 10
GIANT_SPEED      = 128
GIANT_RENDER_SCALE = 10.0

# -- Fonts ---------------------------------------------------------------------
try:
    fnt_big = pygame.font.SysFont("arial", 46, bold=True)
    fnt_med = pygame.font.SysFont("arial", 28, bold=True)
    fnt_sm  = pygame.font.SysFont("arial", 18)
except Exception:
    fnt_big = pygame.font.Font(None, 52)
    fnt_med = pygame.font.Font(None, 34)
    fnt_sm  = pygame.font.Font(None, 22)

# -- Colors --------------------------------------------------------------------
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
GRAY   = (150, 150, 150)
RED    = (220,  60,  60)
GREEN  = ( 60, 200,  60)
BLUE   = ( 60, 120, 220)
YELLOW = (240, 220,  60)
ORANGE = (230, 130,  40)
PINK   = (240, 100, 180)
CYAN   = ( 60, 210, 210)
DARK   = ( 20,  15,  30)

CEIL_C  = (38, 44, 56)
FLOOR_C = (58, 46, 40)

# Wall type -> RGB base colour
WCOL = {
    1: (108, 82, 96),    # dim mauve wall
    2: (76, 110, 138),   # cold blue wall
    3: (132, 98, 70),    # wooden gate/door
    4: (72, 130, 88),    # open green gate
    5: (142, 70, 98),    # faded pink accent
}

# -- Map -----------------------------------------------------------------------
# 0=floor  1=main wall  2=inner wall  3=locked door  4=open door  5=accent wall
_M = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,2,2,2,0,0,0,0,1,0,0,0,0,2,2,2,0,0,0,0,1],
    [1,0,0,0,2,0,2,0,0,0,0,3,0,0,0,0,2,0,2,0,0,0,0,1],
    [1,0,0,0,2,0,2,0,0,0,0,1,0,0,0,0,2,0,2,0,0,0,0,1],
    [1,0,0,0,2,2,2,0,0,0,0,1,0,0,0,0,2,2,2,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1,0,5,0,1,0,0,0,0,0,1,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,3,0,0,1,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1,1,1,0,1,1,1,1,0,0,1,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,1,0,0,3,0,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]


def scale_map(src, factor):
    if factor <= 1:
        return [row[:] for row in src]
    out = []
    for row in src:
        expanded = []
        for cell in row:
            expanded.extend([cell] * factor)
        for _ in range(factor):
            out.append(expanded[:])
    return out


def add_extra_rooms(map_data):
    """Add additional room structures on the scaled map for richer layout."""
    s = MAZE_SCALE

    rooms = [
        # (x0, y0, x1, y1) in original map coordinates
        (2, 2, 7, 7),
        (14, 2, 20, 7),
        (2, 10, 7, 16),
        (14, 10, 21, 16),
        (9, 2, 13, 6),
        (9, 12, 13, 16),
        (2, 6, 5, 9),
        (6, 6, 9, 9),
        (14, 6, 17, 9),
        (17, 6, 20, 9),
        (2, 16, 6, 17),
        (7, 16, 10, 17),
        (11, 8, 13, 10),
        (18, 14, 21, 17),
    ]

    for x0, y0, x1, y1 in rooms:
        sx0, sy0 = x0 * s, y0 * s
        sx1, sy1 = x1 * s, y1 * s
        sx0 = max(1, min(sx0, MW - 2))
        sy0 = max(1, min(sy0, MH - 2))
        sx1 = max(1, min(sx1, MW - 2))
        sy1 = max(1, min(sy1, MH - 2))

        for yy in range(sy0, sy1 + 1):
            for xx in range(sx0, sx1 + 1):
                is_border = (yy == sy0 or yy == sy1 or xx == sx0 or xx == sx1)
                map_data[yy][xx] = 2 if is_border else 0

    # Doors between the newly added rooms and corridors.
    doors = [
        (7, 4), (14, 4),
        (7, 13), (14, 13),
        (11, 6), (11, 12),
        (5, 6), (9, 7),
        (17, 7), (20, 8),
        (6, 16), (10, 16),
        (13, 9), (18, 16),
    ]
    for dx, dy in doors:
        cx = min(max(dx * s, 1), MW - 2)
        cy = min(max(dy * s, 1), MH - 2)
        map_data[cy][cx] = 3

    # Extra open corridors to keep movement fluid.
    for by in [5, 8, 9, 11, 15]:
        yy = min(max(by * s, 1), MH - 2)
        for xx in range(2 * s, MW - 2 * s):
            if map_data[yy][xx] != 1:
                map_data[yy][xx] = 0


MAP  = scale_map(_M, MAZE_SCALE)   # mutable copy (doors change state)
MH   = len(MAP)
MW   = len(MAP[0])

def tile_at(mx, my):
    if mx < 0 or my < 0 or mx >= MW or my >= MH:
        return 1
    return MAP[my][mx]

def solid(mx, my):
    v = tile_at(mx, my)
    return v not in (0, 4)   # open door (4) is passable

# -- Sprite surface generators -------------------------------------------------
SZ = 128   # atlas size for each sprite

def _surf(sz=SZ):
    return pygame.Surface((sz, sz), pygame.SRCALPHA)


def _load_mouth_img():
    path = os.path.join(os.path.dirname(__file__), "img", "images (9).jpeg")
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception:
        return None


MOUTH_IMG = _load_mouth_img()


def _blit_mouth(dst, cx, cy, w, h):
    if MOUTH_IMG is None:
        return
    mouth = pygame.transform.smoothscale(MOUTH_IMG, (max(12, int(w)), max(10, int(h))))
    x = int(cx - mouth.get_width() // 2)
    y = int(cy - mouth.get_height() // 2)
    dst.blit(mouth, (x, y))

def mk_banban():
    s = _surf(); sz = SZ; c = sz // 2
    body = pygame.Rect(c - 21, 18, 42, 82)
    pygame.draw.rect(s, (64, 220, 94), body, border_radius=16)
    pygame.draw.rect(s, BLACK, body, 4, border_radius=16)

    # Asymmetric mascot arms for mural-like personality.
    pygame.draw.line(s, (64, 220, 94), (c - 18, 43), (c - 46, 56), 12)
    pygame.draw.line(s, BLACK, (c - 18, 43), (c - 46, 56), 4)
    pygame.draw.line(s, (64, 220, 94), (c + 18, 42), (c + 44, 72), 12)
    pygame.draw.line(s, BLACK, (c + 18, 42), (c + 44, 72), 4)

    pygame.draw.line(s, (64, 220, 94), (c - 10, 98), (c - 14, 124), 11)
    pygame.draw.line(s, BLACK, (c - 10, 98), (c - 14, 124), 4)
    pygame.draw.line(s, (64, 220, 94), (c + 10, 98), (c + 14, 124), 11)
    pygame.draw.line(s, BLACK, (c + 10, 98), (c + 14, 124), 4)

    for ex in (-10, 10):
        pygame.draw.circle(s, WHITE, (c + ex, 38), 7)
        pygame.draw.circle(s, BLACK, (c + ex + 1, 39), 3)

    grin = pygame.Rect(c - 18, 50, 36, 16)
    pygame.draw.rect(s, (250, 250, 250), grin, border_radius=6)
    pygame.draw.rect(s, BLACK, grin, 3, border_radius=6)
    for i in range(1, 6):
        x = grin.x + i * (grin.w // 6)
        pygame.draw.line(s, BLACK, (x, grin.y + 2), (x, grin.bottom - 3), 1)
    return s

def mk_opila():
    s = _surf(); sz = SZ; c = sz // 2
    # Long-neck pink bird mascot.
    pygame.draw.ellipse(s, (242, 134, 168), (c - 24, 48, 48, 40))
    pygame.draw.ellipse(s, BLACK, (c - 24, 48, 48, 40), 4)
    pygame.draw.rect(s, (242, 134, 168), (c - 8, 28, 16, 24), border_radius=7)
    pygame.draw.rect(s, BLACK, (c - 8, 28, 16, 24), 3, border_radius=7)
    pygame.draw.circle(s, (242, 134, 168), (c, 22), 12)
    pygame.draw.circle(s, BLACK, (c, 22), 12, 3)

    pygame.draw.circle(s, WHITE, (c - 4, 21), 4)
    pygame.draw.circle(s, BLACK, (c - 3, 22), 2)
    pygame.draw.polygon(s, (255, 190, 70), [(c + 6, 22), (c + 20, 19), (c + 20, 25)])
    pygame.draw.polygon(s, BLACK, [(c + 6, 22), (c + 20, 19), (c + 20, 25)], 2)

    pygame.draw.line(s, (242, 134, 168), (c - 11, 84), (c - 20, 123), 8)
    pygame.draw.line(s, BLACK, (c - 11, 84), (c - 20, 123), 3)
    pygame.draw.line(s, (242, 134, 168), (c + 11, 84), (c + 20, 123), 8)
    pygame.draw.line(s, BLACK, (c + 11, 84), (c + 20, 123), 3)

    pygame.draw.line(s, (242, 134, 168), (c - 23, 62), (c - 42, 74), 8)
    pygame.draw.line(s, BLACK, (c - 23, 62), (c - 42, 74), 3)
    pygame.draw.line(s, (242, 134, 168), (c + 23, 62), (c + 42, 58), 8)
    pygame.draw.line(s, BLACK, (c + 23, 62), (c + 42, 58), 3)
    return s

def mk_banbaleena():
    s = _surf(); sz = SZ; c = sz // 2
    # Red horned mascot with broad silhouette.
    body = pygame.Rect(c - 22, 28, 44, 74)
    pygame.draw.rect(s, (224, 66, 66), body, border_radius=14)
    pygame.draw.rect(s, BLACK, body, 4, border_radius=14)

    pygame.draw.polygon(s, (224, 66, 66), [(c - 14, 28), (c - 6, 10), (c - 1, 28)])
    pygame.draw.polygon(s, BLACK, [(c - 14, 28), (c - 6, 10), (c - 1, 28)], 3)
    pygame.draw.polygon(s, (224, 66, 66), [(c + 14, 28), (c + 6, 10), (c + 1, 28)])
    pygame.draw.polygon(s, BLACK, [(c + 14, 28), (c + 6, 10), (c + 1, 28)], 3)

    for ex in (-9, 9):
        pygame.draw.circle(s, WHITE, (c + ex, 42), 6)
        pygame.draw.circle(s, BLACK, (c + ex + 1, 43), 3)

    mouth = pygame.Rect(c - 14, 54, 28, 13)
    pygame.draw.rect(s, (242, 242, 242), mouth, border_radius=5)
    pygame.draw.rect(s, BLACK, mouth, 3, border_radius=5)
    for i in range(1, 5):
        x = mouth.x + i * (mouth.w // 5)
        pygame.draw.line(s, BLACK, (x, mouth.y + 1), (x, mouth.bottom - 2), 1)

    pygame.draw.line(s, (224, 66, 66), (c - 20, 56), (c - 42, 66), 9)
    pygame.draw.line(s, BLACK, (c - 20, 56), (c - 42, 66), 4)
    pygame.draw.line(s, (224, 66, 66), (c + 20, 56), (c + 42, 66), 9)
    pygame.draw.line(s, BLACK, (c + 20, 56), (c + 42, 66), 4)

    pygame.draw.line(s, (224, 66, 66), (c - 10, 100), (c - 13, 124), 10)
    pygame.draw.line(s, BLACK, (c - 10, 100), (c - 13, 124), 4)
    pygame.draw.line(s, (224, 66, 66), (c + 10, 100), (c + 13, 124), 10)
    pygame.draw.line(s, BLACK, (c + 10, 100), (c + 13, 124), 4)
    return s


def mk_giant():
    s = _surf(); sz = SZ; c = sz // 2
    body = pygame.Rect(c - 28, 10, 56, 106)
    pygame.draw.rect(s, (84, 210, 92), body, border_radius=20)
    pygame.draw.rect(s, BLACK, body, 5, border_radius=20)

    for ex in (-13, 13):
        pygame.draw.circle(s, WHITE, (c + ex, 32), 8)
        pygame.draw.circle(s, (160, 0, 0), (c + ex + 1, 33), 5)
        pygame.draw.circle(s, BLACK, (c + ex + 2, 33), 2)

    grin = pygame.Rect(c - 20, 48, 40, 20)
    pygame.draw.rect(s, (248, 248, 248), grin, border_radius=7)
    pygame.draw.rect(s, BLACK, grin, 3, border_radius=7)
    for i in range(1, 7):
        x = grin.x + i * (grin.w // 7)
        pygame.draw.line(s, BLACK, (x, grin.y + 2), (x, grin.bottom - 3), 1)

    pygame.draw.line(s, (84, 210, 92), (c - 24, 58), (c - 52, 76), 12)
    pygame.draw.line(s, BLACK, (c - 24, 58), (c - 52, 76), 5)
    pygame.draw.line(s, (84, 210, 92), (c + 24, 58), (c + 52, 76), 12)
    pygame.draw.line(s, BLACK, (c + 24, 58), (c + 52, 76), 5)
    return s

def mk_key():
    s = _surf(64); sz = 64; c = sz//2
    pygame.draw.circle(s, YELLOW, (c-4, sz//3), 12, 4)
    pygame.draw.rect(s, YELLOW, (c+6, sz//3-3, sz//3+4, 6))
    pygame.draw.rect(s, YELLOW, (c+sz//5+6, sz//3-10, 5, 8))
    pygame.draw.rect(s, YELLOW, (c+sz//4+8, sz//3-10, 5, 8))
    return s

def mk_note():
    s = _surf(64); sz = 64; c = sz//2
    pygame.draw.rect(s, (255,248,185), (c-14, sz//5, 28, sz//2+4), border_radius=3)
    pygame.draw.rect(s, GRAY,          (c-14, sz//5, 28, sz//2+4), 2, border_radius=3)
    for i in range(4):
        pygame.draw.line(s, GRAY, (c-8, sz//4+i*9), (c+8, sz//4+i*9), 1)
    return s

def mk_exit():
    s = _surf(64); sz = 64; c = sz//2
    pygame.draw.rect(s, (0, 210, 0), (sz//5, sz//8, 3*sz//5, 3*sz//4), border_radius=6)
    pygame.draw.polygon(s, WHITE, [(c, sz//5),(3*sz//4,c),(c,4*sz//5)])
    pygame.draw.polygon(s, WHITE, [(c, sz//5),(sz//4,c),(c,4*sz//5)])
    t = fnt_sm.render("EXIT", True, WHITE)
    s.blit(t, (c-t.get_width()//2, c-t.get_height()//2))
    return s

def mk_body():
    img_path = os.path.join(os.path.dirname(__file__), "img", "55d79dd3-1f65-4ecc-b09c-b0079ac9751b.png")
    try:
        img = pygame.image.load(img_path).convert_alpha()
        img = pygame.transform.rotate(img, 90)
        return pygame.transform.smoothscale(img, (160, 90))
    except Exception:
        # Fallback if image is missing/corrupt
        s = _surf(96)
        pygame.draw.ellipse(s, (95, 75, 70), (18, 38, 58, 24))
        pygame.draw.circle(s, (215, 180, 150), (74, 50), 10)
        pygame.draw.line(s, (80, 60, 55), (28, 44), (14, 36), 5)
        pygame.draw.line(s, (80, 60, 55), (30, 56), (14, 64), 5)
        pygame.draw.line(s, (70, 50, 45), (58, 56), (46, 72), 5)
        pygame.draw.line(s, (70, 50, 45), (66, 56), (56, 72), 5)
        return s

SURFS = {
    "banban":     mk_banban(),
    "opila":      mk_opila(),
    "banbaleena": mk_banbaleena(),
    "giant":      mk_giant(),
    "key":        mk_key(),
    "note":       mk_note(),
    "exit":       mk_exit(),
    "body":       mk_body(),
}

# -- Player --------------------------------------------------------------------
class Player:
    def __init__(self):
        self.x = 1.5 * MAZE_SCALE * TILE
        self.y = 1.5 * MAZE_SCALE * TILE
        self.angle     = 0.0
        self.health    = 3
        self.has_key   = False
        self.notes     = 0
        self.score     = 0
        self.kills     = 0
        self.body_found = False
        self.invincible = 0.0
        self.shoot_cd   = 0.0
        self.radio_cd   = 0.0

    def move(self, fwd, strafe, dt):
        spd = MOVE_SPD * dt
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        nx = self.x + ca * fwd * spd - sa * strafe * spd
        ny = self.y + sa * fwd * spd + ca * strafe * spd
        m  = 14
        if not solid(int((nx+m)//TILE), int(self.y//TILE)) and \
           not solid(int((nx-m)//TILE), int(self.y//TILE)):
            self.x = nx
        if not solid(int(self.x//TILE), int((ny+m)//TILE)) and \
           not solid(int(self.x//TILE), int((ny-m)//TILE)):
            self.y = ny

    def update(self, dt):
        self.invincible = max(0.0, self.invincible - dt)
        self.shoot_cd = max(0.0, self.shoot_cd - dt)
        self.radio_cd = max(0.0, self.radio_cd - dt)

    def hit(self):
        if self.invincible <= 0:
            self.health -= 1
            self.invincible = 1.5
            return True
        return False

# -- Monster -------------------------------------------------------------------
class Monster:
    def __init__(self, kind, x, y, hp=1, spd=65, sight=280):
        self.kind  = kind
        self.x     = float(x)
        self.y     = float(y)
        self.hp    = hp
        self.spd   = spd
        self.sight = sight
        self.active = True
        self.stun   = 0.0
        self.anim   = random.randint(0, 200)
        self.state  = "wander"
        self.forced_chase = False
        self.enraged = False
        ang = random.uniform(0, 6.28)
        self.vx = math.cos(ang) * 35
        self.vy = math.sin(ang) * 35

    def update(self, player, dt):
        if not self.active: return
        self.anim += 1
        if self.stun > 0:
            self.stun -= dt; return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if self.kind == "giant":
            self.state = "chase"
            if dist > 1:
                nx = self.x + (dx / dist) * self.spd * dt
                ny = self.y + (dy / dist) * self.spd * dt
                self.x = min(max(nx, TILE), (MW - 2) * TILE)
                self.y = min(max(ny, TILE), (MH - 2) * TILE)
            self.break_walls()
            return

        if self.forced_chase:
            self.state = "chase"
        elif dist < self.sight:
            self.state = "chase"
        elif dist > self.sight * 1.6:
            self.state = "wander"

        if self.state == "chase":
            if dist > 1:
                cur_spd = self.spd * (1.65 if self.enraged else 1.0)
                nx = self.x + (dx/dist) * cur_spd * dt
                ny = self.y + (dy/dist) * cur_spd * dt
                if not solid(int(nx//TILE), int(self.y//TILE)): self.x = nx
                if not solid(int(self.x//TILE), int(ny//TILE)): self.y = ny
        else:
            nx = self.x + self.vx * dt
            ny = self.y + self.vy * dt
            if solid(int(nx//TILE), int(self.y//TILE)):
                self.vx *= -1
            else:
                self.x = nx
            if solid(int(self.x//TILE), int(ny//TILE)):
                self.vy *= -1
            else:
                self.y = ny
            if random.random() < 0.006:
                ang2 = random.uniform(0, 6.28)
                self.vx = math.cos(ang2) * 35
                self.vy = math.sin(ang2) * 35

    def break_walls(self):
        if self.kind != "giant":
            return
        mx = int(self.x // TILE)
        my = int(self.y // TILE)
        for yy in range(my - 1, my + 2):
            for xx in range(mx - 1, mx + 2):
                if xx <= 0 or yy <= 0 or xx >= MW - 1 or yy >= MH - 1:
                    continue
                if MAP[yy][xx] in (1, 2, 3, 5):
                    MAP[yy][xx] = 0

# -- Item ----------------------------------------------------------------------
class Item:
    def __init__(self, kind, x, y):
        self.kind   = kind
        self.x      = float(x)
        self.y      = float(y)
        self.active = True
        self.anim   = random.randint(0, 200)


def angle_diff(a, b):
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return abs(d)


def has_line_of_sight(x0, y0, x1, y1):
    dx = x1 - x0
    dy = y1 - y0
    dist = math.hypot(dx, dy)
    if dist < 1:
        return True

    steps = max(4, int(dist / (TILE * 0.18)))
    for i in range(1, steps):
        t = i / steps
        sx = x0 + dx * t
        sy = y0 + dy * t
        if solid(int(sx // TILE), int(sy // TILE)):
            return False
    return True


def try_shoot(player, monsters):
    if player.shoot_cd > 0:
        return "cooldown"

    player.shoot_cd = SHOOT_COOLDOWN
    target = None
    best = 10**9

    for m in monsters:
        if not m.active:
            continue

        dx = m.x - player.x
        dy = m.y - player.y
        dist = math.hypot(dx, dy)
        if dist > SHOOT_RANGE:
            continue

        ang = math.atan2(dy, dx)
        if angle_diff(ang, player.angle) > SHOOT_ARC:
            continue

        if not has_line_of_sight(player.x, player.y, m.x, m.y):
            continue

        if dist < best:
            best = dist
            target = m

    if target is None:
        return "miss"

    target.hp -= 1
    if target.hp <= 0:
        target.active = False
        player.kills += 1
        player.score += 120
        return "kill"

    target.stun = STUN_TIME
    player.score += 35
    return "hit"


def trigger_radio_pulse(player):
    if player.radio_cd > 0:
        return False
    player.radio_cd = RADIO_COOLDOWN
    return True


def alert_all_monsters(monsters):
    for m in monsters:
        if not m.active:
            continue
        m.forced_chase = True
        m.state = "chase"
        m.stun = max(0.0, m.stun - 0.35)


def enrage_all_monsters(monsters):
    for m in monsters:
        if not m.active:
            continue
        m.enraged = True
        m.forced_chase = True
        m.state = "chase"


def spawn_giant_monster(player, monsters):
    # Spawn away from player, then force chase.
    candidates = [
        (3.5, 3.5),
        (20.5, 3.5),
        (3.5, 16.5),
        (20.5, 16.5),
        (12.5, 9.5),
    ]
    random.shuffle(candidates)
    for cx, cy in candidates:
        wx = cx * MAZE_SCALE * TILE
        wy = cy * MAZE_SCALE * TILE
        dist = math.hypot(wx - player.x, wy - player.y)
        if dist < TILE * 7:
            continue
        if solid(int(wx // TILE), int(wy // TILE)):
            continue
        g = Monster("giant", wx, wy, hp=GIANT_HP, spd=GIANT_SPEED, sight=9999)
        g.forced_chase = True
        g.enraged = True
        monsters.append(g)
        return g

    # Fallback if no candidate works.
    g = Monster("giant", 12.5 * MAZE_SCALE * TILE, 9.5 * MAZE_SCALE * TILE, hp=GIANT_HP, spd=GIANT_SPEED, sight=9999)
    g.forced_chase = True
    g.enraged = True
    monsters.append(g)
    return g

# -- Raycasting ----------------------------------------------------------------
def raycast(player):
    """DDA raycasting - returns (z_buffer, strip_list).
    z_buffer[col] = perpendicular wall distance (world units).
    strip_list = list of (col, top, bot, rgb).
    """
    z_buf   = [0.0] * W
    strips  = []
    ray_ang = player.angle - HALF_FOV
    da      = FOV / W

    for col in range(W):
        ca = math.cos(ray_ang)
        sa = math.sin(ray_ang)
        if ca == 0: ca = 1e-9
        if sa == 0: sa = 1e-9

        mx = int(player.x // TILE)
        my = int(player.y // TILE)

        ddx = abs(1.0 / ca)
        ddy = abs(1.0 / sa)

        if ca < 0:
            sx = -1; sdx = (player.x/TILE - mx) * ddx
        else:
            sx =  1; sdx = (mx + 1 - player.x/TILE) * ddx
        if sa < 0:
            sy = -1; sdy = (player.y/TILE - my) * ddy
        else:
            sy =  1; sdy = (my + 1 - player.y/TILE) * ddy

        wtype = 1; side = 0
        for _ in range(MW + MH):
            if sdx < sdy:
                sdx += ddx; mx += sx; side = 0
            else:
                sdy += ddy; my += sy; side = 1
            v = tile_at(mx, my)
            if v not in (0, 4):
                wtype = v; break

        # Perpendicular (fish-eye-free) distance
        if side == 0:
            perp = (sdx - ddx) * TILE
        else:
            perp = (sdy - ddy) * TILE
        perp = max(perp, 0.5)

        z_buf[col] = perp

        wh  = min(int(PROJ_DIST * TILE / perp), H * 4)
        top = HALF_H - wh // 2
        bot = top + wh

        shade = max(0.12, 1.0 - perp / (TILE * 13))
        if side == 1: shade *= 0.62
        bc = WCOL.get(wtype, (110,75,145))
        c2 = (max(0,min(255,int(bc[0]*shade))),
              max(0,min(255,int(bc[1]*shade))),
              max(0,min(255,int(bc[2]*shade))))
        strips.append((col, top, bot, c2))
        ray_ang += da

    return z_buf, strips

# -- Scene drawing -------------------------------------------------------------
def draw_scene(player, monsters, items, z_buf, strips, tick, radio_anim=0.0):
    # Ceiling & floor with creepy kindergarten mood
    screen.fill(CEIL_C)
    pygame.draw.rect(screen, FLOOR_C, (0, HALF_H, W, HALF_H))

    # Dark wood-like floor bands with faint color remnants.
    for row in range(0, HALF_H, 4):
        t = row / max(1, HALF_H)
        band = int((row // 16) % 5)
        if band == 0:
            base = (86, 58, 52)
        elif band == 1:
            base = (74, 64, 88)
        elif band == 2:
            base = (88, 66, 48)
        elif band == 3:
            base = (62, 78, 70)
        else:
            base = (80, 54, 70)
        r2 = int(base[0] * (0.8 + 0.2 * t))
        g2 = int(base[1] * (0.8 + 0.2 * t))
        b2 = int(base[2] * (0.8 + 0.2 * t))
        pygame.draw.line(screen, (r2,g2,b2), (0, HALF_H+row), (W, HALF_H+row))

    # Subtle darkness overlay that pulses slightly for creepy ambience.
    pulse = 34 + int(10 * abs(math.sin(tick * 0.035)))
    dark_ov = pygame.Surface((W, H), pygame.SRCALPHA)
    dark_ov.fill((0, 0, 0, pulse))
    screen.blit(dark_ov, (0, 0))

    # Walls
    for col, top, bot, c2 in strips:
        pygame.draw.line(screen, c2, (col, top), (col, bot))

    # -- Sprites ----------------------------------------------------------------
    all_spr = []
    for m in monsters:
        if m.active:
            m.anim += 1
            all_spr.append((m.x, m.y, m.kind, True,  m.stun > 0, m.anim, m.enraged))
    for it in items:
        if it.active:
            it.anim += 1
            all_spr.append((it.x, it.y, it.kind, False, False,     it.anim, False))

    # Sort far -> near (painter's order)
    all_spr.sort(key=lambda s: (s[0]-player.x)**2 + (s[1]-player.y)**2, reverse=True)

    for sx, sy, skind, is_monster, stunned, sanim, enraged in all_spr:
        dx = sx - player.x
        dy = sy - player.y
        euc = math.hypot(dx, dy)
        if euc < 1: continue

        rel = math.atan2(dy, dx) - player.angle
        while rel >  math.pi: rel -= 2 * math.pi
        while rel < -math.pi: rel += 2 * math.pi
        if abs(rel) > HALF_FOV + 0.25: continue

        # Perpendicular distance
        perp = euc * math.cos(rel)
        if perp < 1: continue

        spr_h = min(int(PROJ_DIST * TILE / perp), H * 3)
        if skind == "giant":
            spr_h = min(int(spr_h * GIANT_RENDER_SCALE), H * 20)
        if is_monster and enraged:
            spr_h = int(spr_h * 1.35)
        spr_w = spr_h
        if spr_h < 2: continue

        scr_x = int(W / 2 + rel / HALF_FOV * (W / 2))
        scr_y = HALF_H - spr_h // 2

        # Bob for items
        if not is_monster:
            scr_y += int(math.sin(sanim * 0.07) * 5)

        surf  = SURFS.get(skind, SURFS["banban"])
        sw, sh = max(1,spr_w), max(1,spr_h)
        scaled = pygame.transform.scale(surf, (sw, sh))
        left   = scr_x - sw // 2

        # Distance fog
        fog = max(0, min(180, int(perp / (TILE * 10) * 180)))
        _ = fog

        for i in range(sw):
            col_s = left + i
            if 0 <= col_s < W and z_buf[col_s] > perp:
                strip_rect = pygame.Rect(i, 0, 1, sh)
                if strip_rect.right <= scaled.get_width():
                    screen.blit(scaled.subsurface(strip_rect), (col_s, scr_y))

        # Stun stars above monster
        if stunned:
            for i in range(3):
                a2  = sanim * 0.05 + i * 2.09
                px2 = scr_x + int(math.cos(a2) * sw * 0.45)
                py2 = scr_y - 10 + int(math.sin(a2) * 8)
                if 0 <= px2 < W and 0 <= py2 < H:
                    pygame.draw.circle(screen, YELLOW, (px2, py2), max(3, sw//16))

        # Enraged eyes overlay for extra horror look.
        if is_monster and enraged:
            eye_y = scr_y + int(sh * 0.27)
            eye_dx = max(4, int(sw * 0.12))
            eye_r = max(3, int(sw * 0.035))
            for ex in (-eye_dx, eye_dx):
                px = scr_x + ex
                if 0 <= px < W and 0 <= eye_y < H:
                    pygame.draw.circle(screen, (255, 0, 0), (px, eye_y), eye_r)
                    pygame.draw.circle(screen, (255, 120, 120), (px, eye_y), max(1, eye_r // 2))

    if radio_anim > 0:
        p = max(0.0, min(1.0, radio_anim / RADIO_PULSE_TIME))
        fade = int(140 * (1.0 - p))
        cx, cy = W // 2, HALF_H
        base = int(24 + p * max(W, H) * 0.75)
        for i in range(3):
            rr = max(6, base - i * 90)
            if rr > 8:
                pygame.draw.circle(screen, (80, 230, 255, max(24, fade - i * 30)), (cx, cy), rr, 3)


def draw_minimap(player, monsters, items, size=150, tsz=8):
    ox, oy = 10, H - size - 10
    mm = pygame.Surface((size, size), pygame.SRCALPHA)
    mm.fill((0, 0, 0, 155))

    pc = int(player.x // TILE); pr = int(player.y // TILE)
    cols = size // tsz; rows = size // tsz
    sc0 = pc - cols//2; sr0 = pr - rows//2

    for r in range(rows):
        for c in range(cols):
            mc, mr = sc0+c, sr0+r
            if 0 <= mc < MW and 0 <= mr < MH:
                v  = MAP[mr][mc]
                fc = WCOL.get(v, (55,45,68)) if v else (55,45,68)
                pygame.draw.rect(mm, fc, (c*tsz, r*tsz, tsz-1, tsz-1))

    SCOLORS = {"banban":BLUE,"opila":YELLOW,"banbaleena":PINK,"giant":RED,
               "key":YELLOW,"note":(200,200,100),"exit":GREEN}
    for obj in [*monsters, *items]:
        if not obj.active: continue
        sc, sr = int(obj.x//TILE), int(obj.y//TILE)
        px2 = (sc - sc0)*tsz + tsz//2
        py2 = (sr - sr0)*tsz + tsz//2
        if 0 <= px2 < size and 0 <= py2 < size:
            pygame.draw.circle(mm, SCOLORS.get(obj.kind, WHITE), (px2, py2), 3)

    # Player
    ppx = (pc - sc0)*tsz + tsz//2
    ppy = (pr - sr0)*tsz + tsz//2
    pygame.draw.circle(mm, (0,255,0), (ppx, ppy), 5)
    ex2 = int(math.cos(player.angle)*11)
    ey2 = int(math.sin(player.angle)*11)
    pygame.draw.line(mm, CYAN, (ppx,ppy), (ppx+ex2,ppy+ey2), 2)

    screen.blit(mm, (ox, oy))


def draw_hud(player, monsters_left):
    # Hearts
    for i in range(3):
        c = RED if i < player.health else (55,25,25)
        cx, cy = 22+i*36, 26
        pygame.draw.circle(screen, c, (cx,cy), 13)
        pygame.draw.circle(screen, WHITE, (cx,cy), 13, 2)

    # Key icon
    if player.has_key:
        km = fnt_sm.render("🔑 !חתפמ שי", True, YELLOW)
        screen.blit(km, (125, 14))

    # Notes count
    nm = fnt_sm.render(f"📝 {player.notes}", True, YELLOW)
    screen.blit(nm, (12, 50))

    # Mission status
    mission = "BODY: FOUND" if player.body_found else "BODY: SEARCH"
    mm = fnt_sm.render(mission, True, GREEN if player.body_found else ORANGE)
    screen.blit(mm, (12, 72))

    mon = fnt_sm.render(f"MONSTERS: {monsters_left}", True, WHITE)
    screen.blit(mon, (12, 94))

    shoot_state = "READY" if player.shoot_cd <= 0 else "RECHARGE"
    shoot_col = CYAN if player.shoot_cd <= 0 else GRAY
    shot = fnt_sm.render(f"LMB: {shoot_state}", True, shoot_col)
    screen.blit(shot, (12, 116))

    radio_state = "READY" if player.radio_cd <= 0 else f"{player.radio_cd:0.1f}s"
    radio_col = CYAN if player.radio_cd <= 0 else GRAY
    radio = fnt_sm.render(f"1 RADIO: {radio_state}", True, radio_col)
    screen.blit(radio, (12, 138))

    # Score
    sc = fnt_sm.render(f":דוקינ {player.score}", True, WHITE)
    screen.blit(sc, (W - sc.get_width() - 10, 8))

    # Crosshair
    cx, cy = W//2, HALF_H
    pygame.draw.line(screen, (200,200,200), (cx-14,cy),   (cx-4,cy),   1)
    pygame.draw.line(screen, (200,200,200), (cx+4, cy),   (cx+14,cy),  1)
    pygame.draw.line(screen, (200,200,200), (cx,   cy-14),(cx,  cy-4), 1)
    pygame.draw.line(screen, (200,200,200), (cx,   cy+4), (cx,  cy+14),1)
    pygame.draw.circle(screen, (200,200,200), (cx,cy), 2)

    # Controls bar
    hint = fnt_sm.render("W/A/S/D move | mouse look | LMB shoot | 1 radio | 2 rage | E inspect | ESC quit", True, (90,90,115))
    screen.blit(hint, (W//2 - hint.get_width()//2, H - 20))


def draw_damage_flash(alpha):
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((200, 0, 0, int(alpha)))
    screen.blit(ov, (0, 0))


NOTE_TEXTS = [
    ["...ןגב דבא ידלי :ןמוי", "!ותוא אוצמל בייח"],
    ["!םייח םילספה :הרהזא", "!וררועתי םהש ינפל חרב"],
]


def draw_note_card(lines):
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 165))
    screen.blit(ov, (0, 0))
    card = pygame.Rect(W//2-240, H//2-110, 480, 220)
    pygame.draw.rect(screen, (255,248,185), card, border_radius=14)
    pygame.draw.rect(screen, (100,80,30),  card, 3, border_radius=14)
    for i, line in enumerate(lines):
        lt = fnt_med.render(line, True, DARK)
        screen.blit(lt, (card.centerx - lt.get_width()//2, card.y+30+i*44))
    cont = fnt_sm.render("...ךשמהל שקמ לכ ץחל", True, (100,80,30))
    screen.blit(cont, (card.centerx - cont.get_width()//2, card.bottom-28))


def draw_overlay(lines, col):
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 185))
    screen.blit(ov, (0, 0))
    for i, line in enumerate(lines):
        f  = fnt_big if i == 0 else fnt_med
        t  = f.render(line, True, col)
        screen.blit(t, (W//2 - t.get_width()//2, H//2 - 70 + i*54))


def draw_center_hint(text, col=(255, 80, 80)):
    box = pygame.Rect(W//2 - 210, H//2 - 55, 420, 110)
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 70))
    screen.blit(ov, (0, 0))
    pygame.draw.rect(screen, (25, 20, 35), box, border_radius=10)
    pygame.draw.rect(screen, col, box, 3, border_radius=10)
    txt = fnt_big.render(text, True, col)
    screen.blit(txt, (box.centerx - txt.get_width()//2, box.centery - txt.get_height()//2))


# -- Title screen --------------------------------------------------------------
def draw_title():
    screen.fill(DARK)
    # Animated creepy background lines
    for i in range(0, H, 20):
        v = int(10 + 15 * abs(math.sin(i*0.05 + pygame.time.get_ticks()*0.001)))
        pygame.draw.line(screen, (v, 0, v*2), (0,i),(W,i))

    title = fnt_big.render("🌸 D3 ןבנב לש ןג 🌸", True, PINK)
    sub   = fnt_med.render("ידממ-תלת המיא קחשמ", True, (180,140,220))
    inst  = fnt_sm.render("ליחתהל ידכ חוור וא RETNE ץחל", True, WHITE)
    esc   = fnt_sm.render("האיצי = CSE", True, GRAY)

    t = pygame.time.get_ticks()
    pulse = int(abs(math.sin(t*0.002))*30)
    title2 = pygame.transform.scale(title,
        (title.get_width()+pulse, title.get_height()+pulse//4))

    screen.blit(title2, (W//2 - title2.get_width()//2, H//2 - 140))
    screen.blit(sub,    (W//2 - sub.get_width()//2,   H//2 - 50))
    screen.blit(inst,   (W//2 - inst.get_width()//2,  H//2 + 30))
    screen.blit(esc,    (W//2 - esc.get_width()//2,   H//2 + 70))

    # Draw the 3 monsters at bottom
    y0 = H - 140
    for i, (surf, label) in enumerate([
            (SURFS["banban"],     "ןבנב"),
            (SURFS["opila"],      "הליפוא"),
            (SURFS["banbaleena"], "הנילאבנב"),
    ]):
        scaled = pygame.transform.scale(surf, (90,90))
        x0 = W//4*(i+1) - 45
        screen.blit(scaled, (x0, y0))
        lbl = fnt_sm.render(label, True, GRAY)
        screen.blit(lbl, (x0+45 - lbl.get_width()//2, y0+94))


# -- Main ----------------------------------------------------------------------
def build():
    global MAP
    MAP = scale_map(_M, MAZE_SCALE)
    add_extra_rooms(MAP)
    p = Player()
    monsters = [
        Monster("banban",      6.5*MAZE_SCALE*TILE,   5.5*MAZE_SCALE*TILE, hp=1, spd=65,  sight=280),
        Monster("opila",      16.5*MAZE_SCALE*TILE,   3.5*MAZE_SCALE*TILE, hp=2, spd=48,  sight=340),
        Monster("banbaleena", 18.5*MAZE_SCALE*TILE,  14.5*MAZE_SCALE*TILE, hp=1, spd=80,  sight=250),
        Monster("banban",      4.5*MAZE_SCALE*TILE,  15.5*MAZE_SCALE*TILE, hp=1, spd=72,  sight=260),
        Monster("opila",      20.5*MAZE_SCALE*TILE,  10.5*MAZE_SCALE*TILE, hp=2, spd=52,  sight=320),
        Monster("banbaleena",  9.5*MAZE_SCALE*TILE,  16.5*MAZE_SCALE*TILE, hp=1, spd=84,  sight=240),
        Monster("banban",      3.5*MAZE_SCALE*TILE,   3.5*MAZE_SCALE*TILE, hp=1, spd=78,  sight=290),
        Monster("opila",       7.5*MAZE_SCALE*TILE,   6.5*MAZE_SCALE*TILE, hp=2, spd=56,  sight=360),
        Monster("banbaleena", 15.5*MAZE_SCALE*TILE,   6.5*MAZE_SCALE*TILE, hp=1, spd=90,  sight=260),
        Monster("banban",     19.5*MAZE_SCALE*TILE,   5.5*MAZE_SCALE*TILE, hp=1, spd=74,  sight=300),
        Monster("opila",       5.5*MAZE_SCALE*TILE,  12.5*MAZE_SCALE*TILE, hp=2, spd=58,  sight=350),
        Monster("banbaleena",  6.5*MAZE_SCALE*TILE,  15.5*MAZE_SCALE*TILE, hp=1, spd=88,  sight=255),
        Monster("banban",     15.5*MAZE_SCALE*TILE,  13.5*MAZE_SCALE*TILE, hp=1, spd=76,  sight=285),
        Monster("opila",      20.5*MAZE_SCALE*TILE,  15.5*MAZE_SCALE*TILE, hp=2, spd=60,  sight=365),
    ]
    items = [
        Item("key",   15.5*MAZE_SCALE*TILE,   5.5*MAZE_SCALE*TILE),
        Item("key",   14.5*MAZE_SCALE*TILE,  15.5*MAZE_SCALE*TILE),
        Item("note",   5.5*MAZE_SCALE*TILE,  10.5*MAZE_SCALE*TILE),
        Item("note",  17.5*MAZE_SCALE*TILE,  12.5*MAZE_SCALE*TILE),
        Item("body",  12.5*MAZE_SCALE*TILE,   1.5*MAZE_SCALE*TILE),
        Item("exit",  21.5*MAZE_SCALE*TILE,  17.5*MAZE_SCALE*TILE),
    ]
    return p, monsters, items


def main():
    state = "title"
    player, monsters, items = build()
    note_text  = []
    flash      = 0.0
    tick       = 0
    msg_timer = 0.0
    msg_text = ""
    radio_anim = 0.0
    radio_pending_alert = False
    giant_spawned = False

    pygame.mouse.set_visible(False)

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        tick += 1

        # -- Events ------------------------------------------------------------
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.event.set_grab(False)
                    pygame.mouse.set_visible(True)
                    pygame.quit(); sys.exit()

                if state == "title":
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        state = "play"
                        pygame.event.set_grab(True)

                elif state == "note":
                    state = "play"

                elif state in ("win", "lose") and ev.key == pygame.K_r:
                    player, monsters, items = build()
                    state = "play"
                    flash = 0.0
                    giant_spawned = False

                elif state == "play" and ev.key == pygame.K_e:
                    for it in items:
                        if it.active and it.kind == "body":
                            if math.hypot(it.x - player.x, it.y - player.y) < 70:
                                it.active = False
                                player.body_found = True
                                player.score += 220
                                msg_text = "Body found! Reach EXIT"
                                msg_timer = 2.2
                                break

                elif state == "play" and ev.key == pygame.K_1:
                    if trigger_radio_pulse(player):
                        radio_anim = RADIO_PULSE_TIME
                        radio_pending_alert = True
                        msg_text = "Radio pulse sent"
                        msg_timer = 0.8
                    else:
                        msg_text = "Radio recharging"
                        msg_timer = 0.5

                elif state == "play" and ev.key == pygame.K_2:
                    enrage_all_monsters(monsters)
                    msg_text = "Rage mode: monsters empowered"
                    msg_timer = 1.4

            if ev.type == pygame.MOUSEBUTTONDOWN and state == "play":
                if ev.button == 1:
                    shot = try_shoot(player, monsters)
                    if shot == "kill":
                        msg_text = "Target down"
                        msg_timer = 0.8
                    elif shot == "hit":
                        msg_text = "Hit"
                        msg_timer = 0.5
                    elif shot == "cooldown":
                        msg_text = "Reloading"
                        msg_timer = 0.35

            if ev.type == pygame.MOUSEMOTION and state == "play":
                player.angle += ev.rel[0] * 0.003
                player.angle %= 2 * math.pi

        # -- Update ------------------------------------------------------------
        if state == "play":
            keys = pygame.key.get_pressed()
            fwd = strafe = 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:    fwd    =  1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:  fwd    = -1
            if keys[pygame.K_a]:                          strafe = -1
            if keys[pygame.K_d]:                          strafe =  1
            if keys[pygame.K_LEFT]:  player.angle -= ROT_SPD * dt
            if keys[pygame.K_RIGHT]: player.angle += ROT_SPD * dt

            player.move(fwd, strafe, dt)
            player.update(dt)
            flash = max(0.0, flash - 240 * dt)
            msg_timer = max(0.0, msg_timer - dt)

            if radio_anim > 0:
                radio_anim = max(0.0, radio_anim - dt)
                if radio_anim <= 0 and radio_pending_alert:
                    alert_all_monsters(monsters)
                    radio_pending_alert = False
                    msg_text = "They heard you. Run!"
                    msg_timer = 1.4

            # Monsters - movement + attack
            for m in monsters:
                if not m.active: continue
                m.update(player, dt)
                hit_radius = 44 if m.kind == "giant" else 30
                if math.hypot(m.x - player.x, m.y - player.y) < hit_radius:
                    if player.hit():
                        flash = 220
                        if player.health <= 0:
                            state = "lose"

            # Items - pickup
            for it in items:
                if not it.active: continue
                if math.hypot(it.x - player.x, it.y - player.y) < 44:
                    if it.kind == "key":
                        it.active = False
                        player.has_key = True
                        player.score  += 50
                        if not giant_spawned:
                            spawn_giant_monster(player, monsters)
                            giant_spawned = True
                            msg_text = "Giant broke in! RUN!"
                            msg_timer = 2.0
                    elif it.kind == "note":
                        it.active = False
                        idx = player.notes % len(NOTE_TEXTS)
                        note_text = NOTE_TEXTS[idx]
                        player.notes += 1
                        player.score += 30
                        state = "note"
                    elif it.kind == "exit":
                        if player.body_found:
                            state = "win"
                            player.score += 500
                        else:
                            msg_text = "Find the body first"
                            msg_timer = 1.2

            # Unlock doors adjacent to player
            pc, pr = int(player.x // TILE), int(player.y // TILE)
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = pr+dr, pc+dc
                if 0 <= nr < MH and 0 <= nc < MW:
                    if MAP[nr][nc] == 3 and player.has_key:
                        MAP[nr][nc] = 4
                        player.has_key = False
                        player.score  += 100

        # -- Render ------------------------------------------------------------
        if state == "title":
            draw_title()
        else:
            z_buf, strips = raycast(player)
            draw_scene(player, monsters, items, z_buf, strips, tick, radio_anim)
            monsters_left = sum(1 for m in monsters if m.active)
            draw_hud(player, monsters_left)
            draw_minimap(player, monsters, items)

            if flash > 0:
                draw_damage_flash(flash)

            if state == "note":
                draw_note_card(note_text)
            elif state == "win":
                draw_overlay(
                    ["🎉  !תחצינ  🎉",
                     f"{player.score} :דוקינ  !ךדלי תא תאצמ",
                     "האיצי = CSE   |   בוש קחש = R"], GREEN)
            elif state == "lose":
                draw_overlay(
                    ["💀  !תספתנ  💀",
                     "...ךתוא לכא ןבנבה",
                     "האיצי = CSE   |   בוש קחש = R"], RED)

            if state == "play" and msg_timer > 0:
                draw_center_hint(msg_text)

        pygame.display.flip()


if __name__ == "__main__":
    main()
