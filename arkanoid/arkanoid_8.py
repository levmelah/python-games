import tkinter as tk
import random
import math

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
FLEE_RADIUS = 170
FLEE_MAX_SPEED = 2.2

BRICK_COLORS = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db"]
BRICK_POINTS = [50, 40, 30, 20, 10]


class Arkanoid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Arkanoid")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#1a1a2e")
        self.canvas.pack()

        self.score = 0
        self.lives = 3
        self.game_started = False
        self.game_over = False
        self.mouth_anim_t = 0.0

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
        self.ball = self.canvas.create_oval(
            x - BALL_R, y - BALL_R,
            x + BALL_R, y + BALL_R,
            fill="white", outline="white"
        )

    def _shade_color(self, hex_color, factor):
        """Lighten/darken a color by multiplying RGB with factor."""
        if not (isinstance(hex_color, str) and hex_color.startswith("#") and len(hex_color) == 7):
            return hex_color
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _create_bricks(self):
        self.bricks = []
        total_bricks = BRICK_ROWS * BRICK_COLS
        center_x = WIDTH / 2
        center_y = HEIGHT / 2
        total_w = BRICK_COLS * (BRICK_W + BRICK_PAD) - BRICK_PAD
        start_x = (WIDTH - total_w) // 2
        for row in range(BRICK_ROWS):
            color = BRICK_COLORS[row]
            points = BRICK_POINTS[row]
            for col in range(BRICK_COLS):
                idx = row * BRICK_COLS + col
                x1 = start_x + col * (BRICK_W + BRICK_PAD)
                y1 = TOP_OFFSET + row * (BRICK_H + BRICK_PAD)
                x2 = x1 + BRICK_W
                y2 = y1 + BRICK_H

                # 3D shadow and bevel faces.
                shadow = self.canvas.create_polygon(
                    x1 + 3, y1 + 3,
                    x2 + 4, y1 + 3,
                    x2 + 4, y2 + 4,
                    x1 + 3, y2 + 4,
                    fill="#0f1221", outline="", width=0,
                )
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color, outline=self._shade_color(color, 0.72), width=1
                )

                top_bevel = self.canvas.create_polygon(
                    x1 + 1, y1 + 1,
                    x2 - 1, y1 + 1,
                    x2 - 4, y1 + 5,
                    x1 + 4, y1 + 5,
                    fill=self._shade_color(color, 1.28), outline="", width=0,
                )
                left_bevel = self.canvas.create_polygon(
                    x1 + 1, y1 + 1,
                    x1 + 5, y1 + 4,
                    x1 + 5, y2 - 4,
                    x1 + 1, y2 - 1,
                    fill=self._shade_color(color, 0.82), outline="", width=0,
                )
                right_bevel = self.canvas.create_polygon(
                    x2 - 1, y1 + 1,
                    x2 - 5, y1 + 4,
                    x2 - 5, y2 - 4,
                    x2 - 1, y2 - 1,
                    fill=self._shade_color(color, 0.62), outline="", width=0,
                )

                mouth_ids = self._draw_mouth_on_brick(x1, y1, x2, y2)

                # Unique escape target for each brick so they scatter to different places.
                ang = (idx / max(1, total_bricks)) * math.tau
                ang += random.uniform(-0.12, 0.12)
                radius_x = random.uniform(230, 320)
                radius_y = random.uniform(120, 190)
                escape_x = center_x + math.cos(ang) * radius_x
                escape_y = center_y + math.sin(ang) * radius_y
                escape_x = max(8 + BRICK_W / 2, min(WIDTH - 8 - BRICK_W / 2, escape_x))
                escape_y = max(TOP_OFFSET - 2 + BRICK_H / 2, min(HEIGHT * 0.56 + BRICK_H / 2, escape_y))

                self.bricks.append(
                    {
                        "id": rect,
                        "points": points,
                        "decor": mouth_ids,
                        "faces": [shadow, top_bevel, left_bevel, right_bevel],
                        "escape_target": (escape_x, escape_y),
                    }
                )

    def _draw_mouth_on_brick(self, x1, y1, x2, y2):
        """Draw a stylized mouth with animated triangular teeth."""

        margin_x = 8
        margin_top = 5
        margin_bottom = 5
        left = x1 + margin_x + 2
        right = x2 - margin_x - 2
        base_top = y1 + BRICK_H * 0.45
        base_bottom = y2 - 4
        max_open = max(4.0, (base_bottom - base_top) * 0.7)

        # Eyes (style inspired by reference image).
        eye_outer_ids = []
        eye_pupils = []
        eye_shines = []
        eye_centers = []
        eye_r = 4
        for ex in (x1 + BRICK_W * 0.35, x1 + BRICK_W * 0.65):
            ey = y1 + BRICK_H * 0.26
            eye_centers.append((ex, ey))
            outer_black = self.canvas.create_oval(ex - eye_r - 2, ey - eye_r - 2, ex + eye_r + 2, ey + eye_r + 2, fill="#111111", outline="#111111", width=1)
            outer_white = self.canvas.create_oval(ex - eye_r, ey - eye_r, ex + eye_r, ey + eye_r, fill="#ffffff", outline="#111111", width=1)
            pupil = self.canvas.create_oval(ex - 2, ey - 2, ex + 2, ey + 2, fill="#111111", outline="#111111", width=1)
            shine = self.canvas.create_oval(ex - 2.2, ey - 2.0, ex - 0.7, ey - 0.6, fill="#ffffff", outline="#ffffff", width=0)
            eye_outer_ids.extend([outer_black, outer_white])
            eye_pupils.append(pupil)
            eye_shines.append(shine)

        # Outer smile outline.
        smile = self.canvas.create_arc(
            x1 + margin_x,
            y1 + margin_top,
            x2 - margin_x,
            y2 - margin_bottom,
            start=200,
            extent=140,
            style=tk.ARC,
            outline="#111111",
            width=2,
        )

        # Mouth cavity.
        teeth_top = base_top
        teeth_bottom = base_bottom
        mouth_bg = self.canvas.create_rectangle(
            left,
            teeth_top,
            right,
            teeth_bottom,
            fill="#0b0b0b",
            outline="#111111",
            width=1,
        )

        # Triangular teeth (top and bottom rows).
        tooth_count = 6
        tooth_w = (right - left) / tooth_count
        top_teeth = []
        bottom_teeth = []
        for _ in range(tooth_count):
            top_tooth = self.canvas.create_polygon(0, 0, 0, 0, 0, 0, fill="#ffffff", outline="#111111", width=1)
            bottom_tooth = self.canvas.create_polygon(0, 0, 0, 0, 0, 0, fill="#ffffff", outline="#111111", width=1)
            top_teeth.append(top_tooth)
            bottom_teeth.append(bottom_tooth)

        return {
            "smile": smile,
            "mouth_bg": mouth_bg,
            "top_teeth": top_teeth,
            "bottom_teeth": bottom_teeth,
            "eye_outer_ids": eye_outer_ids,
            "eye_pupils": eye_pupils,
            "eye_shines": eye_shines,
            "eye_centers": eye_centers,
            "tooth_count": tooth_count,
            "left": left,
            "right": right,
            "base_top": base_top,
            "base_bottom": base_bottom,
            "max_open": max_open,
            "phase": random.uniform(0.0, math.tau),
        }

    def _animate_brick_mouths(self):
        """Animate all brick mouths opening and closing."""
        self.mouth_anim_t += 0.16
        for brick in self.bricks:
            decor = brick.get("decor")
            if not isinstance(decor, dict):
                continue

            open_factor = 0.5 + 0.5 * math.sin(self.mouth_anim_t + decor["phase"])
            teeth_top = decor["base_top"] + (1.0 - open_factor) * decor["max_open"]
            teeth_bottom = decor["base_bottom"]
            if teeth_top > teeth_bottom - 2:
                teeth_top = teeth_bottom - 2

            self.canvas.coords(decor["mouth_bg"], decor["left"], teeth_top, decor["right"], teeth_bottom)

            left = decor["left"]
            right = decor["right"]
            tooth_count = decor["tooth_count"]
            tooth_w = (right - left) / tooth_count
            mid_y = (teeth_top + teeth_bottom) / 2
            tooth_gap = 1.5

            for i in range(tooth_count):
                tx1 = left + i * tooth_w + tooth_gap
                tx2 = left + (i + 1) * tooth_w - tooth_gap
                txm = (tx1 + tx2) / 2

                top_tip_y = mid_y - 1.2
                self.canvas.coords(decor["top_teeth"][i], tx1, teeth_top, tx2, teeth_top, txm, top_tip_y)

                bottom_tip_y = mid_y + 1.2
                self.canvas.coords(decor["bottom_teeth"][i], tx1, teeth_bottom, tx2, teeth_bottom, txm, bottom_tip_y)

            # Subtle eye movement so the bricks feel alive.
            for i, (cx, cy) in enumerate(decor.get("eye_centers", [])):
                dx = math.sin(self.mouth_anim_t * 1.3 + decor["phase"] + i * 0.8) * 0.9
                dy = math.cos(self.mouth_anim_t * 1.1 + decor["phase"] + i * 0.6) * 0.5
                px = cx + dx
                py = cy + dy
                self.canvas.coords(decor["eye_pupils"][i], px - 2, py - 2, px + 2, py + 2)
                self.canvas.coords(decor["eye_shines"][i], px - 2.2, py - 2.0, px - 0.7, py - 0.6)

            arc_extent = 120 + open_factor * 40
            arc_start = 200 - open_factor * 8
            self.canvas.itemconfig(decor["smile"], start=arc_start, extent=arc_extent)

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
            text="ARKANOID", fill="#f1c40f",
            font=("Courier", 42, "bold")
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text="Press SPACE to start!", fill="white",
            font=("Courier", 20)
        ))
        self.start_items.append(self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 40,
            text="← → = Move Paddle", fill="#aaa",
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
        if not self.game_over:
            self._animate_brick_mouths()
        if self.game_started and not self.game_over:
            self._flee_bricks_from_ball()
            self._move_paddle()
            self._move_ball()
            self._check_collisions()
        self.root.after(1000 // FPS, self._game_loop)

    def _move_brick_with_decor(self, brick, dx, dy):
        """Move one brick and all attached face parts together."""
        if dx == 0 and dy == 0:
            return

        self.canvas.move(brick["id"], dx, dy)
        for face_id in brick.get("faces", []):
            self.canvas.move(face_id, dx, dy)
        decor = brick.get("decor")
        if not isinstance(decor, dict):
            return

        self.canvas.move(decor.get("smile"), dx, dy)
        self.canvas.move(decor.get("mouth_bg"), dx, dy)
        for item_id in decor.get("top_teeth", []):
            self.canvas.move(item_id, dx, dy)
        for item_id in decor.get("bottom_teeth", []):
            self.canvas.move(item_id, dx, dy)
        for item_id in decor.get("eye_outer_ids", []):
            self.canvas.move(item_id, dx, dy)
        for item_id in decor.get("eye_pupils", []):
            self.canvas.move(item_id, dx, dy)
        for item_id in decor.get("eye_shines", []):
            self.canvas.move(item_id, dx, dy)

        # Keep animation anchors synced with moved brick.
        decor["left"] += dx
        decor["right"] += dx
        decor["base_top"] += dy
        decor["base_bottom"] += dy
        centers = []
        for cx, cy in decor.get("eye_centers", []):
            centers.append((cx + dx, cy + dy))
        decor["eye_centers"] = centers

    def _flee_bricks_from_ball(self):
        """Make bricks run to their own unique escape targets when ball gets close."""
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        ball_x = (bx1 + bx2) / 2
        ball_y = (by1 + by2) / 2

        min_x = 6
        max_x = WIDTH - BRICK_W - 6
        min_y = TOP_OFFSET - 8
        max_y = int(HEIGHT * 0.56)

        for brick in self.bricks:
            x1, y1, x2, y2 = self.canvas.coords(brick["id"] )
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2

            vx = cx - ball_x
            vy = cy - ball_y
            dist = math.hypot(vx, vy)
            if dist <= 0.001 or dist > FLEE_RADIUS:
                continue

            tx, ty = brick.get("escape_target", (cx, cy))
            to_tx = tx - cx
            to_ty = ty - cy
            to_target_dist = max(0.001, math.hypot(to_tx, to_ty))

            away_x = vx / dist
            away_y = vy / dist

            threat = 1.0 - (dist / FLEE_RADIUS)
            speed = 0.35 + FLEE_MAX_SPEED * threat

            # Base motion toward each brick's personal target.
            target_dir_x = to_tx / to_target_dist
            target_dir_y = to_ty / to_target_dist

            # Prevent any target that would send the brick toward the ball.
            # If target direction points toward the ball, mirror it to an away direction.
            if (target_dir_x * away_x + target_dir_y * away_y) < 0.0:
                target_dir_x = away_x
                target_dir_y = away_y

            dx = target_dir_x * speed
            dy = target_dir_y * speed

            # Add slight push directly away from ball so the reaction still feels natural.
            away_mix = 0.35
            dx += away_x * speed * away_mix
            dy += away_y * speed * away_mix

            # Final safety: never allow movement toward the ball.
            if (dx * away_x + dy * away_y) <= 0.0:
                dx = away_x * speed
                dy = away_y * speed

            # Stay inside gameplay bounds.
            nx1 = x1 + dx
            ny1 = y1 + dy
            if nx1 < min_x:
                dx += (min_x - nx1)
            elif nx1 > max_x:
                dx -= (nx1 - max_x)

            if ny1 < min_y:
                dy += (min_y - ny1)
            elif ny1 > max_y:
                dy -= (ny1 - max_y)

            self._move_brick_with_decor(brick, dx, dy)

    def _move_paddle(self):
        coords = self.canvas.coords(self.paddle)
        if self.paddle_speed < 0 and coords[0] > 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)
        elif self.paddle_speed > 0 and coords[2] < WIDTH - 5:
            self.canvas.move(self.paddle, self.paddle_speed, 0)

    def _move_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)

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

        # Brick collision
        for brick in self.bricks[:]:
            brx1, bry1, brx2, bry2 = self.canvas.coords(brick["id"])
            if (bx2 >= brx1 and bx1 <= brx2 and
                    by2 >= bry1 and by1 <= bry2):
                self.score += brick["points"]
                self.canvas.delete(brick["id"])
                for face_id in brick.get("faces", []):
                    self.canvas.delete(face_id)
                decor = brick.get("decor")
                if isinstance(decor, dict):
                    self.canvas.delete(decor.get("smile"))
                    self.canvas.delete(decor.get("mouth_bg"))
                    for eye_id in decor.get("eye_outer_ids", []):
                        self.canvas.delete(eye_id)
                    for pupil_id in decor.get("eye_pupils", []):
                        self.canvas.delete(pupil_id)
                    for shine_id in decor.get("eye_shines", []):
                        self.canvas.delete(shine_id)
                    for tooth_id in decor.get("top_teeth", []):
                        self.canvas.delete(tooth_id)
                    for tooth_id in decor.get("bottom_teeth", []):
                        self.canvas.delete(tooth_id)
                else:
                    for decor_id in brick.get("decor", []):
                        self.canvas.delete(decor_id)
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
            self.paddle,
            WIDTH // 2 - PADDLE_W // 2, HEIGHT - 40,
            WIDTH // 2 + PADDLE_W // 2, HEIGHT - 40 + PADDLE_H
        )
        self.ball_dx = 4 * random.choice([-1, 1])
        self.ball_dy = -4
        self.game_started = False
        msg = self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text="Press SPACE to continue", fill="white",
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
            text="GAME OVER!", fill="#e74c3c",
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
            text="YOU WIN!", fill="#2ecc71",
            font=("Courier", 32, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 20,
            text=f"Final Score: {self.score}", fill="white",
            font=("Courier", 18)
        )


if __name__ == "__main__":
    Arkanoid()
