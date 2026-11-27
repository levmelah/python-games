"""
חתול צוללן + חתול טייס + חתול אסטרונאוט  —  גרסת פייתון
==========================================================
בהתחלה בוחרים שפה (עברית, ערבית, רוסית, אנגלית), לוחצים "שחקו!", ובוחרים דמות: חתול, כלב, ארנב או צב.
הפעלה:
    pip install pygame
    python diving_cat.py

שליטה: חיצים או WASD, או לחיצה ממושכת עם העכבר לכיוון שאליו רוצים להגיע.
L = יומן תגליות   ·   Esc = סגירת חלון / יציאה לתפריט
"""
import json
import math
import os
import random
import re

import pygame as pg

# ---------------------------------------------------------------- basics
W, H = 960, 640
PX = 8                      # pixels per metre
FLOOR = 1000 * PX           # sea floor (stage 1)
CEIL = -1000 * PX           # top of space (stage 2)
MOON = 1000 * PX            # moon surface (stage 3)
TAU = math.tau
SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diving_cat_save.json")


def clamp(v, a, b):
    return a if v < a else b if v > b else v


def lerp(a, b, t):
    return a + (b - a) * t


def rnd(a, b):
    return random.uniform(a, b)


def hx(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, a):
    f, t = (255 if a > 0 else 0), abs(a)
    return tuple(int(v + (f - v) * t) for v in c[:3])


def mix(c0, c1, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c0, c1))


def quad(p0, p1, p2, n=10):
    out = []
    for i in range(1, n + 1):
        t = i / n
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return out


def cubic(p0, p1, p2, p3, n=14):
    out = []
    for i in range(1, n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def rot(pts, a, ox=0, oy=0):
    c, s = math.cos(a), math.sin(a)
    return [(ox + x * c - y * s, oy + x * s + y * c) for x, y in pts]


# ---------------------------------------------------------------- Hebrew text
try:
    from bidi.algorithm import get_display as _bidi
except Exception:
    _bidi = None
_LTR = re.compile(r"[0-9A-Za-z][0-9A-Za-z.,:/%\-–]*[0-9A-Za-z%]|[0-9A-Za-z]")
_MIRROR = str.maketrans("()[]{}<>", ")(][}{><")


def heb(s):
    """Turn logical Hebrew text into display order (pygame draws left to right)."""
    if _bidi:
        return _bidi(s)
    r = s[::-1].translate(_MIRROR)
    return _LTR.sub(lambda m: m.group(0)[::-1], r)


_FONTS = {}
FONT_SETS = {
    "he": "arialhebrew,arial,segoeui,tahoma,arialunicodems,dejavusans,notosanshebrew,freesans",
    "ar": "tahoma,arial,segoeui,geezapro,arialunicodems,dejavusans,notosansarabic,notonaskharabic,freesans",
    "ru": "arial,segoeui,tahoma,helvetica,dejavusans,notosans,freesans",
    "en": "arial,segoeui,tahoma,helvetica,dejavusans,notosans,freesans",
}


PROBE = {"he": "אבג", "ar": "\uFE8D\uFEDF\uFEFB\uFE91", "ru": "Жя", "en": "Ag"}
_FONT_PATH = {}


def font_path(lang, bold):
    """First installed font from the list that really has this language's letters."""
    key = (lang, bold)
    if key not in _FONT_PATH:
        chosen = None
        for name in FONT_SETS[lang].split(","):
            path = pg.font.match_font(name, bold=bold)
            if not path:
                continue
            try:
                f = pg.font.Font(path, 20)
                missing = f.metrics("\uE000")[0]
                if all(m is not None and m != missing for m in f.metrics(PROBE[lang])):
                    chosen = path
                    break
            except Exception:
                pass
        _FONT_PATH[key] = chosen
    return _FONT_PATH[key]


def font(size, bold=False, lang=None):
    lang = lang or LANG
    key = (size, bold, lang)
    if key not in _FONTS:
        path = font_path(lang, bold) or font_path(lang, False)
        if path:
            f = pg.font.Font(path, size)
            if bold and "bold" not in os.path.basename(path).lower() and "bd" not in os.path.basename(path).lower():
                f.set_bold(True)
        else:
            f = pg.font.SysFont(FONT_SETS[lang], size, bold=bold)
        _FONTS[key] = f
    return _FONTS[key]


def text(surf, s, size, col, pos, anchor="topright", bold=False, shadow=True, alpha=255, lang=None):
    f = font(size, bold, lang)
    shown = shape(s, lang)
    img = f.render(shown, True, col)
    r = img.get_rect(**{anchor: pos})
    if shadow:
        sh = f.render(shown, True, (0, 0, 0))
        sh.set_alpha(int(110 * alpha / 255))
        surf.blit(sh, r.move(1, 2))
    if alpha < 255:
        img.set_alpha(alpha)
    surf.blit(img, r)
    return r


def wrap(s, size, maxw, bold=False, lang=None):
    f, lines, cur = font(size, bold, lang), [], ""
    for w in s.split(" "):
        t = (cur + " " + w).strip()
        if f.size(shape(t, lang))[0] > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- drawing canvas
class P:
    """Small drawing surface with a local origin, a zoom and 2x supersampling for smooth edges."""

    def __init__(self, w, h, cx, cy, z=1.0, k=2):
        self.w, self.h, self.cx, self.cy, self.z, self.k = int(w), int(h), cx, cy, z, k
        self.s = pg.Surface((self.w * k, self.h * k), pg.SRCALPHA)

    def pt(self, x, y):
        return ((self.cx + x * self.z) * self.k, (self.cy + y * self.z) * self.k)

    def ell(self, c, x, y, rx, ry, width=0):
        rx, ry = abs(rx) * self.z * self.k, abs(ry) * self.z * self.k
        r = pg.Rect(0, 0, max(1, 2 * rx), max(1, 2 * ry))
        r.center = self.pt(x, y)
        pg.draw.ellipse(self.s, c, r, max(1, int(width * self.z * self.k)) if width else 0)

    def circ(self, c, x, y, r, width=0):
        self.ell(c, x, y, r, r, width)

    def rell(self, c, x, y, rx, ry, a):
        pts = [(rx * math.cos(i / 20 * TAU), ry * math.sin(i / 20 * TAU)) for i in range(20)]
        self.poly(c, rot(pts, a, x, y))

    def poly(self, c, pts):
        if len(pts) >= 3:
            pg.draw.polygon(self.s, c, [self.pt(x, y) for x, y in pts])

    def line(self, c, pts, w):
        q = [self.pt(x, y) for x, y in pts]
        ww = max(1, int(w * self.z * self.k))
        pg.draw.lines(self.s, c, False, q, ww)
        if ww > 2:
            for p in q:
                pg.draw.circle(self.s, c, p, ww / 2)

    def arc(self, c, x, y, r, a0, a1, w, n=16):
        self.line(c, [(x + r * math.cos(lerp(a0, a1, i / n)), y + r * math.sin(lerp(a0, a1, i / n))) for i in range(n + 1)], w)

    def rect(self, c, x, y, w, h, rad=0):
        x0, y0 = self.pt(x, y)
        pg.draw.rect(self.s, c, pg.Rect(x0, y0, w * self.z * self.k, h * self.z * self.k), border_radius=int(rad * self.z * self.k))

    def layer(self, fn, alpha):
        q = P(self.w, self.h, self.cx, self.cy, self.z, self.k)
        fn(q)
        q.s.set_alpha(alpha)
        self.s.blit(q.s, (0, 0))

    def done(self):
        return pg.transform.smoothscale(self.s, (self.w, self.h))


def eye(p, x, y, r, iris=(17, 17, 17)):
    p.circ((255, 255, 255), x, y, r)
    p.circ(iris, x + r * .3, y, r * .58)
    p.circ((255, 255, 255), x + r * .5, y - r * .35, r * .22)


def fish(p, x, y, L, h, body, fin, ph):
    w = math.sin(ph) * h * .35
    p.poly(fin, [(x - L * .5, y), (x - L, y - h * .95 + w), (x - L * .86, y + w * .4), (x - L, y + h * .95 + w)])
    p.poly(fin, [(x - L * .25, y - h * .6)] + quad((x - L * .25, y - h * .75), (x, y - h * 1.55), (x + L * .22, y - h * .8)))
    p.ell(body, x, y, L * .62, h)
    p.ell(shade(body, -.22), x, y - h * .42, L * .5, h * .5)
    p.ell(shade(body, .5), x + L * .05, y + h * .42, L * .46, h * .45)
    p.arc(shade(body, -.35), x + L * .3, y, h * .7, -1.1, 1.1, max(.8, h * .12))


# ---------------------------------------------------------------- sea sprites (all face right)
def d_reef(p, t, off):
    for ox, oy, ph, body, fin in off:
        fish(p, ox, oy + math.sin(t + ph) * 2, 14, 5, body, fin, t * 2 + ph)
        eye(p, ox + 5, oy - 1 + math.sin(t + ph) * 2, 1.7)


def d_clown(p, t):
    fish(p, 0, 0, 22, 10, hx("#ff7b1c"), hx("#ff9a3c"), t)
    for x in (5.2, -5.8):
        p.ell((26, 26, 26), x, 0, 3.3, 9.3)
        p.ell((255, 255, 255), x, 0, 2.5, 9)
    eye(p, 9, -2, 2.6)


def d_seahorse(p, t):
    f = math.sin(t) * .4
    p.poly(hx("#ffd98c"), rot([(0, 0), (-8, -4), (-8, 5)], f, -7, 0))
    c, d = hx("#f5b62a"), hx("#d28b12")
    p.line(hx("#e8a21c"), [(-1, 12)] + quad((-1, 12), (-7, 30), (3, 32)) + quad((3, 32), (12, 32), (10, 25)) + quad((10, 25), (8, 20), (3, 23)), 5)
    p.rell(c, 0, 2, 8, 15, .22)
    for i in range(-2, 4):
        p.line(d, [(-5, i * 4 + 2), (5, i * 4 + 3)], 1.2)
    p.ell(c, 1, -16, 7.5, 7)
    p.rell(c, 12, -13, 7, 2.8, .25)
    p.poly(c, [(-4, -21), (-2, -28), (1, -22), (3, -27), (5, -21)])
    eye(p, 3, -17, 2.3)


def d_turtle(p, t):
    f = math.sin(t)
    fl = hx("#5c9e5a")
    for s in (1, -1):
        p.rell(fl, -22 - 6 * math.cos(.6 * s), 10 * s, 10, 4, (.6 + f * .2) * s)
        p.rell(fl, 14 + 13 * math.cos(.9), 12 * s + 13 * math.sin(.9 + f * .5) * s, 18, 6, (.9 + f * .5) * s)
    p.ell(hx("#6fb36a"), 36, 0, 11, 8)
    eye(p, 40, -2, 2.4)
    p.ell(hx("#4f4220"), 0, 0, 30, 20)
    p.ell(hx("#7a6834"), -1, -1.5, 28, 17.5)
    for x, y, rx, ry in ((0, 0, 9, 7), (-14, -8, 6, 5), (-14, 8, 6, 5), (14, -8, 6, 5), (14, 8, 6, 5), (-22, 0, 4, 5), (22, 0, 4, 5)):
        p.ell(hx("#9a8644"), x, y, rx, ry)


def d_dolphin(p, t):
    k = math.sin(t) * .35
    top, mid, bel = hx("#6f8ea6"), hx("#88a6bc"), hx("#dbe7ef")
    tail = [(0, 0)] + quad((0, 0), (-10, -6), (-20, -16)) + quad((-20, -16), (-14, -2), (-8, 0)) + quad((-8, 0), (-14, 2), (-20, 16)) + quad((-20, 16), (-10, 6), (0, 0))
    p.poly(top, rot(tail, k, -48, 0))
    p.poly(top, [(-4, -13)] + quad((-4, -13), (-12, -26), (-20, -29)) + quad((-20, -29), (-18, -18), (-22, -11)))
    body = [(50, 3)] + quad((50, 3), (42, -1), (34, -7)) + quad((34, -7), (22, -16), (0, -15)) + quad((0, -15), (-30, -12), (-50, -2)) + [(-50, 2)] + quad((-50, 2), (-10, 14), (26, 9)) + quad((26, 9), (42, 7), (50, 3))
    p.poly(mid, body)
    p.poly(top, [(48, 1)] + quad((48, 1), (42, -2), (34, -7.5)) + quad((34, -7.5), (22, -16), (0, -15)) + quad((0, -15), (-30, -12), (-50, -2)) + quad((-50, -2), (-10, -6), (30, -3)))
    p.poly(bel, [(-40, 3.5)] + quad((-40, 3.5), (-10, 13.5), (26, 8.6)) + quad((26, 8.6), (42, 6.6), (49, 3.3)) + quad((49, 3.3), (20, 3), (-40, 3.5)))
    p.rell(hx("#7d9ab0"), 12 + 6 * math.cos(.7 + k * .4), 6 + 6 * math.sin(.7 + k * .4), 9, 3, .7 + k * .4)
    p.circ(hx("#1d2a35"), 28, -5, 2.2)
    p.line(hx("#4f6a7e"), quad((48, 3.5), (40, 6), (34, 3)), 1.3)


def d_octopus(p, t):
    arm = hx("#a8418f")
    for i in range(8):
        bx = -14 + i * 4
        pts = [(bx, -2)] + [(bx + (i - 3.5) * j * 2.1 + math.sin(t + i + j * .7) * 4, j * 7) for j in range(1, 7)]
        for j in range(len(pts) - 1):
            p.line(arm, [pts[j], pts[j + 1]], 5.5 - j * .7)
    p.ell(hx("#8e3474"), 0, -15, 19, 22)
    p.ell(hx("#c4559f"), -1, -17, 17.5, 20)
    p.ell(hx("#dd82bf"), -5, -26, 9, 8)
    for x, y, r in ((-8, -26, 3), (6, -30, 2.5), (9, -20, 2), (-3, -34, 2)):
        p.circ(hx("#e9a0d0"), x, y, r)
    eye(p, -7, -10, 4.5)
    eye(p, 7, -10, 4.5)


def d_shark(p, t, pal=None, boss=False):
    pal = pal or dict(top=hx("#5c7386"), fin=hx("#62798c"), bel=hx("#e3ebf0"), line=hx("#4a5f70"))
    w = math.sin(t) * 6
    p.poly(pal["fin"], [(-66, 0), (-92, -32 + w), (-80, 0), (-90, 22 + w)])
    p.poly(pal["fin"], [(2, -17), (-12, -46), (-24, -16)])
    body = [(72, 4)] + quad((72, 4), (68, -14), (32, -18)) + quad((32, -18), (-30, -20), (-70, -3)) + [(-70, 3)] + quad((-70, 3), (-20, 16), (32, 14)) + quad((32, 14), (62, 12), (72, 4))
    p.poly(pal["top"], body)
    p.poly(shade(pal["top"], .18), [(-60, 2)] + quad((-60, 2), (-20, 8), (40, 4)) + quad((40, 4), (60, 2), (71, 3)) + quad((71, 3), (60, 12), (32, 13.6)) + quad((32, 13.6), (-20, 15.6), (-60, 3)))
    p.poly(pal["bel"], [(-50, 5.5)] + quad((-50, 5.5), (-20, 15.4), (32, 13.6)) + quad((32, 13.6), (62, 11.6), (71, 4.6)) + quad((71, 4.6), (40, 8), (-50, 5.5)))
    p.rell(pal["fin"], 18 + 10 * math.cos(.6), 10 + 10 * math.sin(.6), 16, 4, .6)
    for i in range(3):
        p.line(pal["line"], [(30 - i * 5, -6), (28 - i * 5, 4)], 1.3)
    p.line(pal["line"], quad((66, 8), (58, 10), (52, 8)), 1.3)
    if not boss:
        p.circ((17, 17, 17), 54, -5, 2.3)
        return
    sc = (220, 230, 236)
    p.line(sc, [(4, -12), (16, -2)], 1.2)
    p.line(sc, [(8, -4), (13, -11)], 1.2)
    p.line(sc, [(-30, -6), (-20, 2)], 1.2)
    for x in range(52, 67, 3):
        p.poly((255, 255, 255), [(x, 8.5), (x + 1.4, 4.5), (x + 2.8, 8.5)])
    p.circ(hx("#ff3b30"), 54, -5, 2.8)
    p.circ((255, 255, 255), 54.8, -5.8, .8)
    p.line(hx("#1a2027"), [(49, -10), (59, -7.5)], 2)
    crown = [(-9, 0), (-9, -8), (-5, -4), (0, -11), (5, -4), (9, -8), (9, 0)]
    p.poly(hx("#ffd23f"), rot(crown, .12, 40, -19.5))
    p.poly(hx("#d9a531"), rot([(-9, -2), (9, -2), (9, .5), (-9, .5)], .12, 40, -19.5))
    p.circ(hx("#ff3b6b"), *rot([(0, -4)], .12, 40, -19.5)[0], 1.8)


def d_whale(p, t):
    k = math.sin(t) * .25
    top, bel = hx("#2f5f8c"), hx("#8fb3cf")
    tail = [(0, 0)] + quad((0, 0), (-20, -10), (-40, -40)) + quad((-40, -40), (-30, -10), (-18, 0)) + quad((-18, 0), (-30, 10), (-40, 40)) + quad((-40, 40), (-20, 10), (0, 0))
    p.poly(top, rot(tail, k, -128, 0))
    body = [(132, 4)] + cubic((132, 4), (132, -42), (62, -54), (0, -46)) + cubic((0, -46), (-60, -38), (-110, -14), (-130, -4)) + [(-130, 4)] + cubic((-130, 4), (-100, 20), (-40, 40), (20, 42)) + cubic((20, 42), (84, 44), (132, 36), (132, 4))
    p.poly(hx("#3d70a0"), body)
    p.poly(hx("#2a5784"), [(131, -4)] + cubic((131, -4), (128, -42), (62, -54), (0, -46)) + cubic((0, -46), (-60, -38), (-110, -14), (-130, -4)) + cubic((-130, -4), (-60, -8), (40, -10), (131, -4)))
    p.poly(bel, [(-100, 12)] + cubic((-100, 12), (-60, 30), (-10, 40), (20, 41)) + cubic((20, 41), (84, 43), (128, 34), (131, 10)) + cubic((131, 10), (100, 20), (20, 24), (-100, 12)))
    for i in range(6):
        p.line(hx("#5d86aa"), quad((120, 16 + i * 3.5), (60, 30 + i * 3), (0, 30 + i * 2)), 1.4)
    for x, y, rx, ry in ((30, -30, 6, 3), (-20, -24, 5, 2.5), (-60, -14, 4, 2), (60, -36, 4, 2), (0, -36, 3, 2)):
        p.ell(hx("#5a82a8"), x, y, rx, ry)
    p.rell(hx("#24507c"), 50 - 26 * math.cos(.5 + k * .5), 30 - 26 * math.sin(.5 + k * .5), 32, 7, .5 + k * .5)
    eye(p, 92, 6, 4.5, hx("#0d1e30"))
    p.line(hx("#1d3d5e"), quad((130, 10), (110, 16), (96, 14)), 2)


def d_jelly(p, t, c):
    pul = 1 + math.sin(t) * .12
    tc = shade(c, .25)
    for i in range(6):
        x0 = (i - 2.5) * 7
        p.line(tc, [(x0, 4)] + [(x0 + math.sin(t * 1.3 + j * .8 + i) * 4, 4 + j * 7 * pul) for j in range(1, 9)], 1.8)
    bell = [(24 * math.cos(a), 4 - 22 / pul * math.sin(a)) for a in [i / 16 * math.pi for i in range(17)]]
    scal = []
    for i in range(6):
        scal += quad((-24 + i * 8, 4), (-24 + i * 8 + 4, 10), (-24 + (i + 1) * 8, 4), 4)
    p.poly(c, bell + scal)
    p.ell(shade(c, .45), -6, -8 / pul, 7, 4 / pul)


def d_squid(p, t):
    w = math.sin(t)
    c, d = hx("#d24a35"), hx("#b8392a")
    for i in range(8):
        pts = [(-10, (i - 3.5) * 3)] + quad((-10, (i - 3.5) * 3), (-50, (i - 3.5) * 6 + w * 8 * (1 if i % 2 else -1)), (-82 - (i % 3) * 10, (i - 3.5) * 8 + math.sin(t * .8 + i) * 10))
        p.line(d, pts, 4)
    for s in (1, -1):
        e = (-130, s * 12 + math.sin(t * .5 + s) * 16)
        p.line(d, [(-10, s * 3)] + quad((-10, s * 3), (-70, s * 20 + w * 10), e), 2.5)
        p.ell(d, e[0], e[1], 7, 4)
    p.poly(c, [(84, 0), (104, -22 - w * 3), (106, 0), (104, 22 + w * 3)])
    p.poly(c, [(6, -14)] + quad((6, -14), (60, -17), (104, 0)) + quad((104, 0), (60, 17), (6, 14)))
    p.poly(shade(c, -.15), [(6, 2)] + quad((6, 2), (60, 6), (104, 0)) + quad((104, 0), (60, 17), (6, 14)))
    for x, y, r in ((30, -6, 3), (50, 4, 3), (70, -3, 2.5), (22, 6, 2)):
        p.ell(hx("#e9725a"), x, y, r, r * .7)
    p.ell(c, -4, 0, 14, 12)
    eye(p, -2, -3, 6.5, hx("#120707"))


def d_angler(p, t):
    p.poly(hx("#3a2622"), [(-26, 0), (-48, -18 + math.sin(t) * 4), (-48, 18 + math.sin(t) * 4)])
    p.ell(hx("#2c1c19"), 0, 0, 32, 26)
    p.ell(hx("#4a322b"), -3, -5, 27, 19)
    p.ell(hx("#6b4a40"), -6, -10, 14, 8)
    p.poly(hx("#120707"), [(34, -2), (8, 6), (30, 20)])
    for i in range(5):
        x = 30 - i * 5
        p.poly(hx("#f2efe6"), [(x, -1.5 + i * 1.5), (x - 2, 5 + i * 1.5), (x - 4, i * 1.5)])
    for i in range(4):
        x = 28 - i * 5
        p.poly(hx("#f2efe6"), [(x, 18 - i * 2.6), (x - 2, 10 - i * 2), (x - 4, 16 - i * 2.6)])
    eye(p, 14, -11, 4, hx("#1a1010"))
    by = -46 + math.sin(t * .5) * 4
    p.line(hx("#5a4038"), [(4, -24)] + quad((4, -24), (18, -62), (44, by)), 2.5)
    p.circ(hx("#f0fff8"), 44, by, 5)


def d_chest(p, t):
    p.poly(hx("#5a3416"), rot([(-34, -26), (34, -26), (34, 0), (-34, 0)], -.45, 0, -14))
    p.poly(hx("#d9a531"), rot([(-34, -6), (34, -6), (34, -1), (-34, -1)], -.45, 0, -14))
    for x, y, rx, ry in ((-14, -16, 8, 6), (0, -20, 9, 7), (13, -15, 8, 6), (-4, -12, 10, 6), (8, -24, 6, 5)):
        p.ell(hx("#ffd23f"), x, y, rx, ry)
        p.ell(hx("#fff0a0"), x - rx * .3, y - ry * .3, rx * .35, ry * .3)
    p.rect(hx("#6b3f1c"), -34, -14, 68, 32)
    p.rect(hx("#7d4c24"), -34, -14, 68, 10)
    for y in (-14, 13):
        p.rect(hx("#d9a531"), -34, y, 68, 5)
    for x in (-24, 18):
        p.rect(hx("#d9a531"), x, -14, 6, 32)
    p.rect(hx("#ffe58a"), -5, -6, 10, 10)
    p.rect(hx("#6b3f1c"), -1.5, -3, 3, 5)


def branch(p, x, y, a, l, w, d, c):
    x2, y2 = x + math.cos(a) * l, y + math.sin(a) * l
    p.line(c, [(x, y), (x2, y2)], w)
    if d > 0:
        branch(p, x2, y2, a - .45, l * .74, w * .72, d - 1, c)
        branch(p, x2, y2, a + .42, l * .74, w * .72, d - 1, c)
    else:
        p.circ(shade(c, .3), x2, y2, w * 1.1)


def d_coral(p, kind, c, lean):
    if kind == "branch":
        branch(p, 0, 0, -math.pi / 2 + lean, 20, 6, 4, c)
    elif kind == "fan":
        def fan(q):
            for i in range(13):
                a = -math.pi / 2 + lean + (i / 12 - .5) * 1.9
                q.line(c, [(0, 0), (math.cos(a) * 44, math.sin(a) * 44)], 1.6)
            for r in (16, 27, 38):
                q.arc(c, 0, 0, r, -math.pi / 2 + lean - .95, -math.pi / 2 + lean + .95, 1)
        p.layer(fan, 230)
    elif kind == "brain":
        p.ell(shade(c, -.2), 0, -10, 24, 14)
        p.ell(c, -1, -12, 22, 12)
        for i in range(4):
            p.line(shade(c, -.3), [(x, -16 + i * 4 + math.sin(x * .5 + i) * 2) for x in range(-18, 19, 4)], 1.6)
    elif kind == "tube":
        for x, h in ((-10, 30), (0, 42), (10, 24)):
            p.rect(c, x - 5, -h, 10, h, 5)
            p.rect(shade(c, .2), x - 5, -h, 4, h, 2)
            p.ell(shade(c, -.55), x, -h + 3, 3.5, 2)
    else:  # anemone
        for i in range(12):
            bx = -12 + i * 2.2
            tx, ty = bx + (i - 5.5) * 2.5, -30 - math.cos(i) * 4
            p.line(c, [(bx, -4)] + quad((bx, -4), (bx + math.sin(i) * 6, -18), (tx, ty)), 3.5)
            p.circ(shade(c, .5), tx, ty, 2.4)
        p.ell(shade(c, -.2), 0, -2, 14, 6)


# ---------------------------------------------------------------- hero skins
FUR = {
    "cat": (hx("#f2953a"), hx("#c9681a"), hx("#ffc07a")),
    "dog": (hx("#b07a45"), hx("#7d532c"), hx("#d9ac78")),
    "rabbit": (hx("#dcd6d1"), hx("#a9a29c"), hx("#f6f3f0")),
    "turtle": (hx("#6fb36a"), hx("#3f7f3a"), hx("#a4d89e")),
}


def head(p, skin, x, y, z=1.0, ears=1.0, mid=None):
    """Hero head facing right, centred on (x, y). `mid` draws between the head and the face (the pilot's cap)."""
    base, dark, light = FUR[skin]

    def q(a, b):
        return (x + a * z, y + b * z)
    pink = hx("#ff9fb0")
    if skin == "cat":
        p.poly(base, [q(-9, -7), q(-8, -7 - 13 * ears), q(-1, -10)])
        p.poly(base, [q(2, -10), q(9, -7 - 12 * ears), q(10, -5)])
        p.poly(pink, [q(-7, -8), q(-6.5, -8 - 8 * ears), q(-3, -10)])
        p.poly(pink, [q(4, -10), q(8, -8 - 7.5 * ears), q(8.5, -7)])
    elif skin == "rabbit":
        for ex, a in ((-5, -.25), (3, .12)):
            L = 13 * ears
            p.rell(dark, *q(ex - math.sin(a) * L, -8 - L), 4.2 * z, L * z, a)
            p.rell(base, *q(ex - math.sin(a) * L, -8.5 - L), 3.8 * z, (L - .6) * z, a)
            p.rell(pink, *q(ex - math.sin(a) * L, -8 - L), 2 * z, (L - 3) * z, a)
    p.ell(dark, *q(0, .5), 12 * z, 11 * z)
    p.ell(base, *q(-.4, -.5), 11.3 * z, 10 * z)
    p.ell(light, *q(-3, -5), 5.5 * z, 3.6 * z)
    if skin == "cat":
        for sx in (-3.5, 0, 3.5):
            p.line(dark, [q(sx, -10.4), q(sx + .4, -7)], 1.5 * z)
    if skin == "turtle":
        for sx, sy, r in ((-6, -5, 1.6), (-2, -8, 1.3), (-8, 1, 1.2)):
            p.circ(dark, *q(sx, sy), r * z)
    if mid:
        mid(p)
    if skin == "dog":
        p.rell(dark, *q(-6.5, 1), 4.2 * z, 9 * z, .35)
        p.ell(light, *q(8, 4), 7.8 * z, 5.4 * z)
    elif skin == "turtle":
        p.ell(light, *q(6, 4.5), 6.4 * z, 4.2 * z)
    else:
        p.ell((255, 240, 220) if skin == "cat" else (255, 255, 255), *q(6, 4), 6.2 * z, 4.6 * z)
    if skin != "turtle":
        p.ell(hx("#ffa5b4"), *q(-5.5, 4.5), 3.4 * z, 2.1 * z)
    iris = {"cat": hx("#3f9a45"), "dog": hx("#6b3e17"), "rabbit": hx("#3a2626"), "turtle": hx("#1d1d1d")}[skin]
    er = .9 if skin == "turtle" else 1
    eye(p, *q(-2, -.5), 3.4 * z * er, iris)
    eye(p, *q(6, -.5), 3.2 * z * er, iris)
    brown = hx("#5a3a20")
    if skin == "cat":
        p.poly(hx("#ff7a8a"), [q(9.5, 1.5), q(13, 1.5), q(11.2, 3.7)])
    elif skin == "rabbit":
        p.poly(hx("#ff8fa3"), [q(10, 2), q(12.6, 2), q(11.3, 3.6)])
        p.rect((255, 255, 255), *q(9.6, 5.4), 3.2 * z, 3 * z)
    elif skin == "dog":
        p.ell(hx("#2a1a10"), *q(14, 2.2), 3 * z, 2.3 * z)
        p.ell(hx("#ff7a8a"), *q(11, 8), 2 * z, 2.6 * z)
    else:
        p.circ(dark, *q(11, 2), .7 * z)
        p.circ(dark, *q(12.5, 2.3), .7 * z)
    if skin == "turtle":
        p.arc(dark, *q(6, 3), 4.5 * z, .35, 2.6, 1 * z)
    else:
        nx, ny = (14, 4.4) if skin == "dog" else (11.2, 3.7)
        p.line(brown, [q(nx, ny)] + [q(*a) for a in quad((nx, ny), (nx - 1.2, ny + 2.8), (nx - 3.7, ny + 2))], .9 * z)
        p.line(brown, [q(nx, ny)] + [q(*a) for a in quad((nx, ny), (nx + 1.3, ny + 2.8), (nx + 3.3, ny + 1.8))], .9 * z)
    if skin in ("cat", "rabbit"):
        for a in (-.15, .08):
            p.line((255, 255, 255), [q(9, 4.5), q(19, 4.5 + a * 30)], .8 * z)


def tail(p, skin, t, base, dark):
    fl = math.sin(t)
    if skin == "cat":
        p.line(shade(base, -.05), [(-20, -2)] + quad((-20, -2), (-36, -4 + fl * 5), (-44, -17 + fl * 7)), 7)
        p.circ((255, 243, 226), -44, -17 + fl * 7, 3.6)
    elif skin == "dog":
        p.line(base, [(-20, -4)] + quad((-20, -4), (-30, -8 + fl * 3), (-32, -18 + fl * 4)), 5)
    elif skin == "rabbit":
        p.circ((255, 255, 255), -23, -3, 6)
        p.circ(hx("#e9e4df"), -22, -1, 4)
    else:
        p.poly(dark, [(-20, -2), (-30, 1 + fl * 2), (-20, 3)])


def d_diver(p, t, lamp, skin="cat"):
    base, dark, light = FUR[skin]
    tail(p, skin, t, base, dark)
    for y, off in ((9, 0), (5, 1.4)):
        a = .2 + math.sin(t + off) * .45
        fin = [(0, -1.5)] + quad((0, -1.5), (-12, -8), (-23, -7.5)) + quad((-23, -7.5), (-26, 0), (-23, 7.5)) + quad((-23, 7.5), (-12, 6), (0, 2.5))
        p.poly(hx("#2a6fd0"), rot(fin, a, -18, y))
        p.poly(hx("#62b8ff"), rot([(-12, -6.5), (-23, -7.5), (-25.5, 0), (-23, 7.5), (-12, 5)], a, -18, y))
    p.rect(hx("#62737f"), -20, -23, 27, 10.5, 5)
    p.rect(hx("#cfdbe3"), -20, -23, 27, 6, 4)
    p.rect(hx("#ffcf3f"), -15, -23, 4, 10.5)
    p.rect(hx("#5a6772"), 6, -21, 4, 6)
    p.ell(dark, 0, 1, 24, 13)
    p.ell(base, -1, -1, 23, 11.5)
    p.ell(light, -2, -5, 13, 4.5)
    if skin == "cat":
        for x in (-14, -7, 0):
            p.line(dark, quad((x, -12), (x + 3, -5), (x, -1)), 2.4)
    if skin == "turtle":
        p.ell(hx("#4f4220"), -3, -5, 19, 9)
        p.ell(hx("#7a6834"), -3, -6, 17, 7.5)
        for x in (-12, -3, 6):
            p.ell(hx("#9a8644"), x, -6, 4, 3.4)
    p.ell(light if skin != "cat" else (255, 238, 215), 4, 6, 13, 6)
    p.line(hx("#26384a"), quad((-5, -13), (-3, 0), (-1, 12)), 2.6)
    p.ell(base, 16, 9 + math.sin(t + 1) * 2, 6, 3.5)
    p.circ(light, 20.5, 9 + math.sin(t + 1) * 2, 2.6)
    p.line(hx("#6c7a85"), [(5, -19)] + quad((5, -19), (12, -26), (14, -17)), 3)
    head(p, skin, 21.5, -7.5, 1.0, ears=.85 if skin == "rabbit" else 1)
    p.layer(lambda q: q.circ((170, 225, 255), 23, -7, 19), 60)
    p.circ((235, 250, 255), 23, -7, 19, 1.6)
    p.arc(hx("#cbd7e0"), 23, -7, 19, math.pi * .6, math.pi * 1.05, 4.5)
    p.arc(hx("#7f8f9a"), 23, -7, 21.4, math.pi * .6, math.pi * 1.05, 1.2)
    p.arc((255, 255, 255), 23, -7, 14.5, -2.65, -1.8, 3)
    p.circ((255, 255, 255), 35, -16, 1.8)
    p.rect(hx("#5d6c77"), 16, -29.5, 11, 5.5, 2)
    p.circ(hx("#fff4c2") if lamp else hx("#d8e3ea"), 27, -26.8, 2.4)


def d_pilot(p, t, space, wheels, skin="cat"):
    if space:
        fl = 10 + math.sin(t * 3) * 4
        p.poly(hx("#ff5028"), [(-36, -6), (-36 - fl * 3, 0), (-36, 6)])
        p.poly(hx("#ff9632"), [(-36, -4.5), (-36 - fl * 2, 0), (-36, 4.5)])
        p.poly(hx("#fff5c8"), [(-36, -2.5), (-36 - fl, 0), (-36, 2.5)])
        p.rect(hx("#7d8a96"), -40, -6, 16, 12, 4)
        p.rect(hx("#e3e9ee"), -40, -6, 16, 6, 3)
    sw = math.sin(t * 2)
    p.line(hx("#ffd23f"), [(0, -11)] + quad((0, -11), (-14, -14 + sw * 3), (-30, -12 + sw * 5)), 4)
    p.line(hx("#f0b820"), [(0, -10)] + quad((0, -10), (-12, -7 - sw * 2), (-23, -5 - sw * 4)), 3)
    p.poly(hx("#c9352a"), [(-24, -3), (-34, -21), (-27, -21), (-14, -5)])
    p.poly(hx("#c9352a"), [(-26, 1), (-38, 6), (-18, 4)])
    body = [(30, -5)] + quad((30, -5), (31, 1), (30, 6)) + [(-8, 7), (-30, 2), (-30, -2), (-8, -7)]
    p.poly(hx("#a82a1e"), body)
    p.poly(hx("#ff7564"), [(30, -5), (30, 0), (-8, 0), (-30, -.5), (-30, -2), (-8, -7)])
    p.poly(hx("#e8432f"), [(30, -2), (30, 2), (-8, 2), (-30, 1), (-30, -1), (-8, -3)])
    p.rect((255, 255, 255), -22, 1, 40, 2.4)
    hx0, hy0, z = 4, -15, .85

    def hp(x, y):
        return (hx0 + x * z, hy0 + y * z)

    def cap(q):
        q.poly(hx("#7a4a24"), [hp(12.4 * math.cos(a), 12.4 * math.sin(a)) for a in [math.pi * 1.06 + i / 12 * math.pi * .88 for i in range(13)]])
        if skin != "dog":
            q.ell(hx("#6a3e1d"), *hp(-10, 2), 3.2 * z, 5.5 * z)
        q.line(hx("#3b3b3b"), [hp(-12, -6), hp(11, -7.5)], 1.6 * z)
        for x in (1, 8):
            q.ell(hx("#4a4a4a"), *hp(x, -7.5), 3.8 * z, 3.4 * z)
            q.ell(hx("#9fe3ff"), *hp(x, -7.5), 2.6 * z, 2.3 * z)
            q.circ((255, 255, 255), *hp(x - .8, -8.3), .8 * z)
    head(p, skin, hx0, hy0, z, ears=.8, mid=cap)
    p.layer(lambda q: q.poly((200, 240, 255), [(15, -6), (19, -16), (22, -6)]), 170)
    p.line(hx("#7a2016"), [(-8, -6.5), (14, -6.5)], 2)
    p.ell(hx("#a82a1e"), 2, 4, 19, 4.2)
    p.ell(hx("#ff6b5a"), 2, 2.6, 18, 2.8)
    if wheels:
        p.line(hx("#333333"), [(6, 6), (8, 12)], 2)
        p.circ(hx("#222222"), 8, 12.5, 3.4)
        p.circ(hx("#999999"), 8, 12.5, 1.2)
    p.poly(hx("#e8eef3"), [(30, -5)] + quad((30, -5), (37, 0), (30, 6)))
    p.layer(lambda q: q.ell((220, 220, 220), 36, 0, 2.5, 17), 90)
    pr = abs(math.cos(t * 4)) * 17
    p.rect(hx("#3a3a3a"), 35, -pr, 2.4, pr * 2)
    if space:
        p.layer(lambda q: q.circ((170, 225, 255), 4, -15, 16.5), 60)
        p.circ((235, 250, 255), 4, -15, 16.5, 1.5)
        p.arc((255, 255, 255), 4, -15, 12.5, -2.65, -1.8, 2.5)


def d_astro(p, t, flame, skin="cat"):
    suit, sd = hx("#f4f6f8"), hx("#c5ced6")
    base = FUR[skin][0]
    if flame:
        fl = 9 + math.sin(t * 3) * 3
        for nx in (-17, -11):
            p.poly(hx("#ff7a3a"), [(nx - 3, 13), (nx, 13 + fl * 1.6), (nx + 3, 13)])
            p.poly(hx("#fff0b0"), [(nx - 1.6, 13), (nx, 13 + fl * .8), (nx + 1.6, 13)])
    p.rect(hx("#8a96a1"), -22, -14, 14, 27, 4)
    p.rect(hx("#b7c2cb"), -22, -14, 6, 27, 3)
    p.rect(hx("#5d6c77"), -20, 10, 5, 4, 1)
    p.rect(hx("#5d6c77"), -14, 10, 5, 4, 1)
    sw = math.sin(t) * .25
    p.poly(sd, rot([(-4, 0), (4, 0), (4, 16), (-4, 16)], .15 + sw, -3, 13))
    p.poly(suit, rot([(-4, 0), (4, 0), (4, 15), (-4, 15)], -.1 - sw, 5, 13))
    for bx, a in ((-3, .15 + sw), (5, -.1 - sw)):
        qq = rot([(0, 16)], a, bx, 13)[0]
        p.ell(hx("#6c7a85"), qq[0] + 1.5, qq[1], 5.5, 3.2)
    p.ell(sd, 1, 5, 13.5, 15)
    p.ell(suit, 0, 3.5, 12.5, 14)
    p.rect(hx("#4bcffa"), -5, -2, 10, 7, 2)
    p.circ(hx("#ff5e57"), -2, 1, 1.3)
    p.circ(hx("#ffd23f"), 2, 1, 1.3)
    p.circ(base, 7, 9, 2.6)
    p.poly(sd, rot([(0, -3.5), (16, -3.5), (16, 3.5), (0, 3.5)], -.5 + math.sin(t + 1) * .2, 8, -2))
    hand = rot([(17, 0)], -.5 + math.sin(t + 1) * .2, 8, -2)[0]
    p.circ(hx("#6c7a85"), hand[0], hand[1], 3.4)
    head(p, skin, 2, -17.5, .9, ears=.55)
    p.layer(lambda q: q.circ((170, 225, 255), 2, -18, 16), 55)
    p.circ((235, 250, 255), 2, -18, 16, 1.6)
    p.arc(sd, 2, -18, 16, math.pi * .25, math.pi * .75, 4)
    p.arc((255, 255, 255), 2, -18, 12, -2.7, -1.9, 2.6)
    p.circ((255, 255, 255), 13, -26, 1.6)
    p.line(hx("#8a96a1"), [(-6, -33), (-9, -40)], 1.4)
    p.circ(hx("#ff5e57") if math.sin(t * 2) > 0 else hx("#ffd23f"), -9, -40, 1.8)


def d_flag(p, t, skin="cat"):
    p.rect(hx("#cfd6dc"), -2, -90, 4, 92, 2)
    p.circ(hx("#ffd23f"), 0, -91, 4)
    pts_top = [(2 + i * 6, -86 + math.sin(t + i * .7) * 3) for i in range(9)]
    pts_bot = [(x, y + 38) for x, y in pts_top]
    p.poly(hx("#ff7a59"), pts_top + pts_bot[::-1])
    p.poly(hx("#ffd23f"), [(x, y + 26) for x, y in pts_top] + [(x, y + 38) for x, y in pts_top][::-1])
    head(p, skin, 24, -67 + math.sin(t + 2.8) * 3, .75, ears=.55)


# ---------------------------------------------------------------- sky sprites
def d_gulls(p, t, off):
    for ox, oy, ph in off:
        f = math.sin(t + ph * 1.7)
        p.poly(hx("#c9d0d6"), [(ox - 3, oy - 1)] + quad((ox - 3, oy - 1), (ox - 4, oy - 13 * f), (ox - 15, oy - 15 * f)) + quad((ox - 15, oy - 15 * f), (ox - 5, oy - 5 * f), (ox + 4, oy - 1)))
        p.ell(hx("#f6f7f5"), ox, oy, 8, 3.4)
        p.ell(hx("#4a4f55"), ox - 7, oy, 2.5, 1.6)
        p.poly(hx("#ffb020"), [(ox + 7.5, oy - .6), (ox + 12, oy + .2), (ox + 7.5, oy + 1.2)])
        p.circ((17, 17, 17), ox + 5, oy - 1, .9)
        p.poly(hx("#e9ecef"), [(ox - 1, oy - 1)] + quad((ox - 1, oy - 1), (ox + 2, oy - 12 * f), (ox - 6, oy - 16 * f)) + quad((ox - 6, oy - 16 * f), (ox, oy - 6 * f), (ox + 5, oy - 1)))
        p.ell(hx("#3a3f45"), ox - 6 - f, oy - 15.5 * f, 2.2, 1.2)


def d_balloon(p, t, c):
    env = [(0, 22)] + cubic((0, 22), (-46, 0), (-44, -62), (0, -62)) + cubic((0, -62), (44, -62), (46, 0), (0, 22))
    p.poly(c[0], env)
    for xx in (-24, 0, 24):
        sx = xx * .72
        p.poly(c[1], [(sx * .2, 20)] + cubic((sx * .2, 20), (sx - 6, 0), (sx - 6, -58), (sx * .3, -61)) + cubic((sx * .3, -61), (sx + 6, -58), (sx + 6, 0), (sx * .2 + 3, 20)))
    p.ell(shade(c[0], .35), -18, -36, 7, 18)
    p.line(hx("#6b4a2e"), [(-7, 19), (-8, 36)], 1)
    p.line(hx("#6b4a2e"), [(7, 19), (8, 36)], 1)
    p.poly(hx("#ffb020"), [(-3, 31), (0, 22 - math.sin(t) * 2), (3, 31)])
    p.rect(hx("#8a5a2b"), -10, 36, 20, 13, 2)
    p.rect(hx("#6b4420"), -10, 36, 20, 3)


def d_heli(p, t):
    b = hx("#2f6ad0")
    p.rect(hx("#2a63bf"), -72, -7, 52, 6)
    p.poly(hx("#2a63bf"), [(-72, -7), (-80, -24), (-68, -24), (-62, -7)])
    a = t
    p.line(hx("#333333"), rot([(-11, 0), (11, 0)], a, -74, -16), 2)
    p.line(hx("#333333"), [(-14, 18), (-10, 24)], 2)
    p.line(hx("#333333"), [(14, 18), (10, 24)], 2)
    p.line(hx("#333333"), [(-26, 24), (26, 24), (31, 20)], 2)
    p.ell(hx("#1f4e9a"), 0, 1, 32, 18)
    p.ell(b, -1, -1, 31, 16)
    p.ell(hx("#5a9cf0"), -4, -8, 22, 6)
    p.poly(hx("#bfe6ff"), [(14, -15)] + [(14 + 15 * math.cos(x), -3 + 12 * math.sin(x)) for x in [-math.pi / 2 + i / 10 * math.pi for i in range(11)]])
    p.ell((255, 255, 255), 18, -8, 4, 2)
    p.rect(hx("#ffd23f"), -26, 4, 30, 3)
    p.rect(hx("#444444"), -3, -24, 6, 7)
    L = abs(math.cos(t * 2)) * 66
    p.layer(lambda q: q.ell((60, 60, 60), 0, -25, 66, 3), 70)
    p.rect(hx("#333333"), -L, -26, L * 2, 2.2)


def d_plane(p, t):
    p.poly(hx("#d9e2ea"), [(-100, -10), (-130, -58), (-112, -58), (-70, -12)])
    p.poly(hx("#ff7a59"), [(-124, -48), (-130, -58), (-112, -58), (-103, -48)])
    p.poly(hx("#b9c6d1"), [(14, -4), (-28, -34), (-42, -34), (-18, -4)])
    body = [(132, 2)] + quad((132, 2), (128, -15), (104, -16)) + [(-100, -12), (-132, -5), (-110, 8), (100, 12)] + quad((100, 12), (128, 12), (132, 2))
    p.poly(hx("#c9d5df"), body)
    p.poly((255, 255, 255), [(130, -2)] + quad((130, -2), (126, -15), (104, -16)) + [(-100, -12), (-130, -5), (-100, 0), (130, -2)])
    p.rect(hx("#ff7a59"), -104, 2, 210, 3)
    for x in range(-84, 93, 11):
        p.ell(hx("#36506b"), x, -5, 2.8, 3.3)
    p.poly(hx("#36506b"), [(112, -10), (124, -8), (122, -4), (110, -5)])
    p.poly(hx("#d9e2ea"), [(-100, -1), (-130, 10), (-118, 10), (-92, 1)])
    p.poly(hx("#e6edf2"), [(22, 4), (-30, 46), (-46, 46), (-20, 6)])
    p.rect(hx("#9aa8b4"), -14, 18, 32, 12, 6)
    p.ell(hx("#55626d"), 18, 24, 2, 5.5)


def d_jet(p, t):
    fl = 8 + math.sin(t) * 3
    p.poly(hx("#ff9632"), [(-60, -4), (-62 - fl * 2.4, 0), (-60, 4)])
    p.poly(hx("#fff0aa"), [(-60, -2), (-62 - fl, 0), (-60, 2)])
    p.poly(hx("#6f7c88"), [(-38, -6), (-58, -30), (-48, -30), (-20, -6)])
    p.poly(hx("#5f6b77"), [(74, 0), (30, -7), (-60, -6), (-60, 5), (30, 6)])
    p.poly(hx("#b5c1cb"), [(74, 0), (30, -7), (-60, -6), (-60, -1), (30, 0)])
    p.poly(hx("#7fd4ff"), [(15, -7)] + [(30 + 15 * math.cos(a), -7 - 5.5 * math.sin(a)) for a in [i / 10 * math.pi for i in range(11)]][::-1])
    p.ell((255, 255, 255), 26, -9, 4, 1.5)
    p.poly(hx("#7d8a96"), [(14, 2), (-28, 22), (-40, 22), (-22, 2)])
    p.circ(hx("#4bcffa"), -12, 0, 3)


def d_wballoon(p, t):
    sw = math.sin(t) * 3
    p.line((235, 240, 245), [(0, 30), (sw, 64)], 1)
    p.rect(hx("#f3a33a"), -6 + sw, 64, 12, 10, 2)
    p.ell(hx("#c3cad2"), 0, 0, 28, 30)
    p.ell(hx("#e6eaee"), -3, -4, 24, 25)
    p.ell((255, 255, 255), -10, -12, 9, 10)
    p.poly(hx("#c3cad2"), [(-5, 28), (0, 34), (5, 28)])


def d_meteor(p, t):
    for i in range(10):
        a = i / 10
        c = mix(hx("#ff6e28"), hx("#ffd26e"), a)
        p.layer(lambda q, a=a, c=c: q.poly(c, [(2 - 112 * (1 - a), 0), (2, -13 * (1 - a * .5)), (2, 13 * (1 - a * .5))]), int(30 + 25 * a))
    pts = [((11 + math.sin(i * 2.3) * 3) * math.cos(i / 9 * TAU + t), (11 + math.sin(i * 2.3) * 3) * math.sin(i / 9 * TAU + t)) for i in range(9)]
    p.poly(hx("#ffb347"), [(x * 1.18, y * 1.18) for x, y in pts])
    p.poly(hx("#5e4234"), pts)
    p.ell(hx("#3f2b22"), 3, -2, 3, 2.4)
    p.ell(hx("#3f2b22"), -4, 4, 2, 1.6)


def d_satellite(p, t):
    for s in (-1, 1):
        x0 = 18 if s > 0 else -64
        p.rect(hx("#1f4fa8"), x0, -13, 46, 26)
        for i in range(1, 4):
            p.line(hx("#8fb8ff"), [(x0 + i * 11.5, -13), (x0 + i * 11.5, 13)], .8)
        p.line(hx("#8fb8ff"), [(x0, 0), (x0 + 46, 0)], .8)
        p.line(hx("#aaaaaa"), [(s * 14, 0), (s * 18, 0)], 2)
    p.rect(hx("#b8861f"), -14, -16, 28, 32, 3)
    p.rect(hx("#ffe08a"), -14, -16, 28, 14, 3)
    p.line(hx("#cccccc"), [(0, -16), (0, -22)], 1.5)
    p.ell(hx("#e8eef3"), 0, -25, 11, 4)
    if math.sin(t) > .3:
        p.circ(hx("#ff4d4d"), 8, 10, 2.2)


def d_iss(p, t):
    p.rect(hx("#b8c2cb"), -160, -3, 320, 6)
    for x in (-146, -112, 112, 146):
        for s in (-1, 1):
            y0 = 7 if s > 0 else -59
            p.rect(hx("#c58a32"), x - 13, y0, 26, 52)
            for i in range(1, 5):
                p.line(hx("#8c5f20"), [(x - 13, y0 + i * 10.4), (x + 13, y0 + i * 10.4)], .8)
            p.line(hx("#8c5f20"), [(x, y0), (x, y0 + 52)], .8)
    p.rect(hx("#f4f6f8"), -70, 8, 14, 34)
    p.rect(hx("#f4f6f8"), 56, 8, 14, 34)
    p.rect(hx("#aeb8c1"), -46, -11, 92, 22, 9)
    p.rect((255, 255, 255), -46, -11, 92, 12, 9)
    p.rect(hx("#dfe5ea"), -11, -34, 22, 68, 8)
    p.rect(hx("#dfe5ea"), 30, -20, 30, 14, 6)
    for x in (-30, -18, 18, 30):
        p.circ(hx("#36506b"), x, 0, 2)


def d_astronaut(p, t):
    a = math.sin(t) * .4
    wht = hx("#f4f6f8")

    def r(pts):
        return rot(pts, a)
    p.poly(hx("#c9d0d6"), r([(-18, -14), (-8, -14), (-8, 12), (-18, 12)]))
    p.poly(wht, r([(-6, 10), (2, 10), (6, 30), (-2, 30)]))
    p.poly(wht, r([(3, 10), (11, 10), (12, 30), (4, 30)]))
    p.poly(wht, r([(-9, -12), (12, -12), (12, 13), (-9, 13)]))
    p.poly(wht, r([(9, -9), (24, -20), (28, -15), (12, -3)]))
    p.poly(hx("#ff5e57"), r([(-2, -6), (6, -6), (6, -1), (-2, -1)]))
    hxy = r([(2, -21)])[0]
    p.circ(wht, hxy[0], hxy[1], 11.5)
    vxy = r([(5, -21)])[0]
    p.ell(hx("#c48a1f"), vxy[0], vxy[1], 7.5, 6.5)
    p.ell(hx("#ffe08a"), vxy[0] - 1, vxy[1] - 1.5, 5.5, 4)
    p.ell((255, 255, 255), vxy[0] - 2, vxy[1] - 3, 2.2, 1.3)


def d_ufo(p, t):
    p.line(hx("#5bc94f"), [(-1, -24), (-8, -31)], 1.6)
    p.line(hx("#5bc94f"), [(10, -24), (16, -31)], 1.6)
    p.circ(hx("#ffd23f"), -8, -31, 2)
    p.circ(hx("#ffd23f"), 16, -31, 2)
    p.circ(hx("#7be36b"), 4, -18, 10.5)
    p.ell((17, 17, 17), 2, -19, 2.6, 3.6)
    p.ell((17, 17, 17), 9.5, -19, 2.4, 3.4)
    p.circ((255, 255, 255), 2.8, -20.3, .8)
    p.circ((255, 255, 255), 10.2, -20.3, .7)
    p.line(hx("#1d5e17"), [(-1, -25), (4, -23)], 1.4)
    p.line(hx("#1d5e17"), [(7, -23), (12.5, -25)], 1.4)
    p.line(hx("#1d5e17"), quad((3, -12.5), (7, -15), (10, -12.5)), 1.4)
    p.poly(hx("#ffd23f"), [(x + 4, y - 29) for x, y in [(-7, 0), (-7, -6), (-3.5, -3), (0, -8), (3.5, -3), (7, -6), (7, 0)]])
    p.layer(lambda q: q.poly((170, 240, 255), [(29 * math.cos(a), -8 + 32 * math.sin(a)) for a in [math.pi + i / 16 * math.pi for i in range(17)]]), 90)
    p.arc((230, 250, 255), 0, -8, 29, math.pi + .1, TAU - .1, 1.2)
    p.ell(hx("#46515c"), 0, -1, 66, 14)
    p.ell(hx("#9aa7b3"), 0, -4, 64, 12)
    p.ell(hx("#eef2f5"), 0, -8, 52, 6)
    p.ell(hx("#38424c"), 0, 8, 28, 7)
    cols = [hx("#ff5e57"), hx("#ffd23f"), hx("#4bcffa")]
    for i in range(9):
        p.ell(cols[(int(t) + i) % 3], -52 + i * 13, 0, 3, 2.6)


def d_goldstar(p, t):
    r = 32
    pts = [((r if i % 2 == 0 else r * .46) * math.cos(i * math.pi / 5 - math.pi / 2), (r if i % 2 == 0 else r * .46) * math.sin(i * math.pi / 5 - math.pi / 2)) for i in range(10)]
    pts = rot(pts, math.sin(t) * .15)
    p.poly(hx("#b8780c"), [(x * 1.07, y * 1.07) for x, y in pts])
    p.poly(hx("#f5b81f"), pts)
    p.poly(hx("#fff3a8"), [(x * .6, y * .6 - 4) for x, y in pts])
    eye(p, -6, -2, 3.2, hx("#5a3a10"))
    eye(p, 6, -2, 3.2, hx("#5a3a10"))
    p.arc(hx("#8a5a10"), 0, 4, 5, .2, math.pi - .2, 1.6)



def make_cloud():
    c = pg.Surface((360, 170), pg.SRCALPHA)
    pg.draw.ellipse(c, (212, 227, 240), (40, 112, 280, 40))
    n = random.randint(9, 13)
    bl = []
    for i in range(n):
        t = i / (n - 1)
        bl.append((60 + t * 240 + rnd(-15, 15), 118 - math.sin(t * math.pi) * rnd(28, 55), rnd(28, 50)))
    bl.sort(key=lambda b: -b[1])
    for bx, by, r in bl:
        pg.draw.circle(c, (207, 223, 238), (bx, by + 3), r)
    for bx, by, r in bl:
        pg.draw.circle(c, (242, 247, 251), (bx, by), r * .96)
        pg.draw.circle(c, (255, 255, 255), (bx - r * .25, by - r * .3), r * .62)
    return c


# ---------------------------------------------------------------- space sprites (stage 3)
def d_rocket(p, t):
    fl = 14 + math.sin(t * 2) * 5
    p.poly(hx("#ff7a3a"), [(-52, -8), (-52 - fl * 2.2, 0), (-52, 8)])
    p.poly(hx("#ffd26e"), [(-52, -5), (-52 - fl * 1.4, 0), (-52, 5)])
    p.poly(hx("#fff6d0"), [(-52, -2.5), (-52 - fl * .7, 0), (-52, 2.5)])
    p.poly(hx("#c9352a"), [(-30, -12), (-52, -26), (-52, -10)])
    p.poly(hx("#c9352a"), [(-30, 12), (-52, 26), (-52, 10)])
    p.rect(hx("#5d6c77"), -56, -9, 8, 18, 2)
    p.rect(hx("#d5dde3"), -50, -13, 78, 26, 8)
    p.rect((255, 255, 255), -50, -13, 78, 12, 7)
    p.poly(hx("#e8432f"), [(28, -13)] + quad((28, -13), (50, -10), (62, 0)) + quad((62, 0), (50, 10), (28, 13)))
    p.poly(hx("#ff7564"), [(28, -13)] + quad((28, -13), (50, -10), (62, 0)) + [(28, -2)])
    p.circ(hx("#7f8f9a"), 8, 0, 7.5)
    p.circ(hx("#7fd4ff"), 8, 0, 5.5)
    p.circ((255, 255, 255), 6, -2, 1.6)
    p.rect(hx("#c9352a"), -36, -13, 5, 26)
    p.poly(hx("#c9352a"), [(-12, 0), (-34, 12), (-34, -1)])


def d_saucer(p, t, col):
    dome = shade(col, .55)
    p.layer(lambda q: q.poly(dome, [(18 * math.cos(a), -6 - 18 * math.sin(a)) for a in [i / 14 * math.pi for i in range(15)]]), 170)
    p.circ(hx("#7be36b"), 0, -10, 6.5)
    p.ell((17, 17, 17), -2, -11, 1.6, 2.4)
    p.ell((17, 17, 17), 2.5, -11, 1.6, 2.4)
    p.ell(shade(col, -.45), 0, 2, 40, 9)
    p.ell(col, 0, -1, 39, 8)
    p.ell(shade(col, .3), 0, -4, 30, 3.5)
    lights = [hx("#ffd23f"), hx("#4bcffa"), hx("#ff5e57")]
    for i in range(7):
        p.ell(lights[(int(t) + i) % 3], -30 + i * 10, 1, 2.4, 2)
    p.ell(hx("#2b2f38"), 0, 8, 14, 3.5)


def d_fighter(p, t):
    fl = 8 + math.sin(t * 3) * 3
    for y in (-9, 9):
        p.poly(hx("#7be3ff"), [(-46, y - 3), (-46 - fl * 2.4, y), (-46, y + 3)])
        p.poly((235, 255, 255), [(-46, y - 1.5), (-46 - fl * 1.2, y), (-46, y + 1.5)])
    p.poly(hx("#3b2a5a"), [(-10, -6), (-34, -30), (-22, -30), (10, -6)])
    p.poly(hx("#3b2a5a"), [(-10, 6), (-34, 30), (-22, 30), (10, 6)])
    p.poly(hx("#ff3b6b"), [(-30, -30), (-22, -30), (-20, -26), (-28, -26)])
    p.poly(hx("#ff3b6b"), [(-30, 30), (-22, 30), (-20, 26), (-28, 26)])
    p.rect(hx("#2b2f38"), -48, -13, 22, 8, 3)
    p.rect(hx("#2b2f38"), -48, 5, 22, 8, 3)
    p.poly(hx("#4a3a6e"), [(58, 0), (20, -11), (-34, -9), (-40, 0), (-34, 9), (20, 11)])
    p.poly(hx("#6b57a0"), [(58, 0), (20, -11), (-34, -9), (-40, 0), (20, -2)])
    p.poly(hx("#7be36b"), [(30, -2), (14, -8), (2, -6), (4, -1)])
    p.circ(hx("#ff3b6b"), -6, 0, 2.4)


def d_asteroid(p, t):
    pts = []
    for i in range(12):
        a = i / 12 * TAU + t / 4
        r = 26 + math.sin(i * 2.7) * 5 + math.cos(i * 1.3) * 3
        pts.append((math.cos(a) * r, math.sin(a) * r))
    p.poly(hx("#4a4038"), [(x * 1.05, y * 1.05 + 1.5) for x, y in pts])
    p.poly(hx("#7a6a5c"), pts)
    p.poly(hx("#93806e"), [(x * .7 - 4, y * .7 - 5) for x, y in pts])
    for a, d, r in ((.3, 12, 5), (2.2, 14, 4), (4, 8, 3.5), (5.2, 17, 3)):
        a += t / 4
        x, y = math.cos(a) * d, math.sin(a) * d
        p.ell(hx("#5e5146"), x, y, r, r * .85)
        p.ell(hx("#4a4038"), x + r * .2, y + r * .2, r * .7, r * .55)


def d_comet(p, t):
    for i in range(12):
        a = i / 12
        c = mix(hx("#4bcffa"), hx("#e8fbff"), a)
        p.layer(lambda q, a=a, c=c: q.poly(c, [(-170 * (1 - a), math.sin(t + a * 4) * 4 * (1 - a)), (0, -10 * (1 - a * .4)), (0, 10 * (1 - a * .4))]), int(22 + 26 * a))
    p.circ(hx("#e8fbff"), 0, 0, 7)
    p.circ((255, 255, 255), -1, -1, 4)


def d_mothership(p, t):
    hull = [(170, 6), (120, -22), (-60, -30), (-160, -14), (-170, 6), (-150, 22), (120, 24)]
    p.poly(hx("#241a3a"), [(x, y + 3) for x, y in hull])
    p.poly(hx("#3b2a5a"), hull)
    p.poly(hx("#55407f"), [(160, 2), (118, -20), (-60, -28), (-150, -12), (-60, -12), (118, -4)])
    p.layer(lambda q: q.poly(hx("#ff8fd8"), [(-20 + 40 * math.cos(a), -28 - 22 * math.sin(a)) for a in [i / 16 * math.pi for i in range(17)]]), 150)
    for i in range(14):
        on = (int(t) + i) % 3 == 0
        p.rect(hx("#ffd23f") if on else hx("#8a7a40"), -140 + i * 20, 4, 9, 5, 1)
    for x in (-100, 0, 100):
        p.ell(hx("#7be3ff"), x, 22, 16, 4)
    p.poly(hx("#3b2a5a"), [(-120, -16), (-150, -50), (-128, -50), (-96, -20)])
    p.circ(hx("#ff3b6b"), -150, -50, 3)


def d_saturn(p, t):
    ring_back = [(95 * math.cos(a), 22 * math.sin(a)) for a in [math.pi + i / 24 * math.pi for i in range(25)]]
    p.line(hx("#cdb38a"), ring_back, 7)
    p.line(hx("#a9926c"), [(x * .82, y * .82) for x, y in ring_back], 4)
    p.circ(hx("#c9a46c"), 0, 0, 46)
    for y, c in ((-30, "#e3c896"), (-16, "#b98f56"), (0, "#dcbf8c"), (14, "#b5894f"), (28, "#d9b984")):
        w = math.sqrt(max(0, 46 * 46 - y * y))
        p.ell(hx(c), 0, y, w * .98, 6)
    p.ell(hx("#e9d2a6"), -14, -18, 16, 10)
    ring_front = [(95 * math.cos(a), 22 * math.sin(a)) for a in [i / 24 * math.pi for i in range(25)]]
    p.line(hx("#e6cf9f"), ring_front, 7)
    p.line(hx("#bfa57a"), [(x * .82, y * .82) for x, y in ring_front], 4)


def d_rover(p, t):
    for x in (-26, 0, 26):
        p.circ(hx("#3a3f45"), x, 12, 9)
        p.circ(hx("#8a96a1"), x, 12, 4)
    p.rect(hx("#c7ced4"), -38, -6, 76, 12, 3)
    p.rect(hx("#e9edf0"), -38, -6, 76, 5, 3)
    p.rect(hx("#ffd23f"), -30, -16, 26, 10, 2)
    p.line(hx("#8a96a1"), [(22, -6), (22, -26)], 2)
    p.ell(hx("#e9edf0"), 22, -28, 9, 3)
    p.line(hx("#8a96a1"), [(-34, -6), (-40, -22)], 1.5)
    p.circ(hx("#ff5e57"), -40, -22, 2)


def d_o2tank(p, t):
    p.rect(hx("#5d6c77"), -4, -24, 8, 6, 2)
    p.rect(hx("#2e86de"), -11, -19, 22, 38, 7)
    p.rect(hx("#6fc3ff"), -11, -19, 9, 38, 5)
    p.rect((255, 255, 255), -11, -6, 22, 9)


# ---------------------------------------------------------------- sprite registry
SAUCER_COLS = [hx("#9aa7b3"), hx("#c56cf0"), hx("#ff9f43")]
REEF_COLS = [(hx("#4bcffa"), hx("#2e86de")), (hx("#ffd23f"), hx("#f0a500")), (hx("#a0e7ff"), hx("#6cc4e8")), (hx("#ff9ff3"), hx("#f368e0"))]
JELLY_COLS = [hx("#ff8fd8"), hx("#9be7ff"), hx("#c9a0ff"), hx("#8affc1")]
BALLOON_COLS = [(hx("#ff5e57"), hx("#ffd23f")), (hx("#4bcffa"), hx("#ffffff")), (hx("#7bed9f"), hx("#ff9f43")), (hx("#c56cf0"), hx("#ffd23f"))]
random.seed(7)
REEF_OFF = [[(rnd(-34, 34), rnd(-20, 20), rnd(0, 6), *REEF_COLS[v]) for _ in range(9)] for v in range(4)]
GULL_OFF = [[(0, 0, 0)] + [(rnd(-42, 42), rnd(-24, 24), rnd(0, 6)) for _ in range(n)] for n in (3, 5, 6)]
random.seed()

# id: (w, h, cx, cy, zoom, frames, draw(p, t, variant))
SPR = {
    "reef": (110, 70, 55, 35, 1, 6, lambda p, t, v: d_reef(p, t, REEF_OFF[v])),
    "clown": (60, 40, 32, 20, 1, 6, lambda p, t, v: d_clown(p, t)),
    "seahorse": (50, 82, 22, 42, 1, 4, lambda p, t, v: d_seahorse(p, t)),
    "turtle": (110, 84, 58, 42, 1, 6, lambda p, t, v: d_turtle(p, t)),
    "dolphin": (130, 76, 70, 38, 1, 6, lambda p, t, v: d_dolphin(p, t)),
    "octopus": (70, 104, 35, 44, 1, 6, lambda p, t, v: d_octopus(p, t)),
    "shark": (180, 110, 95, 60, 1, 6, lambda p, t, v: d_shark(p, t)),
    "whale": (300, 130, 172, 64, 1, 6, lambda p, t, v: d_whale(p, t)),
    "jelly": (60, 96, 30, 30, 1, 6, lambda p, t, v: d_jelly(p, t, JELLY_COLS[v])),
    "squid": (260, 90, 140, 45, 1, 6, lambda p, t, v: d_squid(p, t)),
    "angler": (110, 112, 55, 66, 1, 6, lambda p, t, v: d_angler(p, t)),
    "chest": (100, 80, 50, 50, 1, 1, lambda p, t, v: d_chest(p, t)),
    "boss": (420, 250, 218, 140, 2.3, 6, lambda p, t, v: d_shark(p, t, dict(top=hx("#323d48"), fin=hx("#3b4754"), bel=hx("#c4ced6"), line=hx("#232b33")), True)),
    "diver": (100, 76, 50, 42, 1, 8, lambda p, t, v: d_diver(p, t, v[0], SKINS[v[1]])),
    "bird": (120, 82, 62, 44, 1, 6, lambda p, t, v: d_gulls(p, t, GULL_OFF[v])),
    "balloon": (100, 124, 50, 66, 1, 4, lambda p, t, v: d_balloon(p, t, BALLOON_COLS[v])),
    "heli": (170, 70, 88, 34, 1, 6, lambda p, t, v: d_heli(p, t)),
    "plane": (280, 110, 140, 62, 1, 1, lambda p, t, v: d_plane(p, t)),
    "jet": (170, 64, 98, 32, 1, 4, lambda p, t, v: d_jet(p, t)),
    "wballoon": (70, 112, 35, 36, 1, 4, lambda p, t, v: d_wballoon(p, t)),
    "meteor": (150, 60, 120, 30, 1, 6, lambda p, t, v: d_meteor(p, t)),
    "satellite": (140, 64, 70, 34, 1, 2, lambda p, t, v: d_satellite(p, t)),
    "iss": (340, 130, 170, 65, 1, 1, lambda p, t, v: d_iss(p, t)),
    "astronaut": (70, 80, 35, 42, 1, 6, lambda p, t, v: d_astronaut(p, t)),
    "ufo": (240, 140, 120, 80, 1.7, 3, lambda p, t, v: d_ufo(p, t)),
    "goldstar": (80, 80, 40, 40, 1, 6, lambda p, t, v: d_goldstar(p, t)),
    "pilot": (110, 84, 64, 52, 1, 6, lambda p, t, v: d_pilot(p, t, v[0], v[1], SKINS[v[2]])),
    "astro": (90, 100, 45, 54, 1, 6, lambda p, t, v: d_astro(p, t, v[0], SKINS[v[1]])),
    "rocket": (170, 64, 100, 32, 1, 4, lambda p, t, v: d_rocket(p, t)),
    "saucer": (100, 56, 50, 34, 1, 3, lambda p, t, v: d_saucer(p, t, SAUCER_COLS[v])),
    "fighter": (140, 70, 82, 35, 1, 4, lambda p, t, v: d_fighter(p, t)),
    "asteroid": (76, 76, 38, 38, 1, 12, lambda p, t, v: d_asteroid(p, t)),
    "comet": (200, 34, 186, 17, 1, 6, lambda p, t, v: d_comet(p, t)),
    "mothership": (360, 120, 180, 66, 1, 3, lambda p, t, v: d_mothership(p, t)),
    "saturn": (210, 110, 105, 55, 1, 1, lambda p, t, v: d_saturn(p, t)),
    "flag": (70, 104, 10, 98, 1, 6, lambda p, t, v: d_flag(p, t, SKINS[v])),
    "rover": (100, 64, 50, 40, 1, 1, lambda p, t, v: d_rover(p, t)),
    "o2tank": (30, 50, 15, 26, 1, 1, lambda p, t, v: d_o2tank(p, t)),
}
_SCACHE = {}


def sprite(sid, frame=0, variant=0, flip=False):
    w, h, cx, cy, z, n, fn = SPR[sid]
    frame %= n
    key = (sid, frame, variant, flip)
    s = _SCACHE.get(key)
    if s is None:
        if flip:
            s = pg.transform.flip(sprite(sid, frame, variant), True, False)
        else:
            p = P(w, h, cx, cy, z)
            fn(p, frame / n * TAU, variant)
            s = p.done()
        _SCACHE[key] = s
    return s


_CORAL = {}


def coral_sprite(kind, col, side, scale):
    key = (kind, col, side, round(scale, 1))
    if key not in _CORAL:
        p = P(130, 90, 65, 82, scale)
        d_coral(p, kind, col, -.35 if side else .35)
        _CORAL[key] = p.done()
    return _CORAL[key]


_GLOW = {}


def glow(r, col, strength=1.0):
    """Soft additive light disc (black background, blit with BLEND_RGB_ADD)."""
    r = max(2, int(r))
    key = (r, col, round(strength, 2))
    if key not in _GLOW:
        s = pg.Surface((2 * r, 2 * r))
        steps = min(40, r)
        for i in range(steps):
            rr = r * (1 - i / steps)
            k = strength * (i / steps) ** 1.8
            pg.draw.circle(s, tuple(int(c * k) for c in col), (r, r), rr)
        _GLOW[key] = s
    return _GLOW[key]


def blit_glow(dst, x, y, r, col, strength=1.0):
    g = glow(r, col, strength)
    dst.blit(g, (x - g.get_width() / 2, y - g.get_height() / 2), special_flags=pg.BLEND_RGB_ADD)


def silhouette(sid, frame, variant, flip):
    key = ("sil", sid, frame % SPR[sid][5], variant, flip)
    if key not in _SCACHE:
        m = pg.mask.from_surface(sprite(sid, frame, variant, flip), 40)
        _SCACHE[key] = m.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    return _SCACHE[key]


def cone_mask(L, half, peak, color=None):
    """A soft wedge pointing right from the centre. color=None -> alpha mask, else additive RGB."""
    q = 4
    s = pg.Surface((2 * L // q, 2 * L // q), pg.SRCALPHA if color is None else 0)
    c = L // q
    steps = 36
    for i in range(steps):
        r = (L // q) * (1 - i / steps)
        k = peak * (i / steps) ** .9
        pts = [(c, c)] + [(c + r * math.cos(a), c + r * math.sin(a)) for a in [-half + j / 12 * 2 * half for j in range(13)]]
        if color is None:
            pg.draw.polygon(s, (0, 0, 0, int(255 * k)), pts)
        else:
            pg.draw.polygon(s, tuple(int(v * k) for v in color), pts)
    return pg.transform.smoothscale(s, (2 * L, 2 * L))


def radial_mask(R, peak=255):
    s = pg.Surface((2 * R, 2 * R), pg.SRCALPHA)
    for i in range(40):
        r = R * (1 - i / 40)
        pg.draw.circle(s, (0, 0, 0, int(peak * min(1, (i / 40) ** .8 * 1.4))), (R, R), r)
    return s


_GRAD = {}


def vgrad(c0, c1, w=W, h=H):
    key = (tuple(v // 3 for v in c0), tuple(v // 3 for v in c1), w, h)
    g = _GRAD.get(key)
    if g is None:
        if len(_GRAD) > 300:
            _GRAD.clear()
        g = _GRAD[key] = _vgrad(c0, c1, w, h)
    return g


_ROT = {}


def rotated(img, deg, tag):
    key = (tag, int(deg // 3) % 120)
    r = _ROT.get(key)
    if r is None:
        r = _ROT[key] = pg.transform.rotate(img, key[1] * 3)
    return r


def _vgrad(c0, c1, w=W, h=H):
    t = pg.Surface((1, 16))
    for i in range(16):
        t.set_at((0, i), mix(c0, c1, i / 15))
    return pg.transform.smoothscale(t, (w, h))


# ---------------------------------------------------------------- species
SEA = [
    dict(id="coral", name="אלמוגים", min=0, max=150, fact="אלמוגים הם בעלי חיים זעירים שבונים יחד שוניות ענקיות."),
    dict(id="reef", name="להקת דגים", min=0, max=150, n=12, spd=(30, 60), len=60, var=4, fact="דגים שוחים בלהקה כדי שיהיה קשה לטורפים לבחור אחד מהם."),
    dict(id="clown", name="דג ליצן", min=3, max=60, n=6, spd=(20, 40), len=30, fact="דג הליצן גר בתוך שושנת ים ולא נעקץ ממנה."),
    dict(id="seahorse", name="סוסון ים", min=8, max=80, n=5, spd=(4, 10), len=30, fact="אצל סוסוני ים, האבא הוא זה שנושא את הביצים בכיס."),
    dict(id="turtle", name="צב ים", min=10, max=120, n=5, spd=(25, 45), len=60, fact="צבי ים שוחים אלפי קילומטרים וחוזרים להטיל ביצים בחוף שבו נולדו."),
    dict(id="dolphin", name="דולפין", min=3, max=110, n=7, spd=(80, 130), len=100, fact="דולפינים קוראים זה לזה בשריקות מיוחדות, כמו בשמות."),
    dict(id="octopus", name="תמנון", min=60, max=260, n=5, spd=(8, 18), len=40, fact="לתמנון יש שלושה לבבות ודם בצבע כחול."),
    dict(id="shark", name="כריש", min=90, max=320, n=5, spd=(45, 75), len=150, fact="לכרישים אין עצמות. השלד שלהם עשוי סחוס, כמו האוזן שלנו."),
    dict(id="whale", name="לוויתן", min=160, max=460, n=4, spd=(18, 30), len=300, fact="הלוויתן הכחול הוא בעל החיים הגדול ביותר שחי אי פעם על כדור הארץ."),
    dict(id="jelly", name="מדוזה", min=240, max=680, n=20, spd=(5, 14), len=40, var=4, glow=1, fact="מדוזות חיות בים כבר יותר מ-500 מיליון שנה. אין להן מוח ולא לב."),
    dict(id="squid", name="דיונון ענק", min=480, max=900, n=5, spd=(30, 55), len=230, fact="לדיונון הענק יש את העיניים הגדולות ביותר בעולם החי, בגודל כדורגל."),
    dict(id="angler", name="דג חכאי", min=640, max=985, n=7, spd=(10, 22), len=80, glow=1, fact="דג החכאי מושך טרף בעזרת פנס קטן שזוהר מעל הראש שלו."),
    dict(id="boss", name="בוס הכרישים", min=880, max=1000, fact="שומר על האוצר בקרקעית. הוא רואה רק קדימה, אז חכו שיסתובב ושחו מאחוריו!"),
    dict(id="chest", name="תיבת אוצר", min=1000, max=1000, fact="מצאתם את האוצר בקרקעית הים! אמיצים במיוחד."),
]
SKY = [
    dict(id="cloud", name="עננים", min=110, max=490, fact="ענן גדול יכול לשקול כמו 100 פילים. הוא מרחף כי הוא עשוי מטיפות מים זעירות."),
    dict(id="bird", name="להקת שחפים", min=5, max=220, n=12, spd=(60, 110), len=80, hazard=1, hit=30, var=3, fact="ציפורים נודדות עפות אלפי קילומטרים בכל שנה ומוצאות את הדרך לפי השמש והכוכבים."),
    dict(id="balloon", name="בלון פורח", min=40, max=240, n=5, spd=(10, 20), len=80, var=4, fact="בלון פורח עולה למעלה כי אוויר חם קל יותר מאוויר קר."),
    dict(id="heli", name="מסוק", min=15, max=180, n=4, spd=(50, 80), len=140, hazard=1, hit=34, fact="מסוק יכול לרחף במקום אחד, לטוס אחורה ואפילו הצידה."),
    dict(id="plane", name="מטוס נוסעים", min=220, max=520, n=6, spd=(150, 210), len=260, hazard=1, hit=40, fact="מטוסי נוסעים טסים בגובה של בערך 10 קילומטרים, מעל רוב העננים."),
    dict(id="jet", name="מטוס קרב", min=430, max=620, n=5, spd=(250, 330), len=140, hazard=1, hit=28, fact="מטוסי קרב יכולים לטוס מהר יותר מהקול."),
    dict(id="wballoon", name="בלון מזג אוויר", min=450, max=640, n=4, spd=(6, 12), len=60, fact="בלון מזג אוויר מתנפח ככל שהוא עולה, עד שהוא מתפוצץ בגובה של כ-30 קילומטר."),
    dict(id="aurora", name="זוהר צפוני", min=620, max=760, fact="הזוהר הצפוני נוצר כשחלקיקים מהשמש פוגעים באוויר שמעל כדור הארץ."),
    dict(id="meteor", name="מטאור", min=600, max=880, n=10, spd=(190, 280), len=60, hazard=1, hit=24, fact="כוכב נופל הוא בעצם אבן קטנה מהחלל שנשרפת כשהיא נכנסת לאוויר."),
    dict(id="satellite", name="לוויין", min=760, max=990, n=6, spd=(30, 50), len=130, fact="אלפי לוויינים מקיפים את כדור הארץ. הם עוזרים לנו בניווט, בטלוויזיה ובתחזית."),
    dict(id="iss", name="תחנת החלל", min=820, max=930, n=1, spd=(22, 22), len=320, fact="בתחנת החלל גרים אסטרונאוטים, והיא מקיפה את כדור הארץ בערך כל 90 דקות."),
    dict(id="astronaut", name="אסטרונאוט", min=760, max=980, n=3, spd=(8, 15), len=50, fact="בחלל הכול מרחף, אז אסטרונאוטים ישנים בשקי שינה שקשורים לקיר."),
    dict(id="ufo", name="בוס החייזרים", min=930, max=1000, fact="שומר על כוכב הזהב. הקרן שלו מאירה רק קדימה, אז חכו שיסתובב וטוסו מאחוריו!"),
    dict(id="goldstar", name="כוכב הזהב", min=1000, max=1000, fact="הגעתם לחלל ולקחתם את כוכב הזהב! טייס אמיתי."),
]
SPACE = [
    dict(id="earth", name="כדור הארץ", min=0, max=40, fact="מהחלל רואים שכדור הארץ מכוסה ברובו במים, בערך 71 אחוז."),
    dict(id="rocket", name="רקטה", min=30, max=380, n=6, spd=(120, 180), len=120, hazard=1, hit=22, fact='כדי להישאר במסלול סביב כדור הארץ, רקטה צריכה לטוס בערך 28,000 קמ"ש.'),
    dict(id="saucer", name="צלחת מעופפת", min=120, max=700, n=9, spd=(60, 110), len=80, hazard=1, hit=18, var=3, fact="אף אחד עוד לא מצא חייזרים, אבל מדענים מחפשים סימני חיים על כוכבי לכת רחוקים."),
    dict(id="comet", name="שביט", min=250, max=350, fact="לשביט יש זנב שתמיד מצביע הרחק מהשמש."),
    dict(id="saturn", name="שבתאי", min=300, max=650, fact="הטבעות של שבתאי עשויות מגושי קרח וסלעים. חלקם קטנים כמו גרגר חול וחלקם גדולים כמו בית."),
    dict(id="asteroid", name="אסטרואיד", min=300, max=620, n=16, spd=(15, 40), len=56, hazard=1, hit=24, fact="רוב האסטרואידים במערכת השמש נמצאים בחגורה בין מאדים לצדק."),
    dict(id="fighter", name="חללית קרב", min=520, max=900, n=9, spd=(200, 290), len=110, hazard=1, hit=22, fact="חלליות קרב של חייזרים קיימות רק בסרטים ובמשחקים. לפחות עד כמה שאנחנו יודעים!"),
    dict(id="mothership", name="ספינת האם", min=700, max=900, n=2, spd=(25, 40), len=330, hazard=1, hit=34, fact="ספינת האם של החייזרים ענקית ואיטית. עקפו אותה מהצד!"),
    dict(id="moon", name="הירח", min=720, max=1000, fact="כוח המשיכה על הירח חלש פי 6 מאשר על כדור הארץ, אז אפשר לקפוץ שם גבוה מאוד!"),
    dict(id="rover", name="רכב ירח", min=900, max=1000, fact="אסטרונאוטים נהגו על הירח ברכב חשמלי מיוחד כבר בשנת 1971."),
    dict(id="flag", name="הדגל שלכם", min=1000, max=1000, fact="נחתתם על הירח ושתלתם את הדגל שלכם! אסטרונאוט אמיתי."),
]
SP = {s["id"]: s for s in SEA + SKY + SPACE}

# ---------------------------------------------------------------- languages
LANG = "he"
LANG_NAMES = [("he", "עברית"), ("ar", "العربية"), ("ru", "Русский"), ("en", "English")]
SKINS = ["cat", "dog", "rabbit", "turtle"]

UI = {
    "he": dict(
        z_surface="על פני המים", z_reef="שונית האלמוגים", z_open="המים הפתוחים", z_twilight="אזור הדמדומים", z_midnight="אזור החצות", z_floor="קרקעית הים",
        z_runway="על מסלול ההמראה", z_city="שמי העיר", z_clouds="בין העננים", z_high="השמיים הגבוהים", z_edge="סף החלל", z_space="החלל", z_orbit="מסלול סביב כדור הארץ",
        z_eorbit="מסלול סביב כדור הארץ", z_ospace="החלל הפתוח", z_asteroids="שדה האסטרואידים", z_fleet="צי החייזרים", z_above="מעל הירח", z_onmoon="על הירח",
        m="מטר", m_short="מ'", km='ק"מ', km_moon='ק"מ לירח', oxygen="חמצן", fuel="דלק", log="יומן תגליות", found="גילית: {x}!",
        low_o2="חמצן נמוך!", low_o2_b="אספו בועות חמצן זוהרות או עלו למעלה.", low_o2_space="אספו מכלי חמצן כחולים.",
        low_fuel="דלק נמוך!", low_fuel_b="אספו מכלי דלק או נחתו על המסלול.",
        jelly="אאוץ', מדוזה!", jelly_b="מדוזות עוקצות. היא לקחה לך קצת חמצן.",
        bite="הבוס נשך אותך!", bite_b="איבדת הרבה חמצן. חכו שיסתובב והתגנבו מאחוריו.",
        zap="זאפ! בוס החייזרים פגע בך", zap_b="איבדת הרבה דלק. חכו שיסתובב וטוסו מאחוריו.",
        hit_bird="שחפים!", hit_heli="זהירות, מסוק!", hit_plane="כמעט התנגשת במטוס!", hit_jet="מטוס קרב!", hit_meteor="מטאור!",
        hit_rocket="זהירות, רקטה!", hit_saucer="צלחת מעופפת!", hit_asteroid="אסטרואיד!", hit_fighter="חללית קרב!", hit_mothership="ספינת האם!",
        ouch="אאוץ'!", lost_fuel="איבדת קצת דלק.", lost_o2="איבדת קצת חמצן.",
        hard="נחיתה קשה!", hard_b="האטו לפני הנחיתה: לחצו למעלה כדי לבלום.", soft="נחיתה מושלמת!", soft_b="שותלים את הדגל על הירח...",
        subtitle="3 שלבים: ים, שמיים וחלל",
        intro="בחרו שלב. בים צוללים עד הקרקעית ועוקפים את בוס הכרישים. בשמיים טסים מהעיר עד החלל ועוקפים את בוס החייזרים. ובחלל מתחמקים מחלליות ומאסטרואידים, נוחתים על הירח ושותלים שם דגל.",
        controls="חיצים או WASD כדי לזוז · לחיצה ממושכת עם העכבר לכיוון שרוצים · L ליומן",
        stage="שלב {n}", change_hero="החלפת דמות", language="שפה", choose_lang="בחרו שפה", play="שחקו!", choose_hero="בחרו דמות", next="המשך",
        over_sea="נגמר החמצן!", over_sea_b="עליתם מהר בחזרה לסירה. הגעתם לעומק {d} מטר וגיליתם {n} מתוך {t} תגליות.",
        win_sea="מצאתם את האוצר!", win_sea_b="עקפתם את בוס הכרישים ולקחתם את האוצר מקרקעית הים. ביומן יש {n} מתוך {t} תגליות. עכשיו מחכה שלב 2: {r}!",
        over_sky="נגמר הדלק!", over_sky_b="המטוס גלש בחזרה למסלול. הגעתם לגובה {a} וגיליתם {n} מתוך {t} תגליות.",
        win_sky="כוכב הזהב שלכם!", win_sky_b="עקפתם את בוס החייזרים ולקחתם את כוכב הזהב בחלל. ביומן יש {n} מתוך {t} תגליות. עכשיו מחכה שלב 3: {r}!",
        over_space="נגמר החמצן!", over_space_b="חזרתם לתחנת החלל למלא חמצן. נשארו {k} עד הירח, וגיליתם {n} מתוך {t} תגליות.",
        win_space="הדגל על הירח!", win_space_b="התחמקתם מכל החלליות, נחתתם על הירח ושתלתם את הדגל. ניצחתם במשחק! ביומן יש {n} מתוך {t} תגליות.",
        dive_again="לצלול שוב", to_stage="לשלב {k}: {r}", keep="להמשיך לחקור", fly_again="לטוס שוב", back_sea="לחזור לים", menu="לתפריט", play_again="לשחק שוב",
        close="סגירה", not_found="עוד לא גילית. המשיכו לחקור כדי למצוא.", scroll="גללו עם העכבר לעוד תגליות",
        and_up="{v} ומעלה", from_moon="{v} מהירח", on_moon="על הירח",
    ),
    "en": dict(
        z_surface="At the surface", z_reef="Coral reef", z_open="Open water", z_twilight="Twilight zone", z_midnight="Midnight zone", z_floor="Sea floor",
        z_runway="On the runway", z_city="Over the city", z_clouds="Among the clouds", z_high="High sky", z_edge="Edge of space", z_space="Space", z_orbit="Orbit around Earth",
        z_eorbit="Earth orbit", z_ospace="Open space", z_asteroids="Asteroid field", z_fleet="Alien fleet", z_above="Above the Moon", z_onmoon="On the Moon",
        m="m", m_short="m", km="km", km_moon="km to the Moon", oxygen="Oxygen", fuel="Fuel", log="Discovery log", found="Discovered: {x}!",
        low_o2="Low oxygen!", low_o2_b="Collect glowing oxygen bubbles or swim up.", low_o2_space="Collect blue oxygen tanks.",
        low_fuel="Low fuel!", low_fuel_b="Grab fuel cans or land on the runway.",
        jelly="Ouch, a jellyfish!", jelly_b="Jellyfish sting. It took some of your oxygen.",
        bite="The boss bit you!", bite_b="You lost a lot of oxygen. Wait for it to turn and sneak behind it.",
        zap="Zap! The Alien Boss got you", zap_b="You lost a lot of fuel. Wait for it to turn and fly behind it.",
        hit_bird="Gulls!", hit_heli="Watch out, helicopter!", hit_plane="That plane was close!", hit_jet="Fighter jet!", hit_meteor="Meteor!",
        hit_rocket="Watch out, rocket!", hit_saucer="Flying saucer!", hit_asteroid="Asteroid!", hit_fighter="Alien fighter!", hit_mothership="Mothership!",
        ouch="Ouch!", lost_fuel="You lost a little fuel.", lost_o2="You lost a little oxygen.",
        hard="Hard landing!", hard_b="Slow down before landing: press up to brake.", soft="Perfect landing!", soft_b="Planting the flag on the Moon...",
        subtitle="3 stages: sea, sky and space",
        intro="Pick a stage. In the sea, dive to the bottom and sneak past the Shark Boss. In the sky, fly from the city to space and get around the Alien Boss. In space, dodge spaceships and asteroids, land on the Moon and plant your flag.",
        controls="Arrows or WASD to move · hold the mouse where you want to go · L for the log",
        stage="Stage {n}", change_hero="Change hero", language="Language", choose_lang="Choose a language", play="Play!", choose_hero="Choose your hero", next="Continue",
        over_sea="Out of oxygen!", over_sea_b="You swam quickly back to the boat. You reached {d} m deep and made {n} of {t} discoveries.",
        win_sea="You found the treasure!", win_sea_b="You got past the Shark Boss and took the treasure from the sea floor. Your log has {n} of {t} discoveries. Next up, stage 2: {r}!",
        over_sky="Out of fuel!", over_sky_b="The plane glided back to the runway. You reached {a} and made {n} of {t} discoveries.",
        win_sky="The golden star is yours!", win_sky_b="You got past the Alien Boss and took the golden star in space. Your log has {n} of {t} discoveries. Next up, stage 3: {r}!",
        over_space="Out of oxygen!", over_space_b="You headed back to the space station for more oxygen, {k} short of the Moon. You made {n} of {t} discoveries.",
        win_space="Flag on the Moon!", win_space_b="You dodged every spaceship, landed on the Moon and planted your flag. You beat the game! Your log has {n} of {t} discoveries.",
        dive_again="Dive again", to_stage="Stage {k}: {r}", keep="Keep exploring", fly_again="Fly again", back_sea="Back to the sea", menu="Menu", play_again="Play again",
        close="Close", not_found="Not found yet. Keep exploring to find it.", scroll="Scroll with the mouse for more",
        and_up="{v} and up", from_moon="{v} from the Moon", on_moon="On the Moon",
    ),
    "ru": dict(
        z_surface="На поверхности", z_reef="Коралловый риф", z_open="Открытое море", z_twilight="Сумеречная зона", z_midnight="Полуночная зона", z_floor="Морское дно",
        z_runway="На взлётной полосе", z_city="Над городом", z_clouds="Среди облаков", z_high="Высокое небо", z_edge="Край космоса", z_space="Космос", z_orbit="Орбита Земли",
        z_eorbit="Орбита Земли", z_ospace="Открытый космос", z_asteroids="Поле астероидов", z_fleet="Флот пришельцев", z_above="Над Луной", z_onmoon="На Луне",
        m="м", m_short="м", km="км", km_moon="км до Луны", oxygen="Кислород", fuel="Топливо", log="Журнал открытий", found="Открытие: {x}!",
        low_o2="Мало кислорода!", low_o2_b="Собирайте светящиеся пузырьки кислорода или всплывайте.", low_o2_space="Собирайте синие баллоны с кислородом.",
        low_fuel="Мало топлива!", low_fuel_b="Собирайте канистры с топливом или садитесь на полосу.",
        jelly="Ай, медуза!", jelly_b="Медузы жалятся. Она отняла немного кислорода.",
        bite="Босс укусил вас!", bite_b="Вы потеряли много кислорода. Дождитесь, пока он повернётся, и проскользните сзади.",
        zap="Зап! Босс пришельцев попал в вас", zap_b="Вы потеряли много топлива. Дождитесь, пока он повернётся, и пролетите сзади.",
        hit_bird="Чайки!", hit_heli="Осторожно, вертолёт!", hit_plane="Чуть не врезались в самолёт!", hit_jet="Истребитель!", hit_meteor="Метеор!",
        hit_rocket="Осторожно, ракета!", hit_saucer="Летающая тарелка!", hit_asteroid="Астероид!", hit_fighter="Корабль пришельцев!", hit_mothership="Корабль-матка!",
        ouch="Ай!", lost_fuel="Вы потеряли немного топлива.", lost_o2="Вы потеряли немного кислорода.",
        hard="Жёсткая посадка!", hard_b="Сбавьте скорость перед посадкой: нажмите вверх, чтобы затормозить.", soft="Идеальная посадка!", soft_b="Ставим флаг на Луне...",
        subtitle="3 уровня: море, небо и космос",
        intro="Выберите уровень. В море нырните до дна и проскользните мимо Босса акул. В небе долетите от города до космоса и обойдите Босса пришельцев. В космосе уворачивайтесь от кораблей и астероидов, сядьте на Луну и поставьте флаг.",
        controls="Стрелки или WASD — движение · зажмите мышь там, куда хотите · L — журнал",
        stage="Уровень {n}", change_hero="Сменить героя", language="Язык", choose_lang="Выберите язык", play="Играть!", choose_hero="Выберите героя", next="Далее",
        over_sea="Кислород закончился!", over_sea_b="Вы быстро всплыли к лодке. Вы достигли глубины {d} м и сделали {n} из {t} открытий.",
        win_sea="Вы нашли сокровище!", win_sea_b="Вы обошли Босса акул и забрали сокровище со дна. В журнале {n} из {t} открытий. Дальше уровень 2: {r}!",
        over_sky="Топливо закончилось!", over_sky_b="Самолёт спланировал обратно на полосу. Вы поднялись на {a} и сделали {n} из {t} открытий.",
        win_sky="Золотая звезда ваша!", win_sky_b="Вы обошли Босса пришельцев и забрали золотую звезду. В журнале {n} из {t} открытий. Дальше уровень 3: {r}!",
        over_space="Кислород закончился!", over_space_b="Вы вернулись на космическую станцию за кислородом. До Луны оставалось {k}, и вы сделали {n} из {t} открытий.",
        win_space="Флаг на Луне!", win_space_b="Вы увернулись от всех кораблей, сели на Луну и поставили флаг. Вы прошли игру! В журнале {n} из {t} открытий.",
        dive_again="Нырнуть снова", to_stage="Уровень {k}: {r}", keep="Исследовать дальше", fly_again="Лететь снова", back_sea="Обратно в море", menu="Меню", play_again="Играть снова",
        close="Закрыть", not_found="Ещё не найдено. Исследуйте дальше.", scroll="Прокрутите колёсиком мыши",
        and_up="от {v}", from_moon="{v} от Луны", on_moon="На Луне",
    ),
    "ar": dict(
        z_surface="على سطح الماء", z_reef="الشعاب المرجانية", z_open="المياه المفتوحة", z_twilight="منطقة الشفق", z_midnight="منطقة منتصف الليل", z_floor="قاع البحر",
        z_runway="على المدرج", z_city="فوق المدينة", z_clouds="بين الغيوم", z_high="السماء العالية", z_edge="حافة الفضاء", z_space="الفضاء", z_orbit="مدار حول الأرض",
        z_eorbit="مدار الأرض", z_ospace="الفضاء المفتوح", z_asteroids="حقل الكويكبات", z_fleet="أسطول الفضائيين", z_above="فوق القمر", z_onmoon="على القمر",
        m="متر", m_short="م", km="كم", km_moon="كم إلى القمر", oxygen="أكسجين", fuel="وقود", log="سجل الاكتشافات", found="اكتشاف: {x}!",
        low_o2="الأكسجين منخفض!", low_o2_b="اجمع فقاعات الأكسجين المضيئة أو اصعد إلى الأعلى.", low_o2_space="اجمع أسطوانات الأكسجين الزرقاء.",
        low_fuel="الوقود منخفض!", low_fuel_b="اجمع علب الوقود أو اهبط على المدرج.",
        jelly="آخ، قنديل بحر!", jelly_b="قناديل البحر تلسع. لقد أخذ منك بعض الأكسجين.",
        bite="عضك الزعيم!", bite_b="خسرت الكثير من الأكسجين. انتظر حتى يستدير وتسلل من خلفه.",
        zap="زاب! أصابك زعيم الفضائيين", zap_b="خسرت الكثير من الوقود. انتظر حتى يستدير وطر من خلفه.",
        hit_bird="نوارس!", hit_heli="انتبه، مروحية!", hit_plane="كدت تصطدم بالطائرة!", hit_jet="طائرة مقاتلة!", hit_meteor="نيزك!",
        hit_rocket="انتبه، صاروخ!", hit_saucer="صحن طائر!", hit_asteroid="كويكب!", hit_fighter="مركبة مقاتلة!", hit_mothership="السفينة الأم!",
        ouch="آخ!", lost_fuel="خسرت قليلا من الوقود.", lost_o2="خسرت قليلا من الأكسجين.",
        hard="هبوط قاس!", hard_b="خفف سرعتك قبل الهبوط: اضغط للأعلى لتفرمل.", soft="هبوط مثالي!", soft_b="نغرس العلم على القمر...",
        subtitle="3 مراحل: البحر والسماء والفضاء",
        intro="اختر مرحلة. في البحر، اغطس حتى القاع وتسلل من وراء زعيم القروش. في السماء، طر من المدينة إلى الفضاء وتجاوز زعيم الفضائيين. وفي الفضاء، تفاد المركبات والكويكبات واهبط على القمر واغرس علمك.",
        controls="الأسهم أو WASD للحركة · اضغط مطولا بالفأرة حيث تريد · L للسجل",
        stage="المرحلة {n}", change_hero="تغيير الشخصية", language="اللغة", choose_lang="اختر اللغة", play="العب!", choose_hero="اختر شخصيتك", next="متابعة",
        over_sea="نفد الأكسجين!", over_sea_b="صعدت بسرعة إلى القارب. وصلت إلى عمق {d} متر واكتشفت {n} من {t}.",
        win_sea="وجدت الكنز!", win_sea_b="تجاوزت زعيم القروش وأخذت الكنز من قاع البحر. في سجلك {n} من {t} اكتشافات. والآن المرحلة 2: {r}!",
        over_sky="نفد الوقود!", over_sky_b="انزلقت الطائرة عائدة إلى المدرج. وصلت إلى ارتفاع {a} واكتشفت {n} من {t}.",
        win_sky="النجمة الذهبية لك!", win_sky_b="تجاوزت زعيم الفضائيين وأخذت النجمة الذهبية في الفضاء. في سجلك {n} من {t} اكتشافات. والآن المرحلة 3: {r}!",
        over_space="نفد الأكسجين!", over_space_b="عدت إلى محطة الفضاء لتملأ الأكسجين. بقي {k} حتى القمر، واكتشفت {n} من {t}.",
        win_space="العلم على القمر!", win_space_b="تفاديت كل المركبات وهبطت على القمر وغرست علمك. لقد فزت باللعبة! في سجلك {n} من {t} اكتشافات.",
        dive_again="اغطس مرة أخرى", to_stage="المرحلة {k}: {r}", keep="تابع الاستكشاف", fly_again="طر مرة أخرى", back_sea="العودة إلى البحر", menu="القائمة", play_again="العب مرة أخرى",
        close="إغلاق", not_found="لم تكتشفه بعد. تابع الاستكشاف لتجده.", scroll="مرر بالفأرة لرؤية المزيد",
        and_up="{v} وأعلى", from_moon="{v} من القمر", on_moon="على القمر",
    ),
}

SKIN_NAMES = {"he": ["חתול", "כלב", "ארנב", "צב"], "en": ["Cat", "Dog", "Bunny", "Turtle"],
              "ru": ["Кот", "Пёс", "Кролик", "Черепаха"], "ar": ["قط", "كلب", "أرنب", "سلحفاة"]}
ROLES = {
    "he": {s: [f"{n} צוללן", f"{n} טייס", f"{n} אסטרונאוט"] for s, n in zip(SKINS, SKIN_NAMES["he"])},
    "en": {s: [f"Diver {n}", f"Pilot {n}", f"Astronaut {n}"] for s, n in zip(SKINS, SKIN_NAMES["en"])},
    "ru": {s: [f"{n}-водолаз", f"{n}-пилот", f"{n}-астронавт"] for s, n in zip(SKINS, SKIN_NAMES["ru"])},
    "ar": {"cat": ["القط الغواص", "القط الطيار", "القط رائد الفضاء"], "dog": ["الكلب الغواص", "الكلب الطيار", "الكلب رائد الفضاء"],
           "rabbit": ["الأرنب الغواص", "الأرنب الطيار", "الأرنب رائد الفضاء"], "turtle": ["السلحفاة الغواصة", "السلحفاة الطيارة", "السلحفاة رائدة الفضاء"]},
}

# species names and facts for the other languages (Hebrew lives in the species lists)
TR = {
    "en": {
        "coral": ("Corals", "Corals are tiny animals that build huge reefs together."),
        "reef": ("School of fish", "Fish swim in schools so it's hard for predators to pick just one."),
        "clown": ("Clownfish", "The clownfish lives inside a sea anemone and doesn't get stung."),
        "seahorse": ("Seahorse", "With seahorses, it's the dad who carries the eggs in a pouch."),
        "turtle": ("Sea turtle", "Sea turtles swim thousands of kilometres and come back to lay eggs on the beach where they hatched."),
        "dolphin": ("Dolphin", "Dolphins call each other with special whistles, like names."),
        "octopus": ("Octopus", "An octopus has three hearts and blue blood."),
        "shark": ("Shark", "Sharks have no bones. Their skeleton is made of cartilage, like your ear."),
        "whale": ("Whale", "The blue whale is the biggest animal that has ever lived on Earth."),
        "jelly": ("Jellyfish", "Jellyfish have lived in the sea for more than 500 million years. They have no brain and no heart."),
        "squid": ("Giant squid", "The giant squid has the biggest eyes in the animal kingdom, as big as a football."),
        "angler": ("Anglerfish", "The anglerfish lures prey with a little glowing lamp on its head."),
        "boss": ("Shark Boss", "Guards the treasure on the sea floor. It only sees forward, so wait for it to turn and swim behind it!"),
        "chest": ("Treasure chest", "You found the treasure on the sea floor! Very brave."),
        "cloud": ("Clouds", "A big cloud can weigh as much as 100 elephants. It floats because it's made of tiny water droplets."),
        "bird": ("Flock of gulls", "Migrating birds fly thousands of kilometres every year and find their way by the sun and stars."),
        "balloon": ("Hot-air balloon", "A hot-air balloon rises because hot air is lighter than cold air."),
        "heli": ("Helicopter", "A helicopter can hover in one spot, fly backwards and even sideways."),
        "plane": ("Airliner", "Airliners fly about 10 kilometres up, above most clouds."),
        "jet": ("Fighter jet", "Fighter jets can fly faster than sound."),
        "wballoon": ("Weather balloon", "A weather balloon swells as it rises, until it pops about 30 kilometres up."),
        "aurora": ("Northern lights", "The northern lights appear when particles from the sun hit the air high above the Earth."),
        "meteor": ("Meteor", "A shooting star is really a small space rock burning up as it enters the air."),
        "satellite": ("Satellite", "Thousands of satellites orbit the Earth. They help with navigation, TV and weather forecasts."),
        "iss": ("Space station", "Astronauts live on the space station, and it circles the Earth about every 90 minutes."),
        "astronaut": ("Astronaut", "In space everything floats, so astronauts sleep in sleeping bags tied to the wall."),
        "ufo": ("Alien Boss", "Guards the golden star. Its beam only shines forward, so wait for it to turn and fly behind it!"),
        "goldstar": ("Golden star", "You reached space and grabbed the golden star! A real pilot."),
        "earth": ("Earth", "From space you can see that Earth is mostly covered with water, about 71 percent."),
        "rocket": ("Rocket", "To stay in orbit around Earth, a rocket has to fly at about 28,000 km/h."),
        "saucer": ("Flying saucer", "No one has found aliens yet, but scientists are looking for signs of life on faraway planets."),
        "comet": ("Comet", "A comet's tail always points away from the sun."),
        "saturn": ("Saturn", "Saturn's rings are made of chunks of ice and rock. Some are as small as a grain of sand, others as big as a house."),
        "asteroid": ("Asteroid", "Most asteroids in the solar system are in a belt between Mars and Jupiter."),
        "fighter": ("Alien fighter", "Alien fighter ships only exist in movies and games. At least as far as we know!"),
        "mothership": ("Mothership", "The aliens' mothership is huge and slow. Go around it!"),
        "moon": ("The Moon", "Gravity on the Moon is 6 times weaker than on Earth, so you can jump really high!"),
        "rover": ("Moon buggy", "Astronauts drove a special electric car on the Moon back in 1971."),
        "flag": ("Your flag", "You landed on the Moon and planted your flag! A real astronaut."),
    },
    "ru": {
        "coral": ("Кораллы", "Кораллы — крошечные животные, которые вместе строят огромные рифы."),
        "reef": ("Стая рыб", "Рыбы плавают стаями, чтобы хищнику было трудно выбрать одну."),
        "clown": ("Рыба-клоун", "Рыба-клоун живёт в актинии, и та её не жалит."),
        "seahorse": ("Морской конёк", "У морских коньков икру в сумке вынашивает папа."),
        "turtle": ("Морская черепаха", "Морские черепахи проплывают тысячи километров и возвращаются откладывать яйца на пляж, где родились."),
        "dolphin": ("Дельфин", "Дельфины зовут друг друга особыми свистами, как по именам."),
        "octopus": ("Осьминог", "У осьминога три сердца и голубая кровь."),
        "shark": ("Акула", "У акул нет костей. Их скелет из хряща, как наше ухо."),
        "whale": ("Кит", "Синий кит — самое большое животное, когда-либо жившее на Земле."),
        "jelly": ("Медуза", "Медузы живут в море больше 500 миллионов лет. У них нет ни мозга, ни сердца."),
        "squid": ("Гигантский кальмар", "У гигантского кальмара самые большие глаза в мире животных, размером с футбольный мяч."),
        "angler": ("Рыба-удильщик", "Удильщик приманивает добычу маленьким светящимся фонариком на голове."),
        "boss": ("Босс акул", "Охраняет сокровище на дне. Он видит только вперёд: дождитесь, пока он повернётся, и проплывите сзади!"),
        "chest": ("Сундук с сокровищем", "Вы нашли сокровище на дне моря! Какая смелость!"),
        "cloud": ("Облака", "Большое облако может весить как 100 слонов. Оно парит, потому что состоит из крошечных капелек воды."),
        "bird": ("Стая чаек", "Перелётные птицы каждый год пролетают тысячи километров и находят дорогу по солнцу и звёздам."),
        "balloon": ("Воздушный шар", "Воздушный шар поднимается, потому что тёплый воздух легче холодного."),
        "heli": ("Вертолёт", "Вертолёт умеет зависать на месте, летать назад и даже боком."),
        "plane": ("Пассажирский самолёт", "Пассажирские самолёты летают на высоте около 10 километров, выше большинства облаков."),
        "jet": ("Истребитель", "Истребители могут летать быстрее звука."),
        "wballoon": ("Метеозонд", "Метеозонд раздувается по мере подъёма, пока не лопнет на высоте около 30 километров."),
        "aurora": ("Северное сияние", "Северное сияние появляется, когда частицы от Солнца сталкиваются с воздухом высоко над Землёй."),
        "meteor": ("Метеор", "Падающая звезда — это маленький камень из космоса, который сгорает, влетая в воздух."),
        "satellite": ("Спутник", "Вокруг Земли летают тысячи спутников. Они помогают с навигацией, телевидением и прогнозом погоды."),
        "iss": ("Космическая станция", "На космической станции живут космонавты, и она облетает Землю примерно за 90 минут."),
        "astronaut": ("Космонавт", "В космосе всё парит, поэтому космонавты спят в спальных мешках, привязанных к стене."),
        "ufo": ("Босс пришельцев", "Охраняет золотую звезду. Его луч светит только вперёд: дождитесь, пока он повернётся, и пролетите сзади!"),
        "goldstar": ("Золотая звезда", "Вы долетели до космоса и забрали золотую звезду! Настоящий пилот."),
        "earth": ("Земля", "Из космоса видно, что Земля в основном покрыта водой, примерно на 71 процент."),
        "rocket": ("Ракета", "Чтобы остаться на орбите Земли, ракета должна лететь со скоростью около 28 000 км/ч."),
        "saucer": ("Летающая тарелка", "Пришельцев пока никто не нашёл, но учёные ищут признаки жизни на далёких планетах."),
        "comet": ("Комета", "Хвост кометы всегда направлен в сторону от Солнца."),
        "saturn": ("Сатурн", "Кольца Сатурна состоят из кусков льда и камня. Одни размером с песчинку, другие с дом."),
        "asteroid": ("Астероид", "Большинство астероидов Солнечной системы находятся в поясе между Марсом и Юпитером."),
        "fighter": ("Корабль пришельцев", "Боевые корабли пришельцев бывают только в кино и играх. По крайней мере, насколько мы знаем!"),
        "mothership": ("Корабль-матка", "Корабль-матка пришельцев огромный и медленный. Облетите его сбоку!"),
        "moon": ("Луна", "Сила тяжести на Луне в 6 раз слабее, чем на Земле, поэтому там можно прыгать очень высоко!"),
        "rover": ("Лунный автомобиль", "Астронавты ездили по Луне на специальной электромашине ещё в 1971 году."),
        "flag": ("Ваш флаг", "Вы сели на Луну и поставили свой флаг! Настоящий космонавт."),
    },
    "ar": {
        "coral": ("المرجان", "المرجان حيوانات صغيرة جدا تبني معا شعابا ضخمة."),
        "reef": ("سرب أسماك", "تسبح الأسماك في أسراب حتى يصعب على المفترس أن يختار واحدة منها."),
        "clown": ("سمكة المهرج", "تعيش سمكة المهرج داخل شقائق النعمان البحرية ولا تلسعها."),
        "seahorse": ("فرس البحر", "عند فرس البحر، الأب هو الذي يحمل البيض في جيبه."),
        "turtle": ("سلحفاة بحرية", "تسبح السلاحف البحرية آلاف الكيلومترات وتعود لتضع بيضها على الشاطئ الذي ولدت فيه."),
        "dolphin": ("دلفين", "تنادي الدلافين بعضها بصفير خاص، كأنه أسماء."),
        "octopus": ("أخطبوط", "للأخطبوط ثلاثة قلوب ودم أزرق."),
        "shark": ("قرش", "ليس لأسماك القرش عظام. هيكلها من الغضروف، مثل الأذن عندنا."),
        "whale": ("حوت", "الحوت الأزرق هو أكبر حيوان عاش على الأرض على الإطلاق."),
        "jelly": ("قنديل البحر", "تعيش قناديل البحر في البحر منذ أكثر من 500 مليون سنة. ليس لها دماغ ولا قلب."),
        "squid": ("الحبار العملاق", "للحبار العملاق أكبر عيون في عالم الحيوان، بحجم كرة القدم."),
        "angler": ("سمكة الصياد", "تجذب سمكة الصياد فريستها بمصباح صغير يضيء فوق رأسها."),
        "boss": ("زعيم القروش", "يحرس الكنز في قاع البحر. يرى إلى الأمام فقط، فانتظر حتى يستدير واسبح من خلفه!"),
        "chest": ("صندوق الكنز", "وجدت الكنز في قاع البحر! يا لك من بطل شجاع."),
        "cloud": ("الغيوم", "قد تزن الغيمة الكبيرة مثل 100 فيل. وهي تطفو لأنها مصنوعة من قطرات ماء صغيرة جدا."),
        "bird": ("سرب نوارس", "تطير الطيور المهاجرة آلاف الكيلومترات كل عام وتجد طريقها بالشمس والنجوم."),
        "balloon": ("منطاد الهواء الساخن", "يرتفع المنطاد لأن الهواء الساخن أخف من الهواء البارد."),
        "heli": ("مروحية", "تستطيع المروحية أن تبقى في مكانها في الهواء، وأن تطير إلى الخلف وحتى إلى الجانب."),
        "plane": ("طائرة ركاب", "تطير طائرات الركاب على ارتفاع نحو 10 كيلومترات، فوق معظم الغيوم."),
        "jet": ("طائرة مقاتلة", "تستطيع الطائرات المقاتلة أن تطير أسرع من الصوت."),
        "wballoon": ("منطاد الطقس", "ينتفخ منطاد الطقس كلما ارتفع، حتى ينفجر على ارتفاع نحو 30 كيلومترا."),
        "aurora": ("الشفق القطبي", "يظهر الشفق القطبي عندما تصطدم جسيمات من الشمس بالهواء عاليا فوق الأرض."),
        "meteor": ("نيزك", "الشهاب في الحقيقة صخرة صغيرة من الفضاء تحترق عندما تدخل الهواء."),
        "satellite": ("قمر صناعي", "تدور آلاف الأقمار الصناعية حول الأرض. وهي تساعدنا في الملاحة والتلفزيون والنشرة الجوية."),
        "iss": ("محطة الفضاء", "يعيش رواد الفضاء في محطة الفضاء، وهي تدور حول الأرض كل 90 دقيقة تقريبا."),
        "astronaut": ("رائد فضاء", "في الفضاء كل شيء يطفو، لذلك ينام رواد الفضاء في أكياس نوم مربوطة بالجدار."),
        "ufo": ("زعيم الفضائيين", "يحرس النجمة الذهبية. شعاعه يضيء إلى الأمام فقط، فانتظر حتى يستدير وطر من خلفه!"),
        "goldstar": ("النجمة الذهبية", "وصلت إلى الفضاء وأخذت النجمة الذهبية! طيار حقيقي."),
        "earth": ("الأرض", "من الفضاء ترى أن الماء يغطي معظم الأرض، نحو 71 في المئة."),
        "rocket": ("صاروخ", "لكي يبقى الصاروخ في مدار حول الأرض، عليه أن يطير بسرعة نحو 28,000 كم في الساعة."),
        "saucer": ("صحن طائر", "لم يجد أحد كائنات فضائية بعد، لكن العلماء يبحثون عن علامات للحياة على كواكب بعيدة."),
        "comet": ("مذنب", "ذيل المذنب يشير دائما بعيدا عن الشمس."),
        "saturn": ("زحل", "حلقات زحل مصنوعة من قطع الجليد والصخور. بعضها صغير مثل حبة رمل وبعضها كبير مثل بيت."),
        "asteroid": ("كويكب", "توجد معظم كويكبات المجموعة الشمسية في حزام بين المريخ والمشتري."),
        "fighter": ("مركبة فضائية مقاتلة", "المركبات المقاتلة للفضائيين موجودة فقط في الأفلام والألعاب. على حد علمنا!"),
        "mothership": ("السفينة الأم", "سفينة الفضائيين الأم ضخمة وبطيئة. التف من حولها!"),
        "moon": ("القمر", "الجاذبية على القمر أضعف بست مرات منها على الأرض، لذلك يمكنك القفز عاليا جدا!"),
        "rover": ("عربة القمر", "قاد رواد الفضاء سيارة كهربائية خاصة على القمر منذ عام 1971."),
        "flag": ("علمك", "هبطت على القمر وغرست علمك! رائد فضاء حقيقي."),
    },
}


def T(key, **kw):
    s = UI.get(LANG, UI["he"]).get(key) or UI["he"][key]
    return s.format(**kw) if kw else s


def rtl(lang=None):
    return (lang or LANG) in ("he", "ar")


def role(skin, stage):
    return ROLES[LANG][skin][stage - 1]


def nm(sid):
    return SP[sid]["name"] if LANG == "he" else TR[LANG][sid][0]


def fact(sid):
    return SP[sid]["fact"] if LANG == "he" else TR[LANG][sid][1]


# ---- Arabic letter joining (pygame draws each letter on its own, so we pick the joined forms ourselves)
_AR = {"ء": (0xFE80, None, None, None)}
for _ch, _b in zip("آأؤإاةدذرزوى", (0xFE81, 0xFE83, 0xFE85, 0xFE87, 0xFE8D, 0xFE93, 0xFEA9, 0xFEAB, 0xFEAD, 0xFEAF, 0xFEED, 0xFEEF)):
    _AR[_ch] = (_b, _b + 1, None, None)
for _ch, _b in zip("ئبتثجحخسشصضطظعغفقكلمنهي", (0xFE89, 0xFE8F, 0xFE95, 0xFE99, 0xFE9D, 0xFEA1, 0xFEA5, 0xFEB1, 0xFEB5, 0xFEB9, 0xFEBD, 0xFEC1, 0xFEC5, 0xFEC9, 0xFECD, 0xFED1, 0xFED5, 0xFED9, 0xFEDD, 0xFEE1, 0xFEE5, 0xFEE9, 0xFEF1)):
    _AR[_ch] = (_b, _b + 1, _b + 2, _b + 3)
_LAMALEF = {"آ": (0xFEF5, 0xFEF6), "أ": (0xFEF7, 0xFEF8), "إ": (0xFEF9, 0xFEFA), "ا": (0xFEFB, 0xFEFC)}


def reshape_ar(s):
    def joins_next(ch):
        f = _AR.get(ch)
        return bool(f and f[2])
    out, i, n = [], 0, len(s)
    while i < n:
        ch = s[i]
        prev = s[i - 1] if i else ""
        if ch == "ل" and i + 1 < n and s[i + 1] in _LAMALEF:
            iso, fin = _LAMALEF[s[i + 1]]
            out.append(chr(fin if joins_next(prev) else iso))
            i += 2
            continue
        f = _AR.get(ch)
        if not f:
            out.append(ch)
            i += 1
            continue
        nxt = s[i + 1] if i + 1 < n else ""
        cp = joins_next(prev) and f[1] is not None
        cn = f[2] is not None and nxt in _AR and _AR[nxt][1] is not None
        out.append(chr(f[3] if cp and cn else f[1] if cp else f[2] if cn else f[0]))
        i += 1
    return "".join(out)


def shape(s, lang=None):
    lang = lang or LANG
    if lang == "he":
        return heb(s)
    if lang == "ar":
        return heb(reshape_ar(s))
    return s


SEA_STOPS = [(0, (70, 196, 222)), (60, (31, 134, 184)), (200, (18, 74, 134)), (450, (11, 35, 80)), (750, (5, 13, 38)), (1000, (2, 5, 15))]
SKY_STOPS = [(0, (150, 214, 255)), (200, (110, 186, 242)), (450, (62, 128, 210)), (600, (30, 64, 140)), (750, (11, 22, 64)), (1000, (3, 4, 14))]
KM = [(0, 0), (200, 2), (450, 12), (600, 50), (750, 100), (1000, 400)]
COLS = [hx(c) for c in ("#ff6f91", "#ff9f43", "#c56cf0", "#ffd23f", "#ff5e57", "#4bcffa", "#7bed9f")]


def stops(tbl, d):
    d = clamp(d, 0, 1000)
    for i in range(1, len(tbl)):
        if d <= tbl[i][0]:
            a, c0 = tbl[i - 1]
            b, c1 = tbl[i]
            return mix(c0, c1, (d - a) / (b - a))
    return tbl[-1][1]


def km_of(u):
    u = clamp(u, 0, 1000)
    for i in range(1, len(KM)):
        if u <= KM[i][0]:
            (a, b), (c, d) = KM[i - 1], KM[i]
            return lerp(b, d, (u - a) / (c - a))
    return 400


def fmt_alt(u):
    km = km_of(u)
    if km < 1:
        return str(round(km * 1000)), T("m")
    return (f"{km:.1f}" if km < 10 else str(round(km))), T("km")


def sea_zone(d):
    if d < 1: return T("z_surface")
    if d < 150: return T("z_reef")
    if d < 400: return T("z_open")
    if d < 700: return T("z_twilight")
    if d < 995: return T("z_midnight")
    return T("z_floor")


def km_to_moon(d):
    return round(384400 * max(0, 1 - d / 997))


def space_zone(d):
    if d < 80: return T("z_eorbit")
    if d < 300: return T("z_ospace")
    if d < 620: return T("z_asteroids")
    if d < 850: return T("z_fleet")
    if d < 995: return T("z_above")
    return T("z_onmoon")


def sky_zone(u):
    if u < 3: return T("z_runway")
    if u < 200: return T("z_city")
    if u < 450: return T("z_clouds")
    if u < 600: return T("z_high")
    if u < 750: return T("z_edge")
    if u < 990: return T("z_space")
    return T("z_orbit")



# UI colours
GOLD, FOAM, MIST, KELP, CORAL_C, ABYSS = hx("#ffc94a"), hx("#eaf8ff"), hx("#9cc7e0"), hx("#7fe0a8"), hx("#ff7a59"), hx("#04122b")


# ---------------------------------------------------------------- game
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.time = 0.0
        self.stage = 1
        self.mode = "lang"            # lang | skin | start | play | over | win
        self.log_open = False
        self.log_scroll = 0
        self.buttons = []
        self.toasts, self.toast = [], None
        self.keys = set()
        self.pointer = None
        global LANG
        self.found, self.skin = set(), "cat"
        try:
            with open(SAVE, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                data = dict(found=data)
            self.found = set(data.get("found", []))
            if data.get("lang") in UI:
                LANG = data["lang"]
            if data.get("skin") in SKINS:
                self.skin = data["skin"]
        except Exception:
            pass
        self.cat = dict(x=W / 2, y=-4, vx=0, vy=0, face=1, flap=0, hurt=0)
        self.boss = dict(x=0, y=0, dir=1, state="patrol", t=0, vx=0, vy=0, ph=0, warned=False)
        self.o2, self.cam, self.max_d, self.warned_low = 100, 0, 0, False
        self.ov = pg.Surface((W, H), pg.SRCALPHA)
        self.dark = pg.Surface((W, H), pg.SRCALPHA)
        self.vign = self._vignette()
        self.lamp_r = radial_mask(170)
        self.lamp_cone = cone_mask(430, .4, .6)
        self.lamp_beam = cone_mask(430, .3, .13, (255, 235, 190))
        self.boss_cone = cone_mask(340, .6, .3, (255, 70, 60))
        self.boss_cone_hi = cone_mask(340, .6, .55, (255, 70, 60))
        self.ufo_cone = cone_mask(340, .6, .3, (120, 255, 150))
        self.ufo_cone_hi = cone_mask(340, .6, .55, (120, 255, 150))
        self.shaft = self._shaft()
        self.caustic = self._caustic()
        self.clouds = [make_cloud() for _ in range(4)]
        self.build_sea()
        self.sky_built = False
        self.space_built = False
        self.landed = None
        self.reset_sea()
        self.cat["y"] = 40
        self.cam = -H * .3

    # ---- precomputed art
    def _vignette(self):
        s = pg.Surface((W, H), pg.SRCALPHA)
        s.fill((0, 6, 18, 120))
        for i in range(30):
            t = i / 29
            r = pg.Rect(0, 0, W * lerp(1.45, .7, t), H * lerp(1.6, .75, t))
            r.center = (W / 2, H / 2)
            pg.draw.ellipse(s, (0, 6, 18, int(120 * (1 - t) ** 1.6)), r)
        return s

    def _shaft(self):
        s = pg.Surface((300, 900), pg.SRCALPHA)
        for y in range(0, 900, 3):
            a = int(55 * (1 - y / 900) ** 1.4)
            w = lerp(30, 120, y / 900)
            x0 = y * .22
            pg.draw.rect(s, (200, 240, 255, a), (x0 + 40 - w / 2 + 40, y, w, 3))
        return s

    def _caustic(self):
        N = 96
        s = pg.Surface((N, N))
        for j in range(N):
            for i in range(N):
                u, w = i / N * TAU, j / N * TAU
                v = math.sin(u * 2 + math.sin(w * 3 + 1.3) * 1.4) + math.sin(w * 2 + math.sin(u * 3 + 2.2) * 1.4) + math.sin(u + w * 2 + .8) * .8
                b = (1 - abs(math.sin(v * 1.6))) ** 7
                s.set_at((i, j), (int(70 * b), int(82 * b), int(86 * b)))
        return pg.transform.smoothscale(s, (288, 288))

    # ---- worlds
    def mk(self, s, sign):
        k = dict(sp=s["id"], x=rnd(0, W), y=sign * rnd(s["min"], s["max"]) * PX, dir=random.choice((1, -1)),
                 spd=rnd(*s["spd"]), ph=rnd(0, 10), var=random.randrange(s.get("var", 1)), seed=random.random())
        if s["id"] == "balloon":
            k["dir"] = random.choice((1, -1))
        return k

    def build_sea(self):
        self.creatures = [self.mk(s, 1) for s in SEA if s.get("n") for _ in range(s["n"])]
        self.walls, self.rocks, self.weeds, self.far, self.corals = [[], []], [[], []], [[], []], [[], []], []
        for side in (0, 1):
            y = -20
            while y <= 158 * PX:
                w = 14 if y < 0 else rnd(18, 50) * (max(0, 1 - (y - 140 * PX) / (18 * PX)) if y > 140 * PX else 1)
                self.walls[side].append((y, w))
                if y > 0 and w > 10:
                    for _ in range(3):
                        r = rnd(5, 14)
                        self.rocks[side].append(dict(y=y + rnd(-18, 18), x=rnd(r * .5, max(r, w - r * .5)), r=r, c=hx(random.choice(["#3a4f5e", "#31444f", "#46606d", "#2a3a45", "#4a5a54"]))))
                    if random.random() < .45:
                        self.weeds[side].append(dict(y=y, w=w, len=rnd(30, 70), ph=rnd(0, 6), c=hx(random.choice(["#3f8f5a", "#5aa86a", "#7a8f3a"]))))
                y += 36
            y = 50
            while y < 150 * PX:
                self.corals.append(dict(side=side, y=y, kind=random.choice(["branch", "branch", "fan", "brain", "tube", "anem"]), c=random.choice(COLS), h=rnd(.75, 1.3)))
                y += rnd(40, 80)
            y = -80
            while y <= 360 * PX:
                self.far[side].append((y, 30 if y < 0 else rnd(50, 150) * (max(0, 1 - (y - 300 * PX) / (50 * PX)) if y > 300 * PX else 1)))
                y += 70
        self.bg = []
        for sid, n, a, b, par, spd in (("reef", 8, 0, 280, .6, (14, 28)), ("dolphin", 3, 0, 90, .6, (30, 50)), ("shark", 2, 140, 420, .55, (18, 30)),
                                       ("whale", 3, 120, 560, .5, (8, 14)), ("squid", 2, 480, 860, .5, (10, 18))):
            for _ in range(n):
                self.bg.append(dict(sp=sid, x=rnd(0, W), y=rnd(a, b) * PX, par=par, dir=random.choice((1, -1)), spd=rnd(*spd), ph=rnd(0, 10), var=random.randrange(4) if sid == "reef" else 0))
        self.kelps = [dict(x=rnd(0, 1), y=rnd(30, 190) * PX, len=rnd(260, 520), ph=rnd(0, 6)) for _ in range(16)]
        self.plank = [dict(x=rnd(0, 1), y=rnd(200, 1000) * PX, ph=rnd(0, 6), f=0, c=random.choice([(120, 255, 230), (140, 200, 255), (190, 160, 255), (255, 170, 230)])) for _ in range(360)]
        self.snow = [dict(x=random.random(), y=random.random(), r=rnd(.6, 1.8), v=rnd(4, 12)) for _ in range(70)]
        self.decor = []
        for _ in range(28):
            x = rnd(.03, .97)
            if abs(x - .5) < .08:
                continue
            self.decor.append(dict(x=x, kind=random.choice(["rock", "rock", "star", "anem", "worm", "pen", "worm"]), s=rnd(.7, 1.3), c=random.choice(COLS[:5]), rot=rnd(0, 6), ph=rnd(0, 6)))
        self.decor.sort(key=lambda d: d["kind"] != "rock")

    def build_sky(self):
        self.sky_built = True
        self.things = [self.mk(s, -1) for s in SKY if s.get("n") for _ in range(s["n"])]
        self.sky_clouds = [dict(x=rnd(-.1, 1.1), y=-rnd(110, 490) * PX, s=rnd(.7, 1.4), i=random.randrange(4), v=rnd(4, 10)) for _ in range(26)]
        self.far_clouds = [dict(x=rnd(-.1, 1.1), y=-rnd(20, 620) * PX, s=rnd(.4, .9), i=random.randrange(4), v=rnd(2, 5)) for _ in range(34)]
        self.stars = [dict(x=random.random(), y=random.random(), r=random.choice((1, 1, 1, 2)), ph=rnd(0, 6)) for _ in range(180)]
        self.buildings = []
        x = -.02
        while x < 1.05:
            w = rnd(.035, .08)
            self.buildings.append(dict(x=x, w=w, h=rnd(60, 190), c=hx(random.choice(["#7f93a8", "#90a3b6", "#6d8197", "#a3b3c2"])), win=random.random() < .8))
            x += w + rnd(.002, .012)
        self.fuel, self.smoke, self.fuel_t, self.smoke_t = [], [], 1, 0

    def reset_sea(self):
        c = self.cat
        c.update(x=W / 2, y=-4, vx=0, vy=0, hurt=0, face=1)
        self.o2, self.max_d, self.warned_low = 100, 0, False
        self.bubbles, self.puffs, self.bubble_t, self.puff_t = [], [], 1, 0
        self.cam = c["y"] - H * .42
        self.boss.update(x=W * .3, y=FLOOR - 120, dir=1, state="patrol", t=0, vx=0, vy=0, warned=False)

    def reset_sky(self):
        c = self.cat
        c.update(x=W * .25, y=-14, vx=0, vy=0, hurt=0, face=1)
        self.o2, self.max_d, self.warned_low = 100, 0, False
        self.fuel, self.smoke = [], []
        self.cam = -H * .8
        self.boss.update(x=W * .3, y=CEIL + 140, dir=1, state="patrol", t=0, vx=0, vy=0, warned=False)

    def start(self, n):
        self.stage = n
        self.log_open = False
        if n == 3:
            if not self.space_built:
                self.build_space()
            self.reset_space()
        elif n == 2:
            if not self.sky_built:
                self.build_sky()
            self.reset_sky()
        else:
            self.reset_sea()
        self.mode = "play"

    def in_menu(self):
        return self.mode in ("lang", "skin", "start")

    def cur_list(self):
        return {1: SEA, 2: SKY, 3: SPACE}[self.stage]

    # ---- discoveries & toasts
    def discover(self, sid):
        if sid in self.found:
            return
        self.found.add(sid)
        self.save()
        self.say(T("found", x=nm(sid)), fact(sid))

    def say(self, title, body, warn=False):
        self.toasts.append(dict(title=title, body=body, warn=warn, t=2.2 if warn else 3.4, lang=LANG))

    def end(self, kind):
        self.mode = kind

    # ---- input
    def steer(self):
        k, ax, ay = self.keys, 0, 0
        if pg.K_LEFT in k or pg.K_a in k: ax -= 1
        if pg.K_RIGHT in k or pg.K_d in k: ax += 1
        if pg.K_UP in k or pg.K_w in k: ay -= 1
        if pg.K_DOWN in k or pg.K_s in k: ay += 1
        if self.pointer:
            dx, dy = self.pointer[0] - self.cat["x"], self.pointer[1] - (self.cat["y"] - self.cam)
            d = math.hypot(dx, dy)
            if d > 18:
                ax, ay = dx / d, dy / d
        l = math.hypot(ax, ay)
        if l > 1:
            ax, ay = ax / l, ay / l
        return ax, ay

    def move_cat(self, dt, ax, ay, maxv, buoy):
        c = self.cat
        c["vx"] += ax * 900 * dt
        c["vy"] += ay * 900 * dt
        dr = math.exp(-2.4 * dt)
        c["vx"] *= dr
        c["vy"] *= dr
        if buoy and not ay and c["y"] > 0:
            c["vy"] -= 14 * dt
        sp = math.hypot(c["vx"], c["vy"])
        if sp > maxv:
            c["vx"] *= maxv / sp
            c["vy"] *= maxv / sp
        c["x"] = clamp(c["x"] + c["vx"] * dt, 24, W - 24)
        c["y"] += c["vy"] * dt
        if abs(c["vx"]) > 12:
            c["face"] = 1 if c["vx"] > 0 else -1
        c["flap"] += dt * (3 + sp / 30)
        if c["hurt"] > 0:
            c["hurt"] -= dt
        return sp

    def wrap_x(self, k, m):
        if k["x"] > W + m: k["x"] = -m
        elif k["x"] < -m: k["x"] = W + m

    # ---- boss (works for both stages)
    def boss_update(self, dt, sky):
        b, c = self.boss, self.cat
        b["ph"] += dt
        b["t"] -= dt
        base = CEIL + 140 if sky else FLOOR - 120
        home = base + math.sin(self.time * .7) * (50 if sky else 55)
        L, R, V = W / 2 - W * .36, W / 2 + W * .36, 340
        reach = 55 if sky else 120
        hx_, hy_ = b["x"] + b["dir"] * reach, b["y"] + (4 if sky else 0)
        dx, dy = c["x"] - hx_, c["y"] - hy_
        sees = math.hypot(dx, dy) < 340 and abs(math.atan2(dy, dx * b["dir"])) < .6
        st = b["state"]
        if st == "patrol":
            b["x"] += b["dir"] * 85 * dt
            if b["x"] > R: b["x"], b["dir"] = R, -1
            if b["x"] < L: b["x"], b["dir"] = L, 1
            b["y"] = lerp(b["y"], home, 1 - math.exp(-2 * dt))
            if self.mode == "play" and c["hurt"] <= 0 and sees:
                b["state"], b["t"] = "alert", .55
        elif st == "alert":
            b["dir"] = 1 if c["x"] > b["x"] else -1
            if b["t"] <= 0:
                d = math.hypot(c["x"] - b["x"], c["y"] - b["y"]) or 1
                b.update(state="charge", t=1.5, vx=(c["x"] - b["x"]) / d * V, vy=(c["y"] - b["y"]) / d * V)
        elif st == "charge":
            d = math.hypot(c["x"] - b["x"], c["y"] - b["y"]) or 1
            k = 1 - math.exp(-1.5 * dt)
            b["vx"] = lerp(b["vx"], (c["x"] - b["x"]) / d * V, k)
            b["vy"] = lerp(b["vy"], (c["y"] - b["y"]) / d * V, k)
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            b["y"] = max(b["y"], CEIL + 50) if sky else min(b["y"], FLOOR - 50)
            b["dir"] = 1 if b["vx"] > 0 else -1
            if b["t"] <= 0:
                b["state"] = "return"
        else:
            tx = clamp(b["x"], L, R)
            ddx, ddy = tx - b["x"], home - b["y"]
            d = math.hypot(ddx, ddy)
            if d > 1:
                b["x"] += ddx / d * 120 * dt
                b["y"] += ddy / d * 120 * dt
            if abs(ddx) > 4:
                b["dir"] = 1 if ddx > 0 else -1
            if d < 12:
                b["state"] = "patrol"
        b["x"] = clamp(b["x"], -60, W + 60)
        if self.mode != "play":
            return
        if not b["warned"] and ((sky and c["y"] < CEIL + 560) or (not sky and c["y"] > FLOOR - 560)):
            b["warned"] = True
            self.discover("ufo" if sky else "boss")
        bite = (b["x"], b["y"]) if sky else (b["x"] + b["dir"] * 135, b["y"] + 8)
        if c["hurt"] <= 0 and math.hypot(c["x"] - bite[0], c["y"] - bite[1]) < (78 if sky else 62):
            self.o2 -= 35
            c.update(hurt=2, vy=380 if sky else -380, vx=(1 if c["x"] > b["x"] else -1) * 250)
            b["state"] = "return"
            if sky:
                self.say(T("zap"), T("zap_b"), True)
            else:
                self.say(T("bite"), T("bite_b"), True)
            if self.o2 <= 0:
                self.o2 = 0
                self.end("over")

    # ---- stage 1 update
    def update_sea(self, dt):
        for k in self.creatures:
            k["ph"] += dt
            k["x"] += k["dir"] * k["spd"] * dt
            self.wrap_x(k, SP[k["sp"]]["len"] * .6 + 40)
        for k in self.bg:
            k["ph"] += dt
            k["x"] += k["dir"] * k["spd"] * dt
            self.wrap_x(k, 200)
        if self.mode != "play":
            self.boss_update(dt, False)
            return
        c = self.cat
        ax, ay = self.steer()
        self.move_cat(dt, ax, ay, 270, True)
        if c["y"] < -6:
            c["y"], c["vy"] = -6, max(c["vy"], 0)
        if c["y"] > FLOOR - 26:
            c["y"], c["vy"] = FLOOR - 26, min(c["vy"], 0)
        depth = max(0, c["y"] / PX)
        self.max_d = max(self.max_d, depth)
        if depth < 2:
            self.o2 = min(100, self.o2 + 40 * dt)
            self.warned_low = False
        else:
            self.o2 -= (.9 + depth / 1000 * .7) * dt
        if self.o2 < 25 and not self.warned_low:
            self.warned_low = True
            self.say(T("low_o2"), T("low_o2_b"), True)
        if self.o2 <= 0:
            self.o2 = 0
            self.end("over")
            return
        self.cam = lerp(self.cam, clamp(c["y"] - H * .42, -H * .3, FLOOR - H * .82), 1 - math.exp(-6 * dt))
        self.bubble_t -= dt
        if self.bubble_t <= 0 and depth > 4:
            self.bubble_t = rnd(1.4, 2.8)
            self.bubbles.append(dict(x=rnd(40, W - 40), y=self.cam + H + 30, r=rnd(13, 17), ph=rnd(0, 6)))
        for b in self.bubbles:
            b["y"] -= 46 * dt
            b["ph"] += dt
            b["x"] += math.sin(b["ph"] * 2) * 12 * dt
            if math.hypot(b["x"] - c["x"], b["y"] - c["y"]) < b["r"] + 22:
                b["dead"] = 1
                self.o2 = min(100, self.o2 + 16)
                if self.o2 > 30:
                    self.warned_low = False
                for _ in range(6):
                    self.puffs.append(dict(x=b["x"], y=b["y"], vx=rnd(-40, 40), vy=rnd(-60, -10), life=.8, r=rnd(2, 4)))
        self.bubbles = [b for b in self.bubbles if not b.get("dead") and b["y"] > self.cam - 80]
        self.puff_t -= dt
        if self.puff_t <= 0 and c["y"] > 4:
            self.puff_t = rnd(.5, 1.1)
            self.puffs.append(dict(x=c["x"] + c["face"] * 22, y=c["y"] - 14, vx=rnd(-6, 6), vy=-55, life=2.4, r=rnd(1.8, 3.4)))
        for p in self.puffs:
            p["x"] += p["vx"] * dt + math.sin(self.time * 6 + p["r"]) * 10 * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
        self.puffs = [p for p in self.puffs if p["life"] > 0 and p["y"] > -2]
        for k in self.creatures:
            dy = k["y"] - c["y"]
            if abs(dy) > 400:
                continue
            d = math.hypot(k["x"] - c["x"], dy)
            sp = SP[k["sp"]]
            if d < sp["len"] * .5 + 110:
                self.discover(k["sp"])
            if k["sp"] == "jelly" and c["hurt"] <= 0 and d < 34:
                c["hurt"] = 1.4
                self.o2 -= 12
                c["vx"] += (c["x"] - k["x"]) * 4
                c["vy"] += (c["y"] - k["y"]) * 4
                self.say(T("jelly"), T("jelly_b"), True)
        for co in self.corals:
            if abs(co["y"] - c["y"]) < 150 and abs((W - 30 if co["side"] else 30) - c["x"]) < 170:
                self.discover("coral")
                break
        self.boss_update(dt, False)
        if self.mode == "play" and c["y"] > FLOOR - 160 and math.hypot(c["x"] - W / 2, c["y"] - (FLOOR - 30)) < 90:
            self.discover("chest")
            self.end("win")

    # ---- stage 2 update
    def update_sky(self, dt):
        for k in self.things:
            k["ph"] += dt
            sp = SP[k["sp"]]
            if k["sp"] == "meteor":
                k["x"] += k["dir"] * k["spd"] * dt
                k["y"] += k["spd"] * .6 * dt
                if k["y"] > -sp["min"] * PX or k["x"] < -140 or k["x"] > W + 140:
                    k["y"] = -rnd(sp["min"] + 60, sp["max"]) * PX
                    k["x"] = -120 if k["dir"] > 0 else W + 120
                continue
            k["x"] += k["dir"] * k["spd"] * dt
            self.wrap_x(k, sp["len"] * .6 + 60)
        for cl in self.sky_clouds + self.far_clouds:
            cl["x"] += cl["v"] * dt / W
            if cl["x"] > 1.25:
                cl["x"] = -.25
        for p in self.smoke:
            p["life"] -= dt
            p["r"] += p["g"] * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
        self.smoke = [p for p in self.smoke if p["life"] > 0]
        if self.mode != "play":
            self.boss_update(dt, True)
            return
        c = self.cat
        ax, ay = self.steer()
        sp = self.move_cat(dt, ax, ay, 280, False)
        if c["y"] > -14:
            c["y"], c["vy"] = -14, min(c["vy"], 0)
        if c["y"] < CEIL + 26:
            c["y"], c["vy"] = CEIL + 26, max(c["vy"], 0)
        alt = max(0, -c["y"] / PX)
        self.max_d = max(self.max_d, alt)
        if alt < 3:
            self.o2 = min(100, self.o2 + 40 * dt)
            self.warned_low = False
        else:
            self.o2 -= (.9 + alt / 1000 * .6) * dt
        if self.o2 < 25 and not self.warned_low:
            self.warned_low = True
            self.say(T("low_fuel"), T("low_fuel_b"), True)
        if self.o2 <= 0:
            self.o2 = 0
            self.end("over")
            return
        self.cam = lerp(self.cam, clamp(c["y"] - H * .58, CEIL - H * .18, -H * .8), 1 - math.exp(-6 * dt))
        self.smoke_t -= dt
        if self.smoke_t <= 0 and 1 < alt < 600 and sp > 40:
            self.smoke_t = .07
            self.smoke.append(dict(x=c["x"] - c["face"] * 30, y=c["y"], vx=rnd(-8, 8), vy=rnd(-8, 8), r=3, g=14, life=1.1, max=1.1, c=(235, 240, 245)))
        self.fuel_t -= dt
        if self.fuel_t <= 0 and alt > 4:
            self.fuel_t = rnd(1.5, 2.8)
            self.fuel.append(dict(x=rnd(40, W - 40), y=self.cam - 40, ph=rnd(0, 6)))
        for f in self.fuel:
            f["y"] += 40 * dt
            f["ph"] += dt
            if math.hypot(f["x"] - c["x"], f["y"] - c["y"]) < 34:
                f["dead"] = 1
                self.o2 = min(100, self.o2 + 16)
                if self.o2 > 30:
                    self.warned_low = False
                for _ in range(8):
                    self.smoke.append(dict(x=f["x"], y=f["y"], vx=rnd(-80, 80), vy=rnd(-80, 80), r=2.5, g=0, life=.6, max=.6, c=(255, 215, 90)))
        self.fuel = [f for f in self.fuel if not f.get("dead") and f["y"] < self.cam + H + 60]
        for k in self.things:
            dy = k["y"] - c["y"]
            if abs(dy) > 420:
                continue
            s = SP[k["sp"]]
            dx = k["x"] - c["x"]
            if math.hypot(dx, dy) < s["len"] * .5 + 110:
                self.discover(k["sp"])
            if s.get("hazard") and c["hurt"] <= 0:
                a, b = (48 if k["sp"] == "bird" else s["len"] * .42), s["hit"]
                if (dx / a) ** 2 + (dy / b) ** 2 < 1:
                    c.update(hurt=1.4, vx=(1 if c["x"] > k["x"] else -1) * 260, vy=(1 if c["y"] > k["y"] else -1) * 220)
                    self.o2 -= 14
                    self.say(T("hit_" + k["sp"]), T("lost_fuel"), True)
        if 110 < alt < 490:
            for cl in self.sky_clouds:
                if abs(cl["y"] - c["y"]) < 70 * cl["s"] and abs(cl["x"] * W - c["x"]) < 140 * cl["s"]:
                    self.discover("cloud")
                    break
        if 630 < alt < 760:
            self.discover("aurora")
        self.boss_update(dt, True)
        if self.mode == "play" and math.hypot(c["x"] - W / 2, c["y"] - (CEIL + 44)) < 80:
            self.discover("goldstar")
            self.end("win")

    def update(self, dt):
        self.time += dt
        if self.toast is None and self.toasts:
            self.toast = self.toasts.pop(0)
            self.toast["age"] = 0
        if self.toast:
            self.toast["age"] += dt
            if self.toast["age"] > self.toast["t"] + .35:
                self.toast = None
        if self.log_open:
            return
        if self.stage == 3:
            self.update_space(dt)
        elif self.stage == 2:
            self.update_sky(dt)
        else:
            self.update_sea(dt)

    # ================================================================ drawing
    def blit_center(self, img, x, y):
        self.screen.blit(img, (x - img.get_width() / 2, y - img.get_height() / 2))

    def put(self, sid, img, x, y, flip=False):
        """Blit a sprite so that its drawing origin lands on (x, y)."""
        w, h, cx, cy = SPR[sid][:4]
        ox, oy = cx - w / 2, cy - h / 2
        self.blit_center(img, x - (-ox if flip else ox), y - oy)

    def creature_img(self, k, speed=7):
        sp = k["sp"]
        frame = int(k["ph"] * speed)
        flip = k["dir"] < 0 and sp not in ("jelly", "balloon", "wballoon")
        return sprite(sp, frame, k.get("var", 0), flip)

    def draw_boss(self, sky):
        b, scr = self.boss, self.screen
        x, y = b["x"], b["y"] - self.cam
        if y < -320 or y > H + 320:
            return
        if b["state"] != "charge":
            reach = 55 if sky else 120
            hx_, hy_ = x + b["dir"] * reach, y + (4 if sky else 0)
            cone = (self.ufo_cone_hi if b["state"] == "alert" else self.ufo_cone) if sky else (self.boss_cone_hi if b["state"] == "alert" else self.boss_cone)
            if b["dir"] < 0:
                cone = pg.transform.flip(cone, True, False)
            scr.blit(cone, (hx_ - cone.get_width() / 2, hy_ - cone.get_height() / 2), special_flags=pg.BLEND_RGB_ADD)
        bob = math.sin(b["ph"] * 1.4) * 5 if b["state"] == "patrol" else 0
        sid = "ufo" if sky else "boss"
        img = sprite(sid, int(b["ph"] * (10 if b["state"] == "charge" else 5)), 0, b["dir"] < 0)
        if b["state"] == "charge":
            ang = math.degrees(math.atan2(b["vy"], abs(b["vx"]))) * (.4 if sky else .6)
            img = pg.transform.rotate(img, ang * (-1 if b["dir"] > 0 else 1))
        self.put(sid, img, x, y + bob, b["dir"] < 0)
        if b["state"] in ("alert", "charge"):
            ex = x if sky else x + b["dir"] * 60
            text(scr, "!", 54, GOLD, (ex, y - (100 if sky else 95)), "center", bold=True)

    def draw_diver(self):
        c = self.cat
        lamp = c["y"] > 140 * PX
        img = sprite("diver", int(c["flap"] / TAU * 8), (1 if lamp else 0, SKINS.index(self.skin)), c["face"] < 0)
        ang = -math.degrees(c["face"] * clamp(c["vy"] / 420, -.55, .55))
        img = pg.transform.rotozoom(img, ang, 1)
        if c["hurt"] > 0 and int(c["hurt"] * 12) % 2:
            img.set_alpha(110)
        self.put("diver", img, c["x"], c["y"] - self.cam, c["face"] < 0)

    def draw_pilot(self):
        c = self.cat
        alt = -c["y"] / PX
        v = (alt > 600, alt < 25, SKINS.index(self.skin))
        img = sprite("pilot", int(self.time * 20), v, c["face"] < 0)
        ang = -math.degrees(c["face"] * clamp(c["vy"] / 500, -.45, .45))
        img = pg.transform.rotozoom(img, ang, 1)
        if c["hurt"] > 0 and int(c["hurt"] * 12) % 2:
            img.set_alpha(110)
        self.put("pilot", img, c["x"], c["y"] - self.cam, c["face"] < 0)

    # ---- stage 1 scene
    def render_sea(self):
        scr, cam, t = self.screen, self.cam, self.time
        d_top, d_bot = cam / PX, (cam + H) / PX
        d_mid = max(0, (cam + H / 2) / PX)
        surf = -cam
        scr.blit(vgrad(stops(SEA_STOPS, d_top), stops(SEA_STOPS, d_bot)), (0, 0))

        if cam < 110 * PX:
            fade = clamp(1 - cam / (110 * PX), 0, 1)
            self.shaft.set_alpha(int(255 * fade))
            for i in range(7):
                x = W * (i + .3) / 7 + math.sin(t * .25 + i * 1.7) * 40
                scr.blit(self.shaft, (x - 80, surf), special_flags=0)

        ov = self.ov
        ov.fill((0, 0, 0, 0))
        def py(y, par):
            return (y - (cam + H / 2)) * par + H / 2
        if d_mid < 380:
            sc = stops(SEA_STOPS, d_mid)
            fc = (int(sc[0] * .62), int(sc[1] * .62), int(min(255, sc[2] * .77)), 200)
            for side in (0, 1):
                pts = self.far[side]
                poly = [(W if side else 0, py(pts[0][0], .45))] + [((W - w) if side else w, py(y, .45)) for y, w in pts] + [(W if side else 0, py(pts[-1][0], .45))]
                pg.draw.polygon(ov, fc, poly)
        sc = stops(SEA_STOPS, d_mid)
        silc = (int(sc[0] * .5), int(sc[1] * .5), int(min(255, sc[2] * .65)), 130)
        for k in self.bg:
            y = py(k["y"], k["par"])
            if -160 < y < H + 160:
                s = silhouette(k["sp"], int(k["ph"] * 5), k["var"], k["dir"] < 0)
                s = pg.transform.smoothscale(s, (int(s.get_width() * .6), int(s.get_height() * .6))) if k["sp"] in ("whale", "squid", "shark") else s
                s = s.copy()
                s.fill(silc, special_flags=pg.BLEND_RGBA_MULT)
                ov.blit(s, (k["x"] - s.get_width() / 2, y - s.get_height() / 2 + math.sin(k["ph"]) * 6))
        if d_mid < 240:
            kc = tuple(int(v * .5) for v in sc) + (170,)
            for kl in self.kelps:
                by = py(kl["y"], .7)
                L = kl["len"]
                if by < -20 or by - L > H + 20:
                    continue
                x = kl["x"] * W
                pts = [(x + math.sin(t * .8 + kl["ph"] + i / 12 * 3) * 24 * (i / 12), by - L * i / 12) for i in range(13)]
                pg.draw.lines(ov, kc, False, pts, 4)
                for i in range(3, 13, 2):
                    px_, py_ = pts[i]
                    pg.draw.ellipse(ov, kc, (px_, py_ - 3, 20, 7))
                    pg.draw.ellipse(ov, kc, (px_ - 20, py_ - 3, 20, 7))
        da = clamp(d_top / 400, 0, 1)
        for p in self.snow:
            p["y"] += p["v"] * .000015
            span = H * 1.2
            y = ((p["y"] * span - cam * .9) % span) - H * .1
            x = ((p["x"] + math.sin(t * .2 + p["r"] * 7) * .01) % 1) * W
            pg.draw.circle(ov, (225, 242, 255, int(255 * (.12 + da * .3) * (p["r"] / 1.8))), (x, y), p["r"])
        scr.blit(ov, (0, 0))

        if -80 < surf < H:
            for i in range(20):
                a = int(110 * (1 - i / 20))
                ov.fill((0, 0, 0, 0), (0, 0, W, 4))
                pg.draw.rect(scr, mix(stops(SEA_STOPS, 0), (225, 250, 255), a / 255 * .5), (0, surf + i * 4, W, 4))
        if surf > 0:
            self.draw_surface_sky(surf)

        if cam < 165 * PX:
            for side in (0, 1):
                pts = self.walls[side]
                poly = [(W if side else 0, pts[0][0] - cam)] + [((W - w) if side else w, y - cam) for y, w in pts] + [(W if side else 0, pts[-1][0] - cam)]
                pg.draw.polygon(scr, hx("#2a3c48"), poly)
                inner = [((W - w * .55) if side else w * .55, y - cam) for y, w in pts]
                pg.draw.polygon(scr, hx("#1a2831"), [(W if side else 0, pts[0][0] - cam)] + inner + [(W if side else 0, pts[-1][0] - cam)])
                for r in self.rocks[side]:
                    y = r["y"] - cam
                    if -30 < y < H + 30:
                        x = W - r["x"] if side else r["x"]
                        pg.draw.ellipse(scr, r["c"], (x - r["r"], y - r["r"] * .8, r["r"] * 2, r["r"] * 1.6))
                        pg.draw.ellipse(scr, shade(r["c"], .15), (x - r["r"] * .7, y - r["r"] * .6, r["r"] * 1.1, r["r"] * .7))
                for wd in self.weeds[side]:
                    y = wd["y"] - cam
                    if -90 < y < H + 20:
                        ex = W - wd["w"] if side else wd["w"]
                        dr = -1 if side else 1
                        for j in range(3):
                            sw = math.sin(t * 1.3 + wd["ph"] + j) * 10
                            pts2 = [(ex, y)] + quad((ex, y), (ex + dr * (8 + j * 6), y - wd["len"] * .5), (ex + dr * (12 + j * 8) + sw, y - (wd["len"] - j * 8)), 8)
                            pg.draw.lines(scr, wd["c"], False, pts2, 3)
            for co in self.corals:
                y = co["y"] - cam
                if -90 < y < H + 90:
                    img = coral_sprite(co["kind"], co["c"], co["side"], co["h"])
                    x = W - 26 if co["side"] else 26
                    scr.blit(img, (x - 65, y - 82))

        top, bot = cam - 350, cam + H + 350
        for k in self.creatures:
            if not SP[k["sp"]].get("glow") and top < k["y"] < bot:
                img = self.creature_img(k)
                bob = math.sin(k["ph"] * 1.5) * 6 if k["sp"] == "seahorse" else math.sin(k["ph"] * 1.2) * 4
                self.put(k["sp"], img, k["x"], k["y"] - cam + bob, k["dir"] < 0)

        cf = clamp(1 - d_mid / 90, 0, 1)
        if cf > .02:
            tex = self.caustic.copy()
            v = int(255 * cf)
            tex.fill((v, v, v), special_flags=pg.BLEND_RGB_MULT)
            tw = tex.get_width()
            for i, (sx, sy) in enumerate(((t * 10, -cam * .9 + t * 5), (-t * 13 + 100, -cam * .9 + t * 8 + 50))):
                ox, oy = -(sx % tw), -(sy % tw)
                y0 = max(0, surf)
                yy = oy
                while yy < H:
                    xx = ox
                    while xx < W:
                        if yy + tw > y0:
                            area = pg.Rect(0, max(0, y0 - yy), tw, tw)
                            scr.blit(tex, (xx, yy + area.y), area, special_flags=pg.BLEND_RGB_ADD)
                        xx += tw
                    yy += tw

        fy = FLOOR - cam

        def fh(x):
            return fy + math.sin(x * .02) * 8 + math.sin(x * .07) * 3
        if fy < H + 80:
            pts = [(0, H + 10)] + [(x, fh(x)) for x in range(0, W + 17, 16)] + [(W, H + 10)]
            pg.draw.polygon(scr, hx("#3a3024"), pts)
            for i, c in enumerate((hx("#4f4130"), hx("#5a4a36"))):
                pg.draw.lines(scr, c, False, [(x, fh(x) + i) for x in range(0, W + 17, 16)], 3)
            for r in range(1, 6):
                pg.draw.lines(scr, hx("#463a2c"), False, [(x, fy + r * 16 + math.sin(x * .05 + r) * 4) for x in range(0, W + 17, 16)], 2)
            for d in self.decor:
                x = d["x"] * W
                y = fh(x) + 4
                if d["kind"] == "rock":
                    r = 24 * d["s"]
                    pg.draw.ellipse(scr, hx("#26221c"), (x - r, y - r * .85, 2 * r, 1.3 * r))
                    pg.draw.ellipse(scr, hx("#4a463e"), (x - r * .8, y - r * .8, 1.4 * r, .8 * r))
                elif d["kind"] == "star":
                    r = 12 * d["s"]
                    pts = [(x + (r if i % 2 == 0 else r * .42) * math.cos(i * math.pi / 5 + d["rot"]), y + 4 + .55 * (r if i % 2 == 0 else r * .42) * math.sin(i * math.pi / 5 + d["rot"])) for i in range(10)]
                    pg.draw.polygon(scr, d["c"], pts)
                elif d["kind"] == "anem":
                    img = coral_sprite("anem", d["c"], 0, d["s"] * .8)
                    scr.blit(img, (x - 65, y - 80))

        if not self.in_menu():
            self.draw_diver()

        dk = 0 if self.in_menu() else clamp((self.cat["y"] / PX - 140) / 560, 0, 1) * .93
        if dk > 0:
            c = self.cat
            cx, cy = c["x"], c["y"] - cam
            r = c["face"] * clamp(c["vy"] / 420, -.55, .55)
            lx, ly = 23 * c["face"], -7
            hpx, hpy = cx + lx * math.cos(r) - ly * math.sin(r), cy + lx * math.sin(r) + ly * math.cos(r)
            ang = r + (math.pi if c["face"] < 0 else 0)
            self.dark.fill((0, 3, 10, int(255 * dk)))
            self.dark.blit(self.lamp_r, (cx - 170, cy - 170), special_flags=pg.BLEND_RGBA_SUB)
            cone = rotated(self.lamp_cone, -math.degrees(ang), "lamp")
            self.dark.blit(cone, (hpx - cone.get_width() / 2, hpy - cone.get_height() / 2), special_flags=pg.BLEND_RGBA_SUB)
            scr.blit(self.dark, (0, 0))
            beam = rotated(self.lamp_beam, -math.degrees(ang), "beam")
            scr.blit(beam, (hpx - beam.get_width() / 2, hpy - beam.get_height() / 2), special_flags=pg.BLEND_RGB_ADD)

        self.draw_boss(False)
        for k in self.creatures:
            if SP[k["sp"]].get("glow") and top < k["y"] < bot:
                if k["sp"] == "jelly":
                    y = k["y"] - cam + math.sin(k["ph"] * .7 + k["seed"] * 6) * 18
                    blit_glow(scr, k["x"], y - 4, 40, JELLY_COLS[k["var"]], .45)
                    img = sprite("jelly", int(k["ph"] * 4 + k["seed"] * 6), k["var"])
                    img.set_alpha(210)
                    self.put("jelly", img, k["x"], y)
                else:
                    y = k["y"] - cam + math.sin(k["ph"] * 1.2) * 4
                    fr = int(k["ph"] * 7)
                    self.put("angler", self.creature_img(k), k["x"], y, k["dir"] < 0)
                    lt = fr % 6 / 6 * TAU
                    by = -46 + math.sin(lt * .5) * 4
                    blit_glow(scr, k["x"] + 44 * k["dir"], y + by, 30, (170, 255, 225), .9)

        if d_mid > 180:
            cy = self.cat["y"] - cam
            for p in self.plank:
                y = p["y"] - cam
                if y < -10 or y > H + 10:
                    continue
                x = p["x"] * W + math.sin(t * .4 + p["ph"]) * 14
                if self.mode == "play" and abs(x - self.cat["x"]) < 80 and abs(y - cy) < 80:
                    p["f"] = 1
                else:
                    p["f"] *= .985
                vis = clamp((p["y"] / PX - 200) / 200, 0, 1)
                a = (.18 + .12 * math.sin(t * 2 + p["ph"] * 3) + p["f"] * .8) * vis
                if a > .05:
                    blit_glow(scr, x, y, 4 + p["f"] * 4, p["c"], min(1, a * .5))
                    col = tuple(int(v * min(1, a)) for v in p["c"])
                    scr.fill(col, (x - 1, y - 1, 2, 2), special_flags=pg.BLEND_RGB_ADD)

        if fy < H + 120:
            for d in self.decor:
                x = d["x"] * W
                y = fh(x) + 4
                if d["kind"] == "worm":
                    for i in range(4):
                        tx = x + (i - 1.5) * 6
                        h = (18 + i % 2 * 10) * d["s"]
                        tip = tx + math.sin(t + i) * 2
                        pg.draw.line(scr, (95, 88, 78), (tx, y), (tip, y - h), 3)
                        pulse = .5 + .5 * math.sin(t * 2 + d["ph"] + i)
                        blit_glow(scr, tip, y - h, 11, (255, 120, 200), .5 + pulse * .5)
                elif d["kind"] == "pen":
                    h = 42 * d["s"]
                    sw = math.sin(t * .8 + d["ph"]) * 4
                    pts = [(x, y)] + quad((x, y), (x + sw, y - h * .6), (x + sw * 1.5, y - h), 8)
                    pg.draw.lines(scr, (70, 150, 170), False, pts, 2)
                    for i in range(2, 9):
                        tt = i / 9
                        px_, py_ = x + sw * 1.5 * tt * tt, y - h * tt
                        a = .35 + .35 * math.sin(t * 3 - i + d["ph"])
                        blit_glow(scr, px_ - 5, py_, 6, (120, 230, 255), a)
                        blit_glow(scr, px_ + 5, py_, 6, (120, 230, 255), a)
            blit_glow(scr, W / 2, fy - 10, 230, (255, 200, 90), .32)
            blit_glow(scr, W / 2, fy - 24, 80, (255, 210, 90), .55)
            self.put("chest", sprite("chest"), W / 2, fy - 14)
            for i in range(4):
                a = t * 1.5 + i * 1.6
                rr = 30 + math.sin(t * 2 + i) * 8
                self.sparkle(W / 2 + math.cos(a) * rr, fy - 34 + math.sin(a) * rr * .5, 2 + math.sin(t * 5 + i) * 1.5)

        for b in self.bubbles:
            y = b["y"] - cam
            blit_glow(scr, b["x"], y, b["r"] * 2.2, (140, 240, 255), .35)
            pg.draw.circle(scr, (230, 252, 255), (b["x"], y), b["r"], 2)
            pg.draw.circle(scr, (255, 255, 255), (b["x"] - b["r"] * .38, y - b["r"] * .38), b["r"] * .2)
            o = font(int(b["r"] * .9), True).render("O", True, (234, 248, 255))
            two = font(int(b["r"] * .55), True).render("2", True, (234, 248, 255))
            scr.blit(o, (b["x"] - o.get_width() / 2 - 2, y - o.get_height() / 2))
            scr.blit(two, (b["x"] + o.get_width() / 2 - 2, y))
        for p in self.puffs:
            pg.draw.circle(scr, (230, 250, 255), (p["x"], p["y"] - cam), p["r"], 1)
        scr.blit(self.vign, (0, 0))

    def sparkle(self, x, y, s):
        c = (255, 246, 200)
        pg.draw.polygon(self.screen, c, [(x, y - s * 2), (x + s * .5, y), (x, y + s * 2), (x - s * .5, y)])
        pg.draw.polygon(self.screen, c, [(x - s * 2, y), (x, y + s * .5), (x + s * 2, y), (x, y - s * .5)])

    def draw_surface_sky(self, surf):
        scr, t = self.screen, self.time
        sky = vgrad(hx("#4fa8e8"), hx("#e6f7ff"), W, max(1, int(surf) + 10))
        def wave(x):
            return math.sin(x * .03 + t * 2) * 4 + math.sin(x * .011 - t * 1.3) * 3
        top_pts = [(x, surf + wave(x)) for x in range(0, W + 9, 8)]
        mask = pg.Surface((W, int(surf) + 12), pg.SRCALPHA)
        pg.draw.polygon(mask, (255, 255, 255, 255), [(0, 0), (W, 0)] + top_pts[::-1])
        sky2 = pg.Surface((W, int(surf) + 12), pg.SRCALPHA)
        sky2.blit(sky, (0, 0))
        sky2.blit(mask, (0, 0), special_flags=pg.BLEND_RGBA_MIN)
        scr.blit(sky2, (0, 0))
        sx, sy = W * .18, surf - H * .17
        blit_glow(scr, sx, sy, 120, (255, 245, 190), .6)
        pg.draw.circle(scr, hx("#fffbe0"), (sx, sy), 22)
        for cx, cy, s in ((.08, .16, 1), (.46, .1, .7), (.74, .2, 1.15)):
            x = ((cx * W + t * 7 * s) % (W + 220)) - 110
            y = surf - H * cy
            for ox, oy, r in ((0, 0, 20), (22, -10, 25), (46, 0, 19), (24, 6, 22)):
                pg.draw.ellipse(scr, (255, 255, 255), (x + ox * s - r * s, y + oy * s - r * s * .75, 2 * r * s, 1.5 * r * s))
        bx, by = W * .72, surf + math.sin(t * 1.5) * 3
        pg.draw.line(scr, hx("#6b4a2e"), (bx - 8, by - 14), (bx - 8, by - 70), 3)
        pg.draw.polygon(scr, hx("#fff8ea"), [(bx - 5, by - 66), (bx + 36, by - 22), (bx - 5, by - 22)])
        pg.draw.polygon(scr, hx("#ff7a59"), [(bx - 8, by - 70), (bx + 10, by - 65), (bx - 8, by - 60)])
        pg.draw.polygon(scr, hx("#a8461f"), [(bx - 62, by - 16), (bx + 62, by - 16)] + [(bx + x2, by + y2) for x2, y2 in quad((62, -16), (52, 4), (40, 6))] + [(bx - 44, by + 6)] + [(bx + x2, by + y2) for x2, y2 in quad((-44, 6), (-56, 2), (-62, -16))])
        pg.draw.rect(scr, (255, 255, 255), (bx - 62, by - 19, 124, 4))
        pg.draw.lines(scr, (255, 255, 255), False, top_pts, 3)

    # ---- stage 2 scene
    def render_sky(self):
        scr, cam, t = self.screen, self.cam, self.time
        a_top, a_bot = -cam / PX, -(cam + H) / PX
        a_mid = max(0, -(cam + H / 2) / PX)
        gy = -cam
        scr.blit(vgrad(stops(SKY_STOPS, a_top), stops(SKY_STOPS, max(0, a_bot))), (0, 0))
        sa = clamp((a_mid - 420) / 250, 0, 1)
        if sa > 0:
            for s in self.stars:
                span = H * 1.5
                y = ((s["y"] * span - cam * .05) % span) - H * .25
                b = int(255 * sa * (.55 + .45 * math.sin(t * 2 + s["ph"] * 5)))
                scr.fill((b, b, b), (s["x"] * W, y, s["r"], s["r"]), special_flags=pg.BLEND_RGB_MAX)
        sx, sy = W * .82, H * .15
        blit_glow(scr, sx, sy, 150, (255, 245, 200), .7 - sa * .3)
        pg.draw.circle(scr, hx("#fffbe6"), (sx, sy), 24)

        if a_mid > 620:
            ea = clamp((a_mid - 620) / 120, 0, 1)
            R = max(W, H) * 1.6
            top = H - (a_mid - 620) / 380 * H * .34
            cx, cy = W / 2, top + R
            lay = self.ov
            lay.fill((0, 0, 0, 0))
            for i in range(12):
                pg.draw.circle(lay, (130, 205, 255, int(150 * (i / 11) ** 2)), (cx, cy), R + 60 - i * 5)
            pg.draw.circle(lay, hx("#1d4f96") + (255,), (cx, cy), R)
            pg.draw.circle(lay, hx("#3b88d6") + (255,), (cx, cy + 6), R - 4)

            def top_at(x):
                return cy - math.sqrt(max(0, R * R - (x - cx) ** 2))
            for fx, dy, rx, ry, c in ((.1, 40, 110, 30, hx("#4f9a52")), (.45, 70, 160, 40, hx("#5aa35a")), (.8, 30, 90, 26, hx("#c9b071")), (.3, 18, 140, 10, (255, 255, 255)), (.7, 55, 180, 12, (240, 245, 250))):
                x = ((fx * W + t * 6) % (W + 360)) - 180
                pg.draw.ellipse(lay, c + (255,), (x - rx, top_at(x) + dy - ry, 2 * rx, 2 * ry))
            lay.set_alpha(int(255 * ea))
            scr.blit(lay, (0, 0))
            lay.set_alpha(None)
            # (atmosphere rim drawn additively)
        au = clamp(1 - abs(a_mid - 690) / 110, 0, 1)
        if au > 0:
            lay = self.ov
            lay.fill((0, 0, 0, 0))
            for i, (c, yy) in enumerate((((120, 255, 170), .22), ((90, 220, 255), .34), ((255, 120, 220), .46))):
                t0 = H * yy
                for band in range(6):
                    off = band * 28
                    k = .2 * au * max(0, 1 - abs(band - 2) / 3)
                    pts = [(x, t0 + off + math.sin(x * .006 + t * .4 + i * 2) * 40) for x in range(0, W + 9, 16)]
                    pts2 = [(x, y + 30) for x, y in pts]
                    pg.draw.polygon(lay, tuple(int(v * k) for v in c) + (255,), pts + pts2[::-1])
                scr.blit(lay, (0, 0), special_flags=pg.BLEND_RGB_ADD)
                lay.fill((0, 0, 0, 0))

        fc = 1 - clamp((a_mid - 420) / 220, 0, 1)
        if fc > 0:
            for cl in self.far_clouds:
                y = (cl["y"] - (cam + H / 2)) * .5 + H / 2
                if -120 < y < H + 120:
                    img = pg.transform.smoothscale(self.clouds[cl["i"]], (int(360 * cl["s"]), int(170 * cl["s"])))
                    img.set_alpha(int(130 * fc))
                    scr.blit(img, (cl["x"] * W - img.get_width() / 2, y - img.get_height() / 2))

        if gy < H + 260:
            my = (0 - (cam + H / 2)) * .5 + H / 2
            mpts = [(x, my - (70 + 40 * math.sin(x * .008) + 25 * math.sin(x * .021 + 1))) for x in range(0, W + 13, 12)]
            pg.draw.polygon(scr, hx("#93b6d2"), [(0, H + 10)] + mpts + [(W, H + 10)])
            cy2 = (0 - (cam + H / 2)) * .82 + H / 2
            for b in self.buildings:
                bx, bw, bh = b["x"] * W, b["w"] * W, b["h"]
                pg.draw.rect(scr, b["c"], (bx, cy2 - bh, bw, bh + H))
                pg.draw.rect(scr, shade(b["c"], -.12), (bx + bw * .7, cy2 - bh, bw * .3, bh + H))
                if b["win"]:
                    r = 0
                    wy = cy2 - bh + 8
                    while wy < cy2 - 6:
                        cnum = 0
                        wx = bx + 5
                        while wx < bx + bw - 6:
                            if (r * 3 + cnum * 7) % 5:
                                pg.draw.rect(scr, mix(b["c"], (255, 244, 200), .55), (wx, wy, 4, 6))
                            wx += 10
                            cnum += 1
                        wy += 14
                        r += 1
            if gy < H + 20:
                scr.blit(vgrad(hx("#78c463"), hx("#3f7f3a"), W, 140), (0, gy))
                if gy + 140 < H:
                    pg.draw.rect(scr, hx("#3f7f3a"), (0, gy + 140, W, H))
                for i in range(9):
                    tx, ty = ((i * .137 + .05) % 1) * W, gy + 38 + (i % 3) * 10
                    pg.draw.rect(scr, hx("#5a3a20"), (tx - 2, ty - 4, 4, 10))
                    pg.draw.ellipse(scr, hx("#4f9a4a") if i % 2 else hx("#3f8a42"), (tx - 11, ty - 22, 22, 24))
                pg.draw.rect(scr, hx("#4a4f57"), (0, gy + 2, W, 22))
                for x in range(10, W, 46):
                    pg.draw.rect(scr, hx("#f4f4f0"), (x, gy + 12, 24, 3))
                pg.draw.rect(scr, hx("#d8d8d0"), (0, gy + 3, W, 2))
                pg.draw.rect(scr, hx("#d8d8d0"), (0, gy + 21, W, 2))
                tx = W * .9
                pg.draw.rect(scr, hx("#d9dfe5"), (tx - 6, gy - 70, 12, 70))
                pg.draw.rect(scr, hx("#3c5a78"), (tx - 16, gy - 90, 32, 20), border_radius=4)
                pg.draw.rect(scr, hx("#9fe3ff"), (tx - 13, gy - 86, 26, 10))
                pg.draw.circle(scr, hx("#ff4d4d") if math.sin(t * 4) > 0 else hx("#7a2a2a"), (tx, gy - 93), 3)

        top, bot = cam - 400, cam + H + 400
        for k in self.things:
            if top < k["y"] < bot:
                sp = k["sp"]
                bob = math.sin(k["ph"] * .8) * 8 if sp in ("balloon", "wballoon", "astronaut") else math.sin(k["ph"] * 1.5) * 3
                y = k["y"] - cam + bob
                if sp == "plane":
                    pass
                if sp == "meteor":
                    img = sprite("meteor", int(k["ph"] * 8), 0, k["dir"] < 0)
                    img = pg.transform.rotozoom(img, -31 if k["dir"] > 0 else 31, 1)
                    blit_glow(scr, k["x"], y, 30, (255, 150, 60), .6)
                    self.blit_center(img, k["x"], y)
                    continue
                if sp == "plane":
                    trail = pg.Surface((300, 5), pg.SRCALPHA)
                    for i in range(30):
                        pg.draw.rect(trail, (255, 255, 255, int(140 * i / 30)), (i * 10, 0, 10, 5))
                    if k["dir"] < 0:
                        trail = pg.transform.flip(trail, True, False)
                    scr.blit(trail, (k["x"] - k["dir"] * 130 - (300 if k["dir"] > 0 else 0), y - 3))
                speed = {"heli": 14, "jet": 12, "bird": 9}.get(sp, 5)
                self.put(sp, self.creature_img(k, speed), k["x"], y, k["dir"] < 0 and sp not in ("balloon", "wballoon"))

        for f in self.fuel:
            x, y = f["x"] + math.sin(f["ph"] * 2) * 6, f["y"] - cam
            blit_glow(scr, x, y, 36, (255, 220, 90), .45)
            pg.draw.rect(scr, hx("#8a1f15"), (x - 7, y - 20, 11, 7), 3, border_radius=2)
            pg.draw.rect(scr, hx("#ffd23f"), (x + 5, y - 20, 4, 8))
            pg.draw.rect(scr, hx("#b3291c"), (x - 12, y - 14, 24, 29), border_radius=4)
            pg.draw.rect(scr, hx("#ff6b5a"), (x - 12, y - 14, 12, 29), border_radius=4)
            pg.draw.circle(scr, (255, 255, 255), (x, y + 4), 5)
            pg.draw.polygon(scr, (255, 255, 255), [(x - 4.6, y + 2.5), (x, y - 6), (x + 4.6, y + 2.5)])

        for p in self.smoke:
            a = p["life"] / p["max"]
            s = pg.Surface((int(p["r"] * 2) + 2, int(p["r"] * 2) + 2), pg.SRCALPHA)
            pg.draw.circle(s, p["c"] + (int(115 * a),), (s.get_width() / 2, s.get_height() / 2), p["r"])
            scr.blit(s, (p["x"] - s.get_width() / 2, p["y"] - cam - s.get_height() / 2))

        if not self.in_menu():
            self.draw_pilot()
        self.draw_boss(True)
        sy2 = CEIL + 44 - cam
        if -140 < sy2 < H + 140:
            blit_glow(scr, W / 2, sy2, 90, (255, 220, 90), .6)
            self.blit_center(sprite("goldstar", int(t * 4)), W / 2, sy2)
            for i in range(4):
                a = t * 1.5 + i * 1.6
                rr = 48 + math.sin(t * 2 + i) * 8
                self.sparkle(W / 2 + math.cos(a) * rr, sy2 + math.sin(a) * rr * .6, 2 + math.sin(t * 5 + i) * 1.5)
        for cl in self.sky_clouds:
            y = cl["y"] - cam
            if -120 < y < H + 120:
                img = pg.transform.smoothscale(self.clouds[cl["i"]], (int(360 * cl["s"]), int(170 * cl["s"])))
                img.set_alpha(215)
                scr.blit(img, (cl["x"] * W - img.get_width() / 2, y - img.get_height() / 2))
        va = clamp((a_mid - 350) / 400, 0, 1)
        if va > 0:
            self.vign.set_alpha(int(255 * va))
            scr.blit(self.vign, (0, 0))
            self.vign.set_alpha(None)

    # ================================================================ stage 3: חתול אסטרונאוט
    def build_space(self):
        self.space_built = True
        self.ships = []
        for s in SPACE:
            for _ in range(s.get("n", 0)):
                k = self.mk(s, 1)
                k["y0"] = k["y"]
                self.ships.append(k)
        self.sp_stars = [dict(x=random.random(), y=random.random(), r=random.choice((1, 1, 1, 2)), ph=rnd(0, 6), par=random.choice((.05, .12, .2))) for _ in range(260)]
        self.nebulae = [dict(x=rnd(0, W), y=rnd(100, 950) * PX, r=rnd(160, 320), c=random.choice([(140, 80, 255), (60, 150, 255), (255, 90, 200), (80, 220, 200)])) for _ in range(9)]
        self.craters = [dict(x=rnd(0, 1), d=rnd(20, 150), r=rnd(14, 60)) for _ in range(16)]
        self.moon_rocks = [dict(x=rnd(0, 1), d=rnd(0, 30), r=rnd(5, 16)) for _ in range(22)]
        self.rover_x = W * random.choice((.2, .8))

    def ground_y(self, x):
        R = 4000
        return MOON + (R - math.sqrt(max(0, R * R - (x - W / 2) ** 2)))

    def reset_space(self):
        c = self.cat
        c.update(x=W / 2, y=30, vx=0, vy=0, hurt=0, face=1)
        self.o2, self.max_d, self.warned_low = 100, 0, False
        self.tanks, self.tank_t, self.dust, self.landed = [], 1.2, [], None
        self.cam = -H * .25

    def update_space(self, dt):
        for k in self.ships:
            k["ph"] += dt
            sp = SP[k["sp"]]
            k["x"] += k["dir"] * k["spd"] * dt
            if k["sp"] == "saucer":
                k["y"] = k["y0"] + math.sin(k["ph"] * 1.8 + k["seed"] * 6) * 45
            self.wrap_x(k, sp["len"] * .6 + 80)
        for d in self.dust:
            d["x"] += d["vx"] * dt
            d["y"] += d["vy"] * dt
            d["vy"] += 30 * dt
            d["life"] -= dt
        self.dust = [d for d in self.dust if d["life"] > 0]
        if self.mode != "play":
            return
        c = self.cat
        if self.landed is not None:
            self.landed += dt
            c["vx"] = c["vy"] = 0
            c["flap"] += dt * 2
            if self.landed > 2.6:
                self.discover("flag")
                self.end("win")
            return
        ax, ay = self.steer()
        self.move_cat(dt, ax, ay, 260, False)
        depth = max(0, c["y"] / PX)
        if depth > 930:
            c["vy"] += 55 * dt          # the moon pulls you in
        gy = self.ground_y(c["x"]) - 22
        if c["y"] < 10:
            c["y"], c["vy"] = 10, max(c["vy"], 0)
        if c["y"] >= gy:
            if c["vy"] > 150:
                c["y"], c["vy"] = gy - 2, -190
                self.o2 -= 8
                self.say(T("hard"), T("hard_b"), True)
                self.puff_dust(c["x"], gy + 22, 10)
            else:
                c["y"], c["vy"], c["vx"] = gy, 0, 0
                self.landed = 0
                self.puff_dust(c["x"], gy + 22, 16)
                self.say(T("soft"), T("soft_b"))
                return
        self.max_d = max(self.max_d, depth)
        self.o2 -= (.9 + depth / 1000 * .6) * dt
        if self.o2 < 25 and not self.warned_low:
            self.warned_low = True
            self.say(T("low_o2"), T("low_o2_space"), True)
        if self.o2 <= 0:
            self.o2 = 0
            self.end("over")
            return
        self.cam = lerp(self.cam, clamp(c["y"] - H * .42, -H * .25, MOON - H * .8), 1 - math.exp(-6 * dt))
        self.tank_t -= dt
        if self.tank_t <= 0 and depth < 960:
            self.tank_t = rnd(1.5, 2.8)
            self.tanks.append(dict(x=rnd(40, W - 40), y=self.cam + H + 40, ph=rnd(0, 6)))
        for tk in self.tanks:
            tk["y"] -= 42 * dt
            tk["ph"] += dt
            if math.hypot(tk["x"] - c["x"], tk["y"] - c["y"]) < 34:
                tk["dead"] = 1
                self.o2 = min(100, self.o2 + 16)
                if self.o2 > 30:
                    self.warned_low = False
        self.tanks = [t for t in self.tanks if not t.get("dead") and t["y"] > self.cam - 60]
        for k in self.ships:
            dy = k["y"] - c["y"]
            if abs(dy) > 420:
                continue
            s = SP[k["sp"]]
            dx = k["x"] - c["x"]
            if math.hypot(dx, dy) < s["len"] * .5 + 110:
                self.discover(k["sp"])
            if s.get("hazard") and c["hurt"] <= 0:
                a, b = s["len"] * .42, s["hit"]
                if (dx / a) ** 2 + (dy / b) ** 2 < 1:
                    c.update(hurt=1.4, vx=(1 if c["x"] > k["x"] else -1) * 260, vy=(1 if c["y"] > k["y"] else -1) * 220)
                    self.o2 -= 14
                    self.say(T("hit_" + k["sp"]), T("lost_o2"), True)
        if depth < 40:
            self.discover("earth")
        if 300 < depth < 650 and abs(self.saturn_y() - (c["y"] - self.cam)) < 260:
            self.discover("saturn")
        if depth > 720:
            self.discover("moon")
        if depth > 900 and abs(c["x"] - self.rover_x) < 220:
            self.discover("rover")

    def saturn_y(self):
        return (420 * PX - (self.cam + H / 2)) * .25 + H / 2

    def puff_dust(self, x, y, n):
        for _ in range(n):
            self.dust.append(dict(x=x + rnd(-10, 10), y=y, vx=rnd(-90, 90), vy=rnd(-70, -10), life=rnd(.6, 1.2), r=rnd(3, 7)))

    def render_space(self):
        scr, cam, t = self.screen, self.cam, self.time
        d_mid = clamp((cam + H / 2) / PX, 0, 1000)
        top_c = mix(hx("#0b1240"), hx("#05060f"), clamp(d_mid / 500, 0, 1))
        bot_c = mix(hx("#140a30"), hx("#1a1a24"), clamp((d_mid - 700) / 300, 0, 1))
        scr.blit(vgrad(top_c, bot_c), (0, 0))
        for n in self.nebulae:
            y = (n["y"] - (cam + H / 2)) * .3 + H / 2
            if -n["r"] < y < H + n["r"]:
                blit_glow(scr, n["x"], y, n["r"], n["c"], .22)
        for s in self.sp_stars:
            span = H * 1.4
            y = ((s["y"] * span - cam * s["par"]) % span) - H * .2
            b = int(255 * (.55 + .45 * math.sin(t * 2 + s["ph"] * 5)) * (.6 + s["par"] * 2))
            b = min(255, b)
            scr.fill((b, b, b), (s["x"] * W, y, s["r"], s["r"]), special_flags=pg.BLEND_RGB_MAX)
        # Earth behind us
        ey = (-60 - (cam + H / 2)) * .4 + H / 2
        if ey > -200:
            R = W * 1.3
            blit_glow(scr, W / 2, ey, 260, (90, 170, 255), .35)
            pg.draw.circle(scr, hx("#1d4f96"), (W / 2, ey - R), R)
            pg.draw.circle(scr, hx("#3b88d6"), (W / 2, ey - R - 6), R - 4)
            for fx, dy, rx, ry, c in ((.15, -30, 120, 26, hx("#4f9a52")), (.55, -45, 170, 34, hx("#5aa35a")), (.82, -24, 90, 20, hx("#c9b071")), (.35, -14, 150, 8, (255, 255, 255)), (.7, -40, 170, 9, (240, 245, 250))):
                x = ((fx * W + t * 5) % (W + 360)) - 180
                bottom = ey - R + math.sqrt(max(0, R * R - (x - W / 2) ** 2))
                pg.draw.ellipse(scr, c, (x - rx, bottom + dy - ry, 2 * rx, 2 * ry))
        sy = self.saturn_y()
        if -120 < sy < H + 120:
            self.blit_center(sprite("saturn"), W * .78, sy)
        # comet streaks on the far layer
        cy = (300 * PX - (cam + H / 2)) * .35 + H / 2
        if -100 < cy < H + 100:
            x = ((t * 60) % (W + 600)) - 300
            blit_glow(scr, x, cy, 40, (120, 220, 255), .7)
            self.put("comet", sprite("comet", int(t * 6)), x, cy)
        mg = clamp((d_mid - 600) / 350, 0, 1)
        if mg > 0:
            blit_glow(scr, W / 2, H + 120, int(300 + 200 * mg), (200, 205, 220), .45 * mg)

        fy = self.ground_y(W / 2) - cam
        if fy < H + 60:
            R = 4000
            cxs, cys = W / 2, MOON + R - cam
            blit_glow(scr, W / 2, fy, 420, (190, 200, 215), .25)
            pg.draw.circle(scr, hx("#6e717a"), (cxs, cys), R)
            pg.draw.circle(scr, hx("#9a9da6"), (cxs, cys + 5), R - 2)
            for cr in self.craters:
                x = cr["x"] * W
                y = self.ground_y(x) - cam + cr["d"]
                if y > H + 80:
                    continue
                r = cr["r"]
                pg.draw.ellipse(scr, hx("#7c7f88"), (x - r, y - r * .32, 2 * r, r * .64))
                pg.draw.ellipse(scr, hx("#6a6d76"), (x - r * .8, y - r * .22, 1.6 * r, r * .46))
                pg.draw.arc(scr, hx("#b9bcc4"), (x - r, y - r * .32, 2 * r, r * .64), math.pi, TAU, 2)
            for rk in self.moon_rocks:
                x = rk["x"] * W
                y = self.ground_y(x) - cam + rk["d"]
                r = rk["r"]
                pg.draw.ellipse(scr, hx("#5c5f68"), (x - r, y - r * .7, 2 * r, r * 1.2))
                pg.draw.ellipse(scr, hx("#b0b3bb"), (x - r * .7, y - r * .6, r, r * .5))
            ry = self.ground_y(self.rover_x) - cam
            self.put("rover", sprite("rover"), self.rover_x, ry - 21)
            blit_glow(scr, W / 2, fy - 10, 50, (255, 230, 120), .25 if self.landed is None else 0)

        top, bot = cam - 400, cam + H + 400
        for k in self.ships:
            if top < k["y"] < bot:
                speed = {"rocket": 12, "fighter": 12, "asteroid": 3}.get(k["sp"], 6)
                img = self.creature_img(k, speed)
                if k["sp"] in ("fighter", "rocket"):
                    blit_glow(scr, k["x"] - k["dir"] * 60, k["y"] - cam, 34, (120, 220, 255) if k["sp"] == "fighter" else (255, 150, 60), .5)
                self.put(k["sp"], img, k["x"], k["y"] - cam, k["dir"] < 0)

        for tk in self.tanks:
            x, y = tk["x"] + math.sin(tk["ph"] * 2) * 6, tk["y"] - cam
            blit_glow(scr, x, y, 36, (110, 200, 255), .5)
            self.put("o2tank", sprite("o2tank"), x, y)
            o = font(12, True).render("O", True, hx("#2e86de"))
            two = font(8, True).render("2", True, hx("#2e86de"))
            scr.blit(o, (x - 6, y - 8))
            scr.blit(two, (x + 3, y - 3))

        for d in self.dust:
            s = pg.Surface((int(d["r"] * 2) + 2,) * 2, pg.SRCALPHA)
            pg.draw.circle(s, (200, 203, 210, int(160 * d["life"])), (s.get_width() / 2,) * 2, d["r"])
            scr.blit(s, (d["x"] - s.get_width() / 2, d["y"] - cam - s.get_height() / 2))

        if self.landed is not None:
            fx = self.cat["x"] + 34
            gy = self.ground_y(fx) - cam + 4
            grow = clamp(self.landed / 1.2, 0, 1)
            fimg = sprite("flag", int(t * 6), SKINS.index(self.skin))
            h = int(fimg.get_height() * grow)
            if h > 2:
                part = fimg.subsurface((0, 0, fimg.get_width(), h))
                w, hh, cx, cyy = SPR["flag"][:4]
                scr.blit(part, (fx - cx, gy - h))
        if not self.in_menu():
            c = self.cat
            img = sprite("astro", int(c["flap"] / TAU * 6), (self.landed is None, SKINS.index(self.skin)), c["face"] < 0)
            if self.landed is None:
                ang = -math.degrees(c["face"] * clamp(c["vx"] / 600, -.3, .3))
                img = pg.transform.rotozoom(img, ang, 1)
            if c["hurt"] > 0 and int(c["hurt"] * 12) % 2:
                img.set_alpha(110)
            self.put("astro", img, c["x"], c["y"] - cam, c["face"] < 0)
        scr.blit(self.vign, (0, 0))

    # ---- UI
    def button(self, label, rect, cb, primary=True, sub=None, color=None, lang=None, size=None):
        scr = self.screen
        r = pg.Rect(rect)
        hover = r.collidepoint(pg.mouse.get_pos())
        rad = r.h // 2 if not sub else 18
        if primary:
            base = color or GOLD
            pg.draw.rect(scr, shade(base, -.3), r.move(0, 4), border_radius=rad)
            pg.draw.rect(scr, shade(base, .12) if hover else base, r, border_radius=rad)
            tc = ABYSS
        else:
            s = pg.Surface(r.size, pg.SRCALPHA)
            pg.draw.rect(s, (234, 248, 255, 50 if hover else 30), s.get_rect(), border_radius=rad)
            pg.draw.rect(s, (234, 248, 255, 140), s.get_rect(), 2, border_radius=rad)
            scr.blit(s, r)
            tc = FOAM
        sz = size or (24 if sub else 19)
        while sz > 12 and font(sz, True, lang).size(shape(label, lang))[0] > r.w - 22:
            sz -= 1
        if sub:
            text(scr, sub, 13, tc, (r.centerx, r.y + 10), "midtop", shadow=False, alpha=190, lang=lang)
            text(scr, label, sz, tc, (r.centerx, r.bottom - 12), "midbottom", bold=True, shadow=False, lang=lang)
        else:
            text(scr, label, sz, tc, r.center, "center", bold=True, shadow=False, lang=lang)
        self.buttons.append((r, cb))

    def panel(self, w, h):
        scr = self.screen
        sh = pg.Surface((W, H), pg.SRCALPHA)
        sh.fill((2, 8, 22, 150))
        scr.blit(sh, (0, 0))
        r = pg.Rect(0, 0, w, h)
        r.center = (W / 2, H / 2)
        card = vgrad(hx("#0f3966"), hx("#071d3d"), w, h)
        m = pg.Surface((w, h), pg.SRCALPHA)
        pg.draw.rect(m, (255, 255, 255, 255), m.get_rect(), border_radius=22)
        c2 = pg.Surface((w, h), pg.SRCALPHA)
        c2.blit(card, (0, 0))
        c2.blit(m, (0, 0), special_flags=pg.BLEND_RGBA_MIN)
        scr.blit(c2, r)
        s = pg.Surface((w, h), pg.SRCALPHA)
        pg.draw.rect(s, (234, 248, 255, 70), s.get_rect(), 2, border_radius=22)
        scr.blit(s, r)
        return r

    def para(self, s, size, col, x, y, maxw, gap=6, anchor="midtop"):
        for line in wrap(s, size, maxw):
            r = text(self.screen, line, size, col, (x, y), anchor, shadow=False)
            y = r.bottom + gap
        return y

    def draw_toast(self):
        tt = self.toast
        if not tt:
            return
        age = tt["age"]
        a = clamp(min(age / .35, (tt["t"] + .35 - age) / .35), 0, 1)
        if a <= 0:
            return
        lg = tt.get("lang")
        lines = wrap(tt["body"], 15, 380, lang=lg)
        h = 40 + len(lines) * 20
        w = 440
        s = pg.Surface((w, h), pg.SRCALPHA)
        pg.draw.rect(s, (4, 18, 43, 215), s.get_rect(), border_radius=16)
        bc = CORAL_C if tt["warn"] else KELP
        pg.draw.rect(s, bc + (255,), s.get_rect(), 2, border_radius=16)
        text(s, tt["title"], 20, bc, (w / 2, 8), "midtop", bold=True, shadow=False, lang=lg)
        y = 36
        for ln in lines:
            text(s, ln, 15, FOAM, (w / 2, y), "midtop", shadow=False, lang=lg)
            y += 20
        s.set_alpha(int(255 * a))
        self.screen.blit(s, (W / 2 - w / 2, 96 - (1 - a) * 20))

    def open_log(self):
        self.log_open = True
        self.log_scroll = 0

    def draw_hud(self):
        scr, c = self.screen, self.cat
        if self.stage == 3:
            d = max(0, c["y"] / PX)
            n, unit, zone, lbl = f"{km_to_moon(d):,}", T("km_moon"), space_zone(d), T("oxygen")
        elif self.stage == 2:
            a = max(0, -c["y"] / PX)
            n, unit = fmt_alt(a)
            zone, lbl = sky_zone(a), T("fuel")
        else:
            d = max(0, c["y"] / PX)
            n, unit, zone, lbl = str(round(d)), T("m"), sea_zone(d), T("oxygen")
        if rtl():
            r = text(scr, n, 50, FOAM, (W - 18, 8), "topright", bold=True)
            text(scr, unit, 18, FOAM, (r.left - 8, r.bottom - 10), "bottomright")
        else:
            uw = font(18).size(shape(unit))[0]
            r = text(scr, n, 50, FOAM, (W - 26 - uw, 8), "topright", bold=True)
            text(scr, unit, 18, FOAM, (W - 18, r.bottom - 10), "bottomright")
        text(scr, zone, 14, FOAM, (W - 18, r.bottom + 2), "topright", alpha=220)
        text(scr, lbl, 15, FOAM, (190, 14), "topleft")
        bar = pg.Rect(18, 15, 165, 13)
        pg.draw.rect(scr, (4, 18, 43), bar, border_radius=7)
        fillw = int((bar.w - 4) * clamp(self.o2, 0, 100) / 100)
        if fillw > 0:
            col = (255, 94, 87) if self.o2 < 25 else (79, 227, 255)
            pg.draw.rect(scr, col, (bar.x + 2, bar.y + 2, fillw, bar.h - 4), border_radius=5)
        pg.draw.rect(scr, (234, 248, 255), bar, 2, border_radius=7)
        lst = self.cur_list()
        cnt = sum(1 for s in lst if s["id"] in self.found)
        self.button(f"{T('log')}  {cnt}/{len(lst)}", (18, 38, 210, 34), self.open_log)

    def save(self):
        try:
            with open(SAVE, "w", encoding="utf-8") as f:
                json.dump(dict(found=sorted(self.found), lang=LANG, skin=self.skin), f)
        except Exception:
            pass

    def set_lang(self, code):
        global LANG
        LANG = code
        self.toasts, self.toast = [], None
        pg.display.set_caption(role(self.skin, 1))
        self.save()

    def set_skin(self, skin):
        self.skin = skin
        pg.display.set_caption(role(self.skin, 1))
        self.save()

    def draw_lang(self):
        scr = self.screen
        r = self.panel(600, 440)
        cx = r.centerx
        text(scr, role(self.skin, 1), 48, GOLD, (cx, r.y + 26), "midtop", bold=True)
        text(scr, T("choose_lang"), 20, FOAM, (cx, r.y + 96), "midtop")
        bw, bh, gap = 240, 60, 14
        for i, (code, label) in enumerate(LANG_NAMES):
            col, row = i % 2, i // 2
            x = cx + gap / 2 if col == 0 else cx - gap / 2 - bw
            y = r.y + 140 + row * (bh + gap)
            self.button(label, (x, y, bw, bh), lambda c=code: self.set_lang(c), primary=(code == LANG), lang=code, size=24,
                        color=hx("#8fd3ff"))
        self.button(T("play"), (cx - 150, r.bottom - 100, 300, 70), self.go_skin, size=32)

    def go_skin(self):
        self.mode = "skin"

    def draw_skin(self):
        scr = self.screen
        r = self.panel(760, 450)
        cx = r.centerx
        text(scr, T("choose_hero"), 36, GOLD, (cx, r.y + 24), "midtop", bold=True)
        cw, ch, gap = 162, 230, 14
        total = 4 * cw + 3 * gap
        for i, skin in enumerate(SKINS):
            k = (3 - i) if rtl() else i
            x = cx - total / 2 + k * (cw + gap)
            y = r.y + 86
            rect = pg.Rect(x, y, cw, ch)
            sel = skin == self.skin
            hover = rect.collidepoint(pg.mouse.get_pos())
            s = pg.Surface(rect.size, pg.SRCALPHA)
            pg.draw.rect(s, (255, 201, 74, 60) if sel else (234, 248, 255, 34 if hover else 18), s.get_rect(), border_radius=18)
            pg.draw.rect(s, GOLD + (255,) if sel else (234, 248, 255, 70), s.get_rect(), 3 if sel else 1, border_radius=18)
            scr.blit(s, rect)
            img = sprite("diver", int(self.time * 6) + i * 2, (0, i), False)
            img = pg.transform.smoothscale(img, (int(img.get_width() * 1.45), int(img.get_height() * 1.45)))
            self.blit_center(img, rect.centerx - 4, rect.y + 86 + math.sin(self.time * 2 + i) * 5)
            text(scr, SKIN_NAMES[LANG][i], 24, GOLD if sel else FOAM, (rect.centerx, rect.bottom - 50), "midtop", bold=True)
            self.buttons.append((rect, lambda s=skin: self.set_skin(s)))
        self.button(T("next"), (cx - 130, r.bottom - 84, 260, 58), self.to_menu, size=26)

    def draw_start(self):
        r = self.panel(680, 410)
        cx = r.centerx
        text(self.screen, role(self.skin, 1), 48, GOLD, (cx, r.y + 22), "midtop", bold=True)
        text(self.screen, T("subtitle"), 21, FOAM, (cx, r.y + 84), "midtop")
        y = self.para(T("intro"), 16, MIST, cx, r.y + 124, 610)
        self.para(T("controls"), 14, FOAM, cx, y + 6, 620)
        bw, gap = 204, 12
        cols = (None, hx("#8fd3ff"), hx("#c9a0ff"))
        for i in range(3):
            k = i if rtl() else 2 - i
            x = cx + bw * 1.5 + gap - k * (bw + gap)
            self.button(role(self.skin, i + 1), (x - bw, r.bottom - 96, bw, 70), lambda n=i + 1: self.start(n), sub=T("stage", n=i + 1), color=cols[i])
        self.button(T("change_hero"), (cx + 6, r.bottom + 14, 200, 42), self.go_skin, False)
        self.button(T("language"), (cx - 206, r.bottom + 14, 200, 42), lambda: setattr(self, "mode", "lang"), False)

    def draw_end(self):
        lst = self.cur_list()
        n, tot = sum(1 for s in lst if s["id"] in self.found), len(lst)
        win = self.mode == "win"
        if self.stage == 1:
            if not win:
                title, body = T("over_sea"), T("over_sea_b", d=round(self.max_d), n=n, t=tot)
                btns = [(T("dive_again"), lambda: self.start(1), True), (T("menu"), self.to_menu, False)]
            else:
                title, body = T("win_sea"), T("win_sea_b", n=n, t=tot, r=role(self.skin, 2))
                btns = [(T("to_stage", k=2, r=role(self.skin, 2)), lambda: self.start(2), True), (T("keep"), self.keep_exploring, False)]
        elif self.stage == 2:
            num, unit = fmt_alt(self.max_d)
            if not win:
                title, body = T("over_sky"), T("over_sky_b", a=f"{num} {unit}", n=n, t=tot)
                btns = [(T("fly_again"), lambda: self.start(2), True), (T("back_sea"), lambda: self.start(1), False)]
            else:
                title, body = T("win_sky"), T("win_sky_b", n=n, t=tot, r=role(self.skin, 3))
                btns = [(T("to_stage", k=3, r=role(self.skin, 3)), lambda: self.start(3), True), (T("fly_again"), lambda: self.start(2), False)]
        else:
            if not win:
                title, body = T("over_space"), T("over_space_b", k=f"{km_to_moon(self.max_d):,} {T('km')}", n=n, t=tot)
                btns = [(T("fly_again"), lambda: self.start(3), True), (T("menu"), self.to_menu, False)]
            else:
                title, body = T("win_space"), T("win_space_b", n=n, t=tot)
                btns = [(T("play_again"), lambda: self.start(3), True), (T("menu"), self.to_menu, False)]
        r = self.panel(540, 300)
        text(self.screen, title, 34, FOAM, (r.centerx, r.y + 28), "midtop", bold=True)
        self.para(body, 17, MIST, r.centerx, r.y + 90, 470, 8)
        bw = 236
        total = bw * len(btns) + 12 * (len(btns) - 1)
        for i, (label, cb, prim) in enumerate(btns):
            k = i if rtl() else len(btns) - 1 - i
            x = r.centerx + total / 2 - k * (bw + 12) - bw
            self.button(label, (x, r.bottom - 74, bw, 46), cb, prim)

    def to_menu(self):
        self.mode = "start"

    def keep_exploring(self):
        self.o2 = 100
        self.cat["y"] -= 60
        self.cat["vy"] = -120
        self.mode = "play"

    def draw_log(self):
        scr = self.screen
        R = rtl()
        r = self.panel(880, 580)
        if R:
            text(scr, T("log"), 30, FOAM, (r.right - 28, r.y + 20), "topright", bold=True)
            self.button(T("close"), (r.x + 24, r.y + 20, 130, 38), self.close_log, False)
        else:
            text(scr, T("log"), 30, FOAM, (r.x + 28, r.y + 20), "topleft", bold=True)
            self.button(T("close"), (r.right - 154, r.y + 20, 130, 38), self.close_log, False)
        area = pg.Rect(r.x + 20, r.y + 74, r.w - 40, r.h - 94)
        lst = self.cur_list()
        cols, gap = 4, 12
        cw = (area.w - gap * (cols - 1)) // cols
        ch = 200
        rows = (len(lst) + cols - 1) // cols
        content_h = rows * (ch + gap)
        self.log_scroll = clamp(self.log_scroll, 0, max(0, content_h - area.h))
        surf = pg.Surface(area.size, pg.SRCALPHA)
        anchor, tx = ("topright", cw - 12) if R else ("topleft", 12)
        for i, s in enumerate(lst):
            col, row = i % cols, i // cols
            x = area.w - (col + 1) * cw - col * gap if R else col * (cw + gap)
            y = row * (ch + gap) - self.log_scroll
            if y > area.h or y + ch < 0:
                continue
            card = pg.Surface((cw, ch), pg.SRCALPHA)
            pg.draw.rect(card, (234, 248, 255, 16), card.get_rect(), border_radius=14)
            pg.draw.rect(card, (234, 248, 255, 40), card.get_rect(), 1, border_radius=14)
            got = s["id"] in self.found
            img = self.icon(s["id"], got, cw - 20, 72)
            card.blit(img, (cw / 2 - img.get_width() / 2, 10 + 36 - img.get_height() / 2))
            text(card, nm(s["id"]) if got else "???", 18, FOAM if got else (130, 150, 170), (tx, 88), anchor, bold=True, shadow=False)
            if self.stage == 3:
                rng = T("on_moon") if s["min"] >= 1000 else T("from_moon", v=f"{km_to_moon(s['min']):,} {T('km')}")
            elif self.stage == 2:
                a, u = fmt_alt(s["min"])
                rng = T("and_up", v=f"{a} {u}")
            else:
                rng = f"1000 {T('m_short')}" if s["id"] == "chest" else f"{s['min']}–{s['max']} {T('m_short')}"
            text(card, rng, 12, MIST, (tx, 112), anchor, shadow=False, alpha=180)
            yy = 132
            for ln in wrap(fact(s["id"]) if got else T("not_found"), 12, cw - 22)[:4]:
                text(card, ln, 12, MIST, (tx, yy), anchor, shadow=False)
                yy += 16
            surf.blit(card, (x, y))
        scr.blit(surf, area)
        if content_h > area.h:
            text(scr, T("scroll"), 12, MIST, (r.centerx, r.bottom - 18), "midbottom", shadow=False, alpha=160)

    def close_log(self):
        self.log_open = False

    def icon(self, sid, got, mw, mh):
        key = ("icon", sid, got, mw, mh, self.skin if sid == "flag" else "")
        if key in _SCACHE:
            return _SCACHE[key]
        if sid == "coral":
            base = pg.Surface((240, 100), pg.SRCALPHA)
            base.blit(coral_sprite("fan", COLS[2], 0, .8), (90, 5))
            base.blit(coral_sprite("branch", COLS[0], 0, 1), (55, 10))
            base.blit(coral_sprite("brain", COLS[6], 0, .8), (20, 16))
        elif sid == "aurora":
            base = pg.Surface((160, 90), pg.SRCALPHA)
            for i, c in enumerate(((120, 255, 170), (90, 220, 255), (255, 120, 220))):
                pts = [(x, 20 + i * 18 + math.sin(x * .05 + i) * 8) for x in range(0, 161, 8)]
                pg.draw.polygon(base, c + (170,), pts + [(x, y + 16) for x, y in pts[::-1]])
        elif sid == "cloud":
            base = self.clouds[0]
        elif sid in ("earth", "moon"):
            p = P(90, 90, 45, 45)
            if sid == "earth":
                p.circ(hx("#1d4f96"), 0, 0, 40)
                p.circ(hx("#3b88d6"), -2, -2, 37)
                for x, y, rx, ry, c in ((-14, -10, 14, 10, "#4f9a52"), (12, 8, 16, 11, "#5aa35a"), (8, -20, 9, 5, "#c9b071"), (-6, 18, 18, 4, "#ffffff")):
                    p.ell(hx(c), x, y, rx, ry)
            else:
                p.circ(hx("#6e717a"), 0, 0, 40)
                p.circ(hx("#a3a6ae"), -2, -2, 37)
                for x, y, r in ((-12, -10, 8), (14, 6, 10), (-8, 16, 6), (10, -20, 5)):
                    p.circ(hx("#7c7f88"), x, y, r)
            base = p.done()
        else:
            base = sprite(sid, 1, SKINS.index(self.skin) if sid == "flag" else 0)
        sc = min(mw / base.get_width(), mh / base.get_height(), 1.6)
        img = pg.transform.smoothscale(base, (max(1, int(base.get_width() * sc)), max(1, int(base.get_height() * sc))))
        if not got:
            m = pg.mask.from_surface(img, 30)
            img = m.to_surface(setcolor=(234, 248, 255, 45), unsetcolor=(0, 0, 0, 0))
        _SCACHE[key] = img
        return img

    def draw(self):
        self.buttons = []
        if self.stage == 3:
            self.render_space()
        elif self.stage == 2:
            self.render_sky()
        else:
            self.render_sea()
        if not self.in_menu():
            self.draw_hud()
            self.draw_toast()
        if self.mode == "lang":
            self.draw_lang()
        elif self.mode == "skin":
            self.draw_skin()
        elif self.mode == "start":
            self.draw_start()
        elif self.mode in ("over", "win"):
            self.draw_end()
        if self.log_open:
            self.draw_log()

    # ---- events
    def handle(self, e):
        if e.type == pg.KEYDOWN:
            self.keys.add(e.key)
            if e.key == pg.K_l and self.mode == "play":
                self.log_open = not self.log_open
            elif e.key == pg.K_ESCAPE:
                if self.log_open:
                    self.log_open = False
                elif not self.in_menu():
                    self.mode = "start"
                elif self.mode == "start":
                    self.mode = "skin"
                elif self.mode == "skin":
                    self.mode = "lang"
                else:
                    return False
            elif e.key in (pg.K_RETURN, pg.K_SPACE) and self.in_menu():
                if self.mode == "lang":
                    self.mode = "skin"
                elif self.mode == "skin":
                    self.mode = "start"
                else:
                    self.start(1)
        elif e.type == pg.KEYUP:
            self.keys.discard(e.key)
        elif e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
            for r, cb in self.buttons:
                if r.collidepoint(e.pos):
                    cb()
                    return True
            if self.mode == "play" and not self.log_open:
                self.pointer = e.pos
        elif e.type == pg.MOUSEMOTION and self.pointer:
            self.pointer = e.pos
        elif e.type == pg.MOUSEBUTTONUP and e.button == 1:
            self.pointer = None
        elif e.type == pg.MOUSEWHEEL and self.log_open:
            self.log_scroll -= e.y * 60
        return True


def main():
    pg.init()
    pg.display.set_caption("Diving Cat")
    screen = pg.display.set_mode((W, H), pg.SCALED | pg.RESIZABLE)
    clock = pg.time.Clock()
    game = Game(screen)
    running = True
    while running:
        dt = min(.05, clock.tick(60) / 1000)
        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
            elif not game.handle(e):
                running = False
        game.update(dt)
        game.draw()
        pg.display.flip()
    pg.quit()


if __name__ == "__main__":
    main()