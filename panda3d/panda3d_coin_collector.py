from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import AmbientLight
from panda3d.core import BitMask32
from panda3d.core import CollisionHandlerQueue
from panda3d.core import CollisionNode
from panda3d.core import CollisionRay
from panda3d.core import CollisionTraverser
from panda3d.core import DirectionalLight
from panda3d.core import LColor
from panda3d.core import PNMImage
from panda3d.core import TextNode
from panda3d.core import Texture
from panda3d.core import Vec3
from panda3d.core import WindowProperties
import json
import math
import os
import random


class SimpleMinecraftGame(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()
        self.setBackgroundColor(0.53, 0.81, 0.95, 1)
        self.world_size = 38
        self.water_level = 1
        self.player_height = 1.7
        self.player_eye_offset = 1.2
        self.block_scale = 0.505
        self.block_half_size = self.block_scale
        self.move_speed = 8
        self.mouse_sensitivity = 0.15
        self.jump_speed = 7.5
        self.gravity = 18
        self.vertical_speed = 0
        self.on_ground = False
        self.pitch = 0
        self.selected_block = 'grass'
        self.blocks = {}
        self.save_file = os.path.join(os.path.dirname(__file__), 'panda3d_minecraft_save.json')
        self.key_map = {
            'forward': False,
            'back': False,
            'left': False,
            'right': False,
        }
        self.block_palette = {
            'grass': LColor(0.32, 0.75, 0.28, 1),
            'dirt': LColor(0.55, 0.36, 0.2, 1),
            'stone': LColor(0.62, 0.64, 0.68, 1),
            'gold': LColor(0.95, 0.8, 0.15, 1),
            'sand': LColor(0.86, 0.79, 0.53, 1),
            'wood': LColor(0.58, 0.4, 0.22, 1),
            'leaves': LColor(0.2, 0.58, 0.18, 1),
            'water': LColor(0.28, 0.5, 0.92, 0.8),
        }
        self.tree_positions = []
        self.block_textures = self._create_block_textures()

        self._setup_window()
        self._setup_lights()
        self._setup_player()
        self._setup_picker()
        self._build_world()
        self._create_ui()
        self._bind_keys()

        self.taskMgr.add(self.update_game, 'update_game')

    def _setup_window(self):
        props = WindowProperties()
        props.setTitle('Simple Panda3D Minecraft')
        props.setCursorHidden(True)
        self.win.requestProperties(props)
        self._recenter_pointer()

    def _recenter_pointer(self):
        self.center_x = self.win.getXSize() // 2
        self.center_y = self.win.getYSize() // 2
        self.win.movePointer(0, self.center_x, self.center_y)

    def _setup_lights(self):
        ambient = AmbientLight('ambient')
        ambient.setColor((0.65, 0.65, 0.7, 1))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

        sun = DirectionalLight('sun')
        sun.setColor((0.95, 0.93, 0.85, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(-45, -55, 0)
        self.render.setLight(sun_np)

    def _setup_player(self):
        self.player = self.render.attachNewNode('player')
        self.player.setPos(0, -4, self.player_height)

        self.camera_pivot = self.player.attachNewNode('camera_pivot')
        self.camera.reparentTo(self.camera_pivot)
        self.camera.setPos(0, 0, 0)
        self.camera.lookAt(0, 1, 0)

    def _create_block_textures(self):
        return {
            'grass': self._make_texture((58, 160, 55), (35, 110, 36), seed=10),
            'dirt': self._make_texture((122, 82, 48), (90, 58, 34), seed=20),
            'stone': self._make_texture((145, 147, 152), (105, 110, 118), seed=30),
            'gold': self._make_texture((232, 194, 46), (176, 140, 22), seed=40),
            'sand': self._make_texture((226, 212, 149), (194, 178, 118), seed=50),
            'wood': self._make_texture((139, 94, 52), (103, 68, 36), seed=60),
            'leaves': self._make_texture((57, 139, 49), (32, 96, 28), seed=70),
            'water': self._make_texture((70, 120, 215), (40, 84, 170), seed=80),
        }

    def _make_texture(self, base_rgb, accent_rgb, seed):
        image = PNMImage(16, 16)
        rng = random.Random(seed)
        for x in range(16):
            for y in range(16):
                mix = 0.18 if (x + y) % 2 == 0 else 0.0
                noise = rng.uniform(-0.08, 0.08)
                red = min(255, max(0, int(base_rgb[0] * (1 - mix) + accent_rgb[0] * mix + noise * 255)))
                green = min(255, max(0, int(base_rgb[1] * (1 - mix) + accent_rgb[1] * mix + noise * 255)))
                blue = min(255, max(0, int(base_rgb[2] * (1 - mix) + accent_rgb[2] * mix + noise * 255)))
                image.setXelA(x, y, red / 255, green / 255, blue / 255, 1)

        texture = Texture()
        texture.load(image)
        texture.setMagfilter(Texture.FTNearest)
        texture.setMinfilter(Texture.FTNearest)
        return texture

    def _setup_picker(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        self.picker_node = CollisionNode('picker')
        self.picker_node.setFromCollideMask(BitMask32.bit(1))
        self.picker_node.setIntoCollideMask(BitMask32.allOff())
        self.picker_ray = CollisionRay()
        self.picker_node.addSolid(self.picker_ray)
        self.picker_np = self.camera.attachNewNode(self.picker_node)
        self.picker.addCollider(self.picker_np, self.pq)

    def _create_ui(self):
        self.title_text = OnscreenText(
            text='Simple Panda3D Minecraft',
            pos=(0, 0.9),
            scale=0.08,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )
        self.block_text = OnscreenText(
            text='Block: Grass',
            pos=(-1.3, 0.88),
            scale=0.06,
            fg=(1, 0.95, 0.35, 1),
            align=TextNode.ALeft,
        )
        self.help_text = OnscreenText(
            text='WASD move | Mouse look | Space jump | Left break | Right place | 1-7 select | F5 save | F9 load',
            pos=(0, -0.92),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )
        self.status_text = OnscreenText(
            text='Ready',
            pos=(-1.3, 0.8),
            scale=0.05,
            fg=(0.85, 0.95, 1, 1),
            align=TextNode.ALeft,
        )
        self.crosshair = OnscreenText(
            text='+',
            pos=(0, -0.02),
            scale=0.08,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )

    def _bind_keys(self):
        bindings = {
            'w': ('forward', True),
            'w-up': ('forward', False),
            'arrow_up': ('forward', True),
            'arrow_up-up': ('forward', False),
            's': ('back', True),
            's-up': ('back', False),
            'arrow_down': ('back', True),
            'arrow_down-up': ('back', False),
            'a': ('left', True),
            'a-up': ('left', False),
            'arrow_left': ('left', True),
            'arrow_left-up': ('left', False),
            'd': ('right', True),
            'd-up': ('right', False),
            'arrow_right': ('right', True),
            'arrow_right-up': ('right', False),
        }

        for event_name, (action, value) in bindings.items():
            self.accept(event_name, self._set_key, [action, value])

        self.accept('mouse1', self.break_block)
        self.accept('mouse3', self.place_block)
        self.accept('space', self.jump)
        self.accept('1', self.select_block, ['grass'])
        self.accept('2', self.select_block, ['dirt'])
        self.accept('3', self.select_block, ['stone'])
        self.accept('4', self.select_block, ['gold'])
        self.accept('5', self.select_block, ['sand'])
        self.accept('6', self.select_block, ['wood'])
        self.accept('7', self.select_block, ['leaves'])
        self.accept('f5', self.save_world)
        self.accept('f9', self.load_world)
        self.accept('escape', self.userExit)

    def _set_key(self, key, value):
        self.key_map[key] = value

    def _build_world(self):
        self.clear_world()
        self.tree_positions = []
        for x in range(-self.world_size, self.world_size + 1):
            for y in range(-self.world_size, self.world_size + 1):
                height = self._height_at(x, y)
                for z in range(-2, height + 1):
                    block_type = self._block_type_for_layer(z, height)
                    self.add_block((x, y, z), block_type)

                if height < self.water_level:
                    for z in range(height + 1, self.water_level + 1):
                        self.add_block((x, y, z), 'water')

                if self._should_spawn_tree(x, y, height):
                    self.tree_positions.append((x, y))
                    self._create_tree(x, y, height)

        self.add_block((6, 6, 5), 'gold')
        self.add_block((6, 6, 6), 'gold')

    def _height_at(self, x, y):
        rolling = math.sin(x * 0.22) * 1.6 + math.cos(y * 0.18) * 1.4
        ridges = math.sin((x + y) * 0.14) * 1.1 + math.cos((x - y) * 0.16) * 0.9
        lake_pull = max(0, 3.8 - math.hypot(x - 2, y + 1) * 0.42)
        height = int(round(rolling + ridges + 2.5 - lake_pull))
        return max(-1, min(6, height))

    def _block_type_for_layer(self, z, column_height):
        if z == column_height:
            if column_height <= self.water_level:
                return 'sand'
            if column_height >= 5:
                return 'stone'
            return 'grass'

        if z >= column_height - 2:
            return 'dirt' if column_height > self.water_level else 'sand'
        return 'stone'

    def _should_spawn_tree(self, x, y, height):
        if height <= self.water_level + 1:
            return False
        if abs(x) < 3 and abs(y) < 3:
            return False
        if height >= 5:
            return False
        if (x * 29 + y * 13) % 41 != 0:
            return False
        if not self._is_flat_tree_spot(x, y, height):
            return False

        for tree_x, tree_y in self.tree_positions:
            if abs(tree_x - x) < 5 and abs(tree_y - y) < 5:
                return False
        return True

    def _is_flat_tree_spot(self, x, y, base_height):
        for offset_x in (-1, 0, 1):
            for offset_y in (-1, 0, 1):
                neighbor_height = self._height_at(x + offset_x, y + offset_y)
                if abs(neighbor_height - base_height) > 1:
                    return False
        return True

    def _create_tree(self, x, y, ground_height):
        trunk_height = 4 + ((x + y) % 2)
        for z in range(ground_height + 1, ground_height + trunk_height + 1):
            self.add_block((x, y, z), 'wood')

        leaf_base = ground_height + trunk_height
        for lx in range(-2, 3):
            for ly in range(-2, 3):
                if abs(lx) == 2 and abs(ly) == 2:
                    continue
                self.add_block((x + lx, y + ly, leaf_base), 'leaves')
                self.add_block((x + lx, y + ly, leaf_base + 1), 'leaves')

        for lx in range(-1, 2):
            for ly in range(-1, 2):
                self.add_block((x + lx, y + ly, leaf_base + 2), 'leaves')

        self.add_block((x, y, leaf_base + 3), 'leaves')

    def clear_world(self):
        for block_data in self.blocks.values():
            block_data['node'].removeNode()
        self.blocks.clear()

    def add_block(self, grid_pos, block_type):
        if grid_pos in self.blocks:
            self.remove_block(grid_pos)

        x, y, z = grid_pos
        block = self.loader.loadModel('models/box')
        block.reparentTo(self.render)
        block.setPos(x, y, z)
        block.setScale(self.block_scale)
        block.setColor(self.block_palette[block_type])
        block.setTexture(self.block_textures[block_type], 1)
        if block_type == 'water':
            block.setTransparency(True)
        block.setTag('grid', f'{x},{y},{z}')
        block.setTag('block', '1')
        block.setCollideMask(BitMask32.bit(1))
        self.blocks[grid_pos] = {'node': block, 'type': block_type}

    def remove_block(self, grid_pos):
        block_data = self.blocks.pop(grid_pos, None)
        if block_data:
            block_data['node'].removeNode()

    def select_block(self, block_type):
        self.selected_block = block_type
        self.block_text.setText(f'Block: {block_type.title()}')
        self.status_text.setText(f'Selected {block_type.title()}')

    def jump(self):
        if self.on_ground:
            self.vertical_speed = self.jump_speed
            self.on_ground = False

    def _get_ground_height(self, x_pos, y_pos):
        highest_top = -1000
        grid_x = round(x_pos)
        grid_y = round(y_pos)
        for offset_x in (-1, 0, 1):
            for offset_y in (-1, 0, 1):
                candidate = (grid_x + offset_x, grid_y + offset_y)
                if abs(candidate[0] - x_pos) > 0.6 or abs(candidate[1] - y_pos) > 0.6:
                    continue
                column = [grid_pos[2] for grid_pos in self.blocks if grid_pos[0] == candidate[0] and grid_pos[1] == candidate[1]]
                if not column:
                    continue
                highest_top = max(highest_top, max(column) + self.block_half_size)
        return highest_top

    def _get_camera_ground_z(self, x_pos, y_pos):
        highest_top = self._get_ground_height(x_pos, y_pos)
        if highest_top < -900:
            return self.player_eye_offset
        return highest_top + self.player_eye_offset

    def _apply_vertical_physics(self, dt):
        self.vertical_speed -= self.gravity * dt
        next_z = self.player.getZ() + self.vertical_speed * dt
        ground_z = self._get_camera_ground_z(self.player.getX(), self.player.getY())

        if next_z <= ground_z:
            self.player.setZ(ground_z)
            self.vertical_speed = 0
            self.on_ground = True
            return

        self.player.setZ(next_z)
        self.on_ground = False

    def _parse_grid_tag(self, node_path):
        tagged_np = node_path.findNetTag('grid')
        if tagged_np.isEmpty():
            return None, None

        raw = tagged_np.getTag('grid')
        x_str, y_str, z_str = raw.split(',')
        return tagged_np, (int(x_str), int(y_str), int(z_str))

    def _pick_block(self):
        self.picker_ray.setFromLens(self.camNode, 0, 0)
        self.picker.traverse(self.render)
        if self.pq.getNumEntries() == 0:
            return None

        self.pq.sortEntries()
        for index in range(self.pq.getNumEntries()):
            entry = self.pq.getEntry(index)
            block_np, grid_pos = self._parse_grid_tag(entry.getIntoNodePath())
            if grid_pos is None:
                continue
            return entry, block_np, grid_pos
        return None

    def break_block(self):
        picked = self._pick_block()
        if not picked:
            return

        _, _, grid_pos = picked
        block_data = self.blocks.get(grid_pos)
        if not block_data:
            return
        if block_data['type'] == 'water':
            return
        if grid_pos[2] <= -2:
            return
        self.selected_block = block_data['type']
        self.block_text.setText(f'Block: {self.selected_block.title()}')
        self.remove_block(grid_pos)

    def place_block(self):
        picked = self._pick_block()
        if not picked:
            return

        entry, _, grid_pos = picked
        normal = entry.getSurfaceNormal(self.render)
        normal = Vec3(round(normal.x), round(normal.y), round(normal.z))
        target_pos = (grid_pos[0] + int(normal.x), grid_pos[1] + int(normal.y), grid_pos[2] + int(normal.z))

        if target_pos in self.blocks or target_pos[2] < 0:
            return

        player_pos = self.player.getPos()
        if abs(target_pos[0] - player_pos.x) < 1 and abs(target_pos[1] - player_pos.y) < 1 and abs(target_pos[2] - player_pos.z) < 2:
            return

        self.add_block(target_pos, self.selected_block)

    def save_world(self):
        save_data = {
            'selected_block': self.selected_block,
            'player': {
                'x': round(self.player.getX(), 3),
                'y': round(self.player.getY(), 3),
                'z': round(self.player.getZ(), 3),
                'heading': round(self.player.getH(), 3),
                'pitch': round(self.pitch, 3),
            },
            'blocks': [
                {'x': x_pos, 'y': y_pos, 'z': z_pos, 'type': block_data['type']}
                for (x_pos, y_pos, z_pos), block_data in sorted(self.blocks.items())
            ],
        }
        with open(self.save_file, 'w', encoding='utf-8') as save_handle:
            json.dump(save_data, save_handle, indent=2)
        self.status_text.setText('World saved')

    def load_world(self):
        if not os.path.exists(self.save_file):
            self.status_text.setText('No save file found')
            return

        with open(self.save_file, 'r', encoding='utf-8') as save_handle:
            save_data = json.load(save_handle)

        self.clear_world()
        for block_data in save_data.get('blocks', []):
            self.add_block((block_data['x'], block_data['y'], block_data['z']), block_data['type'])

        player_data = save_data.get('player', {})
        self.player.setPos(
            player_data.get('x', 0),
            player_data.get('y', -4),
            player_data.get('z', self.player_height),
        )
        self.player.setH(player_data.get('heading', 0))
        self.pitch = player_data.get('pitch', 0)
        self.camera_pivot.setP(self.pitch)
        self.selected_block = save_data.get('selected_block', 'grass')
        self.block_text.setText(f'Block: {self.selected_block.title()}')
        self.vertical_speed = 0
        self.on_ground = False
        self.status_text.setText('World loaded')

    def _update_mouse_look(self):
        if not self.mouseWatcherNode.hasMouse():
            return

        pointer = self.win.getPointer(0)
        delta_x = pointer.getX() - self.center_x
        delta_y = pointer.getY() - self.center_y

        if delta_x or delta_y:
            self.player.setH(self.player.getH() - delta_x * self.mouse_sensitivity)
            self.pitch = max(-75, min(75, self.pitch - delta_y * self.mouse_sensitivity))
            self.camera_pivot.setP(self.pitch)
            self._recenter_pointer()

    def _update_movement(self, dt):
        move = Vec3(0, 0, 0)
        if self.key_map['forward']:
            move.y += 1
        if self.key_map['back']:
            move.y -= 1
        if self.key_map['left']:
            move.x -= 1
        if self.key_map['right']:
            move.x += 1

        if move.length_squared() == 0:
            return

        move.normalize()
        forward = self.player.getQuat(self.render).getForward()
        right = self.player.getQuat(self.render).getRight()
        forward.z = 0
        right.z = 0
        if forward.length_squared() == 0 or right.length_squared() == 0:
            return
        forward.normalize()
        right.normalize()

        next_pos = self.player.getPos() + (forward * move.y + right * move.x) * self.move_speed * dt
        next_pos.x = max(-self.world_size + 1, min(self.world_size - 1, next_pos.x))
        next_pos.y = max(-self.world_size + 1, min(self.world_size - 1, next_pos.y))
        self.player.setPos(next_pos)

    def update_game(self, task):
        dt = globalClock.getDt()
        self._update_mouse_look()
        self._update_movement(dt)
        self._apply_vertical_physics(dt)
        return task.cont


if __name__ == '__main__':
    game = SimpleMinecraftGame()
    game.run()