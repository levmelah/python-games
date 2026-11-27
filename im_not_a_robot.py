import array
import math
import random
import string
import time
from pathlib import Path

import pygame

WIDTH, HEIGHT = 900, 650
FPS = 60
SAMPLE_RATE = 44100

BG = (18, 18, 26)
PANEL = (30, 30, 42)
BORDER = (70, 70, 90)
WHITE = (235, 235, 240)
GRAY = (150, 150, 160)
GREEN = (29, 209, 161)
RED = (255, 107, 107)
YELLOW = (254, 202, 87)
BLUE = (84, 160, 255)
GOOGLE_BLUE = (66, 133, 244)

SHAPE_COLORS = [(255, 107, 107), (254, 202, 87), (29, 209, 161), (84, 160, 255), (255, 159, 243)]
SHAPES = ["circle", "square", "triangle", "star"]
CHALLENGE_TYPES = [
    "shapes", "math", "sequence", "moving_button",
    "distorted_text", "steady_hand", "reaction", "traffic_light_grid",
]

HIGH_SCORE_FILE = Path(__file__).with_name("im_not_a_robot_highscore.txt")

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("I'm Not a Robot")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("couriernew", 46, bold=True)
font_med = pygame.font.SysFont("couriernew", 26, bold=True)
font_small = pygame.font.SysFont("couriernew", 18)
font_code = pygame.font.SysFont("couriernew", 40, bold=True)

try:
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
    SOUND_ENABLED = True
except pygame.error:
    SOUND_ENABLED = False


def tone_array(freq, duration, volume=0.3, decay=True):
    n = int(SAMPLE_RATE * duration)
    arr = array.array("h", [0] * n)
    for i in range(n):
        t = i / SAMPLE_RATE
        amp = volume * (1 - i / n) if decay else volume
        arr[i] = int(amp * 32767 * math.sin(2 * math.pi * freq * t))
    return arr


def silence_array(duration):
    return array.array("h", [0] * int(SAMPLE_RATE * duration))


def make_sound(arr):
    return pygame.mixer.Sound(buffer=arr.tobytes()) if SOUND_ENABLED else None


def play_sound(sound):
    if SOUND_ENABLED and sound:
        sound.play()


CLICK_SOUND = make_sound(tone_array(700, 0.04, 0.22))
SUCCESS_SOUND = make_sound(tone_array(660, 0.09, 0.3) + tone_array(880, 0.12, 0.3)) if SOUND_ENABLED else None
FAIL_SOUND = make_sound(tone_array(200, 0.18, 0.3))


def speak_code_sound(code):
    if not SOUND_ENABLED:
        return None
    arr = array.array("h")
    for ch in code:
        freq = 300 + (ord(ch) - 65) * 18
        arr += tone_array(freq, 0.12, 0.28)
        arr += silence_array(0.03)
    return make_sound(arr)


def load_best_score():
    try:
        return int(HIGH_SCORE_FILE.read_text(encoding="utf-8").strip() or "0")
    except (FileNotFoundError, ValueError):
        return 0


def save_best_score(value):
    HIGH_SCORE_FILE.write_text(str(value), encoding="utf-8")


def draw_text(surface, text, font, color, center):
    img = font.render(text, True, color)
    surface.blit(img, img.get_rect(center=center))


def draw_shape(surface, shape, color, center, size):
    x, y = center
    if shape == "circle":
        pygame.draw.circle(surface, color, (x, y), size)
    elif shape == "square":
        pygame.draw.rect(surface, color, (x - size, y - size, size * 2, size * 2))
    elif shape == "triangle":
        pygame.draw.polygon(surface, color, [(x, y - size), (x - size, y + size), (x + size, y + size)])
    elif shape == "star":
        pts = []
        for i in range(10):
            r = size if i % 2 == 0 else size * 0.45
            ang = math.pi / 2 + i * math.pi / 5
            pts.append((x + r * math.cos(ang), y - r * math.sin(ang)))
        pygame.draw.polygon(surface, color, pts)


class Game:
    def __init__(self):
        self.best = load_best_score()
        self.reset_run()
        self.state = "menu"
        self.checkbox_hover = False

    def reset_run(self):
        self.score = 0
        self.level = 1
        self.last_type = None
        self.type_bag = []
        self.challenge = None
        self.result_text = ""
        self.result_color = WHITE
        self.result_until = 0

    def lvl(self, cap=20):
        return min(self.level, cap)

    def _next_type(self):
        if not self.type_bag:
            bag = CHALLENGE_TYPES.copy()
            random.shuffle(bag)
            if bag[0] == self.last_type:
                swap_with = random.randint(1, len(bag) - 1)
                bag[0], bag[swap_with] = bag[swap_with], bag[0]
            self.type_bag = bag
        return self.type_bag.pop(0)

    def start_challenge(self):
        ctype = self._next_type()
        self.last_type = ctype
        now = time.time()
        c = {"type": ctype}

        if ctype == "shapes":
            while True:
                cells = [(random.choice(SHAPES), random.choice(SHAPE_COLORS)) for _ in range(9)]
                target = random.choice(SHAPES)
                count = sum(1 for s, _ in cells if s == target)
                if 2 <= count <= 5:
                    break
            c["cells"] = cells
            c["target"] = target
            c["selected"] = set()

        elif ctype == "math":
            a = random.randint(2, 9 + self.lvl())
            b = random.randint(2, 9 + self.lvl())
            op = random.choice(["+", "-", "x"])
            if op == "-" and b > a:
                a, b = b, a
            answer = a + b if op == "+" else (a - b if op == "-" else a * b)
            c["question"] = f"{a} {op} {b} = ?"
            c["answer"] = answer
            c["typed"] = ""

        elif ctype == "sequence":
            n = min(4 + self.lvl() // 2, 8)
            positions = []
            area = pygame.Rect(80, 180, WIDTH - 160, HEIGHT - 320)
            while len(positions) < n:
                p = (random.randint(area.left + 30, area.right - 30), random.randint(area.top + 30, area.bottom - 30))
                if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 70 for q in positions):
                    positions.append(p)
            labels = list(range(1, n + 1))
            random.shuffle(labels)
            c["dots"] = list(zip(positions, labels))
            c["next_needed"] = 1
            c["n"] = n

        elif ctype == "moving_button":
            c["move_interval"] = max(0.4, 0.9 - self.lvl() * 0.02)
            c["last_move"] = now
            c["rect"] = self._random_button_rect()

        elif ctype == "distorted_text":
            length = random.randint(5, 7)
            code = "".join(random.choices(string.ascii_uppercase, k=length))
            c["code"] = code
            c["phase"] = random.uniform(0, math.pi * 2)
            c["typed"] = ""

        elif ctype == "steady_hand":
            c["center"] = (WIDTH // 2, HEIGHT // 2 + 40)
            c["radius"] = max(40, 90 - self.lvl() * 2)
            c["progress"] = 0.0

        elif ctype == "reaction":
            c["phase"] = "wait"
            c["turn_time"] = now + random.uniform(0.8, 2.2)

        elif ctype == "traffic_light_grid":
            scene_rect = pygame.Rect(WIDTH // 2 - 150, 210, 300, 300)
            grid_n = 3
            cell = scene_rect.width // grid_n
            lights = []
            for _ in range(random.randint(1, 2)):
                lx = random.randint(scene_rect.left + 25, scene_rect.right - 25)
                ly = random.randint(scene_rect.top + 25, scene_rect.top + 180)
                lights.append((lx, ly))
            target_cells = set()
            for lx, ly in lights:
                col = max(0, min(grid_n - 1, (lx - scene_rect.left) // cell))
                row = max(0, min(grid_n - 1, (ly - scene_rect.top) // cell))
                target_cells.add(row * grid_n + col)
            c["scene_rect"] = scene_rect
            c["grid_n"] = grid_n
            c["lights"] = lights
            c["target_cells"] = target_cells
            c["selected"] = set()

        self.challenge = c
        self.state = "challenge"

    def _random_button_rect(self):
        w, h = 140, 60
        x = random.randint(80, WIDTH - 80 - w)
        y = random.randint(180, HEIGHT - 120 - h)
        return pygame.Rect(x, y, w, h)

    def finish_challenge(self, success):
        if success:
            self.score += 10 * self.lvl()
            self.level += 1
            self.result_text, self.result_color = "VERIFIED", GREEN
            play_sound(SUCCESS_SOUND)
        else:
            self.result_text, self.result_color = "TRY AGAIN", RED
            play_sound(FAIL_SOUND)
        self.result_until = time.time() + 0.8
        self.state = "result"

    def update(self, dt):
        if self.state == "challenge":
            c = self.challenge
            now = time.time()
            if c["type"] == "moving_button":
                if now - c["last_move"] >= c["move_interval"]:
                    c["last_move"] = now
                    c["rect"] = self._random_button_rect()
            elif c["type"] == "steady_hand":
                mx, my = pygame.mouse.get_pos()
                cx, cy = c["center"]
                inside = math.hypot(mx - cx, my - cy) <= c["radius"]
                c["progress"] += (55 if inside else -80) * dt
                c["progress"] = max(0.0, min(100.0, c["progress"]))
                if c["progress"] >= 100.0:
                    self.finish_challenge(True)
                    return
            elif c["type"] == "reaction":
                if c["phase"] == "wait" and now >= c["turn_time"]:
                    c["phase"] = "go"

        elif self.state == "result":
            if time.time() >= self.result_until:
                self.start_challenge()

    def _go_to_menu(self):
        if self.score > self.best:
            self.best = self.score
            save_best_score(self.best)
        self.state = "menu"

    def handle_click(self, pos):
        play_sound(CLICK_SOUND)

        if self.state == "menu":
            box = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 40, 44, 44)
            label_rect = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 60, 440, 90)
            if box.collidepoint(pos) or label_rect.collidepoint(pos):
                self.reset_run()
                self.start_challenge()
            return

        if self.state != "challenge":
            return

        c = self.challenge
        reroll_rect = pygame.Rect(WIDTH - 70, 20, 40, 40)
        if reroll_rect.collidepoint(pos):
            self.start_challenge()
            return

        if c["type"] == "shapes":
            grid_rect = pygame.Rect(WIDTH // 2 - 240, 220, 480, 300)
            cell_w, cell_h = 160, 100
            for i in range(9):
                col, row = i % 3, i // 3
                cell = pygame.Rect(grid_rect.left + col * cell_w, grid_rect.top + row * cell_h, cell_w, cell_h)
                if cell.collidepoint(pos):
                    c["selected"] ^= {i}
                    return
            verify_rect = pygame.Rect(WIDTH // 2 - 90, 540, 180, 50)
            if verify_rect.collidepoint(pos):
                correct = {i for i, (s, _) in enumerate(c["cells"]) if s == c["target"]}
                self.finish_challenge(c["selected"] == correct)

        elif c["type"] == "math":
            verify_rect = pygame.Rect(WIDTH // 2 - 90, 460, 180, 50)
            if verify_rect.collidepoint(pos):
                try:
                    ok = int(c["typed"]) == c["answer"]
                except ValueError:
                    ok = False
                self.finish_challenge(ok)

        elif c["type"] == "sequence":
            for (px, py), label in c["dots"]:
                if math.hypot(pos[0] - px, pos[1] - py) <= 28:
                    if label == c["next_needed"]:
                        c["next_needed"] += 1
                        if c["next_needed"] > c["n"]:
                            self.finish_challenge(True)
                    else:
                        self.finish_challenge(False)
                    return

        elif c["type"] == "moving_button":
            if c["rect"].collidepoint(pos):
                self.finish_challenge(True)

        elif c["type"] == "distorted_text":
            box = pygame.Rect(WIDTH // 2 - 260, 220, 520, 130)
            refresh_center = (box.right - 22, box.bottom - 18)
            if math.hypot(pos[0] - refresh_center[0], pos[1] - refresh_center[1]) <= 14:
                self.start_challenge()
                return
            speaker_center = (box.left + 22, box.bottom - 18)
            if math.hypot(pos[0] - speaker_center[0], pos[1] - speaker_center[1]) <= 14:
                play_sound(speak_code_sound(c["code"]))
                return
            input_rect = pygame.Rect(WIDTH // 2 - 260, box.bottom + 30, 340, 50)
            submit_rect = pygame.Rect(input_rect.right + 20, input_rect.top, 120, 50)
            if submit_rect.collidepoint(pos):
                self.finish_challenge(c["typed"].upper() == c["code"])

        elif c["type"] == "reaction":
            if c["phase"] == "wait":
                self.finish_challenge(False)
            else:
                self.finish_challenge(True)

        elif c["type"] == "traffic_light_grid":
            rect = c["scene_rect"]
            n = c["grid_n"]
            cell = rect.width // n
            for i in range(n * n):
                col, row = i % n, i // n
                cell_rect = pygame.Rect(rect.left + col * cell, rect.top + row * cell, cell, cell)
                if cell_rect.collidepoint(pos):
                    c["selected"] ^= {i}
                    return
            verify_rect = pygame.Rect(WIDTH // 2 - 90, rect.bottom + 30, 180, 50)
            if verify_rect.collidepoint(pos):
                self.finish_challenge(c["selected"] == c["target_cells"])

    def handle_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self._go_to_menu()
            return
        if self.state != "challenge":
            return
        c = self.challenge
        if c["type"] == "math":
            if event.key == pygame.K_BACKSPACE:
                c["typed"] = c["typed"][:-1]
            elif event.key == pygame.K_RETURN:
                try:
                    ok = int(c["typed"]) == c["answer"]
                except ValueError:
                    ok = False
                self.finish_challenge(ok)
            elif event.unicode.isdigit() and len(c["typed"]) < 5:
                c["typed"] += event.unicode
        elif c["type"] == "distorted_text":
            if event.key == pygame.K_BACKSPACE:
                c["typed"] = c["typed"][:-1]
            elif event.key == pygame.K_RETURN:
                self.finish_challenge(c["typed"].upper() == c["code"])
            elif event.unicode.isalnum() and len(c["typed"]) < len(c["code"]):
                c["typed"] += event.unicode.upper()

    def draw(self):
        screen.fill(BG)
        if self.state == "menu":
            self.draw_menu()
        elif self.state in ("challenge", "result"):
            self.draw_hud()
            self.draw_challenge()
            if self.state == "result":
                overlay = pygame.Surface((WIDTH, 90))
                overlay.set_alpha(210)
                overlay.fill(PANEL)
                screen.blit(overlay, (0, HEIGHT // 2 - 45))
                draw_text(screen, self.result_text, font_big, self.result_color, (WIDTH // 2, HEIGHT // 2))

    def draw_menu(self):
        panel = pygame.Rect(WIDTH // 2 - 240, HEIGHT // 2 - 90, 480, 180)
        pygame.draw.rect(screen, PANEL, panel, border_radius=10)
        pygame.draw.rect(screen, BORDER, panel, width=2, border_radius=10)

        box = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 40, 44, 44)
        pygame.draw.rect(screen, WHITE, box, width=2, border_radius=4)
        if self.checkbox_hover:
            pygame.draw.rect(screen, (45, 45, 60), box.inflate(-4, -4), border_radius=3)
        draw_text(screen, "I'm not a robot", font_med, WHITE, (WIDTH // 2 + 30, HEIGHT // 2 - 18))

        cx, cy = WIDTH // 2 + 175, HEIGHT // 2 + 30
        pygame.draw.arc(screen, GRAY, (cx - 14, cy - 14, 28, 28), 0.6, 5.6, 2)
        draw_text(screen, "reCAPTCHA-ish", font_small, GRAY, (WIDTH // 2 + 150, HEIGHT // 2 + 55))

        draw_text(screen, "Click the checkbox to prove you're human", font_small, GRAY, (WIDTH // 2, HEIGHT // 2 + 130))
        draw_text(screen, f"Score: {self.score}   Best: {self.best}", font_small, YELLOW, (WIDTH // 2, HEIGHT // 2 + 160))

    def draw_hud(self):
        pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, 70))
        draw_text(screen, f"Score: {self.score}", font_small, WHITE, (110, 25))
        draw_text(screen, f"Level: {self.level}", font_small, WHITE, (110, 50))
        draw_text(screen, "ESC: finish session", font_small, GRAY, (WIDTH // 2, 40))

        reroll_rect = pygame.Rect(WIDTH - 70, 20, 40, 40)
        pygame.draw.circle(screen, BLUE, reroll_rect.center, 20, width=3)
        pygame.draw.arc(screen, BLUE, reroll_rect.inflate(-14, -14), 0.6, 5.6, 3)

    def draw_challenge(self):
        c = self.challenge
        t = c["type"]

        if t == "shapes":
            draw_text(screen, f"Click every {c['target'].upper()}, then Verify", font_small, WHITE, (WIDTH // 2, 190))
            grid_rect = pygame.Rect(WIDTH // 2 - 240, 220, 480, 300)
            cell_w, cell_h = 160, 100
            for i, (shape, color) in enumerate(c["cells"]):
                col, row = i % 3, i // 3
                cell = pygame.Rect(grid_rect.left + col * cell_w, grid_rect.top + row * cell_h, cell_w, cell_h)
                pygame.draw.rect(screen, PANEL, cell)
                pygame.draw.rect(screen, GREEN if i in c["selected"] else BORDER, cell, width=3)
                draw_shape(screen, shape, color, cell.center, 28)
            verify_rect = pygame.Rect(WIDTH // 2 - 90, 540, 180, 50)
            pygame.draw.rect(screen, GREEN, verify_rect, border_radius=6)
            draw_text(screen, "VERIFY", font_small, BG, verify_rect.center)

        elif t == "math":
            draw_text(screen, "Solve to verify:", font_small, GRAY, (WIDTH // 2, 220))
            draw_text(screen, c["question"], font_big, WHITE, (WIDTH // 2, 300))
            input_rect = pygame.Rect(WIDTH // 2 - 100, 370, 200, 50)
            pygame.draw.rect(screen, PANEL, input_rect, border_radius=6)
            pygame.draw.rect(screen, BORDER, input_rect, width=2, border_radius=6)
            draw_text(screen, c["typed"] or " ", font_med, WHITE, input_rect.center)
            verify_rect = pygame.Rect(WIDTH // 2 - 90, 460, 180, 50)
            pygame.draw.rect(screen, GREEN, verify_rect, border_radius=6)
            draw_text(screen, "VERIFY", font_small, BG, verify_rect.center)

        elif t == "sequence":
            draw_text(screen, f"Click the numbers in order (1 to {c['n']})", font_small, WHITE, (WIDTH // 2, 150))
            for (pos, label) in c["dots"]:
                done = label < c["next_needed"]
                pygame.draw.circle(screen, GREEN if done else BLUE, pos, 28)
                draw_text(screen, str(label), font_med, BG, pos)

        elif t == "moving_button":
            draw_text(screen, "Catch the button!", font_small, WHITE, (WIDTH // 2, 150))
            pygame.draw.rect(screen, YELLOW, c["rect"], border_radius=8)
            draw_text(screen, "CLICK ME", font_small, BG, c["rect"].center)

        elif t == "distorted_text":
            box = pygame.Rect(WIDTH // 2 - 260, 220, 520, 130)
            pygame.draw.rect(screen, (245, 245, 240), box, border_radius=4)
            pygame.draw.rect(screen, BORDER, box, width=2, border_radius=4)
            draw_text(screen, "Enter the text below", font_small, WHITE, (box.centerx, box.top - 20))

            code = c["code"]
            phase = c["phase"]
            n = len(code)
            char_w = 48
            start_x = box.centerx - (n * char_w) // 2
            for i, ch in enumerate(code):
                img = font_code.render(ch, True, (70, 90, 110))
                angle = math.sin(i * 0.9 + phase) * 18
                img = pygame.transform.rotate(img, angle)
                y_off = math.sin(i * 0.7 + phase) * 14
                screen.blit(img, (start_x + i * char_w, box.centery - img.get_height() // 2 + y_off))

            noise_rng = random.Random(code)
            for _ in range(3):
                amp = noise_rng.uniform(10, 25)
                ph = noise_rng.uniform(0, math.pi * 2)
                pts = []
                for x in range(box.left, box.right, 8):
                    y = box.centery + amp * math.sin((x - box.left) * 0.05 + ph)
                    pts.append((x, y))
                pygame.draw.lines(screen, (230, 100, 90), False, pts, 2)

            spk = (box.left + 22, box.bottom - 18)
            pygame.draw.polygon(screen, GRAY, [
                (spk[0] - 8, spk[1] - 6), (spk[0] - 2, spk[1] - 6), (spk[0] + 6, spk[1] - 14),
                (spk[0] + 6, spk[1] + 14), (spk[0] - 2, spk[1] + 6), (spk[0] - 8, spk[1] + 6),
            ])
            refresh_center = (box.right - 22, box.bottom - 18)
            pygame.draw.circle(screen, BLUE, refresh_center, 12, width=2)
            pygame.draw.arc(screen, BLUE, (refresh_center[0] - 9, refresh_center[1] - 9, 18, 18), 0.6, 5.6, 2)

            input_rect = pygame.Rect(WIDTH // 2 - 260, box.bottom + 30, 340, 50)
            pygame.draw.rect(screen, (255, 255, 255), input_rect, border_radius=4)
            pygame.draw.rect(screen, BORDER, input_rect, width=2, border_radius=4)
            txt_color = (30, 30, 30) if c["typed"] else (150, 150, 150)
            draw_text(screen, c["typed"] or "Answer", font_med, txt_color, input_rect.center)
            submit_rect = pygame.Rect(input_rect.right + 20, input_rect.top, 120, 50)
            pygame.draw.rect(screen, GOOGLE_BLUE, submit_rect, border_radius=4)
            draw_text(screen, "Submit", font_small, WHITE, submit_rect.center)

        elif t == "steady_hand":
            draw_text(screen, "Keep the cursor inside the ring", font_small, WHITE, (WIDTH // 2, 150))
            cx, cy = c["center"]
            pygame.draw.circle(screen, BORDER, (cx, cy), c["radius"], width=3)
            bar_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 90, 300, 24)
            pygame.draw.rect(screen, (60, 60, 70), bar_rect, border_radius=6)
            fill_w = int(bar_rect.width * c["progress"] / 100)
            pygame.draw.rect(screen, GREEN, (bar_rect.x, bar_rect.y, fill_w, bar_rect.height), border_radius=6)
            pygame.draw.rect(screen, BORDER, bar_rect, width=2, border_radius=6)

        elif t == "reaction":
            draw_text(screen, "Click only when it turns green", font_small, WHITE, (WIDTH // 2, 200))
            box_rect = pygame.Rect(WIDTH // 2 - 150, 260, 300, 200)
            color = RED if c["phase"] == "wait" else GREEN
            pygame.draw.rect(screen, color, box_rect, border_radius=10)
            label = "WAIT..." if c["phase"] == "wait" else "CLICK NOW!"
            draw_text(screen, label, font_med, BG, box_rect.center)

        elif t == "traffic_light_grid":
            draw_text(screen, "Select all squares with a traffic light", font_small, WHITE, (WIDTH // 2, 185))
            rect = c["scene_rect"]
            n = c["grid_n"]
            cell = rect.width // n

            pygame.draw.rect(screen, (120, 170, 220), rect)
            ground_rect = pygame.Rect(rect.left, rect.bottom - 90, rect.width, 90)
            pygame.draw.rect(screen, (90, 90, 95), ground_rect)
            for tx in (rect.left + 40, rect.right - 40):
                pygame.draw.circle(screen, (40, 120, 60), (tx, rect.bottom - 95), 26)
                pygame.draw.rect(screen, (90, 60, 40), (tx - 4, rect.bottom - 95, 8, 40))

            for lx, ly in c["lights"]:
                pygame.draw.line(screen, (30, 30, 30), (lx, ly + 22), (lx, rect.bottom - 90), 4)
                box = pygame.Rect(lx - 10, ly - 22, 20, 44)
                pygame.draw.rect(screen, (25, 25, 25), box, border_radius=4)
                pygame.draw.circle(screen, (255, 90, 90), (lx, ly - 12), 6)
                pygame.draw.circle(screen, (255, 220, 90), (lx, ly), 6)
                pygame.draw.circle(screen, (90, 255, 140), (lx, ly + 12), 6)

            for i in range(n + 1):
                pygame.draw.line(screen, WHITE, (rect.left + i * cell, rect.top), (rect.left + i * cell, rect.bottom), 2)
                pygame.draw.line(screen, WHITE, (rect.left, rect.top + i * cell), (rect.right, rect.top + i * cell), 2)

            for idx in c["selected"]:
                row, col = divmod(idx, n)
                cell_rect = pygame.Rect(rect.left + col * cell, rect.top + row * cell, cell, cell)
                overlay = pygame.Surface((cell, cell), pygame.SRCALPHA)
                overlay.fill((29, 209, 161, 120))
                screen.blit(overlay, cell_rect.topleft)
                pygame.draw.rect(screen, GREEN, cell_rect, width=3)

            verify_rect = pygame.Rect(WIDTH // 2 - 90, rect.bottom + 30, 180, 50)
            pygame.draw.rect(screen, GREEN, verify_rect, border_radius=6)
            draw_text(screen, "VERIFY", font_small, BG, verify_rect.center)


def main():
    game = Game()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                game.handle_key(event)

        if game.state == "menu":
            box = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 40, 44, 44)
            game.checkbox_hover = box.collidepoint(pygame.mouse.get_pos())

        game.update(dt)
        game.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
