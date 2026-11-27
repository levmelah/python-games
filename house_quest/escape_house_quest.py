"""משחק חדר בריחה (Quest) בתלת-ממד עם מנוע Ursina.

הסיפור: יוצאים מהבית בלילה, צריך למצוא מפתח בתיבת הדואר כדי להיכנס.
בתוך הבית צריך לעבור בין מטבח -> ארון בחדר שינה -> קוד בשירותים ->
פתיחת כספת -> משרד -> ספר זהוב שחושף מבוך לבה נסתר, ובסופו גביע ניצחון.

שליטה: WASD תנועה, עכבר הסתכלות, רווח קפיצה, לחיצה שמאלית = אינטראקציה.
"""

from ursina import (
    Ursina, Text, window, camera,
    raycast, invoke, curve, color, distance, application,
)
from ursina.prefabs.first_person_controller import FirstPersonController

import quest_world as world


app = Ursina()
window.title = 'בריחה מהבית - חידת לילה'
window.fps_counter.enabled = True
window.exit_button.visible = False

# הפונט הרגיל של Ursina לא כולל אותיות עבריות, אז מחליפים לפונט שתומך בעברית
Text.default_font = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'

world.build_lighting_and_sky()
ext = world.build_exterior()
interior = world.build_interior()
maze = world.build_maze()

door = ext['door']
mailbox_body = ext['mailbox_body']
mailbox_flap = ext['mailbox_flap']
key_entity = ext['key']

oven_note = interior['oven_note']
closet = interior['closet']
safe = interior['safe']
mirror_note = interior['mirror_note']
desk_note = interior['desk_note']
golden_book = interior['golden_book']
secret_wall = interior['secret_wall']
golden_book_start_y = golden_book.y

trophy = maze['trophy']

player = FirstPersonController(position=world.EXTERIOR_SPAWN, origin_y=-0.5, speed=6, jump_height=1.6)
player.cursor.visible = False

INTERACT_DISTANCE = 4
SAFE_CODE = '1265983809'

PHASE_INTRO = 'intro'
PHASE_HOUSE = 'house'
PHASE_MAZE = 'maze'
PHASE_WIN = 'win'

phase = PHASE_INTRO
has_key = False
mailbox_opened = False
door_open = False
closet_opened = False
safe_unlocked = False
book_taken = False
entering_code = False
code_buffer = ''
message_counter = 0


crosshair = Text(text='+', parent=camera.ui, origin=(0, 0), scale=1.6, color=color.white)

message_text = Text(
    text='', parent=camera.ui, position=(0, -0.42), origin=(0, 0),
    scale=1.3, color=color.white, background=True,
)
message_text.enabled = False

key_hud = Text(text='', parent=camera.ui, position=(-0.85, 0.45), scale=1.3, color=color.yellow, background=True)

code_text = Text(
    text='', parent=camera.ui, position=(0, 0), origin=(0, 0),
    scale=1.6, color=color.yellow, background=True,
)
code_text.enabled = False

help_text = Text(
    text='WASD תנועה | רווח קפיצה | לחיצה שמאלית אינטראקציה | Esc יציאה',
    parent=camera.ui, position=(-0.85, -0.47), scale=0.85, color=color.white, background=True,
)


def show_message(text, duration=4):
    global message_counter
    message_counter += 1
    my_id = message_counter
    message_text.text = text
    message_text.enabled = True
    if duration:
        invoke(hide_message, my_id, delay=duration)


def hide_message(my_id):
    if my_id == message_counter:
        message_text.enabled = False


def update_code_display():
    shown = code_buffer if code_buffer else '_'
    code_text.text = f'קוד לכספת: {shown}\n(ספרות, Enter לאישור, Esc לביטול)'


def open_mailbox():
    global mailbox_opened
    mailbox_opened = True
    mailbox_flap.animate('rotation_x', -110, duration=0.4)
    key_entity.enabled = True
    show_message('תיבת הדואר נפתחה! יש שם מפתח, אפשר ללחוץ עליו כדי לקחת אותו.', 4)


def pickup_key():
    global has_key
    has_key = True
    key_entity.enabled = False
    key_hud.text = 'יש לי מפתח!'
    show_message('מצאתי את המפתח!', 3)


def try_open_door():
    global door_open
    if door_open:
        return
    if not has_key:
        show_message('הדלת נעולה... אני צריך למצוא מפתח קודם.', 3)
        return
    door_open = True
    door.animate('rotation_y', -100, duration=1, curve=curve.out_expo)
    show_message('המפתח מתאים! הדלת נפתחת...', 2)
    invoke(enter_house, delay=1.2)


def enter_house():
    global phase
    phase = PHASE_HOUSE
    player.position = world.INTERIOR_SPAWN
    player.rotation_y = 0
    show_message('לך למטבח', 3)


def open_closet():
    global closet_opened
    closet_opened = True
    closet.animate('rotation_y', 100, duration=0.6, curve=curve.out_expo)
    safe.enabled = True
    show_message('בתוך הארון יש כספת! פתק עליה:\n"מצא את הקוד לכספת בשירותים"', 5)


def interact_safe():
    global entering_code, code_buffer
    if not closet_opened:
        show_message('הכספת נעולה בתוך הארון בחדר השינה.', 3)
        return
    if safe_unlocked:
        show_message('הכספת כבר פתוחה.', 2)
        return
    entering_code = True
    code_buffer = ''
    code_text.enabled = True
    update_code_display()


def submit_code():
    global entering_code, safe_unlocked, code_buffer
    if code_buffer == SAFE_CODE:
        safe_unlocked = True
        entering_code = False
        code_text.enabled = False
        safe.color = color.rgb32(255, 215, 0)
        show_message('הכספת נפתחה! בפנים יש פתק:\n"לך למשרד"', 5)
    else:
        show_message('קוד שגוי, נסה שוב.', 2)
    code_buffer = ''
    update_code_display()


def cancel_code():
    global entering_code, code_buffer
    entering_code = False
    code_buffer = ''
    code_text.enabled = False


def take_book():
    global book_taken
    book_taken = True
    golden_book.animate('y', golden_book_start_y + 0.3, duration=0.3)
    secret_wall.animate('rotation_x', -90, duration=1, curve=curve.out_expo)
    show_message('לקחתי את הספר הזהוב...\nקיר נפתח וגילית מבוך נסתר!', 4)
    invoke(enter_maze, delay=1.6)


def enter_maze():
    global phase
    phase = PHASE_MAZE
    player.position = world.MAZE_SPAWN
    player.rotation_y = 0
    show_message('קפוץ מרהיט לרהיט כדי לעבור מעל הלבה, עד שתמצא את הגביע!', 5)


def win_game():
    global phase
    phase = PHASE_WIN
    show_message('ניצחת! מצאת את הגביע! (לחץ R כדי לשחק שוב)', None)


def reset_game():
    global phase, has_key, mailbox_opened, door_open, closet_opened
    global safe_unlocked, book_taken, entering_code, code_buffer

    phase = PHASE_INTRO
    has_key = False
    mailbox_opened = False
    door_open = False
    closet_opened = False
    safe_unlocked = False
    book_taken = False
    entering_code = False
    code_buffer = ''

    key_hud.text = ''
    code_text.enabled = False
    key_entity.enabled = False
    mailbox_flap.rotation_x = 0
    door.rotation_y = 0
    closet.rotation_y = 0
    safe.enabled = False
    safe.color = color.rgb32(60, 60, 65)
    golden_book.y = golden_book_start_y
    secret_wall.rotation_x = 0

    player.position = world.EXTERIOR_SPAWN
    player.rotation_y = 0
    show_message('אני עומד ליד הבית בלילה... אני צריך למצוא מפתח.\nהמפתח בטח נמצא בתיבת הדואר!', 3)


def get_looked_entity():
    hit_info = raycast(camera.world_position, camera.forward, distance=INTERACT_DISTANCE, ignore=[player])
    if hit_info.hit:
        return hit_info.entity
    return None


def handle_click():
    target = get_looked_entity()
    if target is None:
        return

    if target == mailbox_body:
        if not mailbox_opened:
            open_mailbox()
    elif target == key_entity:
        if not has_key:
            pickup_key()
    elif target == door:
        if phase == PHASE_INTRO:
            try_open_door()
    elif target == oven_note:
        show_message('פתק על התנור:\n"תפתח את הארון בחדר השינה"', 5)
    elif target == closet:
        if not closet_opened:
            open_closet()
    elif target == safe:
        interact_safe()
    elif target == mirror_note:
        show_message(f'פתק על המראה:\nהקוד לכספת הוא {SAFE_CODE}', 6)
    elif target == desk_note:
        show_message('פתק על השולחן:\n"קח את הספר הזהוב מהמדף"', 5)
    elif target == golden_book:
        if not book_taken:
            take_book()


def input(key):
    global code_buffer

    if entering_code:
        if key == 'escape':
            cancel_code()
            return
        if key == 'enter':
            submit_code()
            return
        if key == 'backspace':
            code_buffer = code_buffer[:-1]
            update_code_display()
            return
        if len(key) == 1 and key.isdigit():
            if len(code_buffer) < 10:
                code_buffer += key
                update_code_display()
        return

    if key == 'left mouse down':
        handle_click()
        return

    if key == 'escape':
        application.quit()
        return

    if key == 'r' and phase == PHASE_WIN:
        reset_game()


def update():
    if phase == PHASE_MAZE:
        if player.y < world.MAZE_FALL_Y:
            player.position = world.MAZE_SPAWN
            show_message('נפלת ללבה! חוזר להתחלת המבוך.', 3)
        elif distance(player.position, trophy.world_position) < 1.6:
            win_game()


show_message('אני עומד ליד הבית בלילה... אני צריך למצוא מפתח.\nהמפתח בטח נמצא בתיבת הדואר!', 3)

app.run()
