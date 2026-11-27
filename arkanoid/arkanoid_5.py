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

BRICK_COLORS = ["#ff0066", "#ff6600", "#ffcc00", "#00ff66", "#0066ff"]
BRICK_POINTS = [50, 40, 30, 20, 10]

class Arkanoid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Space Arkanoid")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#000008")
        self.canvas.pack()

        self._draw_space_background()
        self._create_twinkling_stars()
        self._create_asteroids()
        
        self.score = 0
        self.lives = 3
        self.game_started = False
        self.game_over = False
        self.frame_count = 0

        # Ball speed
        self.ball_dx = 5
        self.ball_dy = -5

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
        self.root.bind("<KeyPress-Left>", lambda e: self._set_paddle_speed(-9))
        self.root.bind("<KeyRelease-Left>", lambda e: self._stop_paddle("left"))
        self.root.bind("<KeyPress-Right>", lambda e: self._set_paddle_speed(9))
        self.root.bind("<KeyRelease-Right>", lambda e: self._stop_paddle("right"))
        self.root.bind("<space>", self._start_game)

        self._game_loop()
        self.root.mainloop()

    # ─── Space Background ───

    def _draw_space_background(self):
        """Draw deep space background with nebulae and galaxies."""
        # Deep space gradient
        for i in range(100):
            y = i * HEIGHT // 100
            color_val = int(8 + (i * 0.15))
            color = f"#{color_val:02x}{color_val:02x}{18:02x}"
            self.canvas.create_line(0, y, WIDTH, y, fill=color)
        
        # Nebula glows
        nebulae = [
            (200, 150, 300, 200, "#1a0533", "#2d1b69"),
            (600, 400, 250, 180, "#0a1628", "#1a3a5c"),
            (400, 300, 400, 300, "#1a0a1a", "#3d1a3d"),
        ]
        for x, y, w, h, color1, color2 in nebulae:
            for i in range(30):
                angle = random.uniform(0, 2*math.pi)
                radius = random.uniform(0, max(w,h)//2)
                px = x + radius * math.cos(angle)
                py = y + radius * math.sin(angle)
                size = random.randint(20, 80)
                self.canvas.create_oval(px-size//2, py-size//2, px+size//2, py+size//2,
                                       fill=color1, outline="", stipple="gray50")
        
        # Milky Way band
        for i in range(150):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            if abs(y - 300) < 100 + 50 * math.sin(x/200):
                size = random.choice([1, 1, 2, 2, 3])
                colors = ["#ffffff", "#e0e7ff", "#c7d2fe", "#a5b4fc", "#818cf8"]
                self.canvas.create_oval(x, y, x+size, y+size, 
                                       fill=random.choice(colors), outline="")
        
        # Distant galaxies
        for _ in range(5):
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, HEIGHT-50)
            self._draw_galaxy(x, y, random.randint(30, 70))
        
        # Large planets
        planets = [
            (650, 80, 50, "#f59e0b", "#fbbf24", True),  # Gas giant
            (100, 500, 35, "#0ea5e9", "#38bdf8", False),  # Water world
            (750, 450, 25, "#dc2626", "#ef4444", False),  # Red planet
            (50, 150, 20, "#9ca3af", "#d1d5db", False),  # Rocky planet
        ]
        for x, y, r, color, outline, has_ring in planets:
            # Planet body
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=outline, width=2)
            # Atmosphere glow
            self.canvas.create_oval(x-r*1.3, y-r*1.3, x+r*1.3, y+r*1.3, 
                                   outline=outline, width=1, stipple="gray50")
            if has_ring:
                self.canvas.create_oval(x-r*2.2, y-r*0.6, x+r*2.2, y+r*0.6,
                                       outline="#fde68a", width=2, stipple="gray25")
                # Ring glow
                self.canvas.create_oval(x-r*2.4, y-r*0.8, x+r*2.4, y+r*0.8,
                                       outline="#fef08a", width=1, stipple="gray75")
            # Surface details
            for _ in range(random.randint(5, 15)):
                sx = x + random.randint(-r//2, r//2)
                sy = y + random.randint(-r//2, r//2)
                if (sx-x)**2 + (sy-y)**2 < r**2:
                    self.canvas.create_oval(sx-2, sy-2, sx+2, sy+2, 
                                          fill=outline, outline="", stipple="gray50")

    def _draw_galaxy(self, cx, cy, size):
        """Draw a spiral galaxy."""
        for i in range(50):
            angle = random.uniform(0, 2*math.pi)
            radius = random.uniform(0, size) * random.uniform(0.3, 1)
            x = cx + radius * math.cos(angle + radius/10)
            y = cy + radius * math.sin(angle + radius/10)
            size2 = random.randint(1, 3)
            colors = ["#ffffff", "#fde68a", "#fcd34d", "#fbbf24"]
            self.canvas.create_oval(x, y, x+size2, y+size2, 
                                   fill=random.choice(colors), outline="")

    def _create_twinkling_stars(self):
        """Create animated twinkling stars."""
        self.twinkling_stars = []
        for _ in range(60):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.choice([1, 1, 2, 2, 3])
            brightness = random.randint(100, 255)
            star = self.canvas.create_oval(x, y, x+size, y+size,
                                          fill=f"#{brightness:02x}{brightness:02x}{brightness:02x}",
                                          outline="")
            self.twinkling_stars.append({
                "id": star,
                "x": x,
                "y": y,
                "size": size,
                "phase": random.uniform(0, 2*math.pi),
                "speed": random.uniform(0.02, 0.08)
            })

    def _create_asteroids(self):
        """Create floating asteroids."""
        self.asteroids = []
        for _ in range(8):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(5, 12)
            points = []
            num_points = random.randint(6, 10)
            for i in range(num_points):
                angle = 2*math.pi * i / num_points
                r = size * random.uniform(0.6, 1.4)
                points.append(x + r * math.cos(angle))
                points.append(y + r * math.sin(angle))
            asteroid = self.canvas.create_polygon(points, fill="#4a4a4a", outline="#6a6a6a", width=1)
            self.asteroids.append({
                "id": asteroid,
                "x": x,
                "y": y,
                "dx": random.uniform(-0.3, 0.3),
                "dy": random.uniform(-0.3, 0.3),
                "points": points,
                "angle": random.uniform(0, 2*math.pi),
                "rot_speed": random.uniform(-0.02, 0.02),
                "size": size,
                "num_points": num_points
            })

    def _animate_space(self):
        """Animate space background elements."""
        self.frame_count += 1
        
        # Twinkling stars
        for star in self.twinkling_stars:
            brightness = 100 + 155 * (0.5 + 0.5 * math.sin(self.frame_count * star["speed"] + star["phase"]))
            self.canvas.itemconfig(star["id"], fill=f"#{int(brightness):02x}{int(brightness):02x}{int(brightness):02x}")
        
        # Floating asteroids with rotation
        for ast in self.asteroids:
            # Move asteroid
            self.canvas.move(ast["id"], ast["dx"], ast["dy"])
            ast["x"] += ast["dx"]
            ast["y"] += ast["dy"]
            
            # Wrap around screen
            if ast["x"] < -20:
                ast["x"] += WIDTH + 40
                self.canvas.move(ast["id"], WIDTH + 40, 0)
            elif ast["x"] > WIDTH + 20:
                ast["x"] -= WIDTH + 40
                self.canvas.move(ast["id"], -(WIDTH + 40), 0)
            if ast["y"] < -20:
                ast["y"] += HEIGHT + 40
                self.canvas.move(ast["id"], 0, HEIGHT + 40)
            elif ast["y"] > HEIGHT + 20:
                ast["y"] -= HEIGHT + 40
                self.canvas.move(ast["id"], 0, -(HEIGHT + 40))
            
            # Rotate asteroid (update polygon points)
            ast["angle"] += ast["rot_speed"]
            new_points = []
            for i in range(ast["num_points"]):
                angle = 2*math.pi * i / ast["num_points"] + ast["angle"]
                r = ast["size"] * (0.6 + 0.8 * (0.5 + 0.5 * math.sin(i * 1.7 + ast["angle"] * 2)))
                new_points.append(ast["x"] + r * math.cos(angle))
                new_points.append(ast["y"] + r * math.sin(angle))
            self.canvas.coords(ast["id"], *new_points)

    # ─── Create objects ───

    def _create_paddle(self):
        x = WIDTH // 2
        y = HEIGHT - 40
        # Space cruiser paddle
        self.paddle = self.canvas.create_rectangle(
            x - PADDLE_W // 2, y,
            x + PADDLE_W // 2, y + PADDLE_H,
            fill="#00d4ff", outline="#00d4ff", width=0
        )
        # Glow
        self.paddle_glow = self.canvas.create_rectangle(
            x - PADDLE_W // 2 - 5, y - 5,
            x + PADDLE_W // 2 + 5, y + PADDLE_H + 5,
            outline="#00d4ff", width=2, stipple="gray50"
        )
        # Core
        self.paddle_core = self.canvas.create_rectangle(
            x - 20, y + 3,
            x + 20, y + PADDLE_H - 3,
            fill="#ffffff", outline="#ffffff", width=0
        )
        # Engine glow
        self.paddle_engine = self.canvas.create_rectangle(
            x - 15, y - 8,
            x + 15, y - 3,
            fill="#00d4ff", outline="", stipple="gray25"
        )

    def _create_ball(self):
        x = WIDTH // 2
        y = HEIGHT - 60
        # Invisible hitbox
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R,
            x + BALL_R, y + BALL_R,
            fill="", outline=""
        )
        # Spaceship sprite
        self.ball_sprite = self.canvas.create_polygon(
            x, y - 14,
            x - 10, y + 6,
            x - 6, y + 2,
            x - 4, y + 10,
            x, y + 14,
            x + 4, y + 10,
            x + 6, y + 2,
            x + 10, y + 6,
            fill="#60a5fa", outline="#93c5fd", width=2
        )
        # Cockpit
        self.ball_cockpit = self.canvas.create_oval(
            x - 3, y - 8,
            x + 3, y - 2,
            fill="#1e3a8a", outline="#93c5fd", width=1
        )
        # Engine flame
        self.ball_flame = self.canvas.create_polygon(
            x - 3, y + 8,
            x, y + 18,
            x + 3, y + 8,
            fill="#f97316", outline="#fb923c", width=1
        )
        # Flame glow
        self.ball_flame_glow = self.canvas.create_polygon(
            x - 5, y + 10,
            x, y + 22,
            x + 5, y + 10,
            fill="#fbbf24", outline="", stipple="gray50"
        )
        # Wing lights
        self.wing_lights = []
        for dx in [-8, 8]:
            light = self.canvas.create_oval(
                x + dx - 2, y - 2,
                x + dx + 2, y + 2,
                fill="#ff0066", outline="#ff0066"
            )
            self.wing_lights.append(light)

    def _sync_ball_sprite(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        cx = (bx1 + bx2) / 2
        cy = (by1 + by2) / 2
        
        # Ship body
        self.canvas.coords(
            self.ball_sprite,
            cx, cy - 14,
            cx - 10, cy + 6,
            cx - 6, cy + 2,
            cx - 4, cy + 10,
            cx, cy + 14,
            cx + 4, cy + 10,
            cx + 6, cy + 2,
            cx + 10, cy + 6
        )
        # Cockpit
        self.canvas.coords(
            self.ball_cockpit,
            cx - 3, cy - 8,
            cx + 3, cy - 2
        )
        # Flame (pulsing)
        flame_size = 16 + 4 * math.sin(self.frame_count * 0.3)
        self.canvas.coords(
            self.ball_flame,
            cx - 3, cy + 8,
            cx, cy + flame_size,
            cx + 3, cy + 8
        )
        self.canvas.coords(
            self.ball_flame_glow,
            cx - 5, cy + 10,
            cx, cy + flame_size + 4,
            cx + 5, cy + 10
        )
        # Wing lights (blinking)
        for i, light in enumerate(self.wing_lights):
            dx = -8 if i == 0 else 8
            self.canvas.coords(
                light,
                cx + dx - 2, cy - 2,
                cx + dx + 2, cy + 2
            )
            # Blink
            if self.frame_count % 30 < 15:
                self.canvas.itemconfig(light, fill="#ff0066", outline="#ff0066")
            else:
                self.canvas.itemconfig(light, fill="#ff0000", outline="#ff0000")

    def _create_bricks(self):
        self.bricks = []
        planet_colors = [
            {"fill": "#f59e0b", "outline": "#fbbf24", "stripe": "#fde68a", "ring": None},
            {"fill": "#eab308", "outline": "#facc15", "stripe": None, "ring": "#fef08a"},
            {"fill": "#38bdf8", "outline": "#7dd3fc", "stripe": None, "ring": None},
            {"fill": "#22d3ee", "outline": "#67e8f9", "stripe": "#a5f3fc", "ring": None},
            {"fill": "#f97316", "outline": "#fb923c", "stripe": None, "ring": None},
        ]
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        for row in range(BRICK_ROWS):
            points = BRICK_POINTS[row]
            colors = planet_colors[row % len(planet_colors)]
            for col in range(BRICK_COLS):
                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                r = BRICK_H * 0.4
                
                # Planet body
                body = self.canvas.create_oval(
                    cx - r, cy - r,
                    cx + r, cy + r,
                    fill=colors["fill"], outline=colors["outline"], width=2
                )
                extras = []
                
                # Stripe
                if colors["stripe"]:
                    stripe = self.canvas.create_oval(
                        cx - r*0.85, cy - r*0.25,
                        cx + r*0.85, cy + r*0.25,
                        fill=colors["stripe"], outline=""
                    )
                    extras.append(stripe)
                
                # Ring
                if colors["ring"]:
                    ring = self.canvas.create_oval(
                        cx - r*1.5, cy - r*0.5,
                        cx + r*1.5, cy + r*0.5,
                        outline=colors["ring"], width=2
                    )
                    self.canvas.tag_lower(ring, body)
                    extras.append(ring)
                
                # Star shine
                shine = self.canvas.create_oval(
                    cx - r*0.6, cy - r*0.6,
                    cx + r*0.4, cy + r*0.2,
                    fill="white", outline="", stipple="gray25"
                )
                extras.append(shine)
                
                self.bricks.append({
                    "id": body,
                    "extra_ids": extras,
                    "points": points,
                    "bbox": (x1, y1, x2, y2)
                })

    def _draw_heart(self, cx, cy, size=14):
        points = []
        for i in range(100):
            t = 2 * math.pi * i / 100
            x = size * 16 * (math.sin(t) ** 3) / 16
            y = -size * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)) / 16
            points.append(cx + x)
            points.append(cy + y)
        return self.canvas.create_polygon(points, fill="#ff0044", outline="#ff0044", width=1, smooth=True)

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
        # Space HUD
        self.hud_frame = self.canvas.create_rectangle(
            10, 10, 200, 40,
            outline="#00d4ff", fill="#000020", width=1
        )
        self.score_text = self.canvas.create_text(
            25, 25, text=f"SCORE: {self.score}",
            fill="#00d4ff", font=("Courier", 16, "bold"), anchor="w"
        )
        self.star_text = self.canvas.create_text(
            WIDTH//2, 55,
            text="✦ SPACE SECTOR 7 ✦", fill="#8888ff",
            font=("Courier", 10)
        )

    def _update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"SCORE: {self.score}")
        self._redraw_hearts()

    def _show_start_screen(self):
        self.start_items = []
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 80,
            text="🚀 SPACE ARKANOID 🚀", fill="#00d4ff",
            font=("Courier", 40, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 20,
            text="▶ PRESS SPACE TO LAUNCH ◀", fill="#ffffff",
            font=("Courier", 22, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 30,
            text="← →  MOVE SPACE CRUISER", fill="#8888ff",
            font=("Courier", 16)
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 60,
            text="✦ DESTROY ALL PLANETS ✦", fill="#fcd34d",
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
        self._animate_space()
        
        if self.game_started and not self.game_over:
            self._move_paddle()
            self._move_ball()
            self._check_collisions()
        
        self.root.after(1000 // FPS, self._game_loop)

    def _move_paddle(self):
        coords = self.canvas.coords(self.paddle)
        if self.paddle_speed < 0 and coords[0] > 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
            self.canvas.move(self.paddle_glow, self.paddle_speed, 0)
            self.canvas.move(self.paddle_core, self.paddle_speed, 0)
            self.canvas.move(self.paddle_engine, self.paddle_speed, 0)
        elif self.paddle_speed > 0 and coords[2] < WIDTH - 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
            self.canvas.move(self.paddle_glow, self.paddle_speed, 0)
            self.canvas.move(self.paddle_core, self.paddle_speed, 0)
            self.canvas.move(self.paddle_engine, self.paddle_speed, 0)

    def _move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        self._sync_ball_sprite()

    def _check_collisions(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        bcx = (bx1 + bx2) / 2

        # Wall collisions
        if bx1 <= 0:
            self.ball_dx = abs(self.ball_dx)
            self._create_explosion(bcx, by1, 8)
        if bx2 >= WIDTH:
            self.ball_dx = -abs(self.ball_dx)
            self._create_explosion(bcx, by1, 8)
        if by1 <= 0:
            self.ball_dy = abs(self.ball_dy)
            self._create_explosion(bcx, by1, 8)

        # Bottom — lose life
        if by2 >= HEIGHT:
            self._create_explosion(bcx, HEIGHT-20, 30)
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
            speed = min(max(speed, 5), 9)
            self.ball_dx = speed * math.cos(angle) * (1 if hit_pos >= 0 else -1)
            self.ball_dy = -abs(speed * math.sin(angle))
            self.canvas.coords(self.ball, bx1, py1 - BALL_R * 2, bx2, py1)
            self._sync_ball_sprite()
            self._create_explosion(bcx, py1, 15)

        # Brick collision
        for brick in self.bricks[:]:
            brx1, bry1, brx2, bry2 = brick["bbox"]
            if (bx2 >= brx1 and bx1 <= brx2 and
                    by2 >= bry1 and by1 <= bry2):
                self.score += brick["points"]
                # Create explosion at planet
                self._create_explosion((brx1+brx2)/2, (bry1+bry2)/2, 25)
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
        """Create a particle explosion effect."""
        particles = []
        for _ in range(20):
            angle = random.uniform(0, 2*math.pi)
            distance = random.uniform(3, size)
            dx = distance * math.cos(angle)
            dy = distance * math.sin(angle)
            size_p = random.randint(2, 5)
            color = random.choice(["#f97316", "#fb923c", "#fbbf24", "#fcd34d", "#ffffff", "#ff0066"])
            particle = self.canvas.create_oval(
                cx + dx - size_p, cy + dy - size_p,
                cx + dx + size_p, cy + dy + size_p,
                fill=color, outline=""
            )
            particles.append({
                "id": particle,
                "dx": dx / 10,
                "dy": dy / 10,
                "life": 30
            })
        
        # Animate particles
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
        self._sync_ball_sprite()
        self.ball_dx = 5 * random.choice([-1, 1])
        self.ball_dy = -5
        self.game_started = False
        msg = self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text="🔄 REBOOTING... PRESS SPACE", fill="#00d4ff",
            font=("Courier", 18, "bold")
        )
        self.start_items = [msg]

    def _game_over_screen(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        # Space-style game over
        self.canvas.create_rectangle(
            WIDTH // 2 - 300, HEIGHT // 2 - 100,
            WIDTH // 2 + 300, HEIGHT // 2 + 100,
            fill="#000020", outline="#ff0044", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 40,
            text="💥 MISSION FAILED 💥", fill="#ff0044",
            font=("Courier", 28, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text=f"FINAL SCORE: {self.score}", fill="#ffffff",
            font=("Courier", 22, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 50,
            text="✦ GAME OVER ✦", fill="#8888ff",
            font=("Courier", 16)
        )

    def _game_win(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self.canvas.create_rectangle(
            WIDTH // 2 - 300, HEIGHT // 2 - 100,
            WIDTH // 2 + 300, HEIGHT // 2 + 100,
            fill="#000020", outline="#00ff66", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 40,
            text="🌟 MISSION ACCOMPLISHED 🌟", fill="#00ff66",
            font=("Courier", 28, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text=f"FINAL SCORE: {self.score}", fill="#ffffff",
            font=("Courier", 22, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 50,
            text="✦ YOU SAVED THE GALAXY! ✦", fill="#00d4ff",
            font=("Courier", 16, "bold")
        )

if __name__ == "__main__":
    Arkanoid()