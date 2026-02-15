import pygame
import random
import math
import sys
import os
import json
import hashlib

pygame.init()
pygame.mixer.init()

# --- 1. SCREEN SETUP ---
try:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    info = pygame.display.Info()
    SW, SH = info.current_w, info.current_h
except:
    SW, SH = 1280, 720
    screen = pygame.display.set_mode((SW, SH))

pygame.display.set_caption("Galaxy Defender")

# --- 2. COLORS & FONTS ---
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
CYAN = (0, 255, 255)
GREEN = (80, 255, 80)
RED = (255, 80, 80)
BLUE = (80, 150, 255)
PURPLE = (180, 80, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
PINK = (255, 105, 180)
GRAY = (40, 40, 60)
DARK = (5, 5, 20)
LIGHT_BLUE = (100, 180, 255)
BUTTON_GRAY = (60, 60, 80, 180)  # Semi-transparent for on-screen buttons

SCALE = min(SW / 1000, SH / 800)
def get_f(size): 
    return pygame.font.SysFont('trebuchet ms', int(size * SCALE), bold=True)

title_f = get_f(75)
main_f = get_f(32)
stat_f = get_f(24)
small_f = get_f(16)
tiny_f = get_f(12)

# --- 3. DATA PERSISTENCE & USER MANAGEMENT ---

SESSION_FILE = "session.json"

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(hashed_password, user_password):
    """Verify a stored password against one provided by user."""
    return hashed_password == hash_password(user_password)

# --- SESSION HANDLING FUNCTIONS ---

def save_session(username):
    """Saves the last logged-in username to a session file for auto-login."""
    with open(SESSION_FILE, "w") as f:
        json.dump({"last_user": username}, f)

def clear_session():
    """Removes the session file when the user logs out manually."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def get_last_session():
    """Retrieves the username from the last session if it exists."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                return data.get("last_user")
        except:
            return None
    return None

# --- USER CLASS AND SYSTEM ---

class User:
    def __init__(self, username):
        self.username = username
        self.data = {
            "coins": 0, 
            "high_score": 0, 
            "selected": "Interceptor", 
            "unlocked": ["Interceptor"],
            "selected_bullet": "Standard", 
            "unlocked_bullets": ["Standard"],
            "selected_map": "Deep Space", 
            "unlocked_maps": ["Deep Space"],
            "level": 1,
            "levels_completed": 0,
            "boss_defeated": False,
            "touch_controls": False
        }
        self.filepath = f"user_{username}.json"

    def save(self):
        """Save user data to file."""
        with open(self.filepath, "w") as f:
            json.dump(self.data, f)
    
    def load(self):
        """Load user data from file."""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                self.data = json.load(f)
        return self.data

# Global user management
current_user = None
users_file = "users.json"

def load_users():
    """Load all registered users."""
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save all registered users."""
    with open(users_file, "w") as f:
        json.dump(users, f)

def register_user(username, password):
    """Register a new user and login."""
    users = load_users()
    if username in users:
        return False, "Username already exists!"
    
    users[username] = {
        "password_hash": hash_password(password),
        "created_at": pygame.time.get_ticks()
    }
    save_users(users)
    
    # Create and save user data file
    user = User(username)
    user.save()
    
    return True, "Registration successful!"

def login_user(username, password):
    """Login an existing user and save session for auto-login."""
    users = load_users()
    if username not in users:
        return False, "User does not exist!"
    
    if not check_password(users[username]["password_hash"], password):
        return False, "Incorrect password!"
    
    global current_user
    current_user = User(username)
    current_user.load()
    
    # NEW: Create session file
    save_session(username)
    
    return True, "Login successful!"

def logout_user():
    """Logout current user and clear session file."""
    global current_user
    if current_user:
        current_user.save()
    current_user = None
    
    # NEW: Clear session data
    clear_session()

def get_game_data():
    """Get current user's game data."""
    global current_user
    if current_user:
        return current_user.data
    return None

def update_game_data(key, value):
    """Update current user's game data."""
    global current_user
    if current_user:
        current_user.data[key] = value

def save_current_user():
    """Save current user's data."""
    global current_user
    if current_user:
        current_user.save()

# --- 4. ASSET LOADING WITH FALLBACK ---
def load_asset(name, w, h, is_bullet=False, is_enemy=False, enemy_type=""):
    if is_enemy:
        # Try to load enemy image
        fname = f"enemy_{enemy_type.lower()}.png"
        if os.path.exists(fname):
            img = pygame.image.load(fname).convert_alpha()
        else:
            # Create colored circle as fallback
            img = pygame.Surface((w, h), pygame.SRCALPHA)
            color_dict = {
                "basic": RED,
                "fast": GREEN,
                "tank": ORANGE,
                "boss": PURPLE,
                "elite": GOLD,
                "swarmer": CYAN,
                "splitter": PINK,
                "healer": BLUE
            }
            color = color_dict.get(enemy_type, RED)
            pygame.draw.circle(img, color, (w//2, h//2), w//2)
            pygame.draw.circle(img, WHITE, (w//2, h//2), w//2, 2)
    elif is_bullet:
        fname = f"bullet_{name[:3].lower()}.png"
        if os.path.exists(fname):
            img = pygame.image.load(fname).convert_alpha()
        else:
            img = pygame.Surface((w, h), pygame.SRCALPHA)
            color_dict = {
                "Standard": CYAN, "Fast": GREEN, "Heavy": ORANGE,
                "Plasma": PURPLE, "Golden": GOLD
            }
            color = color_dict.get(name, CYAN)
            pygame.draw.rect(img, color, (0, 0, w, h), border_radius=3)
    else:
        fname = f"{name.lower().replace(' ', '_')}.png"
        if os.path.exists(fname):
            img = pygame.image.load(fname).convert_alpha()
        else:
            img = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(img, BLUE, (0, 0, w, h), border_radius=10)
            pygame.draw.rect(img, WHITE, (0, 0, w, h), 2, border_radius=10)
    
    return pygame.transform.scale(img, (int(w*SCALE), int(h*SCALE)))

# --- 5. SHIPS ---
SHIPS = {
    "Interceptor": {"speed": 8, "cap": 12, "price": 0, "reload": 1.2, "shield": 10},
    "Stinger": {"speed": 14, "cap": 10, "price": 1000, "reload": 0.8, "shield": 15},
    "Titan": {"speed": 5, "cap": 15, "price": 3000, "reload": 2.0, "shield": 20},
    "Falcon": {"speed": 11, "cap": 14, "price": 5000, "reload": 1.0, "shield": 25},
    "Phoenix": {"speed": 12, "cap": 20, "price": 7000, "reload": 0.7, "shield": 30}
}

# --- 6. BULLETS ---
BULLETS = {
    "Standard": {"spd": 13, "price": 0, "damage": 1, "color": CYAN},
    "Fast": {"spd": 25, "price": 990, "damage": 2, "color": GREEN},
    "Heavy": {"spd": 9, "price": 1110, "damage": 3, "color": ORANGE},
    "Plasma": {"spd": 18, "price": 2000, "damage": 4, "color": PURPLE},
    "Golden": {"spd": 16, "price": 5000, "damage": 5, "color": GOLD}
}

# --- 7. MAPS ---
MAPS = {
    "Deep Space": {"price": 0, "bg_color": (10, 10, 30), "star_color": (200, 200, 255)},
    "Mars Base": {"price": 2000, "bg_color": (50, 20, 10), "star_color": (255, 200, 150)},
    "Nebula X": {"price": 4000, "bg_color": (30, 10, 50), "star_color": (255, 150, 255)}
}

# --- 8. ENEMY TYPES ---
ENEMY_TYPES = {
    "basic": {"health": 1, "speed": 3, "size": 30, "score": 10, "coin_chance": 0.3, "color": RED},
    "fast": {"health": 1, "speed": 6, "size": 25, "score": 15, "coin_chance": 0.4, "color": GREEN},
    "tank": {"health": 3, "speed": 2, "size": 40, "score": 30, "coin_chance": 0.5, "color": ORANGE},
    "elite": {"health": 2, "speed": 4, "size": 35, "score": 25, "coin_chance": 0.6, "color": GOLD},
    "swarmer": {"health": 1, "speed": 5, "size": 20, "score": 20, "coin_chance": 0.4, "color": CYAN},
    "splitter": {"health": 2, "speed": 3, "size": 35, "score": 35, "coin_chance": 0.7, "color": PINK},
    "healer": {"health": 2, "speed": 3, "size": 30, "score": 40, "coin_chance": 0.8, "color": BLUE},
    "boss": {
        "health": 50, 
        "speed": 0,  # Boss doesn't move down!
        "size": 80, 
        "score": 500, 
        "coin_chance": 1.0, 
        "color": PURPLE,
        "fire_rate": 1.5,
        "bullet_speed": 6,
        "bullet_damage": 1,
        "movement_range": 300,
        "move_speed": 3,
        "fixed_y": 150  # Fixed vertical position
    }
}

# --- 9. LEVEL DESIGNS (40 Levels) ---
LEVELS = [
    # Levels 1-10: Basic training
    {"enemies": [{"type": "basic", "count": 30}], "time_limit": 60, "coin_reward": 10},
    {"enemies": [{"type": "basic", "count": 30}], "time_limit": 70, "coin_reward": 20},
    {"enemies": [{"type": "basic", "count": 30}, {"type": "fast", "count": 2}], "time_limit": 80, "coin_reward": 30},
    {"enemies": [{"type": "fast", "count": 30}], "time_limit": 75, "coin_reward": 40},
    {"enemies": [{"type": "basic", "count": 30}, {"type": "fast", "count": 4}], "time_limit": 90, "coin_reward": 50},
    {"enemies": [{"type": "tank", "count": 30}], "time_limit": 100, "coin_reward": 60},
    {"enemies": [{"type": "basic", "count": 30}, {"type": "tank", "count": 2}], "time_limit": 110, "coin_reward": 70},
    {"enemies": [{"type": "fast", "count": 30}, {"type": "tank", "count": 3}], "time_limit": 120, "coin_reward": 80},
    {"enemies": [{"type": "elite", "count": 30}], "time_limit": 100, "coin_reward": 90},
    {"enemies": [{"type": "basic", "count": 30}], "time_limit": 130, "coin_reward": 100},
    
    # Levels 11-20: Intermediate challenges
    {"enemies": [{"type": "swarmer", "count": 8}], "time_limit": 110, "coin_reward": 110},
    {"enemies": [{"type": "basic", "count": 30}, {"type": "swarmer", "count": 6}], "time_limit": 120, "coin_reward": 120},
    {"enemies": [{"type": "tank", "count": 30}, {"type": "fast", "count": 4}], "time_limit": 140, "coin_reward": 130},
    {"enemies": [{"type": "splitter", "count": 30}], "time_limit": 130, "coin_reward": 140},
    {"enemies": [{"type": "elite", "count": 36}, {"type": "swarmer", "count": 30}], "time_limit": 150, "coin_reward": 150},
    {"enemies": [{"type": "healer", "count": 32}, {"type": "tank", "count": 24}], "time_limit": 160, "coin_reward": 160},
    {"enemies": [{"type": "fast", "count": 12}, {"type": "swarmer", "count": 10}], "time_limit": 170, "coin_reward": 170},
    {"enemies": [{"type": "splitter", "count": 6}], "time_limit": 150, "coin_reward": 180},
    {"enemies": [{"type": "elite", "count": 8}, {"type": "healer", "count": 3}], "time_limit": 180, "coin_reward": 190},
    {"enemies": [{"type": "boss", "count": 1}], "time_limit": 300, "coin_reward": 200, "is_boss": True},
    
    # Levels 21-30: Advanced challenges
    {"enemies": [{"type": "basic", "count": 20}], "time_limit": 180, "coin_reward": 210},
    {"enemies": [{"type": "fast", "count": 15}, {"type": "swarmer", "count": 15}], "time_limit": 200, "coin_reward": 220},
    {"enemies": [{"type": "tank", "count": 10}, {"type": "elite", "count": 5}], "time_limit": 220, "coin_reward": 230},
    {"enemies": [{"type": "splitter", "count": 8}, {"type": "healer", "count": 4}], "time_limit": 210, "coin_reward": 240},
    {"enemies": [{"type": "elite", "count": 12}], "time_limit": 230, "coin_reward": 250},
    {"enemies": [{"type": "swarmer", "count": 25}], "time_limit": 240, "coin_reward": 260},
    {"enemies": [{"type": "healer", "count": 6}, {"type": "tank", "count": 8}], "time_limit": 250, "coin_reward": 270},
    {"enemies": [{"type": "fast", "count": 20}, {"type": "elite", "count": 10}], "time_limit": 260, "coin_reward": 280},
    {"enemies": [{"type": "splitter", "count": 12}], "time_limit": 240, "coin_reward": 290},
    {"enemies": [{"type": "boss", "count": 1}, {"type": "elite", "count": 5}], "time_limit": 350, "coin_reward": 300, "is_boss": True},
    
    # Levels 31-40: Expert challenges
    {"enemies": [{"type": "basic", "count": 30}, {"type": "fast", "count": 20}], "time_limit": 280, "coin_reward": 310},
    {"enemies": [{"type": "tank", "count": 35}, {"type": "elite", "count": 30}, {"type": "healer", "count": 35}], "time_limit": 300, "coin_reward": 320},
    {"enemies": [{"type": "swarmer", "count": 40}], "time_limit": 320, "coin_reward": 330},
    {"enemies": [{"type": "splitter", "count": 35}, {"type": "fast", "count": 20}], "time_limit": 340, "coin_reward": 340},
    {"enemies": [{"type": "elite", "count": 30}, {"type": "healer", "count": 30}], "time_limit": 360, "coin_reward": 350},
    {"enemies": [{"type": "tank", "count": 30}, {"type": "elite", "count": 35}], "time_limit": 380, "coin_reward": 360},
    {"enemies": [{"type": "fast", "count": 30}, {"type": "swarmer", "count": 30}], "time_limit": 400, "coin_reward": 370},
    {"enemies": [{"type": "splitter", "count": 20}, {"type": "healer", "count": 10}], "time_limit": 420, "coin_reward": 380},
    {"enemies": [{"type": "elite", "count": 25}, {"type": "tank", "count": 15}], "time_limit": 440, "coin_reward": 390},
    {"enemies": [{"type": "boss", "count": 30}], "time_limit": 500, "coin_reward": 400, "is_boss": True}
]

# --- 10. LOAD ASSETS ---
SHIP_IMGS = {n: load_asset(n, 100, 100) for n in SHIPS}
BULL_IMGS = {n: load_asset(n, 20, 60, is_bullet=True) for n in BULLETS}
COIN_IMG = load_asset("coin", 32, 32)
HEART_IMG = load_asset("heart", 32, 32)
ENEMY_IMGS = {etype: load_asset("enemy", 60, 60, is_enemy=True, enemy_type=etype) for etype in ENEMY_TYPES.keys()}

# --- 11. CREATE MAP BACKGROUNDS ---
MAP_BGS = {}
for name, data in MAPS.items():
    bg = pygame.Surface((SW, SH))
    bg.fill(data["bg_color"])
    
    # Add stars
    for _ in range(150):
        x = random.randint(0, SW)
        y = random.randint(0, SH)
        size = random.randint(1, 3)
        brightness = random.randint(100, 255)
        color = (
            min(255, data["star_color"][0] + random.randint(-50, 50)),
            min(255, data["star_color"][1] + random.randint(-50, 50)),
            min(255, data["star_color"][2] + random.randint(-50, 50))
        )
        pygame.draw.circle(bg, color, (x, y), size)
    
    # Add nebula effects
    if name == "Nebula X":
        for _ in range(5):
            x = random.randint(0, SW)
            y = random.randint(0, SH)
            radius = random.randint(100, 300)
            nebula = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            for i in range(radius):
                alpha = int(30 * (1 - i/radius))
                pygame.draw.circle(nebula, (180, 50, 255, alpha), (radius, radius), radius-i)
            bg.blit(nebula, (x-radius, y-radius))
    
    MAP_BGS[name] = bg

# --- 12. UI COMPONENTS ---
def draw_btn(text, rect, color, hover, font=None):
    if font is None:
        font = main_f
    
    # Draw shadow
    shadow = rect.move(5, 5)
    pygame.draw.rect(screen, (0, 0, 0, 100), shadow, border_radius=12)
    
    # Draw button
    btn_color = color
    if hover:
        btn_color = tuple(min(255, c + 30) for c in color)
    
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (*btn_color, 200), (0, 0, rect.width, rect.height), border_radius=12)
    pygame.draw.rect(s, WHITE, (0, 0, rect.width, rect.height), 2, border_radius=12)
    screen.blit(s, (rect.x, rect.y))
    
    # Draw text
    t = font.render(text, True, WHITE)
    screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))

def draw_text(text, font, color, pos, center=True):
    rendered = font.render(text, True, color)
    if center:
        pos = (pos[0] - rendered.get_width()//2, pos[1])
    screen.blit(rendered, pos)

def draw_progress_bar(x, y, width, height, progress, color):
    # Background
    pygame.draw.rect(screen, (50, 50, 50), (x, y, width, height), border_radius=height//2)
    # Progress
    if progress > 0:
        bar_width = int(width * progress)
        pygame.draw.rect(screen, color, (x, y, bar_width, height), border_radius=height//2)
    # Border
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 2, border_radius=height//2)

def draw_input_field(rect, text, active, max_length=20):
    # Draw background
    pygame.draw.rect(screen, (30, 30, 50), rect, border_radius=8)
    pygame.draw.rect(screen, CYAN if active else WHITE, rect, 2, border_radius=8)
    
    # Draw text
    display_text = text
    if active:
        # Add blinking cursor
        if pygame.time.get_ticks() % 1000 < 500:
            display_text += "|"
    
    text_surface = small_f.render(display_text, True, WHITE)
    screen.blit(text_surface, (rect.x + 10, rect.centery - text_surface.get_height()//2))

def draw_touch_button(rect, text, active=False, color=BUTTON_GRAY):
    """Draw a semi-transparent touch button for on-screen controls."""
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    
    # Draw button background
    btn_color = (*color[:3], 200) if active else color
    pygame.draw.circle(s, btn_color, (rect.width//2, rect.height//2), rect.width//2)
    pygame.draw.circle(s, WHITE, (rect.width//2, rect.height//2), rect.width//2, 2)
    
    # Draw text/icon
    if text == "←":
        pygame.draw.polygon(s, WHITE, [
            (rect.width//2 + 15, rect.height//2 - 15),
            (rect.width//2 + 15, rect.height//2 + 15),
            (rect.width//2 - 15, rect.height//2)
        ])
    elif text == "→":
        pygame.draw.polygon(s, WHITE, [
            (rect.width//2 - 15, rect.height//2 - 15),
            (rect.width//2 - 15, rect.height//2 + 15),
            (rect.width//2 + 15, rect.height//2)
        ])
    elif text == "FIRE":
        # Draw fire icon (triangle)
        pygame.draw.polygon(s, RED, [
            (rect.width//2, rect.height//2 - 20),
            (rect.width//2 - 15, rect.height//2 + 10),
            (rect.width//2 + 15, rect.height//2 + 10)
        ])
        pygame.draw.polygon(s, ORANGE, [
            (rect.width//2, rect.height//2 - 15),
            (rect.width//2 - 10, rect.height//2 + 5),
            (rect.width//2 + 10, rect.height//2 + 5)
        ])
    
    screen.blit(s, (rect.x, rect.y))

# --- 13. LOGIN/REGISTER SCREEN (Android-friendly) ---
def show_auth_screen():
    mode = "login"  # "login" or "register"
    username = ""
    password = ""
    confirm_password = ""
    active_field = None  # None, "username", "password", "confirm_password"
    message = ""
    message_color = RED
    show_keyboard = False
    keyboard_text = ""
    
    # On-screen keyboard layout
    keyboard_rows = [
        "1234567890",
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm@._"
    ]
    keyboard_buttons = []
    special_keys = [
        {"text": "SPACE", "width": 200, "action": "space"},
        {"text": "DELETE", "width": 150, "action": "delete"},
        {"text": "DONE", "width": 150, "action": "done"}
    ]
    
    while True:
        m_pos = pygame.mouse.get_pos()
        screen.fill(DARK)
        
        # Title
        title = "LOGIN" if mode == "login" else "REGISTER"
        draw_text(title, title_f, CYAN, (SW//2, 80))
        
        y_offset = 150
        
        # Username field
        username_rect = pygame.Rect(SW//2 - 200, y_offset, 400, 60)
        draw_text("Username:", small_f, WHITE, (SW//2, y_offset - 25))
        
        # Draw field with selection indicator
        field_color = CYAN if active_field == "username" else WHITE
        pygame.draw.rect(screen, (30, 30, 50), username_rect, border_radius=10)
        pygame.draw.rect(screen, field_color, username_rect, 3, border_radius=10)
        
        # Draw username text
        display_text = username if username else "Tap to enter username"
        text_color = WHITE if username else (150, 150, 150)
        text_surface = small_f.render(display_text, True, text_color)
        screen.blit(text_surface, (username_rect.x + 15, username_rect.centery - text_surface.get_height()//2))
        
        y_offset += 80
        
        # Password field
        password_rect = pygame.Rect(SW//2 - 200, y_offset, 400, 60)
        draw_text("Password:", small_f, WHITE, (SW//2, y_offset - 25))
        
        field_color = CYAN if active_field == "password" else WHITE
        pygame.draw.rect(screen, (30, 30, 50), password_rect, border_radius=10)
        pygame.draw.rect(screen, field_color, password_rect, 3, border_radius=10)
        
        display_text = "*" * len(password) if password else "Tap to enter password"
        text_color = WHITE if password else (150, 150, 150)
        text_surface = small_f.render(display_text, True, text_color)
        screen.blit(text_surface, (password_rect.x + 15, password_rect.centery - text_surface.get_height()//2))
        
        y_offset += 80
        
        # Confirm password field (only for register)
        confirm_rect = None
        if mode == "register":
            confirm_rect = pygame.Rect(SW//2 - 200, y_offset, 400, 60)
            draw_text("Confirm Password:", small_f, WHITE, (SW//2, y_offset - 25))
            
            field_color = CYAN if active_field == "confirm_password" else WHITE
            pygame.draw.rect(screen, (30, 30, 50), confirm_rect, border_radius=10)
            pygame.draw.rect(screen, field_color, confirm_rect, 3, border_radius=10)
            
            display_text = "*" * len(confirm_password) if confirm_password else "Tap to confirm password"
            text_color = WHITE if confirm_password else (150, 150, 150)
            text_surface = small_f.render(display_text, True, text_color)
            screen.blit(text_surface, (confirm_rect.x + 15, confirm_rect.centery - text_surface.get_height()//2))
            
            y_offset += 80
        
        # Mode toggle button
        toggle_rect = pygame.Rect(SW//2 - 150, y_offset, 300, 50)
        toggle_text = "Switch to Register" if mode == "login" else "Switch to Login"
        draw_btn(toggle_text, toggle_rect, BLUE, toggle_rect.collidepoint(m_pos), small_f)
        
        # Submit button
        submit_rect = pygame.Rect(SW//2 - 150, y_offset + 70, 300, 60)
        submit_text = "LOGIN" if mode == "login" else "REGISTER"
        draw_btn(submit_text, submit_rect, GREEN, submit_rect.collidepoint(m_pos))
        
        # Back button
        back_rect = pygame.Rect(SW//2 - 150, y_offset + 150, 300, 50)
        draw_btn("BACK TO MENU", back_rect, RED, back_rect.collidepoint(m_pos))
        
        # Display message
        if message:
            draw_text(message, small_f, message_color, (SW//2, y_offset + 220))
        
        # Draw on-screen keyboard if a field is active
        if active_field is not None:
            # Semi-transparent overlay
            overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            # Keyboard area
            keyboard_y = SH - 300
            key_size = 60
            key_margin = 5
            
            # Draw current field value preview
            preview_rect = pygame.Rect(50, keyboard_y - 80, SW - 100, 60)
            pygame.draw.rect(screen, (40, 40, 60), preview_rect, border_radius=10)
            pygame.draw.rect(screen, CYAN, preview_rect, 3, border_radius=10)
            
            current_text = ""
            if active_field == "username":
                current_text = username
                field_name = "Username: "
            elif active_field == "password":
                current_text = "*" * len(password)
                field_name = "Password: "
            else:
                current_text = "*" * len(confirm_password)
                field_name = "Confirm: "
            
            preview_text = small_f.render(field_name + current_text, True, WHITE)
            screen.blit(preview_text, (preview_rect.x + 20, preview_rect.centery - preview_text.get_height()//2))
            
            # Draw keyboard buttons
            keyboard_buttons.clear()
            start_x = (SW - (len(keyboard_rows[0]) * (key_size + key_margin))) // 2
            
            for row_idx, row in enumerate(keyboard_rows):
                row_y = keyboard_y + row_idx * (key_size + key_margin)
                for col_idx, char in enumerate(row):
                    key_x = start_x + col_idx * (key_size + key_margin)
                    key_rect = pygame.Rect(key_x, row_y, key_size, key_size)
                    keyboard_buttons.append((key_rect, char))
                    
                    # Draw key
                    pygame.draw.rect(screen, (60, 60, 80), key_rect, border_radius=8)
                    pygame.draw.rect(screen, WHITE, key_rect, 2, border_radius=8)
                    
                    # Draw character
                    char_surf = small_f.render(char.upper(), True, WHITE)
                    screen.blit(char_surf, (key_rect.centerx - char_surf.get_width()//2, 
                                           key_rect.centery - char_surf.get_height()//2))
            
            # Draw special keys (Space, Delete, Done)
            special_y = keyboard_y + 4 * (key_size + key_margin)
            special_start_x = (SW - (200 + 150 + 150 + 40)) // 2  # 40 for margins
            
            for i, special in enumerate(special_keys):
                key_x = special_start_x + i * (special["width"] + 20)
                key_rect = pygame.Rect(key_x, special_y, special["width"], key_size)
                keyboard_buttons.append((key_rect, special["action"]))
                
                # Draw special key
                pygame.draw.rect(screen, BLUE, key_rect, border_radius=8)
                pygame.draw.rect(screen, WHITE, key_rect, 2, border_radius=8)
                
                # Draw text
                text_surf = small_f.render(special["text"], True, WHITE)
                screen.blit(text_surf, (key_rect.centerx - text_surf.get_width()//2, 
                                       key_rect.centery - text_surf.get_height()//2))
        
        pygame.display.flip()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                # Handle field selection
                if username_rect.collidepoint(e.pos):
                    active_field = "username"
                elif password_rect.collidepoint(e.pos):
                    active_field = "password"
                elif mode == "register" and confirm_rect and confirm_rect.collidepoint(e.pos):
                    active_field = "confirm_password"
                
                # Handle keyboard buttons if active
                elif active_field is not None:
                    for key_rect, key_char in keyboard_buttons:
                        if key_rect.collidepoint(e.pos):
                            if key_char == "space":
                                char_to_add = " "
                            elif key_char == "delete":
                                char_to_add = "BACKSPACE"
                            elif key_char == "done":
                                active_field = None
                                continue
                            else:
                                char_to_add = key_char
                            
                            # Update the appropriate field
                            if active_field == "username":
                                if char_to_add == "BACKSPACE":
                                    username = username[:-1]
                                elif len(username) < 20:
                                    username += char_to_add
                            elif active_field == "password":
                                if char_to_add == "BACKSPACE":
                                    password = password[:-1]
                                elif len(password) < 20:
                                    password += char_to_add
                            elif active_field == "confirm_password":
                                if char_to_add == "BACKSPACE":
                                    confirm_password = confirm_password[:-1]
                                elif len(confirm_password) < 20:
                                    confirm_password += char_to_add
                            break
                
                # Handle mode toggle
                elif toggle_rect.collidepoint(e.pos):
                    mode = "register" if mode == "login" else "login"
                    username = ""
                    password = ""
                    confirm_password = ""
                    active_field = None
                    message = ""
                
                # Handle submit
                elif submit_rect.collidepoint(e.pos):
                    if not username or not password:
                        message = "Please fill in all fields!"
                        message_color = RED
                    elif mode == "register" and password != confirm_password:
                        message = "Passwords do not match!"
                        message_color = RED
                    elif len(username) < 3:
                        message = "Username must be at least 3 characters!"
                        message_color = RED
                    elif len(password) < 4:
                        message = "Password must be at least 4 characters!"
                        message_color = RED
                    else:
                        if mode == "login":
                            success, msg = login_user(username, password)
                            message_color = GREEN if success else RED
                            message = msg
                            if success:
                                pygame.time.wait(500)
                                return True
                        else:
                            success, msg = register_user(username, password)
                            message_color = GREEN if success else RED
                            message = msg
                            if success:
                                # Auto-login after successful registration
                                success, msg = login_user(username, password)
                                if success:
                                    pygame.time.wait(500)
                                    return True
                
                # Handle back button
                elif back_rect.collidepoint(e.pos):
                    return False
                
                # Click outside closes keyboard
                elif active_field is not None:
                    # Check if click is outside keyboard area
                    if e.pos[1] < SH - 350:  # Above keyboard area
                        active_field = None
            
            # Handle keyboard input (for testing on PC)
            elif e.type == pygame.KEYDOWN and active_field is None:
                if e.key == pygame.K_TAB:
                    # Tab through fields
                    if mode == "login":
                        if active_field == "username":
                            active_field = "password"
                        else:
                            active_field = "username"
                    else:
                        if active_field == "username":
                            active_field = "password"
                        elif active_field == "password":
                            active_field = "confirm_password"
                        else:
                            active_field = "username"
                elif e.key == pygame.K_RETURN:
                    # Simulate submit click
                    pass
                elif e.key == pygame.K_BACKSPACE:
                    # Handle backspace
                    if active_field == "username":
                        username = username[:-1]
                    elif active_field == "password":
                        password = password[:-1]
                    elif active_field == "confirm_password":
                        confirm_password = confirm_password[:-1]
                else:
                    # Handle text input
                    if e.unicode.isprintable():
                        if active_field == "username" and len(username) < 20:
                            username += e.unicode
                        elif active_field == "password" and len(password) < 20:
                            password += e.unicode
                        elif active_field == "confirm_password" and len(confirm_password) < 20:
                            confirm_password += e.unicode
                            
# --- 14. LEVEL SELECTION ---
def select_level():
    game_data = get_game_data()
    if not game_data:
        return None
    
    current_level = game_data["level"]
    max_unlocked = min(game_data["levels_completed"] + 1, 40)
    
    rows = 8
    cols = 5
    cell_width = 150
    cell_height = 100
    start_x = SW//2 - (cols * cell_width)//2
    start_y = 150
    
    while True:
        screen.fill(DARK)
        
        # Title
        draw_text("SELECT LEVEL", title_f, CYAN, (SW//2, 50))
        
        # Level grid
        for i in range(40):
            row = i // cols
            col = i % cols
            
            level_num = i + 1
            rect = pygame.Rect(
                start_x + col * cell_width,
                start_y + row * cell_height,
                cell_width - 20,
                cell_height - 20
            )
            
            # Determine button color
            if level_num == current_level:
                color = GREEN
            elif level_num <= max_unlocked:
                color = BLUE
            else:
                color = GRAY
            
            hover = rect.collidepoint(pygame.mouse.get_pos())
            if hover and level_num <= max_unlocked:
                color = tuple(min(255, c + 30) for c in color)
            
            # Draw level button
            pygame.draw.rect(screen, color, rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, rect, 2, border_radius=15)
            
            # Level number
            draw_text(str(level_num), main_f, WHITE, (rect.centerx, rect.centery - 15))
            
            # Stars for completed levels
            if level_num <= game_data["levels_completed"]:
                star_color = GOLD
                for s in range(3):
                    pygame.draw.circle(screen, star_color, 
                                     (rect.centerx - 20 + s*20, rect.centery + 15), 5)
            
            # Handle clicks
            if pygame.mouse.get_pressed()[0] and hover and level_num <= max_unlocked:
                update_game_data("level", level_num)
                save_current_user()
                return LEVELS[level_num - 1]
        
        # Back button
        back_btn = pygame.Rect(50, SH - 100, 200, 50)
        draw_btn("BACK", back_btn, RED, back_btn.collidepoint(pygame.mouse.get_pos()))
        
        # Display current progress
        draw_text(f"Levels Completed: {game_data['levels_completed']}/40", stat_f, WHITE, (SW//2, SH - 150))
        
        pygame.display.flip()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.collidepoint(e.pos):
                    return None

# --- 15. SHOP MENU ---
def show_shop():
    game_data = get_game_data()
    if not game_data:
        return
    
    tab = "SHIPS"
    
    while True:
        m_pos = pygame.mouse.get_pos()
        screen.fill(DARK)
        
        # Title
        draw_text("HANGAR", title_f, CYAN, (SW//2, 50))
        
        # Tabs
        tabs = ["SHIPS", "BULLETS", "MAPS"]
        for i, tab_name in enumerate(tabs):
            rect = pygame.Rect(SW//2 - 150 + i*120, 130, 100, 40)
            draw_btn(tab_name, rect, BLUE if tab == tab_name else GRAY, rect.collidepoint(m_pos))
            if pygame.mouse.get_pressed()[0] and rect.collidepoint(m_pos):
                tab = tab_name
        
        # Content based on tab
        if tab == "SHIPS":
            items = SHIPS
            unlocked = game_data["unlocked"]
            selected = game_data["selected"]
            preview_imgs = SHIP_IMGS
        elif tab == "BULLETS":
            items = BULLETS
            unlocked = game_data["unlocked_bullets"]
            selected = game_data["selected_bullet"]
            preview_imgs = BULL_IMGS
        else:
            items = MAPS
            unlocked = game_data["unlocked_maps"]
            selected = game_data["selected_map"]
            preview_imgs = MAP_BGS
        
        # Display items
        cards = []
        for i, (name, data) in enumerate(items.items()):
            row = i // 3
            col = i % 3
            
            card = pygame.Rect(SW//2 - 350 + col*250, 200 + row*280, 220, 260)
            
            # Card background
            pygame.draw.rect(screen, (30, 30, 50), card, border_radius=15)
            pygame.draw.rect(screen, WHITE, card, 2, border_radius=15)
            
            # Item image
            if tab == "MAPS":
                img = pygame.transform.scale(preview_imgs[name], (200, 100))
                screen.blit(img, (card.centerx - 100, card.y + 10))
            else:
                img = preview_imgs[name]
                screen.blit(img, (card.centerx - img.get_width()//2, card.y + 10))
            
            # Item name
            draw_text(name, small_f, WHITE, (card.centerx, card.y + (130 if tab == "MAPS" else 120)))
            
            # Stats
            if tab == "SHIPS":
                stats = f"Speed: {data['speed']} | Shield: {data['shield']}"
            elif tab == "BULLETS":
                stats = f"Speed: {data['spd']} | Damage: {data['damage']}"
            else:
                stats = f"Price: ${data['price']}"
            
            draw_text(stats, small_f, CYAN, (card.centerx, card.y + (150 if tab == "MAPS" else 140)))
            
            # Purchase/Select button
            btn = pygame.Rect(card.x + 30, card.y + 200, 160, 40)
            
            if name in unlocked:
                if name == selected:
                    status = "SELECTED"
                    btn_color = GREEN
                else:
                    status = "SELECT"
                    btn_color = BLUE
            else:
                status = f"${data['price']}"
                btn_color = GOLD if game_data['coins'] >= data['price'] else GRAY
            
            draw_btn(status, btn, btn_color, btn.collidepoint(m_pos))
            cards.append((btn, name, data.get('price', 0), status))
        
        # Coin display
        screen.blit(COIN_IMG, (SW - 150, 30))
        draw_text(f"{game_data['coins']}", main_f, GOLD, (SW - 100, 35), center=False)
        
        # Back button
        back_btn = pygame.Rect(50, SH - 80, 150, 50)
        draw_btn("BACK", back_btn, RED, back_btn.collidepoint(m_pos))
        
        pygame.display.flip()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.collidepoint(e.pos):
                    return
                
                for btn, name, price, status in cards:
                    if btn.collidepoint(e.pos):
                        if status == "SELECT":
                            if tab == "SHIPS":
                                update_game_data("selected", name)
                            elif tab == "BULLETS":
                                update_game_data("selected_bullet", name)
                            else:
                                update_game_data("selected_map", name)
                        elif status.startswith("$"):
                            if game_data['coins'] >= price:
                                update_game_data('coins', game_data['coins'] - price)
                                if tab == "SHIPS":
                                    unlocked = game_data["unlocked"]
                                    unlocked.append(name)
                                    update_game_data("unlocked", unlocked)
                                    update_game_data("selected", name)
                                elif tab == "BULLETS":
                                    unlocked_bullets = game_data["unlocked_bullets"]
                                    unlocked_bullets.append(name)
                                    update_game_data("unlocked_bullets", unlocked_bullets)
                                    update_game_data("selected_bullet", name)
                                else:
                                    unlocked_maps = game_data["unlocked_maps"]
                                    unlocked_maps.append(name)
                                    update_game_data("unlocked_maps", unlocked_maps)
                                    update_game_data("selected_map", name)
                        save_current_user()
                        break

# --- 16. SETTINGS MENU ---
def show_settings():
    game_data = get_game_data()
    if not game_data:
        return
    
    touch_controls = game_data.get("touch_controls", False)
    
    while True:
        m_pos = pygame.mouse.get_pos()
        screen.fill(DARK)
        
        # Title
        draw_text("SETTINGS", title_f, CYAN, (SW//2, 50))
        
        # Touch controls toggle
        touch_rect = pygame.Rect(SW//2 - 200, 150, 400, 60)
        touch_color = GREEN if touch_controls else GRAY
        draw_btn("TOUCH CONTROLS: " + ("ON" if touch_controls else "OFF"), 
                touch_rect, touch_color, touch_rect.collidepoint(m_pos))
        
        # Control instructions
        y_offset = 230
        draw_text("Keyboard Controls:", small_f, WHITE, (SW//2, y_offset))
        draw_text("Arrow Keys / A/D: Move", small_f, CYAN, (SW//2, y_offset + 30))
        draw_text("Spacebar: Shoot", small_f, CYAN, (SW//2, y_offset + 50))
        draw_text("ESC: Pause/Exit", small_f, CYAN, (SW//2, y_offset + 70))
        
        if touch_controls:
            y_offset += 120
            draw_text("Touch Controls:", small_f, WHITE, (SW//2, y_offset))
            draw_text("Left/Right Buttons: Move", small_f, CYAN, (SW//2, y_offset + 30))
            draw_text("Fire Button: Shoot", small_f, CYAN, (SW//2, y_offset + 50))
        
        # Back button
        back_btn = pygame.Rect(SW//2 - 150, SH - 100, 300, 50)
        draw_btn("BACK", back_btn, RED, back_btn.collidepoint(m_pos))
        
        pygame.display.flip()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                if touch_rect.collidepoint(e.pos):
                    touch_controls = not touch_controls
                    update_game_data("touch_controls", touch_controls)
                    save_current_user()
                elif back_btn.collidepoint(e.pos):
                    return

# --- 17. GAME ENGINE WITH TOUCH CONTROLS ---
def main_game():
    # Check if user is logged in
    game_data = get_game_data()
    if not game_data:
        return
    
    # Check if touch controls are enabled
    touch_controls = game_data.get("touch_controls", False)
    
    # Select level
    level_data = select_level()
    if not level_data:
        return
    
    level_num = game_data["level"]
    
    # Game state
    score = 0
    collected_coins = 0
    bullets = []
    enemies = []
    coins = []
    powerups = []
    enemy_bullets = []  # Add this for boss bullets
    
    # Player setup
    ship = SHIPS[game_data["selected"]]
    bullet_cfg = BULLETS[game_data["selected_bullet"]]
    bg = MAP_BGS[game_data["selected_map"]]
    
    p_img = SHIP_IMGS[game_data["selected"]]
    b_img = BULL_IMGS[game_data["selected_bullet"]]
    
    # Player initial position - fixed at bottom of screen
    player_width = 100
    player_height = 100
    px, py = SW//2 - player_width//2, SH - player_height - 50
    shield = ship["shield"]
    ammo = ship["cap"]
    reloading = False
    reload_timer = 0
    reload_time = ship["reload"] * 1000
    
    # Touch control state
    left_pressed = False
    right_pressed = False
    fire_pressed = False
    fire_cooldown = 0
    fire_cooldown_time = 200  # ms between shots for touch controls
    
    # Define touch control buttons
    button_size = 80
    button_margin = 30
    
    # Left movement button
    left_btn = pygame.Rect(
        button_margin,
        SH - button_size - button_margin,
        button_size,
        button_size
    )
    
    # Right movement button
    right_btn = pygame.Rect(
        button_margin * 2 + button_size,
        SH - button_size - button_margin,
        button_size,
        button_size
    )
    
    # Fire button
    fire_btn = pygame.Rect(
        SW - button_size - button_margin,
        SH - button_size - button_margin,
        button_size,
        button_size
    )
    
    # Time management
    time_limit = level_data["time_limit"]
    start_time = pygame.time.get_ticks()
    
    # Spawn enemies based on level design
    for enemy_data in level_data["enemies"]:
        enemy_type = enemy_data["type"]
        count = enemy_data["count"]
        
        for _ in range(count):
            if enemy_type == "boss":
                # Boss spawns at center horizontally, fixed vertical position
                enemy_dict = {
                    "type": enemy_type,
                    "x": SW // 2,  # Start at center
                    "y": ENEMY_TYPES[enemy_type]["fixed_y"],
                    "speed": ENEMY_TYPES[enemy_type]["speed"],
                    "size": ENEMY_TYPES[enemy_type]["size"],
                    "health": ENEMY_TYPES[enemy_type]["health"],
                    "max_health": ENEMY_TYPES[enemy_type]["health"],
                    "color": ENEMY_TYPES[enemy_type]["color"],
                    "score": ENEMY_TYPES[enemy_type]["score"],
                    "coin_chance": ENEMY_TYPES[enemy_type]["coin_chance"]
                }
            else:
                # Regular enemies spawn randomly
                enemy_dict = {
                    "type": enemy_type,
                    "x": random.randint(100, SW - 100),
                    "y": random.randint(-300, -100),
                    "speed": ENEMY_TYPES[enemy_type]["speed"],
                    "size": ENEMY_TYPES[enemy_type]["size"],
                    "health": ENEMY_TYPES[enemy_type]["health"],
                    "max_health": ENEMY_TYPES[enemy_type]["health"],
                    "color": ENEMY_TYPES[enemy_type]["color"],
                    "score": ENEMY_TYPES[enemy_type]["score"],
                    "coin_chance": ENEMY_TYPES[enemy_type]["coin_chance"]
                }
            
            # Add boss-specific properties
            if enemy_type == "boss":
                # Calculate safe movement bounds based on boss size and screen width
                boss_size = enemy_dict["size"]
                min_x = boss_size + 20  # 20 pixels margin from left edge
                max_x = SW - boss_size - 20  # 20 pixels margin from right edge
                
                enemy_dict.update({
                    "fire_timer": 0,
                    "fire_rate": ENEMY_TYPES[enemy_type]["fire_rate"],
                    "bullet_speed": ENEMY_TYPES[enemy_type]["bullet_speed"],
                    "bullet_damage": ENEMY_TYPES[enemy_type]["bullet_damage"],
                    "direction": random.choice([-1, 1]),  # 1 for right, -1 for left
                    "start_x": enemy_dict["x"],  # Original position for movement bounds
                    "movement_range": min(ENEMY_TYPES[enemy_type]["movement_range"], (max_x - min_x) // 2),
                    "move_speed": ENEMY_TYPES[enemy_type]["move_speed"],
                    "min_x": min_x,  # Minimum X position (left boundary)
                    "max_x": max_x   # Maximum X position (right boundary)
                })
            
            enemies.append(enemy_dict)
    
    # Game loop
    clock = pygame.time.Clock()
    game_over = False
    victory = False
    paused = False
    
    while not game_over and not victory:
        current_time = pygame.time.get_ticks()
        
        # Calculate elapsed time
        elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
        time_left = max(0, time_limit - elapsed_time)
        
        # Event handling
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    paused = not paused
                elif not paused:
                    if e.key == pygame.K_SPACE and not reloading and ammo > 0:
                        # Shoot with keyboard
                        bullets.append({
                            "x": px + player_width//2,
                            "y": py,
                            "speed": bullet_cfg["spd"],
                            "damage": bullet_cfg["damage"],
                            "color": bullet_cfg["color"]
                        })
                        ammo -= 1
                        if ammo == 0:
                            reloading = True
                            reload_timer = pygame.time.get_ticks()
            
            # Touch controls
            if touch_controls and not paused:
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if left_btn.collidepoint(e.pos):
                        left_pressed = True
                    elif right_btn.collidepoint(e.pos):
                        right_pressed = True
                    elif fire_btn.collidepoint(e.pos):
                        fire_pressed = True
                
                elif e.type == pygame.MOUSEBUTTONUP:
                    if left_btn.collidepoint(e.pos):
                        left_pressed = False
                    elif right_btn.collidepoint(e.pos):
                        right_pressed = False
                    elif fire_btn.collidepoint(e.pos):
                        fire_pressed = False
        
        if paused:
            # Draw pause screen
            screen.fill((0, 0, 0, 150))  # Semi-transparent overlay
            draw_text("PAUSED", title_f, YELLOW, (SW//2, SH//2 - 50))
            draw_text("Press ESC to resume", main_f, WHITE, (SW//2, SH//2 + 50))
            draw_text("Arrow Keys / A/D: Move", small_f, CYAN, (SW//2, SH//2 + 100))
            draw_text("Spacebar: Shoot", small_f, CYAN, (SW//2, SH//2 + 130))
            
            pygame.display.flip()
            clock.tick(60)
            continue
        
        # Player movement
        move_speed = ship["speed"]
        
        # Keyboard movement (always available)
        keys = pygame.key.get_pressed()
        keyboard_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        keyboard_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        
        # Combine keyboard and touch controls
        move_left = keyboard_left or (touch_controls and left_pressed)
        move_right = keyboard_right or (touch_controls and right_pressed)
        
        # Horizontal movement with boundaries
        if move_left and px > 0:
            px -= move_speed
        if move_right and px < SW - player_width:
            px += move_speed
        
        # Keep player at fixed vertical position (bottom of screen)
        py = SH - player_height - 50
        
        # Touch fire control
        if touch_controls and fire_pressed and not reloading and ammo > 0:
            current_time = pygame.time.get_ticks()
            if current_time - fire_cooldown > fire_cooldown_time:
                bullets.append({
                    "x": px + player_width//2,
                    "y": py,
                    "speed": bullet_cfg["spd"],
                    "damage": bullet_cfg["damage"],
                    "color": bullet_cfg["color"]
                })
                ammo -= 1
                fire_cooldown = current_time
                if ammo == 0:
                    reloading = True
                    reload_timer = pygame.time.get_ticks()
        
        # Reload
        if reloading:
            if pygame.time.get_ticks() - reload_timer > reload_time:
                ammo = ship["cap"]
                reloading = False
        
        # Draw background
        screen.blit(bg, (0, 0))
        
        # Update bullets
        for bullet in bullets[:]:
            bullet["y"] -= bullet["speed"]
            
            # Draw bullet
            pygame.draw.circle(screen, bullet["color"], (int(bullet["x"]), int(bullet["y"])), 5)
            pygame.draw.circle(screen, WHITE, (int(bullet["x"]), int(bullet["y"])), 5, 1)
            
            # Remove off-screen bullets
            if bullet["y"] < -10:
                bullets.remove(bullet)
        
        # Update enemy bullets
        for bullet in enemy_bullets[:]:
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]
            
            # Draw enemy bullet (different from player bullets)
            pygame.draw.circle(screen, bullet["color"], (int(bullet["x"]), int(bullet["y"])), 8)
            pygame.draw.circle(screen, WHITE, (int(bullet["x"]), int(bullet["y"])), 8, 2)
            
            # Player collision with enemy bullet
            player_center_x = px + player_width//2
            player_center_y = py + player_height//2
            bullet_distance = math.hypot(player_center_x - bullet["x"], player_center_y - bullet["y"])
            
            if bullet_distance < player_width//2 + 8:
                shield -= bullet["damage"]
                if shield <= 0:
                    game_over = True
                enemy_bullets.remove(bullet)
            
            # Remove off-screen bullets
            elif (bullet["x"] < -50 or bullet["x"] > SW + 50 or 
                  bullet["y"] < -50 or bullet["y"] > SH + 50):
                enemy_bullets.remove(bullet)
        
        # Update enemies
        enemies_alive = 0
        for enemy in enemies[:]:
            # Only regular enemies move down, boss stays at fixed position
            if enemy["type"] != "boss":
                enemy["y"] += enemy["speed"]
            enemies_alive += 1
            
            # Boss-specific movement and shooting
            if enemy["type"] == "boss":
                # Horizontal movement only (no vertical movement)
                enemy["x"] += enemy["direction"] * enemy["move_speed"]
                
                # Ensure boss stays within screen boundaries
                if enemy["x"] < enemy["min_x"]:
                    enemy["x"] = enemy["min_x"]
                    enemy["direction"] = 1  # Change direction to right
                elif enemy["x"] > enemy["max_x"]:
                    enemy["x"] = enemy["max_x"]
                    enemy["direction"] = -1  # Change direction to left
                
                # Change direction at movement range bounds (if still using that system)
                if enemy["x"] > enemy["start_x"] + enemy["movement_range"]:
                    enemy["direction"] = -1
                elif enemy["x"] < enemy["start_x"] - enemy["movement_range"]:
                    enemy["direction"] = 1
                
                # Boss shooting with warning effect
                time_since_last_shot = current_time - enemy.get("fire_timer", 0)
                
                # Draw warning indicator
                if time_since_last_shot > enemy["fire_rate"] * 1000 - 500:  # Last 500ms before shooting
                    pulse = abs(math.sin(current_time / 100)) * 255
                    s = pygame.Surface((enemy["size"] * 2 + 40, enemy["size"] * 2 + 40), pygame.SRCALPHA)
                    pygame.draw.circle(s, (255, 0, 0, int(pulse * 0.7)), 
                                     (enemy["size"] + 20, enemy["size"] + 20), 
                                     enemy["size"] + 20, 3)
                    screen.blit(s, (enemy["x"] - enemy["size"] - 20, enemy["y"] - enemy["size"] - 20))
                
                if time_since_last_shot > enemy["fire_rate"] * 1000:
                    # Shoot at player
                    dx = (px + player_width//2) - enemy["x"]
                    dy = (py + player_height//2) - enemy["y"]
                    distance = max(1, math.hypot(dx, dy))
                    
                    enemy_bullets.append({
                        "x": enemy["x"],
                        "y": enemy["y"] + enemy["size"],
                        "dx": dx/distance * enemy["bullet_speed"],
                        "dy": dy/distance * enemy["bullet_speed"],
                        "damage": enemy["bullet_damage"],
                        "color": PURPLE
                    })
                    enemy["fire_timer"] = current_time
            
            # Draw enemy
            if enemy["type"] in ENEMY_IMGS:
                img = ENEMY_IMGS[enemy["type"]]
                screen.blit(img, (enemy["x"] - enemy["size"], enemy["y"] - enemy["size"]))
            else:
                pygame.draw.circle(screen, enemy["color"], (int(enemy["x"]), int(enemy["y"])), enemy["size"])
                pygame.draw.circle(screen, WHITE, (int(enemy["x"]), int(enemy["y"])), enemy["size"], 2)
            
            # Draw health bar for enemies with health > 1
            if enemy["max_health"] > 1:
                health_ratio = enemy["health"] / enemy["max_health"]
                bar_width = enemy["size"] * 2
                bar_x = enemy["x"] - bar_width // 2
                bar_y = enemy["y"] - enemy["size"] - 15
                draw_progress_bar(bar_x, bar_y, bar_width, 8, health_ratio, GREEN)
            
            # Bullet collision
            for bullet in bullets[:]:
                distance = math.hypot(bullet["x"] - enemy["x"], bullet["y"] - enemy["y"])
                if distance < enemy["size"] + 5:
                    enemy["health"] -= bullet["damage"]
                    
                    if enemy["health"] <= 0:
                        # Enemy defeated
                        score += enemy["score"]
                        enemies_alive -= 1
                        
                        # Drop coin
                        if random.random() < enemy["coin_chance"]:
                            coins.append({
                                "x": enemy["x"],
                                "y": enemy["y"],
                                "value": enemy["score"] // 5 + 1
                            })
                        
                        # Remove enemy
                        enemies.remove(enemy)
                        
                        # Splitter enemy splits
                        if enemy["type"] == "splitter" and len(enemies) < 50:
                            for _ in range(2):
                                enemies.append({
                                    "type": "swarmer",
                                    "x": enemy["x"],
                                    "y": enemy["y"],
                                    "speed": ENEMY_TYPES["swarmer"]["speed"],
                                    "size": ENEMY_TYPES["swarmer"]["size"],
                                    "health": ENEMY_TYPES["swarmer"]["health"],
                                    "max_health": ENEMY_TYPES["swarmer"]["health"],
                                    "color": ENEMY_TYPES["swarmer"]["color"],
                                    "score": ENEMY_TYPES["swarmer"]["score"],
                                    "coin_chance": ENEMY_TYPES["swarmer"]["coin_chance"]
                                })
                    
                    bullets.remove(bullet)
                    break
            
            # Player collision
            player_center_x = px + player_width//2
            player_center_y = py + player_height//2
            player_distance = math.hypot(player_center_x - enemy["x"], player_center_y - enemy["y"])
            
            if player_distance < enemy["size"] + player_width//2:
                shield -= 1
                if shield <= 0:
                    game_over = True
                else:
                    # Push player back with screen boundary protection
                    dx = player_center_x - enemy["x"]
                    dy = player_center_y - enemy["y"]
                    dist = math.hypot(dx, dy) or 1
                    px += (dx / dist) * 20
                    
                    # Keep player within horizontal bounds after collision
                    px = max(0, min(SW - player_width, px))
                    
                    # Bounce enemy (except boss)
                    if enemy["type"] != "boss":
                        enemy["x"] -= (dx / dist) * 20
            
            # Remove regular enemies that go off screen (boss stays)
            if enemy["type"] != "boss" and enemy["y"] > SH + 100:
                enemies.remove(enemy)
        
        # Update coins
        for coin in coins[:]:
            coin["y"] += 3
            
            # Draw coin with animation
            coin_size = 16 + 4 * math.sin(pygame.time.get_ticks() / 200)
            pygame.draw.circle(screen, GOLD, (int(coin["x"]), int(coin["y"])), int(coin_size))
            pygame.draw.circle(screen, YELLOW, (int(coin["x"]), int(coin["y"])), int(coin_size * 0.7))
            
            # Collect coin
            player_center_x = px + player_width//2
            player_center_y = py + player_height//2
            if math.hypot(player_center_x - coin["x"], player_center_y - coin["y"]) < 40:
                collected_coins += coin["value"]
                coins.remove(coin)
            
            # Remove off-screen coins
            elif coin["y"] > SH + 50:
                coins.remove(coin)
        
        # Draw player
        screen.blit(p_img, (px, py))
        
        # Draw shield
        shield_ratio = shield / ship["shield"]
        draw_progress_bar(px + player_width//2 - 25, py - 20, 50, 8, shield_ratio, BLUE)
        
        # Draw HUD
        # Level info
        draw_text(f"Level {level_num}", stat_f, CYAN, (SW//2, 20))
        
        # Score
        draw_text(f"Score: {score}", main_f, WHITE, (20, 20), center=False)
        
        # Coins
        screen.blit(COIN_IMG, (20, 60))
        draw_text(f"{collected_coins}", main_f, GOLD, (60, 65), center=False)
        
        # Ammo
        ammo_text = f"Ammo: {ammo}/{ship['cap']}"
        if reloading:
            ammo_text += " (RELOADING)"
            reload_progress = (pygame.time.get_ticks() - reload_timer) / reload_time
            draw_progress_bar(20, 110, 200, 15, reload_progress, GREEN)
        draw_text(ammo_text, small_f, WHITE, (20, 100), center=False)
        
        # Time
        time_color = RED if time_left < 10 else YELLOW if time_left < 30 else WHITE
        draw_text(f"Time: {time_left}s", stat_f, time_color, (SW - 100, 20), center=False)
        
        # Enemies remaining
        draw_text(f"Enemies: {enemies_alive}", small_f, WHITE, (SW - 100, 60), center=False)
        
        # Shield
        screen.blit(pygame.transform.scale(HEART_IMG, (24, 24)), (SW - 150, 95))
        draw_text(f"{shield}", small_f, BLUE, (SW - 120, 100), center=False)
        
        # Draw touch control buttons if enabled
        if touch_controls:
            # Left movement button
            draw_touch_button(left_btn, "←", left_pressed)
            
            # Right movement button
            draw_touch_button(right_btn, "→", right_pressed)
            
            # Fire button
            draw_touch_button(fire_btn, "FIRE", fire_pressed, (200, 50, 50, 180))
            
            # Draw touch control hint
            draw_text("Touch Controls Active", tiny_f, YELLOW, (SW//2, SH - 120))
        
        # Check for victory
        if enemies_alive == 0:
            victory = True
        
        # Check for time out
        if time_left <= 0:
            game_over = True
        
        pygame.display.flip()
        clock.tick(60)
    
    # Game over or victory screen
    if victory:
        # Level completed
        reward_coins = level_data["coin_reward"]
        game_data = get_game_data()
        game_data["coins"] += reward_coins + collected_coins
        
        if level_num > game_data["levels_completed"]:
            game_data["levels_completed"] = level_num
        
        if level_num < 40:
            update_game_data("level", level_num + 1)
        
        # Check if boss was defeated
        if level_data.get("is_boss", False):
            update_game_data("boss_defeated", True)
        
        # Update high score
        if score > game_data["high_score"]:
            update_game_data("high_score", score)
        
        # Update coins
        update_game_data("coins", game_data["coins"])
        save_current_user()
        
        # Victory screen
        screen.fill(DARK)
        draw_text("VICTORY!", title_f, GREEN, (SW//2, SH//3))
        draw_text(f"Level {level_num} Completed!", main_f, CYAN, (SW//2, SH//2))
        draw_text(f"Score: {score}", stat_f, WHITE, (SW//2, SH//2 + 50))
        draw_text(f"Coins Earned: {reward_coins + collected_coins}", stat_f, GOLD, (SW//2, SH//2 + 100))
        
        # Show next level unlock
        if level_num < 40:
            draw_text(f"Next Level: {level_num + 1}", main_f, BLUE, (SW//2, SH//2 + 150))
        
        pygame.display.flip()
        pygame.time.wait(3000)
    
    elif game_over:
        # Update high score
        game_data = get_game_data()
        if score > game_data["high_score"]:
            update_game_data("high_score", score)
            save_current_user()
        
        # Game over screen
        screen.fill(DARK)
        draw_text("MISSION FAILED", title_f, RED, (SW//2, SH//3))
        draw_text(f"Level {level_num}", main_f, WHITE, (SW//2, SH//2))
        draw_text(f"Score: {score}", stat_f, WHITE, (SW//2, SH//2 + 50))
        draw_text(f"Coins Collected: {collected_coins}", stat_f, GOLD, (SW//2, SH//2 + 100))
        
        pygame.display.flip()
        pygame.time.wait(3000)

# --- 18. MAIN MENU ---
def main_menu():
    # Animated stars for background
    stars = []
    for _ in range(100):
        stars.append({
            "x": random.randint(0, SW),
            "y": random.randint(0, SH),
            "speed": random.uniform(0.1, 0.5),
            "size": random.randint(1, 3),
            "brightness": random.randint(100, 255)
        })
    
    while True:
        # Update stars
        for star in stars:
            star["y"] += star["speed"]
            if star["y"] > SH:
                star["y"] = 0
                star["x"] = random.randint(0, SW)
        
        # Draw background
        screen.fill(DARK)
        for star in stars:
            # Twinkling effect
            twinkle = int(50 * math.sin(pygame.time.get_ticks() / 1000 + star["x"]))
            brightness = star["brightness"] + twinkle
            brightness = max(50, min(255, brightness))
            pygame.draw.circle(screen, (brightness, brightness, brightness), 
                             (int(star["x"]), int(star["y"])), star["size"])
        
        # Title with glow
        title = title_f.render("GALAXY DEFENDER", True, CYAN)
        for offset in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            screen.blit(title, (SW//2 - title.get_width()//2 + offset[0], 
                              SH//4 + offset[1]))
        screen.blit(title, (SW//2 - title.get_width()//2, SH//4))
        
        # User status display
        user_status_rect = pygame.Rect(SW - 250, 20, 230, 40)
        if current_user:
            # Show logged in user with logout button
            pygame.draw.rect(screen, (30, 30, 60), user_status_rect, border_radius=8)
            pygame.draw.rect(screen, GREEN, user_status_rect, 2, border_radius=8)
            user_text = small_f.render(f"User: {current_user.username}", True, CYAN)
            screen.blit(user_text, (user_status_rect.x + 10, user_status_rect.centery - user_text.get_height()//2))
            
            # Logout button
            logout_rect = pygame.Rect(SW - 120, 70, 100, 30)
            draw_btn("LOGOUT", logout_rect, RED, logout_rect.collidepoint(pygame.mouse.get_pos()), tiny_f)
        else:
            # Show login prompt
            pygame.draw.rect(screen, (30, 30, 60), user_status_rect, border_radius=8)
            pygame.draw.rect(screen, YELLOW, user_status_rect, 2, border_radius=8)
            login_text = small_f.render("Not Logged In", True, YELLOW)
            screen.blit(login_text, (user_status_rect.x + 10, user_status_rect.centery - login_text.get_height()//2))
            
            # Login button
            login_btn_rect = pygame.Rect(SW - 120, 70, 100, 30)
            draw_btn("LOGIN", login_btn_rect, BLUE, login_btn_rect.collidepoint(pygame.mouse.get_pos()), tiny_f)
        
        # Player stats (only if logged in)
        if current_user:
            game_data = get_game_data()
            draw_text(f"Coins: {game_data['coins']}", stat_f, GOLD, (SW//2, SH//3 + 50))
            draw_text(f"High Score: {game_data['high_score']}", stat_f, GREEN, (SW//2, SH//3 + 90))
            draw_text(f"Level: {game_data['level']}/40", stat_f, BLUE, (SW//2, SH//3 + 130))
        else:
            draw_text("Please login to play!", stat_f, YELLOW, (SW//2, SH//3 + 50))
            draw_text("Your progress will be saved.", small_f, CYAN, (SW//2, SH//3 + 90))
        
        # Menu buttons
        m_pos = pygame.mouse.get_pos()
        
        buttons = [
            {"text": "PLAY", "rect": pygame.Rect(SW//2 - 150, SH//2, 300, 60), "color": GREEN, "enabled": current_user is not None},
            {"text": "SELECT LEVEL", "rect": pygame.Rect(SW//2 - 150, SH//2 + 80, 300, 60), "color": BLUE, "enabled": current_user is not None},
            {"text": "HANGAR", "rect": pygame.Rect(SW//2 - 150, SH//2 + 160, 300, 60), "color": PURPLE, "enabled": current_user is not None},
            {"text": "SETTINGS", "rect": pygame.Rect(SW//2 - 150, SH//2 + 240, 300, 60), "color": ORANGE, "enabled": current_user is not None},
            {"text": "QUIT", "rect": pygame.Rect(SW//2 - 150, SH//2 + 320, 300, 60), "color": RED, "enabled": True}
        ]
        
        for btn in buttons:
            if btn["enabled"]:
                draw_btn(btn["text"], btn["rect"], btn["color"], btn["rect"].collidepoint(m_pos))
            else:
                # Draw disabled button
                s = pygame.Surface((btn["rect"].width, btn["rect"].height), pygame.SRCALPHA)
                pygame.draw.rect(s, (*GRAY, 150), (0, 0, btn["rect"].width, btn["rect"].height), border_radius=12)
                pygame.draw.rect(s, WHITE, (0, 0, btn["rect"].width, btn["rect"].height), 2, border_radius=12)
                screen.blit(s, (btn["rect"].x, btn["rect"].y))
                
                t = main_f.render(btn["text"], True, (150, 150, 150))
                screen.blit(t, (btn["rect"].centerx - t.get_width()//2, btn["rect"].centery - t.get_height()//2))
        
        # Selected loadout (only if logged in)
        if current_user:
            game_data = get_game_data()
            y_offset = SH//2 + 400
            draw_text("Current Loadout:", small_f, WHITE, (SW//2, y_offset))
            draw_text(f"Ship: {game_data['selected']}", small_f, CYAN, (SW//2, y_offset + 30))
            draw_text(f"Bullet: {game_data['selected_bullet']}", small_f, CYAN, (SW//2, y_offset + 50))
            
            # Show touch controls status
            if game_data.get("touch_controls", False):
                draw_text("Touch Controls: ON", small_f, GREEN, (SW//2, y_offset + 80))
            else:
                draw_text("Touch Controls: OFF", small_f, YELLOW, (SW//2, y_offset + 80))
        
        pygame.display.flip()
        
        # Event handling
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                # Save before quitting
                if current_user:
                    save_current_user()
                pygame.quit()
                sys.exit()
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                # Handle user status buttons
                if current_user:
                    # Logout button
                    logout_rect = pygame.Rect(SW - 120, 70, 100, 30)
                    if logout_rect.collidepoint(e.pos):
                        logout_user()
                else:
                    # Login button
                    login_btn_rect = pygame.Rect(SW - 120, 70, 100, 30)
                    if login_btn_rect.collidepoint(e.pos):
                        if show_auth_screen():
                            # Login successful, continue
                            pass
                
                # Handle menu buttons
                if buttons[0]["rect"].collidepoint(e.pos) and buttons[0]["enabled"]:
                    main_game()
                elif buttons[1]["rect"].collidepoint(e.pos) and buttons[1]["enabled"]:
                    # Direct level selection
                    level_data = select_level()
                    if level_data:
                        main_game()
                elif buttons[2]["rect"].collidepoint(e.pos) and buttons[2]["enabled"]:
                    show_shop()
                elif buttons[3]["rect"].collidepoint(e.pos) and buttons[3]["enabled"]:
                    show_settings()
                elif buttons[4]["rect"].collidepoint(e.pos) and buttons[4]["enabled"]:
                    # Save before quitting
                    if current_user:
                        save_current_user()
                    pygame.quit()
                    sys.exit()

# --- 19. START GAME ---
if __name__ == "__main__":
    # Check if a user was previously logged in
    last_user = get_last_session()
    
    if last_user:
        # Auto-login the last user
        current_user = User(last_user)
        if os.path.exists(current_user.filepath):
            current_user.load()
            # Successfully loaded, go straight to main menu
            main_menu()
        else:
            # User file not found, clear bad session and show login
            clear_session()
            if show_auth_screen():
                main_menu()
    else:
        # No session found, proceed to normal login/register
        if show_auth_screen():
            main_menu()
