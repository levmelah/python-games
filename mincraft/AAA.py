from ursina import *
import random
import math

# אתחול המנוע התלת-ממדי
app = Ursina()

# הגדרות חלון חסינות באגים של מסך לבן/שחור
window.color = color.rgb(135, 206, 250) # שמיים כחולים
window.show_ursina_splash = False       # טעינה מהירה ללא מסך פתיחה

# מאגר הבלוקים הרשמי של המשחק
BLOCK_TYPES = {
    '1': {'name': 'Grass', 'texture': 'grass', 'color': color.white},
    '2': {'name': 'Stone', 'texture': 'stone', 'color': color.white},
    '3': {'name': 'Brick', 'texture': 'brick', 'color': color.white},
    '4': {'name': 'Dirt',  'texture': 'dirt',  'color': color.white},
    '5': {'name': 'Blue Wool', 'texture': 'white_cube', 'color': color.blue},
    '6': {'name': 'Yellow Wool', 'texture': 'white_cube', 'color': color.yellow},
    '7': {'name': 'Pink Wool', 'texture': 'white_cube', 'color': color.pink},
    '8': {'name': 'Orange Wool', 'texture': 'white_cube', 'color': color.orange}
}

current_key = '1'
generated_chunks = {} # מילון לשמירת המיקומים שכבר יצרנו בעולם
loaded_voxels = {}    # מילון לשמירת הבלוקים שקיימים כרגע פיזית על המסך

class Voxel(Button):
    """מחלקה לייצוג קובייה בעולם תלת-ממדי"""
    def __init__(self, position=(0,0,0), block_info=BLOCK_TYPES['1']):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=block_info['texture'],
            color=block_info['color'],
            scale=1,
            collider='box'
        )

    def dig_block(self):
        """חפירת הבלוק הנוכחי מטווח קרוב"""
        if distance(player.position, self.position) < 5.5:
            # הסרה ממילון הבלוקים הנטענים כדי שלא יווצר מחדש
            pos_key = (int(self.x), int(self.y), int(self.z))
            if pos_key in loaded_voxels:
                del loaded_voxels[pos_key]
            destroy(self)

    def build_block(self, normal):
        """בניית בלוק חדש לפי סוג הבלוק שנבחר"""
        build_pos = self.position + normal
        pos_key = (int(build_pos.x), int(build_pos.y), int(build_pos.z))
        voxel = Voxel(position=build_pos, block_info=BLOCK_TYPES[current_key])
        loaded_voxels[pos_key] = voxel

# 🧱 יצירת ממשק המשתמש (UI)
crosshair = Text(text='+', position=(0, 0), origin=(0, 0), scale=2, color=color.white)

# סרגל כלים תחתון (Hotbar Slots)
hotbar_slots = []
for i, key in enumerate(BLOCK_TYPES.keys()):
    slot = Entity(
        parent=camera.ui,
        model='quad',
        texture=BLOCK_TYPES[key]['texture'],
        color=BLOCK_TYPES[key]['color'],
        scale=(0.06, 0.06),
        position=(-0.245 + (i * 0.07), -0.42)
    )
    hotbar_slots.append(slot)

# מסגרת הבחירה הלבנה בתוך ה-Hotbar
selector = Entity(
    parent=camera.ui,
    model='quad',
    color=color.rgba(255, 255, 255, 0.5),
    scale=(0.068, 0.068),
    position=(hotbar_slots[0].x, hotbar_slots[0].y),
    z=-1
)

# מודל הבלוק שמוחזק ביד של השחקן (Hand Block)
hand_block = Entity(
    parent=camera.ui,
    model='cube',
    texture=BLOCK_TYPES[current_key]['texture'],
    color=BLOCK_TYPES[current_key]['color'],
    scale=(0.12, 0.12, 0.12),
    position=(0.6, -0.3, 0.5),
    rotation=(20, -30, 10)
)

# יצירת ישות השחקן והמצלמה (מתחיל בגובה 15 בשמיים)
player = Entity(position=(0, 15, 0))
camera.parent = player
camera.position = (0, 1.5, 0) 
camera.rotation = (0, 0, 0)
player_rotation_x = 0

# תאורת סביבה לקבלת צללים ועומק
main_light = DirectionalLight(parent=scene, y=30, x=20, z=10)
main_light.look_at(Vec3(0, 0, 0))

def create_tree_dynamic(x, y_start, z):
    """מחולל עץ ריאליסטי דינמי ישירות לתוך מאגר הבלוקים"""
    trunk_height = random.randint(3, 4)
    # גזע עץ
    for y in range(1, trunk_height + 1):
        pos = (x, y_start + y, z)
        if pos not in loaded_voxels:
            loaded_voxels[pos] = Voxel(position=pos, block_info=BLOCK_TYPES['2'])
    
    # עלים
    for lx in range(-1, 2):
        for lz in range(-1, 2):
            for ly in range(trunk_height + 1, trunk_height + 3):
                pos = (x + lx, y_start + ly, z + lz)
                if pos not in loaded_voxels:
                    loaded_voxels[pos] = Voxel(position=pos, block_info=BLOCK_TYPES['3'])

def manage_infinite_world():
    """מנגנון חכם המייצר ומנקה בלוקים סביב מיקום השחקן בזמן אמת"""
    # רדיוס הטעינה סביב השחקן (שומר על ביצועים גבוהים)
    view_radius = 18 
    
    player_x = int(player.x)
    player_z = int(player.z)
    
    # 1. יצירת בלוקים חדשים בטווח הראייה
    for z in range(player_z - view_radius, player_z + view_radius):
        for x in range(player_x - view_radius, player_x + view_radius):
            # חישוב מתמטי חלק של גבעות ועמקים (Perlin Noise אלטרנטיבי)
            freq = 0.08
            amp = 5
            y_height = int((math.sin(x * freq) * math.cos(z * freq)) * amp)
            
            # מפתח המיקום הייחודי של רצפת הקרקע הזו
            pos_key_grass = (x, y_height, z)
            pos_key_stone = (x, y_height - 1, z)
            
            # אם הבלוק לא נטען עדיין על המסך
            if pos_key_grass not in loaded_voxels:
                # יצירת דשא
                loaded_voxels[pos_key_grass] = Voxel(position=pos_key_grass, block_info=BLOCK_TYPES['1'])
                # יצירת סלע תחתיו
                loaded_voxels[pos_key_stone] = Voxel(position=pos_key_stone, block_info=BLOCK_TYPES['2'])
                
                # סיכוי אקראי מבוסס מיקום ליצירת עץ קבוע
                # משתמשים בפונקציה מתמטית יציבה כדי שהעצים לא ישתנו בכל פעם שחוזרים לאותו מקום
                if (abs(sin(x*5) * cos(z*3))) > 0.97 and (abs(x) > 4 or abs(z) > 4):
                    create_tree_dynamic(x, y_height, z)

    # 2. מחיקת בלוקים רחוקים מדי כדי למנוע עומס על הזיכרון
    for pos_key in list(loaded_voxels.keys()):
        voxel_x, voxel_y, voxel_z = pos_key
        # אם הבלוק רחוק מדי מהשחקן, ננקה אותו זמנית מהמסך
        if abs(voxel_x - player_x) > view_radius + 4 or abs(voxel_z - player_z) > view_radius + 4:
            destroy(loaded_voxels[pos_key])
            del loaded_voxels[pos_key]

def update():
    """לולאת המשחק הראשית שרצה כל פריים"""
    global current_key, player_rotation_x
    
    # קריאה למנהל העולם האינסופי
    manage_infinite_world()
    
    # 1. סיבוב המבט (מקשי החצים)
    look_speed = 100 * time.dt
    if held_keys['left arrow']:  player.rotation_y -= look_speed
    if held_keys['right arrow']: player.rotation_y += look_speed
    
    if held_keys['up arrow']:    player_rotation_x -= look_speed
    if held_keys['down arrow']:  player_rotation_x += look_speed
    player_rotation_x = clamp(player_rotation_x, -80, 80)
    camera.rotation_x = player_rotation_x

    # 2. תנועת השחקן (WASD)
    move_speed = 8 * time.dt
    if held_keys['w']: player.position += player.forward * move_speed
    if held_keys['s']: player.position -= player.forward * move_speed
    if held_keys['a']: player.position -= player.right * move_speed
    if held_keys['d']: player.position += player.right * move_speed
    
    # 3. תעופה חופשית (רווח לעלייה, שיפט שמאלי לירידה)
    if held_keys['space']:      player.position += Vec3(0, 6 * time.dt, 0)
    if held_keys['left shift']: player.position -= Vec3(0, 6 * time.dt, 0)
    
    # 4. החלפת בלוקים (1 עד 8) + עדכון הבלוק שביד
    for key in BLOCK_TYPES.keys():
        if held_keys[key]:
            current_key = key
            index = list(BLOCK_TYPES.keys()).index(key)
            selector.x = hotbar_slots[index].x
            hand_block.texture = BLOCK_TYPES[key]['texture']
            hand_block.color = BLOCK_TYPES[key]['color']

def input(key):
    """ניהול קלט מקלדת לפעולות חפירה ובנייה אינטראקטיביות"""
    hit_info = raycast(player.position + Vec3(0, 1.5, 0), player.forward, distance=6)
    
    if hit_info.hit and isinstance(hit_info.entity, Voxel):
        target_voxel = hit_info.entity
        
        # מקש Z: חפירה ושבירת הבלוק
        if key == 'z':
            target_voxel.dig_block()
            
        # מקש X: בניית בלוק חדש
        if key == 'x':
            if distance(player.position, target_voxel.position) < 5.5:
                target_voxel.build_block(hit_info.normal)

# הרצת המשחק
app.run()
