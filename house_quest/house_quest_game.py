from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import house_quest_world as world

app = Ursina()
window.title = 'House Quest'
window.borderless = False
window.size = (1280, 720)
window.color = color.rgb(18, 22, 30)
window.fps_counter.enabled = True
window.exit_button.visible = False

Text.default_font = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'

world.build_lighting_and_sky()

visible_ground = Entity(model='plane', scale=120, y=-1, color=color.rgb(40, 54, 40), collider='box')

outside_objects = world.build_exterior()
inside_objects = world.build_interior()
maze_objects = world.build_maze()

door = outside_objects['door']
mailbox_body = outside_objects['mailbox_body']
mailbox_flap = outside_objects['mailbox_flap']
key = outside_objects['key']

oven_note = inside_objects['oven_note']
closet = inside_objects['closet']
safe = inside_objects['safe']
mirror_note = inside_objects['mirror_note']
desk_note = inside_objects['desk_note']
golden_book = inside_objects['golden_book']
secret_wall = inside_objects['secret_wall']

maze_trophy = maze_objects['trophy']

player = FirstPersonController(position=world.EXTERIOR_SPAWN, speed=5.5, jump_height=1.6)
player.cursor.visible = False
player.rotation_x = 0
player.rotation_y = 0
camera.position = (0, 2.2, -1.2)
camera.rotation_x = 0
camera.rotation_y = 0
camera.fov = 90

INTERACT_DISTANCE = 4
SAFE_CODE = '1265983809'

PHASE_OUTSIDE = 'outside'
PHASE_INSIDE = 'inside'
PHASE_MAZE = 'maze'
PHASE_WIN = 'win'

phase = PHASE_OUTSIDE
has_key = False
mailbox_opened = False
door_opened = False
closet_opened = False
safe_unlocked = False
book_taken = False
in_code_mode = False
code_buffer = ''

message_text = Text(text='', parent=camera.ui, position=(0, -0.42), origin=(0, 0), scale=1.4, color=color.white, background=True)
message_text.enabled = False

code_text = Text(text='', parent=camera.ui, position=(0, 0.15), origin=(0, 0), scale=1.5, color=color.yellow, background=True)
code_text.enabled = False

help_text = Text(text='WASD movement | Space jump | Left click = interact | Esc = exit', parent=camera.ui, position=(-0.85, -0.48), scale=0.8, color=color.white)


def show_message(text, duration=3):
    message_text.text = text
    message_text.enabled = True
    if duration is not None:
        invoke(lambda: setattr(message_text, 'enabled', False), delay=duration)


def enter_house():
    global phase
    phase = PHASE_INSIDE
    player.position = world.INTERIOR_SPAWN
    show_message('הגעתי לבית. עכשיו ללכת למטבח.', 3)


def open_mailbox():
    global mailbox_opened
    mailbox_opened = True
    mailbox_flap.animate('rotation_x', -110, duration=0.4)
    key.enabled = True
    show_message('תיבת הדואר נפתחה! יש שם מפתח.', 3)


def take_key():
    global has_key
    has_key = True
    key.enabled = False
    show_message('מצאתי את המפתח!', 2)


def try_open_door():
    global door_opened
    if has_key:
        door_opened = True
        door.animate('rotation_y', -100, duration=1)
        show_message('המפתח מתאים. הדלת נפתחת!', 2)
        invoke(enter_house, delay=1.2)
    else:
        show_message('הדלת נעולה. אני צריך מפתח.', 3)


def open_closet():
    global closet_opened
    closet_opened = True
    closet.animate('rotation_y', 100, duration=0.7)
    safe.enabled = True
    show_message('הארון נפתח. יש שם כספת. חפש את הקוד בשירותים.', 4)


def trigger_safe_prompt():
    global in_code_mode, code_buffer
    if not closet_opened:
        show_message('הכספת בפנים בארון בחדר השינה.', 3)
        return
    if safe_unlocked:
        show_message('הכספת כבר פתוחה.', 2)
        return
    in_code_mode = True
    code_buffer = ''
    code_text.enabled = True
    code_text.text = 'קוד לכספת: _'


def submit_code():
    global safe_unlocked, in_code_mode
    if code_buffer == SAFE_CODE:
        safe_unlocked = True
        in_code_mode = False
        code_text.enabled = False
        safe.color = color.rgb(255, 215, 0)
        show_message('הכספת נפתחה! בפנים יש פתק: לך למשרד.', 5)
    else:
        show_message('הקוד שגוי. נסה שוב.', 2)
        code_buffer = ''
        code_text.text = 'קוד לכספת: _'


def cancel_code():
    global in_code_mode, code_buffer
    in_code_mode = False
    code_buffer = ''
    code_text.enabled = False


def take_book():
    global book_taken
    if book_taken:
        return
    book_taken = True
    golden_book.animate('y', golden_book.y + 0.3, duration=0.2)
    secret_wall.animate('rotation_x', -100, duration=1)
    show_message('לקחתי את הספר הזהוב. הקיר נפתח! היכנס למבוך.', 4)
    invoke(enter_maze, delay=1.2)


def enter_maze():
    global phase
    phase = PHASE_MAZE
    player.position = world.MAZE_SPAWN
    player.rotation_y = 0
    show_message('במבוך: קפוץ מרהיט לרהיט כדי להגיע לגביע.', 4)


def restart_game():
    global phase, has_key, mailbox_opened, door_opened, closet_opened, safe_unlocked, book_taken, in_code_mode, code_buffer
    phase = PHASE_OUTSIDE
    has_key = False
    mailbox_opened = False
    door_opened = False
    closet_opened = False
    safe_unlocked = False
    book_taken = False
    in_code_mode = False
    code_buffer = ''
    code_text.enabled = False
    key.enabled = False
    mailbox_flap.rotation_x = 0
    door.rotation_y = 0
    closet.rotation_y = 0
    safe.enabled = False
    safe.color = color.rgb(55, 60, 66)
    golden_book.y = 1.96
    secret_wall.rotation_x = 0
    player.position = world.EXTERIOR_SPAWN
    show_message('אני עומד ליד בית רגיל בלילה. אני חייב למצוא את המפתח.', 3)


def get_hovered_entity():
    hit = raycast(camera.world_position, camera.forward, distance=INTERACT_DISTANCE, ignore=[player])
    if hit.hit:
        return hit.entity
    return None


def handle_click():
    target = get_hovered_entity()
    if target is None:
        return

    if target == mailbox_body and not mailbox_opened:
        open_mailbox()
    elif target == key and not has_key:
        take_key()
    elif target == door and phase == PHASE_OUTSIDE:
        try_open_door()
    elif target == oven_note:
        show_message('פתק על התנור: פתח את הארון בחדר השינה.', 4)
    elif target == closet and phase == PHASE_INSIDE:
        if not closet_opened:
            open_closet()
    elif target == safe:
        trigger_safe_prompt()
    elif target == mirror_note:
        show_message('פתק על המראה:\n1265983809', 4)
    elif target == desk_note:
        show_message('פתק על השולחן: קח את הספר הזהוב מהמדף.', 4)
    elif target == golden_book and phase == PHASE_INSIDE:
        take_book()


def input(key):
    global code_buffer

    if in_code_mode:
        if key == 'escape':
            cancel_code(); return
        if key == 'enter':
            submit_code(); return
        if key == 'backspace':
            code_buffer = code_buffer[:-1]
            code_text.text = f'קוד לכספת: {code_buffer if code_buffer else "_"}'
            return
        if len(key) == 1 and key.isdigit() and len(code_buffer) < 10:
            code_buffer += key
            code_text.text = f'קוד לכספת: {code_buffer}'
        return

    if key == 'left mouse down':
        handle_click(); return

    if key == 'escape':
        application.quit(); return

    if key == 'r' and phase == PHASE_WIN:
        restart_game(); return


def check_maze_win():
    global phase
    if phase != PHASE_MAZE:
        return
    if player.y < world.MAZE_FALL_Y:
        player.position = world.MAZE_SPAWN
        show_message('נפלת לתוך הלבה! חזרתי להתחלה.', 3)
    elif distance(player.position, maze_trophy.world_position) < 1.6:
        phase = PHASE_WIN
        show_message('ניצחת! מצאת את הגביע!', 5)


show_message('אני עומד ליד בית רגיל בלילה. אני צריך למצוא את המפתח.', 3)

app.run()
