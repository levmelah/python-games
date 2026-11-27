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


class DinoArenaGame(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()
        self.setBackgroundColor(0.72, 0.87, 0.96, 1)

        self.base_move_speed = 11
        self.move_speed = self.base_move_speed
        self.turn_speed = 150
        self.attack_range = 2.2
        self.attack_cooldown = 0.45
        self.dash_speed = 28
        self.dash_time = 0.2
        self.dash_cooldown = 1.1
        self.player_hp = 5
        self.score = 0
        self.coins = 0
        self.attack_power = 1
        self.coin_spin = 0
        self.attack_anim_timer = 0
        self.message_timer = 0
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_direction = Vec3(0, 1, 0)
        self.game_over = False
        self.keys = {
            'forward': False,
            'back': False,
            'left': False,
            'right': False,
        }
        self.enemies = []
        self.pickups = []
        self.arena_nodes = []
        self.time_since_attack = 0

        self._setup_lights()
        self._build_arena()
        self._create_player()
        self._spawn_enemy_wave(count=4)
        self._spawn_arena_coins(count=6)
        self._create_ui()
        self._bind_keys()

        self.taskMgr.add(self.update_game, 'update_game')

    def _setup_lights(self):
        ambient = AmbientLight('ambient')
        ambient.setColor((0.75, 0.75, 0.78, 1))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

        sun = DirectionalLight('sun')
        sun.setColor((0.98, 0.95, 0.9, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(-40, -45, 0)
        self.render.setLight(sun_np)

    def _build_arena(self):
        ground_maker = CardMaker('ground')
        ground_maker.setFrame(-22, 22, -22, 22)
        ground = self.render.attachNewNode(ground_maker.generate())
        ground.setP(-90)
        ground.setPos(0, 0, 0)
        ground.setColor(LColor(0.82, 0.72, 0.42, 1))
        self.arena_nodes.append(ground)

        for x_pos, y_pos, size_x, size_y in [(-22, 0, 1.5, 44), (22, 0, 1.5, 44), (0, -22, 44, 1.5), (0, 22, 44, 1.5)]:
            wall = self.loader.loadModel('models/box')
            wall.reparentTo(self.render)
            wall.setScale(size_x, size_y, 4)
            wall.setPos(x_pos, y_pos, 2)
            wall.setColor(LColor(0.54, 0.43, 0.28, 1))
            self.arena_nodes.append(wall)

        for rock_pos in [(-8, -6), (7, -4), (-6, 8), (9, 7)]:
            rock = self.loader.loadModel('models/box')
            rock.reparentTo(self.render)
            rock.setScale(2.5, 2.2, 1.5)
            rock.setPos(rock_pos[0], rock_pos[1], 0.75)
            rock.setColor(LColor(0.58, 0.56, 0.52, 1))
            self.arena_nodes.append(rock)

        shop = self.loader.loadModel('models/box')
        shop.reparentTo(self.render)
        shop.setScale(2.4, 2.4, 2.2)
        shop.setPos(0, 14, 1.1)
        shop.setColor(LColor(0.2, 0.55, 0.95, 1))
        self.shop = shop

        shop_top = self.loader.loadModel('models/box')
        shop_top.reparentTo(shop)
        shop_top.setScale(0.5, 0.5, 0.35)
        shop_top.setPos(0, 0, 0.9)
        shop_top.setColor(LColor(1.0, 0.95, 0.35, 1))

    def _create_player(self):
        self.player = self.render.attachNewNode('player_root')
        self.player.setPos(0, 0, 0.9)
        self.player_visual = self.player.attachNewNode('player_visual')
        self.player_visual.setScale(1.2, 1.7, 1.1)

        self.player_body = self.loader.loadModel('models/box')
        self.player_body.reparentTo(self.player_visual)
        self.player_body.setScale(0.95, 1.0, 0.75)
        self.player_body.setPos(0, -0.05, 0.0)
        self.player_body.setColor(LColor(0.38, 0.82, 0.38, 1))

        self.player_chest = self.loader.loadModel('models/box')
        self.player_chest.reparentTo(self.player_visual)
        self.player_chest.setScale(0.8, 0.6, 0.55)
        self.player_chest.setPos(0, 0.48, 0.18)
        self.player_chest.setColor(LColor(0.5, 0.9, 0.5, 1))

        self.player_head = self.loader.loadModel('models/box')
        self.player_head.reparentTo(self.player_visual)
        self.player_head.setScale(0.95, 0.85, 0.8)
        self.player_head.setPos(0, 1.0, 0.45)
        self.player_head.setColor(LColor(0.42, 0.86, 0.42, 1))

        self.player_snout = self.loader.loadModel('models/box')
        self.player_snout.reparentTo(self.player_head)
        self.player_snout.setScale(0.52, 0.46, 0.28)
        self.player_snout.setPos(0, 0.55, -0.08)
        self.player_snout.setColor(LColor(0.62, 0.95, 0.62, 1))

        self.player_eye_left = self.loader.loadModel('models/box')
        self.player_eye_left.reparentTo(self.player_head)
        self.player_eye_left.setScale(0.12, 0.12, 0.12)
        self.player_eye_left.setPos(-0.2, 0.46, 0.12)
        self.player_eye_left.setColor(LColor(0.05, 0.05, 0.05, 1))

        self.player_eye_right = self.loader.loadModel('models/box')
        self.player_eye_right.reparentTo(self.player_head)
        self.player_eye_right.setScale(0.12, 0.12, 0.12)
        self.player_eye_right.setPos(0.2, 0.46, 0.12)
        self.player_eye_right.setColor(LColor(0.05, 0.05, 0.05, 1))

        self.player_tail = self.loader.loadModel('models/box')
        self.player_tail.reparentTo(self.player_visual)
        self.player_tail.setScale(0.35, 1.5, 0.25)
        self.player_tail.setPos(0, -1.35, -0.15)
        self.player_tail.setP(-20)
        self.player_tail.setColor(LColor(0.3, 0.75, 0.3, 1))

        self.player_spikes = []
        for spike_y, spike_z in [(-0.65, 0.45), (-0.05, 0.65), (0.55, 0.82)]:
            spike = self.loader.loadModel('models/box')
            spike.reparentTo(self.player_visual)
            spike.setScale(0.18, 0.18, 0.3)
            spike.setPos(0, spike_y, spike_z)
            spike.setP(22)
            spike.setColor(LColor(0.2, 0.55, 0.2, 1))
            self.player_spikes.append(spike)

        self.player_legs = []
        for leg_x, leg_y in [(-0.34, 0.35), (0.34, 0.35), (-0.26, -0.45), (0.26, -0.45)]:
            leg = self.loader.loadModel('models/box')
            leg.reparentTo(self.player_visual)
            leg.setScale(0.18, 0.18, 0.5)
            leg.setPos(leg_x, leg_y, -0.62)
            leg.setColor(LColor(0.27, 0.7, 0.27, 1))
            self.player_legs.append(leg)

    def _spawn_arena_coins(self, count):
        for _ in range(count):
            self._spawn_coin_pickup(random.randint(-16, 16), random.randint(-16, 16), value=1)

    def _spawn_coin_pickup(self, x_pos, y_pos, value):
        coin = self.loader.loadModel('models/box')
        coin.reparentTo(self.render)
        coin.setScale(0.35, 0.12, 0.35)
        coin.setPos(x_pos, y_pos, 0.8)
        coin.setColor(LColor(1.0, 0.9, 0.15, 1))
        self.pickups.append({'node': coin, 'base_z': 0.8, 'value': value})

    def _spawn_enemy_wave(self, count):
        for _ in range(count):
            self._spawn_enemy()

    def _spawn_enemy(self):
        enemy = self.render.attachNewNode('enemy_root')
        enemy_visual = enemy.attachNewNode('enemy_visual')
        enemy_visual.setScale(1.1, 1.5, 1.0)

        while True:
            x_pos = random.randint(-16, 16)
            y_pos = random.randint(-16, 16)
            if abs(x_pos) + abs(y_pos) > 8:
                break

        enemy.setPos(x_pos, y_pos, 0.8)
        enemy_body = self.loader.loadModel('models/box')
        enemy_body.reparentTo(enemy_visual)
        enemy_body.setScale(0.9, 0.95, 0.7)
        enemy_body.setPos(0, 0.0, 0.0)
        enemy_body.setColor(LColor(0.88, 0.38, 0.22, 1))

        head = self.loader.loadModel('models/box')
        head.reparentTo(enemy_visual)
        head.setScale(0.8, 0.75, 0.7)
        head.setPos(0, 0.9, 0.35)
        head.setColor(LColor(0.94, 0.45, 0.28, 1))

        jaw = self.loader.loadModel('models/box')
        jaw.reparentTo(head)
        jaw.setScale(0.42, 0.3, 0.14)
        jaw.setPos(0, 0.48, -0.2)
        jaw.setColor(LColor(0.98, 0.72, 0.45, 1))

        mouth = self.loader.loadModel('models/box')
        mouth.reparentTo(head)
        mouth.setScale(0.35, 0.12, 0.08)
        mouth.setPos(0, 0.4, -0.1)
        mouth.setColor(LColor(0.18, 0.08, 0.04, 1))

        enemy_horns = []
        for horn_x in (-0.24, 0.24):
            horn = self.loader.loadModel('models/box')
            horn.reparentTo(head)
            horn.setScale(0.1, 0.1, 0.25)
            horn.setPos(horn_x, -0.05, 0.46)
            horn.setP(-25)
            horn.setColor(LColor(0.95, 0.9, 0.8, 1))
            enemy_horns.append(horn)

        enemy_tail = self.loader.loadModel('models/box')
        enemy_tail.reparentTo(enemy_visual)
        enemy_tail.setScale(0.28, 1.1, 0.2)
        enemy_tail.setPos(0, -1.1, -0.1)
        enemy_tail.setP(-14)
        enemy_tail.setColor(LColor(0.78, 0.32, 0.18, 1))

        enemy_legs = []
        for leg_x, leg_y in [(-0.32, 0.3), (0.32, 0.3), (-0.24, -0.35), (0.24, -0.35)]:
            leg = self.loader.loadModel('models/box')
            leg.reparentTo(enemy_visual)
            leg.setScale(0.15, 0.15, 0.45)
            leg.setPos(leg_x, leg_y, -0.62)
            leg.setColor(LColor(0.76, 0.3, 0.16, 1))
            enemy_legs.append(leg)

        self.enemies.append(
            {
                'node': enemy,
                'visual': enemy_visual,
                'speed': random.uniform(3.6, 5.2),
                'damage_cooldown': random.uniform(0.5, 1.0),
                'attack_timer': 0,
                'hp': 3,
                'flash_timer': 0,
                'body': enemy_body,
                'head': head,
                'tail': enemy_tail,
                'legs': enemy_legs,
            }
        )

    def _create_ui(self):
        self.title_text = OnscreenText(
            text='Dino Arena',
            pos=(0, 0.9),
            scale=0.085,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )
        self.hp_text = OnscreenText(
            text='',
            pos=(-1.3, 0.88),
            scale=0.06,
            fg=(1, 0.35, 0.25, 1),
            align=TextNode.ALeft,
        )
        self.score_text = OnscreenText(
            text='',
            pos=(-1.3, 0.8),
            scale=0.055,
            fg=(1, 0.95, 0.25, 1),
            align=TextNode.ALeft,
        )
        self.coins_text = OnscreenText(
            text='',
            pos=(-1.3, 0.72),
            scale=0.055,
            fg=(1, 0.9, 0.3, 1),
            align=TextNode.ALeft,
        )
        self.upgrade_text = OnscreenText(
            text='',
            pos=(1.28, 0.86),
            scale=0.047,
            fg=(0.95, 0.98, 1, 1),
            align=TextNode.ARight,
        )
        self.help_text = OnscreenText(
            text='WASD move | Shift dash | Space bite | 1 heal | 2 bite+ | 3 speed+ | R restart | Esc quit',
            pos=(0, -0.92),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
        )
        self.message_text = OnscreenText(
            text='',
            pos=(0, 0.02),
            scale=0.085,
            fg=(0.15, 0.08, 0.02, 1),
            align=TextNode.ACenter,
        )
        self._update_ui()

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

        self.accept('space', self.player_attack)
        self.accept('shift', self.try_dash)
        self.accept('1', self.buy_heal)
        self.accept('2', self.buy_bite_upgrade)
        self.accept('3', self.buy_speed_upgrade)
        self.accept('r', self.restart_game)
        self.accept('escape', self.userExit)

    def _set_key(self, key_name, value):
        self.keys[key_name] = value

    def _update_ui(self):
        self.hp_text.setText(f'HP: {self.player_hp}')
        self.score_text.setText(f'Score: {self.score}')
        self.coins_text.setText(f'Coins: {self.coins}')
        self.upgrade_text.setText(
            'Upgrades\n'
            '1 Heal: 4\n'
            '2 Bite+: 6\n'
            '3 Speed+: 5'
        )

    def _update_camera(self):
        player_pos = self.player.getPos()
        backward = self.player.getQuat(self.render).getForward() * -1
        backward.z = 0
        if backward.length_squared() == 0:
            backward = Vec3(0, -1, 0)
        else:
            backward.normalize()

        camera_pos = player_pos + backward * 9 + Vec3(0, 0, 6)
        self.camera.setPos(camera_pos)
        self.camera.lookAt(player_pos + Vec3(0, 0, 1.1))

    def player_attack(self):
        if self.game_over or self.time_since_attack < self.attack_cooldown:
            return

        self.time_since_attack = 0
        self.attack_anim_timer = 0.18
        self.player_head.setColor(LColor(0.9, 1.0, 0.55, 1))
        self.doMethodLater(0.12, self._reset_player_head_color, 'reset_head_color')

        remaining = []
        player_pos = self.player.getPos()
        player_forward = self.player.getQuat(self.render).getForward()
        player_forward.z = 0
        if player_forward.length_squared() > 0:
            player_forward.normalize()

        for enemy in self.enemies:
            enemy_pos = enemy['node'].getPos()
            to_enemy = enemy_pos - player_pos
            to_enemy.z = 0
            close_enough = to_enemy.length() < self.attack_range
            facing_enemy = True
            if to_enemy.length_squared() > 0 and player_forward.length_squared() > 0:
                to_enemy.normalize()
                facing_enemy = player_forward.dot(to_enemy) > 0.1

            if close_enough and facing_enemy:
                enemy['hp'] -= self.attack_power
                enemy['flash_timer'] = 0.16
                enemy['node'].setColor(LColor(1.0, 0.85, 0.25, 1))
                if enemy['hp'] <= 0:
                    drop_count = random.randint(2, 4)
                    for _ in range(drop_count):
                        offset_x = random.uniform(-0.6, 0.6)
                        offset_y = random.uniform(-0.6, 0.6)
                        self._spawn_coin_pickup(enemy_pos.x + offset_x, enemy_pos.y + offset_y, value=1)
                    enemy['node'].removeNode()
                    self.score += 1
                    continue
            remaining.append(enemy)

        if len(remaining) != len(self.enemies):
            self.enemies = remaining
            if len(self.enemies) < 3:
                self._spawn_enemy_wave(2)
        self._update_ui()

    def _reset_player_head_color(self, task):
        if not self.player_head.isEmpty():
            self.player_head.setColor(LColor(0.42, 0.86, 0.42, 1))
        return task.done

    def _show_message(self, text, duration=1.5):
        self.message_text.setText(text)
        self.message_timer = duration

    def try_dash(self):
        if self.game_over or self.dash_timer > 0 or self.dash_cooldown_timer > 0:
            return

        dash_vector = Vec3(0, 0, 0)
        if self.keys['forward']:
            dash_vector.y += 1
        if self.keys['back']:
            dash_vector.y -= 1

        if dash_vector.length_squared() == 0:
            dash_vector = self.player.getQuat(self.render).getForward()

        dash_vector.z = 0
        if dash_vector.length_squared() == 0:
            dash_vector = Vec3(0, 1, 0)
        else:
            dash_vector.normalize()

        self.dash_direction = dash_vector
        self.dash_timer = self.dash_time
        self.dash_cooldown_timer = self.dash_cooldown
        self._show_message('Dash!', duration=0.35)

    def buy_heal(self):
        if self.game_over:
            return
        if self.coins < 4:
            self._show_message('Need 4 coins')
            return
        if self.player_hp >= 8:
            self._show_message('HP already high')
            return
        self.coins -= 4
        self.player_hp += 2
        self._show_message('+2 HP')
        self._update_ui()

    def buy_bite_upgrade(self):
        if self.game_over:
            return
        if self.coins < 6:
            self._show_message('Need 6 coins')
            return
        if self.attack_power >= 3:
            self._show_message('Bite is maxed')
            return
        self.coins -= 6
        self.attack_power += 1
        self._show_message('Bite power up')
        self._update_ui()

    def buy_speed_upgrade(self):
        if self.game_over:
            return
        if self.coins < 5:
            self._show_message('Need 5 coins')
            return
        if self.base_move_speed >= 16:
            self._show_message('Speed is maxed')
            return
        self.coins -= 5
        self.base_move_speed += 1.5
        self.move_speed = self.base_move_speed
        self._show_message('Speed up')
        self._update_ui()

    def _update_pickups(self, dt):
        self.coin_spin += dt * 200
        bob_phase = globalClock.getFrameTime() * 4
        player_pos = self.player.getPos()
        remaining = []
        for index, pickup in enumerate(self.pickups):
            node = pickup['node']
            if node.isEmpty():
                continue

            node.setH((self.coin_spin + index * 25) % 360)
            node.setZ(pickup['base_z'] + math.sin(bob_phase + index) * 0.12)

            if (node.getPos() - player_pos).length() < 1.2:
                self.coins += pickup['value']
                node.removeNode()
                self._update_ui()
                continue
            remaining.append(pickup)
        self.pickups = remaining

        if len(self.pickups) < 4:
            self._spawn_arena_coins(2)

    def _update_attack_animation(self, dt):
        if self.attack_anim_timer > 0:
            self.attack_anim_timer = max(0, self.attack_anim_timer - dt)
            lunge = 0.28 if self.attack_anim_timer > 0.09 else 0.12
            self.player_head.setY(0.75 + lunge)
            self.player_tail.setP(-35)
            self.player_visual.setScale(1.26, 1.8, 1.05)
        else:
            self.player_head.setY(1.0)
            self.player_tail.setP(-20)
            self.player_visual.setScale(1.2, 1.7, 1.1)

    def _update_dash(self, dt):
        self.move_speed = self.base_move_speed
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer = max(0, self.dash_cooldown_timer - dt)

        if self.dash_timer > 0:
            self.dash_timer = max(0, self.dash_timer - dt)
            self.player.setPos(self.player.getPos() + self.dash_direction * self.dash_speed * dt)
            self.player_visual.setScale(1.4, 1.95, 0.9)
            self.player_tail.setP(-45)

    def _update_message(self, dt):
        if self.message_timer <= 0:
            return
        self.message_timer = max(0, self.message_timer - dt)
        if self.message_timer == 0 and not self.game_over:
            self.message_text.setText('')

    def _update_player(self, dt):
        turn_direction = int(self.keys['left']) - int(self.keys['right'])
        move_direction = int(self.keys['forward']) - int(self.keys['back'])

        self.player.setH(self.player.getH() + turn_direction * self.turn_speed * dt)
        if move_direction and self.dash_timer <= 0:
            self.player.setPos(self.player, 0, move_direction * self.move_speed * dt, 0)

        pos = self.player.getPos()
        pos.x = max(-18, min(18, pos.x))
        pos.y = max(-18, min(18, pos.y))
        pos.z = 0.9
        self.player.setPos(pos)

    def _update_enemies(self, dt):
        player_pos = self.player.getPos()
        for enemy in self.enemies:
            enemy_node = enemy['node']
            enemy['attack_timer'] += dt
            if enemy['flash_timer'] > 0:
                enemy['flash_timer'] = max(0, enemy['flash_timer'] - dt)
                if enemy['flash_timer'] == 0:
                    enemy['body'].setColor(LColor(0.88, 0.38, 0.22, 1))
                    enemy['head'].setColor(LColor(0.94, 0.45, 0.28, 1))

            direction = player_pos - enemy_node.getPos()
            direction.z = 0
            if direction.length_squared() > 0:
                direction.normalize()
                enemy_node.setPos(enemy_node.getPos() + direction * enemy['speed'] * dt)
                enemy_node.lookAt(player_pos)
                enemy_node.setP(0)
                enemy_node.setR(0)
                enemy['visual'].setScale(1.1, 1.45 + math.sin(globalClock.getFrameTime() * 8) * 0.08, 1.0)

                stride = math.sin(globalClock.getFrameTime() * 10) * 0.07
                for index, leg in enumerate(enemy['legs']):
                    leg.setZ(-0.62 + (stride if index % 2 == 0 else -stride))
                enemy['tail'].setP(-14 + math.sin(globalClock.getFrameTime() * 9) * 12)

            if (enemy_node.getPos() - player_pos).length() < 1.5 and enemy['attack_timer'] >= enemy['damage_cooldown']:
                enemy['attack_timer'] = 0
                self.player_hp -= 1
                self.camera.setZ(self.camera.getZ() + 0.22)
                self._show_message('Ouch!', duration=0.4)
                self._update_ui()
                if self.player_hp <= 0:
                    self.game_over = True
                    self.message_text.setText('Dino defeated!\nPress R to restart')
                    return

    def restart_game(self):
        for enemy in self.enemies:
            enemy['node'].removeNode()
        self.enemies.clear()

        self.player_hp = 5
        self.score = 0
        self.coins = 0
        self.attack_power = 1
        self.base_move_speed = 11
        self.move_speed = self.base_move_speed
        self.game_over = False
        self.time_since_attack = 0
        self.attack_anim_timer = 0
        self.message_timer = 0
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.player.setPos(0, 0, 0.9)
        self.player.setH(0)
        self.message_text.setText('')
        for pickup in self.pickups:
            pickup['node'].removeNode()
        self.pickups.clear()
        self._spawn_enemy_wave(4)
        self._spawn_arena_coins(6)
        self._update_ui()

    def update_game(self, task):
        dt = globalClock.getDt()
        self.time_since_attack += dt
        self._update_dash(dt)

        if not self.game_over:
            self._update_player(dt)
            self._update_enemies(dt)
            self._update_pickups(dt)

        self._update_attack_animation(dt)
        self._update_message(dt)
        self._update_camera()
        return task.cont


if __name__ == '__main__':
    game = DinoArenaGame()
    game.run()