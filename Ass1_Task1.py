from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

# Window dimensions
win_width = 800
win_height = 600

# Rain settings
drop_count = 300
drop_list = []
drop_tilt = 0
fall_velocity = 4

# Sky color (initial: night)
sky_tone = [0, 0, 0]

def initialize_drops():
    global drop_list
    drop_list = []
    for _ in range(drop_count):
        xpos = random.randint(-win_width//2, win_width//2)
        ypos = random.randint(-win_height//2, win_height//2 + 300)
        hue = random.choice([(0, 0, 1), (1, 1, 1)])
        drop_list.append([xpos, ypos, hue])

def render_rainfall():
    glBegin(GL_LINES)
    for drip in drop_list:
        x, y, col = drip
        glColor3f(*col)
        glVertex2f(x, y)
        glVertex2f(x + drop_tilt, y - 15)
    glEnd()

def update_drops():
    for drip in drop_list:
        drip[0] += drop_tilt
        drip[1] -= fall_velocity
        if drip[1] < -win_height//2:
            drip[0] = random.randint(-win_width//2, win_width//2)
            drip[1] = random.randint(win_height//2, win_height//2 + 300)
            drip[2] = random.choice([(0, 0, 1), (1, 1, 1)])

def draw_trees_row():
    spacing = 80
    base_y = -40
    top_y = 60
    start_x = -win_width // 2
    end_x = win_width // 2

    for pos in range(start_x, end_x, spacing):
        glBegin(GL_TRIANGLES)
        glColor3f(0, 1, 0)
        glVertex2f(pos, base_y)
        glColor3f(0, 1, 0)
        glVertex2f(pos + spacing, base_y)
        glColor3f(0, 0, 0)
        glVertex2f(pos + spacing / 2, top_y)
        glEnd()

def draw_background_land():
    glColor3f(0.5, 0.4, 0.1)
    glBegin(GL_TRIANGLES)
    glVertex2f(-win_width // 2, -40)
    glVertex2f(win_width // 2, -40)
    glVertex2f(win_width // 2, -win_height // 2)
    glVertex2f(-win_width // 2, -40)
    glVertex2f(win_width // 2, -win_height // 2)
    glVertex2f(-win_width // 2, -win_height // 2)
    glEnd()

def draw_ground():
    glColor3f(0.5, 0.4, 0.1)
    glBegin(GL_TRIANGLES)
    glVertex2f(-win_width//2, -100)
    glVertex2f(win_width//2, -100)
    glVertex2f(win_width//2, -win_height//2)
    glVertex2f(-win_width//2, -100)
    glVertex2f(win_width//2, -win_height//2)
    glVertex2f(-win_width//2, -win_height//2)
    glEnd()

def construct_building():
    # Roof
    glColor3f(0.4, 0.0, 0.7)
    glBegin(GL_TRIANGLES)
    glVertex2f(-150, 50)
    glVertex2f(150, 50)
    glVertex2f(0, 150)
    glEnd()

    # Wall
    glColor3f(1.0, 0.95, 0.85)
    glBegin(GL_TRIANGLES)
    glVertex2f(-150, -100)
    glVertex2f(150, -100)
    glVertex2f(150, 50)
    glVertex2f(-150, -100)
    glVertex2f(150, 50)
    glVertex2f(-150, 50)
    glEnd()

    # Door
    glColor3f(0.2, 0.6, 1.0)
    glBegin(GL_TRIANGLES)
    glVertex2f(-25, -100)
    glVertex2f(25, -100)
    glVertex2f(25, -30)
    glVertex2f(-25, -100)
    glVertex2f(25, -30)
    glVertex2f(-25, -30)
    glEnd()

    # Windows
    for offset in [-90, 60]:
        glColor3f(0.2, 0.6, 1.0)
        glBegin(GL_TRIANGLES)
        glVertex2f(offset, -20)
        glVertex2f(offset + 40, -20)
        glVertex2f(offset + 40, 20)
        glVertex2f(offset, -20)
        glVertex2f(offset + 40, 20)
        glVertex2f(offset, 20)
        glEnd()

        glColor3f(0, 0, 0)
        glBegin(GL_LINES)
        glVertex2f(offset + 20, -20)
        glVertex2f(offset + 20, 20)
        glVertex2f(offset, 0)
        glVertex2f(offset + 40, 0)
        glEnd()

def switch_theme(key, x, y):
    global sky_tone
    key = key.decode("utf-8")
    if key == 'd':
        for i in range(3):
            sky_tone[i] = min(1.0, sky_tone[i] + 0.05)
    elif key == 'n':
        for i in range(3):
            sky_tone[i] = max(0.0, sky_tone[i] - 0.05)

def handle_arrows(key, x, y):
    global drop_tilt
    if key == GLUT_KEY_LEFT:
        drop_tilt -= 1
    elif key == GLUT_KEY_RIGHT:
        drop_tilt += 1

def draw_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(*sky_tone, 1.0)
    glLoadIdentity()
    draw_background_land()
    draw_trees_row()
    draw_ground()
    construct_building()
    render_rainfall()
    glutSwapBuffers()

def refresh_loop():
    update_drops()
    glutPostRedisplay()

def configure():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-win_width // 2, win_width // 2, -win_height // 2, win_height // 2)
    glMatrixMode(GL_MODELVIEW)

def reshape(w, h):
    global win_width, win_height
    win_width = w
    win_height = h
    glViewport(0, 0, w, h)
    configure()


glutInit()
glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH)
glutInitWindowSize(win_width, win_height)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"Task 1 - Final: Gradient Trees, Rain, House")

configure()
initialize_drops()

glutDisplayFunc(draw_scene)
glutIdleFunc(refresh_loop)
glutKeyboardFunc(switch_theme)
glutSpecialFunc(handle_arrows)
glutReshapeFunc(reshape)

glutMainLoop()
