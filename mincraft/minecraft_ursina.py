from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math
import random


app = Ursina()
window.title = 'Minecraft Python'
window.borderless = False
window.exit_button.visible = False
window.fps_counter.enabled = True
window.color = color.rgb(120, 190, 255)

WORLD_RADIUS = 16
WATER_LEVEL = 2
INTERACT_DISTANCE = 7
TREE_CHANCE = 0.08

BLOCK_TYPES = {
    'grass': {'texture': 'grass', 'color': color.color(0, 0, 1)},
    'dirt': {'texture': 'white_cube', 'color': color.rgb(120, 78, 48)},
    'stone': {'texture': 'white_cube', 'color': color.rgb(130, 130, 130)},
    'sand': {'texture': 'white_cube', 'color': color.rgb(228, 212, 145)},
    'wood': {'texture': 'white_cube', 'color': color.rgb(110, 80, 52)},
    'leaves': {'texture': 'white_cube', 'color': color.rgb(70, 150, 80)},
    'brick': {'texture': 'brick', 'color': color.white},
}

BLOCK_ORDER = ['grass', 'dirt', 'stone', 'sand', 'wood', 'leaves', 'brick']
current_block = BLOCK_ORDER[0]
voxels = {}


def grid_pos(value):
    return int(round(value))


def to_grid_tuple(position):
    return (grid_pos(position.x), grid_pos(position.y), grid_pos(position.z))


def height_at(x, z):
    large_hills = math.sin(x * 0.22) * 1.8 + math.cos(z * 0.18) * 1.7
    small_hills = math.sin((x + z) * 0.35) * 0.8
    return max(1, int(round(large_hills + small_hills + 3)))


def top_block_for_height(height):
    if height <= WATER_LEVEL + 1:
        return 'sand'
    if height >= 6:
        return 'stone'
    return 'grass'


class Voxel(Button):
    def __init__(self, position=(0, 0, 0), block_type='grass'):
        block_data = BLOCK_TYPES[block_type]
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=block_data['texture'],
            color=block_data['color'],
            highlight_color=color.rgba(255, 255, 255, 70),
            scale=1,
            collider='box',
        )
        self.block_type = block_type


def add_block(position, block_type):
    if position in voxels:
        destroy(voxels[position])
    voxels[position] = Voxel(position=position, block_type=block_type)


def remove_block(position):
    voxel = voxels.pop(position, None)
    if voxel:
        destroy(voxel)


def generate_tree(base_x, base_y, base_z):
    trunk_height = random.randint(3, 4)
    for y in range(base_y + 1, base_y + trunk_height + 1):
        add_block((base_x, y, base_z), 'wood')

    leaf_y = base_y + trunk_height
    for lx in range(-2, 3):
        for lz in range(-2, 3):
            for ly in range(0, 3):
                if abs(lx) + abs(lz) < 4:
                    leaf_pos = (base_x + lx, leaf_y + ly, base_z + lz)
                    if leaf_pos not in voxels:
                        add_block(leaf_pos, 'leaves')


def generate_world():
    random.seed(7)
    for x in range(-WORLD_RADIUS, WORLD_RADIUS + 1):
        for z in range(-WORLD_RADIUS, WORLD_RADIUS + 1):
            top_y = height_at(x, z)

            for y in range(0, top_y + 1):
                if y == top_y:
                    block_type = top_block_for_height(top_y)
                elif y >= top_y - 2:
                    block_type = 'dirt'
                else:
                    block_type = 'stone'
                add_block((x, y, z), block_type)

            if top_y < WATER_LEVEL:
                for y in range(top_y + 1, WATER_LEVEL + 1):
                    add_block((x, y, z), 'sand')

            if top_block_for_height(top_y) == 'grass' and abs(x) > 3 and abs(z) > 3:
                if random.random() < TREE_CHANCE:
                    generate_tree(x, top_y, z)


def can_place_block(position):
    if position[1] < 0:
        return False

    inside_player_x = abs(position[0] - player.x) < 1
    inside_player_z = abs(position[2] - player.z) < 1
    inside_player_y = abs(position[1] - (player.y - 1)) < 2
    return not (inside_player_x and inside_player_y and inside_player_z)


def update_selected_block_text():
    selected_text.text = f'Block: {current_block} | 1-7 switch | LMB break | RMB build | Esc quit'


def select_block(index):
    global current_block
    current_block = BLOCK_ORDER[index]
    update_selected_block_text()
    for slot_index, panel in enumerate(hotbar_slots):
        panel.color = color.azure if slot_index == index else color.rgba(0, 0, 0, 140)


def mine_block():
    hit_info = raycast(camera.world_position, camera.forward, distance=INTERACT_DISTANCE, ignore=[player])
    if hit_info.hit and isinstance(hit_info.entity, Voxel):
        remove_block(to_grid_tuple(hit_info.entity.position))


def place_block():
    hit_info = raycast(camera.world_position, camera.forward, distance=INTERACT_DISTANCE, ignore=[player])
    if not hit_info.hit or not isinstance(hit_info.entity, Voxel):
        return

    place_position = to_grid_tuple(hit_info.entity.position + hit_info.normal)
    if place_position in voxels:
        return
    if can_place_block(place_position):
        add_block(place_position, current_block)


def input(key):
    if key in ('escape', 'q'):
        application.quit()
        return

    if key == 'left mouse down':
        mine_block()
        return

    if key == 'right mouse down':
        place_block()
        return

    if key in ('1', '2', '3', '4', '5', '6', '7'):
        select_block(int(key) - 1)


def update():
    if player.y < -20:
        player.position = Vec3(0, height_at(0, 0) + 3, 0)


Sky(color=color.rgb(135, 206, 235))
sun = DirectionalLight(shadows=True)
sun.look_at(Vec3(1, -1, -1))
AmbientLight(color=color.rgba(170, 170, 170, 0.6))

generate_world()

player = FirstPersonController(
    y=height_at(0, 0) + 3,
    origin_y=-0.5,
    speed=5,
    jump_height=1.8,
)
player.cursor.visible = False

crosshair = Text(text='+', origin=(0, 0), scale=2, color=color.white)
selected_text = Text(
    text='',
    parent=camera.ui,
    position=(-0.63, 0.45),
    scale=1.1,
    background=True,
)
help_text = Text(
    text='WASD move | Space jump | Mouse look',
    parent=camera.ui,
    position=(-0.63, 0.4),
    scale=1,
    background=True,
)

hotbar_slots = []
for index, block_name in enumerate(BLOCK_ORDER):
    panel = Entity(
        parent=camera.ui,
        model='quad',
        color=color.rgba(0, 0, 0, 140),
        scale=(0.09, 0.09),
        position=(-0.3 + index * 0.1, -0.44),
    )
    Entity(parent=panel, model='quad', texture=BLOCK_TYPES[block_name]['texture'], color=BLOCK_TYPES[block_name]['color'], scale=0.72)
    Text(parent=panel, text=str(index + 1), position=(-0.035, 0.03), scale=1.4, color=color.white)
    hotbar_slots.append(panel)

select_block(0)

app.run()