from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import random
import math

GRID_LENGTH = 600
GRID_SIZE = 7
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
fovY = 120

player_pos = [0, 0, 0]
player_direction = 0
player_angle = 0
player_life = 5
player_score = 0
bullets_missed = 0
game_over = False

camera_pos = [0, 500, 500]
camera_angle = 0
camera_mode = 0  # 0 = third-person, 1 = first-person

cheat_mode = False
cheat_vision = False

# -------------------- Tunables --------------------
BULLET_SPEED = 20.0
PLAYER_STEP = 10.0
BULLET_SPAWN_OFFSET = 30.0  # how far in front of player bullets spawn
ENEMY_BASE_SPEED = 0.03       # constant speed for enemies (lower than before)
ENEMY_RESPAWN_RADIUS = GRID_LENGTH // 2

bullets = []  # Each bullet: [x, y, z, angle]

enemies = []
NUM_ENEMIES = 5
for _ in range(NUM_ENEMIES):
    enemies.append([random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS),
                    random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS),
                    0, 1.0, 0.01])


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 1, 1)
    glRasterPos2f(x, y)
    for ch in text:
        GLUT.glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# -------------------- Helpers --------------------
# In our model, the player mesh at angle=0 visually faces +Y.
# So the *forward* vector for a given angle is (sin, cos), not (cos, sin).
# This brings movement, bullets, and camera into the same convention.

def forward_xy(angle_deg: float):
    rad = math.radians(angle_deg)
    return math.sin(rad), math.cos(rad)


def clamp_to_grid(val):
    return max(-GRID_LENGTH, min(GRID_LENGTH, val))


# Player dimensions
SCALE_OF_PLAYER = 1.5
RADIUS_OF_HEAD = 10 * SCALE_OF_PLAYER
WIDTH_OF_BODY = 20 * SCALE_OF_PLAYER
HEIGHT_OF_BODY = 30 * SCALE_OF_PLAYER
DEPTH_OF_BODY = 10 * SCALE_OF_PLAYER
RADIUS_OF_ARM = 5 * SCALE_OF_PLAYER
LENGTH_OF_ARM = 20 * SCALE_OF_PLAYER
RADIUS_OF_LEG = 7 * SCALE_OF_PLAYER
LENGTH_OF_LEG = 25 * SCALE_OF_PLAYER

def draw_player():
    pos_x, pos_y, pos_z = player_pos
    glPushMatrix()
    glTranslatef(pos_x, pos_y, pos_z)
    glRotatef(player_angle, 0, 0, 1)

    # head
    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(0, 0, HEIGHT_OF_BODY + RADIUS_OF_HEAD)
    gluSphere(gluNewQuadric(), RADIUS_OF_HEAD, 12, 12)
    glPopMatrix()

    # body
    glColor3f(0.5, 0.6, 0.3)
    glPushMatrix()
    glTranslatef(0, 0, HEIGHT_OF_BODY / 2)
    glScalef(WIDTH_OF_BODY, DEPTH_OF_BODY, HEIGHT_OF_BODY)
    glutSolidCube(1.0)
    glPopMatrix()

    # arm (left)
    glColor3f(1.0, 0.8, 0.6)
    glPushMatrix()
    glTranslatef(-WIDTH_OF_BODY / 2 - RADIUS_OF_ARM, 0, HEIGHT_OF_BODY - LENGTH_OF_ARM / 2)
    glRotatef(-20, 0, 1, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), RADIUS_OF_ARM, RADIUS_OF_ARM * 0.8, LENGTH_OF_ARM, 8, 2)
    glPopMatrix()

    # arm (right)
    glColor3f(1.0, 0.8, 0.6)
    glPushMatrix()
    glTranslatef(WIDTH_OF_BODY / 2 + RADIUS_OF_ARM, 0, HEIGHT_OF_BODY - LENGTH_OF_ARM / 2)
    glRotatef(20, 0, 1, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), RADIUS_OF_ARM, RADIUS_OF_ARM * 0.8, LENGTH_OF_ARM, 8, 2)
    glPopMatrix()

    # gun
    glColor3f(0.8, 0.8, 0.8)
    glPushMatrix()
    glTranslatef(0, 0, HEIGHT_OF_BODY - LENGTH_OF_ARM / 2)
    glRotatef(0, 0, 1, 0)
    glRotatef(90, 1, 0, 0)
    gun_quad = gluNewQuadric()
    gluCylinder(gun_quad, RADIUS_OF_ARM * 1.5, 0.0, LENGTH_OF_ARM * 1.5, 8, 2)
    glPopMatrix()

    # leg (left)
    glColor3f(0, 0, 1)
    glPushMatrix()
    glTranslatef(-WIDTH_OF_BODY / 4, 0, 0)
    glRotatef(90, 0, 0, 1)
    gluCylinder(gluNewQuadric(), RADIUS_OF_LEG, RADIUS_OF_LEG * 0.6, LENGTH_OF_LEG, 8, 2)
    glPopMatrix()

    # leg (right)
    glColor3f(0, 0, 1)
    glPushMatrix()
    glTranslatef(WIDTH_OF_BODY / 4, 0, 0)
    glRotatef(90, 0, 0, 1)
    gluCylinder(gluNewQuadric(), RADIUS_OF_LEG, RADIUS_OF_LEG * 0.6, LENGTH_OF_LEG, 8, 2)
    glPopMatrix()

    glPopMatrix()


def draw_enemies():
    for enemy in enemies:
        x, y, z, scale, dir = enemy
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(scale, scale, scale)
        glColor3f(1, 0, 0)
        glutSolidSphere(15, 20, 20)
        glTranslatef(0, 0, 20)
        glColor3f(0, 0, 0)
        glutSolidSphere(10, 20, 20)
        glPopMatrix()
        enemy[3] += enemy[4]
        if enemy[3] > 1.5 or enemy[3] < 0.5:
            enemy[4] *= -1


def draw_bullets():
    for bullet in bullets:
        x, y, z, angle = bullet
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(angle, 0, 0, 1)
        glColor3f(1, 0, 0)
        glutSolidCube(20)
        glPopMatrix()


CELL_SIZE = (GRID_LENGTH / GRID_SIZE)


def draw_checkerboard():
    cell_size = GRID_LENGTH / GRID_SIZE
    glBegin(GL_QUADS)
    for i in range(-GRID_SIZE, GRID_SIZE):
        for j in range(-GRID_SIZE, GRID_SIZE):
            if (i + j) % 2 == 0:
                glColor3f(1, 1, 1)
            else:
                glColor3f(0.7, 0.5, 0.9)
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
    # Blue border
    glColor3f(0, 0, 1)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 100)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 100)
    # Cyan border
    glColor3f(0, 1, 1)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 100)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 100)
    # Green border
    glColor3f(0, 1, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 100)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 100)
    # White border
    glColor3f(1, 1, 1)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 100)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 100)
    glEnd()


def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if camera_mode == 0:
        # Third-person: orbiting camera determined by camera_pos
        gluLookAt(*camera_pos, 0, 0, 0, 0, 0, 1)
    else:
        # First-person: behind/above the player, aligned with forward vector
        px, py, pz = player_pos
        fx, fy = forward_xy(player_angle)
        cx = px - 50 * fx
        cy = py - 50 * fy
        cz = pz + 50
        if cheat_vision and cheat_mode:
            cz += 50
        gluLookAt(cx, cy, cz, px + fx * 10, py + fy * 10, pz, 0, 0, 1)


def keyboardListener(key, x, y):
    global player_angle, player_pos, cheat_mode, cheat_vision, game_over
    if game_over:
        if key == b'r':
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
    elif key == b'r':
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
    # Recompute orbit position
    camera_pos[0] = 500 * math.cos(math.radians(camera_angle))
    camera_pos[1] = 500 * math.sin(math.radians(camera_angle))


def mouseListener(button, state, x, y):
    global camera_mode
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        # Spawn bullet slightly in front of the player along forward dir
        fx, fy = forward_xy(player_angle)
        spawn_x = player_pos[0] + fx * BULLET_SPAWN_OFFSET
        spawn_y = player_pos[1] + fy * BULLET_SPAWN_OFFSET
        bullets.append([spawn_x, spawn_y, player_pos[2], -player_angle+180])
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = 1 - camera_mode


def move_bullets():
    global bullets, bullets_missed
    for bullet in bullets:
        fx, fy = forward_xy(bullet[3])
        bullet[0] += BULLET_SPEED * fx
        bullet[1] += BULLET_SPEED * fy
    prev_len = len(bullets)
    bullets[:] = [b for b in bullets if -GRID_LENGTH < b[0] < GRID_LENGTH and -GRID_LENGTH < b[1] < GRID_LENGTH]
    bullets_missed += prev_len - len(bullets)


def check_collisions():
    global enemies, bullets, player_life, player_score, game_over
    to_remove = []
    for i, bullet in enumerate(bullets):
        bx, by, _, _ = bullet
        for enemy in enemies:
            ex, ey, _, _, _ = enemy
            if abs(bx - ex) < 20 and abs(by - ey) < 20:
                player_score += 1
                enemy[0] = random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS)
                enemy[1] = random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS)
                to_remove.append(i)
                break
    bullets[:] = [b for idx, b in enumerate(bullets) if idx not in to_remove]

    for enemy in enemies:
        if abs(enemy[0] - player_pos[0]) < 20 and abs(enemy[1] - player_pos[1]) < 20:
            player_life -= 1
            enemy[0] = random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS)
            enemy[1] = random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS)
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
        enemies.append([random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS),
                        random.randint(-ENEMY_RESPAWN_RADIUS, ENEMY_RESPAWN_RADIUS),
                        0, 1.0, 0.01])
    game_over = False


def idle():
    global player_angle, game_over
    if game_over:
        glutPostRedisplay()
        return
    if cheat_mode:
        # Auto-fire from gun front while rotating
        fx, fy = forward_xy(player_angle)
        spawn_x = player_pos[0] + fx * BULLET_SPAWN_OFFSET
        spawn_y = player_pos[1] + fy * BULLET_SPAWN_OFFSET
        bullets.append([spawn_x, spawn_y, player_pos[2], player_angle])
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
        draw_text(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2, "Game Over! Press R to Restart")

    glutSwapBuffers()


# -------------------- Boot --------------------

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
glutInitWindowPosition(0, 0)
glutCreateWindow(b"Bullet Frenzy")
glEnable(GL_DEPTH_TEST)
glutDisplayFunc(showScreen)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutMouseFunc(mouseListener)
glutIdleFunc(idle)
glutMainLoop()
