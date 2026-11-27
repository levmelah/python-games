import bpy

# 1. מחיקת כל האובייקטים הקיימים כדי להתחיל דף חלק
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 2. יצירת המבנה המרכזי של הטירה (קובייה מתוחה)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2))
main_body = bpy.context.active_object
main_body.name = "Castle_Main"
main_body.scale = (6, 6, 4)

# 3. פונקציה לבניית מגדל שמירה עם גג מחודד
def create_tower(x, y, name):
    # גוף המגדל (גליל)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=8, location=(x, y, 4))
    tower = bpy.context.active_object
    tower.name = f"Tower_{name}"
    
    # גג המגדל (קונוס שפיצי)
    bpy.ops.mesh.primitive_cone_add(radius1=1, depth=3, location=(x, y, 9.5))
    roof = bpy.context.active_object
    roof.name = f"Roof_{name}"

# 4. בניית 4 מגדלי פינה
create_tower(-3, -3, "Front_Left")
create_tower(3, -3, "Front_Right")
create_tower(-3, 3, "Back_Left")
create_tower(3, 3, "Back_Right")

# 5. בניית המגדל המרכזי הגבוה (הצריח הראשי של סינדרלה)
bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=12, location=(0, 0, 6))
center_tower = bpy.context.active_object
center_tower.name = "Center_Tower"

bpy.ops.mesh.primitive_cone_add(radius1=1.5, depth=5, location=(0, 0, 14.5))
center_roof = bpy.context.active_object
center_roof.name = "Center_Roof"

print("הטירה נבנתה בהצלחה!")