from collections import deque
from direct.gui.DirectGui import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import AmbientLight
from panda3d.core import DirectionalLight
from panda3d.core import LColor
from panda3d.core import Point2
from panda3d.core import Point3
from panda3d.core import TextNode
from panda3d.core import Vec3
import math
import random


class ForestScene(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()
        self.setBackgroundColor(0.47, 0.75, 0.98, 1)
        self.world_size = 40
        self.water_level = 2
        self.block_size = 1.0
        self.world_limit = self.world_size * self.block_size + 2
        self.max_build_height = 30
        self.world_random = random.Random(14)
        self.blocks = {}
        self.generation_queue = deque()
        self.world_ready = False
        self.blocks_per_frame = 320
        self.block_palette = {
            '1': ('grass', LColor(0.26, 0.68, 0.25, 1)),
            '2': ('stone', LColor(0.52, 0.52, 0.56, 1)),
            '3': ('brick', LColor(0.7, 0.22, 0.18, 1)),
            '4': ('dirt', LColor(0.47, 0.31, 0.16, 1)),
        }
        self.selected_block_key = '1'
        self.place_block_name, self.place_block_color = self.block_palette[self.selected_block_key]
        self.max_reach = 14
        self.attack_range = 8.5
        self.attack_anim_timer = 0.0
        self.camera_move_speed = 18
        self.camera_turn_speed = 75
        self.max_player_health = 500
        self.player_health = self.max_player_health
        self.game_active = True
        self.time_of_day = 0.0
        self.message_timer = 0.0
        self.wave_number = 0
        self.shadow_wave_number = 0
        self.shadow_world_active = False
        self.portal_open = False
        self.shadow_portal = None
        self.enemies = []
        self.projectiles = []
        self.camera_keys = {
            'forward': False,
            'back': False,
            'left': False,
            'right': False,
            'up': False,
            'down': False,
            'turn_left': False,
            'turn_right': False,
        }

        self._setup_lights()
        self._create_ui()
        self._create_world()
        self._setup_camera()
        self._bind_keys()

        self.taskMgr.add(self.update_scene, 'update_scene')

    def _setup_lights(self):
        ambient = AmbientLight('ambient')
        ambient.setColor((0.6, 0.65, 0.7, 1))
        self.ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(self.ambient_np)

        sun = DirectionalLight('sun')
        sun.setColor((0.98, 0.95, 0.86, 1))
        self.sun_np = self.render.attachNewNode(sun)
        self.sun_np.setHpr(-35, -50, 0)
        self.render.setLight(self.sun_np)

    def _create_world(self):
        terrain_heights = {}
        self.surface_heights = terrain_heights

        for x_pos in range(-self.world_size, self.world_size + 1):
            for y_pos in range(-self.world_size, self.world_size + 1):
                height = self._terrain_height(x_pos, y_pos)
                terrain_heights[(x_pos, y_pos)] = height
                biome_name = self._biome_at(x_pos, y_pos, height)

                for z_pos in range(height + 1):
                    color, block_kind = self._terrain_block_style(biome_name, z_pos, height)
                    self.generation_queue.append((x_pos, y_pos, z_pos, color, block_kind))

                if height < self.water_level:
                    for water_z in range(height + 1, self.water_level + 1):
                        self.generation_queue.append((x_pos, y_pos, water_z, LColor(0.2, 0.5, 0.9, 0.82), 'water'))

        self._create_voxel_trees(terrain_heights)
        self.status_text.setText('Generating world...')
        self.taskMgr.add(self._process_generation_queue, 'generate_world')

    def _terrain_height(self, x_pos, y_pos):
        base_height = 2.8
        base_height += math.sin(x_pos * 0.35) * 1.4
        base_height += math.cos(y_pos * 0.32) * 1.2
        base_height += math.sin((x_pos + y_pos) * 0.18) * 1.1

        ridge_x = x_pos + 9
        ridge_y = y_pos - 11
        ridge_distance = math.sqrt(ridge_x * ridge_x + ridge_y * ridge_y)
        ridge_height = max(0, 6.5 - ridge_distance * 0.55)

        spawn_clear = max(abs(x_pos), abs(y_pos)) <= 2
        height = int(max(1, round(base_height + ridge_height)))
        if spawn_clear:
            return max(2, min(3, height))
        return min(10, height)

    def _biome_at(self, x_pos, y_pos, height):
        if height >= 9 or (x_pos > 14 and y_pos > 6):
            return 'snow'
        if x_pos < -12 and y_pos < 8:
            return 'desert'
        if y_pos > 18 or (x_pos < -6 and y_pos > 14):
            return 'stone'
        return 'grass'

    def _terrain_block_style(self, biome_name, z_pos, height):
        if z_pos == height:
            if height <= self.water_level:
                return LColor(0.78, 0.73, 0.45, 1), 'sand'
            if biome_name == 'snow':
                return LColor(0.92, 0.94, 0.98, 1), 'snow'
            if biome_name == 'desert':
                return LColor(0.84, 0.77, 0.45, 1), 'sand'
            if biome_name == 'stone':
                return LColor(0.52, 0.52, 0.56, 1), 'stone_surface'
            return LColor(0.26, 0.68, 0.25, 1), 'grass_surface'

        if z_pos >= height - 2:
            if biome_name == 'desert':
                return LColor(0.73, 0.56, 0.27, 1), 'sandstone'
            return LColor(0.47, 0.31, 0.16, 1), 'dirt'

        return LColor(0.36, 0.36, 0.39, 1), 'stone'

    def _add_block(self, x_pos, y_pos, z_pos, color, block_kind='placed'):
        block_pos = (x_pos, y_pos, z_pos)
        if block_pos in self.blocks or z_pos < 0:
            return False

        block = self.loader.loadModel('models/box')
        block.reparentTo(self.render)
        block.setScale(self.block_size, self.block_size, self.block_size)
        block.setPos(
            x_pos * self.block_size,
            y_pos * self.block_size,
            z_pos * self.block_size,
        )
        block.setColor(color)
        if color[3] < 1:
            block.setTransparency(True)
        self.blocks[block_pos] = {'node': block, 'kind': block_kind}
        return True

    def _remove_block(self, block_pos):
        block_entry = self.blocks.pop(block_pos, None)
        if block_entry is None:
            return False
        block_entry['node'].removeNode()
        return True

    def _create_voxel_trees(self, terrain_heights):
        tree_positions = []
        for x_pos in range(-self.world_size + 2, self.world_size - 1):
            for y_pos in range(-self.world_size + 2, self.world_size - 1):
                height = terrain_heights[(x_pos, y_pos)]
                biome_name = self._biome_at(x_pos, y_pos, height)
                if height <= self.water_level or height >= 8:
                    continue
                if biome_name != 'grass':
                    continue
                if max(abs(x_pos), abs(y_pos)) <= 4:
                    continue
                if self.world_random.random() < 0.055:
                    tree_positions.append((x_pos, y_pos, height))

        for x_pos, y_pos, ground_height in tree_positions:
            trunk_height = self.world_random.randint(2, 3)
            for offset in range(1, trunk_height + 1):
                self.generation_queue.append((x_pos, y_pos, ground_height + offset, LColor(0.5, 0.34, 0.18, 1), 'wood'))

            leaf_base = ground_height + trunk_height
            for x_offset in range(-1, 2):
                for y_offset in range(-1, 2):
                    self.generation_queue.append(
                        (x_pos + x_offset, y_pos + y_offset, leaf_base + 1, LColor(0.17, 0.58, 0.16, 1), 'leaf')
                    )

            self.generation_queue.append((x_pos, y_pos, leaf_base + 2, LColor(0.17, 0.58, 0.16, 1), 'leaf'))

    def _process_generation_queue(self, task):
        block_count = min(self.blocks_per_frame, len(self.generation_queue))
        for _ in range(block_count):
            x_pos, y_pos, z_pos, color, block_kind = self.generation_queue.popleft()
            self._add_block(x_pos, y_pos, z_pos, color, block_kind)

        if self.generation_queue:
            self.status_text.setText(f'Generating world... {len(self.generation_queue)} blocks left')
            return task.cont

        self.world_ready = True
        self.status_text.setText('World ready')
        self._spawn_enemy_wave()
        self._update_ui()
        return task.done

    def _setup_camera(self):
        self.camera.setPos(0, -16, 9)
        self.camera.setHpr(0, -18, 0)

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
            'd': ('right', True),
            'd-up': ('right', False),
            'q': ('up', True),
            'q-up': ('up', False),
            'e': ('down', True),
            'e-up': ('down', False),
            'arrow_left': ('turn_left', True),
            'arrow_left-up': ('turn_left', False),
            'arrow_right': ('turn_right', True),
            'arrow_right-up': ('turn_right', False),
        }

        for event_name, (key_name, value) in bindings.items():
            self.accept(event_name, self._set_camera_key, [key_name, value])

        self.accept('f', self.break_block)
        self.accept('g', self.place_block)
        self.accept('space', self.attack_enemy)
        self.accept('mouse1', self.attack_enemy)
        self.accept('1', self.select_block, ['1'])
        self.accept('2', self.select_block, ['2'])
        self.accept('3', self.select_block, ['3'])
        self.accept('4', self.select_block, ['4'])

    def _create_ui(self):
        self.help_text = OnscreenText(
            text='F break | G place | Space attack | 1-4 blocks | WASD move | Arrows turn/forward | Q/E up/down',
            pos=(0, -0.93),
            scale=0.045,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )
        self.status_text = OnscreenText(
            text='',
            pos=(-1.3, 0.9),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
        )
        self.health_bg = DirectFrame(
            parent=self.aspect2d,
            frameColor=(0, 0, 0, 0.7),
            frameSize=(0, 0.42, -0.025, 0.025),
            pos=(-1.3, 0, 0.83),
        )
        self.health_fill = DirectFrame(
            parent=self.aspect2d,
            frameColor=(0.9, 0.15, 0.15, 1),
            frameSize=(0, 0.4, -0.018, 0.018),
            pos=(-1.29, 0, 0.83),
        )
        self.health_text = OnscreenText(
            text='',
            pos=(-1.07, 0.77),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
        )
        self.block_text = OnscreenText(
            text='',
            pos=(-1.3, 0.68),
            scale=0.05,
            fg=(0.7, 0.92, 1, 1),
            align=TextNode.ALeft,
        )
        self.wave_text = OnscreenText(
            text='',
            pos=(-1.3, 0.6),
            scale=0.05,
            fg=(1, 0.9, 0.35, 1),
            align=TextNode.ALeft,
        )
        self.enemy_text = OnscreenText(
            text='',
            pos=(-1.3, 0.52),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
        )
        self.portal_text = OnscreenText(
            text='',
            pos=(0, 0.7),
            scale=0.06,
            fg=(0.8, 0.55, 1, 1),
            align=TextNode.ACenter,
        )
        self.message_text = OnscreenText(
            text='',
            pos=(0, 0.78),
            scale=0.06,
            fg=(1, 1, 0.4, 1),
            align=TextNode.ACenter,
        )
        self.crosshair_text = OnscreenText(
            text='+',
            pos=(0, 0),
            scale=0.09,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )
        self.sword_root = self.aspect2d.attachNewNode('sword_root')
        self.sword_root.setPos(1.02, 0, -0.62)
        self.sword_root.setR(28)

        self.sword_blade = DirectFrame(
            parent=self.sword_root,
            frameColor=(0.82, 0.84, 0.9, 1),
            frameSize=(-0.03, 0.03, -0.32, 0.16),
            pos=(0, 0, 0),
        )
        self.sword_guard = DirectFrame(
            parent=self.sword_root,
            frameColor=(0.52, 0.38, 0.12, 1),
            frameSize=(-0.09, 0.09, -0.018, 0.018),
            pos=(0, 0, -0.28),
        )
        self.sword_handle = DirectFrame(
            parent=self.sword_root,
            frameColor=(0.32, 0.2, 0.08, 1),
            frameSize=(-0.02, 0.02, -0.14, 0.02),
            pos=(0, 0, -0.37),
        )
        self._update_ui()

    def _update_ui(self):
        health_ratio = max(0.0, min(1.0, self.player_health / self.max_player_health))
        self.health_fill['frameSize'] = (0, 0.4 * health_ratio, -0.018, 0.018)
        self.health_text.setText(f'Health: {int(self.player_health)}/{self.max_player_health}')
        self.block_text.setText(f'Selected Block: {self.place_block_name}')
        if self.shadow_world_active:
            self.wave_text.setText(f'Shadow Wave {max(1, self.shadow_wave_number)}')
        else:
            self.wave_text.setText(f'Wave {max(1, self.wave_number)}')
        enemy_name = 'Mutants' if self.shadow_world_active else ('Skeletons' if self.wave_number >= 3 else 'Zombies')
        self.enemy_text.setText(f'{enemy_name} Left: {len(self.enemies)}')
        self.portal_text.setText('Portal Open' if self.portal_open and not self.shadow_world_active else '')

    def _show_message(self, text, duration=1.2):
        self.message_text.setText(text)
        self.message_timer = duration

    def _update_message(self, dt):
        if self.message_timer <= 0:
            return
        self.message_timer = max(0, self.message_timer - dt)
        if self.message_timer == 0:
            self.message_text.setText('')

    def _play_attack_animation(self):
        self.attack_anim_timer = 0.16

    def _update_attack_animation(self, dt):
        if self.attack_anim_timer > 0:
            self.attack_anim_timer = max(0, self.attack_anim_timer - dt)
            self.sword_root.setPos(0.9, 0, -0.46)
            self.sword_root.setR(-18)
        else:
            self.sword_root.setPos(1.02, 0, -0.62)
            self.sword_root.setR(28)

    def _set_camera_key(self, key_name, value):
        self.camera_keys[key_name] = value

    def select_block(self, key_name):
        self.selected_block_key = key_name
        self.place_block_name, self.place_block_color = self.block_palette[key_name]
        self._update_ui()

    def _shadow_color_for_kind(self, block_kind):
        if block_kind in ('grass_surface', 'leaf'):
            return LColor(0.16, 0.12, 0.2, 1)
        if block_kind == 'wood':
            return LColor(0.22, 0.15, 0.1, 1)
        if block_kind in ('snow', 'stone_surface', 'stone'):
            return LColor(0.26, 0.24, 0.3, 1)
        if block_kind in ('sand', 'sandstone', 'dirt'):
            return LColor(0.28, 0.14, 0.12, 1)
        if block_kind == 'water':
            return LColor(0.9, 0.32, 0.08, 0.88)
        return LColor(0.32, 0.18, 0.18, 1)

    def _apply_shadow_world_palette(self):
        for block_entry in self.blocks.values():
            node = block_entry['node']
            color = self._shadow_color_for_kind(block_entry['kind'])
            node.setColor(color)
            if color[3] < 1:
                node.setTransparency(True)

    def _spawn_shadow_portal(self):
        if self.shadow_portal is not None or self.shadow_world_active:
            return

        portal = self.render.attachNewNode('shadow_portal')
        portal.setPos(0, 12, self.surface_heights.get((0, 12), self.water_level + 1) + 1.6)

        frame = self.loader.loadModel('models/box')
        frame.reparentTo(portal)
        frame.setScale(1.8, 0.3, 3.2)
        frame.setColor(LColor(0.05, 0.05, 0.08, 1))

        side_left = self.loader.loadModel('models/box')
        side_left.reparentTo(portal)
        side_left.setScale(0.3, 0.3, 3.2)
        side_left.setPos(-1.05, 0, 0)
        side_left.setColor(LColor(0.05, 0.05, 0.08, 1))

        side_right = self.loader.loadModel('models/box')
        side_right.reparentTo(portal)
        side_right.setScale(0.3, 0.3, 3.2)
        side_right.setPos(1.05, 0, 0)
        side_right.setColor(LColor(0.05, 0.05, 0.08, 1))

        top = self.loader.loadModel('models/box')
        top.reparentTo(portal)
        top.setScale(1.8, 0.3, 0.3)
        top.setPos(0, 0, 1.75)
        top.setColor(LColor(0.05, 0.05, 0.08, 1))

        core = self.loader.loadModel('models/box')
        core.reparentTo(portal)
        core.setScale(1.35, 0.12, 2.7)
        core.setPos(0, 0, 0.05)
        core.setColor(LColor(0.7, 0.24, 0.95, 0.78))
        core.setTransparency(True)

        glow = self.loader.loadModel('models/box')
        glow.reparentTo(portal)
        glow.setScale(1.55, 0.04, 2.95)
        glow.setPos(0, -0.12, 0.05)
        glow.setColor(LColor(0.95, 0.55, 1.0, 0.32))
        glow.setTransparency(True)

        self.shadow_portal = {'node': portal, 'core': core, 'glow': glow}
        self.portal_open = True
        self._show_message('Portal Open', duration=2.2)
        self._update_ui()

    def _clear_enemies_and_projectiles(self):
        for enemy in self.enemies:
            enemy['node'].removeNode()
        self.enemies.clear()

        for projectile in self.projectiles:
            projectile['node'].removeNode()
        self.projectiles.clear()

    def _enter_shadow_world(self):
        if self.shadow_world_active:
            return

        self.shadow_world_active = True
        self.shadow_wave_number = 0
        self.portal_open = False
        if self.shadow_portal is not None:
            self.shadow_portal['node'].removeNode()
            self.shadow_portal = None

        self._apply_shadow_world_palette()
        self._clear_enemies_and_projectiles()
        self.camera.setPos(0, -8, 9)
        self._show_message('Entered Shadow World', duration=2.2)
        self._spawn_enemy_wave()
        self._update_ui()

    def damage_player(self, amount):
        if not self.game_active:
            return
        self.player_health = max(0, self.player_health - amount)
        if self.player_health == 0:
            self.game_active = False
            self.status_text.setText('Game Over')
            self._show_message('Game Over', duration=3)
        self._update_ui()

    def heal_player(self, amount):
        if not self.game_active:
            return
        self.player_health = min(self.max_player_health, self.player_health + amount)
        self._update_ui()

    def _world_point_to_block(self, point):
        return (
            int(math.floor(point.x / self.block_size + 0.5)),
            int(math.floor(point.y / self.block_size + 0.5)),
            int(math.floor(point.z / self.block_size + 0.5)),
        )

    def _get_mouse_ray(self):
        if self.mouseWatcherNode.hasMouse():
            mouse_pos = self.mouseWatcherNode.getMouse()
        else:
            mouse_pos = Point2(0, 0)
        near_point = Point3()
        far_point = Point3()
        if not self.camLens.extrude(mouse_pos, near_point, far_point):
            return None, None

        near_world = self.render.getRelativePoint(self.camera, near_point)
        far_world = self.render.getRelativePoint(self.camera, far_point)
        direction = far_world - near_world
        if direction.length_squared() == 0:
            return None, None

        direction.normalize()
        return self.camera.getPos(self.render), direction

    def _pick_enemy(self):
        ray_origin, ray_direction = self._get_mouse_ray()
        if ray_origin is None:
            return None

        best_enemy = None
        best_distance = self.attack_range
        for enemy in self.enemies:
            enemy_pos = enemy['node'].getPos() + Vec3(0, 0, 0.8)
            to_enemy = enemy_pos - ray_origin
            distance_along_ray = to_enemy.dot(ray_direction)
            if distance_along_ray <= 0 or distance_along_ray > best_distance:
                continue

            closest_point = ray_origin + ray_direction * distance_along_ray
            miss_distance = (enemy_pos - closest_point).length()
            if miss_distance > 1.1:
                continue

            best_enemy = enemy
            best_distance = distance_along_ray

        return best_enemy

    def _pick_block(self):
        ray_origin, ray_direction = self._get_mouse_ray()
        if ray_origin is None:
            return None, None

        step_distance = 0.08
        last_empty_block = None
        last_block = None
        max_steps = int(self.max_reach / step_distance)

        for step_index in range(1, max_steps + 1):
            sample_point = ray_origin + ray_direction * (step_index * step_distance)
            block_pos = self._world_point_to_block(sample_point)
            if block_pos == last_block:
                continue

            last_block = block_pos
            if block_pos in self.blocks:
                return block_pos, last_empty_block
            last_empty_block = block_pos

        return None, None

    def break_block(self):
        if not self.world_ready or not self.game_active:
            return
        hit_block, _ = self._pick_block()
        if hit_block is None or hit_block[2] <= 0:
            return
        if self._remove_block(hit_block):
            self.heal_player(5)

    def place_block(self):
        if not self.world_ready or not self.game_active:
            return
        hit_block, adjacent_block = self._pick_block()
        if hit_block is None or adjacent_block is None:
            return
        if adjacent_block[2] < 0 or adjacent_block[2] > self.max_build_height:
            return
        color = self.place_block_color
        if self.shadow_world_active:
            color = self._shadow_color_for_kind(self.place_block_name)
        self._add_block(adjacent_block[0], adjacent_block[1], adjacent_block[2], color, self.place_block_name)

    def _spawn_enemy_wave(self):
        if not self.world_ready or self.enemies or (self.portal_open and not self.shadow_world_active):
            return

        if self.shadow_world_active:
            self.shadow_wave_number += 1
            enemy_kind = 'mutant'
        else:
            self.wave_number += 1
            enemy_kind = 'zombie' if self.wave_number <= 2 else 'skeleton'

        for _ in range(5):
            self._spawn_enemy(enemy_kind)
        if self.shadow_world_active:
            self._show_message(f'Shadow Wave {self.shadow_wave_number}')
        else:
            self._show_message(f'Wave {self.wave_number}')
        self._update_ui()

    def _spawn_enemy(self, enemy_kind):
        while True:
            x_pos = self.world_random.randint(-self.world_size + 3, self.world_size - 3)
            y_pos = self.world_random.randint(-self.world_size + 3, self.world_size - 3)
            if max(abs(x_pos), abs(y_pos)) > 10:
                break

        ground_height = self.surface_heights.get((x_pos, y_pos), self.water_level + 1)
        enemy = self.render.attachNewNode(f'{enemy_kind}_root')
        enemy.setPos(x_pos, y_pos, ground_height + 1.4)

        body = self.loader.loadModel('models/box')
        body.reparentTo(enemy)
        body.setScale(0.8, 0.8, 1.2)
        body.setPos(0, 0, 0)

        head = self.loader.loadModel('models/box')
        head.reparentTo(enemy)
        head.setScale(0.65, 0.65, 0.55)
        head.setPos(0, 0, 1.05)

        if enemy_kind == 'zombie':
            body.setColor(LColor(0.12, 0.55, 0.22, 1))
            head.setColor(LColor(0.18, 0.7, 0.3, 1))
            health = 3
            speed = self.world_random.uniform(2.4, 3.4)
            attack_range = 2.0
            cooldown = 0.7
        elif enemy_kind == 'skeleton':
            body.setColor(LColor(0.78, 0.78, 0.82, 1))
            head.setColor(LColor(0.92, 0.92, 0.95, 1))
            health = 4
            speed = self.world_random.uniform(1.8, 2.5)
            attack_range = 12.0
            cooldown = self.world_random.uniform(1.2, 2.0)
        else:
            body.setColor(LColor(0.16, 0.72, 0.28, 1))
            head.setColor(LColor(0.36, 0.1, 0.42, 1))
            health = 6
            speed = self.world_random.uniform(2.0, 2.8)
            attack_range = 2.3
            cooldown = 0.55

        self.enemies.append(
            {
                'node': enemy,
                'kind': enemy_kind,
                'hp': health,
                'max_hp': health,
                'speed': speed,
                'attack_range': attack_range,
                'attack_timer': 0.0,
                'cooldown': cooldown,
            }
        )

    def attack_enemy(self):
        if not self.game_active or not self.world_ready:
            return

        self._play_attack_animation()
        best_enemy = self._pick_enemy()

        if best_enemy is None:
            return

        if best_enemy['kind'] == 'zombie':
            best_enemy['hp'] = 0
        else:
            best_enemy['hp'] -= 1
        if best_enemy['kind'] == 'zombie':
            best_enemy['node'].setColor(LColor(0.9, 0.25, 0.25, 1))
        else:
            best_enemy['node'].setColor(LColor(1, 0.6, 0.6, 1))

        if best_enemy['hp'] <= 0:
            best_enemy['node'].removeNode()
            self.enemies.remove(best_enemy)
            self.heal_player(15)
            if not self.enemies:
                if not self.shadow_world_active and self.wave_number >= 3 and not self.portal_open:
                    self._spawn_shadow_portal()
                else:
                    self._spawn_enemy_wave()
        self._update_ui()

    def _spawn_projectile(self, start_pos, direction):
        projectile = self.loader.loadModel('models/box')
        projectile.reparentTo(self.render)
        projectile.setScale(0.14, 0.36, 0.14)
        projectile.setPos(start_pos)
        projectile.lookAt(start_pos + direction)
        projectile.setColor(LColor(0.55, 0.33, 0.12, 1))
        self.projectiles.append(
            {
                'node': projectile,
                'direction': Vec3(direction),
                'speed': 18,
                'life': 3.0,
                'damage': 25,
            }
        )

    def _update_enemies(self, dt):
        if not self.game_active:
            return

        player_pos = self.camera.getPos()
        for enemy in list(self.enemies):
            enemy['attack_timer'] += dt
            enemy_node = enemy['node']
            direction = player_pos - enemy_node.getPos()
            direction.z = 0
            distance = direction.length()

            if distance > 0.1:
                move_direction = Vec3(direction)
                move_direction.normalize()
                enemy_node.lookAt(player_pos)
                enemy_node.setP(0)
                enemy_node.setR(0)

                if enemy['kind'] in ('zombie', 'mutant'):
                    enemy_node.setPos(enemy_node.getPos() + move_direction * enemy['speed'] * dt)
                    attack_damage = 18 if enemy['kind'] == 'zombie' else 26
                    hit_distance = 1.9 if enemy['kind'] == 'zombie' else 2.2
                    if distance < hit_distance:
                        self.damage_player(attack_damage * dt)
                else:
                    if distance > 8:
                        enemy_node.setPos(enemy_node.getPos() + move_direction * enemy['speed'] * dt)
                    elif distance < 4:
                        enemy_node.setPos(enemy_node.getPos() - move_direction * enemy['speed'] * dt)

                    if distance < enemy['attack_range'] and enemy['attack_timer'] >= enemy['cooldown']:
                        enemy['attack_timer'] = 0.0
                        shot_direction = player_pos + Vec3(0, 0, 0.5) - (enemy_node.getPos() + Vec3(0, 0, 0.9))
                        if shot_direction.length_squared() > 0:
                            shot_direction.normalize()
                            self._spawn_projectile(enemy_node.getPos() + Vec3(0, 0, 0.9), shot_direction)

    def _update_projectiles(self, dt):
        if not self.game_active:
            return

        player_pos = self.camera.getPos()
        for projectile in list(self.projectiles):
            projectile['life'] -= dt
            if projectile['life'] <= 0:
                projectile['node'].removeNode()
                self.projectiles.remove(projectile)
                continue

            new_pos = projectile['node'].getPos() + projectile['direction'] * projectile['speed'] * dt
            projectile['node'].setPos(new_pos)

            if (new_pos - player_pos).length() < 1.1:
                self.damage_player(projectile['damage'])
                projectile['node'].removeNode()
                self.projectiles.remove(projectile)
                continue

            if self._world_point_to_block(new_pos) in self.blocks:
                projectile['node'].removeNode()
                self.projectiles.remove(projectile)

    def _update_day_night(self, dt):
        if self.shadow_world_active:
            self.setBackgroundColor(0.26, 0.06, 0.34, 1)
            self.ambient_np.node().setColor((0.32, 0.22, 0.4, 1))
            self.sun_np.node().setColor((0.38, 0.16, 0.5, 1))
            return

        self.time_of_day += dt * 0.08
        daylight = 0.5 + 0.5 * math.sin(self.time_of_day)
        sky_r = 0.08 + daylight * 0.39
        sky_g = 0.12 + daylight * 0.63
        sky_b = 0.2 + daylight * 0.78
        self.setBackgroundColor(sky_r, sky_g, sky_b, 1)

        ambient_strength = 0.18 + daylight * 0.52
        self.ambient_np.node().setColor((ambient_strength, ambient_strength, ambient_strength + 0.05, 1))
        sun_strength = 0.2 + daylight * 0.8
        self.sun_np.node().setColor((sun_strength, sun_strength * 0.97, sun_strength * 0.9, 1))

    def _update_portal(self, dt):
        if self.shadow_portal is None:
            return

        portal_node = self.shadow_portal['node']
        portal_node.setH(portal_node.getH() + 25 * dt)
        self.shadow_portal['core'].setR(self.shadow_portal['core'].getR() + 80 * dt)
        self.shadow_portal['glow'].setR(self.shadow_portal['glow'].getR() - 55 * dt)

        if (self.camera.getPos() - portal_node.getPos()).length() < 2.8:
            self._enter_shadow_world()

    def _update_camera(self, dt):
        turn_direction = int(self.camera_keys['turn_left']) - int(self.camera_keys['turn_right'])
        if turn_direction:
            self.camera.setH(self.camera.getH() + turn_direction * self.camera_turn_speed * dt)

        move_direction = Vec3(0, 0, 0)
        forward = self.camera.getQuat(self.render).getForward()
        forward.z = 0
        if forward.length_squared() > 0:
            forward.normalize()

        right = self.camera.getQuat(self.render).getRight()
        right.z = 0
        if right.length_squared() > 0:
            right.normalize()

        if self.camera_keys['forward']:
            move_direction += forward
        if self.camera_keys['back']:
            move_direction -= forward
        if self.camera_keys['left']:
            move_direction -= right
        if self.camera_keys['right']:
            move_direction += right
        if self.camera_keys['up']:
            move_direction.z += 1
        if self.camera_keys['down']:
            move_direction.z -= 1

        if move_direction.length_squared() > 0:
            move_direction.normalize()
            self.camera.setPos(self.camera.getPos() + move_direction * self.camera_move_speed * dt)

        camera_pos = self.camera.getPos()
        camera_pos.x = max(-self.world_limit, min(self.world_limit, camera_pos.x))
        camera_pos.y = max(-self.world_limit, min(self.world_limit, camera_pos.y))
        camera_pos.z = max(2.5, min(self.max_build_height, camera_pos.z))
        self.camera.setPos(camera_pos)

    def update_scene(self, task):
        dt = globalClock.getDt()
        self._update_day_night(dt)
        self._update_camera(dt)
        self._update_attack_animation(dt)
        self._update_portal(dt)
        self._update_enemies(dt)
        self._update_projectiles(dt)
        self._update_message(dt)
        self._update_ui()
        return task.cont


if __name__ == '__main__':
    app = ForestScene()
    app.run()