import pygame
import random
import math
import sys
import pygame.gfxdraw as gfxdraw

# 1. אתחול והגדרות בסיסיות
pygame.init()
WIDTH, HEIGHT = 2000, 1200  # מפה גדולה בהרבה עם כל המתקנים החדשים

# חלון המשחק בפועל - מתאים את עצמו לגודל המסך ושומר על יחס הגובה-רוחב של המפה
_info = pygame.display.Info()
_max_w, _max_h = _info.current_w - 80, _info.current_h - 120
_scale = min(1.0, _max_w / WIDTH, _max_h / HEIGHT)
WINDOW_WIDTH, WINDOW_HEIGHT = int(WIDTH * _scale), int(HEIGHT * _scale)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
world = pygame.Surface((WIDTH, HEIGHT))  # כל הציור מתבצע כאן, ואז מוקטן למסך
pygame.display.set_caption("Cursor Camp Ultimate Edition")
clock = pygame.time.Clock()

def to_world(pos):
    return (pos[0] / _scale, pos[1] / _scale)

# צבעים
SAND = (242, 212, 126)
SAND_DEEP = (222, 184, 108)
GRASS = (140, 190, 85)
GRASS_DARK = (120, 172, 70)
LIGHT_GRASS = (168, 210, 110)
WATER = (127, 218, 227)
DEEP_WATER = (24, 90, 150)
HOUSE_ROOF = (235, 77, 61)
HOUSE_ROOF_DARK = (195, 55, 45)
HOUSE_BODY = (245, 245, 240)
NET_COLOR = (240, 240, 240)
WOOD = (194, 133, 85)
WOOD_DARK = (150, 100, 60)
CAVE_COLOR = (44, 62, 80)
CAVE_INSIDE = (18, 24, 32)

# צבעים לפנים המבנים
ROOM_FLOOR = (210, 170, 120)
ROOM_WALL = (250, 235, 210)
CAVE_ROCK = (60, 55, 65)
CAVE_FLOOR = (30, 27, 32)
CRYSTAL_COLOR = (120, 200, 255)

# צבעים להרחבת המפה
TREE_DARK = (32, 95, 55)
TREE_MID = (46, 120, 65)
TREE_LIGHT = (72, 150, 80)
TRACK_ASPHALT = (65, 65, 74)
RIVER_WATER = (100, 200, 215)
SLIDE_COLOR = (240, 100, 60)

font = pygame.font.SysFont(None, 40)

def draw_hebrew(surface, text, pos, color=(255, 255, 255)):
    # פונט לא תומך בכיוון ימין-לשמאל אוטומטית, לכן הופכים את הטקסט ידנית
    img = font.render(text[::-1], True, color)
    surface.blit(img, pos)

def cursor_shape(x, y):
    # צורת חץ עכבר קלאסית (בהשראת neal.fun/cursor-camp)
    return [
        (x, y),
        (x, y + 22),
        (x + 5, y + 17),
        (x + 8, y + 24),
        (x + 12, y + 22),
        (x + 9, y + 15),
        (x + 15, y + 15),
    ]

# --- כלי ציור לגרפיקה חלקה: אנטי-אליאסינג, גרדיאנטים וצללים רכים ---

def aa_circle(surface, color, center, radius, width=0):
    cx, cy, r = int(center[0]), int(center[1]), max(int(radius), 1)
    if width <= 0:
        gfxdraw.filled_circle(surface, cx, cy, r, color)
        gfxdraw.aacircle(surface, cx, cy, r, color)
    else:
        for i in range(width):
            gfxdraw.aacircle(surface, cx, cy, max(r - i, 1), color)

def aa_ellipse(surface, color, center, rx, ry):
    cx, cy, rx, ry = int(center[0]), int(center[1]), max(int(rx), 1), max(int(ry), 1)
    gfxdraw.filled_ellipse(surface, cx, cy, rx, ry, color)
    gfxdraw.aaellipse(surface, cx, cy, rx, ry, color)

def aa_polygon(surface, color, points):
    pts = [(int(px), int(py)) for px, py in points]
    gfxdraw.filled_polygon(surface, pts, color)
    gfxdraw.aapolygon(surface, pts, color)

def vertical_gradient(size, top_color, bottom_color):
    w, h = size
    h = max(int(h), 1)
    band = pygame.Surface((1, h))
    for i in range(h):
        t = i / max(h - 1, 1)
        band.set_at((0, i), (
            int(top_color[0] + (bottom_color[0] - top_color[0]) * t),
            int(top_color[1] + (bottom_color[1] - top_color[1]) * t),
            int(top_color[2] + (bottom_color[2] - top_color[2]) * t),
        ))
    return pygame.transform.scale(band, (int(w), h))

_shadow_cache = {}

def draw_shadow(surface, center, rx, ry, alpha=90):
    key = (max(int(rx), 1), max(int(ry), 1), alpha)
    img = _shadow_cache.get(key)
    if img is None:
        img = pygame.Surface((key[0] * 2, key[1] * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(img, (10, 15, 10, alpha), (0, 0, key[0] * 2, key[1] * 2))
        _shadow_cache[key] = img
    surface.blit(img, (center[0] - key[0], center[1] - key[1]))

def soft_glow(surface, center, radius, color, max_alpha=140):
    radius = max(int(radius), 4)
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -4):
        alpha = int(max_alpha * (1 - r / radius))
        pygame.draw.circle(glow, (*color, alpha), (radius, radius), r)
    surface.blit(glow, (int(center[0] - radius), int(center[1] - radius)), special_flags=pygame.BLEND_RGBA_ADD)

# תמונות רקע מוכנות מראש (נוצרות פעם אחת בלבד, כדי לא לחשב גרדיאנט בכל פריים)
SEA_IMG = vertical_gradient((WIDTH, 130), (18, 70, 120), (140, 220, 230))
SAND_IMG = vertical_gradient((WIDTH, 180), (250, 226, 165), SAND_DEEP)
ROOM_WALL_IMG = vertical_gradient((WIDTH, HEIGHT - 220), (255, 245, 225), (232, 212, 182))
ROOM_FLOOR_IMG = vertical_gradient((WIDTH, 220), (225, 178, 122), (190, 148, 98))
TREEHOUSE_WALL_IMG = vertical_gradient((WIDTH, HEIGHT - 260), (240, 228, 200), (208, 193, 163))
TREEHOUSE_FLOOR_IMG = vertical_gradient((WIDTH, 260), (210, 160, 105), (168, 118, 72))
CAVE_ROCK_IMG = vertical_gradient((WIDTH, HEIGHT - 200), (78, 71, 84), (44, 40, 50))
CAVE_FLOOR_IMG = vertical_gradient((WIDTH, 200), (40, 36, 44), (20, 18, 24))

# מים שטוחים כמו במבט מלמעלה (לא כדור מבריק) - צבע כמעט אחיד עם רמז עדין של עומק
_POOL_SIZE = 210
_pool_r = _POOL_SIZE // 2
POOL_WATER_IMG = pygame.Surface((_POOL_SIZE, _POOL_SIZE), pygame.SRCALPHA)
pygame.draw.circle(POOL_WATER_IMG, (78, 185, 210), (_pool_r, _pool_r), _pool_r)
pygame.draw.circle(POOL_WATER_IMG, (235, 250, 255), (_pool_r, _pool_r), _pool_r, 4)   # קו אריחים לבן בשפה
pygame.draw.circle(POOL_WATER_IMG, (60, 155, 190), (_pool_r, _pool_r), _pool_r - 6, 12)  # טבעת עומק כהה יותר
pygame.draw.circle(POOL_WATER_IMG, (110, 210, 225), (_pool_r, _pool_r), int(_pool_r * 0.45))  # רמז אור עדין במרכז

# מרקם עשב עדין (נקודות אקראיות שנקבעות פעם אחת בלבד)
grass_speckles = [
    (random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(2, 4),
     random.choice([LIGHT_GRASS, GRASS_DARK]))
    for _ in range(500)
]

# 2. מחלקת בוטים (מדמה שחקנים אחרים במחנה)
class OnlineCursor:
    def __init__(self):
        self.x = random.randint(100, WIDTH - 100)
        self.y = random.randint(100, HEIGHT - 100)
        self.target_x = self.x
        self.target_y = self.y
        self.speed = random.uniform(2, 4.5)
        self.base_color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        self.color = self.base_color

    def update(self):
        if random.random() < 0.02 or (abs(self.x - self.target_x) < 10 and abs(self.y - self.target_y) < 10):
            self.target_x = random.randint(50, WIDTH - 50)
            self.target_y = random.randint(50, HEIGHT - 50)

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        # אפקט סביבתי: האם השחקן בתוך הים העמוק?
        if self.y < 90:
            self.color = (52, 152, 219) # צבע שחייה כחול
        # האם השחקן בתוך המערה?
        elif self.x > 1000 and self.y > 500:
            self.color = (35, 45, 55) # צבע הסוואה חשוך
        else:
            self.color = self.base_color

    def draw(self, surface):
        draw_shadow(surface, (self.x + 6, self.y + 20), 9, 4, alpha=65)
        points = cursor_shape(self.x, self.y)
        ipts = [(int(px), int(py)) for px, py in points]
        gfxdraw.filled_polygon(surface, ipts, self.color)
        gfxdraw.aapolygon(surface, ipts, self.color)
        gfxdraw.aapolygon(surface, ipts, (25, 25, 25))

# יצירת הבוטים
other_players = [OnlineCursor() for _ in range(15)]

# 3. מחלקת עטלפים למערה (מופיעים רק כשהפנס מאיר עליהם)
class Bat:
    def __init__(self):
        self.x = random.randint(60, WIDTH - 60)
        self.y = random.randint(80, HEIGHT - 260)
        self.angle = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(1.5, 3)

    def update(self):
        self.angle += random.uniform(-0.35, 0.35)
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        if self.x < 40 or self.x > WIDTH - 40:
            self.angle = math.pi - self.angle
        if self.y < 60 or self.y > HEIGHT - 220:
            self.angle = -self.angle
        self.x = max(30, min(self.x, WIDTH - 30))
        self.y = max(50, min(self.y, HEIGHT - 210))

    def draw(self, surface, frame):
        flap = 9 * math.sin(frame * 0.5 + self.x)
        aa_polygon(surface, (10, 10, 15), [
            (self.x - 16, self.y - flap), (self.x, self.y + 5),
            (self.x + 16, self.y - flap), (self.x, self.y - 3)
        ])

cave_bats = [Bat() for _ in range(4)]

# 4. הרחבת המפה: נהר, סירות, מסלול מירוצים, יער ומגלשה
RIVER_BASE_Y = 830

def river_y(x):
    return RIVER_BASE_Y + 70 * math.sin(x * 0.0025)

# עצי היער (מיקום קבוע שנוצר פעם אחת בהתחלה) - יער צפוף לאורך כל רצועת התחתית
forest_trees = [
    (random.randint(20, WIDTH - 40), random.randint(950, HEIGHT - 30), random.randint(14, 30))
    for _ in range(140)
]
forest_trees.sort(key=lambda t: t[1])  # עצים רחוקים (למעלה) מצוירים לפני קרובים, לתחושת עומק

class Boat:
    def __init__(self, start_x):
        self.x = start_x
        self.speed = random.uniform(0.35, 0.7)
        self.hull_color = random.choice([(150, 100, 60), (170, 60, 60), (60, 110, 150)])

    def update(self):
        self.x += self.speed
        if self.x > WIDTH + 40:
            self.x = -40

    def draw(self, surface):
        y = river_y(self.x)
        draw_shadow(surface, (self.x, y + 16), 26, 8, alpha=70)
        aa_polygon(surface, self.hull_color, [
            (self.x - 28, y), (self.x + 28, y), (self.x + 18, y + 14), (self.x - 18, y + 14)
        ])
        pygame.draw.line(surface, WOOD_DARK, (self.x, y - 2), (self.x, y - 30), 4)
        aa_polygon(surface, (255, 255, 255), [(self.x, y - 30), (self.x, y - 4), (self.x + 20, y - 8)])

river_boats = [Boat(x) for x in (150, 700, 1350, 1850)]

class RaceCar:
    def __init__(self, angle, color):
        self.angle = angle
        self.color = color
        self.speed = random.uniform(0.018, 0.03)

    def update(self):
        self.angle += self.speed

    def pos(self):
        cx, cy = TRACK_CENTER
        rx, ry = TRACK_MID_R
        return (cx + rx * math.cos(self.angle), cy + ry * math.sin(self.angle))

    def draw(self, surface):
        x, y = self.pos()
        draw_shadow(surface, (x, y + 9), 14, 5, alpha=70)
        pygame.draw.rect(surface, self.color, (x - 12, y - 7, 24, 14), border_radius=5)
        pygame.draw.rect(surface, (20, 20, 20), (x - 12, y - 7, 24, 14), 2, border_radius=5)
        pygame.draw.circle(surface, (25, 25, 25), (int(x - 7), int(y + 7)), 4)
        pygame.draw.circle(surface, (25, 25, 25), (int(x + 7), int(y + 7)), 4)

TRACK_CENTER = (1610, 320)
TRACK_OUTER_R = (330, 190)
TRACK_INNER_R = (255, 115)
TRACK_MID_R = (292, 152)
race_cars = [RaceCar(i * (2 * math.pi / 3), col) for i, col in enumerate(
    [(220, 40, 40), (40, 120, 220), (240, 200, 30)]
)]

treehouse_rect = pygame.Rect(90, 830, 160, 200)
slide_top = (900, 780)
slide_bottom = (975, 890)
slide_rider_t = 0.0

# מיקומי כדורים ופיזיקה
v_ball_x, v_ball_y = 260, 190
v_ball_sx, v_ball_sy = 0, 0

f_ball_x, f_ball_y = 250, 500
f_ball_sx, f_ball_sy = 0, 0

# משתני סרט קולנוע (אנימציה קלה למסך)
movie_frame = 0

# מיקום השחקן: "outside" / "house" / "cave" / "treehouse"
location = "outside"

# אזורי לחיצה לכניסה לבית, למערה ולבית העץ
house_rect = pygame.Rect(480, 150, 140, 170)
cave_center = (1050, 620)
cave_radius = 70

running = True
pygame.mouse.set_visible(False)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            location = "outside"
        elif event.type == pygame.MOUSEBUTTONDOWN:
            wx, wy = to_world(event.pos)
            if location == "outside":
                if house_rect.collidepoint(wx, wy):
                    location = "house"
                elif treehouse_rect.collidepoint(wx, wy):
                    location = "treehouse"
                elif math.hypot(wx - cave_center[0], wy - cave_center[1]) < cave_radius:
                    location = "cave"
            else:
                # לחיצה בתוך הבית/מערה/בית העץ מוציאה חזרה החוצה
                location = "outside"

    mouse_x, mouse_y = to_world(pygame.mouse.get_pos())

    if location == "outside":
        # עדכון בוטים
        for player in other_players:
            player.update()

        # עדכון סירות בנהר, מכוניות מירוץ ורוכב המגלשה
        for boat in river_boats:
            boat.update()
        for car in race_cars:
            car.update()
        slide_rider_t += 0.02
        if slide_rider_t > 1:
            slide_rider_t = 0.0

        # --- פיזיקה: כדורעף ---
        dist_to_v_ball = math.hypot(mouse_x - v_ball_x, mouse_y - v_ball_y)
        if dist_to_v_ball < 22:
            v_ball_sx = (v_ball_x - mouse_x) * 0.6
            v_ball_sy = (v_ball_y - mouse_y) * 0.6
        v_ball_x += v_ball_sx
        v_ball_y += v_ball_sy
        v_ball_sx *= 0.93
        v_ball_sy *= 0.93
        v_ball_x = max(160, min(v_ball_x, 380))
        v_ball_y = max(110, min(v_ball_y, 270))

        # --- פיזיקה: כדורגל ---
        dist_to_f_ball = math.hypot(mouse_x - f_ball_x, mouse_y - f_ball_y)
        if dist_to_f_ball < 25:
            f_ball_sx = (f_ball_x - mouse_x) * 0.7
            f_ball_sy = (f_ball_y - mouse_y) * 0.7

        # תנועת כדורי הבוטים (גם הם יכולים לגעת בכדורגל!)
        for p in other_players:
            if math.hypot(p.x - f_ball_x, p.y - f_ball_y) < 20:
                f_ball_sx = (f_ball_x - p.x) * 0.4
                f_ball_sy = (f_ball_y - p.y) * 0.4

        f_ball_x += f_ball_sx
        f_ball_y += f_ball_sy
        f_ball_sx *= 0.95
        f_ball_sy *= 0.95

        # גבולות מגרש כדורגל
        f_ball_x = max(60, min(f_ball_x, 440))
        f_ball_y = max(390, min(f_ball_y, 610))

        # --- ציור הרקע ---
        world.fill(GRASS)
        for gx, gy, gr, gcol in grass_speckles:
            pygame.draw.circle(world, gcol, (gx, gy), gr)

        # 1. 🌊 ים עמוק וחוף ים (חלק עליון) - גרדיאנט + נצנוץ גלים
        world.blit(SEA_IMG, (0, 0))
        world.blit(SAND_IMG, (0, 130))
        wave_shift = int(movie_frame / 2) % 20
        for i in range(0, WIDTH, 60):
            aa_circle(world, (255, 255, 255), (i + wave_shift, 92), 5)
            aa_circle(world, WATER, (i + wave_shift + 22, 97), 8)

        # 1.5 🏎️ מסלול מירוצים (פינה ימנית של המפה המורחבת)
        aa_ellipse(world, TRACK_ASPHALT, TRACK_CENTER, TRACK_OUTER_R[0], TRACK_OUTER_R[1])
        aa_ellipse(world, GRASS, TRACK_CENTER, TRACK_INNER_R[0], TRACK_INNER_R[1])
        for ang_deg in range(0, 360, 12):
            ang = math.radians(ang_deg)
            mx = TRACK_CENTER[0] + TRACK_MID_R[0] * math.cos(ang)
            my = TRACK_CENTER[1] + TRACK_MID_R[1] * math.sin(ang)
            pygame.draw.circle(world, (245, 245, 245), (int(mx), int(my)), 3)
        start_x, start_y = TRACK_CENTER[0], TRACK_CENTER[1] - TRACK_MID_R[1]
        for i in range(4):
            col = (255, 255, 255) if i % 2 == 0 else (30, 30, 30)
            pygame.draw.rect(world, col, (start_x - 20 + i * 10, start_y - 6, 10, 12))

        # 2. ⚽ מגרש כדורגל (פינה שמאלית תחתונה) עם פסי כיסוח
        draw_shadow(world, (250, 622), 200, 14, alpha=40)
        pygame.draw.rect(world, (39, 174, 96), (50, 380, 400, 240))
        for i, sx in enumerate(range(50, 450, 40)):
            if i % 2 == 0:
                pygame.draw.rect(world, (34, 160, 88), (sx, 380, 40, 240))
        pygame.draw.rect(world, NET_COLOR, (50, 380, 400, 240), 3)
        aa_circle(world, NET_COLOR, (250, 500), 40, width=3)
        pygame.draw.line(world, NET_COLOR, (250, 380), (250, 620), 3)
        pygame.draw.rect(world, (255, 255, 255), (20, 460, 30, 80), 3)
        pygame.draw.rect(world, (255, 255, 255), (450, 460, 30, 80), 3)

        # 3. 🏐 מגרש כדורעף (על החול)
        pygame.draw.rect(world, (235, 195, 100), (150, 100, 240, 180))
        for i, sx in enumerate(range(150, 390, 30)):
            if i % 2 == 0:
                pygame.draw.rect(world, (225, 185, 92), (sx, 100, 30, 180))
        pygame.draw.rect(world, (255, 255, 255), (150, 100, 240, 180), 2)
        pygame.draw.line(world, NET_COLOR, (270, 100), (270, 280), 3)
        for ny in range(106, 280, 16):
            pygame.draw.line(world, (255, 255, 255), (252, ny), (288, ny), 1)

        # 4. 🏠 הבית
        draw_shadow(world, (550, 322), 90, 18, alpha=70)
        pygame.draw.rect(world, (150, 110, 90), (585, 165, 18, 40))  # ארובה
        smoke_t = pygame.time.get_ticks() * 0.002
        for i in range(3):
            sx = 594 + 6 * math.sin(smoke_t + i)
            sy = 158 - i * 20
            soft_glow(world, (sx, sy), 10 + i * 3, (255, 255, 255), max_alpha=55)
        aa_polygon(world, HOUSE_ROOF_DARK, [(480, 224), (550, 154), (620, 224)])
        aa_polygon(world, HOUSE_ROOF, [(480, 220), (550, 150), (620, 220)])
        pygame.draw.rect(world, HOUSE_BODY, (490, 220, 120, 90))
        pygame.draw.rect(world, (218, 218, 210), (490, 285, 120, 25))
        pygame.draw.rect(world, (150, 210, 240), (500, 230, 26, 26))
        pygame.draw.rect(world, HOUSE_ROOF, (494, 230, 6, 26))
        pygame.draw.rect(world, HOUSE_ROOF, (528, 230, 6, 26))
        pygame.draw.rect(world, (100, 50, 20), (535, 260, 30, 50), border_radius=10)
        aa_circle(world, (230, 190, 90), (556, 285), 2)
        pygame.draw.rect(world, WOOD_DARK, (496, 258, 34, 10))
        for fx, fcol in [(502, (230, 80, 90)), (510, (250, 210, 60)), (518, (230, 80, 90)), (525, (250, 210, 60))]:
            aa_circle(world, fcol, (fx, 256), 4)

        # 5. 🏊 בריכת שחייה (פינה ימנית עליונה)
        draw_shadow(world, (950, 204), 110, 30, alpha=70)
        aa_circle(world, WOOD_DARK, (950, 200), 105)
        aa_circle(world, WOOD, (950, 200), 100)
        world.blit(POOL_WATER_IMG, (950 - _POOL_SIZE // 2, 200 - _POOL_SIZE // 2))
        # אדוות מים עדינות (קווים מתעקלים, לא נקודות מרחפות)
        ripple_t = pygame.time.get_ticks() * 0.0015
        for k in range(4):
            rx = 950 + 55 * math.cos(k * 1.6 + ripple_t * 0.3)
            ry = 200 + 32 * math.sin(k * 1.6 + ripple_t * 0.3)
            rw = 16 + 4 * math.sin(ripple_t + k)
            pygame.draw.arc(world, (225, 248, 255), (rx - rw, ry - 4, rw * 2, 8), 0.3, 2.8, 2)
        # סולם כניסה קבוע בשפת הבריכה
        pygame.draw.rect(world, (220, 220, 220), (1038, 172, 6, 56))
        pygame.draw.rect(world, (220, 220, 220), (1050, 172, 6, 56))
        for ry in (182, 196, 210):
            pygame.draw.line(world, (220, 220, 220), (1038, ry), (1056, ry), 3)

        # 6. 🎬 קולנוע פתוח / מסך סרט (מרכז ימין)
        draw_shadow(world, (710, 522), 130, 20, alpha=55)
        pygame.draw.rect(world, (44, 62, 80), (600, 380, 220, 140), border_radius=10)
        movie_frame += 1
        screen_b = int(180 + 50 * math.sin(movie_frame * 0.1))
        soft_glow(world, (710, 450), 90, (60, 140, min(screen_b, 255)), max_alpha=45)
        pygame.draw.rect(world, (20, 100, screen_b), (610, 390, 200, 120), border_radius=6)
        pygame.draw.rect(world, (127, 140, 141), (700, 520, 20, 40))
        for cx, cy, ccol in [(640, 570, (231, 76, 60)), (710, 580, (241, 196, 15)), (770, 560, (155, 89, 182))]:
            draw_shadow(world, (cx, cy + 10), 14, 5, alpha=60)
            aa_circle(world, ccol, (cx, cy), 12)
            aa_circle(world, (0, 0, 0), (cx, cy), 12, width=1)

        # 7. 🕳️ המערה המסתורית - גוש סלעים טבעי עם פתח חשוך (פינה ימנית תחתונה)
        cvx, cvy = cave_center
        draw_shadow(world, (cvx, cvy + 100), 150, 32, alpha=55)
        rock_tones = [(64, 71, 82), (54, 61, 73), (74, 81, 92)]
        rock_blobs = [
            (-95, 45, 82), (-45, -70, 78), (50, -78, 74), (105, 15, 88),
            (60, 90, 68), (-70, 90, 62), (10, 5, 96),
        ]
        for i, (dx, dy, r) in enumerate(rock_blobs):
            aa_circle(world, rock_tones[i % len(rock_tones)], (cvx + dx, cvy + dy), r)
        # קווי סדק/מרקם עדינים על הסלע
        for dx, dy, ang, ln in [(-70, 20, 0.6, 40), (60, -40, -0.4, 35), (30, 70, 1.1, 30)]:
            ex = cvx + dx + ln * math.cos(ang)
            ey = cvy + dy + ln * math.sin(ang)
            pygame.draw.line(world, (40, 46, 56), (cvx + dx, cvy + dy), (ex, ey), 3)
        # פתח המערה החשוך עם מסגרת כהה טבעית
        aa_circle(world, (24, 22, 27), (cvx, cvy), cave_radius + 10)
        aa_circle(world, (11, 12, 17), (cvx, cvy), cave_radius)
        aa_circle(world, CAVE_INSIDE, (cvx, cvy), cave_radius - 10)
        # אבנים קטנות ודשא בבסיס הסלע
        for sx, sy, sr in [(cvx - 150, cvy + 78, 13), (cvx + 155, cvy + 55, 15),
                           (cvx + 35, cvy + 128, 11), (cvx - 120, cvy - 88, 10)]:
            aa_circle(world, (90, 92, 96), (sx, sy), sr)

        # 7.5 🔥 מדורה (בין הבריכה, הקולנוע והמערה)
        soft_glow(world, (900, 435), 90, (255, 150, 40), max_alpha=100)
        draw_shadow(world, (900, 462), 46, 14, alpha=60)
        aa_circle(world, (110, 80, 55), (900, 440), 42)
        pygame.draw.rect(world, WOOD, (873, 436, 54, 9))
        pygame.draw.rect(world, WOOD, (896, 415, 9, 50), border_radius=2)
        flame_h = 22 + 6 * math.sin(movie_frame * 0.3)
        aa_polygon(world, (255, 140, 0), [(886, 436), (900, 436 - flame_h), (914, 436)])
        aa_polygon(world, (255, 210, 60), [(892, 434), (900, 436 - flame_h * 0.55), (908, 434)])
        for ang in range(0, 360, 45):
            sx = 900 + 38 * math.cos(math.radians(ang))
            sy = 440 + 38 * math.sin(math.radians(ang))
            aa_circle(world, (140, 130, 120), (sx, sy), 7)

        # 7.6 🏞️ נהר מתפתל עם נצנוץ
        river_points = [(x, river_y(x)) for x in range(-20, WIDTH + 20, 12)]
        for px, py in river_points:
            pygame.draw.circle(world, WATER, (int(px), int(py)), 46)
        for px, py in river_points:
            pygame.draw.circle(world, RIVER_WATER, (int(px), int(py)), 30)
        shimmer_offset = (pygame.time.get_ticks() // 20) % 80
        for px, py in river_points[::3]:
            if (int(px) + shimmer_offset) % 80 < 14:
                pygame.draw.circle(world, (225, 250, 255), (int(px), int(py) - 6), 5)

        # 7.7 🌲 יער עם צללים וגוונים תלת-שכבתיים
        for tx, ty, tsize in forest_trees:
            draw_shadow(world, (tx, ty + tsize * 0.15), tsize * 0.9, tsize * 0.32, alpha=65)
            pygame.draw.rect(world, (105, 65, 38), (tx - 4, ty - 6, 8, tsize + 6), border_radius=3)
            aa_circle(world, TREE_DARK, (tx, ty - tsize * 0.75), tsize)
            aa_circle(world, TREE_MID, (tx - tsize * 0.4, ty - tsize * 1.05), tsize * 0.72)
            aa_circle(world, TREE_LIGHT, (tx + tsize * 0.3, ty - tsize * 1.15), tsize * 0.5)

        # 7.8 🌳 בית העץ
        th_x, th_y = 170, 950
        draw_shadow(world, (th_x, th_y + 210), 90, 22, alpha=70)
        pygame.draw.rect(world, (100, 65, 38), (th_x - 12, th_y, 24, 220), border_radius=6)
        aa_circle(world, TREE_DARK, (th_x, th_y - 40), 95)
        aa_circle(world, TREE_MID, (th_x - 45, th_y - 75), 65)
        aa_circle(world, TREE_LIGHT, (th_x + 35, th_y - 90), 45)
        pygame.draw.rect(world, WOOD_DARK, (th_x - 58, th_y - 113, 116, 8))
        pygame.draw.rect(world, WOOD, (th_x - 55, th_y - 110, 110, 70))
        aa_polygon(world, HOUSE_ROOF_DARK, [(th_x - 68, th_y - 108), (th_x, th_y - 154), (th_x + 68, th_y - 108)])
        aa_polygon(world, HOUSE_ROOF, [(th_x - 65, th_y - 110), (th_x, th_y - 150), (th_x + 65, th_y - 110)])
        pygame.draw.rect(world, (100, 50, 20), (th_x - 12, th_y - 60, 24, 20), border_radius=6)
        for ry in range(th_y + 10, th_y + 120, 22):
            pygame.draw.rect(world, WOOD_DARK, (th_x - 18, ry, 36, 8), border_radius=3)

        # 7.9 🛝 מגלשה ליד הנהר
        draw_shadow(world, (slide_top[0] - 14, slide_top[1]), 10, 40, alpha=55)
        pygame.draw.rect(world, WOOD, (slide_top[0] - 30, slide_top[1] - 90, 16, 90))
        pygame.draw.rect(world, WOOD, (slide_top[0] - 34, slide_top[1] - 92, 60, 14), border_radius=4)
        pygame.draw.line(world, SLIDE_COLOR, slide_top, slide_bottom, 22)
        pygame.draw.line(world, (255, 255, 255), slide_top, slide_bottom, 4)
        rider_x = slide_top[0] + (slide_bottom[0] - slide_top[0]) * slide_rider_t
        rider_y = slide_top[1] + (slide_bottom[1] - slide_top[1]) * slide_rider_t
        draw_shadow(world, (rider_x, rider_y + 6), 8, 3, alpha=55)
        aa_circle(world, (250, 210, 80), (rider_x, rider_y), 9)

        # 7.10 🧺 פינת פיקניק
        draw_shadow(world, (1390, 815), 70, 16, alpha=55)
        pygame.draw.rect(world, (200, 40, 40), (1320, 740, 100, 70), border_radius=4)
        for gx in range(1320, 1421, 20):
            pygame.draw.line(world, (255, 255, 255), (gx, 740), (gx, 810), 7)
        aa_ellipse(world, (120, 80, 40), (1462, 778), 22, 14)
        pygame.draw.line(world, WOOD_DARK, (1448, 764), (1476, 764), 3)

        # 8. ציור הכדורים
        draw_shadow(world, (v_ball_x, v_ball_y + 10), 10, 4, alpha=60)
        aa_circle(world, (241, 196, 15), (v_ball_x, v_ball_y), 10)
        aa_circle(world, (41, 128, 185), (v_ball_x, v_ball_y), 10, width=2)
        draw_shadow(world, (f_ball_x, f_ball_y + 12), 12, 5, alpha=60)
        aa_circle(world, (255, 255, 255), (f_ball_x, f_ball_y), 12)
        aa_circle(world, (0, 0, 0), (f_ball_x, f_ball_y), 12, width=2)
        aa_circle(world, (0, 0, 0), (f_ball_x, f_ball_y), 4)

        # 9. ציור הבוטים המטיילים
        for player in other_players:
            player.draw(world)

        # 9.5 סירות ומכוניות מירוץ בתנועה
        for boat in river_boats:
            boat.draw(world)
        for car in race_cars:
            car.draw(world)

    elif location == "house":
        # --- פנים הבית: סלון חמים עם קמין, ספרייה ומיטה ---
        world.blit(ROOM_WALL_IMG, (0, 0))
        world.blit(ROOM_FLOOR_IMG, (0, HEIGHT - 220))

        # חלון
        pygame.draw.rect(world, (150, 210, 240), (150, 120, 140, 100))
        pygame.draw.rect(world, WOOD, (150, 120, 140, 100), 6)
        aa_circle(world, (255, 255, 255), (220, 170), 4)

        # קמין ואש בוערת
        pygame.draw.rect(world, (90, 60, 35), (385, 700, 230, 18))          # אח
        pygame.draw.rect(world, (120, 120, 125), (400, 718, 200, 262))      # אבן הקמין
        pygame.draw.rect(world, (25, 18, 18), (440, 860, 120, 120))         # פתח האש
        fire_flicker = 12 * math.sin(pygame.time.get_ticks() * 0.012)
        soft_glow(world, (500, 930), 90, (255, 140, 40), max_alpha=90)
        aa_polygon(world, (255, 120, 20), [(455, 975), (500, 880 - fire_flicker), (545, 975)])
        aa_polygon(world, (255, 200, 60), [(468, 975), (500, 915 - fire_flicker * 0.6), (532, 975)])
        pygame.draw.rect(world, WOOD, (450, 970, 100, 14))                  # בולי עץ

        # תמונה קטנה מעל הקמין
        pygame.draw.rect(world, (90, 60, 30), (455, 600, 90, 70))
        pygame.draw.rect(world, (200, 230, 255), (462, 607, 76, 56))
        aa_circle(world, (255, 220, 80), (490, 625), 10)
        aa_polygon(world, TREE_DARK, [(470, 663), (490, 618), (510, 663)])

        # שטיח מתחת לשולחן
        aa_ellipse(world, (170, 80, 80), (1000, 1020), 170, 45)
        aa_ellipse(world, (210, 120, 110), (1000, 1020), 135, 30)

        # שולחן וכיסאות
        draw_shadow(world, (847, 962), 45, 12, alpha=55)
        pygame.draw.rect(world, WOOD, (820, 945, 55, 15))     # כיסא שמאלי
        pygame.draw.rect(world, WOOD, (822, 895, 10, 50))
        draw_shadow(world, (1000, 950), 100, 16, alpha=55)
        pygame.draw.rect(world, WOOD, (WIDTH // 2 - 90, HEIGHT - 300, 180, 25))
        pygame.draw.rect(world, WOOD, (WIDTH // 2 - 80, HEIGHT - 275, 15, 60))
        pygame.draw.rect(world, WOOD, (WIDTH // 2 + 65, HEIGHT - 275, 15, 60))
        draw_shadow(world, (1152, 962), 45, 12, alpha=55)
        pygame.draw.rect(world, WOOD, (1125, 945, 55, 15))    # כיסא ימני
        pygame.draw.rect(world, WOOD, (1168, 895, 10, 50))

        # ספריית ספרים
        draw_shadow(world, (1400, 985), 105, 16, alpha=55)
        pygame.draw.rect(world, (110, 70, 40), (1300, 760, 200, 220))
        for shelf_y in (822, 884, 946):
            pygame.draw.line(world, (70, 45, 25), (1300, shelf_y), (1500, shelf_y), 6)
        book_colors = [(200, 60, 60), (60, 130, 200), (230, 190, 50), (70, 160, 90), (160, 90, 190)]
        for row_y in (770, 832, 894):
            bx = 1312
            for i in range(9):
                col = book_colors[(i + row_y) % len(book_colors)]
                bw = 10 + (i % 3) * 3
                pygame.draw.rect(world, col, (bx, row_y, bw, 46))
                bx += bw + 3

        # מיטה נעימה בפינה
        draw_shadow(world, (1800, 985), 155, 16, alpha=55)
        pygame.draw.rect(world, (120, 80, 50), (1650, 860, 300, 120))
        pygame.draw.rect(world, (250, 245, 235), (1665, 900, 270, 70))
        pygame.draw.rect(world, (255, 255, 255), (1672, 900, 65, 32), border_radius=6)
        pygame.draw.rect(world, (230, 90, 90), (1665, 942, 270, 30))

        # מנורת תקרה תלויה
        pygame.draw.line(world, (60, 40, 20), (1000, 0), (1000, 380), 4)
        glow_pulse = 6 * math.sin(pygame.time.get_ticks() * 0.01)
        soft_glow(world, (1000, 410), 70 + glow_pulse, (255, 235, 170), max_alpha=110)
        aa_circle(world, (255, 200, 80), (1000, 410), 22)

        draw_hebrew(world, "בפנים הבית", (WIDTH // 2 - 100, 40), (60, 40, 20))
        draw_hebrew(world, "לחץ בכל מקום או ESC כדי לצאת", (WIDTH // 2 - 220, 90), (90, 60, 30))

    elif location == "cave":
        # --- פנים המערה: חשוכה, מוארת רק ע"י פנס הסמן שלך (כמו ב-cursor camp) ---
        for bat in cave_bats:
            bat.update()

        world.blit(CAVE_ROCK_IMG, (0, 0))
        world.blit(CAVE_FLOOR_IMG, (0, HEIGHT - 200))
        # גבישים זוהרים
        glow = int(150 + 100 * math.sin(movie_frame * 0.08))
        for cx, cy, size in [(200, 300, 30), (500, 220, 45), (850, 350, 25), (1000, 250, 35)]:
            soft_glow(world, (cx, cy), size * 1.8, (glow // 2, glow, 255), max_alpha=70)
            aa_polygon(world, (glow // 2, glow, 255),
                       [(cx, cy - size), (cx + size // 2, cy), (cx, cy + size), (cx - size // 2, cy)])
        movie_frame += 1

        for bat in cave_bats:
            bat.draw(world, movie_frame)

        # אפקט פנס: חושך מלא עם עיגול אור רך סביב הסמן שחושף את מה שסביבו
        darkness = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        darkness.fill((5, 5, 15, 238))
        steps = 10
        max_r = 150
        for i in range(steps, 0, -1):
            r = int(max_r * i / steps)
            alpha = int(238 * (i / steps))
            pygame.draw.circle(darkness, (5, 5, 15, alpha), (mouse_x, mouse_y), r)
        world.blit(darkness, (0, 0))

        draw_hebrew(world, "בפנים המערה", (WIDTH // 2 - 100, 40), (200, 220, 255))
        draw_hebrew(world, "לחץ בכל מקום או ESC כדי לצאת", (WIDTH // 2 - 220, 90), (170, 190, 220))

    elif location == "treehouse":
        # --- פנים בית העץ: ערסל, פנס תלוי, דגלונים וארגז מטמון ---
        world.blit(TREEHOUSE_WALL_IMG, (0, 0))
        world.blit(TREEHOUSE_FLOOR_IMG, (0, HEIGHT - 260))
        for lx in range(0, WIDTH, 60):
            pygame.draw.line(world, (150, 100, 60), (lx, HEIGHT - 260), (lx, HEIGHT), 3)
        pygame.draw.rect(world, (60, 40, 25), (WIDTH // 2 - 40, HEIGHT - 260, 80, 40))  # פתח סולם ברצפה
        pygame.draw.rect(world, WOOD, (WIDTH // 2 - 60, HEIGHT - 260, 14, 90))          # מעקה בטיחות לפתח
        pygame.draw.rect(world, WOOD, (WIDTH // 2 + 46, HEIGHT - 260, 14, 90))
        pygame.draw.line(world, WOOD, (WIDTH // 2 - 60, HEIGHT - 210), (WIDTH // 2 + 60, HEIGHT - 210), 6)

        # ענפים ועלווה נשקפים מבעד לחלונות
        aa_circle(world, TREE_DARK, (170, 160), 110)
        aa_circle(world, TREE_LIGHT, (330, 130), 80)
        aa_circle(world, TREE_LIGHT, (1900, 150), 90)
        aa_circle(world, TREE_DARK, (1750, 180), 70)
        aa_circle(world, (150, 210, 240), (230, 220), 90)  # חלון עגול
        aa_circle(world, WOOD, (230, 220), 90, width=8)

        # דגלוני קישוט לאורך התקרה
        bunting_colors = [(230, 60, 60), (240, 200, 40), (60, 150, 220), (90, 200, 120)]
        pygame.draw.line(world, (80, 60, 40), (500, 60), (1400, 60), 3)
        for i, fx in enumerate(range(520, 1400, 55)):
            col = bunting_colors[i % len(bunting_colors)]
            aa_polygon(world, col, [(fx, 62), (fx + 28, 62), (fx + 14, 100)])

        # פנס נפט תלוי
        pygame.draw.line(world, (70, 50, 30), (1000, 0), (1000, 260), 4)
        lantern_glow = 6 * math.sin(pygame.time.get_ticks() * 0.012)
        soft_glow(world, (1000, 300), 55 + lantern_glow, (255, 210, 130), max_alpha=120)
        aa_polygon(world, (90, 60, 30), [(970, 260), (1000, 235), (1030, 260)])
        pygame.draw.rect(world, (90, 60, 30), (975, 260, 50, 60))
        pygame.draw.rect(world, (255, 225, 140), (985, 270, 30, 40))

        # ערסל תלוי בין הענפים
        hammock_a, hammock_b, sag = (1500, 320), (1880, 320), 130
        hammock_pts = []
        for i in range(21):
            t = i / 20
            hx = hammock_a[0] + (hammock_b[0] - hammock_a[0]) * t
            hy = hammock_a[1] + sag * 4 * t * (1 - t)
            hammock_pts.append((hx, hy))
        draw_shadow(world, (1690, 900), 200, 18, alpha=40)
        pygame.draw.line(world, (110, 70, 40), (hammock_a[0] - 20, hammock_a[1] - 40), hammock_a, 5)
        pygame.draw.line(world, (110, 70, 40), (hammock_b[0] + 20, hammock_b[1] - 40), hammock_b, 5)
        pygame.draw.lines(world, (210, 170, 110), False, hammock_pts, 10)
        for px, py in hammock_pts[::3]:
            pygame.draw.line(world, (150, 110, 65), (px, py - 8), (px, py + 8), 2)

        # ארגז מטמון בפינה
        draw_shadow(world, (1650, 985), 90, 14, alpha=55)
        pygame.draw.rect(world, (120, 80, 45), (1580, 900, 140, 70))
        pygame.draw.rect(world, (90, 60, 30), (1580, 878, 140, 28), border_radius=8)
        pygame.draw.rect(world, (200, 170, 60), (1638, 888, 24, 55))
        pygame.draw.line(world, (200, 170, 60), (1580, 916), (1720, 916), 4)

        draw_hebrew(world, "בפנים בית העץ", (WIDTH // 2 - 120, 40), (70, 45, 20))
        draw_hebrew(world, "לחץ בכל מקום או ESC כדי לצאת", (WIDTH // 2 - 220, 90), (100, 65, 30))

    # 10. ציור סמן העכבר שלך (חץ בסגנון סמן עכבר קלאסי, מוחלק ועם צל)
    my_color = (231, 76, 60) # אדום כברירת מחדל
    if location == "outside":
        if mouse_y < 90:
            my_color = (41, 128, 185) # כחול שחייה בים
        elif mouse_x > 1000 and mouse_y > 520:
            my_color = (30, 40, 50) # מוסתר במערה
    elif location == "cave":
        my_color = (255, 240, 200) # פנס זוהר בתוך המערה

    draw_shadow(world, (mouse_x + 6, mouse_y + 22), 10, 4, alpha=70)
    my_cursor_points = cursor_shape(mouse_x, mouse_y)
    my_ipts = [(int(px), int(py)) for px, py in my_cursor_points]
    gfxdraw.filled_polygon(world, my_ipts, my_color)
    gfxdraw.aapolygon(world, my_ipts, my_color)
    gfxdraw.aapolygon(world, my_ipts, (20, 20, 20))

    # עדכון מסך: הקטנת המפה הגדולה לגודל החלון בפועל
    if _scale >= 0.999:
        screen.blit(world, (0, 0))
    else:
        pygame.transform.smoothscale(world, (WINDOW_WIDTH, WINDOW_HEIGHT), screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
