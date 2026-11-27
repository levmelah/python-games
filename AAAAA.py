from ursina import *
import random
import math

app = Ursina()

# הגדרות חלון המשחק
window.title = "Angry Birds Clone - 10 Hardcore Levels"
window.fps_counter.enabled = False

score = 0
current_level = 0
level_transitioning = False
GRAVITY_VAL = -18 

# 10 שלבים מעוצבים עם רמות קושי קיצוניות בסוף
levels = [
    # שלב 1: חימום - מבנה בסיסי
    {"pigs": [(8, -2, 0), (10, -2, 0)], "blocks": [(8, -0.5, 0), (10, -0.5, 0)]},
    # שלב 2: פירמידה קטנה ומגדל מרכזי
    {"pigs": [(9, -2, 0), (13, -2, 0), (11, 1, 0)], "blocks": [(9, -0.5, 0), (13, -0.5, 0), (11, -0.5, 0), (11, 2.5, 0)]},
    # שלב 3: מגדל גבוה - דורש פגיעה בבסיס
    {"pigs": [(12, -2, 0), (12, 1, 0), (12, 4, 0)], "blocks": [(12, -0.5, 0), (12, 2.5, 0), (10, 1, 0), (14, 1, 0)]},
    # שלב 4: מבצר כפול - שני מבנים נפרדים
    {"pigs": [(8, -2, 0), (16, -2, 0), (12, 1, 0)], "blocks": [(8, -0.5, 0), (10, -0.5, 0), (14, -0.5, 0), (16, -0.5, 0), (12, -0.5, 0)]},
    # שלב 5: "החומה הסינית" - חזירים מוגנים מאחורי בלוקים גבוהים
    {"pigs": [(11, -2, 0), (15, -2, 0), (19, -2, 0)], "blocks": [(9, -0.5, 0), (9, 1.0, 0), (13, -0.5, 0), (13, 1.0, 0), (17, -0.5, 0)]},
    # שלב 6: מגדל תלוי ומחסום קדמי (מאלץ ירי קשתי גבוה)
    {"pigs": [(16, -2, 0), (16, 1, 0), (10, -2, 0)], "blocks": [(8, -0.5, 0), (8, 1.5, 0), (8, 3.5, 0), (16, -0.5, 0), (16, 2.5, 0)]},
    # שלב 7: הבוס הגדול המקורי - מבנה ענק, צפוף ומרובה מטרות
    {"pigs": [(10, -2, 0), (14, -2, 0), (18, -2, 0), (12, 1, 0), (16, 1, 0), (14, 4, 0)], "blocks": [(10, -0.5, 0), (14, -0.5, 0), (18, -0.5, 0), (12, 2.5, 0), (16, 2.5, 0), (14, 5.5, 0)]},
    
    # --- שלבים קשים במיוחד (חדשים) ---
    # שלב 8: הפירמידה הכפולה והגשר התלוי
    {
        "pigs": [(10, -2, 0), (16, -2, 0), (13, 1, 0), (13, 4, 0)], 
        "blocks": [(10, -0.5, 0), (16, -0.5, 0), (11.5, 1, 0), (14.5, 1, 0), (13, 2.5, 0), (13, 5.5, 0)]
    },
    # שלב 9: כלוב המגננה (דורש ירי קשתי מדויק מעבר לקיר המגן ב-X=7)
    {
        "pigs": [(12, -2, 0), (18, -2, 0), (15, 2, 0)], 
        "blocks": [(7, -2, 0), (7, -0.5, 0), (7, 1, 0), (12, -0.5, 0), (14, 0.5, 0), (16, 0.5, 0), (18, -0.5, 0)]
    },
    # שלב 10: מגה מבצר הגיהנום - הבוס האולטימטיבי (8 חזירים, 10 בלוקים)
    {
        "pigs": [(9, -2, 0), (13, -2, 0), (17, -2, 0), (21, -2, 0), (11, 1, 0), (15, 1, 0), (19, 1, 0), (15, 4, 0)], 
        "blocks": [(9, -0.5, 0), (13, -0.5, 0), (17, -0.5, 0), (21, -0.5, 0), (11, 2.5, 0), (15, 2.5, 0), (19, 2.5, 0), (13, 4, 0), (17, 4, 0), (15, 5.5, 0)]
    }
]

# סביבת המשחק (הורחבה עוד כדי להתאים לשלבים המסיביים)
ground = Entity(model='cube', scale=(90, 1, 10), position=(20, -4, 0), color=color.green, collider='box')
launcher = Entity(model='sphere', color=color.red, scale=1.5, position=(-15, -2, 0))

pigs = []
blocks = []
birds = []
aim_dots = []
particles = []

# יצירת נקודות כוונת
for i in range(15):
    dot = Entity(model='sphere', color=color.rgba(255, 255, 255, 150), scale=0.25, position=(0, 0, 0))
    aim_dots.append(dot)

# ממשק משתמש
score_text = Text(text='Score: 0', position=(-0.85, 0.45), scale=2, color=color.white)
level_text = Text(text='Level: 1', position=(-0.2, 0.45), scale=2, color=color.cyan)
instructions = Text(text="Left Click = Shoot (Towards Aim Line)\nR = Restart Level", position=(-0.85, 0.35), scale=1.5)

def create_explosion(position):
    for _ in range(12):
        p = Entity(model='sphere', color=color.lime, scale=random.uniform(0.15, 0.35), position=position)
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(5, 12)
        p.velocity = Vec3(math.cos(angle) * speed, random.uniform(2, 10), 0)
        p.lifetime = 0.5
        particles.append(p)

def clear_level():
    global pigs, blocks, birds, particles
    for p in pigs: destroy(p)
    for b in blocks: destroy(b)
    for bird in birds: destroy(bird)
    for part in particles: destroy(part)
    pigs, blocks, birds, particles = [], [], [], []

def load_level(level_index):
    global current_level, level_transitioning
    clear_level()
    current_level = level_index
    level_transitioning = False
    level_text.text = f'Level: {level_index + 1}'
    
    level = levels[level_index]
    for pos in level["pigs"]:
        pig = Entity(model='sphere', color=color.lime, scale=1.2, position=pos, collider='box')
        pigs.append(pig)
    for pos in level["blocks"]:
        block = Entity(model='cube', color=color.orange, scale=(1.4, 1.4, 1.4), position=pos, collider='box')
        blocks.append(block)

load_level(0)

def get_shoot_direction():
    target_x = mouse.x * 35 + camera.x
    target_y = mouse.y * 20 + camera.y
    return Vec3(target_x - launcher.x, target_y - launcher.y, 0).normalized()

def shoot():
    bird = Entity(model='sphere', color=color.red, scale=1.0, position=launcher.position, collider='sphere')
    bird.velocity = get_shoot_direction() * 28
    birds.append(bird)

def input(key):
    if key == 'left mouse down': shoot()
    if key == 'r': load_level(current_level)

def next_level():
    global current_level, level_transitioning
    if level_transitioning: return
    level_transitioning = True
    if current_level + 1 < len(levels):
        load_level(current_level + 1)
    else:
        Text(text='YOU WIN THE GAME!', scale=5, origin=(0, 0), color=color.gold, background=True)

def update_aim_line():
    direction = get_shoot_direction()
    start_vel = direction * 28
    dt = 0.08
    for i, dot in enumerate(aim_dots):
        t = (i + 1) * dt
        pred_x = launcher.x + start_vel.x * t
        pred_y = launcher.y + start_vel.y * t + 0.5 * GRAVITY_VAL * (t ** 2)
        dot.position = Vec3(pred_x, pred_y, 0)

def update():
    global score
    update_aim_line()
    gravity = Vec3(0, GRAVITY_VAL, 0)
    
    for p in particles[:]:
        p.velocity += gravity * time.dt
        p.position += p.velocity * time.dt
        p.lifetime -= time.dt
        p.color = color.rgba(p.color.r*255, p.color.g*255, p.color.b*255, int(p.lifetime * 2 * 255))
        if p.lifetime <= 0:
            destroy(p)
            particles.remove(p)
            
    for bird in birds[:]:
        bird.velocity += gravity * time.dt
        bird.position += bird.velocity * time.dt
        
        for pig in pigs[:]:
            if distance(bird.position, pig.position) < 1.2:
                create_explosion(pig.position)
                destroy(pig)
                if pig in pigs: pigs.remove(pig)
                score += 100
                score_text.text = f'Score: {score}'
                
        for block in blocks:
            if distance(bird.position, block.position) < 1.4:
                block.rotation_z += 300 * time.dt
                block.position += Vec3(0.1, -0.08, 0)
                
        if bird.y < -10:
            destroy(bird)
            if bird in birds: birds.remove(bird)
                
    if len(pigs) == 0 and not level_transitioning:
        next_level()

# עדכון מיקום המצלמה כדי שתוכל לראות את כל המבצר המורחב בשלבים האחרונים
camera.position = (8, 4, -42)
camera.look_at((10, 2, 0))

app.run()
