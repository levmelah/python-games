"""
גן של בנבן 3D – Raycasting first-person horror game
W/A/S/D = תנועה    ←→ = סיבוב    עכבר = סיבוב    ESC = יציאה    R = שחק שוב
"""

import pygame, math, sys, random
pygame.init()

# ── Window & engine constants ─────────────────────────────────────────────────
W, H     = 960, 560
HALF_H   = H // 2
screen   = pygame.display.set_mode((W, H))
pygame.display.set_caption("🌸 גן של בנבן 3D 🌸")
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
GREEN  = ( 60, 200,  60)
BLUE   = ( 60, 120, 220)
YELLOW = (240, 220,  60)
ORANGE = (230, 130,  40)
PINK   = (240, 100, 180)
CYAN   = ( 60, 210, 210)
DARK   = ( 20,  15,  30)

CEIL_C  = (15, 8, 28)
FLOOR_C = (50, 40, 60)

# Wall type → RGB base colour
WCOL = {
    1: (110, 75, 145),   # purple (main)
    2: ( 70, 105, 160),  # blue (inner rooms)
    3: (160,  90,  45),  # brown (locked door)
    4: ( 45, 140,  45),  # green (open door – passable)
    5: (160,  65,  65),  # red (accent)
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

def mk_banban():
    s = _surf(); sz = SZ; c = sz // 2
    # body
    pygame.draw.ellipse(s, (60,130,230), (c-sz//5, c, sz*2//5, sz//3))
    # head
    pygame.draw.circle(s, (75, 145, 245), (c, c - sz//8), sz // 4)
    # beak
    bx = c + sz//4
    pygame.draw.polygon(s, YELLOW, [(bx, c-sz//8), (bx+18, c-sz//8-5), (bx+18, c-sz//8+5)])
    # eyes
    for ex in [-sz//10, sz//10]:
        pygame.draw.circle(s, WHITE, (c+ex, c-sz//6), 7)
        pygame.draw.circle(s, BLACK, (c+ex+2, c-sz//6+1), 3)
    # wings
    pygame.draw.ellipse(s, (40,110,210), (c-sz//2, c+sz//8, sz//3, sz//5))
    pygame.draw.ellipse(s, (40,110,210), (c+sz//6, c+sz//8, sz//3, sz//5))
    return s

def mk_opila():
    s = _surf(); sz = SZ; c = sz // 2
    # body
    pygame.draw.ellipse(s, (230,200,50), (c-sz//4, c-sz//8, sz//2, sz//2))
    # head
    pygame.draw.circle(s, (240,210,55), (c, c-sz//4), sz//4)
    # crest
    for i in range(5):
        pygame.draw.circle(s, ORANGE, (c-8+i*4, c-sz//2+i*2), 5)
    # big beak
    pygame.draw.polygon(s, ORANGE, [(c-10,c-sz//8+4),(c+10,c-sz//8+4),(c,c-sz//8+22)])
    # scary eyes
    for ex in [-sz//10, sz//10]:
        pygame.draw.circle(s, RED,   (c+ex, c-sz//4-4), 9)
        pygame.draw.circle(s, BLACK, (c+ex, c-sz//4-4), 4)
        # white highlight
        pygame.draw.circle(s, WHITE, (c+ex+2, c-sz//4-6), 2)
    # legs
    pygame.draw.line(s, ORANGE, (c-8, sz-16), (c-14, sz-2), 4)
    pygame.draw.line(s, ORANGE, (c+8, sz-16), (c+14, sz-2), 4)
    return s

def mk_banbaleena():
    s = _surf(); sz = SZ; c = sz // 2
    # dress
    pts = [(sz//5, sz//3),(4*sz//5, sz//3),(sz*7//8, sz-4),(sz//8, sz-4)]
    pygame.draw.polygon(s, PINK, pts)
    pygame.draw.polygon(s, (200,60,140), pts, 3)
    # upper body
    pygame.draw.ellipse(s, (255,155,205), (c-sz//7, c-sz//5, sz*2//7, sz//4))
    # head
    pygame.draw.circle(s, (255,185,215), (c, c-sz//3), sz//5)
    # big bow
    pygame.draw.polygon(s, RED, [(c-14, sz//7),(c, sz//7+10),(c+14, sz//7)])
    pygame.draw.polygon(s, RED, [(c-14, sz//7),(c,sz//7-2),(c-4,sz//7+12)])
    pygame.draw.polygon(s, RED, [(c+14, sz//7),(c,sz//7-2),(c+4,sz//7+12)])
    # eyes with lashes
    for ex in [-sz//12, sz//12]:
        pygame.draw.circle(s, BLACK, (c+ex, c-sz//3-2), 4)
        pygame.draw.circle(s, WHITE, (c+ex+1, c-sz//3-3), 1)
    # smile
    pygame.draw.arc(s, (150,0,80), (c-8, c-sz//3+4, 16, 8), math.pi, 2*math.pi, 2)
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

SURFS = {
    "banban":     mk_banban(),
    "opila":      mk_opila(),
    "banbaleena": mk_banbaleena(),
    "key":        mk_key(),
    "note":       mk_note(),
    "exit":       mk_exit(),
}

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

        shade = max(0.12, 1.0 - perp / (TILE * 13))
        if side == 1: shade *= 0.62
        bc = WCOL.get(wtype, (110,75,145))
        c2 = (max(0,min(255,int(bc[0]*shade))),
              max(0,min(255,int(bc[1]*shade))),
              max(0,min(255,int(bc[2]*shade))))
        strips.append((col, top, bot, c2))
        ray_ang += da

    return z_buf, strips

# ── Scene drawing ─────────────────────────────────────────────────────────────
def draw_scene(player, monsters, items, z_buf, strips, tick):
    # Ceiling & floor with gradient
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

        surf  = SURFS.get(skind, SURFS["banban"])
        sw, sh = max(1,spr_w), max(1,spr_h)
        scaled = pygame.transform.scale(surf, (sw, sh))
        left   = scr_x - sw // 2

        # Distance fog
        fog = max(0, min(180, int(perp / (TILE * 10) * 180)))

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
                fc = WCOL.get(v, (55,45,68)) if v else (55,45,68)
                pygame.draw.rect(mm, fc, (c*tsz, r*tsz, tsz-1, tsz-1))

    SCOLORS = {"banban":BLUE,"opila":YELLOW,"banbaleena":PINK,
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


def draw_hud(player):
    # Hearts
    for i in range(3):
        c = RED if i < player.health else (55,25,25)
        cx, cy = 22+i*36, 26
        pygame.draw.circle(screen, c, (cx,cy), 13)
        pygame.draw.circle(screen, WHITE, (cx,cy), 13, 2)

    # Key icon
    if player.has_key:
        km = fnt_sm.render("🔑 יש מפתח!", True, YELLOW)
        screen.blit(km, (125, 14))

    # Notes count
    nm = fnt_sm.render(f"📝 {player.notes}", True, YELLOW)
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
    hint = fnt_sm.render("W/A/S/D = תנועה  |  ← → / עכבר = סיבוב  |  ESC = יציאה", True, (90,90,115))
    screen.blit(hint, (W//2 - hint.get_width()//2, H - 20))


def draw_damage_flash(alpha):
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((200, 0, 0, int(alpha)))
    screen.blit(ov, (0, 0))


NOTE_TEXTS = [
    ["יומן: ילדי אבד בגן...", "חייב למצוא אותו!"],
    ["אזהרה: הפסלים חיים!", "ברח לפני שהם יתעוררו!"],
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
    cont = fnt_sm.render("לחץ כל מקש להמשך...", True, (100,80,30))
    screen.blit(cont, (card.centerx - cont.get_width()//2, card.bottom-28))


def draw_overlay(lines, col):
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 185))
    screen.blit(ov, (0, 0))
    for i, line in enumerate(lines):
        f  = fnt_big if i == 0 else fnt_med
        t  = f.render(line, True, col)
        screen.blit(t, (W//2 - t.get_width()//2, H//2 - 70 + i*54))


# ── Title screen ──────────────────────────────────────────────────────────────
def draw_title():
    screen.fill(DARK)
    # Animated creepy background lines
    for i in range(0, H, 20):
        v = int(10 + 15 * abs(math.sin(i*0.05 + pygame.time.get_ticks()*0.001)))
        pygame.draw.line(screen, (v, 0, v*2), (0,i),(W,i))

    title = fnt_big.render("🌸 גן של בנבן 3D 🌸", True, PINK)
    sub   = fnt_med.render("משחק אימה תלת-ממדי", True, (180,140,220))
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
            (SURFS["banban"],     "בנבן"),
            (SURFS["opila"],      "אופילה"),
            (SURFS["banbaleena"], "בנבאלינה"),
    ]):
        scaled = pygame.transform.scale(surf, (90,90))
        x0 = W//4*(i+1) - 45
        screen.blit(scaled, (x0, y0))
        lbl = fnt_sm.render(label, True, GRAY)
        screen.blit(lbl, (x0+45 - lbl.get_width()//2, y0+94))


# ── Main ──────────────────────────────────────────────────────────────────────
def build():
    global MAP
    MAP = [row[:] for row in _M]
    p = Player()
    monsters = [
        Monster("banban",      5.5*TILE,  2.5*TILE, hp=1, spd=65,  sight=280),
        Monster("opila",      14.5*TILE,  5.5*TILE, hp=2, spd=48,  sight=360),
        Monster("banbaleena", 12.5*TILE, 12.5*TILE, hp=1, spd=82,  sight=250),
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

            if ev.type == pygame.MOUSEMOTION and state == "play":
                player.angle += ev.rel[0] * 0.003
                player.angle %= 2 * math.pi

        # ── Update ────────────────────────────────────────────────────────────
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

            # Monsters – movement + attack
            for m in monsters:
                if not m.active: continue
                m.update(player, dt)
                if math.hypot(m.x - player.x, m.y - player.y) < 30:
                    if player.hit():
                        flash = 220
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

        # ── Render ────────────────────────────────────────────────────────────
        if state == "title":
            draw_title()
        else:
            z_buf, strips = raycast(player)
            draw_scene(player, monsters, items, z_buf, strips, tick)
            draw_hud(player)
            draw_minimap(player, monsters, items)

            if flash > 0:
                draw_damage_flash(flash)

            if state == "note":
                draw_note_card(note_text)
            elif state == "win":
                draw_overlay(
                    ["🎉  ניצחת!  🎉",
                     f"מצאת את ילדך!  ניקוד: {player.score}",
                     "R = שחק שוב   |   ESC = יציאה"], GREEN)
            elif state == "lose":
                draw_overlay(
                    ["💀  נתפסת!  💀",
                     "הבנבן אכל אותך...",
                     "R = שחק שוב   |   ESC = יציאה"], RED)

        pygame.display.flip()


if __name__ == "__main__":
    main()
