from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import random
import math

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800

LENGTH_OF_GRID  = 600
SIZE_OF_GRID = 7
fovY = 120

player_pos = [0, 0, 0]
player_life = 5
player_score = 0
bullets_missed = 0
player_direction = 0
player_angle = 0
game_over = False

camera_pos = [0, 500, 500]
camera_angle = 0
camera_mode = 0  # 0 = 3rd-person view, 1 = 1st-person view

cheat_vision = False
cheat_mode = False

PLAYER_STEP = 10.0
BULLET_SPEED = 1.0
BULLET_SPAWN_OFFSET = 30.0
ENEMY_RESPAWN_RADIUS = LENGTH_OF_GRID // 2
ENEMY_BASE_SPEED = 0.01

bullets = []

enemies = []
NUM_ENEMIES = 5
for _ in range(NUM_ENEMIES):
    enemies.append([random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS),
                    random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS),
                    0, 1.0, 0.01])

# ---------------- Calming Color Palette ----------------
PLAYER_HEAD = (0.05, 0.05, 0.05)   # Almost black head & ears
PLAYER_BODY = (0.3, 0.3, 0.3)      # Medium-dark grey torso
PLAYER_LEGS = (0.0, 0.0, 0.0)      # Black legs
PLAYER_GUN = (1.0, 0.85, 0.3)      # Gun in light yellow

ENEMY_BODY = (0.6, 0.4, 0.7)  # Mild Joker purple
ENEMY_EYE = (0.3, 0.2, 0.9)   # Deep indigo
MILD_EYE_COLORS = [
    (0.8, 0.4, 0.4),  # Mild red
    (0.4, 0.8, 0.4),  # Mild green
    (0.4, 0.4, 0.8),  # Mild blue
]

BULLET_RED   = (0.8, 0.4, 0.4)   # Mild red
BULLET_GREEN = (0.4, 0.8, 0.4)   # Mild green
BULLET_BLUE  = (0.4, 0.4, 0.8)   # Mild blue

current_bullet_color = BULLET_RED  # default

GROUND_LIGHT = (1, 1, 1)
GROUND_DARK = (0.8, 0.8, 0.8)

FENCE_COLOR = (1.0, 0.9, 0.6)

UI_TEXT_COLOR    = (0.3, 0.6, 0.9)

# ---------------- Utility Functions ----------------
enemies = []
NUM_ENEMIES = 5
for _ in range(NUM_ENEMIES):
    enemies.append([
        random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS),
        random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS),
        0, 1.0, 0.01,
        random.choice(MILD_EYE_COLORS)
    ])

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(*UI_TEXT_COLOR)
    glRasterPos2f(x, y)
    for ch in text:
        GLUT.glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def clamp_to_grid(val):
    return max(-LENGTH_OF_GRID, min(LENGTH_OF_GRID, val))

def forward_xy(angle_deg: float):
    rad = math.radians(angle_deg)
    return math.sin(rad), math.cos(rad)

# Dimensions of Player
SCALE_OF_PLAYER = 1.5
RADIUS_OF_HEAD = 10 * SCALE_OF_PLAYER
WIDTH_OF_BODY = 20 * SCALE_OF_PLAYER
HEIGHT_OF_BODY = 30 * SCALE_OF_PLAYER
DEPTH_OF_BODY = 10 * SCALE_OF_PLAYER
RADIUS_OF_GUN = 5 * SCALE_OF_PLAYER
LENGTH_OF_GUN = 20 * SCALE_OF_PLAYER
RADIUS_OF_LEG = 7 * SCALE_OF_PLAYER
LENGTH_OF_LEG = 25 * SCALE_OF_PLAYER

def draw_player():
    pos_x, pos_y, pos_z = player_pos
    glPushMatrix()
    glTranslatef(pos_x, pos_y, pos_z)
    glRotatef(player_angle, 0, 0, 1)

    scale_factor = 2.0
    head_radius = RADIUS_OF_HEAD

    # BODY DIMENSIONS
    body_width = WIDTH_OF_BODY * scale_factor
    body_height = HEIGHT_OF_BODY * scale_factor
    body_depth = DEPTH_OF_BODY * scale_factor
    leg_radius = RADIUS_OF_LEG * scale_factor
    leg_length = LENGTH_OF_LEG * scale_factor

    # ---------------- HEAD ----------------
    glColor3f(*PLAYER_HEAD)
    glPushMatrix()
    glTranslatef(0, 0, body_height + head_radius)
    gluSphere(gluNewQuadric(), head_radius, 16, 16)

    # BAT EARS (triangular)
    ear_height = head_radius * 2.0
    ear_base = head_radius * 0.6

    # left ear
    glPushMatrix()
    glTranslatef(-head_radius*0.5, 0, head_radius*0.1)
    glRotatef(-20, 0, 1, 0)
    glBegin(GL_TRIANGLES)
    glVertex3f(0, 0, 0)
    glVertex3f(-ear_base, 0, 0)
    glVertex3f(0, 0, ear_height)
    glEnd()
    glPopMatrix()

    # right ear
    glPushMatrix()
    glTranslatef(head_radius*0.5, 0, head_radius*0.1)
    glRotatef(20, 0, 1, 0)
    glBegin(GL_TRIANGLES)
    glVertex3f(0, 0, 0)
    glVertex3f(ear_base, 0, 0)
    glVertex3f(0, 0, ear_height)
    glEnd()
    glPopMatrix()

    glPopMatrix()  # head

    # ---------------- BODY (tapered torso) ----------------
    glColor3f(*PLAYER_BODY)
    glPushMatrix()
    glTranslatef(0, 0, body_height/2)
    glScalef(body_width, body_depth*0.6, body_height)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(*PLAYER_LEGS)
    # left leg
    glPushMatrix()
    glTranslatef(-body_width*0.15, 0, 0)
    glRotatef(-10, 1, 0, 0)
    gluCylinder(gluNewQuadric(), leg_radius, leg_radius*0.6, leg_length, 10, 2)
    glPopMatrix()

    # right leg
    glPushMatrix()
    glTranslatef(body_width*0.15, 0, 0)
    glRotatef(-10, 1, 0, 0)
    gluCylinder(gluNewQuadric(), leg_radius, leg_radius*0.6, leg_length, 10, 2)
    glPopMatrix()

    # gun
    glColor3f(*PLAYER_GUN)
    glPushMatrix()
    glTranslatef(0, 0, body_height - leg_length / 2)
    glRotatef(0, 0, 1, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), RADIUS_OF_GUN * 2, RADIUS_OF_GUN * 0.8, LENGTH_OF_GUN * 1.5, 8, 2)
    glPopMatrix()

    glPopMatrix()  # pop player


def draw_enemies():
    for enemy in enemies:
        x, y, z, scale, dir, eye_color = enemy
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(scale, scale, scale)

        glColor3f(*ENEMY_BODY)
        glutSolidSphere(15 * 1.5, 20, 20)

        glTranslatef(0, 0, 20 * 1.5)
        glColor3f(*eye_color)
        glutSolidSphere(10 * 1.5, 20, 20)

        glPopMatrix()
        enemy[3] += enemy[4]
        if enemy[3] > 1.5 or enemy[3] < 0.5:
            enemy[4] *= -1


def draw_bullets():
    global bullets
    for bullet in bullets:
        bx, by, bz, angle, color = bullet
        glPushMatrix()
        glTranslatef(bx, by, bz)
        glColor3f(*color)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()



SIZE_OF_CELL = (LENGTH_OF_GRID / SIZE_OF_GRID)

def draw_checkerboard():
    cell_size = LENGTH_OF_GRID / SIZE_OF_GRID
    glBegin(GL_QUADS)
    for i in range(-SIZE_OF_GRID, SIZE_OF_GRID):
        for j in range(-SIZE_OF_GRID, SIZE_OF_GRID):
            if (i + j) % 2 == 0:
                glColor3f(*GROUND_LIGHT)
            else:
                glColor3f(*GROUND_DARK)
            x1 = i * cell_size
            y1 = j * cell_size
            x2 = (i + 1) * cell_size
            y2 = (j + 1) * cell_size
            glVertex3f(x1, y1, 0)
            glVertex3f(x2, y1, 0)
            glVertex3f(x2, y2, 0)
            glVertex3f(x1, y2, 0)
    glEnd()

    glBegin(GL_QUADS)
    # Fences
    glColor3f(*FENCE_COLOR)
    glVertex3f(-LENGTH_OF_GRID, -LENGTH_OF_GRID, 0)
    glVertex3f(-LENGTH_OF_GRID, LENGTH_OF_GRID, 0)
    glVertex3f(-LENGTH_OF_GRID, LENGTH_OF_GRID, 100)
    glVertex3f(-LENGTH_OF_GRID, -LENGTH_OF_GRID, 100)

    glColor3f(*FENCE_COLOR)
    glVertex3f(-LENGTH_OF_GRID, LENGTH_OF_GRID, 0)
    glVertex3f(LENGTH_OF_GRID, LENGTH_OF_GRID, 0)
    glVertex3f(LENGTH_OF_GRID, LENGTH_OF_GRID, 100)
    glVertex3f(-LENGTH_OF_GRID, LENGTH_OF_GRID, 100)

    glColor3f(*FENCE_COLOR)
    glVertex3f(LENGTH_OF_GRID, -LENGTH_OF_GRID, 0)
    glVertex3f(LENGTH_OF_GRID, LENGTH_OF_GRID, 0)
    glVertex3f(LENGTH_OF_GRID, LENGTH_OF_GRID, 100)
    glVertex3f(LENGTH_OF_GRID, -LENGTH_OF_GRID, 100)

    glColor3f(*FENCE_COLOR)
    glVertex3f(-LENGTH_OF_GRID, -LENGTH_OF_GRID, 0)
    glVertex3f(LENGTH_OF_GRID, -LENGTH_OF_GRID, 0)
    glVertex3f(LENGTH_OF_GRID, -LENGTH_OF_GRID, 100)
    glVertex3f(-LENGTH_OF_GRID, -LENGTH_OF_GRID, 100)
    glEnd()


def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if camera_mode == 0:
        # 3rd-person view
        gluLookAt(*camera_pos, 0, 0, 0, 0, 0, 1)
    else:
        # 1st-person view
        px, py, pz = player_pos
        fx, fy = forward_xy(player_angle)
        cx = px - 50 * fx
        cy = py - 50 * fy
        cz = pz + 50
        if cheat_vision and cheat_mode:
            cz += 50
        gluLookAt(cx, cy, cz, px + fx * 10, py + fy * 10, pz, 0, 0, 1)


def keyboardListener(key, x, y):
    global player_angle, player_pos, cheat_mode, cheat_vision, game_over, current_bullet_color

    if game_over:
        if key == b'n':   # restart on 'n'
            restart_game()
        return

    if key == b's':
        fx, fy = forward_xy(-player_angle)
        player_pos[0] = clamp_to_grid(player_pos[0] + PLAYER_STEP * fx)
        player_pos[1] = clamp_to_grid(player_pos[1] + PLAYER_STEP * fy)

    elif key == b'w':
        fx, fy = forward_xy(-player_angle)
        player_pos[0] = clamp_to_grid(player_pos[0] - PLAYER_STEP * fx)
        player_pos[1] = clamp_to_grid(player_pos[1] - PLAYER_STEP * fy)

    elif key == b'd':
        player_angle += 5

    elif key == b'a':
        player_angle -= 5

    elif key == b'c':
        cheat_mode = not cheat_mode

    elif key == b'v':
        cheat_vision = not cheat_vision

    # ---------- Bullet Color Switching ----------
    elif key == b'r':   # mild red
        current_bullet_color = BULLET_RED
    elif key == b'g':   # mild green
        current_bullet_color = BULLET_GREEN
    elif key == b'b':   # mild blue
        current_bullet_color = BULLET_BLUE

    # ---------- Restart Game ----------
    elif key == b'n':
        restart_game()



def specialKeyListener(key, x, y):
    global camera_pos, camera_angle
    if key == GLUT_KEY_UP:
        camera_pos[2] += 10
    elif key == GLUT_KEY_DOWN:
        camera_pos[2] -= 10
    elif key == GLUT_KEY_LEFT:
        camera_angle -= 5
    elif key == GLUT_KEY_RIGHT:
        camera_angle += 5

    camera_pos[0] = 500 * math.cos(math.radians(camera_angle))
    camera_pos[1] = 500 * math.sin(math.radians(camera_angle))


def mouseListener(button, state, x, y):
    global camera_mode
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        fx, fy = forward_xy(player_angle)
        spawn_x = player_pos[0] + fx * BULLET_SPAWN_OFFSET
        spawn_y = player_pos[1] + fy * BULLET_SPAWN_OFFSET
        bullets.append([spawn_x, spawn_y, player_pos[2], -player_angle + 180, current_bullet_color])
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = 1 - camera_mode



def move_bullets():
    global bullets, bullets_missed
    for bullet in bullets:
        fx, fy = forward_xy(bullet[3])  # angle
        bullet[0] += BULLET_SPEED * fx  # x
        bullet[1] += BULLET_SPEED * fy  # y
    prev_len = len(bullets)
    bullets[:] = [b for b in bullets if -LENGTH_OF_GRID < b[0] < LENGTH_OF_GRID and -LENGTH_OF_GRID < b[1] < LENGTH_OF_GRID]
    bullets_missed += prev_len - len(bullets)



def check_collisions():
    global enemies, bullets, player_life, player_score, game_over
    to_remove = []
    for i, bullet in enumerate(bullets):
        bx, by, _, _, _ = bullet
        for enemy in enemies:
            ex, ey, _, _, _, _ = enemy
            if abs(bx - ex) < 20 and abs(by - ey) < 20:
                player_score += 1
                # respawn enemy at new location
                enemy[0] = random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS)
                enemy[1] = random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS)
                enemy[5] = random.choice(MILD_EYE_COLORS)
                to_remove.append(i)
                break

    # remove bullets that hit
    bullets[:] = [b for idx, b in enumerate(bullets) if idx not in to_remove]

    # check player-enemy collisions
    for enemy in enemies:
        if abs(enemy[0] - player_pos[0]) < 20 and abs(enemy[1] - player_pos[1]) < 20:
            player_life -= 1
            enemy[0] = random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS)
            enemy[1] = random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS)
            enemy[5] = random.choice(MILD_EYE_COLORS)  # refresh on collision
            if player_life <= 0:
                game_over = True



def move_enemies_towards_player():
    for enemy in enemies:
        dx = player_pos[0] - enemy[0]
        dy = player_pos[1] - enemy[1]
        dist = math.hypot(dx, dy)
        if dist > 1e-3:
            enemy[0] += ENEMY_BASE_SPEED * (dx / dist)
            enemy[1] += ENEMY_BASE_SPEED * (dy / dist)


def restart_game():
    global player_life, player_score, bullets_missed, bullets, enemies, player_pos, player_angle, game_over
    player_life = 5
    player_score = 0
    bullets_missed = 0
    bullets.clear()
    player_pos = [0, 0, 0]
    player_angle = 0
    enemies.clear()
    for _ in range(NUM_ENEMIES):
        enemies.append([
            random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS),
            random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS),
            0, 1.0, 0.01,
            random.choice(MILD_EYE_COLORS)
        ])
    game_over = False


def idle():
    global player_angle, game_over
    if game_over:
        glutPostRedisplay()
        return
    if cheat_mode:
        fx, fy = forward_xy(player_angle)
        spawn_x = player_pos[0] + fx * BULLET_SPAWN_OFFSET
        spawn_y = player_pos[1] + fy * BULLET_SPAWN_OFFSET
        bullets.append([spawn_x, spawn_y, player_pos[2], player_angle, current_bullet_color])
        player_angle += 20

    move_bullets()
    move_enemies_towards_player()
    check_collisions()
    if player_life <= 0 or bullets_missed >= 10:
        game_over = True
    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    setup_camera()

    draw_checkerboard()
    draw_player()
    draw_enemies()
    draw_bullets()

    draw_text(50, 670, f"Player Life Remaining: {player_life}")
    draw_text(50, 650, f"Player Bullets Missed: {bullets_missed}")
    draw_text(50, 630, f"Game Score: {player_score}")

    if game_over:
        draw_text(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2, "Game Over! Press N to Restart")

    glutSwapBuffers()




glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
glutInitWindowPosition(0, 0)
glutCreateWindow(b"Bullet Frenzy")
glClearColor(1.0, 1.0, 1.0, 1.0)
glEnable(GL_DEPTH_TEST)
glutDisplayFunc(showScreen)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutMouseFunc(mouseListener)
glutIdleFunc(idle)
glutMainLoop()