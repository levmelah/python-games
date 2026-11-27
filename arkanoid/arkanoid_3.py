import tkinter as tk
import random
import math
import time

# ─── Constants ───
WIDTH = 800
HEIGHT = 600
PADDLE_W = 100
PADDLE_H = 15
BALL_R = 8
BRICK_ROWS = 5
BRICK_COLS = 10
BRICK_W = 70
BRICK_H = 25
BRICK_PAD = 4
TOP_OFFSET = 60
FPS = 60

BRICK_COLORS = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db"]
BRICK_POINTS = [50, 40, 30, 20, 10]


class Arkanoid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("❄️ Antarctic Arkanoid ❄️")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#dff3ff")
        self.canvas.pack()
        
        self.frame_count = 0
        self._draw_antarctica_background()
        self._create_falling_snow()
        self._create_penguins()
        self._create_aurora()
        self._create_ice_bergs()

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

    # ─── Antarctic Background ───

    def _draw_antarctica_background(self):
        # Sky gradient - polar sky
        for i in range(100):
            y = i * HEIGHT // 100
            color_val = int(150 + (i * 0.8))
            blue_val = int(200 + (i * 0.5))
            color = f"#{color_val:02x}{blue_val:02x}{255:02x}"
            self.canvas.create_line(0, y, WIDTH, y, fill=color)
        
        # Distant mountains
        mountains = [
            (0, 280, 100, 180, 200, 260, 280, 200, 350, 270),
            (300, 250, 400, 160, 480, 230, 550, 190, 620, 250),
            (500, 270, 600, 200, 680, 240, 750, 190, 800, 260)
        ]
        for m in mountains:
            self.canvas.create_polygon(m, fill="#c8dce6", outline="#a8c4d4", width=1)
            # Snow caps
            self.canvas.create_polygon(
                m[0], m[1]-5, m[2], m[3]-5, m[4], m[5]-5,
                fill="#ffffff", outline=""
            )
        
        # Ice shelf
        self.canvas.create_polygon(
            0, HEIGHT - 140,
            150, HEIGHT - 180,
            300, HEIGHT - 160,
            450, HEIGHT - 200,
            600, HEIGHT - 170,
            750, HEIGHT - 190,
            WIDTH, HEIGHT - 150,
            WIDTH, HEIGHT,
            0, HEIGHT,
            fill="#e8f4f8", outline="#b5dde6", width=2
        )
        
        # Ice cracks on the shelf
        for i in range(10):
            x1 = random.randint(50, WIDTH-50)
            y1 = HEIGHT - random.randint(120, 170)
            x2 = x1 + random.randint(-30, 30)
            y2 = HEIGHT - random.randint(80, 120)
            self.canvas.create_line(x1, y1, x2, y2, fill="#b5dde6", width=1, dash=(4, 4))

    def _create_falling_snow(self):
        """Create falling snow particles."""
        self.snow_particles = []
        for _ in range(80):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.choice([1, 2, 3])
            speed = random.uniform(1, 3)
            drift = random.uniform(-0.5, 0.5)
            snow = self.canvas.create_oval(x, y, x+size, y+size, 
                                          fill="#ffffff", outline="")
            self.snow_particles.append({
                "id": snow,
                "x": x,
                "y": y,
                "speed": speed,
                "drift": drift,
                "size": size
            })

    def _create_penguins(self):
        """Create adorable penguins."""
        self.penguins = []
        penguin_positions = [
            (80, HEIGHT-60, 1),
            (150, HEIGHT-55, -1),
            (680, HEIGHT-65, 1),
            (730, HEIGHT-50, -1),
            (400, HEIGHT-70, 1)
        ]
        for x, y, direction in penguin_positions:
            penguin = self._draw_penguin(x, y, direction)
            self.penguins.append({
                "id": penguin,
                "x": x,
                "y": y,
                "direction": direction,
                "walk_frame": 0
            })

    def _draw_penguin(self, x, y, direction):
        """Draw a single penguin."""
        penguin_parts = []
        # Body
        body = self.canvas.create_oval(x-15, y-25, x+15, y+5, fill="#1a1a2e", outline="#0d0d1a")
        penguin_parts.append(body)
        # White belly
        belly = self.canvas.create_oval(x-10, y-20, x+10, y+3, fill="#ffffff", outline="")
        penguin_parts.append(belly)
        # Head
        head = self.canvas.create_oval(x-12, y-35, x+12, y-20, fill="#1a1a2e", outline="#0d0d1a")
        penguin_parts.append(head)
        # Eyes
        eye1 = self.canvas.create_oval(x-6, y-32, x-4, y-30, fill="white", outline="")
        eye2 = self.canvas.create_oval(x+4, y-32, x+6, y-30, fill="white", outline="")
        penguin_parts.extend([eye1, eye2])
        # Eye pupils
        pupil1 = self.canvas.create_oval(x-5, y-32, x-4, y-31, fill="black", outline="")
        pupil2 = self.canvas.create_oval(x+5, y-32, x+6, y-31, fill="black", outline="")
        penguin_parts.extend([pupil1, pupil2])
        # Beak
        beak = self.canvas.create_polygon(
            x + (10*direction), y-28,
            x + (17*direction), y-27,
            x + (10*direction), y-25,
            fill="#f59e0b", outline="#d97706"
        )
        penguin_parts.append(beak)
        # Wings
        wing1 = self.canvas.create_oval(x-20, y-20, x-10, y-5, fill="#1a1a2e", outline="#0d0d1a")
        wing2 = self.canvas.create_oval(x+10, y-20, x+20, y-5, fill="#1a1a2e", outline="#0d0d1a")
        penguin_parts.extend([wing1, wing2])
        # Feet
        foot1 = self.canvas.create_oval(x-8, y+3, x-2, y+10, fill="#f59e0b", outline="#d97706")
        foot2 = self.canvas.create_oval(x+2, y+3, x+8, y+10, fill="#f59e0b", outline="#d97706")
        penguin_parts.extend([foot1, foot2])
        return penguin_parts

    def _create_aurora(self):
        """Create animated aurora borealis."""
        self.aurora = []
        aurora_colors = ["#00ff66", "#00ccff", "#9900ff", "#ff00cc", "#00ff99"]
        for i in range(8):
            y_base = 50 + random.randint(0, 100)
            points = []
            for j in range(10):
                x = j * 90 + random.randint(-20, 20)
                y = y_base + 20 * math.sin(j * 0.8 + i * 1.2)
                points.extend([x, y])
            aurora = self.canvas.create_polygon(
                points, 
                fill=random.choice(aurora_colors), 
                outline="", 
                stipple="gray25",
                width=0
            )
            self.aurora.append({
                "id": aurora,
                "y_base": y_base,
                "phase": i * 1.2,
                "color": random.choice(aurora_colors)
            })

    def _create_ice_bergs(self):
        """Create floating icebergs in the background."""
        for _ in range(5):
            x = random.randint(30, WIDTH-30)
            y = random.randint(100, 250)
            size = random.randint(30, 60)
            points = []
            num_points = random.randint(5, 8)
            for i in range(num_points):
                angle = 2*math.pi * i / num_points
                r = size * random.uniform(0.5, 1.2)
                points.append(x + r * math.cos(angle))
                points.append(y + r * math.sin(angle) * 0.6)
            self.canvas.create_polygon(
                points,
                fill="#d4eaf7", outline="#a8d4e6", width=1,
                stipple="gray50"
            )

    def _animate_background(self):
        """Animate all background elements."""
        self.frame_count += 1
        
        # Falling snow
        for snow in self.snow_particles:
            snow["x"] += snow["drift"]
            snow["y"] += snow["speed"]
            if snow["y"] > HEIGHT:
                snow["y"] = -10
                snow["x"] = random.randint(0, WIDTH)
            if snow["x"] < 0:
                snow["x"] = WIDTH
            elif snow["x"] > WIDTH:
                snow["x"] = 0
            self.canvas.coords(snow["id"], snow["x"], snow["y"], 
                              snow["x"]+snow["size"], snow["y"]+snow["size"])
        
        # Aurora animation
        for aurora in self.aurora:
            aurora["phase"] += 0.02
            points = []
            for j in range(10):
                x = j * 90 + 20 * math.sin(j * 0.8 + aurora["phase"])
                y = aurora["y_base"] + 20 * math.sin(j * 0.8 + aurora["phase"] * 0.7)
                points.extend([x, y])
            self.canvas.coords(aurora["id"], *points)
        
        # Animate penguins
        for penguin in self.penguins:
            penguin["walk_frame"] += 1
            if penguin["walk_frame"] % 60 < 30:
                # Slight bobbing
                offset = 1 if penguin["walk_frame"] % 30 < 15 else -1
                for i, part in enumerate(penguin["id"]):
                    current_coords = self.canvas.coords(part)
                    if current_coords and i < len(penguin["id"]):
                        # Move feet slightly
                        if i >= len(penguin["id"]) - 2:  # Feet
                            self.canvas.move(part, 0, offset * 0.5)
            
            # Slow penguin waddle
            if penguin["walk_frame"] % 120 < 60:
                dx = penguin["direction"] * 0.2
                for part in penguin["id"]:
                    self.canvas.move(part, dx, 0)
                penguin["x"] += dx
                
                # Reverse direction at edges
                if penguin["x"] > WIDTH - 100 or penguin["x"] < 100:
                    penguin["direction"] *= -1
                    # Flip penguin (simple version - move wings)
                    for i, part in enumerate(penguin["id"]):
                        if i < len(penguin["id"]):
                            self.canvas.scale(part, penguin["x"], penguin["y"], -1, 1)

    # ─── Create objects ───

    def _create_paddle(self):
        x = WIDTH // 2
        y = HEIGHT - 40
        # Ice paddle
        self.paddle = self.canvas.create_rectangle(
            x - PADDLE_W // 2, y,
            x + PADDLE_W // 2, y + PADDLE_H,
            fill="#00d4ff", outline="#00d4ff", width=0
        )
        # Ice shine
        self.paddle_shine = self.canvas.create_rectangle(
            x - PADDLE_W // 2 + 5, y + 2,
            x + PADDLE_W // 2 - 5, y + 6,
            fill="#ffffff", outline="", stipple="gray25"
        )

    def _create_ball(self):
        x = WIDTH // 2
        y = HEIGHT - 60
        # Ice ball with glow
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R,
            x + BALL_R, y + BALL_R,
            fill="#88ddff", outline="#00ccff", width=2
        )
        # Inner core
        self.ball_core = self.canvas.create_oval(
            x - BALL_R//2, y - BALL_R//2,
            x + BALL_R//2, y + BALL_R//2,
            fill="#ffffff", outline=""
        )
        # Ice sparkle
        self.ball_sparkle = self.canvas.create_oval(
            x - 1, y - BALL_R//2,
            x + 1, y - BALL_R//2 + 3,
            fill="#ffffff", outline=""
        )

    def _create_bricks(self):
        self.bricks = []
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        
        ice_patterns = [
            {"base": "#cfefff", "dark": "#bde6fb", "crack": "#9ed2eb"},
            {"base": "#bde6fb", "dark": "#a8d4f0", "crack": "#85c7e6"},
            {"base": "#d4eaf7", "dark": "#c2dded", "crack": "#a8c8d8"},
            {"base": "#e8f4f8", "dark": "#d4eaf0", "crack": "#b5dde6"},
            {"base": "#c2dded", "dark": "#b0cfe0", "crack": "#90b8cc"},
        ]
        
        for row in range(BRICK_ROWS):
            points = BRICK_POINTS[row]
            pattern = ice_patterns[row % len(ice_patterns)]
            for col in range(BRICK_COLS):
                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H
                
                # Ice cube body
                ice_color = pattern["base"] if (row + col) % 2 == 0 else pattern["dark"]
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=ice_color, outline=pattern["dark"], width=2
                )
                
                # Ice shine on top
                shine = self.canvas.create_rectangle(
                    x1 + 3, y1 + 2, x2 - 3, y1 + 8,
                    fill="#ffffff", outline="", stipple="gray25"
                )
                
                # Frost patterns
                frost1 = self.canvas.create_line(
                    x1 + 10, y1 + 15,
                    x1 + 25, y1 + BRICK_H - 8,
                    fill=pattern["crack"], width=1, dash=(3, 3)
                )
                frost2 = self.canvas.create_line(
                    x2 - 10, y1 + 12,
                    x2 - 25, y2 - 10,
                    fill=pattern["crack"], width=1, dash=(3, 3)
                )
                frost3 = self.canvas.create_line(
                    x1 + 20, y1 + 5,
                    x1 + 40, y1 + 5,
                    fill=pattern["crack"], width=1, dash=(2, 4)
                )
                
                # Ice crystals (tiny sparkles)
                sparkles = []
                for _ in range(3):
                    sx = x1 + random.randint(5, BRICK_W-5)
                    sy = y1 + random.randint(5, BRICK_H-5)
                    sparkle = self.canvas.create_oval(
                        sx-1, sy-1, sx+1, sy+1,
                        fill="#ffffff", outline=""
                    )
                    sparkles.append(sparkle)
                
                self.bricks.append({
                    "id": rect,
                    "parts": [rect, shine, frost1, frost2, frost3] + sparkles,
                    "points": points,
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
        return self.canvas.create_polygon(points, fill="#ff0044", outline="#cc0033", width=1, smooth=True)

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
        # Ice HUD
        self.hud_frame = self.canvas.create_rectangle(
            10, 10, 180, 40,
            outline="#88ddff", fill="#000020", width=1
        )
        self.score_text = self.canvas.create_text(
            25, 25, text=f"❄️ SCORE: {self.score}",
            fill="#88ddff", font=("Courier", 16, "bold"), anchor="w"
        )
        self.temp_text = self.canvas.create_text(
            WIDTH//2, 55,
            text="🌨️ -20°C  |  ANTARCTIC SECTOR 🌨️", fill="#88ddff",
            font=("Courier", 10)
        )

    def _update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"❄️ SCORE: {self.score}")
        self._redraw_hearts()

    def _show_start_screen(self):
        self.start_items = []
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 80,
            text="❄️ ANTARCTIC ARKANOID ❄️", fill="#88ddff",
            font=("Courier", 40, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 20,
            text="▶ PRESS SPACE TO START ◀", fill="#ffffff",
            font=("Courier", 22, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 30,
            text="← →  MOVE ICE PADDLE", fill="#88ddff",
            font=("Courier", 16)
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 60,
            text="🐧 BREAK ALL ICE CUBES 🐧", fill="#ffffff",
            font=("Courier", 14, "bold")
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
            self._move_ball()
            self._check_collisions()
        
        self.root.after(1000 // FPS, self._game_loop)

    def _move_paddle(self):
        coords = self.canvas.coords(self.paddle)
        if self.paddle_speed < 0 and coords[0] > 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
            self.canvas.move(self.paddle_shine, self.paddle_speed, 0)
        elif self.paddle_speed > 0 and coords[2] < WIDTH - 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
            self.canvas.move(self.paddle_shine, self.paddle_speed, 0)

    def _move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        self.canvas.move(self.ball_core, self.ball_dx, self.ball_dy)
        self.canvas.move(self.ball_sparkle, self.ball_dx, self.ball_dy)

    def _check_collisions(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        bcx = (bx1 + bx2) / 2

        # Wall collisions
        if bx1 <= 0:
            self.ball_dx = abs(self.ball_dx)
            self._create_ice_explosion(bcx, by1, 10)
        if bx2 >= WIDTH:
            self.ball_dx = -abs(self.ball_dx)
            self._create_ice_explosion(bcx, by1, 10)
        if by1 <= 0:
            self.ball_dy = abs(self.ball_dy)
            self._create_ice_explosion(bcx, by1, 10)

        # Bottom — lose life
        if by2 >= HEIGHT:
            self._create_ice_explosion(bcx, HEIGHT-20, 20)
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
            self._sync_ball_parts(bx1, py1 - BALL_R * 2, bx2, py1)

        # Brick collision
        for brick in self.bricks[:]:
            brx1, bry1, brx2, bry2 = self.canvas.coords(brick["id"])
            if (bx2 >= brx1 and bx1 <= brx2 and
                    by2 >= bry1 and by1 <= bry2):
                self.score += brick["points"]
                self._create_ice_explosion((brx1+brx2)/2, (bry1+bry2)/2, 20)
                for part in brick.get("parts", [brick["id"]]):
                    self.canvas.delete(part)
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

    def _sync_ball_parts(self, bx1, by1, bx2, by2):
        cx = (bx1 + bx2) / 2
        cy = (by1 + by2) / 2
        self.canvas.coords(
            self.ball_core,
            cx - BALL_R//2, cy - BALL_R//2,
            cx + BALL_R//2, cy + BALL_R//2
        )
        self.canvas.coords(
            self.ball_sparkle,
            cx - 1, cy - BALL_R//2,
            cx + 1, cy - BALL_R//2 + 3
        )

    def _create_ice_explosion(self, cx, cy, size):
        """Create ice particle explosion."""
        particles = []
        for _ in range(15):
            angle = random.uniform(0, 2*math.pi)
            distance = random.uniform(3, size)
            dx = distance * math.cos(angle)
            dy = distance * math.sin(angle)
            size_p = random.randint(2, 5)
            color = random.choice(["#ffffff", "#d4eaf7", "#bde6fb", "#88ddff", "#cfefff"])
            particle = self.canvas.create_oval(
                cx + dx - size_p, cy + dy - size_p,
                cx + dx + size_p, cy + dy + size_p,
                fill=color, outline=""
            )
            particles.append({
                "id": particle,
                "dx": dx / 8,
                "dy": dy / 8,
                "life": 20
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

    def _reset_ball(self):
        self.canvas.coords(
            self.ball,
            WIDTH // 2 - BALL_R, HEIGHT - 60 - BALL_R,
            WIDTH // 2 + BALL_R, HEIGHT - 60 + BALL_R
        )
        self._sync_ball_parts(
            WIDTH // 2 - BALL_R, HEIGHT - 60 - BALL_R,
            WIDTH // 2 + BALL_R, HEIGHT - 60 + BALL_R
        )
        self.ball_dx = 4 * random.choice([-1, 1])
        self.ball_dy = -4
        self.game_started = False
        msg = self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text="❄️ REBOOTING... PRESS SPACE ❄️", fill="#88ddff",
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
            text="❄️ GAME OVER ❄️", fill="#ff0044",
            font=("Courier", 32, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text=f"FINAL SCORE: {self.score}", fill="#ffffff",
            font=("Courier", 22, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 55,
            text="🐧 THE PENGUINS ARE SAD 🐧", fill="#88ddff",
            font=("Courier", 14)
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
            text="🌟 YOU SAVED THE ICE! 🌟", fill="#00ff66",
            font=("Courier", 32, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text=f"FINAL SCORE: {self.score}", fill="#ffffff",
            font=("Courier", 22, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 55,
            text="🐧 THE PENGUINS ARE HAPPY! 🐧", fill="#88ddff",
            font=("Courier", 14, "bold")
        )

if __name__ == "__main__":
    Arkanoid()