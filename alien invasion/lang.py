"""Game text in English and Hebrew, with right-to-left shaping for Hebrew."""
import os

import pygame

try:
    from bidi.algorithm import get_display
except ImportError:                      # pragma: no cover - fallback if bidi is absent
    def get_display(text):
        """Very rough fallback: reverse the string so Hebrew is at least readable."""
        return text[::-1]

# The Hebrew interface also shows Latin key names (P, M, Q) and separators, so
# the font has to cover all three. DejaVu does; most Hebrew-only faces do not.
HEBREW_FONTS = (
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/culmus/FrankRuehlCLM-Bold.ttf',
    '/usr/share/fonts/truetype/culmus/MiriamCLM-Bold.ttf',
)

LANGUAGES = ('en', 'he')

LANGUAGE_NAMES = {'en': 'English', 'he': 'עברית'}

TEXT = {
    'en': {
        'title': 'Alien Invasion',
        'play': 'Play',
        'score': 'Score',
        'high': 'High',
        'level': 'Level',
        'game_over': 'Game Over',
        'press_play': 'Click Play or press P',
        'language': 'Language',
        'music': 'Music',
        'sound_on': 'Sound: on',
        'sound_off': 'Sound: off',
        'track_space': 'Space',
        'track_arcade': 'Arcade',
        'track_pulse': 'Pulse',
        'track_none': 'Silence',
        'hint': 'Arrows / A D move · Space fires · P plays · L language · M mute · N next track · Q quits',
    },
    'he': {
        'title': 'פלישת החייזרים',
        'play': 'שחק',
        'score': 'ניקוד',
        'high': 'שיא',
        'level': 'שלב',
        'game_over': 'המשחק נגמר',
        'press_play': 'לחץ שחק או P',
        'language': 'שפה',
        'music': 'מוזיקה',
        'sound_on': 'צליל: דולק',
        'sound_off': 'צליל: כבוי',
        'track_space': 'חלל',
        'track_arcade': 'ארקייד',
        'track_pulse': 'פעימה',
        'track_none': 'שקט',
        'hint': 'חצים / A D לזוז · רווח לירות · P להתחיל · L שפה · M השתקה · N מוזיקה · Q יציאה',
    },
}


class Lang:
    """Holds the chosen language and hands out shaped text and fonts."""

    def __init__(self, code='en'):
        self.code = code if code in LANGUAGES else 'en'
        self._fonts = {}
        self._hebrew_font_path = next(
            (p for p in HEBREW_FONTS if os.path.exists(p)), None)

    @property
    def is_rtl(self):
        return self.code == 'he'

    def set_language(self, code):
        if code in LANGUAGES:
            self.code = code

    def next_language(self):
        """Switch to the next language and return its code."""
        self.code = LANGUAGES[(LANGUAGES.index(self.code) + 1) % len(LANGUAGES)]
        return self.code

    def language_name(self, code=None):
        return LANGUAGE_NAMES[code or self.code]

    def t(self, key):
        """Look up a string in the current language, unshaped.

        Shaping happens once, when the finished line is drawn - otherwise text
        built by joining pieces (\"Score 450\") would be reordered twice.
        """
        return TEXT[self.code].get(key) or TEXT['en'].get(key, key)

    def ts(self, key):
        """Look up a string and shape it, ready to pass to render()."""
        return self.shape(self.t(key))

    def shape(self, text):
        """Reorder Hebrew so pygame draws it right to left."""
        return self.shape_for(self.code, text)

    @staticmethod
    def shape_for(code, text):
        """Shape text for one specific language, whatever the UI is set to."""
        if code == 'he':
            return get_display(text)
        return text

    def font(self, size, bold=True):
        """A font that can draw the current language, cached per size."""
        return self.font_for(self.code, size, bold)

    def font_for(self, code, size, bold=True):
        """A font for one specific language - the language buttons need to
        show 'עברית' even while the rest of the interface is in English."""
        key = (code, size, bold)
        if key not in self._fonts:
            if code == 'he' and self._hebrew_font_path:
                font = pygame.font.Font(self._hebrew_font_path, size)
            else:
                font = pygame.font.SysFont(None, int(size * 1.25), bold=bold)
            self._fonts[key] = font
        return self._fonts[key]
