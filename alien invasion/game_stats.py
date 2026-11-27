import json
import os

# Keep the high score next to the game, not in whatever folder it was started from
HIGH_SCORE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'alien_invasion_highscore.json')


class GameStats:
    def __init__(self, ai_game):
        self.settings = ai_game.settings
        self.reset_stats()

        self.game_active = False

        # The high score is kept on disk, so it survives closing the game
        self.high_score = self._load_high_score()

    def reset_stats(self):
        self.ships_left = self.settings.ship_limit
        self.score = 0
        self.level = 1
        self.coins = 0

    def _load_high_score(self):
        """Read the saved high score, or start from 0 the first time."""
        try:
            with open(HIGH_SCORE_FILE, encoding='utf-8') as f:
                saved = json.load(f)
            return int(saved.get('high_score', 0))
        except (FileNotFoundError, ValueError, TypeError, AttributeError, OSError):
            return 0

    def save_high_score(self):
        """Write the high score to disk; called when the game closes."""
        try:
            with open(HIGH_SCORE_FILE, 'w', encoding='utf-8') as f:
                json.dump({'high_score': int(self.high_score)}, f)
        except OSError:
            pass
