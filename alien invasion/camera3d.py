"""The little bit of 3D maths the game needs.

The world is right-handed and simple:
  x  grows to the right
  y  grows upwards (the floor is below the ship, at negative y)
  z  grows away from the player, into the screen

The camera sits a short way behind and above the ship and looks straight down
the +z axis, so one perspective divide is all a point needs.
"""

NEAR_Z = 6.0          # anything closer than this is behind the camera


class Camera:
    def __init__(self, view_rect, focal=560.0, height=48.0):
        self.view_rect = view_rect       # the playfield, above the control bar
        self.focal = focal
        self.height = height             # camera y
        self.horizon_ratio = 0.30        # where the horizon sits in the view

    @property
    def center_x(self):
        return self.view_rect.centerx

    @property
    def horizon_y(self):
        return self.view_rect.top + self.view_rect.height * self.horizon_ratio

    def scale_at(self, z):
        """Pixels per world unit at depth z."""
        return self.focal / max(z, NEAR_Z)

    def project(self, x, y, z):
        """World point -> (screen_x, screen_y, scale). None when behind the camera."""
        if z <= NEAR_Z:
            return None
        scale = self.focal / z
        return (self.center_x + x * scale,
                self.horizon_y - (y - self.height) * scale,
                scale)

    def project_floor(self, x, z):
        """Shortcut for a point on the floor plane."""
        return self.project(x, FLOOR_Y, z)


FLOOR_Y = -8.0       # the grid floor, used by the background and the shadows
