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
    Shift     - ספרינט (עם סטמינה)
    עכבר      - מבט סביב (מצלמת גוף ראשון)
    רווח      - קפיצה
    1         - גלי רדיו (כל המפלצות ננעלות עליך)
    2         - מפה טקטית + ירי בלחיצה
    3         - העלמת קירות
    P         - השהיה / המשך
    ESC       - יציאה מהמשחק
"""

import random
import math
from collections import deque

from ursina import (
    Ursina, Entity, application, color, camera, window,
    Text, destroy, mouse, time as ursina_time, held_keys
)
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.lights import AmbientLight

# ---------- הגדרות כלליות ----------

CELL_SIZE = 2.2          # גודל כל תא במפה (יחידות עולם)
WALL_HEIGHT = 3
DETECTION_RANGE = 7.0     # טווח גילוי קבוע של המפלצת
MONSTER_SPEED = 2.3
MONSTER_COUNT = 3
CATCH_DISTANCE = 1.3
DOOR_OPEN_DISTANCE = 1.5
KEY_PICKUP_DISTANCE = 1.4
BASE_TEXTURE = 'white_cube'
WALK_SPEED = 5.0
SPRINT_SPEED = 8.3
MAX_STAMINA = 100.0
STAMINA_DRAIN_PER_SEC = 33.0
STAMINA_REGEN_PER_SEC = 22.0
CHASE_MEMORY_SECONDS = 2.5
RADIO_ALERT_SECONDS = 6.0
RADIO_COOLDOWN_SECONDS = 14.0
MAP_SHOT_COOLDOWN_SECONDS = 1.0
MAP_HIT_RADIUS_CELLS = 1

# ---------- מפת המשחק ----------
# 1 = קיר, 0 = רצפה, K = מפתח, D = דלת, P = התחלת שחקן, M = התחלת מפלצת

GAME_MAP = [
    "1111111111111111111111111",
    "1P000000010000000000000D1",
    "1000000000100000000000001",
    "1011110001101111111011101",
    "1010000001100000001010001",
    "1010111101111110101010101",
    "1P000000010000000000000D1",
    "1000000000100000000000001",
    "1000000000100000000000001",
    "1000000000100000000000001",
    "1010100000K00010101010101",
    "1010101111111010101010101",
    "1010100000000010001010001",
    "1011111011111110111110101",
    "1000000010000000100000101",
    "1011111010111111100111101",
    "1010000M00100000000001001",
    "1010111111011111101101001",
    "1010000000000K00000101001",
    "1011111111111111101101001",
    "1011111110111111111011101",
    "1000000010000000000010001",
    "1011111010111111111010101",
    "1010000010100000000010101",
    "1010111110101111111010101",
    "100000000000000K000000001",
    "1000000000000000000000001",
     "1P000000010000000000000D1",
    "1000000000100000000000001",
    "1011110001101111111011101",
    "1010000001100000001010001",
    "1010111101111110101010101",
    "1010100000K00010101010101",
    "1010101111111010101010101",
    "1010100000000010001010001",
    "1011111011111110111110101",
    "1000000010000000100000101",
    "1011111010111111100111101",
    "1010000M00100000000001001",
    "1010111111011111101101001",
    "1010000000000K00000101001",
    "1011111111111111101101001",
    "1011111110111111111011101",
    "1000000010000000000010001",
    "1011111010111111111010101",
    "1010000010100000000010101",
    "1010111110101111111010101",
    "100000000000000K000000001",
    "1000000000000000000000001",
    "1P000000010000000000000D1",
    "1000000000100000000000001",
    "1011110001101111111011101",
    "1010000001100000001010001",
    "1010111101111110101010101",
    "1P000000010000000000000D1",
    "1000000000100000000000001",
    "1000000000100000000000001",
    "1000000000100000000000001",
    "1010100000K00010101010101",
    "1010101111111010101010101",
    "1010100000000010001010001",
    "1011111011111110111110101",
    "1000000010000000100000101",
    "1011111010111111100111101",
    "1010000M00100000000001001",
    "1010111111011111101101001",
    "1010000000000K00000101001",
    "1011111111111111101101001",
    "1011111110111111111011101",
    "1000000010000000000010001",
    "1011111010111111111010101",
    "1010000010100000000010101",
    "1010111110101111111010101",
    "100000000000000K000000001",
    "1000000000000000000000001",
    "1P000000010000000000000D1",
    "1000000000100000000000001",
    "1011110001101111111011101",
    "1010000001100000001010001",
    "1010111101111110101010101",
    "1010100000K00010101010101",
    "1010101111111010101010101",
    "1010100000000010001010001",
    "1011111011111110111110101",
    "1000000010000000100000101",
    "1011111010111111100111101",
    "1010000M00100000000001001",
    "1010111111011111101101001",
    "1010000000000K00000101001",
    "1011111111111111101101001",
    "1011111110111111111011101",
    "1000000010000000000010001",
    "1011111010111111111010101",
    "1010000010100000000010101",
    "1010111110101111111010101",
    "100000000000000K000000001",
    "1000000000000000000000001",
    "1111111111111111111111111",
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
        if walls_hidden:
            return True
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


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def format_time(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


# ---------- בניית האפליקציה ----------

app = Ursina()

window.title = "הגן הנטוש - Abandoned Garden"
window.color = color.black
window.fps_counter.enabled = False
window.exit_button.visible = False

# תאורה עמומה כללית (אווירת אימה)
AmbientLight(color=color.rgba(20, 20, 28, 90))

player_start = (1, 1)
monster_starts = []
door_cell = (1, 23)
key_cells = []

wall_entities = []

# פלטת צבעים בהשראת גן ילדים - צבעים עליזים שנראים מטרידים תחת התאורה העמומה
WALL_PALETTE = [
    color.rgb(235, 110, 130),   # ורוד
    color.rgb(240, 200, 90),    # צהוב
    color.rgb(110, 170, 220),   # תכלת
    color.rgb(140, 200, 140),   # ירוק מנטה
    color.rgb(230, 150, 90),    # כתום
    color.rgb(180, 130, 210),   # סגול בהיר
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
                texture=BASE_TEXTURE,
                position=(x, WALL_HEIGHT / 2, z),
                scale=(CELL_SIZE, WALL_HEIGHT, CELL_SIZE),
                collider='box',
            )
            # רצועת קישוט כהה יותר בתחתית הקיר, כמו במשעול פיזי
            trim = Entity(
                model='cube',
                color=base_color.tint(-.35),
                texture=BASE_TEXTURE,
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
            monster_starts.append((row, col))

# רצפה גדולה מתחת לכל המפה
floor_w = MAP_COLS * CELL_SIZE
floor_d = MAP_ROWS * CELL_SIZE
floor = Entity(
    model='plane',
    color=color.rgb(20, 18, 24),
    position=(floor_w / 2 - CELL_SIZE / 2, 0, floor_d / 2 - CELL_SIZE / 2),
    scale=(floor_w, 1, floor_d),
    collider='box',
    texture=BASE_TEXTURE,
    texture_scale=(MAP_COLS, MAP_ROWS),
)

# תקרה (כדי שלא ייראה שמיים בהיר מלמעלה - עוד אפקט אימה)
ceiling = Entity(
    model='plane',
    color=color.rgb(8, 8, 10),
    position=(floor_w / 2 - CELL_SIZE / 2, WALL_HEIGHT, floor_d / 2 - CELL_SIZE / 2),
    scale=(floor_w, 1, floor_d),
    texture=BASE_TEXTURE,
    double_sided=True,
    rotation=(180, 0, 0),
)

# ---------- שחקן ----------

px, pz = grid_to_world(*player_start)
player = FirstPersonController(
    position=(px, 1, pz),
    speed=WALK_SPEED,
    jump_height=1.5,
)
player.cursor.visible = False
stamina = MAX_STAMINA

# ---------- מפתחות ----------

key_entities = []
for (row, col) in key_cells:
    x, z = grid_to_world(row, col)
    k = Entity(
        model='sphere',
        color=color.yellow,
        texture=BASE_TEXTURE,
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
    texture=BASE_TEXTURE,
    position=(dx, WALL_HEIGHT / 2, dz),
    scale=(CELL_SIZE, WALL_HEIGHT, CELL_SIZE),
    collider='box',
)
door_locked = True

# ---------- מפלצות ----------

monster_spawn_cells = list(dict.fromkeys(monster_starts))
walkable_cells = [
    (r, c)
    for r in range(MAP_ROWS)
    for c in range(MAP_COLS)
    if GAME_MAP[r][c] != "1" and (r, c) != player_start and (r, c) != door_cell
]
random.shuffle(walkable_cells)
for cell in walkable_cells:
    if len(monster_spawn_cells) >= MONSTER_COUNT:
        break
    if cell not in monster_spawn_cells:
        monster_spawn_cells.append(cell)

if not monster_spawn_cells:
    monster_spawn_cells = [player_start]

monster_spawn_cells = monster_spawn_cells[:MONSTER_COUNT]
monsters = []
for idx, start_cell in enumerate(monster_spawn_cells):
    mx, mz = grid_to_world(*start_cell)
    monster_entity = Entity(
        model='cube',
        color=color.rgb(140, 15 + idx * 18, 25 + idx * 10),
        texture=BASE_TEXTURE,
        position=(mx, 1, mz),
        scale=(1.2, 2, 1.2),
    )
    monsters.append({
        "entity": monster_entity,
        "grid_pos": [start_cell[0], start_cell[1]],
        "path": [],
        "repath_timer": 0.0,
        "wander_target": start_cell,
        "chase_memory": 0.0,
    })

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

hint_text = Text(
    text="",
    origin=(0, 0),
    position=(0, -0.42),
    scale=1.2,
    color=color.rgb(255, 230, 120),
)

radio_text = Text(
    text="",
    origin=(0, 0),
    position=(0, -0.33),
    scale=1.1,
    color=color.rgb(120, 255, 255),
)

radio_wave_fx = Entity(
    parent=camera.ui,
    model='quad',
    color=color.rgba(80, 220, 255, 0),
    texture=BASE_TEXTURE,
    scale=(0.05, 0.05),
    z=0.05,
)

map_panel = Entity(
    parent=camera.ui,
    model='quad',
    color=color.rgba(12, 16, 24, 230),
    texture=BASE_TEXTURE,
    position=(0.32, 0.0),
    scale=(0.62, 0.62),
    collider='box',
    enabled=False,
)

map_border = Entity(
    parent=map_panel,
    model='quad',
    color=color.rgba(70, 120, 170, 170),
    texture=BASE_TEXTURE,
    scale=(1.02, 1.02),
    z=0.01,
)

for r in range(MAP_ROWS):
    for c in range(MAP_COLS):
        cell = GAME_MAP[r][c]
        cell_x = -0.5 + (c + 0.5) / MAP_COLS
        cell_y = 0.5 - (r + 0.5) / MAP_ROWS
        if cell == '1':
            Entity(
                parent=map_panel,
                model='quad',
                color=color.rgba(40, 44, 56, 245),
                texture=BASE_TEXTURE,
                position=(cell_x, cell_y, -0.001),
                scale=(1 / MAP_COLS, 1 / MAP_ROWS),
            )

player_map_dot = Entity(
    parent=map_panel,
    model='quad',
    color=color.azure,
    texture=BASE_TEXTURE,
    scale=(0.018, 0.018),
    z=-0.02,
)

monster_map_dots = [
    Entity(
        parent=map_panel,
        model='circle',
        color=color.rgba(255, 0, 0, 255),
        scale=(0.035, 0.035),
        z=-0.02,
    )
    for i in range(len(monsters))
]

monster_map_labels = [
    Text(
        parent=map_panel,
        text=f"M{i + 1}",
        origin=(0, 0),
        scale=0.55,
        color=color.rgb(255, 0, 0),
        z=-0.05,
    )
    for i in range(len(monsters))
]

map_debug_text = Text(
    parent=map_panel,
    text="",
    origin=(-0.5, 0.5),
    position=(-0.49, 0.49),
    scale=0.75,
    color=color.rgb(255, 120, 80),
)

shot_ping = Entity(
    parent=map_panel,
    model='quad',
    color=color.rgba(255, 235, 90, 0),
    texture=BASE_TEXTURE,
    scale=(0.03, 0.03),
    z=-0.03,
)

map_title_text = Text(
    parent=map_panel,
    text='מפה טקטית',
    origin=(0, 0),
    position=(0, 0.56),
    scale=1.2,
    color=color.rgb(170, 220, 255),
)

map_help_text = Text(
    parent=map_panel,
    text='לחץ עכבר כדי לירות | 2 לסגירה',
    origin=(0, 0),
    position=(0, -0.58),
    scale=0.9,
    color=color.rgb(255, 240, 180),
)

game_state = {"status": "playing"}  # playing / won / lost
elapsed_time = 0.0
danger_level = 0.0
radio_alert_timer = 0.0
radio_cooldown_timer = 0.0
map_visible = False
map_shot_cooldown = 0.0
walls_hidden = False


def update_hud():
    stamina_pct = int((stamina / MAX_STAMINA) * 100)
    danger_pct = int(danger_level * 100)
    radio_label = "מוכן"
    if radio_cooldown_timer > 0:
        radio_label = f"{int(radio_cooldown_timer) + 1}ש׳"
    hud_text.text = (
        f"מפתחות: {keys_collected}/{total_keys}   |   "
        f"סטמינה: {stamina_pct}%   |   "
        f"סכנה: {danger_pct}%   |   "
        f"רדיו: {radio_label}   |   "
        f"זמן: {format_time(elapsed_time)}"
    )


update_hud()


def end_game(status):
    game_state["status"] = status
    player.enabled = False
    mouse.locked = False
    hint_text.text = ""
    radio_text.text = ""
    if status == "won":
        message_text.text = f"ברחת בהצלחה!\nזמן סיום: {format_time(elapsed_time)}\nלחץ ESC ליציאה"
        message_text.color = color.green
    else:
        message_text.text = "נתפסת...\nלחץ ESC ליציאה"
        message_text.color = color.red


def activate_radio_wave():
    global radio_alert_timer, radio_cooldown_timer

    radio_alert_timer = RADIO_ALERT_SECONDS
    radio_cooldown_timer = RADIO_COOLDOWN_SECONDS
    for monster_data in monsters:
        monster_data["chase_memory"] = max(monster_data["chase_memory"], CHASE_MEMORY_SECONDS)
    radio_wave_fx.scale = (0.05, 0.05)
    radio_wave_fx.color = color.rgba(80, 220, 255, 170)
    radio_text.text = "גלי רדיו הופעלו! הם יודעים איפה אתה"


def update_tactical_map_markers():
    player_row, player_col = world_to_grid(player.x, player.z)
    player_col = int(clamp(player_col, 0, MAP_COLS - 1))
    player_row = int(clamp(player_row, 0, MAP_ROWS - 1))

    player_map_dot.position = (
        -0.5 + (player_col + 0.5) / MAP_COLS,
        0.5 - (player_row + 0.5) / MAP_ROWS,
        -0.02,
    )
    debug_lines = [f"M count: {len(monsters)}"]
    for idx, (monster_data, map_dot) in enumerate(zip(monsters, monster_map_dots)):
        monster_entity = monster_data["entity"]
        monster_row, monster_col = world_to_grid(monster_entity.x, monster_entity.z)
        monster_col = int(clamp(monster_col, 0, MAP_COLS - 1))
        monster_row = int(clamp(monster_row, 0, MAP_ROWS - 1))
        debug_lines.append(f"M{idx + 1}: {monster_row},{monster_col}")
        marker_x = -0.5 + (monster_col + 0.5) / MAP_COLS
        marker_y = 0.5 - (monster_row + 0.5) / MAP_ROWS
        map_dot.position = (
            marker_x,
            marker_y,
            -0.02,
        )
        if idx < len(monster_map_labels):
            monster_map_labels[idx].position = (marker_x, marker_y + 0.018)

    map_debug_text.text = "\n".join(debug_lines)


def toggle_tactical_map():
    global map_visible

    if game_state["status"] != "playing":
        return

    map_visible = not map_visible
    map_panel.enabled = map_visible
    player.enabled = not map_visible
    mouse.locked = not map_visible
    if map_visible:
        update_tactical_map_markers()
        radio_text.text = "מפה טקטית פעילה"
    else:
        if radio_text.text == "מפה טקטית פעילה":
            radio_text.text = ""


def shoot_on_map(target_row, target_col):
    global map_shot_cooldown

    if map_shot_cooldown > 0:
        radio_text.text = f"ירי בטעינה: {map_shot_cooldown:.1f}ש׳"
        return

    map_shot_cooldown = MAP_SHOT_COOLDOWN_SECONDS
    shot_ping.position = (
        -0.5 + (target_col + 0.5) / MAP_COLS,
        0.5 - (target_row + 0.5) / MAP_ROWS,
        -0.03,
    )
    shot_ping.scale = (0.03, 0.03)
    shot_ping.color = color.rgba(255, 235, 90, 220)

    hit_count = 0
    walkable_cells = [
        (r, c)
        for r in range(MAP_ROWS)
        for c in range(MAP_COLS)
        if GAME_MAP[r][c] != "1"
    ]

    for monster_data in monsters:
        m_row, m_col = monster_data["grid_pos"]
        hit = (
            abs(target_row - m_row) <= MAP_HIT_RADIUS_CELLS
            and abs(target_col - m_col) <= MAP_HIT_RADIUS_CELLS
        )
        if not hit:
            continue
        hit_count += 1
        if walkable_cells:
            new_row, new_col = random.choice(walkable_cells)
            new_x, new_z = grid_to_world(new_row, new_col)
            monster_data["entity"].x, monster_data["entity"].z = new_x, new_z
            monster_data["grid_pos"][0], monster_data["grid_pos"][1] = new_row, new_col
            monster_data["path"] = []
        monster_data["chase_memory"] = 0.0

    if hit_count > 0:
        radio_text.text = f"פגיעה! הוסטו {hit_count} מפלצות"
        shot_ping.color = color.rgba(110, 255, 120, 220)
    else:
        radio_text.text = "פספוס"


def set_walls_hidden(hidden):
    global walls_hidden

    walls_hidden = hidden
    for wall_entity in wall_entities:
        wall_entity.enabled = not hidden


def input(key):
    global radio_cooldown_timer

    if key == 'p' and game_state["status"] in ("playing", "paused"):
        if game_state["status"] == "playing":
            game_state["status"] = "paused"
            player.enabled = False
            mouse.locked = False
            message_text.text = "השהיה\nלחץ P להמשך"
            message_text.color = color.azure
        else:
            game_state["status"] = "playing"
            player.enabled = True
            mouse.locked = True
            message_text.text = ""
    if key == '1' and game_state["status"] == "playing":
        if radio_cooldown_timer <= 0:
            activate_radio_wave()
        else:
            radio_text.text = f"רדיו בטעינה: {int(radio_cooldown_timer) + 1} שניות"
    if key == '2':
        toggle_tactical_map()
    if key == '3' and game_state["status"] == "playing":
        if not walls_hidden:
            set_walls_hidden(True)
            hint_text.text = "הקירות נעלמו!"
            radio_text.text = "מצב מעבר חופשי הופעל"
    if key == 'left mouse down' and map_visible:
        if map_panel.hovered:
            u = clamp((mouse.x - (map_panel.x - map_panel.scale_x / 2)) / map_panel.scale_x, 0.0, 0.999)
            v = clamp((mouse.y - (map_panel.y - map_panel.scale_y / 2)) / map_panel.scale_y, 0.0, 0.999)
            target_col = int(u * MAP_COLS)
            target_row = int((1.0 - v) * MAP_ROWS)
            shoot_on_map(target_row, target_col)
    if key == 'escape':
        application.quit()


def update():
    global keys_collected, door_locked, stamina, elapsed_time, danger_level
    global radio_alert_timer, radio_cooldown_timer, map_shot_cooldown

    if game_state["status"] == "paused":
        update_hud()
        return

    if game_state["status"] != "playing":
        return

    elapsed_time += ursina_time.dt
    radio_alert_timer = max(0.0, radio_alert_timer - ursina_time.dt)
    radio_cooldown_timer = max(0.0, radio_cooldown_timer - ursina_time.dt)
    map_shot_cooldown = max(0.0, map_shot_cooldown - ursina_time.dt)

    if map_visible:
        update_tactical_map_markers()
        pulse = 1.0 + math.sin(ursina_time.time() * 7.0) * 0.2
        for idx, map_dot in enumerate(monster_map_dots):
            map_dot.scale = (0.035 * pulse, 0.035 * pulse)
            map_dot.color = color.rgba(255, 0, 0, 255)
            if idx < len(monster_map_labels):
                monster_map_labels[idx].scale = 0.55 * pulse
        if shot_ping.color.a > 0:
            shot_ping.scale = (
                shot_ping.scale_x + ursina_time.dt * 0.2,
                shot_ping.scale_y + ursina_time.dt * 0.2,
            )
            shot_ping.color = color.rgba(shot_ping.color.r, shot_ping.color.g, shot_ping.color.b, int(max(0, shot_ping.color.a - ursina_time.dt * 260)))

    # --- ספרינט וסטמינה ---
    is_moving = any(held_keys[k] for k in ('w', 'a', 's', 'd'))
    wants_sprint = held_keys['shift']
    if wants_sprint and is_moving and stamina > 0:
        player.speed = SPRINT_SPEED
        stamina = max(0.0, stamina - STAMINA_DRAIN_PER_SEC * ursina_time.dt)
    else:
        player.speed = WALK_SPEED
        stamina = min(MAX_STAMINA, stamina + STAMINA_REGEN_PER_SEC * ursina_time.dt)

    if stamina <= 1 and wants_sprint:
        hint_text.text = "נגמר לך האוויר..."
    else:
        hint_text.text = ""

    if radio_alert_timer > 0:
        radio_text.color = color.rgba(120, 255, 255, 230)
        radio_wave_fx.scale = (
            radio_wave_fx.scale_x + ursina_time.dt * 1.8,
            radio_wave_fx.scale_y + ursina_time.dt * 1.8,
        )
        fx_alpha = int(clamp(210 - radio_wave_fx.scale_x * 95, 0, 210))
        radio_wave_fx.color = color.rgba(80, 220, 255, fx_alpha)
        if radio_wave_fx.scale_x > 2.4:
            radio_wave_fx.scale = (0.05, 0.05)
    else:
        radio_wave_fx.color = color.rgba(80, 220, 255, 0)
        if radio_cooldown_timer <= 0 and radio_text.text.startswith("רדיו בטעינה"):
            radio_text.text = ""

    # אנימציה קלה למפתחות כדי להבליט אותם
    for i, key_ent in enumerate(key_entities):
        if key_ent.enabled:
            key_ent.rotation_y += (80 + i * 7) * ursina_time.dt
            key_ent.y = 1 + math.sin(ursina_time.time() * 2.7 + i) * 0.18

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
        door.collider = None
        door.y = -WALL_HEIGHT
        hint_text.text = "הדלת נפתחה! רוץ ליציאה"

    # --- בדיקת יציאה מהדלת ---
    door_dist = (player.position - door.position).length()
    if door_locked and door_dist < (DOOR_OPEN_DISTANCE + 1.0):
        hint_text.text = "הדלת נעולה. צריך לאסוף את כל המפתחות"

    if not door_locked and (player.position - door.position).length() < DOOR_OPEN_DISTANCE:
        end_game("won")
        return

    # --- לוגיקת המפלצות ---
    is_radio_alert = radio_alert_timer > 0
    nearest_dist = None
    player_grid = world_to_grid(player.x, player.z)

    for monster_data in monsters:
        monster_entity = monster_data["entity"]
        dist_to_player = (player.position - monster_entity.position).length()
        if nearest_dist is None or dist_to_player < nearest_dist:
            nearest_dist = dist_to_player

        if dist_to_player < DETECTION_RANGE:
            monster_data["chase_memory"] = CHASE_MEMORY_SECONDS
        else:
            monster_data["chase_memory"] = max(0.0, monster_data["chase_memory"] - ursina_time.dt)

        is_chasing = monster_data["chase_memory"] > 0 or is_radio_alert
        monster_data["repath_timer"] -= ursina_time.dt

        if monster_data["repath_timer"] <= 0:
            monster_data["repath_timer"] = 0.25 if is_chasing else 0.45
            if is_chasing:
                # מצב רדיפה - מסלול ישיר לעבר השחקן
                monster_data["path"] = bfs_path(tuple(monster_data["grid_pos"]), player_grid)
            else:
                # מצב שיטוט - בוחר תא פתוח אקראי בקרבת מקום
                if tuple(monster_data["grid_pos"]) == tuple(monster_data["wander_target"]) or not monster_data["path"]:
                    candidates = [
                        (monster_data["grid_pos"][0] + dr, monster_data["grid_pos"][1] + dc)
                        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)]
                        if is_walkable(monster_data["grid_pos"][0] + dr, monster_data["grid_pos"][1] + dc)
                    ]
                    if candidates:
                        monster_data["wander_target"] = random.choice(candidates)
                        monster_data["path"] = bfs_path(tuple(monster_data["grid_pos"]), monster_data["wander_target"])

        # תזוזה חלקה לאורך המסלול שחושב
        if len(monster_data["path"]) > 1:
            next_row, next_col = monster_data["path"][1]
            target_x, target_z = grid_to_world(next_row, next_col)
            cur_x, cur_z = monster_entity.x, monster_entity.z
            dx_, dz_ = target_x - cur_x, target_z - cur_z
            dist_step = math.hypot(dx_, dz_)
            key_progress = keys_collected / total_keys if total_keys else 0
            near_bonus = 0.35 if is_chasing else 0.0
            radio_bonus = 0.45 if is_radio_alert else 0.0
            monster_speed_now = MONSTER_SPEED * (1.0 + key_progress * 0.45 + near_bonus + radio_bonus)
            step = monster_speed_now * ursina_time.dt
            if dist_step <= step or dist_step == 0:
                monster_entity.x, monster_entity.z = target_x, target_z
                monster_data["grid_pos"][0], monster_data["grid_pos"][1] = next_row, next_col
                monster_data["path"].pop(0)
            else:
                monster_entity.x += dx_ / dist_step * step
                monster_entity.z += dz_ / dist_step * step

        # --- בדיקת תפיסה ---
        if (player.position - monster_entity.position).length() < CATCH_DISTANCE:
            end_game("lost")
            return

    if nearest_dist is None:
        danger_level = 0.0
    else:
        danger_level = clamp(1.0 - (nearest_dist / (DETECTION_RANGE * 1.35)), 0.0, 1.0)

    update_hud()


app.run()