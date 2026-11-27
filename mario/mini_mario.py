import sys
import pygame
import math

# הגדרות מסך וקצב פריימים
WIDTH, HEIGHT = 1000, 600
FPS = 60

# פלטת צבעים
SKY = (125, 200, 255)
GROUND = (110, 80, 40)
GRASS = (70, 170, 70)
BRICK = (170, 95, 55)
PIPE_GREEN = (40, 160, 65)
PIPE_DARK = (25, 120, 45)
WHITE = (255, 255, 255)
BLACK = (25, 25, 25)
YELLOW = (255, 225, 40)
CLOUD_COLOR = (240, 245, 255)


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 34, 50)
        self.vx = 0
        self.vy = 0
        self.speed = 4.2
        self.jump_force = 12.5
        self.gravity = 0.62
        self.max_fall = 12
        self.on_ground = False
        self.coins = 0
        self.lives = 3
        self.invuln_timer = 0

    def input(self):
        keys = pygame.key.get_pressed()
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = self.speed
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vy = -self.jump_force
            self.on_ground = False

    def apply_gravity(self):
        self.vy += self.gravity
        if self.vy > self.max_fall:
            self.vy = self.max_fall

    def move_and_collide(self, solids):
        self.rect.x += int(self.vx)
        for tile in solids:
            if self.rect.colliderect(tile):
                if self.vx > 0:
                    self.rect.right = tile.left
                elif self.vx < 0:
                    self.rect.left = tile.right

        self.rect.y += int(self.vy)
        self.on_ground = False
        for tile in solids:
            if self.rect.colliderect(tile):
                if self.vy > 0:
                    self.rect.bottom = tile.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = tile.bottom
                    self.vy = 0

    def draw(self, screen, cam_x):
        x = self.rect.x - cam_x
        y = self.rect.y

        # אפקט הבהוב בזמן חסינות (לאחר פגיעה)
        if self.invuln_timer > 0 and (self.invuln_timer // 5) % 2 == 0:
            return

        # ציור דמות מריו וקטורית בסיסית
        pygame.draw.rect(screen, (200, 35, 35), (x + 5, y + 6, 24, 16), border_radius=4)  # חולצה
        pygame.draw.rect(screen, (45, 85, 220), (x + 5, y + 24, 24, 26), border_radius=5) # אוברול
        pygame.draw.circle(screen, (245, 210, 170), (x + 17, y + 20), 9)                  # פנים
        pygame.draw.rect(screen, (180, 25, 25), (x + 2, y + 8, 30, 5), border_radius=3)   # כובע
        pygame.draw.rect(screen, (120, 70, 20), (x + 5, y + 40, 8, 9), border_radius=2)   # נעל שמאל
        pygame.draw.rect(screen, (120, 70, 20), (x + 21, y + 40, 8, 9), border_radius=2)  # נעל ימין


class Enemy:
    def __init__(self, x, y, left_limit, right_limit):
        self.rect = pygame.Rect(x, y, 34, 30)
        self.vx = -1.4
        self.left_limit = left_limit
        self.right_limit = right_limit
        self.alive = True
        self.death_timer = 0  # טיימר להצגת האויב מעוך

    def update(self):
        if not self.alive:
            if self.death_timer > 0:
                self.death_timer -= 1
            return
        
        self.rect.x += int(self.vx)
        if self.rect.left <= self.left_limit or self.rect.right >= self.right_limit:
            self.vx *= -1

    def draw(self, screen, cam_x):
        x = self.rect.x - cam_x
        y = self.rect.y
        
        if not self.alive:
            if self.death_timer > 0:
                # ציור אויב מעוך (אפקט קפיצה מוצלח)
                pygame.draw.ellipse(screen, (150, 90, 35), (x, y + 20, 34, 10))
            return

        # ציור אויב חי (פטרייה/גומבה)
        pygame.draw.ellipse(screen, (150, 90, 35), (x, y, 34, 24))
        pygame.draw.circle(screen, WHITE, (x + 10, y + 10), 3)
        pygame.draw.circle(screen, WHITE, (x + 24, y + 10), 3)
        pygame.draw.circle(screen, BLACK, (x + 10, y + 10), 1)
        pygame.draw.circle(screen, BLACK, (x + 24, y + 10), 1)
        pygame.draw.rect(screen, (100, 60, 20), (x + 2, y + 22, 12, 6))
        pygame.draw.rect(screen, (100, 60, 20), (x + 20, y + 22, 12, 6))


class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.t = 0
        self.collected = False

    def update(self):
        self.t += 0.15

    def draw(self, screen, cam_x):
        if self.collected:
            return
        x = self.rect.x - cam_x
        # ריחוף קל למעלה ולמטה
        y_offset = int(3 * math.sin(self.t))
        y = self.rect.y + y_offset
        
        # אפקט סיבוב חזותי בעזרת רוחב משתנה
        animated_width = int(20 * abs(math.cos(self.t)))
        if animated_width < 2: 
            animated_width = 2
        
        center_x = x + 10
        draw_x = center_x - animated_width // 2
        
        pygame.draw.ellipse(screen, (245, 200, 30), (draw_x, y, animated_width, 20))
        if animated_width > 6:
            pygame.draw.ellipse(screen, YELLOW, (draw_x + 2, y + 3, animated_width - 4, 14), 1)


class Cloud:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.speed = speed

    def update(self):
        self.x -= self.speed
        if self.x < -150:
            self.x = 2500  # חזרה לקצה רמת המשחק

    def draw(self, screen, cam_x):
        cx = self.x - cam_x * 0.5  # אפקט פארלקס (רקע זז לאט יותר)
        pygame.draw.circle(screen, CLOUD_COLOR, (int(cx), self.y), 25)
        pygame.draw.circle(screen, CLOUD_COLOR, (int(cx + 20), self.y - 10), 30)
        pygame.draw.circle(screen, CLOUD_COLOR, (int(cx + 50), self.y), 25)
        pygame.draw.circle(screen, CLOUD_COLOR, (int(cx + 25), self.y + 10), 20)


def make_level():
    solids = []
    ground_y = 540

    solids.append(pygame.Rect(-200, ground_y, 2600, 80))

    solids.extend([
        pygame.Rect(220, 460, 120, 20),
        pygame.Rect(420, 400, 120, 20),
        pygame.Rect(620, 340, 140, 20),
        pygame.Rect(850, 450, 180, 20),
        pygame.Rect(1170, 390, 140, 20),
        pygame.Rect(1400, 330, 140, 20),
        pygame.Rect(1620, 270, 140, 20),
        pygame.Rect(1840, 420, 180, 20),
    ])

    pipes = [
        pygame.Rect(520, 470, 70, 70),
        pygame.Rect(980, 430, 70, 110),
        pygame.Rect(1520, 410, 70, 130),
    ]
    solids.extend(pipes)

    enemies = [
        Enemy(720, 510, 640, 940),
        Enemy(1260, 360, 1170, 1310),
        Enemy(1880, 390, 1840, 2020),
    ]

    coins = [
        Coin(250, 420), Coin(290, 420),
        Coin(450, 360), Coin(490, 360),
        Coin(655, 300), Coin(700, 300),
        Coin(910, 410), Coin(960, 410),
        Coin(1210, 350), Coin(1450, 290),
        Coin(1670, 230), Coin(1710, 230),
        Coin(1900, 380), Coin(1950, 380),
    ]

    clouds = [
        Cloud(200, 100, 0.3),
        Cloud(600, 80, 0.2),
        Cloud(1100, 120, 0.4),
        Cloud(1600, 70, 0.25),
        Cloud(2100, 110, 0.35)
    ]

    flag_x = 2200
    flag_rect = pygame.Rect(flag_x, 250, 18, 290)

    return solids, pipes, enemies, coins, clouds, flag_rect, ground_y


def draw_world(screen, solids, pipes, ground_y, cam_x):
    screen.fill(SKY)

    # ציור עננים (יבוצע מתוך הלולאה הראשית עם אפקט פארלקס)
    pygame.draw.rect(screen, GRASS, (0, ground_y - 10, WIDTH, 10))
    pygame.draw.rect(screen, GROUND, (0, ground_y, WIDTH, HEIGHT - ground_y))

    for tile in solids:
        if tile.y >= ground_y:
            continue
        x = tile.x - cam_x
        y = tile.y
        color = BRICK
        pygame.draw.rect(screen, color, (x, y, tile.width, tile.height), border_radius=3)
        pygame.draw.line(screen, (130, 70, 35), (x, y + tile.height // 2), (x + tile.width, y + tile.height // 2), 2)

    for p in pipes:
        x = p.x - cam_x
        y = p.y
        pygame.draw.rect(screen, PIPE_GREEN, (x, y, p.width, p.height))
        pygame.draw.rect(screen, PIPE_DARK, (x + 5, y + 5, p.width - 10, p.height - 5))
        pygame.draw.rect(screen, PIPE_GREEN, (x - 8, y - 12, p.width + 16, 16))


def draw_flag(screen, flag_rect, cam_x):
    x = flag_rect.x - cam_x
    pygame.draw.rect(screen, (220, 220, 220), (x, flag_rect.y, flag_rect.width, flag_rect.height))
    pygame.draw.polygon(
        screen,
        (255, 70, 70),
        [(x + flag_rect.width, flag_rect.y + 20), (x + flag_rect.width + 65, flag_rect.y + 45), (x + flag_rect.width, flag_rect.y + 70)],
    )


def draw_hud(screen, font, player, win):
    pygame.draw.rect(screen, (15, 15, 20), (0, 0, WIDTH, 42))
    txt = font.render(f"COINS: {player.coins}   LIVES: {player.lives}", True, WHITE)
    screen.blit(txt, (18, 9))
    
    if win:
        t2 = font.render("YOU WIN! Press R to restart", True, YELLOW)
        screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, 9))
    elif player.lives <= 0:
        t3 = font.render("GAME OVER! Press R to restart", True, (255, 50, 50))
        screen.blit(t3, (WIDTH // 2 - t3.get_width() // 2, 9))


def reset_game():
    player = Player(80, 470)
    solids, pipes, enemies, coins, clouds, flag_rect, ground_y = make_level()
    return player, solids, pipes, enemies, coins, clouds, flag_rect, ground_y


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mini Mario - Enhanced Pygame")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 26)

    player, solids, pipes, enemies, coins, clouds, flag_rect, ground_y = reset_game()

    world_width = 2400
    win = False

    while True:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and (win or player.lives <= 0):
                player, solids, pipes, enemies, coins, clouds, flag_rect, ground_y = reset_game()
                win = False

        # עדכון העננים (זזים גם כשהמשחק נגמר)
        for cloud in clouds:
            cloud.update()

        if not win and player.lives > 0:
            player.input()
            player.apply_gravity()
            player.move_and_collide(solids)

            # לא לצאת מגבולות העולם
            if player.rect.left < 0:
                player.rect.left = 0
            if player.rect.right > world_width:
                player.rect.right = world_width

            if player.invuln_timer > 0:
                player.invuln_timer -= 1

            # איסוף מטבעות
            for coin in coins:
                coin.update()
                if not coin.collected and player.rect.colliderect(coin.rect):
                    coin.collected = True
                    player.coins += 1

            # אויבים: קפיצה עליהם מלמעלה מועכת אותם, נגיעה מהצד מורידה חיים
            for enemy in enemies:
                enemy.update()
                if not enemy.alive:
                    continue
                if player.rect.colliderect(enemy.rect):
                    if player.vy > 0 and player.rect.bottom - enemy.rect.top < 18:
                        enemy.alive = False
                        enemy.death_timer = 30
                        player.vy = -9
                    elif player.invuln_timer == 0:
                        player.lives -= 1
                        player.invuln_timer = 90

            # הגעה לדגל = ניצחון
            if player.rect.colliderect(flag_rect):
                win = True

            # נפילה מהמסך = מאבדים חיים וחוזרים להתחלה
            if player.rect.top > HEIGHT + 120:
                player.lives -= 1
                player.rect.topleft = (80, 470)
                player.vx = 0
                player.vy = 0
                player.invuln_timer = 90

        # מצלמה שעוקבת אחרי השחקן
        cam_x = int(player.rect.centerx - WIDTH * 0.35)
        cam_x = max(0, min(cam_x, world_width - WIDTH))

        # ציור
        draw_world(screen, solids, pipes, ground_y, cam_x)
        for cloud in clouds:
            cloud.draw(screen, cam_x)
        for coin in coins:
            coin.draw(screen, cam_x)
        for enemy in enemies:
            enemy.draw(screen, cam_x)
        draw_flag(screen, flag_rect, cam_x)
        player.draw(screen, cam_x)
        draw_hud(screen, font, player, win)

        pygame.display.flip()


if __name__ == "__main__":
    main()
