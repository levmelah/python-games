import pygame
import sys

# Initialize pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Level Devil Ultimate - Bridge Cheat Edition")
clock = pygame.time.Clock()
FPS = 60

# Colors (Fallback shapes color scheme)
WHITE = (255, 255, 255)
DARK_GRAY = (44, 62, 80)
BLUE = (52, 152, 219)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
GOLD = (241, 196, 15)
PURPLE = (155, 89, 182)

# Safe Image Loader with automatic geometric fallback block
images_loaded = True
try:
    player_img = pygame.image.load("player.png").convert_alpha()
    platform_img = pygame.image.load("platform.png").convert_alpha()
    trap_img = pygame.image.load("trap.png").convert_alpha()
    door_img = pygame.image.load("door.png").convert_alpha()
    
    player_img = pygame.transform.scale(player_img, (40, 40))
    door_img = pygame.transform.scale(door_img, (50, 80))
except Exception:
    images_loaded = False
    print("Note: Asset images missing. Running smoothly with default colored blocks layout.")

# Player mechanics configuration 
player_width = 40
player_height = 40
player_x = 80
player_y = 450
player_vel_x = 0
player_vel_y = 0
player_speed = 5
gravity = 0.8
jump_strength = -17
is_grounded = False

# Progression system states
current_level = 1
max_levels = 5
deaths = 0

# Dynamic Trap Tracking Metrics
trap_triggered = False
trap_velocity = 0
level_4_revealed = False
door_escaped = False

# מנגנון הגשר הסודי לשלב 1
bridge_active = False
secret_bridge = pygame.Rect(450, 450, 250, 30) # גשר סגול שיחבר בין הפלטפורמות

def load_level(level_num):
    """Loads map configurations dynamically with structural hidden triggers"""
    global platforms, goal_rect, trap_triggered, trap_velocity, player_x, player_y, player_vel_x, player_vel_y, level_4_revealed, door_escaped, bridge_active
    
    player_x = 80
    player_y = 450
    player_vel_x = 0
    player_vel_y = 0
    trap_triggered = False
    trap_velocity = 0
    level_4_revealed = False
    door_escaped = False
    bridge_active = False # איפוס הגשר בכל טעינת שלב

    if level_num == 1:
        goal_rect = pygame.Rect(700, 300, 50, 80)
        platforms = [
            pygame.Rect(50, 520, 200, 30),
            pygame.Rect(300, 450, 150, 30),
            pygame.Rect(500, 380, 150, 30),  # הבלוק שייעלם
            pygame.Rect(680, 380, 100, 30)
        ]
    elif level_num == 2:
        goal_rect = pygame.Rect(700, 420, 50, 80)
        platforms = [
            pygame.Rect(50, 520, 200, 30),
            pygame.Rect(300, 500, 120, 30),
            pygame.Rect(480, 600, 100, 30),  
            pygame.Rect(650, 500, 120, 30)
        ]
    elif level_num == 3:
        goal_rect = pygame.Rect(700, 420, 50, 80)
        platforms = [
            pygame.Rect(50, 520, 250, 30),
            pygame.Rect(350, 520, 150, 30),
            pygame.Rect(550, 500, 200, 30),
            pygame.Rect(650, 100, 120, 30)   
        ]
    elif level_num == 4:
        goal_rect = pygame.Rect(710, 440, 50, 80)
        platforms = [
            pygame.Rect(50, 520, 300, 30),
            pygame.Rect(350, -100, 100, 30), 
            pygame.Rect(450, 520, 320, 30)
        ]
    elif level_num == 5:
        goal_rect = pygame.Rect(500, 440, 50, 80) 
        platforms = [
            pygame.Rect(50, 520, 400, 30),   
            pygame.Rect(500, 520, 260, 30)   
        ]

# Build world structure instance
load_level(current_level)

# Typography settings
font = pygame.font.SysFont("Arial", 28, bold=True)

# Main gameplay update execution frame loop
running = True
while running:
    # 1. Capture Player Control Registries
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_UP, pygame.K_w] and is_grounded:
                player_vel_y = jump_strength
            if event.key == pygame.K_1 and current_level == 1:
                bridge_active = True

    keys = pygame.key.get_pressed()
    player_vel_x = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player_vel_x = -player_speed
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player_vel_x = player_speed

    # 2. Kinematics Core Acceleration Updates
    player_vel_y += gravity
    
    player_x += player_vel_x
    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
    
    for i, plat in enumerate(platforms):
        if current_level == 1 and i == 2 and trap_triggered:
            continue
        if player_rect.colliderect(plat):
            if player_vel_x > 0:
                player_x = plat.left - player_width
            elif player_vel_x < 0:
                player_x = plat.right

    if current_level == 1 and bridge_active:
        if player_rect.colliderect(secret_bridge):
            if player_vel_x > 0:
                player_x = secret_bridge.left - player_width
            elif player_vel_x < 0:
                player_x = secret_bridge.right

    player_y += player_vel_y
    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
    is_grounded = False
    
    for i, plat in enumerate(platforms):
        if current_level == 1 and i == 2 and trap_triggered:
            continue
        if player_rect.colliderect(plat):
            if player_vel_y > 0: 
                player_y = plat.top - player_height
                player_vel_y = 0
                is_grounded = True
            elif player_vel_y < 0: 
                player_y = plat.bottom
                player_vel_y = 0

    if current_level == 1 and bridge_active:
        if player_rect.colliderect(secret_bridge):
            if player_vel_y > 0:
                player_y = secret_bridge.top - player_height
                player_vel_y = 0
                is_grounded = True
            elif player_vel_y < 0:
                player_y = secret_bridge.bottom
                player_vel_y = 0

    # 3. Troll Trap Sequence Triggers
    if current_level == 1:
        if player_x > 450 and not trap_triggered:
            trap_triggered = True

    elif current_level == 2 and len(platforms) > 2:
        if player_x > 380 and not trap_triggered:
            trap_triggered = True
        if trap_triggered and platforms[2].y > 480:
            platforms[2].y -= 6

    elif current_level == 3 and len(platforms) > 3:
        if player_x > 580 and not trap_triggered:
            trap_triggered = True
        if trap_triggered:
            trap_velocity += 0.5
            platforms[3].y += trap_velocity

    elif current_level == 4 and len(platforms) > 1:
        if player_x > 280 and not trap_triggered:
            trap_triggered = True
            level_4_revealed = True
            platforms[1].x = 350
            platforms[1].y = 490  

    elif current_level == 5:
        if player_x > 340 and not door_escaped:
            door_escaped = True
        if door_escaped and goal_rect.x < 700:
            goal_rect.x += 8  

    # 4. Out of Bounds & Hazard Collision Checks
    if player_y > SCREEN_HEIGHT or player_y < -100:
        deaths += 1
        load_level(current_level)

    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
    
    if current_level == 2 and len(platforms) > 2 and player_rect.colliderect(platforms[2]):
        deaths += 1
        load_level(current_level)
    elif current_level == 3 and len(platforms) > 3 and player_rect.colliderect(platforms[3]):
        deaths += 1
        load_level(current_level)
    elif current_level == 4 and level_4_revealed and len(platforms) > 1 and player_rect.colliderect(platforms[1]):
        deaths += 1
        load_level(current_level)

    # Goal collision processing
    if player_rect.colliderect(goal_rect):
        if current_level < max_levels:
            current_level += 1
            load_level(current_level)
        else:
            screen.fill(DARK_GRAY)
            win_text = font.render(f"VICTORY! Total Trolls Survived. Total Deaths: {deaths}", True, WHITE)
            screen.blit(win_text, (SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(5000)
            running = False
            continue

    # 5. Visual Rendering Framework Pipelines
    screen.fill(DARK_GRAY)

    if images_loaded:
        screen.blit(door_img, (goal_rect.x, goal_rect.y))
    else:
        pygame.draw.rect(screen, GOLD, goal_rect)

    if current_level == 1 and bridge_active:
        pygame.draw.rect(screen, PURPLE, secret_bridge)

    for i, plat in enumerate(platforms):
        if current_level == 1 and i == 2 and trap_triggered:
            continue
            
        is_trap = (current_level == 1 and i == 2) or (current_level == 2 and i == 2) or (current_level == 3 and i == 3) or (current_level == 4 and i == 1)
        
        if current_level == 4 and i == 1 and not level_4_revealed:
            continue

        if images_loaded:
            current_img = trap_img if is_trap else platform_img
            scaled_plat_img = pygame.transform.scale(current_img, (plat.width, plat.height))
            screen.blit(scaled_plat_img, (plat.x, plat.y))
        else:
            color = RED if is_trap else GREEN
            pygame.draw.rect(screen, color, plat)

    if images_loaded:
        screen.blit(player_img, (player_x, player_y))
    else:
        pygame.draw.rect(screen, BLUE, player_rect)

    ui_text = font.render(f"Level: {current_level}/{max_levels}   Deaths: {deaths}", True, WHITE)
    screen.blit(ui_text, (20, 20))
    
    if current_level == 1 and not bridge_active:
        cheat_text = font.render("Press '1' for a Bridge!", True, WHITE)
        screen.blit(cheat_text, (SCREEN_WIDTH // 2 - 120, 20))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
