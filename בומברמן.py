"""
Bomberman - משחק בומברמן בפייתון עם pygame (גרסה עם גרפיקה משודרגת)
====================================================================
שלטים:
  חצים / WASD  - תנועה
  רווח (SPACE) - הנחת פצצה / מעבר לשלב הבא (אחרי סיום שלב)
  ENTER        - הנחת פצצת אטום (פיצוץ ענק, ללא הגבלת שימוש)
  SHIFT        - הנחת פצצת מימן (פיצוץ ענק מאוד, ללא הגבלת שימוש)
  1            - רעידת אדמה! מנפצת לבנים ומפילה אויבים בכל המפה (עם השהיה קצרה)
  2            - טורנדו נודד! עמוד סופה שנע על המפה, שואב ומחסל אויבים ומנפץ לבנים
  3            - צונאמי! קיר מים ענק שסוחף את כל המפה מקצה לקצה (השהיה ארוכה)
  4            - הר געש! מתפרץ בלי סוף - עשן ולבה שנוחתת ונשארת בוערת (זהירות, שורף גם אותך!)
  5            - סופת חול ואבק! קיר אבק ענק ומתגלגל שסוחף את המפה מקצה לקצה (השהיה ארוכה)
  ESC          - יציאה
  R            - התחלה מחדש אחרי Game Over / ניצחון

המשחק כולל 4 שלבים בקושי עולה (יותר אויבים, מהירים יותר, פחות זמן).
בשלב 2 יש מפלצות מסוג "רודף" (אדומות) שנעות ישירות לעבר השחקן.
בשלב 3 יש "רוחות רפאים" (חיוורות) שרודפות את השחקן ונעלמות מהעין לרגעים.
בשלב 4 (השלב האחרון) מחכה בוס ענק ועמיד עם פס חיים משלו, שמלווה במפלצות "רודף" -
הבוס נע לאט אך נחוש, ומדי כמה שניות "משליך" ומנפץ לבנים סביבו כדי לפרוץ דרך אליכם.
הניקוד נשמר בין השלבים, והחיים מתחדשים בכל מעבר שלב.

מיוחד:
  * השחקן הוא צב (שריון סולקטה) - הראש פונה לכיוון ההליכה.
  * מקש "2" - טורנדו נודד שנע על המפה כמה שניות, מנפץ לבנים בדרכו,
    שואב אליו אויבים ומחסל את מי שנקלע לליבה. השהיה קצרה בין הפעלות.
  * מקש "3" - צונאמי: קיר מים ענק שנכנס מהצד הרחוק מהשחקן ושוטף את כל המפה -
    מנפץ את כל הלבנים בדרכו ומטביע כל אויב. "נשק אולטימטיבי" עם השהיה ארוכה.
  * "קומבו" - חיסול של כמה אויבים בפיצוץ אחד מזכה בבונוס ניקוד מטפס.
  * רעידת מסך דרמטית בכל פיצוץ גדול.
  * מקש "1" - רעידת אדמה: רשת סדקים פוליגונלית (כמו בוץ יבש) נפערת על פני כל
    הקרקע ו-נשארת עד סוף השלב (ומצטברת בכל רעידה נוספת). המסך מיטלטל בעוצמה,
    חלק גדול מהלבנים מתנפץ ואויבים אקראיים נופלים. השהיה קצרה בין הפעלות.
  * מקש "5" - סופת חול ואבק: קיר אבק ענק וסמיך (בגוני חול-כתום, עם גושי אבק
    מתגלגלים וגרגירים נסחפים) שנכנס מהצד הרחוק מהשחקן וגורף את כל המפה -
    קובר לבנים בדרכו וסוחף כל אויב שנתפס בו. משאיר אחריו ענן אבק דליל שמתפזר
    לאט. "נשק אולטימטיבי" נוסף עם השהיה ארוכה.
  * שלב 4 - בוס: אויב ענק עם פס חיים (מספר "פגיעות" עד לחיסול), עמיד בפני נשק
    רגיל ובפני הנשקים המיוחדים (סופג נזק חלקי מכל אחד מהם), וכל כמה שניות
    "רועם" ומנפץ לבנים בסביבתו כדי להתקדם לעברכם.

איך להריץ:
  1. ודא שמותקן פייתון 3
  2. התקן pygame:   pip install pygame
  3. הרץ:           python bomberman.py

מטרה: לפוצץ את כל האויבים לפני שנגמר הזמן / החיים, תוך הימנעות מהתפוצצויות.
"""

import pygame
import random
import sys
import time
import math

# ---------------------------------------------------------------------------
# הגדרות כלליות
# ---------------------------------------------------------------------------
TILE = 44
COLS = 15
ROWS = 13
WIDTH = COLS * TILE
HEIGHT = ROWS * TILE + 64  # + פס מידע עליון
FPS = 60

BOMB_TIMER = 2.0
EXPLOSION_DURATION = 0.55
EXPLOSION_RANGE = 2
PLAYER_SPEED_DELAY = 0.11
ENEMY_MOVE_DELAY = 0.35

# ---------------------------------------------------------------------------
# שלבים (4 שלבים בקושי עולה, האחרון עם בוס)
# ---------------------------------------------------------------------------
LEVELS = [
    {"enemies": 4, "enemy_delay": 0.38, "time_limit": 150, "brick_density": 0.55, "enemy_kind": "roamer"},
    {"enemies": 6, "enemy_delay": 0.30, "time_limit": 130, "brick_density": 0.62, "enemy_kind": "chaser"},
    {"enemies": 7, "enemy_delay": 0.26, "time_limit": 110, "brick_density": 0.70, "enemy_kind": "ghost"},
    {"enemies": 4, "enemy_delay": 0.30, "time_limit": 200, "brick_density": 0.48, "enemy_kind": "chaser", "boss": True},
]
TOTAL_LEVELS = len(LEVELS)

ATOM_RANGE = 4          # רדיוס פיצוץ פצצת האטום (משבצות) - שימוש ללא הגבלה
HYDROGEN_RANGE = 8      # רדיוס פיצוץ פצצת המימן (ענק) - שימוש ללא הגבלה

# ---------------------------------------------------------------------------
# בוס (שלב 4)
# ---------------------------------------------------------------------------
BOSS_HP = 12                # מספר "פגיעות" (מנורמלות לנזק פצצה רגילה) עד לחיסול
BOSS_ROAR_INTERVAL = 3.2    # שניות בין "שאגות" שמנפצות לבנים סביב הבוס

# ---------------------------------------------------------------------------
# רעידת אדמה (מקש 1)
# ---------------------------------------------------------------------------
EARTHQUAKE_COOLDOWN = 6.0        # שניות המתנה בין הפעלות
EARTHQUAKE_BRICK_CHANCE = 0.5    # סיכוי לניפוץ כל לבנה
EARTHQUAKE_ENEMY_CHANCE = 0.5    # סיכוי להפלת כל אויב
EARTHQUAKE_SHAKE_TIME = 1.6      # משך ניעור המסך
EARTHQUAKE_GLOW_TIME = 1.1       # כמה זמן סדקים טריים "לוהטים" בכתום לפני שמתקררים
EARTHQUAKE_CRACK_REVEAL = 0.4    # משך אנימציית ה"היבקעות" של הסדקים כלפי חוץ
EARTHQUAKE_FLASH = 0.4           # עוצמת הבזק המסך ברגע הרעש
# הסדקים באדמה נשארים לצמיתות (עד סוף השלב) ומצטברים בכל רעידת אדמה נוספת

CRACK_SHADOW = (6, 10, 6)       # הילת צל רכה סביב הסדק
CRACK_WALL = (58, 44, 33)       # דופן הבקע (חום אדמה)
CRACK_LINE = (17, 13, 10)       # ליבת הבקע (כמעט שחור)
CRACK_LIP = (232, 240, 205)     # שפה מוארת בצד אחד (תחושת "לוח" מורם)
CRACK_HOT_COLOR = (255, 148, 40)
CRACK_HOT_CORE = (255, 226, 150)

# ---------------------------------------------------------------------------
# טורנדו (מקש 2) - עמוד סופה נודד ששואב ומחסל אויבים ומנפץ לבנים בדרכו
# ---------------------------------------------------------------------------
TORNADO_COOLDOWN = 8.0
TORNADO_LIFETIME = 5.2
TORNADO_SPEED = 122.0           # פיקסלים לשנייה
TORNADO_WANDER = 2.1           # רעש הנדידה (rad/s)
TORNADO_HOMING = 2.2          # נטייה לעבר האויב הקרוב (rad/s)
TORNADO_KILL_R = TILE * 1.25   # רדיוס חיסול אויבים
TORNADO_SUCK_R = TILE * 2.7    # רדיוס שאיבה פנימה

# ---------------------------------------------------------------------------
# צונאמי (מקש 3) - קיר מים ענק שסוחף את כל המפה מקצה לקצה
# ---------------------------------------------------------------------------
TSUNAMI_COOLDOWN = 14.0
TSUNAMI_CROSS_TIME = 2.0       # שניות למעבר מלא על פני המפה
TSUNAMI_BAND = 210            # רוחב קיר המים (פיקסלים)
WATER_ABYSS = (12, 58, 92)     # מים עמוקים בגב הגל
WATER_DEEP = (22, 96, 138)
WATER_MID = (52, 150, 190)
WATER_CREST = (146, 220, 232)  # טורקיז בהיר בשפת הגל
WATER_FOAM = (240, 250, 255)

# ---------------------------------------------------------------------------
# הר געש (מקש 4) - מתפרץ במקום השחקן ונשאר פעיל עד סוף השלב, פולט עשן ולבה
# בלתי-פוסקים: כל כמה רגעים נורה גוש לבה שנוחת ונשאר כברֵכה בוערת לצמיתות.
# ---------------------------------------------------------------------------
VOLCANO_COOLDOWN = 22.0          # השהיה ארוכה - נשק "יום דין"
VOLCANO_ERUPT_INTERVAL = 0.42    # שניות בין פליטות לבה
VOLCANO_RADIUS = 3.4             # רדיוס (במשבצות) שבו נוחתים גושי הלבה
VOLCANO_EMBER_FLIGHT = 0.55      # שניות מעוף של גוש לבה מהקרטר ועד הנחיתה
LAVA_TICK = 0.5                  # תדירות "כוויה" לשחקן שעומד בלבה

LAVA_CORE = (255, 224, 120)
LAVA_HOT = (255, 122, 34)
LAVA_MID = (214, 62, 24)
LAVA_DEEP = (120, 30, 20)
ROCK_CHAR = (46, 36, 34)
ROCK_CHAR_LIGHT = (78, 62, 56)
SMOKE_LIGHT = (176, 172, 168)
SMOKE_DARK = (90, 84, 82)

# ---------------------------------------------------------------------------
# סופת חול ואבק (מקש 5) - קיר אבק ענק ומתגלגל שסוחף את המפה מקצה לקצה
# ---------------------------------------------------------------------------
SANDSTORM_COOLDOWN = 16.0
SANDSTORM_CROSS_TIME = 2.6      # שניות למעבר מלא על פני המפה (קיר כבד, נע לאט מהצונאמי)
SANDSTORM_BAND = 260            # רוחב קיר האבק (פיקסלים)
SAND_DARK = (108, 66, 28)       # ליבת האבק בחזית הסופה (הכי צפוף)
SAND_MID = (184, 118, 52)       # גוף החול העיקרי
SAND_LIGHT = (222, 164, 92)     # אבק בהיר יותר, רחוק מהחזית
SAND_GLOW = (255, 208, 132)     # קו אור זהוב שחודר את קיר האבק
DUST_HAZE = (206, 158, 100)     # אבק שנשאר תלוי באוויר אחרי מעבר הסופה

# הצב (השחקן) - שריון סולקטה בגוני חול/חום
SHELL_LIGHT = (240, 216, 150)
SHELL_MID = (208, 168, 96)
SHELL_DARK = (150, 104, 50)
SHELL_LINE = (98, 62, 30)
TURTLE_SKIN = (178, 158, 108)
TURTLE_SKIN_DARK = (128, 110, 72)

# תוספות חמודות לצב - כוכב נוצץ, סומק, נצנצים (סגנון נייטרלי, לא "ילדותי-ורוד")
STAR_GOLD = (255, 210, 90)
STAR_GOLD_DARK = (224, 160, 48)
STAR_AMBER = (255, 158, 56)
BLUSH_CORAL = (255, 142, 104)
SPARKLE_WHITE = (255, 255, 255)

# פלטת צבעים (מודרנית ורכה יותר)
BLACK = (18, 18, 24)
WHITE = (245, 245, 250)
GRAY = (140, 145, 155)
DARK_GRAY = (58, 62, 74)
PANEL_BG = (24, 26, 36)

FLOOR_A = (86, 172, 96)
FLOOR_B = (76, 158, 86)

WALL_TOP = (108, 114, 128)
WALL_SIDE = (66, 70, 82)
WALL_LINE = (150, 155, 168)

BRICK_TOP = (200, 120, 72)
BRICK_SIDE = (140, 78, 44)
BRICK_LINE = (230, 160, 110)

YELLOW = (255, 214, 82)
ORANGE = (255, 140, 40)
RED_FLAME = (235, 70, 50)
DEEP_RED = (200, 40, 40)

PLAYER_BODY = (64, 140, 235)
PLAYER_DARK = (36, 90, 170)
PLAYER_FACE = (255, 224, 189)

ENEMY_BODY = (190, 80, 210)
ENEMY_DARK = (130, 40, 150)

# מפלצת מסוג "רודף" (שלב 2) - צבע שונה, נעה לכיוון השחקן
CHASER_BODY = (235, 95, 70)
CHASER_DARK = (160, 45, 35)

# מפלצת מסוג "רוח רפאים" (שלב 3) - חיוורת, רודפת, ונעלמת מהעין לרגעים
GHOST_BODY = (200, 232, 245)
GHOST_DARK = (130, 175, 200)
ENEMY_EYE = (255, 255, 255)

# הבוס (שלב 4) - ענק, סגול-כהה עם קוצים אדומים בוערים ופס חיים
BOSS_BODY = (128, 46, 156)
BOSS_DARK = (66, 18, 90)
BOSS_ACCENT = (255, 86, 58)

GREEN = (86, 200, 120)
RED = (230, 70, 70)

# סוגי משבצות
EMPTY = 0
WALL = 1
BRICK = 2


# ---------------------------------------------------------------------------
# עזרי ציור
# ---------------------------------------------------------------------------
def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_vgradient(surface, rect, color_top, color_bottom):
    x, y, w, h = rect
    if h <= 0:
        return
    for i in range(h):
        t = i / max(h - 1, 1)
        color = lerp_color(color_top, color_bottom, t)
        pygame.draw.line(surface, color, (x, y + i), (x + w, y + i))


def star_points(cx, cy, r_out, r_in, n, phase, jit):
    """נקודות של כוכב קוצני (קוץ חד ואז מפרץ פנימי), לסגנון פיצוץ קומיקס."""
    pts = []
    for i in range(n):
        a_out = phase + (i / n) * math.tau
        a_in = phase + ((i + 0.5) / n) * math.tau
        ro = r_out * jit[i % len(jit)]
        pts.append((cx + math.cos(a_out) * ro, cy + math.sin(a_out) * ro))
        pts.append((cx + math.cos(a_in) * r_in, cy + math.sin(a_in) * r_in))
    return [(int(x), int(y)) for x, y in pts]


def draw_shadow_ellipse(surface, cx, cy, w, h, alpha=90):
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, alpha), (0, 0, w, h))
    surface.blit(shadow, (cx - w // 2, cy - h // 2))


def make_map(brick_density=0.6):
    grid = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            if r == 0 or c == 0 or r == ROWS - 1 or c == COLS - 1:
                grid[r][c] = WALL
            elif r % 2 == 0 and c % 2 == 0:
                grid[r][c] = WALL

    safe_zones = {(1, 1), (1, 2), (2, 1), (1, COLS - 2), (1, COLS - 3), (2, COLS - 2)}

    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if grid[r][c] == EMPTY and (r, c) not in safe_zones:
                if random.random() < brick_density:
                    grid[r][c] = BRICK
    return grid


class Bomb:
    def __init__(self, row, col, power, owner, atom=False, hydro=False):
        self.row = row
        self.col = col
        self.power = power
        self.placed_at = time.time()
        self.owner = owner
        self.exploded = False
        self.atom = atom
        self.hydro = hydro

    @property
    def area_radius(self):
        if self.hydro:
            return HYDROGEN_RANGE
        if self.atom:
            return ATOM_RANGE
        return None


class Explosion:
    def __init__(self, cells, center, kind="normal"):
        self.cells = cells
        self.center = center
        self.kind = kind
        self.created_at = time.time()
        self.duration = 0.85 if kind in ("atom", "hydro") else EXPLOSION_DURATION
        self.kills = 0
        self.hit_enemies = set()      # מזהי אויבים שכבר נפגעו מהפיצוץ הזה (מונע פגיעה כפולה)
        # כוכב קוצני בסגנון קומיקס: מספר קוצים + אורך אקראי לכל קוץ + סיבוב
        self.n_spikes = random.choice([11, 12, 13])
        self.spike_jit = [random.uniform(0.82, 1.0) for _ in range(self.n_spikes)]
        self.spin = random.uniform(0, math.tau)
        self.spin_dir = random.choice([-1, 1])


class FloatText:
    """טקסט קופץ קצר לתצוגת משוב (קומבו / רעידת אדמה)."""
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.created_at = time.time()
        self.duration = 1.1


class Entity:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.alive = True

    @property
    def pos(self):
        return (self.row, self.col)


class Player(Entity):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.lives = 3
        self.bomb_capacity = 3
        self.bomb_power = EXPLOSION_RANGE
        self.last_move = 0
        self.score = 0
        self.invincible_until = 0
        self.facing = (0, 1)
        self.walk_phase = 0.0
        self.moving = False

    def hit(self):
        now = time.time()
        if now < self.invincible_until:
            return
        self.lives -= 1
        self.invincible_until = now + 2.0
        if self.lives <= 0:
            self.alive = False


class Enemy(Entity):
    def __init__(self, row, col, kind="roamer"):
        super().__init__(row, col)
        self.kind = kind
        self.last_move = 0
        self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        self.bob_phase = random.uniform(0, math.tau)
        # בוסים מקבלים כמה "נקודות חיים" ולוקח מספר פגיעות לחסל אותם
        self.max_hp = BOSS_HP if kind == "boss" else 1
        self.hp = self.max_hp
        self.hit_flash_until = 0.0     # הבהוב לבן קצר כשנפגע
        self.last_roar = time.time()   # לשימוש הבוס (שאגה שמנפצת לבנים)
        self.last_lava_tick = 0.0      # קצב "כוויה" מלבה, לאויבים עם כמה חיים
        self.move_delay = None         # None = להשתמש בקצב התנועה הכללי של השלב


class Tornado:
    """עמוד סופה נודד (מקש 2). מיקום בפיקסלים, כיוון מתפתל, וחיים מוגבלים."""
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.born = time.time()
        self.heading = random.uniform(0, math.tau)
        self.spin = random.uniform(0, math.tau)
        self.last_pull = 0.0
        # רסיסים שמסתחררים סביב העמוד: (זווית התחלה, רדיוס יחסי, גובה יחסי, מהירות)
        self.debris = [(random.uniform(0, math.tau), random.uniform(0.35, 1.0),
                        random.uniform(0.05, 0.95), random.uniform(0.7, 1.6))
                       for _ in range(16)]


class Tsunami:
    """קיר מים ענק (מקש 3) שנע מקצה אחד של המפה לקצה השני וסוחף הכול."""
    def __init__(self, direction):
        self.dir = direction                     # +1 ימינה, -1 שמאלה
        self.born = time.time()
        self.front = float(-TSUNAMI_BAND) if direction > 0 else float(WIDTH + TSUNAMI_BAND)
        self.spray = [(random.random(), random.random(), random.uniform(0.6, 1.4))
                      for _ in range(34)]
        self.hit_ids = set()          # מזהי אויבים שכבר נפגעו מהגל הזה


class Sandstorm:
    """סופת חול ואבק (מקש 5) - קיר אבק ענק ומתגלגל שנע מקצה אחד של המפה לשני."""
    def __init__(self, direction):
        self.dir = direction                     # +1 ימינה, -1 שמאלה
        self.born = time.time()
        self.front = float(-SANDSTORM_BAND) if direction > 0 else float(WIDTH + SANDSTORM_BAND)
        # גושי אבק "כרוביתיים" שבונים את גוף הקיר - קבועים לאורך חיי הסופה,
        # rx=0 עמוק בגב הקיר (בהיר, שקוף) עד rx=1 בחזית (כהה, צפוף)
        self.chunks = []
        rows = 10
        for ri in range(rows):
            ry = ri / (rows - 1)
            for _ in range(random.randint(3, 5)):
                self.chunks.append((random.uniform(0.05, 1.0), ry,
                                    random.uniform(0.55, 1.15), random.uniform(0, math.tau),
                                    random.uniform(0.6, 1.4)))
        # "כתר" גושים גבוהים שמתנשאים מעל קו הקרקע - תחושת קיר ענק שממלא את השמיים
        self.crown = [(random.uniform(0.15, 1.0), random.uniform(0.0, 1.0),
                       random.uniform(0.5, 1.0), random.uniform(0, math.tau))
                      for _ in range(16)]
        self.grains = [(random.random(), random.random(), random.uniform(0.6, 1.6))
                       for _ in range(46)]
        self.hit_ids = set()          # מזהי אויבים שכבר נפגעו מהסופה הזו


class Volcano:
    """הר געש (מקש 4) - מתפרץ במקום נתון ונשאר פעיל עד סוף השלב."""
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.born = time.time()
        self.next_erupt = 0.0
        self.last_smoke = 0.0
        self.embers = []   # [sx, sy, tx, ty, trow, tcol, born]
        self.smoke = []    # [x, y, vx, radius, born]
        self.sparks = []   # [x, y, vx, vy, born]  - ניצוצות זעירים עולים בתוך עמוד העשן

        # --- מראה ההר: פרופיל משונן קבוע (לא "רועד" בין פריימים), שונה מעט בכל הפעלה ---
        seed = (row * 1013 + col * 7919 + int(self.born * 1000)) & 0xFFFFFFFF
        rng = random.Random(seed)
        self.tilt = rng.uniform(-0.14, 0.14)                 # פסגה מוטה קלות
        self.left_jag = [rng.uniform(-1, 1) for _ in range(11)]
        self.right_jag = [rng.uniform(-1, 1) for _ in range(11)]
        self.strata = sorted(rng.uniform(0.14, 0.88) for _ in range(5))
        # נהרות לבה זוהרים במורד המדרון - כמה, ברוחב ואורך משתנים, חלקם עד הבסיס
        self.fissures = [(rng.uniform(0.55, 0.95), rng.uniform(-0.62, 0.62),
                          rng.uniform(0.6, 1.6), rng.uniform(2.0, 4.2)) for _ in range(6)]
        self.rubble = [(rng.uniform(-1.85, 1.85), rng.uniform(0.55, 1.0),
                        rng.uniform(2, 5)) for _ in range(12)]


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Bomberman")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.big_font = pygame.font.SysFont("arial", 48, bold=True)
        self.small_font = pygame.font.SysFont("arial", 16)
        self._floor_vignette = None
        self.reset()

    def reset(self):
        self.level = 1
        self.player = Player(1, 1)
        self.start_level()

    def start_level(self):
        cfg = LEVELS[self.level - 1]
        self.grid = make_map(cfg["brick_density"])
        self.player.row, self.player.col = 1, 1
        self.player.facing = (0, 1)
        self.player.lives = 3          # חידוש חיים בכל מעבר שלב
        self.player.alive = True
        self.player.invincible_until = time.time() + 2.0
        self.bombs = []
        self.explosions = []
        self.float_texts = []
        self.crack_paths = []             # פוליליינים של סדקים שנצברו בשלב
        self.crack_big = None             # שכבת-על ב-supersampling (מציירים עליה רק סדקים חדשים)
        self.crack_rendered = 0           # כמה מ-crack_paths כבר צוירו ל-crack_big
        self.crack_surface = None         # שכבת ציור מוכנה (עם anti-alias) של כל הסדקים
        self.shake_until = 0.0
        self.shake_mag = 0.0
        self.earthquake_ready_at = 0.0
        self.tornado = None
        self.tornado_ready_at = 0.0
        self.tsunami = None
        self.tsunami_ready_at = 0.0
        self.flood_until = 0.0
        self.sandstorm = None
        self.sandstorm_ready_at = 0.0
        self.dust_until = 0.0
        self.volcanoes = []
        self.volcano_ready_at = 0.0
        self.lava = {}                     # (row,col) -> זמן היווצרות (ברֵכת לבה קבועה)
        self._last_lava_tick = 0.0
        self._terrain_dirty = True         # רצפה+קירות+לבנים מרונדרים לשכבה ומצוירים כ-blit
        self.enemy_move_delay = cfg["enemy_delay"]
        self.enemies = self.spawn_enemies(cfg)
        self.game_over = False
        self.win = False
        self.lost = False
        self.level_cleared = False
        self.start_time = time.time()
        self.time_limit = cfg["time_limit"]

    def next_level(self):
        if self.level < TOTAL_LEVELS:
            self.level += 1
            self.start_level()

    def spawn_enemies(self, cfg):
        n = cfg["enemies"]
        kind = cfg.get("enemy_kind", "roamer")
        is_boss_level = cfg.get("boss", False)
        target_n = (n - 1) if is_boss_level else n
        enemies = []
        attempts = 0
        while len(enemies) < target_n and attempts < 500:
            attempts += 1
            r = random.randint(1, ROWS - 2)
            c = random.randint(1, COLS - 2)
            if self.grid[r][c] == EMPTY and (r > 3 or c > 3):
                if not any(e.pos == (r, c) for e in enemies):
                    enemies.append(Enemy(r, c, kind))

        if is_boss_level:
            # מציבים את הבוס בתא הפנוי הרחוק ביותר מנקודת הפתיחה של השחקן
            best, best_d = None, -1
            for r in range(1, ROWS - 1):
                for c in range(1, COLS - 1):
                    if self.grid[r][c] == EMPTY and not any(e.pos == (r, c) for e in enemies):
                        d = abs(r - self.player.row) + abs(c - self.player.col)
                        if d > best_d:
                            best_d, best = d, (r, c)
            if best is None:
                best = (ROWS - 2, COLS - 2)
            boss = Enemy(best[0], best[1], "boss")
            boss.move_delay = cfg["enemy_delay"] * 1.9   # הבוס איטי אך נחוש
            enemies.append(boss)
        return enemies

    # ------------------------------------------------------------------
    # לוגיקת משחק
    # ------------------------------------------------------------------
    def is_walkable(self, row, col):
        if row < 0 or col < 0 or row >= ROWS or col >= COLS:
            return False
        if self.grid[row][col] != EMPTY:
            return False
        if any(b.row == row and b.col == col for b in self.bombs):
            return False
        return True

    def try_move(self, entity, drow, dcol):
        nr, nc = entity.row + drow, entity.col + dcol
        if self.is_walkable(nr, nc):
            entity.row, entity.col = nr, nc
            return True
        return False

    def place_bomb(self):
        active_bombs = [b for b in self.bombs if b.owner == "player"]
        if len(active_bombs) >= self.player.bomb_capacity:
            return
        if any(b.row == self.player.row and b.col == self.player.col for b in self.bombs):
            return
        self.bombs.append(Bomb(self.player.row, self.player.col, self.player.bomb_power, "player"))

    def place_atom_bomb(self):
        if any(b.row == self.player.row and b.col == self.player.col for b in self.bombs):
            return
        self.bombs.append(Bomb(self.player.row, self.player.col, ATOM_RANGE, "player", atom=True))

    def place_hydro_bomb(self):
        if any(b.row == self.player.row and b.col == self.player.col for b in self.bombs):
            return
        self.bombs.append(Bomb(self.player.row, self.player.col, HYDROGEN_RANGE, "player", hydro=True))

    def destroy_brick(self, r, c):
        """הופך לבנה לרצפה."""
        self.grid[r][c] = EMPTY
        self._terrain_dirty = True     # לבנות המטוחנות -> לרנדר מחדש את שכבת השטח

    def add_shake(self, magnitude, seconds):
        self.shake_mag = max(self.shake_mag, magnitude)
        self.shake_until = max(self.shake_until, time.time() + seconds)

    def hit_enemy(self, enemy, dmg=1):
        """מפעיל נזק על אויב. אויבים רגילים מתים ממכה אחת; בוסים סופגים נזק
        לפי פס החיים שלהם. מחזיר True אם האויב מת מהפגיעה הזו."""
        if not enemy.alive:
            return False
        if enemy.max_hp > 1:
            enemy.hp -= dmg
            enemy.hit_flash_until = time.time() + 0.2
            if enemy.hp <= 0:
                enemy.alive = False
                return True
            return False
        enemy.alive = False
        return True

    def award_kill(self, enemy, row, col, label, color):
        """מוסיף ניקוד ומציג טקסט קופץ עבור חיסול אויב (עם התייחסות מיוחדת לבוס)."""
        if enemy.kind == "boss":
            gain = 500
            self.player.score += gain
            self.spawn_float(row, col, f"BOSS DEFEATED!  +{gain}", BOSS_ACCENT)
            self.add_shake(22, 0.7)
        else:
            self.player.score += 100
            self.spawn_float(row, col, label, color)

    def trigger_earthquake(self):
        now = time.time()
        if now < self.earthquake_ready_at:
            return
        self.earthquake_ready_at = now + EARTHQUAKE_COOLDOWN

        # ניעור מסך חזק וארוך
        self.add_shake(28, EARTHQUAKE_SHAKE_TIME)

        # האדמה נבקעת - רשת סדקים פוליגונלית שנשארת על הקרקע
        self.spawn_quake_cracks()

        # ניפוץ לבנים בכל המפה
        for r in range(1, ROWS - 1):
            for c in range(1, COLS - 1):
                if self.grid[r][c] == BRICK and random.random() < EARTHQUAKE_BRICK_CHANCE:
                    self.destroy_brick(r, c)

        # הפלת אויבים שנתפסו ברעש (בוסים סופגים נזק חלקי בלבד)
        for enemy in self.enemies:
            if enemy.alive and random.random() < EARTHQUAKE_ENEMY_CHANCE:
                died = self.hit_enemy(enemy, 3)
                if died:
                    self.award_kill(enemy, enemy.row, enemy.col, "quake!", (210, 170, 120))
                elif enemy.kind == "boss":
                    self.spawn_float(enemy.row, enemy.col, "-3", (210, 170, 120))

        self.spawn_float(self.player.row, self.player.col, "EARTHQUAKE!", ORANGE)

    # ------------------------------------------------------------------
    # טורנדו (מקש 2)
    # ------------------------------------------------------------------
    def trigger_tornado(self):
        now = time.time()
        if now < self.tornado_ready_at or self.tornado is not None:
            return
        self.tornado_ready_at = now + TORNADO_COOLDOWN
        top = 64
        self.tornado = Tornado(self.player.col * TILE + TILE // 2,
                               self.player.row * TILE + top + TILE // 2)
        self.spawn_float(self.player.row, self.player.col, "TORNADO!", (205, 228, 242))
        self.add_shake(10, 0.5)

    def update_tornado(self):
        t = self.tornado
        if t is None:
            return
        now = time.time()
        if now - t.born > TORNADO_LIFETIME:
            self.tornado = None
            return

        top = 64
        dt = 1.0 / FPS
        # נדידה אקראית + נטייה עדינה לעבר האויב החי הקרוב ביותר
        t.heading += random.uniform(-1.0, 1.0) * TORNADO_WANDER * dt
        alive = [e for e in self.enemies if e.alive]
        if alive:
            tgt = min(alive, key=lambda e: (e.col * TILE - t.x) ** 2
                      + (e.row * TILE + top - t.y) ** 2)
            desired = math.atan2(tgt.row * TILE + top + TILE // 2 - t.y,
                                 tgt.col * TILE + TILE // 2 - t.x)
            diff = (desired - t.heading + math.pi) % math.tau - math.pi
            t.heading += max(-TORNADO_HOMING * dt, min(TORNADO_HOMING * dt, diff))
        nx = t.x + math.cos(t.heading) * TORNADO_SPEED * dt
        ny = t.y + math.sin(t.heading) * TORNADO_SPEED * dt
        margin = TILE * 0.8
        if nx < margin or nx > WIDTH - margin:
            t.heading = math.pi - t.heading
            nx = min(max(nx, margin), WIDTH - margin)
        if ny < top + margin or ny > HEIGHT - margin:
            t.heading = -t.heading
            ny = min(max(ny, top + margin), HEIGHT - margin)
        t.x, t.y = nx, ny
        t.spin += dt * 16

        # מנפץ לבנים בתאים שמתחת/סביב הליבה
        trow = int((t.y - top) // TILE)
        tcol = int(t.x // TILE)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                r, c = trow + dr, tcol + dc
                if 0 <= r < ROWS and 0 <= c < COLS and self.grid[r][c] == BRICK:
                    self.destroy_brick(r, c)

        pull = (now - t.last_pull) >= 0.09
        if pull:
            t.last_pull = now
        for e in self.enemies:
            if not e.alive:
                continue
            ex = e.col * TILE + TILE // 2
            ey = e.row * TILE + top + TILE // 2
            d = math.hypot(ex - t.x, ey - t.y)
            if d < TORNADO_KILL_R:
                if e.max_hp > 1:
                    if pull:
                        died = self.hit_enemy(e, 1)
                        if died:
                            self.award_kill(e, e.row, e.col, "swept!", (205, 224, 236))
                else:
                    e.alive = False
                    self.award_kill(e, e.row, e.col, "swept!", (205, 224, 236))
            elif d < TORNADO_SUCK_R and pull:
                # צעד אחד לכיוון הליבה (בציר הדומיננטי)
                if abs(t.y - ey) > abs(t.x - ex):
                    self.try_move(e, 1 if t.y > ey else -1, 0)
                else:
                    self.try_move(e, 0, 1 if t.x > ex else -1)

        self.add_shake(5, 0.1)

    # ------------------------------------------------------------------
    # צונאמי (מקש 3)
    # ------------------------------------------------------------------
    def trigger_tsunami(self):
        now = time.time()
        if now < self.tsunami_ready_at or self.tsunami is not None:
            return
        self.tsunami_ready_at = now + TSUNAMI_COOLDOWN
        # מגיע מהצד הרחוק מהשחקן, כדי שהגל יעבור על פני כל המפה
        direction = 1 if self.player.col < COLS // 2 else -1
        self.tsunami = Tsunami(direction)
        self.spawn_float(self.player.row, self.player.col, "TSUNAMI!", WATER_FOAM)
        self.add_shake(14, 0.6)

    def update_tsunami(self):
        t = self.tsunami
        if t is None:
            return
        speed = (WIDTH + 2 * TSUNAMI_BAND) / TSUNAMI_CROSS_TIME
        prev = t.front
        t.front += t.dir * speed / FPS
        lo, hi = min(prev, t.front), max(prev, t.front)

        for c in range(1, COLS - 1):
            ccx = c * TILE + TILE // 2
            if lo <= ccx <= hi:                    # חזית הגל חוצה את העמודה הזו
                for r in range(1, ROWS - 1):
                    if self.grid[r][c] == BRICK:
                        self.destroy_brick(r, c)
                for e in self.enemies:
                    if e.alive and e.col == c and id(e) not in t.hit_ids:
                        t.hit_ids.add(id(e))
                        died = self.hit_enemy(e, 4)
                        if died:
                            self.award_kill(e, e.row, e.col, "washed away!", (150, 210, 240))

        self.add_shake(7, 0.15)
        if (t.dir > 0 and t.front > WIDTH + TSUNAMI_BAND) or \
           (t.dir < 0 and t.front < -TSUNAMI_BAND):
            self.tsunami = None
            self.flood_until = time.time() + 1.1   # שאריות מים מתנקזות

    # ------------------------------------------------------------------
    # סופת חול ואבק (מקש 5)
    # ------------------------------------------------------------------
    def trigger_sandstorm(self):
        now = time.time()
        if now < self.sandstorm_ready_at or self.sandstorm is not None:
            return
        self.sandstorm_ready_at = now + SANDSTORM_COOLDOWN
        # מגיע מהצד הרחוק מהשחקן, כדי שהקיר יעבור על פני כל המפה
        direction = 1 if self.player.col < COLS // 2 else -1
        self.sandstorm = Sandstorm(direction)
        self.spawn_float(self.player.row, self.player.col, "SANDSTORM!", SAND_GLOW)
        self.add_shake(12, 0.7)

    def update_sandstorm(self):
        t = self.sandstorm
        if t is None:
            return
        speed = (WIDTH + 2 * SANDSTORM_BAND) / SANDSTORM_CROSS_TIME
        prev = t.front
        t.front += t.dir * speed / FPS
        lo, hi = min(prev, t.front), max(prev, t.front)

        for c in range(1, COLS - 1):
            ccx = c * TILE + TILE // 2
            if lo <= ccx <= hi:                    # חזית הסופה חוצה את העמודה הזו
                for r in range(1, ROWS - 1):
                    if self.grid[r][c] == BRICK:
                        self.destroy_brick(r, c)
                for e in self.enemies:
                    if e.alive and e.col == c and id(e) not in t.hit_ids:
                        t.hit_ids.add(id(e))
                        died = self.hit_enemy(e, 4)
                        if died:
                            self.award_kill(e, e.row, e.col, "buried!", SAND_LIGHT)

        self.add_shake(4, 0.12)
        if (t.dir > 0 and t.front > WIDTH + SANDSTORM_BAND) or \
           (t.dir < 0 and t.front < -SANDSTORM_BAND):
            self.sandstorm = None
            self.dust_until = time.time() + 1.8    # אבק דליל שנשאר תלוי באוויר ומתפזר

    # ------------------------------------------------------------------
    # הר געש (מקש 4)
    # ------------------------------------------------------------------
    def trigger_volcano(self):
        now = time.time()
        if now < self.volcano_ready_at:
            return
        self.volcano_ready_at = now + VOLCANO_COOLDOWN
        v = Volcano(self.player.row, self.player.col)
        self.volcanoes.append(v)
        self._ignite(v.row, v.col)             # פתח הלוע עצמו הופך ללבה
        self.spawn_float(v.row, v.col, "VOLCANO!", LAVA_HOT)
        self.add_shake(18, 0.9)

    def _ignite(self, r, c):
        if 1 <= r < ROWS - 1 and 1 <= c < COLS - 1 and self.grid[r][c] != WALL:
            if self.grid[r][c] == BRICK:
                self.destroy_brick(r, c)
            self.lava.setdefault((r, c), time.time())

    def update_volcanoes(self):
        now = time.time()
        top = 64
        dt = 1.0 / FPS
        for v in self.volcanoes:
            ccx = v.col * TILE + TILE // 2
            ccy = v.row * TILE + top + TILE // 2 - 12       # גובה הלוע

            # עמוד עשן גדול ומאיים שמיתמר בלי הפסקה, כמו בהתפרצות אמיתית
            if now - v.last_smoke > 0.055:
                v.last_smoke = now
                v.smoke.append([ccx + random.uniform(-4, 4), ccy - 6,
                                random.uniform(-9, 13), random.uniform(7, 12), now])
                if len(v.smoke) > 60:
                    v.smoke.pop(0)
            for s in v.smoke:
                age = now - s[4]
                # מאט ומתרחב ככל שעולה - כמו ענן שמתפזר בגובה (מראה "פטרייה")
                rise = 30 * max(0.35, 1.0 - age / 3.2)
                s[1] -= rise * dt
                s[0] += s[2] * dt
                s[3] += (11 if age < 1.2 else 6) * dt
            v.smoke = [s for s in v.smoke if now - s[4] < 3.6]

            # ניצוצות זעירים שנורים מהלוע ועולים בתוך עמוד העשן, דועכים בגובה
            if random.random() < 0.55:
                ang = random.uniform(-0.5, 0.5) - math.pi / 2
                spd = random.uniform(30, 70)
                v.sparks.append([ccx + random.uniform(-6, 6), ccy - 4,
                                 math.cos(ang) * spd * 0.3, math.sin(ang) * spd, now])
            for sp in v.sparks:
                sp[0] += sp[2] * dt
                sp[1] += sp[3] * dt
                sp[3] += 46 * dt        # מאט את העלייה (כבידה) עד שדועך
            v.sparks = [sp for sp in v.sparks if now - sp[4] < 1.1]

            # פליטת גושי לבה
            if now >= v.next_erupt:
                v.next_erupt = now + VOLCANO_ERUPT_INTERVAL * random.uniform(0.6, 1.4)
                for _ in range(random.randint(2, 4)):
                    ang = random.uniform(0, math.tau)
                    rad = random.uniform(0.7, VOLCANO_RADIUS)
                    tr = int(round(v.row + math.sin(ang) * rad))
                    tc = int(round(v.col + math.cos(ang) * rad))
                    if not (1 <= tr < ROWS - 1 and 1 <= tc < COLS - 1):
                        continue
                    if self.grid[tr][tc] == WALL:
                        continue
                    v.embers.append([float(ccx), float(ccy),
                                     tc * TILE + TILE // 2, tr * TILE + top + TILE // 2,
                                     tr, tc, now])

            for e in list(v.embers):
                if now - e[6] >= VOLCANO_EMBER_FLIGHT:
                    v.embers.remove(e)
                    self._ignite(e[4], e[5])

        # לוגיקת הברֵכות: הלבה נשארת לצמיתות, מחסלת אויבים (בוסים נשרפים בהדרגה) ושורפת את השחקן
        if self.lava:
            for e in self.enemies:
                if e.alive and (e.row, e.col) in self.lava:
                    if e.max_hp > 1:
                        if now - e.last_lava_tick >= LAVA_TICK:
                            e.last_lava_tick = now
                            died = self.hit_enemy(e, 1)
                            if died:
                                self.award_kill(e, e.row, e.col, "burned!", LAVA_HOT)
                    else:
                        e.alive = False
                        self.award_kill(e, e.row, e.col, "burned!", LAVA_HOT)
            if (self.player.row, self.player.col) in self.lava:
                if now - self._last_lava_tick >= LAVA_TICK:
                    self._last_lava_tick = now
                    self.player.hit()
                    self.spawn_float(self.player.row, self.player.col, "-1", RED)

    def spawn_quake_cracks(self):
        """יוצר רשת סדקים פוליגונלית בסגנון "בוץ יבש" על פני כל הקרקע.

        נבנית סריג נקודות מטולטל (jitter), ובין שכנות מותחים קו סדק משונן -
        וכך נוצרים תאים סגורים לא-סדירים. חלק מהקשתות מושמט לאי-סדירות.
        הכול נצבר ל-self.crack_paths ונשאר עד סוף השלב.
        """
        top = 64
        paths = self.crack_paths
        base = len(paths)
        G = random.choice((44, 48, 52))          # גודל תא מבוקש
        jitter = G * 0.36
        ncols = WIDTH // G + 2
        nrows = (HEIGHT - top) // G + 2
        nodes = {}
        for i in range(nrows + 1):
            for j in range(ncols + 1):
                nodes[(i, j)] = (j * G + random.uniform(-jitter, jitter),
                                 top + i * G + random.uniform(-jitter, jitter))

        def add_edge(p, q):
            if random.random() < 0.10:            # תא פתוח פה ושם
                return
            major = random.random() < 0.24
            w = random.uniform(3.2, 5.0) if major else random.uniform(1.4, 2.8)
            (x1, y1), (x2, y2) = p, q
            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy) or 1.0
            nrx, nry = -dy / length, dx / length  # ניצב לקשת
            parts = random.randint(3, 6)
            pts = [(x1, y1)]
            for k in range(1, parts):
                t = k / parts
                bend = random.uniform(-G * 0.13, G * 0.13)
                slide = random.uniform(-0.06, 0.06)   # גם קצת לאורך, שלא ייצא סימטרי
                pts.append((x1 + dx * (t + slide) + nrx * bend,
                            y1 + dy * (t + slide) + nry * bend))
            pts.append((x2, y2))
            # זווית תאורה קבועה לכל הסדקים -> שפה מוארת עקבית באותו צד
            paths.append({"pts": pts, "w": w, "seed": random.uniform(0, 100.0)})

        # תקרה רכה - שלא ייהפך ללא-קריא אחרי המון רעידות באותו שלב
        if len(paths) < 1200:
            for i in range(nrows + 1):
                for j in range(ncols + 1):
                    if (i, j + 1) in nodes:
                        add_edge(nodes[(i, j)], nodes[(i, j + 1)])
                    if (i + 1, j) in nodes:
                        add_edge(nodes[(i, j)], nodes[(i + 1, j)])

        self._render_cracks()
        return len(paths) - base

    # כיוון "אור" גלובלי - הצד המואר של כל בקע (יחידה)
    _LIGHT_DIR = (-0.55, -0.83)
    _CRACK_SS = 3               # supersampling ל-anti-alias

    def _ribbon(self, pts, w, seed):
        """בונה מצולע 'סרט' משונן שעוקב אחרי הפוליליין, צר בקצוות ורחב באמצע."""
        n = len(pts)
        left, right = [], []
        for idx in range(n):
            px, py = pts[idx]
            ax, ay = pts[max(0, idx - 1)]
            bx, by = pts[min(n - 1, idx + 1)]
            tx, ty = bx - ax, by - ay
            tl = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / tl, tx / tl              # ניצב מקומי
            u = idx / (n - 1)
            taper = 0.30 + 0.70 * math.sin(u * math.pi) ** 0.6   # צר בקצוות
            wob = 1.0 + 0.42 * math.sin(u * 7.3 + seed) + 0.18 * math.sin(u * 19.0 + seed * 2)
            hw = max(0.5, 0.5 * w * taper * max(0.35, wob))
            left.append((px + nx * hw, py + ny * hw))
            right.append((px - nx * hw, py - ny * hw))
        return left + right[::-1], left, right

    def _render_cracks(self):
        """מוסיף את הסדקים החדשים לשכבת-העל ומכין crack_surface מוקטן ומוחלק."""
        SS = self._CRACK_SS
        if self.crack_big is None:
            self.crack_big = pygame.Surface((WIDTH * SS, HEIGHT * SS), pygame.SRCALPHA)
            self.crack_rendered = 0
        big = self.crack_big
        ldx, ldy = self._LIGHT_DIR

        for path in self.crack_paths[self.crack_rendered:]:
            pts = [(x * SS, y * SS) for x, y in path["pts"]]
            w = path["w"] * SS
            seed = path["seed"]
            poly, left, right = self._ribbon(pts, w, seed)

            # 1) הילת צל רכה (כמה שכבות מתרחבות, שקופות)
            for grow, a in ((3.4 * SS, 26), (2.0 * SS, 34), (0.9 * SS, 44)):
                spoly, _, _ = self._ribbon(pts, path["w"] * SS + grow, seed)
                pygame.draw.polygon(big, (*CRACK_SHADOW, a), spoly)

            # 2) דופן הבקע (חום) ואז הליבה הכהה מעט צרה יותר
            pygame.draw.polygon(big, (*CRACK_WALL, 255), poly)
            cpoly, _, _ = self._ribbon(pts, max(0.6, path["w"] * SS - 1.6 * SS), seed)
            pygame.draw.polygon(big, (*CRACK_LINE, 255), cpoly)

            # 3) שפה מוארת בצד שפונה ל"אור" (תחושת לוח מורם)
            lit = left if (left and right and
                           (left[len(left) // 2][0] - right[len(right) // 2][0]) * ldx +
                           (left[len(left) // 2][1] - right[len(right) // 2][1]) * ldy > 0) else right
            if len(lit) >= 2:
                pygame.draw.lines(big, (*CRACK_LIP, 110), False, lit, max(1, SS // 2))

        self.crack_rendered = len(self.crack_paths)
        self.crack_surface = pygame.transform.smoothscale(big, (WIDTH, HEIGHT))

    def explode_bomb(self, bomb):
        if bomb.area_radius is not None:
            cells = []
            R = bomb.area_radius
            for dr in range(-R, R + 1):
                for dc in range(-R, R + 1):
                    r, c = bomb.row + dr, bomb.col + dc
                    if r < 0 or c < 0 or r >= ROWS or c >= COLS:
                        continue
                    if self.grid[r][c] == WALL:
                        continue
                    if self.grid[r][c] == BRICK:
                        self.destroy_brick(r, c)
                    cells.append((r, c))
            self.explosions.append(Explosion(cells, (bomb.row, bomb.col),
                                             "hydro" if bomb.hydro else "atom"))
            self.add_shake(16 if bomb.hydro else 11, 0.5 if bomb.hydro else 0.4)
            for other in self.bombs:
                if other is not bomb and not other.exploded and (other.row, other.col) in cells:
                    other.exploded = True
                    self.explode_bomb(other)
            return

        cells = [(bomb.row, bomb.col)]
        for drow, dcol in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for step in range(1, bomb.power + 1):
                r, c = bomb.row + drow * step, bomb.col + dcol * step
                if r < 0 or c < 0 or r >= ROWS or c >= COLS:
                    break
                if self.grid[r][c] == WALL:
                    break
                cells.append((r, c))
                if self.grid[r][c] == BRICK:
                    self.destroy_brick(r, c)
                    break
        self.explosions.append(Explosion(cells, (bomb.row, bomb.col)))
        self.add_shake(7, 0.28)

        for other in self.bombs:
            if other is not bomb and not other.exploded and (other.row, other.col) in cells:
                other.exploded = True
                self.explode_bomb(other)

    def update_bombs(self):
        now = time.time()
        for bomb in list(self.bombs):
            if not bomb.exploded and now - bomb.placed_at >= BOMB_TIMER:
                bomb.exploded = True
                self.explode_bomb(bomb)
        self.bombs = [b for b in self.bombs if not b.exploded]

    def update_explosions(self):
        now = time.time()
        still_active = []
        for exp in self.explosions:
            age = now - exp.created_at
            if age < exp.duration:
                still_active.append(exp)
                if age < 0.35:
                    if (self.player.row, self.player.col) in exp.cells:
                        self.player.hit()
                    dmg = 3 if exp.kind == "hydro" else (2 if exp.kind == "atom" else 1)
                    for enemy in self.enemies:
                        if (enemy.alive and (enemy.row, enemy.col) in exp.cells
                                and id(enemy) not in exp.hit_enemies):
                            exp.hit_enemies.add(id(enemy))
                            died = self.hit_enemy(enemy, dmg)
                            r, c = enemy.row, enemy.col
                            if died:
                                exp.kills += 1
                                if enemy.kind == "boss":
                                    self.award_kill(enemy, r, c, "", (0, 0, 0))
                                else:
                                    gain = 100 * exp.kills   # קומבו: כל חיסול נוסף שווה יותר
                                    self.player.score += gain
                                    if exp.kills >= 2:
                                        self.spawn_float(r, c, f"COMBO x{exp.kills}  +{gain}", YELLOW)
                                        self.add_shake(9, 0.3)
                            elif enemy.kind == "boss":
                                self.spawn_float(r, c, f"-{dmg}", (255, 200, 120))
        self.explosions = still_active

    def spawn_float(self, row, col, text, color):
        top = 64
        x = col * TILE + TILE // 2
        y = row * TILE + top + TILE // 2
        self.float_texts.append(FloatText(x, y, text, color))

    def update_float_texts(self):
        now = time.time()
        self.float_texts = [f for f in self.float_texts
                            if now - f.created_at < f.duration]

    def update_enemies(self):
        now = time.time()
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            delay = enemy.move_delay if enemy.move_delay is not None else self.enemy_move_delay
            if now - enemy.last_move < delay:
                continue
            enemy.last_move = now
            if enemy.kind == "boss":
                self.move_boss(enemy)
            elif enemy.kind == "chaser":
                self.move_chaser(enemy)
            elif enemy.kind == "ghost":
                self.move_ghost(enemy)
            else:
                drow, dcol = enemy.direction
                if not self.try_move(enemy, drow, dcol):
                    options = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                    random.shuffle(options)
                    for d in options:
                        if self.try_move(enemy, d[0], d[1]):
                            enemy.direction = d
                            break

            if enemy.pos == self.player.pos:
                self.player.hit()

    def move_chaser(self, enemy):
        def sgn(x):
            return (x > 0) - (x < 0)

        dr = sgn(self.player.row - enemy.row)
        dc = sgn(self.player.col - enemy.col)
        if abs(self.player.row - enemy.row) > abs(self.player.col - enemy.col):
            prefs = [(dr, 0), (0, dc), (0, -dc), (-dr, 0)]
        else:
            prefs = [(0, dc), (dr, 0), (-dr, 0), (0, -dc)]
        for d in prefs:
            if d != (0, 0) and self.try_move(enemy, d[0], d[1]):
                enemy.direction = d
                return
        options = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(options)
        for d in options:
            if self.try_move(enemy, d[0], d[1]):
                enemy.direction = d
                return

    def move_ghost(self, enemy):
        # רודף את השחקן בחלק מהמהלכים, אחרת נסחף בכיוונו
        if random.random() < 0.55:
            self.move_chaser(enemy)
            return
        if not self.try_move(enemy, enemy.direction[0], enemy.direction[1]):
            options = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random.shuffle(options)
            for d in options:
                if self.try_move(enemy, d[0], d[1]):
                    enemy.direction = d
                    return

    def move_boss(self, enemy):
        """הבוס נע לאט אך נחוש לעבר השחקן, ומדי כמה שניות 'שואג' ומנפץ
        לבנים בסביבתו הקרובה כדי לפרוץ דרך מכשולים."""
        now = time.time()
        if now - enemy.last_roar > BOSS_ROAR_INTERVAL:
            enemy.last_roar = now
            smashed = False
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    r, c = enemy.row + dr, enemy.col + dc
                    if 0 <= r < ROWS and 0 <= c < COLS and self.grid[r][c] == BRICK:
                        self.destroy_brick(r, c)
                        smashed = True
            if smashed:
                self.spawn_float(enemy.row, enemy.col, "SMASH!", BOSS_ACCENT)
                self.add_shake(10, 0.25)
        self.move_chaser(enemy)

    def check_win_lose(self):
        if not self.player.alive:
            self.lost = True
            self.game_over = True
        elif all(not e.alive for e in self.enemies):
            if self.level < TOTAL_LEVELS:
                self.level_cleared = True
            else:
                self.win = True
            self.game_over = True
        elif time.time() - self.start_time > self.time_limit:
            self.lost = True
            self.game_over = True

    # ------------------------------------------------------------------
    # קלט
    # ------------------------------------------------------------------
    def handle_input(self):
        keys = pygame.key.get_pressed()
        now = time.time()
        self.player.moving = False
        if now - self.player.last_move >= PLAYER_SPEED_DELAY:
            moved = False
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.player.facing = (-1, 0)
                moved = self.try_move(self.player, -1, 0)
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.player.facing = (1, 0)
                moved = self.try_move(self.player, 1, 0)
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player.facing = (0, -1)
                moved = self.try_move(self.player, 0, -1)
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player.facing = (0, 1)
                moved = self.try_move(self.player, 0, 1)
            if moved:
                self.player.last_move = now
                self.player.moving = True

    # ------------------------------------------------------------------
    # ציור
    # ------------------------------------------------------------------
    def draw_grid(self):
        # רצפה+קירות+לבנים הם כמעט-סטטיים: מרונדרים פעם אחת לשכבות ומוצגים כ-blit.
        if self._terrain_dirty:
            self._rebuild_terrain()
        self.screen.blit(self._floor_cache, (0, 0))
        self.draw_quake_cracks()
        self.draw_lava()
        self.screen.blit(self._blocks_cache, (0, 0))
        self.draw_volcano_cones()

    def _rebuild_terrain(self):
        self._floor_cache = pygame.Surface((WIDTH, HEIGHT))
        self._blocks_cache = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        real = self.screen
        try:
            self.screen = self._floor_cache
            self.draw_floor()
            self.screen = self._blocks_cache
            self.draw_blocks()
        finally:
            self.screen = real
        self._terrain_dirty = False

    def draw_floor(self):
        top = 64
        for r in range(ROWS):
            for c in range(COLS):
                x, y = c * TILE, r * TILE + top
                floor_color = FLOOR_A if (r + c) % 2 == 0 else FLOOR_B
                pygame.draw.rect(self.screen, floor_color, (x, y, TILE, TILE))
                # קו גרוט עדין בין המשבצות - נותן תחושת ריצוף מוגדר
                pygame.draw.rect(self.screen, lerp_color(floor_color, BLACK, 0.14),
                                 (x, y, TILE, TILE), 1)
                # מרקם עדין וקבוע (זרעי RNG לפי המשבצת, כך שלא מרצד בין פריימים)
                rng = random.Random(r * 1000 + c)
                speck_light = lerp_color(floor_color, WHITE, 0.22)
                speck_dark = lerp_color(floor_color, BLACK, 0.18)
                for _ in range(3):
                    sx = x + rng.randint(6, TILE - 6)
                    sy = y + rng.randint(6, TILE - 6)
                    pygame.draw.circle(self.screen, speck_light, (sx, sy), 1)
                for _ in range(2):
                    sx = x + rng.randint(5, TILE - 5)
                    sy = y + rng.randint(5, TILE - 5)
                    pygame.draw.circle(self.screen, speck_dark, (sx, sy), 1)
        # ויניאטה עדינה בפינות הזירה לתחושת עומק (מחושבת פעם אחת ונשמרת)
        if self._floor_vignette is None:
            self._floor_vignette = self._build_vignette()
        self.screen.blit(self._floor_vignette, (0, top))

    def _build_vignette(self):
        fh = HEIGHT - 64
        surf = pygame.Surface((WIDTH, fh), pygame.SRCALPHA)
        cx, cy = WIDTH / 2, fh / 2
        maxd = math.hypot(cx, cy)
        step = 8
        for yy in range(0, fh, step):
            for xx in range(0, WIDTH, step):
                d = math.hypot(xx - cx, yy - cy) / maxd
                a = max(0, int((d - 0.55) * 150))
                if a > 0:
                    pygame.draw.rect(surf, (0, 0, 0, min(75, a)), (xx, yy, step, step))
        return surf

    def draw_quake_cracks(self):
        """מציג את שכבת הסדקים המוכנה (נשארת עד סוף השלב)."""
        if self.crack_surface is not None:
            self.screen.blit(self.crack_surface, (0, 0))

    def draw_blocks(self):
        top = 64
        for r in range(ROWS):
            for c in range(COLS):
                x, y = c * TILE, r * TILE + top
                tile = self.grid[r][c]
                if tile == WALL:
                    depth = 6
                    draw_shadow_ellipse(self.screen, x + TILE // 2, y + TILE - 4, TILE - 6, 8, alpha=55)
                    pygame.draw.rect(self.screen, WALL_SIDE, (x + 2, y + depth, TILE - 4, TILE - depth - 2), border_radius=4)
                    draw_vgradient(self.screen, (x + 2, y, TILE - 4, TILE - depth), lerp_color(WALL_TOP, WHITE, 0.15), WALL_TOP)
                    pygame.draw.rect(self.screen, WALL_LINE, (x + 2, y, TILE - 4, TILE - depth), 2, border_radius=3)
                    # פינות מוברגות (רוקדים) - תחושת בטון/מתכת תעשייתי
                    for bxs, bys in ((7, 7), (TILE - 7, 7), (7, TILE - depth - 6), (TILE - 7, TILE - depth - 6)):
                        bxp, byp = x + bxs, y + bys
                        pygame.draw.circle(self.screen, lerp_color(WALL_SIDE, BLACK, 0.35), (bxp, byp), 2)
                        pygame.draw.circle(self.screen, lerp_color(WALL_TOP, WHITE, 0.45), (bxp - 1, byp - 1), 1)
                elif tile == BRICK:
                    depth = 6
                    draw_shadow_ellipse(self.screen, x + TILE // 2, y + TILE - 3, TILE - 8, 7, alpha=50)
                    pygame.draw.rect(self.screen, BRICK_SIDE, (x + 3, y + depth, TILE - 6, TILE - depth - 3), border_radius=3)
                    draw_vgradient(self.screen, (x + 3, y + 2, TILE - 6, TILE - depth - 2), lerp_color(BRICK_TOP, WHITE, 0.1), BRICK_TOP)
                    mid = y + (TILE - depth) // 2 + 1
                    # שפה עליונה מוארת - תחושת בבל מחודד
                    pygame.draw.line(self.screen, lerp_color(BRICK_TOP, WHITE, 0.4), (x + 4, y + 3), (x + TILE - 4, y + 3), 1)
                    pygame.draw.line(self.screen, BRICK_LINE, (x + 3, mid), (x + TILE - 3, mid), 2)
                    pygame.draw.line(self.screen, BRICK_LINE, (x + TILE // 2, y + 2), (x + TILE // 2, mid), 2)
                    q1 = x + 3 + (TILE - 6) // 4
                    q3 = x + 3 + 3 * (TILE - 6) // 4
                    pygame.draw.line(self.screen, BRICK_LINE, (q1, mid), (q1, y + TILE - depth - 2), 1)
                    pygame.draw.line(self.screen, BRICK_LINE, (q3, mid), (q3, y + TILE - depth - 2), 1)

    def draw_bombs(self):
        top = 64
        now = time.time()
        for bomb in self.bombs:
            cx, cy = bomb.col * TILE + TILE // 2, bomb.row * TILE + top + TILE // 2
            t_left = max(0, BOMB_TIMER - (now - bomb.placed_at))
            pulse_speed = 6 if t_left > 0.6 else 14
            pulse = (math.sin(now * pulse_speed) + 1) / 2
            special = bomb.atom or bomb.hydro
            base = 0.42 if special else 0.32
            radius = int(TILE * base + pulse * (5 if special else 3))

            draw_shadow_ellipse(self.screen, cx, cy + radius - 2, radius * 2, radius, alpha=70)
            if bomb.hydro:
                core_color = (120, 60, 190)
            elif bomb.atom:
                core_color = (40, 120, 70)
            else:
                core_color = lerp_color((60, 60, 68), (10, 10, 14), 0.0)
            draw_vgradient_circle(self.screen, cx, cy, radius, core_color)
            pygame.draw.circle(self.screen, (255, 255, 255, 40), (cx - radius // 3, cy - radius // 3), max(2, radius // 4))
            if special:
                ring_color = (200, 120, 255) if bomb.hydro else GREEN
                ring_r = int(radius + 4 + pulse * 4)
                pygame.draw.circle(self.screen, ring_color, (cx, cy), ring_r, 2)
                label = "H" if bomb.hydro else "A"
                sign_font = self.small_font.render(label, True, (245, 240, 255))
                self.screen.blit(sign_font, sign_font.get_rect(center=(cx, cy)))

            fuse_x, fuse_y = cx + radius // 2, cy - radius
            pygame.draw.line(self.screen, (110, 70, 40), (cx, cy - radius + 2), (fuse_x, fuse_y - 6), 3)
            spark_color = ORANGE if int(now * 10) % 2 == 0 else YELLOW
            pygame.draw.circle(self.screen, spark_color, (fuse_x, fuse_y - 6), 4)
            # ניצוצות זעירים סביב ראש הפתיל (זרעי RNG שמתחלף כמה פעמים בשנייה)
            spark_rng = random.Random((id(bomb) ^ int(now * 14)) & 0xFFFFFFFF)
            for _ in range(2):
                ang = spark_rng.uniform(0, math.tau)
                dist = spark_rng.uniform(3, 8)
                exx = fuse_x + math.cos(ang) * dist
                eyy = fuse_y - 6 + math.sin(ang) * dist
                pygame.draw.circle(self.screen, (255, 214, 150), (int(exx), int(eyy)), 1)

            # טבעת אזהרה אדומה פועמת כשהפצצה קרובה להתפוצץ (לא לפצצות מיוחדות)
            if not special and t_left < 0.6:
                danger_t = 1.0 - (t_left / 0.6)
                warn_color = lerp_color(ORANGE, RED, danger_t)
                warn_r = int(radius + 3 + pulse * 4)
                pygame.draw.circle(self.screen, warn_color, (cx, cy), warn_r, 2)

    # שכבות הכוכב הקוצני בסגנון קומיקס: (יחס רדיוס חיצוני, יחס רדיוס פנימי, צבע)
    EXPLOSION_LAYERS = [
        (1.06, 0.58, (150, 20, 15)),    # קו דיו כהה
        (1.00, 0.55, (226, 42, 30)),    # אדום
        (0.84, 0.45, (255, 122, 18)),   # כתום
        (0.63, 0.34, (255, 216, 46)),   # צהוב
        (0.42, 0.30, (255, 255, 255)),  # לבן
    ]

    def draw_explosions(self):
        top = 64
        now = time.time()
        for exp in self.explosions:
            age = now - exp.created_at
            progress = min(1.0, age / exp.duration)
            # מגיע לגודל מלא ב-35% מהזמן, עם קפיצונת "pop", ואז דעיכה
            grow = 1.0 - (1.0 - min(progress / 0.35, 1.0)) ** 2
            pop = 1.0 + 0.07 * math.sin(min(progress, 0.5) / 0.5 * math.pi)
            alpha = 255 if progress < 0.65 else int(255 * (1.0 - (progress - 0.65) / 0.35))
            alpha = max(0, min(255, alpha))

            ccx = exp.center[1] * TILE + TILE // 2
            ccy = exp.center[0] * TILE + top + TILE // 2

            # רדיוס הכוכב מכסה את התא הרחוק ביותר בפיצוץ
            max_d = 0.0
            for (r, c) in exp.cells:
                px = c * TILE + TILE // 2
                py = r * TILE + top + TILE // 2
                max_d = max(max_d, math.hypot(px - ccx, py - ccy))
            R = (max_d + TILE * 0.78) * grow * pop
            if R < 4:
                continue

            spin = exp.spin + exp.spin_dir * age * 1.1
            n = exp.n_spikes
            jit = exp.spike_jit

            surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for r_out, r_in, col in self.EXPLOSION_LAYERS:
                pts = star_points(ccx, ccy, R * r_out, R * r_in, n, spin, jit)
                pygame.draw.polygon(surf, (*col, alpha), pts)
            # ליבה עגולה לבנה חלקה
            pygame.draw.circle(surf, (255, 255, 255, alpha), (ccx, ccy), int(R * 0.30))
            self.screen.blit(surf, (0, 0))

    def draw_float_texts(self):
        now = time.time()
        for f in self.float_texts:
            if not f.text:
                continue
            age = now - f.created_at
            t = age / f.duration
            alpha = max(0, min(255, int(255 * (1.0 - t))))
            surf = self.font.render(f.text, True, f.color)
            surf.set_alpha(alpha)
            rect = surf.get_rect(center=(f.x, int(f.y - 26 * t)))
            self.screen.blit(surf, rect)

    def apply_screen_shake(self):
        now = time.time()
        if now >= self.shake_until or self.shake_mag <= 0:
            self.shake_mag = 0.0
            return
        remaining = self.shake_until - now
        mag = self.shake_mag * min(1.0, remaining / 0.25)
        dx = int(random.uniform(-mag, mag))
        dy = int(random.uniform(-mag, mag))
        frame = self.screen.copy()
        self.screen.fill(BLACK)
        self.screen.blit(frame, (dx, dy))

    def draw_player(self):
        top = 64
        now = time.time()
        if now < self.player.invincible_until and int(now * 10) % 2 == 0:
            return
        cx = self.player.col * TILE + TILE // 2
        cy = self.player.row * TILE + top + TILE // 2
        bob = math.sin(now * 10) * 2 if self.player.moving else 0
        cy += int(bob)

        draw_shadow_ellipse(self.screen, cx, self.player.row * TILE + top + TILE - 6,
                            TILE - 8, 11, alpha=85)
        self.draw_tortoise(cx, cy, self.player.facing, self.player.moving, now)

    def draw_tortoise(self, cx, cy, facing, moving, now):
        """צב-תינוק חמוד: שריון עגלגל, ראש גדול ועיניים גדולות נוצצות + סומק."""
        dr, dc = facing
        scr = TILE // 2 - 4                         # רדיוס השריון (עגלגל)
        fx, fy = dc, dr                             # "קדימה"
        px, py = -dr, dc                            # ניצב (רוחב הפנים)
        wig = math.sin(now * 9) * 1.5 if moving else 0.0

        # --- רגליים קטנות ושמנמנות (מתחת לשריון) ---
        for lx_s, ly_s in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            diag = (lx_s * ly_s > 0)
            step = moving and ((int(now * 8) % 2 == 0) == diag)
            ext = 2 if step else 0
            lx = int(cx + lx_s * (scr * 0.74 + ext))
            ly = int(cy + ly_s * (scr * 0.72 + ext))
            pygame.draw.circle(self.screen, TURTLE_SKIN_DARK, (lx, ly), 5)
            pygame.draw.circle(self.screen, TURTLE_SKIN, (lx, ly), 4)
            pygame.draw.circle(self.screen, (250, 244, 224), (lx, ly - 1), 1)

        # --- זנב זעיר ---
        tx = int(cx - fx * (scr + 2)); ty = int(cy - fy * (scr + 2))
        pygame.draw.circle(self.screen, TURTLE_SKIN_DARK, (tx, ty), 4)
        pygame.draw.circle(self.screen, TURTLE_SKIN, (tx, ty), 3)

        # --- צוואר קצרצר שמחבר ראש לשריון ---
        nx = cx + fx * scr * 0.7; ny = cy + fy * scr * 0.7
        pygame.draw.line(self.screen, TURTLE_SKIN, (nx, ny),
                         (nx + fx * 9, ny + fy * 9), 9)

        # --- שריון עגלגל וכיפתי ---
        pygame.draw.circle(self.screen, SHELL_LINE, (cx, cy), scr + 2)
        pygame.draw.circle(self.screen, SHELL_DARK, (cx, cy), scr + 1)
        pygame.draw.circle(self.screen, SHELL_MID, (cx, cy), scr - 1)
        pygame.draw.circle(self.screen, SHELL_LIGHT, (int(cx - scr * 0.28),
                                                      int(cy - scr * 0.34)), int(scr * 0.62))

        def star_shape(scx, scy, r_out, r_in, col_fill, col_line, n=5, phase=-math.pi / 2):
            pts = []
            for k in range(n):
                a_out = phase + k / n * math.tau
                a_in = phase + (k + 0.5) / n * math.tau
                pts.append((scx + math.cos(a_out) * r_out, scy + math.sin(a_out) * r_out))
                pts.append((scx + math.cos(a_in) * r_in, scy + math.sin(a_in) * r_in))
            pygame.draw.polygon(self.screen, col_fill, pts)
            pygame.draw.polygon(self.screen, col_line, pts, 1)

        # --- כל השריון מכוסה בכוכבים, כמו רקמת כוכבים הודית מסורתית ---
        star_tw = (math.sin(now * 3.0) + 1) / 2

        # כוכב גדול ומרכזי, שמיני-קצוות
        star_shape(cx, cy - scr * 0.02, scr * 0.30, scr * 0.13, STAR_GOLD, SHELL_LINE, n=8)
        pygame.draw.circle(self.screen, (255, 255, 255, 120),
                           (int(cx - scr * 0.08), int(cy - scr * 0.14)), max(1, int(scr * 0.06)))

        # טבעת כוכבים בינוניים סביב המרכז, גוונים לסירוגין
        ring1 = 6
        for k in range(ring1):
            a = k / ring1 * math.tau + 0.35
            sx = cx + math.cos(a) * scr * 0.56
            sy = cy + math.sin(a) * scr * 0.56
            tone = STAR_GOLD if k % 2 == 0 else STAR_AMBER
            star_shape(sx, sy, scr * 0.19, scr * 0.085, tone, SHELL_LINE, n=6, phase=a)

        # טבעת כוכבים קטנים קרוב לשוליים - כך שכל השריון מתמלא בכוכבים עד הקצה
        ring2 = 10
        for k in range(ring2):
            a = k / ring2 * math.tau + 0.15
            sx = cx + math.cos(a) * scr * 0.83
            sy = cy + math.sin(a) * scr * 0.83
            tone = STAR_AMBER if k % 3 == 0 else lerp_color(STAR_GOLD, SHELL_LIGHT, 0.25)
            star_shape(sx, sy, scr * 0.115, scr * 0.05, tone, SHELL_LINE, n=5, phase=a)

        # נצנוץ קטן שנודד בין כוכבי הטבעת הפנימית
        pop_i = int(now * 2.0) % ring1
        pa = pop_i / ring1 * math.tau + 0.35
        psx = cx + math.cos(pa) * scr * 0.56
        psy = cy + math.sin(pa) * scr * 0.56
        pygame.draw.circle(self.screen, (255, 255, 255, int(190 * star_tw)), (int(psx), int(psy)), 1)

        # ברק על השריון (גלוס)
        gloss = pygame.Surface((scr * 2, scr * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(gloss, (255, 255, 255, 75),
                            (scr * 0.35, scr * 0.2, scr * 0.9, scr * 0.55))
        self.screen.blit(gloss, (cx - scr, cy - scr))

        # נצנצים קטנים ומנצנצים על השריון (מהבהבים חליפין)
        for k, (ox, oy) in enumerate(((-0.55, -0.55), (0.62, -0.18), (0.30, 0.62))):
            tw = (math.sin(now * 3.4 + k * 2.1) + 1) / 2
            if tw < 0.55:
                continue
            sx = int(cx + ox * scr)
            sy = int(cy + oy * scr)
            a = int(200 * (tw - 0.55) / 0.45)
            r = 2 if k != 1 else 1
            spark = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
            pygame.draw.line(spark, (*SPARKLE_WHITE, a), (0, r * 3), (r * 6, r * 3), 1)
            pygame.draw.line(spark, (*SPARKLE_WHITE, a), (r * 3, 0), (r * 3, r * 6), 1)
            pygame.draw.circle(spark, (*SPARKLE_WHITE, min(255, a + 40)), (r * 3, r * 3), r)
            self.screen.blit(spark, (sx - r * 3, sy - r * 3))

        # --- ראש גדול (פרופורציית תינוק, קצת יותר גדול ועגלגל לחמידות) ---
        hr = 13
        hx = int(cx + fx * (scr + hr - 4) + px * wig)
        hy = int(cy + fy * (scr + hr - 4) + py * wig)
        pygame.draw.circle(self.screen, TURTLE_SKIN_DARK, (hx, hy), hr + 1)
        pygame.draw.circle(self.screen, TURTLE_SKIN, (hx, hy), hr)
        pygame.draw.circle(self.screen, lerp_color(TURTLE_SKIN, WHITE, 0.28),
                           (int(hx - fx * 3), int(hy - fy * 3)), hr - 4)

        # --- כוכב קטן ונוצץ מעל הראש - נגיעת קסם ניטרלית, יציבה בלי קשר לכיוון הפנייה ---
        stx, sty = hx - 1, hy - hr - 3
        twinkle = (math.sin(now * 3.0) + 1) / 2
        star_r = 3.4 + twinkle * 1.2
        pygame.draw.line(self.screen, (*STAR_GOLD, int(140 + 80 * twinkle)),
                         (int(stx - star_r), int(sty)), (int(stx + star_r), int(sty)), 1)
        pygame.draw.line(self.screen, (*STAR_GOLD, int(140 + 80 * twinkle)),
                         (int(stx), int(sty - star_r)), (int(stx), int(sty + star_r)), 1)
        pygame.draw.circle(self.screen, STAR_GOLD_DARK, (int(stx), int(sty)), 2)
        pygame.draw.circle(self.screen, STAR_GOLD, (int(stx), int(sty)), 1)

        # סומק חמוד וטבעי בלחיים
        blush = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(blush, (*BLUSH_CORAL, 110), (7, 7), 5)
        pygame.draw.circle(blush, (*BLUSH_CORAL, 60), (7, 7), 6)
        for s in (-1, 1):
            bx = hx + px * 7.5 * s + fx * 3
            by = hy + py * 7.5 * s + fy * 3
            self.screen.blit(blush, (int(bx) - 7, int(by) - 7))

        # --- עיניים גדולות, נוצצות וחמודות - פשוטות וברורות גם בגודל קטן ---
        blink = moving and (int(now * 8) % 9 == 0)
        for s in (-1, 1):
            ex = hx + px * 4.7 * s + fx * 3.3
            ey = hy + py * 4.7 * s + fy * 3.3

            if blink:
                pygame.draw.line(self.screen, (90, 60, 40),
                                 (int(ex) - 3, int(ey)), (int(ex) + 3, int(ey)), 2)
                continue

            pygame.draw.circle(self.screen, (255, 255, 255, 70), (int(ex), int(ey)), 5)
            pygame.draw.circle(self.screen, WHITE, (int(ex), int(ey)), 4)
            pupx, pupy = int(ex + fx * 1.2), int(ey + fy * 1.2)
            pygame.draw.circle(self.screen, (60, 42, 78), (pupx, pupy), 3)
            pygame.draw.circle(self.screen, (24, 18, 22), (pupx, pupy), 2)
            # ניצוץ כפול - כוכבון גדול למעלה, נקודה קטנה למטה-נגדית
            pygame.draw.circle(self.screen, WHITE, (pupx - 1, pupy - 1), 1)
            pygame.draw.circle(self.screen, (255, 255, 255, 200), (pupx + 1, pupy + 1), 1)

            # ריס זעיר יחיד - נגיעה עדינה כלפי חוץ-מעלה, בלי לבלגן את העין
            pygame.draw.line(self.screen, (70, 48, 34),
                             (int(ex + px * s * 3.6), int(ey - 3.2)),
                             (int(ex + px * s * 5.6), int(ey - 5.4)), 1)

        # אף כפתור זעיר וחמוד
        nose_x = hx + fx * (hr * 0.62)
        nose_y = hy + fy * (hr * 0.62)
        pygame.draw.circle(self.screen, (110, 70, 44), (int(nose_x), int(nose_y)), 2)
        pygame.draw.circle(self.screen, lerp_color((110, 70, 44), WHITE, 0.4),
                           (int(nose_x - 0.6), int(nose_y - 0.6)), 1)

        # חיוך קטנטן בסגנון "w" - הכי חמוד שיש
        base = (hx + fx * (hr * 0.68), hy + fy * (hr * 0.68))
        dip = (px * 2.6, py * 2.6)
        w_pts = [
            (base[0] - px * 4 - fx * 1.5, base[1] - py * 4 - fy * 1.5),
            (base[0] - dip[0] + fx * 1.5, base[1] - dip[1] + fy * 1.5),
            (base[0] + fx * 2.4, base[1] + fy * 2.4),
            (base[0] + dip[0] + fx * 1.5, base[1] + dip[1] + fy * 1.5),
            (base[0] + px * 4 - fx * 1.5, base[1] + py * 4 - fy * 1.5),
        ]
        pygame.draw.lines(self.screen, (120, 74, 46), False,
                          [(int(x), int(y)) for x, y in w_pts], 2)

    def draw_enemies(self):
        top = 64
        now = time.time()
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            cx = enemy.col * TILE + TILE // 2
            cy = enemy.row * TILE + top + TILE // 2
            bob = math.sin(now * 6 + enemy.bob_phase) * 2
            cy_draw = cy + int(bob)

            if enemy.kind == "ghost":
                self.draw_ghost(cx, cy_draw, now, enemy.bob_phase)
                continue

            if enemy.kind == "boss":
                self.draw_boss(cx, cy_draw, enemy, now)
                continue

            draw_shadow_ellipse(self.screen, cx, enemy.row * TILE + top + TILE - 6, TILE - 12, 9, alpha=75)

            is_chaser = enemy.kind == "chaser"
            body_c = CHASER_BODY if is_chaser else ENEMY_BODY
            dark_c = CHASER_DARK if is_chaser else ENEMY_DARK

            body_r = TILE // 2 - 7
            pygame.draw.circle(self.screen, dark_c, (cx, cy_draw + 2), body_r)
            draw_vgradient_circle(self.screen, cx, cy_draw, body_r, body_c)

            for sign in (-1, 1):
                ex = cx + sign * 5
                ey = cy_draw - 2
                pygame.draw.circle(self.screen, ENEMY_EYE, (ex, ey), 4)
                blink = (int((now * 3 + enemy.bob_phase)) % 5 == 0)
                pygame.draw.circle(self.screen, (25, 20, 30), (ex, ey), 2 if not blink else 0)
                if is_chaser:
                    # גבות זועפות
                    pygame.draw.line(self.screen, (30, 15, 15),
                                     (ex - 4, ey - 5), (ex + 4, ey - 2), 2)

            if is_chaser:
                # קרניים כלפי מעלה
                for sign in (-1, 1):
                    base_x = cx + sign * (body_r - 3)
                    pygame.draw.polygon(self.screen, dark_c, [
                        (base_x, cy_draw - body_r + 3),
                        (base_x + sign * 6, cy_draw - body_r - 7),
                        (base_x + sign * 2, cy_draw - body_r + 4),
                    ])
            else:
                spike_len = 5
                for angle_deg in (200, 250, 290, 340):
                    a = math.radians(angle_deg)
                    sx = cx + math.cos(a) * body_r
                    sy = cy_draw + math.sin(a) * body_r
                    ex = cx + math.cos(a) * (body_r + spike_len)
                    ey = cy_draw + math.sin(a) * (body_r + spike_len)
                    pygame.draw.line(self.screen, dark_c, (sx, sy), (ex, ey), 3)

    def draw_ghost(self, cx, cy, now, phase):
        body_r = TILE // 2 - 6
        S = body_r * 2 + 8
        g = pygame.Surface((S, S * 2), pygame.SRCALPHA)
        gx = S // 2
        gy = body_r + 4

        # אחת לכ-2.4 שניות הרוח "נעלמת" לרגע וקשה לראות אותה
        cycle = (now * 0.42 + phase) % 1.0
        if cycle > 0.80:
            t = (cycle - 0.80) / 0.20
            vis = 1.0 - 0.82 * math.sin(t * math.pi)
        else:
            vis = 1.0
        alpha = int((140 + 40 * math.sin(now * 3 + phase)) * vis)
        alpha = max(12, min(255, alpha))

        # גוף: כיפה עגולה למעלה + חצאית גלית למטה
        pygame.draw.circle(g, (*GHOST_BODY, alpha), (gx, gy), body_r)
        pygame.draw.rect(g, (*GHOST_BODY, alpha), (gx - body_r, gy, body_r * 2, body_r))
        waves = 4
        step = (body_r * 2) / waves
        pts = [(gx - body_r, gy + body_r)]
        for i in range(waves + 1):
            x = gx - body_r + i * step
            dip = 7 if i % 2 == 0 else 0
            off = math.sin(now * 5 + phase + i) * 2
            pts.append((x, gy + body_r + dip + off))
        pts.append((gx + body_r, gy + body_r))
        pygame.draw.polygon(g, (*GHOST_BODY, alpha), pts)

        # מתאר עדין ועיניים חלולות
        pygame.draw.circle(g, (*GHOST_DARK, alpha), (gx, gy), body_r, 2)
        for sign in (-1, 1):
            pygame.draw.ellipse(g, (60, 90, 110, min(255, alpha + 60)),
                                (gx + sign * 5 - 3, gy - 4, 6, 9))

        self.screen.blit(g, (cx - gx, cy - gy))

    def draw_boss(self, cx, cy, enemy, now):
        """מפלצת בוס ענקית עם כתר קוצים בוערים, עיניים לוהטות ופס חיים."""
        top = 64
        draw_shadow_ellipse(self.screen, cx, enemy.row * TILE + top + TILE, TILE + 14, 13, alpha=95)

        body_r = TILE // 2 - 1
        flash = now < enemy.hit_flash_until
        body_c = WHITE if flash else BOSS_BODY
        dark_c = WHITE if flash else BOSS_DARK

        # כתר קוצים בוערים סביב הגוף
        for angle_deg in range(0, 360, 36):
            a = math.radians(angle_deg) + math.sin(now * 1.4) * 0.05
            sx = cx + math.cos(a) * (body_r - 3)
            sy = cy + math.sin(a) * (body_r - 3)
            ex = cx + math.cos(a) * (body_r + 10)
            ey = cy + math.sin(a) * (body_r + 10)
            pygame.draw.line(self.screen, WHITE if flash else BOSS_ACCENT, (sx, sy), (ex, ey), 4)
            pygame.draw.circle(self.screen, WHITE if flash else lerp_color(BOSS_ACCENT, YELLOW, 0.4),
                               (int(ex), int(ey)), 2)

        pygame.draw.circle(self.screen, dark_c, (cx, cy + 3), body_r)
        draw_vgradient_circle(self.screen, cx, cy, body_r, body_c)

        # עיניים בוערות ופועמות
        glow = (math.sin(now * 8) + 1) / 2
        for sign in (-1, 1):
            ex = cx + sign * 8
            ey = cy - 3
            pygame.draw.circle(self.screen, lerp_color((255, 120, 40), (255, 230, 120), glow), (ex, ey), 6)
            pygame.draw.circle(self.screen, (30, 10, 10), (ex, ey), 3)
            pygame.draw.line(self.screen, (25, 8, 8), (ex - 5, ey - 7), (ex + 5, ey - 3), 2)

        # פה זועם עם ניבים
        mouth_y = cy + body_r * 0.42
        pygame.draw.arc(self.screen, (25, 8, 8), (cx - 10, mouth_y - 6, 20, 14), math.pi, math.tau, 3)
        for sign in (-1, 1):
            fx0 = cx + sign * 6
            pygame.draw.polygon(self.screen, WHITE, [
                (fx0, mouth_y + 1), (fx0 + sign * 3, mouth_y + 1), (fx0, mouth_y + 6)])

        # פס חיים מעל הראש
        bar_w, bar_h = TILE + 8, 7
        bx0 = cx - bar_w // 2
        by0 = cy - body_r - 20
        pygame.draw.rect(self.screen, (18, 18, 22), (bx0 - 1, by0 - 1, bar_w + 2, bar_h + 2), border_radius=4)
        frac = max(0.0, enemy.hp / enemy.max_hp)
        fill_c = lerp_color(RED, GREEN, frac)
        if frac > 0:
            pygame.draw.rect(self.screen, fill_c, (bx0 + 1, by0 + 1, int((bar_w - 2) * frac), bar_h - 2), border_radius=3)
        pygame.draw.rect(self.screen, (10, 10, 14), (bx0 - 1, by0 - 1, bar_w + 2, bar_h + 2), 1, border_radius=4)
        boss_label = self.small_font.render("BOSS", True, WHITE)
        self.screen.blit(boss_label, boss_label.get_rect(center=(cx, by0 - 9)))

    def draw_tornado(self):
        t = self.tornado
        if t is None:
            return
        now = time.time()
        age = now - t.born
        life = age / TORNADO_LIFETIME
        fade = 1.0 if life < 0.82 else max(0.0, 1.0 - (life - 0.82) / 0.18)
        grow = min(1.0, age / 0.4)

        H = int(132 * grow)
        base_w, top_w = 16, 108
        SW, SH = top_w + 60, H + 80
        surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
        bx, by = SW // 2, SH - 30

        def sway_at(f):
            return math.sin(now * 7 + f * 4.5) * (3 + f * 18)

        # 1) גוף משפכי אטום-למחצה (מצולע מבסיס צר לראש רחב)
        left_pts, right_pts = [], []
        LAY = 18
        for i in range(LAY + 1):
            f = i / LAY
            ly = by - f * H
            hw = (base_w + f * (top_w - base_w)) / 2
            sway = sway_at(f)
            left_pts.append((bx - hw + sway, ly))
            right_pts.append((bx + hw + sway, ly))
        pygame.draw.polygon(surf, (128, 134, 142, int(150 * fade)),
                            left_pts + right_pts[::-1])

        # 2) פסי סחרור (אליפסות מתחלפות בהיר/כהה) - נותנים תחושת סיבוב
        for i in range(LAY):
            f = i / LAY
            ly = by - int(f * H)
            w = int(base_w + f * (top_w - base_w))
            h = int(6 + f * 16)
            sway = sway_at(f)
            phase = math.sin(t.spin * 3 + f * 4)
            bright = 220 if phase > 0 else 110
            a = int((190 if phase > 0 else 230) * fade * (0.55 + 0.45 * (1 - f)))
            pygame.draw.ellipse(surf, (bright, bright + 6, bright + 12, a),
                                (bx - w // 2 + sway, ly - h // 2, w, h), 4)

        # 3) רסיסים ועלים שנשאבים במעגל
        for base_a, rad, hf, sp in t.debris:
            aa = t.spin * (2.0 + sp) + base_a
            ry = by - hf * H
            rr = (8 + 34 * rad) * (0.4 + 0.6 * grow)
            dbx = bx + math.cos(aa) * rr + sway_at(hf)
            dby = ry + math.sin(aa) * rr * 0.42
            col = (92, 70, 50) if (int(aa) % 2) else (232, 236, 240)
            pygame.draw.circle(surf, (*col, int(240 * fade)), (int(dbx), int(dby)),
                               2 if rad < 0.65 else 3)

        # 4) ענן אבק מתפשט בבסיס
        pygame.draw.ellipse(surf, (200, 208, 212, int(130 * fade)),
                            (bx - 60, by - 14, 120, 32))
        pygame.draw.ellipse(surf, (150, 158, 164, int(160 * fade)),
                            (bx - 48, by - 10, 96, 24), 3)

        # לא לצייר מעל פס המידע העליון
        self.screen.set_clip((0, 64, WIDTH, HEIGHT - 64))
        self.screen.blit(surf, (int(t.x) - bx, int(t.y) - by))
        self.screen.set_clip(None)

    def draw_tsunami(self):
        top = 64
        fh = HEIGHT - top
        now = time.time()

        # שאריות מים על כל המפה שמתנקזות אחרי שהגל עבר (עם אדוות זוחלות)
        if self.flood_until > now:
            k = (self.flood_until - now) / 1.1
            ov = pygame.Surface((WIDTH, fh), pygame.SRCALPHA)
            ov.fill((*WATER_MID, int(70 * k)))
            for i in range(7):
                yy = int((i / 7 + (now * 0.12) % (1 / 7)) * fh)
                pygame.draw.line(ov, (*WATER_FOAM, int(26 * k)), (0, yy), (WIDTH, yy), 2)
            self.screen.blit(ov, (0, top))

        t = self.tsunami
        if t is None:
            return

        band = TSUNAMI_BAND
        surf = pygame.Surface((band, fh), pygame.SRCALPHA)
        face = band - 24                               # חזית הגל בתוך הסרט (גרסת "ימינה")

        def wob_at(y):
            return (math.sin(now * 5.5 + y * 0.045) * 15
                    + math.sin(now * 3.1 + y * 0.11) * 9
                    + math.sin(now * 12.0 - y * 0.23) * 4)

        edge = [(face + wob_at(y), y) for y in range(0, fh + 1, 4)]
        redge = edge[::-1]

        # 1) גוף המים - הגב הכי כהה, ואז רצועות בהירות והולכות לעבר החזית
        pygame.draw.polygon(surf, (*WATER_ABYSS, 250),
                            [(0, 0)] + edge + [(0, fh)])
        for depth, col in ((64, WATER_DEEP), (38, WATER_MID), (16, WATER_CREST)):
            ribbon = [(x - depth, y) for x, y in edge] + [(x, y) for x, y in redge]
            pygame.draw.polygon(surf, (*col, 255), ribbon)

        # 2) פסי אור אופקיים בגוף המים (תחושת זרימה)
        for i in range(9):
            yy = int((i / 9 + (now * 0.14) % (1 / 9)) * fh)
            xr = face + wob_at(yy) - 26
            pygame.draw.line(surf, (210, 240, 245, 55), (8, yy), (max(8, xr), yy), 2)

        # 3) הגלילה (barrel) - חלל כהה מתחת לשפה + שפת טורקיז מוארת
        curl = [(x - 20, y) for x, y in edge] + [(x - 5, y) for x, y in redge]
        pygame.draw.polygon(surf, (9, 44, 64, 150), curl)
        pygame.draw.aalines(surf, (*WATER_CREST, 255), False,
                            [(x - 4, y) for x, y in edge])

        # 4) קצף רך רב-שכבתי לאורך החזית
        for i in range(0, len(edge), 3):
            x, y = edge[i]
            churn = math.sin(now * 9 + i) * 4
            for rr, a in ((9, 60), (5, 120), (3, 235)):
                pygame.draw.circle(surf, (*WATER_FOAM, a), (int(x - 2 + churn), y), rr)
            if i % 6 == 0:                             # רסיסי קצף נשפכים אחורה
                pygame.draw.circle(surf, (*WATER_FOAM, 85),
                                   (int(x - random.uniform(12, 30)), y), 2)

        # 5) תרסיס שמותז קדימה מעל החזית
        for sx, sy, sp in t.spray:
            phase = (now * sp * 1.5 + sx * 9) % 1.0
            px = face + 4 + phase * 32
            py = sy * fh + math.sin(now * 5 + sx * 10) * 10 - phase * 8
            a = int(235 * (1.0 - phase) ** 1.5)
            pygame.draw.circle(surf, (*WATER_FOAM, a), (int(px), int(py)),
                               1 if sp < 1.0 else 2)

        # 6) צל שהגל מטיל על הקרקע לפניו (תחושת קיר מים גבוה)
        sh_w = 34
        shadow = pygame.Surface((sh_w, fh), pygame.SRCALPHA)
        for i in range(sh_w):
            pygame.draw.line(shadow, (8, 18, 28, int(80 * (1 - i / sh_w))),
                             (i, 0), (i, fh))

        fx = int(t.front)
        self.screen.set_clip((0, top, WIDTH, fh))
        if t.dir < 0:
            surf = pygame.transform.flip(surf, True, False)
            shadow = pygame.transform.flip(shadow, True, False)
            self.screen.blit(shadow, (fx - sh_w, top))
            self.screen.blit(surf, (fx - 24, top))
        else:
            self.screen.blit(shadow, (fx, top))
            self.screen.blit(surf, (fx - (band - 24), top))
        self.screen.set_clip(None)

    def draw_sandstorm(self):
        """קיר אבק ענק ומתגלגל - שכבות גושים כרוביתיים מהחזית הכהה ועד הגב הבהיר,
        עם כתר עננים שמתנשא מעל קו הקרקע (מכוסה אחר-כך ע"י ה-HUD כמו עשן ההר געש)."""
        now = time.time()

        # אבק דליל שנשאר תלוי באוויר אחרי מעבר הסופה, ומתפזר לאט
        if self.dust_until > now:
            top = 64
            fh = HEIGHT - top
            k = (self.dust_until - now) / 1.8
            ov = pygame.Surface((WIDTH, fh), pygame.SRCALPHA)
            ov.fill((*DUST_HAZE, int(55 * k)))
            self.screen.blit(ov, (0, top))

        t = self.sandstorm
        if t is None:
            return

        band = SANDSTORM_BAND
        fx = t.front
        d = t.dir
        OFF = 260                      # ריפוד מעל המסך לכתר הגבוה (מוסתר תחת ה-HUD)

        def wob(y):
            return (math.sin(now * 2.6 + y * 0.02) * 18
                    + math.sin(now * 1.4 + y * 0.05) * 26
                    + math.sin(now * 5.0 - y * 0.09) * 8)

        overlay = pygame.Surface((WIDTH, HEIGHT + OFF), pygame.SRCALPHA)

        # 1) גוף הקיר - המון גושי אבק חופפים, מהעמוקים בגב (בהירים, שקופים)
        #    ועד לחזית (כהים וצפופים) - מראה מתגלגל ותלת-ממדי
        for rx, ry, rr, phase, spd in t.chunks:
            dist_back = rx * band * 0.85
            x = fx - d * dist_back + wob(ry * HEIGHT) * (0.3 + rx * 0.5)
            y = ry * HEIGHT + math.sin(now * spd + phase) * 10
            radius = int(30 + rr * 36)
            tone = lerp_color(SAND_LIGHT, SAND_DARK, rx)
            alpha = int(120 + 90 * rx)
            pygame.draw.circle(overlay, (*tone, alpha), (int(x), int(OFF + y)), radius)

        # 2) כתר גושים שמתנשא גבוה מעל קו הקרקע - תחושת קיר ענק שממלא את השמיים
        for rx, ry, rr, phase in t.crown:
            dist_back = rx * band * 0.7
            x = fx - d * dist_back + wob(ry * 60) * 0.4
            y = -ry * 210 + math.sin(now * 1.6 + phase) * 16
            radius = int(34 + rr * 44)
            tone = lerp_color(SAND_MID, SAND_LIGHT, ry)
            alpha = int(60 + 50 * (1 - ry))
            pygame.draw.circle(overlay, (*tone, alpha), (int(x), int(OFF + y)), radius)

        # 3) קו אור זהוב שחודר את קיר האבק בקו החזית
        edge_pts = [(fx + d * 2 + wob(yy) * 0.4, OFF + yy) for yy in range(-180, HEIGHT, 8)]
        if len(edge_pts) >= 2:
            pygame.draw.lines(overlay, (*SAND_GLOW, 140), False, edge_pts, 4)

        # 4) גרגירי חול נסחפים לפני החזית, בכיוון התנועה
        for gx, gy, sp in t.grains:
            phase = (now * sp * 2.0 + gx * 11) % 1.0
            px = fx + d * (6 + phase * 50)
            py = gy * HEIGHT + math.sin(now * 6 + gx * 9) * 8
            a = int(190 * (1 - phase))
            length = 6 + int(6 * (1 - phase))
            pygame.draw.line(overlay, (*SAND_GLOW, a), (px, OFF + py), (px - d * length, OFF + py), 1)

        self.screen.blit(overlay, (0, -OFF))

    def draw_lava(self):
        """ברֵכות לבה קבועות שנוצרו מהר הגעש - זוהרות ומפעפעות."""
        if not self.lava:
            return
        top = 64
        now = time.time()
        if getattr(self, "_lava_glow", None) is None:
            gs = TILE + 22
            glow = pygame.Surface((gs, gs), pygame.SRCALPHA)
            for rr, aa in ((gs // 2, 26), (gs // 2 - 7, 46), (gs // 2 - 15, 74)):
                pygame.draw.circle(glow, (255, 120, 44, aa), (gs // 2, gs // 2), rr)
            self._lava_glow = glow
        gs = self._lava_glow.get_width()

        for (r, c) in self.lava:
            x, y = c * TILE, r * TILE + top
            cx, cy = x + TILE // 2, y + TILE // 2
            p = (math.sin(now * 3.5 + r * 1.7 + c * 2.3) + 1) / 2
            q = (math.sin(now * 6.0 + r * 3.1 - c * 1.3) + 1) / 2

            self.screen.blit(self._lava_glow, (cx - gs // 2, cy - gs // 2))
            # גוף מותך לא-סדיר (כמה עיגולים חופפים, קבועים לכל תא)
            for k in range(4):
                a = k * 1.9 + r + c
                ox = math.cos(a) * (TILE * 0.16)
                oy = math.sin(a) * (TILE * 0.16)
                pygame.draw.circle(self.screen,
                                   lerp_color(LAVA_MID, LAVA_HOT, 0.25 + 0.45 * p),
                                   (int(cx + ox), int(cy + oy)), int(TILE * 0.30))
            # ליבה בוהקת פועמת
            pygame.draw.circle(self.screen, lerp_color(LAVA_HOT, LAVA_CORE, q),
                               (cx, cy), int(TILE * 0.17 + p * 4))
            # פיסות קרום סלע שצפות על פני הלבה
            for k in range(3):
                a = k * 2.4 - r + c * 0.7
                px = cx + math.cos(a) * TILE * 0.28
                py = cy + math.sin(a) * TILE * 0.24
                pygame.draw.circle(self.screen, ROCK_CHAR, (int(px), int(py)), 3)
            # ניצוץ מתרומם
            ey = y + TILE - int((now * 45 + r * 13 + c * 7) % (TILE + 6))
            pygame.draw.circle(self.screen, LAVA_CORE,
                               (cx + int(math.sin(now * 3 + c) * 6), ey), 2)

    def draw_volcano_cones(self):
        """מצייר הר געש 'אמיתי' יותר: צללית סלעית משוננת, תאורה דו-צדדית,
        שכבות סלע (סטרטה), פיסורות לבה זוהרות במורד, לוע בוער עם קרטר,
        אבנים בבסיס והילת חום סביב הפסגה."""
        top = 64
        now = time.time()
        for v in self.volcanoes:
            cx = v.col * TILE + TILE // 2
            by = v.row * TILE + top + TILE + 6
            h = TILE * 2.05          # הר גבוה ודרמטי יותר
            base_w = TILE * 1.08
            peak_w = TILE * 0.06
            ay = by - h
            glow = (math.sin(now * 5) + 1) / 2
            bubble = (math.sin(now * 2.6) + 1) / 2

            # --- הילת חום עוצמתית סביב הפסגה (מגיבה לפעימת הלבה) - מאירה גם את העשן ---
            halo_w, halo_h = int(base_w * 6.4), int(h * 1.25)
            halo = pygame.Surface((halo_w, halo_h), pygame.SRCALPHA)
            for rr, aa in ((halo_w * 0.46, 20), (halo_w * 0.30, 34), (halo_w * 0.17, 60), (halo_w * 0.08, 90)):
                pygame.draw.ellipse(halo, (255, 128, 36, int(aa + 26 * glow)),
                                    (halo_w / 2 - rr, halo_h * 0.06, rr * 2, halo_h * 0.55))
            self.screen.blit(halo, (int(cx - halo_w / 2), int(ay - halo_h * 0.42)))

            # --- צללית הר משוננת וקבועה (שונה מעט בכל הר) ---
            n = len(v.left_jag)

            def side(jag, sign):
                pts = []
                for i in range(n):
                    f = i / n
                    width = base_w * (1 - f) + peak_w * f
                    jit = jag[i] * TILE * 0.10 * (1 - f * 0.7)
                    pts.append((cx + sign * width + jit, by - f * h))
                return pts

            left_pts = side(v.left_jag, -1)
            right_pts = side(v.right_jag, 1)
            peak = (cx + v.tilt * base_w, ay)
            silhouette = left_pts + [peak] + list(reversed(right_pts))

            # גוף ההר (צל בסיס כהה)
            pygame.draw.polygon(self.screen, ROCK_CHAR, silhouette)

            # פן מואר בצד שמאל - תחושת תלת-ממד ("אור" בא משמאל-מעלה)
            lit = left_pts + [peak, (cx, by)]
            pygame.draw.polygon(self.screen, ROCK_CHAR_LIGHT, lit)

            # --- שכבות סלע (סטרטה) משוננות לרוחב ההר ---
            for sf in v.strata:
                wgt = base_w * (1 - sf) + peak_w * sf
                yy = by - sf * h
                band_pts = []
                steps = 6
                for i in range(steps + 1):
                    fxr = -1 + 2 * i / steps
                    jitter = math.sin(sf * 41 + fxr * 5 + v.tilt * 9) * TILE * 0.05
                    band_pts.append((cx + fxr * wgt + jitter, yy + jitter * 0.4))
                col = lerp_color(ROCK_CHAR, ROCK_CHAR_LIGHT, 0.32)
                pygame.draw.lines(self.screen, col, False, band_pts, 1)

            # --- נהרות לבה זוהרים במורד ההר - כמה זרמים, חלקם עד הבסיס, פועמים ---
            for off, dirx, speed, flow_w in v.fissures:
                fpts = [(cx + v.tilt * base_w * off, by - off * h)]
                steps = 7
                for i in range(1, steps + 1):
                    f = off * (1 - i / (steps + 1))
                    if f <= 0.015:
                        break
                    wgt = (base_w * (1 - f) + peak_w * f) * dirx
                    wobble = math.sin(f * 22 + off * 9) * TILE * 0.03
                    fpts.append((cx + wgt * (i / steps) * 1.25 + wobble, by - f * h))
                pulse = (math.sin(now * speed * 3 + off * 8) + 1) / 2
                if len(fpts) >= 2:
                    # דופן כהה (אפר קריר) מתחת לזוהר, ואז ליבה זוהרת פועמת
                    pygame.draw.lines(self.screen, lerp_color(LAVA_DEEP, BLACK, 0.3),
                                      False, fpts, int(flow_w) + 2)
                    glow_col = lerp_color(LAVA_MID, LAVA_CORE, 0.30 + 0.55 * pulse)
                    pygame.draw.lines(self.screen, glow_col, False, fpts, max(1, int(flow_w)))
                    hot_col = lerp_color(LAVA_HOT, LAVA_CORE, 0.5 + 0.4 * pulse)
                    pygame.draw.lines(self.screen, hot_col, False, fpts, max(1, int(flow_w * 0.45)))

            # מתאר כהה עדין סביב קווי המתאר של ההר (מגדיר צורה)
            outline_col = lerp_color(ROCK_CHAR, BLACK, 0.45)
            pygame.draw.lines(self.screen, outline_col, False, left_pts + [peak], 2)
            pygame.draw.lines(self.screen, outline_col, False, [peak] + list(reversed(right_pts)), 2)

            # --- רברבה/אבנים מפוזרות בבסיס ---
            for dx, dy, rr in v.rubble:
                rx = cx + dx * base_w
                ry = by - dy * 3
                pygame.draw.circle(self.screen, lerp_color(ROCK_CHAR, BLACK, 0.15), (int(rx), int(ry) + 1), int(rr))
                pygame.draw.circle(self.screen, ROCK_CHAR_LIGHT, (int(rx) - 1, int(ry) - 1), max(1, int(rr * 0.55)))

            # --- לוע הר הגעש: קרטר אליפטי עם בריכת לבה בוערת ומבעבעת ---
            crater_w, crater_h = base_w * 0.60, base_w * 0.22
            crx, cry = cx + v.tilt * base_w * 0.4, ay + 2

            pygame.draw.ellipse(self.screen, lerp_color(ROCK_CHAR, BLACK, 0.3),
                                (crx - crater_w / 2, cry - crater_h / 2 + 3, crater_w, crater_h))
            for k in range(3):
                a = now * 1.7 + k * 2.1
                ox = math.cos(a) * crater_w * 0.14
                oy = math.sin(a) * crater_h * 0.14
                rr = crater_w * (0.20 + 0.05 * math.sin(now * 4 + k))
                pygame.draw.ellipse(self.screen, lerp_color(LAVA_MID, LAVA_HOT, 0.3 + 0.5 * bubble),
                                    (crx - rr / 2 + ox, cry - rr * 0.4 + oy, rr, rr * 0.75))
            pygame.draw.ellipse(self.screen, lerp_color(LAVA_HOT, LAVA_CORE, bubble),
                                (crx - crater_w * 0.22, cry - crater_h * 0.28, crater_w * 0.44, crater_h * 0.6))
            pygame.draw.ellipse(self.screen, lerp_color(ROCK_CHAR, BLACK, 0.15),
                                (crx - crater_w / 2, cry - crater_h / 2, crater_w, crater_h), 2)

    def draw_volcano_fx(self):
        now = time.time()
        top = 64
        for v in self.volcanoes:
            vent_y = v.row * TILE + top + TILE // 2 - 12
            # מסלקים סדר לפי גיל (הכי ישן/גבוה קודם) כך שענני עשן חדשים וזוהרים
            # מצוירים מעל הישנים - נותן תחושת עומק לעמוד המתרומם.
            for s in sorted(v.smoke, key=lambda s: -(now - s[4])):
                age = now - s[4]
                k = max(0.0, 1.0 - age / 3.6)
                if k <= 0:
                    continue
                # רעש קבוע לכל ענן-עשן (לפי זמן/מיקום הלידה) כדי שלא "יהבהב" בין פריימים
                rng = random.Random((int(s[4] * 977) ^ int(s[0] * 31) ^ int(s[1])) & 0xFFFFFFFF)
                d = int(s[3])
                if d <= 0:
                    continue
                # ככל שקרוב יותר לפתח (גובה נמוך יותר מעל הלוע) - מואר יותר מלמטה
                # ע"י זוהר הלבה, בדומה לענני אפר אמיתיים; גבוה יותר -> אפור-שחור כבד
                height_frac = max(0.0, min(1.0, (vent_y - s[1]) / (TILE * 5.2)))
                warm = max(0.0, 1.0 - height_frac * 1.4) * max(0.0, 1.0 - age / 1.6)
                base_col = lerp_color(SMOKE_DARK, (34, 30, 30), min(1.0, height_frac))
                col = lerp_color(base_col, LAVA_HOT, 0.55 * warm)
                pad = d * 3 + 10
                puff = pygame.Surface((pad, pad), pygame.SRCALPHA)
                pc = pad / 2
                for _ in range(4):
                    ox = rng.uniform(-d * 0.55, d * 0.55)
                    oy = rng.uniform(-d * 0.4, d * 0.4)
                    rr = max(1, int(d * rng.uniform(0.5, 0.88)))
                    pygame.draw.circle(puff, (*col, int(110 * k)), (int(pc + ox), int(pc + oy)), rr)
                # תחתית הענן זוהרת חם יותר מהזוהר של הלבה מתחת
                if warm > 0.05:
                    under = lerp_color(LAVA_HOT, LAVA_CORE, 0.3)
                    pygame.draw.circle(puff, (*under, int(90 * k * warm)),
                                       (int(pc), int(pc + d * 0.32)), max(1, int(d * 0.5)))
                highlight = lerp_color(col, WHITE, 0.22)
                pygame.draw.circle(puff, (*highlight, int(55 * k)),
                                   (int(pc), int(pc - d * 0.25)), max(1, int(d * 0.42)))
                self.screen.blit(puff, (int(s[0] - pc), int(s[1] - pc)))

            # ניצוצות עולים בתוך עמוד העשן - דועכים ומחווירים ככל שעולים גבוה
            for sp in v.sparks:
                age = now - sp[4]
                k = max(0.0, 1.0 - age / 1.1)
                if k <= 0:
                    continue
                col = lerp_color(LAVA_CORE, LAVA_HOT, min(1.0, age / 0.6))
                r = max(1, int(2.4 * k))
                spark_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
                pygame.draw.circle(spark_surf, (*LAVA_HOT, int(70 * k)), (r * 2, r * 2), r * 2)
                pygame.draw.circle(spark_surf, col, (r * 2, r * 2), r)
                self.screen.blit(spark_surf, (int(sp[0] - r * 2), int(sp[1] - r * 2)))

            for e in v.embers:
                f = max(0.0, min(1.0, (now - e[6]) / VOLCANO_EMBER_FLIGHT))
                x = e[0] + (e[2] - e[0]) * f
                y = e[1] + (e[3] - e[1]) * f - math.sin(f * math.pi) * 52
                S = 26
                fx_surf = pygame.Surface((S * 2, S * 2), pygame.SRCALPHA)
                # שובל דועך מאחורי גוש הלבה המעופף
                for tstep, a in ((0.18, 55), (0.11, 95), (0.05, 150)):
                    tf = max(0.0, f - tstep)
                    tx = e[0] + (e[2] - e[0]) * tf
                    ty = e[1] + (e[3] - e[1]) * tf - math.sin(tf * math.pi) * 52
                    pygame.draw.circle(fx_surf, (*LAVA_MID, a),
                                       (int(S + tx - x), int(S + ty - y)), 3)
                pygame.draw.circle(fx_surf, (*LAVA_HOT, 70), (S, S), 9)
                pygame.draw.circle(fx_surf, LAVA_MID, (S, S + 2), 5)
                pygame.draw.circle(fx_surf, LAVA_HOT, (S, S), 4)
                pygame.draw.circle(fx_surf, LAVA_CORE, (S - 1, S - 1), 2)
                self.screen.blit(fx_surf, (int(x) - S, int(y) - S))

    def draw_hud(self):
        draw_vgradient(self.screen, (0, 0, WIDTH, 64), lerp_color(PANEL_BG, WHITE, 0.05), PANEL_BG)
        pygame.draw.line(self.screen, (255, 255, 255, 30), (0, 0), (WIDTH, 0), 1)
        pygame.draw.line(self.screen, (10, 10, 16), (0, 64), (WIDTH, 64), 2)
        pygame.draw.line(self.screen, lerp_color(PANEL_BG, BLACK, 0.5), (0, 63), (WIDTH, 63), 1)

        heart_x = 14
        for i in range(3):
            color = DEEP_RED if i < self.player.lives else (60, 60, 68)
            self.draw_heart(heart_x + i * 26, 32, 9, color)

        def shadow_text(font, text, color, pos):
            sh = font.render(text, True, (0, 0, 0))
            sh.set_alpha(120)
            self.screen.blit(sh, (pos[0] + 1, pos[1] + 1))
            self.screen.blit(font.render(text, True, color), pos)

        remaining = max(0, int(self.time_limit - (time.time() - self.start_time)))
        time_color = RED if remaining < 20 else WHITE
        enemies_left = sum(1 for e in self.enemies if e.alive)

        shadow_text(self.font, f"Score {self.player.score}", WHITE, (WIDTH - 230, 12))
        shadow_text(self.font, f"Time {remaining}", time_color, (WIDTH - 400, 12))
        shadow_text(self.font, f"Enemies {enemies_left}", WHITE, (WIDTH - 560, 12))
        shadow_text(self.font, f"Level {self.level}/{TOTAL_LEVELS}", YELLOW, (150, 12))
        self.screen.blit(self.small_font.render(
            "SPACE / ENTER / SHIFT bombs", True, GREEN), (150, 40))

        # תגי יכולות מיוחדות (רעידה / טורנדו / צונאמי / הר געש) - עיגולים עם ספירה לאחור
        now = time.time()
        badges = [
            ("Q", self.earthquake_ready_at - now, ORANGE),
            ("T", self.tornado_ready_at - now, (150, 200, 235)),
            ("W", self.tsunami_ready_at - now, WATER_MID),
            ("S", self.sandstorm_ready_at - now, SAND_MID),
            ("V", self.volcano_ready_at - now, LAVA_HOT),
        ]
        bx = WIDTH - 30
        for letter, left, color in reversed(badges):
            self.draw_ability_badge(bx, 40, letter, left <= 0, left, color)
            bx -= 30

        # פס חיים קטן של הבוס בפינה (נוסף רק בשלב הבוס, כדי שגם אם הוא רחוק/מחוץ למסך
        # אפשר יהיה לעקוב אחרי כמה נותר לו)
        boss = next((e for e in self.enemies if e.alive and e.kind == "boss"), None)
        if boss is not None:
            bw, bh = 150, 10
            bx0, by0 = WIDTH // 2 - bw // 2, 44
            frac = max(0.0, boss.hp / boss.max_hp)
            pygame.draw.rect(self.screen, (18, 18, 22), (bx0 - 1, by0 - 1, bw + 2, bh + 2), border_radius=5)
            fill_c = lerp_color(RED, GREEN, frac)
            if frac > 0:
                pygame.draw.rect(self.screen, fill_c, (bx0 + 1, by0 + 1, int((bw - 2) * frac), bh - 2), border_radius=4)
            label = self.small_font.render("BOSS", True, WHITE)
            self.screen.blit(label, label.get_rect(midright=(bx0 - 6, by0 + bh // 2)))

    def draw_ability_badge(self, x, y, letter, ready, seconds_left, color):
        r = 12
        pygame.draw.circle(self.screen, (10, 10, 16), (x, y), r + 2)
        bg = color if ready else lerp_color(color, (34, 36, 44), 0.7)
        pygame.draw.circle(self.screen, bg, (x, y), r)
        if ready:
            pulse = (math.sin(time.time() * 6) + 1) / 2
            pygame.draw.circle(self.screen, WHITE, (x, y), int(r + 1 + pulse * 2), 1)
            label = letter
            tcolor = (30, 24, 16)
        else:
            label = str(max(0, int(seconds_left) + 1))
            tcolor = (225, 225, 230)
        txt = self.small_font.render(label, True, tcolor)
        self.screen.blit(txt, txt.get_rect(center=(x, y)))

    def draw_heart(self, x, y, size, color):
        r = size // 2
        pygame.draw.circle(self.screen, color, (x - r // 2, y - r // 3), r // 2 + 2)
        pygame.draw.circle(self.screen, color, (x + r // 2, y - r // 3), r // 2 + 2)
        points = [(x - size, y - r // 4), (x + size, y - r // 4), (x, y + size)]
        pygame.draw.polygon(self.screen, color, points)

    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 16, 190))
        self.screen.blit(overlay, (0, 0))
        if self.level_cleared:
            msg = f"LEVEL {self.level} COMPLETE"
            color = GREEN
            hint_msg = "Press SPACE for next level"
        elif self.win:
            msg = "YOU WIN!"
            color = GREEN
            hint_msg = "Press R to play again"
        else:
            msg = "GAME OVER"
            color = RED
            hint_msg = "Press R to restart"

        # רסיסי אור צפים עדינים ברקע - עוזרים לתחושת "חיות" של המסך הסטטי
        now = time.time()
        for i in range(26):
            seed = i * 977
            bx = seed % WIDTH
            speed = 18 + (seed % 34)
            by = HEIGHT - ((now * speed + seed) % (HEIGHT + 40))
            a = max(0, min(255, 55 + int(45 * math.sin(now * 2 + i))))
            pygame.draw.circle(self.screen, (*color, a), (int(bx), int(by)), 2)

        # פנל רך מסביב להודעה
        panel = pygame.Surface((380, 140), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*color, 26), panel.get_rect(), border_radius=20)
        pygame.draw.rect(panel, (*color, 170), panel.get_rect(), width=2, border_radius=20)
        self.screen.blit(panel, (WIDTH // 2 - 190, HEIGHT // 2 - 80))

        shadow = self.big_font.render(msg, True, (0, 0, 0))
        text = self.big_font.render(msg, True, color)
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
        self.screen.blit(shadow, (rect.x + 3, rect.y + 3))
        self.screen.blit(text, rect)
        hint = self.font.render(hint_msg, True, WHITE)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 34))
        self.screen.blit(hint, hint_rect)

    # ------------------------------------------------------------------
    # לולאה ראשית
    # ------------------------------------------------------------------
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE and self.level_cleared:
                        self.next_level()
                    elif event.key == pygame.K_SPACE and not self.game_over:
                        self.place_bomb()
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and not self.game_over:
                        self.place_atom_bomb()
                    elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT) and not self.game_over:
                        self.place_hydro_bomb()
                    elif event.key in (pygame.K_1, pygame.K_KP1) and not self.game_over:
                        self.trigger_earthquake()
                    elif event.key in (pygame.K_2, pygame.K_KP2) and not self.game_over:
                        self.trigger_tornado()
                    elif event.key in (pygame.K_3, pygame.K_KP3) and not self.game_over:
                        self.trigger_tsunami()
                    elif event.key in (pygame.K_4, pygame.K_KP4) and not self.game_over:
                        self.trigger_volcano()
                    elif event.key in (pygame.K_5, pygame.K_KP5) and not self.game_over:
                        self.trigger_sandstorm()
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset()

            if not self.game_over:
                self.handle_input()
                self.update_bombs()
                self.update_explosions()
                self.update_float_texts()
                self.update_tornado()
                self.update_tsunami()
                self.update_sandstorm()
                self.update_volcanoes()
                self.update_enemies()
                self.check_win_lose()
            else:
                # שהאסונות יסיימו את האנימציה שלהם גם אחרי סיום השלב
                self.update_tornado()
                self.update_tsunami()
                self.update_sandstorm()
                self.update_volcanoes()
                self.update_float_texts()

            self.screen.fill(BLACK)
            self.draw_grid()   # רצפה -> סדקים -> לבה -> קירות/לבנים -> לוע
            self.draw_bombs()
            self.draw_explosions()
            self.draw_player()
            self.draw_enemies()
            self.draw_tornado()
            self.draw_tsunami()
            self.draw_sandstorm()
            self.draw_volcano_fx()
            self.draw_float_texts()
            self.draw_hud()
            if self.game_over:
                self.draw_game_over()

            self.apply_screen_shake()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def draw_vgradient_circle(surface, cx, cy, radius, base_color):
    """מצייר עיגול עם גרדיאנט קל (בהיר למעלה, כהה למטה) לתחושת נפח."""
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    top = lerp_color(base_color, WHITE, 0.35)
    bottom = lerp_color(base_color, BLACK, 0.25)
    for i in range(radius * 2):
        t = i / max(radius * 2 - 1, 1)
        color = lerp_color(top, bottom, t)
        pygame.draw.line(surf, color, (0, i), (radius * 2, i))
    mask = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surface.blit(surf, (cx - radius, cy - radius))


if __name__ == "__main__":
    Game().run()