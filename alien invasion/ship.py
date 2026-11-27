import pygame
from pygame.sprite import Sprite

import models3d
from camera3d import FLOOR_Y


class Ship(Sprite):
    """The player's ship: a mesh parked at a fixed depth, banking as it moves."""

    SIZE = 16.0          # world units across

    def __init__(self, ai_game):
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.camera = getattr(ai_game, 'camera', None)
        self.mesh = models3d.make_ship()

        self.x = 0.0                       # world x
        self.y = 0.0
        self.z = self.settings.ship_z
        self.moving_right = False
        self.moving_left = False
        self.roll = 0.0                    # banking, eased towards a target

        self.rect = pygame.Rect(0, 0, 1, 1)
        if self.camera:
            self._project()

    def _project(self):
        projected = self.camera.project(self.x, self.y, self.z)
        if projected is None:
            return
        sx, sy, scale = projected
        size = max(16, int(self.SIZE * scale))
        self.rect = pygame.Rect(0, 0, size, int(size * 0.6))
        self.rect.center = (int(sx), int(sy))

    def update(self):
        limit = self.settings.play_half_width - self.SIZE / 2
        target_roll = 0.0
        if self.moving_right and self.x < limit:
            self.x += self.settings.ship_speed
            target_roll = -0.42
        if self.moving_left and self.x > -limit:
            self.x -= self.settings.ship_speed
            target_roll = 0.42
        # Ease into the bank so the turn reads as a movement, not a snap
        self.roll += (target_roll - self.roll) * 0.18
        self._project()

    def blitme(self):
        self._draw_shadow()
        models3d.draw(self.screen, self.camera, self.mesh,
                      (self.x, self.y, self.z), scale=self.SIZE / 2.6,
                      yaw=0.0, pitch=-0.12, roll=self.roll)

    def _draw_shadow(self):
        spot = self.camera.project(self.x, FLOOR_Y, self.z)
        if spot is None:
            return
        sx, sy, scale = spot
        w = max(8, int(self.SIZE * scale))
        h = max(3, int(w * 0.3))
        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        self.screen.blit(shadow, (int(sx - w / 2), int(sy - h / 2)))

    def center_ship(self):
        self.x = 0.0
        self.roll = 0.0
        self._project()

    def icon(self, height):
        """A small rendered copy of the ship, for the lives row."""
        return models3d.render_icon(self.mesh, int(height * 1.6), height,
                                    yaw=3.14159, pitch=0.6, scale=0.78)
