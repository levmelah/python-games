"""Player preferences (language, music choice, mute) kept between sessions."""
import json
import os

PREFS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'alien_invasion_prefs.json')

DEFAULTS = {
    'language': 'en',
    'music_track': 0,
    'muted': False,
}


def load():
    """Read the saved preferences, falling back to the defaults."""
    prefs = dict(DEFAULTS)
    try:
        with open(PREFS_FILE, encoding='utf-8') as f:
            saved = json.load(f)
    except (FileNotFoundError, ValueError, OSError):
        return prefs
    if isinstance(saved, dict):
        for key in DEFAULTS:
            if key in saved:
                prefs[key] = saved[key]
    return prefs


def save(prefs):
    """Write the preferences; a read-only folder must not crash the game."""
    try:
        with open(PREFS_FILE, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, ensure_ascii=False)
    except OSError:
        pass
