import os
import tkinter as tk
import random
import math
from xml.etree.ElementInclude import include

try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

try:
    from PIL import ImageTk
    PIL_IMAGETK_AVAILABLE = True
except Exception:
    PIL_IMAGETK_AVAILABLE = False

# קבועי משחק
WIDTH = 1500
HEIGHT = 900
PADDLE_WIDTH = 14
PADDLE_HEIGHT = 100
BALL_SIZE = 16
INITIAL_BALL_SPEED = 7
SPEED_ACCELERATION = 1.07  # מהיר יותר!
AI_SPEED = 6
PADDLE_SPEED = 8
WINNING_SCORE = 5

class NeonPonk:
    def __init__(self, root):
        self.root = root
        root.title('⚡ NEON PONK 2026 ⚡')
        root.resizable(False, False)

        # קנבס שחור למראה ניאון עתידני
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='#0b0c10', highlightthickness=0)
        self.canvas.pack()

        self.background_photo = None
        self.bg_image_id = None
        self.neon_lines = []
        self.neon_stars = []
        self.chat_bubbles = []
        self.pulse_phase = 0
        self.obstacle_glow_phase = 0
        self.ai_blink_counter = 120

        self.draw_background_image()

        self.player_score = 0
        self.ai_score = 0
        self.current_ball_speed = INITIAL_BALL_SPEED
        self.is_paused = False
        self.game_over = False
        
        # מערכות אפקטים
        self.trail_particles = []
        self.explosion_particles = []
        self.shake_remaining = 0
        self.shake_intensity = 0

        self.keys_pressed = {"Up": False, "Down": False}
        
        # מכשולים
        self.obstacles = []
        self.obstacle_rects = []
        self.neon_lines = []
        self.neon_stars = []
        self.chat_bubbles = []
        self.pulse_phase = 0
        self.obstacle_glow_phase = 0
        self.ai_blink_counter = 120

        # AI face (initialize early so setup can draw it)
        self.ai_face_ids = []
        self.ai_face_state = 'neutral'

        self.setup_game_elements()
        self.bind_events()
        
        self.reset_ball(direction=random.choice([1, -1]))
        self.update_game()

        # צ'אט
        self.chat_entry = None
        self.chat_button = None
        self.chat_toggle_button = None
        self.chat_active = False
        self.chat_texts = []

    def setup_game_elements(self):
        # רשת ניאון מרכזית
        for y in range(10, HEIGHT, 25):
            self.canvas.create_rectangle(WIDTH // 2 - 1, y, WIDTH // 2 + 1, y + 12, fill='#1f2833', outline='')

        # יצירת מכשולים
        self.create_obstacles()

        # מטליות ניאון זוהרות
        self.player_paddle = self.canvas.create_rectangle(
            35, HEIGHT // 2 - PADDLE_HEIGHT // 2,
            35 + PADDLE_WIDTH, HEIGHT // 2 + PADDLE_HEIGHT // 2,
            fill='#00f5ff', outline='#00f5ff', width=2  # ציאן זוהר
        )
        self.ai_paddle = self.canvas.create_rectangle(
            WIDTH - 35 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2,
            WIDTH - 35, HEIGHT // 2 + PADDLE_HEIGHT // 2,
            fill='#ff007f', outline='#ff007f', width=2  # ורוד מגנטה זוהר
        )
        
        # כדור
        self.ball = self.canvas.create_oval(0, 0, BALL_SIZE, BALL_SIZE, fill='#ffffff', outline='#00f5ff', width=2)

        # טקסטים בעיצוב סייבר
        self.score_text = self.canvas.create_text(
            WIDTH // 2, 50,
            text=self.get_score_text(),
            font=('Impact', 36),
            fill='#ffffff'
        )
        self.speed_text = self.canvas.create_text(
            WIDTH // 2, 100,
            text="SPEED: 100%",
            font=('Consolas', 11, 'bold'),
            fill='#45f3ff'
        )
        self.hint_text = self.canvas.create_text(
            WIDTH // 2, HEIGHT - 25,
            text='▲▼ : MOVE  |  SPACE : PAUSE  |  C : CHAT',
            font=('Consolas', 11, 'bold'),
            fill='#45f3ff'
        )
        
        self.overlay_rect = None
        self.overlay_text = None
        self.restart_button = None
        # כפתור צ'אט גלוי תמיד
        self.chat_toggle_button = tk.Button(
            self.root, text='CHAT (C)', font=('Consolas', 10, 'bold'),
            bg='#1f2833', fg='white', bd=0, command=self.open_chat
        )
        self.canvas.create_window(WIDTH//2 + 300, HEIGHT - 60, window=self.chat_toggle_button, width=100)
        # draw initial AI face
        self.draw_ai_face('neutral')

    def create_obstacles(self):
        """יצירת מכשולים בעיצוב ניאון"""
        obstacle_width = 80
        obstacle_height = 20
        gap = 100
        
        # מכשולים בשורות שונות
        obstacle_configs = [
            (WIDTH // 2 - 200, HEIGHT // 4),         # שורה עליונה
            (WIDTH // 2 + 100, HEIGHT // 4 + 50),    # שורה עליונה ימין
            (WIDTH // 2 - 100, HEIGHT // 2),         # אמצע
            (WIDTH // 2 + 150, HEIGHT // 2 - 30),    # אמצע ימין
            (WIDTH // 2 - 250, HEIGHT // 4 * 3),     # שורה תחתונה
            (WIDTH // 2 + 50, HEIGHT // 4 * 3 + 40), # שורה תחתונה ימין
        ]
        
        for x, y in obstacle_configs:
            # רקטנגל ניאון זוהר
            rect_id = self.canvas.create_rectangle(
                x, y, x + obstacle_width, y + obstacle_height,
                fill='#ff00ff', outline='#00ffff', width=2
            )
            self.obstacles.append(rect_id)
            self.obstacle_rects.append((x, y, x + obstacle_width, y + obstacle_height))

    def bind_events(self):
        self.root.bind('<KeyPress-Up>', lambda e: self.set_key_state("Up", True))
        self.root.bind('<KeyRelease-Up>', lambda e: self.set_key_state("Up", False))
        self.root.bind('<KeyPress-Down>', lambda e: self.set_key_state("Down", True))
        self.root.bind('<KeyRelease-Down>', lambda e: self.set_key_state("Down", False))
        self.root.bind('<space>', lambda e: self.toggle_pause())
        # הקשה על 'c' לפתיחת חלון צ'אט
        self.root.bind('<KeyPress-c>', lambda e: self.open_chat())

    def set_key_state(self, key, state):
        self.keys_pressed[key] = state

    def toggle_pause(self):
        if self.game_over: return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.show_overlay("SYSTEM PAUSED\nPRESS SPACE TO RESUME")
        else:
            self.hide_overlay()

    def trigger_shake(self, intensity=8, duration=10):
        # Screen shake disabled per user request.
        return

    def apply_screen_shake(self):
        # Screen shake disabled.
        return

    def create_explosion(self, x, y, color):
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 7)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            p = self.canvas.create_oval(x-3, y-3, x+3, y+3, fill=color, outline='')
            self.explosion_particles.append({'id': p, 'dx': dx, 'dy': dy, 'life': 20})

    # ----- AI face drawing -----
    def clear_ai_face(self):
        for i in self.ai_face_ids:
            try:
                self.canvas.delete(i)
            except Exception:
                pass
        self.ai_face_ids = []

    def draw_ai_face(self, state='neutral'):
        # remove previous
        self.clear_ai_face()
        self.ai_face_state = state
        cx = WIDTH - 120
        cy = 60
        r = 40
        # face background
        face_id = self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill='#ff8fcf', outline='#ff007f', width=3)
        self.ai_face_ids.append(face_id)

        # eyes
        if state == 'happy':
            # smiling eyes (arcs)
            left_eye = self.canvas.create_arc(cx-20, cy-10, cx-6, cy+6, start=0, extent=180, style='arc', width=3)
            right_eye = self.canvas.create_arc(cx+6, cy-10, cx+20, cy+6, start=0, extent=180, style='arc', width=3)
            mouth = self.canvas.create_arc(cx-18, cy-2, cx+18, cy+26, start=180, extent=180, style='arc', width=4)
            self.ai_face_ids += [left_eye, right_eye, mouth]
        elif state == 'angry':
            # angry slanted brows and frown
            brow1 = self.canvas.create_line(cx-26, cy-22, cx-6, cy-12, width=4, fill='#660033')
            brow2 = self.canvas.create_line(cx+26, cy-22, cx+6, cy-12, width=4, fill='#660033')
            left_eye = self.canvas.create_oval(cx-18, cy-6, cx-12, cy, fill='#330011')
            right_eye = self.canvas.create_oval(cx+12, cy-6, cx+18, cy, fill='#330011')
            mouth = self.canvas.create_arc(cx-18, cy+2, cx+18, cy+24, start=0, extent=180, style='arc', width=4)
            self.ai_face_ids += [brow1, brow2, left_eye, right_eye, mouth]
        elif state == 'blink':
            left_eye = self.canvas.create_line(cx-18, cy-7, cx-12, cy-7, width=4, fill='#330011')
            right_eye = self.canvas.create_line(cx+12, cy-7, cx+18, cy-7, width=4, fill='#330011')
            mouth = self.canvas.create_line(cx-14, cy+12, cx+14, cy+12, width=3)
            self.ai_face_ids += [left_eye, right_eye, mouth]
        else:
            # neutral: simple eyes and straight mouth
            left_eye = self.canvas.create_oval(cx-18, cy-10, cx-12, cy-4, fill='#330011')
            right_eye = self.canvas.create_oval(cx+12, cy-10, cx+18, cy-4, fill='#330011')
            mouth = self.canvas.create_line(cx-14, cy+12, cx+14, cy+12, width=3)
            self.ai_face_ids += [left_eye, right_eye, mouth]

    def set_ai_face_temporary(self, state, ms=1500):
        self.draw_ai_face(state)
        self.root.after(ms, lambda: self.draw_ai_face('neutral'))

    def update_particles(self):
        # 1. עדכון שובל הכדור (Motion Trail)
        ball_coords = self.canvas.coords(self.ball)
        if ball_coords and not self.is_paused and not self.game_over:
            bx = (ball_coords[0] + ball_coords[2]) / 2
            by = (ball_coords[1] + ball_coords[3]) / 2
            # יצירת חלקיק שובל חדש
            color = '#00f5ff' if self.ball_dx > 0 else '#ff007f'
            p = self.canvas.create_oval(bx-4, by-4, bx+4, by+4, fill=color, outline='')
            self.trail_particles.append({'id': p, 'life': 1.0})

        # דעיכת שובל
        for p in self.trail_particles[:]:
            p['life'] -= 0.1
            if p['life'] <= 0:
                self.canvas.delete(p['id'])
                self.trail_particles.remove(p)
            else:
                # שינוי גודל החלקיק שייראה כאילו הוא נעלם
                coords = self.canvas.coords(p['id'])
                if coords:
                    cx, cy = (coords[0]+coords[2])/2, (coords[1]+coords[3])/2
                    r = 4 * p['life']
                    self.canvas.coords(p['id'], cx-r, cy-r, cx+r, cy+r)

        # 2. עדכון פיצוצים
        for p in self.explosion_particles[:]:
            self.canvas.move(p['id'], p['dx'], p['dy'])
            p['life'] -= 1
            if p['life'] <= 0:
                self.canvas.delete(p['id'])
                self.explosion_particles.remove(p)

    def draw_background_image(self):
        self.neon_lines.clear()
        self.neon_stars.clear()
        if PIL_AVAILABLE and PIL_IMAGETK_AVAILABLE:
            image_path = os.path.join(os.path.dirname(__file__), 'img', 'images (1).jpeg')
            try:
                image = Image.open(image_path)
                image = image.resize((WIDTH, HEIGHT), Image.ANTIALIAS)
                self.background_photo = ImageTk.PhotoImage(image)
                self.bg_image_id = self.canvas.create_image(0, 0, image=self.background_photo, anchor='nw')
                self.canvas.lower(self.bg_image_id)
                return
            except Exception:
                pass
        self.draw_neon_background()

    def draw_neon_background(self):
        self.neon_lines.clear()
        self.neon_stars.clear()
        for i in range(14):
            x = 60 + i * 100
            line_id = self.canvas.create_line(x, 0, x, HEIGHT, fill='#09141a', width=2)
            self.neon_lines.append((line_id, x))

        for _ in range(25):
            x = random.randint(40, WIDTH - 40)
            y = random.randint(40, HEIGHT - 120)
            r = random.randint(2, 4)
            star_id = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill='#1f8cff', outline='')
            self.neon_stars.append((star_id, x, y, r))

    def animate_neon_background(self):
        self.pulse_phase += 0.06
        for idx, (line_id, x) in enumerate(self.neon_lines):
            green = 110 + int(60 * math.sin(self.pulse_phase + idx * 0.4))
            blue = 180 + int(60 * math.cos(self.pulse_phase + idx * 0.4))
            green = max(0, min(255, green))
            blue = max(0, min(255, blue))
            color = f'#0{green:02x}{blue:02x}'
            self.canvas.itemconfigure(line_id, fill=color)

        for star_id, x, y, r in self.neon_stars:
            alpha = 170 + int(60 * math.sin(self.pulse_phase * 1.2 + x * 0.03))
            alpha = max(0, min(255, alpha))
            color = f'#1{alpha:02x}ff'
            try:
                self.canvas.itemconfigure(star_id, fill=color)
            except Exception:
                pass

    def animate_obstacles(self):
        self.obstacle_glow_phase += 0.08
        for idx, obstacle in enumerate(self.obstacles):
            glow = 150 + int(60 * math.sin(self.obstacle_glow_phase + idx * 0.7))
            blue = 120 + int(80 * math.cos(self.obstacle_glow_phase + idx * 0.7))
            blue = max(0, min(255, blue))
            glow = max(0, min(255, glow))
            color = f'#ff{glow:02x}{blue:02x}'
            try:
                self.canvas.itemconfigure(obstacle, fill=color, outline=color)
            except Exception:
                pass

    def animate_ui_texts(self):
        intensity = 180 + int(40 * math.sin(self.pulse_phase * 1.3))
        intensity = max(0, min(255, intensity))
        color = f'#{intensity:02x}{intensity:02x}{255:02x}'
        try:
            self.canvas.itemconfigure(self.speed_text, fill=color)
            self.canvas.itemconfigure(self.hint_text, fill=color)
        except Exception:
            pass

    def animate_ai_face(self):
        if self.ai_face_state == 'neutral':
            self.ai_blink_counter -= 1
            if self.ai_blink_counter <= 0:
                self.draw_ai_face('blink')
                self.root.after(130, lambda: self.draw_ai_face('neutral'))
                self.ai_blink_counter = random.randint(100, 180)

    def animate_chat_bubbles(self):
        for bubble in self.chat_bubbles[:]:
            bubble['life'] -= 1
            if bubble['life'] <= 0:
                try:
                    self.canvas.delete(bubble['id'])
                except Exception:
                    pass
                self.chat_bubbles.remove(bubble)
                continue
            fade = int(255 * (bubble['life'] / 40))
            if bubble['color'] == '#00f5ff':
                fill = f'#00{fade:02x}{fade:02x}'
            else:
                fill = f'#{fade:02x}00{fade:02x}'
            try:
                self.canvas.itemconfigure(bubble['id'], fill=fill)
            except Exception:
                pass

        self.chat_bubbles = [b for b in self.chat_bubbles if b['life'] > 0 and self.canvas.coords(b['id'])]

    def show_overlay(self, message, show_restart=False):
        self.hide_overlay()
        self.overlay_rect = self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill='#0b0c10', stipple='gray75')
        self.overlay_text = self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - (40 if show_restart else 0),
            text=message, font=('Impact', 28), fill='#ffffff', justify='center'
        )
        if show_restart:
            self.restart_button = tk.Button(
                self.root, text="REBOOT SYSTEM", font=('Consolas', 12, 'bold'),
                bg='#00f5ff', fg='#0b0c10', activebackground='#ff007f', activeforeground='white',
                command=self.start_new_game, bd=0, padx=25, pady=12
            )
            self.canvas.create_window(WIDTH // 2, HEIGHT // 2 + 60, window=self.restart_button)

    def hide_overlay(self):
        if self.overlay_rect: self.canvas.delete(self.overlay_rect); self.overlay_rect = None
        if self.overlay_text: self.canvas.delete(self.overlay_text); self.overlay_text = None
        if self.restart_button: self.restart_button.destroy(); self.restart_button = None

    def start_new_game(self):
        self.player_score = 0
        self.ai_score = 0
        self.game_over = False
        self.is_paused = False
        self.canvas.itemconfigure(self.score_text, text=self.get_score_text())
        self.hide_overlay()
        self.reset_ball(direction=random.choice([1, -1]))

    # ----- Chat / talk to enemy -----
    def open_chat(self):
        if self.chat_active or self.game_over:
            return
        self.chat_active = True
        # עצור את המשחק בזמן כתיבה
        self.is_paused = True

        self.chat_entry = tk.Entry(self.root, font=('Consolas', 12))
        self.chat_button = tk.Button(self.root, text='SEND', command=self.send_chat_message, font=('Consolas', 10, 'bold'))
        # מיקום חלון הצ'אט בתחתית המסך
        self.canvas.create_window(WIDTH//2 - 120, HEIGHT - 60, window=self.chat_entry, width=360)
        self.canvas.create_window(WIDTH//2 + 180, HEIGHT - 60, window=self.chat_button, width=80)
        self.chat_entry.focus_set()
        # שליחת הודעה בלחיצה על Enter
        self.chat_entry.bind('<Return>', lambda e: self.send_chat_message())

    def close_chat(self):
        if self.chat_entry:
            try:
                self.chat_entry.destroy()
            except Exception:
                pass
            self.chat_entry = None
        if self.chat_button:
            try:
                self.chat_button.destroy()
            except Exception:
                pass
            self.chat_button = None
        self.chat_active = False
        self.is_paused = False

    def send_chat_message(self):
        if not self.chat_entry:
            return
        msg = self.chat_entry.get().strip()
        if not msg:
            self.close_chat()
            return
        # הצגת הודעת השחקן משמאל
        self.display_chat_message(msg, sender='player')
        self.close_chat()
        # תגובת AI מתוזמנת
        self.root.after(700, lambda: self.ai_send_reply(msg))

    def display_chat_message(self, text, sender='player'):
        # קבע מיקום ליד המטלות
        if sender == 'player':
            x1, y1, x2, y2 = self.canvas.coords(self.player_paddle)
            x = x2 + 120
            y = (y1 + y2) / 2
            color = '#00f5ff'
        else:
            x1, y1, x2, y2 = self.canvas.coords(self.ai_paddle)
            x = x1 - 120
            y = (y1 + y2) / 2
            color = '#ff007f'

        txt_id = self.canvas.create_text(x, y, text=text, font=('Consolas', 12, 'bold'), fill=color, anchor='center')
        self.chat_texts.append(txt_id)
        self.chat_bubbles.append({'id': txt_id, 'life': 240, 'color': color})
        # הסרה אוטומטית אחרי זמן קצר
        self.root.after(4000, lambda: self._remove_chat_text(txt_id))

    def _remove_chat_text(self, txt_id):
        try:
            self.canvas.delete(txt_id)
            if txt_id in self.chat_texts:
                self.chat_texts.remove(txt_id)
        except Exception:
            pass

    def ai_send_reply(self, player_msg):
        reply = self.ai_reply_logic(player_msg)
        self.display_chat_message(reply, sender='ai')

    def ai_reply_logic(self, player_msg):
        # Longer English replies; avoid answering 'why' questions
        msg = player_msg.lower()
        # If player asks 'why' (English or Hebrew), refuse to explain
        if 'why' in msg or 'למה' in msg:
            return "I won't explain my reasons — let's keep the focus on the game."

        greetings = [
            'Hello. Ready for the challenge. I hope you brought your best moves; this will be fun.',
            'Hey there. I am ready — let the match begin. Give it your all and I will respond in kind.'
        ]

        small_talk = [
            'All good — getting warmed up to play. Expect a fast match, so stay sharp and react quickly.',
            'I am warmed up and focused. Let us play — no holding back now.'
        ]

        provocation = [
            "I'll try to stop you. Don't underestimate me; I learn from each round and adapt.",
            'Bring it on. I will counter your strategies and press the advantage when I can.'
        ]

        default_long = [
            "I'm going to win! This is going to be intense; make every hit count.",
            'Tell me your strategy... then watch me try to counter it. Good games are about adaptation.',
            'This will be an interesting match. Expect close calls and quick comebacks.'
        ]

        if any(w in msg for w in ['hi', 'hello', 'hey']):
            return random.choice(greetings)
        if any(w in msg for w in ["what's up", 'what is up', 'what', 'how are you', 'how']):
            return random.choice(small_talk)
        if any(w in msg for w in ['give me', 'show me', 'win', 'beat']):
            return random.choice(provocation)

        return random.choice(default_long)

    def get_score_text(self):
        return f'{self.player_score}   I   {self.ai_score}'

    def move_player(self):
        dy = 0
        if self.keys_pressed["Up"]: dy -= PADDLE_SPEED
        if self.keys_pressed["Down"]: dy += PADDLE_SPEED

        if dy != 0:
            x1, y1, x2, y2 = self.canvas.coords(self.player_paddle)
            if y1 + dy < 0: dy = -y1
            elif y2 + dy > HEIGHT: dy = HEIGHT - y2
            self.canvas.move(self.player_paddle, 0, dy)

    def update_ai(self):
        ball_coords = self.canvas.coords(self.ball)
        if not ball_coords: return
        bx1, by1, bx2, by2 = ball_coords
        ai_x1, ai_y1, ai_x2, ai_y2 = self.canvas.coords(self.ai_paddle)
        
        ball_center = (by1 + by2) / 2
        ai_center = (ai_y1 + ai_y2) / 2

        # בדיקה אם יש מכשול בדרך של ה-AI
        obstacle_ahead = self.check_obstacles_in_ai_path(ai_y1, ai_y2)

        if self.ball_dx > 0:
            if obstacle_ahead:
                # התחמק מהמכשול
                dy = self.get_obstacle_avoidance_move(ai_y1, ai_y2)
            else:
                # תנועה רגילה לעבר הכדור
                if ball_center < ai_center - 15:
                    dy = -AI_SPEED
                elif ball_center > ai_center + 15:
                    dy = AI_SPEED
                else:
                    dy = 0
        else:
            dy = 0

        if ai_y1 + dy < 0:
            dy = -ai_y1
        elif ai_y2 + dy > HEIGHT:
            dy = HEIGHT - ai_y2
        self.canvas.move(self.ai_paddle, 0, dy)

    def check_obstacles_in_ai_path(self, ai_y1, ai_y2):
        """בדיקה אם יש מכשול בדרך של ה-AI"""
        padding = 40
        for ox1, oy1, ox2, oy2 in self.obstacle_rects:
            # בדוק אם מכשול קרוב לעבר ה-AI
            if ox1 > WIDTH - 35 - PADDLE_WIDTH - 150:
                # בדוק אם המכשול חוצה את Y של ה-AI
                if not (ai_y2 + padding < oy1 or ai_y1 - padding > oy2):
                    return True
        return False

    def get_obstacle_avoidance_move(self, ai_y1, ai_y2):
        """חישוב תנועה כדי להתחמק ממכשול"""
        ai_center = (ai_y1 + ai_y2) / 2
        
        # מצא את המכשולים הקרובים
        closest_obstacle = None
        min_dist = float('inf')
        
        for ox1, oy1, ox2, oy2 in self.obstacle_rects:
            if ox1 > WIDTH - 35 - PADDLE_WIDTH - 150:
                obstacle_center = (oy1 + oy2) / 2
                dist = abs(ai_center - obstacle_center)
                if dist < min_dist:
                    min_dist = dist
                    closest_obstacle = (oy1, oy2, obstacle_center)
        
        if closest_obstacle:
            oy1, oy2, obstacle_center = closest_obstacle
            # תנוע למרחק מהמכשול
            if ai_center < obstacle_center:
                return -AI_SPEED
            else:
                return AI_SPEED
        
        return 0

    def reset_ball(self, direction):
        self.current_ball_speed = INITIAL_BALL_SPEED
        self.canvas.coords(
            self.ball,
            WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2 - BALL_SIZE // 2,
            WIDTH // 2 + BALL_SIZE // 2, HEIGHT // 2 + BALL_SIZE // 2,
        )
        self.ball_dx = self.current_ball_speed * direction
        self.ball_dy = random.choice([-4, -2, 2, 4])
        self.update_speed_ui()

    def update_speed_ui(self):
        pct = int((self.current_ball_speed / INITIAL_BALL_SPEED) * 100)
        self.canvas.itemconfigure(self.speed_text, text=f"BALL SPEED: {pct}%")

    def check_game_over(self):
        if self.player_score >= WINNING_SCORE:
            self.game_over = True
            self.show_overlay("VICTORY\nHUMAN WINS THE MATCH 🎉", show_restart=True)
            return True
        elif self.ai_score >= WINNING_SCORE:
            self.game_over = True
            self.show_overlay("DEFEAT\nAI DOMINATION INITIALIZED 🤖", show_restart=True)
            return True
        return False

    def update_game(self):
        self.apply_screen_shake()
        self.update_particles()
        self.animate_neon_background()
        self.animate_obstacles()
        self.animate_ui_texts()
        self.animate_ai_face()
        self.animate_chat_bubbles()

        if not self.is_paused and not self.game_over:
            self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
            self.move_player()
            self.update_ai()

            ball_coords = self.canvas.coords(self.ball)
            if not ball_coords:
                return
            bx1, by1, bx2, by2 = ball_coords

            # קירות עליון ותחתון
            if by1 <= 0:
                self.ball_dy = abs(self.ball_dy)
                self.trigger_shake(intensity=3, duration=4)
            elif by2 >= HEIGHT:
                self.ball_dy = -abs(self.ball_dy)
                self.trigger_shake(intensity=3, duration=4)

            # בדיקת התנגשות עם מכשולים
            self.check_obstacle_collision(bx1, by1, bx2, by2)

            player_x1, player_y1, player_x2, player_y2 = self.canvas.coords(self.player_paddle)
            ai_x1, ai_y1, ai_x2, ai_y2 = self.canvas.coords(self.ai_paddle)

            # פגיעה בשחקן
            if self.ball_dx < 0 and self.check_collision(player_x1, player_y1, player_x2, player_y2, bx1, by1, bx2, by2):
                self.current_ball_speed *= SPEED_ACCELERATION
                self.ball_dx = abs(self.ball_dx) * SPEED_ACCELERATION
                self.adjust_ball_angle(player_y1, player_y2, by1, by2)
                self.trigger_shake(intensity=10, duration=8)  # רעידה חזקה בפגיעה במטלית
                self.update_speed_ui()

            # פגיעה במחשב
            elif self.ball_dx > 0 and self.check_collision(ai_x1, ai_y1, ai_x2, ai_y2, bx1, by1, bx2, by2):
                self.current_ball_speed *= SPEED_ACCELERATION
                self.ball_dx = -abs(self.ball_dx) * SPEED_ACCELERATION
                self.adjust_ball_angle(ai_y1, ai_y2, by1, by2)
                self.trigger_shake(intensity=10, duration=8)
                self.update_speed_ui()

            # שערים ופסילות
            if bx1 <= 0:
                self.create_explosion((bx1 + bx2) / 2, (by1 + by2) / 2, '#ff007f')
                self.ai_score += 1
                # AI is happy when it scores
                try:
                    self.set_ai_face_temporary('happy', ms=1800)
                except Exception:
                    pass
                self.canvas.itemconfigure(self.score_text, text=self.get_score_text())
                self.trigger_shake(intensity=20, duration=15)
                if not self.check_game_over():
                    self.reset_ball(direction=1)
            elif bx2 >= WIDTH:
                self.create_explosion((bx1 + bx2) / 2, (by1 + by2) / 2, '#00f5ff')
                self.player_score += 1
                # AI is angry when player scores
                try:
                    self.set_ai_face_temporary('angry', ms=1800)
                except Exception:
                    pass
                self.canvas.itemconfigure(self.score_text, text=self.get_score_text())
                self.trigger_shake(intensity=20, duration=15)
                if not self.check_game_over():
                    self.reset_ball(direction=-1)

        self.root.after(16, self.update_game)

    def check_collision(self, px1, py1, px2, py2, bx1, by1, bx2, by2):
        return not (bx2 < px1 or bx1 > px2 or by2 < py1 or by1 > py2)

    def check_obstacle_collision(self, bx1, by1, bx2, by2):
        """בדיקת התנגשות כדור עם מכשול"""
        for ox1, oy1, ox2, oy2 in self.obstacle_rects:
            if self.check_collision(ox1, oy1, ox2, oy2, bx1, by1, bx2, by2):
                # קביעת כיוון הרתע
                ball_center_x = (bx1 + bx2) / 2
                ball_center_y = (by1 + by2) / 2
                obstacle_center_x = (ox1 + ox2) / 2
                obstacle_center_y = (oy1 + oy2) / 2
                
                # חישוב המרחק לכל צד של המכשול
                dx = ball_center_x - obstacle_center_x
                dy = ball_center_y - obstacle_center_y
                
                # רתע בהתאם לצד הפגיעה
                if abs(dx) > abs(dy):
                    # פגיעה מימין או משמאל
                    self.ball_dx = -self.ball_dx * 0.95
                else:
                    # פגיעה מלמעלה או מלמטה
                    self.ball_dy = -self.ball_dy * 0.95
                
                self.create_explosion(ball_center_x, ball_center_y, '#00ff00')
                self.trigger_shake(intensity=5, duration=5)
                return True
        return False

    def adjust_ball_angle(self, paddle_y1, paddle_y2, ball_y1, ball_y2):
        paddle_center = (paddle_y1 + paddle_y2) / 2
        ball_center = (ball_y1 + ball_y2) / 2
        distance = ball_center - paddle_center
        self.ball_dy = (distance / (PADDLE_HEIGHT / 2)) * self.current_ball_speed
        if abs(self.ball_dy) < 2:
            self.ball_dy = 2 * (1 if self.ball_dy >= 0 else -1)
        elif abs(self.ball_dy) > self.current_ball_speed * 0.85:
            self.ball_dy = (self.current_ball_speed * 0.85) * (1 if self.ball_dy >= 0 else -1)

if __name__ == '__main__':
    root = tk.Tk()
    NeonPonk(root)
    root.mainloop()
    