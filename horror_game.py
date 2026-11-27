import sys
import math
import random
import array
from collections import deque
import pygame

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
try:
    AUDIO = pygame.mixer.get_init() is not None
except pygame.error:
    AUDIO = False

W, H = 960, 640
RW, RH = 320, 213          # internal 3D render size (scaled up 3x -> chunky retro look)
SW = 1                     # pixels per ray column
NR = RW // SW
FOV = 1.15
PROJ = (RW / 2) / math.tan(FOV / 2)
H2 = RH // 2
FPS = 60
TILE = 40
TS = 64                    # texture size

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Night Shift 3D - The Toy Factory")
clock = pygame.time.Clock()


def mkfont(size, bold=True, serif=False):
    names = "georgia,timesnewroman,dejavuserif,serif" if serif else "couriernew,consolas,dejavusansmono,monospace"
    return pygame.font.SysFont(names, size, bold=bold)


F_TITLE = mkfont(86, serif=True)
F_BIG = mkfont(48, serif=True)
F_MED = mkfont(24)
F_SM = mkfont(18)
F_XS = mkfont(15, bold=False)

# ---------- Tuning ----------
FL_RANGE = 520
WALK, SPRINT = 120, 200
TURN_SPEED = 2.6
MOUSE_SENS = 0.0026
BATTERY_DRAIN = 1.3
LEVELS = 13               # brightness shades per texture

MAP = [
    "################################################",
    "#P.....#...........#..........#...............B#",
    "#......#...........#..........#................#",
    "#......#....C......#....L.....#.....######.....#",
    "#..L...#...........#..........#.....#....#.....#",
    "#......######..#####..........#.....#.F..#.....#",
    "#.................................L.#....#.....#",
    "#..........................................A...#",
    "#......#####...######.....#######...#....#.....#",
    "####.###...#...#....#.....#.....#...######.....#",
    "#......#...#...#....#######.....#..............#",
    "#..C...#.F.#...#...........B....#.....=====....#",
    "#......#...#...#................#..............#",
    "#......#...#...#....##########..#####...########",
    "#..B...#.......#....#........#......#..........#",
    "#......#########....#...L....#......#..........#",
    "#...................#........#......#....C.....#",
    "#.......L...........#....F...#......#..........#",
    "#####...######......#........#......#.....L....#",
    "#.......#....#......####..####......#..........#",
    "#.......#....#.................................#",
    "#..====.#....#.....................#######.....#",
    "#.......#.L..#.....######..........#.....#.....#",
    "#.......#....#.....#....#..........#..B..#.....#",
    "#.......##..##.....#....#....C.....#.....#.....#",
    "#..................#....#..........###.###.....#",
    "#####.......L......#.M..#......................#",
    "#...#..............#....#..####..........#######",
    "#...#..######......##..##..#..#..........#.....#",
    "#.B.#..#....#..............#..#....L.....#.....#",
    "#...#..#....#......C.......#..#..........#..E..#",
    "#......#....#..............####..........#.....#",
    "#...........#..........................L.......#",
    "################################################",
]
SOLID = "#C"
GLITCH_COLS = [(40, 120, 255), (255, 40, 60), (20, 60, 255), (255, 20, 40), (120, 200, 255)]


# ---------- Helpers ----------
def clamp(v, a, b):
    return a if v < a else b if v > b else v


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def wrap(a):
    return (a + math.pi) % math.tau - math.pi


def fmt_time(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


_glow_cache = {}


def glow(radius, color):
    key = (radius, color)
    s = _glow_cache.get(key)
    if s is None:
        s = pygame.Surface((radius * 2, radius * 2))
        s.fill((0, 0, 0))
        for r in range(radius, 0, -1):
            t = (1 - r / radius) ** 2
            pygame.draw.circle(s, tuple(int(c * t) for c in color), (radius, radius), r)
        _glow_cache[key] = s
    return s


def blit_glow(surf, pos, radius, color):
    surf.blit(glow(radius, color), (int(pos[0]) - radius, int(pos[1]) - radius), special_flags=pygame.BLEND_ADD)


def text(surf, fnt, s, color, pos, anchor="center", alpha=255, shadow=True):
    img = fnt.render(s, True, color)
    r = img.get_rect(**{anchor: pos})
    if alpha < 255:
        img.set_alpha(alpha)
    if shadow:
        sh = fnt.render(s, True, (0, 0, 0))
        if alpha < 255:
            sh.set_alpha(alpha)
        surf.blit(sh, r.move(2, 2))
    surf.blit(img, r)
    return r


def make_vignette(color, strength, inner=0.3, size=(W, H)):
    sw, sh = 48, 32
    small = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cx, cy = (sw - 1) / 2, (sh - 1) / 2
    for y in range(sh):
        for x in range(sw):
            d = math.hypot((x - cx) / cx, (y - cy) / cy) / math.sqrt(2)
            t = clamp((d - inner) / (1 - inner), 0, 1)
            small.set_at((x, y), (*color, int((t ** 1.5) * strength)))
    return pygame.transform.smoothscale(small, size)


def make_noise(maxv, seed):
    rng = random.Random(seed)
    s = pygame.Surface((W // 4, H // 4))
    for y in range(H // 4):
        for x in range(W // 4):
            v = rng.randint(0, maxv)
            s.set_at((x, y), (v, v, v))
    return pygame.transform.scale(s, (W, H))


def shade(surf, f):
    s = surf.copy()
    v = int(255 * clamp(f, 0, 1))
    s.fill((v, v, v), special_flags=pygame.BLEND_MULT)
    return s


# ---------- Sound (generated in code) ----------
SR = pygame.mixer.get_init()[0] if AUDIO else 22050
CH = pygame.mixer.get_init()[2] if AUDIO else 1


class Silent:
    def play(self, *a, **k):
        return None

    def stop(self):
        pass


def make_sound(fn, dur, vol=1.0):
    if not AUDIO:
        return Silent()
    data = array.array("h")
    for i in range(int(SR * dur)):
        v = int(clamp(fn(i / SR) * vol, -1, 1) * 30000)
        data.append(v)
        if CH == 2:
            data.append(v)
    return pygame.mixer.Sound(buffer=data.tobytes())


def build_sounds():
    rnd = random.Random(9)
    tau = math.tau

    def heart(t):
        v = 0.0
        for t0, a in ((0.0, 1.0), (0.17, 0.7)):
            tt = t - t0
            if tt >= 0:
                v += a * (math.sin(tau * 52 * tt) * math.exp(-tt * 16) + 0.5 * math.sin(tau * 95 * tt) * math.exp(-tt * 28))
        return v

    lp = [0.0]

    def drone(t):
        lp[0] += (rnd.uniform(-1, 1) - lp[0]) * 0.02
        base = 0.22 * math.sin(tau * 45 * t) + 0.18 * math.sin(tau * 47.5 * t) + 0.08 * math.sin(tau * 90.5 * t)
        return base * (0.6 + 0.4 * math.sin(tau * t / 6)) + lp[0] * 1.3

    def clank(t):
        return (rnd.uniform(-1, 1) * math.exp(-t * 70) * 0.5 + math.sin(tau * 1900 * t) * math.exp(-t * 30) * 0.45
                + math.sin(tau * 2750 * t) * math.exp(-t * 45) * 0.3)

    lp2 = [0.0]

    def squelch(t):
        lp2[0] += (rnd.uniform(-1, 1) - lp2[0]) * 0.08
        return math.sin(math.pi * t / 0.45) * (lp2[0] * 2.2 + 0.35 * math.sin(tau * (60 + 25 * math.sin(tau * 7 * t)) * t))

    clicks, tt, gap = [], 0.05, 0.13
    while tt < 1.3:
        clicks.append(tt)
        tt += gap
        gap *= 0.9

    def wind(t):
        v = 0.0
        for c in clicks:
            d = t - c
            if 0 <= d < 0.03:
                v += rnd.uniform(-1, 1) * math.exp(-d * 250) * 0.6 + math.sin(tau * 3100 * d) * math.exp(-d * 200) * 0.5
        return v

    ph = [0.0]

    def screech(t):
        fr = 1700 * math.exp(-t * 1.4) + 180
        ph[0] += fr / SR
        saw = 2 * (ph[0] % 1) - 1
        sq = 1 if (ph[0] * 1.5) % 1 < 0.5 else -1
        return min(1.0, t / 0.02) * math.exp(-t * 1.1) * (0.45 * saw + 0.2 * sq + 0.5 * rnd.uniform(-1, 1))

    def pickup(t):
        return (math.sin(tau * 660 * t) + 0.6 * math.sin(tau * 990 * t) + 0.3 * math.sin(tau * 1320 * t)) * math.exp(-t * 5) * 0.4

    a1, a2 = [0.0], [0.0]

    def whisper(t):
        n = rnd.uniform(-1, 1)
        a1[0] += (n - a1[0]) * 0.5
        a2[0] += (n - a2[0]) * 0.08
        return (a1[0] - a2[0]) * max(0.0, math.sin(tau * 2.6 * t)) ** 2 * math.sin(math.pi * t / 1.6) * 1.6

    def pop(t):
        return rnd.uniform(-1, 1) * math.exp(-t * 18) * 0.8

    ph2 = [0.0]

    def gate(t):
        ph2[0] += (200 + 300 * min(1.0, t / 1.2)) / SR
        return (0.35 * (2 * ((40 * t) % 1) - 1) + 0.35 * math.sin(tau * ph2[0])) * min(1.0, t * 4) * math.exp(-t * 0.8)

    def click(t):
        return rnd.uniform(-1, 1) * math.exp(-t * 220)

    def sting(t):
        env = min(1.0, t / 0.004) * math.exp(-t * 2.6)
        v = sum(2 * ((f * t) % 1) - 1 for f in (880, 932, 1245, 1318, 1661))
        return env * (v * 0.16 + 0.6 * math.sin(tau * 55 * t) * math.exp(-t * 6) + rnd.uniform(-1, 1) * 0.35 * math.exp(-t * 9))

    b1, b2 = [0.0], [0.0]

    def breath(t):
        n = rnd.uniform(-1, 1)
        b1[0] += (n - b1[0]) * 0.35
        b2[0] += (n - b2[0]) * 0.04
        return (b1[0] - b2[0]) * max(0.0, math.sin(tau * 0.85 * t)) ** 1.5 * 2.2

    def bang(t):
        return (0.8 * math.sin(tau * 60 * t) * math.exp(-t * 7) + rnd.uniform(-1, 1) * math.exp(-t * 11) * 0.7
                + 0.35 * math.sin(tau * 420 * t) * math.exp(-t * 3) + 0.2 * math.sin(tau * 613 * t) * math.exp(-t * 3.5))

    lp3 = [0.0]

    def step(t):
        lp3[0] += (rnd.uniform(-1, 1) - lp3[0]) * 0.15
        return lp3[0] * 3 * math.exp(-t * 35) + 0.3 * math.sin(tau * 80 * t) * math.exp(-t * 30)

    def glitch(t):
        seg = int(t * 90)
        r2 = random.Random(seg * 7 + 3)
        f = r2.choice((220, 440, 880, 1320, 1760))
        sq = 1 if (f * t) % 1 < 0.5 else -1
        return (sq * 0.35 + (r2.uniform(-1, 1) if r2.random() < 0.5 else 0) * 0.5) * (1 if r2.random() < 0.7 else 0) * math.exp(-t * 12)

    lp4 = [0.0]

    def drag(t):
        lp4[0] += (rnd.uniform(-1, 1) - lp4[0]) * 0.05
        return lp4[0] * 3.2 * math.sin(math.pi * t / 0.6) + 0.25 * math.sin(tau * 38 * t) * math.sin(math.pi * t / 0.6)

    return {
        "glitch": make_sound(glitch, 0.25), "drag": make_sound(drag, 0.6),
        "heart": make_sound(heart, 0.55), "drone": make_sound(drone, 6.0, 0.8), "clank": make_sound(clank, 0.13),
        "squelch": make_sound(squelch, 0.45), "wind": make_sound(wind, 1.35), "screech": make_sound(screech, 1.4),
        "pickup": make_sound(pickup, 0.6), "whisper": make_sound(whisper, 1.6), "pop": make_sound(pop, 0.3),
        "gate": make_sound(gate, 1.6), "click": make_sound(click, 0.05), "sting": make_sound(sting, 1.3),
        "breath": make_sound(breath, 2.4), "bang": make_sound(bang, 1.4), "step": make_sound(step, 0.15),
    }


# ---------- Textures & sprites (all drawn in code) ----------
def tex_wall(rng, kind):
    s = pygame.Surface((TS, TS))
    s.fill((92, 90, 98))
    for _ in range(900):
        v = rng.randint(-14, 10)
        x, y = rng.randrange(TS), rng.randrange(TS)
        c = s.get_at((x, y))
        s.set_at((x, y), (clamp(c[0] + v, 0, 255), clamp(c[1] + v, 0, 255), clamp(c[2] + v, 0, 255)))
    pygame.draw.line(s, (58, 56, 62), (0, 30), (TS - 1, 30), 2)
    pygame.draw.line(s, (58, 56, 62), (31, 0), (31, 30), 2)
    pygame.draw.line(s, (58, 56, 62), (15, 31), (15, 50), 2)
    pygame.draw.line(s, (58, 56, 62), (47, 31), (47, 50), 2)
    for y in range(50, TS):
        pygame.draw.line(s, mix((70, 68, 72), (28, 26, 28), (y - 50) / 14), (0, y), (TS - 1, y))
    for x in range(-TS, TS, 10):
        pygame.draw.polygon(s, (150, 125, 40), [(x, 52), (x + 5, 52), (x + 9, 57), (x + 4, 57)])
    for _ in range(6):
        x = rng.randrange(TS)
        pygame.draw.line(s, (46, 44, 48), (x, 0), (x, rng.randint(6, 40)), rng.choice((1, 2)))
    for _ in range(3):
        pygame.draw.circle(s, (100, 70, 52), (rng.randrange(TS), rng.randrange(40)), rng.randint(2, 5))
    if kind == "blood":
        pygame.draw.polygon(s, (105, 14, 12), [(10, 18), (42, 12), (54, 26), (30, 34), (14, 30)])
        for _ in range(6):
            x = rng.randint(14, 50)
            pygame.draw.line(s, (90, 10, 10), (x, 24), (x, 24 + rng.randint(6, 26)), 2)
    elif kind == "scratch":
        for k in range(4):
            x0 = 14 + k * 9
            pygame.draw.line(s, (30, 28, 32), (x0 + 1, 9), (x0 + 13, 45), 3)
            pygame.draw.line(s, (150, 146, 150), (x0, 8), (x0 + 12, 44), 1)
    elif kind in ("run", "hears", "back"):
        fnt = mkfont(17)
        words = {"run": ["RUN"], "hears": ["IT", "HEARS"], "back": ["DONT", "LOOK"]}[kind]
        for i, wd in enumerate(words):
            img = fnt.render(wd, True, (130, 16, 14))
            s.blit(img, img.get_rect(center=(TS // 2, 16 + i * 17 + (8 if len(words) == 1 else 0))))
    return s


def tex_crate(rng):
    s = pygame.Surface((TS, TS))
    s.fill((96, 68, 40))
    for k in range(4):
        y = k * 16
        pygame.draw.rect(s, mix((110, 78, 46), (80, 56, 34), rng.random()), (2, y + 1, TS - 4, 14))
        pygame.draw.line(s, (60, 42, 24), (0, y), (TS - 1, y), 2)
    pygame.draw.line(s, (126, 92, 56), (4, 4), (TS - 5, TS - 5), 5)
    pygame.draw.line(s, (126, 92, 56), (TS - 5, 4), (4, TS - 5), 5)
    pygame.draw.rect(s, (58, 40, 24), s.get_rect(), 4)
    for x, y in ((6, 6), (TS - 7, 6), (6, TS - 7), (TS - 7, TS - 7)):
        pygame.draw.circle(s, (160, 160, 165), (x, y), 2)
    return s


def spr_clank(frame):
    w, h = 64, 100
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    e = pygame.Surface((w, h))
    e.fill((0, 0, 0))
    rust, dark, light = (132, 78, 42), (64, 36, 20), (170, 112, 66)
    # legs
    for sd in (-1, 1):
        hip = (32 + sd * 10, 74)
        knee = (32 + sd * 20, 86)
        foot = (32 + sd * 14, 99)
        pygame.draw.lines(s, dark, False, [hip, knee, foot], 6)
        pygame.draw.lines(s, light, False, [hip, knee, foot], 2)
    # wind-up key behind the head
    pygame.draw.line(s, (120, 100, 70), (40, 20), (54, 6), 5)
    for dx, dy in ((-6, -3), (6, 3)):
        pygame.draw.ellipse(s, (170, 140, 90), (50 + dx - 6, 2 + dy - 4, 12, 9))
        pygame.draw.ellipse(s, (90, 70, 45), (50 + dx - 6, 2 + dy - 4, 12, 9), 2)
    # arms (raised claws, twitch between frames)
    up = 0 if frame == 0 else 8
    for sd in (-1, 1):
        sh = (32 + sd * 20, 52)
        el = (32 + sd * 30, 62 - up // 2)
        hand = (32 + sd * 24, 38 + up)
        pygame.draw.lines(s, dark, False, [sh, el, hand], 6)
        pygame.draw.lines(s, light, False, [sh, el, hand], 2)
        for c in (-1, 0, 1):
            pygame.draw.line(s, (220, 210, 190), hand, (hand[0] + c * 4 - sd * 2, hand[1] - 9), 2)
    # barrel body
    body = pygame.Rect(12, 44, 40, 36)
    pygame.draw.ellipse(s, dark, body)
    pygame.draw.ellipse(s, rust, body.inflate(-4, -4))
    pygame.draw.ellipse(s, light, (18, 48, 14, 10))
    for k in range(7):
        pygame.draw.circle(s, (190, 140, 95), (16 + k * 5.3, 62), 1)
    pygame.draw.circle(s, (70, 100, 88), (40, 70), 4)
    pygame.draw.circle(s, (90, 50, 28), (24, 72), 3)
    # head
    pygame.draw.circle(s, dark, (32, 26), 20)
    pygame.draw.circle(s, rust, (32, 26), 18)
    pygame.draw.circle(s, light, (26, 18), 6)
    for sd in (-1, 1):
        ex, ey = 32 + sd * 8, 25
        pygame.draw.circle(s, (12, 6, 3), (ex, ey), 6)
        pygame.draw.circle(s, (255, 140, 40), (ex, ey), 3)
        pygame.draw.polygon(s, dark, [(ex - sd * 10, ey - 9), (ex + sd * 7, ey - 5), (ex + sd * 7, ey - 2), (ex - sd * 10, ey - 6)])
        blit_glow(e, (ex, ey), 10, (230, 110, 20))
        pygame.draw.circle(e, (255, 230, 170), (ex, ey), 2)
    mouth = pygame.Rect(22, 33, 20, 7)
    pygame.draw.rect(s, (10, 2, 2), mouth)
    for k in range(5):
        x = mouth.x + k * 4
        pygame.draw.polygon(s, (215, 205, 185), [(x, mouth.y), (x + 4, mouth.y), (x + 2, mouth.y + 4)])
        pygame.draw.polygon(s, (215, 205, 185), [(x, mouth.bottom), (x + 4, mouth.bottom), (x + 2, mouth.bottom - 3)])
    return s, e


def spr_patch(open_mouth, seed=3):
    rng = random.Random(seed)
    w, h = 128, 116
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    e = pygame.Surface((w, h))
    e.fill((0, 0, 0))
    cx, cy = 64, 62
    outline = []
    for i in range(24):
        a = i / 24 * math.tau
        rr = 1 + 0.08 * math.sin(i * 1.7) + 0.06 * math.sin(i * 2.9)
        outline.append((cx + math.cos(a) * 58 * rr, cy + math.sin(a) * 52 * rr))
    pygame.draw.polygon(s, (56, 46, 54), outline)
    pal = [(150, 125, 60), (60, 105, 105), (105, 64, 105), (120, 110, 100), (135, 66, 58), (80, 90, 60)]
    for _ in range(9):
        px, py = cx + rng.uniform(-38, 38), cy + rng.uniform(-34, 30)
        r = rng.uniform(14, 24)
        pts = [(px + math.cos(k / 5 * math.tau) * r * rng.uniform(0.8, 1.1), py + math.sin(k / 5 * math.tau) * r * rng.uniform(0.7, 1.0))
               for k in range(5)]
        pygame.draw.polygon(s, rng.choice(pal), pts)
        for k in range(5):
            x0, y0 = pts[k]
            x1, y1 = pts[(k + 1) % 5]
            for j in range(3):
                t = (j + 0.5) / 3
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                pygame.draw.line(s, (215, 205, 185), (x - 2, y - 2), (x + 2, y + 2), 1)
    pygame.draw.polygon(s, (30, 24, 30), outline, 3)
    for _ in range(6):
        bx, by, r = cx + rng.uniform(-40, 40), cy + rng.uniform(-38, 4), rng.randint(5, 10)
        col = rng.choice(((30, 28, 30), (210, 200, 180), (140, 30, 30), (50, 70, 110)))
        pygame.draw.circle(s, col, (bx, by), r)
        pygame.draw.circle(s, mix(col, (255, 255, 255), 0.3), (bx, by), r, 1)
        for hx, hy in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            pygame.draw.circle(s, (8, 8, 8), (bx + hx, by + hy), 1)
    for ex, ey, r in ((cx - 18, cy - 18, 10), (cx + 20, cy - 12, 7)):
        pygame.draw.ellipse(s, (225, 218, 196), (ex - r, ey - r * 0.8, r * 2, r * 1.6))
        pygame.draw.line(s, (160, 30, 30), (ex - r + 2, ey), (ex - r // 2, ey - 2), 1)
        pygame.draw.circle(s, (10, 10, 10), (ex, ey), max(2, r // 4))
        blit_glow(e, (ex, ey), r + 6, (70, 90, 60))
        pygame.draw.circle(e, (200, 220, 180), (ex, ey), 1)
    mx, my = cx, cy + 26
    if open_mouth:
        mouth = pygame.Rect(mx - 30, my - 14, 60, 30)
        pygame.draw.ellipse(s, (8, 2, 4), mouth)
        blit_glow(e, mouth.center, 22, (40, 4, 6))
        for k in range(14):
            a = k / 14 * math.tau
            bx, by = mouth.centerx + math.cos(a) * 30, mouth.centery + math.sin(a) * 15
            tx, ty = mouth.centerx + math.cos(a) * 20, mouth.centery + math.sin(a) * 8
            pygame.draw.polygon(s, (200, 202, 210), [(bx - 2, by), (bx + 2, by), (tx, ty)])
    else:
        pygame.draw.line(s, (25, 18, 22), (mx - 28, my), (mx + 28, my), 3)
        for k in range(-3, 4):
            pygame.draw.line(s, (215, 205, 185), (mx + k * 8, my - 4), (mx + k * 8, my + 4), 2)
    for k in range(4):
        fx = cx - 36 + k * 24
        pygame.draw.ellipse(s, (60, 50, 58), (fx - 8, h - 14, 16, 12))
    return s, e


def spr_reaper(frame, jaw_open, seed=1):
    rng = random.Random(seed * 10 + frame * 2 + jaw_open)
    w, h = 76, 124
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    e = pygame.Surface((w, h))
    e.fill((0, 0, 0))
    robe, fold, edge = (14, 12, 15), (32, 30, 36), (44, 42, 50)
    cx = w // 2
    # robe with a ragged hem
    left = [(cx - 20, 34), (cx - 26, 70), (cx - 32, 112)]
    right = [(cx + 32, 112), (cx + 26, 70), (cx + 20, 34)]
    hem = []
    x = cx - 32
    while x < cx + 32:
        hem.append((x, 112 + rng.randint(0, 10)))
        x += rng.randint(4, 8)
        hem.append((x, 108 + rng.randint(-3, 3)))
    pygame.draw.polygon(s, robe, left + hem + right)
    for k in range(5):
        fx = cx - 18 + k * 9 + rng.randint(-2, 2)
        pygame.draw.line(s, fold, (fx, 44), (fx + rng.randint(-5, 5), 108), 2)
    # torn sleeves reaching out
    up = 0 if frame == 0 else 7
    for sd in (-1, 1):
        sh = (cx + sd * 18, 38)
        hand = (cx + sd * 32, 66 - up)
        sleeve = [sh, (cx + sd * 34, 58 - up), (cx + sd * 30, 74 - up), (cx + sd * 14, 60)]
        pygame.draw.polygon(s, robe, sleeve)
        for k in range(5):
            tx = cx + sd * (16 + k * 4)
            ty = 62 - up // 2 + k * 2
            pygame.draw.line(s, robe, (tx, ty), (tx + rng.randint(-2, 2), ty + rng.randint(7, 14)), 2)
        # red skeletal hand with long fingers
        hx, hy = hand
        pygame.draw.ellipse(s, (170, 30, 18), (hx - 5, hy - 4, 10, 9))
        for f in range(4):
            fx0 = hx - 4 + f * 3
            tipx = fx0 + sd * (2 + f) - sd * 2
            tipy = hy - 14 - (2 if f in (1, 2) else 0)
            mid = (fx0 + sd * 2, hy - 8)
            pygame.draw.lines(s, (215, 55, 28), False, [(fx0, hy - 2), mid, (tipx, tipy)], 2)
            pygame.draw.circle(s, (120, 18, 10), mid, 1)
        blit_glow(e, (hx, hy - 6), 12, (150, 20, 8))
        pygame.draw.ellipse(e, (200, 40, 20), (hx - 4, hy - 3, 8, 7))
    # hood
    hood = [(cx, 0), (cx - 13, 6), (cx - 20, 22), (cx - 21, 40), (cx - 10, 46), (cx, 44), (cx + 10, 46), (cx + 21, 40),
            (cx + 20, 22), (cx + 13, 6)]
    pygame.draw.polygon(s, (24, 22, 26), hood)
    pygame.draw.lines(s, edge, False, hood[1:5], 2)
    pygame.draw.ellipse(s, (2, 1, 2), (cx - 13, 8, 26, 34))
    # glowing red skull inside the hood
    sk = (cx, 22)
    pygame.draw.ellipse(s, (175, 34, 18), (sk[0] - 9, sk[1] - 10, 18, 17))
    pygame.draw.ellipse(s, (235, 105, 50), (sk[0] - 6, sk[1] - 9, 8, 6))
    jy = sk[1] + 6 + (4 if jaw_open else 0)
    if jaw_open:
        pygame.draw.rect(s, (8, 0, 0), (sk[0] - 6, sk[1] + 5, 12, 6))
    pygame.draw.rect(s, (160, 28, 14), (sk[0] - 6, jy, 12, 5), border_radius=2)
    for k in range(5):
        pygame.draw.line(s, (240, 150, 110), (sk[0] - 5 + k * 2.5, sk[1] + 5), (sk[0] - 5 + k * 2.5, sk[1] + 7), 1)
        pygame.draw.line(s, (240, 150, 110), (sk[0] - 5 + k * 2.5, jy), (sk[0] - 5 + k * 2.5, jy + 2), 1)
    for sd in (-1, 1):
        pygame.draw.ellipse(s, (6, 0, 0), (sk[0] + sd * 4 - 3, sk[1] - 4, 6, 5))
        pygame.draw.circle(s, (255, 170, 80), (sk[0] + sd * 4, sk[1] - 2), 1)
    pygame.draw.polygon(s, (10, 0, 0), [(sk[0], sk[1] + 1), (sk[0] - 2, sk[1] + 4), (sk[0] + 2, sk[1] + 4)])
    blit_glow(e, sk, 20, (170, 25, 8))
    pygame.draw.ellipse(e, (190, 40, 18), (sk[0] - 8, sk[1] - 9, 16, 15))
    for sd in (-1, 1):
        pygame.draw.ellipse(e, (0, 0, 0), (sk[0] + sd * 4 - 3, sk[1] - 4, 6, 5))
        pygame.draw.circle(e, (255, 190, 110), (sk[0] + sd * 4, sk[1] - 2), 1)
    # baked-in glitch blocks
    for _ in range(5):
        bw = rng.randint(2, 5)
        bx, by = rng.randint(4, w - 10), rng.randint(4, h - 12)
        if s.get_at((bx, by))[3] > 0 or rng.random() < 0.3:
            col = rng.choice(GLITCH_COLS)
            pygame.draw.rect(s, col, (bx, by, bw, bw))
            pygame.draw.rect(e, mix(col, (0, 0, 0), 0.5), (bx, by, bw, bw))
    return s, e


def spr_simple(kind):
    if kind == "fuse":
        s = pygame.Surface((26, 14), pygame.SRCALPHA)
        e = pygame.Surface((26, 14))
        e.fill((0, 0, 0))
        pygame.draw.rect(s, (200, 200, 210), (3, 2, 20, 10), border_radius=3)
        pygame.draw.rect(s, (255, 210, 80), (8, 4, 10, 6))
        pygame.draw.rect(s, (120, 120, 130), (0, 2, 4, 10))
        pygame.draw.rect(s, (120, 120, 130), (22, 2, 4, 10))
        blit_glow(e, (13, 7), 12, (110, 80, 10))
        return s, e
    if kind == "battery":
        s = pygame.Surface((12, 22), pygame.SRCALPHA)
        pygame.draw.rect(s, (40, 120, 60), (0, 3, 12, 19), border_radius=2)
        pygame.draw.rect(s, (200, 200, 205), (3, 0, 6, 4))
        pygame.draw.rect(s, (140, 220, 120), (2, 9, 8, 4))
        e = pygame.Surface((12, 22))
        e.fill((0, 0, 0))
        pygame.draw.rect(e, (20, 60, 20), (2, 9, 8, 4))
        return s, e
    if kind == "lamp":
        s = pygame.Surface((36, 26), pygame.SRCALPHA)
        pygame.draw.line(s, (60, 60, 66), (18, 0), (18, 8), 2)
        pygame.draw.polygon(s, (70, 76, 70), [(4, 20), (32, 20), (24, 8), (12, 8)])
        pygame.draw.ellipse(s, (200, 200, 170), (12, 16, 12, 8))
        e = pygame.Surface((36, 26))
        e.fill((0, 0, 0))
        blit_glow(e, (18, 21), 14, (200, 210, 160))
        return s, e
    if kind == "gate":
        s = pygame.Surface((64, 72), pygame.SRCALPHA)
        pygame.draw.rect(s, (40, 42, 48), (4, 10, 56, 62))
        for k in range(10):
            pygame.draw.line(s, (90, 92, 100), (6, 14 + k * 6), (57, 14 + k * 6), 2)
        for x in range(4, 60, 8):
            pygame.draw.line(s, (230, 190, 40), (x, 10), (x + 4, 10), 4)
        pygame.draw.rect(s, (230, 190, 40), (4, 10, 56, 62), 3)
        img = mkfont(14).render("EXIT", True, (230, 230, 230))
        s.blit(img, img.get_rect(center=(32, 4)))
        return s, None
    if kind == "eyes":
        e = pygame.Surface((40, 14))
        e.fill((0, 0, 0))
        for x in (10, 30):
            blit_glow(e, (x, 7), 7, (190, 20, 15))
            pygame.draw.circle(e, (255, 80, 60), (x, 7), 2)
        return None, e


# ---------- Entities ----------
class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.r = 11
        self.aim = 0.0
        self.stamina = 100.0
        self.exhausted = False
        self.moving = self.sprint = False
        self.walk = 0.0


class Monster:
    def __init__(self, kind, x, y, rng):
        self.kind = kind
        self.x, self.y = x, y
        clank = kind == "clank"
        self.wall_r = 13 if clank else 16
        self.hit_r = 18 if clank else 26
        self.speed_wander = 60 if clank else 45
        self.speed_hunt = 165 if clank else 100
        self.awake = False
        self.state = "dormant"
        self.angle = rng.uniform(0, math.tau)
        self.t = rng.uniform(0, 10)
        self.goal = None
        self.field = None
        self.last_seen = None
        self.lost_t = 0.0
        self.search_t = 0.0
        self.pause = 0.0
        self.dash = 0.0
        self.next_pause = rng.uniform(3, 5)
        self.step_t = 0.0
        self.moving = False
        self.mouth = 0.0
        self.spotted_t = -99.0
        self.visible = False

    def update(self, dt, g):
        self.t += dt
        if not self.awake:
            return
        p = g.player
        d = math.hypot(p.x - self.x, p.y - self.y)
        if g.finale or g.monster_sees(self, d) or (g.noise > 0 and d < g.noise):
            self.state = "hunt"
            self.last_seen = (p.x, p.y)
            self.lost_t = 0.0
        elif self.state == "hunt":
            self.lost_t += dt
            if self.lost_t > 1.5:
                self.state = "investigate"
                self.field = g.bfs(g.cell(*self.last_seen))
        if self.state == "hunt":
            goal, field = (p.x, p.y), g.player_field
            speed = self.speed_hunt * (1.12 if g.finale else 1.0)
        elif self.state == "investigate":
            goal, field = self.last_seen, self.field
            speed = self.speed_hunt * 0.75
            if math.hypot(goal[0] - self.x, goal[1] - self.y) < 30:
                self.state = "search"
                self.search_t = 6.0
                self.goal = None
        if self.state in ("search", "wander", "dormant"):
            if self.state == "search":
                self.search_t -= dt
                if self.search_t <= 0:
                    self.state = "wander"
                    self.goal = None
            if self.goal is None or math.hypot(self.goal[0] - self.x, self.goal[1] - self.y) < 30:
                self.goal = g.random_floor((self.x, self.y) if self.state == "search" else None)
                self.field = g.bfs(g.cell(*self.goal))
            goal, field = self.goal, self.field
            speed = self.speed_wander
        if self.kind == "clank" and self.state == "hunt":
            if self.pause > 0:
                self.pause -= dt
                speed = 0
                if self.pause <= 0:
                    self.dash = 0.75
            else:
                self.next_pause -= dt
                if self.next_pause <= 0:
                    self.pause = 0.45
                    self.next_pause = random.uniform(3, 5.5)
                    g.play("wind", g.vol_at(self, 700) * 0.8)
            if self.dash > 0:
                self.dash -= dt
                speed *= 1.5
            speed *= 0.6 + 0.4 * abs(math.sin(self.t * 9))
        tx, ty = goal
        if not (math.hypot(tx - self.x, ty - self.y) < 260 and g.los(self.x, self.y, tx, ty)):
            nxt = g.next_step(field, self.x, self.y)
            if nxt:
                tx, ty = nxt
        dx, dy = tx - self.x, ty - self.y
        dd = math.hypot(dx, dy)
        self.moving = speed > 0 and dd > 2
        if self.moving:
            step = min(dd, speed * dt)
            self.x += dx / dd * step
            self.y += dy / dd * step
            self.x, self.y = g.push_out(self.x, self.y, self.wall_r)
            self.angle += wrap(math.atan2(dy, dx) - self.angle) * min(1.0, dt * (10 if self.kind == "clank" else 4))
            self.step_t -= dt
            if self.step_t <= 0:
                if self.kind == "clank":
                    self.step_t = 0.22 if self.state == "hunt" else 0.4
                    g.play("glitch", g.vol_at(self, 650) * 0.6)
                else:
                    self.step_t = 0.6
                    g.play("drag", g.vol_at(self, 600) * 0.8)
                    if random.random() < 0.4:
                        g.play("glitch", g.vol_at(self, 600) * 0.5)
        target_m = 1.0 if (self.state == "hunt" and d < 260) else 0.0
        self.mouth += (target_m - self.mouth) * min(1.0, dt * 4)


# ---------- Game ----------
class Game:
    def __init__(self):
        self.parse_map()
        rng = random.Random(77)
        kinds = {"plain": tex_wall(rng, "plain"), "plain2": tex_wall(rng, "plain"), "blood": tex_wall(rng, "blood"),
                 "scratch": tex_wall(rng, "scratch"), "run": tex_wall(rng, "run"), "hears": tex_wall(rng, "hears"),
                 "back": tex_wall(rng, "back"), "crate": tex_crate(rng)}
        self.tex_names = list(kinds)
        self.tex = []        # tex[i][level] -> 64x64 surface
        self.cols = []       # cols[i][level][u] -> 1x64 subsurface
        for name in self.tex_names:
            levels = [shade(kinds[name], (lv / (LEVELS - 1)) ** 1.25) for lv in range(LEVELS)]
            self.tex.append(levels)
            self.cols.append([[lv.subsurface((u, 0, 1, TS)) for u in range(TS)] for lv in levels])
        self.cell_tex = {}
        for r in range(self.rows):
            for c in range(self.cols_n):
                ch = self.grid[r][c]
                if ch == "C":
                    self.cell_tex[(c, r)] = self.tex_names.index("crate")
                elif ch == "#":
                    h = (c * 73856093 ^ r * 19349663) % 41
                    name = {0: "run", 1: "hears", 2: "back", 3: "blood", 4: "blood", 5: "scratch", 6: "scratch", 7: "scratch"}.get(
                        h, "plain" if h % 2 else "plain2")
                    self.cell_tex[(c, r)] = self.tex_names.index(name)
        self.spr = {
            "clank": [spr_reaper(f, j, 1) for j in (0, 1) for f in (0, 1)],
            "patch": [spr_reaper(f, j, 2) for j in (0, 1) for f in (0, 1)],
            "fuse": spr_simple("fuse"), "battery": spr_simple("battery"), "lamp": spr_simple("lamp"),
            "gate": spr_simple("gate"), "eyes": spr_simple("eyes"),
        }
        self.bake_lamp_light()
        self.bgs = [self.bake_bg(f) for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
        self.beam = self.make_beam()
        self.view = pygame.Surface((RW, RH)).convert()
        self.vignette = make_vignette((0, 0, 0), 230)
        self.red_vig = make_vignette((150, 0, 0), 230, 0.35)
        self.grain = [make_noise(11, s) for s in range(3)]
        self.static = [make_noise(48, s + 10) for s in range(3)]
        self.static_hard = [make_noise(70, s + 20) for s in range(2)]
        self.snd = build_sounds()
        self.faces = {"clank": self.face_reaper(1), "patch": self.face_reaper(2)}
        self.white = pygame.Surface((W, H))
        self.white.fill((255, 255, 255))
        self.state = "title"
        self.t = 0.0
        self.deaths = 0
        self.drone_ch = None
        self.zbuf = [1e9] * NR

    # ----- map -----
    def parse_map(self):
        self.grid = MAP
        self.rows, self.cols_n = len(MAP), len(MAP[0])
        self.fuse_spots, self.battery_spots, self.lamps = [], [], []
        for r, line in enumerate(MAP):
            assert len(line) == self.cols_n, (r, len(line))
            for c, ch in enumerate(line):
                cx, cy = c * TILE + TILE / 2, r * TILE + TILE / 2
                if ch == "P":
                    self.start = (cx, cy)
                elif ch == "E":
                    self.gate = (cx, cy)
                elif ch == "F":
                    self.fuse_spots.append((cx, cy))
                elif ch == "B":
                    self.battery_spots.append((cx, cy))
                elif ch == "L":
                    self.lamps.append({"x": cx, "y": cy})
                elif ch == "A":
                    self.spawn_clank = (cx, cy)
                elif ch == "M":
                    self.spawn_patch = (cx, cy)
        reach = self.bfs(self.cell(*self.start))
        self.floor_cells = [(c, r) for r in range(self.rows) for c in range(self.cols_n)
                            if not self.solid(c, r) and reach[r * self.cols_n + c] < 10 ** 6]

    def solid(self, c, r):
        if 0 <= r < self.rows and 0 <= c < self.cols_n:
            return self.grid[r][c] in SOLID
        return True

    def cell(self, x, y):
        return int(x // TILE), int(y // TILE)

    def bfs(self, start):
        n = self.cols_n
        dist = [10 ** 6] * (n * self.rows)
        c0, r0 = start
        if self.solid(c0, r0):
            return dist
        dist[r0 * n + c0] = 0
        q = deque([start])
        while q:
            c, r = q.popleft()
            nd = dist[r * n + c] + 1
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nc, nr = c + dc, r + dr
                if not self.solid(nc, nr) and dist[nr * n + nc] > nd:
                    dist[nr * n + nc] = nd
                    q.append((nc, nr))
        return dist

    def next_step(self, field, x, y):
        if field is None:
            return None
        n = self.cols_n
        c, r = self.cell(x, y)
        if self.solid(c, r):
            return None
        best, bc = field[r * n + c], None
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                nc, nr = c + dc, r + dr
                if self.solid(nc, nr) or (dc and dr and (self.solid(c + dc, r) or self.solid(c, r + dr))):
                    continue
                v = field[nr * n + nc]
                if v < best:
                    best, bc = v, (nc, nr)
        if bc is None:
            return None
        return bc[0] * TILE + TILE / 2, bc[1] * TILE + TILE / 2

    def random_floor(self, near=None):
        if near:
            c0, r0 = self.cell(*near)
            opts = [(c, r) for c, r in self.floor_cells if abs(c - c0) + abs(r - r0) < 7]
        else:
            opts = self.floor_cells
        c, r = random.choice(opts)
        return c * TILE + TILE / 2, r * TILE + TILE / 2

    def push_out(self, x, y, rad):
        for _ in range(2):
            for r in range(int((y - rad) // TILE), int((y + rad) // TILE) + 1):
                for c in range(int((x - rad) // TILE), int((x + rad) // TILE) + 1):
                    if not self.solid(c, r):
                        continue
                    nx = clamp(x, c * TILE, c * TILE + TILE)
                    ny = clamp(y, r * TILE, r * TILE + TILE)
                    dx, dy = x - nx, y - ny
                    d2 = dx * dx + dy * dy
                    if d2 < rad * rad:
                        if d2 == 0:
                            y = r * TILE - rad if y < r * TILE + TILE / 2 else r * TILE + TILE + rad
                            continue
                        d = math.sqrt(d2)
                        x += dx / d * (rad - d)
                        y += dy / d * (rad - d)
        return x, y

    def ray(self, x, y, ang, maxd=2000):
        """DDA ray: returns (dist, hit cell, side, last empty cell, texture u)."""
        dx, dy = math.cos(ang), math.sin(ang)
        c, r = int(x // TILE), int(y // TILE)
        sc = 1 if dx > 0 else -1
        sr = 1 if dy > 0 else -1
        tdx = abs(TILE / dx) if dx else 1e9
        tdy = abs(TILE / dy) if dy else 1e9
        tmx = ((c + 1) * TILE - x) / dx if dx > 0 else (x - c * TILE) / -dx if dx < 0 else 1e9
        tmy = ((r + 1) * TILE - y) / dy if dy > 0 else (y - r * TILE) / -dy if dy < 0 else 1e9
        side = 0
        while True:
            pc, pr = c, r
            if tmx < tmy:
                t = tmx
                tmx += tdx
                c += sc
                side = 0
            else:
                t = tmy
                tmy += tdy
                r += sr
                side = 1
            if t >= maxd:
                return maxd, None, side, (pc, pr), 0.0
            if self.solid(c, r):
                if side == 0:
                    u = ((y + dy * t) % TILE) / TILE
                    if dx < 0:
                        u = 1 - u
                else:
                    u = ((x + dx * t) % TILE) / TILE
                    if dy > 0:
                        u = 1 - u
                return t, (c, r), side, (pc, pr), u

    def cast(self, x, y, ang, maxd):
        return self.ray(x, y, ang, maxd)[0]

    def los(self, x0, y0, x1, y1):
        d = math.hypot(x1 - x0, y1 - y0)
        if d < 1:
            return True
        return self.cast(x0, y0, math.atan2(y1 - y0, x1 - x0), d) >= d - 1

    # ----- lighting -----
    def bake_lamp_light(self):
        """For every floor cell: which lamps reach it (with line of sight) and how strongly."""
        n = self.cols_n
        self.cell_lamps = [[] for _ in range(n * self.rows)]
        for i, lamp in enumerate(self.lamps):
            lc, lr = self.cell(lamp["x"], lamp["y"])
            for r in range(lr - 6, lr + 7):
                for c in range(lc - 6, lc + 7):
                    if self.solid(c, r):
                        continue
                    cx, cy = c * TILE + TILE / 2, r * TILE + TILE / 2
                    d = math.hypot(cx - lamp["x"], cy - lamp["y"])
                    if d < 230 and self.los(lamp["x"], lamp["y"], cx, cy):
                        self.cell_lamps[r * n + c].append((i, (1 - d / 230) ** 1.4 * 0.95))
            lamp["mode"] = ("steady", "flicker", "broken", "flicker")[i % 4]
            lamp["orig_mode"] = lamp["mode"]
            lamp["k"] = 1.0
            lamp["timer"] = 0.0
            lamp["on"] = True

    def light_at(self, d, off, cell):
        b = 0.05 + 0.5 * max(0.0, 1 - d / 120)
        if self.flash_eff > 0:
            cone = clamp((0.6 - abs(off)) / 0.22, 0, 1)
            b += 1.3 * self.flash_eff * max(0.0, 1 - d / self.fl_range) ** 1.1 * cone
        if cell is not None and self.blackout_t <= 0:
            c, r = cell
            if 0 <= c < self.cols_n and 0 <= r < self.rows:
                for i, v in self.cell_lamps[r * self.cols_n + c]:
                    b += self.lamps[i]["k"] * v
        return b

    def bake_bg(self, fl):
        """Ceiling + floor gradient, lit by a flashlight of strength fl (0..1)."""
        s = pygame.Surface((RW, RH + 16)).convert()
        h2 = RH // 2 + 8
        self.flash_eff, self.fl_range, self.blackout_t = fl, FL_RANGE, 0
        for y in range(RH + 16):
            if y < h2:
                d = (0.5 * TILE * PROJ) / (h2 - y + 0.5)
                base, k = (46, 46, 52), 0.55
            else:
                d = (0.5 * TILE * PROJ) / (y - h2 + 0.5)
                base, k = (84, 78, 70), 1.0
            for x in range(0, RW, 4):
                off = math.atan((x + 2 - RW / 2) / PROJ)
                b = clamp(self.light_at(d, off, None) * k, 0, 1)
                s.fill(mix((0, 0, 0), base, b ** 1.25), (x, y, 4, 1))
        return s

    def make_beam(self):
        s = pygame.Surface((RW, RH)).convert()
        cx, cy = RW / 2, RH / 2 + 6
        for y in range(0, RH, 2):
            for x in range(0, RW, 2):
                r = math.hypot((x - cx) / (RW * 0.42), (y - cy) / (RH * 0.62))
                v = int(255 * (0.5 + 0.5 * clamp(1.15 - r, 0, 1) ** 0.9))
                s.fill((v, v, v), (x, y, 2, 2))
        return pygame.transform.smoothscale(s, (RW, RH))

    # ----- game flow -----
    def reset(self):
        rng = random.Random()
        self.player = Player(*self.start)
        self.monsters = [Monster("clank", *self.spawn_clank, rng), Monster("patch", *self.spawn_patch, rng)]
        self.clank, self.patch = self.monsters
        self.fuses = [{"x": x, "y": y, "taken": False} for x, y in self.fuse_spots]
        self.batteries = [{"x": x, "y": y, "taken": False} for x, y in self.battery_spots]
        self.fuse_count = 0
        self.battery = 100.0
        self.light_on = True
        self.light_k = 1.0
        self.fl_range = FL_RANGE
        self.flash_eff = 1.0
        self.noise = 0
        self.finale = False
        self.play_t = 0.0
        self.player_field = self.bfs(self.cell(*self.start))
        self.field_t = 0.0
        self.msgs = []
        self.ghosts = []
        self.fake_eyes = None
        self.event_t = random.uniform(14, 20)
        self.blackout_t = 0.0
        self.flash_t = 0.0
        self.flash_face = None
        self.punch = 0.0
        self.hb_t = 0.0
        self.pulse = 0.0
        self.fear = 0.0
        self.shake = 0.0
        self.step_phase = 0
        for lamp in self.lamps:
            lamp["mode"] = lamp["orig_mode"]
            lamp["k"] = 1.0
        self.say("Night shift. The power is out.", (220, 210, 190), 4)
        self.say("Find 3 fuses for the exit gate.", (255, 210, 90), 5)
        self.say("Your light gives you away.  [F] = light off", (170, 175, 190), 6)
        self.state = "play"
        self.grab(True)
        if AUDIO:
            if self.drone_ch:
                self.drone_ch.stop()
            self.drone_ch = self.snd["drone"].play(-1)
            if self.drone_ch:
                self.drone_ch.set_volume(0.35)

    def grab(self, on):
        try:
            pygame.event.set_grab(on)
            pygame.mouse.set_visible(not on)
            pygame.mouse.get_rel()
        except pygame.error:
            pass

    def say(self, msg, color=(230, 225, 215), secs=3.0):
        self.msgs.append([msg, secs, color])
        self.msgs = self.msgs[-3:]

    def play(self, name, vol=1.0):
        if vol <= 0.01:
            return
        ch = self.snd[name].play()
        if ch:
            ch.set_volume(clamp(vol, 0, 1))

    def vol_at(self, obj, maxd):
        return clamp(1 - math.hypot(obj.x - self.player.x, obj.y - self.player.y) / maxd, 0, 1) ** 1.3

    def monster_sees(self, m, d):
        p = self.player
        if d < 70:
            return True
        if d > 620 or not self.los(m.x, m.y, p.x, p.y):
            return False
        if self.light_on and d < 560:
            return True
        return d < (230 if m.kind == "clank" else 190)

    # ----- update -----
    def update(self, dt, keys):
        self.t += dt
        if self.state == "play":
            self.update_play(dt, keys)
        elif self.state == "scare":
            self.scare_t += dt
            if self.scare_t > 0.95 and not self.lunged:
                self.lunged = True
                self.play("bang", 1.0)
                self.play("sting", 1.0)
            if self.scare_t > 2.3:
                self.state = "dead"

    def update_play(self, dt, keys):
        self.play_t += dt
        p = self.player

        # turning: mouse + arrow keys
        rel = pygame.mouse.get_rel()[0] if pygame.mouse.get_focused() else 0
        p.aim += rel * MOUSE_SENS
        p.aim += ((keys[pygame.K_RIGHT]) - (keys[pygame.K_LEFT])) * TURN_SPEED * dt
        p.aim %= math.tau
        fwd = (keys[pygame.K_w] or keys[pygame.K_UP]) - (keys[pygame.K_s] or keys[pygame.K_DOWN])
        strafe = keys[pygame.K_d] - keys[pygame.K_a]
        fx, fy = math.cos(p.aim), math.sin(p.aim)
        mx, my = fx * fwd - fy * strafe, fy * fwd + fx * strafe
        moving = bool(fwd or strafe)
        if moving:
            ln = math.hypot(mx, my)
            mx, my = mx / ln, my / ln
        if p.stamina <= 0:
            p.exhausted = True
        if p.exhausted and p.stamina > 30:
            p.exhausted = False
        sprint = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and moving and fwd > 0 and not p.exhausted
        p.stamina = max(0.0, p.stamina - 34 * dt) if sprint else min(100.0, p.stamina + (24 if not moving else 14) * dt)
        spd = SPRINT if sprint else WALK
        p.x, p.y = self.push_out(p.x + mx * spd * dt, p.y + my * spd * dt, p.r)
        p.moving, p.sprint = moving, sprint
        if moving:
            p.walk += dt * (13 if sprint else 9)
            ph = int(p.walk / math.pi)
            if ph != self.step_phase:
                self.step_phase = ph
                self.play("step", 0.35 if sprint else 0.18)
        self.noise = 380 if sprint else (120 if moving else 0)

        # flashlight
        pd = math.hypot(self.patch.x - p.x, self.patch.y - p.y) if self.patch.awake else 9999
        near_patch = clamp(1 - pd / 300, 0, 1)
        if self.light_on:
            self.battery -= dt * (BATTERY_DRAIN + 2.5 * near_patch)
            if self.battery <= 0:
                self.battery = 0
                self.light_on = False
                self.say("The battery died...", (255, 90, 80))
        k = 1.0
        if self.battery < 20 and random.random() < 0.1:
            k = random.uniform(0.05, 0.5)
        if near_patch > 0 and random.random() < 0.45 * near_patch:
            k = random.uniform(0.0, 0.3)
        self.light_k = k
        self.fl_range = FL_RANGE * (0.55 + 0.45 * self.battery / 100)
        on = self.light_on and self.blackout_t <= 0
        self.flash_eff = (self.light_k * (0.6 + 0.4 * self.battery / 100)) if on else 0.0

        def spotted_me(m):
            return math.hypot(m.x - p.x, m.y - p.y) < 380 and self.los(p.x, p.y, m.x, m.y)

        if not self.clank.awake and (self.play_t > 7 or spotted_me(self.clank)):
            self.clank.awake = True
            self.clank.state = "wander"
            self.say("Something in the dark just... glitched.", (255, 90, 80), 4)
            self.play("glitch", 0.9)
        if not self.patch.awake and (self.fuse_count >= 1 or self.play_t > 14 or spotted_me(self.patch)):
            self.patch.awake = True
            self.patch.state = "wander"
            self.say("A second shadow is moving. A bigger one.", (130, 160, 255), 4)
            self.play("drag", 1.0)

        self.field_t -= dt
        if self.field_t <= 0:
            self.player_field = self.bfs(self.cell(p.x, p.y))
            self.field_t = 0.25
        for m in self.monsters:
            m.update(dt, self)

        for f in self.fuses:
            if not f["taken"] and math.hypot(f["x"] - p.x, f["y"] - p.y) < 26:
                f["taken"] = True
                self.fuse_count += 1
                self.play("pickup", 0.8)
                if self.fuse_count < 3:
                    self.say(f"Fuse {self.fuse_count}/3", (255, 210, 90))
                else:
                    self.finale = True
                    for m in self.monsters:
                        m.awake = True
                        m.state = "hunt"
                    self.play("gate", 1.0)
                    self.say("The gate has power. THEY KNOW WHERE YOU ARE.", (255, 70, 60), 5)
                    self.say("RUN TO THE EXIT!", (255, 220, 120), 5)
        for b in self.batteries:
            if not b["taken"] and math.hypot(b["x"] - p.x, b["y"] - p.y) < 26 and self.battery < 99:
                b["taken"] = True
                self.battery = min(100.0, self.battery + 40)
                self.play("pickup", 0.5)
                self.say("+ Battery", (150, 230, 150), 2)

        gd = math.hypot(self.gate[0] - p.x, self.gate[1] - p.y)
        if self.finale and gd < 30:
            self.state = "win"
            self.win_time = self.play_t
            self.grab(False)
            if self.drone_ch:
                self.drone_ch.stop()
            return
        if not self.finale and gd < 34 and (not self.msgs or self.msgs[-1][0] != "The gate is locked. No power."):
            self.say("The gate is locked. No power.", (200, 120, 110), 2)

        # the moment your light lands on a monster -> sting
        for m in self.monsters:
            if not m.awake:
                continue
            vis = self.lit_visible(m)
            if vis and not m.visible and self.play_t - m.spotted_t > 7:
                self.play("sting", 0.95)
                self.punch = 1.0
                self.shake = max(self.shake, 0.35)
            if vis:
                m.spotted_t = self.play_t
            m.visible = vis
        self.punch = max(0.0, self.punch - dt * 2.5)
        self.flash_t = max(0.0, self.flash_t - dt)
        if self.blackout_t > 0:
            self.blackout_t -= dt
            if self.blackout_t <= 0:
                self.end_blackout()

        for m in self.monsters:
            if m.awake and math.hypot(m.x - p.x, m.y - p.y) < m.hit_r + p.r - 3:
                self.start_scare(m)
                return

        dmin = min((math.hypot(m.x - p.x, m.y - p.y) for m in self.monsters if m.awake), default=9999)
        hunting = any(m.state == "hunt" for m in self.monsters if m.awake)
        self.fear = clamp(1 - (dmin - 60) / 480, 0, 1) * (1.0 if hunting else 0.6)
        if self.fear > 0.08:
            self.hb_t -= dt
            if self.hb_t <= 0:
                self.hb_t = 1.25 - 0.8 * self.fear
                self.play("heart", 0.25 + 0.75 * self.fear)
                self.pulse = 1.0
        self.pulse = max(0.0, self.pulse - dt * 3)
        self.shake = max(0.0, self.shake - dt * (0.5 if self.shake > 0.1 else 1))
        if self.fear > 0.75:
            self.shake = max(self.shake, 0.05)
        if self.drone_ch:
            self.drone_ch.set_volume(0.3 + 0.4 * self.fear)

        self.update_lamps(dt)
        self.update_events(dt)
        for m in self.msgs:
            m[1] -= dt
        self.msgs = [m for m in self.msgs if m[1] > 0]
        for gh in self.ghosts:
            gh[3] -= dt
        self.ghosts = [gh for gh in self.ghosts if gh[3] > 0]
        if self.fake_eyes:
            self.fake_eyes[2] -= dt
            if self.fake_eyes[2] <= 0:
                self.fake_eyes = None

    def update_lamps(self, dt):
        for lamp in self.lamps:
            mode = lamp["mode"]
            if mode == "steady":
                lamp["k"] = 0.35 if random.random() < 0.006 else 1.0
            elif mode == "flicker":
                lamp["timer"] -= dt
                if lamp["timer"] <= 0:
                    lamp["on"] = not lamp["on"]
                    lamp["timer"] = random.uniform(0.03, 0.3) if lamp["on"] else random.uniform(0.02, 0.9)
                lamp["k"] = 1.0 if lamp["on"] else 0.0
            else:
                if lamp["k"] > 0:
                    lamp["k"] = max(0.0, lamp["k"] - dt * 6)
                elif random.random() < 0.0015:
                    lamp["k"] = 0.9

    def update_events(self, dt):
        self.event_t -= dt
        if self.event_t > 0:
            return
        self.event_t = random.uniform(12, 22)
        p = self.player
        options = ["whisper", "pop", "eyes", "bang"]
        if self.play_t > 20:
            options += ["flash", "flash"]
        if any(m.awake for m in self.monsters) and not self.finale:
            options += ["blackout", "blackout"]
        kind = random.choice(options)
        if kind == "flash":
            self.flash_t = 0.16
            self.flash_face = random.choice(list(self.faces.values()))
            self.play("sting", 0.85)
        elif kind == "blackout":
            self.blackout_t = 2.6
            self.play("pop", 0.7)
            self.play("breath", 0.9)
            self.say("...", (150, 30, 30), 2)
        elif kind == "bang":
            self.play("bang", 0.9)
            self.shake = 0.5
            for lamp in self.lamps:
                if math.hypot(lamp["x"] - p.x, lamp["y"] - p.y) < 500:
                    lamp["k"] = 0.0
                    lamp["on"] = False
                    lamp["timer"] = 1.2
        elif kind == "pop":
            near = [l for l in self.lamps if l["mode"] != "broken" and math.hypot(l["x"] - p.x, l["y"] - p.y) < 500]
            if near:
                lamp = random.choice(near)
                lamp["mode"] = "broken"
                lamp["k"] = 0.0
                self.play("pop", clamp(1 - math.hypot(lamp["x"] - p.x, lamp["y"] - p.y) / 700, 0.2, 1))
            else:
                kind = "whisper"
        if kind == "whisper":
            self.play("whisper", 0.55)
            msg = random.choice(("behind you", "it sees you", "don't stop", "so close now", "turn around"))
            self.ghosts.append([msg, random.randint(160, W - 160), random.randint(160, H - 200), 2.6])
        elif kind == "eyes":
            for _ in range(40):
                x, y = self.random_floor()
                d = math.hypot(x - p.x, y - p.y)
                ang = abs(wrap(math.atan2(y - p.y, x - p.x) - p.aim))
                if 220 < d < 480 and 0.15 < ang < 0.5 and self.los(p.x, p.y, x, y):
                    self.fake_eyes = [x, y, 1.6]
                    break

    def lit_visible(self, m):
        p = self.player
        if self.flash_eff < 0.3:
            return False
        d = math.hypot(m.x - p.x, m.y - p.y)
        if d > self.fl_range or d < 40:
            return False
        if abs(wrap(math.atan2(m.y - p.y, m.x - p.x) - p.aim)) > 0.45:
            return False
        return self.los(p.x, p.y, m.x, m.y)

    def end_blackout(self):
        """Lights come back... and something is standing right in front of you."""
        p = self.player
        awake = [m for m in self.monsters if m.awake]
        if not awake:
            return
        m = min(awake, key=lambda mm: math.hypot(mm.x - p.x, mm.y - p.y))
        for d in (150, 125, 175, 105, 200):
            for da in (0, 0.15, -0.15, 0.3, -0.3):
                a = p.aim + da
                x, y = p.x + math.cos(a) * d, p.y + math.sin(a) * d
                if not self.solid(*self.cell(x, y)) and self.los(p.x, p.y, x, y):
                    m.x, m.y = self.push_out(x, y, m.wall_r)
                    m.angle = math.atan2(p.y - m.y, p.x - m.x)
                    m.state = "hunt"
                    m.last_seen = (p.x, p.y)
                    m.pause = 0.7
                    m.mouth = 1.0
                    m.spotted_t = self.play_t
                    m.visible = True
                    self.play("sting", 1.0)
                    self.punch = 1.0
                    self.shake = 0.4
                    return

    def start_scare(self, m):
        self.state = "scare"
        self.scare_t = 0.0
        self.scare_by = m.kind
        self.deaths += 1
        self.scare_face = self.faces[m.kind]
        self.lunged = False
        self.grab(False)
        if self.drone_ch:
            self.drone_ch.stop()
        self.play("screech", 1.0)

    # ----- 3D rendering -----
    def render_view(self, bob):
        V = self.view
        p = self.player
        lvl = int(round(clamp(self.flash_eff, 0, 1) * 4))
        V.blit(self.bgs[lvl], (0, -8 + int(bob)))
        zbuf = self.zbuf
        cols = self.cols
        tex = self.tex
        cell_tex = self.cell_tex
        aim = p.aim
        h2 = H2 + bob
        for i in range(NR):
            x = i * SW
            off = math.atan((x + SW / 2 - RW / 2) / PROJ)
            dist, hit, side, last, u = self.ray(p.x, p.y, aim + off)
            perp = max(1.0, dist * math.cos(off))
            zbuf[i] = perp
            if hit is None:
                continue
            b = self.light_at(dist, off, last)
            if side == 1:
                b *= 0.78
            lv = int(clamp(b, 0, 1) * (LEVELS - 1) + 0.5)
            if lv == 0:
                continue
            t = cell_tex[hit]
            tu = min(TS - 1, int(u * TS))
            lh = TILE * PROJ / perp
            if lh <= RH * 1.4:
                img = pygame.transform.scale(cols[t][lv][tu], (SW, int(lh) + 1))
                V.blit(img, (x, int(h2 - lh / 2)))
            else:
                f = RH * 1.4 / lh
                th = max(1, int(TS * f))
                ty0 = (TS - th) // 2
                img = pygame.transform.scale(tex[t][lv].subsurface((tu, ty0, 1, th)), (SW, int(RH * 1.4)))
                V.blit(img, (x, int(h2 - RH * 0.7)))

        # sprites, far to near
        sprites = []
        t = self.t
        for lamp in self.lamps:
            sprites.append((lamp["x"], lamp["y"], self.spr["lamp"], 0.32, "ceil", lamp))
        for f in self.fuses:
            if not f["taken"]:
                sprites.append((f["x"], f["y"], self.spr["fuse"], 0.16, "floor", None))
        for bt in self.batteries:
            if not bt["taken"]:
                sprites.append((bt["x"], bt["y"], self.spr["battery"], 0.2, "floor", None))
        gate_spr = self.spr["gate"]
        sprites.append((self.gate[0], self.gate[1], gate_spr, 0.9, "floor", "gate"))
        for m in self.monsters:
            frame = int(m.t * (9 if m.kind == "clank" else 4)) % 2 if m.moving else 0
            spr = self.spr[m.kind][frame + (2 if m.mouth > 0.5 else 0)]
            sprites.append((m.x, m.y, spr, 0.86 if m.kind == "clank" else 1.08, "floor", m))
        if self.fake_eyes and (self.fake_eyes[2] > 0.25 or int(t * 20) % 2):
            sprites.append((self.fake_eyes[0], self.fake_eyes[1], self.spr["eyes"], 0.08, "eye", None))
        sprites.sort(key=lambda s: -((s[0] - p.x) ** 2 + (s[1] - p.y) ** 2))
        emissive = []
        self.glitch_px = []
        for sx, sy, (img, emis), hw, anchor, ref in sprites:
            self.draw_sprite(V, img, emis, sx, sy, hw, anchor, ref, h2, emissive)

        if self.flash_eff > 0.2:
            V.blit(self.beam, (0, 0), special_flags=pygame.BLEND_MULT)
        for rect, col in self.glitch_px:
            V.fill(col, rect)
        for e_img, ex, ey, runs in emissive:
            for rx0, rx1 in runs:
                V.blit(e_img, (rx0, ey), (rx0 - ex, 0, rx1 - rx0, e_img.get_height()), special_flags=pygame.BLEND_ADD)

    def draw_sprite(self, V, img, emis, wx, wy, hw, anchor, ref, h2, emissive):
        p = self.player
        dx, dy = wx - p.x, wy - p.y
        dist = math.hypot(dx, dy)
        ang = wrap(math.atan2(dy, dx) - p.aim)
        if abs(ang) > FOV / 2 + 0.5:
            return
        depth = dist * math.cos(ang)
        if depth < 10:
            return
        base = img if img is not None else emis
        bw, bh = base.get_size()
        hpx = min(RH * 3.0, hw * TILE * PROJ / depth)
        wpx = hpx * bw / bh
        if isinstance(ref, Monster) and ref.kind == "patch":
            wpx *= 1 + 0.05 * math.sin(ref.t * 4)
        sxc = RW / 2 + math.tan(ang) * PROJ
        x0 = int(sxc - wpx / 2)
        x1 = int(sxc + wpx / 2)
        if x1 < 0 or x0 >= RW or wpx < 1:
            return
        floor_y = h2 + (0.5 * TILE * PROJ) / depth
        ceil_y = h2 - (0.5 * TILE * PROJ) / depth
        if anchor == "floor":
            top = floor_y - hpx
        elif anchor == "ceil":
            top = ceil_y
        else:
            top = h2 - (0.18 * TILE * PROJ) / depth
        # visible column runs (z-buffer test)
        runs = []
        start = None
        for i in range(max(0, x0 // SW), min(NR - 1, x1 // SW) + 1):
            vis = self.zbuf[i] > depth
            if vis and start is None:
                start = i
            elif not vis and start is not None:
                runs.append((max(x0, start * SW), i * SW))
                start = None
        if start is not None:
            runs.append((max(x0, start * SW), min(x1, (min(NR - 1, x1 // SW) + 1) * SW)))
        runs = [(a, b) for a, b in runs if b > a]
        if not runs:
            return
        size = (max(1, x1 - x0), max(1, int(hpx)))
        if img is not None:
            cell = self.cell(wx, wy)
            b = self.light_at(dist, ang, cell)
            if ref == "gate" and self.finale:
                b += 0.5
            b = clamp(b, 0, 1)
            monster = isinstance(ref, Monster)
            if monster:
                b = max(b, 0.18)          # the dark robe is always faintly visible against the dark
            if b > 0.02:
                scaled = pygame.transform.scale(img, size)
                if b < 0.99:
                    v = int(255 * b ** 1.2)
                    scaled.fill((v, v, v, 255), special_flags=pygame.BLEND_RGBA_MULT)
                if monster and random.random() < 0.35:
                    # glitch: tear horizontal slices sideways
                    for _ in range(random.randint(1, 3)):
                        sh = random.randint(2, max(3, size[1] // 6))
                        sy = random.randint(0, max(0, size[1] - sh))
                        strip = scaled.subsurface((0, sy, size[0], sh)).copy()
                        scaled.fill((0, 0, 0, 0), (0, sy, size[0], sh))
                        scaled.blit(strip, (random.randint(-size[0] // 5, size[0] // 5), sy))
                if monster and random.random() < 0.25:
                    # glitch: red / blue colour split
                    for col, dxo in (((255, 30, 40, 255), -max(2, size[0] // 18)), ((30, 90, 255, 255), max(2, size[0] // 18))):
                        ghost = scaled.copy()
                        ghost.fill(col, special_flags=pygame.BLEND_RGBA_MULT)
                        for a, bb in runs:
                            V.blit(ghost, (a + dxo, int(top)), (a - x0, 0, bb - a, size[1]), special_flags=pygame.BLEND_ADD)
                for a, bb in runs:
                    V.blit(scaled, (a, int(top)), (a - x0, 0, bb - a, size[1]))
            if monster:
                # glitch: blue and red squares flickering on and around the body
                n = 1 + int(size[0] / 25) + (2 if ref.state == "hunt" else 0)
                for _ in range(n):
                    q = max(1, int(random.uniform(0.03, 0.08) * size[0]))
                    qx = int(x0 + random.uniform(-0.1, 1.1) * size[0])
                    qy = int(top + random.uniform(-0.15, 1.05) * size[1])
                    ci = qx // SW
                    if 0 <= ci < NR and self.zbuf[ci] > depth:
                        self.glitch_px.append(((qx, qy, q, q), random.choice(GLITCH_COLS)))
        e = emis
        if ref == "gate":
            col = (60, 255, 110) if self.finale else ((255, 40, 30) if int(self.t * 2) % 2 else (90, 10, 8))
            e = pygame.Surface((bw, bh))
            e.fill((0, 0, 0))
            blit_glow(e, (bw // 2, 10), 9, col)
        if isinstance(ref, dict):          # ceiling lamp: glow only while on
            if ref["k"] < 0.1 or self.blackout_t > 0:
                e = None
        if e is not None:
            if isinstance(ref, Monster) and not self.los(p.x, p.y, ref.x, ref.y):
                return
            emissive.append((pygame.transform.scale(e, size), x0, int(top), runs))

    def draw_play(self, surf):
        p = self.player
        bob = math.sin(p.walk * 2) * (2.2 if p.sprint else 1.3) if p.moving else 0
        if self.shake > 0:
            bob += random.uniform(-2, 2)
        self.render_view(bob)
        sx = random.randint(-6, 6) if self.shake > 0 else 0
        surf.blit(pygame.transform.scale(self.view, (W, H)), (sx, 0))

        if self.fear > 0.05:
            rv = self.red_vig
            rv.set_alpha(int(200 * clamp(self.fear * (0.4 + 0.6 * self.pulse), 0, 1)))
            surf.blit(rv, (0, 0))
        if self.fear > 0.55 and random.random() < (self.fear - 0.5) * 0.6:
            surf.blit(random.choice(self.static), (random.randint(-20, 0), random.randint(-20, 0)), special_flags=pygame.BLEND_ADD)
        if self.fear > 0.3:
            for _ in range(int((self.fear - 0.3) * 6) if random.random() < 0.5 else 0):
                q = random.randint(6, 26)
                surf.fill(random.choice(GLITCH_COLS), (random.randint(0, W), random.randint(0, H), q, q))
            if random.random() < self.fear * 0.3:
                self.tear(surf, 3, int(20 * self.fear))
        surf.blit(self.vignette, (0, 0))
        surf.blit(random.choice(self.grain), (0, 0), special_flags=pygame.BLEND_ADD)
        for msg, x, y, life in self.ghosts:
            text(surf, F_MED, msg, (150, 20, 20), (x + random.randint(-1, 1), y), alpha=int(160 * min(1, life)), shadow=False)
        if self.punch > 0.05:
            z = 1 + 0.08 * self.punch
            big = pygame.transform.scale(surf, (int(W * z), int(H * z)))
            surf.blit(big, (-(big.get_width() - W) // 2, -(big.get_height() - H) // 2))
            surf.fill((int(70 * self.punch), 0, 0), special_flags=pygame.BLEND_ADD)
        if self.flash_t > 0:
            img = pygame.transform.scale(self.flash_face, (int(W * 1.15), int(H * 1.15)))
            surf.blit(img, (-W * 0.075 + random.randint(-15, 15), -H * 0.075 + random.randint(-15, 15)))
            surf.blit(random.choice(self.static_hard), (0, 0), special_flags=pygame.BLEND_ADD)
            self.tear(surf)
            return
        self.draw_hud(surf)

    def draw_hud(self, surf):
        text(surf, F_SM, "FUSES", (200, 195, 185), (20, 18), "topleft")
        for i in range(3):
            r = pygame.Rect(96 + i * 30, 16, 22, 22)
            pygame.draw.rect(surf, (255, 210, 80) if i < self.fuse_count else (50, 48, 46), r, border_radius=4)
            pygame.draw.rect(surf, (120, 110, 90), r, 1, border_radius=4)
        goal = "RUN TO THE EXIT!" if self.finale else "Find the fuses"
        text(surf, F_XS, goal, (255, 120, 90) if self.finale else (170, 165, 155), (20, 46), "topleft")
        bx, by = 20, H - 58
        pygame.draw.rect(surf, (200, 200, 205), (bx, by, 84, 30), 2, border_radius=4)
        pygame.draw.rect(surf, (200, 200, 205), (bx + 84, by + 9, 5, 12))
        lvl = self.battery / 100
        col = (110, 220, 110) if lvl > 0.5 else (240, 200, 70) if lvl > 0.2 else (240, 70, 60)
        if lvl > 0.2 or int(self.t * 3) % 2:
            pygame.draw.rect(surf, col, (bx + 4, by + 4, int(76 * lvl), 22), border_radius=2)
        text(surf, F_SM, f"{int(self.battery)}%", (230, 230, 230), (bx + 100, by + 15), "midleft")
        text(surf, F_XS, "LIGHT ON" if self.light_on else "LIGHT OFF  [F]",
             (230, 220, 160) if self.light_on else (150, 150, 160), (bx, by - 18), "topleft")
        pygame.draw.rect(surf, (40, 40, 46), (bx, by + 36, 140, 6), border_radius=3)
        pygame.draw.rect(surf, (230, 120, 60) if self.player.exhausted else (150, 190, 230),
                         (bx, by + 36, int(140 * self.player.stamina / 100), 6), border_radius=3)
        hx, hy = W - 50, H - 46
        sc = 1 + 0.35 * self.pulse
        hc = mix((90, 30, 30), (240, 30, 40), self.fear)
        for s in (-1, 1):
            pygame.draw.circle(surf, hc, (hx + s * 8 * sc, hy - 5 * sc), int(9 * sc))
        pygame.draw.polygon(surf, hc, [(hx - 17 * sc, hy - 2 * sc), (hx + 17 * sc, hy - 2 * sc), (hx, hy + 18 * sc)])
        y = 22
        for msg, life, color in self.msgs:
            text(surf, F_MED, msg, color, (W // 2, y), "midtop", alpha=int(255 * min(1, life)))
            y += 32

    # ----- jumpscare art -----
    def face_reaper(self, seed):
        rng = random.Random(seed)
        s = pygame.Surface((W, H))
        s.fill((0, 0, 0))
        cx, cy = W // 2, H // 2 + 20
        # ragged hood filling the screen
        hood = []
        for k in range(40):
            a = math.pi + k / 39 * math.pi
            r = 470 + rng.randint(-25, 25)
            hood.append((cx + math.cos(a) * r * 1.05, cy + 60 + math.sin(a) * r * 1.05))
        hood += [(cx + 520, H + 40), (cx - 520, H + 40)]
        pygame.draw.polygon(s, (26, 24, 30), hood)
        for k in range(14):
            x = cx - 460 + k * 70 + rng.randint(-20, 20)
            pygame.draw.line(s, (40, 38, 46), (x, 120 + rng.randint(0, 80)), (x + rng.randint(-60, 60), H), 4)
        pygame.draw.ellipse(s, (2, 1, 2), (cx - 330, cy - 300, 660, 620))
        # glowing red skull
        blit_glow(s, (cx, cy - 20), 330, (150, 20, 6))
        pygame.draw.ellipse(s, (170, 30, 14), (cx - 230, cy - 270, 460, 400))
        pygame.draw.ellipse(s, (225, 80, 36), (cx - 170, cy - 250, 220, 140))
        pygame.draw.ellipse(s, (250, 150, 90), (cx - 140, cy - 235, 110, 60))
        for _ in range(9):
            x, y = cx + rng.randint(-190, 190), cy + rng.randint(-240, 60)
            pts = [(x, y)]
            for _ in range(4):
                x += rng.randint(-30, 30)
                y += rng.randint(-30, 30)
                pts.append((x, y))
            pygame.draw.lines(s, (90, 10, 4), False, pts, 3)
        for sd in (-1, 1):
            ex, ey = cx + sd * 100, cy - 80
            pygame.draw.ellipse(s, (4, 0, 0), (ex - 78, ey - 62, 156, 124))
            blit_glow(s, (ex, ey + 6), 34, (255, 120, 30))
            pygame.draw.circle(s, (255, 230, 170), (ex, ey + 6), 7)
        pygame.draw.polygon(s, (6, 0, 0), [(cx, cy - 10), (cx - 34, cy + 50), (cx + 34, cy + 50)])
        jaw = pygame.Rect(cx - 190, cy + 90, 380, 150)
        pygame.draw.rect(s, (5, 0, 0), (cx - 180, cy + 70, 360, 120))
        for k in range(12):
            x = cx - 175 + k * 30
            pygame.draw.rect(s, (235, 170, 130), (x, cy + 60, 24, 42 + rng.randint(-6, 8)), border_radius=5)
            pygame.draw.rect(s, (225, 150, 110), (x, cy + 160 - rng.randint(0, 10), 24, 40), border_radius=5)
        pygame.draw.ellipse(s, (150, 26, 12), (jaw.x, jaw.y + 70, jaw.w, 110))
        # skeletal red hands reaching in from the bottom corners
        for sd in (-1, 1):
            hx, hy = cx + sd * 380, H - 40
            pygame.draw.ellipse(s, (170, 30, 14), (hx - 70, hy - 50, 140, 110))
            for f in range(4):
                fx = hx - 60 + f * 40
                pts = [(fx, hy - 30), (fx - sd * 20, hy - 140 - f % 2 * 20), (fx - sd * 70, hy - 230 - (f in (1, 2)) * 40)]
                pygame.draw.lines(s, (215, 60, 30), False, pts, 18)
                for jx, jy in pts[1:]:
                    pygame.draw.circle(s, (120, 16, 8), (jx, jy), 11)
        # glitch blocks
        for _ in range(12):
            q = rng.randint(6, 36)
            s.fill(rng.choice(GLITCH_COLS), (rng.randint(0, W), rng.randint(0, H), q, q))
        for _ in range(12):
            hgt = rng.randint(6, 40)
            y = rng.randint(0, H - hgt)
            strip = s.subsurface((0, y, W, hgt)).copy()
            s.blit(strip, (rng.randint(-80, 80), y))
        s.blit(self.vignette, (0, 0))
        return s

    def tear(self, surf, n=7, amt=40):
        for _ in range(n):
            h = random.randint(6, 40)
            y = random.randint(0, H - h)
            strip = surf.subsurface((0, y, W, h)).copy()
            surf.blit(strip, (random.randint(-amt, amt), y))

    def draw_scare(self, surf):
        t = self.scare_t
        surf.fill((0, 0, 0))
        if t < 0.05:
            surf.fill((255, 255, 255))
            return
        if t > 1.7:
            if int(t * 18) % 3 == 0:
                surf.blit(random.choice(self.static_hard), (0, 0), special_flags=pygame.BLEND_ADD)
            return
        if t < 0.95:
            sc = 0.55 + 0.8 * min(1.0, t / 0.16) + 0.05 * math.sin(t * 55)
        else:
            sc = 1.35 + 0.9 * min(1.0, (t - 0.95) / 0.12)
        img = pygame.transform.scale(self.scare_face, (int(W * sc), int(H * sc)))
        sh = 34 * (1 - min(1.0, t / 1.7)) + (30 if 0.95 < t < 1.2 else 0)
        surf.blit(img, img.get_rect(center=(W // 2 + random.uniform(-sh, sh), H // 2 + random.uniform(-sh, sh))))
        if int(t * 14) % 5 == 0:
            inv = self.white.copy()
            inv.blit(surf, (0, 0), special_flags=pygame.BLEND_SUB)
            surf.blit(inv, (0, 0))
        if t < 0.45 and int(t * 14) % 2 == 0:
            surf.fill((90, 0, 0), special_flags=pygame.BLEND_ADD)
        if 0.95 < t < 1.05:
            surf.fill((200, 200, 200), special_flags=pygame.BLEND_ADD)
        self.tear(surf, 9, 60)
        for _ in range(5):
            q = random.randint(8, 40)
            surf.fill(random.choice(GLITCH_COLS), (random.randint(0, W), random.randint(0, H), q, q))
        surf.blit(random.choice(self.static_hard), (0, 0), special_flags=pygame.BLEND_ADD)

    # ----- screens -----
    def draw_title(self, surf):
        surf.fill((4, 4, 6))
        ex, ey = W * 0.84 + math.sin(self.t * 0.4) * 30, H * 0.8
        if math.sin(self.t * 0.9) < 0.96:
            for s in (-9, 9):
                blit_glow(surf, (ex + s, ey), 18, (130, 10, 10))
                pygame.draw.circle(surf, (255, 60, 50), (int(ex + s), int(ey)), 3)
        jitter = random.random() < 0.07
        if not jitter or random.random() < 0.5:
            dx = random.randint(-4, 4) if jitter else 0
            text(surf, F_TITLE, "NIGHT SHIFT", (60, 0, 0), (W // 2 + 4 + dx, 130), shadow=False)
            text(surf, F_TITLE, "NIGHT SHIFT", (190, 24, 20), (W // 2 + dx, 126), shadow=False)
        text(surf, F_MED, "T H E   T O Y   F A C T O R Y   -   3 D", (170, 160, 150), (W // 2, 200))
        lines = [
            "The factory closed years ago. Tonight you're the only one here.",
            "Or so you thought.",
            "",
            "Find 3 fuses to power the exit gate, then run.",
            "Your flashlight lets you see them... and lets them see you.",
        ]
        for i, ln in enumerate(lines):
            text(surf, F_SM, ln, (200, 195, 185) if i != 1 else (200, 60, 50), (W // 2, 270 + i * 28))
        text(surf, F_XS, "W/S: walk   A/D: sidestep   Mouse or Left/Right: look around", (150, 150, 160), (W // 2, 430))
        text(surf, F_XS, "Shift: run (loud!)   F / Right click: flashlight   Esc: menu", (150, 150, 160), (W // 2, 452))
        if int(self.t * 1.6) % 2 == 0:
            text(surf, F_MED, "PRESS ENTER", (230, 220, 200), (W // 2, 520))
        if self.deaths:
            text(surf, F_XS, f"Times caught: {self.deaths}", (150, 60, 60), (W // 2, 560))
        surf.blit(self.vignette, (0, 0))
        surf.blit(random.choice(self.grain), (0, 0), special_flags=pygame.BLEND_ADD)

    def draw_dead(self, surf):
        surf.fill((14, 0, 0))
        surf.blit(random.choice(self.static_hard), (0, 0), special_flags=pygame.BLEND_ADD)
        surf.fill((90, 0, 0), special_flags=pygame.BLEND_MULT)
        who = "THE REAPER caught you." if self.scare_by == "clank" else "THE SHADE took you."
        text(surf, F_BIG, "YOU DIDN'T SURVIVE THE NIGHT", (230, 40, 30), (W // 2, H // 2 - 60))
        text(surf, F_MED, who, (230, 210, 200), (W // 2, H // 2 + 4))
        text(surf, F_SM, f"Fuses found: {self.fuse_count}/3     Time: {fmt_time(self.play_t)}", (200, 180, 170), (W // 2, H // 2 + 46))
        text(surf, F_SM, "SPACE - try again     ESC - quit", (230, 220, 210), (W // 2, H // 2 + 110))
        surf.blit(self.vignette, (0, 0))

    def draw_win(self, surf):
        top, bot = (20, 18, 40), (150, 80, 60)
        for y in range(0, H, 4):
            pygame.draw.rect(surf, mix(top, bot, y / H), (0, y, W, 4))
        text(surf, F_TITLE, "YOU ESCAPED", (255, 220, 150), (W // 2, H // 2 - 70))
        text(surf, F_MED, "The gate slams shut behind you. Dawn is coming.", (240, 225, 210), (W // 2, H // 2 + 10))
        text(surf, F_SM, f"Time: {fmt_time(self.win_time)}     Times caught: {self.deaths}", (240, 220, 200), (W // 2, H // 2 + 56))
        text(surf, F_SM, "SPACE - play again     ESC - quit", (255, 240, 220), (W // 2, H // 2 + 120))
        surf.blit(random.choice(self.grain), (0, 0), special_flags=pygame.BLEND_ADD)

    def draw(self, surf):
        if self.state == "title":
            self.draw_title(surf)
        elif self.state == "play":
            self.draw_play(surf)
        elif self.state == "scare":
            self.draw_scare(surf)
        elif self.state == "dead":
            self.draw_dead(surf)
        else:
            self.draw_win(surf)

    # ----- input -----
    def toggle_light(self):
        if self.battery <= 0:
            self.say("No battery.", (200, 120, 110), 1.5)
            return
        self.light_on = not self.light_on
        self.play("click", 0.6)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.state == "play":
            self.toggle_light()
        if event.type != pygame.KEYDOWN:
            return True
        k = event.key
        if self.state == "title":
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.reset()
            elif k == pygame.K_ESCAPE:
                return False
        elif self.state == "play":
            if k == pygame.K_f:
                self.toggle_light()
            elif k == pygame.K_ESCAPE:
                if self.drone_ch:
                    self.drone_ch.stop()
                self.grab(False)
                self.state = "title"
        elif self.state in ("dead", "win"):
            if k == pygame.K_SPACE:
                self.reset()
            elif k == pygame.K_ESCAPE:
                return False
        return True


def main():
    game = Game()
    while True:
        dt = min(clock.tick(FPS) / 1000.0, 1 / 30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or not game.handle(event):
                pygame.quit()
                sys.exit()
        game.update(dt, pygame.key.get_pressed())
        game.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()