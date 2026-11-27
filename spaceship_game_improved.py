import tkinter as tk
import random
import math

# Constants
WIDTH = 800
HEIGHT = 600
FPS = 60
PLAYER_SIZE = 15
ENEMY_SIZE = 12
PROJECTILE_SIZE = 4
POWER_UP_SIZE = 10

class SpaceshipGameImproved:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Space Invaders - Enhanced Edition")
        self.root.resizable(False, False)
        
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#000011")
        self.canvas.pack()
        
        self._draw_stars()
        self._reset_game()
        self._create_ui()
        
        # Bindings
        self.root.bind("<KeyPress-a>", lambda e: self._move_player(-12, 0))
        self.root.bind("<KeyPress-d>", lambda e: self._move_player(12, 0))
        self.root.bind("<KeyPress-Left>", lambda e: self._move_player(-12, 0))
        self.root.bind("<KeyPress-Right>", lambda e: self._move_player(12, 0))
        self.root.bind("<space>", self._shoot)
        self.root.bind("<q>", self._use_super)
        self.root.bind("<r>", self._restart_game)
        
        self._game_loop()
        self.root.mainloop()
    
    def _draw_stars(self):
        """Draw background stars for space effect"""
        for _ in range(150):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(1, 3)
            color = random.choice(["#ffffff", "#f0f8ff", "#e6f2ff"])
            self.canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=color, outline=""
            )
    
    def _reset_game(self):
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT - 50
        self.player_health = 100
        self.player_max_health = 100
        self.super_energy = 0
        self.super_max_energy = 100
        self.score = 0
        self.wave = 1
        self.enemies = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.power_ups = []
        self.particles = []
        self.game_over = False
        self.spawn_timer = 0
        self.rapid_fire_timer = 0
        self.shield_timer = 0
        self.combo = 0
        self.combo_timer = 0
        
        self._spawn_enemies()
    
    def _create_ui(self):
        self.health_text = self.canvas.create_text(
            20, 20, text=f"Shield: {self.player_health}/{self.player_max_health}",
            fill="#00ff00", font=("Courier", 14, "bold"), anchor="w"
        )
        self.super_text = self.canvas.create_text(
            20, 45, text=f"Laser: {int(self.super_energy)}/{self.super_max_energy}",
            fill="#ffff00", font=("Courier", 14, "bold"), anchor="w"
        )
        self.score_text = self.canvas.create_text(
            20, 70, text=f"Score: {self.score}",
            fill="#00ffff", font=("Courier", 14, "bold"), anchor="w"
        )
        self.wave_text = self.canvas.create_text(
            WIDTH - 20, 20, text=f"Wave: {self.wave}",
            fill="#ff00ff", font=("Courier", 14, "bold"), anchor="e"
        )
        self.combo_text = self.canvas.create_text(
            WIDTH - 20, 45, text=f"Combo: {self.combo}x",
            fill="#ff6600", font=("Courier", 14, "bold"), anchor="e"
        )
        self.help_text = self.canvas.create_text(
            WIDTH // 2, HEIGHT - 20,
            text="A/D or ← → = Move | Space = Shoot | Q = Laser | R = Restart",
            fill="#00ff00", font=("Courier", 11)
        )
    
    def _update_ui(self):
        self.canvas.itemconfig(self.health_text, text=f"Shield: {self.player_health}/{self.player_max_health}")
        self.canvas.itemconfig(self.super_text, text=f"Laser: {int(self.super_energy)}/{self.super_max_energy}")
        self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
        self.canvas.itemconfig(self.wave_text, text=f"Wave: {self.wave}")
        combo_color = "#ff6600" if self.combo < 5 else ("#ffaa00" if self.combo < 10 else "#ff0000")
        self.canvas.itemconfig(self.combo_text, text=f"Combo: {self.combo}x", fill=combo_color)
    
    def _draw_player(self):
        # Remove old player
        if hasattr(self, 'player_id'):
            self.canvas.delete(self.player_id)
        if hasattr(self, 'player_flame'):
            self.canvas.delete(self.player_flame)
        if hasattr(self, 'player_shield'):
            self.canvas.delete(self.player_shield)
        
        # Draw shield if active
        if self.shield_timer > 0:
            shield_color = "#00ffff" if self.shield_timer % 10 > 5 else "#0088ff"
            self.player_shield = self.canvas.create_oval(
                self.player_x - PLAYER_SIZE - 8, self.player_y - PLAYER_SIZE - 8,
                self.player_x + PLAYER_SIZE + 8, self.player_y + PLAYER_SIZE + 8,
                outline=shield_color, width=2
            )
        
        # Draw spaceship (triangle pointing up)
        size = PLAYER_SIZE
        self.player_id = self.canvas.create_polygon(
            self.player_x, self.player_y - size,
            self.player_x - size, self.player_y + size,
            self.player_x + size, self.player_y + size,
            fill="#00ff00", outline="#00aa00", width=2
        )
        
        # Draw engine flame (more intense if rapid fire)
        flame_length = random.randint(10, 18) if self.rapid_fire_timer > 0 else random.randint(8, 15)
        flame_offset = random.randint(-3, 3)
        self.player_flame = self.canvas.create_polygon(
            self.player_x - 2, self.player_y + size,
            self.player_x + 2, self.player_y + size,
            self.player_x + flame_offset, self.player_y + size + flame_length,
            fill="#ff6600", outline="#ff3300"
        )
    
    def _spawn_enemies(self):
        num_enemies = 3 + self.wave
        for _ in range(num_enemies):
            x = random.randint(ENEMY_SIZE + 20, WIDTH - ENEMY_SIZE - 20)
            y = random.randint(-100, -20)
            
            # Different enemy types based on wave
            enemy_type = "normal"
            health = 20 + self.wave * 5
            speed = 1.5 + self.wave * 0.2
            
            if random.random() < self.wave * 0.08 and self.wave > 2:
                enemy_type = "tough"
                health = 40 + self.wave * 10
            elif random.random() < self.wave * 0.05 and self.wave > 3:
                enemy_type = "fast"
                speed = 3 + self.wave * 0.3
            
            if self.wave >= 5 and len(self.enemies) == num_enemies - 1 and random.random() < 0.3:
                enemy_type = "boss"
                health = 60 + self.wave * 15
                speed = 1.2 + self.wave * 0.1
            
            self.enemies.append({
                "x": x,
                "y": y,
                "health": health,
                "max_health": health,
                "type": enemy_type,
                "speed": speed,
                "shoot_timer": random.randint(30, 100),
                "id": None
            })
    
    def _move_player(self, dx, dy):
        if self.game_over:
            return
        
        new_x = self.player_x + dx
        
        if PLAYER_SIZE + 5 < new_x < WIDTH - PLAYER_SIZE - 5:
            self.player_x = new_x
    
    def _shoot(self, event=None):
        if self.game_over:
            return
        
        # Rapid fire mode
        if self.rapid_fire_timer > 0:
            for offset in [-6, -2, 2, 6]:
                self.projectiles.append({
                    "x": self.player_x + offset,
                    "y": self.player_y - PLAYER_SIZE,
                    "vx": offset * 0.15,
                    "vy": -14,
                    "id": None
                })
        else:
            # Normal fire
            for offset in [-4, 0, 4]:
                self.projectiles.append({
                    "x": self.player_x + offset,
                    "y": self.player_y - PLAYER_SIZE,
                    "vx": offset * 0.1,
                    "vy": -12,
                    "id": None
                })
    
    def _draw_explosion(self, x, y, size=30):
        """Draw explosion with particles"""
        explosion = self.canvas.create_oval(
            x - size, y - size, x + size, y + size,
            fill="#f59e0b", outline="#ff6600", width=2
        )
        self.root.after(150, lambda: self.canvas.delete(explosion))
        
        # Create particles
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            self.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": 30,
                "id": None
            })
    
    def _use_super(self, event=None):
        if self.game_over or self.super_energy < self.super_max_energy:
            return
        
        self.super_energy = 0
        
        # Laser: damage all enemies in column
        laser_x = self.player_x
        laser = self.canvas.create_line(
            laser_x, self.player_y, laser_x, 0,
            fill="#ffff00", width=4
        )
        self.root.after(100, lambda: self.canvas.delete(laser))
        
        damage = 50
        hit_count = 0
        for enemy in self.enemies[:]:
            if abs(enemy["x"] - laser_x) < ENEMY_SIZE + 10:
                enemy["health"] -= damage
                if enemy["health"] <= 0:
                    self.enemies.remove(enemy)
                    self.score += 200 + self.combo * 50
                    self.combo += 1
                    hit_count += 1
                    self._draw_explosion(enemy["x"], enemy["y"], size=40)
        
        self._update_ui()
    
    def _apply_power_up(self, power_type):
        """Apply power-up effects"""
        if power_type == "health":
            self.player_health = min(self.player_max_health, self.player_health + 30)
            self.score += 25
        elif power_type == "rapid":
            self.rapid_fire_timer = 300  # 5 seconds at 60 FPS
            self.score += 50
        elif power_type == "shield":
            self.shield_timer = 360  # 6 seconds at 60 FPS
            self.score += 50
    
    def _game_loop(self):
        if not self.game_over:
            # Update timers
            if self.rapid_fire_timer > 0:
                self.rapid_fire_timer -= 1
            if self.shield_timer > 0:
                self.shield_timer -= 1
            if self.combo_timer > 0:
                self.combo_timer -= 1
            else:
                self.combo = 0
            
            # Update particles
            for particle in self.particles[:]:
                particle["x"] += particle["vx"]
                particle["y"] += particle["vy"]
                particle["vy"] += 0.2  # gravity
                particle["life"] -= 1
                
                if particle["id"]:
                    self.canvas.delete(particle["id"])
                
                if particle["life"] <= 0:
                    self.particles.remove(particle)
                else:
                    particle["id"] = self.canvas.create_oval(
                        particle["x"] - 2, particle["y"] - 2,
                        particle["x"] + 2, particle["y"] + 2,
                        fill="#ff6600", outline=""
                    )
            
            # Update power-ups
            for power_up in self.power_ups[:]:
                power_up["y"] += 2
                if power_up["id"]:
                    self.canvas.delete(power_up["id"])
                
                if power_up["y"] > HEIGHT:
                    self.power_ups.remove(power_up)
                    continue
                
                color = {"health": "#00ff00", "rapid": "#ffff00", "shield": "#00ffff"}[power_up["type"]]
                power_up["id"] = self.canvas.create_rectangle(
                    power_up["x"] - POWER_UP_SIZE, power_up["y"] - POWER_UP_SIZE,
                    power_up["x"] + POWER_UP_SIZE, power_up["y"] + POWER_UP_SIZE,
                    fill=color, outline="#ffffff", width=1
                )
                
                # Check collision with player
                if abs(power_up["x"] - self.player_x) < POWER_UP_SIZE + PLAYER_SIZE and \
                   abs(power_up["y"] - self.player_y) < POWER_UP_SIZE + PLAYER_SIZE:
                    self._apply_power_up(power_up["type"])
                    self.power_ups.remove(power_up)
            
            # Update enemies
            for enemy in self.enemies[:]:
                # Move downward
                enemy["y"] += enemy["speed"]
                
                # Shoot occasionally
                enemy["shoot_timer"] -= 1
                if enemy["shoot_timer"] <= 0:
                    shoot_speed = 8 if enemy["type"] == "fast" else 6
                    self.enemy_projectiles.append({
                        "x": enemy["x"],
                        "y": enemy["y"],
                        "vx": 0,
                        "vy": shoot_speed,
                        "id": None
                    })
                    enemy["shoot_timer"] = random.randint(40, 100)
                
                # Delete old enemy visual
                if enemy["id"]:
                    self.canvas.delete(enemy["id"])
                
                # Draw enemy (inverted triangle) with type variation
                size = ENEMY_SIZE
                if enemy["type"] == "tough":
                    color = "#ff00ff"
                    outline = "#aa00aa"
                    size = ENEMY_SIZE + 3
                elif enemy["type"] == "fast":
                    color = "#ffaa00"
                    outline = "#ff6600"
                elif enemy["type"] == "boss":
                    color = "#ff0000"
                    outline = "#ffffff"
                    size = ENEMY_SIZE + 5
                else:
                    color = "#ff0000"
                    outline = "#aa0000"
                
                enemy["id"] = self.canvas.create_polygon(
                    enemy["x"], enemy["y"] + size,
                    enemy["x"] - size, enemy["y"] - size,
                    enemy["x"] + size, enemy["y"] - size,
                    fill=color, outline=outline, width=2
                )
                
                # Draw health bar for tough/boss enemies
                if enemy["type"] in ("tough", "boss"):
                    health_pct = enemy["health"] / enemy["max_health"]
                    self.canvas.create_rectangle(
                        enemy["x"] - size - 2, enemy["y"] - size - 8,
                        enemy["x"] - size - 2 + (size * 2 + 4) * health_pct, enemy["y"] - size - 4,
                        fill="#00ff00", outline="#00aa00"
                    )
                
                # Check if enemy reached bottom (lose life)
                if enemy["y"] > HEIGHT:
                    self.enemies.remove(enemy)
                    self.player_health -= 10
                    self._update_ui()
                    if self.player_health <= 0:
                        self._game_over_screen()
                        break
            
            # Update player projectiles
            for projectile in self.projectiles[:]:
                projectile["x"] += projectile["vx"]
                projectile["y"] += projectile["vy"]
                
                # Delete old projectile visual
                if projectile["id"]:
                    self.canvas.delete(projectile["id"])
                
                # Remove if out of bounds
                if projectile["y"] < 0:
                    self.projectiles.remove(projectile)
                    continue
                
                # Draw projectile
                projectile["id"] = self.canvas.create_rectangle(
                    projectile["x"] - 2, projectile["y"] - 6,
                    projectile["x"] + 2, projectile["y"] + 6,
                    fill="#00ff00", outline="#00aa00", width=1
                )
                
                # Check collision with enemies
                hit = False
                for enemy in self.enemies[:]:
                    dist = math.sqrt((projectile["x"] - enemy["x"])**2 + (projectile["y"] - enemy["y"])**2)
                    if dist < ENEMY_SIZE + PROJECTILE_SIZE:
                        enemy["health"] -= 15
                        self.super_energy = min(self.super_max_energy, self.super_energy + 10)
                        self.combo_timer = 120  # Reset combo timer
                        hit = True
                        
                        if enemy["health"] <= 0:
                            self.enemies.remove(enemy)
                            base_score = {"normal": 50, "tough": 150, "fast": 100, "boss": 500}.get(enemy["type"], 50)
                            self.score += base_score + self.combo * 25
                            self.combo += 1
                            self._draw_explosion(enemy["x"], enemy["y"])
                            
                            # Drop power-ups randomly
                            if random.random() < 0.15:
                                power_type = random.choice(["health", "rapid", "shield"])
                                self.power_ups.append({
                                    "x": enemy["x"],
                                    "y": enemy["y"],
                                    "type": power_type,
                                    "id": None
                                })
                
                if hit and projectile in self.projectiles:
                    self.projectiles.remove(projectile)
            
            # Update enemy projectiles
            for enemy_proj in self.enemy_projectiles[:]:
                enemy_proj["x"] += enemy_proj["vx"]
                enemy_proj["y"] += enemy_proj["vy"]
                
                if enemy_proj["id"]:
                    self.canvas.delete(enemy_proj["id"])
                
                if enemy_proj["y"] > HEIGHT:
                    self.enemy_projectiles.remove(enemy_proj)
                    continue
                
                enemy_proj["id"] = self.canvas.create_oval(
                    enemy_proj["x"] - 3, enemy_proj["y"] - 3,
                    enemy_proj["x"] + 3, enemy_proj["y"] + 3,
                    fill="#ff6600", outline="#ff3300"
                )
                
                # Check collision with player
                dist = math.sqrt((enemy_proj["x"] - self.player_x)**2 + (enemy_proj["y"] - self.player_y)**2)
                if dist < PLAYER_SIZE + 3:
                    damage = 5
                    if self.shield_timer > 0:
                        damage = 0
                        self.shield_timer -= 10
                    else:
                        self.player_health -= damage
                    self.enemy_projectiles.remove(enemy_proj)
                    self._update_ui()
                    if self.player_health <= 0:
                        self._game_over_screen()
                        break
            
            # Draw player
            self._draw_player()
            
            # Check if all enemies defeated
            if len(self.enemies) == 0:
                self.wave += 1
                self._spawn_enemies()
            
            self._update_ui()
        
        self.root.after(1000 // FPS, self._game_loop)
    
    def _game_over_screen(self):
        self.game_over = True
        self.canvas.create_rectangle(
            WIDTH // 2 - 150, HEIGHT // 2 - 80,
            WIDTH // 2 + 150, HEIGHT // 2 + 80,
            fill="#000011", outline="#ff0000", width=3
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 30,
            text="SHIP DESTROYED!", fill="#ff0000",
            font=("Courier", 28, "bold")
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 5,
            text=f"Final Score: {self.score}", fill="#00ff00",
            font=("Courier", 18)
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 35,
            text=f"Wave reached: {self.wave}", fill="#ffff00",
            font=("Courier", 16)
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 65,
            text="Press R to restart", fill="#00ff00",
            font=("Courier", 14)
        )
    
    def _restart_game(self, event=None):
        self.canvas.delete("all")
        self._draw_stars()
        self._reset_game()
        self._create_ui()


if __name__ == "__main__":
    SpaceshipGameImproved()
