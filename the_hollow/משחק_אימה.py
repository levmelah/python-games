#!/usr/bin/env python3
"""
THE HOLLOW  -  first-person psychological horror
================================================

Install:   pip install pygame numpy
Run:       python the_hollow.py

You ARE the character. You see only what your flashlight shows you.
Best played at night, lights off, headphones on (sound is directional).

Controls
  W / S          walk forward / back
  A / D          step sideways
  Mouse          look around   (Q / E or arrow keys also turn)
  Shift          run (limited breath)  - loud!
  C / Ctrl       sneak (slow and silent)
  F              flashlight on / off  (save battery)
  Space / Enter  close a page / continue
  Esc            pause (frees the mouse)

Goal: find the way out of the maze. Listen for the crickets - that's outside.
It freezes while your light is on it - but staring at it breaks your mind.
"""
import array
import math
import random
import sys
from collections import deque

import pygame

try:
    import numpy as np      # optional: textured floors & ceilings
except ImportError:
    np = None

W, H = 1024, 704
FPS = 60
MW = MH = 31          # maze size in tiles (odd)
TEX = 128             # wall texture size
CW = 4                # pixel width of one ray column
NCOL = W // CW
FOVK = 0.66           # camera plane length (~66 degree field of view)
SPOT = 0.26           # half-angle (radians) of the bright flashlight spot
MASK_PAD = 150
LEVELS = 22           # distance-darkness levels
LEVK = 2.6            # levels per tile of distance
MOUSE_SENS = 0.0025
PAGES_TOTAL = 0       # no pages any more: just get out

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
            pygame.mixer.set_reserved(6)
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
            self.grind = self._snd(self._grind())
            self.crunch = self._snd(self._crunch())
            self.breath = self._snd(self._breath())
            self.ch_heart = pygame.mixer.Channel(0)
            self.ch_drone = pygame.mixer.Channel(1)
            self.ch_static = pygame.mixer.Channel(2)
            self.ch_amb = [pygame.mixer.Channel(3), pygame.mixer.Channel(4)]
            self.amb_i = 0
            self.amb_cur = None
            self.musicbox = self._snd(self._musicbox())
            self.buzz = self._snd(self._buzz())
            self.clock = self._snd(self._clock())
            self.wind = self._snd(self._wind())
            self.drip = self._snd(self._drip())
            self.beep = self._snd(self._beep())
            self.crickets = self._snd(self._crickets())
            self.ch_out = pygame.mixer.Channel(5)
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
            for c in (self.ch_heart, self.ch_drone, self.ch_static, self.ch_out) + tuple(self.ch_amb):
                c.stop()
            self.amb_cur = None

    def ambience(self, snd, vol):
        """Crossfade the looping sound of the area you are in."""
        if not self.ok or snd is self.amb_cur:
            return
        self.ch_amb[self.amb_i].fadeout(1500)
        self.amb_i ^= 1
        self.amb_cur = snd
        if snd is not None:
            ch = self.ch_amb[self.amb_i]
            ch.set_volume(vol)
            ch.play(snd, loops=-1, fade_ms=2000)

    # -- area ambience
    def _musicbox(self):
        """A slightly out-of-tune music box playing a lullaby nobody remembers."""
        r = self.rate
        A = 440.0
        semis = [0, 3, 7, 5, 3, 2, 0, None, -5, 0, 2, 3, 2, -1, 0, None]
        step = 0.48
        n = int(r * step * len(semis))
        out = [0.0] * n
        rnd = random.Random(5)
        for i, sm in enumerate(semis):
            if sm is None:
                continue
            f = A * 2 ** (sm / 12) * (1 + rnd.uniform(-0.006, 0.006))
            s0 = int(i * step * r)
            for j in range(int(r * 1.1)):
                if s0 + j >= n:
                    break
                t = j / r
                env = math.exp(-t * 3.2)
                out[s0 + j] += env * (0.6 * math.sin(2 * math.pi * f * t) + 0.25 * math.sin(2 * math.pi * f * 2.76 * t) * math.exp(-t * 6))
        return [v * 0.55 for v in out]

    def _buzz(self):
        r = self.rate
        out = []
        crackle = 0.0
        for i in range(int(r * 2)):
            t = i / r
            ph = (t * 120) % 1.0
            if random.random() < 0.0008:
                crackle = 1.0
            crackle *= 0.997
            out.append(0.18 * (ph * 2 - 1) + 0.1 * math.sin(2 * math.pi * 240 * t) + crackle * random.uniform(-0.5, 0.5))
        return out

    def _clock(self):
        r = self.rate
        out = [0.0] * int(r * 2)
        for s0, f in ((0, 2200), (int(r * 1.0), 1600)):
            for j in range(int(r * 0.03)):
                t = j / r
                out[s0 + j] += math.sin(2 * math.pi * f * t) * math.exp(-t * 180) * 0.8 + random.uniform(-0.2, 0.2) * math.exp(-t * 300)
        return out

    def _wind(self):
        r = self.rate
        out, lp = [], 0.0
        n = int(r * 4)
        for i in range(n):
            t = i / r
            lp += (random.uniform(-1, 1) - lp) * (0.02 + 0.015 * math.sin(2 * math.pi * t / 4))
            fade = min(1, i / 2000, (n - i) / 2000)
            out.append(lp * 3.0 * (0.6 + 0.4 * math.sin(2 * math.pi * t / 4)) * fade)
        return out

    def _drip(self):
        r = self.rate
        out = []
        for i in range(int(r * 0.5)):
            t = i / r
            v = math.sin(2 * math.pi * (1500 - 900 * min(t * 20, 1)) * t) * math.exp(-t * 40)
            if t > 0.18:
                tt = t - 0.18
                v += 0.3 * math.sin(2 * math.pi * 700 * tt) * math.exp(-tt * 40)
            out.append(v * 0.7)
        return out

    def _crickets(self):
        """Night outside: crickets and a soft breeze. The sound of freedom."""
        r = self.rate
        n = int(r * 3)
        out, lp = [0.0] * n, 0.0
        rnd = random.Random(9)
        for f, start_times in ((4600, (0.1, 0.9, 1.7, 2.4)), (4150, (0.5, 1.3, 2.1))):
            for st in start_times:
                s0 = int(st * r)
                for j in range(int(r * 0.12)):
                    if s0 + j >= n:
                        break
                    t = j / r
                    pulse = 1.0 if (t * 30) % 1.0 < 0.5 else 0.0
                    out[s0 + j] += 0.25 * pulse * math.sin(2 * math.pi * f * t) * (1 - t / 0.12)
        for i in range(n):
            lp += (rnd.uniform(-1, 1) - lp) * 0.03
            fade = min(1, i / 1500, (n - i) / 1500)
            out[i] += lp * 1.2 * fade
        return out

    def _beep(self):
        r = self.rate
        return [0.35 * math.copysign(1, math.sin(2 * math.pi * 980 * i / r)) * (1 if i < r * 0.13 else 0) * math.exp(-i / r * 3)
                for i in range(int(r * 0.16))]

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


    def _grind(self):
        r = self.rate
        out, lp, ph = [], 0.0, 0.0
        for i in range(int(r * 0.7)):
            t = i / r
            lp += (random.uniform(-1, 1) - lp) * 0.05
            ph += (28 + 6 * math.sin(t * 20)) / r
            env = math.sin(math.pi * t / 0.7)
            out.append((lp * 2.2 + 0.5 * math.sin(2 * math.pi * ph) + random.uniform(-0.08, 0.08)) * env)
        return out

    def _crunch(self):
        r = self.rate
        out = []
        for i in range(int(r * 1.2)):
            t = i / r
            crack = random.uniform(-1, 1) if random.random() < 0.35 * math.exp(-t * 5) + 0.02 else 0.0
            out.append((crack + 0.8 * math.sin(2 * math.pi * (50 - 20 * t) * t)) * math.exp(-t * 2.5))
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
        for y in range(10, 140):   # night sky -> grass
            k = (y - 10) / 130
            pygame.draw.line(s, (int(60 + 60 * k), int(80 + 70 * k), int(130 + 60 * k)), (10, y), (69, y))
        pygame.draw.circle(s, (235, 240, 255), (52, 34), 7)               # the moon
        for x, h in ((14, 40), (24, 28), (60, 46), (68, 30)):              # tree silhouettes
            pygame.draw.polygon(s, (20, 26, 34), [(x - 6, 112), (x + 6, 112), (x, 112 - h)])
        pygame.draw.rect(s, (24, 34, 30), (10, 112, 60, 28))
        pygame.draw.line(s, (30, 18, 8), (40, 10), (40, 140), 1)
    else:
        for y in range(10, 140, 26):
            pygame.draw.line(s, (50, 30, 15), (8, y), (72, y), 2)
        pygame.draw.line(s, (130, 130, 130), (6, 30), (74, 110), 5)
        pygame.draw.line(s, (130, 130, 130), (74, 30), (6, 110), 5)
        pygame.draw.rect(s, (110, 100, 50), (30, 62, 20, 18))
    return s


# --------------------------------------------------------------------------- areas
def _noise(t, rnd, amount, lo=-14, hi=10):
    w, h = t.get_size()
    for _ in range(amount):
        x, y = rnd.randrange(w), rnd.randrange(h)
        c = t.get_at((x, y))
        d = rnd.randint(lo, hi)
        t.set_at((x, y), (clamp(c.r + d, 0, 255), clamp(c.g + d, 0, 255), clamp(c.b + d, 0, 255)))


def _grime(t, rnd, col=(30, 26, 20), height=40):
    """Dirt creeping up from the floor."""
    g = pygame.Surface((TEX, height), pygame.SRCALPHA)
    for y in range(height):
        a = int(150 * (y / height) ** 2)
        pygame.draw.line(g, col + (a,), (0, y), (TEX, y))
    t.blit(g, (0, TEX - height))
    for _ in range(5):
        x = rnd.randrange(TEX)
        pygame.draw.line(t, col, (x, TEX - height + rnd.randint(0, 20)), (x + rnd.randint(-2, 2), TEX), rnd.randint(1, 3))


def _scrawl(t, rnd, font, text, color, y=None):
    img = font.render(text, True, color)
    s = min(1.0, (TEX - 10) / img.get_width())
    img = pygame.transform.scale(img, (max(1, int(img.get_width() * s)), max(1, int(img.get_height() * s))))
    img = pygame.transform.rotate(img, rnd.uniform(-12, 12))
    t.blit(img, img.get_rect(center=(TEX // 2, y if y is not None else rnd.randint(40, 90))))


def tex_hospital(kind, rnd, font):
    t = pygame.Surface((TEX, TEX))
    t.fill((70, 80, 74))
    for ty in range(0, TEX, 16):
        for tx in range(0, TEX, 16):
            b = rnd.randint(150, 175)
            col = (b - 15, b, b - 8)
            if kind != "door" and rnd.random() < 0.04:
                col = (30, 34, 32)          # missing tile
            pygame.draw.rect(t, col, (tx + 1, ty + 1, 14, 14))
    pygame.draw.rect(t, (95, 120, 105), (0, 76, TEX, 10))   # stripe
    _noise(t, rnd, 2500)
    if kind == "door":
        d = pygame.Rect(26, 10, 76, 118)
        pygame.draw.rect(t, (88, 96, 92), d)
        pygame.draw.rect(t, (50, 56, 54), d, 3)
        win = pygame.Rect(46, 26, 36, 26)
        pygame.draw.rect(t, (8, 10, 10), win)
        pygame.draw.rect(t, (40, 46, 44), win, 2)
        pygame.draw.line(t, (40, 46, 44), win.midtop, win.midbottom, 2)
        if rnd.random() < 0.5:   # a face in the little window
            pygame.draw.ellipse(t, (120, 118, 110), (56, 32, 14, 18))
            pygame.draw.circle(t, (0, 0, 0), (60, 39), 2)
            pygame.draw.circle(t, (0, 0, 0), (66, 39), 2)
        pygame.draw.circle(t, (140, 140, 120), (92, 78), 4)
        plate = font.render("ROOM %d" % rnd.choice((13, 6, 66, 0, 4)), True, (30, 30, 30))
        t.blit(plate, plate.get_rect(center=(64, 64)))
    elif kind == "blood":
        red = (115, 8, 6)
        x = rnd.randint(10, 60)
        for i in range(5):   # dragged hand smear
            pygame.draw.line(t, red, (x + i * 5, 40 + rnd.randint(-3, 3)), (x + 40 + i * 5, 100 + rnd.randint(-5, 5)), 4)
    elif kind == "text":
        _scrawl(t, rnd, font, rnd.choice(("NURSE?", "NO VISITORS", "IT'S IN THE WARD")), (110, 10, 8))
    _grime(t, rnd, (40, 46, 30))
    return t


def tex_red(kind, rnd, font):
    t = pygame.Surface((TEX, TEX))
    t.fill((140, 26, 26))
    # damask pattern
    for py in range(0, TEX, 32):
        for px in range(0, TEX, 32):
            ox = 16 if (py // 32) % 2 else 0
            cx, cy = px + ox, py + 16
            pts = [(cx, cy - 12), (cx + 7, cy), (cx, cy + 12), (cx - 7, cy)]
            pygame.draw.polygon(t, (98, 14, 16), pts)
            pygame.draw.circle(t, (175, 120, 60), (cx, cy), 3)
            pygame.draw.arc(t, (98, 14, 16), (cx - 13, cy - 14, 26, 28), 0.5, 2.6, 2)
    pygame.draw.rect(t, (40, 22, 14), (0, 104, TEX, 24))      # dark wainscot
    pygame.draw.line(t, (150, 110, 50), (0, 104), (TEX, 104), 2)
    _noise(t, rnd, 2500)
    if kind == "portrait":
        fr = pygame.Rect(30, 14, 68, 82)
        pygame.draw.rect(t, (150, 110, 40), fr)
        pygame.draw.rect(t, (90, 60, 20), fr, 3)
        inner = fr.inflate(-14, -14)
        pygame.draw.rect(t, (24, 20, 18), inner)
        # a portrait whose face was scratched out
        pygame.draw.ellipse(t, (130, 116, 100), (inner.centerx - 12, inner.y + 10, 24, 30))
        pygame.draw.rect(t, (40, 34, 40), (inner.centerx - 18, inner.y + 40, 36, 30))
        for _ in range(7):
            x0 = inner.centerx + rnd.randint(-12, 12)
            pygame.draw.line(t, (10, 6, 6), (x0, inner.y + 10), (x0 + rnd.randint(-6, 6), inner.y + 40), 2)
    elif kind == "peel":
        r = pygame.Rect(rnd.randint(10, 60), rnd.randint(10, 50), rnd.randint(30, 50), rnd.randint(30, 50))
        pygame.draw.ellipse(t, (150, 140, 120), r)
        pygame.draw.ellipse(t, (60, 8, 10), r, 3)
    elif kind == "text":
        _scrawl(t, rnd, font, rnd.choice(("LET ME OUT", "SMILE", "HE WATCHES")), (20, 0, 0))
    return t


def tex_nursery(kind, rnd, font):
    t = pygame.Surface((TEX, TEX))
    t.fill((172, 150, 158))
    for x in range(0, TEX, 16):
        pygame.draw.rect(t, (150, 160, 175), (x, 0, 8, TEX))
    for _ in range(9):   # little stars
        cx, cy = rnd.randrange(TEX), rnd.randrange(96)
        pygame.draw.polygon(t, (200, 185, 120), [(cx, cy - 4), (cx + 2, cy), (cx, cy + 4), (cx - 2, cy)])
    pygame.draw.rect(t, (120, 100, 90), (0, 108, TEX, 20))
    _noise(t, rnd, 3000)
    if kind == "drawing":
        paper = pygame.Rect(22, 20, 84, 64)
        pygame.draw.rect(t, (220, 215, 200), paper)
        # child's crayon drawing: a house, a family... and something tall
        pygame.draw.polygon(t, (200, 40, 40), [(34, 58), (50, 44), (66, 58)], 2)
        pygame.draw.rect(t, (200, 40, 40), (36, 58, 28, 18), 2)
        for i, h in enumerate((14, 12, 8)):
            x = 72 + i * 7
            pygame.draw.circle(t, (40, 40, 200), (x, 76 - h - 3), 2)
            pygame.draw.line(t, (40, 40, 200), (x, 76 - h), (x, 76), 1)
        pygame.draw.line(t, (10, 10, 10), (98, 30), (98, 78), 4)
        pygame.draw.circle(t, (10, 10, 10), (98, 28), 5)
        pygame.draw.circle(t, (255, 255, 255), (96, 27), 1)
        pygame.draw.circle(t, (255, 255, 255), (100, 27), 1)
        _scrawl(t, rnd, font, "HE IS HERE", (20, 20, 20), 96)
    elif kind == "chart":
        pygame.draw.rect(t, (200, 190, 150), (56, 10, 16, 98))
        for i in range(8):
            pygame.draw.line(t, (60, 50, 40), (56, 14 + i * 12), (64, 14 + i * 12))
        pygame.draw.line(t, (120, 10, 8), (50, 8), (78, 8), 2)   # someone too tall was measured
    elif kind == "torn":
        r = pygame.Rect(rnd.randint(10, 60), rnd.randint(10, 50), 44, 48)
        pygame.draw.polygon(t, (60, 50, 50), [r.topleft, (r.right, r.top + 8), (r.right - 6, r.bottom), (r.left + 8, r.bottom - 4)])
        for i in range(4):
            x = r.left + 6 + i * 9
            pygame.draw.line(t, (25, 18, 18), (x, r.top + 6), (x + 8, r.bottom - 6), 2)   # claw marks
    _grime(t, rnd, (60, 45, 40), 30)
    return t


def tex_wood(kind, rnd, font):
    t = pygame.Surface((TEX, TEX))
    for x in range(0, TEX, 16):
        b = rnd.randint(95, 125)
        pygame.draw.rect(t, (b, int(b * 0.68), int(b * 0.42)), (x, 0, 16, TEX))
        for _ in range(4):
            gx = x + rnd.randint(2, 13)
            pygame.draw.line(t, (b - 22, int(b * 0.68) - 18, int(b * 0.42) - 12), (gx, 0), (gx + rnd.randint(-2, 2), TEX), 1)
        pygame.draw.line(t, (20, 12, 6), (x, 0), (x, TEX), 2)
        for ny in (10, TEX - 12):
            pygame.draw.circle(t, (40, 40, 42), (x + 8, ny), 2)
    _noise(t, rnd, 2500)
    if kind == "claw":
        x0, y0 = rnd.randint(20, 80), rnd.randint(20, 60)
        for i in range(4):
            pygame.draw.line(t, (190, 150, 110), (x0 + i * 8, y0), (x0 + i * 8 + 14, y0 + 50), 3)
            pygame.draw.line(t, (30, 20, 12), (x0 + i * 8 + 2, y0), (x0 + i * 8 + 16, y0 + 50), 1)
    elif kind == "window":
        w_ = pygame.Rect(24, 24, 80, 60)
        pygame.draw.rect(t, (4, 4, 6), w_)
        for i in range(3):
            y = w_.y + 8 + i * 20
            pygame.draw.rect(t, (90, 62, 38), (w_.x - 6, y, w_.width + 12, 10))
        if rnd.random() < 0.6:   # fingers between the boards
            for i in range(3):
                pygame.draw.line(t, (170, 160, 145), (50 + i * 6, w_.y + 18), (50 + i * 6, w_.y + 26), 3)
    elif kind == "text":
        _scrawl(t, rnd, font, rnd.choice(("DON'T GO DOWN", "COUNT THE DOORS", "IT LIVES HERE")), (190, 170, 140))
    return t


def tex_crypt(kind, rnd, font):
    t = pygame.Surface((TEX, TEX))
    t.fill((40, 42, 48))
    for row in range(0, TEX, 32):
        off = 24 if (row // 32) % 2 else 0
        for col in range(-1, 3):
            b = rnd.randint(92, 112)
            pygame.draw.rect(t, (b, b + 2, b + 8), (col * 48 + off + 2, row + 2, 44, 28))
    _noise(t, rnd, 3500, -20, 10)
    for _ in range(4):   # moss
        x = rnd.randrange(TEX)
        pygame.draw.ellipse(t, (50, 70, 44), (x, rnd.randrange(TEX), rnd.randint(8, 22), rnd.randint(4, 10)))
    if kind == "niche":
        n = pygame.Rect(36, 34, 56, 48)
        pygame.draw.ellipse(t, (12, 12, 14), (n.x, n.y - 18, n.width, 40))
        pygame.draw.rect(t, (12, 12, 14), n)
        # skull
        pygame.draw.ellipse(t, (190, 182, 160), (52, 50, 24, 22))
        pygame.draw.rect(t, (190, 182, 160), (57, 68, 14, 8))
        pygame.draw.circle(t, (10, 10, 10), (59, 60), 4)
        pygame.draw.circle(t, (10, 10, 10), (69, 60), 4)
        pygame.draw.polygon(t, (10, 10, 10), [(64, 64), (62, 68), (66, 68)])
    elif kind == "chains":
        for x in (40, 88):
            for y in range(0, 90, 8):
                pygame.draw.ellipse(t, (60, 58, 56), (x - 3 + (y // 8 % 2), y, 7, 10), 2)
        pygame.draw.rect(t, (60, 58, 56), (30, 90, 70, 8), 2)
    elif kind == "text":
        _scrawl(t, rnd, font, rnd.choice(("REST", "WE WAITED", "YOU'RE LATE")), (150, 150, 160))
    _grime(t, rnd, (20, 30, 18), 30)
    return t


def tex_plaster(kind, rnd, font):
    return make_wall_texture(kind, rnd, font)


# name shown on screen, texture maker, [(kind, weight)], wall tint, ceiling, floor, decorations
THEMES = [
    ("THE HANDS",   tex_plaster,  [("plain", 4), ("hands", 7), ("blood", 1)],
     (255, 246, 232), (18, 16, 15), (58, 50, 43), ["hand"]),
    ("THE WARD",    tex_hospital, [("tiles", 7), ("door", 2), ("blood", 1), ("text", 1)],
     (225, 255, 238), (12, 17, 15), (42, 54, 48), ["wheelchair", "bed", "lamp", "lamp"]),
    ("THE RED ROOM", tex_red,     [("plain", 6), ("portrait", 3), ("peel", 1), ("text", 1)],
     (255, 205, 195), (22, 6, 6), (58, 18, 15), ["candle", "chair"]),
    ("THE NURSERY", tex_nursery,  [("plain", 6), ("drawing", 2), ("chart", 1), ("torn", 1)],
     (255, 240, 250), (17, 15, 19), (52, 44, 50), ["doll", "doll", "crib"]),
    ("THE CELLAR",  tex_wood,     [("plain", 6), ("claw", 2), ("window", 2), ("text", 1)],
     (255, 226, 190), (14, 10, 7), (50, 35, 22), ["lantern", "barrel"]),
    ("THE CRYPT",   tex_crypt,    [("plain", 6), ("niche", 3), ("chains", 1), ("text", 1)],
     (205, 222, 255), (10, 11, 15), (36, 39, 46), ["candle", "candle", "skulls"]),
]


# --------------------------------------------------------------------------- decorations
def deco_candle():
    s = pygame.Surface((24, 60), pygame.SRCALPHA)
    pygame.draw.rect(s, (220, 210, 180), (8, 24, 8, 36))
    pygame.draw.ellipse(s, (240, 230, 200), (6, 54, 12, 6))
    pygame.draw.ellipse(s, (255, 170, 40), (7, 8, 10, 18))
    pygame.draw.ellipse(s, (255, 240, 180), (9, 13, 6, 10))
    return s


def deco_lantern():
    s = pygame.Surface((30, 90), pygame.SRCALPHA)
    pygame.draw.line(s, (40, 40, 40), (15, 0), (15, 46), 2)
    pygame.draw.rect(s, (30, 26, 22), (5, 46, 20, 32), 2)
    pygame.draw.rect(s, (255, 190, 80), (8, 50, 14, 25))
    pygame.draw.rect(s, (255, 240, 190), (12, 56, 6, 12))
    pygame.draw.polygon(s, (30, 26, 22), [(3, 46), (27, 46), (15, 38)])
    return s


def deco_doll():
    s = pygame.Surface((40, 56), pygame.SRCALPHA)
    pygame.draw.polygon(s, (150, 40, 60), [(20, 22), (34, 54), (6, 54)])          # dress
    pygame.draw.line(s, (210, 190, 175), (8, 30), (2, 44), 3)
    pygame.draw.line(s, (210, 190, 175), (32, 30), (38, 44), 3)
    pygame.draw.circle(s, (215, 200, 185), (20, 14), 11)                          # porcelain head
    pygame.draw.line(s, (90, 80, 70), (14, 6), (22, 18), 1)                         # crack
    pygame.draw.circle(s, (0, 0, 0), (16, 13), 3)
    pygame.draw.circle(s, (0, 0, 0), (24, 13), 3)
    pygame.draw.line(s, (120, 20, 20), (17, 20), (23, 20), 1)
    pygame.draw.arc(s, (60, 40, 20), (8, 0, 24, 18), 0.2, 2.9, 4)                  # hair
    return s


def deco_wheelchair():
    s = pygame.Surface((70, 70), pygame.SRCALPHA)
    pygame.draw.circle(s, (50, 52, 54), (24, 48), 20, 3)
    pygame.draw.line(s, (50, 52, 54), (24, 30), (24, 66), 1)
    pygame.draw.line(s, (50, 52, 54), (6, 48), (42, 48), 1)
    pygame.draw.circle(s, (50, 52, 54), (58, 62), 6, 2)
    pygame.draw.rect(s, (70, 90, 85), (18, 30, 34, 8))
    pygame.draw.rect(s, (70, 90, 85), (18, 6, 8, 28))
    pygame.draw.line(s, (90, 92, 94), (20, 6), (12, 2), 3)
    pygame.draw.line(s, (90, 92, 94), (52, 38), (58, 58), 3)
    return s


def deco_bed():
    s = pygame.Surface((110, 60), pygame.SRCALPHA)
    pygame.draw.rect(s, (90, 95, 95), (4, 24, 102, 6))
    for x in (6, 104):
        pygame.draw.line(s, (90, 95, 95), (x, 10), (x, 60), 3)
    pygame.draw.rect(s, (190, 192, 185), (8, 14, 96, 12))
    pygame.draw.ellipse(s, (205, 205, 198), (14, 4, 30, 16))           # something under the sheet...
    pygame.draw.ellipse(s, (195, 196, 190), (40, 8, 60, 14))
    pygame.draw.rect(s, (110, 10, 8), (60, 24, 12, 4))
    return s


def deco_chair():
    s = pygame.Surface((50, 80), pygame.SRCALPHA)
    wood = (70, 38, 22)
    pygame.draw.rect(s, wood, (8, 0, 6, 80))
    pygame.draw.rect(s, wood, (36, 0, 6, 80))
    for y in (8, 20, 32):
        pygame.draw.line(s, wood, (10, y), (40, y), 3)
    pygame.draw.rect(s, (100, 20, 26), (4, 44, 42, 8))
    pygame.draw.line(s, wood, (6, 52), (6, 80), 4)
    pygame.draw.line(s, wood, (44, 52), (44, 80), 4)
    return s


def deco_crib():
    s = pygame.Surface((90, 60), pygame.SRCALPHA)
    c = (200, 190, 175)
    pygame.draw.rect(s, c, (2, 10, 86, 6))
    pygame.draw.rect(s, c, (2, 46, 86, 6))
    for x in range(4, 90, 9):
        pygame.draw.line(s, c, (x, 10), (x, 60), 2)
    pygame.draw.circle(s, (160, 140, 110), (60, 40), 8)       # a teddy bear, watching
    pygame.draw.circle(s, (160, 140, 110), (54, 33), 3)
    pygame.draw.circle(s, (160, 140, 110), (66, 33), 3)
    pygame.draw.circle(s, (0, 0, 0), (57, 39), 1)
    pygame.draw.line(s, (120, 10, 8), (62, 38), (63, 44), 2)   # one eye torn out
    return s


def deco_barrel():
    s = pygame.Surface((50, 70), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (75, 48, 26), (2, 0, 46, 70))
    pygame.draw.rect(s, (75, 48, 26), (4, 6, 42, 58))
    for y in (12, 56):
        pygame.draw.line(s, (40, 40, 40), (3, y), (47, y), 3)
    for x in (14, 25, 36):
        pygame.draw.line(s, (45, 28, 14), (x, 4), (x, 66), 1)
    return s


def deco_skulls():
    s = pygame.Surface((70, 40), pygame.SRCALPHA)
    for (x, y, r) in ((14, 26, 11), (36, 28, 12), (56, 26, 10), (26, 12, 10), (46, 12, 10)):
        pygame.draw.ellipse(s, (190, 182, 160), (x - r, y - r, 2 * r, int(1.8 * r)))
        pygame.draw.circle(s, (12, 10, 10), (x - r // 3, y - 1), max(2, r // 4))
        pygame.draw.circle(s, (12, 10, 10), (x + r // 3, y - 1), max(2, r // 4))
    return s


# name -> (maker, height in wall units, lift above floor, glows?)
DECOS = {
    "candle": (deco_candle, 0.16, 0.0, True),
    "lantern": (deco_lantern, 0.32, 0.55, True),
    "doll": (deco_doll, 0.2, 0.0, False),
    "wheelchair": (deco_wheelchair, 0.42, 0.0, False),
    "bed": (deco_bed, 0.36, 0.0, False),
    "chair": (deco_chair, 0.45, 0.0, False),
    "crib": (deco_crib, 0.32, 0.0, False),
    "barrel": (deco_barrel, 0.36, 0.0, False),
    "skulls": (deco_skulls, 0.14, 0.0, False),
}


def make_glow():
    g = pygame.Surface((128, 128))
    g.fill((0, 0, 0))
    for i in range(40):
        k = i / 39
        b = int(150 * k ** 2)
        pygame.draw.circle(g, (b, int(b * 0.6), int(b * 0.25)), (64, 64), int(64 * (1 - k) + 2))
    return g


# --------------------------------------------------------------------------- floors & ceilings
FTEX = 64   # floor / ceiling texture size


def _ftex(base, rnd, noise=900):
    t = pygame.Surface((FTEX, FTEX))
    t.fill(base)
    for _ in range(noise):
        x, y = rnd.randrange(FTEX), rnd.randrange(FTEX)
        d = rnd.randint(-16, 12)
        t.set_at((x, y), tuple(clamp(c + d, 0, 255) for c in base))
    return t


def floor_hands(rnd):           # cracked, stained concrete
    t = _ftex((112, 104, 94), rnd, 1400)
    for _ in range(3):
        pygame.draw.ellipse(t, (88, 80, 72), (rnd.randrange(FTEX), rnd.randrange(FTEX), rnd.randint(10, 30), rnd.randint(8, 20)))
    x, y = rnd.randrange(FTEX), 0
    for _ in range(6):
        nx, ny = x + rnd.randint(-8, 8), y + rnd.randint(6, 14)
        pygame.draw.line(t, (60, 55, 50), (x, y), (nx, ny), 1)
        x, y = nx, ny
    pygame.draw.rect(t, (95, 88, 80), (0, 0, FTEX, FTEX), 1)
    return t


def floor_ward(rnd):            # checkerboard linoleum
    t = pygame.Surface((FTEX, FTEX))
    for j in range(2):
        for i in range(2):
            c = (170, 182, 170) if (i + j) % 2 == 0 else (70, 96, 86)
            pygame.draw.rect(t, c, (i * 32, j * 32, 32, 32))
    for _ in range(900):
        x, y = rnd.randrange(FTEX), rnd.randrange(FTEX)
        c = t.get_at((x, y))
        d = rnd.randint(-18, 8)
        t.set_at((x, y), (clamp(c.r + d, 0, 255), clamp(c.g + d, 0, 255), clamp(c.b + d, 0, 255)))
    if rnd.random() < 0.5:
        pygame.draw.ellipse(t, (90, 20, 16), (rnd.randint(4, 40), rnd.randint(4, 40), 14, 9))
    return t


def floor_red(rnd):             # old patterned carpet
    t = _ftex((92, 16, 18), rnd, 1600)
    for (cx, cy) in ((16, 16), (48, 48), (16, 48), (48, 16)):
        pygame.draw.polygon(t, (128, 76, 30), [(cx, cy - 9), (cx + 9, cy), (cx, cy + 9), (cx - 9, cy)], 2)
        pygame.draw.circle(t, (60, 8, 10), (cx, cy), 3)
    pygame.draw.rect(t, (60, 8, 10), (0, 0, FTEX, FTEX), 2)
    return t


def floor_nursery(rnd):         # pale wooden boards
    t = pygame.Surface((FTEX, FTEX))
    for i in range(4):
        b = rnd.randint(118, 140)
        pygame.draw.rect(t, (b, int(b * 0.8), int(b * 0.6)), (0, i * 16, FTEX, 16))
        pygame.draw.line(t, (60, 45, 34), (0, i * 16), (FTEX, i * 16), 1)
        x = rnd.randrange(FTEX)
        pygame.draw.line(t, (60, 45, 34), (x, i * 16), (x, i * 16 + 15), 1)
        for _ in range(3):
            y = i * 16 + rnd.randint(3, 13)
            pygame.draw.line(t, (b - 20, int(b * 0.8) - 18, int(b * 0.6) - 14), (rnd.randrange(FTEX), y), (rnd.randrange(FTEX), y), 1)
    return t


def floor_cellar(rnd):          # packed dirt and stones
    t = _ftex((70, 54, 38), rnd, 2200)
    for _ in range(7):
        b = rnd.randint(80, 105)
        r = pygame.Rect(rnd.randrange(FTEX), rnd.randrange(FTEX), rnd.randint(5, 11), rnd.randint(4, 9))
        pygame.draw.ellipse(t, (b, b - 6, b - 14), r)
        pygame.draw.ellipse(t, (40, 32, 24), r, 1)
    return t


def floor_crypt(rnd):           # flagstones
    t = pygame.Surface((FTEX, FTEX))
    t.fill((36, 38, 44))
    for r in ((1, 1, 38, 30), (41, 1, 22, 30), (1, 33, 22, 30), (25, 33, 38, 30)):
        b = rnd.randint(78, 96)
        pygame.draw.rect(t, (b, b + 2, b + 8), r)
    for _ in range(1500):
        x, y = rnd.randrange(FTEX), rnd.randrange(FTEX)
        c = t.get_at((x, y))
        d = rnd.randint(-18, 8)
        t.set_at((x, y), (clamp(c.r + d, 0, 255), clamp(c.g + d, 0, 255), clamp(c.b + d, 0, 255)))
    return t


def ceil_plain(base, beams=None):
    def f(rnd):
        t = _ftex(base, rnd, 1200)
        if beams:
            pygame.draw.rect(t, beams, (0, 26, FTEX, 12))
            pygame.draw.line(t, tuple(max(0, c - 20) for c in beams), (0, 26), (FTEX, 26), 1)
        return t
    return f


def ceil_ward(rnd):             # suspended ceiling tiles, some missing
    t = _ftex((150, 156, 150), rnd, 1500)
    pygame.draw.rect(t, (95, 100, 96), (0, 0, FTEX, FTEX), 2)
    pygame.draw.line(t, (95, 100, 96), (32, 0), (32, FTEX), 2)
    pygame.draw.line(t, (95, 100, 96), (0, 32), (FTEX, 32), 2)
    if rnd.random() < 0.5:
        pygame.draw.rect(t, (6, 6, 6), (34, 34, 28, 28))
    return t


def ceil_nursery(rnd):
    t = _ftex((120, 112, 130), rnd, 800)
    for _ in range(4):
        cx, cy = rnd.randrange(FTEX), rnd.randrange(FTEX)
        pygame.draw.polygon(t, (190, 175, 110), [(cx, cy - 3), (cx + 2, cy), (cx, cy + 3), (cx - 2, cy)])
    return t


# same order as THEMES
FLOOR_MAKERS = [floor_hands, floor_ward, floor_red, floor_nursery, floor_cellar, floor_crypt]
CEIL_MAKERS = [ceil_plain((96, 92, 86)), ceil_ward, ceil_plain((60, 20, 18), (50, 30, 20)), ceil_nursery,
               ceil_plain((62, 46, 32), (40, 28, 18)), ceil_plain((58, 60, 66))]


# --------------------------------------------------------------------------- better creature
def make_entity_sprite(frame, mouth=False):
    """Pale, starved, far too tall. Drawn at high resolution with soft shading."""
    S = 2
    w, h = 70 * S, 210 * S
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    rnd = random.Random(frame)
    skin = (176, 170, 160)
    dark = (96, 90, 86)
    J = lambda v=2: rnd.randint(-v, v) * S

    def L(a, b, wd, col=skin):
        pygame.draw.line(s, col, (a[0] * S, a[1] * S), (b[0] * S, b[1] * S), wd * S)
        pygame.draw.circle(s, col, (a[0] * S, a[1] * S), wd * S // 2)
        pygame.draw.circle(s, col, (b[0] * S, b[1] * S), wd * S // 2)

    # legs with knobbly knees
    for lx, fx in ((31, 27), (39, 43)):
        kx = lx + rnd.randint(-1, 1)
        L((lx, 140), (kx, 175), 5)
        L((kx, 175), (fx + rnd.randint(-2, 2), 208), 4)
        pygame.draw.circle(s, skin, (kx * S, 175 * S), 4 * S)
    # torso: ribcage and sunken belly
    pygame.draw.ellipse(s, skin, (22 * S, 52 * S, 26 * S, 62 * S))
    pygame.draw.ellipse(s, skin, (25 * S, 100 * S, 20 * S, 46 * S))
    for i in range(6):
        pygame.draw.arc(s, dark, (24 * S, (60 + i * 8) * S, 22 * S, 9 * S), 3.5, 5.9, S)
    pygame.draw.line(s, dark, (35 * S, 58 * S), (35 * S, 108 * S), S)
    # arms: shoulder -> elbow -> hand, far too long
    for side in (-1, 1):
        sh = (35 + side * 11, 58)
        el = (35 + side * (17 + rnd.randint(0, 3)), 112)
        hd = (35 + side * (20 + rnd.randint(0, 5)), 168)
        L(sh, el, 4)
        L(el, hd, 3)
        pygame.draw.circle(s, skin, (el[0] * S, el[1] * S), 3 * S)
        for f in (-5, -2, 1, 4):
            tip = (hd[0] + f + side, hd[1] + 22 + rnd.randint(0, 6))
            mid = (hd[0] + f * 0.6, hd[1] + 11)
            L(hd, (int(mid[0]), mid[1]), 1)
            L((int(mid[0]), mid[1]), tip, 1)
    # neck + head, tilted
    L((35, 40), (35, 56), 6)
    hx = 36 + rnd.randint(-1, 1)
    head = pygame.Rect(0, 0, 25 * S, 33 * S)
    head.center = (hx * S, 32 * S)
    pygame.draw.ellipse(s, skin, head)
    # sunken cheeks
    for ex in (-6, 6):
        pygame.draw.ellipse(s, dark, ((hx + ex - 2) * S, 37 * S, 4 * S, 7 * S))
    # long wet black hair
    for i in range(11):
        x0 = hx - 13 + i * 2.6
        pts = [(x0 * S, 15 * S)]
        y = 15
        x = x0
        for _ in range(4):
            x += rnd.uniform(-1.5, 1.5)
            y += rnd.uniform(7, 14)
            pts.append((x * S, y * S))
        pygame.draw.lines(s, (8, 6, 6), False, pts, 2 * S)
    pygame.draw.ellipse(s, (8, 6, 6), ((hx - 13) * S, 12 * S, 26 * S, 11 * S))
    # eye holes with a pinprick of light, and the mouth
    for ex in (-5, 5):
        pygame.draw.ellipse(s, (0, 0, 0), ((hx + ex - 4) * S, 25 * S, 8 * S, 10 * S))
        pygame.draw.circle(s, (255, 255, 255), ((hx + ex) * S, 30 * S), S)
    if not mouth:
        pygame.draw.ellipse(s, (0, 0, 0), ((hx - 4) * S, 38 * S, 8 * S, 12 * S))
    else:
        # the jaw unhinges: a mouth far too big for its head
        jaw = pygame.Rect((hx - 9) * S, 34 * S, 18 * S, 34 * S)
        pygame.draw.ellipse(s, skin, jaw.inflate(6 * S, 6 * S))
        pygame.draw.ellipse(s, (6, 0, 0), jaw)
        pygame.draw.ellipse(s, (70, 8, 10), jaw.inflate(-8 * S, -10 * S))
        for i in range(6):
            x = jaw.left + (i + 0.5) * jaw.width / 6
            pygame.draw.polygon(s, (230, 224, 200), [(x - 2 * S, jaw.top + 4 * S), (x + 2 * S, jaw.top + 4 * S), (x, jaw.top + 10 * S)])
            pygame.draw.polygon(s, (230, 224, 200), [(x - 2 * S, jaw.bottom - 4 * S), (x + 2 * S, jaw.bottom - 4 * S), (x, jaw.bottom - 10 * S)])
    # soft round shading: lit from the left
    shade = pygame.Surface((w, h), pygame.SRCALPHA)
    for x in range(w):
        k = int(255 - 120 * max(0.0, (x - w * 0.35) / (w * 0.65)))
        pygame.draw.line(shade, (k, k, k, 255), (x, 0), (x, h))
    s.blit(shade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return s


def deco_lamp():
    """Fluorescent tube hanging from the ceiling (in the ward)."""
    s = pygame.Surface((90, 40), pygame.SRCALPHA)
    pygame.draw.line(s, (40, 40, 40), (20, 0), (20, 22), 2)
    pygame.draw.line(s, (40, 40, 40), (70, 0), (70, 22), 2)
    pygame.draw.rect(s, (60, 62, 60), (6, 20, 78, 12))
    pygame.draw.rect(s, (220, 255, 235), (10, 30, 70, 6))
    return s


# light sources: colour (0..1), radius in tiles, intensity, height above the floor (0..1)
LIGHTS = {
    "candle": ((1.0, 0.60, 0.26), 2.6, 0.85, 0.12),
    "lantern": ((1.0, 0.66, 0.30), 3.3, 1.0, 0.62),
    "lamp": ((0.70, 0.92, 1.0), 3.6, 0.95, 0.88),
    "door": ((0.55, 0.68, 1.0), 3.6, 1.0, 0.45),
}


def make_hand_sprite_fp():
    """Your hand gripping the flashlight, rendered once with real shading."""
    Wd, Hd = 340, 380
    s = pygame.Surface((Wd, Hd), pygame.SRCALPHA)
    cx = 180

    def body_w(y):           # the flashlight gets wider towards you
        return 44 + (y - 70) / (Hd - 70) * 56

    # --- flashlight body: brushed dark metal, cylinder shading
    for y in range(70, Hd):
        w = body_w(y)
        for x in range(int(cx - w / 2), int(cx + w / 2)):
            n = (x - cx) / (w / 2)
            b = 0.22 + 0.55 * max(0.0, 1 - (n + 0.35) ** 2) + 0.5 * max(0.0, 1 - ((n + 0.45) / 0.12) ** 2)
            if 210 < y < 340 and (y // 6) % 2 == 0:
                b *= 0.75   # knurled grip
            c = int(clamp(62 * b + 8, 0, 255))
            s.set_at((x, y), (c, c, int(c * 1.08), 255))
    # --- head: flared cone + chrome bezel
    for y in range(28, 72):
        k = (y - 28) / 44
        w = 96 - 52 * k
        for x in range(int(cx - w / 2), int(cx + w / 2)):
            n = (x - cx) / (w / 2)
            b = 0.25 + 0.6 * max(0.0, 1 - (n + 0.3) ** 2) + 0.7 * max(0.0, 1 - ((n + 0.5) / 0.1) ** 2)
            c = int(clamp(70 * b + 8, 0, 255))
            s.set_at((x, y), (c, c, int(c * 1.1), 255))
    rim = pygame.Rect(0, 0, 100, 34)
    rim.center = (cx, 30)
    pygame.draw.ellipse(s, (70, 72, 80), rim)
    pygame.draw.ellipse(s, (130, 132, 140), rim, 3)
    pygame.draw.arc(s, (200, 200, 210), rim.inflate(-6, -6), 2.4, 3.6, 2)
    # --- skin
    def shade(c, b):
        return (int(clamp(c[0] * b, 0, 255)), int(clamp(c[1] * b, 0, 255)), int(clamp(c[2] * b, 0, 255)), 255)
    skin = (205, 152, 126)

    def capsule(x0, y0, x1, y1, r, base, light_dir=-1):
        """Rounded finger segment, shaded like a cylinder (lit from above)."""
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            for j in range(r, 0, -1):
                b = 0.45 + 0.55 * (1 - j / r) ** 0.5
                pygame.draw.circle(s, shade(base, b), (int(x), int(y + (r - j) * 0.35 * light_dir * -1)), j)
    # back of the hand + wrist (going off the bottom-left)
    pygame.draw.polygon(s, shade(skin, 0.55), [(0, Hd), (40, 250), (cx - 60, 150), (cx - 40, 330), (110, Hd)])
    for i in range(3):   # tendons
        pygame.draw.line(s, shade(skin, 0.68), (30 + i * 22, Hd), (cx - 70 + i * 10, 170 + i * 30), 3)
    # four fingers wrapped around the flashlight
    for i in range(4):
        y = 156 + i * 38
        capsule(cx - 82, y, cx + 26, y + 6, 18, skin)
        pygame.draw.circle(s, shade(skin, 1.05), (cx - 84, y), 19)            # knuckle
        pygame.draw.circle(s, shade(skin, 0.6), (cx - 84, y), 19, 2)
        pygame.draw.line(s, shade(skin, 0.5), (cx - 30, y - 15), (cx - 26, y + 15), 2)   # joint crease
        nail = pygame.Rect(0, 0, 16, 22)
        nail.center = (cx + 34, y + 6)
        pygame.draw.ellipse(s, shade(skin, 1.15), nail)
        pygame.draw.ellipse(s, shade(skin, 0.7), nail, 1)
        if i < 3:
            pygame.draw.line(s, shade(skin, 0.38), (cx - 70, y + 20), (cx + 30, y + 24), 3)   # gap between fingers
    # thumb over the top of the grip
    capsule(cx + 86, 300, cx + 8, 132, 20, skin)
    tn = pygame.Rect(0, 0, 22, 26)
    tn.center = (cx + 12, 138)
    pygame.draw.ellipse(s, shade(skin, 1.2), tn)
    pygame.draw.ellipse(s, shade(skin, 0.75), tn, 1)
    # coat sleeve
    pygame.draw.polygon(s, (30, 28, 34, 255), [(0, 300), (70, 318), (150, Hd), (0, Hd)])
    for i in range(4):
        pygame.draw.line(s, (18, 16, 22, 255), (8 + i * 26, 306 + i * 5), (30 + i * 30, Hd), 2)
    pygame.draw.line(s, (52, 50, 58, 255), (0, 300), (70, 318), 3)
    return s


def make_mask_glow():
    g = pygame.Surface((128, 128))
    g.fill((0, 0, 0))
    for i in range(48):
        k = i / 47
        b = int(235 * k ** 1.6)
        pygame.draw.circle(g, (b, b, b), (64, 64), int(64 * (1 - k) + 1))
    return g


def make_beam_dust(n=90):
    return [[random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.2, 1.0),
             random.uniform(0, 6.28)] for _ in range(n)]


DECOS["lamp"] = (deco_lamp, 0.12, 0.84, True)


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
        self.bg_cols = None
        self.deco_imgs = {k: v[0]() for k, v in DECOS.items()}
        self.glow = make_glow()
        self.glow_cool = make_glow()
        self.glow_cool.fill((90, 200, 255), special_flags=pygame.BLEND_RGB_MULT)
        self.f_serif = pygame.font.SysFont("georgia,palatinolinotype,palatino,timesnewroman,dejavuserif,serif", 64)
        self.f_serif_big = pygame.font.SysFont("georgia,palatinolinotype,palatino,timesnewroman,dejavuserif,serif", 104)
        self.f_hand = pygame.font.SysFont("inkfree,segoeprint,bradleyhanditc,comicsansms,dejavusansmono", 24)
        self.dust = make_beam_dust()
        self.mask_glow = make_mask_glow()
        self.hand_fp = make_hand_sprite_fp()
        self.mask_frame = self.mask.copy()
        self.ash = []
        self.fade = 1.0
        self.death_frame = None
        self.drips = [(random.uniform(-0.48, 0.48), random.uniform(0.05, 0.16), random.uniform(25, 90), random.random())
                      for _ in range(16)]
        self.paper = self.make_paper()
        self.amb_t = 0.0
        self.build_floors()
        self.ent_frames = [make_entity_sprite(i) for i in range(3)]
        self.ent_mouth = [make_entity_sprite(i, mouth=True) for i in range(3)]
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
        """Every area has its own set of wall textures (2 random copies of each kind)."""
        rnd = random.Random(11)
        self.tex_cols = []          # [texture index][x] -> 1xTEX column surface
        self.tex_base = []          # [texture index] -> full texture
        self.tex_theme = []         # [texture index] -> theme (for its tint)
        self.shade_cache = {}
        self.theme_tex = []         # [theme] -> list of (texture index, weight)
        for th_i, (name, maker, kinds, *_) in enumerate(THEMES):
            lst = []
            for kind, weight in kinds:
                for _ in range(2):
                    tex = maker(kind, rnd, self.f_tex)
                    ao = pygame.Surface((TEX, TEX))
                    for y in range(TEX):
                        k = min(1.0, 0.45 + 0.55 * min(y / 16, (TEX - 1 - y) / 20))
                        c = int(255 * k)
                        pygame.draw.line(ao, (c, c, c), (0, y), (TEX, y))
                    tex.blit(ao, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                    self.tex_cols.append([tex.subsurface((x, 0, 1, TEX)) for x in range(TEX)])
                    self.tex_base.append(tex)
                    self.tex_theme.append(th_i)
                    lst.append((len(self.tex_cols) - 1, weight))
            self.theme_tex.append(lst)

    SHADE_PER_TILE = 2.0

    def shaded_cols(self, kind, q):
        """Wall texture multiplied by a (quantised) light colour - cached."""
        key = (kind, q)
        cols = self.shade_cache.get(key)
        if cols is None:
            if len(self.shade_cache) > 900:
                self.shade_cache.clear()
            tex = self.tex_base[kind].copy()
            tex.fill((min(255, q[0] * 12), min(255, q[1] * 12), min(255, q[2] * 12)), special_flags=pygame.BLEND_RGB_MULT)
            cols = [tex.subsurface((x, 0, 1, TEX)) for x in range(TEX)]
            self.shade_cache[key] = cols
        return cols

    # ---------------------------------------------------------------- lights
    def build_lights(self):
        self.lights = []
        for dx_, dy_, name in self.decos:
            if name in LIGHTS:
                self.lights.append({"x": dx_, "y": dy_, "kind": name, "ph": random.uniform(0, 6.28)})
        self.lights.append({"x": self.exit[0], "y": self.exit[1], "kind": "door", "ph": 0.0})
        self.compute_lightmap()

    def compute_lightmap(self):
        """Which floor tiles each light can actually reach (walls block light)."""
        self.tile_lights = {}
        self.light_vis = []
        for i, L in enumerate(self.lights):
            col, rad, inten, hgt = LIGHTS[L["kind"]]
            lx, ly = L["x"], L["y"]
            arr = np.zeros((MH, MW), dtype=np.float32) if np is not None else None
            R_ = int(rad) + 1
            for ty in range(int(ly) - R_, int(ly) + R_ + 1):
                for tx in range(int(lx) - R_, int(lx) + R_ + 1):
                    if 0 < tx < MW - 1 and 0 < ty < MH - 1 and not self.grid[ty][tx]:
                        cx, cy = tx + 0.5, ty + 0.5
                        if (cx - lx) ** 2 + (cy - ly) ** 2 <= (rad + 0.7) ** 2 and self.los(lx, ly, cx, cy):
                            self.tile_lights.setdefault((tx, ty), []).append(i)
                            if arr is not None:
                                arr[ty, tx] = 1.0
            self.light_vis.append(arr)

    def update_lights(self):
        """This frame's colour/intensity of every light (they flicker)."""
        now = []
        for L in self.lights:
            col, rad, inten, hgt = LIGHTS[L["kind"]]
            if L["kind"] == "door":
                f = 1.0
            elif L["kind"] == "lamp":
                f = 0.12 if random.random() < 0.06 else 0.95 + random.uniform(-0.03, 0.03)
            else:
                f = 0.86 + 0.12 * math.sin(self.t * 13 + L["ph"]) + random.uniform(-0.04, 0.04)
            I = inten * f
            now.append((L["x"], L["y"], col[0] * I, col[1] * I, col[2] * I, rad * rad, I))
        self.light_now = now

    def light_at(self, x, y, tile):
        lr = lg = lb = 0.0
        L = self.tile_lights.get(tile)
        if L:
            ln = self.light_now
            for i in L:
                lx, ly, cr, cg, cb, rad2, I = ln[i]
                d2 = (x - lx) ** 2 + (y - ly) ** 2
                if d2 < rad2:
                    f = (1 - d2 / rad2) / (1 + d2 * 2.2)
                    lr += cr * f
                    lg += cg * f
                    lb += cb * f
        return lr, lg, lb

    def pick_wall(self, x, y, rnd=random):
        idx, wts = zip(*self.theme_tex[self.zone[y][x]])
        self.wallkind[y][x] = rnd.choices(idx, wts)[0]

    def update_bg(self, ceil, floor):
        """Ceiling/floor gradient tinted for the area you are in."""
        key = tuple(int(c) for c in list(ceil) + list(floor))
        if key == self.bg_cols:
            return
        self.bg_cols = key
        strip = pygame.Surface((1, 2 * H))
        for y in range(2 * H):
            if y < H:
                k = (1 - y / H) ** 2
                c = [3 + (ceil[i] - 3) * k for i in range(3)]
            else:
                k = ((y - H) / H) ** 1.5
                c = [3 + (floor[i] - 3) * k for i in range(3)]
            strip.set_at((0, y), [int(v) for v in c])
        self.bg = pygame.transform.scale(strip, (W, 2 * H))

    def build_floors(self):
        self.floor_tex = self.ceil_tex = None
        if np is None:
            return
        rnd = random.Random(21)
        fl = [pygame.surfarray.array3d(m(rnd)) for m in FLOOR_MAKERS]
        ce = [pygame.surfarray.array3d(m(rnd)) for m in CEIL_MAKERS]
        self.floor_tex = np.stack(fl).astype(np.float32)    # [zone, x, y, rgb]
        self.ceil_tex = np.stack(ce).astype(np.float32)
        self.tints_np = np.array([t_[3] for t_ in THEMES], dtype=np.float32) / 255.0
        self.floor_flat = self.floor_tex.reshape(-1, 3)
        self.ceil_flat = self.ceil_tex.reshape(-1, 3)
        self.lr_w, self.lr_h = W // 4, H // 4
        self.lr_cols = ((np.arange(self.lr_w) + 0.5) / self.lr_w * 2 - 1).astype(np.float32)
        self.lr_rows = ((np.arange(self.lr_h) + 0.5) * (H / self.lr_h)).astype(np.float32)

    def refresh_np(self):
        if np is not None:
            self.grid_np = np.array(self.grid, dtype=np.float32)
            self.zone_np = np.array(self.zone, dtype=np.int32)

    def cast_floor(self, hz, ox):
        """Textured floor and ceiling, with soft shadows where they meet the walls."""
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        plx, ply = -sa * FOVK, ca * FOVK
        f32 = np.float32
        rdx = f32(ca) + f32(plx) * self.lr_cols
        rdy = f32(sa) + f32(ply) * self.lr_cols
        dy = self.lr_rows - f32(hz)
        dist = np.minimum(f32(0.5 * H) / np.maximum(np.abs(dy), f32(0.5)), f32(14.0))
        wx = f32(self.px) + dist[:, None] * rdx[None, :]
        wy = f32(self.py) + dist[:, None] * rdy[None, :]
        ix = np.clip(wx.astype(np.int32), 1, MW - 2)
        iy = np.clip(wy.astype(np.int32), 1, MH - 2)
        fx = wx - np.floor(wx)
        fy = wy - np.floor(wy)
        z = self.zone_np[iy, ix]
        tx = (fx * FTEX).astype(np.int32) & (FTEX - 1)
        ty = (fy * FTEX).astype(np.int32) & (FTEX - 1)
        k = int(np.searchsorted(dy, 0))           # rows below k are ceiling, from k on floor
        col = np.empty(wx.shape + (3,), dtype=np.float32)
        flat = (z * FTEX + tx) * FTEX + ty
        np.take(self.ceil_flat, flat[:k], axis=0, out=col[:k])
        np.take(self.floor_flat, flat[k:], axis=0, out=col[k:])
        g = self.grid_np
        e = 0.32
        ao = (g[iy, ix - 1] * np.clip(1 - fx / e, 0, 1) + g[iy, ix + 1] * np.clip(1 - (1 - fx) / e, 0, 1)
              + g[iy - 1, ix] * np.clip(1 - fy / e, 0, 1) + g[iy + 1, ix] * np.clip(1 - (1 - fy) / e, 0, 1))
        np.clip(ao, 0, 1, out=ao)
        ao = 1 - 0.6 * ao * np.sqrt(ao)
        rowk = np.exp(-dist * 0.30) * np.where(np.arange(len(dy)) >= k, 0.85, 0.55)
        fog = rowk[:, None] * ao
        mult = np.take(self.tints_np, z, axis=0)
        mult *= fog[..., None]
        aof = ao * np.where(np.arange(len(dy)) >= k, f32(1.1), f32(0.75))[:, None]
        ti = iy * MW + ix
        nrow, ncol = wx.shape
        for i, (lx, ly, cr, cg, cb, rad2, I) in enumerate(self.light_now):
            rad = math.sqrt(rad2)
            relx, rely = lx - self.px, ly - self.py
            ld = relx * ca + rely * sa                  # depth of the light in front of you
            if ld < -rad or abs(relx) > 11 or abs(rely) > 11:
                continue
            side = -relx * sa + rely * ca
            # only the block of floor/ceiling pixels the light can reach
            near = max(ld - rad, 0.25)
            cx_ = side / (max(ld, 0.25) * FOVK)
            half = rad / (near * FOVK)
            c0 = max(0, int((cx_ - half + 1) / 2 * ncol) - 1)
            c1 = min(ncol, int((cx_ + half + 1) / 2 * ncol) + 2)
            if ld - rad < 0.3:
                c0, c1 = 0, ncol
            if c1 <= c0:
                continue
            inrange = (dist > ld - rad) & (dist < ld + rad)
            vis_flat = self.light_vis[i].ravel()
            colr = np.array((cr, cg, cb), dtype=f32)
            for r0, r1 in ((0, k), (k, nrow)):
                rows = np.nonzero(inrange[r0:r1])[0]
                if len(rows) == 0:
                    continue
                rs = slice(r0 + rows[0], r0 + rows[-1] + 1)
                sl = (rs, slice(c0, c1))
                d2 = (wx[sl] - f32(lx)) ** 2 + (wy[sl] - f32(ly)) ** 2
                f = np.take(vis_flat, ti[sl]) * np.clip(1 - d2 / f32(rad2), 0, 1) / (1 + d2 * f32(2.2)) * aof[sl]
                mult[sl] += f[..., None] * colr
        col *= mult
        arr = np.clip(col, 0, 255).astype(np.uint8)
        surf = pygame.surfarray.make_surface(arr.transpose(1, 0, 2))
        self.screen.blit(pygame.transform.scale(surf, (W, H)), (int(ox), 0))

    # ---------------------------------------------------------------- setup
    def new_game(self):
        self.grid = gen_maze(MW, MH)
        rnd = random.Random()
        start = (1, 1)
        # carve open rooms into the maze
        self.rooms = []
        for _ in range(80):
            if len(self.rooms) >= 9:
                break
            rw, rh = rnd.randint(3, 5), rnd.randint(3, 5)
            rx, ry = rnd.randint(1, MW - rw - 1), rnd.randint(1, MH - rh - 1)
            r = pygame.Rect(rx, ry, rw, rh)
            if r.inflate(4, 4).collidelist(self.rooms) != -1 or rx + ry < 6:
                continue
            self.rooms.append(r)
            for yy in range(ry, ry + rh):
                for xx in range(rx, rx + rw):
                    self.grid[yy][xx] = 0
        # split the maze into areas, each one with its own look
        opens0 = [(x, y) for y in range(MH) for x in range(MW) if not self.grid[y][x]]
        seeds = [rnd.choice(opens0)]
        while len(seeds) < len(THEMES):
            seeds.append(max(opens0, key=lambda p: min((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 for q in seeds)))
        order = list(range(len(THEMES)))
        rnd.shuffle(order)
        self.zone = [[order[min(range(len(seeds)), key=lambda i: (x - seeds[i][0]) ** 2 + (y - seeds[i][1]) ** 2)]
                      for x in range(MW)] for y in range(MH)]
        self.wallkind = [[0] * MW for _ in range(MH)]
        for y in range(MH):
            for x in range(MW):
                self.pick_wall(x, y, rnd)
        self.cur_zone = self.zone[start[1]][start[0]]
        self.seen_zones = {self.cur_zone}
        th_ = THEMES[self.cur_zone]
        self.bg_ceil, self.bg_floor = list(th_[4]), list(th_[5])
        self.zone_title = th_[0]
        self.zone_title_t = 4.0
        self.shift_t = random.uniform(25, 35)
        self.shift_count = 0
        self.crush = [[0.0] * MW for _ in range(MH)]
        self.corient = [[0] * MW for _ in range(MH)]
        self.death_cause = "IT FOUND YOU"
        self.crush_warned = False
        self.compute_segments()
        self.refresh_np()
        # a camera spot for the title screen: the middle of a room
        rr = self.rooms[0] if self.rooms else pygame.Rect(1, 1, 1, 1)
        self.title_cam = (rr.centerx + 0.5, rr.centery + 0.5)
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
        pool = [p for p in opens if dist.get(p, 0) > 6 and p != exit_tile and p not in pages]
        random.shuffle(pool)
        while len(pages) < PAGES_TOTAL:
            pages.append(pool.pop())
        self.pages = [center(p) for p in pages]
        self.batteries = [center(pool.pop()) for _ in range(7)]
        self.exit = center(exit_tile)
        self.exit_tile = exit_tile
        self.exit_map = bfs(self.grid, exit_tile)
        self.start_exit_d = max(1, self.exit_map.get(start, 1))
        self.progress = 0.0
        self.progress_t = 0.0
        self.near_warned = False
        # the monster does not know where you are: it has to find you
        self.ai = "wander"          # wander -> investigate -> hunt -> search -> wander
        self.ai_target = None       # tile it is walking to
        self.ai_last = None         # last place it saw / heard you
        self.ai_t = 0.0             # time in the current state
        self.ai_idle = 0.0          # standing still, listening
        self.ai_lost = 0.0          # time since it last perceived you
        self.hear_t = 0.0
        self.noise = 0.0            # how loud you are right now (in tiles)
        self.noise_event = 0.0      # extra noise from clicks, traps...
        self.wander_far_t = 0.0
        self.sneaking = False
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
        self.msg_text = "Find the way out. Listen for the crickets. Do not let it touch you."
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
            chance = 0.2 if THEMES[self.zone[ty][tx]][0] == "THE HANDS" else 0.012
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if self.grid[ty + ddy][tx + ddx] and rnd.random() < chance:
                    side = rnd.uniform(-0.3, 0.3)
                    self.hands.append({"x": tx + 0.5 + ddx * 0.44 + ddy * side,
                                       "y": ty + 0.5 + ddy * 0.44 + ddx * side,
                                       "lift": rnd.uniform(0.25, 0.7), "var": rnd.randrange(5),
                                       "done": False, "twitch": 0.0})
        self.decos = []
        item_tiles = {(int(x), int(y)) for x, y in self.pages + self.batteries + [self.exit]}
        def add_deco(tx, ty):
            names = THEMES[self.zone[ty][tx]][6]
            name = rnd.choice(names)
            if name == "hand":
                return
            self.decos.append((tx + rnd.uniform(0.25, 0.75), ty + rnd.uniform(0.25, 0.75), name))
        for r in self.rooms:
            tiles = [(x, y) for y in range(r.top, r.bottom) for x in range(r.left, r.right) if (x, y) not in item_tiles]
            for tx, ty in rnd.sample(tiles, min(len(tiles), rnd.randint(2, 4))):
                add_deco(tx, ty)
        for (tx, ty) in opens:
            if (tx, ty) != start and (tx, ty) not in item_tiles and rnd.random() < 0.05:
                add_deco(tx, ty)
        self.build_lights()
        self.bob_phase = 0.0
        self.bob = 0.0
        self.sway = 0.0
        self.turn_vel = 0.0

    # ---------------------------------------------------------------- geometry
    def solid(self, x, y):
        tx, ty = int(x), int(y)
        if tx < 0 or ty < 0 or tx >= MW or ty >= MH:
            return True
        if self.grid[ty][tx] == 1:
            return True
        sq = self.crush[ty][tx]
        if sq:
            f = (y - ty) if self.corient[ty][tx] == 0 else (x - tx)
            return f < sq or f > 1 - sq
        return False

    def free(self, x, y, r=0.22):
        g = self.grid
        for ox, oy in ((-r, -r), (r, -r), (-r, r), (r, r)):
            if g[int(y + oy)][int(x + ox)]:
                return False
        rs = 0.12   # you can squeeze a bit closer to the moving walls
        return not any(self.solid(x + ox, y + oy) for ox, oy in ((-rs, -rs), (rs, -rs), (-rs, rs), (rs, rs)))

    def slab_hit(self, mx, my, px, py, rdx, rdy, t0, t1):
        """Ray inside a corridor whose walls are closing in: hit the moving wall?"""
        sq = self.crush[my][mx]
        if self.corient[my][mx] == 0:       # corridor runs along x, walls move in y
            f = py + t0 * rdy - my
            if f < sq or f > 1 - sq:        # straight into the end of the moving wall
                wy = my - 1 if f < sq else my + 1
                return max(t0, 0.02), 0, f % 1.0, mx, wy
            if rdy:
                Y = my + sq if rdy < 0 else my + 1 - sq
                t = (Y - py) / rdy
                if t0 <= t <= t1:
                    wx = px + t * rdx
                    return max(t, 0.02), 1, wx - math.floor(wx), mx, (my - 1 if rdy < 0 else my + 1)
        else:                               # corridor runs along y, walls move in x
            f = px + t0 * rdx - mx
            if f < sq or f > 1 - sq:
                wx_ = mx - 1 if f < sq else mx + 1
                return max(t0, 0.02), 1, f % 1.0, wx_, my
            if rdx:
                X = mx + sq if rdx < 0 else mx + 1 - sq
                t = (X - px) / rdx
                if t0 <= t <= t1:
                    wy = py + t * rdy
                    return max(t, 0.02), 0, wy - math.floor(wy), (mx - 1 if rdx < 0 else mx + 1), my
        return None

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
        crush = self.crush
        if crush[my][mx]:
            hit = self.slab_hit(mx, my, px, py, rdx, rdy, 0.0, min(sdx, sdy))
            if hit:
                return hit
        while True:
            if sdx < sdy:
                t0 = sdx
                sdx += ddx
                mx += stx
                side = 0
            else:
                t0 = sdy
                sdy += ddy
                my += sty
                side = 1
            if grid[my][mx]:
                break
            if crush[my][mx]:
                hit = self.slab_hit(mx, my, px, py, rdx, rdy, t0, min(sdx, sdy))
                if hit:
                    return hit
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
        self.fade = max(0.0, self.fade - dt * 0.6)
        if self.state == "play":
            self.update_play(dt)
        elif self.state == "caught":
            self.update_caught(dt)
        elif self.state == "crushed":
            if self.t > 1.8:
                self.state, self.t = "dead", 0.0
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
        sneaking = (keys[pygame.K_c] or keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and moving
        running = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and moving and self.stamina > 1 and not sneaking
        self.sneaking = sneaking
        if running:
            self.stamina = max(0.0, self.stamina - 30 * dt)
        else:
            self.stamina = min(100.0, self.stamina + 14 * dt)
        spd = 4.0 if running else 1.25 if sneaking else 2.4
        self.noise = 7.5 if running else 1.0 if sneaking else 3.2 if moving else 0.0
        self.noise_event = max(0.0, self.noise_event - dt * 4)
        if moving:
            ca, sa = math.cos(self.angle), math.sin(self.angle)
            vx = ca * fwd - sa * strafe
            vy = sa * fwd + ca * strafe
            n = math.hypot(vx, vy)
            nx = self.px + vx / n * spd * dt
            if self.free(nx, self.py) or not self.free(self.px, self.py):
                self.px = nx
            ny = self.py + vy / n * spd * dt
            if self.free(self.px, ny) or not self.free(self.px, self.py):
                self.py = ny
            self.bob_phase += dt * (13 if running else 8.5)
            self.bob = math.sin(self.bob_phase) * (9 if running else 5)
            self.step_t -= dt
            if self.step_t <= 0:
                self.step_t = 0.3 if running else 0.7 if sneaking else 0.46
                a.play(a.step, 0.05 if sneaking else 0.22 if running else 0.16)
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

        self.update_ai(dt, dist, pan, torch_ok)

        if self.sanity <= 0:
            self.sanity = 45
            self.blackout = 2.6
            a.play(a.whisper, 1.0)
            a.play(a.sting, 0.7)
            self.say("YOU LOOKED TOO LONG", 2.5)

        if self.ent_wait <= 0 and (dist < 0.5 or (dist < 1.4 and self.ent_visible_line)):
            self.trigger_caught()
            return

        # --- atmosphere
        self.heart_t -= dt
        if self.heart_t <= 0:
            self.heart_t = clamp(dist / 7, 0.32, 1.5) * (0.6 if self.ai == "hunt" else 1.0)
            if a.ok:
                a.ch_heart.play(a.heart)
                a.ch_heart.set_volume(clamp(1.1 - dist / 14, 0.1, 1.0))
        a.loop(a.ch_drone, a.drone, clamp(0.3 + (9 - dist) / 18, 0.3, 0.8) if a.ok else 0)
        a.loop(a.ch_static, a.static, clamp((100 - self.sanity) / 100, 0, 1) * (0.55 if self.seen else 0.25))

        self.event_t -= dt
        if self.event_t <= 0:
            self.event_t = random.uniform(12, 28) - self.progress * 7
            self.random_event()
        for item in self.queue[:]:
            item[0] -= dt
            if item[0] <= 0:
                self.queue.remove(item)
                if len(item) > 3:
                    a.play(a.beep, 0.25, -0.5)
                else:
                    a.play(a.step, item[1], item[2])
        self.sub_t = max(0.0, self.sub_t - dt)
        self.glimpse = max(0.0, self.glimpse - dt)
        self.msg_t = max(0.0, self.msg_t - dt)

        if self.update_crush(dt):
            return

        # --- which area are you in?
        z = self.zone[int(self.py)][int(self.px)]
        if z != self.cur_zone:
            self.cur_zone = z
            if z not in self.seen_zones:
                self.seen_zones.add(z)
                self.zone_title, self.zone_title_t = THEMES[z][0], 4.5
                a.play(a.sting, 0.35)
        th_ = THEMES[self.cur_zone]
        for i in range(3):
            self.bg_ceil[i] += (th_[4][i] - self.bg_ceil[i]) * min(1, dt * 1.5)
            self.bg_floor[i] += (th_[5][i] - self.bg_floor[i]) * min(1, dt * 1.5)
        self.zone_title_t = max(0.0, self.zone_title_t - dt)
        name = THEMES[self.cur_zone][0]
        loops = {"THE NURSERY": (a.musicbox, 0.32), "THE WARD": (a.buzz, 0.16), "THE RED ROOM": (a.clock, 0.4),
                 "THE CELLAR": (a.wind, 0.35), "THE HANDS": (a.wind, 0.18)} if a.ok else {}
        snd, vol = loops.get(name, (None, 0))
        a.ambience(snd, vol)
        self.amb_t -= dt
        if self.amb_t <= 0:
            self.amb_t = random.uniform(0.6, 2.5)
            if name == "THE CRYPT":
                a.play(a.drip, random.uniform(0.15, 0.5), random.uniform(-1, 1))
            elif name == "THE WARD" and random.random() < 0.15:
                for i in range(3):
                    self.queue.append([0.9 * i, 0.0, 0.0, "beep"])
            elif name == "THE CELLAR" and random.random() < 0.2:
                a.play(a.creak, 0.3, random.uniform(-1, 1))

        # --- the maze rearranges itself behind your back
        self.shift_t -= dt
        if self.shift_t <= 0:
            self.shift_t = random.uniform(16, 28)
            if not self.crush_active() and self.shift_walls():
                self.compute_segments()
                self.refresh_np()
                self.exit_map = bfs(self.grid, self.exit_tile)
                self.build_lights()
                self.shift_count += 1
                a.play(a.boom, 0.45, random.uniform(-0.6, 0.6))
                a.play(a.creak, 0.6)
                if self.shift_count == 1:
                    self.say("...something moved. The walls?", 3.5)

        # --- the walls notice you
        for hd in self.hands:
            hd["twitch"] = max(0.0, hd["twitch"] - dt)
            if not hd["done"] and abs(hd["x"] - self.px) < 0.9 and abs(hd["y"] - self.py) < 0.9:
                hd["done"] = True
                hd["twitch"] = 1.2
                a.play(a.creak, 0.25, math.sin(self.rel_angle(hd["x"], hd["y"])))

        # --- how far is the way out? (path distance, not straight line)
        self.progress_t -= dt
        if self.progress_t <= 0:
            self.progress_t = 0.4
            d = self.exit_map.get((int(self.px), int(self.py)))
            if d is not None:
                self.exit_d = d
                self.progress = clamp(1 - d / self.start_exit_d, 0, 1)
        d = getattr(self, "exit_d", self.start_exit_d)
        if a.ok:
            v = clamp(1 - d / 24, 0, 1) ** 1.5 * 0.75 + 0.03
            pan = math.sin(self.rel_angle(*self.exit))
            if not a.ch_out.get_busy():
                a.ch_out.play(a.crickets, loops=-1)
            a.ch_out.set_volume(v * min(1, 1 - pan), v * min(1, 1 + pan))
        if self.progress > 0.75 and not self.near_warned:
            self.near_warned = True
            self.say("You can hear the outside.  It can hear you too.", 4)
            a.play(a.sting, 0.6)
            if self.ent_wait <= 0 and self.ai != "hunt":
                self.ai_alert((int(self.px) + random.randint(-2, 2), int(self.py) + random.randint(-2, 2)), "investigate")

        # --- pickups
        for b in self.batteries[:]:
            if math.hypot(b[0] - self.px, b[1] - self.py) < 0.5:
                self.batteries.remove(b)
                self.battery = min(100.0, self.battery + 45)
                a.play(a.click, 0.6)
                self.say("+ battery", 1.5)
                self.noise_event = max(self.noise_event, 2.5)
        if math.hypot(self.exit[0] - self.px, self.exit[1] - self.py) < 0.6:
            a.stop_loops()
            self.state, self.t = "win", 0.0
            self.release_mouse()

    # ---------------------------------------------------------------- monster brain
    def ent_tile(self):
        return (int(self.ex), int(self.ey))

    def nearest_open(self, t):
        x, y = clamp(t[0], 1, MW - 2), clamp(t[1], 1, MH - 2)
        if not self.grid[y][x]:
            return (x, y)
        for r in range(1, 4):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    xx, yy = clamp(x + dx, 1, MW - 2), clamp(y + dy, 1, MH - 2)
                    if not self.grid[yy][xx]:
                        return (xx, yy)
        return self.ent_tile()

    def ai_alert(self, tile, state):
        """It heard or saw something at `tile`."""
        a = self.audio
        tile = self.nearest_open(tile)
        if state == "hunt" and self.ai != "hunt":
            a.play(a.sting, 0.7)
            a.play(a.whisper, 0.9, math.sin(self.rel_angle(self.ex, self.ey)))
            self.say("IT KNOWS WHERE YOU ARE", 2.5)
        elif state == "investigate" and self.ai in ("wander", "search"):
            a.play(a.creak, 0.35, math.sin(self.rel_angle(self.ex, self.ey)))
        if self.ai == "hunt" and state == "investigate":
            state = "hunt"   # it is already chasing; a noise just updates where it goes
        self.ai = state
        self.ai_last = tile
        self.ai_target = tile
        self.ai_t = 0.0
        self.ai_idle = 0.0
        self.ai_lost = 0.0
        self.path = []

    def pick_wander_target(self):
        et = self.ent_tile()
        dmap = bfs(self.grid, et)
        if random.random() < 0.2:
            # a vague feeling of where you might be: somewhere in your part of the maze
            px, py = int(self.px), int(self.py)
            cands = [t for t in dmap if 4 < abs(t[0] - px) + abs(t[1] - py) < 13]
        else:
            cands = [t for t, d in dmap.items() if 5 <= d <= 15]
        return random.choice(cands) if cands else et

    def update_ai(self, dt, dist, pan, torch_ok):
        a = self.audio
        if self.ent_wait > 0:
            self.ent_wait -= dt
            return
        ptile = (int(self.px), int(self.py))
        self.ai_t += dt

        # --- does it see you? (your flashlight makes you easy to spot)
        sight = 8.0 if self.light_on else 2.2
        if self.sneaking:
            sight *= 0.7
        sees = dist < sight and self.ent_visible_line
        if self.seen:          # you are shining your light right at it - now it knows
            sees = True
        if sees:
            if self.ai != "hunt":
                self.ai_alert(ptile, "hunt")
            self.ai_last = ptile
            self.ai_lost = 0.0

        # --- does it hear you? (path distance through the maze, not through walls)
        self.hear_t -= dt
        loud = max(self.noise, self.noise_event)
        if self.hear_t <= 0 and loud > 0 and not sees:
            self.hear_t = 0.3
            d = bfs(self.grid, self.ent_tile()).get(ptile)
            if d is not None and d <= loud:
                if self.ai == "hunt" or loud >= 7 and d <= 3:
                    self.ai_alert(ptile, "hunt")
                else:
                    off = 0 if d < 3 else 1   # far away it only knows roughly where
                    self.ai_alert((ptile[0] + random.randint(-off, off), ptile[1] + random.randint(-off, off)), "investigate")

        # --- frozen in your light
        if self.seen:
            self.sanity -= 23 * dt
            return
        self.sanity = min(100.0, self.sanity + 6 * dt)

        # --- state machine
        st = self.ai
        if st == "hunt":
            self.ai_lost += dt
            if not sees:
                self.ai_target = self.ai_last
            else:
                self.ai_target = ptile
            if self.ai_lost > 4.0 and self.ent_tile() == self.ai_target:
                self.ai, self.ai_t = "search", 0.0
                a.play(a.whisper, 0.5, pan)
                self.say("It lost you...", 2)
                self.ai_target = None
        elif st == "investigate":
            if self.ent_tile() == self.ai_target:
                self.ai_idle += dt          # stands there, listening
                if self.ai_idle > 2.5:
                    self.ai, self.ai_t = "search", 0.0
                    self.ai_target = None
        elif st == "search":
            # sniffs around the last place it knew about
            if self.ai_target is None or self.ent_tile() == self.ai_target:
                base = self.ai_last or self.ent_tile()
                dmap = bfs(self.grid, base)
                near = [t for t, d in dmap.items() if d <= 4]
                self.ai_target = random.choice(near) if near else base
                self.path = []
            if self.ai_t > 9:
                self.ai, self.ai_t, self.ai_target = "wander", 0.0, None
        if self.ai == "wander":
            if self.ai_target is None or self.ent_tile() == self.ai_target:
                self.ai_idle += dt
                if self.ai_target is None or self.ai_idle > random.uniform(1.0, 3.0):
                    self.ai_idle = 0.0
                    self.ai_target = self.pick_wander_target()
                    self.path = []
            # wandered far away for a long time: it drifts somewhere closer (unseen)
            if dist > 15:
                self.wander_far_t += dt
                if self.wander_far_t > 40:
                    self.wander_far_t = 0
                    self.teleport_entity()
            else:
                self.wander_far_t = 0

        # --- move
        base = 1.45 + 1.5 * self.progress
        speed = {"hunt": base * (1.0 if torch_ok else 1.4), "investigate": base * 0.85,
                 "search": base * 0.6, "wander": base * 0.55}[self.ai]
        if self.ai == "wander" and self.ai_target and self.ent_tile() == self.ai_target:
            speed = 0
        if speed > 0 and self.ai_target is not None:
            self.move_entity(speed * dt, self.ai_target, chase=(self.ai == "hunt" and sees))
            if dist < 10:
                self.ent_step_t -= dt
                if self.ent_step_t <= 0:
                    self.ent_step_t = 0.4 if self.ai == "hunt" else 0.7
                    a.play(a.step, clamp(1 - dist / 10, 0, 1) * (0.9 if self.ai == "hunt" else 0.5), pan)
        if dist < 7 and random.random() < 0.12 * dt:
            a.play(a.whisper, 0.6, pan)

    def move_entity(self, step, target, chase=False):
        self.path_t -= step
        etile = self.ent_tile()
        if self.path_t <= 0 or not self.path or self.path[-1] != target:
            self.path = bfs_path(self.grid, etile, target)[1:]
            self.path_t = 0.3
        while step > 0:
            if self.path:
                tx, ty = center(self.path[0])
            elif chase:
                tx, ty = self.px, self.py
            else:
                tx, ty = center(target)
            ddx, ddy = tx - self.ex, ty - self.ey
            d = math.hypot(ddx, ddy)
            if d <= step:
                self.ex, self.ey = tx, ty
                step -= d
                if self.path:
                    self.path.pop(0)
                else:
                    break
            elif d > 0:
                self.ex += ddx / d * step
                self.ey += ddy / d * step
                step = 0

    def out_of_sight(self, tx, ty):
        cx, cy = center((tx, ty))
        if math.hypot(cx - self.px, cy - self.py) < 1.6:
            return False
        if abs(self.rel_angle(cx, cy)) < 1.0:      # inside your field of view
            return False
        return not self.los(self.px, self.py, cx, cy)

    # ---------------------------------------------------------------- crushing corridors
    def compute_segments(self):
        """Straight corridors (3+ tiles, walls on both sides) - every one of them is a trap."""
        g = self.grid
        room_tiles = {(x, y) for r in self.rooms for y in range(r.top, r.bottom) for x in range(r.left, r.right)}
        self.seg_of = [[-1] * MW for _ in range(MH)]
        self.segments = []

        def horiz(x, y):
            return not g[y][x] and g[y - 1][x] and g[y + 1][x] and (x, y) not in room_tiles

        def vert(x, y):
            return not g[y][x] and g[y][x - 1] and g[y][x + 1] and (x, y) not in room_tiles

        for orient, test in ((0, horiz), (1, vert)):
            seen = set()
            for y in range(1, MH - 1):
                for x in range(1, MW - 1):
                    if (x, y) in seen or not test(x, y):
                        continue
                    run = []
                    cx, cy = x, y
                    while 0 < cx < MW - 1 and 0 < cy < MH - 1 and test(cx, cy):
                        run.append((cx, cy))
                        seen.add((cx, cy))
                        if orient == 0:
                            cx += 1
                        else:
                            cy += 1
                    if len(run) >= 3:
                        idx = len(self.segments)
                        self.segments.append({"tiles": run, "orient": orient, "state": "idle",
                                              "sq": 0.0, "t": 0.0, "cool": 0.0, "snd": 0.0})
                        for tx, ty in run:
                            self.seg_of[ty][tx] = idx

    def crush_active(self):
        return any(sg["state"] != "idle" for sg in self.segments)

    def update_crush(self, dt):
        a = self.audio
        ptile = (int(self.px), int(self.py))
        here = self.seg_of[ptile[1]][ptile[0]]
        busy = any(sg["state"] in ("warn", "closing") for sg in self.segments)
        if here >= 0 and not busy and self.alive_t > 6:
            sg = self.segments[here]
            if sg["state"] == "idle" and sg["cool"] <= 0:
                sg["state"], sg["t"] = "warn", 0.9
                self.noise_event = max(self.noise_event, 9.0)    # the grinding stone is LOUD
                a.play(a.grind, 0.7)
                a.play(a.boom, 0.35)
                if not self.crush_warned:
                    self.crush_warned = True
                    self.say("THE WALLS ARE MOVING.  GET OUT OF THE CORRIDOR!", 4)
        self.rumble = 0.0
        for i, sg in enumerate(self.segments):
            st = sg["state"]
            if st == "idle":
                sg["cool"] = max(0.0, sg["cool"] - dt)
                continue
            sg["t"] -= dt
            if st == "warn":
                if sg["t"] <= 0:
                    sg["state"] = "closing"
                    sg["dur"] = 3.4 + 0.42 * len(sg["tiles"])
            elif st == "closing":
                sg["sq"] = min(0.5, sg["sq"] + 0.5 / sg["dur"] * dt)
                if sg["sq"] >= 0.5:
                    sg["state"], sg["t"] = "closed", 4.0
                    a.play(a.boom, 0.6)
            elif st == "closed":
                if sg["t"] <= 0:
                    sg["state"] = "opening"
            elif st == "opening":
                sg["sq"] = max(0.0, sg["sq"] - 0.5 / 3.0 * dt)
                if sg["sq"] <= 0:
                    sg["state"], sg["cool"] = "idle", 35.0
            if st in ("warn", "closing", "opening"):
                d = min(abs(tx + 0.5 - self.px) + abs(ty + 0.5 - self.py) for tx, ty in sg["tiles"])
                near = clamp(1 - d / 7, 0, 1)
                self.rumble = max(self.rumble, near * (1.0 if st != "opening" else 0.4))
                sg["snd"] -= dt
                if sg["snd"] <= 0 and near > 0:
                    sg["snd"] = 0.55
                    a.play(a.grind, 0.25 + 0.6 * near)
            for tx, ty in sg["tiles"]:
                self.crush[ty][tx] = sg["sq"]
                self.corient[ty][tx] = sg["orient"]
        # are you caught between them?
        sq = self.crush[ptile[1]][ptile[0]]
        if sq:
            tx, ty = ptile
            o = self.corient[ty][tx]
            lo, hi = sq + 0.13, 1 - sq - 0.13
            if lo > hi:
                self.trigger_crush()
                return True
            if o == 0:
                self.py = clamp(self.py, ty + lo, ty + hi)
            else:
                self.px = clamp(self.px, tx + lo, tx + hi)
        return False

    def trigger_crush(self):
        self.audio.stop_loops()
        self.audio.play(self.audio.crunch, 1.0)
        self.audio.play(self.audio.boom, 1.0)
        self.death_cause = "CRUSHED"
        self.crush_frame = self.screen.copy()
        self.death_frame = self.crush_frame
        self.state, self.t = "crushed", 0.0
        self.release_mouse()

    def shift_walls(self):
        """Close a passage behind you and open a new one elsewhere - only where you can't see."""
        g = self.grid
        ptile = (int(self.px), int(self.py))
        etile = (int(self.ex), int(self.ey))
        keep = {ptile, etile} | {(int(x), int(y)) for x, y in self.pages + self.batteries + [self.exit]}
        pd = bfs(g, ptile)
        close_c = [t_ for t_, d in pd.items() if 2 <= d <= 6 and t_ not in keep and self.out_of_sight(*t_)]
        open_c = []
        for y in range(2, MH - 2):
            for x in range(2, MW - 2):
                if g[y][x] and ((not g[y][x - 1] and not g[y][x + 1] and g[y - 1][x] and g[y + 1][x]) or
                                (not g[y - 1][x] and not g[y + 1][x] and g[y][x - 1] and g[y][x + 1])):
                    if 3 <= abs(x - ptile[0]) + abs(y - ptile[1]) <= 12 and self.out_of_sight(x, y):
                        open_c.append((x, y))
        random.shuffle(close_c)
        random.shuffle(open_c)
        must_reach = keep
        for oc in open_c[:4]:
            g[oc[1]][oc[0]] = 0
            for cc in close_c[:15]:
                g[cc[1]][cc[0]] = 1
                reach = bfs(g, ptile)
                if all(t_ in reach for t_ in must_reach) and len(reach) >= len(pd):
                    self.pick_wall(cc[0], cc[1])
                    self.path = []
                    # hands that were on the wall that vanished go with it
                    self.hands = [h for h in self.hands
                                  if not (abs(h["x"] - oc[0] - 0.5) < 0.9 and abs(h["y"] - oc[1] - 0.5) < 0.9)
                                  and not (int(h["x"]), int(h["y"])) == cc]
                    self.decos = [d for d in self.decos if (int(d[0]), int(d[1])) != cc]
                    return True
                g[cc[1]][cc[0]] = 0
            g[oc[1]][oc[0]] = 1
        return False

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
                self.ai_target = None
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

    def trigger_caught(self):
        """It is close enough. Your body stops obeying you."""
        a = self.audio
        a.stop_loops()
        a.play(a.sting, 1.0)
        a.play(a.whisper, 1.0, math.sin(self.rel_angle(self.ex, self.ey)))
        self.state, self.t = "caught", 0.0
        self.caught_from = self.angle
        self.caught_heart = 0.0
        self.caught_flags = set()
        self.death_cause = "IT ATE YOU"
        self.msg_t = 0
        self.zone_title_t = 0

    def update_caught(self, dt):
        a = self.audio
        t = self.t
        # your head turns towards it - slowly, against your will
        target = math.atan2(self.ey - self.py, self.ex - self.px)
        diff = (target - self.caught_from + math.pi) % (2 * math.pi) - math.pi
        k = clamp(t / 1.0, 0, 1)
        ease = 1 - (1 - k) ** 3
        self.angle = self.caught_from + diff * ease + random.uniform(-0.012, 0.012) * (1 - ease * 0.5)
        # ...and up, to look into its face
        d = max(math.hypot(self.ex - self.px, self.ey - self.py), 0.25)
        up = clamp((t - 0.5) / 0.9, 0, 1)
        up = up * up * (3 - 2 * up)
        self.bob = up * 0.45 * H / d + random.uniform(-3, 3) * (1 + 3 * up)
        self.sway = random.uniform(-6, 6)
        # the light stutters
        self.light_on = random.random() > (0.12 if t < 1.15 else 0.3)
        # a pounding heart
        self.caught_heart -= dt
        if self.caught_heart <= 0:
            self.caught_heart = 0.28
            a.play(a.heart, 1.0)
        # it lunges
        if 1.15 < t < 1.7:
            d = math.hypot(self.ex - self.px, self.ey - self.py)
            if d > 0.32:
                step = min(d - 0.32, dt * 4.5)
                self.ex -= (self.ex - self.px) / d * step
                self.ey -= (self.ey - self.py) / d * step
            if "lunge" not in self.caught_flags:
                self.caught_flags.add("lunge")
                a.play(a.breath, 1.0)
        if t > 1.7 and "scream" not in self.caught_flags:
            self.caught_flags.add("scream")
            a.play(a.scream, 1.0)
        if t > 2.45 and "chomp" not in self.caught_flags:
            self.caught_flags.add("chomp")
            a.play(a.crunch, 1.0)
            a.play(a.boom, 0.8)
        if t > 3.3:
            self.state, self.t = "dead", 0.0
            self.release_mouse()

    def draw_caught_overlay(self):
        scr = self.screen
        t = self.t
        if t < 1.7:
            # tunnel vision closing in while you turn
            k = clamp(t / 1.7, 0, 1)
            edge = pygame.Surface((W, H), pygame.SRCALPHA)
            for i in range(10):
                pygame.draw.rect(edge, (0, 0, 0, int(25 + 20 * k)), (i * 14 * k, i * 10 * k, W - i * 28 * k, H - i * 20 * k), int(16 * k) + 1)
            scr.blit(edge, (0, 0))
            red = pygame.Surface((W, H), pygame.SRCALPHA)
            red.fill((110, 0, 0, int(60 * k * (0.6 + 0.4 * math.sin(t * 20)))))
            scr.blit(red, (0, 0))
            return
        # its face fills everything
        scr.fill((60, 0, 0) if int(t * 22) % 2 else (0, 0, 0))
        s_ = 1.0 + min(1.0, (t - 1.7) * 2.2) * 0.9
        draw_face(scr, W // 2 + random.uniform(-25, 25), H // 2 - 40 * s_ + random.uniform(-25, 25), s_, jit=10)
        if t > 2.3:
            # the jaws close
            k = clamp((t - 2.3) / 0.18, 0, 1) ** 2
            gap = int((H // 2) * (1 - k))
            top_y = H // 2 - gap
            bot_y = H // 2 + gap
            pygame.draw.rect(scr, (22, 4, 4), (0, 0, W, top_y))
            pygame.draw.rect(scr, (22, 4, 4), (0, bot_y, W, H - bot_y))
            pygame.draw.rect(scr, (95, 18, 22), (0, top_y - 14, W, 14))
            pygame.draw.rect(scr, (95, 18, 22), (0, bot_y, W, 14))
            n = 14
            for i in range(n):
                x0 = i * W / n
                x1 = (i + 1) * W / n
                xm = (x0 + x1) / 2
                L = 70 + 25 * math.sin(i * 1.7)
                pygame.draw.polygon(scr, (232, 226, 200), [(x0 + 4, top_y), (x1 - 4, top_y), (xm, top_y + L)])
                pygame.draw.polygon(scr, (232, 226, 200), [(x0 + 4 + W / n / 2, bot_y), (x1 - 4 + W / n / 2, bot_y), (xm + W / n / 2, bot_y - L)])
            if t > 2.45:
                scr.fill((0, 0, 0))
                if t < 2.6:
                    scr.fill((150, 0, 0))
        scr.blit(self.grain[int(t * 30) % 4], (0, 0))

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
                self.noise_event = max(self.noise_event, 1.8)
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
        self.death_frame = None
        self.death_bg = None
        self.fade = 1.0
        self.ash = []
        self.grab_mouse()

    # ---------------------------------------------------------------- drawing
    def draw(self):
        s = self.state
        if s == "title":
            self.draw_title()
        elif s == "caught":
            self.draw_world()
            if self.t < 1.65:
                self.death_frame = self.screen.copy()
            self.draw_caught_overlay()
        elif s in ("play", "pause", "note"):
            self.draw_world()
            if s == "pause":
                self.overlay_text(["PAUSED", "", "ESC - resume     Q - quit"])
            elif s == "note":
                self.draw_note()
        elif s == "jumpscare":
            self.draw_jumpscare()
        elif s == "crushed":
            self.draw_crushed()
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

    def draw_sprite(self, scr, sx, sy, img, hscale, hz, lift=0.0, min_depth=0.25, max_depth=99.0, glow=False):
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
        # only scale the part of the sprite that is actually on screen
        vx0, vx1 = max(0.0, left), min(float(W), left + wid)
        vy0, vy1 = max(0.0, top), min(float(H), top + hgt)
        if vx1 <= vx0 or vy1 <= vy0:
            return None
        iw, ih = img.get_size()
        sx0 = int((vx0 - left) / wid * iw)
        sx1 = min(iw, int(math.ceil((vx1 - left) / wid * iw)))
        sy0 = int((vy0 - top) / hgt * ih)
        sy1 = min(ih, int(math.ceil((vy1 - top) / hgt * ih)))
        if sx1 <= sx0 or sy1 <= sy0:
            return None
        # screen position of that cropped part
        cl = left + sx0 / iw * wid
        ct = top + sy0 / ih * hgt
        cw = (sx1 - sx0) / iw * wid
        ch = (sy1 - sy0) / ih * hgt
        scaled = pygame.transform.scale(img.subsurface((sx0, sy0, sx1 - sx0, sy1 - sy0)), (int(cw) + 1, int(ch) + 1))
        if not glow:
            k = math.exp(-depth * 0.30)
            tx_, ty_ = int(sx) % MW, int(sy) % MH
            tint = THEMES[self.zone[ty_][tx_]][3]
            lr, lg, lb = self.light_at(sx, sy, (tx_, ty_))
            scaled.fill((min(255, int(tint[0] * k + 270 * lr)), min(255, int(tint[1] * k + 270 * lg)),
                         min(255, int(tint[2] * k + 270 * lb))), special_flags=pygame.BLEND_RGB_MULT)
        c0 = max(0, int(cl // CW))
        c1 = min(NCOL - 1, int((cl + cw) // CW))
        zb = self.zbuf
        run0 = None
        # blit in runs of visible columns (much fewer blits than one per column)
        for col in range(c0, c1 + 2):
            vis = col <= c1 and depth < zb[col]
            if vis and run0 is None:
                run0 = col
            elif not vis and run0 is not None:
                x0 = run0 * CW
                x1 = col * CW
                scr.blit(scaled, (x0, int(ct)), pygame.Rect(int(x0 - cl), 0, x1 - x0, int(ch) + 1))
                run0 = None
        return scx, top, hgt, depth

    def draw_world(self, view_only=False):
        scr = self.screen
        playing = self.state == "play" and not view_only
        shake = 0.0
        if playing:
            shake = clamp((5.5 - self.ent_dist) / 5.5, 0, 1) * 7 + (100 - self.sanity) / 100 * 5 + getattr(self, 'rumble', 0) * 6
        ox, oy = random.uniform(-shake, shake), random.uniform(-shake, shake)
        hz = int(H / 2 + self.bob + oy)

        self.update_lights()
        if self.floor_tex is not None:
            self.cast_floor(hz, ox)
        else:
            self.update_bg(self.bg_ceil, self.bg_floor)
            scr.blit(self.bg, (0, hz - H))

        # walls
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        plx, ply = -sa * FOVK, ca * FOVK
        px, py = self.px, self.py
        zb = self.zbuf
        texcols = self.tex_cols
        wallkind = self.wallkind
        zone = self.zone
        tints = [t_[3] for t_ in THEMES]
        scale = pygame.transform.scale
        blit = scr.blit
        cache = self.shade_cache
        light_at = self.light_at
        exp = math.exp
        for c in range(NCOL):
            camx = 2 * (c + 0.5) / NCOL - 1
            rdx, rdy = ca + plx * camx, sa + ply * camx
            perp, side, wx, mx, my = self.dda(px, py, rdx, rdy)
            zb[c] = perp
            texx = int(wx * TEX)
            if (side == 0 and rdx < 0) or (side == 1 and rdy > 0):
                texx = TEX - 1 - texx
            if perp > 9.5:
                continue
            kind = wallkind[my][mx]
            # tile in front of this wall face: the light that reaches it
            if side == 0:
                prev = (mx - 1 if rdx > 0 else mx + 1, my)
            else:
                prev = (mx, my - 1 if rdy > 0 else my + 1)
            k = exp(-0.30 * perp) * (1.0 if side == 0 else 0.74)
            t_ = tints[zone[my][mx]]
            lr, lg, lb = light_at(px + rdx * perp, py + rdy * perp, prev)
            q = (min(21, int((t_[0] * k + 270 * lr) / 12)), min(21, int((t_[1] * k + 270 * lg) / 12)),
                 min(21, int((t_[2] * k + 270 * lb) / 12)))
            cols = cache.get((kind, q))
            if cols is None:
                cols = self.shaded_cols(kind, q)
            column = cols[texx]
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
        glowing = []
        for dx_, dy_, name in self.decos:
            if abs(dx_ - px) < 9 and abs(dy_ - py) < 9:
                mk, hs, lift, glows = DECOS[name]
                sprites.append((dx_, dy_, self.deco_imgs[name], hs, lift))
                if glows:
                    glowing.append((dx_, dy_, name))
        sprites.append((self.exit[0], self.exit[1],
                        self.door_open, 0.95, 0.0))
        frames = self.ent_mouth if (self.state == "caught" and self.t > 1.15) else self.ent_frames
        ent_img = frames[int(self.t * (20 if self.state == 'caught' else 9)) % 3]
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
        mx_off = int(-self.sway * 2 + math.sin(self.bob_phase * 0.5) * 8 + ox)
        my_off = int(abs(self.bob) * 0.8 + oy)
        mf = self.mask_frame
        if self.light_on:
            mf.blit(self.mask, (0, 0))
            if self.battery < 25:
                k = int(255 * (0.5 + self.battery / 50))
                mf.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)
        else:
            mf.fill((16, 16, 20))
        # every light you can see opens up its own pool of light in the darkness
        for (lx, ly, cr, cg, cb, rad2, I), L in zip(self.light_now, self.lights):
            if abs(lx - px) > 11 or abs(ly - py) > 11:
                continue
            pr = self.project(lx, ly)
            if not pr:
                continue
            scx, depth = pr
            depth = max(depth, 0.3)
            col_ = int(scx // CW)
            if not (-60 < scx < W + 60):
                continue
            if 0 <= col_ < NCOL and depth > self.zbuf[col_] + 0.8 and not self.los(px, py, lx, ly):
                continue
            hgt = LIGHTS[L["kind"]][3]
            size = int(H / depth * math.sqrt(rad2) * 0.95)
            if size < 6:
                continue
            g = self.glow_img(self.mask_glow, size, int(clamp(I, 0, 1) * 4.99))
            sy_ = hz + H / (2 * depth) - H / depth * hgt
            mf.blit(g, g.get_rect(center=(int(scx) + MASK_PAD - mx_off, int(sy_) + MASK_PAD - my_off)),
                    special_flags=pygame.BLEND_RGB_ADD)
        scr.blit(mf, (-MASK_PAD + mx_off, -MASK_PAD + my_off), special_flags=pygame.BLEND_RGB_MULT)

        # candles and lanterns give their own light
        for dx_, dy_, name in glowing:
            mk, hs, lift, glows = DECOS[name]
            r = self.draw_sprite(scr, dx_, dy_, self.deco_imgs[name], hs, hz, lift, glow=True)
            if r:
                scx, top, hgt, depth = r
                col = int(scx // CW)
                if 0 <= col < NCOL and depth < self.zbuf[col] + 0.3:
                    flick = 0.85 + 0.15 * math.sin(self.t * 13 + dx_ * 7) + random.uniform(-0.05, 0.05)
                    if name == "lamp" and random.random() < 0.08:
                        continue   # dying fluorescent tube
                    size = int(H / depth * 1.3 * flick)
                    if 4 < size < 2200:
                        g = self.glow_img(self.glow_cool if name == "lamp" else self.glow, size)
                        scr.blit(g, g.get_rect(center=(int(scx), int(top + hgt * 0.2))), special_flags=pygame.BLEND_RGB_ADD)

        # moonlight through the open door - a beacon in the dark
        r = self.draw_sprite(scr, self.exit[0], self.exit[1], self.door_open, 0.95, hz, 0.0, glow=True)
        if r:
            scx, top, hgt, depth = r
            col = int(scx // CW)
            if 0 <= col < NCOL and depth < self.zbuf[col] + 0.3:
                size = int(H / depth * 2.2)
                if 4 < size < 2600:
                    g = self.glow_img(self.glow_cool, size)
                    scr.blit(g, g.get_rect(center=(int(scx), int(top + hgt * 0.5))), special_flags=pygame.BLEND_RGB_ADD)

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

        if not view_only:
            self.draw_hand_and_beam(scr, ox, oy)

        # red pulse when it is near
        if self.ent_dist < 5.5 and playing:
            red = pygame.Surface((W, H), pygame.SRCALPHA)
            a_ = int(clamp((5.5 - self.ent_dist) / 5.5, 0, 1) * (40 + 30 * math.sin(self.t * 9)))
            red.fill((120, 0, 0, max(0, a_)))
            scr.blit(red, (0, 0))

        # trapped in a closing corridor: pulsing red edges
        sg_i = self.seg_of[int(self.py)][int(self.px)]
        if playing and sg_i >= 0 and self.segments[sg_i]["state"] in ("warn", "closing"):
            edge = pygame.Surface((W, H), pygame.SRCALPHA)
            a_ = int(90 + 70 * math.sin(self.t * 14))
            for i in range(6):
                pygame.draw.rect(edge, (170, 0, 0, max(0, a_ - i * 14)), (i * 10, i * 10, W - i * 20, H - i * 20), 10)
            scr.blit(edge, (0, 0))
            if int(self.t * 4) % 2 == 0:
                self.blit_center(self.f_big, "GET OUT", (190, 20, 15), H // 2 + 150, scr)

        scr.blit(self.vignette, (0, 0))
        scr.blit(self.grain[int(self.t * 24) % 4], (0, 0))
        if self.sanity < 60:
            g2 = self.grain[(int(self.t * 30) + 2) % 4]
            for _ in range(int((60 - self.sanity) / 15)):
                scr.blit(g2, (random.randint(-20, 20), random.randint(-20, 20)))
        if self.sub_t > 0 and playing:
            scr.fill((0, 0, 0))
            self.blit_center(self.f_huge, self.sub_text, (170, 0, 0), H // 2, scr)
        self.draw_ash(scr, hz)
        fear = 0.0
        if self.state in ("play", "caught"):
            fear = max(clamp((4.5 - self.ent_dist) / 4.5, 0, 1), clamp((45 - self.sanity) / 45, 0, 1))
            if self.state == "caught":
                fear = 1.0
        if fear > 0.12:
            self.chromatic(scr, int(2 + 9 * fear))
        if self.fade > 0:
            f = pygame.Surface((W, H))
            f.fill((0, 0, 0))
            f.set_alpha(int(255 * clamp(self.fade, 0, 1)))
            scr.blit(f, (0, 0))
        if not view_only and self.state != "caught":
            self.draw_hud()

    def draw_hand_and_beam(self, scr, ox, oy):
        sway_x = -self.sway * 0.6 + math.sin(self.bob_phase * 0.5) * 6
        hx = int(W * 0.72 + sway_x)
        hy = int(H + 10 + abs(self.bob) * 1.5)
        lens_c = (hx + 10, hy - 262)
        spot = (W // 2 + int(-self.sway * 2 + math.sin(self.bob_phase * 0.5) * 8 + ox), H // 2 + 30 + int(abs(self.bob) * 0.8 + oy))
        # visible beam + dust floating in it
        if self.light_on:
            beam = self.beam_surf if hasattr(self, "beam_surf") else pygame.Surface((W, H))
            self.beam_surf = beam
            beam.fill((0, 0, 0))
            for i, (wd, c) in enumerate(((150, 10), (95, 14), (50, 20))):
                pygame.draw.polygon(beam, (c, int(c * 0.92), int(c * 0.75)),
                                    [(lens_c[0] - 18 + i * 5, lens_c[1]), (lens_c[0] + 18 - i * 5, lens_c[1]),
                                     (spot[0] + wd, spot[1] - wd // 3), (spot[0] - wd, spot[1] - wd // 3)])
            k = 1.0 if self.battery > 25 else 0.5
            if k < 1:
                beam.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
            scr.blit(beam, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            for d in self.dust:
                d[3] += 0.01
                d[0] += math.sin(d[3] * 1.3) * 0.0015 - self.sway * 0.0004
                d[1] += math.cos(d[3]) * 0.0012 + 0.0004
                if abs(d[0]) > 1 or abs(d[1]) > 1:
                    d[0], d[1] = random.uniform(-1, 1), random.uniform(-1, 1)
                u = d[2]
                bx = lens_c[0] + (spot[0] - lens_c[0]) * u + d[0] * 160 * u
                by = lens_c[1] + (spot[1] - lens_c[1]) * u + d[1] * 110 * u
                b = int((120 + 120 * u) * (0.6 + 0.4 * math.sin(d[3] * 3)) * k)
                pygame.draw.circle(scr, (b, int(b * 0.95), int(b * 0.8)), (int(bx), int(by)), 1 if u < 0.6 else 2)
        # your hand and the flashlight, lit by the spill of the beam and any lights nearby
        lr, lg, lb = self.light_at(self.px, self.py, (int(self.px), int(self.py))) if hasattr(self, "light_now") else (0, 0, 0)
        base = 0.72 if self.light_on else 0.16
        q = (int(clamp((base + lr * 0.9) * 16, 0, 16)), int(clamp((base * 0.95 + lg * 0.9) * 16, 0, 16)),
             int(clamp((base * 0.88 + lb * 0.9) * 16, 0, 16)))
        hc = self.__dict__.setdefault("_hand_cache", {})
        img = hc.get(q)
        if img is None:
            if len(hc) > 60:
                hc.clear()
            img = self.hand_fp.copy()
            img.fill((min(255, q[0] * 16), min(255, q[1] * 16), min(255, q[2] * 16)), special_flags=pygame.BLEND_RGB_MULT)
            hc[q] = img
        bx, by = lens_c[0] - 180, lens_c[1] - 30
        scr.blit(img, (bx, by))
        lens = pygame.Rect(0, 0, 84, 26)
        lens.center = lens_c
        if self.light_on:
            pygame.draw.ellipse(scr, (255, 240, 200), lens)
            pygame.draw.ellipse(scr, (255, 255, 245), lens.inflate(-30, -10))
        else:
            pygame.draw.ellipse(scr, (10, 10, 12), lens)
            pygame.draw.arc(scr, (40, 40, 46), lens.inflate(-8, -6), 2.5, 3.4, 2)

    def glow_img(self, base, size, level=4):
        """Scaled glow sprites are cached by (rounded) size and brightness."""
        size = max(8, min(1100, (size // 16) * 16))
        key = (id(base), size, level)
        cache = self.__dict__.setdefault("_glow_cache", {})
        g = cache.get(key)
        if g is None:
            if len(cache) > 400:
                cache.clear()
            g = pygame.transform.scale(base, (size, size))
            if level < 4:
                v = int(255 * (level + 1) / 5)
                g.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
            cache[key] = g
        return g

    def draw_ash(self, scr, hz):
        """Ash and dust drifting in the air all around you - you only see it where there is light."""
        px, py = self.px, self.py
        if len(self.ash) < 110:
            for _ in range(110 - len(self.ash)):
                self.ash.append([px + random.uniform(-4, 4), py + random.uniform(-4, 4), random.uniform(0.05, 0.95),
                                 random.uniform(0, 6.28)])
        spot_x, spot_y = W / 2, H / 2 + 30
        zb = self.zbuf
        for p_ in self.ash:
            p_[3] += 0.012
            p_[0] += math.sin(p_[3]) * 0.0016
            p_[1] += math.cos(p_[3] * 0.7) * 0.0016
            p_[2] -= 0.0007
            if p_[2] < 0 or abs(p_[0] - px) > 4.5 or abs(p_[1] - py) > 4.5 or self.solid(p_[0], p_[1]):
                p_[0], p_[1], p_[2] = px + random.uniform(-4, 4), py + random.uniform(-4, 4), random.uniform(0.6, 0.98)
                continue
            pr = self.project(p_[0], p_[1])
            if not pr or pr[1] < 0.3:
                continue
            sx, depth = pr
            col = int(sx // CW)
            if not (0 <= col < NCOL) or depth > zb[col]:
                continue
            sy = hz + H / depth * (0.5 - p_[2])
            r_ = math.hypot(sx - spot_x, (sy - spot_y) * 1.2)
            b = (clamp(1 - r_ / 330, 0, 1) * (1 if self.light_on else 0)) * clamp(1.2 - depth / 5, 0, 1)
            lr, lg, lb = self.light_at(p_[0], p_[1], (int(p_[0]), int(p_[1])))
            cr = 190 * b + 300 * lr
            cg = 182 * b + 300 * lg
            cb_ = 165 * b + 300 * lb
            if cr + cg + cb_ < 25:
                continue
            size = 2 if depth < 1.4 else 1
            pygame.draw.circle(scr, (min(255, int(cr)), min(255, int(cg)), min(255, int(cb_))), (int(sx), int(sy)), size)

    def chromatic(self, scr, off):
        """Red and blue drift apart: your eyes can't focus."""
        red = scr.copy()
        red.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        scr.fill((0, 255, 255), special_flags=pygame.BLEND_RGB_MULT)
        scr.blit(red, (off, int(off * 0.3)), special_flags=pygame.BLEND_RGB_ADD)

    def text_shadow(self, font, text, color, center, surf=None):
        surf = surf or self.screen
        sh = font.render(text, True, (0, 0, 0))
        img = font.render(text, True, color)
        r = img.get_rect(center=center)
        surf.blit(sh, r.move(3, 3))
        surf.blit(img, r)

    def draw_hud(self):
        scr = self.screen
        # the eye: does it know where you are?
        ex_, ey_ = W - 60, 40
        st = self.ai
        if st == "hunt":
            col, open_ = (200, 20, 15), 1.0
        elif st in ("investigate", "search"):
            col, open_ = (200, 160, 60), 0.5
        else:
            col, open_ = (90, 85, 80), 0.12
        h = max(2, int(22 * open_))
        pygame.draw.ellipse(scr, (12, 10, 10), (ex_ - 30, ey_ - h // 2 - 2, 60, h + 4))
        pygame.draw.ellipse(scr, col, (ex_ - 28, ey_ - h // 2, 56, h), 2)
        if open_ > 0.3:
            pygame.draw.circle(scr, col, (ex_, ey_), max(2, int(h * 0.32)))
            pygame.draw.circle(scr, (0, 0, 0), (ex_, ey_), max(1, int(h * 0.14)))
        if st == "hunt" and int(self.t * 4) % 2 == 0:
            pygame.draw.ellipse(scr, (120, 0, 0), (ex_ - 34, ey_ - h // 2 - 6, 68, h + 12), 1)
        # how loud you are
        loud = max(self.noise, self.noise_event)
        nx_, ny_ = 26, H - 92
        for i in range(4):
            on = loud > [0.5, 2.0, 4.0, 7.0][i]
            c = (170, 160, 140) if on else (55, 52, 48)
            if on and i == 3:
                c = (200, 60, 40)
            pygame.draw.arc(scr, c, (nx_ - 6 - i * 7, ny_ - 6 - i * 7, 12 + i * 14, 12 + i * 14), -0.9, 0.9, 2)
        pygame.draw.circle(scr, (150, 140, 125), (nx_, ny_), 3)
        if getattr(self, "sneaking", False):
            scr.blit(self.f_small.render("sneaking", True, (120, 115, 105)), (nx_ + 40, ny_ - 9))
        # battery icon with segments
        bx, by = 24, H - 54
        pygame.draw.rect(scr, (120, 115, 105), (bx, by, 64, 26), 2, border_radius=4)
        pygame.draw.rect(scr, (120, 115, 105), (bx + 64, by + 8, 5, 10))
        segs = int(math.ceil(self.battery / 20))
        for i in range(5):
            col = (190, 175, 90) if self.battery > 25 else (190, 45, 30)
            if i < segs and not (self.battery <= 25 and int(self.t * 3) % 2 and i == segs - 1):
                pygame.draw.rect(scr, col, (bx + 5 + i * 12, by + 5, 9, 16), border_radius=2)
        # breath only shows when you are using it
        if self.stamina < 99:
            k = clamp((100 - self.stamina) / 20, 0, 1)
            pygame.draw.rect(scr, (int(50 * k), int(55 * k), int(60 * k)), (bx + 84, by + 9, 120, 8), border_radius=4)
            pygame.draw.rect(scr, (int(110 * k), int(140 * k), int(170 * k)), (bx + 84, by + 9, int(120 * self.stamina / 100), 8), border_radius=4)
        if self.msg_t > 0:
            alpha = clamp(self.msg_t, 0, 1)
            self.text_shadow(self.f_mid, self.msg_text, tuple(int(c * alpha) for c in (215, 205, 185)), (W // 2, 92))
        if self.zone_title_t > 0 and self.state == "play":
            k = clamp(min(self.zone_title_t, 4.5 - self.zone_title_t), 0, 1)
            name = " ".join(self.zone_title)
            self.text_shadow(self.f_serif, name, (int(185 * k), int(170 * k), int(150 * k)), (W // 2, H // 2 - 190))
            pygame.draw.line(scr, (int(110 * k), int(30 * k), int(25 * k)), (W // 2 - 160, H // 2 - 150), (W // 2 + 160, H // 2 - 150), 2)
        if self.sanity < 35 and self.seen and int(self.t * 6) % 2 == 0:
            self.text_shadow(self.f_serif_big, "LOOK AWAY", (170, 0, 0), (W // 2, H // 2 - 160))

    def make_paper(self):
        rnd = random.Random(4)
        p = pygame.Surface((580, 440), pygame.SRCALPHA)
        p.fill((206, 194, 160, 255))
        for _ in range(9000):
            x, y = rnd.randrange(580), rnd.randrange(440)
            d = rnd.randint(-22, 8)
            p.set_at((x, y), (clamp(206 + d, 0, 255), clamp(194 + d, 0, 255), clamp(160 + d, 0, 255), 255))
        edge = pygame.Surface((580, 440), pygame.SRCALPHA)   # darker, burnt edges
        for i in range(30):
            pygame.draw.rect(edge, (90, 60, 30, int(70 * (1 - i / 30))), (i, i, 580 - 2 * i, 440 - 2 * i), 1)
        p.blit(edge, (0, 0))
        pygame.draw.line(p, (175, 160, 125), (290, 0), (290, 440), 1)       # fold
        pygame.draw.line(p, (175, 160, 125), (0, 220), (580, 220), 1)
        pygame.draw.circle(p, (150, 110, 70), (470, 360), 46, 5)            # mug ring
        for _ in range(3):
            pygame.draw.ellipse(p, (170, 140, 100), (rnd.randint(10, 500), rnd.randint(10, 380), rnd.randint(20, 60), rnd.randint(14, 40)))
        # a bloody thumbprint
        for i in range(6):
            pygame.draw.ellipse(p, (120, 20, 15), (40 + i, 370 + i, 34 - 2 * i, 44 - 2 * i), 1)
        return p

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
        s_ = pygame.Surface((W, H), pygame.SRCALPHA)
        s_.fill((0, 0, 0, 205))
        self.screen.blit(s_, (0, 0))
        page = self.paper.copy()
        hdr = self.f_hand.render("- %d -" % (self.note_idx + 1), True, (110, 30, 25))
        page.blit(hdr, hdr.get_rect(center=(290, 40)))
        shown = NOTES[self.note_idx][: int(self.t * 40)]
        shaky = self.note_idx in (2, 5)
        for i, ln in enumerate(self.wrap(shown, self.f_hand, 500)):
            img = self.f_hand.render(ln, True, (40, 28, 22))
            j = random.uniform(-0.8, 0.8) if shaky else 0
            page.blit(img, (40 + j, 80 + i * 34 + j))
        ang = -2.0 + math.sin(self.t * 0.8) * 0.4
        page = pygame.transform.rotozoom(page, ang, min(1.0, 0.85 + self.t * 0.6))
        self.screen.blit(page, page.get_rect(center=(W // 2, H // 2 - 10)))
        if self.t > 0.6:
            self.blit_center(self.f_small, "[ SPACE ]", (150, 140, 130), H - 50)

    def draw_title(self):
        scr = self.screen
        # the real maze in 3D behind the title, the camera slowly turning in a room
        saved = (self.px, self.py, self.angle, self.light_on, self.ent_dist, self.bob, self.sway)
        self.px, self.py = self.title_cam
        self.angle = self.t * 0.12
        self.light_on, self.ent_dist, self.bob, self.sway = True, 99, 0, 0
        self.draw_world(view_only=True)
        (self.px, self.py, self.angle, self.light_on, self.ent_dist, self.bob, self.sway) = saved
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        scr.blit(dim, (0, 0))
        if self.title_face > 0:
            face = pygame.Surface((W, H))
            draw_face(face, W // 2, H // 2, 1.0)
            face.set_alpha(40)
            scr.blit(face, (0, 0))
        col = (165, 10, 8) if random.random() > 0.06 else (40, 0, 0)
        title_img = self.f_serif_big.render("T H E    H O L L O W", True, col)
        tr = title_img.get_rect(center=(W // 2, 190))
        self.text_shadow(self.f_serif_big, "T H E    H O L L O W", col, (W // 2, 190))
        for (fx, speed, maxlen, ph) in self.drips:
            x = int(W // 2 + fx * tr.width)
            prog = (self.t * speed + ph) % 1.0
            ln = maxlen * min(1.0, prog * 1.6)
            y0 = tr.bottom - 14
            pygame.draw.line(scr, (115, 4, 4), (x, y0), (x, int(y0 + ln)), 3)
            pygame.draw.circle(scr, (140, 6, 6), (x, int(y0 + ln)), 3)
            if prog > 0.62:   # a drop falls
                fy = y0 + maxlen + (prog - 0.62) * 900
                if fy < H:
                    pygame.draw.circle(scr, (130, 5, 5), (x, int(fy)), 2)
        pygame.draw.line(scr, (90, 20, 15), (W // 2 - 260, 250), (W // 2 + 260, 250), 2)
        self.text_shadow(self.f_mid, "Find the way out.  Do not let it touch you.", (175, 165, 150), (W // 2, 310))
        lines = ["WASD - walk    MOUSE - look    SHIFT - run (loud)    C - sneak    F - flashlight",
                 "It doesn't know where you are.  It listens.  It looks for light.  C = sneak.",
                 "Corridors close in.   Rooms are safe.   The walls are never where you left them."]
        for i, ln in enumerate(lines):
            self.text_shadow(self.f_small, ln, (140, 132, 122), (W // 2, 390 + i * 32))
        if int(self.t * 2) % 2 == 0:
            self.text_shadow(self.f_mid, "press ENTER", (200, 190, 175), (W // 2, 545))
        self.blit_center(self.f_small, "headphones on.  lights off.", (95, 88, 80), 650)
        if self.floor_tex is None:
            self.blit_center(self.f_small, "(pip install numpy  for textured floors)", (70, 66, 60), 680)

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

    def draw_crushed(self):
        scr = self.screen
        t = self.t
        k = clamp(t / 0.35, 0, 1) ** 2
        scr.blit(self.crush_frame, (random.randint(-25, 25), random.randint(-25, 25)))
        w = int(W / 2 * k)
        pygame.draw.rect(scr, (30, 26, 24), (0, 0, w, H))
        pygame.draw.rect(scr, (30, 26, 24), (W - w, 0, w, H))
        pygame.draw.line(scr, (70, 62, 55), (w, 0), (w, H), 4)
        pygame.draw.line(scr, (70, 62, 55), (W - w, 0), (W - w, H), 4)
        if t > 0.35:
            scr.fill((0, 0, 0))
            if t < 0.5:
                scr.fill((140, 0, 0))

    def draw_dead(self):
        scr = self.screen
        t = self.t
        if self.death_frame is not None and getattr(self, "death_bg", None) is None:
            try:
                bg = pygame.transform.grayscale(self.death_frame)
            except Exception:
                bg = self.death_frame.copy()
            bg.fill((150, 70, 64), special_flags=pygame.BLEND_RGB_MULT)
            self.death_bg = bg
        scr.fill((0, 0, 0))
        if getattr(self, "death_bg", None) is not None:
            k = clamp(t / 2.0, 0, 1)
            bg = self.death_bg.copy()
            v = int(255 * (0.25 + 0.35 * k))
            bg.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
            z = 1.0 + 0.05 * k
            bg = pygame.transform.smoothscale(bg, (int(W * z), int(H * z)))
            scr.blit(bg, bg.get_rect(center=(W // 2, H // 2)))
            scr.blit(self.vignette, (0, 0))
            scr.blit(self.vignette, (0, 0))
        k = clamp(t / 1.5, 0, 1)
        title_c = (int(170 * k), int(8 * k), int(6 * k))
        self.text_shadow(self.f_serif_big, " ".join(self.death_cause), title_c, (W // 2, H // 2 - 70))
        # blood running down from the letters
        img = self.f_serif_big.render(" ".join(self.death_cause), True, title_c)
        rr = img.get_rect(center=(W // 2, H // 2 - 70))
        rnd = random.Random(len(self.death_cause))
        for i in range(10):
            x = rr.left + rnd.uniform(0.05, 0.95) * rr.width
            ln = clamp(t * rnd.uniform(15, 40), 0, rnd.uniform(30, 110))
            pygame.draw.line(scr, (int(110 * k), 0, 0), (int(x), rr.bottom - 16), (int(x), int(rr.bottom - 16 + ln)), 3)
        mins, secs = divmod(int(self.alive_t), 60)
        self.text_shadow(self.f_mid, "you were %d%% of the way out      survived %d:%02d" % (int(self.progress * 100), mins, secs),
                         (int(170 * k), int(160 * k), int(145 * k)), (W // 2, H // 2 + 60))
        if t > 1.5:
            self.text_shadow(self.f_small, "ENTER - try again        ESC - quit", (150, 140, 130), (W // 2, H // 2 + 140))
        scr.blit(self.grain[int(t * 24) % 4], (0, 0))

    def build_outside(self):
        """The night outside the maze."""
        bg = pygame.Surface((W, H))
        for y in range(H):
            k = y / H
            pygame.draw.line(bg, (int(8 + 22 * k), int(12 + 26 * k), int(30 + 40 * k)), (0, y), (W, y))
        rnd = random.Random(3)
        for _ in range(260):
            b = rnd.randint(90, 230)
            bg.set_at((rnd.randrange(W), rnd.randrange(int(H * 0.6))), (b, b, min(255, b + 20)))
        # moon with a halo
        for i in range(30):
            r = 120 - i * 3
            c = int(4 + i * 1.6)
            pygame.draw.circle(bg, (min(255, 18 + c), min(255, 24 + c), min(255, 46 + c)), (840, 300), r)
        pygame.draw.circle(bg, (232, 236, 248), (840, 300), 38)
        pygame.draw.circle(bg, (205, 210, 225), (825, 290), 8)
        pygame.draw.circle(bg, (210, 214, 230), (852, 316), 6)
        # far tree line
        x = 0
        while x < W:
            h = rnd.randint(60, 150)
            w = rnd.randint(30, 60)
            pygame.draw.polygon(bg, (12, 18, 26), [(x - w // 2, 520), (x + w // 2, 520), (x, 520 - h)])
            x += rnd.randint(18, 40)
        # the building you escaped from
        pygame.draw.rect(bg, (6, 6, 9), (90, 250, 380, 300))
        pygame.draw.polygon(bg, (6, 6, 9), [(70, 255), (490, 255), (280, 170)])
        for wx in (140, 210, 350, 420):
            pygame.draw.rect(bg, (14, 14, 18), (wx, 320, 26, 40))
        pygame.draw.rect(bg, (2, 2, 3), (255, 430, 54, 120))         # the open door
        # ground
        pygame.draw.rect(bg, (14, 22, 18), (0, 540, W, H - 540))
        for _ in range(500):
            gx = rnd.randrange(W)
            gy = rnd.randint(545, H)
            pygame.draw.line(bg, (24, 36, 28), (gx, gy), (gx + rnd.randint(-2, 2), gy - rnd.randint(3, 8)), 1)
        return bg

    def draw_outside(self, t):
        scr = self.screen
        if getattr(self, "outside", None) is None:
            self.outside = self.build_outside()
        scr.blit(self.outside, (0, 0))
        # something is still standing in the doorway, watching you leave
        if t > 3.2 and int(t * 2.3) % 7 != 0:
            pygame.draw.circle(scr, (200, 10, 8), (275, 468), 2)
            pygame.draw.circle(scr, (200, 10, 8), (289, 468), 2)
        # drifting ground fog
        fog = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(7):
            fx = (i * 230 + t * (12 + i * 3)) % (W + 400) - 200
            pygame.draw.ellipse(fog, (150, 160, 175, 22), (fx, 500 + (i % 3) * 30, 420, 70))
        scr.blit(fog, (0, 0))

    def draw_win(self):
        scr = self.screen
        t = self.t
        if 6.0 < t < 6.35:
            scr.fill((0, 0, 0))
            draw_face(scr, W // 2, H // 2 - 30, 1.2, jit=8)
            return
        self.draw_outside(t)
        if t < 1.2:   # fade in from the dark corridor
            f = pygame.Surface((W, H))
            f.set_alpha(int(255 * (1 - t / 1.2)))
            scr.blit(f, (0, 0))
        k = clamp((t - 0.8) / 2.0, 0, 1)
        if t < 6:
            self.text_shadow(self.f_serif_big, "Y O U    E S C A P E D", (int(225 * k), int(222 * k), int(212 * k)), (W // 2, 120))
            if t > 3:
                kk = clamp((t - 3) / 1.5, 0, 1)
                self.text_shadow(self.f_serif, "...didn't you?", (int(170 * kk), int(160 * kk), int(150 * kk)), (W // 2, 210))
        else:
            dim = pygame.Surface((W, H), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 150))
            scr.blit(dim, (0, 0))
            self.text_shadow(self.f_serif, "see you tomorrow night.", (165, 8, 6), (W // 2, H // 2 - 20))
            if t > 7.5:
                self.text_shadow(self.f_small, "ENTER - play again        ESC - quit", (150, 140, 130), (W // 2, H // 2 + 70))
        scr.blit(self.vignette, (0, 0))
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