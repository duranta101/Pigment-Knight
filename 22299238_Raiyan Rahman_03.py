from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import math, random, time

# Window / projection
WIN_W, WIN_H = 1000, 800
ASPECT = WIN_W / WIN_H
fovY = 120
GRID_LENGTH = 600
TILE = 40
WALL_H = 140
rand_var = 423

# Camera (Z up)
camera_pos = (0, 500, 500)
camera_mode = "third"            # "third" or "first"
cam_orbit_angle = 45.0
cam_radius = 900.0
cam_height = 420.0
FP_EYE_OFFSET = (0.0, 28.0, 60.0)
FP_LOOK_AHEAD = 150.0

# Player / gameplay
player_pos = [0.0, 0.0, 0.0]
player_yaw = 0.0
PLAYER_STEP = 20.0               # W/S step distance
ROT_STEP_DEG = 10.0              # A/D yaw step

# Bullets
bullets = []                     # {"x","y","yaw"}
BULLET_SPEED = 22.0
BULLET_SIZE = 12.0

# Enemies (always 5)
enemies = []                     # {"x","y","phase"}
ENEMY_BASE_R = 26.0
ENEMY_HEAD_R = 10.0
ENEMY_SPEED = 1.4
RESPAWN_MARGIN = 80.0

# Cheat mode
cheat_mode = False
cheat_camera_follow = False
CHEAT_ROTATE_DEG_PER_SEC = 90.0
CHEAT_FIRE_COOLDOWN = 0.15
CHEAT_AIM_EPS_DEG = 10.0
_last_auto_shot = 0.0

# Game state
player_life = 5
game_score = 0
bullets_missed = 0
game_over = False

quadric = None
_start_time = time.time()
_prev_time = None

# -------- utils --------
def clamp(v, lo, hi): return lo if v < lo else hi if v > hi else v

def ang_wrap_deg(a):
    while a <= -180: a += 360
    while a > 180: a -= 360
    return a

def dist2_xy(ax, ay, bx, by):
    dx, dy = ax - bx, ay - by
    return dx*dx + dy*dy

def world_bounds_inner():
    w = GRID_LENGTH - RESPAWN_MARGIN
    return -w, w, -w, w

def random_spawn_xy():
    xmin, xmax, ymin, ymax = world_bounds_inner()
    return random.uniform(xmin, xmax), random.uniform(ymin, ymax)

# -------- text HUD --------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text: glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# -------- scene --------
def draw_checker_grid():
    xmin, xmax = -GRID_LENGTH, GRID_LENGTH
    ymin, ymax = -GRID_LENGTH, GRID_LENGTH
    x = xmin; toggle0 = 0
    while x < xmax:
        y = ymin; toggle = toggle0
        while y < ymax:
            glColor3f(1.0,1.0,1.0) if toggle == 0 else glColor3f(0.7,0.5,0.95)
            glBegin(GL_QUADS)
            glVertex3f(x, y, 0); glVertex3f(x+TILE, y, 0)
            glVertex3f(x+TILE, y+TILE, 0); glVertex3f(x, y+TILE, 0)
            glEnd()
            y += TILE; toggle ^= 1
        x += TILE; toggle0 ^= 1

def draw_walls():
    t = 12.0
    glColor3f(0,1,0)
    glPushMatrix(); glTranslatef(GRID_LENGTH, 0, WALL_H/2); glScalef(t, GRID_LENGTH*2, WALL_H); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(-GRID_LENGTH, 0, WALL_H/2); glScalef(t, GRID_LENGTH*2, WALL_H); glutSolidCube(1); glPopMatrix()
    glColor3f(0,0.6,1)
    glPushMatrix(); glTranslatef(0, GRID_LENGTH, WALL_H/2); glScalef(GRID_LENGTH*2, t, WALL_H); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(0, -GRID_LENGTH, WALL_H/2); glScalef(GRID_LENGTH*2, t, WALL_H); glutSolidCube(1); glPopMatrix()

def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], 0.0)
    glRotatef(player_yaw, 0,0,1)
    glColor3f(0.2,0.6,0.2)
    glPushMatrix(); glTranslatef(0,0,35); glScalef(28,18,70); glutSolidCube(1); glPopMatrix()
    glColor3f(0,0,0)
    glPushMatrix(); glTranslatef(0,0,89); gluSphere(quadric, 14, 16, 16); glPopMatrix()
    glColor3f(1.0,0.85,0.7)
    glPushMatrix(); glTranslatef(18,0,60); gluSphere(quadric, 6, 12, 12); glPopMatrix()
    glPushMatrix(); glTranslatef(-18,0,60); gluSphere(quadric, 6, 12, 12); glPopMatrix()
    glPushMatrix(); glTranslatef(18,0,58); glRotatef(90,0,1,0); gluCylinder(quadric, 4.5,4.5,28,12,1); glPopMatrix()
    glPushMatrix(); glTranslatef(-18,0,58); glRotatef(90,0,1,0); gluCylinder(quadric, 4.5,4.5,18,12,1); glPopMatrix()
    glColor3f(0.2,0.3,0.9)
    glPushMatrix(); glTranslatef(9,0,20);  glScalef(10,12,40); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(-9,0,20); glScalef(10,12,40); glutSolidCube(1); glPopMatrix()
    glColor3f(0.45,0.45,0.45)
    glPushMatrix(); glTranslatef(0,18,55); glRotatef(90,1,0,0); gluCylinder(quadric, 3.5,3.0,22,12,1); glPopMatrix()
    glPopMatrix()

def draw_enemy(e):
    t = time.time() - _start_time
    pulsate = 1.0 + 0.13*math.sin(2.0*t + e["phase"])
    body_r = ENEMY_BASE_R * pulsate
    head_r = ENEMY_HEAD_R * pulsate
    glPushMatrix()
    glTranslatef(e["x"], e["y"], body_r)
    glColor3f(1.0,0.1,0.1); gluSphere(quadric, body_r, 18, 18)
    glTranslatef(0,0, body_r + head_r)
    glColor3f(0,0,0);   gluSphere(quadric, head_r, 14, 14)
    glPopMatrix()

def draw_bullet(b):
    glColor3f(1,1,0)
    glPushMatrix()
    glTranslatef(b["x"], b["y"], 55.0)
    glRotatef(b["yaw"], 0,0,1)
    glTranslatef(0, BULLET_SIZE*0.5, 0)
    glScalef(BULLET_SIZE, BULLET_SIZE, BULLET_SIZE)
    glutSolidCube(1)
    glPopMatrix()

# -------- movement / actions --------
def translate_player(step):
    if game_over: return
    r = math.radians(player_yaw)
    nx = clamp(player_pos[0] + math.sin(r) * step, -GRID_LENGTH+20, GRID_LENGTH-20)
    ny = clamp(player_pos[1] + math.cos(r) * step, -GRID_LENGTH+20, GRID_LENGTH-20)
    player_pos[0], player_pos[1] = nx, ny

def rotate_player(delta_deg):
    if game_over: return
    global player_yaw
    player_yaw = ang_wrap_deg(player_yaw + delta_deg)

def fire_bullet():
    if game_over: return
    r = math.radians(player_yaw)
    start_x = player_pos[0] + math.sin(r) * 28.0
    start_y = player_pos[1] + math.cos(r) * 28.0
    bullets.append({"x": start_x, "y": start_y, "yaw": player_yaw})
    print("Bullet fired!")

# -------- gameplay updates --------
def bullet_hit_radius(): return (BULLET_SIZE * math.sqrt(3)) * 0.5

def hit_enemy_index(x, y):
    Rb = bullet_hit_radius()
    for i, e in enumerate(enemies):
        if dist2_xy(x, y, e["x"], e["y"]) <= (Rb + ENEMY_BASE_R)**2:
            return i
    return None

def respawn_enemy(i):
    ex, ey = random_spawn_xy()
    enemies[i]["x"], enemies[i]["y"] = ex, ey
    enemies[i]["phase"] = random.uniform(0, math.tau)

def increment_score():
    global game_score
    game_score += 1

def update_bullets(dt):
    global bullets, bullets_missed
    if not bullets: return
    new_list = []
    for b in bullets:
        r = math.radians(b["yaw"])
        b["x"] += math.sin(r) * BULLET_SPEED
        b["y"] += math.cos(r) * BULLET_SPEED
        if abs(b["x"]) > GRID_LENGTH or abs(b["y"]) > GRID_LENGTH:
            bullets_missed += 1
            print(f"Bullet missed: {bullets_missed}")
            continue
        idx = hit_enemy_index(b["x"], b["y"])
        if idx is not None:
            respawn_enemy(idx); increment_score(); continue
        new_list.append(b)
    bullets = new_list

def update_enemies(dt):
    global player_life, game_over
    if game_over: return
    for e in enemies:
        vx, vy = player_pos[0] - e["x"], player_pos[1] - e["y"]
        d = math.hypot(vx, vy) + 1e-6
        step = ENEMY_SPEED * dt * 60.0
        e["x"] += (vx/d) * step
        e["y"] += (vy/d) * step
        if dist2_xy(e["x"], e["y"], player_pos[0], player_pos[1]) < (ENEMY_BASE_R + 20.0)**2:
            player_life = max(0, player_life - 1)
            print(f"Remaining player lives: {player_life}")
            respawn_enemy(enemies.index(e))
            if player_life <= 0: set_game_over()

def nearest_enemy_in_sight():
    best_i, best_d2 = None, 1e18
    for i, e in enumerate(enemies):
        dx, dy = e["x"] - player_pos[0], e["y"] - player_pos[1]
        if dx == 0 and dy == 0: continue
        target = math.degrees(math.atan2(dx, dy))
        diff = abs(ang_wrap_deg(target - player_yaw))
        if diff <= CHEAT_AIM_EPS_DEG:
            d2 = dx*dx + dy*dy
            if d2 < best_d2: best_i, best_d2 = i, d2
    return best_i

def cheat_update(dt):
    global player_yaw, _last_auto_shot
    if not cheat_mode or game_over: return
    player_yaw = ang_wrap_deg(player_yaw + CHEAT_ROTATE_DEG_PER_SEC * dt)
    idx = nearest_enemy_in_sight()
    now = time.time()
    if idx is not None and (now - _last_auto_shot) >= CHEAT_FIRE_COOLDOWN:
        fire_bullet(); _last_auto_shot = now

def set_game_over():
    global game_over
    if game_over: return
    game_over = True
    print("Game over!")

def reset_game():
    global player_pos, player_yaw, player_life, game_score, bullets_missed, bullets, game_over
    player_pos[:] = [0.0, 0.0, 0.0]
    player_yaw = 0.0
    player_life = 5
    game_score = 0
    bullets_missed = 0
    bullets = []
    for i in range(5): respawn_enemy(i)
    game_over = False

# -------- input --------
def keyboardListener(key, x, y):
    global cheat_mode, cheat_camera_follow, _last_auto_shot, camera_mode
    k = key.lower() if isinstance(key, bytes) else key
    if k == b'w': translate_player(+PLAYER_STEP)
    if k == b's': translate_player(-PLAYER_STEP)
    if k == b'a': rotate_player(-ROT_STEP_DEG)
    if k == b'd': rotate_player(+ROT_STEP_DEG)
    if k == b'c': cheat_mode = not cheat_mode; _last_auto_shot = 0.0
    if k == b'v': cheat_camera_follow = not cheat_camera_follow
    if k == b'r': reset_game()

def specialKeyListener(key, x, y):
    global camera_pos, cam_height, cam_orbit_angle
    cx, cy, cz = camera_pos
    if key == GLUT_KEY_UP:   cam_height = clamp(cam_height + 14.0, 60.0, 1000.0)
    if key == GLUT_KEY_DOWN: cam_height = clamp(cam_height - 14.0, 20.0, 1000.0)
    if key == GLUT_KEY_LEFT: cam_orbit_angle -= 2.0
    if key == GLUT_KEY_RIGHT:cam_orbit_angle += 2.0
    camera_pos = (cx, cy, cz)

def mouseListener(button, state, x, y):
    global camera_mode
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN: fire_bullet()
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = "first" if camera_mode == "third" else "third"

# -------- camera & render --------
def setupCamera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 3000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    if camera_mode == "first":
        r = math.radians(player_yaw)
        ox, oy, oz = FP_EYE_OFFSET
        rx =  ox*math.cos(r) + oy*math.sin(r)
        ry = -ox*math.sin(r) + oy*math.cos(r)
        eyeX = player_pos[0] + rx; eyeY = player_pos[1] + ry; eyeZ = oz
        lookX = eyeX + math.sin(r) * FP_LOOK_AHEAD
        lookY = eyeY + math.cos(r) * FP_LOOK_AHEAD
        lookZ = oz
        if cheat_mode and cheat_camera_follow:
            lookX += math.sin(r) * 40.0; lookY += math.cos(r) * 40.0
        gluLookAt(eyeX, eyeY, eyeZ, lookX, lookY, lookZ, 0, 0, 1)
        cx, cy, cz = eyeX, eyeY, eyeZ
    else:
        ang = math.radians(cam_orbit_angle)
        cx = math.cos(ang) * cam_radius
        cy = math.sin(ang) * cam_radius
        cz = cam_height
        gluLookAt(cx, cy, cz, 0, 0, 0, 0, 0, 1)
    global camera_pos; camera_pos = (cx, cy, cz)

def idle():
    global _prev_time
    now = time.time()
    if _prev_time is None: _prev_time = now
    dt = now - _prev_time; _prev_time = now
    if not game_over:
        update_bullets(dt)
        update_enemies(dt)
        cheat_update(dt)
    glutPostRedisplay()

def draw_hud():
    draw_text(10, WIN_H-30,  f"Player Life Remaining: {player_life}")
    draw_text(10, WIN_H-60,  f"Game Score: {game_score}")
    draw_text(10, WIN_H-90,  f"Player Bullet Missed: {bullets_missed}")
    draw_text(10, WIN_H-120, f"Mode: {camera_mode.upper()}  |  Cheat: {'ON' if cheat_mode else 'OFF'}  |  Follow: {'ON' if cheat_camera_follow else 'OFF'}")
    if game_over:
        draw_text(WIN_W//2 - 120, WIN_H//2 + 20, "GAME OVER")
        draw_text(WIN_W//2 - 220, WIN_H//2 - 10, "Press R to Restart")

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)
    setupCamera()
    glPointSize(6)
    glBegin(GL_POINTS); glColor3f(1,1,1); glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0); glEnd()
    draw_checker_grid()
    draw_walls()
    for e in enemies: draw_enemy(e)
    draw_player()
    for b in bullets: draw_bullet(b)
    draw_hud()
    glutSwapBuffers()

# -------- init / main --------
def init_enemies():
    enemies.clear()
    for _ in range(5):
        x, y = random_spawn_xy()
        enemies.append({"x": x, "y": y, "phase": random.uniform(0, math.tau)})

def main():
    random.seed(42)
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Bullet Frenzy 3D (PyOpenGL)")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    global quadric; quadric = gluNewQuadric()
    init_enemies()
    glutMainLoop()

if __name__ == "__main__":
    main()
