from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

# אתחול המנוע התלת-ממדי
app = Ursina()

# הגדרת השמים והרצפה במשחק
Sky()
floor = Entity(
    model='plane', 
    scale=(100, 1, 100), 
    color=color.lime, 
    texture='white_cube', 
    collider='box'
)

# רשימה שתשמור את הבלוקים והכדורים לצורך חישובי פיזיקה בסיסיים
blocks = []
balls = []

def create_block_wall():
    """יצירת קיר תלת-ממדי של בלוקים (קוביות)"""
    for x in range(-3, 4):         # רוחב הקיר
        for y in range(1, 6):      # גובה הקיר
            # יצירת קובייה תלת-ממדית
            block = Entity(
                model='cube',
                color=color.rgb(random.randint(150,255), 50, 50),
                position=(x * 1.1, y * 1.1, 15), # מיקום במרחב (X, Y, Z)
                scale=(1, 1, 1),
                collider='box'
            )
            # הוספת תכונות פיזיקה בסיסיות (מהירות וכבידה) קסטום
            block.velocity = Vec3(0, 0, 0)
            block.is_falling = False
            blocks.append(block)

# יצירת הקיר בתחילת המשחק
create_block_wall()

def input(key):
    """זיהוי לחיצות עכבר ומקלדת"""
    if key in ('escape', 'q'):
        application.quit()
        return

    if key == 'left mouse down':
        shot_direction = camera.forward
        # יצירת כדור ירי במיקום של השחקן
        ball = Entity(
            model='sphere',
            color=color.blue,
            position=camera.world_position + shot_direction * 1.2,
            scale=(0.4, 0.4, 0.4),
            collider='sphere'
        )
        # זריקת הכדור קדימה בכיוון שהשחקן מסתכל אליו
        ball.velocity = shot_direction * 35
        balls.append(ball)

def update():
    """לולאת המשחק הראשית - רצה כל פריים ומעדכנת תנועה ופיזיקה"""
    # 1. עדכון תנועת הכדורים שנורו
    for ball in balls:
        ball.position += ball.velocity * time.dt
        # הפעלת כוח משיכה קל על הכדור
        ball.velocity.y -= 9.8 * time.dt
        
        # בדיקת פגיעה של הכדור בבלוקים
        hit_info = ball.intersects()
        if hit_info.hit and hit_info.entity in blocks:
            # הפיכת הבלוק ל"דינמי" שמושפע מהמכה
            hit_block = hit_info.entity
            hit_block.is_falling = True
            # העברת עוצמת המכה מהכדור אל הבלוק
            hit_block.velocity = ball.velocity * 0.3 + Vec3(0, 2, 0)
            
            # העלמת הכדור לאחר הפגיעה
            if ball in balls:
                balls.remove(ball)
                destroy(ball)

    # 2. עדכון הפיזיקה והנפילה של הבלוקים שנפגעו
    for block in blocks:
        if block.is_falling:
            # הזזת הבלוק לפי המהירות שלו
            block.position += block.velocity * time.dt
            # כוח משיכה שמושך את הבלוק לרצפה
            block.velocity.y -= 9.8 * time.dt
            
            # חיכוך קל כדי שהבלוק יעצור בסוף
            block.velocity.x *= 0.98
            block.velocity.z *= 0.98
            
            # עצירה כאשר הבלוק נוגע ברצפה
            if block.y  <= 0.5:
                 block.velocity.x *= 0.98
            block.velocity.z *= 0.98
            
# הגדרת בקר שליטה של שחקן גוף ראשון (תנועה ומבט)
player = FirstPersonController()
player.cursor.visible = True  # הצגת כוונת במרכז המסך

# הרצת המשחק
app.run()
