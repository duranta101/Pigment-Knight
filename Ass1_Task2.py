from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time

# Window dimensions
win_width = 800
win_height = 600

# Particle format: [x, y, dx, dy, color, is_visible]
particles = []

# States
particle_speed = 0.1
is_blinking = False
is_paused = False
last_blink_time = time.time()
blink_interval = 0.5


def setup_scene():
    glClearColor(0, 0, 0, 1)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, win_width, 0, win_height)
    glMatrixMode(GL_MODELVIEW)


def draw_particles():
    glPointSize(6)
    glBegin(GL_POINTS)
    for p in particles:
        if p[5]:  # is_visible
            glColor3f(*p[4])  # color
            glVertex2f(p[0], p[1])  # position
    glEnd()


def update_particles():
    global last_blink_time
    if is_paused:
        return

    current_time = time.time()

    if is_blinking and (current_time - last_blink_time) >= blink_interval:
        for p in particles:
            p[5] = not p[5]  # toggle visibility
        last_blink_time = current_time

    for p in particles:
        p[0] += p[2] * particle_speed
        p[1] += p[3] * particle_speed

        # Bounce off window edges
        if p[0] >= win_width or p[0] <= 0:
            p[2] *= -1
        if p[1] >= win_height or p[1] <= 0:
            p[3] *= -1


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    draw_particles()
    glutSwapBuffers()


def animate():
    update_particles()
    glutPostRedisplay()


def handle_mouse(button, state, x, y):
    global is_blinking
    if is_paused or state != GLUT_DOWN:
        return

    if button == GLUT_RIGHT_BUTTON:
        dx = random.choice([-1, 1])
        dy = random.choice([-1, 1])
        color = (random.random(), random.random(), random.random())
        particles.append([x, win_height - y, dx, dy, color, True])  # y is inverted in OpenGL

    elif button == GLUT_LEFT_BUTTON:
        is_blinking = not is_blinking
        for p in particles:
            p[5] = True  # ensure visible when toggle starts


def handle_special_keys(key, x, y):
    global particle_speed
    if is_paused:
        return

    if key == GLUT_KEY_UP:
        particle_speed += 0.2
        print("Speed increased to:", round(particle_speed, 2))
    elif key == GLUT_KEY_DOWN:
        particle_speed = max(0.1, particle_speed - 0.2)
        print("Speed decreased to:", round(particle_speed, 2))


def handle_keyboard(key, x, y):
    global is_paused
    key = key.decode("utf-8")
    if key == ' ':
        is_paused = not is_paused
        print("Paused" if is_paused else "Resumed")


def reshape(w, h):
    global win_width, win_height
    win_width = w
    win_height = h
    glViewport(0, 0, w, h)
    setup_scene()


glutInit()
glutInitWindowSize(win_width, win_height)
glutInitWindowPosition(50, 50)
glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH)
glutCreateWindow(b"Amazing Box - Fullscreen Particle Animation")

setup_scene()

glutDisplayFunc(display)
glutIdleFunc(animate)
glutMouseFunc(handle_mouse)
glutSpecialFunc(handle_special_keys)
glutKeyboardFunc(handle_keyboard)
glutReshapeFunc(reshape)

glutMainLoop()