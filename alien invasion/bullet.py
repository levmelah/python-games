import pygame
from pygame.sprite import Sprite


class Bullet(Sprite):
    """A shot that travels away from the player, into the screen."""

    SIZE = 1.1          # world units

    def __init__(self, ai_game):
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.camera = ai_game.camera
        self.color = self.settings.bullet_color

        self.x = ai_game.ship.x
        self.y = ai_game.settings.bullet_y
        self.z = ai_game.settings.ship_z + 4.0

        self.rect = pygame.Rect(0, 0, 4, 10)
        self.visible = False
        self._project()

    def _project(self):
        projected = self.camera.project(self.x, self.y, self.z)
        if projected is None:
            self.visible = False
            return
        sx, sy, scale = projected
        # A short streak rather than a dot, so fast shots stay readable
        w = max(2, int(self.SIZE * scale))
        h = max(4, int(self.SIZE * 2.6 * scale))
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (int(sx), int(sy))
        self.visible = self.rect.colliderect(self.camera.view_rect)

    def update(self):
        self.z += self.settings.bullet_speed
        self._project()

    def draw_bullet(self):
        if not self.visible:
            return
        # Bright core with a dimmer halo, so it glows against the starfield
        halo = self.rect.inflate(4, 6)
        pygame.draw.rect(self.screen, (90, 40, 10), halo, border_radius=3)
        pygame.draw.rect(self.screen, self.color, self.rect, border_radius=2)
