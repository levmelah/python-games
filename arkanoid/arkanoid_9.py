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
        self.root.title("Arkanoid - Robot Edition")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#050510")
        self.canvas.pack()

        # ─── Robot Background Elements ───
        self._draw_robot_background()
        self._create_scanning_lines()
        self._create_binary_rain()
        
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

    # ─── Robot Background ───
    
    def _draw_robot_background(self):
        """Draw advanced robot-themed background."""
        # Main grid
        for x in range(0, WIDTH, 40):
            self.canvas.create_line(x, 0, x, HEIGHT, fill="#0a0a20", width=1)
        for y in range(0, HEIGHT, 40):
            self.canvas.create_line(0, y, WIDTH, y, fill="#0a0a20", width=1)
        
        # Glowing grid lines
        for x in range(0, WIDTH, 160):
            self.canvas.create_line(x, 0, x, HEIGHT, fill="#1a1a3a", width=2, dash=(10, 10))
        for y in range(0, HEIGHT, 160):
            self.canvas.create_line(0, y, WIDTH, y, fill="#1a1a3a", width=2, dash=(10, 10))
        
        # Corner brackets (robot HUD style)
        corners = [
            (20, 20, 80, 20, 80, 40),
            (20, 20, 20, 80, 40, 80),
            (WIDTH-20, 20, WIDTH-80, 20, WIDTH-80, 40),
            (WIDTH-20, 20, WIDTH-20, 80, WIDTH-40, 80),
            (20, HEIGHT-20, 80, HEIGHT-20, 80, HEIGHT-40),
            (20, HEIGHT-20, 20, HEIGHT-80, 40, HEIGHT-80),
            (WIDTH-20, HEIGHT-20, WIDTH-80, HEIGHT-20, WIDTH-80, HEIGHT-40),
            (WIDTH-20, HEIGHT-20, WIDTH-20, HEIGHT-80, WIDTH-40, HEIGHT-80),
        ]
        for x1,y1,x2,y2,x3,y3 in corners:
            self.canvas.create_line(x1, y1, x2, y2, fill="#00ffff", width=2)
            self.canvas.create_line(x2, y2, x3, y3, fill="#00ffff", width=2)
        
        # Robot eyes at top
        self._draw_robot_eye(150, 30, 40, 20)
        self._draw_robot_eye(WIDTH-150, 30, 40, 20)
        
        # Center screen display
        self.canvas.create_rectangle(WIDTH//2-120, 10, WIDTH//2+120, 40, 
                                     outline="#00ffff", fill="#050510", width=1)
        self.canvas.create_text(WIDTH//2, 27, text="SYSTEM: ONLINE", 
                                fill="#00ff66", font=("Courier", 12, "bold"))
        
        # Status LEDs
        for i in range(3):
            x = WIDTH//2 - 80 + i*30
            color = ["#00ff66", "#ffcc00", "#00ff66"][i]
            self.canvas.create_oval(x, 12, x+8, 20, fill=color, outline=color)
        
        # Bottom status bar
        self.canvas.create_rectangle(20, HEIGHT-30, WIDTH-20, HEIGHT-20, 
                                     outline="#00ffff", fill="#050510", width=1)
        self.canvas.create_text(30, HEIGHT-25, text="ROBOT ARKANOID v2.0", 
                                fill="#8888ff", font=("Courier", 10), anchor="w")
        
        # CPU usage indicator
        self.canvas.create_text(WIDTH-30, HEIGHT-25, text="CPU: 42%", 
                                fill="#00ff66", font=("Courier", 10), anchor="e")
        
        # Radar circle
        cx, cy = WIDTH//2, HEIGHT//2
        for r in [100, 200, 300]:
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, 
                                   outline="#0a0a30", width=1, dash=(5, 10))
        
        # Crosshairs
        self.canvas.create_line(cx-20, cy, cx+20, cy, fill="#0a0a30", width=1)
        self.canvas.create_line(cx, cy-20, cx, cy+20, fill="#0a0a30", width=1)
        
        # Hexagonal patterns
        self._draw_hexagon(100, 150, 30, "#0a0a30")
        self._draw_hexagon(WIDTH-100, 150, 30, "#0a0a30")
        self._draw_hexagon(100, HEIGHT-150, 30, "#0a0a30")
        self._draw_hexagon(WIDTH-100, HEIGHT-150, 30, "#0a0a30")
    
    def _draw_robot_eye(self, cx, cy, width, height):
        """Draw a robotic eye."""
        # Outer casing
        self.canvas.create_oval(cx-width, cy-height, cx+width, cy+height, 
                               outline="#00ffff", fill="#0a0a20", width=2)
        # Inner ring
        self.canvas.create_oval(cx-width//2, cy-height//2, cx+width//2, cy+height//2,
                               outline="#00ffff", fill="#000000", width=1)
        # Pupil
        pupil = self.canvas.create_oval(cx-5, cy-8, cx+5, cy+8, fill="#00ffff", outline="#00ffff")
        # Glow
        self.canvas.create_oval(cx-2, cy-12, cx+2, cy+12, fill="#ffffff", outline="")
        # Scanning line (will be animated)
        self.eye_scan = self.canvas.create_line(cx-width, cy, cx+width, cy, 
                                               fill="#00ffff", width=1, dash=(2, 4))
        self.eye_scan2 = self.canvas.create_line(cx, cy-height, cx, cy+height,
                                                fill="#00ffff", width=1, dash=(2, 4))
    
    def _draw_hexagon(self, cx, cy, size, color):
        """Draw a hexagon."""
        points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            x = cx + size * math.cos(angle)
            y = cy + size * math.sin(angle)
            points.extend([x, y])
        self.canvas.create_polygon(points, outline=color, fill="", width=1)
    
    def _create_scanning_lines(self):
        """Create animated scanning lines."""
        self.scan_lines = []
        for i in range(5):
            y = 50 + i * 120
            line = self.canvas.create_line(0, y, WIDTH, y, 
                                          fill="#00ffff", width=1, 
                                          dash=(10, 20), stipple="gray50")
            self.scan_lines.append(line)
    
    def _create_binary_rain(self):
        """Create binary rain particles."""
        self.binary_particles = []
        for i in range(30):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            speed = random.uniform(0.5, 2)
            char = random.choice(["0", "1"])
            text = self.canvas.create_text(x, y, text=char, 
                                          fill="#00ff66", font=("Courier", 10))
            self.binary_particles.append({"id": text, "x": x, "y": y, "speed": speed, "char": char})
    
    def _animate_background(self):
        """Animate background elements."""
        self.frame_count += 1
        
        # Animate binary rain
        for p in self.binary_particles:
            self.canvas.move(p["id"], 0, p["speed"])
            coords = self.canvas.coords(p["id"])
            if coords[1] > HEIGHT:
                self.canvas.coords(p["id"], random.randint(0, WIDTH), -10)
                new_char = random.choice(["0", "1"])
                self.canvas.itemconfig(p["id"], text=new_char)
                p["char"] = new_char
        
        # Animate scanning lines
        for i, line in enumerate(self.scan_lines):
            offset = (self.frame_count * 2 + i * 20) % 40
            self.canvas.itemconfig(line, dash=(10-offset%10, 20+offset%10))
        
        # Animate robot eyes (scanning)
        if hasattr(self, 'eye_scan'):
            scan_y = 20 + 30 * math.sin(self.frame_count * 0.05)
            self.canvas.coords(self.eye_scan, 110, 30+scan_y, 190, 30+scan_y)
            self.canvas.coords(self.eye_scan2, 150+scan_y, 10, 150+scan_y, 50)
    
    # ─── Create objects ───

    def _create_paddle(self):
        x = WIDTH // 2
        y = HEIGHT - 40
        # Robot paddle
        self.paddle = self.canvas.create_rectangle(
            x - PADDLE_W // 2, y,
            x + PADDLE_W // 2, y + PADDLE_H,
            fill="#00ffff", outline="#00ffff", width=0
        )
        # Glow effect
        self.paddle_glow = self.canvas.create_rectangle(
            x - PADDLE_W // 2 - 4, y - 4,
            x + PADDLE_W // 2 + 4, y + PADDLE_H + 4,
            outline="#00ffff", width=2, stipple="gray50"
        )
        # Paddle details
        self.paddle_core = self.canvas.create_rectangle(
            x - 20, y + 3,
            x + 20, y + PADDLE_H - 3,
            fill="#ffffff", outline="#ffffff", width=0
        )
        # Sensor dots
        self.sensor_dots = []
        for i in range(-3, 4):
            dot_x = x + i * 12
            dot = self.canvas.create_oval(dot_x-2, y-6, dot_x+2, y-2, 
                                         fill="#ff6600", outline="#ff6600")
            self.sensor_dots.append(dot)

    def _create_ball(self):
        x = WIDTH // 2
        y = HEIGHT - 60
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R,
            x + BALL_R, y + BALL_R,
            fill="#ffffff", outline="#00ffff", width=2
        )
        self.ball_core = self.canvas.create_oval(
            x - BALL_R//2, y - BALL_R//2,
            x + BALL_R//2, y + BALL_R//2,
            fill="#00ffff", outline="#00ffff"
        )
        # Ball trail effect
        self.ball_trail = self.canvas.create_oval(
            x - BALL_R-3, y - BALL_R-3,
            x + BALL_R+3, y + BALL_R+3,
            outline="#00ffff", width=1, stipple="gray50"
        )

    def _create_bricks(self):
        self.bricks = []
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        for row in range(BRICK_ROWS):
            color = BRICK_COLORS[row]
            points = BRICK_POINTS[row]
            for col in range(BRICK_COLS):
                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color, outline="#ffffff", width=1
                )
                shine = self.canvas.create_rectangle(
                    x1+3, y1+3, x2-3, y1+BRICK_H//3,
                    fill="white", outline="", stipple="gray25"
                )
                self.bricks.append({"id": rect, "points": points, "shine": shine})

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
        # Robot-style score display
        self.score_frame = self.canvas.create_rectangle(
            10, 10, 180, 40,
            outline="#00ffff", fill="#050510", width=1
        )
        self.score_text = self.canvas.create_text(
            25, 25, text=f"SCORE: {self.score}",
            fill="#00ffff", font=("Courier", 16, "bold"), anchor="w"
        )
        
        # Level indicator
        self.level_text = self.canvas.create_text(
            WIDTH//2, 55,
            text="LEVEL 1", fill="#8888ff",
            font=("Courier", 10)
        )

    def _update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"SCORE: {self.score}")
        self._redraw_hearts()

    def _show_start_screen(self):
        self.start_items = []
        # Animated title
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 100,
            text="[ ROBOT ARKANOID ]", fill="#00ffff",
            font=("Courier", 44, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 40,
            text="▶ PRESS SPACE TO INITIALIZE ◀", fill="#ffffff",
            font=("Courier", 20, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text="CONTROLS: ← →  MOVE PADDLE", fill="#8888ff",
            font=("Courier", 14)
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 40,
            text="⚡ ROBOT MODE: ACTIVE ⚡", fill="#ff6600",
            font=("Courier", 12, "bold")
        ))
        
        # Animated status bar
        for i in range(3):
            x = WIDTH//2 - 60 + i * 60
            bar = self.canvas.create_rectangle(x, HEIGHT//2 + 70, x+40, HEIGHT//2 + 85,
                                              fill="#0a0a20", outline="#00ffff", width=1)
            self.start_items.append(bar)

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
        # Animate background
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
            self.canvas.move(self.paddle_glow, self.paddle_speed, 0)
            self.canvas.move(self.paddle_core, self.paddle_speed, 0)
            for dot in self.sensor_dots:
                self.canvas.move(dot, self.paddle_speed, 0)
        elif self.paddle_speed > 0 and coords[2] < WIDTH - 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
            self.canvas.move(self.paddle_glow, self.paddle_speed, 0)
            self.canvas.move(self.paddle_core, self.paddle_speed, 0)
            for dot in self.sensor_dots:
                self.canvas.move(dot, self.paddle_speed, 0)

    def _move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        self.canvas.move(self.ball_core, self.ball_dx, self.ball_dy)
        self.canvas.move(self.ball_trail, self.ball_dx, self.ball_dy)

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
            speed = min(max(speed, 5), 9)
            self.ball_dx = speed * math.cos(angle) * (1 if hit_pos >= 0 else -1)
            self.ball_dy = -abs(speed * math.sin(angle))
            self.canvas.coords(self.ball, bx1, py1 - BALL_R * 2, bx2, py1)
            self.canvas.coords(self.ball_core, 
                              (bx1+bx2)//2 - BALL_R//2, py1 - BALL_R*2 - BALL_R//2,
                              (bx1+bx2)//2 + BALL_R//2, py1 - BALL_R*2 + BALL_R//2)
            self.canvas.coords(self.ball_trail,
                              (bx1+bx2)//2 - BALL_R-3, py1 - BALL_R*2 - BALL_R-3,
                              (bx1+bx2)//2 + BALL_R+3, py1 - BALL_R*2 + BALL_R+3)

        # Brick collision
        for brick in self.bricks[:]:
            brx1, bry1, brx2, bry2 = self.canvas.coords(brick["id"])
            if (bx2 >= brx1 and bx1 <= brx2 and
                    by2 >= bry1 and by1 <= bry2):
                self.score += brick["points"]
                self.canvas.delete(brick["id"])
                self.canvas.delete(brick["shine"])
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

    def _reset_ball(self):
        self.canvas.coords(
            self.ball,
            WIDTH // 2 - BALL_R, HEIGHT - 60 - BALL_R,
            WIDTH // 2 + BALL_R, HEIGHT - 60 + BALL_R
        )
        self.canvas.coords(
            self.ball_core,
            WIDTH // 2 - BALL_R//2, HEIGHT - 60 - BALL_R - BALL_R//2,
            WIDTH // 2 + BALL_R//2, HEIGHT - 60 + BALL_R - BALL_R//2
        )
        self.canvas.coords(
            self.ball_trail,
            WIDTH // 2 - BALL_R-3, HEIGHT - 60 - BALL_R-3,
            WIDTH // 2 + BALL_R+3, HEIGHT - 60 + BALL_R+3
        )
        self.ball_dx = 5 * random.choice([-1, 1])
        self.ball_dy = -5
        self.game_started = False
        msg = self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text="⚠ REBOOTING... PRESS SPACE ⚠", fill="#ff6600",
            font=("Courier", 18, "bold")
        )
        self.start_items = [msg]

    def _game_over_screen(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        # Terminal-style game over
        self.canvas.create_rectangle(
            WIDTH // 2 - 300, HEIGHT // 2 - 100,
            WIDTH // 2 + 300, HEIGHT // 2 + 100,
            fill="#050510", outline="#ff0044", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 40,
            text="⚠ SYSTEM CRITICAL FAILURE ⚠", fill="#ff0044",
            font=("Courier", 26, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text=f"FINAL SCORE: {self.score}", fill="#ffffff",
            font=("Courier", 22, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 50,
            text="[ GAME OVER ]", fill="#ff6600",
            font=("Courier", 16)
        )

    def _game_win(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self.canvas.create_rectangle(
            WIDTH // 2 - 300, HEIGHT // 2 - 100,
            WIDTH // 2 + 300, HEIGHT // 2 + 100,
            fill="#050510", outline="#00ff66", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 40,
            text="✓ MISSION ACCOMPLISHED ✓", fill="#00ff66",
            font=("Courier", 26, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text=f"FINAL SCORE: {self.score}", fill="#ffffff",
            font=("Courier", 22, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 50,
            text="[ YOU WIN! ]", fill="#00ffff",
            font=("Courier", 16)
        )

if __name__ == "__main__":
    Arkanoid()