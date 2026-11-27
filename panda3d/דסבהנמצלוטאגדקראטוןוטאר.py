from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import AmbientLight, DirectionalLight, LColor
from panda3d.core import PerlinNoise2

# רעש פרלין מובנה של panda3d (במקום ספריית noise, שלא מותקנת)
_perlin = PerlinNoise2(1, 1, 256, 1)

def pnoise2(x, y):
    # 0.7 - כדי שהטווח יהיה כמו של pnoise2 מספריית noise
    return _perlin.noise(x, y) * 0.7
import random
import json
import os

CHUNK_SIZE = 8
RENDER_DISTANCE = 2
SCALE = 35.0

WATER_LEVEL = 3

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_save.json")


class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.disableMouse()
        self.camera.setPos(0, -40, 15)

        self.setup_lights()

        self.chunks = {}

        # טען עולם אם קיים
        self.load_world()

        self.taskMgr.add(self.update, "update")

    # 💡 אור
    def setup_lights(self):
        ambient = AmbientLight("ambient")
        ambient.setColor(LColor(0.6, 0.6, 0.6, 1))
        self.render.setLight(self.render.attachNewNode(ambient))

        sun = DirectionalLight("sun")
        sun.setColor(LColor(1, 1, 1, 1))
        sun_node = self.render.attachNewNode(sun)
        sun_node.setHpr(45, -60, 0)
        self.render.setLight(sun_node)

    # 🧱 בלוק
    def create_block(self, x, y, z, color):
        block = self.loader.loadModel("models/box")
        block.reparentTo(self.render)
        block.setPos(x, y, z)
        block.setScale(1)
        block.setColor(*color)
        return block

    # 🌄 גובה שטח
    def get_height(self, x, y):
        h = pnoise2(x / SCALE, y / SCALE)
        return int((h + 1) * 6)

    # 🪨 מערות (noise שני)
    def is_cave(self, x, y, z):
        c = pnoise2((x + 100) / 12.0, (y + 100) / 12.0)
        return c > 0.35 and z < 4

    # 🌳 יצירת עץ
    def generate_tree(self, x, y, z, blocks):
        # גזע
        height = random.randint(3, 5)
        for i in range(height):
            blocks.append(self.create_block(x, y, z + i, (0.55, 0.27, 0.07, 1)))

        # עלים
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for dz in range(2, 4):
                    if abs(dx) + abs(dy) < 3:
                        blocks.append(self.create_block(
                            x + dx, y + dy, z + height + dz,
                            (0.1, 0.7, 0.1, 1)
                        ))

    # 🌍 chunk
    def generate_chunk(self, cx, cy):
        blocks = []

        start_x = cx * CHUNK_SIZE
        start_y = cy * CHUNK_SIZE

        for x in range(CHUNK_SIZE):
            for y in range(CHUNK_SIZE):

                wx = start_x + x
                wy = start_y + y

                height = self.get_height(wx, wy)

                tree_chance = random.random() < 0.08

                for z in range(height):

                    # 🪨 מערות
                    if self.is_cave(wx, wy, z):
                        continue

                    # אדמה
                    color = (0.25, 0.8, 0.25, 1)

                    if z < 2:
                        color = (0.4, 0.3, 0.2, 1)
                    elif z > 6:
                        color = (0.7, 0.7, 0.7, 1)

                    blocks.append(self.create_block(wx, wy, z, color))

                # 🌊 מים
                for z in range(height, WATER_LEVEL):
                    blocks.append(self.create_block(wx, wy, z, (0.2, 0.4, 0.9, 0.6)))

                # 🌳 עצים
                if tree_chance and height > WATER_LEVEL:
                    self.generate_tree(wx, wy, height, blocks)

        self.chunks[(cx, cy)] = blocks

    # ❌ מחיקה
    def remove_chunk(self, cx, cy):
        if (cx, cy) in self.chunks:
            for b in self.chunks[(cx, cy)]:
                b.removeNode()
            del self.chunks[(cx, cy)]

    # 🌍 chunks מסביב לשחקן
    def update_chunks(self):
        cx = int(self.camera.getX() // CHUNK_SIZE)
        cy = int(self.camera.getY() // CHUNK_SIZE)

        needed = set()

        for x in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            for y in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
                chunk = (cx + x, cy + y)
                needed.add(chunk)

                if chunk not in self.chunks:
                    self.generate_chunk(chunk[0], chunk[1])

        for chunk in list(self.chunks.keys()):
            if chunk not in needed:
                self.remove_chunk(chunk[0], chunk[1])

    # 💾 שמירה
    def save_world(self):
        data = []

        for chunk, blocks in self.chunks.items():
            for b in blocks:
                pos = b.getPos()
                color = b.getColor()

                data.append({
                    "x": pos.x,
                    "y": pos.y,
                    "z": pos.z,
                    "r": color[0],
                    "g": color[1],
                    "b": color[2],
                    "a": color[3],
                })

        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)

        print("World saved!")

    # 📂 טעינה
    def load_world(self):
        if not os.path.exists(SAVE_FILE):
            return

        with open(SAVE_FILE, "r") as f:
            data = json.load(f)

        for b in data:
            self.create_block(
                b["x"], b["y"], b["z"],
                (b["r"], b["g"], b["b"], b["a"])
            )

        print("World loaded!")

    # 🎮 update
    def update(self, task):
        dt = globalClock.getDt()
        speed = 12 * dt

        if self.mouseWatcherNode.is_button_down("w"):
            self.camera.setY(self.camera, speed)
        if self.mouseWatcherNode.is_button_down("s"):
            self.camera.setY(self.camera, -speed)
        if self.mouseWatcherNode.is_button_down("a"):
            self.camera.setX(self.camera, -speed)
        if self.mouseWatcherNode.is_button_down("d"):
            self.camera.setX(self.camera, speed)

        # שמירה עם S
        if self.mouseWatcherNode.is_button_down("lshift"):
            self.save_world()

        self.update_chunks()

        return task.cont


game = Game()
game.run()