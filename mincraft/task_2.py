from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math
import random

app = Ursina()

RENDER_DISTANCE = 8
generated_voxels = {}

# שמירת גובה הקרקע
terrain_height = {}

class Voxel(Button):
    def __init__(self, position=(0,0,0), block_color=color.green):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture='white_cube',
            color=block_color,
            highlight_color=color.lime
        )

    def input(self, key):
        if self.hovered:
            if key == 'left mouse down':
                Voxel(position=self.position + mouse.normal)

            if key == 'right mouse down':
                destroy(self)


def make_tree(x, y, z):
    # גזע
    for i in range(3):
        Voxel(
            position=(x, y+i, z),
            block_color=color.brown
        )

    # עלים
    for xx in range(-1,2):
        for zz in range(-1,2):
            for yy in range(2):
                Voxel(
                    position=(x+xx, y+3+yy, z+zz),
                    block_color=color.green
                )


player = FirstPersonController()
player.y = 10


def update():
    px = math.floor(player.x)
    pz = math.floor(player.z)

    for x in range(px-RENDER_DISTANCE, px+RENDER_DISTANCE):
        for z in range(pz-RENDER_DISTANCE, pz+RENDER_DISTANCE):

            if (x,z) not in terrain_height:

                # יוצר גובה אקראי (הרים)
                h = int(
                    3 * math.sin(x*0.25) +
                    3 * math.cos(z*0.25) +
                    random.randint(-1,1)
                )

                terrain_height[(x,z)] = h

                for y in range(h+1):

                    if y == h:
                        c = color.green
                    elif y > h-3:
                        c = color.rgb(120,90,50)
                    else:
                        c = color.gray

                    Voxel(
                        position=(x,y,z),
                        block_color=c
                    )

                # יצירת עצים
                if random.random() < 0.06 and h > 1:
                    make_tree(x, h+1, z)


app.run()