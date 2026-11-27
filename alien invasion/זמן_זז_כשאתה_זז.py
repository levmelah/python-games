"""
TIME MOVES ONLY WHEN YOU MOVE  -  CITY EDITION
-----------------------------------------------
Top-down city warfare. Shoot, fire rockets, blow up cars, collapse buildings...
but the whole world freezes in mid-air while you stand still.

Controls:
  WASD / Arrows  - move (time flows)
  Mouse          - aim
  Left click     - machine gun
  Right click    - rocket (explodes where you aim)
  Enter          - time grenade (thrown toward the mouse)
  T              - call in tanks
  B              - black hole (run!)
  Hold Shift     - energy shield (press it right before a hit to reflect the shot)
  F              - gravity gun: grab a car / enemy / piece of a building, F or click to throw
  Y              - tsunami
  U              - alien invasion
  N              - nuke
  R              - restart after death
  ESC            - quit

Install & run:
  pip install pygame
  python time_moves.py
"""
import math
import random
import pygame

# ====================== the avocado hero ======================
AVO_W, AVO_H = 60, 74     # drawing canvas (design units)
AVO_SCALE = 0.7           # how big the avocado is on screen (1.0 = 60x74 pixels)
SS = 4                    # supersampling: drawn 4x bigger then scaled down = smooth edges
OUTLINE = (22, 38, 20)
SKIN = (46, 128, 52)
SKIN_HI = (92, 176, 80)
FLESH = (190, 232, 104)
FLESH_HI = (226, 248, 160)
PIT = (128, 74, 38)
CAPE = (255, 112, 28)
CAPE_DARK = (196, 66, 16)


def render_avocado(pose, phase, blink, cape_i, scale=1.0):
    """Draws the avocado facing right. pose: idle / walk / fly / hurt; phase 0-7 drives the animation."""
    scale *= AVO_SCALE
    k = SS * scale
    cw, ch = int(AVO_W * k), int(AVO_H * k)
    s = pygame.Surface((cw, ch), pygame.SRCALPHA)
    ox, oy = cw / 2, ch - 3 * k

    def V(x, y):
        return (ox + x * k, oy + y * k)

    def circ(col, x, y, r, width=0):
        pygame.draw.circle(s, col, V(x, y), r * k, int(width * k) if width else 0)

    def line(col, a, b, wdt):
        pygame.draw.line(s, col, V(*a), V(*b), max(1, int(wdt * k)))
        pygame.draw.circle(s, col, V(*a), wdt * k / 2)
        pygame.draw.circle(s, col, V(*b), wdt * k / 2)

    def ellipse(col, x, y, w, h, width=0):
        pygame.draw.ellipse(s, col, (ox + (x - w / 2) * k, oy + (y - h / 2) * k, w * k, h * k),
                            int(width * k) if width else 0)

    ang = phase / 8 * math.tau
    walk = pose == "walk"
    fly = pose == "fly"
    breathe = math.sin(ang) * 0.6 if pose == "idle" else 0
    swing = math.sin(ang) * 0.55 if walk else 0

    # ---- cape (behind everything) ----
    cw_ = cape_i / 6 * math.tau
    trail = -5 if walk else (-8 if fly else -1)
    wave = [math.sin(cw_ + i * 1.3) * (2.2 if walk or fly else 1.0) for i in range(5)]
    cape = [(-9, -46), (9, -46),
            (17 + trail * 0.3, -7 + wave[0]), (8 + trail, -4 + wave[1]), (0 + trail, -6 + wave[2]),
            (-8 + trail, -4 + wave[3]), (-17 + trail * 0.3, -7 + wave[4])]
    pygame.draw.polygon(s, OUTLINE, [V(x, y) for x, y in cape], int(3 * k))
    pygame.draw.polygon(s, CAPE, [V(x, y) for x, y in cape])
    pygame.draw.polygon(s, CAPE_DARK, [V(x, y) for x, y in [cape[0], (-3, -45), cape[5], cape[6]]])

    # ---- legs & shoes ----
    for side, sgn in ((-1, 1), (1, -1)):
        a = swing * sgn
        if fly:
            a = side * 0.7 + math.sin(ang * 2 + side) * 0.3
        hip = (side * 4.5, -13)
        foot = (hip[0] + math.sin(a) * 11, hip[1] + math.cos(a) * 11)
        line(OUTLINE, hip, foot, 2.6)
        ellipse(OUTLINE, foot[0] + 1.8, foot[1] + 0.5, 9, 5.4)
        ellipse((235, 70, 70), foot[0] + 1.8, foot[1] - 0.1, 7, 3.6)           # red sneakers
        ellipse((255, 255, 255), foot[0] + 0.5, foot[1] + 1.2, 6, 1.4)

    # ---- back arm (waves when idle, swings when walking, flails when flying) ----
    sh = (-9, -34)
    if fly:
        hand = (-17 + math.sin(ang * 2) * 2, -49 + math.cos(ang * 2) * 2)
    elif walk:
        hand = (-10 - math.sin(ang) * 7, -28)
    elif pose == "hurt":
        hand = (-14, -27)
    else:
        hand = (-17, -45 + math.sin(ang * 2) * 2.5)                            # waving
    line(OUTLINE, sh, hand, 2.2)
    circ(OUTLINE, hand[0], hand[1], 3.6)
    circ((255, 255, 255), hand[0], hand[1], 2.7)
    circ((255, 255, 255), hand[0] + 1.8, hand[1] - 2.2, 1.2)                  # thumb

    # ---- body: pear shape = two circles + a bridge, with an outline ----
    top_y = -42 + breathe
    def pear(col, grow, dx=0.0):
        circ(col, dx, top_y, 11.2 + grow)
        circ(col, dx, -28, 14.8 + grow)
        pygame.draw.polygon(s, col, [V(dx - 11.2 - grow, top_y), V(dx + 11.2 + grow, top_y),
                                     V(dx + 14.8 + grow, -28), V(dx - 14.8 - grow, -28)])
    pear(OUTLINE, 1.7)
    pear(SKIN, 0)
    circ(SKIN_HI, -6, top_y - 3, 3.2)                                          # shine on the skin
    # flesh (shifted toward the front)
    circ(FLESH, 2, top_y + 0.5, 8.6)
    circ(FLESH, 2, -28, 12.2)
    pygame.draw.polygon(s, FLESH, [V(-6.6, top_y + 0.5), V(10.6, top_y + 0.5), V(14.2, -28), V(-10.2, -28)])
    circ(FLESH_HI, -1, top_y - 2, 3)
    # pit
    circ(OUTLINE, 3, -25, 6.6)
    circ(PIT, 3, -25, 5.8)
    ellipse((186, 124, 76), 1.2, -27.2, 4, 2.6)

    # ---- face ----
    ex = (0.5, 6.5)
    ey = top_y - 1
    look = 1.0 if not fly else 0
    if pose == "hurt":
        for x, d in ((ex[0], 1), (ex[1], -1)):   # squeezed ">  <" eyes
            line(OUTLINE, (x - 1.6 * d, ey - 1.8), (x + 1.4 * d, ey), 1.1)
            line(OUTLINE, (x + 1.4 * d, ey), (x - 1.6 * d, ey + 1.8), 1.1)
    elif blink and not fly:
        for x in ex:
            line((14, 14, 18), (x - 2.2, ey + 0.5), (x + 2.2, ey + 0.5), 1.4)
    else:
        size = 1.25 if fly else 1.0
        for x in ex:   # big black oval eyes with a white shine, like the original drawing
            ellipse((14, 14, 18), x, ey, 4.6 * size, 7.4 * size)
            ellipse((255, 255, 255), x + 0.9 * look + 0.3, ey - 1.9 * size, 1.7 * size, 2.4 * size)
            circ((255, 255, 255), x - 0.9, ey + 2.0 * size, 0.45)
    my = top_y + 5.2
    if fly:
        ellipse(OUTLINE, 3.6, my + 0.6, 3.4, 4)
        ellipse((150, 40, 50), 3.6, my + 1, 2.2, 2.4)
    elif pose == "hurt":
        pygame.draw.arc(s, OUTLINE, (ox + 0.6 * k, oy + (my + 0.8) * k, 6 * k, 4 * k), 0.3, math.pi - 0.3, int(1.1 * k))
    else:
        pygame.draw.arc(s, OUTLINE, (ox + 0.4 * k, oy + (my - 3) * k, 6.4 * k, 4.6 * k), math.pi + 0.3, math.tau - 0.3, int(1.1 * k))
    blush = pygame.Surface((int(4 * k), int(2.4 * k)), pygame.SRCALPHA)
    pygame.draw.ellipse(blush, (255, 120, 130, 110), blush.get_rect())
    for x in (-2.6, 9.6):
        s.blit(blush, V(x - 2, my - 2.4))

    return pygame.transform.smoothscale(s, (int(AVO_W * scale), int(AVO_H * scale)))


class AvocadoSprites:
    """Lazily renders and caches every animation frame (and its mirror image)."""

    def __init__(self):
        self.cache = {}

    def get(self, pose, phase, blink, cape_i, facing, scale=1.0):
        key = (pose, phase, blink, cape_i, scale)
        img = self.cache.get(key)
        if img is None:
            img = render_avocado(pose, phase, blink, cape_i, scale)
            self.cache[key] = img
        if facing < 0:
            fk = key + ("flip",)
            f = self.cache.get(fk)
            if f is None:
                f = pygame.transform.flip(img, True, False)
                self.cache[fk] = f
            return f
        return img

W, H = 1024, 704
FPS = 60
CAM = pygame.Vector2(W / 2, H / 2)
PERSP = 0.0006          # perspective: tall things lean away from the screen center
TILT = 0.48             # camera tilt: tall things are drawn higher on screen (you see the walls)
SUN = pygame.Vector2(0.55, 0.32)   # shadow direction/length per unit of height
GRAVITY = 900

PLAYER_SPEED = 230
UNIT_R = 11
BULLET_SPEED = 800
ENEMY_BULLET_SPEED = 270
ROCKET_SPEED = 430
ENEMY_ROCKET_SPEED = 220
GUN_CD = 0.28
ROCKET_CD = 1.1
FROZEN_SCALE = 0.02
SHOT_BURST = 0.12
MAX_PARTICLES = 1100

ROADS_V = [200, 512, 824]
ROADS_H = [190, 500]
ROAD_HALF = 34
SIDEWALK = 12

ASPHALT = (28, 30, 38)
SIDEWALK_COL = (58, 60, 70)
LOT = (40, 42, 50)
PARK = (30, 58, 40)
ROOFS = [(96, 102, 120), (118, 106, 96), (82, 96, 110), (124, 120, 112), (74, 82, 100), (104, 92, 104)]
CAR_COLS = [(200, 50, 50), (230, 190, 60), (60, 120, 210), (220, 220, 225), (50, 50, 60), (60, 170, 110), (240, 130, 40)]
CYAN = (90, 230, 255)
PLAYER_COL = (235, 250, 255)
ENEMY_COL = (255, 60, 90)
BULLET_ENEMY = (255, 150, 70)
TEXT = (225, 235, 255)
DIM = (120, 135, 170)
SMOKE = (60, 60, 66)
DUST = (120, 110, 96)


# ====================== helpers ======================
def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def scale_color(c, k):
    return tuple(max(0, min(255, int(ch * k))) for ch in c)


def proj(pos, z):
    """Screen position of a world point at height z (camera looks down at screen center)."""
    v = pygame.Vector2(pos)
    return v + (v - CAM) * (z * PERSP) + pygame.Vector2(0, -z * TILT)


def rand_dir():
    a = random.uniform(0, math.tau)
    return pygame.Vector2(math.cos(a), math.sin(a))


def rect_dist(pos, rect):
    cx = max(rect.left, min(pos.x, rect.right))
    cy = max(rect.top, min(pos.y, rect.bottom))
    return math.hypot(pos.x - cx, pos.y - cy)


def circle_hits_rect(pos, radius, rect):
    return rect_dist(pos, rect) < radius


def move_circle(pos, delta, radius, walls):
    new = pygame.Vector2(pos.x + delta.x, pos.y)
    if not any(circle_hits_rect(new, radius, w) for w in walls):
        pos.x = new.x
    new = pygame.Vector2(pos.x, pos.y + delta.y)
    if not any(circle_hits_rect(new, radius, w) for w in walls):
        pos.y = new.y
    pos.x = max(radius, min(W - radius, pos.x))
    pos.y = max(radius + 44, min(H - radius, pos.y))


def line_of_sight(a, b, walls):
    return not any(w.clipline(a, b) for w in walls)


def fire_color(u):
    u = round(max(0.0, min(1.0, u)), 1)
    stops = [(255, 250, 210), (255, 190, 70), (240, 90, 30), (120, 40, 30)]
    x = u * (len(stops) - 1)
    i = min(int(x), len(stops) - 2)
    return lerp_color(stops[i], stops[i + 1], x - i)


# ---------- cached sprites ----------
_glow = {}
_soft = {}


def blit_glow(surf, pos, radius, color, intensity=1.0):
    intensity = round(max(0.0, min(1.5, intensity)), 1)
    radius = int(radius)
    if intensity <= 0 or radius < 2:
        return
    key = (radius, color, intensity)
    g = _glow.get(key)
    if g is None:
        g = pygame.Surface((radius * 2, radius * 2))
        for r in range(radius, 0, -1):
            t = 1 - r / radius
            pygame.draw.circle(g, scale_color(color, (t ** 2.2) * intensity), (radius, radius), r)
        _glow[key] = g
    surf.blit(g, (pos[0] - radius, pos[1] - radius), special_flags=pygame.BLEND_RGB_ADD)


def blit_soft(surf, pos, radius, color, alpha):
    """Soft round blob with alpha (smoke, dust, scorch marks)."""
    if alpha < 6:
        return
    radius = max(2, min(70, int(radius)))
    key = (radius, color)
    s = _soft.get(key)
    if s is None:
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            t = 1 - r / radius
            pygame.draw.circle(s, (*color, int(255 * min(1, t * 1.8))), (radius, radius), r)
        _soft[key] = s
    s.set_alpha(int(min(255, alpha)))
    surf.blit(s, (pos[0] - radius, pos[1] - radius))


# ====================== particles ======================
class P:
    __slots__ = ("kind", "pos", "vel", "z", "vz", "life", "max", "size", "grow", "col", "rot", "vrot")

    def __init__(self, kind, pos, vel=(0, 0), z=0.0, vz=0.0, life=1.0, size=4.0, grow=0.0, col=(255, 255, 255)):
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.z, self.vz = z, vz
        self.life = self.max = life
        self.size, self.grow = size, grow
        self.col = col
        self.rot = random.uniform(0, math.tau)
        self.vrot = random.uniform(-8, 8)

    def update(self, dt, game):
        self.life -= dt
        self.pos += self.vel * dt
        k = self.kind
        if k == "chunk":
            self.vz -= GRAVITY * dt
            self.z += self.vz * dt
            self.rot += self.vrot * dt
            if self.z <= 0:
                self.z = 0
                if self.vz < -140:
                    self.vz *= -0.35
                    self.vel *= 0.5
                    self.vrot *= 0.5
                else:
                    game.stamp_chunk(self)
                    self.life = 0
        elif k in ("fire", "smoke", "dust"):
            self.vel *= 0.94 ** (dt * 60)
            self.z += self.vz * dt
            self.size += self.grow * dt
        elif k == "spark":
            self.vel *= 0.9 ** (dt * 60)
        elif k == "lift":
            self.z += self.vz * dt
            self.rot += self.vrot * dt
        elif k == "glass":
            self.vz -= GRAVITY * dt
            self.z += self.vz * dt
            if self.z <= 0:
                self.z, self.vz = 0, 0
                self.vel *= 0.8 ** (dt * 60)

    def draw(self, surf):
        t = 1 - self.life / self.max
        k = self.kind
        p = proj(self.pos, self.z)
        if k == "fire":
            if t < 0.45:
                c = fire_color(t / 0.45)
                blit_glow(surf, p, self.size * 2.2, c, 1.1 - t)
                pygame.draw.circle(surf, c, p, max(1, self.size * (1 - t * 0.6)))
            else:
                blit_soft(surf, p, self.size * 1.3, SMOKE, 210 * (1 - (t - 0.45) / 0.55))
        elif k == "smoke":
            blit_soft(surf, p, self.size, self.col, 170 * (1 - t) * min(1, t * 6))
        elif k == "dust":
            blit_soft(surf, p, self.size, DUST, 140 * (1 - t) * min(1, t * 6))
        elif k == "spark":
            tail = p - self.vel * 0.025
            pygame.draw.line(surf, scale_color((255, 220, 140), 1 - t), tail, p, 2)
        elif k == "chunk":
            sh = self.pos + pygame.Vector2(3, 4) + self.pos * 0  # shadow on ground
            s = self.size * (1 + self.z * 0.003)
            if self.z > 1:
                pygame.draw.circle(surf, (8, 8, 12), sh, self.size * 0.7)
            pts = [p + pygame.Vector2(math.cos(self.rot + a), math.sin(self.rot + a)) * s
                   for a in (0, 2.1, 3.3, 4.9)]
            pygame.draw.polygon(surf, self.col, pts)
        elif k == "lift":
            s = self.size * (1 + self.z * 0.003) * min(1, self.life * 1.5)
            pts = [p + pygame.Vector2(math.cos(self.rot + a), math.sin(self.rot + a)) * s
                   for a in (0, 2.1, 3.3, 4.9)]
            pygame.draw.polygon(surf, self.col, pts)
            blit_glow(surf, p, 10, (80, 255, 120), 0.4)
        elif k == "glass":
            c = (200, 235, 255) if int(self.life * 30) % 2 else (120, 170, 220)
            pygame.draw.rect(surf, scale_color(c, min(1, self.life * 2)), (p.x - 1, p.y - 1, 2, 2))
        elif k == "flash":
            blit_glow(surf, p, self.size, (255, 200, 120), 1.5 * (1 - t))
        elif k == "ring":
            r = self.size * (1 - (1 - t) ** 3)
            pygame.draw.circle(surf, scale_color((255, 230, 190), 1 - t), p, max(1, int(r)), max(1, int(5 * (1 - t))))


# ====================== knockback & shockwaves ======================
def knock_update(obj, dt, walls, radius):
    """Physics for units thrown by a shockwave. Returns impact speed if slammed into a wall."""
    if obj.knock.length_squared() < 0.01 and obj.kz <= 0:
        obj.knock.update(0, 0)
        return 0
    before = pygame.Vector2(obj.pos)
    want = obj.knock * dt
    move_circle(obj.pos, want, radius, walls)
    moved = obj.pos - before
    slam = 0
    speed = obj.knock.length()
    if want.length() > 0.5 and (want - moved).length() > want.length() * 0.5 and speed > 230:
        slam = speed
        obj.knock *= -0.25
    obj.knock *= (0.55 if obj.kz > 0 else 0.015) ** dt
    obj.kvz -= GRAVITY * dt
    obj.kz += obj.kvz * dt
    if obj.kz <= 0:
        obj.kz = 0
        obj.kvz = 0
    obj.kspin *= 0.3 ** dt
    obj.kangle += obj.kspin * dt
    return slam


class Shockwave:
    """Expanding ring. Everything its front passes gets thrown away from the center."""

    def __init__(self, pos, max_r, strength=1.0, speed=620, hits_player=True, nuke=False):
        self.pos = pygame.Vector2(pos)
        self.hits_player = hits_player
        self.nuke = nuke
        self.max_r = max_r
        self.r = 4.0
        self.strength = strength
        self.speed = speed
        self.alive = True

    def push(self, target_pos, r0, r1):
        d = target_pos.distance_to(self.pos)
        if not (r0 < d <= r1) and not (r0 == 4.0 and d <= r1):
            return None
        k = self.strength * (1 - d / self.max_r) ** 1.1
        dirv = (target_pos - self.pos)
        dirv = dirv.normalize() if dirv.length() > 0 else rand_dir()
        return dirv, max(0.0, k)

    def update(self, dt, game):
        r0 = self.r
        r1 = min(self.max_r, self.r + self.speed * dt)
        if r1 <= r0:
            return
        first = r0 == 4.0
        self.r = r1
        if first:
            r0 = -1
        # units
        for e in game.enemies:
            res = self.push(e.pos, r0, r1)
            if res:
                d, k = res
                e.knock += d * 760 * k
                e.kvz += 420 * k
                e.kspin += random.uniform(-14, 14) * k
        if not game.dead and self.hits_player:
            res = self.push(game.player, r0, r1)
            if res:
                d, k = res
                if self.nuke:
                    game.nuke_hit_player(d)
                    k = 0
                game.knock += d * 620 * k
                game.kvz += 330 * k
                game.kspin += random.uniform(-10, 10) * k
        # cars
        for c in game.cars:
            res = self.push(c.pos, r0, r1)
            if res:
                d, k = res
                if c.state == "drive":
                    if k > 0.25:
                        c.toss()
                    else:
                        continue
                c.vel += d * 560 * k
                c.vz += 430 * k
                c.z = max(c.z, 1)
                c.spin += random.uniform(-520, 520) * k
        if self.nuke:
            for u in game.ufos:
                if not u.falling and r0 < u.pos.distance_to(self.pos) <= r1:
                    u.hit(999, game)
            for tk in game.tanks:
                if tk.alive and r0 < tk.pos.distance_to(self.pos) <= r1:
                    tk.alive = False
                    game.explosion_fx(tk.pos, 60)
        # particles & debris
        for p in game.particles:
            if p.kind in ("flash", "ring", "spark"):
                continue
            res = self.push(p.pos, r0, r1)
            if res:
                d, k = res
                p.vel += d * 420 * k
                if p.kind == "chunk":
                    p.vz += 220 * k
                    p.z = max(p.z, 1)
        # bullets get deflected
        for sh in game.shots:
            res = self.push(sh.pos, r0, r1)
            if res:
                d, k = res
                spd = sh.vel.length()
                nv = sh.vel + d * 700 * k
                if nv.length() > 0:
                    sh.vel = nv.normalize() * spd
        # windows shatter (or, for a nuke, the whole building is torn apart)
        for b in game.buildings:
            if b.state in ("up", "falling"):
                bd = rect_dist(self.pos, b.rect)
                if self.nuke and r0 < bd <= r1:
                    dv = pygame.Vector2(b.rect.center) - self.pos
                    game.disintegrate(b, dv.normalize() if dv.length() else rand_dir())
                    continue
                if b.state == "up" and r0 < bd <= r1:
                    for _ in range(int(30 * self.strength * (1 - bd / self.max_r))):
                        b.windows[random.randrange(len(b.windows))] = False
                    b.win_ver += 1
                    for _ in range(4):
                        q = pygame.Vector2(max(b.rect.left, min(self.pos.x, b.rect.right)),
                                           max(b.rect.top, min(self.pos.y, b.rect.bottom)))
                        game.add(P("glass", q + rand_dir() * 6, rand_dir() * random.uniform(60, 200),
                                   random.uniform(5, b.h * 0.6), random.uniform(0, 120), 1.2, 2))
        if self.nuke:
            game.break_props(self.pos, r1)
        # kick up dust along the front
        a = 1 - self.r / self.max_r
        if a > 0.15:
            n = int(min(28, min(10, 2 + (r1 - r0) * 0.25) * (self.strength ** 2)))
            for _ in range(n):
                ang = random.uniform(0, math.tau)
                q = self.pos + pygame.Vector2(math.cos(ang), math.sin(ang)) * self.r
                game.add(P("dust", q, pygame.Vector2(math.cos(ang), math.sin(ang)) * 140 * a, 0, 10,
                           random.uniform(0.6, 1.3), random.uniform(5, 9), 16))
        if self.r >= self.max_r:
            self.alive = False

    def draw(self, add):
        a = 1 - self.r / self.max_r
        if a <= 0:
            return
        r = int(self.r)
        st = min(1.0, self.strength)
        pygame.draw.circle(add, scale_color((70, 90, 130), a), self.pos, r, max(1, int(22 * a * st)))
        pygame.draw.circle(add, scale_color((150, 175, 230), a), self.pos, r, max(1, int(8 * a * st)))
        pygame.draw.circle(add, scale_color((255, 255, 255), a), self.pos, r, 2)
        if self.nuke:
            a2 = max(a, 0.35)
            pygame.draw.circle(add, scale_color((140, 90, 50), a2), self.pos, r, max(1, int(70 * a2)))
            pygame.draw.circle(add, scale_color((255, 220, 170), a2), self.pos, r, max(2, int(14 * a2)))
        if r > 30:
            pygame.draw.circle(add, scale_color((60, 80, 120), a * 0.6), self.pos, int(r * 0.8), max(1, int(4 * a)))


# ====================== buildings ======================
class Building:
    SIDE_NORMALS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    def __init__(self, rect, rng):
        self.rect = rect
        area = rect.w * rect.h
        self.h0 = self.h = rng.randint(35, 70) + min(110, area // 180) * rng.uniform(0.4, 1.0)
        self.max_hp = self.hp = 8 + area / 1400
        self.roof = rng.choice(ROOFS)
        self.state = "up"
        self.shake = 0.0
        self.fall_v = 20.0
        self.fires = []
        self.scorch = []
        self.windows = [rng.random() < 0.38 for _ in range(400)]
        wincols = [(255, 214, 130), (255, 190, 110), (210, 225, 255), (255, 235, 180)]
        self.wincol = [rng.choice(wincols) if rng.random() > 0.1 else (120, 170, 255) for _ in range(400)]
        self.flicker = [rng.random() < 0.03 for _ in range(400)]
        self.neon = rng.choice([None, None, None, (255, 60, 170), (60, 220, 255), (170, 90, 255), (255, 150, 40)])
        self.tank = rng.random() < 0.35 and area > 3000   # rooftop water tank
        self.tank_pos = (rng.uniform(0.25, 0.75), rng.uniform(0.25, 0.75))
        self.speck_seed = rng.randint(0, 10 ** 6)
        self._roof_cache = None
        self._img = None
        self.win_ver = 0
        self.details = []
        for _ in range(rng.randint(1, 4)):
            fw, fh = rng.uniform(0.1, 0.25), rng.uniform(0.1, 0.25)
            self.details.append((rng.uniform(0.08, 0.9 - fw), rng.uniform(0.08, 0.9 - fh), fw, fh))
        self.acc_dust = self.acc_chunk = self.acc_fire = 0.0

    def solid(self):
        return self.state == "up" or (self.state == "falling" and self.h > 25)

    def roof_texture(self, w, h, roof):
        """Gravel roof with a raised parapet, cached per size/colour."""
        w, h = max(2, int(w)), max(2, int(h))
        key = (w, h, roof)
        if self._roof_cache and self._roof_cache[0] == key:
            return self._roof_cache[1]
        t = pygame.Surface((w, h))
        t.fill(scale_color(roof, 0.86))
        rng = random.Random(self.speck_seed)
        for _ in range(w * h // 30):
            x, y = rng.randrange(w), rng.randrange(h)
            t.set_at((x, y), scale_color(roof, rng.uniform(0.72, 1.0)))
        edge = max(2, int(min(w, h) * 0.07))
        pygame.draw.rect(t, scale_color(roof, 1.05), (0, 0, w, h), edge)
        pygame.draw.line(t, scale_color(roof, 1.25), (0, 0), (w, 0), 1)
        pygame.draw.line(t, scale_color(roof, 0.65), (edge, h - edge), (w - edge, h - edge), 1)
        self._roof_cache = (key, t)
        return t

    def damage(self, amount, game, at=None):
        if self.state != "up":
            return
        self.hp -= amount
        self.shake = 0.15
        game.money += int(amount * 2500)
        if at is not None and amount >= 2 and len(self.scorch) < 8:
            fx = (max(self.rect.left, min(at.x, self.rect.right)) - self.rect.x) / self.rect.w
            fy = (max(self.rect.top, min(at.y, self.rect.bottom)) - self.rect.y) / self.rect.h
            self.scorch.append((fx, fy, random.uniform(8, 16)))
        if self.hp < self.max_hp * 0.55 and len(self.fires) < 3 and random.random() < 0.5:
            self.fires.append((random.uniform(0.15, 0.85), random.uniform(0.15, 0.85)))
        if self.hp <= 0:
            self.state = "falling"
            game.on_collapse(self)

    def random_point(self):
        return pygame.Vector2(random.uniform(self.rect.left, self.rect.right),
                              random.uniform(self.rect.top, self.rect.bottom))

    def update(self, dt, game):
        self.shake = max(0, self.shake - dt)
        r = self.rect
        if self.state == "falling":
            self.fall_v += 160 * dt
            self.h -= self.fall_v * dt
            self.acc_dust += 70 * dt
            self.acc_chunk += 26 * dt
            while self.acc_dust >= 1:
                self.acc_dust -= 1
                side = random.randrange(4)
                p = [pygame.Vector2(random.uniform(r.left, r.right), r.top),
                     pygame.Vector2(r.right, random.uniform(r.top, r.bottom)),
                     pygame.Vector2(random.uniform(r.left, r.right), r.bottom),
                     pygame.Vector2(r.left, random.uniform(r.top, r.bottom))][side]
                out = pygame.Vector2(self.SIDE_NORMALS[side]) * random.uniform(30, 110)
                game.add(P("dust", p, out, random.uniform(0, max(1, self.h)), 8,
                           random.uniform(1.5, 3.5), random.uniform(8, 14), 22))
            while self.acc_chunk >= 1:
                self.acc_chunk -= 1
                p = self.random_point()
                out = (p - pygame.Vector2(r.center))
                out = out.normalize() * random.uniform(40, 170) if out.length() else rand_dir() * 80
                game.add(P("chunk", p, out, self.h, random.uniform(40, 260), 12,
                           random.uniform(4, 11), 0, scale_color(self.roof, random.uniform(0.5, 1.0))))
            if self.h <= 3:
                self.state = "rubble"
                game.stamp_rubble(self)
        elif self.fires:
            self.acc_fire += 9 * len(self.fires) * dt
            while self.acc_fire >= 1:
                self.acc_fire -= 1
                fx, fy = random.choice(self.fires)
                p = pygame.Vector2(r.x + fx * r.w, r.y + fy * r.h) + rand_dir() * 4
                if random.random() < 0.6:
                    game.add(P("fire", p, rand_dir() * 8, self.h, 30, random.uniform(0.6, 1.1),
                               random.uniform(4, 8), 6))
                else:
                    game.add(P("smoke", p, rand_dir() * 10 + pygame.Vector2(14, -6), self.h + 5, 35,
                               random.uniform(2.5, 4.5), 7, 14, SMOKE))

    def draw(self, surf):
        """The camera never moves, so a standing building is rendered once and reused."""
        neon_on = bool(self.neon) and math.sin(pygame.time.get_ticks() * 0.004 + self.speck_seed) > -0.85
        if self.state != "up" or self.shake > 0:
            return self.render(surf, pygame.Vector2(), neon_on)
        dmg = round(1 - max(0, self.hp) / self.max_hp, 1)
        key = (int(self.h), dmg, self.win_ver, neon_on, len(self.scorch))
        if self._img is None or self._img[0] != key:
            r = self.rect
            pts = [pygame.Vector2(q) for q in (r.topleft, r.topright, r.bottomright, r.bottomleft)]
            allp = pts + [proj(q, self.h) for q in pts]
            m = 34
            x0, y0 = min(q.x for q in allp) - m, min(q.y for q in allp) - m
            x1, y1 = max(q.x for q in allp) + m, max(q.y for q in allp) + m
            img = pygame.Surface((int(x1 - x0) + 1, int(y1 - y0) + 1), pygame.SRCALPHA)
            self.render(img, pygame.Vector2(x0, y0), neon_on)
            self._img = (key, img, (int(x0), int(y0)))
        surf.blit(self._img[1], self._img[2])

    def render(self, surf, off, neon_on):
        r = self.rect
        h = self.h
        jit = pygame.Vector2(random.uniform(-2, 2), random.uniform(-2, 2)) \
            if (self.shake > 0 or self.state == "falling") else pygame.Vector2()
        base = [pygame.Vector2(r.left, r.top) - off, pygame.Vector2(r.right, r.top) - off,
                pygame.Vector2(r.right, r.bottom) - off, pygame.Vector2(r.left, r.bottom) - off]
        top = [proj(p + off, h) + jit - off for p in base]
        dmg = 1 - max(0, self.hp) / self.max_hp
        roof = lerp_color(self.roof, (44, 38, 38), dmg * 0.55)
        shades = (0.5, 0.68, 0.84, 0.62)
        disp = proj(r.center, max(h, 1)) - pygame.Vector2(r.center)
        floors = max(1, int(h // 16))
        for i in (0, 1, 3, 2):  # draw the front (south) wall last
            n = self.SIDE_NORMALS[i]
            if n[0] * disp.x + n[1] * disp.y >= 0:
                continue  # wall faces away from the camera -> hidden behind the building
            a, b = base[i], base[(i + 1) % 4]
            ta, tb = top[i], top[(i + 1) % 4]
            side_col = scale_color(roof, shades[i])
            pygame.draw.polygon(surf, side_col, [a, b, tb, ta])
            # light catching the vertical corners + darker bottom (ambient occlusion)
            pygame.draw.line(surf, scale_color(side_col, 1.35), a, ta, 1)
            pygame.draw.line(surf, scale_color(side_col, 0.7), b, tb, 1)
            pygame.draw.polygon(surf, scale_color(side_col, 0.75), [a, b, b.lerp(tb, 0.12), a.lerp(ta, 0.12)])
            # floors with lit windows
            nwin = max(2, int(a.distance_to(b) // 14))
            for f in range(floors):
                u = (f + 0.5) / floors
                la, lb = a.lerp(ta, u), b.lerp(tb, u)
                for j in range(nwin):
                    idx = (i * 97 + f * 13 + j) % len(self.windows)
                    wp = la.lerp(lb, (j + 0.5) / nwin)
                    lit = self.windows[idx] and dmg < 0.8
                    col = self.wincol[idx] if lit else scale_color(side_col, 0.62)
                    pygame.draw.rect(surf, col, (wp.x - 2, wp.y - 1, 4, 3))
        # base line where the walls meet the street
        pygame.draw.line(surf, (10, 10, 14), base[3], base[2], 2)
        rr = pygame.Rect(top[0], top[2] - top[0])
        surf.blit(self.roof_texture(rr.w, rr.h, roof), rr.topleft)
        pygame.draw.polygon(surf, scale_color(roof, 1.3), top, 2)
        if self.neon and dmg < 0.7:
            if neon_on:
                pygame.draw.polygon(surf, self.neon, top, 2)
                pygame.draw.line(surf, scale_color(self.neon, 0.8), top[3] + (0, 4), top[2] + (0, 4), 2)
        if self.tank:
            c = pygame.Vector2(rr.x + self.tank_pos[0] * rr.w, rr.y + self.tank_pos[1] * rr.h)
            rad = max(5, min(rr.w, rr.h) * 0.13)
            pygame.draw.ellipse(surf, scale_color(roof, 0.5), (c.x - rad + 2, c.y - rad * 0.5 + 3, rad * 2, rad))
            pygame.draw.rect(surf, (88, 70, 58), (c.x - rad, c.y - 12, rad * 2, 12))
            pygame.draw.ellipse(surf, (120, 96, 78), (c.x - rad, c.y - 12 - rad * 0.5, rad * 2, rad))
            pygame.draw.ellipse(surf, (70, 56, 46), (c.x - rad, c.y - 12 - rad * 0.5, rad * 2, rad), 1)
        for fx, fy, fw, fh in self.details:   # rooftop boxes (AC units, stairwells) with their own height
            d = pygame.Rect(rr.x + fx * rr.w, rr.y + fy * rr.h, fw * rr.w, fh * rr.h)
            dh = 5
            pygame.draw.rect(surf, scale_color(roof, 0.55), d.move(3, 2))
            pygame.draw.rect(surf, scale_color(roof, 0.8), d.move(0, -dh + 3).inflate(0, dh))
            pygame.draw.rect(surf, scale_color(roof, 1.15), d.move(0, -dh))
        for fx, fy, s in self.scorch:
            blit_soft(surf, (rr.x + fx * rr.w, rr.y + fy * rr.h), s, (12, 10, 10), 190)


# ====================== cars ======================
def make_car_sprite(col):
    s = pygame.Surface((38, 20), pygame.SRCALPHA)
    pygame.draw.rect(s, scale_color(col, 0.55), (0, 0, 38, 20), border_radius=6)
    pygame.draw.rect(s, col, (1, 1, 36, 18), border_radius=6)
    pygame.draw.rect(s, scale_color(col, 1.18), (11, 3, 11, 14), border_radius=2)
    pygame.draw.rect(s, (22, 28, 40), (23, 3, 7, 14), border_radius=2)
    pygame.draw.line(s, (150, 170, 200), (25, 4), (28, 15), 1)          # windshield reflection
    pygame.draw.line(s, scale_color(col, 1.6), (12, 4), (20, 4), 1)     # roof highlight
    pygame.draw.line(s, scale_color(col, 1.4), (3, 2), (34, 2), 1)      # glossy edge
    pygame.draw.rect(s, (22, 28, 40), (5, 4, 5, 12), border_radius=2)
    pygame.draw.rect(s, (255, 240, 190), (34, 2, 3, 4))
    pygame.draw.rect(s, (255, 240, 190), (34, 14, 3, 4))
    pygame.draw.rect(s, (220, 30, 30), (0, 2, 2, 4))
    pygame.draw.rect(s, (220, 30, 30), (0, 14, 2, 4))
    return s


def make_wreck_sprite(sprite):
    s = sprite.copy()
    s.fill((105, 92, 86, 255), special_flags=pygame.BLEND_RGBA_MULT)
    for _ in range(5):
        pygame.draw.circle(s, (12, 10, 10), (random.randint(4, 34), random.randint(3, 17)), random.randint(2, 5))
    return s


def make_shadow(sprite):
    s = sprite.copy()
    s.fill((0, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MULT)
    s.fill((0, 0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
    return s


class Car:
    def __init__(self, lane, along):
        self.lane = lane  # (axis, coord, dir)
        axis, coord, d = lane
        self.pos = pygame.Vector2(along, coord) if axis == "h" else pygame.Vector2(coord, along)
        self.heading = pygame.Vector2(d, 0) if axis == "h" else pygame.Vector2(0, d)
        self.angle = {("h", 1): 0, ("h", -1): 180, ("v", 1): -90, ("v", -1): 90}[(axis, d)]
        self.max_speed = random.uniform(70, 125)
        self.speed = self.max_speed
        self.sprite = make_car_sprite(random.choice(CAR_COLS))
        self.shadow = make_shadow(self.sprite)
        self.side = self.sprite.copy()
        self.side.fill((90, 90, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
        self._rot = {}
        self.state = "drive"
        self.hp = 3
        self.fuse = None
        self.push = rand_dir()
        self.z = 0.0
        self.vz = 0.0
        self.vel = pygame.Vector2()
        self.spin = 0.0
        self.burn = 0.0
        self.acc = 0.0
        self.exploded = False

    def along(self):
        return self.pos.x if self.lane[0] == "h" else self.pos.y

    def toss(self):
        """Thrown by a shockwave without exploding (yet)."""
        self.state = "wreck"
        self.speed = 0

    def launch(self, direction, power=1.0):
        """Any hit sends the car flying (and juggles it if it's already in the air)."""
        self.toss()
        d = direction.normalize() if direction.length() > 0 else rand_dir()
        self.vel += d * random.uniform(260, 380) * power
        self.vz = max(self.vz, 0) + random.uniform(260, 380) * power
        self.z = max(self.z, 1)
        self.spin += random.uniform(-600, 600) * power

    def hit(self, amount, game, push=None):
        if self.exploded:
            return
        self.hp -= amount
        if push is not None and push.length() > 0:
            self.push = push.normalize()
        if self.hp <= 0 and self.fuse is None:
            self.fuse = random.uniform(0.06, 0.35)  # small delay -> visible chain reactions

    def blast(self, origin, k, game):
        push = self.pos - origin
        push = push.normalize() if push.length() > 0 else rand_dir()
        self.hit(5 * k + 1, game, push)  # the push itself comes from the shockwave

    def blow(self, game):
        self.state = "wreck"
        self.exploded = True
        self.sprite = make_wreck_sprite(self.sprite)
        self.side = self.sprite.copy()
        self.side.fill((90, 90, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
        self._rot = {}
        self.z = 1
        self.vz = random.uniform(320, 520)
        self.vel = self.push * random.uniform(60, 170)
        self.spin = random.uniform(-500, 500)
        self.burn = random.uniform(6, 10)
        game.money += 38000
        game.cars_destroyed += 1
        game.explode(self.pos, 82)

    def update(self, dt, game):
        if getattr(self, "held", False):
            return
        if self.fuse is not None and not self.exploded:
            self.fuse -= dt
            if self.fuse <= 0:
                self.blow(game)
                return
        if self.state == "drive":
            blocked = False
            for o in game.cars:
                if o is self:
                    continue
                rel = o.pos - self.pos
                ahead = rel.dot(self.heading)
                lateral = abs(rel.x * self.heading.y - rel.y * self.heading.x)
                if 0 < ahead < 48 and lateral < 14:
                    blocked = True
                    break
            for u in [game.player] + [e.pos for e in game.enemies]:
                rel = u - self.pos
                ahead = rel.dot(self.heading)
                if 0 < ahead < 40 and abs(rel.x * self.heading.y - rel.y * self.heading.x) < 16:
                    blocked = True
            target = 0 if blocked else self.max_speed
            self.speed = lerp(self.speed, target, min(1, dt * 5))
            self.pos += self.heading * self.speed * dt
            m = 40
            if self.lane[0] == "h":
                if self.pos.x > W + m: self.pos.x = -m
                if self.pos.x < -m: self.pos.x = W + m
            else:
                if self.pos.y > H + m: self.pos.y = -m
                if self.pos.y < -m: self.pos.y = H + m
        else:
            self.vz -= GRAVITY * dt
            self.z += self.vz * dt
            self.pos += self.vel * dt
            self.angle += self.spin * dt
            spd = self.vel.length()
            # crash into buildings
            b = game.building_at(self.pos)
            if b and b.h > self.z:
                self.pos -= self.vel * dt
                if spd > 180:
                    b.damage(spd / (70 if spd > 500 else 160), game, self.pos)
                    if spd > 500:
                        game.mini_wave(self.pos, True)
                    game.fx_impact(self.pos, b.roof)
                    game.shake = max(game.shake, 5)
                    self.hit(spd / 200, game)
                self.vel *= -0.35
                self.spin *= -0.6
            # flying cars hit people
            if spd > 200 and self.z < 25:
                for e in game.enemies:
                    if e.alive and e.pos.distance_to(self.pos) < 20:
                        game.kill_enemy(e)
                if not game.dead and game.player.distance_to(self.pos) < 18:
                    game.hurt_player(1)
            if self.z <= 0:
                self.z = 0
                if self.vz < -400 and not self.exploded:
                    self.hit(2, game)
                if self.vz < -160:
                    self.vz *= -0.3
                    self.vel *= 0.55
                    self.spin *= 0.5
                    game.fx_dust_puff(self.pos, 10)
                    game.shake = max(game.shake, 4)
                else:
                    self.vz = 0
                    self.vel *= 0.85 ** (dt * 60)
                    self.spin *= 0.85 ** (dt * 60)
            if self.burn > 0:
                self.burn -= dt
                self.acc += 14 * dt
                while self.acc >= 1:
                    self.acc -= 1
                    if random.random() < 0.55:
                        game.add(P("fire", self.pos + rand_dir() * 6, rand_dir() * 10, self.z + 6, 30,
                                   random.uniform(0.5, 0.9), random.uniform(4, 8), 6))
                    else:
                        game.add(P("smoke", self.pos + rand_dir() * 5, pygame.Vector2(14, -6) + rand_dir() * 8,
                                   self.z + 10, 40, random.uniform(2.5, 4.5), 6, 14, SMOKE))

    def rot(self, which, angle, scale):
        key = (which, int(angle) % 360 // 3, round(scale, 2))
        img = self._rot.get(key)
        if img is None:
            src = {"top": self.sprite, "side": self.side, "shadow": self.shadow}[which]
            img = pygame.transform.rotozoom(src, key[1] * 3, key[2])
            if len(self._rot) > 400:
                self._rot.clear()
            self._rot[key] = img
        return img

    def draw(self, surf):
        scale = 1 + self.z * 0.0028
        sh = self.rot("shadow", self.angle, 1.0)
        so = self.pos + SUN * (self.z + 8)
        surf.blit(sh, sh.get_rect(center=so))
        side = self.rot("side", self.angle, scale)
        for dz in (1, 4, 7):          # stacked layers = the car's body with real height
            surf.blit(side, side.get_rect(center=proj(self.pos, self.z + dz)))
        spr = self.rot("top", self.angle, scale)
        p = proj(self.pos, self.z + 10)
        surf.blit(spr, spr.get_rect(center=p))
        if self.state == "drive":
            side = pygame.Vector2(-self.heading.y, self.heading.x)
            for s in (-6, 6):
                blit_glow(surf, self.pos + self.heading * 20 + side * s, 12, (255, 230, 170), 0.8)
            blit_glow(surf, self.pos + self.heading * 48, 30, (255, 220, 150), 0.25)
            for s in (-6, 6):
                blit_glow(surf, self.pos - self.heading * 20 + side * s, 8, (255, 40, 40), 0.7)


# ====================== units & shots ======================
def draw_person(surf, pos, z, aim_n, dark, col, head_col, glow):
    """A small 3D soldier: shadow, legs, body and head stacked at different heights."""
    s = 1 + z * 0.004
    pygame.draw.ellipse(surf, (4, 4, 8), (pos.x + SUN.x * (z + 14) - 9, pos.y + SUN.y * (z + 14) - 6, 18, 12))
    feet = proj(pos, z)
    body = proj(pos, z + 10)
    head = proj(pos, z + 19)
    pygame.draw.line(surf, scale_color(dark, 0.7), feet, body, int(10 * s))
    blit_glow(surf, body, 34, col, glow)
    pygame.draw.circle(surf, dark, body, UNIT_R * s)
    pygame.draw.circle(surf, col, body, UNIT_R * s, 3)
    pygame.draw.line(surf, col, body + aim_n * (UNIT_R - 3), body + aim_n * (UNIT_R + 10), 5)
    pygame.draw.circle(surf, scale_color(dark, 0.8), head + (1, 2), 6 * s)
    pygame.draw.circle(surf, head_col, head, 6 * s)


# ====================== enemy AI ======================
CELL = 16
ROLES = ("assault", "flanker", "sniper")
ROLE_INFO = {
    #           preferred range, speed, seconds between bursts, shots per burst, aim error (radians)
    "assault": dict(rng=(110, 200), speed=1.15, fire=0.9, burst=3, acc=0.10, col=(255, 60, 90), dark=(110, 20, 40)),
    "flanker": dict(rng=(160, 250), speed=1.4, fire=1.1, burst=2, acc=0.12, col=(255, 150, 40), dark=(120, 60, 10)),
    "sniper": dict(rng=(300, 430), speed=0.85, fire=2.3, burst=1, acc=0.025, col=(190, 90, 255), dark=(70, 30, 110)),
}
NEIGH = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
         (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
_icon_font = None


class NavGrid:
    """A walkability grid of the city + A* pathfinding, so enemies walk around buildings."""

    def __init__(self):
        self.cols = W // CELL + 1
        self.rows = H // CELL + 1
        self.blocked = bytearray(self.cols * self.rows)
        self.sig = None

    def update(self, game):
        sig = len(game.walls)
        if sig == self.sig:
            return
        self.sig = sig
        b = bytearray(self.cols * self.rows)
        pad = UNIT_R + 2
        for r in game.walls:
            x0, x1 = max(0, int((r.left - pad) // CELL)), min(self.cols - 1, int((r.right + pad) // CELL))
            y0, y1 = max(0, int((r.top - pad) // CELL)), min(self.rows - 1, int((r.bottom + pad) // CELL))
            for cy in range(y0, y1 + 1):
                for cx in range(x0, x1 + 1):
                    if rect_dist(pygame.Vector2(cx * CELL + CELL / 2, cy * CELL + CELL / 2), r) < pad:
                        b[cy * self.cols + cx] = 1
        for cy in range(0, (44 + UNIT_R) // CELL + 1):   # the HUD bar
            for cx in range(self.cols):
                b[cy * self.cols + cx] = 1
        self.blocked = b

    def cell(self, p):
        return (min(self.cols - 1, max(0, int(p[0] // CELL))), min(self.rows - 1, max(0, int(p[1] // CELL))))

    def free(self, c):
        return 0 <= c[0] < self.cols and 0 <= c[1] < self.rows and not self.blocked[c[1] * self.cols + c[0]]

    def free_pos(self, p):
        return self.free(self.cell(p))

    def center(self, c):
        return pygame.Vector2(c[0] * CELL + CELL / 2, c[1] * CELL + CELL / 2)

    def clear_line(self, a, b):
        d = pygame.Vector2(b) - a
        n = int(d.length() // 8) + 1
        for i in range(n + 1):
            if not self.free_pos(a + d * (i / n)):
                return False
        return True

    def nearest_free(self, c, maxr=6):
        if self.free(c):
            return c
        for r in range(1, maxr + 1):
            for dx in range(-r, r + 1):
                for cc in ((c[0] + dx, c[1] - r), (c[0] + dx, c[1] + r), (c[0] - r, c[1] + dx), (c[0] + r, c[1] + dx)):
                    if self.free(cc):
                        return cc
        return None

    def path(self, a, b):
        import heapq
        start = self.nearest_free(self.cell(a))
        goal = self.nearest_free(self.cell(b))
        if not start or not goal:
            return []
        openh = [(0.0, start)]
        came = {start: None}
        g = {start: 0.0}
        n = 0
        while openh and n < 2500:
            n += 1
            _, cur = heapq.heappop(openh)
            if cur == goal:
                break
            for dx, dy, cost in NEIGH:
                nxt = (cur[0] + dx, cur[1] + dy)
                if not self.free(nxt):
                    continue
                if dx and dy and (not self.free((cur[0] + dx, cur[1])) or not self.free((cur[0], cur[1] + dy))):
                    continue
                ng = g[cur] + cost
                if ng < g.get(nxt, 1e9):
                    g[nxt] = ng
                    came[nxt] = cur
                    hx, hy = abs(goal[0] - nxt[0]), abs(goal[1] - nxt[1])
                    heapq.heappush(openh, (ng + max(hx, hy) + 0.414 * min(hx, hy), nxt))
        if goal not in came:
            return []
        cells = []
        c = goal
        while c:
            cells.append(c)
            c = came[c]
        cells.reverse()
        pts = [self.center(c) for c in cells]
        # string-pulling: skip waypoints we can walk straight past
        out, cur, i = [], pygame.Vector2(a), 0
        while i < len(pts):
            j = i
            while j + 1 < len(pts) and self.clear_line(cur, pts[j + 1]):
                j += 1
            out.append(pts[j])
            cur = pts[j]
            i = j + 1
        return out


class Enemy:
    """A soldier with a brain: it attacks, flanks, takes cover, dodges, hunts and works with its squad."""

    def __init__(self, pos, level, role="assault"):
        self.pos = pygame.Vector2(pos)
        self.alive = True
        self.role = role
        self.info = ROLE_INFO[role]
        self.level = level
        self.speed = (60 + level * 4) * self.info["speed"]
        self.fire_rate = max(0.45, self.info["fire"] * (1.2 - min(0.45, level * 0.05)))
        self.cooldown = random.uniform(1.2, 2.2)
        self.burst_left = 0
        self.burst_t = 0.0
        self.rocket_cd = random.uniform(max(4, 10 - level), max(7, 14 - level)) if role != "sniper" else 1e9
        self.dodge_chance = min(0.8, 0.3 + level * 0.07) * (1.25 if role == "flanker" else 1.0)
        self.flash = 0
        self.sees = False
        self.phase = random.uniform(0, math.tau)
        self.knock = pygame.Vector2()
        self.kz = self.kvz = self.kspin = self.kangle = 0.0
        # brain
        self.state = "patrol"
        self.goal = None
        self.path = []
        self.need_path = False
        self.think_t = random.uniform(0.1, 0.5)
        self.cover_t = 0.0
        self.suppress = 0.0
        self.dodge_t = 0.0
        self.dodge_cd = 0.0
        self.dodge_vec = pygame.Vector2()
        self.alert = 0.0
        self.flank_side = random.choice((-1, 1))
        self.strafe_t = random.uniform(0.5, 1.5)

    # ---------- senses ----------
    def sense_threats(self, dt, game):
        self.dodge_cd -= dt
        self.suppress = max(0.0, self.suppress - dt * 0.7)
        for s in game.shots:
            if not s.friendly or not s.alive:
                continue
            sp = s.vel.length()
            if sp < 1:
                continue
            vn = s.vel / sp
            rel = self.pos - s.pos
            along = rel.dot(vn)
            if along <= 0 or along > 260:
                continue
            perp = rel - vn * along
            pd = perp.length()
            if pd < 60:
                self.suppress += dt * 6          # bullets flying past = keep your head down
            danger_w = 70 if s.rocket else 20
            if pd < danger_w and along < (260 if s.rocket else 170) and self.dodge_cd <= 0:
                self.dodge_cd = 0.9
                if s.rocket or random.random() < self.dodge_chance:
                    side = perp.normalize() if pd > 0.5 else pygame.Vector2(-vn.y, vn.x) * random.choice((-1, 1))
                    self.dodge_vec = side
                    self.dodge_t = 0.32 if s.rocket else 0.2
                    game.ai_dodges = getattr(game, "ai_dodges", 0) + 1

    # ---------- decisions ----------
    def think(self, game):
        P = game.player
        mem = game.ai_mem
        here = game.danger_at(self.pos)
        if (self.suppress > 0.55 and self.role != "sniper") or here > 1.0:
            if self.state != "cover":
                self.cover_t = random.uniform(1.4, 2.4)
            self.state = "cover"
        elif self.state == "cover" and self.cover_t > 0:
            pass
        elif self.sees:
            self.state = "attack"
        elif mem["pos"] is not None and game.world_t - mem["t"] < 9:
            self.state = "hunt"
        else:
            self.state = "patrol"

        goal = None
        if self.state == "cover":
            goal = self.find_cover(game)
        if goal is None and self.state in ("attack", "cover"):
            goal = self.find_attack_pos(game, P)
        if self.state == "hunt":
            lp = mem["pos"]
            if self.role == "flanker":   # come at the last known spot from the side
                d = lp - self.pos
                if d.length() > 1:
                    side = pygame.Vector2(-d.y, d.x).normalize() * 90 * self.flank_side
                    cand = lp + side
                    goal = cand if game.nav.free_pos(cand) else lp
            goal = goal or pygame.Vector2(lp)
        if self.state == "patrol":
            if self.goal is None or self.pos.distance_to(self.goal) < 20:
                for _ in range(20):
                    q = pygame.Vector2(random.uniform(40, W - 40), random.uniform(70, H - 40))
                    if game.nav.free_pos(q):
                        goal = q
                        break
            else:
                goal = self.goal
        if goal is not None and (self.goal is None or goal.distance_to(self.goal) > 24 or not self.path):
            self.goal = pygame.Vector2(goal)
            self.need_path = True

    def find_attack_pos(self, game, P):
        lo, hi = self.info["rng"]
        base = self.pos - P
        base_ang = math.atan2(base.y, base.x) if base.length() > 0 else random.uniform(0, math.tau)
        offs = [0, 0.45, -0.45, 0.9, -0.9]
        if self.role == "flanker":
            offs = [self.flank_side * 1.3, self.flank_side * 0.9, self.flank_side * 1.7, 0]
        best, bs = None, 1e9
        for o in offs:
            for rr in (lo, (lo + hi) / 2, hi):
                a = base_ang + o + random.uniform(-0.15, 0.15)
                q = P + pygame.Vector2(math.cos(a), math.sin(a)) * rr
                if not (20 < q.x < W - 20 and 64 < q.y < H - 20) or not game.nav.free_pos(q):
                    continue
                if not line_of_sight(q, P, game.walls):
                    continue
                score = q.distance_to(self.pos) + game.danger_at(q) * 400
                for e in game.enemies:   # spread out, don't bunch up
                    if e is not self and e.goal is not None and e.goal.distance_to(q) < 60:
                        score += 180
                if score < bs:
                    best, bs = q, score
        return best

    def find_cover(self, game):
        P = game.player
        best, bs = None, 1e9
        for _ in range(20):
            a = random.uniform(0, math.tau)
            q = self.pos + pygame.Vector2(math.cos(a), math.sin(a)) * random.uniform(30, 180)
            if not (20 < q.x < W - 20 and 64 < q.y < H - 20) or not game.nav.free_pos(q):
                continue
            if line_of_sight(q, P, game.walls) or q.distance_to(P) < 110:
                continue
            score = q.distance_to(self.pos) + game.danger_at(q) * 400
            if score < bs:
                best, bs = q, score
        return best

    # ---------- body ----------
    def move(self, dt, game):
        spd = self.speed
        if self.dodge_t > 0:
            self.dodge_t -= dt
            move_circle(self.pos, self.dodge_vec * spd * 3.4 * dt, UNIT_R, game.walls)
            return
        if self.need_path and game.path_budget > 0 and self.goal is not None:
            game.path_budget -= 1
            self.path = game.nav.path(self.pos, self.goal)
            self.need_path = False
        target = None
        if self.goal is not None and self.pos.distance_to(self.goal) > 8:
            if self.pos.distance_to(self.goal) < 260 and game.nav.clear_line(self.pos, self.goal):
                target = self.goal
            elif self.path:
                while self.path and self.pos.distance_to(self.path[0]) < 9:
                    self.path.pop(0)
                if self.path:
                    target = self.path[0]
                else:
                    self.need_path = True
            else:
                self.need_path = True
        v = pygame.Vector2()
        if target is not None:
            d = target - self.pos
            if d.length() > 1:
                v = d.normalize()
        elif self.state == "attack" and self.sees:      # in position: strafe while shooting
            self.strafe_t -= dt
            if self.strafe_t <= 0:
                self.flank_side *= -1
                self.strafe_t = random.uniform(0.6, 1.6)
            to_p = game.player - self.pos
            if to_p.length() > 1:
                v = pygame.Vector2(-to_p.y, to_p.x).normalize() * 0.45 * self.flank_side
        for e in game.enemies:   # separation
            if e is not self and e.alive:
                d = self.pos - e.pos
                if 0 < d.length() < 30:
                    v += d.normalize() * 0.9
        v += game.danger_push(self.pos)
        if v.length() > 1:
            v = v.normalize()
        move_circle(self.pos, v * spd * dt, UNIT_R, game.walls)

    def fire_bullet(self, game, speed):
        start = self.pos + (game.player - self.pos).normalize() * (UNIT_R + 6)
        aim = game.predict_player(start, speed) - start
        if aim.length() < 1:
            return
        err = random.gauss(0, self.info["acc"] * max(0.5, 1.3 - self.level * 0.06))
        game.shots.append(Shot(start, aim.rotate_rad(err), speed, False))
        game.fx_muzzle(start, BULLET_ENEMY)
        self.flash = 0.1

    def shoot(self, dt, game):
        self.cooldown -= dt
        self.rocket_cd -= dt
        if not self.sees or game.dead:
            self.burst_left = 0
            return
        dist = self.pos.distance_to(game.player)
        if dist > 600 or dist < 1:
            return
        if self.state == "cover" and self.cover_t > 0.5 and self.role != "sniper":
            return   # hiding
        speed = ENEMY_BULLET_SPEED * (1.7 if self.role == "sniper" else 1.0)
        if self.rocket_cd <= 0 and dist > 160:
            self.rocket_cd = random.uniform(7, 12)
            start = self.pos + (game.player - self.pos).normalize() * (UNIT_R + 6)
            tgt = game.predict_player(start, ENEMY_ROCKET_SPEED)
            game.shots.append(Shot(start, tgt - start, ENEMY_ROCKET_SPEED, False, True, tgt))
            game.fx_muzzle(start, BULLET_ENEMY, 10)
            self.flash = 0.15
        elif self.burst_left > 0:
            self.burst_t -= dt
            if self.burst_t <= 0:
                self.fire_bullet(game, speed)
                self.burst_left -= 1
                self.burst_t = 0.13
        elif self.cooldown <= 0:
            self.cooldown = self.fire_rate * random.uniform(0.85, 1.15)
            self.burst_left = self.info["burst"]
            self.burst_t = 0.0

    def update(self, dt, game):
        if getattr(self, "held", False):
            return
        self.phase += dt * 4
        slam = knock_update(self, dt, game.walls, UNIT_R)
        if slam > 300:
            game.kill_enemy(self)
            return
        if self.kz > 0 or self.knock.length() > 60:
            self.sees = False
            self.need_path = True
            return  # stunned while flying
        self.flash = max(0, self.flash - dt)
        self.alert = max(0, self.alert - dt)
        self.cover_t = max(0, self.cover_t - dt)
        mem = game.ai_mem
        self.sees = (not game.dead) and line_of_sight(self.pos, game.player, game.walls)
        if self.sees:
            if game.world_t - mem["t"] > 2.5:
                self.alert = 1.2
                game.squad_alert(self)
            mem["pos"] = pygame.Vector2(game.player)
            mem["t"] = game.world_t
        self.sense_threats(dt, game)
        self.think_t -= dt
        if self.think_t <= 0:
            self.think(game)
            self.think_t = random.uniform(0.3, 0.55)
        self.move(dt, game)
        self.shoot(dt, game)

    def draw(self, surf, player):
        global _icon_font
        col, dark = self.info["col"], self.info["dark"]
        aim = player - self.pos
        aim_n = aim.normalize() if aim.length() > 0 else pygame.Vector2(1, 0)
        warn = 0.9 if self.role == "sniper" else 0.45
        if self.kz > 0 or self.knock.length() > 60:
            aim_n = aim_n.rotate_rad(self.kangle)
        elif self.sees and self.cooldown < warn and self.burst_left == 0:
            k = 1 - self.cooldown / warn
            pygame.draw.line(surf, scale_color(col, 0.2 + 0.5 * k), proj(self.pos, 10),
                             proj(self.pos + aim_n * min(aim.length(), 1000), 10), 2 if self.role == "sniper" else 1)
        draw_person(surf, self.pos, self.kz, aim_n, dark, col, (255, 215, 220),
                    0.5 + 0.15 * math.sin(self.phase) + (0.6 if self.flash else 0))
        # what the enemy is thinking
        if _icon_font is None:
            _icon_font = pygame.font.SysFont("arial", 15, bold=True)
        head = proj(self.pos, self.kz + 33)
        icon = None
        if self.alert > 0:
            icon = ("!", (255, 220, 60))
        elif self.state == "hunt":
            icon = ("?", (200, 200, 220))
        elif self.state == "cover" and self.cover_t > 0:
            pygame.draw.arc(surf, (120, 190, 255), (head.x - 7, head.y - 7, 14, 14), 0.3, math.pi - 0.3, 3)
        if icon:
            img = _icon_font.render(icon[0], True, icon[1])
            surf.blit(img, img.get_rect(center=head))
        if self.role == "sniper":   # sniper scope glint
            blit_glow(surf, proj(self.pos, self.kz + 10) + aim_n * 10, 10, (210, 160, 255), 0.8)


class Shot:
    def __init__(self, pos, direction, speed, friendly, rocket=False, target=None):
        self.pos = pygame.Vector2(pos)
        self.vel = direction.normalize() * speed
        self.friendly = friendly
        self.rocket = rocket
        self.alive = True
        self.trail = []
        self.range = min(1000, self.pos.distance_to(target)) if target is not None else 1000
        self.acc = 0.0

    @property
    def color(self):
        if getattr(self, "alien", False):
            return (90, 255, 120)
        if getattr(self, "tank", False):
            return (255, 200, 90)
        return CYAN if self.friendly else BULLET_ENEMY

    def boom(self, game):
        self.alive = False
        if self.rocket:
            game.explode(self.pos, 78)

    def update(self, dt, game):
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > 10:
            self.trail.pop(0)
        step = self.vel * dt
        self.pos += step
        if self.rocket:
            self.range -= step.length()
            self.acc += 70 * dt
            while self.acc >= 1:
                self.acc -= 1
                game.add(P("smoke", self.pos - self.vel.normalize() * 8 + rand_dir() * 2, rand_dir() * 12, 6, 6,
                           random.uniform(0.8, 1.6), 4, 16, (110, 110, 118)))
            if self.range <= 0:
                return self.boom(game)
        if not (-20 <= self.pos.x <= W + 20 and 0 <= self.pos.y <= H + 20):
            self.alive = False
            return
        b = game.building_at(self.pos)
        if b:
            if self.rocket:
                return self.boom(game)
            game.bullet_hit_building(b, self)
            self.alive = False
            return
        for car in game.cars:
            if car.z < 22 and car.pos.distance_to(self.pos) < 17:
                if self.rocket:
                    return self.boom(game)
                car.hit(1, game, self.vel)
                car.launch(self.vel, 1.0 if self.friendly else 0.7)
                game.fx_impact(self.pos, (200, 200, 200))
                game.fx_dust_puff(car.pos, 4)
                game.shake = max(game.shake, 3)
                game.mini_wave(self.pos, self.friendly)
                self.alive = False
                return
        if self.friendly:
            for u in game.ufos:
                if not u.falling and proj(u.pos, u.z).distance_to(self.pos) < 36:
                    if self.rocket:
                        u.hit(8, game)
                        game.explosion_fx(self.pos, 50)
                        self.alive = False
                    else:
                        u.hit(1, game)
                        game.fx_muzzle(self.pos, (120, 255, 140), 6)
                        self.alive = False
                    return
            for e in game.enemies:
                if e.alive and e.pos.distance_to(self.pos) < UNIT_R + 4:
                    if self.rocket:
                        return self.boom(game)
                    game.kill_enemy(e)
                    game.mini_wave(self.pos, True)
                    self.alive = False
                    return
        elif game.shield_on and not game.dead and self.pos.distance_to(game.player) < SHIELD_R:
            game.shield_block(self)
        elif self.pos.distance_to(game.player) < UNIT_R + 3:
            if self.rocket:
                return self.boom(game)
            game.hurt_player(1)
            self.alive = False

    def draw(self, surf):
        col = self.color
        pts = [proj(q, 10) for q in self.trail + [self.pos]]
        here = pts[-1]
        pygame.draw.circle(surf, (6, 6, 10), self.pos + SUN * 10, 2)
        n = len(pts)
        for i in range(1, n):
            k = i / n
            pygame.draw.line(surf, scale_color(col, k * 0.8), pts[i - 1], pts[i], max(1, int((5 if self.rocket else 3) * k)))
        if self.rocket:
            d = self.vel.normalize()
            pygame.draw.line(surf, (230, 230, 235), here - d * 7, here + d * 6, 5)
            blit_glow(surf, here - d * 9, 18, (255, 170, 60), 1.0)
        else:
            if not self.friendly:
                pygame.draw.line(surf, scale_color(col, 0.35), here, here + self.vel.normalize() * 60, 1)
            blit_glow(surf, here, 14, col, 0.9)
            pygame.draw.circle(surf, (255, 255, 240), here, 3)


# ====================== time grenade ======================
TIME_FIELD_SCALE = 0.02
GRENADE_CD = 4.0        # game-time seconds between throws
FIELD_DURATION = 5.0    # game-time seconds
FIELD_RADIUS = 115
FIELD_COL = (150, 110, 255)


class Grenade:
    def __init__(self, start, target):
        self.start = pygame.Vector2(start)
        self.target = pygame.Vector2(target)
        dist = self.start.distance_to(self.target)
        self.flight = 0.25 + dist / 900
        self.u = 0.0
        self.pos = pygame.Vector2(start)
        self.z = 0.0
        self.fuse = None
        self.alive = True

    def update(self, dt, game):
        if self.fuse is None:
            self.u = min(1.0, self.u + dt / self.flight)
            self.pos = self.start.lerp(self.target, self.u)
            self.z = 4 * 90 * self.u * (1 - self.u)
            if self.u >= 1:
                self.fuse = 0.35
                game.fx_muzzle(self.pos, FIELD_COL, 6)
        else:
            self.fuse -= dt
            if self.fuse <= 0:
                self.alive = False
                game.fields.append(TimeField(self.pos))
                game.add(P("ring", self.pos, life=0.5, size=FIELD_RADIUS * 1.2))
                game.add(P("flash", self.pos, life=0.2, size=90))
                game.shake = max(game.shake, 5)

    def draw(self, surf, t):
        pygame.draw.circle(surf, (5, 5, 8), self.pos + (3, 5), 5)
        p = proj(self.pos, self.z)
        r = 5 * (1 + self.z * 0.004)
        pygame.draw.circle(surf, (60, 50, 90), p, r)
        pygame.draw.circle(surf, FIELD_COL, p, r, 2)
        blink = self.fuse is not None and int(t * 20) % 2
        blit_glow(surf, p, 22, FIELD_COL, 1.2 if blink else 0.6)
        if self.fuse is not None:
            pygame.draw.circle(surf, FIELD_COL, self.pos, int(FIELD_RADIUS * (1 - self.fuse / 0.35)), 1)


class TimeField:
    """A bubble where time (almost) stops - for everything except you."""
    _overlay = {}

    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.r = FIELD_RADIUS
        self.life = FIELD_DURATION
        self.strength = 0.0
        self.alive = True

    def update(self, dt, game):
        self.life -= dt
        if self.life > 0.3:
            self.strength = min(1.0, self.strength + dt * 6)
        else:
            self.strength = max(0.0, self.life / 0.3)
        if self.life <= 0:
            self.alive = False
            game.add(P("ring", self.pos, life=0.4, size=self.r * 1.1))
            for _ in range(14):
                game.add(P("spark", self.pos + rand_dir() * self.r * 0.9, rand_dir() * random.uniform(60, 200),
                           0, 0, random.uniform(0.2, 0.4)))

    def scale_at(self, pos):
        d = self.pos.distance_to(pos)
        if d >= self.r:
            return 1.0
        edge = min(1.0, (self.r - d) / 18)
        return lerp(1.0, TIME_FIELD_SCALE, edge * self.strength)

    def overlay(self, r):
        s = TimeField._overlay.get(r)
        if s is None:
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            for i in range(r, 0, -1):
                t = i / r
                a = int(25 + 70 * t ** 6)
                pygame.draw.circle(s, (110, 80, 230, a), (r, r), i)
            TimeField._overlay[r] = s
        return s

    def draw(self, surf, add, t):
        st = self.strength
        if st <= 0:
            return
        r = int(self.r * (0.8 + 0.2 * st))
        ov = self.overlay(r)
        ov.set_alpha(int(255 * st))
        surf.blit(ov, (self.pos.x - r, self.pos.y - r))
        c = self.pos
        pygame.draw.circle(add, scale_color(FIELD_COL, st), c, r, 3)
        ripple = (t * 0.6) % 1
        pygame.draw.circle(add, scale_color(FIELD_COL, 0.4 * st * (1 - ripple)), c, max(1, int(r * ripple)), 2)
        for i in range(12):  # clock ticks
            a = i * math.tau / 12
            d = pygame.Vector2(math.cos(a), math.sin(a))
            pygame.draw.line(add, scale_color(FIELD_COL, 0.7 * st), c + d * (r - 12), c + d * (r - 4), 2)
        frac = max(0.0, self.life / FIELD_DURATION)  # remaining time arc
        rect = pygame.Rect(c.x - r + 6, c.y - r + 6, (r - 6) * 2, (r - 6) * 2)
        pygame.draw.arc(add, scale_color((220, 200, 255), st), rect, math.pi / 2, math.pi / 2 + math.tau * frac, 4)
        hand = pygame.Vector2(math.cos(t * 0.4), math.sin(t * 0.4))
        pygame.draw.line(add, scale_color(FIELD_COL, 0.6 * st), c, c + hand * r * 0.55, 2)
        pygame.draw.line(add, scale_color(FIELD_COL, 0.6 * st), c, c + hand.rotate(130) * r * 0.35, 3)


# ====================== tanks ======================
TANK_CD = 12.0          # game-time seconds between calls
TANK_COUNT = 3
HULL = (96, 116, 72)
TURRET = (116, 138, 90)
TANK_STAY = 30.0       # game-time seconds a tank patrols before leaving


class Tank:
    """Rolls along the roads, crushes cars and shells everything it sees."""

    def __init__(self, delay):
        if random.random() < 0.5:
            coord = random.choice(ROADS_H)
            d = random.choice((1, -1))
            self.pos = pygame.Vector2(-70 - delay if d > 0 else W + 70 + delay, coord)
            self.heading = pygame.Vector2(d, 0)
        else:
            coord = random.choice(ROADS_V)
            d = random.choice((1, -1))
            self.pos = pygame.Vector2(coord, -70 - delay if d > 0 else H + 70 + delay)
            self.heading = pygame.Vector2(0, d)
        self.hull_angle = math.atan2(self.heading.y, self.heading.x)
        self.turret = self.hull_angle
        self.speed = 62
        self.fire_cd = random.uniform(1.0, 2.0)
        self.target = None
        self.retarget = 0.0
        self.recoil = 0.0
        self.tread = 0.0
        self.mark = 0.0
        self.last_turn = None
        self.entered = False
        self.alive = True
        self.life = TANK_STAY

    # --- targeting ---
    def target_pos(self):
        kind, obj = self.target
        if kind == "enemy":
            return obj.pos if obj.alive else None
        if kind == "building":
            return pygame.Vector2(obj.rect.center) if obj.state == "up" else None
        return obj.pos if obj.z < 5 else None

    def pick_target(self, game):
        cands = []
        for e in game.enemies:
            if e.alive and e.pos.distance_to(self.pos) < 520:
                cands += [("enemy", e)] * 3
        for b in game.buildings:
            if b.state == "up" and pygame.Vector2(b.rect.center).distance_to(self.pos) < 480:
                cands.append(("building", b))
        for c in game.cars:
            if c.z < 5 and c.pos.distance_to(self.pos) < 420:
                cands.append(("car", c))
        self.target = random.choice(cands) if cands else None
        self.retarget = random.uniform(2.5, 4.5)

    def update(self, dt, game):
        step = self.speed * dt
        self.pos += self.heading * step
        self.tread += step
        self.mark += step
        # turn at intersections sometimes
        for ix in ROADS_V:
            for iy in ROADS_H:
                if (ix, iy) != self.last_turn and self.pos.distance_to((ix, iy)) <= step + 1.5:
                    self.last_turn = (ix, iy)
                    if random.random() < 0.45:
                        self.pos.update(ix, iy)
                        self.heading = pygame.Vector2(-self.heading.y, self.heading.x) * random.choice((1, -1))
        # hull rotates smoothly toward the heading
        want = math.atan2(self.heading.y, self.heading.x)
        diff = (want - self.hull_angle + math.pi) % math.tau - math.pi
        self.hull_angle += max(-2.5 * dt, min(2.5 * dt, diff))
        # track marks
        if self.mark > 9:
            self.mark = 0
            side = pygame.Vector2(-self.heading.y, self.heading.x)
            for sgn in (-1, 1):
                q = self.pos + side * 13 * sgn - self.heading * 22
                pygame.draw.rect(game.ground, (22, 23, 28), (q.x - 3, q.y - 3, 6, 6))
        # crush cars and people in the way
        for c in game.cars:
            if c.z < 12 and c.pos.distance_to(self.pos + self.heading * 14) < 30:
                c.hit(5, game, self.heading)
                side = pygame.Vector2(-self.heading.y, self.heading.x) * random.choice((-1, 1))
                c.launch(self.heading + side * 0.7, 1.3)
                game.fx_impact(c.pos, (200, 200, 200))
                game.shake = max(game.shake, 5)
        for e in game.enemies:
            if e.alive and e.pos.distance_to(self.pos) < 28:
                game.kill_enemy(e)
        # entering / leaving the map
        self.life -= dt
        on_screen = -30 < self.pos.x < W + 30 and 40 < self.pos.y < H + 30
        if on_screen:
            self.entered = True
        elif self.entered:
            if self.life > 0:       # still on duty: U-turn back into the city
                self.heading = -self.heading
                self.pos += self.heading * (step + 2)
                self.last_turn = None
            else:
                self.alive = False
                return
        # turret & firing
        self.recoil = max(0, self.recoil - dt * 30)
        self.retarget -= dt
        tp = self.target_pos() if self.target else None
        if tp is None or self.retarget <= 0:
            self.pick_target(game)
            tp = self.target_pos() if self.target else None
        if tp is None:
            return
        aim = tp - self.pos
        want = math.atan2(aim.y, aim.x)
        diff = (want - self.turret + math.pi) % math.tau - math.pi
        self.turret += max(-1.8 * dt, min(1.8 * dt, diff))
        self.fire_cd -= dt
        if self.fire_cd <= 0 and abs(diff) < 0.08 and self.entered and aim.length() > 50:
            self.fire_cd = random.uniform(1.6, 2.6)
            d = pygame.Vector2(math.cos(self.turret), math.sin(self.turret))
            muzzle = self.pos + d * 38
            shell = Shot(muzzle, d, 540, True, True, pygame.Vector2(tp))
            shell.tank = True
            game.shots.append(shell)
            self.recoil = 7
            game.add(P("flash", muzzle, life=0.12, size=50))
            for _ in range(8):
                game.add(P("smoke", muzzle + rand_dir() * 4, d * random.uniform(40, 120) + rand_dir() * 20, 8, 10,
                           random.uniform(0.8, 1.5), 7, 14, (90, 90, 96)))
            game.fx_muzzle(muzzle, (255, 200, 90), 10)
            game.shake = max(game.shake, 6)
            game.burst = max(game.burst, 0.0)

    def hull_sprite(self):
        s = pygame.Surface((60, 40), pygame.SRCALPHA)
        for y in (0, 31):  # treads
            pygame.draw.rect(s, (28, 30, 26), (0, y, 60, 9), border_radius=3)
            off = int(self.tread) % 8
            for x in range(-8 + off, 60, 8):
                pygame.draw.line(s, (55, 58, 50), (x, y + 1), (x, y + 7), 2)
        pygame.draw.rect(s, scale_color(HULL, 0.7), (4, 6, 52, 28), border_radius=4)
        pygame.draw.rect(s, HULL, (6, 8, 48, 24), border_radius=4)
        pygame.draw.rect(s, scale_color(HULL, 1.2), (40, 10, 10, 20), border_radius=2)
        pygame.draw.rect(s, scale_color(HULL, 0.6), (8, 12, 8, 16), border_radius=2)
        return s

    def turret_sprite(self):
        s = pygame.Surface((90, 90), pygame.SRCALPHA)
        c = (45, 45)
        pygame.draw.rect(s, scale_color(TURRET, 0.7), (45, 41, 40 - self.recoil, 8), border_radius=2)
        pygame.draw.rect(s, (40, 44, 36), (80 - self.recoil, 40, 6, 10), border_radius=2)
        pygame.draw.circle(s, scale_color(TURRET, 0.7), c, 16)
        pygame.draw.circle(s, TURRET, c, 14)
        pygame.draw.circle(s, scale_color(TURRET, 1.25), (41, 41), 5)
        return s

    def draw(self, surf):
        deg = -math.degrees(self.hull_angle)
        hull = pygame.transform.rotate(self.hull_sprite(), deg)
        shadow = hull.copy()
        shadow.fill((0, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MULT)
        shadow.fill((0, 0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        surf.blit(shadow, shadow.get_rect(center=self.pos + SUN * 22))
        dark = hull.copy()
        dark.fill((80, 80, 80, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for dz in (0, 3):
            surf.blit(dark, dark.get_rect(center=proj(self.pos, dz)))
        surf.blit(hull, hull.get_rect(center=proj(self.pos, 6)))
        tur = pygame.transform.rotate(self.turret_sprite(), -math.degrees(self.turret))
        tdark = tur.copy()
        tdark.fill((70, 70, 70, 255), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(tdark, tdark.get_rect(center=proj(self.pos, 10)))
        surf.blit(tur, tur.get_rect(center=proj(self.pos, 15)))


# ====================== keyboard ======================
# Physical key positions (SDL scancodes), so the letter keys work in any keyboard language (Hebrew too).
PHYS = {"a": 4, "b": 5, "d": 7, "e": 8, "f": 9, "g": 10, "n": 17, "q": 20, "r": 21, "s": 22,
        "t": 23, "u": 24, "w": 26, "y": 28}


def key_is(e, ch):
    return e.key == getattr(pygame, "K_" + ch) or getattr(e, "scancode", None) == PHYS[ch]


# ====================== shield ======================
SHIELD_MAX = 100.0
SHIELD_R = 27            # bubble radius (pixels)
SHIELD_DRAIN = 6.0       # energy per game-second while it's up
SHIELD_REGEN = 16.0      # energy per game-second while it's down
SHIELD_DELAY = 1.4       # game-seconds before it starts recharging
SHIELD_PARRY = 0.25      # raise it this close to a hit (real seconds) and the shot bounces back
SHIELD_COL = (90, 220, 255)
_shield_sprite = None


def shield_sprite():
    """Honeycomb bubble, drawn once."""
    global _shield_sprite
    if _shield_sprite is None:
        r = SHIELD_R * 4
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*SHIELD_COL, 16), (r, r), r)
        hx = 22
        for row in range(-6, 7):
            for col in range(-6, 7):
                cx = r + col * hx * 1.5
                cy = r + row * hx * 1.732 + (hx * 0.866 if col % 2 else 0)
                if (cx - r) ** 2 + (cy - r) ** 2 > (r - 8) ** 2:
                    continue
                pts = [(cx + math.cos(a) * hx * 0.92, cy + math.sin(a) * hx * 0.92)
                       for a in [i * math.pi / 3 for i in range(6)]]
                pygame.draw.polygon(s, (*SHIELD_COL, 42), pts, 3)
        for i in range(10):   # brighter toward the rim
            pygame.draw.circle(s, (*SHIELD_COL, 8 + i * 6), (r, r), r - i, 2)
        pygame.draw.circle(s, (200, 245, 255, 150), (r, r), r, 4)
        pygame.draw.arc(s, (255, 255, 255, 130), (r * 0.35, r * 0.3, r * 0.9, r * 0.8), 1.9, 2.9, 6)   # shine
        _shield_sprite = pygame.transform.smoothscale(s, (SHIELD_R * 2, SHIELD_R * 2))
    return _shield_sprite


# ====================== black hole ======================
HOLE_DURATION = 16.0     # game-time seconds until it collapses
HOLE_PULL_R = 560
HOLE_CD = 8.0


class BlackHole:
    """Sucks in the whole city. Run!"""
    _dark = {}

    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.age = 0.0
        self.horizon = 6.0
        self.power = 0.0
        self.alive = True
        self.acc = 0.0
        self.disk = []
        for _ in range(170):
            rm = random.uniform(1.25, 4.2)
            hot = 1 - (rm - 1.25) / 2.95
            col = lerp_color((150, 70, 255), (255, 200, 120), hot ** 0.7)
            if random.random() < 0.15:
                col = (255, 245, 220)
            self.disk.append([rm, random.uniform(0, math.tau), col, random.uniform(1.5, 3.5)])

    def progress(self):
        return min(1.0, self.age / HOLE_DURATION)

    def collapsing(self):
        return self.age > HOLE_DURATION - 1.4

    def accel_at(self, pos):
        dv = self.pos - pygame.Vector2(pos)
        d = dv.length()
        if d >= HOLE_PULL_R or d < 0.5:
            return pygame.Vector2(), d
        inward = dv / d
        tang = pygame.Vector2(-inward.y, inward.x)
        mag = self.power * 135000 / max(d, 22) ** 1.12 * (1 - d / HOLE_PULL_R) ** 0.6
        return inward * mag + tang * mag * 0.5 * min(1.0, (d - self.horizon) / 160), d

    def update(self, dt, game):
        self.age += dt
        g = self.progress()
        if not self.collapsing():
            self.horizon = lerp(self.horizon, 14 + 34 * g, min(1, dt * 3))
            self.power = min(1.0, self.age / 1.5) * (1 + 0.9 * g)
        else:
            k = max(0.0, (HOLE_DURATION - self.age) / 1.4)
            self.horizon = max(3.0, (14 + 34 * g) * k)
            self.power *= 1 + dt * 1.5
        for dot in self.disk:
            dot[1] += dt * 4.5 / dot[0] ** 1.3
        h = self.horizon
        eat = h + 4
        game.shake = max(game.shake, 2 + 4 * g)

        # tear buildings apart
        tear_r = 60 + 230 * g
        for b in game.buildings:
            if b.state in ("up", "falling") and rect_dist(self.pos, b.rect) < tear_r:
                out = pygame.Vector2(b.rect.center) - self.pos
                out = out.normalize() if out.length() else rand_dir()
                game.disintegrate(b, pygame.Vector2(-out.y, out.x) * 0.6 - out * 0.4, speed=0.45)
        # player
        if not game.dead:
            a, d = self.accel_at(game.player)
            game.knock += a * dt
            if d < eat:
                game.consume_player()
        # enemies
        for e in game.enemies:
            if e.alive:
                a, d = self.accel_at(e.pos)
                e.knock += a * dt
                if d < eat:
                    e.alive = False
                    game.consumed += 1
                    game.fx_muzzle(self.pos, (200, 150, 255), 6)
        # cars float and spiral in
        for c in game.cars:
            a, d = self.accel_at(c.pos)
            if a.length() > 60:
                if c.state == "drive":
                    c.toss()
                c.vel += a * dt
                if d < 300:
                    c.vz += GRAVITY * dt * (1.05 - d / 300)
                    c.z = max(c.z, 1)
            if d < eat + 10:
                c.consumed = True
                game.consumed += 1
        # tanks are dragged in
        for tk in game.tanks:
            a, d = self.accel_at(tk.pos)
            tk.pos += a * dt * 0.3
            if d < eat + 14:
                tk.alive = False
                game.consumed += 1
        # bullets bend
        for sh in game.shots:
            a, d = self.accel_at(sh.pos)
            sh.vel += a * dt * 1.6
            if d < eat:
                sh.alive = False
        # everything else
        for p in game.particles:
            a, d = self.accel_at(p.pos)
            p.vel += a * dt
            if d < eat:
                p.life = 0
        # ground debris ripped up into the vortex
        self.acc += (14 + 40 * g) * dt
        while self.acc >= 1:
            self.acc -= 1
            q = self.pos + rand_dir() * random.uniform(h * 3, 60 + 260 * g)
            out = q - self.pos
            tang = pygame.Vector2(-out.y, out.x).normalize() if out.length() else rand_dir()
            col = random.choice([(70, 72, 80), (58, 60, 70), (90, 84, 80), (40, 42, 50)])
            game.add(P("chunk", q, tang * random.uniform(60, 160), 1, random.uniform(40, 140), 6,
                       random.uniform(2, 6), 0, col))
        if self.age >= HOLE_DURATION:
            self.alive = False
            game.hole_collapsed(self)

    # --- drawing ---
    def dark_sprite(self, r):
        r = max(8, int(r) // 4 * 4)
        s = BlackHole._dark.get(r)
        if s is None:
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            for i in range(r, 0, -1):
                t = 1 - i / r
                pygame.draw.circle(s, (6, 2, 14, int(235 * t ** 1.6)), (r, r), i)
            BlackHole._dark[r] = s
        return s

    def draw_dark(self, surf):
        s = self.dark_sprite(self.horizon * 6 + 40 * self.progress())
        surf.blit(s, s.get_rect(center=self.pos))

    def draw_glow(self, add, t):
        h = self.horizon
        c = self.pos
        blit_glow(add, c, h * 5, (120, 60, 220), 0.6)
        for rm, ang, col, size in self.disk:
            r = rm * h
            p = c + pygame.Vector2(math.cos(ang), math.sin(ang) * 0.55) * r  # tilted disk
            pygame.draw.circle(add, col, p, size * (0.6 + h / 50))
        for k in range(3):
            rr = h * (1.4 + k * 0.9)
            rect = pygame.Rect(c.x - rr, c.y - rr * 0.55, rr * 2, rr * 1.1)
            a0 = t * (2.2 - k * 0.6)
            pygame.draw.arc(add, scale_color((255, 180, 110), 0.7 - k * 0.2), rect, a0, a0 + 2.2, 2)
            pygame.draw.arc(add, scale_color((170, 90, 255), 0.6 - k * 0.15), rect, a0 + 3.1, a0 + 5.0, 2)

    def draw_core(self, surf):
        h = self.horizon
        pygame.draw.circle(surf, (0, 0, 0), self.pos, h)
        pygame.draw.circle(surf, (255, 235, 200), self.pos, h + 2, 2)


# ====================== gravity gun ======================
class Slab:
    """A chunk ripped off a building by the gravity gun."""

    def __init__(self, pos, col, z, size):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2()
        self.z, self.vz = z, 0.0
        self.rot = random.uniform(0, math.tau)
        self.size = size
        self.col = col
        self.alive = True
        self.held = True
        self.rest = 0.0

    def corners(self, c, scale=1.0):
        out = []
        for a, m in ((0.6, 1.0), (math.pi - 0.6, 1.0), (math.pi + 0.6, 1.0), (-0.6, 1.0)):
            out.append(c + pygame.Vector2(math.cos(self.rot + a), math.sin(self.rot + a)) * self.size * scale * m)
        return out

    def shatter(self, game):
        self.alive = False
        for _ in range(12):
            game.add(P("chunk", self.pos, rand_dir() * random.uniform(60, 240), self.z + 2, random.uniform(80, 260),
                       8, random.uniform(3, 7), 0, scale_color(self.col, random.uniform(0.6, 1.0))))
        game.fx_dust_puff(self.pos, 8)

    def update(self, dt, game):
        if self.held:
            return
        self.vz -= GRAVITY * dt
        self.z += self.vz * dt
        self.pos += self.vel * dt
        spd = self.vel.length()
        self.rot += 7 * dt * min(1, spd / 300)
        b = game.building_at(self.pos)
        if b and b.h > self.z and spd > 150:
            b.damage(spd / 90 + 3, game, self.pos)
            game.mini_wave(self.pos, True)
            game.fx_impact(self.pos, b.roof)
            game.shake = max(game.shake, 8)
            return self.shatter(game)
        if spd > 200 and self.z < 30:
            for e in game.enemies:
                if e.alive and e.pos.distance_to(self.pos) < 24:
                    game.kill_enemy(e)
            for c in game.cars:
                if c.z < 20 and c.pos.distance_to(self.pos) < 26:
                    c.hit(5, game, self.vel)
                    c.launch(self.vel, 1.2)
        if self.z <= 0:
            self.z = 0
            if self.vz < -200:
                self.vz *= -0.3
                self.vel *= 0.6
                game.fx_dust_puff(self.pos, 6)
                game.shake = max(game.shake, 4)
            else:
                self.vz = 0
                self.vel *= 0.88 ** (dt * 60)
            if self.vel.length() < 15:
                self.rest += dt
                if self.rest > 0.6:
                    pygame.draw.polygon(game.ground, scale_color(self.col, 0.7), self.corners(self.pos))
                    self.alive = False
        if not (-100 < self.pos.x < W + 100 and -100 < self.pos.y < H + 100):
            self.alive = False

    def draw(self, surf):
        pygame.draw.polygon(surf, (6, 6, 10), self.corners(self.pos + (4 + self.z * 0.05, 6 + self.z * 0.08)))
        sc = 1 + self.z * 0.003
        pts = self.corners(proj(self.pos, self.z), sc)
        pygame.draw.polygon(surf, self.col, pts)
        pygame.draw.polygon(surf, scale_color(self.col, 0.6), pts, 2)


# ====================== tsunami ======================
TSUNAMI_CD = 10.0


class Tsunami:
    """A giant wave floods the city from one side."""

    def __init__(self):
        side = random.choice(("left", "right", "top", "bottom"))
        self.side = side
        if side == "left":
            self.origin, self.dirn, self.length, self.span = pygame.Vector2(0, 0), pygame.Vector2(1, 0), W, H
        elif side == "right":
            self.origin, self.dirn, self.length, self.span = pygame.Vector2(W, H), pygame.Vector2(-1, 0), W, H
        elif side == "top":
            self.origin, self.dirn, self.length, self.span = pygame.Vector2(W, 0), pygame.Vector2(0, 1), H, W
        else:
            self.origin, self.dirn, self.length, self.span = pygame.Vector2(0, H), pygame.Vector2(0, -1), H, W
        self.perp = pygame.Vector2(-self.dirn.y, self.dirn.x)
        self.phase = "warn"
        self.warn = 2.5
        self.f = -40.0
        self.speed = 170
        self.alpha = 1.0
        self.alive = True
        self.hit_buildings = set()
        self.hit_player = False
        self.acc = 0.0
        self.overlay = pygame.Surface((W, H), pygame.SRCALPHA)

    def P(self, s, u):
        return self.origin + self.dirn * s + self.perp * u

    def s_of(self, pos):
        return (pygame.Vector2(pos) - self.origin).dot(self.dirn)

    def in_water(self, pos):
        return self.phase in ("flood", "recede") and self.s_of(pos) < self.f

    def at_front(self, pos):
        return self.phase == "flood" and self.f - 55 < self.s_of(pos) < self.f + 12

    def current(self):
        return self.dirn * 95 * self.alpha

    def update(self, dt, real_dt, game):
        if self.phase == "warn":
            self.warn -= real_dt
            if self.warn <= 0:
                self.phase = "flood"
                game.shake = max(game.shake, 10)
            return
        if self.phase == "flood":
            self.f += self.speed * dt
            game.shake = max(game.shake, 4)
            # spray along the crest
            self.acc += 90 * dt
            while self.acc >= 1:
                self.acc -= 1
                q = self.P(self.f + random.uniform(-10, 10), random.uniform(0, self.span))
                game.add(P("smoke", q, self.dirn * random.uniform(60, 180) + rand_dir() * 40, random.uniform(5, 40),
                           random.uniform(30, 90), random.uniform(0.6, 1.4), random.uniform(6, 12), 18, (215, 232, 250)))
            if self.f > self.length + 200:
                self.phase = "recede"
        elif self.phase == "recede":
            self.alpha -= dt / 4
            if self.alpha <= 0:
                self.alive = False
                return
        cur = self.current()
        push = self.dirn * self.speed * 2.2
        # buildings get smashed by the front
        for b in game.buildings:
            if b.state == "up" and id(b) not in self.hit_buildings:
                near = min(self.s_of(c) for c in (b.rect.topleft, b.rect.topright, b.rect.bottomleft, b.rect.bottomright))
                if self.phase == "flood" and near < self.f:
                    self.hit_buildings.add(id(b))
                    b.damage(b.max_hp * random.uniform(0.45, 1.15), game, pygame.Vector2(b.rect.center) - self.dirn * 30)
                    for _ in range(10):
                        q = pygame.Vector2(b.random_point())
                        game.add(P("smoke", q, self.dirn * random.uniform(40, 140) + rand_dir() * 50,
                                   random.uniform(10, b.h), 40, random.uniform(0.8, 1.5), 10, 18, (215, 232, 250)))
        # cars ride the wave and float
        for c in game.cars:
            if getattr(c, "held", False):
                continue
            if self.at_front(c.pos):
                if c.state == "drive":
                    c.toss()
                c.vel = c.vel.lerp(push, 0.25)
                c.vz = max(c.vz, 140)
                c.z = max(c.z, 2)
                c.spin += random.uniform(-200, 200) * dt
                c.burn = 0
            elif self.in_water(c.pos):
                if c.state == "drive":
                    c.toss()
                c.burn = 0
                c.z = max(c.z, 2)
                c.vz = max(c.vz, 0)
                c.vel += (cur - c.vel) * min(1, dt * 0.9)
                c.angle += c.spin * dt * 0.2
        # people are swept away
        for e in game.enemies:
            if getattr(e, "held", False):
                continue
            if self.at_front(e.pos):
                e.knock = e.knock.lerp(push, 0.35)
                e.kvz = max(e.kvz, 60)
            elif self.in_water(e.pos):
                e.knock += cur * dt * 4.5
        if not game.dead:
            if self.at_front(game.player):
                game.knock = game.knock.lerp(push, 0.35)
                game.kvz = max(game.kvz, 40)
                if not self.hit_player:
                    self.hit_player = True
                    game.hurt_player(1)
            elif self.in_water(game.player):
                game.knock += cur * dt * 4.5
        for tk in game.tanks:
            if self.at_front(tk.pos):
                tk.pos += self.dirn * self.speed * dt * 0.9
            elif self.in_water(tk.pos):
                tk.pos += cur * dt * 0.4
        for sl in game.slabs:
            if not sl.held and self.in_water(sl.pos):
                sl.vel += cur * dt
        # water puts out fire and carries debris
        for p in game.particles:
            if self.in_water(p.pos):
                if p.kind == "fire" and p.z < 30:
                    p.life = 0
                elif p.kind in ("chunk", "dust", "smoke", "glass"):
                    p.vel += cur * dt * 2

    def draw_water(self, surf, t):
        if self.phase == "warn":
            return
        ov = self.overlay
        ov.fill((0, 0, 0, 0))
        f = min(self.f, self.length + 200)
        a = self.alpha
        pygame.draw.polygon(ov, (25, 85, 150, int(140 * a)),
                            [self.P(-10, -10), self.P(f, -10), self.P(f, self.span + 10), self.P(-10, self.span + 10)])
        if self.phase == "flood":
            pygame.draw.polygon(ov, (40, 120, 190, 120),
                                [self.P(max(-10, f - 70), -10), self.P(f, -10), self.P(f, self.span + 10),
                                 self.P(max(-10, f - 70), self.span + 10)])
        off = (t * 60) % 46
        s = -40 + off
        while s < f - 10:
            for u in range(0, int(self.span), 70):
                wob = math.sin(t * 2 + s * 0.05 + u * 0.1) * 8
                pygame.draw.line(ov, (120, 190, 240, int(70 * a)), self.P(s + wob, u), self.P(s + wob + 10, u + 30), 2)
            s += 46
        surf.blit(ov, (0, 0))

    def draw_crest(self, surf, t):
        if self.phase == "warn":
            # warning: flashing edge on the side the wave comes from
            pulse = 0.5 + 0.5 * math.sin(t * 12)
            ov = self.overlay
            ov.fill((0, 0, 0, 0))
            pygame.draw.polygon(ov, (60, 160, 255, int(60 + 90 * pulse)),
                                [self.P(0, 0), self.P(60, 0), self.P(60, self.span), self.P(0, self.span)])
            surf.blit(ov, (0, 0))
            return
        if self.phase != "flood":
            return
        f = self.f
        WALL = 55
        step = 14
        prev = None
        for u in range(-20, int(self.span) + 30, step):
            wob = math.sin(t * 7 + u * 0.13) * 7 + math.sin(t * 3.1 + u * 0.05) * 5
            g = self.P(f + wob, u)
            top = proj(g, WALL + 6 * math.sin(t * 5 + u * 0.2))
            if prev:
                pg, pt = prev
                pygame.draw.polygon(surf, (30, 100, 170), [pg, g, top, pt])
                pygame.draw.line(surf, (90, 170, 230), pt, top, 3)
            prev = (g, top)
        for u in range(-10, int(self.span) + 20, 14):
            wob = math.sin(t * 7 + u * 0.13) * 7 + math.sin(t * 3.1 + u * 0.05) * 5
            q = proj(self.P(f + wob, u), WALL)
            pygame.draw.circle(surf, (205, 228, 250), q, 13 + 4 * math.sin(t * 9 + u))
            pygame.draw.circle(surf, (250, 252, 255), q + self.dirn * 4, 7)


# ====================== aliens ======================
ALIEN_CD = 15.0
UFO_COUNT = 3


class UFO:
    def __init__(self, delay):
        side = random.choice(("left", "right", "top"))
        if side == "left":
            self.pos = pygame.Vector2(-120 - delay, random.uniform(120, H - 120))
        elif side == "right":
            self.pos = pygame.Vector2(W + 120 + delay, random.uniform(120, H - 120))
        else:
            self.pos = pygame.Vector2(random.uniform(120, W - 120), -120 - delay)
        self.z = 150.0
        self.vz = 0.0
        self.vel = pygame.Vector2()
        self.hp = 22
        self.state = "move"
        self.target = self.new_target()
        self.timer = 0.0
        self.shots = 0
        self.shot_t = 0.0
        self.life = 45.0
        self.falling = False
        self.alive = True
        self.flash = 0.0
        self.spin = 0.0
        self.acc = 0.0

    @staticmethod
    def new_target():
        return pygame.Vector2(random.uniform(90, W - 90), random.uniform(110, H - 90))

    def hit(self, dmg, game):
        if self.falling:
            return
        self.hp -= dmg
        self.flash = 0.12
        if self.hp <= 0:
            self.falling = True
            self.vel = rand_dir() * 90
            self.vz = 40
            game.money += 250000
            game.ufos_down += 1
            game.explosion_fx(proj(self.pos, self.z), 45)

    def update(self, dt, game):
        self.flash = max(0, self.flash - dt)
        self.spin += dt * (14 if self.falling else 3)
        sp = proj(self.pos, self.z)
        if self.falling:
            self.vz -= 420 * dt
            self.z += self.vz * dt
            self.pos += self.vel * dt
            self.acc += 40 * dt
            while self.acc >= 1:
                self.acc -= 1
                game.add(P("fire" if random.random() < 0.4 else "smoke", self.pos + rand_dir() * 8, rand_dir() * 20,
                           self.z, 20, random.uniform(0.8, 1.6), random.uniform(6, 11), 12, SMOKE))
            if self.z <= 0:
                self.alive = False
                game.explode(self.pos, 115)
                game.waves.append(Shockwave(self.pos, 480, 1.3, 650))
                game.shake = max(game.shake, 18)
            return
        self.life -= dt
        if self.life <= 0 and self.state != "leave":
            self.state = "leave"
            self.target = pygame.Vector2(self.pos.x, -300)
        if self.state in ("move", "leave"):
            d = self.target - self.pos
            if d.length() < 6:
                if self.state == "leave":
                    self.alive = False
                    return
                self.state = "beam"
                self.timer = random.uniform(3.0, 4.5)
            else:
                self.pos += d.normalize() * min(d.length(), 95 * dt)
        elif self.state == "beam":
            self.timer -= dt
            game.ufo_beam(self, dt)
            if self.timer <= 0:
                self.state = "shoot"
                self.shots = 3
                self.shot_t = 0.2
        elif self.state == "shoot":
            self.shot_t -= dt
            if self.shot_t <= 0:
                self.shots -= 1
                self.shot_t = 0.45
                if random.random() < 0.6 and not game.dead:
                    tgt = pygame.Vector2(game.player) + rand_dir() * 25
                else:
                    ups = [b for b in game.buildings if b.state == "up"]
                    tgt = pygame.Vector2(random.choice(ups).rect.center) if ups else self.new_target()
                aim = tgt - sp
                if aim.length() > 1:
                    laser = Shot(sp, aim, 520, False, True, tgt)
                    laser.alien = True
                    game.shots.append(laser)
                    game.add(P("flash", sp, life=0.1, size=40))
                if self.shots <= 0:
                    self.state = "move"
                    self.target = self.new_target()

    def draw_beam(self, add, t):
        if self.state != "beam" or self.falling:
            return
        sp = proj(self.pos, self.z)
        k = 0.75 + 0.25 * math.sin(t * 10)
        pygame.draw.polygon(add, scale_color((40, 150, 60), k),
                            [sp + (-16, 8), sp + (16, 8), self.pos + (48, 0), self.pos + (-48, 0)])
        pygame.draw.polygon(add, scale_color((80, 230, 110), k),
                            [sp + (-7, 8), sp + (7, 8), self.pos + (20, 0), self.pos + (-20, 0)])
        for i in range(3):
            r = 48 * ((t * 0.8 + i / 3) % 1)
            pygame.draw.circle(add, scale_color((80, 255, 120), 1 - r / 48), self.pos, max(1, int(r)), 2)

    def draw(self, surf, t):
        sp = proj(self.pos, self.z)
        sc = 1 + self.z * 0.003
        blit_soft(surf, self.pos + (self.z * 0.06, self.z * 0.09), 30 * (1.4 - self.z / 300), (0, 0, 0), 150)
        blit_glow(surf, sp, 60, (80, 255, 120), 0.5 + (0.6 if self.flash else 0))
        w, h = 74 * sc, 30 * sc
        body = pygame.Rect(0, 0, w, h)
        body.center = sp
        pygame.draw.ellipse(surf, (70, 76, 90), body.move(0, 3))
        pygame.draw.ellipse(surf, (255, 255, 255) if self.flash else (170, 178, 195), body)
        pygame.draw.ellipse(surf, (110, 118, 135), body, 2)
        dome = pygame.Rect(0, 0, w * 0.42, h * 0.75)
        dome.center = (sp.x, sp.y - h * 0.18)
        pygame.draw.ellipse(surf, (90, 230, 200), dome)
        pygame.draw.ellipse(surf, (200, 255, 240), dome.inflate(-dome.w * 0.55, -dome.h * 0.55).move(-3, -2))
        for i in range(8):
            a = self.spin + i * math.tau / 8
            q = sp + pygame.Vector2(math.cos(a) * w * 0.4, math.sin(a) * h * 0.32 + h * 0.08)
            col = [(255, 80, 80), (255, 220, 80), (80, 255, 120), (80, 180, 255)][(i + int(t * 6)) % 4]
            pygame.draw.circle(surf, col, q, 3)
        if not self.falling and self.hp < 22:
            bw = 50
            pygame.draw.rect(surf, (40, 10, 10), (sp.x - bw / 2, sp.y - h, bw, 4))
            pygame.draw.rect(surf, (90, 255, 120), (sp.x - bw / 2, sp.y - h, bw * max(0, self.hp) / 22, 4))


# ====================== game ======================
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Time Moves Only When You Move - City")
        self.screen = pygame.display.set_mode((W, H))
        self.world = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)
        self.avo = AvocadoSprites()
        self.held_keys = set()
        self.walk_dist = 0.0
        fam = "consolas,dejavusansmono,couriernew,arial"
        self.font = pygame.font.SysFont(fam, 19, bold=True)
        self.small = pygame.font.SysFont(fam, 15)
        self.big = pygame.font.SysFont("arial black,impact,arial", 70, bold=True)
        self.mid = pygame.font.SysFont("arial black,impact,arial", 32, bold=True)
        self.vignette = self.make_vignette()
        self.scanlines = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, 3):
            pygame.draw.line(self.scanlines, (120, 200, 255, 14), (0, y), (W, y))
        self.tint = pygame.Surface((W, H), pygame.SRCALPHA)
        self.add_layer = pygame.Surface((W, H))
        self.shadow_layer = pygame.Surface((W, H), pygame.SRCALPHA)
        self.cloud = self.make_cloud()
        self.clouds = [[random.uniform(-200, W), random.uniform(0, H), random.uniform(0.8, 1.4)] for _ in range(4)]
        self.world_t = 0.0
        bx = 236
        self.hole_btn = pygame.Rect(bx, H - 54, 140, 40)
        self.nuke_btn = pygame.Rect(bx + 148, H - 54, 140, 40)
        self.tank_btn = pygame.Rect(bx + 296, H - 54, 140, 40)
        self.tsunami_btn = pygame.Rect(bx + 444, H - 54, 140, 40)
        self.alien_btn = pygame.Rect(bx + 592, H - 54, 140, 40)
        self.best = 1
        self.state = "menu"
        self.t = 0.0
        self.money = 0
        self.new_game()

    # ---------- setup ----------
    @staticmethod
    def make_vignette():
        sw, sh = 128, 88
        s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for y in range(sh):
            for x in range(sw):
                dx, dy = (x / sw - 0.5) * 2, (y / sh - 0.5) * 2
                d = min(1, math.sqrt(dx * dx * 0.8 + dy * dy * 0.9))
                s.set_at((x, y), (0, 0, 0, int(210 * d ** 2.6)))
        return pygame.transform.smoothscale(s, (W, H))

    def new_game(self):
        self.money = 0
        self.cars_destroyed = 0
        self.buildings_destroyed = 0
        self.hp = 3
        self.reset(1)

    def build_city(self, seed):
        rng = random.Random(seed)
        g = pygame.Surface((W, H))
        g.fill(ASPHALT)
        xs = [0] + [v for x in ROADS_V for v in (x - ROAD_HALF, x + ROAD_HALF)] + [W]
        ys = [0] + [v for y in ROADS_H for v in (y - ROAD_HALF, y + ROAD_HALF)] + [H]
        buildings, lamps, trees = [], [], []
        for i in range(0, len(xs), 2):
            for j in range(0, len(ys), 2):
                block = pygame.Rect(xs[i], ys[j], xs[i + 1] - xs[i], ys[j + 1] - ys[j])
                pygame.draw.rect(g, SIDEWALK_COL, block)
                for k in range(block.left, block.right, 22):
                    pygame.draw.line(g, scale_color(SIDEWALK_COL, 0.88), (k, block.top), (k, block.top + SIDEWALK))
                    pygame.draw.line(g, scale_color(SIDEWALK_COL, 0.88), (k, block.bottom - SIDEWALK), (k, block.bottom))
                inner = block.inflate(-2 * SIDEWALK, -2 * SIDEWALK)
                for x in range(block.left + 30, block.right - 10, 115):
                    lamps += [(x, block.top + 5), (x, block.bottom - 5)]
                if rng.random() < 0.13:
                    pygame.draw.rect(g, PARK, inner)
                    for _ in range(inner.w * inner.h // 25):
                        q = (rng.randrange(inner.left, inner.right), rng.randrange(inner.top, inner.bottom))
                        g.set_at(q, scale_color(PARK, rng.uniform(0.75, 1.3)))
                    # winding path
                    pts = [(inner.left, inner.centery + rng.randint(-20, 20))]
                    for k in range(1, 6):
                        pts.append((inner.left + inner.w * k / 5, inner.centery + rng.randint(-30, 30)))
                    pygame.draw.lines(g, (92, 84, 66), False, pts, 7)
                    pygame.draw.lines(g, (112, 102, 80), False, pts, 3)
                    pygame.draw.circle(g, (40, 90, 120), (inner.centerx + rng.randint(-20, 20), inner.centery), 14)  # pond
                    pygame.draw.circle(g, (70, 130, 160), (inner.centerx - 3, inner.centery - 3), 6)
                    for _ in range(inner.w * inner.h // 1100):
                        p = (rng.randint(inner.left + 8, inner.right - 8), rng.randint(inner.top + 8, inner.bottom - 8))
                        trees.append([pygame.Vector2(p), rng.randint(7, 12)])
                    continue
                pygame.draw.rect(g, LOT, inner)
                for x in range(inner.left + 6, inner.right - 6, 16):   # parking-lot stripes
                    pygame.draw.line(g, scale_color(LOT, 1.25), (x, inner.top + 4), (x, inner.top + 18))
                    pygame.draw.line(g, scale_color(LOT, 1.25), (x, inner.bottom - 18), (x, inner.bottom - 4))
                pygame.draw.rect(g, scale_color(SIDEWALK_COL, 1.35), block, 2)     # curb highlight
                for rect in self.split(inner, rng, 0):
                    rect = rect.inflate(-6, -6)
                    if rect.w > 28 and rect.h > 28:
                        buildings.append(Building(rect, rng))
        # asphalt texture, cracks, stains and manholes
        for _ in range(9000):
            q = (rng.randrange(W), rng.randrange(H))
            if g.get_at(q)[:3] == ASPHALT:
                g.set_at(q, scale_color(ASPHALT, rng.uniform(0.7, 1.35)))
        for _ in range(26):
            q = (rng.randrange(W), rng.randrange(H))
            if g.get_at(q)[:3][0] < 40:
                blit_soft(g, q, rng.randint(8, 18), (12, 12, 16), 90)
        for x in ROADS_V:
            for y in range(40, H, 170):
                q = (x + rng.choice((-20, 20)), y + rng.randint(0, 60))
                pygame.draw.circle(g, (20, 20, 26), q, 6)
                pygame.draw.circle(g, (48, 50, 58), q, 6, 1)
        for y in ROADS_H:
            for x in range(60, W, 200):
                q = (x + rng.randint(0, 60), y + rng.choice((-20, 20)))
                pygame.draw.circle(g, (20, 20, 26), q, 6)
                pygame.draw.circle(g, (48, 50, 58), q, 6, 1)
        # white lane edges
        for y in ROADS_H:
            for yy in (y - ROAD_HALF + 3, y + ROAD_HALF - 3):
                pygame.draw.line(g, (110, 112, 120), (0, yy), (W, yy), 1)
        for x in ROADS_V:
            for xx in (x - ROAD_HALF + 3, x + ROAD_HALF - 3):
                pygame.draw.line(g, (110, 112, 120), (xx, 0), (xx, H), 1)
        # road markings
        for y in ROADS_H:
            for x in range(0, W, 36):
                if all(abs(x + 9 - vx) > ROAD_HALF + 18 for vx in ROADS_V):
                    pygame.draw.line(g, (190, 160, 60), (x, y), (x + 18, y), 2)
        for x in ROADS_V:
            for y in range(0, H, 36):
                if all(abs(y + 9 - hy) > ROAD_HALF + 18 for hy in ROADS_H):
                    pygame.draw.line(g, (190, 160, 60), (x, y), (x, y + 18), 2)
        for x in ROADS_V:
            for y in ROADS_H:
                for yy in range(y - 30, y + 30, 8):
                    pygame.draw.rect(g, (150, 150, 158), (x - ROAD_HALF - 14, yy, 10, 4))
                    pygame.draw.rect(g, (150, 150, 158), (x + ROAD_HALF + 4, yy, 10, 4))
                for xx in range(x - 30, x + 30, 8):
                    pygame.draw.rect(g, (150, 150, 158), (xx, y - ROAD_HALF - 14, 4, 10))
                    pygame.draw.rect(g, (150, 150, 158), (xx, y + ROAD_HALF + 4, 4, 10))
        for p, r in trees:   # tree shadows on the grass
            blit_soft(g, p + SUN * 22, r + 3, (6, 16, 10), 150)
        self.trees = trees
        self.lamps = [pygame.Vector2(l) for l in lamps]
        for l in self.lamps:
            pygame.draw.circle(g, (20, 20, 24), l, 3)
            pygame.draw.line(g, (12, 12, 16), l, l + SUN * 32, 2)
        lights = self.make_lights()
        return g, lights, buildings

    def make_lights(self):
        lights = pygame.Surface((W, H))
        for l in self.lamps:
            blit_glow(lights, l + (0, 4), 70, (255, 180, 100), 0.35)
        return lights

    def break_props(self, pos, radius):
        """Explosions knock down trees and street lamps."""
        pos = pygame.Vector2(pos)
        for tr in list(self.trees):
            if tr[0].distance_to(pos) < radius:
                self.trees.remove(tr)
                for _ in range(10):
                    self.add(P("chunk", tr[0], rand_dir() * random.uniform(50, 200), 15, random.uniform(80, 250), 6,
                               random.uniform(2, 5), 0, random.choice([(40, 92, 54), (60, 120, 70), (70, 50, 30)])))
                pygame.draw.circle(self.ground, (30, 26, 20), tr[0], 4)
        before = len(self.lamps)
        self.lamps = [l for l in self.lamps if l.distance_to(pos) >= radius * 0.8]
        if len(self.lamps) != before:
            self.lights = self.make_lights()

    def split(self, rect, rng, depth):
        if depth > 2 or (rect.w < 120 and rect.h < 120) or (depth > 0 and rng.random() < 0.25):
            return [rect]
        gap = 14
        if rect.w > rect.h:
            cut = rng.randint(int(rect.w * 0.35), int(rect.w * 0.65))
            a = pygame.Rect(rect.x, rect.y, cut - gap // 2, rect.h)
            b = pygame.Rect(rect.x + cut + gap // 2, rect.y, rect.w - cut - gap // 2, rect.h)
        else:
            cut = rng.randint(int(rect.h * 0.35), int(rect.h * 0.65))
            a = pygame.Rect(rect.x, rect.y, rect.w, cut - gap // 2)
            b = pygame.Rect(rect.x, rect.y + cut + gap // 2, rect.w, rect.h - cut - gap // 2)
        return self.split(a, rng, depth + 1) + self.split(b, rng, depth + 1)

    def reset(self, level):
        self.level = level
        self.ground, self.lights, self.buildings = self.build_city(level * 7919 + random.randint(0, 999))
        self.player = pygame.Vector2(ROADS_V[1], (ROADS_H[0] + ROADS_H[1]) / 2)
        self.walls = [b.rect for b in self.buildings]
        self.shots, self.enemies, self.particles, self.trail = [], [], [], []
        self.waves = []
        self.nav = NavGrid()
        self.ai_mem = {"pos": pygame.Vector2(self.player), "t": self.world_t if hasattr(self, "world_t") else 0.0}
        self.player_vel = pygame.Vector2()
        self.prev_player = None
        self.path_budget = 0
        self.fields = []
        self.grenades = []
        self.tanks = []
        self.tank_cd = 0.0
        self.tank_msg = 0.0
        self.holes = []
        self.hole_cd = 0.0
        self.escape_msg = 0.0
        self.consumed = 0
        self.spaghetti = False
        self.slabs = []
        self.shield_on = False
        self.shield = SHIELD_MAX
        self.shield_wait = 0.0
        self.shield_raised_t = -9.0
        self.shield_flash = 0.0
        self.shield_hits = []      # (direction, life) ripples where shots hit
        self.shield_broken = False
        self.popups = []           # floating texts like "REFLECT!"
        self.held = None
        self.tsunami = None
        self.tsunami_cd = 0.0
        self.ufos = []
        self.alien_cd = 0.0
        self.alien_msg = 0.0
        self.ufos_down = 0
        self.abducted = False
        self.grenade_cd = 0.0
        self.max_particles = MAX_PARTICLES
        self.nuke_state = None
        self.nuke_t = 0.0
        self.nuke_flash = 0.0
        self.nuke_death = None
        self.nuked = False
        self.nuke_target = pygame.Vector2(CAM)
        self.knock = pygame.Vector2()
        self.kz = self.kvz = self.kspin = self.kangle = 0.0
        self.cars = []
        lanes = []
        for y in ROADS_H:
            lanes += [("h", y + 16, 1), ("h", y - 16, -1)]
        for x in ROADS_V:
            lanes += [("v", x - 16, 1), ("v", x + 16, -1)]
        for lane in lanes:
            length = W if lane[0] == "h" else H
            for k in range(random.randint(2, 3)):
                along = (k + random.uniform(0, 0.6)) * length / 3
                if lane[0] == "v" and abs(lane[1] - self.player.x) < 30 and abs(along - self.player.y) < 60:
                    continue
                self.cars.append(Car(lane, along))
        self.gun_cd = self.rocket_cd = 0.0
        self.burst = 0.0
        self.time_scale = FROZEN_SCALE
        self.shake = 0.0
        self.inv = 0.0
        self.dead = False
        self.death_t = 0.0
        self.clear_t = None
        self.level_msg = 2.0
        for _ in range(level + 2):
            for _try in range(200):
                if random.random() < 0.5:
                    pos = pygame.Vector2(random.uniform(30, W - 30), random.choice(ROADS_H) + random.uniform(-25, 25))
                else:
                    pos = pygame.Vector2(random.choice(ROADS_V) + random.uniform(-25, 25), random.uniform(70, H - 30))
                if pos.distance_to(self.player) > 330:
                    self.enemies.append(Enemy(pos, level, ROLES[len(self.enemies) % 3]))
                    break

    # ---------- world events ----------
    def add(self, p):
        if len(self.particles) < self.max_particles:
            self.particles.append(p)

    def building_at(self, pos):
        for b in self.buildings:
            if b.solid() and b.rect.collidepoint(pos):
                return b
        return None

    def fx_muzzle(self, pos, col, n=5):
        for _ in range(n):
            self.add(P("spark", pos, rand_dir() * random.uniform(80, 220), 0, 0, random.uniform(0.08, 0.2)))

    def fx_impact(self, pos, col):
        for _ in range(5):
            self.add(P("spark", pos, rand_dir() * random.uniform(60, 200), 0, 0, random.uniform(0.1, 0.25)))
        for _ in range(2):
            self.add(P("chunk", pos, rand_dir() * random.uniform(30, 90), 4, random.uniform(60, 150), 5, 2, 0,
                       scale_color(col, 0.8)))

    def fx_dust_puff(self, pos, n):
        for _ in range(n):
            self.add(P("dust", pos + rand_dir() * 8, rand_dir() * random.uniform(20, 70), 0, 6,
                       random.uniform(0.8, 1.8), random.uniform(5, 9), 14))

    def explosion_fx(self, pos, radius):
        self.add(P("flash", pos, life=0.28, size=radius * 2.2))
        self.add(P("ring", pos, life=0.3, size=radius * 0.9))
        self.waves.append(Shockwave(pos, radius * 3.2))
        for _ in range(26):
            self.add(P("fire", pos + rand_dir() * random.uniform(0, 10), rand_dir() * random.uniform(20, 170),
                       random.uniform(0, 10), random.uniform(20, 110), random.uniform(0.6, 1.4),
                       random.uniform(6, 14), 10))
        for _ in range(12):
            self.add(P("smoke", pos + rand_dir() * 10, rand_dir() * random.uniform(10, 60), 10,
                       random.uniform(10, 40), random.uniform(2.5, 5.5), random.uniform(10, 18), 18, SMOKE))
        for _ in range(22):
            self.add(P("spark", pos, rand_dir() * random.uniform(150, 520), 0, 0, random.uniform(0.2, 0.5)))
        for _ in range(10):
            self.add(P("chunk", pos, rand_dir() * random.uniform(60, 230), 2, random.uniform(150, 430), 10,
                       random.uniform(2, 5), 0, random.choice([(70, 66, 64), (90, 84, 80), (50, 46, 46)])))
        blit_soft(self.ground, pos, radius * 0.75, (8, 6, 6), 170)
        self.shake = max(self.shake, 10)

    def explode(self, pos, radius):
        pos = pygame.Vector2(pos)
        self.break_props(pos, radius * 0.6)
        self.explosion_fx(pos, radius)
        for b in self.buildings:
            if b.state == "up":
                d = rect_dist(pos, b.rect)
                if d < radius:
                    b.damage(7 * (1 - d / radius) + 1, self, pos)
        for c in self.cars:
            d = c.pos.distance_to(pos)
            if d < radius:
                c.blast(pos, 1 - d / radius, self)
        for e in self.enemies:
            if e.alive and e.pos.distance_to(pos) < radius * 0.45:
                self.kill_enemy(e)
        if not self.dead:
            d = self.player.distance_to(pos)
            if d < radius * 0.7:
                self.hurt_player(2 if d < radius * 0.35 else 1)

    def mini_wave(self, pos, friendly):
        self.waves.append(Shockwave(pos, 130, 0.6, 520, hits_player=not friendly))
        self.add(P("flash", pos, life=0.12, size=40))

    def bullet_hit_building(self, b, shot):
        """Every bullet tears pieces off the building; 3 hits bring it down."""
        b.damage(b.max_hp * 0.36 + 0.1, self, shot.pos)
        self.shake = max(self.shake, 4)
        back = -shot.vel.normalize()
        for _ in range(7):
            d = (back + rand_dir() * 0.7)
            d = d.normalize() if d.length() else rand_dir()
            self.add(P("chunk", shot.pos, d * random.uniform(60, 220), random.uniform(5, max(6, b.h * 0.8)),
                       random.uniform(40, 220), 10, random.uniform(3, 8), 0,
                       scale_color(b.roof, random.uniform(0.5, 1.0))))
        for _ in range(6):
            self.add(P("dust", shot.pos + rand_dir() * 4, back * random.uniform(30, 90) + rand_dir() * 20,
                       random.uniform(0, b.h * 0.6), 6, random.uniform(0.8, 1.8), random.uniform(6, 10), 16))
        self.fx_impact(shot.pos, b.roof)
        self.mini_wave(shot.pos, shot.friendly)

    def on_collapse(self, b):
        self.buildings_destroyed += 1
        self.money += int(b.rect.w * b.rect.h * 160)
        self.shake = max(self.shake, 14)
        for _ in range(40):
            self.add(P("dust", b.random_point(), rand_dir() * random.uniform(30, 140), random.uniform(0, b.h), 10,
                       random.uniform(2, 4), random.uniform(10, 18), 24))
        center = pygame.Vector2(b.rect.center)
        for _ in range(16 + b.rect.w * b.rect.h // 1500):
            q = b.random_point()
            out = q - center
            out = out.normalize() if out.length() else rand_dir()
            self.add(P("chunk", q, out * random.uniform(60, 240), random.uniform(b.h * 0.4, b.h),
                       random.uniform(60, 320), 14, random.uniform(7, 16), 0,
                       scale_color(b.roof, random.uniform(0.55, 1.05))))
        self.waves.append(Shockwave(center, 200 + max(b.rect.w, b.rect.h), 0.8, 450))

    def stamp_chunk(self, p):
        pts = [p.pos + pygame.Vector2(math.cos(p.rot + a), math.sin(p.rot + a)) * p.size for a in (0, 2.1, 3.3, 4.9)]
        pygame.draw.polygon(self.ground, scale_color(p.col, 0.75), pts)

    def ls(self, pos):
        """Local time scale at a position (time grenade bubbles)."""
        if not self.fields:
            return 1.0
        k = 1.0
        for f in self.fields:
            k = min(k, f.scale_at(pos))
        return k

    # ----- gravity gun -----
    def gravity_action(self):
        if self.dead or self.nuke_death is not None:
            return
        if self.held:
            return self.throw_held()
        m = pygame.Vector2(pygame.mouse.get_pos())
        best, bd = None, 70
        for c in self.cars:
            if not getattr(c, "consumed", False):
                d = proj(c.pos, c.z).distance_to(m)
                if d < bd and c.pos.distance_to(self.player) < 480:
                    best, bd = ("car", c), d
        for e in self.enemies:
            if e.alive:
                d = proj(e.pos, e.kz).distance_to(m)
                if d < bd and e.pos.distance_to(self.player) < 480:
                    best, bd = ("enemy", e), d
        for sl in self.slabs:
            if sl.alive:
                d = proj(sl.pos, sl.z).distance_to(m)
                if d < bd and sl.pos.distance_to(self.player) < 480:
                    best, bd = ("slab", sl), d
        if best is None:
            b = self.building_at(m)
            if b and m.distance_to(self.player) < 480:
                pt = pygame.Vector2(max(b.rect.left, min(self.player.x, b.rect.right)),
                                    max(b.rect.top, min(self.player.y, b.rect.bottom)))
                b.damage(b.max_hp * 0.3, self, pt)
                sl = Slab(pt, scale_color(b.roof, 0.95), b.h * 0.5, random.uniform(14, 22))
                self.slabs.append(sl)
                best = ("slab", sl)
                for _ in range(8):
                    self.add(P("chunk", pt, rand_dir() * random.uniform(40, 160), b.h * 0.5, random.uniform(50, 200),
                               8, random.uniform(2, 5), 0, b.roof))
                self.fx_dust_puff(pt, 8)
                self.shake = max(self.shake, 6)
        if best:
            kind, obj = best
            if kind == "car" and obj.state == "drive":
                obj.toss()
            obj.held = True
            self.held = best
            self.burst = SHOT_BURST

    def throw_held(self):
        kind, obj = self.held
        self.held = None
        obj.held = False
        m = pygame.Vector2(pygame.mouse.get_pos())
        d = m - obj.pos
        if d.length() < 25:
            d = m - self.player
        dirv = d.normalize() if d.length() > 0 else pygame.Vector2(1, 0)
        if kind == "car":
            obj.vel = dirv * 980
            obj.vz = 140
            obj.z = max(obj.z, 10)
            obj.spin = random.uniform(-800, 800)
        elif kind == "enemy":
            obj.knock = dirv * 1100
            obj.kvz = 180
        else:
            obj.vel = dirv * 1050
            obj.vz = 110
        self.burst = 0.3
        self.shake = max(self.shake, 5)
        self.add(P("flash", proj(obj.pos, 20), life=0.15, size=60))

    def held_screen_pos(self):
        kind, obj = self.held
        if kind == "car":
            return proj(obj.pos, obj.z + 5)
        if kind == "enemy":
            return proj(obj.pos, obj.kz)
        return proj(obj.pos, obj.z)

    def update_held(self, real_dt):
        if not self.held:
            return
        kind, obj = self.held
        gone = (kind == "enemy" and not obj.alive) or (kind == "car" and getattr(obj, "consumed", False)) or \
               (kind == "slab" and not obj.alive) or self.dead
        if gone:
            obj.held = False
            self.held = None
            return
        m = pygame.Vector2(pygame.mouse.get_pos())
        d = m - self.player
        dist = max(55, min(170, d.length()))
        hold = self.player + (d.normalize() if d.length() > 0 else pygame.Vector2(1, 0)) * dist
        obj.pos += (hold - obj.pos) * min(1, real_dt * 10)
        zf = 24 + 4 * math.sin(self.t * 4)
        if kind == "car":
            obj.z, obj.vz = zf, 0
            obj.vel.update(0, 0)
            obj.angle += 50 * real_dt
        elif kind == "enemy":
            obj.kz, obj.kvz = zf, 0
            obj.knock.update(0, 0)
            obj.kangle += 3 * real_dt
        else:
            obj.z, obj.vz = zf, 0
            obj.vel.update(0, 0)
            obj.rot += 2 * real_dt

    def draw_gravity_beam(self, add):
        if not self.held:
            return
        a = self.player
        b = self.held_screen_pos()
        d = b - a
        if d.length() < 1:
            return
        n = pygame.Vector2(-d.y, d.x).normalize()
        pts = []
        for i in range(17):
            u = i / 16
            wob = math.sin(self.t * 25 + u * 12) * 5 * math.sin(u * math.pi)
            pts.append(a + d * u + n * wob)
        pygame.draw.lines(add, (255, 150, 60), False, pts, 3)
        pygame.draw.lines(add, (255, 230, 170), False, pts, 1)
        blit_glow(add, b, 42, (255, 150, 60), 0.7)
        blit_glow(add, a, 20, (255, 170, 80), 0.8)

    # ----- tsunami & aliens -----
    def start_tsunami(self):
        if self.tsunami or self.tsunami_cd > 0 or self.dead or self.nuke_state:
            return
        self.tsunami = Tsunami()

    def start_aliens(self):
        if self.ufos or self.alien_cd > 0 or self.dead or self.nuke_state:
            return
        for i in range(UFO_COUNT):
            self.ufos.append(UFO(i * 140))
        self.alien_msg = 2.5

    def ufo_beam(self, ufo, dt):
        R = 48
        c = ufo.pos
        for car in self.cars:
            if getattr(car, "held", False) or getattr(car, "consumed", False):
                continue
            if car.pos.distance_to(c) < R + 10:
                if car.state == "drive":
                    car.toss()
                car.vel = car.vel.lerp((c - car.pos) * 2, min(1, dt * 4))
                car.vz = GRAVITY * dt
                car.z += 70 * dt
                car.spin = 120
                if car.z > 120:
                    car.consumed = True
                    self.money += 20000
        for e in self.enemies:
            if e.alive and not getattr(e, "held", False) and e.pos.distance_to(c) < R:
                e.knock = (c - e.pos) * 2
                e.kvz = 70 + GRAVITY * dt
                if e.kz > 110:
                    e.alive = False
        if not self.dead and self.player.distance_to(c) < R:
            self.knock = (c - self.player) * 1.5
            self.kvz = 55 + GRAVITY * dt
            if self.kz > 110:
                self.dead = True
                self.abducted = True
                self.hp = 0
                self.best = max(self.best, self.level)
        for b in self.buildings:
            if b.state == "up" and rect_dist(c, b.rect) < R:
                b.damage(3 * dt, self)
                ufo.acc += 30 * dt
                while ufo.acc >= 1:
                    ufo.acc -= 1
                    q = c + rand_dir() * random.uniform(0, R)
                    if b.rect.collidepoint(q):
                        self.add(P("lift", q, (c - q) * 0.6, b.h, 95, random.uniform(1.0, 1.6), random.uniform(3, 7), 0,
                                   scale_color(b.roof, random.uniform(0.6, 1.0))))

    # ----- AI helpers -----
    def predict_player(self, frm, speed):
        """Where you will be when a bullet fired now reaches you."""
        P = pygame.Vector2(self.player)
        t = frm.distance_to(P) / speed
        for _ in range(2):
            t = frm.distance_to(P + self.player_vel * t) / speed
        return P + self.player_vel * min(t, 1.5)

    def squad_alert(self, spotter):
        for e in self.enemies:
            if e is not spotter:
                e.think_t = min(e.think_t, random.uniform(0.05, 0.3))

    def danger_at(self, p):
        d = 0.0
        for h in self.holes:
            dist = p.distance_to(h.pos)
            if dist < 330:
                d += (330 - dist) / 330 * 2
        for s in self.shots:
            if s.friendly and s.rocket and s.vel.length() > 0:
                land = s.pos + s.vel.normalize() * max(0.0, s.range)
                if land.distance_to(p) < 100:
                    d += 1.5
        for f in self.fields:
            if p.distance_to(f.pos) < f.r + 12:
                d += 1.0
        if self.tsunami and self.tsunami.in_water(p):
            d += 0.6
        for tk in self.tanks:
            if p.distance_to(tk.pos) < 70:
                d += 1.0
        return d

    def danger_push(self, p):
        v = pygame.Vector2()
        for h in self.holes:
            d = p - h.pos
            if 0 < d.length() < 330:
                v += d.normalize() * (1 - d.length() / 330) * 1.6
        for s in self.shots:
            if s.friendly and s.rocket and s.vel.length() > 0:
                land = s.pos + s.vel.normalize() * max(0.0, s.range)
                d = p - land
                if 0 < d.length() < 110:
                    v += d.normalize() * 1.2
        for tk in self.tanks:
            d = p - tk.pos
            if 0 < d.length() < 70:
                v += d.normalize()
        return v

    def open_black_hole(self):
        if self.holes or self.hole_cd > 0 or self.dead or self.nuke_state:
            return
        best = None
        for _ in range(60):
            q = self.player + rand_dir() * random.uniform(200, 290)
            if 90 < q.x < W - 90 and 110 < q.y < H - 90:
                best = q
                break
        if best is None:
            best = pygame.Vector2(CAM) if self.player.distance_to(CAM) > 180 else pygame.Vector2(W * 0.25, H * 0.5)
        self.holes.append(BlackHole(best))
        self.add(P("flash", best, life=0.4, size=160))
        self.shake = max(self.shake, 12)

    def consume_player(self):
        if self.dead:
            return
        self.dead = True
        self.spaghetti = True
        self.hp = 0
        self.best = max(self.best, self.level)
        for _ in range(30):
            self.add(P("spark", self.player, rand_dir() * random.uniform(100, 300), 0, 0, random.uniform(0.3, 0.7)))

    def hole_collapsed(self, hole):
        self.hole_cd = HOLE_CD
        self.explosion_fx(hole.pos, 70)
        self.waves.append(Shockwave(hole.pos, 650, 1.4, 700, hits_player=False))
        self.add(P("flash", hole.pos, life=0.5, size=260))
        self.shake = max(self.shake, 20)
        if not self.dead:
            self.money += 1_000_000
            self.escape_msg = 3.0

    def call_tanks(self):
        if self.tank_cd > 0 or self.dead or self.nuke_state:
            return
        for i in range(TANK_COUNT):
            self.tanks.append(Tank(i * 110))
        self.tank_cd = TANK_CD
        self.tank_msg = 2.2

    def throw_grenade(self):
        if self.grenade_cd > 0 or self.dead or self.nuke_death is not None:
            return
        target = pygame.Vector2(pygame.mouse.get_pos())
        d = target - self.player
        if d.length() > 420:
            target = self.player + d.normalize() * 420
        self.grenades.append(Grenade(self.player, target))
        self.grenade_cd = GRENADE_CD
        self.burst = SHOT_BURST

    def launch_nuke(self):
        if self.nuke_state or self.dead:
            return
        self.nuke_state = "countdown"
        self.nuke_t = 3.0
        self.nuke_target = pygame.Vector2(CAM)

    def nuke_impact(self):
        self.nuke_state = "impact"
        self.nuke_flash = 1.0
        self.max_particles = 2600
        pos = self.nuke_target
        self.explosion_fx(pos, 55)                       # small explosion...
        self.waves.append(Shockwave(pos, 1500, 3.0, 900, nuke=True))   # ...huge shockwave
        for _ in range(30):
            self.add(P("fire", pos + rand_dir() * 10, rand_dir() * random.uniform(10, 60), 5,
                       random.uniform(80, 200), random.uniform(1.0, 2.0), random.uniform(10, 18), 14))
        self.shake = 28

    def nuke_hit_player(self, d):
        if self.nuke_death is not None:
            return
        self.nuked = True
        self.knock += d * 1500
        self.kvz += 650
        self.kspin += random.choice((-1, 1)) * 22
        self.nuke_death = 2.6

    def disintegrate(self, b, dirv, speed=1.0):
        """Nuke: the building is ripped apart and thrown with the shockwave."""
        n = min(55, 18 + b.rect.w * b.rect.h // 500)
        for _ in range(n):
            q = b.random_point()
            d = dirv + rand_dir() * 0.45
            d = d.normalize() if d.length() else dirv
            self.add(P("chunk", q, d * random.uniform(280, 700) * speed, random.uniform(0, b.h),
                       random.uniform(80, 420), 14, random.uniform(5, 15), 0,
                       scale_color(b.roof, random.uniform(0.5, 1.05))))
        for _ in range(10):
            self.add(P("dust", b.random_point(), dirv * random.uniform(200, 420) + rand_dir() * 40,
                       random.uniform(0, b.h), 10, random.uniform(1.5, 3), random.uniform(12, 22), 30))
        for _ in range(int(b.h // 25)):
            self.add(P("glass", b.random_point(), dirv * random.uniform(300, 600) + rand_dir() * 80,
                       random.uniform(5, b.h), random.uniform(50, 200), 1.5, 2))
        if b.state == "up":
            self.buildings_destroyed += 1
            self.money += int(b.rect.w * b.rect.h * 160)
        b.state = "rubble"
        self.stamp_rubble(b, quiet=True)

    def stamp_rubble(self, b, quiet=False):
        r = b.rect
        pygame.draw.rect(self.ground, (38, 36, 38), r.inflate(10, 10), border_radius=8)
        for _ in range(r.w * r.h // 60):
            c = pygame.Vector2(random.uniform(r.left - 4, r.right + 4), random.uniform(r.top - 4, r.bottom + 4))
            s = random.uniform(3, 9)
            pts = [c + pygame.Vector2(math.cos(a), math.sin(a)) * s * random.uniform(0.6, 1.2)
                   for a in (0, 1.6, 3.0, 4.6)]
            pygame.draw.polygon(self.ground, scale_color(b.roof, random.uniform(0.35, 0.8)), pts)
        blit_soft(self.ground, r.center, min(70, max(r.w, r.h) // 2), (10, 8, 8), 110)
        if quiet:
            return
        for _ in range(50):
            self.add(P("dust", b.random_point(), rand_dir() * random.uniform(40, 160), 0, 12,
                       random.uniform(2.5, 5), random.uniform(12, 20), 26))
        for _ in range(3):
            self.add(P("fire", b.random_point(), rand_dir() * 10, 0, 25, random.uniform(0.8, 1.4), 9, 8))

    def kill_enemy(self, e):
        e.alive = False
        self.money += 5000
        for _ in range(16):
            self.add(P("spark", e.pos, rand_dir() * random.uniform(100, 320), 0, 0, random.uniform(0.2, 0.5)))
        for _ in range(8):
            self.add(P("chunk", e.pos, rand_dir() * random.uniform(50, 150), 4, random.uniform(100, 260), 8, 3, 0,
                       random.choice([ENEMY_COL, (110, 20, 40), (60, 60, 64)])))
        self.add(P("ring", e.pos, life=0.4, size=50))
        blit_soft(self.ground, e.pos, 14, (12, 8, 8), 150)
        self.shake = max(self.shake, 6)

    # ----- shield -----
    def raise_shield(self):
        if self.dead or self.nuke_death is not None or self.shield_on:
            return
        if self.shield > 8 and not self.shield_broken:
            self.shield_on = True
            self.shield_raised_t = self.t
            self.add(P("ring", self.shield_center(), life=0.25, size=SHIELD_R * 1.6))

    def lower_shield(self):
        if self.shield_on:
            self.shield_on = False
            self.shield_wait = SHIELD_DELAY * 0.5

    def toggle_shield(self):   # kept for tests / other callers
        if self.shield_on:
            self.lower_shield()
        else:
            self.raise_shield()

    def shield_center(self):
        return proj(self.player, self.kz + 14)

    def shield_absorb(self, cost, from_pos=None):
        """Returns True if the shield took the hit."""
        if not self.shield_on:
            return False
        self.shield -= cost
        self.shield_flash = 0.18
        self.shield_wait = SHIELD_DELAY
        if from_pos is not None:
            d = pygame.Vector2(from_pos) - self.player
            if d.length() > 0:
                self.shield_hits.append([d.normalize(), 0.35])
        self.shake = max(self.shake, 3)
        if self.shield <= 0:
            self.shield = 0
            self.shield_on = False
            self.shield_broken = True
            self.shield_wait = SHIELD_DELAY * 2.2
            c = self.shield_center()
            for _ in range(30):
                self.add(P("glass", c + rand_dir() * SHIELD_R, rand_dir() * random.uniform(80, 240),
                           random.uniform(5, 25), random.uniform(40, 160), 1.2, 2))
            self.add(P("ring", c, life=0.4, size=SHIELD_R * 2.5))
            self.popups.append(["SHIELD BROKEN", pygame.Vector2(c), 1.2, (255, 120, 120)])
            self.shake = max(self.shake, 9)
        return True

    def shield_block(self, shot):
        """An enemy shot touched the bubble: reflect it (perfect timing) or destroy it."""
        c = self.shield_center()
        if self.t - self.shield_raised_t < SHIELD_PARRY:
            shot.friendly = True
            shot.vel = -shot.vel
            shot.pos = self.player + (shot.pos - self.player).normalize() * (SHIELD_R + 4) \
                if (shot.pos - self.player).length() > 0 else shot.pos
            if shot.rocket:
                shot.range = 900
            shot.trail = []
            self.shield_flash = 0.25
            self.popups.append(["REFLECT!", pygame.Vector2(c) + (0, -30), 0.9, (140, 255, 255)])
            self.money += 2000
            return
        if self.shield_absorb(30 if shot.rocket else 10, shot.pos):
            if shot.rocket:
                self.explosion_fx(shot.pos, 45)
                self.waves.append(Shockwave(shot.pos, 120, 0.5, 520, hits_player=False))
            else:
                for _ in range(6):
                    self.add(P("spark", shot.pos, rand_dir() * random.uniform(80, 220), 10, 0, random.uniform(0.1, 0.3)))
            shot.alive = False

    def update_shield(self, dt, real_dt):
        self.shield_flash = max(0, self.shield_flash - real_dt)
        for h in self.shield_hits:
            h[1] -= real_dt
        self.shield_hits = [h for h in self.shield_hits if h[1] > 0]
        for pu in self.popups:
            pu[2] -= real_dt
            pu[1].y -= 30 * real_dt
        self.popups = [pu for pu in self.popups if pu[2] > 0]
        if self.shield_on:
            self.shield -= SHIELD_DRAIN * dt
            if self.shield <= 0:
                self.shield_absorb(0.01)
        else:
            self.shield_wait -= dt
            if self.shield_wait <= 0:
                self.shield = min(SHIELD_MAX, self.shield + SHIELD_REGEN * dt)
                if self.shield_broken and self.shield > SHIELD_MAX * 0.35:
                    self.shield_broken = False

    def draw_shield(self, surf):
        if not self.shield_on or self.dead:
            return
        c = self.shield_center()
        frac = self.shield / SHIELD_MAX
        flicker = frac < 0.25 and int(self.t * 18) % 3 == 0
        spr = shield_sprite()
        pulse = 0.85 + 0.15 * math.sin(self.t * 6)
        spr.set_alpha(int(255 * (0.5 + 0.4 * frac) * pulse * (0.4 if flicker else 1)))
        surf.blit(spr, spr.get_rect(center=c))
        blit_glow(surf, c, SHIELD_R * 1.6, SHIELD_COL, 0.1 + (0.3 if self.shield_flash else 0))
        for d, life in self.shield_hits:   # ripples where shots hit
            k = life / 0.35
            a = math.atan2(-d.y, d.x)
            rr = pygame.Rect(0, 0, SHIELD_R * 2 + 6, SHIELD_R * 2 + 6)
            rr.center = c
            pygame.draw.arc(surf, scale_color((230, 255, 255), k), rr, a - 0.7, a + 0.7, 3)
            blit_glow(surf, c + d * SHIELD_R, 14, SHIELD_COL, k * 0.5)

    def draw_shield_hud(self, surf):
        x, y = 16, H - 118
        panel = pygame.Surface((210, 28), pygame.SRCALPHA)
        panel.fill((5, 8, 16, 170))
        surf.blit(panel, (x, y))
        frac = self.shield / SHIELD_MAX
        col = (255, 110, 110) if self.shield_broken else (SHIELD_COL if self.shield_on else (120, 170, 200))
        c = (x + 18, y + 14)
        pts = [(c[0], c[1] - 9), (c[0] + 8, c[1] - 5), (c[0] + 7, c[1] + 4), (c[0], c[1] + 9),
               (c[0] - 7, c[1] + 4), (c[0] - 8, c[1] - 5)]
        if self.shield_on:
            blit_glow(surf, c, 22, SHIELD_COL, 0.6)
        pygame.draw.polygon(surf, col, pts, 0 if self.shield_on else 2)
        label = "SHIELD BROKEN" if self.shield_broken else ("SHIELD ON" if self.shield_on else "SHIELD [HOLD SHIFT]")
        surf.blit(self.small.render(label, True, col), (x + 34, y + 1))
        pygame.draw.rect(surf, (30, 36, 56), (x + 34, y + 18, 166, 6), border_radius=3)
        pygame.draw.rect(surf, col, (x + 34, y + 18, max(4, 166 * frac), 6), border_radius=3)

    def hurt_player(self, n):
        if self.inv > 0 or self.dead or self.nuke_death is not None:
            return
        if self.shield_absorb(22 * n):   # explosions, cars, waves... the shield takes it
            self.inv = 0.25
            return
        self.hp -= n
        self.inv = 0.9
        self.shake = max(self.shake, 12)
        if self.hp <= 0:
            self.dead = True
            self.best = max(self.best, self.level)
            self.explosion_fx(self.player, 90)
            self.add(P("ring", self.player, life=0.9, size=170))

    # ---------- loop ----------
    def run(self):
        while True:
            real_dt = min(self.clock.tick(FPS) / 1000, 0.05)
            self.t += real_dt
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    self.held_keys.add(getattr(e, "scancode", -1))
                    self.held_keys.add(("k", e.key))
                elif e.type == pygame.KEYUP:
                    self.held_keys.discard(getattr(e, "scancode", -1))
                    self.held_keys.discard(("k", e.key))
                elif e.type in (getattr(pygame, "WINDOWFOCUSLOST", -1), getattr(pygame, "ACTIVEEVENT", -1)):
                    self.held_keys.clear()
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    pygame.quit()
                    return
                if self.state == "menu":
                    if e.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                        self.state = "play"
                        self.level_msg = 2.0
                elif e.type == pygame.KEYDOWN and e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.raise_shield()
                elif e.type == pygame.KEYUP and e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.lower_shield()
                elif e.type == pygame.KEYDOWN and key_is(e, "r") and self.dead:
                    self.new_game()
                elif e.type == pygame.KEYDOWN and key_is(e, "n"):
                    self.launch_nuke()
                elif e.type == pygame.KEYDOWN and key_is(e, "t"):
                    self.call_tanks()
                elif e.type == pygame.KEYDOWN and key_is(e, "b"):
                    self.open_black_hole()
                elif e.type == pygame.KEYDOWN and key_is(e, "f"):
                    self.gravity_action()
                elif e.type == pygame.KEYDOWN and key_is(e, "y"):
                    self.start_tsunami()
                elif e.type == pygame.KEYDOWN and key_is(e, "u"):
                    self.start_aliens()
                elif e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.throw_grenade()
                elif e.type == pygame.MOUSEBUTTONDOWN and not self.dead:
                    if e.button == 1 and self.nuke_btn.collidepoint(e.pos):
                        self.launch_nuke()
                    elif e.button == 1 and self.tank_btn.collidepoint(e.pos):
                        self.call_tanks()
                    elif e.button == 1 and self.hole_btn.collidepoint(e.pos):
                        self.open_black_hole()
                    elif e.button == 1 and self.tsunami_btn.collidepoint(e.pos):
                        self.start_tsunami()
                    elif e.button == 1 and self.alien_btn.collidepoint(e.pos):
                        self.start_aliens()
                    elif e.button == 1 and self.held:
                        self.throw_held()
                    elif e.button == 1:
                        self.fire(False)
                    elif e.button == 3:
                        self.fire(True)
                    elif e.button == 2:
                        self.throw_grenade()
            if self.state == "play":
                if pygame.mouse.get_pressed()[0] and not self.dead and \
                        not self.nuke_btn.collidepoint(pygame.mouse.get_pos()) and \
                        not self.tank_btn.collidepoint(pygame.mouse.get_pos()) and \
                        not self.hole_btn.collidepoint(pygame.mouse.get_pos()) and \
                        not self.tsunami_btn.collidepoint(pygame.mouse.get_pos()) and \
                        not self.alien_btn.collidepoint(pygame.mouse.get_pos()) and \
                        not self.held and self.nuke_death is None:
                    self.fire(False)
                self.update(real_dt)
            self.draw()

    def fire(self, rocket):
        if (self.rocket_cd if rocket else self.gun_cd) > 0:
            return
        # enemies hear gunfire: they learn roughly where you are
        self.ai_mem["pos"] = self.player + rand_dir() * random.uniform(0, 40)
        self.ai_mem["t"] = self.world_t
        target = pygame.Vector2(pygame.mouse.get_pos())
        aim = target - self.player
        if aim.length() < 1:
            return
        start = self.player + aim.normalize() * (UNIT_R + 6)
        if rocket:
            self.shots.append(Shot(start, aim, ROCKET_SPEED, True, True, target))
            self.rocket_cd = ROCKET_CD
            self.shake = max(self.shake, 5)
            self.fx_muzzle(start, CYAN, 10)
        else:
            self.shots.append(Shot(start, aim + rand_dir() * aim.length() * 0.03, BULLET_SPEED, True))
            self.gun_cd = GUN_CD
            self.shake = max(self.shake, 2)
            self.fx_muzzle(start, CYAN)
        self.burst = SHOT_BURST

    def update(self, real_dt):
        self.level_msg = max(0, self.level_msg - real_dt)
        self.shake = max(0, self.shake - real_dt * 30)
        self.inv = max(0, self.inv - real_dt)

        self.nuke_flash = max(0, self.nuke_flash - real_dt * 0.9)
        if self.nuke_state == "countdown":
            self.nuke_t -= real_dt
            if self.nuke_t <= 0:
                self.nuke_impact()
        elif self.nuke_state == "impact":
            self.nuke_t += real_dt
        if self.nuke_death is not None and not self.dead:
            self.nuke_death -= real_dt
            if self.nuke_death <= 0:
                self.dead = True
                self.hp = 0
                self.best = max(self.best, self.level)

        moving = False
        move = pygame.Vector2()
        if not self.dead and self.nuke_death is None:
            keys = pygame.key.get_pressed()
            hk = self.held_keys

            def down(ch):
                return PHYS[ch] in hk or ("k", getattr(pygame, "K_" + ch)) in hk

            move = pygame.Vector2(
                (down("d") or keys[pygame.K_RIGHT]) - (down("a") or keys[pygame.K_LEFT]),
                (down("s") or keys[pygame.K_DOWN]) - (down("w") or keys[pygame.K_UP]))
            # safety: if Shift was released while the window wasn't listening, drop the shield
            if self.shield_on and not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                self.lower_shield()
            moving = move.length() > 0
        self.burst = max(0, self.burst - real_dt)
        if self.dead:
            self.death_t += real_dt
            target = 0.25
        elif self.nuke_state == "impact":
            target = 0.4   # forced slow motion while the city is blown away
        else:
            target = 1.0 if (moving or self.burst > 0) else FROZEN_SCALE
            if self.holes:
                target = max(target, 0.3)   # the black hole doesn't let time stop
        self.time_scale = lerp(self.time_scale, target, min(1, real_dt * 14))
        dt = real_dt * self.time_scale
        self.world_t += dt

        self.walls = [b.rect for b in self.buildings if b.solid()]
        if moving:
            move_circle(self.player, move.normalize() * PLAYER_SPEED * real_dt, UNIT_R, self.walls)
            self.trail.append([pygame.Vector2(self.player), 0.35])
            self.walk_dist += PLAYER_SPEED * real_dt
        for t in self.trail:
            t[1] -= real_dt
        self.trail = [t for t in self.trail if t[1] > 0]
        self.gun_cd = max(0, self.gun_cd - dt)
        self.rocket_cd = max(0, self.rocket_cd - dt)

        self.grenade_cd = max(0, self.grenade_cd - dt)
        for gr in self.grenades:
            gr.update(dt, self)
        self.grenades = [gr for gr in self.grenades if gr.alive]
        for f in self.fields:
            f.update(dt, self)
        self.fields = [f for f in self.fields if f.alive]
        ls = self.ls
        self.tank_cd = max(0, self.tank_cd - dt)
        self.tank_msg = max(0, self.tank_msg - real_dt)
        for tk in self.tanks:
            tk.update(dt * ls(tk.pos), self)
        self.tanks = [tk for tk in self.tanks if tk.alive]
        self.hole_cd = max(0, self.hole_cd - dt)
        self.escape_msg = max(0, self.escape_msg - real_dt)
        for hole in self.holes:
            hole.update(dt, self)
        self.holes = [hole for hole in self.holes if hole.alive]
        self.update_held(real_dt)
        self.update_shield(dt, real_dt)
        for sl in self.slabs:
            sl.update(dt * ls(sl.pos), self)
        self.slabs = [sl for sl in self.slabs if sl.alive]
        self.tsunami_cd = max(0, self.tsunami_cd - dt)
        if self.tsunami:
            self.tsunami.update(dt, real_dt, self)
            if not self.tsunami.alive:
                self.tsunami = None
                self.tsunami_cd = TSUNAMI_CD
        self.alien_cd = max(0, self.alien_cd - dt)
        self.alien_msg = max(0, self.alien_msg - real_dt)
        for u in self.ufos:
            u.update(dt * ls(u.pos), self)
        if self.ufos:
            self.ufos = [u for u in self.ufos if u.alive]
            if not self.ufos:
                self.alien_cd = ALIEN_CD
        if any(getattr(c, "consumed", False) for c in self.cars):
            self.cars = [c for c in self.cars if not getattr(c, "consumed", False)]
        for b in self.buildings:
            b.update(dt * ls(b.rect.center), self)
        for c in self.cars:
            c.update(dt * ls(c.pos), self)
        # AI bookkeeping: navigation grid, path budget, how fast you're moving (for aiming ahead)
        self.nav.update(self)
        self.path_budget = 2
        if self.prev_player is not None and dt > 1e-4:
            inst = (self.player - self.prev_player) / dt
            if inst.length() > 320:
                inst.scale_to_length(320)
            self.player_vel = self.player_vel.lerp(inst, 0.2)
        self.prev_player = pygame.Vector2(self.player)
        if not self.dead:
            for e in self.enemies:
                if e.alive:
                    e.update(dt * ls(e.pos), self)
        for s in list(self.shots):
            if s.alive:
                s.update(dt * ls(s.pos), self)
        # your bullets can cancel enemy bullets
        for s in self.shots:
            if s.alive and s.friendly and not s.rocket:
                for o in self.shots:
                    if o.alive and not o.friendly and s.pos.distance_to(o.pos) < 11:
                        s.alive = False
                        o.boom(self) if o.rocket else setattr(o, "alive", False)
                        self.fx_muzzle(o.pos, BULLET_ENEMY, 8)
        for wv in self.waves:
            wv.update(dt, self)
        if not self.dead or self.nuked:
            pl = pygame.Vector2(self.player)
            holder = self
            holder.pos = pl
            slam = knock_update(holder, dt, [] if self.nuked else self.walls, UNIT_R)
            self.player = holder.pos
            if slam > 330 and not self.nuked:
                self.hurt_player(1)
                self.fx_impact(self.player, (200, 200, 200))
        if self.fields:
            for p in self.particles:
                p.update(dt * ls(p.pos), self)
        else:
            for p in self.particles:
                p.update(dt, self)
        self.waves = [wv for wv in self.waves if wv.alive]

        self.shots = [s for s in self.shots if s.alive]
        self.enemies = [e for e in self.enemies if e.alive]
        self.particles = [p for p in self.particles if p.life > 0]
        self.buildings = [b for b in self.buildings if b.state != "rubble"]

        if not self.enemies and not self.dead and not self.nuke_state and not self.holes \
                and not self.ufos and not self.tsunami:
            if self.clear_t is None:
                self.clear_t = 2.0
            self.clear_t -= real_dt
            if self.clear_t <= 0:
                self.reset(self.level + 1)

    # ---------- drawing ----------
    def frozen_amount(self):
        if self.state != "play":
            return 1.0
        return max(0.0, min(1.0, 1 - (self.time_scale - FROZEN_SCALE) / (1 - FROZEN_SCALE)))

    def text(self, surf, txt, font, col, center, alpha=255, glow_col=None):
        img = font.render(txt, True, col)
        rect = img.get_rect(center=center)
        if glow_col:
            g = font.render(txt, True, glow_col)
            g.set_alpha(int(alpha * 0.35))
            for off in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                surf.blit(g, rect.move(off))
        img.set_alpha(alpha)
        surf.blit(img, rect)

    def draw_player(self, surf):
        for pos, life in self.trail:
            k = life / 0.35
            pygame.draw.circle(surf, scale_color((120, 230, 90), k * 0.25), proj(pos, 4), UNIT_R * k * 0.7)
        if self.inv > 0 and int(self.t * 20) % 2 and not self.nuked:
            return
        aim = pygame.Vector2(pygame.mouse.get_pos()) - self.player
        aim_n = aim.normalize() if aim.length() > 0 else pygame.Vector2(1, 0)
        facing = 1 if aim.x >= 0 else -1
        z = self.kz
        pos = self.player
        walking = bool(self.trail) and self.trail[-1][1] > 0.3
        if z > 0:
            pose, phase = "fly", int(self.t * 12) % 8
        elif self.inv > 0.45:
            pose, phase = "hurt", 0
        elif walking:
            pose, phase = "walk", int(self.walk_dist / 7) % 8
        else:
            pose, phase = "idle", int(self.t * 4) % 8
        blink = (self.t % 3.3) > 3.17
        cape_i = int(self.t * (12 if walking or z > 0 else 4)) % 6
        img = self.avo.get(pose, phase, blink, cape_i, facing)

        # shadow
        A = AVO_SCALE
        pygame.draw.ellipse(surf, (4, 4, 8), (pos.x + SUN.x * (z + 24 * A) - 14 * A, pos.y + SUN.y * (z + 24 * A) - 7 * A,
                                              28 * A, 14 * A))
        feet = proj(pos, z)
        bob = abs(math.sin(self.walk_dist / 7 / 8 * math.tau)) * 2.5 if walking else 0
        if z > 0:
            img = pygame.transform.rotozoom(img, -math.degrees(self.kangle), 1 + z * 0.004)
            rect = img.get_rect(center=(feet.x, feet.y - AVO_H * 0.45 * A))
            body_off = pygame.Vector2(0, 0)
        else:
            rect = img.get_rect(midbottom=(feet.x, feet.y + 3 * A - bob))
            body_off = None
        blit_glow(surf, feet - (0, 30 * A), 40 * A, (120, 230, 90), 0.35)
        surf.blit(img, rect)

        # front arm holding the blaster (drawn live so it follows the mouse exactly)
        if body_off is None:
            shoulder = pygame.Vector2(feet.x + facing * 7 * A, feet.y - bob - 34 * A)
        else:
            shoulder = pygame.Vector2(rect.center)
        recoil = 3 if self.gun_cd > GUN_CD * 0.6 else 0
        hand = shoulder + aim_n * (11 * A - recoil)
        pygame.draw.line(surf, OUTLINE, shoulder, hand, 2)
        tip = hand + aim_n * 15 * A
        nrm = pygame.Vector2(-aim_n.y, aim_n.x)
        body = [hand - nrm * 2.2, tip - nrm * 1.8, tip + nrm * 1.8, hand + nrm * 2.2]
        pygame.draw.polygon(surf, (40, 44, 56), body)
        pygame.draw.polygon(surf, (16, 16, 22), body, 1)
        pygame.draw.line(surf, (120, 130, 160), hand + aim_n * 3 - nrm, tip - nrm, 1)
        pygame.draw.circle(surf, CYAN, tip, 2)
        if recoil:
            blit_glow(surf, tip + aim_n * 4, 18, CYAN, 1.0)
        pygame.draw.circle(surf, OUTLINE, hand, 3)
        pygame.draw.circle(surf, (255, 255, 255), hand, 2.2)

    def draw_tree(self, surf, p, r):
        top = proj(p, 13)
        pygame.draw.line(surf, (70, 50, 32), p, top, 4)
        for z, k, col in ((13, 1.0, (30, 74, 42)), (19, 0.85, (44, 100, 58)), (25, 0.55, (70, 140, 80))):
            pygame.draw.circle(surf, col, proj(p, z), r * k)

    def draw_lamp(self, surf, l):
        top = proj(l, 32)
        pygame.draw.line(surf, (70, 72, 80), l, top, 2)
        pygame.draw.circle(surf, (255, 230, 180), top, 3)
        blit_glow(surf, top, 14, (255, 200, 130), 0.9)

    @staticmethod
    def make_cloud():
        s = pygame.Surface((120, 80), pygame.SRCALPHA)
        rng = random.Random(7)
        for _ in range(14):
            c = (rng.randint(30, 90), rng.randint(25, 55))
            r = rng.randint(14, 26)
            for i in range(r, 0, -2):
                a = int(30 * (1 - i / r) + 6)
                pygame.draw.circle(s, (0, 0, 12, min(255, a)), c, i)
        return pygame.transform.smoothscale(s, (480, 320))

    def draw_clouds(self, w):
        for c in self.clouds:
            x = (c[0] + self.world_t * 12 * c[2]) % (W + 600) - 500
            y = c[1] + math.sin(self.world_t * 0.05 + c[2]) * 30 - 160
            w.blit(self.cloud, (x, y))

    def bloom(self, w):
        """Soft glow around bright things (lights, fire, neon). Recomputed every other frame."""
        self._bloom_n = getattr(self, "_bloom_n", 0) + 1
        if self._bloom_n % 2 or getattr(self, "_bloom", None) is None:
            small = pygame.transform.smoothscale(w, (W // 6, H // 6))
            small.fill((88, 88, 88), special_flags=pygame.BLEND_RGB_SUB)      # keep only bright pixels
            small.blit(small, (0, 0), special_flags=pygame.BLEND_RGB_ADD)    # x2 intensity
            tiny = pygame.transform.smoothscale(small, (W // 16, H // 16))
            small = pygame.transform.smoothscale(tiny, (W // 6, H // 6))
            self._bloom = pygame.transform.smoothscale(small, (W, H))
        w.blit(self._bloom, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def draw_shadows(self, w):
        sl = self.shadow_layer
        sl.fill((0, 0, 0, 0))
        for b in self.buildings:
            if b.state == "rubble":
                continue
            r = b.rect
            o = SUN * b.h
            pts = [r.topleft, r.topright, r.topright + o, r.bottomright + o, r.bottomleft + o, r.bottomleft]
            pygame.draw.polygon(sl, (0, 0, 10, 255), pts)
        sl.set_alpha(115)
        w.blit(sl, (0, 0))

    def draw_radiation(self, surf, c, r, col, bg):
        pygame.draw.circle(surf, bg, c, r)
        for i in range(3):
            a0 = math.radians(90 + i * 120 - 30)
            pts = [c] + [c + pygame.Vector2(math.cos(a0 + j * math.radians(60) / 8),
                                            -math.sin(a0 + j * math.radians(60) / 8)) * (r - 2) for j in range(9)]
            pygame.draw.polygon(surf, col, pts)
        pygame.draw.circle(surf, bg, c, r * 0.32)
        pygame.draw.circle(surf, col, c, r * 0.2)

    def draw_grenade_hud(self, surf):
        x, y = 16, H - 46
        panel = pygame.Surface((210, 34), pygame.SRCALPHA)
        panel.fill((5, 8, 16, 170))
        surf.blit(panel, (x, y))
        ready = self.grenade_cd <= 0
        col = FIELD_COL if ready else (90, 80, 120)
        c = pygame.Vector2(x + 18, y + 17)
        if ready:
            blit_glow(surf, c, 22, FIELD_COL, 0.5 + 0.3 * math.sin(self.t * 5))
        pygame.draw.circle(surf, col, c, 9, 2)
        pygame.draw.line(surf, col, c, c + (0, -6), 2)
        pygame.draw.line(surf, col, c, c + (4, 2), 2)
        surf.blit(self.small.render("TIME GRENADE [ENTER]", True, col), (x + 34, y + 3))
        frac = 1 - self.grenade_cd / GRENADE_CD
        pygame.draw.rect(surf, (30, 36, 56), (x + 34, y + 21, 166, 6), border_radius=3)
        pygame.draw.rect(surf, col, (x + 34, y + 21, max(6, 166 * frac), 6), border_radius=3)

    def draw_simple_button(self, surf, b, label, ready, cd_frac, base, edge, glow, icon):
        ready = ready and not self.dead and not self.nuke_state
        hover = b.collidepoint(pygame.mouse.get_pos()) and ready
        col = scale_color(base, 1.35) if hover else (base if ready else scale_color(base, 0.45))
        if ready:
            blit_glow(surf, b.center, 70, glow, 0.45 if hover else 0.2)
        pygame.draw.rect(surf, (8, 10, 16), b.move(0, 4), border_radius=10)
        pygame.draw.rect(surf, col, b, border_radius=10)
        if not ready and 0 < cd_frac < 1:
            pygame.draw.rect(surf, scale_color(base, 0.9), (b.x, b.y, b.w * (1 - cd_frac), b.h), border_radius=10)
        pygame.draw.rect(surf, edge if ready else scale_color(edge, 0.5), b, 3, border_radius=10)
        c = pygame.Vector2(b.left + 20, b.centery)
        if icon == "wave":
            pts = [c + (-12 + i * 3, math.sin(self.t * 4 + i * 0.9) * 4) for i in range(9)]
            pygame.draw.lines(surf, (220, 240, 255), False, pts, 3)
            pygame.draw.circle(surf, (255, 255, 255), pts[-1], 3)
        else:
            pygame.draw.ellipse(surf, (190, 200, 210), (c.x - 13, c.y - 3, 26, 9))
            pygame.draw.ellipse(surf, (90, 230, 200), (c.x - 6, c.y - 8, 12, 9))
            for i in range(3):
                pygame.draw.circle(surf, (80, 255, 120), (c.x - 7 + i * 7, c.y + 2), 1)
        t = self.small.render(label, True, (240, 245, 255))
        surf.blit(t, t.get_rect(midleft=(b.left + 38, b.centery)))

    def draw_gravity_hud(self, surf):
        x, y = 16, H - 86
        panel = pygame.Surface((210, 30), pygame.SRCALPHA)
        panel.fill((5, 8, 16, 170))
        surf.blit(panel, (x, y))
        col = (255, 170, 80) if self.held else (200, 150, 100)
        pygame.draw.circle(surf, col, (x + 18, y + 15), 8, 2)
        pygame.draw.circle(surf, col, (x + 18, y + 15), 3)
        label = "THROW: F / CLICK" if self.held else "GRAVITY GUN [F]"
        surf.blit(self.small.render(label, True, col), (x + 34, y + 7))

    def draw_hole_button(self, surf):
        b = self.hole_btn
        ready = not self.holes and self.hole_cd <= 0 and not self.dead and not self.nuke_state
        hover = b.collidepoint(pygame.mouse.get_pos()) and ready
        base = (60, 30, 110) if ready else (36, 28, 50)
        if hover:
            base = (90, 50, 160)
        if ready:
            blit_glow(surf, b.center, 70, (150, 80, 255), 0.45 if hover else 0.2)
        pygame.draw.rect(surf, (10, 6, 18), b.move(0, 4), border_radius=10)
        pygame.draw.rect(surf, base, b, border_radius=10)
        if self.hole_cd > 0 and not self.holes:
            frac = 1 - self.hole_cd / HOLE_CD
            pygame.draw.rect(surf, (80, 50, 130), (b.x, b.y, b.w * frac, b.h), border_radius=10)
        pygame.draw.rect(surf, (200, 160, 255) if ready else (90, 80, 110), b, 3, border_radius=10)
        c = pygame.Vector2(b.left + 22, b.centery)
        for k, col in enumerate([(255, 190, 120), (190, 120, 255)]):
            rect = pygame.Rect(c.x - 13 + k * 2, c.y - 7 + k, 26 - k * 4, 14 - k * 2)
            pygame.draw.arc(surf, col, rect, self.t * 3 + k * 3, self.t * 3 + k * 3 + 4, 2)
        pygame.draw.circle(surf, (0, 0, 0), c, 6)
        pygame.draw.circle(surf, (255, 235, 200), c, 7, 1)
        t = self.small.render("B.HOLE [B]", True, (240, 230, 255))
        surf.blit(t, t.get_rect(midleft=(b.left + 38, b.centery)))

    def draw_tank_button(self, surf):
        b = self.tank_btn
        ready = self.tank_cd <= 0 and not self.dead and not self.nuke_state
        hover = b.collidepoint(pygame.mouse.get_pos()) and ready
        base = (60, 110, 45) if ready else (40, 52, 38)
        if hover:
            base = (85, 150, 60)
        if ready:
            blit_glow(surf, b.center, 70, (90, 200, 70), 0.45 if hover else 0.2)
        pygame.draw.rect(surf, (10, 16, 10), b.move(0, 4), border_radius=10)
        pygame.draw.rect(surf, base, b, border_radius=10)
        if not ready and self.tank_cd > 0:
            frac = 1 - self.tank_cd / TANK_CD
            pygame.draw.rect(surf, (70, 120, 55), (b.x, b.y, b.w * frac, b.h), border_radius=10)
        pygame.draw.rect(surf, (190, 230, 140) if ready else (90, 110, 80), b, 3, border_radius=10)
        # little tank icon
        ix, iy = b.left + 12, b.centery
        pygame.draw.rect(surf, (25, 30, 22), (ix, iy - 7, 24, 14), border_radius=3)
        pygame.draw.rect(surf, (150, 190, 110), (ix + 2, iy - 5, 20, 10), border_radius=2)
        pygame.draw.circle(surf, (25, 30, 22), (ix + 11, iy), 5)
        pygame.draw.line(surf, (25, 30, 22), (ix + 11, iy), (ix + 30, iy), 3)
        t = self.small.render("TANKS [T]", True, (240, 250, 225))
        surf.blit(t, t.get_rect(midleft=(b.left + 46, b.centery)))

    def draw_nuke_button(self, surf):
        b = self.nuke_btn
        active = self.nuke_state is None and not self.dead
        hover = b.collidepoint(pygame.mouse.get_pos()) and active
        base = (200, 30, 30) if active else (70, 40, 40)
        if hover:
            base = (255, 60, 50)
        blit_glow(surf, b.center, 70, (255, 60, 30), 0.5 if hover else 0.25)
        pygame.draw.rect(surf, (20, 10, 10), b.move(0, 4), border_radius=10)
        pygame.draw.rect(surf, base, b, border_radius=10)
        # hazard stripes
        clip = surf.get_clip()
        surf.set_clip(b.inflate(-6, -6))
        for x in range(b.left - 40, b.right + 40, 16):
            pygame.draw.line(surf, scale_color(base, 0.75), (x, b.bottom), (x + 30, b.top), 6)
        surf.set_clip(clip)
        pygame.draw.rect(surf, (255, 210, 60) if active else (120, 100, 60), b, 3, border_radius=10)
        self.draw_radiation(surf, pygame.Vector2(b.left + 24, b.centery), 13, (20, 20, 20), (255, 210, 60))
        t = self.small.render("NUKE [N]", True, (255, 245, 220))
        surf.blit(t, t.get_rect(midleft=(b.left + 46, b.centery)))

    def draw_nuke_incoming(self, surf):
        c = self.nuke_target
        k = 1 - self.nuke_t / 3.0
        for i in range(3):
            r = 200 * (1 - k) + 30 + i * 30
            pygame.draw.circle(surf, (255, 60 + i * 40, 40), c, int(r), 2)
        ang = self.t * 2
        for i in range(4):
            d = pygame.Vector2(math.cos(ang + i * math.pi / 2), math.sin(ang + i * math.pi / 2))
            pygame.draw.line(surf, (255, 80, 40), c + d * 18, c + d * 60, 3)
        blit_glow(surf, c, 60, (255, 40, 20), 0.4 + 0.4 * math.sin(self.t * 12))
        # the bomb falls during the last 1.2 seconds
        if self.nuke_t < 1.2:
            u = self.nuke_t / 1.2
            z = 3000 * u * u
            sh = max(4, 30 * (1 - u))
            blit_soft(surf, c + (6, 10), sh, (0, 0, 0), 200)
            sc = 1 + z * 0.004
            body = pygame.Surface((26, 60), pygame.SRCALPHA)
            pygame.draw.ellipse(body, (60, 66, 60), (3, 6, 20, 48))
            pygame.draw.ellipse(body, (95, 102, 92), (7, 10, 8, 38))
            pygame.draw.polygon(body, (40, 44, 40), [(0, 0), (26, 0), (18, 12), (8, 12)])
            pygame.draw.rect(body, (255, 210, 60), (3, 30, 20, 5))
            img = pygame.transform.rotozoom(body, 0, sc)
            surf.blit(img, img.get_rect(center=proj(c, z)))

    def draw_crosshair(self, surf):
        m = pygame.Vector2(pygame.mouse.get_pos())
        col = CYAN if self.gun_cd <= 0 else DIM
        for i in range(4):
            a = self.t * 1.5 + i * math.pi / 2
            d = pygame.Vector2(math.cos(a), math.sin(a))
            pygame.draw.line(surf, col, m + d * 7, m + d * 14, 2)
        pygame.draw.circle(surf, col, m, 2)
        if self.rocket_cd <= 0:
            pygame.draw.circle(surf, (255, 170, 60), m, 20, 1)

    def draw_hud(self, surf, frozen):
        panel = pygame.Surface((W, 44), pygame.SRCALPHA)
        panel.fill((5, 8, 16, 175))
        pygame.draw.line(panel, (*DIM, 90), (0, 43), (W, 43))
        surf.blit(panel, (0, 0))
        surf.blit(self.font.render(f"DISTRICT {self.level:02d}", True, TEXT), (16, 12))
        for i in range(3):
            c = (190 + i * 22, 22)
            col = (255, 70, 100) if i < self.hp else (60, 60, 75)
            pygame.draw.polygon(surf, col, [(c[0], c[1] + 7), (c[0] - 8, c[1] - 1), (c[0] - 4, c[1] - 6),
                                            (c[0], c[1] - 3), (c[0] + 4, c[1] - 6), (c[0] + 8, c[1] - 1)])
        for i in range(len(self.enemies)):
            c = (280 + i * 16, 22)
            pygame.draw.circle(surf, ENEMY_COL, c, 5)
        dmg = self.font.render(f"DAMAGE ${self.money:,}", True, (255, 200, 90))
        surf.blit(dmg, dmg.get_rect(center=(W / 2 + 60, 22)))
        # rocket readiness
        rx = W - 330
        surf.blit(self.small.render("RKT", True, DIM), (rx, 14))
        frac = 1 - self.rocket_cd / ROCKET_CD
        pygame.draw.rect(surf, (30, 36, 56), (rx + 34, 16, 50, 10), border_radius=5)
        pygame.draw.rect(surf, (255, 170, 60) if frac >= 1 else (130, 100, 60), (rx + 34, 16, max(10, 50 * frac), 10), border_radius=5)
        # time meter
        bx, bw = W - 220, 130
        pygame.draw.rect(surf, (30, 36, 56), (bx, 15, bw, 14), border_radius=7)
        col = lerp_color((255, 170, 90), CYAN, frozen)
        pygame.draw.rect(surf, col, (bx, 15, max(14, bw * self.time_scale), 14), border_radius=7)
        surf.blit(self.small.render("FROZEN" if frozen > 0.8 else "FLOW", True, col), (bx + bw + 10, 13))

    def draw(self):
        frozen = self.frozen_amount()
        w = self.world
        w.blit(self.ground, (0, 0))
        self.draw_shadows(w)
        w.blit(self.lights, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        if self.tsunami:
            self.tsunami.draw_water(w, self.t)

        # depth sorting: things further down the screen (closer to the camera) are drawn in front
        items = []
        for b in self.buildings:
            items.append((b.rect.bottom, 0, b.draw, ()))
        for c in self.cars:
            items.append((c.pos.y + c.z * 2, 1, c.draw, ()))
        for tk in self.tanks:
            items.append((tk.pos.y + 6, 1, tk.draw, ()))
        for e in self.enemies:
            items.append((e.pos.y + e.kz * 2, 2, e.draw, (self.player,)))
        if (not self.dead or self.nuked) and self.state == "play":
            items.append((self.player.y + self.kz * 2, 2, self.draw_player, ()))
        for p, r in self.trees:
            items.append((p.y, 1, self.draw_tree, (p, r)))
        for l in self.lamps:
            items.append((l.y, 1, self.draw_lamp, (l,)))
        items.sort(key=lambda it: (it[0], it[1]))
        for _, _, fn, args in items:
            fn(w, *args)
        if (not self.dead) and self.state == "play":   # x-ray outline so you never lose yourself behind a building
            f = proj(self.player, self.kz)
            pygame.draw.ellipse(w, (120, 230, 90), (f.x - 11, f.y - 5, 22, 10), 1)
        self.draw_shield(w)
        for s in self.shots:
            s.draw(w)
        for gr in self.grenades:
            gr.draw(w, self.t)
        if self.waves or self.fields:
            self.add_layer.fill((0, 0, 0))
            for wv in self.waves:
                wv.draw(self.add_layer)
            for f in self.fields:
                f.draw(w, self.add_layer, self.t)
            w.blit(self.add_layer, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        for hole in self.holes:
            hole.draw_dark(w)
        order = {"chunk": 0, "glass": 0, "lift": 4, "dust": 1, "smoke": 2, "fire": 3, "spark": 4, "ring": 5, "flash": 6}
        for p in sorted(self.particles, key=lambda p: order[p.kind]):
            p.draw(w)
        if self.holes:
            self.add_layer.fill((0, 0, 0))
            for hole in self.holes:
                hole.draw_glow(self.add_layer, self.t)
            w.blit(self.add_layer, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            for hole in self.holes:
                hole.draw_core(w)
        for sl in self.slabs:
            sl.draw(w)
        if self.tsunami:
            self.tsunami.draw_crest(w, self.t)
        if self.ufos or self.held:
            self.add_layer.fill((0, 0, 0))
            for u in self.ufos:
                u.draw_beam(self.add_layer, self.t)
            self.draw_gravity_beam(self.add_layer)
            w.blit(self.add_layer, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        for u in sorted(self.ufos, key=lambda u: u.z):
            u.draw(w, self.t)

        self.draw_clouds(w)
        self.bloom(w)
        if self.nuke_state == "countdown":
            self.draw_nuke_incoming(w)
        self.tint.fill((40, 120, 220, int(30 * frozen)))
        w.blit(self.tint, (0, 0))
        self.scanlines.set_alpha(int(255 * frozen))
        w.blit(self.scanlines, (0, 0))
        w.blit(self.vignette, (0, 0))

        s = self.shake
        off = (random.uniform(-s, s), random.uniform(-s, s)) if s > 0 else (0, 0)
        scr = self.screen
        scr.fill((0, 0, 0))
        scr.blit(w, off)

        if self.state == "menu":
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((3, 6, 14, 165))
            scr.blit(ov, (0, 0))
            bob = math.sin(self.t * 2.5) * 6
            blink = (self.t % 3.3) > 3.17
            left = self.avo.get("idle", int(self.t * 4) % 8, blink, int(self.t * 5) % 6, 1, 3.6)
            right = self.avo.get("walk", int(self.t * 10) % 8, blink, int(self.t * 10) % 6, -1, 3.6)
            blit_glow(scr, (150, H / 2 + 10), 150, (120, 230, 90), 0.35)
            blit_glow(scr, (W - 150, H / 2 + 10), 150, (120, 230, 90), 0.35)
            scr.blit(left, left.get_rect(center=(150, H / 2 + 10 + bob)))
            scr.blit(right, right.get_rect(center=(W - 150, H / 2 + 10 - abs(math.sin(self.t * 10 / 8 * math.tau)) * 8)))
            self.text(scr, "TIME MOVES", self.big, TEXT, (W / 2, H / 2 - 120), glow_col=CYAN)
            self.text(scr, "ONLY WHEN YOU MOVE", self.mid, CYAN, (W / 2, H / 2 - 55))
            self.text(scr, "- CITY EDITION -", self.font, (255, 200, 90), (W / 2, H / 2 - 15))
            for i, l in enumerate(["WASD - move     MOUSE - aim",
                                   "LEFT CLICK - machine gun     RIGHT CLICK - rocket",
                                   "HOLD SHIFT - shield (raise it just before a hit to REFLECT)     F - gravity gun",
                                   "ENTER - time grenade",
                                   "T - tanks   B - black hole   N - nuke   Y - tsunami   U - aliens",
                                   "Blow up cars, bring buildings down. Stand still and the world freezes."]):
                self.text(scr, l, self.small, DIM, (W / 2, H / 2 + 35 + i * 24))
            a = int(140 + 115 * math.sin(self.t * 3))
            self.text(scr, "CLICK TO START", self.font, TEXT, (W / 2, H / 2 + 175), a)
            pygame.display.flip()
            return

        self.draw_hud(scr, frozen)
        self.draw_nuke_button(scr)
        self.draw_grenade_hud(scr)
        self.draw_tank_button(scr)
        self.draw_hole_button(scr)
        self.draw_simple_button(scr, self.tsunami_btn, "TSUNAMI [Y]", not self.tsunami and self.tsunami_cd <= 0,
                                self.tsunami_cd / TSUNAMI_CD, (30, 80, 150), (150, 210, 255), (60, 150, 255), "wave")
        self.draw_simple_button(scr, self.alien_btn, "ALIENS [U]", not self.ufos and self.alien_cd <= 0,
                                self.alien_cd / ALIEN_CD, (30, 110, 60), (150, 255, 170), (80, 255, 120), "ufo")
        self.draw_gravity_hud(scr)
        self.draw_shield_hud(scr)
        for text, pos, life, col in self.popups:
            self.text(scr, text, self.font, col, pos, int(255 * min(1, life / 0.4)))
        if self.tsunami and self.tsunami.phase == "warn":
            pulse = 0.5 + 0.5 * math.sin(self.t * 10)
            self.text(scr, "TSUNAMI WARNING", self.mid, (150, 210, 255), (W / 2, 85), int(160 + 95 * pulse), (30, 90, 200))
            self.text(scr, f"from the {self.tsunami.side.upper()}", self.font, TEXT, (W / 2, 122), 220)
        if self.alien_msg > 0 and not self.dead:
            a = int(255 * min(1, self.alien_msg / 0.5))
            self.text(scr, "ALIEN INVASION", self.mid, (130, 255, 150), (W / 2, 95), a, (30, 140, 60))
            self.text(scr, "shoot the saucers down!", self.font, TEXT, (W / 2, 130), a)
        if self.holes and not self.dead:
            hole = self.holes[0]
            pulse = 0.5 + 0.5 * math.sin(self.t * 8)
            self.text(scr, "BLACK HOLE  -  ESCAPE!", self.mid, (210, 160, 255), (W / 2, 80), int(160 + 95 * pulse), (120, 40, 220))
            frac = 1 - hole.progress()
            pygame.draw.rect(scr, (30, 20, 50), (W / 2 - 150, 104, 300, 8), border_radius=4)
            pygame.draw.rect(scr, (190, 130, 255), (W / 2 - 150, 104, 300 * frac, 8), border_radius=4)
            d = hole.pos.distance_to(self.player)
            if d < 200:
                ov = pygame.Surface((W, H), pygame.SRCALPHA)
                ov.fill((60, 0, 110, int(70 * (1 - d / 200))))
                scr.blit(ov, (0, 0))
        if self.escape_msg > 0 and not self.dead:
            a = int(255 * min(1, self.escape_msg / 0.6))
            self.text(scr, "YOU ESCAPED THE BLACK HOLE!", self.mid, (255, 230, 140), (W / 2, 90), a, (200, 120, 40))
            self.text(scr, "+$1,000,000", self.font, (255, 200, 90), (W / 2, 128), a)
        if self.tank_msg > 0 and not self.dead:
            a = int(255 * min(1, self.tank_msg / 0.5))
            self.text(scr, "ARMOR INCOMING", self.mid, (170, 220, 120), (W / 2, 95), a, (60, 120, 40))
        if self.nuke_state == "countdown":
            pulse = 0.5 + 0.5 * math.sin(self.t * 12)
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 20, 20, int(25 + 45 * pulse)))
            scr.blit(ov, (0, 0))
            self.text(scr, "NUCLEAR STRIKE INCOMING", self.mid, (255, 220, 80), (W / 2, 90), int(150 + 105 * pulse), (255, 60, 30))
            self.text(scr, str(max(1, math.ceil(self.nuke_t))), self.big, (255, 255, 255), (W / 2, 160), 255, (255, 60, 30))
        if self.nuke_flash > 0:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 250, 235, int(255 * min(1, self.nuke_flash * 1.3))))
            scr.blit(ov, (0, 0))
        if self.inv > 0.6 and not self.dead:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 30, 50, int(min(90, 90 * (self.inv - 0.6) / 0.3))))
            scr.blit(ov, (0, 0))
        if self.level_msg > 0 and not self.dead:
            a = int(255 * min(1, self.level_msg / 0.6))
            self.text(scr, f"DISTRICT {self.level}", self.big, TEXT, (W / 2, H / 2 - 120), a, CYAN)
        if self.clear_t is not None and not self.dead:
            self.text(scr, "DISTRICT CLEARED", self.mid, (255, 200, 90), (W / 2, H / 2 - 120))
        if self.dead:
            k = min(1, self.death_t / 1.0)
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((20, 0, 8, int(160 * k)))
            scr.blit(ov, (0, 0))
            a = int(255 * k)
            self.text(scr, "NUKED" if self.nuked else "SPAGHETTIFIED" if self.spaghetti else
                      "ABDUCTED" if self.abducted else "YOU DIED", self.big, (255, 90, 110), (W / 2, H / 2 - 80), a, ENEMY_COL)
            self.text(scr, f"District {self.level}   |   Best {self.best}", self.font, TEXT, (W / 2, H / 2 - 15), a)
            self.text(scr, f"Damage ${self.money:,}   |   {self.buildings_destroyed} buildings   |   "
                           f"{self.cars_destroyed} cars", self.font, (255, 200, 90), (W / 2, H / 2 + 20), a)
            self.text(scr, "Press R to restart", self.small, DIM, (W / 2, H / 2 + 60), a)
        else:
            self.draw_crosshair(scr)
        pygame.display.flip()


if __name__ == "__main__":
    Game().run()