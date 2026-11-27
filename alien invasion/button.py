import pygame


class Button:
    """The Play button, drawn in the middle of the playfield."""

    def __init__(self, ai_game, text_key='play'):
        self.screen = ai_game.screen
        self.lang = ai_game.lang
        self.text_key = text_key

        self.width, self.height = 220, 62
        self.button_color = (92, 72, 190)
        self.border_color = (170, 160, 240)
        self.text_color = (255, 255, 255)

        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = ai_game.camera.view_rect.center

    def draw_button(self):
        pygame.draw.rect(self.screen, self.button_color, self.rect,
                         border_radius=12)
        pygame.draw.rect(self.screen, self.border_color, self.rect, 2,
                         border_radius=12)
        font = self.lang.font(34)
        image = font.render(self.lang.ts(self.text_key), True, self.text_color)
        self.screen.blit(image, image.get_rect(center=self.rect.center))
