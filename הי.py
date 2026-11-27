import math
import random
from collections import deque
from pathlib import Path

import numpy as np
import pygame

# ---------- Constants ----------
SCREEN_W, SCREEN_H = 960, 600
HUD_H = 74
TILE = 32
MAP_COLS, MAP_ROWS = 60, 46
FPS = 60

VISION_RADIUS = 13.0

PLAYER_RADIUS = 0.3
PLAYER_SPEED = 3.4
PLAYER_MAX_HP = 100
PLAYER_ATTACK = 12
PLAYER_ATTACK_RANGE = 1.15
PLAYER_ATTACK_COOLDOWN = 0.45
PLAYER_ATTACK_ANIM = 0.32
PLAYER_HIT_COOLDOWN = 0.5

ENEMY_AGGRO_RANGE = 6.0
ENEMY_LEASH_RANGE = 10.0

HIGH_SCORE_FILE = Path(__file__).with_name("hi_roguelike_highscore.txt")

WALL_COLOR = (46, 40, 58)
WALL_DIM = (28, 25, 34)
FLOOR_COLOR = (40, 35, 50)
FLOOR_DIM = (20, 18, 26)

WALL_TOP = (60, 53, 78)
WALL_TOP_DIM = (33, 29, 41)
WALL_FACE = (37, 32, 47)
WALL_FACE_DIM = (21, 19, 27)
WALL_EDGE = (92, 83, 120)

ENEMY_TYPES = {
    "rat": dict(hp=14, dmg=4, speed=2.0, radius=0.25, color=(140, 110, 86), gold=(2, 6), atk=2),
    "goblin": dict(hp=26, dmg=7, speed=2.4, radius=0.3, color=(96, 156, 78), gold=(4, 10), atk=5),
    "orc": dict(hp=48, dmg=13, speed=1.7, radius=0.38, color=(120, 132, 100), gold=(8, 18), atk=10),
    # base reference stats for sprite building; the real per-floor stats come from cyclops_stats()
    "cyclops": dict(hp=50, dmg=9, speed=1.35, radius=0.5, color=(150, 118, 88), gold=(10, 20), atk=7),
}


def cyclops_stats(floor_num):
    """Stats for the boss guarding the stairs down — soft on floor 1, a fair bit stronger every floor after."""
    return dict(
        hp=50 + 30 * (floor_num - 1),
        dmg=9 + 4 * (floor_num - 1),
        speed=1.35 + 0.035 * (floor_num - 1),
        radius=0.5,
        color=(150, 118, 88),
        gold=(10 + 3 * (floor_num - 1), 20 + 5 * (floor_num - 1)),
        atk=7 + 2 * (floor_num - 1),
    )

ITEM_COLORS = {"potion": (220, 70, 90), "gold": (240, 200, 60), "shard": (120, 180, 240)}


# ---------- Dungeon generation ----------
class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, other, pad=1):
        return (self.x - pad < other.x + other.w and self.x + self.w + pad > other.x
                and self.y - pad < other.y + other.h and self.y + self.h + pad > other.y)


def carve_h_corridor(walls, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        walls[y][x] = False


def carve_v_corridor(walls, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        walls[y][x] = False


def generate_dungeon(floor_num):
    walls = [[True] * MAP_COLS for _ in range(MAP_ROWS)]
    rooms = []
    target_rooms = 8 + min(floor_num, 6)
    attempts = 0
    while len(rooms) < target_rooms and attempts < 400:
        attempts += 1
        w = random.randint(5, 9)
        h = random.randint(4, 7)
        x = random.randint(1, MAP_COLS - w - 2)
        y = random.randint(1, MAP_ROWS - h - 2)
        room = Room(x, y, w, h)
        if any(room.intersects(r) for r in rooms):
            continue
        for ry in range(room.y, room.y + room.h):
            for rx in range(room.x, room.x + room.w):
                walls[ry][rx] = False
        if rooms:
            prev_cx, prev_cy = rooms[-1].center()
            cx, cy = room.center()
            if random.random() < 0.5:
                carve_h_corridor(walls, prev_cx, cx, prev_cy)
                carve_v_corridor(walls, prev_cy, cy, cx)
            else:
                carve_v_corridor(walls, prev_cy, cy, prev_cx)
                carve_h_corridor(walls, prev_cx, cx, cy)
        rooms.append(room)
    return walls, rooms


def is_wall_grid(walls, col, row):
    if col < 0 or col >= MAP_COLS or row < 0 or row >= MAP_ROWS:
        return True
    return walls[row][col]


def can_occupy(walls, x, y, radius):
    for ox in (-radius, radius):
        for oy in (-radius, radius):
            if is_wall_grid(walls, int(x + ox), int(y + oy)):
                return False
    return True


def has_line_of_sight(walls, x0, y0, x1, y1):
    col0, row0 = int(x0), int(y0)
    col1, row1 = int(x1), int(y1)
    dx = abs(col1 - col0)
    dy = abs(row1 - row0)
    sx = 1 if col0 < col1 else -1
    sy = 1 if row0 < row1 else -1
    err = dx - dy
    col, row = col0, row0
    while (col, row) != (col1, row1):
        if (col, row) != (col0, row0) and is_wall_grid(walls, col, row):
            return False
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            col += sx
        if e2 < dx:
            err += dx
            row += sy
    return True


def bfs_path(walls, start, goal):
    if start == goal:
        return []
    frontier = deque([start])
    came_from = {start: None}
    while frontier:
        current = frontier.popleft()
        if current == goal:
            break
        cx, cy = current
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cx + dx, cy + dy)
            if nxt in came_from or is_wall_grid(walls, nxt[0], nxt[1]):
                continue
            came_from[nxt] = current
            frontier.append(nxt)
    if goal not in came_from:
        return None
    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path


def _spot_far_from(room, avoid_xy, tries=14):
    """A random point inside `room`, biased toward the side farthest from `avoid_xy`."""
    best, best_d = None, -1.0
    for _ in range(tries):
        x = random.uniform(room.x + 0.8, room.x + room.w - 0.8)
        y = random.uniform(room.y + 0.8, room.y + room.h - 0.8)
        d = math.hypot(x - avoid_xy[0], y - avoid_xy[1])
        if d > best_d:
            best, best_d = (x, y), d
    return best


def populate_floor(floor_num, rooms):
    player_room = rooms[0]
    start = player_room.center()
    stairs_room = rooms[-1]
    stairs = (stairs_room.center()[0] + 0.5, stairs_room.center()[1] + 0.5)
    candidate_rooms = rooms[1:] or rooms

    kinds = ["rat"]
    if floor_num >= 2:
        kinds.append("goblin")
    if floor_num >= 4:
        kinds.append("orc")

    enemies = []
    for _ in range(min(4 + floor_num * 2, 30)):
        room = random.choice(candidate_rooms)
        x = random.uniform(room.x + 0.8, room.x + room.w - 0.8)
        y = random.uniform(room.y + 0.8, room.y + room.h - 0.8)
        enemies.append(Enemy(random.choice(kinds), x, y))

    # a cyclops boss guards every stairwell down, growing tougher floor after floor
    bx, by = _spot_far_from(stairs_room, stairs)
    enemies.append(Enemy("cyclops", bx, by, stats_override=cyclops_stats(floor_num)))

    items = []
    for _ in range(3 + floor_num // 2):
        room = random.choice(candidate_rooms)
        x = random.uniform(room.x + 0.8, room.x + room.w - 0.8)
        y = random.uniform(room.y + 0.8, room.y + room.h - 0.8)
        kind = random.choices(["potion", "gold", "shard"], weights=[3, 5, 1])[0]
        items.append(Item(kind, x, y))

    return start, stairs, enemies, items


# ---------- Entities ----------
class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.attack = PLAYER_ATTACK
        self.gold = 0
        self.facing = (0, 1)
        self.attack_cooldown = 0.0
        self.attack_flash = 0.0
        self.hit_flash = 0.0
        self.walk_phase = 0.0
        self.moving = False

    def move(self, dx, dy, dt, walls):
        if not dx and not dy:
            self.moving = False
            return
        length = math.hypot(dx, dy)
        dx, dy = dx / length, dy / length
        self.facing = (dx, dy)
        self.moving = True
        self.walk_phase += dt * 14
        nx = self.x + dx * PLAYER_SPEED * dt
        ny = self.y + dy * PLAYER_SPEED * dt
        if can_occupy(walls, nx, self.y, PLAYER_RADIUS):
            self.x = nx
        if can_occupy(walls, self.x, ny, PLAYER_RADIUS):
            self.y = ny

    def take_damage(self, amount):
        if self.hit_flash > 0:
            return
        self.hp -= amount
        self.hit_flash = PLAYER_HIT_COOLDOWN


class Enemy:
    def __init__(self, kind, x, y, stats_override=None):
        stats = stats_override or ENEMY_TYPES[kind]
        self.kind = kind
        self.x, self.y = x, y
        self.hp = stats["hp"]
        self.max_hp = stats["hp"]
        self.dmg = stats["dmg"]
        self.speed = stats["speed"]
        self.radius = stats["radius"]
        self.color = stats["color"]
        self.gold_range = stats["gold"]
        self.atk_reward = stats["atk"]
        self.path = []
        self.path_timer = 0.0
        self.attack_cooldown = 0.0
        self.hit_flash = 0.0
        self.aggro = False
        self.wander_target = None
        self.wander_timer = 0.0
        self.face = (1.0, 0.0)
        self.walk_phase = 0.0
        self.moving = False

    def grid(self):
        return int(self.x), int(self.y)

    def update(self, dt, player, walls):
        px, py = self.x, self.y
        self.path_timer -= dt
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)
        dist_to_player = math.hypot(player.x - self.x, player.y - self.y)
        if dist_to_player < ENEMY_AGGRO_RANGE and has_line_of_sight(walls, self.x, self.y, player.x, player.y):
            self.aggro = True

        if self.aggro:
            if dist_to_player > ENEMY_LEASH_RANGE:
                self.aggro = False
                self.path = []
            else:
                if self.path_timer <= 0:
                    self.path = bfs_path(walls, self.grid(), (int(player.x), int(player.y))) or []
                    self.path_timer = 0.4
                self._follow_path(dt, walls)
                if (dist_to_player < self.radius + PLAYER_RADIUS + 0.25 and self.attack_cooldown <= 0
                        and has_line_of_sight(walls, self.x, self.y, player.x, player.y)):
                    player.take_damage(self.dmg)
                    self.attack_cooldown = 0.9
        else:
            self._wander(dt, walls)

        moved = math.hypot(self.x - px, self.y - py)
        self.moving = moved > 0.0008
        if self.moving:
            self.walk_phase += moved * 4.5

    def _follow_path(self, dt, walls):
        if not self.path:
            return
        tx, ty = self.path[0]
        cx, cy = tx + 0.5, ty + 0.5
        dx, dy = cx - self.x, cy - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.12:
            self.path.pop(0)
            return
        dx, dy = dx / dist, dy / dist
        self.face = (dx, dy)
        nx = self.x + dx * self.speed * dt
        ny = self.y + dy * self.speed * dt
        if can_occupy(walls, nx, self.y, self.radius):
            self.x = nx
        if can_occupy(walls, self.x, ny, self.radius):
            self.y = ny

    def _wander(self, dt, walls):
        self.wander_timer -= dt
        if self.wander_timer <= 0 or self.wander_target is None:
            col, row = self.grid()
            options = [(col + dx, row + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                       if not is_wall_grid(walls, col + dx, row + dy)]
            self.wander_target = random.choice(options) if options else (col, row)
            self.wander_timer = random.uniform(1.0, 2.5)
        tx, ty = self.wander_target
        cx, cy = tx + 0.5, ty + 0.5
        dx, dy = cx - self.x, cy - self.y
        dist = math.hypot(dx, dy)
        if dist > 0.05:
            dx, dy = dx / dist, dy / dist
            self.face = (dx, dy)
            nx = self.x + dx * self.speed * 0.5 * dt
            ny = self.y + dy * self.speed * 0.5 * dt
            if can_occupy(walls, nx, self.y, self.radius):
                self.x = nx
            if can_occupy(walls, self.x, ny, self.radius):
                self.y = ny

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash = 0.15
        self.aggro = True


class Item:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x, self.y = x, y


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "grav", "kind")

    def __init__(self, x, y, vx, vy, life, color, size, grav=0.0, kind="spark"):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size
        self.grav = grav
        self.kind = kind

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.grav * dt
        self.vx *= (1 - 1.6 * dt)
        self.life -= dt


def spawn_burst(particles, x, y, color, n=10, speed=3.5, kind="spark"):
    for _ in range(n):
        a = random.uniform(0, math.tau)
        sp = random.uniform(0.25, 1.0) * speed
        particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp,
                                  random.uniform(0.25, 0.55), color,
                                  random.randint(2, 3), grav=5.0, kind=kind))


class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.timer = 0.8

    def update(self, dt):
        self.y -= dt * 0.6
        self.timer -= dt


def try_attack(player, enemies, walls):
    if player.attack_cooldown > 0:
        return []
    player.attack_cooldown = PLAYER_ATTACK_COOLDOWN
    player.attack_flash = PLAYER_ATTACK_ANIM
    fx, fy = player.facing
    hits = []
    for enemy in enemies:
        dx, dy = enemy.x - player.x, enemy.y - player.y
        dist = math.hypot(dx, dy)
        if dist == 0 or dist > PLAYER_ATTACK_RANGE:
            continue
        if (dx / dist) * fx + (dy / dist) * fy > 0.35 and has_line_of_sight(walls, player.x, player.y, enemy.x, enemy.y):
            enemy.take_damage(player.attack)
            hits.append(enemy)
    return hits


def apply_item(item, player, popups):
    if item.kind == "potion":
        player.hp = min(player.max_hp, player.hp + 30)
        popups.append(FloatingText(item.x, item.y, "+30 HP", (120, 220, 140)))
    elif item.kind == "gold":
        amount = random.randint(5, 15)
        player.gold += amount
        popups.append(FloatingText(item.x, item.y, f"+{amount}g", (240, 200, 60)))
    else:
        player.attack += 3
        popups.append(FloatingText(item.x, item.y, "+3 ATK", (120, 180, 240)))


def compute_visible(walls, player):
    visible = set()
    pcol, prow = int(player.x), int(player.y)
    r = int(VISION_RADIUS) + 1
    for row in range(prow - r, prow + r + 1):
        for col in range(pcol - r, pcol + r + 1):
            if col < 0 or col >= MAP_COLS or row < 0 or row >= MAP_ROWS:
                continue
            if math.hypot(col + 0.5 - player.x, row + 0.5 - player.y) > VISION_RADIUS:
                continue
            if has_line_of_sight(walls, player.x, player.y, col + 0.5, row + 0.5):
                visible.add((col, row))
    return visible


def compute_camera(player):
    view_w = SCREEN_W / TILE
    view_h = (SCREEN_H - HUD_H) / TILE
    cam_x = max(0.0, min(MAP_COLS - view_w, player.x - view_w / 2))
    cam_y = max(0.0, min(MAP_ROWS - view_h, player.y - view_h / 2))
    return cam_x, cam_y


def world_to_screen(cam_x, cam_y, x, y):
    return (x - cam_x) * TILE, (y - cam_y) * TILE + HUD_H


def load_best_floor():
    try:
        return int(HIGH_SCORE_FILE.read_text(encoding="utf-8").strip() or "0")
    except (OSError, ValueError):
        return 0


def save_best_floor(value):
    try:
        HIGH_SCORE_FILE.write_text(str(value), encoding="utf-8")
    except OSError:
        pass


# ---------- Audio (all sound is synthesized in-process; no asset files) ----------
SND_RATE = 44100


def _fade_edges(env, n, ms=6):
    """Ramp the first/last few ms of an envelope to silence so clips don't click."""
    k = min(n // 2, max(1, int(SND_RATE * ms / 1000)))
    if k <= 0:
        return env
    ramp = np.linspace(0.0, 1.0, k)
    env = env.copy()
    env[:k] *= ramp
    env[-k:] *= ramp[::-1]
    return env


def _tone(freq, dur, kind="sine", vol=0.5, decay=None, sweep_to=None, noise_mix=0.0):
    """Render one synthesized layer as a mono float array in [-1, 1]."""
    n = max(1, int(SND_RATE * dur))
    t = np.linspace(0, dur, n, False)
    f = np.linspace(freq, sweep_to if sweep_to is not None else freq, n)
    phase = np.cumsum(f) / SND_RATE
    if kind == "sine":
        w = np.sin(2 * np.pi * phase)
    elif kind == "square":
        w = np.sign(np.sin(2 * np.pi * phase))
    elif kind == "triangle":
        w = 2 * np.abs(2 * (phase - np.floor(phase + 0.5))) - 1
    elif kind == "noise":
        w = np.random.uniform(-1, 1, n)
    else:
        raise ValueError(f"unknown waveform kind: {kind}")
    if noise_mix:
        w = (1 - noise_mix) * w + noise_mix * np.random.uniform(-1, 1, n)
    env = np.exp(-t / decay) if decay else np.ones(n)
    env = _fade_edges(env, n)
    return w * env * vol


def _mix(*layers):
    n = max(len(layer) for layer in layers)
    out = np.zeros(n)
    for layer in layers:
        out[:len(layer)] += layer
    return out


def _to_sound(mono):
    arr = np.clip(mono, -1.0, 1.0)
    arr16 = (arr * 32767).astype(np.int16)
    stereo = np.ascontiguousarray(np.column_stack([arr16, arr16]))
    return pygame.sndarray.make_sound(stereo)


def _sfx_swing():
    return _to_sound(_tone(1500, 0.10, kind="noise", vol=0.20, decay=0.045))


def _sfx_hit():
    body = _tone(190, 0.09, kind="square", vol=0.32, decay=0.05, sweep_to=70)
    crack = _tone(2000, 0.05, kind="noise", vol=0.20, decay=0.02)
    return _to_sound(_mix(body, crack))


def _sfx_hurt():
    return _to_sound(_tone(150, 0.22, kind="square", vol=0.38, decay=0.14, sweep_to=55, noise_mix=0.25))


def _sfx_enemy_death():
    thud = _tone(220, 0.16, kind="triangle", vol=0.30, decay=0.09, sweep_to=50)
    crunch = _tone(900, 0.09, kind="noise", vol=0.22, decay=0.04)
    return _to_sound(_mix(thud, crunch))


def _sfx_player_death():
    return _to_sound(_tone(220, 1.1, kind="sine", vol=0.4, decay=0.55, sweep_to=40))


def _sfx_gold():
    a = _tone(1400, 0.07, kind="square", vol=0.16, decay=0.05)
    b = _tone(1866, 0.09, kind="square", vol=0.14, decay=0.06)
    gap = np.zeros(int(SND_RATE * 0.03))
    return _to_sound(np.concatenate([a, gap, b]))


def _sfx_potion():
    a = _tone(760, 0.16, kind="sine", vol=0.22, decay=0.12)
    b = _tone(1140, 0.20, kind="sine", vol=0.15, decay=0.16)
    return _to_sound(_mix(a, b))


def _sfx_shard():
    a = _tone(1760, 0.14, kind="triangle", vol=0.18, decay=0.10)
    b = _tone(2640, 0.14, kind="sine", vol=0.11, decay=0.10)
    return _to_sound(_mix(a, b))


def _sfx_stairs():
    rumble = _tone(90, 0.9, kind="sine", vol=0.28, decay=0.5, sweep_to=45)
    hiss = _tone(600, 0.5, kind="noise", vol=0.07, decay=0.3)
    return _to_sound(_mix(rumble, hiss))


def _sfx_menu():
    return _to_sound(_tone(880, 0.06, kind="square", vol=0.16, decay=0.045))


def _sfx_confirm():
    a = _tone(660, 0.07, kind="square", vol=0.18, decay=0.05)
    b = _tone(990, 0.10, kind="square", vol=0.18, decay=0.07)
    gap = np.zeros(int(SND_RATE * 0.02))
    return _to_sound(np.concatenate([a, gap, b]))


def _build_ambient_loop(dur=12.0):
    """A slow, seamlessly-looping dungeon pad + soft wind bed.

    Every partial completes a whole number of cycles across `dur` seconds, so
    the waveform lines up with itself at the loop seam and doesn't click.
    """
    n = int(SND_RATE * dur)
    t = np.linspace(0, dur, n, False)

    def locked(cycles, vol, phase=0.0):
        return vol * np.sin(2 * np.pi * (cycles / dur) * t + phase)

    swell = 0.5 + 0.5 * locked(2, 1.0, phase=1.1)
    pad = (locked(22, 0.05) + locked(33, 0.032) + locked(55, 0.018)) * (0.5 + 0.5 * swell)
    drone = locked(11, 0.045)

    rng = np.random.default_rng(7)
    wind = rng.uniform(-1, 1, n)
    k = 500
    wind = np.convolve(wind, np.ones(k) / k, mode="same") * 0.06

    mono = pad + drone + wind
    peak = np.max(np.abs(mono))
    if peak > 1e-6:
        mono = mono / peak * 0.55
    return _to_sound(mono)


class Audio:
    """Thin wrapper around pygame.mixer; degrades silently with no audio device."""

    def __init__(self):
        self.enabled = False
        self.muted = False
        self.sfx = {}
        self.music = None
        self.music_channel = None
        try:
            pygame.mixer.init(frequency=SND_RATE, size=-16, channels=2)
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)
            self.music_channel = pygame.mixer.Channel(0)
            self.sfx = {
                "swing": _sfx_swing(),
                "hit": _sfx_hit(),
                "hurt": _sfx_hurt(),
                "enemy_death": _sfx_enemy_death(),
                "player_death": _sfx_player_death(),
                "gold": _sfx_gold(),
                "potion": _sfx_potion(),
                "shard": _sfx_shard(),
                "stairs": _sfx_stairs(),
                "menu": _sfx_menu(),
                "confirm": _sfx_confirm(),
            }
            self.music = _build_ambient_loop()
            self.enabled = True
        except Exception:
            self.enabled = False

    def start_music(self):
        if self.enabled and self.music_channel:
            self.music_channel.play(self.music, loops=-1, fade_ms=1500)
            self.music_channel.set_volume(0.0 if self.muted else 1.0)

    def play(self, name):
        if self.enabled and not self.muted:
            snd = self.sfx.get(name)
            if snd:
                snd.play()

    def toggle_mute(self):
        if not self.enabled:
            return self.muted
        self.muted = not self.muted
        if self.music_channel:
            self.music_channel.set_volume(0.0 if self.muted else 1.0)
        return self.muted


# ---------- Rendering ----------
def clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def _lerp3(a, b, f):
    return (clamp(a[0] + (b[0] - a[0]) * f),
            clamp(a[1] + (b[1] - a[1]) * f),
            clamp(a[2] + (b[2] - a[2]) * f))


def _hires(size, fn, scale=4):
    """Draw `fn(surf, S)` at `scale`x then smooth-downscale for anti-aliased sprites."""
    S = size * scale
    surf = pygame.Surface((S, S), pygame.SRCALPHA)
    fn(surf, S)
    return pygame.transform.smoothscale(surf, (size, size))


def _shaded_disc(surf, cx, cy, r, top, bot):
    if r < 1:
        return
    grad = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    for i in range(r * 2):
        grad.fill((*_lerp3(top, bot, i / (r * 2 - 1)), 255), (0, i, r * 2, 1))
    m = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(m, (255, 255, 255, 255), (r, r), r)
    grad.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(grad, (cx - r, cy - r))


def _tint_white(spr):
    c = spr.copy()
    c.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return c


WALK_FRAMES = 6
ATK_FRAMES = 5

# ---- selectable knight skins (palette + optional cape) ----
SKINS = [
    {"name": "Dark Knight",
     "pal": dict(hi=(176, 178, 192), mid=(96, 98, 112), dk=(44, 44, 56), edge=(15, 15, 21),
                 accent=(214, 218, 232), plume=(24, 22, 28), cape=(92, 42, 120))},
    {"name": "Warlord",
     "pal": dict(hi=(224, 150, 86), mid=(168, 96, 50), dk=(96, 50, 26), edge=(33, 19, 10),
                 accent=(240, 206, 130), plume=(30, 20, 16), cape=(150, 58, 30))},
    {"name": "Black Baron",
     "pal": dict(hi=(112, 114, 126), mid=(54, 54, 62), dk=(24, 24, 30), edge=(8, 8, 12),
                 accent=(208, 212, 226), plume=(18, 16, 20), cape=(152, 28, 32))},
    {"name": "Templar",
     "pal": dict(hi=(200, 202, 214), mid=(122, 124, 136), dk=(60, 60, 70), edge=(18, 18, 24),
                 accent=(44, 44, 52), plume=(236, 236, 240), cape=(238, 238, 240))},
    {"name": "Lion Knight",
     "pal": dict(hi=(224, 226, 236), mid=(150, 152, 166), dk=(84, 86, 98), edge=(26, 26, 34),
                 accent=(232, 200, 120), plume=(206, 52, 48), cape=None)},
]


def _spr_knight(pal, hurt=False, phase=0.0, atk=None):
    """Top-down knight in full plate, facing east.

    `pal` is a skin palette dict (hi/mid/dk/edge/accent/plume/cape). `phase` in
    [0,1) drives the walk cycle. `atk` in [0,1], when given, drives a sword-swing
    pose (wind-up -> follow-through) instead of the resting blade.
    """
    swing = math.sin(phase * math.tau)

    def fn(s, S):
        c = S // 2
        u = S * 0.01
        lw = max(1, int(1.6 * u))

        def tint(col):
            return _lerp3(col, (214, 92, 82), 0.55) if hurt else col

        mtl_hi, mtl, mtl_dk = tint(pal["hi"]), tint(pal["mid"]), tint(pal["dk"])
        edge = pal["edge"]
        gold = pal["accent"]
        plume = pal["plume"]
        plume_hi = _lerp3(plume, (255, 255, 255), 0.32)
        cape_col = pal["cape"]
        glim = (255, 194, 104)

        # ---- flowing cape fanned out behind (west), if this skin has one ----
        if cape_col:
            cd = _lerp3(cape_col, (0, 0, 0), 0.42)
            ch = _lerp3(cape_col, (255, 255, 255), 0.30)
            billow = 7 * u * swing
            pts = [(int(c - 3 * u), int(c - 15 * u)), (int(c - 34 * u), int(c - 30 * u + billow)),
                   (int(c - 44 * u), int(c - 6 * u + billow * 0.4)),
                   (int(c - 45 * u), int(c + 10 * u - billow * 0.4)),
                   (int(c - 33 * u), int(c + 30 * u - billow)), (int(c - 3 * u), int(c + 15 * u))]
            pygame.draw.polygon(s, cape_col, pts)
            pygame.draw.polygon(s, cd, pts, lw)
            for fyv in (-18, -7, 5, 16):
                pygame.draw.line(s, cd, (int(c - 8 * u), int(c + fyv * u)),
                                 (int(c - 40 * u), int(c + fyv * u * 1.5 + billow * 0.3)), lw)
            pygame.draw.line(s, ch, (int(c - 6 * u), int(c - 13 * u)),
                             (int(c - 34 * u), int(c - 25 * u + billow)), lw)

        def ring(cx, cy, r0, r1, step, col, w=None):
            for a in range(0, 360, step):
                ar = math.radians(a)
                pygame.draw.line(s, col,
                                 (cx + math.cos(ar) * r0, cy + math.sin(ar) * r0),
                                 (cx + math.cos(ar) * r1, cy + math.sin(ar) * r1),
                                 w or lw)

        # ---- black horsehair plume streaming back from the helm (west) ----
        sway = 10 * u * swing
        segs = [(12, 0.0), (-2, 0.22), (-16, 0.5), (-30, 0.8), (-40, 1.0)]
        w0 = 8 * u
        top, bot = [], []
        for i, (dx, kk) in enumerate(segs):
            ww = w0 * (1 - i / (len(segs) + 0.5))
            xx = c + dx * u
            yy = c + sway * kk
            top.append((xx, yy - ww))
            bot.append((xx, yy + ww))
        pygame.draw.polygon(s, plume, top + bot[::-1])
        pygame.draw.lines(s, plume_hi, False,
                          [(c + dx * u, c + sway * kk - 1) for dx, kk in segs], max(1, int(1.4 * u)))

        # ---- fauld / skirt plates peeking below the breastplate ----
        _shaded_disc(s, int(c - 2 * u), int(c + 8 * u), int(17 * u), mtl, mtl_dk)
        ring(c - 2 * u, c + 8 * u, 9 * u, 17 * u, 26, edge)
        pygame.draw.circle(s, edge, (int(c - 2 * u), int(c + 8 * u)), int(17 * u), lw)

        # ---- greaves / boots (opposed stride) ----
        o = 9 * u * swing
        for side, sgn in ((-1, 1), (1, -1)):
            bx = int(c + o * sgn)
            by = int(c + side * 15 * u)
            _shaded_disc(s, bx, by, int(5.5 * u), mtl_hi, mtl_dk)
            pygame.draw.circle(s, edge, (bx, by), int(5.5 * u), 1)
            pygame.draw.line(s, mtl_dk, (bx - 3 * u, by - 2 * u), (bx, by + 2 * u), max(1, int(u)))
            pygame.draw.line(s, mtl_dk, (bx + 3 * u, by - 2 * u), (bx, by + 2 * u), max(1, int(u)))

        # ---- rounded fluted pauldrons on both flanks ----
        for side in (-1, 1):
            py = int(c + side * 16 * u)
            _shaded_disc(s, int(c - 1 * u), py, int(11 * u), mtl_hi, mtl_dk)
            pygame.draw.circle(s, edge, (int(c - 1 * u), py), int(11 * u), lw)
            ring(c - 1 * u, py, 5 * u, 10 * u, 45, mtl_dk, max(1, int(u)))
            _shaded_disc(s, int(c + 1 * u), int(c + side * 24 * u), int(7 * u), mtl_hi, mtl)
            pygame.draw.circle(s, edge, (int(c + 1 * u), int(c + side * 24 * u)), int(7 * u), lw)

        # ---- fluted breastplate with radiating sunburst ----
        _shaded_disc(s, c, c, int(18 * u), mtl_hi, mtl_dk)
        pygame.draw.circle(s, edge, (c, c), int(18 * u), max(2, int(2 * u)))
        ring(c, c, 7 * u, 16 * u, 24, mtl_dk, max(1, int(1.3 * u)))
        for a in range(0, 360, 60):
            ar = math.radians(a)
            pygame.draw.circle(s, gold, (int(c + math.cos(ar) * 13 * u), int(c + math.sin(ar) * 13 * u)),
                               max(1, int(1.3 * u)))
        boss = [(c, int(c - 6 * u)), (int(c + 6 * u), c), (c, int(c + 6 * u)), (int(c - 6 * u), c)]
        pygame.draw.polygon(s, mtl_hi, boss)
        pygame.draw.polygon(s, edge, boss, 1)
        pygame.draw.circle(s, gold, (c, c), max(1, int(1.7 * u)))

        # ---- gorget between chest and helm ----
        pygame.draw.circle(s, mtl, (int(c + 10 * u), c), int(6 * u))
        pygame.draw.circle(s, edge, (int(c + 10 * u), c), int(6 * u), lw)

        if atk is None:
            # ---- greatsword resting point-forward, both gauntlets on the grip ----
            gx, gy = int(c + 2 * u), int(c + 4 * u)
            blade_dy = int(2 * u * swing)
            btip = (int(c + 47 * u), int(gy + 2 * u + blade_dy))
            pygame.draw.line(s, mtl_dk, (gx, gy), btip, max(3, int(5 * u)))
            pygame.draw.line(s, (224, 216, 198), (gx, gy), btip, max(2, int(3 * u)))
            pygame.draw.line(s, (246, 243, 233),
                             (int(gx + (btip[0] - gx) * 0.2), int(gy + (btip[1] - gy) * 0.2)), btip,
                             max(1, int(1.2 * u)))
            pygame.draw.line(s, gold, (int(gx - 2 * u), int(gy - 7 * u)),
                             (int(gx + 2 * u), int(gy + 7 * u)), max(2, int(3 * u)))
            pygame.draw.circle(s, gold, (int(gx - 4 * u), gy), max(2, int(3 * u)))
            pygame.draw.circle(s, edge, (int(gx - 4 * u), gy), max(2, int(3 * u)), 1)
            for hxx, hyy in ((5, 1), (12, -1)):
                pygame.draw.circle(s, mtl_hi, (int(gx + hxx * u), int(gy + hyy * u)), max(2, int(3.6 * u)))
                pygame.draw.circle(s, edge, (int(gx + hxx * u), int(gy + hyy * u)), max(2, int(3.6 * u)), 1)
        else:
            # ---- greatsword mid-swing: sweeps a wide frontal arc ----
            piv = (c + 2 * u, c + 3 * u)
            e = atk ** 0.6                       # ease-out: fast bite, slow recovery
            L = 52 * u

            def blade_ang(prog):
                return math.radians(116 - 232 * prog)   # wind-up (down) -> follow-through (up)

            for j, tf in enumerate((0.5, 0.32, 0.18)):
                pe = e - (j + 1) * 0.13
                if pe <= 0:
                    continue
                pa = blade_ang(pe)
                pt = (piv[0] + math.cos(pa) * L, piv[1] + math.sin(pa) * L)
                tr = pygame.Surface((S, S), pygame.SRCALPHA)
                pygame.draw.line(tr, (236, 226, 200, int(150 * tf)), piv, pt, max(2, int(5 * u)))
                s.blit(tr, (0, 0))

            ang = blade_ang(e)
            tip = (piv[0] + math.cos(ang) * L, piv[1] + math.sin(ang) * L)
            perp = (math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2))
            pygame.draw.line(s, mtl_dk, piv, tip, max(3, int(6 * u)))
            pygame.draw.line(s, (224, 216, 198), piv, tip, max(2, int(4 * u)))
            pygame.draw.line(s, (248, 245, 236),
                             (piv[0] + math.cos(ang) * 11 * u, piv[1] + math.sin(ang) * 11 * u),
                             tip, max(1, int(1.6 * u)))
            pygame.draw.line(s, gold,
                             (piv[0] - perp[0] * 7 * u, piv[1] - perp[1] * 7 * u),
                             (piv[0] + perp[0] * 7 * u, piv[1] + perp[1] * 7 * u), max(2, int(3 * u)))
            pygame.draw.circle(s, gold, (int(piv[0]), int(piv[1])), max(2, int(3.4 * u)))

        # ---- closed great helm at the front (east) ----
        hx = int(c + 16 * u)
        _shaded_disc(s, hx, c, int(11 * u), mtl_hi, mtl)
        pygame.draw.circle(s, edge, (hx, c), int(11 * u), max(1, int(1.8 * u)))
        pygame.draw.circle(s, gold, (int(hx - 3 * u), c), max(1, int(2 * u)))   # plume socket
        vx = int(hx + 2 * u)
        visor = [(vx, int(c - 7 * u)), (int(vx + 12 * u), int(c - 4 * u)),
                 (int(vx + 12 * u), int(c + 4 * u)), (vx, int(c + 7 * u))]
        pygame.draw.polygon(s, mtl_dk, visor)
        pygame.draw.polygon(s, edge, visor, 1)
        for sy in (-4, -1.5, 1, 3.5):
            pygame.draw.line(s, edge, (int(vx + 3 * u), int(c + sy * u)),
                             (int(vx + 11 * u), int(c + sy * u)), max(1, int(1.2 * u)))
        pygame.draw.circle(s, glim, (int(vx + 7 * u), int(c - 1 * u)), max(1, int(1.3 * u)))
    return _hires(TILE + 32, fn)


def _spr_rat(color):
    def fn(s, S):
        c = S // 2
        lite = _lerp3(color, (255, 255, 255), 0.30)
        dk = _lerp3(color, (0, 0, 0), 0.38)
        pink = (232, 172, 180)
        u = S * 0.01
        # curling tail (west)
        pygame.draw.lines(s, pink, False,
                          [(int(c - 16 * u), c), (int(c - 30 * u), int(c - 7 * u)),
                           (int(c - 40 * u), int(c + 5 * u)), (int(c - 48 * u), int(c - 3 * u))],
                          max(2, int(3.4 * u)))
        # four paws
        for lx, ly in ((-11, 15), (10, 16), (-11, -15), (10, -16)):
            pygame.draw.circle(s, dk, (int(c + lx * u), int(c + ly * u)), max(2, int(5 * u)))
        # elongated body
        _shaded_disc(s, int(c - 3 * u), c, int(20 * u), lite, dk)
        _shaded_disc(s, int(c + 14 * u), c, int(15 * u), lite, dk)
        # head
        hx = int(c + 26 * u)
        _shaded_disc(s, hx, c, int(12 * u), lite, color)
        # ears
        _shaded_disc(s, int(hx - 3 * u), int(c - 12 * u), int(6 * u), pink, _lerp3(pink, (0, 0, 0), 0.3))
        _shaded_disc(s, int(hx + 6 * u), int(c - 10 * u), int(5 * u), pink, _lerp3(pink, (0, 0, 0), 0.3))
        # snout + nose
        _shaded_disc(s, int(hx + 10 * u), int(c + u), int(6 * u), lite, color)
        pygame.draw.circle(s, (44, 32, 34), (int(hx + 16 * u), int(c + u)), max(2, int(3 * u)))
        # whiskers
        for dy in (-2, 1, 4):
            pygame.draw.line(s, (238, 238, 242), (int(hx + 12 * u), int(c + dy * u)),
                             (int(hx + 27 * u), int(c + dy * u + 4 * u)), max(1, int(1.2 * u)))
        # eye
        pygame.draw.circle(s, (18, 14, 16), (int(hx + 2 * u), int(c - 3 * u)), max(2, int(3.6 * u)))
        pygame.draw.circle(s, (255, 246, 205), (int(hx + 3 * u), int(c - 4 * u)), max(1, int(1.5 * u)))
    return _hires(TILE + 8, fn)


GOBLIN_WALK_FRAMES = 8


def _spr_goblin(color, phase=0.0):
    """Hunched goblin facing the viewer. `phase` in [0,1) drives a stomping
    walk cycle: legs stride, arms counter-swing, the body bobs and leans."""
    sw = math.sin(phase * math.tau)              # stride: legs / arms swing
    bob = math.sin(phase * 2 * math.tau)         # vertical bob at twice the stride rate

    def fn(s, S):
        c = S // 2
        u = S * 0.01
        yb = -1.6 * u * bob                       # torso rises on the pass, drops on the plant
        lean = 1.4 * u * sw
        lite = _lerp3(color, (255, 255, 255), 0.34)
        dk = _lerp3(color, (0, 0, 0), 0.42)
        cloth = (122, 74, 46)
        # striding feet (opposed): the forward leg lifts and swings ahead
        for fx in (-11, 11):
            st = sw if fx < 0 else -sw
            lift = max(0.0, st) * 8 * u
            fxx = int(c + fx * u + st * 4 * u)
            fyy = int(c + 30 * u - lift)
            _shaded_disc(s, fxx, fyy, int(6 * u), dk, _lerp3(dk, (0, 0, 0), 0.4))
        # hunched torso
        _shaded_disc(s, int(c + lean), int(c + 12 * u + yb), int(19 * u),
                     _lerp3(color, (255, 255, 255), 0.16), dk)
        pygame.draw.rect(s, cloth, (int(c - 14 * u + lean), int(c + 12 * u + yb),
                                    int(28 * u), int(12 * u)), border_radius=int(3 * u))
        # arms swinging opposite the legs
        la_y = int(c + 23 * u + yb + sw * 5 * u)
        ra_y = int(c + 22 * u + yb - sw * 5 * u)
        pygame.draw.line(s, color, (int(c - 12 * u + lean), int(c + 5 * u + yb)),
                         (int(c - 19 * u), la_y), max(2, int(7 * u)))
        pygame.draw.line(s, color, (int(c + 12 * u + lean), int(c + 5 * u + yb)),
                         (int(c + 20 * u), ra_y), max(2, int(7 * u)))
        pygame.draw.circle(s, lite, (int(c - 19 * u), la_y), max(2, int(5 * u)))
        # crude dagger in right hand (tracks the swinging fist)
        pygame.draw.line(s, (90, 60, 40), (int(c + 16 * u), ra_y + int(2 * u)),
                         (int(c + 22 * u), ra_y - int(4 * u)), max(2, int(5 * u)))
        pygame.draw.line(s, (205, 210, 222), (int(c + 21 * u), ra_y - int(2 * u)),
                         (int(c + 33 * u), ra_y - int(19 * u)), max(2, int(4 * u)))
        # big head
        hx = int(c + lean * 1.3)
        hy = int(c - 15 * u + yb)
        _shaded_disc(s, hx, hy, int(22 * u), lite, color)
        pygame.draw.circle(s, dk, (hx, hy), int(22 * u), max(1, int(2 * u)))
        # long pointed ears
        for sgn in (-1, 1):
            ear = [(int(hx + sgn * 19 * u), hy), (int(hx + sgn * 43 * u), int(hy - 10 * u)),
                   (int(hx + sgn * 20 * u), int(hy + 11 * u))]
            pygame.draw.polygon(s, color, ear)
            pygame.draw.polygon(s, dk, ear, max(1, int(1.6 * u)))
        # hooked nose
        pygame.draw.polygon(s, _lerp3(color, (0, 0, 0), 0.16),
                            [(hx, hy), (int(hx - 4 * u), int(hy + 15 * u)), (int(hx + 6 * u), int(hy + 10 * u))])
        # angry brows
        pygame.draw.line(s, dk, (int(hx - 15 * u), int(hy - 6 * u)), (int(hx - 3 * u), hy), max(2, int(3 * u)))
        pygame.draw.line(s, dk, (int(hx + 15 * u), int(hy - 6 * u)), (int(hx + 3 * u), hy), max(2, int(3 * u)))
        # glowing eyes
        for ex in (-9, 9):
            pygame.draw.circle(s, (255, 232, 96), (int(hx + ex * u), hy), max(2, int(4.5 * u)))
            pygame.draw.circle(s, (60, 30, 10), (int(hx + ex * u), hy), max(1, int(2 * u)))
        # grin with teeth
        pygame.draw.arc(s, (28, 18, 14), (int(hx - 10 * u), int(hy + 4 * u), int(20 * u), int(14 * u)), 3.4, 6.0, max(2, int(2 * u)))
        for tx in (-5, 3):
            pygame.draw.polygon(s, (242, 236, 222),
                                [(int(hx + tx * u), int(hy + 9 * u)), (int(hx + tx * u + 3 * u), int(hy + 9 * u)),
                                 (int(hx + tx * u + 1.5 * u), int(hy + 15 * u))])
    return _hires(TILE + 18, fn)


def _spr_orc(color):
    def fn(s, S):
        c = S // 2
        u = S * 0.01
        skin = color
        lite = _lerp3(skin, (255, 255, 255), 0.28)
        dk = _lerp3(skin, (0, 0, 0), 0.44)
        armor = (150, 60, 50)
        armor_dk = (86, 32, 30)

        # feet
        for fx in (-14, 14):
            _shaded_disc(s, int(c + fx * u), int(c + 35 * u), int(8 * u), dk, _lerp3(dk, (0, 0, 0), 0.4))
        # thick arms + fists
        pygame.draw.line(s, skin, (int(c - 16 * u), int(c + 8 * u)), (int(c - 28 * u), int(c + 27 * u)), max(3, int(11 * u)))
        pygame.draw.line(s, skin, (int(c + 16 * u), int(c + 8 * u)), (int(c + 30 * u), int(c + 25 * u)), max(3, int(11 * u)))
        _shaded_disc(s, int(c - 28 * u), int(c + 28 * u), int(7 * u), lite, dk)
        _shaded_disc(s, int(c + 30 * u), int(c + 25 * u), int(7 * u), lite, dk)
        # wooden club in right fist
        pygame.draw.line(s, (92, 64, 42), (int(c + 28 * u), int(c + 24 * u)), (int(c + 44 * u), int(c - 8 * u)), max(3, int(6 * u)))
        _shaded_disc(s, int(c + 46 * u), int(c - 12 * u), int(11 * u), (126, 92, 60), (72, 50, 32))
        # massive crimson-armored torso
        _shaded_disc(s, c, int(c + 16 * u), int(27 * u), _lerp3(armor, (255, 255, 255), 0.2), armor_dk)
        pygame.draw.circle(s, (40, 16, 16), (c, int(c + 16 * u)), int(27 * u), max(1, int(2 * u)))
        pygame.draw.line(s, armor_dk, (int(c - 10 * u), int(c + 6 * u)), (int(c - 3 * u), int(c + 40 * u)), max(1, int(2 * u)))
        # bone shoulder spikes
        for sgn in (-1, 1):
            pygame.draw.polygon(s, (228, 222, 206),
                                [(int(c + sgn * 16 * u), int(c + 2 * u)), (int(c + sgn * 30 * u), int(c - 12 * u)),
                                 (int(c + sgn * 24 * u), int(c + 5 * u))])
            pygame.draw.polygon(s, (150, 144, 128),
                                [(int(c + sgn * 16 * u), int(c + 2 * u)), (int(c + sgn * 30 * u), int(c - 12 * u)),
                                 (int(c + sgn * 24 * u), int(c + 5 * u))], 1)

        # low, jutting head
        hy = int(c - 17 * u)
        _shaded_disc(s, c, hy, int(20 * u), lite, skin)
        pygame.draw.circle(s, dk, (c, hy), int(21 * u), max(1, int(2 * u)))
        # ears
        for sgn in (-1, 1):
            pygame.draw.polygon(s, skin,
                                [(int(c + sgn * 19 * u), hy), (int(c + sgn * 31 * u), int(hy - 5 * u)),
                                 (int(c + sgn * 18 * u), int(hy + 8 * u))])
        # heavy brow ridge
        pygame.draw.line(s, dk, (int(c - 15 * u), int(hy - 3 * u)), (int(c + 15 * u), int(hy - 3 * u)), max(2, int(4 * u)))
        # deep-set glowing eyes
        for ex in (-8, 8):
            pygame.draw.circle(s, (255, 138, 70), (int(c + ex * u), int(hy + 2 * u)), max(2, int(3.6 * u)))
            pygame.draw.circle(s, (90, 22, 8), (int(c + ex * u), int(hy + 2 * u)), max(1, int(1.6 * u)))
        # flat snout + frown
        _shaded_disc(s, c, int(hy + 11 * u), int(8 * u), lite, skin)
        pygame.draw.line(s, (34, 20, 16), (int(c - 8 * u), int(hy + 15 * u)), (int(c + 8 * u), int(hy + 15 * u)), max(2, int(2.4 * u)))
        # big tusks pointing up past the snout
        for sgn in (-1, 1):
            pygame.draw.polygon(s, (246, 242, 228),
                                [(int(c + sgn * 8 * u), int(hy + 16 * u)),
                                 (int(c + sgn * 12 * u), int(hy + 1 * u)),
                                 (int(c + sgn * 3 * u), int(hy + 14 * u))])
            pygame.draw.polygon(s, (150, 146, 132),
                                [(int(c + sgn * 8 * u), int(hy + 16 * u)),
                                 (int(c + sgn * 12 * u), int(hy + 1 * u)),
                                 (int(c + sgn * 3 * u), int(hy + 14 * u))], 1)
        # war paint slash across the brow
        pygame.draw.line(s, (206, 62, 56), (int(c - 14 * u), int(hy - 9 * u)),
                         (int(c + 12 * u), int(hy - 12 * u)), max(2, int(3 * u)))
    return _hires(TILE + 26, fn)


CYCLOPS_WALK_FRAMES = 8


def _spr_cyclops(color, phase=0.0, hurt=False):
    """The stairwell boss: a squat, pot-bellied ogre hugging a boulder,
    bald pink-tan head, one big pale eye, a bulbous nose and an underbite.

    `phase` in [0,1) drives a lumbering, side-to-side walk cycle: legs
    stride, the body bobs and sways. `hurt` swaps in a genuine pained
    reaction — a scrunched-shut eye, brow pinched up, a gasping open
    mouth, head thrown back — instead of a flat color flash.
    """
    sw = math.sin(phase * math.tau)         # stride: legs step, body sways
    bob = math.sin(phase * 2 * math.tau)    # body bob at twice the stride rate

    def fn(s, S):
        c = S // 2
        u = S * 0.01
        lean = 1.6 * sw
        yb = -1.7 * bob
        recoil = -1.6 if hurt else 0.0

        def P(x, y):
            return (int(c + x * u), int(c + y * u))

        def Q(x, y):
            """A body-part point that sways/bobs with the stride and flinches when hurt."""
            return (int(c + (x + lean) * u), int(c + (y + yb + recoil) * u))

        def tint(col):
            return _lerp3(col, (214, 92, 82), 0.4) if hurt else col

        skin = tint(color)
        lite = _lerp3(skin, (255, 255, 255), 0.28)
        dk = _lerp3(skin, (0, 0, 0), 0.40)
        vdk = _lerp3(skin, (0, 0, 0), 0.58)
        headskin = tint(_lerp3(color, (232, 176, 158), 0.55))
        headskin_lite = _lerp3(headskin, (255, 255, 255), 0.30)
        headskin_dk = _lerp3(headskin, (0, 0, 0), 0.30)
        cloth = (222, 196, 150)
        cloth_dk = (170, 142, 98)
        spot = (92, 62, 34)
        stone = (150, 146, 138)
        stone_dk = (86, 82, 76)
        tooth = (240, 234, 218)
        tooth_dk = (150, 140, 122)

        # ---- short, stubby legs, striding in place ----
        for sgn in (-1, 1):
            st = sw if sgn < 0 else -sw
            lift = max(0.0, st) * 5
            hip = P(sgn * 13, 30)
            foot = P(sgn * 17 + st * 3, 41 - lift)
            pygame.draw.line(s, dk, hip, foot, max(3, int(15 * u)))
            _shaded_disc(s, foot[0], foot[1], int(8 * u), skin, vdk)
            pygame.draw.ellipse(s, vdk, (foot[0] - int(9 * u), foot[1] - int(1 * u), int(20 * u), int(7 * u)))

        # ---- pot-bellied torso, built from two blended discs for a soft silhouette ----
        _shaded_disc(s, *Q(0, -3), int(20 * u), lite, dk)
        _shaded_disc(s, *Q(0, 15), int(25 * u), lite, dk)
        pygame.draw.circle(s, dk, Q(0, 15), int(25 * u), max(1, int(2.2 * u)))
        pygame.draw.arc(s, dk, (Q(-13, -11)[0], Q(0, -11)[1], int(26 * u), int(11 * u)), 3.7, 5.7, max(1, int(1.5 * u)))
        pygame.draw.line(s, lite, Q(-15, -12), Q(-11, -3), max(1, int(3 * u)))

        # ---- leopard-print loincloth wrapped around the hips ----
        band = [Q(-20, 20), Q(20, 20), Q(13, 34), Q(-13, 34)]
        pygame.draw.polygon(s, cloth, band)
        pygame.draw.polygon(s, cloth_dk, band, max(1, int(1.6 * u)))
        for sx, sy, rr in ((-12, 24, 2.6), (-2, 26, 2.2), (9, 23, 2.4), (12, 29, 2.0),
                           (-12, 29, 2.0), (3, 31, 2.0), (-5, 30, 1.8)):
            pygame.draw.circle(s, spot, Q(sx, sy), max(1, int(rr * u)))

        # ---- long arms, drawn over the torso, reaching down to hug the boulder ----
        for sgn in (-1, 1):
            shoulder = Q(sgn * 17, -6)
            hand = Q(sgn * 13, 18)
            _shaded_disc(s, *shoulder, int(9 * u), lite, dk)
            pygame.draw.line(s, skin, shoulder, hand, max(4, int(13 * u)))
            _shaded_disc(s, *hand, int(8 * u), lite, dk)

        # ---- boulder, hugged against the belly by both hands ----
        bx, by = Q(0, 16)
        _shaded_disc(s, bx, by, int(16 * u), stone, stone_dk)
        pygame.draw.circle(s, (52, 50, 46), (bx, by), int(16 * u), max(1, int(2 * u)))
        for sx, sy, rr in ((-7, -6, 3.2), (6, -8, 2.6), (2, 7, 3.4), (-6, 6, 2.4), (8, 3, 2.2)):
            pygame.draw.circle(s, stone_dk, (int(bx + sx * u), int(by + sy * u)), max(1, int(rr * u)))
        pygame.draw.line(s, (188, 184, 174), (int(bx - 8 * u), int(by - 10 * u)), (int(bx + 2 * u), int(by - 4 * u)), max(1, int(2 * u)))
        for sgn in (-1, 1):
            _shaded_disc(s, *Q(sgn * 14, 20), int(7 * u), lite, dk)

        # ---- neck shadow so the head doesn't look glued to the shoulders ----
        pygame.draw.ellipse(s, vdk, (Q(-8, -20)[0], Q(0, -20)[1], int(16 * u), int(10 * u)))

        # ---- bald head, slightly pinker than the body ----
        hy = -30
        _shaded_disc(s, *Q(0, hy), int(18 * u), headskin_lite, headskin)
        pygame.draw.circle(s, headskin_dk, Q(0, hy), int(18 * u), max(1, int(2 * u)))
        pygame.draw.ellipse(s, headskin_lite, (Q(-9, hy - 14)[0], Q(0, hy - 14)[1], int(14 * u), int(9 * u)))
        # jaw taper with a heavy, undershot chin
        jaw = [Q(-13, hy + 9), Q(13, hy + 9), Q(8, hy + 19), Q(0, hy + 23), Q(-8, hy + 19)]
        pygame.draw.polygon(s, headskin, jaw)
        pygame.draw.polygon(s, headskin_dk, jaw, max(1, int(1.5 * u)))
        # small round ears
        for sgn in (-1, 1):
            _shaded_disc(s, *Q(sgn * 17, hy + 2), int(4 * u), headskin_lite, headskin_dk)

        if hurt:
            # ---- brow pinched up in distress ----
            peak = Q(0, hy - 9)
            pygame.draw.line(s, headskin_dk, peak, Q(-12, hy - 2), max(2, int(4 * u)))
            pygame.draw.line(s, headskin_dk, peak, Q(12, hy - 2), max(2, int(4 * u)))
            # ---- eye scrunched shut ----
            ex, ey = Q(0, hy)
            pygame.draw.arc(s, headskin_dk, (ex - int(10 * u), ey - int(7 * u), int(20 * u), int(14 * u)), 3.5, 6.05, max(2, int(3 * u)))
            pygame.draw.line(s, headskin_dk, (int(ex - 6 * u), int(ey + 1 * u)), (int(ex + 6 * u), int(ey - 1 * u)), max(2, int(2.2 * u)))
            for lx in (-11, -5, 5, 11):
                pygame.draw.line(s, headskin_dk, (int(ex + lx * u), int(ey - 9 * u)),
                                 (int(ex + lx * u * 1.3), int(ey - 14 * u)), max(1, int(1.6 * u)))
        else:
            # ---- thick single brow over the eye ----
            pygame.draw.line(s, headskin_dk, Q(-12, hy - 6), Q(11, hy - 8), max(2, int(5 * u)))
            # ---- one big pale, watchful eye ----
            ex, ey = Q(0, hy)
            _shaded_disc(s, ex, ey, int(10 * u), (255, 255, 252), (222, 220, 206))
            pygame.draw.circle(s, headskin_dk, (ex, ey), int(10 * u), max(1, int(1.8 * u)))
            pygame.draw.circle(s, (168, 188, 196), (ex, ey), max(2, int(6 * u)))
            pygame.draw.circle(s, (98, 122, 132), (ex, ey), max(2, int(6 * u)), max(1, int(1.1 * u)))
            pygame.draw.circle(s, (26, 24, 24), (ex, ey), max(2, int(3.2 * u)))
            pygame.draw.circle(s, (255, 255, 255), (int(ex - 2.6 * u), int(ey - 2.6 * u)), max(1, int(1.8 * u)))

        # ---- bulbous nose ----
        _shaded_disc(s, *Q(0, hy + 12), int(6 * u), headskin_lite, headskin_dk)
        for sgn in (-1, 1):
            pygame.draw.circle(s, headskin_dk, Q(sgn * 2, hy + 14), max(1, int(1.1 * u)))

        if hurt:
            # ---- mouth thrown open in a pained gasp ----
            mx, my = Q(0, hy + 20)
            pygame.draw.ellipse(s, (60, 22, 20), (mx - int(6 * u), my - int(6 * u), int(12 * u), int(11 * u)))
            pygame.draw.ellipse(s, (196, 70, 66), (mx - int(4 * u), my - int(2 * u), int(8 * u), int(5 * u)))
            for sgn in (-1, 1):
                fang = [Q(sgn * 4, hy + 16), Q(sgn * 7, hy + 10), Q(sgn * 2, hy + 15)]
                pygame.draw.polygon(s, tooth, fang)
                pygame.draw.polygon(s, tooth_dk, fang, 1)
        else:
            # ---- wide downturned mouth with an underbite ----
            pygame.draw.arc(s, (60, 34, 30), (Q(-9, hy + 17)[0], Q(0, hy + 17)[1], int(18 * u), int(9 * u)), 3.5, 6.0, max(2, int(2 * u)))
            for sgn in (-1, 1):
                fang = [Q(sgn * 3, hy + 22), Q(sgn * 6, hy + 15), Q(sgn * 1, hy + 20)]
                pygame.draw.polygon(s, tooth, fang)
                pygame.draw.polygon(s, tooth_dk, fang, 1)
    return _hires(TILE + 40, fn)


def _spr_potion():
    def fn(s, S):
        c = S // 2
        pygame.draw.rect(s, (70, 60, 55), (c - S // 16, int(S * 0.16), S // 8, S // 10), border_radius=max(1, S // 60))
        pygame.draw.rect(s, (196, 206, 216), (c - S // 12, int(S * 0.26), S // 6, S // 14))
        _shaded_disc(s, c, int(S * 0.60), int(S * 0.26), (232, 96, 116), (150, 34, 54))
        pygame.draw.circle(s, (30, 12, 18), (c, int(S * 0.60)), int(S * 0.26), max(1, S // 60))
        pygame.draw.circle(s, (255, 255, 255), (c - S // 12, int(S * 0.5)), max(1, S // 22))
    return _hires(TILE, fn)


def _spr_gold():
    def fn(s, S):
        c = S // 2
        for off in (int(S * 0.12), int(S * 0.06), 0):
            _shaded_disc(s, c, c + off, int(S * 0.28), (255, 224, 120), (150, 108, 24))
        pygame.draw.circle(s, (120, 84, 18), (c, c), int(S * 0.28), max(1, S // 50))
        pygame.draw.circle(s, (255, 248, 200), (c - int(S * 0.09), c - int(S * 0.09)), int(S * 0.07))
    return _hires(TILE, fn)


def _spr_shard():
    def fn(s, S):
        c = S // 2
        pts = [(c, int(S * 0.14)), (int(S * 0.74), c), (c, int(S * 0.86)), (int(S * 0.26), c)]
        pygame.draw.polygon(s, (96, 158, 226), pts)
        pygame.draw.polygon(s, (188, 226, 255), [(c, int(S * 0.14)), (int(S * 0.74), c), (c, c)])
        pygame.draw.polygon(s, (40, 70, 120), pts, max(1, S // 50))
        pygame.draw.line(s, (230, 244, 255), (c, int(S * 0.2)), (c, int(S * 0.8)), max(1, S // 80))
    return _hires(TILE, fn)


def _spr_torch():
    def fn(s, S):
        c = S // 2
        u = S * 0.01
        topy, boty = int(S * 0.16), int(S * 0.99)
        tw, bw = int(3.5 * u), int(5.5 * u)
        # tall charred wooden shaft
        pygame.draw.polygon(s, (58, 41, 27),
                            [(c - tw, topy), (c + tw, topy), (c + bw, boty), (c - bw, boty)])
        # wood grain streaks
        for gx, gc in ((-2.4, (88, 61, 39)), (-0.3, (38, 27, 17)), (1.8, (74, 51, 32)), (3.1, (28, 20, 13))):
            pygame.draw.line(s, gc, (int(c + gx * u), topy + int(3 * u)),
                             (int(c + gx * u * 1.4), boty - int(2 * u)), max(1, int(1.3 * u)))
        pygame.draw.line(s, (24, 17, 11), (c - tw, topy), (c - bw, boty), max(1, int(1.5 * u)))
        pygame.draw.line(s, (94, 66, 42), (c + tw, topy), (c + bw, boty), max(1, int(1.3 * u)))
        # wax / pitch drips down the lower shaft
        for dx, dl in ((-3.5, 13), (2.4, 20), (4.4, 8)):
            yy = int(S * 0.5)
            pygame.draw.line(s, (150, 120, 78), (int(c + dx * u), yy),
                             (int(c + dx * u), yy + int(dl * u)), max(1, int(2 * u)))
            pygame.draw.circle(s, (170, 140, 94), (int(c + dx * u), yy + int(dl * u)), max(1, int(1.8 * u)))
        # round drip-plate
        py = int(S * 0.62)
        pygame.draw.ellipse(s, (118, 90, 52), (int(c - 17 * u), py, int(34 * u), int(9 * u)))
        pygame.draw.ellipse(s, (168, 132, 82), (int(c - 17 * u), py - int(2 * u), int(34 * u), int(9 * u)))
        pygame.draw.ellipse(s, (72, 52, 30), (int(c - 17 * u), py - int(2 * u), int(34 * u), int(9 * u)),
                            max(1, int(1.4 * u)))
        pygame.draw.line(s, (212, 182, 132), (int(c - 10 * u), py - int(u)),
                         (int(c + 8 * u), py - int(u)), max(1, int(u)))
        # charred glowing crown where the flame springs
        pygame.draw.circle(s, (22, 16, 12), (c, topy + int(2 * u)), int(5.5 * u))
        for ex, ecol in ((-3, (255, 128, 46)), (1, (255, 182, 80)), (4, (196, 66, 26))):
            pygame.draw.circle(s, ecol, (int(c + ex * u), topy + int(u)), max(1, int(1.8 * u)))
    return _hires(TILE, fn)


_GLOW_RGB = None


def _glow_template():
    global _GLOW_RGB
    if _GLOW_RGB is None:
        n = 96
        g = pygame.Surface((n, n)).convert()
        g.fill((0, 0, 0))
        cx = n / 2
        for r in range(int(cx), 0, -1):
            v = int(255 * (1 - r / cx) ** 2.1)
            pygame.draw.circle(g, (v, v, v), (int(cx), int(cx)), r)
        _GLOW_RGB = g
    return _GLOW_RGB


def _draw_flame(screen, x, y, t, ph):
    fl = (0.82 + 0.12 * math.sin(t * 15 + ph) + 0.08 * math.sin(t * 33 + ph * 2.1)
          + 0.05 * math.sin(t * 57 + ph))

    def tongue(col, scale, height, width):
        h = height * scale * fl
        w = max(1.5, width * scale * fl)
        segs = 6
        left, right = [], []
        for i in range(segs + 1):
            f = i / segs
            yy = y + 3 - h * f
            lean = math.sin(t * 6 + ph + f * 2.4) * 4.5 * f * scale
            taper = w * (1 - f) ** 0.6
            left.append((x + lean - taper, yy))
            right.append((x + lean + taper, yy))
        pygame.draw.polygon(screen, col, [(int(px), int(py)) for px, py in left + right[::-1]])

    # soft radial heat glow (additive, smooth falloff)
    sz = int(70 + 34 * fl)
    glow = pygame.transform.smoothscale(_glow_template(), (sz, sz))
    k = 0.5 + 0.5 * min(1.0, fl)
    glow.fill((int(255 * k), int(140 * k), int(52 * k)), special_flags=pygame.BLEND_RGB_MULT)
    screen.blit(glow, (int(x - sz / 2), int(y - sz * 0.6)), special_flags=pygame.BLEND_RGB_ADD)

    # tall, wispy tapering flame: outer -> white-hot core
    tongue((190, 62, 20), 1.0, 32, 5.6)
    tongue((255, 120, 32), 0.82, 27, 4.6)
    tongue((255, 186, 74), 0.55, 19, 3.3)
    tongue((255, 242, 204), 0.3, 11, 2.0)

    # rising embers
    for i in range(4):
        et = (t * 0.8 + i * 0.31 + ph) % 1.0
        ex = x + math.sin(t * 4 + i * 2.3 + ph) * 6 * et
        ey = y - 4 - et * 34
        r = 2 if et < 0.45 else 1
        e = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
        pygame.draw.circle(e, (255, 190, 96, clamp(220 * (1 - et))), (r, r), r)
        screen.blit(e, (int(ex - r), int(ey - r)), special_flags=pygame.BLEND_RGB_ADD)


_AO_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def compute_ao(walls):
    ao = {}
    for row in range(MAP_ROWS):
        wr = walls[row]
        for col in range(MAP_COLS):
            if wr[col]:
                continue
            n = sum(1 for dx, dy in _AO_DIRS if is_wall_grid(walls, col + dx, row + dy))
            if n:
                ao[(col, row)] = min(5, n)
    return ao


def place_torches(walls, rooms):
    seen = set()
    torches = []
    for rm in rooms:
        cands = [(rm.x + rm.w // 2, rm.y - 1), (rm.x + rm.w // 2, rm.y + rm.h),
                 (rm.x - 1, rm.y + rm.h // 2), (rm.x + rm.w, rm.y + rm.h // 2)]
        random.shuffle(cands)
        placed = 0
        for cx, cy in cands:
            if placed >= 2 or (cx, cy) in seen:
                continue
            if 0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS and walls[cy][cx]:
                seen.add((cx, cy))
                torches.append((cx, cy, random.uniform(0, math.tau)))
                placed += 1
    return torches


def _make_floor_tile(rng):
    s = pygame.Surface((TILE, TILE)).convert()
    base = (39, 35, 49)
    s.fill(base)
    for _ in range(5):
        w, h = rng.randint(9, 15), rng.randint(9, 15)
        x, y = rng.randint(-4, TILE - 4), rng.randint(-4, TILE - 4)
        col = tuple(clamp(c + rng.randint(-9, 11)) for c in base)
        pygame.draw.rect(s, col, (x, y, w, h), border_radius=3)
        pygame.draw.rect(s, tuple(clamp(c - 13) for c in col), (x, y, w, h), 1, border_radius=3)
        pygame.draw.line(s, tuple(clamp(c + 15) for c in col), (x + 1, y + 1), (x + w - 2, y + 1))
    for _ in range(16):
        x, y = rng.randint(0, TILE - 1), rng.randint(0, TILE - 1)
        s.set_at((x, y), tuple(clamp(c + rng.randint(-15, 17)) for c in base))
    return s


def _make_wall_tile(rng):
    s = pygame.Surface((TILE, TILE)).convert()
    base = (54, 48, 68)
    s.fill(tuple(clamp(c - 15) for c in base))
    bh = 8
    for i, by in enumerate(range(0, TILE, bh)):
        off = bh if i % 2 else 0
        for bx in range(-bh + off, TILE, 14):
            col = tuple(clamp(c + rng.randint(-6, 9)) for c in base)
            pygame.draw.rect(s, col, (bx + 1, by + 1, 12, bh - 2))
            pygame.draw.line(s, tuple(clamp(c + 19) for c in col), (bx + 1, by + 1), (bx + 12, by + 1))
            pygame.draw.line(s, tuple(clamp(c - 17) for c in col), (bx + 1, by + bh - 2), (bx + 12, by + bh - 2))
    pygame.draw.line(s, (106, 96, 130), (0, 0), (TILE, 0), 2)
    pygame.draw.line(s, (20, 17, 26), (0, TILE - 1), (TILE, TILE - 1), 2)
    return s


def _make_wall_shadow():
    h = 14
    s = pygame.Surface((TILE, h), pygame.SRCALPHA)
    for i in range(h):
        pygame.draw.line(s, (0, 0, 0, clamp(120 * (1 - i / h))), (0, i), (TILE, i))
    return s


def _make_vignette(w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w / 2, h / 2
    maxd = math.hypot(cx, cy)
    for rr in range(int(maxd), 0, -6):
        pygame.draw.circle(s, (0, 0, 0, clamp(40 * (rr / maxd) ** 2.6)), (int(cx), int(cy)), rr)
    return s


def build_skin_sprites(pal):
    """All player animation frames for one skin palette."""
    return {
        "player": [_spr_knight(pal, phase=i / WALK_FRAMES) for i in range(WALK_FRAMES)],
        "player_hurt": [_spr_knight(pal, hurt=True, phase=i / WALK_FRAMES) for i in range(WALK_FRAMES)],
        "player_atk": [_spr_knight(pal, atk=i / (ATK_FRAMES - 1)) for i in range(ATK_FRAMES)],
        "player_atk_hurt": [_spr_knight(pal, hurt=True, atk=i / (ATK_FRAMES - 1)) for i in range(ATK_FRAMES)],
    }


def build_assets():
    rng = random.Random(20240607)
    floors = [_make_floor_tile(rng) for _ in range(6)]
    wall = _make_wall_tile(rng)

    def dim(surf, f):
        d = surf.copy()
        d.fill((int(255 * f), int(255 * f), int(255 * f + 6), 255), special_flags=pygame.BLEND_RGBA_MULT)
        return d

    spr = {
        **build_skin_sprites(SKINS[0]["pal"]),
        "rat": _spr_rat(ENEMY_TYPES["rat"]["color"]),
        "goblin": [_spr_goblin(ENEMY_TYPES["goblin"]["color"], phase=i / GOBLIN_WALK_FRAMES)
                   for i in range(GOBLIN_WALK_FRAMES)],
        "orc": _spr_orc(ENEMY_TYPES["orc"]["color"]),
        "cyclops": [_spr_cyclops(ENEMY_TYPES["cyclops"]["color"], phase=i / CYCLOPS_WALK_FRAMES)
                    for i in range(CYCLOPS_WALK_FRAMES)],
        "potion": _spr_potion(),
        "gold": _spr_gold(),
        "shard": _spr_shard(),
        "torch": _spr_torch(),
    }
    spr["torch_dim"] = dim(spr["torch"], 0.66)
    for k in ("rat", "orc"):
        spr[k + "_hit"] = _tint_white(spr[k])
    spr["goblin_hit"] = [_tint_white(f) for f in spr["goblin"]]
    # the boss gets a genuine pained pose (scrunched eye, gasping mouth) rather than a flat white flash
    spr["cyclops_hit"] = [_spr_cyclops(ENEMY_TYPES["cyclops"]["color"], phase=i / CYCLOPS_WALK_FRAMES, hurt=True)
                          for i in range(CYCLOPS_WALK_FRAMES)]

    ao = [None]
    for lvl in range(1, 6):
        a = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        a.fill((0, 0, 0, min(58, lvl * 12)))
        ao.append(a)

    return {
        "floor": floors,
        "floor_dim": [dim(s, 0.66) for s in floors],
        "wall": wall,
        "wall_dim": dim(wall, 0.66),
        "wall_shadow": _make_wall_shadow(),
        "vignette": _make_vignette(SCREEN_W, SCREEN_H - HUD_H),
        "spr": spr,
        "ao": ao,
        "skin_prev": [_spr_knight(sk["pal"]) for sk in SKINS],
    }


def _shadow(screen, cx, cy, rx, ry=None):
    ry = ry or max(2, rx // 2)
    s = pygame.Surface((rx * 2 + 2, ry * 2 + 2), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 95), (0, 0, rx * 2, ry * 2))
    screen.blit(s, (int(cx - rx), int(cy - ry + rx * 0.5)))


def draw_player_sprite(screen, cx, cy, player, t, A):
    fx, fy = player.facing
    face_ang = math.atan2(fy, fx)
    attacking = player.attack_flash > 0
    k = (1 - player.attack_flash / PLAYER_ATTACK_ANIM) if attacking else 0.0

    bob = math.sin(player.walk_phase) * 1.9 if player.moving else math.sin(t * 3) * 0.9
    if attacking:
        lunge = math.sin(min(1.0, k * 1.5) * math.pi) * 3.0
        cx += fx * lunge
        cy += fy * lunge
    cx, cy = int(cx), int(cy + bob)

    _shadow(screen, cx, cy + 9, 13, 6)

    if attacking:
        frames = A["spr"]["player_atk_hurt"] if player.hit_flash > 0 else A["spr"]["player_atk"]
        idx = min(len(frames) - 1, int(k * len(frames)))
    else:
        frames = A["spr"]["player_hurt"] if player.hit_flash > 0 else A["spr"]["player"]
        idx = int(player.walk_phase * 0.8) % len(frames) if player.moving else 0
    spr = pygame.transform.rotozoom(frames[idx], -math.degrees(face_ang), 1.0)
    screen.blit(spr, spr.get_rect(center=(cx, cy)))

    if attacking:
        e = k ** 0.6
        center = -face_ang + math.radians(232 * e - 116)     # crescent tracks the blade sweep
        rad = int(PLAYER_ATTACK_RANGE * TILE * 1.0)
        arc = pygame.Surface((rad * 2 + 14, rad * 2 + 14), pygame.SRCALPHA)
        a = clamp(235 * math.sin(min(1.0, k * 1.25) * math.pi))
        pygame.draw.arc(arc, (255, 255, 236, a), (7, 7, rad * 2, rad * 2), center - 0.5, center + 0.5, 6)
        pygame.draw.arc(arc, (255, 214, 138, a // 2), (3, 3, rad * 2 + 8, rad * 2 + 8),
                        center - 0.6, center + 0.6, 3)
        screen.blit(arc, (cx - rad - 7, cy - rad - 7))


def draw_enemy_sprite(screen, cx, cy, enemy, t, A, font_small=None):
    cx, cy = int(cx), int(cy)
    rr = int(enemy.radius * TILE)
    flash = enemy.hit_flash > 0
    boss = enemy.kind == "cyclops"
    breathe = int(math.sin(t * 3 + cx * 0.3) * 1.6)

    _shadow(screen, cx, cy + 6, rr + 3, rr // 2 + 2)
    if boss and not flash:
        pulse = 0.5 + 0.5 * math.sin(t * 2.2)
        g = pygame.Surface((96, 96), pygame.SRCALPHA)
        pygame.draw.circle(g, (255, 90, 40, int(20 + 14 * pulse)), (48, 48), 48)
        screen.blit(g, (cx - 48, cy - 48))
    if enemy.aggro and not flash:
        g = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(g, (255, 70, 50, 22), (32, 32), 32)
        screen.blit(g, (cx - 32, cy - 32))

    base = A["spr"][enemy.kind + ("_hit" if flash else "")]
    if isinstance(base, list):
        idx = int(enemy.walk_phase) % len(base) if enemy.moving else 0
        base = base[idx]
        if enemy.face[0] < 0:
            base = pygame.transform.flip(base, True, False)
    elif enemy.kind == "rat":
        base = pygame.transform.rotate(base, -math.degrees(math.atan2(enemy.face[1], enemy.face[0])))
    screen.blit(base, base.get_rect(center=(cx, cy + breathe)))

    if boss and font_small is not None:
        nm = font_small.render("CYCLOPS", True, (255, 200, 150))
        screen.blit(nm, nm.get_rect(center=(cx, cy - rr - 24)))

    if enemy.hp < enemy.max_hp or boss:
        bw = rr * 2 + 8
        bx, by = cx - bw // 2, cy - rr - 12
        ratio = max(0.0, enemy.hp / enemy.max_hp)
        pygame.draw.rect(screen, (0, 0, 0), (bx - 1, by - 1, bw + 2, 5), border_radius=2)
        pygame.draw.rect(screen, (40, 15, 15), (bx, by, bw, 3))
        pygame.draw.rect(screen, (230, 80, 70), (bx, by, int(bw * ratio), 3))


def draw_item_sprite(screen, cx, cy, kind, t, A):
    cx = int(cx)
    cy = int(cy + math.sin(t * 3 + cx * 0.5) * 3)
    gc = ITEM_COLORS[kind]
    glow = pygame.Surface((44, 44), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*gc, clamp(58 + 26 * math.sin(t * 4 + cx))), (22, 22), 18)
    screen.blit(glow, (cx - 22, cy - 22), special_flags=pygame.BLEND_RGB_ADD)
    _shadow(screen, cx, cy + 9, 7, 3)
    spr = A["spr"][kind]
    screen.blit(spr, spr.get_rect(center=(cx, cy)))
    if int(t * 3 + cx) % 6 == 0:
        pygame.draw.circle(screen, (255, 255, 255), (cx + 7, cy - 8), 1)


def draw_game(screen, player, walls, enemies, items, stairs, explored, visible_now, popups,
              particles, torches, ao, font_small, t, A, cam_x, cam_y):
    play_rect = pygame.Rect(0, HUD_H, SCREEN_W, SCREEN_H - HUD_H)
    screen.fill((6, 6, 10), play_rect)
    prev_clip = screen.get_clip()
    screen.set_clip(play_rect)

    col_start = max(0, int(cam_x) - 1)
    col_end = min(MAP_COLS, int(cam_x + SCREEN_W / TILE) + 2)
    row_start = max(0, int(cam_y) - 1)
    row_end = min(MAP_ROWS, int(cam_y + (SCREEN_H - HUD_H) / TILE) + 2)

    floors, floors_dim, ao_layers = A["floor"], A["floor_dim"], A["ao"]
    nfloor = len(floors)
    for row in range(row_start, row_end):
        for col in range(col_start, col_end):
            if (col, row) not in explored:
                continue
            visible = (col, row) in visible_now
            sx, sy = world_to_screen(cam_x, cam_y, col, row)
            pos = (int(sx), int(sy))
            if walls[row][col]:
                screen.blit(A["wall"] if visible else A["wall_dim"], pos)
            else:
                v = ((col * 2654435761) ^ (row * 40503)) % nfloor
                screen.blit(floors[v] if visible else floors_dim[v], pos)
                if row > 0 and walls[row - 1][col] and (col, row - 1) in explored:
                    screen.blit(A["wall_shadow"], pos)
                lvl = ao.get((col, row))
                if lvl and visible:
                    screen.blit(ao_layers[lvl], pos)

    tspr, tspr_dim = A["spr"]["torch"], A["spr"]["torch_dim"]
    for tc, tr, ph in torches:
        if (tc, tr) not in explored:
            continue
        sx, sy = world_to_screen(cam_x, cam_y, tc, tr)
        if (tc, tr) in visible_now:
            screen.blit(tspr, (int(sx), int(sy)))
            _draw_flame(screen, int(sx + TILE / 2), int(sy + TILE * 0.17), t, ph)
        else:
            screen.blit(tspr_dim, (int(sx), int(sy)))

    stairs_col, stairs_row = int(stairs[0]), int(stairs[1])
    if (stairs_col, stairs_row) in explored:
        sx, sy = world_to_screen(cam_x, cam_y, stairs_col, stairs_row)
        isx, isy = int(sx), int(sy)
        lit = (stairs_col, stairs_row) in visible_now
        pygame.draw.rect(screen, (14, 12, 18), (isx + 2, isy + 2, TILE - 3, TILE - 3), border_radius=3)
        steps = 4
        for i in range(steps):
            k = i * (TILE - 8) // (2 * steps)
            s = 70 + i * 45 if lit else 42 + i * 9
            pygame.draw.rect(screen, (s, int(s * 0.82), int(s * 0.4)),
                             (isx + 4 + k, isy + 4 + k, TILE - 7 - 2 * k, TILE - 7 - 2 * k),
                             border_radius=2)
        if lit:
            glow = pygame.Surface((TILE * 2, TILE * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (250, 210, 90, clamp(45 + 25 * math.sin(t * 3))),
                               (TILE, TILE), TILE)
            screen.blit(glow, (isx - TILE // 2, isy - TILE // 2))

    for p in particles:
        if p.kind != "dust":
            continue
        sx, sy = world_to_screen(cam_x, cam_y, p.x, p.y)
        d = pygame.Surface((3, 3), pygame.SRCALPHA)
        d.fill((*p.color, clamp(85 * (p.life / p.max_life))))
        screen.blit(d, (int(sx), int(sy)))

    for item in items:
        if (int(item.x), int(item.y)) not in visible_now:
            continue
        sx, sy = world_to_screen(cam_x, cam_y, item.x, item.y)
        draw_item_sprite(screen, sx, sy, item.kind, t, A)

    for enemy in enemies:
        if enemy.grid() not in visible_now:
            continue
        sx, sy = world_to_screen(cam_x, cam_y, enemy.x, enemy.y)
        draw_enemy_sprite(screen, sx, sy, enemy, t, A, font_small)

    psx, psy = world_to_screen(cam_x, cam_y, player.x, player.y)
    draw_player_sprite(screen, psx, psy, player, t, A)

    for p in particles:
        if p.kind == "dust":
            continue
        sx, sy = world_to_screen(cam_x, cam_y, p.x, p.y)
        sz = max(1, int(p.size * (p.life / p.max_life)))
        pygame.draw.circle(screen, p.color, (int(sx), int(sy)), sz)

    for p in popups:
        sx, sy = world_to_screen(cam_x, cam_y, p.x, p.y)
        alpha = clamp(255 * (p.timer / 0.8))
        sh = font_small.render(p.text, True, (0, 0, 0))
        sh.set_alpha(alpha // 2)
        surf = font_small.render(p.text, True, p.color)
        surf.set_alpha(alpha)
        screen.blit(sh, (sx - surf.get_width() / 2 + 1, sy + 1))
        screen.blit(surf, (sx - surf.get_width() / 2, sy))

    screen.blit(A["vignette"], (0, HUD_H))
    screen.set_clip(prev_clip)
    pygame.draw.rect(screen, (58, 52, 74), play_rect, 1)


def _draw_bar(screen, bx, by, bw, bh, ratio, top):
    pygame.draw.rect(screen, (0, 0, 0), (bx - 2, by - 2, bw + 4, bh + 4), border_radius=6)
    pygame.draw.rect(screen, (40, 18, 20), (bx, by, bw, bh), border_radius=5)
    if ratio > 0:
        fill_w = max(4, int(bw * ratio))
        bot = tuple(clamp(c * 0.55) for c in top)
        bar = pygame.Surface((fill_w, bh))
        for i in range(bh):
            f = i / bh
            bar.fill(tuple(clamp(top[k] + (bot[k] - top[k]) * f) for k in range(3)), (0, i, fill_w, 1))
        screen.blit(bar, (bx, by))
    pygame.draw.rect(screen, (210, 210, 225), (bx, by, bw, bh), 2, border_radius=5)


def draw_hud(screen, font_med, font_small, floor_num, best_floor, player, muted=False):
    for i in range(HUD_H):
        s = 12 + int(8 * (1 - i / HUD_H))
        pygame.draw.line(screen, (s, s - 1, s + 4), (0, i), (SCREEN_W, i))
    pygame.draw.line(screen, (90, 80, 120), (0, HUD_H - 1), (SCREEN_W, HUD_H - 1), 2)

    screen.blit(font_med.render(f"Floor {floor_num}", True, (245, 240, 250)), (16, 10))
    screen.blit(font_small.render(f"Best  {best_floor}", True, (170, 180, 205)), (16, 42))

    bx, by, bw, bh = 150, 14, 230, 22
    ratio = max(0.0, player.hp / player.max_hp)
    top = (231, 76, 60) if ratio <= 0.25 else (241, 196, 15) if ratio <= 0.5 else (46, 204, 113)
    _draw_bar(screen, bx, by, bw, bh, ratio, top)
    hp_txt = font_small.render(f"{max(0, int(player.hp))} / {player.max_hp}", True, (245, 245, 250))
    screen.blit(hp_txt, hp_txt.get_rect(center=(bx + bw // 2, by + bh // 2)))
    screen.blit(font_small.render("HP", True, (200, 205, 220)), (bx, by + bh + 4))

    gx = 430
    pygame.draw.circle(screen, (180, 140, 30), (gx, 23), 8)
    pygame.draw.circle(screen, (245, 205, 70), (gx, 22), 7)
    pygame.draw.circle(screen, (255, 240, 170), (gx - 2, 20), 2)
    screen.blit(font_med.render(f"{player.gold}", True, (245, 220, 140)), (gx + 14, 11))

    ax = 430
    pygame.draw.line(screen, (150, 120, 60), (ax - 2, 55), (ax + 4, 49), 3)
    pygame.draw.line(screen, (225, 233, 246), (ax + 1, 52), (ax + 13, 40), 3)
    screen.blit(font_med.render(f"{player.attack}", True, (205, 215, 245)), (ax + 20, 37))

    screen.blit(font_small.render(
        "WASD / Arrows  Move       Space  Attack       R  Restart       M  Mute" + (" (muted)" if muted else ""),
        True, (195, 200, 218)), (560, 12))
    screen.blit(font_small.render(
        "Potion  heal      Gold  coins      Shard  +ATK      Stairs  descend",
        True, (165, 175, 198)), (560, 40))


def draw_dead_screen(screen, font_big, font_med, font_small, floor_num, best_floor, t):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((8, 6, 10, 210))
    screen.blit(overlay, (0, 0))
    pw, ph = 470, 210
    px, py = (SCREEN_W - pw) // 2, (SCREEN_H - ph) // 2
    pygame.draw.rect(screen, (22, 18, 26), (px, py, pw, ph), border_radius=12)
    pygame.draw.rect(screen, (120, 40, 45), (px, py, pw, ph), 2, border_radius=12)
    pulse = clamp(200 + 55 * math.sin(t * 4))
    msg = font_big.render("YOU DIED", True, (pulse, 70, 70))
    screen.blit(msg, msg.get_rect(center=(SCREEN_W / 2, py + 58)))
    sub = font_med.render(f"Reached floor {floor_num}       Best  {best_floor}", True, (230, 230, 235))
    screen.blit(sub, sub.get_rect(center=(SCREEN_W / 2, py + 115)))
    hint = font_small.render("Press R to try again", True, (200, 200, 210))
    screen.blit(hint, hint.get_rect(center=(SCREEN_W / 2, py + 158)))


def draw_transition(screen, font_big, next_floor_num, t):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((8, 6, 10, 190))
    screen.blit(overlay, (0, 0))
    dots = "." * (1 + int(t * 3) % 3)
    msg = font_big.render(f"Descending to floor {next_floor_num}{dots}", True, (235, 215, 145))
    screen.blit(msg, msg.get_rect(center=(SCREEN_W / 2, SCREEN_H / 2 - 10)))
    for i in range(5):
        w = 130 - i * 20
        yy = SCREEN_H / 2 + 34 + i * 12
        s = 95 + i * 22
        pygame.draw.rect(screen, (s, int(s * 0.8), int(s * 0.4)),
                         (SCREEN_W / 2 - w / 2, yy, w, 9), border_radius=2)


PLAY_BTN = pygame.Rect(SCREEN_W // 2 - 120, 372, 240, 70)


def skin_card_rects():
    n = len(SKINS)
    cw, ch, gap = 158, 250, 18
    total = n * cw + (n - 1) * gap
    x0 = (SCREEN_W - total) // 2
    return [pygame.Rect(x0 + i * (cw + gap), 178, cw, ch) for i in range(n)]


def _menu_backdrop(screen, t):
    screen.fill((12, 10, 16))
    for i in range(70):
        x = (i * 137 + int(t * 12)) % SCREEN_W
        y = (i * 89) % SCREEN_H
        a = 30 + 20 * math.sin(t * 2 + i)
        screen.fill((clamp(18 + a), clamp(15 + a * 0.7), clamp(24 + a)), (x, y, 2, 2))


def draw_menu(screen, font_big, font_med, font_small, t):
    _menu_backdrop(screen, t)
    title = font_big.render("DUNGEON ROGUELIKE", True, (240, 226, 198))
    screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 216)))
    sub = font_small.render("a torch-lit descent", True, (150, 150, 168))
    screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 252)))

    hover = PLAY_BTN.collidepoint(pygame.mouse.get_pos())
    pulse = 0.5 + 0.5 * math.sin(t * 3)
    base = (54, 150, 92) if hover else (44, 122, 78)
    col = tuple(clamp(cc + 34 * pulse) for cc in base)
    pygame.draw.rect(screen, col, PLAY_BTN, border_radius=14)
    pygame.draw.rect(screen, (238, 246, 238), PLAY_BTN, 3, border_radius=14)
    lbl = font_big.render("PLAY", True, (10, 20, 12))
    screen.blit(lbl, lbl.get_rect(center=PLAY_BTN.center))
    hint = font_small.render("click PLAY  or  press Enter", True, (170, 172, 186))
    screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, PLAY_BTN.bottom + 34)))


def draw_select(screen, font_big, font_med, font_small, previews, sel, t):
    _menu_backdrop(screen, t)
    ttl = font_big.render("CHOOSE YOUR KNIGHT", True, (238, 226, 200))
    screen.blit(ttl, ttl.get_rect(center=(SCREEN_W // 2, 92)))

    for i, r in enumerate(skin_card_rects()):
        on = (i == sel)
        pygame.draw.rect(screen, (42, 38, 30) if on else (24, 22, 30), r, border_radius=12)
        pygame.draw.rect(screen, (236, 202, 132) if on else (66, 62, 78), r, 3 if on else 2,
                         border_radius=12)
        spr = pygame.transform.smoothscale(previews[i], (128, 128))
        bob = math.sin(t * 3 + i * 1.3) * 3 if on else 0
        screen.blit(spr, spr.get_rect(center=(r.centerx, r.centery - 8 + bob)))
        nm = font_small.render(SKINS[i]["name"], True, (236, 230, 240) if on else (166, 164, 178))
        screen.blit(nm, nm.get_rect(center=(r.centerx, r.bottom - 26)))

    hint = font_small.render("arrow keys + Enter,  or click a knight", True, (156, 156, 170))
    screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 46)))


# ---------- Main ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Dungeon Roguelike")
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("arial", 40, bold=True)
    font_med = pygame.font.SysFont("arial", 22, bold=True)
    font_small = pygame.font.SysFont("arial", 16)

    assets = build_assets()
    audio = Audio()
    audio.start_music()
    elapsed = 0.0

    best_floor = load_best_floor()

    def start_new_run():
        walls, rooms = generate_dungeon(1)
        start, stairs, enemies, items = populate_floor(1, rooms)
        player = Player(start[0] + 0.5, start[1] + 0.5)
        return 1, walls, stairs, enemies, items, player, place_torches(walls, rooms), compute_ao(walls)

    def go_to_floor(floor_num, player):
        walls, rooms = generate_dungeon(floor_num)
        start, stairs, enemies, items = populate_floor(floor_num, rooms)
        player.x, player.y = start[0] + 0.5, start[1] + 0.5
        player.hp = min(player.max_hp, player.hp + 20)
        return walls, stairs, enemies, items, place_torches(walls, rooms), compute_ao(walls)

    floor_num, walls, stairs, enemies, items, player, torches, ao = start_new_run()
    explored = set()
    popups = []
    particles = []
    state = "menu"
    transition_timer = 0.0
    visible_now = set()
    shake = 0.0
    cam_x, cam_y = compute_camera(player)

    skin_cache = {}
    chosen = 0

    def start_with_skin(idx):
        nonlocal floor_num, walls, stairs, enemies, items, player, torches, ao
        nonlocal state, cam_x, cam_y
        if idx not in skin_cache:
            skin_cache[idx] = build_skin_sprites(SKINS[idx]["pal"])
        assets["spr"].update(skin_cache[idx])
        floor_num, walls, stairs, enemies, items, player, torches, ao = start_new_run()
        explored.clear()
        popups.clear()
        particles.clear()
        visible_now.clear()
        cam_x, cam_y = compute_camera(player)
        state = "playing"

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        elapsed += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if state == "playing" and floor_num > best_floor:
                    best_floor = floor_num
                    save_best_floor(best_floor)
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state in ("select", "playing", "dead"):
                        if state == "playing" and floor_num > best_floor:
                            best_floor = floor_num
                            save_best_floor(best_floor)
                        state = "menu"
                    else:
                        running = False
                elif event.key == pygame.K_m:
                    audio.toggle_mute()
                elif state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        state = "select"
                        audio.play("menu")
                elif state == "select":
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        chosen = (chosen + 1) % len(SKINS)
                        audio.play("menu")
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        chosen = (chosen - 1) % len(SKINS)
                        audio.play("menu")
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        start_with_skin(chosen)
                        audio.play("confirm")
                elif event.key in (pygame.K_SPACE, pygame.K_f) and state == "playing":
                    hits = try_attack(player, enemies, walls)
                    audio.play("swing")
                    if hits:
                        shake = max(shake, 3.0)
                        audio.play("hit")
                        for e in hits:
                            spawn_burst(particles, e.x, e.y, (255, 240, 185), 6, 3.0)
                elif event.key == pygame.K_r and state == "dead":
                    start_with_skin(chosen)
                    audio.play("confirm")
            elif event.type == pygame.MOUSEMOTION and state == "select":
                for i, r in enumerate(skin_card_rects()):
                    if r.collidepoint(event.pos):
                        chosen = i
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "menu" and PLAY_BTN.collidepoint(event.pos):
                    state = "select"
                    audio.play("menu")
                elif state == "select":
                    for i, r in enumerate(skin_card_rects()):
                        if r.collidepoint(event.pos):
                            start_with_skin(i)
                            audio.play("confirm")

        keys = pygame.key.get_pressed()
        shake = max(0.0, shake - dt * 40)

        if state == "playing":
            dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
            dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
            player.move(dx, dy, dt, walls)
            player.attack_cooldown = max(0.0, player.attack_cooldown - dt)
            player.attack_flash = max(0.0, player.attack_flash - dt)
            player.hit_flash = max(0.0, player.hit_flash - dt)

            prev_hp = player.hp
            for enemy in enemies:
                enemy.update(dt, player, walls)
            if player.hp < prev_hp:
                shake = max(shake, 7.0)
                spawn_burst(particles, player.x, player.y, (255, 95, 95), 9, 2.6)
                audio.play("hurt")
            for dead in [e for e in enemies if e.hp <= 0]:
                gold = random.randint(*dead.gold_range)
                player.gold += gold
                player.attack += dead.atk_reward
                popups.append(FloatingText(dead.x, dead.y, f"+{gold}g", (240, 200, 60)))
                popups.append(FloatingText(dead.x, dead.y - 0.5, f"+{dead.atk_reward} ATK", (120, 180, 240)))
                spawn_burst(particles, dead.x, dead.y, dead.color, 14, 4.2)
                audio.play("enemy_death")
            enemies[:] = [e for e in enemies if e.hp > 0]

            for item in items[:]:
                if math.hypot(item.x - player.x, item.y - player.y) < 0.5:
                    apply_item(item, player, popups)
                    spawn_burst(particles, item.x, item.y, ITEM_COLORS[item.kind], 12, 3.2)
                    audio.play(item.kind)
                    items.remove(item)

            for p in popups:
                p.update(dt)
            popups[:] = [p for p in popups if p.timer > 0]

            if random.random() < dt * 7:
                ang = random.uniform(0, math.tau)
                d = random.uniform(1.0, VISION_RADIUS * 0.75)
                particles.append(Particle(player.x + math.cos(ang) * d, player.y + math.sin(ang) * d,
                                          random.uniform(-0.15, 0.15), random.uniform(-0.35, -0.05),
                                          random.uniform(2.0, 4.0), (170, 158, 140), 1, kind="dust"))

            visible_now = compute_visible(walls, player)
            explored |= visible_now

            if torches and random.random() < dt * 12:
                tc, tr, _ = random.choice(torches)
                if (tc, tr) in visible_now:
                    particles.append(Particle(tc + 0.5 + random.uniform(-0.12, 0.12), tr + 0.15,
                                              random.uniform(-0.1, 0.1), random.uniform(-0.7, -0.35),
                                              random.uniform(0.5, 1.1), (255, 170, 70), 2,
                                              grav=-0.6, kind="spark"))

            if player.hp <= 0:
                state = "dead"
                audio.play("player_death")
                if floor_num > best_floor:
                    best_floor = floor_num
                    save_best_floor(best_floor)
            elif math.hypot(player.x - stairs[0], player.y - stairs[1]) < 0.6:
                state = "descending"
                transition_timer = 1.1
                audio.play("stairs")
                if floor_num > best_floor:
                    best_floor = floor_num
                    save_best_floor(best_floor)

        elif state == "descending":
            transition_timer -= dt
            if transition_timer <= 0:
                floor_num += 1
                walls, stairs, enemies, items, torches, ao = go_to_floor(floor_num, player)
                explored.clear()
                particles.clear()
                cam_x, cam_y = compute_camera(player)
                visible_now = compute_visible(walls, player)
                explored |= visible_now
                state = "playing"

        for p in particles:
            p.update(dt)
        particles[:] = [p for p in particles if p.life > 0]

        if state == "menu":
            draw_menu(screen, font_big, font_med, font_small, elapsed)
        elif state == "select":
            draw_select(screen, font_big, font_med, font_small, assets["skin_prev"], chosen, elapsed)
        else:
            tgt_x, tgt_y = compute_camera(player)
            lerp = min(1.0, dt * 9)
            cam_x += (tgt_x - cam_x) * lerp
            cam_y += (tgt_y - cam_y) * lerp
            dcx = cam_x + random.uniform(-shake, shake) / TILE
            dcy = cam_y + random.uniform(-shake, shake) / TILE

            draw_game(screen, player, walls, enemies, items, stairs, explored, visible_now, popups,
                      particles, torches, ao, font_small, elapsed, assets, dcx, dcy)
            draw_hud(screen, font_med, font_small, floor_num, best_floor, player, audio.muted)

            if state == "dead":
                draw_dead_screen(screen, font_big, font_med, font_small, floor_num, best_floor, elapsed)
            elif state == "descending":
                draw_transition(screen, font_big, floor_num + 1, elapsed)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()