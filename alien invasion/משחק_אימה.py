#!/usr/bin/env python3
"""
ТЛЕЮЩИЙ КОРЕНЬ — небольшая метроидвания на pygame.

Вы — странник с фонарём вместо лица. Спуститесь в подземные пещеры,
найдите рывок и двойной прыжок и одолейте Хранителя Корня.

Запуск:  pip install pygame  &&  python ember_root.py

Управление:
  ← → / A D      — движение
  ↑ ↓ / W S      — направление удара, ↑ у фонаря — отдых
  Z / Пробел     — прыжок (держите — выше; в воздухе — двойной прыжок)
  X / J          — удар серпом (↓+X в воздухе — отскок от врагов)
  C / K          — рывок
  V / L (держать)— лечение за 33 единицы света
  Esc            — пауза
"""
import math
import random
import sys

import pygame

SCREEN_W, SCREEN_H = 960, 540
T = 32
FPS = 60

GRAVITY = 2200
MAX_FALL = 900
RUN_SPEED = 290
JUMP_V = 1100
DJUMP_V = 950
JUMP_CUT = 380
DASH_SPEED = 820
DASH_TIME = 0.18
DASH_CD = 0.45
POGO_V = 560
HEAL_TIME = 0.9
GLOW_COST = 33
GLOW_PER_HIT = 11

C_ROCK = (36, 46, 52)
C_ROCK_D = (24, 31, 36)
C_ROCK_TOP = (70, 98, 88)
C_MOSS = (88, 142, 110)
C_SPIKE = (128, 50, 54)
C_SPIKE_L = (190, 92, 86)
C_AMBER = (255, 186, 92)
C_AMBER_L = (255, 228, 160)
C_CLOAK = (82, 54, 92)
C_CLOAK_D = (50, 32, 58)
C_TEAL = (70, 200, 185)
C_WHITE = (236, 232, 220)
C_RED = (230, 80, 70)
C_TEXT = (150, 172, 162)

LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
JUMP_KEYS = (pygame.K_z, pygame.K_SPACE)
ATTACK_KEYS = (pygame.K_x, pygame.K_j)
DASH_KEYS = (pygame.K_c, pygame.K_k)
HEAL_KEYS = (pygame.K_v, pygame.K_l)
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


def sign(v):
    return (v > 0) - (v < 0)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# --------------------------------------------------------------------------
# Мир
# --------------------------------------------------------------------------
class RoomDef:
    def __init__(self, name, w, h, tint, dark):
        self.name, self.w, self.h = name, w, h
        self.tint, self.dark = tint, dark
        self.grid = [["." for _ in range(w)] for _ in range(h)]
        self.objects, self.signs = [], []
        self.left = self.right = None
        self.left_row = self.right_row = None
        for x in range(w):
            self.grid[0][x] = self.grid[h - 1][x] = "#"
        for y in range(h):
            self.grid[y][0] = self.grid[y][w - 1] = "#"

    def box(self, x0, y0, x1, y1, c="#"):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < self.w and 0 <= y < self.h:
                    self.grid[y][x] = c

    def open_left(self, row, target):
        for y in range(row, row + 3):
            self.grid[y][0] = "."
        self.left_row, self.left = row, target

    def open_right(self, row, target):
        for y in range(row, row + 3):
            self.grid[y][self.w - 1] = "."
        self.right_row, self.right = row, target

    def add(self, kind, tx, ty):
        self.objects.append({"kind": kind, "tx": tx, "ty": ty,
                             "id": f"{self.name}:{kind}:{tx}:{ty}"})

    def sign(self, tx, ty, text):
        self.signs.append((tx * T, ty * T, text))


def build_world():
    rooms = []

    # 0 — стартовый привал
    r = RoomDef("Тлеющий привал", 40, 17, ((10, 20, 26), (22, 40, 44)), 120)
    r.box(0, 15, 39, 16)
    r.box(12, 11, 16, 11)
    r.box(21, 8, 26, 8)
    r.box(31, 12, 33, 14)
    r.add("shrine", 8, 14)
    r.add("shard", 14, 10)
    r.add("shard", 23, 7)
    r.add("shard", 24, 7)
    r.sign(4, 9, "Стрелки / A D — идти     Z / Пробел — прыжок")
    r.sign(9, 12, "Вверх у фонаря — отдых")
    r.sign(22, 12, "X — удар серпом   Вверх/Вниз + X — удар вверх / вниз")
    r.open_right(12, 1)
    rooms.append(r)

    # 1 — галерея
    r = RoomDef("Грибная галерея", 90, 17, ((10, 22, 18), (24, 44, 32)), 150)
    r.box(0, 15, 89, 16)
    r.box(20, 15, 22, 15, "^")
    r.box(41, 15, 44, 15, "^")
    r.box(66, 15, 76, 15, "^")
    r.box(28, 11, 33, 11)
    r.box(36, 8, 40, 8)
    r.box(48, 11, 52, 11)
    r.box(55, 9, 58, 9)
    r.box(45, 1, 47, 4)
    r.box(78, 11, 80, 14)
    r.add("crawler", 12, 14)
    r.add("crawler", 31, 10)
    r.add("crawler", 52, 14)
    r.add("flyer", 38, 4)
    r.add("flyer", 57, 5)
    r.add("crawler", 85, 14)
    r.add("shard", 38, 7)
    r.add("shard", 56, 8)
    r.add("dash", 62, 13)
    r.add("shrine", 84, 14)
    r.sign(6, 11, "Удары копят свет. Держите V — лечение")
    r.open_left(12, 0)
    r.open_right(12, 2)
    rooms.append(r)

    # 2 — колодец
    r = RoomDef("Колодец спор", 40, 34, ((8, 16, 28), (20, 34, 52)), 170)
    r.box(0, 32, 39, 33)
    for x0, x1, y in [(14, 19, 26), (24, 29, 20), (14, 19, 15)]:
        r.box(x0, y, x1, y)
    r.box(22, 5, 39, 5)
    r.add("crawler", 22, 31)
    r.add("crawler", 29, 31)
    r.add("flyer", 8, 16)
    r.add("flyer", 22, 9)
    r.add("shard", 15, 25)
    r.add("shard", 34, 4)
    r.add("djump", 35, 30)
    r.sign(20, 28, "Наверх не допрыгнуть...")
    r.open_left(29, 1)
    r.open_right(2, 3)
    rooms.append(r)

    # 3 — логово босса
    r = RoomDef("Логово Корня", 40, 20, ((22, 10, 12), (44, 20, 20)), 140)
    r.box(0, 18, 39, 19)
    r.box(1, 5, 5, 5)
    r.box(0, 7, 0, 17)
    r.open_left(2, 2)
    rooms.append(r)
    return rooms


_LIGHTS, _GLOWS = {}, {}


def make_light(radius, strength):
    key = (radius, strength)
    if key not in _LIGHTS:
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        steps = 32
        for i in range(steps, 0, -1):
            t = i / steps
            a = int(strength * (1 - t ** 1.6))
            pygame.draw.circle(s, (0, 0, 0, a), (radius, radius), max(1, int(radius * t)))
        _LIGHTS[key] = s
    return _LIGHTS[key]


def make_glow(radius, color, intensity):
    key = (radius, color, intensity)
    if key not in _GLOWS:
        s = pygame.Surface((radius * 2, radius * 2))
        steps = 24
        for i in range(steps, 0, -1):
            t = i / steps
            k = intensity * (1 - t) ** 2
            pygame.draw.circle(s, tuple(int(c * k) for c in color), (radius, radius),
                               max(1, int(radius * t)))
        _GLOWS[key] = s
    return _GLOWS[key]


class Room:
    def __init__(self, d, idx):
        self.d, self.idx = d, idx
        self.w, self.h = d.w, d.h
        self.grid = [row[:] for row in d.grid]
        self.glows = []
        self.render()
        self.bg_far = self.make_far()
        self.bg_mid = self.make_mid()

    def reset(self):
        if self.grid != self.d.grid:
            self.grid = [row[:] for row in self.d.grid]
            self.render()

    def is_solid(self, tx, ty, oob=False):
        if ty < 0 or ty >= self.h:
            return True
        if tx < 0 or tx >= self.w:
            return oob
        return self.grid[ty][tx] == "#"

    def is_spike(self, tx, ty):
        return 0 <= ty < self.h and 0 <= tx < self.w and self.grid[ty][tx] == "^"

    def solids_near(self, rect, oob):
        out = []
        for ty in range(rect.top // T, (rect.bottom - 1) // T + 1):
            for tx in range(rect.left // T, (rect.right - 1) // T + 1):
                if self.is_solid(tx, ty, oob):
                    out.append(pygame.Rect(tx * T, ty * T, T, T))
        return out

    def touching_ground(self, rect, oob=True):
        ty = rect.bottom // T
        for tx in range(rect.left // T, (rect.right - 1) // T + 1):
            if self.is_solid(tx, ty, oob):
                return True
        return False

    def render(self):
        surf = pygame.Surface((self.w * T, self.h * T), pygame.SRCALPHA)
        rng = random.Random(self.idx * 977 + 13)
        self.glows = []
        g = self.grid
        for ty in range(self.h):
            for tx in range(self.w):
                c = g[ty][tx]
                x, y = tx * T, ty * T
                if c == "#":
                    v = rng.randint(-5, 5)
                    pygame.draw.rect(surf, tuple(clamp(ch + v, 0, 255) for ch in C_ROCK), (x, y, T, T))
                    if rng.random() < 0.3:
                        pygame.draw.line(surf, C_ROCK_D, (x + rng.randint(4, 28), y + rng.randint(6, 28)),
                                         (x + rng.randint(4, 28), y + rng.randint(6, 28)), 2)
                    up_open = ty > 0 and g[ty - 1][tx] != "#"
                    if up_open:
                        pygame.draw.rect(surf, C_ROCK_TOP, (x, y, T, 5))
                        for _ in range(3):
                            pygame.draw.circle(surf, C_MOSS, (x + rng.randint(2, 30), y + rng.randint(1, 5)),
                                               rng.randint(2, 4))
                        if g[ty - 1][tx] == "." and rng.random() < 0.13:
                            col = C_TEAL if rng.random() < 0.6 else C_AMBER
                            mx = x + rng.randint(8, 24)
                            hgt = rng.randint(6, 12)
                            pygame.draw.line(surf, (170, 170, 150), (mx, y), (mx, y - hgt), 2)
                            pygame.draw.ellipse(surf, col, (mx - 6, y - hgt - 4, 12, 7))
                            self.glows.append((mx, y - hgt, col))
                    if tx > 0 and g[ty][tx - 1] != "#":
                        pygame.draw.line(surf, (52, 66, 70), (x, y), (x, y + T - 1), 2)
                    if tx < self.w - 1 and g[ty][tx + 1] != "#":
                        pygame.draw.line(surf, (52, 66, 70), (x + T - 2, y), (x + T - 2, y + T - 1), 2)
                    if ty < self.h - 1 and g[ty + 1][tx] != "#":
                        pygame.draw.rect(surf, C_ROCK_D, (x, y + T - 4, T, 4))
                        if rng.random() < 0.35:
                            sx = x + rng.randint(4, 28)
                            pygame.draw.line(surf, (60, 100, 80), (sx, y + T), (sx, y + T + rng.randint(5, 14)), 2)
                elif c == "^":
                    pygame.draw.rect(surf, (40, 22, 26), (x, y + T - 6, T, 6))
                    for i in range(3):
                        bx = x + 1 + i * 10
                        tip = y + 6 + rng.randint(0, 6)
                        pygame.draw.polygon(surf, C_SPIKE, [(bx, y + T), (bx + 5, tip), (bx + 10, y + T)])
                        pygame.draw.line(surf, C_SPIKE_L, (bx + 5, tip), (bx + 3, y + T - 4), 1)
        self.surface = surf

    def make_far(self):
        top, bot = self.d.tint
        s = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            s.fill(tuple(int(a + (b - a) * t) for a, b in zip(top, bot)), (0, y, SCREEN_W, 1))
        return s

    def make_mid(self):
        w = int(self.w * T * 0.5 + SCREEN_W)
        h = int(self.h * T * 0.5 + SCREEN_H)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        rng = random.Random(self.idx * 31 + 5)
        top, bot = self.d.tint
        col = tuple(int(c * 0.55) for c in bot)
        col2 = tuple(min(255, int(c * 1.25)) for c in bot)
        for _ in range(w // 60):
            x = rng.randint(0, w)
            ln = rng.randint(40, 180)
            wd = rng.randint(16, 50)
            pygame.draw.polygon(s, col, [(x - wd, 0), (x + wd, 0), (x + rng.randint(-8, 8), ln)])
        for _ in range(w // 160):
            x = rng.randint(0, w)
            wd = rng.randint(30, 70)
            pygame.draw.rect(s, col, (x, 0, wd, h))
            for yy in range(0, h, 40):
                pygame.draw.line(s, col2, (x + 4, yy + rng.randint(0, 30)), (x + wd - 4, yy + rng.randint(0, 30)), 1)
        for _ in range(w // 90):
            x = rng.randint(0, w)
            ln = rng.randint(40, 140)
            wd = rng.randint(20, 60)
            pygame.draw.polygon(s, col, [(x - wd, h), (x + wd, h), (x, h - ln)])
        for _ in range(w // 25):
            pygame.draw.circle(s, (*col2, 120), (rng.randint(0, w), rng.randint(0, h)), rng.randint(1, 2))
        return s


# --------------------------------------------------------------------------
# Физика
# --------------------------------------------------------------------------
def collide_move(obj, dx, dy, room, oob_solid):
    hit_x = hit_y = False
    if dx:
        obj.fx += dx
        obj.rect.x = round(obj.fx)
        for tr in room.solids_near(obj.rect, oob_solid):
            if obj.rect.colliderect(tr):
                if dx > 0:
                    obj.rect.right = tr.left
                else:
                    obj.rect.left = tr.right
                obj.fx = float(obj.rect.x)
                hit_x = True
    if dy:
        obj.fy += dy
        obj.rect.y = round(obj.fy)
        for tr in room.solids_near(obj.rect, oob_solid):
            if obj.rect.colliderect(tr):
                if dy > 0:
                    obj.rect.bottom = tr.top
                else:
                    obj.rect.top = tr.bottom
                obj.fy = float(obj.rect.y)
                hit_y = True
    return hit_x, hit_y


class Input:
    def __init__(self):
        self.left = self.right = self.up = self.down = False
        self.jump_h = self.heal_h = False
        self.jump_p = self.attack_p = self.dash_p = self.up_p = False
        self.confirm = self.pause_p = self.quit = False


# --------------------------------------------------------------------------
# Игрок
# --------------------------------------------------------------------------
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 22, 38)
        self.has_dash = self.has_djump = False
        self.hp = self.max_hp = 5
        self.glow = 0
        self.place(x, y)
        self.reset_motion()

    def reset_motion(self):
        self.vx = self.vy = 0.0
        self.facing = 1
        self.on_ground = False
        self.coyote = self.jump_buf = 0.0
        self.can_djump = self.can_dash = True
        self.dash_t = self.dash_cd = 0.0
        self.dash_dir = 1
        self.attack_cd = 0.0
        self.swing = None
        self.inv = 0.0
        self.knock_t = 0.0
        self.heal_t = 0.0
        self.pogo = False
        self.anim = 0.0
        self.scarf = [self.rect.center] * 6

    def place(self, x, y):
        self.rect.midbottom = (int(x), int(y))
        self.fx, self.fy = float(self.rect.x), float(self.rect.y)
        self.scarf = [self.rect.center] * 6

    def swing_rect(self):
        s, r = self.swing, self.rect
        if s["dir"] == "up":
            return pygame.Rect(r.centerx - 30, r.top - 54, 60, 60)
        if s["dir"] == "down":
            return pygame.Rect(r.centerx - 30, r.bottom - 6, 60, 58)
        if s["facing"] > 0:
            return pygame.Rect(r.centerx, r.centery - 26, 70, 52)
        return pygame.Rect(r.centerx - 70, r.centery - 26, 70, 52)

    def update(self, dt, inp, game):
        room = game.room
        self.anim += dt
        for n in ("inv", "dash_cd", "attack_cd", "coyote", "jump_buf", "knock_t"):
            setattr(self, n, max(0.0, getattr(self, n) - dt))
        move = int(inp.right) - int(inp.left)
        if inp.jump_p:
            self.jump_buf = 0.12

        if self.dash_t > 0:
            self.dash_t -= dt
            self.vx = self.dash_dir * DASH_SPEED
            self.vy = 0
            game.burst(self.rect.centerx, self.rect.centery + random.randint(-12, 12), 1,
                       C_AMBER, 40, 0.3, 3, 0)
        else:
            if self.knock_t <= 0:
                self.vx = move * RUN_SPEED
                if move:
                    self.facing = move
            self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)
            if self.jump_buf > 0:
                if self.on_ground or self.coyote > 0:
                    self.vy = -JUMP_V
                    self.jump_buf = self.coyote = 0
                    self.pogo = False
                    game.burst(self.rect.centerx, self.rect.bottom, 6, (150, 160, 150), 120, 0.35, 3, 300)
                elif self.has_djump and self.can_djump:
                    self.vy = -DJUMP_V
                    self.can_djump = False
                    self.jump_buf = 0
                    self.pogo = False
                    game.burst(self.rect.centerx, self.rect.bottom, 12, C_TEAL, 180, 0.4, 3, 0)
            if not inp.jump_h and self.vy < -JUMP_CUT and not self.pogo:
                self.vy = -JUMP_CUT
            if self.vy >= 0:
                self.pogo = False
            if inp.dash_p and self.has_dash and self.can_dash and self.dash_cd <= 0:
                self.dash_t = DASH_TIME
                self.dash_dir = move or self.facing
                self.facing = self.dash_dir
                self.can_dash = False
                self.dash_cd = DASH_CD
                self.vy = 0
                self.heal_t = 0
                game.burst(self.rect.centerx, self.rect.centery, 10, C_AMBER_L, 200, 0.3, 3, 0)

        healing = (inp.heal_h and self.on_ground and self.glow >= GLOW_COST and self.hp < self.max_hp
                   and move == 0 and self.dash_t <= 0 and self.knock_t <= 0)
        if healing:
            self.heal_t += dt
            self.vx = 0
            if random.random() < 0.6:
                a = random.uniform(0, math.tau)
                px = self.rect.centerx + math.cos(a) * 40
                py = self.rect.centery + math.sin(a) * 40
                game.particles.append([px, py, -math.cos(a) * 90, -math.sin(a) * 90, 0.45, 0.45, C_AMBER_L, 3, 0])
            if self.heal_t >= HEAL_TIME:
                self.hp += 1
                self.glow -= GLOW_COST
                self.heal_t = 0
                game.burst(self.rect.centerx, self.rect.centery, 24, C_AMBER_L, 220, 0.6, 3, -100)
                game.shake(4, 0.15)
        else:
            self.heal_t = 0

        if inp.attack_p and self.attack_cd <= 0 and self.dash_t <= 0:
            d = "up" if inp.up else ("down" if inp.down and not self.on_ground else "side")
            self.swing = {"dir": d, "t": 0.14, "facing": self.facing, "hit": set()}
            self.attack_cd = 0.3
            self.heal_t = 0
        if self.swing:
            self.swing["t"] -= dt
            if self.swing["t"] <= 0:
                self.swing = None

        vy0 = self.vy
        _, hy = collide_move(self, self.vx * dt, self.vy * dt, room, False)
        if hy:
            self.vy = 0
        was = self.on_ground
        self.on_ground = room.touching_ground(self.rect, False)
        if self.on_ground:
            if not was and vy0 > 500:
                game.burst(self.rect.centerx, self.rect.bottom, 8, (150, 160, 150), 140, 0.35, 3, 300)
            self.coyote = 0.09
            self.can_djump = True
            if self.dash_t <= 0:
                self.can_dash = True

        anchor = (self.rect.centerx - self.facing * 5, self.rect.bottom - 24)
        self.scarf[0] = anchor
        for i in range(1, len(self.scarf)):
            px, py = self.scarf[i - 1]
            sx, sy = self.scarf[i]
            tx = px - self.facing * 5
            ty = py + 1 + math.sin(self.anim * 9 + i) * 1.6
            self.scarf[i] = (sx + (tx - sx) * 0.5, sy + (ty - sy) * 0.5)

    def hurt(self, game, from_x):
        if self.inv > 0 or game.state != "play":
            return False
        self.hp -= 1
        self.inv = 1.2
        d = sign(self.rect.centerx - from_x) or -self.facing
        self.vx, self.vy = d * 340, -380
        self.knock_t = 0.22
        self.dash_t = self.heal_t = 0
        self.swing = None
        game.shake(10, 0.25)
        game.hitstop = 0.1
        game.flash = 0.15
        game.burst(self.rect.centerx, self.rect.centery, 16, C_WHITE, 260, 0.45, 3, 200)
        if self.hp <= 0:
            game.kill_player()
        return True

    def draw(self, s, cam, t):
        if self.inv > 0 and int(self.inv * 18) % 2 == 0:
            return
        x = self.rect.centerx - cam[0]
        y = self.rect.bottom - cam[1]
        f = self.facing
        if len(self.scarf) > 1:
            pts = [(sx - cam[0], sy - cam[1]) for sx, sy in self.scarf]
            pygame.draw.lines(s, C_TEAL, False, pts, 4)
        moving = abs(self.vx) > 20 and self.on_ground
        sway = math.sin(self.anim * 16) * 3 if moving else 0
        lean = -f * 5 if self.dash_t > 0 else 0
        cloak = [(x - 7 + lean, y - 26), (x + 7 + lean, y - 26), (x + 12 + sway, y), (x - 12 + sway, y)]
        pygame.draw.polygon(s, C_CLOAK, cloak)
        pygame.draw.polygon(s, C_CLOAK_D, cloak, 2)
        for i in range(3):
            bx = x - 10 + i * 8 + sway
            pygame.draw.line(s, C_CLOAK_D, (bx, y - 6), (bx + 2, y), 2)
        hx, hy = x + lean, y - 31
        pygame.draw.circle(s, C_CLOAK_D, (hx, hy), 14)
        pygame.draw.circle(s, C_AMBER, (hx + f * 2, hy + 1), 10)
        pygame.draw.circle(s, C_AMBER_L, (hx + f * 2, hy + 1), 6)
        for ex in (-4, 3):
            pygame.draw.ellipse(s, (50, 24, 22), (hx + f * 3 + ex - 1, hy - 3, 3, 7))
        fl = 6 + math.sin(t * 22) * 2
        pygame.draw.polygon(s, C_AMBER_L, [(hx - 3, hy - 12), (hx + 3, hy - 12), (hx - f * 2, hy - 12 - fl)])
        if self.heal_t > 0:
            pygame.draw.circle(s, C_AMBER_L, (x, y - 20), int(26 * self.heal_t / HEAL_TIME) + 4, 2)
        if self.swing:
            self.draw_swing(s, cam)

    def draw_swing(self, s, cam):
        sw = self.swing
        p = 1 - sw["t"] / 0.14
        base = {"up": -math.pi / 2, "down": math.pi / 2}.get(sw["dir"], 0 if sw["facing"] > 0 else math.pi)
        cx = self.rect.centerx - cam[0]
        cy = self.rect.centery - cam[1]
        span = 2.4
        a0 = base - span / 2
        a1 = a0 + span * min(1, p * 1.6)
        n = 10
        outer = [(cx + math.cos(a0 + (a1 - a0) * i / n) * 64, cy + math.sin(a0 + (a1 - a0) * i / n) * 64)
                 for i in range(n + 1)]
        inner = [(cx + math.cos(a0 + (a1 - a0) * i / n) * 44, cy + math.sin(a0 + (a1 - a0) * i / n) * 44)
                 for i in reversed(range(n + 1))]
        pygame.draw.polygon(s, C_WHITE, outer + inner)
        pygame.draw.lines(s, C_AMBER_L, False, outer, 2)


# --------------------------------------------------------------------------
# Враги
# --------------------------------------------------------------------------
class Crawler:
    drop = 3

    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 34, 24)
        self.rect.midbottom = (x, y)
        self.fx, self.fy = float(self.rect.x), float(self.rect.y)
        self.vy = 0.0
        self.dir = random.choice((-1, 1))
        self.hp = 3
        self.flash = self.knock = 0.0
        self.kvx = 0.0
        self.alive = True
        self.anim = random.random() * 10

    def hurt(self, dmg, dx, dy, game):
        self.hp -= dmg
        self.flash = 0.15
        self.knock = 0.15
        self.kvx = dx * 260 if dx else 0
        if self.hp <= 0:
            self.alive = False
            game.enemy_died(self)

    def update(self, dt, game):
        room = game.room
        self.anim += dt
        self.flash = max(0, self.flash - dt)
        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)
        if self.knock > 0:
            self.knock -= dt
            vx = self.kvx
        else:
            vx = self.dir * 70
        hx, hy = collide_move(self, vx * dt, self.vy * dt, room, True)
        if hy:
            self.vy = 0
        if hx and self.knock <= 0:
            self.dir *= -1
        elif self.knock <= 0 and room.touching_ground(self.rect):
            front = self.rect.right + 2 if self.dir > 0 else self.rect.left - 3
            if not room.is_solid(front // T, self.rect.bottom // T, True):
                self.dir *= -1

    def draw(self, s, cam, t):
        r = self.rect.move(-cam[0], -cam[1])
        shell = C_WHITE if self.flash > 0 else (52, 74, 70)
        for i in range(3):
            lx = r.left + 7 + i * 10
            k = math.sin(self.anim * 14 + i * 2) * 3
            pygame.draw.line(s, (30, 40, 40), (lx, r.bottom - 6), (lx + k, r.bottom), 2)
        pygame.draw.ellipse(s, shell, (r.left, r.top, r.w, r.h - 2))
        pygame.draw.ellipse(s, (30, 44, 42), (r.left, r.top, r.w, r.h - 2), 2)
        for i in range(3):
            pygame.draw.circle(s, C_TEAL, (r.left + 9 + i * 8, r.top + 7 + (i % 2) * 3), 2)
        ex = r.right - 6 if self.dir > 0 else r.left + 6
        pygame.draw.circle(s, C_AMBER, (ex, r.centery + 2), 3)


class Flyer:
    drop = 2

    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 28, 22)
        self.rect.center = (x, y)
        self.fx, self.fy = float(self.rect.x), float(self.rect.y)
        self.vx = self.vy = 0.0
        self.hp = 2
        self.flash = self.knock = 0.0
        self.alive = True
        self.aggro = False
        self.anim = random.random() * 10

    def hurt(self, dmg, dx, dy, game):
        self.hp -= dmg
        self.flash = 0.15
        self.knock = 0.25
        self.vx, self.vy = dx * 320, dy * 320
        if self.hp <= 0:
            self.alive = False
            game.enemy_died(self)

    def update(self, dt, game):
        p = game.player
        self.anim += dt
        self.flash = max(0, self.flash - dt)
        dx = p.rect.centerx - self.rect.centerx
        dy = p.rect.centery - 10 - self.rect.centery
        d = math.hypot(dx, dy) or 1
        if d < 320:
            self.aggro = True
        if self.knock > 0:
            self.knock -= dt
            self.vx *= 0.92
            self.vy *= 0.92
        elif self.aggro:
            self.vx += dx / d * 520 * dt
            self.vy += dy / d * 520 * dt
            sp = math.hypot(self.vx, self.vy)
            if sp > 170:
                self.vx, self.vy = self.vx / sp * 170, self.vy / sp * 170
        else:
            self.vx = math.cos(self.anim * 0.8) * 40
            self.vy = math.sin(self.anim * 1.7) * 30
        hx, hy = collide_move(self, self.vx * dt, self.vy * dt, game.room, True)
        if hx:
            self.vx *= -0.6
        if hy:
            self.vy *= -0.6

    def draw(self, s, cam, t):
        r = self.rect.move(-cam[0], -cam[1])
        flap = abs(math.sin(self.anim * 18))
        wing = (110, 90, 130) if self.flash <= 0 else C_WHITE
        ww, wh = 20, int(6 + flap * 12)
        pygame.draw.ellipse(s, wing, (r.centerx - ww - 2, r.centery - wh, ww, wh))
        pygame.draw.ellipse(s, wing, (r.centerx + 2, r.centery - wh, ww, wh))
        body = C_WHITE if self.flash > 0 else (70, 56, 84)
        pygame.draw.ellipse(s, body, (r.centerx - 8, r.centery - 8, 16, 20))
        pygame.draw.circle(s, (240, 120, 160), (r.centerx, r.centery - 2), 3)


class Boss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 76, 86)
        self.rect.midbottom = (x, y)
        self.fx, self.fy = float(self.rect.x), float(self.rect.y)
        self.vx = self.vy = 0.0
        self.max_hp = self.hp = 28
        self.state, self.t = "intro", 0.0
        self.facing = -1
        self.flash = 0.0
        self.alive = True
        self.on_ground = False
        self.anim = 0.0
        self.last = None
        self.jit = 0

    @property
    def phase2(self):
        return self.hp <= self.max_hp // 2

    def set_state(self, st, t=0.0):
        self.state, self.t = st, t

    def hurt(self, dmg, dx, dy, game):
        if self.state == "dead":
            return
        self.hp -= dmg
        self.flash = 0.1
        if self.hp <= 0:
            self.set_state("dead", 2.2)
            self.vx = 0
            game.on_boss_dead(self)

    def choose(self, game):
        dxp = game.player.rect.centerx - self.rect.centerx
        opts = ["hop", "charge", "slam"]
        if self.last in opts and random.random() < 0.65:
            opts.remove(self.last)
        c = random.choice(opts)
        self.last = c
        self.facing = sign(dxp) or self.facing
        if c == "hop":
            self.vy = -720
            self.vx = clamp(dxp / 0.65, -440, 440)
            self.set_state("air")
        elif c == "charge":
            self.set_state("wind", 0.4 if self.phase2 else 0.6)
        else:
            self.vy = -980
            self.vx = clamp(dxp / 0.9, -340, 340)
            self.set_state("slam")

    def update(self, dt, game):
        room = game.room
        self.anim += dt
        self.flash = max(0, self.flash - dt)
        self.t -= dt
        self.jit = 0
        if self.state == "dead":
            if random.random() < 0.5:
                game.burst(self.rect.centerx + random.randint(-30, 30), self.rect.centery + random.randint(-30, 30),
                           3, random.choice((C_AMBER, C_RED, C_AMBER_L)), 200, 0.6, 4, -50)
            if self.t <= 0:
                self.alive = False
                game.burst(self.rect.centerx, self.rect.centery, 60, C_AMBER_L, 420, 1.2, 4, 100)
            return
        self.vy = min(self.vy + GRAVITY * dt, 1100)
        hx, hy = collide_move(self, self.vx * dt, self.vy * dt, room, True)
        if hy:
            self.vy = 0
        ground = room.touching_ground(self.rect)
        landed = ground and not self.on_ground
        self.on_ground = ground
        st = self.state
        if landed:
            game.burst(self.rect.centerx, self.rect.bottom, 14, (140, 120, 110), 220, 0.5, 4, 400)
        if st == "intro":
            if landed:
                game.shake(16, 0.5)
                self.set_state("roar", 1.3)
        elif st == "roar":
            self.jit = random.randint(-2, 2)
            if self.t <= 0:
                self.set_state("idle", 0.6)
        elif st == "idle":
            self.vx *= 0.8
            if self.t <= 0 and self.on_ground:
                self.choose(game)
        elif st == "air":
            if landed:
                self.vx = 0
                game.shake(6, 0.15)
                self.set_state("idle", 0.25 if self.phase2 else 0.5)
        elif st == "wind":
            self.vx = 0
            self.jit = random.randint(-3, 3)
            if self.t <= 0:
                self.set_state("charge")
                self.vx = self.facing * (580 if self.phase2 else 470)
        elif st == "charge":
            if random.random() < 0.5:
                game.burst(self.rect.centerx - self.facing * 30, self.rect.bottom, 2, (140, 120, 110), 80, 0.4, 3, 200)
            if hx:
                self.vx = 0
                game.shake(14, 0.35)
                n = 4 if self.phase2 else 2
                for _ in range(n):
                    game.hazards.append(Hazard("rock", random.randint(3, room.w - 3) * T, T + 12,
                                               delay=random.uniform(0.3, 0.9)))
                self.set_state("stun", 0.55 if self.phase2 else 0.8)
        elif st == "stun":
            if self.t <= 0:
                self.set_state("idle", 0.3)
        elif st == "slam":
            if landed:
                self.vx = 0
                game.shake(18, 0.4)
                sp = 460 if self.phase2 else 380
                for d in (-1, 1):
                    game.hazards.append(Hazard("wave", self.rect.centerx + d * 40, self.rect.bottom, d * sp))
                self.set_state("idle", 0.4 if self.phase2 else 0.65)

    def draw(self, s, cam, t):
        r = self.rect.move(-cam[0] + self.jit, -cam[1])
        hit = self.flash > 0
        body = C_WHITE if hit else (74, 46, 38)
        cap = C_WHITE if hit else ((140, 52, 44) if self.phase2 else (112, 54, 44))
        if self.state == "dead":
            sink = int((2.2 - self.t) * 20)
            r = r.move(random.randint(-3, 3), sink)
        for i in range(5):
            lx = r.left + 8 + i * 15
            k = math.sin(self.anim * (14 if self.state == "charge" else 4) + i) * 6
            pygame.draw.line(s, (54, 34, 30), (lx, r.bottom - 22), (lx + k, r.bottom), 5)
        pygame.draw.ellipse(s, body, (r.left + 4, r.top + 22, r.w - 8, r.h - 26))
        pygame.draw.ellipse(s, (40, 24, 20), (r.left + 4, r.top + 22, r.w - 8, r.h - 26), 3)
        pygame.draw.ellipse(s, cap, (r.left - 16, r.top - 4, r.w + 32, 46))
        pygame.draw.ellipse(s, (60, 26, 22), (r.left - 16, r.top - 4, r.w + 32, 46), 3)
        for i, (sx, sy) in enumerate([(-22, 8), (0, 2), (22, 8), (-10, 20), (14, 20)]):
            glow = 0.6 + 0.4 * math.sin(t * 4 + i)
            pygame.draw.circle(s, tuple(int(c * glow) for c in C_AMBER), (r.centerx + sx, r.top + 14 + sy), 5)
        ex = r.centerx + self.facing * 12
        eye = (255, 240, 200) if self.state in ("wind", "roar") else (255, 90, 70)
        pygame.draw.circle(s, eye, (ex - 11, r.top + 54), 5)
        pygame.draw.circle(s, eye, (ex + 11, r.top + 54), 5)


class Hazard:
    def __init__(self, kind, x, y, vx=0.0, delay=0.0):
        self.kind, self.delay = kind, delay
        self.alive = True
        self.t = 0.0
        if kind == "wave":
            self.rect = pygame.Rect(0, 0, 24, 36)
            self.rect.midbottom = (x, y)
        else:
            self.rect = pygame.Rect(0, 0, 22, 22)
            self.rect.center = (x, y)
        self.fx, self.fy = float(self.rect.x), float(self.rect.y)
        self.vx, self.vy = vx, 0.0

    @property
    def active(self):
        return self.delay <= 0

    def update(self, dt, game):
        room = game.room
        if self.delay > 0:
            self.delay -= dt
            if random.random() < 0.5:
                game.particles.append([self.rect.centerx + random.uniform(-6, 6), T + 4, 0, 120,
                                       0.4, 0.4, (120, 110, 100), 2, 300])
            return
        self.t += dt
        if self.kind == "wave":
            self.fx += self.vx * dt
            self.rect.x = round(self.fx)
            front = self.rect.right if self.vx > 0 else self.rect.left
            if room.is_solid(front // T, (self.rect.bottom - 6) // T, True) or self.t > 4:
                self.alive = False
                game.burst(self.rect.centerx, self.rect.centery, 10, C_AMBER, 160, 0.4, 3, 0)
            if random.random() < 0.6:
                game.particles.append([self.rect.centerx, self.rect.bottom - 4, -self.vx * 0.1,
                                       -random.uniform(40, 140), 0.4, 0.4, C_AMBER, 3, 0])
        else:
            self.vy = min(self.vy + GRAVITY * dt, 900)
            _, hy = collide_move(self, 0, self.vy * dt, room, True)
            if hy:
                self.alive = False
                game.burst(self.rect.centerx, self.rect.bottom, 12, (130, 120, 110), 200, 0.5, 3, 500)
                game.shake(4, 0.1)

    def draw(self, s, cam, t):
        if self.delay > 0:
            return
        r = self.rect.move(-cam[0], -cam[1])
        if self.kind == "wave":
            for i, col in enumerate((C_RED, C_AMBER, C_AMBER_L)):
                h = r.h - i * 9 + math.sin(t * 30 + i) * 4
                w = r.w // 2 - i * 3
                pygame.draw.polygon(s, col, [(r.centerx - w, r.bottom), (r.centerx + w, r.bottom),
                                             (r.centerx, r.bottom - h)])
        else:
            pts = [(r.centerx + math.cos(a) * 11 * (0.8 + 0.2 * ((k * 7) % 3)),
                    r.centery + math.sin(a) * 11 * (0.8 + 0.2 * ((k * 5) % 3)))
                   for k, a in enumerate([i * math.tau / 7 for i in range(7)])]
            pygame.draw.polygon(s, (110, 100, 96), pts)
            pygame.draw.polygon(s, (60, 54, 52), pts, 2)


# --------------------------------------------------------------------------
# Предметы
# --------------------------------------------------------------------------
class Shard:
    def __init__(self, x, y, vx=0.0, vy=0.0, pid=None):
        self.rect = pygame.Rect(0, 0, 12, 14)
        self.rect.center = (x, y)
        self.fx, self.fy = float(self.rect.x), float(self.rect.y)
        self.vx, self.vy = vx, vy
        self.pid = pid
        self.static = pid is not None
        self.age = random.random() * 3 if self.static else 0.0
        self.alive = True

    def update(self, dt, game):
        self.age += dt
        p = game.player
        if not self.static:
            dx = p.rect.centerx - self.rect.centerx
            dy = p.rect.centery - self.rect.centery
            d = math.hypot(dx, dy) or 1
            if self.age > 0.45 and d < 110:
                self.fx += dx / d * 520 * dt
                self.fy += dy / d * 520 * dt
                self.rect.topleft = (round(self.fx), round(self.fy))
            else:
                self.vy = min(self.vy + GRAVITY * 0.7 * dt, 700)
                vy0 = self.vy
                hx, hy = collide_move(self, self.vx * dt, self.vy * dt, game.room, True)
                if hy:
                    self.vy = -vy0 * 0.35 if vy0 > 150 else 0
                    self.vx *= 0.6
                if hx:
                    self.vx *= -0.5
        if self.rect.colliderect(p.rect):
            self.alive = False
            game.shards += 1
            if self.pid:
                game.collected.add(self.pid)
            game.burst(self.rect.centerx, self.rect.centery, 6, (180, 240, 230), 120, 0.3, 2, 0)

    def draw(self, s, cam, t):
        bob = math.sin(self.age * 3) * 3 if self.static else 0
        cx = self.rect.centerx - cam[0]
        cy = self.rect.centery - cam[1] + bob
        pts = [(cx, cy - 7), (cx + 5, cy), (cx, cy + 7), (cx - 5, cy)]
        pygame.draw.polygon(s, (150, 230, 220), pts)
        pygame.draw.polygon(s, (230, 255, 250), [(cx, cy - 7), (cx + 2, cy - 1), (cx - 2, cy - 1)])


class Orb:
    INFO = {
        "dash": ("Рывок", "Нажмите C / K, чтобы рвануться вперёд — даже в воздухе"),
        "djump": ("Споровые крылья", "Нажмите прыжок ещё раз в воздухе"),
    }

    def __init__(self, kind, x, y, pid):
        self.kind, self.pid = kind, pid
        self.rect = pygame.Rect(0, 0, 28, 28)
        self.rect.center = (x, y)
        self.alive = True

    def update(self, dt, game):
        p = game.player
        if self.rect.colliderect(p.rect):
            self.alive = False
            game.collected.add(self.pid)
            if self.kind == "dash":
                p.has_dash = True
            else:
                p.has_djump = True
            title, sub = self.INFO[self.kind]
            game.show_banner("Получено: " + title, sub, 4.0)
            game.burst(self.rect.centerx, self.rect.centery, 40, C_TEAL, 320, 0.9, 4, 0)
            game.hitstop = 0.2
            game.shake(8, 0.3)

    def draw(self, s, cam, t):
        cx = self.rect.centerx - cam[0]
        cy = self.rect.centery - cam[1] + math.sin(t * 2.5) * 5
        r = 12 + math.sin(t * 5) * 2
        pygame.draw.circle(s, C_TEAL, (cx, cy), int(r))
        pygame.draw.circle(s, (210, 255, 245), (cx, cy), int(r * 0.5))
        for i in range(3):
            a = t * 2 + i * math.tau / 3
            pygame.draw.circle(s, (180, 240, 230), (cx + math.cos(a) * 22, cy + math.sin(a) * 22), 2)


class Shrine:
    def __init__(self, x, y):
        self.pos = (x, y)
        self.rect = pygame.Rect(0, 0, 70, 60)
        self.rect.midbottom = (x, y)
        self.lit = False

    def draw(self, s, cam, t, near):
        x, y = self.pos[0] - cam[0], self.pos[1] - cam[1]
        pygame.draw.rect(s, (48, 42, 40), (x - 18, y - 6, 36, 6))
        pygame.draw.line(s, (70, 60, 56), (x, y - 6), (x, y - 50), 4)
        pygame.draw.line(s, (70, 60, 56), (x, y - 50), (x + 14, y - 50), 3)
        lx, ly = x + 14, y - 40
        col = C_AMBER if self.lit else (120, 90, 60)
        pygame.draw.rect(s, (40, 34, 32), (lx - 9, ly - 8, 18, 22), border_radius=4)
        pygame.draw.rect(s, col, (lx - 6, ly - 5, 12, 16), border_radius=3)
        if self.lit:
            fl = 5 + math.sin(t * 18) * 2
            pygame.draw.polygon(s, C_AMBER_L, [(lx - 3, ly + 8), (lx + 3, ly + 8), (lx, ly + 8 - fl - 4)])


# --------------------------------------------------------------------------
# Игра
# --------------------------------------------------------------------------
class Game:
    def __init__(self, headless=False):
        pygame.init()
        pygame.display.set_caption("Тлеющий Корень")
        flags = 0 if headless else pygame.SCALED
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
        self.clock = pygame.time.Clock()
        self.f_big = pygame.font.Font(None, 84)
        self.f_mid = pygame.font.Font(None, 42)
        self.f_small = pygame.font.Font(None, 26)
        self.f_tiny = pygame.font.Font(None, 22)
        self.defs = build_world()
        self.rooms = {}
        self.dark = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.spores = [[random.uniform(0, SCREEN_W), random.uniform(0, SCREEN_H),
                        random.uniform(8, 25), random.uniform(0, 6), random.choice((1, 1, 2))]
                       for _ in range(60)]
        self.t = 0.0
        self.reset_run()
        self.state = "title"

    # ---------------- состояние ----------------
    def reset_run(self):
        self.collected = set()
        self.visited = set()
        self.shards = 0
        self.boss_defeated = False
        self.respawn_point = (0, (8 * T + T // 2, 15 * T))
        self.player = Player(4 * T, 15 * T)
        self.time = 0.0
        self.banner = None
        self.hitstop = 0.0
        self.slowmo = 0.0
        self.flash = 0.0
        self.fade = 0.0
        self.shake_amt = self.shake_t = 0.0
        self.win_t = 0.0
        self.dying_t = 0.0
        self.cam = [0.0, 0.0]
        self.load_room(0)
        self.player.place(4 * T, 15 * T)
        self.safe = (self.player.fx, self.player.fy)
        self.update_camera(0, snap=True)

    def get_room(self, idx):
        if idx not in self.rooms:
            self.rooms[idx] = Room(self.defs[idx], idx)
        room = self.rooms[idx]
        room.reset()
        return room

    def load_room(self, idx):
        self.room_idx = idx
        self.room = self.get_room(idx)
        d = self.defs[idx]
        self.enemies, self.pickups, self.shrines, self.hazards, self.particles = [], [], [], [], []
        self.boss = None
        self.boss_active = False
        for o in d.objects:
            k, x, y = o["kind"], o["tx"] * T + T // 2, (o["ty"] + 1) * T
            if k == "crawler":
                self.enemies.append(Crawler(x, y))
            elif k == "flyer":
                self.enemies.append(Flyer(x, y - T // 2))
            elif k == "shard" and o["id"] not in self.collected:
                self.pickups.append(Shard(x, y - T // 2, pid=o["id"]))
            elif k in ("dash", "djump") and o["id"] not in self.collected:
                self.pickups.append(Orb(k, x, y - T // 2, o["id"]))
            elif k == "shrine":
                sh = Shrine(x, y)
                sh.lit = self.respawn_point == (idx, (x, y))
                self.shrines.append(sh)
        if idx not in self.visited:
            self.visited.add(idx)
            self.show_banner(d.name, "", 2.6)

    def show_banner(self, title, sub, dur):
        self.banner = [title, sub, dur, dur]

    def shake(self, amt, dur):
        self.shake_amt = max(self.shake_amt, amt)
        self.shake_t = max(self.shake_t, dur)

    def burst(self, x, y, n, color, speed, life, size, grav):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(0.3, 1.0) * speed
            lf = life * random.uniform(0.6, 1.0)
            self.particles.append([x, y, math.cos(a) * v, math.sin(a) * v, lf, lf, color, size, grav])

    def enemy_died(self, e):
        self.burst(e.rect.centerx, e.rect.centery, 18, (170, 200, 190), 260, 0.6, 3, 300)
        for _ in range(e.drop):
            self.pickups.append(Shard(e.rect.centerx, e.rect.centery,
                                      random.uniform(-170, 170), random.uniform(-460, -220)))
        self.shake(5, 0.12)

    def on_boss_dead(self, boss):
        self.boss_defeated = True
        self.hitstop = 0.3
        self.slowmo = 1.4
        self.shake(20, 0.8)
        self.hazards.clear()
        self.room.reset()
        self.show_banner("ХРАНИТЕЛЬ ПОВЕРЖЕН", "", 3.0)
        self.win_t = 3.4

    def kill_player(self):
        self.state = "dying"
        self.dying_t = 1.8
        p = self.player
        self.burst(p.rect.centerx, p.rect.centery, 50, C_AMBER, 300, 1.2, 4, 80)
        self.shake(14, 0.5)

    def respawn(self):
        p = self.player
        p.hp = p.max_hp
        p.reset_motion()
        p.inv = 1.0
        idx, (x, y) = self.respawn_point
        self.load_room(idx)
        p.place(x, y)
        self.safe = (p.fx, p.fy)
        self.update_camera(0, snap=True)
        self.state = "play"
        self.fade = 0.8

    def rest(self, shrine):
        p = self.player
        p.hp = p.max_hp
        self.respawn_point = (self.room_idx, shrine.pos)
        px, py = p.rect.midbottom
        self.load_room(self.room_idx)
        p.place(px, py)
        self.show_banner("Фонарь зажжён", "Здоровье восстановлено · враги вернулись", 2.4)
        self.burst(shrine.pos[0] + 14, shrine.pos[1] - 40, 30, C_AMBER_L, 200, 0.8, 3, -80)
        self.flash = 0.1

    def spike_hit(self):
        p = self.player
        damaged = p.inv <= 0
        if damaged:
            p.hp -= 1
            self.shake(10, 0.25)
            self.hitstop = 0.12
        self.burst(p.rect.centerx, p.rect.centery, 20, C_SPIKE_L, 240, 0.5, 3, 300)
        if p.hp <= 0:
            self.kill_player()
            return
        p.fx, p.fy = self.safe
        p.rect.topleft = (round(p.fx), round(p.fy))
        p.scarf = [p.rect.center] * len(p.scarf)
        p.vx = p.vy = 0
        p.dash_t = p.knock_t = 0
        p.swing = None
        p.inv = max(p.inv, 1.0)
        self.fade = 0.35

    # ---------------- ввод ----------------
    def read_input(self):
        inp = Input()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                inp.quit = True
            elif e.type == pygame.KEYDOWN:
                k = e.key
                if k in JUMP_KEYS:
                    inp.jump_p = True
                if k in ATTACK_KEYS:
                    inp.attack_p = True
                if k in DASH_KEYS:
                    inp.dash_p = True
                if k in UP_KEYS:
                    inp.up_p = True
                if k in CONFIRM_KEYS:
                    inp.confirm = True
                if k == pygame.K_ESCAPE:
                    inp.pause_p = True
        keys = pygame.key.get_pressed()
        inp.left = any(keys[k] for k in LEFT_KEYS)
        inp.right = any(keys[k] for k in RIGHT_KEYS)
        inp.up = any(keys[k] for k in UP_KEYS)
        inp.down = any(keys[k] for k in DOWN_KEYS)
        inp.jump_h = any(keys[k] for k in JUMP_KEYS)
        inp.heal_h = any(keys[k] for k in HEAL_KEYS)
        return inp

    # ---------------- обновление ----------------
    def update(self, dt, inp):
        self.t += dt
        for sp in self.spores:
            sp[1] -= sp[2] * dt
            sp[0] += math.sin(self.t + sp[3]) * 8 * dt
            if sp[1] < -5:
                sp[1] = SCREEN_H + 5
                sp[0] = random.uniform(0, SCREEN_W)

        if self.state == "title":
            if inp.confirm or inp.jump_p:
                self.state = "play"
                self.fade = 0.6
            elif inp.pause_p:
                return False
            return True
        if self.state == "paused":
            if inp.pause_p or inp.confirm:
                self.state = "play"
            return True
        if self.state == "win":
            self.update_particles(dt)
            self.win_t += dt
            if self.win_t > 1.0 and (inp.confirm or inp.jump_p):
                self.reset_run()
                self.state = "title"
            return True
        if inp.pause_p and self.state == "play":
            self.state = "paused"
            return True

        self.flash = max(0, self.flash - dt)
        self.fade = max(0, self.fade - dt)
        if self.banner:
            self.banner[2] -= dt
            if self.banner[2] <= 0:
                self.banner = None
        if self.shake_t > 0:
            self.shake_t -= dt
            if self.shake_t <= 0:
                self.shake_amt = 0
        if self.hitstop > 0:
            self.hitstop -= dt
            return True

        sdt = dt
        if self.slowmo > 0:
            self.slowmo -= dt
            sdt = dt * 0.35

        if self.state == "dying":
            self.dying_t -= dt
            self.update_particles(dt)
            if self.dying_t <= 0:
                self.respawn()
            return True

        self.time += dt
        p = self.player
        p.update(sdt, inp, self)
        self.check_spikes()
        if self.state != "play":
            return True

        if p.on_ground:
            tyb = p.rect.bottom // T
            l, r = p.rect.left // T, (p.rect.right - 1) // T
            if (self.room.is_solid(l, tyb) and self.room.is_solid(r, tyb)
                    and not any(self.room.is_spike(x, tyb) or self.room.is_spike(x, tyb - 1)
                                for x in range(l - 1, r + 2))):
                self.safe = (p.fx, p.fy)

        if inp.up_p and p.on_ground:
            for sh in self.shrines:
                if sh.rect.colliderect(p.rect):
                    self.rest(sh)
                    break

        if p.swing:
            self.resolve_swing()

        for e in self.enemies:
            e.update(sdt, self)
            if e.alive and e.rect.inflate(-6, -6).colliderect(p.rect):
                p.hurt(self, e.rect.centerx)
        self.enemies = [e for e in self.enemies if e.alive]

        if self.boss:
            self.boss.update(sdt, self)
            if self.boss.state != "dead" and self.boss.rect.inflate(-14, -10).colliderect(p.rect):
                p.hurt(self, self.boss.rect.centerx)
            if not self.boss.alive:
                self.boss = None

        for h in self.hazards:
            h.update(sdt, self)
            if h.alive and h.active and h.rect.inflate(-4, -4).colliderect(p.rect):
                p.hurt(self, h.rect.centerx)
        self.hazards = [h for h in self.hazards if h.alive]

        for it in self.pickups:
            it.update(sdt, self)
        self.pickups = [it for it in self.pickups if it.alive]

        self.update_particles(sdt)
        self.check_exits()
        self.check_boss_trigger()

        if self.win_t > 0:
            self.win_t -= dt
            if self.win_t <= 0:
                self.state = "win"
                self.win_t = 0.0
                self.final_time = self.time

        self.update_camera(dt)
        return True

    def resolve_swing(self):
        p = self.player
        sw = p.swing
        hb = p.swing_rect()
        d = sw["dir"]
        dx, dy = {"up": (0, -1), "down": (0, 1)}.get(d, (sw["facing"], 0))
        targets = list(self.enemies)
        if self.boss and self.boss.state != "dead":
            targets.append(self.boss)
        for e in targets:
            if id(e) in sw["hit"] or not e.alive or not hb.colliderect(e.rect):
                continue
            sw["hit"].add(id(e))
            e.hurt(1, dx, dy, self)
            p.glow = min(99, p.glow + GLOW_PER_HIT)
            cx = (hb.centerx + e.rect.centerx) // 2
            cy = (hb.centery + e.rect.centery) // 2
            self.burst(cx, cy, 10, C_WHITE, 300, 0.25, 3, 0)
            self.hitstop = max(self.hitstop, 0.045)
            self.shake(3, 0.08)
            if d == "down":
                p.vy = -POGO_V
                p.pogo = True
                p.can_dash = p.can_djump = True
            elif d == "side":
                p.vx = -dx * 200
                p.knock_t = 0.08

    def check_spikes(self):
        r = self.player.rect
        for ty in range(r.top // T, (r.bottom - 1) // T + 1):
            for tx in range(r.left // T, (r.right - 1) // T + 1):
                if self.room.is_spike(tx, ty):
                    if r.colliderect(pygame.Rect(tx * T + 3, ty * T + 10, T - 6, T - 10)):
                        self.spike_hit()
                        return

    def check_exits(self):
        p = self.player
        d = self.defs[self.room_idx]
        if p.rect.centerx > d.w * T and d.right is not None:
            nd = self.defs[d.right]
            fy = p.fy + (nd.left_row - d.right_row) * T
            self.load_room(d.right)
            p.fx, p.fy = 4.0, fy
        elif p.rect.centerx < 0 and d.left is not None:
            nd = self.defs[d.left]
            fy = p.fy + (nd.right_row - d.left_row) * T
            self.load_room(d.left)
            p.fx, p.fy = float(nd.w * T - p.rect.w - 4), fy
        else:
            return
        p.rect.topleft = (round(p.fx), round(p.fy))
        p.scarf = [p.rect.center] * len(p.scarf)
        p.swing = None
        self.safe = (p.fx, p.fy)
        self.update_camera(0, snap=True)

    def check_boss_trigger(self):
        if self.room_idx != 3 or self.boss_defeated or self.boss_active:
            return
        p = self.player
        if p.rect.left > 9 * T and p.on_ground:
            self.boss_active = True
            for y in range(2, 5):
                self.room.grid[y][0] = "#"
            self.room.render()
            self.boss = Boss(26 * T, 2 * T + 86)
            self.show_banner("ХРАНИТЕЛЬ КОРНЯ", "Древний страж подземелья", 2.8)
            self.shake(6, 0.6)

    def update_particles(self, dt):
        for pt in self.particles:
            pt[0] += pt[2] * dt
            pt[1] += pt[3] * dt
            pt[3] += pt[8] * dt
            pt[2] *= 0.98
            pt[4] -= dt
        self.particles = [pt for pt in self.particles if pt[4] > 0]

    def update_camera(self, dt, snap=False):
        p = self.player
        tx = p.rect.centerx - SCREEN_W / 2 + p.facing * 50
        ty = p.rect.centery - SCREEN_H / 2 - 20
        maxx = max(0, self.room.w * T - SCREEN_W)
        maxy = max(0, self.room.h * T - SCREEN_H)
        tx, ty = clamp(tx, 0, maxx), clamp(ty, 0, maxy)
        if snap:
            self.cam = [tx, ty]
        else:
            k = 1 - math.exp(-7 * dt)
            self.cam[0] += (tx - self.cam[0]) * k
            self.cam[1] += (ty - self.cam[1]) * k

    # ---------------- отрисовка ----------------
    def draw(self):
        s = self.screen
        sx = sy = 0
        if self.shake_amt > 0:
            sx = random.uniform(-1, 1) * self.shake_amt
            sy = random.uniform(-1, 1) * self.shake_amt
        cam = (int(self.cam[0] + sx), int(self.cam[1] + sy))
        room = self.room
        s.blit(room.bg_far, (0, 0))
        s.blit(room.bg_mid, (-cam[0] * 0.5, -cam[1] * 0.5))
        for x, y, _, _, sz in self.spores:
            pygame.draw.circle(s, (90, 140, 130), (int(x), int(y)), sz)
        s.blit(room.surface, (-cam[0], -cam[1]))

        t = self.t
        p = self.player
        for sh in self.shrines:
            sh.draw(s, cam, t, sh.rect.colliderect(p.rect))
        for it in self.pickups:
            it.draw(s, cam, t)
        for e in self.enemies:
            e.draw(s, cam, t)
        if self.boss:
            self.boss.draw(s, cam, t)
        for h in self.hazards:
            h.draw(s, cam, t)
        if self.state not in ("dying",):
            p.draw(s, cam, t)
        for pt in self.particles:
            r = max(1, int(pt[7] * pt[4] / pt[5]))
            pygame.draw.circle(s, pt[6], (int(pt[0] - cam[0]), int(pt[1] - cam[1])), r)

        self.draw_lighting(cam)

        for wx, wy, text in self.defs[self.room_idx].signs:
            img = self.f_small.render(text, True, C_TEXT)
            s.blit(img, (wx - cam[0], wy - cam[1]))
        for sh in self.shrines:
            if sh.rect.colliderect(p.rect) and self.state == "play":
                img = self.f_small.render("Вверх — отдохнуть", True, C_AMBER_L)
                s.blit(img, (sh.pos[0] - cam[0] - img.get_width() // 2, sh.pos[1] - cam[1] - 90))

        if self.state != "title":
            self.draw_hud()
        if self.banner and self.state in ("play", "dying"):
            self.draw_banner()
        if self.flash > 0:
            ov = pygame.Surface((SCREEN_W, SCREEN_H))
            ov.fill((255, 240, 220))
            ov.set_alpha(int(160 * self.flash / 0.15))
            s.blit(ov, (0, 0))
        if self.fade > 0:
            ov = pygame.Surface((SCREEN_W, SCREEN_H))
            ov.set_alpha(int(255 * min(1, self.fade / 0.35)))
            s.blit(ov, (0, 0))
        if self.state == "dying":
            ov = pygame.Surface((SCREEN_W, SCREEN_H))
            ov.set_alpha(int(255 * clamp(1 - (self.dying_t - 0.3) / 1.5, 0, 1)))
            s.blit(ov, (0, 0))
        if self.state == "title":
            self.draw_title()
        elif self.state == "paused":
            self.draw_pause()
        elif self.state == "win":
            self.draw_win()

    def draw_lighting(self, cam):
        s = self.screen
        p = self.player
        self.dark.fill((4, 6, 10, self.defs[self.room_idx].dark))
        sub = pygame.BLEND_RGBA_SUB
        lights = []
        if self.state != "dying":
            lights.append((p.rect.centerx, p.rect.centery - 10, 240))
        for sh in self.shrines:
            lights.append((sh.pos[0] + 14, sh.pos[1] - 40, 200 if sh.lit else 140))
        for it in self.pickups:
            if isinstance(it, Orb):
                lights.append((it.rect.centerx, it.rect.centery, 150))
        if self.boss:
            lights.append((self.boss.rect.centerx, self.boss.rect.centery, 180))
        for h in self.hazards:
            if h.kind == "wave" and h.active:
                lights.append((h.rect.centerx, h.rect.centery, 90))
        for gx, gy, _ in self.room.glows:
            if -80 < gx - cam[0] < SCREEN_W + 80 and -80 < gy - cam[1] < SCREEN_H + 80:
                lights.append((gx, gy, 60))
        strength = self.defs[self.room_idx].dark
        for lx, ly, r in lights:
            img = make_light(r, strength)
            self.dark.blit(img, (lx - cam[0] - r, ly - cam[1] - r), special_flags=sub)
        s.blit(self.dark, (0, 0))
        add = pygame.BLEND_ADD
        if self.state != "dying":
            g = make_glow(80, C_AMBER, 0.35)
            s.blit(g, (p.rect.centerx - cam[0] - 80, p.rect.top + 7 - cam[1] - 80), special_flags=add)
        for gx, gy, col in self.room.glows:
            if -40 < gx - cam[0] < SCREEN_W + 40 and -40 < gy - cam[1] < SCREEN_H + 40:
                g = make_glow(26, col, 0.5)
                s.blit(g, (gx - cam[0] - 26, gy - cam[1] - 26), special_flags=add)
        for sh in self.shrines:
            g = make_glow(60, C_AMBER, 0.5 if sh.lit else 0.2)
            s.blit(g, (sh.pos[0] + 14 - cam[0] - 60, sh.pos[1] - 40 - cam[1] - 60), special_flags=add)

    def draw_hud(self):
        s = self.screen
        p = self.player
        x, y, r = 46, 46, 26
        pygame.draw.circle(s, (16, 20, 24), (x, y), r + 5)
        fill = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
        pygame.draw.circle(fill, C_AMBER, (r, r), r)
        h = int(2 * r * p.glow / 99)
        if h > 0:
            s.blit(fill, (x - r, y + r - h), area=pygame.Rect(0, 2 * r - h, 2 * r, h))
        ring = C_AMBER_L if p.glow >= GLOW_COST else (150, 145, 135)
        pygame.draw.circle(s, ring, (x, y), r + 5, 2)
        for i in range(p.max_hp):
            lx, ly = 98 + i * 30, 34
            pygame.draw.rect(s, (60, 52, 48), (lx - 3, ly - 15, 6, 4))
            if i < p.hp:
                pygame.draw.rect(s, C_AMBER, (lx - 8, ly - 11, 16, 22), border_radius=5)
                pygame.draw.rect(s, C_AMBER_L, (lx - 4, ly - 5, 8, 12), border_radius=3)
            else:
                pygame.draw.rect(s, (34, 34, 38), (lx - 8, ly - 11, 16, 22), border_radius=5)
                pygame.draw.rect(s, (90, 90, 96), (lx - 8, ly - 11, 16, 22), 2, border_radius=5)
        cx, cy = 98, 70
        pygame.draw.polygon(s, (150, 230, 220), [(cx, cy - 7), (cx + 5, cy), (cx, cy + 7), (cx - 5, cy)])
        s.blit(self.f_small.render(str(self.shards), True, C_WHITE), (cx + 12, cy - 9))
        icons = []
        if p.has_dash:
            icons.append("рывок")
        if p.has_djump:
            icons.append("двойной прыжок")
        if icons:
            img = self.f_tiny.render(" · ".join(icons), True, C_TEXT)
            s.blit(img, (SCREEN_W - img.get_width() - 16, 16))
        if self.boss and self.boss.state not in ("intro",):
            bw = 420
            bx, by = SCREEN_W // 2 - bw // 2, SCREEN_H - 40
            frac = max(0, self.boss.hp) / self.boss.max_hp
            pygame.draw.rect(s, (20, 14, 14), (bx - 3, by - 3, bw + 6, 16))
            pygame.draw.rect(s, (190, 60, 50), (bx, by, int(bw * frac), 10))
            name = self.f_small.render("Хранитель Корня", True, C_WHITE)
            s.blit(name, (SCREEN_W // 2 - name.get_width() // 2, by - 26))

    def draw_banner(self):
        title, sub, left, dur = self.banner
        a = clamp(min(left, dur - left) / 0.5, 0, 1)
        img = self.f_mid.render(title, True, C_WHITE)
        img.set_alpha(int(255 * a))
        self.screen.blit(img, (SCREEN_W // 2 - img.get_width() // 2, 110))
        w = img.get_width() // 2 + 30
        line = pygame.Surface((w * 2, 2))
        line.fill(C_AMBER)
        line.set_alpha(int(200 * a))
        self.screen.blit(line, (SCREEN_W // 2 - w, 150))
        if sub:
            im2 = self.f_small.render(sub, True, C_TEXT)
            im2.set_alpha(int(255 * a))
            self.screen.blit(im2, (SCREEN_W // 2 - im2.get_width() // 2, 162))

    def overlay(self, alpha):
        ov = pygame.Surface((SCREEN_W, SCREEN_H))
        ov.fill((6, 8, 12))
        ov.set_alpha(alpha)
        self.screen.blit(ov, (0, 0))

    def center(self, font, text, y, color):
        img = font.render(text, True, color)
        self.screen.blit(img, (SCREEN_W // 2 - img.get_width() // 2, y))

    def draw_title(self):
        self.overlay(150)
        glow = make_glow(180, C_AMBER, 0.35)
        self.screen.blit(glow, (SCREEN_W // 2 - 180, 150 - 180), special_flags=pygame.BLEND_ADD)
        self.center(self.f_big, "ТЛЕЮЩИЙ КОРЕНЬ", 110, C_AMBER_L)
        self.center(self.f_small, "маленькая подземная метроидвания", 175, C_TEXT)
        lines = ["Стрелки / A D  — движение", "Z / Пробел  — прыжок",
                 "X / J  — удар  (Вверх / Вниз — направление)", "C / K  — рывок (когда найдёте)",
                 "V / L держать  — лечение светом", "Вверх у фонаря — отдых   ·   Esc — пауза"]
        for i, ln in enumerate(lines):
            self.center(self.f_small, ln, 250 + i * 28, C_WHITE)
        if int(self.t * 2) % 2 == 0:
            self.center(self.f_mid, "Enter / Z — начать", 440, C_AMBER)

    def draw_pause(self):
        self.overlay(170)
        self.center(self.f_big, "ПАУЗА", 170, C_WHITE)
        self.center(self.f_small, "Esc / Enter — продолжить", 260, C_TEXT)

    def draw_win(self):
        self.overlay(int(clamp(self.win_t, 0, 1) * 200))
        self.center(self.f_big, "КОРЕНЬ УСПОКОЕН", 150, C_AMBER_L)
        tm = getattr(self, "final_time", self.time)
        self.center(self.f_mid, f"Время: {int(tm // 60):02d}:{int(tm % 60):02d}   ·   Осколки: {self.shards}",
                    250, C_WHITE)
        self.center(self.f_small, "Спасибо за игру!", 300, C_TEXT)
        if self.win_t > 1.0:
            self.center(self.f_small, "Enter — в начало", 380, C_AMBER)

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000, 1 / 30)
            inp = self.read_input()
            if inp.quit:
                break
            running = self.update(dt, inp)
            self.draw()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
    sys.exit()