import sys
import math
import random
import pygame

pygame.init()

WIDTH, HEIGHT = 960, 540
FPS = 60
TILE = 32

# ---------- Tuning ----------
LASER_PERIOD = 2.6   # full on/off cycle (seconds)
LASER_ON = 1.1       # how long the beam is deadly
LASER_WARN = 0.5     # flicker warning before it turns on
SAW_R = 12
SAW_SPEED_H = 115
SAW_SPEED_V = 95
PAD_POWER = -930
CRUMBLE_DELAY = 0.45
CRUMBLE_RESPAWN = 2.6

# ---------- Palette ----------
BG_TOP = (10, 14, 26)
BG_BOTTOM = (24, 32, 52)
GRID = (26, 34, 52)
METAL_EDGE = (30, 38, 54)
METAL = (58, 70, 94)
METAL_LIGHT = (96, 114, 146)
METAL_DARK = (40, 48, 66)
INTERIOR = (36, 44, 62)
RIVET = (125, 140, 165)
NEON = (90, 200, 235)
SPIKE = (185, 195, 210)
SPIKE_DARK = (105, 114, 132)
SPIKE_TIP = (240, 80, 80)
ACID = (80, 235, 100)
ACID_DARK = (30, 140, 60)
EXIT = (80, 225, 135)
EXIT_LOCKED = (130, 95, 110)
DOOR = (235, 165, 60)
KEY = (255, 215, 70)
WHITE = (235, 240, 255)
SLIME = (100, 235, 160)
SLIME_DARK = (30, 150, 95)
SLIME_LIGHT = (205, 255, 228)
BLOCK = (70, 200, 210)
BLOCK_DARK = (25, 105, 125)
BLOCK_LIGHT = (180, 248, 252)
CRUMBLE = (135, 102, 72)
CRUMBLE_DARK = (62, 46, 36)
CRUMBLE_LIGHT = (175, 140, 104)
PAD = (255, 110, 185)
SAW = (155, 165, 180)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Slime Lab - Inspired Platformer")
clock = pygame.time.Clock()
font = pygame.font.SysFont("segoeui,arial", 26, bold=True)
big_font = pygame.font.SysFont("segoeui,arial", 46, bold=True)
small_font = pygame.font.SysFont("segoeui,arial", 18, bold=True)
hint_font = pygame.font.SysFont("segoeui,arial", 16)

# ---------- Levels ----------
# Legend:
#  #  wall              S  start            E  exit           K  key
#  D  door (opens when all keys are collected)
#  ^  floor spikes      v  ceiling spikes   ~  acid
#  M  saw moving left/right                 N  saw moving up/down
#  L  laser emitter (fires downward on a timer, blocked by walls and your blocks)
#  C  crumbling platform (breaks shortly after you stand on it, then returns)
#  B  bounce pad


def make_level(name, title, rows):
    assert len(rows) == 10, name
    for r in rows:
        assert len(r) == 28, (name, r, len(r))
    return {"name": name, "title": title, "map": ["#" * 30] + ["#" + r + "#" for r in rows] + ["#" * 30]}


LEVELS = [
    {
        "name": "Lab 1",
        "map": [
            "##############################",
            "#S.........................K.#",
            "#.............####...........#",
            "#.................#..........#",
            "#.........^.......#......E...#",
            "#......######.....#..#########",
            "#....................#########",
            "#..............~~............#",
            "#...........########.........#",
            "#.......................######",
            "#.......................######",
            "##############################",
        ],
    },
    {
        "name": "Lab 2",
        "map": [
            "##############################",
            "#S.......................K...#",
            "#.....######.................#",
            "#.................D..........#",
            "#.................D..........#",
            "#.....^^^^........D..........#",
            "#..................#####.....#",
            "#......~~~~..................#",
            "#..............######........#",
            "#...........E................#",
            "#.......................######",
            "##############################",
        ],
    },
    {
        "name": "Lab 3",
        "map": [
            "##############################",
            "#S....................K......#",
            "#........######..............#",
            "#....................####....#",
            "#....^^^^....................#",
            "#...........~~~~.............#",
            "#.................D..........#",
            "#.................D..........#",
            "#.................D..........#",
            "#..E..............####.......#",
            "#.......................######",
            "##############################",
        ],
    },
    make_level("Lab 4", "Drip Room - watch the ceiling", [
        "S...........................",
        "####........................",
        "........######......######..",
        "........vvvvvv......vvvvvv..",
        "............................",
        "..####.........####.......K.",
        "..vvvv.........vvvv......###",
        "............................",
        "............######..........",
        "E...........^^......^^......",
    ]),
    make_level("Lab 5", "Crumble Zone - keep moving", [
        "S...........................",
        "###CCCCCC...CCCCC...........",
        ".................CCCC......K",
        "......................######",
        "E...........................",
        "##..CCCC....CCCC............",
        "............................",
        "............................",
        "............................",
        "~~~~~~~~~~~~~~~~~~~~~~~~~~~.",
    ]),
    make_level("Lab 6", "Boing! - try the bounce pads", [
        "...........................K",
        "......................######",
        "............................",
        "............................",
        "..........#####.............",
        "............................",
        "............................",
        "......#####.................",
        "............................",
        "S...B.......B..^^^^.B.....E.",
    ]),
    make_level("Lab 7", "Saw Mill", [
        "S...........................",
        "########################....",
        "............M...............",
        "....########################",
        "............................",
        "........M...................",
        "########################....",
        "............................",
        "............................",
        "E.......M..................K",
    ]),
    make_level("Lab 8", "Laser Hall - wait for the gap", [
        "S.......L.......L.......L...",
        "###.........................",
        "............................",
        "............................",
        "............................",
        "...........######...........",
        "............................",
        "............................",
        "............................",
        ".....^^.........^^.....E...K",
    ]),
    make_level("Lab 9", "Elevator Saws", [
        "S...........................",
        "###...N.......N.......N.....",
        "............................",
        "............................",
        "...........................K",
        "........................####",
        "............................",
        "............................",
        "............................",
        "E...........................",
    ]),
    make_level("Lab 10", "Acid Steps", [
        "S.........vvvvvvvv..........",
        "###.........................",
        "...CCC...CCC...CCC...CCC....",
        "..........................K.",
        "........................####",
        "............................",
        "..........#####.............",
        "............................",
        "E...........................",
        "##~~~~~~~~~~~~~~~~~~~~~~~~~~",
    ]),
    make_level("Lab 11", "High Ceiling, Sharp Ceiling", [
        "...........................K",
        "..........######.......#####",
        "..........vvvvvv............",
        "............................",
        "............................",
        "....######..................",
        "....vvvvvv..................",
        "............................",
        "............................",
        "S.B....B......B....B......E.",
    ]),
    make_level("Lab 12", "Locked Lasers", [
        "K....L.....L.....L....#L....",
        "###...................#.....",
        "......................#.....",
        "......................#.....",
        "....####..........#####.....",
        "......................#.....",
        "......................D.....",
        "......................D.....",
        "......................D.....",
        "S.........^^..........D...E.",
    ]),
    make_level("Lab 13", "Grinder", [
        "S...........................",
        "######################......",
        "..........N........N........",
        "............................",
        "......######################",
        "............................",
        "...M........................",
        "########################....",
        "............................",
        "E.............M............K",
    ]),
    make_level("Lab 14", "Acid Lake", [
        "S...........................",
        "##..........................",
        "...CC....CC....CC....CC.....",
        "............................",
        "......CC....CC....CC....CC.K",
        "...........................#",
        ".CC.....CC.....CC...........",
        "............................",
        "E...........................",
        "#~~~~~~~~~~~~~~~~~~~~~~~~~~~",
    ]),
    make_level("Lab 15", "The Climb", [
        "E...........................",
        "####........................",
        ".......########.............",
        ".......vvvvvvvv.......####..",
        "......................vvvv..",
        "..####.......####...........",
        "..vvvv.......vvvv......K....",
        ".......................###..",
        "............................",
        "S.........^^^...............",
    ]),
    make_level("Lab 16", "Saws and Beams", [
        "S.....L.....L.....L.....L...",
        "###.........................",
        "............................",
        "............................",
        "........M...................",
        "............................",
        "......######......######....",
        "............................",
        "............................",
        "E...........M..............K",
    ]),
    make_level("Lab 17", "Trampoline Tower", [
        "..........................E.",
        ".........................###",
        "............................",
        "...............###..........",
        "...............vvv..........",
        "..........B.................",
        "..........###......B........",
        "...................###......",
        "....B......................K",
        "S...#....^^^^^^^^^^^^^^^^^##",
    ]),
    make_level("Lab 18", "Two Keys", [
        "S..........................K",
        "####...............#########",
        ".....................#......",
        "..........######.....#......",
        ".....................#......",
        "K....................D......",
        "######...............D......",
        "....................#D......",
        "....................#D......",
        ".........^^^^.......#D....E.",
    ]),
    make_level("Lab 19", "Spike Maze", [
        "S..............vvvvvvvvvvvvv",
        "###.........................",
        "......^^^......^^^......K...",
        "....#########..#############",
        "....vvvvvvvvv..vvvvvvvvv....",
        "............................",
        "............^^^^............",
        "..........########..........",
        "............................",
        "E......^^^^.........^^^^....",
    ]),
    make_level("Lab 20", "Shaky Ground", [
        "S...........................",
        "##CCCCCC....CCCCCC....CCCC..",
        "............................",
        ".......N.........N........K.",
        "........................####",
        "....######......######......",
        "............................",
        "...M........................",
        "............................",
        "E....~~~~~~~~~~~~~~~~~~.....",
    ]),
    make_level("Lab 21", "Laser Grid", [
        "S...L...L...L...L...L...L...",
        "###.........................",
        "............................",
        "............######..........",
        "...........................K",
        ".....................#######",
        "............................",
        "......######................",
        "............................",
        "E...........................",
    ]),
    make_level("Lab 22", "Everything Room", [
        "S.......L..........vvvvvv...",
        "####.....................K..",
        "..........CCCC.........#####",
        "........................#...",
        "...######...........M...#...",
        "..........N.............#...",
        "........................D...",
        "...B....######..........D...",
        "####....................D...",
        "....^^^^......~~~~......D.E.",
    ]),
    make_level("Lab 23", "Final Exam", [
        "S....L....L....L....L......K",
        "###...................CC####",
        "............................",
        ".........M..................",
        "#####........N.......N......",
        "D...........................",
        "D...........................",
        "D.......########......B.....",
        "D...........vvvv.....###....",
        "E~~~~~~~~~~~...........^^^^.",
    ]),
]

SOLID_CHARS = "#L"


# ---------- Visual helpers ----------
def vertical_gradient(w, h, top, bottom):
    s = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        c = [int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)]
        pygame.draw.line(s, c, (0, y), (w, y))
    return s


def make_vignette(w, h, strength=170):
    sw, sh = 48, 27
    small = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cx, cy = (sw - 1) / 2, (sh - 1) / 2
    for y in range(sh):
        for x in range(sw):
            d = math.hypot((x - cx) / cx, (y - cy) / cy) / math.sqrt(2)
            t = max(0.0, min(1.0, (d - 0.35) / 0.65))
            small.set_at((x, y), (0, 0, 0, int((t ** 1.6) * strength)))
    return pygame.transform.smoothscale(small, (w, h))


_glow_cache = {}


def glow(radius, color, intensity=1.0):
    key = (radius, color, round(intensity, 1))
    s = _glow_cache.get(key)
    if s is None:
        s = pygame.Surface((radius * 2, radius * 2))
        s.fill((0, 0, 0))
        for r in range(radius, 0, -1):
            t = (1 - r / radius) ** 2 * key[2]
            c = tuple(min(255, int(ch * t)) for ch in color)
            pygame.draw.circle(s, c, (radius, radius), r)
        _glow_cache[key] = s
    return s


def blit_glow(surf, pos, radius, color, intensity=1.0):
    g = glow(radius, color, intensity)
    surf.blit(g, (int(pos[0]) - radius, int(pos[1]) - radius), special_flags=pygame.BLEND_ADD)


def text_with_shadow(surf, fnt, text, color, pos, center=False, alpha=255):
    shadow = fnt.render(text, True, (0, 0, 0))
    main = fnt.render(text, True, color)
    if alpha < 255:
        shadow.set_alpha(alpha)
        main.set_alpha(alpha)
    x, y = pos
    if center:
        x -= main.get_width() // 2
    surf.blit(shadow, (x + 2, y + 2))
    surf.blit(main, (x, y))
    return main.get_width()


def circle_hits_rect(cx, cy, radius, rect):
    qx = max(rect.left, min(cx, rect.right))
    qy = max(rect.top, min(cy, rect.bottom))
    return (qx - cx) ** 2 + (qy - cy) ** 2 < radius * radius


# ---------- Worlds ----------
def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def jitter(c, rng, amt=8):
    d = rng.randint(-amt, amt)
    return tuple(max(0, min(255, v + d)) for v in c)


# liquid = (main, dark, light, glow)
LIQ_ACID = ((80, 235, 100), (30, 140, 60), (190, 255, 180), (20, 95, 35))
LIQ_LAVA = ((255, 125, 30), (185, 45, 10), (255, 225, 130), (130, 45, 5))
LIQ_PURPLE = ((175, 85, 235), (95, 35, 145), (225, 175, 255), (60, 20, 90))
LIQ_TOXIC = ((175, 230, 40), (95, 135, 20), (235, 255, 150), (60, 90, 10))
LIQ_MAGENTA = ((235, 45, 125), (135, 12, 62), (255, 160, 205), (90, 10, 40))


def world(**kw):
    d = dict(wall=None, glow=None, deco=(0, 0, 0), deco2=(0, 0, 0), liquid=LIQ_ACID,
             ambient="dust", amb=(255, 255, 255))
    d.update(kw)
    return d


WORLDS = [
    world(name="Slime Lab", sky=((10, 14, 26), (24, 32, 52)), wall=(16, 22, 36), backdrop="pipes",
          style="metal", base=(58, 70, 94), light=(96, 114, 146), dark=(40, 48, 66), edge=(30, 38, 54),
          top=(90, 200, 235), interior=(36, 44, 62), glow=(20, 60, 75), ambient="dust", amb=(110, 140, 180)),
    world(name="Emerald Forest", sky=((12, 34, 40), (40, 92, 80)), backdrop="trees",
          deco=(20, 54, 48), deco2=(14, 40, 36), style="grass",
          base=(96, 66, 44), light=(130, 92, 60), dark=(66, 44, 30), edge=(50, 34, 24),
          top=(80, 190, 80), interior=(74, 50, 34), ambient="fireflies", amb=(220, 255, 120)),
    world(name="Sunset Desert", sky=((60, 30, 70), (240, 140, 80)), backdrop="dunes", sun=(255, 215, 130),
          deco=(190, 105, 75), deco2=(140, 70, 60), style="sand",
          base=(210, 170, 110), light=(240, 210, 150), dark=(160, 120, 70), edge=(130, 95, 55),
          top=(245, 225, 170), interior=(180, 140, 85), ambient="dust", amb=(255, 220, 170)),
    world(name="Frozen Peaks", sky=((30, 50, 90), (140, 180, 220)), backdrop="mountains", snowcaps=True,
          deco=(95, 125, 165), deco2=(60, 85, 125), style="ice",
          base=(150, 200, 235), light=(225, 245, 255), dark=(100, 150, 200), edge=(70, 110, 160),
          top=(250, 252, 255), interior=(120, 170, 215), ambient="snow", amb=(255, 255, 255)),
    world(name="Lava Caves", sky=((20, 6, 6), (70, 20, 10)), wall=(34, 14, 12), backdrop="lava",
          deco=(50, 18, 14), style="stone",
          base=(70, 40, 36), light=(110, 64, 54), dark=(44, 24, 22), edge=(30, 16, 14),
          top=(255, 120, 40), interior=(52, 30, 28), glow=(90, 30, 5), liquid=LIQ_LAVA,
          ambient="embers", amb=(255, 150, 60)),
    world(name="Candy Land", sky=((215, 115, 175), (255, 200, 225)), backdrop="clouds",
          deco=(255, 235, 245), style="candy",
          base=(240, 110, 160), light=(255, 190, 215), dark=(190, 70, 120), edge=(150, 50, 95),
          top=(255, 250, 250), interior=(210, 90, 140), liquid=LIQ_PURPLE,
          ambient="sparkles", amb=(255, 255, 255)),
    world(name="Deep Ocean", sky=((4, 30, 60), (10, 80, 110)), backdrop="bubbles",
          deco=(60, 160, 190), deco2=(20, 90, 80), style="stone",
          base=(40, 90, 100), light=(70, 140, 145), dark=(25, 60, 70), edge=(15, 40, 50),
          top=(255, 130, 120), interior=(30, 70, 80), liquid=LIQ_PURPLE,
          ambient="bubbles", amb=(160, 230, 255)),
    world(name="Neon City", sky=((8, 6, 20), (44, 22, 66)), backdrop="city", window=(255, 200, 90),
          deco=(30, 22, 54), deco2=(18, 14, 34), style="metal",
          base=(40, 40, 60), light=(80, 80, 110), dark=(28, 28, 42), edge=(18, 18, 30),
          top=(255, 60, 200), interior=(30, 30, 46), glow=(80, 10, 60), ambient="rain", amb=(120, 140, 200)),
    world(name="Outer Space", sky=((2, 2, 10), (14, 10, 36)), backdrop="stars", planet=(130, 90, 210), ring=True,
          style="metal", base=(80, 84, 100), light=(130, 135, 155), dark=(55, 58, 70), edge=(36, 38, 48),
          top=(255, 200, 80), interior=(60, 62, 76), glow=(60, 45, 10), ambient="twinkle", amb=(255, 255, 255)),
    world(name="Haunted Graveyard", sky=((14, 10, 28), (48, 36, 70)), backdrop="graves", moon=(230, 230, 210),
          deco=(30, 24, 46), deco2=(20, 16, 32), style="stone",
          base=(78, 74, 92), light=(112, 108, 130), dark=(52, 48, 64), edge=(34, 30, 44),
          top=(90, 140, 80), interior=(60, 56, 74), liquid=LIQ_PURPLE,
          ambient="fireflies", amb=(160, 255, 180)),
    world(name="Sky Kingdom", sky=((80, 140, 225), (190, 225, 255)), backdrop="clouds",
          deco=(255, 255, 255), style="cloud",
          base=(245, 248, 255), light=(255, 255, 255), dark=(195, 208, 232), edge=(170, 185, 215),
          top=(255, 255, 255), interior=(230, 236, 250), ambient="sparkles", amb=(255, 250, 200)),
    world(name="Crystal Mines", sky=((12, 8, 24), (30, 20, 50)), wall=(22, 16, 36), backdrop="crystals",
          deco=(90, 60, 160), deco2=(50, 120, 160), style="crystal",
          base=(50, 40, 80), light=(170, 120, 255), dark=(34, 26, 56), edge=(22, 16, 36),
          top=(120, 240, 255), interior=(40, 32, 64), glow=(40, 20, 80), ambient="sparkles", amb=(200, 170, 255)),
    world(name="Mushroom Grove", sky=((30, 14, 40), (80, 40, 90)), backdrop="mushrooms",
          deco=(70, 36, 82), deco2=(130, 60, 120), style="grass",
          base=(70, 50, 60), light=(100, 72, 86), dark=(48, 34, 42), edge=(34, 24, 30),
          top=(190, 90, 230), interior=(58, 40, 50), ambient="fireflies", amb=(255, 150, 255)),
    world(name="Toxic Swamp", sky=((16, 24, 14), (54, 70, 34)), backdrop="trees", round_trees=True,
          deco=(30, 42, 24), deco2=(20, 30, 16), style="grass",
          base=(64, 58, 40), light=(94, 86, 58), dark=(44, 40, 28), edge=(30, 28, 20),
          top=(120, 150, 50), interior=(52, 48, 32), liquid=LIQ_TOXIC,
          ambient="fireflies", amb=(200, 255, 80)),
    world(name="Autumn Woods", sky=((70, 34, 44), (235, 150, 90)), backdrop="trees", round_trees=True,
          deco=(150, 70, 40), deco2=(100, 44, 30), style="grass",
          base=(110, 70, 44), light=(150, 100, 62), dark=(80, 50, 30), edge=(58, 36, 22),
          top=(230, 120, 40), interior=(92, 58, 36), ambient="leaves", amb=(240, 130, 40)),
    world(name="Cyber Grid", sky=((4, 4, 16), (34, 6, 56)), backdrop="grid",
          deco=(255, 60, 200), deco2=(40, 220, 255), style="circuit",
          base=(14, 18, 30), light=(40, 220, 255), dark=(8, 10, 18), edge=(24, 60, 90),
          top=(40, 220, 255), interior=(12, 14, 24), glow=(10, 60, 80), liquid=LIQ_MAGENTA,
          ambient="sparkles", amb=(40, 220, 255)),
    world(name="Ancient Temple", sky=((40, 26, 20), (200, 140, 80)), backdrop="pillars",
          deco=(150, 100, 62), deco2=(115, 76, 48), style="stone",
          base=(190, 150, 95), light=(225, 190, 130), dark=(140, 105, 65), edge=(110, 80, 50),
          top=(230, 200, 140), interior=(165, 125, 80), ambient="dust", amb=(255, 230, 180)),
    world(name="Snowy Village", sky=((10, 16, 40), (44, 64, 104)), backdrop="mountains", snowcaps=True,
          deco=(44, 60, 96), deco2=(28, 40, 70), style="wood",
          base=(120, 80, 50), light=(160, 110, 70), dark=(84, 54, 34), edge=(60, 38, 24),
          top=(245, 250, 255), interior=(100, 66, 42), ambient="snow", amb=(255, 255, 255)),
    world(name="Volcano Peak", sky=((30, 8, 8), (125, 32, 16)), backdrop="mountains", lava_glow=True,
          deco=(62, 18, 14), deco2=(38, 10, 8), style="stone",
          base=(44, 38, 38), light=(74, 64, 62), dark=(28, 24, 24), edge=(16, 14, 14),
          top=(255, 90, 20), interior=(34, 30, 30), glow=(100, 30, 0), liquid=LIQ_LAVA,
          ambient="embers", amb=(255, 140, 50)),
    world(name="Moon Base", sky=((0, 0, 4), (10, 10, 22)), backdrop="stars", planet=(60, 130, 210),
          style="metal", base=(170, 175, 185), light=(220, 225, 235), dark=(120, 125, 135), edge=(80, 84, 94),
          top=(255, 90, 90), interior=(140, 145, 155), glow=(60, 10, 10), ambient="twinkle", amb=(255, 255, 255)),
    world(name="Jungle Ruins", sky=((10, 40, 24), (44, 115, 64)), backdrop="trees", round_trees=True,
          deco=(18, 60, 32), deco2=(12, 44, 24), style="stone",
          base=(90, 100, 80), light=(130, 140, 110), dark=(62, 70, 56), edge=(42, 48, 38),
          top=(70, 170, 60), interior=(74, 82, 66), ambient="rain", amb=(150, 200, 170)),
    world(name="Dreamland", sky=((60, 30, 110), (240, 140, 200)), backdrop="clouds",
          deco=(255, 200, 240), style="candy",
          base=(140, 110, 230), light=(200, 180, 255), dark=(100, 70, 180), edge=(70, 50, 140),
          top=(255, 240, 140), interior=(120, 90, 200), liquid=LIQ_MAGENTA,
          ambient="sparkles", amb=(255, 240, 180)),
    world(name="Shadow Realm", sky=((4, 0, 8), (34, 4, 34)), backdrop="crystals",
          deco=(70, 14, 70), deco2=(110, 14, 50), style="stone",
          base=(34, 22, 40), light=(74, 44, 84), dark=(20, 14, 24), edge=(10, 6, 14),
          top=(210, 40, 130), interior=(26, 18, 32), glow=(60, 5, 40), liquid=LIQ_MAGENTA,
          ambient="embers", amb=(230, 70, 170)),
]


# ----- Tile styles -----
def tile_metal(surf, r, top, interior, w, rng):
    if interior:
        pygame.draw.rect(surf, w["interior"], r)
        pygame.draw.rect(surf, w["edge"], r, 1)
        return
    pygame.draw.rect(surf, w["edge"], r)
    inner = r.inflate(-4, -4)
    pygame.draw.rect(surf, w["base"], inner, border_radius=3)
    pygame.draw.line(surf, w["light"], (inner.left + 2, inner.top), (inner.right - 3, inner.top))
    pygame.draw.line(surf, w["light"], (inner.left, inner.top + 2), (inner.left, inner.bottom - 3))
    pygame.draw.line(surf, w["dark"], (inner.left + 2, inner.bottom - 1), (inner.right - 3, inner.bottom - 1))
    rivet = mix(w["light"], (255, 255, 255), 0.2)
    for cx, cy in ((inner.left + 4, inner.top + 4), (inner.right - 5, inner.top + 4),
                   (inner.left + 4, inner.bottom - 5), (inner.right - 5, inner.bottom - 5)):
        pygame.draw.circle(surf, rivet, (cx, cy), 1)
    if top:
        pygame.draw.rect(surf, w["top"], (r.x, r.y, r.w, 3))
        pygame.draw.line(surf, mix(w["top"], (255, 255, 255), 0.6), (r.x, r.y), (r.right - 1, r.y))


def tile_stone(surf, r, top, interior, w, rng):
    base = w["interior"] if interior else w["base"]
    pygame.draw.rect(surf, w["edge"], r)
    for bx, by, bw, bh in ((1, 1, 14, 14), (17, 1, 14, 14), (1, 17, 6, 14), (9, 17, 14, 14), (25, 17, 6, 14)):
        br = pygame.Rect(r.x + bx, r.y + by, bw, bh)
        c = jitter(base, rng, 7)
        pygame.draw.rect(surf, c, br, border_radius=2)
        if not interior:
            pygame.draw.line(surf, mix(c, w["light"], 0.6), (br.x + 1, br.y), (br.right - 2, br.y))
            pygame.draw.line(surf, mix(c, w["dark"], 0.6), (br.x + 1, br.bottom - 1), (br.right - 2, br.bottom - 1))
    if top:
        pygame.draw.rect(surf, w["top"], (r.x, r.y, r.w, 4))
        pygame.draw.line(surf, mix(w["top"], (255, 255, 255), 0.4), (r.x, r.y), (r.right - 1, r.y))
        for _ in range(2):
            x = r.x + rng.randint(2, r.w - 5)
            pygame.draw.rect(surf, w["top"], (x, r.y + 4, 3, rng.randint(2, 7)), border_radius=1)


def tile_grass(surf, r, top, interior, w, rng):
    base = w["interior"] if interior else w["base"]
    pygame.draw.rect(surf, base, r)
    for _ in range(5):
        x = r.x + rng.randint(2, r.w - 4)
        y = r.y + rng.randint(9 if top else 2, r.h - 4)
        pygame.draw.rect(surf, rng.choice((w["dark"], w["light"])), (x, y, 2, 2))
    if not interior:
        pygame.draw.line(surf, w["dark"], (r.x, r.bottom - 1), (r.right - 1, r.bottom - 1))
    if top:
        pygame.draw.rect(surf, mix(w["top"], (0, 0, 0), 0.4), (r.x, r.y + 5, r.w, 3))
        pygame.draw.rect(surf, w["top"], (r.x, r.y, r.w, 6))
        for i in range(5):
            x = r.x + 3 + i * 6 + rng.randint(-1, 1)
            h = rng.randint(3, 6)
            pygame.draw.polygon(surf, w["top"], [(x - 2, r.y + 1), (x, r.y - h), (x + 2, r.y + 1)])
        pygame.draw.line(surf, mix(w["top"], (255, 255, 255), 0.35), (r.x, r.y), (r.right - 1, r.y))


def tile_sand(surf, r, top, interior, w, rng):
    base = w["interior"] if interior else w["base"]
    pygame.draw.rect(surf, w["edge"], r)
    pygame.draw.rect(surf, base, r.inflate(-2, -2), border_radius=2)
    for _ in range(6):
        pygame.draw.circle(surf, rng.choice((w["light"], w["dark"])),
                           (r.x + rng.randint(3, r.w - 4), r.y + rng.randint(7, r.h - 4)), 1)
    if top:
        pts = [(r.x, r.y)] + [(r.x + i, r.y + 5 + math.sin((r.x + i) * 0.3) * 1.5) for i in range(0, r.w + 1, 4)]
        pts.append((r.right, r.y))
        pygame.draw.polygon(surf, w["top"], pts)


def snow_cap(surf, r, w, rng):
    pygame.draw.rect(surf, w["top"], (r.x, r.y, r.w, 5), border_radius=2)
    for _ in range(3):
        pygame.draw.circle(surf, w["top"], (r.x + rng.randint(3, r.w - 4), r.y + 4), rng.randint(2, 4))


def tile_ice(surf, r, top, interior, w, rng):
    base = w["interior"] if interior else w["base"]
    pygame.draw.rect(surf, w["edge"], r)
    inner = r.inflate(-2, -2)
    pygame.draw.rect(surf, base, inner, border_radius=3)
    if not interior:
        pygame.draw.line(surf, w["light"], (inner.x + 4, inner.bottom - 6), (inner.x + 14, inner.y + 5), 2)
        pygame.draw.line(surf, w["light"], (inner.x + 10, inner.bottom - 4), (inner.x + 16, inner.bottom - 12), 1)
        pygame.draw.line(surf, w["dark"], (inner.x + 1, inner.bottom - 1), (inner.right - 2, inner.bottom - 1))
    if top:
        snow_cap(surf, r, w, rng)


def tile_candy(surf, r, top, interior, w, rng):
    base = w["interior"] if interior else w["base"]
    pygame.draw.rect(surf, w["edge"], r)
    inner = r.inflate(-2, -2)
    pygame.draw.rect(surf, base, inner, border_radius=4)
    if not interior:
        clip = surf.get_clip()
        surf.set_clip(inner)
        for k in range(-r.w, r.w, 10):
            pygame.draw.line(surf, w["light"], (inner.x + k, inner.bottom), (inner.x + k + inner.h, inner.y), 3)
        surf.set_clip(clip)
    if top:
        pygame.draw.rect(surf, w["top"], (r.x, r.y, r.w, 6), border_radius=3)
        for _ in range(2):
            x = r.x + rng.randint(4, r.w - 5)
            pygame.draw.rect(surf, w["top"], (x - 3, r.y + 3, 6, 4))
            pygame.draw.circle(surf, w["top"], (x, r.y + 7), 3)
        for _ in range(3):
            pygame.draw.rect(surf, rng.choice(((255, 90, 90), (90, 200, 255), (255, 220, 80), (140, 255, 140))),
                             (r.x + rng.randint(2, r.w - 5), r.y + 1 + rng.randint(0, 3), 3, 2))


def tile_circuit(surf, r, top, interior, w, rng):
    pygame.draw.rect(surf, w["interior"] if interior else w["base"], r)
    pygame.draw.rect(surf, w["edge"], r, 1)
    tc = mix(w["light"], w["base"], 0.65)
    y = r.y + rng.randint(8, 24)
    x = r.x + rng.randint(8, 24)
    pygame.draw.line(surf, tc, (r.x, y), (x, y), 1)
    pygame.draw.line(surf, tc, (x, y), (x, r.bottom - 1 if rng.random() < 0.5 else r.y), 1)
    pygame.draw.circle(surf, mix(w["light"], w["base"], 0.3), (x, y), 2)
    if top:
        pygame.draw.rect(surf, w["top"], (r.x, r.y, r.w, 2))


def tile_cloud(surf, r, top, interior, w, rng):
    if interior:
        pygame.draw.rect(surf, w["interior"], r)
        return
    pygame.draw.rect(surf, w["dark"], (r.x, r.y + 6, r.w, r.h - 6), border_radius=6)
    pygame.draw.rect(surf, w["base"], (r.x, r.y + 3, r.w, r.h - 9), border_radius=6)
    if top:
        for cx, rad in ((r.x + 7, 8), (r.x + 18, 10), (r.x + 28, 7)):
            pygame.draw.circle(surf, w["base"], (cx, r.y + 9), rad)
        pygame.draw.circle(surf, w["light"], (r.x + 14, r.y + 3), 3)


def tile_crystal(surf, r, top, interior, w, rng):
    base = w["interior"] if interior else w["base"]
    pygame.draw.rect(surf, w["edge"], r)
    inner = r.inflate(-2, -2)
    pygame.draw.rect(surf, base, inner, border_radius=2)
    if not interior:
        p = [(inner.x + rng.randint(2, 10), inner.bottom - 2),
             (inner.x + rng.randint(10, 20), inner.y + rng.randint(3, 10)),
             (inner.right - rng.randint(2, 8), inner.bottom - rng.randint(4, 12))]
        pygame.draw.polygon(surf, mix(base, w["light"], 0.35), p)
        pygame.draw.line(surf, w["light"], p[0], p[1], 1)
    if top:
        for _ in range(2):
            x = r.x + rng.randint(4, r.w - 6)
            h = rng.randint(5, 10)
            pygame.draw.polygon(surf, w["top"], [(x - 3, r.y + 2), (x, r.y - h), (x + 3, r.y + 2)])
            pygame.draw.line(surf, (255, 255, 255), (x, r.y - h + 2), (x, r.y), 1)
        pygame.draw.line(surf, w["top"], (r.x, r.y), (r.right - 1, r.y), 2)


def tile_wood(surf, r, top, interior, w, rng):
    base = w["interior"] if interior else w["base"]
    pygame.draw.rect(surf, w["edge"], r)
    for y, h in ((1, 9), (11, 10), (22, 9)):
        pr = pygame.Rect(r.x + 1, r.y + y, r.w - 2, h)
        c = jitter(base, rng, 8)
        pygame.draw.rect(surf, c, pr)
        if not interior:
            gx = pr.x + rng.randint(3, 18)
            pygame.draw.line(surf, mix(c, w["dark"], 0.5), (gx, pr.centery), (gx + rng.randint(5, 9), pr.centery), 1)
            pygame.draw.circle(surf, w["dark"], (pr.x + 3, pr.centery), 1)
            pygame.draw.circle(surf, w["dark"], (pr.right - 4, pr.centery), 1)
    if top:
        snow_cap(surf, r, w, rng)


TILE_STYLES = dict(metal=tile_metal, stone=tile_stone, grass=tile_grass, sand=tile_sand, ice=tile_ice,
                   candy=tile_candy, circuit=tile_circuit, cloud=tile_cloud, crystal=tile_crystal, wood=tile_wood)


# ----- Backdrops -----
def draw_backdrop(surf, w, area, rng):
    kind = w["backdrop"]
    d1, d2 = w["deco"], w["deco2"]

    if kind == "pipes":
        for _ in range(4):
            px = rng.randrange(area.left + 40, area.right - 40)
            pygame.draw.rect(surf, (24, 32, 50), (px, area.top, 10, area.h))
            pygame.draw.line(surf, (36, 48, 72), (px + 2, area.top), (px + 2, area.bottom), 2)
        for _ in range(2):
            py = rng.randrange(area.top + 60, area.bottom - 60)
            pygame.draw.rect(surf, (24, 32, 50), (area.left, py, area.w, 8))
            pygame.draw.line(surf, (36, 48, 72), (area.left, py + 2), (area.right, py + 2), 2)
        for _ in range(10):
            lx = rng.randrange(area.left + 20, area.right - 20)
            ly = rng.randrange(area.top + 20, area.bottom - 20)
            color = rng.choice([(40, 120, 150), (40, 130, 80), (140, 80, 50)])
            blit_glow(surf, (lx, ly), 14, color, 0.6)
            pygame.draw.circle(surf, color, (lx, ly), 2)

    elif kind == "stars":
        for _ in range(180):
            x, y = rng.randrange(WIDTH), rng.randrange(HEIGHT)
            b = rng.random()
            c = mix(w["sky"][0], (255, 255, 255), 0.25 + 0.75 * b * b)
            surf.set_at((x, y), c)
            if b > 0.93:
                pygame.draw.line(surf, c, (x - 2, y), (x + 2, y))
                pygame.draw.line(surf, c, (x, y - 2), (x, y + 2))
        if w.get("planet"):
            pc = w["planet"]
            px, py = rng.randint(area.left + 140, area.right - 140), rng.randint(area.top + 70, area.top + 140)
            rad = rng.randint(42, 58)
            blit_glow(surf, (px, py), rad + 45, mix(pc, (0, 0, 0), 0.65), 1.0)
            pygame.draw.circle(surf, pc, (px, py), rad)
            pygame.draw.circle(surf, mix(pc, (255, 255, 255), 0.25), (px - rad // 3, py - rad // 3), rad // 3)
            for _ in range(5):
                a, dd = rng.random() * math.tau, rng.random() * rad * 0.6
                pygame.draw.circle(surf, mix(pc, (0, 0, 0), 0.25),
                                   (int(px + math.cos(a) * dd), int(py + math.sin(a) * dd)), rng.randint(3, 8))
            if w.get("ring"):
                pygame.draw.ellipse(surf, mix(pc, (255, 255, 255), 0.45),
                                    (px - int(rad * 1.7), py - int(rad * 0.3), int(rad * 3.4), int(rad * 0.6)), 2)

    elif kind == "mountains":
        if w.get("lava_glow"):
            for _ in range(6):
                blit_glow(surf, (rng.randint(area.left, area.right), area.bottom), rng.randint(90, 140), (90, 25, 4), 1.0)
        for layer, (col, lo, hi) in enumerate(((d1, 30, 150), (d2, 120, 230))):
            pts = [(0, HEIGHT)]
            x = -20
            while x < WIDTH + 80:
                pts.append((x, area.top + rng.randint(lo, hi)))
                x += rng.randint(50, 110)
            pts.append((WIDTH, HEIGHT))
            pygame.draw.polygon(surf, col, pts)
            if layer == 0 and w.get("snowcaps"):
                cap = mix(col, (255, 255, 255), 0.6)
                for i in range(2, len(pts) - 2):
                    (x, y), (_, ya), (_, yb) = pts[i], pts[i - 1], pts[i + 1]
                    if y < ya and y < yb:
                        pygame.draw.polygon(surf, cap, [(x - 13, y + 15), (x, y), (x + 13, y + 15)])

    elif kind == "trees":
        for col, n, (hlo, hhi), scale in ((d1, 16, (110, 200), 0.8), (d2, 9, (150, 260), 1.0)):
            for _ in range(n):
                x = rng.randint(area.left - 20, area.right + 20)
                by = area.bottom
                h = rng.randint(hlo, hhi)
                pygame.draw.rect(surf, col, (x - 4, int(by - h * 0.45), 8, int(h * 0.45)))
                if w.get("round_trees"):
                    for _ in range(4):
                        pygame.draw.circle(surf, col, (x + rng.randint(-20, 20), int(by - h * 0.55 - rng.randint(0, 45))),
                                           int(24 * scale + rng.randint(0, 10)))
                else:
                    for k in range(3):
                        tw = int((40 - k * 9) * scale)
                        ty = by - h * 0.3 - k * h * 0.22
                        pygame.draw.polygon(surf, col, [(x - tw, int(ty)), (x, int(ty - h * 0.35)), (x + tw, int(ty))])

    elif kind == "dunes":
        sx, sy = area.right - 170, area.top + 90
        blit_glow(surf, (sx, sy), 110, mix(w["sun"], (0, 0, 0), 0.55), 1.0)
        pygame.draw.circle(surf, w["sun"], (sx, sy), 42)
        for col, base, amp, f in ((d1, area.top + 220, 26, 0.012), (d2, area.top + 290, 20, 0.018)):
            ph = rng.random() * 6
            pts = [(0, HEIGHT)] + [(x, base + math.sin(x * f + ph) * amp) for x in range(0, WIDTH + 10, 10)]
            pts.append((WIDTH, HEIGHT))
            pygame.draw.polygon(surf, col, pts)

    elif kind == "lava":
        for _ in range(7):
            blit_glow(surf, (rng.randint(area.left, area.right), area.bottom - rng.randint(0, 40)),
                      rng.randint(90, 140), (85, 22, 4), 1.0)
        for _ in range(22):
            x = rng.randint(area.left, area.right)
            h, wd = rng.randint(20, 70), rng.randint(10, 24)
            pygame.draw.polygon(surf, d1, [(x - wd, area.top + TILE), (x, area.top + TILE + h), (x + wd, area.top + TILE)])

    elif kind == "clouds":
        layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for _ in range(14):
            cx, cy = rng.randint(-40, WIDTH + 40), rng.randint(area.top, area.bottom - 40)
            a = rng.randint(60, 130)
            for _ in range(5):
                pygame.draw.ellipse(layer, (*d1, a), (cx + rng.randint(-50, 40), cy + rng.randint(-14, 10),
                                                      rng.randint(50, 100), rng.randint(26, 44)))
        surf.blit(layer, (0, 0))

    elif kind == "bubbles":
        layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for _ in range(6):
            x, wd = rng.randint(area.left - 100, area.right), rng.randint(30, 70)
            pygame.draw.polygon(layer, (*d1, 22), [(x, 0), (x + wd, 0), (x + wd + 140, HEIGHT), (x + 140, HEIGHT)])
        surf.blit(layer, (0, 0))
        for _ in range(16):
            x, h, ph = rng.randint(area.left, area.right), rng.randint(60, 150), rng.random() * 6
            pts = [(x + math.sin(ph + k * 0.5) * 6, area.bottom - k * 8) for k in range(h // 8)]
            pygame.draw.lines(surf, d2, False, pts, 4)
        for _ in range(30):
            pygame.draw.circle(surf, mix(d1, w["sky"][0], 0.5),
                               (rng.randint(area.left, area.right), rng.randint(area.top, area.bottom)), rng.randint(2, 6), 1)

    elif kind == "city":
        mx, my = area.right - 160, area.top + 80
        blit_glow(surf, (mx, my), 80, (50, 40, 70), 1.0)
        pygame.draw.circle(surf, (230, 225, 240), (mx, my), 26)
        for col, hl, hh, wp in ((d1, 120, 260, 0.25), (d2, 60, 170, 0.35)):
            x = area.left - 20
            while x < area.right + 20:
                bw, bh = rng.randint(40, 80), rng.randint(hl, hh)
                br = pygame.Rect(x, area.bottom - bh, bw, bh)
                pygame.draw.rect(surf, col, br)
                for wx in range(br.x + 6, br.right - 6, 10):
                    for wy in range(br.y + 8, br.bottom - 8, 14):
                        if rng.random() < wp:
                            pygame.draw.rect(surf, mix(col, w["window"], 0.55), (wx, wy, 4, 6))
                x += bw + rng.randint(4, 20)

    elif kind == "graves":
        mx, my = area.left + 150, area.top + 90
        blit_glow(surf, (mx, my), 100, (60, 60, 70), 1.0)
        pygame.draw.circle(surf, w["moon"], (mx, my), 36)
        pygame.draw.circle(surf, mix(w["moon"], (0, 0, 0), 0.15), (mx + 10, my - 6), 7)
        ph = rng.random() * 6
        hill = lambda x: area.bottom - 70 + math.sin(x * 0.01 + ph) * 18
        pts = [(0, HEIGHT)] + [(x, hill(x)) for x in range(0, WIDTH + 10, 10)] + [(WIDTH, HEIGHT)]
        pygame.draw.polygon(surf, d1, pts)
        for _ in range(12):
            x = rng.randint(area.left, area.right)
            y = int(hill(x))
            pygame.draw.rect(surf, d2, (x, y - 26, 16, 32), border_top_left_radius=8, border_top_right_radius=8)
        for _ in range(3):
            x = rng.randint(area.left, area.right)
            y = int(hill(x))
            pygame.draw.line(surf, d2, (x, y), (x, y - 110), 4)
            for k in range(4):
                by = y - 50 - k * 15
                d = rng.choice((-1, 1)) * rng.randint(16, 30)
                pygame.draw.line(surf, d2, (x, by), (x + d, by - 18), 2)

    elif kind == "crystals":
        layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for _ in range(16):
            x = rng.randint(area.left, area.right)
            up = rng.random() < 0.6
            base_y = area.bottom if up else area.top + TILE
            h, wd = rng.randint(60, 180), rng.randint(14, 34)
            col = rng.choice((d1, d2))
            tip = base_y - h if up else base_y + h
            mid = base_y + (tip - base_y) * 0.75
            pygame.draw.polygon(layer, (*col, 120), [(x - wd, base_y), (x - wd * 0.6, mid), (x, tip),
                                                     (x + wd * 0.6, mid), (x + wd, base_y)])
            pygame.draw.line(layer, (*mix(col, (255, 255, 255), 0.4), 140), (x, tip), (x, base_y), 1)
        surf.blit(layer, (0, 0))
        for _ in range(5):
            blit_glow(surf, (rng.randint(area.left, area.right), rng.randint(area.top, area.bottom)), 50,
                      mix(d1, (0, 0, 0), 0.5), 1.0)

    elif kind == "mushrooms":
        for _ in range(11):
            x, h, sw = rng.randint(area.left, area.right), rng.randint(70, 200), rng.randint(8, 16)
            pygame.draw.rect(surf, d1, (x - sw // 2, area.bottom - h, sw, h))
            cw = rng.randint(40, 80)
            cap = pygame.Rect(0, 0, cw * 2, cw)
            cap.midbottom = (x, area.bottom - h + 12)
            blit_glow(surf, cap.center, cw + 20, mix(d2, (0, 0, 0), 0.6), 1.0)
            pygame.draw.ellipse(surf, d2, cap)
            for _ in range(4):
                pygame.draw.circle(surf, mix(d2, (255, 255, 255), 0.3),
                                   (cap.x + rng.randint(cw // 3, cw * 2 - cw // 3), cap.y + rng.randint(cw // 5, cw // 2)),
                                   rng.randint(3, 7))

    elif kind == "grid":
        hy = area.top + int(area.h * 0.42)
        cx = WIDTH // 2
        blit_glow(surf, (cx, hy - 20), 140, mix(d1, (0, 0, 0), 0.6), 1.0)
        pygame.draw.circle(surf, d1, (cx, hy - 20), 70)
        for k in range(6):
            y = hy - 20 + k * 10
            sky_c = mix(w["sky"][0], w["sky"][1], y / HEIGHT)
            pygame.draw.rect(surf, sky_c, (cx - 75, y, 150, 2 + k))
        floor = mix(w["sky"][1], (0, 0, 0), 0.45)
        pygame.draw.rect(surf, floor, (0, hy, WIDTH, HEIGHT - hy))
        line = mix(d2, floor, 0.55)
        for k in range(14):
            y = hy + int((k / 13) ** 2 * (HEIGHT - hy))
            pygame.draw.line(surf, line, (0, y), (WIDTH, y), 1)
        for i in range(-12, 13):
            pygame.draw.line(surf, line, (cx + i * 18, hy), (cx + i * 150, HEIGHT), 1)
        pygame.draw.line(surf, d2, (0, hy), (WIDTH, hy), 2)

    elif kind == "pillars":
        for x in range(area.left + 40, area.right, 120):
            pw = 34
            pygame.draw.rect(surf, d1, (x, area.top + 40, pw, area.h - 40))
            pygame.draw.rect(surf, d2, (x + pw - 8, area.top + 40, 8, area.h - 40))
            for fx in (x + 8, x + 16):
                pygame.draw.line(surf, d2, (fx, area.top + 54), (fx, area.bottom), 1)
            pygame.draw.rect(surf, d1, (x - 8, area.top + 30, pw + 16, 12))
            pygame.draw.rect(surf, d2, (x - 8, area.top + 40, pw + 16, 3))


# ----- Ambient particles (snow, rain, embers ...) -----
AMB_COUNT = dict(dust=40, snow=80, leaves=28, embers=45, sparkles=35, twinkle=40, bubbles=30, rain=110, fireflies=22)


class Ambient:
    __slots__ = ("x", "y", "vx", "vy", "t", "life", "size", "seed")


# ---------- Particles ----------
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "gravity")

    def __init__(self, x, y, vx, vy, life, color, size, gravity=500):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity

    def update(self, dt):
        self.life -= dt
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return self.life > 0

    def draw(self, surf, ox, oy):
        t = max(0.0, self.life / self.max_life)
        r = max(1, int(self.size * t))
        pygame.draw.circle(surf, self.color, (int(self.x + ox), int(self.y + oy)), r)


# ---------- Player ----------
class Player:
    def __init__(self, x, y):
        self.w = 24
        self.h = 24
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1
        self.squash = 0.0
        self.blink = 0.0
        self.blink_timer = random.uniform(2, 4)

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)


# ---------- Game ----------
class Game:
    def __init__(self):
        self.level_index = 0
        self.deaths = 0
        self.win = False
        self.time = 0.0
        self.shake = 0.0
        self.particles = []
        self.bg = vertical_gradient(WIDTH, HEIGHT, BG_TOP, BG_BOTTOM)
        self.vignette = make_vignette(WIDTH, HEIGHT)
        self.load_level(self.level_index)

    # ----- Level -----
    def load_level(self, idx):
        data = LEVELS[idx]
        self.world = WORLDS[idx % len(WORLDS)]
        self.level_name = data["name"]
        self.map_data = data["map"]
        self.h = len(self.map_data)
        self.w = len(self.map_data[0])
        self.ox = (WIDTH - self.w * TILE) // 2
        self.oy = (HEIGHT - self.h * TILE) // 2 + 10

        self.solids = []
        self.spikes = []
        self.ceil_spikes = []
        self.acids = []
        self.hazards = []
        self.exits = []
        self.keys = []
        self.doors = []
        self.emitters = []   # laser emitter rects (solid)
        self.lasers = []     # dicts: rect, phase, beam
        self.saws = []       # dicts: x, y, dx, dy, angle
        self.crumbles = []   # dicts: rect, state, t
        self.pads = []       # dicts: rect, t
        self.placed = []     # [rect, age]
        spawn = (TILE, TILE)

        for row, line in enumerate(self.map_data):
            for col, ch in enumerate(line):
                r = pygame.Rect(col * TILE, row * TILE, TILE, TILE)
                if ch == "#":
                    self.solids.append(r)
                elif ch == "^":
                    self.spikes.append(r)
                    self.hazards.append(r)
                elif ch == "v":
                    self.ceil_spikes.append(r)
                    self.hazards.append(r)
                elif ch == "~":
                    self.acids.append(r)
                    self.hazards.append(r)
                elif ch == "E":
                    self.exits.append(r)
                elif ch == "K":
                    self.keys.append(r)
                elif ch == "D":
                    self.doors.append(r)
                elif ch == "L":
                    self.emitters.append(r)
                    self.lasers.append({"rect": r, "phase": (col * 0.53) % LASER_PERIOD, "beam": None})
                elif ch == "M":
                    self.saws.append({"x": r.centerx, "y": r.centery, "dx": SAW_SPEED_H, "dy": 0, "angle": 0.0})
                elif ch == "N":
                    self.saws.append({"x": r.centerx, "y": r.centery, "dx": 0, "dy": SAW_SPEED_V, "angle": 0.0})
                elif ch == "C":
                    self.crumbles.append({"rect": r, "state": "solid", "t": 0.0})
                elif ch == "B":
                    self.pads.append({"rect": r, "t": 0.0})
                elif ch == "S":
                    spawn = (col * TILE + 4, row * TILE + 4)

        self.player = Player(*spawn)
        self.spawn = spawn
        self.collected_keys = 0
        self.total_keys = len(self.keys)
        self.door_open = self.total_keys == 0
        self.blocks_used = 0
        self.message_timer = 0.0
        self.message = ""
        self.particles = []
        self.build_static()
        self.ambient = []
        for _ in range(AMB_COUNT.get(self.world["ambient"], 0)):
            a = Ambient()
            self.spawn_ambient(a, initial=True)
            self.ambient.append(a)
        self.set_message(self.world["name"], 2.8, data.get("title", ""))

    def tile_at(self, col, row):
        if 0 <= row < self.h and 0 <= col < self.w:
            return self.map_data[row][col]
        return "#"

    def build_static(self):
        w = self.world
        surf = vertical_gradient(WIDTH, HEIGHT, *w["sky"])
        ox, oy = self.ox, self.oy
        rng = random.Random(self.level_index * 97 + 13)
        area = pygame.Rect(ox, oy, self.w * TILE, self.h * TILE)

        # indoor worlds get a back wall
        if w.get("wall"):
            pygame.draw.rect(surf, w["wall"], area)
            for x in range(area.left, area.right, TILE * 3):
                pygame.draw.line(surf, mix(w["wall"], (255, 255, 255), 0.04), (x, area.top), (x, area.bottom), 2)
            for y in range(area.top, area.bottom, TILE):
                pygame.draw.line(surf, mix(w["wall"], (255, 255, 255), 0.06), (area.left, y), (area.right, y), 1)

        draw_backdrop(surf, w, area, rng)

        # saw tracks
        for s in self.saws:
            col, row = int(s["x"]) // TILE, int(s["y"]) // TILE
            if s["dx"]:
                a = b = col
                while self.tile_at(a - 1, row) not in SOLID_CHARS:
                    a -= 1
                while self.tile_at(b + 1, row) not in SOLID_CHARS:
                    b += 1
                p1 = (a * TILE + 6 + ox, row * TILE + TILE // 2 + oy)
                p2 = ((b + 1) * TILE - 6 + ox, row * TILE + TILE // 2 + oy)
            else:
                a = b = row
                while self.tile_at(col, a - 1) not in SOLID_CHARS:
                    a -= 1
                while self.tile_at(col, b + 1) not in SOLID_CHARS:
                    b += 1
                p1 = (col * TILE + TILE // 2 + ox, a * TILE + 6 + oy)
                p2 = (col * TILE + TILE // 2 + ox, (b + 1) * TILE - 6 + oy)
            pygame.draw.line(surf, (8, 10, 18), p1, p2, 6)
            pygame.draw.line(surf, (44, 52, 72), p1, p2, 2)
            for p in (p1, p2):
                pygame.draw.circle(surf, (44, 52, 72), p, 4)

        # solid tiles
        for r in self.solids:
            col, row = r.x // TILE, r.y // TILE
            top_open = self.tile_at(col, row - 1) not in SOLID_CHARS
            interior = all(
                self.tile_at(col + dx, row + dy) == "#"
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            trng = random.Random(r.x * 7919 + r.y * 104729 + self.level_index)
            TILE_STYLES[w["style"]](surf, r.move(ox, oy), top_open, interior, w, trng)

        # glow on exposed floors
        if w.get("glow"):
            for r in self.solids:
                col, row = r.x // TILE, r.y // TILE
                if row > 0 and self.tile_at(col, row - 1) not in SOLID_CHARS:
                    sr = r.move(ox, oy)
                    blit_glow(surf, (sr.centerx, sr.top), 18, w["glow"], 1.0)

        # spikes
        for r in self.spikes:
            self.draw_spikes(surf, r.move(ox, oy))
        for r in self.ceil_spikes:
            self.draw_spikes(surf, r.move(ox, oy), down=True)

        self.static = surf

    # ----- Ambient -----
    def spawn_ambient(self, a, initial=False):
        kind = self.world["ambient"]
        ww, hh = self.w * TILE, self.h * TILE
        a.x, a.y = random.uniform(0, ww), random.uniform(0, hh)
        a.t, a.life = 0.0, 999.0
        a.seed = random.random() * 10
        a.size = random.uniform(1, 3)
        a.vx = a.vy = 0.0
        if kind == "snow":
            a.vx, a.vy = random.uniform(-15, 5), random.uniform(25, 60)
            if not initial:
                a.y = -5
        elif kind == "leaves":
            a.vx, a.vy, a.size = random.uniform(-20, 10), random.uniform(35, 65), 3
            if not initial:
                a.y = -5
        elif kind == "embers":
            a.vx, a.vy = random.uniform(-10, 10), random.uniform(-60, -25)
            if not initial:
                a.y = hh + 5
        elif kind == "bubbles":
            a.vy, a.size = random.uniform(-45, -20), random.uniform(2, 4.5)
            if not initial:
                a.y = hh + 5
        elif kind == "rain":
            a.vx, a.vy = -70, random.uniform(520, 620)
            if not initial:
                a.y, a.x = -10, random.uniform(0, ww + 60)
        elif kind == "dust":
            a.vx, a.vy, a.life = random.uniform(-8, 8), random.uniform(-6, 6), random.uniform(6, 12)
        elif kind in ("sparkles", "twinkle"):
            a.life = random.uniform(0.8, 2.2)
            a.t = 0.0 if not initial else random.uniform(0, a.life)
        elif kind == "fireflies":
            a.vx, a.vy = random.uniform(-20, 20), random.uniform(-20, 20)

    def update_ambient(self, dt):
        kind = self.world["ambient"]
        ww, hh = self.w * TILE, self.h * TILE
        for a in self.ambient:
            a.t += dt
            a.x += a.vx * dt
            a.y += a.vy * dt
            if kind in ("snow", "leaves", "bubbles"):
                a.x += math.sin(a.t * 2 + a.seed) * 20 * dt
            elif kind == "fireflies":
                a.vx = max(-30, min(30, a.vx + random.uniform(-60, 60) * dt))
                a.vy = max(-30, min(30, a.vy + random.uniform(-60, 60) * dt))
            if a.x < -20 or a.x > ww + 80 or a.y < -20 or a.y > hh + 20 or a.t > a.life:
                self.spawn_ambient(a)

    def draw_ambient(self, surf, ox, oy):
        kind = self.world["ambient"]
        c = self.world["amb"]
        for a in self.ambient:
            x, y = int(a.x + ox), int(a.y + oy)
            if kind == "snow":
                pygame.draw.circle(surf, c, (x, y), int(a.size))
            elif kind == "leaves":
                ang = a.t * 3 + a.seed
                ca, sa = math.cos(ang), math.sin(ang)
                col = mix(c, (200, 60, 20), (a.seed % 1) * 0.7)
                pygame.draw.polygon(surf, col, [(x + ca * 4, y + sa * 4), (x - sa * 2, y + ca * 2),
                                                (x - ca * 4, y - sa * 4), (x + sa * 2, y - ca * 2)])
            elif kind == "embers":
                f = 0.5 + 0.5 * math.sin(a.t * 12 + a.seed)
                blit_glow(surf, (x, y), 6, mix(c, (0, 0, 0), 0.6), 1.0)
                pygame.draw.circle(surf, mix((80, 20, 0), c, f), (x, y), 1 if a.size < 2 else 2)
            elif kind == "bubbles":
                pygame.draw.circle(surf, c, (x, y), int(a.size) + 1, 1)
                pygame.draw.circle(surf, (255, 255, 255), (x - 1, y - 1), 1)
            elif kind == "rain":
                pygame.draw.line(surf, c, (x, y), (x - 1, y + 9), 1)
            elif kind == "dust":
                pygame.draw.circle(surf, mix(c, (0, 0, 0), 0.4), (x, y), 1)
            elif kind in ("sparkles", "twinkle"):
                b = math.sin(math.pi * min(1.0, a.t / a.life))
                s = int(a.size * 2 * b) + 1
                col = mix((0, 0, 0), c, b) if kind == "twinkle" else c
                if b > 0.15:
                    pygame.draw.line(surf, col, (x - s, y), (x + s, y))
                    pygame.draw.line(surf, col, (x, y - s), (x, y + s))
            elif kind == "fireflies":
                b = round(0.5 + 0.5 * math.sin(a.t * 3 + a.seed * 3), 1)
                blit_glow(surf, (x, y), 10, mix((0, 0, 0), c, 0.6 * b + 0.1), 1.0)
                pygame.draw.circle(surf, c, (x, y), 1)

    @staticmethod
    def draw_spikes(surf, r, down=False):
        if down:
            blit_glow(surf, (r.centerx, r.top + 8), 20, (90, 20, 20), 1.0)
            pygame.draw.rect(surf, METAL_DARK, (r.x, r.top, r.w, 6))
            pygame.draw.line(surf, METAL_LIGHT, (r.x, r.top + 5), (r.right - 1, r.top + 5))
            base_y, tip_y, sign = r.top + 6, r.bottom - 8, -1
        else:
            blit_glow(surf, (r.centerx, r.bottom - 8), 20, (90, 20, 20), 1.0)
            pygame.draw.rect(surf, METAL_DARK, (r.x, r.bottom - 6, r.w, 6))
            pygame.draw.line(surf, METAL_LIGHT, (r.x, r.bottom - 6), (r.right - 1, r.bottom - 6))
            base_y, tip_y, sign = r.bottom - 6, r.y + 8, 1
        n = 3
        sw = r.w / n
        for i in range(n):
            x0 = r.x + i * sw
            tip = (x0 + sw / 2, tip_y)
            pygame.draw.polygon(surf, SPIKE_DARK, [(x0 + 1, base_y), tip, (x0 + sw - 1, base_y)])
            pygame.draw.polygon(surf, SPIKE, [(x0 + 1, base_y), tip, (x0 + sw / 2, base_y)])
            pygame.draw.polygon(surf, SPIKE_TIP, [(tip[0] - 2.5, tip_y + 6 * sign), tip, (tip[0] + 2.5, tip_y + 6 * sign)])

    # ----- Helpers -----
    def solid_rects(self):
        rects = self.solids + self.emitters + [b[0] for b in self.placed]
        rects += [c["rect"] for c in self.crumbles if c["state"] != "broken"]
        if not self.door_open:
            rects = rects + self.doors
        return rects

    def set_message(self, text, seconds=1.2, sub=""):
        self.message = text
        self.message_sub = sub
        self.message_timer = seconds

    def burst(self, x, y, color, n, speed=160, life=0.6, size=4, gravity=500, up=False):
        for _ in range(n):
            a = random.uniform(math.pi * 1.1, math.pi * 1.9) if up else random.uniform(0, math.tau)
            sp = random.uniform(speed * 0.3, speed)
            self.particles.append(Particle(
                x, y, math.cos(a) * sp, math.sin(a) * sp,
                random.uniform(life * 0.5, life), color,
                random.uniform(size * 0.5, size), gravity,
            ))

    def respawn(self):
        p = self.player
        self.burst(p.rect.centerx, p.rect.centery, SLIME, 26, speed=260, life=0.8, size=5)
        self.burst(p.rect.centerx, p.rect.centery, SLIME_DARK, 12, speed=180, life=0.7, size=4)
        self.shake = 0.25
        self.deaths += 1
        self.player = Player(*self.spawn)
        self.set_message("Respawn")

    def next_level(self):
        self.level_index += 1
        if self.level_index >= len(LEVELS):
            self.level_index = len(LEVELS) - 1
            self.win = True
            return
        self.load_level(self.level_index)

    def laser_state(self, las):
        t = (self.time + las["phase"]) % LASER_PERIOD
        if t < LASER_ON:
            return "on"
        if t > LASER_PERIOD - LASER_WARN:
            return "warn"
        return "off"

    # ----- Block placing -----
    def cell_free(self, cell):
        groups = (self.solids, self.emitters, self.doors, self.hazards, self.exits, self.keys,
                  [b[0] for b in self.placed], [c["rect"] for c in self.crumbles], [pd["rect"] for pd in self.pads])
        if any(cell.colliderect(r) for g in groups for r in g):
            return False
        return not any(circle_hits_rect(s["x"], s["y"], SAW_R, cell) for s in self.saws)

    def place_target(self):
        """Returns (cell, mode) for where Enter would put a block, or None."""
        p = self.player
        r = p.rect
        col = r.centerx // TILE
        if p.on_ground:
            # Standing: put the block where we are and pop up on top of it
            row = (r.bottom - 1) // TILE
            mode = "pillar"
        else:
            # In the air: put the block right under our feet
            row = (r.bottom + TILE - 1) // TILE
            mode = "below"
        if not (1 <= col < self.w - 1 and 1 <= row < self.h - 1):
            return None
        cell = pygame.Rect(col * TILE, row * TILE, TILE, TILE)
        if not self.cell_free(cell):
            return None
        if mode == "pillar":
            test = pygame.Rect(int(p.x), cell.top - p.h, p.w, p.h)
            if test.top < 0 or any(test.colliderect(b) for b in self.solid_rects()):
                return None
        elif cell.colliderect(r):
            return None
        return cell, mode

    def place_block(self):
        if self.win:
            return
        target = self.place_target()
        if not target:
            self.set_message("Can't place here", 0.6)
            return
        cell, mode = target
        p = self.player
        if mode == "pillar":
            p.y = cell.top - p.h
            p.vy = 0
            p.squash = -0.35
        self.placed.append([cell, 0.0])
        self.blocks_used += 1
        self.burst(cell.centerx, cell.centery, BLOCK, 14, speed=150, life=0.45, size=4, gravity=250)
        self.burst(cell.centerx, cell.centery, BLOCK_LIGHT, 6, speed=90, life=0.35, size=3, gravity=0)

    # ----- Obstacles -----
    def update_crumbles(self, dt):
        p = self.player
        feet = p.rect.move(0, 1)
        for c in self.crumbles:
            if c["state"] == "solid":
                if p.on_ground and feet.colliderect(c["rect"]):
                    c["state"] = "shaking"
                    c["t"] = CRUMBLE_DELAY
            elif c["state"] == "shaking":
                c["t"] -= dt
                if c["t"] <= 0:
                    c["state"] = "broken"
                    c["t"] = CRUMBLE_RESPAWN
                    r = c["rect"]
                    self.burst(r.centerx, r.centery, CRUMBLE, 12, speed=120, life=0.6, size=4, gravity=700)
                    self.burst(r.centerx, r.centery, CRUMBLE_DARK, 6, speed=90, life=0.5, size=3, gravity=700)
            else:
                c["t"] -= dt
                blocked = p.rect.colliderect(c["rect"]) or any(
                    circle_hits_rect(s["x"], s["y"], SAW_R, c["rect"]) for s in self.saws)
                if c["t"] <= 0 and not blocked:
                    c["state"] = "solid"

    def update_pads(self, dt):
        p = self.player
        for pad in self.pads:
            pad["t"] = max(0.0, pad["t"] - dt)
            r = pad["rect"]
            hit = pygame.Rect(r.x + 4, r.bottom - 10, r.w - 8, 10)
            if p.vy >= 0 and p.rect.colliderect(hit):
                p.vy = PAD_POWER
                p.on_ground = False
                p.squash = -0.6
                pad["t"] = 0.25
                self.burst(r.centerx, r.bottom - 10, PAD, 14, speed=180, life=0.5, size=3, gravity=300, up=True)

    def update_saws(self, dt):
        solids = self.solid_rects()
        for s in self.saws:
            s["angle"] += dt * 9
            nx, ny = s["x"] + s["dx"] * dt, s["y"] + s["dy"] * dt
            box = pygame.Rect(0, 0, SAW_R * 2, SAW_R * 2)
            box.center = (int(nx), int(ny))
            if any(box.colliderect(b) for b in solids):
                s["dx"], s["dy"] = -s["dx"], -s["dy"]
            else:
                s["x"], s["y"] = nx, ny

    def update_lasers(self):
        solids = self.solid_rects()
        cells = {(b.x // TILE, b.y // TILE) for b in solids}
        bottom = self.h * TILE
        for las in self.lasers:
            e = las["rect"]
            col = e.x // TILE
            end = bottom
            for row in range(e.bottom // TILE, self.h):
                if (col, row) in cells:
                    end = row * TILE
                    break
            las["beam"] = pygame.Rect(e.centerx - 3, e.bottom, 6, max(0, end - e.bottom))
            las["state"] = self.laser_state(las)

    # ----- Update -----
    def update(self, dt, keys_pressed):
        self.time += dt
        self.shake = max(0.0, self.shake - dt)
        self.particles = [pt for pt in self.particles if pt.update(dt)]
        self.update_ambient(dt)
        for b in self.placed:
            b[1] += dt

        if self.win:
            if random.random() < dt * 20:
                self.burst(random.uniform(0, self.w * TILE), -10, random.choice([SLIME, KEY, BLOCK, EXIT]),
                           1, speed=60, life=2.5, size=4, gravity=120)
            return

        p = self.player
        speed = 230
        gravity = 1650

        p.squash *= max(0.0, 1 - dt * 12)
        p.blink = max(0.0, p.blink - dt)
        p.blink_timer -= dt
        if p.blink_timer <= 0:
            p.blink = 0.12
            p.blink_timer = random.uniform(2, 5)

        move = 0
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            move -= 1
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            move += 1

        p.vx = move * speed
        if move != 0:
            p.facing = 1 if move > 0 else -1

        p.vy += gravity * dt
        if p.vy > 900:
            p.vy = 900

        was_on_ground = p.on_ground
        fall_speed = p.vy
        p.on_ground = False

        solids = self.solid_rects()
        p.x += p.vx * dt
        rect = p.rect
        for block in solids:
            if rect.colliderect(block):
                if p.vx > 0:
                    rect.right = block.left
                elif p.vx < 0:
                    rect.left = block.right
                p.x = rect.x

        p.y += p.vy * dt
        rect = p.rect
        for block in solids:
            if rect.colliderect(block):
                if p.vy > 0:
                    rect.bottom = block.top
                    p.on_ground = True
                elif p.vy < 0:
                    rect.top = block.bottom
                p.vy = 0
                p.y = rect.y

        # landing effects
        if p.on_ground and not was_on_ground and fall_speed > 250:
            p.squash = min(0.6, fall_speed / 1400)
            self.burst(p.rect.centerx, p.rect.bottom, (130, 150, 180), 8, speed=110, life=0.35, size=3, up=True)

        # walking dust
        if p.on_ground and move != 0 and random.random() < dt * 12:
            self.particles.append(Particle(p.rect.centerx - p.facing * 10, p.rect.bottom - 1,
                                           -p.facing * random.uniform(20, 60), random.uniform(-40, -10),
                                           0.35, (110, 130, 160), 2.5, 0))

        self.update_crumbles(dt)
        self.update_pads(dt)
        self.update_saws(dt)
        self.update_lasers()

        # deadly stuff
        pr = p.rect
        dead = any(pr.colliderect(h.inflate(-6, -8)) for h in self.hazards)
        dead = dead or any(circle_hits_rect(s["x"], s["y"], SAW_R - 1, pr) for s in self.saws)
        dead = dead or any(l["state"] == "on" and pr.colliderect(l["beam"]) for l in self.lasers)
        if dead or p.y > self.h * TILE + 100:
            self.respawn()
            return

        for k in self.keys[:]:
            if p.rect.colliderect(k):
                self.keys.remove(k)
                self.collected_keys += 1
                self.burst(k.centerx, k.centery, KEY, 22, speed=220, life=0.6, size=4, gravity=200)
                if self.collected_keys >= self.total_keys:
                    self.door_open = True
                    self.shake = 0.12
                    for d in self.doors:
                        self.burst(d.centerx, d.centery, DOOR, 8, speed=140, life=0.5, size=3, gravity=150)
                    self.set_message("Door Open")
                else:
                    self.set_message("Key Collected")

        if self.door_open:
            for e in self.exits:
                if random.random() < dt * 10:
                    self.particles.append(Particle(random.uniform(e.left + 6, e.right - 6), e.bottom - 4,
                                                   0, random.uniform(-70, -30), 0.8, EXIT, 2.5, 0))

        touching_exit = any(p.rect.colliderect(e) for e in self.exits)
        if touching_exit:
            if self.door_open:
                self.next_level()
                return
            self.set_message("Need all keys")

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""

    def jump(self):
        if self.win:
            return
        p = self.player
        if p.on_ground:
            p.vy = -610
            p.squash = -0.45
            self.burst(p.rect.centerx, p.rect.bottom, (130, 150, 180), 6, speed=90, life=0.3, size=3, up=True)

    # ----- Drawing -----
    def draw_player(self, surf, ox, oy):
        p = self.player
        r = p.rect.move(ox, oy)

        sx, sy = 1.0, 1.0
        if not p.on_ground:
            k = min(1.0, abs(p.vy) / 600)
            sx, sy = 1 - 0.12 * k, 1 + 0.15 * k
        elif abs(p.vx) > 20:
            wob = math.sin(self.time * 18) * 0.06
            sx, sy = 1.06 + wob, 0.94 - wob
        sx += p.squash * 0.35
        sy -= p.squash * 0.35

        w = max(8, int(r.width * sx))
        h = max(8, int(r.height * sy))
        body = pygame.Rect(0, 0, w, h)
        body.midbottom = r.midbottom

        blit_glow(surf, body.center, 30, (25, 90, 60), 1.0)

        if p.on_ground:
            sh = pygame.Surface((w + 6, 6), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 90), sh.get_rect())
            surf.blit(sh, (body.centerx - (w + 6) // 2, body.bottom - 3))

        pygame.draw.ellipse(surf, SLIME_DARK, body)
        inner = body.inflate(-4, -4)
        pygame.draw.ellipse(surf, SLIME, inner)
        hl = pygame.Rect(0, 0, max(4, w // 3), max(3, h // 4))
        hl.topleft = (inner.x + 3, inner.y + 2)
        pygame.draw.ellipse(surf, SLIME_LIGHT, hl)

        look = p.facing * 2
        eye_y = body.y + int(h * 0.42)
        pupil_dy = 1 if p.vy > 120 else (-1 if p.vy < -120 else 0)
        for ex in (body.centerx - w // 5 + look, body.centerx + w // 5 + look):
            if p.blink > 0:
                pygame.draw.line(surf, (20, 70, 45), (ex - 3, eye_y), (ex + 3, eye_y), 2)
            else:
                pygame.draw.circle(surf, WHITE, (ex, eye_y), 4)
                pygame.draw.circle(surf, (18, 26, 38), (ex + p.facing, eye_y + pupil_dy), 2)

    def draw_obstacles(self, surf, ox, oy):
        t = self.time

        # laser beams
        for las in self.lasers:
            beam = las.get("beam")
            state = las.get("state", "off")
            if not beam or beam.h <= 0:
                continue
            b = beam.move(ox, oy)
            if state == "on":
                for w, c in ((20, (60, 8, 8)), (10, (140, 25, 25)), (4, (255, 120, 120))):
                    rr = pygame.Rect(0, 0, w, b.h)
                    rr.midtop = (b.centerx, b.top)
                    surf.fill(c, rr, special_flags=pygame.BLEND_ADD)
                pygame.draw.line(surf, (255, 235, 235), (b.centerx, b.top), (b.centerx, b.bottom - 1), 1)
                blit_glow(surf, (b.centerx, b.bottom), 18, (220, 50, 50), 1.0)
                if random.random() < 0.3:
                    self.particles.append(Particle(b.centerx + ox * 0 - ox, b.bottom - oy - 2,
                                                   random.uniform(-80, 80), random.uniform(-120, -40),
                                                   0.25, (255, 150, 120), 2, 600))
            elif state == "warn" and int(t * 18) % 2 == 0:
                pygame.draw.line(surf, (200, 60, 60), (b.centerx, b.top), (b.centerx, b.bottom - 1), 1)

        # laser emitters
        for las in self.lasers:
            r = las["rect"].move(ox, oy)
            state = las.get("state", "off")
            pygame.draw.rect(surf, METAL_EDGE, r)
            body = pygame.Rect(r.x + 3, r.y, r.w - 6, r.h - 4)
            pygame.draw.rect(surf, METAL, body, border_bottom_left_radius=8, border_bottom_right_radius=8)
            pygame.draw.rect(surf, METAL_LIGHT, body, 1, border_bottom_left_radius=8, border_bottom_right_radius=8)
            pygame.draw.line(surf, METAL_DARK, (body.x + 4, body.y + 8), (body.right - 5, body.y + 8), 2)
            lens = (r.centerx, r.bottom - 9)
            if state == "on":
                color = (255, 90, 90)
                blit_glow(surf, lens, 18, (180, 30, 30), 1.0)
            elif state == "warn":
                color = (255, 170, 70) if int(t * 18) % 2 == 0 else (120, 60, 40)
                blit_glow(surf, lens, 12, (120, 60, 20), 1.0)
            else:
                color = (90, 40, 45)
            pygame.draw.circle(surf, (24, 18, 24), lens, 6)
            pygame.draw.circle(surf, color, lens, 4)

        # crumbling platforms
        for c in self.crumbles:
            r = c["rect"].move(ox, oy)
            if c["state"] == "broken":
                pygame.draw.rect(surf, (60, 48, 40), r, 1, border_radius=3)
                continue
            if c["state"] == "shaking":
                r = r.move(random.randint(-1, 1), random.randint(-1, 1))
            pygame.draw.rect(surf, CRUMBLE_DARK, r, border_radius=3)
            inner = r.inflate(-4, -4)
            pygame.draw.rect(surf, CRUMBLE, inner, border_radius=3)
            pygame.draw.line(surf, CRUMBLE_LIGHT, (inner.x + 2, inner.y), (inner.right - 3, inner.y), 2)
            crack = (70, 50, 38)
            pygame.draw.lines(surf, crack, False, [(inner.x + 6, inner.y + 4), (inner.x + 12, inner.y + 12),
                                                   (inner.x + 9, inner.bottom - 4)], 2)
            pygame.draw.lines(surf, crack, False, [(inner.right - 5, inner.y + 6), (inner.right - 11, inner.y + 14),
                                                   (inner.right - 7, inner.bottom - 6)], 1)
            if c["state"] == "shaking":
                pygame.draw.line(surf, (255, 200, 140), (inner.x + 3, inner.centery), (inner.right - 4, inner.centery + 3), 1)

        # bounce pads
        for pad in self.pads:
            r = pad["rect"].move(ox, oy)
            ext = pad["t"] / 0.25
            spring_h = 8 + int(8 * ext)
            base = pygame.Rect(r.x + 3, r.bottom - 5, r.w - 6, 5)
            pygame.draw.rect(surf, METAL_DARK, base, border_radius=2)
            pygame.draw.line(surf, METAL_LIGHT, base.topleft, (base.right - 1, base.top))
            pts = []
            for i in range(5):
                y = base.top - i * spring_h / 4
                x = r.centerx + (-6 if i % 2 else 6)
                pts.append((x, y))
            pygame.draw.lines(surf, (190, 200, 215), False, pts, 2)
            plate = pygame.Rect(r.x + 3, int(base.top - spring_h - 5), r.w - 6, 5)
            blit_glow(surf, plate.center, 22, (120, 30, 80), 0.8 + 0.2 * math.sin(t * 6))
            pygame.draw.rect(surf, PAD, plate, border_radius=2)
            pygame.draw.line(surf, (255, 200, 230), (plate.x + 2, plate.y), (plate.right - 3, plate.y))

        # saws
        for s in self.saws:
            cx, cy = s["x"] + ox, s["y"] + oy
            blit_glow(surf, (cx, cy), 26, (90, 20, 20), 0.8)
            pts = []
            for i in range(16):
                a = s["angle"] + i * math.pi / 8
                rad = SAW_R + 2 if i % 2 == 0 else SAW_R - 3
                pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
            pygame.draw.polygon(surf, SAW, pts)
            pygame.draw.polygon(surf, (225, 232, 245), pts, 1)
            pygame.draw.circle(surf, (90, 98, 115), (int(cx), int(cy)), 7)
            pygame.draw.circle(surf, (235, 70, 70), (int(cx), int(cy)), 3)

    def draw_world_objects(self, surf, ox, oy):
        t = self.time

        # exits
        for e in self.exits:
            r = e.move(ox, oy)
            if self.door_open:
                pulse = 0.7 + 0.3 * math.sin(t * 4)
                blit_glow(surf, r.center, 52, EXIT, pulse)
                pygame.draw.rect(surf, (12, 50, 30), r, border_radius=6)
                inner = r.inflate(-8, -8)
                for i in range(4):
                    yy = inner.bottom - ((t * 30 + i * 7) % inner.h)
                    pygame.draw.line(surf, (120, 255, 170), (inner.left + 2, yy), (inner.right - 3, yy), 1)
                pygame.draw.rect(surf, EXIT, r, 3, border_radius=6)
                pygame.draw.rect(surf, (210, 255, 225), r, 1, border_radius=6)
            else:
                pygame.draw.rect(surf, (30, 24, 34), r, border_radius=6)
                pygame.draw.rect(surf, EXIT_LOCKED, r, 3, border_radius=6)
                cx, cy = r.center
                pygame.draw.circle(surf, (200, 170, 180), (cx, cy - 3), 5, 2)
                pygame.draw.rect(surf, (200, 170, 180), (cx - 6, cy - 1, 12, 9), border_radius=2)

        # doors
        for d in self.doors:
            r = d.move(ox, oy)
            if self.door_open:
                pygame.draw.rect(surf, (60, 46, 30), (r.x + 4, r.y, 3, r.h))
                pygame.draw.rect(surf, (60, 46, 30), (r.right - 7, r.y, 3, r.h))
                continue
            flick = 0.6 + 0.4 * math.sin(t * 10 + r.y * 0.3)
            blit_glow(surf, r.center, 30, (120, 70, 20), 1.0)
            pygame.draw.rect(surf, (44, 30, 18), r)
            beam = (int(235 * flick), int(155 * flick), int(55 * flick))
            pygame.draw.rect(surf, beam, r.inflate(-14, 0))
            pygame.draw.line(surf, (255, 230, 170), (r.centerx, r.top), (r.centerx, r.bottom - 1), 1)
            pygame.draw.rect(surf, DOOR, (r.x + 3, r.y, 5, r.h))
            pygame.draw.rect(surf, DOOR, (r.right - 8, r.y, 5, r.h))

        # keys
        for k in self.keys:
            bob = math.sin(t * 3 + k.x * 0.1) * 3
            cx, cy = k.centerx + ox, int(k.centery + oy + bob)
            blit_glow(surf, (cx, cy), 32, (150, 115, 20), 0.8 + 0.2 * math.sin(t * 5))
            pygame.draw.circle(surf, KEY, (cx - 6, cy), 6, 3)
            pygame.draw.rect(surf, KEY, (cx - 1, cy - 2, 12, 4))
            pygame.draw.rect(surf, KEY, (cx + 6, cy + 1, 2, 5))
            pygame.draw.rect(surf, KEY, (cx + 9, cy + 1, 2, 4))
            pygame.draw.circle(surf, (255, 250, 210), (cx - 8, cy - 2), 1)

        # liquid (acid / lava / poison depending on the world)
        liq_main, liq_dark, liq_light, liq_glow = self.world["liquid"]
        for a in self.acids:
            r = a.move(ox, oy)
            blit_glow(surf, r.center, 30, liq_glow, 1.0)
            pts = [(r.left, r.bottom)]
            for i in range(0, TILE + 1, 4):
                pts.append((r.left + i, r.top + 9 + math.sin(t * 4 + (a.x + i) * 0.2) * 2.5))
            pts.append((r.right, r.bottom))
            pygame.draw.polygon(surf, liq_dark, pts)
            pygame.draw.polygon(surf, liq_main, [(x, y + 3) for x, y in pts[1:-1]] + [(r.right, r.bottom - 4), (r.left, r.bottom - 4)])
            pygame.draw.lines(surf, liq_light, False, pts[1:-1], 2)
            for j in range(2):
                phase = (t * 0.7 + j * 0.5 + a.x * 0.013) % 1
                bx = r.left + 9 + j * 14
                by = int(r.bottom - 6 - phase * (TILE - 16))
                pygame.draw.circle(surf, liq_light, (bx, by), 2, 1)
            pygame.draw.rect(surf, METAL_DARK, (r.x, r.bottom - 4, r.w, 4))

        # placed blocks
        for cell, age in self.placed:
            r = cell.move(ox, oy)
            s = min(1.0, age / 0.15)
            scale = 0.6 + 0.4 * (1 - (1 - s) ** 3)
            rr = pygame.Rect(0, 0, int(TILE * scale), int(TILE * scale))
            rr.center = r.center
            blit_glow(surf, rr.center, 28, (12, 60, 70), 1.0)
            pygame.draw.rect(surf, BLOCK_DARK, rr, border_radius=5)
            inner = rr.inflate(-6, -6)
            pygame.draw.rect(surf, BLOCK, inner, border_radius=4)
            pygame.draw.rect(surf, BLOCK_LIGHT, (inner.x + 3, inner.y + 2, max(1, inner.w - 6), 3), border_radius=2)
            c = inner.center
            d = max(2, inner.w // 6)
            pygame.draw.polygon(surf, BLOCK_LIGHT, [(c[0], c[1] - d), (c[0] + d, c[1]), (c[0], c[1] + d), (c[0] - d, c[1])])

    def draw_place_preview(self, surf, ox, oy):
        if self.win:
            return
        target = self.place_target()
        if not target:
            return
        cell = target[0].move(ox, oy)
        a = int(70 + 40 * math.sin(self.time * 6))
        ghost = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(ghost, (*BLOCK, a // 3), ghost.get_rect(), border_radius=5)
        pygame.draw.rect(ghost, (*BLOCK, a + 60), ghost.get_rect(), 2, border_radius=5)
        surf.blit(ghost, cell.topleft)

    def draw_hud(self, surf):
        panel = pygame.Surface((WIDTH - 16, 40), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 12, 22, 200), panel.get_rect(), border_radius=10)
        pygame.draw.rect(panel, (90, 200, 235, 80), panel.get_rect(), 1, border_radius=10)
        surf.blit(panel, (8, 6))

        x = 24
        label = f"{self.level_index + 1}/{len(LEVELS)}  {self.world['name'].upper()}"
        x += text_with_shadow(surf, small_font, label, mix(self.world["top"], (255, 255, 255), 0.35), (x, 15)) + 30
        items = [
            (f"Keys  {self.collected_keys}/{self.total_keys}", KEY),
            (f"Deaths  {self.deaths}", (240, 120, 120)),
            (f"Blocks  {self.blocks_used}", BLOCK),
        ]
        for text, color in items:
            pygame.draw.circle(surf, color, (x + 5, 26), 5)
            x += 16
            x += text_with_shadow(surf, small_font, text, WHITE, (x, 15)) + 30

        hint = "A/D or Arrows: move  |  Space/Up: jump  |  Enter: place block  |  R: restart"
        hs = hint_font.render(hint, True, WHITE)
        band = pygame.Surface((hs.get_width() + 28, 26), pygame.SRCALPHA)
        pygame.draw.rect(band, (8, 12, 22, 150), band.get_rect(), border_radius=13)
        surf.blit(band, (WIDTH // 2 - band.get_width() // 2, HEIGHT - 30))
        text_with_shadow(surf, hint_font, hint, (190, 210, 240), (WIDTH // 2, HEIGHT - 27), center=True)

        if self.message:
            alpha = int(min(255, self.message_timer * 500))
            text_with_shadow(surf, font, self.message, WHITE, (WIDTH // 2, 54), center=True, alpha=alpha)
            if self.message_sub:
                text_with_shadow(surf, small_font, self.message_sub, (215, 228, 248), (WIDTH // 2, 88),
                                 center=True, alpha=alpha)

    def draw(self, surf):
        sx = sy = 0
        if self.shake > 0:
            amt = int(self.shake * 30)
            sx, sy = random.randint(-amt, amt), random.randint(-amt, amt)
        ox, oy = self.ox + sx, self.oy + sy

        surf.fill(BG_TOP)
        surf.blit(self.static, (sx, sy))
        self.draw_world_objects(surf, ox, oy)
        self.draw_obstacles(surf, ox, oy)
        self.draw_place_preview(surf, ox, oy)
        if not self.win:
            self.draw_player(surf, ox, oy)
        for pt in self.particles:
            pt.draw(surf, ox, oy)
        self.draw_ambient(surf, ox, oy)

        surf.blit(self.vignette, (0, 0))
        self.draw_hud(surf)

        if self.win:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surf.blit(overlay, (0, 0))
            box = pygame.Rect(0, 0, 440, 200)
            box.center = (WIDTH // 2, HEIGHT // 2)
            panel = pygame.Surface(box.size, pygame.SRCALPHA)
            pygame.draw.rect(panel, (10, 16, 28, 230), panel.get_rect(), border_radius=16)
            pygame.draw.rect(panel, (*EXIT, 180), panel.get_rect(), 2, border_radius=16)
            surf.blit(panel, box.topleft)
            text_with_shadow(surf, big_font, "Lab Cleared!", EXIT, (WIDTH // 2, box.y + 28), center=True)
            text_with_shadow(surf, small_font, f"Total deaths: {self.deaths}", (210, 230, 255),
                             (WIDTH // 2, box.y + 100), center=True)
            text_with_shadow(surf, small_font, "Press R to play again or ESC to quit", (170, 195, 230),
                             (WIDTH // 2, box.y + 134), center=True)


def main():
    game = Game()

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 1 / 30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    if game.win:
                        game = Game()
                    else:
                        game.load_level(game.level_index)
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    game.jump()
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    game.place_block()

        keys_pressed = pygame.key.get_pressed()
        game.update(dt, keys_pressed)
        game.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main() 