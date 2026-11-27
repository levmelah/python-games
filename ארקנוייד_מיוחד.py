"""
Arkanoid ב-PyQt6
=================
התקנה:  pip install PyQt6
הרצה:   python arkanoid.py

שליטה:
  עכבר / חיצים (או A/D)  - הזזת המחבט
  רווח / לחיצת עכבר      - שחרור הכדור
  P / Esc                - השהייה
  Enter                  - התחלה / משחק חדש
"""

import os
import sys
import math
import random

# עוקף קריסה ידועה של Qt ב-GNOME/Ubuntu:
# "Settings schema 'org.gnome.settings-daemon.plugins.xsettings' does not contain a key named 'antialiasing'"
# הקריסה נגרמת מערכת הנושא של GTK ש-Qt טוען, ולכן מבקשים מ-Qt לא לטעון אותה.
os.environ["QT_QPA_PLATFORMTHEME"] = "xdgdesktopportal"

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, QElapsedTimer
from PyQt6.QtGui import (QPainter, QColor, QPen, QFont, QLinearGradient,
                         QRadialGradient)
from PyQt6.QtWidgets import QApplication, QWidget

# ---------- קבועים ----------
W, H = 800, 600            # גודל העולם הלוגי (מוגדל/מוקטן לפי החלון)
HUD = 40                   # גובה פס המידע העליון
PADDLE_Y = H - 50
PADDLE_H = 14
PADDLE_W = 100
PADDLE_W_BIG = 160
PADDLE_SPEED = 650
BALL_R = 8
BALL_SPEED = 380
BALL_SPEED_MAX = 640
COLS = 12
BRICK_W, BRICK_H, GAP = 60, 22, 4
BRICKS_LEFT = (W - (COLS * (BRICK_W + GAP) - GAP)) / 2
BRICKS_TOP = HUD + 40
POWERUP_CHANCE = 0.16
START_LIVES = 3

ROW_COLORS = ["#ff4d6d", "#ff9f1c", "#ffd60a", "#06d6a0", "#118ab2",
              "#7b2cbf", "#ef476f", "#4cc9f0"]

# '.' ריק, 1-3 = מספר פגיעות, '#' = בלתי שביר
LEVELS = [
    [
        "............",
        "111111111111",
        "111111111111",
        "111111111111",
        "111111111111",
        "111111111111",
    ],
    [
        "2..........2",
        "22........22",
        "1221....1221",
        "111122221111",
        ".1111111111.",
        "..11####11..",
    ],
    [
        "3.3.3.3.3.3.",
        ".2.2.2.2.2.2",
        "111111111111",
        "#..#....#..#",
        "222222222222",
        "111111111111",
        "..##....##..",
    ],
    [
        "....3333....",
        "...322223...",
        "..32111123..",
        ".3211..1123.",
        "..32111123..",
        "...322223...",
        "#...3333...#",
    ],
    [
        "333333333333",
        "3##########3",
        "3.2222222.#3",
        "3#.111111.#3",
        "3#2222222.#3",
        "3..........3",
        "111111111111",
    ],
]

POWERUPS = {
    "E": ("#4cc9f0", "הרחבה"),
    "M": ("#ff9f1c", "מולטי"),
    "S": ("#06d6a0", "האטה"),
    "L": ("#ff4d6d", "חיים"),
    "C": ("#c77dff", "תפיסה"),
}


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ---------- ישויות ----------
class Ball:
    def __init__(self, x, y, vx=0.0, vy=0.0, stuck=True):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.stuck = stuck
        self.offset = 0.0          # מיקום יחסי למחבט כשהכדור תקוע
        self.trail = []

    @property
    def speed(self):
        return math.hypot(self.vx, self.vy)

    def set_speed(self, s):
        cur = self.speed
        if cur > 0:
            self.vx *= s / cur
            self.vy *= s / cur


class Brick:
    def __init__(self, rect, hp, color):
        self.rect = rect
        self.hp = hp
        self.max_hp = hp
        self.solid = hp < 0        # בלתי שביר
        self.color = QColor(color)
        self.flash = 0.0


class PowerUp:
    def __init__(self, x, y, kind):
        self.x, self.y, self.kind = x, y, kind

    @property
    def rect(self):
        return QRectF(self.x - 20, self.y - 9, 40, 18)


class Particle:
    def __init__(self, x, y, color):
        a = random.uniform(0, 2 * math.pi)
        s = random.uniform(60, 260)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * s, math.sin(a) * s - 80
        self.life = self.max_life = random.uniform(0.4, 0.9)
        self.color = QColor(color)
        self.size = random.uniform(2, 5)


# ---------- המשחק ----------
class Arkanoid(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arkanoid – PyQt6")
        self.resize(W, H)
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.BlankCursor)

        self.keys = set()
        self.high_score = 0
        self.stars = [(random.uniform(0, W), random.uniform(0, H),
                       random.uniform(0.5, 1.8)) for _ in range(90)]
        self.new_game()
        self.state = "menu"

        self.clock = QElapsedTimer()
        self.clock.start()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    # ----- אתחול -----
    def new_game(self):
        self.score = 0
        self.lives = START_LIVES
        self.level = 0
        self.load_level()

    def load_level(self):
        self.bricks = []
        for r, row in enumerate(LEVELS[self.level % len(LEVELS)]):
            for c, ch in enumerate(row):
                if ch == ".":
                    continue
                rect = QRectF(BRICKS_LEFT + c * (BRICK_W + GAP),
                              BRICKS_TOP + r * (BRICK_H + GAP),
                              BRICK_W, BRICK_H)
                if ch == "#":
                    self.bricks.append(Brick(rect, -1, "#9aa5b1"))
                else:
                    self.bricks.append(Brick(rect, int(ch),
                                             ROW_COLORS[r % len(ROW_COLORS)]))
        self.powerups = []
        self.particles = []
        self.reset_paddle_and_ball()
        # כל שלב קצת יותר מהיר
        self.base_speed = min(BALL_SPEED + self.level * 30, BALL_SPEED_MAX - 100)

    def reset_paddle_and_ball(self):
        self.paddle_x = W / 2
        self.paddle_w = PADDLE_W
        self.paddle_target_w = PADDLE_W
        self.expand_t = 0.0
        self.slow_t = 0.0
        self.catch_t = 0.0
        self.balls = [Ball(self.paddle_x, PADDLE_Y - BALL_R)]
        self.message_t = 0.0
        self.message = ""

    def show_msg(self, text):
        self.message = text
        self.message_t = 1.6

    # ----- לולאה -----
    def tick(self):
        dt = self.clock.restart() / 1000.0
        dt = min(dt, 0.033)
        if self.state == "play":
            self.update_game(dt)
        self.update_particles(dt)
        self.update()

    def update_game(self, dt):
        # מחבט
        move = 0
        if Qt.Key.Key_Left in self.keys or Qt.Key.Key_A in self.keys:
            move -= 1
        if Qt.Key.Key_Right in self.keys or Qt.Key.Key_D in self.keys:
            move += 1
        self.paddle_x += move * PADDLE_SPEED * dt
        self.paddle_w += (self.paddle_target_w - self.paddle_w) * min(1, dt * 10)
        self.paddle_x = clamp(self.paddle_x, self.paddle_w / 2, W - self.paddle_w / 2)

        # טיימרים של פאוור-אפים
        if self.expand_t > 0:
            self.expand_t -= dt
            if self.expand_t <= 0:
                self.paddle_target_w = PADDLE_W
        if self.slow_t > 0:
            self.slow_t -= dt
        if self.catch_t > 0:
            self.catch_t -= dt
        if self.message_t > 0:
            self.message_t -= dt

        # כדורים
        for b in self.balls[:]:
            if b.stuck:
                b.x = self.paddle_x + b.offset
                b.y = PADDLE_Y - BALL_R
                b.trail.clear()
                continue
            target = self.base_speed * (0.65 if self.slow_t > 0 else 1.0)
            # האצה/האטה הדרגתית לעבר מהירות היעד
            if abs(b.speed - target) > 1 and b.speed < BALL_SPEED_MAX:
                b.set_speed(b.speed + (target - b.speed) * min(1, dt * 2))
            dist = b.speed * dt
            steps = max(1, int(math.ceil(dist / (BALL_R * 0.5))))
            h = dt / steps
            for _ in range(steps):
                if not self.step_ball(b, h):
                    break
            b.trail.append((b.x, b.y))
            if len(b.trail) > 10:
                b.trail.pop(0)
            if b.y - BALL_R > H:
                self.balls.remove(b)

        if not self.balls:
            self.lives -= 1
            if self.lives <= 0:
                self.high_score = max(self.high_score, self.score)
                self.state = "over"
            else:
                self.reset_paddle_and_ball()
                self.show_msg("נפסלת! נשארו %d" % self.lives)

        # פאוור-אפים
        prect = self.paddle_rect()
        for p in self.powerups[:]:
            p.y += 140 * dt
            if p.rect.intersects(prect):
                self.apply_powerup(p.kind)
                self.powerups.remove(p)
            elif p.y > H + 20:
                self.powerups.remove(p)

        # סיום שלב
        if not any(not br.solid for br in self.bricks):
            self.level += 1
            self.score += 500
            if self.level >= len(LEVELS):
                self.high_score = max(self.high_score, self.score)
                self.state = "win"
            else:
                self.load_level()
                self.show_msg("שלב %d" % (self.level + 1))

        for br in self.bricks:
            if br.flash > 0:
                br.flash -= dt * 4

    def step_ball(self, b, h):
        b.x += b.vx * h
        b.y += b.vy * h

        # קירות
        if b.x - BALL_R < 0:
            b.x = BALL_R
            b.vx = abs(b.vx)
        elif b.x + BALL_R > W:
            b.x = W - BALL_R
            b.vx = -abs(b.vx)
        if b.y - BALL_R < HUD:
            b.y = HUD + BALL_R
            b.vy = abs(b.vy)

        # מחבט
        pr = self.paddle_rect()
        if b.vy > 0 and self.circle_hits(b, pr):
            rel = clamp((b.x - self.paddle_x) / (self.paddle_w / 2), -1, 1)
            ang = rel * math.radians(62)
            s = b.speed
            b.vx = s * math.sin(ang)
            b.vy = -s * math.cos(ang)
            b.y = pr.top() - BALL_R
            if self.catch_t > 0:
                b.stuck = True
                b.offset = b.x - self.paddle_x
                return False
            return True

        # לבנים
        for br in self.bricks:
            r = br.rect
            cx = clamp(b.x, r.left(), r.right())
            cy = clamp(b.y, r.top(), r.bottom())
            dx, dy = b.x - cx, b.y - cy
            if dx * dx + dy * dy <= BALL_R * BALL_R:
                if dx == 0 and dy == 0:
                    b.vy = -b.vy
                elif abs(dx) > abs(dy):
                    b.vx = abs(b.vx) if dx > 0 else -abs(b.vx)
                    b.x = (r.right() + BALL_R) if dx > 0 else (r.left() - BALL_R)
                else:
                    b.vy = abs(b.vy) if dy > 0 else -abs(b.vy)
                    b.y = (r.bottom() + BALL_R) if dy > 0 else (r.top() - BALL_R)
                self.hit_brick(br)
                # מניעת מסלול אופקי לגמרי
                if abs(b.vy) < b.speed * 0.2:
                    b.vy = math.copysign(b.speed * 0.2, b.vy or -1)
                b.set_speed(min(b.speed + 4, BALL_SPEED_MAX))
                break
        return True

    def hit_brick(self, br):
        br.flash = 1.0
        if br.solid:
            return
        br.hp -= 1
        if br.hp <= 0:
            self.bricks.remove(br)
            self.score += 10 * br.max_hp
            c = br.rect.center()
            for _ in range(14):
                self.particles.append(Particle(c.x(), c.y(), br.color))
            if random.random() < POWERUP_CHANCE:
                kind = random.choices("EMSLC", weights=[3, 3, 3, 1, 2])[0]
                self.powerups.append(PowerUp(c.x(), c.y(), kind))
        else:
            self.score += 5

    def apply_powerup(self, kind):
        self.score += 50
        self.show_msg(POWERUPS[kind][1] + "!")
        if kind == "E":
            self.paddle_target_w = PADDLE_W_BIG
            self.expand_t = 12
        elif kind == "S":
            self.slow_t = 10
        elif kind == "L":
            self.lives += 1
        elif kind == "C":
            self.catch_t = 12
        elif kind == "M":
            new = []
            for b in self.balls:
                if b.stuck:
                    self.launch(b)
                for a in (-0.45, 0.45):
                    ca, sa = math.cos(a), math.sin(a)
                    nb = Ball(b.x, b.y, b.vx * ca - b.vy * sa,
                              b.vx * sa + b.vy * ca, stuck=False)
                    new.append(nb)
            self.balls.extend(new[:12])

    def launch(self, b):
        b.stuck = False
        ang = math.radians(random.uniform(-25, 25))
        b.vx = self.base_speed * math.sin(ang)
        b.vy = -self.base_speed * math.cos(ang)

    def launch_all(self):
        for b in self.balls:
            if b.stuck:
                self.launch(b)

    def update_particles(self, dt):
        for p in self.particles[:]:
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)
                continue
            p.vy += 500 * dt
            p.x += p.vx * dt
            p.y += p.vy * dt

    # ----- עזרים -----
    def paddle_rect(self):
        return QRectF(self.paddle_x - self.paddle_w / 2, PADDLE_Y,
                      self.paddle_w, PADDLE_H)

    @staticmethod
    def circle_hits(b, r):
        cx = clamp(b.x, r.left(), r.right())
        cy = clamp(b.y, r.top(), r.bottom())
        return (b.x - cx) ** 2 + (b.y - cy) ** 2 <= BALL_R * BALL_R

    def view_transform(self):
        s = min(self.width() / W, self.height() / H)
        ox = (self.width() - W * s) / 2
        oy = (self.height() - H * s) / 2
        return s, ox, oy

    # ----- קלט -----
    def keyPressEvent(self, e):
        k = e.key()
        self.keys.add(k)
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.state in ("menu", "over", "win"):
                self.new_game()
                self.state = "play"
                self.show_msg("שלב 1")
        elif k == Qt.Key.Key_Space:
            if self.state == "play":
                self.launch_all()
            elif self.state == "menu":
                self.state = "play"
        elif k in (Qt.Key.Key_P, Qt.Key.Key_Escape):
            if self.state == "play":
                self.state = "paused"
            elif self.state == "paused":
                self.state = "play"

    def keyReleaseEvent(self, e):
        self.keys.discard(e.key())

    def mouseMoveEvent(self, e):
        if self.state != "play":
            return
        s, ox, _ = self.view_transform()
        x = (e.position().x() - ox) / s
        self.paddle_x = clamp(x, self.paddle_w / 2, W - self.paddle_w / 2)

    def mousePressEvent(self, e):
        if self.state == "play":
            self.launch_all()
        elif self.state == "paused":
            self.state = "play"
        else:
            self.new_game()
            self.state = "play"
            self.show_msg("שלב 1")

    def focusOutEvent(self, e):
        self.keys.clear()
        if self.state == "play":
            self.state = "paused"

    # ----- ציור -----
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#05050c"))
        s, ox, oy = self.view_transform()
        p.translate(ox, oy)
        p.scale(s, s)
        p.setClipRect(QRectF(0, 0, W, H))

        self.draw_background(p)
        self.draw_bricks(p)
        self.draw_powerups(p)
        self.draw_particles(p)
        self.draw_paddle(p)
        self.draw_balls(p)
        self.draw_hud(p)
        self.draw_overlay(p)
        p.end()

    def draw_background(self, p):
        g = QLinearGradient(0, 0, 0, H)
        g.setColorAt(0, QColor("#10102a"))
        g.setColorAt(1, QColor("#1b0b2e"))
        p.fillRect(QRectF(0, 0, W, H), g)
        p.setPen(Qt.PenStyle.NoPen)
        for x, y, r in self.stars:
            p.setBrush(QColor(255, 255, 255, int(60 + r * 60)))
            p.drawEllipse(QPointF(x, y), r, r)

    def draw_bricks(self, p):
        for br in self.bricks:
            r = br.rect
            base = QColor(br.color)
            if not br.solid and br.max_hp > 1:
                # לבנה פגועה – כהה יותר
                base = base.darker(100 + (br.max_hp - br.hp) * 35)
            if br.flash > 0:
                base = base.lighter(100 + int(br.flash * 80))
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, base.lighter(140))
            g.setColorAt(0.5, base)
            g.setColorAt(1, base.darker(150))
            p.setBrush(g)
            p.setPen(QPen(base.darker(200), 1))
            p.drawRoundedRect(r, 4, 4)
            p.setPen(QPen(QColor(255, 255, 255, 90), 1))
            p.drawLine(QPointF(r.left() + 4, r.top() + 3),
                       QPointF(r.right() - 4, r.top() + 3))
            if br.solid:
                p.setPen(QPen(QColor(60, 60, 70, 160), 2))
                p.drawLine(r.topLeft() + QPointF(6, 5), r.bottomRight() - QPointF(6, 5))
            elif br.hp > 1:
                p.setPen(QColor(255, 255, 255, 200))
                p.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                p.drawText(r, Qt.AlignmentFlag.AlignCenter, str(br.hp))

    def draw_paddle(self, p):
        r = self.paddle_rect()
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        main = QColor("#c77dff") if self.catch_t > 0 else QColor("#4cc9f0")
        g.setColorAt(0, main.lighter(150))
        g.setColorAt(1, main.darker(160))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(main.red(), main.green(), main.blue(), 50))
        p.drawRoundedRect(r.adjusted(-6, -6, 6, 6), 12, 12)
        p.setBrush(g)
        p.drawRoundedRect(r, 7, 7)
        p.setBrush(QColor("#ff4d6d"))
        p.drawRoundedRect(QRectF(r.left(), r.top(), 12, r.height()), 6, 6)
        p.drawRoundedRect(QRectF(r.right() - 12, r.top(), 12, r.height()), 6, 6)

    def draw_balls(self, p):
        p.setPen(Qt.PenStyle.NoPen)
        for b in self.balls:
            for i, (tx, ty) in enumerate(b.trail):
                a = int(80 * (i + 1) / len(b.trail))
                p.setBrush(QColor(255, 220, 120, a))
                rr = BALL_R * (0.4 + 0.6 * (i + 1) / len(b.trail))
                p.drawEllipse(QPointF(tx, ty), rr, rr)
            g = QRadialGradient(QPointF(b.x - 3, b.y - 3), BALL_R * 1.6)
            g.setColorAt(0, QColor("#ffffff"))
            g.setColorAt(0.5, QColor("#ffe066"))
            g.setColorAt(1, QColor("#ff9f1c"))
            p.setBrush(g)
            p.drawEllipse(QPointF(b.x, b.y), BALL_R, BALL_R)

    def draw_powerups(self, p):
        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        for pu in self.powerups:
            col = QColor(POWERUPS[pu.kind][0])
            r = pu.rect
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, col.lighter(150))
            g.setColorAt(1, col.darker(150))
            p.setBrush(g)
            p.setPen(QPen(QColor(255, 255, 255, 160), 1))
            p.drawRoundedRect(r, 9, 9)
            p.setPen(QColor("white"))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, pu.kind)

    def draw_particles(self, p):
        p.setPen(Qt.PenStyle.NoPen)
        for pt in self.particles:
            c = QColor(pt.color)
            c.setAlpha(int(255 * pt.life / pt.max_life))
            p.setBrush(c)
            p.drawRect(QRectF(pt.x, pt.y, pt.size, pt.size))

    def draw_hud(self, p):
        p.fillRect(QRectF(0, 0, W, HUD), QColor(0, 0, 0, 120))
        p.setPen(QPen(QColor("#4cc9f0"), 1))
        p.drawLine(QPointF(0, HUD), QPointF(W, HUD))
        p.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        p.setPen(QColor("white"))
        p.drawText(QRectF(15, 0, 250, HUD), Qt.AlignmentFlag.AlignVCenter,
                   "SCORE  %d" % self.score)
        p.drawText(QRectF(0, 0, W, HUD), Qt.AlignmentFlag.AlignCenter,
                   "LEVEL  %d" % (self.level + 1))
        # חיים
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#ff4d6d"))
        for i in range(min(self.lives, 8)):
            p.drawRoundedRect(QRectF(W - 30 - i * 30, 15, 24, 9), 4, 4)
        # טיימרים פעילים
        x = 220
        p.setFont(QFont("Arial", 9))
        for t, kind in ((self.expand_t, "E"), (self.slow_t, "S"), (self.catch_t, "C")):
            if t > 0:
                p.setPen(QColor(POWERUPS[kind][0]))
                p.drawText(QRectF(x, 0, 60, HUD), Qt.AlignmentFlag.AlignVCenter,
                           "%s %.0f" % (kind, t))
                x += 50

    def draw_overlay(self, p):
        def center_text(text, y, size, color="white", bold=True):
            p.setFont(QFont("Arial", size,
                            QFont.Weight.Bold if bold else QFont.Weight.Normal))
            p.setPen(QColor(color))
            p.drawText(QRectF(0, y, W, size * 2.2), Qt.AlignmentFlag.AlignCenter, text)

        if self.state == "play":
            if self.message_t > 0:
                center_text(self.message, H / 2 - 20, 26, "#ffd60a")
            if any(b.stuck for b in self.balls) and self.message_t <= 0:
                center_text("רווח / לחיצה לשחרור הכדור", H / 2 + 40, 13,
                            "#cccccc", False)
            return

        p.fillRect(QRectF(0, 0, W, H), QColor(0, 0, 0, 160))
        if self.state == "menu":
            center_text("ARKANOID", 150, 56, "#4cc9f0")
            center_text("Enter או לחיצה כדי להתחיל", 290, 18)
            center_text("עכבר / חיצים – הזזה    רווח – שחרור    P – השהייה",
                        340, 12, "#bbbbbb", False)
            y = 400
            legend = "   ".join("%s = %s" % (k, v[1]) for k, v in POWERUPS.items())
            center_text(legend, y, 11, "#ffd60a", False)
        elif self.state == "paused":
            center_text("הפסקה", 230, 40, "#ffd60a")
            center_text("P או לחיצה להמשך", 310, 14)
        elif self.state == "over":
            center_text("GAME OVER", 190, 48, "#ff4d6d")
            center_text("ניקוד: %d" % self.score, 290, 20)
            center_text("שיא: %d" % self.high_score, 330, 14, "#bbbbbb")
            center_text("Enter למשחק חדש", 390, 14)
        elif self.state == "win":
            center_text("ניצחת!", 190, 48, "#06d6a0")
            center_text("ניקוד: %d" % self.score, 290, 20)
            center_text("Enter למשחק חדש", 360, 14)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = Arkanoid()
    game.show()
    sys.exit(app.exec())