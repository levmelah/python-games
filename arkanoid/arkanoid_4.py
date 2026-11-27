import tkinter as tk
import random
import math

# ─── Constants ───
WIDTH = 800
HEIGHT = 600
PADDLE_W = 100
PADDLE_H = 15
BALL_R = 8
PUFFER_INFLATE_ADD = 6
FISH_ROWS = 5
FISH_COLS = 8
FISH_W = 78
FISH_H = 30
FISH_PAD = 14
SHARK_W = 138
SHARK_H = 34
TOP_OFFSET = 82
FPS = 60

FISH_COLORS = ["#b0c0d0", "#a8c8a8", "#d0c8a0", "#c8a8c8", "#a8b8d0"]
FISH_POINTS = [50, 40, 30, 20, 10]


class Arkanoid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Fish Hunter")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#0a2a4a")
        self.canvas.pack()

        self.score = 0
        self.lives = 3
        self.game_started = False
        self.game_over = False
        self.wave_tick = 0

        # Ball speed
        self.ball_dx = 4
        self.ball_dy = -4

        # Paddle speed
        self.paddle_speed = 0

        # Create objects
        self._draw_underwater_bg()
        self._create_paddle()
        self._create_ball()
        self._create_shark()
        self._create_fish_school()
        self._create_ui()
        self._redraw_hearts()
        self._show_start_screen()

        # Bindings
        self.root.bind("<KeyPress-Left>", lambda e: self._set_paddle_speed(-8))
        self.root.bind("<KeyRelease-Left>", lambda e: self._stop_paddle("left"))
        self.root.bind("<KeyPress-Right>", lambda e: self._set_paddle_speed(8))
        self.root.bind("<KeyRelease-Right>", lambda e: self._stop_paddle("right"))
        self.root.bind("<space>", self._start_game)

        self._game_loop()
        self.root.mainloop()

    # ─── Underwater background ───

    def _draw_underwater_bg(self):
        # Water gradient layers (dark deep → lighter top)
        layers = [
            (0,   60,  "#0a2a4a"),
            (60,  120, "#0b3055"),
            (120, 180, "#0d3a66"),
            (180, 260, "#0f4478"),
            (260, 360, "#114e8a"),
            (360, 460, "#135898"),
            (460, 540, "#1a6aaa"),
            (540, HEIGHT, "#1e78bb"),
        ]
        for y1, y2, color in layers:
            self.canvas.create_rectangle(0, y1, WIDTH, y2, fill=color, outline="")

        # Sun light rays from top
        ray_color = "#1e90ff"
        ray_positions = [80, 160, 280, 400, 520, 650, 730]
        ray_widths    = [40,  25,  55,  30,  50,  20,  45]
        for rx, rw in zip(ray_positions, ray_widths):
            self.canvas.create_polygon(
                rx - rw//2, 0,
                rx + rw//2, 0,
                rx + rw*2,  HEIGHT//2,
                rx - rw*2,  HEIGHT//2,
                fill=ray_color, outline="", stipple="gray25"
            )

        # Surface shimmer lines
        for i in range(12):
            sy = 4 + i * 4
            self.canvas.create_line(
                random.randint(0, 200), sy,
                random.randint(200, 500), sy,
                fill="#5bcfff", width=1
            )
            self.canvas.create_line(
                random.randint(400, 620), sy,
                random.randint(620, WIDTH), sy,
                fill="#5bcfff", width=1
            )

        # Seabed
        self.canvas.create_rectangle(0, HEIGHT-38, WIDTH, HEIGHT, fill="#c8a96e", outline="")
        self.canvas.create_rectangle(0, HEIGHT-44, WIDTH, HEIGHT-38, fill="#d4b87a", outline="")
        # Seabed pebbles
        for _ in range(28):
            px = random.randint(0, WIDTH)
            pr = random.randint(3, 9)
            self.canvas.create_oval(px-pr, HEIGHT-44, px+pr, HEIGHT-38+pr//2,
                                    fill="#bfa060", outline="#a08840")

        # Coral clusters
        corals = [
            (60,  HEIGHT-44, "#ff4466"),
            (160, HEIGHT-44, "#ff7733"),
            (310, HEIGHT-44, "#ff4488"),
            (480, HEIGHT-44, "#ffaa00"),
            (620, HEIGHT-44, "#ff3355"),
            (740, HEIGHT-44, "#ff6600"),
        ]
        for cx, cy, cc in corals:
            # branches
            for angle, length in [(-60,28),(-30,34),(0,38),(30,34),(60,28)]:
                rad = math.radians(angle - 90)
                ex = cx + length * math.cos(rad)
                ey = cy + length * math.sin(rad)
                self.canvas.create_line(cx, cy, ex, ey, fill=cc, width=3, capstyle="round")
                self.canvas.create_oval(ex-4, ey-4, ex+4, ey+4, fill=cc, outline="")

        # Seaweed
        for sx in [120, 240, 385, 555, 680, 790]:
            pts = []
            for i in range(10):
                t = i / 9
                wy = (HEIGHT-44) - t * 70
                wx = sx + 10 * math.sin(t * math.pi * 3)
                pts += [wx, wy]
            self.canvas.create_line(*pts, fill="#22aa44", width=4, smooth=True)

        # Background bubbles
        for _ in range(35):
            bx = random.randint(10, WIDTH-10)
            by = random.randint(60, HEIGHT-60)
            br = random.randint(3, 10)
            self.canvas.create_oval(bx-br, by-br, bx+br, by+br,
                                    outline="#88ddff", width=1, fill="")
            self.canvas.create_arc(bx-br+2, by-br+2, bx+2, by,
                                   start=40, extent=60,
                                   outline="#cceeff", width=1, style="arc")

    # ─── Create objects ───

    def _create_paddle(self):
        x = WIDTH // 2
        y = HEIGHT - 40
        self.paddle = self.canvas.create_rectangle(
            x - PADDLE_W // 2, y,
            x + PADDLE_W // 2, y + PADDLE_H,
            fill="#00d4ff", outline="#00d4ff", width=0
        )

    def _create_ball(self):
        x = WIDTH // 2
        y = HEIGHT - 60
        self.ball_inflated = False
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R,
            x + BALL_R, y + BALL_R,
            fill="", outline=""
        )
        self.ball_sprite_ids = []
        self.ball_sprite_center = (x, y)
        self._draw_puffer_ball(x, y)

    def _draw_puffer_ball(self, cx, cy):
        for item_id in self.ball_sprite_ids:
            self.canvas.delete(item_id)

        puffer_r = BALL_R + 3 + (PUFFER_INFLATE_ADD if self.ball_inflated else 0)
        eye_offset = 5 + (2 if self.ball_inflated else 0)
        mouth_size = 3 + (1 if self.ball_inflated else 0)

        spike_ids = []
        for i in range(18 if self.ball_inflated else 16):
            ang = (2 * math.pi * i) / 16
            inner = puffer_r
            outer = puffer_r + 5 + (1 if i % 2 == 0 else -1)
            x1 = cx + inner * math.cos(ang)
            y1 = cy + inner * math.sin(ang)
            x2 = cx + outer * math.cos(ang)
            y2 = cy + outer * math.sin(ang)
            spike_ids.append(self.canvas.create_line(
                x1, y1, x2, y2,
                fill="#f7e1a3", width=2,
                tags=("ball_puffer",)
            ))

        body = self.canvas.create_oval(
            cx - puffer_r, cy - puffer_r,
            cx + puffer_r, cy + puffer_r,
            fill="#f4cf7a", outline="#9e7a2a", width=2,
            tags=("ball_puffer",)
        )
        belly = self.canvas.create_oval(
            cx - (puffer_r - 2), cy - 1,
            cx + (puffer_r - 2), cy + (puffer_r - 1),
            fill="#f7e6bc", outline="", tags=("ball_puffer",)
        )
        left_eye = self.canvas.create_oval(
            cx - eye_offset, cy - 5, cx - eye_offset + 4, cy - 1,
            fill="white", outline="#222", width=1,
            tags=("ball_puffer",)
        )
        right_eye = self.canvas.create_oval(
            cx + eye_offset - 4, cy - 5, cx + eye_offset, cy - 1,
            fill="white", outline="#222", width=1,
            tags=("ball_puffer",)
        )
        left_pupil = self.canvas.create_oval(
            cx - eye_offset + 1, cy - 4, cx - eye_offset + 3, cy - 2,
            fill="#111", outline="", tags=("ball_puffer",)
        )
        right_pupil = self.canvas.create_oval(
            cx + eye_offset - 3, cy - 4, cx + eye_offset - 1, cy - 2,
            fill="#111", outline="", tags=("ball_puffer",)
        )
        mouth = self.canvas.create_oval(
            cx - mouth_size, cy + 1, cx + mouth_size, cy + 1 + 2 * mouth_size,
            fill="#5d3a1e", outline="#3b2412", width=1,
            tags=("ball_puffer",)
        )

        self.ball_sprite_ids = [*spike_ids, body, belly, left_eye, right_eye, left_pupil, right_pupil, mouth]
        self.ball_sprite_center = (cx, cy)
        self.canvas.tag_raise("ball_puffer")

    def _set_ball_inflated(self, inflated):
        if self.ball_inflated == inflated:
            return
        self.ball_inflated = inflated
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        cx = (bx1 + bx2) / 2
        cy = (by1 + by2) / 2
        self._draw_puffer_ball(cx, cy)

    def _sync_ball_sprite(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        cx = (bx1 + bx2) / 2
        cy = (by1 + by2) / 2
        old_x, old_y = self.ball_sprite_center
        dx = cx - old_x
        dy = cy - old_y
        if abs(dx) > 0.001 or abs(dy) > 0.001:
            for item_id in self.ball_sprite_ids:
                self.canvas.move(item_id, dx, dy)
            self.ball_sprite_center = (cx, cy)

    def _draw_fish(self, x1, y1, color, tag, wave=0):
        x2 = x1 + FISH_W
        y2 = y1 + FISH_H
        cy = y1 + FISH_H / 2
        tw = 5 * math.sin(wave)
        dk = "#3a4a5a"

        # Main body - realistic fish shape (head right, tail left)
        body = self.canvas.create_polygon(
            x1+18, cy,
            x1+24, y1+6,
            x1+36, y1+2,
            x1+52, y1+3,
            x1+64, y1+8,
            x1+72, cy,
            x1+64, y2-8,
            x1+52, y2-3,
            x1+36, y2-2,
            x1+24, y2-6,
            x1+18, cy,
            fill=color, outline=dk, width=2,
            smooth=True,
            tags=(tag, "fish")
        )
        # Forked tail - 5 points (animated)
        tail = self.canvas.create_polygon(
            x1+18, cy-3,
            x1,    y1+2+tw,
            x1+8,  cy,
            x1,    y2-2+tw,
            x1+18, cy+3,
            fill=color, outline=dk, width=1,
            smooth=False,
            tags=(tag, "fish_tail")
        )
        # Dorsal fin - spiky ridge on top
        dorsal = self.canvas.create_polygon(
            x1+28, y1+4,
            x1+30, y1-5,
            x1+35, y1-8,
            x1+40, y1-5,
            x1+45, y1-9,
            x1+50, y1-5,
            x1+54, y1-2,
            x1+57, y1+3,
            fill=color, outline=dk, width=1,
            smooth=False,
            tags=(tag, "fish")
        )
        # Ventral fin - bottom
        ventral = self.canvas.create_polygon(
            x1+42, cy+2,
            x1+46, y2+2,
            x1+52, y2+3,
            x1+56, cy+2,
            fill=color, outline=dk, width=1,
            smooth=True,
            tags=(tag, "fish")
        )
        # Gill arc
        gill = self.canvas.create_arc(
            x1+52, y1+4, x1+70, y2-4,
            start=110, extent=120,
            outline=dk, width=2, style="arc",
            tags=(tag, "fish")
        )
        # Horizontal body stripes
        sc = "#607080"
        stripes = []
        for sy in [cy-6, cy-2, cy+2, cy+6]:
            stripes.append(self.canvas.create_line(
                x1+22, sy, x1+62, sy,
                fill=sc, width=1,
                tags=(tag, "fish")
            ))
        # Eye
        eye = self.canvas.create_oval(
            x1+58, y1+7, x1+68, y1+17,
            fill="white", outline=dk, width=1,
            tags=(tag, "fish")
        )
        pupil = self.canvas.create_oval(
            x1+60, y1+9, x1+66, y1+15,
            fill="#111111", outline="",
            tags=(tag, "fish")
        )
        return [body, tail, dorsal, ventral, gill, *stripes, eye, pupil]

    def _draw_shark(self, x1, y1, tag):
        x2 = x1 + SHARK_W
        y2 = y1 + SHARK_H
        cy = y1 + SHARK_H / 2

        # Top body (blue back)
        body = self.canvas.create_polygon(
            x1 + 26, cy,
            x1 + 40, y1 + 6,
            x1 + 66, y1 + 3,
            x1 + 92, y1 + 4,
            x1 + 118, y1 + 8,
            x1 + 134, cy,
            x1 + 118, y2 - 8,
            x1 + 92, y2 - 4,
            x1 + 66, y2 - 3,
            x1 + 40, y2 - 6,
            x1 + 26, cy,
            fill="#2b5f91", outline="#1f3f63", width=2,
            smooth=True,
            tags=(tag, "shark")
        )

        # White belly overlay for realistic shading
        belly = self.canvas.create_polygon(
            x1 + 42, cy + 1,
            x1 + 66, cy + 4,
            x1 + 98, cy + 5,
            x1 + 122, cy + 2,
            x1 + 130, cy,
            x1 + 122, y2 - 7,
            x1 + 94, y2 - 4,
            x1 + 66, y2 - 3,
            x1 + 48, y2 - 5,
            x1 + 42, cy + 2,
            fill="#dbe7ef", outline="#8aa6bc", width=1,
            smooth=True,
            tags=(tag, "shark")
        )

        # Crescent tail (animated in _move_shark)
        tail = self.canvas.create_polygon(
            x1 + 26, cy - 4,
            x1 + 6, y1 - 2,
            x1 + 14, cy,
            x1 + 6, y2 + 2,
            x1 + 26, cy + 4,
            fill="#2e6ca1", outline="#1f3f63", width=2,
            tags=(tag, "shark_tail")
        )

        # Tall dorsal fin
        dorsal = self.canvas.create_polygon(
            x1 + 72, y1 + 5,
            x1 + 84, y1 - 18,
            x1 + 96, y1 + 6,
            fill="#3b78ad", outline="#1f3f63", width=1,
            tags=(tag, "shark")
        )

        # Pectoral fin (bottom)
        pectoral = self.canvas.create_polygon(
            x1 + 76, y2 - 2,
            x1 + 70, y2 + 14,
            x1 + 86, y2 + 2,
            fill="#2e6ca1", outline="#1f3f63", width=1,
            tags=(tag, "shark")
        )

        # Gill slits
        gill_1 = self.canvas.create_line(
            x1 + 104, y1 + 10, x1 + 101, y2 - 2,
            fill="#7da0bd", width=2,
            tags=(tag, "shark")
        )
        gill_2 = self.canvas.create_line(
            x1 + 109, y1 + 11, x1 + 106, y2 - 1,
            fill="#7da0bd", width=2,
            tags=(tag, "shark")
        )

        eye = self.canvas.create_oval(
            x2 - 30, y1 + 10, x2 - 23, y1 + 17,
            fill="white", outline="#1f3f63", width=1,
            tags=(tag, "shark")
        )
        pupil = self.canvas.create_oval(
            x2 - 28, y1 + 12, x2 - 25, y1 + 15,
            fill="#111111", outline="",
            tags=(tag, "shark")
        )

        # Snout line
        snout = self.canvas.create_line(
            x2 - 16, cy, x2 - 2, cy - 2,
            fill="#1f3f63", width=2,
            tags=(tag, "shark")
        )
        return [body, tail, dorsal, pectoral, belly, gill_1, gill_2, eye, pupil, snout]

    def _create_shark(self):
        shark_x = WIDTH // 2 - SHARK_W // 2
        shark_y = 42
        self.shark = {
            "tag": "bonus_shark",
            "x1": shark_x,
            "y1": shark_y,
            "dx": random.choice([-2.0, 2.0]),
            "min_x": 10,
            "max_x": WIDTH - SHARK_W - 10,
            "hits": 0,
            "alive": True,
        }
        self.shark["parts"] = self._draw_shark(shark_x, shark_y, self.shark["tag"])

    def _create_fish_school(self):
        self.fish = []
        total_w = FISH_COLS * (FISH_W + FISH_PAD) - FISH_PAD
        start_x = (WIDTH - total_w) // 2
        for row in range(FISH_ROWS):
            color = FISH_COLORS[row]
            points = FISH_POINTS[row]
            row_speed = random.choice([1.2, 1.6, 2.0]) * random.choice([-1, 1])
            min_x = start_x
            max_x = start_x + total_w - FISH_W
            for col in range(FISH_COLS):
                x1 = start_x + col * (FISH_W + FISH_PAD)
                y1 = TOP_OFFSET + row * (FISH_H + FISH_PAD)
                tag = f"fish_{row}_{col}"
                # offset phase per fish so they don't all wag in sync
                phase = (row * FISH_COLS + col) * 0.4
                parts = self._draw_fish(x1, y1, color, tag, wave=phase)
                self.fish.append({
                    "tag": tag,
                    "parts": parts,
                    "points": points,
                    "dx": row_speed,
                    "min_x": min_x,
                    "max_x": max_x,
                    "x1": x1,
                    "y1": y1,
                    "color": color,
                    "phase": phase,
                })

    def _draw_heart(self, cx, cy, size=14):
        """Draw a heart shape using parametric equation."""
        points = []
        for i in range(100):
            t = 2 * math.pi * i / 100
            x = size * 16 * (math.sin(t) ** 3) / 16
            y = -size * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)) / 16
            points.append(cx + x)
            points.append(cy + y)
        return self.canvas.create_polygon(points, fill="#e74c3c", outline="#c0392b", width=1, smooth=True)

    def _redraw_hearts(self):
        if hasattr(self, 'heart_ids'):
            for hid in self.heart_ids:
                self.canvas.delete(hid)
        self.heart_ids = []
        for i in range(self.lives):
            hx = WIDTH - 40 - i * 35
            hy = 25
            hid = self._draw_heart(hx, hy, size=14)
            self.heart_ids.append(hid)

    def _create_ui(self):
        self.score_text = self.canvas.create_text(
            15, 20, text=f"Score: {self.score}",
            fill="white", font=("Courier", 18, "bold"), anchor="w"
        )

    def _update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
        self._redraw_hearts()

    def _show_start_screen(self):
        self.start_items = []
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 60,
            text="🐟 FISH HUNTER 🐟", fill="#f1c40f",
            font=("Courier", 38, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text="!לצוד כדי SPACE לחץ", fill="white",
            font=("Courier", 20)
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 40,
            text="המחבט הזזת = → ←", fill="#aaa",
            font=("Courier", 16)
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
            self.game_started = True
            for item in self.start_items:
                self.canvas.delete(item)
            self.start_items.clear()

    # ─── Game loop ───

    def _game_loop(self):
        if self.game_started and not self.game_over:
            self._move_paddle()
            self._move_fish_school()
            self._move_shark()
            self._move_ball()
            self._check_collisions()
        self.root.after(1000 // FPS, self._game_loop)

    def _move_paddle(self):
        coords = self.canvas.coords(self.paddle)
        if self.paddle_speed < 0 and coords[0] > 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
        elif self.paddle_speed > 0 and coords[2] < WIDTH - 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)

    def _move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        self._sync_ball_sprite()

    def _move_fish_school(self):
        self.wave_tick += 0.12
        for fish in self.fish:
            if not self.canvas.find_withtag(fish["tag"]):
                continue
            if fish["x1"] <= fish["min_x"] and fish["dx"] < 0:
                fish["dx"] *= -1
            elif fish["x1"] >= fish["max_x"] and fish["dx"] > 0:
                fish["dx"] *= -1
            fish["x1"] += fish["dx"]
            self.canvas.move(fish["tag"], fish["dx"], 0)
            # animate forked tail
            tail_id = fish["parts"][1]
            x1 = fish["x1"]
            y1 = fish["y1"]
            cy = y1 + FISH_H / 2
            tw = 5 * math.sin(self.wave_tick + fish["phase"])
            self.canvas.coords(
                tail_id,
                x1+18, cy-3,
                x1,    y1+2+tw,
                x1+8,  cy,
                x1,    y1+FISH_H-2+tw,
                x1+18, cy+3,
            )

    def _move_shark(self):
        if not self.shark["alive"] or not self.canvas.find_withtag(self.shark["tag"]):
            return
        if self.shark["x1"] <= self.shark["min_x"] and self.shark["dx"] < 0:
            self.shark["dx"] *= -1
        elif self.shark["x1"] >= self.shark["max_x"] and self.shark["dx"] > 0:
            self.shark["dx"] *= -1
        self.shark["x1"] += self.shark["dx"]
        self.canvas.move(self.shark["tag"], self.shark["dx"], 0)

        # subtle tail wag for life-like motion
        tail_id = self.shark["parts"][1]
        x1 = self.shark["x1"]
        y1 = self.shark["y1"]
        cy = y1 + SHARK_H / 2
        tw = 4 * math.sin(self.wave_tick * 1.1)
        self.canvas.coords(
            tail_id,
            x1 + 26, cy - 4,
            x1 + 6, y1 - 2 + tw,
            x1 + 14, cy,
            x1 + 6, y1 + SHARK_H + 2 + tw,
            x1 + 26, cy + 4,
        )

    def _check_collisions(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        bcx = (bx1 + bx2) / 2

        # Wall collisions
        if bx1 <= 0:
            self.ball_dx = abs(self.ball_dx)
        if bx2 >= WIDTH:
            self.ball_dx = -abs(self.ball_dx)
        if by1 <= 0:
            self.ball_dy = abs(self.ball_dy)

        # Bottom — lose life
        if by2 >= HEIGHT:
            self.lives -= 1
            self._update_score()
            if self.lives <= 0:
                self._game_over_screen()
                return
            else:
                self._reset_ball()
                return

        # Paddle collision
        px1, py1, px2, py2 = self.canvas.coords(self.paddle)
        if (self.ball_dy > 0 and
                by2 >= py1 and by1 <= py2 and
                bx2 >= px1 and bx1 <= px2):
            hit_pos = (bcx - (px1 + px2) / 2) / (PADDLE_W / 2)
            hit_pos = max(-1, min(1, hit_pos))
            angle = math.radians(30 + (1 - abs(hit_pos)) * 60)
            speed = math.sqrt(self.ball_dx**2 + self.ball_dy**2)
            speed = min(max(speed, 4), 8)
            self.ball_dx = speed * math.cos(angle) * (1 if hit_pos >= 0 else -1)
            self.ball_dy = -abs(speed * math.sin(angle))
            self.canvas.coords(self.ball, bx1, py1 - BALL_R * 2, bx2, py1)
            self._set_ball_inflated(False)
            self._sync_ball_sprite()

        # Shark collision: 2 hits destroy shark and give +100
        if self.shark["alive"]:
            shark_box = self.canvas.bbox(self.shark["tag"])
            if shark_box:
                sx1, sy1, sx2, sy2 = shark_box
                if (bx2 >= sx1 and bx1 <= sx2 and
                        by2 >= sy1 and by1 <= sy2):
                    self.shark["hits"] += 1

                    overlap_left = bx2 - sx1
                    overlap_right = sx2 - bx1
                    overlap_top = by2 - sy1
                    overlap_bottom = sy2 - by1
                    min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                    if min_overlap == overlap_top or min_overlap == overlap_bottom:
                        self.ball_dy *= -1
                    else:
                        self.ball_dx *= -1

                    if self.shark["hits"] >= 2:
                        self.shark["alive"] = False
                        self.canvas.delete(self.shark["tag"])
                        self.score += 100
                        self._update_score()
                    else:
                        # first hit feedback: darker body
                        self.canvas.itemconfig(self.shark["parts"][0], fill="#5f6d79")
                    return

        # Fish collision
        for fish in self.fish[:]:
            fish_box = self.canvas.bbox(fish["tag"])
            if not fish_box:
                continue
            brx1, bry1, brx2, bry2 = fish_box
            if (bx2 >= brx1 and bx1 <= brx2 and
                    by2 >= bry1 and by1 <= bry2):
                self._set_ball_inflated(True)
                self.score += fish["points"]
                self.canvas.delete(fish["tag"])
                self.fish.remove(fish)
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
                break

        # Win condition
        if len(self.fish) == 0:
            self._game_win()

    def _reset_ball(self):
        self.canvas.coords(
            self.ball,
            WIDTH // 2 - BALL_R, HEIGHT - 60 - BALL_R,
            WIDTH // 2 + BALL_R, HEIGHT - 60 + BALL_R
        )
        self._set_ball_inflated(False)
        self._sync_ball_sprite()
        self.canvas.coords(
            self.paddle,
            WIDTH // 2 - PADDLE_W // 2, HEIGHT - 40,
            WIDTH // 2 + PADDLE_W // 2, HEIGHT - 40 + PADDLE_H
        )
        self.ball_dx = 4 * random.choice([-1, 1])
        self.ball_dy = -4
        self.game_started = False
        msg = self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text="להמשך SPACE לחץ", fill="white",
            font=("Courier", 18)
        )
        self.start_items = [msg]

    def _game_over_screen(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self.canvas.create_rectangle(
            WIDTH // 2 - 200, HEIGHT // 2 - 60,
            WIDTH // 2 + 200, HEIGHT // 2 + 60,
            fill="#1a1a2e", outline="#e74c3c", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 20,
            text="🐠 !ברחו הדגים 🐠", fill="#e74c3c",
            font=("Courier", 32, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text=f"Final Score: {self.score}", fill="white",
            font=("Courier", 18)
        )

    def _game_win(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self.canvas.create_rectangle(
            WIDTH // 2 - 200, HEIGHT // 2 - 60,
            WIDTH // 2 + 200, HEIGHT // 2 + 60,
            fill="#1a1a2e", outline="#2ecc71", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 20,
            text="🎣 !הדגים כל את תפסת 🎣", fill="#2ecc71",
            font=("Courier", 32, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text=f"Final Score: {self.score}", fill="white",
            font=("Courier", 18)
        )


if __name__ == "__main__":
    Arkanoid()
