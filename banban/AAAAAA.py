from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import os
import random
from math import sin

# ביטול שמע למניעת בעיות תאימות בלינוקס
os.environ['PANDA_PRC_DIR'] = '' 

app = Ursina()

# הגדרות חלון המשחק
window.title = "Garten Of Banban - Connected Mega-Maze"
window.fps_counter.enabled = False
window.color = color.rgb(15, 0, 0)
try:
    sky = Sky(texture=None)
    sky.color = color.rgb(15, 0, 0)
    scene.fog_color = color.rgb(15, 0, 0)
    scene.fog_density = 0.018
except Exception:
    pass

# משתני משחק גלובליים
hp = 500
game_over = False
current_zone = 1
max_zones = 5

# רשימות לניהול אובייקטים דינמיים
keys_dict = {}     
doors_dict = {}    
inventory = {1: False, 2: False, 3: False, 4: False, 5: False}
walls_dict = {}
corridor_positions = set()

# פנס ידני פשוט (ניתן לכבות/להדליק ב-F)
flashlight = None
flashlight_on = True

# מחלקה אינטראקטיבית פשוטה (מניפולטורים, הקלטות וכו')
class Interactive(Entity):
    def __init__(self, action=None, **kwargs):
        super().__init__(**kwargs)
        self.action = action
        self.interactive = True

    def interact(self):
        if callable(self.action):
            try:
                self.action(self)
            except Exception:
                pass

# grabbed object state
grabbed_entity = None
projectiles = []

class Doll(Entity):
    def __init__(self, name='Poppy', pos=(0,1,0), scale=(0.9,1.6,0.9)):
        super().__init__(model='cube', texture='scary_face.png', position=pos, scale=scale, collider='box')
        self.name = name
        self.wobble = 0
        self.grabbable = True
        self.interactive = True

    def update(self):
        # simple idle bob and slight rotation to feel alive
        self.wobble += time.dt * 3.0
        self.y = 1 + sin(self.wobble) * 0.08
        self.rotation_y += time.dt * 6

    def interact(self):
        # default interaction is grab
        try_grab(self)

def try_grab(ent):
    global grabbed_entity
    if grabbed_entity is None:
        # pick up
        grabbed_entity = ent
        grabbed_entity.original_parent = ent.parent
        grabbed_entity.parent = camera
        grabbed_entity.position = Vec3(0, -0.2, 1.4)
        grabbed_entity.rotation = Vec3(0,0,0)
        try:
            grabbed_entity.collider = None
        except Exception:
            pass
        mission.text = f"Grabbed: {getattr(ent,'name','object')}"
    else:
        # drop current
        drop_grabbed()

def drop_grabbed(throw=False):
    global grabbed_entity
    if not grabbed_entity:
        return
    e = grabbed_entity
    grabbed_entity = None
    e.parent = scene
    # place in front of player
    place = player.position + camera.forward * 3
    e.position = Vec3(place.x, max(0.5, place.y), place.z)
    try:
        e.collider = 'box'
    except Exception:
        pass
    mission.text = "Released"

class MonsterBullet(Entity):
    def __init__(self, position, direction):
        super().__init__(model='sphere', color=color.green, position=position, scale=0.5, collider='box')
        self.direction = direction.normalized()
        self.speed = 22
        self.hit = False

    def update(self):
        global hp, game_over
        self.position += self.direction * self.speed * time.dt
        hit_player = False
        try:
            hit_player = self.intersects(player).hit
        except Exception:
            pass
        if (hit_player or distance(self.position, player.position) < 2.0) and not self.hit:
            self.hit = True
            hp -= 10
            if hp < 0:
                hp = 0
            hp_text.text = f"HP: {hp}"
            if hp <= 30:
                hp_text.color = color.red
            elif hp <= 60:
                hp_text.color = color.yellow
            else:
                hp_text.color = color.green
            camera_shake()
            if hp <= 0:
                game_over = True
                message.text = "YOU DIED"
                message.color = color.red
                player.speed = 0
                mouse.locked = False
            destroy(self)
            return
        if distance(self.position, player.position) > 120:
            destroy(self)

# אפקט זעזוע מצלמה
def camera_shake(intensity=0.15, duration=0.18, steps=5):
    original_pos = camera.position
    for i in range(steps):
        offset = Vec3(random.uniform(-intensity, intensity), random.uniform(-intensity, intensity), 0)
        invoke(setattr, camera, 'position', original_pos + offset, delay=(i * duration / steps))
    invoke(setattr, camera, 'position', original_pos, delay=duration)

# אפקט שולחן אימה קצר
def scare_flash():
    try:
        screen_overlay.enabled = True
        screen_overlay.color = color.rgba(255, 0, 0, 150)
        invoke(setattr, screen_overlay, 'color', color.rgba(255, 0, 0, 0), delay=0.08)
        invoke(setattr, screen_overlay, 'enabled', False, delay=0.09)
    except Exception:
        pass

# אפקט כיבוי/הדלקת פנס מהירה
def flicker_light():
    try:
        if flashlight:
            was_on = flashlight.enabled
            flashlight.enabled = False
            invoke(setattr, flashlight, 'enabled', was_on, delay=0.07)
    except Exception:
        pass

# אפקט ברק קפיצה
def lightning_flash():
    try:
        lightning_overlay.enabled = True
        lightning_overlay.color = color.rgba(255,255,255,180)
        invoke(setattr, lightning_overlay, 'color', color.rgba(255,255,255,0), delay=0.05)
        invoke(setattr, lightning_overlay, 'enabled', False, delay=0.06)
        if flashlight and flashlight_on:
            flashlight.enabled = False
            invoke(setattr, flashlight, 'enabled', True, delay=0.06)
    except Exception:
        pass

# עיצוב ממשק המשתמש (UI)
hp_text = Text(text="HP: 500", position=(-0.85, 0.45), scale=2, color=color.yellow)
zone_text = Text(text="Zone: 1/3", position=(-0.85, 0.38), scale=1.8, color=color.azure)
mission = Text(text="FIND THE FIRST GOLDEN KEY", position=(-0.25, 0.45), scale=2, color=color.rgb(140, 0, 0))
message = Text(text="", origin=(0, 0), scale=4, color=color.white)

# וינייטה/אווירה קטנה לאווירת אימה
vignette = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,50), scale=(2,2), enabled=False)

# אפקט אדום לחלקי קפיצה בלבד
screen_overlay = Entity(parent=camera.ui, model='quad', color=color.rgba(255,0,0,0), scale=(2,2), enabled=False)

# אפקט ברק לבן
lightning_overlay = Entity(parent=camera.ui, model='quad', color=color.rgba(255,255,255,0), scale=(2,2), enabled=False)

# רשימת רוחות זמניות
ghosts = []

# ניסיון לנגן צליל אווירה אם קיים (לא חובה)
ambient_sound = None
try:
    ambient_sound = Audio('ambient.ogg', loop=True, autoplay=True)
except Exception:
    ambient_sound = None

# שחקן - נוצר זמנית ללא כוח משיכה כדי שלא ייפול בזמן שהמפה נטענת
player = FirstPersonController(speed=7, gravity=0)

# מערך המבוכים המחוברים
LEVEL_MAPS = {
    1: [
        "WWWWWWWWWWWWWWWWWWWWWWWW",
        "WSR                    W",
        "W  WWWWWW      WWWWWW  W",
        "W  W K  W        W     W",
        "W  W    WWWWW     W    W",
        "W  WWWW            W   W",
        "W       WWWWW        W W",
        "WWWWWW  W   W        W W",
        "W B     W   W      WWWWWW",
        "W  WWWWWW               W",
        "W       W     D         W", 
        "WWWWWWWWWWWWWWWWWWWWWWWW"
                 
    




    ],
    2: [
        "WWWWWWWWWWWWWWWWWW", 
        "W      W         W",
        "W  WWW W WWW     W",
        "W  W   W   W     W",
        "W  W N W K W     W",
        "W  W   W   W     W",
        "W  WWWWW   W     W",
        "W          W     W",
        "W  WWWWWWWWW     W",
        "W  W             W",
        "W  W B           W",
        "W  WWWWWWWWW     W",
        "W            D   W", 
        "WWWWWWWWWWWWWWWWWW"
    ],
    3: [
        "WWWWWWWWWWWWWWWWWW", 
        "W    W      K    W",
        "W    W WWWWWW    W",
        "W WW W W         W",
        "W W  W W N       W",
        "W W BB WWWWWW    W",
        "W W              W",
        "W WWWWWWWWWW     W",
        "W W  B     W     W",
        "W W WWWWWW W     W",
        "W W      W W     W",
        "W WWWWWW W W     W",
        "W            D   W", 
        "WWWWWWWWWWWWWWWWWW"
    ],
    4: [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   W    B      K  W",
        "W   W WWWWWWWW WWW W",
        "W   W      N      W",
        "W WWWW WWWWWWWWWW W",
        "W W              WW",
        "W W WWWWWWWWWW    W",
        "W W W      W W    W",
        "W W W  B   W W    W",
        "W W WWWWWWWW W    W",
        "W W            W  W",
        "W WWWWWWWWWWWW WWWW",
        "W            D    W",
        "WWWWWWWWWWWWWWWWWWWW"
    ],
    5: [
        "WWWWWWWWWWWWWWWWWWWWWW",
        "W K  WWWWWWWWWWWWW  W",
        "W WW W          W W W",
        "W W  W WWWWWWWW W W W",
        "W W WW W      W W W W",
        "W W    W  BB  W W W W",
        "W WWWWWW WWWW W W W W",
        "W        W  W W W W W",
        "W WWWWWW W  W W W W W",
        "W W    W W  W W W W W",
        "W W WW W W  W W W W W",
        "W W  W W W  W W W   W",
        "W WW W W WW W W WWW W",
        "W    W W    W W    W",
        "W WWWWWWWWWWWW WWWW W",
        "W N           B    W",
        "W WWWWWWWWWWWWWWWW W",
        "W                D W",
        "WWWWWWWWWWWWWWWWWWWWWW"
    ]
}

# מחלקת מפלצות בצבע כתום
class Monster(Entity):
    def __init__(self, name, eye_color, pos, speed, damage, size=(1.2, 2.5, 1.2)):
        super().__init__(
            model='cube',
            color=color.rgb(120, 30, 140),         
            texture='scary_face.png',   
            position=pos,
            scale=size,
            collider='box',
            origin_y=-0.5
        )
        self.name = name
        self.base_speed = speed
        self.speed = speed
        self.damage = damage
        self.attack_cooldown = 0
        self.wobble_time = 0
        self.chasing = False
        self.stealth_timer = 0
        
        # override eye color to red for creepier look
        eye_color = color.red
        self.eye_left = Entity(parent=self, model='cube', color=eye_color, position=(-0.2, 0.6, 0.51), scale=(0.15, 0.15, 0.05))
        self.eye_right = Entity(parent=self, model='cube', color=eye_color, position=(0.2, 0.6, 0.51), scale=(0.15, 0.15, 0.05))

        # optional breathing/heartbeat sound reference (if asset exists)
        self._heartbeat = None
        try:
            self._heartbeat = Audio('heartbeat.ogg', loop=False, autoplay=False)
        except Exception:
            self._heartbeat = None
        # growl / screamer fallback
        try:
            self._scream = Audio('screamer.ogg', loop=False, autoplay=False)
        except Exception:
            self._scream = None
        self.shoot_cooldown = 0

    def shoot(self, target):
        bullet_pos = self.position + self.forward * 1.4 + Vec3(0, 0.5, 0)
        bullet_dir = (target.position + Vec3(0, 0.7, 0) - self.position).normalized()
        b = MonsterBullet(position=bullet_pos, direction=bullet_dir)
        projectiles.append(b)

    def update(self):
        global hp, game_over
        if game_over:
            return

        if distance(self, player) > 40:
            return

        target_pos = Vec3(player.position.x, self.position.y, player.position.z)
        self.look_at(target_pos)
        
        dist = distance(self, player)
        if dist < 5.0:
            self.speed = 0
            if self.shoot_cooldown <= 0:
                self.shoot(player)
                self.shoot_cooldown = 1.4
        else:
            self.speed = self.base_speed
            # threat state
            if dist < 18:
                self.chasing = True
                self.color = color.rgb(180, 20, 20)
            elif dist > 26:
                self.chasing = False

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= time.dt

        if self.name == "Nabnab":
            player_forward = camera.forward
            to_monster = (self.position - player.position).normalized()
            dot_product = player_forward.dot(to_monster)
            if dot_product > 0.7:
                self.speed = 0
                self.color = color.rgb(200, 100, 0)
            else:
                self.speed = self.base_speed
                if self.chasing:
                    self.color = color.red
                else:
                    self.color = color.orange

        # adapt speed when chasing
        if self.chasing:
            move_speed = self.speed * 1.9
        else:
            move_speed = self.speed

        if dist < 2.2:
            move_speed = 0

        self.position += self.forward * move_speed * time.dt
        
        if self.speed > 0:
            self.wobble_time += time.dt * 10
            self.scale_y = 2.5 + sin(self.wobble_time) * 0.15
            
            flash = sin(self.wobble_time * 2)
            if flash > 0:
                self.color = color.rgb(220, 40, 20)
            else:
                self.color = color.rgb(255, 69, 0)

        if distance(self, player) < 2.0:
            self.attack_cooldown -= time.dt
            if self.attack_cooldown <= 0:
                hp -= self.damage
                self.attack_cooldown = 1.2
                
                hp_text.text = f"HP: {hp}"
                if hp <= 30:
                    hp_text.color = color.red
                elif hp <= 60:
                    hp_text.color = color.yellow

                if hp <= 0:
                    game_over = True
                    message.text = "YOU DIED!!!"
                    message.color = color.red
                    player.speed = 0
                    mouse.locked = False

        # trigger a jumpscare if very close
        if distance(self, player) < 3.0:
            try:
                if self._scream and not self._scream.playing:
                    self._scream.play()
            except Exception:
                pass

        # play a subtle heartbeat sound when monster is near
        try:
            if self._heartbeat and distance(self, player) < 6 and not self._heartbeat.playing:
                self._heartbeat.play()
        except Exception:
            pass

# פונקציה הבונה את כל העולם המחובר
def build_mega_maze():
    z_offset = 0  
    gap_distance = 170 
    
    for zone_id in range(1, max_zones + 1):
        current_map = LEVEL_MAPS[zone_id]
        door_pos = None
        
        for z, row in enumerate(current_map):
            for x, char in enumerate(row):
                pos = Vec3(x * 3, 0, (z * 3) + z_offset)
                
                # בניית רצפה מוצקה לכל משבצת במפה (צבע שחור)
                Entity(model='cube', color=color.black, position=(pos.x, 0, pos.z), scale=(3, 0.5, 3), collider='box')
                
                if char == 'W':
                    wall = Entity(model='cube', color=color.rgb(40, 0, 10), position=(pos.x, 1.5, pos.z), scale=(3, 3, 3), collider='box')
                    walls_dict[(int(pos.x), int(pos.z))] = wall
                elif char == 'S' and zone_id == 1:
                    # מיקום השחקן מוצב בדיוק מעל הרצפה (Y=1)
                    player.position = Vec3(pos.x, 1, pos.z)
                elif char == 'K':
                    key = Entity(model='cube', color=color.gold, position=(pos.x, 1, pos.z), scale=(0.6, 0.6, 0.6), collider='box')
                    keys_dict[zone_id] = key
                elif char == 'D':
                    # remove any wall in a 3x3 area around the door position so there's an actual opening
                    for dx in (-3, 0, 3):
                        for dz in (-3, 0, 3):
                            wkey = (int(pos.x + dx), int(pos.z + dz))
                            existing = walls_dict.pop(wkey, None)
                            if existing:
                                destroy(existing)

                    # create a visual door but don't block the player (no collider)
                    door = Entity(model='cube', color=color.blue, position=(pos.x, 1.5, pos.z), scale=(3, 3, 0.5), collider=None)
                    doors_dict[zone_id] = door
                    door_pos = pos
                    # add a simple lever near the door the player can interact with
                    try:
                        def _pull(lever, zid=zone_id):
                            inventory[zid] = True
                            mission.text = f"LEVER PULLED: ZONE {zid} UNLOCKED"
                            mission.color = color.green
                            destroy(lever)
                            try:
                                Audio('lever.ogg', autoplay=True)
                            except Exception:
                                pass

                        Interactive(action=_pull, model='cube', color=color.azure, position=(pos.x + 3, 1, pos.z), scale=(0.6,0.6,0.6), collider='box')
                    except Exception:
                        pass
                elif char == 'B':
                    Monster(name="Banban", eye_color=color.green, pos=(pos.x, 1, pos.z), speed=3, damage=20)
                elif char == 'N':
                    Monster(name="Nabnab", eye_color=color.magenta, pos=(pos.x, 1, pos.z), speed=4.2, damage=30)
                    if zone_id == 5:
                        Monster(name="Nabnab", eye_color=color.magenta, pos=(pos.x + 3, 1, pos.z), speed=5.2, damage=35)
                
        # בניית מסדרון מחבר תוך שימוש במיקום ה-Z הגלובלי המדויק
        if door_pos and zone_id < max_zones:
            next_zone_z_start = z_offset + gap_distance
            start_z = int(door_pos.z) + 3
            # try to align corridor end with the next zone's door x position
            try:
                next_map = LEVEL_MAPS[zone_id + 1]
                next_door_x = None
                for nz, nrow in enumerate(next_map):
                    if 'D' in nrow:
                        next_door_x = nrow.index('D') * 3
                        break
                if next_door_x is None:
                    next_door_x = door_pos.x
            except Exception:
                next_door_x = door_pos.x

            # compute corridor steps and interpolate x across corridor so it connects to next door
            corridor_z_list = list(range(start_z, next_zone_z_start + 3, 3))
            steps = max(1, len(corridor_z_list))
            start_x = int(door_pos.x)
            end_x = int(next_door_x)

            for i, corridor_z in enumerate(corridor_z_list):
                t = i / max(1, steps - 1)
                target_x = round(start_x + (end_x - start_x) * t)
                # snap to grid multiple of 3
                if target_x % 3 != 0:
                    target_x = int(round(target_x / 3.0) * 3)

                # הסר קירות קיימים במסלול המסדרון סביב היעד (מרכז ושני הצדדים)
                for dx in (0, -3, 3):
                    wkey = (int(target_x + dx), int(corridor_z))
                    existing = walls_dict.pop(wkey, None)
                    if existing:
                        destroy(existing)

                # רצפת מסדרון (צבע שחור)
                Entity(model='cube', color=color.black, position=(target_x, 0, corridor_z), scale=(3, 0.5, 3), collider='box')
                # record corridor positions so later zone walls won't block the path
                corridor_positions.add((int(target_x), int(corridor_z)))
                corridor_positions.add((int(target_x - 3), int(corridor_z)))
                corridor_positions.add((int(target_x + 3), int(corridor_z)))

                # no side walls for the bridge section

        z_offset += gap_distance 

        # לאחר בניית כל האזורים והמסדרונות - נוודא שקירות לא חסמו את המסדרון
        for key in list(corridor_positions):
            existing = walls_dict.pop(key, None)
            if existing:
                destroy(existing)

        # רק לאחר שכל הרצפות והקירות נבנו, נחזיר לשחקן את כוח המשיכה שלו
        # הורדת כוח הכבידה תאפשר קפיצה גבוהה יותר
        player.gravity = 0.25
        # נסיון להגדיל גם פרמטר קפיצה במידה וה-FPC תומך בו
        try:
            player.jump_height = 3.2
        except Exception:
            pass

build_mega_maze()

# יצירת פנס שמחובר למצלמה (ניתן לכבות/להדליק עם F)
try:
    flashlight = PointLight(parent=camera, color=color.rgb(255,180,120), range=18, shadows=False)
    flashlight.enabled = flashlight_on
except Exception:
    flashlight = None

# מפזר אור אדום וחושך סביב השחקן
try:
    ambient_light = AmbientLight(color=color.rgb(70, 0, 0))
except Exception:
    ambient_light = None

# spawn dolls near keys/doors for player to grab
try:
    for zone_id, current_map in LEVEL_MAPS.items():
        z_offset = (zone_id - 1) * 130
        placed = 0
        for z, row in enumerate(current_map):
            if placed >= 1:
                break
            if 'K' in row or 'D' in row or 'B' in row:
                x = row.find('K') if 'K' in row else (row.find('D') if 'D' in row else row.find('B'))
                if x >= 0:
                    doll_pos = Vec3(x * 3, 1, (z * 3) + z_offset + 3)
                    d = Doll(name=f'Poppy_{zone_id}', pos=doll_pos, scale=(0.9,1.6,0.9))
                    d.grabbable = True
                    placed += 1
except Exception:
    pass

def input(key):
    global flashlight_on, grabbed_entity
    if key == 'f':
        flashlight_on = not flashlight_on
        try:
            flashlight.enabled = flashlight_on
        except Exception:
            pass
        mission.text = "Flashlight On" if flashlight_on else "Flashlight Off"

    if key == 'left mouse down' and mouse.hovered_entity:
        ent = mouse.hovered_entity
        if getattr(ent, 'interactive', False):
            ent.interact()

    # grab/release with G
    if key == 'g':
        if grabbed_entity:
            drop_grabbed()
        else:
            if mouse.hovered_entity and getattr(mouse.hovered_entity, 'grabbable', False):
                try_grab(mouse.hovered_entity)

def update():
    global game_over, current_zone
    if game_over:
        return

    if held_keys['left shift']:
        player.speed = 12  
    else:
        player.speed = 7  

    # עדכון אזור לפי מיקום השחקן
    current_zone = min(max_zones, int(player.position.z / 150) + 1)
        
    zone_text.text = f"Zone: {current_zone}/{max_zones}"

    # סיבוב ובדיקת איסוף מפתחות
    for zone_id, key in keys_dict.items():
        if key and key.enabled:
            key.rotation_y += 60 * time.dt
            if distance(player, key) < 2.5:
                inventory[zone_id] = True
                key.enabled = False
                destroy(key)
                if zone_id == max_zones:
                    mission.text = "FINAL KEY ACQUIRED! OPEN THE FINAL DOOR"
                else:
                    mission.text = f"ZONE {zone_id} KEY ACQUIRED! UNLOCK THE RED DOOR"
                mission.color = color.green

    # בדיקת אינטראקציה ופתיחת דלתות
    for zone_id, door in doors_dict.items():
        if door and door.enabled:
            if distance(player, door) < 3.5:
                if inventory[zone_id]:
                    door.enabled = False
                    destroy(door)
                    
                    if zone_id == max_zones:
                        message.text = "FINAL DOOR OPENED! FACE THE ULTIMATE CHALLENGE"
                        message.color = color.orange
                        mission.text = "ZONE 5: FINAL SHOWDOWN"
                        player.speed = 7
                    else:
                        mission.text = f"PROCEED TO ZONE {zone_id + 1}"
                        mission.color = color.cyan
                else:
                    if mission.text != f"ZONE {zone_id} IS LOCKED! FIND THE GOLDEN KEY":
                        mission.text = f"ZONE {zone_id} IS LOCKED! FIND THE GOLDEN KEY"
                        mission.color = color.red

    # אפקטי אווירה רנדומליים: רוחות קטנות ונקודות אימה
    try:
        if random.random() < 0.02:
            g = Entity(model='quad', color=color.rgba(255,255,255,30), position=player.position + Vec3(random.uniform(-6,6), random.uniform(-1,3), random.uniform(-6,6)), scale=(1.4,2), double_sided=True, rotation=Vec3(0, random.uniform(0,360), 0))
            invoke(destroy, g, delay=1.2)

        if random.random() < 0.008:
            scare_flash()
            if flashlight_on and flashlight:
                flicker_light()

        if random.random() < 0.006:
            lightning_flash()

        if random.random() < 0.004:
            ghost = Entity(model='quad', color=color.rgba(255,255,255,15), position=player.position + camera.forward * 7 + Vec3(random.uniform(-1.5,1.5), random.uniform(-0.5,1.5), 0), scale=(3,3), double_sided=True, rotation=Vec3(0, random.uniform(0,360), 0), collider=None)
            invoke(destroy, ghost, delay=0.4)
    except Exception:
        pass

app.run()
