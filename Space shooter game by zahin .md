import pygame
import random
import math
import sys
import os

pygame.init()

# Screen setup - try fullscreen first, then windowed
try:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_info = pygame.display.Info()
    SCREEN_WIDTH = screen_info.current_w
    SCREEN_HEIGHT = screen_info.current_h
    FULLSCREEN = True
except:
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    FULLSCREEN = False

# Game name and icon
pygame.display.set_caption("Space Shooter Game by Zahin")

# Create game icon
icon = pygame.Surface((32, 32), pygame.SRCALPHA)
pygame.draw.circle(icon, (100, 100, 255), (16, 16), 15)
pygame.draw.polygon(icon, (255, 255, 0), [(16, 5), (10, 25), (22, 25)])
pygame.draw.circle(icon, (255, 0, 0), (16, 12), 3)
pygame.display.set_icon(icon)

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
DARK_BLUE = (10, 10, 40)

# Calculate scaled sizes based on screen size
SCALE_FACTOR = min(SCREEN_WIDTH / 800, SCREEN_HEIGHT / 600)
FONT_SIZE_TITLE = int(64 * SCALE_FACTOR)
FONT_SIZE_LARGE = int(48 * SCALE_FACTOR)
FONT_SIZE_MEDIUM = int(35 * SCALE_FACTOR)
FONT_SIZE_SMALL = int(28 * SCALE_FACTOR)
BUTTON_WIDTH = int(200 * SCALE_FACTOR)
BUTTON_HEIGHT = int(60 * SCALE_FACTOR)

# Background - create space background
bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT * 2))  # Double height for scrolling
bg.fill(DARK_BLUE)
# Add stars to background
for _ in range(300):
    x = random.randint(0, SCREEN_WIDTH)
    y = random.randint(0, SCREEN_HEIGHT * 2)
    radius = random.randint(1, 3)
    brightness = random.randint(150, 255)
    pygame.draw.circle(bg, (brightness, brightness, brightness), (x, y), radius)

bg_y = 0

# Fonts
try:
    title_font = pygame.font.Font("freesansbold.ttf", FONT_SIZE_TITLE)
    menu_font = pygame.font.Font("freesansbold.ttf", FONT_SIZE_LARGE)
    font = pygame.font.Font("freesansbold.ttf", FONT_SIZE_MEDIUM)
    font2 = pygame.font.Font("freesansbold.ttf", FONT_SIZE_TITLE)
    small_font = pygame.font.Font("freesansbold.ttf", FONT_SIZE_SMALL)
except:
    title_font = pygame.font.SysFont('arial', FONT_SIZE_TITLE, bold=True)
    menu_font = pygame.font.SysFont('arial', FONT_SIZE_LARGE, bold=True)
    font = pygame.font.SysFont('arial', FONT_SIZE_MEDIUM)
    font2 = pygame.font.SysFont('arial', FONT_SIZE_TITLE, bold=True)
    small_font = pygame.font.SysFont('arial', FONT_SIZE_SMALL)

# Score
score = 0
high_score = 0

# Difficulty settings
difficulty = "normal"
difficulty_speeds = {
    "easy": 5 * SCALE_FACTOR,
    "normal": 10 * SCALE_FACTOR,
    "hard": 20 * SCALE_FACTOR
}

# Bullet system
MAX_BULLETS = 10  # Maximum 10 bullets in the list
bullets_available = 0  # Start with 0 bullets
bullet_list = []  # List to track active bullets

def score_f(x, y):
    score_show = font.render("Score: " + str(score), True, WHITE)
    screen.blit(score_show, (x, y))

def high_score_f(x, y):
    high_score_show = font.render("High Score: " + str(high_score), True, YELLOW)
    screen.blit(high_score_show, (x, y))

def draw_bullet_list():
    """Draw the bullet list UI showing available bullets"""
    bullet_text = font.render("Bullets:", True, WHITE)
    screen.blit(bullet_text, (SCREEN_WIDTH - 200, 10))
    
    # Draw bullet slots
    slot_width = 30
    slot_height = 15
    slot_margin = 5
    
    for i in range(MAX_BULLETS):
        slot_x = SCREEN_WIDTH - 190 + (i % 5) * (slot_width + slot_margin)
        slot_y = 50 + (i // 5) * (slot_height + slot_margin)
        
        # Draw empty slot
        pygame.draw.rect(screen, (50, 50, 50), (slot_x, slot_y, slot_width, slot_height))
        pygame.draw.rect(screen, WHITE, (slot_x, slot_y, slot_width, slot_height), 1)
        
        # Fill slot if bullet available
        if i < bullets_available:
            pygame.draw.rect(screen, YELLOW, (slot_x + 2, slot_y + 2, slot_width - 4, slot_height - 4))

# Game over text with buttons
def game_over():
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2
    
    # Game over text
    gameover_text = font2.render("GAME OVER", True, RED)
    text_rect = gameover_text.get_rect(center=(center_x, center_y - 100))
    screen.blit(gameover_text, text_rect)
    
    # Score display
    final_score = font.render(f"Final Score: {score}", True, YELLOW)
    final_rect = final_score.get_rect(center=(center_x, center_y - 50))
    screen.blit(final_score, final_rect)
    
    # Create buttons
    button_width = BUTTON_WIDTH
    button_height = BUTTON_HEIGHT - 10
    restart_button = pygame.Rect(center_x - button_width - 20, center_y + 20, button_width, button_height)
    menu_button = pygame.Rect(center_x + 20, center_y + 20, button_width, button_height)
    
    # Draw buttons
    pygame.draw.rect(screen, (0, 200, 0), restart_button)
    pygame.draw.rect(screen, (0, 0, 200), menu_button)
    pygame.draw.rect(screen, GREEN, restart_button, 3)
    pygame.draw.rect(screen, CYAN, menu_button, 3)
    
    # Button text - centered
    restart_text = small_font.render("RESTART", True, WHITE)
    menu_text = small_font.render("MAIN MENU", True, WHITE)
    
    restart_text_rect = restart_text.get_rect(center=restart_button.center)
    menu_text_rect = menu_text.get_rect(center=menu_button.center)
    
    screen.blit(restart_text, restart_text_rect)
    screen.blit(menu_text, menu_text_rect)
    
    return restart_button, menu_button

# How to Play screen
def show_how_to_play():
    how_to_active = True
    back_button = pygame.Rect(SCREEN_WIDTH // 2 - BUTTON_WIDTH // 2, SCREEN_HEIGHT - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
    
    while how_to_active:
        screen.fill(BLACK)
        # Draw background
        screen.blit(bg, (0, 0))
        screen.blit(bg, (0, -SCREEN_HEIGHT))
        
        # Title
        title = title_font.render("HOW TO PLAY", True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title, title_rect)
        
        # Instructions
        instructions = [
            "CONTROLS:",
            "← → Arrow Keys : Move Spaceship",
            "SPACE : Shoot Laser",
            "ESC : Pause/Return to Menu",
            "",
            "BULLET SYSTEM:",
            "• Start with 0 bullets",
            "• Collect green power-ups to get 5 bullets",
            "• Maximum 10 bullets can be stored",
            "• Each shot uses 1 bullet",
            "",
            "GAME OBJECTIVE:",
            "• Shoot enemy spaceships to score points",
            "• Avoid collisions with enemies",
            "• Collect power-ups for bullets",
            "• Survive as long as possible!",
            "",
            "DIFFICULTY LEVELS:",
            "• EASY: Slow enemies",
            "• NORMAL: Balanced gameplay", 
            "• HARD: Fast and challenging"
        ]
        
        y_pos = 150
        for instruction in instructions:
            if ":" in instruction and not instruction.startswith(" "):
                # Main categories
                text = font.render(instruction, True, YELLOW)
            elif instruction.startswith("•"):
                # Bullet points
                text = small_font.render(instruction, True, GREEN)
            elif instruction == "":
                # Empty line
                text = small_font.render(instruction, True, WHITE)
                y_pos += 20
                continue
            else:
                # Regular text
                text = small_font.render(instruction, True, WHITE)
            
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            screen.blit(text, text_rect)
            y_pos += 40
        
        # Mobile instructions
        if SCREEN_WIDTH < 1000:  # Assuming mobile if screen width is small
            mobile_text = small_font.render("Mobile: Use touch controls", True, ORANGE)
            mobile_rect = mobile_text.get_rect(center=(SCREEN_WIDTH // 2, y_pos + 20))
            screen.blit(mobile_text, mobile_rect)
        
        # Back button
        pygame.draw.rect(screen, (0, 0, 180), back_button)
        pygame.draw.rect(screen, BLUE, back_button, 3)
        back_text = small_font.render("BACK", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_button.center)
        screen.blit(back_text, back_text_rect)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_b:
                    return

# Difficulty selection screen
def show_difficulty_menu():
    global difficulty
    diff_active = True
    
    center_x = SCREEN_WIDTH // 2
    button_width = BUTTON_WIDTH
    button_height = BUTTON_HEIGHT
    
    # Difficulty buttons
    easy_button = pygame.Rect(center_x - button_width // 2, 200 * SCALE_FACTOR, button_width, button_height)
    normal_button = pygame.Rect(center_x - button_width // 2, 300 * SCALE_FACTOR, button_width, button_height)
    hard_button = pygame.Rect(center_x - button_width // 2, 400 * SCALE_FACTOR, button_width, button_height)
    back_button = pygame.Rect(center_x - button_width // 2, 500 * SCALE_FACTOR, button_width, button_height)
    
    while diff_active:
        screen.fill(BLACK)
        # Draw background
        screen.blit(bg, (0, 0))
        screen.blit(bg, (0, -SCREEN_HEIGHT))
        
        # Title
        title_text = title_font.render("SELECT DIFFICULTY", True, CYAN)
        title_rect = title_text.get_rect(center=(center_x, 100 * SCALE_FACTOR))
        screen.blit(title_text, title_rect)
        
        # Draw buttons
        buttons = [
            (easy_button, (0, 180, 0), GREEN, "EASY"),
            (normal_button, (180, 180, 0), YELLOW, "NORMAL"),
            (hard_button, (180, 0, 0), RED, "HARD"),
            (back_button, (0, 0, 180), BLUE, "BACK")
        ]
        
        for button, color, border_color, text in buttons:
            pygame.draw.rect(screen, color, button)
            pygame.draw.rect(screen, border_color, button, 3)
            
            button_text = small_font.render(text, True, WHITE)
            text_rect = button_text.get_rect(center=button.center)
            screen.blit(button_text, text_rect)
        
        # Draw current selection
        current_button = None
        if difficulty == "easy":
            current_button = easy_button
        elif difficulty == "normal":
            current_button = normal_button
        elif difficulty == "hard":
            current_button = hard_button
        
        if current_button:
            pygame.draw.rect(screen, CYAN, current_button, 6)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                
                if easy_button.collidepoint(mouse_pos):
                    difficulty = "easy"
                    return "start"
                if normal_button.collidepoint(mouse_pos):
                    difficulty = "normal"
                    return "start"
                if hard_button.collidepoint(mouse_pos):
                    difficulty = "hard"
                    return "start"
                if back_button.collidepoint(mouse_pos):
                    return "menu"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1 or event.key == pygame.K_e:
                    difficulty = "easy"
                    return "start"
                elif event.key == pygame.K_2 or event.key == pygame.K_n:
                    difficulty = "normal"
                    return "start"
                elif event.key == pygame.K_3 or event.key == pygame.K_h:
                    difficulty = "hard"
                    return "start"
                elif event.key == pygame.K_ESCAPE:
                    return "menu"
    
    return "menu"

# Start menu
def show_menu():
    menu_active = True
    
    center_x = SCREEN_WIDTH // 2
    button_width = BUTTON_WIDTH
    button_height = BUTTON_HEIGHT
    
    # Menu buttons
    play_button = pygame.Rect(center_x - button_width // 2, 250 * SCALE_FACTOR, button_width, button_height)
    how_to_button = pygame.Rect(center_x - button_width // 2, 330 * SCALE_FACTOR, button_width, button_height)
    quit_button = pygame.Rect(center_x - button_width // 2, 410 * SCALE_FACTOR, button_width, button_height)
    
    while menu_active:
        screen.fill(BLACK)
        # Draw background
        screen.blit(bg, (0, 0))
        screen.blit(bg, (0, -SCREEN_HEIGHT))
        
        # Title
        title_text = title_font.render("SPACE SHOOTER", True, (100, 200, 255))
        title_rect = title_text.get_rect(center=(center_x, 100 * SCALE_FACTOR))
        screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle = font.render("by Zahin", True, YELLOW)
        subtitle_rect = subtitle.get_rect(center=(center_x, 160 * SCALE_FACTOR))
        screen.blit(subtitle, subtitle_rect)
        
        # Draw buttons
        buttons = [
            (play_button, (0, 150, 0), GREEN, "PLAY GAME"),
            (how_to_button, (150, 150, 0), YELLOW, "HOW TO PLAY"),
            (quit_button, (150, 0, 0), RED, "QUIT")
        ]
        
        for button, color, border_color, text in buttons:
            pygame.draw.rect(screen, color, button)
            pygame.draw.rect(screen, border_color, button, 4)
            
            button_text = small_font.render(text, True, WHITE)
            text_rect = button_text.get_rect(center=button.center)
            screen.blit(button_text, text_rect)
        
        # Draw current difficulty
        diff_text = small_font.render(f"Difficulty: {difficulty.upper()}", True, YELLOW)
        diff_rect = diff_text.get_rect(center=(center_x, 500 * SCALE_FACTOR))
        screen.blit(diff_text, diff_rect)
        
        # Fullscreen info
        screen_mode = "FULLSCREEN" if FULLSCREEN else "WINDOWED"
        mode_text = small_font.render(f"Mode: {screen_mode} (F11 to toggle)", True, CYAN)
        mode_rect = mode_text.get_rect(center=(center_x, 530 * SCALE_FACTOR))
        screen.blit(mode_text, mode_rect)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                
                if play_button.collidepoint(mouse_pos):
                    return "difficulty"
                if how_to_button.collidepoint(mouse_pos):
                    show_how_to_play()
                if quit_button.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    return "difficulty"
                elif event.key == pygame.K_h:
                    show_how_to_play()
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_F11:
                    toggle_fullscreen()
    
    return "quit"

def toggle_fullscreen():
    global screen, SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN, bg, SCALE_FACTOR
    global FONT_SIZE_TITLE, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL
    global BUTTON_WIDTH, BUTTON_HEIGHT
    
    pygame.display.quit()
    pygame.display.init()
    
    if FULLSCREEN:
        screen = pygame.display.set_mode((800, 600))
        SCREEN_WIDTH = 800
        SCREEN_HEIGHT = 600
        FULLSCREEN = False
    else:
        try:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            screen_info = pygame.display.Info()
            SCREEN_WIDTH = screen_info.current_w
            SCREEN_HEIGHT = screen_info.current_h
            FULLSCREEN = True
        except:
            screen = pygame.display.set_mode((800, 600))
            SCREEN_WIDTH = 800
            SCREEN_HEIGHT = 600
            FULLSCREEN = False
    
    # Recalculate scale factors
    SCALE_FACTOR = min(SCREEN_WIDTH / 800, SCREEN_HEIGHT / 600)
    FONT_SIZE_TITLE = int(64 * SCALE_FACTOR)
    FONT_SIZE_LARGE = int(48 * SCALE_FACTOR)
    FONT_SIZE_MEDIUM = int(35 * SCALE_FACTOR)
    FONT_SIZE_SMALL = int(28 * SCALE_FACTOR)
    BUTTON_WIDTH = int(200 * SCALE_FACTOR)
    BUTTON_HEIGHT = int(60 * SCALE_FACTOR)
    
    # Recreate background for new size
    bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT * 2))
    bg.fill(DARK_BLUE)
    for _ in range(300):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT * 2)
        radius = random.randint(1, 3)
        brightness = random.randint(150, 255)
        pygame.draw.circle(bg, (brightness, brightness, brightness), (x, y), radius)
    
    # Reinitialize fonts
    try:
        title_font = pygame.font.Font("freesansbold.ttf", FONT_SIZE_TITLE)
        menu_font = pygame.font.Font("freesansbold.ttf", FONT_SIZE_LARGE)
        font = pygame.font.Font("freesansbold.ttf", FONT_SIZE_MEDIUM)
        font2 = pygame.font.Font("freesansbold.ttf", FONT_SIZE_TITLE)
        small_font = pygame.font.Font("freesansbold.ttf", FONT_SIZE_SMALL)
    except:
        title_font = pygame.font.SysFont('arial', FONT_SIZE_TITLE, bold=True)
        menu_font = pygame.font.SysFont('arial', FONT_SIZE_LARGE, bold=True)
        font = pygame.font.SysFont('arial', FONT_SIZE_MEDIUM)
        font2 = pygame.font.SysFont('arial', FONT_SIZE_TITLE, bold=True)
        small_font = pygame.font.SysFont('arial', FONT_SIZE_SMALL)

# Player
player_size = int(64 * SCALE_FACTOR)
player_img = pygame.Surface((player_size, player_size), pygame.SRCALPHA)
# Draw player spaceship scaled
scale = player_size / 64
pygame.draw.polygon(player_img, BLUE, [
    (32*scale, 0), (12*scale, 24*scale), (32*scale, 60*scale), (52*scale, 24*scale)
])
pygame.draw.circle(player_img, CYAN, (32*scale, 20*scale), 8*scale)
pygame.draw.circle(player_img, WHITE, (32*scale, 20*scale), 4*scale)

playerx = SCREEN_WIDTH // 2 - player_size // 2
playery = SCREEN_HEIGHT - 100
playerx_change = 0
player_speed = 8 * SCALE_FACTOR

def player(x, y):
    screen.blit(player_img, (x, y))

# Bullet
bullet_width = int(8 * SCALE_FACTOR)
bullet_height = int(20 * SCALE_FACTOR)
bullet_img = pygame.Surface((bullet_width, bullet_height), pygame.SRCALPHA)
pygame.draw.rect(bullet_img, (255, 255, 0), (2*SCALE_FACTOR, 0, 4*SCALE_FACTOR, 16*SCALE_FACTOR))

bullety_change = 15 * SCALE_FACTOR

def bullet_fire(x, y):
    """Fire a bullet from the given position"""
    global bullets_available
    if bullets_available > 0:
        bullets_available -= 1
        bullet_list.append({
            'x': x + player_size // 2 - bullet_width // 2,
            'y': y + 10,
            'active': True
        })

def update_bullets():
    """Update all active bullets"""
    for bullet in bullet_list[:]:
        if bullet['active']:
            bullet['y'] -= bullety_change
            screen.blit(bullet_img, (bullet['x'], bullet['y']))
            
            # Remove bullet if it goes off screen
            if bullet['y'] <= 0:
                bullet['active'] = False
                bullet_list.remove(bullet)

# Enemies
enemy_img = []
enemyx = []
enemyy = []
enemyx_change = []
enemyy_change = []
num_enemy = 6

def init_enemies():
    global enemy_img, enemyx, enemyy, enemyx_change, enemyy_change
    enemy_img = []
    enemyx = []
    enemyy = []
    enemyx_change = []
    enemyy_change = []
    
    base_speed = difficulty_speeds[difficulty]
    enemy_size = int(64 * SCALE_FACTOR)
    
    for i in range(num_enemy):
        img = pygame.Surface((enemy_size, enemy_size), pygame.SRCALPHA)
        color = random.choice([RED, PURPLE, ORANGE])
        scale = enemy_size / 64
        
        pygame.draw.circle(img, color, (32*scale, 32*scale), 20*scale)
        pygame.draw.circle(img, YELLOW, (20*scale, 20*scale), 6*scale)
        pygame.draw.circle(img, YELLOW, (44*scale, 20*scale), 6*scale)
        
        enemy_img.append(img)
        enemyx.append(random.randint(0, SCREEN_WIDTH - enemy_size))
        enemyy.append(random.randint(50, 150))
        enemyx_change.append(base_speed + random.random() * 2)
        enemyy_change.append(40 * SCALE_FACTOR)

def enemy(x, y, i):
    screen.blit(enemy_img[i], (x, y))

# Explosion effect
explosion_size = int(64 * SCALE_FACTOR)
explosion_img = pygame.Surface((explosion_size, explosion_size), pygame.SRCALPHA)
scale = explosion_size / 64
pygame.draw.circle(explosion_img, (255, 255, 0), (32*scale, 32*scale), 30*scale)
pygame.draw.circle(explosion_img, (255, 150, 0), (32*scale, 32*scale), 22*scale)
pygame.draw.circle(explosion_img, (255, 0, 0), (32*scale, 32*scale), 14*scale)

explosion_timer = 0
explosion_duration = 10
explosion_x = 0
explosion_y = 0

def explosion(x, y):
    screen.blit(explosion_img, (x, y))

# Stars for background
stars = []
for _ in range(100):
    x = random.randint(0, SCREEN_WIDTH)
    y = random.randint(0, SCREEN_HEIGHT)
    size = random.randint(1, 3)
    speed = random.uniform(0.5, 2)
    brightness = random.randint(150, 255)
    stars.append([x, y, size, speed, brightness])

# Power-ups
powerup_size = int(30 * SCALE_FACTOR)
powerup_img = pygame.Surface((powerup_size, powerup_size), pygame.SRCALPHA)
scale = powerup_size / 30
pygame.draw.circle(powerup_img, GREEN, (15*scale, 15*scale), 12*scale)
# Add a bullet symbol to the power-up
pygame.draw.rect(powerup_img, YELLOW, (12*scale, 8*scale, 6*scale, 14*scale))

powerup_x = random.randint(0, SCREEN_WIDTH - powerup_size)
powerup_y = -30
powerup_speed = 3 * SCALE_FACTOR
powerup_active = False
powerup_timer = 0
powerup_duration = 300

# Touch controls for mobile
touch_controls = {
    'left': pygame.Rect(50, SCREEN_HEIGHT - 100, 80, 80),
    'right': pygame.Rect(150, SCREEN_HEIGHT - 100, 80, 80),
    'shoot': pygame.Rect(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100, 80, 80)
}

def draw_touch_controls():
    if SCREEN_WIDTH < 1000:  # Show on mobile screens
        # Left button
        pygame.draw.circle(screen, (100, 100, 100, 150), touch_controls['left'].center, 40)
        pygame.draw.polygon(screen, WHITE, [
            (touch_controls['left'].centerx - 15, touch_controls['left'].centery),
            (touch_controls['left'].centerx + 15, touch_controls['left'].centery - 15),
            (touch_controls['left'].centerx + 15, touch_controls['left'].centery + 15)
        ])
        
        # Right button
        pygame.draw.circle(screen, (100, 100, 100, 150), touch_controls['right'].center, 40)
        pygame.draw.polygon(screen, WHITE, [
            (touch_controls['right'].centerx + 15, touch_controls['right'].centery),
            (touch_controls['right'].centerx - 15, touch_controls['right'].centery - 15),
            (touch_controls['right'].centerx - 15, touch_controls['right'].centery + 15)
        ])
        
        # Shoot button
        pygame.draw.circle(screen, (200, 50, 50, 150), touch_controls['shoot'].center, 40)
        pygame.draw.circle(screen, RED, touch_controls['shoot'].center, 30, 3)
        pygame.draw.circle(screen, YELLOW, touch_controls['shoot'].center, 15)

# Collision detection
def iscollision(enemyx, enemyy, bulletx, bullety):
    distance = math.sqrt((enemyx - bulletx) ** 2 + (enemyy - bullety) ** 2)
    return distance < 27 * SCALE_FACTOR

def player_collision(enemyx, enemyy, playerx, playery):
    distance = math.sqrt((enemyx - playerx) ** 2 + (enemyy - playery) ** 2)
    return distance < 50 * SCALE_FACTOR

# Background drawing
def back():
    global bg_y
    screen.blit(bg, (0, bg_y))
    screen.blit(bg, (0, bg_y - SCREEN_HEIGHT))
    bg_y += 1
    if bg_y >= SCREEN_HEIGHT:
        bg_y = 0
    
    for star in stars:
        star[1] += star[3]
        if star[1] > SCREEN_HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, SCREEN_WIDTH)
        color = (star[4], star[4], star[4])
        pygame.draw.circle(screen, color, (int(star[0]), int(star[1])), star[2])

# Main game function
def main_game():
    global score, high_score, playerx, playery, playerx_change
    global powerup_active, powerup_timer, explosion_timer, game_over_flag
    global bullets_available, bullet_list
    
    # Reset bullet system
    bullets_available = 0
    bullet_list = []
    
    init_enemies()
    
    run = True
    game_over_flag = False
    clock = pygame.time.Clock()
    restart_button = None
    menu_button = None
    shooting = False  # Touch shooting flag

    while run:
        screen.fill(BLACK)
        back()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if not game_over_flag:
                # Keyboard controls
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        playerx_change = player_speed
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        playerx_change = -player_speed
                    if event.key == pygame.K_SPACE:
                        bullet_fire(playerx, playery)
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
                    if event.key == pygame.K_F11:
                        toggle_fullscreen()

                if event.type == pygame.KEYUP:
                    if event.key in [pygame.K_d, pygame.K_RIGHT, pygame.K_a, pygame.K_LEFT]:
                        playerx_change = 0

                # Touch controls
                if event.type == pygame.MOUSEBUTTONDOWN and SCREEN_WIDTH < 1000:
                    mouse_pos = event.pos
                    if touch_controls['left'].collidepoint(mouse_pos):
                        playerx_change = -player_speed
                    elif touch_controls['right'].collidepoint(mouse_pos):
                        playerx_change = player_speed
                    elif touch_controls['shoot'].collidepoint(mouse_pos):
                        shooting = True

                if event.type == pygame.MOUSEBUTTONUP and SCREEN_WIDTH < 1000:
                    playerx_change = 0
                    shooting = False
            else:
                # Game over screen controls
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if restart_button and restart_button.collidepoint(mouse_pos):
                        # Reset game
                        score = 0
                        bullets_available = 0
                        bullet_list = []
                        playerx = SCREEN_WIDTH // 2 - player_size // 2
                        playerx_change = 0
                        game_over_flag = False
                        init_enemies()
                    elif menu_button and menu_button.collidepoint(mouse_pos):
                        return "menu"
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Reset game
                        score = 0
                        bullets_available = 0
                        bullet_list = []
                        playerx = SCREEN_WIDTH // 2 - player_size // 2
                        playerx_change = 0
                        game_over_flag = False
                        init_enemies()
                    elif event.key == pygame.K_m:
                        return "menu"

        if not game_over_flag:
            # Continuous shooting for touch
            if shooting and bullets_available > 0:
                bullet_fire(playerx, playery)

            # Player movement
            playerx += playerx_change
            if playerx <= 0:
                playerx = 0
            elif playerx >= SCREEN_WIDTH - player_size:
                playerx = SCREEN_WIDTH - player_size

            # Update bullets
            update_bullets()

            # Enemy movement
            for i in range(num_enemy):
                # Game over if enemy reaches bottom or collides with player
                if enemyy[i] > SCREEN_HEIGHT - 100 or player_collision(enemyx[i], enemyy[i], playerx, playery):
                    game_over_flag = True
                    if score > high_score:
                        high_score = score
                    break

                enemyx[i] += enemyx_change[i]

                if enemyx[i] <= 0:
                    enemyx_change[i] = abs(enemyx_change[i])
                    enemyy[i] += enemyy_change[i]
                elif enemyx[i] >= SCREEN_WIDTH - enemy_img[i].get_width():
                    enemyx_change[i] = -abs(enemyx_change[i])
                    enemyy[i] += enemyy_change[i]

                # Collision with bullets
                for bullet in bullet_list[:]:
                    if bullet['active'] and iscollision(enemyx[i], enemyy[i], bullet['x'] + bullet_width/2, bullet['y']):
                        explosion_x = enemyx[i]
                        explosion_y = enemyy[i]
                        explosion_timer = explosion_duration
                        bullet['active'] = False
                        bullet_list.remove(bullet)
                        score += 1
                        # Reset enemy
                        enemyx[i] = random.randint(0, SCREEN_WIDTH - enemy_img[i].get_width())
                        enemyy[i] = random.randint(50, 150)
                        break

                enemy(enemyx[i], enemyy[i], i)

            # Explosion
            if explosion_timer > 0:
                explosion(explosion_x, explosion_y)
                explosion_timer -= 1

            # Power-up
            if powerup_active:
                powerup_y += powerup_speed
                screen.blit(powerup_img, (powerup_x, powerup_y))
                if powerup_y > SCREEN_HEIGHT:
                    powerup_active = False
            else:
                # Randomly spawn power-up
                if random.randint(0, 1000) < 2:
                    powerup_active = True
                    powerup_x = random.randint(0, SCREEN_WIDTH - powerup_size)
                    powerup_y = -30

            # Power-up collection
            if powerup_active and (playerx < powerup_x + powerup_size and playerx + player_size > powerup_x and
                                  playery < powerup_y + powerup_size and playery + player_size > powerup_y):
                powerup_active = False
                # Add 5 bullets, but don't exceed maximum
                bullets_available = min(bullets_available + 5, MAX_BULLETS)

            # Draw player
            player(playerx, playery)

            # Draw UI
            score_f(10, 10)
            high_score_f(10, 50)
            draw_bullet_list()  # Draw bullet list
            
            # Show current difficulty
            diff_text = font.render(f"Difficulty: {difficulty.upper()}", True, YELLOW)
            screen.blit(diff_text, (10, 90))

            # Draw touch controls
            if SCREEN_WIDTH < 1000:
                draw_touch_controls()

        else:
            # Game over screen
            restart_button, menu_button = game_over()

        pygame.display.update()
        clock.tick(60)

    return "quit"

# Main program loop
def main():
    while True:
        menu_result = show_menu()
        
        if menu_result == "difficulty":
            diff_result = show_difficulty_menu()
            
            if diff_result == "start":
                game_result = main_game()
                
                if game_result == "quit":
                    pygame.quit()
                    sys.exit()
        elif menu_result == "quit":
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()
