import tkinter as tk
import random
import math

# ─── Constants ───
WIDTH = 800
HEIGHT = 600
PADDLE_W = 100
PADDLE_H = 15
BALL_R = 10
BRICK_ROWS = 5
BRICK_COLS = 10
BRICK_W = 70
BRICK_H = 25
BRICK_PAD = 4
TOP_OFFSET = 60
FPS = 60

BRICK_COLORS = ["#ff6b35", "#ffd23f", "#4ecdc4", "#45b7d1", "#96ceb4"]
BRICK_POINTS = [50, 40, 30, 20, 10]

class Arkanoid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🦕 Dino Arkanoid 🦕")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#2d5a27")
        self.canvas.pack()

        self._draw_jungle_background()
        self._create_trees()
        self._create_dino_herd()
        
        self.score = 0
        self.lives = 3
        self.game_started = False
        self.game_over = False
        self.frame_count = 0

        # Ball speed
        self.ball_dx = 4
        self.ball_dy = -4

        # Paddle speed
        self.paddle_speed = 0

        # Effects
        self.particles = []

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

    # ─── Jungle Background ───

    def _draw_jungle_background(self):
        # Sky gradient
        for i in range(0, 150, 5):
            y = i * HEIGHT // 150
            color_val = int(80 + (i * 0.5))
            green_val = int(160 + (i * 0.3))
            blue_val = int(80 + (i * 0.2))
            color = f"#{color_val:02x}{green_val:02x}{blue_val:02x}"
            self.canvas.create_line(0, y, WIDTH, y, fill=color)
        
        # Sun
        self.canvas.create_oval(WIDTH-120, 20, WIDTH-30, 110, fill="#ffd23f", outline="#fbbf24", width=3)
        
        # Mountains
        mountains = [
            (0, 350, 100, 280, 200, 340, 300, 290, 400, 350),
            (300, 340, 400, 270, 500, 330, 600, 280, 700, 350),
            (500, 350, 600, 290, 700, 340, 800, 310)
        ]
        for m in mountains:
            self.canvas.create_polygon(m, fill="#3d7a3a", outline="#2d5a27", width=1)
        
        # Ground
        self.canvas.create_rectangle(0, HEIGHT-40, WIDTH, HEIGHT, fill="#2d5a27", outline="")
        self.canvas.create_rectangle(0, HEIGHT-20, WIDTH, HEIGHT, fill="#1f4a1a", outline="")

    def _create_trees(self):
        """Create palm trees."""
        tree_positions = [(30, 320, 0.8), (750, 330, 0.7), (100, 350, 0.6), (680, 350, 0.9)]
        for x, y, scale in tree_positions:
            # Trunk
            self.canvas.create_line(x, y, x-10, y-80*scale, fill="#8B7355", width=6*scale)
            # Leaves
            for angle in [-60, -30, 0, 30, 60]:
                rad = math.radians(angle)
                x1 = x - 10 + 15*scale * math.cos(rad)
                y1 = y - 80*scale + 15*scale * math.sin(rad)
                x2 = x - 10 + 50*scale * math.cos(rad + 0.5)
                y2 = y - 80*scale + 25*scale * math.sin(rad + 0.5)
                self.canvas.create_line(x1, y1, x2, y2, fill="#22c55e", width=4*scale)

    def _create_dino_herd(self):
        """Create a herd of walking dinosaurs at the bottom."""
        self.dinos = []
        dino_colors = ["#4CAF50", "#66BB6A", "#81C784", "#43A047", "#388E3C", "#2E7D32"]
        
        # Create 7 dinosaurs in different positions
        for i in range(7):
            x = 50 + i * 105
            y = HEIGHT - 35 - random.randint(-10, 10)
            color = random.choice(dino_colors)
            size = random.uniform(0.7, 1.2)
            
            dino_parts = self._create_single_dino(x, y, color, size)
            self.dinos.append({
                "parts": dino_parts,
                "x": x,
                "y": y,
                "direction": random.choice([-1, 1]),
                "speed": random.uniform(0.3, 0.8),
                "walk_frame": random.randint(0, 100),
                "size": size,
                "color": color
            })

    def _create_single_dino(self, x, y, color, size=1.0):
        """Create a single dinosaur and return its parts."""
        parts = []
        
        # Body
        body = self.canvas.create_oval(
            x - 20*size, y - 15*size, 
            x + 20*size, y + 5*size, 
            fill=color, outline="#2d7a2a", width=2
        )
        parts.append(body)
        
        # Head
        head = self.canvas.create_oval(
            x + 12*size, y - 18*size, 
            x + 28*size, y - 2*size, 
            fill=color, outline="#2d7a2a", width=2
        )
        parts.append(head)
        
        # Eye
        eye = self.canvas.create_oval(
            x + 18*size, y - 13*size, 
            x + 22*size, y - 9*size, 
            fill="white", outline=""
        )
        parts.append(eye)
        pupil = self.canvas.create_oval(
            x + 19*size, y - 12*size, 
            x + 21*size, y - 10*size, 
            fill="black", outline=""
        )
        parts.append(pupil)
        
        # Legs
        for lx in [-10*size, 10*size]:
            leg = self.canvas.create_rectangle(
                x+lx-3*size, y+3*size, 
                x+lx+3*size, y+12*size, 
                fill=color, outline="#2d7a2a", width=1
            )
            parts.append(leg)
        
        # Tail
        tail = self.canvas.create_polygon(
            x-20*size, y-2*size,
            x-32*size, y-8*size,
            x-28*size, y+2*size,
            fill=color, outline="#2d7a2a", width=1
        )
        parts.append(tail)
        
        # Spikes on back
        for i in range(3):
            sx = x - 12*size + i*10*size
            sy = y - 15*size
            spike = self.canvas.create_polygon(
                sx, sy,
                sx+3*size, sy-8*size,
                sx+6*size, sy,
                fill="#22c55e", outline="#16a34a"
            )
            parts.append(spike)
        
        return parts

    def _animate_dino_herd(self):
        """Animate all dinosaurs in the herd."""
        self.frame_count += 1
        
        for dino in self.dinos:
            # Move
            if self.frame_count % 2 == 0:  # Move every other frame
                dino["x"] += dino["direction"] * dino["speed"]
            
            # Change direction at edges
            if dino["x"] > WIDTH - 60:
                dino["direction"] = -1
                # Flip the dino (simplified - just move other way)
            elif dino["x"] < 40:
                dino["direction"] = 1
            
            # Bob up and down
            bob = math.sin(self.frame_count * 0.08 + dino["walk_frame"]) * 2
            
            # Update position
            current_x = dino["x"]
            current_y = HEIGHT - 35 + bob
            
            # Move all parts
            dx = dino["direction"] * dino["speed"]
            if self.frame_count % 2 == 0:
                for part in dino["parts"]:
                    self.canvas.move(part, dx, 0)
            
            # Update walk frame
            dino["walk_frame"] += 0.5

    # ─── Create objects ───

    def _create_paddle(self):
        x = WIDTH // 2
        y = HEIGHT - 40
        # Log paddle
        self.paddle = self.canvas.create_rectangle(
            x - PADDLE_W // 2, y,
            x + PADDLE_W // 2, y + PADDLE_H,
            fill="#8B7355", outline="#654321", width=2
        )
        self.paddle_grain = self.canvas.create_line(
            x - 30, y + 7, x + 30, y + 7,
            fill="#654321", width=1
        )
        # Dino family on paddle
        self.paddle_dinos = self.canvas.create_text(
            x, y + 8,
            text="🦕🦕🦕", font=("Arial", 10)
        )

    def _create_ball(self):
        x = WIDTH // 2
        y = HEIGHT - 60
        # Dino egg ball
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R,
            x + BALL_R, y + BALL_R,
            fill="#8B4513", outline="#654321", width=2
        )
        self.ball_inner = self.canvas.create_oval(
            x - BALL_R//2, y - BALL_R//2,
            x + BALL_R//2, y + BALL_R//2,
            fill="#4CAF50", outline=""
        )
        self.ball_dino = self.canvas.create_text(
            x, y,
            text="🦕", font=("Arial", 8)
        )

    def _create_bricks(self):
        self.bricks = []
        egg_colors = [
            ("#ff6b35", "#e55a2b"),
            ("#ffd23f", "#e5b82b"),
            ("#4ecdc4", "#3ab8b0"),
            ("#45b7d1", "#359fc9"),
            ("#96ceb4", "#7ab89a"),
        ]
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        for row in range(BRICK_ROWS):
            points = BRICK_POINTS[row]
            color1, color2 = egg_colors[row % len(egg_colors)]
            for col in range(BRICK_COLS):
                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                size = BRICK_H * 0.35
                
                # Egg
                egg = self.canvas.create_oval(
                    cx - size, cy - size*1.2,
                    cx + size, cy + size*0.8,
                    fill=color1, outline=color2, width=2
                )
                # Spot
                spot = self.canvas.create_oval(
                    cx - size*0.3, cy - size*0.3,
                    cx + size*0.3, cy + size*0.1,
                    fill=color2, outline=""
                )
                # Dino emoji
                dino = self.canvas.create_text(
                    cx, cy,
                    text="🦕", font=("Arial", 14)
                )
                
                self.bricks.append({
                    "id": egg,
                    "parts": [egg, spot, dino],
                    "points": points,
                })

    def _draw_heart(self, cx, cy, size=14):
        points = []
        for i in range(100):
            t = 2 * math.pi * i / 100
            x = size * 16 * (math.sin(t) ** 3) / 16
            y = -size * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)) / 16
            points.append(cx + x)
            points.append(cy + y)
        return self.canvas.create_polygon(points, fill="#ef4444", outline="#dc2626", width=1, smooth=True)

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
            15, 20, text=f"🦕 Score: {self.score}",
            fill="#4ade80", font=("Courier", 16, "bold"), anchor="w"
        )
        self.title_text = self.canvas.create_text(
            WIDTH//2, 45,
            text="🌴 Jurassic Jungle 🌴", fill="#4ade80",
            font=("Courier", 12, "bold")
        )

    def _update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"🦕 Score: {self.score}")
        self._redraw_hearts()

    def _show_start_screen(self):
        self.start_items = []
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 90,
            text="🦕 DINO ARKANOID 🦕", fill="#4ade80",
            font=("Courier", 40, "bold")
        ))
        # Dino herd on start screen
        for i in range(5):
            x = WIDTH//2 - 160 + i*80
            self.start_items.append(self.canvas.create_text(
                x, HEIGHT//2 - 30,
                text="🦕", font=("Arial", random.randint(24, 36))
            ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text="▶  PRESS SPACE TO START  ◀", fill="#ffffff",
            font=("Courier", 20, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 60,
            text="← →  MOVE LOG PADDLE", fill="#4ade80",
            font=("Courier", 16)
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 90,
            text="🥚 HATCH ALL THE EGGS! 🥚", fill="#ffd23f",
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
        if not self.game_over:
            self._animate_dino_herd()
        
        if self.game_started and not self.game_over:
            self._move_paddle()
            self._move_ball()
            self._check_collisions()
            self._update_particles()
        
        self.root.after(1000 // FPS, self._game_loop)

    def _move_paddle(self):
        coords = self.canvas.coords(self.paddle)
        if self.paddle_speed < 0 and coords[0] > 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
            self.canvas.move(self.paddle_grain, self.paddle_speed, 0)
            self.canvas.move(self.paddle_dinos, self.paddle_speed, 0)
        elif self.paddle_speed > 0 and coords[2] < WIDTH - 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
            self.canvas.move(self.paddle_grain, self.paddle_speed, 0)
            self.canvas.move(self.paddle_dinos, self.paddle_speed, 0)

    def _move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        self.canvas.move(self.ball_inner, self.ball_dx, self.ball_dy)
        self.canvas.move(self.ball_dino, self.ball_dx, self.ball_dy)

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
            self._sync_ball_parts(bx1, py1 - BALL_R * 2, bx2, py1)

        # Brick collision
        for brick in self.bricks[:]:
            brx1, bry1, brx2, bry2 = self.canvas.coords(brick["id"])
            if (bx2 >= brx1 and bx1 <= brx2 and
                    by2 >= bry1 and by1 <= bry2):
                self.score += brick["points"]
                self._create_explosion((brx1+brx2)/2, (bry1+bry2)/2)
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

    def _create_explosion(self, cx, cy):
        """Create explosion with many dino emojis."""
        # Dino emoji explosion
        for _ in range(6):
            angle = random.uniform(0, 2*math.pi)
            distance = random.uniform(10, 40)
            dx = distance * math.cos(angle)
            dy = distance * math.sin(angle)
            dino = self.canvas.create_text(
                cx + dx, cy + dy,
                text="🦕", font=("Arial", random.randint(12, 22))
            )
            self.particles.append({
                "id": dino,
                "dx": dx / 10,
                "dy": dy / 10 - 0.5,
                "life": 20
            })
        
        # Colorful particles
        colors = ["#4ade80", "#22c55e", "#ffd23f", "#ff6b35", "#f97316", "#4ecdc4"]
        for _ in range(8):
            angle = random.uniform(0, 2*math.pi)
            distance = random.uniform(3, 15)
            dx = distance * math.cos(angle)
            dy = distance * math.sin(angle)
            size_p = random.randint(2, 5)
            color_p = random.choice(colors)
            particle = self.canvas.create_oval(
                cx + dx - size_p, cy + dy - size_p,
                cx + dx + size_p, cy + dy + size_p,
                fill=color_p, outline=""
            )
            self.particles.append({
                "id": particle,
                "dx": dx / 6,
                "dy": dy / 6 - 0.3,
                "life": 15
            })

    def _update_particles(self):
        dead = []
        for p in self.particles:
            self.canvas.move(p["id"], p["dx"], p["dy"])
            p["dy"] += 0.1
            p["life"] -= 1
            if p["life"] <= 0:
                self.canvas.delete(p["id"])
                dead.append(p)
        for p in dead:
            self.particles.remove(p)

    def _sync_ball_parts(self, bx1, by1, bx2, by2):
        cx = (bx1 + bx2) / 2
        cy = (by1 + by2) / 2
        self.canvas.coords(
            self.ball_inner,
            cx - BALL_R//2, cy - BALL_R//2,
            cx + BALL_R//2, cy + BALL_R//2
        )
        self.canvas.coords(
            self.ball_dino,
            cx, cy
        )

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
            text="🥚 Press SPACE to continue 🥚", fill="#4ade80",
            font=("Courier", 18, "bold")
        )
        self.start_items = [msg]

    def _game_over_screen(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self.canvas.create_rectangle(
            WIDTH // 2 - 200, HEIGHT // 2 - 70,
            WIDTH // 2 + 200, HEIGHT // 2 + 70,
            fill="#1a3a1a", outline="#ef4444", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 30,
            text="🦕 GAME OVER 🦕", fill="#ef4444",
            font=("Courier", 28, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text=f"Score: {self.score}", fill="#4ade80",
            font=("Courier", 18, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 40,
            text="😢 The dinosaurs are sad", fill="#ffd23f",
            font=("Courier", 12)
        )
        # Sad dinos
        for i in range(3):
            self.canvas.create_text(
                WIDTH//2 - 60 + i*60, HEIGHT//2 + 65,
                text="🦕", font=("Arial", 24)
            )

    def _game_win(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self.canvas.create_rectangle(
            WIDTH // 2 - 200, HEIGHT // 2 - 70,
            WIDTH // 2 + 200, HEIGHT // 2 + 70,
            fill="#1a3a1a", outline="#22c55e", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 30,
            text="🌟 YOU WIN! 🌟", fill="#22c55e",
            font=("Courier", 28, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text=f"Score: {self.score}", fill="#4ade80",
            font=("Courier", 18, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 40,
            text="🦕 The dinosaurs are happy!", fill="#ffd23f",
            font=("Courier", 14, "bold")
        )
        # Happy dino party
        for i in range(7):
            x = WIDTH//2 - 180 + i*60
            y = HEIGHT//2 + 65 + random.randint(-10, 10)
            self.canvas.create_text(
                x, y,
                text="🦕", font=("Arial", random.randint(20, 32))
            )

if __name__ == "__main__":
    Arkanoid()