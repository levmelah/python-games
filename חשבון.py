# -*- coding: utf-8 -*-
"""
תופסים את התשובה! - משחק חיסור במאונך עם פריטה

הפעלה:
    pip install pygame python-bidi
    python catch_subtraction.py

איך משחקים:
    התרגיל כתוב במחברת. פותרים עמודה אחרי עמודה - מתחילים באחדות.
    בלונים עם ספרות נופלים מלמעלה. זזים עם החצים או עם העכבר ותופסים
    את הספרה הנכונה לעמודה המסומנת. מתחמקים מהספרות הלא נכונות.
    אם הספרה למעלה קטנה מהספרה למטה - קודם לוחצים רווח (או על הכפתור) כדי לפרוט!
"""
import math
import random
import re
import sys
from functools import lru_cache

import pygame
import pygame.gfxdraw as gfx

W, H = 1000, 720
FPS = 60
FIELD_X = 370                      # מכאן מתחיל שטח המשחק
GROUND_Y = 668
CATCH_Y = 608
CATCH_W = 124

# ---------------------------------------------------------------- צבעים
WHITE = (255, 255, 255)
INK = (230, 238, 255)          # טקסט בהיר על לוחות כהים
INK_SOFT = (150, 165, 215)
RED = (255, 80, 100)
GREEN = (70, 240, 150)
ORANGE = (255, 150, 40)
YELLOW = (255, 220, 70)
CYAN = (80, 230, 255)
PANEL = (22, 26, 62)
PANEL_EDGE = (90, 120, 255)
SPACE_TOP = (6, 6, 24)
SPACE_BOTTOM = (34, 16, 70)
BALLOON_COLS = [(255, 90, 110), (255, 160, 40), (80, 230, 140), (80, 170, 255),
                (190, 120, 255), (255, 110, 200), (60, 225, 235)]


# ---------------------------------------------------------------- עברית
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
    w, h = base.get_width() + width * 2, base.get_height() + width * 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx * dx + dy * dy <= width * width + 1:
                surf.blit(ol, (dx + width, dy + width))
    surf.blit(base, (width, width))
    return surf


def text(surf, s, size, color, center, bold=True, outline=None, ow=3, scale=1.0, alpha=255):
    img = render_outlined(s, size, tuple(color), tuple(outline), ow, bold) if outline else \
        render(s, size, tuple(color), bold)
    if scale != 1.0:
        img = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * scale)),
                                                 max(1, int(img.get_height() * scale))))
    if alpha < 255:
        img = img.copy()
        img.set_alpha(alpha)
    r = img.get_rect(center=(int(center[0]), int(center[1])))
    surf.blit(img, r)
    return r


# ---------------------------------------------------------------- ציור רך
def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def aa_circle(s, col, x, y, r):
    x, y, r = int(x), int(y), int(r)
    if r < 1:
        return
    gfx.filled_circle(s, x, y, r, col)
    gfx.aacircle(s, x, y, r, col)


def aa_ellipse(s, col, x, y, rx, ry):
    x, y, rx, ry = int(x), int(y), int(rx), int(ry)
    if rx < 1 or ry < 1:
        return
    gfx.filled_ellipse(s, x, y, rx, ry, col)
    gfx.aaellipse(s, x, y, rx, ry, col)


def aa_poly(s, col, pts):
    pts = [(int(x), int(y)) for x, y in pts]
    gfx.filled_polygon(s, pts, col)
    gfx.aapolygon(s, pts, col)


def thick_line(s, col, a, b, w):
    pygame.draw.line(s, col, a, b, w)
    aa_circle(s, col, a[0], a[1], w / 2)
    aa_circle(s, col, b[0], b[1], w / 2)


@lru_cache(maxsize=64)
def shadow_surface(w, h, radius, strength):
    pad = 18
    s = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    for k in range(8, 0, -1):
        a = int(strength * (1 - k / 9) / 2.2)
        pygame.draw.rect(s, (20, 30, 70, a), (pad - k, pad - k + 6, w + k * 2, h + k * 2),
                         border_radius=radius + k)
    return s


@lru_cache(maxsize=64)
def glow_surface(w, h, radius, col):
    pad = 16
    s = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    for k in range(12, 0, -2):
        pygame.draw.rect(s, (*col, int(10 + 8 * (12 - k) / 2)), (pad - k, pad - k, w + k * 2, h + k * 2),
                         border_radius=radius + k)
    return s


def card(s, rect, col=PANEL, radius=20, border=PANEL_EDGE, bw=3, shadow=60, alpha=235):
    """לוח חללי: רקע כהה שקוף-למחצה עם מסגרת ניאון זוהרת."""
    rect = pygame.Rect(rect)
    if shadow:
        s.blit(shadow_surface(rect.w, rect.h, radius, shadow), (rect.x - 18, rect.y - 18))
    if border:
        s.blit(glow_surface(rect.w, rect.h, radius, border), (rect.x - 16, rect.y - 16))
    body = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(body, (*col, alpha), body.get_rect(), border_radius=radius)
    s.blit(body, rect.topleft)
    if border:
        pygame.draw.rect(s, border, rect, bw, border_radius=radius)


def button3d(s, rect, col, label, size=30, pressed=False, hover=False):
    rect = pygame.Rect(rect)
    depth = 2 if pressed else 7
    dark = mix(col, (0, 0, 0), 0.3)
    top = mix(col, WHITE, 0.15) if hover else col
    s.blit(glow_surface(rect.w, rect.h, 18, col), (rect.x - 16, rect.y - 13))
    card(s, rect.move(0, 7), dark, radius=18, shadow=50, border=None, alpha=255)
    face = rect.move(0, 7 - depth)
    pygame.draw.rect(s, top, face, border_radius=18)
    pygame.draw.rect(s, mix(top, WHITE, 0.35), (face.x + 10, face.y + 6, face.w - 20, face.h * 0.32),
                     border_radius=12)
    text(s, label, size, WHITE, face.center, outline=dark, ow=2)
    return rect


def draw_heart(s, x, y, size, col=RED):
    r = size * 0.55
    aa_circle(s, col, x - r * 0.95, y, r)
    aa_circle(s, col, x + r * 0.95, y, r)
    aa_poly(s, col, [(x - r * 1.9, y + r * 0.35), (x + r * 1.9, y + r * 0.35), (x, y + r * 2.5)])
    aa_circle(s, mix(col, WHITE, 0.6), x - r * 1.1, y - r * 0.25, r * 0.3)


def draw_star(s, x, y, r, col, rot=0.0):
    pts = []
    for k in range(10):
        a = rot + k * math.pi / 5 - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    aa_poly(s, col, pts)


def digits(n):
    return [n // 100, n // 10 % 10, n % 10]


# ---------------------------------------------------------------- תרגילים
def needs(a, b):
    ad, bd = digits(a), digits(b)
    u = ad[2] < bd[2]
    t = ad[1] - u < bd[1]
    return u, t


def make_problem(level):
    """כל תרגיל דורש פריטה.
       1-2: פריטה בדו-ספרתי  3: תלת-ספרתי, פריטה אחת
       4: פריטה כפולה  5+: גם אפס באמצע"""
    for _ in range(5000):
        if level <= 2:
            a = random.randint(21, 98)
            b = random.randint(11, a - 1)
        else:
            a = random.randint(102, 989)
            b = random.randint(11, a - 1)
        if b % 10 == 0:
            continue
        u, t = needs(a, b)
        ad = digits(a)
        if level <= 2 and u and not t:
            return a, b
        if level == 3 and (u != t):
            return a, b
        if level == 4 and u and t and ad[1] != 0:
            return a, b
        if level >= 5:
            if ad[1] == 0 and u and random.random() < 0.5:
                return a, b
            if u or t:
                return a, b
    return 403, 178


# ---------------------------------------------------------------- רקע
def soft_blob(surf, x, y, r, col, strength=40):
    blob = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    for k in range(r, 0, -4):
        gfx.filled_circle(blob, r, r, k, (*col, int(strength * (1 - k / r) ** 1.5)))
    surf.blit(blob, (x - r, y - r))


def build_background():
    bg = pygame.Surface((W, H))
    for y in range(H):
        pygame.draw.line(bg, mix(SPACE_TOP, SPACE_BOTTOM, (y / H) ** 1.3), (0, y), (W, y))
    rnd = random.Random(7)
    # ערפיליות
    for x, y, r, c in ((620, 220, 260, (140, 60, 220)), (900, 420, 220, (40, 120, 230)),
                       (450, 470, 200, (220, 60, 160)), (150, 120, 220, (60, 80, 220))):
        soft_blob(bg, x, y, r, c, 60)
    # כוכבים קבועים
    for _ in range(260):
        x, y = rnd.randint(0, W), rnd.randint(0, GROUND_Y)
        b = rnd.randint(90, 220)
        bg.set_at((x, y), (b, b, min(255, b + 30)))
    # כוכב לכת עם טבעת
    px, py, pr = 870, 150, 58
    soft_blob(bg, px, py, 110, (255, 160, 90), 35)
    ring_back = pygame.Surface((300, 120), pygame.SRCALPHA)
    pygame.draw.ellipse(ring_back, (240, 200, 150, 160), (20, 35, 260, 50), 6)
    bg.blit(ring_back, (px - 150, py - 60))
    aa_circle(bg, (230, 120, 70), px, py, pr)
    for k, c in enumerate([(245, 150, 90), (215, 105, 60), (250, 175, 110)]):
        band = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
        pygame.draw.circle(band, (*c, 255), (pr, pr), pr)
        mask = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 22 + k * 26, pr * 2, 12))
        band.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        bg.blit(band, (px - pr, py - pr))
    shade = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
    pygame.draw.circle(shade, (0, 0, 30, 110), (pr + 22, pr + 18), pr)
    m2 = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
    pygame.draw.circle(m2, (255, 255, 255, 255), (pr, pr), pr)
    shade.blit(m2, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    bg.blit(shade, (px - pr, py - pr))
    ring_front = pygame.Surface((300, 120), pygame.SRCALPHA)
    pygame.draw.arc(ring_front, (250, 215, 165, 230), (20, 35, 260, 50), math.pi, 2 * math.pi, 6)
    bg.blit(ring_front, (px - 150, py - 60))
    # ירח קטן
    aa_circle(bg, (190, 200, 230), 470, 90, 16)
    aa_circle(bg, (150, 160, 200), 476, 94, 13)
    # קרקע של ירח
    pts = [(0, H)]
    for x in range(0, W + 10, 10):
        pts.append((x, GROUND_Y - 14 - 10 * math.sin(x * 0.012) - 5 * math.sin(x * 0.041)))
    pts.append((W, H))
    aa_poly(bg, (120, 115, 150), pts)
    pts2 = [(x, y + 12) for x, y in pts[1:-1]]
    aa_poly(bg, (90, 85, 120), [(0, H)] + pts2 + [(W, H)])
    for _ in range(18):          # מכתשים
        x = rnd.randint(0, W)
        y = rnd.randint(GROUND_Y + 4, H - 10)
        r = rnd.randint(6, 18)
        aa_ellipse(bg, (70, 66, 98), x, y, r, r * 0.4)
        aa_ellipse(bg, (105, 100, 135), x, y + 2, r * 0.8, r * 0.3)
    return bg


def build_cloud(w):
    """אסטרואיד קטן שמרחף ברקע."""
    r = w // 6
    s = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
    rnd = random.Random(w)
    pts = []
    for k in range(11):
        a = k / 11 * math.tau
        rr = r * rnd.uniform(0.75, 1.0)
        pts.append((r + 3 + math.cos(a) * rr, r + 3 + math.sin(a) * rr))
    aa_poly(s, (95, 90, 120, 255), pts)
    aa_circle(s, (75, 70, 100, 255), r * 0.8, r * 0.9, r * 0.25)
    aa_circle(s, (75, 70, 100, 255), r * 1.4, r * 1.4, r * 0.18)
    return s


# ---------------------------------------------------------------- המשחק
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.time = 0.0
        self.state = "menu"
        self.catch_x = FIELD_X + (W - FIELD_X) / 2
        self.bg = build_background()
        self.clouds = [[random.uniform(0, W), random.uniform(160, 520), random.uniform(6, 16),
                        build_cloud(random.choice([110, 140, 170, 200]))] for _ in range(4)]
        self.twinkles = [(random.uniform(0, W), random.uniform(0, GROUND_Y - 40),
                          random.uniform(1, 4), random.random() * 6) for _ in range(55)]
        self.shooting = None
        self.menu_balloons = [self.make_menu_balloon(random.uniform(0, H)) for _ in range(12)]
        self.buttons = {}
        self.reset()

    def reset(self):
        self.score = 0
        self.shown_score = 0.0
        self.hearts = 3
        self.level = 1
        self.solved = 0
        self.streak = 0
        self.balloons = []
        self.particles = []
        self.popups = []
        self.flyers = []
        self.msg = ""
        self.msg_col = WHITE
        self.msg_t = 0.0
        self.msg_age = 0.0
        self.shake = 0.0
        self.squash = 0.0
        self.hurt = 0.0
        self.blink = 3.0

    def make_menu_balloon(self, y=None):
        return {"x": random.uniform(20, W - 20), "y": y if y is not None else -80,
                "v": random.uniform(30, 70), "d": random.randint(0, 9),
                "c": random.choice(BALLOON_COLS), "w": random.random() * 6, "s": random.uniform(0.6, 1.0)}

    # ------------------------------------------------------------ תרגיל חדש
    def new_problem(self, problem=None):
        self.a, self.b = problem or make_problem(self.level)
        self.orig = digits(self.a)
        self.top = digits(self.a)
        self.bot = digits(self.b)
        self.ans = [None, None, None]
        self.ans_t = [0.0, 0.0, 0.0]
        self.top_t = [-9.0, -9.0, -9.0]
        self.col = 2
        self.balloons.clear()
        self.spawn_t = 0.3
        self.done_t = -1
        self.state = "play"
        self.say("מתחילים באחדות!", INK)

    def say(self, s, col=WHITE, t=2.5):
        self.msg, self.msg_col, self.msg_t, self.msg_age = s, col, t, 0.0

    def need_borrow(self):
        return self.top[self.col] < self.bot[self.col]

    def correct_digit(self):
        return self.top[self.col] - self.bot[self.col]

    # ------------------------------------------------------------ פריטה
    def borrow(self):
        if self.state != "play" or self.done_t >= 0:
            return
        i = self.col
        if not self.need_borrow():
            self.say(f"לא צריך לפרוט: {self.top[i]} לא קטן מ-{self.bot[i]}", ORANGE)
            return
        j = i - 1
        delay = 0.0
        if self.top[j] == 0:                 # אפס באמצע - פורטים קודם מהמאות
            self.top[j - 1] -= 1
            self.top[j] += 10
            self.top_t[j - 1] = self.top_t[j] = self.time
            self.fly(j - 1, j)
            delay = 0.45
            self.say("אין עשרות! פורטים קודם מהמאות", ORANGE)
        else:
            self.say(f"פרטנו! עכשיו למעלה {self.top[i] + 10}", GREEN)
        self.top[j] -= 1
        self.top[i] += 10
        self.top_t[j] = self.top_t[i] = self.time + delay
        self.fly(j, i, delay)
        for b in self.balloons:
            self.pop(b, small=True)
        self.balloons.clear()
        self.spawn_t = 0.7

    def fly(self, src, dst, delay=0.0):
        self.flyers.append([self.col_x(src), 150, self.col_x(dst), 98, -delay])

    # ------------------------------------------------------------ תפיסה
    def caught(self, bal):
        d = bal["d"]
        i = self.col
        self.squash = 0.25
        if self.need_borrow():
            self.mistake(f"שכחת לפרוט! {self.top[i]} קטן מ-{self.bot[i]}", bal)
            return
        if d == self.correct_digit():
            self.ans[i] = d
            self.ans_t[i] = self.time
            self.streak += 1
            pts = 10 * self.streak
            self.score += pts
            self.pop(bal)
            self.popups.append([f"+{pts}", bal["x"], CATCH_Y - 40, 1.0, GREEN])
            self.say(["יופי!", "מעולה!", "כל הכבוד!", "אלופים!"][min(self.streak, 4) - 1], GREEN, 1.5)
            self.next_column()
        else:
            self.mistake(f"לא נכון. {self.top[i]} פחות {self.bot[i]} זה לא {d}", bal)

    def mistake(self, why, bal=None):
        self.hearts -= 1
        self.streak = 0
        self.shake = 14
        self.hurt = 0.6
        if bal:
            self.pop(bal, small=True)
        self.say(why, RED, 3)
        self.balloons.clear()
        self.spawn_t = 1.0
        if self.hearts <= 0:
            self.state = "gameover"

    def next_column(self):
        for b in self.balloons:
            self.pop(b, small=True)
        self.balloons.clear()
        self.spawn_t = 0.8
        self.col -= 1
        # לא כותבים אפסים בהתחלה של המספר
        if self.col >= 0 and all(self.top[k] == self.bot[k] for k in range(self.col + 1)):
            self.col = -1
        if self.col < 0 or (self.col == 0 and self.a < 100):
            self.done_t = 0
            self.solved += 1
            self.score += 50
            self.popups.append(["+50", FIELD_X + (W - FIELD_X) / 2, 300, 1.4, YELLOW])
            for _ in range(5):
                self.confetti(random.randint(FIELD_X + 40, W - 40), random.randint(150, 450), 30)
            self.say("פתרתם את התרגיל!", GREEN, 2)
            if self.solved % 3 == 0 and self.level < 6:
                self.level += 1
                self.popups.append([f"שלב {self.level}!", FIELD_X + (W - FIELD_X) / 2, 380, 1.8, ORANGE])
        else:
            self.say("עכשיו עמודת ה" + ["מאות", "עשרות"][self.col], INK, 2)

    # ------------------------------------------------------------ בלונים ואפקטים
    def spawn(self):
        good = self.correct_digit() if not self.need_borrow() else None
        r = random.random()
        if good is not None and r < 0.4:
            d = good
        elif self.need_borrow() and r < 0.3:
            d = abs(self.top[self.col] - self.bot[self.col])   # הטעות הנפוצה
        else:
            d = random.randint(0, 9)
        x = random.randint(FIELD_X + 45, W - 45)
        for _ in range(12):
            if all(abs(x - b["x"]) > 80 or b["y"] > 140 for b in self.balloons):
                break
            x = random.randint(FIELD_X + 45, W - 45)
        speed = 85 + self.level * 18 + random.random() * 30
        self.balloons.append({"x": x, "y": -60.0, "d": d, "v": speed,
                              "c": random.choice(BALLOON_COLS), "w": random.random() * 6, "s": 1.0})

    def pop(self, b, small=False):
        x, y = b["x"] + math.sin(b["w"]) * 6, b["y"]
        self.particles.append(["ring", x, y, 0.0, 0.35, b["c"]])
        self.confetti(x, y, 10 if small else 24, [b["c"], mix(b["c"], WHITE, 0.5)])

    def confetti(self, x, y, n, cols=None):
        for _ in range(n):
            a = random.random() * math.tau
            sp = random.uniform(80, 320)
            self.particles.append(["bit", x, y, math.cos(a) * sp, math.sin(a) * sp - 120,
                                   random.uniform(0.8, 1.4), random.choice(cols or BALLOON_COLS),
                                   random.random() * 6, random.uniform(-10, 10), random.choice([0, 1])])

    # ------------------------------------------------------------ עדכון
    def update(self, dt):
        self.time += dt
        self.msg_t -= dt
        self.msg_age += dt
        self.shake = max(0, self.shake - 50 * dt)
        self.squash = max(0, self.squash - dt)
        self.hurt = max(0, self.hurt - dt)
        self.blink -= dt
        if self.blink < -0.15:
            self.blink = random.uniform(2, 5)
        self.shown_score += (self.score - self.shown_score) * min(1, dt * 8)
        for c in self.clouds:
            c[0] += c[2] * dt
            if c[0] > W + 20:
                c[0] = -c[3].get_width()
        for p in self.particles[:]:
            if p[0] == "ring":
                p[3] += dt
                if p[3] > p[4]:
                    self.particles.remove(p)
                continue
            p[1] += p[3] * dt
            p[2] += p[4] * dt
            p[4] += 520 * dt
            p[3] *= 0.985
            p[5] -= dt
            p[7] += p[8] * dt
            if p[5] <= 0:
                self.particles.remove(p)
        for pu in self.popups[:]:
            pu[2] -= 50 * dt
            pu[3] -= dt
            if pu[3] <= 0:
                self.popups.remove(pu)
        for f in self.flyers[:]:
            f[4] += dt
            if f[4] > 0.7:
                self.flyers.remove(f)
        if self.state == "menu":
            for b in self.menu_balloons:
                b["y"] += b["v"] * dt
                b["w"] += dt * 2
                if b["y"] > GROUND_Y:
                    self.pop(b, small=True)
                    b.update(self.make_menu_balloon())
        if self.state != "play":
            return
        keys = pygame.key.get_pressed()
        sp = 540 * dt
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.catch_x -= sp
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.catch_x += sp
        self.catch_x = max(FIELD_X + CATCH_W / 2, min(W - CATCH_W / 2, self.catch_x))

        if self.done_t >= 0:
            self.done_t += dt
            if self.done_t > 1.9:
                self.new_problem()
            return

        self.spawn_t -= dt
        if self.spawn_t <= 0:
            self.spawn()
            self.spawn_t = max(0.55, 1.2 - self.level * 0.1)
        for b in self.balloons[:]:
            b["y"] += b["v"] * dt
            b["w"] += dt * 3
            if abs(b["x"] - self.catch_x) < CATCH_W / 2 + 18 and CATCH_Y - 34 < b["y"] < CATCH_Y + 10:
                self.balloons.remove(b)
                self.caught(b)
                return
            if b["y"] > GROUND_Y - 10:
                self.balloons.remove(b)
                self.pop(b, small=True)

    # ------------------------------------------------------------ ציור: עולם
    def col_x(self, i):
        return [150, 220, 290][i]

    def draw_world(self, s):
        s.blit(self.bg, (0, 0))
        for x, y, sz, ph in self.twinkles:         # כוכבים מנצנצים
            a = (math.sin(self.time * sz + ph) + 1) / 2
            if a > 0.25:
                c = mix((80, 90, 140), (255, 255, 255), a)
                r = 1 + a * 1.5
                pygame.draw.line(s, c, (x - r * 2, y), (x + r * 2, y), 1)
                pygame.draw.line(s, c, (x, y - r * 2), (x, y + r * 2), 1)
                aa_circle(s, c, x, y, r * 0.8)
        for x, y, _, img in self.clouds:
            s.blit(img, (x, y))
        # כוכב נופל
        if self.shooting is None and random.random() < 0.004:
            self.shooting = [random.uniform(200, W), random.uniform(0, 200), 0.0]
        if self.shooting:
            sx, sy, t = self.shooting
            self.shooting[2] += 1 / FPS
            hx, hy = sx - t * 700, sy + t * 350
            for k in range(14):
                c = mix((255, 255, 255), SPACE_TOP, k / 14)
                pygame.draw.line(s, c, (hx + k * 6, hy - k * 3), (hx + k * 6 + 6, hy - k * 3 - 3), 2)
            if t > 0.8:
                self.shooting = None

    def draw_balloon(self, s, b):
        """מטאור זוהר עם זנב אש - הספרה בתוכו."""
        sc = b.get("s", 1.0)
        x = b["x"] + math.sin(b["w"]) * 3
        y = b["y"]
        r = 32 * sc
        c = b["c"]
        up = b.get("up", False)                 # בתפריט המטאורים עולים
        tail_dir = 1 if up else -1
        # זנב
        for k in range(10, 0, -1):
            t = k / 10
            tr = r * (1 - t * 0.75)
            ty = y + tail_dir * t * r * 2.6
            tx = x + math.sin(self.time * 12 + k + b["w"]) * 3 * t
            col = mix(mix(c, (255, 240, 200), 0.3), SPACE_BOTTOM, t * 0.8)
            aa_circle(s, col, tx, ty, tr)
        soft_blob(s, x, y, int(r * 2), c, 70)
        # סלע
        aa_circle(s, mix(c, (0, 0, 0), 0.45), x, y, r)
        aa_circle(s, mix(c, (0, 0, 0), 0.2), x - 3 * sc, y - 3 * sc, r - 4 * sc)
        for dx, dy, cr in ((-12, 10, 6), (13, -6, 5), (8, 15, 4)):
            aa_circle(s, mix(c, (0, 0, 0), 0.4), x + dx * sc, y + dy * sc, cr * sc)
        aa_circle(s, mix(c, WHITE, 0.55), x - 12 * sc, y - 13 * sc, 5 * sc)
        text(s, str(b["d"]), int(42 * sc), WHITE, (x, y + 1), outline=mix(c, (0, 0, 0), 0.6), ow=3)

    def draw_catcher(self, s):
        """צלחת מעופפת עם חייזר וקרן משיכה."""
        x = self.catch_x
        sq = math.sin(self.squash / 0.25 * math.pi) if self.squash > 0 else 0
        hover = math.sin(self.time * 3) * 4
        w = CATCH_W * (1 + 0.1 * sq)
        cy = GROUND_Y - 44 + hover + sq * 6
        # צל על הירח
        sh = pygame.Surface((int(w + 30), 18), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 20, 90), sh.get_rect())
        s.blit(sh, (x - w / 2 - 15, GROUND_Y - 6))
        # קרן משיכה כלפי מעלה
        beam = pygame.Surface((int(w + 60), 150), pygame.SRCALPHA)
        bw = beam.get_width()
        pulse = 0.8 + 0.2 * math.sin(self.time * 6)
        for yy in range(150):            # קרן שדועכת כלפי מעלה
            t = yy / 150
            half = w * 0.28 + (bw / 2 - 4 - w * 0.28) * (1 - t)
            pygame.draw.line(beam, (140, 240, 255, int(80 * t * pulse)), (bw / 2 - half, yy), (bw / 2 + half, yy))
        for k in range(4):
            yy = (self.time * 120 + k * 40) % 150
            pygame.draw.line(beam, (*CYAN, 90), (bw / 2 - w * 0.3 - (150 - yy) * 0.2, yy),
                             (bw / 2 + w * 0.3 + (150 - yy) * 0.2, yy), 2)
        s.blit(beam, (x - bw / 2, cy - 30 - 150))
        hurt = self.hurt > 0
        hull = (170, 180, 210) if not hurt else mix((170, 180, 210), RED, math.sin(self.time * 30) * 0.5 + 0.5)
        # כיפה
        dome_r = w * 0.27
        aa_ellipse(s, (120, 200, 255), x, cy - 12, dome_r, dome_r * 0.95)
        # חייזר
        face = (120, 220, 110)
        aa_circle(s, face, x, cy - 14, dome_r * 0.62)
        for side in (-1, 1):
            pygame.draw.line(s, face, (x + side * 8, cy - 30), (x + side * 14, cy - 42), 3)
            aa_circle(s, (255, 230, 90), x + side * 14, cy - 43, 4)
            ex = x + side * 8
            if self.blink < 0:
                pygame.draw.line(s, (20, 40, 20), (ex - 5, cy - 16), (ex + 5, cy - 16), 3)
            else:
                look = self.nearest_balloon_dx() if self.state == "play" else 0
                aa_ellipse(s, (20, 20, 30), ex + look * 2, cy - 17, 5, 7)
                aa_circle(s, WHITE, ex + look * 2 + 2, cy - 19, 2)
        if hurt:
            pygame.draw.arc(s, (20, 50, 20), (x - 7, cy - 8, 14, 9), 0, math.pi, 2)
        else:
            pygame.draw.arc(s, (20, 50, 20), (x - 7, cy - 12, 14, 9), math.pi, 2 * math.pi, 2)
        glass = pygame.Surface((int(dome_r * 2), int(dome_r * 2)), pygame.SRCALPHA)
        pygame.draw.ellipse(glass, (255, 255, 255, 70), (dome_r * 0.25, dome_r * 0.15, dome_r * 0.5, dome_r * 0.6))
        s.blit(glass, (x - dome_r, cy - 12 - dome_r))
        # גוף הצלחת
        aa_ellipse(s, mix(hull, (0, 0, 0), 0.35), x, cy + 6, w / 2, 17)
        aa_ellipse(s, hull, x, cy + 1, w / 2, 15)
        aa_ellipse(s, mix(hull, WHITE, 0.4), x, cy - 3, w / 2 - 12, 6)
        for k in range(6):               # אורות מהבהבים
            lx = x - w / 2 + 14 + k * (w - 28) / 5
            on = int(self.time * 6 + k) % 3 == 0
            col = [YELLOW, CYAN, (255, 110, 200)][k % 3]
            aa_circle(s, col if on else mix(col, (0, 0, 0), 0.5), lx, cy + 6, 4)

    def nearest_balloon_dx(self):
        if not self.balloons:
            return 0
        b = max(self.balloons, key=lambda b: b["y"])
        return max(-1, min(1, (b["x"] - self.catch_x) / 120))

    # ------------------------------------------------------------ ציור: מחברת
    def draw_notebook(self, s):
        p = pygame.Rect(22, 22, 330, 340)
        card(s, p, PANEL, radius=18, shadow=70, border=CYAN)
        band = pygame.Rect(p.x + 3, p.y + 3, p.w - 6, 44)
        pygame.draw.rect(s, (40, 60, 150), band, border_top_left_radius=16, border_top_right_radius=16)
        text(s, "מחשב החללית", 24, CYAN, band.center)
        for k in (0, 1):                 # נורות סטטוס
            col = GREEN if int(self.time * 2 + k) % 2 else mix(GREEN, (0, 0, 0), 0.6)
            aa_circle(s, col, band.x + 20 + k * 18, band.centery, 5)
        for y in range(p.y + 80, p.bottom - 8, 34):       # רשת הולוגרמה
            pygame.draw.line(s, (40, 60, 120), (p.x + 10, y), (p.right - 10, y), 1)
        for x in range(p.x + 30, p.right - 8, 35):
            pygame.draw.line(s, (32, 45, 100), (x, band.bottom + 4), (x, p.bottom - 10), 1)
        scan = p.y + 50 + (self.time * 80) % (p.h - 60)  # קו סריקה
        sl = pygame.Surface((p.w - 12, 3), pygame.SRCALPHA)
        sl.fill((*CYAN, 40))
        s.blit(sl, (p.x + 6, scan))

        show = [self.a >= 100, True, True]
        if 0 <= self.col <= 2 and self.done_t < 0:
            pulse = (math.sin(self.time * 5) + 1) / 2
            hl = pygame.Surface((64, 270), pygame.SRCALPHA)
            pygame.draw.rect(hl, (255, 210, 60, int(70 + 50 * pulse)), hl.get_rect(), border_radius=16)
            pygame.draw.rect(hl, (255, 170, 30, 200), hl.get_rect(), 3, border_radius=16)
            s.blit(hl, (self.col_x(self.col) - 32, p.y + 58))

        y_small, y_top, y_bot, y_line, y_ans = p.y + 80, p.y + 140, p.y + 208, p.y + 250, p.y + 295
        for i in range(3):
            if not show[i]:
                continue
            x = self.col_x(i)
            r = text(s, str(self.orig[i]), 58, INK, (x, y_top))
            if self.top[i] != self.orig[i] and self.time >= self.top_t[i]:
                age = self.time - self.top_t[i]
                sc = 1 + 0.5 * max(0, 1 - age * 4)
                thick_line(s, RED, (r.left + 2, r.bottom - 12), (r.right - 2, r.top + 12), 4)
                tag = render(str(self.top[i]), 28, WHITE).get_rect(center=(x, y_small))
                tag.inflate_ip(14, 2)
                pygame.draw.rect(s, ORANGE, tag, border_radius=10)
                text(s, str(self.top[i]), 28, WHITE, (x, y_small), scale=sc)
            if self.b >= 100 or i > 0:
                text(s, str(self.bot[i]), 58, INK, (x, y_bot))
            if self.ans[i] is not None:
                age = self.time - self.ans_t[i]
                sc = 1 + 0.6 * max(0, 1 - age * 4)
                text(s, str(self.ans[i]), 58, GREEN, (x, y_ans), scale=sc)
            elif i == self.col and self.done_t < 0:
                bob = math.sin(self.time * 4) * 3
                text(s, "?", 54, YELLOW, (x, y_ans + bob))
        text(s, "−", 58, INK, (82, y_bot))
        thick_line(s, INK, (62, y_line), (322, y_line), 4)
        for f in self.flyers:          # "10" שעף בזמן פריטה
            if f[4] < 0:
                continue
            t = min(1, f[4] / 0.6)
            e = 1 - (1 - t) ** 3
            x = f[0] + (f[2] - f[0]) * e
            y = f[1] + (f[3] - f[1]) * e - math.sin(t * math.pi) * 55
            text(s, "10", 32, ORANGE, (x, y), outline=WHITE, ow=3, scale=1 + 0.3 * math.sin(t * math.pi))

    def draw_helper(self, s):
        """הסבר קצר על העמודה הנוכחית - מה עושים עכשיו."""
        box = pygame.Rect(22, 384, 330, 186)
        self.borrow_btn = None
        if self.done_t >= 0 or not (0 <= self.col <= 2):
            card(s, box, PANEL, radius=18, shadow=60, border=GREEN)
            sc = 1 + 0.08 * math.sin(self.time * 8)
            text(s, "כל הכבוד!", 44, GREEN, (box.centerx, box.centery - 20), scale=sc)
            for k in range(3):
                draw_star(s, box.centerx - 50 + k * 50, box.centery + 40, 16, YELLOW, self.time + k)
            return
        i = self.col
        borrow = self.need_borrow()
        head = (255, 120, 60) if borrow else (70, 120, 255)
        card(s, box, PANEL, radius=18, shadow=60, border=head)
        hb = pygame.Rect(box.x, box.y, box.w, 44)
        hb = hb.inflate(-6, -6).move(0, 0)
        pygame.draw.rect(s, head, hb, border_top_left_radius=16, border_top_right_radius=16)
        name = ["המאות", "העשרות", "האחדות"][i]
        text(s, f"עמודת {name}", 24, WHITE, hb.center)
        if borrow:
            text(s, f"{self.top[i]} קטן מ-{self.bot[i]}", 30, RED, (box.centerx, box.y + 76))
            self.borrow_btn = pygame.Rect(box.x + 45, box.y + 108, box.w - 90, 54)
            hover = self.borrow_btn.collidepoint(pygame.mouse.get_pos())
            pulse = (math.sin(self.time * 6) + 1) / 2
            col = mix((255, 140, 30), (255, 175, 40), pulse)
            button3d(s, self.borrow_btn, col, "לפרוט - רווח", 28,
                     pressed=pygame.mouse.get_pressed()[0] and hover, hover=hover)
        else:
            text(s, f"{self.top[i]} - {self.bot[i]} = ?", 46, INK, (box.centerx, box.y + 92))
            text(s, "תפסו את המטאור הנכון", 22, INK_SOFT, (box.centerx, box.y + 148), bold=False)

    # ------------------------------------------------------------ ציור: ממשק
    def pill(self, s, center, w, label, col):
        r = pygame.Rect(0, 0, w, 44)
        r.center = center
        card(s, r, PANEL, radius=22, shadow=45, border=col, bw=2)
        text(s, label, 24, col, r.center)
        return r

    def draw_hud(self, s):
        r = self.pill(s, (FIELD_X + 120, 32), 170, f"ניקוד {int(round(self.shown_score))}", INK)
        draw_star(s, r.x + 4, r.centery, 18, YELLOW, self.time * 0.5)
        self.pill(s, (FIELD_X + 290, 32), 120, f"שלב {self.level}", ORANGE)
        hr = pygame.Rect(0, 0, 40 * 3 + 30, 44)
        hr.topright = (W - 140, 10)
        for k in range(3):
            x = W - 168 - k * 38
            col = RED if k < self.hearts else (200, 205, 220)
            beat = 1 + 0.08 * math.sin(self.time * 6) if k < self.hearts else 1
            draw_heart(s, x, 28, 15 * beat, col)
        if self.streak >= 2:
            text(s, f"רצף ×{self.streak}", 22, ORANGE, (FIELD_X + 120, 66), outline=WHITE, ow=2)
        # הודעה
        if self.msg_t > 0 and self.msg:
            appear = min(1, self.msg_age / 0.18)
            sc = 0.7 + 0.3 * (1 - (1 - appear) ** 3)
            alpha = int(255 * min(1, self.msg_t / 0.3))
            img = render(self.msg, 26, tuple(self.msg_col))
            bw, bh = img.get_width() + 40, img.get_height() + 18
            bub = pygame.Surface((bw, bh + 12), pygame.SRCALPHA)
            pygame.draw.rect(bub, (*PANEL, 240), (0, 0, bw, bh), border_radius=bh // 2)
            pygame.draw.rect(bub, self.msg_col, (0, 0, bw, bh), 3, border_radius=bh // 2)
            pygame.draw.polygon(bub, self.msg_col, [(bw / 2 - 10, bh - 2), (bw / 2 + 10, bh - 2), (bw / 2, bh + 10)])
            bub.blit(img, (20, 9))
            bub = pygame.transform.smoothscale(bub, (int(bw * sc), int((bh + 12) * sc)))
            bub.set_alpha(alpha)
            cx = max(FIELD_X + 20 + bub.get_width() / 2, min(W - 20 - bub.get_width() / 2, (FIELD_X + W) / 2))
            s.blit(bub, bub.get_rect(center=(cx, 108)))

    def draw_effects(self, s):
        for p in self.particles:
            if p[0] == "ring":
                t = p[3] / p[4]
                r = int(20 + 40 * t)
                ring = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(ring, (*p[5], int(220 * (1 - t))), (r + 2, r + 2), r, 4)
                s.blit(ring, (p[1] - r - 2, p[2] - r - 2))
            else:
                _, x, y, _, _, life, col, rot, _, shape = p
                a = min(1, life / 0.4)
                size = 6 * a + 1
                if shape:
                    draw_star(s, x, y, size + 2, col, rot)
                else:
                    c, sn = math.cos(rot), math.sin(rot)
                    pts = [(x + c * dx - sn * dy, y + sn * dx + c * dy)
                           for dx, dy in ((-size, -size / 2), (size, -size / 2), (size, size / 2), (-size, size / 2))]
                    aa_poly(s, col, pts)
        for txt, x, y, life, col in self.popups:
            text(s, txt, 40, col, (x, y), outline=WHITE, ow=3, alpha=int(255 * min(1, life / 0.4)),
                 scale=1 + 0.3 * max(0, life - 0.8))

    def draw_play(self, s):
        self.draw_world(s)
        for b in self.balloons:
            self.draw_balloon(s, b)
        self.draw_catcher(s)
        self.draw_effects(s)
        self.draw_notebook(s)
        self.draw_helper(s)
        self.draw_hud(s)
        if self.hurt > 0:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 60, 60, int(90 * self.hurt)))
            s.blit(ov, (0, 0))

    def draw_menu(self, s):
        self.draw_world(s)
        for b in self.menu_balloons:
            self.draw_balloon(s, b)
        self.draw_effects(s)
        bounce = math.sin(self.time * 2) * 6
        text(s, "תופסים את התשובה בחלל!", 66, WHITE, (W / 2, 92 + bounce), outline=(120, 60, 220), ow=6)
        box = pygame.Rect(W / 2 - 330, 170, 660, 330)
        card(s, box, PANEL, radius=26, shadow=80, border=CYAN)
        steps = [
            ("1", "פותרים עמודה אחרי עמודה - מתחילים באחדות", (90, 140, 240)),
            ("2", "תופסים בצלחת את המטאור עם הספרה הנכונה", (60, 190, 110)),
            ("3", "הספרה למעלה קטנה? לוחצים רווח כדי לפרוט", (255, 130, 40)),
            ("4", "מתחמקים ממטאורים לא נכונים - יש רק 3 לבבות", (235, 70, 80)),
        ]
        for k, (num, ln, col) in enumerate(steps):
            y = box.y + 52 + k * 64
            aa_circle(s, col, box.right - 50, y, 22)
            text(s, num, 26, WHITE, (box.right - 50, y))
            img = render(ln, 26, INK, False)
            s.blit(img, img.get_rect(midright=(box.right - 88, y)))
        text(s, "תזוזה: חיצים או עכבר", 22, INK_SOFT, (box.centerx, box.bottom - 30), bold=False)
        self.buttons = {}
        btn = pygame.Rect(W / 2 - 150, 540, 300, 76)
        hover = btn.collidepoint(pygame.mouse.get_pos())
        button3d(s, btn, (50, 190, 100), "התחלה", 40, pressed=hover and pygame.mouse.get_pressed()[0],
                 hover=hover)
        self.buttons["start"] = btn

    def draw_gameover(self, s):
        self.draw_play(s)
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((5, 5, 25, 170))
        s.blit(ov, (0, 0))
        box = pygame.Rect(W / 2 - 260, 150, 520, 400)
        card(s, box, PANEL, radius=26, shadow=90, border=RED)
        text(s, "נגמרו הלבבות", 54, RED, (box.centerx, box.y + 60))
        text(s, f"פתרתם {self.solved} תרגילים", 34, INK, (box.centerx, box.y + 140))
        r = text(s, f"ניקוד: {self.score}", 34, INK, (box.centerx, box.y + 205))
        draw_star(s, r.left - 28, r.centery, 20, YELLOW, self.time)
        draw_star(s, r.right + 28, r.centery, 20, YELLOW, -self.time)
        self.buttons = {}
        btn = pygame.Rect(box.centerx - 150, box.bottom - 120, 300, 76)
        hover = btn.collidepoint(pygame.mouse.get_pos())
        button3d(s, btn, (50, 190, 100), "עוד פעם!", 38, hover=hover)
        self.buttons["start"] = btn

    def draw(self):
        s = self.canvas
        {"menu": self.draw_menu, "play": self.draw_play, "gameover": self.draw_gameover}[self.state](s)
        self.screen.fill((0, 0, 0))
        self.screen.blit(s, (random.uniform(-1, 1) * self.shake, random.uniform(-1, 1) * self.shake))

    # ------------------------------------------------------------ אירועים
    def start(self):
        self.reset()
        self.new_problem()

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            return False
        if self.state in ("menu", "gameover"):
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start()
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and "start" in self.buttons:
                if self.buttons["start"].collidepoint(e.pos):
                    self.start()
        elif self.state == "play":
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_UP):
                self.borrow()
            elif e.type == pygame.MOUSEMOTION and e.pos[0] > FIELD_X:
                self.catch_x = e.pos[0]
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                if getattr(self, "borrow_btn", None) and self.borrow_btn.collidepoint(e.pos):
                    self.borrow()
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
    pygame.init()
    pygame.display.set_caption("תופסים את התשובה בחלל - חיסור ופריטה")
    screen = pygame.display.set_mode((W, H))
    Game(screen).run()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()