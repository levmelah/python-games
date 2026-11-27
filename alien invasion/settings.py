class Settings:
    """Stores all the settings for Alien Invasion.

    Speeds are per frame at the capped frame rate (see FPS), and distances are
    in world units, not pixels - the camera turns them into pixels.
    """

    def __init__(self):
        # Screen settings
        self.screen_width = 1200
        self.screen_height = 800
        self.bg_color = (6, 7, 22)
        self.control_bar_height = 96     # the bar along the bottom
        self.fps = 60

        # World layout. The ship sits far enough from the camera that its full
        # sideways travel still fits on screen: at ship_z the view is about
        # (screen_width / 2) / (focal / ship_z) world units wide either way, so
        # play_half_width must stay under that, and the fleet must stay inside
        # play_half_width too, or the player could not line up with an alien.
        self.play_half_width = 88.0      # limit for the ship and for the fleet
        self.ship_z = 90.0               # the depth the ship sits at
        self.alien_y = 0.0               # ship, aliens and shots share one altitude
        self.bullet_y = 0.0
        self.alien_rows = 5              # rows of aliens, stacked in depth
        self.alien_columns = 7
        self.row_spacing = 48.0          # world units between rows
        self.first_row_z = 160.0
        self.column_spacing = 22.0

        # Ship settings
        self.ship_limit = 3              # three lives

        # Bullet settings
        self.bullet_color = (255, 170, 60)
        self.bullet_allowed = 3

        # How far the fleet jumps towards the player when it hits an edge
        self.fleet_advance = 5.0

        # How quickly the game speeds up
        self.speedup_scale = 1.1
        # How quickly the alien point values increase
        self.score_scale = 1.5

        self.initialize_dynamic_settings()

    def initialize_dynamic_settings(self):
        """Initialize the settings that change during the game."""
        self.ship_speed = 1.7
        self.bullet_speed = 6.5
        self.alien_speed = 0.36

        # fleet_direction of 1 means right; -1 means left
        self.fleet_direction = 1

        # Scoring
        self.alien_points = 50

    def increase_speed(self):
        """Increase speed settings and alien point values."""
        self.ship_speed *= self.speedup_scale
        self.bullet_speed *= self.speedup_scale
        self.alien_speed *= self.speedup_scale

        self.alien_points = int(self.alien_points * self.score_scale)
