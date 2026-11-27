#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מלחמת שרבוטים — Doodle War (Python / pygame)

התקנה:   pip install pygame
הרצה:    python doodle_war.py

שליטה:
  עכבר שמאלי  – ציור היחידה הנבחרת
  עכבר ימני   – מחק
  רווח        – השהה / המשך
  1-9         – בחירת יחידה בקטגוריה
  Tab         – מעבר קטגוריה
  B           – מברשת גדולה / רגילה
  S           – מהירות
  C           – ניקוי המסך
  F11         – מסך מלא
  Esc         – יציאה
"""
import math
import random
import re
import sys

try:
    import pygame
except ImportError:
    print("צריך להתקין pygame:  pip install pygame")
    sys.exit(1)

TAU = math.tau
PI = math.pi
SS = 4  # supersampling for sprites


def hexc(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,)


OUT = (34, 34, 34, 255)
WHITE = (255, 255, 255, 255)
BLACK = (17, 17, 17, 255)

# ====================== Unit definitions ======================
T = {
    # Army
    'soldier':   dict(cat='army', name='חייל', hp=30, sp=42, r=9, range=170, cd=1.0, dmg=8, atk='bullet', col='#3f6fe0'),
    'rifleman':  dict(cat='army', name='מקלען', hp=35, sp=36, r=9, range=150, cd=0.18, dmg=3, atk='bullet', spread=.18, col='#d84a3a'),
    'sniper':    dict(cat='army', name='צלף', hp=25, sp=30, r=9, range=420, cd=2.6, dmg=32, atk='bullet', bs=900, col='#c9b48a'),
    'roman':     dict(cat='army', name='לגיונר', hp=65, sp=38, r=9, range=6, cd=0.8, dmg=10, atk='melee', shield=.5, col='#d33b3b'),
    'grenadier': dict(cat='army', name='רמונאי', hp=32, sp=36, r=9, range=210, cd=2.6, dmg=28, atk='grenade', aoe=45, col='#5aa0b0'),
    'archer':    dict(cat='army', name='קשת', hp=25, sp=38, r=9, range=250, cd=1.4, dmg=10, atk='arrow', col='#a98fd6'),
    'cavalry':   dict(cat='army', name='פרש', hp=85, sp=92, r=13, range=6, cd=0.7, dmg=14, atk='melee', kb=120, col='#f4f1e6'),
    'ninja':     dict(cat='army', name='נינג׳ה', hp=35, sp=100, r=8, range=6, cd=0.38, dmg=11, atk='melee', dodge=.35, col='#3a3a48'),
    'knight':    dict(cat='army', name='אביר', hp=130, sp=30, r=10, range=6, cd=1.0, dmg=18, atk='melee', armor=.6, col='#b8bec8'),
    # Animals
    'wolf':      dict(cat='animals', name='זאב', hp=35, sp=88, r=9, range=5, cd=0.55, dmg=8, atk='melee', col='#8a8f99'),
    'bear':      dict(cat='animals', name='דוב', hp=170, sp=45, r=15, range=6, cd=1.2, dmg=26, atk='melee', kb=80, col='#8a5a34'),
    'bull':      dict(cat='animals', name='שור', hp=110, sp=72, r=13, range=5, cd=1.1, dmg=20, atk='melee', kb=220, col='#5b3a26'),
    'chicken':   dict(cat='animals', name='תרנגולת', hp=8, sp=55, r=6, range=4, cd=0.6, dmg=2, atk='melee', col='#fafafa'),
    'bee':       dict(cat='animals', name='דבורה', hp=4, sp=130, r=4, range=3, cd=0.5, dmg=3, atk='melee', fly=1, col='#ffcf2e'),
    'croc':      dict(cat='animals', name='תנין', hp=120, sp=40, r=13, range=6, cd=1.0, dmg=22, atk='melee', swim=1, col='#5c8a3a'),
    # Mythical
    'zombie':    dict(cat='myth', name='זומבי', hp=50, sp=24, r=9, range=5, cd=1.0, dmg=8, atk='melee', col='#8fae7a'),
    'slime':     dict(cat='myth', name='סליים', hp=30, sp=34, r=9, range=4, cd=0.9, dmg=6, atk='melee', col='#f27fb8'),
    'wizard':    dict(cat='myth', name='קוסם', hp=30, sp=34, r=9, range=230, cd=2.3, dmg=22, atk='fireball', aoe=38, col='#5468d8'),
    'golem':     dict(cat='myth', name='גולם', hp=260, sp=22, r=14, range=6, cd=1.6, dmg=35, atk='melee', kb=160, armor=.7, col='#d18a5a'),
    'dragon':    dict(cat='myth', name='דרקון', hp=700, sp=36, r=28, range=150, cd=0.05, dmg=2.2, atk='breath', fly=1, col='#c0302a'),
    'ghost':     dict(cat='myth', name='רוח רפאים', hp=40, sp=42, r=9, range=5, cd=0.8, dmg=7, atk='melee', fly=1, phase=.6, col='#f2f2f8'),
    # Terrain
    'tree':      dict(cat='terrain', name='עץ', hp=90, r=13, stat=1, col='#4caf50'),
    'barrel':    dict(cat='terrain', name='חבית נפץ', hp=12, r=8, stat=1, col='#d22b2b'),
    'mine':      dict(cat='terrain', name='מוקש', hp=1, r=6, stat=1, col='#3d4a3a'),
    'rock':      dict(cat='terrain', name='סלע', hp=600, r=14, stat=1, col='#9aa0a8'),
    'lake':      dict(cat='terrain', name='אגם', special=1, r=11, col='#5bb8e8'),
    'eraser':    dict(cat='terrain', name='מחק', special=1, r=11, col='#ffffff'),
}
for _k, _d in T.items():
    _d['c'] = hexc(_d['col'])
    for _f in ('fly', 'stat', 'special', 'swim'):
        _d.setdefault(_f, 0)
CATS = [('army', 'צבא'), ('animals', 'חיות'), ('myth', 'מיתולוגי'), ('terrain', 'שטח')]

# ====================== Hebrew text ======================
try:
    from bidi.algorithm import get_display  # optional: pip install python-bidi
except Exception:
    get_display = None
HEB = re.compile('[֐-׿]')
LTR = r'[A-Za-z0-9.×+:%/\-]+'


def bidi(s):
    if not HEB.search(s):
        return s
    if get_display:
        return get_display(s)
    toks = re.findall(LTR + r'|[^A-Za-z0-9.×+:%/\-]+', s)
    out = []
    for t in reversed(toks):
        out.append(t if re.fullmatch(LTR, t) else t[::-1])
    return ''.join(out)


FONTS = {}
FONT_NAMES = ['arial', 'segoeui', 'tahoma', 'rubik', 'alef', 'notosanshebrew', 'dejavusans', 'freesans', 'liberationsans']


def font(size, bold=False):
    key = (size, bold)
    if key not in FONTS:
        f = None
        for n in FONT_NAMES:
            p = pygame.font.match_font(n, bold=bold)
            if p:
                try:
                    f = pygame.font.Font(p, size)
                    break
                except Exception:
                    pass
        FONTS[key] = f or pygame.font.Font(None, size + 6)
    return FONTS[key]


TXT = {}


def text(s, size, col=(40, 40, 40), bold=False, outline=None, ow=2):
    key = (s, size, col, bold, outline, ow)
    if key in TXT:
        return TXT[key]
    f = font(size, bold)
    t = bidi(s)
    base = f.render(t, True, col)
    if outline:
        o = f.render(t, True, outline)
        w, h = base.get_width() + ow * 2, base.get_height() + ow * 2 + ow
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for dx in range(-ow, ow + 1):
            for dy in range(-ow, ow + 2):
                if dx * dx + dy * dy <= ow * ow + ow:
                    surf.blit(o, (ow + dx, ow + dy))
        surf.blit(base, (ow, ow))
        base = surf
    if len(TXT) > 600:
        TXT.clear()
    TXT[key] = base
    return base


# ====================== Sprite pen ======================
class Pen:
    def __init__(self, surf, cx, cy, k):
        self.s, self.cx, self.cy, self.k = surf, cx, cy, k

    def P(self, x, y):
        return (self.cx + x * self.k, self.cy + y * self.k)

    def circle(self, x, y, r, fill, out=None, w=0):
        c = self.P(x, y)
        if out:
            pygame.draw.circle(self.s, out, c, max(1, (r + w / 2) * self.k))
            pygame.draw.circle(self.s, fill, c, max(1, (r - w / 2) * self.k))
        else:
            pygame.draw.circle(self.s, fill, c, max(1, r * self.k))

    def poly(self, pts, fill, out=None, w=0):
        pp = [self.P(x, y) for x, y in pts]
        if len(pp) < 3:
            return
        pygame.draw.polygon(self.s, fill, pp)
        if out:
            lw = max(1, int(w * self.k))
            pygame.draw.polygon(self.s, out, pp, lw)
            for q in pp:
                pygame.draw.circle(self.s, out, q, lw / 2)

    def rect(self, x, y, w, h, fill, out=None, ow=0, rad=0):
        R = pygame.Rect(0, 0, max(1, w * self.k), max(1, h * self.k))
        R.topleft = self.P(x, y)
        if out:
            O = R.inflate(ow * self.k * 2, ow * self.k * 2)
            pygame.draw.rect(self.s, out, O, border_radius=int((rad + ow) * self.k))
        pygame.draw.rect(self.s, fill, R, border_radius=int(rad * self.k))

    def ellipse(self, x, y, rx, ry, fill, out=None, w=0):
        if out:
            R = pygame.Rect(0, 0, (rx + w / 2) * 2 * self.k, (ry + w / 2) * 2 * self.k)
            R.center = self.P(x, y)
            pygame.draw.ellipse(self.s, out, R)
            rx, ry = rx - w / 2, ry - w / 2
        R = pygame.Rect(0, 0, max(1, rx * 2 * self.k), max(1, ry * 2 * self.k))
        R.center = self.P(x, y)
        pygame.draw.ellipse(self.s, fill, R)

    def line(self, x1, y1, x2, y2, col, w):
        a, b = self.P(x1, y1), self.P(x2, y2)
        lw = max(1, int(w * self.k))
        pygame.draw.line(self.s, col, a, b, lw)
        pygame.draw.circle(self.s, col, a, lw / 2)
        pygame.draw.circle(self.s, col, b, lw / 2)

    def polyline(self, pts, col, w):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], col, w)

    def chord(self, x, y, r, a0, a1, fill, out=None, w=0, n=18):
        pts = [(x + math.cos(a0 + (a1 - a0) * i / n) * r, y + math.sin(a0 + (a1 - a0) * i / n) * r) for i in range(n + 1)]
        self.poly(pts, fill, out, w)


def arcpts(cx, cy, r, a0, a1, n=14):
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * r, cy + math.sin(a0 + (a1 - a0) * i / n) * r) for i in range(n + 1)]


def qcurve(p0, p1, p2, n=10):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 2
        b = 2 * (1 - t) * t
        c = t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return out


def draw_unit(p, t, r, fr, burnt=False):
    d = T[t]
    col = d['c']

    def body(c=col):
        w = max(1.2, r * .15)
        p.circle(0, 0, r + w / 2, OUT)
        p.circle(0, 0, r - w / 2, mix(c, BLACK, .3))
        p.circle(-r * .09, -r * .1, r * .76, c)
        p.circle(-r * .3, -r * .34, r * .32, mix(c, WHITE, .22))
        p.circle(-r * .36, -r * .42, r * .16, mix(c, WHITE, .55))

    def eyes(ey=None, s=1.0):
        ey = -r * .12 if ey is None else ey
        for ex in (r * .08, r * .52):
            p.circle(ex, ey, r * .25 * s, WHITE, OUT, max(.6, r * .07))
            p.circle(ex + r * .09, ey, r * .12 * s, BLACK)
            p.circle(ex + r * .05, ey - r * .05, r * .04 * s, WHITE)

    def gun(L=1.5):
        p.rect(r * .1, r * .22, r * L, r * .24, (43, 43, 43, 255))
        p.rect(r * .05, r * .3, r * .45, r * .3, (107, 74, 43, 255))

    if t == 'soldier':
        body(); eyes()
        p.chord(0, -r * .35, r * .92, PI * 1.05, PI * 1.95, hexc('#2a3f7a'))
        p.rect(0, -r * .55, r * 1.1, r * .18, hexc('#2a3f7a'))
        gun()
    elif t == 'rifleman':
        body(); eyes()
        p.chord(0, -r * .3, r * .95, PI * 1.05, PI * 1.95, hexc('#222222'))
        p.rect(-r * .3, -r * 1.05, r * .6, r * .2, hexc('#ffd43b'))
        gun(1.4)
        p.rect(r * 1.2, r * .25, r * .4, r * .16, hexc('#e0a020'))
    elif t == 'sniper':
        body(); eyes(ey=-r * .02)
        p.ellipse(0, -r * .42, r * 1.35, r * .28, hexc('#7a5a32'), OUT, r * .08)
        p.ellipse(0, -r * .62, r * .65, r * .42, hexc('#7a5a32'))
        p.rect(-r * .6, -r * .5, r * 1.2, r * .12, hexc('#4a3a22'))
        gun(2.2)
        p.rect(r * .7, r * .04, r * .5, r * .16, BLACK)
    elif t == 'roman':
        body(); eyes()
        p.rect(-r * .5, -r * 1.45, r * 1.0, r * .4, hexc('#d33b3b'), rad=r * .15)
        p.chord(0, -r * .3, r * .9, PI, TAU, hexc('#e6b422'))
        p.line(r * .6, r * 1.2, r * 1.1, -r * 1.4, hexc('#5a3a1a'), r * .16)
        p.poly([(r * 1.1, -r * 1.6), (r * .9, -r * 1.05), (r * 1.3, -r * 1.1)], hexc('#cccccc'))
        p.rect(r * .7, -r * .1, r * .45, r * 1.1, hexc('#b8862a'), hexc('#5a3a1a'), r * .08, rad=r * .1)
        p.circle(r * .92, r * .45, r * .1, hexc('#f0d060'))
    elif t == 'grenadier':
        body(); eyes()
        p.chord(0, -r * .3, r * .95, PI, TAU, hexc('#3b5b3a'))
        p.circle(r * .95, r * .45, r * .32, hexc('#3d4a2a'), BLACK, r * .08)
        p.rect(r * .88, r * .02, r * .14, r * .18, hexc('#999999'))
    elif t == 'archer':
        body()
        p.chord(0, -r * .1, r * 1.05, PI * .95, PI * 2.05, hexc('#3e8e4a'))
        p.poly([(-r * .6, -r * .8), (-r * 1.4, -r * 1.25), (-r * .2, -r * 1.0)], hexc('#3e8e4a'))
        eyes(ey=r * .05)
        bow = arcpts(r * .7, r * .2, r * .9, -1.2, 1.2)
        p.polyline(bow, hexc('#8b5a2b'), r * .16)
        p.line(bow[0][0], bow[0][1], bow[-1][0], bow[-1][1], hexc('#dddddd'), r * .06)
    elif t == 'cavalry':
        k = r / 13
        leg = 3 if fr else -3
        for lx, ph in ((-8, 1), (-4, -1), (6, -1), (10, 1)):
            p.line(lx * k, 3 * k, (lx + leg * ph) * k, 13 * k, OUT, 2.5 * k)
        p.poly([(-13 * k, 0), (-17 * k, 6 * k), (-14 * k, 8 * k)], hexc('#c9a46a'))
        p.ellipse(0, 2 * k, 13 * k, 6.5 * k, hexc('#f4f1e6'), OUT, 1.6 * k)
        p.poly([(9 * k, 0), (15 * k, -9 * k), (20 * k, -7 * k), (13 * k, 3 * k)], hexc('#f4f1e6'), OUT, 1.6 * k)
        p.circle(18 * k, -8 * k, 1 * k, BLACK)
        p.rect(-4 * k, -3 * k, 7 * k, 5 * k, hexc('#c04040'), rad=1 * k)
        p.circle(-1 * k, -8 * k, 6 * k, hexc('#f2c94c'), OUT, 1.4 * k)
        for ex in (-.5, 2.6):
            p.circle(ex * k, -8.7 * k, 1.5 * k, WHITE, OUT, .4 * k)
            p.circle((ex + .5) * k, -8.7 * k, .75 * k, BLACK)
        p.chord(-1 * k, -9.5 * k, 6 * k, PI, TAU, hexc('#9aa0a8'))
        p.line(1 * k, -4 * k, 20 * k, -14 * k, hexc('#777777'), 1.4 * k)
    elif t == 'ninja':
        body()
        p.rect(-r * .1, -r * .35, r * .95, r * .4, hexc('#f0d9c0'), rad=r * .1)
        p.circle(r * .18, -r * .15, r * .12, BLACK)
        p.circle(r * .6, -r * .15, r * .12, BLACK)
        p.rect(-r * .95, -r * .72, r * 1.85, r * .22, hexc('#e03030'))
        p.poly([(-r * .9, -r * .7), (-r * 1.6, -r * .95), (-r * 1.5, -r * .55)], hexc('#e03030'))
        p.line(r * .5, r * .6, r * 1.7, -r * .6, hexc('#e0e0e0'), r * .14)
        p.line(r * .3, r * .8, r * .55, r * .55, hexc('#7a2a2a'), r * .2)
    elif t == 'knight':
        body()
        p.chord(0, -r * .1, r * .95, PI, TAU, hexc('#7d838e'))
        p.rect(-r * .1, -r * .32, r * .95, r * .14, BLACK)
        p.rect(-r * .15, -r * 1.35, r * .3, r * .45, hexc('#3060c0'), rad=r * .12)
        p.line(r * .6, r * .6, r * 1.6, -r * .7, hexc('#e8e8e8'), r * .18)
        p.line(r * .4, r * .25, r * .9, r * .8, hexc('#8b6a2a'), r * .16)
    elif t == 'wolf':
        for ex in (-r * .25, r * .45):
            p.poly([(ex - r * .32, -r * .6), (ex, -r * 1.4), (ex + r * .32, -r * .6)], col, OUT, r * .14)
            p.poly([(ex - r * .15, -r * .7), (ex, -r * 1.15), (ex + r * .15, -r * .7)], hexc('#e8b0b0'))
        body()
        p.ellipse(r * .78, r * .22, r * .48, r * .32, hexc('#cfd2d8'), OUT, r * .08)
        p.circle(r * 1.15, r * .12, r * .14, BLACK)
        eyes(s=.85)
    elif t == 'bear':
        p.circle(-r * .55, -r * .75, r * .32, col, OUT, r * .1)
        p.circle(r * .45, -r * .8, r * .32, col, OUT, r * .1)
        p.circle(-r * .55, -r * .75, r * .15, hexc('#d9b48a'))
        p.circle(r * .45, -r * .8, r * .15, hexc('#d9b48a'))
        body()
        p.circle(r * .55, r * .25, r * .36, hexc('#d9b48a'), OUT, r * .06)
        p.circle(r * .75, r * .12, r * .13, BLACK)
        eyes(s=.7, ey=-r * .25)
    elif t == 'bull':
        h1 = qcurve((-r * .3, -r * .7), (-r * .8, -r * 1.4), (-r * .2, -r * 1.55))
        h2 = qcurve((r * .5, -r * .7), (r * 1.0, -r * 1.4), (r * .4, -r * 1.55))
        p.polyline(h1, hexc('#555555'), r * .28)
        p.polyline(h2, hexc('#555555'), r * .28)
        p.polyline(h1, hexc('#f0ebe0'), r * .18)
        p.polyline(h2, hexc('#f0ebe0'), r * .18)
        body()
        p.ellipse(r * .72, r * .3, r * .4, r * .3, hexc('#d99a8a'), OUT, r * .06)
        p.circle(r * .6, r * .3, r * .07, OUT)
        p.circle(r * .86, r * .3, r * .07, OUT)
        eyes(s=.75, ey=-r * .25)
    elif t == 'chicken':
        p.circle(-r * .05, -r * .95, r * .3, hexc('#ee3333'))
        p.circle(r * .35, -r * .9, r * .25, hexc('#ee3333'))
        body()
        p.poly([(r * .8, -r * .1), (r * 1.45, r * .05), (r * .8, r * .28)], hexc('#f5a623'), OUT, r * .06)
        p.ellipse(r * .7, r * .45, r * .14, r * .22, hexc('#ee3333'))
        p.circle(r * .4, -r * .2, r * .15, BLACK)
    elif t == 'bee':
        wy = .8 + (.35 if fr else -.2)
        p.ellipse(-r * .2, -r * 1.0, r * .5, r * wy, hexc('#e6f0ff'), hexc('#9ab0c8'), r * .08)
        body()
        for sx in (-r * .4, r * .05):
            hh = math.sqrt(max(0, r * r - (sx + r * .12) ** 2)) * .9
            p.rect(sx, -hh, r * .25, hh * 2, hexc('#222222'))
        p.circle(r * .62, -r * .15, r * .18, BLACK)
    elif t == 'croc':
        k = r / 13
        top = qcurve((-20 * k, 2 * k), (-10 * k, -8 * k), (6 * k, -6 * k))
        bot = qcurve((6 * k, 6 * k), (-8 * k, 8 * k), (-20 * k, 2 * k))
        pts = top + [(22 * k, -3 * k), (22 * k, 4 * k)] + bot
        p.poly(pts, col, OUT, 1.6 * k)
        for i in range(-3, 3):
            p.poly([(i * 4 * k, -5.5 * k), (i * 4 * k + 2 * k, -8.5 * k), (i * 4 * k + 4 * k, -5 * k)], mix(col, OUT, .3))
        p.line(6 * k, .5 * k, 21 * k, .5 * k, OUT, .8 * k)
        for i in range(4):
            p.poly([(8 * k + i * 3.5 * k, -.4 * k), (9.7 * k + i * 3.5 * k, 2.5 * k), (11.4 * k + i * 3.5 * k, -.4 * k)], WHITE)
        p.circle(6 * k, -7 * k, 3 * k, WHITE, OUT, 1 * k)
        p.circle(7 * k, -7 * k, 1.5 * k, BLACK)
    elif t == 'zombie':
        for y in (-r * .05, r * .42):
            p.rect(r * .3, y, r * 1.05, r * .28, col, OUT, r * .08)
        body()
        p.circle(r * .1, -r * .25, r * .27, WHITE, OUT, r * .07)
        p.circle(r * .15, -r * .25, r * .09, hexc('#cc0000'))
        p.circle(r * .55, -r * .3, r * .18, WHITE, OUT, r * .07)
        p.circle(r * .58, -r * .3, r * .07, BLACK)
        p.line(r * .05, r * .38, r * .55, r * .3, hexc('#5a3a3a'), r * .1)
        p.rect(-r * .55, r * .05, r * .25, r * .2, hexc('#6a8a5a'))
    elif t == 'slime':
        sq = 1.07 if fr else .95
        X = lambda x: x / sq
        Y = lambda y: y * sq
        pts = (qcurve((X(-r * 1.1), Y(r * .6)), (X(-r * 1.2), Y(-r * .95)), (0, Y(-r * .95)))
               + qcurve((0, Y(-r * .95)), (X(r * 1.2), Y(-r * .95)), (X(r * 1.1), Y(r * .6)))[1:]
               + qcurve((X(r * 1.1), Y(r * .6)), (0, Y(r * .95)), (X(-r * 1.1), Y(r * .6)))[1:])
        p.poly(pts, col, hexc('#8a2f62'), max(1, r * .14))
        p.circle(X(-r * .5), Y(-r * .45), r * .2, mix(col, WHITE, .6))
        p.circle(X(-r * .2), Y(-r * .65), r * .08, mix(col, WHITE, .6))
        eyes(s=.8, ey=-r * .1)
    elif t == 'wizard':
        p.line(r * .9, r * 1.1, r * 1.1, -r * 1.1, hexc('#6b4a2b'), r * .16)
        p.circle(r * 1.1, -r * 1.25, r * .3, hexc('#ffb04a'), hexc('#c06010'), r * .06)
        p.circle(r * 1.05, -r * 1.32, r * .1, hexc('#fff3c0'))
        body()
        p.circle(r * .3, -r * .05, r * .55, hexc('#f0d9c0'))
        p.circle(r * .15, -r * .12, r * .1, BLACK)
        p.circle(r * .5, -r * .12, r * .1, BLACK)
        p.poly([(-r * .1, r * .25), (r * .3, r * 1.15), (r * .75, r * .25)], hexc('#e8e8e8'), hexc('#999999'), r * .05)
        p.poly([(-r * 1.15, -r * .45), (-r * .1, -r * 2.05), (r * 1.1, -r * .45)], hexc('#3b3f9a'), OUT, r * .1)
        p.circle(-r * .05, -r * .95, r * .15, hexc('#ffd43b'))
        p.circle(r * .35, -r * 1.35, r * .07, hexc('#ffd43b'))
    elif t == 'golem':
        pts = [(-r, -r * .6), (-r * .5, -r), (r * .6, -r * .95), (r, -r * .3), (r * .9, r * .8), (-r * .8, r * .9)]
        p.poly(pts, col, hexc('#4a2e1a'), r * .12)
        p.poly([(-r * .6, -r * .5), (-r * .3, -r * .75), (r * .3, -r * .7), (-r * .1, -r * .4)], mix(col, WHITE, .3))
        p.polyline([(-r * .4, r * .2), (0, r * .5), (-r * .2, r * .8)], hexc('#4a2e1a'), r * .1)
        p.polyline([(r * .5, r * .1), (r * .7, r * .4)], hexc('#4a2e1a'), r * .08)
        p.circle(r * .1, -r * .35, r * .2, hexc('#ffe08a'))
        p.circle(r * .55, -r * .35, r * .2, hexc('#ffe08a'))
        p.circle(r * .1, -r * .35, r * .12, hexc('#ff9a1e'))
        p.circle(r * .55, -r * .35, r * .12, hexc('#ff9a1e'))
    elif t == 'dragon':
        k = r / 28
        fl = 6 if fr else -4
        dk = hexc('#5a1210')
        wing = [(-6, -6), (-22, -30 - fl), (-14, -24 - fl), (-6, -34 - fl), (2, -24 - fl), (12, -30 - fl), (8, -6)]
        p.poly([(x * k, y * k) for x, y in wing], hexc('#9a221d'), dk, 2 * k)
        p.polyline([(-6 * k, -6 * k), (-14 * k, -24 * k - fl * k)], dk, 1.2 * k)
        p.polyline([(2 * k, -6 * k), (2 * k, -24 * k - fl * k)], dk, 1.2 * k)
        tail = qcurve((-14, 4), (-34, 12), (-46, 0)) + [(-40, 6)] + qcurve((-40, 6), (-30, 16), (-14, 10))[1:]
        p.poly([(x * k, y * k) for x, y in tail], col, dk, 2 * k)
        p.poly([(-46 * k, 0), (-52 * k, -6 * k), (-44 * k, -4 * k)], hexc('#f0c060'))
        for lx in (-12, -4, 8, 14):
            p.line(lx * k, 12 * k, (lx + (2 if fr else -2)) * k, 21 * k, dk, 3 * k)
        p.ellipse(0, 4 * k, 22 * k, 11 * k, col, dk, 2 * k)
        p.ellipse(2 * k, 9 * k, 16 * k, 4 * k, hexc('#f0c060'))
        p.ellipse(-4 * k, -1 * k, 10 * k, 4 * k, mix(col, WHITE, .2))
        head = [(14, -2), (26, -14), (38, -12), (43, -6), (28, -4), (20, 6)]
        p.poly([(x * k, y * k) for x, y in head], col, dk, 2 * k)
        p.poly([(30 * k, -12 * k), (27 * k, -21 * k), (33 * k, -13 * k)], WHITE)
        p.circle(32 * k, -10 * k, 2.4 * k, hexc('#ffdd33'), OUT, 1 * k)
        p.circle(32.6 * k, -10 * k, 1 * k, BLACK)
        for i in range(-14, 12, 6):
            p.poly([(i * k, -6 * k), ((i + 3) * k, -11 * k), ((i + 6) * k, -6 * k)], hexc('#f0c060'))
    elif t == 'ghost':
        wv = 0.8 if fr else 0
        pts = [(-r, r * .9), (-r, 0)] + arcpts(0, 0, r, PI, TAU, 14)[1:] + [(r, r * .9)]
        for i in range(4):
            x = r - (i + .5) * r * .5
            pts += qcurve(pts[-1], (x + r * .12, r * (1.2 + math.sin(wv + i) * .15)), (x - r * .25, r * .9), 5)[1:]
        p.poly(pts, col, hexc('#9a9aa8'), max(1, r * .1))
        p.circle(r * .1, -r * .1, r * .18, OUT)
        p.circle(r * .55, -r * .1, r * .18, OUT)
        p.ellipse(r * .35, r * .35, r * .12, r * .18, OUT)
    elif t == 'tree':
        c1 = hexc('#6d6a3a') if burnt else hexc('#62c062')
        c2 = hexc('#57552d') if burnt else hexc('#3f9a45')
        line = hexc('#3a3a20') if burnt else hexc('#2e6b30')
        p.rect(-r * .18, 0, r * .36, r * .95, hexc('#7a5230'), hexc('#3e2a16'), r * .06)
        for x, y, s, c in ((-r * .45, -r * .2, .6, c2), (r * .45, -r * .2, .6, c2), (0, -r * .55, .7, c1), (0, -r * .05, .6, c1)):
            p.circle(x, y, r * s, c, line, r * .09)
        if not burnt:
            p.circle(-r * .2, -r * .8, r * .2, hexc('#8ed88e'))
            p.circle(r * .3, -r * .35, r * .12, hexc('#8ed88e'))
    elif t == 'barrel':
        p.rect(-r * .75, -r, r * 1.5, r * 2, col, hexc('#5a1010'), r * .1, rad=r * .3)
        p.rect(-r * .75, -r * .55, r * 1.5, r * .18, hexc('#7a1414'))
        p.rect(-r * .75, r * .4, r * 1.5, r * .18, hexc('#7a1414'))
        p.rect(-r * .55, -r * .9, r * .2, r * 1.7, mix(col, WHITE, .3), rad=r * .1)
        p.poly([(0, -r * .35), (r * .32, 0), (0, r * .32), (-r * .32, 0)], hexc('#ffd43b'), OUT, r * .05)
    elif t == 'mine':
        p.circle(0, 0, r, col, hexc('#1a1f18'), r * .18)
        p.circle(0, 0, r * .55, hexc('#56634f'))
        p.circle(0, 0, r * .28, hexc('#ff3030') if fr else hexc('#7a1a1a'))
    elif t == 'rock':
        pts = [(-r, r * .6), (-r * .85, -r * .3), (-r * .3, -r * .85), (r * .5, -r * .75), (r, -r * .1), (r * .85, r * .65)]
        p.poly(pts, col, hexc('#4d5258'), r * .12)
        p.poly([(-r * .5, -r * .4), (-r * .2, -r * .65), (r * .3, -r * .55), (-r * .1, -r * .3)], hexc('#c4c9cf'))
        p.polyline([(r * .2, r * .1), (r * .5, r * .35)], hexc('#6d7278'), r * .08)
    elif t == 'lake':
        p.circle(0, 0, r * 1.15, hexc('#eee2b4'))
        p.circle(0, 0, r * .98, hexc('#a6e6ef'))
        p.circle(0, 0, r * .8, hexc('#4aa8e0'))
        p.ellipse(-r * .25, -r * .3, r * .3, r * .12, hexc('#bfe8ff'))
    elif t == 'eraser':
        a = -.5
        def rot(x, y):
            return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))
        p.poly([rot(-r, -r * .5), rot(r, -r * .5), rot(r, r * .5), rot(-r, r * .5)], hexc('#f6a5b8'), OUT, r * .12)
        p.poly([rot(-r, -r * .5), rot(-r * .3, -r * .5), rot(-r * .3, r * .5), rot(-r, r * .5)], hexc('#7aa6e8'), OUT, r * .12)


SPR = {}
ANIM = {'cavalry', 'bee', 'dragon', 'slime', 'ghost', 'mine'}


def sprite(t, r, face=1, fr=0, flash=False, burnt=False):
    key = (t, round(r * 2), face, fr if t in ANIM else 0, flash, burnt)
    s = SPR.get(key)
    if s is not None:
        return s
    if flash or face < 0:
        base = sprite(t, r, 1, fr, False, burnt)
        s = base.copy()
        if flash:
            s.fill((150, 150, 150, 0), special_flags=pygame.BLEND_RGBA_ADD)
        if face < 0:
            s = pygame.transform.flip(s, True, False)
        SPR[key] = s
        return s
    box = int(r * 5.2) + 12 if t != 'dragon' else int(r * 4.4) + 12
    big = pygame.Surface((box * SS, box * SS), pygame.SRCALPHA)
    pen = Pen(big, box * SS / 2, box * SS / 2, SS)
    draw_unit(pen, t, r, fr, burnt)
    s = pygame.transform.smoothscale(big, (box, box))
    if t == 'ghost':
        s.fill((255, 255, 255, 210), special_flags=pygame.BLEND_RGBA_MULT)
    SPR[key] = s
    return s


CORPSE = {}


def corpse_sprite(t, r, face):
    key = (t, round(r * 2), face)
    c = CORPSE.get(key)
    if c is None:
        base = sprite(t, r, face)
        c = pygame.transform.rotate(base, -90 * face)
        c.fill((70, 70, 70, 0), special_flags=pygame.BLEND_RGB_SUB)
        CORPSE[key] = c
    return c


ICON_R = {'dragon': 15, 'cavalry': 11, 'croc': 11, 'golem': 13, 'bear': 12, 'bull': 12, 'tree': 13, 'rock': 13}
ICONS = {}


def icon(t, size):
    key = (t, size)
    if key not in ICONS:
        r = ICON_R.get(t, 11) * size / 40
        s = sprite(t, r * 1.0)
        bw = s.get_width()
        # crop to content
        rect = s.get_bounding_rect()
        crop = s.subsurface(rect).copy() if rect.w > 0 else s
        sc = min(size * .95 / max(1, crop.get_width()), size * .9 / max(1, crop.get_height()))
        crop = pygame.transform.smoothscale(crop, (max(1, int(crop.get_width() * sc)), max(1, int(crop.get_height() * sc))))
        ICONS[key] = crop
    return ICONS[key]


GLOW = {}


def glow(col, rad):
    rad = max(2, int(rad))
    key = (col[:3], rad)
    g = GLOW.get(key)
    if g is None:
        g = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
        for i in range(rad, 0, -1):
            a = int(255 * (1 - i / rad) ** 1.4)
            pygame.draw.circle(g, (col[0], col[1], col[2], a), (rad, rad), i)
        if len(GLOW) > 1500:
            GLOW.clear()
        GLOW[key] = g
    return g


SHADOW = {}


def shadow(w, h):
    key = (int(w), int(h))
    s = SHADOW.get(key)
    if s is None:
        s = pygame.Surface((max(2, key[0] * 2), max(2, key[1] * 2)), pygame.SRCALPHA)
        for i in range(6, 0, -1):
            rr = pygame.Rect(0, 0, s.get_width() * i / 6, s.get_height() * i / 6)
            rr.center = (s.get_width() / 2, s.get_height() / 2)
            pygame.draw.ellipse(s, (30, 50, 20, 14), rr)
        SHADOW[key] = s
    return s


# ====================== Entities ======================
class Ent:
    __slots__ = ('type', 'd', 'team', 'x', 'y', 'vx', 'vy', 'kx', 'ky', 'r', 'hp', 'max', 'cd', 'rt',
                 'target', 'face', 'anim', 'flash', 'burn', 'dead', 'stat', 'gen', 'wa', 'lunge', 'ldx', 'ldy')


class Proj:
    __slots__ = ('x', 'y', 'vx', 'vy', 'team', 'dmg', 'life', 'max', 'kind', 'aoe', 'src', 'dead')


class Part:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max', 'r', 'col', 'kind', 'g')


def part(x, y, vx, vy, life, r, col, kind='dot', g=0):
    q = Part()
    q.x, q.y, q.vx, q.vy, q.life, q.max, q.r, q.col, q.kind, q.g = x, y, vx, vy, life, life, r, col, kind, g
    G.parts.append(q)


class Game:
    def __init__(self):
        self.ents = []
        self.projs = []
        self.parts = []
        self.pending = []
        self.texts = []
        self.lakes = []
        self.sparkles = []
        self.corpses = []
        self.nums = []
        self.butterflies = []
        self.clouds = []
        self.paused = False
        self.speed = 1
        self.big = False
        self.tool = 'soldier'
        self.cat = 'army'
        self.shake = 0.0
        self.had_battle = False
        self.hint = True
        self.mobiles = []
        self.grid = {}


G = Game()
CS = 48
W, H = 1280, 800
LG = 6
lake_grid = bytearray()
LGW = LGH = 0


def spawn(t, x, y, **kw):
    d = T[t]
    if d['special'] or len(G.ents) > 2500:
        return None
    e = Ent()
    e.type = t; e.d = d; e.team = t; e.x = x; e.y = y
    e.vx = e.vy = e.kx = e.ky = 0.0
    e.r = d['r'] * (random.uniform(.85, 1.2) if t == 'tree' else 1)
    e.hp = e.max = d['hp']
    e.cd = random.random() * d.get('cd', 1)
    e.rt = 0; e.target = None
    e.face = random.choice((1, -1))
    e.anim = random.random() * 10
    e.flash = 0; e.burn = 0; e.dead = False; e.stat = bool(d['stat']); e.gen = 0
    e.wa = random.random() * TAU
    e.lunge = 0.0; e.ldx = e.ldy = 0.0
    for k, v in kw.items():
        setattr(e, k, v)
    G.ents.append(e)
    return e


# ---------------- lakes ----------------
lake_layers = []
lake_surf = None


def rebuild_lakes():
    global lake_grid, LGW, LGH, lake_layers, lake_surf
    LGW, LGH = W // LG + 2, H // LG + 2
    lake_grid = bytearray(LGW * LGH)
    lake_layers = [pygame.Surface((W, H), pygame.SRCALPHA) for _ in range(5)]
    lake_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    for l in G.lakes:
        stamp_lake(l, compose=False)
    compose_lakes()


def compose_lakes():
    lake_surf.fill((0, 0, 0, 0))
    for L in lake_layers[:4]:
        lake_surf.blit(L, (0, 0))


def stamp_lake(l, compose=True):
    x, y, r = l
    pygame.draw.circle(lake_layers[0], (236, 225, 178, 255), (x, y), r + 14)
    pygame.draw.circle(lake_layers[1], (166, 226, 236, 255), (x, y), r + 6)
    pygame.draw.circle(lake_layers[2], (82, 172, 226, 255), (x, y), r)
    pygame.draw.circle(lake_layers[3], (58, 145, 210, 255), (x, y), max(2, r - 16))
    pygame.draw.circle(lake_layers[4], (255, 255, 255, 255), (x, y), max(2, r - 4))
    x0, x1 = max(0, int((x - r) // LG)), min(LGW - 1, int((x + r) // LG))
    y0, y1 = max(0, int((y - r) // LG)), min(LGH - 1, int((y + r) // LG))
    rr = r * r
    for gy in range(y0, y1 + 1):
        cy = gy * LG + LG / 2 - y
        row = gy * LGW
        for gx in range(x0, x1 + 1):
            cx = gx * LG + LG / 2 - x
            if cx * cx + cy * cy < rr:
                lake_grid[row + gx] = 1
    if compose:
        compose_lakes()


def in_water(x, y):
    gx, gy = int(x // LG), int(y // LG)
    if gx < 0 or gy < 0 or gx >= LGW or gy >= LGH:
        return False
    return lake_grid[gy * LGW + gx] == 1


# ---------------- background ----------------
bg = None
decal = None
vignette = None


def build_background():
    global bg, decal, vignette
    rng = random.Random(7)
    bg = pygame.Surface((W, H))
    bg.fill((205, 228, 176))
    patch = pygame.Surface((W, H), pygame.SRCALPHA)
    for _ in range(int(W * H / 9000)):
        c = rng.choice([(190, 218, 160), (215, 236, 186), (198, 224, 168), (222, 238, 196)])
        rr = rng.randint(30, 110)
        g = glow(c, rr)
        patch.blit(g, (rng.randint(-50, W), rng.randint(-50, H)))
    bg.blit(patch, (0, 0))
    for _ in range(int(W * H / 1800)):
        x, y = rng.randint(0, W), rng.randint(0, H)
        c = rng.choice([(150, 190, 120), (165, 200, 132), (140, 182, 110)])
        for j in range(3):
            pygame.draw.line(bg, c, (x + j * 2, y), (x + j * 2 + rng.randint(-2, 2), y - rng.randint(3, 6)), 1)
    for _ in range(int(W * H / 30000)):
        x, y = rng.randint(0, W), rng.randint(0, H)
        c = rng.choice([(255, 255, 255), (255, 230, 120), (240, 170, 200)])
        pygame.draw.circle(bg, c, (x, y), 2)
        pygame.draw.circle(bg, (250, 220, 90), (x, y), 1)
    decal = pygame.Surface((W, H), pygame.SRCALPHA)
    vignette = pygame.Surface((W, H), pygame.SRCALPHA)
    # simple radial vignette
    vg = pygame.Surface((64, 40), pygame.SRCALPHA)
    for yy in range(40):
        for xx in range(64):
            dx, dy = (xx - 31.5) / 32, (yy - 19.5) / 20
            dd = min(1, math.sqrt(dx * dx + dy * dy))
            vg.set_at((xx, yy), (20, 40, 10, int(70 * max(0, dd - .55) / .45)))
    vignette = pygame.transform.smoothscale(vg, (W, H))
    build_waves()
    build_clouds()
    if not G.butterflies:
        for _ in range(7):
            G.butterflies.append([random.uniform(0, W), random.uniform(0, H), random.random() * TAU, random.random() * 10,
                                  random.choice([(255, 170, 60), (255, 255, 255), (150, 180, 255), (255, 130, 190), (255, 230, 90)])])


wave_tex = None
wave_buf = None


def build_waves():
    global wave_tex, wave_buf
    tw, th = 160, 100
    tile = pygame.Surface((tw, th), pygame.SRCALPHA)
    rng = random.Random(3)
    for _ in range(14):
        x0, y0 = rng.uniform(0, tw), rng.uniform(0, th)
        L = rng.uniform(10, 26)
        for ox in (-tw, 0, tw):
            for oy in (-th, 0, th):
                pts = [(x0 + ox + i * L / 8, y0 + oy + math.sin(i / 8 * PI) * -3) for i in range(9)]
                pygame.draw.lines(tile, (255, 255, 255, 95), False, pts, 2)
    wave_tex = pygame.Surface((W + tw, H + th), pygame.SRCALPHA)
    for yy in range(0, H + th, th):
        for xx in range(0, W + tw, tw):
            wave_tex.blit(tile, (xx, yy))
    wave_buf = pygame.Surface((W, H), pygame.SRCALPHA)


def build_clouds():
    G.clouds = []
    rng = random.Random(11)
    for i in range(5):
        cw, ch = rng.randint(380, 620), rng.randint(200, 320)
        cs = pygame.Surface((cw, ch), pygame.SRCALPHA)
        for _ in range(9):
            rr = rng.randint(60, 120)
            cs.blit(glow((20, 45, 25), rr), (rng.uniform(0, cw - rr * 2), rng.uniform(0, ch - rr * 2)))
        cs.set_alpha(34)
        G.clouds.append([rng.uniform(-cw, W), rng.uniform(-ch / 2, H - ch / 2), cs, rng.uniform(8, 16)])


# ---------------- grid ----------------
def build_grid():
    g = {}
    for e in G.ents:
        if not e.dead:
            k = (int(e.x) // CS, int(e.y) // CS)
            c = g.get(k)
            if c is None:
                g[k] = [e]
            else:
                c.append(e)
    G.grid = g


def around(x, y, rad):
    g = G.grid
    gx0, gx1 = int(x - rad) // CS, int(x + rad) // CS
    gy0, gy1 = int(y - rad) // CS, int(y + rad) // CS
    out = []
    for gy in range(gy0, gy1 + 1):
        for gx in range(gx0, gx1 + 1):
            c = g.get((gx, gy))
            if c:
                out.extend(c)
    return out


def find_target(e):
    best, bd = None, 1e18
    rad = CS * 2
    while rad <= CS * 8 and best is None:
        for o in around(e.x, e.y, rad):
            if o.dead or o.stat or o.team == e.team:
                continue
            dx, dy = o.x - e.x, o.y - e.y
            dd = dx * dx + dy * dy
            if dd < bd:
                bd, best = dd, o
        rad *= 2
    if best is None and G.mobiles:
        for _ in range(40):
            o = random.choice(G.mobiles)
            if o.dead or o.team == e.team:
                continue
            dx, dy = o.x - e.x, o.y - e.y
            dd = dx * dx + dy * dy
            if dd < bd:
                bd, best = dd, o
    return best


# ---------------- combat ----------------
def txt(x, y, s):
    if len(G.texts) < 40:
        G.texts.append([x, y, s, .9])


def damage(t, amt, src=None, kind='melee'):
    if t.dead:
        return
    d = t.d
    if d.get('dodge') and random.random() < d['dodge']:
        if random.random() < .25:
            txt(t.x, t.y - 14, 'החטיא!')
        return
    if d.get('armor'):
        amt *= d['armor']
    if d.get('shield') and kind == 'proj':
        amt *= d['shield']
    t.hp -= amt
    t.flash = .1
    if amt >= 7 and not t.stat and len(G.nums) < 60 and random.random() < .7:
        G.nums.append([t.x + random.uniform(-4, 4), t.y - t.r - 4, int(round(amt)), .8])
    if t.hp <= 0:
        kill(t, src)


def kill(t, src):
    t.dead = True
    d = t.d
    if t.type == 'barrel':
        G.pending.append([.06, t.x, t.y, 75, 45]); return
    if t.type == 'mine':
        G.pending.append([0, t.x, t.y, 55, 60]); return
    if t.type in ('tree', 'rock'):
        c = (74, 122, 58) if t.type == 'tree' else (154, 160, 168)
        if t.burn > 0:
            c = (70, 60, 40)
        for _ in range(9):
            part(t.x, t.y, random.uniform(-70, 70), random.uniform(-100, 30), .7, random.uniform(2, 4.5), c, 'dot', 220)
        part(t.x, t.y, 0, -12, 1.0, t.r * 1.4, (200, 200, 200), 'smoke')
        if t.type == 'tree':
            pygame.draw.circle(decal, (60, 45, 30, 150), (t.x, t.y + t.r * .7), t.r * .32)
            pygame.draw.circle(decal, (110, 80, 50, 160), (t.x, t.y + t.r * .7), t.r * .22)
        else:
            for _ in range(5):
                pygame.draw.circle(decal, (120, 125, 130, 140), (t.x + random.uniform(-t.r, t.r), t.y + random.uniform(-t.r / 2, t.r / 2)), random.uniform(1.5, 3.5))
        return
    for _ in range(int(6 + t.r / 2)):
        part(t.x, t.y, random.uniform(-80, 80), random.uniform(-110, 30), .55, random.uniform(1.8, 3.5), d['c'], 'dot', 320)
    part(t.x, t.y, 0, -15, .7, t.r * 1.3, (255, 255, 255), 'smoke')
    if t.type == 'slime':
        for _ in range(5):
            c = d['c']
            pygame.draw.circle(decal, (c[0], c[1], c[2], 110), (t.x + random.uniform(-t.r, t.r), t.y + random.uniform(-t.r * .5, t.r * .7)), random.uniform(t.r * .2, t.r * .5))
    elif t.type == 'ghost':
        part(t.x, t.y, 0, -40, 1.0, t.r * 1.2, (240, 240, 255), 'smoke')
    elif len(G.corpses) < 260:
        G.corpses.append([t.x, t.y, t.type, t.r, t.face, 3.5, t.kx * .3, t.ky * .3 - 30, 0.0])
    if t.type == 'slime' and t.gen < 2:
        for _ in range(2):
            s = spawn('slime', t.x + random.uniform(-5, 5), t.y + random.uniform(-5, 5), gen=t.gen + 1)
            if s:
                s.r = t.r * .72
                s.hp = s.max = T['slime']['hp'] * (.55 ** s.gen)
                s.kx, s.ky = random.uniform(-80, 80), random.uniform(-80, 80)
    if src is not None and src.type == 'zombie' and not src.dead and not d['fly'] and t.type not in ('golem', 'zombie'):
        z = spawn('zombie', t.x, t.y)
        if z:
            z.flash = .3
            txt(t.x, t.y - 14, 'זומבי!')


def explode(x, y, rad, dmg):
    for _ in range(16):
        a = random.random() * TAU
        s = random.random() * rad * 1.7
        part(x, y, math.cos(a) * s, math.sin(a) * s, random.uniform(.5, .85), random.uniform(rad * .25, rad * .5),
             random.choice([(255, 150, 40), (255, 196, 80), (255, 110, 30)]), 'fire')
    for _ in range(7):
        part(x + random.uniform(-rad / 2, rad / 2), y + random.uniform(-rad / 2, rad / 2), random.uniform(-10, 10), -22,
             random.uniform(1.0, 1.6), rad * .45, (215, 215, 215), 'smoke')
    for _ in range(10):
        a = random.random() * TAU
        part(x, y, math.cos(a) * 300, math.sin(a) * 300, .3, 2, (255, 240, 180), 'spark')
    part(x, y, 0, 0, .3, rad, (255, 245, 210), 'ring')
    part(x, y, 0, 0, .7, rad * 1.5, (200, 185, 150), 'ring')
    for _ in range(8):
        a = random.random() * TAU
        part(x, y, math.cos(a) * random.uniform(80, 200), math.sin(a) * random.uniform(80, 200) - 80, random.uniform(.5, .9),
             random.uniform(1.5, 3), (90, 75, 55), 'dot', 400)
    gsc = glow((70, 60, 30), int(rad * .7))
    gsc.set_alpha(55)
    decal.blit(gsc, (x - rad * .7, y - rad * .7))
    gsc.set_alpha(255)
    G.shake = min(9, G.shake + rad / 22)
    for o in around(x, y, rad + 30):
        if o.dead:
            continue
        dx, dy = o.x - x, o.y - y
        dd = math.hypot(dx, dy)
        if dd > rad + o.r:
            continue
        f = 1 - min(1, dd / (rad + o.r)) * .6
        damage(o, dmg * f, None, 'boom')
        if o.type == 'tree' and random.random() < .6:
            o.burn = 6
        if not o.stat:
            k = 260 * f / (dd or 1)
            o.kx += dx * k
            o.ky += dy * k


def shoot(e, t, kind, dist, dx, dy):
    d = e.d
    if kind in ('bullet', 'arrow'):
        sp = d.get('bs', 380 if kind == 'arrow' else 620)
        a = math.atan2(dy, dx) + random.uniform(-.5, .5) * d.get('spread', .06)
        p = Proj()
        p.x, p.y = e.x + math.cos(a) * e.r, e.y + math.sin(a) * e.r
        p.vx, p.vy = math.cos(a) * sp, math.sin(a) * sp
        p.team, p.dmg, p.life, p.kind, p.src, p.dead, p.aoe = e.team, d['dmg'], (d['range'] + 60) / sp, kind, e, False, 0
        p.max = p.life
        G.projs.append(p)
        if kind == 'bullet':
            part(e.x + math.cos(a) * e.r * 1.9, e.y + math.sin(a) * e.r * 1.9, 0, 0, .07, 5, (255, 220, 110), 'fire')
    elif kind in ('grenade', 'fireball'):
        sp = 260 if kind == 'grenade' else 300
        tx, ty = t.x + random.uniform(-10, 10), t.y + random.uniform(-10, 10)
        dd = max(1, math.hypot(tx - e.x, ty - e.y))
        p = Proj()
        p.x, p.y = e.x, e.y
        p.vx, p.vy = (tx - e.x) / dd * sp, (ty - e.y) / dd * sp
        p.team, p.dmg, p.life, p.kind, p.src, p.dead, p.aoe = e.team, d['dmg'], dd / sp, kind, e, False, d['aoe']
        p.max = p.life
        G.projs.append(p)
    elif kind == 'breath':
        a = math.atan2(dy, dx) + random.uniform(-.22, .22)
        sp = random.uniform(260, 340)
        p = Proj()
        p.x, p.y = e.x + e.face * e.r * 1.3, e.y - e.r * .3
        p.vx, p.vy = math.cos(a) * sp, math.sin(a) * sp
        p.team, p.dmg, p.life, p.kind, p.src, p.dead, p.aoe = e.team, d['dmg'], .5, 'flame', e, False, 0
        p.max = p.life
        G.projs.append(p)


# ---------------- update ----------------
def update(dt):
    build_grid()
    G.mobiles = [e for e in G.ents if not e.dead and not e.stat]
    for p in G.pending:
        p[0] -= dt
    ready = [p for p in G.pending if p[0] <= 0]
    G.pending = [p for p in G.pending if p[0] > 0]
    for p in ready:
        explode(p[1], p[2], p[3], p[4])

    for e in G.ents:
        if e.dead:
            continue
        d = e.d
        e.anim += dt
        if e.flash > 0:
            e.flash -= dt
        wet = in_water(e.x, e.y)
        if e.burn > 0:
            if wet and not d['fly']:
                e.burn = 0
                part(e.x, e.y - 5, 0, -20, .6, e.r, (230, 230, 230), 'smoke')
            else:
                e.burn -= dt
                damage(e, (7 if e.type == 'tree' else 5) * dt, None, 'fire')
                if random.random() < dt * 14:
                    part(e.x + random.uniform(-e.r / 2, e.r / 2), e.y - e.r * .3 + random.uniform(-e.r / 2, e.r / 2),
                         random.uniform(-5, 5), random.uniform(-70, -40), .5, random.uniform(3, 3 + e.r * .4),
                         random.choice([(255, 138, 42), (255, 200, 74)]), 'fire')
                if random.random() < dt * 4:
                    part(e.x + random.uniform(-e.r, e.r), e.y - e.r, random.uniform(-20, 20), random.uniform(-90, -50), 1.0, 1.5, (255, 200, 90), 'spark')
                if e.type == 'tree' and random.random() < dt * 2:
                    part(e.x, e.y - e.r, random.uniform(-6, 6), -30, 1.6, e.r * .7, (120, 115, 110), 'smoke')
                if e.type == 'tree' and random.random() < dt * 1.2:
                    for o in around(e.x, e.y, 45):
                        if o is e or o.dead:
                            continue
                        dd = math.hypot(o.x - e.x, o.y - e.y)
                        if o.type == 'tree' and o.burn <= 0 and dd < 45:
                            o.burn = random.uniform(6, 9)
                        elif o.type == 'barrel' and dd < 35:
                            damage(o, 99)
        if e.stat:
            if e.type == 'mine' and not e.dead:
                for o in around(e.x, e.y, 20):
                    if not e.dead and not o.dead and not o.stat and not o.d['fly'] and math.hypot(o.x - e.x, o.y - e.y) < e.r + o.r + 2:
                        e.dead = True
                        G.pending.append([0, e.x, e.y, 55, 60])
            continue
        e.cd -= dt
        e.rt -= dt
        if e.lunge > 0:
            e.lunge -= dt
        if e.target is None or e.target.dead or e.rt <= 0:
            e.target = find_target(e)
            e.rt = random.uniform(.35, .75)
        t = e.target
        mx = my = 0.0
        if t is not None:
            dx, dy = t.x - e.x, t.y - e.y
            dist = math.hypot(dx, dy) or 1
            if abs(dx) > 2:
                e.face = 1 if dx > 0 else -1
            reach = d['range'] + e.r + t.r
            if dist > reach * .85:
                mx, my = dx / dist, dy / dist
            if dist <= reach and e.cd <= 0:
                e.cd = d['cd'] * random.uniform(.85, 1.15)
                e.lunge = .16
                e.ldx, e.ldy = dx / dist, dy / dist
                if d['atk'] != 'melee':
                    e.ldx, e.ldy = -e.ldx * .4, -e.ldy * .4
                if d['atk'] == 'melee':
                    damage(t, d['dmg'], e, 'melee')
                    if d.get('kb') and not t.stat:
                        t.kx += dx / dist * d['kb']
                        t.ky += dy / dist * d['kb']
                    if e.type == 'bull' and random.random() < .4:
                        txt(t.x, t.y - 14, 'בום!')
                    for _ in range(2):
                        part(t.x - dx / dist * t.r, t.y - dy / dist * t.r, random.uniform(-60, 60), random.uniform(-60, 60), .2, 1.6, (255, 255, 230), 'spark')
                else:
                    shoot(e, t, d['atk'], dist, dx, dy)
        else:
            e.wa += random.uniform(-1.5, 1.5) * dt
            mx, my = math.cos(e.wa) * .25, math.sin(e.wa) * .25
        sp = d['sp']
        if wet and not d['fly']:
            sp *= 1.6 if d['swim'] else .45
        if e.burn > 0:
            sp *= 1.2
        f = min(1, dt * 8)
        e.vx += (mx * sp - e.vx) * f
        e.vy += (my * sp - e.vy) * f
        e.x += (e.vx + e.kx) * dt
        e.y += (e.vy + e.ky) * dt
        kd = .02 ** dt
        e.kx *= kd
        e.ky *= kd
        fly = d['fly']
        for o in around(e.x, e.y, e.r + 30):
            if o is e or o.dead or o.type == 'mine':
                continue
            if fly and o.stat:
                continue
            if o.d['fly'] != fly and not o.stat:
                continue
            dx, dy = e.x - o.x, e.y - o.y
            rr = e.r + o.r
            d2 = dx * dx + dy * dy
            if d2 >= rr * rr or d2 == 0:
                continue
            dd = math.sqrt(d2)
            push = rr - dd
            s = 1 if o.stat else (.25 if o.team == e.team else .5)
            e.x += dx / dd * push * s
            e.y += dy / dd * push * s
        e.x = max(e.r, min(W - e.r, e.x))
        e.y = max(e.r + 4, min(H - e.r, e.y))
        if not fly and not wet and d['sp'] > 55 and abs(e.vx) + abs(e.vy) > 50 and random.random() < dt * 5:
            part(e.x - e.face * e.r * .6, e.y + e.r * .8, -e.vx * .1, -8, .5, e.r * .45, (205, 190, 150), 'smoke')

    for p in G.projs:
        p.life -= dt
        p.x += p.vx * dt
        p.y += p.vy * dt
        if p.kind in ('grenade', 'fireball'):
            if p.kind == 'fireball' and random.random() < dt * 40:
                part(p.x, p.y, 0, -10, .35, 5, (255, 150, 40), 'fire')
            if p.life <= 0:
                p.dead = True
                explode(p.x, p.y, p.aoe, p.dmg)
                if p.kind == 'fireball':
                    for o in around(p.x, p.y, p.aoe):
                        if not o.dead and math.hypot(o.x - p.x, o.y - p.y) < p.aoe and (o.type == 'tree' or not o.stat):
                            o.burn = max(o.burn, 6 if o.type == 'tree' else 2.5)
            continue
        if p.life <= 0 or p.x < -20 or p.y < -20 or p.x > W + 20 or p.y > H + 20:
            p.dead = True
            continue
        for o in around(p.x, p.y, 10):
            if p.dead or o.dead or o.team == p.team or o.type == 'mine':
                continue
            dx, dy = o.x - p.x, o.y - p.y
            rr = o.r + (4 if p.kind == 'flame' else 1)
            if dx * dx + dy * dy > rr * rr:
                continue
            if o.d.get('phase') and p.kind != 'flame' and random.random() < o.d['phase']:
                continue
            p.dead = True
            damage(o, p.dmg, p.src, 'proj')
            if p.kind == 'flame':
                if random.random() < .08 or o.type == 'tree':
                    o.burn = max(o.burn, 6 if o.type == 'tree' else 2)
            else:
                part(p.x, p.y, 0, 0, .12, 5, (255, 230, 140), 'fire')
    G.projs = [p for p in G.projs if not p.dead]

    for q in G.parts:
        q.life -= dt
        q.x += q.vx * dt
        q.y += q.vy * dt
        if q.g:
            q.vy += q.g * dt
        if q.kind == 'fire' or q.kind == 'spark':
            q.vx *= .92
            q.vy *= .92
    G.parts = [q for q in G.parts if q.life > 0]
    if len(G.parts) > 2200:
        G.parts = G.parts[-2200:]
    for s in G.texts:
        s[3] -= dt
        s[1] -= 25 * dt
    G.texts = [s for s in G.texts if s[3] > 0]
    for n in G.nums:
        n[3] -= dt
        n[1] -= 30 * dt
    G.nums = [n for n in G.nums if n[3] > 0]
    for c in G.corpses:
        c[5] -= dt
        c[8] = min(1, c[8] + dt * 7)
        c[0] += c[6] * dt
        c[1] += c[7] * dt
        c[6] *= .02 ** dt
        c[7] = c[7] * .02 ** dt
    G.corpses = [c for c in G.corpses if c[5] > 0]
    for b in G.butterflies:
        b[2] += random.uniform(-2.5, 2.5) * dt
        b[0] += math.cos(b[2]) * 28 * dt
        b[1] += math.sin(b[2]) * 28 * dt
        b[3] += dt
        if b[0] < -20: b[0] = W + 15
        if b[0] > W + 20: b[0] = -15
        if b[1] < -20: b[1] = H + 15
        if b[1] > H + 20: b[1] = -15
    for c in G.clouds:
        c[0] += c[3] * dt
        if c[0] > W + 20:
            c[0] = -c[2].get_width()
            c[1] = random.uniform(-c[2].get_height() / 2, H - c[2].get_height() / 2)
    G.ents = [e for e in G.ents if not e.dead]
    G.shake *= .01 ** dt

    # lake sparkles
    if G.lakes and random.random() < dt * min(30, len(G.lakes) * .8):
        x, y, r = random.choice(G.lakes)
        a = random.random() * TAU
        rr = random.random() * r * .8
        sx, sy = x + math.cos(a) * rr, y + math.sin(a) * rr
        if in_water(sx, sy):
            G.sparkles.append([sx, sy, 1.2, 1.2])
    for s in G.sparkles:
        s[2] -= dt
    G.sparkles = [s for s in G.sparkles if s[2] > 0]


# ====================== Rendering ======================
UI_HITS = []
mouse = [0, 0]
hover_tip = None


def panel(surf, rect, rad=12, col=(255, 255, 255, 235), border=(225, 228, 235), sh=True):
    if sh:
        s = pygame.Surface((rect.w + 16, rect.h + 16), pygame.SRCALPHA)
        for i in range(4):
            pygame.draw.rect(s, (0, 0, 0, 10), pygame.Rect(8 - i * 2 + 2, 8 - i * 2 + 5, rect.w + i * 4 - 4, rect.h + i * 4 - 4), border_radius=rad + i * 2)
        surf.blit(s, (rect.x - 8, rect.y - 8))
    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(s, col, s.get_rect(), border_radius=rad)
    if border:
        pygame.draw.rect(s, border, s.get_rect(), 1, border_radius=rad)
    surf.blit(s, rect.topleft)


def button(surf, rect, label, on=False, cb=None, size=15):
    hov = rect.collidepoint(mouse)
    col = (232, 237, 255, 245) if on else ((246, 247, 251, 245) if hov else (255, 255, 255, 235))
    panel(surf, rect, 10, col, (124, 143, 216) if on else (222, 225, 232), sh=True)
    ts = text(label, size, (40, 44, 60), True)
    surf.blit(ts, ts.get_rect(center=rect.center))
    if cb:
        UI_HITS.append((rect, cb))


def render(screen, t):
    global hover_tip
    UI_HITS.clear()
    hover_tip = None
    ox = oy = 0
    if G.shake > .3:
        ox, oy = random.uniform(-G.shake, G.shake), random.uniform(-G.shake, G.shake)
    screen.blit(bg, (ox, oy))
    screen.blit(decal, (ox, oy))
    if G.lakes:
        screen.blit(lake_surf, (ox, oy))
        if wave_tex is not None:
            off = t * 14
            wave_buf.fill((0, 0, 0, 0))
            wave_buf.blit(wave_tex, (-(off % 160), -((off * .35) % 100)))
            wave_buf.blit(lake_layers[4], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(wave_buf, (ox, oy))
        for s in G.sparkles:
            k = s[2] / s[3]
            a = int(200 * math.sin(k * PI))
            w = 6 + (1 - k) * 6
            ss = pygame.Surface((int(w * 2) + 2, 4), pygame.SRCALPHA)
            pygame.draw.ellipse(ss, (255, 255, 255, a), ss.get_rect())
            screen.blit(ss, (s[0] - w + ox, s[1] + oy))

    for c in G.corpses:
        cs = corpse_sprite(c[2], c[3], c[4])
        a = int(255 * min(1, c[5] / 1.0))
        cs.set_alpha(a)
        screen.blit(cs, (c[0] - cs.get_width() / 2 + ox, c[1] - cs.get_height() / 2 + c[3] * .3 + oy))
        cs.set_alpha(255)

    ents = sorted(G.ents, key=lambda e: (e.type != 'mine', e.d['fly'], e.y))
    # shadows
    for e in ents:
        if e.type == 'mine':
            continue
        if e.d['fly']:
            sh = shadow(e.r * .9, e.r * .3)
            screen.blit(sh, (e.x - sh.get_width() / 2 + ox, e.y + e.r * 1.7 - sh.get_height() / 2 + oy))
        elif not in_water(e.x, e.y):
            sh = shadow(e.r * 1.1, e.r * .42)
            screen.blit(sh, (e.x - sh.get_width() / 2 + ox, e.y + e.r * .95 - sh.get_height() / 2 + oy))
    for e in ents:
        d = e.d
        fr = 0
        if e.type in ANIM:
            rate = {'bee': 30, 'cavalry': 7, 'dragon': 3, 'slime': 3, 'ghost': 2, 'mine': 1.2}[e.type]
            fr = int(e.anim * rate) % 2
        bob = 0
        if not e.stat:
            if d['fly']:
                bob = math.sin(e.anim * 4) * 2.5 - 4
            elif abs(e.vx) + abs(e.vy) > 5:
                bob = -abs(math.sin(e.anim * 12)) * 2.2
        spr = sprite(e.type, e.r, e.face if not e.stat else 1, fr, e.flash > 0, e.type == 'tree' and e.burn > 0)
        sw, sh_ = spr.get_width(), spr.get_height()
        lx = ly = 0
        if e.lunge > 0:
            lk = math.sin(max(0, e.lunge) / .16 * PI) * e.r * .55
            lx, ly = e.ldx * lk, e.ldy * lk
        if e.stat and e.burn > 0:
            lx = math.sin(t * 30 + e.x) * .8
        px, py = e.x - sw / 2 + ox + lx, e.y + bob - sh_ / 2 + oy + ly
        if not d['fly'] and not e.stat and in_water(e.x, e.y):
            cut = int(sh_ / 2 + e.r * .45)
            screen.blit(spr, (px, py + 2), pygame.Rect(0, 0, sw, cut))
            rs = pygame.Surface((int(e.r * 2.6), int(e.r * .8)), pygame.SRCALPHA)
            pygame.draw.ellipse(rs, (255, 255, 255, 150), rs.get_rect(), 2)
            screen.blit(rs, (e.x - e.r * 1.3 + ox, e.y + e.r * .45 - e.r * .4 + 2 + oy))
        else:
            screen.blit(spr, (px, py))
        if not e.stat and e.hp < e.max:
            w = max(14, e.r * 2)
            bx, by = e.x - w / 2 + ox, e.y - e.r - 10 + bob + oy
            if e.type == 'dragon':
                by -= 14
            pygame.draw.rect(screen, (40, 40, 40), (bx - 1, by - 1, w + 2, 5), border_radius=2)
            fr_ = max(0, e.hp / e.max)
            c = (90, 210, 90) if fr_ > .5 else ((240, 190, 50) if fr_ > .25 else (235, 70, 60))
            pygame.draw.rect(screen, c, (bx, by, w * fr_, 3), border_radius=2)

    for p in G.projs:
        x, y = p.x + ox, p.y + oy
        if p.kind == 'bullet':
            l = math.hypot(p.vx, p.vy)
            ux, uy = p.vx / l, p.vy / l
            if len(G.projs) < 350:
                g = glow((255, 220, 120), 6)
                screen.blit(g, (x - 6, y - 6))
            pygame.draw.line(screen, (255, 235, 160), (x - ux * 12, y - uy * 12), (x, y), 2)
            pygame.draw.circle(screen, (255, 250, 220), (x, y), 1.6)
        elif p.kind == 'arrow':
            l = math.hypot(p.vx, p.vy)
            ux, uy = p.vx / l, p.vy / l
            pygame.draw.line(screen, (107, 74, 43), (x, y), (x - ux * 13, y - uy * 13), 2)
            pygame.draw.line(screen, (230, 230, 230), (x - ux * 11, y - uy * 11), (x - ux * 14 - uy * 2, y - uy * 14 + ux * 2), 2)
            pygame.draw.circle(screen, (90, 90, 90), (x, y), 1.5)
        elif p.kind == 'grenade':
            k = 1 - p.life / p.max
            hgt = math.sin(k * PI) * 32
            sh = shadow(4, 2)
            screen.blit(sh, (x - 4, y - 2))
            pygame.draw.circle(screen, (20, 20, 20), (x, y - hgt), 5)
            pygame.draw.circle(screen, (61, 74, 42), (x, y - hgt), 4)
        elif p.kind == 'fireball':
            g = glow((255, 140, 40), 16)
            screen.blit(g, (x - 16, y - 16))
            pygame.draw.circle(screen, (255, 150, 50), (x, y), 6)
            pygame.draw.circle(screen, (255, 240, 160), (x, y), 3)
        elif p.kind == 'flame':
            k = p.life / p.max
            rr = 5 + (1 - k) * 10
            g = glow((255, 210, 80) if k > .55 else (255, 110, 30), rr * 1.6)
            g.set_alpha(int(255 * min(1, k * 1.6)))
            screen.blit(g, (x - g.get_width() / 2, y - g.get_height() / 2))
            g.set_alpha(255)

    for q in G.parts:
        k = q.life / q.max
        x, y = q.x + ox, q.y + oy
        if q.kind == 'dot':
            pygame.draw.circle(screen, q.col, (x, y), max(1, q.r * min(1, k * 2)))
        elif q.kind == 'fire':
            rr = q.r * (.7 + k * .6) * 1.6
            g = glow(q.col, rr)
            g.set_alpha(int(255 * min(1, k * 1.7)))
            screen.blit(g, (x - g.get_width() / 2, y - g.get_height() / 2))
            g.set_alpha(255)
        elif q.kind == 'smoke':
            rr = q.r * (1.5 - k * .5)
            g = glow(q.col, rr)
            g.set_alpha(int(170 * k))
            screen.blit(g, (x - g.get_width() / 2, y - g.get_height() / 2))
            g.set_alpha(255)
        elif q.kind == 'spark':
            pygame.draw.line(screen, q.col, (x, y), (x - q.vx * .02, y - q.vy * .02), 2)
        elif q.kind == 'ring':
            rr = int(q.r * (1.25 - k * .7))
            s = pygame.Surface((rr * 2 + 6, rr * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (q.col[0], q.col[1], q.col[2], int(220 * k)), (rr + 3, rr + 3), rr, 3)
            screen.blit(s, (x - rr - 3, y - rr - 3))

    for s in G.texts:
        ts = text(s[2], 15, (40, 40, 40), True, (255, 255, 255), 2)
        ts.set_alpha(int(255 * min(1, s[3] * 2)))
        screen.blit(ts, ts.get_rect(center=(s[0] + ox, s[1] + oy)))
        ts.set_alpha(255)

    for n in G.nums:
        v = n[2]
        col = (255, 255, 255) if v < 15 else ((255, 214, 80) if v < 30 else (255, 110, 70))
        ts = text(str(v), 12 if v < 15 else (15 if v < 30 else 18), col, True, (40, 30, 30), 2)
        ts.set_alpha(int(255 * min(1, n[3] * 2.5)))
        screen.blit(ts, ts.get_rect(center=(n[0] + ox, n[1] + oy)))
        ts.set_alpha(255)

    for b in G.butterflies:
        fl = abs(math.sin(b[3] * 14)) * 4 + 1
        x, y = b[0], b[1] + math.sin(b[3] * 3) * 3
        pygame.draw.ellipse(screen, b[4], (x - fl - 1, y - 3, fl, 5))
        pygame.draw.ellipse(screen, b[4], (x + 1, y - 3, fl, 5))
        pygame.draw.line(screen, (60, 50, 40), (x, y - 2), (x, y + 2), 1)

    for c in G.clouds:
        screen.blit(c[2], (c[0], c[1]))

    screen.blit(vignette, (0, 0))

    # brush cursor
    if not over_ui(mouse) and pygame.mouse.get_focused():
        rr = 32 if G.tool == 'eraser' else (44 if G.big else 28) if G.tool == 'lake' else (32 if G.big else 12)
        s = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (124, 143, 216, 40), (rr + 2, rr + 2), rr)
        pygame.draw.circle(s, (90, 110, 200, 170), (rr + 2, rr + 2), rr, 2)
        screen.blit(s, (mouse[0] - rr - 2, mouse[1] - rr - 2))

    draw_ui(screen, t)


DOCK_RECT = pygame.Rect(0, 0, 0, 0)
STATS_RECT = pygame.Rect(0, 0, 0, 0)
TOP_RECTS = []


def over_ui(pos):
    if DOCK_RECT.collidepoint(pos) or STATS_RECT.collidepoint(pos):
        return True
    return any(r.collidepoint(pos) for r in TOP_RECTS)


def set_cat(c):
    G.cat = c
    tools = [k for k in T if T[k]['cat'] == c]
    if G.tool not in tools:
        G.tool = tools[0]


def draw_ui(screen, t):
    global DOCK_RECT, STATS_RECT, TOP_RECTS, hover_tip
    # Title
    title1 = text('מלחמת ', 34, (255, 255, 255), True, (34, 34, 34), 3)
    title2 = text('שרבוטים', 34, (255, 207, 58), True, (34, 34, 34), 3)
    tw = title1.get_width() + title2.get_width()
    tx = W / 2 - tw / 2
    ty = 10 + math.sin(t * 1.6) * 1.5
    tsh = glow((0, 30, 0), 60)
    tsh.set_alpha(60)
    screen.blit(pygame.transform.smoothscale(tsh, (int(tw + 60), 60)), (tx - 30, ty - 8))
    tsh.set_alpha(255)
    screen.blit(title2, (tx, ty))
    screen.blit(title1, (tx + title2.get_width(), ty))

    # Top buttons (right side)
    TOP_RECTS = []
    labels = [
        ('נקה', clear_all, False),
        ('מברשת: ' + ('גדולה' if G.big else 'רגילה'), toggle_brush, G.big),
        ('מהירות x' + (str(G.speed) if G.speed != .5 else '0.5'), cycle_speed, G.speed != 1),
        ('המשך' if G.paused else 'השהה', toggle_pause, G.paused),
    ]
    x = W - 12
    for lab, cb, on in labels:
        ts = text(lab, 15, (40, 44, 60), True)
        w = ts.get_width() + 26
        r = pygame.Rect(x - w, 12, w, 36)
        button(screen, r, lab, on, cb)
        TOP_RECTS.append(r)
        x -= w + 8
    # pause overlay
    if G.paused:
        ts = text('מושהה', 22, (255, 255, 255), True, (34, 34, 34), 2)
        screen.blit(ts, ts.get_rect(center=(W / 2, 70)))

    # Dock
    tools = [k for k in T if T[k]['cat'] == G.cat]
    bw, bh, gap = 58, 54, 6
    tw_ = len(tools) * (bw + gap) - gap + 16
    tabw = [text(n, 15, (0, 0, 0), True).get_width() + 26 for _, n in CATS]
    tabsw = sum(tabw) + 6 * (len(CATS) - 1) + 12
    dw = max(tw_, tabsw)
    dx = W / 2 - dw / 2
    dy = H - bh - 16 - 46
    DOCK_RECT = pygame.Rect(dx, dy, dw, bh + 16 + 46)
    # tabs (RTL order: first category on the right)
    tabs_rect = pygame.Rect(W / 2 - tabsw / 2, dy, tabsw, 38)
    panel(screen, tabs_rect, 12)
    xx = tabs_rect.right - 6
    for (k, n), w in zip(CATS, tabw):
        r = pygame.Rect(xx - w, dy + 5, w, 28)
        on = k == G.cat
        if on:
            pygame.draw.rect(screen, (232, 236, 250), r, border_radius=8)
        elif r.collidepoint(mouse):
            pygame.draw.rect(screen, (244, 245, 249), r, border_radius=8)
        ts = text(n, 15, (30, 30, 40) if on else (130, 132, 145), True)
        screen.blit(ts, ts.get_rect(center=r.center))
        UI_HITS.append((r, (lambda kk=k: set_cat(kk))))
        xx -= w + 6
    tools_rect = pygame.Rect(W / 2 - tw_ / 2, dy + 46, tw_, bh + 16)
    panel(screen, tools_rect, 14)
    xx = tools_rect.right - 8
    for i, k in enumerate(tools):
        r = pygame.Rect(xx - bw, tools_rect.y + 8, bw, bh)
        on = k == G.tool
        hov = r.collidepoint(mouse)
        if on:
            pygame.draw.rect(screen, (235, 239, 252), r, border_radius=10)
            pygame.draw.rect(screen, (124, 143, 216), r, 2, border_radius=10)
        elif hov:
            pygame.draw.rect(screen, (244, 245, 249), r, border_radius=10)
        ic = icon(k, 44)
        lift = (-3 - abs(math.sin(t * 5)) * 2.5) if on else (-3 if hov else 0)
        screen.blit(ic, ic.get_rect(center=(r.centerx, r.centery + lift)))
        num = text(str(i + 1), 10, (170, 172, 185), True)
        screen.blit(num, (r.right - num.get_width() - 4, r.bottom - num.get_height() - 1))
        UI_HITS.append((r, (lambda kk=k: setattr(G, 'tool', kk))))
        if hov:
            dd = T[k]
            sub = None
            if not dd['stat'] and not dd['special']:
                sub = 'חיים ' + str(dd['hp']) + ' · נזק ' + (str(dd['dmg']) if dd['dmg'] >= 1 else str(dd['dmg']))
            hover_tip = (dd['name'], r.centerx, r.y - 8, sub)
        xx -= bw + gap

    # Stats
    cnt = {}
    for e in G.ents:
        if e.type != 'mine':
            cnt[e.type] = cnt.get(e.type, 0) + 1
    arr = sorted(cnt.items(), key=lambda kv: -kv[1])
    if arr:
        rows = arr[:8]
        hgt = len(rows) * 24 + 14 + (20 if len(arr) > 8 else 0)
        STATS_RECT = pygame.Rect(12, H - hgt - 12, 170, hgt)
        panel(screen, STATS_RECT, 12)
        yy = STATS_RECT.y + 8
        total = sum(v for _, v in arr) or 1
        for k, v in rows:
            ic = icon(k, 22)
            screen.blit(ic, ic.get_rect(center=(STATS_RECT.right - 20, yy + 11)))
            nm = text(T[k]['name'], 14, (100, 104, 115))
            screen.blit(nm, (STATS_RECT.right - 36 - nm.get_width(), yy + 3))
            ns = text(str(v), 14, (30, 30, 40), True)
            screen.blit(ns, (STATS_RECT.x + 12, yy + 3))
            yy += 24
        if len(arr) > 8:
            more = text('+' + str(len(arr) - 8), 13, (150, 150, 160))
            screen.blit(more, (STATS_RECT.x + 12, yy))
    else:
        STATS_RECT = pygame.Rect(0, 0, 0, 0)

    # winner
    fighters = [k for k, v in arr if not T[k]['stat']]
    if len(fighters) > 1:
        G.had_battle = True
    if not fighters:
        G.had_battle = False
    if len(fighters) == 1 and G.had_battle:
        ts = text(T[fighters[0]]['name'] + ' ניצחו!', 24, (255, 255, 255), True)
        ic = icon(fighters[0], 34)
        w = ts.get_width() + ic.get_width() + 44
        r = pygame.Rect(W / 2 - w / 2, 60, w, 50)
        pulse = 1 + math.sin(t * 4) * .03
        panel(screen, r.inflate(int(w * (pulse - 1)), 0), 25, (40, 42, 58, 240), None)
        screen.blit(ts, (r.x + 18, r.centery - ts.get_height() / 2))
        screen.blit(ic, ic.get_rect(center=(r.right - 26, r.centery)))

    # power bar
    if len(fighters) > 1:
        tot = sum(cnt[k] * T[k]['hp'] for k in fighters) or 1
        bw_, bh_ = min(420, W * .35), 10
        bx = W / 2 - bw_ / 2
        by = 58
        panel(screen, pygame.Rect(bx - 4, by - 4, bw_ + 8, bh_ + 8), 9, (255, 255, 255, 220), None)
        bar = pygame.Surface((int(bw_), bh_), pygame.SRCALPHA)
        xx = 0.0
        for k in sorted(fighters, key=lambda k: -cnt[k] * T[k]['hp']):
            w = cnt[k] * T[k]['hp'] / tot * bw_
            c = T[k]['c']
            if c[0] > 235 and c[1] > 235:
                c = (200, 200, 210, 255)
            pygame.draw.rect(bar, c, (int(xx), 0, int(math.ceil(w)), bh_))
            pygame.draw.rect(bar, mix(c, WHITE, .35), (int(xx), 0, int(math.ceil(w)), 3))
            xx += w
        mask = pygame.Surface((int(bw_), bh_), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=5)
        bar.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(bar, (bx, by))
        lab = text('מאזן כוחות', 11, (90, 100, 90), True)
        screen.blit(lab, lab.get_rect(midtop=(W / 2, by + bh_ + 5)))

    # hint
    if G.hint and not G.ents:
        l1 = text('בחרו יחידה למטה, וציירו אותה על המסך', 22, (90, 110, 80), True)
        l2 = text('כל סוג יחידה נלחם בכל השאר — מי ישרוד?', 18, (110, 130, 100))
        l3 = text('קליק ימני = מחק · רווח = השהה · 1-9 = בחירת יחידה', 14, (130, 150, 120))
        cy = H * .42
        for i, l in enumerate((l1, l2, l3)):
            screen.blit(l, l.get_rect(center=(W / 2, cy + i * 34)))

    if hover_tip:
        ts = text(hover_tip[0], 14, (255, 255, 255), True)
        sub = text(hover_tip[3], 11, (180, 185, 205)) if hover_tip[3] else None
        w = max(ts.get_width(), sub.get_width() if sub else 0) + 18
        h = ts.get_height() + (sub.get_height() if sub else 0) + 10
        bgr = pygame.Rect(0, 0, w, h)
        bgr.midbottom = (hover_tip[1], hover_tip[2])
        panel(screen, bgr, 8, (34, 36, 48, 245), None)
        pygame.draw.polygon(screen, (34, 36, 48), [(bgr.centerx - 5, bgr.bottom), (bgr.centerx + 5, bgr.bottom), (bgr.centerx, bgr.bottom + 5)])
        screen.blit(ts, ts.get_rect(midtop=(bgr.centerx, bgr.y + 5)))
        if sub:
            screen.blit(sub, sub.get_rect(midtop=(bgr.centerx, bgr.y + 5 + ts.get_height())))


# ====================== Actions ======================
def clear_all():
    G.ents.clear(); G.projs.clear(); G.parts.clear(); G.pending.clear(); G.lakes.clear(); G.sparkles.clear()
    G.corpses.clear(); G.nums.clear(); G.texts.clear()
    G.had_battle = False
    decal.fill((0, 0, 0, 0))
    rebuild_lakes()


def toggle_brush():
    G.big = not G.big


def cycle_speed():
    G.speed = {1: 2, 2: 4, 4: .5, .5: 1}[G.speed]


def toggle_pause():
    G.paused = not G.paused


def brush_at(x, y, tool=None):
    tool = tool or G.tool
    if tool == 'eraser':
        for e in G.ents:
            if math.hypot(e.x - x, e.y - y) < 32 + e.r * .5:
                e.dead = True
        G.ents = [e for e in G.ents if not e.dead]
        n = len(G.lakes)
        G.lakes = [l for l in G.lakes if math.hypot(l[0] - x, l[1] - y) >= l[2] + 20]
        if len(G.lakes) != n:
            rebuild_lakes()
        return
    G.hint = False
    if tool == 'lake':
        l = (int(x), int(y), 44 if G.big else 28)
        G.lakes.append(l)
        stamp_lake(l)
        return
    d = T[tool]
    n = (1 if d['r'] > 20 else 3 if d['r'] > 11 else 5) if G.big else 1
    for _ in range(n):
        a = random.random() * TAU
        rr = random.random() * 30 if G.big else 0
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr
        if d['stat'] and any(e.stat and math.hypot(e.x - px, e.y - py) < (e.r + d['r']) * .8 for e in G.ents):
            continue
        e = spawn(tool, px + random.uniform(-1.5, 1.5), py + random.uniform(-1.5, 1.5))
        if e:
            part(px, py + e.r * .6, 0, -8, .35, e.r * .9, (255, 255, 255), 'smoke')


def spacing(tool):
    if tool == 'eraser':
        return 14
    if tool == 'lake':
        return 16 if G.big else 10
    d = T[tool]
    return max(9, d['r'] * (1.7 if d['stat'] else 2.1)) * (1.6 if G.big else 1)


# ====================== Main ======================
def main():
    global W, H, mouse
    pygame.init()
    pygame.display.set_caption('מלחמת שרבוטים — Doodle War')
    info = pygame.display.Info()
    W = min(1400, max(900, info.current_w - 100)) if info.current_w > 0 else 1280
    H = min(860, max(600, info.current_h - 140)) if info.current_h > 0 else 800
    screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    build_background()
    rebuild_lakes()
    pygame.mouse.set_visible(True)

    drawing = None  # tool used for current stroke
    last = None
    acc = 0.0
    fullscreen = False
    t = 0.0
    while True:
        dt = min(.05, clock.tick(60) / 1000)
        t += dt
        mouse = list(pygame.mouse.get_pos())
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); return
            elif ev.type == pygame.VIDEORESIZE and not fullscreen:
                W, H = max(640, ev.w), max(480, ev.h)
                screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
                build_background(); rebuild_lakes()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); return
                elif ev.key == pygame.K_SPACE:
                    toggle_pause()
                elif ev.key == pygame.K_c:
                    clear_all()
                elif ev.key == pygame.K_b:
                    toggle_brush()
                elif ev.key == pygame.K_s:
                    cycle_speed()
                elif ev.key == pygame.K_TAB:
                    ks = [k for k, _ in CATS]
                    set_cat(ks[(ks.index(G.cat) + 1) % len(ks)])
                elif ev.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((1280, 800), pygame.RESIZABLE)
                    W, H = screen.get_size()
                    build_background(); rebuild_lakes()
                elif pygame.K_1 <= ev.key <= pygame.K_9:
                    tools = [k for k in T if T[k]['cat'] == G.cat]
                    i = ev.key - pygame.K_1
                    if i < len(tools):
                        G.tool = tools[i]
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 3):
                if ev.button == 1:
                    hit = next((cb for r, cb in UI_HITS if r.collidepoint(ev.pos)), None)
                    if hit:
                        hit(); continue
                if over_ui(ev.pos):
                    continue
                drawing = 'eraser' if ev.button == 3 else G.tool
                last = ev.pos
                acc = 0.0
                brush_at(ev.pos[0], ev.pos[1], drawing)
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button in (1, 3):
                drawing = None
            elif ev.type == pygame.MOUSEMOTION and drawing:
                p = ev.pos
                dx, dy = p[0] - last[0], p[1] - last[1]
                dist = math.hypot(dx, dy)
                s = spacing(drawing)
                tt = s - acc
                while tt <= dist:
                    brush_at(last[0] + dx * tt / dist, last[1] + dy * tt / dist, drawing)
                    tt += s
                acc = (acc + dist) % s if dist < s else dist - (tt - s)
                last = p
        if not G.paused:
            remaining = dt * G.speed
            while remaining > 1e-6:
                step = min(1 / 40, remaining)
                update(step)
                remaining -= step
        render(screen, t)
        pygame.display.flip()


if __name__ == '__main__':
    main()