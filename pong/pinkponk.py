import tkinter as tk
import random

# קבועי משחק
WIDTH = 800
HEIGHT = 500
PADDLE_WIDTH = 12
PADDLE_HEIGHT = 100
BALL_SIZE = 18
INITIAL_BALL_SPEED = 6
SPEED_ACCELERATION = 1.05  # הכדור מאיץ ב-5% בכל פגיעה
AI_SPEED = 5
PADDLE_SPEED = 7  # מהירות תנועה חלקה בכל פריים

class PinkPonk:
    def __init__(self, root):
        self.root = root
        root.title('PinkPonk - המשחק המשופר')
        root.resizable(False, False)

        # קנבס בעיצוב נקי
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='#ffb6c1', highlightthickness=0)
        self.canvas.pack()

        self.player_score = 0
        self.ai_score = 0
        self.current_ball_speed = INITIAL_BALL_SPEED

        # מערכת מעקב אחרי מקשים לטובת תנועה חלקה
        self.keys_pressed = {"Up": False, "Down": False}

        self.setup_game_elements()
        self.bind_events()
        
        self.reset_ball(direction=random.choice([1, -1]))
        self.update_game()

    def setup_game_elements(self):
        # קו אמצע דקורטיבי
        for y in range(10, HEIGHT, 30):
            self.canvas.create_rectangle(WIDTH // 2 - 2, y, WIDTH // 2 + 2, y + 15, fill='#ffffff', outline='')

        # מטליות
        self.player_paddle = self.canvas.create_rectangle(
            30, HEIGHT // 2 - PADDLE_HEIGHT // 2,
            30 + PADDLE_WIDTH, HEIGHT // 2 + PADDLE_HEIGHT // 2,
            fill='#ff69b4', outline='#e0115f', width=2
        )
        self.ai_paddle = self.canvas.create_rectangle(
            WIDTH - 30 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2,
            WIDTH - 30, HEIGHT // 2 + PADDLE_HEIGHT // 2,
            fill='#c71585', outline='#4a0033', width=2
        )
        
        # כדור
        self.ball = self.canvas.create_oval(0, 0, BALL_SIZE, BALL_SIZE, fill='white', outline='#ff69b4', width=2)

        # טקסטים
        self.score_text = self.canvas.create_text(
            WIDTH // 2, 40,
            text=self.get_score_text(),
            font=('Segoe UI', 28, 'bold'),
            fill='#8b008b'
        )
        self.hint_text = self.canvas.create_text(
            WIDTH // 2, HEIGHT - 25,
            text='השתמש בחצים למעלה / למטה לתנועה חלקקה',
            font=('Segoe UI', 12, 'italic'),
            fill='#4b0082'
        )

    def bind_events(self):
        # האזנה ללחיצה ושחרור של המקשים
        self.root.bind('<KeyPress-Up>', lambda e: self.set_key_state("Up", True))
        self.root.bind('<KeyRelease-Up>', lambda e: self.set_key_state("Up", False))
        self.root.bind('<KeyPress-Down>', lambda e: self.set_key_state("Down", True))
        self.root.bind('<KeyRelease-Down>', lambda e: self.set_key_state("Down", False))

    def set_key_state(self, key, state):
        self.keys_pressed[key] = state

    def get_score_text(self):
        return f'{self.player_score}   :   {self.ai_score}'

    def move_player(self):
        # חישוב כיוון התנועה הנוכחי
        dy = 0
        if self.keys_pressed["Up"]:
            dy -= PADDLE_SPEED
        if self.keys_pressed["Down"]:
            dy += PADDLE_SPEED

        if dy != 0:
            x1, y1, x2, y2 = self.canvas.coords(self.player_paddle)
            if y1 + dy < 0:
                dy = -y1
            elif y2 + dy > HEIGHT:
                dy = HEIGHT - y2
            self.canvas.move(self.player_paddle, 0, dy)

    def update_ai(self):
        ball_coords = self.canvas.coords(self.ball)
        if not ball_coords: return
        
        bx1, by1, bx2, by2 = ball_coords
        ai_x1, ai_y1, ai_x2, ai_y2 = self.canvas.coords(self.ai_paddle)
        
        ball_center = (by1 + by2) / 2
        ai_center = (ai_y1 + ai_y2) / 2

        # המחשב עוקב אחרי הכדור רק כשהוא נע לכיוונו (משפר ביצועים ותחושה)
        if self.ball_dx > 0:
            if ball_center < ai_center - 15:
                dy = -AI_SPEED
            elif ball_center > ai_center + 15:
                dy = AI_SPEED
            else:
                dy = 0
        else:
            # חזרה איטית למרכז כשהכדור בצד השני
            if ai_center < HEIGHT // 2 - 10:
                dy = 2
            elif ai_center > HEIGHT // 2 + 10:
                dy = -2
            else:
                dy = 0

        if ai_y1 + dy < 0:
            dy = -ai_y1
        elif ai_y2 + dy > HEIGHT:
            dy = HEIGHT - ai_y2
        self.canvas.move(self.ai_paddle, 0, dy)

    def reset_ball(self, direction):
        self.current_ball_speed = INITIAL_BALL_SPEED
        self.canvas.coords(
            self.ball,
            WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2 - BALL_SIZE // 2,
            WIDTH // 2 + BALL_SIZE // 2, HEIGHT // 2 + BALL_SIZE // 2,
        )
        self.ball_dx = self.current_ball_speed * direction
        self.ball_dy = random.choice([-3, -2, 2, 3])

    def flash_screen(self, color):
        # אפקט ויזואלי קצר בעת הבקעת שער
        orig_bg = self.canvas.cget("bg")
        self.canvas.configure(bg=color)
        self.root.after(150, lambda: self.canvas.configure(bg=orig_bg))

    def update_game(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        self.move_player()
        self.update_ai()

        ball_coords = self.canvas.coords(self.ball)
        if not ball_coords: return
        bx1, by1, bx2, by2 = ball_coords

        # התנגשות בקירות עליון ותחתון
        if by1 <= 0:
            self.ball_dy = abs(self.ball_dy)
        elif by2 >= HEIGHT:
            self.ball_dy = -abs(self.ball_dy)

        player_x1, player_y1, player_x2, player_y2 = self.canvas.coords(self.player_paddle)
        ai_x1, ai_y1, ai_x2, ai_y2 = self.canvas.coords(self.ai_paddle)

        # התנגשות במטלית השחקן (רק כשהכדור נע שמאלה)
        if self.ball_dx < 0 and self.check_collision(player_x1, player_y1, player_x2, player_y2, bx1, by1, bx2, by2):
            self.current_ball_speed *= SPEED_ACCELERATION
            self.ball_dx = abs(self.ball_dx) * SPEED_ACCELERATION
            self.adjust_ball_angle(player_y1, player_y2, by1, by2)
            
        # התנגשות במטלית המחשב (רק כשהכדור נע ימינה)
        elif self.ball_dx > 0 and self.check_collision(ai_x1, ai_y1, ai_x2, ai_y2, bx1, by1, bx2, by2):
            self.current_ball_speed *= SPEED_ACCELERATION
            self.ball_dx = -abs(self.ball_dx) * SPEED_ACCELERATION
            self.adjust_ball_angle(ai_y1, ai_y2, by1, by2)

        # בדיקת נקודות ופסילות
        if bx1 <= 0:
            self.ai_score += 1
            self.flash_screen('#ffcccb')
            self.canvas.itemconfigure(self.score_text, text=self.get_score_text())
            self.reset_ball(direction=1)
        elif bx2 >= WIDTH:
            self.player_score += 1
            self.flash_screen('#lightgreen')
            self.canvas.itemconfigure(self.score_text, text=self.get_score_text())
            self.reset_ball(direction=-1)

        self.root.after(16, self.update_game)  # ~60 FPS לחלקות מקסימלית

    def check_collision(self, px1, py1, px2, py2, bx1, by1, bx2, by2):
        return not (bx2 < px1 or bx1 > px2 or by2 < py1 or by1 > py2)

    def adjust_ball_angle(self, paddle_y1, paddle_y2, ball_y1, ball_y2):
        paddle_center = (paddle_y1 + paddle_y2) / 2
        ball_center = (ball_y1 + ball_y2) / 2
        distance = ball_center - paddle_center
        
        # שינוי זווית החזרה דינמי לפי מיקום הפגיעה במטלית
        self.ball_dy = (distance / (PADDLE_HEIGHT / 2)) * self.current_ball_speed
        
        # הגבלת מהירות אנכית מינימלית ומקסימלית למניעת תנועה משעממת או אנכית מדי
        if abs(self.ball_dy) < 1.5:
            self.ball_dy = 1.5 * (1 if self.ball_dy >= 0 else -1)
        elif abs(self.ball_dy) > self.current_ball_speed * 0.9:
            self.ball_dy = (self.current_ball_speed * 0.9) * (1 if self.ball_dy >= 0 else -1)

if __name__ == '__main__':
    root = tk.Tk()
    PinkPonk(root)
    root.mainloop()
