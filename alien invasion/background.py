"""The 3D backdrop: deep-space gradient, a star volume and a grid floor."""
import random

import pygame

from camera3d import FLOOR_Y, NEAR_Z


class Background:
    def __init__(self, ai_game):
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.camera = ai_game.camera
        self.view = self.camera.view_rect

        self.sky = self._make_sky()
        self.stars = self._make_stars(170)
        self.grid_offset = 0.0
        self.last_ticks = pygame.time.get_ticks()

    # ---------------------------------------------------------------- sky ---
    TOP_COLOR = (4, 5, 20)
    HORIZON_COLOR = (38, 26, 74)

    def _make_sky(self):
        """A one-pixel-wide gradient, stretched; built once, blitted per frame."""
        height = self.view.height
        strip = pygame.Surface((1, height))
        horizon = max(1, int(self.camera.horizon_y - self.view.top))
        for y in range(height):
            if y <= horizon:
                ratio = y / horizon
                a, b = self.TOP_COLOR, self.HORIZON_COLOR
            else:
                # Below the horizon it darkens again, into the floor
                ratio = 1 - (y - horizon) / max(1, height - horizon)
                a, b = (6, 6, 16), self.HORIZON_COLOR
            strip.set_at((0, y), tuple(
                int(c1 + (c2 - c1) * ratio) for c1, c2 in zip(a, b)))
        return pygame.transform.scale(strip, (self.view.width, height))

    # -------------------------------------------------------------- stars ---
    def _make_stars(self, count):
        stars = []
        for _ in range(count):
            stars.append([
                random.uniform(-260, 260),                 # x
                random.uniform(-10, 150),                  # y
                random.uniform(NEAR_Z + 10, 620),          # z
            ])
        return stars

    def _respawn_star(self, star):
        star[0] = random.uniform(-260, 260)
        star[1] = random.uniform(-10, 150)
        star[2] = 620.0

    # ------------------------------------------------------------- update ---
    STAR_SPEED = 26.0        # world units per second, towards the camera
    GRID_SPEED = 30.0

    def update(self):
        now = pygame.time.get_ticks()
        dt = min((now - self.last_ticks) / 1000.0, 0.1)
        self.last_ticks = now

        for star in self.stars:
            star[2] -= self.STAR_SPEED * dt
            if star[2] <= NEAR_Z + 4:
                self._respawn_star(star)

        self.grid_offset = (self.grid_offset + self.GRID_SPEED * dt) % self.GRID_STEP

    # --------------------------------------------------------------- draw ---
    GRID_STEP = 40.0         # spacing of the floor lines, in world units
    GRID_FAR = 560.0
    GRID_HALF_WIDTH = 240.0
    GRID_COLOR = (58, 48, 120)

    def draw(self):
        self.screen.blit(self.sky, self.view.topleft)
        self._draw_horizon_glow()
        self._draw_floor()
        self._draw_stars()

    def _draw_stars(self):
        for x, y, z in self.stars:
            projected = self.camera.project(x, y, z)
            if projected is None:
                continue
            sx, sy, scale = projected
            if not self.view.collidepoint(sx, sy):
                continue
            # Near stars are bigger and brighter; far ones fade into the sky
            depth = min(1.0, max(0.0, 1.0 - z / self.GRID_FAR))
            brightness = int(70 + 170 * depth)
            size = 1 if depth < 0.45 else (2 if depth < 0.8 else 3)
            self.screen.fill((brightness, brightness, min(255, brightness + 25)),
                             (int(sx), int(sy), size, size))

    def _draw_horizon_glow(self):
        """A soft band of light where the floor meets the sky."""
        glow_height = 70
        glow = pygame.Surface((self.view.width, glow_height), pygame.SRCALPHA)
        for i in range(glow_height):
            alpha = int(62 * (1 - i / glow_height) ** 2)
            pygame.draw.line(glow, (120, 90, 220, alpha), (0, i),
                             (self.view.width, i))
        top = int(self.camera.horizon_y) - glow_height // 2
        self.screen.blit(glow, (self.view.left, top))

    def _draw_floor(self):
        """Lines running away to the horizon, plus rungs sliding towards us."""
        clip = self.screen.get_clip()
        self.screen.set_clip(self.view)

        # Lines parallel to z: they converge at the vanishing point
        x = -self.GRID_HALF_WIDTH
        while x <= self.GRID_HALF_WIDTH:
            near = self.camera.project(x, FLOOR_Y, NEAR_Z + 8)
            far = self.camera.project(x, FLOOR_Y, self.GRID_FAR)
            if near and far:
                pygame.draw.line(self.screen, self.GRID_COLOR,
                                 (near[0], near[1]), (far[0], far[1]))
            x += self.GRID_STEP

        # Rungs across the floor, scrolling to fake forward motion
        z = NEAR_Z + 8 + self.grid_offset
        while z <= self.GRID_FAR:
            left = self.camera.project(-self.GRID_HALF_WIDTH, FLOOR_Y, z)
            right = self.camera.project(self.GRID_HALF_WIDTH, FLOOR_Y, z)
            if left and right:
                fade = max(0.12, 1 - z / self.GRID_FAR)
                color = tuple(int(c * fade) for c in (110, 95, 210))
                pygame.draw.line(self.screen, color,
                                 (left[0], left[1]), (right[0], right[1]))
            z += self.GRID_STEP

        self.screen.set_clip(clip)
