from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import AmbientLight
from panda3d.core import CardMaker
from panda3d.core import DirectionalLight
from panda3d.core import LColor
from panda3d.core import TextNode
from panda3d.core import Vec3
import math
import random


class CoinCollector3D(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()
        self.setBackgroundColor(0.53, 0.8, 0.95, 1)

        self.move_speed = 9
        self.turn_speed = 130
        self.camera_height = 1.4
        self.coin_count = 12
        self.score = 0
        self.level = 1
        self.game_finished = False
        self.level_spawn_points = {
            1: Vec3(0, 0, 0.6),
            2: Vec3(0, -18, 0.6),
            3: Vec3(0, -18, 0.6),
        }
        self.keys = {
            'forward': False,
            'back': False,
            'left': False,
            'right': False,
        }
        self.coins = []
        self.world_nodes = []
        self.obstacle_boxes = []
        self.moving_obstacles = []
        self.rotating_hammers = []
        self.monsters = []
        self.lava_zones = []

        self._setup_lights()
        self._build_world()
        self._create_ui()
        self._bind_keys()

        self.taskMgr.add(self.update_game, 'update_game')

    def _setup_lights(self):
        ambient = AmbientLight('ambient')
        ambient.setColor((0.7, 0.7, 0.72, 1))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

        sun = DirectionalLight('sun')
        sun.setColor((0.95, 0.93, 0.88, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(-35, -50, 0)
        self.render.setLight(sun_np)

    def _build_world(self):
        self._clear_world_nodes()

        if self.level == 1:
            ground_maker = CardMaker('ground')
            ground_maker.setFrame(-22, 22, -22, 22)
            ground = self.render.attachNewNode(ground_maker.generate())
            ground.setP(-90)
            ground.setPos(0, 0, 0)
            ground.setColor(LColor(0.22, 0.6, 0.25, 1))
            self.world_nodes.append(ground)
            self._build_level_one_world()
        elif self.level == 2:
            self._build_level_two_world()
        else:
            self._build_level_three_world()

        self.player = self.loader.loadModel('models/box')
        self.player.reparentTo(self.render)
        self.player.setScale(0.7, 1.0, 1.2)
        self.player.setPos(self.level_spawn_points[self.level])
        self.player.setColor(LColor(0.95, 0.35, 0.18, 1))
        self.player.hide()

        self._spawn_coins()
        self._update_camera()

    def _build_level_one_world(self):
        for x_pos, y_pos in [(-10, -8), (-8, 10), (9, -10), (11, 9)]:
            trunk = self.loader.loadModel('models/box')
            trunk.reparentTo(self.render)
            trunk.setScale(1, 1, 3.5)
            trunk.setPos(x_pos, y_pos, 1.75)
            trunk.setColor(LColor(0.5, 0.32, 0.12, 1))
            self.world_nodes.append(trunk)

            leaves = self.loader.loadModel('models/box')
            leaves.reparentTo(self.render)
            leaves.setScale(2.5, 2.5, 2.0)
            leaves.setPos(x_pos, y_pos, 4.8)
            leaves.setColor(LColor(0.18, 0.58, 0.2, 1))
            self.world_nodes.append(leaves)

    def _build_level_two_world(self):
        platform_specs = [
            (0, -18, 12, 7, 0.6, LColor(0.98, 0.82, 0.22, 1)),
            (0, -8, 14, 6, 0.6, LColor(0.93, 0.45, 0.75, 1)),
            (0, 2, 14, 6, 0.6, LColor(0.2, 0.82, 0.88, 1)),
            (0, 12, 14, 6, 0.6, LColor(0.98, 0.58, 0.2, 1)),
            (0, 20, 16, 8, 0.6, LColor(0.45, 0.88, 0.38, 1)),
        ]

        for x_pos, y_pos, scale_x, scale_y, scale_z, color_value in platform_specs:
            platform = self.loader.loadModel('models/box')
            platform.reparentTo(self.render)
            platform.setScale(scale_x, scale_y, scale_z)
            platform.setPos(x_pos, y_pos, scale_z / 2 - 0.3)
            platform.setColor(color_value)
            self.world_nodes.append(platform)

        bumper_specs = [
            (-4.0, -12, 1.1, 1.1, 1.0, LColor(1.0, 0.25, 0.55, 1)),
            (4.0, -9.5, 1.1, 1.1, 1.0, LColor(1.0, 0.25, 0.55, 1)),
            (0, 15, 1.5, 1.5, 1.0, LColor(1.0, 0.25, 0.55, 1)),
        ]

        for x_pos, y_pos, scale_x, scale_y, scale_z, color_value in bumper_specs:
            bumper = self.loader.loadModel('models/box')
            bumper.reparentTo(self.render)
            bumper.setScale(scale_x, scale_y, scale_z)
            bumper.setPos(x_pos, y_pos, scale_z / 2)
            bumper.setColor(color_value)
            self.world_nodes.append(bumper)
            self.obstacle_boxes.append(
                {
                    'node': bumper,
                    'min_x': x_pos - scale_x / 2,
                    'max_x': x_pos + scale_x / 2,
                    'min_y': y_pos - scale_y / 2,
                    'max_y': y_pos + scale_y / 2,
                    'moving': False,
                }
            )

        moving_specs = [
            {'start': Vec3(-3.8, -3, 1.4), 'axis': 'x', 'range': 6, 'speed': 2.2, 'scale': (2.2, 1.0, 2.0), 'color': LColor(0.25, 0.72, 1.0, 1)},
            {'start': Vec3(0, 8, 1.4), 'axis': 'x', 'range': 7, 'speed': 1.8, 'scale': (2.4, 1.0, 2.0), 'color': LColor(0.25, 0.72, 1.0, 1)},
        ]

        for spec in moving_specs:
            obstacle = self.loader.loadModel('models/box')
            obstacle.reparentTo(self.render)
            obstacle.setScale(*spec['scale'])
            obstacle.setPos(spec['start'])
            obstacle.setColor(spec['color'])
            self.world_nodes.append(obstacle)
            self.moving_obstacles.append(
                {
                    'node': obstacle,
                    'start': Vec3(spec['start']),
                    'axis': spec['axis'],
                    'range': spec['range'],
                    'speed': spec['speed'],
                    'scale': spec['scale'],
                }
            )

        hammer_specs = [
            {'pos': Vec3(-4.0, -7.5, 1.5), 'speed': 110, 'length': 3.0, 'angle': 0},
            {'pos': Vec3(4.0, 3.0, 1.5), 'speed': -120, 'length': 3.2, 'angle': 90},
        ]

        for spec in hammer_specs:
            pivot = self.render.attachNewNode('hammer_pivot')
            pivot.setPos(spec['pos'])
            pivot.setH(spec['angle'])
            self.world_nodes.append(pivot)

            arm = self.loader.loadModel('models/box')
            arm.reparentTo(pivot)
            arm.setScale(0.35, spec['length'], 0.35)
            arm.setPos(0, spec['length'] / 2, 0)
            arm.setColor(LColor(0.3, 0.85, 1.0, 1))
            self.world_nodes.append(arm)

            head = self.loader.loadModel('models/box')
            head.reparentTo(pivot)
            head.setScale(1.8, 1.1, 1.5)
            head.setPos(0, spec['length'], 0)
            head.setColor(LColor(1.0, 0.3, 0.6, 1))
            self.world_nodes.append(head)

            self.rotating_hammers.append(
                {
                    'pivot': pivot,
                    'head': head,
                    'speed': spec['speed'],
                }
            )

    def _build_level_three_world(self):
        platform_specs = [
            (0, -18, 10, 5, 0.6, LColor(0.36, 0.36, 0.42, 1)),
            (0, -8, 8, 4, 0.6, LColor(0.42, 0.42, 0.48, 1)),
            (-6, 0, 5, 4, 0.6, LColor(0.45, 0.45, 0.5, 1)),
            (6, 0, 5, 4, 0.6, LColor(0.45, 0.45, 0.5, 1)),
            (0, 8, 8, 4, 0.6, LColor(0.48, 0.48, 0.54, 1)),
            (0, 18, 12, 6, 0.6, LColor(0.55, 0.55, 0.6, 1)),
        ]

        for x_pos, y_pos, scale_x, scale_y, scale_z, color_value in platform_specs:
            platform = self.loader.loadModel('models/box')
            platform.reparentTo(self.render)
            platform.setScale(scale_x, scale_y, scale_z)
            platform.setPos(x_pos, y_pos, scale_z / 2 - 0.3)
            platform.setColor(color_value)
            self.world_nodes.append(platform)

        wall_specs = [
            (-12, 0, 1.5, 40, 4.5),
            (12, 0, 1.5, 40, 4.5),
        ]

        for x_pos, y_pos, scale_x, scale_y, scale_z in wall_specs:
            wall = self.loader.loadModel('models/box')
            wall.reparentTo(self.render)
            wall.setScale(scale_x, scale_y, scale_z)
            wall.setPos(x_pos, y_pos, scale_z / 2)
            wall.setColor(LColor(0.28, 0.28, 0.32, 1))
            self.world_nodes.append(wall)
            self.obstacle_boxes.append(
                {
                    'node': wall,
                    'min_x': x_pos - scale_x / 2,
                    'max_x': x_pos + scale_x / 2,
                    'min_y': y_pos - scale_y / 2,
                    'max_y': y_pos + scale_y / 2,
                    'moving': False,
                }
            )

        lava_specs = [
            (0, -13, 20, 5),
            (0, -1, 20, 5),
            (0, 13, 20, 5),
        ]

        for x_pos, y_pos, scale_x, scale_y in lava_specs:
            lava = self.loader.loadModel('models/box')
            lava.reparentTo(self.render)
            lava.setScale(scale_x, scale_y, 0.25)
            lava.setPos(x_pos, y_pos, -0.2)
            lava.setColor(LColor(1.0, 0.32, 0.08, 1))
            self.world_nodes.append(lava)
            self.lava_zones.append(
                {
                    'min_x': x_pos - scale_x / 2,
                    'max_x': x_pos + scale_x / 2,
                    'min_y': y_pos - scale_y / 2,
                    'max_y': y_pos + scale_y / 2,
                }
            )

        monster_specs = [
            {'start': Vec3(0, -8, 1.0), 'axis': 'x', 'range': 10, 'speed': 2.0, 'scale': (1.4, 1.4, 2.2), 'color': LColor(0.75, 0.85, 0.9, 1)},
            {'start': Vec3(-6, 8, 1.0), 'axis': 'x', 'range': 8, 'speed': 2.5, 'scale': (1.5, 1.5, 2.4), 'color': LColor(0.88, 0.45, 0.4, 1)},
            {'start': Vec3(0, 18, 1.0), 'axis': 'x', 'range': 9, 'speed': 1.7, 'scale': (1.8, 1.8, 2.8), 'color': LColor(0.72, 0.9, 0.42, 1)},
        ]

        for spec in monster_specs:
            monster = self.loader.loadModel('models/box')
            monster.reparentTo(self.render)
            monster.setScale(*spec['scale'])
            monster.setPos(spec['start'])
            monster.setColor(spec['color'])
            self.world_nodes.append(monster)

            eye_left = self.loader.loadModel('models/box')
            eye_left.reparentTo(monster)
            eye_left.setScale(0.12, 0.12, 0.12)
            eye_left.setPos(-0.22, 0.78, 0.4)
            eye_left.setColor(LColor(0.1, 0.05, 0.02, 1))
            self.world_nodes.append(eye_left)

            eye_right = self.loader.loadModel('models/box')
            eye_right.reparentTo(monster)
            eye_right.setScale(0.12, 0.12, 0.12)
            eye_right.setPos(0.22, 0.78, 0.4)
            eye_right.setColor(LColor(0.1, 0.05, 0.02, 1))
            self.world_nodes.append(eye_right)

            self.monsters.append(
                {
                    'node': monster,
                    'start': Vec3(spec['start']),
                    'axis': spec['axis'],
                    'range': spec['range'],
                    'speed': spec['speed'],
                    'scale': spec['scale'],
                }
            )

    def _clear_world_nodes(self):
        for node in self.world_nodes:
            node.removeNode()
        self.world_nodes.clear()
        self.obstacle_boxes.clear()
        self.moving_obstacles.clear()
        self.rotating_hammers.clear()
        self.monsters.clear()
        self.lava_zones.clear()

        if hasattr(self, 'player') and not self.player.isEmpty():
            self.player.removeNode()

    def _create_ui(self):
        self.title_text = OnscreenText(
            text='Panda3D Coin Collector',
            pos=(0, 0.9),
            scale=0.08,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )
        self.score_text = OnscreenText(
            text='',
            pos=(-1.3, 0.88),
            scale=0.06,
            fg=(1, 0.94, 0.25, 1),
            align=TextNode.ALeft,
        )
        self.level_text = OnscreenText(
            text='',
            pos=(-1.3, 0.8),
            scale=0.055,
            fg=(0.9, 1, 1, 1),
            align=TextNode.ALeft,
        )
        self.help_text = OnscreenText(
            text='You are the player | WASD or arrows to move | R restart | Esc quit',
            pos=(0, -0.92),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )
        self.message_text = OnscreenText(
            text='',
            pos=(0, 0.02),
            scale=0.09,
            fg=(0.15, 0.08, 0.02, 1),
            align=TextNode.ACenter,
        )
        self._update_score_text()
        self._update_level_text()

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

        for event_name, (key_name, value) in bindings.items():
            self.accept(event_name, self._set_key, [key_name, value])

        self.accept('r', self.restart_game)
        self.accept('escape', self.userExit)

    def _set_key(self, key_name, value):
        self.keys[key_name] = value

    def _spawn_coins(self):
        for coin_data in self.coins:
            coin_data['node'].removeNode()
        self.coins.clear()

        if self.level == 2:
            self.coin_count = 8
            course_positions = [(-3, -16), (3, -12), (0, -6), (-4, -1), (4, 4), (0, 9), (-3, 14), (0, 21)]
            for x_pos, y_pos in course_positions:
                coin = self.loader.loadModel('models/smiley')
                coin.reparentTo(self.render)
                coin.setScale(0.45)
                coin.setPos(x_pos, y_pos, 1.15)
                coin.setColor(LColor(1.0, 0.9, 0.1, 1))
                self.coins.append({'node': coin, 'spin_offset': random.uniform(0, 360)})
            return

        if self.level == 3:
            self.coin_count = 6
            course_positions = [(0, -18), (0, -8), (-6, 0), (6, 0), (0, 8), (0, 18)]
            for x_pos, y_pos in course_positions:
                coin = self.loader.loadModel('models/smiley')
                coin.reparentTo(self.render)
                coin.setScale(0.48)
                coin.setPos(x_pos, y_pos, 1.1)
                coin.setColor(LColor(1.0, 0.92, 0.1, 1))
                self.coins.append({'node': coin, 'spin_offset': random.uniform(0, 360)})
            return

        self.coin_count = 12

        used_positions = set()
        while len(self.coins) < self.coin_count:
            x_pos = random.randint(-16, 16)
            y_pos = random.randint(-16, 16)
            if (x_pos, y_pos) in used_positions:
                continue
            if abs(x_pos) < 2 and abs(y_pos) < 2:
                continue

            used_positions.add((x_pos, y_pos))
            coin = self.loader.loadModel('models/smiley')
            coin.reparentTo(self.render)
            coin.setScale(0.35)
            coin.setPos(x_pos, y_pos, 0.8)
            coin.setColor(LColor(1.0, 0.85, 0.1, 1))
            self.coins.append({'node': coin, 'spin_offset': random.uniform(0, 360)})

    def _update_score_text(self):
        self.score_text.setText(f'Coins: {self.score}/{self.coin_count}')

    def _update_level_text(self):
        if self.level == 1:
            world_name = 'World 1: Meadow'
        elif self.level == 2:
            world_name = 'World 2: Obstacles'
        else:
            world_name = 'World 3: Lava + Monsters'
        self.level_text.setText(world_name)

    def _update_camera(self):
        player_pos = self.player.getPos()
        forward = self.player.getQuat(self.render).getForward()
        forward.z = 0
        if forward.length_squared() == 0:
            forward = Vec3(0, 1, 0)
        else:
            forward.normalize()

        camera_pos = player_pos + Vec3(0, 0, self.camera_height)
        self.camera.setPos(camera_pos)
        self.camera.lookAt(camera_pos + forward * 10)

    def restart_game(self):
        self.level = 1
        self.score = 0
        self.game_finished = False
        self.message_text.setText('')
        self._build_world()
        self._update_score_text()
        self._update_level_text()

    def _collect_coins(self):
        remaining = []
        player_pos = self.player.getPos()
        for coin_data in self.coins:
            coin = coin_data['node']
            if (coin.getPos() - player_pos).length() < 1.1:
                coin.removeNode()
                self.score += 1
            else:
                remaining.append(coin_data)

        self.coins = remaining
        self._update_score_text()

        if self.score >= self.coin_count and not self.game_finished:
            if self.level == 1:
                self._advance_to_next_world()
            elif self.level == 2:
                self._advance_to_next_world()
            else:
                self.game_finished = True
                self.message_text.setText('You cleared all three worlds!\nPress R to restart')

    def _advance_to_next_world(self):
        self.level += 1
        self.score = 0
        if self.level == 2:
            self.message_text.setText('New world unlocked: obstacles ahead!')
        else:
            self.message_text.setText('World 3 unlocked: lava and monsters!')
        self._build_world()
        self._update_score_text()
        self._update_level_text()

    def _update_player(self, dt):
        turn_direction = int(self.keys['left']) - int(self.keys['right'])
        move_direction = int(self.keys['forward']) - int(self.keys['back'])

        self.player.setH(self.player.getH() + turn_direction * self.turn_speed * dt)
        if move_direction:
            move_vec = Vec3(0, move_direction * self.move_speed * dt, 0)
            self.player.setPos(self.player, move_vec)
            candidate_pos = self.player.getPos(self.render)

            if self._hits_obstacle(candidate_pos.x, candidate_pos.y):
                self._reset_to_level_spawn('Obstacle hit! Back to start')
                return

        if self._hits_lava(self.player.getX(), self.player.getY()):
            self._reset_to_level_spawn('Lava! Back to start')
            return

        if self._hits_monster(self.player.getX(), self.player.getY()):
            self._reset_to_level_spawn('Monster hit! Back to start')
            return

        position = self.player.getPos()
        position.x = max(-20, min(20, position.x))
        position.y = max(-22, min(24, position.y))
        position.z = 0.6
        self.player.setPos(position)

    def _reset_to_level_spawn(self, message):
        self.player.setPos(self.level_spawn_points[self.level])
        self.player.setH(0)
        self.message_text.setText(message)

    def _hits_obstacle(self, x_pos, y_pos):
        padding = 0.7
        for obstacle_box in self.obstacle_boxes:
            if obstacle_box['min_x'] - padding <= x_pos <= obstacle_box['max_x'] + padding and obstacle_box['min_y'] - padding <= y_pos <= obstacle_box['max_y'] + padding:
                return True

        for obstacle in self.moving_obstacles:
            obstacle_pos = obstacle['node'].getPos()
            scale_x, scale_y, _ = obstacle['scale']
            if obstacle_pos.x - scale_x / 2 - padding <= x_pos <= obstacle_pos.x + scale_x / 2 + padding and obstacle_pos.y - scale_y / 2 - padding <= y_pos <= obstacle_pos.y + scale_y / 2 + padding:
                return True

        for hammer in self.rotating_hammers:
            head_pos = hammer['head'].getPos(self.render)
            if (Vec3(x_pos, y_pos, 0.6) - Vec3(head_pos.x, head_pos.y, 0.6)).length() < 1.7:
                return True

        return False

    def _hits_lava(self, x_pos, y_pos):
        for lava_zone in self.lava_zones:
            if lava_zone['min_x'] <= x_pos <= lava_zone['max_x'] and lava_zone['min_y'] <= y_pos <= lava_zone['max_y']:
                return True
        return False

    def _hits_monster(self, x_pos, y_pos):
        for monster in self.monsters:
            monster_pos = monster['node'].getPos()
            scale_x, scale_y, _ = monster['scale']
            if monster_pos.x - scale_x / 2 - 0.6 <= x_pos <= monster_pos.x + scale_x / 2 + 0.6 and monster_pos.y - scale_y / 2 - 0.6 <= y_pos <= monster_pos.y + scale_y / 2 + 0.6:
                return True
        return False

    def _update_moving_obstacles(self, task_time):
        if self.level not in (2, 3):
            return

        for obstacle in self.moving_obstacles:
            offset = math.sin(task_time * obstacle['speed']) * obstacle['range'] * 0.5
            position = Vec3(obstacle['start'])
            if obstacle['axis'] == 'x':
                position.x += offset
            else:
                position.y += offset
            obstacle['node'].setPos(position)

        dt = globalClock.getDt()
        for hammer in self.rotating_hammers:
            hammer['pivot'].setH((hammer['pivot'].getH() + hammer['speed'] * dt) % 360)

        for monster in self.monsters:
            offset = math.sin(task_time * monster['speed']) * monster['range'] * 0.5
            position = Vec3(monster['start'])
            if monster['axis'] == 'x':
                position.x += offset
            else:
                position.y += offset
            monster['node'].setPos(position)

    def update_game(self, task):
        dt = globalClock.getDt()

        self._update_moving_obstacles(task.time)

        if not self.game_finished:
            self._update_player(dt)
            self._collect_coins()

        for index, coin_data in enumerate(self.coins):
            coin = coin_data['node']
            coin.setH((task.time * 180 + coin_data['spin_offset'] + index * 15) % 360)
            coin.setZ(0.8 + 0.12 * math.sin(task.time * 3 + index))

        self._update_camera()
        return task.cont


if __name__ == '__main__':
    game = CoinCollector3D()
    game.run()