#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הגן הנטוש - Abandoned Garden (גרסה תלת-ממדית, גוף ראשון)
===========================================================
משחק אימה מקורי בהשראת ז'אנר "מסקוט הורור".
אתה הדמות - חוקר גן ילדים נטוש במבט גוף ראשון, אוסף מפתחות,
ונמנע מיצור מסתורי שרודף אחריך כשאתה קרוב מדי אליו.

זהו תוכן מקורי לגמרי - אין בו שימוש בדמויות, שמות, או נכסים
מכל משחק מסחרי קיים.

דרישות התקנה:
    pip install ursina

הרצה:
    python3 garden_escape_3d.py

שליטה:
    W A S D   - תנועה
    עכבר      - מבט סביב (מצלמת גוף ראשון)
    רווח      - קפיצה
    F         - הדלקה/כיבוי פנס
    ESC       - יציאה מהמשחק
"""

import random
import math
from collections import deque

from ursina import (
    Ursina, Entity, application, color, held_keys, camera, window,
    Text, invoke, destroy, mouse, Vec3, time as ursina_time
)
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.lights import PointLight, AmbientLight

# ---------- הגדרות כלליות ----------

ENABLE_MONSTER = False   # בינתיים בלי מפלצת - אפשר להחזיר ל-True בעתיד

CELL_SIZE = 2.2          # גודל כל תא במפה (יחידות עולם)
WALL_HEIGHT = 3
DETECTION_RANGE_ON = 9.0     # טווח גילוי המפלצת כשהפנס דלוק
DETECTION_RANGE_OFF = 4.5    # טווח גילוי כשהפנס כבוי
MONSTER_SPEED = 2.3
CATCH_DISTANCE = 1.3
DOOR_OPEN_DISTANCE = 1.5
KEY_PICKUP_DISTANCE = 1.4

# ---------- מפת המשחק ----------
# 1 = קיר, 0 = רצפה, K = מפתח, D = דלת, P = התחלת שחקן, M = התחלת מפלצת
#
# תכנון: מסדרון מרכזי אופקי (שורה 9) עם 4 חדרים מסביבו:
#   למעלה-שמאל = כיתה   |  למעלה-ימין = חדר משחקים
#   למטה-שמאל  = חדר אוכל |  למטה-ימין = חדר שינה

GAME_MAP = [
    "11111111111111111111111111111",
    "10000000000000100000000000001",
    "10000000000K00100000000000001",
    "10000000000000100000000000001",
    "10000000000000000000000000001",
    "10000000000000100000000000001",
    "10000000000000100000000000001",
    "10000000000000100000000000001",
    "11111110111111111111101111111",
    "1P000000000000M0000000000000D",
    "11111110111111111111101111111",
    "10000000000000100000000000001",
    "100000000000001000000000K0001",
    "10000000000000100000000000001",
    "10000000000000000000000000001",
    "10000000000000100000000000001",
    "10000000000000100000000000001",
    "10000000000000100000000000001",
    "11111111111111111111111111111",
]

MAP_ROWS = len(GAME_MAP)
MAP_COLS = len(GAME_MAP[0])


def grid_to_world(row, col):
    """ממיר קואורדינטת שורה/עמודה במפה למיקום עולם תלת-ממדי (x, z)"""
    x = col * CELL_SIZE
    z = row * CELL_SIZE
    return x, z


def is_walkable(row, col):
    if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
        return GAME_MAP[row][col] != "1"
    return False


def bfs_path(start, goal):
    """מוצא מסלול קצר ביותר בין שני תאים במפה (עבור תנועת המפלצת)"""
    if start == goal:
        return [start]
    visited = {start}
    queue = deque([[start]])
    while queue:
        path = queue.popleft()
        r, c = path[-1]
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if is_walkable(nr, nc) and (nr, nc) not in visited:
                visited.add((nr, nc))
                new_path = path + [(nr, nc)]
                if (nr, nc) == goal:
                    return new_path
                queue.append(new_path)
    return [start]


def world_to_grid(x, z):
    return round(z / CELL_SIZE), round(x / CELL_SIZE)


def rgb255(r, g, b, a=255):
    """ממיר ערכי צבע בטווח 0-255 (מוכר) לטווח 0-1 שה-Ursina מצפה לו בפועל.
    בלי זה, ערכים כמו 235 היו נחתכים ל-1.0 ויוצאים כמעט תמיד לבן."""
    return color.rgba(r / 255, g / 255, b / 255, a / 255)


# ---------- פונקציות ליצירת רהיטים וקישוטים ----------
# כל הפונקציות מקבלות מיקום עולם (x, z) ומחזירות רשימת ישויות (Entity)
# שנוצרו, כדי שנוכל להחזיק בהן רפרנס אם צריך (לא חובה להשתמש בערך המוחזר).

def make_small_table(x, z, top_color=None):
    """שולחן קטן וריבועי - לכיתה"""
    top_color = top_color or rgb255(85, 62, 40)
    top = Entity(model='cube', color=top_color, position=(x, 0.55, z),
                 scale=(1.3, 0.12, 1.3), collider='box')
    leg = Entity(model='cube', color=top_color.tint(-.25), position=(x, 0.27, z),
                 scale=(0.18, 0.55, 0.18))
    return [top, leg]


def make_chair(x, z, facing='south', seat_color=None):
    """כיסא קטן - הכיוון קובע לאיזה צד פונה משענת הגב"""
    seat_color = seat_color or rgb255(65, 50, 36)
    offsets = {'north': (0, -0.24), 'south': (0, 0.24), 'east': (-0.24, 0), 'west': (0.24, 0)}
    dx, dz = offsets.get(facing, (0, 0.24))
    seat = Entity(model='cube', color=seat_color, position=(x, 0.3, z),
                  scale=(0.55, 0.1, 0.55), collider='box')
    back = Entity(model='cube', color=seat_color, position=(x + dx, 0.58, z + dz),
                  scale=(0.55, 0.5, 0.1))
    return [seat, back]


def make_table_with_chairs(x, z, top_color=None, chair_color=None):
    """שולחן קטן מוקף ב-4 כיסאות - מתאים לכיתה"""
    entities = make_small_table(x, z, top_color)
    entities += make_chair(x, z - 1.0, facing='south', seat_color=chair_color)
    entities += make_chair(x, z + 1.0, facing='north', seat_color=chair_color)
    entities += make_chair(x - 1.0, z, facing='east', seat_color=chair_color)
    entities += make_chair(x + 1.0, z, facing='west', seat_color=chair_color)
    return entities


def make_dining_table(x, z, top_color=None, chair_color=None):
    """שולחן אוכל ארוך עם כיסאות משני הצדדים - לחדר האוכל"""
    top_color = top_color or rgb255(78, 54, 34)
    top = Entity(model='cube', color=top_color, position=(x, 0.6, z),
                 scale=(2.8, 0.12, 1.2), collider='box')
    leg1 = Entity(model='cube', color=top_color.tint(-.25), position=(x - 1.15, 0.3, z),
                  scale=(0.18, 0.6, 0.18))
    leg2 = Entity(model='cube', color=top_color.tint(-.25), position=(x + 1.15, 0.3, z),
                  scale=(0.18, 0.6, 0.18))
    entities = [top, leg1, leg2]
    for cx in (x - 0.9, x - 0.3, x + 0.3, x + 0.9):
        entities += make_chair(cx, z - 0.9, facing='south', seat_color=chair_color)
        entities += make_chair(cx, z + 0.9, facing='north', seat_color=chair_color)
    return entities


def make_shelf_with_toys(x, z, shelf_color=None):
    """מדף צעצועים עם קוביות צבעוניות למעלה - לחדר משחקים"""
    shelf_color = shelf_color or rgb255(82, 60, 40)
    shelf = Entity(model='cube', color=shelf_color, position=(x, 0.9, z),
                   scale=(1.8, 1.6, 0.4), collider='box')
    toy_colors = [rgb255(115, 48, 52), rgb255(52, 92, 115), rgb255(118, 102, 42)]
    entities = [shelf]
    for i, tc in enumerate(toy_colors):
        tx = x - 0.6 + i * 0.6
        entities.append(Entity(model='cube', color=tc, position=(tx, 1.55, z), scale=(0.3, 0.3, 0.3)))
    return entities


def make_toy_box(x, z, box_color=None):
    """קופסת צעצועים קטנה בודדת - לפיזור ברחבי חדר המשחקים"""
    box_color = box_color or random.choice([
        rgb255(112, 50, 55), rgb255(50, 95, 112), rgb255(120, 100, 42), rgb255(70, 100, 68)
    ])
    return [Entity(model='cube', color=box_color, position=(x, 0.3, z), scale=(0.55, 0.55, 0.55), collider='box')]


def make_bed(x, z, blanket_color=None):
    """מיטה נמוכה עם כרית - לחדר השינה"""
    blanket_color = blanket_color or rgb255(78, 68, 82)
    base = Entity(model='cube', color=blanket_color, position=(x, 0.2, z),
                  scale=(1.0, 0.35, 1.9), collider='box')
    pillow = Entity(model='cube', color=rgb255(155, 148, 130), position=(x, 0.42, z - 0.75),
                     scale=(0.85, 0.18, 0.4))
    return [base, pillow]


def make_kitchen_counter(x, z, counter_color=None):
    """דלפק/ארון מטבח - לחדר האוכל"""
    counter_color = counter_color or rgb255(95, 92, 88)
    return [Entity(model='cube', color=counter_color, position=(x, 0.5, z),
                    scale=(1.8, 1.0, 0.7), collider='box')]


def make_rug(x, z, w=3.5, d=3.5, rug_color=None):
    """שטיח צבעוני שטוח על הרצפה"""
    rug_color = rug_color or rgb255(95, 48, 55)
    return [Entity(model='plane', color=rug_color, position=(x, 0.02, z), scale=(w, 1, d))]


def make_bulletin_board(x, z, board_color=None):
    """לוח מודעות עומד על רגל - קישוט חופשי, לא צמוד לקיר"""
    board_color = board_color or rgb255(52, 72, 48)
    pole = Entity(model='cube', color=rgb255(52, 40, 30), position=(x, 0.6, z), scale=(0.1, 1.2, 0.1))
    board = Entity(model='cube', color=board_color, position=(x, 1.35, z), scale=(1.3, 0.9, 0.1))
    return [pole, board]


def make_wall_art(row, col, side, size=1.0, canvas_color=None, torn=None):
    """'ציור ילדים' תלוי על קיר - עכשיו דהוי ולעיתים קרוע/חסר, כמו
    שיישאר שנים בבניין נטוש. side קובע על איזה קיר חיצוני: 'north'
    (שורה 0), 'south' (שורה אחרונה), 'west' (עמודה 0) או 'east' (עמודה
    אחרונה). double_sided=True כדי שהציור יהיה גלוי גם אם כיוון הסיבוב
    יצא הפוך ממה שתוכנן."""
    x, z = grid_to_world(row, col)
    if torn is None:
        torn = random.random() < 0.5  # חצי מהתמונות "נעלמו" עם השנים
    canvas_color = canvas_color or random.choice([
        rgb255(110, 85, 40), rgb255(95, 45, 55), rgb255(45, 75, 90),
        rgb255(70, 90, 55), rgb255(100, 65, 35), rgb255(80, 60, 90),
    ])
    frame_color = rgb255(30, 24, 20)
    offset = CELL_SIZE / 2 + 0.06

    if side == 'north':
        pos_frame = (x, 1.6, z + offset)
        pos_canvas = (x, 1.6, z + offset + 0.02)
        rot = (90, 0, 0)
    elif side == 'south':
        pos_frame = (x, 1.6, z - offset)
        pos_canvas = (x, 1.6, z - offset - 0.02)
        rot = (-90, 0, 0)
    elif side == 'west':
        pos_frame = (x + offset, 1.6, z)
        pos_canvas = (x + offset + 0.02, 1.6, z)
        rot = (0, 0, -90)
    else:  # 'east'
        pos_frame = (x - offset, 1.6, z)
        pos_canvas = (x - offset - 0.02, 1.6, z)
        rot = (0, 0, 90)

    frame = Entity(model='plane', color=frame_color, position=pos_frame,
                   scale=(size * 1.3, 1, size * 1.3), rotation=rot, double_sided=True)
    entities = [frame]
    if not torn:
        canvas = Entity(model='plane', color=canvas_color, position=pos_canvas,
                         scale=(size, 1, size), rotation=rot, double_sided=True)
        entities.append(canvas)
    return entities


def make_cobweb(x, y, z, rot=(45, 0, 45), size=0.9):
    """קור עכביש שקוף-למחצה בפינת חדר - קישוט נטישה"""
    web_color = color.rgba(0.75, 0.75, 0.75, 0.35)
    return [Entity(model='plane', color=web_color, position=(x, y, z),
                    scale=(size, 1, size), rotation=rot, double_sided=True)]


def make_dust_speck(x, y, z):
    """גרגר אבק זעיר תלוי באוויר - נראה יפה כשהפנס מאיר עליו"""
    return [Entity(model='sphere', color=color.rgba(0.9, 0.9, 0.85, 0.5), position=(x, y, z), scale=0.05)]


def make_floor_stain(x, z, size=1.2, stain_color=None):
    """כתם לכלוך כהה על הרצפה"""
    stain_color = stain_color or color.rgba(0.05, 0.05, 0.05, 0.4)
    return [Entity(model='plane', color=stain_color, position=(x, 0.03, z), scale=(size, 1, size))]


def make_broken_chair(x, z, chair_color=None):
    """כיסא הפוך/שבור על הרצפה - קישוט נטישה, מוצג בצורה מופשטת"""
    chair_color = chair_color or rgb255(75, 58, 42)
    part1 = Entity(model='cube', color=chair_color, position=(x, 0.12, z),
                   rotation=(0, random.uniform(0, 360), 80), scale=(0.55, 0.1, 0.55))
    part2 = Entity(model='cube', color=chair_color, position=(x + 0.15, 0.3, z + 0.1),
                   rotation=(0, random.uniform(0, 360), 15), scale=(0.5, 0.08, 0.08))
    return [part1, part2]


def make_spilled_toybox(x, z):
    """קופסת צעצועים הפוכה עם צעצועים מפוזרים לידה"""
    box_color = rgb255(80, 62, 45)
    box = Entity(model='cube', color=box_color, position=(x, 0.25, z),
                 rotation=(0, 20, 70), scale=(0.55, 0.55, 0.55))
    toy_colors = [rgb255(140, 55, 55), rgb255(55, 100, 140), rgb255(140, 120, 45)]
    entities = [box]
    for i, tc in enumerate(toy_colors):
        entities.append(Entity(model='cube', color=tc,
                                position=(x + 0.3 + i * 0.25, 0.15, z + 0.2 - i * 0.15),
                                scale=(0.25, 0.25, 0.25)))
    return entities


def make_crack(row, col, side, size=0.5):
    """סדק כהה על קיר - קישוט נטישה נוסף, אותה לוגיקת כיוון כמו ציורי הקיר"""
    x, z = grid_to_world(row, col)
    offset = CELL_SIZE / 2 + 0.04
    crack_color = color.rgba(0.04, 0.04, 0.04, 0.6)

    if side == 'north':
        pos = (x, 1.2, z + offset)
        rot = (90, 0, 0)
    elif side == 'south':
        pos = (x, 1.2, z - offset)
        rot = (-90, 0, 0)
    elif side == 'west':
        pos = (x + offset, 1.2, z)
        rot = (0, 0, -90)
    else:  # 'east'
        pos = (x - offset, 1.2, z)
        rot = (0, 0, 90)

    return [Entity(model='plane', color=crack_color, position=pos,
                    scale=(size * 0.25, 1, size * 2.2), rotation=rot, double_sided=True)]


def make_abandoned_doll(x, z, rot_y=0):
    """בובה נטושה יושבת על הרצפה - קישוט מטריד ושקט, לא נע ולא תוקף"""
    body_color = rgb255(75, 58, 68)
    head_color = rgb255(150, 118, 108)
    body = Entity(model='cube', color=body_color, position=(x, 0.32, z),
                  rotation=(0, rot_y, 0), scale=(0.34, 0.5, 0.24), collider='box')
    head = Entity(model='cube', color=head_color, position=(x, 0.66, z),
                  rotation=(0, rot_y, 0), scale=(0.24, 0.24, 0.22))
    return [body, head]


def make_block_tower(x, z, blocks=5, block_size=0.5):
    """מגדל קוביות צבעוניות - כמו קוביות עץ שילדים בונים איתן"""
    palette = [rgb255(115, 48, 48), rgb255(48, 88, 115), rgb255(122, 105, 42),
               rgb255(60, 100, 60), rgb255(100, 60, 110)]
    entities = []
    for i in range(blocks):
        c = palette[i % len(palette)]
        y = block_size / 2 + i * block_size
        entities.append(Entity(model='cube', color=c, position=(x, y, z),
                                scale=(block_size, block_size, block_size),
                                collider='box' if i == 0 else None))
    return entities


def make_ball(x, z, ball_color=None):
    """כדור צעצוע קטן - קישוט חופשי בחדר המשחקים"""
    ball_color = ball_color or random.choice([
        rgb255(115, 48, 52), rgb255(48, 105, 72), rgb255(120, 100, 42)
    ])
    return [Entity(model='sphere', color=ball_color, position=(x, 0.35, z), scale=0.5)]


def make_wardrobe(x, z, wardrobe_color=None):
    """ארון בגדים גבוה - לחדר השינה"""
    wardrobe_color = wardrobe_color or rgb255(72, 55, 40)
    body = Entity(model='cube', color=wardrobe_color, position=(x, 1.1, z),
                  scale=(1.1, 2.2, 0.6), collider='box')
    handle = Entity(model='cube', color=rgb255(120, 108, 78), position=(x + 0.3, 1.1, z + 0.31),
                     scale=(0.06, 0.4, 0.06))
    return [body, handle]


def make_nightstand(x, z, stand_color=None):
    """שידת לילה קטנה עם מנורה - לחדר השינה"""
    stand_color = stand_color or rgb255(82, 68, 54)
    top = Entity(model='cube', color=stand_color, position=(x, 0.4, z),
                 scale=(0.5, 0.5, 0.5), collider='box')
    lamp_base = Entity(model='cube', color=rgb255(118, 112, 78), position=(x, 0.75, z),
                        scale=(0.15, 0.2, 0.15))
    lamp_shade = Entity(model='cube', color=rgb255(128, 118, 90), position=(x, 0.9, z),
                          scale=(0.25, 0.12, 0.25))
    return [top, lamp_base, lamp_shade]


def make_bookshelf(x, z, shelf_color=None):
    """כוננית ספרים קטנה - לכיתה"""
    shelf_color = shelf_color or rgb255(70, 50, 36)
    shelf = Entity(model='cube', color=shelf_color, position=(x, 0.8, z),
                   scale=(1.4, 1.4, 0.35), collider='box')
    book_colors = [rgb255(100, 45, 45), rgb255(45, 68, 100), rgb255(112, 95, 42), rgb255(50, 88, 58)]
    entities = [shelf]
    for i, bc in enumerate(book_colors):
        bx = x - 0.5 + i * 0.33
        entities.append(Entity(model='cube', color=bc, position=(bx, 1.3, z), scale=(0.12, 0.5, 0.28)))
    return entities


# ---------- בניית האפליקציה ----------

app = Ursina()

window.title = "הגן הנטוש - Abandoned Garden"
window.color = color.black
window.fps_counter.enabled = False
window.exit_button.visible = False

# כיפת "שמיים" כהה גדולה שעוטפת את כל הסצנה - גיבוי לרקע חשוך
# גם אם window.color לא משפיע על הרקע התלת-ממדי בפועל
sky_dome = Entity(
    model='sphere',
    color=rgb255(3, 3, 5),
    scale=400,
    double_sided=True,
)

# תאורה עמומה כמעט אפסית - חושך כמעט מוחלט, הפנס הוא כמעט מקור האור היחיד
AmbientLight(color=rgb255(6, 6, 9, 70))

player_start = (1, 1)
monster_start = (5, 5)
door_cell = (1, 23)
key_cells = []

wall_entities = []

# פלטת צבעים דהויה ומוכתמת - כאילו הצבעים העליזים המקוריים דהו ולכלכו
# עם השנים בבניין נטוש
WALL_PALETTE = [
    rgb255(115, 65, 75),    # ורוד דהוי/מוכתם
    rgb255(125, 105, 55),   # צהוב מלוכלך
    rgb255(60, 90, 100),    # תכלת עמום
    rgb255(70, 95, 70),     # ירוק מודבק/עובש
    rgb255(115, 78, 48),    # כתום חלוד
    rgb255(85, 68, 95),     # סגול דהוי
]

for row in range(MAP_ROWS):
    for col in range(MAP_COLS):
        ch = GAME_MAP[row][col]
        x, z = grid_to_world(row, col)
        if ch == "1":
            base_color = random.choice(WALL_PALETTE)
            w = Entity(
                model='cube',
                color=base_color,
                position=(x, WALL_HEIGHT / 2, z),
                scale=(CELL_SIZE, WALL_HEIGHT, CELL_SIZE),
                collider='box',
            )
            # רצועת קישוט כהה יותר בתחתית הקיר, כמו במשעול פיזי
            trim = Entity(
                model='cube',
                color=base_color.tint(-.35),
                position=(x, 0.25, z),
                scale=(CELL_SIZE * 1.01, 0.5, CELL_SIZE * 1.01),
            )
            wall_entities.append(w)
            wall_entities.append(trim)
        elif ch == "K":
            key_cells.append((row, col))
        elif ch == "D":
            door_cell = (row, col)
        elif ch == "P":
            player_start = (row, col)
        elif ch == "M":
            monster_start = (row, col)

# רצפה גדולה מתחת לכל המפה
floor_w = MAP_COLS * CELL_SIZE
floor_d = MAP_ROWS * CELL_SIZE
floor = Entity(
    model='plane',
    color=rgb255(14, 12, 10),
    position=(floor_w / 2 - CELL_SIZE / 2, 0, floor_d / 2 - CELL_SIZE / 2),
    scale=(floor_w, 1, floor_d),
    collider='box',
    texture='white_cube',
    texture_scale=(MAP_COLS, MAP_ROWS),
)

# תקרה (כדי שלא ייראה שמיים בהיר מלמעלה - עוד אפקט אימה)
ceiling = Entity(
    model='plane',
    color=rgb255(4, 4, 5),
    position=(floor_w / 2 - CELL_SIZE / 2, WALL_HEIGHT, floor_d / 2 - CELL_SIZE / 2),
    scale=(floor_w, 1, floor_d),
    double_sided=True,
    rotation=(180, 0, 0),
)

# ---------- ריהוט וקישוטים ----------
# שים לב: הרהיטים הם קישוט חזותי בלבד ולא נכללים בחישוב המסלול (BFS)
# של המפלצת - כלומר המפלצת (כשתופעל) "מתעלמת" מהם בתנועה שלה, בעוד
# שהשחקן כן מתנגש בהם פיזית (יש להם collider).

# --- כיתה (חדר שמאלי-עליון) ---
tx, tz = grid_to_world(4, 4)
make_table_with_chairs(tx, tz)
bx, bz = grid_to_world(6, 2)
make_bulletin_board(bx, bz)
shelf_x, shelf_z = grid_to_world(2, 10)
make_bookshelf(shelf_x, shelf_z)

# --- חדר משחקים (חדר ימני-עליון) - מלא במגדלי קוביות ומשחקים ---
rx, rz = grid_to_world(4, 21)
make_rug(rx, rz, w=4, d=4, rug_color=rgb255(115, 95, 50))
sx, sz = grid_to_world(1, 19)
make_shelf_with_toys(sx, sz)
for (tr, tc) in [(2, 25), (6, 17), (6, 25), (2, 17)]:
    box_x, box_z = grid_to_world(tr, tc)
    make_toy_box(box_x, box_z)
for (twr, twc) in [(3, 24), (6, 21)]:
    tower_x, tower_z = grid_to_world(twr, twc)
    make_block_tower(tower_x, tower_z, blocks=random.randint(4, 6))
for (bwr, bwc) in [(2, 21), (5, 24), (6, 19)]:
    ball_x, ball_z = grid_to_world(bwr, bwc)
    make_ball(ball_x, ball_z)

# --- חדר אוכל (חדר שמאלי-תחתון) - מלא בשולחנות אוכל ---
for (dr, dc) in [(14, 6), (12, 10), (16, 10)]:
    dtx, dtz = grid_to_world(dr, dc)
    make_dining_table(dtx, dtz)
kx, kz = grid_to_world(12, 2)
make_kitchen_counter(kx, kz)

# --- חדר שינה (חדר ימני-תחתון) ---
bed_positions = [17, 19.6, 22.2]
for bed_col in bed_positions:
    bed_x, bed_z = grid_to_world(12, bed_col)
    make_bed(bed_x, bed_z)
for mid_col in [(bed_positions[0] + bed_positions[1]) / 2, (bed_positions[1] + bed_positions[2]) / 2]:
    ns_x, ns_z = grid_to_world(12, mid_col)
    make_nightstand(ns_x, ns_z)
nap_rug_x, nap_rug_z = grid_to_world(15, 20)
make_rug(nap_rug_x, nap_rug_z, w=3, d=3, rug_color=rgb255(65, 78, 95))
wardrobe_x, wardrobe_z = grid_to_world(14, 26)
make_wardrobe(wardrobe_x, wardrobe_z)

# --- ציורי ילדים על הקירות (בכל החדרים, חלקם דהויים/קרועים) ---
for col in (3, 6, 9, 12):
    make_wall_art(0, col, 'north')       # קיר צפוני של הכיתה
for col in (17, 20, 23, 26):
    make_wall_art(0, col, 'north')       # קיר צפוני של חדר המשחקים
for col in (3, 6, 9, 12):
    make_wall_art(18, col, 'south')      # קיר דרומי של חדר האוכל
for col in (17, 20, 23, 26):
    make_wall_art(18, col, 'south')      # קיר דרומי של חדר השינה

# --- קורי עכביש בפינות החדרים ---
for (cr, cc) in [(1, 1), (1, 12), (1, 16), (1, 26), (17, 1), (17, 12), (17, 16), (17, 26)]:
    cob_x, cob_z = grid_to_world(cr, cc)
    make_cobweb(cob_x, WALL_HEIGHT - 0.3, cob_z)

# --- כתמי לכלוך על הרצפה - מסדרון וחדרים (חלקם בגוון חומני-אדמדם עמוק) ---
STAIN_COLORS = [
    color.rgba(0.04, 0.04, 0.04, 0.45),
    color.rgba(0.10, 0.06, 0.03, 0.5),
    color.rgba(0.14, 0.03, 0.03, 0.4),
]
for (sr, sc) in [(9, 5), (9, 14), (9, 23), (5, 7), (5, 23), (13, 4), (15, 11), (13, 18), (16, 25)]:
    stain_x, stain_z = grid_to_world(sr, sc)
    make_floor_stain(stain_x, stain_z, size=random.uniform(0.9, 1.8),
                      stain_color=random.choice(STAIN_COLORS))

# --- אבק תלוי באוויר - נראה יפה כשהפנס מאיר עליו ---
for _ in range(16):
    room_row = random.uniform(2, 16)
    room_col = random.uniform(2, 26)
    dust_x, dust_z = grid_to_world(room_row, room_col)
    dust_y = random.uniform(0.4, 2.3)
    make_dust_speck(dust_x, dust_y, dust_z)

# --- רהיטים הפוכים/שבורים - סימני נטישה ---
broken_chair_x, broken_chair_z = grid_to_world(3, 6)
make_broken_chair(broken_chair_x, broken_chair_z)
broken_chair2_x, broken_chair2_z = grid_to_world(13, 9)
make_broken_chair(broken_chair2_x, broken_chair2_z)
broken_chair3_x, broken_chair3_z = grid_to_world(9, 10)
make_broken_chair(broken_chair3_x, broken_chair3_z)

# --- קופסת צעצועים שנשפכה בחדר המשחקים ---
spilled_x, spilled_z = grid_to_world(6, 23)
make_spilled_toybox(spilled_x, spilled_z)

# --- סדקים כהים על כמה קירות ---
for (crk_row, crk_col, crk_side) in [(0, 5, 'north'), (0, 24, 'north'), (18, 4, 'south'), (18, 22, 'south')]:
    make_crack(crk_row, crk_col, crk_side)

# --- בובות נטושות - קישוט שקט אך מטריד ---
doll1_x, doll1_z = grid_to_world(16, 17)
make_abandoned_doll(doll1_x, doll1_z, rot_y=35)
doll2_x, doll2_z = grid_to_world(9, 20)
make_abandoned_doll(doll2_x, doll2_z, rot_y=-60)

# ---------- שחקן ----------

px, pz = grid_to_world(*player_start)
player = FirstPersonController(
    position=(px, 1, pz),
    speed=5,
    jump_height=1.5,
)
player.cursor.visible = False

flashlight_on = True
FLASHLIGHT_BASE = (185, 190, 175)  # אור קר, חלש וצר יותר - לא "נעים" בכלל
flashlight = PointLight(parent=camera, position=(0, 0, 0), color=rgb255(*FLASHLIGHT_BASE), y=0)
flashlight.enabled = flashlight_on
flicker_timer = 0.0

# מנסים לצמצם את טווח האור כדי ליצור "בועת אור" קטנה שהחושך לוחץ עליה
# מכל עבר - אם התכונה לא קיימת בגרסת Ursina המותקנת, פשוט מתעלמים
try:
    flashlight.attenuation = Vec3(1, 0.15, 0.9)
except Exception:
    pass

# --- אור חירום אדום מהבהב במסדרון המרכזי (קלאסיקה של סרטי אימה) ---
emergency_light_x, emergency_light_z = grid_to_world(9, 14)
emergency_fixture = Entity(
    model='cube', color=rgb255(60, 10, 10),
    position=(emergency_light_x, WALL_HEIGHT - 0.2, emergency_light_z),
    scale=(0.3, 0.15, 0.3),
)
emergency_light = PointLight(
    position=(emergency_light_x, WALL_HEIGHT - 0.3, emergency_light_z),
    color=rgb255(160, 15, 15),
)
try:
    emergency_light.attenuation = Vec3(1, 0.2, 1.4)
except Exception:
    pass
emergency_flicker_timer = 0.0

# ---------- מפתחות ----------

key_entities = []
for (row, col) in key_cells:
    x, z = grid_to_world(row, col)
    k = Entity(
        model='sphere',
        color=color.yellow,
        position=(x, 1, z),
        scale=0.4,
    )
    key_entities.append(k)

total_keys = len(key_entities)
keys_collected = 0

# ---------- דלת ----------

dx, dz = grid_to_world(*door_cell)
door = Entity(
    model='cube',
    color=color.red.tint(-.3),
    position=(dx, WALL_HEIGHT / 2, dz),
    scale=(CELL_SIZE, WALL_HEIGHT, CELL_SIZE),
    collider='box',
)
door_locked = True

# ---------- מפלצת (מושבתת בינתיים) ----------

monster = None
monster_grid_pos = list(monster_start)
monster_path = []
monster_repath_timer = 0.0
monster_wander_target = monster_start

if ENABLE_MONSTER:
    mx, mz = grid_to_world(*monster_start)
    monster = Entity(
        model='cube',
        color=rgb255(140, 15, 25),
        position=(mx, 1, mz),
        scale=(1.2, 2, 1.2),
    )

# ---------- ממשק משתמש ----------

hud_text = Text(
    text="",
    position=(-0.85, 0.45),
    scale=1.3,
    color=color.white,
    background=True,
)

message_text = Text(
    text="",
    origin=(0, 0),
    position=(0, 0.15),
    scale=2,
    color=color.white,
)

game_state = {"status": "playing"}  # playing / won / lost


def update_hud():
    flashlight_state = "דלוק" if flashlight_on else "כבוי"
    hud_text.text = f"מפתחות: {keys_collected}/{total_keys}   |   פנס (F): {flashlight_state}"


update_hud()


def end_game(status):
    game_state["status"] = status
    player.enabled = False
    mouse.locked = False
    if status == "won":
        message_text.text = "ברחת בהצלחה!\nלחץ ESC ליציאה"
        message_text.color = color.green
    else:
        message_text.text = "נתפסת...\nלחץ ESC ליציאה"
        message_text.color = color.red


def input(key):
    global flashlight_on
    if key == 'f':
        flashlight_on = not flashlight_on
        flashlight.enabled = flashlight_on
        update_hud()
    if key == 'escape':
        application.quit()


def update():
    global keys_collected, door_locked
    global monster_repath_timer, monster_path, monster_wander_target
    global flicker_timer, emergency_flicker_timer

    if game_state["status"] != "playing":
        return

    # --- הבהוב פנס אגרסיבי - חיווט רעוע, כולל "עֵררות חושך" מלאות לרגע ---
    if flashlight_on:
        flicker_timer -= ursina_time.dt
        if flicker_timer <= 0:
            flicker_timer = random.uniform(0.04, 0.3)
            roll = random.random()
            if roll < 0.10:
                factor = 0.0          # כיבוי מוחלט לרגע
            elif roll < 0.32:
                factor = random.uniform(0.2, 0.6)
            else:
                factor = 1.0
            r, g, b = FLASHLIGHT_BASE
            flashlight.color = rgb255(int(r * factor), int(g * factor), int(b * factor))

    # --- פעימת אור החירום האדום במסדרון ---
    emergency_flicker_timer -= ursina_time.dt
    if emergency_flicker_timer <= 0:
        emergency_flicker_timer = random.uniform(0.4, 1.1)
        pulse = random.uniform(0.3, 1.0)
        emergency_light.color = rgb255(int(160 * pulse), int(15 * pulse), int(15 * pulse))

    # --- איסוף מפתחות ---
    for k in list(key_entities):
        if k.enabled and (player.position - k.position).length() < KEY_PICKUP_DISTANCE:
            k.enabled = False
            destroy(k)
            key_entities.remove(k)
            keys_collected += 1
            update_hud()

    if keys_collected >= total_keys and door_locked:
        door_locked = False
        door.color = color.green.tint(-.2)

    # --- בדיקת יציאה מהדלת ---
    if not door_locked and (player.position - door.position).length() < DOOR_OPEN_DISTANCE:
        end_game("won")
        return

    # --- לוגיקת המפלצת (מושבתת בינתיים) ---
    if not ENABLE_MONSTER:
        return

    dist_to_player = (player.position - monster.position).length()
    detection_range = DETECTION_RANGE_ON if flashlight_on else DETECTION_RANGE_OFF

    monster_repath_timer -= ursina_time.dt
    if monster_repath_timer <= 0:
        monster_repath_timer = 0.4  # מחשב מסלול מחדש כל 0.4 שניות
        player_grid = world_to_grid(player.x, player.z)

        if dist_to_player < detection_range:
            # מצב רדיפה - מסלול ישיר לעבר השחקן
            monster_path = bfs_path(tuple(monster_grid_pos), player_grid)
        else:
            # מצב שיטוט - בוחר תא פתוח אקראי בקרבת מקום
            if tuple(monster_grid_pos) == tuple(monster_wander_target) or not monster_path:
                candidates = [
                    (monster_grid_pos[0] + dr, monster_grid_pos[1] + dc)
                    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)]
                    if is_walkable(monster_grid_pos[0] + dr, monster_grid_pos[1] + dc)
                ]
                if candidates:
                    monster_wander_target = random.choice(candidates)
                    monster_path = bfs_path(tuple(monster_grid_pos), monster_wander_target)

    # תזוזה חלקה לאורך המסלול שחושב
    if len(monster_path) > 1:
        next_row, next_col = monster_path[1]
        target_x, target_z = grid_to_world(next_row, next_col)
        cur_x, cur_z = monster.x, monster.z
        dx_, dz_ = target_x - cur_x, target_z - cur_z
        dist_step = math.hypot(dx_, dz_)
        step = MONSTER_SPEED * ursina_time.dt
        if dist_step <= step or dist_step == 0:
            monster.x, monster.z = target_x, target_z
            monster_grid_pos[0], monster_grid_pos[1] = next_row, next_col
            monster_path.pop(0)
        else:
            monster.x += dx_ / dist_step * step
            monster.z += dz_ / dist_step * step

    # --- בדיקת תפיסה ---
    if (player.position - monster.position).length() < CATCH_DISTANCE:
        end_game("lost")


app.run()