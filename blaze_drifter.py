from ursina import *
from PIL import Image

app = Ursina()

# 1. הגדרות סביבה (שמיים ורצפה)
Sky(color=color.light_gray)
floor = Entity(model='quad', scale=(300, 300), rotation_x=90, color=color.brown, y=-0.5)

# 2. טעינת תמונת המבוך וניתוח הפיקסלים שלה
# ודא שתמונת המבוך שמורה באותה תיקייה תחת השם maze.png
try:
    img = Image.open('maze.png').convert('1')  # הופך את התמונה לשחור-לבן מוחלט
    width, height = img.size
except FileNotFoundError:
    print("שגיאה: לא מצאתי את הקובץ maze.png באותה התיקייה!")
    img = None

walls = []

# 3. סריקת התמונה ובניית הקירות (רץ רק אם התמונה קיימת)
if img:
    # כדי שהמשחק ירוץ חלק עם אלפי קירות, אנחנו משתמשים ב-combine() שמאחד אותם לישות אחת מהירה
    wall_builder = Entity()
    
    for z in range(height):
        for x in range(width):
            pixel = img.getpixel((x, z))
            if pixel == 0:  # פיקסל שחור = קיר במבוך
                # יוצר קוביית קיר קטנה במיקום המתאים
                Entity(model='cube', color=color.green, position=(x, 0, height - z), scale=(1, 2, 1), parent=wall_builder)
    
    # איחוד כל הקירות למניעת תקיעות במשחק (Optimization)
    wall_builder.combine(auto_destroy=True)
    walls.append(wall_builder)

# 4. יצירת השחקן (הקובייה האדומה)
# המיקום (2, 0, height - 2) מציב אותו קרוב לאחת הכניסות
player = Entity(model='cube', color=color.red, position=(2, 0, height - 2), scale=(0.6, 0.6, 0.6))

# 5. מצלמה שעוקבת אחרי השחקן מלמעלה
camera.parent = player
camera.position = (0, 25, -15)  # מוגבהת יותר בגלל שהמבוך ענק
camera.rotation_x = 60

# 6. לולאת העדכון של המשחק
def update():
    speed = 8 * time.dt  # מהירות מעט גבוהה יותר למבוך הגדול
    old_pos = Vec3(player.position)

    # תנועת השחקן
    if held_keys['a'] or held_keys['left arrow']:
        player.x -= speed
    if held_keys['d'] or held_keys['right arrow']:
        player.x += speed
    if held_keys['w'] or held_keys['up arrow']:
        player.z += speed
    if held_keys['s'] or held_keys['down arrow']:
        player.z -= speed

    # מנגנון התנגשות בקירות המאוחדים
    for wall in walls:
        if player.intersects(wall).hit:
            player.position = old_pos
            break

app.run()
