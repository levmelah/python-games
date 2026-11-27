from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from panda3d.core import PerlinNoise2

# רעש פרלין מובנה של panda3d (במקום ספריית noise, שלא מותקנת) ליצירת גבעות טבעיות
_perlin = PerlinNoise2(1, 1, 256, 1)

def pnoise2(x, y, octaves=1):
    # כמו pnoise2 מספריית noise: כל שכבה בתדר כפול ובחצי עוצמה
    total, amp, freq, max_amp = 0.0, 1.0, 1.0, 0.0
    for _ in range(octaves):
        total += _perlin.noise(x * freq, y * freq) * amp
        max_amp += amp
        amp *= 0.5
        freq *= 2.0
    # 0.7 - כדי שהטווח יהיה כמו של ספריית noise
    return total / max_amp * 0.7
import random

# 1. אתחול מנוע המשחק
app = Ursina()

# 2. הגדרת סוגי הבלוקים והטקסטורות שלהם
# נשתמש בטקסטורות ובצבעים מובנים של Ursina
BLOCKS = {
    1: {'name': 'Grass', 'texture': 'grass', 'color': color.white},
    2: {'name': 'Stone', 'texture': 'stone', 'color': color.light_gray},
    3: {'name': 'Wood', 'texture': 'brick', 'color': color.brown},
    4: {'name': 'Glass', 'texture': 'white_cube', 'color': color.rgba(255,255,255,100)}, # חצי שקוף
    5: {'name': 'Lava', 'texture': 'white_cube', 'color': color.orange}
}

# הבלוק הנוכחי שנבחר (ברירת מחדל: דשא)
current_block_id = 1

# 3. יצירת אלמנטים על המסך (UI)
# טקסט המציג את הבלוק הנבחר
block_text = Text(
    text=f"Current Block: {BLOCKS[current_block_id]['name']}",
    position=(-0.85, 0.45),
    scale=2,
    color=color.black
)

# כוונת קטנה במרכז המסך (Crosshair)
crosshair = Entity(model='quad', color=color.black, scale=0.01, parent=camera.ui)

# 4. הגדרת מחלקת הקוביה (Voxel)
class Voxel(Button):
    def __init__(self, position=(0,0,0), block_id=1):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=BLOCKS[block_id]['texture'],
            color=BLOCKS[block_id]['color'],
            highlight_color=color.cyan
        )
        self.block_id = block_id

    def input(self, key):
        if self.hovered:
            # לחיצה ימנית: בניית הבלוק שנבחר כעת
            if key == 'right mouse down':
                new_pos = self.position + mouse.normal
                Voxel(position=new_pos, block_id=current_block_id)
            
            # לחיצה שמאלית: הריסת הבלוק
            if key == 'left mouse down':
                # בלוק לבה משאיר צליל או אפקט קטן אם תרצה, כרגע פשוט נהרס
                destroy(self)

# 5. יצירת עולם אוטומטי (Terrain Generation) עם רעש פרלין
world_size = 26 # גודל המפה (26x26)
scale_noise = 15.0 # רמת החלקה של הגבעות

for z in range(world_size):
    for x in range(world_size):
        # חישוב גובה הבלוק לפי קואורדינטות X ו-Z בעזרת Perlin Noise
        # הנוסחה מחזירה ערך בין 1- ל-1, נמיר אותו לגובה של בין 0 ל-5 קוביות
        noise_val = pnoise2(x / scale_noise, z / scale_noise, octaves=2)
        height = int((noise_val + 1) * 2.5)
        
        # בניית הבלוקים מהרצפה ועד הגובה שחושב
        for y in range(height + 1):
            # השכבה העליונה תהיה דשא, השכבות מתחתיה יהיו אבן
            if y == height:
                Voxel(position=(x, y, z), block_id=1) # דשא
            else:
                Voxel(position=(x, y, z), block_id=2) # אבן

# 6. הגדרת שמיים ומחזור יום ולילה דינמי
sky = Sky()
sky_time = 0 # משתנה לעקב אחר הזמן ביום

# 7. הגדרת שחקן בגוף ראשון
player = FirstPersonController()
player.y = 10 # נמקם את השחקן גבוה כדי שלא יתקע בתוך הגבעות באתחול

# 8. פונקציית העדכון הכללית של המשחק (רצה בכל פריים)
def update():
    global current_block_id, sky_time
    
    # א) מערכת החלפת בלוקים (מקשים 1-5)
    for i in range(1, 6):
        if held_keys[str(i)]:
            current_block_id = i
            block_text.text = f"Current Block: {BLOCKS[current_block_id]['name']}"
            
    # ב) יציאה מהמשחק עם מקש Esc
    if held_keys['escape']:
        application.quit()
        
    # ג) מחזור יום ולילה: שינוי צבע השמיים בהדרגה
    sky_time += time.dt * 0.05 # מהירות חילוף היום והלילה
    # שימוש בפונקציית סינוס כדי ליצור מעבר חלק בין אור לחושך
    light_value = (math.sin(sky_time) + 1) / 2 # ערך בין 0 ל-1
    sky.color = color.rgb(light_value * 135, light_value * 206, light_value * 235) # מגוון כחול שמשתנה לקראת שחור

# 9. הרצת המשחק
app.run()
