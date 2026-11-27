"""
פופי פליי טיים 3D – Raycasting first-person horror game (גרסה מבהילה)
W/A/S/D = תנועה    ←→ = סיבוב    עכבר = סיבוב    ESC = יציאה    R = שחק שוב
"""

import pygame, math, sys, random
pygame.init()

# ── Window & engine constants ─────────────────────────────────────────────────
W, H     = 960, 560
HALF_H   = H // 2
display  = pygame.display.set_mode((W, H))          # real window
screen   = pygame.Surface((W, H))                    # render buffer (for shake fx)
pygame.display.set_caption("🧸 פופי פליי טיים 3D 🧸")
clock    = pygame.time.Clock()

FOV       = math.pi / 3          # 60°
HALF_FOV  = FOV / 2
PROJ_DIST = (W / 2) / math.tan(HALF_FOV)   # projection plane distance
TILE      = 64
MOVE_SPD  = 130    # world-units / sec
ROT_SPD   = 1.8    # rad / sec

# ── Fonts ─────────────────────────────────────────────────────────────────────
try:
    fnt_big = pygame.font.SysFont("arial", 46, bold=True)
    fnt_med = pygame.font.SysFont("arial", 28, bold=True)
    fnt_sm  = pygame.font.SysFont("arial", 18)
except Exception:
    fnt_big = pygame.font.Font(None, 52)
    fnt_med = pygame.font.Font(None, 34)
    fnt_sm  = pygame.font.Font(None, 22)

# ── Colors ────────────────────────────────────────────────────────────────────
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
GRAY   = (150, 150, 150)
RED    = (220,  60,  60)
BLOOD  = (150,   0,   0)
GREEN  = ( 60, 200,  60)
BLUE   = ( 40,  90, 200)
YELLOW = (240, 220,  60)
ORANGE = (230, 130,  40)
PINK   = (230,  70, 140)
CYAN   = ( 60, 210, 210)
DARK   = (  8,   8,  12)

CEIL_C  = ( 5,  5,  7)
FLOOR_C = (18, 15, 13)

# Wall type → RGB base colour (abandoned toy-factory palette)
WCOL = {
    1: ( 45,  58,  62),   # dull teal steel (main)
    2: ( 78,  60,  30),   # rusty brown (inner rooms)
    3: (150,  25,  25),   # red (locked door)
    4: ( 40, 120,  40),   # green (open door – passable)
    5: (200, 140,  20),   # caution yellow/orange (accent)
}

# ── Map ───────────────────────────────────────────────────────────────────────
# 0=floor  1=main wall  2=inner wall  3=locked door  4=open door  5=accent wall
_M = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,2,2,2,0,0,0,1,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,2,0,2,0,0,0,3,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,2,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,2,2,2,0,0,0,1,0,0,0,1,1,1,1,1,5,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,1],
    [1,1,1,1,3,1,1,0,1,1,1,0,0,1,0,0,1,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,1,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]
MAP  = [row[:] for row in _M]   # mutable copy (doors change state)
MH   = len(MAP)
MW   = len(MAP[0])

def tile_at(mx, my):
    if mx < 0 or my < 0 or mx >= MW or my >= MH:
        return 1
    return MAP[my][mx]

def solid(mx, my):
    v = tile_at(mx, my)
    return v not in (0, 4)   # open door (4) is passable

# ── Sprite surface generators ─────────────────────────────────────────────────
SZ = 128   # atlas size for each sprite

def _surf(sz=SZ):
    return pygame.Surface((sz, sz), pygame.SRCALPHA)

def mk_huggy():
    s = _surf(); sz = SZ; c = sz // 2
    # long dangling arms
    pygame.draw.line(s, (20,40,150), (c-sz//3, c-10), (c-sz//2-8, sz-10), 10)
    pygame.draw.line(s, (20,40,150), (c+sz//3, c-10), (c+sz//2+8, sz-10), 10)
    pygame.draw.circle(s, (25,45,160), (c-sz//2-8, sz-10), 9)
    pygame.draw.circle(s, (25,45,160), (c+sz//2+8, sz-10), 9)
    # claw blood stains
    pygame.draw.circle(s, BLOOD, (c-sz//2-8, sz-10), 4)
    pygame.draw.circle(s, BLOOD, (c+sz//2+8, sz-10), 4)
    # body
    pygame.draw.ellipse(s, (30,55,180), (c-sz//4, c-4, sz//2, sz//2))
    pygame.draw.ellipse(s, BLOOD, (c-10, c+8, 18, 10))  # blood smear on chest
    # head
    pygame.draw.circle(s, (35,65,200), (c, c-sz//5), sz//3)
    # huge grin with teeth
    mouth = pygame.Rect(c-sz//4, c-sz//5+4, sz//2, sz//5)
    pygame.draw.arc(s, (110,5,5), mouth, math.pi*1.05, math.pi*1.95, 8)
    for i in range(6):
        tx = c - sz//5 + i * (sz*2//5)//5
        pygame.draw.polygon(s, WHITE, [(tx, c-sz//5+10),(tx+6, c-sz//5+10),(tx+3, c-sz//5+20)])
        if i % 2 == 0:
            pygame.draw.line(s, BLOOD, (tx+3, c-sz//5+20), (tx+3, c-sz//5+30), 2)
    # big round bloodshot eyes
    for ex in [-sz//8, sz//8]:
        pygame.draw.circle(s, YELLOW, (c+ex, c-sz//4), 11)
        pygame.draw.circle(s, BLACK,  (c+ex, c-sz//4), 5)
        pygame.draw.line(s, BLOOD, (c+ex-9, c-sz//4-6), (c+ex-3, c-sz//4-1), 1)
    return s

def mk_mommy():
    s = _surf(); sz = SZ; c = sz // 2
    # long spindly legs
    for i, dx in enumerate([-1, -0.5, 0.5, 1]):
        lx = c + int(dx * sz//2.2)
        pygame.draw.line(s, (170,20,70), (c, c+sz//6), (lx, sz-6), 6)
    # body / dress
    pygame.draw.polygon(s, (220,40,110),
        [(c-sz//6, c-sz//8),(c+sz//6, c-sz//8),(c+sz//5, c+sz//6),(c-sz//5, c+sz//6)])
    pygame.draw.ellipse(s, BLOOD, (c-8, c, 16, 8))
    # head
    pygame.draw.circle(s, (250,205,190), (c, c-sz//3), sz//5)
    # blonde ponytail
    pygame.draw.polygon(s, (235,210,60), [(c+sz//6, c-sz//3-6),(c+sz//3, c-sz//5),(c+sz//5, c-sz//8)])
    # eyes (wide, unsettling, bloodshot)
    for ex in [-sz//12, sz//12]:
        pygame.draw.circle(s, WHITE, (c+ex, c-sz//3-2), 6)
        pygame.draw.circle(s, BLACK, (c+ex, c-sz//3-2), 3)
        pygame.draw.line(s, BLOOD, (c+ex-5, c-sz//3-6), (c+ex-1, c-sz//3-2), 1)
    # red smile too wide, dripping
    pygame.draw.arc(s, (150,5,20), (c-16, c-sz//3+2, 32, 16), math.pi, 2*math.pi, 3)
    for dx in (-10, 0, 10):
        pygame.draw.line(s, BLOOD, (c+dx, c-sz//3+16), (c+dx, c-sz//3+16+random.randint(4,12)), 2)
    return s

def mk_bunzo():
    s = _surf(); sz = SZ; c = sz // 2
    # ears
    pygame.draw.ellipse(s, (235,140,30), (c-sz//4-6, sz//8, 16, sz//2))
    pygame.draw.ellipse(s, (235,140,30), (c+sz//4-10, sz//8, 16, sz//2))
    pygame.draw.line(s, BLOOD, (c-sz//4+2, sz//8+8), (c-sz//4+2, sz//8+22), 2)
    # body
    pygame.draw.ellipse(s, (245,150,35), (c-sz//4, c-4, sz//2, sz//2))
    # head
    pygame.draw.circle(s, (250,160,40), (c, c-sz//6), sz//4)
    # cymbals
    pygame.draw.circle(s, (200,170,60), (c-sz//2-6, c+sz//6), 16)
    pygame.draw.circle(s, (200,170,60), (c+sz//2+6, c+sz//6), 16)
    # eyes
    for ex in [-sz//10, sz//10]:
        pygame.draw.circle(s, BLACK, (c+ex, c-sz//6), 6)
        pygame.draw.circle(s, RED,   (c+ex, c-sz//6), 3)
    # teeth grin dripping blood
    pygame.draw.polygon(s, WHITE, [(c-14, c+2),(c+14, c+2),(c, c+16)])
    pygame.draw.line(s, BLOOD, (c-6, c+10), (c-6, c+20), 2)
    pygame.draw.line(s, BLOOD, (c+6, c+10), (c+6, c+22), 2)
    return s

def mk_key():
    s = _surf(64); sz = 64; c = sz//2
    pygame.draw.rect(s, (235, 40, 40), (c-18, sz//3-14, 36, 26), border_radius=4)
    pygame.draw.rect(s, WHITE, (c-18, sz//3-14, 36, 26), 2, border_radius=4)
    pygame.draw.circle(s, YELLOW, (c, sz//3-2), 6)
    for i in range(3):
        pygame.draw.line(s, WHITE, (c-14, sz//3+6+i*4), (c+2, sz//3+6+i*4), 2)
    return s

def mk_note():
    # VHS tape
    s = _surf(64); sz = 64; c = sz//2
    pygame.draw.rect(s, (25,25,30), (c-18, sz//3-6, 36, 22), border_radius=3)
    pygame.draw.circle(s, (10,10,12), (c-9, sz//3+5), 6)
    pygame.draw.circle(s, (10,10,12), (c+9, sz//3+5), 6)
    pygame.draw.rect(s, (240,230,180), (c-15, sz//3-3, 30, 8))
    return s

def mk_exit():
    s = _surf(64); sz = 64; c = sz//2
    pygame.draw.rect(s, (0, 210, 0), (sz//5, sz//8, 3*sz//5, 3*sz//4), border_radius=6)
    pygame.draw.polygon(s, WHITE, [(c, sz//5),(3*sz//4,c),(c,4*sz//5)])
    pygame.draw.polygon(s, WHITE, [(c, sz//5),(sz//4,c),(c,4*sz//5)])
    t = fnt_sm.render("EXIT", True, WHITE)
    s.blit(t, (c-t.get_width()//2, c-t.get_height()//2))
    return s

SURFS = {
    "huggy": mk_huggy(),
    "mommy": mk_mommy(),
    "bunzo": mk_bunzo(),
    "key":   mk_key(),
    "note":  mk_note(),
    "exit":  mk_exit(),
}

# ── Atmosphere: vignette + blood overlay ───────────────────────────────────────
def _make_vignette(tint):
    small = pygame.Surface((120, 70), pygame.SRCALPHA)
    cx, cy = 60, 35
    maxd = math.hypot(cx, cy)
    for y in range(70):
        for x in range(120):
            d = math.hypot(x - cx, y - cy) / maxd
            a = int(max(0, min(255, (d - 0.32) / 0.68 * 235)))
            small.set_at((x, y), (tint[0], tint[1], tint[2], a))
    return pygame.transform.smoothscale(small, (W, H))

VIGNETTE     = _make_vignette((0, 0, 0))
RED_VIGNETTE = _make_vignette((140, 0, 0))

blood_layer = pygame.Surface((W, H), pygame.SRCALPHA)

def add_blood_splat(layer, cx, cy, big=False):
    n = random.randint(8, 14) if big else random.randint(4, 7)
    for _ in range(n):
        spread = 60 if big else 25
        ox = cx + random.randint(-spread, spread)
        oy = cy + random.randint(-spread, spread)
        r  = random.randint(8, 22) if big else random.randint(3, 10)
        col = (random.randint(110, 170), 0, 0, random.randint(150, 225))
        pygame.draw.circle(layer, col, (ox, oy), r)
        if random.random() < 0.65:
            dl = random.randint(10, 45)
            pygame.draw.line(layer, (120, 0, 0, 190), (ox, oy),
                              (ox + random.randint(-4, 4), oy + dl), random.randint(2, 5))

def spawn_hit_blood(layer, big=False):
    for _ in range(3 if not big else 5):
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":     cx, cy = random.randint(0, W), random.randint(0, 40)
        elif side == "bottom":cx, cy = random.randint(0, W), random.randint(H - 60, H)
        elif side == "left":  cx, cy = random.randint(0, 40), random.randint(0, H)
        else:                 cx, cy = random.randint(W - 40, W), random.randint(0, H)
        add_blood_splat(layer, cx, cy, big=big or random.random() < 0.3)

def draw_drip_text(text, font, color, x, y, tick, ndrips=8):
    rendered = font.render(text, True, color)
    screen.blit(rendered, (x, y))
    rw, rh = rendered.get_size()
    for i in range(ndrips):
        dx = x + int(rw * (i + 0.5) / ndrips)
        base_len = 10 + (i * 7) % 25
        length = base_len + int(15 * abs(math.sin(tick * 0.04 + i * 1.3)))
        pygame.draw.line(screen, BLOOD, (dx, y + rh - 4), (dx, y + rh - 4 + length), 3)
        pygame.draw.circle(screen, BLOOD, (dx, y + rh - 4 + length), 3)

# ── Player ────────────────────────────────────────────────────────────────────
class Player:
    def __init__(self):
        self.x = 1.5 * TILE
        self.y = 1.5 * TILE
        self.angle     = 0.0
        self.health    = 3
        self.has_key   = False
        self.notes     = 0
        self.score     = 0
        self.invincible = 0.0

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

    def hit(self):
        if self.invincible <= 0:
            self.health -= 1
            self.invincible = 1.5
            return True
        return False

# ── Monster ───────────────────────────────────────────────────────────────────
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

        if dist < self.sight:
            self.state = "chase"
        elif dist > self.sight * 1.6:
            self.state = "wander"

        if self.state == "chase":
            if dist > 1:
                nx = self.x + (dx/dist) * self.spd * dt
                ny = self.y + (dy/dist) * self.spd * dt
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

# ── Item ──────────────────────────────────────────────────────────────────────
class Item:
    def __init__(self, kind, x, y):
        self.kind   = kind
        self.x      = float(x)
        self.y      = float(y)
        self.active = True
        self.anim   = random.randint(0, 200)

# ── Raycasting ────────────────────────────────────────────────────────────────
def raycast(player):
    """DDA raycasting – returns (z_buffer, strip_list).
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
        for _ in range(30):
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

        shade = max(0.10, 1.0 - perp / (TILE * 12))
        if side == 1: shade *= 0.60
        bc = WCOL.get(wtype, (45,58,62))
        c2 = (max(0,min(255,int(bc[0]*shade))),
              max(0,min(255,int(bc[1]*shade))),
              max(0,min(255,int(bc[2]*shade))))
        strips.append((col, top, bot, c2))
        ray_ang += da

    return z_buf, strips

# ── Scene drawing ─────────────────────────────────────────────────────────────
def draw_scene(player, monsters, items, z_buf, strips, tick):
    # Ceiling & floor
    screen.fill(CEIL_C)
    pygame.draw.rect(screen, FLOOR_C, (0, HALF_H, W, HALF_H))

    # Floor gradient (cheap – overdraw lower half)
    for row in range(0, HALF_H, 4):
        t = row / HALF_H
        r2 = int(FLOOR_C[0] + (CEIL_C[0]-FLOOR_C[0]) * t * 0.3)
        g2 = int(FLOOR_C[1] + (CEIL_C[1]-FLOOR_C[1]) * t * 0.3)
        b2 = int(FLOOR_C[2] + (CEIL_C[2]-FLOOR_C[2]) * t * 0.3)
        pygame.draw.line(screen, (r2,g2,b2), (0, HALF_H+row), (W, HALF_H+row))

    # Walls
    for col, top, bot, c2 in strips:
        pygame.draw.line(screen, c2, (col, top), (col, bot))

    # ── Sprites ───────────────────────────────────────────────────────────────
    all_spr = []
    for m in monsters:
        if m.active:
            m.anim += 1
            all_spr.append((m.x, m.y, m.kind, True,  m.stun > 0, m.anim))
    for it in items:
        if it.active:
            it.anim += 1
            all_spr.append((it.x, it.y, it.kind, False, False,     it.anim))

    # Sort far → near (painter's order)
    all_spr.sort(key=lambda s: (s[0]-player.x)**2 + (s[1]-player.y)**2, reverse=True)

    for sx, sy, skind, is_monster, stunned, sanim in all_spr:
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
        spr_w = spr_h
        if spr_h < 2: continue

        scr_x = int(W / 2 + rel / HALF_FOV * (W / 2))
        scr_y = HALF_H - spr_h // 2

        # Bob for items
        if not is_monster:
            scr_y += int(math.sin(sanim * 0.07) * 5)

        surf  = SURFS.get(skind, SURFS["huggy"])
        sw, sh = max(1,spr_w), max(1,spr_h)
        scaled = pygame.transform.scale(surf, (sw, sh))
        left   = scr_x - sw // 2

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
                fc = WCOL.get(v, (30,28,26)) if v else (30,28,26)
                pygame.draw.rect(mm, fc, (c*tsz, r*tsz, tsz-1, tsz-1))

    SCOLORS = {"huggy":BLUE,"mommy":PINK,"bunzo":ORANGE,
               "key":RED,"note":(200,200,100),"exit":GREEN}
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


def draw_hud(player):
    # Hearts (dripping blood when low)
    for i in range(3):
        c = RED if i < player.health else (40,15,15)
        cx, cy = 22+i*36, 26
        pygame.draw.circle(screen, c, (cx,cy), 13)
        pygame.draw.circle(screen, WHITE, (cx,cy), 13, 2)
        if i < player.health and player.health == 1:
            pygame.draw.line(screen, BLOOD, (cx, cy+11), (cx, cy+11+6), 2)

    # Key icon
    if player.has_key:
        km = fnt_sm.render("🔑 יש כרטיס גישה!", True, YELLOW)
        screen.blit(km, (125, 14))

    # Tapes count
    nm = fnt_sm.render(f"📼 {player.notes}", True, YELLOW)
    screen.blit(nm, (12, 50))

    # Score
    sc = fnt_sm.render(f"ניקוד: {player.score}", True, WHITE)
    screen.blit(sc, (W - sc.get_width() - 10, 8))

    # Crosshair
    cx, cy = W//2, HALF_H
    pygame.draw.line(screen, (200,200,200), (cx-14,cy),   (cx-4,cy),   1)
    pygame.draw.line(screen, (200,200,200), (cx+4, cy),   (cx+14,cy),  1)
    pygame.draw.line(screen, (200,200,200), (cx,   cy-14),(cx,  cy-4), 1)
    pygame.draw.line(screen, (200,200,200), (cx,   cy+4), (cx,  cy+14),1)
    pygame.draw.circle(screen, (200,200,200), (cx,cy), 2)

    # Controls bar
    hint = fnt_sm.render("W/A/S/D = תנועה  |  ← → / עכבר = סיבוב  |  ESC = יציאה", True, (90,80,80))
    screen.blit(hint, (W//2 - hint.get_width()//2, H - 20))


def draw_atmosphere(tick, flicker_val, player):
    screen.blit(VIGNETTE, (0, 0))
    if flicker_val > 1:
        ov = pygame.Surface((W, H))
        ov.fill((0, 0, 0))
        ov.set_alpha(int(flicker_val))
        screen.blit(ov, (0, 0))
    if player.health <= 1:
        pulse = int(abs(math.sin(tick * 0.15)) * 110)
        RED_VIGNETTE.set_alpha(pulse)
        screen.blit(RED_VIGNETTE, (0, 0))
    screen.blit(blood_layer, (0, 0))


def draw_damage_flash(alpha):
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((200, 0, 0, int(alpha)))
    screen.blit(ov, (0, 0))


def draw_jumpscare(kind, t, dur, tick):
    prog = 1 - max(0.0, t) / dur
    strobe = (200, 0, 0) if (tick // 2) % 2 == 0 else (10, 0, 0)
    ov = pygame.Surface((W, H))
    ov.fill(strobe)
    ov.set_alpha(110)
    screen.blit(ov, (0, 0))

    surf = SURFS.get(kind, SURFS["huggy"])
    size = int(W * (0.75 + 0.25 * prog) + math.sin(tick * 0.9) * 16)
    size = max(40, size)
    scaled = pygame.transform.scale(surf, (size, size))
    jitter = 20
    jx = W//2 - size//2 + random.randint(-jitter, jitter)
    jy = H//2 - size//2 + random.randint(-jitter, jitter)
    screen.blit(scaled, (jx, jy))

    msg = random.choice(["!!!", "תברח!!!", "הוא כאן!!!", "תפסתי אותך!!!"])
    t2 = fnt_big.render(msg, True, (255, 30, 30))
    tx = W//2 - t2.get_width()//2 + random.randint(-8, 8)
    ty = H//2 - t2.get_height()//2 + random.randint(-8, 8)
    screen.blit(t2, (tx, ty))


NOTE_TEXTS = [
    ["יומן עובד: הניסויים יצאו משליטה...", "אל תסתכל להאגי בעיניים!"],
    ["אזהרה: מפעל הצעצועים ננטש", "אבל משהו עדיין מסתובב כאן..."],
]


def draw_note_card(lines):
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 165))
    screen.blit(ov, (0, 0))
    card = pygame.Rect(W//2-240, H//2-110, 480, 220)
    pygame.draw.rect(screen, (215,205,190), card, border_radius=14)
    pygame.draw.rect(screen, (60,55,40),  card, 3, border_radius=14)
    for i, line in enumerate(lines):
        lt = fnt_med.render(line, True, DARK)
        screen.blit(lt, (card.centerx - lt.get_width()//2, card.y+30+i*44))
    cont = fnt_sm.render("לחץ כל מקש להמשך...", True, (60,55,40))
    screen.blit(cont, (card.centerx - cont.get_width()//2, card.bottom-28))


def draw_win_overlay(lines):
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 185))
    screen.blit(ov, (0, 0))
    for i, line in enumerate(lines):
        f  = fnt_big if i == 0 else fnt_med
        t  = f.render(line, True, GREEN)
        screen.blit(t, (W//2 - t.get_width()//2, H//2 - 70 + i*54))


def draw_death_screen(player, tick, last_kind):
    base = (30, 0, 0) if (tick // 6) % 2 == 0 else (6, 0, 0)
    screen.fill(base)

    surf = SURFS.get(last_kind, SURFS["huggy"])
    size = 360
    scaled = pygame.transform.scale(surf, (size, size))
    jx = W//2 - size//2 + random.randint(-5, 5)
    jy = 44 + random.randint(-5, 5)
    screen.blit(scaled, (jx, jy))

    screen.blit(blood_layer, (0, 0))
    for _ in range(2):
        add_blood_splat(blood_layer, random.randint(0, W), random.randint(0, H//2), big=True)

    draw_drip_text("מת.", fnt_big, (235, 20, 20), W//2 - 55, H - 175, tick, ndrips=6)
    sub = fnt_med.render(f"ניקוד: {player.score}", True, WHITE)
    screen.blit(sub, (W//2 - sub.get_width()//2, H - 95))
    hint = fnt_sm.render("R = שחק שוב   |   ESC = יציאה", True, (220, 170, 170))
    screen.blit(hint, (W//2 - hint.get_width()//2, H - 60))


# ── Title screen ──────────────────────────────────────────────────────────────
def draw_title():
    screen.fill(DARK)
    # Animated creepy background lines
    for i in range(0, H, 20):
        v = int(6 + 12 * abs(math.sin(i*0.05 + pygame.time.get_ticks()*0.001)))
        pygame.draw.line(screen, (v, v, v*2), (0,i),(W,i))

    title = fnt_big.render("🧸 פופי פליי טיים 3D 🧸", True, (230,60,120))
    sub   = fnt_med.render("משחק אימה במפעל הצעצועים הנטוש", True, (140,150,220))
    inst  = fnt_sm.render( "לחץ ENTER או רווח כדי להתחיל", True, WHITE)
    esc   = fnt_sm.render( "ESC = יציאה", True, GRAY)

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
            (SURFS["huggy"], "האגי וואגי"),
            (SURFS["mommy"], "מאמי לונג לגס"),
            (SURFS["bunzo"], "בונזו באני"),
    ]):
        scaled = pygame.transform.scale(surf, (90,90))
        x0 = W//4*(i+1) - 45
        screen.blit(scaled, (x0, y0))
        lbl = fnt_sm.render(label, True, GRAY)
        screen.blit(lbl, (x0+45 - lbl.get_width()//2, y0+94))

    screen.blit(VIGNETTE, (0, 0))


# ── Main ──────────────────────────────────────────────────────────────────────
def build():
    global MAP
    MAP = [row[:] for row in _M]
    blood_layer.fill((0, 0, 0, 0))
    p = Player()
    monsters = [
        Monster("huggy",  5.5*TILE,  2.5*TILE, hp=1, spd=78,  sight=330),
        Monster("mommy", 14.5*TILE,  5.5*TILE, hp=2, spd=55,  sight=420),
        Monster("bunzo", 12.5*TILE, 12.5*TILE, hp=1, spd=66,  sight=280),
    ]
    items = [
        Item("key",   15.5*TILE,  3.5*TILE),
        Item("note",   4.5*TILE,  8.5*TILE),
        Item("note",  15.5*TILE, 10.5*TILE),
        Item("exit",  17.5*TILE, 13.5*TILE),
    ]
    return p, monsters, items


def main():
    state = "title"
    player, monsters, items = build()
    note_text  = []
    flash      = 0.0
    tick       = 0
    flicker_val = 0.0
    hit_shake_t  = 0.0
    jumpscare_t  = 0.0
    jumpscare_kind = "huggy"
    JS_DUR = 0.5
    last_hit_kind = "huggy"

    pygame.mouse.set_visible(False)

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        tick += 1

        # ── Events ────────────────────────────────────────────────────────────
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
                    hit_shake_t = 0.0
                    jumpscare_t = 0.0

            if ev.type == pygame.MOUSEMOTION and state == "play":
                player.angle += ev.rel[0] * 0.003
                player.angle %= 2 * math.pi

        # ── Update ────────────────────────────────────────────────────────────
        # Flickering factory lights (random walk)
        flicker_val += random.uniform(-18, 18)
        flicker_val = max(0.0, min(70.0, flicker_val))
        if random.random() < 0.01:
            flicker_val = 150.0   # sudden bulb-dying spike

        ambient_mag = 0.0
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
            hit_shake_t = max(0.0, hit_shake_t - dt)
            jumpscare_t = max(0.0, jumpscare_t - dt)

            # Monsters – movement + attack
            for m in monsters:
                if not m.active: continue
                m.update(player, dt)
                d = math.hypot(m.x - player.x, m.y - player.y)
                if m.state == "chase" and d < 170:
                    ambient_mag = max(ambient_mag, (1 - d/170) * 7)
                if d < 30:
                    if player.hit():
                        flash = 220
                        hit_shake_t = 0.5
                        jumpscare_t = JS_DUR
                        jumpscare_kind = m.kind
                        last_hit_kind = m.kind
                        spawn_hit_blood(blood_layer, big=(player.health <= 0))
                        if player.health <= 0:
                            state = "lose"

            # Items – pickup
            for it in items:
                if not it.active: continue
                if math.hypot(it.x - player.x, it.y - player.y) < 44:
                    if it.kind == "key":
                        it.active = False
                        player.has_key = True
                        player.score  += 50
                    elif it.kind == "note":
                        it.active = False
                        idx = player.notes % len(NOTE_TEXTS)
                        note_text = NOTE_TEXTS[idx]
                        player.notes += 1
                        player.score += 30
                        state = "note"
                    elif it.kind == "exit":
                        state = "win"
                        player.score += 500

            # Unlock doors adjacent to player
            pc, pr = int(player.x // TILE), int(player.y // TILE)
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = pr+dr, pc+dc
                if 0 <= nr < MH and 0 <= nc < MW:
                    if MAP[nr][nc] == 3 and player.has_key:
                        MAP[nr][nc] = 4
                        player.has_key = False
                        player.score  += 100

        # ── Render (into buffer `screen`) ────────────────────────────────────
        if state == "title":
            draw_title()
        else:
            z_buf, strips = raycast(player)
            draw_scene(player, monsters, items, z_buf, strips, tick)
            draw_hud(player)
            draw_minimap(player, monsters, items)
            draw_atmosphere(tick, flicker_val, player)

            if flash > 0:
                draw_damage_flash(flash)
            if jumpscare_t > 0:
                draw_jumpscare(jumpscare_kind, jumpscare_t, JS_DUR, tick)

            if state == "note":
                draw_note_card(note_text)
            elif state == "win":
                draw_win_overlay(
                    ["🎉  ברחת מהמפעל!  🎉",
                     f"שרדת את האגי וחבריו!  ניקוד: {player.score}",
                     "R = שחק שוב   |   ESC = יציאה"])
            elif state == "lose":
                draw_death_screen(player, tick, last_hit_kind)

        # ── Composite buffer -> real window (with screen-shake) ─────────────
        total_mag = ambient_mag + 14 * (hit_shake_t / 0.5 if hit_shake_t > 0 else 0)
        if total_mag > 0.5:
            ox = random.randint(-int(total_mag), int(total_mag))
            oy = random.randint(-int(total_mag), int(total_mag))
        else:
            ox = oy = 0
        display.fill(BLACK)
        display.blit(screen, (ox, oy))
        pygame.display.flip()


if __name__ == "__main__":
    main()
