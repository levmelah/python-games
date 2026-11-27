import tkinter as tk
import random
import math

# ─── Constants ───
WIDTH = 800
HEIGHT = 600
PADDLE_W = 100
PADDLE_H = 15
BALL_R = 8
BRICK_ROWS = 3
BRICK_COLS = 7
BRICK_W = 70
BRICK_H = 25
BRICK_PAD = 4
TOP_OFFSET = 60
FPS = 60

BRICK_COLORS = ["#ff1900", "#ff7700", "#ffcc00", "#00ff6a", "#0099ff"]
BRICK_POINTS = [50, 40, 30, 20, 10]


class Arkanoid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🦜 Tropical Arkanoid")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#87ceeb")
        self.canvas.pack()

        self.frame_count = 0
        self._draw_sky_background()
        self._create_floating_clouds()
        self._create_butterflies()

        self.score = 0
        self.lives = 3
        self.game_started = False
        self.game_over = False

        # Ball speed
        self.ball_dx = 4
        self.ball_dy = -4

        # Paddle speed
        self.paddle_speed = 0

        # Create objects
        self._create_paddle()
        self._create_ball()
        self._create_bricks()
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

    # ─── Background ───

    def _draw_sky_background(self):
        # Sky gradient
        for i in range(100):
            y = i * HEIGHT // 100
            color_val = int(135 + (i * 0.3))
            green_val = int(206 + (i * 0.2))
            blue_val = int(235 + (i * 0.1))
            color = f"#{color_val:02x}{green_val:02x}{blue_val:02x}"
            self.canvas.create_line(0, y, WIDTH, y, fill=color)
        
        # Sun
        sun = self.canvas.create_oval(
            WIDTH - 120, 30, 
            WIDTH - 30, 120,
            fill="#facc15", outline="#fde047", width=3
        )
        # Sun rays
        for i in range(12):
            angle = i * math.pi / 6
            x1 = WIDTH - 75 + 60 * math.cos(angle)
            y1 = 75 + 60 * math.sin(angle)
            x2 = WIDTH - 75 + 80 * math.cos(angle)
            y2 = 75 + 80 * math.sin(angle)
            self.canvas.create_line(x1, y1, x2, y2, fill="#fde047", width=2)
        
        # Rainbow arcs (more vibrant)
        rainbow_colors = ["#ef4444", "#f97316", "#facc15", "#22c55e", "#3b82f6", "#8b5cf6"]
        for i, color in enumerate(rainbow_colors):
            self.canvas.create_arc(
                WIDTH // 2 - 300 + i * 10,
                -170 + i * 10,
                WIDTH // 2 + 300 - i * 10,
                370 - i * 10,
                start=28,
                extent=124,
                style=tk.ARC,
                outline=color,
                width=10
            )
        
        # Mountains in background
        mountains = [
            (0, 350, 80, 270, 160, 340, 230, 290, 300, 350),
            (200, 340, 280, 260, 360, 330, 430, 280, 500, 350),
            (400, 350, 480, 280, 560, 340, 630, 300, 700, 350),
            (600, 340, 680, 270, 760, 330, 800, 310)
        ]
        for m in mountains:
            self.canvas.create_polygon(m, fill="#6b8f71", outline="#5a7a60", width=1)
            # Snow caps
            self.canvas.create_polygon(
                m[0], m[1]-5, m[2], m[3]-5, m[4], m[5]-5,
                fill="#ffffff", outline=""
            )
        
        # Palm trees (simplified)
        palm_positions = [(50, 330), (740, 340), (30, 350), (760, 360)]
        for x, y in palm_positions:
            # Trunk
            self.canvas.create_line(x, y, x-10, y-40, fill="#8B7355", width=6)
            # Leaves
            for angle in [-60, -30, 0, 30, 60]:
                rad = math.radians(angle)
                x1 = x - 10 + 15 * math.cos(rad)
                y1 = y - 40 + 15 * math.sin(rad)
                x2 = x - 10 + 45 * math.cos(rad + 0.5)
                y2 = y - 40 + 20 * math.sin(rad + 0.5)
                self.canvas.create_line(x1, y1, x2, y2, fill="#22c55e", width=3)
        
        # Ocean in distance
        self.canvas.create_rectangle(0, HEIGHT-20, WIDTH, HEIGHT, fill="#0ea5e9", outline="")
        self.canvas.create_rectangle(0, HEIGHT-10, WIDTH, HEIGHT, fill="#0284c7", outline="")

    def _create_floating_clouds(self):
        """Create animated clouds."""
        self.clouds = []
        cloud_positions = [
            (115, 110, 1.1, 0.3),
            (300, 85, 1.35, -0.5),
            (520, 95, 1.2, 0.4),
            (705, 125, 1.0, -0.3),
            (200, 180, 0.8, 0.6),
            (600, 200, 0.9, -0.4)
        ]
        for x, y, scale, speed in cloud_positions:
            cloud = self._draw_cloud(x, y, scale)
            self.clouds.append({"id": cloud, "x": x, "speed": speed})

    def _draw_cloud(self, cx, cy, scale=1.0):
        r = 24 * scale
        cloud_parts = []
        # Cloud body
        parts = [
            (cx - r * 2.2, cy - r * 0.7, cx + r * 2.2, cy + r * 1.1),
            (cx - r * 1.8, cy - r * 1.3, cx - r * 0.4, cy + r * 0.3),
            (cx - r * 0.7, cy - r * 1.6, cx + r * 0.8, cy + r * 0.2),
            (cx + r * 0.4, cy - r * 1.2, cx + r * 1.9, cy + r * 0.4)
        ]
        for x1, y1, x2, y2 in parts:
            cloud = self.canvas.create_oval(x1, y1, x2, y2, fill="white", outline="#e0e7ff", width=1)
            cloud_parts.append(cloud)
        return cloud_parts

    def _create_butterflies(self):
        """Create decorative butterflies."""
        self.butterflies = []
        for _ in range(5):
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, 300)
            color = random.choice(["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6"])
            butterfly = self.canvas.create_polygon(
                x-8, y-4, x, y-8, x+8, y-4, x, y,
                fill=color, outline=color
            )
            self.butterflies.append({
                "id": butterfly,
                "x": x,
                "y": y,
                "dx": random.uniform(0.5, 1.5),
                "dy": random.uniform(-0.5, 0.5),
                "phase": random.uniform(0, 2*math.pi)
            })

    def _animate_background(self):
        """Animate background elements."""
        self.frame_count += 1
        
        # Move clouds
        for cloud in self.clouds:
            cloud["x"] += cloud["speed"]
            if cloud["x"] > WIDTH + 50:
                cloud["x"] = -100
            for i, part in enumerate(cloud["id"]):
                self.canvas.move(part, cloud["speed"], 0)
        
        # Animate butterflies
        for butterfly in self.butterflies:
            butterfly["x"] += butterfly["dx"]
            butterfly["y"] += math.sin(self.frame_count * 0.05 + butterfly["phase"]) * 0.5
            if butterfly["x"] > WIDTH:
                butterfly["x"] = 0
            if butterfly["x"] < 0:
                butterfly["x"] = WIDTH
            # Wing flapping
            scale = 1 + 0.3 * math.sin(self.frame_count * 0.1 + butterfly["phase"])
            self.canvas.coords(
                butterfly["id"],
                butterfly["x"]-8*scale, butterfly["y"]-4,
                butterfly["x"], butterfly["y"]-8*scale,
                butterfly["x"]+8*scale, butterfly["y"]-4,
                butterfly["x"], butterfly["y"]
            )

    # ─── Create objects ───

    def _create_paddle(self):
        x = WIDTH // 2
        y = HEIGHT - 40
        # Tropical paddle
        self.paddle = self.canvas.create_rectangle(
            x - PADDLE_W // 2, y,
            x + PADDLE_W // 2, y + PADDLE_H,
            fill="#00d4ff", outline="#00d4ff", width=0
        )
        # Decorative flowers on paddle
        for i in range(3):
            fx = x - 30 + i * 30
            self._draw_flower(fx, y-5, 6, random.choice(["#ef4444", "#facc15", "#f97316"]))

    def _draw_flower(self, cx, cy, size, color):
        """Draw a small decorative flower."""
        for i in range(5):
            angle = i * 2*math.pi / 5
            x = cx + size * math.cos(angle)
            y = cy + size * math.sin(angle)
            self.canvas.create_oval(x-size/2, y-size/2, x+size/2, y+size/2, 
                                   fill=color, outline="")
        self.canvas.create_oval(cx-size/3, cy-size/3, cx+size/3, cy+size/3, 
                               fill="#facc15", outline="")

    def _create_ball(self):
        x = WIDTH // 2
        y = HEIGHT - 60
        # Tropical ball - like a fruit
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R,
            x + BALL_R, y + BALL_R,
            fill="#facc15", outline="#f59e0b", width=2
        )
        # Leaf on ball
        self.ball_leaf = self.canvas.create_polygon(
            x, y-BALL_R,
            x-3, y-BALL_R-8,
            x+3, y-BALL_R-8,
            fill="#22c55e", outline="#16a34a"
        )

    def _create_bricks(self):
        self.bricks = []
        # More vibrant parrot colors
        parrot_palettes = [
            {"body": "#ef4444", "wing_main": "#2563eb", "wing_accent": "#facc15", "tail": "#1d4ed8", "chest": "#fca5a5"},
            {"body": "#f97316", "wing_main": "#1d4ed8", "wing_accent": "#fde047", "tail": "#1e40af", "chest": "#fdba74"},
            {"body": "#dc2626", "wing_main": "#0ea5e9", "wing_accent": "#eab308", "tail": "#2563eb", "chest": "#fca5a5"},
            {"body": "#8b5cf6", "wing_main": "#06b6d4", "wing_accent": "#fde047", "tail": "#2563eb", "chest": "#c4b5fd"},
            {"body": "#ec4899", "wing_main": "#3b82f6", "wing_accent": "#facc15", "tail": "#1d4ed8", "chest": "#f9a8d4"},
            {"body": "#14b8a6", "wing_main": "#8b5cf6", "wing_accent": "#fde047", "tail": "#1e40af", "chest": "#99f6e4"},
        ]
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        for row in range(BRICK_ROWS):
            points = BRICK_POINTS[row]
            for col in range(BRICK_COLS):
                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                palette = parrot_palettes[(row * BRICK_COLS + col) % len(parrot_palettes)]
                facing = -1 if (row + col) % 2 == 0 else 1

                # Body
                body = self.canvas.create_oval(
                    cx - 15, cy - 10, cx + 12, cy + 10,
                    fill=palette["body"], outline="#7f1d1d", width=2
                )
                # Chest
                chest = self.canvas.create_oval(
                    cx - 8, cy - 4, cx + 4, cy + 8,
                    fill=palette["chest"], outline=""
                )
                # Wing
                wing = self.canvas.create_polygon(
                    cx - 5, cy - 1,
                    cx + 6, cy - 8,
                    cx + 12, cy + 1,
                    cx + 2, cy + 8,
                    fill=palette["wing_main"], outline="#1e3a8a", width=1
                )
                # Wing accent
                wing_accent = self.canvas.create_polygon(
                    cx - 1, cy,
                    cx + 6, cy - 4,
                    cx + 10, cy + 2,
                    cx + 3, cy + 5,
                    fill=palette["wing_accent"], outline=""
                )
                # Head
                head = self.canvas.create_oval(
                    cx - 20 * facing - 7, cy - 12,
                    cx - 20 * facing + 7, cy + 1,
                    fill="#fff7ed", outline="#d6d3d1", width=1
                )
                # Eye
                eye = self.canvas.create_oval(
                    cx - 20 * facing - 2, cy - 8,
                    cx - 20 * facing + 1, cy - 5,
                    fill="#111827", outline=""
                )
                # Eye shine
                eye_shine = self.canvas.create_oval(
                    cx - 20 * facing - 1, cy - 7,
                    cx - 20 * facing, cy - 6,
                    fill="white", outline=""
                )
                # Beak
                beak = self.canvas.create_polygon(
                    cx - 25 * facing, cy - 6,
                    cx - 32 * facing, cy - 3,
                    cx - 25 * facing, cy,
                    fill="#0f172a", outline="#334155", width=1
                )
                # Tail feathers
                tail_colors = [palette["tail"], palette["wing_main"], palette["wing_accent"]]
                for i, color in enumerate(tail_colors):
                    tail = self.canvas.create_polygon(
                        cx + 11 + i*2, cy + 5 + i*2,
                        cx + 24 + i*2, cy + 12 + i*2,
                        cx + 14 + i*2, cy + 13 + i*2,
                        cx + 6 + i*2, cy + 8 + i*2,
                        fill=color, outline="#1e3a8a", width=1
                    )
                    # Store tail separately
                    tail_id = tail

                # Small branch/perch
                branch = self.canvas.create_line(
                    cx - 22, cy + 12,
                    cx + 22, cy + 12,
                    fill="#8B7355", width=3
                )

                self.bricks.append({
                    "id": body,
                    "extra_ids": [chest, wing, wing_accent, head, eye, eye_shine, beak, tail_id, branch],
                    "points": points,
                    "bbox": [x1, y1, x2, y2],
                    "vx": (0.7 + row * 0.08) * (-1 if (row + col) % 2 == 0 else 1),
                    "flap_phase": random.uniform(0, 2*math.pi)
                })

    def _move_birds(self):
        """Animate parrots with wing flapping."""
        for brick in self.bricks:
            x1, y1, x2, y2 = brick["bbox"]
            vx = brick["vx"]

            # Bounce inside game area
            if x1 + vx < 5 or x2 + vx > WIDTH - 5:
                vx *= -1
                brick["vx"] = vx

            # Move all parts
            self.canvas.move(brick["id"], vx, 0)
            for extra_id in brick.get("extra_ids", []):
                self.canvas.move(extra_id, vx, 0)

            brick["bbox"][0] += vx
            brick["bbox"][2] += vx

            # Wing flapping (only for the wing part - second extra_id)
            if len(brick["extra_ids"]) >= 3:
                wing_id = brick["extra_ids"][1]  # Wing
                coords = self.canvas.coords(wing_id)
                if coords:
                    flap = math.sin(self.frame_count * 0.1 + brick["flap_phase"])
                    # Slight wing movement
                    self.canvas.coords(
                        wing_id,
                        coords[0], coords[1] + flap,
                        coords[2], coords[3] + flap,
                        coords[4], coords[5] + flap,
                        coords[6], coords[7] + flap
                    )

    def _draw_heart(self, cx, cy, size=14):
        points = []
        for i in range(100):
            t = 2 * math.pi * i / 100
            x = size * 16 * (math.sin(t) ** 3) / 16
            y = -size * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)) / 16
            points.append(cx + x)
            points.append(cy + y)
        return self.canvas.create_polygon(points, fill="#ff0066", outline="#cc0055", width=1, smooth=True)

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
        # Tropical HUD - moved to top left
        self.hud_frame = self.canvas.create_rectangle(
            10, 10, 200, 40,
            outline="#00d4ff", fill="#000020", width=1
        )
        self.score_text = self.canvas.create_text(
            25, 25, text=f"🦜 SCORE: {self.score}",
            fill="#00d4ff", font=("Courier", 16, "bold"), anchor="w"
        )
        # Title at top center - moved down slightly
        self.title_text = self.canvas.create_text(
            WIDTH//2, 45,
            text="🌴 TROPICAL PARADISE 🌴", fill="#ffffff",
            font=("Courier", 12, "bold")
        )

    def _update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"🦜 SCORE: {self.score}")
        self._redraw_hearts()

    def _show_start_screen(self):
        self.start_items = []
        # Main title - moved up
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, 140,
            text="🦜 TROPICAL ARKANOID 🦜", fill="#00d4ff",
            font=("Courier", 44, "bold")
        ))
        # Subtitle - moved down
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, 200,
            text="🐦 PARROT EDITION 🐦", fill="#facc15",
            font=("Courier", 20, "bold")
        ))
        # Press space - moved down
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, 280,
            text="▶  PRESS SPACE TO START  ◀", fill="#ffffff",
            font=("Courier", 24, "bold")
        ))
        # Controls - moved down
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, 340,
            text="←  →  =  MOVE PADDLE", fill="#88ddff",
            font=("Courier", 18)
        ))
        # Slogan - moved down
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, 400,
            text="🦜 SAVE THE PARROTS! 🦜", fill="#facc15",
            font=("Courier", 20, "bold")
        ))
        # Decorative line
        self.start_items.append(self.canvas.create_line(
            WIDTH//2 - 200, 430,
            WIDTH//2 + 200, 430,
            fill="#00d4ff", width=2, dash=(10, 5)
        ))
        # Version
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, 460,
            text="v2.0 - Tropical Paradise", fill="#8888ff",
            font=("Courier", 10)
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
        self._animate_background()
        
        if self.game_started and not self.game_over:
            self._move_paddle()
            self._move_birds()
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
        self.canvas.move(self.ball_leaf, self.ball_dx, self.ball_dy)

    def _check_collisions(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        bcx = (bx1 + bx2) / 2

        # Wall collisions
        if bx1 <= 0:
            self.ball_dx = abs(self.ball_dx)
            self._create_explosion(bcx, by1, 10)
        if bx2 >= WIDTH:
            self.ball_dx = -abs(self.ball_dx)
            self._create_explosion(bcx, by1, 10)
        if by1 <= 0:
            self.ball_dy = abs(self.ball_dy)
            self._create_explosion(bcx, by1, 10)

        # Bottom — lose life
        if by2 >= HEIGHT:
            self._create_explosion(bcx, HEIGHT-20, 20)
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
            self._sync_ball_leaf(bx1, py1 - BALL_R * 2, bx2, py1)
            self._create_explosion(bcx, py1, 15)

        # Brick collision
        for brick in self.bricks[:]:
            brx1, bry1, brx2, bry2 = brick["bbox"]
            if (bx2 >= brx1 and bx1 <= brx2 and
                    by2 >= bry1 and by1 <= bry2):
                self.score += brick["points"]
                # Explosion effect
                self._create_explosion((brx1+brx2)/2, (bry1+bry2)/2, 25)
                # Delete all parts
                self.canvas.delete(brick["id"])
                for extra_id in brick.get("extra_ids", []):
                    self.canvas.delete(extra_id)
                self.bricks.remove(brick)
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
        if len(self.bricks) == 0:
            self._game_win()

    def _create_explosion(self, cx, cy, size):
        """Create colorful explosion effect."""
        particles = []
        colors = ["#ef4444", "#f97316", "#facc15", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6"]
        for _ in range(25):
            angle = random.uniform(0, 2*math.pi)
            distance = random.uniform(3, size)
            dx = distance * math.cos(angle)
            dy = distance * math.sin(angle)
            size_p = random.randint(2, 6)
            color = random.choice(colors)
            particle = self.canvas.create_oval(
                cx + dx - size_p, cy + dy - size_p,
                cx + dx + size_p, cy + dy + size_p,
                fill=color, outline=""
            )
            particles.append({
                "id": particle,
                "dx": dx / 8,
                "dy": dy / 8,
                "life": 25
            })
        
        def animate_particles():
            for p in particles[:]:
                self.canvas.move(p["id"], p["dx"], p["dy"])
                p["life"] -= 1
                if p["life"] <= 0:
                    self.canvas.delete(p["id"])
                    particles.remove(p)
            if particles:
                self.root.after(50, animate_particles)
        
        animate_particles()

    def _sync_ball_leaf(self, bx1, by1, bx2, by2):
        cx = (bx1 + bx2) / 2
        cy = (by1 + by2) / 2
        self.canvas.coords(
            self.ball_leaf,
            cx, cy-BALL_R,
            cx-3, cy-BALL_R-8,
            cx+3, cy-BALL_R-8
        )

    def _reset_ball(self):
        self.canvas.coords(
            self.ball,
            WIDTH // 2 - BALL_R, HEIGHT - 60 - BALL_R,
            WIDTH // 2 + BALL_R, HEIGHT - 60 + BALL_R
        )
        self._sync_ball_leaf(
            WIDTH // 2 - BALL_R, HEIGHT - 60 - BALL_R,
            WIDTH // 2 + BALL_R, HEIGHT - 60 + BALL_R
        )
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
            text="🔄 PRESS SPACE TO CONTINUE 🔄", fill="#00d4ff",
            font=("Courier", 18, "bold")
        )
        self.start_items = [msg]

    def _game_over_screen(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self.canvas.create_rectangle(
            WIDTH // 2 - 250, HEIGHT // 2 - 80,
            WIDTH // 2 + 250, HEIGHT // 2 + 80,
            fill="#000020", outline="#ff0044", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 30,
            text="🦜 GAME OVER 🦜", fill="#ff0044",
            font=("Courier", 32, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text=f"FINAL SCORE: {self.score}", fill="#ffffff",
            font=("Courier", 22, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 55,
            text="😢 THE PARROTS ARE SAD 😢", fill="#00d4ff",
            font=("Courier", 14, "bold")
        )

    def _game_win(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self.canvas.create_rectangle(
            WIDTH // 2 - 250, HEIGHT // 2 - 80,
            WIDTH // 2 + 250, HEIGHT // 2 + 80,
            fill="#000020", outline="#00ff66", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 30,
            text="🌟 YOU'RE A HERO! 🌟", fill="#00ff66",
            font=("Courier", 32, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text=f"FINAL SCORE: {self.score}", fill="#ffffff",
            font=("Courier", 22, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 55,
            text="🦜 THE PARROTS ARE FREE! 🦜", fill="#facc15",
            font=("Courier", 14, "bold")
        )

if __name__ == "__main__":
    Arkanoid()