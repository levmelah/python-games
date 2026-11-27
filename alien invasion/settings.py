class Settings:
    def __init__(self):
        self.screen_width = 1200
        self.screen_height = 800
        self.bg_color = (70,130,180)
        self.ship_speed = 1.5
        self.bullet_speed = 5.0
        self.bullet_width = 1000
        self.bullet_height = 15
        self.bullet_color = (139, 69, 19)  # brown1
        self.bullet_allowed = 3  # Maximum number of bullets on screen at once
        self.alien_speed = 10.0
        self.fleet_drop_speed = 10
        self.fleet_direction = 1
        self.ship_limit = 3