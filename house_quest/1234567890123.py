# -*- coding: utf-8 -*-
"""
משחק קווסט - הבית בלילה
========================
משחק הרפתקאות ראשוני-גוף (First Person) בנוי במנוע Ursina.

איך משחקים:
    W A S D  - תנועה
    עכבר     - הסתכלות
    רווח     - קפיצה (בשלב המבוך)
    קליק שמאלי - אינטראקציה עם עצמים (תיבת דואר, דלת, ארון, כספת, פתקים, ספר...)
    Esc       - שחרור/נעילת העכבר

כדי להריץ:
    pip install ursina
    python quest_game.py
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

window.title = "הבית בלילה - משחק קווסט"
window.borderless = False
window.fps_counter.enabled = True
window.exit_button.visible = False

# ---------------------------------------------------------------------------
# מצב המשחק הגלובלי
# ---------------------------------------------------------------------------
state = {
    'has_key': False,          # יש לשחקן מפתח
    'mailbox_open': False,     # תיבת הדואר נפתחה
    'door_unlocked': False,    # דלת הכניסה נפתחה
    'entered_house': False,    # השחקן נכנס לבית
    'found_code_note': False,  # השחקן ראה את הפתק עם הקוד בשירותים
    'safe_open': False,        # הכספת נפתחה
    'has_book': False,         # השחקן לקח את הספר הזהוב
    'wall_open': False,        # הקיר הסודי נפתח והמבוך זמין
    'game_won': False,         # השחקן ניצח
}

SAFE_CODE = "1265983809"
input_mode = {'active': False, 'typed': ""}

# ---------------------------------------------------------------------------
# עזרי ממשק - הודעות על המסך
# ---------------------------------------------------------------------------
current_message = None

def show_message(text, duration=3, y=0.35, scale=1.6, color_=color.white):
    """מציג הודעה במרכז המסך למשך duration שניות."""
    global current_message
    if current_message:
        destroy(current_message)
    current_message = Text(
        text=text,
        origin=(0, 0),
        position=(0, y),
        scale=scale,
        color=color_,
        background=True,
        z=-1,
    )
    if duration:
        invoke(hide_message, delay=duration)


def hide_message():
    global current_message
    if current_message:
        destroy(current_message)
        current_message = None


# פתק/רמז שנשאר על המסך עד קליק נוסף (לא נעלם לבד)
note_display = None

def show_note(text):
    global note_display
    if note_display:
        destroy(note_display)
    note_display = Text(
        text=text,
        origin=(0, 0),
        position=(0, 0.25),
        scale=1.4,
        color=color.yellow,
        background=True,
        z=-1,
    )
    invoke(lambda: destroy(note_display), delay=4.5)


# ---------------------------------------------------------------------------
# עצם לחיץ בסיסי
# ---------------------------------------------------------------------------
class Clickable(Entity):
    """Entity שמריץ פונקציה כאשר לוחצים עליו עם קליק שמאלי."""
    def __init__(self, on_click=None, **kwargs):
        super().__init__(**kwargs)
        # ursina לא מקבל None ב-on_click, ולכן מציבים רק פונקציה אמיתית.
        # את הקליק עצמו ursina מפעיל לבד (לכל האובייקטים כאן יש collider).
        if on_click:
            self.on_click = on_click


# ---------------------------------------------------------------------------
# עולם: תאורה, שמיים בלילה, קרקע
# ---------------------------------------------------------------------------
Sky(color=color.rgb(10, 12, 35))
scene.fog_color = color.rgb(10, 12, 35)
scene.fog_density = 0.012

AmbientLight(color=color.rgba(90, 90, 130, 255))
moon = DirectionalLight(y=2, z=3, shadows=False)
moon.look_at(Vec3(1, -1, 1))

ground = Entity(
    model='plane', scale=(200, 1, 200), position=(0, 0, 0),
    texture='white_cube', texture_scale=(80, 80),
    color=color.rgb(20, 40, 25), collider='box'
)

# ---------------------------------------------------------------------------
# פריסת העולם (ציר Z הולך "פנימה" - עומק המשחק)
# ---------------------------------------------------------------------------
WALL_COLOR = color.rgb(90, 80, 70)
FLOOR_COLOR = color.rgb(120, 100, 80)
WALL_H = 4

def wall(pos, scale):
    return Entity(model='cube', color=WALL_COLOR, position=pos, scale=scale, collider='box')

def floor_tile(pos, scale, c=FLOOR_COLOR):
    # scale = (רוחב, עומק), ואפשר גם (רוחב, גובה, עומק) - לוקחים את האיבר האחרון כעומק
    return Entity(model='cube', color=c, position=(pos[0], pos[1]-0.05, pos[2]), scale=(scale[0], 0.1, scale[-1]), collider='box')


# --- חוץ הבית (חצר) ---
player = FirstPersonController(position=(0, 1, 2), speed=6)
player.cursor.visible = False

# קיר קדמי של הבית עם פתח לדלת
wall((-5, WALL_H/2, 15), (7, WALL_H, 0.5))
wall((5.5, WALL_H/2, 15), (6, WALL_H, 0.5))
wall((0, WALL_H+1, 15), (16, 2, 0.5))
Entity(model='cube', color=color.rgb(60, 40, 30), position=(0, WALL_H, 15), scale=(16, 0.4, 0.6))  # גג-שוליים

# גג בסיסי לבית כדי שיראה כמו בית
Entity(model='cube', color=color.rgb(50, 30, 25), position=(0, WALL_H + 0.2, 30), scale=(20, 0.5, 30))

door_frame_light = PointLight(position=(0, 3, 15), color=color.rgba(255, 200, 120, 180))

house_door = Clickable(
    model='cube', color=color.rgb(70, 45, 25),
    position=(0, 1.8, 15.1), scale=(2.5, 3.6, 0.3),
    collider='box'
)

mailbox_pole = Entity(model='cube', color=color.rgb(40, 40, 40), position=(4, 0.6, 8), scale=(0.15, 1.2, 0.15))
mailbox = Clickable(
    model='cube', color=color.rgb(180, 30, 30),
    position=(4, 1.25, 8), scale=(0.6, 0.4, 0.35),
    collider='box'
)
mailbox_light = PointLight(position=(4, 1.6, 8), color=color.rgba(255, 255, 200, 90))

key_pickup = None  # ייווצר כשנפתחת תיבת הדואר


def open_mailbox():
    global key_pickup
    if state['mailbox_open']:
        return
    state['mailbox_open'] = True
    mailbox.color = color.rgb(120, 15, 15)
    show_message("תיבת הדואר נפתחה - יש בפנים מפתח!", duration=3)
    key_pickup = Clickable(
        model='cube', color=color.gold,
        position=(4, 1.1, 8.35), scale=(0.35, 0.08, 0.08),
        collider='box', on_click=None
    )
    key_pickup.on_click = pick_key


def pick_key():
    global key_pickup
    if state['has_key'] or key_pickup is None:
        return
    state['has_key'] = True
    show_message("לקחת את המפתח!", duration=2)
    destroy(key_pickup)
    key_pickup = None


mailbox.on_click = open_mailbox


def try_open_door():
    if state['entered_house']:
        return
    if not state['has_key']:
        show_message("הדלת נעולה... אולי יש מפתח איפשהו בחצר?", duration=2.5)
        return
    if not state['door_unlocked']:
        state['door_unlocked'] = True
        house_door.color = color.rgb(100, 65, 35)
        show_message("פתחת את הדלת עם המפתח!", duration=2)
    # כניסה לבית
    state['entered_house'] = True
    player.position = (0, 1, 22)
    player.rotation_y = 0
    invoke(lambda: show_message("לך למטבח", duration=3), delay=0.3)


house_door.on_click = try_open_door

# ---------------------------------------------------------------------------
# פנים הבית - מסדרון מרכזי
# ---------------------------------------------------------------------------
floor_tile((0, 0, 40), (24, 60))

wall((-12, WALL_H/2, 40), (0.5, WALL_H, 60))
wall((12, WALL_H/2, 40), (0.5, WALL_H, 60))

hallway_light1 = PointLight(position=(0, 3.5, 25), color=color.rgba(255, 225, 180, 130))
hallway_light2 = PointLight(position=(0, 3.5, 45), color=color.rgba(255, 225, 180, 130))
hallway_light3 = PointLight(position=(0, 3.5, 60), color=color.rgba(255, 225, 180, 130))

# --- מטבח (משמאל למסדרון) ---
KITCHEN_POS = (-18, 0, 28)
wall((KITCHEN_POS[0]-6, WALL_H/2, KITCHEN_POS[2]-8), (0.5, WALL_H, 10))
wall((KITCHEN_POS[0]-6, WALL_H/2, KITCHEN_POS[2]+7), (0.5, WALL_H, 4))
wall((KITCHEN_POS[0]+0.2, WALL_H/2, KITCHEN_POS[2]+9), (12.5, WALL_H, 0.5))
wall((KITCHEN_POS[0]+0.2, WALL_H/2, KITCHEN_POS[2]-9), (12.5, WALL_H, 0.5))

stove = Clickable(
    model='cube', color=color.rgb(50, 50, 50),
    position=(KITCHEN_POS[0], 0.6, KITCHEN_POS[2]-3), scale=(2, 1.2, 1.2),
    collider='box'
)
Entity(model='cube', color=color.rgb(30, 30, 30), position=(KITCHEN_POS[0], 1.25, KITCHEN_POS[2]-3), scale=(1.6, 0.05, 0.9))

kitchen_note_text = "פתק על התנור:\n\"תפתח את הארון בחדר השינה\""

def click_stove():
    show_note(kitchen_note_text)


stove.on_click = click_stove

# --- חדר שינה (מימין למסדרון) ---
BEDROOM_POS = (18, 0, 28)
wall((BEDROOM_POS[0]+6, WALL_H/2, BEDROOM_POS[2]-8), (0.5, WALL_H, 10))
wall((BEDROOM_POS[0]-0.2, WALL_H/2, BEDROOM_POS[2]-9), (12.5, WALL_H, 0.5))

bed = Entity(model='cube', color=color.rgb(120, 40, 60), position=(BEDROOM_POS[0]+3, 0.4, BEDROOM_POS[2]-4), scale=(3, 0.8, 4.5))
Entity(model='cube', color=color.rgb(220, 220, 220), position=(BEDROOM_POS[0]+3, 0.85, BEDROOM_POS[2]-5.7), scale=(2.8, 0.4, 1))

closet = Clickable(
    model='cube', color=color.rgb(70, 45, 30),
    position=(BEDROOM_POS[0]-4, 1.5, BEDROOM_POS[2]-1), scale=(2.5, 3, 1),
    collider='box'
)

safe = None

def open_closet():
    global safe
    if state.get('closet_open'):
        return
    state['closet_open'] = True
    closet.color = color.rgb(45, 28, 18)
    show_message("הארון נפתח - יש בפנים כספת!", duration=3)
    safe = Clickable(
        model='cube', color=color.rgb(40, 40, 45),
        position=(BEDROOM_POS[0]-4, 0.8, BEDROOM_POS[2]-0.3), scale=(1.3, 1.3, 0.8),
        collider='box'
    )
    safe.on_click = click_safe


closet.on_click = open_closet

# --- שירותים (מחוברים לחדר השינה, בהמשך המסדרון) ---
BATHROOM_POS = (18, 0, 40)
wall((BATHROOM_POS[0]+6, WALL_H/2, BATHROOM_POS[2]), (0.5, WALL_H, 8))
wall((BATHROOM_POS[0]-0.2, WALL_H/2, BATHROOM_POS[2]+4), (12.5, WALL_H, 0.5))

mirror = Clickable(
    model='cube', color=color.rgb(180, 210, 220),
    position=(BATHROOM_POS[0]+2, 1.6, BATHROOM_POS[2]-2), scale=(1.6, 1.6, 0.1),
    collider='box'
)
sink = Entity(model='cube', color=color.white, position=(BATHROOM_POS[0]+2, 0.6, BATHROOM_POS[2]-1.6), scale=(1.2, 0.8, 0.6))

code_note_text = f"פתק על המראה:\nהקוד לכספת הוא: {SAFE_CODE}"

def click_mirror():
    state['found_code_note'] = True
    show_note(code_note_text)


mirror.on_click = click_mirror

# --- כספת - לחיצה פותחת מצב הקלדת קוד ---

def click_safe():
    if state['safe_open']:
        show_note("הכספת כבר פתוחה, יש בפנים פתק:\n\"לך למשרד\"")
        return
    if not state['found_code_note']:
        show_message("צריך קודם למצוא את הקוד לכספת (בשירותים)", duration=2.5)
        return
    start_code_input()


def start_code_input():
    input_mode['active'] = True
    input_mode['typed'] = ""
    player.enabled = False
    mouse.locked = False
    mouse.visible = True
    refresh_code_ui()


code_ui = None

def refresh_code_ui():
    global code_ui
    if code_ui:
        destroy(code_ui)
    code_ui = Text(
        text=f"הזן קוד לכספת (Enter לאישור, Esc לביטול):\n{input_mode['typed']}_",
        origin=(0, 0), position=(0, 0.1), scale=1.6,
        color=color.azure, background=True, z=-1,
    )


def close_code_input():
    global code_ui
    input_mode['active'] = False
    input_mode['typed'] = ""
    if code_ui:
        destroy(code_ui)
        code_ui = None
    player.enabled = True
    mouse.locked = True
    mouse.visible = False


def submit_code():
    global code_ui
    if input_mode['typed'] == SAFE_CODE:
        state['safe_open'] = True
        close_code_input()
        show_message("הקוד נכון! הכספת נפתחת...", duration=2)
        invoke(lambda: show_note("בתוך הכספת יש פתק:\n\"לך למשרד\""), delay=2.1)
    else:
        input_mode['typed'] = ""
        refresh_code_ui()
        show_message("קוד שגוי, נסה שוב", duration=1.5)


# --- משרד (בקצה המסדרון) ---
OFFICE_POS = (0, 0, 60)
wall((OFFICE_POS[0]-12, WALL_H/2, OFFICE_POS[2]+8), (0.5, WALL_H, 16))
wall((OFFICE_POS[0]+12, WALL_H/2, OFFICE_POS[2]+8), (0.5, WALL_H, 16))
office_back_wall = Entity(model='cube', color=WALL_COLOR, position=(OFFICE_POS[0], WALL_H/2, OFFICE_POS[2]+16), scale=(24, WALL_H, 0.5), collider='box')

desk = Clickable(
    model='cube', color=color.rgb(80, 55, 35),
    position=(OFFICE_POS[0], 0.6, OFFICE_POS[2]+4), scale=(3, 1.2, 1.5),
    collider='box'
)

office_note_text = "פתק על השולחן:\n\"קח את הספר הזהוב מהמדף\""

def click_desk():
    show_note(office_note_text)


desk.on_click = click_desk

shelf = Entity(model='cube', color=color.rgb(60, 40, 25), position=(OFFICE_POS[0], 2, OFFICE_POS[2]+15.4), scale=(10, 3.4, 0.6))
golden_book = Clickable(
    model='cube', color=color.gold,
    position=(OFFICE_POS[0]+2, 2, OFFICE_POS[2]+15.1), scale=(0.9, 1.3, 0.25),
    collider='box'
)

secret_wall = office_back_wall
maze_light = None


def take_golden_book():
    if state['has_book']:
        return
    state['has_book'] = True
    destroy(golden_book)
    show_message("לקחת את הספר הזהוב... הקיר נפתח!", duration=3)
    open_secret_wall()


golden_book.on_click = take_golden_book


def open_secret_wall():
    global maze_light
    state['wall_open'] = True
    secret_wall.color = color.rgb(15, 10, 10)
    secret_wall.collider = None
    secret_wall.scale_y = 0.2
    secret_wall.y = 0.1
    maze_light = PointLight(position=(OFFICE_POS[0], 3, OFFICE_POS[2] + 20), color=color.rgba(255, 90, 20, 160))
    invoke(build_maze, delay=0.2)


# ---------------------------------------------------------------------------
# המבוך - לבה ורהיטים צפים
# ---------------------------------------------------------------------------
MAZE_START_Z = OFFICE_POS[2] + 18
maze_respawn_point = Vec3(OFFICE_POS[0], 1, MAZE_START_Z)
platforms = []

trophy = None

def build_maze():
    global trophy
    lava = Entity(
        model='plane', color=color.rgb(200, 60, 10),
        position=(OFFICE_POS[0], -3, MAZE_START_Z + 25), scale=(24, 1, 55),
        texture='white_cube', texture_scale=(10, 20)
    )
    PointLight(position=(OFFICE_POS[0], -1, MAZE_START_Z + 25), color=color.rgba(255, 100, 30, 200))

    # פלטפורמת התחלה קבועה
    Entity(
        model='cube', color=color.rgb(90, 70, 50),
        position=(OFFICE_POS[0], -0.15, MAZE_START_Z), scale=(4, 0.3, 3),
        collider='box'
    )

    furniture_colors = [color.rgb(120, 40, 60), color.rgb(60, 90, 130), color.rgb(110, 100, 40), color.rgb(70, 110, 70)]
    furniture_models = ['cube', 'cube', 'cube', 'cube']

    zigzag_x = [0, 3, -3, 2.5, -2.5, 1.5, -1.5, 0, 2, -2, 0]
    z = MAZE_START_Z + 3
    for i, dx in enumerate(zigzag_x):
        pos = (OFFICE_POS[0] + dx, -0.15, z)
        plat = Entity(
            model='cube',
            color=furniture_colors[i % len(furniture_colors)],
            position=pos, scale=(2.2, 0.5, 2.2),
            collider='box'
        )
        platforms.append(plat)
        z += 3.4

    # פלטפורמת סיום עם גביע
    end_pos = (OFFICE_POS[0], -0.15, z)
    Entity(model='cube', color=color.rgb(90, 70, 50), position=end_pos, scale=(4.5, 0.3, 4), collider='box')
    PointLight(position=(end_pos[0], 3, end_pos[2]), color=color.rgba(255, 230, 150, 220))

    trophy = Clickable(
        model='cube', color=color.gold,
        position=(end_pos[0], 0.7, end_pos[2]), scale=(0.8, 1.1, 0.8),
        collider='box'
    )
    trophy.on_click = win_game

    show_message("קפוץ מרהיט לרהיט מעל הלבה כדי להגיע לגביע!", duration=4)


def win_game():
    if state['game_won']:
        return
    state['game_won'] = True
    show_message("ניצחת!\nמצאת את הגביע וסיימת את הקווסט!", duration=None, scale=2.2, color_=color.gold)


# ---------------------------------------------------------------------------
# לוגיקת קלט גלובלית (קוד כספת) + נפילה ללבה
# ---------------------------------------------------------------------------

def input(key):
    if input_mode['active']:
        if key == 'escape':
            close_code_input()
            return
        if key == 'enter':
            submit_code()
            return
        if key == 'backspace':
            input_mode['typed'] = input_mode['typed'][:-1]
            refresh_code_ui()
            return
        if key in [str(n) for n in range(10)]:
            if len(input_mode['typed']) < 20:
                input_mode['typed'] += key
                refresh_code_ui()
            return
        return  # במצב הקלדה לא מעבירים מקשים אחרים הלאה


def update():
    # נפילה ללבה במבוך -> חזרה לנקודת התחלה
    if state['wall_open'] and not state['game_won']:
        if player.y < -1.5 and player.z > MAZE_START_Z - 1:
            player.position = maze_respawn_point
            show_message("נפלת ללבה! נסה שוב", duration=2)


# ---------------------------------------------------------------------------
# הודעת פתיחה
# ---------------------------------------------------------------------------
show_message("אתה עומד ליד בית רגיל בלילה...\nתמצא את המפתח - המפתח נמצא בתוך תיבת הדואר!", duration=3)

controls_help = Text(
    text="WASD תנועה | עכבר הסתכלות | קליק שמאלי אינטראקציה | רווח קפיצה",
    position=window.top_left + Vec2(0.02, -0.02), scale=0.8, color=color.rgba(255,255,255,160)
)

app.run()