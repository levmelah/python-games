import pygame
import sys
import math
import re

pygame.init()

WIDTH, HEIGHT = 1000, 620
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Football Game")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 28, True)
SMALL_FONT = pygame.font.SysFont("Arial", 20)
LARGE_FONT = pygame.font.SysFont("Arial", 54, True)

WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
DARK_GREEN = (20, 90, 20)
BLACK = (0, 0, 0)
BLUE = (20, 120, 220)
RED = (220, 50, 50)
YELLOW = (248, 235, 70)
SUPER_GREEN = (40, 220, 90)
SUPER_SPEED_MULTIPLIER = 1.15
SUB_LEAVE_DURATION = 50
SUB_ENTER_DURATION = 50
WIN_SCORE = 3

PLAYER_RADIUS = 24
BALL_RADIUS = 14
PLAYER_SPEED = 6
BALL_FRICTION = 0.986
BALL_MAX_SPEED = 18
GOAL_WIDTH = 20
GOAL_HEIGHT = 180
GOAL_TEXT_DURATION = 70
YELLOW_CARD_DURATION = 120
CAMERA_ZOOM_SPEED = 0.08
CAMERA_MOVE_SPEED = 0.12
CAMERA_ZOOM_IDLE = 0.95
CAMERA_ZOOM_ACTIVE = 1.25
CAMERA_ZOOM_MIN = 0.8
CAMERA_ZOOM_MAX = 1.4

LANGUAGES = ["en", "he", "ru", "es", "fr"]
LANGUAGE_NAMES = {
    "en": "English",
    "he": "עברית",
    "ru": "Русский",
    "es": "Español",
    "fr": "Français",
}
RTL_LANGUAGES = {"he"}

TRANSLATIONS = {
    "en": {
        "app_title": "FOOTBALL",
        "subtitle": "Score more goals than your opponent",
        "play": "PLAY",
        "play_sub": "1 Player vs AI",
        "twop": "2 PLAYERS",
        "twop_sub": "Local co-op on one keyboard",
        "help_btn": "HOW TO PLAY",
        "language_btn": "LANGUAGE",
        "quit_btn": "QUIT",
        "back_btn": "BACK",
        "how_to_play_title": "HOW TO PLAY",
        "select_language_title": "SELECT LANGUAGE",
        "how_to_lines": [
            "Blue player: W/A/S/D or Arrow keys",
            "Red player (2 Players mode): Up/Down/Left/Right",
            "Bump into the ball to kick it towards the goal.",
            "Colliding with the other player can earn a yellow card,",
            "two yellow cards give a red card and slow the player down.",
            "If Red gets a red card, Green comes on as a tougher substitute.",
            "First to {n} goals wins the match!",
            "Restart the match: R      Back to menu: Esc",
        ],
        "team_blue": "Blue",
        "team_red": "Red",
        "team_green": "Green",
        "win_note": "First to {n} goals wins!",
        "controls_hint": "{blue}: W/A/S/D or Arrows, R = restart",
        "mode_ai": "1 Player vs AI",
        "mode_2p": "2 Players",
        "esc_menu": "Esc = menu",
        "goal": "GOAL!",
        "yellow_card": "Yellow Card: {name}!",
        "red_card": "Red Card: {name}!",
        "already_sent_off": "Already sent off: {name}",
        "red_card_leaving": "RED CARD! {name} is walking off...",
        "green_coming": "GREEN is coming on...",
        "green_on": "GREEN is on!",
        "wins_match": "{name} WINS THE MATCH!",
        "wins_bang": "{name} WINS!",
        "final_score": "Final score: {s1} - {s2}",
        "play_again": "Press R to play again   Esc for menu",
    },
    "he": {
        "app_title": "כדורגל",
        "subtitle": "כבוש יותר שערים מהיריב",
        "play": "שחק",
        "play_sub": "שחקן אחד מול המחשב",
        "twop": "שני שחקנים",
        "twop_sub": "משחק זוגי על אותה מקלדת",
        "help_btn": "איך משחקים",
        "language_btn": "שפה",
        "quit_btn": "יציאה",
        "back_btn": "חזרה",
        "how_to_play_title": "איך משחקים",
        "select_language_title": "בחר שפה",
        "how_to_lines": [
            "שחקן כחול: W/A/S/D או מקשי חצים",
            "שחקן אדום (במצב שני שחקנים): חצים למעלה/למטה/שמאלה/ימינה",
            "התנגש בכדור כדי לבעוט אותו לכיוון השער.",
            "התנגשות עם השחקן השני עלולה לזכות בכרטיס צהוב,",
            "שני כרטיסים צהובים נותנים כרטיס אדום ומאטים את השחקן.",
            "אם האדום מקבל כרטיס אדום, הירוק נכנס כמחליף חזק יותר.",
            "מי שמבקיע {n} שערים ראשון מנצח במשחק!",
            "התחלה מחדש: R      חזרה לתפריט: Esc",
        ],
        "team_blue": "כחול",
        "team_red": "אדום",
        "team_green": "ירוק",
        "win_note": "מי שמבקיע {n} שערים ראשון מנצח!",
        "controls_hint": "{blue}: W/A/S/D או חצים, R = התחלה מחדש",
        "mode_ai": "שחקן אחד מול המחשב",
        "mode_2p": "שני שחקנים",
        "esc_menu": "Esc = תפריט",
        "goal": "גול!",
        "yellow_card": "כרטיס צהוב: {name}!",
        "red_card": "כרטיס אדום: {name}!",
        "already_sent_off": "כבר הורחק: {name}",
        "red_card_leaving": "כרטיס אדום! {name} יוצא מהמגרש...",
        "green_coming": "הירוק נכנס...",
        "green_on": "הירוק במגרש!",
        "wins_match": "{name} ניצח במשחק!",
        "wins_bang": "{name} ניצח!",
        "final_score": "תוצאה סופית: {s1} - {s2}",
        "play_again": "לחץ R לשחק שוב   Esc לתפריט",
    },
    "ru": {
        "app_title": "ФУТБОЛ",
        "subtitle": "Забей больше голов, чем соперник",
        "play": "ИГРАТЬ",
        "play_sub": "1 игрок против ИИ",
        "twop": "2 ИГРОКА",
        "twop_sub": "Локальная игра на одной клавиатуре",
        "help_btn": "КАК ИГРАТЬ",
        "language_btn": "ЯЗЫК",
        "quit_btn": "ВЫХОД",
        "back_btn": "НАЗАД",
        "how_to_play_title": "КАК ИГРАТЬ",
        "select_language_title": "ВЫБЕРИТЕ ЯЗЫК",
        "how_to_lines": [
            "Синий игрок: W/A/S/D или стрелки",
            "Красный игрок (режим 2 игрока): стрелки вверх/вниз/влево/вправо",
            "Столкнитесь с мячом, чтобы ударить его в сторону ворот.",
            "Столкновение с другим игроком может дать жёлтую карточку,",
            "две жёлтые карточки дают красную карточку и замедляют игрока.",
            "Если Красный получает красную карточку, выходит более сильный Зелёный.",
            "Первый, кто забьёт {n} гола, побеждает в матче!",
            "Начать заново: R      В меню: Esc",
        ],
        "team_blue": "Синий",
        "team_red": "Красный",
        "team_green": "Зелёный",
        "win_note": "Первый, кто забьёт {n} гола, побеждает!",
        "controls_hint": "{blue}: W/A/S/D или стрелки, R = заново",
        "mode_ai": "1 игрок против ИИ",
        "mode_2p": "2 игрока",
        "esc_menu": "Esc = меню",
        "goal": "ГОЛ!",
        "yellow_card": "Жёлтая карточка: {name}!",
        "red_card": "Красная карточка: {name}!",
        "already_sent_off": "Уже удалён: {name}",
        "red_card_leaving": "КРАСНАЯ КАРТОЧКА! {name} покидает поле...",
        "green_coming": "Зелёный выходит на поле...",
        "green_on": "Зелёный в игре!",
        "wins_match": "{name} ПОБЕЖДАЕТ В МАТЧЕ!",
        "wins_bang": "{name} ПОБЕДИЛ!",
        "final_score": "Итоговый счёт: {s1} - {s2}",
        "play_again": "R - играть снова   Esc - в меню",
    },
    "es": {
        "app_title": "FÚTBOL",
        "subtitle": "Marca más goles que tu rival",
        "play": "JUGAR",
        "play_sub": "1 Jugador vs IA",
        "twop": "2 JUGADORES",
        "twop_sub": "Cooperativo local en un teclado",
        "help_btn": "CÓMO JUGAR",
        "language_btn": "IDIOMA",
        "quit_btn": "SALIR",
        "back_btn": "ATRÁS",
        "how_to_play_title": "CÓMO JUGAR",
        "select_language_title": "ELEGIR IDIOMA",
        "how_to_lines": [
            "Jugador azul: W/A/S/D o flechas",
            "Jugador rojo (modo 2 jugadores): flechas arriba/abajo/izquierda/derecha",
            "Choca con el balón para patearlo hacia la portería.",
            "Chocar con el otro jugador puede dar una tarjeta amarilla,",
            "dos amarillas dan una tarjeta roja y ralentizan al jugador.",
            "Si el Rojo recibe tarjeta roja, entra el Verde, mucho más fuerte.",
            "¡Quien anote {n} goles primero gana el partido!",
            "Reiniciar partido: R      Volver al menú: Esc",
        ],
        "team_blue": "Azul",
        "team_red": "Rojo",
        "team_green": "Verde",
        "win_note": "¡Quien anote {n} goles primero gana!",
        "controls_hint": "{blue}: W/A/S/D o flechas, R = reiniciar",
        "mode_ai": "1 Jugador vs IA",
        "mode_2p": "2 Jugadores",
        "esc_menu": "Esc = menú",
        "goal": "¡GOL!",
        "yellow_card": "Tarjeta amarilla: ¡{name}!",
        "red_card": "Tarjeta roja: ¡{name}!",
        "already_sent_off": "Ya expulsado: {name}",
        "red_card_leaving": "¡TARJETA ROJA! {name} se retira...",
        "green_coming": "Verde está entrando...",
        "green_on": "¡Verde está en el campo!",
        "wins_match": "¡{name} GANA EL PARTIDO!",
        "wins_bang": "¡{name} GANA!",
        "final_score": "Resultado final: {s1} - {s2}",
        "play_again": "Pulsa R para jugar de nuevo   Esc para el menú",
    },
    "fr": {
        "app_title": "FOOTBALL",
        "subtitle": "Marque plus de buts que ton adversaire",
        "play": "JOUER",
        "play_sub": "1 Joueur contre IA",
        "twop": "2 JOUEURS",
        "twop_sub": "Coop locale sur un seul clavier",
        "help_btn": "COMMENT JOUER",
        "language_btn": "LANGUE",
        "quit_btn": "QUITTER",
        "back_btn": "RETOUR",
        "how_to_play_title": "COMMENT JOUER",
        "select_language_title": "CHOISIR LA LANGUE",
        "how_to_lines": [
            "Joueur bleu : W/A/S/D ou les flèches",
            "Joueur rouge (mode 2 joueurs) : flèches haut/bas/gauche/droite",
            "Percute le ballon pour le tirer vers le but.",
            "Percuter l'autre joueur peut donner un carton jaune,",
            "deux cartons jaunes donnent un carton rouge et ralentissent le joueur.",
            "Si le Rouge reçoit un carton rouge, le Vert entre, bien plus fort.",
            "Le premier à marquer {n} buts gagne le match !",
            "Recommencer : R      Retour au menu : Échap",
        ],
        "team_blue": "Bleu",
        "team_red": "Rouge",
        "team_green": "Vert",
        "win_note": "Le premier à marquer {n} buts gagne !",
        "controls_hint": "{blue} : W/A/S/D ou flèches, R = recommencer",
        "mode_ai": "1 Joueur contre IA",
        "mode_2p": "2 Joueurs",
        "esc_menu": "Échap = menu",
        "goal": "BUT !",
        "yellow_card": "Carton jaune : {name} !",
        "red_card": "Carton rouge : {name} !",
        "already_sent_off": "Déjà expulsé : {name}",
        "red_card_leaving": "CARTON ROUGE ! {name} quitte le terrain...",
        "green_coming": "Vert entre sur le terrain...",
        "green_on": "Vert est en jeu !",
        "wins_match": "{name} GAGNE LE MATCH !",
        "wins_bang": "{name} GAGNE !",
        "final_score": "Score final : {s1} - {s2}",
        "play_again": "Appuie sur R pour rejouer   Échap pour le menu",
    },
}

_HEBREW_RUN_RE = re.compile(r'[֐-׿]+|[^֐-׿]+')


def _rtl_fix(text):
    """Best-effort RTL layout for Hebrew without a full bidi engine: reverse each
    Hebrew run internally and reverse the overall run order, but keep non-Hebrew
    runs (numbers, punctuation, latin key names) internally untouched so things
    like scores and 'W/A/S/D' don't come out backwards."""
    runs = _HEBREW_RUN_RE.findall(text)
    fixed = [run[::-1] if run and '֐' <= run[0] <= '׿' else run for run in runs]
    return "".join(reversed(fixed))


def T(language, key, **kwargs):
    """Look up and format a translated string (or list of strings) for the given language."""
    table = TRANSLATIONS.get(language, TRANSLATIONS["en"])
    template = table.get(key, TRANSLATIONS["en"].get(key, key))

    def _finish(text):
        text = text.format(**kwargs) if kwargs else text
        if language in RTL_LANGUAGES:
            text = _rtl_fix(text)
        return text

    if isinstance(template, list):
        return [_finish(line) for line in template]
    return _finish(template)


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def world_to_screen(x, y, camera):
    return (
        WIDTH // 2 + (x - camera["x"]) * camera["zoom"],
        HEIGHT // 2 + (y - camera["y"]) * camera["zoom"],
    )


def world_length(value, camera):
    return max(1, int(value * camera["zoom"]))


class Player:
    def __init__(self, x, y, color, up_keys, down_keys, left_keys, right_keys, speed_multiplier=1.0):
        self.x = x
        self.y = y
        self.color = color
        self.keys = (
            tuple(up_keys) if isinstance(up_keys, (list, tuple)) else (up_keys,),
            tuple(down_keys) if isinstance(down_keys, (list, tuple)) else (down_keys,),
            tuple(left_keys) if isinstance(left_keys, (list, tuple)) else (left_keys,),
            tuple(right_keys) if isinstance(right_keys, (list, tuple)) else (right_keys,),
        )
        self.score = 0
        self.vx = 0
        self.vy = 0
        self.name = ""
        self.yellow_cards = 0
        self.red_card = False
        self.card_timer = 0
        self.speed_multiplier = speed_multiplier
        self.super_ai = False

    def get_speed_multiplier(self):
        if self.red_card:
            return 0.25
        if self.card_timer > 0:
            return 0.7
        return 1.0

    def issue_yellow_card(self):
        """Returns an (event_code, team_id) tuple; the caller localizes the message."""
        if self.red_card:
            return ("already_sent_off", self.name)
        self.yellow_cards += 1
        self.card_timer = YELLOW_CARD_DURATION
        if self.yellow_cards >= 2:
            self.red_card = True
            self.card_timer = YELLOW_CARD_DURATION * 2
            return ("red_card", self.name)
        return ("yellow_card", self.name)

    def move(self, pressed):
        dx = 0
        dy = 0
        if any(pressed[k] for k in self.keys[0]):
            dy -= 1
        if any(pressed[k] for k in self.keys[1]):
            dy += 1
        if any(pressed[k] for k in self.keys[2]):
            dx -= 1
        if any(pressed[k] for k in self.keys[3]):
            dx += 1

        if dx or dy:
            distance = math.hypot(dx, dy)
            speed = PLAYER_SPEED * self.speed_multiplier * self.get_speed_multiplier()
            self.vx = dx / distance * speed
            self.vy = dy / distance * speed
        else:
            self.vx = 0
            self.vy = 0

        self.x += self.vx
        self.y += self.vy
        self.x = clamp(self.x, PLAYER_RADIUS + GOAL_WIDTH, WIDTH - PLAYER_RADIUS - GOAL_WIDTH)
        self.y = clamp(self.y, PLAYER_RADIUS + 10, HEIGHT - PLAYER_RADIUS - 10)

        if self.card_timer > 0:
            self.card_timer -= 1

    @property
    def pos(self):
        return self.x, self.y

    def draw(self, surf, camera):
        px, py = world_to_screen(self.x, self.y, camera)
        radius = max(8, world_length(PLAYER_RADIUS, camera))
        shadow = pygame.Rect(int(px - radius * 1.1), int(py + radius * 0.5), int(radius * 2.2), int(radius * 0.5))
        pygame.draw.ellipse(surf, (10, 10, 10), shadow)
        pygame.draw.circle(surf, self.color, (int(px), int(py)), radius)
        pygame.draw.circle(surf, WHITE, (int(px), int(py)), radius, 3)
        if self.card_timer > 0:
            card_color = RED if self.red_card else YELLOW
            card_size = max(10, world_length(14, camera))
            card_rect = pygame.Rect(int(px + radius * 0.7), int(py - radius - card_size - 4), card_size, int(card_size * 1.4))
            pygame.draw.rect(surf, card_color, card_rect, border_radius=4)
            pygame.draw.rect(surf, BLACK, card_rect, 2, border_radius=4)

    def move_ai(self, ball):
        target_x = WIDTH - 220
        target_y = HEIGHT // 2
        chase_margin = 80 if not self.super_ai else 120
        if ball.x > WIDTH // 2 or abs(ball.y - self.y) > chase_margin:
            lead = 3 if self.super_ai else 0
            target_x = clamp(ball.x + ball.vx * lead + 60, WIDTH // 2 + PLAYER_RADIUS + GOAL_WIDTH, WIDTH - PLAYER_RADIUS - GOAL_WIDTH)
            target_y = clamp(ball.y + ball.vy * lead, PLAYER_RADIUS + 10, HEIGHT - PLAYER_RADIUS - 10)

        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        speed = PLAYER_SPEED * self.speed_multiplier * self.get_speed_multiplier()
        if ball.x <= WIDTH // 2:
            # A little sharper than the regular AI, but still slows down on defense.
            speed *= 0.7 if self.super_ai else 0.55

        if distance > 1:
            # Ease off as it nears the target so it doesn't overshoot the ball and flip
            # direction every frame (that flip-flop is what looks like shaking/vibrating).
            arrive_speed = speed * clamp(distance / 40, 0.25, 1.0)
            desired_vx = dx / distance * arrive_speed
            desired_vy = dy / distance * arrive_speed
        else:
            desired_vx = 0
            desired_vy = 0

        # Ease the actual velocity toward the desired one instead of snapping to it,
        # so a flipped target doesn't cause an instant direction reversal.
        steer = 0.3
        self.vx += (desired_vx - self.vx) * steer
        self.vy += (desired_vy - self.vy) * steer

        self.x += self.vx
        self.y += self.vy
        self.x = clamp(self.x, PLAYER_RADIUS + GOAL_WIDTH, WIDTH - PLAYER_RADIUS - GOAL_WIDTH)
        self.y = clamp(self.y, PLAYER_RADIUS + 10, HEIGHT - PLAYER_RADIUS - 10)

        if self.card_timer > 0:
            self.card_timer -= 1


class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.vx = 0
        self.vy = 0

    @property
    def pos(self):
        return self.x, self.y

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= BALL_FRICTION
        self.vy *= BALL_FRICTION

        if abs(self.vx) < 0.05:
            self.vx = 0
        if abs(self.vy) < 0.05:
            self.vy = 0

        if self.y - BALL_RADIUS <= 0 or self.y + BALL_RADIUS >= HEIGHT:
            self.vy = -self.vy
            self.y = clamp(self.y, BALL_RADIUS, HEIGHT - BALL_RADIUS)

        if self.x - BALL_RADIUS <= GOAL_WIDTH and not (HEIGHT//2 - GOAL_HEIGHT//2 < self.y < HEIGHT//2 + GOAL_HEIGHT//2):
            self.vx = -self.vx
            self.x = GOAL_WIDTH + BALL_RADIUS
        if self.x + BALL_RADIUS >= WIDTH - GOAL_WIDTH and not (HEIGHT//2 - GOAL_HEIGHT//2 < self.y < HEIGHT//2 + GOAL_HEIGHT//2):
            self.vx = -self.vx
            self.x = WIDTH - GOAL_WIDTH - BALL_RADIUS

    def kick(self, player):
        dx = self.x - player.x
        dy = self.y - player.y
        distance = math.hypot(dx, dy) or 1
        if distance <= PLAYER_RADIUS + BALL_RADIUS + 6:
            momentum = math.hypot(player.vx, player.vy)
            power = 10 + min(8, momentum * 1.25)
            self.vx = clamp(dx / distance * power + player.vx * 0.8, -BALL_MAX_SPEED, BALL_MAX_SPEED)
            self.vy = clamp(dy / distance * power + player.vy * 0.8, -BALL_MAX_SPEED, BALL_MAX_SPEED)
            overlap = PLAYER_RADIUS + BALL_RADIUS - distance + 2
            self.x += dx / distance * overlap
            self.y += dy / distance * overlap

    def draw(self, surf, camera):
        px, py = world_to_screen(self.x, self.y, camera)
        radius = max(6, world_length(BALL_RADIUS, camera))
        shadow = pygame.Rect(int(px - radius * 0.8), int(py + radius * 0.4), int(radius * 1.6), int(radius * 0.5))
        pygame.draw.ellipse(surf, (20, 20, 20), shadow)
        pygame.draw.circle(surf, YELLOW, (int(px), int(py)), radius)
        pygame.draw.circle(surf, BLACK, (int(px), int(py)), radius, 2)
        highlight = pygame.Rect(int(px - radius * 0.4), int(py - radius * 0.6), int(radius * 0.6), int(radius * 0.35))
        pygame.draw.ellipse(surf, WHITE, highlight)


player_move_vector = [0, 0]


def draw_crowd(surf):
    stand_height = 90
    band_height = 30
    top_band = pygame.Rect(0, 0, WIDTH, stand_height)
    bottom_band = pygame.Rect(0, HEIGHT - stand_height, WIDTH, stand_height)
    pygame.draw.rect(surf, (30, 30, 80), top_band)
    pygame.draw.rect(surf, (30, 30, 80), bottom_band)

    for y in (16, HEIGHT - stand_height + 16, HEIGHT - 32):
        for x in range(20, WIDTH, 18):
            color = (180 + ((x // 18) % 2) * 40, 180 - ((x // 36) % 2) * 50, 100 + ((x // 54) % 2) * 60)
            pygame.draw.rect(surf, color, (x, y, 12, 12), border_radius=3)

    pygame.draw.line(surf, WHITE, (0, stand_height), (WIDTH, stand_height), 4)
    pygame.draw.line(surf, WHITE, (0, HEIGHT - stand_height), (WIDTH, HEIGHT - stand_height), 4)


def draw_pitch_background(surf):
    """A top-down mowed pitch used behind the start menu."""
    stripe_width = 42
    light = (75, 150, 76)
    dark = (57, 128, 58)
    for i, x in enumerate(range(0, WIDTH, stripe_width)):
        color = light if i % 2 == 0 else dark
        pygame.draw.rect(surf, color, (x, 0, stripe_width, HEIGHT))

    margin = 34
    line_color = (232, 238, 232)
    line_w = 3
    field_rect = pygame.Rect(margin, margin, WIDTH - margin * 2, HEIGHT - margin * 2)
    pygame.draw.rect(surf, line_color, field_rect, line_w, border_radius=4)

    pygame.draw.line(surf, line_color, (WIDTH // 2, margin), (WIDTH // 2, HEIGHT - margin), line_w)
    pygame.draw.circle(surf, line_color, (WIDTH // 2, HEIGHT // 2), 72, line_w)
    pygame.draw.circle(surf, line_color, (WIDTH // 2, HEIGHT // 2), 4)

    pen_w, pen_h = 130, 240
    goal_w, goal_h = 55, 120
    for side in (-1, 1):
        pen_x = margin if side == -1 else WIDTH - margin - pen_w
        pen_rect = pygame.Rect(pen_x, HEIGHT // 2 - pen_h // 2, pen_w, pen_h)
        pygame.draw.rect(surf, line_color, pen_rect, line_w)

        goal_x = margin if side == -1 else WIDTH - margin - goal_w
        goal_rect = pygame.Rect(goal_x, HEIGHT // 2 - goal_h // 2, goal_w, goal_h)
        pygame.draw.rect(surf, line_color, goal_rect, line_w)

        spot_x = margin + 95 if side == -1 else WIDTH - margin - 95
        pygame.draw.circle(surf, line_color, (spot_x, HEIGHT // 2), 3)

        corner_r = 16
        corner_center = (margin, margin) if side == -1 else (WIDTH - margin, margin)
        start_angle, end_angle = (0, math.pi / 2) if side == -1 else (math.pi / 2, math.pi)
        pygame.draw.arc(
            surf, line_color,
            (corner_center[0] - corner_r, corner_center[1] - corner_r, corner_r * 2, corner_r * 2),
            start_angle, end_angle, line_w,
        )
        corner_center_b = (margin, HEIGHT - margin) if side == -1 else (WIDTH - margin, HEIGHT - margin)
        start_angle_b, end_angle_b = (-math.pi / 2, 0) if side == -1 else (math.pi, math.pi * 1.5)
        pygame.draw.arc(
            surf, line_color,
            (corner_center_b[0] - corner_r, corner_center_b[1] - corner_r, corner_r * 2, corner_r * 2),
            start_angle_b, end_angle_b, line_w,
        )


def draw_field(surf, camera):
    draw_crowd(surf)
    field_corners = [
        (GOAL_WIDTH, 0),
        (WIDTH - GOAL_WIDTH, 0),
        (WIDTH - GOAL_WIDTH, HEIGHT),
        (GOAL_WIDTH, HEIGHT),
    ]
    field_poly = [world_to_screen(x, y, camera) for x, y in field_corners]
    pygame.draw.polygon(surf, GREEN, field_poly)
    pygame.draw.polygon(surf, WHITE, field_poly, world_length(18, camera))

    for i in range(0, WIDTH, 40):
        top = world_to_screen(i, 0, camera)
        bottom = world_to_screen(i, HEIGHT, camera)
        pygame.draw.line(surf, (40, 160, 40), top, bottom, max(1, world_length(20, camera)))

    halfway_top = world_to_screen(WIDTH // 2, 0, camera)
    halfway_bottom = world_to_screen(WIDTH // 2, HEIGHT, camera)
    pygame.draw.line(surf, WHITE, halfway_top, halfway_bottom, world_length(6, camera))

    left_goal_poly = [
        world_to_screen(0, HEIGHT // 2 - GOAL_HEIGHT // 2, camera),
        world_to_screen(GOAL_WIDTH, HEIGHT // 2 - GOAL_HEIGHT // 2, camera),
        world_to_screen(GOAL_WIDTH, HEIGHT // 2 + GOAL_HEIGHT // 2, camera),
        world_to_screen(0, HEIGHT // 2 + GOAL_HEIGHT // 2, camera),
    ]
    right_goal_poly = [
        world_to_screen(WIDTH - GOAL_WIDTH, HEIGHT // 2 - GOAL_HEIGHT // 2, camera),
        world_to_screen(WIDTH, HEIGHT // 2 - GOAL_HEIGHT // 2, camera),
        world_to_screen(WIDTH, HEIGHT // 2 + GOAL_HEIGHT // 2, camera),
        world_to_screen(WIDTH - GOAL_WIDTH, HEIGHT // 2 + GOAL_HEIGHT // 2, camera),
    ]
    pygame.draw.polygon(surf, (200, 220, 255), left_goal_poly)
    pygame.draw.polygon(surf, (200, 220, 255), right_goal_poly)
    pygame.draw.lines(surf, WHITE, True, left_goal_poly, world_length(6, camera))
    pygame.draw.lines(surf, WHITE, True, right_goal_poly, world_length(6, camera))

    center = world_to_screen(WIDTH // 2, HEIGHT // 2, camera)
    pygame.draw.circle(surf, WHITE, (int(center[0]), int(center[1])), world_length(90, camera), world_length(6, camera))
    pygame.draw.circle(surf, WHITE, (int(center[0]), int(center[1])), world_length(12, camera))

    pygame.draw.rect(surf, WHITE, (WIDTH // 2 - 100, 20, 200, 40), border_radius=10)


def draw_scoreboard(surf, p1, p2):
    panel_w, panel_h = 260, 56
    panel_rect = pygame.Rect(WIDTH // 2 - panel_w // 2, 12, panel_w, panel_h)

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (8, 10, 16, 190), panel_surf.get_rect(), border_radius=12)
    surf.blit(panel_surf, panel_rect.topleft)
    pygame.draw.rect(surf, WHITE, panel_rect, 2, border_radius=12)
    pygame.draw.line(surf, (90, 90, 100), (panel_rect.centerx, panel_rect.y + 8),
                      (panel_rect.centerx, panel_rect.bottom - 8), 2)

    swatch_r = 10
    pygame.draw.circle(surf, p1.color, (panel_rect.x + 30, panel_rect.centery), swatch_r)
    pygame.draw.circle(surf, WHITE, (panel_rect.x + 30, panel_rect.centery), swatch_r, 1)
    pygame.draw.circle(surf, p2.color, (panel_rect.right - 30, panel_rect.centery), swatch_r)
    pygame.draw.circle(surf, WHITE, (panel_rect.right - 30, panel_rect.centery), swatch_r, 1)

    left_score = FONT.render(str(p1.score), True, WHITE)
    right_score = FONT.render(str(p2.score), True, WHITE)
    surf.blit(left_score, (panel_rect.centerx - 18 - left_score.get_width(), panel_rect.centery - left_score.get_height() // 2))
    surf.blit(right_score, (panel_rect.centerx + 18, panel_rect.centery - right_score.get_height() // 2))


def draw_ui(surf, p1, p2, goal_text="", language="en"):
    draw_scoreboard(surf, p1, p2)
    win_note = T(language, "win_note", n=WIN_SCORE)
    controls = T(language, "controls_hint", blue=T(language, "team_blue"))
    help_text = SMALL_FONT.render(f"{win_note}   {controls}", True, WHITE)
    surf.blit(help_text, (WIDTH//2 - help_text.get_width()//2, 72))
    if goal_text:
        goal_render = FONT.render(goal_text, True, YELLOW)
        surf.blit(goal_render, (WIDTH//2 - goal_render.get_width()//2, HEIGHT//2 - 120))


def check_goal(ball, p1, p2):
    if ball.x - BALL_RADIUS <= 0 and HEIGHT//2 - GOAL_HEIGHT//2 < ball.y < HEIGHT//2 + GOAL_HEIGHT//2:
        p2.score += 1
        ball.reset()
        return True
    if ball.x + BALL_RADIUS >= WIDTH and HEIGHT//2 - GOAL_HEIGHT//2 < ball.y < HEIGHT//2 + GOAL_HEIGHT//2:
        p1.score += 1
        ball.reset()
        return True
    return False


def resolve_collision(ball, player):
    dx = ball.x - player.x
    dy = ball.y - player.y
    distance = math.hypot(dx, dy)
    if distance == 0:
        return
    if distance < BALL_RADIUS + PLAYER_RADIUS:
        overlap = BALL_RADIUS + PLAYER_RADIUS - distance
        ball.x += dx / distance * overlap
        ball.y += dy / distance * overlap
        ball.kick(player)


def resolve_player_collision(p1, p2, ball):
    """Returns an (event_code, team_id) tuple from Player.issue_yellow_card, or None."""
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    distance = math.hypot(dx, dy)
    if distance == 0:
        return None
    if distance < PLAYER_RADIUS * 2:
        overlap = PLAYER_RADIUS * 2 - distance
        half_dx = dx / distance * overlap * 0.5
        half_dy = dy / distance * overlap * 0.5
        p1.x -= half_dx
        p1.y -= half_dy
        p2.x += half_dx
        p2.y += half_dy

        ball_dist1 = math.hypot(ball.x - p1.x, ball.y - p1.y)
        ball_dist2 = math.hypot(ball.x - p2.x, ball.y - p2.y)
        if ball_dist1 < ball_dist2:
            return p2.issue_yellow_card()
        return p1.issue_yellow_card()
    return None


class Match:
    def __init__(self, mode, language="en"):
        self.mode = mode  # "ai" or "2p"
        self.language = language
        self.player1 = self._make_player1()
        self.player2 = self._make_player2()

        self.camera = {
            "x": self.player1.x,
            "y": self.player1.y,
            "zoom": CAMERA_ZOOM_IDLE,
        }
        self.ball = Ball()
        self.goal_text = ""
        self.goal_timer = 0
        self.sub_anim = None
        self.finished = False
        self.winner_id = None

    @staticmethod
    def _make_player1():
        player1 = Player(
            220,
            HEIGHT // 2,
            BLUE,
            (pygame.K_w, pygame.K_UP),
            (pygame.K_s, pygame.K_DOWN),
            (pygame.K_a, pygame.K_LEFT),
            (pygame.K_d, pygame.K_RIGHT),
            speed_multiplier=1.35,
        )
        player1.name = "blue"
        return player1

    @staticmethod
    def _make_player2():
        player2 = Player(WIDTH - 220, HEIGHT // 2, RED, pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)
        player2.name = "red"
        return player2

    def restart(self):
        self.player1 = self._make_player1()
        self.player2 = self._make_player2()
        self.ball.reset()
        self.goal_text = ""
        self.goal_timer = 0
        self.sub_anim = None
        self.finished = False
        self.winner_id = None

    def start_green_substitution(self):
        """Red is sent off: he walks to the sideline while Green walks on to replace him."""
        old = self.player2
        if old.color == SUPER_GREEN:
            # Already substituted - just clear the cards, no need to animate again.
            old.yellow_cards = 0
            old.red_card = False
            old.card_timer = 0
            return

        sideline_x = clamp(old.x, GOAL_WIDTH + PLAYER_RADIUS, WIDTH - GOAL_WIDTH - PLAYER_RADIUS)
        leave_start = (old.x, old.y)
        leave_end = (sideline_x, HEIGHT + 70)
        enter_end = (old.x, old.y)

        new_player = Player(
            leave_end[0], leave_end[1],
            SUPER_GREEN,
            old.keys[0], old.keys[1], old.keys[2], old.keys[3],
            speed_multiplier=SUPER_SPEED_MULTIPLIER,
        )
        new_player.name = "green"
        new_player.score = old.score
        if self.mode == "ai":
            new_player.super_ai = True

        old.vx = 0
        old.vy = 0

        self.sub_anim = {
            "phase": "leaving",
            "timer": 0,
            "leave_start": leave_start,
            "leave_end": leave_end,
            "enter_start": leave_end,
            "enter_end": enter_end,
            "new_player": new_player,
        }
        self.goal_text = T(self.language, "red_card_leaving", name=T(self.language, f"team_{old.name}"))
        self.goal_timer = SUB_LEAVE_DURATION + SUB_ENTER_DURATION + 40

    def _advance_substitution(self):
        anim = self.sub_anim
        anim["timer"] += 1

        if anim["phase"] == "leaving":
            t = min(1.0, anim["timer"] / SUB_LEAVE_DURATION)
            sx, sy = anim["leave_start"]
            ex, ey = anim["leave_end"]
            self.player2.x = sx + (ex - sx) * t
            self.player2.y = sy + (ey - sy) * t
            if t >= 1.0:
                anim["phase"] = "entering"
                anim["timer"] = 0
                self.goal_text = T(self.language, "green_coming")

        elif anim["phase"] == "entering":
            t = min(1.0, anim["timer"] / SUB_ENTER_DURATION)
            sx, sy = anim["enter_start"]
            ex, ey = anim["enter_end"]
            new_player = anim["new_player"]
            new_player.x = sx + (ex - sx) * t
            new_player.y = sy + (ey - sy) * t
            if t >= 1.0:
                self.player2 = new_player
                self.sub_anim = None
                self.goal_text = T(self.language, "green_on")
                self.goal_timer = GOAL_TEXT_DURATION

    def update(self, pressed):
        if self.finished:
            return

        animating = self.sub_anim is not None

        self.player1.move(pressed)
        if not animating:
            if self.mode == "2p":
                self.player2.move(pressed)
            else:
                self.player2.move_ai(self.ball)
        self.ball.update()

        resolve_collision(self.ball, self.player1)

        result_text = ""
        if not animating:
            resolve_collision(self.ball, self.player2)
            p2_had_red = self.player2.red_card
            event = resolve_player_collision(self.player1, self.player2, self.ball)
            if not p2_had_red and self.player2.red_card:
                self.start_green_substitution()
                animating = True
            elif event:
                code, team_id = event
                result_text = T(self.language, code, name=T(self.language, f"team_{team_id}"))
        else:
            self._advance_substitution()

        if check_goal(self.ball, self.player1, self.player2):
            result_text = T(self.language, "goal")

        if result_text:
            self.goal_text = result_text
            self.goal_timer = GOAL_TEXT_DURATION

        if self.player1.score >= WIN_SCORE or self.player2.score >= WIN_SCORE:
            self.finished = True
            winner = self.player1 if self.player1.score >= WIN_SCORE else self.player2
            self.winner_id = winner.name
            self.goal_text = T(self.language, "wins_match", name=T(self.language, f"team_{winner.name}"))
            self.goal_timer = GOAL_TEXT_DURATION
            return

        target_zoom = CAMERA_ZOOM_ACTIVE if (abs(self.player1.vx) + abs(self.player1.vy)) > 0.1 else CAMERA_ZOOM_IDLE
        target_zoom = clamp(target_zoom, CAMERA_ZOOM_MIN, CAMERA_ZOOM_MAX)
        self.camera["zoom"] += (target_zoom - self.camera["zoom"]) * CAMERA_ZOOM_SPEED

        visible_half_width = WIDTH / (2 * self.camera["zoom"])
        visible_half_height = HEIGHT / (2 * self.camera["zoom"])
        camera_target_x = clamp(self.player1.x, visible_half_width, WIDTH - visible_half_width)
        camera_target_y = clamp(self.player1.y, visible_half_height, HEIGHT - visible_half_height)
        self.camera["x"] += (camera_target_x - self.camera["x"]) * CAMERA_MOVE_SPEED
        self.camera["y"] += (camera_target_y - self.camera["y"]) * CAMERA_MOVE_SPEED

        if self.goal_timer > 0:
            self.goal_timer -= 1
            if self.goal_timer == 0:
                self.goal_text = ""

    def draw(self, surf):
        draw_field(surf, self.camera)
        self.player1.draw(surf, self.camera)
        self.player2.draw(surf, self.camera)
        if self.sub_anim and self.sub_anim["phase"] == "entering":
            self.sub_anim["new_player"].draw(surf, self.camera)
        self.ball.draw(surf, self.camera)
        draw_ui(surf, self.player1, self.player2, self.goal_text if not self.finished else "", self.language)
        mode_key = "mode_2p" if self.mode == "2p" else "mode_ai"
        mode_label = T(self.language, mode_key)
        esc_label = T(self.language, "esc_menu")
        mode_render = SMALL_FONT.render(f"{mode_label}   {esc_label}", True, WHITE)
        surf.blit(mode_render, (WIDTH // 2 - mode_render.get_width() // 2, 98))

        if self.finished:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surf.blit(overlay, (0, 0))
            winner_display = T(self.language, f"team_{self.winner_id}")
            t1 = LARGE_FONT.render(T(self.language, "wins_bang", name=winner_display).upper(), True, WHITE)
            t2 = FONT.render(T(self.language, "final_score", s1=self.player1.score, s2=self.player2.score), True, WHITE)
            t3 = SMALL_FONT.render(T(self.language, "play_again"), True, (220, 220, 220))
            surf.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 70))
            surf.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 + 2))
            surf.blit(t3, (WIDTH // 2 - t3.get_width() // 2, HEIGHT // 2 + 44))


class Button:
    def __init__(self, rect, label, sub_label=""):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.sub_label = sub_label

    def is_hover(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surf, hovered):
        base = (40, 170, 60) if hovered else DARK_GREEN
        edge = (200, 255, 200) if hovered else WHITE
        pygame.draw.rect(surf, base, self.rect, border_radius=10)
        pygame.draw.rect(surf, edge, self.rect, 2, border_radius=10)
        text = FONT.render(self.label, True, WHITE)
        ty = self.rect.centery - text.get_height() // 2 - (8 if self.sub_label else 0)
        surf.blit(text, (self.rect.centerx - text.get_width() // 2, ty))
        if self.sub_label:
            sub = SMALL_FONT.render(self.sub_label, True, (220, 220, 220))
            surf.blit(sub, (self.rect.centerx - sub.get_width() // 2, ty + 32))


class App:
    """Owns the top-level flow: main menu, how-to-play screen and the running Match."""

    def __init__(self):
        self.state = "menu"
        self.match = None

        cx = WIDTH // 2
        self.menu_buttons = [
            ("ai", Button((cx - 170, 230, 340, 68), "PLAY", "1 Player vs AI")),
            ("2p", Button((cx - 170, 316, 340, 68), "2 PLAYERS", "Local co-op on one keyboard")),
            ("help", Button((cx - 170, 402, 340, 68), "HOW TO PLAY")),
            ("quit", Button((cx - 170, 488, 340, 68), "QUIT")),
        ]
        self.back_button = Button((40, HEIGHT - 96, 160, 52), "BACK")

    def start_match(self, mode):
        self.match = Match(mode)
        self.state = "play"

    def handle_click(self, pos):
        if self.state == "menu":
            for key, button in self.menu_buttons:
                if button.is_hover(pos):
                    if key == "ai":
                        self.start_match("ai")
                    elif key == "2p":
                        self.start_match("2p")
                    elif key == "help":
                        self.state = "how_to_play"
                    elif key == "quit":
                        pygame.quit()
                        sys.exit()
                    return
        elif self.state == "how_to_play":
            if self.back_button.is_hover(pos):
                self.state = "menu"

    def handle_keydown(self, key):
        if self.state == "play":
            if key == pygame.K_ESCAPE:
                self.state = "menu"
            elif key == pygame.K_r:
                self.match.restart()
        else:
            if key == pygame.K_ESCAPE:
                if self.state == "menu":
                    pygame.quit()
                    sys.exit()
                else:
                    self.state = "menu"
            elif key == pygame.K_RETURN and self.state == "menu":
                self.start_match("ai")

    def draw_menu(self, surf):
        draw_pitch_background(surf)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 20, 8, 120))
        surf.blit(overlay, (0, 0))

        title = LARGE_FONT.render("FOOTBALL", True, WHITE)
        title_shadow = LARGE_FONT.render("FOOTBALL", True, (0, 0, 0))
        surf.blit(title_shadow, (WIDTH // 2 - title.get_width() // 2 + 3, 103))
        surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
        subtitle = SMALL_FONT.render("Score more goals than your opponent", True, (225, 235, 225))
        surf.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 172))

        mouse = pygame.mouse.get_pos()
        for _, button in self.menu_buttons:
            button.draw(surf, button.is_hover(mouse))

    def draw_how_to_play(self, surf):
        surf.fill((14, 40, 18))
        title = FONT.render("HOW TO PLAY", True, WHITE)
        surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 90))

        lines = [
            "Blue player: W/A/S/D or Arrow keys",
            "Red player (2 Players mode): Up/Down/Left/Right",
            "Bump into the ball to kick it towards the goal.",
            "Colliding with the other player can earn a yellow card,",
            "two yellow cards give a red card and slow the player down.",
            "If Red gets a red card, Green comes on as a tougher substitute.",
            f"First to {WIN_SCORE} goals wins the match!",
            "Restart the match: R      Back to menu: Esc",
        ]
        for i, line in enumerate(lines):
            t = SMALL_FONT.render(line, True, (220, 230, 220))
            surf.blit(t, (WIDTH // 2 - t.get_width() // 2, 170 + i * 34))

        mouse = pygame.mouse.get_pos()
        self.back_button.draw(surf, self.back_button.is_hover(mouse))

    def draw(self, surf):
        if self.state == "menu":
            self.draw_menu(surf)
        elif self.state == "how_to_play":
            self.draw_how_to_play(surf)
        elif self.state == "play":
            self.match.draw(surf)


def main():
    app = App()

    while True:
        CLOCK.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                app.handle_keydown(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                app.handle_click(event.pos)

        if app.state == "play":
            pressed = pygame.key.get_pressed()
            app.match.update(pressed)

        app.draw(SCREEN)
        pygame.display.flip()


if __name__ == "__main__":
    main()
