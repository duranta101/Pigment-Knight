from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import sys

WIDTH, HEIGHT = 400, 500
BOWL_WIDTH = 100
BOWL_HEIGHT = 15
BOWL_Y = 10
BOWL_SPEED = 20

DIAMOND_SIZE = 12
DIAMOND_SPEED_START = 0.4
DIAMOND_SPEED_INCREMENT = 0.05

WHITE = (1, 1, 1)
RED = (1, 0, 0)
TEAL = (0, 1, 1)
YELLOW = (1, 1, 0)

bowl_x = WIDTH // 2
diamond_x = random.randint(DIAMOND_SIZE, WIDTH - DIAMOND_SIZE)
diamond_y = HEIGHT
diamond_speed = DIAMOND_SPEED_START
diamond_color = (random.random(), random.random(), random.random())

score = 0
game_over = False
paused = False


def draw_pixel(x, y, color):
    glColor3f(*color)
    glBegin(GL_POINTS)
    glVertex2i(int(x), int(y))
    glEnd()


def draw_midpoint_line(x0, y0, x1, y1, color):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        draw_pixel(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def draw_diamond(x, y, color):
    draw_midpoint_line(x, y - DIAMOND_SIZE, x + DIAMOND_SIZE, y, color)
    draw_midpoint_line(x + DIAMOND_SIZE, y, x, y + DIAMOND_SIZE, color)
    draw_midpoint_line(x, y + DIAMOND_SIZE, x - DIAMOND_SIZE, y, color)
    draw_midpoint_line(x - DIAMOND_SIZE, y, x, y - DIAMOND_SIZE, color)


def draw_bowl(x, y, color):
    half = BOWL_WIDTH // 4
    quarter = BOWL_WIDTH // 2
    draw_midpoint_line(x - half, y, x + half, y, color)
    draw_midpoint_line(x - half, y, x - quarter, y + BOWL_HEIGHT, color)
    draw_midpoint_line(x + half, y, x + quarter, y + BOWL_HEIGHT, color)
    draw_midpoint_line(x - quarter, y + BOWL_HEIGHT, x + quarter, y + BOWL_HEIGHT, color)


def draw_buttons():
    # Left Arrow Button
    draw_midpoint_line(20, HEIGHT - 30, 50, HEIGHT - 30, TEAL)
    draw_midpoint_line(20, HEIGHT - 30, 30, HEIGHT - 40, TEAL)
    draw_midpoint_line(20, HEIGHT - 30, 30, HEIGHT - 20, TEAL)

    # Play/Pause
    if paused:
        draw_midpoint_line(190, HEIGHT - 40, 190, HEIGHT - 20, YELLOW)
        draw_midpoint_line(190, HEIGHT - 20, 210, HEIGHT - 30, YELLOW)
        draw_midpoint_line(210, HEIGHT - 30, 190, HEIGHT - 40, YELLOW)
    else:
        draw_midpoint_line(185, HEIGHT - 40, 185, HEIGHT - 20, YELLOW)
        draw_midpoint_line(195, HEIGHT - 40, 195, HEIGHT - 20, YELLOW)

    # Cross Button
    draw_midpoint_line(360, HEIGHT - 40, 380, HEIGHT - 20, RED)
    draw_midpoint_line(360, HEIGHT - 20, 380, HEIGHT - 40, RED)


def update():
    global diamond_y, diamond_x, score, diamond_speed, diamond_color, game_over

    if not game_over and not paused:
        diamond_y -= diamond_speed

        if (
            bowl_x - BOWL_WIDTH // 2 <= diamond_x <= bowl_x + BOWL_WIDTH // 2
            and BOWL_Y <= diamond_y <= BOWL_Y + DIAMOND_SIZE
        ):
            score += 1
            print(f"Score: {score}")
            diamond_y = HEIGHT
            diamond_x = random.randint(DIAMOND_SIZE, WIDTH - DIAMOND_SIZE)
            diamond_color = (random.random(), random.random(), random.random())
            diamond_speed += DIAMOND_SPEED_INCREMENT

        if diamond_y < 0:
            print(f"Game Over! Final Score: {score}")
            game_over = True

    glutPostRedisplay()


def keyboard(key, x, y):
    if key == b'\x1b':
        print(f"Goodbye! Final Score: {score}")
        sys.exit()


def special_keys(key, x, y):
    global bowl_x
    if not game_over and not paused:
        if key == GLUT_KEY_LEFT and bowl_x - BOWL_WIDTH // 2 - BOWL_SPEED >= 0:
            bowl_x -= BOWL_SPEED
        elif key == GLUT_KEY_RIGHT and bowl_x + BOWL_WIDTH // 2 + BOWL_SPEED <= WIDTH:
            bowl_x += BOWL_SPEED


def mouse(button, state, x, y):
    global paused, game_over, diamond_x, diamond_y, diamond_speed, diamond_color, bowl_x, score

    if state == GLUT_DOWN:
        y = HEIGHT - y

        if 20 <= x <= 50 and HEIGHT - 40 <= y <= HEIGHT - 20:
            # Restart
            paused = False
            game_over = False
            score = 0
            bowl_x = WIDTH // 2
            diamond_x = random.randint(DIAMOND_SIZE, WIDTH - DIAMOND_SIZE)
            diamond_y = HEIGHT
            diamond_speed = DIAMOND_SPEED_START
            diamond_color = (random.random(), random.random(), random.random())
            print("Starting Over")

        elif 185 <= x <= 210 and HEIGHT - 40 <= y <= HEIGHT - 20:
            paused = not paused

        elif 360 <= x <= 380 and HEIGHT - 40 <= y <= HEIGHT - 20:
            print(f"Goodbye! Final Score: {score}")
            glutDestroyWindow(glutGetWindow())
            import threading
            threading.Timer(0.1, sys.exit).start()


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    draw_buttons()
    draw_bowl(bowl_x, BOWL_Y, RED if game_over else WHITE)
    if not game_over:
        draw_diamond(diamond_x, diamond_y, diamond_color)

    glutSwapBuffers()


glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(WIDTH, HEIGHT)
glutInitWindowPosition(0, 0)
glutCreateWindow(b"Catch the Diamonds!")

glViewport(0, 0, WIDTH, HEIGHT)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluOrtho2D(0, WIDTH, 0, HEIGHT)
glMatrixMode(GL_MODELVIEW)
glClearColor(0, 0, 0, 1)
glPointSize(2)

glutDisplayFunc(display)
glutIdleFunc(update)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special_keys)
glutMouseFunc(mouse)
glutMainLoop()