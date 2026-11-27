#!/usr/bin/env python3
"""
THE HOLLOW  -  first-person psychological horror
================================================

Install:   pip install pygame
Run:       python the_hollow.py

You ARE the character. You see only what your flashlight shows you.
Best played at night, lights off, headphones on (sound is directional).

Controls
  W / S          walk forward / back
  A / D          step sideways
  Mouse          look around   (Q / E or arrow keys also turn)
  Shift          run (limited breath)
  F              flashlight on / off  (save battery)
  Space / Enter  close a page / continue
  Esc            pause (frees the mouse)

Goal: find the 6 pages hidden in the maze, then reach the door.
It freezes while your light is on it - but staring at it breaks your mind.
"""
import array
import math
import random
import sys
from collections import deque

import pygame

W, H = 1024, 704
FPS = 60
MW = MH = 27          # maze size in tiles (odd)
TEX = 128             # wall texture size
CW = 4                # pixel width of one ray column
NCOL = W // CW
FOVK = 0.66           # camera plane length (~66 degree field of view)
SPOT = 0.26           # half-angle (radians) of the bright flashlight spot
MASK_PAD = 150
LEVELS = 22           # distance-darkness levels
LEVK = 2.6            # levels per tile of distance
MOUSE_SENS = 0.0025
PAGES_TOTAL = 6

NOTES = [
    "Day 3. The lights went out for the first time. Something walked past my door. "
    "Its footsteps were wrong. Too slow. Too many joints.",
    "It does not move while you look at it. So I looked. For hours. My eyes are bleeding "
    "and it is still standing there. Closer than before.",
    "Do not let the flashlight die. DO NOT LET THE FLASHLIGHT DIE. DO NOT",
    "I heard my mother calling my name from the dark corridor. My mother has been dead "
    "for eleven years.",
    "It is faster now. It knows I am collecting these pages. Every page makes it hungrier.",
    "The door is open now. If you are reading this, I didn't make it. Run. Don't look back. "
    "It is right behi",
]

SCRAWLS = ["TURN BACK", "IT SEES YOU", "DON'T STARE", "RUN", "NO EXIT", "HELP ME",
           "IT'S BEHIND YOU", "WHY DID YOU COME", "DON'T LOOK AWAY", "LIGHTS OUT"]

SUBLIMINAL = ["BEHIND YOU", "IT KNOWS YOUR NAME", "DON'T TURN AROUND", "WAKE UP",
              "I SEE YOU", "YOU ARE NOT ALONE", "LOOK AT ME"]


def clamp(v, a, b):
    return a if v < a else b if v > b else v


# --------------------------------------------------------------------------- sound

class Audio:
    """All sounds are synthesised at start-up - no asset files needed."""

    def __init__(self):
        self.ok = False
        try:
            info = pygame.mixer.get_init()
            if not info:
                pygame.mixer.init(22050, -16, 2, 512)
                info = pygame.mixer.get_init()
            if not info or info[1] != -16:
                return
            self.rate, _, self.ch = info
            pygame.mixer.set_num_channels(24)
            pygame.mixer.set_reserved(3)
        except Exception:
            return
        try:
            self.heart = self._snd(self._heartbeat())
            self.drone = self._snd(self._drone())
            self.step = self._snd(self._footstep())
            self.whisper = self._snd(self._whisper())
            self.scream = self._snd(self._scream())
            self.sting = self._snd(self._sting())
            self.creak = self._snd(self._creak())
            self.static = self._snd(self._static())
            self.click = self._snd(self._click())
            self.boom = self._snd(self._boom())
            self.breath = self._snd(self._breath())
            self.ch_heart = pygame.mixer.Channel(0)
            self.ch_drone = pygame.mixer.Channel(1)
            self.ch_static = pygame.mixer.Channel(2)
            self.ok = True
        except Exception:
            self.ok = False

    # -- helpers
    def _snd(self, samples):
        buf = array.array("h")
        for s in samples:
            v = int(clamp(s, -1.0, 1.0) * 30000)
            for _ in range(self.ch):
                buf.append(v)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, snd, vol=1.0, pan=0.0):
        if not self.ok:
            return
        c = snd.play()
        if c:
            pan = clamp(pan, -1, 1)
            c.set_volume(vol * min(1, 1 - pan), vol * min(1, 1 + pan))

    def loop(self, channel, snd, vol):
        if not self.ok:
            return
        if not channel.get_busy():
            channel.play(snd, loops=-1)
        channel.set_volume(vol)

    def stop_loops(self):
        if self.ok:
            for c in (self.ch_heart, self.ch_drone, self.ch_static):
                c.stop()

    # -- synthesis
    def _heartbeat(self):
        r = self.rate
        out = [0.0] * int(r * 0.6)
        for start, amp in ((0.0, 1.0), (0.18, 0.75)):
            s0 = int(start * r)
            for i in range(int(0.16 * r)):
                t = i / r
                env = math.exp(-t * 26) * min(1, t * 300)
                f = 58 - 28 * t / 0.16
                out[s0 + i] += amp * env * math.sin(2 * math.pi * f * t)
        return out

    def _drone(self):
        r = self.rate
        out = []
        for i in range(int(r * 6)):
            t = i / r
            v = (0.35 * math.sin(2 * math.pi * 55 * t)
                 + 0.30 * math.sin(2 * math.pi * 58.5 * t)
                 + 0.15 * math.sin(2 * math.pi * 110.5 * t + 2 * math.sin(2 * math.pi * 0.5 * t))
                 + 0.10 * math.sin(2 * math.pi * 233 * t) * math.sin(2 * math.pi * t / 6))
            out.append(v * 0.55)
        return out

    def _footstep(self):
        r = self.rate
        out, lp = [], 0.0
        for i in range(int(r * 0.13)):
            t = i / r
            lp += (random.uniform(-1, 1) - lp) * 0.18
            out.append(lp * 3 * math.exp(-t * 38) + 0.6 * math.sin(2 * math.pi * 72 * t) * math.exp(-t * 45))
        return out

    def _whisper(self):
        r = self.rate
        out, prev = [], 0.0
        dur = 1.8
        for i in range(int(r * dur)):
            t = i / r
            w = random.uniform(-1, 1)
            hp, prev = w - prev, w
            env = math.sin(math.pi * t / dur) ** 2
            mod = 0.5 + 0.5 * math.sin(2 * math.pi * (5 + 3 * math.sin(t * 3)) * t)
            out.append(hp * 0.4 * env * mod)
        return out

    def _scream(self):
        r = self.rate
        out, ph = [], [0.0, 0.0, 0.0, 0.0]
        mult = (1.0, 1.37, 1.93, 2.71)
        for i in range(int(r * 1.6)):
            t = i / r
            base = 320 + 950 * min(1, t * 3) + random.uniform(-60, 60)
            env = min(1, t * 40) * (1 if t < 1.2 else max(0, (1.6 - t) / 0.4))
            v = 0.0
            for k, m in enumerate(mult):
                ph[k] += base * m / r
                v += ((ph[k] % 1.0) * 2 - 1) / (k + 1)
            v += random.uniform(-1, 1) * 0.55
            out.append(v * 0.75 * env)
        return out

    def _sting(self):
        r = self.rate
        freqs = (196.0, 207.7, 293.7, 311.1, 415.3)
        out = []
        for i in range(int(r * 2.2)):
            t = i / r
            env = min(1, t * 6) * math.exp(-t * 1.6)
            v = sum(math.sin(2 * math.pi * f * t * (1 + 0.002 * math.sin(t * 7))) for f in freqs) / len(freqs)
            out.append(v * env * 0.9)
        return out

    def _creak(self):
        r = self.rate
        out, ph = [], 0.0
        for i in range(int(r * 1.5)):
            t = i / r
            f = 22 + 30 * math.sin(t * 2.3) ** 2
            ph += f / r
            pulse = 1.0 if (ph % 1.0) < 0.08 else 0.0
            env = math.sin(math.pi * t / 1.5)
            out.append(pulse * math.sin(2 * math.pi * 340 * t) * env * 0.6 + random.uniform(-0.05, 0.05) * env)
        return out

    def _static(self):
        return [random.uniform(-0.5, 0.5) for _ in range(self.rate)]

    def _click(self):
        r = self.rate
        return [random.uniform(-1, 1) * math.exp(-i / r * 300) for i in range(int(r * 0.04))]

    def _boom(self):
        r = self.rate
        out = []
        for i in range(int(r * 2.5)):
            t = i / r
            out.append((math.sin(2 * math.pi * (42 - 8 * t) * t) + random.uniform(-0.3, 0.3)) * math.exp(-t * 1.8))
        return out


    def _breath(self):
        r = self.rate
        out, lp = [], 0.0
        for i in range(int(r * 0.7)):
            t = i / r
            lp += (random.uniform(-1, 1) - lp) * 0.08
            out.append(lp * 1.6 * math.sin(math.pi * t / 0.7) ** 2)
        return out


# --------------------------------------------------------------------------- world gen
def gen_maze(w, h):
    grid = [[1] * w for _ in range(h)]
    grid[1][1] = 0
    stack = [(1, 1)]
    while stack:
        x, y = stack[-1]
        nb = [(x + dx, y + dy, dx, dy) for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2))
              if 0 < x + dx < w - 1 and 0 < y + dy < h - 1 and grid[y + dy][x + dx] == 1]
        if nb:
            nx, ny, dx, dy = random.choice(nb)
            grid[y + dy // 2][x + dx // 2] = 0
            grid[ny][nx] = 0
            stack.append((nx, ny))
        else:
            stack.pop()
    # knock out some walls to create loops (so you can run around it)
    for _ in range(w * h // 16):
        x, y = random.randrange(1, w - 1), random.randrange(1, h - 1)
        if grid[y][x] == 1:
            horiz = grid[y][x - 1] == 0 and grid[y][x + 1] == 0 and grid[y - 1][x] == 1 and grid[y + 1][x] == 1
            vert = grid[y - 1][x] == 0 and grid[y + 1][x] == 0 and grid[y][x - 1] == 1 and grid[y][x + 1] == 1
            if horiz or vert:
                grid[y][x] = 0
    return grid


def bfs(grid, start):
    dist = {start: 0}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if grid[ny][nx] == 0 and (nx, ny) not in dist:
                dist[(nx, ny)] = dist[(x, y)] + 1
                q.append((nx, ny))
    return dist


def bfs_path(grid, start, goal):
    if start == goal:
        return [start]
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        x, y = cur
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if grid[n[1]][n[0]] == 0 and n not in prev:
                prev[n] = cur
                q.append(n)
    if goal not in prev:
        return []
    path, c = [], goal
    while c is not None:
        path.append(c)
        c = prev[c]
    return path[::-1]



def draw_face(surf, cx, cy, s, jit=0.0, seed=3):
    """The thing's face. Procedural, no image files."""
    def J():
        return random.uniform(-jit, jit)
    head = pygame.Rect(0, 0, int(330 * s), int(460 * s))
    head.center = (int(cx + J()), int(cy + J()))
    pygame.draw.ellipse(surf, (206, 201, 190), head)
    pygame.draw.ellipse(surf, (160, 154, 146), head, max(1, int(14 * s)))
    # cracks
    rnd = random.Random(seed)
    for _ in range(7):
        x, y = head.centerx + rnd.uniform(-120, 120) * s, head.centery + rnd.uniform(-190, 150) * s
        pts = [(int(x), int(y))]
        for _ in range(5):
            x += rnd.uniform(-30, 30) * s
            y += rnd.uniform(-10, 40) * s
            pts.append((int(x), int(y)))
        pygame.draw.lines(surf, (95, 85, 80), False, pts, max(1, int(3 * s)))
    # eyes: empty black holes with tiny pupils
    for side in (-1, 1):
        e = pygame.Rect(0, 0, int(100 * s), int(140 * s))
        e.center = (int(cx + side * 78 * s + J()), int(cy - 60 * s + J()))
        pygame.draw.ellipse(surf, (6, 4, 4), e)
        pygame.draw.circle(surf, (255, 255, 255), (int(e.centerx + J() * 0.4), int(e.centery + 12 * s)), max(2, int(7 * s)))
        pygame.draw.line(surf, (14, 8, 8), (e.centerx - int(8 * s), e.bottom - 4),
                         (int(e.centerx - 14 * s + J()), int(e.bottom + 110 * s)), max(1, int(8 * s)))
    # mouth, stretched far too wide
    m = pygame.Rect(0, 0, int(160 * s), int(220 * s))
    m.center = (int(cx + J()), int(cy + 125 * s))
    pygame.draw.ellipse(surf, (4, 0, 0), m)
    hw, hh = m.width / 2, m.height / 2
    n = 9
    for i in range(n):
        x0 = m.left + m.width * (i + 0.15) / n
        x1 = m.left + m.width * (i + 0.85) / n
        xm = (x0 + x1) / 2
        for top in (True, False):
            u = clamp((xm - m.centerx) / hw, -0.99, 0.99)
            edge = hh * math.sqrt(1 - u * u)
            ye = m.centery - edge if top else m.centery + edge
            tip = ye + (26 * s if top else -26 * s)
            pygame.draw.polygon(surf, (232, 228, 205), [(int(x0), int(ye)), (int(x1), int(ye)), (int(xm), int(tip))])



def center(tile):
    return tile[0] + 0.5, tile[1] + 0.5


def make_vignette():
    v = pygame.Surface((W, H), pygame.SRCALPHA)
    v.fill((0, 0, 0, 230))
    maxr = int(math.hypot(W, H) / 2)
    steps = 70
    for i in range(steps):
        k = i / steps
        pygame.draw.circle(v, (0, 0, 0, int(230 * (1 - k) ** 2.4)), (W // 2, H // 2), int(maxr * (1 - k)))
    return v


def make_grain():
    small = pygame.Surface((W // 4, H // 4), pygame.SRCALPHA)
    for y in range(H // 4):
        for x in range(W // 4):
            g = random.randint(0, 255)
            small.set_at((x, y), (g, g, g, random.randint(0, 26)))
    return pygame.transform.scale(small, (W, H))


def make_flash_mask():
    """Warm round flashlight spot, multiplied over the whole frame."""
    m = pygame.Surface((W + 2 * MASK_PAD, H + 2 * MASK_PAD))
    m.fill((20, 20, 25))
    cx, cy = m.get_width() // 2, m.get_height() // 2 + 30
    steps = 60
    for i in range(steps):
        k = i / (steps - 1)                     # 0 outer -> 1 inner
        r = int(640 * (1 - k) + 130 * k)
        b = 20 + 235 * (k ** 1.3)
        pygame.draw.circle(m, (int(b), int(b * 0.94), int(b * 0.80)), (cx, cy), r)
    return m


# ---------------------------------------------------------------- textures
def draw_hand(surf, cx, cy, size, rot, curl, col, dark, rnd, shadow=True):
    """A pale, plaster-like hand reaching out, fingers up. (cx, cy) = middle of the palm."""
    c, sn = math.cos(rot), math.sin(rot)

    def P(dx, dy):
        return (cx + (dx * c - dy * sn) * size, cy + (dx * sn + dy * c) * size)

    w = max(2, int(size * 0.15))
    parts = []  # (kind, data)
    parts.append(("poly", [P(-0.24, 0.3), P(0.24, 0.3), P(0.19, 1.25), P(-0.19, 1.25)]))   # wrist / forearm
    parts.append(("poly", [P(-0.34, 0.38), P(0.32, 0.38), P(0.38, -0.28), P(-0.36, -0.28)]))  # palm
    fingers = ((-0.27, 0.50, -0.30), (-0.09, 0.66, -0.10), (0.10, 0.62, 0.10), (0.28, 0.46, 0.30))
    for bx, ln, spread in fingers:
        ang = -math.pi / 2 + spread
        x, y = bx, -0.26
        pts = [P(x, y)]
        for seg, frac in enumerate((0.45, 0.33, 0.24)):
            L = ln * frac * (1 - curl * 0.35 * seg)
            x += math.cos(ang) * L
            y += math.sin(ang) * L
            pts.append(P(x, y))
            ang += (rnd.uniform(0.15, 0.55) * curl + rnd.uniform(-0.12, 0.12)) * (1 if bx > 0 else -1)
        parts.append(("finger", pts))
    # thumb
    ang = math.pi + 0.6
    x, y = -0.34, 0.12
    pts = [P(x, y)]
    for frac in (0.25, 0.2):
        ang += 0.35 * curl - 0.2
        x += math.cos(ang) * frac
        y += math.sin(ang) * frac
        pts.append(P(x, y))
    parts.append(("finger", pts))

    def render(color, ox, oy, extra):
        for kind, data in parts:
            pts = [(int(px + ox), int(py + oy)) for px, py in data]
            if kind == "poly":
                pygame.draw.polygon(surf, color, pts)
            else:
                pygame.draw.lines(surf, color, False, pts, w + extra)
                for q in pts:
                    pygame.draw.circle(surf, color, q, (w + extra) // 2)

    if shadow:
        sh = max(2, int(size * 0.18))
        render(dark, sh, sh, 2)          # cast shadow on the wall
    render((col[0] - 35, col[1] - 35, col[2] - 35), 0, 0, 2)   # outline
    render(col, -1, -1, 0)                                     # lit surface


def make_wall_texture(kind, rnd, font):
    """Pale, rough plaster - and hands pushing out of it."""
    t = pygame.Surface((TEX, TEX))
    base = rnd.randint(158, 172)
    t.fill((base, base - 4, base - 12))
    for _ in range(TEX * TEX // 3):
        x, y = rnd.randrange(TEX), rnd.randrange(TEX)
        d = rnd.randint(-18, 12)
        b = base + d
        t.set_at((x, y), (b, b - 4, b - 12))
    for _ in range(6):  # soft blotches / damp
        b = base - rnd.randint(8, 20)
        pygame.draw.ellipse(t, (b, b - 4, b - 10), (rnd.randrange(TEX), rnd.randrange(TEX), rnd.randint(10, 40), rnd.randint(10, 40)))
    for _ in range(3):  # hairline cracks
        x, y = rnd.randrange(TEX), rnd.randrange(TEX)
        pts = [(x, y)]
        for _ in range(4):
            x += rnd.randint(-10, 10)
            y += rnd.randint(4, 14)
            pts.append((x, y))
        pygame.draw.lines(t, (base - 45, base - 48, base - 52), False, pts, 1)
    if kind == "hands":
        dark = (base - 70, base - 72, base - 76)
        col = (min(255, base + 40), min(255, base + 36), min(255, base + 28))
        for _ in range(rnd.randint(1, 3)):
            size = rnd.uniform(22, 36)
            draw_hand(t, rnd.uniform(20, TEX - 20), rnd.uniform(30, TEX - 25), size,
                      rnd.uniform(-1.3, 1.3), rnd.uniform(0.4, 1.0), col, dark, rnd)
    elif kind == "blood":
        red = (120, 10, 8)
        for i in range(4):
            x = rnd.randint(30, 90) + i * 6
            pygame.draw.line(t, red, (x, 20), (x + rnd.randint(-4, 4), 20 + rnd.randint(40, 90)), 3)
    return t


def make_hand_sprite(seed, curl):
    """A hand sticking out of the wall towards you."""
    s = pygame.Surface((90, 120), pygame.SRCALPHA)
    rnd = random.Random(seed)
    draw_hand(s, 45, 58, 44, rnd.uniform(-0.3, 0.3), curl, (200, 194, 182), (0, 0, 0, 0), rnd, shadow=False)
    # fake 3D: darken the right half so it looks rounded and lit from the left
    shade = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    for x in range(s.get_width()):
        k = int(255 - 90 * max(0.0, (x - 30) / 60))
        pygame.draw.line(shade, (k, k, k, 255), (x, 0), (x, s.get_height()))
    s.blit(shade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return s


def make_entity_sprite(frame):
    """Pale, starved, far too tall. Black holes where the eyes should be."""
    s = pygame.Surface((70, 210), pygame.SRCALPHA)
    rnd = random.Random(frame)
    skin = (168, 162, 152)
    shade = (110, 104, 98)
    # long thin legs
    pygame.draw.line(s, shade, (30, 140), (27 + rnd.randint(-2, 2), 210), 5)
    pygame.draw.line(s, shade, (40, 140), (43 + rnd.randint(-2, 2), 210), 5)
    # torso with ribs
    pygame.draw.ellipse(s, skin, (22, 52, 26, 100))
    for i in range(5):
        pygame.draw.arc(s, shade, (24, 62 + i * 9, 22, 10), 3.4, 6.0, 1)
    # arms hanging far too low
    for side in (-1, 1):
        sx = 35 + side * 10
        hx = 35 + side * (22 + rnd.randint(0, 4))
        pygame.draw.line(s, skin, (sx, 60), (hx, 175), 4)
        for f in (-4, -1, 2, 5):
            pygame.draw.line(s, shade, (hx, 175), (hx + f, 194 + rnd.randint(0, 6)), 2)
    # neck + tilted head
    pygame.draw.line(s, skin, (35, 44), (35, 56), 6)
    hx = 36 + rnd.randint(-1, 1)
    pygame.draw.ellipse(s, skin, (hx - 12, 16, 24, 32))
    # long black hair
    for i in range(9):
        x0 = hx - 12 + i * 3
        pygame.draw.line(s, (10, 8, 8), (x0, 16), (x0 + rnd.randint(-3, 3), 46 + rnd.randint(0, 30)), 2)
    pygame.draw.ellipse(s, (10, 8, 8), (hx - 13, 13, 26, 10))
    # eye holes + mouth
    for ex in (-5, 5):
        pygame.draw.ellipse(s, (0, 0, 0), (hx + ex - 3, 26, 7, 9))
        pygame.draw.circle(s, (255, 255, 255), (hx + ex, 31), 1)
    pygame.draw.ellipse(s, (0, 0, 0), (hx - 4, 38, 8, 10))
    return s


def make_page_sprite():
    s = pygame.Surface((26, 32), pygame.SRCALPHA)
    pygame.draw.polygon(s, (225, 215, 185), [(0, 2), (24, 0), (26, 30), (2, 32)])
    for i in range(5):
        pygame.draw.line(s, (90, 80, 70), (4, 7 + i * 5), (21, 6 + i * 5))
    return s


def make_battery_sprite():
    s = pygame.Surface((16, 30), pygame.SRCALPHA)
    pygame.draw.rect(s, (190, 165, 40), (0, 4, 16, 26), border_radius=3)
    pygame.draw.rect(s, (40, 40, 40), (0, 4, 16, 8), border_radius=3)
    pygame.draw.rect(s, (200, 200, 200), (5, 0, 6, 4))
    return s


def make_door_sprite(unlocked):
    s = pygame.Surface((80, 140), pygame.SRCALPHA)
    pygame.draw.rect(s, (60, 36, 20), (0, 0, 80, 140))
    pygame.draw.rect(s, (30, 18, 8), (0, 0, 80, 140), 6)
    if unlocked:
        pygame.draw.rect(s, (2, 2, 2), (10, 10, 60, 130))
        pygame.draw.rect(s, (25, 30, 32), (16, 18, 48, 120), 1)
    else:
        for y in range(10, 140, 26):
            pygame.draw.line(s, (50, 30, 15), (8, y), (72, y), 2)
        pygame.draw.line(s, (130, 130, 130), (6, 30), (74, 110), 5)
        pygame.draw.line(s, (130, 130, 130), (74, 30), (6, 110), 5)
        pygame.draw.rect(s, (110, 100, 50), (30, 62, 20, 18))
    return s


# --------------------------------------------------------------------------- game
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        self.f_huge = pygame.font.Font(None, 120)
        self.f_big = pygame.font.Font(None, 72)
        self.f_mid = pygame.font.Font(None, 40)
        self.f_small = pygame.font.Font(None, 26)
        self.f_tex = pygame.font.Font(None, 22)
        self.f_note = pygame.font.SysFont("couriernew,courier,dejavusansmono,liberationmono,monospace", 22)
        self.vignette = make_vignette()
        self.grain = [make_grain() for _ in range(4)]
        self.mask = make_flash_mask()
        self.build_textures()
        self.bg = pygame.Surface((W, 2 * H))
        for y in range(2 * H):
            if y < H:
                k = (1 - y / H) ** 2
                c = (int(3 + 14 * k), int(3 + 12 * k), int(3 + 11 * k))
            else:
                k = ((y - H) / H) ** 1.5
                c = (int(3 + 52 * k), int(3 + 45 * k), int(3 + 38 * k))
            pygame.draw.line(self.bg, c, (0, y), (W, y))
        self.ent_frames = [make_entity_sprite(i) for i in range(3)]
        self.page_img = make_page_sprite()
        self.batt_img = make_battery_sprite()
        self.hand_frames = [(make_hand_sprite(i, 0.6), make_hand_sprite(i, 1.35)) for i in range(5)]
        self.door_locked = make_door_sprite(False)
        self.door_open = make_door_sprite(True)
        self.zbuf = [0.0] * NCOL
        self.state = "title"
        self.t = 0.0
        self.title_face = 0.0
        self.new_game()

    def build_textures(self):
        rnd = random.Random(11)
        kinds = ["plain", "plain", "hands", "hands", "hands", "hands", "hands", "blood"]
        self.tex_cols = []   # [variant][side][level][x] -> 1xTEX surface
        for kind in kinds:
            base = make_wall_texture(kind, rnd, self.f_tex)
            per_side = []
            for side in (0, 1):
                levels = []
                for lv in range(LEVELS):
                    k = math.exp(-lv / LEVK * 0.30) * (1.0 if side == 0 else 0.75)
                    shaded = base.copy()
                    c = int(255 * k)
                    shaded.fill((c, c, c), special_flags=pygame.BLEND_RGB_MULT)
                    levels.append([shaded.subsurface((x, 0, 1, TEX)) for x in range(TEX)])
                per_side.append(levels)
            self.tex_cols.append(per_side)

    # ---------------------------------------------------------------- setup
    def new_game(self):
        self.grid = gen_maze(MW, MH)
        rnd = random.Random()
        self.wallvar = [[rnd.randint(0, 1) if rnd.random() < 0.35 else 7 if rnd.random() < 0.04 else rnd.randint(2, 6)
                         for _ in range(MW)] for _ in range(MH)]
        start = (1, 1)
        dist = bfs(self.grid, start)
        self.px, self.py = center(start)
        opens = [(x, y) for y in range(MH) for x in range(MW) if not self.grid[y][x]]
        exit_tile = max(opens, key=lambda p: dist.get(p, -1))
        far = max(dist.values())
        self.angle = 0.0 if self.grid[1][2] == 0 else math.pi / 2

        def walls(p):
            x, y = p
            return self.grid[y][x + 1] + self.grid[y][x - 1] + self.grid[y + 1][x] + self.grid[y - 1][x]

        dead = [p for p in opens if p != exit_tile and dist.get(p, 0) > 10 and walls(p) == 3]
        random.shuffle(dead)
        pages = []
        for p in dead:
            if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) > 7 for q in pages):
                pages.append(p)
            if len(pages) == PAGES_TOTAL:
                break
        pool = [p for p in opens if dist.get(p, 0) > 6 and p != exit_tile and p not in pages]
        random.shuffle(pool)
        while len(pages) < PAGES_TOTAL:
            pages.append(pool.pop())
        self.pages = [center(p) for p in pages]
        self.batteries = [center(pool.pop()) for _ in range(7)]
        self.exit = center(exit_tile)
        spawn = random.choice([p for p in opens if dist.get(p, 0) > far * 0.55])
        self.ex, self.ey = center(spawn)

        self.battery = 100.0
        self.stamina = 100.0
        self.sanity = 100.0
        self.flash_on = True
        self.blackout = 0.0
        self.flick = 0.0
        self.flick_off = 0.0
        self.collected = 0
        self.path = []
        self.path_t = 0.0
        self.ent_wait = 8.0
        self.far_t = 0.0
        self.heart_t = 0.0
        self.step_t = 0.0
        self.ent_step_t = 0.0
        self.breath_t = 0.0
        self.event_t = random.uniform(10, 20)
        self.queue = []
        self.sub_t = 0.0
        self.sub_text = ""
        self.glimpse = 0.0
        self.glimpse_side = 1
        self.msg_text = "Find the 6 pages. Find the door. Do not let it touch you."
        self.msg_t = 7.0
        self.alive_t = 0.0
        self.seen = False
        self.light_on = True
        self.ent_dist = 99.0
        self.note_idx = 0
        self.win_scared = False
        # hands reaching out of the corridor walls
        self.hands = []
        for (tx, ty) in opens:
            if (tx, ty) == start:
                continue
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if self.grid[ty + ddy][tx + ddx] and rnd.random() < 0.13:
                    side = rnd.uniform(-0.3, 0.3)
                    self.hands.append({"x": tx + 0.5 + ddx * 0.44 + ddy * side,
                                       "y": ty + 0.5 + ddy * 0.44 + ddx * side,
                                       "lift": rnd.uniform(0.25, 0.7), "var": rnd.randrange(5),
                                       "done": False, "twitch": 0.0})
        self.bob_phase = 0.0
        self.bob = 0.0
        self.sway = 0.0
        self.turn_vel = 0.0

    # ---------------------------------------------------------------- geometry
    def solid(self, x, y):
        tx, ty = int(x), int(y)
        if tx < 0 or ty < 0 or tx >= MW or ty >= MH:
            return True
        return self.grid[ty][tx] == 1

    def free(self, x, y, r=0.22):
        return not any(self.solid(x + ox, y + oy) for ox, oy in ((-r, -r), (r, -r), (-r, r), (r, r)))

    def los(self, ax, ay, bx, by):
        d = math.hypot(bx - ax, by - ay)
        n = int(d / 0.12) + 1
        for i in range(1, n):
            k = i / n
            if self.solid(ax + (bx - ax) * k, ay + (by - ay) * k):
                return False
        return True

    def dda(self, px, py, rdx, rdy):
        mx, my = int(px), int(py)
        ddx = abs(1 / rdx) if rdx else 1e30
        ddy = abs(1 / rdy) if rdy else 1e30
        if rdx < 0:
            stx, sdx = -1, (px - mx) * ddx
        else:
            stx, sdx = 1, (mx + 1 - px) * ddx
        if rdy < 0:
            sty, sdy = -1, (py - my) * ddy
        else:
            sty, sdy = 1, (my + 1 - py) * ddy
        grid = self.grid
        while True:
            if sdx < sdy:
                sdx += ddx
                mx += stx
                side = 0
            else:
                sdy += ddy
                my += sty
                side = 1
            if grid[my][mx]:
                break
        if side == 0:
            perp = sdx - ddx
            wx = py + perp * rdy
        else:
            perp = sdy - ddy
            wx = px + perp * rdx
        return max(perp, 0.02), side, wx - math.floor(wx), mx, my

    def light_range(self):
        return 3.0 + 4.5 * min(1.0, self.battery / 40)

    # ---------------------------------------------------------------- update
    def update(self, dt):
        self.t += dt
        if self.state == "play":
            self.update_play(dt)
        elif self.state == "jumpscare":
            if self.t > 1.6:
                self.state, self.t = "dead", 0.0
        elif self.state == "title":
            self.title_face -= dt
            if self.title_face < -random.uniform(6, 12):
                self.title_face = 0.12
        elif self.state == "win":
            if not self.win_scared and self.t > 6.0:
                self.win_scared = True
                self.audio.play(self.audio.scream, 0.8)

    def say(self, text, t=3.0):
        self.msg_text, self.msg_t = text, t

    def rel_angle(self, x, y):
        return (math.atan2(y - self.py, x - self.px) - self.angle + math.pi) % (2 * math.pi) - math.pi

    def update_play(self, dt):
        a = self.audio
        self.alive_t += dt
        keys = pygame.key.get_pressed()

        # --- look
        turn = (keys[pygame.K_RIGHT] or keys[pygame.K_e]) - (keys[pygame.K_LEFT] or keys[pygame.K_q])
        self.angle += turn * 2.4 * dt
        self.sway *= 0.85

        # --- movement
        fwd = (keys[pygame.K_w] or keys[pygame.K_UP]) - (keys[pygame.K_s] or keys[pygame.K_DOWN])
        strafe = keys[pygame.K_d] - keys[pygame.K_a]
        moving = bool(fwd or strafe)
        running = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and moving and self.stamina > 1
        if running:
            self.stamina = max(0.0, self.stamina - 30 * dt)
        else:
            self.stamina = min(100.0, self.stamina + 14 * dt)
        spd = 4.0 if running else 2.4
        if moving:
            ca, sa = math.cos(self.angle), math.sin(self.angle)
            vx = ca * fwd - sa * strafe
            vy = sa * fwd + ca * strafe
            n = math.hypot(vx, vy)
            nx = self.px + vx / n * spd * dt
            if self.free(nx, self.py):
                self.px = nx
            ny = self.py + vy / n * spd * dt
            if self.free(self.px, ny):
                self.py = ny
            self.bob_phase += dt * (13 if running else 8.5)
            self.bob = math.sin(self.bob_phase) * (9 if running else 5)
            self.step_t -= dt
            if self.step_t <= 0:
                self.step_t = 0.3 if running else 0.46
                a.play(a.step, 0.16)
        else:
            self.bob *= 0.9
        if self.stamina < 30:
            self.breath_t -= dt
            if self.breath_t <= 0:
                self.breath_t = 0.9
                a.play(a.breath, 0.35 * (1 - self.stamina / 30) + 0.1)

        # --- flashlight
        if self.flash_on and self.blackout <= 0 and self.battery > 0:
            self.battery = max(0.0, self.battery - dt * 0.62)
            if self.battery == 0:
                self.say("The flashlight is dead.", 4)
        self.blackout = max(0.0, self.blackout - dt)
        self.flick = max(0.0, self.flick - dt)
        self.flick_off = max(0.0, self.flick_off - dt)
        chance = 0.0
        if self.battery < 25:
            chance = 0.05 + (25 - self.battery) * 0.004
        if self.flick > 0:
            chance = 0.25
        if self.ent_dist < 4.5:
            chance = max(chance, 0.08)
        if self.flick_off <= 0 and random.random() < chance:
            self.flick_off = random.uniform(0.04, 0.18)
        torch_ok = self.flash_on and self.battery > 0 and self.blackout <= 0
        self.light_on = torch_ok and self.flick_off <= 0

        # --- the entity
        dx, dy = self.ex - self.px, self.ey - self.py
        dist = math.hypot(dx, dy)
        self.ent_dist = dist
        rel = self.rel_angle(self.ex, self.ey)
        pan = math.sin(rel)
        in_spot = abs(rel) < SPOT + 0.2 / max(dist, 0.3)
        self.ent_visible_line = self.los(self.px, self.py, self.ex, self.ey)
        self.seen = torch_ok and in_spot and dist < self.light_range() and self.ent_visible_line

        if self.ent_wait > 0:
            self.ent_wait -= dt
        elif self.seen:
            self.sanity -= 23 * dt
            self.far_t = 0
        else:
            self.sanity = min(100.0, self.sanity + 6 * dt)
            speed = 1.45 + 0.28 * self.collected
            if not torch_ok:
                speed *= 1.5
            if dist > 13:
                speed *= 1.9
            self.move_entity(speed * dt)
            if dist < 10:
                self.ent_step_t -= dt
                if self.ent_step_t <= 0:
                    self.ent_step_t = 0.55
                    a.play(a.step, clamp(1 - dist / 10, 0, 1) * 0.8, pan)
            if dist > 15:
                self.far_t += dt
                if self.far_t > 10:
                    self.teleport_entity()
            else:
                self.far_t = 0
            if dist < 7 and random.random() < 0.12 * dt:
                a.play(a.whisper, 0.6, pan)

        if self.sanity <= 0:
            self.sanity = 45
            self.blackout = 2.6
            a.play(a.whisper, 1.0)
            a.play(a.sting, 0.7)
            self.say("YOU LOOKED TOO LONG", 2.5)

        if dist < 0.45 and self.ent_wait <= 0:
            self.trigger_jumpscare()
            return

        # --- atmosphere
        self.heart_t -= dt
        if self.heart_t <= 0:
            self.heart_t = clamp(dist / 7, 0.32, 1.5)
            if a.ok:
                a.ch_heart.play(a.heart)
                a.ch_heart.set_volume(clamp(1.1 - dist / 14, 0.1, 1.0))
        a.loop(a.ch_drone, a.drone, clamp(0.3 + (9 - dist) / 18, 0.3, 0.8) if a.ok else 0)
        a.loop(a.ch_static, a.static, clamp((100 - self.sanity) / 100, 0, 1) * (0.55 if self.seen else 0.25))

        self.event_t -= dt
        if self.event_t <= 0:
            self.event_t = random.uniform(12, 28) - self.collected * 1.2
            self.random_event()
        for item in self.queue[:]:
            item[0] -= dt
            if item[0] <= 0:
                self.queue.remove(item)
                a.play(a.step, item[1], item[2])
        self.sub_t = max(0.0, self.sub_t - dt)
        self.glimpse = max(0.0, self.glimpse - dt)
        self.msg_t = max(0.0, self.msg_t - dt)

        # --- the walls notice you
        for hd in self.hands:
            hd["twitch"] = max(0.0, hd["twitch"] - dt)
            if not hd["done"] and abs(hd["x"] - self.px) < 0.9 and abs(hd["y"] - self.py) < 0.9:
                hd["done"] = True
                hd["twitch"] = 1.2
                a.play(a.creak, 0.25, math.sin(self.rel_angle(hd["x"], hd["y"])))

        # --- pickups
        for p in self.pages[:]:
            if math.hypot(p[0] - self.px, p[1] - self.py) < 0.55:
                self.pages.remove(p)
                self.note_idx = self.collected
                self.collected += 1
                a.play(a.sting, 0.8)
                self.state, self.t = "note", 0.0
                if self.collected == PAGES_TOTAL:
                    a.play(a.boom, 1.0)
                return
        for b in self.batteries[:]:
            if math.hypot(b[0] - self.px, b[1] - self.py) < 0.5:
                self.batteries.remove(b)
                self.battery = min(100.0, self.battery + 45)
                a.play(a.click, 0.6)
                self.say("+ battery", 1.5)
        if math.hypot(self.exit[0] - self.px, self.exit[1] - self.py) < 0.6:
            if self.collected >= PAGES_TOTAL:
                a.stop_loops()
                self.state, self.t = "win", 0.0
                self.release_mouse()
            elif self.msg_t <= 0:
                self.say("The door is locked. %d pages left." % (PAGES_TOTAL - self.collected), 2.5)

    def move_entity(self, step):
        self.path_t -= step
        etile = (int(self.ex), int(self.ey))
        ptile = (int(self.px), int(self.py))
        if self.path_t <= 0 or not self.path:
            self.path = bfs_path(self.grid, etile, ptile)[1:]
            self.path_t = 0.3
        while step > 0:
            if self.path:
                tx, ty = center(self.path[0])
            else:
                tx, ty = self.px, self.py
            ddx, ddy = tx - self.ex, ty - self.ey
            d = math.hypot(ddx, ddy)
            if d <= step:
                self.ex, self.ey = tx, ty
                step -= d
                if self.path:
                    self.path.pop(0)
                else:
                    break
            else:
                self.ex += ddx / d * step
                self.ey += ddy / d * step
                step = 0

    def teleport_entity(self):
        dist = bfs(self.grid, (int(self.px), int(self.py)))
        cands = [p for p, d in dist.items() if 6 <= d <= 9]
        random.shuffle(cands)
        for p in cands:
            cx, cy = center(p)
            if not self.los(self.px, self.py, cx, cy):
                self.ex, self.ey = cx, cy
                self.path = []
                self.far_t = 0
                self.audio.play(self.audio.creak, 0.5, math.sin(self.rel_angle(cx, cy)))
                return

    def random_event(self):
        a = self.audio
        kind = random.choice(["steps", "steps", "whisper", "flicker", "text", "creak", "glimpse", "glimpse"])
        if kind == "steps":
            pan = random.choice((-0.3, 0.3))  # right behind you
            for i in range(5):
                self.queue.append([0.45 * i, 0.25 + 0.12 * i, pan])
        elif kind == "whisper":
            a.play(a.whisper, 0.9, random.choice((-1, 1)))
        elif kind == "flicker":
            self.flick = 1.4
        elif kind == "text":
            self.sub_t = 0.09
            self.sub_text = random.choice(SUBLIMINAL)
        elif kind == "creak":
            a.play(a.creak, 0.7, random.uniform(-1, 1))
        elif kind == "glimpse":
            self.glimpse = 0.3
            self.glimpse_side = random.choice((-1, 1))

    def trigger_jumpscare(self):
        self.audio.stop_loops()
        self.audio.play(self.audio.scream, 1.0)
        self.state, self.t = "jumpscare", 0.0
        self.release_mouse()

    # ---------------------------------------------------------------- input
    def grab_mouse(self):
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        pygame.mouse.get_rel()

    def release_mouse(self):
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)

    def handle(self, ev):
        if ev.type == pygame.QUIT:
            return False
        if ev.type == pygame.MOUSEMOTION and self.state == "play":
            self.angle += ev.rel[0] * MOUSE_SENS
            self.sway = clamp(self.sway + ev.rel[0] * 0.4, -30, 30)
            return True
        if ev.type != pygame.KEYDOWN:
            return True
        k = ev.key
        if self.state == "title":
            if k in (pygame.K_RETURN, pygame.K_SPACE):
                self.start()
            elif k == pygame.K_ESCAPE:
                return False
        elif self.state == "play":
            if k == pygame.K_f:
                self.flash_on = not self.flash_on
                self.audio.play(self.audio.click, 0.5)
            elif k == pygame.K_ESCAPE:
                self.state = "pause"
                self.release_mouse()
        elif self.state == "pause":
            if k == pygame.K_ESCAPE:
                self.state = "play"
                self.grab_mouse()
            elif k == pygame.K_q:
                return False
        elif self.state == "note":
            if k in (pygame.K_SPACE, pygame.K_RETURN) and self.t > 0.6:
                self.state = "play"
                pygame.mouse.get_rel()
                if self.collected == PAGES_TOTAL:
                    self.say("Somewhere, a door unlocked. It is angry now. RUN.", 5)
                    self.ent_wait = 0
                    self.teleport_entity()
        elif self.state in ("dead", "win"):
            if k in (pygame.K_RETURN, pygame.K_SPACE) and self.t > 1.5:
                self.new_game()
                self.start()
            elif k == pygame.K_ESCAPE:
                return False
        return True

    def start(self):
        self.state, self.t = "play", 0.0
        self.grab_mouse()

    # ---------------------------------------------------------------- drawing
    def draw(self):
        s = self.state
        if s == "title":
            self.draw_title()
        elif s in ("play", "pause", "note"):
            self.draw_world()
            if s == "pause":
                self.overlay_text(["PAUSED", "", "ESC - resume     Q - quit"])
            elif s == "note":
                self.draw_note()
        elif s == "jumpscare":
            self.draw_jumpscare()
        elif s == "dead":
            self.draw_dead()
        elif s == "win":
            self.draw_win()
        pygame.display.flip()

    def blit_center(self, font, text, color, y, surf=None):
        img = font.render(text, True, color)
        (surf or self.screen).blit(img, img.get_rect(center=(W // 2, y)))

    def project(self, sx, sy):
        """World point -> (screen x, depth) or None if behind the camera."""
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        relx, rely = sx - self.px, sy - self.py
        depth = relx * ca + rely * sa
        side = -relx * sa + rely * ca
        if depth < 0.12:
            return None
        return W / 2 * (1 + side / (depth * FOVK)), depth

    def draw_sprite(self, scr, sx, sy, img, hscale, hz, lift=0.0, min_depth=0.25, max_depth=99.0):
        pr = self.project(sx, sy)
        if not pr or pr[1] > max_depth:
            return None
        scx, depth = pr
        depth = max(depth, min_depth)
        hgt = H / depth * hscale
        wid = hgt * img.get_width() / img.get_height()
        floor_y = hz + H / (2 * depth) - H / depth * lift
        top = floor_y - hgt
        left = scx - wid / 2
        if left > W or left + wid < 0 or wid < 1 or hgt < 1:
            return None
        scaled = pygame.transform.scale(img, (int(wid) + 1, int(hgt) + 1))
        lv = min(LEVELS - 1, int(depth * LEVK))
        c = int(255 * math.exp(-lv / LEVK * 0.30))
        scaled.fill((c, c, c), special_flags=pygame.BLEND_RGB_MULT)
        c0 = max(0, int(left // CW))
        c1 = min(NCOL - 1, int((left + wid) // CW))
        zb = self.zbuf
        for col in range(c0, c1 + 1):
            if depth < zb[col]:
                x0 = col * CW
                scr.blit(scaled, (x0, int(top)), pygame.Rect(int(x0 - left), 0, CW, int(hgt) + 1))
        return scx, top, hgt, depth

    def draw_world(self):
        scr = self.screen
        playing = self.state == "play"
        shake = 0.0
        if playing:
            shake = clamp((5.5 - self.ent_dist) / 5.5, 0, 1) * 7 + (100 - self.sanity) / 100 * 5
        ox, oy = random.uniform(-shake, shake), random.uniform(-shake, shake)
        hz = int(H / 2 + self.bob + oy)

        scr.blit(self.bg, (0, hz - H))

        # walls
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        plx, ply = -sa * FOVK, ca * FOVK
        px, py = self.px, self.py
        zb = self.zbuf
        texcols = self.tex_cols
        wallvar = self.wallvar
        scale = pygame.transform.scale
        blit = scr.blit
        for c in range(NCOL):
            camx = 2 * (c + 0.5) / NCOL - 1
            rdx, rdy = ca + plx * camx, sa + ply * camx
            perp, side, wx, mx, my = self.dda(px, py, rdx, rdy)
            zb[c] = perp
            texx = int(wx * TEX)
            if (side == 0 and rdx > 0) or (side == 1 and rdy < 0):
                texx = TEX - 1 - texx
            lv = int(perp * LEVK)
            if lv >= LEVELS:
                continue
            column = texcols[wallvar[my][mx]][side][lv][texx]
            lh = H / perp
            top = hz - lh / 2
            x = int(c * CW + ox)
            if lh <= H:
                blit(scale(column, (CW, int(lh) + 1)), (x, int(top)))
            else:
                ty0 = (-top) / lh * TEX
                th = H / lh * TEX
                ty0 = clamp(ty0, 0, TEX - 1)
                th = clamp(th, 1, TEX - ty0)
                sub = column.subsurface((0, int(ty0), 1, max(1, int(th))))
                blit(scale(sub, (CW, H)), (x, 0))

        # sprites, far to near
        sprites = []
        for p in self.pages:
            sprites.append((p[0], p[1], self.page_img, 0.2, 0.0))
        for b in self.batteries:
            sprites.append((b[0], b[1], self.batt_img, 0.17, 0.0))
        for hd in self.hands:
            if abs(hd["x"] - px) < 8 and abs(hd["y"] - py) < 8:
                fr = self.hand_frames[hd["var"]]
                grab = hd["twitch"] > 0 and int(hd["twitch"] * 10) % 2 == 0
                sprites.append((hd["x"], hd["y"], fr[1] if grab else fr[0], 0.24, hd["lift"]))
        sprites.append((self.exit[0], self.exit[1],
                        self.door_open if self.collected >= PAGES_TOTAL else self.door_locked, 0.95, 0.0))
        ent_img = self.ent_frames[int(self.t * 9) % 3]
        sprites.append((self.ex, self.ey, ent_img, 1.12, 0.0, "ent"))
        if self.glimpse > 0:
            ga = self.angle + self.glimpse_side * 0.45
            d, *_ = self.dda(px, py, math.cos(ga), math.sin(ga))
            d = min(d - 0.4, 4.5)
            if d > 1.5:
                sprites.append((px + math.cos(ga) * d, py + math.sin(ga) * d, ent_img, 1.12, 0.0))
        sprites.sort(key=lambda s_: -((s_[0] - px) ** 2 + (s_[1] - py) ** 2))
        ent_screen = None
        for sp in sprites:
            r = self.draw_sprite(scr, sp[0], sp[1], sp[2], sp[3], hz, sp[4])
            if len(sp) > 5 and r:
                ent_screen = r

        # flashlight
        if self.light_on:
            mx_off = int(-self.sway * 2 + math.sin(self.bob_phase * 0.5) * 8 + ox)
            my_off = int(abs(self.bob) * 0.8 + oy)
            scr.blit(self.mask, (-MASK_PAD + mx_off, -MASK_PAD + my_off), special_flags=pygame.BLEND_RGB_MULT)
            if self.battery < 25:
                k = int(255 * (0.5 + self.battery / 50))
                scr.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)
        else:
            scr.fill((16, 16, 20), special_flags=pygame.BLEND_RGB_MULT)

        # its eyes, in the dark
        if (ent_screen and not self.seen and self.ent_dist < 8 and getattr(self, "ent_visible_line", False)
                and (self.t * 3) % 4 > 0.25):
            scx, top, hgt, depth = ent_screen
            col = int(scx // CW)
            if 0 <= col < NCOL and depth < self.zbuf[col] + 0.05:
                glow = int(clamp(230 - self.ent_dist * 20, 70, 230))
                ey = int(top + hgt * 31 / 210)
                er = max(1, int(hgt / 120))
                for e in (-5, 5):
                    pygame.draw.circle(scr, (glow, 8, 8), (int(scx + e * hgt / 210), ey), er)

        # the flashlight in your hand
        hx = int(W * 0.72 - self.sway * 0.6 + math.sin(self.bob_phase * 0.5) * 6)
        hy = int(H + 10 + abs(self.bob) * 1.5)
        body = [(hx - 30, hy), (hx + 70, hy), (hx + 34, hy - 150), (hx + 4, hy - 150)]
        pygame.draw.polygon(scr, (22, 22, 25), body)
        pygame.draw.polygon(scr, (40, 40, 45), [(hx + 30, hy), (hx + 52, hy), (hx + 30, hy - 150), (hx + 22, hy - 150)])
        head = pygame.Rect(0, 0, 54, 22)
        head.center = (hx + 19, hy - 155)
        pygame.draw.ellipse(scr, (30, 30, 34), head)
        lens = head.inflate(-10, -8)
        pygame.draw.ellipse(scr, (230, 220, 180) if self.light_on else (20, 20, 22), lens)
        pygame.draw.polygon(scr, (52, 40, 34), [(hx - 50, H), (hx - 30, hy - 60), (hx + 70, hy - 50), (hx + 90, H)])

        # red pulse when it is near
        if self.ent_dist < 5.5 and playing:
            red = pygame.Surface((W, H), pygame.SRCALPHA)
            a_ = int(clamp((5.5 - self.ent_dist) / 5.5, 0, 1) * (40 + 30 * math.sin(self.t * 9)))
            red.fill((120, 0, 0, max(0, a_)))
            scr.blit(red, (0, 0))

        scr.blit(self.vignette, (0, 0))
        scr.blit(self.grain[int(self.t * 24) % 4], (0, 0))
        if self.sanity < 60:
            g2 = self.grain[(int(self.t * 30) + 2) % 4]
            for _ in range(int((60 - self.sanity) / 15)):
                scr.blit(g2, (random.randint(-20, 20), random.randint(-20, 20)))
        if self.sub_t > 0:
            scr.fill((0, 0, 0))
            self.blit_center(self.f_huge, self.sub_text, (170, 0, 0), H // 2, scr)
        self.draw_hud()

    def draw_hud(self):
        scr = self.screen
        pygame.draw.rect(scr, (60, 60, 60), (20, H - 40, 120, 14), 1)
        bc = (170, 160, 90) if self.battery > 25 else (170, 40, 30)
        pygame.draw.rect(scr, bc, (22, H - 38, int(116 * self.battery / 100), 10))
        scr.blit(self.f_small.render("LIGHT", True, (110, 110, 110)), (20, H - 62))
        pygame.draw.rect(scr, (60, 60, 60), (160, H - 40, 90, 14), 1)
        pygame.draw.rect(scr, (90, 110, 130), (162, H - 38, int(86 * self.stamina / 100), 10))
        scr.blit(self.f_small.render("BREATH", True, (110, 110, 110)), (160, H - 62))
        t = self.f_mid.render("PAGES  %d / %d" % (self.collected, PAGES_TOTAL), True, (150, 140, 120))
        scr.blit(t, (W - t.get_width() - 24, 20))
        if self.msg_t > 0:
            alpha = clamp(self.msg_t, 0, 1)
            self.blit_center(self.f_mid, self.msg_text, tuple(int(c * alpha) for c in (200, 190, 170)), 70)
        if self.sanity < 35 and self.seen and int(self.t * 6) % 2 == 0:
            self.blit_center(self.f_big, "LOOK AWAY", (160, 0, 0), H // 2 - 160)

    def overlay_text(self, lines):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 190))
        self.screen.blit(s, (0, 0))
        for i, ln in enumerate(lines):
            self.blit_center(self.f_mid if i else self.f_big, ln, (180, 170, 160), H // 2 - 60 + i * 50)

    def wrap(self, text, font, width):
        words, lines, cur = text.split(), [], ""
        for w_ in words:
            test = (cur + " " + w_).strip()
            if font.size(test)[0] > width:
                lines.append(cur)
                cur = w_
            else:
                cur = test
        if cur:
            lines.append(cur)
        return lines

    def draw_note(self):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        self.screen.blit(s, (0, 0))
        paper = pygame.Rect(0, 0, 560, 420)
        paper.center = (W // 2, H // 2)
        pygame.draw.rect(self.screen, (196, 186, 158), paper)
        pygame.draw.rect(self.screen, (120, 108, 88), paper, 3)
        rnd = random.Random(self.note_idx)
        for _ in range(4):
            pygame.draw.ellipse(self.screen, (150, 125, 95),
                                (paper.x + rnd.randint(10, 480), paper.y + rnd.randint(10, 360), rnd.randint(20, 60), rnd.randint(14, 40)))
        hdr = self.f_note.render("page %d" % (self.note_idx + 1), True, (90, 30, 25))
        self.screen.blit(hdr, (paper.x + 30, paper.y + 24))
        shown = NOTES[self.note_idx][: int(self.t * 45)]
        for i, ln in enumerate(self.wrap(shown, self.f_note, paper.width - 60)):
            j = random.uniform(-0.6, 0.6) if self.note_idx in (2, 5) else 0
            self.screen.blit(self.f_note.render(ln, True, (35, 25, 20)), (paper.x + 30 + j, paper.y + 70 + i * 30))
        if self.t > 0.6:
            self.blit_center(self.f_small, "[ SPACE ]", (150, 140, 130), paper.bottom + 30)

    def draw_title(self):
        scr = self.screen
        scr.fill((0, 0, 0))
        if self.title_face > 0:
            face = pygame.Surface((W, H))
            draw_face(face, W // 2, H // 2, 1.0)
            face.set_alpha(28)
            scr.blit(face, (0, 0))
        col = (150, 8, 8) if random.random() > 0.06 else (40, 0, 0)
        self.blit_center(self.f_huge, "T H E   H O L L O W", col, 200)
        self.blit_center(self.f_mid, "Find the 6 pages.  Find the door.  Do not let it touch you.", (150, 140, 130), 320)
        lines = ["WASD - walk      MOUSE - look around      SHIFT - run      F - flashlight",
                 "It cannot move while your light is on it.",
                 "But do not stare for too long."]
        for i, ln in enumerate(lines):
            self.blit_center(self.f_small, ln, (110, 105, 100), 390 + i * 32)
        if int(self.t * 2) % 2 == 0:
            self.blit_center(self.f_mid, "press ENTER", (170, 160, 150), 540)
        self.blit_center(self.f_small, "headphones on.  lights off.", (70, 65, 60), 640)
        scr.blit(self.grain[int(self.t * 24) % 4], (0, 0))

    def draw_jumpscare(self):
        scr = self.screen
        t = self.t
        if t < 0.06:
            scr.fill((255, 255, 255))
            return
        scr.fill((90, 0, 0) if int(t * 22) % 2 else (0, 0, 0))
        s = 0.8 + min(1.0, t * 2.5) * 0.5
        draw_face(scr, W // 2 + random.uniform(-30, 30), H // 2 - 30 * s + random.uniform(-30, 30), s, jit=10)
        scr.blit(self.grain[int(t * 30) % 4], (0, 0))
        scr.blit(self.grain[(int(t * 30) + 1) % 4], (0, 0))

    def draw_dead(self):
        scr = self.screen
        scr.fill((0, 0, 0))
        k = clamp(self.t / 2, 0, 1)
        self.blit_center(self.f_huge, "IT FOUND YOU", (int(150 * k), 0, 0), H // 2 - 60)
        mins, secs = divmod(int(self.alive_t), 60)
        self.blit_center(self.f_mid, "pages: %d / %d      survived: %d:%02d" % (self.collected, PAGES_TOTAL, mins, secs),
                         (int(130 * k), int(120 * k), int(110 * k)), H // 2 + 30)
        if self.t > 1.5:
            self.blit_center(self.f_small, "ENTER - try again        ESC - quit", (110, 105, 100), H // 2 + 110)
        scr.blit(self.grain[int(self.t * 24) % 4], (0, 0))

    def draw_win(self):
        scr = self.screen
        t = self.t
        scr.fill((0, 0, 0))
        if 6.0 < t < 6.35:
            draw_face(scr, W // 2, H // 2 - 30, 1.2, jit=8)
            return
        k = clamp(t / 2.5, 0, 1)
        if t < 6:
            self.blit_center(self.f_huge, "YOU ESCAPED", (int(190 * k), int(185 * k), int(170 * k)), H // 2 - 40)
            if t > 3:
                self.blit_center(self.f_mid, "...didn't you?", (120, 110, 100), H // 2 + 50)
        else:
            self.blit_center(self.f_big, "see you tomorrow night.", (140, 0, 0), H // 2 - 20)
            if t > 7.5:
                self.blit_center(self.f_small, "ENTER - play again        ESC - quit", (110, 105, 100), H // 2 + 70)
        scr.blit(self.grain[int(t * 24) % 4], (0, 0))

    # ---------------------------------------------------------------- loop
    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                if not self.handle(ev):
                    running = False
            if self.state != "pause":
                self.update(dt)
            self.draw()
        pygame.quit()


def main():
    pygame.mixer.pre_init(22050, -16, 2, 512)
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("THE HOLLOW")
    screen.fill((0, 0, 0))
    img = pygame.font.Font(None, 36).render("loading the dark...", True, (90, 80, 70))
    screen.blit(img, img.get_rect(center=(W // 2, H // 2)))
    pygame.display.flip()
    Game(screen).run()
    sys.exit()


if __name__ == "__main__":
    main()