# Pigment Panic 3D — Fusion + Powerups + Steve Player (template-safe)
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import sys, os, math, random, time

# ------------------------------- Window / Projection -------------------------------
WINDOW_W, WINDOW_H = 1920, 1080
ASPECT = WINDOW_W / WINDOW_H
fovY = 120

LENGTH_OF_GRID = 600        # half-extent in both X and Y
SIZE_OF_GRID = 7            # checkerboard resolution

# ------------------------------- Player & Gameplay -------------------------------
PLAYER_RADIUS = 20.0
PLAYER_HEIGHT_Z = 0.0
PLAYER_STEP = 20.0
ROT_STEP_DEG = 6.0

# Smooth movement (hold-to-move; time-based)
MOVE_SPEED = 420.0              # units per second (forward/back)
ROT_SPEED_DEG_PER_SEC = 180.0   # degrees per second (left/right turn)
keys_down = {'w': False, 's': False, 'a': False, 'd': False}

BULLET_RADIUS = 6.0
BULLET_SPEED = 600.0
BULLET_TTL = 2.0

ENEMY_BASE_RADIUS = 18.0
ENEMY_HEAD_RADIUS = 10.0
ENEMY_BASE_HP = 1
ENEMY_WRONG_HIT_RADIUS_INC = 2.5
ENEMY_WRONG_HIT_HP_INC = 1
ENEMY_SPEED_BASE = 80.0
ENEMY_SPEED_WAVE_INC = 6.0

PARTICLE_COUNT_KILL = 18
PARTICLE_MINI_COUNT = 8

SCORE_PER_KILL = 25
SCORE_PER_HIT = 5
COMBO_BONUS_PER_HIT = 2
WAVE_START_COUNT = 4
WAVE_ENEMY_INC = 2

CHEAT_AIM_COOLDOWN = 0.18

# Power-ups
POWERUP_RADIUS = 14.0
POWERUP_FIELD_LIFETIME = 10.0
POWERUP_EFFECT_DURATION = 5.0
POWERUP_MIN_INTERVAL = 12.0
POWERUP_MAX_INTERVAL = 20.0

# Camera (3rd-person orbit of world origin, 1st-person behind player)
camera_pos = [0.0, 500.0, 500.0]
camera_angle = 0.0
camera_height = 500.0
camera_mode = 0  # 0 third-person, 1 first-person

FP_BACK_DIST = 60.0
FP_UP = 50.0

# ------------------------------- Colors -------------------------------
MILD_RED   = (0.8, 0.4, 0.4)
MILD_GREEN = (0.4, 0.8, 0.4)
MILD_BLUE  = (0.4, 0.4, 0.8)

WHITE = (1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0)
GREY  = (0.6, 0.6, 0.6)
GROUND_LIGHT = (1.0, 1.0, 1.0)
GROUND_DARK  = (0.82, 0.78, 0.95)
FENCE_COLOR  = (1.0, 0.9, 0.6)
UI_TEXT_COLOR= (0.95, 0.95, 0.95)

ACCENT1 = (0.9, 0.5, 0.2)   # lane stripe color X
ACCENT2 = (0.2, 0.8, 0.9)   # lane stripe color Y
POST_BASE = (0.95, 0.85, 0.4)
POST_CAP  = (0.95, 0.7, 0.2)
TOWER_BODY= (0.6, 0.65, 0.8)
TOWER_CAP = (0.95, 0.95, 1.0)

# Steve-ish palette
SKIN  = (0.67, 0.49, 0.37)
HAIR  = (0.15, 0.10, 0.06)
SHIRT = (0.10, 0.75, 0.75)
PANTS = (0.20, 0.25, 0.65)
BOOTS = (0.15, 0.15, 0.15)
EYE_W = (1.0, 1.0, 1.0)
EYE_B = (0.25, 0.45, 0.95)

# Power-up colors
CYAN   = (0.2, 1.0, 1.0)   # shield
ORANGE = (1.0, 0.6, 0.2)   # freeze

COLOR_NAMES = {
    'R': ('RED', MILD_RED),
    'G': ('GREEN', MILD_GREEN),
    'B': ('BLUE', MILD_BLUE),
}

# ------------------------------- Data Classes -------------------------------
class Player:
    def __init__(self):
        self.x, self.y, self.z = 0.0, 0.0, PLAYER_HEIGHT_Z
        self.yaw_deg = 0.0
        self.hp = 100
        self.max_hp = 100
        self.score = 0
        self.combo = 0
        self.best_combo = 0
        self.kills = 0
        self.ammo_key = 'R'
        self.aimbot = False
        self.cheat_unlimited_hp = False
        self.alive = True
        self.hit_cooldown_until = 0.0
        # Power-up state
        self.shield_until = 0.0

    def has_shield(self, now):
        return now < self.shield_until or self.cheat_unlimited_hp

class Bullet:
    __slots__ = ('x','y','z','dx','dy','speed','radius','color_key','created_at','ttl','alive')
    def __init__(self, x, y, z, dx, dy, color_key, now):
        self.x, self.y, self.z = x, y, z
        self.dx, self.dy = dx, dy
        self.speed = BULLET_SPEED
        self.radius = BULLET_RADIUS
        self.color_key = color_key
        self.created_at = now
        self.ttl = BULLET_TTL
        self.alive = True

class Enemy:
    __slots__ = ('x','y','z','radius','hp','color_key','alive','speed','pulse_phase')
    def __init__(self, x, y, color_key, wave_idx):
        self.x, self.y, self.z = x, y, ENEMY_BASE_RADIUS
        self.radius = ENEMY_BASE_RADIUS
        self.hp = ENEMY_BASE_HP
        self.color_key = color_key
        self.alive = True
        self.speed = ENEMY_SPEED_BASE + ENEMY_SPEED_WAVE_INC * (wave_idx - 1)
        self.pulse_phase = random.uniform(0.0, math.tau)

class Particle:
    __slots__ = ('x','y','z','dx','dy','dz','life','r','g','b')
    def __init__(self, x, y, z, base_color):
        self.x, self.y, self.z = float(x), float(y), float(z)
        self.dx = random.uniform(-3.0, 3.0)
        self.dy = random.uniform(-3.0, 3.0)
        self.dz = random.uniform( 0.0,  5.0)
        self.life = 1.0
        r,g,b = base_color
        self.r, self.g, self.b = r, g, b

class PowerUp:
    __slots__ = ('x','y','z','kind','spawned_at','alive')
    def __init__(self, x, y, kind, now):
        self.x, self.y, self.z = x, y, POWERUP_RADIUS
        self.kind = kind  # 'shield' or 'freeze'
        self.spawned_at = now
        self.alive = True

# ------------------------------- Global Game State -------------------------------
player = Player()
bullets = []
enemies = []
particles = []
powerups = []

current_wave = 0
pending_spawn = 0
next_spawn_time = 0.0

# Power-up timing
next_powerup_time = 0.0
freeze_enemies_until = 0.0

last_shot_time = 0.0

_prev_time = time.perf_counter()
game_paused = False
game_over = False

# ------------------------------- Helpers -------------------------------
def clamp(v, lo, hi): return max(lo, min(hi, v))

def ang_rad(d): return math.radians(d)

def normalize2d(dx, dy):
    mag = math.sqrt(dx*dx + dy*dy)
    if mag <= 1e-6: return (0.0, 0.0)
    return (dx/mag, dy/mag)

def dist2d(ax, ay, bx, by):
    dx, dy = ax-bx, ay-by
    return math.sqrt(dx*dx + dy*dy)

def inside_bounds(x, y, margin=0.0):
    r = LENGTH_OF_GRID - margin
    return (-r <= x <= r) and (-r <= y <= r)

# >>> Core fix: forward vector that matches glRotatef(+yaw around +Z) <<<
# Local +Y (the muzzle direction) rotated by yaw maps to world (-sin(yaw), cos(yaw)).
def yaw_forward(yaw_deg):
    r = math.radians(yaw_deg)
    return -math.sin(r), math.cos(r)

def color_key_to_rgb(k):
    return COLOR_NAMES.get(k, ('RED', MILD_RED))[1]

def nearest_enemy_to(px, py):
    best = None
    best_d = 1e9
    for e in enemies:
        if not e.alive: continue
        d = dist2d(px, py, e.x, e.y)
        if d < best_d:
            best_d = d
            best = e
    return best, best_d

def random_spawn_xy():
    radius_min = LENGTH_OF_GRID * 0.55
    radius_max = LENGTH_OF_GRID * 0.9
    angle = random.uniform(0.0, 2.0 * math.pi)
    r = random.uniform(radius_min, radius_max)
    return math.cos(angle) * r, math.sin(angle) * r

def safe_quit():
    """Leave GLUT cleanly; fall back to hard-exit without traceback."""
    try:
        glutLeaveMainLoop()
        return
    except Exception:
        pass
    try:
        wid = glutGetWindow()
        if wid:
            glutDestroyWindow(wid)
    except Exception:
        pass
    os._exit(0)

# ------------------------------- Rendering Utilities -------------------------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(*UI_TEXT_COLOR)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# -- Terrain (checkerboard with accent lanes, fences, posts, towers) --
def draw_terrain():
    cell_size = LENGTH_OF_GRID / SIZE_OF_GRID

    glBegin(GL_QUADS)
    for i in range(-SIZE_OF_GRID, SIZE_OF_GRID):
        for j in range(-SIZE_OF_GRID, SIZE_OF_GRID):
            if (i + j) % 2 == 0: cr, cg, cb = GROUND_LIGHT
            else:                 cr, cg, cb = GROUND_DARK
            glColor3f(cr, cg, cb)
            x1 = i * cell_size; y1 = j * cell_size
            x2 = (i + 1) * cell_size; y2 = (j + 1) * cell_size
            glVertex3f(x1, y1, 0)
            glVertex3f(x2, y1, 0)
            glVertex3f(x2, y2, 0)
            glVertex3f(x1, y2, 0)
    glEnd()

    # Axis lane stripes
    band = 24.0
    glBegin(GL_QUADS)
    glColor3f(*ACCENT1)  # X-axis stripe
    glVertex3f(-LENGTH_OF_GRID, -band, 0.2)
    glVertex3f( LENGTH_OF_GRID, -band, 0.2)
    glVertex3f( LENGTH_OF_GRID,  band, 0.2)
    glVertex3f(-LENGTH_OF_GRID,  band, 0.2)

    glColor3f(*ACCENT2)  # Y-axis stripe
    glVertex3f(-band, -LENGTH_OF_GRID, 0.2)
    glVertex3f( band, -LENGTH_OF_GRID, 0.2)
    glVertex3f( band,  LENGTH_OF_GRID, 0.2)
    glVertex3f(-band,  LENGTH_OF_GRID, 0.2)
    glEnd()

    # Perimeter fences
    glBegin(GL_QUADS)
    glColor3f(*FENCE_COLOR)
    # West
    glVertex3f(-LENGTH_OF_GRID, -LENGTH_OF_GRID, 0)
    glVertex3f(-LENGTH_OF_GRID,  LENGTH_OF_GRID, 0)
    glVertex3f(-LENGTH_OF_GRID,  LENGTH_OF_GRID, 100)
    glVertex3f(-LENGTH_OF_GRID, -LENGTH_OF_GRID, 100)
    # North
    glVertex3f(-LENGTH_OF_GRID, LENGTH_OF_GRID, 0)
    glVertex3f( LENGTH_OF_GRID, LENGTH_OF_GRID, 0)
    glVertex3f( LENGTH_OF_GRID, LENGTH_OF_GRID, 100)
    glVertex3f(-LENGTH_OF_GRID, LENGTH_OF_GRID, 100)
    # East
    glVertex3f(LENGTH_OF_GRID, -LENGTH_OF_GRID, 0)
    glVertex3f(LENGTH_OF_GRID,  LENGTH_OF_GRID, 0)
    glVertex3f(LENGTH_OF_GRID,  LENGTH_OF_GRID, 100)
    glVertex3f(LENGTH_OF_GRID, -LENGTH_OF_GRID, 100)
    # South
    glVertex3f(-LENGTH_OF_GRID, -LENGTH_OF_GRID, 0)
    glVertex3f( LENGTH_OF_GRID, -LENGTH_OF_GRID, 0)
    glVertex3f( LENGTH_OF_GRID, -LENGTH_OF_GRID, 100)
    glVertex3f(-LENGTH_OF_GRID, -LENGTH_OF_GRID, 100)
    glEnd()

    # Inner ring posts
    N = 24
    ring_r = LENGTH_OF_GRID * 0.72
    for k in range(N):
        ang = 2.0 * math.pi * (k / float(N))
        px = ring_r * math.cos(ang)
        py = ring_r * math.sin(ang)

        glPushMatrix()
        glTranslatef(px, py, 0.0)
        glRotatef(90, 1, 0, 0)
        glColor3f(*POST_BASE)
        gluCylinder(gluNewQuadric(), 6.0, 6.0, 40.0, 12, 1)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(px, py, 40.0)
        glColor3f(*POST_CAP)
        gluSphere(gluNewQuadric(), 6.0, 12, 12)
        glPopMatrix()

    # Corner towers
    for sx in (-1, 1):
        for sy in (-1, 1):
            tx = sx * LENGTH_OF_GRID * 0.9
            ty = sy * LENGTH_OF_GRID * 0.9
            glPushMatrix()
            glTranslatef(tx, ty, 0.0)
            # body
            glColor3f(*TOWER_BODY)
            glPushMatrix()
            glTranslatef(0, 0, 35)
            glScalef(40, 40, 70)
            glutSolidCube(1)
            glPopMatrix()
            # cap
            glTranslatef(0, 0, 80)
            glColor3f(*TOWER_CAP)
            gluSphere(gluNewQuadric(), 16, 16, 16)
            glPopMatrix()

# ---------- Steve-like player with right-hand blaster ----------
STEVE_SCALE = 2.0
STEVE_BODY_W = 12 * STEVE_SCALE
STEVE_BODY_D = 6  * STEVE_SCALE
STEVE_BODY_H = 18 * STEVE_SCALE
STEVE_HEAD   = 8  * STEVE_SCALE
STEVE_ARM_W  = 5  * STEVE_SCALE
STEVE_ARM_L  = 14 * STEVE_SCALE
STEVE_LEG_W  = 5  * STEVE_SCALE
STEVE_LEG_L  = 16 * STEVE_SCALE

# Blaster offsets relative to player local axes (+Y is forward in model space)
BLASTER_RIGHT  = (STEVE_BODY_W/2 + STEVE_ARM_W*0.8)     # x (to the right)
BLASTER_FORWARD= (STEVE_BODY_D/2 + 10.0)                # y (in front)
BLASTER_UP     = STEVE_BODY_H*0.65                      # z (arm height)

def draw_box(w, d, h, color):
    glColor3f(*color)
    glPushMatrix()
    glScalef(w, d, h)
    glutSolidCube(1.0)
    glPopMatrix()

def draw_steve_player():
    glPushMatrix()
    glTranslatef(player.x, player.y, 0.0)
    glRotatef(player.yaw_deg, 0, 0, 1)

    # Feet/legs (two boxes)
    for sx in (-1, 1):
        glPushMatrix()
        glTranslatef(sx*(STEVE_LEG_W*0.6), 0.0, STEVE_LEG_L*0.5)
        draw_box(STEVE_LEG_W, STEVE_LEG_W*0.9, STEVE_LEG_L, PANTS)
        glTranslatef(0, 0, -STEVE_LEG_L*0.5)
        glTranslatef(0, 0, 0.5*STEVE_LEG_W)
        draw_box(STEVE_LEG_W, STEVE_LEG_W, STEVE_LEG_W, BOOTS)
        glPopMatrix()

    # Torso
    glPushMatrix()
    glTranslatef(0, 0, STEVE_LEG_L + STEVE_BODY_H*0.5)
    draw_box(STEVE_BODY_W, STEVE_BODY_D, STEVE_BODY_H, SHIRT)
    glPopMatrix()

    # Head
    glPushMatrix()
    glTranslatef(0, 0, STEVE_LEG_L + STEVE_BODY_H + STEVE_HEAD*0.5)
    draw_box(STEVE_HEAD, STEVE_HEAD, STEVE_HEAD, SKIN)
    # Hair cap
    glTranslatef(0, 0, STEVE_HEAD*0.55)
    draw_box(STEVE_HEAD*0.98, STEVE_HEAD*0.98, STEVE_HEAD*0.1, HAIR)
    glPopMatrix()

    # Arms (left relaxed, right holds blaster straight forward)
    # Left arm
    glPushMatrix()
    glTranslatef(-STEVE_BODY_W*0.5 - STEVE_ARM_W*0.5, 0, STEVE_LEG_L + STEVE_BODY_H*0.75)
    draw_box(STEVE_ARM_W, STEVE_ARM_W*0.9, STEVE_ARM_L, SKIN)
    glPopMatrix()

    # Right arm + blaster
    glPushMatrix()
    glTranslatef(STEVE_BODY_W*0.5 + STEVE_ARM_W*0.5, 0, STEVE_LEG_L + STEVE_BODY_H*0.75)
    # upper arm
    draw_box(STEVE_ARM_W, STEVE_ARM_W*0.9, STEVE_ARM_L*0.5, SKIN)
    # forearm pushing forward (as a slim box)
    glTranslatef(0, STEVE_ARM_W*0.7, -STEVE_ARM_L*0.1)
    draw_box(STEVE_ARM_W*0.9, STEVE_ARM_W*1.6, STEVE_ARM_W*0.9, SKIN)
    # blaster (box barrel)
    glTranslatef(0, STEVE_ARM_W*1.2, 0)
    draw_box(STEVE_ARM_W*0.9, STEVE_ARM_W*2.6, STEVE_ARM_W*0.9, GREY)
    # muzzle ring
    glTranslatef(0, STEVE_ARM_W*1.4, 0)
    gluCylinder(gluNewQuadric(), STEVE_ARM_W*0.25, STEVE_ARM_W*0.25, STEVE_ARM_W*0.4, 10, 1)
    glPopMatrix()

    glPopMatrix()

def muzzle_world():
    """Compute world-space muzzle position from player pose (for bullet spawn & FP)."""
    fx, fy = yaw_forward(player.yaw_deg)        # forward (+Y when yaw=0) fixed
    rightx, righty = (fy, -fx)                  # +X to the model's right
    mx = player.x + rightx*BLASTER_RIGHT + fx*BLASTER_FORWARD
    my = player.y + righty*BLASTER_RIGHT + fy*BLASTER_FORWARD
    mz = BLASTER_UP
    return mx, my, mz

def draw_enemy_shape(e):
    t = time.perf_counter()
    pulsate = 1.0 + 0.12 * math.sin(2.0 * t + e.pulse_phase)
    body_r = e.radius * pulsate
    head_r = ENEMY_HEAD_RADIUS * pulsate
    glPushMatrix()
    glTranslatef(e.x, e.y, body_r)
    glColor3f(*color_key_to_rgb(e.color_key))
    gluSphere(gluNewQuadric(), body_r, 18, 18)
    glTranslatef(0, 0, body_r + head_r)
    glColor3f(0,0,0)
    gluSphere(gluNewQuadric(), head_r, 14, 14)
    glPopMatrix()

def draw_bullet_shape(b):
    glPushMatrix()
    glColor3f(*color_key_to_rgb(b.color_key))
    glTranslatef(b.x, b.y, b.z)
    glutSolidSphere(BULLET_RADIUS, 10, 10)
    glPopMatrix()

def draw_particle(p):
    life = clamp(p.life, 0.0, 1.0)
    glPushMatrix()
    glColor3f(p.r * life, p.g * life, p.b * life)
    glTranslatef(p.x, p.y, p.z)
    glutSolidSphere(2.0, 6, 6)
    glPopMatrix()

def draw_powerup(pu):
    if not pu.alive: return
    if pu.kind == 'shield':
        glColor3f(*CYAN)
        glPushMatrix()
        glTranslatef(pu.x, pu.y, pu.z)
        glutSolidCube(POWERUP_RADIUS*1.2)
        glPopMatrix()
    else:  # freeze
        glColor3f(*ORANGE)
        glPushMatrix()
        glTranslatef(pu.x, pu.y, pu.z)
        gluSphere(gluNewQuadric(), POWERUP_RADIUS, 12, 12)
        glPopMatrix()

# ------------------------------- Camera -------------------------------
def setup_camera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(fovY, ASPECT, 0.1, 2000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    if camera_mode == 0:
        # Orbiting third-person of world origin
        ex = 500.0 * math.cos(math.radians(camera_angle))
        ey = 500.0 * math.sin(math.radians(camera_angle))
        ez = camera_height
        camera_pos[0], camera_pos[1], camera_pos[2] = ex, ey, ez
        gluLookAt(ex, ey, ez, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    else:
        # First-person: track player's yaw; stick slightly behind to avoid clipping the model
        fx, fy = yaw_forward(player.yaw_deg)
        # Feel free to set FP_BACK_DIST to 0.0 for true nose-cam; 60 keeps the body visible.
        ex = player.x - fx * FP_BACK_DIST
        ey = player.y - fy * FP_BACK_DIST
        ez = FP_UP
        lx = player.x + fx * 10.0
        ly = player.y + fy * 10.0
        lz = FP_UP
        gluLookAt(ex, ey, ez, lx, ly, lz, 0.0, 0.0, 1.0)

# ------------------------------- UI Overlay -------------------------------
def ui_overlay(now):
    hp_text = "∞" if player.cheat_unlimited_hp else f"{player.hp}"
    mode = "1st" if camera_mode == 1 else "3rd"
    aimbot = "ON" if player.aimbot else "OFF"
    shield = "ON" if player.has_shield(now) else "OFF"
    freeze = "ON" if now < freeze_enemies_until else "OFF"
    draw_text(10, WINDOW_H-30, f"Pigment Panic 3D — Fusion | Mode: {mode} | HP: {hp_text} | Ammo: {COLOR_NAMES[player.ammo_key][0]}")
    draw_text(10, WINDOW_H-60, f"Score: {player.score}  Combo: {player.combo}  Best: {player.best_combo}  Wave: {current_wave}  Enemies: {sum(1 for e in enemies if e.alive)}")
    draw_text(10, WINDOW_H-90, f"Aimbot: {aimbot}  Shield: {shield}  Freeze: {freeze}  |  Controls: W/S move, A/D turn, 1/2/3 ammo, H aimbot, C infinite HP, P pause, R reset, RightClick camera")

# ------------------------------- Game Logic -------------------------------
def reset_game():
    global player, bullets, enemies, particles, powerups
    global current_wave, pending_spawn, next_spawn_time
    global game_over, game_paused, last_shot_time
    global next_powerup_time, freeze_enemies_until

    player = Player()
    bullets = []
    enemies = []
    particles = []
    powerups = []

    game_paused = False
    game_over = False
    last_shot_time = 0.0

    current_wave = 0
    pending_spawn = 0
    next_spawn_time = 0.0

    freeze_enemies_until = 0.0
    next_powerup_time = time.perf_counter() + random.uniform(POWERUP_MIN_INTERVAL, POWERUP_MAX_INTERVAL)

    start_next_wave(delay=0.5)

def start_next_wave(delay=1.5):
    global current_wave, pending_spawn, next_spawn_time
    current_wave += 1
    count = WAVE_START_COUNT + (current_wave-1) * WAVE_ENEMY_INC
    pending_spawn = count
    next_spawn_time = time.perf_counter() + delay

def spawn_enemy_once():
    global pending_spawn
    if pending_spawn <= 0: return
    color_key = random.choice(list(COLOR_NAMES.keys()))
    x, y = random_spawn_xy()
    enemies.append(Enemy(x, y, color_key, current_wave))
    pending_spawn -= 1

def try_spawn_powerup(now):
    global next_powerup_time
    if now < next_powerup_time: return
    kind = 'shield' if random.random() < 0.5 else 'freeze'
    x = random.uniform(-LENGTH_OF_GRID*0.8, LENGTH_OF_GRID*0.8)
    y = random.uniform(-LENGTH_OF_GRID*0.8, LENGTH_OF_GRID*0.8)
    powerups.append(PowerUp(x, y, kind, now))
    next_powerup_time = now + random.uniform(POWERUP_MIN_INTERVAL, POWERUP_MAX_INTERVAL)

def fire_bullet(now, target=None):
    global last_shot_time
    if now - last_shot_time < CHEAT_AIM_COOLDOWN: return

    fx, fy = yaw_forward(player.yaw_deg)  # fixed
    color_key = player.ammo_key
    bx, by, bz = muzzle_world()
    if target is not None:
        dx, dy = target.x - bx, target.y - by
        fx, fy = normalize2d(dx, dy)
        color_key = target.color_key

    bullets.append(Bullet(bx, by, bz, fx, fy, color_key, now))
    last_shot_time = now

def damage_player(amount, now):
    global game_over
    if player.cheat_unlimited_hp: return
    if player.has_shield(now): return
    if now < player.hit_cooldown_until: return
    player.hp -= amount
    player.hit_cooldown_until = now + 0.5
    if player.hp <= 0:
        player.hp = 0
        game_over = True

def spawn_death_particles(x, y, color_rgb, big=False):
    n = PARTICLE_COUNT_KILL if big else PARTICLE_MINI_COUNT
    z = 18.0
    for _ in range(n):
        particles.append(Particle(x, y, z, color_rgb))

def handle_bullet_enemy_collisions(now):
    for b in bullets:
        if not b.alive: continue
        for e in enemies:
            if not e.alive: continue
            d = dist2d(b.x, b.y, e.x, e.y)
            if d <= (b.radius + e.radius):
                if b.color_key == e.color_key:
                    e.hp -= 1
                    player.combo += 1
                    player.best_combo = max(player.best_combo, player.combo)
                    if e.hp <= 0:
                        e.alive = False
                        player.kills += 1
                        player.score += SCORE_PER_KILL + (COMBO_BONUS_PER_HIT * player.combo)
                        spawn_death_particles(e.x, e.y, color_key_to_rgb(e.color_key), big=True)
                    else:
                        player.score += SCORE_PER_HIT + (COMBO_BONUS_PER_HIT * max(player.combo-1,0))
                        spawn_death_particles(e.x, e.y, color_key_to_rgb(e.color_key), big=False)
                else:
                    e.radius += ENEMY_WRONG_HIT_RADIUS_INC
                    e.hp += ENEMY_WRONG_HIT_HP_INC
                    player.combo = 0
                b.alive = False
                break

def handle_player_enemy_collisions(now):
    for e in enemies:
        if not e.alive: continue
        if dist2d(player.x, player.y, e.x, e.y) <= (PLAYER_RADIUS + e.radius*0.9):
            damage_player(10, now)

def handle_player_powerup_pickups(now):
    global freeze_enemies_until
    for pu in powerups:
        if not pu.alive: continue
        # Expire on ground
        if now - pu.spawned_at > POWERUP_FIELD_LIFETIME:
            pu.alive = False
            continue
        # Pickup
        if dist2d(player.x, player.y, pu.x, pu.y) <= (PLAYER_RADIUS + POWERUP_RADIUS):
            if pu.kind == 'shield':
                player.shield_until = now + POWERUP_EFFECT_DURATION
            else:
                freeze_enemies_until = now + POWERUP_EFFECT_DURATION
            pu.alive = False

def update_enemies(dt, now):
    frozen = now < freeze_enemies_until
    if frozen: return
    for e in enemies:
        if not e.alive: continue
        vx, vy = player.x - e.x, player.y - e.y
        dx, dy = normalize2d(vx, vy)
        e.x += dx * e.speed * dt
        e.y += dy * e.speed * dt
        e.x = clamp(e.x, -LENGTH_OF_GRID*0.95, LENGTH_OF_GRID*0.95)
        e.y = clamp(e.y, -LENGTH_OF_GRID*0.95, LENGTH_OF_GRID*0.95)

def update_bullets(dt, now):
    for b in bullets:
        if not b.alive: continue
        b.x += b.dx * b.speed * dt
        b.y += b.dy * b.speed * dt
        if now - b.created_at > b.ttl:
            b.alive = False
            continue
        if not inside_bounds(b.x, b.y, margin=10.0):
            b.alive = False
            spawn_death_particles(b.x, b.y, color_key_to_rgb(b.color_key), big=False)

def cleanup_and_wave_progress():
    global enemies
    bullets[:] = [b for b in bullets if b.alive]
    keep = []
    for p in particles:
        p.x += p.dx; p.y += p.dy; p.z += p.dz
        p.dz -= 0.2
        p.life -= 0.04
        if p.life > 0.0:
            keep.append(p)
    particles[:] = keep
    if pending_spawn == 0 and all(not e.alive for e in enemies):
        start_next_wave(delay=2.0)

# Smooth tank-style motion — W/S along muzzle; A/D rotate in place
def update_player_motion(dt):
    if game_paused or game_over:
        return

    # Rotate
    if keys_down['a'] and not keys_down['d']:
        player.yaw_deg += ROT_SPEED_DEG_PER_SEC * dt
    elif keys_down['d'] and not keys_down['a']:
        player.yaw_deg -= ROT_SPEED_DEG_PER_SEC * dt

    # Translate exactly along muzzle direction
    move_dir = 0
    if keys_down['w']: move_dir += 1
    if keys_down['s']: move_dir -= 1
    if move_dir != 0:
        fx, fy = yaw_forward(player.yaw_deg)
        player.x += fx * MOVE_SPEED * dt * move_dir
        player.y += fy * MOVE_SPEED * dt * move_dir
        player.x = clamp(player.x, -LENGTH_OF_GRID*0.95, LENGTH_OF_GRID*0.95)
        player.y = clamp(player.y, -LENGTH_OF_GRID*0.95, LENGTH_OF_GRID*0.95)

def update_world(dt, now):
    global next_spawn_time
    # integrate smooth W/S/A/D controls
    update_player_motion(dt)

    # wave spawning
    if pending_spawn > 0 and now >= next_spawn_time:
        spawn_enemy_once()
        next_spawn_time = now + 0.12 + random.uniform(0.0, 0.04)

    # aimbot
    if player.aimbot and not game_paused and not game_over:
        tgt, _ = nearest_enemy_to(player.x, player.y)
        if tgt is not None and tgt.alive:
            fire_bullet(now, target=tgt)

    # power-ups: spawn + pickup
    try_spawn_powerup(now)
    handle_player_powerup_pickups(now)

    # updates
    update_enemies(dt, now)
    update_bullets(dt, now)
    handle_bullet_enemy_collisions(now)
    handle_player_enemy_collisions(now)
    cleanup_and_wave_progress()

# ------------------------------- GLUT Callbacks -------------------------------
def keyboardListener(key, x, y):
    global game_paused, game_over, camera_mode
    k = key.lower()

    # Clean exit
    if k == b'\x1b' or k == b'x':
        safe_quit()
        return

    if k == b'p':
        globals()['game_paused'] = not globals()['game_paused']
        return

    if k == b'r':
        reset_game()
        return

    if game_over:
        return

    if k == b'c':
        player.cheat_unlimited_hp = not player.cheat_unlimited_hp
        return
    if k == b'h':
        player.aimbot = not player.aimbot
        return

    if k == b'1':
        player.ammo_key = 'R'; return
    if k == b'2':
        player.ammo_key = 'G'; return
    if k == b'3':
        player.ammo_key = 'B'; return

    # Hold-to-move: press = set true
    if k == b'w': keys_down['w'] = True; return
    if k == b's': keys_down['s'] = True; return
    if k == b'a': keys_down['a'] = True; return
    if k == b'd': keys_down['d'] = True; return

def keyboardUpListener(key, x, y):
    k = key.lower()
    if k == b'w': keys_down['w'] = False
    if k == b's': keys_down['s'] = False
    if k == b'a': keys_down['a'] = False
    if k == b'd': keys_down['d'] = False

def specialKeyListener(key, x, y):
    global camera_angle, camera_height
    if key == GLUT_KEY_LEFT:
        camera_angle -= 5.0
    elif key == GLUT_KEY_RIGHT:
        camera_angle += 5.0
    elif key == GLUT_KEY_UP:
        camera_height += 10.0
    elif key == GLUT_KEY_DOWN:
        camera_height -= 10.0
    camera_height = clamp(camera_height, 40.0, 900.0)

def mouseListener(button, state, x, y):
    global camera_mode
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        now = time.perf_counter()
        if not game_over and not game_paused:
            if player.aimbot:
                tgt, _ = nearest_enemy_to(player.x, player.y)
                fire_bullet(now, target=tgt if tgt else None)
            else:
                fire_bullet(now, target=None)
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = 1 - camera_mode  # toggle 0<->1

def idle():
    global _prev_time
    now = time.perf_counter()
    dt = now - _prev_time
    _prev_time = now
    dt = min(max(dt, 0.0), 0.033)
    if not game_paused and not game_over:
        update_world(dt, now)
    glutPostRedisplay()

# ------------------------------- Main Render -------------------------------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_W, WINDOW_H)

    setup_camera()
    draw_terrain()

    # Entities
    draw_steve_player()
    for e in enemies:
        if e.alive: draw_enemy_shape(e)
    for b in bullets:
        if b.alive: draw_bullet_shape(b)
    for pu in powerups:
        draw_powerup(pu)
    for p in particles:
        draw_particle(p)

    ui_overlay(time.perf_counter())
    glutSwapBuffers()

# ------------------------------- Main -------------------------------
def main():
    random.seed(423)
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GL_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Pigment Panic 3D Fusion + Powerups + Steve Player")
    reset_game()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)   # key release for smooth controls
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glEnable(GL_DEPTH_TEST)
    glutMainLoop()

if __name__ == "__main__":
    main()
