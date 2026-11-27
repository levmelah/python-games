from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math

# אתחול המנוע התלת-ממדי (Ursina)
app = Ursina()

window.title = 'Minecraft - Ursina Edition'
window.fps_counter.enabled = True
window.exit_button.visible = False

# --------------------------------------------------------
# הגדרות עולם וטקסטורות
# --------------------------------------------------------
WORLD_SIZE = 24        # רדיוס העולם (מהמרכז לכל כיוון)
HILL_HEIGHT = 4         # גובה מקסימלי של הגבעות

block_types = ['grass', 'dirt', 'stone', 'sand', 'wood', 'leaves']
block_colors = {
    'grass':  color.rgb(95, 159, 53),
    'dirt':   color.rgb(120, 72, 40),
    'stone':  color.rgb(120, 120, 120),
    'sand':   color.rgb(220, 205, 140),
    'wood':   color.rgb(92, 61, 33),
    'leaves': color.rgb(45, 110, 40),
}

time_of_day = 0.0
selected_block_index = 0


class Voxel(Button):
    """קובייה בודדת בעולם - ניתנת לשבירה והצבה"""
    def __init__(self, position, block_type='grass'):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            color=block_colors[block_type],
            scale=1,
            highlight_color=color.rgba(255, 255, 255, 60),
        )
        self.block_type = block_type


hotbar_slots = []
hotbar_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 140),
                    scale=(0.06 * len(block_types) + 0.02, 0.08), position=(0, -0.45))

for i, block_name in enumerate(block_types):
    slot_x = -0.03 * (len(block_types) - 1) + i * 0.06
    slot = Entity(parent=camera.ui, model='quad', color=block_colors[block_name],
                  scale=0.05, position=(slot_x, -0.45))
    border = Entity(parent=slot, model='quad', color=color.white, scale=1.15, z=0.01, enabled=(i == 0))
    hotbar_slots.append(border)

info_text = Text(
    text='WASD: Move | Space: Jump | LMB: Break | RMB: Place | 1-6: Select Block | Esc: Quit',
    position=(-0.85, 0.47), scale=0.8, color=color.white
)
selected_text = Text(text=f'Block: {block_types[0]}', position=(-0.85, 0.42), scale=1, color=color.yellow)


def select_block(index):
    global selected_block_index
    hotbar_slots[selected_block_index].enabled = False
    selected_block_index = index
    hotbar_slots[selected_block_index].enabled = True
    selected_text.text = f'Block: {block_types[selected_block_index]}'


def get_height(x, z):
    """גובה גבעה פשוט מבוסס גלים - יוצר תוואי שטח לא שטוח"""
    height = math.sin(x * 0.25) * math.cos(z * 0.25) * HILL_HEIGHT
    height += math.sin(x * 0.08 + z * 0.08) * 2
    return int(height)


def create_tree(x, base_y, z):
    trunk_height = random.randint(3, 4)
    for y in range(1, trunk_height + 1):
        Voxel(position=(x, base_y + y, z), block_type='wood')

    for lx in range(-1, 2):
        for lz in range(-1, 2):
            for ly in range(trunk_height, trunk_height + 2):
                if abs(lx) + abs(lz) <= 2:
                    Voxel(position=(x + lx, base_y + ly + 1, z + lz), block_type='leaves')


def build_world():
    for x in range(-WORLD_SIZE, WORLD_SIZE + 1):
        for z in range(-WORLD_SIZE, WORLD_SIZE + 1):
            surface_y = get_height(x, z)

            if surface_y <= -2:
                top_block = 'sand'
            else:
                top_block = 'grass'

            Voxel(position=(x, surface_y, z), block_type=top_block)

            fill_block = 'sand' if top_block == 'sand' else 'dirt'
            for y in range(surface_y - 1, surface_y - 3, -1):
                Voxel(position=(x, y, z), block_type=fill_block)

            for y in range(surface_y - 3, surface_y - 6, -1):
                Voxel(position=(x, y, z), block_type='stone')

            if top_block == 'grass' and abs(x) > 3 and abs(z) > 3 and random.random() < 0.02:
                create_tree(x, surface_y, z)


def update():
    global time_of_day
    time_of_day += time.dt * 0.05

    sky.color = color.rgb(
        max(15, int(135 - math.sin(time_of_day) * 120)),
        max(15, int(206 - math.sin(time_of_day) * 190)),
        max(25, int(250 - math.sin(time_of_day) * 220))
    )


def input(key):
    if key == 'escape':
        application.quit()

    for i in range(1, len(block_types) + 1):
        if key == str(i):
            select_block(i - 1)

    if key == 'left mouse down':
        if isinstance(mouse.hovered_entity, Voxel):
            destroy(mouse.hovered_entity)

    if key == 'right mouse down':
        if isinstance(mouse.hovered_entity, Voxel):
            new_position = mouse.hovered_entity.position + mouse.normal
            Voxel(position=new_position, block_type=block_types[selected_block_index])


build_world()

player = FirstPersonController(position=(0, get_height(0, 0) + 2, 0))
player.cursor.visible = True

sky = Sky()

app.run()
