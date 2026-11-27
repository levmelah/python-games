"""The control bar along the bottom: language, music choice and mute."""
import pygame

from lang import LANGUAGES


class BarButton:
    """A small clickable button that knows how to label itself."""

    def __init__(self, rect, label_fn, action, active_fn=None, font_size=20,
                 lang_code=None):
        self.rect = pygame.Rect(rect)
        self.label_fn = label_fn          # called to get the current text
        self.action = action
        self.active_fn = active_fn or (lambda: False)
        self.font_size = font_size
        self.lang_code = lang_code      # force a font, whatever the UI language
        self.hovered = False

    COLORS = {
        'idle': (30, 32, 58),
        'hover': (48, 52, 92),
        'active': (92, 72, 190),
        'border': (120, 130, 200),
        'text': (232, 234, 248),
    }

    def draw(self, screen, lang):
        active = self.active_fn()
        if active:
            fill = self.COLORS['active']
        elif self.hovered:
            fill = self.COLORS['hover']
        else:
            fill = self.COLORS['idle']
        pygame.draw.rect(screen, fill, self.rect, border_radius=8)
        pygame.draw.rect(screen, self.COLORS['border'], self.rect, 1,
                         border_radius=8)

        if self.lang_code:
            font = lang.font_for(self.lang_code, self.font_size)
            text = lang.shape_for(self.lang_code, self.label_fn())
        else:
            font = lang.font(self.font_size)
            text = lang.shape(self.label_fn())
        image = font.render(text, True, self.COLORS['text'])
        screen.blit(image, image.get_rect(center=self.rect.center))

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()
            return True
        return False


class ControlBar:
    """Lives at the bottom of the window, outside the playfield."""

    BG_COLOR = (14, 15, 30)
    TOP_LINE = (90, 80, 170)
    LABEL_COLOR = (150, 156, 190)
    HINT_COLOR = (108, 112, 145)

    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.lang = ai_game.lang
        self.sounds = ai_game.sounds

        height = self.settings.control_bar_height
        self.rect = pygame.Rect(0, self.settings.screen_height - height,
                                self.settings.screen_width, height)
        self.buttons = []
        self._build()

    # --------------------------------------------------------------- build ---
    def _build(self):
        """Lay the bar out in three groups: language, music, sound."""
        self.buttons = []
        row_y = self.rect.top + 30
        btn_h = 34

        # --- language: one button per language, the active one lit up ------
        x = 28
        for code in LANGUAGES:
            width = 96
            self.buttons.append(BarButton(
                (x, row_y, width, btn_h),
                label_fn=lambda c=code: self.lang.language_name(c),
                action=lambda c=code: self.ai_game.set_language(c),
                active_fn=lambda c=code: self.lang.code == c,
                lang_code=code,
            ))
            x += width + 8
        self.language_label_pos = (28, self.rect.top + 8)

        # --- music: previous / name / next --------------------------------
        group_x = self.rect.centerx - 150
        self.buttons.append(BarButton(
            (group_x, row_y, 38, btn_h), lambda: '<',
            action=self.ai_game.previous_track))
        self.track_box = pygame.Rect(group_x + 46, row_y, 206, btn_h)
        self.buttons.append(BarButton(
            (group_x + 46, row_y, 206, btn_h),
            label_fn=lambda: self.lang.t(self.sounds.track_key),
            action=self.ai_game.next_track))
        self.buttons.append(BarButton(
            (group_x + 260, row_y, 38, btn_h), lambda: '>',
            action=self.ai_game.next_track))
        self.music_label_pos = (group_x, self.rect.top + 8)

        # --- sound on / off ------------------------------------------------
        width = 176
        sound_x = self.rect.right - width - 28
        self.buttons.append(BarButton(
            (sound_x, row_y, width, btn_h),
            label_fn=lambda: self.lang.t(
                'sound_off' if self.sounds.muted else 'sound_on'),
            action=self.ai_game.toggle_mute,
            active_fn=lambda: not self.sounds.muted,
        ))

    def refresh(self):
        """Called after a language change; the labels are read live, so this
        only needs to re-measure the layout."""
        self._build()

    # -------------------------------------------------------------- events ---
    def handle_event(self, event):
        """Returns True when the bar consumed the event."""
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.hovered = button.rect.collidepoint(event.pos)
            return self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                return False
            for button in self.buttons:
                if button.handle_click(event.pos):
                    break
            return True
        return False

    # ---------------------------------------------------------------- draw ---
    def draw(self):
        pygame.draw.rect(self.screen, self.BG_COLOR, self.rect)
        pygame.draw.line(self.screen, self.TOP_LINE, self.rect.topleft,
                         (self.rect.right, self.rect.top), 2)

        small = self.lang.font(16)
        for pos, key in ((self.language_label_pos, 'language'),
                         (self.music_label_pos, 'music')):
            image = small.render(self.lang.ts(key), True, self.LABEL_COLOR)
            self.screen.blit(image, pos)

        for button in self.buttons:
            button.draw(self.screen, self.lang)

        hint = small.render(self.lang.ts('hint'), True, self.HINT_COLOR)
        self.screen.blit(hint, hint.get_rect(
            midbottom=(self.rect.centerx, self.rect.bottom - 5)))
