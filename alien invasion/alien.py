import math

import pygame
from pygame.sprite import Sprite

import models3d
from camera3d import FLOOR_Y

# One mesh is shared by every alien; only the transform differs
_MESH = None


def alien_mesh():
    global _MESH
    if _MESH is None:
        _MESH = models3d.make_alien()
    return _MESH


class Alien(Sprite):
    """A saucer that lives in world space and is drawn as a spinning mesh."""

    SIZE = 11.0          # world units across

    def __init__(self, ai_game, x=0.0, z=0.0):
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.camera = ai_game.camera
        self.mesh = alien_mesh()

        self.x = float(x)
        self.y = ai_game.settings.alien_y
        self.z = float(z)

        # Each saucer spins from its own starting angle, so the fleet is not
        # one rigid block
        self.spin_offset = (abs(hash((round(x, 2), round(z, 2)))) % 628) / 100.0

        self.rect = pygame.Rect(0, 0, 1, 1)
        self.visible = False
        self.update_projection()

    @property
    def half_width(self):
        return self.SIZE / 2

    def update(self):
        """Slide sideways with the fleet."""
        self.x += self.settings.alien_speed * self.settings.fleet_direction
        self.update_projection()

    def update_projection(self):
        """Work out where the saucer lands on screen and how big it is."""
        projected = self.camera.project(self.x, self.y, self.z)
        if projected is None:
            self.visible = False
            return
        sx, sy, scale = projected
        size = max(6, int(self.SIZE * scale))
        self.rect = pygame.Rect(0, 0, size, size)
        self.rect.center = (int(sx), int(sy))
        self.visible = self.rect.colliderect(self.camera.view_rect)

    def check_edges(self):
        """True when the alien has reached the edge of the play area."""
        limit = self.settings.play_half_width
        return self.x + self.half_width >= limit or self.x - self.half_width <= -limit

    def draw(self):
        if not self.visible:
            return
        self._draw_shadow()
        yaw = self.spin_offset + pygame.time.get_ticks() / 1400.0
        bob = math.sin(self.spin_offset + pygame.time.get_ticks() / 520.0) * 0.6
        models3d.draw(self.screen, self.camera, self.mesh,
                      (self.x, self.y + bob, self.z),
                      scale=self.SIZE / 2, yaw=yaw, pitch=0.16)

    def _draw_shadow(self):
        """A squashed ellipse on the floor; cheap, and it sells the depth."""
        spot = self.camera.project(self.x, FLOOR_Y, self.z)
        if spot is None:
            return
        sx, sy, scale = spot
        w = max(4, int(self.SIZE * scale))
        h = max(2, int(w * 0.28))
        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
        self.screen.blit(shadow, (int(sx - w / 2), int(sy - h / 2)))

    def blitme(self):
        self.draw()
