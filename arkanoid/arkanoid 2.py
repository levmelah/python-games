import tkinter as tk
import random
import math
import sys
from pathlib import Path

# ─── Constants ───
WIDTH = 800
HEIGHT = 600
PADDLE_W = 80
PADDLE_H = 15
BALL_R = 10
BRICK_ROWS = 6
BRICK_COLS = 10
BRICK_W = 70
BRICK_H = 25
BRICK_PAD = 4
TOP_OFFSET = 60
FPS = 60
INITIAL_BALL_SPEED = 4.0
MAX_BALL_SPEED = 8
BALL_SPEEDUP = 0.24
ZOMBIE_COUNT = 7
GHOST_COUNT = 9
FOG_COUNT = 6
LIGHTNING_CHANCE = 0.004

BRICK_COLORS = ["#8b0000", "#7b0070", "#1a006e", "#005050", "#1a3300"]
BRICK_HIGHLIGHT = ["#c43030", "#b03090", "#3030b0", "#208080", "#406010"]
BRICK_SHADOW = ["#3a0000", "#2a0030", "#04001a", "#001818", "#040d00"]
BRICK_POINTS = [60, 50, 40, 30, 20, 10]
SKULL_CHAR = "☠"
TRAIL_LENGTH = 7
SPEED_BLOCK_W = 90
SPEED_BLOCK_H = 18
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
HIGH_SCORE_FILE = APP_DIR / "arkanoid2_high_score.txt"

DIFFICULTY_PRESETS = {
    "easy": {"initial": 3.2, "max": 6.5, "speedup": 0.16, "label": "EASY"},
    "normal": {"initial": 4.0, "max": 8.0, "speedup": 0.24, "label": "NORMAL"},
    "hard": {"initial": 4.8, "max": 10.0, "speedup": 0.32, "label": "HARD"},
}


class Arkanoid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("☠ Skeleton Arkanoid ☠")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#08001a")
        self.canvas.pack()

        self.score = 0
        self.lives = 5
        self.best_score = self._load_best_score()
        self.game_started = False
        self.game_over = False
        self.paused = False
        self.difficulty = "normal"

        self.ball_dx = INITIAL_BALL_SPEED
        self.ball_dy = -INITIAL_BALL_SPEED
        self.paddle_speed = 0

        # Effects
        self.particles = []   # [{id, dx, dy, life, max_life}]
        self.trail = []       # [canvas oval id, ...]
        self.popups = []      # [{id, life}]
        self.paddle_flash = 0  # ticks remaining
        self.zombies = []     # [{parts, x, y, dx, bob, phase}]
        self.ghosts = []      # [{parts, x, y, dx, bob, phase}]
        self.fog_bands = []   # [{id, x, y, dx, bob, phase}]
        self.lightning_ticks = 0
        self.lightning_bolts = []  # canvas ids of current bolt lines

        self._create_haunted_sky()
        self._draw_bone_borders()
        self._create_ghosts()
        self._create_zombies()
        self._create_paddle()
        self._create_ball()
        self._create_bricks()
        self._create_speed_block()
        self._create_ui()
        self._redraw_skulls()
        self.overlay_items = []
        self._show_start_screen()

        self.root.bind("<KeyPress-Left>", lambda e: self._set_paddle_speed(-8))
        self.root.bind("<KeyRelease-Left>", lambda e: self._stop_paddle("left"))
        self.root.bind("<KeyPress-Right>", lambda e: self._set_paddle_speed(8))
        self.root.bind("<KeyRelease-Right>", lambda e: self._stop_paddle("right"))
        self.root.bind("<space>", self._start_game)
        self.root.bind("<p>", self._toggle_pause)
        self.root.bind("<P>", self._toggle_pause)
        self.root.bind("<r>", self._restart_game)
        self.root.bind("<R>", self._restart_game)
        self.root.bind("1", lambda e: self._set_difficulty("easy"))
        self.root.bind("2", lambda e: self._set_difficulty("normal"))
        self.root.bind("3", lambda e: self._set_difficulty("hard"))

        self._game_loop()
        self.root.mainloop()

    # ─── Visual helpers ───

    def _load_best_score(self):
        try:
            return int(HIGH_SCORE_FILE.read_text(encoding="utf-8").strip() or "0")
        except (FileNotFoundError, ValueError):
            return 0

    def _save_best_score(self):
        HIGH_SCORE_FILE.write_text(str(self.best_score), encoding="utf-8")

    def _set_difficulty(self, mode):
        if mode not in DIFFICULTY_PRESETS:
            return
        self.difficulty = mode
        if not self.game_started and not self.game_over:
            self._apply_difficulty()
            self._update_score()
            self._refresh_start_screen()

    def _apply_difficulty(self):
        preset = DIFFICULTY_PRESETS[self.difficulty]
        self.ball_dx = preset["initial"] * random.choice([-1, 1])
        self.ball_dy = -preset["initial"]

    def _refresh_start_screen(self):
        if hasattr(self, "start_items") and self.start_items:
            for item in self.start_items:
                self.canvas.delete(item)
        self._show_start_screen()

    def _clear_overlay_items(self):
        for item in self.overlay_items:
            self.canvas.delete(item)
        self.overlay_items = []

    def _clear_bricks(self):
        for brick in self.bricks:
            self.canvas.delete(brick["id"])
            self.canvas.delete(brick["label"])
            self.canvas.delete(brick.get("hl", ""))
            self.canvas.delete(brick.get("sl", ""))
            self.canvas.delete(brick.get("ll", ""))
        self.bricks = []

    def _draw_skull_shape(self, cx, cy, r, tag=None):
        """Draw a skull centered at (cx,cy) with radius r. Returns list of canvas item ids."""
        kw = {"tags": tag} if tag else {}
        items = []
        skull_fill = "#e6e1d6"
        skull_shadow = "#b7afa1"
        skull_outline = "#8e877b"
        socket_fill = "#191919"
        tooth_fill = "#f4f0e8"
        items.append(self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=skull_fill, outline=skull_outline, width=1, **kw))
        items.append(self.canvas.create_oval(
            cx - r + 3, cy - r + 3, cx + r - 5, cy,
            fill="#f3eee4", outline="", **kw))
        jaw_w = max(6, int(r * 1.15))
        jaw_h = max(4, int(r * 0.7))
        items.append(self.canvas.create_rectangle(
            cx - jaw_w // 2, cy + r // 3,
            cx + jaw_w // 2, cy + r // 3 + jaw_h,
            fill=skull_fill, outline=skull_outline, width=1, **kw))
        items.append(self.canvas.create_polygon(
            cx - r + 2, cy + 1,
            cx - r // 2, cy + r // 4,
            cx - r // 3, cy + r // 2,
            cx - r + 4, cy + r // 2,
            fill=skull_shadow, outline="", **kw))
        items.append(self.canvas.create_polygon(
            cx + r - 2, cy + 1,
            cx + r // 2, cy + r // 4,
            cx + r // 3, cy + r // 2,
            cx + r - 4, cy + r // 2,
            fill=skull_shadow, outline="", **kw))
        eye_w = max(4, r // 2)
        eye_h = max(4, r // 3)
        items.append(self.canvas.create_oval(
            cx - eye_w - 2, cy - eye_h // 2,
            cx - 1, cy + eye_h,
            fill=socket_fill, outline="#2b2b2b", width=1, **kw))
        items.append(self.canvas.create_oval(
            cx + 1, cy - eye_h // 2,
            cx + eye_w + 2, cy + eye_h,
            fill=socket_fill, outline="#2b2b2b", width=1, **kw))
        items.append(self.canvas.create_line(
            cx - r // 2, cy - 1, cx + r // 2, cy - 1,
            fill=skull_shadow, width=2, **kw))
        items.append(self.canvas.create_polygon(
            cx, cy + 3,
            cx - max(2, r // 6), cy + max(6, r // 2),
            cx + max(2, r // 6), cy + max(6, r // 2),
            fill="#5a5a5a", outline="#3e3e3e", width=1, **kw))
        mouth_y = cy + r // 2 + 1
        items.append(self.canvas.create_rectangle(
            cx - jaw_w // 2 + 1, mouth_y,
            cx + jaw_w // 2 - 1, mouth_y + max(4, r // 3),
            fill=tooth_fill, outline=skull_outline, width=1, **kw))
        tooth_count = 4 if r < 12 else 5
        tooth_step = jaw_w / tooth_count
        for index in range(1, tooth_count):
            tx = cx - jaw_w / 2 + tooth_step * index
            items.append(self.canvas.create_line(
                tx, mouth_y + 1, tx, mouth_y + max(3, r // 3),
                fill=skull_shadow, width=1, **kw))
        if r >= 8:
            items.append(self.canvas.create_line(
                cx + r // 3, cy - r + 3,
                cx + r // 4, cy - r // 2,
                cx + r // 2, cy - r // 5,
                fill="#7b7469", width=1, **kw))
        return items

    def _draw_bone(self, x1, y1, x2, y2):
        color = "#c8c0a0"
        mid_y = (y1 + y2) // 2
        half_h = max(3, (y2 - y1) // 4)
        ball_r = half_h + 3
        self.canvas.create_rectangle(x1 + ball_r, mid_y - half_h,
                                     x2 - ball_r, mid_y + half_h,
                                     fill=color, outline="", width=0)
        for cx in [x1 + ball_r, x2 - ball_r]:
            self.canvas.create_oval(cx - ball_r, mid_y - ball_r, cx + ball_r, mid_y + ball_r,
                                    fill=color, outline="")
            self.canvas.create_oval(cx - ball_r + 3, mid_y - ball_r + 3,
                                    cx + ball_r - 3, mid_y + ball_r - 3,
                                    fill="#d8d0b8", outline="")

    def _draw_vbone(self, x1, y1, x2, y2):
        color = "#c8c0a0"
        mid_x = (x1 + x2) // 2
        half_w = max(3, (x2 - x1) // 4)
        ball_r = half_w + 3
        self.canvas.create_rectangle(mid_x - half_w, y1 + ball_r,
                                     mid_x + half_w, y2 - ball_r,
                                     fill=color, outline="", width=0)
        for cy in [y1 + ball_r, y2 - ball_r]:
            self.canvas.create_oval(mid_x - ball_r, cy - ball_r, mid_x + ball_r, cy + ball_r,
                                    fill=color, outline="")
            self.canvas.create_oval(mid_x - ball_r + 3, cy - ball_r + 3,
                                    mid_x + ball_r - 3, cy + ball_r - 3,
                                    fill="#d8d0b8", outline="")

    def _draw_bone_borders(self):
        for x in range(20, WIDTH - 20, 80):
            self._draw_bone(x, 4, x + 60, 18)
        for y in range(50, HEIGHT - 40, 80):
            self._draw_vbone(2, y, 14, y + 60)
        for y in range(50, HEIGHT - 40, 80):
            self._draw_vbone(WIDTH - 14, y, WIDTH - 2, y + 60)
        for cx, cy in [(10, 10), (WIDTH - 10, 10), (10, HEIGHT - 10), (WIDTH - 10, HEIGHT - 10)]:
            self._draw_skull_shape(cx, cy, 8)

    def _create_haunted_sky(self):
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#05000f", outline="")
        self.moon_glow = self.canvas.create_oval(
            WIDTH - 210, 25, WIDTH - 70, 165,
            fill="#2a0008", outline=""
        )
        self.moon = self.canvas.create_oval(
            WIDTH - 190, 40, WIDTH - 90, 140,
            fill="#7d0f19", outline="#c74444", width=2
        )
        self.moon_crack_1 = self.canvas.create_line(
            WIDTH - 145, 45, WIDTH - 155, 75, WIDTH - 130, 95, WIDTH - 150, 130,
            fill="#2b0000", width=2
        )
        self.moon_crack_2 = self.canvas.create_line(
            WIDTH - 120, 55, WIDTH - 110, 85, WIDTH - 132, 115,
            fill="#2b0000", width=2
        )
        self.far_eyes = []
        for ex, ey in [(110, 92), (155, 150), (690, 185), (520, 118)]:
            left = self.canvas.create_oval(ex, ey, ex + 8, ey + 4, fill="#cc1111", outline="")
            right = self.canvas.create_oval(ex + 12, ey, ex + 20, ey + 4, fill="#cc1111", outline="")
            self.far_eyes.extend([left, right])
        for _ in range(FOG_COUNT):
            x = random.randint(-40, WIDTH - 60)
            y = random.randint(80, HEIGHT - 100)
            w = random.randint(120, 220)
            h = random.randint(24, 40)
            band = self.canvas.create_oval(
                x, y, x + w, y + h,
                fill="#140f1f", outline=""
            )
            self.fog_bands.append({
                "id": band,
                "x": float(x),
                "y": float(y),
                "w": w,
                "dx": random.uniform(0.15, 0.45),
                "bob": random.uniform(0.2, 0.6),
                "phase": random.uniform(0, math.pi * 2),
            })

    def _draw_lightning_bolt(self):
        """Draw a random jagged lightning bolt from sky to near ground."""
        ids = []
        x = random.randint(60, WIDTH - 60)
        y = 0
        segs = random.randint(5, 9)
        seg_h = random.randint(40, 70)
        fork_done = False
        pts = [(x, y)]
        cx, cy = x, y
        for i in range(segs):
            cx += random.randint(-40, 40)
            cy += seg_h
            pts.append((cx, cy))
        # main bolt
        for i in range(len(pts) - 1):
            ids.append(self.canvas.create_line(
                pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1],
                fill="#ffffff", width=3, tags="lightning"))
            # yellow glow behind
            ids.append(self.canvas.create_line(
                pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1],
                fill="#ffffaa", width=6, tags="lightning"))
            self.canvas.tag_lower(ids[-1], ids[-2])
        # small fork from middle segment
        mid = len(pts) // 2
        fx, fy = pts[mid]
        fpts = [(fx, fy)]
        fcx, fcy = fx, fy
        for _ in range(3):
            fcx += random.randint(-25, 25)
            fcy += random.randint(20, 40)
            fpts.append((fcx, fcy))
        for i in range(len(fpts) - 1):
            ids.append(self.canvas.create_line(
                fpts[i][0], fpts[i][1], fpts[i+1][0], fpts[i+1][1],
                fill="#ccccff", width=2, tags="lightning"))
        self.lightning_bolts.extend(ids)

    def _clear_lightning_bolts(self):
        for bid in self.lightning_bolts:
            self.canvas.delete(bid)
        self.lightning_bolts = []

    def _update_ambient_horror(self):
        if self.lightning_ticks > 0:
            self.lightning_ticks -= 1
            self.canvas.configure(bg="#1a1730")
            self.canvas.itemconfig(self.moon, fill="#b6262f", outline="#ff8e8e")
            if self.lightning_ticks == 0:
                self._clear_lightning_bolts()
        else:
            self.canvas.configure(bg="#08001a")
            self.canvas.itemconfig(self.moon, fill="#7d0f19", outline="#c74444")
            if random.random() < LIGHTNING_CHANCE:
                self.lightning_ticks = 3
                self._clear_lightning_bolts()
                for _ in range(random.randint(1, 2)):
                    self._draw_lightning_bolt()

        eye_color = "#ff6666" if self.lightning_ticks else "#cc1111"
        for eye in self.far_eyes:
            self.canvas.itemconfig(eye, fill=eye_color)

        for fog in self.fog_bands:
            prev_x = fog["x"]
            prev_y = fog["y"]
            fog["x"] += fog["dx"]
            fog["phase"] += fog["bob"] * 0.03
            fog["y"] += math.sin(fog["phase"]) * 0.15
            if fog["x"] > WIDTH + 20:
                fog["x"] = -fog["w"]
            mx = fog["x"] - prev_x
            my = fog["y"] - prev_y
            self.canvas.move(fog["id"], mx, my)

    def _create_ghost_shape(self, x, y, size):
        body_color = "#c8d4ff"
        edge_color = "#93a6ef"
        glow = self.canvas.create_oval(
            x - size - 6, y - size - 6, x + size + 6, y + size + 14,
            fill="#151533", outline=""
        )
        head = self.canvas.create_oval(
            x - size, y - size, x + size, y + size,
            fill=body_color, outline=edge_color, width=1
        )
        body = self.canvas.create_rectangle(
            x - size, y, x + size, y + size + 12,
            fill=body_color, outline=edge_color, width=1
        )
        eye_l = self.canvas.create_oval(
            x - size // 2 - 2, y - size // 3, x - size // 2 + 2, y - size // 3 + 4,
            fill="#ff4b4b", outline=""
        )
        eye_r = self.canvas.create_oval(
            x + size // 2 - 2, y - size // 3, x + size // 2 + 2, y - size // 3 + 4,
            fill="#ff4b4b", outline=""
        )
        wave = []
        step = max(6, (size * 2) // 4)
        start_x = x - size
        for i in range(5):
            wx = start_x + i * step
            wave.append(self.canvas.create_oval(
                wx, y + size + 5, wx + step, y + size + 14,
                fill=body_color, outline=edge_color, width=1
            ))
        parts = [glow, head, body, eye_l, eye_r] + wave
        return parts

    def _create_ghosts(self):
        for _ in range(GHOST_COUNT):
            size = random.randint(13, 22)
            x = random.randint(50, WIDTH - 50)
            y = random.randint(65, HEIGHT - 140)
            parts = self._create_ghost_shape(x, y, size)
            ghost = {
                "parts": parts,
                "x": float(x),
                "y": float(y),
                "dx": random.choice([-1, 1]) * random.uniform(0.18, 0.45),
                "bob": random.uniform(0.25, 0.55),
                "phase": random.uniform(0, math.pi * 2),
            }
            self.ghosts.append(ghost)

    def _update_ghosts(self):
        for ghost in self.ghosts:
            prev_x = ghost["x"]
            prev_y = ghost["y"]
            ghost["x"] += ghost["dx"]
            ghost["phase"] += ghost["bob"] * 0.045
            ghost["y"] += math.sin(ghost["phase"]) * 0.28

            if ghost["x"] < 32:
                ghost["x"] = 32
                ghost["dx"] *= -1
            elif ghost["x"] > WIDTH - 32:
                ghost["x"] = WIDTH - 32
                ghost["dx"] *= -1

            mx = ghost["x"] - prev_x
            my = ghost["y"] - prev_y
            for part in ghost["parts"]:
                self.canvas.move(part, mx, my)

    def _create_zombie_shape(self, x, y, size):
        skin = "#7fbf6a"
        shadow = "#4a6f3d"
        cloth = "#4b3f5f"
        glow = self.canvas.create_oval(
            x - size - 6, y - size - 8, x + size + 6, y + size + 22,
            fill="#112211", outline=""
        )
        head = self.canvas.create_oval(
            x - size, y - size, x + size, y + size,
            fill=skin, outline=shadow, width=1
        )
        jaw = self.canvas.create_rectangle(
            x - size + 3, y + size - 3, x + size - 3, y + size + size // 2,
            fill=skin, outline=shadow, width=1
        )
        torso = self.canvas.create_rectangle(
            x - size, y + size // 2, x + size, y + size + 18,
            fill=cloth, outline="#2b2335", width=1
        )
        arm_l = self.canvas.create_rectangle(
            x - size - 8, y + size // 2 + 3, x - size + 2, y + size + 12,
            fill=skin, outline=shadow, width=1
        )
        arm_r = self.canvas.create_rectangle(
            x + size - 2, y + size // 2 + 3, x + size + 8, y + size + 12,
            fill=skin, outline=shadow, width=1
        )
        eye_l = self.canvas.create_rectangle(
            x - size // 2 - 3, y - size // 3, x - size // 2 + 2, y - size // 3 + 4,
            fill="#ff2a2a", outline=""
        )
        eye_r = self.canvas.create_rectangle(
            x + size // 2 - 2, y - size // 3, x + size // 2 + 3, y - size // 3 + 4,
            fill="#ff2a2a", outline=""
        )
        mouth = self.canvas.create_line(
            x - size // 2, y + size // 2, x + size // 2, y + size // 2,
            fill="#1a1a1a", width=2
        )
        parts = [glow, head, jaw, torso, arm_l, arm_r, eye_l, eye_r, mouth]
        return parts

    def _create_zombies(self):
        for _ in range(ZOMBIE_COUNT):
            size = random.randint(12, 20)
            x = random.randint(40, WIDTH - 40)
            y = random.randint(70, HEIGHT - 120)
            parts = self._create_zombie_shape(x, y, size)
            zombie = {
                "parts": parts,
                "x": float(x),
                "y": float(y),
                "dx": random.choice([-1, 1]) * random.uniform(0.2, 0.6),
                "bob": random.uniform(0.2, 0.5),
                "phase": random.uniform(0, math.pi * 2),
            }
            self.zombies.append(zombie)

    def _update_zombies(self):
        for zombie in self.zombies:
            prev_x = zombie["x"]
            prev_y = zombie["y"]
            zombie["x"] += zombie["dx"]
            zombie["phase"] += zombie["bob"] * 0.05
            zombie["y"] += math.sin(zombie["phase"]) * 0.2

            if zombie["x"] < 30:
                zombie["x"] = 30
                zombie["dx"] *= -1
            elif zombie["x"] > WIDTH - 30:
                zombie["x"] = WIDTH - 30
                zombie["dx"] *= -1

            mx = zombie["x"] - prev_x
            my = zombie["y"] - prev_y
            for part in zombie["parts"]:
                self.canvas.move(part, mx, my)

    # ─── Create objects ───

    def _create_paddle(self):
        x = WIDTH // 2
        y = HEIGHT - 40
        self.paddle = self.canvas.create_rectangle(
            x - PADDLE_W // 2, y,
            x + PADDLE_W // 2, y + PADDLE_H,
            fill="#e8dfc0", outline="#c8b870", width=2
        )
        self.paddle_skull = self._draw_skull_shape(x, y + PADDLE_H // 2, PADDLE_H // 2 - 1)

    def _create_ball(self):
        x = WIDTH // 2
        y = HEIGHT - 60
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R, x + BALL_R, y + BALL_R,
            fill="", outline="", tags="ball_group"
        )
        self._draw_skull_shape(x, y, BALL_R, tag="ball_group")

    def _create_bricks(self):
        self.bricks = []
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        for row in range(BRICK_ROWS):
            ri = row % len(BRICK_COLORS)
            color = BRICK_COLORS[ri]
            hi = BRICK_HIGHLIGHT[ri]
            sh = BRICK_SHADOW[ri]
            points = BRICK_POINTS[row]
            for col in range(BRICK_COLS):
                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color, outline="#000000", width=1
                )
                # Top highlight edge
                hl = self.canvas.create_line(x1+1, y1+1, x2-1, y1+1, fill=hi, width=2)
                # Bottom shadow edge
                sl = self.canvas.create_line(x1+1, y2-2, x2-1, y2-2, fill=sh, width=2)
                # Left highlight
                ll = self.canvas.create_line(x1+1, y1+1, x1+1, y2-1, fill=hi, width=2)
                label = self.canvas.create_text(
                    (x1 + x2) // 2, (y1 + y2) // 2,
                    text=SKULL_CHAR, fill="#ffffff",
                    font=("Arial", 11)
                )
                self.bricks.append({"id": rect, "hl": hl, "sl": sl, "ll": ll,
                                    "label": label, "points": points,
                                    "color": color})

    def _create_speed_block(self):
        center_x = WIDTH // 2
        center_y = HEIGHT // 2 - 35
        glow = self.canvas.create_oval(
            center_x - SPEED_BLOCK_W // 2 - 10,
            center_y - SPEED_BLOCK_H // 2 - 10,
            center_x + SPEED_BLOCK_W // 2 + 10,
            center_y + SPEED_BLOCK_H // 2 + 10,
            fill="#1f1f34", outline="", width=0
        )
        block = self.canvas.create_rectangle(
            center_x - SPEED_BLOCK_W // 2,
            center_y - SPEED_BLOCK_H // 2,
            center_x + SPEED_BLOCK_W // 2,
            center_y + SPEED_BLOCK_H // 2,
            fill="#ffffff", outline="#d8d8ff", width=2
        )
        label = self.canvas.create_text(
            center_x, center_y,
            text="SPEED", fill="#222244",
            font=("Courier", 12, "bold")
        )
        self.speed_block = {
            "glow": glow,
            "id": block,
            "label": label,
            "active": True,
        }
        self.canvas.tag_lower(glow, block)

    def _reset_speed_block(self):
        if hasattr(self, "speed_block"):
            for item in (self.speed_block["glow"], self.speed_block["id"], self.speed_block["label"]):
                self.canvas.delete(item)
        self._create_speed_block()

    def _redraw_skulls(self):
        if hasattr(self, 'heart_ids'):
            for skull_items in self.heart_ids:
                for hid in skull_items:
                    self.canvas.delete(hid)
        self.heart_ids = []
        for i in range(self.lives):
            hx = WIDTH - 40 - i * 35
            hy = 25
            skull_items = self._draw_skull_shape(hx, hy, 13)
            self.heart_ids.append(skull_items)

    def _create_ui(self):
        self.score_text = self.canvas.create_text(
            15, 20, text=f"Score: {self.score}",
            fill="#00ff88", font=("Courier", 18, "bold"), anchor="w"
        )
        self.best_text = self.canvas.create_text(
            WIDTH // 2, 20, text=f"Best: {self.best_score}",
            fill="#e6e6e6", font=("Courier", 15, "bold"), anchor="n"
        )
        self.mode_text = self.canvas.create_text(
            WIDTH - 15, 20, text="Mode: NORMAL",
            fill="#f1c40f", font=("Courier", 14, "bold"), anchor="e"
        )

    def _update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
        self.canvas.itemconfig(self.best_text, text=f"Best: {self.best_score}")
        mode_label = DIFFICULTY_PRESETS[self.difficulty]["label"]
        self.canvas.itemconfig(self.mode_text, text=f"Mode: {mode_label}")
        self._redraw_skulls()

    def _show_start_screen(self):
        self._clear_overlay_items()
        self.start_items = []
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 70,
            text="☠  ARKANOID  ☠", fill="#cc3300",
            font=("Courier", 40, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 20,
            text="SKELETON EDITION", fill="#888888",
            font=("Courier", 16, "italic")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text="Press SPACE if you dare", fill="white",
            font=("Courier", 20)
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 55,
            text="← → move | P pause | R restart", fill="#aaaaaa",
            font=("Courier", 15)
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 84,
            text="1 easy   2 normal   3 hard", fill="#f1c40f",
            font=("Courier", 14, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 112,
            text="The dead are watching from the fog", fill="#b34a4a",
            font=("Courier", 13)
        ))

    # ─── Controls ───

    def _set_paddle_speed(self, speed):
        self.paddle_speed = speed

    def _stop_paddle(self, direction):
        if direction == "left" and self.paddle_speed < 0:
            self.paddle_speed = 0
        elif direction == "right" and self.paddle_speed > 0:
            self.paddle_speed = 0

    def _start_game(self, event=None):
        if not self.game_started and not self.game_over:
            self.paused = False
            self.game_started = True
            for item in self.start_items:
                self.canvas.delete(item)
            self.start_items.clear()

    def _toggle_pause(self, event=None):
        if not self.game_started or self.game_over:
            return
        self.paused = not self.paused
        if self.paused:
            self.start_items = [
                self.canvas.create_text(
                    WIDTH // 2, HEIGHT // 2,
                    text="PAUSED", fill="#ffffff",
                    font=("Courier", 34, "bold")
                )
            ]
        else:
            if hasattr(self, "start_items"):
                for item in self.start_items:
                    self.canvas.delete(item)
                self.start_items.clear()

    def _restart_game(self, event=None):
        self.score = 0
        self.lives = 5
        self.game_over = False
        self.game_started = False
        self.paused = False
        self._clear_overlay_items()
        if hasattr(self, "start_items"):
            for item in self.start_items:
                self.canvas.delete(item)
            self.start_items = []
        self._clear_bricks()
        self._create_bricks()
        self._apply_difficulty()
        self._update_score()
        self._reset_ball()
        self._refresh_start_screen()

    def _increase_ball_speed(self):
        preset = DIFFICULTY_PRESETS[self.difficulty]
        speed = math.sqrt(self.ball_dx ** 2 + self.ball_dy ** 2)
        if speed == 0:
            return
        new_speed = min(preset["max"], speed + preset["speedup"])
        scale = new_speed / speed
        self.ball_dx *= scale
        self.ball_dy *= scale

    def _boost_ball_speed(self, bonus=1.2):
        preset = DIFFICULTY_PRESETS[self.difficulty]
        speed = math.sqrt(self.ball_dx ** 2 + self.ball_dy ** 2)
        if speed == 0:
            return
        new_speed = min(preset["max"] + 1.5, speed + bonus)
        scale = new_speed / speed
        self.ball_dx *= scale
        self.ball_dy *= scale

    # ─── Effects ───

    def _spawn_particles(self, cx, cy, color, count=14):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(2, 7)
            dx = spd * math.cos(angle)
            dy = spd * math.sin(angle)
            size = random.randint(3, 7)
            pid = self.canvas.create_oval(
                cx - size, cy - size, cx + size, cy + size,
                fill=color, outline=""
            )
            life = random.randint(12, 22)
            self.particles.append({"id": pid, "dx": dx, "dy": dy,
                                    "life": life, "max_life": life})

    def _update_particles(self):
        dead = []
        for p in self.particles:
            self.canvas.move(p["id"], p["dx"], p["dy"])
            p["dy"] += 0.4  # gravity
            p["life"] -= 1
            # Fade by shrinking
            if p["life"] <= 0:
                self.canvas.delete(p["id"])
                dead.append(p)
        for p in dead:
            self.particles.remove(p)

    def _update_trail(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        bcx = (bx1 + bx2) / 2
        bcy = (by1 + by2) / 2

        sizes = [BALL_R * (i + 1) // (TRAIL_LENGTH + 1) for i in range(TRAIL_LENGTH)]
        colors = ["#cc2200", "#992200", "#661100", "#440000", "#330000", "#220000", "#110000"]

        tid = self.canvas.create_oval(
            bcx - BALL_R + 2, bcy - BALL_R + 2,
            bcx + BALL_R - 2, bcy + BALL_R - 2,
            fill=colors[0], outline=""
        )
        self.canvas.tag_lower(tid, "ball_group")
        self.trail.append(tid)

        if len(self.trail) > TRAIL_LENGTH:
            old = self.trail.pop(0)
            self.canvas.delete(old)

        for i, tid in enumerate(self.trail):
            alpha = i / len(self.trail)
            sz = max(1, int(BALL_R * alpha))
            ci = min(i, len(colors) - 1)
            try:
                self.canvas.itemconfig(tid, fill=colors[ci])
            except Exception:
                pass

    def _show_score_popup(self, x, y, pts):
        pid = self.canvas.create_text(
            x, y, text=f"+{pts}",
            fill="#ffff00", font=("Courier", 14, "bold")
        )
        self.popups.append({"id": pid, "life": 20})

    def _update_popups(self):
        dead = []
        for p in self.popups:
            self.canvas.move(p["id"], 0, -1)
            p["life"] -= 1
            if p["life"] <= 0:
                self.canvas.delete(p["id"])
                dead.append(p)
        for p in dead:
            self.popups.remove(p)

    def _update_paddle_flash(self):
        if self.paddle_flash > 0:
            self.paddle_flash -= 1
            flash_color = "#ffffff" if self.paddle_flash % 4 < 2 else "#e8dfc0"
            self.canvas.itemconfig(self.paddle, fill=flash_color)
        else:
            self.canvas.itemconfig(self.paddle, fill="#e8dfc0")

    # ─── Game loop ───

    def _game_loop(self):
        self._update_ambient_horror()
        self._update_ghosts()
        self._update_zombies()
        if self.game_started and not self.game_over and not self.paused:
            self._move_paddle()
            self._move_ball()
            self._check_collisions()
            self._update_trail()
            self._update_paddle_flash()
        self._update_particles()
        self._update_popups()
        self.root.after(1000 // FPS, self._game_loop)

    def _move_paddle(self):
        coords = self.canvas.coords(self.paddle)
        if self.paddle_speed < 0 and coords[0] > 16:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
            for item in self.paddle_skull:
                self.canvas.move(item, self.paddle_speed, 0)
        elif self.paddle_speed > 0 and coords[2] < WIDTH - 16:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
            for item in self.paddle_skull:
                self.canvas.move(item, self.paddle_speed, 0)

    def _move_ball(self):
        self.canvas.move("ball_group", self.ball_dx, self.ball_dy)

    def _check_collisions(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        bcx = (bx1 + bx2) / 2

        if bx1 <= 16:
            self.ball_dx = abs(self.ball_dx)
        if bx2 >= WIDTH - 16:
            self.ball_dx = -abs(self.ball_dx)
        if by1 <= 20:
            self.ball_dy = abs(self.ball_dy)

        if self.speed_block["active"]:
            sx1, sy1, sx2, sy2 = self.canvas.coords(self.speed_block["id"])
            if bx2 >= sx1 and bx1 <= sx2 and by2 >= sy1 and by1 <= sy2:
                self._boost_ball_speed()
                self._show_score_popup((sx1 + sx2) / 2, sy1 - 12, 0)
                self.canvas.itemconfig(self.popups[-1]["id"], text="SPEED UP", fill="#ffffff")
                self._spawn_particles((sx1 + sx2) / 2, (sy1 + sy2) / 2, "#ffffff", count=20)
                self.canvas.delete(self.speed_block["glow"])
                self.canvas.delete(self.speed_block["id"])
                self.canvas.delete(self.speed_block["label"])
                self.speed_block["active"] = False
                self.ball_dy *= -1

        if by2 >= HEIGHT:
            self.lives -= 1
            self.lightning_ticks = 3
            self._update_score()
            if self.lives <= 0:
                self._game_over_screen()
                return
            else:
                self._reset_ball()
                return

        px1, py1, px2, py2 = self.canvas.coords(self.paddle)
        if (self.ball_dy > 0 and
                by2 >= py1 and by1 <= py2 and
                bx2 >= px1 and bx1 <= px2):
            hit_pos = (bcx - (px1 + px2) / 2) / (PADDLE_W / 2)
            hit_pos = max(-1, min(1, hit_pos))
            angle = math.radians(30 + (1 - abs(hit_pos)) * 60)
            speed = math.sqrt(self.ball_dx ** 2 + self.ball_dy ** 2)
            preset = DIFFICULTY_PRESETS[self.difficulty]
            speed = min(max(speed + preset["speedup"], preset["initial"]), preset["max"])
            self.ball_dx = speed * math.cos(angle) * (1 if hit_pos >= 0 else -1)
            self.ball_dy = -abs(speed * math.sin(angle))
            self.canvas.coords(self.ball, bx1, py1 - BALL_R * 2, bx2, py1)
            self.paddle_flash = 8
            self._spawn_particles(bcx, py1, "#e8dfc0", count=8)

        for brick in self.bricks[:]:
            brx1, bry1, brx2, bry2 = self.canvas.coords(brick["id"])
            if (bx2 >= brx1 and bx1 <= brx2 and
                    by2 >= bry1 and by1 <= bry2):
                self.score += brick["points"]
                cx_b = (brx1 + brx2) / 2
                cy_b = (bry1 + bry2) / 2
                color = brick.get("color", "#888888")
                self._spawn_particles(cx_b, cy_b, color, count=16)
                self._show_score_popup(cx_b, bry1, brick["points"])
                self.canvas.delete(brick["id"])
                self.canvas.delete(brick["label"])
                self.canvas.delete(brick.get("hl", ""))
                self.canvas.delete(brick.get("sl", ""))
                self.canvas.delete(brick.get("ll", ""))
                self.bricks.remove(brick)
                if self.score > self.best_score:
                    self.best_score = self.score
                    self._save_best_score()
                self._update_score()

                overlap_left = bx2 - brx1
                overlap_right = brx2 - bx1
                overlap_top = by2 - bry1
                overlap_bottom = bry2 - by1
                min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                if min_overlap == overlap_top or min_overlap == overlap_bottom:
                    self.ball_dy *= -1
                else:
                    self.ball_dx *= -1
                self._increase_ball_speed()
                break

        if len(self.bricks) == 0:
            self._game_win()

    def _reset_ball(self):
        self.canvas.delete("ball_group")
        for tid in self.trail:
            self.canvas.delete(tid)
        self.trail.clear()
        self._reset_speed_block()
        x, y = WIDTH // 2, HEIGHT - 60
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R, x + BALL_R, y + BALL_R,
            fill="", outline="", tags="ball_group"
        )
        self._draw_skull_shape(x, y, BALL_R, tag="ball_group")

        self.canvas.coords(
            self.paddle,
            WIDTH // 2 - PADDLE_W // 2, HEIGHT - 40     ,
            WIDTH // 2 + PADDLE_W // 2, HEIGHT - 40 + PADDLE_H
        )
        for item in self.paddle_skull:
            self.canvas.delete(item)
        self.paddle_skull = self._draw_skull_shape(
            WIDTH // 2, HEIGHT - 40 + PADDLE_H // 2, PADDLE_H // 2 - 1
        )

        self._apply_difficulty()
        self.game_started = False
        self.paused = False
        msg = self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text="☠  Press SPACE to continue  ☠", fill="white",
            font=("Courier", 18)
        )
        self.start_items = [msg]

    def _game_over_screen(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self._clear_overlay_items()
        self.overlay_items.append(self.canvas.create_rectangle(
            WIDTH // 2 - 230, HEIGHT // 2 - 80,
            WIDTH // 2 + 230, HEIGHT // 2 + 80,
            fill="#08001a", outline="#cc0000", width=4
        ))
        self.overlay_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 35,
            text="☠  GAME OVER  ☠", fill="#cc0000",
            font=("Courier", 30, "bold")
        ))
        self.overlay_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text=f"Final Score: {self.score}", fill="white",
            font=("Courier", 20)
        ))
        self.overlay_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 30,
            text=f"Best: {self.best_score}", fill="#e6e6e6",
            font=("Courier", 14)
        ))
        self.overlay_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 52,
            text="The graveyard kept your name.", fill="#8a3d3d",
            font=("Courier", 13)
        ))
        for cx in [WIDTH // 2 - 80, WIDTH // 2, WIDTH // 2 + 80]:
            self.overlay_items.extend(self._draw_skull_shape(cx, HEIGHT // 2 - 65, 10))

    def _game_win(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self._clear_overlay_items()
        self.overlay_items.append(self.canvas.create_rectangle(
            WIDTH // 2 - 230, HEIGHT // 2 - 80,
            WIDTH // 2 + 230, HEIGHT // 2 + 80,
            fill="#08001a", outline="#00cc44", width=4
        ))
        self.overlay_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 35,
            text="☠  YOU WIN!  ☠", fill="#00cc44",
            font=("Courier", 30, "bold")
        ))
        self.overlay_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text=f"Final Score: {self.score}", fill="white",
            font=("Courier", 20)
        ))
        self.overlay_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 30,
            text=f"Best: {self.best_score}", fill="#e6e6e6",
            font=("Courier", 14)
        ))
        self.overlay_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 52,
            text="For tonight, the darkness obeys you.", fill="#b3b3b3",
            font=("Courier", 13)
        ))
        for cx in [WIDTH // 2 - 80, WIDTH // 2, WIDTH // 2 + 80]:
            self.overlay_items.extend(self._draw_skull_shape(cx, HEIGHT // 2 - 65, 10))


if __name__ == "__main__":
    Arkanoid()
