import tkinter as tk
import random
import math

# ─── Constants ───
WIDTH = 800
HEIGHT = 600
PADDLE_W = 130
PADDLE_H = 15
BALL_R = 8
BRICK_ROWS = 6
BRICK_COLS = 12
BRICK_W = 58
BRICK_H = 25
BRICK_PAD = 4
TOP_OFFSET = 60
FPS = 60
MAX_LEVELS = 9
BALL_SPEED_STEP = 0.7
PADDLE_SHRINK_PER_LEVEL = 10
MIN_PADDLE_W = 56
VIP_LEVEL = 8
VIP_ENTRY_COST = 20

BRICK_COLORS = ["#124E4E", "#8A0909", "#943737", "#EEFF00", "#003003"]
BRICK_POINTS = [50, 40, 30, 20, 10]
LEVEL_BG_COLORS = {
    1: "#87CEEB",  # light blue
    2: "#1E90FF",  # blue
    3: "#2ECC71",  # green
    4: "#F5B041",  # orange-yellow
    5: "#E74C3C",  # red
    6: "#1F2937",  # dark gray-blue
    7: "#0b0b0b",  # impossible level
    8: "#2b1f0a",  # vip gold-brown
    9: "#0a0018",  # omega level
}

SMILEY_FACES = [":)", ":D", ";)", ":P", ":O", ":("]
CHARACTERS = {
    1: {
        "name": "Blue Thunder",
        "fill": "#3b82f6",
        "outline": "#1d4ed8",
        "shadow": "#1e40af",
        "shine": "#bfdbfe",
    },
    2: {
        "name": "Orange Fire",
        "fill": "#f59e0b",
        "outline": "#c2410c",
        "shadow": "#9a3412",
        "shine": "#fed7aa",
    },
    3: {
        "name": "Yellow Water",
        "fill": "#D4AF37",
        "outline": "#8C6A16",
        "shadow": "#9E7E21",
        "shine": "#FFF7C2",
    },
}


def _shade_color(color, amount):
    color = color.lstrip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)

    red = max(0, min(255, red + amount))
    green = max(0, min(255, green + amount))
    blue = max(0, min(255, blue + amount))

    return f"#{red:02x}{green:02x}{blue:02x}"


class Arkanoid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Arkanoid")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#1a1a2e")
        self.canvas.pack()

        self.base_ball_speed = 4
        self.start_items = []
        self.pause_items = []
        self._reset_state()
        self._apply_level_background(self.level)

        # Create objects
        self._create_paddle()
        self._create_ball()
        self._create_bricks()
        self._create_ui()
        self._redraw_hearts()
        self._show_start_screen(level_select=True)

        # Bindings
        self.root.bind("<KeyPress-Left>", lambda e: self._set_paddle_speed(-8))
        self.root.bind("<KeyRelease-Left>", lambda e: self._stop_paddle("left"))
        self.root.bind("<KeyPress-Right>", lambda e: self._set_paddle_speed(8))
        self.root.bind("<KeyRelease-Right>", lambda e: self._stop_paddle("right"))
        self.root.bind("<space>", self._start_game)
        self.root.bind("<Return>", self._start_game)
        self.root.bind("<p>", self._toggle_pause)
        self.root.bind("<P>", self._toggle_pause)
        self.root.bind("<r>", self._restart_game)
        self.root.bind("<R>", self._restart_game)
        self.root.bind("<Up>", lambda e: self._change_selected_level(-1))
        self.root.bind("<Down>", lambda e: self._change_selected_level(1))
        self.root.bind("<a>", lambda e: self._change_selected_character(-1))
        self.root.bind("<A>", lambda e: self._change_selected_character(-1))
        self.root.bind("<d>", lambda e: self._change_selected_character(1))
        self.root.bind("<D>", lambda e: self._change_selected_character(1))
        self.root.bind("<KeyPress-0>", self._activate_character_power)
        for lvl in range(1, MAX_LEVELS + 1):
            self.root.bind(f"<KeyPress-{lvl}>", lambda e, n=lvl: self._set_selected_level(n))

        self._game_loop()
        self.root.mainloop()

    # ─── Create objects ───
 
    def _reset_state(self):
        self.score = 0
        self.lives = 10
        self.level = 1
        self.game_started = False
        self.game_over = False
        self.paused = False
        self.paddle_speed = 0
        self.current_paddle_width = PADDLE_W
        self.ball_dx = self.base_ball_speed
        self.ball_dy = -self.base_ball_speed
        self.selected_level = 1
        self.special_brick = None
        self.special_brick_dx = 11
        self.smiley_face_index = 0
        self.smiley_anim_tick = 0
        self.vip_paid = False
        self.selected_character = 1
        self.character_id = 1

    def _create_paddle(self):
        x = WIDTH // 2
        y = HEIGHT - 40
        self.paddle = self.canvas.create_rectangle(
            x - self.current_paddle_width // 2, y,
            x + self.current_paddle_width // 2, y + PADDLE_H,
            fill="#00d4ff", outline="#00d4ff", width=0
        )

    def _create_ball(self):
        x = WIDTH // 2
        y = HEIGHT - 60
        palette = CHARACTERS[self.character_id]
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R,
            x + BALL_R, y + BALL_R,
            fill=palette["fill"], outline=palette["outline"], width=2
        )
        self.ball_shadow = self.canvas.create_oval(
            x - BALL_R + 2, y - BALL_R + 5,
            x + BALL_R - 2, y + BALL_R - 1,
            fill=palette["shadow"], outline=""
        )
        self.ball_shine = self.canvas.create_oval(
            x - BALL_R + 1, y - BALL_R + 1,
            x - BALL_R + 6, y - BALL_R + 6,
            fill=palette["shine"], outline=""
        )
        self.ball_crown_base = self.canvas.create_polygon(
            x - 10, y - BALL_R - 4,
            x - 8, y - BALL_R - 12,
            x - 3, y - BALL_R - 5,
            x, y - BALL_R - 13,
            x + 3, y - BALL_R - 5,
            x + 8, y - BALL_R - 12,
            x + 10, y - BALL_R - 4,
            fill="#d4af37", outline="#8c6a16", width=1, state="hidden"
        )
        self.ball_crown_jewel = self.canvas.create_oval(
            x - 2, y - BALL_R - 10,
            x + 2, y - BALL_R - 6,
            fill="#e74c3c", outline="", state="hidden"
        )
        self.ball_crown_parts = [self.ball_crown_base, self.ball_crown_jewel]
        self._sync_ball_effects()

    def _apply_character_style(self):
        palette = CHARACTERS[self.character_id]
        self.canvas.itemconfig(self.ball, fill=palette["fill"], outline=palette["outline"])
        self.canvas.itemconfig(self.ball_shadow, fill=palette["shadow"])
        self.canvas.itemconfig(self.ball_shine, fill=palette["shine"])
        self._sync_ball_effects()

    def _sync_ball_effects(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        cx = (bx1 + bx2) / 2
        self.canvas.coords(
            self.ball_shadow,
            bx1 + 2, by1 + 5,
            bx2 - 2, by2 - 1
        )
        self.canvas.coords(
            self.ball_shine,
            bx1 + 1, by1 + 1,
            bx1 + 6, by1 + 6
        )
        self.canvas.coords(
            self.ball_crown_base,
            cx - 10, by1 - 4,
            cx - 8, by1 - 12,
            cx - 3, by1 - 5,
            cx, by1 - 13,
            cx + 3, by1 - 5,
            cx + 8, by1 - 12,
            cx + 10, by1 - 4
        )
        self.canvas.coords(
            self.ball_crown_jewel,
            cx - 2, by1 - 10,
            cx + 2, by1 - 6
        )
        crown_state = "normal" if self.level in (VIP_LEVEL, 9) else "hidden"
        for item in self.ball_crown_parts:
            self.canvas.itemconfig(item, state=crown_state)
        self.canvas.tag_raise(self.ball)
        self.canvas.tag_raise(self.ball_shine)
        for item in self.ball_crown_parts:
            self.canvas.tag_raise(item)

    def _create_bricks(self):
        self.bricks = []
        self.special_brick = None
        if self.level == 6:
            self._create_smiley_boss_brick()
            return
        if self.level == 7:
            self._create_impossible_bricks()
            return
        if self.level == VIP_LEVEL:
            self._create_vip_bricks()
            return
        if self.level == 9:
            self._create_omega_bricks()
            return

        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        for row in range(BRICK_ROWS):
            color = BRICK_COLORS[row % len(BRICK_COLORS)]
            light_color = _shade_color(color, 45)
            dark_color = _shade_color(color, -45)
            face_color = _shade_color(color, 15)
            points = BRICK_POINTS[row % len(BRICK_POINTS)]
            for col in range(BRICK_COLS):
                if self.level > 1:
                    gap_mod = max(5 - min(self.level, 4), 2)
                    if (row + col + self.level) % gap_mod == 0:
                        continue

                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H

                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=face_color, outline=dark_color, width=1
                )

                top_edge = self.canvas.create_line(
                    x1 + 2, y1 + 2, x2 - 2, y1 + 2,
                    fill=light_color, width=2
                )
                left_edge = self.canvas.create_line(
                    x1 + 2, y1 + 2, x1 + 2, y2 - 2,
                    fill=light_color, width=2
                )
                bottom_edge = self.canvas.create_line(
                    x1 + 2, y2 - 2, x2 - 2, y2 - 2,
                    fill=dark_color, width=2
                )
                right_edge = self.canvas.create_line(
                    x2 - 2, y1 + 2, x2 - 2, y2 - 2,
                    fill=dark_color, width=2
                )
                shine = self.canvas.create_rectangle(
                    x1 + 6, y1 + 5, x2 - 18, y1 + 10,
                    fill=light_color, outline="", stipple="gray25"
                )

                self.bricks.append({
                    "id": rect,
                    "parts": [rect, top_edge, left_edge, bottom_edge, right_edge, shine],
                    "points": points,
                })

    def _create_vip_bricks(self):
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        for row in range(BRICK_ROWS):
            color = "#d4af37"
            light_color = _shade_color(color, 35)
            dark_color = _shade_color(color, -45)
            face_color = _shade_color(color, 8)
            points = 70 - row * 8
            for col in range(BRICK_COLS):
                if (row + col) % 3 == 0:
                    continue

                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H

                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=face_color, outline=dark_color, width=1
                )
                top_edge = self.canvas.create_line(
                    x1 + 2, y1 + 2, x2 - 2, y1 + 2,
                    fill=light_color, width=2
                )
                left_edge = self.canvas.create_line(
                    x1 + 2, y1 + 2, x1 + 2, y2 - 2,
                    fill=light_color, width=2
                )
                bottom_edge = self.canvas.create_line(
                    x1 + 2, y2 - 2, x2 - 2, y2 - 2,
                    fill=dark_color, width=2
                )
                right_edge = self.canvas.create_line(
                    x2 - 2, y1 + 2, x2 - 2, y2 - 2,
                    fill=dark_color, width=2
                )
                shine = self.canvas.create_rectangle(
                    x1 + 6, y1 + 5, x2 - 18, y1 + 10,
                    fill=light_color, outline="", stipple="gray25"
                )

                self.bricks.append({
                    "id": rect,
                    "parts": [rect, top_edge, left_edge, bottom_edge, right_edge, shine],
                    "points": 1000000,
                })

    def _create_impossible_bricks(self):
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        rows = BRICK_ROWS
        for row in range(rows):
            color = BRICK_COLORS[row % len(BRICK_COLORS)]
            light_color = _shade_color(color, 45)
            dark_color = _shade_color(color, -45)
            face_color = _shade_color(color, 15)
            points = BRICK_POINTS[row % len(BRICK_POINTS)]
            for col in range(BRICK_COLS):
                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H

                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=face_color, outline=dark_color, width=1
                )
                top_edge = self.canvas.create_line(
                    x1 + 2, y1 + 2, x2 - 2, y1 + 2,
                    fill=light_color, width=2
                )
                left_edge = self.canvas.create_line(
                    x1 + 2, y1 + 2, x1 + 2, y2 - 2,
                    fill=light_color, width=2
                )
                bottom_edge = self.canvas.create_line(
                    x1 + 2, y2 - 2, x2 - 2, y2 - 2,
                    fill=dark_color, width=2
                )
                right_edge = self.canvas.create_line(
                    x2 - 2, y1 + 2, x2 - 2, y2 - 2,
                    fill=dark_color, width=2
                )
                shine = self.canvas.create_rectangle(
                    x1 + 6, y1 + 5, x2 - 18, y1 + 10,
                    fill=light_color, outline="", stipple="gray25"
                )
                self.bricks.append({
                    "id": rect,
                    "parts": [rect, top_edge, left_edge, bottom_edge, right_edge, shine],
                    "points": points,
                    "unbreakable": True,
                })

    def _create_omega_bricks(self):
        # Level 9: mix of VIP gold, normal colorful, and unbreakable obsidian walls.
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        rows = BRICK_ROWS + 1

        for row in range(rows):
            for col in range(BRICK_COLS):
                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H

                # Side columns and middle spine are unbreakable barriers (level 7 style).
                is_barrier = col in (0, BRICK_COLS - 1) or (col == BRICK_COLS // 2 and row % 2 == 0)

                if is_barrier:
                    color = "#111827"
                    light_color = _shade_color(color, 28)
                    dark_color = _shade_color(color, -25)
                    face_color = _shade_color(color, 8)
                    points = 0
                    unbreakable = True
                elif (row + col) % 4 == 0:
                    # VIP-like gold blocks with big points.
                    color = "#d4af37"
                    light_color = _shade_color(color, 35)
                    dark_color = _shade_color(color, -45)
                    face_color = _shade_color(color, 10)
                    points = 2500
                    unbreakable = False
                else:
                    # Colorful upgraded normal bricks.
                    base = BRICK_COLORS[(row + col) % len(BRICK_COLORS)]
                    light_color = _shade_color(base, 55)
                    dark_color = _shade_color(base, -45)
                    face_color = _shade_color(base, 18)
                    points = 120 + (rows - row) * 20
                    unbreakable = False

                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=face_color, outline=dark_color, width=1
                )
                top_edge = self.canvas.create_line(
                    x1 + 2, y1 + 2, x2 - 2, y1 + 2,
                    fill=light_color, width=2
                )
                left_edge = self.canvas.create_line(
                    x1 + 2, y1 + 2, x1 + 2, y2 - 2,
                    fill=light_color, width=2
                )
                bottom_edge = self.canvas.create_line(
                    x1 + 2, y2 - 2, x2 - 2, y2 - 2,
                    fill=dark_color, width=2
                )
                right_edge = self.canvas.create_line(
                    x2 - 2, y1 + 2, x2 - 2, y2 - 2,
                    fill=dark_color, width=2
                )
                shine = self.canvas.create_rectangle(
                    x1 + 6, y1 + 5, x2 - 18, y1 + 10,
                    fill=light_color, outline="", stipple="gray25"
                )

                brick_info = {
                    "id": rect,
                    "parts": [rect, top_edge, left_edge, bottom_edge, right_edge, shine],
                    "points": points,
                }
                if unbreakable:
                    brick_info["unbreakable"] = True
                self.bricks.append(brick_info)

        # Add upgraded moving boss from level 6 as part of omega mix.
        self._create_smiley_boss_brick()
        if self.special_brick:
            self.special_brick["points"] = 6000
            self.special_brick_dx = 14

    def _create_smiley_boss_brick(self):
        x1 = WIDTH // 2 - 38
        y1 = TOP_OFFSET + 70
        x2 = WIDTH // 2 + 38
        y2 = y1 + 76

        circle = self.canvas.create_oval(
            x1, y1, x2, y2,
            fill="#f1c40f", outline="#b9770e", width=3
        )
        smiley_text = self.canvas.create_text(
            (x1 + x2) // 2, (y1 + y2) // 2,
            text=SMILEY_FACES[self.smiley_face_index],
            fill="#2c3e50", font=("Courier", 22, "bold")
        )

        self.special_brick = {
            "id": circle,
            "parts": [circle, smiley_text],
            "text_id": smiley_text,
            "points": 500,
        }
        self.bricks.append(self.special_brick)

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
        self.level_text = self.canvas.create_text(
            WIDTH // 2, 20, text=f"Level: {self.level}/{MAX_LEVELS}",
            fill="#f1c40f", font=("Courier", 18, "bold")
        )
        self.help_text = self.canvas.create_text(
            WIDTH // 2, HEIGHT - 18,
            text="SPACE launch | P pause | R restart",
            fill="#aab0c5", font=("Courier", 12)
        )

    def _apply_level_background(self, level):
        color = LEVEL_BG_COLORS.get(level, "#1a1a2e")
        self.canvas.configure(bg=color)

    def _update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
        self.canvas.itemconfig(self.level_text, text=f"Level: {self.level}/{MAX_LEVELS}")
        self._redraw_hearts()

    def _clear_items(self, items):
        for item in items:
            self.canvas.delete(item)
        items.clear()

    def _show_start_screen(self, title="ARKANOID", message="Press SPACE to start!", hint="Left / Right = Move Paddle", level_select=False):
        self._clear_items(self.start_items)
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 60,
            text=title, fill="#f1c40f",
            font=("Courier", 42, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text=message, fill="white",
            font=("Courier", 20)
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 40,
            text=hint, fill="#aaa",
            font=("Courier", 16)
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 74,
            text="P = Pause   R = Restart", fill="#7f8c8d",
            font=("Courier", 13)
        ))
        if level_select:
            selector_y = HEIGHT // 2 + 112
            self.start_items.append(self.canvas.create_text(
                WIDTH // 2, selector_y,
                text="Choose level:", fill="#f8c471",
                font=("Courier", 15, "bold")
            ))

            level_labels = []
            for lvl in range(1, MAX_LEVELS + 1):
                if lvl == self.selected_level:
                    level_labels.append(f"[{lvl}]")
                else:
                    level_labels.append(str(lvl))

            self.start_items.append(self.canvas.create_text(
                WIDTH // 2, selector_y + 28,
                text="   ".join(level_labels), fill="#ecf0f1",
                font=("Courier", 18, "bold")
            ))
            self.start_items.append(self.canvas.create_text(
                WIDTH // 2, selector_y + 56,
                text="Up/Down or 1-9 to select level", fill="#95a5a6",
                font=("Courier", 12)
            ))
            vip_ready = self.score >= VIP_ENTRY_COST or self.vip_paid
            vip_text = "VIP 8 unlocked" if vip_ready else f"VIP 8 needs {VIP_ENTRY_COST} score"
            self.start_items.append(self.canvas.create_text(
                WIDTH // 2, selector_y + 82,
                text=vip_text, fill="#f8c471",
                font=("Courier", 12, "bold")
            ))
            char_text_parts = []
            for cid in (1, 2, 3):
                label = f"{cid}:{CHARACTERS[cid]['name']}"
                if cid == self.selected_character:
                    label = f"[{label}]"
                char_text_parts.append(label)
            self.start_items.append(self.canvas.create_text(
                WIDTH // 2, selector_y + 106,
                text="   ".join(char_text_parts), fill="#81e6d9",
                font=("Courier", 11, "bold")
            ))
            self.start_items.append(self.canvas.create_text(
                WIDTH // 2, selector_y + 126,
                text="A/D or Left/Right choose character | 0 = power in game",
                fill="#9cd3ff", font=("Courier", 11)
            ))

    # ─── Controls ───

    def _set_paddle_speed(self, speed):
        if not self.game_started and not self.game_over and not self.paused:
            self._change_selected_character(-1 if speed < 0 else 1)
            return
        self.paddle_speed = speed

    def _stop_paddle(self, direction):
        if direction == "left" and self.paddle_speed < 0:
            self.paddle_speed = 0
        elif direction == "right" and self.paddle_speed > 0:
            self.paddle_speed = 0

    def _start_game(self, event=None):
        if not self.game_started and not self.game_over:
            if not self._apply_selected_level():
                return
            self.character_id = self.selected_character
            self._apply_character_style()
            self.game_started = True
            self._clear_items(self.start_items)

    def _change_selected_character(self, delta):
        if self.game_started or self.game_over or self.paused:
            return
        self.selected_character += delta
        if self.selected_character < 1:
            self.selected_character = 3
        elif self.selected_character > 3:
            self.selected_character = 1
        self.character_id = self.selected_character
        self._apply_character_style()
        self._show_start_screen(level_select=True)

    def _ball_center(self):
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        return (bx1 + bx2) / 2, (by1 + by2) / 2

    def _nearest_bricks(self, count):
        cx, cy = self._ball_center()
        ranked = []
        for brick in self.bricks:
            x1, y1, x2, y2 = self.canvas.coords(brick["id"])
            bx = (x1 + x2) / 2
            by = (y1 + y2) / 2
            ranked.append(((bx - cx) ** 2 + (by - cy) ** 2, brick))
        ranked.sort(key=lambda pair: pair[0])
        return [brick for _, brick in ranked[:count]]

    def _collect_brick(self, brick):
        self.score += brick.get("points", 0)
        for part in brick["parts"]:
            self.canvas.delete(part)
        if brick is self.special_brick:
            self.special_brick = None
        if brick in self.bricks:
            self.bricks.remove(brick)

    def _draw_lightning_effect(self, target_bricks):
        sx, sy = self._ball_center()
        fx_items = []
        for brick in target_bricks:
            x1, y1, x2, y2 = self.canvas.coords(brick["id"])
            tx = (x1 + x2) / 2
            ty = (y1 + y2) / 2
            points = [sx, sy]
            for i in range(1, 5):
                t = i / 5
                jx = random.randint(-8, 8)
                jy = random.randint(-6, 6)
                points.extend([sx + (tx - sx) * t + jx, sy + (ty - sy) * t + jy])
            points.extend([tx, ty])
            fx_items.append(self.canvas.create_line(points, fill="#a5f3fc", width=2))
        self.root.after(140, lambda: [self.canvas.delete(item) for item in fx_items])

    def _draw_fire_effect(self, target_bricks):
        fx_items = []
        for brick in target_bricks:
            x1, y1, x2, y2 = self.canvas.coords(brick["id"])
            fx_items.append(self.canvas.create_oval(
                x1 + 4, y1 + 2, x2 - 4, y2,
                fill="#ef4444", outline=""
            ))
            fx_items.append(self.canvas.create_oval(
                x1 + 8, y1 - 2, x2 - 8, y2 - 4,
                fill="#f59e0b", outline=""
            ))
        self.root.after(170, lambda: [self.canvas.delete(item) for item in fx_items])

    def _draw_water_storm_effect(self):
        cx, cy = self._ball_center()
        ring = self.canvas.create_oval(
            cx - 20, cy - 20, cx + 20, cy + 20,
            outline="#7dd3fc", width=4
        )
        for step in range(1, 8):
            self.root.after(step * 30, lambda s=step: self.canvas.coords(
                ring,
                cx - 20 - s * 35, cy - 20 - s * 25,
                cx + 20 + s * 35, cy + 20 + s * 25,
            ))
        self.root.after(260, lambda: self.canvas.delete(ring))

    def _activate_character_power(self, event=None):
        if not self.game_started or self.game_over or self.paused or not self.bricks:
            return
        if self.level in (6, 7, 9):
            return

        if self.character_id == 1:
            targets = self._nearest_bricks(5)
            self._draw_lightning_effect(targets)
        elif self.character_id == 2:
            targets = self._nearest_bricks(5)
            self._draw_fire_effect(targets)
        else:
            targets = self.bricks[:]
            self._draw_water_storm_effect()

        removed = 0
        for brick in targets:
            if brick in self.bricks:
                self._collect_brick(brick)
                removed += 1

        if removed > 0:
            self._update_score()

        if len(self.bricks) == 0 and not self.game_over:
            self._advance_level()

    def _change_selected_level(self, delta):
        if self.game_started or self.game_over or self.paused:
            return
        new_level = self.selected_level + delta
        self.selected_level = max(1, min(MAX_LEVELS, new_level))
        self._apply_level_background(self.selected_level)
        self._show_start_screen(level_select=True)

    def _set_selected_level(self, level):
        if self.game_started or self.game_over or self.paused:
            return
        self.selected_level = max(1, min(MAX_LEVELS, level))
        self._apply_level_background(self.selected_level)
        self._show_start_screen(level_select=True)

    def _apply_selected_level(self):
        target_level = self.selected_level

        if target_level == VIP_LEVEL and not self.vip_paid:
            if self.score < VIP_ENTRY_COST:
                need = VIP_ENTRY_COST - self.score
                self._show_start_screen(
                    title="VIP LEVEL LOCKED",
                    message=f"Need {need} more score",
                    hint=f"VIP entry costs {VIP_ENTRY_COST} points",
                    level_select=True
                )
                return False
            self.score -= VIP_ENTRY_COST
            self.vip_paid = True
        elif target_level != VIP_LEVEL:
            self.vip_paid = False

        if self.level != target_level:
            self.level = target_level
        self._apply_level_background(self.level)

        for brick in self.bricks:
            for part in brick["parts"]:
                self.canvas.delete(part)
        self.bricks.clear()
        self._create_bricks()

        self.current_paddle_width = self._paddle_width_for_level()
        speed = self._ball_speed_for_level()

        self.canvas.coords(
            self.paddle,
            WIDTH // 2 - self.current_paddle_width // 2, HEIGHT - 40,
            WIDTH // 2 + self.current_paddle_width // 2, HEIGHT - 40 + PADDLE_H
        )
        self.canvas.coords(
            self.ball,
            WIDTH // 2 - BALL_R, HEIGHT - 60 - BALL_R,
            WIDTH // 2 + BALL_R, HEIGHT - 60 + BALL_R
        )
        self._sync_ball_effects()
        self.ball_dx = speed * random.choice([-1, 1])
        self.ball_dy = -speed
        self._update_score()
        return True

    def _toggle_pause(self, event=None):
        if self.game_over or not self.game_started:
            return

        self.paused = not self.paused
        if self.paused:
            self.pause_items = [
                self.canvas.create_rectangle(
                    WIDTH // 2 - 180, HEIGHT // 2 - 55,
                    WIDTH // 2 + 180, HEIGHT // 2 + 55,
                    fill="#111827", outline="#f1c40f", width=3
                ),
                self.canvas.create_text(
                    WIDTH // 2, HEIGHT // 2 - 12,
                    text="PAUSED", fill="#f1c40f",
                    font=("Courier", 30, "bold")
                ),
                self.canvas.create_text(
                    WIDTH // 2, HEIGHT // 2 + 22,
                    text="Press P to continue", fill="white",
                    font=("Courier", 16)
                ),
            ]
        else:
            self._clear_items(self.pause_items)

    def _restart_game(self, event=None):
        self.canvas.delete("all")
        self._clear_items(self.start_items)
        self._clear_items(self.pause_items)
        self._reset_state()
        self._apply_level_background(self.level)
        self._create_paddle()
        self._create_ball()
        self._create_bricks()
        self._create_ui()
        self._redraw_hearts()
        self._show_start_screen(level_select=True)

    # ─── Game loop ───

    def _game_loop(self):
        if self.game_started and not self.game_over and not self.paused:
            self._move_paddle()
            self._move_ball()
            self._update_special_brick()
            self._check_collisions()
        self.root.after(1000 // FPS, self._game_loop)

    def _update_special_brick(self):
        if self.level not in (6, 9) or not self.special_brick:
            return

        for part in self.special_brick["parts"]:
            self.canvas.move(part, self.special_brick_dx, 0)

        bx1, _, bx2, _ = self.canvas.coords(self.special_brick["id"])
        if bx1 <= 8:
            self.special_brick_dx = abs(self.special_brick_dx)
        elif bx2 >= WIDTH - 8:
            self.special_brick_dx = -abs(self.special_brick_dx)

        tick_step = 3 if self.level == 9 else 4
        self.smiley_anim_tick += 1
        if self.smiley_anim_tick % tick_step == 0:
            self.smiley_face_index = (self.smiley_face_index + 1) % len(SMILEY_FACES)
            self.canvas.itemconfig(
                self.special_brick["text_id"],
                text=SMILEY_FACES[self.smiley_face_index]
            )

    def _move_paddle(self):
        coords = self.canvas.coords(self.paddle)
        if self.paddle_speed < 0 and coords[0] > 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
        elif self.paddle_speed > 0 and coords[2] < WIDTH - 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)

    def _move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        self._sync_ball_effects()

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
            hit_pos = (bcx - (px1 + px2) / 2) / (self.current_paddle_width / 2)
            hit_pos = max(-1, min(1, hit_pos))
            angle = math.radians(30 + (1 - abs(hit_pos)) * 60)
            speed = math.sqrt(self.ball_dx**2 + self.ball_dy**2)
            speed = min(max(speed, 4), 8)
            self.ball_dx = speed * math.cos(angle) * (1 if hit_pos >= 0 else -1)
            self.ball_dy = -abs(speed * math.sin(angle))
            self.canvas.coords(self.ball, bx1, py1 - BALL_R * 2, bx2, py1)
            self._sync_ball_effects()

        # Brick collision
        for brick in self.bricks[:]:
            brx1, bry1, brx2, bry2 = self.canvas.coords(brick["id"])
            if (bx2 >= brx1 and bx1 <= brx2 and
                    by2 >= bry1 and by1 <= bry2):
                if brick.get("unbreakable"):
                    pass
                else:
                    self.score += brick["points"]
                    for part in brick["parts"]:
                        self.canvas.delete(part)
                    if brick is self.special_brick:
                        self.special_brick = None
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
            self._advance_level()

    def _ball_speed_for_level(self):
        speed = self.base_ball_speed + (self.level - 1) * BALL_SPEED_STEP
        if self.level == 9:
            speed += 0.8
        return speed

    def _paddle_width_for_level(self):
        return max(MIN_PADDLE_W, PADDLE_W - (self.level - 1) * PADDLE_SHRINK_PER_LEVEL)

    def _reset_ball(self):
        self.current_paddle_width = self._paddle_width_for_level()
        speed = self._ball_speed_for_level()
        self._apply_level_background(self.level)
        self.canvas.coords(
            self.ball,
            WIDTH // 2 - BALL_R, HEIGHT - 60 - BALL_R,
            WIDTH // 2 + BALL_R, HEIGHT - 60 + BALL_R
        )
        self._sync_ball_effects()
        self.canvas.coords(
            self.paddle,
            WIDTH // 2 - self.current_paddle_width // 2, HEIGHT - 40,
            WIDTH // 2 + self.current_paddle_width // 2, HEIGHT - 40 + PADDLE_H
        )
        self.ball_dx = speed * random.choice([-1, 1])
        self.ball_dy = -speed
        self.game_started = False
        self.paused = False
        self._show_start_screen(
            title=f"LEVEL {self.level}",
            message="Press SPACE to launch",
            hint=f"Ball speed {speed:.1f}   Paddle width {self.current_paddle_width}",
            level_select=False
        )

    def _advance_level(self):
        if self.level >= MAX_LEVELS:
            self._game_win()
            return

        self.level += 1
        self._create_bricks()
        self._update_score()
        self._reset_ball()

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
            text="GAME OVER!", fill="#e74c3c",
            font=("Courier", 32, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text=f"Final Score: {self.score}", fill="white",
            font=("Courier", 18)
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 48,
            text="Press R to restart", fill="#f8c471",
            font=("Courier", 14)
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
            text="YOU WIN!", fill="#2ecc71",
            font=("Courier", 32, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text=f"Final Score: {self.score}", fill="white",
            font=("Courier", 18)
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 48,
            text="Press R to play again", fill="#f8c471",
            font=("Courier", 14)
        )


if __name__ == "__main__":
    Arkanoid()
