import pygame


class Scoreboard:
    """Reports the score, the high score, the level and the lives left."""

    TEXT_COLOR = (235, 235, 248)

    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        self.lang = ai_game.lang
        self.view = ai_game.camera.view_rect

        self.prep_all()

    def prep_all(self):
        """Re-render every label, e.g. after the language changes."""
        self.font = self.lang.font(26)
        self.prep_score()
        self.prep_high_score()
        self.prep_level()
        self.prep_ships()

    def _render(self, text):
        return self.font.render(self.lang.shape(text), True, self.TEXT_COLOR)

    def prep_score(self):
        rounded = round(self.stats.score, -1)
        self.score_image = self._render(f"{self.lang.t('score')} {rounded:,}")
        self.score_rect = self.score_image.get_rect()
        self.score_rect.right = self.view.right - 20
        self.score_rect.top = self.view.top + 14

    def prep_high_score(self):
        high = round(self.stats.high_score, -1)
        self.high_score_image = self._render(f"{self.lang.t('high')} {high:,}")
        self.high_score_rect = self.high_score_image.get_rect()
        self.high_score_rect.centerx = self.view.centerx
        self.high_score_rect.top = self.view.top + 14

    def prep_level(self):
        self.level_image = self._render(
            f"{self.lang.t('level')} {self.stats.level}")
        self.level_rect = self.level_image.get_rect()
        self.level_rect.right = self.view.right - 20
        self.level_rect.top = self.score_rect.bottom + 8

    def prep_ships(self):
        """One small ship icon per life left."""
        icon = self.ai_game.ship.icon(28)
        self.life_icons = []
        x = self.view.left + 20
        for _ in range(max(0, self.stats.ships_left)):
            rect = icon.get_rect(topleft=(x, self.view.top + 14))
            self.life_icons.append(rect)
            x += rect.width + 8
        self.life_icon = icon

    def show_score(self):
        self.screen.blit(self.score_image, self.score_rect)
        self.screen.blit(self.high_score_image, self.high_score_rect)
        self.screen.blit(self.level_image, self.level_rect)
        for rect in self.life_icons:
            self.screen.blit(self.life_icon, rect)

    def check_high_score(self):
        if self.stats.score > self.stats.high_score:
            self.stats.high_score = self.stats.score
            self.prep_high_score()
