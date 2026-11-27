#!/usr/bin/env python3
"""
ציידי המפלצות 2  -  Monster Hunters
====================================
משחק חיפוש מפלצות מפחיד ב-Python:
  שחק -> בוחרים מפלצת -> קוראים את הסיפור שלה -> המשך ->
  יורדים לסביבת המחייה שלה, מחפשים אותה ומצלמים אותה... לפני שהיא תופסת אתכם!

מפלצות: נינגן, אוגופוגו, בלופ, נסי (לוך נס), קראקן, ביגפוט (ביום, ביער).
בכל מקום יש גם מסיחי דעת: לוויתנים, כרישים, בולי עץ, לוטרות, דובים,
ואפילו בן אדם בתחפושת - כולם מופיעים בסונאר וצריך לבדוק מי הוא מי.

כל הגרפיקה והצלילים נוצרים בקוד - אין צורך בקבצים חיצוניים.

התקנה:  pip install pygame numpy
הרצה:   python monster_hunters.py

שליטה במשחק:
  W A S D / חצים   - תנועה             Shift  - טורבו (עושה רעש!)
  עכבר             - כיוון הפנס / המצלמה
  קליק שמאלי / רווח - צילום
  E / קליק ימני     - סונאר (ביער: הקשבה)
  Esc              - חזרה לבחירת מפלצת
"""
import json
import math
import os
import random
import re
import sys

import numpy as np
import pygame

W, H = 1280, 720
FPS = 60
TAU = math.pi * 2
F32 = np.float32
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monster_hunters_save.json")
SRCALPHA = pygame.SRCALPHA
KEY = (255, 0, 255)

# ======================================================================= עזרים


def clamp(v, a, b):
    return a if v < a else b if v > b else v


def mix(a, b, t):
    t = clamp(t, 0.0, 1.0)
    return tuple(int(clamp(a[i] + (b[i] - a[i]) * t, 0, 255)) for i in range(3))


def mul(c, k):
    return tuple(int(clamp(v * k, 0, 255)) for v in c[:3])


def fmul(c, k):
    return tuple(v * k for v in c)


# ---------------------------------------------------------------- עברית (ימין לשמאל)
_HEB = re.compile(r"[֐-׿]")
_LTR = re.compile(r"[A-Za-z0-9]+(?:[.,:'/\-][A-Za-z0-9]+)*%?")
_MIRROR = str.maketrans("()[]{}<>", ")(][}{><")


def vis(s):
    """הופך שורה בעברית לסדר תצוגה (pygame מצייר רק משמאל לימין)."""
    if not _HEB.search(s):
        return s
    runs, pos = [], 0
    for m in _LTR.finditer(s):
        if m.start() > pos:
            runs.append((False, s[pos:m.start()]))
        runs.append((True, m.group()))
        pos = m.end()
    if pos < len(s):
        runs.append((False, s[pos:]))
    return "".join(txt if ltr else txt[::-1].translate(_MIRROR) for ltr, txt in reversed(runs))


_FONTS = {}
FONT_LIST = "arial,arialhebrew,segoeui,tahoma,dejavusans,freesans,liberationsans,notosanshebrew"


def F(size, bold=True):
    key = (size, bold)
    if key not in _FONTS:
        try:
            _FONTS[key] = pygame.font.SysFont(FONT_LIST, size, bold=bold)
        except Exception:
            _FONTS[key] = pygame.font.Font(None, size)
    return _FONTS[key]


def text(surf, s, size, col, x, y, align="center", bold=True, shadow=2, alpha=255, glow=None):
    f = F(size, bold)
    v = vis(s)
    img = f.render(v, True, col)
    w = img.get_width()
    x0 = x - w // 2 if align == "center" else (x - w if align == "right" else x)
    if glow:
        g = f.render(v, True, glow)
        g.set_alpha(int(55 * alpha / 255))
        for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            surf.blit(g, (x0 + ox, y + oy))
    if shadow:
        sh = f.render(v, True, (0, 0, 0))
        sh.set_alpha(int(alpha * 0.7))
        surf.blit(sh, (x0 + shadow, y + shadow))
    if alpha < 255:
        img.set_alpha(int(alpha))
    surf.blit(img, (x0, y))
    return pygame.Rect(x0, y, w, img.get_height())


def fit_size(s, width, size, bold=True):
    while size > 12 and F(size, bold).size(vis(s))[0] > width:
        size -= 2
    return size


def wrap(s, size, width, bold=False):
    f = F(size, bold)
    lines, cur = [], ""
    for word in s.split():
        cand = (cur + " " + word).strip()
        if not cur or f.size(vis(cand))[0] <= width:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_star(surf, cx, cy, r, col, outline=None):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    pygame.draw.polygon(surf, col, pts)
    if outline:
        pygame.draw.polygon(surf, outline, pts, 2)


def draw_check(surf, cx, cy, r, col):
    pygame.draw.circle(surf, (20, 120, 50), (cx, cy), r)
    pygame.draw.circle(surf, (120, 255, 150), (cx, cy), r, 2)
    pygame.draw.lines(surf, col, False, [(cx - r * 0.5, cy), (cx - r * 0.12, cy + r * 0.42),
                                         (cx + r * 0.55, cy - r * 0.4)], max(2, int(r * 0.28)))


def draw_heart(surf, cx, cy, r, col):
    pygame.draw.circle(surf, col, (cx - r * 0.5, cy - r * 0.2), r * 0.55)
    pygame.draw.circle(surf, col, (cx + r * 0.5, cy - r * 0.2), r * 0.55)
    pygame.draw.polygon(surf, col, [(cx - r * 1.02, cy - r * 0.05), (cx + r * 1.02, cy - r * 0.05), (cx, cy + r)])


def bezier(p0, p1, p2, n):
    out = []
    for i in range(n):
        t = i / (n - 1)
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


# ---------------------------------------------------------------- רעש פרוצדורלי


def vnoise(w, h, cx, cy, rng):
    g = rng.random((cx + 2, cy + 2)).astype(F32)
    xs = np.arange(w, dtype=F32) * cx / w
    ys = np.arange(h, dtype=F32) * cy / h
    x0, y0 = xs.astype(int), ys.astype(int)
    fx, fy = xs - x0, ys - y0
    fx = (fx * fx * (3 - 2 * fx))[:, None]
    fy = (fy * fy * (3 - 2 * fy))[None, :]
    a, b = g[x0][:, y0], g[x0 + 1][:, y0]
    c, d = g[x0][:, y0 + 1], g[x0 + 1][:, y0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(w, h, cx, cy, rng, octaves=5):
    out = np.zeros((w, h), F32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        out += vnoise(w, h, cx * 2 ** o, cy * 2 ** o, rng) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def line_noise(n, cells, rng, octaves=3):
    return fbm(n, 1, cells, 1, rng, octaves)[:, 0]


def tile_noise(n, cells, rng, octaves):
    """רעש שמתחבר בקצוות (לטקסטורת עור)."""
    out = np.zeros((n, n), F32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = cells * 2 ** o
        g = rng.random((c, c)).astype(F32)
        xs = np.arange(n, dtype=F32) * c / n
        i0 = xs.astype(int)
        f = xs - i0
        f = f * f * (3 - 2 * f)
        i1 = (i0 + 1) % c
        a, b = g[i0][:, i0], g[i0][:, i1]
        cc, d = g[i1][:, i0], g[i1][:, i1]
        fy, fx = f[None, :], f[:, None]
        out += ((a * (1 - fy) + b * fy) * (1 - fx) + (cc * (1 - fy) + d * fy) * fx) * amp
        tot += amp
        amp *= 0.5
    return out / tot


_NOISE = []


def noise_tex():
    if not _NOISE:
        rng = np.random.default_rng(11)
        _NOISE.append(tile_noise(256, 6, rng, 5))
        _NOISE.append(tile_noise(256, 48, rng, 2))
    return _NOISE


# ======================================================================= קנבס תלת-ממדי
# כל המפלצות מצוירות מצורות מוצללות (כדורים, צינורות) עם תאורה, ברק, טקסטורת עור,
# ואור קצה כחלחל - ומשהו "זוהר" (עיניים, נקודות אור) שנראה גם בחושך.

_L = np.array([-0.35, -0.8, 0.5], F32)
LX, LY, LZ = (_L / np.linalg.norm(_L)).tolist()


class Canvas:
    def __init__(self, bw, bh, s, rim=(0.18, 0.32, 0.5), amb=0.2):
        self.s = s
        self.w, self.h = max(2, int(bw * s)), max(2, int(bh * s))
        self.rgb = np.zeros((self.w, self.h, 3), F32)
        self.a = np.zeros((self.w, self.h), F32)
        self.e = np.zeros((self.w, self.h, 3), F32)
        self.rim = np.array(rim, F32)
        self.amb = amb

    def _grid(self, x0, x1, y0, y1):
        return (np.arange(x0, x1, dtype=F32) + 0.5)[:, None], (np.arange(y0, y1, dtype=F32) + 0.5)[None, :]

    def _box(self, xa, xb, ya, yb):
        return (max(0, int(xa) - 1), min(self.w, int(xb) + 2), max(0, int(ya) - 1), min(self.h, int(yb) + 2))

    def _tex(self, X, Y, tex, fine):
        if tex <= 0:
            return 1.0
        n1, n2 = noise_tex()
        u = (X / self.s).astype(np.int32) % 256
        v = (Y / self.s).astype(np.int32) % 256
        n = n1[u, v] * (1 - fine) + n2[u, v] * fine
        return 1 + tex * (2 * n - 1) * 1.5

    def _shade(self, nx, ny, nz, col, spec, shine, tm, rim):
        ndl = nx * LX + ny * LY + nz * LZ
        diff = np.clip(ndl, 0, 1)
        occ = 0.82 - 0.22 * np.clip(ny, -1, 1)
        base = (self.amb + 0.9 * diff) * occ * tm
        c = np.asarray(col, F32) * base[..., None]
        if spec:
            c = c + (spec * diff ** shine)[..., None]
        if rim:
            c = c + ((1 - np.clip(nz, 0, 1)) ** 3 * rim)[..., None] * self.rim
        return c

    def _paint(self, x0, x1, y0, y1, c, aa, em):
        sl = (slice(x0, x1), slice(y0, y1))
        a3 = aa[..., None]
        self.rgb[sl] = self.rgb[sl] * (1 - a3) + c * a3
        self.e[sl] = self.e[sl] * (1 - a3) + em * a3
        self.a[sl] = np.maximum(self.a[sl], aa)

    def ellipsoid(self, cx, cy, rx, ry, col, ang=0.0, spec=0.25, shine=18, tex=0.15, fine=0.3, em=0.0,
                  rim=1.0, alpha=1.0):
        s = self.s
        cx, cy, rx, ry = cx * s, cy * s, max(0.5, rx * s), max(0.5, ry * s)
        R = max(rx, ry)
        x0, x1, y0, y1 = self._box(cx - R, cx + R, cy - R, cy + R)
        if x0 >= x1 or y0 >= y1:
            return
        X, Y = self._grid(x0, x1, y0, y1)
        dx, dy = X - cx, Y - cy
        if ang:
            ca, sa = math.cos(ang), math.sin(ang)
            u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        else:
            u, v = dx + 0 * dy, dy + 0 * dx
        nu, nv = u / rx, v / ry
        r2 = nu * nu + nv * nv
        aa = np.clip((1 - np.sqrt(r2)) * min(rx, ry), 0, 1) * alpha
        if not (aa > 0).any():
            return
        nz = np.sqrt(np.clip(1 - r2, 0, 1))
        if ang:
            nx, ny = nu * ca - nv * sa, nu * sa + nv * ca
        else:
            nx, ny = nu, nv
        c = self._shade(nx, ny, nz, col, spec, shine, self._tex(X, Y, tex, fine), rim)
        self._paint(x0, x1, y0, y1, c, aa, np.asarray(col, F32) * em)

    def capsule(self, x0, y0, x1, y1, r0, r1, col, spec=0.25, shine=18, tex=0.15, fine=0.3, em=0.0, rim=1.0):
        s = self.s
        x0, y0, x1, y1, r0, r1 = x0 * s, y0 * s, x1 * s, y1 * s, max(0.4, r0 * s), max(0.4, r1 * s)
        rm = max(r0, r1)
        bx0, bx1, by0, by1 = self._box(min(x0, x1) - rm, max(x0, x1) + rm, min(y0, y1) - rm, max(y0, y1) + rm)
        if bx0 >= bx1 or by0 >= by1:
            return
        X, Y = self._grid(bx0, bx1, by0, by1)
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1e-6
        t = np.clip(((X - x0) * dx + (Y - y0) * dy) / L2, 0, 1)
        vx, vy = X - (x0 + dx * t), Y - (y0 + dy * t)
        r = r0 + (r1 - r0) * t
        nx, ny = vx / r, vy / r
        n2 = nx * nx + ny * ny
        aa = np.clip((1 - np.sqrt(n2)) * np.maximum(r, 0.6), 0, 1)
        if not (aa > 0).any():
            return
        nz = np.sqrt(np.clip(1 - n2, 0, 1))
        c = self._shade(nx, ny, nz, col, spec, shine, self._tex(X, Y, tex, fine), rim)
        self._paint(bx0, bx1, by0, by1, c, aa, np.asarray(col, F32) * em)

    def chain(self, pts, rads, col, spec=0.25, shine=18, tex=0.15, fine=0.3, em=0.0, rim=1.0):
        """צינור רציף וחלק דרך כמה נקודות (גוף נחש, זנב, זרוע)."""
        s = self.s
        P = [(x * s, y * s) for x, y in pts]
        R = [max(0.4, r * s) for r in rads]
        rm = max(R)
        xs, ys = [p[0] for p in P], [p[1] for p in P]
        x0, x1, y0, y1 = self._box(min(xs) - rm, max(xs) + rm, min(ys) - rm, max(ys) + rm)
        if x0 >= x1 or y0 >= y1:
            return
        X, Y = self._grid(x0, x1, y0, y1)
        shape = (x1 - x0, y1 - y0)
        best = np.full(shape, 9.0, F32)
        bnx = np.zeros(shape, F32)
        bny = np.zeros(shape, F32)
        br = np.ones(shape, F32)
        for j in range(len(P) - 1):
            (ax, ay), (bx, by) = P[j], P[j + 1]
            r0, r1 = R[j], R[j + 1]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy or 1e-6
            t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
            vx, vy = X - (ax + dx * t), Y - (ay + dy * t)
            r = r0 + (r1 - r0) * t
            nx, ny = vx / r, vy / r
            n2 = nx * nx + ny * ny
            m = n2 < best
            best = np.where(m, n2, best)
            bnx = np.where(m, nx, bnx)
            bny = np.where(m, ny, bny)
            br = np.where(m, r, br)
        aa = np.clip((1 - np.sqrt(best)) * np.maximum(br, 0.6), 0, 1)
        if not (aa > 0).any():
            return
        nz = np.sqrt(np.clip(1 - best, 0, 1))
        c = self._shade(bnx, bny, nz, col, spec, shine, self._tex(X, Y, tex, fine), rim)
        self._paint(x0, x1, y0, y1, c, aa, np.asarray(col, F32) * em)

    def cone(self, x0, y0, x1, y1, r, col=(0.93, 0.89, 0.78)):
        self.capsule(x0, y0, x1, y1, r, r * 0.12, col, spec=0.7, shine=30, tex=0.05, rim=0.3)

    def poly(self, points, col, center=None, fall=1.0, tex=0.1, em=0.0):
        s = self.s
        pts = [(x * s, y * s) for x, y in points]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, x1, y0, y1 = self._box(min(xs), max(xs), min(ys), max(ys))
        if x0 >= x1 or y0 >= y1:
            return
        surf = pygame.Surface((x1 - x0, y1 - y0))
        pygame.draw.polygon(surf, (255, 255, 255), [(x - x0, y - y0) for x, y in pts])
        m = pygame.surfarray.array_red(surf).astype(F32) / 255
        X, Y = self._grid(x0, x1, y0, y1)
        k = self._tex(X, Y, tex, 0.4) * (1.0 + 0 * X * Y)
        if center:
            d = np.hypot(X - center[0] * s, Y - center[1] * s) / (fall * s)
            k = k * np.clip(d, 0.03, 1) ** 1.4
        else:
            k = k * (1.05 - 0.35 * (Y - y0) / max(1, y1 - y0))
        c = np.asarray(col, F32) * k[..., None]
        self._paint(x0, x1, y0, y1, c, m, np.asarray(col, F32) * em)

    def glow(self, cx, cy, r, col):
        s = self.s
        cx, cy, r = cx * s, cy * s, max(1.0, r * s)
        x0, x1, y0, y1 = self._box(cx - r, cx + r, cy - r, cy + r)
        if x0 >= x1 or y0 >= y1:
            return
        X, Y = self._grid(x0, x1, y0, y1)
        g = np.clip(1 - np.hypot(X - cx, Y - cy) / r, 0, 1) ** 2
        self.e[x0:x1, y0:y1] += g[..., None] * np.asarray(col, F32)

    def eye(self, cx, cy, r, col, pupil="slit", glow=3.0, iem=1.5):
        self.ellipsoid(cx, cy, r * 1.35, r * 1.18, (0.03, 0.025, 0.025), spec=0.1, tex=0, rim=0)
        self.ellipsoid(cx, cy, r, r * 0.92, col, spec=0.9, shine=50, tex=0.35, fine=1.0, em=iem, rim=0)
        blk = (0.0, 0.0, 0.0)
        if pupil == "slit":
            self.ellipsoid(cx + r * 0.1, cy, r * 0.17, r * 0.78, blk, spec=0.3, tex=0, rim=0)
        elif pupil == "h":
            self.ellipsoid(cx + r * 0.1, cy, r * 0.65, r * 0.2, blk, spec=0.3, tex=0, rim=0)
        elif pupil == "round":
            self.ellipsoid(cx + r * 0.15, cy, r * 0.42, r * 0.42, blk, spec=0.3, tex=0, rim=0)
        self.ellipsoid(cx - r * 0.33, cy - r * 0.35, r * 0.2, r * 0.16, (1, 1, 1), spec=0, tex=0, em=1.0, rim=0)
        if glow:
            self.glow(cx, cy, r * glow, fmul(col, 0.55))

    def surfaces(self):
        col = 1 - np.exp(-(self.rgb + self.e) * 1.3)
        body = pygame.Surface((self.w, self.h), SRCALPHA)
        px = pygame.surfarray.pixels3d(body)
        px[:] = (np.clip(col, 0, 1) * 255).astype(np.uint8)
        del px
        pa = pygame.surfarray.pixels_alpha(body)
        pa[:] = (np.clip(self.a, 0, 1) * 255).astype(np.uint8)
        del pa
        glow = None
        if self.e.max() > 0.03:
            g = 1 - np.exp(-self.e * 1.4)
            glow = pygame.surfarray.make_surface((np.clip(g, 0, 1) * 255).astype(np.uint8))
        return body, glow


def render_canvas_frames(painter, bw, bh, k, n, rs=0.8, rim=(0.18, 0.32, 0.5)):
    """מחזיר (גופים, זוהרים) לכל פריים אנימציה."""
    bodies, glows = [], []
    size = (max(2, int(bw * k)), max(2, int(bh * k)))
    for i in range(n):
        c = Canvas(bw, bh, k * rs, rim)
        painter(c, i / n * TAU)
        b, g = c.surfaces()
        if rs != 1:
            b = pygame.transform.smoothscale(b, size)
            if g is not None:
                g = pygame.transform.smoothscale(g, size)
        bodies.append(b)
        glows.append(g)
    return bodies, glows


_GLOW = {}


def glow_sprite(r, col):
    r = max(2, int(r))
    key = (r, col)
    if key not in _GLOW:
        n = 2 * r
        X, Y = np.meshgrid(np.arange(n) + 0.5, np.arange(n) + 0.5, indexing="ij")
        g = np.clip(1 - np.hypot(X - r, Y - r) / r, 0, 1) ** 2
        arr = np.clip(g[..., None] * np.array(col, F32), 0, 255).astype(np.uint8)
        _GLOW[key] = pygame.surfarray.make_surface(arr)
        if len(_GLOW) > 300:
            _GLOW.pop(next(iter(_GLOW)))
    return _GLOW[key]


def add_glow(surf, x, y, r, col):
    g = glow_sprite(r, col)
    surf.blit(g, (x - g.get_width() // 2, y - g.get_height() // 2), special_flags=pygame.BLEND_ADD)

# ======================================================================= המפלצות (ציור)


def paint_ningen(c, t):
    pale, far = (0.86, 0.9, 0.95), (0.58, 0.64, 0.74)
    SK = dict(spec=0.5, shine=32, tex=0.07, fine=0.5, rim=1.4, em=0.05)
    sw = math.sin(t)

    def arm(col, sx, sy, ph):
        ex, ey = sx + 28 + math.sin(ph) * 14, sy + 62
        hx, hy = ex + 22 + math.sin(ph + 0.7) * 18, ey + 50
        c.capsule(sx, sy, ex, ey, 22, 15, col, **SK)
        c.ellipsoid(ex, ey, 15, 15, col, **SK)
        c.capsule(ex, ey, hx, hy, 15, 11, col, **SK)
        c.ellipsoid(hx, hy + 4, 17, 12, col, **SK)
        for j in range(5):
            a = math.radians(45 + j * 22) + math.sin(ph) * 0.12
            mx, my = hx + math.cos(a) * 20, hy + 6 + math.sin(a) * 17
            c.capsule(hx, hy + 6, mx, my, 4.4, 3.4, col, **SK)
            a2 = a + 0.4
            c.capsule(mx, my, mx + math.cos(a2) * 19, my + math.sin(a2) * 17, 3.4, 1.4, col, **SK)

    arm(far, 350, 185, t + 1.6)
    pts = [(70 + k * 280, 150 + math.sin(t - k * 2.2) * 16 * (1 - k)) for k in np.linspace(0, 1, 12)]
    rads = [10 + k * 58 for k in np.linspace(0, 1, 12)]
    tx, ty = pts[0]
    c.ellipsoid(tx - 30, ty - 30 + sw * 10, 42, 11, pale, ang=-0.75, **SK)
    c.ellipsoid(tx - 30, ty + 30 + sw * 10, 42, 11, pale, ang=0.75, **SK)
    c.chain(pts, rads, pale, **SK)
    c.ellipsoid(370, 150, 92, 74, pale, **SK)
    c.ellipsoid(478, 128, 72, 66, pale, **SK)
    for ex, ey, rx, ry in ((513, 112, 15, 11), (542, 117, 10, 9)):
        c.ellipsoid(ex, ey, rx, ry, (0.02, 0.03, 0.05), spec=0.15, tex=0, rim=0)
        c.ellipsoid(ex + 1, ey + 1, rx * 0.28, ry * 0.3, (0.55, 0.85, 1.0), em=2.5, spec=0, tex=0, rim=0)
        c.glow(ex + 1, ey + 1, rx * 1.6, (0.2, 0.45, 0.8))
    c.chain([(492, 152), (510, 150), (530, 150), (550, 153)], [2.4, 3.6, 3.6, 2.2], (0.01, 0.01, 0.02), spec=0, tex=0, rim=0)
    for ex, ey in ((513, 124), (542, 127)):
        c.ellipsoid(ex, ey, 10, 3, (0.55, 0.6, 0.7), tex=0.05, spec=0.1, rim=0)
    arm(pale, 395, 190, t)


def ogo_points(t):
    pts, rads = [], []
    for k in np.linspace(0, 1, 30):
        y = 175 + math.sin(k * 10 - t) * 38 * (0.35 + 0.65 * math.sin(math.pi * min(1, k * 1.15)))
        if k > 0.82:
            y -= ((k - 0.82) / 0.18) ** 1.5 * 70
        r = 5 + 24 * min(1, k * 1.8)
        pts.append((70 + k * 700, y))
        rads.append(r * (0.85 if k > 0.9 else 1))
    return pts, rads


def paint_ogopogo(c, t):
    body, belly, dark = (0.32, 0.4, 0.26), (0.66, 0.6, 0.4), (0.15, 0.18, 0.12)
    SK = dict(spec=0.45, shine=26, tex=0.32, fine=0.65, rim=1.0)
    pts, rads = ogo_points(t)

    def flipper(col, i):
        x, y = pts[i]
        ph = math.sin(t * 2 + i)
        c.capsule(x, y + 8, x - 16, y + 34, 8, 6, col, **SK)
        c.ellipsoid(x - 30 + ph * 8, y + 44, 24, 8, col, ang=0.45 + ph * 0.3, **SK)

    flipper(fmul(body, 0.65), 21)
    flipper(fmul(body, 0.65), 10)
    tx, ty = pts[0]
    c.ellipsoid(tx - 26, ty - 16, 30, 7, body, ang=-0.6, **SK)
    c.ellipsoid(tx - 26, ty + 16, 30, 7, body, ang=0.6, **SK)
    for i in range(3, 26, 2):
        x, y = pts[i]
        c.cone(x, y - rads[i] * 0.6, x - 10, y - rads[i] - 17, 4.5, (0.55, 0.5, 0.38))
    c.chain(pts, rads, body, **SK)
    c.chain([(x, y + r * 0.5) for (x, y), r in zip(pts, rads)], [r * 0.45 for r in rads], belly, spec=0.3, tex=0.25, rim=0.3)
    rr = random.Random(5)
    for i in range(3, 26):
        x, y = pts[i]
        c.ellipsoid(x + rr.uniform(-6, 6), y - rads[i] * 0.35, rads[i] * 0.33, rads[i] * 0.2, dark, tex=0.2, spec=0.2)
    for i in range(22, 30):
        x, y = pts[i]
        for m in range(2):
            c.capsule(x - 4 + m * 6, y - rads[i] * 0.7, x - 26 + m * 4, y - rads[i] - 22 - m * 5, 3.5, 1, (0.12, 0.1, 0.08), tex=0.3, spec=0.2)
    hx, hy = pts[-1]
    ja = 0.5 + 0.5 * math.sin(t * 1.3)
    c.ellipsoid(hx + 72, hy + 7, 36, 10 + 9 * ja, (0.3, 0.04, 0.05), ang=0.15, tex=0, spec=0.1, rim=0)
    c.ellipsoid(hx + 34, hy - 8, 44, 25, body, ang=-0.1, **SK)
    for k in range(8):
        x = hx + 50 + k * 7.5
        c.cone(x, hy + 7, x + 1, hy + 16 + (k % 2) * 3, 2.3)
        c.cone(x - 2, hy + 18 + 12 * ja, x - 1, hy + 10 + 12 * ja, 2.0)
    c.ellipsoid(hx + 76, hy - 1, 36, 13, body, ang=-0.05, **SK)
    c.ellipsoid(hx + 70, hy + 20 + 12 * ja, 32, 8, body, ang=0.18 + ja * 0.25, **SK)
    c.ellipsoid(hx + 44, hy - 22, 13, 4, dark, ang=-0.25)
    c.eye(hx + 46, hy - 13, 6.5, (1.0, 0.78, 0.12), "slit")
    c.ellipsoid(hx + 104, hy - 6, 3, 2, (0.03, 0.03, 0.02), tex=0, rim=0)
    flipper(body, 22)
    flipper(body, 11)


def paint_bloop(c, t):
    body, belly = (0.2, 0.25, 0.34), (0.55, 0.6, 0.68)
    SK = dict(spec=0.5, shine=24, tex=0.25, fine=0.5, rim=1.0)
    op = 0.72 + 0.28 * math.sin(t)
    sw = math.sin(t)
    pts = [(80 + k * 420, 360 + math.sin(t - k * 2) * 30 * (1 - k)) for k in np.linspace(0, 1, 10)]
    rads = [18 + k * 170 for k in np.linspace(0, 1, 10)]
    tx, ty = pts[0]
    c.ellipsoid(tx - 40, ty - 70 + sw * 20, 75, 20, body, ang=-0.95, **SK)
    c.ellipsoid(tx - 40, ty + 70 + sw * 20, 75, 20, body, ang=0.95, **SK)
    c.ellipsoid(700, 560 + sw * 10, 110, 26, fmul(body, 0.65), ang=0.8, **SK)
    c.chain(pts, rads, body, **SK)
    c.ellipsoid(700, 350, 430, 245, body, **SK)
    c.ellipsoid(960, 330, 300, 250, body, **SK)
    for j in range(7):
        line = []
        for x in range(380, 1001, 40):
            ry = 245 * math.sqrt(max(0.0, 1 - ((x - 700) / 430) ** 2))
            line.append((x, 350 + ry * (0.34 + j * 0.09)))
        c.chain(line, [3.5] * len(line), belly, spec=0.2, tex=0.2, rim=0.2)
    rr = random.Random(2)
    for _ in range(9):
        x, y = rr.uniform(450, 1000), rr.uniform(170, 330)
        c.capsule(x, y, x + rr.uniform(30, 90), y + rr.uniform(-20, 20), 2.5, 1.5, (0.62, 0.66, 0.72), tex=0.1, spec=0.1, rim=0)
    for i in range(18):
        x = 380 + i * 36
        y = 350 - 245 * math.sqrt(max(0.0, 1 - ((x - 700) / 430) ** 2)) * 0.12 + 40
        c.ellipsoid(x, y, 5, 5, (0.35, 0.95, 1.0), em=2.6, spec=0, tex=0, rim=0)
        c.glow(x, y, 20, (0.05, 0.4, 0.55))
    hx, hy = 880, 370
    ut, lt = (1335, 370 - 215 * op), (1300, 370 + 200 * op)
    front = bezier(ut, (1375, 370), lt, 14)
    c.poly([(hx, hy)] + front, (0.62, 0.08, 0.11), center=(hx + 40, hy), fall=430)
    c.ellipsoid(1080, 380 + 90 * op, 160, 36, (0.5, 0.12, 0.15), ang=-0.12, tex=0.3, spec=0.4, rim=0)
    rr = random.Random(9)
    for (ax, ay), (bx, by), sign, jr in (((900, 300), ut, 1, (48, 13)), ((900, 445), lt, -1, (56, 15))):
        L = math.hypot(bx - ax, by - ay)
        dxu, dyu = (bx - ax) / L, (by - ay) / L
        nx, ny = -dyu, dxu
        if ny * sign < 0:
            nx, ny = -nx, -ny
        for row, (n0, ln0, rad0) in enumerate(((17, 40, 9), (11, 22, 6))):
            for i in range(n0):
                u = 0.14 + i * (0.8 / n0) + row * 0.03
                jrad = jr[0] + (jr[1] - jr[0]) * u
                px, py = ax + (bx - ax) * u, ay + (by - ay) * u
                off = jrad * 0.55 + row * 16
                base = (px + nx * off, py + ny * off)
                ln = ln0 * (1 - u * 0.35) * rr.uniform(0.7, 1.2)
                c.cone(base[0], base[1], base[0] + nx * ln + dxu * 6, base[1] + ny * ln + dyu * 6, rad0 * (1 - u * 0.3))
    c.capsule(900, 300, ut[0], ut[1], 48, 13, body, **SK)
    c.capsule(900, 445, lt[0], lt[1], 56, 15, fmul(body, 1.08), **SK)
    c.ellipsoid(790, 590 + sw * 12, 120, 28, body, ang=0.75, **SK)
    c.eye(985, 205, 13, (1.0, 0.72, 0.28), "round", glow=4)


def paint_nessie(c, t):
    body, belly, dk = (0.3, 0.36, 0.24), (0.6, 0.58, 0.42), (0.16, 0.18, 0.12)
    SK = dict(spec=0.5, shine=28, tex=0.3, fine=0.6, rim=1.0)

    def flipper(col, x, y, ph):
        c.ellipsoid(x - 10 + 20 * math.sin(ph), y + 36, 54, 15, col, ang=0.85 + 0.4 * math.sin(ph), **SK)

    flipper(fmul(body, 0.65), 400, 300, t + math.pi)
    flipper(fmul(body, 0.65), 230, 300, t)
    tail = [(170 - k * 150, 280 + k * 45 + math.sin(t - k * 3) * 12 * k) for k in np.linspace(0, 1, 10)]
    c.chain(tail, [55 - 50 * k for k in np.linspace(0, 1, 10)], body, **SK)
    c.ellipsoid(310, 270, 175, 82, body, **SK)
    c.ellipsoid(320, 318, 140, 28, belly, spec=0.3, tex=0.2, rim=0.2)
    rr = random.Random(4)
    for _ in range(16):
        c.ellipsoid(rr.uniform(180, 440), rr.uniform(205, 260), rr.uniform(6, 13), rr.uniform(4, 8), dk, tex=0.2)
    for i in range(9):
        x = 200 + i * 26
        c.ellipsoid(x, 196 + abs(i - 4) * 2.5, 9, 7, body, **SK)
    p2 = (540 + math.sin(t) * 12, 70 + math.cos(t) * 5)
    neck = bezier((430, 245), (545, 205), p2, 16)
    nr = [46 - 29 * k for k in np.linspace(0, 1, 16)]
    c.chain(neck, nr, body, **SK)
    c.chain([(x + r * 0.45, y + r * 0.15) for (x, y), r in zip(neck, nr)], [r * 0.45 for r in nr], belly, spec=0.3, tex=0.2, rim=0.2)
    hx, hy = p2
    c.ellipsoid(hx + 26, hy - 6, 38, 20, body, **SK)
    c.ellipsoid(hx + 56, hy, 20, 11, body, **SK)
    c.chain([(hx + 38, hy + 6), (hx + 56, hy + 7), (hx + 72, hy + 3)], [1.6, 1.8, 1.4], (0.05, 0.03, 0.02), spec=0, tex=0, rim=0)
    for k in range(5):
        x = hx + 44 + k * 6
        c.cone(x, hy + 5, x + 1, hy + 11, 1.6)
    c.ellipsoid(hx + 36, hy - 18, 11, 3.5, dk, ang=-0.2)
    c.eye(hx + 37, hy - 11, 5, (0.65, 1.0, 0.35), "slit")
    flipper(body, 420, 310, t)
    flipper(body, 250, 310, t + math.pi)


def paint_kraken(c, t):
    red, dk = (0.6, 0.13, 0.11), (0.36, 0.07, 0.07)
    SK = dict(spec=0.6, shine=30, tex=0.28, fine=0.5, rim=1.0)

    def arm(col, j, long=False):
        by = 225
        spread = (j - 3.5) * 24 if not long else (-30 if j else 40)
        L = 270 if long else 230
        pts, rads = [], []
        for k in np.linspace(0, 1, 14):
            y = by + spread * k + math.sin(t + k * 5 + j * 1.3) * 26 * k
            if k > 0.78 and not long:
                y += math.sin((k - 0.78) * 14 + j) * 12
            pts.append((520 + k * L, y))
            rads.append((11 if long else 17) * (1 - k) + 2.5)
        c.chain(pts, rads, col, **SK)
        if long:
            x, y = pts[-1]
            c.ellipsoid(x - 8, y, 22, 10, col, **SK)
        for (x, y), r in zip(pts[1:-1], rads[1:-1]):
            c.ellipsoid(x, y + r * 0.72, r * 0.34, r * 0.24, (0.95, 0.78, 0.72), spec=0.5, tex=0, rim=0)

    for j in range(0, 8, 2):
        arm(dk, j)
    c.ellipsoid(55, 175 + math.sin(t) * 8, 50, 16, red, ang=-0.8, **SK)
    c.ellipsoid(55, 255 - math.sin(t) * 8, 50, 16, red, ang=0.8, **SK)
    c.ellipsoid(255, 215, 215, 92, red, ang=0.02, **SK)
    rr = random.Random(3)
    for _ in range(26):
        c.ellipsoid(rr.uniform(90, 420), rr.uniform(150, 270), rr.uniform(5, 13), rr.uniform(3, 8), dk, tex=0.3)
    c.ellipsoid(470, 225, 78, 72, red, **SK)
    c.ellipsoid(478, 188, 40, 14, dk, ang=0.1)
    c.eye(478, 207, 27, (0.95, 0.78, 0.3), "h", glow=1.8, iem=0.55)
    for j in range(1, 8, 2):
        arm(red, j)
    arm(red, 0, True)
    arm(red, 1, True)


def paint_bigfoot(c, t, costume=False):
    fur, face = (0.36, 0.24, 0.14), (0.22, 0.16, 0.12)
    FUR = dict(spec=0.1, shine=8, tex=0.32, fine=1.0, rim=0.9)
    hipx, hipy = 104, 190
    shx, shy = 128, 98

    def leg(col, ph):
        kx, ky = hipx + 8 + math.sin(ph) * 26, hipy + 56
        fx, fy = hipx + math.sin(ph) * 38 + 6, 292
        c.chain([(hipx, hipy - 6), (kx, ky), (fx, fy)], [32, 21, 14], col, **FUR)
        if costume:
            c.ellipsoid(fx + 14, fy + 9, 25, 10, (0.95, 0.95, 0.95), spec=0.4, tex=0.05)
            c.capsule(fx - 2, fy + 10, fx + 30, fy + 10, 2, 2, (0.85, 0.15, 0.15), tex=0)
        else:
            c.ellipsoid(fx + 16, fy + 9, 30, 10, fmul(col, 0.7), **FUR)

    def arm(col, ph):
        ex, ey = shx + 6 + math.sin(ph) * 24, shy + 72
        hx, hy = shx + math.sin(ph) * 40 + 14, shy + 140
        c.chain([(shx, shy), (ex, ey), (hx, hy)], [21, 15, 12], col, **FUR)
        c.ellipsoid(hx + 3, hy + 8, 12, 16, fmul(col, 0.85), **FUR)
        for k in range(3):
            c.capsule(hx - 3 + k * 5, hy + 18, hx - 2 + k * 5, hy + 28, 3, 2.2, fmul(face, 1.1), spec=0.2, tex=0.1)

    leg(fmul(fur, 0.6), t + math.pi)
    arm(fmul(fur, 0.6), t)
    c.ellipsoid(110, 148, 54, 74, fur, ang=-0.18, **FUR)
    c.ellipsoid(126, 100, 54, 40, fur, ang=-0.3, **FUR)
    rr = random.Random(7)
    for _ in range(160):
        x, y = rr.uniform(64, 170), rr.uniform(64, 215)
        if ((x - 112) / 54) ** 2 + ((y - 140) / 76) ** 2 < 0.92:
            col = fmul(fur, rr.uniform(0.55, 1.45))
            c.capsule(x, y, x - 4, y + rr.uniform(9, 16), 1.7, 0.5, col, spec=0.12, tex=0.1, rim=0.5)
    if costume:
        c.capsule(130, 92, 132, 200, 1.6, 1.6, (0.85, 0.85, 0.8), spec=0.8, tex=0)
        c.capsule(146, 92, 92, 190, 2, 2, (0.1, 0.1, 0.1), spec=0.4, tex=0)
    c.ellipsoid(146, 72, 27, 28, fur, **FUR)
    c.ellipsoid(136, 50, 22, 20, fur, ang=-0.5, **FUR)
    if costume:
        c.ellipsoid(160, 78, 14, 16, (0.92, 0.74, 0.62), spec=0.3, tex=0.05, rim=0.3)
        c.ellipsoid(163, 72, 6, 5, (0.08, 0.08, 0.1), spec=0.9, tex=0)
        c.ellipsoid(163, 72, 3.5, 3, (0.6, 0.75, 0.9), spec=0.9, tex=0)
        c.chain([(155, 86), (162, 90), (170, 87)], [1.4, 1.6, 1.4], (0.45, 0.12, 0.12), tex=0, spec=0)
    else:
        c.ellipsoid(161, 80, 15, 17, face, spec=0.35, shine=20, tex=0.25, fine=1.0)
        c.ellipsoid(163, 66, 17, 7, fmul(fur, 0.45), ang=0.1, **FUR)
        c.ellipsoid(166, 72, 3.4, 2.4, (0.02, 0.01, 0.01), spec=0.9, shine=40, tex=0)
        c.ellipsoid(171, 84, 7, 6, fmul(face, 1.3), spec=0.4, tex=0.2)
        c.chain([(156, 93), (164, 94), (172, 92)], [1.5, 1.7, 1.4], (0.06, 0.04, 0.03), tex=0, spec=0)
    leg(fur, t)
    arm(fur, t + math.pi)


# ---------------------------------------------------------------- מסיחי דעת

def paint_whale(c, t, sperm=False):
    body = (0.25, 0.28, 0.33) if not sperm else (0.3, 0.29, 0.3)
    SK = dict(spec=0.5, shine=26, tex=0.2, fine=0.5, rim=1.0)
    sw = math.sin(t)
    pts = [(45 + k * 190, 100 + math.sin(t - k * 2) * 12 * (1 - k)) for k in np.linspace(0, 1, 9)]
    c.ellipsoid(pts[0][0] - 18, pts[0][1] - 14 + sw * 8, 34, 9, body, ang=-0.7, **SK)
    c.ellipsoid(pts[0][0] - 18, pts[0][1] + 14 + sw * 8, 34, 9, body, ang=0.7, **SK)
    if not sperm:
        c.ellipsoid(270, 150, 75, 11, fmul((0.7, 0.72, 0.74), 0.7), ang=0.8, **SK)
    c.chain(pts, [8 + k * 52 for k in np.linspace(0, 1, 9)], body, **SK)
    c.ellipsoid(260, 98, 150, 60, body, **SK)
    c.ellipsoid(205, 44, 20, 6, body, ang=-0.4, **SK)
    if sperm:
        c.ellipsoid(345, 88, 80, 56, body, **SK)
        c.ellipsoid(330, 140, 60, 9, (0.55, 0.55, 0.55), ang=0.05, **SK)
        rr = random.Random(1)
        for _ in range(10):
            x, y = rr.uniform(280, 400), rr.uniform(50, 110)
            c.capsule(x, y, x + rr.uniform(15, 40), y + rr.uniform(-6, 6), 1.5, 1, (0.65, 0.65, 0.65), tex=0, rim=0)
        c.ellipsoid(320, 108, 4, 3, (0.02, 0.02, 0.02), spec=0.8, tex=0)
    else:
        c.ellipsoid(275, 125, 125, 26, (0.75, 0.76, 0.76), spec=0.3, tex=0.2, rim=0.2)
        for j in range(5):
            c.chain([(180, 118 + j * 7), (300, 125 + j * 6), (380, 112 + j * 4)], [1.4] * 3, (0.3, 0.32, 0.35), tex=0, rim=0)
        c.ellipsoid(360, 100, 70, 42, body, **SK)
        for i in range(6):
            c.ellipsoid(345 + i * 12, 70 + (i % 2) * 4, 4, 4, (0.38, 0.4, 0.45), tex=0.1)
        c.ellipsoid(345, 108, 4, 3, (0.02, 0.02, 0.02), spec=0.8, tex=0)
        c.ellipsoid(300, 150, 85, 12, (0.72, 0.74, 0.76), ang=0.7, **SK)


def paint_shark(c, t):
    body, bel = (0.38, 0.45, 0.53), (0.86, 0.87, 0.86)
    SK = dict(spec=0.55, shine=30, tex=0.15, fine=0.7, rim=1.0)
    pts = [(45 + k * 130, 65 + math.sin(t - k * 2.5) * 10 * (1 - k)) for k in np.linspace(0, 1, 8)]
    tx, ty = pts[0]
    c.ellipsoid(tx - 12, ty - 22, 32, 8, body, ang=-1.0, **SK)
    c.ellipsoid(tx - 8, ty + 18, 22, 7, body, ang=0.9, **SK)
    c.chain(pts, [6 + 34 * k for k in np.linspace(0, 1, 8)], body, **SK)
    c.poly([(165, 38), (195, -2 + 2), (218, 36)], fmul(body, 0.9))
    c.ellipsoid(190, 65, 110, 36, body, **SK)
    c.ellipsoid(200, 84, 92, 15, bel, spec=0.3, tex=0.05, rim=0.2)
    c.ellipsoid(285, 63, 32, 21, body, **SK)
    c.poly([(215, 84), (180, 122), (245, 92)], fmul(body, 0.8))
    for i in range(4):
        c.capsule(238 + i * 6, 54, 236 + i * 6, 72, 1.3, 1.3, (0.15, 0.18, 0.22), tex=0, rim=0)
    c.chain([(262, 78), (285, 80), (306, 72)], [2, 2, 1.6], (0.12, 0.05, 0.05), tex=0, spec=0, rim=0)
    for k in range(6):
        c.cone(266 + k * 6, 78, 267 + k * 6, 84, 1.6)
    c.ellipsoid(272, 56, 4.5, 4.5, (0.01, 0.01, 0.01), spec=0.9, shine=40, tex=0, rim=0)


def paint_seal(c, t):
    body = (0.5, 0.53, 0.56)
    SK = dict(spec=0.6, shine=30, tex=0.15, fine=0.5, rim=1.0)
    sw = math.sin(t)
    c.ellipsoid(25, 60 + sw * 6, 26, 8, body, ang=-0.5 + sw * 0.2, **SK)
    c.ellipsoid(25, 78 - sw * 6, 26, 8, body, ang=0.5 - sw * 0.2, **SK)
    c.chain([(40, 70), (80, 66), (120, 62)], [12, 28, 34], body, **SK)
    c.ellipsoid(115, 62, 72, 32, body, **SK)
    rr = random.Random(8)
    for _ in range(18):
        c.ellipsoid(rr.uniform(60, 170), rr.uniform(42, 78), rr.uniform(3, 7), rr.uniform(2, 5), (0.22, 0.23, 0.26), tex=0.1)
    c.ellipsoid(140, 85, 30, 8, body, ang=0.6 + sw * 0.3, **SK)
    c.ellipsoid(190, 54, 34, 25, body, **SK)
    c.ellipsoid(215, 60, 16, 12, fmul(body, 1.1), **SK)
    c.ellipsoid(196, 46, 6, 6, (0.01, 0.01, 0.01), spec=0.9, shine=40, tex=0, rim=0)
    for k in range(3):
        c.capsule(215, 62, 230, 56 + k * 6, 0.8, 0.5, (0.9, 0.9, 0.85), tex=0, rim=0)


def paint_log(c, t):
    bark = (0.34, 0.24, 0.15)
    SK = dict(spec=0.15, shine=8, tex=0.7, fine=0.75, rim=0.6)
    c.capsule(30, 52, 370, 40, 26, 21, bark, **SK)
    c.ellipsoid(372, 40, 9, 20, (0.6, 0.45, 0.28), tex=0.4, fine=1.0)
    c.capsule(140, 36, 120, 4, 6, 3, bark, **SK)
    c.capsule(260, 34, 300, 8, 5, 2.5, bark, **SK)
    c.capsule(200, 62, 230, 82, 5, 2.5, bark, **SK)
    rr = random.Random(6)
    for _ in range(8):
        c.ellipsoid(rr.uniform(50, 350), rr.uniform(32, 60), rr.uniform(8, 20), rr.uniform(4, 8), (0.25, 0.38, 0.15), tex=0.4)


def paint_sturgeon(c, t):
    body, bel = (0.42, 0.4, 0.34), (0.75, 0.72, 0.62)
    SK = dict(spec=0.5, shine=26, tex=0.25, fine=0.6, rim=1.0)
    pts = [(55 + k * 210, 55 + math.sin(t - k * 2.2) * 10 * (1 - k)) for k in np.linspace(0, 1, 10)]
    rads = [7 + 24 * min(1, k * 1.4) for k in np.linspace(0, 1, 10)]
    tx, ty = pts[0]
    c.ellipsoid(tx - 24, ty - 16, 34, 7, body, ang=-0.7, **SK)
    c.ellipsoid(tx - 14, ty + 10, 18, 6, body, ang=0.7, **SK)
    c.chain(pts, rads, body, **SK)
    c.chain([(x, y + r * 0.5) for (x, y), r in zip(pts, rads)], [r * 0.45 for r in rads], bel, spec=0.3, tex=0.1, rim=0.2)
    for (x, y), r in zip(pts[1:], rads[1:]):
        c.ellipsoid(x, y - r * 0.85, 5, 3.5, (0.78, 0.75, 0.66), spec=0.6, tex=0.1)
        c.ellipsoid(x + 8, y, 3.5, 2.5, (0.72, 0.7, 0.6), spec=0.6, tex=0.1)
    c.capsule(262, 54, 312, 62, 20, 5, body, **SK)
    for k in range(4):
        c.capsule(290 + k * 4, 66, 290 + k * 4, 78, 1, 0.8, (0.8, 0.75, 0.65), tex=0, rim=0)
    c.ellipsoid(268, 48, 3.5, 3.5, (0.02, 0.02, 0.02), spec=0.9, tex=0, rim=0)


def paint_otters(c, t):
    fur = (0.36, 0.25, 0.15)
    SK = dict(spec=0.5, shine=26, tex=0.3, fine=0.8, rim=1.0)
    for i in range(3):
        ox = 15 + i * 95
        ph = t + i * 1.3
        bump = math.sin(ph) * 12
        pts = [(ox + k * 70, 48 - math.sin(k * math.pi) * (10 + bump)) for k in np.linspace(0, 1, 7)]
        c.chain(pts, [4, 9, 13, 14, 13, 11, 10], fur, **SK)
        hx, hy = pts[-1]
        c.ellipsoid(hx + 10, hy - 2, 14, 11, fur, **SK)
        c.ellipsoid(hx + 3, hy - 12, 3.5, 3, fur, **SK)
        c.ellipsoid(hx + 20, hy, 6, 5, fmul(fur, 1.3), **SK)
        c.ellipsoid(hx + 14, hy - 5, 2.4, 2.4, (0.01, 0.01, 0.01), spec=0.9, tex=0, rim=0)


def paint_eel(c, t):
    body, bel = (0.3, 0.3, 0.22), (0.6, 0.56, 0.4)
    SK = dict(spec=0.65, shine=34, tex=0.15, fine=0.6, rim=1.0)
    pts, rads = [], []
    for k in np.linspace(0, 1, 28):
        pts.append((20 + k * 320, 45 + math.sin(k * 9 - t) * 18 * (0.3 + 0.7 * (1 - k))))
        rads.append(3 + 12 * min(1, k * 2.2))
    c.chain([(x, y - r * 0.9) for (x, y), r in zip(pts, rads)], [r * 0.35 for r in rads], fmul(body, 0.7), **SK)
    c.chain(pts, rads, body, **SK)
    c.chain([(x, y + r * 0.45) for (x, y), r in zip(pts, rads)], [r * 0.45 for r in rads], bel, spec=0.4, tex=0.1, rim=0.2)
    hx, hy = pts[-1]
    c.ellipsoid(hx + 16, hy, 24, 13, body, **SK)
    c.chain([(hx + 14, hy + 6), (hx + 38, hy + 4)], [1.3, 1.2], (0.05, 0.03, 0.02), tex=0, spec=0, rim=0)
    c.ellipsoid(hx + 24, hy - 4, 3, 3, (0.85, 0.75, 0.3), em=0.5, spec=0.9, tex=0, rim=0)


def paint_deer(c, t):
    fur, bel = (0.55, 0.36, 0.2), (0.85, 0.78, 0.66)
    SK = dict(spec=0.15, shine=10, tex=0.35, fine=0.85, rim=0.8)
    sw = math.sin(t)

    def leg(col, x, ph):
        kx, ky = x + math.sin(ph) * 12, 140
        c.capsule(x, 110, kx, ky, 8, 5, col, **SK)
        c.capsule(kx, ky, kx + math.sin(ph) * 8, 192, 4.5, 3.5, col, **SK)
        c.ellipsoid(kx + math.sin(ph) * 8 + 2, 194, 5, 3, (0.1, 0.08, 0.06), tex=0)

    leg(fmul(fur, 0.65), 62, t + math.pi)
    leg(fmul(fur, 0.65), 140, t)
    c.ellipsoid(100, 95, 64, 30, fur, **SK)
    c.ellipsoid(105, 112, 50, 12, bel, spec=0.1, tex=0.2, rim=0.2)
    c.ellipsoid(38, 80, 9, 6, (0.95, 0.95, 0.92), tex=0.1)
    c.capsule(148, 82, 168, 40, 16, 11, fur, **SK)
    c.ellipsoid(178, 38, 20, 13, fur, ang=0.2, **SK)
    c.ellipsoid(196, 44, 9, 7, fmul(fur, 0.8), **SK)
    c.ellipsoid(166, 20, 11, 4, fur, ang=-1.0, **SK)
    c.ellipsoid(182, 22, 4, 4, (0.01, 0.01, 0.01), spec=0.9, tex=0, rim=0)
    c.ellipsoid(203, 44, 3, 2.5, (0.02, 0.02, 0.02), tex=0, rim=0)
    leg(fur, 72, t)
    leg(fur, 150, t + math.pi)
    _ = sw


def paint_bear(c, t):
    fur = (0.36, 0.23, 0.13)
    SK = dict(spec=0.12, shine=8, tex=0.5, fine=0.85, rim=0.8)

    def leg(col, x, ph):
        fx = x + math.sin(ph) * 20
        c.capsule(x, 110, fx, 176, 20, 15, col, **SK)
        c.ellipsoid(fx + 6, 180, 19, 8, fmul(col, 0.8), **SK)

    leg(fmul(fur, 0.65), 70, t + math.pi)
    leg(fmul(fur, 0.65), 175, t)
    c.ellipsoid(125, 100, 98, 55, fur, **SK)
    c.ellipsoid(165, 72, 52, 36, fur, **SK)
    c.ellipsoid(220, 100, 36, 30, fur, **SK)
    c.ellipsoid(248, 110, 18, 13, (0.6, 0.45, 0.32), **SK)
    c.ellipsoid(260, 106, 6, 5, (0.02, 0.02, 0.02), spec=0.8, tex=0, rim=0)
    c.ellipsoid(206, 74, 9, 8, fur, **SK)
    c.ellipsoid(232, 92, 3.5, 3, (0.01, 0.01, 0.01), spec=0.9, tex=0, rim=0)
    leg(fur, 82, t)
    leg(fur, 185, t + math.pi)


def paint_bush(c, seed, kind="green"):
    rr = random.Random(seed)
    n = 22 if kind != "dry" else 0
    for i in range(n):
        k = i / 22
        x = rr.uniform(40, 240)
        y = 160 - rr.uniform(10, 120) * (1 - abs(x - 140) / 140) ** 0.5
        if kind == "snow":
            col = (rr.uniform(0.75, 0.9), rr.uniform(0.8, 0.92), rr.uniform(0.9, 1.0)) if rr.random() < 0.6 else (0.1, 0.22, 0.15)
        elif kind == "hedge":
            col = (rr.uniform(0.05, 0.1), rr.uniform(0.16, 0.24), rr.uniform(0.06, 0.1))
        else:
            col = (rr.uniform(0.12, 0.25), rr.uniform(0.3, 0.48), rr.uniform(0.08, 0.15))
        c.ellipsoid(x, y, rr.uniform(26, 44), rr.uniform(20, 34), fmul(col, 0.7 + 0.5 * k),
                    spec=0.15, shine=8, tex=0.6, fine=0.9, rim=0.5)
    if kind == "dry":
        for _ in range(60):
            a = -math.pi / 2 + rr.uniform(-1.3, 1.3)
            L = rr.uniform(60, 140)
            col = (rr.uniform(0.4, 0.55), rr.uniform(0.3, 0.4), rr.uniform(0.18, 0.25))
            c.capsule(140, 165, 140 + math.cos(a) * L, 165 + math.sin(a) * L, 3, 1, col, spec=0.1, tex=0.3)
        for _ in range(30):
            c.ellipsoid(rr.uniform(50, 230), rr.uniform(40, 140), 9, 6, (0.45, 0.48, 0.25), tex=0.5, spec=0.1)
    elif kind == "green":
        for _ in range(6):
            c.ellipsoid(rr.uniform(50, 230), rr.uniform(60, 150), 4, 4, (0.85, 0.15, 0.2), spec=0.8, tex=0)


# ---------------------------------------------------------------- שחקנים (צוללת וחוקר)


def _pg_ell(S, col, cx, cy, rx, ry, s):
    for i in range(6):
        k = i / 5
        f = 1 - 0.75 * k
        c = mix(mul(col, 0.45), mix(col, (255, 255, 255), 0.3), k)
        w, h = 2 * rx * f * s, 2 * ry * f * s
        if w >= 1 and h >= 1:
            pygame.draw.ellipse(S, c, pygame.Rect((cx - rx * 0.18 * k) * s - w / 2, (cy - ry * 0.25 * k) * s - h / 2, w, h))


def _pg_line(S, col, a, b, w, s):
    pygame.draw.line(S, col, (a[0] * s, a[1] * s), (b[0] * s, b[1] * s), max(1, int(w * s)))


def paint_sub(S, t, s):
    yel = (240, 192, 45)
    ry = 16 * abs(math.cos(t))
    _pg_line(S, (90, 90, 95), (24, 36), (8, 36), 5, s)
    if ry > 1.5:
        _pg_ell(S, (160, 160, 170), 8, 36, 4, ry, s)
    _pg_line(S, mul(yel, 0.8), (30, 30), (16, 14), 7, s)
    _pg_line(S, mul(yel, 0.8), (30, 42), (16, 58), 7, s)
    _pg_ell(S, yel, 66, 38, 50, 21, s)
    _pg_ell(S, yel, 66, 19, 18, 11, s)
    _pg_line(S, (80, 80, 85), (72, 12), (72, 2), 3, s)
    _pg_line(S, (80, 80, 85), (72, 2), (80, 2), 3, s)
    pygame.draw.line(S, (190, 60, 30), (24 * s, 44 * s), (110 * s, 44 * s), max(1, int(3 * s)))
    for x, r in ((88, 11), (62, 7)):
        pygame.draw.circle(S, (60, 60, 66), (x * s, 35 * s), r * s)
        pygame.draw.circle(S, (110, 195, 255), (x * s, 35 * s), (r - 3) * s)
        pygame.draw.circle(S, (230, 250, 255), ((x - 3) * s, 32 * s), 2.5 * s)
    _pg_ell(S, (255, 250, 215), 114, 40, 5, 7, s)


def paint_explorer(S, t, s, head=True):
    pants, jacket, skin, boot = (55, 62, 85), (190, 75, 40), (235, 190, 150), (50, 35, 25)
    hip = (45, 100)

    def leg(col, ph):
        kx, ky = hip[0] + math.sin(ph) * 16, hip[1] + 34
        fx, fy = hip[0] + math.sin(ph) * 24, 156
        _pg_line(S, col, hip, (kx, ky), 16, s)
        _pg_line(S, col, (kx, ky), (fx, fy), 14, s)
        _pg_ell(S, boot, fx + 6, fy + 5, 12, 6, s)

    leg(mul(pants, 0.7), t + math.pi)
    _pg_ell(S, (90, 100, 60), 26, 66, 15, 26, s)
    _pg_ell(S, jacket, 46, 70, 19, 33, s)
    leg(pants, t)
    _pg_line(S, jacket, (50, 54), (70, 72), 12, s)
    _pg_ell(S, skin, 74, 72, 6, 6, s)
    _pg_line(S, (40, 40, 45), (72, 66), (92, 60), 7, s)
    pygame.draw.rect(S, (30, 30, 30), (80 * s, 56 * s, 14 * s, 10 * s))
    if not head:
        _pg_line(S, skin, (50, 42), (51, 33), 8, s)
        return
    _pg_ell(S, skin, 52, 27, 13, 14, s)
    _pg_ell(S, (120, 90, 50), 52, 16, 21, 5, s)
    _pg_ell(S, (120, 90, 50), 51, 11, 12, 8, s)
    pygame.draw.circle(S, (30, 20, 15), (59 * s, 25 * s), 1.6 * s)


def render_frames(painter, bw, bh, k, n, ss=2):
    frames = []
    for i in range(n):
        big = pygame.Surface((max(1, int(bw * k * ss)), max(1, int(bh * k * ss))), SRCALPHA)
        painter(big, i / n * TAU, k * ss)
        frames.append(pygame.transform.smoothscale(big, (max(1, int(bw * k)), max(1, int(bh * k)))))
    return frames


# ---------------------------------------------------------------- מפלצות יבשה חדשות


def paint_deathworm(c, t):
    red, dk = (0.62, 0.1, 0.08), (0.3, 0.03, 0.03)
    SK = dict(spec=0.85, shine=40, tex=0.25, fine=0.6, rim=1.0)
    pts, rads = [], []
    for k in np.linspace(0, 1, 16):
        x = 130 + math.sin(t + k * 3.2) * 16 * k + 18 * k
        y = 385 - k * 300
        pts.append((x, y))
        rads.append(44 - 6 * k)
    for (x, y), r in zip(pts[1:-2:2], rads[1:-2:2]):
        c.cone(x - r * 0.7, y, x - r - 14, y - 8, 5, (0.45, 0.08, 0.06))
    c.chain(pts, rads, red, **SK)
    for (x, y), r in zip(pts[1:-1], rads[1:-1]):
        c.capsule(x - r * 0.92, y + 4, x + r * 0.92, y + 4, 3.2, 3.2, dk, spec=0.3, tex=0.2, rim=0.2)
    hx, hy = pts[-1]
    c.ellipsoid(hx + 2, hy - 8, 40, 20, red, ang=-0.15, **SK)
    c.ellipsoid(hx + 4, hy - 12, 30, 13, (0.2, 0.02, 0.03), ang=-0.15, tex=0, spec=0.2, rim=0)
    c.ellipsoid(hx + 5, hy - 10, 18, 7, (0.05, 0.0, 0.0), ang=-0.15, tex=0, spec=0, rim=0)
    for i in range(14):
        a = i / 14 * TAU
        rx, ry = 30 * math.cos(a), 13 * math.sin(a)
        ca, sa = math.cos(-0.15), math.sin(-0.15)
        bx, by = hx + 4 + rx * ca - ry * sa, hy - 12 + rx * sa + ry * ca
        c.cone(bx, by, hx + 4 + (bx - hx - 4) * 0.55, hy - 12 + (by - hy + 12) * 0.55 + 2, 2.6)
    drip = (math.sin(t) * 0.5 + 0.5)
    c.ellipsoid(hx + 30, hy + 4 + drip * 20, 4, 6, (0.5, 1.0, 0.2), em=1.8, tex=0, spec=0.6, rim=0)
    c.glow(hx + 30, hy + 4 + drip * 20, 22, (0.2, 0.5, 0.05))
    c.glow(hx + 4, hy - 12, 40, (0.15, 0.35, 0.03))


def paint_nightcrawlers(c, t):
    white = (0.92, 0.93, 0.95)
    SK = dict(spec=0.3, shine=16, tex=0.05, fine=0.5, rim=1.2, em=0.12)

    def crawler(x, hip, foot, sc, ph):
        for side, col in ((math.pi, fmul(white, 0.75)), (0, white)):
            p2 = ph + side
            kx, ky = x + math.sin(p2) * 20 * sc, hip + (foot - hip) * 0.5
            fx = x + math.sin(p2) * 34 * sc
            c.chain([(x, hip), (kx, ky), (fx, foot)], [9 * sc, 6.5 * sc, 5 * sc], col, **SK)
            c.ellipsoid(fx + 6 * sc, foot + 3, 9 * sc, 4 * sc, col, **SK)
            if side == math.pi:
                c.ellipsoid(x, hip - 30 * sc, 24 * sc, 38 * sc, white, **SK)
                c.ellipsoid(x - 2 * sc, hip - 62 * sc, 13 * sc, 12 * sc, white, **SK)

    crawler(55, 205, 312, 0.62, t + 1.3)
    crawler(130, 120, 312, 1.0, t)


def paint_wendigo(c, t):
    skin, bone, dk = (0.5, 0.46, 0.42), (0.9, 0.87, 0.78), (0.16, 0.13, 0.12)
    SK = dict(spec=0.35, shine=20, tex=0.35, fine=0.8, rim=1.0)
    sw = math.sin(t)
    hipx, hipy = 118, 255
    shx, shy = 145, 135

    def leg(col, ph):
        kx, ky = hipx + 20 + math.sin(ph) * 22, hipy + 70
        ax, ay = hipx - 10 + math.sin(ph) * 30, hipy + 125
        fx, fy = ax + 18, 425
        c.chain([(hipx, hipy), (kx, ky), (ax, ay), (fx, fy)], [17, 10, 7, 6], col, **SK)
        for k in range(3):
            c.cone(fx + 2, fy, fx + 22, fy + 2 - k * 3, 2.5, (0.2, 0.18, 0.16))

    def arm(col, ph):
        ex, ey = shx + 12 + math.sin(ph) * 22, shy + 95
        hx, hy = shx + 26 + math.sin(ph) * 36, shy + 190
        c.chain([(shx, shy), (ex, ey), (hx, hy)], [13, 8, 6], col, **SK)
        for k in range(4):
            a = 1.2 + k * 0.18
            fx, fy = hx + math.cos(a) * 34, hy + math.sin(a) * 34
            c.capsule(hx, hy, fx, fy, 3, 2, col, **SK)
            c.cone(fx, fy, fx + math.cos(a) * 14, fy + math.sin(a) * 14, 2, (0.15, 0.13, 0.12))

    leg(fmul(skin, 0.6), t + math.pi)
    arm(fmul(skin, 0.6), t)
    c.ellipsoid(128, 200, 36, 70, skin, ang=-0.35, **SK)
    for i in range(6):
        y = 165 + i * 15
        c.capsule(108 + i * 3, y, 160 - i * 4, y - 12, 3, 2.5, fmul(skin, 1.35), spec=0.4, tex=0.2, rim=0.3)
    c.ellipsoid(140, 140, 40, 26, skin, ang=-0.5, **SK)
    rr = random.Random(12)
    for _ in range(26):
        x, y = rr.uniform(110, 170), rr.uniform(118, 150)
        c.capsule(x, y, x - rr.uniform(5, 15), y + rr.uniform(15, 40), 2, 0.6, dk, spec=0.1, tex=0.2)
    c.capsule(160, 120, 180, 96, 9, 7, skin, **SK)
    hx, hy = 196, 92
    c.ellipsoid(hx, hy, 26, 20, bone, ang=0.35, spec=0.4, tex=0.3, fine=0.9)
    c.capsule(hx + 6, hy + 6, hx + 40, hy + 26, 13, 7, bone, spec=0.4, tex=0.3, fine=0.9)
    c.ellipsoid(hx + 2, hy, 9, 8, (0.02, 0.01, 0.01), tex=0, spec=0, rim=0)
    c.ellipsoid(hx + 3, hy + 1, 2.6, 2.6, (1.0, 0.25, 0.15), em=3.0, tex=0, spec=0, rim=0)
    c.glow(hx + 3, hy + 1, 18, (0.6, 0.1, 0.05))
    for k in range(5):
        x = hx + 18 + k * 4.5
        c.cone(x, hy + 30 + k * 2.5, x + 1, hy + 39 + k * 2.5, 1.7)
    antler = (0.42, 0.33, 0.24)
    for side, off in ((-1, -6), (1, 6)):
        base = (hx - 8 + off, hy - 14)
        p1 = (base[0] - 18 + side * 6, base[1] - 40)
        p2 = (p1[0] - 22 + side * 8, p1[1] - 38)
        c.chain([base, p1, p2], [5, 4, 2.5], antler, spec=0.3, tex=0.5, fine=0.9)
        for (bx, by), ln in ((p1, 26), (((base[0] + p1[0]) / 2, (base[1] + p1[1]) / 2), 18), (p2, 16)):
            c.capsule(bx, by, bx + 10 + side * 6, by - ln, 3, 1.5, antler, spec=0.3, tex=0.5, fine=0.9)
    leg(skin, t)
    arm(skin, t + math.pi)
    _ = sw


def paint_dover(c, t):
    skin = (0.86, 0.68, 0.55)
    SK = dict(spec=0.35, shine=22, tex=0.14, fine=1.0, rim=1.0)

    def leg(col, ph):
        hx, hy = 82, 160
        kx, ky = hx + math.sin(ph) * 14, 200
        fx, fy = hx + math.sin(ph) * 22, 238
        c.chain([(hx, hy), (kx, ky), (fx, fy)], [6, 4.5, 4], col, **SK)
        for k in range(3):
            c.capsule(fx, fy, fx + 16, fy + 3 - k * 3, 2, 1.2, col, **SK)

    def arm(col, ph):
        sx, sy = 92, 112
        ex, ey = sx + math.sin(ph) * 12 + 6, 150
        hx, hy = sx + math.sin(ph) * 18 + 10, 184
        c.chain([(sx, sy), (ex, ey), (hx, hy)], [4.5, 3.5, 3], col, **SK)
        for k in range(4):
            a = 1.0 + k * 0.25
            c.chain([(hx, hy), (hx + math.cos(a) * 14, hy + math.sin(a) * 14),
                     (hx + math.cos(a + 0.5) * 24, hy + math.sin(a + 0.5) * 26)], [1.8, 1.4, 1.0], col, **SK)

    leg(fmul(skin, 0.65), t + math.pi)
    arm(fmul(skin, 0.65), t)
    c.ellipsoid(86, 135, 16, 30, skin, **SK)
    c.capsule(92, 104, 98, 90, 5, 4, skin, **SK)
    c.ellipsoid(100, 58, 48, 40, skin, ang=0.25, **SK)
    for ex, ey in ((118, 58), (138, 64)):
        c.ellipsoid(ex, ey, 9, 7, (1.0, 0.55, 0.1), em=2.6, spec=0.8, tex=0.2, fine=1.0, rim=0)
        c.glow(ex, ey, 24, (0.7, 0.3, 0.02))
    leg(skin, t)
    arm(skin, t + math.pi)


# ---------------------------------------------------------------- מסיחי דעת ביבשה


def paint_camel(c, t):
    fur = (0.68, 0.52, 0.32)
    SK = dict(spec=0.1, shine=8, tex=0.25, fine=1.0, rim=0.8)

    def leg(col, x, ph):
        kx = x + math.sin(ph) * 14
        c.chain([(x, 150), (kx, 205), (kx + math.sin(ph) * 8, 252)], [13, 8, 7], col, **SK)
        c.ellipsoid(kx + math.sin(ph) * 8 + 4, 254, 11, 5, fmul(col, 0.7), **SK)

    leg(fmul(fur, 0.65), 105, t + math.pi)
    leg(fmul(fur, 0.65), 200, t)
    c.capsule(70, 125, 50, 175, 5, 3, fur, **SK)
    c.ellipsoid(150, 135, 88, 42, fur, **SK)
    c.ellipsoid(118, 88, 28, 32, fmul(fur, 0.9), **SK)
    c.ellipsoid(180, 88, 28, 32, fmul(fur, 0.9), **SK)
    c.chain([(225, 125), (248, 108), (255, 72)], [20, 14, 12], fur, **SK)
    c.ellipsoid(270, 64, 26, 14, fur, ang=0.15, **SK)
    c.ellipsoid(254, 50, 4, 6, fur, **SK)
    c.ellipsoid(268, 58, 3, 3, (0.02, 0.02, 0.02), spec=0.8, tex=0, rim=0)
    leg(fur, 115, t)
    leg(fur, 210, t + math.pi)


def paint_snake(c, t):
    col = (0.72, 0.6, 0.42)
    SK = dict(spec=0.5, shine=24, tex=0.3, fine=0.7, rim=0.8)
    pts = [(12 + k * 230, 46 + math.sin(k * 10 - t) * 9) for k in np.linspace(0, 1, 26)]
    rads = [2 + 8 * min(1, k * 2.5) for k in np.linspace(0, 1, 26)]
    c.chain(pts, rads, col, **SK)
    for (x, y), r in zip(pts[2:-1:2], rads[2:-1:2]):
        c.ellipsoid(x, y - r * 0.2, r * 0.6, r * 0.5, (0.38, 0.26, 0.16), tex=0.2, spec=0.3)
    hx, hy = pts[-1]
    c.ellipsoid(hx + 12, hy - 2, 15, 9, col, **SK)
    c.ellipsoid(hx + 16, hy - 5, 2, 2, (0.02, 0.02, 0.02), spec=0.9, tex=0, rim=0)


def paint_cat(c, t):
    fur = (0.13, 0.13, 0.14)
    SK = dict(spec=0.3, shine=18, tex=0.3, fine=0.9, rim=1.0)

    def leg(col, x, ph):
        c.capsule(x, 55, x + math.sin(ph) * 8, 86, 5, 3.5, col, **SK)

    leg(fmul(fur, 0.6), 35, t + math.pi)
    leg(fmul(fur, 0.6), 80, t)
    c.chain([(25, 50), (10, 30), (12, 8)], [4, 3.5, 3], fur, **SK)
    c.ellipsoid(58, 52, 34, 16, fur, **SK)
    c.ellipsoid(100, 38, 15, 13, fur, **SK)
    c.poly([(90, 30), (92, 14), (100, 27)], fur)
    c.poly([(102, 27), (110, 12), (112, 30)], fur)
    c.eye(106, 37, 3.4, (0.5, 1.0, 0.3), "slit", glow=4)
    leg(fur, 45, t)
    leg(fur, 90, t + math.pi)


def paint_raccoon(c, t):
    fur, dk = (0.48, 0.46, 0.44), (0.12, 0.11, 0.1)
    SK = dict(spec=0.2, shine=12, tex=0.45, fine=0.9, rim=1.0)

    def leg(col, x, ph):
        c.capsule(x, 62, x + math.sin(ph) * 8, 92, 6, 4.5, col, **SK)

    leg(fmul(dk, 1.2), 50, t + math.pi)
    leg(fmul(dk, 1.2), 100, t)
    tail = [(36 - k * 34, 52 - k * 16) for k in np.linspace(0, 1, 7)]
    for i, (x, y) in enumerate(tail):
        c.ellipsoid(x, y, 10, 9, dk if i % 2 else fur, **SK)
    c.ellipsoid(75, 58, 40, 22, fur, **SK)
    c.ellipsoid(122, 48, 20, 16, fur, **SK)
    c.ellipsoid(142, 54, 10, 6, (0.75, 0.73, 0.7), **SK)
    c.ellipsoid(128, 44, 13, 6, dk, tex=0.2)
    c.ellipsoid(114, 32, 5, 7, fur, **SK)
    c.eye(130, 44, 2.6, (1.0, 0.85, 0.4), "round", glow=4)
    leg(dk, 60, t)
    leg(dk, 110, t + math.pi)


def paint_ghost(c, t):
    sheet = (0.95, 0.95, 0.93)
    sw = math.sin(t) * 6
    for k in (math.pi, 0):
        fx = 70 + math.sin(t + k) * 14
        c.ellipsoid(fx, 232, 14, 6, (0.95, 0.95, 0.95), spec=0.5, tex=0.05)
        c.capsule(fx - 10, 230, fx + 12, 230, 2, 2, (0.2, 0.35, 0.85), tex=0)
    pts = [(70, 30), (40, 70), (28, 150), (20 + sw, 222), (50, 214), (75, 224), (100, 214), (122 + sw, 222), (112, 150), (100, 70)]
    c.poly(pts, sheet, tex=0.15, em=0.05)
    c.ellipsoid(70, 52, 32, 32, sheet, spec=0.2, tex=0.1, em=0.05)
    for x in (60, 82):
        c.ellipsoid(x, 52, 6, 8, (0.02, 0.02, 0.02), tex=0, spec=0, rim=0)


def paint_wolf(c, t):
    fur = (0.42, 0.42, 0.44)
    SK = dict(spec=0.15, shine=10, tex=0.45, fine=0.9, rim=1.0)

    def leg(col, x, ph):
        kx = x + math.sin(ph) * 12
        c.chain([(x, 82), (kx, 112), (kx + math.sin(ph) * 6, 144)], [10, 6, 5], col, **SK)

    leg(fmul(fur, 0.6), 70, t + math.pi)
    leg(fmul(fur, 0.6), 150, t)
    c.chain([(55, 68), (30, 80), (12, 104)], [12, 11, 7], fur, **SK)
    c.ellipsoid(110, 72, 62, 28, fur, **SK)
    c.ellipsoid(150, 62, 30, 26, fur, **SK)
    c.ellipsoid(190, 54, 22, 17, fur, **SK)
    c.capsule(200, 58, 226, 64, 10, 6, fmul(fur, 1.1), **SK)
    c.poly([(178, 40), (184, 18), (194, 38)], fmul(fur, 0.8))
    c.ellipsoid(228, 63, 3.5, 3, (0.02, 0.02, 0.02), tex=0, rim=0)
    c.eye(204, 50, 3.6, (1.0, 0.85, 0.2), "round", glow=4)
    leg(fur, 80, t)
    leg(fur, 160, t + math.pi)

# ======================================================================= נתוני המפלצות

WATER_RIM = (0.18, 0.32, 0.5)
DAY_RIM = (0.32, 0.3, 0.22)

MONSTERS = [
    dict(key="ningen", name="נינגן", place="האוקיינוס הדרומי, אנטארקטיקה", stars=2,
         painter=paint_ningen, size=(660, 459), k=1.0, rs=0.75, nframes=10, anim=4.5,
         sprite=dict(key="ningen", w=660, eyes=[(0.727, 0.162), (0.643, 0.138)], eye_col=(140, 200, 255), eye_r=20,
                     wag=(0.35, 0.66, 14)),
         speed=55, flee=200, mode="stalker", charge=150, home=(0.68, 9999), depth=(0.1, 0.9),
         samples=[(0.69, 0.17), (0.54, 0.47), (0.12, 0.35), (0.43, 0.9)],
         face=(0.69, 0.22, 0.75), roar=0.45, bubbles=0.4,
         hab=dict(kind="water", w=4600, h=1900, ice=True, top_col=(45, 88, 125), bot_col=(4, 10, 24),
                  floor_col=(70, 78, 92), sand_col=(145, 155, 170), floor_base=140, floor_amp=330,
                  dark_top=165, dark_bot=240, dark_col=(0, 4, 14), jelly=10, fish=0, kelp=0, rocks=40,
                  rays=True, decoys=[("whale", 2), ("seal", 4)]),
         story=["בשנות ה-2000 התחילו להופיע באינטרנט היפני סיפורים מוזרים. מלחים על ספינות במים הקפואים של "
                "אנטארקטיקה סיפרו שראו בלילה יצור לבן וענק שצף לידם בחושך.",
                "ליצור היו ידיים ארוכות עם אצבעות, ראש עגול וחלק בלי אוזניים, ולפעמים זנב כמו של לוויתן. "
                "האורך שלו: 20 עד 30 מטר! המלחים קראו לו 'נינגן', שפירושו ביפנית 'בן אדם'.",
                "אף אחד עוד לא הצליח לצלם אותו בבירור. עכשיו תורך: צלול עם הצוללת אל מתחת לקרח, "
                "בין קרחונים חשוכים, ותמצא את הענק הלבן."],
         tip="זהירות: אומרים שהנינגן קופא במקום כשמאירים עליו... ומתקרב אליך כשאתה מסתכל לכיוון אחר.",
         fact="ידעת? 'נינגן' פירושו 'בן אדם' ביפנית, כי לפי הסיפורים יש לו ידיים וגוף שנראים קצת אנושיים."),
    dict(key="ogopogo", name="אוגופוגו", place="אגם אוקנגן, קנדה", stars=1,
         painter=paint_ogopogo, size=(950, 300), k=0.9, rs=0.8, nframes=12, anim=6,
         speed=75, flee=240, mode="shy", home=(0.62, 1500), depth=(0.0, 0.75),
         samples=[(0.5, 0.55), (0.25, 0.6), (0.85, 0.3), (0.65, 0.55)],
         face=(0.86, 0.3, 0.32), roar=0.3, bubbles=0.35,
         hab=dict(kind="water", w=4800, h=1350, surface=150, top_col=(55, 115, 105), bot_col=(8, 30, 32),
                  floor_col=(85, 78, 60), sand_col=(150, 135, 95), floor_base=110, floor_amp=280,
                  dark_top=50, dark_bot=215, dark_sky=0, dark_col=(0, 10, 8), jelly=0, fish=30, kelp=55,
                  rocks=30, rays=True, sky_top=(80, 140, 215), sky_hor=(190, 220, 240),
                  mount=(75, 100, 120), island=True,
                  decoys=[("log", 3), ("sturgeon", 3), ("otters", 2)]),
         story=["באגם אוקנגן שבקנדה מסתתר, לפי האגדה, נחש מים ענק. בני העמים המקומיים סיפרו כבר לפני "
                "מאות שנים על יצור מים בשם נאיטקה, שגר ליד אי קטן באמצע האגם.",
                "התצפית הראשונה שנרשמה הייתה בשנת 1872. אנשים מתארים גוף ארוך כמו של נחש, עם דבשות "
                "שבולטות מעל המים, וראש שנראה כמו של סוס או נחש. יש אפילו שראו לו רעמה!",
                "רוב התצפיות היו ליד האי רטלסנייק ובאזור סקוואלי פוינט, שם המים עמוקים ויש הרבה דגים. "
                "קח את הצוללת הקטנה וחפש בין עשבי המים."],
         tip="שים לב: באגם יש גם בולי עץ, חדקנים ענקיים ולוטרות ששוחות בשורה - מרחוק כולם נראים כמו אוגופוגו!",
         fact="ידעת? לפי העדים אוגופוגו שוחה בתנועות גל של הגוף למעלה ולמטה, ולכן רואים לו 'דבשות' מעל המים."),
    dict(key="bloop", name="בלופ", place="מעמקי האוקיינוס השקט", stars=3,
         painter=paint_bloop, sprite=dict(key="bloop", w=1350, eyes=[(0.817, 0.108)], wag=(0.42, 1.0, 26)), size=(1350, 767), k=1.0, rs=0.6, nframes=8, anim=2.2,
         speed=45, flee=120, mode="hunter", charge=310, home=(0.65, 9999), depth=(0.45, 1.0),
         samples=[(0.55, 0.45), (0.3, 0.45), (0.75, 0.3), (0.86, 0.55), (0.65, 0.75)],
         face=(0.7, 0.42, 0.95), roar=1.0, bubbles=0.25,
         hab=dict(kind="water", w=5200, h=2500, top_col=(10, 22, 48), bot_col=(0, 2, 8),
                  floor_col=(40, 38, 45), sand_col=(80, 75, 80), floor_base=150, floor_amp=300,
                  dark_top=228, dark_bot=252, dark_col=(0, 1, 6), jelly=16, fish=0, kelp=0, rocks=50,
                  rays=False, vents=4, anglers=10, decoys=[("sperm", 2), ("shark", 4)]),
         story=["בקיץ 1997 קלטו מיקרופונים תת-ימיים של מדענים צליל עמוק ועוצמתי מאוד שהגיע ממעמקי "
                "האוקיינוס השקט. הצליל נשמע במכשירים שהיו רחוקים זה מזה כ-5,000 קילומטר!",
                "הצליל קיבל את השם 'בלופ'. הוא היה חזק יותר מקולו של כל בעל חיים מוכר, ולכן אנשים דמיינו "
                "מפלצת ענקית - גדולה יותר מלוויתן כחול, עם פה שיכול לבלוע צוללת שלמה.",
                "מדענים חושבים היום שהצליל נוצר כנראה מקרחון ענק שנסדק. אבל מי יודע מה באמת מסתתר בחושך "
                "המוחלט שם למטה? השתמש בסונאר - בעומק הזה הפנס לבד לא יספיק."],
         tip="אם בלופ שומע אותך - הוא תוקף עם הפה פתוח! צלם מהר ותברח. וזהירות: לוויתנים וכרישים מבלבלים את הסונאר.",
         fact="ידעת? את הצליל 'בלופ' קלטו מכשירים של NOAA, סוכנות האוקיינוסים של ארה\"ב, שמאזינים לים כל הזמן."),
    dict(key="nessie", name="נסי", place="לוך נס, סקוטלנד", stars=1,
         painter=paint_nessie, size=(600, 532), k=1.0, rs=0.8, nframes=10, anim=4,
         sprite=dict(key="nessie", w=600, eyes=[(0.887, 0.05)], eye_col=(150, 255, 120), eye_r=14, wag=(0.3, 1.0, 12)),
         speed=65, flee=220, mode="shy", home=(0.62, 9999), depth=(0.05, 0.85),
         samples=[(0.6, 0.56), (0.15, 0.74), (0.9, 0.12), (0.93, 0.35), (0.54, 0.88)],
         face=(0.78, 0.3, 0.75), roar=0.35, bubbles=0.35,
         hab=dict(kind="water", w=4400, h=1500, surface=150, top_col=(95, 82, 45), bot_col=(14, 11, 5),
                  floor_col=(70, 60, 45), sand_col=(120, 105, 75), floor_base=120, floor_amp=320,
                  dark_top=95, dark_bot=232, dark_sky=25, dark_col=(6, 4, 0), jelly=0, fish=22, kelp=45,
                  rocks=35, rays=True, sky_top=(110, 120, 135), sky_hor=(175, 180, 185),
                  mount=(55, 75, 55), castle=True, decoys=[("log", 3), ("eel", 4), ("sturgeon", 1)]),
         story=["לוך נס הוא אגם ארוך ועמוק בסקוטלנד, והמים שלו כהים כמו תה בגלל אדמת הכבול. כבר לפני "
                "כ-1,500 שנה סופר על 'חיה' שחיה בנהר שליד האגם.",
                "בשנת 1933 נסלל כביש חדש לאורך האגם, ופתאום אנשים רבים דיווחו שראו יצור עם צוואר ארוך וגוף "
                "גדול. ב-1934 פורסמה 'תמונת המנתח' המפורסמת, שהתגלתה שנים אחר כך כזיוף.",
                "עד היום אנשים מחפשים את נסי עם מצלמות וסונארים. האגם עמוק יותר מ-200 מטר - צלול פנימה "
                "ותהיה הראשון שמצלם אותה באמת!"],
         tip="צלופחים ענקיים ובולי עץ שוקעים כבר בלבלו הרבה ציידים. תבדוק כל צל בסונאר!",
         fact="ידעת? בלוך נס יש יותר מים מתוקים מבכל האגמים של אנגליה וויילס ביחד."),
    dict(key="kraken", name="קראקן", place="הים הנורבגי", stars=2,
         painter=paint_kraken, size=(860, 439), k=1.0, rs=0.8, nframes=10, anim=4,
         sprite=dict(key="kraken", w=860, margin=10, bob=8, wag=(0.3, 1.0, 0),
                     eyes=[(0.437, 0.445), (0.518, 0.455)], eye_col=(255, 120, 60), eye_r=24),
         speed=60, flee=260, mode="ambush", charge=340, home=(0.7, 1000), depth=(0.45, 1.0),
         samples=[(0.5, 0.3), (0.48, 0.6), (0.2, 0.55), (0.82, 0.5), (0.4, 0.85)],
         face=(0.48, 0.42, 0.5), roar=0.7, bubbles=0.35,
         hab=dict(kind="water", w=4800, h=2000, top_col=(22, 48, 80), bot_col=(2, 6, 14),
                  floor_col=(55, 60, 66), sand_col=(110, 112, 115), floor_base=130, floor_amp=300,
                  dark_top=170, dark_bot=242, dark_col=(0, 3, 10), jelly=10, fish=0, kelp=25, rocks=40,
                  rays=False, wreck=True, decoys=[("whale", 1), ("shark", 3), ("sperm", 1)]),
         story=["ימאים נורבגים סיפרו לפני מאות שנים על הקראקן - מפלצת ים ענקית שחיה במים הקרים בין "
                "נורבגיה לגרינלנד, עם זרועות ארוכות שיכולות לגרור ספינה שלמה למצולות.",
                "היום אנחנו יודעים שהאגדה נולדה כנראה מהדיונון הענק - יצור אמיתי שיכול להגיע לאורך של יותר "
                "מ-12 מטר, עם עיניים בגודל של צלחת!",
                "דיונון ענק חי צולם בטבע לראשונה רק בשנת 2004. אומרים שהקראקן אוהב להסתתר ליד ספינות "
                "טרופות... תמצא אותו לפני שהוא ימצא אותך."],
         tip="הקראקן אורב בחושך. אם תתקרב מדי הוא יזנק עליך ואז יתיז ענן דיו שחור ויברח!",
         fact="ידעת? לדיונון הענק יש שלושה לבבות ודם בצבע כחול!"),
    dict(key="bigfoot", name="ביגפוט", place="יערות צפון-מערב אמריקה", stars=2,
         painter=paint_bigfoot, size=(230, 320), k=0.8, rs=0.9, nframes=12, anim=0,
         speed=85, flee=340, mode="hider", home=(0.62, 9999), depth=(0, 1),
         samples=[(0.5, 0.45), (0.62, 0.2), (0.45, 0.82)],
         face=(0.66, 0.24, 0.62), roar=0.35, bubbles=0,
         hab=dict(kind="forest", theme="forest_day", w=6400, h=H, dark_top=0, dark_bot=10, dark_col=(10, 6, 20),
                  decoys=[("deer", 3), ("bear", 2), ("costume", 1)]),
         story=["ביערות העבותים של צפון-מערב אמריקה מספרים על ביגפוט, שנקרא גם סאסקוואץ' - יצור דמוי קוף, "
                "מכוסה פרווה חומה, שגובהו 2 עד 3 מטרים.",
                "בשנת 1958 מצאו פועלים בקליפורניה עקבות ענקיות בבוץ, והעיתונים קראו ליצור 'ביגפוט', "
                "כלומר 'כף רגל גדולה'. ב-1967 צולם סרט קצר ומפורסם שבו רואים דמות שעירה הולכת ביער.",
                "עכשיו אמצע היום ביער. ביגפוט מסתתר מאחורי השיחים - חפש עקבות, הקשב לדפיקות על עצים, "
                "ושים לב לציפורים שבורחות פתאום. יש לך זמן רק עד השקיעה!"],
         tip="אל תרוץ (Shift) - הוא שומע אותך! וזהירות: ביער יש גם צבאים, דובים חומים... ואפילו אנשים בתחפושת.",
         fact="ידעת? המילה 'סאסקוואץ'' מגיעה משפה של אחד העמים הילידים בקנדה, ופירושה 'איש פראי'."),
    dict(key="deathworm", name="תולעת המוות המונגולית", place="מדבר גובי, מונגוליה", stars=3,
         painter=paint_deathworm, size=(340, 376), k=1.0, rs=0.9, nframes=10, anim=5,
         sprite=dict(key="deathworm", w=340, margin=0, wag=(0.3, 1.0, 0),
                     eyes=[(0.684, 0.161), (0.735, 0.154), (0.842, 0.161), (0.878, 0.137)], eye_col=(255, 60, 30), eye_r=12,
                     spots=[(0.827, 0.707, 22, (150, 140, 20)), (0.8, 0.45, 40, (90, 40, 0))]),
         speed=150, flee=200, mode="burrower", home=(0.62, 9999), depth=(0, 1),
         samples=[(0.8, 0.24), (0.34, 0.08), (0.15, 0.6), (0.22, 0.9)],
         face=(0.62, 0.38, 1.5), roar=0.7, bubbles=0,
         hab=dict(kind="forest", theme="desert", w=6400, h=H, dark_top=0, dark_bot=8, dark_col=(20, 8, 0),
                  decoys=[("camel", 3), ("snake", 3)]),
         story=["במדבר גובי שבמונגוליה מספרים הנוודים על אולגוי-חורחוי, שפירושו 'תולעת המעי' - יצור ארוך "
                "ועבה בצבע אדום כהה כמו דם, שחי מתחת לחול.",
                "לפי האגדות, היא זוחלת מתחת לאדמה ומשאירה גלים בחול. אומרים שהיא יכולה לירוק רעל שמשתיק כל דבר, "
                "ואפילו להרוג מרחוק בהתחשמלות! לכן קוראים לה 'תולעת המוות'.",
                "המערב שמע עליה לראשונה בספר של החוקר רוי צ'פמן אנדרוז משנת 1926. מאז יצאו כמה משלחות "
                "לחפש אותה - ואף אחת לא מצאה אותה."],
         tip="שים לב לחול שזז! התולעת חופרת מתחת לאדמה וקופצת החוצה פתאום. אל תעמוד מעליה - צלם ממרחק בטוח.",
         fact="ידעת? ב-1983 הראו למקומיים נחש חול טטרי, והם אמרו שזה בדיוק היצור שהם קוראים לו 'אולגוי-חורחוי'!"),
    dict(key="fresno", name="שוטטי הלילה מפרזנו", place="פרזנו, קליפורניה", stars=1,
         painter=paint_nightcrawlers, size=(220, 291), k=1.0, rs=1.0, nframes=12, anim=0,
         sprite=dict(key="fresno", w=220, margin=6, bob=5, wag=(0.3, 1.0, 0),
                     spots=[(0.27, 0.25, 70, (40, 40, 45)), (0.82, 0.6, 45, (30, 30, 35))]),
         speed=55, flee=300, mode="shy", home=(0.62, 9999), depth=(0, 1),
         samples=[(0.27, 0.2), (0.27, 0.55), (0.82, 0.65)],
         face=(0.3, 0.28, 1.2), roar=0.0, bubbles=0,
         hab=dict(kind="forest", theme="town", night=True, w=6000, h=H, dark_top=140, dark_bot=225, dark_col=(2, 3, 12),
                  decoys=[("cat", 3), ("raccoon", 3), ("ghost", 2)]),
         story=["בשנת 2007 תושב בעיר פרזנו שבקליפורניה רצה לדעת למה הכלבים שלו נובחים כל לילה. הוא התקין "
                "מצלמת אבטחה בחצר - וראה משהו מוזר מאוד.",
                "בסרטון הלילה הופיעה דמות לבנה שהולכת על שתי רגליים ארוכות מאוד, בלי ידיים - כמו זוג מכנסיים "
                "לבנים שהולכים לבד! ב-2011 צולם סרטון נוסף ובו שתי דמויות כאלה, אחת גדולה ואחת קטנה.",
                "אנשים קראו להם 'שוטטי הלילה מפרזנו'. רבים חושבים שזה זיוף, אבל יש מי שמאמינים שהם מסתובבים "
                "בשכונות בשקט כשכולם ישנים..."],
         tip="הם ביישנים ובורחים מהאור. היזהר: בשכונה יש גם חתולים, דביבונים... וילדים מחופשים לרוחות רפאים.",
         fact="ידעת? הסרטון של שוטטי הלילה הפך לתופעה באינטרנט, ויש היום בובות, חולצות ואפילו כוסות עם הדמות שלהם."),
    dict(key="wendigo", name="הוונדיגו", place="יערות הצפון הקפואים, קנדה", stars=3,
         painter=paint_wendigo, size=(250, 374), k=1.0, rs=0.9, nframes=12, anim=0,
         sprite=dict(key="wendigo", w=250, margin=6, bob=6, wag=(0.3, 1.0, 0),
                     eyes=[(0.59, 0.334)], eye_col=(255, 70, 40), eye_r=22),
         speed=60, flee=260, mode="hunter", charge=300, home=(0.65, 9999), depth=(0, 1),
         samples=[(0.63, 0.35), (0.39, 0.4), (0.33, 0.66), (0.6, 0.1)],
         face=(0.64, 0.38, 0.85), roar=0.8, bubbles=0,
         whispers=["שמעת מישהו קורא בשמך מתוך היער...", "הרוח נשמעת כמו צחוק עמוק...", "משהו נשבר בין העצים. ממש קרוב."],
         hab=dict(kind="forest", theme="snow", night=True, w=6400, h=H, dark_top=150, dark_bot=228, dark_col=(2, 4, 14),
                  decoys=[("deer", 3), ("wolf", 3)]),
         story=["בסיפורים של העמים האלגונקיניים בצפון אמריקה, כמו האוג'יבווה והקרי, מסופר על הוונדיגו - "
                "רוח רעבה של חורף, שמסתובבת ביערות הקפואים בלילות הארוכים.",
                "הסיפורים מתארים יצור גבוה ורזה מאוד, כמעט שלד, שאף פעם לא שבע. הם נועדו להזהיר אנשים מפני "
                "חמדנות, ולהזכיר לחלוק אוכל בחורף הקשה. בסרטים ובמשחקים של היום מציירים לו גם ראש של צבי עם קרניים.",
                "עכשיו לילה שלג ביער. לך בזהירות עם הפנס... ואם תשמע מישהו קורא בשמך - אל תענה."],
         tip="הוונדיגו הוא צייד! אם הוא מגלה אותך הוא רץ אליך מהר מאוד. צלם ומיד תברח (Shift)!",
         fact="ידעת? המילה 'ונדיגו' מגיעה משפות אלגונקיניות, ויש לה הרבה צורות כתיבה: ויטיקו, ויטיגו ועוד."),
    dict(key="dover", name="השד מדובר", place="דובר, מסצ'וסטס", stars=2,
         painter=paint_dover, size=(180, 213), k=1.0, rs=1.0, nframes=12, anim=0,
         sprite=dict(key="dover", w=180, margin=6, bob=6, wag=(0.3, 1.0, 0),
                     eyes=[(0.26, 0.181), (0.476, 0.181)], eye_col=(255, 140, 30), eye_r=26),
         speed=60, flee=320, mode="shy", home=(0.62, 9999), depth=(0, 1),
         samples=[(0.4, 0.18), (0.45, 0.53), (0.5, 0.86)],
         face=(0.4, 0.3, 1.3), roar=0.2, bubbles=0,
         hab=dict(kind="forest", theme="dover", night=True, w=6000, h=H, dark_top=150, dark_bot=230, dark_col=(2, 3, 12),
                  decoys=[("cat", 2), ("raccoon", 3)]),
         story=["בלילה של 21 באפריל 1977 נסע ביל ברטלט, נער בן 17, עם חברים ברחוב פארם בעיירה דובר שבמסצ'וסטס. "
                "פתאום אורות המכונית האירו יצור מוזר שעמד על חומת אבנים נמוכה.",
                "ליצור היה ראש ענק בצורת אבטיח, עיניים כתומות שזוהרות, גוף רזה בצבע ורוד-בהיר ואצבעות ארוכות "
                "ודקות. גובהו היה בערך מטר. באותו לילה ובלילה שאחריו עוד שני נערים סיפרו שראו אותו!",
                "ביל צייר אותו וכתב מתחת: 'אני נשבע שראיתי את היצור הזה'. המשטרה חשבה שזו מתיחה, אבל עד היום "
                "אף אחד לא יודע מה הם ראו. חפש לאורך חומות האבנים..."],
         tip="השד מדובר קטן ומהיר. חפש את העיניים הכתומות הזוהרות בחושך - אבל גם לחתולים ולדביבונים יש עיניים זוהרות!",
         fact="ידעת? השד מדובר נראה רק במשך יומיים, ב-21 וב-22 באפריל 1977 - ומאז אף אחד לא ראה אותו שוב."),
]
MON_BY_KEY = {m["key"]: m for m in MONSTERS}

DECOYS = {
    "whale": dict(name="לוויתן גבנון", painter=paint_whale, size=(420, 190), k=1.0, n=8, anim=3, speed=70,
                  depth=(0.1, 0.8), msg="זה סתם לוויתן גבנון! ענק ויפה, אבל לא מפלצת.", beh="roam"),
    "sperm": dict(name="לוויתן זרע", painter=lambda c, t: paint_whale(c, t, True), size=(420, 190), k=1.1, n=8,
                  anim=3, speed=65, depth=(0.2, 1.0), msg="לוויתן זרע! הוא צולל עמוק מאוד - אבל זה לא בלופ.", beh="roam"),
    "shark": dict(name="כריש", painter=paint_shark, size=(320, 130), k=1.0, n=8, anim=5, speed=120,
                  depth=(0.1, 0.95), msg="כריש! מפחיד... אבל זה לא מה שחיפשנו.", beh="roam"),
    "seal": dict(name="כלב ים נמרי", painter=paint_seal, size=(230, 110), k=1.0, n=8, anim=5, speed=130,
                 depth=(0.0, 0.6), msg="כלב ים נמרי! הוא רק סקרן לגבי הצוללת.", beh="roam"),
    "log": dict(name="בול עץ", painter=paint_log, size=(400, 90), k=1.0, n=1, anim=0, speed=14,
                depth=(0.0, 0.5), msg="זה בול עץ שוקע... ככה נוצרות הרבה תצפיות מזויפות!", beh="drift"),
    "sturgeon": dict(name="חדקן", painter=paint_sturgeon, size=(320, 110), k=1.15, n=8, anim=5, speed=60,
                     depth=(0.5, 1.0), msg="חדקן ענק! יש שחושבים שאנשים מתבלבלים בינו לבין מפלצות אגם.", beh="roam"),
    "otters": dict(name="לוטרות", painter=paint_otters, size=(300, 80), k=1.0, n=8, anim=6, speed=95,
                   depth=(0.0, 0.12), msg="שלוש לוטרות בשורה - מרחוק הן נראות כמו דבשות של נחש!", beh="roam"),
    "eel": dict(name="צלופח", painter=paint_eel, size=(380, 90), k=1.15, n=8, anim=6, speed=70,
                depth=(0.5, 1.0), msg="צלופח ענק! יש מדענים שחושבים שנסי היא בעצם צלופח.", beh="roam"),
    "deer": dict(name="צבי", painter=paint_deer, size=(210, 200), k=0.85, n=8, anim=0, speed=60,
                 msg="צבי! הוא נבהל וברח לו.", beh="flee"),
    "bear": dict(name="דוב חום", painter=paint_bear, size=(260, 190), k=0.95, n=8, anim=0, speed=45,
                 msg="דוב חום! הוא לא ביגפוט - ועדיף לא להתקרב אליו...", beh="bear"),
    "costume": dict(name="אדם בתחפושת", painter=lambda c, t: paint_bigfoot(c, t, True), size=(230, 320), k=0.8,
                    n=12, anim=0, speed=50, msg="חחח! זה סתם בן אדם בתחפושת של ביגפוט!", beh="roam"),
    "camel": dict(name="גמל דו-דבשתי", painter=paint_camel, size=(300, 265), k=0.85, n=8, anim=0, speed=40,
                  msg="גמל דו-דבשתי! הוא סתם מחפש צל.", beh="roam"),
    "snake": dict(name="נחש חול", painter=paint_snake, size=(280, 70), k=1.0, n=8, anim=0, speed=50,
                  msg="נחש חול טטרי! יש מדענים שחושבים שהוא בעצם 'תולעת המוות' האמיתית.", beh="bear"),
    "cat": dict(name="חתול", painter=paint_cat, size=(130, 100), k=1.0, n=8, anim=0, speed=60,
                msg="חתול שחור! העיניים שלו זוהרות בחושך - אבל זה רק חתול.", beh="flee"),
    "raccoon": dict(name="דביבון", painter=paint_raccoon, size=(160, 100), k=1.0, n=8, anim=0, speed=45,
                    msg="דביבון! הוא בא לחפש אוכל בפחי האשפה.", beh="roam"),
    "ghost": dict(name="ילד מחופש", painter=paint_ghost, size=(150, 245), k=0.8, n=8, anim=0, speed=45,
                  msg="חחח! זה סתם ילד מחופש לרוח רפאים עם סדין!", beh="roam"),
    "wolf": dict(name="זאב", painter=paint_wolf, size=(240, 150), k=1.0, n=8, anim=0, speed=70,
                 msg="זאב! העיניים שלו זהרו בחושך... אבל הוא לא הוונדיגו.", beh="bear"),
}

# ======================================================================= סאונד


class Sounds:
    def __init__(self):
        self.s = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            R, _, ch = pygame.mixer.get_init()
            pygame.mixer.set_num_channels(24)
        except Exception:
            return
        rng = np.random.default_rng(3)

        def mk(x, vol=1.0):
            a = (np.clip(x, -1, 1) * 26000 * vol).astype(np.int16)
            if ch > 1:
                a = np.repeat(a[:, None], ch, axis=1)
            return pygame.sndarray.make_sound(np.ascontiguousarray(a))

        def tt(sec):
            return np.arange(int(R * sec)) / R

        def tone(sec, f0, f1):
            f = np.linspace(f0, f1, int(R * sec))
            return np.sin(np.cumsum(f) * TAU / R)

        def lowpass(x, n):
            return np.convolve(x, np.ones(n) / n, mode="same")

        def noise(sec):
            return rng.uniform(-1, 1, int(R * sec))

        t = tt(1.3)
        ping = np.sin(TAU * 1250 * t) * np.exp(-t * 6)
        for d, a in ((0.38, 0.35), (0.76, 0.12)):
            k = int(d * R)
            ping[k:] += np.sin(TAU * 1250 * t[:-k]) * np.exp(-t[:-k] * 9) * a
        t = tt(0.07)
        beep = np.sin(TAU * 1600 * t) * np.sin(np.linspace(0, math.pi, len(t)))
        n = noise(0.16)
        sh = np.zeros_like(n)
        sh[:int(R * 0.025)] = 1
        sh[int(R * 0.07):int(R * 0.12)] = np.linspace(1, 0, int(R * 0.12) - int(R * 0.07))
        shutter = np.diff(n, prepend=0) * sh * 0.5
        t = tt(2.0)
        f = np.linspace(48, 30, len(t))
        saw = ((np.cumsum(f) / R) % 1) * 2 - 1
        roar = lowpass(saw * 0.7 + noise(2.0)[:len(t)] * 0.5, 30) * np.sin(np.linspace(0, math.pi, len(t))) ** 0.6 * 2.4
        notes = [523, 659, 784, 1047]
        win = np.concatenate([(np.sin(TAU * fq * tt(0.16)) + 0.3 * np.sin(TAU * 2 * fq * tt(0.16)))
                              * np.exp(-tt(0.16) * 6) for fq in notes] +
                             [(np.sin(TAU * 1047 * tt(0.6)) + 0.3 * np.sin(TAU * 1568 * tt(0.6))) * np.exp(-tt(0.6) * 4)]) * 0.5
        fail = np.concatenate([np.sin(TAU * fq * tt(0.25)) * np.exp(-tt(0.25) * 4) for fq in (440, 370, 311, 262)]) * 0.5
        pick = tone(0.22, 600, 1300) * np.exp(-tt(0.22) * 8) * 0.6
        click = noise(0.03) * np.linspace(1, 0, int(R * 0.03)) * 0.4
        # פעימת לב
        t = tt(0.55)
        heart = np.zeros_like(t)
        for d, a in ((0.0, 1.0), (0.2, 0.7)):
            m = t >= d
            tt2 = t[m] - d
            heart[m] += np.sin(TAU * 52 * tt2) * np.exp(-tt2 * 22) * a
        heart = lowpass(heart, 8) * 1.6
        # יבבה מאיימת מהמעמקים
        t = tt(3.2)
        fq = 120 + 50 * np.sin(np.linspace(0, math.pi * 1.5, len(t))) + 6 * np.sin(TAU * 5 * t)
        ph = np.cumsum(fq) * TAU / R
        moan = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3.01 * ph)) * np.sin(np.linspace(0, math.pi, len(t))) ** 1.5 * 0.5
        # צעקה של קפיצת בהלה
        t = tt(1.3)
        sting = (np.sin(TAU * 880 * t) + np.sin(TAU * 932 * t) + np.sin(TAU * 1245 * t) + noise(1.3)[:len(t)] * 0.8) \
            * np.exp(-t * 2.5) * 0.4
        # דפיקה על עץ
        kn = np.zeros(int(R * 0.6))
        for d in (0.0, 0.33):
            k = int(d * R)
            m = int(R * 0.09)
            seg = (lowpass(noise(0.09), 6) * 1.5 + np.sin(TAU * 260 * tt(0.09))) * np.exp(-tt(0.09) * 45)
            kn[k:k + m] += seg[:len(kn[k:k + m])]
        snap = np.diff(noise(0.07), prepend=0) * np.exp(-tt(0.07) * 60) * 0.8
        bird = np.concatenate([tone(0.07, 3000, 4600) * np.sin(np.linspace(0, math.pi, int(R * 0.07))) * 0.3
                               for _ in range(3)] + [np.zeros(int(R * 0.05))])
        splash = lowpass(noise(0.7), 4) * np.exp(-tt(0.7) * 6) * 0.7
        t = tt(1.0)
        growl = (((np.cumsum(np.full(len(t), 85.0)) / R) % 1) * 2 - 1) * (0.6 + 0.4 * np.sin(TAU * 7 * t)) \
            * np.sin(np.linspace(0, math.pi, len(t))) * 0.6
        growl = lowpass(growl + noise(1.0)[:len(t)] * 0.3, 12) * 1.5
        sec = 6.0
        br = np.cumsum(noise(sec))
        br = lowpass(br - lowpass(br, 4000), 60)
        br = br / (np.abs(br).max() + 1e-6)
        fade = np.ones_like(br)
        m = int(R * 0.4)
        fade[:m] = np.linspace(0, 1, m)
        fade[-m:] = np.linspace(1, 0, m)
        water = br * fade * 0.6
        tf = tt(sec)
        wind = lowpass(noise(sec), 30)[:len(tf)] * (0.5 + 0.5 * np.sin(TAU * 0.25 * tf)) * 1.6
        forest = wind * fade * 0.4
        self.s = dict(ping=mk(ping, 0.8), beep=mk(beep, 0.35), shutter=mk(shutter), roar=mk(roar),
                      win=mk(win), fail=mk(fail), pickup=mk(pick), click=mk(click), heart=mk(heart),
                      moan=mk(moan), sting=mk(sting), knock=mk(kn), snap=mk(snap), bird=mk(bird),
                      splash=mk(splash), growl=mk(growl),
                      amb_water=mk(water, 0.5), amb_forest=mk(forest, 0.6))

    def play(self, name, vol=1.0):
        s = self.s.get(name)
        if s:
            c = s.play()
            if c:
                c.set_volume(clamp(vol, 0, 1))

    def loop(self, name):
        self.stop_loops()
        s = self.s.get(name)
        if s:
            c = s.play(loops=-1)
            if c:
                c.set_volume(0.5)

    def stop_loops(self):
        for k in ("amb_water", "amb_forest"):
            if k in self.s:
                self.s[k].stop()


# ======================================================================= סביבת המחייה


def pine(surf, x, base, h, col, trunk=None, snow=False):
    tw = max(3, h * 0.045)
    pygame.draw.rect(surf, trunk or mul(col, 0.8), (x - tw / 2, base - h * 0.3, tw, h * 0.3 + 4))
    for i in range(6):
        k = i / 6
        y = base - h * 0.22 - k * h * 0.78
        hw = h * 0.24 * (1 - k * 0.8)
        pygame.draw.polygon(surf, mul(col, 0.9 + 0.25 * k), [(x - hw, y), (x + hw, y), (x, y - h * 0.24)])
        if snow:
            sc = mix(col, (225, 232, 245), 0.75)
            pygame.draw.polygon(surf, sc, [(x - hw * 0.55, y - h * 0.11), (x + hw * 0.55, y - h * 0.11), (x, y - h * 0.24)])


def round_tree(surf, x, base, h, col, rr, trunk=None):
    tc = trunk or mul(col, 0.7)
    tw = max(4, h * 0.06)
    pygame.draw.rect(surf, tc, (x - tw / 2, base - h * 0.55, tw, h * 0.55 + 4))
    for k in range(4):
        a = -math.pi / 2 + rr.uniform(-0.9, 0.9)
        pygame.draw.line(surf, tc, (x, base - h * (0.4 + k * 0.08)),
                         (x + math.cos(a) * h * 0.25, base - h * (0.4 + k * 0.08) + math.sin(a) * h * 0.2), max(2, int(tw * 0.4)))
    for _ in range(7):
        pygame.draw.circle(surf, mul(col, rr.uniform(0.85, 1.2)),
                           (int(x + rr.uniform(-h * 0.22, h * 0.22)), int(base - h * rr.uniform(0.6, 0.95))), int(h * rr.uniform(0.12, 0.2)))


def dry_shrub(surf, x, base, h, col, rr):
    for _ in range(14):
        a = -math.pi / 2 + rr.uniform(-1.1, 1.1)
        L = h * rr.uniform(0.5, 1.0)
        ex, ey = x + math.cos(a) * L, base + math.sin(a) * L
        pygame.draw.line(surf, col, (x, base), (ex, ey), 2)
        pygame.draw.circle(surf, mul(col, 1.2), (int(ex), int(ey)), 3)


THEMES = {
    "forest_day": dict(ground_y=592, hill=26, sky=((80, 150, 230), (210, 232, 245)), sun=(690, 105, 190, (70, 65, 30)),
                       clouds=60, layers=[(0.12, "ridge", (125, 155, 185), 430, None), (0.3, "pines", (85, 130, 125), 520, (200, 330)),
                                          (0.6, "pines", (50, 95, 65), 565, (260, 440))],
                       main="pines", main_col=(30, 72, 42), trunk=(84, 58, 38), ground=((86, 128, 52), (60, 90, 36)),
                       grass=1600, grass_cols=[(70, 120, 45), (110, 160, 60), (60, 100, 40)], flowers=140, rocks=50,
                       rock=(0.45, 0.45, 0.45), bush="green", bush_gap=(260, 520),
                       fore_trunks=((52, 36, 24), (24, 58, 30)), fore_bush=(30, 62, 30), butterflies=True),
    "desert": dict(ground_y=600, hill=40, sky=((95, 160, 225), (250, 222, 165)), sun=(690, 90, 230, (90, 70, 25)),
                   layers=[(0.15, "ridge", (190, 150, 120), 470, None), (0.35, "dunes", (215, 170, 110), 540, None),
                           (0.6, "dunes", (228, 182, 118), 585, None)],
                   main="saxaul", main_col=(110, 85, 55), trunk=None, ground=((228, 188, 125), (200, 155, 95)),
                   ripples=True, rocks=35, rock=(0.62, 0.42, 0.28), bush="dry", bush_gap=(500, 900),
                   fore_bush=None),
    "town": dict(ground_y=600, hill=6, night=True, sky=((4, 6, 22), (34, 32, 62)), moon=(420, 140), stars=True,
                 layers=[(0.3, "houses", (24, 28, 44), 545, None), (0.6, "trees", (16, 24, 28), 575, (180, 300))],
                 main="town", main_col=(20, 30, 25), trunk=None, ground=((34, 58, 34), (24, 34, 24)),
                 grass=900, grass_cols=[(40, 70, 40), (30, 55, 30)], rocks=0, bush="hedge", bush_gap=(320, 600),
                 fore_trunks=((14, 12, 12), None), fore_bush=(12, 22, 14), rec=True),
    "snow": dict(ground_y=595, hill=24, night=True, sky=((6, 10, 30), (46, 52, 80)), moon=(1000, 230), stars=True,
                 layers=[(0.12, "ridge", (55, 65, 92), 440, None), (0.3, "pines", (32, 42, 58), 525, (200, 330)),
                         (0.6, "pines", (22, 30, 40), 568, (260, 440))], snowy=True, snowcaps=True,
                 main="pines", main_col=(22, 45, 35), trunk=(50, 38, 30), ground=((215, 225, 238), (175, 185, 205)),
                 rocks=30, rock=(0.5, 0.52, 0.56), bush="snow", bush_gap=(300, 600),
                 fore_trunks=((20, 16, 14), None), fore_bush=(200, 210, 225), snowfall=True),
    "dover": dict(ground_y=598, hill=14, night=True, sky=((6, 8, 28), (40, 38, 58)), moon=(760, 120), stars=True,
                  layers=[(0.3, "trees", (22, 28, 42), 540, (150, 260)), (0.6, "trees", (14, 20, 26), 572, (220, 340))],
                  main="trees", main_col=(26, 40, 28), trunk=(40, 32, 26), ground=((44, 58, 36), (26, 34, 22)),
                  grass=1000, grass_cols=[(50, 72, 40), (36, 55, 30)], rocks=30, rock=(0.45, 0.45, 0.43),
                  bush="green", bush_gap=(360, 700), wall=True, fore_trunks=((14, 12, 10), None), fore_bush=(14, 22, 14)),
}


class Habitat:
    def __init__(self, cfg, seed):
        self.cfg = cfg
        self.kind = cfg["kind"]
        self.w, self.h = cfg["w"], cfg["h"]
        self.surface = cfg.get("surface")
        rng = np.random.default_rng(seed)
        self.vents, self.kelp, self.bushes = [], [], []
        if self.kind == "forest":
            self.build_forest(rng)
        else:
            self.build_water(rng)
        y = np.arange(self.h, dtype=F32)
        top = self.surface or 0
        t = np.clip((y - top) / (self.h - top), 0, 1) ** 0.8
        prof = cfg["dark_top"] + (cfg["dark_bot"] - cfg["dark_top"]) * t
        if self.surface:
            prof = np.where(y < self.surface, cfg.get("dark_sky", 0), prof)
        self.dark = prof.astype(F32)
        self.floor = [float(v) for v in self.floor]
        self.ceil = [float(v) for v in self.ceil]
        self.kelp = [(float(a), float(b), float(c), float(d), e) for a, b, c, d, e in self.kelp]
        self.vents = [(float(a), float(b)) for a, b in self.vents]

    # ------------------------------------------------------------ מים
    def build_water(self, rng):
        c, w, h = self.cfg, self.w, self.h
        xs = np.arange(w, dtype=F32)
        floor = h - c["floor_base"] - c["floor_amp"] * (0.75 * line_noise(w, 7, rng) + 0.25 * line_noise(w, 40, rng))
        if c.get("ice"):
            ceil = 45 + 50 * line_noise(w, 40, rng)
            for _ in range(10):
                cx = rng.uniform(900, w - 200)
                ceil += rng.uniform(160, 420) * np.exp(-((xs - cx) / rng.uniform(60, 170)) ** 2)
            ceil += 25 * line_noise(w, 300, rng)
        elif self.surface:
            ceil = np.full(w, self.surface + 16, F32)
        else:
            ceil = np.full(w, 26.0, F32)
        if c.get("island"):
            ix = w * 0.62
            floor = np.minimum(floor, (self.surface + 300) + (h - self.surface) * np.clip(np.abs(xs - ix) / 700, 0, 1) ** 1.5)
        floor = np.clip(np.maximum(floor, ceil + 420), 0, h - 30)
        self.floor, self.ceil = floor.astype(F32), ceil.astype(F32)

        q = 2
        lw, lh = w // q, h // q
        Y = (np.arange(lh, dtype=F32) * q)[None, :]
        n = fbm(lw, lh, lw // 140 + 2, lh // 140 + 2, rng, 5)[..., None]
        top = self.surface or 0
        tt = (np.clip((Y - top) / (h - top), 0, 1) ** 0.75)[..., None]
        tc, bc = np.array(c["top_col"], F32), np.array(c["bot_col"], F32)
        col = (tc * (1 - tt) + bc * tt) * (0.88 + 0.24 * n)
        fl = self.floor[::q][:lw][:, None]
        n2 = fbm(lw, lh, lw // 50 + 2, lh // 50 + 2, rng, 5)[..., None]
        depth = np.clip((Y - fl) / 260, 0, 1)[..., None]
        rock = np.array(c["floor_col"], F32) * (0.45 + 0.9 * n2) * (1 - 0.45 * depth)
        rim = np.clip(1 - (Y - fl) / 16, 0, 1)[..., None]
        rock = rock * (1 - rim) + np.array(c["sand_col"], F32) * (0.8 + 0.4 * n2) * rim
        col = np.where((Y > fl)[..., None], rock, col)
        if c.get("ice"):
            cl = self.ceil[::q][:lw][:, None]
            n3 = fbm(lw, lh, lw // 60 + 2, lh // 60 + 2, rng, 4)[..., None]
            ice = np.array([150, 185, 215], F32) * (0.7 + 0.45 * n3)
            edge = np.clip(1 - (cl - Y) / 14, 0, 1)[..., None]
            ice = ice * (1 - edge) + np.array([225, 245, 255], F32) * edge
            col = np.where((Y < cl)[..., None], ice, col)
        if self.surface:
            sy = self.surface
            st = np.clip(Y / sy, 0, 1)[..., None]
            sky = np.array(c["sky_top"], F32) * (1 - st) + np.array(c["sky_hor"], F32) * st
            mline = sy - 25 - 150 * (0.7 * line_noise(lw, 6, rng) + 0.3 * line_noise(lw, 30, rng))[:, None]
            mcol = np.array(c["mount"], F32) * (0.8 + 0.35 * n2) * (0.85 + 0.3 * np.clip((Y - mline) / 80, 0, 1)[..., None])
            sky = np.where(((Y > mline) & (Y < sy))[..., None], mcol, sky)
            col = np.where((Y < sy)[..., None], sky, col)
        arr = np.clip(col, 0, 255).astype(np.uint8)
        self.bg = pygame.transform.smoothscale(pygame.surfarray.make_surface(arr), (w, h)).convert()
        bg = self.bg
        self.floor = [float(v) for v in self.floor]
        rr = random.Random(int(rng.integers(1e9)))
        for _ in range(c.get("rocks", 0)):
            x = rr.uniform(100, w - 100)
            y = self.floor[int(x)]
            rx = rr.uniform(25, 90)
            cv = Canvas(rx * 2.2, rx * 1.4, 1.0, rim=(0.1, 0.15, 0.22))
            cv.ellipsoid(rx * 1.1, rx * 0.75, rx, rx * rr.uniform(0.45, 0.65), fmul([v / 255 for v in c["floor_col"]], rr.uniform(1.0, 1.6)),
                         spec=0.15, tex=0.5, fine=0.5)
            rs, _g = cv.surfaces()
            bg.blit(rs, (x - rx * 1.1, y - rx * 0.6))
        if c.get("island"):
            ix, sy = w * 0.62, self.surface
            pts = [(ix - 420, sy + 4)] + [(ix + k * 420, sy - 120 * (1 - k * k) ** 0.7) for k in np.linspace(-1, 1, 30)] + [(ix + 420, sy + 4)]
            pygame.draw.polygon(bg, (70, 85, 60), pts)
            for k in np.linspace(-0.8, 0.8, 16):
                pine(bg, ix + k * 420 + rr.uniform(-15, 15), sy - 112 * (1 - k * k) ** 0.7 + 8, rr.uniform(50, 90), (35, 60, 40))
        if c.get("castle"):
            cx, sy = w * 0.3, self.surface
            pygame.draw.polygon(bg, (50, 70, 45), [(cx - 300, sy + 2), (cx - 120, sy - 60), (cx + 140, sy - 58), (cx + 320, sy + 2)])
            stone = (88, 84, 78)
            pygame.draw.rect(bg, stone, (cx - 30, sy - 170, 70, 115))
            for i in range(4):
                pygame.draw.rect(bg, stone, (cx - 30 + i * 20, sy - 182, 12, 14))
            pygame.draw.rect(bg, mul(stone, 0.9), (cx - 110, sy - 95, 80, 40))
            pygame.draw.rect(bg, mul(stone, 0.9), (cx + 40, sy - 110, 60, 55))
            for wx, wy in ((cx - 10, sy - 150), (cx + 14, sy - 150), (cx + 2, sy - 115)):
                pygame.draw.rect(bg, (30, 28, 26), (wx, wy, 8, 16))
        if c.get("wreck"):
            self.wreck_x = wx = w * 0.7
            fy = self.floor[int(wx)]
            wood = (78, 56, 38)
            hull = [(wx - 330, fy - 120), (wx + 300, fy - 175), (wx + 350, fy - 150), (wx + 260, fy - 30),
                    (wx - 250, fy + 10), (wx - 330, fy - 60)]
            pygame.draw.polygon(bg, wood, hull)
            for i in range(7):
                y0 = fy - 110 + i * 18 - i * 3
                pygame.draw.line(bg, mul(wood, 0.7), (wx - 320, y0 - i * 2), (wx + 320, y0 - 50 + i * 4), 3)
            pygame.draw.polygon(bg, (25, 18, 14), [(wx - 60, fy - 90), (wx + 40, fy - 120), (wx + 70, fy - 60), (wx - 30, fy - 30)])
            pygame.draw.line(bg, mul(wood, 0.9), (wx - 40, fy - 140), (wx - 140, fy - 470), 14)
            pygame.draw.line(bg, mul(wood, 0.9), (wx - 100, fy - 340), (wx + 20, fy - 370), 8)
            pygame.draw.line(bg, mul(wood, 0.9), (wx + 180, fy - 160), (wx + 230, fy - 330), 10)
            for i in range(5):
                pygame.draw.circle(bg, (20, 15, 12), (wx - 200 + i * 90, fy - 80 - i * 10), 10)
            for i in range(3):
                bx = wx - 150 + i * 120
                pygame.draw.circle(bg, (200, 190, 170), (bx, fy - 5), 9)
                pygame.draw.circle(bg, (20, 15, 12), (bx - 3, fy - 7), 2)
                pygame.draw.circle(bg, (20, 15, 12), (bx + 3, fy - 7), 2)
        for i in range(c.get("vents", 0)):
            x = w * (0.35 + 0.15 * i) + rr.uniform(-100, 100)
            fy = self.floor[int(x)]
            hh = rr.uniform(120, 220)
            pygame.draw.polygon(bg, (35, 30, 30), [(x - 45, fy + 20), (x - 14, fy - hh), (x + 14, fy - hh), (x + 50, fy + 20)])
            pygame.draw.polygon(bg, (60, 40, 30), [(x - 14, fy - hh), (x + 14, fy - hh), (x + 8, fy - hh + 30), (x - 8, fy - hh + 30)])
            self.vents.append((x, fy - hh))
        for _ in range(c.get("kelp", 0)):
            x = rr.uniform(150, w - 150)
            self.kelp.append((x, self.floor[int(x)] + 6, rr.uniform(120, 340), rr.uniform(0, TAU),
                              mix((40, 110, 40), (90, 120, 40), rr.random())))

    # ------------------------------------------------------------ יבשה (יער, מדבר, שכונה, שלג)
    def build_forest(self, rng):
        th = THEMES[self.cfg.get("theme", "forest_day")]
        self.theme = th
        w = self.w
        rr = random.Random(int(rng.integers(1e9)))
        gy = th["ground_y"]
        self.floor = [float(v) for v in gy + th["hill"] * line_noise(w, 22, rng)]
        self.ceil = [0.0] * w
        self.lamps, self.windows = [], []
        sky = pygame.Surface((W, H))
        st, sb = th["sky"]
        for y in range(H):
            pygame.draw.line(sky, mix(st, sb, y / (H * 0.75)), (0, y), (W, y))
        if th.get("stars"):
            for _ in range(260):
                c = rr.randint(120, 255)
                sky.set_at((rr.randrange(W), rr.randrange(int(H * 0.65))), (c, c, c))
        if th.get("sun"):
            sx, sy, gr, gc = th["sun"]
            add_glow(sky, sx, sy, gr, gc)
            pygame.draw.circle(sky, (255, 250, 220), (sx, sy), 40)
        if th.get("moon"):
            mx, my = th["moon"]
            add_glow(sky, mx, my, 120, (40, 40, 45))
            pygame.draw.circle(sky, (235, 235, 215), (mx, my), 36)
            pygame.draw.circle(sky, (205, 205, 190), (mx + 12, my - 8), 7)
            pygame.draw.circle(sky, (210, 210, 195), (mx - 10, my + 10), 5)
        if th.get("clouds"):
            for _ in range(9):
                cl = pygame.Surface((300, 120), SRCALPHA)
                for _k in range(9):
                    pygame.draw.ellipse(cl, (255, 255, 255, th["clouds"]), (rr.uniform(0, 160), rr.uniform(20, 70), rr.uniform(90, 140), rr.uniform(35, 55)))
                sky.blit(cl, (rr.uniform(-100, W), rr.uniform(10, 230)))
        self.sky = sky
        self.layers = []
        for par, kind, col, base, hr in th["layers"]:
            lw = int(w * par) + W
            s = pygame.Surface((lw, H))
            s.fill(KEY)
            if kind in ("ridge", "dunes"):
                cells = max(4, lw // (500 if kind == "ridge" else 900))
                ridge = line_noise(lw, cells, rng, 3 if kind == "ridge" else 1)
                amp = 200 if kind == "ridge" else 90
                pts = [(0, H)] + [(x, float(base - amp * ridge[x])) for x in range(0, lw, 8)] + [(lw, H)]
                pygame.draw.polygon(s, col, pts)
                if kind == "dunes":
                    pygame.draw.lines(s, mix(col, (255, 240, 200), 0.35), False, pts[1:-1], 3)
                if th.get("snowcaps") and kind == "ridge":
                    pygame.draw.lines(s, (200, 210, 230), False, pts[1:-1], 4)
            else:
                pygame.draw.rect(s, col, (0, base, lw, H - base))
                x = 0
                while x < lw:
                    if kind == "pines":
                        pine(s, x, base + 6, rr.uniform(*hr), col, snow=th.get("snowy"))
                        x += rr.uniform(25, 70) * hr[0] / 260
                    elif kind == "trees":
                        round_tree(s, x, base + 6, rr.uniform(*hr), col, rr)
                        x += rr.uniform(60, 140)
                    elif kind == "houses":
                        hw, hh = rr.uniform(140, 230), rr.uniform(80, 130)
                        pygame.draw.rect(s, col, (x, base - hh, hw, hh + 6))
                        pygame.draw.polygon(s, col, [(x - 12, base - hh), (x + hw / 2, base - hh - rr.uniform(40, 70)), (x + hw + 12, base - hh)])
                        for i in range(int(hw // 50)):
                            wx_, wy_ = x + 18 + i * 50, base - hh + 26
                            if rr.random() < 0.45:
                                self.windows.append((par, wx_, wy_, 22, 26))
                            else:
                                pygame.draw.rect(s, mul(col, 0.6), (wx_, wy_, 22, 26))
                        x += hw + rr.uniform(40, 140)
            s.set_colorkey(KEY, pygame.RLEACCEL)
            self.layers.append((par, s))
        g = pygame.Surface((w, H))
        g.fill(KEY)
        main = th["main"]
        x = rr.uniform(0, 200)
        while x < w:
            fy = self.floor[int(x)]
            if main == "pines":
                pine(g, x, fy + 8, rr.uniform(360, 560), th["main_col"], trunk=th["trunk"], snow=th.get("snowy"))
                x += rr.uniform(160, 360)
            elif main == "trees":
                round_tree(g, x, fy + 8, rr.uniform(300, 460), th["main_col"], rr, trunk=th["trunk"])
                x += rr.uniform(260, 520)
            elif main == "saxaul":
                dry_shrub(g, x, fy + 4, rr.uniform(50, 110), th["main_col"], rr)
                x += rr.uniform(300, 700)
            elif main == "town":
                pygame.draw.rect(g, (40, 32, 28), (x, fy - 120, w, 0))
                pygame.draw.rect(g, (55, 45, 38), (x - 4, fy - 110, 8, 112))
                for k in range(16):
                    pygame.draw.rect(g, (62, 50, 42), (x + 6 + k * 22, fy - 100, 18, 102))
                pygame.draw.rect(g, (50, 42, 36), (x + 4, fy - 86, 360, 6))
                pygame.draw.rect(g, (50, 42, 36), (x + 4, fy - 40, 360, 6))
                lx = x + rr.uniform(420, 560)
                pygame.draw.rect(g, (45, 48, 55), (lx - 4, fy - 330, 8, 332))
                pygame.draw.rect(g, (45, 48, 55), (lx - 4, fy - 330, 46, 7))
                pygame.draw.rect(g, (230, 220, 170), (lx + 26, fy - 324, 18, 6))
                self.lamps.append((lx + 35, fy - 320))
                x += rr.uniform(800, 1100)
            else:
                x += 400
        if th.get("wall"):
            x = 0
            while x < w:
                seg = rr.uniform(500, 1200)
                xe = min(w - 1, x + seg)
                xx = x
                while xx < xe:
                    sw_ = rr.uniform(20, 38)
                    for row in range(3):
                        fy = self.floor[int(xx)]
                        sh_ = rr.uniform(14, 20)
                        pygame.draw.ellipse(g, mix((105, 105, 100), (70, 70, 68), rr.random()), (xx, fy - 18 - row * 15 - sh_ / 2, sw_, sh_))
                    xx += sw_ * 0.85
                x = xe + rr.uniform(250, 600)
        pts = [(0, H)] + [(x, self.floor[x]) for x in range(0, w, 10)] + [(w - 1, self.floor[-1]), (w, H)]
        gc, gc2 = th["ground"]
        pygame.draw.polygon(g, gc, pts)
        for y in range(0, 140, 6):
            pygame.draw.lines(g, mix(gc, gc2, y / 140), False, [(x, self.floor[x] + y) for x in range(0, w, 20)], 6)
        if th.get("ripples"):
            for _ in range(500):
                x = rr.uniform(0, w - 40)
                y = self.floor[int(x)] + rr.uniform(8, 120)
                pygame.draw.arc(g, mul(gc, 0.85), (x, y, rr.uniform(30, 70), 10), 0.3, 2.8, 2)
        for _ in range(th.get("grass", 0)):
            x = rr.uniform(0, w - 1)
            fy = self.floor[int(x)]
            pygame.draw.line(g, rr.choice(th["grass_cols"]), (x, fy + 2), (x + rr.uniform(-4, 4), fy - rr.uniform(6, 18)), 2)
        for _ in range(th.get("flowers", 0)):
            x = rr.uniform(0, w - 1)
            pygame.draw.circle(g, rr.choice([(240, 230, 90), (240, 240, 240), (200, 120, 220)]),
                               (int(x), int(self.floor[int(x)] - rr.uniform(2, 8))), 3)
        for _ in range(th.get("rocks", 0)):
            x = rr.uniform(0, w - 1)
            rx = rr.uniform(12, 34)
            cv = Canvas(rx * 2.4, rx * 1.5, 1.0, rim=DAY_RIM)
            cv.ellipsoid(rx * 1.2, rx * 0.8, rx, rx * 0.6, th["rock"], spec=0.15, tex=0.5)
            rs, _g = cv.surfaces()
            g.blit(rs, (x - rx * 1.2, self.floor[int(x)] - rx * 0.4))
        g.set_colorkey(KEY, pygame.RLEACCEL)
        self.bg = g
        bush_spr = []
        for sd in range(4):
            cv = Canvas(280, 170, 1.0, rim=DAY_RIM)
            paint_bush(cv, sd, th["bush"])
            bush_spr.append(cv.surfaces()[0])
        x = 500
        while x < w - 200:
            spr = rr.choice(bush_spr)
            k = rr.uniform(0.9, 1.15)
            if k != 1:
                spr = pygame.transform.smoothscale(spr, (int(280 * k), int(170 * k)))
            fy = self.floor[int(x)]
            self.bushes.append(dict(x=x, y=fy - 62 * k, rx=118 * k, ry=82 * k, spr=spr, top=fy - spr.get_height() + 14))
            x += rr.uniform(*th["bush_gap"])
        fw = int(w * 1.25) + W
        fore = pygame.Surface((fw, H))
        fore.fill(KEY)
        if th.get("fore_trunks"):
            tc, lc = th["fore_trunks"]
            x = rr.uniform(200, 500)
            while x < fw:
                tw = rr.uniform(40, 80)
                pygame.draw.rect(fore, tc, (x, -10, tw, H + 20))
                for k in range(3):
                    pygame.draw.line(fore, mul(tc, 0.7), (x + tw * (0.25 + k * 0.25), 0), (x + tw * (0.25 + k * 0.25), H), 3)
                pygame.draw.line(fore, mul(tc, 1.5), (x + 6, 0), (x + 6, H), 4)
                if lc:
                    for k in range(6):
                        pygame.draw.circle(fore, lc, (int(x + tw / 2 + rr.uniform(-110, 110)), int(rr.uniform(-30, 70))), int(rr.uniform(40, 70)))
                x += rr.uniform(800, 1500)
        if th.get("fore_bush"):
            x = 0
            while x < fw:
                for k in range(5):
                    pygame.draw.circle(fore, th["fore_bush"], (int(x + k * 24 + rr.uniform(-6, 6)), int(H - 6 - rr.uniform(0, 26))), int(rr.uniform(22, 38)))
                x += rr.uniform(400, 900)
        fore.set_colorkey(KEY, pygame.RLEACCEL)
        self.fore = fore

    def clamp_y(self, x, y, mt, mb):
        xi = int(clamp(x, 0, self.w - 1))
        lo, hi = self.ceil[xi] + mt, self.floor[xi] - mb
        if lo > hi:
            return (lo + hi) / 2
        return clamp(y, lo, hi)

    def occluded(self, x, y):
        for b in self.bushes:
            if abs(x - b["x"]) < b["rx"] and ((x - b["x"]) / b["rx"]) ** 2 + ((y - b["y"]) / b["ry"]) ** 2 < 1:
                return True
        return False

# ======================================================================= ישויות


class Creature:
    def __init__(self, bodies, glows, hab):
        self.hab = hab
        self.land = hab.kind == "forest"
        self.frames = bodies
        self.frames_l = [pygame.transform.flip(f, True, False) for f in bodies]
        self.glows = glows
        self.glows_l = [pygame.transform.flip(g, True, False) if g is not None else None for g in glows]
        self.w, self.h = bodies[0].get_size()
        self.facing = 1
        self.anim = 0.0
        self.vx = self.vy = 0.0
        self.x = self.y = 0.0

    def idx(self):
        if self.land and abs(self.vx) < 6:
            return 0
        return int(self.anim) % len(self.frames)

    def frame(self):
        return (self.frames if self.facing > 0 else self.frames_l)[self.idx()]

    def glow(self):
        return (self.glows if self.facing > 0 else self.glows_l)[self.idx()]

    def point(self, fx, fy):
        if self.facing < 0:
            fx = 1 - fx
        return self.x + (fx - 0.5) * self.w, self.y + (fy - 0.5) * self.h

    def ground_y(self, x=None):
        x = self.x if x is None else x
        return self.hab.floor[int(clamp(x, 0, self.hab.w - 1))] - self.h * 0.5 + 6

    def rand_y(self, x, depth, rng):
        xi = int(clamp(x, 0, self.hab.w - 1))
        lo, hi = self.hab.ceil[xi] + self.h * 0.3, self.hab.floor[xi] - self.h * 0.36
        return lo + (hi - lo) * rng.uniform(*depth) if hi > lo else (lo + hi) / 2

    def steer(self, dt, tx, ty, speed, acc=1.5):
        ex, ey = tx - self.x, ty - self.y
        ed = math.hypot(ex, ey)
        tvx = ex / ed * speed if ed > 1 and speed else 0.0
        tvy = ey / ed * speed if ed > 1 and speed and not self.land else 0.0
        k = min(1.0, dt * acc)
        self.vx += (tvx - self.vx) * k
        self.vy += (tvy - self.vy) * k
        self.x = clamp(self.x + self.vx * dt, 150, self.hab.w - 150)
        if self.land:
            self.y = self.ground_y()
        else:
            self.y = self.hab.clamp_y(self.x, self.y + self.vy * dt, self.h * 0.3, self.h * 0.36)
        if abs(self.vx) > 4:
            self.facing = 1 if self.vx > 0 else -1
        return ed


class Monster(Creature):
    def __init__(self, md, bodies, glows, hab, rng):
        super().__init__(bodies, glows, hab)
        self.md, self.rng = md, rng
        hx, hr = md["home"]
        self.xmin = clamp(hab.w * hx - hr, 300 + self.w * 0.5, hab.w - 200)
        self.xmax = clamp(hab.w * hx + hr, self.xmin + 10, hab.w - 200 - self.w * 0.3)
        self.xmin = max(self.xmin, hab.w * 0.55)
        self.x = rng.uniform(self.xmin, self.xmax)
        self.mode = md["mode"]
        self.y = self.ground_y() if self.land else self.rand_y(self.x, md["depth"], rng)
        self.facing = 1 if rng.random() < 0.5 else -1
        self.state, self.timer = "roam", 0.0
        self.tx, self.ty = self.x, self.y
        self.notice = 0.0
        self.alerted = False
        self.hunting = False
        self.froze_msg = False
        self.attack_cd = 4.0
        self.bub_t = self.step_d = 0.0
        self.knock_t = rng.uniform(8, 14)
        self.bird_t = 0.0
        self.hidden = False
        self.emerge = 1.0
        self.near_t = 0.0
        if self.mode == "burrower":
            self.state, self.timer, self.hidden, self.emerge = "under", rng.uniform(4, 8), True, 0.0
            self.y = self.ground_y()
        if self.mode == "hider" and hab.bushes:
            self.hide_at(self.nearest_bush(self.x))
        else:
            self.pick_target()

    # ------------------------------------------------ מטרות
    def nearest_bush(self, x, away_from=None, min_d=0):
        cands = [b for b in self.hab.bushes if self.xmin - 400 <= b["x"] <= self.xmax + 400]
        if away_from is not None:
            side = 1 if self.x > away_from else -1
            far = [b for b in cands if (b["x"] - self.x) * side > min_d]
            if not far:
                far = [b for b in cands if abs(b["x"] - away_from) > min_d] or cands
            return min(far, key=lambda b: abs(b["x"] - self.x - side * min_d))
        return min(cands, key=lambda b: abs(b["x"] - x))

    def hide_at(self, b):
        self.x, self.tx = b["x"], b["x"]
        self.y = self.ground_y()
        self.state, self.timer = "hide", self.rng.uniform(5, 9)
        self.vx = 0

    def pick_target(self, away_from=None):
        if away_from is not None:
            side = 1 if self.x > away_from else -1
            tx = self.x + side * self.rng.uniform(900, 1500)
            if tx < self.xmin or tx > self.xmax:
                tx = self.x - side * self.rng.uniform(900, 1500)
        else:
            tx = self.x + self.rng.uniform(-900, 900)
        self.tx = clamp(tx, self.xmin, self.xmax)
        self.ty = self.ground_y(self.tx) if self.land else self.rand_y(self.tx, self.md["depth"], self.rng)

    def respawn_far(self, px):
        side = -1 if self.rng.random() < 0.5 else 1
        x = px + side * self.rng.uniform(1600, 2200)
        if not (self.xmin - 600 < x < self.xmax + 600):
            x = px - side * self.rng.uniform(1600, 2200)
        self.x = clamp(x, 300, self.hab.w - 300)
        self.y = self.ground_y() if self.land else self.rand_y(self.x, self.md["depth"], self.rng)
        self.vx = self.vy = 0
        self.state, self.notice, self.alerted, self.hunting = "roam", 0.0, False, False
        if self.mode == "burrower":
            self.state, self.timer, self.hidden, self.emerge = "under", self.rng.uniform(5, 8), True, 0.0
        self.attack_cd = 12.0
        self.pick_target()

    # ------------------------------------------------ התנהגות
    def update(self, dt, g):
        p, md = g.player, self.md
        dx, dy = p.x - self.x, p.y - self.y
        dist = math.hypot(dx, dy)
        v, frac = g.visibility_of(self)
        lit = v > 0.32 and frac > 0
        self.attack_cd = max(0.0, self.attack_cd - dt)
        if self.mode == "hider":
            self.update_hider(dt, g, dist, frac)
            return
        if self.mode == "burrower":
            self.update_burrower(dt, g, dist)
            return
        if dist < 600 and lit:
            self.notice += dt
        else:
            self.notice = max(0.0, self.notice - dt * 0.5)
        if self.notice > 0.7 and not self.alerted:
            self.alerted = True
            g.snd.play("roar", clamp(1.3 - dist / 1500, 0.3, 1))
            g.shake = max(g.shake, md["roar"])
            if self.mode == "shy":
                g.say("המפלצת גילתה אותך! מהר - צלם לפני שהיא בורחת!", 2.5)
        speed, tx, ty, acc = md["speed"], self.tx, self.ty, 1.5
        if self.mode == "shy":
            if self.notice > 1.6 and self.state != "flee":
                self.state, self.timer = "flee", 5.0
                self.pick_target(away_from=p.x)
                g.snd.play("splash", 0.6)
        elif self.mode == "stalker":
            if not self.hunting and (self.alerted or dist < 950):
                self.hunting = True
                g.snd.play("moan", 0.8)
                g.say("משהו לבן זז בחושך... הוא מתקרב אליך!", 3)
            if self.hunting:
                if lit:
                    speed, acc = 0, 6
                    if not self.froze_msg:
                        self.froze_msg = True
                        g.say("הוא קופא כשהפנס עליו! אל תוריד ממנו את האור - צלם!", 3)
                else:
                    speed, tx, ty, acc = md["charge"], p.x, p.y, 2.5
        elif self.mode == "hunter":
            if (self.alerted or dist < 760) and self.attack_cd <= 0 and self.state != "charge":
                self.state, self.timer = "charge", 6.0
                g.snd.play("roar", 1.0)
                g.shake = max(g.shake, 0.8)
                g.say(f"{md['name']} שמע אותך! הוא תוקף - צלם וברח!", 3)
            if self.state == "charge":
                speed, tx, ty, acc = md["charge"], p.x, p.y, 2.2
                self.timer -= dt
                if self.timer <= 0:
                    self.state, self.attack_cd, self.alerted, self.notice = "roam", 9.0, False, 0.0
                    self.pick_target()
        elif self.mode == "ambush":
            if dist < 600 and self.attack_cd <= 0 and self.state not in ("charge", "flee"):
                self.state, self.timer = "charge", 2.6
                g.snd.play("roar", 1.0)
                g.say("הזרועות זזות! הקראקן זינק עליך!", 2.5)
            if self.state == "charge":
                speed, tx, ty, acc = md["charge"], p.x, p.y, 3.0
                self.timer -= dt
                if self.timer <= 0:
                    self.start_ink_flee(g)
        if self.state == "flee":
            speed = md["flee"]
            self.timer -= dt
            if self.timer <= 0:
                self.state, self.notice = "roam", 0.0
                self.pick_target()
        elif self.state == "idle":
            speed = 0 if not self.hunting else speed
            self.timer -= dt
            if self.timer <= 0:
                self.state = "roam"
                self.pick_target()
        ed = self.steer(dt, tx, ty, speed, acc)
        if ed < 30 and self.state in ("roam", "flee") and not self.hunting:
            if self.state == "flee":
                self.pick_target(away_from=p.x)
            elif self.rng.random() < 0.45:
                self.state, self.timer = "idle", self.rng.uniform(2, 5)
            else:
                self.pick_target()
        if self.land:
            self.anim += abs(self.vx) * dt / 22
        else:
            self.anim += dt * md["anim"] * (1 + 0.8 * (self.state in ("flee", "charge"))) * (0 if (self.hunting and speed == 0) else 1)
        # מגע = התקפה
        if self.mode in ("stalker", "hunter", "ambush") and self.attack_cd <= 0:
            fx, fy, _ = md["face"]
            hx, hy = self.point(fx, fy)
            hr = max(80.0, self.w * 0.14)
            if self.land:
                if abs(self.x - p.x) < max(60.0, self.w * 0.3):
                    g.monster_attack(self)
            elif math.hypot(hx - p.x, hy - p.y) < hr or (dist < self.w * 0.22 and not lit):
                g.monster_attack(self)
        if md["bubbles"]:
            self.bub_t -= dt
            if self.bub_t <= 0:
                self.bub_t = md["bubbles"] * self.rng.uniform(0.6, 1.4)
                fxo = self.facing * self.w * 0.28
                g.bubbles.append([self.x + fxo + self.rng.uniform(-40, 40), self.y - self.h * 0.2, self.rng.uniform(3, 9), 14.0])

    def update_burrower(self, dt, g, dist):
        p, md = g.player, self.md
        adx = abs(p.x - self.x)
        if self.state == "under":
            self.hidden, self.emerge = True, 0.0
            hunting = dist < 1200
            tx = p.x if hunting else self.tx
            ed = self.steer(dt, tx, self.y, md["speed"] * (1.0 if hunting else 0.6), 2)
            if not hunting and ed < 30:
                self.pick_target()
            if random.random() < dt * 14 * min(1, abs(self.vx) / 40 + 0.2):
                g.dust.append([self.x + random.uniform(-40, 40), self.hab.floor[int(self.x)], random.uniform(-40, 40),
                               random.uniform(-90, -30), 1.2])
            self.timer -= dt
            if (hunting and adx < 300) or self.timer <= 0:
                self.state, self.timer = "rise", 0.55
                self.vx = 0
                g.snd.play("roar", clamp(1.3 - dist / 1500, 0.3, 1))
                g.shake = max(g.shake, md["roar"] * (1 if dist < 900 else 0.3))
                for _ in range(40):
                    g.dust.append([self.x + random.uniform(-50, 50), self.hab.floor[int(self.x)], random.uniform(-160, 160),
                                   random.uniform(-320, -80), 1.4])
                if dist < 1100:
                    g.say("החול מתפוצץ! התולעת יוצאת!", 2)
        elif self.state == "rise":
            self.timer -= dt
            self.emerge = 1 - self.timer / 0.55
            self.hidden = self.emerge < 0.6
            if self.timer <= 0:
                self.state, self.timer, self.emerge, self.hidden = "up", self.rng.uniform(3.5, 5.5), 1.0, False
                self.near_t = 0.0
                if adx < 140 and self.attack_cd <= 0:
                    g.monster_attack(self)
                    return
        elif self.state == "up":
            self.timer -= dt
            self.anim += dt * md["anim"]
            self.facing = 1 if p.x > self.x else -1
            self.near_t = self.near_t + dt if adx < 260 else 0.0
            if self.near_t > 1.1 and self.attack_cd <= 0:
                g.say("היא יורקת רעל!", 1.5)
                g.monster_attack(self)
                return
            if self.timer <= 0:
                self.state, self.timer = "dive", 0.5
        elif self.state == "dive":
            self.timer -= dt
            self.emerge = self.timer / 0.5
            self.hidden = self.emerge < 0.6
            if self.timer <= 0:
                self.state, self.timer, self.hidden, self.emerge = "under", self.rng.uniform(4, 8), True, 0.0
                self.pick_target(away_from=p.x)
                g.snd.play("splash", 0.4)

    def start_ink_flee(self, g):
        self.state, self.timer = "flee", 5.0
        self.attack_cd = 12.0
        self.pick_target(away_from=g.player.x)
        g.spray_ink(self.x, self.y)

    def update_hider(self, dt, g, dist, frac):
        p, md = g.player, self.md
        running = g.running and abs(p.vx) > 40
        if dist < 400:
            self.notice += dt * 1.6
        elif running and dist < 1000:
            self.notice += dt * 1.3
        elif dist < 720 and frac >= 0.5 and abs(p.vx) > 40:
            self.notice += dt * 0.5
        else:
            self.notice = max(0.0, self.notice - dt * 0.4)
        if self.notice > 1.4 and self.state != "flee":
            self.state = "flee"
            b = self.nearest_bush(self.x, away_from=p.x, min_d=1100)
            self.tx = b["x"]
            self.notice = 0.0
            g.snd.play("snap", 1.0)
            g.snd.play("growl", 0.5)
            g.spawn_birds(self.x, 10)
            g.say("ביגפוט שמע אותך וברח! תתקרב בשקט יותר...", 3)
        if self.state == "hide":
            self.vx = 0
            self.timer -= dt
            self.knock_t -= dt
            if self.knock_t <= 0:
                self.knock_t = self.rng.uniform(14, 22)
                g.snd.play("knock", clamp(1.2 - dist / 3000, 0.25, 1))
                side = "מימין" if self.x > p.x else "משמאל"
                g.say(f"שמעת דפיקות על עץ... זה הגיע {side}!", 3)
            if self.timer <= 0:
                cands = [b for b in self.hab.bushes if 200 < abs(b["x"] - self.x) < 1400 and self.xmin - 400 <= b["x"] <= self.xmax + 400]
                b = self.rng.choice(cands) if cands else self.nearest_bush(self.x)
                self.tx = b["x"]
                self.state = "walk"
            return
        speed = md["flee"] if self.state == "flee" else md["speed"]
        ed = self.steer(dt, self.tx, self.y, speed, 3)
        self.anim += abs(self.vx) * dt / 22
        self.step_d += abs(self.vx) * dt
        if self.step_d > 70:
            self.step_d = 0
            g.footprints.append([self.x + self.rng.uniform(-6, 6), self.hab.floor[int(self.x)] + 4, self.facing, 120.0])
        self.bird_t -= dt
        if self.bird_t <= 0:
            self.bird_t = 2.5
            g.spawn_birds(self.x, 5)
        if abs(self.tx - self.x) < 12:
            self.hide_at(self.nearest_bush(self.x))
            if self.state == "hide":
                self.timer = self.rng.uniform(6, 11)
        _ = ed


class Critter(Creature):
    def __init__(self, kind, cfg, bodies, glows, hab, rng, xmin):
        super().__init__(bodies, glows, hab)
        self.kind, self.cfg, self.rng = kind, cfg, rng
        self.name, self.msg = cfg["name"], cfg["msg"]
        self.x = rng.uniform(xmin, hab.w - 250)
        self.depth = cfg.get("depth", (0, 1))
        self.y = self.ground_y() if self.land else self.rand_y(self.x, self.depth, rng)
        self.tx, self.ty = self.x, self.y
        self.timer = 0.0
        self.cd = 0.0
        self.samples = [(0.5, 0.5), (0.25, 0.5), (0.75, 0.45)]
        self.new_target()

    def new_target(self):
        self.tx = clamp(self.x + self.rng.uniform(-800, 800), 250, self.hab.w - 250)
        self.ty = self.ground_y(self.tx) if self.land else self.rand_y(self.tx, self.depth, self.rng)

    def update(self, dt, g):
        p = g.player
        beh, speed = self.cfg["beh"], self.cfg["speed"]
        dist = math.hypot(p.x - self.x, p.y - self.y)
        self.cd = max(0.0, self.cd - dt)
        if beh == "flee" and dist < 380 and self.timer <= 0:
            self.timer = 3.0
            self.tx = clamp(self.x + (1 if self.x > p.x else -1) * 900, 250, self.hab.w - 250)
            g.snd.play("snap", 0.6)
            g.spawn_birds(self.x, 4)
        if self.timer > 0:
            self.timer -= dt
            speed = 380
        if beh == "bear":
            self.warn = getattr(self, "warn", 0.0) - dt
            if dist < 340 and self.warn <= 0:
                self.warn = 8.0
                g.snd.play("growl", 0.7)
                g.say(f"זהירות, {self.name}! אל תעמוד לידו - תמשיך ללכת", 2.5)
            self.near = getattr(self, "near", 0.0)
            self.near = self.near + dt if (dist < 150 and abs(p.vx) < 70) else 0.0
            if self.near > 0.8 and self.cd <= 0:
                self.cd = 10.0
                self.near = 0.0
                g.critter_attack(self)
        if beh == "drift":
            speed = 14
        ed = self.steer(dt, self.tx, self.ty, speed, 1.2)
        if ed < 25:
            self.new_target()
        if self.land:
            self.anim += abs(self.vx) * dt / 16
        else:
            self.anim += dt * self.cfg["anim"]


class Player:
    def __init__(self, x, y, land):
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.facing = 1
        self.anim = 0.0
        self.land = land
        self.aim = 0.0


# ======================================================================= משלחת (המשחק עצמו)


class Expedition:
    LR = 4

    def __init__(self, app, md):
        self.app, self.md, self.snd = app, md, app.snd
        seed = random.randrange(1 << 30)
        self.rng = np.random.default_rng(seed)
        self.hab = hab = Habitat(md["hab"], seed)
        self.land = hab.kind == "forest"
        if self.land:
            self.player = Player(300, hab.floor[300] - 66, True)
            self.pframes = explorer_frames()
        else:
            sx = 280
            self.player = Player(sx, hab.ceil[sx] + 160, False)
            self.pframes = render_frames(paint_sub, 124, 66, 1.0, 4)
        self.pframes_l = [pygame.transform.flip(f, True, False) for f in self.pframes]
        bodies, glows = app.monster_frames(md)
        self.monster = Monster(md, bodies, glows, hab, self.rng)
        self.critters = []
        for kind, n in md["hab"].get("decoys", []):
            b, gl = app.decoy_frames(kind, self.land)
            for _ in range(n):
                self.critters.append(Critter(kind, DECOYS[kind], b, gl, hab, self.rng, 700))
        fx, fy, fw = md["face"]
        fr = bodies[0].copy()
        if glows[0] is not None:
            fr.blit(glows[0], (0, 0), special_flags=pygame.BLEND_ADD)
        cw = max(40, int(fr.get_width() * fw))
        ch = int(cw * H / W)
        rect = pygame.Rect(0, 0, cw, ch)
        rect.center = (int(fr.get_width() * fx), int(fr.get_height() * fy))
        face = pygame.Surface(rect.size, SRCALPHA)
        face.blit(fr, (-rect.x, -rect.y))
        scale = max(W * 1.25 / rect.w, H * 1.25 / rect.h)
        self.jump_img = pygame.transform.smoothscale(face, (int(rect.w * scale), int(rect.h * scale)))
        self.cam_x = clamp(self.player.x - W / 2, 0, hab.w - W)
        self.cam_y = clamp(self.player.y - H / 2, 0, hab.h - H)
        self.last_cam = (self.cam_x, self.cam_y)
        rr = random.Random(seed)
        self.rr = rr
        self.theme = hab.theme if self.land else {}
        self.night = bool(self.land and self.theme.get("night"))
        self.pickups = []
        if self.night:
            for i in range(7):
                x = hab.w * (0.15 + 0.8 * i / 6) + rr.uniform(-150, 150)
                self.pickups.append([x, hab.floor[int(x)] - 16])
        if not self.land:
            for i in range(7):
                x = hab.w * (0.15 + 0.8 * i / 6) + rr.uniform(-150, 150)
                y = hab.clamp_y(x, rr.uniform(hab.ceil[int(x)] + 80, hab.floor[int(x)] - 50), 60, 40)
                self.pickups.append([x, y])
        cfg = md["hab"]
        self.jellies = [dict(x=rr.uniform(400, hab.w - 200), y=0, ph=rr.uniform(0, TAU),
                             col=rr.choice([(80, 200, 255), (200, 110, 255), (90, 255, 200), (255, 140, 200)]),
                             vx=rr.uniform(-12, 12)) for _ in range(cfg.get("jelly", 0))]
        for j in self.jellies:
            j["y"] = hab.clamp_y(j["x"], rr.uniform(0, hab.h), 60, 60)
        self.anglers = [dict(x=rr.uniform(500, hab.w - 200), ph=rr.uniform(0, TAU)) for _ in range(cfg.get("anglers", 0))]
        for a in self.anglers:
            a["y"] = hab.clamp_y(a["x"], rr.uniform(hab.h * 0.4, hab.h), 60, 60)
        self.fish = []
        for s in range(cfg.get("fish", 0) // 10):
            cx = rr.uniform(500, hab.w - 300)
            cy = hab.clamp_y(cx, rr.uniform(0, hab.h), 120, 120)
            for _ in range(10):
                self.fish.append(dict(x=cx + rr.uniform(-60, 60), y=cy + rr.uniform(-40, 40), vx=0, vy=0, school=s))
        self.schools = {}
        self.butterflies = [dict(x=rr.uniform(0, hab.w), y=rr.uniform(380, 570), ph=rr.uniform(0, TAU),
                                 col=rr.choice([(255, 200, 40), (90, 170, 255), (255, 120, 180), (255, 255, 255)]))
                            for _ in range(40 if self.theme.get("butterflies") else 0)]
        nsnow = 170 if not self.land else (260 if self.theme.get("snowfall") else 0)
        self.snow = [[rr.uniform(0, W), rr.uniform(0, H), rr.uniform(0.3, 1.0)] for _ in range(nsnow)]
        self.snow_fall = 70 if self.land else 8
        self.dust = []
        self.bubbles, self.footprints, self.pings, self.smoke = [], [], [], []
        self.blips, self.ink, self.birds = [], [], []
        self.time = 0.0
        self.air = 100.0
        self.hull = 3
        self.msg, self.msg_t = "", 0.0
        self.say(f"המשימה: אתר וצלם את {md['name']}!", 4.0)
        self.photo_cd = 0.0
        self.photos = 0
        self.confused = []
        self.flash = 0.0
        self.shake = 0.0
        self.hurt = 0.0
        self.jump_t = 0.0
        self.fail_after = False
        self.ping_cd = 0.0
        self.beep_t = 1.0
        self.heart_t = 1.0
        self.event_t = rr.uniform(10, 16)
        self.bird_event = rr.uniform(6, 10)
        self.flicker_t = 0.0
        self.cone_k = 1.0
        self.dusk = 0.0
        self.running = False
        self.found_t = None
        self.capture_pending = False
        self.photo = None
        self.rating = 1
        self.result = None
        self.fail_reason = ""
        self.tip_shown = False
        self.low_warned = False
        lw, lh = W // self.LR, H // self.LR
        self.GX, self.GY = np.meshgrid((np.arange(lw, dtype=F32) + 0.5) * self.LR,
                                       (np.arange(lh, dtype=F32) + 0.5) * self.LR, indexing="ij")
        self.dark_small = pygame.Surface((lw, lh), SRCALPHA)
        self.dark_small.fill((*cfg["dark_col"], 255))
        self.dark_big = pygame.Surface((W, H), SRCALPHA)
        self.vignette = app.vignette
        self.red_vig = app.red_vignette
        self.ray = app.ray_warm if self.land else app.ray_sprite
        self.whispers = md.get("whispers", [])
        self.air_label = ("סוללה" if self.night else "אור יום") if self.land else "חמצן"
        self.cone_L = 720 if self.land else 640
        self.cone_half = 0.4
        self.ink_spr = app.ink_sprite
        self.snd.loop("amb_forest" if self.land else "amb_water")

    # ------------------------------------------------------------ עזרים
    def say(self, s, t=2.5):
        self.msg, self.msg_t = s, t

    def origin(self):
        p = self.player
        if self.land:
            return p.x + p.facing * 34, p.y - 8
        return p.x + p.facing * 52, p.y + 4

    def extra_lights(self):
        L = []
        cx, cy = self.cam_x, self.cam_y
        for j in self.jellies:
            L.append((j["x"], j["y"], 90, 0.35))
        for vx, vy in self.hab.vents:
            L.append((vx, vy - 20, 230, 0.55))
        for a in self.anglers:
            L.append((a["x"] + 30, a["y"] - 22, 60, 0.3))
        for lx, ly in getattr(self.hab, "lamps", []):
            L.append((lx, ly + 200, 320, 0.85))
        out = []
        for x, y, r, st in L:
            sx, sy = x - cx, y - cy
            if -r < sx < W + r and -r < sy < H + r and st > 0.01:
                out.append((sx, sy, r, st))
        if self.flash > 0:
            ox, oy = self.origin()
            out.append((ox - cx, oy - cy, 900, self.flash * 1.3))
        return out[:14]

    def light_screen(self, sx, sy):
        ox, oy = self.origin()
        ox, oy = ox - self.cam_x, oy - self.cam_y
        dx, dy = sx - ox, sy - oy
        d = math.hypot(dx, dy) + 1e-3
        a = self.player.aim
        cosd = (dx * math.cos(a) + dy * math.sin(a)) / d
        ch = math.cos(self.cone_half)
        light = clamp((cosd - ch) / (1 - ch), 0, 1) ** 0.8 * clamp(1 - d / self.cone_L, 0, 1) ** 0.7 * self.cone_k
        pd = math.hypot(sx - (self.player.x - self.cam_x), sy - (self.player.y - self.cam_y))
        light += clamp(1 - pd / 190, 0, 1) ** 1.5 * 0.8
        for lx, ly, r, st in self.extra_lights():
            light += st * clamp(1 - math.hypot(sx - lx, sy - ly) / r, 0, 1) ** 2
        return clamp(light, 0, 1)

    def base_dark(self, wy):
        b = self.hab.dark[int(clamp(wy, 0, self.hab.h - 1))]
        return min(255.0, b + self.dusk * 175)

    def visibility(self, wx, wy):
        return 1 - self.base_dark(wy) * (1 - self.light_screen(wx - self.cam_x, wy - self.cam_y)) / 255

    def visibility_of(self, cr):
        if getattr(cr, "hidden", False):
            return 0.0, 0.0
        pts = self.md["samples"] if cr is self.monster else cr.samples
        best, on = 0.0, 0
        for fx, fy in pts:
            x, y = cr.point(fx, fy)
            sx, sy = x - self.cam_x, y - self.cam_y
            if 0 <= sx < W and 0 <= sy < H and not (self.land and self.hab.occluded(x, y)):
                on += 1
                best = max(best, self.visibility(x, y))
        return best, on / len(pts)

    def monster_visibility(self):
        return self.visibility_of(self.monster)

    def aimed_at(self, cr):
        if not self.land:
            return True
        mx, my = pygame.mouse.get_pos()
        r = pygame.Rect(0, 0, cr.w + 80, cr.h + 80)
        r.center = (int(cr.x - self.cam_x), int(cr.y - self.cam_y))
        return r.collidepoint(mx, my)

    def photo_ok(self, cr):
        v, frac = self.visibility_of(cr)
        d = math.hypot(cr.x - self.player.x, cr.y - self.player.y)
        return v > 0.35 and frac >= 0.5 and d < 950 and self.aimed_at(cr), v, frac, d

    def danger(self):
        m, p = self.monster, self.player
        d = math.hypot(m.x - p.x, m.y - p.y)
        k = clamp(1 - d / 1300, 0, 1)
        if m.state == "charge" or (m.hunting and d < 1500):
            k = max(k, 0.75)
        return k

    # ------------------------------------------------------------ אירועים
    def take_photo(self):
        if self.photo_cd > 0 or self.found_t is not None or self.jump_t > 0:
            return
        self.photo_cd = 0.9
        self.flash = 1.0
        self.photos += 1
        self.snd.play("shutter")
        m = self.monster
        ok, v, frac, d = self.photo_ok(m)
        if ok:
            self.found_t = 1.4
            self.capture_pending = True
            self.rating = 1 + (v > 0.55) + (frac >= 0.6 and d < 700)
            self.say("!!! תפסת אותו במצלמה !!!", 3)
            self.snd.play("win")
            return
        for cr in sorted(self.critters, key=lambda c: math.hypot(c.x - self.player.x, c.y - self.player.y)):
            if self.photo_ok(cr)[0]:
                self.say(cr.msg, 3.2)
                if cr.name not in self.confused:
                    self.confused.append(cr.name)
                return
        if self.land and d < 950:
            vis_any = any(0 <= m.point(fx, fy)[0] - self.cam_x < W for fx, fy in self.md["samples"])
            if vis_any and frac < 0.5:
                self.say("ביגפוט מסתתר מאחורי השיחים! חכה שייצא...", 2.5)
                return
            if frac >= 0.5 and not self.aimed_at(m):
                self.say("כוון את המצלמה (העכבר) עליו!", 2.2)
                return
        if frac >= 0.5 and d < 950:
            self.say("חשוך מדי! כוון את הפנס ישר אל המפלצת", 2.2)
        elif frac > 0 and d < 950:
            self.say("המפלצת לא בתוך התמונה - הזז את המצלמה אליה!", 2.2)
        else:
            self.say("אין כאן כלום... נסה את " + ("ההקשבה" if self.land else "הסונאר") + " (E)", 2.2)

    def sonar(self):
        if self.ping_cd > 0 or self.found_t is not None:
            return
        self.ping_cd = 3.5
        p = self.player
        self.pings.append([p.x, p.y, 0.0, set()])
        self.snd.play("ping", 0.4 if self.land else 0.7)

    def monster_attack(self, m):
        self.hull -= 1
        self.jump_t = 0.9
        self.shake = 1.4
        self.hurt = 1.0
        self.snd.play("sting", 1.0)
        self.snd.play("roar", 1.0)
        if m.mode == "ambush":
            self.spray_ink(self.player.x + self.player.facing * 150, self.player.y)
        m.respawn_far(self.player.x)
        if self.hull <= 0:
            self.fail_after = True
            self.fail_reason = "attack"
        else:
            self.say(f"{self.md['name']} תקף אותך! נשארו לך {self.hull} חיים", 3)

    def critter_attack(self, cr):
        self.hull -= 1
        self.shake = 0.8
        self.hurt = 1.0
        self.snd.play("growl", 1.0)
        self.player.vx = -self.player.facing * 500
        if self.hull <= 0:
            self.fail_after = True
            self.fail_reason = "bear"
            self.jump_t = 0.01
        else:
            self.say(f"{cr.name} תקף אותך! תתרחק! (נשארו {self.hull} חיים)", 3)

    def spray_ink(self, x, y):
        for _ in range(26):
            self.ink.append([x + random.uniform(-120, 120), y + random.uniform(-80, 80), random.uniform(40, 90), 6.0,
                             random.uniform(-60, 60), random.uniform(-40, 40)])
        self.snd.play("splash", 0.8)

    def spawn_birds(self, x, n):
        for _ in range(n):
            self.birds.append([x + random.uniform(-60, 60), random.uniform(240, 360), random.uniform(-220, 220),
                               random.uniform(-200, -120), random.uniform(0, TAU), 5.0])
        self.snd.play("bird", 0.5)

    # ------------------------------------------------------------ עדכון
    def update(self, dt, keys):
        hab, p, m = self.hab, self.player, self.monster
        self.time += dt
        self.msg_t = max(0.0, self.msg_t - dt)
        self.photo_cd = max(0.0, self.photo_cd - dt)
        self.ping_cd = max(0.0, self.ping_cd - dt)
        self.flash = max(0.0, self.flash - dt * 3.5)
        self.shake = max(0.0, self.shake - dt * 0.8)
        self.hurt = max(0.0, self.hurt - dt * 1.2)
        if self.jump_t > 0:
            self.jump_t -= dt
            if self.jump_t <= 0 and self.fail_after:
                self.result = "fail"
                self.snd.play("fail")
            return
        if self.found_t is not None:
            self.found_t -= dt
            if self.found_t <= 0:
                self.result = "found"
            return
        self.running = boost = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        if self.night:
            self.air -= dt * (100 / 240) * (1.3 if boost else 1.0)
            self.dusk = 0.0
        elif self.land:
            self.air -= dt * 100 / 300
            self.dusk = clamp((40 - self.air) / 40, 0, 1)
            self.cone_k = self.dusk
        else:
            self.air -= dt * (100 / 230) * (1.6 if boost else 1.0)
        if self.air < 25 and not self.low_warned:
            self.low_warned = True
            self.say("הסוללה נגמרת! חפש סוללות על הקרקע" if self.night else
                     ("השמש מתחילה לשקוע! מהר!" if self.land else "חמצן נמוך! חפש מכלים ירוקים זוהרים"), 3)
        if self.air <= 0:
            self.air = 0
            self.result = "fail"
            self.fail_reason = "time"
            self.snd.play("fail")
            return
        if not self.tip_shown and self.time > 14:
            self.tip_shown = True
            self.say("טיפ: לחץ E כדי " + ("להקשיב לרעשים" if self.land else "לשלוח סונאר") + " - אבל לא כל סימון הוא המפלצת!", 3.5)
        mx, my = pygame.mouse.get_pos()
        ox, oy = self.origin()
        p.aim = math.atan2(my - (oy - self.cam_y), mx - (ox - self.cam_x))
        p.facing = 1 if math.cos(p.aim) >= 0 else -1
        ax = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        ay = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if self.land:
            vmax = 330 if boost else 190
            p.vx += (ax * vmax - p.vx) * min(1, dt * 8)
            p.x = clamp(p.x + p.vx * dt, 60, hab.w - 60)
            p.y = hab.floor[int(p.x)] - 66
            p.anim += abs(p.vx) * dt / 18
        else:
            vmax = 430 if boost else 270
            ln = math.hypot(ax, ay) or 1
            p.vx += (ax / ln * vmax - p.vx) * min(1, dt * 2.6)
            p.vy += (ay / ln * vmax - p.vy) * min(1, dt * 2.6)
            p.x = clamp(p.x + p.vx * dt, 60, hab.w - 60)
            ny = hab.clamp_y(p.x, p.y + p.vy * dt, 26, 26)
            if abs(ny - (p.y + p.vy * dt)) > 0.5:
                p.vy *= 0.3
            p.y = ny
            p.anim += dt * (6 + math.hypot(p.vx, p.vy) / 20)
            if math.hypot(p.vx, p.vy) > 60 and random.random() < dt * 14:
                self.bubbles.append([p.x - p.facing * 58, p.y + 2, random.uniform(2, 4), 3.0])
        lead = 120
        tx = p.x - W / 2 + math.cos(p.aim) * lead
        ty = p.y - H / 2 + math.sin(p.aim) * lead * 0.7
        k = min(1, dt * 4)
        self.cam_x = clamp(self.cam_x + (tx - self.cam_x) * k, 0, hab.w - W)
        self.cam_y = clamp(self.cam_y + (ty - self.cam_y) * k, 0, hab.h - H)
        # הבהוב פנס כשהמפלצת קרובה
        dg = self.danger()
        if not self.land or self.night:
            if self.flicker_t > 0:
                self.flicker_t -= dt
                self.cone_k = random.uniform(0.1, 0.55)
            else:
                self.cone_k = 1.0
                if dg > 0.35 and random.random() < dt * 0.7:
                    self.flicker_t = random.uniform(0.15, 0.4)
        if dg > 0.15:
            self.heart_t -= dt
            if self.heart_t <= 0:
                self.heart_t = 1.25 - 0.85 * dg
                self.snd.play("heart", 0.35 + 0.65 * dg)
        m.update(dt, self)
        for cr in self.critters:
            cr.update(dt, self)
        # סונאר
        targets = [m] + self.critters
        for pg in self.pings[:]:
            r0 = pg[2]
            pg[2] += 1300 * dt
            for i, cr in enumerate(targets):
                if i in pg[3]:
                    continue
                d = math.hypot(cr.x - pg[0], cr.y - pg[1])
                if r0 <= d < pg[2]:
                    pg[3].add(i)
                    self.blips.append([cr.x, cr.y, 5.0])
                    self.snd.play("beep", 0.5)
            if pg[2] > 3200:
                self.pings.remove(pg)
        for b in self.blips[:]:
            b[2] -= dt
            if b[2] <= 0:
                self.blips.remove(b)
        lvl = self.signal_level()
        if lvl >= 2:
            self.beep_t -= dt
            if self.beep_t <= 0:
                self.beep_t = {5: 0.25, 4: 0.5, 3: 0.9, 2: 1.5}[lvl]
                self.snd.play("beep", 0.08 + lvl * 0.04)
        # אירועים מפחידים / מסיחי דעת
        self.event_t -= dt
        if self.event_t <= 0:
            self.event_t = self.rr.uniform(13, 22)
            if self.whispers and self.rr.random() < 0.45:
                self.say(self.rr.choice(self.whispers), 3)
                self.snd.play("moan", 0.35)
            elif self.land:
                c = self.rr.random()
                if c < 0.4:
                    self.snd.play("snap", 0.7)
                    self.say("קראק! משהו דרך על ענף... אבל מה?", 2.5)
                elif c < 0.7:
                    self.spawn_birds(p.x + self.rr.choice([-1, 1]) * self.rr.uniform(500, 900), 6)
                else:
                    self.snd.play("growl", 0.35)
                    self.say("שמעת נהמה מרחוק...", 2.2)
            else:
                c = self.rr.random()
                if c < 0.45:
                    self.snd.play("moan", 0.6)
                    self.say("...שמעת את זה? משהו גדול שר בחושך", 2.5)
                elif c < 0.7:
                    self.blips.append([p.x + self.rr.uniform(-1500, 1500), p.y + self.rr.uniform(-500, 500), 4.0])
                    self.snd.play("beep", 0.6)
                    self.say("הסונאר קלט משהו לרגע... ואז הוא נעלם", 2.5)
                else:
                    self.snd.play("roar", 0.25)
                    self.shake = max(self.shake, 0.25)
        if self.land:
            self.bird_event -= dt
            if self.bird_event <= 0:
                self.bird_event = self.rr.uniform(9, 15)
                self.spawn_birds(p.x + self.rr.uniform(-1200, 1200), 4)
        # חפצים וחלקיקים
        for pk in self.pickups[:]:
            if math.hypot(pk[0] - p.x, pk[1] - p.y) < 60:
                self.pickups.remove(pk)
                self.air = min(100, self.air + 35)
                self.low_warned = self.air < 25
                self.snd.play("pickup")
                self.say(f"מצאת עוד {self.air_label}!", 1.5)
        for b in self.bubbles[:]:
            b[1] -= (30 + b[2] * 6) * dt
            b[0] += math.sin(self.time * 3 + b[2] * 7) * 12 * dt
            b[3] -= dt
            if b[3] <= 0 or (not self.land and b[1] < hab.ceil[int(clamp(b[0], 0, hab.w - 1))]):
                self.bubbles.remove(b)
        if len(self.bubbles) > 400:
            del self.bubbles[:50]
        for fp in self.footprints[:]:
            fp[3] -= dt
            if fp[3] <= 0:
                self.footprints.remove(fp)
        for d_ in self.dust[:]:
            d_[0] += d_[2] * dt
            d_[1] += d_[3] * dt
            d_[3] += 260 * dt
            d_[4] -= dt
            if d_[4] <= 0:
                self.dust.remove(d_)
        for ik in self.ink[:]:
            ik[0] += ik[4] * dt
            ik[1] += ik[5] * dt
            ik[2] += 25 * dt
            ik[3] -= dt
            if ik[3] <= 0:
                self.ink.remove(ik)
        for bd in self.birds[:]:
            bd[0] += bd[2] * dt
            bd[1] += bd[3] * dt
            bd[3] += 30 * dt
            bd[4] += dt * 14
            bd[5] -= dt
            if bd[5] <= 0:
                self.birds.remove(bd)
        for j in self.jellies:
            j["ph"] += dt * 1.6
            j["x"] = clamp(j["x"] + j["vx"] * dt, 100, hab.w - 100)
            j["y"] = hab.clamp_y(j["x"], j["y"] + math.sin(j["ph"]) * 14 * dt - 3 * dt, 40, 40)
        for vx, vy in hab.vents:
            if random.random() < dt * 9:
                self.smoke.append([vx + random.uniform(-6, 6), vy, random.uniform(8, 14), 4.0])
        for s in self.smoke[:]:
            s[1] -= 45 * dt
            s[2] += 8 * dt
            s[3] -= dt
            if s[3] <= 0:
                self.smoke.remove(s)
        for f in self.butterflies:
            f["ph"] += dt
            f["x"] += math.sin(f["ph"] * 0.7) * 40 * dt
            f["y"] += math.cos(f["ph"] * 1.3) * 30 * dt
        self.update_fish(dt)
        dcx, dcy = self.cam_x - self.last_cam[0], self.cam_y - self.last_cam[1]
        self.last_cam = (self.cam_x, self.cam_y)
        for s in self.snow:
            s[0] = (s[0] - dcx * s[2] + math.sin(self.time + s[2] * 9) * 6 * dt) % W
            s[1] = (s[1] - dcy * s[2] + self.snow_fall * s[2] * dt) % H

    def update_fish(self, dt):
        hab, p = self.hab, self.player
        for s in {f["school"] for f in self.fish}:
            if s not in self.schools or random.random() < dt * 0.15:
                cx = clamp(p.x + random.uniform(-1500, 1500), 300, hab.w - 300)
                self.schools[s] = (cx, hab.clamp_y(cx, random.uniform(0, hab.h), 120, 120))
        for f in self.fish:
            tx, ty = self.schools[f["school"]]
            ax, ay = (tx - f["x"]) * 0.4, (ty - f["y"]) * 0.4
            dx, dy = f["x"] - p.x, f["y"] - p.y
            d = math.hypot(dx, dy) + 1
            if d < 220:
                ax += dx / d * 900
                ay += dy / d * 900
            f["vx"] = clamp(f["vx"] + (ax + random.uniform(-60, 60)) * dt, -220, 220)
            f["vy"] = clamp(f["vy"] + (ay + random.uniform(-60, 60)) * dt, -120, 120)
            f["x"] = clamp(f["x"] + f["vx"] * dt, 50, hab.w - 50)
            f["y"] = hab.clamp_y(f["x"], f["y"] + f["vy"] * dt, 20, 20)

    def signal_level(self):
        p = self.player
        d = math.hypot(self.monster.x - p.x, self.monster.y - p.y)
        for cr in self.critters:
            d = min(d, math.hypot(cr.x - p.x, cr.y - p.y) * 1.2)
        for lvl, lim in ((5, 450), (4, 850), (3, 1400), (2, 2100), (1, 3000)):
            if d < lim:
                return lvl
        return 0

    # ------------------------------------------------------------ ציור
    def compute_dark(self, screen):
        hab = self.hab
        rows = np.clip((self.GY[0] + self.cam_y).astype(int), 0, hab.h - 1)
        base = np.minimum(255.0, hab.dark[rows] + self.dusk * 175)[None, :]
        if base.max() < 3:
            return
        ox, oy = self.origin()
        ox, oy = ox - self.cam_x, oy - self.cam_y
        dx, dy = self.GX - ox, self.GY - oy
        d = np.sqrt(dx * dx + dy * dy) + 1e-3
        a = self.player.aim
        ch = math.cos(self.cone_half)
        cosd = (dx * math.cos(a) + dy * math.sin(a)) / d
        light = (np.clip((cosd - ch) / (1 - ch), 0, 1) ** 0.8) * (np.clip(1 - d / self.cone_L, 0, 1) ** 0.7) * self.cone_k
        pdx, pdy = self.GX - (self.player.x - self.cam_x), self.GY - (self.player.y - self.cam_y)
        light += np.clip(1 - np.sqrt(pdx * pdx + pdy * pdy) / 190, 0, 1) ** 1.5 * 0.8
        for lx, ly, r, st in self.extra_lights():
            ex, ey = self.GX - lx, self.GY - ly
            light += st * np.clip(1 - np.sqrt(ex * ex + ey * ey) / r, 0, 1) ** 2
        alpha = base * (1 - np.clip(light, 0, 1))
        pa = pygame.surfarray.pixels_alpha(self.dark_small)
        pa[:] = alpha.astype(np.uint8)
        del pa
        pygame.transform.smoothscale(self.dark_small, (W, H), self.dark_big)
        screen.blit(self.dark_big, (0, 0))

    def draw_creature(self, screen, cr, cx, cy):
        if getattr(cr, "mode", "") == "burrower" and cr.emerge < 1:
            gx = cr.x - cx
            fy = self.hab.floor[int(clamp(cr.x, 0, self.hab.w - 1))] - cy
            if -200 < gx < W + 200:
                if cr.state == "under":
                    bump = 10 + 4 * math.sin(self.time * 9)
                    pygame.draw.ellipse(screen, (196, 150, 92), (gx - 70, fy - bump, 140, bump * 2))
                    pygame.draw.ellipse(screen, (230, 190, 130), (gx - 50, fy - bump, 100, bump))
                else:
                    off = int((1 - cr.emerge) * cr.h)
                    fr = cr.frame()
                    x, y = gx - cr.w / 2, cr.y - cy - cr.h / 2 + off
                    screen.blit(fr, (x, y), pygame.Rect(0, 0, cr.w, max(0, cr.h - off - 8)))
            return False
        fr = cr.frame()
        x, y = cr.x - cx - cr.w / 2, cr.y - cy - cr.h / 2
        if x < W and y < H and x + cr.w > 0 and y + cr.h > 0:
            screen.blit(fr, (x, y))
            return True
        return False

    def draw(self, screen):
        hab, p, m, t = self.hab, self.player, self.monster, self.time
        sh = self.shake
        cx = int(self.cam_x + (random.uniform(-1, 1) * sh * 18 if sh else 0))
        cy = int(self.cam_y + (random.uniform(-1, 1) * sh * 18 if sh else 0))
        if self.land:
            screen.blit(hab.sky, (0, 0))
            for par, s in hab.layers:
                screen.blit(s, (0, 0), pygame.Rect(int(cx * par), 0, W, H))
            for i in range(7):
                sx = (i * 380 + 120 - cx * 0.7) % (W + 400) - 200
                screen.blit(self.ray, (sx, -30), special_flags=pygame.BLEND_ADD)
            screen.blit(hab.bg, (0, 0), pygame.Rect(cx, 0, W, H))
        else:
            screen.blit(hab.bg, (0, 0), pygame.Rect(cx, cy, W, H))
            if hab.surface is not None:
                sy = hab.surface - cy
                if -20 < sy < H + 20:
                    pts = [(x, sy + 4 * math.sin(x * 0.02 + t * 2) + 2 * math.sin(x * 0.05 - t * 3)) for x in range(0, W + 16, 16)]
                    pygame.draw.lines(screen, mix(hab.cfg["top_col"], (255, 255, 255), 0.6), False, pts, 3)
                    pygame.draw.lines(screen, mix(hab.cfg["top_col"], (255, 255, 255), 0.3), False, [(x, y + 7) for x, y in pts], 2)
            if hab.cfg.get("rays"):
                top = (hab.surface or 60) - cy
                for i in range(9):
                    sx = i * 520 + 140 - cx * 0.85 + math.sin(t * 0.3 + i) * 40
                    sx = (sx + 300) % (W + 600) - 300
                    if top < H:
                        screen.blit(self.ray, (sx, top), special_flags=pygame.BLEND_ADD)
            for kx, ky, kh, ph, col in hab.kelp:
                sx, sy = kx - cx, ky - cy
                if -60 < sx < W + 60 and sy - kh < H and sy > 0:
                    prev = (sx, sy)
                    for i in range(1, 9):
                        k = i / 8
                        cur = (sx + math.sin(t * 1.2 + ph + k * 2.5) * 22 * k, sy - kh * k)
                        pygame.draw.line(screen, mul(col, 0.7 + 0.5 * k), prev, cur, max(2, int(9 * (1 - k)) + 2))
                        if i % 2 == 0:
                            pygame.draw.ellipse(screen, col, (cur[0] - 2, cur[1] - 6, 16, 7))
                        prev = cur
            for s in self.smoke:
                sx, sy = s[0] - cx, s[1] - cy
                if -40 < sx < W + 40 and -40 < sy < H + 40:
                    pygame.draw.circle(screen, (22, 20, 22), (sx, sy), s[2])
        for fp in self.footprints:
            sx, sy = fp[0] - cx, fp[1] - cy
            if -30 < sx < W + 30:
                c = mix((86, 128, 52), (40, 50, 25), min(1, fp[3] / 20))
                pygame.draw.ellipse(screen, c, (sx - 16, sy - 3, 32, 10))
                for k in range(5):
                    pygame.draw.circle(screen, c, (sx + fp[2] * (12 + k * 1.5) , sy - 4 + k * 2.2), 2.4)
        for b in self.bubbles:
            sx, sy = b[0] - cx, b[1] - cy
            if -10 < sx < W + 10 and -10 < sy < H + 10:
                pygame.draw.circle(screen, (170, 215, 235), (sx, sy), b[2], 1)
                pygame.draw.circle(screen, (230, 250, 255), (sx - b[2] * 0.35, sy - b[2] * 0.35), max(1, b[2] * 0.25))
        for cr in self.critters:
            self.draw_creature(screen, cr, cx, cy)
        self.draw_creature(screen, m, cx, cy)
        if self.land:
            for b in hab.bushes:
                sx = b["x"] - cx - b["spr"].get_width() / 2
                if -300 < sx < W + 20:
                    screen.blit(b["spr"], (sx, b["top"] - cy))
        for f in self.fish:
            sx, sy = f["x"] - cx, f["y"] - cy
            if -10 < sx < W + 10 and -10 < sy < H + 10:
                d = 1 if f["vx"] >= 0 else -1
                pygame.draw.ellipse(screen, (170, 180, 175), (sx - 9, sy - 4, 18, 8))
                pygame.draw.polygon(screen, (140, 150, 145), [(sx - 8 * d, sy), (sx - 15 * d, sy - 5), (sx - 15 * d, sy + 5)])
        for f in self.butterflies:
            sx, sy = f["x"] - cx, f["y"] - cy
            if -10 < sx < W + 10:
                fl = abs(math.sin(t * 12 + f["ph"])) * 7 + 1
                pygame.draw.ellipse(screen, f["col"], (sx - 8, sy - fl / 2, 7, fl))
                pygame.draw.ellipse(screen, f["col"], (sx + 1, sy - fl / 2, 7, fl))
                pygame.draw.line(screen, (30, 30, 30), (sx, sy - 3), (sx, sy + 3), 2)
        for pk in self.pickups:
            sx, sy = pk[0] - cx, pk[1] - cy + math.sin(t * 2 + pk[0]) * 4
            if self.land and -30 < sx < W + 30:
                pygame.draw.rect(screen, (40, 40, 45), (sx - 14, sy - 9, 28, 18), border_radius=3)
                pygame.draw.rect(screen, (90, 230, 110), (sx - 10, sy - 5, 16, 10))
                pygame.draw.rect(screen, (200, 200, 200), (sx + 14, sy - 4, 4, 8))
            elif -30 < sx < W + 30 and -30 < sy < H + 30:
                pygame.draw.rect(screen, (60, 190, 90), (sx - 9, sy - 20, 18, 40), border_radius=8)
                pygame.draw.rect(screen, (150, 250, 170), (sx - 5, sy - 15, 4, 28), border_radius=2)
                pygame.draw.rect(screen, (190, 190, 195), (sx - 4, sy - 27, 8, 8))
        pf = self.pframes if p.facing > 0 else self.pframes_l
        if self.land:
            img = pf[int(p.anim) % len(pf)] if abs(p.vx) > 8 else pf[0]
        else:
            img = pf[int(p.anim) % len(pf)]
        screen.blit(img, (p.x - cx - img.get_width() / 2, p.y - cy - img.get_height() / 2))
        for d_ in self.dust:
            pygame.draw.circle(screen, (214, 172, 112), (d_[0] - cx, d_[1] - cy), 3)
        snowr = 2 if self.land else 1
        for s in self.snow:
            c = int(120 + 110 * s[2])
            pygame.draw.circle(screen, (c, c, min(255, c + 15)), (s[0], s[1]), snowr + (s[2] > 0.75))
        if self.land:
            screen.blit(hab.fore, (0, 0), pygame.Rect(int(cx * 1.25), 0, W, H))
            for bd in self.birds:
                sx, sy = bd[0] - cx, bd[1] - cy
                if -20 < sx < W + 20:
                    fl = math.sin(bd[4]) * 7
                    pygame.draw.lines(screen, (30, 30, 35), False, [(sx - 10, sy - fl), (sx, sy), (sx + 10, sy - fl)], 3)
            if self.dusk > 0:
                ov = pygame.Surface((W, H), SRCALPHA)
                ov.fill((255, 110, 40, int(70 * self.dusk)))
                screen.blit(ov, (0, 0))
        # חושך + אור
        self.compute_dark(screen)
        # דברים זוהרים (נראים גם בחושך)
        for j in self.jellies:
            sx, sy = j["x"] - cx, j["y"] - cy
            if -60 < sx < W + 60 and -60 < sy < H + 80:
                pul = 0.75 + 0.25 * math.sin(j["ph"])
                add_glow(screen, sx, sy, 46, mul(j["col"], 0.45 * pul))
                pygame.draw.ellipse(screen, mul(j["col"], 0.9), (sx - 13 * pul, sy - 10, 26 * pul, 15))
                for k in range(4):
                    x0 = sx - 9 + k * 6
                    pygame.draw.lines(screen, mul(j["col"], 0.5), False,
                                      [(x0 + math.sin(t * 2 + k + i * 0.8) * 3, sy + 4 + i * 7) for i in range(5)], 1)
        for vx, vy in hab.vents:
            sx, sy = vx - cx, vy - cy
            if -200 < sx < W + 200 and -200 < sy < H + 200:
                add_glow(screen, sx, sy, 90, (130, 50, 10))
                add_glow(screen, sx, sy, 26, (220, 120, 40))
        for a in self.anglers:
            sx, sy = a["x"] - cx, a["y"] - cy + math.sin(t + a["ph"]) * 8
            if -40 < sx < W + 40 and -40 < sy < H + 40:
                add_glow(screen, sx + 30, sy - 22, 22, (90, 200, 220))
                pygame.draw.circle(screen, (200, 255, 255), (sx + 30, sy - 22), 3)
        for pk in self.pickups:
            sx, sy = pk[0] - cx, pk[1] - cy
            if -60 < sx < W + 60 and -60 < sy < H + 60:
                add_glow(screen, sx, sy, 40, (25, 90, 35))
        if self.land:
            for par, wx_, wy_, ww, wh in getattr(hab, "windows", []):
                sx = wx_ - cx * par
                if -40 < sx < W + 40:
                    pygame.draw.rect(screen, (200, 160, 80), (sx, wy_, ww, wh))
                    add_glow(screen, sx + ww / 2, wy_ + wh / 2, 34, (60, 45, 15))
            for lx, ly in getattr(hab, "lamps", []):
                sx, sy = lx - cx, ly - cy
                if -300 < sx < W + 300:
                    add_glow(screen, sx, sy, 60, (120, 110, 60))
                    add_glow(screen, sx, sy, 16, (200, 190, 120))
        for cr in self.critters + [m]:
            g = cr.glow()
            if g is not None and not getattr(cr, "hidden", False) and getattr(cr, "emerge", 1) >= 1:
                x, y = cr.x - cx - cr.w / 2, cr.y - cy - cr.h / 2
                if x < W and y < H and x + cr.w > 0 and y + cr.h > 0:
                    screen.blit(g, (x, y), special_flags=pygame.BLEND_ADD)
        for ik in self.ink:
            r = int(ik[2])
            spr = pygame.transform.scale(self.ink_spr, (2 * r, 2 * r))
            spr.set_alpha(int(255 * min(1, ik[3] / 2)))
            screen.blit(spr, (ik[0] - cx - r, ik[1] - cy - r))
        if not self.land or self.night:
            ox, oy = self.origin()
            add_glow(screen, ox - cx, oy - cy, 30, mul((120, 110, 80), self.cone_k))
        for pg in self.pings:
            r = pg[2]
            fade = clamp(1 - r / 3200, 0, 1)
            if r > 4:
                pygame.draw.circle(screen, mul((80, 230, 255) if not self.land else (255, 230, 120), fade * 0.9),
                                   (pg[0] - cx, pg[1] - cy), r, 2)
        for b in self.blips:
            bx, by = b[0] - cx, b[1] - cy
            k = b[2] / 5
            if 0 <= bx < W and 0 <= by < H:
                pygame.draw.circle(screen, mul((255, 80, 60), k), (bx, by), 26 + 8 * math.sin(t * 8), 3)
                text(screen, "?", 26, mul((255, 120, 90), k), int(bx), int(by) - 15, shadow=0)
        screen.blit(self.vignette, (0, 0))
        dg = self.danger()
        if dg > 0.4 and (not self.land or self.night):
            self.red_vig.set_alpha(int(200 * (dg - 0.3) * (0.6 + 0.4 * math.sin(t * 6))))
            screen.blit(self.red_vig, (0, 0))
        if self.hurt > 0:
            red = pygame.Surface((W, H), SRCALPHA)
            red.fill((200, 0, 0, int(110 * self.hurt)))
            screen.blit(red, (0, 0))
        if self.capture_pending:
            self.capture_pending = False
            self.photo = screen.copy()
        if self.flash > 0:
            fl = pygame.Surface((W, H))
            fl.fill((255, 255, 255))
            fl.set_alpha(int(self.flash * 200))
            screen.blit(fl, (0, 0))
        self.draw_hud(screen)
        if self.jump_t > 0 and self.fail_reason != "bear":
            k = self.jump_t / 0.9
            img = self.jump_img
            z = 1 + (1 - k) * 0.25
            if z != 1:
                img = pygame.transform.scale(img, (int(img.get_width() * z), int(img.get_height() * z)))
            screen.fill((0, 0, 0))
            screen.blit(img, (W / 2 - img.get_width() / 2 + random.uniform(-25, 25),
                              H / 2 - img.get_height() / 2 + random.uniform(-25, 25)))
            red = pygame.Surface((W, H), SRCALPHA)
            red.fill((255, 0, 0, int(90 * k)))
            screen.blit(red, (0, 0))

    def draw_hud(self, screen):
        p, m, t = self.player, self.monster, self.time
        md = self.md
        panel = pygame.Surface((330, 160), SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 140), panel.get_rect(), border_radius=14)
        pygame.draw.rect(panel, (255, 255, 255, 40), panel.get_rect(), 2, border_radius=14)
        screen.blit(panel, (W - 350, 16))
        text(screen, md["name"], fit_size(md["name"], 300, 32), (255, 230, 150), W - 34, 22, "right")
        if self.theme.get("rec"):
            if int(t * 2) % 2:
                pygame.draw.circle(screen, (255, 40, 40), (W // 2 - 70, 30), 9)
            text(screen, "REC", 24, (255, 80, 80), W // 2 - 52, 17, "left")
            hh, rem = divmod(int(t) + 2 * 3600 + 13 * 60, 3600)
            text(screen, f"CAM 2   {hh:02d}:{rem // 60:02d}:{rem % 60:02d}", 20, (230, 230, 230), W // 2 + 10, 20, "left", bold=False)
        text(screen, "משימה: לאתר ולצלם", 17, (210, 210, 210), W - 34, 62, "right", bold=False)
        bar = pygame.Rect(W - 330, 96, 190, 18)
        pygame.draw.rect(screen, (30, 20, 20), bar, border_radius=9)
        fw = int(bar.w * self.air / 100)
        col = mix((230, 50, 40), (70, 220, 110), self.air / 60)
        if self.land:
            col = mix((240, 110, 40), (255, 215, 80), self.air / 60)
        if self.air < 25 and int(t * 4) % 2:
            col = (255, 90, 70)
        if fw > 0:
            pygame.draw.rect(screen, col, (bar.right - fw, bar.y, fw, bar.h), border_radius=9)
        text(screen, f"{self.air_label} {int(self.air)}%", 18, (240, 240, 240), W - 34, 93, "right")
        text(screen, "חיים" if self.land else "שריון", 18, (240, 240, 240), W - 34, 127, "right")
        for i in range(3):
            c = (240, 50, 60) if i < self.hull else (70, 50, 55)
            draw_heart(screen, W - 110 - i * 34, 138, 11, c)
        lvl = self.signal_level()
        panel = pygame.Surface((240, 92), SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 140), panel.get_rect(), border_radius=14)
        screen.blit(panel, (16, 16))
        text(screen, "גלאי תנועה", 18, (200, 220, 230), 240, 24, "right")
        for i in range(5):
            on = i < lvl
            c = mix((60, 140, 255), (255, 60, 40), i / 4) if on else (60, 60, 65)
            hh = 10 + i * 7
            pygame.draw.rect(screen, c, (32 + i * 22, 92 - hh, 16, hh), border_radius=3)
        word = ["שקט", "משהו רחוק", "משהו זז", "קרוב!", "קרוב מאוד!", "ממש לידך!"][lvl]
        text(screen, word, 22, mix((140, 190, 255), (255, 90, 60), lvl / 5), 240, 58, "right")
        if self.land:
            info = f"מרחק מהמחנה: {int(p.x / 20)} מ'"
        else:
            info = f"עומק: {int(max(0, p.y - (self.hab.surface or 0)) / 6)} מ'"
        text(screen, info, 18, (200, 210, 220), W - 30, 184, "right", bold=False)
        R = 88
        cxr, cyr = 20 + R, H - 20 - R
        rad = pygame.Surface((2 * R, 2 * R), SRCALPHA)
        pygame.draw.circle(rad, (0, 25, 20, 170), (R, R), R)
        for rr_ in (R * 0.33, R * 0.66):
            pygame.draw.circle(rad, (40, 160, 120, 90), (R, R), rr_, 1)
        a = t * 2
        pygame.draw.line(rad, (80, 255, 180, 120), (R, R), (R + math.cos(a) * R, R + math.sin(a) * R), 2)
        screen.blit(rad, (cxr - R, cyr - R))
        pygame.draw.circle(screen, (80, 200, 160), (cxr, cyr), R, 2)
        scale = R / 2600

        def to_r(wx, wy):
            dx, dy = (wx - p.x) * scale, (wy - p.y) * scale
            d = math.hypot(dx, dy)
            if d > R - 6:
                dx, dy = dx / d * (R - 6), dy / d * (R - 6)
            return int(cxr + dx), int(cyr + dy)

        for pk in self.pickups:
            pygame.draw.circle(screen, (90, 255, 120), to_r(*pk), 3)
        for b in self.blips:
            k = b[2] / 5
            pygame.draw.circle(screen, mul((255, 70, 50), 0.4 + 0.6 * k), to_r(b[0], b[1]), 5 + int(2 * math.sin(t * 8)))
        pygame.draw.circle(screen, (255, 230, 90), (cxr, cyr), 4)
        name = "הקשבה" if self.land else "סונאר"
        if self.ping_cd > 0:
            pygame.draw.arc(screen, (80, 230, 255), (cxr - R - 6, cyr - R - 6, 2 * R + 12, 2 * R + 12), math.pi / 2,
                            math.pi / 2 + TAU * (1 - self.ping_cd / 3.5), 3)
            text(screen, f"{name} נטען...", 16, (150, 200, 220), cxr, cyr - R - 30, bold=False)
        else:
            text(screen, f"E - {name} מוכן", 16, (120, 240, 255), cxr, cyr - R - 30)
        offs = sorted([b for b in self.blips if not (0 <= b[0] - self.cam_x < W and 0 <= b[1] - self.cam_y < H)],
                      key=lambda b: math.hypot(b[0] - p.x, b[1] - p.y))[:4]
        for b in offs:
            bx, by = b[0] - self.cam_x, b[1] - self.cam_y
            ang = math.atan2(by - H / 2, bx - W / 2)
            ex = W / 2 + math.cos(ang) * (W / 2 - 60)
            ey = H / 2 + math.sin(ang) * (H / 2 - 60)
            c = mul((255, 90, 60), 0.5 + 0.5 * b[2] / 5)
            tip = (ex + math.cos(ang) * 22, ey + math.sin(ang) * 22)
            l = (ex + math.cos(ang + 2.5) * 18, ey + math.sin(ang + 2.5) * 18)
            r = (ex + math.cos(ang - 2.5) * 18, ey + math.sin(ang - 2.5) * 18)
            pygame.draw.polygon(screen, c, [tip, l, r])
            dm = int(math.hypot(b[0] - p.x, b[1] - p.y) / 20)
            text(screen, f"{dm} מ'", 18, c, int(ex - math.cos(ang) * 30), int(ey - math.sin(ang) * 30) - 10)
        text(screen, f"תמונות: {self.photos}", 20, (230, 230, 230), W - 30, H - 44, "right")
        pygame.draw.rect(screen, (220, 220, 220), (W - 200, H - 44, 34, 24), border_radius=4)
        pygame.draw.circle(screen, (40, 40, 40), (W - 183, H - 32), 8)
        pygame.draw.circle(screen, (120, 170, 220), (W - 183, H - 32), 5)
        ready = False
        if self.photo_cd <= 0 and self.found_t is None:
            ready = self.photo_ok(m)[0]
            if ready:
                text(screen, "לחץ קליק לצילום!", 26, (255, 240, 120), W // 2, H - 110,
                     alpha=int(170 + 85 * math.sin(t * 8)), glow=(255, 150, 0))
        if self.land:
            mx, my = pygame.mouse.get_pos()
            c = (120, 255, 120) if ready else (255, 255, 255)
            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                x0, y0 = mx + sx * 42, my + sy * 30
                pygame.draw.line(screen, c, (x0, y0), (x0 - sx * 14, y0), 3)
                pygame.draw.line(screen, c, (x0, y0), (x0, y0 - sy * 14), 3)
            pygame.draw.circle(screen, c, (mx, my), 3)
        if self.msg_t > 0:
            text(screen, self.msg, 28, (255, 235, 160), W // 2, 120, alpha=int(255 * min(1, self.msg_t * 2)), glow=(0, 0, 0))
        if self.time < 12:
            hint = "WASD / חצים - תנועה  |  עכבר - " + ("מצלמה" if self.land else "פנס") + \
                   "  |  קליק - צילום  |  E - " + ("הקשבה" if self.land else "סונאר") + "  |  Shift - טורבו  |  Esc - יציאה"
            text(screen, hint, 17, (230, 230, 230), W // 2, H - 34, alpha=int(255 * min(1, (12 - self.time) / 2)), bold=False)
        if self.air < 25:
            k = (0.5 + 0.5 * math.sin(t * 5)) * (1 - self.air / 25)
            self.red_vig.set_alpha(int(160 * k))
            screen.blit(self.red_vig, (0, 0))


# ======================================================================= תמונות מוטמעות
# בלופ - נגזר מהתמונה ששלחת (הרקע הוסר, הפוך שיפנה ימינה).
SPRITES = {"bloop": (
    "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"
    "hsM5/v8wNDT8w7fBqAAAAABJRU5ErkJggg=="
), "ningen": (
    "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"
), "nessie": (
    "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"
    "+jPWIPa/Ab1ELqK78Dg7AAAAAElFTkSuQmCC"
), "deathworm": (
    "iVBORw0KGgoAAAANSUhEUgAAAZsAAAHGCAMAAACVVtbjAAADAFBMVEVrVyGWXBqXWlXeo1yMayNkUyJwThuimFzYnzXYpJpnXERgTiBQMyJ3XVaIMhqR"
    "IBXddEzk0qCuly9AKxmHbEvgHSs8Lh7JYyRYIAp0VkGQPESge4M9LRpdKiRbNUGalFXEM0AyHSA9IQ1/gGGFO0aNgD2+xnz3wD0AAAA2ABZyAximEhRM"
    "AhJuBiKWFRWoDRKOCBKSGSRRCSLMGyPJGhxyFBLJIycYFQyrGSO0JSiId1GxJBVwFCXEeRW2dw+SIyjNuIksJxeRJA7Ht3ePdmhUEyc5BSGKaVRSFBG1"
    "qHApGQ02FA/EIhvKeCp6aUt1aDVTRi56dE/SxI2QamY6NCOShlMaAgCrmGtPRSt2Vk1tSS+JCSIoJRWMWFFyVDW7s3LIqnVHOilPKCpvNzRKOipVNi5x"
    "JA1vKAvMqYlxJipzRitMJhZUFgV0NhVuRzZvSUiNSCmxNDDIhRWKJwmQdTFNJhOQNRFPBwHruI+KNxWph24iGguxbA+1eCfLai+KVjM2KyKpd23MhCll"
    "VTV7cjqWhGhTJhBQORBZVDNjSjPTmShVJA6NSUrOd0tuOCdxZjS1hBWvaxHvuUVrVzOHdjqnl1f2xEppGAKNRzFrKRB0aDGuZ1FGJxCNZxWpDCJyZ0Ss"
    "NBQ0Gw04MhmJWDelaGixhSpYRC2zp1iQh1DHNDDrtzo6JBSxVjHrqozoyKqONi5pOUN2Vy+LaTLUpzU1MxxOGwvOwXq4l4iKQhuycw7npjTqxZVFQiZt"
    "NRluOC+7qIQdEQiLOSiJe0qsRymxd1SviIbNDRk5FgZ0WEJ3ckemeSe4lzHMhm05FCFMNRZbQy9yWRJjWCuwSBSvhjHSlnbVuaMzBwBEHg1UOSiMaDWY"
    "kVY2GQh6c02zZy6jmVfaxqVkSC+FSiuahDSphk+9tYTEWCzQhVAbDgZYOSVnCwByaUV7eGKKZEeYdBGbkmayVBfQaUc6OSJaVCxvNBSOKyyKZEWVgzep"
    "Wk3RlRnMmonIp0daMxpvZS2LVjiKhU1SRRnW9z/qAAABAHRSTlPc2eD+qlug0Oz/XTNR76/L///aLaz/Sf+toP//8sP/q/8ypP+mr///AP7+/v7+/v/+"
    "/v/+/vz+EP7+/vv+/vz+/iz3/v/+//78/S/+/v7++1P+//84/f7+O/+n/wz/pv3+PP//Tf/zyP//w/7Hx/7/x/7+ycVW88r/yv8O+Pr/xDb//lj8/qY7"
    "Vlr9xf/+xqb6xP77/Pr+y/2px/87xf+n/E81qv/4//bG/vv//f///P/Ex/oJqf7/ycf+/w6op/4rx8X8/v//xqWoyvr///+kxDv9yf//zVOk+/unx/3N"
    "/zutxvz///8lwsbL/6nz////ETjwysP3////+sSU/rM5SOjtwAAAdGNJREFUeNrtvQdgXNWV/y9TA5u6adt+u79/17z35s2bkd90a4rKjLqsZsmybFmy"
    "Zctd2Bj3bmJjG1hsY4MDOHRCJwRIIBBaFhJCsgmQkA3Jpmw2m97Lbsr/nHPvq/Nm5o2KbSnzsotlSy6az5x7zz33e76nonKGPaHU4sUHF67YuXPnOnie"
    "WLcOPlp4cPGuVGNoun0rFdPy9Q+lgEBv77/T09u7uCsVCtEvL/nWus2b169Py7KITwyfdDq9fv3qJ3bunL+EvqzMZsrCon3+ihUrKp5ABOvXL4Nn8+Yn"
    "noDoeBiedeuJRqwZntna0xzTEG1et7B9MQQQcQw1plK3di1e3NV1ayp1TkKrmGZc1s16V4ziAf4fXv4Yf2QZIyUmBvWHg6nCZ/bsYDMjBHh2vrR370Hk"
    "u+LZZ5/dDA8sfSvWrZh/cDEsfOcUomnDJtR18LYn1uNShS+5OBtefnjVwxF4wrR+YYQwFEQDsdCX8B+IFHyZnI69a/16mcEkyDJ73rX+2XU7Ia4AUJlN"
    "aRGDYGJjMQyJZlGE1xpeWQQj+hRFjLBYaTbCJshgIBf46qDGLBgUtVCL0Vc3N+P/82Uvhsveztvau84NPBXTAcyS29bBO/30PWzNikQoZuDHSFqBJxKM"
    "wGpmf8IIIhgMi2H4r6itb7NpeWsWLRsS35aaGSNZXb/utoNdjWU2xcksWbhzHaw/seBsEXcRMYxs4AW/J5JWBUHB0BEjjIfP9AAdWvDo82whRDxmGqYF"
    "8P0sziCIZou4e2HWcNaD5xxnk2pfuGJETd9zDwYKvIosbuiRBUFQxyIibhuKPWp8uLPAE4nEZEXxiXzn4WjYomf8vGr2Zz6j8QI4YuSemJzG4AmV2eQl"
    "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"
    "IuyLAAAAAElFTkSuQmCC"
), "dover": (
    "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"
    "QmCC"
), "camhead": (
    "iVBORw0KGgoAAAANSUhEUgAAAKAAAACYCAYAAABj5uLtAACOcklEQVR4Xu29Cbhl11Xfuc655873zVPNc2koDZZkSUbyhKUY8IjtthwDiTsMsSEOoRMI"
    "Ce1OC3WSTkNIB4dmCDQQwxegVQzGQ+N2wLYs2xosyZYllaYaVPMb6s3vzvee099vrbPuO1XIYGHJ4QNtfU/31X33nrPP3muv4b+mQF4e37Jx9913597z"
    "nvf0ueFb3vKWm5eXl7e8853v3FUsFm978MEHf2b//v1fvuuuu+LshF75ylfm9+3bF4yNHU+Wl/fFv//7h/tJ8leacnDnnXcG2W/eddddXOmvdrUXaVw0"
    "oZfHSzPuvPPO0Df7N3/zN7d86lOf/p/7/d733Hbbbbkrrzw0PDc3G/zO73zk1o997P994LbbbpvZunXrG1utzs3tdmdvEiejcRyHYRjGYS7oB0HQCoKw"
    "lcuFjUajsdrpdFb27t3d3rfvQKdSqSwvLi6snjx5ZmV8fGR5fn7+Qq/XWxSRjcOHD3ee7+nSuV1E9N/K8TIBvrQjuPvuu0O4XhiG8s/+2T9/34kTx396"
    "y5Yte7/ru76rPzMzExw9ejQ8cuSJ471e/1dXV1f2dTrdN4oEe3tdGGUgcRxLv9/TWfbjnkiQSNyPpdvtyvT0tOzdu1d27dol27dvl5WVFfniF78ki4sX"
    "ZGlpqRPH8XKv11sIw+BCGOYWRZLzQZA7nSTJU1EUPP6Hf/iHJzIcEFr4lnPDlwnwJRp33HFH7vDhwypuf/7nf/7ar3zlK3c2Go133XTTq5JXv/rV7bW1"
    "tfwDDzwgEOCFCxfiUqmUm5mZkaGhIen3+/0oV0iWlpYkSZIgCAJelfi63U5SKpXkVa+6WbZu3abv5/N5efrpp+XRRx8NFhYWgueee05WV1fDffv2ycjI"
    "iPR6PeEaEHOSxNJudxKR5Fy5XHmgWMz/5h/8wR98gnn+9+CGLxPgiz8CiCIIguQd73jHxFVXXfVPjx079sGRkeHRt771be3p6S25xcXFXKvVSs6fP6+f"
    "XVhYkPn5+WRmZiauVCpBvV4P11Y35Mknn5SDBw9Ks9mEKKXR3JA9e/fIrbfcqsTEgLgeeughgehmZ2chaCXKcrmcTE1Nye7du5NWq8V7iRFgwp6H/X4/"
    "4LpJ0u8ODQ391szMzP/6G7/xG+eyB+dbMV4mwBdxZDfvgx/84DvHx8fveuLIE9fs2rmz9/ff975Oq9UuN+pNKRaLiLqgWCwoZwrDnCCi2+22/kBAvV4s"
    "/V5f/w4BQWjrG6vOIQUueP78ebn//vuVgE+cOCHnzp2TPXv2yLZt27iHXsd/UuKTXC6nxAhBx3E/bjQ2cp1ON6jVal+emJj4wO/93u995VvJCV8mwBdp"
    "3H3H3bn3HH5P/4orrpi44473/B9f+9rXfrDb6QVT09O9KIrCJI7DOE4SxGUURUoghWJR8nl+L0mpWJRyuaS/834hX5BCoaCEBtGUSkWpVMuyvLwsnU5H"
    "HnzwQRW7iOkjR44oh7zmmmtkx44dSsx8BsKFy6Evuqjm3lwXguZvvV436XS6cafTjkql0smZmekPHj58+JOqgNp4SfXClwnwmx8KbwCffN/3fd+3bd++"
    "65fGxkauf/jhr8Tnzp5PJiYmwyAQCYJQoki5jxILnI1hxIEo7ep7/sNnyuWy6ncQzPDwsExMjsnExIScOXNGHn/8MVldXVMiHBsbk+uuu05qtZpyUL7r"
    "BFiv1/Ue/EDIlUpFidp1wna7o3qhSAAR5vL5/MbU1MRPfvSjH/1l1z9fSiJ8mQC/uTHQ997//h95/9jY2M+ViqWhRqPRy+VyuVarPdDVUr1QOY9zpIFx"
    "IaKf48f/zivEBJfiVUWoxILYrlar+u9HHnlExsfH5eqrr1ZCheh4n+9AeHyP9yBI/4E7QoQQtRo2UFcSqxoQRVHcbDZzMOzx8fE7P/nJT/6b9HC9ZHjh"
    "ywT4Vx8Dzvf+9//wvxkbnfgQl2q3231wu163J4kYt4OYeGXw6lyQ4UTIe25YGFGoITN4v9FoSL2xIRsb60rAECHiFCgGzsaA2CA6Jz5EcFb34+8+IECI"
    "FoL0eXAdjOV6fSOsVivJtm3bf/gP/uAPfu2l1AlfJsC/2hhwvh/8wR/899NTW3+i2+33O51O0Ov1AnC7Xk+V/AFX24RBjCid4/G+/9s5Yfa9AVGCwuTM"
    "qICQeIWTQUD88DmIFO7X6XQVO8wSPZ9BDWg2GymhBfoKEbo6gNqHmtDvd+N2u5WbnJw6u3379jf87u/+7rMvFRG+TIAvfAw43w/90Pt/bnR07Mfjftzr"
    "9eKw02kHbD4cD53OuZqLOud+2ffZfDiaE5+/Zj8z+F2Mi/IdiMc5n4HV/ZT4EMMmcrNE70YIxMv8jCAvvo5/p1BQcR5HUZTbs2fP//bHf/zHd6b64Itu"
    "kEQvfP3/do877rgDt1r/ve/9ez9Zqw7/eKfd67Xb7TBJ4gBCYnOdALKczUWxE5NzLSdOF5VZMX3peyLxwDbNwituZPAax4hyCHXT2DEjA4OnrRzPDgeY"
    "oOl/SWLEyr/7/VhyOQymCI6arK6ufvuP/uiPFoMgaKeW8YtKhC8T4AsYqRjqv/3tb3/7yMjIv0GlA8arVMoBm26KPcZEogTG70YcJg55zwjU3ufVOZIR"
    "iHFN/3Fd0LlinKA/xhdZ0M79Lv2uGRbMYZNe+JXPQ1wuno1Lcs/N6zLHfD6PmhGsr6/vXF1dnRSRsy9gqb7h8deZAAfqwaVRHIxvdSRHKoLi22+/fd/4"
    "+OSHi8ViPo7jPu+zYZscxTZ8U+E3McemQxDgf87l3MjIGioQkgPSXMO9IEqMYgaMi1YnUBfhrstxv9RRMiBm7u/En4V7nNg39UD7jo9utztSr9cnIMCM"
    "Rfyijb8uBKh61ZEjR5ToDh8+zAoMIjRSYnu+Ed5xxx2B+1xfwhH89E//NHOLxscnf75UKu6pb2z04jjJmRfDDAknqCy84pzPDYtLuZsbGf45CAUCAvdz"
    "kb6+vq6BBs1mS4mYzzjBOEH69f19Psf3mZtzQr+363/c2zwxm5bwpdft9/u1OI7hgC/J+O9GgIizq666Krjjjjti/KZZIgOjjeMk+PjHP17+/Oc/P9xY"
    "btTqvXp05MjRXGdjQ/Zfub/5nd/5nbMf+MAHGocPH34xF+brcV30vt473/nOH6vVam9rNTu9JElyUZRPrVwzDly/cw6Txf7YbPQv1+sutYrhTsa5DA90"
    "Ec3nAKQhuo16USNdIFau5SPLxeyeNhc3UvyAMPz+WS73fAcHzh7D4vv9Qr/fhwO+JOMlJ0AeBO7h3M0Hirz/ft11103t3bt3fxzL1Y1G4xXr62v7b7jh"
    "hq1xP64lkhuRJKlGUT53+eWXyeWXXx7XhmqdU6dOn33zm992pN1ufOJP//RPf+s97zkcHjr0BASknPOuu+6CyL/uot11l35qsIcp2j+QPZdw3fiNb3zz"
    "q8rl2k9DH/1erN4NF32+mU5Erl8xsuLSRLXdwgnBAWK3hnnlc/4Z/s59MA4AocH95ufnVTyjc2Y51ubAoICrodvpYRZiENzwYbge6IfFD1AWfwzDUH3G"
    "7XZ75CWhPubxUlwY7gbBHT58WLnb87lyPvShf703DHt3dLvd76rX61eePXt2Znl5KcAHunPHHtWVOOW8drvd5Gtf+1owOzsncJ3l5aVyp9sZyeejQ71e"
    "8u5bb33Ntffd98Ufv/RZIMJvdLARv/Ir/zD/6KNRsdlsloOgXMnn+9WlpaXaxMTEvqWllbtyYW642+n0RQICRAdE5L9nuZtzFRexLgadw2Wt2CxR+ued"
    "cN2qdi8JPBrX28bGxsCgGJyiDHgN1zPiM8yRfxs+aIEMWQ556fedGP0wIIa/0XV8oeOlIEDE1UB/+7f/9t9Oraw0x1ut1YlKoTJxbn5uaPHChdd88Yuf"
    "/Z5yuTyKeEFUnDlzJtm+bVfz9ttvb46NjZWazVYun4+gXwgvAOpYXl4OOPnVWjXpLLeTbrfbf+aZp6NyufzDd9555+LKytp0p9OdWV1elrWNjQQDLwjC"
    "Xr/b7SWBxGpg9vtJTzlCP5ckUghESnESl4MgrPzO7zxbEQkqQSBDhUKh1ut1yuPj44WNeqMoggXbBxsLnYicw+FxcK7nXMmxtqzo9c+45ZolvKzFagRj"
    "epmLZRg7npUktbABofF4cM00wuUibpudo+mDnYERlNUb/Rkco3TOa14R88S8lAT4YgLR6HMhBsF73/veV42Ojr4nl8vdGPfjy3o9GY2iqMSpBYPiYTfq"
    "60RvtKMoIv4teOqpp3IL8/NBbWgo6OMv7fWIxJRmoyWNRlNFRj6fRycJVlaXAxB9gi337dsrBw9eloyNjoenTp2R06dPqeXIBkAMLKQr3b6gLgpjIJO+"
    "6VyujDuOhuJfG6qo87+QL8ZDQ2gCSeABBWyMB3qOj41JtVaTtbU11dFyObN4XeeDFSmxZVxrztGcCC/V4/zvMa681JcLDGMY36alyjxdH/RrOf7Iv90Y"
    "QWUolYiCMTgIjohnxEWwW9vOebkmgbH1ej3as2fPz9x7770/leKAL2r4/ovBAZ3wEojvlltec/sTTzzxyThOiq1WUwqFkixeWJZDhw4lO3fuTFZX15JT"
    "p04lnW4rXFhYyLdaLQ2M1GiPiVEePJmYmEiOHj0anDt3VoIgkpGRcRkeGkrGxsdkfGxcSuWi7N1rcW9s+gMPPBDcc8/n+yvLqwkiG12JyGIjPjwGoepQ"
    "5pM1PSzBe5ByGhYbooljgjQ3FAaZnJwMRkaGdGMq5apyXq7X6abGRL8vlWpV3vzmN8tlBw/KY48/rvF5hEM9/cwz0sIlhu4GplYoDIgiF5qhwdFHkYTg"
    "4U6oFgFcLyUaDRjk76lYNaKzvXeL22Ed5nYp5ueE5X9D7MZxT1/dkuZMEA7mwQ6sQafTHhxYH+12GzpJYDCHDh26SMJ9s+OvRICu40FUiNsUBgnf+ta3"
    "3nTixMn/u9FoFkdHRzr79x8Ip6amk8/82Wdzx48fD1ZWVoILFy4EcJ4oMhHjYC1+TAgKJzvMb2xsUhXpAwcvUwLZtWt3UC6XA+Lhnn76KTl16qRcf/31"
    "ct9998ljjz3GZ8LaEA76nBQKRQlzgeZQOPezE2+QSdZocM7DYUHZRyUglJ17EuBpkSeQA+FMoSTCdWNlA2/8ju+QW269VX7nd35HPv/5z2v08tvf/naZ"
    "v3BBReRll12mG37vvfcqN56Z2SKnT51RAoKjc32Mg6mpLQqzdDsGRHd73VRfiKXVbkoBf20OaMC2O2t4cOCcgLIGhetvPL8RH0aMhXc51ONi3jBDO6Rh"
    "GKVrousVdLt9mZqa3vWjP/qjU7/wC7+wkCG4FyWH5IWK4IGY9Ynceeedk1/84hf/QRRF35PPFw6FYVTi4DabTQVoy5WKlIsVjdoljk3fK5d0E1rtlm76"
    "tddeK3OzszI8Miw33ngjHE03BC42M7NVTp0+rdbf6OioPPvsszJUq8q2bVs1ZP306dP6voohlXKBRGkMXT7Kp+4mizRxmITBJjDYQIgFDsz9+B1V4dix"
    "Y/odNs/j5yAirg2nglA/+MEP6vP8p//0n5Q7XnXVVXL8+HFZXFzU5xgeGpJXv+Y18vDDD8uZM6fl7W9/h8yen9PrQti//Mu/LDfccIN+d/euXfKZz3xG"
    "57V//35ZXlmR02dOyczMlAacXriwILnQLGTX73hWnpv5ulXs6oQ/r0dGe/SLEyD3Ye1vvvlmjSX83d/9XZ0neSnMzYm50WgEW7ZsaURR/lixWHh8aenC"
    "4U996lN/xNq9GAEK3zABZm9244037rz++le+e3l56ZZnnz16Sy6X2wHXMfyqo3qaR1kEEshQbQTDQR8K7sKCc2oRPYgBFkmjc/vmKOdviFYWaeHCohw/"
    "fkK+4zu+Q171qlep3nLq5Am5997PK/FBONw3FwLg5lWk+GK7Eu+eiFSP1E2AgIaGalIqlfXzDDaSQ7K6uqqRxnzGo5L1eUKiRfKSS4HgH/7hH9aD8TM/"
    "8zP6eQgcYr399tvlwIEDcv/998ltt92u4fKf+tSn5Cd+/CfkU3/y/8nMlhnZsXOn3H/f/frZX/ylX5Tv/wffrwTxR3/0R/LOd71TSsWSPPPMU/Kqb7tZ"
    "fu3Xfk0eeOB+qZRLg9Au7uXeFZ6f9XKigbNBkMzfxS3P4ciCB6fyeQ7dt33bt8mhQ1fKxz72cSV2PyAwibGxMXJKVFzBFIrFQnf37j0/99RTR/7dl770"
    "pfVv1j/8DYlgch1S3C73/d///f/T0NDQT2JxHnniGZmenpKrrjrUm5ycCuIkCdbWlgO41MmTJ5Wo0MEQM4gVjAaSZyYnJ2RycmqAd4W5nC5Wp9OS9Y11"
    "FccuJt3Cg6uAf3HNVquh4u3QoUOqXOupzhFWlDPiSK1H7g1b9I2xaxE5YkaHu73gzoh2Fhjic09DxgocELMqb6kx8fGPf1ze9773yXvf+175sz/7swE8"
    "AkdHHzxy5El585vfou9PTk5qqP3q2rrsP3BAlpeW9T3lrrmcnDp7Rjnf7MK8dHo9OX7siHz10a/Ita+4RufEs7il6iLYjQ2PmsYq5ncnMDdCsq5AiAsu"
    "b2FZkR465v7AAw/K2NjoIMUTlWLfvn3JW97yluQ//+f/HK+traFfE6gara2t/dSOHTuvfd/73vdjv/3bv33s3e9+NxmACPIXHKjwlxKgJ9rcfvtb9m3b"
    "NvGr9Xr9dghs9vx8b3JyRrZs2RKsrKzmNjbqUq6UdAEOHrxMioWichNECZbazp07B+yfdEIVZ+qf7KsuxAkm6abRqA8sTAii1e7K1i1blCs+/vjjeo3d"
    "u3bKvr17dSM67Y4Sd7PZVgXfjQ2HOrC61aLs9qTT7UgTXa9DgEBH6o2GEjsGA/MwULin1jF4JCpCMSkqFzGvglmz7olATP/7n/1ZFb1bZmbk3PnzKoI5"
    "JK997Wvk6quuki996UtCdlqtWtVNr9fXZevWLfLMM89oWP0b3vAG2b5tm97jkYcfVh12x7ZtcuSxx2RqatJi+BQF0GDRgQ7o8/D8DsSmh+FzLefqPlxs"
    "o5ag01arQ3pQWTs+jw48O9tSjkiENftFht7dd98dsI/j4+MBDIRsPqzjMAzfcuHCQjlJku8+fPjwRmqZq9Phhfjp/0IR7MT3pje96cZisfyH27Zt21mv"
    "17tJHOcWF5cDxG564wHcgQWKmDIRNzTgemwMD8WYm5uT7Tu26sZxAh+4/wFpaTaYWapsIIRhgZ2JLhqbziKjs8Apev2etFttxeAgXj7vIK5HhnAtjzbp"
    "EyPXA9IgJN7yJtwAgbgdfvD3XUd0MTyAdAIIwQiSH/dUOO4HR/MIaAeo/bCpFd3pqNi2DZ/Tzd6yZWvKMY+odHj3u9+tInv3nt1yzdXXkFesa0JesIVS"
    "6aoPoCMXxxzOU6dO6fvuvnPuyJ4gJRynNC4vsnXbFg3rR7rAtS1cq6d7xcFBz2Z92CfWOX22hPdGRkba73rXO/7lvffe++V8Pn/2E5/4xKmMbTCoBvEX"
    "WcpflwBd53v9619/RavV/myxWNpSLBa7Y2NjEYQA8UU5GCgeAdtMiyMD0iCLq6QEyGJAfHACCAM9RDcvChDdcubM2YHf0zO43MXFAPZyj8iBA/tl//4D"
    "eh8+w+fhfGym50P4gch6GlxUmX8VIkytTXVxWcg8xOsRLG6lMtgw/SkWlCuargk3tAQiw9TMK+IGgIt8d81lDQe+6yKS3w2ztAOs4Vwxlm9bOR7XZS6e"
    "18G8ITw/aFns0AFrCIP7cQ/2YGB86L7Y3vgP9wBbJMn9ta99naIJn/3sZwdzdCzVn4dXDry/gsseOLC/df78bJDPR2fDMP+5OO587OzZs1+45557Vr4R"
    "Q+XrESDvB2984xvLs7Ozn+3345t6vX43DEO8Dqr412pDMjoypvoEBMnDQlycLIUS0ng3Jstn+B6imEQa9MOx8ZHUx6m+Rn0w1/sYzpEg8Eq5osQMTIM+"
    "xT08VInF9twHt/xcb3ROxHDsjM2VNLJ4wB0zIfJOlNmoE322QlGKJQ4dQQCb2WuuJ2YhEL+fu7vct+uWp/thDbvb5A+ONRqRdgYH0edE4KjFBF6cS+LE"
    "BzGTGcf1PZmJwfzz+YLO3fVBPyxR3ogcbkd5DyQJKpHnlyB2/dl4HpgB14Zbwjm3bdsGvDYwwIIggU6+KiJ/uLi4+F8//elPUwqE6g7Pywm/HgFyxPvX"
    "XHPNL/X7/R/p9+NuGEYR8IkTHDoEllq1UlFYwgmCRVWdp1Yb5C54lC3v8UD33HOPPHfyuC5Gljs4mJr1myLyyuWKEh4P7AsM0Tn+xQZxfxaK9zAqgBP8"
    "+s4VmYfWVxHjVk54zjEuDRZwnAwu4ocoH5lOmHVnOSdyQtjkTNnPbXovnFsiQdA3CVjNemMYHtJv62NRzv3YOaBxwazVi4iEAWT9vMzD0IauohH5PCC9"
    "4YaXX345a5ScPHUiwMhx9cDVBYgYo4ZX1twPE9b+2bM4CAJd461btyagEZ1OJxkeHk6KxXyuWCwqCpIkyTONRuOff/KTn/yYcpJMiJ2PP2eEuN534403"
    "/kCj0fiROI57uVyUMzO+pNyIh1TAt1hUN9HayrIsXlhUaw09gY09dNUh1W/QM3xj+DsLumXLFjl95qTOIZ3owPXkm5t1UWX9lI7luRjKurQgQhYDi5aT"
    "zCJt3bp1wJVdVbCoZdtAJyTnmllu6BvMBsK9+dEwdhwZXq+FlU3zK7LXcx1ScclU37LcYBPhKilSozEboWzEZ9EwA0mQWMAr34cL+vAD4pzTMT9TEWxA"
    "PKpmYIR1ero2u3fvBnpJuM/K6pLMzc1r4jt77M/PQLKxPnyOOUJ8SC9P6UzVF/z0/C3gEJRKxWR4uBZHUT6p1WqXVau133zjG9/09v/23/7ki8+HG15E"
    "gB5y/rrXve6axcXln+/3kziXi8J8vhgUC4ghWDliyFL6IK7nnjsp5+fmpFSqyOVXHpK9+3bLs888LZ+/57PS7bbkpptuEpz/bAQGihMOp8cyuEzU8Hcn"
    "NBeltgM44S2iwzbbdCPnbrYIxh063Zb+FAqR+nHxIXOP0bFR3QC9RsrznUu5/uaEdOn7zMvF2YAw1E9moIMTUXaYj1W9avrqhMLnw9ymAeP6GXAIB9qJ"
    "U/8NEQWJenQi9VJgfWsCud7YiYz5soZwaD9UTjB+IIzgc1KplqRRz8tNN90subAkswtngse+ZshCt9OTfpgo1hkEpg9n8ULXdxlO8MwfsY3EQSQjlarV"
    "bcHS0ir+fYi/d9lll42Pj4/83IEDB77zrrvu+nO4YZYAMZ/lrW99a+Xo0eO/liTJEGI4l8uFbgS4VwB9aHRkVJHzp55+RkqVikzPlFW/WllbVfdUo16X"
    "rz36FXVPjY1OpuLYOEe7bea+cy8Xh775WeXaiRFR5fCHiyenJvytWLm8j6hmQcANmSebD/F54IBzP4ZDGVlu6857hlu4LKaLTSdURFqWyzk259f14fMf"
    "GEXpc/Bvrusc3Tc4C5pzfS3hkcb9+f1cz3YRy2c2XY4WYKBn13GbdBjAXEH0E6glS0uLKSbaF5LozSceSpTfTNf068Ll0OMB2NER+TcSAcJzUY204XfH"
    "IzudTu7UqVP9gwcPfNuBAwf+5dGjR//nS4sfZQkQGd0/efLUfxSRVwVBQE0TFb3ULXH9QnW86Sl59ig41uNSrQ1JPoqU+tEN1tZWZX52TioV2Dfo+apM"
    "jE8PNsasNEvgcctViSQVO5fqVoPhESW6sOZH9nBzNhXGsL6+oSKG6yEOKlOmLlhouuljWQWeDXIoxTeMTeKznuDNHNlw1wMdX3OXFpvCYP7+45auE5Ub"
    "O6yRh9n7xmbv68TIvV2F8MPhxAin48d1OTeWBgcjtcyzRhHXUIs6TiTSAId+0GrXpd5cV52ca2XnT9ygBzHwLI5cOL4IDMb8OOjo8zATiiJBmB5Vw/UQ"
    "4ezWxkYd1+xPvPnNb/7q4cOH786KYiVAp8pXvOIV39/pdN+fJIkSnxOdcz4WAQ7DRKjKhE7oFm/SqOtNG82GtFlosDXB5I9U7Lh3AcIwQjDMzzmNj03r"
    "d1Npt43ZjHdzrsI8HDohrIpoGQaLRtFG3nPrNwtdQLBZi9uH6zsuYrC68TNj9bvew7y3bds+IFJX2jn1eHmYP5wBPYtNunDhguphWULjfbf8/RBmRZwr"
    "/M41Gcyf75meVVIvih+MLPdzMez34/lNBQgkF+QUeD7y5OMyNTkpFy7MD1SQAQzE3qQqjxuIHBxfV1d/uDd4JsTHnHh2nsV90xiMEOjQ0DCJ+vHGxka+"
    "0+n8h3e84x2P3XXXXU+6URK53nfLLbdcv7Ky8vPsdRTlA5KTuZgDme5HJAjgoYce1sUYHhoecDYDf9HjetIjqiMm8rasUA1aOzoI1wKE5iFwubned6mo"
    "YGR1MSdSB5gRE1mrkbCmHh6KuK/hWugx+p2gr3qXE2zWSPBNvVREsnAcMn7cQPKAU+YEZ2fxWXSGx+N5VYJararEccsttyhHgADwOZ86dVqeeuop/Q5c"
    "06J+zO/tpTT8QGbXw3+HQPxw8jlEH7GK/FyKQQ50zkzQhX43Iec3p3swN39eYZkoMmdC9lC7ngqDYa2dmP3VOSrX5IDyijrmnB4Hg7lMWxpEIRKH3W63"
    "F8fxjtXV1X93xx13vOfw4cOajR+h97397W8fOnbs2K+LyHAguV6hUMwVVfRSNoyEGCNEiBBIRMVcLpK+7nOMrkytCukR3CmRdPsdGapWZfv2XTI1PSlx"
    "HxEQ64SwhDk1TDArLrJcKPvATowc4n6/K4iOQp7qTnghqPxpokWJK06kj5Wo9gqWQqjArotsxdxSvcg3zRX2sZTwKuWywkpKHGmVg6mpaY3g4fuuI27b"
    "vlOJB2OKg4Fb7s1vfqs88+yzakB8/OOfUG6JXnTmTE89DVlr1zmyrWl5wOFAEdhI32Tn1C5SHVHg++BvDI8G4rOuH2YtcyNcAskgJgJlI12rHCB6zg57"
    "Hj+5+80lp3/nG4SVm6oSSQ5DplxWDgxXr1TKki8o3KIH8otf/KLSCcEXPAPP5oeGejnkODWbzbf1er3vJvkR5ocIjp977rl/1e/3r0f0FgulHIg/1O+E"
    "xwIZ9BIZHlap2MIMoIhEiZA4uX7c0cnhbL/9DbdpcEC/11bO8dxzJ1JT30rGOmfLGh1ZrpgVk5xeVD8L4c/rAvWU06WiOc0Cy3JODToQAkABcFlOFtMs"
    "V4iXRVWONz6uzzW4d4oO8/xY3bzfaBB2z3fM2wN3Y02oSMqAA65vbCiBDA2PKM62uHhBAybYEOAhU/I3IRLfHF8LxDnPx2bCWd1FmDU6+KwD8RAZRAgx"
    "gr06lOT3yEJaxv0JgiXo1Y47+COrAkitQRocVkmkkAcqsnAt4gE9+y/ogwiwDlZVgfWgZiHX4SDC+YFquD/raURaUaPTzfdms0lqxfvvvPPOP77rrru6"
    "0RVXXHFDu93+R0EQxMViMcTF5vAAp949HCyeQxaXX3aZhkPlKKJt9R3UCNCTFYgsLizI6179Wjmwz5RVrtnutGVxcUlFDxWefHFUOU4rR2VPu3M+JyhT"
    "zJtq6CA6UJRdJCuco6Fd5EfgibHsf8PNDL4hUCEbUQwnR3x5yNLASk3jBu1wGPdEj3PdxzkT+iGWtn3ewv/ByJgTIg7uwI9BE7guCxc9q4vUrLh0fRXO"
    "wcFANHNvXn1PHKry7zlgDIGBr2aNGzeoBjplCgnxvkMowFyI80qlptwawl+YX1QJgIHC5/C5oztasIa5XW1/+gMYivtTMN2NNoiPZyQAw+6vhl3QB08S"
    "ec2jjz56nYg8SNbP23O5XDWXy/WJKib6NuvAdhiAB+V9xC+hULt27dZTTZSHsvBCQcXuydOn5HWvfZ3cfttt+hAsCCfsySePDDbA3U/uk+Sh/PRmjQWu"
    "675aiAzxxN9tfptuP+7DA5ono5WGdlmtPA3JSrmjZSUlMj4+pmqAuw5VFUh1LA8mMDdeop/xe2LtT89MK/H7JrBh7vJzDsrfFJDvdRQn5X2/jnM71sWJ"
    "2sVr9tC5fgVRQIQEGUCI7ulg+CFm7fgbNaI5GNlDbRwTrhuqxDJxmpMf+IHv17UlNwfd9G1ve5uqCdxPdfx6XV554yuVG8NlP/pHf6yH0VUQO3hGgOwH"
    "/2Zu4ILMhfu435i9qdfJB+rhIaGKWGlhYeG1SoC9Xu8V5H/CCZTY8nBA44Imww04dR1Qw5jqG/LmN71JPv3pT2vIlXKFIFBnPYGVVx26Spr1ui7SyNCw"
    "HD1+TAmXE+Wn0hfdN9IJz993uMIX2vExfdjE8Cy+Y/oS1q6dSncp8TkGDnzEDoYRRhGW8hDQUXrQjHgtKIBnZp4MCAiuwCKyDm5NLi4tKidmo9hwRA9V"
    "Rgkj45rouAZF9Egg1oN7qV6m8ihTkcCJ0bkaa5JdHzaV+xDUwT0dsM5+hu9CLE6Efk8D3k3d4TM8L9Yr8/+t3/ptLXx+6623qmT58Ic/rJHc73znO3V9"
    "77v/fvnKI4/omiQxxLcZjsYctdh+QE1E3wOzuB2GMogr1kNq6osFYqRow6vvuOOOn496vf6eRmMj6PfjAJFUrUZSKuXVk6CbFJnxAVEiYtHp2m3rUfF3"
    "/+7fHUQCw1GmZ2akXCqp2C2WSvrQTz/7jIomxNCAfaclay/dBAjKLUMn+ixH9AFBsclOZM4pszqVQgK4u+JE2hbZKzu2b9eQek4t+hqLxWmFQyoXS91z"
    "JBzxzEuLBqGsLC/q83CtxQsLepAe+vKDSszPPG1uv+3bt8nc7HmFbEZHhlPw2vBR/s7IgsrOCV0K+EF0EZqFU4yzJ4q/YXBg8DBvL7fL4PNci80mzGvr"
    "lm0awu9r7IaYEz+qCpHQG/VV5VzgtRh3eES41913H1ZLfv++/ar+/OZvfGRAwH4Ny9Kz+7oLL6vPQ2wcZJ4JPRJCzeVyAXEESRJcUSgUpqOhoeFhyHht"
    "bV0VzOXlFV1gHpRNY0EBfBHNQDO43OyC5hKD5XPamIiLSz6vOSBnz8rihQsD8TM44Wq1ms7Id9wl59bfJuZmIthFjXK0FDv0uDVX1H0T3FugQG2rpQeI"
    "fAsOF99FSe56ZlwK0CoXRFVIn6NYLivRjIwMK0eDCPm34aCjyhF27tyhz8j3Zmam5cSJ4zIyMqrS4fTpJeVYTlSspRcc4pXn48D6ejgnu/TffN+tdV4h"
    "ZogO75L7vB3w9TViX9bX1ulJM8ArsYDzJIGl0eMWONKQL933RVldXaEdmNx0482a0Xf55Vcqs0G//ZM/+RPllN/7vd83AKvNmPEDa4nvPm/XERnsqUNU"
    "ECieFtZveHhYi3v2+/2p1dULW4Nrr72OcJkd7XabKouafugbwybyU63UABQHkTBePDurQ3ETR9M5ndzc4/qYoF+L37GK0D3YSGPPptg6t+PVw7n8Gq5H"
    "OaDt3I/Bprr4dV3SNwbCg4Dc7YXFFhXy0ut2zQeaekkgpHanI8PDQ7KwcEG2bd2qmwwh+Ry5DkTHpmBoeOqnBtimug8E6+minH5+597MB8OCZ/WUA8cD"
    "/bmznMwPtHMWP9yumrBeHCbmw9q4oaMguzqGQuXQW7dYMIYTKJ9ljyG6669/hf7+mc98Vl55w40yMTWhxto9996jz3Pw4AFdr/u+dJ88/dTTdg0YDSoP"
    "+cU5U3nciOSVZ2ZO7klxsc9am2cEZCcIoyhqbtkyfUdwzTWveDqO48uoiEnQlm+g6yG2AOZ9h7OBcVnWWXEgnj1UyaOHWTwPA3ILzKEBTsL6+po0W3W1"
    "jM06tbAhX3QXpc4ZXW90XcnhCl/MLCEZd7YQIjgPwxdI825NfqiY9e8hguppbvLy0pJKAA5HBTUCd+LqqopY9CT+xlyZG8/LggOBeFISv7uexu8o9gxU"
    "FoiTZ8FahSDdbcVcXc9074MfSkvk3zyQ7p/2Z0Lv4978m/kYpohObnAPc3C/u+8t6+PgukFrVTuYUcGMihKqi6lDRDshGQqpOpPlyt2e6X6sOc/FXFg3"
    "DpxzRd7n2aCRwT4EpAzkgz17dv3DqN/vPZgkchmUGYYhFZEGFg3DxSHDT5KyWhKuI6vM7mzZXVj8nd85JcrBMtWa1GJOQW3XT/gM93Fu564qV1hdlLm1"
    "zELyGYeGXAw7dADXg6iYQ6lcHhgaHt2hBJ22rvL7liplPRDDYyMKbI+Oj0mk+RgNmZqaUELjs35v1BN30Lvfls0H0mDD+V1RglpNPwuX5HnhqPzOMyHy"
    "mKN7UdgkJw4nRD7n0sAkjOldLu5gBHBWdDhUKEalbLnMfNejVFyVcf2NYUQS6HfB+yB04Kkk7EuP4I6uoRgR8BqYYZrMj7RgLpVKSQmWNXFfue+9Sxb2"
    "yJGFjCql+Han0xmO4jh5oN1u/j1zEZj15UCnm9dOKFkOpbhOp5WKrpaeBn8oPo+Ic3CYwEuNTLGGGYMF5XNM1LklD+U5rvzO313UOhSiPNyd6ymhO2w0"
    "OTWlm6EPn3JqIBOzlq0OMyfdr6Hz7KW5IWmKqHJ+AG617EOds59cCAtChAtCNNzHf3fu7MlBiG24HtcDQoEI+SwANgMuCHEwXEzDPdhIC3iAEXiFfUr/"
    "bhY9t4NpjMJ0sECGh8FX65qegM1bKlek1WzJyPCopZ4qnJQC8gCCCkhvJrLt2TMjQ8ND8szTz0i725XhSlkPz8ZGQ9bX65RKUanhhI/BNjE5rtYyawEI"
    "zd8cgnFCZ28uRTwUQbRI+HJULheP1uvrtBbItduthMx417P4UBZC8LAgxuBEBaIGCma2meBp+VcCUfXfVodEH35QbmKzZcFmZXeLP3Prz91TDjlAkLBy"
    "57IullkkFzMoChCzK8nGmS3s3VI0bbh6YZtnxhRlK7TKaco58P1x4v2azAMRquK6Xh8YVhAac8oSJcSGiIOgeCa4HnPBYe8GHqKZNYRbI7KZAwYfBG7h"
    "TAace0Wrwcan6QNOgF4S2LwPZf13o4l6Q4xgVQmHOQ4BQqf1B9EPNeeC4IROU3bs2Cb/4B/8j/Inn/qk/NN/+k/k13/9N+RNb/4ONeLOnZuXez9/nwSF"
    "ovracxrc2pVSmtgPw/BIdyA51/0YDnENIKGLmIeqFZUon8+v5HK5dr/fr/D3OI41wpUv8cqDOVE4ATpHdIvTRbPrZL7Bfgp8Ar54DtxqMnraQ8PN+SyR"
    "+8nJYoPGtXr60Jw6NpuhinwmStnes0KrDtP4fOD0BneYF8agA7we5qXSn1RMcy8X0xwACIt/m4fHQsoQnRCbK9qe1QeXY4PcY8K/mT+iGU5ponNlQMAQ"
    "inNStyDd+DDpY14XfnddzEF9lxCsixmARECnUSxhqPOtDeGd4EBuujDdQORZmCcwG89DNA++XcqK5Atlc4XiZk9dqIYTE+rW1kPJ8MxErsnBQ2Jk3Yi2"
    "/q7KKTZZjYrFYieKIlI9U2vMQEunXsd1GFnII0tkWfgg+7uLSt941xWzli3vuXLMcBG0qYRvFvhG78QAUr/jxMTgRPv1EfmuEPuhwAPg983Ow8Vqluvy"
    "u8M7fMd1TtbCF5VXd7T7KwTHYntTQa7DwYCb8TdELJuDsQChwPWYH7og9+MgwfUc9PZNcvzQjTKv9ec6se9N1mBkLRGL5kumpC+poC2VuBQ4IJmMRogW"
    "qW0SwTMZqWuDCCe/mWoMFF76V//qdfJ//Luf06AD6Rosxv0sOioSScyYY414bqQE6+LJY5uGh9EVz4/emhaJKkV8iUJBcWyi09yyEMVmvgSLfqkSm8Xm"
    "sguSHc6tsgTmAHP2O1m4xvU5Pucb5lYyGwU8wGdcJHH61EuCr5pw91Skco6IwiFwwUPY2QwWjaAE72LkemSzaT3VHO+DGOAcvMdzOPH6OrDgzMOxORdF"
    "bph4tA8bAXHB6eCA/J3Pcl23fnlOZQdVrFHSTSEc4xRcZ/OwO1RlgbW+hozsejKvWg3djMStpq5L2CUS3QBhOJdy0UxOytGjz8qv/8avy8/+7M/IFZdf"
    "rlFHKyt4rwhvSxPdSRHop6pM2uWTV0Qz+Cdzh/g8cSwLLznxsX6pKcCcc4hgjQnr94EmWGyQ7U1qdfHrnO35iNEfHkJwbmMi7uKw9aw1mx1OzP4dJzC1"
    "CJstJZo9u3fL6OiYcoFcEEq5aqmSLK4GJhDFm2aADerpUbsZbxFzyYV6ivk9LEQyXKwq8h+V85KvFqVcKUq/25N2CjqrmE19mpeeYlcJWGyPXnGwGiKC"
    "KG1dDe5gYxC3PD+iGl2P70HE+Hm5FwfJYRkzvAzKcnzVdV9Ololicz1eWi3BQ8YicncioJSWBhNgUAU5IsNRIYgBtPA18p1PnT4lc/Nz+gy//Eu/ovO9"
    "9tprpNXsym995LcligJpNQ2I1+gmjC/EKzV+kkCLTwGtsQ9u9WbXzHVyh8hMiih8U4jCMFQfPWEsYQgX2QSFWeisV8LFm1vHTpSMrOh1QuQ9t4KYhPsC"
    "ed/dSww7FZ49tlk+jQ1AH9m/b68uGocBV1+PYjz1DWktLg66QWKh6bFJROPW2J4ctj7/UZINjli3exGDdiEG6wokycUSVSIp50sWdpa2UdVnSkFbNp+f"
    "rOrAM0A0zNGBbggL7oY45n0nUEcPEE9aI6ZQGIRzeeYZItOlgynypo5oRYTUeDN/t2GyWRXI46v8AEOEHK6krKZGeghQX0yEgsUC1VAlguclEAGvFdW8"
    "vvCFLyr8dOTI0xq0wTMDSPOsdObUvSKolnYTqqbE6r5rt3vS61oQ8ubhsHkOwH7rVTyQKCr9SRo2Q8PKU+S0pNmmoutuNv+i5w/4xZx7uWHC5zz0yBVq"
    "v4bjev6+619ZQ8f/xsJj3eJfhmvVW9Y1sjnf0AX0E2aLjsWdilatsG/8NYabhxaYyvyKnOBCJPleKO1cIG3KLvQSSZo9WdlYloULC8opmK8HZ3g6Agcp"
    "Cxc5hMQBgctBdGptpiHqWnQozajjWhAfxAYH5H3XkVD8nTO4B8gOqMFafNeNNd/YrGi7lAOa/jUur371a7R2InNm7hSeBM/zPBpNZEpdc6g1pDCcP39O"
    "/od3vUsPOfMivIrv7969R6tn4dP3SPDhkRFVK3gW8FOuz55USgDhm23CjMo220q4upB+JhcFQUEZBXqB+VlNz/DT5NwsO3jPrSe3xpwLOm7HqwOUDHfx"
    "2QncrILgFqoTsCv/EB/XUEW+0dBqo+R4wN2GCiUpR9a2lH8TuU2wAETIxis+plVQ8TNb3ZhG3XJVOr2OLOOLLoaS5AjDChUeygWRErrnqqCX+RrA4Two"
    "l43j4Dg3dKuYjcK4wA0FcUGMLDyH0bFDr7zlAQq6YZXKIIhgU6fb9DzxLA5FEYXjItaJ0NADS7gyr4a1YoUbe8yi6V99aXcI4CDQlGbWzYHOSZUvMw4K"
    "MjE+oUQ9PzevRMh+LC5eUOJjPVhL1sLhLob5ei1qyFQG602c1Z2d8LIjCIJ8FMdt4vVDTHMlPDYlDanxBXG4xUVBVtxCJGaNWeydi1LnZI61ZbmcW01Z"
    "duyn36NoOfVsZhgnUitXZWpyzP6Whswroad5uYhZEJdCuSJ5yoNoRG96SAp7pITbMMxpFazl1RVZmJ+Ttdlz0lxflfV+Vzb4fhToZ5DVGB+Sp2qBavdK"
    "QGvra6pzIqZqQ2SsGlLg4KtDMRgaWLe4ATVKen1diQHO56kIzM1TGVkDT2P0DTai2ixGaV0xMSJQBSzDj7XerBdtc+FAEuFSrzeUYKhixme574XFC+o4"
    "oOIqj7W8bFYrfz9/ftaCiY1KVMeGGMl6NFBcNOfDk5PcVekE5xXJEPduM2QNpOcbVsE/NhGMMPeTBTrulOtUyyI7Z3M9jtg/IpM11i42PyK/m3WZBoIK"
    "gZjlQetQhxMcPnCDxfVDNorru9uLEzxUqapIYCj37LSlBRiqNVLMW6EiEwuy35ZWty/SDVR/a7U7UqcwerenOSu4Die0nsl22Tu9RfrtlswtzMmFlSVp"
    "LC3IUlyXBsV7goLkkkgi6krnREJEV5JIk3svWYjRxOSkzpcBgfAeBwSugQcE8eSuQq/2ymdcNLNRnvDuViMEqxa9YrBm/bqPeG2NRG8MHEvZxJrFUGGt"
    "rTcdqMGynDt3XjFAvC98zq12iLC30lFdOUrRAiQE2CCcn7WxMDmOs+iaGYHyphWJYp48s0N0HEq4Zb9fUJjHjFfvk/eXlQpUV2EuCsNiCBFawo4ZE87h"
    "nENlLVuGZsxFNEkx1m/1Usxyhnuooq/wh2j9vpzCPGa5+bWzPmQ2CrHl1iCizAl9rdmQtYYlhlvSTKiL6IPfQfghNAeClVPWajI+Miz57VtTOKirGzQ3"
    "d06OPL0inSSQ0eEh2TZclYloVMZHq7JjpSGNtQ0521yTlaAvDWrChHnJ9RPpBLFUctYYppfEakQgUlEVPHTdSnck+n4WKoIzORHC7Xg2VxUQZXzPy6lB"
    "fO7Oyop7N1ao8WM9fa1RTbttOi4bT+T5448/kYaSjcgVV1yhBwIPzJYtM1Iumj6JKkLSGd6fOK5JMY/3y3OzgahECkUM0s12rhCgA+/snTXMtv2Hs3ql"
    "rTCxvR7sTxpj6cxsk7lZpGyUJJ2yGaAAll2DLFJHvcMNLKbhhZbHrkpyn2AEy3MwqjcLh8VVwkuzoiBMt+7cCHFPCyydjUBcuaOfe/pG+kYpdJKqBSZu"
    "7QEvPRguzrxaky4OoVqUzk3rFY6PT8jU5IQsb9Rldm5eHjxxXMq5SMZqk1IdrkhpJi8H+jWJEbsbLTneX5O1UiSVqCxBQjmzWEIJB/oT7ifliBMTg/As"
    "7ut6rluycA6ey404uJNzQ8+VZlOZr6MHEIta/mWzLDXZvkKlsGEV8+yXeWfsO66P8xkqGGBcmA63qPdmncEYNViXyPJuT5aWl2V0RFtQDHRe587M3e0B"
    "uCz38XgBns/LyDmE5JLNDR+nHye+SyxgA9zz+XwVZbDb6SZEqxLlGoUWP+Zgq3K5NO7fFOJQClFeHdxOmHA9n3DW/eJ6oU/OdQNePS/DYQq1VIvFwUZC"
    "gJppl7arcp3Lr+Wny8WWYW953WwHtPkMCw5RwrWOPPGEBk5UhmsyMTklE9PTivc9t3hc+nN9GR0akanRCRkb2yKTIx2ZafdkttmQZ9eXZCPsSK1SG0TS"
    "ONYHYcC1wPq8agHr4hW83DKGkCA81tYJk+eFY0PEjheyDngveE6PJGFTIVA+74RoItZyMbiXG03ch+fFY8TBoDr/8eNHNdYRf7EbSOq371nBIp4FTp7F"
    "YJ1g1DhNkGy0nMhL0jNGY/tsoWJuZLoxmWUQToDZ9+ywJCE5IUNpzoDdL9P50Q2HrBltJ8W4HDezNEnjfqY8W2Dqxax2E/vxvzmOxuLx4FriAs6RlqXg"
    "9PNgONUBli2/dzO3wVyHFkJkBowp6H5imTMbBu6GTkY8H6mSRJXMLyzJseNPy7NHnpBeB7/ysNTGKxLFgbQaHXlq7YzkalXZun1U9k6OycH+tLxhy63y"
    "lQun5f4nH1d9l2Qst4a1lUM/loX5ecnl88pRDPqwObHBlg1oJdTc4HJ/O2sBd/I61Z4i6kYLxOXZe15Kjc+z5kSyO+EYirFZRQFLnjUDz1teHhtUaWBu"
    "rG+1WhuISw4Q77F/GoSc1nx0ydNX912gIXbMW92EwaaFniWyLHbsg+s47GZDaSIMbr755g/U641fkYS84URTB5D9CuimlqTrhS5ejQtSwYl8UssbdSL0"
    "RfChGGBiC+PBijwgJWC9ZAUbw8J65DA6ncM4fqqzXX24pkXfWN8P0y+t5wgEBsTgUdlc2z0TcCgwrf0Hr5RtWyal267LcydOyGOPPi6z5y9IVC7K1NZp"
    "mRgdkbjdkaW5BcmVC7L9sv2ybXpaXn3VdZIrleWPP/kJefaZZ2UE7wZLBe6VVtDvbDSk2W1LoVxSKcFcgE9YUKJTFCJKdSSXMK7U8z6xeXApuBXftRg9"
    "85rwb9aOQ0sdHK/AhcsNA8UjrbkORMzzejAqqbBHjjyu4pu/m9E0pAC/czp/dXHOnnpZEiqjwahIz3RcF+2LeXkcpKtgru+7hHKVzh0O4+MT8cbGWm5i"
    "Yvy/BTfccMNP9Hrxv+8TgShBmIg1tnNnvhsNPineV38qFenTpiYsyCahOPJu+gk3rdbKqocgRuBIQBWcBtxQiArfCCW6tLEy3IPPQ1AGJKcWmqYWWpiX"
    "c0QT6xaxzenjOvwo2BpaEAXcgLAn5sGcEE2UkKBHBobE+XPn5Atf/KIcP3pUfaX7D+xXJX5leVke+cpXZXxyXMP0L993QF7zbbfI448+Jh//5CelXwil"
    "TFRIvyvdUKQUFiTp9mV9fVV6iXUm4lnUt5wDp7QqCFlVxLmHqhxpWLsB4eRlG4FAMORpYwC6CLUQsKbW91NMNM3uYziAjh7Id4k9xN/tIW3uYx4eNk7q"
    "a5l1oTkBsbeOg7rE87+57k60uOuRfsD8GdlrNUzTDMGhoaG40ajnJifHPxvceOON/1u32/9X/X7CfypdwdEYWW8Hw40Q/If5HAoq1dYt2811RBbbnegM"
    "Fq3ZMj8ii8FniYVjERlOpBBJI60XyH1dFBCha0EElhjv4HZ2ofx3Htyihg1CsAR1i1H0DDLugwKP8aA4Yxiqwv7tr3+9XHnllbpRn/vc51RfLFfKcuMr"
    "b9TqBp/9zGfk6LFjsu/AARmp1uTVN94oxSiQT/+/n5Bz6xsSVmoSEa6k2d85Pcobq4uygbGRVp9iTgRHsInOFRjZyCMX3awPyACfg3iRFjwPPle4mntV"
    "4JBwMQ6YBz64OuRiVLsNqMFnmJ6qNmlQRLls5ZVd2nE/B9l9z7meq07sI3Phx4mKPYQAGc6oePV9cSjI1aPh4eG40WhAgJ8Lrrvuup+J4+Qn6S9TKBS0"
    "coO7a/xUOKrtIpiByY/8cWXfuZj7QJ14KUo5s2VaxfTc3OygoYrDDSycx9zR8M9dYK53EiDLSefE0hSQtg/8zTkLSX1nTp9WzsrgRLLYdv0Nzf5yonTr"
    "jw1k3t6Y5kTaWgHX05ve9CZ5xbXXar+3Rx99dJB89N3v+G5ZX1uT3/l/DkutWpbtkxOyY2pCrty/R75yz5flaGtd6sMlmdwIpZeEshH1pBomsrq+Lqsp"
    "JgjnTlMT9UAwssCtSxsnSp4DEcgGGxdc0ed2WAepAAdTvXZ+fpD4xXO52uTqh3FX0idS6CStNAFHdv3UdTTnngzV+wYVtjbza9gnTz1grb0yGO+7qM1C"
    "b84NGcPDI/H6+mpu7949DwTXXHPNzyVJ8OPdbr+fj/JhvmDeDFcknaqd+HyRVHe4pFStixBf1JnpGRkeGZK19VUt4evwSTZzigXm5OqGpCH4KNgOpcC9"
    "4FCrq5aToe/jHdHgSttIuBa/8z115ANOa5I41p3pi0AIEKKLdrgJi+/J8qdOntSWBKQpXnnlIXnXu96lQDiV46n/Atek5DBNaD72sY/JufPn5MDuXVIK"
    "c3IgJK92UZ4o96UTRDLRKShyW8/1pJgvaJokxSAxUEgW8oPg8IpzBica16U0Z1lEN9qqIhA1U9S14LOsHc/VahECVVUi9PfcS8LnjBAs/N6hK9YE7kmX"
    "AYJP+QwSCuJ74oknVDow1KovFTXayIcbmhwM9o51R2Jwf1QbF+lZPNAJkPuz5ktLi8HU1MS54BWveMXP93rxj2kmCsIjsupJTv0OqTiW59gOQDPlegl6"
    "9Buaw54o3EALFnIdHqTRqquVaEnTs3oqxyfGZWpyKtUhjKPh4mLh4JYsGLVkeAhyPZQbp7oQyjXzWVtfHxClVrEvFgYRwRCX6arGFT3ahNOJAo+/khOP"
    "24pNnUnzNyC2r33taxoG9rrXvU7e+va3Klf/6lcflScef1yNszfc9gZ54sgRBX337Ngt+Xxf9gWh7K5H8kixKWeGizLa1AaTFlRQyUt9ZUNW5pckp2LQ"
    "RBqH2EvrMrJogqs0HsRglrFhgRDVZqopRKLpjrKwMK/f49k9uprhsBXfNwI0gw39EXDeS9Gh7rzmNa/RBHiCC5AAX/nKV5RhOATk4t0PC/OCcB3w9iAL"
    "hovg7OD+HBJautVq1RU44IfjOPknEGC/H4fFkiWRuL7nuI7f0HFAjBBrj2VWKASGAUP/D3p5cMoNLO1oFQIIj8UkeZsagxp/1zcvys6du3QhNC81ymle"
    "7ujoSHoKrQaJcy7zOxrc4idRrWawSwlVPyUoFf2Ng4CqwOdYQMcZEecYQDyLK+UrK0uq4OOMBxv76le+Kk8987RWzqJxDJzvoYe+rP3dUBuuueYaPUiE"
    "KE1PbpGoEsr2sCeXdfLyTNCTheExKbVDicOGtMJYoqAoyUpLzq3M6j0ZHABLGLLIGRfJatClBOl4IlzQmk7DEYcHpdngoryPGIYYOPDETZKg5JLIidCZ"
    "ihMkXBWxTqOcyclp5XL05cOix0B71c2vUilACsF9931Rnjv5nBJ+FuuDcQBzcS30QM/scwJ07u5Miu/yLKQBDw+PLAXXXnvtL7Tb3X8M3lsqlkKt95e2"
    "NPVT6NzPLWM1EApWo8+LcFvkyqrs2btbb8ZCbKyvy+LSksaacWNYPQRoBdIS2TqzVZH46ekZPS3tbmdQXFJbd62v6wK12g0VXXhrsJIJhFSPTXq69QBo"
    "6TGfjwUiaFmRqCAFKsBT47BgljF6kLm7RPbu3afwEPdhjssry+pXxmd8+uQp7Wuytrqq9VPefccdcvbMGfnjj31MXwlhYk04aFPlmrQmijLdE3lDryaP"
    "RhsyT2XUsCClDkXi+tKoiDSX1mRpcUlL3EHoGHJwflSNwWGmAJNCTVa0CSKEY05OWmI768JnPO6Qv3sONOoI1jMHz0FvJ0TXyZyAOIiLi0awIyNjevgm"
    "JiaVm+FLZg/RrV/3utfKza+6SQMcDh8+PDCinCkBeHMYWQcPxXPdMXsI/JClxTmT4eGhheCqq676hV6v/49zYb7f68VhqWxuN1d8XTS4Feo3wA2HqOQE"
    "+ImanT2vzaRZDCYD10MvmJqe1s1yDuSngx4j4xMTaixw/eXVVSVYy6y3ZBcqu8OZEBko8B5hzEZkFVsLjLPyEx6WzwIVI8PNLImmqG0mODxmTWOR0sOt"
    "rlxZi/vAtfuE5jdlanxcClFB7n/gfnnuxHHZsnWb1sMZGx2Vu+++W2u0QKhSiWR9aU22l6ZkfSIn0/2GvEXG5JFiLMv5KhX3JM61JYg7EkYlTX5fpfhR"
    "qrBLkBvgdQNdKUUdPB/Fwp3wRZtI9RRRfndviYV3lWVpaUXFMgaYVdbPNv6x7xthd2RhYU57vuCi5JhAcFwbMUkIG9HSx48fU/zvHe/4bt0n2sqix7n1"
    "jkrE7+x1lgAd83TLOEuA0FitNnQ+uPrqq/+vTqf3wbif9KMorzaGl7h12MN1E89ut82jMoLF5PG5kydPaQTH9MykKsnqI11dlb379mnkCIsDq/ZoCk3U"
    "1nxWymZsyNmzp2VuwWLwvCEND0ADQ7iT+nRTsaTVOjXd0yw6XWDlh+aXHsRh0HQ57VDOZ+FW5VJZhip0eqoNsDNiAnds32bV35stKWr3zZzMEqCayylO"
    "SAkzdEM24C1vfrPihx/7+Mfk0a8+KsOjQ5IAiG/0ZXh8WOJKItO9vvydwlZ5Mt+Tk+VQiklecr1YuoFxNbggNQ1VjehbLB9r44lfBHW4Es/f2GCCB1yV"
    "gCA9HdQDVjn4rDMqDPoc388mkrl1ynBDCAK05PYJVanGRsdVDXLsz4Mgzp0/o89P21wIDbHspUnQ+zy9wBET54BZcNrtB/d5Dw0NnaU+YJIFEFX3y3T1"
    "8Uk7HsUGOAtXcbABzEBmfcdq2S0uDEKBrrjykPYJ5oR6cXMGuJ5OotPSmLXzs2cV+qE5NQuHeCQ6V8FSYcNCjd5QQgsBnM1Stx9TcYMEDdCIkFAsyzII"
    "gNU3a0bHPVnfWJPGekMuLEZSq9bUamOOp8+dlaTTk1wsEvUSKYc5GRsZlVa3o4SJYg6BPPzQQ/LRj35UufR3fed36WF4+MEHZbxSFYzfpZULMpFMyWIp"
    "J/d05+SW3JQ02005WwplKClJGDTVrUjvEixpCM0NPbiCWe0GVLvFuokTmt+V4fF/Dih7ECyEA3fCuIJjtlpWCMr70UGUEB9NH8EU5+YsOd70RIuI8vlA"
    "5F4Uffeu3fr8GCashXMzH469uu2QHc4k3CjJSi7iAfvm2rIStmQ4oSsRD5Zl3S6CXU/BEMDyRGQiHme2UBPlvJw+c0ZF5RVXXpX6LwkOYEFIXaTa1IZa"
    "yqurF+S5U89Jo9WUmS1bZGhkWBprq3L2zNyA6PNRIAERN4ijtBJrHBBH1pcgIWCCRi7efoGFtpOri0h9aMwiDWfzxjGJJOrroZZ0R5ZWF2Vl3TqzT0/M"
    "yCi6WCRSG6pKg4RzzXwjOCIn8/MX9DluufXV8uCDD8i9X/iC1oyh3Sp41BOPPybViETwpqysLcpEOC0nC5FUNmbluuEpWSfbLchJEa6MK64QyuT0lFw4"
    "Py/lSo46CNJuNcza1RluppMqlJL64CmNZzhm2uS719F1xehgY1V0NsA+CdeyMCszBACYidvMqYfHO0gBjHsZD3WZBtaRwPceNQuoZ55KYDSJ7FjXKPd8"
    "OTG58yBrbGQtZv+dz6XzYYQkJSVWzoHOPGmlo85me60sHuiRLy76VlZXFE+iaTUiFSuIUwOOxvdg6ywOD49SDBC6UV8xcTt7XirVqlx24KAS4dnTpyUh"
    "Ky+NKdQHRMTaVmymf8EB4XxpVYkwzkkxKkmBGtba0MVOO/RKgGov7uihUq4Nyh6QBmIcJsphwVt/EQpMUuF1y9SMBPlI8qWyhA3LQ/Hed6bj5DXq+Mtf"
    "/rJihKyJJU0VZHxqUmrttpw9d1bmLszJjqkZORImUlpryOtHt8ifyrK081XJdUV/8rm8DI2PyMbaugb4GheBcIrS6W4We3RR7PVsslyQ9WX/XGSCkzpQ"
    "b54Xq7CAlUy5Oax3uD6GF5AT0snD5Lx9RdZYcZHK91WnjK3ej3udeG7n1JcOj/l0rwhMjHU3b4+Gf+VITFfuZG4VL+cqSunoAlyEm2Q9HXyHjYHYrNjO"
    "vIpdxMHlV1yh+pXXambD+C7sfnl5QU6ePiEbG6syM7NNxkbHdFNh84geDh4JKm4Rmm6X5h5qnCIh8xzSvobZ18rDUspXJJfkFQbq9NP+wCw4UdNxV7pB"
    "W7m5qxLqcsqTomk+Y0Q2sY2x9GSlviobzYZMjk/LlumtStDVIWvUxzOxWWfPUhG2r5VECVM/dvSY5kyQ9onVjx42NTkts3PnZX55QYZntskTjYbsWlmS"
    "a2cq8iAh9RRZ78UaZV2slqXd3NRv2ehi0dIiNH85NRg0yCMV1x4Qyt8gPqtRbWmdDjk56G4MxHA/9gpYBQgKfW7fvn0KKXlesunRm3GBF4vRP++/dubk"
    "a+tc0YcfAA9bMzFvgf+pXZELO50eTWmsoXNqWarfL4ViPPLBZbtDM+hpExPjiu3B/SAiHoisfG6C1YvIgl1fuHBeLizOyrNHn5ZGY0N27NgptWpFTp48"
    "Ic1GXUpYud2eFj3XyvRp9RJyE7S+DD9BpJn5VSnIjpFtsmdqj0zWpqQQ0GPXWgrwXw7cD+LC8qWif7Ei5RJ6aEWvQRUoRNTq8ooC3RpWlKD30Jaiou0n"
    "5hfn5dkTRzWChLVwnydcA48D3BwOcMMNNyjeCOFxenhWOND01JRMzEzJaqsuzcVVqdaG5TPdeam1Ra7Qvm8tNVoodZFLQs0zUegl5RDcE++DBr9mfKqq"
    "L6YibMC14kT1Zq8WBlF4QlX2uwwibfByfOITn1BRv2fPbn0/62J1KWF4r4XZqVjVfORN5MGNDHeZ+r+zuqHrrq5TunheXl6msWGgEVXaXiPua4Eh8xPa"
    "hNzQcPafBX7hflb108Bmqxi6U5VfcwVZACh41EZ9TZaWZrVVAdffsX2nLsyZs2fMMiVOrN2x1gCevpcaGLo4HAR+6ccyPTwh28ZnJApL0qb2Ce0eMEjI"
    "T0pDohJdpJheP4ZBhdYcm3upmKORTtJNu0eS37Gq84JQgTCiQk7yRUrFNeTUqZMyOTUt27dtG2BvbLg77+E4119/vTz80Jc1btE9LqzdzNikdPt9WZyf"
    "l1o1kmB4RB6YOy2379wlp6kNGEei2m1ao9rD71l7jRjPG3xkUTRGCO6TzTIFdDxPcOJzHjsIwJ2tVGU5I4sqafB2YAQ++eRTg+R31/lYnyBAolj0Dofb"
    "9t4j0NM6PJnBfDwgdYBKpNahz9vFtGOH9ndMRD6i2WWeIO4tDeyBs5EMTMS5ARdCfAJaQnSwd42OqQypeKRmSKO+KosLc/LcCasUv3XLFqHxzrmzp427"
    "BabUau1pRKO2k+L9VM9DR8OVluTlipkDcmjHlVLJD0uf6Nwwki4JURAwCnYY6O+JgtTWkoXRw+gAXkc31JwXwsioeU1Hd/oX16RQJONsTRYXZ2V1ZUni"
    "XizlfEUNg9n5c3L85HFZo7MT1eYDrMzRtPcu+GJJrr7m2rSbpZUCwSBY32jItoktKgXOzs1LPolkvliRJy7My3UjNcm3ycQjAg7RRmAv7jRjAPybClTo"
    "fNo1MzXANhV4izQxi9YMJTNKwE4JcggUCuM9jEureGZ5zVjLHBq4NSoE++IcypgOhih6MzWzO9JPuta6K7ESwdCNA+NObB4pw4HJDtcl1TDMpFA4PqiV"
    "8FDCjcVa715N+kkz47KYjnNCJgH7RvTyw6RxpRmHyWv83MjoiJ5MfJMnT1r/tOmpabWiMFTMR7sZXeseFvUzYdUaGClBHEhFSnL1nkOyfXKn9Dsi3Vik"
    "gy8VS5G9SaseKOQCfISVbLXHNFNLPSaIu8wiWLSPcXnt/qN5FjUVe61GU+bn5pQz5kliz0eyvLykhgULjS5IzRm+QwI4z01k8WWXHcxUMbAGMnDIHdt2"
    "aBDCubPnZGR0VB7tdqUy35SDY6Gso2qQxJNGm5iLzri16nyXRKNkcTz3MPAdOK+LYIiDvA+YAgTh3hSH2pBWf/qnfyoPPfSQPr/HTjqsZesC0XpLByuv"
    "Z16TRUU24KwawZ6GXzlXy+KyWajl6w3dhyTpx5bYbCyWB3e57zfwB3fi4zO4ytD7cEQT88cgjpCTs7AwqzgZIgze6osBnpYVJ+q1SKOulSUD5pJdB9Ek"
    "IkNRRV65/1qZrk5Jp9WXLln4nEc4Wi6RfoALri9JYF2UPIzMUgk5XkbT6SU1bZB4R31PFxgBAG5IYEVJ2zcQ3gVRLq8sDWr4sZFwNWtNSjAAnZMoz5ZX"
    "cJ31mZyY1HAuTzzieTTPo9eVnTt2KC53YWlOimNb5OHFBdkfdmSoH0pM9qCmNgJ/mUXp4guO5evjBOcby6F1axTi8HwcxweZhxslLgb5jrvY8G1zmJx7"
    "cU9zU1pbL+7N/DFYYBo8u+t7HvMJwTk850G32ZF9lucbJGOGQRA01Y+Qgs/OLp3jueLo7JQburINHuXou1O/EwHxYd0ePWaLau0SC+hErgSeKr+62IO+"
    "GEo3kkvgfEW5bu+VMlpSx7X2peuGiXTDWLrSly6EB/3kwPViBbXrrbqsN9Zlo1mXTq+tngbq11md5a4mI/HKN4w4CVYl0BVMkVJjlg9BOHy1SpcjS44H"
    "ByNihg09ffqMYp88N5yPQ4n+S/IUFiYHEu6HPuzJUBDH/oMHZOHseSmFgTw3VJTzcytyw/CQ1FuE1qciKhP0y3pnA0MZToQ2b9ML+Z05u3HIYfEazdna"
    "iVkdzGElJ3SIkO/AHWESeLF4hfjY6ywX5eB5i1fnoD6P7Lz8oFzKCQdGjemASUiHJCcu0ytM78tyKpfZXpKBk8GkvfLngIvpAubUi7GxgQ4SadgVDn42"
    "0a0tnbDreQOPBkhk+hOHcmjPZTKet6aGbelJO+ipG6svXdJXlPha3bbqZqgCBDLk8jn1alRqFSlWylKqlMz/m+ZYgINZEKX1RjNA1CKmrbWsAdkkblPe"
    "zN2G8/NzqWeBFMim+rgtE84kAAfIo0T4t5W23VCChECxSqemJhV6OnXiSZke3yoPNWMp9Vdkf6Em3Z7qQYZNpm43VAa3Oj1q3HXA7Cb6BrNOzB0C4fN8"
    "Npue6sSL8QGxOnHzfbNWjZCdAfmrz4G99yQvT3twY8iJ271kLjmzhsglw4swxGTFDYIX8TUCVTB5bsyNsmKY972ELKKKKA4lJiwLCCkXyPrGsszNn5Mo"
    "j25UUe6DL9dj82zxTLnWkmGY4f5DOkA7kcund8t0bUo22i1pU2CRUrUBIrgvMUWF2oR4ravlmS9GUhupqdei0W5Jd6Mt3Q4V960agtXX2OxMxCJBXPT7"
    "oChMq1mXXrsjsZfwRYFE8Y8DGQJyYSNXV+TC/DkJkimpDg0rlz115rRs375Dq4fWRkekOlzT6Bk4IaL4yJEjukFeqmP2/KwcvOKgfOG+eyRZrUtzdFie"
    "WdmQQ8Pb5GhnQ4a6BVkpixS7fTWKrMOoWcTom8zbYQ03DF1lUv27ANBve8YrBMZhY70dEHbwmEPhe+twC8OjZ/wgQnSejecQkVu7DP971l3rB8IJ3keW"
    "E26qeEkS5XK52ArWUBtwc6PcZ+gPzoS1OlWaLK1RIJdUPkK3AqhlZ8HKWDhv9MfgxlZGwhRb616ZFn9Ms9vGh8Zk55Yd0ml3pRNgcAD/ufusL+v1dS0J"
    "gbuwWqtIs9OS1eVFBZ4D5WAU6AYbzElCyqa6FM03rLhY3JfFlTW5sLgiNQyJ0TGpDeVkdc1FjTXdSRT0phI8ynaiESzz87MyHQZSqQ7L8uqyFkSCSIaG"
    "a7K0dEEDF9Sz0OloMxlaawFYc2jh0o3OlFx72VXy1DPH5Irrr5Xjp07K1eOB7CwUZY40gqSsRkkU5mUDIokMb/QNNpepJff4Bjs8ZvtnwDWfcVEMwfja"
    "u6jk7643ci0I0lM7Xbd03Jfv+LWzHI2/QxObgRKbQLUXHvD5+P0v1gkV3lEdMHY2a1avKcSu+/ngy17LRNmxJsl4JQTzXhBUiujBY5EGHQ4mn10EvY+6"
    "1zKZbolIKYlk97bd0oXj4ZvA+S49QfB2+h3d9I3GhopYGBX/pu18Lk/WVlGiMJBOuyXrq6uyvrYqjY116XZoL0pNlK70u20NlefAEfPXSwI5Nzsv8xdM"
    "Z3OOYX5Nq7bK4CCNpglCNGCmWGOxkNdIEhru4AmBsCEGF0+IYdowoLzj/iKf9tzpczI1PaMclgCO/MSoPDs3J1cMjUij1JOIVgj9QINXwS+97p+D1JtB"
    "CRdXMXAVyvVET3qHeXgeshOPqhgpbqeHotHQ4AIikJzosuqX04IbII5YMBd343FtCN1VBCdMpyHnfj4HG8p8YsKgVQdkZC3grHWahWD4jLXvSsVnJukc"
    "3UirJqSBn55E7SzXCda/6xNio3nQmZEpGSrWpNXpmdhNekp+TYhvfVk6va6UyLJrN5UTBlEghRJcwro+bsAZcznZOjMle3ftkpnpSRkbHZJquSglAOYI"
    "MLAr3caGNNdWpIvzv1xSmAbFm5OO4u4Ll03O8krwPP/i0sKgqr655rwXsUWHe71odGS4H0Swbcd2aVJ3ZnlZdgNGnzkj1cqonOl1pBSEMkpxUIwjEIkg"
    "0Ew6rfqSKRPsnM8Ps6sWrGM2tB8O5CI2ywH98zASrGHmna284IeH67mFCx3wGd7Lej0c88uKZCe0LNjsa2nW9WZsoj2DQrSS+IUNfzLHvRMLX3K27L49"
    "TRH0AjSp5wSsrJk6xVkMj1FLvbkXcVJnxQMdkGYn6Etj0xJ3MA5EcT7aKbf7XVlZX9ZqWFExr4o/hkC+mJcoD/LflA3ceeWS7N27R7ZssbqCbAJFeIgK"
    "IWqmWCR4tiCVckGGijkpk7LRbcra0oI0NyzVEYvPq5gyR+Zk3NCME7gkei1ppliMwE5E9oB3elwYnJ3PejkOcmMIObvyiiuEpJvl+SUZp1BQEkl9pS7N"
    "sWGZX1qSK4a2SItWEXn8grEUUj3cXYEcUCcgF8m+uS5S/aBDHK7vsRbOxXiPfYFROLf0uEgvEsA1PFnK6/u4uIcOPDGe3739mXPAi41Zoxs3Zpw4swYU"
    "NIkVrOUQgCHieDMbzqnVH9YxJ0ubLKRGB7GDiAORpaV5xdvwQeAGMqvM3C2bSqeJXIVd0gqmwChE1IxXR6QA9yOoAJFLQEFMWuOadu0BcCZqpht3JSoV"
    "JYyCQXnendu3y+ToqCzMzcrsuXOa39Fsb0ixUpTa0LiUqyMSFSqSi8qSK1SkWK1JdWRYhsdGpVQlcbwh87NnFYjGy7JwYVkmxsfS6hBWBUI9KNphfVRK"
    "pHSur0m72dQ4RfzK7YY1iNFYyrTgOM/qgC161q7dO6W5vi6tRl327d0tZ8+dkXJtSJ5ttGRHty2VEjoq+qtV/HJoyzeWg6C6bpoqqV3gU2bhYo/BXvFd"
    "DyDOqlH+N5dC/prF9jzqie87l+TeDvU4bOPX8vllDY8sx8weHO5j6IMxubDd7iVKXNQfpqlLajW6MuvhNm5ZYYrbFVPLF9O/WdcIF4DevJbgpwuOtfBS"
    "U9Ol/gBktV3CawGGlwtyMjk8gbtXOR84H75cIlP0OqkYAscjQgWdj4w4rkcnTDaUwAaMBvA7CGloaERrXlMjkE4//Kytb9hroyX1Zls6KOuVsoyMjUgh"
    "n1PsC/HH4ixduJDmr5jXxCJ0clItY7hgQceysrykljbnbCmtJqqcBdmSxubhPcASBhfdu2evBm0vzM7K5NZpafdaEq83ZT0fSrO7IdO5onTwuwYWQpUt"
    "mwFHH7ShSLVDh5EcSmEfXUpBWO4LHqhLGYL1393IdI7IgbHMus2ajH5dDErvEMU1HZ5zLpfV8VwfdrXBjalUz/Qgpzy1AXFIAh8E6sTPlOfNmtduCVkO"
    "CHq0hcTzQ3i5ZsWljnpEsZ+KS+sUGhGmNKyV2kVK+aJUihSY7KjOR9Bpu9tWuIMAUgpgUlo3jMh6y2uCOJu+bdsWmZ87r2BxFcyvRJldkWq5Ju1WV+ob"
    "DeVSVHXH+KDkjQY3pBUUqKpPXUGeE1ipUizI7JmTEqgf1CqXegi8Ke8YBtRLGdVYRjZjbWNFRTGf9Q3XY5eWVctak3BBPCfoheRbTM1My8K581IdrsqT"
    "9Q3ZXxqTOCA0y/zhZPj5oc1avR4XqHAZ1me6Z9zLQszMkHTu64Tir85c/LOKo6ZF1cEOUUXck8K+O/qRhWyy+ryL+KwOmB2OqLgqQwwqqt7u3bs3QpF+"
    "V2v4pb5RS2C24RPMxpb5gmo9QKtyqQuK+wrLTS0srXG3qXS6HujiQk9f6grTWnvFmkQSWYO8xKze9eaGdInQpbZLl9MPtFCQRouc3rZsZfPm56SxsaEi"
    "0Tm1wg8Nq/SEKIPwwoCys4HhgmmIkycpMV90RfWfDlWkWork/NnTUquiE27oOsCJ/LDx3KRRWopBIPUNilJSDD036LbuIoeBx4T1wXDDpeX947Tt65Zt"
    "ijFymuYwCDqxjOdD6WkcoJUKdq6SFcMOvSgeqOkHmxEqDjB7JE0WcB5AXqnYdhHvKa8gGFzTpZ1DMM4dGQ7l+HsuhrPP7J/zwf1Y76z3hgDg1dXV5+jb"
    "2mdfIDL3CmStVldmeQ+C9AAFrSWsXXgsU805BJ+3hoApm0vbHfhJtldzPSGCWT1CoZKupKFSFNNuKb6n0UoEiwKdFPPKGWnPQBwinhb0MOUUeYN1ioWq"
    "tJod/T7BdjGRHLjsFEsjlyKRclpdwHQAq+hPg2oWgYNT07xokZOnT6sXB9GKG06b4Cg0Q7A/2N+wckcy6ohxxGCB6L2agXMh181cUXcDBe8I+mOumpfW"
    "ekP6+ZJGwEznIumpb9t0QA8G9g3PilPnZFld0Q8ihGGBwZutEZ7PEOBz7KHrZoOkqLTMXpar8TeI09GSTZVqsyaMD76vakOmrF5mJNgRs7Oz84hgDbvA"
    "cwGXMXec1YLzoEe/oZr2qYnOxEA16uurirNxYg2FJ1wbiy2tuESMIYRmKLdyPi22i/GCR0QQGwVpJ12LZgGRR2ym1+l02xrgQBnZJhVC4Xa5nALDWkwc"
    "oahBrDnF2nD5qR6LOxGDUnCtieQLoQLU6FH1jaY0W13ppn14KYTONbUWoRZcqki7ua6innCrjfW6FPNlyedKGtkC4E0fDs3FTSwwgbAqHhGuyVp4iBsD"
    "QqXKPwcYLkNIPBuO+N+iEcoQY01OtNZkW76iEd8J3qVM1SrnWg5nqJGYrqnrgm6cuAHgbbOykidrhTq8wt+dsBkebuWYob+6RHTx61Hy5k0zyekEy5r4"
    "PJQJXVL6OcUB6yHWvRGdtVDyWs/+UHryLIpAozX832wyelizAfBsnAxFHdfb5kiz/fX7mxaiZaxZuFU+ZEMD6QA5p/1oKUSuC6U1jM0vjUutXW/IcKUq"
    "G6trKk7hbHAevXwubX7T70rY70mZMKkolKFyJGPD5WSoUkzIAWk2WtqgZmR0TGv4aQ5xGvjKfZrtruqapVKkIh54x4qHUzOZwIU0OT6KZHRkVOsut1sd"
    "NZBYZC+s6UWA0NHwmDCoKOu9RNjM+fkFmZqYlAZdiCQnF8K+lCSUYhoSxcj6V9noLLTBcDmTdR44IXp0S5bonJPqfNJCThndzOCnTMHRrIGTJVQPF3Pb"
    "QOeSKvcWN2jRNU6YTpybKoV6QhqqQphFY/qcX+gi/CZ1lLs/0HOELFHFxK9yopDqqJZM49f6ekMnov5jy31QBVnFL1EsbbWO+0lfRbDqldrP11IM683G"
    "4LJujQHTtHttyfXbsmNiJJkcLie5pC21ahCP1ApJpZiToG8dHzX1MbaadcrJifyFC2hYmpUZgSu32uiGdcUb6fBOC1WrzmBBryR/4w8HC6QdluOlEKEl"
    "RxlXcDDX19HL7VKyBOA8KkTSabalJYnGOtaivASgEiRzpXW57UCaW26wmekq8J4TkRsaepjSbqRugWZVKw9Y8PXzsKysyHZiyX42S4RZA8vn5CFkTnze"
    "QTN7b6exJElaUE7HiUU5TYaNZtkmwwlNGzmn3gutRpUSIK++QHYhO6N+c7+2fd6IXS06Nl39vbEVesRtFsMRsUaNoL3MGKIMXclhhIFJrbhyQ3ZPTye7"
    "xseSgoBbFZKhoQopdAGcVIlN/ahW+pfSGNa61IJCITyGc3+CagGc0VfQ84CUiCyGYM0XSsrpkHI7d/izQa4HuuhjKCYXWz1nK49bVWlB3smwpoHWpRvm"
    "ZLXdlBHNUGRtLDNwIHZTkZwVdz5X182cY3rTxa/HCJhP1kBxC9oJLPs9DYfL5Atl7+9illcPchgwqoxx5IPrwuxSZtkhtLPNl/P5fJAVu35DJapUJ3QD"
    "xNxvJrohEKfozRsOcJZNPSaT7J6djLVdsJMNAbbw3eIRCJI0ndI2gFrLymE6cMKUvnkY7V0WSNzrSjWKkr1btsZhJ5F+Ly8SVoMkyEunlwRdpoy4tqh6"
    "A3s14Qmg2SqqOgE6/MTz1utreli4L2KW7zIP//EeH2ymWqWh1QB0juJr4tzCnffKVcKcLC4tyrQaVXWRXF5Wei0ZI8kFLqs+dvPE2MZdDOpn3+MzXNsN"
    "EwjMq0n455w7OrE5kTnA7Dr/psVvkswRA1cBPGzLOaQ/Y1bkXzqyBoszH82YyOepCdNTBR6uhgXrp8A5mv479WDY3YwC8GAMmgQqJ3Mxnm1SYvqhZmlc"
    "0rvEOAQJROighr0pKJ6mAGrH8rSuHfdC7NmptQsNFhbS7fZktDYkRK42m13pYWDEIqvNTtDsgisCAkZqROhstLpXQaNqrO8GB8B0VcXWUp0GzwO1YgiO"
    "IbCBMDI1eihRnMtLtVJTDkk+r+Gj6MFtFdkuGfxgW28OM/CYO0QCMF4CA4076hVqtjrasYkD6EERWR+wX+tSzubwiSEZhk64QZn9LO+5M8HnwXvcww9e"
    "9ruO4bnBwbXcYs4Stv/+fCNrBPlIaaxHMEKao6kJFbrAPvFN3c4eSil+oCciqhCVimMPCMxF46bMT3NqVLpBhHYftRRVqJmux/bj72XzYdEKbCu4bQaS"
    "ht7/uW7hRvDGGWAgxWCt0QrWOu2gG3cCPA30+mi2Yul0Ew1ygHi0UCTNDZX7hUosGD4QPvfneSBBww0TaXVb6n2BALG3rCi7uehK5YrCNIjTnrYvwEOE"
    "J6hxkd7DHN1H6xwHoFmtdi0f0tcobulpoyeJ0kgcz1J0HTArbfT31CMxkE5pOJaylzSvJLvpjse5quQE6+oJ77sI5b2sLcC/nbM7Fun6vn82y5Wz93WG"
    "YcOguHK53A57vV7glqtOKk1UMQ5nIsUnkWW59nfvquk5FpttRP2zm98ZyP10GLeBa8J91d+bVpA3UWGE56f30tPmBD7ApdAB8R03G1LvtBViob55s9HW"
    "chYYMxgyWhCIzkAUiiS4lerzGsC6Gc9mS2T/59m11Ze6Ay1fBsNAuVOK06nzXo0475dHoCuFOzfDzfge1rCHVPGqkc69nuKW5VJF+t1Y2mBH4J60z8Xg"
    "8VJ0qRvTVSPfUD/wl262u8/8c87hnFDdcHHVwLmUGyWedO7eDyc+N7T4nFvA/O7fz+q9zzdc6jGiKGpTmiOntUDCWAJtWMjGbyLeWaLLPqxbzWkC2oAg"
    "tDpVxv9mhGJT0fdTrsWpZ4NhjADMAZl4yuXYZDMIVCynNY2d+/l1KKrEBVSk0Ww7TtS3u9JqBNoNsocLz6KviSvUaivaGbMv3ZiaBOh/VCdBam869f0k"
    "+yFguNJtOq8VxqQ2DbAOh8bx0WxVAZKRONjmvjNyRrqwgaypcxo4JvUPEcetZk+aAOGSaIhWUxsHmlRy0ZuFNVwiuW6X3XwPHvH90wOQ9v/wfXQvhnM8"
    "N3acWJ3Y3KJ1Ee1Eq0fU/arp/mbncCkdZAb4M39fCjudfoEJRDnqFG2KNKfqLBf0v9tNU6pKpbJjhUpUGWU5O4ns0L6+lpWsuh+QA9lt/GABWww03NEq"
    "E6hu1Sd3wfJk0+sm3sCGBjc9xGW/F7SoJajYJtfGz01wgHFbYB9tYU8JskKk9+2nLWp9uINeqTMFaT2qmmHi1/NHzP+qJJZKAutkaRX7fUP0oKQGBb+7"
    "wQAXxWou5IvSbXalkxdL5tLm4dTGsQNgMNWm7uv74jqlg8QuEg0KMsJ3r4brcxgnDjZzHff3ujfMv+PPyN+5vqsOfk/PxMtyP373ELLnGxBZjkoBIo12"
    "u31az7/iRJqMZC40jyHL4ktZRdI238TTJsyS7d/mHM9ebXOMaEzvs81K8WslLPsL/k9gEggHZd3wRTiJpw2gf1mLd7uw+hFTg4h2rORdtnv9wGrD9DWm"
    "UAmMyBtFXEiFzJFkHige2EP0YxWnwLaKVtOD9RACBoMTpmFQPId1m6QCa6QYoftjzTNhljXPYFZlppt8Ciz7tfkb32+0SassStwlVCmSXqettb0cfbjY"
    "gkzzuFMu6tmF7o3wzXcica7Gc2F8wGmJa/TuVC5a4XLAKK4iZEWxHxZ3xXrxUifYS9WCLHjunNEZkc2bgyn1MAwvhFFUUHrQAtaQo/peN/Wh1Fq5xJIx"
    "yxYrEutW9bNBOy2raOX6j4sfxfkg9LQ8L+JeC0hCYBgzGCA9OAPxcBRWSE+7YEBYM2Q6b+p8MJQwGCDEQKRNg2Q4iTrTE8kXSrp5PTDFmOD+OIX7NAIy"
    "SfJRUCwVNOqlC2qP6qEGj0ilVFFQmeoIyi21ympe+uiBgObAMBq8AURiGXQuhchp1povGDgJRY/MremSQ8V1mlzknCLM55Rb4/vtB11JOgWJu221urG0"
    "lbhT5d/FcJYgPRLGN5j5esekLPfFAHICcrwXDkbgrIfWa0vXtMeKH5Lsq+t87vvfPEiWh+L3y/6eJTzmtrGxkaTfn9++ffssiekKRGOM+IP5l5yynb1v"
    "6h9ppIv6djeBUo0KSfM9srqHb8CAG2ogwiaDxnviG+UKvoUZGaFDeFiFALMQAnBGAMeigzraY7dnJduo8by8rAtbqVZMS+jFdC5CDpsFq5VPRHqtltTX"
    "1rSECHkkzJE29C6mPCaORXPsDs7obcnwhqDfOSfilbkPAi3SYIfss3MI6drpg/WiRJt08f2SFBNKkidqx6qEebSRW7PZNR0QYaoiZKEUJwAfWVzPMUVV"
    "fVLxy3s8r8MrHunMZ3jPE9GYh3PYLDG6M8Ln5wERl6pfRAVFUZQMDQ0h/x47fPjwahiGYTNJ4l4YopFvOqUvdbM4Kx+wVMLo0wgR5YCpjuIPeCnrtf3Y"
    "BFPhXlYo0kBoJbg0yYni4h7yz0b02l0tYFQtlaWxvpHWnkm0yzabFQbUOLSWpVyLwEk45uTEhJTxX8N5Oz3ptTrSaTSlvrwqG4vL0q43NZKZQARN4k6S"
    "gevIk7qz8XXoZEr8g1xmb/pimWf0JhmsYaaalBlq2QT8tNKU+tMD6be7EoF99kie6kiXHh4uhVIOqHpZxuOUVf697AjDjY8sLONQSzaayffCidBFL5/h"
    "GnBRj37x62b3z4nRuanv96XDuaKG7OU0WS1djuhTfBYlq81hsAvgEt10nWWxHt7Pum5YPPcGoMMZXGGh4MYpN1HnDLMbvKsPo5zQomO0I2bqaiIAgH8r"
    "i8cTIqLitZLCGMAi1Hru9/qBfUZFeeJ+SN4j7wHOOT46JtOTkzJSq6kohROG9OjAWZ4LZWx4WEaGLQGe6BGGFkdXkNg6UQ6SfLQnB73eLBTNn5W8FEvE"
    "sv7JEIpDVw5tuf47cHlp1S8rI9yN+1Js92RHuSoF9F+qmmZ2coDnZcp2OOflXhxWt65Ze9fB/HtwJH6csLzQu0sdJyYPxfL6j57Q5J/z0DtlGKl6kRW3"
    "2UNhap25JZFKaWelGI4XBMGx4eHyR5UAYxsJC0gkDJNw5dLdS34xXUz3QGgBI8v/0HB+cnjTJtUmdjZXUCudblqudr30z4hiNgODAREF4VHvjoVVgk/j"
    "B/EB84OYpPh5tVzW1guorjFenJR78x13X/Hg83PzUt+oqwhHCR+qVmS4XFHOWFDXXltj/iBAjzQhRZHIYIjIkovoUlRW8VvWpjDmpfD1oipVQRvjUO4W"
    "S97CsRiX6tMQuYa3QWie34EoDiPZPjYtQlSN1h80o43P+H44V1MO7KVNUhXIIZMssfC7xyN6rCKv/uPxegMrO60f7em3TmhOoG7oeAyhu+7c5ZdV4bKq"
    "iVfdD8OAUoBBuVz5Xx5++OHVO+64IwcO2KdPNZam6TtACCYqGX5TP+2b1pUtUKU0JAu9RSnkrQZxILipMCQIqtyEDZyzDqxhxwTZsNSoUKJOy3tALLTN"
    "6lFJFLHQiWV1o65tHfL1hqyurMnw0LASGbqDFeE2QveNRU9jcynfIZRX041L64Be7BTX52ZK3keO6OUdO3emyVVgebTGGkut8Yb2/yCkbK3ekHqzK5PT"
    "4xqk0MebgSuN77jln75yqFAPXEzrQUyDIVaSvqwuLEtSCSRuR4pRJWFPmx86J1NOnyZ06cFMCwM49OI6u3Muh05ccmU5lBs2LlZdxeJerKkaX2mPOv+M"
    "q2XO/RyM5u/OrPweGu+YNvEmvjKOe/1+vxd1Op3ff/rpJ3+PBT18+LByRLAXxQBt48zt5oTmp8/ByeyJ5ndqsXiGk0/MUPTNAEUXyXqPFNO6SDlPLWhb"
    "aNOPiDKxe1qZMqAQRPzayqpGRPPAiEi4lXMa36iLjJ40Lk0L+JDJn9Yi9GgWXzAvPAkBQnwEmyKG4YSE07Og5Pm68u0bBkHBtRHV2UOmxJIpCccA06Ri"
    "gncYdWkC0Iwa0+x2JNLWEqF0KMSupZLNp+uYHITngQcumSAE5sfcEK/Z931Psvqbr4/vefbVq+7zPTdKnBYcO/RrOQdkeFQ1awBHJPCWQA0LUu5T/CDX"
    "6XROVavVH03PENwpCZvNJlZwz/Uvv5krrs4JVcdLrSAfTNKyqMzJ7lYTutAmDHNxRU37nF0ha7zobFIjhQEuxqZi9fapAYMXgUiTZkMjlWmo4iXE6PAD"
    "vKEwT6pLZhd+IELSjkP82zfMB4vFNcmMg3NQRZ68DbPoRP9uPc5MUvAMbBZFOinTS4i+b7y+psXUfShxZipc2QJY4AMoOZw6pk9fL5F+LpAWajlYYlou"
    "z9UKt2hZKzcqeFYXqy6xXKyqpLlkXAQNZf7O+1lsz6/lY7Bf6V5z30EiVhAo0WFsMBcOcHposCtgcEGlUvmxI0eOkJQ8iMcjL3gpCIKGi1jEWJYIVV9J"
    "rdMsyzWrF4WX/rH0DDbUn5s/X1iOEniqC16KNWY3zvVMXnkIEpH6lFfrdaVcIoTJiugQtk+ZMT5H6iME4A+dXaAsMOubkl1Q5k+iEARG6iSbSksxOBsE"
    "Doel2ij977JwCCYUyfhwSKxtrWSQCUvXxssZ37gbIV5/x/5taozuBsQmsVSohR3lpI2KQ450Gm/pPlmGSyhnGroeDboiGRaXfT4nMG+9cOnfsvpf9rA4"
    "ouDXdDpw7umMifvxNw4ng++xnul8KXrQ73a7UavVuuvJJ5/E8ECfMWOCz3/v937vqTiOn0zN1hSU3rSEs7oC1qGXYtCH14LbiYamu9LMpnHmjPVyuTQs"
    "P/U06MFPFezNhzfxr+0OU0PEHwZOZCKGhJiechv142yQi7yhBEJNZzgR3AmuCSFiyLhlyHDOy4KZV8A43vjEpBoZlKrgWhRXh6AR77SbXVtb17ze8fGx"
    "i6xCPChnzliT5mktT5xG0hiaoIS9ufmpOqLPmcY+pmFZGpxJ/w3NjtWOJtomAigGAnV9zgnQlXsGawwHWllZHhBEdmxyOkMlsvreQF3IDCNew1OzVnyW"
    "IfkBsOe0QpZe6Ij1Q4UxojWAo9Vq5dvtzodPnz790ynxZQ18ie66667etm3b/muz2bwtimic1OsHAaphGPDQrgf4xqFjQAghBXTEQvCHR0bNg6HKdqzF"
    "e7w8h0EkFmnNrRGj6nXAQAE70cLNiKdQumxU6v4iST7uUbukIlu37ZDTp09Ks92WYlCQoWpNGvW6ut7Uah6uylilJPVV6sNgsRqMUk3bmDqnyC4sxEqi"
    "OpyDz+677KD+/TztZJtN7X1iBkAsh666WnvHKbdK9brl5VU5c/q8zExtk9rQiNRxAzr30YgZVILNOosmgnH3we8s9F+D0Xpd9YJ06CdCJFiUl67kJOz1"
    "pR/0Ve918esE7WoAnAdDzcCtzX3NSl1Kk9j37UC4wWKHEhzS/c3ps+kzW7f5bhcJx94ZI1HI65JO6Fl90lAEjfGE88WdTieq1+v/YW5u7idSsXsxPocR"
    "xZW3bt362ydPnry+3W7/Y04ok9VoVfMC4CvWo2GLb9HJFMD2E1auUPB7SEUSE4YzIR6zqDvDxQMkqTVotH5zWs1eqzKYHmkh28A8BFb29Npbt27XBjeE"
    "OUkpkMrw0CBLf31pdeDjZJE4lcAdrjpk4QGfM8+C/grHQ2Ug3RNxioeFYuocnHOzc3LbbbcrVyLSxjkp4/ix43qvXbt323NpcE4aFSToZ9SNMXw0K640"
    "uCLNIjOYo6fV+7lvgeoL6NopQoD+h47o8FBWR+O6blE7EWS5mh82f89UpEzbhRQYJ+0hnbgxmSiUboOkMLi4MRXjeuaXdyLMErI/t+nd/TiKwqDZbEJ8"
    "/3phYeF/zeh8f04hVUp7+OGHu0EQ/OiWLVu+1O8nP9Tt9l4Vx3HVMTUmVi6XY22uRKxbq6kiDuKxTaGV6KSWLgPOcH+iEeXyRV4VFlE3RZN/+tJPg131"
    "/RRG8QfiPbLe4EJ0XWIxzp8/Kxv1unI+OCGhV010oA3jiF48x+uauE7pB0AjfzJFcxAfbCQtH/ju1ukZTVRHpL/2dW9Qka4phsw5bRaDcXLiuRNy2WVX"
    "qO4J8WoARSal1V1yToAu3iBURQJS0J21AqbQ3ih0ei/kpY34TTPsfL0ynEbL6S0tLaHZDw4FO+P6WpbT+eEzgtnsQXepPmwXsjo9wGkG4Vjjch9cy0Fu"
    "N4J8fra+YT8IEvS9uNfr/bOFhYX/mBG7f94aSjmghqFgppw/f/5377777rt/6qd+6rpGo/F3er3ea7rd3lUi8c5qtRYVCnlCaZQA0YEI6OTEEPBpNZOr"
    "0mqRwhipNeTlyZygjFgtJJ0N8qKSSiQejpUJhDCRpbxXFwUMEPF66tRz0qzXBQCae45MjGuXSwjQFXKHKvzVTyzc0XqpmV+ThSQymVxdDJGFuXlVO+gB"
    "NzE5o1l/evLT6GKI86tf+5q25dq9b6+pJBcF0hrHQoxlgWMbaaR36ufm3rrZ+JAR26RjAmmQpOA5y6kvOuXcGs2EhNFIGoWpxFEHGMRFm4yDwYnH6H3T"
    "b5+OwVdSNSWgeyk95jwJbHPvLH3CpVhK/ETTJ71ej8xK8ovA+U53u91/NDc394mvJ3YvIuqL/nWJhcLNtm/fPl4sFv9OEIS/Wa3Wyt1uN1lZWQ4o/jNU"
    "G9bMMSxC3GdwjWNHnxkEMNKJmxOFUu8hPUxcORC4nlaBijRfltOG3gTH0zCnlEtRLdQaVEO0JtqCuK91+S5QGDIQyVOMqDYk5XxBxRZE4hHBTvCuB7JO"
    "fpIRwXBKlHm42ML8gsxMTcmrb73VdNgW+Sem+2h0tgTy5Ycf1prXt9xyq0YDYcC00+oCvbRKBMWLVpeWtRWtt0pgHgDVtOWanZ/VMnPoVkiILTPbVCLU"
    "gpyM4XkJ+9Lq9GV1ZUW/D2fWuN0gyDUajSeXl5d7+Xw00e/H1SSJ87lcSML2gF1lVQ6Gq04OjTk3tWFc0bwUujcQU5Iam+qaNehns1Rdev00nBe1Q6th"
    "JN1u5/eq1cq/PH78+KlLaenrjYt5rJnHZgoZV4zPnDmzJCJ3792793viuPcO4sVRFVhAqqSqF06z1npaiPv8+dPSQffR6gVrsm37NuWGlj1n3djpyugn"
    "vtftqOdAKyhQfFyxPCv5pr3hnGtSKwWPSQ8iLMq+A5fLxNSMNr2hGupyoy3rRSOocnVYhjQyBT+dVWlwUWFlzzajWLwYT6VclZtvuEkuv/xyw9XQg7Rz"
    "JMEqlrD1+JEjWsXg1lteLZVyLa2CkKho1tyVfl97DZcLRVnotKVYnBjAGMoxEL9UgCDgliAMbYlGfGIiQaOtpdpwzHdiQqrW1bZA5OEsSJIkn8/nD7/t"
    "bW95/3333RcnSVJZWlqqtVqtSpIktW63O9zv92vtdrsUBEEtDMOJOI5n4jgeD8NwOJ/PD/N+HMflIAigaCzOQhgq8VaSJChhePb7Fh+ajZI28WptLjYN"
    "EiXcZr/fP9nv9z8bRdHhubnZz6aEdhHU8heNSwnQ5MTF+Wt8BiznI61W67sLhUII5wAbQ5Sp/pJaRoVipK24nn76WSkhqrUt66oaJHgXENfGuo3ImCZE"
    "hR6npyotdm61CsENM5GtqYXpjXTgdLSaHx8bk/XVFZm/MC9LK6uysnRBltUIyCs4DTcdNMZRCIQcDOqhWE3l0dER7Rx0YN/BQUEfjzzWtIAUA3388Sfl"
    "3Lnzcuutr5axsQltZONGgRoZaX2dmelpWdcuRRYZ43qa64SoL+ZNwXtgyewaxpYee6RCP7FC7NSxoYtBEAT5JIm/ur6++sEPf/jDmL0M8kW/ocE84jgO"
    "v/3bv71w9uzZQqPRyHe7K/ler1hot9vFWq023O12a51OpxgEAQSNw3sol8vVgiCoQrRxHGtpMDDjXC63COEVCoVjQ0NDzx0/ftyiODaZ1wDn+8vG8xHg"
    "pUMvNjMz8+nFxcWvFovF60nlxCSmAybRIcrCiero9GR8fFKGh2lrUNfFpXj3yMheLWlGtXwV2YPABAvQZP8U79KAz0zdOeWG4GJpbmxaJkRpGLZPP99c"
    "pLoatZc77YZWGyBYod5oWNQHulSH8HTrmIRIGx2bVJ1vZmZaux0hguHgjRal0QwuIZ9Ek+87XfnqI49IvdGUb//2N6hhBTboxJd10GvxzlJJTp54TqXB"
    "Jg5nFib/dpeVgvpp5yXyR1E9SBHoxKRmEp+o1RniXC5HJ4Oz1Wr5XY8//tgCDnx8qJkN93GpOuVDFUfc5SKCQmtKrQ6rMAHm+VcdGGSprsf9Tdy8gPGN"
    "EKBGfT/88MONXbt2/Uq32/3PcC02ko0wLli14ol661D27NkrTzzx2MDqmp2dl23btipRokuh92niUeo6w2iBCLWmiIpHS+QhIrhPAZqYKGjK+KbeBWs1"
    "Y3keQCSkQxKpXCzLTG1Etu3YZYdR/dtWjRNiwkJH3yQtk8AAs1x70mi09DpWIoSwMFKIC7J4YUGeePwJGRoZlZtfdatEeYDfi0uY8QyOyxFDSPFxBigB"
    "TXKc8NwK9goKBsH0Lb6wH0uxXNIYSfKZWadKqRgXCwX0rPVisfw9Dz744ImU+LLc5YVs9vMRaPa9r0fAf9FwaXkRuPxChvf0+8uG2qKFQuH3Op3OU0mS"
    "hMViMWZTEbEOdSCy4IJwCQwQREyYs+pRVI2io5ByjLQEhlYcUP8sRGnGgVqo2hDZKiN4eQ48AwqcamK4VfOnmBFgsRoKCmTnhCT0ZieRdo9Yw0ir2Vs8"
    "nJWWQ08jTpDWWRZwaUo4r1jl6KIkOD1x5El58smntfn2a17zWqsV08S4AaawkmZOfHwfFABjga7xeIY8Q47hijw1ZDhk7kFwvy7B0MoR0T3bLVVZa9Ua"
    "4q6fy0Xve+SRB+99/etfHx0+fBHxvdDhxJJ9NTTcfiDsF/rz54DlFzq+UQJk0uHRo0fX4jj+TwDTcJAqlmKjoT+W0+udlmLtCVypDEmvG6v3Y2F+Vgl1"
    "6/Yd2lTGxTAJ53yvR4dwrBsqbrUa0u40pNNDhHa0LnSX/A3yFTp8noidolqhGtCpCeV9TevURE+tCWiVtcgVthxh++mm4f8Mr8BgREKp4bYcP/GcPPX0"
    "Mxr39/rbbpc9+w+ol0MriHbbWiyzRQswYBySjuJYRoeHJR8GsnxhQdqtpgwNbfrGsxwQzuauTF6tsn1iifI0HOzSNHu9PzxWzRUKuXqYC97z8MMPfhTO"
    "d88996SI8d+s8Y0SoO5X6jX5L+126xHyicvlUt/0vCXlbO5uMgA7kv37D6poVRReAjl9+rRyR4wS1flIvg7AzCz0B2zRvSe42uCgYH3+41HSfI4EJg9N"
    "Mk4SaESJ9gNO/agQpde89rrNpj6mwZ7dvnptZmfnlPDo6VGrDcnNN79KrrvuOjUkNlLMUJPatYwt/UY4CFb/ZYw8Esqm5XJy4vhxNUK8+bdH5riRBhrg"
    "uiN/s0oJfcmXCgrlbDQa/WqlEg0P1ZbLtdo7H3nkkT96ETjfX+vxQuW+mtd79+59Wy4XfSyXi/qtViuEANF/AJ6VVaY9JdC3zp87JyeOHdVYPDaGouB0"
    "Vud9TSDKW81B5A6ueKoWUK+F63g1qQohX8WS1mKJCkVtbg2m5gGXCjaraE47L2kOMM2QLXHcANiLE8zdQOBgMKfa8OggGNXzZOHS7tVxpzv/Vh90rycj"
    "Q8OaU0KRczqDLi0vyxWXXz6IEN6MMKLIEYXUTypnxvvC8LwTzXVpNXtxkuRHRkdOjY6Mvudzn/vcAxDf31TO5+MbMUKyAx0hfO65Ex/fv/+yPwyC4F35"
    "fL5Xq9VyECGFu6tDNU1NBLZFb6NBS6uxIefOz6a1UFq6Efv3HFTjYpU+cgUSu61Cf0KeblqOAgili+eiH0uZCqzlHC6JtKbCZpsv9R9TVZ62q+h6BiLq"
    "q3Y7SjsycX0vrm4uOXPLQcCaR5zGCbpx5GC263z8Hc7MGB0e0d7C2sCx1dZnogWqGxkqMlIPCde3Bo+IbGogdhQ+4nCQJdfqdAgfydeq1SfHx8bf/ZnP"
    "fOZIanD8jRS72fFCCdB4VUIoUPQvut3+t+dyudFKpZI0m81gbm5OthcLhtyn0c+IrgP7D+iiL5CtVirK+tqGnDhxUg4c2C+nz5yUxcUF65qeZplhJMAJ"
    "c/qf+WDZeKDDAnVYch60sOnbxBYhYIDg1UHsnHbgTLukZxrOMFQsEoBJ+Fim4oC5xzCMzNjwV4wHiAuxSX5JfX1DISQibj73+c9qg0LPy/DrM7gvHG+F"
    "5t4SWIPFTDX7WGEBKiTnv7B9+/bv+dSnPnXmeazdv7HjhYpgH+iO8d69+3+oWCz8Wq/X7bXbnRwitVob0pal5sM0r4N2xgwDeeyxx7UqPESIQj82MqEA"
    "8NzsOTl//qTWY8bKtXwSK6ER5embZk2sYWWkPhKiVSqWlaN6lpkSbAqv8Bm4n4ppstfSMhpadV59zlar2hykwDEYMGmZkJQTeiAreh/EByEViyUNn2o2"
    "qJZKs+oZ+cIX7lVjAgL05BxXKbx6PlgZPyq+1UgZ8mjmXqlUosD1J0b3jX7vlz72pfW/TcTH+KsSoB5u1LQDBw78bj6ff2+r1ew1Gq0cHhIU8anp6QHM"
    "ADF5cOiRJ45oAGW+QDWCQGrVYTlwcL/U6ysa4gThuhtIgyipRponl8N8wgZvUDelIKViQfVMrTaP7qifM/1QDwDfoUqB0q/hgKqXDSp1Wc8ShZHSaBaG"
    "cr20cjyGlffrxTvRbTc1+pmo3wceuF+DFTBYvC6ytaewSmBxms/yzNNPm49a21doyy8Fhms1AjwKh6+++ur3feQjH2n9bSO+b5YANZL8iiuuGI/j+P4w"
    "DA80m83+6tpGiJJOs2ZCtOwu5sdN/Zpy5IknFLIggAHsC8514OABKUaRHDt2TBV2ryBKziwcTCsmaJACgQmRgtQcH4wY9D64J4YOYtGJFcDbRa9hcXhU"
    "0jM38E7g7zVsVzO7NE7RuKMT8sb6uhIQ3yRZil7D999/vxpRtGP1sHkPVtWo7m5HK/ufTTuPow+mtaHjcrkc1Gq1cHh4+L9cddVV7//VX/1Voh5UqvyN"
    "lbVfZ3wzHHDABQ8dOvSaXq/3aZGgSOTw+vp6wKYQ7Ek8nSdUOzHAyY4/+6ycO39OC3RrPFgYyc4dO2TLzIycO39efccMz1e26F1EsHE65XakUqZALxHZ"
    "5NPCnTzmT5NiUm6oUE3qjtP0IJ48UzhI+4QpRGOh9aoXJhClVT3gCzxLbagqX/jC5xVYh/g8BpDhET8YNFR0IDSNRoUMiI/8iJGRkahSqcTDw8M/ed99"
    "9/2HwcVfoAvrb8r4ZglwQIQHDx78H0WC/xKGud7GxkYIEUI0O3ftlNpQTZfXCVBhk3xBzpw5ISefO6Y9PoKkoHkRcBcSgCAAcDX8x3weQjQysKAFuJ4H"
    "TUJYmotLz5G0eLgSIeV4Ux10MzaP3kwek2jiEl2NagtwPYdntCYeRk2KTXoC1D2f/5wWKLr+uuvNc5IegM04R0vMIrbw6SefUJ90qlf2x8fHo7GxsXND"
    "Q0M/+IUvfIHSFIP8/L8pBPVCx4tBgAMi3L1794dKpfK/QZrV6/UIJzeEtG37DuUeHiKveSIo9XlceSsaPUOcXKgJAvh9I9m5a7ds3bZdGqsrcurkCS9s"
    "Y7VaMCbQ59I6z4DeiF8tv5vmbOB+Mx+wiX93e5kHxh7botLTzDRNTbHYN8X/ALR7fZmanFTiO3H8hHz5oS/L1PSUXHHFFQNCHQyiZqJIY/gmp6bk1Mnn"
    "NGYR0d/r9fqTk5PRzMzM1+I4xq/rMMs3HDXyN3W8WATIdXCc93fs2PaLtdrwP+r3+91WqxXhK8YbQvdwUvc8lNtBWm9Fdez4MbmwcF6tUgiQkKRSpSL7"
    "IcSZaVldW5PTp8+o3kUVfbOAwQ/NF8z1nBC1YiniWw0XS7RHj9RoNg2+xJfsXZbwD1s1VvXzEiKVz6v+iqGB6HzooYfUi3Po0CGtlqCZf2mCj4ViWfVR"
    "5kZmGDrsU0896YXL+5VKOTp06NAXyuXyez/5yU+e/dsAMH+j48UiQJOOaWj/vn37PjI+Pv73u91ut9FoRhcuLKplSYolGwRX2EyZBBy2COj5+Vk5efI5"
    "jTJW3Y0c5SSUWm1Y9u7Zo+mP6JaL87OytDAv9caGBbdS1JvPB2asKIFp8+JQgtQQUUsYQtQOTeY2ZMLu3pNcQaN6gFYI04LInnzySXnqqadUnF511VX6"
    "Co7nYxAHWSho6zDNxKtW5ZFHHkkrFCS4KqMdO7b/wete97of+YVf+AUPp/pbz/l8vJgE6EQod999d/gv/sW/+M2xsbG/H8dJt9VqgxEGcAY4CyLNCdAt"
    "RwuTpzJpLHNzs3LmzGnN8wiikqZsYqlCAFu2bpUdW7dqX2C41erqklxYXFBguNu2qv1alVQpzvBDF6ua9YVOqNySwkolqVVrMjE5ISPjU8o5URueeeYZ"
    "OXr0qH6eUhrkBWucIlUXUp2Pv6HboRIspuXgOGAPPvigRgghefP5KF+tVj/yoQ996B9+4AMf+Ftr6f5F48UmwAERIqIuu+yyXyyVSj8SBLl+LpcLFhcX"
    "A1xSuK/wG3vmmudpgESgwhXIrOu0ZH5uVs7Pzct6nW7kps+p8RrlpTo8IpOTEzI5NaNFioBw8LNq1AoYnjaLQVQSfWzBCkA2BIwWS1YV1NIOKf22LufO"
    "ndHKCOSvQFSEjvHD71oRwRIqDChPjRX+RgADvmqA6BSaIaein8uF+UIh/1/OnTv3A2nmz99KmOUvGy8FAQ6IEFrZvXv3Tw0NDf/vKcfr1ev13OLikupl"
    "cEK8As4FVXTq1wkwpeKoucuWlldkDkJcW7MKCQApmsBu2XXUkUFMDw3VrI1qpaI6GTVqrEr9ppeDyBqCSjkI+K/JCQHn454jw8Max7hly4x+n3jDi0rg"
    "eqkN7dAZqf+XyGrUg/vvv4/0zoRCPIVCISqXy//32bNn3p9mkXkyxcvjkvFSEeBAJzSX3a7vKxbL/1c+XxgtFovdJElUL8SzgM5kNWCso6QHbxrRWJEf"
    "NTaoBd1uy/LKiqwuLVplhJZFpWiaI9HTRGillRU0wBV2mlbid65FDw58y0wMIwURPDo2pqH5w8MjgypgOtIOnNkEe7wuwCxwS8QzhgrEt7i4EFvCfj5X"
    "qVT+94WFhQ+lCf12ol4ezzteSgL0oS67Xbt23ZDP53+5Wq3eXC5X4lKplCwtLYeesol+5+W8nGOpVeMdmlLHvlq0BB5ofi99f63gYof8D7pWai85ckm0"
    "0ox2LXJXoIbkF0pSLg1bp8uapU3CnT083/C8VG9Ma9V4KimDgAuglptuukk/++Uvf1nW11f7cRxHzG18fPyfPffcc/+RqPHnSfB6eXwLOWB2KBFee+21"
    "1Y2NjX9dLpd/rFSqhKVSCcU8t7CwEBCKjygGqvFO3yq+BvWYN8OveF9r9lGbOT1CMdVUFUqxXnMEwVJ3JgjzSkDof9ZGK9SEer7nWW/ej87rpKjRgkck"
    "sVxeCAtRjb6Hn/uaa65RWOaxxx6D+HvYT2EYLE9OTn7g2LFjh0keT91qL3O+v2R8Kzigj4ESvnfv3reGYfR/RlF0EN/q6OhYb3V1NUeJDAgR5V7dXrWa"
    "lfXIlBzzqgqE/GPREu5Ffi3le3GxUbZNxWSrpcXMKZ9LZavFC0uWJJUqB/46cEVQgsHo0qxl7hsnsr6xrgn3uPiuecUrVGw/8fjjVNNC5GJwRMVidGRy"
    "cvLvPfnkk1/5RhOyXx42vpUE6PeDEPs33XTTxMLC4k8lSfwjU1NTlWqV9FOJm81GDrHsvSjKaWMVLGfXxQCTsWDRHx3YHhoa1sZ/GjSaEjFZadVKSbZu"
    "3aLl18hYA2TWmpCZrpXm4KM2jfV/s6pTqxY6VijKwcsOyvTUlJw8dUqeevKpZGNjg3KzeeZQKpX/69VXX/lPPv3pT5PA/w0nZL88/vsQ4EV6If+4/PLL"
    "b2w0Gh/K5/PvIJWxWq2R9U9pr7Beryt2CEFglXqV0ogSwEjTNCoaQyVH5ad+ovm4iGGvCk/OB3CNx+MN2HFaosPrSnc71poAS9tL7u7Zs0sNJDjgM08/"
    "nSwuLcUUW+S7hULhmZGR2p3Hjp34vbQEy8swy19hfKs5YHao+w5umNag+a5cLvrn+XzhNrhd6k7rYUn2ej2CGwadyPH7FstlKZdLgw5AUY7i6OZe83hC"
    "LeVB9/W0xrIP/u3h9nBajBiAa+4LNARGyTUWFuZU1AKv4FZUXbJQWCkWi790yy23/CyNVv6i0mMvj798/PckwKxuqMlqJPDv2bPnu5Ik/KFCIf9WZBw6"
    "IDnIcEXqljSbzZC8XYvdo4qoVbhXAkxdeh75ojJf67tYqJWHTnlQBNeGq8LlSK0EpIYLzs3NKdGtr68GrVYrx/eiKFqs1Wq/vW3btl+8//77j6aTf1nk"
    "fpPjrwMB/jmxnLrAbup0et8TBOHbcrnwAGAzjaEtZC/up1EscEe1G7RDZRpWbz5ar4hg+R8aup8GrFoNQdMpsZZbrVZS39iI19fXk7W1tVyz2Qqth7IW"
    "6XmqVqt9ZPv27f/13nvvPZ0hvG86Kfvl8a03Qv6y4WJ5sLnXXHPNWKvVfUOv1327SPL6MAz3AEwTH6jWqlVzpd+EpgCngQ5azVU9Fikg7WmZsFl0NqoU"
    "pKmWOYwXQvC9QXYYhmfy+dKnx8eH/+gHfuA7/uzHf/w/Wh6lGRlWXenl8aKMv04c8NLhSfODzcZyXl5evqHdbr+m3+/fGIbhoSAItuZyYZGzpIGuCipf"
    "3P08G+UMkcEdM8XWId75fD7/TD6f/1KlUvnsNddc89Dv//7hpUyt5ZdxvZdo/HUmQB/OFS/iPHC4V77ylVs2NjYO1uv1y3u93sFcLndZq9UaI+c7CIIR"
    "7BE3EtJeKDh918rl8moQBMfDMHy6Vqsd2bZt21N/9md/djpbzjfldspdX3alvXTj/wfpWqBH6GwHQAAAAABJRU5ErkJggg=="
), "fresno": (
    "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"
), "wendigo": (
    "iVBORw0KGgoAAAANSUhEUgAAAXgAAAIhCAMAAABzKlE2AAADAFBMVEVhX2Cbn6BmWFdcX2EZFBLa2ttfTT0dHhsiGRhLIx7Z1tGdm5+anJ9OPUI9Q0WV"
    "b2qGfoHCvrjFwbu6vsG9wshFOzSQfIfFwbzd3+N9gHzDwb1JQTuCeXaFgHs6PEA7PUBHPUC4vcK+wcM+QkRCKh19gHuCa22+wLm8wcbCu7Q4PUE9QT6A"
    "foA6Qjk/QEFjTDx+gHiFP0iBSjy8wb2Xkn+eln+9vsDCr6DDvsIvMDIxKSQtIxonGhJHOTA6NC1PQzlRSURmWVBaVE5vaWVuY1l5dHAcFhCGenCNiIWP"
    "hHcVCANsaGZZVVFOSUaYlZB3dXJHLCQvKiU5NTBpaGhYVlNraWdNSUZqaGh2dXNoS0RFOjN2dXVFKRp0dXVXVVRkWlRXVlVlRzpMSEelmoxKSEdMQzqK"
    "h4UlGhKtpZcvKSVqYlusqaWIiIgsIxuKiIeJiIg5NTG4tbA4NTMjDAM4NjNEOjQuKSaWlZOXlZGDenQpJBsuKidjW1VHMhzJx8VmOTRKQzuJg3tjW1cb"
    "FhCEaFqWlZMlGhNoY1vX1tKkk3wRCQOWlZNoYlyEe3ZDOjXIxLhiW1dlYVyIa2QpIxsbFxKpqKbDu7BlUj2JgnupqKe3trRKQzslGxWEclxpaGh3e4K2"
    "tbSDe3esqaaFWk93d3ZJQjt4fIKqqaf3+PYbFxNKSEdLGROCe3aLiolEPDZWVlZ8goaGgnyJg3waFhO3tbKWlZW3tbPo6OYtIxt7goeiinkkHBY5ODV4"
    "fIGim5VaXGGjm5iimpbX1tT29/ldYWRlKSqmoZymopvLyss1MB14fIJ8g4jKyMUSCQYeIBZpSEeFaWeYnaLn6ux7foGno52mqKvJyccsKylcYWVdYGOn"
    "op23trN9gIM+QDVaXWJ9goWbkXzk4tpELCZaXWJcYWR9cF2jnJTCvbnKycg+QkRZXWFiW1dnYl19g4fV1dcOCAU7PUI7PUFHDAdDLSacoaOlo5vh3dUx"
    "JRpsOkR3e4KFTEyEfYOdoaOli4O8sZzCvLW6YSVRAAABAHRSTlPlmatlZZ7in9/lZGTb45Lq256b4Jdeb27ZpNJcYVyx056W7uK85KfqZl1ezbNtXZtr"
    "+P5jpMtt+PMA+fr6+fj49ff08/fz+Pbz9/fQ0tHz0PvR0W+wsLCQsPnSj/xvkNJv+4/3cNHR0fev0vJu0bCOr/OP+2+wkG7Q0bBwsPv0/LDRj9L7jrCw"
    "8vzSrZCxk/dubveTr873+7Bvb5CR/Fxt0m+N+11xjq/wkV38jVxwXY9ukXCOXLHycmz8cV3P0W9wkdTVj/vRba/7rq5ts/fWy23T7bJd1l1q0I9c6/WN"
    "zvv20bGr+qrPkm3PXF1dtI5xkv24bVz3XfRc+5Ps8/xwuPJ0TgAA0o9JREFUeNrs/QdgXOeVJQjLoR2m3TlMh8lxd2Z299/dP+G9erFyQuWAAlCFnBNB"
    "AARAkASYIDGJUZRE5djK0bIky3Jo2+0c2rnb7Xa3O0znNJ3D7Dn3ewWACQSJIkXRKluJBBFOfe9+N5x7zk1Nb73ekNdNb0HwFvBvAf/W6y3g3wL+rddb"
    "wG/k9V/+9E87NvJx3/jGdry+8RbwjXn92b/KZpOFP5s6+1dfeKf65zvfuX1q+/aXH5sZHMzIK5st5Ce+8+H/8hbwm3r1/FnW1EzTTA4OTiroX3hh5t3z"
    "J0+enJ+fzi8nensTtUQym8loeOm6ppmWG44GE4lksetP3wL+ynFPmgKormcyJ2cm8ZoZVCCbhhUOR6PhQMBxHMsw+TE+H/6mGU4g6OKVynd1vAX8Fb3e"
    "UQXugJOAhkYRRfD/hKlehhWIhgVzw3IM9VHqI/GXgV90I5FgvFD9vbeAv+zXh/NJw1zBU0fEsUzN4EvQdqwAjrvVpgPnND/E+9AYP1g3LQfPQiRe7Kl/"
    "uvbcW8Bv5NVRTdiWRhx9Ps3HEGI4YQBtWYR+h+HcHcZ/dhpt9Rizir0eCvHfdUNz7eRil7obPvxsodrzFvCXxj3v2pahqyMMGHnUO8N77w4HBPkA3oZO"
    "Ar2VH7H6t1gsFurvPxCLqZPvw1OSVHj/XjWPG7fnLeDXf3UliLthAPKYAJ82jLY2hhjDF9L1tKPHtiqo+Rrt79/TPzo4ODM5s337FF4z8/v3HDgQ46Og"
    "9aa6CPdrk8WkbSe7Hn8L+PVwT7quZelAuU0XeHU54b62HYggeCtiW7cymPTjtX///rsA9/ZzP8X2qbs+fwCHf08l0dWB9Kanq5g0/71tX41Df9ONg7tt"
    "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"
    "VX3ybwtkSaZCC42UAAAAAElFTkSuQmCC"
), "kraken": (
    "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"
)}


def sprite_frames(sp, n):
    """טוען תמונה מוטמעת ומייצר פריימים עם תנועת זנב ועיניים זוהרות."""
    import base64
    import io
    raw = base64.b64decode(SPRITES[sp["key"]])
    img = pygame.image.load(io.BytesIO(raw), "sprite.png").convert_alpha()
    width = sp["w"]
    margin = sp.get("margin", 34)
    h = int(img.get_height() * width / img.get_width())
    img = pygame.transform.smoothscale(img, (width, h))
    rgb = pygame.surfarray.array3d(img)
    al = pygame.surfarray.array_alpha(img)
    Hh = h + 2 * margin
    xf, yf, amp = sp.get("wag", (0.42, 1.0, 26))
    ylim = margin + int(h * yf)
    bodies, glows = [], []
    k = np.clip((xf - np.arange(width) / width) / xf, 0, 1) ** 1.6
    if sp.get("wag_side") == "right":
        k = np.clip((np.arange(width) / width - (1 - xf)) / xf, 0, 1) ** 1.3
    for i in range(n):
        t = i / n * TAU
        shift = (np.sin(t + k * 2.5) * amp * k).astype(int)
        r2 = np.zeros((width, Hh, 3), np.uint8)
        a2 = np.zeros((width, Hh), np.uint8)
        r2[:, margin:margin + h] = rgb
        a2[:, margin:margin + h] = al
        if sp.get("bob"):
            dy = int(abs(math.sin(t)) * sp["bob"])
            r2[:, :Hh - dy] = r2[:, dy:].copy()
            a2[:, :Hh - dy] = a2[:, dy:].copy()
            a2[:, Hh - dy:] = 0
        for x in np.nonzero(shift)[0]:
            r2[x, :ylim] = np.roll(r2[x, :ylim], shift[x], axis=0)
            a2[x, :ylim] = np.roll(a2[x, :ylim], shift[x], axis=0)
        s = pygame.Surface((width, Hh), SRCALPHA)
        pygame.surfarray.pixels3d(s)[:] = r2
        pygame.surfarray.pixels_alpha(s)[:] = a2
        bodies.append(s)
        g = None
        if sp.get("eyes") or sp.get("spots"):
            g = pygame.Surface((width, Hh))
            for sx, sy, sr, sc in sp.get("spots", []):
                add_glow(g, sx * width, margin + sy * h, sr, mul(sc, 0.7 + 0.3 * math.sin(t * 2)))
            col = sp.get("eye_col", (255, 200, 120))
            pul = 0.75 + 0.25 * math.sin(t)
            for ex, ey in sp.get("eyes", []):
                ex, ey = ex * width, margin + ey * h
                add_glow(g, ex, ey, sp.get("eye_r", 46), mul(col, 0.55 * pul))
                add_glow(g, ex, ey, max(4, sp.get("eye_r", 46) // 4), mul(col, pul))
        glows.append(g)
    return bodies, glows


def explorer_frames(k=0.85, n=8, pad=30):
    """החוקר עם מצלמה במקום ראש."""
    import base64
    import io
    cam = pygame.image.load(io.BytesIO(base64.b64decode(SPRITES["camhead"])), "cam.png").convert_alpha()
    cw = int(50 * k)
    cam = pygame.transform.smoothscale(cam, (cw, int(cam.get_height() * cw / cam.get_width())))
    cam = pygame.transform.flip(cam, True, False)
    out = []
    for f in render_frames(lambda S, t, s: paint_explorer(S, t, s, head=False), 92, 170, k, n):
        w, h = f.get_size()
        big = pygame.Surface((w, h + 2 * pad), SRCALPHA)
        big.blit(f, (0, pad))
        big.blit(cam, (int(52 * k - cw / 2), int(pad + 38 * k - cam.get_height())))
        out.append(big)
    return out

# ======================================================================= ממשק


class Button:
    def __init__(self, rect, label, size=34, col=(30, 130, 190)):
        self.rect = pygame.Rect(rect)
        self.label, self.size, self.col = label, size, col

    def draw(self, screen, mouse, t):
        hover = self.rect.collidepoint(mouse)
        r = self.rect.move(0, -3 if hover else 0)
        base = mul(self.col, 1.3 if hover else 0.9)
        s = pygame.Surface(r.size, SRCALPHA)
        pygame.draw.rect(s, (*mul(base, 0.45), 235), s.get_rect(), border_radius=20)
        pygame.draw.rect(s, (*base, 220), pygame.Rect(4, 4, r.w - 8, r.h // 2), border_radius=16)
        g = 0.5 + 0.5 * math.sin(t * 4)
        pygame.draw.rect(s, (*mix(base, (255, 255, 255), 0.45 + 0.3 * g * hover), 255), s.get_rect(), 3, border_radius=20)
        screen.blit(s, r.topleft)
        text(screen, self.label, self.size, (255, 255, 255), r.centerx, r.centery - F(self.size).get_height() // 2)


def gradient(size, top, bot):
    w, h = size
    s = pygame.Surface((w, h))
    for y in range(h):
        pygame.draw.line(s, mix(top, bot, y / max(1, h - 1)), (0, y), (w, y))
    return s


def hab_colors(md):
    hc = md["hab"]
    if hc["kind"] == "forest":
        return {"desert": ((120, 170, 225), (170, 120, 60)), "town": ((25, 30, 60), (6, 10, 16)),
                "snow": ((30, 40, 70), (120, 130, 155)), "dover": ((22, 24, 50), (10, 16, 12))}.get(
            hc.get("theme"), ((90, 150, 210), (40, 80, 40)))
    return hc.get("top_col", (30, 40, 70)), hc.get("bot_col", (5, 8, 15))


class App:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.snd = Sounds()
        self.t = 0.0
        self.state = "title"
        self.found = self.load()
        self.mframes, self.dframes, self.portraits = {}, {}, {}
        self.exp = None
        self.cur = None
        self.loading("טוען את המפלצות...")
        X, Y = np.meshgrid(np.linspace(-1, 1, W // 4), np.linspace(-1, 1, H // 4), indexing="ij")
        r2 = X * X + Y * Y
        a = (np.clip(r2 - 0.4, 0, 1.5) / 1.5) ** 1.2 * 225
        v = pygame.Surface((W // 4, H // 4), SRCALPHA)
        v.fill((0, 0, 0, 255))
        pa = pygame.surfarray.pixels_alpha(v)
        pa[:] = a.astype(np.uint8)
        del pa
        self.vignette = pygame.transform.smoothscale(v, (W, H))
        rv = pygame.Surface((W // 4, H // 4), SRCALPHA)
        rv.fill((190, 0, 0, 255))
        pa = pygame.surfarray.pixels_alpha(rv)
        pa[:] = (np.clip(r2 - 0.25, 0, 1.5) / 1.5 * 255).astype(np.uint8)
        del pa
        self.red_vignette = pygame.transform.smoothscale(rv, (W, H))
        X, Y = np.meshgrid(np.linspace(-1, 1, 170), np.linspace(0, 1, 700), indexing="ij")
        shape = (np.clip(1 - np.abs(X) * (1.2 - Y * 0.6), 0, 1) ** 2 * (1 - Y) ** 1.5)[..., None]
        self.ray_sprite = pygame.surfarray.make_surface((shape * np.array([36, 46, 40], F32)).astype(np.uint8))
        self.ray_warm = pygame.surfarray.make_surface((shape * np.array([60, 52, 28], F32)).astype(np.uint8))
        X, Y = np.meshgrid(np.linspace(-1, 1, 64), np.linspace(-1, 1, 64), indexing="ij")
        ink = pygame.Surface((64, 64), SRCALPHA)
        ink.fill((4, 2, 8, 255))
        pa = pygame.surfarray.pixels_alpha(ink)
        pa[:] = (np.clip(1 - np.hypot(X, Y), 0, 1) ** 0.8 * 235).astype(np.uint8)
        del pa
        self.ink_sprite = ink
        self.thumbs = {}
        for md in MONSTERS:
            bw, bh = md["size"]
            k = min(212 / bw, 124 / bh)
            rim = DAY_RIM if md["hab"]["kind"] == "forest" else WATER_RIM
            if md.get("sprite"):
                fb, fg = self.monster_frames(md)
                b = [pygame.transform.smoothscale(fb[0], (int(fb[0].get_width() * k), int(fb[0].get_height() * k)))]
                g = [None]
            else:
                b, g = render_canvas_frames(md["painter"], bw, bh, k, 1, rs=1.0, rim=rim)
            img = b[0].copy()
            if g[0] is not None:
                img.blit(g[0], (0, 0), special_flags=pygame.BLEND_ADD)
            self.thumbs[md["key"]] = img
        bw, bh = MONSTERS[2]["size"]
        fb, fg = self.monster_frames(MONSTERS[2])
        sil = pygame.transform.smoothscale(fb[0], (int(fb[0].get_width() * 0.75), int(fb[0].get_height() * 0.75)))
        g = [pygame.transform.smoothscale(fg[0], sil.get_size())]
        sil.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        sil.fill((6, 16, 32, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self.silhouette, self.sil_glow = sil, g[0]
        self.title_bg = gradient((W, H), (12, 45, 75), (1, 4, 12))
        self.snow = [[random.uniform(0, W), random.uniform(0, H), random.uniform(0.3, 1)] for _ in range(120)]
        self.eyes = [[random.uniform(80, W - 80), random.uniform(330, H - 60), random.uniform(0, 8), random.choice([(255, 200, 60), (120, 220, 255), (255, 80, 60)])] for _ in range(5)]
        self.buttons = []
        self.mouse = (0, 0)

    # ------------------------------------------------------------ שמירה
    def load(self):
        try:
            with open(SAVE_FILE, encoding="utf-8") as f:
                return {k: int(v) for k, v in json.load(f).items()}
        except Exception:
            return {}

    def save(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.found, f)
        except Exception:
            pass

    # ------------------------------------------------------------ גרפיקה (מטמון)
    def monster_frames(self, md):
        key = md["key"]
        if key not in self.mframes and md.get("sprite"):
            self.mframes[key] = sprite_frames(md["sprite"], md["nframes"])
        if key not in self.mframes:
            bw, bh = md["size"]
            rim = DAY_RIM if md["hab"]["kind"] == "forest" else WATER_RIM
            self.mframes[key] = render_canvas_frames(md["painter"], bw, bh, md["k"], md["nframes"], rs=md["rs"], rim=rim)
        return self.mframes[key]

    def decoy_frames(self, kind, land):
        if kind not in self.dframes:
            cfg = DECOYS[kind]
            bw, bh = cfg["size"]
            self.dframes[kind] = render_canvas_frames(cfg["painter"], bw, bh, cfg["k"], cfg["n"], rs=0.85,
                                                      rim=DAY_RIM if land else WATER_RIM)
        return self.dframes[kind]

    # ------------------------------------------------------------ מעברים
    def loading(self, msg="טוען..."):
        self.screen.fill((4, 10, 20))
        text(self.screen, msg, 44, (200, 230, 255), W // 2, H // 2 - 30, glow=(40, 120, 200))
        pygame.display.flip()
        pygame.event.pump()

    def open_story(self, md):
        self.cur = md
        key = md["key"]
        if key not in self.portraits:
            self.loading(f"מכין את {md['name']}...")
            b, g = self.monster_frames(md)
            k = min(540 / b[0].get_width(), 360 / b[0].get_height())
            out = []
            for bi, gi in zip(b, g):
                img = bi.copy()
                if gi is not None:
                    img.blit(gi, (0, 0), special_flags=pygame.BLEND_ADD)
                out.append(pygame.transform.smoothscale(img, (int(img.get_width() * k), int(img.get_height() * k))))
            self.portraits[key] = out
        self.state = "story"
        self.snd.play("click")

    def start_game(self):
        self.loading(f"יורד אל {self.cur['place']}...")
        self.exp = Expedition(self, self.cur)
        self.state = "play"
        self.clock.tick()

    def to_select(self):
        self.snd.stop_loops()
        self.exp = None
        self.state = "select"

    # ------------------------------------------------------------ ציור תפריטים
    def draw_ocean_bg(self, dt, scary=True):
        sc = self.screen
        sc.blit(self.title_bg, (0, 0))
        for i in range(6):
            x = (i * 260 + self.t * 12) % (W + 300) - 150
            sc.blit(self.ray_sprite, (x, -40), special_flags=pygame.BLEND_ADD)
        sx = (self.t * 25) % (W + 1400) - 1100
        sy = 300 + math.sin(self.t * 0.4) * 30
        sc.blit(self.silhouette, (sx, sy))
        if self.sil_glow is not None:
            g = self.sil_glow.copy()
            g.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_MULT)
            sc.blit(g, (sx, sy), special_flags=pygame.BLEND_ADD)
        for s in self.snow:
            s[1] = (s[1] + 10 * s[2] * dt) % H
            s[0] = (s[0] + math.sin(self.t + s[2] * 10) * 6 * dt) % W
            c = int(90 + 100 * s[2])
            pygame.draw.circle(sc, (c, c + 10, min(255, c + 30)), (s[0], s[1]), 1 + (s[2] > 0.8))
        if scary:
            for e in self.eyes:
                e[2] -= dt
                if e[2] < -2.5:
                    e[0], e[1], e[2] = random.uniform(80, W - 80), random.uniform(330, H - 60), random.uniform(1, 6)
                if e[2] < 0:
                    k = min(1, -e[2] * 2, (2.5 + e[2]) * 2)
                    blink = 0.15 if int(self.t * 3 + e[0]) % 9 == 0 else 1
                    for ox in (-14, 14):
                        add_glow(sc, e[0] + ox, e[1], 16, mul(e[3], 0.7 * k * blink))
                        pygame.draw.circle(sc, mul(e[3], k * blink), (int(e[0] + ox), int(e[1])), 3)
        sc.blit(self.vignette, (0, 0))

    def draw_title(self, dt):
        sc = self.screen
        self.draw_ocean_bg(dt)
        bob = math.sin(self.t * 1.5) * 6
        text(sc, "ציידי המפלצות", 96, (255, 215, 90), W // 2, 100 + bob, glow=(200, 20, 0), shadow=4)
        text(sc, "מצא וצלם את היצורים המסתוריים של העולם... אם תעז", 28, (210, 230, 245), W // 2, 230, bold=False)
        n = len(self.found)
        if n:
            text(sc, f"מפלצות שמצאת: {n} מתוך {len(MONSTERS)}", 22, (150, 240, 170), W // 2, 275)
        self.buttons = [(Button((W // 2 - 150, 340, 300, 84), "שחק", 46, (40, 150, 70)), "play"),
                        (Button((W // 2 - 150, 450, 300, 70), "יציאה", 34, (150, 50, 40)), "quit")]
        for b, _ in self.buttons:
            b.draw(sc, self.mouse, self.t)

    def draw_select(self, dt):
        sc = self.screen
        self.draw_ocean_bg(dt, scary=False)
        text(sc, "איזו מפלצת תעז לאתר?", 48, (255, 220, 120), W // 2, 18, glow=(255, 80, 0))
        self.buttons = []
        cols = 5
        cw, ch, gap = 234, 262, 14
        x0 = W // 2 - (cols * cw + (cols - 1) * gap) // 2
        for i, md in enumerate(MONSTERS):
            col_i = cols - 1 - i % cols
            r = pygame.Rect(x0 + col_i * (cw + gap), 84 + (i // cols) * (ch + 14), cw, ch)
            hover = r.collidepoint(self.mouse)
            if hover:
                r.y -= 6
            top, bot = hab_colors(md)
            card = gradient((cw, ch), mul(top, 1.1), bot)
            th = self.thumbs[md["key"]]
            bobv = math.sin(self.t * 2 + i) * 4 if hover else 0
            card.blit(th, (cw // 2 - th.get_width() // 2, 82 - th.get_height() // 2 + bobv))
            mask = pygame.Surface((cw, ch), SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=16)
            card = card.convert_alpha()
            card.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            sc.blit(card, r.topleft)
            sh = pygame.Surface((cw, 104), SRCALPHA)
            pygame.draw.rect(sh, (0, 0, 0, 165), sh.get_rect(), border_bottom_left_radius=16, border_bottom_right_radius=16)
            sc.blit(sh, (r.x, r.bottom - 104))
            text(sc, md["name"], fit_size(md["name"], cw - 22, 28), (255, 240, 200), r.right - 12, r.bottom - 98, "right")
            text(sc, md["place"], fit_size(md["place"], cw - 22, 16, False), (200, 215, 225), r.right - 12, r.bottom - 60, "right", bold=False)
            for s_ in range(3):
                draw_star(sc, r.x + 20 + s_ * 22, r.bottom - 24, 9, (255, 200, 50) if s_ < md["stars"] else (70, 70, 75), (0, 0, 0))
            text(sc, "קושי", 14, (190, 190, 190), r.x + 112, r.bottom - 33, bold=False)
            if md["key"] in self.found:
                draw_check(sc, r.right - 24, r.y + 24, 16, (255, 255, 255))
                for s_ in range(self.found[md["key"]]):
                    draw_star(sc, r.right - 56 - s_ * 18, r.y + 24, 7, (255, 230, 120))
            pc = (255, 200, 80) if hover else (90, 110, 130)
            pygame.draw.rect(sc, pc, r, 4 if hover else 2, border_radius=16)
            self.buttons.append((r, ("mon", md["key"])))
        b = Button((W // 2 - 110, H - 64, 220, 52), "חזרה", 26, (90, 90, 110))
        b.draw(sc, self.mouse, self.t)
        self.buttons.append((b, "title"))

    def draw_story(self, dt):
        sc = self.screen
        md = self.cur
        self.draw_ocean_bg(dt, scary=False)
        top, bot = hab_colors(md)
        pr = pygame.Rect(40, 60, 580, 540)
        panel = gradient(pr.size, mul(top, 1.2), bot).convert_alpha()
        fr = self.portraits[md["key"]]
        sp = md["anim"] if md["anim"] else 6
        img = fr[int(self.t * sp) % len(fr)]
        panel.blit(img, (pr.w // 2 - img.get_width() // 2, pr.h // 2 - img.get_height() // 2 + math.sin(self.t) * 8 - 20))
        mask = pygame.Surface(pr.size, SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=22)
        panel.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        sc.blit(panel, pr.topleft)
        pygame.draw.rect(sc, (200, 220, 240), pr, 3, border_radius=22)
        text(sc, md["place"], 22, (230, 230, 230), pr.centerx, pr.bottom - 50)
        rx = W - 50
        text(sc, md["name"], fit_size(md["name"], 600, 64), (255, 215, 100), rx, 36, "right", glow=(255, 80, 0))
        y = 128
        for para in md["story"]:
            for line in wrap(para, 22, 570):
                text(sc, line, 22, (235, 240, 245), rx, y, "right", bold=False)
                y += 31
            y += 12
        for line in wrap(md["tip"], 21, 570, bold=True):
            text(sc, line, 21, (255, 150, 120), rx, y, "right")
            y += 30
        self.buttons = [(Button((rx - 260, H - 100, 260, 70), "המשך", 38, (40, 150, 70)), "go"),
                        (Button((rx - 470, H - 94, 180, 58), "חזרה", 26, (90, 90, 110)), "select")]
        for b, _ in self.buttons:
            b.draw(sc, self.mouse, self.t)

    def draw_found(self, dt):
        sc = self.screen
        md, exp = self.cur, self.exp
        sc.blit(exp.photo, (0, 0))
        dim = pygame.Surface((W, H), SRCALPHA)
        dim.fill((0, 0, 0, 175))
        sc.blit(dim, (0, 0))
        pol = pygame.Surface((600, 420), SRCALPHA)
        pol.fill((245, 242, 232))
        ph = pygame.transform.smoothscale(exp.photo, (560, 315))
        pol.blit(ph, (20, 20))
        text(pol, f"{md['name']} - {md['place']}", 22, (40, 40, 50), 300, 352, shadow=0)
        rot = pygame.transform.rotozoom(pol, 3, 1)
        sc.blit(rot, (40 + math.sin(self.t) * 2, 110))
        rx = W - 50
        text(sc, f"מצאת את {md['name']}!", fit_size(f"מצאת את {md['name']}!", 560, 54), (255, 220, 100), rx, 60, "right", glow=(255, 120, 0))
        for s in range(3):
            draw_star(sc, rx - 30 - s * 56, 160, 24, (255, 205, 50) if s < exp.rating else (70, 70, 75), (0, 0, 0))
        mm, ss = divmod(int(exp.time), 60)
        text(sc, f"זמן חיפוש: {mm}:{ss:02d}", 25, (230, 230, 230), rx, 200, "right", bold=False)
        text(sc, f"תמונות שצילמת: {exp.photos}", 25, (230, 230, 230), rx, 236, "right", bold=False)
        y = 272
        if exp.confused:
            for line in wrap("התבלבלת בדרך עם: " + ", ".join(exp.confused), 22, 520):
                text(sc, line, 22, (255, 190, 140), rx, y, "right", bold=False)
                y += 30
        y += 10
        for line in wrap(md["fact"], 23, 520):
            text(sc, line, 23, (170, 230, 255), rx, y, "right", bold=False)
            y += 32
        if len(self.found) == len(MONSTERS):
            text(sc, "מצאת את כל המפלצות! אתה צייד מפלצות אמיתי!", 25, (150, 255, 160), rx, y + 14, "right")
        self.buttons = [(Button((rx - 290, H - 110, 290, 70), "מפלצת אחרת", 32, (40, 150, 70)), "select"),
                        (Button((rx - 520, H - 104, 210, 58), "תפריט ראשי", 24, (90, 90, 110)), "title")]
        for b, _ in self.buttons:
            b.draw(sc, self.mouse, self.t)

    def draw_fail(self, dt):
        sc = self.screen
        exp = self.exp
        exp.jump_t = 0
        exp.draw(sc)
        dim = pygame.Surface((W, H), SRCALPHA)
        dim.fill((30, 0, 0, 185))
        sc.blit(dim, (0, 0))
        name = self.cur["name"]
        if exp.fail_reason == "attack":
            msg, sub = f"{name} תפס אותך!", "הצוללת נפגעה קשה וחזרה לבסיס. הפעם צלם לפני שהוא מתקרב!"
        elif exp.fail_reason == "bear":
            msg, sub = "חיית הבר הבריחה אותך!", "היא לא המפלצת - בפעם הבאה עדיף להתרחק ממנה!"
        elif exp.night:
            msg, sub = "הסוללה של הפנס נגמרה!", f"{name} נעלם בחושך... נסה שוב!"
        elif exp.land:
            msg, sub = "השמש שקעה!", f"{name} נעלם בחושך... נסה שוב מחר!"
        else:
            msg, sub = "נגמר החמצן!", f"{name} עדיין מסתתר שם... נסה שוב!"
        text(sc, msg, 72, (255, 110, 90), W // 2, 190, glow=(255, 0, 0))
        text(sc, sub, 27, (240, 220, 220), W // 2, 295, bold=False)
        self.buttons = [(Button((W // 2 + 10, 400, 260, 74), "נסה שוב", 36, (40, 150, 70)), "go"),
                        (Button((W // 2 - 270, 400, 260, 74), "בחר מפלצת", 32, (90, 90, 110)), "select")]
        for b, _ in self.buttons:
            b.draw(sc, self.mouse, self.t)

    # ------------------------------------------------------------ פעולות
    def action(self, act):
        self.snd.play("click")
        if act == "play":
            self.state = "select"
        elif act == "quit":
            return False
        elif act == "title":
            self.to_select()
            self.state = "title"
        elif act == "select":
            self.to_select()
        elif act == "go":
            self.start_game()
        elif isinstance(act, tuple) and act[0] == "mon":
            self.open_story(MON_BY_KEY[act[1]])
        return True

    def click(self, pos):
        for b, act in self.buttons:
            r = b.rect if isinstance(b, Button) else b
            if r.collidepoint(pos):
                return self.action(act)
        return True

    def run(self, max_frames=None):
        running = True
        frame = 0
        while running:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.MOUSEMOTION:
                    self.mouse = ev.pos
                elif self.state == "play":
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_ESCAPE:
                            self.to_select()
                        elif ev.key == pygame.K_e:
                            self.exp.sonar()
                        elif ev.key == pygame.K_SPACE:
                            self.exp.take_photo()
                    elif ev.type == pygame.MOUSEBUTTONDOWN:
                        if ev.button == 1:
                            self.exp.take_photo()
                        elif ev.button == 3:
                            self.exp.sonar()
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.mouse = ev.pos
                    running = self.click(ev.pos) and running
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        if self.state == "title":
                            running = False
                        elif self.state == "select":
                            self.state = "title"
                        else:
                            self.to_select()
                    elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.state == "title":
                            self.action("play")
                        elif self.state in ("story", "fail"):
                            self.action("go")
                        elif self.state == "found":
                            self.action("select")
            if self.state == "play" and self.exp:
                self.exp.update(dt, pygame.key.get_pressed())
                if self.exp.result == "found":
                    key = self.cur["key"]
                    self.found[key] = max(self.found.get(key, 0), self.exp.rating)
                    self.save()
                    self.snd.stop_loops()
                    self.state = "found"
                elif self.exp.result == "fail":
                    self.snd.stop_loops()
                    self.state = "fail"
            if self.state == "title":
                self.draw_title(dt)
            elif self.state == "select":
                self.draw_select(dt)
            elif self.state == "story":
                self.draw_story(dt)
            elif self.state == "play":
                self.exp.draw(self.screen)
            elif self.state == "found":
                self.draw_found(dt)
            elif self.state == "fail":
                self.draw_fail(dt)
            pygame.display.flip()
            frame += 1
            if max_frames and frame >= max_frames:
                break


def main():
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Monster Hunters - ציידי המפלצות")
    App(screen).run()
    pygame.quit()


if __name__ == "__main__":
    main()
    sys.exit()