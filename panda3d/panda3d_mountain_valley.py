from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import AmbientLight
from panda3d.core import CardMaker
from panda3d.core import DirectionalLight
from panda3d.core import LColor
from panda3d.core import Vec3
import math
import random


class MountainValleyScene(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()
        self.setBackgroundColor(0.63, 0.82, 0.98, 1)
        self.camera_angle = 0.0
        self.camera_radius = 24

        self._setup_lights()
        self._create_ground()
        self._create_trees()
        self._create_statue_of_liberty()

        self.taskMgr.add(self.update_scene, 'update_scene')

    def _setup_lights(self):
        ambient = AmbientLight('ambient')
        ambient.setColor((0.63, 0.65, 0.7, 1))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

        sun = DirectionalLight('sun')
        sun.setColor((0.98, 0.96, 0.9, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(-35, -48, 0)
        self.render.setLight(sun_np)

    def _create_ground(self):
        ground_maker = CardMaker('ground')
        ground_maker.setFrame(-20, 20, -20, 20)
        ground = self.render.attachNewNode(ground_maker.generate())
        ground.setP(-90)
        ground.setPos(0, 0, 0)
        ground.setColor(LColor(0.3, 0.64, 0.24, 1))

    def _create_trees(self):
        for _ in range(70):
            x_pos = random.uniform(-14, 14)
            y_pos = random.uniform(-14, 14)
            if abs(x_pos) < 4 and abs(y_pos) < 4:
                continue

            trunk = self.loader.loadModel('models/box')
            trunk.reparentTo(self.render)
            trunk_height = random.uniform(0.9, 1.7)
            trunk.setScale(0.22, 0.22, trunk_height)
            trunk.setPos(x_pos, y_pos, trunk_height)
            trunk.setColor(LColor(0.42, 0.29, 0.14, 1))

            crown = self.loader.loadModel('models/box')
            crown.reparentTo(self.render)
            crown_height = random.uniform(1.0, 2.1)
            crown_width = random.uniform(0.7, 1.25)
            crown.setScale(crown_width, crown_width, crown_height)
            crown.setPos(x_pos, y_pos, trunk_height * 2 + 0.6)
            crown.setColor(LColor(0.15, random.uniform(0.4, 0.68), 0.14, 1))

    def _create_statue_of_liberty(self):
        statue_color = LColor(0.43, 0.72, 0.62, 1)
        dark_statue = LColor(0.35, 0.62, 0.53, 1)
        pedestal_dark = LColor(0.48, 0.49, 0.54, 1)
        flame_core = LColor(1.0, 0.88, 0.3, 1)
        flame_outer = LColor(1.0, 0.52, 0.12, 1)
        voxel_target = 0.14

        statue_root = self.render.attachNewNode('statue_of_liberty')
        cube_template = self.loader.loadModel('models/box')
        cube_template.setTextureOff(1)

        def add_box(name, scale, pos, color, hpr=(0, 0, 0), parent=statue_root):
            group = parent.attachNewNode(name)
            group.setPos(*pos)
            group.setHpr(*hpr)

            x_count = max(1, int(math.ceil(scale[0] / voxel_target)))
            y_count = max(1, int(math.ceil(scale[1] / voxel_target)))
            z_count = max(1, int(math.ceil(scale[2] / voxel_target)))

            voxel_scale = (
                scale[0] / x_count,
                scale[1] / y_count,
                scale[2] / z_count,
            )

            x_start = -scale[0] * 0.5 + voxel_scale[0] * 0.5
            y_start = -scale[1] * 0.5 + voxel_scale[1] * 0.5
            z_start = -scale[2] * 0.5 + voxel_scale[2] * 0.5

            for ix in range(x_count):
                x_pos = x_start + ix * voxel_scale[0]
                for iy in range(y_count):
                    y_pos = y_start + iy * voxel_scale[1]
                    for iz in range(z_count):
                        z_pos = z_start + iz * voxel_scale[2]
                        voxel = cube_template.copyTo(group)
                        voxel.setScale(
                            voxel_scale[0] * 0.92,
                            voxel_scale[1] * 0.92,
                            voxel_scale[2] * 0.92,
                        )
                        voxel.setPos(x_pos, y_pos, z_pos)
                        voxel.setColor(color)

            return group

        add_box('pedestal_base', (3.0, 3.0, 0.7), (0, 0, 0.7), LColor(0.62, 0.62, 0.66, 1))
        add_box('pedestal_mid', (2.55, 2.55, 0.45), (0, 0, 1.5), pedestal_dark)
        add_box('pedestal_top', (2.05, 2.05, 0.65), (0, 0, 2.3), LColor(0.56, 0.57, 0.61, 1))
        add_box('platform', (1.55, 1.55, 0.28), (0, 0, 3.18), pedestal_dark)

        add_box('robe_core', (0.82, 0.72, 2.35), (0, 0, 5.42), statue_color)
        add_box('robe_front', (0.46, 0.34, 2.05), (0, 0.52, 5.22), dark_statue)
        add_box('robe_left_fold', (0.28, 0.4, 2.22), (-0.72, 0.02, 5.35), statue_color, hpr=(0, 0, 8))
        add_box('robe_right_fold', (0.28, 0.4, 2.4), (0.72, -0.02, 5.52), statue_color, hpr=(0, 0, -8))
        add_box('left_foot', (0.23, 0.3, 0.18), (-0.28, 0.2, 3.5), dark_statue)
        add_box('right_foot', (0.23, 0.3, 0.18), (0.2, 0.14, 3.5), dark_statue)

        add_box('torso', (0.74, 0.58, 1.0), (0, 0.04, 6.85), statue_color)
        add_box('shoulders', (0.95, 0.48, 0.18), (0, 0.02, 7.45), dark_statue)
        add_box('neck', (0.16, 0.16, 0.2), (0, 0.0, 7.78), dark_statue)
        add_box('head', (0.52, 0.5, 0.62), (0.02, 0.0, 8.22), statue_color)
        add_box('nose', (0.06, 0.12, 0.09), (0.18, 0.3, 8.2), dark_statue)

        add_box('crown_band', (0.72, 0.72, 0.1), (0.02, 0, 8.58), dark_statue)
        for spike_x, spike_y, spike_h, roll in [
            (0.0, 0.62, 8.96, 0),
            (0.42, 0.42, 8.9, -22),
            (0.62, 0.0, 8.8, -42),
            (0.42, -0.42, 8.72, -60),
            (0.0, -0.62, 8.68, -82),
            (-0.42, -0.42, 8.72, 60),
            (-0.62, 0.0, 8.8, 42),
            (-0.42, 0.42, 8.9, 22),
        ]:
            add_box('crown_spike', (0.06, 0.06, 0.42), (spike_x, spike_y, spike_h), dark_statue, hpr=(0, -12, roll))

        add_box('left_upper_arm', (0.2, 0.2, 0.92), (-0.68, 0.16, 6.82), statue_color, hpr=(0, 0, 48))
        add_box('left_forearm', (0.18, 0.18, 0.78), (-1.08, 0.36, 6.18), statue_color, hpr=(10, 0, 72))
        add_box('tablet', (0.62, 0.18, 0.84), (-1.1, 0.68, 6.16), pedestal_dark, hpr=(14, 10, 16))

        add_box('right_upper_arm', (0.2, 0.2, 1.02), (0.64, 0.06, 7.12), statue_color, hpr=(0, 0, -32))
        add_box('right_forearm', (0.16, 0.16, 1.18), (1.0, 0.02, 8.18), statue_color, hpr=(6, -8, -6))
        add_box('torch_handle', (0.11, 0.11, 0.72), (1.2, 0.0, 9.08), pedestal_dark)
        add_box('torch_cup', (0.24, 0.24, 0.12), (1.2, 0.0, 9.54), pedestal_dark)
        add_box('torch_flame_outer', (0.24, 0.24, 0.42), (1.2, 0.0, 9.92), flame_outer, hpr=(0, 0, 18))
        add_box('torch_flame_core', (0.12, 0.12, 0.3), (1.2, 0.0, 9.96), flame_core, hpr=(0, 0, -10))

        statue_root.flattenStrong()

    def update_scene(self, task):
        dt = globalClock.getDt()
        self.camera_angle += dt * 10

        radians = math.radians(self.camera_angle)
        camera_x = math.cos(radians) * self.camera_radius
        camera_y = math.sin(radians) * self.camera_radius

        self.camera.setPos(camera_x, camera_y, 11)
        self.camera.lookAt(Vec3(0, 0, 2.8))
        return task.cont


if __name__ == '__main__':
    app = MountainValleyScene()
    app.run()