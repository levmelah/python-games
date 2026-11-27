# -*- coding: utf-8 -*-
"""
קפטן מאונך נגד דוקטור טעות - הרפתקת חיסור במאונך עם פריטה

הפעלה:
    pip install pygame python-bidi
    python captain_vertical.py

איך משחקים:
    1. דוקטור טעות פותר תרגיל - ותמיד טועה! לוחצים על הספרה הלא נכונה בתשובה שלו.
    2. פותרים את התרגיל נכון, עמודה אחרי עמודה, מתחילים באחדות.
       - הספרה למעלה קטנה מהספרה למטה? לוחצים "לווים מהשכן" (או רווח).
       - בוחרים את התשובה בכפתורי המספרים (או במקלדת 0-9).
    3. רצף של תשובות נכונות ממלא את מד ה"עיפרון-על" - לוחצים S למכה ענקית!

מקשים: M - מוזיקה, Esc - חזרה למפה
בכל פעם שסוגרים את המשחק, הניקוד והכוכבים מתאפסים.
"""
import json
import math
import os
import random
import re
import sys
from array import array
from functools import lru_cache

import pygame
import pygame.gfxdraw as gfx

W, H = 1100, 720
FPS = 60
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captain_save.json")

# ---------------------------------------------------------------- צבעים
WHITE = (255, 255, 255)
CREAM = (253, 247, 232)
INK = (40, 40, 70)
NAVY = (44, 56, 140)
BLUE = (60, 110, 230)
GREEN = (70, 175, 60)
LIME = (130, 210, 70)
RED = (230, 60, 70)
ORANGE = (255, 150, 40)
YELLOW = (255, 205, 60)
GOLD = (255, 190, 30)
PINK = (250, 170, 190)
PURPLE = (150, 90, 220)
GRAY = (170, 170, 185)

HERO_X, VILLAIN_X, CHAR_Y = 935, 165, 400
COLS_X = [470, 550, 630]
SUPER_MAX = 4

WORLDS = [
    {"name": "הכיתה", "tier": 1, "intro": "ברוכים הבאים לכיתה שלי! פה כל התשובות שגויות!"},
    {"name": "הג'ונגל", "tier": 2, "intro": "בג'ונגל אף אחד לא לווה מהשכן! חה-חה!"},
    {"name": "הירח", "tier": 3, "intro": "על הירח אין כוח משיכה... וגם אין פריטה!"},
    {"name": "הר הגעש", "tier": 4, "intro": "הר הגעש שלי ימיס לכם את כל העשרות!"},
    {"name": "המעבדה", "tier": 4, "intro": "ברוכים הבאים למעבדה שלי! כאן אני הכי חזק!"},
]


# ---------------------------------------------------------------- עברית וטקסט
_HEB = re.compile(r"[֐-׿]")
try:
    from bidi import get_display as _bidi
except Exception:
    try:
        from bidi.algorithm import get_display as _bidi
    except Exception:
        _bidi = None


def heb(s):
    if not _HEB.search(s):
        return s
    if _bidi:
        return _bidi(s)
    rev = s[::-1]
    return re.sub(r"[0-9A-Za-z]+", lambda m: m.group(0)[::-1], rev)


_fonts = {}


def font(size, bold=True):
    if (size, bold) not in _fonts:
        _fonts[(size, bold)] = pygame.font.SysFont(
            "segoeui,arial,arialhebrew,dejavusans,liberationsans,freesans", size, bold=bold)
    return _fonts[(size, bold)]


@lru_cache(maxsize=2048)
def render(s, size, color, bold=True):
    return font(size, bold).render(heb(s), True, color)


@lru_cache(maxsize=512)
def render_outlined(s, size, color, outline, width, bold=True):
    base = render(s, size, color, bold)
    ol = render(s, size, outline, bold)
    surf = pygame.Surface((base.get_width() + width * 2, base.get_height() + width * 2), pygame.SRCALPHA)
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx * dx + dy * dy <= width * width + 1:
                surf.blit(ol, (dx + width, dy + width))
    surf.blit(base, (width, width))
    return surf


def text(s, t, size, color, center, bold=True, outline=None, ow=3, scale=1.0, alpha=255):
    img = render_outlined(t, size, tuple(color), tuple(outline), ow, bold) if outline else \
        render(t, size, tuple(color), bold)
    if scale != 1.0:
        img = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * scale)),
                                                 max(1, int(img.get_height() * scale))))
    if alpha < 255:
        img = img.copy()
        img.set_alpha(alpha)
    r = img.get_rect(center=(int(center[0]), int(center[1])))
    s.blit(img, r)
    return r


def title_row(s, y, size, small, center_x=W / 2):
    """'קפטן מאונך נגד דוקטור טעות' - מימין לשמאל, בשלושה צבעים."""
    parts = [render_outlined("קפטן מאונך", size, BLUE, WHITE, 4),
             render("נגד", small, INK),
             render_outlined("דוקטור טעות", size, GREEN, WHITE, 4)]
    gap = 16
    total = sum(p.get_width() for p in parts) + gap * 2
    x = center_x + total / 2
    for p in parts:
        x -= p.get_width()
        s.blit(p, p.get_rect(midleft=(x, y + (6 if p is parts[1] else 0))))
        x -= gap


def wrap(t, size, width):
    words, lines, cur = t.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font(size).size(test)[0] > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- ציור בסיסי
def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def circle(s, col, x, y, r):
    x, y, r = int(x), int(y), int(r)
    if r >= 1:
        gfx.filled_circle(s, x, y, r, col)
        gfx.aacircle(s, x, y, r, col)


def ellipse(s, col, x, y, rx, ry):
    x, y, rx, ry = int(x), int(y), int(rx), int(ry)
    if rx >= 1 and ry >= 1:
        gfx.filled_ellipse(s, x, y, rx, ry, col)
        gfx.aaellipse(s, x, y, rx, ry, col)


def poly(s, col, pts):
    pts = [(int(x), int(y)) for x, y in pts]
    gfx.filled_polygon(s, pts, col)
    gfx.aapolygon(s, pts, col)


def outlined_circle(s, col, x, y, r, ow=4, oc=INK):
    circle(s, oc, x, y, r + ow)
    circle(s, col, x, y, r)


def outlined_ellipse(s, col, x, y, rx, ry, ow=4, oc=INK):
    ellipse(s, oc, x, y, rx + ow, ry + ow)
    ellipse(s, col, x, y, rx, ry)


def thick(s, col, a, b, w):
    pygame.draw.line(s, col, a, b, max(1, int(w)))
    circle(s, col, a[0], a[1], w / 2)
    circle(s, col, b[0], b[1], w / 2)


def rounded(s, rect, col, radius=18, border=INK, bw=4, shadow=True):
    rect = pygame.Rect(rect)
    if shadow:
        sh = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(sh, (40, 30, 20, 55), sh.get_rect(), border_radius=radius)
        s.blit(sh, (rect.x + 4, rect.y + 6))
    pygame.draw.rect(s, col, rect, border_radius=radius)
    if border:
        pygame.draw.rect(s, border, rect, bw, border_radius=radius)


def button(s, rect, col, label, size=30, hover=False, pressed=False, enabled=True, glow=0.0):
    rect = pygame.Rect(rect)
    if not enabled:
        col = (200, 200, 205)
    if glow > 0:
        g = pygame.Surface((rect.w + 40, rect.h + 40), pygame.SRCALPHA)
        for k in range(10, 0, -2):
            pygame.draw.rect(g, (*col, int(25 * glow)), (20 - k * 2, 20 - k * 2, rect.w + k * 4, rect.h + k * 4),
                             border_radius=20 + k)
        s.blit(g, (rect.x - 20, rect.y - 14))
    dark = mix(col, (0, 0, 0), 0.3)
    depth = 2 if pressed else 6
    pygame.draw.rect(s, INK, rect.move(0, 6).inflate(6, 6), border_radius=16)
    pygame.draw.rect(s, dark, rect.move(0, 6), border_radius=14)
    face = rect.move(0, 6 - depth)
    pygame.draw.rect(s, mix(col, WHITE, 0.15) if hover and enabled else col, face, border_radius=14)
    pygame.draw.rect(s, mix(col, WHITE, 0.4), (face.x + 8, face.y + 5, face.w - 16, face.h * 0.28),
                     border_radius=8)
    text(s, label, size, WHITE, face.center, outline=dark, ow=2)


def star(s, x, y, r, col, rot=0.0, outline=False):
    pts = []
    for k in range(10):
        a = rot + k * math.pi / 5 - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    if outline:
        big = []
        for k in range(10):
            a = rot + k * math.pi / 5 - math.pi / 2
            rr = (r + 4) if k % 2 == 0 else (r + 4) * 0.48
            big.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        poly(s, INK, big)
    poly(s, col, pts)


def heart(s, x, y, size, col=RED):
    r = size * 0.55
    circle(s, INK, x - r * 0.95, y, r + 2)
    circle(s, INK, x + r * 0.95, y, r + 2)
    poly(s, INK, [(x - r * 2.05, y + r * 0.3), (x + r * 2.05, y + r * 0.3), (x, y + r * 2.75)])
    circle(s, col, x - r * 0.95, y, r)
    circle(s, col, x + r * 0.95, y, r)
    poly(s, col, [(x - r * 1.9, y + r * 0.35), (x + r * 1.9, y + r * 0.35), (x, y + r * 2.5)])
    circle(s, mix(col, WHITE, 0.6), x - r * 1.1, y - r * 0.25, r * 0.3)


def bubble(s, t, rect, tail, col=WHITE, size=21, tcol=INK, pop=1.0):
    rect = pygame.Rect(rect)
    lines = wrap(t, size, rect.w - 30)
    rect.h = 26 + len(lines) * (size + 8)
    surf = pygame.Surface((rect.w + 20, rect.h + 80), pygame.SRCALPHA)
    ox, oy = 10, 10
    r = pygame.Rect(ox, oy, rect.w, rect.h)
    tx, ty = tail[0] - rect.x + ox, tail[1] - rect.y + oy
    base_x = max(r.x + 30, min(r.right - 30, tx))
    poly(surf, INK, [(base_x - 16, r.bottom - 6), (base_x + 16, r.bottom - 6), (tx, ty + 4)])
    rounded(surf, r, col, 22)
    poly(surf, col, [(base_x - 12, r.bottom - 8), (base_x + 12, r.bottom - 8), (tx, ty - 2)])
    for k, ln in enumerate(lines):
        text(surf, ln, size, tcol, (r.centerx, r.y + 13 + (size + 8) * (k + 0.5) + 2))
    oh = surf.get_height()
    if pop != 1.0:
        surf = pygame.transform.smoothscale(surf, (max(1, int(surf.get_width() * pop)),
                                                   max(1, int(surf.get_height() * pop))))
    s.blit(surf, surf.get_rect(center=(rect.centerx, rect.y - 10 + oh / 2)))


def soft_glow(s, x, y, r, col, strength=40):
    g = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    for k in range(r, 0, -8):
        pygame.draw.circle(g, (*col, int(strength * (1 - k / r))), (r, r), k)
    s.blit(g, (x - r, y - r))


# ---------------------------------------------------------------- צלילים (מסונתזים, בלי קבצים)
class Sounds:
    def __init__(self):
        self.ok = False
        self.music_on = True
        self.sfx = {}
        try:
            init = pygame.mixer.get_init()
            if not init:
                pygame.mixer.init(22050, -16, 1, 512)
                init = pygame.mixer.get_init()
            self.rate, _, self.ch = init
            self.ok = True
        except Exception:
            return
        S = self.synth
        self.sfx = {
            "click": S([(900, 900, 0.03)], "tri", 0.25),
            "correct": S([(660, 660, 0.08), (990, 990, 0.16)], "tri", 0.35),
            "wrong": S([(180, 140, 0.25)], "square", 0.22),
            "throw": S([(300, 1200, 0.25)], "noise_sweep", 0.18),
            "hit": S([(160, 60, 0.18)], "sine", 0.6),
            "goo": S([(420, 90, 0.3)], "wobble", 0.35),
            "borrow": S([(400, 900, 0.22)], "tri", 0.3),
            "laugh": S([(560, 480, 0.08), (0, 0, 0.04), (600, 500, 0.08), (0, 0, 0.04),
                        (640, 520, 0.09), (0, 0, 0.04), (520, 380, 0.14)], "square", 0.12),
            "star": S([(1320, 1320, 0.12), (1760, 1760, 0.22)], "tri", 0.3),
            "win": S([(523, 523, 0.12), (659, 659, 0.12), (784, 784, 0.12), (1046, 1046, 0.4)], "tri", 0.35),
            "lose": S([(392, 392, 0.2), (330, 330, 0.2), (262, 220, 0.5)], "tri", 0.3),
            "super": S([(200, 1600, 0.35), (1600, 1600, 0.25)], "square", 0.15),
            "shuffle": S([(700, 300, 0.1), (300, 700, 0.1), (700, 300, 0.1)], "tri", 0.25),
            "page": S([(500, 800, 0.08)], "tri", 0.2),
        }
        try:
            self.music = self.make(self.build_music())
            self.music.set_volume(0.5)
            self.music_ch = self.music.play(loops=-1)
        except Exception:
            self.music = None

    def make(self, samples):
        arr = array("h")
        for v in samples:
            iv = int(max(-1.0, min(1.0, v)) * 30000)
            arr.append(iv)
            if self.ch == 2:
                arr.append(iv)
        return pygame.mixer.Sound(buffer=arr.tobytes())

    def wave(self, kind, phase):
        if kind in ("sine", "wobble"):
            return math.sin(phase)
        if kind == "square":
            return 0.7 if math.sin(phase) > 0 else -0.7
        return 2 / math.pi * math.asin(math.sin(phase))

    def samples(self, notes, kind, vol):
        out, phase = [], 0.0
        for f0, f1, d in notes:
            n = int(self.rate * d)
            for i in range(n):
                t = i / n
                if f0 == 0:
                    out.append(0.0)
                    continue
                f = f0 + (f1 - f0) * t
                if kind == "wobble":
                    f *= 1 + 0.25 * math.sin(i / self.rate * 60)
                phase += 2 * math.pi * f / self.rate
                if kind == "noise_sweep":
                    v = random.uniform(-1, 1) * 0.6 + math.sin(phase) * 0.4
                else:
                    v = self.wave(kind, phase)
                env = min(1.0, i / (self.rate * 0.006)) * (1 - t) ** 1.3
                out.append(v * env * vol)
        return out

    def synth(self, notes, kind, vol):
        return self.make(self.samples(notes, kind, vol))

    def build_music(self):
        """לולאה קצבית ועליזה: מנגינה + בס."""
        beat = 0.22
        mel = [72, 76, 79, 76, 77, 74, 71, 74, 72, 76, 79, 84, 83, 79, 77, 74,
               72, 76, 79, 76, 77, 81, 79, 77, 76, 74, 72, 74, 76, 74, 72, 0]
        bass = [48, 48, 43, 43, 41, 41, 43, 43] * 4
        f = lambda m: 440 * 2 ** ((m - 69) / 12)
        n = int(self.rate * beat)
        total = [0.0] * (n * len(mel))
        for k, m in enumerate(mel):
            if m:
                s = self.samples([(f(m), f(m), beat)], "tri", 0.10)
                for i, v in enumerate(s):
                    total[k * n + i] += v
        for k, m in enumerate(bass):
            s = self.samples([(f(m), f(m), beat * 0.9)], "sine", 0.16)
            for i, v in enumerate(s):
                total[k * n + i] += v
        return total

    def play(self, name):
        if self.ok and name in self.sfx:
            self.sfx[name].play()

    def toggle_music(self):
        self.music_on = not self.music_on
        if self.ok and self.music:
            self.music.set_volume(0.5 if self.music_on else 0.0)


# ---------------------------------------------------------------- הדמויות
def draw_captain(s, x, y, t, hit=0.0, cheer=0.0, sc=1.0, power=0.0):
    """קפטן מאונך - פיל-על עם מסכה, גלימה ועיפרון."""
    if hit > 0:
        x += math.sin(t * 50) * 8 * hit
    bob = math.sin(t * 2.5) * 4 - cheer * 18 * abs(math.sin(t * 10))
    y += bob
    k = sc
    if power > 0:
        soft_glow(s, x, y, int(150 * k), GOLD, int(60 * power))
    sh = pygame.Surface((int(170 * k), int(30 * k)), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (40, 30, 20, 55), sh.get_rect())
    s.blit(sh, (x - 85 * k, y + 150 * k - bob))
    wave = math.sin(t * 4) * 6 * k
    poly(s, INK, [(x - 52 * k, y + 30 * k), (x + 52 * k, y + 30 * k), (x + 78 * k + wave, y + 150 * k),
                  (x - 78 * k + wave, y + 150 * k)])
    poly(s, (210, 70, 50), [(x - 46 * k, y + 34 * k), (x + 46 * k, y + 34 * k), (x + 72 * k + wave, y + 145 * k),
                            (x - 72 * k + wave, y + 145 * k)])
    for side in (-1, 1):
        rounded(s, (x + side * 22 * k - 16 * k, y + 105 * k, 32 * k, 42 * k), (140, 150, 195), 10, bw=3, shadow=False)
    body = pygame.Rect(0, 0, 100 * k, 90 * k)
    body.center = (x, y + 72 * k)
    rounded(s, body, (70, 110, 220), int(30 * k), bw=4, shadow=False)
    pygame.draw.rect(s, YELLOW, (body.x + 4, body.centery + 8 * k, body.w - 8, 12 * k))
    pygame.draw.rect(s, INK, (body.x + 4, body.centery + 8 * k, body.w - 8, 12 * k), 2)
    outlined_circle(s, YELLOW, x, y + 58 * k, 17 * k, 3)
    thick(s, RED, (x - 8 * k, y + 58 * k), (x + 8 * k, y + 58 * k), 6 * k)
    hx, hy = x + 62 * k, y + 70 * k
    thick(s, INK, (x + 40 * k, y + 50 * k), (hx, hy), 18 * k)
    thick(s, (150, 160, 200), (x + 40 * k, y + 50 * k), (hx, hy), 12 * k)
    outlined_circle(s, (240, 190, 60), hx + 8 * k, hy, 22 * k, 3)
    circle(s, (255, 245, 210), hx + 8 * k, hy, 15 * k)
    thick(s, RED, (hx, hy), (hx + 16 * k, hy), 5 * k)
    flap = math.sin(t * 3) * 4
    for side in (-1, 1):
        outlined_ellipse(s, (150, 160, 200), x + side * 72 * k, y - 40 * k + flap * side * 0.3, 48 * k, 58 * k, 4)
        ellipse(s, PINK, x + side * 72 * k, y - 38 * k, 32 * k, 42 * k)
    px, py = x - 70 * k, y - 120 * k
    thick(s, INK, (x - 48 * k, y + 40 * k), (px + 4 * k, py + 70 * k), 18 * k)
    thick(s, (150, 160, 200), (x - 48 * k, y + 40 * k), (px + 4 * k, py + 70 * k), 12 * k)
    pc = GOLD if power > 0.5 else YELLOW
    pr = pygame.Rect(px - 9 * k, py - 10 * k, 18 * k, 90 * k)
    pygame.draw.rect(s, INK, pr.inflate(6, 6), border_radius=4)
    pygame.draw.rect(s, pc, pr, border_radius=3)
    pygame.draw.rect(s, PINK, (pr.x, pr.bottom - 14 * k, pr.w, 14 * k), border_radius=3)
    poly(s, INK, [(pr.x - 3, pr.y + 2), (pr.right + 3, pr.y + 2), (px, pr.y - 24 * k)])
    poly(s, (240, 210, 160), [(pr.x, pr.y + 1), (pr.right, pr.y + 1), (px, pr.y - 20 * k)])
    poly(s, INK, [(px - 4 * k, pr.y - 12 * k), (px + 4 * k, pr.y - 12 * k), (px, pr.y - 20 * k)])
    sp = (math.sin(t * 5) + 1) / 2
    star(s, px + 26 * k, pr.y - 22 * k, (6 + 4 * sp) * k, WHITE, t)
    outlined_circle(s, (165, 175, 215), x, y - 40 * k, 58 * k, 4)
    mask = pygame.Rect(x - 60 * k, y - 62 * k, 120 * k, 30 * k)
    pygame.draw.rect(s, INK, mask.inflate(4, 6), border_radius=12)
    pygame.draw.rect(s, (40, 70, 170), mask, border_radius=12)
    tail_w = math.sin(t * 6) * 5
    poly(s, (40, 70, 170), [(x + 56 * k, y - 58 * k), (x + 92 * k, y - 70 * k + tail_w),
                            (x + 88 * k, y - 52 * k + tail_w), (x + 56 * k, y - 46 * k)])
    blink = (t % 4.0) < 0.12
    for side in (-1, 1):
        ex, ey = x + side * 22 * k, y - 48 * k
        if blink:
            thick(s, INK, (ex - 9 * k, ey), (ex + 9 * k, ey), 3)
        else:
            outlined_circle(s, WHITE, ex, ey, 12 * k, 2)
            circle(s, (60, 40, 30), ex, ey + 1, 8 * k)
            circle(s, WHITE, ex + 3 * k, ey - 3 * k, 3 * k)
        circle(s, PINK, x + side * 34 * k, y - 22 * k, 7 * k)
    curl = math.sin(t * 2) * 4
    tr = [(x, y - 34 * k), (x + 1 * k, y - 18 * k), (x + 3 * k, y - 2 * k), (x + 10 * k, y + 12 * k),
          (x + 22 * k + curl, y + 16 * k), (x + 28 * k + curl, y + 6 * k)]
    widths = [22, 20, 18, 15, 12, 10]
    for q in range(len(tr) - 1):
        thick(s, INK, tr[q], tr[q + 1], (widths[q] + 6) * k)
    for q in range(len(tr) - 1):
        thick(s, (165, 175, 215), tr[q], tr[q + 1], widths[q] * k)
    for q in (1, 2, 3):
        pygame.draw.arc(s, (120, 130, 175), (tr[q][0] - 7 * k, tr[q][1] - 3 * k, 14 * k, 8 * k),
                        math.pi, 2 * math.pi, 2)
    if hit > 0:
        for side in (-1, 1):
            thick(s, INK, (x + side * 28 * k, y - 66 * k), (x + side * 14 * k, y - 60 * k), 3)


def draw_doctor(s, x, y, t, hit=0.0, laugh=0.0, sc=1.0, world=0):
    """דוקטור טעות - חייזר ירוק עם שלוש עיניים, שש ידיים, ואביזר לכל עולם."""
    if hit > 0:
        x += math.sin(t * 50) * 8 * hit
    bob = math.sin(t * 2.2 + 1) * 5 - laugh * 14 * abs(math.sin(t * 14))
    y += bob
    k = sc
    green = LIME if hit <= 0 else mix(LIME, RED, 0.5)
    dark = mix(green, (0, 0, 0), 0.25)
    sh = pygame.Surface((int(170 * k), int(30 * k)), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (40, 30, 20, 55), sh.get_rect())
    s.blit(sh, (x - 85 * k, y + 150 * k - bob))
    if world == 4:                       # גלימת בוס סגולה
        wave = math.sin(t * 4) * 6
        poly(s, INK, [(x - 44 * k, y + 36 * k), (x + 44 * k, y + 36 * k), (x + 74 * k + wave, y + 150 * k),
                      (x - 74 * k + wave, y + 150 * k)])
        poly(s, PURPLE, [(x - 40 * k, y + 40 * k), (x + 40 * k, y + 40 * k), (x + 68 * k + wave, y + 145 * k),
                         (x - 68 * k + wave, y + 145 * k)])
    for side in (-1, 1):
        for j in range(3):
            base = (x + side * 30 * k, y + (50 + j * 18) * k)
            pts = []
            for q in range(7):
                u = q / 6
                ang = t * (4 + laugh * 4) + j * 1.3 + u * 3
                pts.append((base[0] + side * (u * 75 * k), base[1] + (j - 1) * 22 * k * u + math.sin(ang) * 10 * k))
            for q in range(len(pts) - 1):
                thick(s, INK, pts[q], pts[q + 1], 14 * k)
            for q in range(len(pts) - 1):
                thick(s, green, pts[q], pts[q + 1], 8 * k)
            outlined_circle(s, green, pts[-1][0], pts[-1][1], 7 * k, 3)
    body = pygame.Rect(0, 0, 90 * k, 95 * k)
    body.center = (x, y + 85 * k)
    rounded(s, body, green, int(34 * k), bw=4, shadow=False)
    poly(s, INK, [(x - 30 * k, y + 38 * k), (x + 30 * k, y + 38 * k), (x, y + 70 * k)])
    poly(s, WHITE, [(x - 26 * k, y + 40 * k), (x + 26 * k, y + 40 * k), (x, y + 66 * k)])
    for side in (-1, 1):
        poly(s, INK, [(x, y + 50 * k), (x + side * 26 * k, y + 38 * k), (x + side * 26 * k, y + 64 * k)])
        poly(s, RED, [(x, y + 51 * k), (x + side * 22 * k, y + 42 * k), (x + side * 22 * k, y + 60 * k)])
    outlined_circle(s, RED, x, y + 51 * k, 7 * k, 3)
    for side in (-1, 1):
        rounded(s, (x + side * 22 * k - 13 * k, y + 125 * k, 26 * k, 26 * k), dark, 10, bw=3, shadow=False)
    sway = math.sin(t * 3) * 8
    thick(s, INK, (x - 10 * k, y - 100 * k), (x - 30 * k + sway, y - 150 * k), 6)
    outlined_circle(s, YELLOW, x - 30 * k + sway, y - 154 * k, 12 * k, 3)
    thick(s, INK, (x + 40 * k, y - 85 * k), (x + 66 * k + sway * 0.5, y - 112 * k), 5)
    outlined_circle(s, RED, x + 66 * k + sway * 0.5, y - 115 * k, 8 * k, 3)
    outlined_circle(s, green, x, y - 30 * k, 72 * k, 4)
    circle(s, mix(green, WHITE, 0.25), x - 30 * k, y - 60 * k, 14 * k)
    eyes = [(-26, -40, 20), (24, -32, 17), (0, -82, 13)]
    for ex, ey, er in eyes:
        ex, ey, er = x + ex * k, y + ey * k, er * k
        outlined_circle(s, WHITE, ex, ey, er, 3)
        look = math.sin(t * 1.7 + ex) * er * 0.25
        circle(s, INK, ex + look, ey + 2, er * 0.5)
        circle(s, WHITE, ex + look + er * 0.2, ey - er * 0.15, er * 0.18)
    mo = 14 + laugh * 10 * abs(math.sin(t * 14))
    mouth = pygame.Rect(x - 26 * k, y + 2 * k, 52 * k, mo * k)
    pygame.draw.ellipse(s, INK, mouth.inflate(6, 6))
    pygame.draw.ellipse(s, (120, 30, 50), mouth)
    pygame.draw.rect(s, WHITE, (x - 6 * k, mouth.y, 12 * k, 11 * k))
    pygame.draw.rect(s, INK, (x - 6 * k, mouth.y, 12 * k, 11 * k), 2)
    ellipse(s, (240, 100, 120), x + 8 * k, mouth.bottom - 4 * k, 10 * k, 6 * k)
    for side in (-1, 1):
        circle(s, PINK, x + side * 50 * k, y - 4 * k, 9 * k)
    # אביזרים לפי עולם
    if world == 1:      # כובע ספארי
        ellipse(s, INK, x, y - 92 * k, 74 * k, 16 * k)
        ellipse(s, (210, 180, 110), x, y - 92 * k, 70 * k, 12 * k)
        outlined_ellipse(s, (210, 180, 110), x, y - 104 * k, 44 * k, 22 * k, 3)
        pygame.draw.rect(s, (150, 100, 50), (x - 44 * k, y - 102 * k, 88 * k, 7 * k))
    elif world == 2:    # קסדת חלל
        g = pygame.Surface((int(190 * k), int(190 * k)), pygame.SRCALPHA)
        pygame.draw.circle(g, (180, 230, 255, 70), (int(95 * k), int(95 * k)), int(92 * k))
        pygame.draw.circle(g, (255, 255, 255, 200), (int(95 * k), int(95 * k)), int(92 * k), 4)
        pygame.draw.ellipse(g, (255, 255, 255, 120), (40 * k, 30 * k, 30 * k, 50 * k))
        s.blit(g, (x - 95 * k, y - 125 * k))
    elif world == 3:    # משקפי שמש
        for side in (-1, 1):
            outlined_ellipse(s, (30, 30, 40), x + side * 25 * k, y - 38 * k, 22 * k, 15 * k, 3)
            ellipse(s, (90, 90, 120), x + side * 25 * k - 6 * k, y - 43 * k, 6 * k, 3 * k)
        thick(s, INK, (x - 4 * k, y - 40 * k), (x + 4 * k, y - 40 * k), 4)
    elif world == 4:    # כתר
        pts = [(x - 40 * k, y - 92 * k), (x - 46 * k, y - 132 * k), (x - 22 * k, y - 110 * k), (x, y - 142 * k),
               (x + 22 * k, y - 110 * k), (x + 46 * k, y - 132 * k), (x + 40 * k, y - 92 * k)]
        poly(s, INK, [(px_, py_ + (3 if py_ > y - 100 * k else -3)) for px_, py_ in pts])
        poly(s, GOLD, pts)
        for cx in (-22, 0, 22):
            circle(s, RED, x + cx * k, y - 100 * k, 4 * k)
    if hit > 0:
        poly(s, (120, 200, 255), [(x + 60 * k, y - 60 * k), (x + 52 * k, y - 44 * k), (x + 68 * k, y - 44 * k)])
        circle(s, (120, 200, 255), x + 60 * k, y - 42 * k, 8 * k)


# ---------------------------------------------------------------- רקעים לעולמות
def gradient(surf, top, bottom, y0=0, y1=H):
    for y in range(y0, y1):
        pygame.draw.line(surf, mix(top, bottom, (y - y0) / max(1, y1 - y0)), (0, y), (W, y))


def build_world_bg(world):
    bg = pygame.Surface((W, H))
    rnd = random.Random(world * 11 + 3)
    if world == 0:          # הכיתה
        bg.fill((250, 238, 206))
        for x in range(0, W, 26):
            for y in range(0, 470, 26):
                pygame.draw.circle(bg, (238, 222, 186), (x + 10, y + 10), 2)
        for wx in (40, 830):
            r = pygame.Rect(wx, 210, 230, 200)
            pygame.draw.rect(bg, (190, 225, 250), r, border_radius=8)
            pygame.draw.rect(bg, (170, 120, 70), r, 10, border_radius=8)
            pygame.draw.line(bg, (170, 120, 70), r.midtop, r.midbottom, 6)
            pygame.draw.line(bg, (170, 120, 70), r.midleft, r.midright, 6)
            pygame.draw.circle(bg, WHITE, (r.x + 70, r.y + 60), 20)
            pygame.draw.circle(bg, WHITE, (r.x + 95, r.y + 55), 26)
        pygame.draw.rect(bg, (220, 180, 130), (0, 470, W, 90))
        pygame.draw.line(bg, (180, 140, 90), (0, 470), (W, 470), 6)
        pygame.draw.rect(bg, (200, 150, 100), (0, 560, W, H - 560))
        for y in range(575, H, 30):
            pygame.draw.line(bg, (180, 130, 85), (0, y), (W, y), 2)
        for k, d in enumerate("0123456789"):
            fx = 300 + k * 52
            pygame.draw.polygon(bg, [RED, ORANGE, YELLOW, LIME, BLUE][k % 5], [(fx, 72), (fx + 40, 72), (fx + 20, 100)])
    elif world == 1:        # ג'ונגל
        gradient(bg, (175, 230, 160), (110, 185, 100), 0, 560)
        for _ in range(40):
            x, y = rnd.randint(-40, W + 40), rnd.randint(-40, 520)
            if 300 < x < 800 and y > 80:
                continue
            c = rnd.choice([(80, 160, 80), (60, 140, 70), (100, 180, 90)])
            ang = rnd.uniform(0, math.tau)
            leaf = pygame.Surface((140, 60), pygame.SRCALPHA)
            pygame.draw.ellipse(leaf, (*c, 220), leaf.get_rect())
            pygame.draw.line(leaf, (*mix(c, (0, 0, 0), 0.3), 220), (5, 30), (135, 30), 3)
            leaf = pygame.transform.rotate(leaf, math.degrees(ang))
            bg.blit(leaf, (x, y))
        for vx in (60, 280, 830, 1040):
            pts = [(vx + math.sin(y * 0.03) * 12, y) for y in range(0, 300, 10)]
            pygame.draw.lines(bg, (60, 120, 50), False, pts, 5)
        pygame.draw.rect(bg, (120, 90, 55), (0, 560, W, H - 560))
        for _ in range(60):
            x = rnd.randint(0, W)
            pygame.draw.line(bg, (80, 150, 60), (x, 562), (x + rnd.randint(-6, 6), 545), 3)
    elif world == 2:        # ירח
        gradient(bg, (10, 10, 35), (45, 25, 90))
        for _ in range(220):
            b = rnd.randint(120, 255)
            bg.set_at((rnd.randint(0, W), rnd.randint(0, 560)), (b, b, b))
        soft_glow(bg, 980, 120, 120, (90, 160, 255), 50)
        circle(bg, (90, 150, 230), 980, 120, 50)
        circle(bg, (110, 200, 120), 965, 105, 18)
        circle(bg, (110, 200, 120), 995, 135, 12)
        pts = [(0, H)] + [(x, 560 - 10 * math.sin(x * 0.012)) for x in range(0, W + 10, 10)] + [(W, H)]
        poly(bg, (150, 145, 170), pts)
        for _ in range(16):
            x, y, r = rnd.randint(0, W), rnd.randint(575, H - 10), rnd.randint(8, 22)
            ellipse(bg, (115, 110, 140), x, y, r, r * 0.4)
    elif world == 3:        # הר געש
        gradient(bg, (255, 200, 140), (210, 90, 70), 0, 560)
        for vx, vw in ((150, 330), (950, 360)):
            poly(bg, (110, 60, 60), [(vx - vw / 2, 560), (vx - 40, 230), (vx + 40, 230), (vx + vw / 2, 560)])
            poly(bg, (255, 120, 30), [(vx - 40, 230), (vx + 40, 230), (vx + 20, 260), (vx - 25, 270)])
            soft_glow(bg, vx, 220, 110, (255, 140, 40), 70)
            pygame.draw.line(bg, (255, 140, 40), (vx, 250), (vx - 30, 420), 6)
        for _ in range(30):
            soft_glow(bg, rnd.randint(0, W), rnd.randint(0, 200), 30, (120, 90, 90), 40)
        pygame.draw.rect(bg, (70, 40, 45), (0, 560, W, H - 560))
        for _ in range(12):
            x = rnd.randint(0, W)
            pts = [(x + rnd.randint(-15, 15) * k, 565 + k * 25) for k in range(6)]
            pygame.draw.lines(bg, (255, 120, 40), False, pts, 3)
    else:                   # המעבדה
        gradient(bg, (70, 45, 110), (30, 20, 55))
        for tx in (60, 120, 900, 970, 1040):
            tube = pygame.Rect(tx - 18, 180, 36, 280)
            pygame.draw.rect(bg, (180, 200, 220), tube.inflate(8, 8), border_radius=18)
            pygame.draw.rect(bg, (60, 200, 90), (tube.x, tube.y + 80, tube.w, tube.h - 80), border_radius=16)
            for _ in range(5):
                circle(bg, (150, 255, 160), tube.x + rnd.randint(8, 28), tube.y + rnd.randint(90, 270), rnd.randint(3, 6))
        for gx, gy, gr in ((260, 120, 40), (840, 110, 34)):
            for k in range(10):
                a = k / 10 * math.tau
                pygame.draw.circle(bg, (110, 90, 150), (int(gx + math.cos(a) * gr), int(gy + math.sin(a) * gr)), 10)
            circle(bg, (110, 90, 150), gx, gy, gr)
            circle(bg, (70, 45, 110), gx, gy, gr * 0.4)
        for y in range(560, H, 40):
            for x in range(0, W, 40):
                c = (60, 50, 90) if (x // 40 + y // 40) % 2 else (45, 35, 70)
                pygame.draw.rect(bg, c, (x, y, 40, 40))
    soft_glow(bg, HERO_X, CHAR_Y - 20, 210, (255, 220, 140), 45)
    soft_glow(bg, VILLAIN_X, CHAR_Y - 20, 210, (170, 240, 140), 45)
    return bg


# ---------------------------------------------------------------- תרגילים
def digits(n):
    return [n // 100, n // 10 % 10, n % 10]


def needs(a, b):
    ad, bd = digits(a), digits(b)
    u = ad[2] < bd[2]
    t = ad[1] - u < bd[1]
    return u, t


def make_problem(tier):
    """כל התרגילים במאות (תלת-ספרתי פחות תלת-ספרתי) וכולם דורשים פריטה.
       1: פריטה מהעשרות לאחדות   2: פריטה מהמאות לעשרות
       3: פריטה כפולה             4: גם אפס באמצע (לווים דרך העשרות)"""
    for _ in range(20000):
        a, b = random.randint(200, 989), random.randint(101, 899)
        if b >= a or a - b < 100 or b % 10 == 0:
            continue
        u, t = needs(a, b)
        ad = digits(a)
        if tier <= 1 and u and not t:
            return a, b
        if tier == 2 and t and not u:
            return a, b
        if tier == 3 and u and t and ad[1] != 0:
            return a, b
        if tier >= 4 and (u or t):
            if ad[1] == 0 and u:
                return a, b
            if random.random() < 0.4:
                return a, b
    return 403, 178


def doctor_answer(a, b):
    """התשובה השגויה של דוקטור טעות - טעויות אמיתיות שילדים עושים."""
    ad, bd = digits(a), digits(b)
    correct = a - b
    flipped = sum(abs(ad[i] - bd[i]) * 10 ** (2 - i) for i in range(3))
    no_dec = sum(((ad[i] + 10 if ad[i] < bd[i] else ad[i]) - bd[i]) * 10 ** (2 - i) for i in range(3))
    options = [x for x in (flipped, no_dec) if x != correct and x < 1000]
    if options and random.random() < 0.85:
        return random.choice(options)
    cd = digits(correct)
    i = 2 if a < 100 else random.randint(1, 2)
    cd[i] = (cd[i] + random.choice([1, 2, 9, 8])) % 10
    return cd[0] * 100 + cd[1] * 10 + cd[2]


# ---------------------------------------------------------------- שמירה
def load_save():
    """בלי שמירה: כל פתיחה של המשחק מתחילה מאפס (ניקוד, כוכבים ועולמות פתוחים).
    אם נשאר קובץ שמירה מגרסה קודמת - מוחקים אותו."""
    try:
        if os.path.exists(SAVE_PATH):
            os.remove(SAVE_PATH)
    except Exception:
        pass
    return {"stars": [0] * 5, "best": 0, "seen_intro": False}


def write_save(data):
    """ההתקדמות נשמרת רק כל עוד המשחק פתוח."""
    pass


# ---------------------------------------------------------------- טקסטים
HERO_HINT = "לא נכון! מתחילים מהאחדות, ואם אין מספיק - לווים מהשכן!"
HERO_WIN = ["בום! תפסתי אותך!", "המאונך מנצח!", "עמודה אחרי עמודה!", "ככה פותרים!", "עוד עיפרון בדרך!"]
DOC_TAUNT = ["חה-חה! לא פגעת!", "טעות זה הכיף שלי!", "מי צריך ללוות? חה-חה!", "אני הכי חכם ביקום!"]
DOC_HURT = ["אאוץ'!", "לא יכול להיות!", "אוי, העיפרון הזה!", "חשבתי שזה נכון..."]
STORY = [
    ("בעיר המספרים כולם פתרו תרגילים בשמחה, עמודה אחרי עמודה...", "hero"),
    ("עד שיום אחד נחת דוקטור טעות - והתחיל לבלבל את כל התרגילים!", "doctor"),
    ("רק גיבור אחד יכול לעצור אותו: קפטן מאונך, הפיל-על! עזרו לו לתקן את כל הטעויות!", "both"),
]


# ---------------------------------------------------------------- המשחק
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.time = 0.0
        self.snd = Sounds()
        self.save = load_save()
        self.world_bgs = {}
        self.map_bg = self.build_map_bg()
        self.buttons = {}
        self.particles = []
        self.popups = []
        self.shake = 0.0
        self.flash = 0.0
        self.story_page = 0
        self.state = "intro" if not self.save["seen_intro"] else "map"
        self.state_t = 0.0

    # ------------------------------------------------------------ מפה
    NODES = [(160, 540), (350, 380), (560, 520), (760, 360), (950, 500)]

    def build_map_bg(self):
        bg = pygame.Surface((W, H))
        gradient(bg, (190, 230, 255), (250, 240, 210))
        rnd = random.Random(5)
        for _ in range(8):
            x, y = rnd.randint(0, W), rnd.randint(90, 250)
            for dx, r in ((-30, 26), (0, 36), (30, 24)):
                circle(bg, WHITE, x + dx, y, r)
        pts = [(0, H)] + [(x, 300 + 30 * math.sin(x * 0.008) + 20 * math.sin(x * 0.02)) for x in range(0, W + 10, 10)] + [(W, H)]
        poly(bg, (170, 220, 140), pts)
        pts = [(0, H)] + [(x, 420 + 25 * math.sin(x * 0.012 + 1)) for x in range(0, W + 10, 10)] + [(W, H)]
        poly(bg, (140, 200, 115), pts)
        # שביל מנוקד בין התחנות
        path = []
        for i in range(len(self.NODES) - 1):
            (x0, y0), (x1, y1) = self.NODES[i], self.NODES[i + 1]
            for k in range(40):
                t = k / 40
                path.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t - math.sin(t * math.pi) * 40))
        for k, (x, y) in enumerate(path):
            if k % 3 == 0:
                circle(bg, (230, 200, 140), x, y, 7)
                circle(bg, (250, 230, 180), x, y, 5)
        return bg

    def unlocked(self, i):
        return i == 0 or self.save["stars"][i - 1] > 0

    # ------------------------------------------------------------ התחלת שלב
    def start_world(self, w):
        self.world = w
        if w not in self.world_bgs:
            self.world_bgs[w] = build_world_bg(w)
        self.bg = self.world_bgs[w]
        self.hearts = 5
        self.score = 0
        self.mistakes = 0
        self.super = 0
        self.doc_max = 6 + w * 2 + (2 if w == 4 else 0)
        self.doc_hp = self.doc_max
        self.shots = []
        self.hero_hit = self.doc_hit = self.hero_cheer = self.doc_laugh = 0.0
        self.hero_power = 0.0
        self.problems_done = 0
        self.pad_order = list(range(10))
        self.pad_x = {d: self.pad_slot_x(d) for d in range(10)}
        self.new_problem()
        self.doc_say = WORLDS[w]["intro"]
        self.doc_say_t = self.time
        self.state = "play"
        self.snd.play("laugh")

    def pad_slot_x(self, slot):
        return 205 + slot * 59

    # ------------------------------------------------------------ תרגיל
    def new_problem(self, problem=None):
        self.a, self.b = problem or make_problem(WORLDS[self.world]["tier"])
        self.wrong = doctor_answer(self.a, self.b)
        self.correct = self.a - self.b
        self.orig = digits(self.a)
        self.top = digits(self.a)
        self.bot = digits(self.b)
        self.ans = [None, None, None]
        self.ans_t = [0.0] * 3
        self.top_t = [-9.0] * 3
        self.show = [self.a >= 100, True, True]
        wd, cd = digits(self.wrong), digits(self.correct)
        self.wrong_cols = [i for i in range(3) if self.show[i] and wd[i] != cd[i]]
        self.marks = {}
        self.tries = 0
        self.phase = "find"
        self.phase_t = 0.0
        self.idle_t = 0.0
        self.col = 2
        self.done_t = -1.0
        self.flyers = []
        self.set_doc(f"חה-חה! {self.a} פחות {self.b} זה {self.wrong}!")
        self.doc_laugh = 1.2
        self.set_hero("רגע... משהו פה לא בסדר. איפה הטעות?")

    def set_hero(self, t):
        self.hero_say, self.hero_say_t = t, self.time

    def set_doc(self, t):
        self.doc_say, self.doc_say_t = t, self.time

    def need_borrow(self):
        return self.top[self.col] < self.bot[self.col]

    # ------------------------------------------------------------ פעולות
    def click_wrong_digit(self, i):
        if self.phase != "find" or i in self.marks:
            return
        self.tries += 1
        self.idle_t = 0
        if i in self.wrong_cols:
            self.marks[i] = "x"
            first = self.tries == 1
            self.attack_doctor(2 if first else 1, "תפסתי אותך! כאן טעית!")
            if first:
                self.add_super()
            self.phase = "erase"
            self.phase_t = 0.0
        else:
            self.marks[i] = "ok"
            self.set_doc("חה-חה! דווקא שם צדקתי!")
            self.doc_laugh = 1.0
            self.snd.play("laugh")
            self.set_hero("הספרה הזאת נכונה. בוא נבדוק עמודה אחרת")

    def borrow(self):
        if self.phase != "solve" or self.done_t >= 0:
            return
        self.idle_t = 0
        i = self.col
        if not self.need_borrow():
            self.set_hero(f"לא צריך ללוות כאן: {self.top[i]} לא קטן מ-{self.bot[i]}")
            self.snd.play("click")
            return
        j = i - 1
        delay = 0.0
        if self.top[j] == 0:
            self.top[j - 1] -= 1
            self.top[j] += 10
            self.top_t[j - 1] = self.top_t[j] = self.time
            self.flyers.append([COLS_X[j - 1], 0.0])
            delay = 0.45
            self.set_hero("לשכן אין כלום! לווים קודם מהמאות, ואז מהעשרות")
        else:
            self.set_hero(f"לווינו מהשכן! עכשיו למעלה {self.top[i] + 10}")
        self.top[j] -= 1
        self.top[i] += 10
        self.top_t[j] = self.top_t[i] = self.time + delay
        self.flyers.append([COLS_X[j], -delay])
        self.snd.play("borrow")

    def answer(self, d):
        if self.phase != "solve" or self.done_t >= 0:
            return
        self.idle_t = 0
        i = self.col
        if self.need_borrow():
            self.attack_hero(HERO_HINT)
            return
        if d != self.top[i] - self.bot[i]:
            self.attack_hero(f"לא נכון! {self.top[i]} פחות {self.bot[i]} זה לא {d}. נסה שוב!")
            return
        self.ans[i] = d
        self.ans_t[i] = self.time
        self.snd.play("correct")
        self.attack_doctor(1, random.choice(HERO_WIN))
        self.add_super()
        self.col -= 1
        if self.col >= 0 and all(self.top[k] == self.bot[k] for k in range(self.col + 1)):
            self.col = -1
        if self.col < 0 or (self.col == 0 and not self.show[0]):
            self.done_t = 0.0
            self.score += 50
            self.problems_done += 1
            self.popups.append(["+50", 550, 300, 1.4, ORANGE])
        elif self.world >= 1 and random.random() < 0.3:
            self.doctor_trick()

    def doctor_trick(self):
        """דוקטור טעות מערבב את כפתורי המספרים!"""
        random.shuffle(self.pad_order)
        self.set_doc("קסם ערבוב! חה-חה! עכשיו תמצאו את המספרים!")
        self.doc_laugh = 1.2
        self.snd.play("shuffle")
        self.snd.play("laugh")

    def add_super(self):
        self.super = min(SUPER_MAX, self.super + 1)
        if self.super == SUPER_MAX:
            self.set_hero("העיפרון-העל מוכן! לחצו S!")

    def use_super(self):
        if self.super < SUPER_MAX or self.state != "play" or self.doc_hp <= 0:
            return
        self.super = 0
        self.flash = 0.5
        self.hero_power = 1.2
        self.snd.play("super")
        self.shots.append({"kind": "super", "x": HERO_X - 60, "y": CHAR_Y - 80, "t": -0.25, "dmg": 3})
        self.set_hero("עיפרון-על! מכה מאונכת!")

    def attack_doctor(self, dmg, line):
        self.shots.append({"kind": "pencil", "x": HERO_X - 60, "y": CHAR_Y - 60, "t": 0.0, "dmg": dmg})
        self.set_hero(line)
        self.hero_cheer = 0.8
        self.score += 10 * dmg
        self.snd.play("throw")

    def attack_hero(self, line):
        self.shots.append({"kind": "goo", "x": VILLAIN_X + 60, "y": CHAR_Y - 30, "t": 0.0, "dmg": 1})
        self.set_doc(random.choice(DOC_TAUNT))
        self.doc_laugh = 1.2
        self.set_hero(line)
        self.mistakes += 1
        self.super = 0
        self.snd.play("wrong")
        self.snd.play("laugh")

    # ------------------------------------------------------------ סיום שלב
    def stars_for_level(self):
        if self.mistakes <= 1:
            return 3
        if self.mistakes <= 3:
            return 2
        return 1

    def win_world(self):
        self.state = "levelwin"
        self.state_t = 0.0
        self.earned = self.stars_for_level()
        w = self.world
        self.save["stars"][w] = max(self.save["stars"][w], self.earned)
        self.save["best"] = max(self.save["best"], self.score)
        write_save(self.save)
        self.snd.play("win")
        self.star_sounded = 0

    # ------------------------------------------------------------ עדכון
    def burst(self, x, y, cols, n=24, speed=300):
        for _ in range(n):
            a = random.random() * math.tau
            sp = random.uniform(60, speed)
            self.particles.append([x, y, math.cos(a) * sp, math.sin(a) * sp - 120, random.uniform(0.6, 1.1),
                                   random.choice(cols), random.random() * 6, random.choice([0, 1])])

    def update(self, dt):
        self.time += dt
        self.state_t += dt
        self.shake = max(0, self.shake - 50 * dt)
        self.flash = max(0, self.flash - dt)
        for p in self.particles[:]:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 600 * dt
            p[4] -= dt
            p[6] += dt * 8
            if p[4] <= 0:
                self.particles.remove(p)
        for pu in self.popups[:]:
            pu[2] -= 50 * dt
            pu[3] -= dt
            if pu[3] <= 0:
                self.popups.remove(pu)
        if self.state == "levelwin":
            n = min(self.earned, int((self.state_t - 0.5) / 0.45) + 1) if self.state_t > 0.5 else 0
            while self.star_sounded < n:
                self.star_sounded += 1
                self.snd.play("star")
                self.burst(W / 2 - 100 + (self.star_sounded - 1) * 100, 300, [GOLD, YELLOW, WHITE], 20)
            return
        if self.state != "play":
            return
        self.hero_hit = max(0, self.hero_hit - dt)
        self.doc_hit = max(0, self.doc_hit - dt)
        self.hero_cheer = max(0, self.hero_cheer - dt)
        self.doc_laugh = max(0, self.doc_laugh - dt)
        self.hero_power = max(0, self.hero_power - dt)
        self.idle_t += dt
        for d in range(10):                 # כפתורים מחליקים למקום החדש אחרי ערבוב
            target = self.pad_slot_x(self.pad_order.index(d))
            self.pad_x[d] += (target - self.pad_x[d]) * min(1, dt * 8)
        for f in self.flyers[:]:
            f[1] += dt
            if f[1] > 0.7:
                self.flyers.remove(f)
        for sh in self.shots[:]:
            sh["t"] += dt
            dur = 0.7 if sh["kind"] == "super" else 0.55
            if sh["t"] >= dur:
                self.shots.remove(sh)
                if sh["kind"] in ("pencil", "super"):
                    self.doc_hp = max(0, self.doc_hp - sh["dmg"])
                    self.doc_hit = 0.5
                    self.shake = 22 if sh["kind"] == "super" else 10
                    self.set_doc(random.choice(DOC_HURT))
                    self.snd.play("hit")
                    big = sh["kind"] == "super"
                    self.burst(VILLAIN_X, CHAR_Y - 40, [YELLOW, ORANGE, WHITE, PINK, GOLD], 60 if big else 24,
                               500 if big else 300)
                    self.popups.append([f"-{sh['dmg']}", VILLAIN_X, CHAR_Y - 140, 1.0, RED])
                    if self.doc_hp <= 0:
                        self.burst(VILLAIN_X, CHAR_Y - 40, [LIME, YELLOW, RED, BLUE], 90, 550)
                        self.win_world()
                        return
                else:
                    self.hearts -= 1
                    self.hero_hit = 0.6
                    self.shake = 14
                    self.snd.play("goo")
                    self.burst(HERO_X, CHAR_Y - 40, [LIME, GREEN, (200, 255, 150)])
                    if self.hearts <= 0:
                        self.state = "gameover"
                        self.state_t = 0.0
                        self.snd.play("lose")
                        return
        self.phase_t += dt
        if self.phase == "erase" and self.phase_t > 1.3:
            self.phase = "solve"
            self.idle_t = 0
            self.set_hero("עכשיו נפתור נכון! מתחילים מהאחדות")
            self.set_doc("נראה אותך! חה-חה!")
        if self.done_t >= 0:
            self.done_t += dt
            if self.done_t > 1.8 and not self.shots:
                self.new_problem()

    # ------------------------------------------------------------ ציור: לוח
    def draw_board(self, s):
        board = pygame.Rect(330, 92, 440, 420)
        rounded(s, board, WHITE, 24)
        head = pygame.Rect(board.x + 4, board.y + 4, board.w - 8, 50)
        pygame.draw.rect(s, (230, 240, 255), head, border_top_left_radius=20, border_top_right_radius=20)
        msg = {"find": "איפה דוקטור טעות טעה? לחצו על הספרה",
               "erase": "מוחקים את הטעות...",
               "solve": "פותרים נכון! בחרו תשובה או לווים מהשכן"}[self.phase]
        if self.done_t >= 0:
            msg = "פתרתם נכון! כל הכבוד!"
        text(s, msg, 22, NAVY, head.center)
        y_small, y_top, y_bot, y_line, y_ans = 182, 238, 308, 350, 400
        if self.phase == "solve" and self.done_t < 0 and self.col >= 0:
            pulse = (math.sin(self.time * 5) + 1) / 2
            hl = pygame.Surface((70, 300), pygame.SRCALPHA)
            pygame.draw.rect(hl, (255, 210, 60, int(60 + 50 * pulse)), hl.get_rect(), border_radius=16)
            pygame.draw.rect(hl, (240, 160, 20, 220), hl.get_rect(), 3, border_radius=16)
            s.blit(hl, (COLS_X[self.col] - 35, 150))
        self.digit_rects = {}
        for i in range(3):
            if not self.show[i]:
                continue
            x = COLS_X[i]
            r = text(s, str(self.orig[i]), 60, INK, (x, y_top))
            if self.top[i] != self.orig[i] and self.time >= self.top_t[i]:
                age = self.time - self.top_t[i]
                thick(s, RED, (r.left + 4, r.bottom - 12), (r.right - 4, r.top + 12), 4)
                tag = render(str(self.top[i]), 28, WHITE).get_rect(center=(x, y_small)).inflate(16, 2)
                pygame.draw.rect(s, INK, tag.inflate(4, 4), border_radius=12)
                pygame.draw.rect(s, ORANGE, tag, border_radius=10)
                text(s, str(self.top[i]), 28, WHITE, (x, y_small), scale=1 + 0.5 * max(0, 1 - age * 4))
            if self.b >= 100 or i > 0:
                text(s, str(self.bot[i]), 60, INK, (x, y_bot))
            if self.phase in ("find", "erase"):
                wd = digits(self.wrong)
                if not (i == 0 and wd[0] == 0 and digits(self.correct)[0] == 0):
                    alpha = 255 if self.phase == "find" else int(255 * max(0, 1 - self.phase_t / 1.0))
                    rr = text(s, str(wd[i]), 60, RED, (x, y_ans), alpha=alpha)
                    hit = rr.inflate(26, 16)
                    self.digit_rects[i] = hit
                    if self.phase == "find" and i not in self.marks and hit.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(s, RED, hit, 3, border_radius=10)
                    mark = self.marks.get(i)
                    if mark == "x" and alpha > 0:
                        thick(s, INK, (x - 26, y_ans - 26), (x + 26, y_ans + 26), 7)
                        thick(s, INK, (x - 26, y_ans + 26), (x + 26, y_ans - 26), 7)
                    elif mark == "ok" and alpha > 0:
                        thick(s, GREEN, (x - 20, y_ans + 18), (x - 6, y_ans + 30), 5)
                        thick(s, GREEN, (x - 6, y_ans + 30), (x + 18, y_ans + 8), 5)
            else:
                if self.ans[i] is not None:
                    age = self.time - self.ans_t[i]
                    text(s, str(self.ans[i]), 60, GREEN, (x, y_ans), scale=1 + 0.6 * max(0, 1 - age * 4))
                elif i == self.col and self.done_t < 0:
                    text(s, "?", 56, (230, 170, 40), (x, y_ans + math.sin(self.time * 4) * 3))
        if self.phase == "erase":
            ex = COLS_X[0] - 40 + (COLS_X[2] - COLS_X[0] + 80) * min(1, self.phase_t / 1.0)
            rounded(s, (ex - 24, y_ans - 20, 48, 34), PINK, 8, bw=3, shadow=False)
            pygame.draw.rect(s, BLUE, (ex - 24, y_ans - 20, 48, 12), border_top_left_radius=8, border_top_right_radius=8)
        text(s, "−", 60, INK, (400, y_bot))
        thick(s, INK, (380, y_line), (690, y_line), 5)
        for f in self.flyers:
            if f[1] < 0:
                continue
            t = min(1, f[1] / 0.6)
            e = 1 - (1 - t) ** 3
            x = f[0] + 80 * e
            y = y_top - 10 + (y_small - y_top + 10) * e - math.sin(t * math.pi) * 50
            text(s, "10", 32, ORANGE, (x, y), outline=WHITE, ow=3)

    def draw_controls(self, s):
        mouse = pygame.mouse.get_pos()
        down = pygame.mouse.get_pressed()[0]
        active = self.phase == "solve" and self.done_t < 0
        br = pygame.Rect(410, 530, 280, 56)
        hint_borrow = active and self.world == 0 and self.need_borrow() and self.idle_t > 6
        button(s, br, ORANGE, "לווים מהשכן - רווח", 26, hover=br.collidepoint(mouse),
               pressed=down and br.collidepoint(mouse), enabled=active,
               glow=(math.sin(self.time * 6) + 1) / 2 if hint_borrow else 0)
        self.buttons["borrow"] = br
        for d in range(10):
            r = pygame.Rect(self.pad_x[d], 612, 52, 58)
            button(s, r, BLUE, str(d), 32, hover=r.collidepoint(mouse), pressed=down and r.collidepoint(mouse),
                   enabled=active)
            self.buttons[d] = r
        # מד עיפרון-על
        sr = pygame.Rect(812, 612, 270, 58)
        ready = self.super >= SUPER_MAX
        if ready:
            button(s, sr, GOLD, "עיפרון-על! - S", 26, hover=sr.collidepoint(mouse),
                   glow=(math.sin(self.time * 6) + 1) / 2)
            self.buttons["super"] = sr
        else:
            rounded(s, sr, WHITE, 16, bw=3)
            text(s, "עיפרון-על", 18, INK, (sr.centerx, sr.y + 15))
            for k in range(SUPER_MAX):
                seg = pygame.Rect(sr.x + 18 + k * 60, sr.y + 30, 52, 16)
                pygame.draw.rect(s, GOLD if k < self.super else (225, 220, 210), seg, border_radius=8)
                pygame.draw.rect(s, INK, seg, 2, border_radius=8)
            self.buttons.pop("super", None)
        # רמז: יד שמצביעה על הכפתור
        if hint_borrow:
            hx, hy = br.right + 30, br.centery + 6 + math.sin(self.time * 8) * 6
            outlined_circle(s, (255, 220, 190), hx + 10, hy, 16, 3)
            thick(s, INK, (hx - 4, hy), (hx - 28, hy - 6), 12)
            thick(s, (255, 220, 190), (hx - 4, hy), (hx - 28, hy - 6), 7)

    def draw_hud(self, s):
        bar_bg = pygame.Surface((W, 76), pygame.SRCALPHA)
        bar_bg.fill((255, 255, 255, 160))
        s.blit(bar_bg, (0, 0))
        title_row(s, 36, 34, 22, center_x=W / 2 + 20)
        for k in range(5):
            heart(s, W - 34 - k * 40, 26, 14, RED if k < self.hearts else (215, 210, 200))
        bar = pygame.Rect(24, 16, 200, 24)
        pygame.draw.rect(s, INK, bar.inflate(6, 6), border_radius=12)
        pygame.draw.rect(s, (230, 220, 210), bar, border_radius=10)
        frac = self.doc_hp / self.doc_max
        if frac > 0:
            pygame.draw.rect(s, LIME, (bar.x, bar.y, bar.w * frac, bar.h), border_radius=10)
        text(s, f"{self.doc_hp}/{self.doc_max}", 18, INK, bar.center)
        text(s, f"{WORLDS[self.world]['name']} - שלב {self.world + 1}", 18, NAVY, (bar.centerx, 58))
        text(s, f"ניקוד {self.score}", 20, ORANGE, (W - 115, 58))
        for label, cx, col in (("הגיבור: קפטן מאונך - פיל-על", HERO_X, YELLOW),
                               ("הנבל: דוקטור טעות", VILLAIN_X, LIME)):
            img = render(label, 18, INK)
            r = img.get_rect(center=(cx, 582)).inflate(24, 12)
            rounded(s, r, col, 14, bw=3)
            s.blit(img, img.get_rect(center=r.center))
        mr = pygame.Rect(24, 640, 120, 44)
        m = pygame.mouse.get_pos()
        button(s, mr, (120, 120, 160), "למפה", 22, hover=mr.collidepoint(m))
        self.buttons["map"] = mr

    def draw_shots(self, s):
        for sh in self.shots:
            if sh["t"] < 0:
                continue
            dur = 0.7 if sh["kind"] == "super" else 0.55
            t = min(1, sh["t"] / dur)
            if sh["kind"] in ("pencil", "super"):
                x0, y0, x1, y1 = sh["x"], sh["y"], VILLAIN_X + 40, CHAR_Y - 40
            else:
                x0, y0, x1, y1 = sh["x"], sh["y"], HERO_X - 40, CHAR_Y - 40
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t - math.sin(t * math.pi) * (220 if sh["kind"] == "super" else 160)
            if sh["kind"] in ("pencil", "super"):
                big = 2.2 if sh["kind"] == "super" else 1.0
                if big > 1:
                    soft_glow(s, x, y, 90, GOLD, 90)
                    for k in range(6):
                        tt = max(0, t - k * 0.04)
                        tx = x0 + (x1 - x0) * tt
                        ty = y0 + (y1 - y0) * tt - math.sin(tt * math.pi) * 220
                        star(s, tx, ty, 10 - k, WHITE, self.time * 5 + k)
                ang = self.time * 20
                c, sn = math.cos(ang), math.sin(ang)

                def rot(px, py):
                    return x + (c * px - sn * py) * big, y + (sn * px + c * py) * big
                poly(s, INK, [rot(-30, -9), rot(22, -9), rot(38, 0), rot(22, 9), rot(-30, 9)])
                poly(s, GOLD if big > 1 else YELLOW, [rot(-26, -6), rot(20, -6), rot(20, 6), rot(-26, 6)])
                poly(s, PINK, [rot(-28, -6), rot(-18, -6), rot(-18, 6), rot(-28, 6)])
                poly(s, (240, 210, 160), [rot(20, -6), rot(34, 0), rot(20, 6)])
            else:
                wob = 1 + 0.15 * math.sin(self.time * 30)
                outlined_ellipse(s, (120, 220, 60), x, y, 22 * wob, 18 / wob, 3)
                circle(s, (190, 250, 140), x - 7, y - 6, 6)

    def draw_particles(self, s):
        for x, y, _, _, life, col, rot, shape in self.particles:
            size = 7 * min(1, life / 0.4) + 1
            if shape:
                star(s, x, y, size + 2, col, rot)
            else:
                circle(s, col, x, y, size * 0.8)
        for t, x, y, life, col in self.popups:
            text(s, t, 44, col, (x, y), outline=WHITE, ow=3, alpha=int(255 * min(1, life / 0.4)))

    def bubble_pop(self, since):
        a = min(1, (self.time - since) / 0.18)
        return 0.75 + 0.25 * (1 - (1 - a) ** 3) + 0.05 * math.sin(a * math.pi)

    def draw_play(self, s):
        s.blit(self.bg, (0, 0))
        boss = 1.12 if self.world == 4 else 1.0
        draw_doctor(s, VILLAIN_X, CHAR_Y, self.time, self.doc_hit, self.doc_laugh, boss, self.world)
        draw_captain(s, HERO_X, CHAR_Y, self.time, self.hero_hit, self.hero_cheer,
                     power=max(self.hero_power, 0.6 if self.super >= SUPER_MAX else 0))
        self.draw_board(s)
        self.draw_controls(s)
        self.draw_hud(s)
        bubble(s, self.doc_say, (16, 92, 296, 80), (VILLAIN_X + 30, 215), (225, 250, 215), 20,
               pop=self.bubble_pop(self.doc_say_t))
        bubble(s, self.hero_say, (788, 92, 296, 80), (HERO_X - 40, 215), WHITE, 20,
               pop=self.bubble_pop(self.hero_say_t))
        self.draw_shots(s)
        self.draw_particles(s)
        if self.hero_hit > 0:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((120, 220, 60, int(70 * self.hero_hit)))
            s.blit(ov, (0, 0))

    # ------------------------------------------------------------ מסכים נוספים
    def overlay(self, s, alpha=130):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((40, 30, 20, alpha))
        s.blit(ov, (0, 0))

    def draw_levelwin(self, s):
        self.draw_play(s)
        self.overlay(s)
        box = pygame.Rect(W / 2 - 310, 120, 620, 470)
        rounded(s, box, CREAM, 28, bw=5)
        text(s, "ניצחת את דוקטור טעות!", 46, BLUE, (box.centerx, box.y + 60), outline=WHITE, ow=4)
        text(s, f"{WORLDS[self.world]['name']} שוחררה מהטעויות!", 26, INK, (box.centerx, box.y + 115))
        for k in range(3):
            x = box.centerx - 100 + k * 100
            appear = self.state_t - 0.5 - k * 0.45
            if k < self.earned and appear > 0:
                sc = 1 + 0.6 * max(0, 1 - appear * 4)
                star(s, x, 300, 38 * sc, GOLD, 0, outline=True)
                circle(s, mix(GOLD, WHITE, 0.6), x - 10 * sc, 288, 6 * sc)
            else:
                star(s, x, 300, 38, (225, 218, 200), 0, outline=True)
        text(s, f"ניקוד: {self.score}    טעויות: {self.mistakes}", 26, INK, (box.centerx, box.y + 265))
        tip = "מושלם! בלי כמעט אף טעות!" if self.earned == 3 else "נסו שוב לשלושה כוכבים - עם פחות טעויות"
        text(s, tip, 22, (110, 100, 90), (box.centerx, box.y + 305), bold=False)
        m = pygame.mouse.get_pos()
        self.buttons = {}
        b1 = pygame.Rect(box.x + 50, box.bottom - 110, 240, 70)
        button(s, b1, (120, 120, 160), "למפה", 30, hover=b1.collidepoint(m))
        self.buttons["map"] = b1
        b2 = pygame.Rect(box.right - 290, box.bottom - 110, 240, 70)
        last = self.world == 4
        button(s, b2, GOLD if last else GREEN, "לתעודה!" if last else "לשלב הבא", 30, hover=b2.collidepoint(m))
        self.buttons["next"] = b2

    def draw_gameover(self, s):
        self.draw_play(s)
        self.overlay(s)
        box = pygame.Rect(W / 2 - 300, 150, 600, 420)
        rounded(s, box, CREAM, 28, bw=5)
        text(s, "דוקטור טעות ניצח הפעם", 44, GREEN, (box.centerx, box.y + 70), outline=WHITE, ow=4)
        draw_doctor(s, box.centerx, box.y + 200, self.time, laugh=1.0, sc=0.55, world=self.world)
        text(s, "זכרו: מתחילים מהאחדות, ואם אין מספיק - לווים!", 22, INK, (box.centerx, box.y + 300))
        m = pygame.mouse.get_pos()
        self.buttons = {}
        b1 = pygame.Rect(box.x + 50, box.bottom - 100, 230, 70)
        button(s, b1, (120, 120, 160), "למפה", 30, hover=b1.collidepoint(m))
        self.buttons["map"] = b1
        b2 = pygame.Rect(box.right - 280, box.bottom - 100, 230, 70)
        button(s, b2, ORANGE, "עוד פעם!", 30, hover=b2.collidepoint(m))
        self.buttons["retry"] = b2

    def draw_map(self, s):
        s.blit(self.map_bg, (0, 0))
        title_row(s, 52, 50, 28)
        text(s, "מפת ההרפתקה - בחרו עולם", 26, NAVY, (W / 2, 108), outline=WHITE, ow=2)
        m = pygame.mouse.get_pos()
        self.buttons = {}
        current = max(i for i in range(5) if self.unlocked(i))
        for i, (x, y) in enumerate(self.NODES):
            unlocked = self.unlocked(i)
            r = 48
            hover = unlocked and math.hypot(m[0] - x, m[1] - y) < r
            sc = 1.1 if hover else 1.0
            col = [ORANGE, GREEN, PURPLE, RED, (120, 60, 160)][i] if unlocked else (180, 180, 190)
            outlined_circle(s, mix(col, (0, 0, 0), 0.2), x, y + 6, r * sc, 4)
            outlined_circle(s, col, x, y, r * sc, 4)
            circle(s, mix(col, WHITE, 0.35), x - 14 * sc, y - 16 * sc, 10 * sc)
            if unlocked:
                text(s, str(i + 1), int(40 * sc), WHITE, (x, y), outline=mix(col, (0, 0, 0), 0.4), ow=3)
            else:     # מנעול
                pygame.draw.arc(s, INK, (x - 14, y - 26, 28, 30), 0, math.pi, 5)
                rounded(s, (x - 18, y - 10, 36, 28), (120, 120, 130), 6, bw=3, shadow=False)
            label = WORLDS[i]["name"] if i < 4 else "המעבדה - קרב הבוס"
            lr = render(label, 20, INK).get_rect(center=(x, y - 72)).inflate(20, 8)
            rounded(s, lr, WHITE, 12, bw=3, shadow=False)
            text(s, label, 20, INK, lr.center)
            for k in range(3):
                star(s, x - 30 + k * 30, y + 70, 12, GOLD if k < self.save["stars"][i] else (215, 210, 195), 0,
                     outline=True)
            if unlocked:
                self.buttons[f"world{i}"] = pygame.Rect(x - r, y - r, r * 2, r * 2)
        hx, hy = self.NODES[current]
        draw_captain(s, hx + 95, hy - 20, self.time, sc=0.42)
        bx, by = self.NODES[4]
        if current < 4:
            draw_doctor(s, bx + 95, by + 20, self.time, laugh=0.5, sc=0.42, world=4)
        total = sum(self.save["stars"])
        text(s, f"כוכבים: {total}/15", 24, ORANGE, (W - 110, 160), outline=WHITE, ow=2)
        b1 = pygame.Rect(30, 640, 170, 54)
        button(s, b1, (120, 120, 160), "הסיפור", 24, hover=b1.collidepoint(m))
        self.buttons["story"] = b1
        b2 = pygame.Rect(215, 640, 200, 54)
        button(s, b2, (90, 160, 200), "מוזיקה: " + ("פועלת" if self.snd.music_on else "כבויה"), 22,
               hover=b2.collidepoint(m))
        self.buttons["music"] = b2

    def draw_intro(self, s):
        s.blit(self.map_bg, (0, 0))
        page = self.story_page
        cap, who = STORY[page]
        panel = pygame.Rect(90, 70, W - 180, 430)
        rounded(s, panel, CREAM, 26, bw=5)
        inner = panel.inflate(-24, -24)
        pygame.draw.rect(s, (230, 240, 255) if who != "doctor" else (225, 245, 215), inner, border_radius=18)
        if who == "hero":
            draw_captain(s, panel.centerx, panel.y + 220, self.time, cheer=0.4 if int(self.time) % 2 else 0, sc=1.0)
            for k in range(6):
                a = self.time * 0.8 + k
                text(s, str((k * 3 + 1) % 10), 34, [BLUE, GREEN, ORANGE][k % 3],
                     (panel.centerx + math.cos(a) * 250, panel.y + 200 + math.sin(a * 1.3) * 120), outline=WHITE)
        elif who == "doctor":
            draw_doctor(s, panel.centerx, panel.y + 220, self.time, laugh=1.0, sc=1.0)
            for k in range(6):
                a = self.time * 1.6 + k
                text(s, random.Random(k).choice(["2+2=22", "9-3=7", "5-8=3", "10-1=0"]), 26, RED,
                     (panel.centerx + math.cos(a) * 270, panel.y + 200 + math.sin(a * 1.1) * 130), outline=WHITE)
        else:
            draw_doctor(s, panel.x + 220, panel.y + 220, self.time, laugh=0.5)
            draw_captain(s, panel.right - 220, panel.y + 220, self.time, cheer=0.3)
            pulse = 1 + 0.08 * math.sin(self.time * 5)
            outlined_circle(s, RED, panel.centerx, panel.y + 200, 46 * pulse, 5)
            text(s, "VS", 40, WHITE, (panel.centerx, panel.y + 200), outline=mix(RED, (0, 0, 0), 0.4), ow=2)
        cap_box = pygame.Rect(140, 520, W - 280, 80)
        rounded(s, cap_box, WHITE, 20, bw=4)
        lines = wrap(cap, 24, cap_box.w - 40)
        for k, ln in enumerate(lines):
            text(s, ln, 24, INK, (cap_box.centerx, cap_box.y + 40 + (k - (len(lines) - 1) / 2) * 32))
        for k in range(len(STORY)):
            circle(s, NAVY if k == page else (200, 200, 210), W / 2 - 30 + k * 30, 625, 8)
        m = pygame.mouse.get_pos()
        self.buttons = {}
        b = pygame.Rect(W / 2 - 120, 645, 240, 60)
        button(s, b, GREEN, "יוצאים לקרב!" if page == len(STORY) - 1 else "המשך", 28, hover=b.collidepoint(m))
        self.buttons["next_page"] = b
        sk = pygame.Rect(W - 170, 655, 140, 46)
        button(s, sk, (150, 150, 170), "דלגו", 22, hover=sk.collidepoint(m))
        self.buttons["skip"] = sk

    def draw_ending(self, s):
        s.blit(self.map_bg, (0, 0))
        for k in range(14):
            a = self.time * 0.5 + k
            star(s, W / 2 + math.cos(a) * 480, 360 + math.sin(a * 1.3) * 300, 10, [GOLD, PINK, BLUE][k % 3], a)
        cert = pygame.Rect(150, 60, W - 300, 560)
        rounded(s, cert, (255, 250, 230), 20, border=GOLD, bw=10)
        pygame.draw.rect(s, (220, 180, 80), cert.inflate(-36, -36), 3, border_radius=14)
        text(s, "תעודת אלוף המאונך", 52, NAVY, (cert.centerx, cert.y + 75), outline=WHITE, ow=3)
        text(s, "על ניצחון על דוקטור טעות בכל חמשת העולמות", 26, INK, (cert.centerx, cert.y + 140))
        text(s, "ועל פריטה מושלמת - עמודה אחרי עמודה!", 26, INK, (cert.centerx, cert.y + 178))
        draw_captain(s, cert.centerx, cert.y + 330, self.time, cheer=0.5, sc=0.8)
        total = sum(self.save["stars"])
        text(s, f"כוכבים שנאספו: {total}/15", 28, ORANGE, (cert.centerx, cert.y + 470), outline=WHITE, ow=2)
        text(s, "חתימה: קפטן מאונך", 20, (120, 110, 90), (cert.right - 140, cert.bottom - 40), bold=False)
        outlined_circle(s, RED, cert.x + 100, cert.bottom - 90, 44, 4)
        star(s, cert.x + 100, cert.bottom - 90, 30, GOLD, 0)
        m = pygame.mouse.get_pos()
        self.buttons = {}
        b = pygame.Rect(W / 2 - 110, 645, 220, 60)
        button(s, b, GREEN, "למפה", 28, hover=b.collidepoint(m))
        self.buttons["map"] = b

    def draw(self):
        s = self.canvas
        self.buttons = {}
        if self.state == "intro":
            self.draw_intro(s)
        elif self.state == "map":
            self.draw_map(s)
        elif self.state == "play":
            self.draw_play(s)
        elif self.state == "levelwin":
            self.draw_levelwin(s)
        elif self.state == "gameover":
            self.draw_gameover(s)
        elif self.state == "ending":
            self.draw_ending(s)
        if self.state not in ("play", "levelwin", "gameover"):
            self.draw_particles(s)
        if self.flash > 0:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 245, 200, int(400 * self.flash)))
            s.blit(ov, (0, 0))
        self.screen.fill((0, 0, 0))
        self.screen.blit(s, (random.uniform(-1, 1) * self.shake, random.uniform(-1, 1) * self.shake))

    # ------------------------------------------------------------ קלט
    def press(self, key):
        self.snd.play("click")
        if key == "next_page":
            self.snd.play("page")
            if self.story_page < len(STORY) - 1:
                self.story_page += 1
            else:
                self.finish_intro()
        elif key == "skip":
            self.finish_intro()
        elif key == "story":
            self.story_page = 0
            self.state = "intro"
        elif key == "music":
            self.snd.toggle_music()
        elif key.startswith("world"):
            self.start_world(int(key[5:]))
        elif key == "map":
            self.state = "map"
        elif key == "retry":
            self.start_world(self.world)
        elif key == "next":
            if self.world == 4:
                self.state = "ending"
                self.snd.play("win")
            else:
                self.start_world(self.world + 1)
        elif key == "borrow":
            self.borrow()
        elif key == "super":
            self.use_super()

    def finish_intro(self):
        self.save["seen_intro"] = True
        write_save(self.save)
        self.state = "map"

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_m:
                self.snd.toggle_music()
            elif e.key == pygame.K_ESCAPE:
                if self.state == "map":
                    return False
                self.state = "map"
            elif self.state == "intro" and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.press("next_page")
            elif self.state == "levelwin" and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.press("next")
            elif self.state == "gameover" and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.press("retry")
            elif self.state == "play":
                if e.key in (pygame.K_SPACE, pygame.K_UP):
                    self.borrow()
                elif e.key == pygame.K_s:
                    self.use_super()
                elif e.unicode and e.unicode.isdigit():
                    self.answer(int(e.unicode))
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if self.state == "play" and self.phase == "find":
                for i, r in getattr(self, "digit_rects", {}).items():
                    if r.collidepoint(e.pos):
                        self.click_wrong_digit(i)
                        return True
            for k, r in list(self.buttons.items()):
                if r.collidepoint(e.pos):
                    if isinstance(k, int):
                        if self.state == "play":
                            self.answer(k)
                    else:
                        self.press(k)
                    break
        return True

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT or not self.handle(e):
                    running = False
            self.update(dt)
            self.draw()
            pygame.display.flip()


def main():
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption("קפטן מאונך נגד דוקטור טעות")
    screen = pygame.display.set_mode((W, H))
    Game(screen).run()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()