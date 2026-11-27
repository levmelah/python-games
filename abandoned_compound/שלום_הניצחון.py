"""
משחק "המתחם הנטוש" - גרסת גוף ראשון (First Person, Raycasting)
==================================================================
עכשיו אתה רואה את המבוך מעיניו של השחקן, כמו במשחקי אימה קלאסיים!

שליטה:
  W / חץ למעלה     - התקדמות
  S / חץ למטה      - נסיגה
  A / חץ שמאלה     - סיבוב שמאלה
  D / חץ ימינה     - סיבוב ימינה
  Q                - צעד צד שמאלה (Strafe)
  E                - צעד צד ימינה (Strafe)
  קליק שמאלי עכבר   - ירי (לא עושה למפלצת שום נזק - רק המון דם)
  1                - החזקה מדליקה פנס חזק במיוחד (טווח וחוזק תאורה מוגברים)
  Enter            - כניסה / יציאה מארון מחבוא (כשעומדים מול הארון) / לקחת את המצלמה
  Shift            - לצלם (אחרי שלקחת את המצלמה מחדר הבקרה)

מחבואים: ארונות עץ מפוזרים בקצוות מבוי סתום. כשתתחבא -
         הוא יאבד את העקבות, יחפש באזור שבו ראה אותך לאחרונה, ובסוף יחזור לישון במאורה.
         בתוך הארון אתה בטוח - אבל כשתצא, אם הוא עדיין בסביבה וראה אותך, המרדף מתחיל מחדש.

מטרה: למצוא את היומן בחדר הפתוח הקטן שמוסתר במבוך, ורק אז להגיע לדלת היציאה.
       הדלת נפתחת כשמתקרבים אליה, ומאחוריה חדר המצלמות - משם רואים מקומות שונים במבוך.
       אם תיכנס בלי היומן - "לא הצלחת במשימה" ותצטרך להתחיל מחדש!
       בחדר המצלמות: לחיצה על מסך מגדילה אותו, לחיצה נוספת מחזירה.
       כל זאת תוך הימנעות מ"השומר" - הוא ישן עד שהפנס שלך מאיר עליו!

לחיצה על R לאחר Game Over / ניצחון - התחלה מחדש
לחיצה על ESC - יציאה

הערה: משחק מקורי - לא שכפול של דמויות או מיתוג מכל משחק קיים.
"""

import pygame
import random
import math
import sys
import os
import wave
import array
from collections import deque

try:
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False


def rtl(text):
    """מתקן כיווניות טקסט עברי לתצוגה נכונה ב-pygame (שלא תומך RTL באופן טבעי).
    דורש: pip install python-bidi
    אם הספרייה לא מותקנת, הטקסט יוצג הפוך (fallback לניסיון פשוט)."""
    if HAS_BIDI:
        return get_display(text)
    # בלי הספרייה: הופכים את הסדר, אבל מילים באנגלית ומספרים (Enter, Shift, 03:22) נשארים
    # כמו שהם, וסוגריים מתהפכים - כך שגם טקסט מעורב נראה נכון
    import re
    mirror = {"(": ")", ")": "(", "[": "]", "]": "[", "<": ">", ">": "<"}
    parts = re.split(r"([A-Za-z0-9][A-Za-z0-9/:.]*[A-Za-z0-9]|[A-Za-z0-9])", text)
    out = []
    for i, part in enumerate(reversed(parts)):
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9/:.]*[A-Za-z0-9]|[A-Za-z0-9]", part or "-"):
            out.append(part)
        else:
            out.append("".join(mirror.get(ch, ch) for ch in reversed(part)))
    return "".join(out)

# ------------------------------
# הגדרות כלליות
# ------------------------------
TEST_NO_MONSTER = True    # מצב בדיקה: True = אין מפלצת בכלל (לא מתעוררת, לא נראית, לא תופסת)
TEST_ENDING_ONLY = True   # מצב בדיקה: True = המשחק מתחיל ישר בסוף (ניצחון -> כעבור חודש -> עיתון)
WIDTH, HEIGHT = 900, 600
CELL = 64
COLS = 29
ROWS = 23

FPS = 60
MOVE_SPEED = 2.6
ROT_SPEED = 0.045
LIGHT_RADIUS = 7.5 * CELL  # טווח הפנס (במרחק פיקסלים אמיתי, לא תאים) - הוקטן = חשוך ומאיים יותר
LIGHT_BOOST_MULTIPLIER = 2.6  # כמה חזק הפנס כשלוחצים 1
LIGHT_BOOST_WAKE_TIME = 1.5   # שניות של החזקה רציפה עד שהאור החזק מעיר את השומר בכפייה
NUM_KEYS = 5
CATCH_DISTANCE = 24
FORCED_TURN_DISTANCE = 110  # מרחק שבו השחקן מאבד שליטה ומסתובב אוטומטית אל המפלצת
FORCED_TURN_SPEED = 0.09    # מהירות הסיבוב הכפוי (יותר מהיר מסיבוב רגיל)
FORCED_TURN_KILL_TIME = 4.0  # שניות עד שהמפלצת תוקפת אחרי שהשחקן קפוא ומביט בה
NOTE_TEXT = "תברח!!!"       # הטקסט שכתוב בדם על הפתקים המפוזרים במבוך
NOTE_COLOR = (150, 12, 14)    # צבע הדם על הפתקים
NUM_NOTES = 6                  # כמה פתקים מפוזרים במבוך
JUMPSCARE_DURATION = 0.9     # משך אנימציית הטריפה
MONSTER_HEIGHT = 0.97        # גובה השומר ביחס לתקרה - כמעט נוגע בה

# דלת היציאה וחדר המצלמות
DOOR_OPEN_DIST = 1.7 * CELL   # מאיזה מרחק הדלת נפתחת לבד
DOOR_OPEN_SPEED = 1.3         # מהירות הפתיחה (חלק מפתיחה מלאה בשנייה)
DOOR_FRAMES = 12              # כמה שלבי אנימציה לדלת הנפתחת
ENTER_FADE = 0.9              # משך המעבר לשחור כשנכנסים בדלת
NUM_CAMERAS = 6               # כמה מסכי מצלמה בחדר
CAM_FEED_SIZE = (206, 130)    # גודל כל מסך קטן
ROOM_COLS, ROOM_ROWS = 5, 6   # חדר הבקרה: 3x4 תאים פנימיים + קירות
ROOM_LIGHT_RADIUS = 10 * CELL # החדר מואר בפלורסנט - כמעט אחיד
NEAR_PLANE = 1.5              # חיתוך פוליגונים קרובים מדי למצלמה
MONITOR_USE_DIST = 2.3 * CELL # מאיזה מרחק אפשר ללחוץ על מסך כדי להגדיל
CAMERA_TAKE_DIST = 1.5 * CELL # מאיזה מרחק אפשר לקחת את המצלמה מהשולחן
# הטקסט בעמוד היומן - כל פסקה בשורה משלה. פסקאות שמתחילות ב-"!" מודגשות באדום
# סוף המשחק: ניצחון -> הכל נעלם -> "כעבור חודש..." -> עיתון
END_WIN_TIME = 5.5        # כמה זמן מוצג מסך הניצחון
END_FADE_TIME = 1.5       # הכל נעלם לשחור
END_MONTH_TIME = 3.5      # "כעבור חודש..."
END_PAPER_SPIN = 1.6      # העיתון מסתובב ונכנס למסך
PHOTO_WIN_DELAY = 1.8     # כמה שניות מסתכלים על התמונה בחדר עד הניצחון

JOURNAL_PAGE_TEXT = [
    "יצרתי משהו שיכול להשמיד את העולם.",
    "ואם מישהו מצא את היומן - יש לי מסר:",
    "אי אפשר להשמיד אותו.",
    "!יש לו רק נקודת חולשה אחת -",
    "!העין השמאלית.",
]
CAM_LIGHT_RADIUS = 11 * CELL  # המצלמות "רואות" רחוק יותר מהפנס שלך

# מקומות מחבוא (ארונות)
NUM_HIDING_SPOTS = 7          # כמה ארונות מפוזרים במבוך
HIDE_REACH = 46               # מרחק (פיקסלים) מחזית הארון שממנו אפשר להיכנס אליו
CLOSET_DEPTH = 0.42           # עומק הארון (חלק מתא) - קופסה תלת-ממדית שצמודה לקיר
CLOSET_WIDTH = 0.62           # רוחב הארון (חלק מתא)
CLOSET_HEIGHT = 0.92         # גובה הארון ביחס לגובה הקיר
HIDDEN_LIGHT_FACTOR = 0.55    # בתוך הארון הפנס מעומעם - רואים רק דרך החרכים
SIGHT_RANGE = 8 * CELL        # טווח הראייה של השומר כשהוא ער (דרוש גם קו ראייה פתוח)
SEARCH_DURATION = 7.0         # כמה שניות השומר מחפש אחרי שאיבד אותך, לפני שחוזר למאורה
MONSTER_SLOW_SPEED = 1.2      # מהירות השומר כשהוא מחפש / חוזר לישון

STORY_TEXT = (
    "פעם חי מדען שהחליט ליצור לעצמו מפלצת מחמד, והוא הצליח. "
    "אבל בניסוי הייתה טעות, והמפלצת יצאה מכלל שליטה. "
    "מאז לא ראו את המדען. "
    "עלייך לחקור הכל על המפלצת במעבדה כשהיא ישנה - אבל תיזהר לא להעיר אותה. "
    "אנחנו ניתן לך מפה, אבל לא רואים עליה את המפלצת כשהיא ישנה. "
    "חפש את היומן של המדען - הוא מוסתר בחדר קטן במעבדה, ובלעדיו כל המשימה לשווא. "
    "ורק אחרי שתמצא אותו - צא מהמעבדה."
)

FOV = math.pi / 3  # 60 מעלות
NUM_RAYS = 300
MAX_DEPTH = 20 * CELL
STRIP_WIDTH = WIDTH // NUM_RAYS

SHAKE_DISTANCE = 6.3 * CELL  # מרחק שממנו דופק הלב על המסך מתחיל להופיע ולהתחזק

# צבעים
BLACK = (2, 2, 4)
DARK = (7, 6, 9)
CEIL_COLOR = (4, 3, 6)
FLOOR_COLOR = (6, 5, 7)
WALL_BASE = (46, 30, 55)
BLOOD_DECAL = (55, 6, 10)
KEY_COLOR = (250, 210, 60)
DOOR_COLOR = (90, 220, 140)
DOOR_LOCKED_COLOR = (90, 90, 90)
MONSTER_AWAKE = (220, 40, 60)
MONSTER_ASLEEP = (100, 80, 100)
WHITE = (240, 240, 240)
RED = (220, 60, 60)
GREEN = (90, 220, 140)
MINIMAP_BG = (0, 0, 0)

WHISPER_LINES = [
    "...הוא רואה אותך...",
    "...אל תסתכל אחורה...",
    "...זה כבר קרוב...",
    "...למה באת לפה...",
    "...אתה לא לבד כאן...",
    "...תברח, עכשיו...",
    "...הוא זוכר אותך...",
    "...אתה שומע את זה?...",
    "...מאחוריך...",
    "...תפסיק לנשום ככה...",
    "...אני רואה אותך מסתתר...",
    "...כולם נעלמו פה...",
    "...זה לא יגמר בשבילך...",
    "...הוא כבר טעם דם היום...",
    "...אל תעצום עיניים...",
    "...אתה שומע את הצעדים?...",
    "...קר לך? זה הוא...",
    "...תמשיך לזוז, אל תעצור...",
    "...הוא אוהב כשמפחדים...",
    "...זה כבר מאוחר מדי...",
]


def generate_maze(cols, rows, extra_connections_ratio=0.3):
    grid = [[1 for _ in range(cols)] for _ in range(rows)]

    def neighbors(cx, cy):
        dirs = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(dirs)
        result = []
        for dx, dy in dirs:
            nx, ny = cx + dx, cy + dy
            if 1 <= nx < cols - 1 and 1 <= ny < rows - 1:
                result.append((nx, ny, dx, dy))
        return result

    grid[1][1] = 0
    stack = [(1, 1)]
    while stack:
        cx, cy = stack[-1]
        moved = False
        for nx, ny, dx, dy in neighbors(cx, cy):
            if grid[ny][nx] == 1:
                grid[cy + dy // 2][cx + dx // 2] = 0
                grid[ny][nx] = 0
                stack.append((nx, ny))
                moved = True
                break
        if not moved:
            stack.pop()

    # שלב שני - פתיחת קירות נוספים כדי ליצור לולאות ומסלולים חלופיים במבוך.
    # במבוך "מושלם" (DFS) יש בדיוק מסלול אחד בין כל שתי נקודות - זה אומר שאם
    # המפלצת חוסמת את הדרך אין ברירה אלא ללכת ישר אליה. פה שוברים קירות
    # "מיותרים" (בין שני תאים פתוחים) כדי לתת לשחקן אפשרויות בריחה אמיתיות.
    wall_candidates = []
    for row in range(1, rows - 1):
        for col in range(1, cols - 1):
            if grid[row][col] != 1:
                continue
            # קיר אנכי בין שני תאים פתוחים לרוחב
            if col - 1 >= 1 and col + 1 < cols - 1 and grid[row][col - 1] == 0 and grid[row][col + 1] == 0:
                wall_candidates.append((row, col))
            # קיר אופקי בין שני תאים פתוחים לגובה
            elif row - 1 >= 1 and row + 1 < rows - 1 and grid[row - 1][col] == 0 and grid[row + 1][col] == 0:
                wall_candidates.append((row, col))

    random.shuffle(wall_candidates)
    num_to_open = int(len(wall_candidates) * extra_connections_ratio)
    for row, col in wall_candidates[:num_to_open]:
        grid[row][col] = 0

    return grid


def is_wall(grid, x, y):
    col, row = int(x // CELL), int(y // CELL)
    if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[0]):
        return True
    return grid[row][col] == 1


def _ray_box(ox, oy, dx, dy, box):
    """חיתוך קרן עם קופסה (AABB) במישור. מחזיר (מרחק, ציר הפאה, מיקום על הפאה 0..1) או None.
    ציר 0 = פאה שהנורמל שלה בכיוון x, ציר 1 = בכיוון y."""
    x0, y0, x1, y1 = box
    tmin, tmax = -1e30, 1e30
    axis = 0
    if abs(dx) < 1e-9:
        if ox < x0 or ox > x1:
            return None
    else:
        tx0, tx1 = (x0 - ox) / dx, (x1 - ox) / dx
        if tx0 > tx1:
            tx0, tx1 = tx1, tx0
        tmin, tmax = tx0, tx1
    if abs(dy) < 1e-9:
        if oy < y0 or oy > y1:
            return None
    else:
        ty0, ty1 = (y0 - oy) / dy, (y1 - oy) / dy
        if ty0 > ty1:
            ty0, ty1 = ty1, ty0
        if ty0 > tmin:
            tmin, axis = ty0, 1
        tmax = min(tmax, ty1)
    if tmax < tmin or tmin <= 0:
        return None
    if axis == 0:
        u = (oy + dy * tmin - y0) / (y1 - y0)
    else:
        u = (ox + dx * tmin - x0) / (x1 - x0)
    return tmin, axis, u


def line_of_sight(grid, x1, y1, x2, y2, step=8):
    """בודק אם יש קו ראייה פתוח (בלי קירות) בין שתי נקודות - דגימה כל כמה פיקסלים"""
    dist = math.hypot(x2 - x1, y2 - y1)
    n = int(dist / step) + 1
    for i in range(1, n):
        t = i / n
        if is_wall(grid, x1 + (x2 - x1) * t, y1 + (y2 - y1) * t):
            return False
    return True


# ------------------------------
# מרקמים פרוצדורליים לקירות (נוצרים פעם אחת בעליית המשחק)
# ------------------------------
TEX_SIZE = 64


def _make_wall_texture(kind, seed):
    """בונה מרקם אבן/לבנים 64x64 שאפשר לחזור עליו אופקית. kind: brick / blood / crack"""
    rng = random.Random(seed)
    tex = pygame.Surface((TEX_SIZE, TEX_SIZE))
    tex.fill((30, 23, 36))  # צבע המישק (הטיח בין הלבנים)
    brick_h, brick_w = 16, 32
    mortar = 2
    for row in range(TEX_SIZE // brick_h):
        offset = brick_w // 2 if row % 2 else 0
        for k in range(TEX_SIZE // brick_w):
            tone = rng.uniform(0.80, 1.14)
            base = (int(106 * tone), int(78 * tone), int(120 * tone))
            x0 = k * brick_w + offset
            y0 = row * brick_h
            for wrap in (-TEX_SIZE, 0, TEX_SIZE):  # עטיפה אופקית כדי שלא יהיה תפר
                rect = pygame.Rect(x0 + wrap + mortar // 2, y0 + mortar // 2,
                                   brick_w - mortar, brick_h - mortar)
                tex.fill(base, rect.clip(tex.get_rect()))
                # הדגשה עליונה וצל תחתון - נותן תחושת נפח ללבנה
                top = pygame.Rect(rect.x, rect.y, rect.w, 1).clip(tex.get_rect())
                bot = pygame.Rect(rect.x, rect.bottom - 1, rect.w, 1).clip(tex.get_rect())
                tex.fill(tuple(min(255, int(c * 1.25)) for c in base), top)
                tex.fill(tuple(int(c * 0.7) for c in base), bot)

    # רעש עדין לכל פיקסל - מרקם אבן מחוספס
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            r, g, b = tex.get_at((x, y))[:3]
            n = rng.randint(-11, 11)
            tex.set_at((x, y), (max(0, min(255, r + n)), max(0, min(255, g + n)),
                                max(0, min(255, b + n))))

    # כתמי רטיבות/עובש כהים אקראיים
    for _ in range(5):
        wx, wy = rng.randint(0, TEX_SIZE - 1), rng.randint(0, TEX_SIZE - 1)
        blob = pygame.Surface((22, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(blob, (10, 8, 14, 60), blob.get_rect())
        tex.blit(blob, (wx - 11, wy - 8))

    if kind == "blood":
        for _ in range(rng.randint(3, 5)):
            x = rng.randint(4, TEX_SIZE - 5)
            length = rng.randint(14, 54)
            width = rng.choice((2, 3, 3, 4))
            pygame.draw.line(tex, (118, 8, 12), (x, 0), (x, length), width)
            pygame.draw.line(tex, (170, 18, 20), (x - 1, 0), (x - 1, length * 0.6), 1)
            pygame.draw.circle(tex, (96, 6, 10), (x, length), width // 2 + 1)
        splat = pygame.Surface((30, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(splat, (110, 6, 10, 170), splat.get_rect())
        tex.blit(splat, (rng.randint(4, 30), rng.randint(14, 36)))
    elif kind == "crack":
        x, y = rng.randint(14, 50), 0
        points = [(x, y)]
        while y < TEX_SIZE:
            x += rng.randint(-5, 5)
            y += rng.randint(5, 10)
            points.append((x, y))
        pygame.draw.lines(tex, (12, 8, 16), False, points, 2)
        bx, by = points[len(points) // 2]
        pygame.draw.lines(tex, (12, 8, 16), False,
                          [(bx, by), (bx + rng.randint(8, 16), by + rng.randint(4, 10)),
                           (bx + rng.randint(14, 24), by + rng.randint(10, 18))], 1)

    # הצללה אנכית - למעלה ולמטה כהה יותר (Ambient Occlusion מזויף)
    for y in range(TEX_SIZE):
        f = int(255 * (0.66 + 0.34 * math.sin(math.pi * (y + 0.5) / TEX_SIZE) ** 0.6))
        tex.fill((f, f, f), (0, y, TEX_SIZE, 1), special_flags=pygame.BLEND_RGB_MULT)
    return tex


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


class Player:
    def __init__(self, x, y, angle=0):
        self.x = x
        self.y = y
        self.angle = angle
        self.radius = 10
        self.hidden = False  # האם השחקן מתחבא כרגע בתוך ארון

    def _blocked(self, x, y, grid, boxes):
        r = self.radius
        if any(is_wall(grid, x + ox, y + oy) for ox in (-r, r) for oy in (-r, r)):
            return True
        for x0, y0, x1, y1 in boxes:  # ארונות הם גוף מוצק
            if x + r > x0 and x - r < x1 and y + r > y0 and y - r < y1:
                return True
        return False

    def try_move(self, dx, dy, grid, boxes=()):
        new_x = self.x + dx
        if not self._blocked(new_x, self.y, grid, boxes):
            self.x = new_x
        new_y = self.y + dy
        if not self._blocked(self.x, new_y, grid, boxes):
            self.y = new_y


class Monster:
    """השומר. מצבים:
       asleep - ישן במאורה עד שהפנס מגיע אליו
       chase  - רודף אחרי השחקן
       search - איבד אותך (התחבאת בלי שראה) - מחפש באזור שבו ראה אותך לאחרונה
       return - ויתר, חוזר למאורה, ושם נרדם שוב"""

    def __init__(self, col, row):
        self.home = (col, row)
        self.x = col * CELL + CELL / 2
        self.y = row * CELL + CELL / 2
        self.path = []
        self.repath_timer = 0
        self.awake = False
        self.state = "asleep"
        self.speed = 1.7
        self.target_cell = None
        self.last_seen = None      # התא שבו ראה את השחקן לאחרונה
        self.saw_hide = False      # האם ראה את השחקן נכנס לארון
        self.search_timer = 0.0
        self.walk_phase = 0.0      # לאנימציית ההליכה
        self.walk_amp = 0.0        # 0 = עומד, 1 = הולך (מעבר חלק)
        self.facing = random.uniform(0, 2 * math.pi)  # הכיוון שהגוף פונה אליו
        self.sees = False

    def wake(self, player):
        self.awake = True
        self.state = "chase"
        self.saw_hide = False
        self.last_seen = (int(player.x // CELL), int(player.y // CELL))
        self.repath_timer = 0

    def can_see(self, grid, player):
        """השומר רואה את השחקן רק אם הוא לא מתחבא, בטווח, ובלי קיר באמצע"""
        if player.hidden:
            return False
        if math.hypot(self.x - player.x, self.y - player.y) > SIGHT_RANGE:
            return False
        return line_of_sight(grid, self.x, self.y, player.x, player.y)

    def _set_target(self, cell):
        if cell != self.target_cell:
            self.target_cell = cell
            self.repath_timer = 0

    def _random_near(self, grid, center, radius=3):
        cands = []
        for c in range(center[0] - radius, center[0] + radius + 1):
            for r in range(center[1] - radius, center[1] + radius + 1):
                if (0 <= r < len(grid) and 0 <= c < len(grid[0])
                        and grid[r][c] == 0 and (c, r) != center):
                    cands.append((c, r))
        return random.choice(cands) if cands else center

    def bfs_path(self, grid, start, goal):
        rows, cols = len(grid), len(grid[0])
        visited = [[False] * cols for _ in range(rows)]
        prev = {}
        q = deque([start])
        visited[start[1]][start[0]] = True
        while q:
            cx, cy = q.popleft()
            if (cx, cy) == goal:
                break
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < cols and 0 <= ny < rows and not visited[ny][nx] and grid[ny][nx] == 0:
                    visited[ny][nx] = True
                    prev[(nx, ny)] = (cx, cy)
                    q.append((nx, ny))
        if goal not in prev and goal != start:
            return []
        path = []
        node = goal
        while node != start:
            path.append(node)
            if node not in prev:
                return []
            node = prev[node]
        path.reverse()
        return path

    def update(self, grid, player, dt, light_radius=LIGHT_RADIUS):
        if TEST_NO_MONSTER:
            return False
        if self.state == "asleep":
            dist = math.hypot(self.x - player.x, self.y - player.y)
            if not player.hidden and dist < light_radius:
                self.wake(player)
            else:
                return False

        my_cell = (int(self.x // CELL), int(self.y // CELL))
        player_cell = (int(player.x // CELL), int(player.y // CELL))
        sees = self.can_see(grid, player)
        self.sees = sees
        if sees:
            self.last_seen = player_cell

        # מעברים בין מצבים
        if self.state == "chase":
            if player.hidden and not self.saw_hide:
                # התחבאת בלי שראה - הוא מאבד אותך והולך לחפש איפה שראה אותך לאחרונה
                self.state = "search"
                self.search_timer = SEARCH_DURATION
                self._set_target(self.last_seen or my_cell)
        elif self.state in ("search", "return", "wander") and sees:
            self.state = "chase"
            self.repath_timer = 0

        # יעד לפי מצב
        if self.state == "wander":
            # משוטט במבוך בזמן שאתה בחדר המצלמות - לפעמים עובר מול מצלמה
            speed = MONSTER_SLOW_SPEED
            if self.target_cell is None or (my_cell == self.target_cell and not self.path):
                pts = getattr(self, "wander_points", None)
                if pts and random.random() < 0.65:
                    self._set_target(random.choice(pts))
                else:
                    free = [(c, r) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == 0]
                    self._set_target(random.choice(free))
        elif self.state == "chase":
            self._set_target(player_cell)
            speed = self.speed
        elif self.state == "search":
            speed = MONSTER_SLOW_SPEED
            self.search_timer -= dt
            if self.search_timer <= 0:
                self.state = "return"
                self._set_target(self.home)
            elif my_cell == self.target_cell and not self.path:
                # הגיע - מסתובב ומרחרח בתאים סמוכים
                self._set_target(self._random_near(grid, self.last_seen or my_cell))
        else:  # return
            speed = MONSTER_SLOW_SPEED
            self._set_target(self.home)
            hx, hy = self.home[0] * CELL + CELL / 2, self.home[1] * CELL + CELL / 2
            if my_cell == self.home and math.hypot(hx - self.x, hy - self.y) < 4:
                self.x, self.y = hx, hy
                self.path = []
                self.state = "asleep"
                self.awake = False
                self.target_cell = None
                return False

        self.repath_timer -= dt
        if self.repath_timer <= 0 and self.target_cell is not None:
            self.repath_timer = 0.5
            self.path = self.bfs_path(grid, my_cell, self.target_cell)

        if self.path:
            nc, nr = self.path[0]
            tx, ty = nc * CELL + CELL / 2, nr * CELL + CELL / 2
        elif my_cell != self.target_cell:
            return True  # אין מסלול כרגע - מחכה לחישוב הבא (לא עובר דרך קירות)
        elif self.state == "chase":
            tx, ty = player.x, player.y  # באותו תא - ישר אל השחקן
        else:
            tx, ty = self.target_cell[0] * CELL + CELL / 2, self.target_cell[1] * CELL + CELL / 2
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 3:
            if self.path:
                self.path.pop(0)
        else:
            step = min(speed, dist)
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
            self.walk_phase += step * 0.085
        return True


class Key:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False


# ==================================================================
# מנוע מוזיקת אימה - סאונד סינתטי מלא, ללא קבצים חיצוניים וללא numpy.
# כל הצלילים נבנים כמערכי דגימות ב-Python נקי בזמן טעינת המשחק.
# ==================================================================
AUDIO_SR = 22050
TWO_PI = 2 * math.pi

# הסינתזה של כל הצלילים ב-Python נקי לוקחת כמה שניות. מריצים אותה פעם אחת
# ושומרים WAV מקומי; בהרצות הבאות טוענים מהמטמון ומתחילים מיד.
_CACHE_VER = 4
try:
    _CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".horror_audio_cache")
except NameError:
    _CACHE_DIR = os.path.join(os.getcwd(), ".horror_audio_cache")


def _clamp16(v):
    if v > 32767:
        return 32767
    if v < -32767:
        return -32767
    return int(v)


def _make_sound(samples):
    """הופך רצף של floats בטווח [-1, 1] ל-pygame.mixer.Sound (מונו, 16-bit)"""
    buf = array.array('h', (_clamp16(s * 32767.0) for s in samples))
    return pygame.mixer.Sound(buffer=buf.tobytes())


def _cached_sound(name, factory):
    """מחזיר Sound מתוך מטמון WAV מקומי, או בונה אותו (ושומר) אם אין."""
    path = os.path.join(_CACHE_DIR, "%s.v%d.wav" % (name, _CACHE_VER))
    if os.path.isfile(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            pass
    snd = factory()
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(AUDIO_SR)
            w.writeframes(snd.get_raw())
    except Exception:
        pass
    return snd


def _gen_creak(seed=5):
    """חריקת דלת ישנה - מסור נמוך עם תדר "מקרטע" ומעטפת לא יציבה"""
    rnd = random.Random(seed)
    n = int(AUDIO_SR * 1.5)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / AUDIO_SR
        f = 95 + 70 * math.sin(t * 2.1) + 25 * math.sin(t * 13.0) + rnd.uniform(-6, 6)
        phase += f / AUDIO_SR
        saw = 2 * (phase % 1.0) - 1
        stick = 0.55 + 0.45 * math.sin(t * 37 + math.sin(t * 5) * 3)  # "גמגום" החריקה
        env = min(1.0, t * 8) * max(0.0, 1 - t / 1.5) ** 0.7
        out.append(saw * stick * env * 0.32)
    return _make_sound(out)


def _gen_shutter():
    """קליק של מצלמה: שני "טיקים" קצרים של רעש"""
    rnd = random.Random(3)
    n = int(AUDIO_SR * 0.22)
    out = []
    for i in range(n):
        t = i / AUDIO_SR
        e1 = math.exp(-t * 90) if t < 0.05 else 0.0
        e2 = math.exp(-(t - 0.09) * 70) if t >= 0.09 else 0.0
        out.append(rnd.uniform(-1, 1) * (e1 * 0.7 + e2 * 0.5))
    return _make_sound(out)


def _gen_complete():
    """צליל "משימה הושלמה" - ארפג'ו מינורי קר, מתאים לאווירה"""
    n = int(AUDIO_SR * 2.4)
    notes = [(0.0, 220.0), (0.18, 261.6), (0.36, 329.6), (0.54, 440.0)]
    out = [0.0] * n
    for start, f in notes:
        s0 = int(start * AUDIO_SR)
        for i in range(s0, n):
            t = (i - s0) / AUDIO_SR
            env = math.exp(-t * 1.6) * min(1.0, t * 60)
            out[i] += (math.sin(TWO_PI * f * t) + 0.3 * math.sin(TWO_PI * f * 2 * t)) * env * 0.16
    return _make_sound(out)


def _gen_drone(seconds, base_hz, partials, noise_level, seed):
    """דרון נמוך ומתמשך - בסיס ה'מוזיקה'. תדרים ננעלים למחזורים שלמים כדי שהלולאה תהיה חלקה."""
    rnd = random.Random(seed)
    n = int(AUDIO_SR * seconds)

    def snap(freq):
        cycles = max(1, round(freq * n / AUDIO_SR))
        return cycles * AUDIO_SR / n

    voices = [(snap(base_hz * mult), amp, rnd.uniform(0, TWO_PI)) for mult, amp in partials]
    lfo_hz = snap(0.07)
    lfo2_hz = snap(0.11)

    out = [0.0] * n
    brown = 0.0
    for i in range(n):
        t = i / AUDIO_SR
        s = 0.0
        for f, a, ph in voices:
            s += a * math.sin(TWO_PI * f * t + ph)
        brown = (brown + 0.02 * rnd.uniform(-1, 1)) * 0.999
        s += noise_level * brown * 6.0
        lfo = (0.55 + 0.45 * math.sin(TWO_PI * lfo_hz * t)) * \
              (0.8 + 0.2 * math.sin(TWO_PI * lfo2_hz * t + 1.3))
        out[i] = s * lfo

    fade = int(AUDIO_SR * 0.4)
    for i in range(fade):
        a = i / fade
        out[i] = out[i] * a + out[n - fade + i] * (1 - a)
    out = out[:n - fade]

    peak = max(1e-6, max(abs(v) for v in out))
    scale = 0.9 / peak
    return _make_sound(v * scale for v in out)


def _gen_heartbeat():
    """פעימת לב כפולה (לאב-דאב) - סינוס נמוך שצולל בגובה ודועך מהר"""
    n = int(AUDIO_SR * 1.15)
    out = [0.0] * n

    def thump(start, amp):
        for i in range(int(AUDIO_SR * 0.35)):
            idx = start + i
            if idx >= n:
                break
            t = i / AUDIO_SR
            env = math.exp(-t / 0.09)
            f = 48 * math.exp(-t * 6) + 30
            out[idx] += amp * env * math.sin(TWO_PI * f * t)

    thump(0, 0.9)
    thump(int(AUDIO_SR * 0.26), 0.72)
    return _make_sound(out)


def _gen_stinger(seed):
    """סטינגר רגע-ההתעוררות - בום נמוך + סוויל דיסוננטי שעולה"""
    rnd = random.Random(seed)
    n = int(AUDIO_SR * 1.6)
    out = [0.0] * n
    for i in range(n):
        t = i / AUDIO_SR
        prog = t / 1.6
        boom = math.sin(TWO_PI * (38 + 10 * math.exp(-t * 3)) * t) * math.exp(-t / 0.5) * 0.9
        rise = 70 + prog * prog * 260
        swell = (math.sin(TWO_PI * rise * t) + 0.6 * math.sin(TWO_PI * rise * 1.5 * t)) \
                * min(1.0, prog * 1.2) * (1 - prog) * 0.5
        noise = rnd.uniform(-1, 1) * prog * (1 - prog) * 0.4
        out[i] = boom + swell + noise
    peak = max(1e-6, max(abs(v) for v in out))
    return _make_sound(v * (0.95 / peak) for v in out)


def _gen_screech(seed):
    """צרחת הטריפה - אשכול תדרים גבוה ודיסוננטי + רעש, חזק ומעוות"""
    rnd = random.Random(seed)
    n = int(AUDIO_SR * 1.3)
    out = [0.0] * n
    parts = [900, 1132, 1350, 1607, 1893, 2250]
    for i in range(n):
        t = i / AUDIO_SR
        prog = t / 1.3
        glide = 1.0 - 0.35 * prog
        s = 0.0
        for k, f in enumerate(parts):
            s += math.sin(TWO_PI * f * glide * t + math.sin(TWO_PI * (3 + k) * t) * 0.8)
        s = s / len(parts) + rnd.uniform(-1, 1) * 0.7
        if prog < 0.03:
            env = prog / 0.03
        elif prog > 0.85:
            env = (1 - prog) / 0.15
        else:
            env = 1.0
        out[i] = s * env
    peak = max(1e-6, max(abs(v) for v in out))
    return _make_sound(v * (0.98 / peak) for v in out)


def _gen_siren(seconds=4.6, lo=370, hi=910):
    """סירנת אזעקה קלאסית - יבבה מכנית איטית שעולה ויורדת בעקומה רכה (כמו סירנת
    'צבע אדום' / אזעקת התקפה אווירית). גוון חם, לא נוקב, ומתגבר מעט בשיא."""
    n = int(AUDIO_SR * seconds)
    out = [0.0] * n
    phase = 0.0
    for i in range(n):
        frac = i / n
        rise = 0.5 - 0.5 * math.cos(TWO_PI * frac)   # 0 -> 1 -> 0 חלק (בלי פינות)
        f = lo + (hi - lo) * rise
        phase += TWO_PI * f / AUDIO_SR
        s = (math.sin(phase)
             + 0.22 * math.sin(2 * phase)
             + 0.09 * math.sin(3 * phase))
        out[i] = s * (0.68 + 0.32 * rise)            # מתחזק כשהסירנה "מתפתלת" למעלה
    fade = int(AUDIO_SR * 0.015)
    for i in range(fade):
        a = i / fade
        out[i] *= a
        out[n - 1 - i] *= a
    peak = max(1e-6, max(abs(v) for v in out))
    return _make_sound(v * (0.8 / peak) for v in out)


def _gen_scream(seed):
    """צרחה אנושית מרוחקת - גובה שעולה בבהלה ואז צונח, עם רעד קול (ויברטו) והד."""
    rnd = random.Random(seed)
    dur = 1.7
    n = int(AUDIO_SR * dur)
    out = [0.0] * n
    phase = 0.0
    for i in range(n):
        t = i / AUDIO_SR
        prog = t / dur
        # קונטור גובה: זינוק מהיר למעלה, החזקה, ואז צניחה
        if prog < 0.15:
            base = 280 + (620 - 280) * (prog / 0.15)
        elif prog < 0.65:
            base = 620 + 60 * math.sin(prog * 22)
        else:
            base = 620 - (620 - 180) * ((prog - 0.65) / 0.35)
        vibrato = 1.0 + 0.06 * math.sin(TWO_PI * 6.5 * t)
        f = base * vibrato
        phase += TWO_PI * f / AUDIO_SR
        # פורמנטים - קולני וקרוע
        s = (math.sin(phase)
             + 0.5 * math.sin(2 * phase)
             + 0.32 * math.sin(3 * phase)
             + 0.2 * math.sin(4 * phase))
        s += 0.18 * rnd.uniform(-1, 1) * s   # חספוס/סדק בקול
        env = math.sin(math.pi * min(1.0, prog / 0.92)) ** 1.3
        out[i] = s * env * 0.4

    # הד פשוט - חוזר דועך
    for delay, gain in ((0.11, 0.4), (0.23, 0.22), (0.37, 0.12)):
        d = int(AUDIO_SR * delay)
        for i in range(n - 1, d - 1, -1):
            out[i] += out[i - d] * gain

    peak = max(1e-6, max(abs(v) for v in out))
    return _make_sound(v * (0.9 / peak) for v in out)


def _gen_music(seed=7):
    """מוזיקת רקע מפחידה - לולאה קומפוזית בלה מינור עם קווינטה מוקטנת (טריטון):
    פעם נמוך פועם, פד עמום ומוטיב פעמונים דליל ומנוגן לאט. נבנית פעם אחת בטעינה."""
    rnd = random.Random(seed)
    beat = 1.15
    beats = 16
    dur = beat * beats
    n = int(AUDIO_SR * dur)
    out = [0.0] * n

    def add_event(start_beat, freq, length, amp, kind):
        """מוסיף צליל קצר וממוקד (פעמון / פעימת באס). דליל ולכן זול."""
        s0 = int(AUDIO_SR * start_beat * beat)
        ns = int(AUDIO_SR * length)
        for k in range(ns):
            idx = s0 + k
            if idx >= n:
                idx -= n
            t = k / AUDIO_SR
            if kind == "bell":
                env = math.exp(-t * 2.4)
                s = (math.sin(TWO_PI * freq * t)
                     + 0.5 * math.sin(TWO_PI * 2 * freq * t) * math.exp(-t * 4)
                     + 0.28 * math.sin(TWO_PI * 3.01 * freq * t) * math.exp(-t * 6))
            else:  # "sub" - פעימה נמוכה
                env = math.exp(-t * 5.5)
                s = math.sin(TWO_PI * freq * t) * (1.0 + 2.0 * math.exp(-t * 18))
            out[idx] += s * env * amp

    A2, C3, E3, F2 = 110.00, 130.81, 164.81, 87.31
    A1 = 55.00
    A4, B4, C5, E4, Eb5, D5 = 440.00, 493.88, 523.25, 329.63, 622.25, 587.33

    # פד - מעבר אחד על כל הבאפר: לה מינור בחצי הראשון, מצע כהה (b6) בחצי השני.
    # תדרים ננעלים למחזורים שלמים כדי שהפד יתפור את הלולאה בלי קליק.
    def snap(freq):
        return max(1, round(freq * n / AUDIO_SR)) * AUDIO_SR / n

    chord_a = [snap(f) for f in (A2, C3, E3)]
    chord_b = [snap(f) for f in (F2, C3, E3)]
    half = n / 2
    for i in range(n):
        t = i / AUDIO_SR
        chord = chord_a if i < half else chord_b
        # מעבר רך בין שני החצאים
        blend = 1.0
        d = min(i, n - i, abs(i - half))
        if d < AUDIO_SR * 0.6:
            blend = 0.4 + 0.6 * (d / (AUDIO_SR * 0.6))
        s = 0.0
        for f in chord:
            s += math.sin(TWO_PI * f * t) + 0.4 * math.sin(TWO_PI * f * 2 * t)
        out[i] += s * 0.05 * blend

    # פעימת באס נמוכה בכל פעימה, עם הדגשה על 1 ו-3 של כל תיבה
    for b in range(beats):
        accent = 0.32 if b % 4 in (0, 2) else 0.2
        add_event(b, A1, 0.5, accent, "sub")

    # מוטיב פעמונים דליל ומאיים - יורד, עם טריטון
    motif = [(0, A4, 3.0), (4, Eb5, 2.2), (7, C5, 1.6),
             (10, B4, 2.4), (13, E4, 3.0)]
    for sb, f, ln in motif:
        add_event(sb + rnd.uniform(-0.03, 0.03), f, ln, 0.16, "bell")
    # הד רפאים חלש חצי-תיבה אחרי כל צליל
    for sb, f, ln in motif:
        add_event(sb + 0.5, f, ln * 0.6, 0.05, "bell")

    fade = int(AUDIO_SR * 0.5)
    for i in range(fade):
        a = i / fade
        out[i] = out[i] * a + out[n - fade + i] * (1 - a)
    out = out[:n - fade]

    peak = max(1e-6, max(abs(v) for v in out))
    return _make_sound(v * (0.82 / peak) for v in out)


class HorrorAudio:
    """מנהל את כל הסאונד - דרון רקע מתמשך שמתגבר לפי הסכנה, פעימות לב, סטינגר וצרחה.
    כל כשל (אין כרטיס קול / מצב headless) פשוט משתיק בשקט בלי להפיל את המשחק."""

    def __init__(self):
        self.enabled = False
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            pygame.mixer.init(frequency=AUDIO_SR, size=-16, channels=1, buffer=512)
        except pygame.error:
            return
        try:
            pygame.mixer.set_num_channels(16)
            self.snd_drone = _cached_sound("drone", lambda: _gen_drone(
                11.0, 46.0, [(0.5, 0.18), (1, 0.5), (2, 0.26), (3, 0.12), (4.01, 0.07)], 0.10, 11))
            self.snd_drone2 = _cached_sound("drone2", lambda: _gen_drone(
                9.0, 46.0, [(1, 0.4), (2.02, 0.24), (2.83, 0.2), (4.24, 0.12), (5.66, 0.06)], 0.06, 27))
            self.snd_heart = _cached_sound("heart", _gen_heartbeat)
            self.snd_stinger = _cached_sound("stinger", lambda: _gen_stinger(42))
            self.snd_screech = _cached_sound("screech", lambda: _gen_screech(99))
            self.snd_siren = _cached_sound("siren", _gen_siren)
            self.snd_screams = [_cached_sound("scream%d" % i, lambda s=s: _gen_scream(s))
                                for i, s in enumerate((201, 202, 203))]
            self.snd_music = _cached_sound("music", _gen_music)
            self.snd_creak = _cached_sound("creak", _gen_creak)
            self.snd_complete = _cached_sound("complete", _gen_complete)
            self.snd_shutter = _cached_sound("shutter", _gen_shutter)
        except Exception:
            return

        self.ch_drone = pygame.mixer.Channel(0)
        self.ch_drone2 = pygame.mixer.Channel(1)
        self.ch_heart = pygame.mixer.Channel(2)
        self.ch_fx = pygame.mixer.Channel(3)
        self.ch_siren = pygame.mixer.Channel(5)
        self.ch_scream = pygame.mixer.Channel(6)
        self.ch_music = pygame.mixer.Channel(7)

        self._music_on = False
        self._awake = False
        self._jump = False
        self._ended = False
        self.target_vol = 0.16
        self.heart_timer = 0.0
        self.scream_timer = random.uniform(8.0, 20.0)
        self.enabled = True

    def play_fx(self, name):
        if self.enabled:
            snd = getattr(self, name, None)
            if snd is not None:
                self.ch_fx.play(snd)

    def _start_music(self):
        self.ch_drone.play(self.snd_drone, loops=-1)
        self.ch_drone.set_volume(0.0)
        self.ch_music.play(self.snd_music, loops=-1)
        self.ch_music.set_volume(0.0)
        self._music_on = True

    def frame_update(self, dt, game):
        if not self.enabled:
            return
        if not self._music_on:
            self._start_music()

        # התחלת סבב חדש - חזרה לאווירת "השומר ישן"
        if self._ended and not (game.game_over or game.win):
            self._ended = False
            self._awake = False
            self._jump = False
            self.ch_heart.stop()
            self.ch_siren.stop()
            if self.ch_drone2.get_busy():
                self.ch_drone2.fadeout(800)
            self.target_vol = 0.16
            self.scream_timer = random.uniform(8.0, 20.0)

        # השומר התעורר - אזעקה + סטינגר + שכבת דרון דיסוננטית והגברת עוצמה
        if game.monster.awake and not self._awake and not game.on_menu and not game.in_camera_room:
            self._awake = True
            self.ch_fx.play(self.snd_stinger)
            self.ch_drone2.play(self.snd_drone2, loops=-1)
            self.ch_drone2.set_volume(0.0)
            self.ch_siren.set_volume(0.34)
            self.ch_siren.play(self.snd_siren, loops=-1, fade_ms=350)
            self.target_vol = 0.26
        elif not game.monster.awake and self._awake:
            # השומר חזר לישון (איבד אותך) - האזעקה והדרון הדיסוננטי דועכים
            self._awake = False
            self.ch_siren.fadeout(1500)
            if self.ch_drone2.get_busy():
                self.ch_drone2.fadeout(1500)
            self.target_vol = 0.16

        # כשהשומר מחפש / חוזר - האזעקה שקטה יותר מאשר במרדף
        if self._awake and not self._jump and not self._ended and self.ch_siren.get_busy():
            siren_target = (0.0 if game.in_camera_room
                            else 0.34 if game.monster.state == "chase" else 0.12)
            sv = self.ch_siren.get_volume()
            self.ch_siren.set_volume(sv + (siren_target - sv) * min(1.0, dt * 2.0))

        # רגע הטריפה - צרחה, והשתקת המוזיקה והאזעקה מתחתיה
        if game.jumpscare_active and not self._jump:
            self._jump = True
            self.ch_fx.play(self.snd_screech)
            self.ch_siren.fadeout(200)
            self.target_vol = 0.08
        elif not game.jumpscare_active:
            self._jump = False

        # מסך סיום
        if (game.win or game.game_over) and not self._ended:
            self._ended = True
            self.ch_siren.fadeout(600)
            if game.win:
                self.ch_drone.fadeout(2500)
                self.ch_drone2.fadeout(2000)
                self.ch_music.fadeout(2500)
                self.ch_heart.stop()
                self._music_on = False
            else:
                self.target_vol = 0.12

        # החלקת עוצמת הדרון לכיוון היעד
        cur = self.ch_drone.get_volume()
        cur += (self.target_vol - cur) * min(1.0, dt * 1.5)
        self.ch_drone.set_volume(cur)

        # מוזיקת הרקע - חזקה יותר כשהשומר ער, מונמכת בטריפה
        if self.ch_music.get_busy():
            if game.jumpscare_active:
                music_target = 0.09
            elif game.game_over or game.win:
                music_target = 0.22
            elif game.on_menu:
                music_target = 0.68
            elif self._awake:
                music_target = 0.92
            else:
                music_target = 0.75
            mc = self.ch_music.get_volume()
            mc += (music_target - mc) * min(1.0, dt * 1.4)
            self.ch_music.set_volume(mc)
        if self.ch_drone2.get_busy():
            d2 = self.ch_drone2.get_volume()
            d2_target = 0.0 if (self._ended and game.win) else (self.target_vol * 0.85 if self._awake else 0.0)
            d2 += (d2_target - d2) * min(1.0, dt * 1.2)
            self.ch_drone2.set_volume(d2)

        # פעימות לב לפי הקרבה למפלצת
        if (game.monster.awake and not game.on_menu and not game.win and not game.in_camera_room
                and not game.game_over and not game.jumpscare_active):
            dist = math.hypot(game.monster.x - game.player.x, game.monster.y - game.player.y)
            threshold = SHAKE_DISTANCE * 1.6
            if dist < threshold:
                closeness = 1.0 - dist / threshold
                self.heart_timer -= dt
                if self.heart_timer <= 0:
                    self.heart_timer = 1.15 - 0.6 * closeness
                    self.ch_heart.play(self.snd_heart)
                    self.ch_heart.set_volume(0.3 + 0.6 * closeness)
            else:
                self.heart_timer = 0.0

        # צרחה מדי פעם - רחוקה כשהשומר ישן, קרובה ותכופה יותר כשהוא ער
        if (not game.on_menu and not game.win and not game.game_over
                and not game.jumpscare_active):
            self.scream_timer -= dt
            if self.scream_timer <= 0:
                if self._awake:
                    self.scream_timer = random.uniform(6.0, 14.0)
                    vol = random.uniform(0.5, 0.8)
                else:
                    self.scream_timer = random.uniform(12.0, 28.0)
                    vol = random.uniform(0.2, 0.4)
                if not self.ch_scream.get_busy():
                    self.ch_scream.play(random.choice(self.snd_screams))
                    self.ch_scream.set_volume(vol)


class FPSGame:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("המתחם הנטוש - בדיקת הסוף")
        self.screen = pygame.Surface((WIDTH, HEIGHT))  # משטח ציור פנימי - מאפשר להזיז אותו לרעד
        self.clock = pygame.time.Clock()
        self.audio = HorrorAudio()
        self.font_big = pygame.font.SysFont("arial", 44, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18)
        self.font_note = pygame.font.SysFont("arial", 30, bold=True)
        self.font_story = pygame.font.SysFont("arial", 22)
        self.font_button = pygame.font.SysFont("arial", 32, bold=True)
        self.font_huge = pygame.font.SysFont("arial", 76, bold=True)
        self._glow_cache = {}
        self.vignette_surface = self.build_vignette()
        self.wall_textures = self.build_wall_textures()
        self.bg_normal = self.build_background(False)
        self.bg_boost = self.build_background(True)
        self.glow_normal = self.build_flashlight_glow(False)
        self.glow_boost = self.build_flashlight_glow(True)
        self.menu_bg = self.build_menu_bg()
        self.hud_bg = self.build_hud_bg()
        self.grain_surface = self.build_grain()
        self.closet_overlay = self.build_closet_overlay()
        self.closet_textures = self.build_closet_textures()
        self.view_room = False
        self.room_grid = [[1]]
        self.room_decals = {}
        self.room_door = (0, 0, (0, 1))
        self.room_props = []
        self.reset()
        self.on_menu = True
        self.play_button_rect = pygame.Rect(0, 0, 220, 64)
        self.play_button_rect.center = (WIDTH // 2, HEIGHT - 110)
        self.restart_button_rect = pygame.Rect(0, 0, 280, 62)
        self.restart_button_rect.center = (WIDTH // 2, HEIGHT - 70)
        if TEST_ENDING_ONLY:
            self.start_test_ending()

    def start_test_ending(self):
        """מצב בדיקה: מדלגים על כל המשחק ומתחילים ישר בסוף, ברקע של חדר הבקרה"""
        self.on_menu = False
        self.journal_collected = True
        self.journal_on_desk = True
        self.enter_camera_room()
        self.room_intro_done = True
        self.start_ending()

    def restart(self):
        self.reset()
        if TEST_ENDING_ONLY:
            self.start_test_ending()

    def reset(self):
        self.grid = generate_maze(COLS, ROWS)
        self.player = Player(CELL + CELL / 2, CELL + CELL / 2, angle=0)

        free_cells = [(c, r) for r in range(ROWS) for c in range(COLS) if self.grid[r][c] == 0]
        free_cells.sort(key=lambda cell: -(abs(cell[0] - 1) + abs(cell[1] - 1)))

        exit_col, exit_row = free_cells[0]

        monster_col, monster_row = free_cells[len(free_cells) // 3]
        self.monster = Monster(monster_col, monster_row)

        # חדר פתוח קטן (2x2) שנחצב במבוך, ובמרכזו היומן שחובה לאסוף לפני היציאה
        self.journal_collected = False
        self.left_without_journal = False
        self.journal_room = self._carve_journal_room(free_cells, (exit_col, exit_row),
                                                     (monster_col, monster_row))
        rc, rr = self.journal_room
        self.journal_pos = ((rc + 1) * CELL, (rr + 1) * CELL)

        # הדלת בנויה בתוך קיר של תא היציאה (עדיפות לקיר שמול הפתח, אם זה מבוי סתום)
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        walls = [d for d in dirs if self.grid[exit_row + d[1]][exit_col + d[0]] == 1]
        opens = [d for d in dirs if d not in walls]
        if len(opens) == 1 and (-opens[0][0], -opens[0][1]) in walls:
            wd = (-opens[0][0], -opens[0][1])
        else:
            wd = walls[0]
        self.exit_wall = (exit_col + wd[0], exit_row + wd[1], wd)
        # נקודת היציאה - צמוד לדלת (מגיעים אליה = נוגעים בדלת)
        self.exit_pos = (exit_col * CELL + CELL / 2 + wd[0] * CELL * 0.3,
                         exit_row * CELL + CELL / 2 + wd[1] * CELL * 0.3)

        self.wall_decals = self.build_wall_decals(self.grid)

        # ארונות מחבוא - בקצוות מבוי סתום, צמודים לקיר
        self.hiding_spots = self._place_hiding_spots((exit_col, exit_row), (monster_col, monster_row))
        closet_cells = {s["cell"] for s in self.hiding_spots}
        self.hide_exit_pos = None
        self.current_spot = None

        # דלת שנפתחת + חדר המצלמות
        self.door_open = 0.0
        self.entering = 0.0           # >0 = באמצע מעבר לשחור לתוך הדלת
        self.in_camera_room = False
        self.room_timer = 0.0
        self.cameras = []
        self.cam_feeds = {}
        self.cam_cursor = 0
        self.cam_focus = None
        self.mission_text = "למצוא את היומן"
        # יומן, מצלמה ותמונות
        self.room_intro_done = False
        self.journal_open = False
        self.journal_on_desk = False
        self.camera_on_desk = False
        self.has_camera = False
        self.photos = []
        self.photo_view = False
        self.photo_pending = False
        self.flash_timer = 0.0
        self.banner = None            # הודעה גדולה זמנית: (כותרת, משנה, צבע, זמן שנשאר)
        self.leaving_room = 0.0       # >0 = באמצע מעבר מהחדר חזרה למבוך
        self.photo_index = -1
        self.win_view_t = 0.0
        self.ending_active = False
        self.ending_t = 0.0
        self.confetti = []
        self.newspaper = None
        self.door_cooldown = 0.0
        if hasattr(self, "door_frames"):
            self.wall_textures["door"], self.wall_textures["door_glow"] = self.door_frames[0]

        # פתקים כתובים בדם, מפוזרים במבוך - "תברח!!!"
        self.notes = []
        note_candidates = [c for c in free_cells
                            if math.hypot(c[0] - 1, c[1] - 1) > 2 and c not in closet_cells]
        random.shuffle(note_candidates)
        for col, row in note_candidates[:NUM_NOTES]:
            nx = col * CELL + CELL / 2 + random.uniform(-CELL * 0.2, CELL * 0.2)
            ny = row * CELL + CELL / 2 + random.uniform(-CELL * 0.2, CELL * 0.2)
            self.notes.append((nx, ny, random.uniform(-8, 8), NOTE_TEXT))

        # פתק מיוחד ליד ההתחלה - "הוא כאן!" - מרגיע את התחושה מהשנייה הראשונה
        intro_col, intro_row = 2, 1
        if 0 <= intro_row < ROWS and 0 <= intro_col < COLS and self.grid[intro_row][intro_col] == 0:
            intro_x = intro_col * CELL + CELL / 2
            intro_y = intro_row * CELL + CELL / 2
        else:
            intro_x, intro_y = CELL * 2, CELL + CELL / 2
        self.notes.append((intro_x, intro_y, random.uniform(-6, 6), "הוא כאן!"))

        self.keys_collected = 0
        self.win = False
        self.message = ""
        self.message_timer = 0
        self.flicker = 0
        self.flicker_timer = random.uniform(2, 5)
        self.forced_turn_active = False
        self.forced_turn_timer = 0.0
        self.jumpscare_active = False
        self.jumpscare_timer = 0.0
        self.game_over = False
        self.blood_particles = []
        self.blood_marks = []
        self.shot_effects = []
        self.depth_buffer = [MAX_DEPTH] * NUM_RAYS

        # אווירת אימה סביבתית - לחישות, "הבזקי צל" ו"הבזקי פנטום" שלא קשורים למפלצת האמיתית
        self.dread_timer = random.uniform(1.5, 2.5)  # ההבזק הראשון קורה כמעט מיד
        self.whisper_text = ""
        self.whisper_timer = 0.0
        self.whisper_pos = (WIDTH / 2, 110)
        self.glimpse_active = False
        self.glimpse_timer = 0.0
        self.glimpse_pos = (WIDTH / 2, HEIGHT / 2)
        self.static_glitch_timer = random.uniform(3, 6)
        self.static_glitch_alpha = 0.0

        # פנס - מצב חזק (לחיצה על 1)
        self.light_boost = False
        self.effective_light_radius = LIGHT_RADIUS
        self.light_boost_hold_timer = 0.0
        self.forced_wake_triggered = False

    def _carve_journal_room(self, free_cells, exit_cell, monster_cell):
        """חוצב חדר פתוח קטן 2x2 במבוך, הרחק מנקודת הזינוק של השומר ומהדלת,
        ומחזיר את פינת השמאל-עליון שלו (עמודה, שורה)"""
        mx, my = monster_cell
        ex, ey = exit_cell
        in_bounds = [c for c in free_cells
                     if 1 <= c[0] <= COLS - 3 and 1 <= c[1] <= ROWS - 3
                     and c not in {exit_cell, monster_cell, (1, 1), (2, 1)}]

        def far_enough(c, monster_min, exit_min):
            return (math.hypot(c[0] - mx, c[1] - my) >= monster_min
                    and math.hypot(c[0] - ex, c[1] - ey) >= exit_min
                    and math.hypot(c[0] - 1, c[1] - 1) >= 5)

        pool = in_bounds or [(COLS // 2, ROWS // 2)]
        for monster_min, exit_min in [(7, 4), (5, 3), (4, 2), (0, 0)]:
            filtered = [c for c in in_bounds if far_enough(c, monster_min, exit_min)]
            if filtered:
                pool = filtered
                break

        rc, rr = pool[len(pool) // 2]
        rc = max(1, min(COLS - 3, rc))
        rr = max(1, min(ROWS - 3, rr))
        for dc in (0, 1):
            for dr in (0, 1):
                self.grid[rr + dr][rc + dc] = 0
        return (rc, rr)

    def _place_hiding_spots(self, exit_cell, monster_cell):
        """מפזר ארונות מחבוא: עדיפות לקצוות מבוי סתום (3 קירות), והארון נצמד לקיר האחורי.
        ארונות מרוחקים זה מזה, מההתחלה, מהדלת, ממאורת השומר ומחדר היומן."""
        grid = self.grid
        rc, rr = self.journal_room
        journal_cells = {(rc + dc, rr + dr) for dc in (-1, 0, 1, 2) for dr in (-1, 0, 1, 2)}
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        candidates = []
        for r in range(1, ROWS - 1):
            for c in range(1, COLS - 1):
                if grid[r][c] != 0:
                    continue
                if (c, r) in journal_cells or (c, r) in (exit_cell, monster_cell):
                    continue
                if math.hypot(c - 1, r - 1) < 4:
                    continue
                walls = [d for d in dirs if grid[r + d[1]][c + d[0]] == 1]
                if len(walls) >= 2:
                    candidates.append((len(walls), (c, r), walls))

        random.shuffle(candidates)
        candidates.sort(key=lambda x: -x[0])  # קודם מבוי סתום (3 קירות)

        spots = []
        for min_gap in (5, 3):
            for _, (c, r), walls in candidates:
                if len(spots) >= NUM_HIDING_SPOTS:
                    break
                if any(math.hypot(c - s["cell"][0], r - s["cell"][1]) < min_gap for s in spots):
                    continue
                if math.hypot(c - monster_cell[0], r - monster_cell[1]) < 3:
                    continue
                if len(walls) == 3:
                    # הקיר האחורי - מול הפתח היחיד
                    open_dir = next(d for d in dirs if d not in walls)
                    back = (-open_dir[0], -open_dir[1])
                else:
                    back = random.choice(walls)
                spots.append(self._make_closet(c, r, back))
            if len(spots) >= NUM_HIDING_SPOTS:
                break
        return spots

    def _make_closet(self, c, r, back):
        """בונה קופסה תלת-ממדית שצמודה לקיר האחורי (back) של התא (c, r)"""
        ccx, ccy = c * CELL + CELL / 2, r * CELL + CELL / 2
        depth, half_w = CELL * CLOSET_DEPTH, CELL * CLOSET_WIDTH / 2
        if back[0] != 0:
            wall_x = ccx + back[0] * CELL / 2
            xa, xb = sorted((wall_x, wall_x - back[0] * depth))
            box = (xa, ccy - half_w, xb, ccy + half_w)
            front_axis = 0
        else:
            wall_y = ccy + back[1] * CELL / 2
            ya, yb = sorted((wall_y, wall_y - back[1] * depth))
            box = (ccx - half_w, ya, ccx + half_w, yb)
            front_axis = 1
        bx, by = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        return {
            "cell": (c, r), "box": box, "front_axis": front_axis,
            "x": bx, "y": by,                                   # המקום שבו עומדים כשמתחבאים
            "fx": bx - back[0] * depth / 2, "fy": by - back[1] * depth / 2,  # מרכז החזית
            "face": math.atan2(-back[1], -back[0]),            # הכיוון שהארון "מביט" אליו
        }

    def nearest_hiding_spot(self):
        best, best_d = None, HIDE_REACH
        for s in self.hiding_spots:
            d = math.hypot(s["fx"] - self.player.x, s["fy"] - self.player.y)
            if d < best_d:
                best, best_d = s, d
        return best

    def can_toggle_hide(self):
        return not (self.on_menu or self.game_over or self.win
                    or self.jumpscare_active or self.forced_turn_active)

    def toggle_hide(self):
        """כניסה לארון / יציאה ממנו"""
        if not self.can_toggle_hide():
            return
        p = self.player
        if p.hidden:
            p.hidden = False
            p.x, p.y = self.hide_exit_pos
            self.current_spot = None
            self.monster.saw_hide = False
            self.message = "יצאת מהארון..."
            self.message_timer = 1.5
            return

        spot = self.nearest_hiding_spot()
        if spot is None:
            return
        # האם השומר רואה אותך ברגע הכניסה?
        # הארון תמיד בטוח - השומר לא יכול לתפוס אותך בפנים, הוא רק יחפש מסביב
        self.hide_exit_pos = (p.x, p.y)
        self.current_spot = spot
        p.hidden = True
        p.x, p.y = spot["x"], spot["y"]
        p.angle = spot["face"]
        self.monster.saw_hide = False
        self.message = "אתה מתחבא... אל תנשום"
        self.message_timer = 2.0

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if self.on_menu:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.on_menu = False
                    continue
                if event.key == pygame.K_r and (self.game_over or self.win):
                    self.restart()
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.journal_open or self.photo_view:
                        pass
                    elif self.in_camera_room and self.near_desk_camera():
                        self.take_camera()
                    elif self.in_camera_room:
                        self.room_click((WIDTH // 2, HEIGHT // 2))
                    else:
                        self.toggle_hide()
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.take_photo()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.on_menu:
                    if self.play_button_rect.collidepoint(event.pos):
                        self.on_menu = False
                elif self.ending_active:
                    if self.ending_restart_ready() and self.ending_button_rect().collidepoint(event.pos):
                        self.restart()
                elif self.game_over or self.win:
                    if self.restart_button_rect.collidepoint(event.pos):
                        self.reset()
                elif self.overlay_click(event.pos):
                    pass
                elif self.in_camera_room:
                    self.room_click(event.pos)
                elif not self.jumpscare_active and self.entering == 0:
                    self.try_shoot(event.pos)

    def try_shoot(self, pos):
        """יריה בעכבר - תמיד יוצרת אפקט ירי, ואם פוגעים במפלצת - הרבה דם, אבל שום נזק אמיתי"""
        mx, my = pos
        # קו יריה חזותי מתחתית המסך לנקודת הלחיצה
        self.shot_effects.append({
            "start": (WIDTH / 2, HEIGHT - 10),
            "end": (mx, my),
            "life": 0.12,
            "max_life": 0.12,
        })

        if not self.monster.awake:
            return

        proj = self.monster_projection()
        if proj is None or not self.monster_visible_at(mx, proj["corr"]):
            return
        H = proj["h"]
        body_top = proj["floor"] - H
        # פגיעה אם הלחיצה בתוך הגוף (ראש, גוף, ידיים)
        if abs(mx - proj["x"]) <= H * 0.24 and body_top <= my <= proj["floor"]:
            self.spawn_blood(mx, my, min(340, H * 0.5))
            flavor = random.choice([
                "לא עושה לו כלום...",
                "הוא אפילו לא מרגיש...",
                "זה סתם מכעיס אותו יותר",
                "הכדורים לא עוצרים אותו",
            ])
            self.message = flavor
            self.message_timer = 1.5

    def spawn_blood(self, x, y, size):
        """יוצר המון חלקיקי דם ופיצוצי דם במקום הפגיעה"""
        # התזה מיידית - חלקיקים שעפים לכל הכיוונים ונופלים בכבידה
        num_particles = random.randint(22, 32)
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 260)
            self.blood_particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 80,
                "life": random.uniform(0.5, 1.1),
                "max_life": 1.1,
                "r": random.uniform(2, 5),
            })

        # כתמי דם גדולים שנשארים על המסך ודוהים לאט - "מלא דם"
        num_marks = random.randint(4, 7)
        for _ in range(num_marks):
            ox = x + random.uniform(-size * 0.35, size * 0.35)
            oy = y + random.uniform(-size * 0.2, size * 0.45)
            self.blood_marks.append({
                "x": ox, "y": oy,
                "r": random.uniform(size * 0.06, size * 0.16),
                "alpha": 220,
            })

    def step_monster(self, dt):
        """מזיז את השומר ומסובב את הגוף שלו לכיוון התנועה (או אליך כשהוא רואה אותך)"""
        m = self.monster
        old_mx, old_my = m.x, m.y
        m.update(self.grid, self.player, dt, self.effective_light_radius)
        mdx, mdy = m.x - old_mx, m.y - old_my
        moved = math.hypot(mdx, mdy) > 0.05
        desired = m.facing
        if m.state == "chase" and m.sees:
            desired = math.atan2(self.player.y - m.y, self.player.x - m.x)
        elif moved:
            desired = math.atan2(mdy, mdx)
        turn = (desired - m.facing + math.pi) % (2 * math.pi) - math.pi
        max_turn = 5.0 * dt
        m.facing += max(-max_turn, min(max_turn, turn))
        m.walk_amp += ((1.0 if moved else 0.0) - m.walk_amp) * min(1.0, dt * 7)

    # ======================= חדר המצלמות =======================
    def pick_cameras(self):
        """בוחר מקומות למצלמות: מאורת השומר, חדר היומן, נקודת ההתחלה, ומסדרונות ארוכים"""
        grid = self.grid
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        def run_len(c, r, d):
            n = 0
            while grid[r + d[1] * (n + 1)][c + d[0] * (n + 1)] == 0:
                n += 1
            return n

        def make(c, r, name):
            d = max(dirs, key=lambda dd: run_len(c, r, dd))
            # המצלמה תלויה בפינה האחורית של התא ומביטה לאורך המסדרון
            back = 0.35 if grid[r - d[1]][c - d[0]] == 1 else 0.0
            return {"cell": (c, r), "name": name,
                    "x": c * CELL + CELL / 2 - d[0] * CELL * back,
                    "y": r * CELL + CELL / 2 - d[1] * CELL * back,
                    "angle": math.atan2(d[1], d[0])}

        rc, rr = self.journal_room
        fixed = [(self.monster.home, "מאורת השומר"), ((rc, rr), "חדר היומן"), ((1, 1), "נקודת הכניסה")]
        cams = [make(c, r, n) for (c, r), n in fixed]
        free = [(c, r) for r in range(1, ROWS - 1) for c in range(1, COLS - 1) if grid[r][c] == 0]
        rng = random.Random(len(free))
        rng.shuffle(free)
        free.sort(key=lambda cr: -max(run_len(cr[0], cr[1], d) for d in dirs))
        names = ["מסדרון צפוני", "מסדרון מערבי", "אגף המעבדה", "מסדרון דרומי", "מחסן"]
        for c, r in free:
            if len(cams) >= NUM_CAMERAS:
                break
            if all(math.hypot(c - k["cell"][0], r - k["cell"][1]) > 6 for k in cams):
                cams.append(make(c, r, names[len(cams) - 3]))
        return cams

    def enter_camera_room(self):
        self.in_camera_room = True
        self.room_timer = 0.0
        self.cam_focus = None
        self.door_cooldown = 1.2
        if self.room_intro_done:
            # חזרה לחדר: בלי הודעות הפתיחה, המצלמות נשארות
            self.player.hidden = True
            self.forced_turn_active = False
            self.build_room()
            self.player.x = (ROOM_COLS // 2 + 0.5) * CELL
            self.player.y = (ROOM_ROWS - 2 + 0.15) * CELL
            self.player.angle = -math.pi / 2
            m = self.monster
            if not TEST_NO_MONSTER and m.awake:
                m.state = "wander"
                m.target_cell = None
                m.path = []
            return
        self.player.hidden = True          # בחדר אתה מחוץ למבוך - השומר לא יכול לראות אותך
        self.forced_turn_active = False
        self.message_timer = 0
        self.cameras = self.pick_cameras()
        self.cam_feeds = {}
        self.build_room()
        # נכנסים לחדר: עומדים ליד הדלת ומביטים פנימה, אל שולחן הבקרה
        self.player.x = (ROOM_COLS // 2 + 0.5) * CELL
        self.player.y = (ROOM_ROWS - 2 + 0.15) * CELL
        self.player.angle = -math.pi / 2
        self.room_monitor_screens = {}
        m = self.monster
        m.wander_points = [k["cell"] for k in self.cameras]
        if TEST_NO_MONSTER:
            return
        m.awake = True
        m.state = "wander"
        m.target_cell = None
        m.path = []

    def exit_camera_room(self):
        """יוצאים מהחדר בחזרה למבוך - עומדים מול הדלת, עם הגב אליה"""
        self.in_camera_room = False
        self.cam_focus = None
        self.player.hidden = False
        wx, wy, wd = self.exit_wall
        ex, ey = wx - wd[0], wy - wd[1]
        self.player.x = ex * CELL + CELL / 2 - wd[0] * CELL * 0.3
        self.player.y = ey * CELL + CELL / 2 - wd[1] * CELL * 0.3
        self.player.angle = math.atan2(-wd[1], -wd[0])
        self.door_open = 1.0
        self.door_cooldown = 1.5
        self.effective_light_radius = LIGHT_RADIUS
        self.message = "תמצא את המפלצת ותצלם אותה (Shift)"
        self.message_timer = 3.0

    # ---------------- יומן, מצלמה ותמונות ----------------
    def journal_button_rect(self):
        r = pygame.Rect(0, 0, 290, 54)
        r.center = (WIDTH // 2, HEIGHT - 74)
        return r

    def place_journal_button_rect(self):
        r = pygame.Rect(0, 0, 420, 56)
        r.center = (WIDTH // 2, HEIGHT - 52)
        return r

    def photo_button_rect(self):
        r = pygame.Rect(0, 0, 290, 50)
        r.bottomright = (WIDTH - 14, HEIGHT - 56)
        return r

    def close_photo_rect(self):
        r = pygame.Rect(0, 0, 180, 50)
        r.center = (WIDTH // 2, HEIGHT - 40)
        return r

    def show_journal_button(self):
        return (self.in_camera_room and self.room_intro_done and not self.journal_on_desk
                and not self.journal_open and self.cam_focus is None)

    def show_photo_button(self):
        return bool(self.photos) and not self.photo_view and not self.journal_open and self.cam_focus is None

    def place_journal_on_desk(self):
        self.journal_open = False
        self.journal_on_desk = True
        self.camera_on_desk = True
        self.build_room()
        self.audio.play_fx("snd_stinger")
        self.message = "מצלמה הופיעה על השולחן..."
        self.message_timer = 3.0

    def near_desk_camera(self):
        if not (self.in_camera_room and self.camera_on_desk):
            return False
        cx_, cy_ = getattr(self, "desk_camera_pos", (0, 0))
        return math.hypot(cx_ - self.player.x, cy_ - self.player.y) < CAMERA_TAKE_DIST

    def take_camera(self):
        self.camera_on_desk = False
        self.has_camera = True
        self.build_room()
        self.mission_text = "לצלם את המפלצת ולברוח לחדר"
        self.banner = ("צריך לצלם את המפלצת", "ולברוח בחזרה לחדר!  (Shift - צילום)", (255, 205, 90), 4.5)
        self.audio.play_fx("snd_complete")

    def take_photo(self):
        if not self.has_camera or self.photo_view or self.journal_open or self.cam_focus is not None:
            return
        if self.game_over or self.win or self.jumpscare_active or self.entering or self.leaving_room:
            return
        self.photo_pending = True     # התמונה עצמה נלכדת בציור הבא, לפני ה-HUD
        self.flash_timer = 0.3
        self.audio.play_fx("snd_shutter")

    def capture_photo(self):
        """שומר עותק של מה שרואים עכשיו (בלי ה-HUD) ובודק אם המפלצת בתמונה"""
        self.photo_pending = False
        img = self.screen.copy()
        has_monster = False
        if not self.in_camera_room and self.monster.awake and not TEST_NO_MONSTER:
            proj = self.monster_projection()
            if proj is not None and proj["light"] > 0.05:
                has_monster = self.monster_visible_at(proj["x"], proj["corr"]) and 0 <= proj["x"] < WIDTH
        self.photos.append({"img": img, "monster": has_monster,
                            "where": "חדר הבקרה" if self.in_camera_room else "המבוך"})
        self.message = "צילמת!"
        self.message_timer = 1.5

    def draw_flash(self):
        if self.flash_timer > 0:
            f = pygame.Surface((WIDTH, HEIGHT))
            f.fill((255, 255, 255))
            f.set_alpha(int(255 * min(1.0, self.flash_timer / 0.3)))
            self.screen.blit(f, (0, 0))

    def draw_banner(self):
        if not self.banner:
            return
        title, sub, color, left = self.banner
        alpha = min(1.0, left / 0.5, (4.5 - left) / 0.3 if left < 4.5 else 1.0)
        band = pygame.Surface((WIDTH, 190), pygame.SRCALPHA)
        band.fill((0, 0, 0, int(185 * alpha)))
        pygame.draw.line(band, (*color, int(200 * alpha)), (0, 0), (WIDTH, 0), 3)
        pygame.draw.line(band, (*color, int(200 * alpha)), (0, 187), (WIDTH, 187), 3)
        self.screen.blit(band, (0, HEIGHT // 2 - 105))
        t1 = self.font_huge.render(rtl(title), True, color)
        if t1.get_width() > WIDTH - 40:
            k = (WIDTH - 40) / t1.get_width()
            t1 = pygame.transform.smoothscale(t1, (int(t1.get_width() * k), int(t1.get_height() * k)))
        t1.set_alpha(int(255 * alpha))
        self.screen.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35)))
        t2 = self.font_button.render(rtl(sub), True, (235, 235, 235))
        t2.set_alpha(int(255 * alpha))
        self.screen.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))

    def draw_journal_page(self):
        """היומן הפתוח - עמוד אחד בכתב ידו של המדען"""
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        self.screen.blit(dim, (0, 0))
        book = pygame.Rect(0, 0, 560, 430)
        book.center = (WIDTH // 2, HEIGHT // 2 - 40)
        pygame.draw.rect(self.screen, (60, 32, 18), book.inflate(28, 22), border_radius=10)      # כריכה
        pygame.draw.rect(self.screen, (90, 50, 28), book.inflate(28, 22), 3, border_radius=10)
        page = pygame.Surface(book.size)
        page.fill((226, 210, 172))
        rng = random.Random(21)
        for y in range(book.h):  # הכתמה והצהבה של נייר ישן
            f = abs(y - book.h / 2) / (book.h / 2)
            pygame.draw.line(page, lerp_color((230, 216, 180), (196, 176, 130), f ** 2), (0, y), (book.w, y))
        for y in range(92, book.h - 20, 34):  # שורות
            pygame.draw.line(page, (176, 160, 130), (30, y), (book.w - 30, y), 1)
        pygame.draw.line(page, (190, 90, 80), (book.w - 52, 20), (book.w - 52, book.h - 20), 1)  # שוליים
        for cx_, cy_ in ((60, 380), (book.w - 90, 395), (110, 36)):  # כתמי דם יבש - בשוליים, לא על הטקסט
            for k in range(6):
                pygame.draw.circle(page, (120 - k * 6, 20, 18), (cx_ + rng.randint(-14, 14), cy_ + rng.randint(-10, 10)),
                                   rng.randint(2, 7))
        title = self.font_big.render(rtl("יומן המדען"), True, (70, 30, 20))
        page.blit(title, title.get_rect(center=(book.w // 2, 46)))
        y = 98
        for para in JOURNAL_PAGE_TEXT:
            red = para.startswith("!")
            para = para.lstrip("!")
            for line in self.wrap_text(para, self.font_story, book.w - 110):
                img = self.font_story.render(rtl(line), True, (140, 16, 16) if red else (40, 26, 20))
                r = img.get_rect(topright=(book.w - 64, y))
                page.blit(img, r)
                if red:
                    pygame.draw.line(page, (140, 16, 16), (r.left, r.bottom), (r.right, r.bottom), 2)
                y += 34
        self.screen.blit(page, book)
        hover = self.place_journal_button_rect().collidepoint(pygame.mouse.get_pos())
        self.draw_button(self.place_journal_button_rect(), "לשים את היומן על השולחן", hover)

    def draw_photo_view(self):
        """התמונה האחרונה שצילמת - בתוך מסגרת של תמונת פולארויד"""
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 215))
        self.screen.blit(dim, (0, 0))
        idx = self.photo_index if 0 <= self.photo_index < len(self.photos) else len(self.photos) - 1
        ph = self.photos[idx]
        img = pygame.transform.smoothscale(ph["img"], (600, 400))
        frame = pygame.Rect(0, 0, 640, 486)
        frame.center = (WIDTH // 2, HEIGHT // 2 - 30)
        pygame.draw.rect(self.screen, (10, 10, 10), frame.move(6, 8), border_radius=4)
        pygame.draw.rect(self.screen, (236, 232, 222), frame, border_radius=4)
        self.screen.blit(img, (frame.x + 20, frame.y + 20))
        cap = self.font_story.render(rtl("תמונה %d - %s" % (idx + 1, ph["where"])), True, (40, 40, 40))
        self.screen.blit(cap, cap.get_rect(center=(frame.centerx, frame.bottom - 32)))
        # רמז קטן מעל התמונה: האם המפלצת בתמונה, ומה עושים עכשיו
        if ph["monster"] and not self.in_camera_room:
            note, col = "יש לך תמונה של המפלצת! עכשיו ברח לחדר הבקרה", (255, 215, 120)
        elif ph["monster"]:
            note, col = "זאת ההוכחה...", (150, 255, 170)
        else:
            note, col = "המפלצת לא בתמונה... נסה שוב", (255, 140, 140)
        nt = self.font_story.render(rtl(note), True, col)
        self.screen.blit(nt, nt.get_rect(center=(WIDTH // 2, frame.top - 2 - nt.get_height() // 2)))
        hover = self.close_photo_rect().collidepoint(pygame.mouse.get_pos())
        self.draw_button(self.close_photo_rect(), "סגור", hover)

    def draw_overlays(self):
        """שכבות שמשותפות למבוך ולחדר: הבזק, הודעה גדולה, כפתורים, יומן ותמונה"""
        self.draw_flash()
        self.draw_banner()
        if self.show_journal_button():
            r = self.journal_button_rect()
            self.draw_button(r, "לקרוא את היומן", r.collidepoint(pygame.mouse.get_pos()))
        if self.show_photo_button() and not self.game_over and not self.win:
            r = self.photo_button_rect()
            self.draw_button(r, "לראות את התמונה", r.collidepoint(pygame.mouse.get_pos()))
        if self.journal_open:
            self.draw_journal_page()
        if self.photo_view and self.photos:
            self.draw_photo_view()

    def overlay_click(self, pos):
        """לחיצה על כפתורי היומן/התמונה. מחזיר True אם הלחיצה טופלה"""
        if self.photo_view:
            if self.close_photo_rect().collidepoint(pos):
                self.photo_view = False
            return True
        if self.journal_open:
            if self.place_journal_button_rect().collidepoint(pos):
                self.place_journal_on_desk()
            return True
        if self.show_journal_button() and self.journal_button_rect().collidepoint(pos):
            self.journal_open = True
            return True
        if self.show_photo_button() and self.photo_button_rect().collidepoint(pos):
            self.photo_view = True
            self.win_view_t = 0.0
            # בחדר הבקרה מראים את התמונה הכי טובה - האחרונה שבה רואים את המפלצת
            self.photo_index = len(self.photos) - 1
            if self.in_camera_room:
                for i in range(len(self.photos) - 1, -1, -1):
                    if self.photos[i]["monster"]:
                        self.photo_index = i
                        break
            return True
        return False

    # ======================= סוף המשחק =======================
    def start_ending(self):
        self.ending_active = True
        self.ending_t = 0.0
        self.photo_view = False
        self.win = True                   # האודיו מזהה ניצחון ומעמעם את המוזיקה
        self.audio.play_fx("snd_complete")
        rng = random.Random()
        self.confetti = [{"x": rng.uniform(0, WIDTH), "y": rng.uniform(-HEIGHT, 0),
                          "vy": rng.uniform(70, 170), "vx": rng.uniform(-30, 30),
                          "a": rng.uniform(0, 6.28), "va": rng.uniform(-6, 6),
                          "c": rng.choice(((255, 215, 90), (255, 255, 255), (120, 220, 255), (255, 120, 140),
                                           (140, 255, 160)))} for _ in range(140)]
        self.newspaper = self.build_newspaper()

    def ending_paper_start(self):
        return END_WIN_TIME + END_FADE_TIME + END_MONTH_TIME

    def ending_restart_ready(self):
        return self.ending_t > self.ending_paper_start() + END_PAPER_SPIN + 2.0

    def ending_button_rect(self):
        r = pygame.Rect(0, 0, 240, 56)
        r.center = (WIDTH // 2, HEIGHT - 36)
        return r

    def update_ending(self, dt):
        prev = self.ending_t
        self.ending_t += dt
        for c in self.confetti:
            c["y"] += c["vy"] * dt
            c["x"] += c["vx"] * dt + math.sin(self.ending_t * 3 + c["a"]) * 20 * dt
            c["a"] += c["va"] * dt
        ps = self.ending_paper_start()
        if prev < ps + END_PAPER_SPIN <= self.ending_t:
            self.audio.play_fx("snd_stinger")   # "באם!" כשהעיתון נוחת

    def draw_ending(self):
        t = self.ending_t
        scr = self.screen
        ps = self.ending_paper_start()
        if t < END_WIN_TIME + END_FADE_TIME:
            # --- מסך ניצחון מעל החדר ---
            self.view_room = True
            saved = self.effective_light_radius
            self.effective_light_radius = ROOM_LIGHT_RADIUS
            self.render_world()
            self.view_room = False
            self.effective_light_radius = saved
            dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 170))
            scr.blit(dim, (0, 0))
            k = min(1.0, t / 0.6)
            # תג בלש מוזהב
            self.draw_detective_badge(WIDTH // 2, 160, 62 * (0.6 + 0.4 * k), t)
            pop = 1 + 0.4 * max(0.0, 1 - t / 0.35)
            title = self.font_huge.render(rtl("ניצחת!"), True, (255, 215, 90))
            title = pygame.transform.smoothscale(title, (int(title.get_width() * pop), int(title.get_height() * pop)))
            shadow = self.font_huge.render(rtl("ניצחת!"), True, (60, 30, 0))
            shadow = pygame.transform.smoothscale(shadow, title.get_size())
            scr.blit(shadow, shadow.get_rect(center=(WIDTH // 2 + 4, 300 + 5)))
            scr.blit(title, title.get_rect(center=(WIDTH // 2, 300)))
            if t > 0.9:
                sub = self.font_big.render(rtl("אתה הבלש הכי טוב השנה!"), True, (255, 255, 255))
                sub.set_alpha(int(255 * min(1.0, (t - 0.9) / 0.5)))
                scr.blit(sub, sub.get_rect(center=(WIDTH // 2, 380)))
            if t > 1.8:
                sub2 = self.font_story.render(rtl("צילמת את המפלצת והבאת את ההוכחה לחדר הבקרה"), True, (200, 210, 220))
                sub2.set_alpha(int(255 * min(1.0, (t - 1.8) / 0.5)))
                scr.blit(sub2, sub2.get_rect(center=(WIDTH // 2, 430)))
            for c in self.confetti:
                if 0 <= c["y"] <= HEIGHT:
                    w = 4 + 3 * abs(math.sin(c["a"]))
                    pygame.draw.rect(scr, c["c"], (c["x"], c["y"], w, 7))
            # הכל נעלם
            if t > END_WIN_TIME:
                fade = pygame.Surface((WIDTH, HEIGHT))
                fade.set_alpha(int(255 * min(1.0, (t - END_WIN_TIME) / END_FADE_TIME)))
                scr.blit(fade, (0, 0))
        elif t < ps:
            # --- "כעבור חודש..." על מסך שחור ---
            scr.fill((0, 0, 0))
            lt = t - END_WIN_TIME - END_FADE_TIME
            a = min(1.0, lt / 0.8, (END_MONTH_TIME - lt) / 0.8)
            txt = self.font_big.render(rtl("כעבור חודש..."), True, (230, 230, 230))
            txt.set_alpha(int(255 * max(0.0, a)))
            scr.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        else:
            # --- העיתון מסתובב ונכנס ---
            scr.fill((10, 10, 12))
            lt = t - ps
            k = min(1.0, lt / END_PAPER_SPIN)
            ease = 1 - (1 - k) ** 3
            angle = (1 - ease) * 720 - 3
            scale = 0.05 + 0.95 * ease
            paper = pygame.transform.rotozoom(self.newspaper, angle, scale)
            scr.blit(paper, paper.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 14)))
            if self.ending_restart_ready():
                hover = self.ending_button_rect().collidepoint(pygame.mouse.get_pos())
                self.draw_button(self.ending_button_rect(), "שחק שוב", hover)

    def draw_detective_badge(self, cx, cy, r, t):
        """תג בלש: כוכב מוזהב עם זכוכית מגדלת"""
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5 + math.sin(t * 2) * 0.05
            rr = r if i % 2 == 0 else r * 0.48
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        self.soft_glow(cx, cy, r * 2.2, (255, 200, 80), 70)
        pygame.draw.polygon(self.screen, (120, 80, 10), [(x + 3, y + 4) for x, y in pts])
        pygame.draw.polygon(self.screen, (240, 190, 60), pts)
        pygame.draw.polygon(self.screen, (255, 236, 150), pts, 3)
        pygame.draw.circle(self.screen, (40, 30, 10), (int(cx - r * 0.08), int(cy - r * 0.08)), int(r * 0.24), 4)
        pygame.draw.line(self.screen, (40, 30, 10), (cx + r * 0.08, cy + r * 0.08), (cx + r * 0.3, cy + r * 0.3), 5)

    def build_prison_photo(self, w, h):
        """התמונה בעיתון: המפלצת בתא כלא, ידיה כבולות לקיר באזיקים ושלשלאות"""
        surf = pygame.Surface((w, h))
        rng = random.Random(77)
        # קיר אבן
        surf.fill((40, 38, 36))
        bh, bw = 22, 44
        for row in range(0, h, bh):
            off = bw // 2 if (row // bh) % 2 else 0
            for x in range(-bw, w + bw, bw):
                tone = rng.randint(78, 104)
                pygame.draw.rect(surf, (tone, tone - 4, tone - 8), (x + off + 2, row + 2, bw - 4, bh - 4))
        floor_y = int(h * 0.84)
        pygame.draw.rect(surf, (52, 48, 44), (0, floor_y, w, h - floor_y))
        pygame.draw.line(surf, (30, 28, 26), (0, floor_y), (w, floor_y), 3)

        # זרקור על המפלצת - שיראו אותה טוב בתמונה
        self.soft_glow(w // 2, int(h * 0.45), int(h * 0.55), (255, 240, 220), 90, target=surf)
        cx = w // 2
        H = h * 0.68
        foot = floor_y + 4
        hip = foot - H * 0.46
        sh = foot - H * 0.76
        dark, mid, hi = (40, 10, 14), (90, 26, 32), (140, 54, 60)

        def limb(a, b, wdt):
            pygame.draw.line(surf, dark, a, b, int(wdt))
            pygame.draw.line(surf, mid, (a[0] - 1, a[1]), (b[0] - 1, b[1]), max(1, int(wdt * 0.55)))
            pygame.draw.circle(surf, dark, (int(b[0]), int(b[1])), int(wdt * 0.6))

        def chain(a, b, links=9):
            for i in range(links):
                t0 = i / links
                x = a[0] + (b[0] - a[0]) * t0
                y = a[1] + (b[1] - a[1]) * t0 + math.sin(t0 * math.pi) * 6
                pygame.draw.ellipse(surf, (150, 150, 156), (x - 4, y - 3, 8, 6), 2)

        # טבעות ברזל בקיר
        rings = {s: (cx + s * H * 0.5, sh - H * 0.27) for s in (-1, 1)}
        for s, (rx, ry) in rings.items():
            pygame.draw.circle(surf, (30, 30, 32), (int(rx), int(ry)), 9)
            pygame.draw.circle(surf, (160, 160, 166), (int(rx), int(ry)), 9, 3)
        # רגליים + כבלים בקרסוליים
        for s in (-1, 1):
            hp = (cx + s * H * 0.05, hip)
            kn = (cx + s * H * 0.09, foot - H * 0.22)
            ft = (cx + s * H * 0.08, foot - 4)
            limb(hp, kn, H * 0.04)
            limb(kn, ft, H * 0.032)
            pygame.draw.rect(surf, (140, 140, 146), (ft[0] - 7, ft[1] - 12, 14, 7), border_radius=2)
            chain((ft[0], ft[1] - 8), (cx + s * H * 0.26, foot - 2), 6)
        # גוף צר עם צלעות
        pygame.draw.polygon(surf, dark, [(cx - H * 0.15, sh), (cx + H * 0.15, sh), (cx + H * 0.07, hip), (cx - H * 0.07, hip)])
        pygame.draw.polygon(surf, mid, [(cx - H * 0.1, sh + 4), (cx + H * 0.1, sh + 4), (cx + H * 0.05, hip - 4), (cx - H * 0.05, hip - 4)])
        for i in range(5):
            yy = sh + 10 + i * (hip - sh - 20) / 5
            ww = H * (0.12 - i * 0.012)
            pygame.draw.arc(surf, (210, 200, 186), (cx - ww, yy, ww * 2, 12), math.pi * 0.1, math.pi * 0.9, 2)
        # ידיים מורמות, כבולות לקיר באזיקים
        for s in (-1, 1):
            sp = (cx + s * H * 0.14, sh + 4)
            el = (cx + s * H * 0.27, sh - H * 0.06)
            wr = (cx + s * H * 0.34, sh - H * 0.22)
            limb(sp, el, H * 0.036)
            limb(el, wr, H * 0.03)
            for k in (-1, 0, 1):  # טפרים
                pygame.draw.line(surf, (220, 214, 200), wr, (wr[0] + s * 6 + k * 4, wr[1] - 12), 2)
            pygame.draw.rect(surf, (20, 20, 22), (wr[0] - 8, wr[1] - 3, 16, 11), border_radius=3)   # אזיק
            pygame.draw.rect(surf, (175, 175, 182), (wr[0] - 7, wr[1] - 2, 14, 9), border_radius=3)
            chain(wr, rings[s], 7)
        # ראש מורכן מעט
        self.draw_monster_head(cx, sh - H * 0.11, H * 0.3, 0.8, 0.8, target=surf)
        # סורגי התא מקדימה
        for x in range(18, w, w // 6):
            pygame.draw.rect(surf, (12, 12, 14), (x, 0, 7, h))
            pygame.draw.line(surf, (120, 120, 126), (x + 2, 0), (x + 2, h), 2)
        pygame.draw.rect(surf, (12, 12, 14), (0, int(h * 0.02), w, 8))
        pygame.draw.rect(surf, (12, 12, 14), (0, int(h * 0.9), w, 10))
        # הדפסת עיתון: שחור-לבן, גרגר ומעט דהייה
        surf = pygame.transform.grayscale(surf)
        surf.fill((30, 30, 30), special_flags=pygame.BLEND_RGB_ADD)         # הבהרה קלה
        surf.fill((236, 228, 210), special_flags=pygame.BLEND_RGB_MULT)
        for _ in range(w * h // 40):
            x, y = rng.randrange(w), rng.randrange(h)
            v = surf.get_at((x, y))[0]
            n = rng.randint(-26, 26)
            surf.set_at((x, y), (max(0, min(255, v + n)),) * 3)
        return surf

    def build_newspaper(self):
        """עמוד ראשון של עיתון: כותרת ענקית, תמונת המפלצת בכלא וטורי טקסט"""
        W, H = 640, 500
        paper = pygame.Surface((W, H))
        paper.fill((236, 230, 212))
        rng = random.Random(5)
        for y in range(H):  # נייר מצהיב בשוליים
            f = abs(y - H / 2) / (H / 2)
            pygame.draw.line(paper, lerp_color((238, 232, 214), (214, 204, 176), f ** 3), (0, y), (W, y))
        ink = (24, 22, 20)
        mast = self.font_huge.render(rtl("חדשות המתחם"), True, ink)
        mast = pygame.transform.smoothscale(mast, (int(mast.get_width() * 0.75), int(mast.get_height() * 0.75)))
        paper.blit(mast, mast.get_rect(center=(W // 2, 42)))
        pygame.draw.line(paper, ink, (20, 76), (W - 20, 76), 3)
        info = self.font_small.render(rtl("גיליון מיוחד  |  מהדורת בוקר  |  מחיר: 5 שקלים"), True, ink)
        paper.blit(info, info.get_rect(center=(W // 2, 90)))
        pygame.draw.line(paper, ink, (20, 102), (W - 20, 102), 1)
        head = self.font_huge.render(rtl("המפלצת נתפסה!"), True, (150, 14, 14))
        head = pygame.transform.smoothscale(head, (int(head.get_width() * 0.62), int(head.get_height() * 0.62)))
        paper.blit(head, head.get_rect(center=(W // 2, 134)))
        photo = self.build_prison_photo(300, 220)
        ph_rect = photo.get_rect(topleft=(24, 166))
        pygame.draw.rect(paper, ink, ph_rect.inflate(6, 6))
        paper.blit(photo, ph_rect)
        cap = self.font_small.render(rtl("המפלצת בתא הכלא, כבולה לקיר באזיקים"), True, ink)
        paper.blit(cap, cap.get_rect(midtop=(ph_rect.centerx, ph_rect.bottom + 8)))
        # טקסט הכתבה (בצד ימין)
        col_r, col_l = W - 24, ph_rect.right + 20
        y = 168
        body = ("בזכות הבלש הכי טוב השנה, שנכנס לבדו למתחם הנטוש וצילם את המפלצת, "
                "הצליחה המשטרה ללכוד את היצור שהטיל אימה על כל האזור. "
                "המפלצת הועברה לכלא מאובטח, שם היא כבולה לקיר בשלשלאות.")
        for line in self.wrap_text(body, self.font_small, col_r - col_l):
            img = self.font_small.render(rtl(line), True, ink)
            paper.blit(img, img.get_rect(topright=(col_r, y)))
            y += 22
        y += 8
        while y < H - 60:  # עוד "טקסט" אפור בטורים
            w_ = rng.randint(int((col_r - col_l) * 0.6), col_r - col_l)
            pygame.draw.line(paper, (120, 116, 108), (col_r - w_, y), (col_r, y), 3)
            y += 12
        pygame.draw.line(paper, ink, (20, H - 66), (W - 20, H - 66), 1)
        y = H - 54
        while y < H - 16:  # טורים בתחתית העמוד
            for c0 in range(24, W - 24, 155):
                w_ = rng.randint(100, 140)
                pygame.draw.line(paper, (120, 116, 108), (c0, y), (c0 + w_, y), 3)
            y += 12
        pygame.draw.rect(paper, (170, 160, 140), paper.get_rect(), 2)
        return paper.convert_alpha()   # כדי שבזמן הסיבוב לא יהיו פינות שחורות

    def update_camera_room(self, dt):
        prev = self.room_timer
        self.room_timer += dt
        if self.message_timer > 0:
            self.message_timer -= dt
        if not self.room_intro_done:
            if prev < 1.6 <= self.room_timer:
                self.audio.play_fx("snd_complete")
            if prev < 7.0 <= self.room_timer:
                self.audio.play_fx("snd_stinger")
                self.mission_text = "לצלם את המפלצת"
            if self.room_timer > 11.5:
                self.room_intro_done = True
        self.door_cooldown = max(0.0, self.door_cooldown - dt)
        if self.banner:
            t_, s_, c_, left = self.banner
            self.banner = (t_, s_, c_, left - dt) if left - dt > 0 else None

        # יציאה מהחדר חזרה למבוך (רק אחרי שלקחת את המצלמה)
        if self.leaving_room > 0:
            self.leaving_room += dt
            if self.leaving_room >= ENTER_FADE:
                self.leaving_room = 0.0
                self.exit_camera_room()
            return
        if self.photo_view and 0 <= self.photo_index < len(self.photos) and self.photos[self.photo_index]["monster"]:
            self.win_view_t += dt
            if self.win_view_t >= PHOTO_WIN_DELAY:
                self.start_ending()
                return
        if self.journal_open or self.photo_view:
            return
        rd = self.room_door
        door_x = (rd[0] + 0.5) * CELL
        door_y = rd[1] * CELL - CELL * 0.2
        d_door = math.hypot(door_x - self.player.x, door_y - self.player.y)
        if self.has_camera and self.door_cooldown <= 0:
            want = d_door < DOOR_OPEN_DIST
            if want and self.door_open == 0.0:
                self.audio.play_fx("snd_creak")
            step = DOOR_OPEN_SPEED * dt
            target = 1.0 if want else 0.0
            self.door_open = max(0.0, min(1.0, self.door_open + max(-step, min(step, target - self.door_open))))
            idx = int(round(self.door_open * (DOOR_FRAMES - 1)))
            self.wall_textures["door"], self.wall_textures["door_glow"] = self.door_frames[idx]
            self.wall_textures["door_room"], self.wall_textures["door_room_glow"] = self.door_frames_room[idx]
            if self.door_open > 0.85 and d_door < 26:
                self.leaving_room = 0.001
                return
        self.effective_light_radius = CAM_LIGHT_RADIUS
        self.step_monster(dt)

        # הדלת נסגרת מאחוריך (כל עוד אין לך מצלמה)
        if self.door_open > 0 and not self.has_camera:
            self.door_open = max(0.0, self.door_open - DOOR_OPEN_SPEED * dt)
            idx = int(round(self.door_open * (DOOR_FRAMES - 1)))
            self.wall_textures["door"], self.wall_textures["door_glow"] = self.door_frames[idx]
            self.wall_textures["door_room"], self.wall_textures["door_room_glow"] = self.door_frames_room[idx]

        # הליכה בחדר (כשלא מסתכלים על מסך מוגדל)
        if self.cam_focus is None and self.room_timer > 0.6 and not self.journal_open and not self.photo_view:
            keys = pygame.key.get_pressed()
            p = self.player
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                p.angle -= ROT_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                p.angle += ROT_SPEED
            mx = my = 0.0
            for k1, k2, off, sign in ((pygame.K_UP, pygame.K_w, 0, 1), (pygame.K_DOWN, pygame.K_s, 0, -1),
                                      (pygame.K_q, pygame.K_q, -math.pi / 2, 1), (pygame.K_e, pygame.K_e, math.pi / 2, 1)):
                if keys[k1] or keys[k2]:
                    mx += math.cos(p.angle + off) * MOVE_SPEED * sign
                    my += math.sin(p.angle + off) * MOVE_SPEED * sign
            p.try_move(mx, my, self.room_grid, [pr["box"] for pr in self.room_props if pr.get("solid")])

    def render_cam_feed(self, idx, size):
        """מצייר את המבוך מנקודת המבט של מצלמה, ומוסיף מראה של מצלמת אבטחה"""
        cam = self.cameras[idx]
        p = self.player
        saved = (p.x, p.y, p.angle, self.light_boost, self.current_spot, self.depth_buffer)
        p.x, p.y, p.angle = cam["x"], cam["y"], cam["angle"]
        self.light_boost = False
        self.current_spot = None
        self.render_world()
        p.x, p.y, p.angle, self.light_boost, self.current_spot, self.depth_buffer = saved

        img = pygame.transform.smoothscale(self.screen, size)
        img = pygame.transform.grayscale(img)
        img.fill((175, 255, 195), special_flags=pygame.BLEND_RGB_MULT)   # גוון ירקרק של מצלמת לילה
        img.fill((20, 30, 22), special_flags=pygame.BLEND_RGB_ADD)
        w, h = size
        if not hasattr(self, "_scan_cache"):
            self._scan_cache = {}
        lines = self._scan_cache.get(size)
        if lines is None:
            lines = pygame.Surface(size, pygame.SRCALPHA)
            for y in range(0, h, 3):
                pygame.draw.line(lines, (0, 0, 0, 70), (0, y), (w, y))
            self._scan_cache[size] = lines
        img.blit(lines, (0, 0))
        if random.random() < 0.08:  # הפרעה רגעית
            gy = random.randint(0, h - 6)
            img.fill((40, 60, 45), (0, gy, w, random.randint(2, 6)), special_flags=pygame.BLEND_RGB_ADD)
        for _ in range(int(w * h / 900)):
            x, y = random.randrange(w), random.randrange(h)
            v = random.randint(60, 200)
            img.set_at((x, y), (v, v, v))
        return img

    def draw_cam_overlay(self, surf, idx, big=False):
        """טקסט על המסך: מספר מצלמה, שם המקום, שעון ונקודת הקלטה"""
        cam = self.cameras[idx]
        font = self.font_story if big else self.font_small
        w, h = surf.get_size()
        label = font.render(rtl("מצלמה %d - %s" % (idx + 1, cam["name"])), True, (210, 255, 220))
        surf.blit(label, (w - label.get_width() - 8, 6))
        secs = int(pygame.time.get_ticks() / 1000) + idx * 1373
        clock = font.render("03:%02d:%02d" % ((secs // 60) % 60, secs % 60), True, (210, 255, 220))
        surf.blit(clock, (8, h - clock.get_height() - 5))
        if (pygame.time.get_ticks() // 600) % 2 == 0:
            rec = font.render("REC", True, (255, 90, 90))
            rx = w - rec.get_width() - 10
            ry = h - rec.get_height() - 5
            surf.blit(rec, (rx, ry))
            pygame.draw.circle(surf, (255, 40, 40), (rx - 9, ry + rec.get_height() // 2), 6 if big else 4)

    # ---------------- חדר הבקרה התלת-ממדי ----------------
    def build_room(self):
        """בונה את חדר הבקרה: מפה קטנה של קירות, ורהיטים תלת-ממדיים (קופסאות) בתוכה"""
        g = [[1] * ROOM_COLS for _ in range(ROOM_ROWS)]
        for r in range(1, ROOM_ROWS - 1):
            for c in range(1, ROOM_COLS - 1):
                g[r][c] = 0
        self.room_grid = g
        mid = ROOM_COLS // 2
        self.room_door = (mid, ROOM_ROWS - 1, (0, 1))           # הדלת שדרכה נכנסת - בקיר שמאחוריך
        self.room_decals = {(0, 1): "clock", (0, 2): "room_sign", (0, 4): "map",
                            (ROOM_COLS - 1, 2): "rack", (ROOM_COLS - 1, 3): "rack",
                            (1, ROOM_ROWS - 1): "extinguisher"}
        self.wall_textures["map"] = self.build_map_texture(self.wall_textures["concrete"])

        cx = (mid + 0.5) * CELL
        wy = CELL  # הקיר העליון (שהשולחן צמוד אליו)
        props = []

        def add(box, z, col, top=None, layer=0, group="desk", solid=False, screen=None, emit=None):
            props.append({"box": box, "z": z, "col": col, "top": top or col, "layer": layer,
                          "group": group, "solid": solid, "screen": screen, "emit": emit})

        # שולחן
        add((cx - 60, wy + 1, cx + 60, wy + 40), (0, 24), (46, 48, 54), top=(104, 78, 56), solid=True)
        add((cx - 60, wy + 40, cx + 60, wy + 42), (21, 24), (110, 84, 60), layer=1)   # קצה עץ קדמי
        # מסכים: שלושה על השולחן ושלושה מעליהם
        for k in range(3):
            xc = cx + (k - 1) * 31
            add((xc - 4, wy + 8, xc + 4, wy + 16), (24, 27), (30, 31, 35), layer=1)          # רגל
            add((xc - 14, wy + 8, xc + 14, wy + 15), (27, 45), (34, 36, 40), layer=2, screen=k + 3)
            add((xc - 14, wy + 6, xc + 14, wy + 13), (45.5, 63), (34, 36, 40), layer=2, screen=k)
        # חפצים על השולחן
        add((cx - 22, wy + 24, cx + 22, wy + 33), (24, 25.6), (24, 25, 28), top=(58, 60, 66), layer=3)  # מקלדת
        add((cx + 30, wy + 26, cx + 34, wy + 30), (24, 25.3), (40, 42, 48), layer=3)                      # עכבר
        add((cx + 40, wy + 24, cx + 46, wy + 30), (24, 31), (150, 140, 128), top=(40, 22, 12), layer=3)   # ספל
        add((cx - 54, wy + 20, cx - 34, wy + 34), (24, 25), (200, 196, 180), layer=3)                     # ניירות
        if self.journal_on_desk:
            add((cx - 52, wy + 21, cx - 38, wy + 31), (25, 26.8), (110, 70, 38), top=(124, 80, 44), layer=4)  # היומן
        if self.camera_on_desk:
            camx, camy = cx + 30, wy + 19
            add((camx - 7, camy - 4, camx + 7, camy + 4), (24, 31), (22, 22, 26), top=(40, 40, 46), layer=4)   # גוף המצלמה
            add((camx - 3, camy + 4, camx + 3, camy + 8), (25.5, 29.5), (70, 72, 80), layer=5)               # עדשה
            add((camx + 3, camy - 3, camx + 6, camy), (31, 32.2), (200, 30, 30), layer=5)                     # כפתור
            self.desk_camera_pos = (camx, camy)
        # ---- מנורת שולחן בקצה הימני ----
        add((210, 70, 218, 78), (24, 25), (40, 42, 46), layer=3)
        add((213, 73, 215, 75), (25, 36), (70, 72, 78), layer=4)
        add((208, 71, 220, 81), (36, 39.5), (30, 60, 52), top=(40, 80, 70), layer=5, emit=(255, 236, 180))
        # פח אשפה ליד השולחן
        add((228, 70, 238, 80), (0, 9), (58, 60, 66), top=(20, 20, 22), group="bin")
        # ---- ארון תיוק: מגירות וידיות ----
        for z in (13.2, 26.6):
            add((CELL + 26, 3.0 * CELL + 2, CELL + 26.6, 3.6 * CELL - 2), (z, z + 0.7), (30, 32, 36), group="cab", layer=1)
        for z in (6, 19.5, 33):
            add((CELL + 26, 3.15 * CELL, CELL + 27.6, 3.45 * CELL), (z, z + 1.6), (180, 182, 190), group="cab", layer=1)
        # ---- מדף עם קלסרים צבעוניים מעל הארון ----
        add((CELL + 1, 2.9 * CELL, CELL + 16, 3.7 * CELL), (45, 46.5), (110, 82, 58), top=(130, 98, 70), group="shelf")
        colors = [(150, 36, 36), (40, 70, 140), (190, 150, 40), (40, 110, 60), (120, 50, 120), (40, 70, 140), (150, 36, 36)]
        for k, col in enumerate(colors):
            y0 = 2.9 * CELL + 3 + k * 6.4
            add((CELL + 2, y0, CELL + 14, y0 + 5), (46.5, 56 - (k % 3)), col, layer=1, group="shelf")
        # ---- עציץ בפינה ----
        px_, py_ = CELL + 16, 4.6 * CELL
        add((px_ - 8, py_ - 8, px_ + 8, py_ + 8), (0, 11), (150, 80, 50), top=(50, 35, 25), group="plant")
        for k, (dx, dy, w, z0, z1, col) in enumerate((
                (0, 0, 7, 11, 24, (40, 110, 50)), (-5, 2, 5, 13, 27, (50, 130, 60)),
                (5, -3, 5, 12, 29, (34, 100, 44)), (1, 5, 5, 18, 33, (60, 140, 70)),
                (-3, -5, 4, 20, 31, (46, 120, 56)))):
            add((px_ + dx - w, py_ + dy - w, px_ + dx + w, py_ + dy + w), (z0, z1), col, layer=k + 1, group="plant")

        # ---- רצפה, שטיח ותאורת תקרה (משטחים שטוחים שמצוירים לפני הרהיטים) ----
        decals = []
        x_lo, x_hi, y_lo, y_hi = CELL, (ROOM_COLS - 1) * CELL, CELL, (ROOM_ROWS - 1) * CELL
        T = 32
        for i in range(int((x_hi - x_lo) / T)):
            for j in range(int((y_hi - y_lo) / T)):
                x0, y0 = x_lo + i * T, y_lo + j * T
                col = (72, 76, 82) if (i + j) % 2 == 0 else (58, 61, 67)
                decals.append(([(x0, y0), (x0 + T, y0), (x0 + T, y0 + T), (x0, y0 + T)], col, 0.04, False))
        # שטיח בורדו עם מסגרת מוזהבת מתחת לשולחן ולאזור העבודה
        rect = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        decals.append((rect(92, 108, 228, 236), (60, 20, 24), 0.06, False))
        decals.append((rect(96, 112, 224, 232), (150, 118, 64), 0.07, False))
        decals.append((rect(100, 116, 220, 228), (98, 28, 36), 0.08, False))
        decals.append((rect(112, 128, 208, 216), (120, 40, 48), 0.09, False))
        decals.append((rect(116, 132, 204, 212), (98, 28, 36), 0.10, False))
        # פנלי תאורה בתקרה
        for y0 in (118, 222):
            decals.append((rect(118, y0, 202, y0 + 34), (120, 124, 130), CELL - 0.3, True))
            decals.append((rect(122, y0 + 4, 198, y0 + 30), (236, 244, 240), CELL - 0.35, True))
            decals.append((rect(159, y0 + 4, 161, y0 + 30), (170, 176, 176), CELL - 0.4, True))
        self.room_floor_decals = decals
        # ארון תיוק ליד הקיר השמאלי
        add((CELL + 1, 3.0 * CELL, CELL + 26, 3.6 * CELL), (0, 40), (76, 80, 88), top=(96, 100, 108), group="cab", solid=True)
        self.room_props = props

    def _to_cam(self, X, Y, Z):
        p = self.player
        ca, sa = math.cos(p.angle), math.sin(p.angle)
        dx, dy = X - p.x, Y - p.y
        return (dx * ca + dy * sa, -dx * sa + dy * ca, Z)

    @staticmethod
    def _clip_near(poly):
        """חיתוך פוליגון (במרחב המצלמה) במישור הקרוב - כדי שאפשר יהיה לעמוד צמוד לרהיטים"""
        out = []
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            ain, bin_ = a[0] >= NEAR_PLANE, b[0] >= NEAR_PLANE
            if ain:
                out.append(a)
            if ain != bin_:
                t = (NEAR_PLANE - a[0]) / (b[0] - a[0])
                out.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(3)))
        return out

    @staticmethod
    def _cam_to_screen(c):
        fwd, lat, z = c
        return ((0.5 + math.atan2(lat, fwd) / FOV) * WIDTH, HEIGHT / 2 - (z - CELL / 2) * HEIGHT / fwd)

    def draw_room_props(self):
        """מצייר את הרהיטים כקופסאות תלת-ממדיות אמיתיות, והמסכים מציגים את המצלמות בשידור חי"""
        p = self.player
        eye = CELL / 2
        scr = self.screen
        self.room_monitor_screens = {}
        # כתמי דם על הרצפה - שטוחים, לכן מצוירים לפני כל הרהיטים
        for pts, col, z, emissive in getattr(self, "room_floor_decals", ()):
            cam = self._clip_near([self._to_cam(x, y, z) for x, y in pts])
            if len(cam) >= 3:
                mx_ = sum(q[0] for q in pts) / len(pts)
                my_ = sum(q[1] for q in pts) / len(pts)
                d = math.hypot(mx_ - p.x, my_ - p.y)
                k = 1.0 if emissive else max(0.5, 1 - d / ROOM_LIGHT_RADIUS)
                pygame.draw.polygon(scr, tuple(int(c * k) for c in col),
                                    [self._cam_to_screen(c) for c in cam])
        # סדר ציור: קבוצות רחוקות קודם; בתוך קבוצה - לפי שכבה (קודם השולחן, אחר כך מה שעליו)
        group_d = {}
        for pr in self.room_props:
            x0, y0, x1, y1 = pr["box"]
            d = math.hypot((x0 + x1) / 2 - p.x, (y0 + y1) / 2 - p.y)
            if pr["layer"] == 0:
                group_d[pr["group"]] = d
        order = sorted(self.room_props, key=lambda pr: (-group_d.get(pr["group"], 0), pr["layer"]))

        for pr in order:
            x0, y0, x1, y1 = pr["box"]
            z0, z1 = pr["z"]
            dist = math.hypot((x0 + x1) / 2 - p.x, (y0 + y1) / 2 - p.y)
            light = max(0.55, 1 - dist / ROOM_LIGHT_RADIUS)
            faces = []
            if eye > z1:
                faces.append(("top", [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], 1.0))
            if eye < z0:
                faces.append(("bottom", [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], 0.45))
            if p.y > y1:
                faces.append(("front", [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], 0.86))
            if p.y < y0:
                faces.append(("back", [(x1, y0, z0), (x0, y0, z0), (x0, y0, z1), (x1, y0, z1)], 0.55))
            if p.x < x0:
                faces.append(("left", [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], 0.68))
            if p.x > x1:
                faces.append(("right", [(x1, y1, z0), (x1, y0, z0), (x1, y0, z1), (x1, y1, z1)], 0.68))
            for name, verts, shade in faces:
                cam = self._clip_near([self._to_cam(*v) for v in verts])
                if len(cam) < 3:
                    continue
                pts = [self._cam_to_screen(c) for c in cam]
                base = pr["top"] if name == "top" else pr["col"]
                k = shade * light
                if name == "bottom" and pr.get("emit"):
                    base, k = pr["emit"], 1.0   # אור המנורה - לא מוצלל
                pygame.draw.polygon(scr, tuple(min(255, int(c * k)) for c in base), pts)
                pygame.draw.polygon(scr, tuple(int(c * k * 0.6) for c in base), pts, 1)
                if name == "front" and pr["screen"] is not None:
                    self._draw_monitor_screen(pr, dist)

    def _draw_monitor_screen(self, pr, dist):
        """מצייר את הצילום החי על חזית המסך, ברצועות אנכיות לפי הפרספקטיבה"""
        idx = pr["screen"]
        if idx >= len(self.cameras):
            return
        x0, y0, x1, y1 = pr["box"]
        z0, z1 = pr["z"]
        bx = (x1 - x0) * 0.07
        bz = (z1 - z0) * 0.1
        sx0, sx1, sz0, sz1 = x0 + bx, x1 - bx, z0 + bz * 1.4, z1 - bz
        feed = self.cam_feeds.get(idx)
        if feed is not None:
            feed = feed.copy()
            self.draw_cam_overlay(feed, idx)
        fw = feed.get_width() if feed else 1
        strips = 18
        rect = None
        for i in range(strips):
            u0, u1 = i / strips, (i + 1) / strips
            xa, xb = sx0 + (sx1 - sx0) * u0, sx0 + (sx1 - sx0) * u1
            ca_b, ca_t = self._to_cam(xa, y1 + 0.05, sz0), self._to_cam(xa, y1 + 0.05, sz1)
            cb_b, cb_t = self._to_cam(xb, y1 + 0.05, sz0), self._to_cam(xb, y1 + 0.05, sz1)
            if min(ca_b[0], cb_b[0]) < NEAR_PLANE:
                continue
            pa_b, pa_t = self._cam_to_screen(ca_b), self._cam_to_screen(ca_t)
            pb_b, pb_t = self._cam_to_screen(cb_b), self._cam_to_screen(cb_t)
            left = int(min(pa_b[0], pb_b[0]))
            right = int(math.ceil(max(pa_b[0], pb_b[0])))
            top = int(min(pa_t[1], pb_t[1]))
            bot = int(max(pa_b[1], pb_b[1]))
            w, h = right - left + 1, bot - top
            if w <= 0 or h <= 0 or right < 0 or left > WIDTH or w > WIDTH * 2 or h > HEIGHT * 3:
                continue
            r = pygame.Rect(left, top, w, h)
            if feed is not None:
                c0 = min(fw - 1, int(u0 * fw))
                c1 = max(c0 + 1, min(fw, int(u1 * fw)))
                piece = pygame.transform.scale(feed.subsurface((c0, 0, c1 - c0, feed.get_height())), (w, h))
                self.screen.blit(piece, r)
            else:
                pygame.draw.rect(self.screen, (20, 34, 26), r)
            rect = r if rect is None else rect.union(r)
        if rect is not None:
            self.room_monitor_screens[idx] = (rect, dist)
            mouse = pygame.mouse.get_pos()
            if self.cam_focus is None and rect.collidepoint(mouse) and dist < MONITOR_USE_DIST:
                pygame.draw.rect(self.screen, (120, 240, 170), rect.inflate(4, 4), 2)

    def room_click(self, pos):
        if self.room_timer < 0.8:
            return
        if self.cam_focus is not None:
            self.cam_focus = None
            return
        hits = [(d, i) for i, (r, d) in getattr(self, "room_monitor_screens", {}).items() if r.collidepoint(pos)]
        if not hits:
            return
        d, i = min(hits)
        if d < MONITOR_USE_DIST:
            self.cam_focus = i
        else:
            self.message = "תתקרב לשולחן כדי לראות את המסך"
            self.message_timer = 2.0

    def draw_camera_room(self):
        # --- עדכון הצילומים: מסך אחד בכל פריים (כמו מצלמות אבטחה אמיתיות), והמוגדל - כל פריים שני ---
        if self.cameras:
            if self.cam_focus is not None:
                self._focus_tick = getattr(self, "_focus_tick", 0) + 1
                key = ("big", self.cam_focus)
                if key not in self.cam_feeds or self._focus_tick % 2 == 0:
                    self.cam_feeds[key] = self.render_cam_feed(self.cam_focus, (720, 450))
            else:
                n = len(self.cameras)
                missing = [i for i in range(n) if i not in self.cam_feeds]
                self._feed_tick = getattr(self, "_feed_tick", 0) + 1
                if missing:
                    for i in missing[:2]:
                        self.cam_feeds[i] = self.render_cam_feed(i, CAM_FEED_SIZE)
                elif self._feed_tick % 2 == 0:   # מסך אחד כל פריים שני - חוסך חישוב
                    self.cam_feeds[self.cam_cursor % n] = self.render_cam_feed(self.cam_cursor % n, CAM_FEED_SIZE)
                    self.cam_cursor += 1

        # --- החדר עצמו, בגוף ראשון ---
        scr = self.screen
        saved_light = self.effective_light_radius
        self.view_room = True
        self.effective_light_radius = ROOM_LIGHT_RADIUS
        self.render_world()
        self.view_room = False
        self.effective_light_radius = saved_light
        if self.photo_pending:
            self.capture_photo()
        self.draw_grain()
        self.draw_vignette()

        # כוונת קטנה באמצע
        if self.cam_focus is None:
            pygame.draw.circle(scr, (220, 230, 225), (WIDTH // 2, HEIGHT // 2), 2)

        # --- מסך מוגדל ---
        if self.cam_focus is not None:
            dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 190))
            scr.blit(dim, (0, 0))
            big = self.cam_feeds.get(("big", self.cam_focus))
            r = pygame.Rect(0, 0, 720, 450)
            r.center = (WIDTH // 2, HEIGHT // 2 + 10)
            pygame.draw.rect(scr, (34, 36, 40), r.inflate(24, 24), border_radius=10)
            if big is not None:
                b2 = big.copy()
                self.draw_cam_overlay(b2, self.cam_focus, big=True)
                scr.blit(b2, r)

        # --- משימה נוכחית + רמזים ---
        if self.room_intro_done:
            self.draw_pill("משימה: " + self.mission_text, (255, 215, 120), 10, 8)
        if self.room_timer > 1.0:
            if self.cam_focus is not None:
                hint = "לחץ שוב כדי לחזור"
            elif self.near_desk_camera():
                hint = "Enter - לקחת את המצלמה"
            elif self.has_camera:
                hint = "Shift - צילום  |  צא מהדלת כדי לחפש את המפלצת"
            else:
                hint = "W/A/S/D - הליכה  |  גש לשולחן ולחץ על מסך כדי להגדיל"
            txt = self.font_small.render(rtl(hint), True, (215, 230, 220))
            box = txt.get_rect(center=(WIDTH // 2, HEIGHT - 18)).inflate(20, 8)
            bg = pygame.Surface(box.size, pygame.SRCALPHA)
            pygame.draw.rect(bg, (0, 0, 0, 150), bg.get_rect(), border_radius=10)
            scr.blit(bg, box)
            scr.blit(txt, txt.get_rect(center=box.center))
        if self.message_timer > 0 and self.room_timer > 1.0:
            msg = self.font_small.render(rtl(self.message), True, WHITE)
            box = msg.get_rect(center=(WIDTH // 2, 54)).inflate(26, 10)
            bg = pygame.Surface(box.size, pygame.SRCALPHA)
            pygame.draw.rect(bg, (0, 0, 0, 160), bg.get_rect(), border_radius=14)
            scr.blit(bg, box)
            scr.blit(msg, msg.get_rect(center=box.center))

        if not self.room_intro_done:
            self.draw_mission_banners()
        self.draw_overlays()

        # כניסה מהשחור / יציאה לשחור
        if self.room_timer < 1.0:
            fade = pygame.Surface((WIDTH, HEIGHT))
            fade.set_alpha(int(255 * (1 - self.room_timer)))
            scr.blit(fade, (0, 0))
        if self.leaving_room > 0:
            fade = pygame.Surface((WIDTH, HEIGHT))
            fade.set_alpha(int(255 * min(1.0, self.leaving_room / ENTER_FADE)))
            scr.blit(fade, (0, 0))

    def draw_mission_banners(self):
        """'המשימה הושלמה' בגדול, ואחרי כמה שניות 'משימה חדשה'"""
        t = self.room_timer
        for start, end, title, sub, color in (
                (1.6, 5.8, "המשימה הושלמה!", "השגת את היומן והגעת לחדר המצלמות", (120, 255, 160)),
                (7.0, 11.5, "משימה חדשה", "לצלם תמונה של המפלצת", (255, 205, 90))):
            if not (start <= t <= end):
                continue
            k = t - start
            alpha = min(1.0, k / 0.35, (end - t) / 0.5)
            pop = 1 + 0.35 * max(0.0, 1 - k / 0.3)   # "קפיצה" קטנה בהופעה
            band = pygame.Surface((WIDTH, 210), pygame.SRCALPHA)
            band.fill((0, 0, 0, int(185 * alpha)))
            pygame.draw.line(band, (*color, int(200 * alpha)), (0, 0), (WIDTH, 0), 3)
            pygame.draw.line(band, (*color, int(200 * alpha)), (0, 207), (WIDTH, 207), 3)
            self.screen.blit(band, (0, HEIGHT // 2 - 115))
            title_s = self.font_huge.render(rtl(title), True, color)
            if pop != 1:
                title_s = pygame.transform.smoothscale(
                    title_s, (int(title_s.get_width() * pop), int(title_s.get_height() * pop)))
            glow = self.font_huge.render(rtl(title), True, (0, 0, 0))
            glow = pygame.transform.smoothscale(glow, title_s.get_size())
            for gx, gy in ((-3, 3), (3, 3), (0, 4)):
                g2 = glow.copy()
                g2.set_alpha(int(150 * alpha))
                self.screen.blit(g2, g2.get_rect(center=(WIDTH // 2 + gx, HEIGHT // 2 - 40 + gy)))
            title_s.set_alpha(int(255 * alpha))
            self.screen.blit(title_s, title_s.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
            sub_s = self.font_button.render(rtl(sub), True, (235, 235, 235))
            sub_s.set_alpha(int(255 * alpha))
            self.screen.blit(sub_s, sub_s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))

    def update_blood(self, dt):
        for p in self.blood_particles:
            p["vy"] += 500 * dt  # כבידה
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
        self.blood_particles = [p for p in self.blood_particles if p["life"] > 0]

        for m in self.blood_marks:
            m["alpha"] -= 55 * dt  # דוהה לאט - נשאר על המסך כמה שניות טובות
        self.blood_marks = [m for m in self.blood_marks if m["alpha"] > 0]

        for s in self.shot_effects:
            s["life"] -= dt
        self.shot_effects = [s for s in self.shot_effects if s["life"] > 0]

    def update(self, dt):
        self.audio.frame_update(dt, self)
        self.flash_timer = max(0.0, self.flash_timer - dt)
        if self.ending_active:
            self.update_ending(dt)
            return
        if self.on_menu:
            return
        self.update_blood(dt)

        if self.jumpscare_active:
            self.jumpscare_timer += dt
            if self.jumpscare_timer >= JUMPSCARE_DURATION:
                self.jumpscare_active = False
                self.game_over = True
            return  # קפוא לגמרי בזמן אנימציית הטריפה

        if self.game_over or self.win:
            return

        if self.in_camera_room:
            self.update_camera_room(dt)
            return
        if self.banner:
            t_, s_, c_, left = self.banner
            self.banner = (t_, s_, c_, left - dt) if left - dt > 0 else None
        self.door_cooldown = max(0.0, getattr(self, "door_cooldown", 0.0) - dt)
        if self.photo_view:
            return   # המשחק עוצר בזמן שמסתכלים על התמונה

        if self.entering > 0:
            # נכנסים בדלת - המסך מחשיך, ואז חדר המצלמות (או כישלון בלי יומן)
            self.entering += dt
            if self.entering >= ENTER_FADE:
                self.entering = 0.0
                if self.journal_collected:
                    self.enter_camera_room()
                else:
                    self.left_without_journal = True
                    self.game_over = True
            return

        self.update_ambient_dread(dt)

        keys = pygame.key.get_pressed()

        # פנס חזק - לחיצה על 1 מגבירה משמעותית את טווח וחוזק התאורה
        # בתוך הארון אין פנס חזק, והאור מעומעם - רואים רק דרך החרכים
        hidden = self.player.hidden
        self.light_boost = keys[pygame.K_1] and not hidden
        if self.light_boost:
            self.effective_light_radius = MAX_DEPTH * 2
        elif hidden:
            self.effective_light_radius = LIGHT_RADIUS * HIDDEN_LIGHT_FACTOR
        else:
            self.effective_light_radius = LIGHT_RADIUS

        # החזקת הפנס החזק 1-2 שניות ברציפות חושפת אותך לגמרי - כאילו אין יותר חושך שמגן עליך
        if self.light_boost:
            self.light_boost_hold_timer += dt
        else:
            self.light_boost_hold_timer = 0.0

        if (self.light_boost_hold_timer >= LIGHT_BOOST_WAKE_TIME
                and not self.monster.awake and not self.forced_wake_triggered and not TEST_NO_MONSTER):
            self.monster.wake(self.player)
            self.forced_wake_triggered = True
            self.message = "האור חשף אותך - אין יותר איפה להסתתר..."
            self.message_timer = 2.5

        # מרחק למפלצת מהפריים הקודם - קובע אם השליטה נלקחת מהשחקן
        dist_to_monster = math.hypot(self.monster.x - self.player.x, self.monster.y - self.player.y)
        # מתחבא בלי שראו אותך = בטוח. הקיפאון קורה רק כשהשומר באמת רודף אחריך
        exposed = not hidden or self.monster.saw_hide
        forced_turn = (self.monster.state == "chase" and exposed
                       and dist_to_monster < FORCED_TURN_DISTANCE)

        if forced_turn:
            if not self.forced_turn_active:
                self.message = "אתה לא מסוגל להזיז את המבט..."
                self.message_timer = 2.0
                self.forced_turn_timer = 0.0
            self.forced_turn_active = True
            self.forced_turn_timer += dt

            # סיבוב אוטומטי כפוי לכיוון המפלצת - השחקן לא שולט בזה, ולא יכול לזוז
            dx = self.monster.x - self.player.x
            dy = self.monster.y - self.player.y
            target_angle = math.atan2(dy, dx)
            diff = (target_angle - self.player.angle + math.pi) % (2 * math.pi) - math.pi
            step = max(-FORCED_TURN_SPEED, min(FORCED_TURN_SPEED, diff))
            self.player.angle += step

            # אחרי 5 שניות של קיפאון מול המפלצת - היא תוקפת
            if self.forced_turn_timer >= FORCED_TURN_KILL_TIME:
                self.jumpscare_active = True
                self.jumpscare_timer = 0.0
                self.message = ""
                self.message_timer = 0
                return
        else:
            self.forced_turn_active = False
            self.forced_turn_timer = 0.0

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player.angle -= ROT_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player.angle += ROT_SPEED

            if hidden:
                # בארון אפשר רק להציץ (לסובב את המבט בטווח מוגבל), לא לזוז
                if self.current_spot is not None:
                    face = self.current_spot["face"]
                    diff = (self.player.angle - face + math.pi) % (2 * math.pi) - math.pi
                    self.player.angle = face + max(-0.6, min(0.6, diff))
            else:
                move_x = move_y = 0
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    move_x += math.cos(self.player.angle) * MOVE_SPEED
                    move_y += math.sin(self.player.angle) * MOVE_SPEED
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    move_x -= math.cos(self.player.angle) * MOVE_SPEED
                    move_y -= math.sin(self.player.angle) * MOVE_SPEED
                if keys[pygame.K_q]:
                    move_x += math.cos(self.player.angle - math.pi / 2) * MOVE_SPEED
                    move_y += math.sin(self.player.angle - math.pi / 2) * MOVE_SPEED
                if keys[pygame.K_e]:
                    move_x += math.cos(self.player.angle + math.pi / 2) * MOVE_SPEED
                    move_y += math.sin(self.player.angle + math.pi / 2) * MOVE_SPEED

                self.player.try_move(move_x, move_y, self.grid,
                                     [sp["box"] for sp in self.hiding_spots])

        was_awake = self.monster.awake
        prev_state = self.monster.state
        self.step_monster(dt)
        state = self.monster.state

        state = self.monster.state
        if self.monster.awake and not was_awake:
            self.message = "השומר התעורר!"
            self.message_timer = 2.0
        elif prev_state == "chase" and state == "search":
            self.message = "הוא איבד את העקבות שלך... הוא מחפש"
            self.message_timer = 2.5
        elif prev_state in ("search", "return") and state == "chase":
            self.message = "הוא מצא אותך!"
            self.message_timer = 2.0
        elif prev_state == "search" and state == "return":
            self.message = "הוא מוותר... וחוזר למאורה"
            self.message_timer = 2.5
        elif was_awake and not self.monster.awake:
            self.message = "השומר נרדם שוב"
            self.message_timer = 2.5
            self.forced_wake_triggered = False

        # איסוף היומן מהחדר הפתוח הקטן
        if (not self.journal_collected
                and math.hypot(self.journal_pos[0] - self.player.x,
                               self.journal_pos[1] - self.player.y) < 34):
            self.journal_collected = True
            self.message = "לקחת את היומן - עכשיו תמצא את היציאה"
            self.message_timer = 3.0

        # דלת היציאה נפתחת לבד כשמתקרבים, ונסגרת כשמתרחקים
        d_exit = math.hypot(self.exit_pos[0] - self.player.x, self.exit_pos[1] - self.player.y)
        want_open = d_exit < DOOR_OPEN_DIST and not self.player.hidden
        if want_open and self.door_open == 0.0:
            self.audio.play_fx("snd_creak")
        target = 1.0 if want_open else 0.0
        step = DOOR_OPEN_SPEED * dt
        self.door_open = max(0.0, min(1.0, self.door_open + max(-step, min(step, target - self.door_open))))
        idx = int(round(self.door_open * (DOOR_FRAMES - 1)))
        self.wall_textures["door"], self.wall_textures["door_glow"] = self.door_frames[idx]

        # נכנסים בדלת הפתוחה
        if self.door_open > 0.85 and d_exit < 24 and self.door_cooldown <= 0:
            self.entering = 0.001
            return

        # תפיסה (מגע ישיר - עדיין אפשרי אם המפלצת מגיעה ממש קרוב לפני תום הזמן הקבוע)
        # בארון, אם השומר לא ראה אותך נכנס - הוא יכול לעבור ממש לידך בלי לגלות
        if (exposed and self.monster.awake
                and math.hypot(self.monster.x - self.player.x, self.monster.y - self.player.y) < CATCH_DISTANCE):
            self.jumpscare_active = True
            self.jumpscare_timer = 0.0
            return

        if self.message_timer > 0:
            self.message_timer -= dt

        self.flicker_timer -= dt
        if self.flicker_timer <= 0:
            self.flicker_timer = random.uniform(0.7, 2.4)
            self.flicker = random.uniform(0.18, 0.5)

    # ------------------------------
    # רינדור גוף ראשון - Raycasting
    # ------------------------------
    # ------------------------------------------------------------
    # כלי עזר גרפיים (נוצרים/נשמרים פעם אחת)
    # ------------------------------------------------------------
    def build_wall_textures(self):
        tex = {
            "brick": _make_wall_texture("brick", 11),
            "blood": _make_wall_texture("blood", 23),
            "crack": _make_wall_texture("crack", 37),
        }
        tex["concrete"] = self.build_concrete_texture(3)
        tex["room_sign"] = self.build_room_sign_texture(tex["concrete"])
        tex["clock"] = self.build_clock_texture(tex["concrete"])
        tex["extinguisher"] = self.build_extinguisher_texture(tex["concrete"])
        tex["rack"] = self.build_rack_texture(tex["concrete"])
        self.door_frames = [self.build_door_texture(tex["brick"], k / (DOOR_FRAMES - 1))
                            for k in range(DOOR_FRAMES)]
        # אותה דלת, אבל על קיר בטון - לצד הפנימי של הדלת בחדר הבקרה
        self.door_frames_room = [self.build_door_texture(tex["concrete"], k / (DOOR_FRAMES - 1), to_maze=True)
                                 for k in range(DOOR_FRAMES)]
        tex["door"], tex["door_glow"] = self.door_frames[0]
        tex["door_room"], tex["door_room_glow"] = self.door_frames_room[0]
        return tex

    def build_concrete_texture(self, seed):
        """קיר מעבדה: פנלים אפורים-כחלחלים, פס כתום דק, חיפוי תחתון כהה ופנל רצפה"""
        rng = random.Random(seed)
        S = TEX_SIZE * 2
        tex = pygame.Surface((S, S))
        wain = int(S * 0.66)
        for y in range(S):
            if y < int(S * 0.03):
                base = (64, 72, 76)                                   # כרכוב עליון
            elif y < wain:
                f = y / wain
                base = lerp_color((118, 132, 136), (100, 114, 118), f)  # הקיר העליון
            elif y < wain + 5:
                base = (196, 150, 64)                                 # פס כתום
            elif y < int(S * 0.94):
                base = (54, 66, 72)                                   # חיפוי תחתון
            else:
                base = (26, 28, 30)                                   # פנל רצפה
            for x in range(S):
                n = rng.randint(-5, 5)
                tex.set_at((x, y), tuple(max(0, min(255, c + n)) for c in base))
        for x in (0, S // 2):  # תפרים בין פנלים
            pygame.draw.line(tex, (80, 92, 96), (x, int(S * 0.03)), (x, wain), 2)
            pygame.draw.line(tex, (138, 152, 156), (x + 2, int(S * 0.03)), (x + 2, wain), 1)
        for y in range(wain + 12, int(S * 0.94), 10):  # חריצים בחיפוי
            pygame.draw.line(tex, (44, 54, 60), (0, y), (S, y), 1)
        pygame.draw.line(tex, (40, 44, 46), (0, wain - 1), (S, wain - 1), 1)
        return tex

    def build_clock_texture(self, wall):
        """קיר עם שעון קיר עגול"""
        S = wall.get_width() * 2
        tex = pygame.transform.scale(wall, (S, S))
        c = (S // 2, int(S * 0.3))
        r = int(S * 0.17)
        pygame.draw.circle(tex, (20, 22, 24), (c[0] + 3, c[1] + 4), r + 4)
        pygame.draw.circle(tex, (40, 42, 46), c, r + 4)
        pygame.draw.circle(tex, (232, 228, 214), c, r)
        for k in range(12):
            a = k / 12 * 2 * math.pi
            p1 = (c[0] + math.cos(a) * r * 0.82, c[1] + math.sin(a) * r * 0.82)
            p2 = (c[0] + math.cos(a) * r * 0.95, c[1] + math.sin(a) * r * 0.95)
            pygame.draw.line(tex, (30, 30, 30), p1, p2, 3 if k % 3 == 0 else 1)
        pygame.draw.line(tex, (20, 20, 20), c, (c[0] + r * 0.45, c[1] - r * 0.2), 5)   # שעה (03:..)
        pygame.draw.line(tex, (20, 20, 20), c, (c[0] - r * 0.1, c[1] - r * 0.78), 3)   # דקות
        pygame.draw.line(tex, (190, 30, 30), c, (c[0] - r * 0.6, c[1] + r * 0.5), 1)   # שניות
        pygame.draw.circle(tex, (20, 20, 20), c, 4)
        return tex

    def build_extinguisher_texture(self, wall):
        """מטף כיבוי אש אדום עם שלט על הקיר"""
        S = wall.get_width() * 2
        tex = pygame.transform.scale(wall, (S, S))
        sign = pygame.Rect(int(S * 0.36), int(S * 0.12), int(S * 0.28), int(S * 0.14))
        pygame.draw.rect(tex, (200, 30, 30), sign, border_radius=4)
        pygame.draw.rect(tex, (250, 250, 250), sign.inflate(-10, -10), 3, border_radius=3)
        body = pygame.Rect(int(S * 0.42), int(S * 0.36), int(S * 0.16), int(S * 0.36))
        pygame.draw.rect(tex, (20, 10, 10), body.move(4, 4), border_radius=10)
        pygame.draw.rect(tex, (190, 26, 26), body, border_radius=10)
        pygame.draw.rect(tex, (230, 70, 70), (body.left + 6, body.top + 8, 6, body.h - 16), border_radius=3)
        pygame.draw.rect(tex, (30, 30, 30), (body.centerx - 8, body.top - 14, 16, 16))
        pygame.draw.line(tex, (30, 30, 30), (body.centerx + 8, body.top - 8), (body.right + 10, body.top + 30), 4)
        pygame.draw.rect(tex, (240, 240, 240), (body.left + 4, body.top + body.h // 3, body.w - 8, body.h // 4))
        return tex

    def build_map_texture(self, wall):
        """מפת המתחם (שרטוט כחול) ממוסגרת על הקיר - נבנית מהמבוך האמיתי"""
        S = wall.get_width() * 2
        tex = pygame.transform.scale(wall, (S, S))
        frame = pygame.Rect(int(S * 0.08), int(S * 0.13), int(S * 0.84), int(S * 0.48))
        pygame.draw.rect(tex, (16, 16, 18), frame.move(4, 5))
        pygame.draw.rect(tex, (70, 52, 36), frame)
        paper = frame.inflate(-14, -14)
        pygame.draw.rect(tex, (26, 62, 120), paper)
        grid = self.grid
        rows, cols = len(grid), len(grid[0])
        cw = (paper.w - 12) / cols
        ch = (paper.h - 12) / rows
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 1:
                    pygame.draw.rect(tex, (190, 214, 240), (paper.left + 6 + c * cw, paper.top + 6 + r * ch,
                                                           math.ceil(cw), math.ceil(ch)))
        hx, hy = self.monster.home
        mxp = (paper.left + 6 + (hx + 0.5) * cw, paper.top + 6 + (hy + 0.5) * ch)
        pygame.draw.line(tex, (230, 30, 30), (mxp[0] - 6, mxp[1] - 6), (mxp[0] + 6, mxp[1] + 6), 3)
        pygame.draw.line(tex, (230, 30, 30), (mxp[0] - 6, mxp[1] + 6), (mxp[0] + 6, mxp[1] - 6), 3)
        font = pygame.font.SysFont("arial", 20, bold=True)
        label = font.render(rtl("מפת המתחם"), True, (24, 28, 32))
        tex.blit(label, label.get_rect(center=(S // 2, frame.top - 14)))
        return tex

    def build_room_sign_texture(self, concrete):
        """קיר בטון עם שלט 'חדר בקרה' ופנל אזהרה"""
        U = 4
        S = TEX_SIZE * U
        tex = pygame.transform.scale(concrete, (S, S))
        sign = pygame.Rect(int(S * 0.12), int(S * 0.22), int(S * 0.76), int(S * 0.2))
        pygame.draw.rect(tex, (20, 22, 26), sign.inflate(8, 8), border_radius=6)
        pygame.draw.rect(tex, (200, 160, 40), sign, border_radius=5)
        font = pygame.font.SysFont("arial", 56, bold=True)
        label = font.render(rtl("חדר בקרה"), True, (20, 18, 14))
        sc = min((sign.w - 20) / label.get_width(), (sign.h - 10) / label.get_height())
        label = pygame.transform.smoothscale(label, (int(label.get_width() * sc), int(label.get_height() * sc)))
        tex.blit(label, label.get_rect(center=sign.center))
        # לוח הודעות עם דפים
        board = pygame.Rect(int(S * 0.2), int(S * 0.5), int(S * 0.6), int(S * 0.3))
        pygame.draw.rect(tex, (110, 80, 50), board)
        pygame.draw.rect(tex, (70, 50, 30), board, 6)
        rng = random.Random(4)
        for k in range(4):
            pr = pygame.Rect(board.left + 14 + k * (board.w // 4), board.top + 16 + rng.randint(0, 20), board.w // 5, board.h // 2)
            pygame.draw.rect(tex, (220, 216, 200), pr)
            for j in range(4):
                pygame.draw.line(tex, (120, 120, 120), (pr.left + 6, pr.top + 10 + j * 12), (pr.right - 6, pr.top + 10 + j * 12), 2)
            pygame.draw.circle(tex, (200, 30, 30), (pr.centerx, pr.top + 4), 4)
        return tex

    def build_rack_texture(self, wall):
        """ארון שרתים עם נוריות - מוצמד לקיר"""
        S = wall.get_width()
        tex = wall.copy()
        rack = pygame.Rect(int(S * 0.15), int(S * 0.08), int(S * 0.7), int(S * 0.92))
        pygame.draw.rect(tex, (18, 19, 22), rack)
        pygame.draw.rect(tex, (50, 52, 58), rack, 2)
        rng = random.Random(8)
        y = rack.top + 6
        while y < rack.bottom - 10:
            unit = pygame.Rect(rack.left + 5, y, rack.w - 10, 9)
            pygame.draw.rect(tex, (34, 36, 40), unit)
            for k in range(rng.randint(2, 6)):
                c = rng.choice(((40, 230, 100), (40, 230, 100), (240, 170, 40), (60, 140, 255)))
                tex.set_at((unit.left + 4 + k * 4, unit.centery), c)
            pygame.draw.line(tex, (60, 62, 68), (unit.right - 22, unit.centery), (unit.right - 6, unit.centery))
            y += 12
        return tex

    def _door_slab_image(self, size):
        """כנף הדלת עצמה (עץ טיק חלק, ידית, מנעול, צירים) כתמונה נפרדת - כדי שתוכל להסתובב"""
        cached = getattr(self, "_slab_cache", None)
        if cached is not None and cached.get_size() == tuple(size):
            return cached
        tex = pygame.Surface(size)
        slab = tex.get_rect()
        rng = random.Random(9)
        rng.random()
        phases = [rng.uniform(0, 6.28) for _ in range(4)]
        for x in range(slab.left, slab.right):
            u = (x - slab.left) / slab.w
            g = (math.sin(u * 23 + phases[0]) * 0.5 + math.sin(u * 61 + phases[1]) * 0.3
                 + math.sin(u * 137 + phases[2]) * 0.2)
            sheen = 0.12 * math.exp(-((u - 0.62) / 0.18) ** 2)  # ברק עדין של לכה
            k = 1 + 0.07 * g + sheen - 0.08 * abs(u - 0.5)
            col = (min(255, int(196 * k)), min(255, int(124 * k)), min(255, int(66 * k)))
            pygame.draw.line(tex, col, (x, slab.top), (x, slab.bottom))
        for _ in range(26):  # פסים כהים דקים בעץ
            x = rng.randint(slab.left + 2, slab.right - 3)
            y0 = rng.randint(slab.top, slab.bottom - 20)
            y1 = min(slab.bottom, y0 + rng.randint(30, 140))
            pygame.draw.line(tex, (150, 88, 44), (x, y0), (x + rng.choice((-1, 0, 1)), y1))
        pygame.draw.line(tex, (214, 150, 92), (slab.left, slab.top), (slab.right, slab.top))

        # ---- ידית מנוף כסופה + חור מנעול (בצד שמאל, באמצע הגובה) ----
        hx = slab.left + int(slab.w * 0.12)
        hy = slab.top + int(slab.h * 0.5)
        pygame.draw.circle(tex, (60, 60, 64), (hx + 1, hy + 2), 6)                 # צל
        pygame.draw.circle(tex, (190, 192, 198), (hx, hy), 6)                      # רוזטה
        pygame.draw.circle(tex, (235, 236, 240), (hx - 2, hy - 2), 2)
        lever = pygame.Rect(hx, hy - 3, int(slab.w * 0.2), 5)
        pygame.draw.rect(tex, (70, 70, 74), lever.move(1, 2), border_radius=2)    # צל
        pygame.draw.rect(tex, (196, 198, 204), lever, border_radius=2)
        pygame.draw.line(tex, (245, 246, 250), (lever.left + 2, lever.top + 1), (lever.right - 3, lever.top + 1))
        ky = hy + 18
        pygame.draw.circle(tex, (190, 192, 198), (hx, ky), 5)
        pygame.draw.circle(tex, (30, 24, 20), (hx, ky - 1), 2)
        pygame.draw.line(tex, (30, 24, 20), (hx, ky), (hx, ky + 3), 2)
        # צירים בצד ימין
        for fy in (0.12, 0.5, 0.86):
            yy = slab.top + int(slab.h * fy)
            pygame.draw.rect(tex, (120, 112, 100), (slab.right - 1, yy, 3, 12))

        self._slab_cache = tex
        return tex

    def _draw_maze_doorway(self, tex, slab):
        """מבפנים, דרך הדלת רואים את המבוך: מסדרון לבנים סגול וחשוך"""
        tex.fill((4, 3, 7), slab)
        for y in range(slab.top, slab.bottom, 10):
            f = 1 - abs((y - slab.centery) / (slab.h / 2))
            c = (int(10 + 16 * f), int(7 + 10 * f), int(14 + 18 * f))
            pygame.draw.line(tex, c, (slab.left, y), (slab.right - 1, y))
        inner = slab.inflate(-slab.w // 2, -slab.h // 2)
        pygame.draw.rect(tex, (2, 2, 4), inner)

    def _draw_doorway(self, tex, glow, slab, S):
        """מה שרואים דרך הדלת הפתוחה: חדר חשוך עם מסכי מצלמות כחלחלים בעומק"""
        for y in range(slab.top, slab.bottom):
            fy = (y - slab.top) / slab.h
            c = (8 + int(10 * fy), 10 + int(12 * fy), 18 + int(16 * fy))
            pygame.draw.line(tex, c, (slab.left, y), (slab.right - 1, y))
        horizon = int(S * 0.5)
        floor = pygame.Rect(slab.left, horizon + 14, slab.w, slab.bottom - horizon - 14)
        pygame.draw.rect(tex, (22, 24, 32), floor)
        # שורת מסכים קטנים בקצה החדר
        mw, mh = max(6, slab.w // 6), max(5, slab.w // 9)
        for row in range(2):
            for i in range(3):
                r = pygame.Rect(0, 0, mw, mh)
                r.center = (slab.centerx + (i - 1) * (mw + 5), horizon - 10 + row * (mh + 4))
                for target in (tex, glow):
                    pygame.draw.rect(target, (10, 12, 14), r.inflate(3, 3))
                    pygame.draw.rect(target, (70, 150, 140) if (i + row) % 2 else (90, 170, 120), r)
        desk = pygame.Rect(slab.centerx - mw * 2, horizon + 6 + mh * 2, mw * 4, 8)
        pygame.draw.rect(tex, (30, 30, 36), desk)
        # אור כחלחל שנשפך על הרצפה
        for i in range(10):
            pygame.draw.line(glow, (0, 6 + i * 2, 8 + i * 2),
                             (slab.left + 3, slab.bottom - 1 - i), (slab.right - 4, slab.bottom - 1 - i))

    def build_door_texture(self, brick, open_amt=0.0, to_maze=False):
        """דלת היציאה כחלק מהקיר: דלת עץ חלקה (גוון טיק, סיבים אנכיים) עם משקוף דק,
        ידית מנוף כסופה וחור מנעול, ושלט 'יציאה' ירוק על הקיר מעליה.
        מחזיר גם שכבת "זוהר" (שחורה חוץ מהשלט) שמתווספת גם כשחשוך."""
        U = 4
        S = TEX_SIZE * U
        tex = pygame.transform.scale(brick, (S, S))
        glow = pygame.Surface((S, S))
        glow.fill((0, 0, 0))
        rng = random.Random(9)

        # ---- משקוף דק ----
        casing = pygame.Rect(int(S * 0.29), int(S * 0.155), int(S * 0.42), S - int(S * 0.155))
        pygame.draw.rect(tex, (18, 10, 6), casing.inflate(6, 0).move(0, -3))     # צל סביב המשקוף
        pygame.draw.rect(tex, (168, 104, 56), casing)
        pygame.draw.line(tex, (206, 140, 82), casing.topleft, casing.topright, 2)
        pygame.draw.line(tex, (206, 140, 82), casing.topleft, casing.bottomleft, 2)
        pygame.draw.line(tex, (118, 70, 36), casing.topright, casing.bottomright, 2)

        # ---- כנף הדלת ----
        slab = casing.inflate(-int(S * 0.05), 0)
        slab.top = casing.top + int(S * 0.025)
        slab.height = S - slab.top
        pygame.draw.rect(tex, (40, 22, 10), slab.inflate(4, 2))  # מרווח כהה בין הכנף למשקוף
        panel = self._door_slab_image(slab.size)
        if open_amt <= 0.001:
            tex.blit(panel, slab)
        else:
            if to_maze:
                self._draw_maze_doorway(tex, slab)
            else:
                self._draw_doorway(tex, glow, slab, S)
            # הכנף מסתובבת פנימה על הצירים שבצד ימין: נהיית צרה, כהה ו"מתרחקת" (פרספקטיבה)
            ang = open_amt * 1.4
            vis_w = max(1, int(slab.w * math.cos(ang)))
            shrink = 0.18 * math.sin(ang)
            dark = 1 - 0.5 * math.sin(ang)
            horizon = S / 2
            for i in range(vis_w):
                u = i / max(1, vis_w - 1)            # 0 = הקצה החופשי, 1 = הצירים
                src_x = min(slab.w - 1, int(u * slab.w))
                f = 1 - shrink * (1 - u)
                top = horizon + (slab.top - horizon) * f
                bot = horizon + (S - horizon) * f
                col = pygame.transform.scale(panel.subsurface((src_x, 0, 1, slab.h)), (1, max(1, int(bot - top))))
                k = int(255 * dark)
                col.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)
                tex.blit(col, (slab.right - vis_w + i, int(top)))
                # הכנף מסתירה את המסכים הזוהרים שמאחוריה
                pygame.draw.line(glow, (0, 0, 0), (slab.right - vis_w + i, int(top)),
                                 (slab.right - vis_w + i, int(bot)))

        # ---- שלט "יציאה" על הקיר מעל הדלת ----
        sign = pygame.Rect(int(S * 0.27), int(S * 0.025), int(S * 0.46), int(S * 0.105))
        pygame.draw.rect(tex, (10, 10, 10), sign.inflate(6, 6), border_radius=6)
        for target, fill, edge in ((tex, (22, 120, 58), (150, 255, 180)), (glow, (20, 120, 55), (110, 230, 140))):
            pygame.draw.rect(target, fill, sign, border_radius=5)
            pygame.draw.rect(target, edge, sign, 3, border_radius=5)
        font = pygame.font.SysFont("arial", 56, bold=True)
        label = font.render(rtl("יציאה"), True, (240, 255, 240))
        sc = min((sign.w - 20) / label.get_width(), (sign.h - 8) / label.get_height())
        label = pygame.transform.smoothscale(label, (max(1, int(label.get_width() * sc)),
                                                     max(1, int(label.get_height() * sc))))
        r = label.get_rect(center=sign.center)
        tex.blit(label, r)
        glow.blit(label, r)
        # הילה ירוקה קלה על הקיר סביב השלט
        halo = pygame.Surface((S, S))
        halo.fill((0, 0, 0))
        for i in range(6, 0, -1):
            pygame.draw.rect(halo, (0, 9 * (7 - i), 4 * (7 - i)), sign.inflate(i * 10, i * 8), border_radius=12)
        glow.blit(halo, (0, 0), special_flags=pygame.BLEND_RGB_MAX)
        glow.blit(tex, sign, sign, special_flags=pygame.BLEND_RGB_MAX)
        return tex, glow

    def build_background(self, boost=False):
        """תקרה ורצפה עם מעבר צבע חלק: קרוב אליך מואר מעט, וככל שמתרחקים לאופק - חשוך"""
        surf = pygame.Surface((WIDTH, HEIGHT))
        half = HEIGHT // 2
        gain = 3.2 if boost else 1.0
        horizon = (3, 3, 6)
        ceil_near = tuple(min(255, int(c * gain)) for c in (22, 16, 30))
        floor_near = tuple(min(255, int(c * gain)) for c in (38, 30, 40))
        for y in range(half):
            t = (1 - y / half) ** 1.5      # 1 למעלה (קרוב), 0 באופק
            pygame.draw.line(surf, lerp_color(horizon, ceil_near, t), (0, y), (WIDTH, y))
            s = ((y) / half) ** 1.4        # 0 באופק, 1 למטה (קרוב)
            pygame.draw.line(surf, lerp_color(horizon, floor_near, s), (0, half + y), (WIDTH, half + y))
        return surf

    def build_flashlight_glow(self, boost=False):
        """כתם אור רך במרכז המסך (נוסף במצב Additive) - נותן תחושת קרן פנס אמיתית"""
        surf = pygame.Surface((WIDTH, HEIGHT))
        surf.fill((0, 0, 0))
        cx, cy = WIDTH // 2, HEIGHT // 2 + 20
        peak = (70, 58, 40) if boost else (30, 25, 17)
        max_r = 400
        steps = 36
        for i in range(steps, 0, -1):
            t = 1 - i / steps
            col = tuple(int(c * (t ** 1.4)) for c in peak)
            pygame.draw.ellipse(surf, col, (cx - max_r * i / steps * 1.25, cy - max_r * i / steps,
                                            2 * max_r * i / steps * 1.25, 2 * max_r * i / steps))
        return surf

    def build_menu_bg(self):
        surf = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = y / HEIGHT
            pygame.draw.line(surf, lerp_color((22, 6, 16), (2, 2, 5), t ** 0.7), (0, y), (WIDTH, y))
        return surf

    def build_hud_bg(self):
        h = 40
        surf = pygame.Surface((WIDTH, h), pygame.SRCALPHA)
        for y in range(h):
            a = int(215 - 125 * (y / h))
            pygame.draw.line(surf, (4, 3, 8, a), (0, y), (WIDTH, y))
        pygame.draw.line(surf, (110, 30, 42, 150), (0, h - 1), (WIDTH, h - 1))
        return surf

    def soft_glow(self, cx, cy, radius, color, alpha=70, target=None):
        """הילה רכה (מעגל מתפוגג) - נשמרת במטמון לפי רדיוס/צבע"""
        radius = int(max(6, min(radius, 420)))
        r = radius // 8 * 8 + 8
        a = max(5, int(alpha) // 5 * 5)
        key = (r, color, a)
        surf = self._glow_cache.get(key)
        if surf is None:
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            steps = 18
            for i in range(steps, 0, -1):
                ai = int(a * (1 - i / steps) ** 1.5)
                pygame.draw.circle(surf, (*color, ai), (r, r), int(r * i / steps))
            self._glow_cache[key] = surf
        (target or self.screen).blit(surf, (cx - r, cy - r))

    def draw_glow_text(self, text, font, color, center, glow=(170, 10, 20)):
        """טקסט עם זוהר ומסגרת צל"""
        base = font.render(rtl(text), True, color)
        g = font.render(rtl(text), True, glow).convert_alpha()
        g.set_alpha(34)
        for r in (6, 4, 2):
            for k in range(8):
                a = k * math.pi / 4
                self.screen.blit(g, g.get_rect(center=(center[0] + math.cos(a) * r, center[1] + math.sin(a) * r)))
        shadow = font.render(rtl(text), True, (0, 0, 0))
        self.screen.blit(shadow, shadow.get_rect(center=(center[0] + 2, center[1] + 3)))
        self.screen.blit(base, base.get_rect(center=center))

    def draw_button(self, rect, label, hover):
        """כפתור מעוצב: צל, מעבר צבע, פינות מעוגלות וקו הדגשה"""
        shadow = pygame.Surface((rect.w + 24, rect.h + 24), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120), (6, 10, rect.w + 12, rect.h + 8), border_radius=18)
        self.screen.blit(shadow, (rect.x - 12, rect.y - 8))

        top = (130, 244, 172) if hover else (98, 214, 144)
        bottom = (52, 160, 100) if hover else (34, 120, 80)
        grad = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(rect.h):
            pygame.draw.line(grad, lerp_color(top, bottom, y / rect.h), (0, y), (rect.w, y))
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=14)
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        self.screen.blit(grad, rect)
        pygame.draw.rect(self.screen, (225, 255, 235) if hover else (170, 240, 200), rect, 2, border_radius=14)
        shine = pygame.Surface((rect.w - 12, rect.h // 2 - 4), pygame.SRCALPHA)
        pygame.draw.rect(shine, (255, 255, 255, 38), shine.get_rect(), border_radius=10)
        self.screen.blit(shine, (rect.x + 6, rect.y + 4))
        txt = self.font_button.render(rtl(label), True, (6, 28, 16))
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def draw_pill(self, text, color, x, y, anchor="left"):
        """תווית קטנה מעוגלת עם נקודת סטטוס צבעונית (לשורת ה-HUD)"""
        label = self.font_small.render(rtl(text), True, color)
        pw, ph = label.get_width() + 38, 26
        pill = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(pill, (*color, 34), (0, 0, pw, ph), border_radius=13)
        pygame.draw.rect(pill, (*color, 140), (0, 0, pw, ph), 1, border_radius=13)
        pygame.draw.circle(pill, color, (pw - 15, ph // 2), 4)
        pill.blit(label, (12, (ph - label.get_height()) // 2))
        rect = pill.get_rect()
        if anchor == "right":
            rect.topright = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(pill, rect)
        return rect

    # ------------------------------------------------------------
    # רינדור המבוך
    # ------------------------------------------------------------
    def cast_rays(self):
        """Raycasting מדויק (DDA) עם קירות מרקמיים, צל לפי כיוון הקיר ותאורת פנס.
        מחזיר depth_buffer (מרחק לפי עמודת מסך)."""
        depth_buffer = [MAX_DEPTH] * NUM_RAYS
        px, py = self.player.x / CELL, self.player.y / CELL
        start_angle = self.player.angle - FOV / 2
        in_room = self.view_room
        grid = self.room_grid if in_room else self.grid
        rows, cols = len(grid), len(grid[0])
        screen = self.screen
        boost = self.light_boost
        radius = self.effective_light_radius
        flicker = self.flicker
        textures = self.wall_textures
        decals = self.room_decals if in_room else self.wall_decals
        player_angle = self.player.angle
        scale = pygame.transform.scale
        door_cx, door_cy, door_dir = self.room_door if in_room else self.exit_wall
        closets = [] if in_room else [sp for sp in self.hiding_spots
                                      if math.hypot(sp["x"] - self.player.x, sp["y"] - self.player.y) < MAX_DEPTH]
        skip_spot = self.current_spot  # מבפנים לא מציירים את הארון שאתה בתוכו
        closet_front = self.closet_textures["front"]
        closet_side = self.closet_textures["side"]

        for ray in range(NUM_RAYS):
            angle = start_angle + ray * (FOV / NUM_RAYS)
            dx, dy = math.cos(angle), math.sin(angle)
            map_x, map_y = int(px), int(py)
            delta_x = abs(1.0 / dx) if dx != 0 else 1e30
            delta_y = abs(1.0 / dy) if dy != 0 else 1e30
            if dx < 0:
                step_x, side_x = -1, (px - map_x) * delta_x
            else:
                step_x, side_x = 1, (map_x + 1.0 - px) * delta_x
            if dy < 0:
                step_y, side_y = -1, (py - map_y) * delta_y
            else:
                step_y, side_y = 1, (map_y + 1.0 - py) * delta_y

            side = 0
            hit = False
            for _ in range(80):
                if side_x < side_y:
                    side_x += delta_x
                    map_x += step_x
                    side = 0
                else:
                    side_y += delta_y
                    map_y += step_y
                    side = 1
                if map_x < 0 or map_x >= cols or map_y < 0 or map_y >= rows:
                    hit = True
                    break
                if grid[map_y][map_x] == 1:
                    hit = True
                    break

            if hit:
                dist_cells = (side_x - delta_x) if side == 0 else (side_y - delta_y)
                dist = min(MAX_DEPTH, dist_cells * CELL)
            else:
                dist_cells = MAX_DEPTH / CELL
                dist = MAX_DEPTH

            corrected = max(dist * math.cos(angle - player_angle), 1)  # תיקון "עין דגה"
            depth_buffer[ray] = corrected

            true_h = (CELL * HEIGHT) / corrected

            # תאורה לפי מרחק מהפנס
            if boost:
                light = 1.0
            else:
                light = max(0.0, min(1.0, 1 - (corrected / radius) - flicker))

            # האם הקרן פגעה בדיוק בפאה של הקיר שבה בנויה הדלת?
            is_door = (hit and map_x == door_cx and map_y == door_cy
                       and ((side == 0 and door_dir[1] == 0 and step_x == door_dir[0])
                            or (side == 1 and door_dir[0] == 0 and step_y == door_dir[1])))

            strip_x = ray * STRIP_WIDTH
            if (light <= 0.01 and not is_door) or not hit:
                h = int(min(HEIGHT, true_h))
                pygame.draw.rect(screen, (2, 2, 4), (strip_x, (HEIGHT - h) // 2, STRIP_WIDTH + 1, h))
            else:
                # איזה מקום בקיר נפגע (0..1) - קובע איזו עמודה של המרקם מציירים
                if side == 0:
                    wx = py + dist_cells * dy
                else:
                    wx = px + dist_cells * dx
                wx -= math.floor(wx)
                if (side == 0 and dx > 0) or (side == 1 and dy < 0):
                    wx = 1 - wx
                decal = decals.get((map_x, map_y))
                flip = is_door
                if is_door:
                    tex = textures["door_room" if in_room else "door"]
                elif in_room:
                    tex = textures[decal or "concrete"]
                    flip = decal is not None   # שלטים עם כיתוב - לא הפוכים במראה
                else:
                    tex = textures["blood" if decal == "blood" else "crack" if decal == "crack" else "brick"]
                TS = tex.get_width()  # לדלת ולשלטים יש מרקם ברזולוציה גבוהה יותר
                tex_x = min(TS - 1, int((1 - wx if flip else wx) * TS))

                if true_h <= HEIGHT:
                    h = max(1, int(true_h))
                    col = scale(tex.subsurface((tex_x, 0, 1, TS)), (STRIP_WIDTH + 1, h))
                    y = (HEIGHT - h) // 2
                else:
                    frac = HEIGHT / true_h
                    src_h = max(1, int(TS * frac))
                    src_y = (TS - src_h) // 2
                    col = scale(tex.subsurface((tex_x, src_y, 1, src_h)), (STRIP_WIDTH + 1, HEIGHT))
                    y = 0

                shade = 0.74 if side == 1 else 1.0  # קירות בכיוון אחד מוצללים - עומק
                k = light * shade
                col.fill((int(255 * k), int(240 * k), int(222 * k)), special_flags=pygame.BLEND_RGB_MULT)
                if is_door:
                    # השלט הירוק זוהר גם בחושך מוחלט
                    gtex = textures["door_room_glow" if in_room else "door_glow"]
                    if true_h <= HEIGHT:
                        gcol = scale(gtex.subsurface((tex_x, 0, 1, TS)), (STRIP_WIDTH + 1, h))
                    else:
                        gcol = scale(gtex.subsurface((tex_x, src_y, 1, src_h)), (STRIP_WIDTH + 1, HEIGHT))
                    col.blit(gcol, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
                screen.blit(col, (strip_x, y))

            # -------- ארונות תלת-ממדיים: קופסה אמיתית בעולם, נבדקת מול הקרן --------
            best = None
            for spot in closets:
                if spot is skip_spot:
                    continue
                hitc = _ray_box(self.player.x, self.player.y, dx, dy, spot["box"])
                if hitc is not None and hitc[0] < dist and (best is None or hitc[0] < best[0]):
                    best = (hitc[0], hitc[1], hitc[2], spot)
            if best is not None:
                t_hit, axis, u, spot = best
                c_corr = max(t_hit * math.cos(angle - player_angle), 1)
                depth_buffer[ray] = min(depth_buffer[ray], c_corr)
                full_h = (CELL * HEIGHT) / c_corr
                floor_y = HEIGHT / 2 + full_h / 2
                top_y = floor_y - full_h * CLOSET_HEIGHT
                if boost:
                    c_light = 1.0
                else:
                    c_light = max(0.0, min(1.0, 1 - (c_corr / radius) - flicker))
                vis_top = max(0, int(top_y))
                vis_bot = min(HEIGHT, int(floor_y))
                if vis_bot > vis_top:
                    if c_light <= 0.01:
                        pygame.draw.rect(screen, (2, 2, 4), (strip_x, vis_top, STRIP_WIDTH + 1, vis_bot - vis_top))
                    else:
                        # הפנים הקדמיות (עם הדלתות) - רק הצד שפונה למסדרון
                        is_front = (axis == spot["front_axis"])
                        ctex = closet_front if is_front else closet_side
                        tw, th = ctex.get_size()
                        ctex_x = min(tw - 1, max(0, int(u * tw)))
                        span = max(1e-6, floor_y - top_y)
                        sy0 = int((vis_top - top_y) / span * th)
                        sy1 = int(math.ceil((vis_bot - top_y) / span * th))
                        sy0 = max(0, min(th - 1, sy0))
                        sy1 = max(sy0 + 1, min(th, sy1))
                        ccol = scale(ctex.subsurface((ctex_x, sy0, 1, sy1 - sy0)),
                                     (STRIP_WIDTH + 1, vis_bot - vis_top))
                        c_shade = 1.0 if is_front else 0.68
                        kk = c_light * c_shade
                        ccol.fill((int(255 * kk), int(236 * kk), int(215 * kk)),
                                  special_flags=pygame.BLEND_RGB_MULT)
                        screen.blit(ccol, (strip_x, vis_top))

        return depth_buffer

    def draw_background(self):
        if self.view_room:
            if getattr(self, "bg_room", None) is None:
                self.bg_room = self.build_room_floor_ceiling()
            self.screen.blit(self.bg_room, (0, 0))
            return
        self.screen.blit(self.bg_boost if self.light_boost else self.bg_normal, (0, 0))

    def build_room_floor_ceiling(self):
        """תקרה ורצפה מוארות של חדר הבקרה"""
        surf = pygame.Surface((WIDTH, HEIGHT))
        half = HEIGHT // 2
        for y in range(half):
            t = (1 - y / half) ** 1.2
            pygame.draw.line(surf, lerp_color((40, 44, 48), (96, 102, 106), t), (0, y), (WIDTH, y))
            s_ = (y / half) ** 1.1
            pygame.draw.line(surf, lerp_color((30, 32, 36), (62, 66, 72), s_), (0, half + y), (WIDTH, half + y))
        return surf

    def draw_flashlight_glow(self):
        """אור פנס רך שנוסף על המסך (Additive) - רק כשהפנס פעיל"""
        glow = self.glow_boost if self.light_boost else self.glow_normal
        self.screen.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def build_vignette(self):
        """מסכת כהות אליפטית וחלקה בפינות המסך (מחושבת פעם אחת)"""
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        cx, cy = WIDTH / 2, HEIGHT / 2
        steps = 56
        for i in range(steps, 0, -1):
            f = i / steps
            alpha = int(215 * max(0.0, (f - 0.28) / 0.72) ** 1.6)
            rx, ry = int(WIDTH * 0.78 * f), int(HEIGHT * 0.82 * f)
            pygame.draw.ellipse(surf, (0, 0, 0, alpha), (cx - rx, cy - ry, rx * 2, ry * 2))
        return surf

    # ------------------------------------------------------------
    # ממשק (HUD, מפה, תפריטים)
    # ------------------------------------------------------------
    def _build_minimap_static(self, scale):
        map_w, map_h = COLS * scale, ROWS * scale
        layer = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        for row in range(ROWS):
            for col in range(COLS):
                if self.grid[row][col] == 1:
                    color = (86, 72, 106, 235)
                else:
                    color = (16, 14, 24, 210)
                pygame.draw.rect(layer, color, (col * scale, row * scale, scale, scale))
        mask = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=8)
        layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return layer

    def draw_minimap(self):
        """מיני-מפה מעוצבת: מסגרת מעוגלת, חרוט ראייה, דלת זוהרת, יומן פועם"""
        scale = 5
        map_w, map_h = COLS * scale, ROWS * scale
        pad = 10
        if getattr(self, "_mm_grid", None) is not self.grid:
            self._mm_static = self._build_minimap_static(scale)
            self._mm_grid = self.grid

        surf = self._mm_static.copy()
        t = pygame.time.get_ticks() * 0.004
        pulse = 0.5 + 0.5 * math.sin(t)

        ex, ey = int(self.exit_pos[0] / CELL * scale), int(self.exit_pos[1] / CELL * scale)
        pygame.draw.circle(surf, (*DOOR_COLOR, 70), (ex, ey), 6)
        pygame.draw.rect(surf, DOOR_COLOR, (ex - 3, ey - 3, 6, 6), border_radius=2)

        if not self.journal_collected:
            jx = int(self.journal_pos[0] / CELL * scale)
            jy = int(self.journal_pos[1] / CELL * scale)
            pygame.draw.circle(surf, (240, 210, 110, int(60 + 80 * pulse)), (jx, jy), int(4 + 3 * pulse))
            pygame.draw.circle(surf, (250, 220, 120), (jx, jy), 3)

        # ארונות מחבוא - ריבועים חומים קטנים
        for s in self.hiding_spots:
            sx_, sy_ = int(s["x"] / CELL * scale), int(s["y"] / CELL * scale)
            pygame.draw.rect(surf, (150, 100, 60), (sx_ - 2, sy_ - 2, 4, 4))

        if self.monster.awake:
            mx = int(self.monster.x / CELL * scale)
            my = int(self.monster.y / CELL * scale)
            pygame.draw.circle(surf, (*MONSTER_AWAKE, int(70 + 100 * pulse)), (mx, my), int(5 + 3 * pulse))
            pygame.draw.circle(surf, MONSTER_AWAKE, (mx, my), 3)

        px, py = self.player.x / CELL * scale, self.player.y / CELL * scale
        a = self.player.angle
        cone = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(cone, (120, 215, 245, 55), [
            (px, py),
            (px + math.cos(a - FOV / 2) * 20, py + math.sin(a - FOV / 2) * 20),
            (px + math.cos(a + FOV / 2) * 20, py + math.sin(a + FOV / 2) * 20)])
        surf.blit(cone, (0, 0))
        tip = (px + math.cos(a) * 6, py + math.sin(a) * 6)
        left = (px + math.cos(a + 2.5) * 4, py + math.sin(a + 2.5) * 4)
        right = (px + math.cos(a - 2.5) * 4, py + math.sin(a - 2.5) * 4)
        pygame.draw.polygon(surf, (110, 215, 245), [tip, left, right])

        panel = pygame.Surface((map_w + 12, map_h + 12), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
        pygame.draw.rect(panel, (130, 50, 66, 190), panel.get_rect(), 2, border_radius=12)
        panel.blit(surf, (6, 6))
        self.screen.blit(panel, (WIDTH - map_w - 12 - pad, 48))

    def draw_hud(self):
        self.screen.blit(self.hud_bg, (0, 0))

        status_label, status_color = {
            "chase": ("השומר ער - ברח!", (255, 90, 100)),
            "search": ("השומר מחפש אותך...", (255, 160, 80)),
            "return": ("השומר חוזר למאורה", (230, 190, 110)),
        }.get(self.monster.state, ("השומר ישן", (140, 215, 160)))
        if TEST_NO_MONSTER:
            status_label, status_color = "מצב בדיקה - בלי מפלצת", (120, 200, 255)
        r1 = self.draw_pill(status_label, status_color, 10, 7)
        if self.player.hidden:
            r1 = self.draw_pill("מתחבא", (170, 140, 220), r1.right + 8, 7)

        journal_label = "יומן: נאסף" if self.journal_collected else "יומן: חסר"
        journal_color = (150, 225, 160) if self.journal_collected else (245, 215, 115)
        self.draw_pill(journal_label, journal_color, r1.right + 8, 7)

        if self.light_boost:
            self.draw_pill("פנס חזק! (1)", (255, 235, 150), WIDTH - 10, 7, anchor="right")

        if self.message_timer > 0:
            msg = self.font_small.render(rtl(self.message), True, WHITE)
            box = msg.get_rect(center=(WIDTH // 2, 20)).inflate(26, 10)
            bg = pygame.Surface(box.size, pygame.SRCALPHA)
            pygame.draw.rect(bg, (0, 0, 0, 150), bg.get_rect(), border_radius=14)
            pygame.draw.rect(bg, (200, 200, 200, 90), bg.get_rect(), 1, border_radius=14)
            self.screen.blit(bg, box)
            self.screen.blit(msg, msg.get_rect(center=box.center))

        # רמז לחיצה ליד ארון / בתוך ארון
        if not (self.game_over or self.win):
            hint = None
            if self.player.hidden:
                hint = "Enter - לצאת מהארון  |  A או D - להציץ"
            elif not self.forced_turn_active and self.nearest_hiding_spot() is not None:
                hint = "Enter - להתחבא בארון"
            if hint:
                txt = self.font_small.render(rtl(hint), True, (235, 220, 200))
                box = txt.get_rect(center=(WIDTH // 2, HEIGHT - 34)).inflate(28, 12)
                bg = pygame.Surface(box.size, pygame.SRCALPHA)
                pygame.draw.rect(bg, (0, 0, 0, 170), bg.get_rect(), border_radius=14)
                pygame.draw.rect(bg, (150, 100, 60, 180), bg.get_rect(), 1, border_radius=14)
                self.screen.blit(bg, box)
                self.screen.blit(txt, txt.get_rect(center=box.center))

    def draw_end_screen(self, title, color, subtitle):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))

        card = pygame.Rect(0, 0, 640, 230)
        card.center = (WIDTH // 2, HEIGHT // 2 - 40)
        panel = pygame.Surface(card.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (10, 6, 14, 215), panel.get_rect(), border_radius=22)
        pygame.draw.rect(panel, (*color, 170), panel.get_rect(), 2, border_radius=22)
        self.screen.blit(panel, card)

        self.draw_glow_text(title, self.font_big, color, (WIDTH // 2, card.centery - 22), glow=color)
        sub_text = self.font_small.render(subtitle, True, (200, 200, 210))
        self.screen.blit(sub_text, sub_text.get_rect(center=(WIDTH // 2, card.centery + 48)))

        hover = self.restart_button_rect.collidepoint(pygame.mouse.get_pos())
        self.draw_button(self.restart_button_rect, "התחל מהתחלה", hover)

    def draw_menu(self):
        """מסך הבית: רקע מדורג, כותרת זוהרת מהבהבת, כרטיס עלילה וכפתור מעוצב"""
        self.screen.blit(self.menu_bg, (0, 0))
        t = pygame.time.get_ticks() * 0.001
        self.soft_glow(WIDTH // 2, 86, 300 + 18 * math.sin(t * 1.7), (150, 10, 24), 95)

        flick = 1.0 if (math.sin(t * 13) * math.sin(t * 5.3)) > -0.82 else 0.55
        title_col = (int(235 * flick), int(60 * flick), int(72 * flick))
        self.draw_glow_text("המתחם הנטוש", self.font_big, title_col, (WIDTH // 2, 86))
        pygame.draw.line(self.screen, (120, 30, 44), (WIDTH // 2 - 150, 122), (WIDTH // 2 + 150, 122), 2)

        lines = self.wrap_text(STORY_TEXT, self.font_story, WIDTH - 180)
        line_height = self.font_story.get_linesize() + 6
        start_y = 168
        card = pygame.Rect(0, 0, WIDTH - 110, len(lines) * line_height + 36)
        card.midtop = (WIDTH // 2, start_y - 26)
        panel = pygame.Surface(card.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 135), panel.get_rect(), border_radius=18)
        pygame.draw.rect(panel, (110, 36, 50, 150), panel.get_rect(), 1, border_radius=18)
        self.screen.blit(panel, card)
        for i, line in enumerate(lines):
            line_surf = self.font_story.render(rtl(line), True, (232, 226, 232))
            self.screen.blit(line_surf, line_surf.get_rect(center=(WIDTH // 2, start_y + i * line_height)))

        hover = self.play_button_rect.collidepoint(pygame.mouse.get_pos())
        self.draw_button(self.play_button_rect, "שחק", hover)
        self.screen.blit(self.vignette_surface, (0, 0))

    def compute_shake_offset(self, extra_shake=0.0):
        """מחשב היסט רעד - כרגע רק מרעד חד-פעמי (כמו בטריפה), לא בגלל קרבה למפלצת"""
        intensity = extra_shake

        if intensity <= 0.05:
            return 0, 0

        t = pygame.time.get_ticks() * 0.02
        ox = math.sin(t * 2.3) * intensity + random.uniform(-1, 1) * intensity * 0.35
        oy = math.cos(t * 1.7) * intensity + random.uniform(-1, 1) * intensity * 0.35
        return ox, oy

    def present_frame(self, extra_shake=0.0):
        """מעתיק את משטח הציור הפנימי למסך בפועל, עם היסט רעד אם המפלצת קרובה"""
        offset_x, offset_y = self.compute_shake_offset(extra_shake)
        self.display.fill(BLACK)
        self.display.blit(self.screen, (offset_x, offset_y))
        pygame.display.flip()

    def build_wall_decals(self, grid):
        """מסמן קירות אקראיים לצייר עליהם כתמי דם/סדקים - לאווירה מפחידה יותר במבוך"""
        decals = {}
        rows, cols = len(grid), len(grid[0])
        for row in range(rows):
            for col in range(cols):
                if grid[row][col] != 1:
                    continue
                # רק קירות שגובלים במעבר פתוח (כלומר "נראים" בפועל)
                touches_floor = False
                for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nc, nr = col + dc, row + dr
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                        touches_floor = True
                        break
                if touches_floor and random.random() < 0.16:
                    decals[(col, row)] = "blood" if random.random() < 0.6 else "crack"
        return decals

    def build_closet_overlay(self):
        """מבט מתוך ארון: דלתות עץ כהות שמכסות את המסך, עם חרכים אופקיים צרים להצצה"""
        rng = random.Random(5)
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        surf.fill((14, 9, 6, 252))
        # סיבי עץ
        for _ in range(260):
            x = rng.randint(0, WIDTH)
            y = rng.randint(0, HEIGHT)
            ln = rng.randint(30, 140)
            shade = rng.randint(18, 34)
            pygame.draw.line(surf, (shade + 8, shade, shade - 6, 255), (x, y), (x + ln, y + rng.randint(-2, 2)), 1)
        # חרכים: פסים אופקיים שקופים במרכז המסך
        slit_h, gap = 13, 30
        top = int(HEIGHT * 0.26)
        y = top
        while y < HEIGHT * 0.74:
            # שקיפות מלאה בחרך, עם קצוות רכים
            surf.fill((0, 0, 0, 0), (60, y, WIDTH - 120, slit_h))
            pygame.draw.line(surf, (60, 42, 28, 230), (60, y - 1), (WIDTH - 60, y - 1), 2)        # שפה עליונה מוארת
            pygame.draw.line(surf, (4, 2, 1, 255), (60, y + slit_h), (WIDTH - 60, y + slit_h), 3)  # צל תחתון
            y += slit_h + gap
        # התפר בין שתי הדלתות
        pygame.draw.rect(surf, (6, 4, 2, 255), (WIDTH // 2 - 4, 0, 8, HEIGHT))
        pygame.draw.line(surf, (50, 36, 24, 255), (WIDTH // 2 + 4, 0), (WIDTH // 2 + 4, HEIGHT), 1)
        return surf

    def build_closet_textures(self):
        """מרקמי הארון התלת-ממדי: חזית עם שתי דלתות וחרכים, וצד עם קרשים"""
        rng = random.Random(77)
        W, H = 64, 96

        def wood_noise(surf):
            for y in range(H):
                for x in range(W):
                    r, g, b = surf.get_at((x, y))[:3]
                    n = rng.randint(-7, 7) + int(4 * math.sin(x * 0.9 + y * 0.05))
                    surf.set_at((x, y), (max(0, min(255, r + n)), max(0, min(255, g + n)),
                                         max(0, min(255, b + n))))

        # ---- חזית ----
        front = pygame.Surface((W, H))
        front.fill((60, 40, 26))                       # מסגרת
        pygame.draw.rect(front, (78, 52, 34), (0, 0, W, 6))   # כרכוב עליון
        pygame.draw.rect(front, (40, 26, 17), (0, 6, W, 2))
        pygame.draw.rect(front, (44, 29, 19), (0, H - 6, W, 6))  # בסיס
        for i, (dx0, dx1) in enumerate(((4, 31), (33, 60))):
            door = pygame.Rect(dx0, 10, dx1 - dx0, H - 18)
            pygame.draw.rect(front, (96, 64, 42), door)
            pygame.draw.rect(front, (50, 33, 22), door, 1)
            # חרכים (תריס) בחלק העליון
            for k in range(7):
                yy = 16 + k * 5
                pygame.draw.line(front, (22, 13, 8), (door.left + 4, yy), (door.right - 5, yy), 2)
                pygame.draw.line(front, (124, 86, 58), (door.left + 4, yy + 2), (door.right - 5, yy + 2), 1)
            # לוח תחתון שקוע
            panel = pygame.Rect(door.left + 4, 56, door.w - 8, 26)
            pygame.draw.rect(front, (78, 52, 34), panel)
            pygame.draw.line(front, (54, 36, 24), panel.topleft, panel.topright, 1)
            pygame.draw.line(front, (54, 36, 24), panel.topleft, panel.bottomleft, 1)
            pygame.draw.line(front, (118, 82, 55), panel.bottomleft, panel.bottomright, 1)
            # ידית
            hx = door.right - 4 if i == 0 else door.left + 3
            pygame.draw.circle(front, (205, 178, 105), (hx, 51), 2)
        pygame.draw.line(front, (20, 12, 8), (32, 10), (32, H - 8), 2)  # התפר בין הדלתות
        # שריטות דם
        for k in range(3):
            x0 = 12 + k * 4
            pygame.draw.line(front, (120, 12, 14), (x0, 50), (x0 + 3, 68), 1)
        wood_noise(front)

        # ---- צד ----
        side = pygame.Surface((W, H))
        side.fill((66, 44, 29))
        for x in range(0, W, 13):
            pygame.draw.line(side, (36, 23, 15), (x, 0), (x, H), 2)
            pygame.draw.line(side, (90, 62, 41), (x + 2, 0), (x + 2, H), 1)
        pygame.draw.rect(side, (78, 52, 34), (0, 0, W, 6))
        pygame.draw.rect(side, (44, 29, 19), (0, H - 6, W, 6))
        wood_noise(side)

        # הצללה: למטה ולמעלה כהה יותר
        for tex in (front, side):
            for y in range(H):
                f = int(255 * (0.72 + 0.28 * math.sin(math.pi * (y + 0.5) / H) ** 0.5))
                tex.fill((f, f, f), (0, y, W, 1), special_flags=pygame.BLEND_RGB_MULT)
        return {"front": front, "side": side}

    def draw_closet_view(self):
        if self.player.hidden:
            self.screen.blit(self.closet_overlay, (0, 0))

    def build_grain(self):
        """בונה טקסטורת 'גרעיניות' סטטית - כתמים כהים פזורים לתחושת סרט ישן/מלוכלך"""
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for _ in range(1400):
            x = random.randint(0, WIDTH - 1)
            y = random.randint(0, HEIGHT - 1)
            shade = 0 if random.random() < 0.85 else 255
            alpha = random.randint(12, 42)
            surf.set_at((x, y), (shade, shade, shade, alpha))
        return surf

    def draw_vignette(self):
        """כהות עדינה בפינות המסך - נותן תחושה קלאוסטרופובית ומאיימת יותר"""
        if self.light_boost:
            return  # בזמן פנס חזק - אין שום כהות, המסך כולו מואר
        self.screen.blit(self.vignette_surface, (0, 0))

    def draw_grain(self):
        """טקסטורת גרעיניות עדינה - נותנת תחושת סרט ישן/מלוכלך, מגבירה אי-נוחות"""
        self.screen.blit(self.grain_surface, (0, 0))

    def draw_heartbeat_pulse(self):
        """הבזק אדום פועם כמו דופק לב, מתחזק ככל שהמפלצת קרובה יותר"""
        if not self.monster.awake or self.win:
            return
        dist = math.hypot(self.monster.x - self.player.x, self.monster.y - self.player.y)
        threshold = SHAKE_DISTANCE * 1.6
        if dist >= threshold:
            return
        closeness = 1 - dist / threshold
        t = pygame.time.get_ticks() * 0.001
        # פעימה כפולה חדה - כמו לב שמפחד, מהירה ועוצמתית יותר ככל שקרובים
        beat_speed = 6.0 + closeness * 5.0
        beat = abs(math.sin(t * beat_speed)) ** 6
        alpha = int(150 * closeness * beat)
        if alpha > 2:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((150, 0, 0, alpha))
            self.screen.blit(overlay, (0, 0))

    def draw_alarm(self):
        """אזעקה אדומה - כשהשומר ער: מסגרת אדומה מהבהבת, גוון אדום פועם וכיתוב 'המפלצת התעוררה'."""
        if (self.monster.state != "chase" or self.win or self.game_over
                or self.jumpscare_active):
            return  # האזעקה המלאה רק במרדף - כשהוא מחפש, השקט מפחיד יותר
        t = pygame.time.get_ticks() * 0.001
        wave = math.sin(t * 9.0)          # ~1.4 הבהובים בשנייה
        soft = 0.5 + 0.5 * wave
        blink = wave > 0

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((165, 0, 0, int(20 + 34 * soft)))
        self.screen.blit(overlay, (0, 0))

        thick = 16
        col = (255, 45, 45) if blink else (110, 0, 0)
        frame = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(thick):
            a = int((205 * (1 - i / thick)) * (0.55 + 0.45 * soft))
            pygame.draw.rect(frame, (*col, a), (i, i, WIDTH - 2 * i, HEIGHT - 2 * i), 1)
        self.screen.blit(frame, (0, 0))

        if blink:
            label = self.font_note.render(rtl("המפלצת התעוררה"), True, (255, 70, 70))
            self.screen.blit(label, label.get_rect(center=(WIDTH // 2, 54)))

    def draw_glimpse(self):
        """הבזק צל קצרצר וחשוד - לא המפלצת האמיתית, רק תחושה שמישהו שם, בגובה מלא ומאיים"""
        if not self.glimpse_active:
            return
        gx, gy = self.glimpse_pos
        h = 340
        w = 110
        alpha = 250
        surf = pygame.Surface((w, int(h) + 10), pygame.SRCALPHA)
        body_rect = pygame.Rect(0, 0, int(w * 0.65), h)
        body_rect.center = (w / 2, h / 2 + 5)
        pygame.draw.ellipse(surf, (2, 1, 3, alpha), body_rect)
        eye_y = int(h * 0.16)
        pygame.draw.circle(surf, (180, 10, 10, alpha), (int(w * 0.38), eye_y), 4)
        pygame.draw.circle(surf, (180, 10, 10, alpha), (int(w * 0.62), eye_y), 4)
        self.screen.blit(surf, (gx - w / 2, gy - h / 2 - 5))

    def draw_static_glitch(self):
        """רעש/גליץ' רגעי על המסך - פסים אופקיים מעוותים, מגביר תחושת אי-נוחות ותקלה"""
        if self.static_glitch_alpha <= 1:
            return
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        num_bars = random.randint(4, 9)
        for _ in range(num_bars):
            by = random.randint(0, HEIGHT - 6)
            bh = random.randint(2, 10)
            bx_offset = random.randint(-30, 30)
            shade = random.choice([(0, 0, 0), (60, 5, 8), (200, 200, 200)])
            a = int(self.static_glitch_alpha * random.uniform(0.4, 1.0))
            pygame.draw.rect(overlay, (*shade, a), (bx_offset, by, WIDTH, bh))
        self.screen.blit(overlay, (0, 0))

    def draw_whisper(self):
        """טקסט לחישה עמום שמופיע ונעלם - אווירה, לא מידע קריטי למשחק"""
        if self.whisper_timer <= 0:
            return
        t = min(1.0, self.whisper_timer / 2.6)
        alpha = int(190 * math.sin(t * math.pi))
        if alpha <= 2:
            return
        text_surf = self.font_small.render(rtl(self.whisper_text), True, (175, 165, 170))
        text_surf.set_alpha(max(0, alpha))
        self.screen.blit(text_surf, text_surf.get_rect(center=self.whisper_pos))

    def update_ambient_dread(self, dt):
        """מנהל את אפקטי האווירה - לחישות, הבזקי צל, פנטום וגליצ'ים - תכוף ומפחיד יותר"""
        if self.whisper_timer > 0:
            self.whisper_timer -= dt
        if self.glimpse_timer > 0:
            self.glimpse_timer -= dt
            if self.glimpse_timer <= 0:
                self.glimpse_active = False

        # גליץ'/סטטיק - עובד גם כשהשומר ער וגם כשהוא ישן, לתחושת תקלה מתמדת
        if self.static_glitch_alpha > 0:
            self.static_glitch_alpha -= 260 * dt
        self.static_glitch_timer -= dt
        if self.static_glitch_timer <= 0:
            self.static_glitch_timer = random.uniform(4, 8) if not self.monster.awake else random.uniform(1.6, 3.2)
            self.static_glitch_alpha = random.uniform(70, 130)

        if self.monster.awake:
            return  # שאר אפקטי האווירה (לחישות/פנטום) רק כשהסכנה עוד לא אמיתית

        self.dread_timer -= dt
        if self.dread_timer <= 0:
            self.dread_timer = random.uniform(4, 8)
            roll = random.random()
            if roll < 0.45:
                self.whisper_text = random.choice(WHISPER_LINES)
                self.whisper_timer = 2.6
                self.whisper_pos = (random.uniform(150, WIDTH - 150), random.uniform(90, 150))
            else:
                self.glimpse_active = True
                self.glimpse_timer = random.uniform(0.12, 0.22)
                self.glimpse_pos = (random.uniform(WIDTH * 0.1, WIDTH * 0.9),
                                     random.uniform(HEIGHT * 0.25, HEIGHT * 0.62))

    def draw_blood_effects(self):
        """מצייר את כל אפקטי הדם - כתמים דוהים, חלקיקים מתעופפים, וקווי ירי"""
        # כתמי דם גדולים דוהים - "מלא דם" שנשאר על המסך
        for m in self.blood_marks:
            alpha = max(0, min(255, int(m["alpha"])))
            surf = pygame.Surface((int(m["r"] * 2), int(m["r"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (110, 8, 10, alpha), (int(m["r"]), int(m["r"])), int(m["r"]))
            self.screen.blit(surf, (m["x"] - m["r"], m["y"] - m["r"]))

        # חלקיקי דם עפים
        for p in self.blood_particles:
            alpha = max(0, min(255, int(255 * (p["life"] / p["max_life"]))))
            surf = pygame.Surface((int(p["r"] * 2) + 2, int(p["r"] * 2) + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 15, 15, alpha), (int(p["r"]) + 1, int(p["r"]) + 1), int(p["r"]))
            self.screen.blit(surf, (p["x"] - p["r"], p["y"] - p["r"]))

        # קו ירי מהיר שדוהה
        for s in self.shot_effects:
            alpha = max(0, min(255, int(255 * (s["life"] / s["max_life"]))))
            surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(surf, (255, 235, 150, alpha), s["start"], s["end"], 2)
            self.screen.blit(surf, (0, 0))

    def get_sprite_projection(self, sx, sy, depth_buffer):
        """מחשב את מיקום וגודל הספרייט על המסך, או None אם הוא לא נראה"""
        dx = sx - self.player.x
        dy = sy - self.player.y
        dist = math.hypot(dx, dy)
        if dist < 1 or dist > self.effective_light_radius * 1.05:
            return None

        angle_to_sprite = math.atan2(dy, dx) - self.player.angle
        while angle_to_sprite > math.pi:
            angle_to_sprite -= 2 * math.pi
        while angle_to_sprite < -math.pi:
            angle_to_sprite += 2 * math.pi

        if abs(angle_to_sprite) > FOV / 2 + 0.2:
            return None

        screen_x = (0.5 + angle_to_sprite / FOV) * WIDTH
        ray_index = int(screen_x / STRIP_WIDTH)
        ray_index = max(0, min(NUM_RAYS - 1, ray_index))

        if dist > depth_buffer[ray_index] + 10:
            return None

        light_factor = 1.0 if self.light_boost else max(0.0, 1 - (dist / self.effective_light_radius))
        return screen_x, dist, light_factor

    def draw_sprite(self, sx, sy, color, size, depth_buffer, glow=False):
        """מצייר ספרייט (מפתח/דלת) עם billboarding פשוט, מוסתר מאחורי קירות"""
        proj = self.get_sprite_projection(sx, sy, depth_buffer)
        if proj is None:
            return
        screen_x, dist, light_factor = proj
        proj_size = min(320, (CELL * HEIGHT * size) / max(dist, 1))

        col = tuple(int(c * max(0.25, light_factor)) for c in color)
        rect = pygame.Rect(0, 0, proj_size, proj_size)
        rect.center = (screen_x, HEIGHT / 2 + proj_size * 0.15)
        pygame.draw.ellipse(self.screen, col, rect)
        if glow:
            pygame.draw.ellipse(self.screen, (255, 255, 255), rect, 2)

    def draw_journal(self, sx, sy, depth_buffer):
        """מצייר את היומן שצריך לאסוף - ספר קטן מרחף עם הילה עמומה כדי שאפשר למצוא אותו"""
        if self.journal_collected:
            return
        proj = self.get_sprite_projection(sx, sy, depth_buffer)
        if proj is None:
            return
        screen_x, dist, light_factor = proj
        lf = max(0.3, light_factor)

        bob = math.sin(pygame.time.get_ticks() * 0.004) * 5
        scale = min(2.4, (CELL * 4.5) / max(dist, 1))
        bw, bh = 62 * scale, 46 * scale
        if bw < 5 or bh < 4:
            return
        cx = screen_x
        cy = HEIGHT / 2 + bh * 0.7 + bob

        # הילה עמומה
        glow_r = int(max(bw, bh) * 1.5)
        self.soft_glow(cx, cy, glow_r, (255, 205, 110), 70 + 25 * math.sin(pygame.time.get_ticks() * 0.005))

        cover = tuple(int(c * lf) for c in (125, 32, 32))
        pages = tuple(int(c * lf) for c in (228, 216, 186))
        seam = tuple(int(c * lf) for c in (150, 140, 115))

        book_rect = pygame.Rect(0, 0, bw, bh)
        book_rect.center = (cx, cy)
        pygame.draw.rect(self.screen, pages, book_rect)
        pygame.draw.rect(self.screen, cover,
                         (book_rect.left, book_rect.top, max(2, bw * 0.16), bh))
        pygame.draw.rect(self.screen, cover, book_rect, max(1, int(2 * scale)))
        pygame.draw.line(self.screen, seam,
                         (book_rect.centerx, book_rect.top + 2),
                         (book_rect.centerx, book_rect.bottom - 2), max(1, int(scale)))

    def draw_note(self, sx, sy, tilt, depth_buffer, text=None):
        """מצייר פתק כתוב בדם התלוי/מונח במבוך - אווירה בלבד"""
        proj = self.get_sprite_projection(sx, sy, depth_buffer)
        if proj is None:
            return
        screen_x, dist, light_factor = proj
        if light_factor <= 0.03:
            return  # חשוך מדי לראות אותו

        note_text = text if text is not None else NOTE_TEXT

        scale = min(1.6, (CELL * 5.0) / max(dist, 1))
        if scale < 0.15:
            return

        # רקע "נייר" מלוכלך ודהוי
        paper_w, paper_h = int(120 * scale), int(70 * scale)
        if paper_w < 4 or paper_h < 4:
            return
        paper = pygame.Surface((paper_w, paper_h), pygame.SRCALPHA)
        paper_shade = int(180 * max(0.2, light_factor))
        pygame.draw.rect(paper, (paper_shade, paper_shade - 15, paper_shade - 25, 230),
                          (0, 0, paper_w, paper_h), border_radius=max(1, int(4 * scale)))
        pygame.draw.rect(paper, (20, 15, 15, 200), (0, 0, paper_w, paper_h),
                          max(1, int(2 * scale)), border_radius=max(1, int(4 * scale)))

        blood_color = tuple(int(c * max(0.35, light_factor)) for c in NOTE_COLOR)
        text_surf = self.font_note.render(rtl(note_text), True, blood_color)
        text_scale = max(0.1, min(1.0, scale * 0.75))
        tw = max(1, int(text_surf.get_width() * text_scale))
        th = max(1, int(text_surf.get_height() * text_scale))
        text_surf = pygame.transform.smoothscale(text_surf, (tw, th))
        paper.blit(text_surf, text_surf.get_rect(center=(paper_w / 2, paper_h / 2)))

        paper = pygame.transform.rotate(paper, tilt)
        rect = paper.get_rect(center=(screen_x, HEIGHT / 2 + paper_h * 0.55))
        self.screen.blit(paper, rect)

    def monster_projection(self):
        """הקרנת השומר למסך: מיקום, גובה הגוף וגבול הרצפה. None אם מחוץ לשדה הראייה או בחושך מוחלט"""
        m, p = self.monster, self.player
        dx, dy = m.x - p.x, m.y - p.y
        dist = math.hypot(dx, dy)
        if dist < 1 or dist > self.effective_light_radius * 1.05:
            return None
        ang = math.atan2(dy, dx) - p.angle
        ang = (ang + math.pi) % (2 * math.pi) - math.pi
        if abs(ang) > FOV / 2 + 0.7:
            return None
        corr = dist * math.cos(ang)
        if corr < 4:
            return None
        wall_h = (CELL * HEIGHT) / corr
        body_h = min(1600.0, wall_h * MONSTER_HEIGHT)
        light_factor = 1.0 if self.light_boost else max(0.0, 1 - dist / self.effective_light_radius)
        return {
            "x": (0.5 + ang / FOV) * WIDTH,
            "floor": HEIGHT / 2 + wall_h / 2,
            "h": body_h,
            "corr": corr,
            "light": light_factor,
        }

    def monster_visible_at(self, screen_x, corr):
        ray = int(screen_x / STRIP_WIDTH)
        if ray < 0 or ray >= NUM_RAYS:
            return False
        return self.depth_buffer[ray] > corr - 6

    # ======================================================================
    #  השומר כמודל תלת-ממדי אמיתי
    #  כל חלק בגוף הוא נקודה בעולם (x, y, גובה). הם מוקרנים דרך אותה מצלמה
    #  של הקירות, ממוינים לפי עומק ומצוירים כצינורות וכדורים מוצללים.
    #  לשומר יש כיוון משלו - מהצד רואים פרופיל, ומאחור רואים את הגב.
    # ======================================================================
    LIGHT_DIR = (-0.55, -0.83)  # כיוון האור "המדומה" על המסך - נותן נפח

    def _project3d(self, wx, wy, wz):
        p = self.player
        ca, sa = math.cos(p.angle), math.sin(p.angle)
        dx, dy = wx - p.x, wy - p.y
        fwd = dx * ca + dy * sa
        if fwd < 3:
            return None
        lat = -dx * sa + dy * ca
        k = HEIGHT / fwd
        return ((0.5 + math.atan2(lat, fwd) / FOV) * WIDTH,
                HEIGHT / 2 - (wz - CELL / 2) * k, fwd, k)

    def _faces_camera(self, point, normal):
        p = self.player
        return (normal[0] * (p.x - point[0]) + normal[1] * (p.y - point[1])
                + normal[2] * (CELL / 2 - point[2])) > 0

    def build_monster_model(self):
        """בונה את השלד בעולם. מחזיר רשימת פרימיטיבים:
           ("tube", a, b, ra, rb, palette) / ("ball", c, r, palette) / ("glow", c, r)
           ("line", a, b, w, color, normal) / ("mouth", upper, lower, normal) / ("shadow",)"""
        m = self.monster
        h = CELL * MONSTER_HEIGHT
        t = pygame.time.get_ticks() * 0.001
        f = m.facing
        Fx, Fy = math.cos(f), math.sin(f)
        Rx, Ry = math.cos(f + math.pi / 2), math.sin(f + math.pi / 2)

        def P(r, fw, z):
            return (m.x + Rx * r + Fx * fw, m.y + Ry * r + Fy * fw, z)

        def Dv(r, fw, z):
            return (Rx * r + Fx * fw, Ry * r + Fy * fw, z)

        amp = m.walk_amp
        phase = m.walk_phase
        bob = abs(math.sin(phase)) * 0.014 * h * amp
        breathe = 1 + 0.03 * math.sin(t * 2.2)
        dist = math.hypot(m.x - self.player.x, m.y - self.player.y)
        reach = 0.0
        if m.state == "chase":
            reach = max(0.0, min(1.0, (230 - dist) / 130))  # מושיט ידיים כשהוא קרוב

        SK = "skin"
        BN = "bone"
        prims = [("shadow",)]

        # ---------- רגליים ----------
        for s in (-1, 1):
            ph = phase + (0 if s > 0 else math.pi)
            stride = math.sin(ph) * 0.11 * h * amp
            lift = max(0.0, math.cos(ph)) * 0.05 * h * amp
            hip = P(s * 0.055 * h, 0, 0.5 * h + bob)
            knee = P(s * 0.075 * h, stride * 0.5 + 0.065 * h, 0.27 * h + lift * 0.6 + bob * 0.5)
            ankle = P(s * 0.07 * h, stride, 0.035 * h + lift)
            prims.append(("tube", hip, knee, 0.026 * h, 0.017 * h, SK))
            prims.append(("tube", knee, ankle, 0.017 * h, 0.011 * h, SK))
            prims.append(("ball", knee, 0.02 * h, SK))
            for k in (-1, 0, 1):  # אצבעות רגל עם טפרים, פונות קדימה
                mid = (ankle[0] + Dv(k * 0.02 * h, 0.035 * h, 0)[0],
                       ankle[1] + Dv(k * 0.02 * h, 0.035 * h, 0)[1], 0.012 * h + lift * 0.5)
                tip = (ankle[0] + Dv(k * 0.03 * h, 0.075 * h, 0)[0],
                       ankle[1] + Dv(k * 0.03 * h, 0.075 * h, 0)[1], 0.002 * h + lift * 0.3)
                prims.append(("tube", ankle, mid, 0.009 * h, 0.006 * h, SK))
                prims.append(("tube", mid, tip, 0.005 * h, 0.0015 * h, BN))

        # ---------- אגן, עמוד שדרה וחזה ----------
        prims.append(("ball", P(0, 0, 0.52 * h + bob), 0.05 * h, SK))
        prims.append(("ball", P(0, 0.015 * h, 0.585 * h + bob), 0.036 * h, SK))  # מותן צרה מאוד
        prims.append(("ball", P(0, 0.035 * h, 0.645 * h + bob), 0.05 * h * breathe, SK))
        for s, r in ((-1, 0.062), (0, 0.07), (1, 0.062)):
            prims.append(("ball", P(s * 0.05 * h, 0.055 * h, 0.71 * h + bob), r * h * breathe, SK))
        prims.append(("ball", P(0, 0.07 * h, 0.765 * h + bob), 0.055 * h, SK))

        # צלעות בולטות - קשתות על פני החזה, נראות רק מהצד שפונה אליך
        for i in range(5):
            z = 0.635 * h + i * 0.028 * h + bob
            rx = (0.1 + 0.025 * math.sin(i / 4 * math.pi)) * h * breathe
            ry = 0.072 * h * breathe
            prev = None
            for j in range(11):
                th = -1.95 + j * 0.39
                pt = P(math.sin(th) * rx, 0.055 * h + math.cos(th) * ry, z)
                if prev is not None:
                    thm = th - 0.195
                    nrm = Dv(math.sin(thm), math.cos(thm), 0)
                    prims.append(("line", prev, pt, 0.008 * h, BN, nrm))
                prev = pt
        # עצם החזה
        prims.append(("line", P(0, 0.13 * h, 0.77 * h + bob), P(0, 0.122 * h, 0.64 * h + bob),
                      0.011 * h, BN, Dv(0, 1, 0)))

        # ---------- צוואר וראש ----------
        tilt = 0.22 * math.sin(t * 0.7)
        if math.sin(t * 1.3) > 0.88:  # עווית ראש פתאומית
            tilt += 0.35 * math.sin(t * 31)
        Rh = (Rx * math.cos(tilt), Ry * math.cos(tilt), math.sin(tilt))
        Uh = (-Rx * math.sin(tilt), -Ry * math.sin(tilt), math.cos(tilt))
        hc = P(0, 0.14 * h + reach * 0.03 * h, 0.865 * h + bob)

        def HP(a, b, c):
            return (hc[0] + Rh[0] * a + Fx * b + Uh[0] * c,
                    hc[1] + Rh[1] * a + Fy * b + Uh[1] * c,
                    hc[2] + Rh[2] * a + Uh[2] * c)

        def HD(a, b, c):
            return (Rh[0] * a + Fx * b + Uh[0] * c, Rh[1] * a + Fy * b + Uh[1] * c, Rh[2] * a + Uh[2] * c)

        prims.append(("tube", P(0, 0.08 * h, 0.78 * h + bob), HP(0, -0.02 * h, -0.04 * h),
                      0.022 * h, 0.02 * h, SK))
        prims.append(("ball", HP(0, -0.012 * h, 0.012 * h), 0.068 * h, SK))   # גולגולת
        prims.append(("ball", HP(0, 0.022 * h, -0.035 * h), 0.05 * h, SK))    # לסת
        # קרניים מעוקלות אחורה
        for s in (-1, 1):
            prev, pr = None, None
            for k in range(6):
                pt = HP(s * (0.04 + 0.014 * k) * h, (-0.005 - 0.016 * k) * h,
                        (0.05 + 0.03 * k - 0.0035 * k * k) * h)
                rr = (0.017 - 0.0026 * k) * h
                if prev is not None:
                    prims.append(("tube", prev, pt, pr, rr, "horn"))
                prev, pr = pt, rr
        # ארובות עיניים ריקות עם אישונים זוהרים
        mouth_open = (0.022 + 0.008 * math.sin(t * 3.1) + reach * 0.02) * h
        for s in (-1, 1):
            n = HD(s * 0.45, 0.85, 0.15)
            sock = HP(s * 0.03 * h, 0.05 * h, 0.012 * h)
            prims.append(("socket", sock, 0.021 * h, n))
            prims.append(("eye", HP(s * 0.03 * h, 0.062 * h, 0.012 * h), 0.008 * h, n))
        # פה פעור עם שיניים
        upper, lower = [], []
        for j in range(9):
            th = -1.05 + j * (2.1 / 8)
            upper.append(HP(math.sin(th) * 0.044 * h, 0.03 * h + math.cos(th) * 0.04 * h, -0.024 * h))
            lower.append(HP(math.sin(th) * 0.04 * h, 0.027 * h + math.cos(th) * 0.036 * h,
                            -0.024 * h - mouth_open * (0.35 + 0.65 * math.cos(th))))
        prims.append(("mouth", upper, lower, HD(0, 1, -0.2)))

        # ---------- ידיים ארוכות ודקות עם טפרים ----------
        for s in (-1, 1):
            ph = phase + (math.pi if s > 0 else 0)
            sw = math.sin(ph) * 0.07 * h * amp
            sway = math.sin(t * 1.6 + s) * 0.008 * h
            shoulder = P(s * 0.125 * h, 0.07 * h, 0.765 * h + bob)
            elbow = P(s * 0.17 * h, 0.05 * h + sw * 0.5 + reach * 0.12 * h,
                      0.56 * h + bob + reach * 0.1 * h)
            hand = P(s * (0.18 - reach * 0.05) * h + sway, 0.09 * h + sw + reach * 0.26 * h,
                     0.35 * h + bob + reach * 0.3 * h)
            prims.append(("tube", P(s * 0.04 * h, 0.08 * h, 0.775 * h + bob), shoulder,
                          0.02 * h, 0.024 * h, SK))  # עצם הבריח
            prims.append(("ball", shoulder, 0.026 * h, SK))
            prims.append(("tube", shoulder, elbow, 0.02 * h, 0.014 * h, SK))
            prims.append(("ball", elbow, 0.016 * h, SK))
            prims.append(("tube", elbow, hand, 0.014 * h, 0.01 * h, SK))
            for k in range(4):  # ארבע אצבעות ארוכות, טפרים לבנים בקצה
                spread = (k - 1.5) * 0.014 * h
                d1 = Dv(spread, 0.02 * h + reach * 0.03 * h, -0.045 * h + reach * 0.03 * h)
                d2 = Dv(spread * 1.6, 0.04 * h + reach * 0.07 * h, -0.095 * h + reach * 0.05 * h)
                j1 = (hand[0] + d1[0], hand[1] + d1[1], hand[2] + d1[2])
                tip = (hand[0] + d2[0], hand[1] + d2[1], hand[2] + d2[2])
                prims.append(("tube", hand, j1, 0.006 * h, 0.004 * h, SK))
                prims.append(("tube", j1, tip, 0.004 * h, 0.001 * h, BN))
        return prims

    def draw_monster(self, sx, sy, depth_buffer):
        m = self.monster
        center = self._project3d(m.x, m.y, CELL / 2)
        if center is None:
            return
        corr = center[2]
        if corr > self.effective_light_radius * 1.05:
            return
        lf = 1.0 if self.light_boost else max(0.0, 1 - corr / self.effective_light_radius)
        L = max(0.3, lf)

        def sh(rgb, k=1.0):
            return tuple(max(0, min(255, int(c * L * k))) for c in rgb)

        palettes = {
            "skin": (sh((30, 7, 10)), sh((70, 20, 26)), sh((128, 46, 50))),
            "bone": (sh((90, 80, 70)), sh((200, 190, 172)), sh((245, 238, 222))),
            "horn": (sh((30, 22, 18)), sh((80, 64, 52)), sh((150, 130, 110))),
        }
        bone_line = tuple(int(c * (0.4 + 0.6 * L)) for c in (215, 205, 190))

        # --- הקרנה של כל הפרימיטיבים + חישוב עומק ---
        proj = []
        for pr in self.build_monster_model():
            kind = pr[0]
            if kind == "shadow":
                pts = []
                for j in range(14):
                    a = j / 14 * 2 * math.pi
                    q = self._project3d(m.x + math.cos(a) * CELL * 0.17, m.y + math.sin(a) * CELL * 0.12, 0)
                    if q:
                        pts.append(q)
                if len(pts) > 2:
                    proj.append((1e9, kind, [(q[0], q[1]) for q in pts], None))
            elif kind == "tube":
                a, b = self._project3d(*pr[1]), self._project3d(*pr[2])
                if a and b:
                    proj.append(((a[2] + b[2]) / 2, kind, [(a[0], a[1]), (b[0], b[1])],
                                 (pr[3] * a[3], pr[4] * b[3], palettes[pr[5]])))
            elif kind in ("ball", "socket", "eye"):
                if kind != "ball" and not self._faces_camera(pr[1], pr[3]):
                    continue
                c = self._project3d(*pr[1])
                if c:
                    d = c[2] - (0.5 if kind == "eye" else 0.3 if kind == "socket" else 0)
                    proj.append((d, kind, [(c[0], c[1])],
                                 (pr[2] * c[3], palettes.get(pr[3]) if kind == "ball" else None)))
            elif kind == "line":
                if not self._faces_camera(pr[1], pr[5]):
                    continue
                a, b = self._project3d(*pr[1]), self._project3d(*pr[2])
                if a and b:
                    proj.append(((a[2] + b[2]) / 2 - 0.2, kind, [(a[0], a[1]), (b[0], b[1])],
                                 (max(1, int(pr[3] * a[3])), bone_line)))
            elif kind == "mouth":
                if not self._faces_camera(pr[1][4], pr[3]):
                    continue
                up = [self._project3d(*q) for q in pr[1]]
                lo = [self._project3d(*q) for q in pr[2]]
                if all(up) and all(lo):
                    d = sum(q[2] for q in up) / len(up) - 0.4
                    proj.append((d, kind, [(q[0], q[1]) for q in up] + [(q[0], q[1]) for q in lo],
                                 (len(up), up[4][3])))
        if not proj:
            return

        # --- משטח עבודה בגודל הדמות בלבד ---
        xs = [p[0] for item in proj for p in item[2]]
        ys = [p[1] for item in proj for p in item[2]]
        pad = 0.12 * CELL * center[3] + 4
        x0 = max(0, int(min(xs) - pad))
        y0 = max(0, int(min(ys) - pad))
        x1 = min(WIDTH, int(max(xs) + pad))
        y1 = min(HEIGHT, int(max(ys) + pad))
        if x1 - x0 < 2 or y1 - y0 < 2:
            return
        surf = pygame.Surface((x1 - x0, y1 - y0), pygame.SRCALPHA)
        # הילה אדומה עמומה סביב הגוף
        chest = self._project3d(*self.build_monster_model_chest())
        if chest:
            self.soft_glow(chest[0] - x0, chest[1] - y0, CELL * 0.45 * chest[3], (170, 10, 24),
                           int(35 + 40 * lf), target=surf)

        proj.sort(key=lambda it: -it[0])
        LX, LY = self.LIGHT_DIR
        for depth, kind, pts, data in proj:
            pts = [(px - x0, py - y0) for px, py in pts]
            if kind == "shadow":
                pygame.draw.polygon(surf, (0, 0, 0, 140), pts)
            elif kind == "tube":
                self._draw_tube(surf, pts[0], pts[1], data[0], data[1], data[2])
            elif kind == "ball":
                r, (dark, mid, hi) = data[0], data[1]
                c = pts[0]
                pygame.draw.circle(surf, dark, c, max(1, r))
                if r > 1.5:
                    pygame.draw.circle(surf, mid, (c[0] + LX * r * 0.2, c[1] + LY * r * 0.2), r * 0.76)
                if r > 4:
                    pygame.draw.circle(surf, hi, (c[0] + LX * r * 0.48, c[1] + LY * r * 0.48), r * 0.3)
            elif kind == "socket":
                pygame.draw.circle(surf, (4, 0, 1), pts[0], max(1, data[0]))
            elif kind == "eye":
                r = max(1.0, data[0])
                c = pts[0]
                self.soft_glow(c[0], c[1], r * 5, (255, 20, 20), 120, target=surf)
                pygame.draw.circle(surf, (255, 60, 50), c, r)
                pygame.draw.circle(surf, (255, 235, 220), c, max(1, r * 0.45))
            elif kind == "line":
                pygame.draw.line(surf, data[1], pts[0], pts[1], data[0])
            elif kind == "mouth":
                n, k = data
                up, lo = pts[:n], pts[n:]
                pygame.draw.polygon(surf, (int(70 * L) + 10, 0, 4), up + lo[::-1])
                inner = [(u[0] * 0.3 + l[0] * 0.7, u[1] * 0.25 + l[1] * 0.75) for u, l in zip(up, lo)]
                pygame.draw.polygon(surf, (6, 0, 1), up[1:-1] + inner[::-1][1:-1])
                tooth = (int(225 * (0.45 + 0.55 * L)),) * 2 + (int(200 * (0.45 + 0.55 * L)),)
                tl = max(2, 0.02 * CELL * k)
                for i in range(n - 1):  # שיניים חדות - למעלה כלפי מטה, למטה כלפי מעלה
                    a, b = up[i], up[i + 1]
                    mx_, my_ = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                    pygame.draw.polygon(surf, tooth, [a, b, (mx_, my_ + tl)])
                    a, b = lo[i], lo[i + 1]
                    mx_, my_ = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                    pygame.draw.polygon(surf, tooth, [a, b, (mx_, my_ - tl * 0.8)])
                # דם נוטף מהפה
                mid_lo = lo[n // 2]
                pygame.draw.line(surf, (150, 8, 12), mid_lo, (mid_lo[0], mid_lo[1] + tl * 2.5),
                                 max(1, int(tl * 0.35)))

        # --- הסתרה מאחורי קירות, עמודה-עמודה ---
        first = max(0, int(x0 // STRIP_WIDTH))
        last = min(NUM_RAYS - 1, int((x1 - 1) // STRIP_WIDTH))
        run_start = None
        for ray in range(first, last + 2):
            visible = ray <= last and depth_buffer[ray] > corr - 10
            if visible and run_start is None:
                run_start = ray
            elif not visible and run_start is not None:
                self.screen.set_clip(pygame.Rect(run_start * STRIP_WIDTH, 0,
                                                 (ray - run_start) * STRIP_WIDTH, HEIGHT))
                self.screen.blit(surf, (x0, y0))
                run_start = None
        self.screen.set_clip(None)

    def build_monster_model_chest(self):
        m = self.monster
        h = CELL * MONSTER_HEIGHT
        return (m.x + math.cos(m.facing) * 0.05 * h, m.y + math.sin(m.facing) * 0.05 * h, 0.7 * h)

    def _draw_tube(self, surf, a, b, ra, rb, pal):
        """צינור מוצלל (איבר עגול): שכבה כהה, שכבת ביניים מוזזת לכיוון האור, ופס הבזק"""
        dark, mid, hi = pal
        ra, rb = max(0.6, ra), max(0.6, rb)
        dx, dy = b[0] - a[0], b[1] - a[1]
        Ln = math.hypot(dx, dy)
        pygame.draw.circle(surf, dark, a, ra)
        pygame.draw.circle(surf, dark, b, rb)
        if Ln < 0.5:
            return
        nx, ny = -dy / Ln, dx / Ln
        if nx * self.LIGHT_DIR[0] + ny * self.LIGHT_DIR[1] < 0:
            nx, ny = -nx, -ny

        def quad(kw, ko, col):
            pygame.draw.polygon(surf, col, [
                (a[0] + nx * ra * (ko + kw), a[1] + ny * ra * (ko + kw)),
                (b[0] + nx * rb * (ko + kw), b[1] + ny * rb * (ko + kw)),
                (b[0] + nx * rb * (ko - kw), b[1] + ny * rb * (ko - kw)),
                (a[0] + nx * ra * (ko - kw), a[1] + ny * ra * (ko - kw))])

        quad(1.0, 0.0, dark)
        if max(ra, rb) > 1.2:
            quad(0.58, 0.28, mid)
        if max(ra, rb) > 3:
            quad(0.18, 0.6, hi)

    def draw_monster_head(self, cx, cy, size, lf, light_factor, mouth_scale=1.0, target=None):
        """מצייר את ראש השומר במיקום/גודל נתונים. mouth_scale>1 = פה פעור רחב יותר (לרגע הטריפה)."""
        target = target or self.screen
        # פעימת אימה - קצת רעד/פעימה כדי שיראה חי ולא סטטי
        pulse = 1.0 + math.sin(pygame.time.get_ticks() * 0.018) * 0.045

        head_w = size * 0.62 * pulse
        head_h = size * 0.72 * pulse

        # "קרניים" / בליטות חדות מעל הראש
        horn_color = tuple(int(c * lf) for c in (35, 8, 12))
        horn_l = [(cx - head_w * 0.35, cy - head_h * 0.42),
                  (cx - head_w * 0.55, cy - head_h * 0.95),
                  (cx - head_w * 0.15, cy - head_h * 0.45)]
        horn_r = [(cx + head_w * 0.35, cy - head_h * 0.42),
                  (cx + head_w * 0.55, cy - head_h * 0.95),
                  (cx + head_w * 0.15, cy - head_h * 0.45)]
        pygame.draw.polygon(target, horn_color, horn_l)
        pygame.draw.polygon(target, horn_color, horn_r)

        # ראש - צבע כהה אדמדם-סגלגל, לא סימטרי כדי להיראות מעוות
        head_color = tuple(int(c * lf) for c in (50, 12, 18))
        head_rect = pygame.Rect(0, 0, head_w, head_h)
        head_rect.center = (cx, cy)
        pygame.draw.ellipse(target, head_color, head_rect)
        pygame.draw.ellipse(target, (int(20 * lf), 0, 0), head_rect, max(2, int(size * 0.02)))

        # -------- טלאי עצם חשופה - "רבע שלד": חלקים בפנים שבהם הבשר קרוע והעצם הלבנה נראית --------
        bone_color = tuple(int(c * (0.4 + 0.6 * lf)) for c in (215, 205, 190))
        bone_shadow = tuple(int(c * lf) for c in (30, 25, 25))
        bone_patch_1 = [
            (cx + head_w * 0.12, cy - head_h * 0.05),
            (cx + head_w * 0.42, cy - head_h * 0.02),
            (cx + head_w * 0.36, cy + head_h * 0.28),
            (cx + head_w * 0.08, cy + head_h * 0.22),
        ]
        pygame.draw.polygon(target, bone_color, bone_patch_1)
        pygame.draw.polygon(target, bone_shadow, bone_patch_1, max(1, int(size * 0.01)))
        bone_patch_2 = [
            (cx - head_w * 0.4, cy - head_h * 0.32),
            (cx - head_w * 0.12, cy - head_h * 0.36),
            (cx - head_w * 0.15, cy - head_h * 0.18),
            (cx - head_w * 0.38, cy - head_h * 0.15),
        ]
        pygame.draw.polygon(target, bone_color, bone_patch_2)
        pygame.draw.polygon(target, bone_shadow, bone_patch_2, max(1, int(size * 0.01)))
        skull_hole = tuple(int(c * lf) for c in (25, 5, 5))
        pygame.draw.circle(target, bone_color,
                            (int(cx - head_w * 0.05), int(cy + head_h * 0.4)), max(2, int(head_w * 0.06)))
        pygame.draw.circle(target, skull_hole,
                            (int(cx - head_w * 0.05), int(cy + head_h * 0.4)), max(1, int(head_w * 0.03)))

        # עיניים - חורים שחורים ריקים לגמרי, בלי אישונים ובלי זוהר - "חלל" מפחיד
        wild_jitter_x = math.sin(pygame.time.get_ticks() * 0.09) * head_w * 0.025
        wild_jitter_y = math.cos(pygame.time.get_ticks() * 0.065) * head_h * 0.02
        eye_y = cy - head_h * 0.08
        for side in (-1, 1):
            eye_scale = 1.15 if side == 1 else 0.95
            eye_w = head_w * 0.20 * eye_scale
            eye_h = head_h * 0.16 * eye_scale
            eye_x = cx + side * head_w * 0.24 + wild_jitter_x
            ey = eye_y + wild_jitter_y

            wild_points = [
                (eye_x - side * eye_w * 1.0, ey - eye_h * 0.3),
                (eye_x - side * eye_w * 0.3, ey - eye_h * 1.0),
                (eye_x + side * eye_w * 0.9, ey - eye_h * 0.5),
                (eye_x + side * eye_w * 0.7, ey + eye_h * 0.6),
                (eye_x - side * eye_w * 0.2, ey + eye_h * 0.9),
            ]
            pygame.draw.polygon(target, (0, 0, 0), wild_points)
            outline_color = tuple(int(c * lf) for c in (25, 5, 5))
            pygame.draw.polygon(target, outline_color, wild_points, max(1, int(size * 0.008)))

        # פה - פעור, משונן, עם שיניים חדות למעלה ולמטה (mouth_scale>1 = פעור רחב לרגע הטריפה)
        mouth_w = head_w * 0.55 * min(1.25, math.sqrt(mouth_scale))
        mouth_h = head_h * 0.28 * mouth_scale
        mouth_y = cy + head_h * 0.22
        mouth_rect = pygame.Rect(0, 0, mouth_w, mouth_h)
        mouth_rect.center = (cx, mouth_y)
        pygame.draw.ellipse(target, (5, 0, 0), mouth_rect)

        num_teeth = 6
        tooth_w = mouth_w / num_teeth
        tooth_h = mouth_h * 0.45
        teeth_color = (235, 230, 220) if light_factor > 0.05 else (120, 118, 115)
        for i in range(num_teeth):
            tx = mouth_rect.left + i * tooth_w
            pygame.draw.polygon(target, teeth_color, [
                (tx, mouth_rect.top),
                (tx + tooth_w, mouth_rect.top),
                (tx + tooth_w / 2, mouth_rect.top + tooth_h)
            ])
            pygame.draw.polygon(target, teeth_color, [
                (tx, mouth_rect.bottom),
                (tx + tooth_w, mouth_rect.bottom),
                (tx + tooth_w / 2, mouth_rect.bottom - tooth_h)
            ])

        # -------- דם זולג מהפה - כמה פסי דם יורדים באורכים משתנים, עם נענוע קל --------
        blood_dark = tuple(int(c * lf) for c in (120, 8, 8))
        blood_bright = tuple(int(c * lf) for c in (170, 15, 15))
        time_wave = pygame.time.get_ticks() * 0.003
        num_drips = 4
        for i in range(num_drips):
            t = i / (num_drips - 1)
            drip_x = mouth_rect.left + t * mouth_w + math.sin(time_wave + i) * size * 0.01
            drip_start_y = mouth_rect.bottom - mouth_h * 0.1
            drip_len = (head_h * (0.25 + 0.18 * ((i * 37) % 5) / 5) * mouth_scale) * \
                       (0.85 + 0.15 * math.sin(time_wave * 2 + i))
            drip_end_y = drip_start_y + drip_len
            width = max(1, int(size * (0.012 if i % 2 == 0 else 0.008)))
            pygame.draw.line(target, blood_dark, (drip_x, drip_start_y), (drip_x, drip_end_y), width)
            pygame.draw.line(target, blood_bright,
                              (drip_x, drip_start_y), (drip_x, drip_start_y + drip_len * 0.5), max(1, width - 1))
            pygame.draw.circle(target, blood_dark, (int(drip_x), int(drip_end_y)), max(1, width))

        chin_blood_rect = pygame.Rect(0, 0, mouth_w * 0.7, mouth_h * 0.35)
        chin_blood_rect.center = (cx, mouth_rect.bottom + mouth_h * 0.05)
        pygame.draw.ellipse(target, blood_dark, chin_blood_rect)

        # קווי סדק/צלקת על הפנים לתחושת אימה נוספת
        crack_color = tuple(int(c * lf) for c in (15, 3, 5))
        pygame.draw.line(target, crack_color,
                          (cx - head_w * 0.3, cy - head_h * 0.25),
                          (cx - head_w * 0.1, cy + head_h * 0.05), max(1, int(size * 0.015)))

    def draw_jumpscare(self):
        """רגע הטריפה - השומר מתקרב, פוער את הפה וממלא את המסך, ואז 'נתפסת!' על המסך"""
        progress = min(1.0, self.jumpscare_timer / JUMPSCARE_DURATION)
        ease = progress ** 0.6

        self.screen.fill(BLACK)

        size = 230 + ease * 300  # הראש הולך ומתקרב/מתמלא על המסך
        mouth_scale = 1.0 + ease * 2.4  # הפה נפער בהדרגה
        cx, cy = WIDTH / 2, HEIGHT / 2

        self.draw_monster_head(cx, cy, size, 1.0, 1.0, mouth_scale=mouth_scale)

        # הבזק אדום פועם לאורך האנימציה
        flash_alpha = int(70 * math.sin(progress * math.pi))
        if flash_alpha > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((160, 0, 0, flash_alpha))
            self.screen.blit(overlay, (0, 0))

        # טקסט "נתפסת!" מופיע לקראת סוף האנימציה
        if progress > 0.55:
            text_alpha = int(255 * min(1.0, (progress - 0.55) / 0.35))
            caught_text = self.font_big.render(rtl("נתפסת!"), True, RED)
            caught_text.set_alpha(text_alpha)
            self.screen.blit(caught_text, caught_text.get_rect(center=(WIDTH / 2, HEIGHT - 90)))

        # רעד חזק בזמן הטריפה עצמה
        self.present_frame(extra_shake=progress * 6)

    def wrap_text(self, text, font, max_width):
        """שובר טקסט ארוך למספר שורות כך שכל שורה נכנסת לרוחב הנתון (לפני היפוך ה-RTL)"""
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def render_world(self):
        """מצייר את המבוך (קירות, ארונות, פתקים, יומן, שומר) מנקודת המבט של self.player"""
        self.draw_background()
        depth_buffer = self.cast_rays()
        self.depth_buffer = depth_buffer
        if self.view_room:
            self.draw_room_props()
            return

        # ציור ספרייטים ממויין לפי מרחק (רחוק לקרוב) - הדלת תמיד פתוחה, בלי מפתחות
        monster_dist = math.hypot(self.monster.x - self.player.x, self.monster.y - self.player.y)

        # מיון משולב: דלת היציאה + היומן + פתקי הדם + השומר (מצויר בנפרד עם פרצוף מפחיד)
        all_items = []
        all_items += [("note", n) for n in self.notes]
        if not self.journal_collected:
            all_items.append(("journal", self.journal_pos))
        if self.monster.awake:
            all_items.append(("monster", monster_dist))

        def item_dist(item):
            kind, data = item
            if kind == "monster":
                return data
            return math.hypot(data[0] - self.player.x, data[1] - self.player.y)

        all_items.sort(key=lambda item: -item_dist(item))

        for kind, data in all_items:
            if kind == "journal":
                self.draw_journal(data[0], data[1], depth_buffer)
            elif kind == "note":
                nx, ny, tilt, note_text = data
                self.draw_note(nx, ny, tilt, depth_buffer, text=note_text)
            else:
                self.draw_monster(self.monster.x, self.monster.y, depth_buffer)


    def draw(self):
        if self.on_menu:
            self.draw_menu()
            self.present_frame()
            return

        if self.jumpscare_active:
            self.draw_jumpscare()
            return

        if self.ending_active:
            self.draw_ending()
            self.present_frame()
            return

        if self.in_camera_room:
            self.draw_camera_room()
            self.present_frame()
            return

        self.render_world()
        depth_buffer = self.depth_buffer
        if self.photo_pending:
            self.capture_photo()
        self.draw_flashlight_glow()
        self.draw_glimpse()
        self.draw_blood_effects()
        self.draw_grain()
        self.draw_vignette()
        self.draw_closet_view()
        self.draw_heartbeat_pulse()
        self.draw_alarm()
        self.draw_static_glitch()
        self.draw_whisper()
        self.draw_minimap()
        self.draw_hud()
        if self.has_camera and not (self.game_over or self.win):
            self.draw_pill("משימה: " + self.mission_text, (255, 215, 120), 10, 40)
            self.draw_pill("Shift - צילום", (200, 220, 255), WIDTH - 10, 186, anchor="right")
        self.draw_overlays()

        if self.entering > 0:
            fade = pygame.Surface((WIDTH, HEIGHT))
            fade.set_alpha(int(255 * min(1.0, self.entering / ENTER_FADE)))
            self.screen.blit(fade, (0, 0))

        if self.game_over:
            if self.left_without_journal:
                self.screen.fill((0, 0, 0))
                self.draw_end_screen("לא הצלחת במשימה", RED,
                                     "Press R to Restart | ESC to Quit")
                sub = self.font_story.render(rtl("נכנסת לחדר בלי היומן..."), True, (230, 170, 170))
                self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 26)))
            else:
                self.draw_end_screen("נתפסת...", RED, "Press R to Restart | ESC to Quit")
        elif self.win:
            self.draw_end_screen("יצאת בשלום!", GREEN, "Press R to Play Again | ESC to Quit")

        self.present_frame()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_input()
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    game = FPSGame()
    game.run()