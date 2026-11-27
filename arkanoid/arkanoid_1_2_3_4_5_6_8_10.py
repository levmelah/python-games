import tkinter as tk
import random
import math

# ─── הגדרות כלליות ───
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

class UnifiedArkanoid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎮 Multi-Theme Arkanoid Arcade 🎮")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#0f172a")
        self.canvas.pack()

        # הגדרת 6 המשחקים השונים
        self.games = [
            {
                "id": "robot",
                "title": "🤖 Robot Cyber Edition",
                "bg": "#050510",
                "paddle": "#00ffff",
                "ball": "#ffffff",
                "life_icon": "⚡",
                "colors": ["#ff0066", "#ff6600", "#ffcc00", "#00ff66", "#0066ff"]
            },
            {
                "id": "dino",
                "title": "🦕 Dino Jungle Edition",
                "bg": "#2d5a27",
                "paddle": "#8b5a2b",
                "ball": "#facc15",
                "life_icon": "🦕",
                "colors": ["#ff6b35", "#ffd23f", "#4ecdc4", "#45b7d1", "#96ceb4"]
            },
            {
                "id": "ice",
                "title": "❄️ Antarctic Ice Edition",
                "bg": "#dff3ff",
                "paddle": "#00d4ff",
                "ball": "#ffffff",
                "life_icon": "🐧",
                "colors": ["#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#38bdf8"]
            },
            {
                "id": "space",
                "title": "🌌 Galactic Space Edition",
                "bg": "#000008",
                "paddle": "#38bdf8",
                "ball": "#facc15",
                "life_icon": "🚀",
                "colors": ["#ff0066", "#ff6600", "#ffcc00", "#00ff66", "#0066ff"]
            },
            {
                "id": "fish",
                "title": "🌊 Ocean Fish Edition",
                "bg": "#0a2a4a",
                "paddle": "#38bdf8",
                "ball": "#facc15",
                "life_icon": "🐠",
                "colors": ["#b0c0d0", "#a8c8a8", "#d0c8a0", "#c8a8c8", "#a8b8d0"]
            },
            {
                "id": "flower",
                "title": "🌸 Garden Flower Edition",
                "bg": "#d9f7be",
                "paddle": "#22c55e",
                "ball": "#1f7a3a",
                "life_icon": "🌸",
                "colors": ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db"]
            }
        ]

        # משתני מצב
        self.in_menu = True
        self.selected_menu_idx = 0
        self.current_game_idx = 0

        self.score = 0
        self.lives = 3
        self.game_started = False
        self.game_over = False

        self.ball_dx = 5
        self.ball_dy = -5
        self.paddle_speed = 0

        self.particles = []
        self.binary_rain = []
        self.bricks = []
        self.heart_ids = []
        self.menu_buttons = []
        self.start_items = []
        self.scan_line = None
        self.scan_y = 0

        # מקשים
        self.root.bind("<KeyPress-Left>", lambda e: self._handle_left())
        self.root.bind("<KeyRelease-Left>", lambda e: self._stop_paddle("left"))
        self.root.bind("<KeyPress-Right>", lambda e: self._handle_right())
        self.root.bind("<KeyRelease-Right>", lambda e: self._stop_paddle("right"))
        self.root.bind("<KeyPress-Up>", lambda e: self._handle_up())
        self.root.bind("<KeyPress-Down>", lambda e: self._handle_down())
        self.root.bind("<space>", self._handle_space)
        self.root.bind("<Return>", self._handle_space)
        self.root.bind("<Tab>", lambda e: self._show_main_menu())
        self.root.bind("<r>", lambda e: self._restart_current_game())
        self.root.bind("<R>", lambda e: self._restart_current_game())
        self.root.bind("<Escape>", lambda e: self.root.quit())

        self._show_main_menu()
        self._game_loop()
        self.root.mainloop()

    # ─── תפריט בחירה ראשי ───
    def _show_main_menu(self):
        self.in_menu = True
        self.game_started = False
        self.game_over = False
        self.canvas.delete("all")
        self.canvas.configure(bg="#0f172a")

        # כותרת התפריט
        self.canvas.create_text(
            WIDTH // 2, 70,
            text="🎮 ARKANOID ARCADE 🎮", fill="#f1c40f",
            font=("Courier", 36, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, 115,
            text="בחר את המשחק שברצונך לשחק:", fill="#ffffff",
            font=("Arial", 16, "bold")
        )

        self._draw_menu_options()

        self.canvas.create_text(
            WIDTH // 2, HEIGHT - 25,
            text="ניווט: חצים (↑ ↓) | בחירה: ENTER / SPACE | חזרה לתפריט בתוך משחק: TAB",
            fill="#94a3b8", font=("Arial", 11)
        )

    def _draw_menu_options(self):
        for btn in self.menu_buttons:
            self.canvas.delete(btn)
        self.menu_buttons.clear()

        start_y = 150
        btn_h = 50

        for idx, g in enumerate(self.games):
            y = start_y + idx * (btn_h + 12)
            is_selected = (idx == self.selected_menu_idx)

            bg_color = "#3b82f6" if is_selected else "#1e293b"
            border_color = "#60a5fa" if is_selected else "#475569"
            text_color = "#ffffff" if is_selected else "#cbd5e1"

            rect = self.canvas.create_rectangle(
                WIDTH // 2 - 180, y,
                WIDTH // 2 + 180, y + btn_h,
                fill=bg_color, outline=border_color, width=2 if is_selected else 1
            )
            text = self.canvas.create_text(
                WIDTH // 2, y + btn_h // 2,
                text=g["title"], fill=text_color,
                font=("Arial", 15, "bold" if is_selected else "normal")
            )

            self.canvas.tag_bind(rect, "<Button-1>", lambda e, i=idx: self._select_and_start(i))
            self.canvas.tag_bind(text, "<Button-1>", lambda e, i=idx: self._select_and_start(i))

            self.menu_buttons.extend([rect, text])

    def _select_and_start(self, idx):
        self.selected_menu_idx = idx
        self._start_game(idx)

    # ─── אתחול משחק נבחר ───
    def _start_game(self, game_idx):
        self.in_menu = False
        self.current_game_idx = game_idx
        self.score = 0
        self.lives = 3
        self.game_started = False
        self.game_over = False
        self.ball_dx = 5
        self.ball_dy = -5
        self.paddle_speed = 0

        self.particles.clear()
        self.binary_rain.clear()

        game = self.games[self.current_game_idx]
        self.canvas.delete("all")
        self.canvas.configure(bg=game["bg"])

        # רקעים מיוחדים לפי המשחק הנבחר
        if game["id"] == "robot":
            self._draw_cyber_grid()
            self._init_binary_rain()
            self._create_scan_line()

        self._create_paddle()
        self._create_ball()
        self._create_bricks()
        self._create_ui()
        self._redraw_lives()
        self._show_start_screen()

    def _restart_current_game(self):
        if not self.in_menu:
            self._start_game(self.current_game_idx)

    # ─── אפקטי רקע ───
    def _draw_cyber_grid(self):
        for x in range(0, WIDTH, 40):
            self.canvas.create_line(x, 0, x, HEIGHT, fill="#0d1b2a", width=1)
        for y in range(0, HEIGHT, 40):
            self.canvas.create_line(0, y, WIDTH, y, fill="#0d1b2a", width=1)

    def _init_binary_rain(self):
        for _ in range(30):
            x = random.randint(10, WIDTH - 10)
            y = random.randint(0, HEIGHT)
            item = self.canvas.create_text(
                x, y, text=random.choice(["0", "1"]), fill="#00ff66",
                font=("Courier", random.randint(10, 14))
            )
            self.binary_rain.append({"id": item, "speed": random.uniform(1.5, 4.0)})

    def _update_binary_rain(self):
        for drop in self.binary_rain:
            self.canvas.move(drop["id"], 0, drop["speed"])
            coords = self.canvas.coords(drop["id"])
            if coords and coords[1] > HEIGHT:
                self.canvas.coords(drop["id"], random.randint(10, WIDTH - 10), 0)

    def _create_scan_line(self):
        self.scan_line = self.canvas.create_line(0, 0, WIDTH, 0, fill="#00ffff", width=2)
        self.scan_y = 0

    def _update_scan_line(self):
        if self.scan_line:
            self.scan_y = (self.scan_y + 2) % HEIGHT
            self.canvas.coords(self.scan_line, 0, self.scan_y, WIDTH, self.scan_y)

    # ─── יצירת אובייקטים ───
    def _create_paddle(self):
        game = self.games[self.current_game_idx]
        x = WIDTH // 2
        y = HEIGHT - 40
        self.paddle = self.canvas.create_rectangle(
            x - PADDLE_W // 2, y,
            x + PADDLE_W // 2, y + PADDLE_H,
            fill=game["paddle"], outline="#ffffff", width=1
        )

    def _create_ball(self):
        game = self.games[self.current_game_idx]
        x = WIDTH // 2
        y = HEIGHT - 60
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R,
            x + BALL_R, y + BALL_R,
            fill=game["ball"], outline="#ffffff"
        )

    def _create_bricks(self):
        self.bricks = []
        game = self.games[self.current_game_idx]
        colors = game["colors"]
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2

        for row in range(BRICK_ROWS):
            color = colors[row % len(colors)]
            points = [50, 40, 30, 20, 10][row % 5]
            for col in range(BRICK_COLS):
                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="#111111", width=1
                )
                self.bricks.append({"id": rect, "points": points})

    def _create_ui(self):
        game = self.games[self.current_game_idx]
        text_color = "#00ffff" if game["id"] == "robot" else "#ffffff"
        self.score_text = self.canvas.create_text(
            20, 25, text=f"SCORE: {self.score}",
            fill=text_color, font=("Courier", 16, "bold"), anchor="w"
        )
        self.title_text = self.canvas.create_text(
            WIDTH // 2, 25, text=game["title"],
            fill="#f1c40f", font=("Courier", 14, "bold")
        )
        self.help_text = self.canvas.create_text(
            WIDTH // 2, HEIGHT - 12,
            text="← → Move | SPACE Start | TAB Menu | R Restart | ESC Quit",
            fill="#94a3b8", font=("Arial", 10)
        )

    def _redraw_lives(self):
        for hid in self.heart_ids:
            self.canvas.delete(hid)
        self.heart_ids = []
        game = self.games[self.current_game_idx]

        for i in range(self.lives):
            lx = WIDTH - 30 - i * 30
            ly = 25
            item = self.canvas.create_text(
                lx, ly, text=game["life_icon"], font=("Arial", 16)
            )
            self.heart_ids.append(item)

    def _show_start_screen(self):
        for item in self.start_items:
            self.canvas.delete(item)
        self.start_items = []
        game = self.games[self.current_game_idx]

        t1 = self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 30,
            text=f"[ {game['title']} ]", fill="#ffffff",
            font=("Courier", 22, "bold")
        )
        t2 = self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text="לחץ SPACE להתחלה", fill="#f1c40f",
            font=("Arial", 16, "bold")
        )
        self.start_items = [t1, t2]

    # ─── טיפול במקשים ───
    def _handle_left(self):
        if not self.in_menu:
            self.paddle_speed = -8

    def _handle_right(self):
        if not self.in_menu:
            self.paddle_speed = 8

    def _handle_up(self):
        if self.in_menu:
            self.selected_menu_idx = (self.selected_menu_idx - 1) % len(self.games)
            self._draw_menu_options()

    def _handle_down(self):
        if self.in_menu:
            self.selected_menu_idx = (self.selected_menu_idx + 1) % len(self.games)
            self._draw_menu_options()

    def _handle_space(self, event=None):
        if self.in_menu:
            self._start_game(self.selected_menu_idx)
        elif self.game_over:
            self._restart_current_game()
        elif not self.game_started:
            self.game_started = True
            for item in self.start_items:
                self.canvas.delete(item)
            self.start_items.clear()

    def _stop_paddle(self, direction):
        if direction == "left" and self.paddle_speed < 0:
            self.paddle_speed = 0
        elif direction == "right" and self.paddle_speed > 0:
            self.paddle_speed = 0

    # ─── לולאת המשחק ───
    def _game_loop(self):
        if not self.in_menu:
            game = self.games[self.current_game_idx]
            if game["id"] == "robot":
                self._update_binary_rain()
                self._update_scan_line()

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
        elif self.paddle_speed > 0 and coords[2] < WIDTH - 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)

    def _move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)

    def _create_explosion(self, cx, cy):
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            dx = speed * math.cos(angle)
            dy = speed * math.sin(angle)
            size = random.randint(2, 5)
            p = self.canvas.create_oval(
                cx - size, cy - size, cx + size, cy + size,
                fill=random.choice(["#ff0066", "#facc15", "#00ff66", "#38bdf8"]), outline=""
            )
            self.particles.append({"id": p, "dx": dx, "dy": dy, "life": 12})

    def _update_particles(self):
        dead = []
        for p in self.particles:
            self.canvas.move(p["id"], p["dx"], p["dy"])
            p["life"] -= 1
            if p["life"] <= 0:
                self.canvas.delete(p["id"])
                dead.append(p)
        for p in dead:
            self.particles.remove(p)

    def _check_collisions(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        bcx = (bx1 + bx2) / 2

        # קירות
        if bx1 <= 0:
            self.ball_dx = abs(self.ball_dx)
        if bx2 >= WIDTH:
            self.ball_dx = -abs(self.ball_dx)
        if by1 <= 0:
            self.ball_dy = abs(self.ball_dy)

        # פסילה (נגיעה בתחתית)
        if by2 >= HEIGHT:
            self.lives -= 1
            self.canvas.itemconfig(self.score_text, text=f"SCORE: {self.score}")
            self._redraw_lives()
            if self.lives <= 0:
                self._game_over_screen()
            else:
                self._reset_ball()
            return

        # התנגשות במטקה
        px1, py1, px2, py2 = self.canvas.coords(self.paddle)
        if (self.ball_dy > 0 and by2 >= py1 and by1 <= py2 and bx2 >= px1 and bx1 <= px2):
            hit_pos = (bcx - (px1 + px2) / 2) / (PADDLE_W / 2)
            hit_pos = max(-1, min(1, hit_pos))
            angle = math.radians(30 + (1 - abs(hit_pos)) * 60)
            speed = math.sqrt(self.ball_dx**2 + self.ball_dy**2)
            self.ball_dx = speed * math.cos(angle) * (1 if hit_pos >= 0 else -1)
            self.ball_dy = -abs(speed * math.sin(angle))
            self.canvas.coords(self.ball, bx1, py1 - BALL_R * 2, bx2, py1)
            self._create_explosion(bcx, py1)

        # התנגשות בלבנים
        for brick in self.bricks[:]:
            brx1, bry1, brx2, bry2 = self.canvas.coords(brick["id"])
            if bx2 >= brx1 and bx1 <= brx2 and by2 >= bry1 and by1 <= bry2:
                self.score += brick["points"]
                self.canvas.itemconfig(self.score_text, text=f"SCORE: {self.score}")
                self._create_explosion((brx1 + brx2) / 2, (bry1 + bry2) / 2)
                self.canvas.delete(brick["id"])
                self.bricks.remove(brick)

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

        if len(self.bricks) == 0:
            self._game_win()

    def _reset_ball(self):
        self.canvas.coords(
            self.ball,
            WIDTH // 2 - BALL_R, HEIGHT - 60 - BALL_R,
            WIDTH // 2 + BALL_R, HEIGHT - 60 + BALL_R
        )
        self.canvas.coords(
            self.paddle,
            WIDTH // 2 - PADDLE_W // 2, HEIGHT - 40,
            WIDTH // 2 + PADDLE_W // 2, HEIGHT - 40 + PADDLE_H
        )
        self.ball_dx = 5 * random.choice([-1, 1])
        self.ball_dy = -5
        self.game_started = False
        msg = self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text="לחץ SPACE להמשך המשחק", fill="#ffffff",
            font=("Arial", 16, "bold")
        )
        self.start_items = [msg]

    # ─── מסכי סיום ───
    def _game_over_screen(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self.canvas.create_rectangle(
            WIDTH // 2 - 220, HEIGHT // 2 - 70,
            WIDTH // 2 + 220, HEIGHT // 2 + 70,
            fill="#0f172a", outline="#ef4444", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 30,
            text="GAME OVER!", fill="#ef4444",
            font=("Courier", 28, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text=f"ניקוד סופי: {self.score}", fill="#ffffff",
            font=("Arial", 16)
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 45,
            text="לחץ TAB לתפריט ראשי | R למשחק חוזר", fill="#f1c40f",
            font=("Arial", 12)
        )

    def _game_win(self):
        self.game_over = True
        self.ball_dx = 0
        self.ball_dy = 0
        self.canvas.create_rectangle(
            WIDTH // 2 - 220, HEIGHT // 2 - 70,
            WIDTH // 2 + 220, HEIGHT // 2 + 70,
            fill="#0f172a", outline="#22c55e", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 30,
            text="YOU WIN! 🎉", fill="#22c55e",
            font=("Courier", 28, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 10,
            text=f"ניקוד סופי: {self.score}", fill="#ffffff",
            font=("Arial", 16)
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 45,
            text="לחץ TAB לתפריט ראשי | R למשחק חוזר", fill="#f1c40f",
            font=("Arial", 12)
        )

if __name__ == "__main__":
    UnifiedArkanoid()