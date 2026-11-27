# -*- coding: utf-8 -*-
"""
PyCraft - מיינקרפט בפייתון
=========================
התקנה:   pip install ursina
הרצה:    python pycraft.py

שליטה:
  W A S D       - תנועה
  רווח          - קפיצה / שחייה למעלה / טיסה למעלה
  Shift שמאלי   - ריצה (בטיסה: ירידה)
  עכבר          - הסתכלות
  לחיצה שמאלית  - שבירת בלוק (להחזיק). מכוש שובר הכול חוץ מיהלום. מכוש ברזל - במכה אחת
  לחיצה ימנית   - הנחת בלוק
  1-9 / גלגלת   - בחירת בלוק
  F             - מצב טיסה
  R             - חזרה לנקודת ההתחלה
  Esc           - שחרור העכבר  (לחיצה על המסך מחזירה)
  Q             - יציאה (המשחק נשמר אוטומטית)
  F5            - שמירה
  E             - מלאי + רשת יצירה 3x3
  G             - מצב יצירתי (כרייה מיידית, בלוקים לא נגמרים, מפלצות לא תוקפות)

מפלצות במערות: חיפושית מערות, גב-סלע ועין קריסטל (יורה רסיסים).
חרב הורגת אותן במכה אחת. יש לך 10 לבבות, והם מתמלאים לאט.

יצירה (Crafting):
  לוחצים E. גוררים חפצים לרשת היצירה, והתוצאה מופיעה בצד ימין - לוחצים עליה כדי לקחת.
  Shift + לחיצה על התוצאה = לייצר כמה שאפשר.
  4 קרשים בריבוע = שולחן יצירה. מניחים אותו ולוחצים עליו קליק ימני = רשת 3x3.
  Crafter: בלוק שמייצר לבד כל 2 שניות מהמתכון שמונח בו.

מתחת לנקודת ההתחלה יש תמיד מערה! המדרגות שליד נקודת ההתחלה יורדות אליה.

פורטל לנדר: מסגרת אובסידיאן סגולה ליד נקודת ההתחלה. נכנסים לחלק הסגול ונשארים בו שנייה.
בנדר יש ים לבה (נוגעים = נשרפים), אבני זוהר, קוורץ וזהב. הפורטל שם מחזיר הביתה.

חיות: חזירים, פרות, כבשים ותרנגולות. לחיצה שמאלית מכה בהן.
מתחת לאדמה: מערות עם פחם, ברזל, זהב ויהלומים (יהלומים רק בעומק, מתחת לגובה 12).
"""
import math
import os
import pickle
import zlib
import atexit
import datetime
import random
from ursina import (Ursina, Entity, Mesh, Texture, Vec3, Vec4, Text, Sky, destroy, invoke, Button,
                    camera, mouse, held_keys, time, scene, window, application, color)
from ursina.shaders import unlit_shader
from PIL import Image, ImageDraw
from panda3d.core import Texture as PandaTexture, SamplerState, TransparencyAttrib


def make_texture(img):
    """יוצר טקסטורה ישירות ב-Panda3D (עובד בכל גרסה של ursina)."""
    img = img.convert('RGBA').transpose(Image.FLIP_TOP_BOTTOM)
    pt = PandaTexture('tex')
    pt.setup2dTexture(img.width, img.height, PandaTexture.T_unsigned_byte, PandaTexture.F_rgba8)
    pt.setRamImageAs(img.tobytes(), 'RGBA')
    pt.setMagfilter(SamplerState.FT_nearest)
    pt.setMinfilter(SamplerState.FT_nearest)
    pt.setWrapU(SamplerState.WM_clamp)
    pt.setWrapV(SamplerState.WM_clamp)
    return Texture(pt)

# ---------------------------------------------------------------- הגדרות
SEED = random.randint(0, 999_999)       # עולם חדש בכל הרצה
_trng = random.Random(SEED)
TERRAIN_SCALE = _trng.uniform(36, 70)     # כמה רחבות הגבעות
TERRAIN_AMP = _trng.uniform(42, 72)       # כמה גבוהים ההרים
TERRAIN_SHIFT = _trng.uniform(-0.06, 0.1)  # יותר ים או יותר יבשה
TREE_CHANCE = _trng.uniform(0.006, 0.025)  # כמה עצים


def set_seed(seed):
    """קובע את מספר העולם. אותו מספר = בדיוק אותו עולם."""
    global SEED, TERRAIN_SCALE, TERRAIN_AMP, TERRAIN_SHIFT, TREE_CHANCE
    SEED = seed
    r = random.Random(seed)
    TERRAIN_SCALE = r.uniform(36, 70)
    TERRAIN_AMP = r.uniform(42, 72)
    TERRAIN_SHIFT = r.uniform(-0.06, 0.1)
    TREE_CHANCE = r.uniform(0.006, 0.025)


# ---------------------------------------------------------------- שמירה
# שומרים רק את מספר העולם ואת מה שהשחקן שינה בו, כך שהקובץ קטן ומהיר
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pycraft_saves')
CHANGES = {}            # עולם -> {מיקום: בלוק} - כל בלוק ששברת או הנחת
LOADED = [None]         # נתוני השמירה שממשיכים ממנה


def save_path(seed):
    return os.path.join(SAVE_DIR, f'world_{seed}.dat')


def list_saves():
    out = []
    if os.path.isdir(SAVE_DIR):
        for name in os.listdir(SAVE_DIR):
            if name.startswith('world_') and name.endswith('.dat'):
                path = os.path.join(SAVE_DIR, name)
                try:
                    with open(path, 'rb') as fh:
                        data = pickle.loads(zlib.decompress(fh.read()))
                    out.append((os.path.getmtime(path), data))
                except Exception:
                    pass
    out.sort(key=lambda t: -t[0])
    return [d for _, d in out]
CHUNK = 16
WORLD_CHUNKS = 6          # העולם הוא 6x6 צ'אנקים = 96x96 בלוקים
SEA = 24                  # העולם עמוק יותר - יש מקום למערות גם מתחת לים
SNOW_LINE = SEA + 18
REACH = 6
MOUSE_SENS = 40

# ---------------------------------------------------------------- בלוקים
AIR, GRASS, DIRT, STONE, COBBLE, LOG, PLANKS, LEAVES, SAND, SNOW, WATER, BEDROCK, BRICK, \
    COAL_ORE, IRON_ORE, GOLD_ORE, DIAMOND_ORE, \
    NETHERRACK, LAVA, GLOWSTONE, SOUL_SAND, QUARTZ_ORE, NETHER_GOLD, OBSIDIAN, PORTAL, \
    CRAFTING_TABLE, CRAFTER, TORCH, IRON_BLOCK, GOLD_BLOCK, DIAMOND_BLOCK, COAL_BLOCK, QUARTZ_BLOCK, \
    SANDSTONE = range(34)

NAMES = {GRASS: 'Grass', DIRT: 'Dirt', STONE: 'Stone', COBBLE: 'Cobblestone', LOG: 'Oak Log',
         PLANKS: 'Oak Planks', LEAVES: 'Leaves', SAND: 'Sand', SNOW: 'Snow', WATER: 'Water',
         BEDROCK: 'Bedrock', BRICK: 'Bricks', COAL_ORE: 'Coal Ore', IRON_ORE: 'Iron Ore',
         GOLD_ORE: 'Gold Ore', DIAMOND_ORE: 'Diamond Ore', NETHERRACK: 'Netherrack', LAVA: 'Lava',
         GLOWSTONE: 'Glowstone', SOUL_SAND: 'Soul Sand', QUARTZ_ORE: 'Quartz Ore',
         NETHER_GOLD: 'Nether Gold Ore', OBSIDIAN: 'Obsidian', PORTAL: 'Portal',
         CRAFTING_TABLE: 'Crafting Table', CRAFTER: 'Crafter', TORCH: 'Torch',
         IRON_BLOCK: 'Block of Iron', GOLD_BLOCK: 'Block of Gold', DIAMOND_BLOCK: 'Block of Diamond',
         COAL_BLOCK: 'Block of Coal', QUARTZ_BLOCK: 'Block of Quartz', SANDSTONE: 'Sandstone'}
HOTBAR = [GRASS, DIRT, STONE, COBBLE, LOG, PLANKS, LEAVES, SAND, BRICK]


NONSOLID = {AIR, WATER, LAVA, PORTAL, TORCH}
FLUIDLIKE = {WATER, LAVA, PORTAL}      # מצוירים רק מול אוויר
TRANSPARENT = {WATER: 0.72, PORTAL: 0.65}
GLOW = {LAVA, GLOWSTONE, PORTAL}       # בלוקים שזוהרים (בלי הצללה)


def is_solid(b):
    return b not in NONSOLID


# ---------------------------------------------------------------- טקסטורות (נוצרות בקוד, 16x16 פיקסלים)
def _clamp(v):
    return max(0, min(255, int(v)))


def tile_noise(base, var, rng):
    img = Image.new('RGB', (16, 16))
    px = img.load()
    for y in range(16):
        for x in range(16):
            f = 1 + rng.uniform(-var, var)
            px[x, y] = tuple(_clamp(c * f) for c in base)
    return img


def make_tiles():
    rng = random.Random(1234)
    t = {}
    t['grass_top'] = tile_noise((95, 159, 53), 0.18, rng)
    t['dirt'] = tile_noise((134, 96, 67), 0.18, rng)

    side = t['dirt'].copy()
    px = side.load()
    for x in range(16):
        depth = 3 + (1 if rng.random() < 0.5 else 0) + (1 if rng.random() < 0.2 else 0)
        for y in range(depth):
            f = 1 + rng.uniform(-0.15, 0.15)
            px[x, y] = (_clamp(95 * f), _clamp(159 * f), _clamp(53 * f))
    t['grass_side'] = side

    t['stone'] = tile_noise((125, 125, 125), 0.13, rng)

    cob = tile_noise((120, 120, 120), 0.22, rng)
    px = cob.load()
    for y in range(16):
        for x in range(16):
            if y % 5 == 0 or (x + (y // 5) * 3) % 6 == 0:
                px[x, y] = (70, 70, 70)
    t['cobble'] = cob

    log = Image.new('RGB', (16, 16))
    px = log.load()
    stripes = [rng.uniform(0.75, 1.15) for _ in range(16)]
    for y in range(16):
        for x in range(16):
            f = stripes[x] * (1 + rng.uniform(-0.06, 0.06))
            px[x, y] = (_clamp(104 * f), _clamp(80 * f), _clamp(48 * f))
    t['log_side'] = log

    top = Image.new('RGB', (16, 16))
    px = top.load()
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d > 7:
                px[x, y] = (104, 80, 48)
            else:
                f = 0.85 + 0.2 * (int(d) % 2) + rng.uniform(-0.05, 0.05)
                px[x, y] = (_clamp(176 * f), _clamp(142 * f), _clamp(88 * f))
    t['log_top'] = top

    pl = tile_noise((176, 138, 84), 0.07, rng)
    px = pl.load()
    for y in range(16):
        for x in range(16):
            if y % 4 == 3 or (x == (0 if (y // 4) % 2 else 8)):
                px[x, y] = (120, 92, 54)
    t['planks'] = pl

    lv = Image.new('RGB', (16, 16))
    px = lv.load()
    for y in range(16):
        for x in range(16):
            r = rng.random()
            if r < 0.18:
                px[x, y] = (30, 70, 25)
            else:
                f = rng.uniform(0.75, 1.2)
                px[x, y] = (_clamp(60 * f), _clamp(130 * f), _clamp(42 * f))
    t['leaves'] = lv

    t['sand'] = tile_noise((219, 207, 163), 0.06, rng)
    t['snow'] = tile_noise((240, 245, 252), 0.03, rng)
    t['water'] = tile_noise((50, 95, 210), 0.08, rng)
    t['bedrock'] = tile_noise((75, 75, 75), 0.55, rng)

    br = Image.new('RGB', (16, 16))
    px = br.load()
    for y in range(16):
        for x in range(16):
            offset = 0 if (y // 4) % 2 == 0 else 4
            if y % 4 == 3 or (x + offset) % 8 == 7:
                px[x, y] = (180, 175, 165)
            else:
                f = 1 + rng.uniform(-0.12, 0.12)
                px[x, y] = (_clamp(150 * f), _clamp(70 * f), _clamp(55 * f))
    t['brick'] = br

    def ore(dot, base='stone'):
        img = t[base].copy()
        p = img.load()
        for _ in range(5):
            cx, cy = rng.randint(2, 13), rng.randint(2, 13)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (1, 1), (0, -1)):
                if rng.random() < 0.8:
                    f = 1 + rng.uniform(-0.15, 0.15)
                    p[cx + dx, cy + dy] = tuple(_clamp(c * f) for c in dot)
        return img
    t['coal_ore'] = ore((35, 35, 35))
    t['iron_ore'] = ore((216, 170, 140))
    t['gold_ore'] = ore((252, 215, 50))
    t['diamond_ore'] = ore((90, 240, 230))

    nr = tile_noise((112, 52, 50), 0.22, rng)
    p = nr.load()
    for _ in range(25):
        p[rng.randrange(16), rng.randrange(16)] = (75, 30, 30)
    t['netherrack'] = nr

    lava = Image.new('RGB', (16, 16))
    p = lava.load()
    for y in range(16):
        for x in range(16):
            w = 0.5 + 0.5 * math.sin(x * 0.9 + math.sin(y * 0.7) * 2) * math.cos(y * 0.6 + x * 0.2)
            w += rng.uniform(-0.12, 0.12)
            p[x, y] = (_clamp(200 + 55 * w), _clamp(70 + 120 * w), _clamp(10 + 30 * w))
    t['lava'] = lava

    gs = tile_noise((250, 205, 110), 0.12, rng)
    p = gs.load()
    for y in range(16):
        for x in range(16):
            if (x * 3 + y * 5) % 7 == 0 or rng.random() < 0.1:
                p[x, y] = (150, 105, 50)
    t['glowstone'] = gs

    ss = tile_noise((84, 64, 50), 0.2, rng)
    p = ss.load()
    for fx, fy in ((4, 5), (11, 9), (6, 12)):
        for dx, dy in ((0, 0), (2, 0), (1, 2)):
            p[fx + dx, fy + dy] = (45, 32, 25)
    t['soul_sand'] = ss

    t['quartz_ore'] = ore((235, 228, 220), 'netherrack')
    t['nether_gold'] = ore((252, 215, 50), 'netherrack')

    ob = tile_noise((22, 17, 34), 0.35, rng)
    p = ob.load()
    for _ in range(14):
        p[rng.randrange(16), rng.randrange(16)] = (70, 40, 110)
    t['obsidian'] = ob

    po = Image.new('RGB', (16, 16))
    p = po.load()
    for y in range(16):
        for x in range(16):
            w = 0.5 + 0.5 * math.sin((x + y) * 0.8 + math.sin(x * 0.5) * 3)
            p[x, y] = (_clamp(110 + 80 * w), _clamp(30 + 40 * w), _clamp(190 + 60 * w))
    t['portal'] = po

    # שולחן יצירה
    tt = t['planks'].copy()
    p = tt.load()
    for i in range(16):
        for j in (0, 15, 5, 10):
            p[i, j] = (95, 70, 40)
            p[j, i] = (95, 70, 40)
    t['table_top'] = tt
    ts = t['planks'].copy()
    p = ts.load()
    for x in range(16):
        for y in range(4):
            p[x, y] = (_clamp(110 * (1 + rng.uniform(-.1, .1))), 80, 45)
    for y in range(6, 14):                      # מסור
        p[3, y] = (170, 170, 170)
        p[4, y] = (150, 150, 150)
    for x in range(9, 13):                      # פטיש
        p[x, 6] = (120, 120, 120)
        p[x, 7] = (120, 120, 120)
    for y in range(8, 14):
        p[11, y] = (95, 65, 35)
    t['table_side'] = ts

    # Crafter
    cs = tile_noise((115, 115, 120), 0.08, rng)
    p = cs.load()
    for i in range(16):
        for j in (0, 1, 14, 15):
            p[i, j] = (60, 60, 65)
            p[j, i] = (60, 60, 65)
    for x in range(5, 11):
        for y in range(5, 11):
            p[x, y] = (40, 40, 45)
    for x in range(6, 10):
        for y in range(6, 10):
            p[x, y] = (220, 120, 40) if (x + y) % 2 else (180, 80, 30)
    t['crafter_side'] = cs
    ct = tile_noise((120, 120, 125), 0.08, rng)
    p = ct.load()
    for i in range(16):
        for j in (0, 5, 10, 15):
            p[i, j] = (55, 55, 60)
            p[j, i] = (55, 55, 60)
    t['crafter_top'] = ct
    t['torch'] = tile_noise((250, 200, 80), 0.05, rng)

    def metal_block(base):
        img = tile_noise(base, 0.05, rng)
        p = img.load()
        hi = tuple(_clamp(c * 1.25) for c in base)
        lo = tuple(_clamp(c * 0.65) for c in base)
        for i in range(16):
            p[i, 0] = p[0, i] = hi
            p[i, 15] = p[15, i] = lo
        for i in range(2, 14):
            p[i, 2] = hi
            p[2, i] = hi
        return img
    t['iron_block'] = metal_block((215, 215, 215))
    t['gold_block'] = metal_block((245, 205, 50))
    t['diamond_block'] = metal_block((95, 225, 215))
    t['coal_block'] = tile_noise((22, 22, 22), 0.4, rng)
    t['quartz_block'] = metal_block((236, 230, 222))
    sst = tile_noise((216, 202, 155), 0.05, rng)
    p = sst.load()
    for x in range(16):
        for y in (3, 4, 11):
            p[x, y] = (190, 175, 125)
    t['sandstone'] = sst
    t['sandstone_top'] = tile_noise((222, 210, 165), 0.04, rng)
    return t


TILES = make_tiles()
TILE_NAMES = list(TILES.keys())
TILE_INDEX = {n: i for i, n in enumerate(TILE_NAMES)}
N_TILES = len(TILE_NAMES)

# (top, side, bottom)
BLOCK_TEX = {
    GRASS: ('grass_top', 'grass_side', 'dirt'),
    DIRT: ('dirt',) * 3, STONE: ('stone',) * 3, COBBLE: ('cobble',) * 3,
    LOG: ('log_top', 'log_side', 'log_top'), PLANKS: ('planks',) * 3,
    LEAVES: ('leaves',) * 3, SAND: ('sand',) * 3, SNOW: ('snow',) * 3,
    WATER: ('water',) * 3, BEDROCK: ('bedrock',) * 3, BRICK: ('brick',) * 3,
    COAL_ORE: ('coal_ore',) * 3, IRON_ORE: ('iron_ore',) * 3,
    GOLD_ORE: ('gold_ore',) * 3, DIAMOND_ORE: ('diamond_ore',) * 3,
    NETHERRACK: ('netherrack',) * 3, LAVA: ('lava',) * 3, GLOWSTONE: ('glowstone',) * 3,
    SOUL_SAND: ('soul_sand',) * 3, QUARTZ_ORE: ('quartz_ore',) * 3, NETHER_GOLD: ('nether_gold',) * 3,
    OBSIDIAN: ('obsidian',) * 3, PORTAL: ('portal',) * 3,
    CRAFTING_TABLE: ('table_top', 'table_side', 'planks'),
    CRAFTER: ('crafter_top', 'crafter_side', 'crafter_top'), TORCH: ('torch',) * 3,
    IRON_BLOCK: ('iron_block',) * 3, GOLD_BLOCK: ('gold_block',) * 3, DIAMOND_BLOCK: ('diamond_block',) * 3,
    COAL_BLOCK: ('coal_block',) * 3, QUARTZ_BLOCK: ('quartz_block',) * 3,
    SANDSTONE: ('sandstone_top', 'sandstone', 'sandstone_top'),
}

# ---------------------------------------------------------------- פונקציות רעש לייצור השטח
def hash2(x, z, s):
    n = (x * 374761393 + z * 668265263 + s * 982451653) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 0xFFFFFFFF


def value_noise(x, z, s):
    xi, zi = math.floor(x), math.floor(z)
    xf, zf = x - xi, z - zi
    u = xf * xf * (3 - 2 * xf)
    v = zf * zf * (3 - 2 * zf)
    a, b = hash2(xi, zi, s), hash2(xi + 1, zi, s)
    c, d = hash2(xi, zi + 1, s), hash2(xi + 1, zi + 1, s)
    return (a + (b - a) * u) + ((c + (d - c) * u) - (a + (b - a) * u)) * v


def fbm(x, z, octaves=4):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for i in range(octaves):
        total += value_noise(x * freq, z * freq, SEED + i * 101) * amp
        norm += amp
        amp *= 0.5
        freq *= 2
    return total / norm


# ---------------------------------------------------------------- העולם
world = {}          # (x, y, z) -> block id
chunk_keys = {}     # (cx, cz) -> set של מיקומים
SIZE = CHUNK * WORLD_CHUNKS


def chunk_of(x, z):
    return (x // CHUNK, z // CHUNK)


def raw_set(pos, b):
    key = chunk_of(pos[0], pos[2])
    if not (0 <= pos[0] < SIZE and 0 <= pos[2] < SIZE and 0 <= pos[1] < 128):
        return False
    if b == AIR:
        world.pop(pos, None)
        chunk_keys.get(key, set()).discard(pos)
    else:
        world[pos] = b
        chunk_keys.setdefault(key, set()).add(pos)
    return True


def height_at(x, z):
    n = fbm(x / TERRAIN_SCALE, z / TERRAIN_SCALE)
    m = fbm(x / 20 + 500, z / 20 + 500, 2)
    h = SEA - 7 + (n - 0.3 + TERRAIN_SHIFT) * TERRAIN_AMP + (m - 0.5) * 4
    return max(13, min(72, int(h)))


def generate():
    rng = random.Random(SEED)
    heights = {}
    for x in range(SIZE):
        for z in range(SIZE):
            h = height_at(x, z)
            heights[(x, z)] = h
            if h <= SEA + 1:
                top, under = SAND, SAND
            elif h > SNOW_LINE:
                top, under = SNOW, STONE
            else:
                top, under = GRASS, DIRT
            for y in range(h + 1):
                if y == 0:
                    b = BEDROCK
                elif y < h - 3:
                    b = STONE
                elif y < h:
                    b = under
                else:
                    b = top
                raw_set((x, y, z), b)
            for y in range(h + 1, SEA + 1):
                raw_set((x, y, z), WATER)

    # מערות - רשת מנהרות ארוכות שמתפתלות מתחת לכל המפה
    CARVABLE = (STONE, DIRT, SAND, SNOW, GRASS)

    def carve_sphere(cx, cy, cz, r, surface_ok):
        for bx in range(int(cx - r), int(cx + r) + 1):
            for bz in range(int(cz - r), int(cz + r) + 1):
                hh = heights.get((bx, bz))
                if hh is None:
                    continue
                limit = hh + 1 if surface_ok else hh - 3   # בדרך כלל נשאר "גג" של 3 בלוקים
                for by in range(max(1, int(cy - r)), min(limit, int(cy + r) + 1)):
                    if (bx - cx) ** 2 + ((by - cy) * 1.3) ** 2 + (bz - cz) ** 2 <= r * r \
                            and world.get((bx, by, bz)) in CARVABLE:
                        raw_set((bx, by, bz), AIR)

    def worm(x, y, z, yaw, pitch, length, r0, entrance=False, depth=0):
        r = r0
        for step in range(length):
            yaw += rng.uniform(-0.3, 0.3) + math.sin(step * 0.07) * 0.08
            if entrance and step < 14:
                pitch = -0.55                      # כניסה: יורדת מפני השטח למטה
            else:
                pitch = pitch * 0.9 + rng.uniform(-0.18, 0.18)
                if y < 5:
                    pitch += 0.08                  # לא נתקעים ליד הסלע התחתון
                elif y > SEA + 14:
                    pitch -= 0.08
            x += math.cos(yaw) * math.cos(pitch)
            z += math.sin(yaw) * math.cos(pitch)
            y += math.sin(pitch) * 1.2
            # נשארים בתוך העולם - פונים חזרה כשמגיעים לקצה
            if not (3 < x < SIZE - 3 and 3 < z < SIZE - 3):
                yaw += math.pi * 0.6
                x, z = max(3.5, min(SIZE - 3.5, x)), max(3.5, min(SIZE - 3.5, z))
            y = max(2.5, min(SEA + 24, y))
            r = max(1.1, min(2.3, r + rng.uniform(-0.15, 0.15)))
            carve_sphere(x, y, z, r, entrance and step < 16)
            if rng.random() < 0.007:               # מדי פעם: חדר רחב
                carve_sphere(x, y, z, rng.uniform(3.2, 4.8), False)
            if depth < 1 and rng.random() < 0.01:   # הסתעפות
                worm(x, y, z, yaw + rng.choice((-1, 1)) * rng.uniform(0.8, 1.6), 0,
                     rng.randint(40, 110), r * 0.85, depth=depth + 1)

    # נקודות התחלה מפוזרות על רשת, כך שהמנהרות מכסות את כל המפה
    GRID = 5
    cell = SIZE / GRID
    for gx in range(GRID):
        for gz in range(GRID):
            x = (gx + rng.uniform(0.2, 0.8)) * cell
            z = (gz + rng.uniform(0.2, 0.8)) * cell
            y = rng.uniform(5, max(6, min(SEA + 12, heights[(int(x), int(z))] - 6)))
            worm(x, y, z, rng.uniform(0, 6.28), 0, rng.randint(90, 160), rng.uniform(1.3, 2.0))

    # השלמה: כל ריבוע של 12x12 בלוקים בלי מערה מקבל מנהרה משלו
    B = 12
    for cx0 in range(0, SIZE, B):
        for cz0 in range(0, SIZE, B):
            has = any((x, y, z) not in world
                      for x in range(cx0, cx0 + B, 3) for z in range(cz0, cz0 + B, 3)
                      for y in range(3, heights[(x, z)] - 3))
            if not has:
                x, z = cx0 + B / 2, cz0 + B / 2
                y = rng.uniform(4, max(5, min(SEA + 10, heights[(int(x), int(z))] - 6)))
                worm(x, y, z, rng.uniform(0, 6.28), 0, rng.randint(50, 90), rng.uniform(1.3, 1.9))

    # כמה כניסות למערות מפני השטח
    made = 0
    for _ in range(200):
        if made >= 5:
            break
        x, z = rng.randrange(8, SIZE - 8), rng.randrange(8, SIZE - 8)
        if heights[(x, z)] > SEA + 3:
            worm(x + 0.5, heights[(x, z)] + 1.0, z + 0.5, rng.uniform(0, 6.28), -0.55,
                 rng.randint(60, 120), 1.8, entrance=True)
            made += 1

    # עפרות: פחם, ברזל, זהב ויהלומים (יהלומים רק עמוק!)
    def vein(block, count, ymin, ymax, size):
        for _ in range(count):
            x, y, z = rng.randrange(SIZE), rng.randint(ymin, ymax), rng.randrange(SIZE)
            for _ in range(size):
                if world.get((x, y, z)) == STONE:
                    raw_set((x, y, z), block)
                x += rng.choice((-1, 0, 1))
                y += rng.choice((-1, 0, 0, 1))
                z += rng.choice((-1, 0, 1))
    vein(COAL_ORE, 230, 3, 55, 9)
    vein(IRON_ORE, 150, 2, 38, 6)
    vein(GOLD_ORE, 50, 2, 16, 5)
    vein(DIAMOND_ORE, 40, 1, 12, 5)

    # עצים
    for x in range(2, SIZE - 2):
        for z in range(2, SIZE - 2):
            h = heights[(x, z)]
            if world.get((x, h, z)) == GRASS and rng.random() < TREE_CHANCE:
                th = rng.randint(4, 6)
                for y in range(h + 1, h + th + 1):
                    raw_set((x, y, z), LOG)
                ty = h + th
                for dy in range(-2, 2):
                    r = 2 if dy < 0 else 1
                    for dx in range(-r, r + 1):
                        for dz in range(-r, r + 1):
                            if abs(dx) == r and abs(dz) == r and rng.random() < 0.5:
                                continue
                            p = (x + dx, ty + dy, z + dz)
                            if p not in world:
                                raw_set(p, LEAVES)
                raw_set((x, ty + 1, z), LEAVES)
    return heights


NETHER_TOP = 48
NETHER_LAVA = 11


def generate_nether():
    """הנדר: עולם מערות סגור עם רצפה, תקרה, ים לבה ואבני זוהר."""
    rng = random.Random(SEED + 666)
    floors = {}
    for x in range(SIZE):
        for z in range(SIZE):
            f = int(2 + fbm(x / 24 + 300, z / 24 + 300) * 26)
            cl = int(NETHER_TOP - 4 - fbm(x / 20 + 900, z / 20 + 900) * 26)
            floors[(x, z)] = f
            soul = fbm(x / 9 + 50, z / 9 + 50, 2) > 0.62
            for y in range(NETHER_TOP + 1):
                if y == 0 or y == NETHER_TOP:
                    b = BEDROCK
                elif y <= f or y >= cl:
                    b = SOUL_SAND if (y == f and soul) else NETHERRACK
                elif y <= NETHER_LAVA:
                    b = LAVA
                else:
                    continue
                raw_set((x, y, z), b)

    # אבני זוהר שתלויות מהתקרה
    for _ in range(45):
        x, z = rng.randrange(2, SIZE - 2), rng.randrange(2, SIZE - 2)
        y = NETHER_TOP - 1
        while y > 1 and world.get((x, y, z)) == NETHERRACK:
            y -= 1
        if world.get((x, y, z)) is not None:
            continue
        for _ in range(rng.randint(6, 16)):
            raw_set((x, y, z), GLOWSTONE)
            x += rng.choice((-1, 0, 1))
            z += rng.choice((-1, 0, 1))
            y -= rng.choice((0, 0, 1))
            x, z = max(0, min(SIZE - 1, x)), max(0, min(SIZE - 1, z))

    # עפרות קוורץ וזהב
    for block, count, size in ((QUARTZ_ORE, 120, 6), (NETHER_GOLD, 60, 4)):
        for _ in range(count):
            x, y, z = rng.randrange(SIZE), rng.randint(2, NETHER_TOP - 2), rng.randrange(SIZE)
            for _ in range(size):
                if world.get((x, y, z)) == NETHERRACK:
                    raw_set((x, y, z), block)
                x += rng.choice((-1, 0, 1))
                y += rng.choice((-1, 0, 1))
                z += rng.choice((-1, 0, 1))
    return floors


def build_portal(x0, y0, z0):
    """בונה מסגרת אובסידיאן 4x5 עם פורטל סגול בפנים (פונה לכיוון z)."""
    for dx in range(4):
        for dy in range(5):
            edge = dx in (0, 3) or dy in (0, 4)
            raw_set((x0 + dx, y0 + dy, z0), OBSIDIAN if edge else PORTAL)


def clear_box(x0, x1, y0, y1, z0, z1):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                raw_set((x, y, z), AIR)


# ---------------------------------------------------------------- בניית רשתות (mesh) לצ'אנקים
FACES = [
    ((1, 0, 0), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)), 1, 0.80),
    ((-1, 0, 0), ((0, 0, 1), (0, 1, 1), (0, 1, 0), (0, 0, 0)), 1, 0.80),
    ((0, 1, 0), ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)), 0, 1.00),
    ((0, -1, 0), ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), 2, 0.50),
    ((0, 0, 1), ((1, 0, 1), (1, 1, 1), (0, 1, 1), (0, 0, 1)), 1, 0.90),
    ((0, 0, -1), ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)), 1, 0.70),
]
FACE_UV = ((0, 0), (0, 1), (1, 1), (1, 0))
EPS_UV = 0.0005


def build_atlas():
    atlas = Image.new('RGB', (16 * N_TILES, 16))
    for name, i in TILE_INDEX.items():
        atlas.paste(TILES[name], (i * 16, 0))
    return make_texture(atlas)


class Chunk:
    def __init__(self, cx, cz, atlas):
        self.cx, self.cz = cx, cz
        self.atlas = atlas
        self.solid = Entity(texture=atlas, shader=unlit_shader)
        self.water = Entity(texture=atlas, shader=unlit_shader)
        self.water.setTransparency(True)
        self.build()

    def build(self):
        sv, su, sc = [], [], []
        wv, wu, wc = [], [], []
        for pos in chunk_keys.get((self.cx, self.cz), ()):
            b = world[pos]
            if b == TORCH:
                continue
            x, y, z = pos
            fluid = b in FLUIDLIKE
            alpha = TRANSPARENT.get(b)
            tex = BLOCK_TEX[b]
            for (nx, ny, nz), corners, kind, shade in FACES:
                nb = world.get((x + nx, y + ny, z + nz), AIR)
                if fluid:
                    if nb == b or is_solid(nb):
                        continue
                elif is_solid(nb):
                    continue
                ti = TILE_INDEX[tex[kind]]
                u0 = ti / N_TILES + EPS_UV
                u1 = (ti + 1) / N_TILES - EPS_UV
                # שינוי בהירות קטן לכל בלוק כדי שייראה טבעי יותר
                s = shade * (0.94 + 0.06 * hash2(x * 7 + y, z * 13 - y, 3))
                if b in GLOW:
                    s = 0.92 + 0.08 * shade
                top_lower = b in (WATER, LAVA) and world.get((x, y + 1, z), AIR) == AIR
                if alpha:
                    col, V, U, C = color.Color(s, s, s, alpha), wv, wu, wc
                else:
                    col, V, U, C = color.Color(s, s, s, 1), sv, su, sc
                quad = []
                for (cx_, cy_, cz_), (uu, vv) in zip(corners, FACE_UV):
                    yy = y + cy_
                    if top_lower and cy_ == 1:
                        yy -= 0.12
                    quad.append((Vec3(x + cx_, yy, z + cz_), (u0 if uu == 0 else u1, vv)))
                for i in (0, 1, 2, 0, 2, 3):
                    V.append(quad[i][0])
                    U.append(quad[i][1])
                    C.append(col)
        self.solid.model = Mesh(vertices=sv, uvs=su, colors=sc, static=True) if sv else None
        self.water.model = Mesh(vertices=wv, uvs=wu, colors=wc, static=True) if wv else None
        if self.solid.model:
            self.solid.double_sided = True
        if self.water.model:
            self.water.double_sided = True


chunks = {}


torch_entities = {}


def make_torch_entity(pos):
    root = Entity(position=(pos[0] + 0.5, pos[1], pos[2] + 0.5))
    part(root, (0.45, 0.32, 0.17), (0.12, 0.6, 0.12), (0, 0.3, 0))
    part(root, (1.0, 0.85, 0.25), (0.16, 0.16, 0.16), (0, 0.66, 0))
    part(root, (1.0, 0.55, 0.1), (0.1, 0.1, 0.1), (0, 0.77, 0))
    torch_entities[pos] = root


def sync_torches():
    for e in torch_entities.values():
        destroy(e)
    torch_entities.clear()
    for pos, b in world.items():
        if b == TORCH:
            make_torch_entity(pos)


def set_block(pos, b):
    old = world.get(pos, AIR)
    if not raw_set(pos, b):
        return
    CHANGES.setdefault(current_dim, {})[pos] = b      # נשמר בקובץ השמירה
    if old == TORCH and b != TORCH and pos in torch_entities:
        destroy(torch_entities.pop(pos))
    if b == TORCH and pos not in torch_entities:
        make_torch_entity(pos)
    x, _, z = pos
    to_update = {chunk_of(x, z)}
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        to_update.add(chunk_of(x + dx, z + dz))
    for key in to_update:
        if key in chunks:
            chunks[key].build()


# ---------------------------------------------------------------- שחקן ופיזיקה
HW, PH, EYE = 0.3, 1.8, 1.62


def collides(x, y, z):
    for bx in range(math.floor(x - HW), math.floor(x + HW - 1e-6) + 1):
        for by in range(math.floor(y), math.floor(y + PH - 1e-6) + 1):
            for bz in range(math.floor(z - HW), math.floor(z + HW - 1e-6) + 1):
                if is_solid(world.get((bx, by, bz), AIR)):
                    return True
    return False


UI_LOCK = [False]     # True כשהמלאי פתוח - השחקן לא זז


class Player:
    def __init__(self, spawn):
        self.spawn = spawn
        self.p = list(spawn)
        self.vy = 0.0
        self.yaw, self.pitch = 45.0, 10.0
        self.on_ground = False
        self.flying = False

    def move_axis(self, axis, d):
        """מזיז בציר אחד, ובמקרה של התנגשות מתקרב עד למגע. מחזיר True אם הייתה התנגשות."""
        if d == 0:
            return False
        steps = max(1, int(abs(d) / 0.4) + 1)
        sd = d / steps
        for _ in range(steps):
            start = self.p[axis]
            self.p[axis] = start + sd
            if collides(*self.p):
                lo, hi = 0.0, 1.0
                for _ in range(10):
                    mid = (lo + hi) / 2
                    self.p[axis] = start + sd * mid
                    if collides(*self.p):
                        hi = mid
                    else:
                        lo = mid
                self.p[axis] = start + sd * lo
                return True
        return False

    def in_water(self):
        return world.get((math.floor(self.p[0]), math.floor(self.p[1] + 0.4), math.floor(self.p[2]))) in (WATER, LAVA)

    def touching(self, block):
        x, y, z = self.p
        for bx in range(math.floor(x - HW), math.floor(x + HW - 1e-6) + 1):
            for by in range(math.floor(y), math.floor(y + PH - 1e-6) + 1):
                for bz in range(math.floor(z - HW), math.floor(z + HW - 1e-6) + 1):
                    if world.get((bx, by, bz)) == block:
                        return True
        return False

    def update(self, dt):
        K = (lambda k: 0) if UI_LOCK[0] else (lambda k: held_keys[k])
        self.frames = getattr(self, 'frames', 0) + 1
        if mouse.locked and self.frames > 10:   # מתעלמים מקפיצת העכבר בהתחלה
            self.yaw += mouse.velocity[0] * MOUSE_SENS
            self.pitch -= mouse.velocity[1] * MOUSE_SENS
            self.pitch = max(-89, min(89, self.pitch))

        r = math.radians(self.yaw)
        fx, fz = math.sin(r), math.cos(r)
        rx, rz = math.cos(r), -math.sin(r)
        f = K('w') - K('s')
        s = K('d') - K('a')
        dx, dz = fx * f + rx * s, fz * f + rz * s
        ln = math.hypot(dx, dz)
        if ln > 0:
            dx, dz = dx / ln, dz / ln

        water = self.in_water()
        if self.flying:
            speed = 11
            self.vy = (K('space') - K('left shift')) * 9
        else:
            speed = 5.6 if K('left shift') else 4.3
            if water:
                speed *= 0.55
                self.vy = max(self.vy - 9 * dt, -3)
                if K('space'):
                    self.vy = 3.6
            else:
                self.vy = max(self.vy - 28 * dt, -55)
                if K('space') and self.on_ground:
                    self.vy = 8.6

        if self.touching(PORTAL):         # הפורטל "תופס" את השחקן
            speed *= 0.12
        self.move_axis(0, dx * speed * dt)
        self.move_axis(2, dz * speed * dt)
        hit = self.move_axis(1, self.vy * dt)
        self.on_ground = hit and self.vy < 0
        if hit:
            self.vy = 0

        if self.p[1] < -30:
            self.respawn()

        camera.position = Vec3(self.p[0], self.p[1] + EYE, self.p[2])
        camera.rotation = Vec3(self.pitch, self.yaw, 0)

    def respawn(self):
        self.p = list(self.spawn)
        self.vy = 0


# ---------------------------------------------------------------- ירי קרן לבחירת בלוק (DDA)
def raycast(origin, direction, maxd=REACH):
    x, y, z = (math.floor(c) for c in origin)
    step, tmax, tdelta = [], [], []
    for i, (o, d) in enumerate(zip(origin, direction)):
        cell = (x, y, z)[i]
        if d > 0:
            step.append(1); tmax.append((cell + 1 - o) / d); tdelta.append(1 / d)
        elif d < 0:
            step.append(-1); tmax.append((o - cell) / -d); tdelta.append(-1 / d)
        else:
            step.append(0); tmax.append(float('inf')); tdelta.append(float('inf'))
    cur = [x, y, z]
    prev = None
    t = 0.0
    while t <= maxd:
        b = world.get(tuple(cur), AIR)
        if is_solid(b) or b == TORCH:
            return tuple(cur), prev
        prev = tuple(cur)
        a = tmax.index(min(tmax))
        t = tmax[a]
        cur[a] += step[a]
        tmax[a] += tdelta[a]
    return None, None


# ---------------------------------------------------------------- חיות
def cube_mesh():
    """קובייה עם הצללה שונה לכל פאה, כדי שהחיות ייראו תלת-ממדיות."""
    verts, cols = [], []
    for _, corners, _, shade in FACES:
        c = color.Color(shade, shade, shade, 1)
        quad = [Vec3(cx - 0.5, cy - 0.5, cz - 0.5) for cx, cy, cz in corners]
        for i in (0, 1, 2, 0, 2, 3):
            verts.append(quad[i])
            cols.append(c)
    return Mesh(vertices=verts, colors=cols, static=True)


def part(parent, col, scale, pos=(0, 0, 0)):
    e = Entity(parent=parent, model=cube_mesh(), color=color.Color(*col, 1),
               scale=scale, position=pos, shader=unlit_shader)
    e.double_sided = True
    return e


MOB_TYPES = {
    'pig': dict(body=(0.62, 0.5, 0.95), leg=(0.22, 0.32, 0.22), leg_x=0.17, leg_z=0.3,
                head=(0.5, 0.48, 0.45), head_pos=(0, 0.72, 0.62),
                col=(0.95, 0.66, 0.66), leg_col=(0.88, 0.58, 0.6), head_col=(0.95, 0.66, 0.66),
                extra=[((0, 0.66, 0.86), (0.26, 0.18, 0.06), (0.85, 0.45, 0.5)),
                       ((0.12, 0.8, 0.85), (0.08, 0.08, 0.02), (0.1, 0.1, 0.1)),
                       ((-0.12, 0.8, 0.85), (0.08, 0.08, 0.02), (0.1, 0.1, 0.1))],
                hp=3, drop='Pork', speed=1.1, two_legs=False),
    'cow': dict(body=(0.72, 0.65, 1.15), leg=(0.24, 0.55, 0.24), leg_x=0.22, leg_z=0.4,
                head=(0.5, 0.5, 0.42), head_pos=(0, 1.15, 0.72),
                col=(0.33, 0.23, 0.16), leg_col=(0.3, 0.2, 0.14), head_col=(0.33, 0.23, 0.16),
                extra=[((0.37, 0.9, 0.1), (0.02, 0.35, 0.45), (0.95, 0.95, 0.92)),
                       ((-0.37, 0.95, -0.25), (0.02, 0.3, 0.35), (0.95, 0.95, 0.92)),
                       ((0, 1.05, 0.95), (0.36, 0.22, 0.06), (0.9, 0.75, 0.7)),
                       ((0.3, 1.38, 0.72), (0.12, 0.08, 0.08), (0.9, 0.88, 0.8)),
                       ((-0.3, 1.38, 0.72), (0.12, 0.08, 0.08), (0.9, 0.88, 0.8))],
                hp=4, drop='Beef', speed=0.9, two_legs=False),
    'sheep': dict(body=(0.7, 0.62, 1.0), leg=(0.2, 0.45, 0.2), leg_x=0.2, leg_z=0.32,
                  head=(0.4, 0.42, 0.4), head_pos=(0, 1.0, 0.6),
                  col=(0.93, 0.93, 0.9), leg_col=(0.85, 0.78, 0.7), head_col=(0.85, 0.78, 0.7),
                  extra=[((0, 1.2, 0.58), (0.46, 0.14, 0.4), (0.93, 0.93, 0.9))],
                  hp=3, drop='Wool', speed=0.95, two_legs=False),
    'chicken': dict(body=(0.36, 0.34, 0.45), leg=(0.06, 0.25, 0.06), leg_x=0.08, leg_z=0.0,
                    head=(0.24, 0.32, 0.2), head_pos=(0, 0.66, 0.22),
                    col=(0.97, 0.97, 0.95), leg_col=(0.95, 0.7, 0.15), head_col=(0.97, 0.97, 0.95),
                    extra=[((0, 0.68, 0.36), (0.12, 0.07, 0.1), (0.98, 0.65, 0.1)),
                           ((0, 0.6, 0.34), (0.07, 0.1, 0.05), (0.85, 0.1, 0.1)),
                           ((0.19, 0.44, -0.02), (0.04, 0.22, 0.32), (0.92, 0.92, 0.9)),
                           ((-0.19, 0.44, -0.02), (0.04, 0.22, 0.32), (0.92, 0.92, 0.9))],
                    hp=2, drop='Feather', speed=1.0, two_legs=True),
}


def ground_at(x, z, y_from):
    """גובה הקרקע (כולל פני מים) מתחת לנקודה. מחזיר (גובה, סוג בלוק)."""
    bx, bz = math.floor(x), math.floor(z)
    for by in range(math.floor(y_from + 1.01), -1, -1):
        b = world.get((bx, by, bz))
        if b is not None:
            return by + 1, b
    return 0, AIR


class Mob(Entity):
    def __init__(self, kind, pos):
        super().__init__(position=pos)
        self.kind = kind
        sp = self.sp = MOB_TYPES[kind]
        lw, lh, ld = sp['leg']
        bw, bh, bd = sp['body']
        part(self, sp['col'], sp['body'], (0, lh + bh / 2, 0))
        part(self, sp['head_col'], sp['head'], sp['head_pos'])
        for pos_, scale_, col_ in sp['extra']:
            part(self, col_, scale_, pos_)
        self.legs = []
        zs = (0,) if sp['two_legs'] else (-1, 1)
        for sx in (-1, 1):
            for sz in zs:
                pivot = Entity(parent=self, position=(sx * sp['leg_x'], lh, sz * sp['leg_z']))
                part(pivot, sp['leg_col'], sp['leg'], (0, -lh / 2, 0))
                self.legs.append((pivot, sx * (sz or 1)))
        self.half = max(bw, bd) / 2 + 0.05
        self.height = max(lh + bh, sp['head_pos'][1] + sp['head'][1] / 2)
        self.hp = sp['hp']
        self.yaw = random.uniform(0, 360)
        self.rotation_y = self.yaw
        self.vy = 0.0
        self.timer = random.uniform(0, 3)
        self.walking = False
        self.flee = 0.0
        self.phase = 0.0
        self.flash = 0.0

    def tick(self, dt):
        self.timer -= dt
        self.flee = max(0.0, self.flee - dt)
        if self.timer <= 0:
            self.walking = random.random() < 0.6 or self.flee > 0
            self.yaw = (self.yaw + random.uniform(-120, 120)) % 360
            self.timer = random.uniform(0.6, 1.2) if self.flee > 0 else random.uniform(2, 5)

        moving = False
        if self.walking:
            speed = self.sp['speed'] * (2.4 if self.flee > 0 else 1)
            r = math.radians(self.yaw)
            dx, dz = math.sin(r) * speed * dt, math.cos(r) * speed * dt
            nx, nz = self.x + dx, self.z + dz
            lx, lz = self.x + math.sin(r) * (self.half + 0.1), self.z + math.cos(r) * (self.half + 0.1)
            g, b = ground_at(lx, lz, self.y + 1)
            inside = 1 <= lx < SIZE - 1 and 1 <= lz < SIZE - 1
            if not inside or b == WATER or g > self.y + 1.01 or g < self.y - 3 \
                    or is_solid(world.get((math.floor(lx), g + 1, math.floor(lz)), AIR)):
                self.yaw = (self.yaw + random.uniform(100, 260)) % 360   # מסתובב אחורה
                self.timer = min(self.timer, 1.0)
            else:
                self.x, self.z = nx, nz
                moving = True
                if g > self.y:            # עולה מדרגה
                    self.y = g

        # כבידה
        g, _ = ground_at(self.x, self.z, self.y)
        if self.y > g + 0.001 or self.vy > 0:
            self.vy -= 22 * dt
            self.y += self.vy * dt
            if self.y <= g:
                self.y, self.vy = g, 0.0
        else:
            self.y, self.vy = g, 0.0

        # סיבוב חלק לכיוון ההליכה
        diff = (self.yaw - self.rotation_y + 180) % 360 - 180
        self.rotation_y += diff * min(1, dt * 6)

        # אנימציית רגליים
        if moving:
            self.phase += dt * 9 * (2 if self.flee > 0 else 1)
            for pivot, sign in self.legs:
                pivot.rotation_x = math.sin(self.phase) * 35 * sign
        else:
            for pivot, _ in self.legs:
                pivot.rotation_x *= 0.85

        if self.flash > 0:
            self.flash -= dt
            if self.flash <= 0:
                self.setColorScale(1, 1, 1, 1)

    def hit_distance(self, o, d):
        """בדיקת פגיעה של קרן בקופסה שסביב החיה."""
        mn = (self.x - self.half, self.y, self.z - self.half)
        mx = (self.x + self.half, self.y + self.height, self.z + self.half)
        t0, t1 = 0.0, REACH
        for i in range(3):
            if abs(d[i]) < 1e-9:
                if o[i] < mn[i] or o[i] > mx[i]:
                    return None
            else:
                a, b = (mn[i] - o[i]) / d[i], (mx[i] - o[i]) / d[i]
                if a > b:
                    a, b = b, a
                t0, t1 = max(t0, a), min(t1, b)
                if t0 > t1:
                    return None
        return t0

    def hurt(self, from_x, from_z, dmg=1):
        self.hp -= dmg
        self.setColorScale(1, 0.35, 0.35, 1)
        self.flash = 0.25
        away = math.degrees(math.atan2(self.x - from_x, self.z - from_z))
        self.yaw = away
        self.rotation_y = away
        self.vy = 5.5
        self.flee = 4.0
        self.walking = True
        self.timer = 1.0
        return self.hp <= 0


mobs = []


def spawn_mob(away_from=None, tries=60):
    for _ in range(tries):
        x, z = random.randrange(2, SIZE - 2), random.randrange(2, SIZE - 2)
        if away_from and math.hypot(x - away_from[0], z - away_from[2]) < 16:
            continue
        g, b = ground_at(x + 0.5, z + 0.5, 95)
        if b == GRASS:
            kind = random.choice(['pig', 'pig', 'cow', 'sheep', 'chicken', 'chicken'])
            mobs.append(Mob(kind, (x + 0.5, g, z + 0.5)))
            return True
    return False


inventory = {}
MAX_MOBS = 22


# ================================================================ מפלצות המערות
# שלוש מפלצות מקוריות שחיות רק במערות. הורגים אותן עם חרב.
MONSTER_TYPES = {
    # חיפושית מערות: קטנה ומהירה, נושכת
    'beetle': dict(hp=8, speed=2.7, dmg=2, reach=1.3, cooldown=1.0, drop=('Coal', 1, 2), fly=False,
                   half=0.45, height=0.6),
    # גב-סלע: איטי וחזק, עם קוצי קריסטל על הגב
    'rockback': dict(hp=14, speed=1.6, dmg=5, reach=1.7, cooldown=1.6, drop=('Iron Ingot', 1, 2), fly=False,
                     half=0.6, height=1.3),
    # עין קריסטל: מרחפת ויורה רסיסים מרחוק
    'eye': dict(hp=6, speed=2.2, dmg=3, reach=14, cooldown=2.4, drop=('Quartz', 1, 2), fly=True,
                half=0.4, height=0.8),
}


NOT_ROOF = (LEAVES, LOG, WATER, TORCH)


def under_roof(x, y, z):
    """האם יש תקרה של אדמה/אבן מעל הנקודה (כלומר אנחנו בתוך מערה ולא תחת כיפת השמיים)."""
    bx, bz = math.floor(x), math.floor(z)
    for by in range(math.floor(y) + 1, 100):
        b = world.get((bx, by, bz))
        if b is not None and b not in NOT_ROOF:
            return True
    return False


class Monster(Entity):
    def __init__(self, kind, pos):
        super().__init__(position=pos)
        self.kind = kind
        self.sp = MONSTER_TYPES[kind]
        self.hp = self.sp['hp']
        self.half, self.height = self.sp['half'], self.sp['height']
        self.vy = 0.0
        self.attack_cd = 1.0
        self.flash = 0.0
        self.phase = random.uniform(0, 6)
        self.legs = []
        self.wander_yaw = random.uniform(0, 360)
        self.wander_t = 0.0
        if kind == 'beetle':
            part(self, (0.28, 0.12, 0.36), (0.8, 0.32, 1.0), (0, 0.38, 0))          # שריון
            part(self, (0.42, 0.2, 0.52), (0.62, 0.12, 0.8), (0, 0.58, -0.05))
            part(self, (0.18, 0.08, 0.22), (0.5, 0.3, 0.32), (0, 0.36, 0.6))       # ראש
            part(self, (1.0, 0.25, 0.1), (0.1, 0.1, 0.04), (0.14, 0.42, 0.77))     # עיניים
            part(self, (1.0, 0.25, 0.1), (0.1, 0.1, 0.04), (-0.14, 0.42, 0.77))
            part(self, (0.12, 0.05, 0.14), (0.05, 0.05, 0.3), (0.12, 0.3, 0.9))    # צבתות
            part(self, (0.12, 0.05, 0.14), (0.05, 0.05, 0.3), (-0.12, 0.3, 0.9))
            for sz in (-0.3, 0.05, 0.38):
                for sx in (-1, 1):
                    pv = Entity(parent=self, position=(sx * 0.42, 0.32, sz))
                    part(pv, (0.14, 0.06, 0.17), (0.32, 0.07, 0.08), (sx * 0.14, -0.12, 0))
                    self.legs.append((pv, sx * (1 if sz != 0.05 else -1)))
        elif kind == 'rockback':
            part(self, (0.42, 0.38, 0.34), (1.0, 0.75, 1.2), (0, 0.85, 0))         # גוף
            part(self, (0.35, 0.31, 0.28), (0.7, 0.55, 0.55), (0, 0.75, 0.82))     # ראש
            part(self, (1.0, 0.55, 0.05), (0.14, 0.1, 0.04), (0.18, 0.85, 1.1))    # עיניים כתומות
            part(self, (1.0, 0.55, 0.05), (0.14, 0.1, 0.04), (-0.18, 0.85, 1.1))
            for i, (x, z, h) in enumerate(((0.2, -0.3, 0.45), (-0.25, 0.1, 0.55), (0.15, 0.35, 0.35),
                                           (-0.1, -0.45, 0.3), (0.3, 0.05, 0.3))):
                part(self, (0.45, 0.85, 0.95), (0.16, h, 0.16), (x, 1.22 + h / 2, z))  # קוצי קריסטל
            for sx in (-1, 1):
                for sz in (-1, 1):
                    pv = Entity(parent=self, position=(sx * 0.35, 0.48, sz * 0.4))
                    part(pv, (0.33, 0.29, 0.26), (0.3, 0.5, 0.3), (0, -0.24, 0))
                    self.legs.append((pv, sx * sz))
        else:  # eye
            self.body = Entity(parent=self, position=(0, 0.4, 0))
            part(self.body, (0.35, 0.85, 0.95), (0.55, 0.55, 0.55))
            core = part(self.body, (0.6, 0.95, 1.0), (0.42, 0.75, 0.42))
            core.rotation_y = 45
            part(self.body, (0.98, 0.98, 1.0), (0.3, 0.3, 0.06), (0, 0, 0.29))      # לבן העין
            part(self.body, (0.6, 0.05, 0.25), (0.13, 0.13, 0.04), (0, 0, 0.33))    # אישון
            for a in range(4):
                sh = part(self.body, (0.25, 0.7, 0.85), (0.12, 0.12, 0.35))
                sh.position = (math.cos(a * 1.57) * 0.38, math.sin(a * 1.57) * 0.38, -0.05)
        self.rotation_y = random.uniform(0, 360)

    hit_distance = Mob.hit_distance

    def free(self, x, y, z):
        """האם יש מקום לגוף של המפלצת בנקודה הזו."""
        for bx in (math.floor(x - self.half * 0.7), math.floor(x + self.half * 0.7)):
            for bz in (math.floor(z - self.half * 0.7), math.floor(z + self.half * 0.7)):
                for by in range(math.floor(y + 0.05), math.floor(y + self.height) + 1):
                    if is_solid(world.get((bx, by, bz), AIR)):
                        return False
        return under_roof(x, y + self.height, z)          # לא יוצאות מהמערה

    def tick(self, dt):
        sp = self.sp
        px, py, pz = player.p
        dx, dz = px - self.x, pz - self.z
        dist = math.hypot(dx, dz)
        dy = (py + 1.0) - (self.y + self.height / 2)
        self.attack_cd = max(0.0, self.attack_cd - dt)
        chasing = math.hypot(dist, dy) < 18 and not creative and under_roof(px, py + PH, pz)
        if chasing:
            yaw = math.degrees(math.atan2(dx, dz))
        else:
            self.wander_t -= dt
            if self.wander_t <= 0:
                self.wander_yaw = random.uniform(0, 360)
                self.wander_t = random.uniform(2, 5)
            yaw = self.wander_yaw
        diff = (yaw - self.rotation_y + 180) % 360 - 180
        self.rotation_y += diff * min(1, dt * 8)

        moving = False
        if sp['fly']:
            # עין: שומרת מרחק של 6-9 בלוקים ומרחפת בגובה העיניים
            want = 0
            if chasing:
                want = 1 if dist > 9 else (-1 if dist < 6 else 0)
            elif random.random() < 0.5:
                want = 0.4
            r = math.radians(yaw)
            nx = self.x + math.sin(r) * sp['speed'] * dt * want
            nz = self.z + math.cos(r) * sp['speed'] * dt * want
            ny = self.y + (max(-1, min(1, dy)) * dt * 1.5 if chasing else math.sin(self.phase) * dt * 0.3)
            if self.free(nx, ny, nz):
                self.x, self.y, self.z = nx, ny, nz
            self.phase += dt * 3
            self.body.y = 0.4 + math.sin(self.phase) * 0.08
            if chasing and dist < sp['reach'] and self.attack_cd == 0:
                self.attack_cd = sp['cooldown']
                shoot_shard(self)
        else:
            speed = sp['speed'] * (1 if chasing else 0.35)
            if chasing and dist < sp['reach'] * 0.8:
                speed = 0
            r = math.radians(self.rotation_y)
            step = (math.sin(r) * speed * dt, math.cos(r) * speed * dt)
            if speed:
                nx, nz = self.x + step[0], self.z + step[1]
                if self.free(nx, self.y, nz):
                    self.x, self.z = nx, nz
                    moving = True
                elif self.free(nx, self.y + 1.05, nz) and self.free(self.x, self.y + 1.05, self.z):
                    self.y += 1.05                                       # עולה מדרגה
                    self.x, self.z = nx, nz
                    moving = True
                elif not chasing:
                    self.wander_t = 0
            # כבידה
            g, _ = ground_at(self.x, self.z, self.y)
            if self.y > g + 0.001:
                self.vy -= 22 * dt
                self.y = max(g, self.y + self.vy * dt)
            else:
                self.y, self.vy = g, 0.0
            if chasing and math.hypot(dist, dy) < sp['reach'] and self.attack_cd == 0:
                self.attack_cd = sp['cooldown']
                hurt_player(sp['dmg'], self.x, self.z)
        # רגליים
        if moving:
            self.phase += dt * (14 if self.kind == 'beetle' else 7)
            for pv, sign in self.legs:
                pv.rotation_x = math.sin(self.phase) * 30 * sign
        if self.flash > 0:
            self.flash -= dt
            if self.flash <= 0:
                self.setColorScale(1, 1, 1, 1)

    def hurt(self, from_x, from_z, dmg=1):
        self.hp -= dmg
        self.setColorScale(1, 0.35, 0.35, 1)
        self.flash = 0.25
        # הודף לאחור
        a = math.atan2(self.x - from_x, self.z - from_z)
        for _ in range(4):
            nx, nz = self.x + math.sin(a) * 0.25, self.z + math.cos(a) * 0.25
            if self.free(nx, self.y, nz):
                self.x, self.z = nx, nz
        if not self.sp['fly']:
            self.vy = 4
        return self.hp <= 0


monsters = []
shards = []
MAX_MONSTERS = 28


def shoot_shard(src):
    e = part(scene, (0.6, 1.0, 1.0), (0.18, 0.18, 0.18), (src.x, src.y + 0.4, src.z))
    tx, ty, tz = player.p[0], player.p[1] + 1.2, player.p[2]
    d = Vec3(tx - e.x, ty - e.y, tz - e.z)
    if d.length() > 0:
        d = d.normalized()
    shards.append([e, d * 9, 3.0])


def update_shards(dt):
    for sh in shards[:]:
        e, v, life = sh
        e.position += v * dt
        e.rotation_y += dt * 400
        sh[2] -= dt
        px, py, pz = player.p
        hit_player = abs(e.x - px) < 0.5 and abs(e.z - pz) < 0.5 and py - 0.1 < e.y < py + PH
        hit_wall = is_solid(world.get((math.floor(e.x), math.floor(e.y), math.floor(e.z)), AIR))
        if hit_player:
            hurt_player(MONSTER_TYPES['eye']['dmg'], e.x - v.x, e.z - v.z)
        if hit_player or hit_wall or sh[2] <= 0:
            destroy(e)
            shards.remove(sh)


def find_cave_spot():
    """מקום ריק בתוך מערה (עם תקרה מעליו), 12-28 בלוקים מהשחקן."""
    for _ in range(14):
        a = random.uniform(0, 6.28)
        r = random.uniform(9, 26)
        x = int(player.p[0] + math.cos(a) * r)
        z = int(player.p[2] + math.sin(a) * r)
        if not (2 <= x < SIZE - 2 and 2 <= z < SIZE - 2):
            continue
        roof = column_top(x, z) - 4                      # מתעלמים מעצים ומים
        y0 = min(roof, int(player.p[1]) + 12)
        for y in range(y0, 1, -1):
            if world.get((x, y, z)) is None and world.get((x, y + 1, z)) is None \
                    and is_solid(world.get((x, y - 1, z), AIR)) and under_roof(x, y + 2, z):
                return x + 0.5, y, z + 0.5
    return None


def spawn_monster():
    spot = find_cave_spot()
    if spot:
        kind = random.choices(['beetle', 'rockback', 'eye'], weights=[5, 2, 3])[0]
        x, y, z = spot
        if kind == 'eye':
            y += 1.2
        monsters.append(Monster(kind, (x, y, z)))


def clear_monsters():
    for m in monsters:
        destroy(m)
    monsters.clear()
    for sh in shards:
        destroy(sh[0])
    shards.clear()


# ---------------------------------------------------------------- הפעלה
app = Ursina(title='PyCraft', borderless=False)
window.fps_counter.enabled = True
window.exit_button.visible = False

# ---- מסך פתיחה: ממשיכים עולם שמור או מתחילים עולם חדש
def title_screen():
    choice = []
    items = []
    bg_img = Image.new('RGB', (16 * 24, 16 * 14))
    for tx in range(24):
        for ty in range(14):
            bg_img.paste(TILES['dirt'], (tx * 16, ty * 16))
    bg_img = bg_img.point(lambda v: int(v * 0.45))
    items.append(Entity(parent=camera.ui, model='quad', texture=make_texture(bg_img), scale=(1.8, 1.05), z=1))
    items.append(Text(parent=camera.ui, text='PyCraft', origin=(0, 0), y=0.33, scale=4.5))
    saves = list_saves()[:5]

    def pick(data):
        choice.append(data)

    def btn(text, y, data, col):
        b = Button(parent=camera.ui, text=text, scale=(0.62, 0.068), y=y, color=col,
                   highlight_color=color.Color(0.55, 0.55, 0.6, 1), on_click=lambda: pick(data))
        b.text_entity.scale *= 0.9
        items.append(b)
    btn('New World', 0.17, 'new', color.Color(0.2, 0.45, 0.2, 1))
    if saves:
        items.append(Text(parent=camera.ui, text='Continue a saved world:', origin=(0, 0), y=0.075, scale=1.1))
        for i, d in enumerate(saves):
            when = datetime.datetime.fromtimestamp(d['time']).strftime('%d/%m %H:%M')
            where = 'Nether' if d['dim'] == 'nether' else 'Overworld'
            btn(f"World #{d['seed']}   -   {where}   -   saved {when}", 0.0 - i * 0.085, d,
                color.Color(0.3, 0.3, 0.34, 1))
    else:
        items.append(Text(parent=camera.ui, text='(no saved worlds yet)', origin=(0, 0), y=0.06, scale=1,
                          color=color.Color(0.8, 0.8, 0.8, 1)))
    mouse.locked = False
    while not choice:
        app.taskMgr.step()
    for e in items:
        destroy(e)
    msg = Text(parent=camera.ui, text='Loading world...', origin=(0, 0), scale=2)
    for _ in range(3):
        app.taskMgr.step()
    destroy(msg)
    return choice[0]


picked = title_screen()
if picked != 'new':
    LOADED[0] = picked
    set_seed(picked['seed'])
    CHANGES.update({k: dict(v) for k, v in picked['changes'].items()})

print(f'Generating world (seed {SEED})...')
heights = generate()
atlas = build_atlas()
for cx in range(WORLD_CHUNKS):
    for cz in range(WORLD_CHUNKS):
        chunks[(cx, cz)] = Chunk(cx, cz, atlas)
print(f'Done: {len(world):,} blocks')

# נקודת התחלה: גבעה גבוהה קרובה למרכז (כדי שתהיה מתחתיה מערה ענקית)
c = SIZE // 2
best = None
for need in (SEA + 12, SEA + 9, SEA + 6, SEA + 2):
    cands = [(math.hypot(x - c, z - c), x, z) for x in range(14, SIZE - 14) for z in range(14, SIZE - 14)
             if need <= heights[(x, z)] <= SNOW_LINE - 2 and world.get((x, heights[(x, z)] + 1, z)) is None
             and min(heights[(x + dx, z + dz)] for dx in (-4, 0, 4) for dz in (-4, 0, 4)) > SEA + 1]
    if cands:
        _, bx, bz = random.Random(SEED + 5).choice(cands)
        best = (bx, bz)
        break
best = best or (c, c)
spawn_y = max(y for (x, y, z) in world if x == best[0] and z == best[1] and is_solid(world[(x, y, z)])) + 1
player = Player((best[0] + 0.5, spawn_y + 0.01, best[1] + 0.5))

# ---- פורטל בעולם הרגיל: רחבה שטוחה בגובה נקודת ההתחלה, הפורטל 4 בלוקים מולך
sx0, sz0 = best
pg = spawn_y - 1
px0, pz0 = sx0 - 2, sz0 - 4
# יישור עדין סביב הפורטל ונקודת ההתחלה: במרכז שטוח, ומשם השטח עולה או יורד בהדרגה
# אל הגבעות שמסביב - בלי קירות אדמה ישרים
CORE = (px0 - 1, px0 + 4, pz0 - 2, sz0 + 2)        # x0, x1, z0, z1 של האזור השטוח
BLEND = 9                                          # כמה בלוקים לוקח המעבר לשטח הטבעי


def column_top(x, z):
    for y in range(95, 0, -1):
        if world.get((x, y, z)) not in (None, WATER, LOG, LEAVES):
            return y
    return 0


rng_p = random.Random(SEED + 3)
for x in range(CORE[0] - BLEND, CORE[1] + BLEND + 1):
    for z in range(CORE[2] - BLEND, CORE[3] + BLEND + 1):
        if not (1 <= x < SIZE - 1 and 1 <= z < SIZE - 1):
            continue
        ddx = max(CORE[0] - x, 0, x - CORE[1])
        ddz = max(CORE[2] - z, 0, z - CORE[3])
        d = math.hypot(ddx, ddz)
        d += (fbm(x / 4 + 70, z / 4 + 70, 2) - 0.5) * 3 if d > 0 else 0   # שוליים לא עגולים מדי
        t = max(0.0, min(1.0, d / BLEND))
        t = t * t * (3 - 2 * t)                       # מעבר חלק
        orig = column_top(x, z)
        h = round(pg * (1 - t) + orig * t)
        if h == orig and t > 0:
            continue
        top = SAND if h <= SEA + 1 else (SNOW if h > SNOW_LINE else GRASS)
        under = SAND if top == SAND else (STONE if top == SNOW else DIRT)
        # מעל הגובה החדש: אוויר (רק אם חתכנו את הגבעה, כדי לא למחוק עצים סתם)
        if orig > h or t == 0:
            for y in range(h + 1, max(orig, h) + 9):
                if world.get((x, y, z)) not in (None, WATER) or y <= orig:
                    raw_set((x, y, z), AIR)
        for y in range(1, h + 1):
            if y == h:
                b = top
            elif y > h - 3 - (1 if rng_p.random() < 0.4 else 0):
                b = under
            else:
                b = STONE if not is_solid(world.get((x, y, z), AIR)) else world[(x, y, z)]
            if y >= h - 4 or y > orig:
                raw_set((x, y, z), b)

# עצים שנחתכו באמצע: מנקים עלים שנשארו באוויר בלי גזע לידם
for x in range(CORE[0] - BLEND - 2, CORE[1] + BLEND + 3):
    for z in range(CORE[2] - BLEND - 2, CORE[3] + BLEND + 3):
        for y in range(pg - 10, pg + 25):
            if world.get((x, y, z)) == LEAVES:
                near_log = any(world.get((x + a, y + b, z + c)) == LOG
                               for a in range(-2, 3) for b in range(-3, 2) for c in range(-2, 3))
                if not near_log:
                    raw_set((x, y, z), AIR)

build_portal(px0, pg, pz0)          # המסגרת שקועה בקרקע - נכנסים בהליכה

# ממרכזים את השחקן על הרחבה
player = Player((sx0 + 0.5, pg + 1.01, sz0 + 0.5))
# השחקן מתחיל כשהוא מסתכל לכיוון הפורטל
player.yaw = math.degrees(math.atan2(px0 + 2 - player.p[0], pz0 + 0.5 - player.p[2]))
player.pitch = 5


# ---- מערה ענקית מתחת לנקודת ההתחלה, עם מדרגות שיורדות אליה
def top_solid(x, z):
    for y in range(95, 0, -1):
        if is_solid(world.get((x, y, z), AIR)):
            return y
    return 0


def carve_giant_cave(cx, cz):
    rng = random.Random(SEED + 77)
    R = 10                                         # רדיוס אופקי
    roof = max(10, top_solid(cx, cz) - 5)          # גובה הכיפה, 5 בלוקים מתחת לרגליים
    floor = max(2, roof - 9)                       # גובה המערה: עד 10 בלוקים
    mid = (roof + floor) / 2
    ry = (roof - floor) / 2
    air = []
    for x in range(max(1, cx - R - 3), min(SIZE - 1, cx + R + 4)):
        for z in range(max(1, cz - R - 3), min(SIZE - 1, cz + R + 4)):
            # קירות לא סדירים בעזרת רעש
            wob = 0.75 + 0.5 * fbm(x / 7 + 40, z / 7 + 40, 2)
            d = math.hypot(x - cx, z - cz) / (R * wob)
            if d >= 1:
                continue
            h = math.sqrt(1 - d * d)
            lo = int(mid - ry * h * 0.9 + (fbm(x / 5, z / 5 + 9, 2) - 0.5) * 3)
            hi = int(mid + ry * h + (fbm(x / 4 + 9, z / 4, 2) - 0.5) * 3)
            hi = min(hi, top_solid(x, z) - 4)      # תמיד 4 בלוקים לפחות מתחת לפני השטח
            for y in range(max(floor, lo), min(roof, hi) + 1):
                if world.get((x, y, z)) not in (None, BEDROCK):
                    raw_set((x, y, z), AIR)
                    air.append((x, y, z))

    def exposed(p):
        x, y, z = p
        return any(world.get(q) is None for q in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z),
                                                     (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)))

    # עמודי אבן שמחברים רצפה ותקרה
    for _ in range(2):
        px, pz = cx + rng.randint(-R // 2, R // 2), cz + rng.randint(-R // 2, R // 2)
        if math.hypot(px - cx, pz - cz) < 4:
            continue
        r = rng.uniform(1.0, 2.0)
        for x in range(int(px - r), int(px + r) + 1):
            for z in range(int(pz - r), int(pz + r) + 1):
                if (x - px) ** 2 + (z - pz) ** 2 <= r * r:
                    for y in range(floor, roof + 1):
                        if world.get((x, y, z)) is None:
                            raw_set((x, y, z), STONE)

    # נטיפים מהתקרה
    for _ in range(22):
        x, z = cx + rng.randint(-R, R), cz + rng.randint(-R, R)
        y = roof
        while y > floor and world.get((x, y, z)) is not None:
            y -= 1
        if y > floor + 3 and is_solid(world.get((x, y + 1, z), AIR)):
            for k in range(rng.randint(1, 3)):
                raw_set((x, y - k, z), STONE)

    # עפרות על הקירות - הרבה יהלומים שרואים מיד
    walls = [p for p in {q for a in air for q in ((a[0] + 1, a[1], a[2]), (a[0] - 1, a[1], a[2]),
                                                   (a[0], a[1] - 1, a[2]), (a[0], a[1] + 1, a[2]),
                                                   (a[0], a[1], a[2] + 1), (a[0], a[1], a[2] - 1))}
             if world.get(p) in (STONE, DIRT) and exposed(p)]
    rng.shuffle(walls)
    for block, n in ((DIAMOND_ORE, 10), (GOLD_ORE, 10), (IRON_ORE, 18), (COAL_ORE, 25), (GLOWSTONE, 5)):
        for _ in range(n):
            if not walls:
                break
            x, y, z = walls.pop()
            if block == DIAMOND_ORE and y > floor + 3:   # יהלומים בחלק התחתון
                walls.insert(0, (x, y, z))
                continue
            raw_set((x, y, z), block)
            if block != GLOWSTONE:                # כמה בלוקים צמודים - נראה כמו וריד
                for q in ((x + 1, y, z), (x, y - 1, z), (x, y, z + 1)):
                    if world.get(q) == STONE and rng.random() < 0.5:
                        raw_set(q, block)

    # בריכת לבה ובריכת מים ברצפה
    for block, (ox, oz), r in ((LAVA, (rng.choice((-5, 5)), rng.choice((-3, 3))), 1.6),
                               (WATER, (rng.choice((-4, 4)), rng.choice((-5, 5))), 1.9)):
        bx, bz = cx + ox, cz + oz
        for x in range(int(bx - r), int(bx + r) + 1):
            for z in range(int(bz - r), int(bz + r) + 1):
                if (x - bx) ** 2 + (z - bz) ** 2 > r * r:
                    continue
                y = floor
                while y < roof and world.get((x, y, z)) is not None:
                    y += 1
                if y < roof and world.get((x, y + 1, z)) is None:
                    if y - 1 >= 1 and world.get((x, y - 1, z)) not in (None, BEDROCK):
                        raw_set((x, y - 1, z), block)   # שוקעת בלוק אחד לתוך הרצפה
    return roof, floor


def carve_stairs(sx, sz, roof, floor, away):
    """מדרגות של 2 בלוקים רוחב מליד נקודת ההתחלה, למטה אל המערה."""
    dx, dz = away
    px, pz = -dz, dx                               # כיוון הרוחב
    x, z = sx + dx * 2, sz + dz * 2
    y = top_solid(sx, sz)                          # מתחילים בגובה הרחבה
    while y > 2:
        if not (2 <= x < SIZE - 2 and 2 <= z < SIZE - 2):
            break
        for w in (0, 1):
            wx, wz = x + px * w, z + pz * w
            for k in range(1, 4):
                raw_set((wx, y + k, wz), AIR)
            if not is_solid(world.get((wx, y, wz), AIR)):
                raw_set((wx, y, wz), COBBLE)       # המדרגה עצמה
        if y < roof - 1 and world.get((x + dx, y, z + dz)) is None:
            return                                 # הגענו לתוך המערה
        if y <= floor + 1:
            break
        x, z, y = x + dx, z + dz, y - 1
    # לא פגענו במערה - חופרים מנהרה ישרה חזרה אליה
    for _ in range(30):
        x, z = x - dx, z - dz
        hit = False
        for w in (0, 1):
            wx, wz = x + px * w, z + pz * w
            for k in range(1, 4):
                if world.get((wx, y + k, wz)) is None:
                    hit = True
                raw_set((wx, y + k, wz), AIR)
            if not is_solid(world.get((wx, y, wz), AIR)):
                raw_set((wx, y, wz), COBBLE)
        if hit:
            return


sx, sz = math.floor(player.p[0]), math.floor(player.p[2])
cave_roof, cave_floor = carve_giant_cave(sx, sz)
# המדרגות יוצאות לכיוון ההפוך מהפורטל
vx, vz = sx - (px0 + 2), sz - pz0
away = (1 if vx >= 0 else -1, 0) if abs(vx) >= abs(vz) else (0, 1 if vz >= 0 else -1)
carve_stairs(sx, sz, cave_roof, cave_floor, away)
build_portal(px0, pg, pz0)                         # ליתר ביטחון - שהפורטל לא ייפגע
print(f'Giant cave under spawn (roof at y={cave_roof})')
for ch in chunks.values():
    ch.build()

dims = {'overworld': {'world': world, 'keys': chunk_keys,
                      'exit': (px0 + 2.0, pg + 1.01, pz0 + 2.5), 'spawn': player.spawn}}
current_dim = 'overworld'

for _ in range(MAX_MOBS):
    spawn_mob()
print(f'{len(mobs)} animals spawned')

sky = Sky()
OVERWORLD_BG = window.color
portal_overlay = Entity(parent=camera.ui, model='quad', scale=(4, 2), z=-0.5,
                        color=color.Color(0.5, 0.1, 0.9, 0))
loading_text = Text(parent=camera.ui, text='', origin=(0, 0), scale=2, z=-0.6)
portal_time = 0.0
portal_cooldown = 0.0


def make_nether():
    global world, chunk_keys
    world, chunk_keys = {}, {}
    floors = generate_nether()
    c = SIZE // 2
    py = max(NETHER_LAVA + 3, floors[(c, c)])
    clear_box(c - 3, c + 6, py + 1, py + 7, c - 4, c + 4)
    for x in range(c - 3, c + 7):           # משטח אובסידיאן מעל הלבה
        for z in range(c - 4, c + 5):
            raw_set((x, py, z), OBSIDIAN)
    build_portal(c, py, c)
    exit_p = (c + 2.0, py + 1.01, c + 2.5)
    return {'world': world, 'keys': chunk_keys, 'exit': exit_p, 'spawn': exit_p}


def finish_switch(new):
    global world, chunk_keys, current_dim, portal_cooldown
    if new not in dims:
        dims[new] = make_nether()
    d = dims[new]
    world, chunk_keys = d['world'], d['keys']
    current_dim = new
    for ch in chunks.values():
        ch.build()
    nether = new == 'nether'
    sky.enabled = not nether
    window.color = color.Color(0.25, 0.05, 0.04, 1) if nether else OVERWORLD_BG
    for m in mobs:
        m.enabled = not nether
    clear_monsters()
    sync_torches()
    player.spawn = d['spawn']
    player.p = list(d['exit'])
    player.vy = 0
    player.flying = False
    portal_cooldown = 2.0
    loading_text.text = ''
    portal_overlay.color = color.Color(0.5, 0.1, 0.9, 0)


def switch_dimension():
    new = 'nether' if current_dim == 'overworld' else 'overworld'
    loading_text.text = 'Entering the Nether...' if new == 'nether' else 'Returning to the Overworld...'
    invoke(finish_switch, new, delay=0.1)   # נותנים למסך להתעדכן לפני הבנייה
camera.fov = 80
mouse.locked = True

highlight = Entity(model='wireframe_cube', color=color.black, scale=1.006, visible=False)

# כוונת
Entity(parent=camera.ui, model='quad', color=color.white, scale=(0.0025, 0.022))
Entity(parent=camera.ui, model='quad', color=color.white, scale=(0.022, 0.0025))

# ================================================================ מלאי, כלים ויצירה (Crafting)
# ---- כלים: (סוג, מהירות כרייה, דרגה, נזק)
MATERIALS = [('Wooden', 2, 1, 2, PLANKS), ('Stone', 4, 2, 3, COBBLE), ('Iron', 6, 3, 4, 'Iron Ingot'),
             ('Golden', 12, 1, 2, 'Gold Ingot'), ('Diamond', 8, 4, 5, 'Diamond')]
TOOLS = {}
for mat, speed, level, dmg, _ in MATERIALS:
    for kind in ('Pickaxe', 'Axe', 'Shovel', 'Sword'):
        TOOLS[f'{mat} {kind}'] = (kind, speed, level, dmg + (2 if kind == 'Sword' else 0))

# ---- קשיות בלוקים: (קשיות, כלי מתאים, דרגה נדרשת כדי לקבל את הבלוק)
BLOCK_INFO = {
    GRASS: (0.6, 'Shovel', 0), DIRT: (0.5, 'Shovel', 0), SAND: (0.5, 'Shovel', 0),
    SNOW: (0.2, 'Shovel', 0), SOUL_SAND: (0.5, 'Shovel', 0), LEAVES: (0.2, None, 0),
    LOG: (2, 'Axe', 0), PLANKS: (2, 'Axe', 0), CRAFTING_TABLE: (2.5, 'Axe', 0),
    STONE: (1.5, 'Pickaxe', 1), COBBLE: (2, 'Pickaxe', 1), BRICK: (2, 'Pickaxe', 1),
    NETHERRACK: (0.4, 'Pickaxe', 1), COAL_ORE: (3, 'Pickaxe', 1), QUARTZ_ORE: (3, 'Pickaxe', 1),
    NETHER_GOLD: (3, 'Pickaxe', 1), IRON_ORE: (3, 'Pickaxe', 2), GOLD_ORE: (3, 'Pickaxe', 3),
    DIAMOND_ORE: (3, 'Pickaxe', 3), OBSIDIAN: (50, 'Pickaxe', 4), GLOWSTONE: (0.3, None, 0),
    CRAFTER: (3.5, 'Pickaxe', 1), TORCH: (0, None, 0),
    IRON_BLOCK: (5, 'Pickaxe', 2), GOLD_BLOCK: (3, 'Pickaxe', 3), DIAMOND_BLOCK: (5, 'Pickaxe', 3),
    COAL_BLOCK: (5, 'Pickaxe', 1), QUARTZ_BLOCK: (0.8, 'Pickaxe', 1), SANDSTONE: (0.8, 'Pickaxe', 1),
}
DROPS = {STONE: COBBLE, GRASS: DIRT, COAL_ORE: 'Coal', IRON_ORE: 'Iron Ingot', GOLD_ORE: 'Gold Ingot',
         NETHER_GOLD: 'Gold Ingot', DIAMOND_ORE: 'Diamond', QUARTZ_ORE: 'Quartz'}


def item_name(it):
    return NAMES.get(it, '?') if isinstance(it, int) else it


def max_stack(it):
    return 1 if it in TOOLS else 64


# ---- מתכונים
RECIPES = []


def add_recipe(rows, key, result, n=1):
    w = max(len(r) for r in rows)
    pat = [[key[c] if c != ' ' else None for c in r.ljust(w)] for r in rows]
    RECIPES.append((pat, result, n))
    mirror = [list(reversed(r)) for r in pat]
    if mirror != pat:
        RECIPES.append((mirror, result, n))


add_recipe(['L'], {'L': LOG}, PLANKS, 4)
add_recipe(['P', 'P'], {'P': PLANKS}, 'Stick', 4)
add_recipe(['PP', 'PP'], {'P': PLANKS}, CRAFTING_TABLE)
add_recipe(['C', 'S'], {'C': 'Coal', 'S': 'Stick'}, TORCH, 4)
add_recipe(['SS', 'SS'], {'S': SAND}, SANDSTONE)
add_recipe(['QQ', 'QQ'], {'Q': 'Quartz'}, QUARTZ_BLOCK)
add_recipe(['GG', 'GG'], {'G': 'Glowstone Dust'}, GLOWSTONE)
for item, block in (('Iron Ingot', IRON_BLOCK), ('Gold Ingot', GOLD_BLOCK), ('Diamond', DIAMOND_BLOCK),
                    ('Coal', COAL_BLOCK)):
    add_recipe(['XXX', 'XXX', 'XXX'], {'X': item}, block)
    add_recipe(['B'], {'B': block}, item, 9)
for mat, _, _, _, m in MATERIALS:
    k = {'M': m, 'S': 'Stick'}
    add_recipe(['MMM', ' S ', ' S '], k, f'{mat} Pickaxe')
    add_recipe(['MM', 'MS', ' S'], k, f'{mat} Axe')
    add_recipe(['M', 'S', 'S'], k, f'{mat} Shovel')
    add_recipe(['M', 'M', 'S'], k, f'{mat} Sword')
# Crafter: 5 ברזל, שולחן יצירה, ו-2 אבני זוהר (במקום רדסטון)
add_recipe(['III', 'ICI', 'G G'], {'I': 'Iron Ingot', 'C': CRAFTING_TABLE, 'G': GLOWSTONE}, CRAFTER)


def match_recipe(grid, size):
    cells = [[grid[r * size + c][0] if grid[r * size + c] else None for c in range(size)] for r in range(size)]
    rows = [r for r in range(size) if any(cells[r])]
    if not rows:
        return None
    cols = [c for c in range(size) if any(cells[r][c] for r in range(size))]
    pat = [cells[r][cols[0]:cols[-1] + 1] for r in range(rows[0], rows[-1] + 1)]
    for p, res, n in RECIPES:
        if p == pat:
            return res, n
    return None


def consume_grid(grid):
    for i, st in enumerate(grid):
        if st:
            st[1] -= 1
            if st[1] <= 0:
                grid[i] = None


# ---- אייקונים לחפצים (ציור פיקסלים)
HANDLE = (110, 78, 40)
MAT_COL = {'Wooden': (165, 120, 65), 'Stone': (140, 140, 140), 'Iron': (228, 228, 228),
           'Golden': (252, 215, 60), 'Diamond': (80, 232, 222)}


def draw_item(name):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    parts = name.split(' ')
    if name in TOOLS:
        col = MAT_COL[parts[0]]
        kind = parts[1]
        if kind == 'Pickaxe':
            d.line([(2, 13), (10, 5)], fill=HANDLE, width=2)
            d.line([(3, 4), (6, 2), (10, 2), (13, 5), (13, 9)], fill=col, width=2)
        elif kind == 'Axe':
            d.line([(2, 13), (11, 4)], fill=HANDLE, width=2)
            d.polygon([(8, 2), (13, 2), (13, 8), (10, 8), (8, 5)], fill=col)
        elif kind == 'Shovel':
            d.line([(2, 13), (9, 6)], fill=HANDLE, width=2)
            d.polygon([(8, 5), (11, 2), (14, 5), (11, 8)], fill=col)
        else:
            d.line([(5, 10), (13, 2)], fill=col, width=3)
            d.line([(3, 8), (7, 12)], fill=(70, 50, 30), width=2)
            d.line([(1, 14), (4, 11)], fill=HANDLE, width=2)
    elif name == 'Stick':
        d.line([(3, 12), (12, 3)], fill=HANDLE, width=2)
    elif name == 'Coal':
        d.ellipse((3, 4, 12, 12), fill=(32, 32, 32))
        d.point([(5, 6), (8, 7), (6, 9)], fill=(75, 75, 75))
    elif name in ('Iron Ingot', 'Gold Ingot'):
        col = (225, 225, 225) if name.startswith('Iron') else (252, 212, 55)
        d.polygon([(1, 11), (4, 6), (14, 6), (11, 11)], fill=col)
        d.line([(5, 7), (13, 7)], fill=(255, 255, 255))
        d.line([(1, 11), (11, 11)], fill=tuple(int(c * 0.7) for c in col))
    elif name == 'Diamond':
        d.polygon([(8, 2), (14, 7), (8, 14), (2, 7)], fill=(70, 225, 215))
        d.polygon([(8, 4), (11, 7), (8, 9), (5, 7)], fill=(190, 255, 250))
    elif name == 'Quartz':
        d.polygon([(6, 2), (10, 2), (12, 8), (8, 14), (4, 8)], fill=(238, 232, 222))
        d.line([(8, 3), (8, 12)], fill=(200, 190, 180))
    elif name == 'Pork':
        d.ellipse((2, 5, 14, 12), fill=(240, 150, 150))
        d.line([(4, 8), (11, 8)], fill=(210, 110, 115))
    elif name == 'Beef':
        d.ellipse((2, 4, 14, 12), fill=(185, 45, 40))
        d.line([(4, 7), (8, 10)], fill=(240, 230, 220))
        d.line([(9, 6), (11, 8)], fill=(240, 230, 220))
    elif name == 'Wool':
        d.rectangle((2, 2, 13, 13), fill=(238, 238, 235))
        d.point([(4, 5), (9, 4), (6, 9), (11, 10), (3, 11)], fill=(200, 200, 198))
    elif name == 'Glowstone Dust':
        for x, y in ((4, 5), (8, 3), (11, 6), (6, 9), (10, 10), (5, 12), (12, 12), (8, 7)):
            d.rectangle((x, y, x + 1, y + 1), fill=(255, 220, 110))
        d.point([(7, 11), (3, 8), (13, 9)], fill=(230, 170, 60))
    elif name == 'Feather':
        d.line([(3, 13), (12, 3)], fill=(245, 245, 245), width=3)
        d.line([(3, 13), (12, 3)], fill=(170, 170, 170), width=1)
    else:
        d.rectangle((3, 3, 12, 12), fill=(255, 0, 255))
    return img


def draw_torch_icon():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((7, 6, 8, 14), fill=HANDLE)
    d.rectangle((6, 2, 9, 5), fill=(255, 210, 60))
    d.rectangle((7, 3, 8, 4), fill=(255, 250, 200))
    return img


icon_cache = {}


def item_icon(it):
    if it not in icon_cache:
        if it == TORCH:
            img = draw_torch_icon()
        elif isinstance(it, int):
            img = TILES[BLOCK_TEX[it][1]]
        else:
            img = draw_item(it)
        icon_cache[it] = make_texture(img)
    return icon_cache[it]


# ---- המלאי: 36 משבצות (0-8 הם סרגל הבלוקים למטה), כל משבצת היא [חפץ, כמות] או None
inv = [None] * 36
inv[0] = ['Iron Pickaxe', 1]          # מתחילים עם מכוש ברזל
cursor = None                # מה שמחזיקים עם העכבר בתוך מסך המלאי
creative = False


def add_item(it, n=1):
    m = max_stack(it)
    for st in inv:
        if n and st and st[0] == it and st[1] < m:
            k = min(n, m - st[1])
            st[1] += k
            n -= k
    for i in range(36):
        if n and inv[i] is None:
            k = min(n, m)
            inv[i] = [it, k]
            n -= k
    return n


def notify(text, big=False):
    popup = Text(parent=camera.ui, text=text, origin=(0, 0), position=(0, 0.08), scale=1.6 if big else 1.2,
                 color=color.Color(0.4, 1, 1, 1) if big else color.white, z=-0.3)
    popup.animate_y(0.16, duration=1)
    destroy(popup, delay=1.1)


def give(it, n=1):
    left = add_item(it, n)
    if left:
        notify('Inventory full!')
    elif not isinstance(it, int):
        notify(f'+{n} {it}', big=(it == 'Diamond'))
    refresh_all()


# ---- תצוגת משבצת
class SlotView:
    def __init__(self, parent, x, y, size=0.068, z=-0.11):
        self.size = size
        self.bg = Entity(parent=parent, model='quad', color=color.Color(0.42, 0.42, 0.44, 1), scale=size, z=z)
        self.icon = Entity(parent=parent, model='quad', scale=size * 0.78, z=z - 0.01, visible=False)
        self.icon.setTransparency(TransparencyAttrib.M_alpha)
        self.shadow = Text(parent=parent, text='', origin=(0.5, -0.5), scale=0.85, z=z - 0.015,
                           color=color.Color(0.24, 0.24, 0.24, 1))
        self.txt = Text(parent=parent, text='', origin=(0.5, -0.5), scale=0.85, z=z - 0.02)
        self.move(x, y)

    def move(self, x, y):
        self.x, self.y = x, y
        self.bg.position = (x, y, self.bg.z)
        self.icon.position = (x, y, self.icon.z)
        self.txt.position = (x + self.size * 0.48, y - self.size * 0.48, self.txt.z)
        self.shadow.position = (x + self.size * 0.48 + 0.004, y - self.size * 0.48 - 0.004, self.shadow.z)

    def show(self, st):
        if st:
            self.icon.texture = item_icon(st[0])
            self.icon.visible = True
            self.txt.text = self.shadow.text = str(st[1]) if st[1] > 1 else ''
        else:
            self.icon.visible = False
            self.txt.text = self.shadow.text = ''

    def set_enabled(self, v):
        for e in (self.bg, self.icon, self.txt):
            e.enabled = v

    def hit(self, mx, my):
        return self.bg.enabled and abs(mx - self.x) < self.size / 2 and abs(my - self.y) < self.size / 2


# ---- סרגל הבלוקים בתחתית המסך
hud = Entity(parent=camera.ui)
SLOT = 0.075
selected = 0
selector = Entity(parent=hud, model='quad', color=color.white, scale=SLOT * 1.18, z=0.02)
for i in range(9):
    Entity(parent=hud, model='quad', color=Vec4(0.15, 0.15, 0.15, 0.85), scale=SLOT * 1.05,
           position=((i - 4) * SLOT * 1.15, -0.44), z=0.01)
hot_views = [SlotView(hud, (i - 4) * SLOT * 1.15, -0.44, size=SLOT * 0.95, z=0) for i in range(9)]
for v in hot_views:
    v.bg.color = color.Color(0, 0, 0, 0)
name_text = Text(parent=hud, text='', origin=(0, 0), position=(0, -0.335), scale=1.1)


def draw_heart(fill):
    """לב בפיקסלים. fill: 0 ריק, 1 חצי, 2 מלא."""
    shape = ['.XX.XX.', 'XXXXXXX', 'XXXXXXX', '.XXXXX.', '..XXX..', '...X...']
    img = Image.new('RGBA', (9, 8), (0, 0, 0, 0))
    p = img.load()
    for y, row in enumerate(shape):
        for x, ch in enumerate(row):
            if ch == 'X':
                inside = fill == 2 or (fill == 1 and x < 3)
                col = (220, 30, 40, 255) if inside else (60, 20, 20, 255)
                if inside and y == 1 and x in (1, 2):
                    col = (255, 160, 160, 255)
                p[x + 1, y + 1] = col
    for y in range(8):                       # קו מתאר
        for x in range(9):
            if p[x, y][3] == 0 and any(0 <= x + a < 9 and 0 <= y + b < 8 and p[x + a, y + b][3] == 255
                                       and p[x + a, y + b][:3] != (0, 0, 0)
                                       for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p[x, y] = (0, 0, 0, 254)
    return make_texture(img)


HEART_TEX = [draw_heart(i) for i in range(3)]
hearts = []
for i in range(10):
    h = Entity(parent=hud, model='quad', texture=HEART_TEX[2], scale=(0.03, 0.027),
               position=(-0.37 + i * 0.032, -0.385), z=-0.01)
    h.setTransparency(TransparencyAttrib.M_alpha)
    hearts.append(h)
MAX_HP = 20
player_hp = [MAX_HP]
regen_clock = [0.0]
hurt_overlay = Entity(parent=camera.ui, model='quad', scale=(4, 2), z=-0.35, color=color.Color(1, 0, 0, 0))


def refresh_hearts():
    hp = player_hp[0]
    for i, h in enumerate(hearts):
        h.texture = HEART_TEX[2 if hp >= (i + 1) * 2 else (1 if hp == i * 2 + 1 else 0)]


def hurt_player(dmg, from_x, from_z):
    if creative:
        return
    player_hp[0] -= dmg
    regen_clock[0] = -3.0
    hurt_overlay.color = color.Color(1, 0, 0, 0.35)
    hurt_overlay.animate_color(color.Color(1, 0, 0, 0), duration=0.4)
    a = math.atan2(player.p[0] - from_x, player.p[2] - from_z)    # הדיפה
    player.move_axis(0, math.sin(a) * 0.7)
    player.move_axis(2, math.cos(a) * 0.7)
    player.vy = max(player.vy, 4.5)
    if player_hp[0] <= 0:
        notify('You died!', big=True)
        player_hp[0] = MAX_HP
        player.respawn()
    refresh_hearts()
info_text = Text(parent=camera.ui, text='', position=(-0.86, 0.47), scale=0.9)
help_text = Text(parent=camera.ui, text='E = inventory / crafting    F5 = save', position=(-0.86, 0.43), scale=0.8,
                 color=color.Color(1, 1, 0.7, 1))

# ---- מסך היצירה - בדיוק בפריסה של מיינקרפט (176x166 פיקסלים), רשת 3x3
PX = 0.0048                                   # גודל פיקסל אחד של המסך ביחידות של ursina
GRID_POS = [(30 + c * 18, 17 + r * 18) for r in range(3) for c in range(3)]
OUT_POS = (124, 35)
INV_POS = [(8 + c * 18, 142) for c in range(9)] + [(8 + c * 18, 84 + r * 18) for r in range(3) for c in range(9)]


def P(px, py):
    """פיקסל במסך של מיינקרפט -> מיקום על המסך."""
    return (px - 88) * PX, 0.02 + (83 - py) * PX


def draw_gui():
    W, H = 176, 166
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W - 1, H - 1), fill=(198, 198, 198), outline=(0, 0, 0))
    d.line([(1, 1), (W - 3, 1)], fill=(255, 255, 255), width=2)
    d.line([(1, 1), (1, H - 3)], fill=(255, 255, 255), width=2)
    d.line([(3, H - 2), (W - 2, H - 2)], fill=(85, 85, 85), width=2)
    d.line([(W - 2, 3), (W - 2, H - 2)], fill=(85, 85, 85), width=2)
    for x, y in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)):
        d.point((x, y), fill=(0, 0, 0, 0))

    def slot(x, y, size=18):
        d.rectangle((x, y, x + size - 1, y + size - 1), fill=(139, 139, 139))
        d.line([(x, y), (x + size - 2, y)], fill=(55, 55, 55))
        d.line([(x, y), (x, y + size - 2)], fill=(55, 55, 55))
        d.line([(x + 1, y + size - 1), (x + size - 1, y + size - 1)], fill=(255, 255, 255))
        d.line([(x + size - 1, y + 1), (x + size - 1, y + size - 1)], fill=(255, 255, 255))
    for x, y in GRID_POS + INV_POS:
        slot(x - 1, y - 1)
    slot(OUT_POS[0] - 5, OUT_POS[1] - 5, 26)
    d.rectangle((90, 40, 103, 44), fill=(139, 139, 139))          # החץ
    d.polygon([(103, 35), (111, 42), (103, 49)], fill=(139, 139, 139))
    return img


panel = Entity(parent=camera.ui, enabled=False)
Entity(parent=panel, model='quad', texture=make_texture(draw_gui()), scale=(176 * PX, 166 * PX),
       position=(0, 0.02), z=-0.1).setTransparency(TransparencyAttrib.M_alpha)
GUI_TEXT = color.Color(0.25, 0.25, 0.25, 1)
title = Text(parent=panel, text='Crafting', position=P(8, 5), scale=1.0, color=GUI_TEXT, z=-0.12)
Text(parent=panel, text='Inventory', position=P(8, 72), scale=1.0, color=GUI_TEXT, z=-0.12)
hint = Text(parent=panel, text='', origin=(0, 0), position=P(128, 64), scale=0.7, color=GUI_TEXT, z=-0.12)
highlight_ui = Entity(parent=panel, model='quad', color=color.Color(1, 1, 1, 0.45), scale=16 * PX, z=-0.115,
                      visible=False)
tip_bg = Entity(parent=camera.ui, model='quad', color=color.Color(0.07, 0.0, 0.1, 0.94), z=-0.45, visible=False,
                origin=(-0.5, 0.5))
tip_text = Text(parent=camera.ui, text='', scale=0.95, z=-0.46)


class GuiSlot:
    def __init__(self, parent, px, py, kind, idx, z=-0.11):
        self.kind, self.idx = kind, idx
        self.px, self.py = px, py
        x, y = P(px + 8, py + 8)
        self.x, self.y = x, y
        self.icon = Entity(parent=parent, model='quad', scale=16 * PX, position=(x, y, z), visible=False)
        self.icon.setTransparency(TransparencyAttrib.M_alpha)
        self.shadow = Text(parent=parent, text='', origin=(0.5, -0.5), scale=0.95,
                           color=color.Color(0.24, 0.24, 0.24, 1), position=(*P(px + 18.3, py + 18.3), z - 0.01))
        self.txt = Text(parent=parent, text='', origin=(0.5, -0.5), scale=0.95,
                        position=(*P(px + 17.5, py + 17.5), z - 0.02))

    def show(self, st):
        if st:
            self.icon.texture = item_icon(st[0])
            self.icon.visible = True
            self.txt.text = self.shadow.text = str(st[1]) if st[1] > 1 else ''
        else:
            self.icon.visible = False
            self.txt.text = self.shadow.text = ''

    def hit(self, mx, my):
        half = (26 if self.kind == 'out' else 18) * PX / 2
        return abs(mx - self.x) < half and abs(my - self.y) < half


inv_views = [GuiSlot(panel, x, y, 'inv', i) for i, (x, y) in enumerate(INV_POS)]
grid_views = [GuiSlot(panel, x, y, 'grid', i) for i, (x, y) in enumerate(GRID_POS)]
out_view = GuiSlot(panel, *OUT_POS, 'out', 0)
all_views = inv_views + grid_views + [out_view]

# הפריט שמחזיקים עם העכבר
cur_icon = Entity(parent=camera.ui, model='quad', scale=16 * PX, z=-0.4, visible=False)
cur_icon.setTransparency(TransparencyAttrib.M_alpha)
cur_txt = Text(parent=camera.ui, text='', origin=(0.5, -0.5), scale=0.95, z=-0.41)

ui = {'mode': None, 'grid': None, 'size': 3, 'crafter': None}
crafters = {}          # (עולם, מיקום) -> {'grid': [...9], 'out': [חפץ, כמות] או None}
crafter_clock = 0.0
drag = {'left': None, 'slots': []}
last_click = {'t': 0.0, 'view': None}
ignore_up = [False]


def open_ui(mode, pos=None):
    ui['mode'] = mode
    if mode == 'crafter':
        cr = crafters.setdefault((current_dim, pos), {'grid': [None] * 9, 'out': None})
        ui.update(grid=cr['grid'], crafter=cr)
        title.text = 'Crafter'
        hint.text = 'automatic: every 2 sec'
    else:
        ui.update(grid=[None] * 9, crafter=None)
        title.text = 'Crafting'
        hint.text = ''
    panel.enabled = True
    hud.enabled = False
    UI_LOCK[0] = True
    mouse.locked = False
    refresh_all()


def close_ui():
    global cursor
    if ui['mode'] != 'crafter' and ui['grid']:
        for st in ui['grid']:
            if st and add_item(st[0], st[1]):
                notify('Inventory full!')
    if cursor:
        add_item(cursor[0], cursor[1])
        cursor = None
    drag.update(left=None, slots=[])
    ui.update(mode=None, grid=None, crafter=None)
    panel.enabled = False
    hud.enabled = True
    tip_bg.visible = False
    tip_text.text = ''
    cur_icon.visible = False
    cur_txt.text = ''
    UI_LOCK[0] = False
    mouse.locked = True
    refresh_all()


def current_output():
    if ui['crafter']:
        return ui['crafter']['out']
    r = match_recipe(ui['grid'], 3)
    return [r[0], r[1]] if r else None


def container(v):
    return inv if v.kind == 'inv' else ui['grid']


def view_stack(v):
    return current_output() if v.kind == 'out' else container(v)[v.idx]


def refresh_all():
    for i, v in enumerate(hot_views):
        v.show(inv[i])
    st = inv[selected]
    name_text.text = item_name(st[0]) if st else ''
    if ui['mode']:
        for v in all_views:
            v.show(view_stack(v))
        # בזמן גרירה מראים את החלוקה העתידית
        if cursor:
            cur_icon.texture = item_icon(cursor[0])
            cur_icon.visible = True
            cur_txt.text = str(cursor[1]) if cursor[1] > 1 else ''
        else:
            cur_icon.visible = False
            cur_txt.text = ''


def view_at(mx, my):
    for v in all_views:
        if v.hit(mx, my):
            return v
    return None


def click_slot(cont, idx, left):
    global cursor
    st = cont[idx]
    if left:
        if cursor is None:
            cont[idx], cursor = None, st
        elif st is None:
            cont[idx], cursor = cursor, None
        elif st[0] == cursor[0]:
            k = min(cursor[1], max_stack(st[0]) - st[1])
            st[1] += k
            cursor[1] -= k
            if cursor[1] <= 0:
                cursor = None
        else:
            cont[idx], cursor = cursor, st
    else:
        if cursor is None and st:
            half = (st[1] + 1) // 2
            cursor = [st[0], half]
            st[1] -= half
            if st[1] <= 0:
                cont[idx] = None
        elif cursor and (st is None or (st[0] == cursor[0] and st[1] < max_stack(st[0]))):
            if st is None:
                cont[idx] = [cursor[0], 1]
            else:
                st[1] += 1
            cursor[1] -= 1
            if cursor[1] <= 0:
                cursor = None
        elif cursor and st and st[0] != cursor[0]:
            cont[idx], cursor = cursor, st


def move_into(st, indices):
    """מכניס ערימה למשבצות (קודם לערימות זהות, אחר כך לריקות). מחזיר מה שנשאר."""
    m = max_stack(st[0])
    for j in indices:
        o = inv[j]
        if o and o[0] == st[0] and o[1] < m:
            k = min(st[1], m - o[1])
            o[1] += k
            st[1] -= k
            if st[1] == 0:
                return None
    for j in indices:
        if inv[j] is None:
            inv[j] = st
            return None
    return st


def quick_move(v):
    """Shift + לחיצה: מעביר ערימה שלמה למקום אחר, כמו במיינקרפט."""
    cont = container(v)
    st = cont[v.idx]
    if not st:
        return
    cont[v.idx] = None
    if v.kind == 'grid':
        left = move_into(st, list(range(9, 36)) + list(range(9)))
    elif v.idx < 9:
        left = move_into(st, range(9, 36))
    else:
        left = move_into(st, range(9))
    if left:
        cont[v.idx] = left


def collect_all():
    """לחיצה כפולה: אוסף את כל הפריטים מאותו סוג אל העכבר."""
    m = max_stack(cursor[0])
    for cont in (ui['grid'], inv):
        for j, st in enumerate(cont):
            if cursor[1] >= m:
                return
            if st and st[0] == cursor[0]:
                k = min(st[1], m - cursor[1])
                cursor[1] += k
                st[1] -= k
                if st[1] == 0:
                    cont[j] = None


def click_output(shift, to_hotbar=None):
    global cursor
    if ui['crafter']:
        out = ui['crafter']['out']
        if not out:
            return
        if shift:
            left = add_item(out[0], out[1])
            ui['crafter']['out'] = [out[0], left] if left else None
        elif cursor is None:
            cursor, ui['crafter']['out'] = out, None
        elif cursor[0] == out[0]:
            k = min(out[1], max_stack(out[0]) - cursor[1])
            cursor[1] += k
            out[1] -= k
            if out[1] <= 0:
                ui['crafter']['out'] = None
        return
    for _ in range(64 if shift else 1):
        r = match_recipe(ui['grid'], 3)
        if not r:
            return
        res, n = r
        if to_hotbar is not None:
            if inv[to_hotbar] is not None:
                return
            inv[to_hotbar] = [res, n]
        elif shift:
            left = move_into([res, n], list(range(9, 36)) + list(range(9)))
            if left:
                return
        elif cursor is None:
            cursor = [res, n]
        elif cursor[0] == res and cursor[1] + n <= max_stack(res):
            cursor[1] += n
        else:
            return
        consume_grid(ui['grid'])


def can_drop_into(v):
    if v.kind == 'out' or cursor is None:
        return False
    st = container(v)[v.idx]
    return st is None or (st[0] == cursor[0] and st[1] < max_stack(st[0]))


def ui_mouse_down(left):
    mx, my = mouse.position[0], mouse.position[1]
    v = view_at(mx, my)
    if v is None:
        return
    shift = held_keys['left shift'] or held_keys['right shift']
    if v.kind == 'out':
        click_output(shift)
    elif shift and cursor is None:
        quick_move(v)
    else:
        now = time.time()
        if left and cursor and last_click['view'] is v and now - last_click['t'] < 0.3:
            collect_all()
            ignore_up[0] = True
        elif cursor is None:
            click_slot(container(v), v.idx, left)
        else:
            drag.update(left=left, slots=[v])     # מתחילים גרירה - מחליטים כשמשחררים
        last_click.update(t=now, view=v)
    refresh_all()


def ui_mouse_up(left):
    global cursor
    if ignore_up[0]:
        ignore_up[0] = False
        drag.update(left=None, slots=[])
        return
    if drag['left'] is None or drag['left'] != left:
        return
    sl = drag['slots']
    drag.update(left=None, slots=[])
    if len(sl) == 1:
        click_slot(container(sl[0]), sl[0].idx, left)
    elif cursor:
        it = cursor[0]
        m = max_stack(it)
        per = cursor[1] // len(sl) if left else 1
        for v in sl:
            if not cursor:
                break
            cont = container(v)
            have = cont[v.idx][1] if cont[v.idx] else 0
            k = min(per, m - have, cursor[1])
            if k <= 0:
                continue
            cont[v.idx] = [it, have + k]
            cursor[1] -= k
            if cursor[1] <= 0:
                cursor = None
    refresh_all()


def ui_number_key(n):
    """מקש 1-9 מעל משבצת: מחליף אותה עם המשבצת המתאימה בסרגל."""
    v = view_at(mouse.position[0], mouse.position[1])
    if v is None:
        return
    if v.kind == 'out':
        if not ui['crafter']:
            click_output(False, to_hotbar=n)
    else:
        cont = container(v)
        cont[v.idx], inv[n] = inv[n], cont[v.idx]
    refresh_all()


def ui_update():
    mx, my = mouse.position[0], mouse.position[1]
    cur_icon.position = (mx, my, cur_icon.z)
    cur_txt.position = (mx + 8.5 * PX, my - 8.5 * PX, cur_txt.z)
    v = view_at(mx, my)
    # גרירה: מוסיפים משבצות שעוברים עליהן
    if drag['left'] is not None and v and v not in drag['slots'] and can_drop_into(v):
        if drag['left'] is False or len(drag['slots']) < cursor[1]:
            drag['slots'].append(v)
    if v:
        highlight_ui.visible = True
        highlight_ui.position = (v.x, v.y, highlight_ui.z)
        highlight_ui.scale = (24 if v.kind == 'out' else 16) * PX
    else:
        highlight_ui.visible = False
    st = view_stack(v) if v else None
    if st and cursor is None:
        tip_text.text = item_name(st[0])
        tip_text.position = (mx + 0.03, my + 0.035, tip_text.z)
        tip_bg.position = (mx + 0.022, my + 0.045, tip_bg.z)
        tip_bg.scale = (tip_text.width + 0.02, 0.045)
        tip_bg.visible = True
    else:
        tip_text.text = ''
        tip_bg.visible = False


def run_crafters():
    """ה-Crafter עובד לבד: כל 2 שניות מייצר פעם אחת מהמתכון שמונח בו."""
    for cr in crafters.values():
        r = match_recipe(cr['grid'], 3)
        if not r:
            continue
        res, n = r
        out = cr['out']
        if out is None:
            cr['out'] = [res, n]
        elif out[0] == res and out[1] + n <= max_stack(res):
            out[1] += n
        else:
            continue
        consume_grid(cr['grid'])


# ---- כרייה
crack = Entity(model='cube', color=color.Color(0, 0, 0, 0), scale=1.012, shader=unlit_shader, visible=False)
crack.setTransparency(TransparencyAttrib.M_alpha)
mining_pos = None
mining_progress = 0.0


def one_hit():
    """מכוש ברזל שובר כל בלוק במכה אחת."""
    st = inv[selected]
    return bool(st) and st[0] == 'Iron Pickaxe'


def held_tool():
    st = inv[selected]
    return TOOLS.get(st[0]) if st else None


def break_time(b, pos=None):
    if b == DIAMOND_ORE:
        return None                                   # יהלום - אי אפשר לשבור
    if b == BEDROCK and (pos is None or pos[1] == 0):
        return None                                   # רצפת העולם נשארת, שלא ניפול החוצה
    tool = held_tool()
    if creative:
        return 0.05, True
    if tool and tool[0] == 'Pickaxe':                 # מכוש שובר הכול, ומהר
        hardness = BLOCK_INFO.get(b, (3, None, 0))[0]
        return max(0.05, min(hardness, 3) * 1.5 / tool[1]), True
    if b not in BLOCK_INFO:
        return None                                   # סלע יסוד ופורטל - רק עם מכוש
    hardness, kind, need = BLOCK_INFO[b]
    speed, level = 1, 0
    if tool and tool[0] == kind:
        speed, level = tool[1], tool[2]
    elif tool and tool[0] == 'Sword' and b == LEAVES:
        speed = 2
    ok = level >= need
    return max(0.05, hardness * (1.5 if ok else 5) / speed), ok


def break_block(pos):
    b = world.get(pos)
    _, ok = break_time(b, pos)
    set_block(pos, AIR)
    if b == CRAFTER:
        cr = crafters.pop((current_dim, pos), None)
        if cr:
            for st in cr['grid'] + [cr['out']]:
                if st:
                    add_item(st[0], st[1])
    above = (pos[0], pos[1] + 1, pos[2])
    if world.get(above) == TORCH:                       # לפיד בלי תמיכה נופל
        set_block(above, AIR)
        add_item(TORCH)
    if ok or creative:
        if b == LEAVES:
            if random.random() < 0.15:
                give('Stick')
        else:
            if b == GLOWSTONE:
                give('Glowstone Dust', random.randint(2, 4))
            else:
                give(DROPS.get(b, b))
    refresh_all()


def select(i):
    global selected
    selected = i % 9
    selector.position = ((selected - 4) * SLOT * 1.15, -0.44)
    refresh_all()


select(0)
monster_clock = [0.0]
target = (None, None)
target_mob = None
spawn_clock = 0.0


def update():
    global target, target_mob, spawn_clock, portal_time, portal_cooldown, mining_pos, mining_progress
    global crafter_clock
    dt = min(time.dt, 0.05)
    if loading_text.text:
        return
    player.update(dt)

    crafter_clock += dt
    if crafter_clock >= 2:
        crafter_clock = 0
        run_crafters()
        if ui['crafter']:
            refresh_all()

    if ui['mode']:
        ui_update()

    # פורטל: עומדים בתוכו ועוברים
    portal_cooldown = max(0.0, portal_cooldown - dt)
    if player.touching(PORTAL) and portal_cooldown == 0:
        portal_time += dt
        if portal_time > 1.2:
            portal_time = 0
            if ui['mode']:
                close_ui()
            switch_dimension()
            return
    else:
        portal_time = max(0.0, portal_time - dt)
    portal_overlay.color = color.Color(0.5, 0.1, 0.9, min(0.85, portal_time * 0.7))

    # לבה שורפת - חוזרים לנקודת ההתחלה
    if player.touching(LAVA):
        notify('Burned!')
        player.respawn()

    if current_dim == 'overworld':
        for m in mobs:
            m.tick(dt)
        for m in monsters[:]:
            m.tick(dt)
            if math.hypot(m.x - player.p[0], m.z - player.p[2]) > 45 \
                    or not under_roof(m.x, m.y + m.height, m.z):           # רחוק מדי או בחוץ - נעלמת
                monsters.remove(m)
                destroy(m)
        update_shards(dt)
        monster_clock[0] += dt
        if monster_clock[0] > 0.7 and len(monsters) < MAX_MONSTERS:
            monster_clock[0] = 0
            spawn_monster()
    # החלמה איטית: חצי לב כל 3 שניות
    regen_clock[0] += dt
    if regen_clock[0] > 3 and player_hp[0] < MAX_HP:
        regen_clock[0] = 0
        player_hp[0] += 1
        refresh_hearts()
    spawn_clock += dt
    if current_dim == 'overworld' and spawn_clock > 8 and len(mobs) < MAX_MOBS:
        spawn_clock = 0
        spawn_mob(away_from=player.p, tries=10)

    eye = (player.p[0], player.p[1] + EYE, player.p[2])
    fwd = camera.forward
    d = (fwd.x, fwd.y, fwd.z)
    target = raycast(eye, d)
    block_dist = REACH + 1
    if target[0]:
        block_dist = math.dist(eye, [c + 0.5 for c in target[0]]) - 0.5
    target_mob = None
    best = block_dist
    for m in ((mobs + monsters) if current_dim == 'overworld' else ()):
        t = m.hit_distance(eye, d)
        if t is not None and t < best:
            best, target_mob = t, m
    if target_mob:
        target = (None, None)
    if target[0]:
        highlight.visible = True
        highlight.position = Vec3(target[0]) + Vec3(0.5, 0.5, 0.5)
    else:
        highlight.visible = False

    # כרייה: מחזיקים לחיצה שמאלית. כלי מתאים כורה מהר יותר
    mining = (not ui['mode']) and mouse.locked and held_keys['left mouse'] and target[0] and not target_mob \
        and not one_hit()
    bt = break_time(world.get(target[0]), target[0]) if mining else None
    if bt:
        if target[0] != mining_pos:
            mining_pos, mining_progress = target[0], 0.0
        mining_progress += dt / bt[0]
        if mining_progress >= 1:
            break_block(mining_pos)
            mining_pos, mining_progress = None, 0.0
            crack.visible = False
        else:
            crack.visible = True
            crack.position = Vec3(mining_pos) + Vec3(0.5, 0.5, 0.5)
            crack.color = color.Color(0, 0, 0, 0.12 + 0.6 * mining_progress)
    else:
        mining_pos, mining_progress = None, 0.0
        crack.visible = False

    mode = ('FLY ' if player.flying else '') + ('CREATIVE ' if creative else '') + \
           ('NETHER' if current_dim == 'nether' else '')
    info_text.text = f'XYZ {player.p[0]:.1f} {player.p[1]:.1f} {player.p[2]:.1f}  {mode}   World #{SEED}'
    autosave_clock[0] += dt
    if autosave_clock[0] > 60:                       # שמירה אוטומטית כל דקה
        autosave_clock[0] = 0
        save_game(show=False)


def input(key):
    global creative
    if key == 'q' and not ui['mode']:
        application.quit()                           # השמירה קורית אוטומטית ביציאה
    if key == 'f5':
        save_game()
        return
    if ui['mode']:
        if key in ('escape', 'e'):
            close_ui()
        elif key in ('left mouse down', 'right mouse down'):
            ui_mouse_down(key == 'left mouse down')
        elif key in ('left mouse up', 'right mouse up'):
            ui_mouse_up(key == 'left mouse up')
        elif key in '123456789' and len(key) == 1:
            ui_number_key(int(key) - 1)
        return
    if key == 'escape':
        mouse.locked = False
        return
    if key == 'e':
        open_ui('inventory')            # גם במלאי יש רשת 3x3
        return
    if key in ('left mouse down', 'right mouse down') and not mouse.locked:
        mouse.locked = True
        return
    if key == 'left mouse down' and target_mob:
        tool = held_tool()
        if target_mob in monsters:
            # מפלצות: רק חרב פוגעת חזק. יד וכלים אחרים - נזק 1
            dmg = 999 if tool and tool[0] == 'Sword' else 1     # חרב הורגת במכה אחת
            if target_mob.hurt(player.p[0], player.p[2], dmg):
                item, lo, hi = target_mob.sp['drop']
                give(item, random.randint(lo, hi))
                notify('Monster defeated!')
                monsters.remove(target_mob)
                destroy(target_mob)
            return
        dmg = tool[3] if tool else 1
        if target_mob.hurt(player.p[0], player.p[2], dmg):
            give(target_mob.sp['drop'])
            mobs.remove(target_mob)
            destroy(target_mob)
        return
    if key == 'left mouse down' and target[0] and one_hit():
        if break_time(world.get(target[0]), target[0]):     # הכול חוץ מיהלום
            break_block(target[0])
        return
    if key == 'right mouse down' and target[0]:
        b = world.get(target[0])
        if b == CRAFTING_TABLE:
            open_ui('table')
            return
        if b == CRAFTER:
            open_ui('crafter', target[0])
            return
    if key == 'right mouse down' and target[1]:
        st = inv[selected]
        if not st or not isinstance(st[0], int):
            return
        it, pos = st[0], target[1]
        if it == TORCH and not is_solid(world.get((pos[0], pos[1] - 1, pos[2]), AIR)):
            return                                       # לפיד צריך משהו לעמוד עליו
        old = world.get(pos, AIR)
        raw_set(pos, it)
        if collides(*player.p):          # לא מניחים בלוק בתוך השחקן
            raw_set(pos, old)
            return
        set_block(pos, it)
        if not creative:
            st[1] -= 1
            if st[1] <= 0:
                inv[selected] = None
        refresh_all()
    if key in '123456789' and len(key) == 1:
        select(int(key) - 1)
    if key == 'scroll up':
        select(selected - 1)
    if key == 'scroll down':
        select(selected + 1)
    if key == 'f':
        player.flying = not player.flying
        player.vy = 0
    if key == 'r':
        player.respawn()
    if key == 'g':
        creative = not creative
        notify('Creative mode ON' if creative else 'Creative mode OFF')



def save_game(show=True):
    os.makedirs(SAVE_DIR, exist_ok=True)
    data = {
        'version': 1, 'seed': SEED, 'time': datetime.datetime.now().timestamp(),
        'changes': CHANGES, 'dim': current_dim,
        'player': {'p': list(player.p), 'yaw': player.yaw, 'pitch': player.pitch, 'flying': player.flying},
        'hp': player_hp[0], 'inv': inv, 'selected': selected, 'creative': creative,
        'crafters': crafters, 'nether_made': 'nether' in dims,
    }
    tmp = save_path(SEED) + '.tmp'
    with open(tmp, 'wb') as fh:
        fh.write(zlib.compress(pickle.dumps(data)))
    os.replace(tmp, save_path(SEED))                 # לא נהרס אם המשחק נסגר באמצע השמירה
    if show:
        notify('Game saved')


def load_game(d):
    global world, chunk_keys, creative, current_dim
    ow = dims['overworld']
    for pos, b in d['changes'].get('overworld', {}).items():
        raw_set(pos, b)
    if d.get('nether_made'):
        dims['nether'] = make_nether()                # בונה את הנדר (משנה את world זמנית)
        for pos, b in d['changes'].get('nether', {}).items():
            raw_set(pos, b)
        world, chunk_keys = ow['world'], ow['keys']
    for i, st in enumerate(d['inv']):
        inv[i] = st
    crafters.update(d['crafters'])
    creative = d['creative']
    player_hp[0] = d['hp']
    if d['dim'] == 'nether':
        finish_switch('nether')
    else:
        for ch in chunks.values():
            ch.build()
        sync_torches()
    pl = d['player']
    player.p = list(pl['p'])
    player.yaw, player.pitch, player.flying = pl['yaw'], pl['pitch'], pl['flying']
    player.vy = 0
    select(d['selected'])
    refresh_hearts()
    refresh_all()
    notify(f'Welcome back to World #{SEED}!')


if LOADED[0]:
    load_game(LOADED[0])
autosave_clock = [0.0]


def _save_on_exit():
    try:
        save_game(show=False)
        print('Game saved.')
    except Exception as ex:
        print('Could not save:', ex)


atexit.register(_save_on_exit)                       # נשמר גם כשסוגרים את החלון
app.run()