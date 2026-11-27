"""A very small polygon renderer, so the ship and the aliens are real meshes.

Each model is a list of vertices plus a list of faces. Drawing a model means:
transform the vertices (spin, scale, move), throw away the faces pointing away
from us, shade the rest by the angle they make with the light, sort them back
to front and fill them. No textures, no z-buffer - just enough for solid shapes
that turn and catch the light.
"""
import math

import pygame

# Where the light comes from (normalised), and how much light is everywhere
LIGHT = (-0.35, 0.78, -0.52)
AMBIENT = 0.34


class Mesh:
    """Vertices in model space plus flat-shaded faces."""

    def __init__(self, vertices, faces):
        self.vertices = vertices
        # face = (indices, colour, emissive) - emissive faces ignore the light
        self.faces = faces


# --------------------------------------------------------------- building ---
def _ring(radius, y, sides, start=0.0):
    """A horizontal ring of points; the building block for saucers and pods."""
    return [(radius * math.cos(start + 2 * math.pi * i / sides),
             y,
             radius * math.sin(start + 2 * math.pi * i / sides))
            for i in range(sides)]


def make_alien():
    """A hexagonal saucer with a glowing dome and two engine pods."""
    sides = 6
    verts = []
    rim = _ring(1.0, 0.0, sides)
    verts.extend(rim)                                   # 0..5
    verts.append((0.0, 0.42, 0.0))                      # 6 hull top
    verts.append((0.0, -0.40, 0.0))                     # 7 hull bottom
    dome = _ring(0.42, 0.40, sides, start=math.pi / 6)
    verts.extend(dome)                                  # 8..13
    verts.append((0.0, 0.78, 0.0))                      # 14 dome apex

    hull = (118, 196, 96)
    hull_dark = (74, 140, 64)
    glass = (150, 255, 220)

    faces = []
    for i in range(sides):
        j = (i + 1) % sides
        faces.append(((i, j, 6), hull, False))          # upper skirt
        faces.append(((j, i, 7), hull_dark, False))     # lower skirt
    for i in range(sides):
        j = (i + 1) % sides
        faces.append(((8 + i, 8 + j, 14), glass, True))  # the lit dome

    # Two pods hanging off the sides, so the silhouette is not a plain disc
    for side in (-1, 1):
        base = len(verts)
        cx = side * 0.95
        verts.extend([
            (cx - 0.22, -0.1, -0.3), (cx + 0.22, -0.1, -0.3),
            (cx + 0.22, -0.1, 0.3), (cx - 0.22, -0.1, 0.3),
            (cx, 0.22, 0.0), (cx, -0.42, 0.0),
        ])
        b = base
        for a, c in ((0, 1), (1, 2), (2, 3), (3, 0)):
            faces.append(((b + a, b + c, b + 4), hull, False))
            faces.append(((b + c, b + a, b + 5), hull_dark, False))

    return Mesh(verts, faces)


def _hull8(corners, faces_out, verts_out, colors):
    """Add a solid with eight corners (a box, or any swept/tapered version).

    Corners are given back face first, then front face, each counter-clockwise
    seen from outside, which keeps every normal pointing away from the solid.
    """
    base = len(verts_out)
    verts_out.extend(corners)
    b = base
    sides = (
        ((4, 5, 6, 7), colors['front']),
        ((1, 0, 3, 2), colors['back']),
        ((7, 6, 2, 3), colors['top']),
        ((0, 1, 5, 4), colors['bottom']),
        ((1, 2, 6, 5), colors['right']),
        ((4, 7, 3, 0), colors['left']),
    )
    for indices, (color, emissive) in sides:
        faces_out.append((tuple(b + i for i in indices), color, emissive))


def _box_corners(center, half):
    cx, cy, cz = center
    hx, hy, hz = half
    return [
        (cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz),
    ]


def _plain(color, emissive=False):
    """The same colour on all six sides of a solid."""
    return {side: (color, emissive) for side in
            ('front', 'back', 'top', 'bottom', 'left', 'right')}


def make_ship():
    """A chunky interceptor: fuselage, nose cone, swept wings, engines, fin.

    It is built from solid blocks rather than single triangles, so it still
    reads as a three-dimensional object when seen from behind and above - which
    is the only angle the player ever gets.
    """
    body = (92, 176, 240)
    body_dark = (44, 96, 158)
    body_top = (120, 198, 250)
    wing = (66, 140, 206)
    wing_top = (98, 170, 230)
    glass = (255, 222, 120)
    flame = (255, 146, 54)
    metal = (120, 128, 150)

    verts, faces = [], []

    # --- fuselage ---------------------------------------------------------
    hull = _plain(body)
    hull['top'] = (body_top, False)
    hull['bottom'] = (body_dark, False)
    hull['back'] = (body_dark, False)
    fuselage = _box_corners((0.0, 0.0, -0.1), (0.32, 0.26, 1.1))
    _hull8(fuselage, faces, verts, hull)

    # --- nose cone: a pyramid off the front face --------------------------
    nose_base = len(verts)
    front = fuselage[4:]
    verts.extend(front)
    verts.append((0.0, 0.02, 1.95))
    apex = nose_base + 4
    for i in range(4):
        faces.append(((nose_base + i, nose_base + (i + 1) % 4, apex),
                      body if i % 2 else body_top, False))

    # --- canopy -----------------------------------------------------------
    canopy = {side: (glass, False) for side in
              ('front', 'back', 'bottom', 'left', 'right')}
    canopy['top'] = (glass, True)
    _hull8([
        (-0.2, 0.2, 0.0), (0.2, 0.2, 0.0), (0.16, 0.44, -0.05), (-0.16, 0.44, -0.05),
        (-0.17, 0.2, 0.75), (0.17, 0.2, 0.75), (0.1, 0.38, 0.6), (-0.1, 0.38, 0.6),
    ], faces, verts, canopy)

    # --- swept wings: thin, tapered slabs ---------------------------------
    for side in (-1, 1):
        inner = side * 0.3
        outer = side * 1.65
        wing_colors = _plain(wing)
        wing_colors['top'] = (wing_top, False)
        wing_colors['bottom'] = (body_dark, False)
        corners = [
            (inner, -0.12, -1.0), (outer, -0.06, -1.05),
            (outer, 0.02, -1.05), (inner, 0.04, -1.0),
            (inner, -0.12, 0.35), (outer, -0.06, -0.45),
            (outer, 0.02, -0.45), (inner, 0.04, 0.35),
        ]
        if side < 0:                      # mirroring flips the winding back
            corners = [corners[i] for i in (1, 0, 3, 2, 5, 4, 7, 6)]
        _hull8(corners, faces, verts, wing_colors)

        # wing-tip pod
        _hull8(_box_corners((outer, -0.02, -0.75), (0.08, 0.08, 0.34)),
               faces, verts, _plain(metal))

    # --- engines, with glowing exhausts -----------------------------------
    for side in (-1, 1):
        engine = _plain(metal)
        engine['back'] = (flame, True)
        engine['top'] = ((150, 158, 178), False)
        _hull8(_box_corners((side * 0.42, -0.06, -0.95), (0.17, 0.17, 0.55)),
               faces, verts, engine)

    # --- tail fin ---------------------------------------------------------
    fin = _plain(body)
    fin['top'] = (body_top, False)
    _hull8([
        (-0.05, 0.2, -1.2), (0.05, 0.2, -1.2), (0.05, 0.78, -1.15), (-0.05, 0.78, -1.15),
        (-0.05, 0.2, -0.35), (0.05, 0.2, -0.35), (0.04, 0.6, -0.72), (-0.04, 0.6, -0.72),
    ], faces, verts, fin)

    return Mesh(verts, faces)


# -------------------------------------------------------------- rendering ---
def _transform(mesh, scale, yaw, pitch, roll, position):
    """Model space -> world space, for every vertex at once."""
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    px, py, pz = position
    out = []
    for vx, vy, vz in mesh.vertices:
        x, y, z = vx * scale, vy * scale, vz * scale
        # roll (about z), then pitch (about x), then yaw (about y)
        x, y = x * cr - y * sr, x * sr + y * cr
        y, z = y * cp - z * sp, y * sp + z * cp
        x, z = x * cy + z * sy, -x * sy + z * cy
        out.append((x + px, y + py, z + pz))
    return out


def _normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length == 0:
        return None
    return nx / length, ny / length, nz / length


def _shade(color, normal):
    lit = AMBIENT + (1 - AMBIENT) * max(0.0, (normal[0] * LIGHT[0]
                                              + normal[1] * LIGHT[1]
                                              + normal[2] * LIGHT[2]))
    return (min(255, int(color[0] * lit)),
            min(255, int(color[1] * lit)),
            min(255, int(color[2] * lit)))


def draw(surface, camera, mesh, position, scale=1.0,
         yaw=0.0, pitch=0.0, roll=0.0, eye=None):
    """Draw one model through the game camera. Returns its screen rect."""
    world = _transform(mesh, scale, yaw, pitch, roll, position)
    if eye is None:
        eye = (0.0, camera.height, 0.0)

    drawable = []
    for indices, color, emissive in mesh.faces:
        points = [world[i] for i in indices]
        normal = _normal(points[0], points[1], points[2])
        if normal is None:
            continue
        # Backface culling: is the face turned towards the camera?
        first = points[0]
        view = (eye[0] - first[0], eye[1] - first[1], eye[2] - first[2])
        if (normal[0] * view[0] + normal[1] * view[1] + normal[2] * view[2]) <= 0:
            continue

        projected = [camera.project(*p) for p in points]
        if any(p is None for p in projected):
            continue
        depth = sum(p[2] for p in points) / len(points)
        shade = color if emissive else _shade(color, normal)
        drawable.append((depth, [(p[0], p[1]) for p in projected], shade))

    if not drawable:
        return None

    # Painter's algorithm: the farthest face is filled first
    drawable.sort(key=lambda item: -item[0])
    min_x = min_y = 10 ** 9
    max_x = max_y = -10 ** 9
    for _, points, color in drawable:
        pygame.draw.polygon(surface, color, points)
        for x, y in points:
            min_x = min(min_x, x); max_x = max(max_x, x)
            min_y = min(min_y, y); max_y = max(max_y, y)
    return pygame.Rect(int(min_x), int(min_y),
                       max(1, int(max_x - min_x)), max(1, int(max_y - min_y)))


class IconCamera:
    """A stand-in camera for drawing a model into a small standalone surface."""

    def __init__(self, width, height, focal=None, distance=4.0):
        self.view_rect = pygame.Rect(0, 0, width, height)
        self.focal = focal if focal else width * 0.9
        self.height = 0.0
        self.distance = distance

    @property
    def center_x(self):
        return self.view_rect.width / 2

    @property
    def horizon_y(self):
        return self.view_rect.height / 2

    def scale_at(self, z):
        return self.focal / max(z, 0.1)

    def project(self, x, y, z):
        z = z + self.distance
        if z <= 0.1:
            return None
        scale = self.focal / z
        return (self.center_x + x * scale, self.horizon_y - y * scale, scale)


def render_icon(mesh, width, height, yaw=0.5, pitch=0.5, scale=1.0, distance=4.0):
    """Render a model once into a transparent surface (used for the lives row)."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    camera = IconCamera(width, height, distance=distance)
    draw(surface, camera, mesh, (0.0, 0.0, 0.0), scale=scale,
         yaw=yaw, pitch=pitch, eye=(0.0, 0.0, -distance))
    return surface
