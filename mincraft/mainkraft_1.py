from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math

# אתחול המנוע התלת-ממדי
app = Ursina()

# הגדרת טקסטורות
grass_texture = 'grass'
stone_texture = 'stone'
brick_texture = 'brick'
dirt_texture  = 'dirt'
water_texture = 'white_cube'
current_texture = grass_texture
current_block_color = None

lake_center = Vec2(10, 8)
lake_radius = 6
shadow_world_active = False
shadow_wave_number = 0
shadow_portal = None
world_half_size = 70
safe_spawn_radius = 5
tree_spawn_padding = 5

# משתני מערכת המשחק
max_player_health = 500
player_health = max_player_health
game_active = True
time_of_day = 0  # משתנה למערכת יום ולילה
zombie_waves_completed = 0
enemy_wave_number = 0
bonus_health_awarded = False

# אלמנטים גרפיים של מערכת החיים של השחקן (UI)
health_bar_bg = Entity(parent=camera.ui, model='quad', color=color.black, scale=(0.4, 0.04), position=(-0.6, 0.45))
health_bar = Entity(parent=camera.ui, model='quad', color=color.red, scale=(0.38, 0.03), position=(-0.6, 0.45), origin_x=-0.5)

# מד ספירת זומבים
zombie_count_text = Text(text='Zombies Left: 5', scale=1.5, position=(-0.78, 0.38), color=color.white)
selected_block_text = Text(text='Selected Block: grass', scale=1.2, position=(-0.78, 0.32), color=color.azure)
wave_status_text = Text(text='Wave 1', scale=1.2, position=(-0.78, 0.26), color=color.yellow)
bonus_text = Text(text='+1000 Health', scale=2, origin=(0, 0), color=color.lime, y=0.25, enabled=False)
portal_text = Text(text='Portal Open', scale=1.6, origin=(0, 0), color=color.violet, y=0.18, enabled=False)

# טקסט Game Over
game_over_text = Text(text='GAME OVER', scale=3, origin=(0, 0), color=color.red, enabled=False)

class Voxel(Button):
    """מחלקה שמייצגת קובייה אחת בעולם"""
    def __init__(self, position=(0,0,0), texture=grass_texture, block_color=None):
        # אם לא הוגדר צבע מיוחד, נשתמש בגוון הירוק האקראי של הרצפה
        final_color = block_color if block_color else color.color(0, 0, random.uniform(0.9, 1.0))
        self.block_texture = texture
        self.block_color = block_color
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=texture,
            color=final_color,
            scale=1
        )

    def input(self, key):
        global current_texture, current_block_color
        if not game_active: return
        if self.hovered:
            if key == 'right mouse down':
                Voxel(position=self.position + mouse.normal, texture=current_texture, block_color=current_block_color)
            elif key == 'left mouse down':
                current_texture = self.block_texture
                current_block_color = self.block_color
                selected_block_text.text = f'Selected Block: {current_texture}'
                heal_player(10)
                destroy(self)

class Sword(Entity):
    """מחלקה שמייצגת את החרב של השחקן"""
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='cube',
            color=color.light_gray,
            position=(0.5, -0.4),
            rotation=(30, -40, 10),
            scale=(0.1, 0.6, 0.1)
        )
        self.handle = Entity(parent=self, model='cube', color=color.brown, position=(0, -0.4, 0), scale=(1.5, 0.2, 1.5))
        self.is_attacking = False

    def attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.animate_position((0.3, -0.2), duration=0.1, curve=curve.linear)
            self.animate_rotation((10, -20, -20), duration=0.1, curve=curve.linear)
            invoke(self.reset_sword, delay=0.1)

    def reset_sword(self):
        self.animate_position((0.5, -0.4), duration=0.1)
        self.animate_rotation((30, -40, 10), duration=0.1)
        self.is_attacking = False


def update_health_bar():
    health_ratio = clamp(player_health / max_player_health, 0, 1)
    health_bar.scale_x = health_ratio * 0.38


def damage_player(amount):
    global player_health, game_active
    if not game_active:
        return

    player_health = max(0, player_health - amount)
    update_health_bar()

    if player_health <= 0:
        game_active = False
        game_over_text.enabled = True


def heal_player(amount):
    global player_health
    if not game_active:
        return

    player_health = min(max_player_health, player_health + amount)
    update_health_bar()


def update_enemy_counter():
    if shadow_world_active:
        enemy_name = 'Mutant Zombies'
        wave_status_text.text = f'Shadow Wave {max(shadow_wave_number, 1)}'
    else:
        enemy_name = 'Skeletons' if enemy_wave_number >= 3 else 'Zombies'
        wave_status_text.text = f'Wave {max(enemy_wave_number, 1)}'

    zombie_count_text.text = f'{enemy_name} Left: {len(zombies_list)}'


def show_bonus_text():
    bonus_text.enabled = True
    bonus_text.alpha = 1
    bonus_text.animate_y(0.33, duration=0.6)
    bonus_text.animate('alpha', 0, duration=0.8, delay=0.8)
    invoke(hide_bonus_text, delay=1.7)


def hide_bonus_text():
    bonus_text.enabled = False
    bonus_text.y = 0.25


def grant_post_zombie_bonus():
    global max_player_health, player_health, bonus_health_awarded
    if bonus_health_awarded:
        return

    max_player_health += 1000
    player_health = min(player_health + 1000, max_player_health)
    bonus_health_awarded = True
    update_health_bar()
    show_bonus_text()


def handle_enemy_defeat(enemy):
    global zombie_waves_completed
    if enemy in zombies_list:
        zombies_list.remove(enemy)

    destroy(enemy)

    if len(zombies_list) == 0 and enemy.enemy_kind == 'zombie':
        zombie_waves_completed += 1
        if zombie_waves_completed == 2:
            grant_post_zombie_bonus()

    if len(zombies_list) == 0 and enemy.enemy_kind == 'skeleton' and not shadow_world_active and shadow_portal is None:
        spawn_shadow_portal()

    update_enemy_counter()


def get_enemy_from_entity(entity):
    current = entity
    while current:
        if isinstance(current, (Zombie, Skeleton, MutantZombie)):
            return current
        current = current.parent
    return None


class Portal(Entity):
    """פורטל שמעביר את השחקן לעולם האפל"""
    def __init__(self, position=(0, 1.5, 12)):
        super().__init__(parent=scene, position=position)
        self.frame = Entity(parent=self, model='cube', color=color.black, scale=(1.8, 3.2, 0.3))
        self.core = Entity(parent=self, model='cube', color=color.rgba(160, 40, 220, 180), scale=(1.2, 2.6, 0.08), z=-0.02)
        self.glow = Entity(parent=self, model='cube', color=color.rgba(210, 120, 255, 90), scale=(1.4, 2.8, 0.02), z=-0.06)

    def update(self):
        self.rotation_y += 30 * time.dt
        self.core.rotation_z += 90 * time.dt
        self.glow.rotation_z -= 70 * time.dt


class Arrow(Entity):
    """חץ שנורה על ידי שלד לעבר השחקן"""
    def __init__(self, position, direction):
        super().__init__(
            parent=scene,
            model='cube',
            color=color.brown,
            position=position,
            scale=(0.08, 0.08, 0.5),
            collider='box'
        )
        self.direction = direction.normalized()
        self.speed = 18
        self.damage = 25
        self.life_time = 3
        self.look_at(self.position + self.direction)

    def update(self):
        if not game_active:
            destroy(self)
            return

        self.position += self.direction * self.speed * time.dt
        self.life_time -= time.dt

        if self.life_time <= 0 or self.y < -10:
            destroy(self)
            return

        if distance(self.position, player.position + Vec3(0, 1, 0)) < 1.2:
            damage_player(self.damage)
            destroy(self)
            return

        hit_info = raycast(self.position, self.direction, distance=0.4, ignore=[self])
        if hit_info.hit and isinstance(hit_info.entity, Voxel):
            destroy(self)

class Zombie(Entity):
    """מחלקה שמייצגת זומבי בעל 3 חיים ופרצוף"""
    def __init__(self, position=(30, 1, 30)):
        super().__init__(
            model='cube',
            color=color.green,
            position=position,
            scale=(1.2, 2, 1.2),
            collider='box'
        )
        self.enemy_kind = 'zombie'
        self.health = 3
        self.max_health = 3
        
        # ראש ופרצוף
        self.head = Entity(parent=self, model='cube', color=color.green, position=(0, 0.6, 0), scale=(0.8, 0.4, 0.8))
        self.left_eye = Entity(parent=self.head, model='cube', color=color.red, position=(-0.25, 0.1, 0.51), scale=(0.15, 0.1, 0.05))
        self.right_eye = Entity(parent=self.head, model='cube', color=color.red, position=(0.25, 0.1, 0.51), scale=(0.15, 0.1, 0.05))
        self.mouth = Entity(parent=self.head, model='cube', color=color.black, position=(0, -0.15, 0.51), scale=(0.4, 0.1, 0.05))
        
        # מד חיים מעל ראש הזומבי
        self.z_health_bg = Entity(parent=self, model='quad', color=color.black, position=(0, 1.2, 0), scale=(0.8, 0.1))
        self.z_health_bar = Entity(parent=self, model='quad', color=color.red, position=(-0.4, 1.2, -0.01), scale=(0.8, 0.08), origin_x=-0.5)
        
        self.speed = random.uniform(2.5, 3.8)

    def take_damage(self):
        self.health -= 1
        self.color = color.red
        invoke(self.reset_color, delay=0.15)
        self.z_health_bar.scale_x = (self.health / self.max_health) * 0.8
        
        if self.health <= 0:
            handle_enemy_defeat(self)

    def reset_color(self):
        if self: self.color = color.green

    def update(self):
        if not game_active: return

        direction = (player.position - self.position)
        direction.y = 0
        
        if direction.length() > 0.1:
            direction = direction.normalized()
            self.position += direction * self.speed * time.dt
            self.look_at(player.position)
            self.rotation_x = 0 
            
            self.z_health_bg.look_at(player.position)
            self.z_health_bar.look_at(player.position)

        distance_to_player = distance_xz(self.position, player.position)
        if distance_to_player < 1.8:
            damage_player(10 * time.dt)


class Skeleton(Entity):
    """מחלקה שמייצגת שלד שיורה חצים על השחקן"""
    def __init__(self, position=(30, 1, 30)):
        super().__init__(
            model='cube',
            color=color.light_gray,
            position=position,
            scale=(1.0, 2, 1.0),
            collider='box'
        )
        self.enemy_kind = 'skeleton'
        self.health = 4
        self.max_health = 4
        self.speed = random.uniform(1.8, 2.6)
        self.shoot_cooldown = random.uniform(0.8, 1.6)

        self.head = Entity(parent=self, model='cube', color=color.white, position=(0, 0.7, 0), scale=(0.75, 0.5, 0.75))
        self.left_eye = Entity(parent=self.head, model='cube', color=color.black, position=(-0.18, 0.08, 0.4), scale=(0.1, 0.08, 0.04))
        self.right_eye = Entity(parent=self.head, model='cube', color=color.black, position=(0.18, 0.08, 0.4), scale=(0.1, 0.08, 0.04))
        self.mouth = Entity(parent=self.head, model='cube', color=color.black, position=(0, -0.12, 0.4), scale=(0.28, 0.06, 0.04))
        self.bow = Entity(parent=self, model='cube', color=color.brown, position=(0.55, 0.1, 0), scale=(0.12, 1.0, 0.12), rotation_z=25)

        self.z_health_bg = Entity(parent=self, model='quad', color=color.black, position=(0, 1.2, 0), scale=(0.8, 0.1))
        self.z_health_bar = Entity(parent=self, model='quad', color=color.orange, position=(-0.4, 1.2, -0.01), scale=(0.8, 0.08), origin_x=-0.5)

    def take_damage(self):
        self.health -= 1
        self.color = color.rgb(255, 210, 210)
        invoke(self.reset_color, delay=0.15)
        self.z_health_bar.scale_x = (self.health / self.max_health) * 0.8

        if self.health <= 0:
            handle_enemy_defeat(self)

    def reset_color(self):
        if self:
            self.color = color.light_gray

    def shoot_arrow(self):
        arrow_start = self.position + Vec3(0, 0.9, 0) + self.forward * 0.8
        target = player.position + Vec3(0, 1, 0)
        Arrow(position=arrow_start, direction=target - arrow_start)

    def update(self):
        if not game_active:
            return

        direction = player.position - self.position
        direction.y = 0

        if direction.length() > 0.1:
            move_direction = direction.normalized()
            self.look_at(player.position)
            self.rotation_x = 0
            self.z_health_bg.look_at(player.position)
            self.z_health_bar.look_at(player.position)

            distance_to_player = distance_xz(self.position, player.position)
            if distance_to_player > 8:
                self.position += move_direction * self.speed * time.dt
            elif distance_to_player < 4:
                self.position -= move_direction * self.speed * time.dt

            self.shoot_cooldown -= time.dt
            if distance_to_player < 18 and self.shoot_cooldown <= 0:
                self.shoot_arrow()
                self.shoot_cooldown = random.uniform(1.2, 2.0)


class MutantZombie(Entity):
    """זומבי מחוזק של העולם האפל"""
    def __init__(self, position=(30, 1, 30)):
        super().__init__(
            model='cube',
            color=color.green,
            position=position,
            scale=(1.4, 2.4, 1.4),
            collider='box'
        )
        self.enemy_kind = 'mutant_zombie'
        self.health = 6
        self.max_health = 6
        self.speed = random.uniform(1.8, 2.5)

        self.head = Entity(parent=self, model='cube', color=color.rgb(76, 132, 68), position=(0, 0.82, 0), scale=(0.9, 0.62, 0.9))
        self.left_eye = Entity(parent=self.head, model='cube', color=color.rgb(40, 40, 40), position=(-0.2, 0.07, 0.46), scale=(0.12, 0.08, 0.04))
        self.right_eye = Entity(parent=self.head, model='cube', color=color.rgb(40, 40, 40), position=(0.2, 0.07, 0.46), scale=(0.12, 0.08, 0.04))
        self.mouth = Entity(parent=self.head, model='cube', color=color.rgb(60, 70, 40), position=(0, -0.12, 0.46), scale=(0.25, 0.08, 0.04))

        self.body = Entity(parent=self, model='cube', color=color.rgb(24, 135, 150), position=(0, 0.15, 0), scale=(1.1, 0.9, 0.6))
        self.body_patch_1 = Entity(parent=self.body, model='cube', color=color.rgb(32, 110, 100), position=(-0.25, 0.18, 0.31), scale=(0.18, 0.1, 0.04))
        self.body_patch_2 = Entity(parent=self.body, model='cube', color=color.rgb(55, 170, 160), position=(0.22, -0.12, 0.31), scale=(0.15, 0.12, 0.04))
        self.left_arm = Entity(parent=self, model='cube', color=color.rgb(86, 140, 72), position=(-0.55, -0.02, 0), scale=(0.26, 1.28, 0.26), rotation_z=8)
        self.right_arm = Entity(parent=self, model='cube', color=color.rgb(86, 140, 72), position=(0.55, -0.02, 0), scale=(0.26, 1.28, 0.26), rotation_z=-8)
        self.left_leg = Entity(parent=self, model='cube', color=color.rgb(92, 78, 150), position=(-0.18, -1.02, 0), scale=(0.28, 1.08, 0.28))
        self.right_leg = Entity(parent=self, model='cube', color=color.rgb(92, 78, 150), position=(0.18, -1.02, 0), scale=(0.28, 1.08, 0.28))

        self.z_health_bg = Entity(parent=self, model='quad', color=color.black, position=(0, 1.5, 0), scale=(0.95, 0.12))
        self.z_health_bar = Entity(parent=self, model='quad', color=color.lime, position=(-0.47, 1.5, -0.01), scale=(0.95, 0.09), origin_x=-0.5)

    def take_damage(self):
        self.health -= 1
        self.color = color.rgb(170, 255, 170)
        invoke(self.reset_color, delay=0.15)
        self.z_health_bar.scale_x = (self.health / self.max_health) * 0.95

        if self.health <= 0:
            handle_enemy_defeat(self)

    def reset_color(self):
        if self:
            self.color = color.green

    def update(self):
        if not game_active:
            return

        direction = player.position - self.position
        direction.y = 0

        if direction.length() > 0.1:
            direction = direction.normalized()
            self.position += direction * self.speed * time.dt
            self.look_at(player.position)
            self.rotation_x = 0
            self.z_health_bg.look_at(player.position)
            self.z_health_bar.look_at(player.position)

        if distance_xz(self.position, player.position) < 2.2:
            damage_player(16 * time.dt)

def create_tree(x, z):
    """🟩 פונקציה מעודכנת: גזע העץ חום, העלים בצבע הרצפה"""
    trunk_height = random.randint(3, 5)
    trunk_texture = grass_texture
    trunk_color = color.brown
    leaves_texture = grass_texture
    leaves_color = None

    if shadow_world_active:
        trunk_texture = water_texture
        trunk_color = color.rgb(18, 18, 18)
        leaves_texture = water_texture
        leaves_color = color.rgb(32, 32, 32)
    
    # גזע עץ בצבע חום קבוע
    for y in range(1, trunk_height + 1):
        Voxel(position=(x, y, z), texture=trunk_texture, block_color=trunk_color)
    
    # עלים בצבע ירוק דינמי (כמו הרצפה)
    for lx in range(-1, 2):
        for lz in range(-1, 2):
            for ly in range(trunk_height + 1, trunk_height + 3):
                Voxel(position=(x + lx, ly, z + lz), texture=leaves_texture, block_color=leaves_color)


def is_inside_lake(x, z):
    return math.hypot(x - lake_center.x, z - lake_center.y) <= lake_radius


def create_lake_tile(x, z):
    lake_distance = math.hypot(x - lake_center.x, z - lake_center.y)
    edge_blend = lake_distance / lake_radius

    if lake_distance < lake_radius * 0.55:
        bottom_y = -3
    elif lake_distance < lake_radius * 0.82:
        bottom_y = -2
    else:
        bottom_y = -1

    for y in range(bottom_y, 0):
        floor_color = color.rgb(126, 84, 44) if not shadow_world_active else color.rgb(36, 18, 18)
        Voxel(position=(x, y, z), texture=water_texture, block_color=floor_color)

    if shadow_world_active:
        lake_color = color.rgb(255, 88, 18)
    else:
        lake_color = color.rgba(60, 140, 220, int(150 + (1 - edge_blend) * 60))

    Voxel(position=(x, 0, z), texture=water_texture, block_color=lake_color)


def build_world():
    for entity in list(scene.entities):
        if isinstance(entity, Voxel):
            destroy(entity) 

    for z in range(-world_half_size, world_half_size):
        for x in range(-world_half_size, world_half_size):
            if is_inside_lake(x, z):
                create_lake_tile(x, z)
            else:
                if shadow_world_active:
                    Voxel(position=(x, 0, z), texture=water_texture, block_color=color.rgb(18, 18, 18))
                else:
                    Voxel(position=(x, 0, z), texture=grass_texture)

    for _ in range(15):
        tx = random.randint(-(world_half_size - tree_spawn_padding), world_half_size - tree_spawn_padding)
        tz = random.randint(-(world_half_size - tree_spawn_padding), world_half_size - tree_spawn_padding)
        if (abs(tx) > safe_spawn_radius or abs(tz) > safe_spawn_radius) and not is_inside_lake(tx, tz):
            create_tree(tx, tz)


def spawn_shadow_portal():
    global shadow_portal
    if shadow_portal or shadow_world_active:
        return

    shadow_portal = Portal(position=(0, 1.6, 10))
    portal_text.enabled = True
    wave_status_text.text = 'Enter The Portal'


def enter_shadow_world():
    global shadow_world_active, shadow_portal, shadow_wave_number
    shadow_world_active = True
    shadow_wave_number = 0

    if shadow_portal:
        destroy(shadow_portal)
        shadow_portal = None

    portal_text.enabled = False
    sky.color = color.rgb(120, 40, 160)
    player.position = Vec3(0, 2, 0)
    build_world()
    update_enemy_counter()

def spawn_enemy_wave():
    """יצירת גל חדש של אויבים: קודם זומבים ואז שלדים יורים"""
    global enemy_wave_number, shadow_wave_number
    if len(zombies_list) == 0:
        if shadow_portal and not shadow_world_active:
            return

        if shadow_world_active:
            shadow_wave_number += 1
            enemy_class = MutantZombie
            spawn_count = 5
        else:
            enemy_wave_number += 1
            enemy_class = Zombie if enemy_wave_number <= 2 else Skeleton
            spawn_count = 5

        for i in range(spawn_count):
            rx = random.randint(-(world_half_size - tree_spawn_padding), world_half_size - tree_spawn_padding)
            rz = random.randint(-(world_half_size - tree_spawn_padding), world_half_size - tree_spawn_padding)
            if abs(rx) < safe_spawn_radius and abs(rz) < safe_spawn_radius:
                rx = safe_spawn_radius * 3 if rx >= 0 else -safe_spawn_radius * 3
            enemy = enemy_class(position=(rx, 1, rz))
            zombies_list.append(enemy)
        update_enemy_counter()

def update():
    """לולאת המשחק הראשית"""
    global current_texture, current_block_color, game_active, time_of_day
    if not game_active: return

    if shadow_portal and distance_xz(player.position, shadow_portal.position) < 2.2:
        enter_shadow_world()
    
    time_of_day += time.dt * 0.05
    if shadow_world_active:
        sky.color = color.rgb(120, 40, 160)
    else:
        sky.color = color.rgb(
            max(10, int(135 - math.sin(time_of_day) * 125)),
            max(10, int(206 - math.sin(time_of_day) * 196)),
            max(20, int(250 - math.sin(time_of_day) * 230))
        )
    
    if math.sin(time_of_day) < -0.5 and len(zombies_list) == 0:
        spawn_enemy_wave()
    
    move_speed = 6 * time.dt
    if held_keys['up arrow'] or held_keys['w']: player.position += player.forward * move_speed
    if held_keys['down arrow'] or held_keys['s']: player.position -= player.forward * move_speed
    if held_keys['left arrow'] or held_keys['a']: player.position -= player.right * move_speed
    if held_keys['right arrow'] or held_keys['d']: player.position += player.right * move_speed
    
    if held_keys['1']:
        current_texture = grass_texture
        current_block_color = None
        selected_block_text.text = 'Selected Block: grass'
    if held_keys['2']:
        current_texture = stone_texture
        current_block_color = None
        selected_block_text.text = 'Selected Block: stone'
    if held_keys['3']:
        current_texture = brick_texture
        current_block_color = None
        selected_block_text.text = 'Selected Block: brick'
    if held_keys['4']:
        current_texture = dirt_texture
        current_block_color = None
        selected_block_text.text = 'Selected Block: dirt'

def input(key):
    if key == 'escape':
        application.quit()

    if not game_active: return
    if key == 'left mouse down':
        if isinstance(mouse.hovered_entity, Voxel):
            return
        sword.attack()
        target_enemy = get_enemy_from_entity(mouse.hovered_entity)
        if target_enemy and distance(player.position, target_enemy.position) < 6:
            target_enemy.take_damage()
            return

        for enemy in list(zombies_list):
            if distance(player.position, enemy.position) < 6:
                enemy.take_damage()
                break

# יצירת עולם גדול (1 קוביות)
build_world()

# הגדרת בקר השחקן
player = FirstPersonController()
player.cursor.visible = True

# יצירת החרב ביד
sword = Sword()

# יצירת רשימת זומבים התחלתית
zombies_list = []
spawn_enemy_wave()

# הגדרת שמים
sky = Sky()

# הרצת המשחק
app.run()
