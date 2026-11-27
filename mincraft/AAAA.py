from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

class Voxel(Button):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture='white_cube',
            color=color.green,
            highlight_color=color.lime
        )

    def input(self, key):
        if self.hovered:
            if key == 'left mouse down':
                Voxel(position=self.position + mouse.normal)
            if key == 'right mouse down':
                destroy(self)


def input(key):
    if key == 'escape':
        application.quit()

# יצירת הקרקע
for z in range(20):
    for x in range(20):
        Voxel(position=(x, 0, z))

player = FirstPersonController()

Sky()
app.run()